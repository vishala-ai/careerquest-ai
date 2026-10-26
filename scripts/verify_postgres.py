"""Run the backend suite in isolated PostgreSQL schemas, without migrating data.

Requires CAREERQUEST_TEST_DATABASE_URL pointing to a dedicated test database.
Random cq_test_* schemas are created and removed; existing tables are untouched.
"""
import hashlib
import os
from pathlib import Path
import sys
import unittest
import uuid
import subprocess
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import psycopg
from psycopg import sql
from careerquest import store
from careerquest.postgres import connect


def main():
    url=os.getenv('CAREERQUEST_TEST_DATABASE_URL')
    if not url:raise SystemExit('Set CAREERQUEST_TEST_DATABASE_URL for a dedicated test database; no test database was opened')
    prefix='cq_test_'+uuid.uuid4().hex[:12]+'_'
    schemas=set()
    def isolated(path=store.DEFAULT_DB):
        schema=prefix+hashlib.sha256(str(path).encode()).hexdigest()[:16]
        if schema not in schemas:
            with psycopg.connect(url,autocommit=True) as admin:admin.execute(sql.SQL('CREATE SCHEMA IF NOT EXISTS {}').format(sql.Identifier(schema)))
            schemas.add(schema)
        return connect(url,store.SCHEMA,schema=schema)
    store.connect=isolated
    original_run=subprocess.run
    def child_run(args,**kwargs):
        # Existing restart tests pass their fixture DB path to a fresh Python
        # process. Route that process to the same isolated PostgreSQL schema.
        if len(args)>4 and args[1]=='-c':
            schema=prefix+hashlib.sha256(str(args[3]).encode()).hexdigest()[:16]
            env=dict(kwargs.get('env',os.environ));env['CAREERQUEST_TEST_SCHEMA']=schema
            prelude="import os; from careerquest import store as _s; from careerquest.postgres import connect as _pg; _s.connect=lambda path=_s.DEFAULT_DB: _pg(os.environ['CAREERQUEST_TEST_DATABASE_URL'],_s.SCHEMA,schema=os.environ['CAREERQUEST_TEST_SCHEMA']); "
            args=[*args[:2],prelude+args[2],*args[3:]];kwargs['env']=env
        return original_run(args,**kwargs)
    try:
        suite=unittest.defaultTestLoader.discover('tests')
        if '--pglite' in sys.argv:
            def limited(group):
                for item in group:
                    if isinstance(item,unittest.TestSuite):limited(item)
                    elif item._testMethodName in ('test_parallel_duplicate_submits_are_atomic','test_one_explorer_per_account_retry_and_parallel_creation_no_xp_or_confirmation'):
                        setattr(item,item._testMethodName,lambda t=item:t.skipTest('PGlite multiplexes one connection; run concurrency checks on native PostgreSQL'))
            limited(suite)
        with patch('subprocess.run',side_effect=child_run):result=unittest.TextTestRunner(verbosity=2).run(suite)
    finally:
        with psycopg.connect(url,autocommit=True) as admin:
            for schema in schemas:admin.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
