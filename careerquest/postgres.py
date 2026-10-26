"""Small PostgreSQL storage adapter for the existing bounded SQLite queries.

Local SQLite remains the default. Cloud transactions serialize writes with a
PostgreSQL advisory lock, preserving BEGIN IMMEDIATE/version allocation semantics.
The appended rowid preserves insertion ordering without leaking into snapshots.
"""
import re
import threading
import hashlib

import psycopg
from psycopg.pq import TransactionStatus

_initialized=set()
_schema_lock=threading.Lock()
WRITE_LOCK=781934650


class Row(dict):
    # sqlite3.Row iterates values but also exposes keys for dict(row).
    def __iter__(self):return iter(self.values())
    def __getitem__(self,key):
        return tuple(self.values())[key] if isinstance(key,int) else super().__getitem__(key)


class Cursor:
    def __init__(self,cursor):self.cursor=cursor
    def _row(self,row):
        if row is None:return None
        return Row((column.name,value) for column,value in zip(self.cursor.description,row) if column.name!='rowid')
    def fetchone(self):return self._row(self.cursor.fetchone())
    def fetchall(self):return [self._row(row) for row in self.cursor.fetchall()]
    def __iter__(self):
        for row in self.cursor:yield self._row(row)


class Connection:
    def __init__(self,url,schema=None):
        if schema and not re.fullmatch(r'[a-z][a-z0-9_]{0,62}',schema):raise ValueError('Use a lowercase PostgreSQL schema name, up to 63 characters')
        self.raw=psycopg.connect(url,autocommit=True,connect_timeout=10,prepare_threshold=None)
        if schema:
            try:
                with self.raw.transaction():
                    self.raw.execute('SELECT pg_advisory_xact_lock(%s)',(WRITE_LOCK,))
                    self.raw.execute(psycopg.sql.SQL('CREATE SCHEMA IF NOT EXISTS {}').format(psycopg.sql.Identifier(schema)))
                self.raw.execute(psycopg.sql.SQL('SET search_path TO {}').format(psycopg.sql.Identifier(schema)))
            except Exception:
                self.raw.close();raise
        self.key=hashlib.sha256((url+'|'+str(schema)).encode()).hexdigest()
    @property
    def in_transaction(self):return self.raw.info.transaction_status!=TransactionStatus.IDLE
    def _begin(self):
        self.raw.execute('BEGIN')
        self.raw.execute('SELECT pg_advisory_xact_lock(%s)',(WRITE_LOCK,))
    def execute(self,sql,parameters=()):
        command=sql.strip()
        if command=="SELECT name FROM sqlite_master WHERE type='table'":
            command="SELECT tablename AS name FROM pg_tables WHERE schemaname=current_schema() ORDER BY tablename"
        if command.upper()=='BEGIN IMMEDIATE':
            if self.raw.info.transaction_status!=TransactionStatus.IDLE:raise RuntimeError('Transaction already started')
            self._begin();return Cursor(self.raw.cursor())
        if command.upper().startswith(('INSERT ','UPDATE ','DELETE ')) and self.raw.info.transaction_status==TransactionStatus.IDLE:self._begin()
        ignore=command.upper().startswith('INSERT OR IGNORE ')
        if ignore:command=re.sub(r'^INSERT OR IGNORE','INSERT',command,flags=re.I)+' ON CONFLICT DO NOTHING'
        command=command.replace('? IS NULL','CAST(? AS TEXT) IS NULL').replace('?','%s')
        return Cursor(self.raw.execute(command,parameters))
    def executescript(self,script):
        key=(self.key,hashlib.sha256(script.encode()).hexdigest())
        with _schema_lock:
            if key in _initialized:return
            try:
                self._begin()
                for statement in script.split(';'):
                    statement=statement.strip()
                    if not statement:continue
                    if statement.upper().startswith('CREATE TABLE'):
                        statement=statement[:-1]+',rowid BIGSERIAL UNIQUE)'
                        # SQLite REAL is binary64; PostgreSQL REAL is binary32,
                        # which would round epoch seconds by up to a minute.
                        statement=re.sub(r'\bREAL\b','DOUBLE PRECISION',statement)
                    self.raw.execute(statement)
                self.commit();_initialized.add(key)
            except Exception:
                self.rollback();raise
    def commit(self):self.raw.commit()
    def rollback(self):self.raw.rollback()
    def close(self):self.raw.close()
    def __enter__(self):return self
    def __exit__(self,kind,value,traceback):
        if kind:self.rollback()
        else:self.commit()


def connect(url,ddl,schema=None):
    c=Connection(url,schema)
    try:c.executescript(ddl)
    except Exception:
        c.close();raise
    return c
