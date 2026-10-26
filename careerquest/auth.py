"""Username/password accounts for the alias-only demo. No public profile claiming."""
import hashlib
import os
import re
import secrets
import time
import uuid
import threading
from urllib.parse import urlsplit

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import HTTPException

HASHER = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)
HASH_CAPACITY = threading.BoundedSemaphore(2)
DUMMY_HASH = HASHER.hash(secrets.token_urlsafe(32))
COOKIE = 'cq_session'
SESSION_SECONDS = 12 * 60 * 60
SCHEMA = '''
CREATE TABLE IF NOT EXISTS auth_accounts(
 id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
 profile_id TEXT UNIQUE REFERENCES profiles(id), created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS auth_sessions(
 token_hash TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES auth_accounts(id),
 csrf TEXT NOT NULL, expires_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS auth_attempts(
 bucket TEXT NOT NULL, attempted_at REAL NOT NULL);
CREATE INDEX IF NOT EXISTS auth_attempt_time ON auth_attempts(bucket,attempted_at);
'''


def initialize(c):
    c.executescript(SCHEMA)


def public_origin():
    origin = os.getenv('CAREERQUEST_PUBLIC_ORIGIN', '').rstrip('/')
    if not origin and os.getenv('CAREERQUEST_ENV','local')=='local' and os.getenv('REPLIT_DEV_DOMAIN'):
        origin='https://'+os.environ['REPLIT_DEV_DOMAIN']
    if origin:
        parts = urlsplit(origin)
        if parts.scheme != 'https' or not parts.netloc or parts.path or parts.query or parts.fragment or parts.username:
            raise RuntimeError('CAREERQUEST_PUBLIC_ORIGIN must be an HTTPS origin without a path')
    return origin


def check_configuration():
    origin = public_origin()
    if os.getenv('CAREERQUEST_ENV', 'local') != 'local' and not origin:
        raise RuntimeError('Set CAREERQUEST_PUBLIC_ORIGIN for shared/cloud deployments')
    if os.getenv('REPLIT_DEPLOYMENT') == '1' or os.getenv('CAREERQUEST_ENV') == 'production':
        if not os.getenv('DATABASE_URL', '').startswith(('postgres://', 'postgresql://')):
            raise RuntimeError('Cloud publishing requires persistent PostgreSQL DATABASE_URL; local SQLite is preserved')


def same_origin(request):
    expected = public_origin()
    if expected:
        if request.headers.get('host', '').lower() != urlsplit(expected).netloc.lower():
            raise HTTPException(400, 'Unexpected application host')
    else:
        host = request.url.hostname
        if host not in ('localhost', '127.0.0.1', '::1', 'testserver'):
            raise HTTPException(503, 'Configure the public HTTPS origin before sharing this app')
        expected = str(request.base_url).rstrip('/')
    origin = request.headers.get('origin')
    if (origin and origin != expected) or request.headers.get('sec-fetch-site') == 'cross-site':
        raise HTTPException(403, 'Use this application’s own login and forms')


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def limit(c, bucket, maximum, window=900):
    """Persist limits across restart; serialize updates across processes."""
    current = time.time()
    with c:
        c.execute('BEGIN IMMEDIATE')
        c.execute('DELETE FROM auth_attempts WHERE attempted_at<?', (current-86400,))
        count = c.execute('SELECT COUNT(*) FROM auth_attempts WHERE bucket=? AND attempted_at>?', (bucket,current-window)).fetchone()[0]
        if count >= maximum:
            raise HTTPException(429, 'Too many attempts. Please try again later.', headers={'Retry-After':str(window)})
        c.execute('INSERT INTO auth_attempts VALUES(?,?)', (bucket,current))


def account(c, request, required=True):
    token = request.cookies.get(COOKIE, '')
    row = c.execute('SELECT a.*,s.csrf,s.expires_at FROM auth_sessions s JOIN auth_accounts a ON a.id=s.account_id WHERE s.token_hash=? AND s.expires_at>?', (digest(token),time.time())).fetchone() if token else None
    if not row and required:
        raise HTTPException(401, 'Please sign in to continue')
    return dict(row) if row else None


def authorize(c, request):
    if not request.url.path.startswith('/api/'):
        return None
    public = ('/api/health','/api/quests','/api/career-worlds','/api/career-discovery-milestone','/api/auth/session','/api/auth/login','/api/auth/register')
    if request.url.path in public and request.method == 'GET':
        return None
    same_origin(request)
    if request.url.path in ('/api/auth/login','/api/auth/register'):
        if request.headers.get('x-cq-request') != '1':
            raise HTTPException(403, 'Submit the login form from this application')
        return None
    owner = account(c,request)
    if request.method not in ('GET','HEAD','OPTIONS'):
        if not secrets.compare_digest(request.headers.get('x-csrf-token',''),owner['csrf']):
            raise HTTPException(403, 'Your form expired. Reload and try again')
    match = re.search(r'/profiles/([^/]+)',request.url.path)
    if match and owner['profile_id'] != match.group(1):
        raise HTTPException(404, 'Explorer not found')
    return owner


def credentials(username, password):
    username = username.strip().lower()
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{2,29}',username):
        raise HTTPException(422, 'Use a username of 3–30 letters, numbers, hyphens or underscores')
    if not 15 <= len(password) <= 128:
        raise HTTPException(422, 'Use a password or passphrase of 15–128 characters')
    if password.lower() in {'passwordpassword','123456789012345','qwertyuiopasdfgh','careerquestdemo'}:
        raise HTTPException(422, 'Choose a less predictable password or passphrase')
    return username


def register(c, username, password, demo_ack, request):
    username = credentials(username,password)
    if demo_ack is not True:
        raise HTTPException(422, 'Confirm that you will use aliases and test data only')
    peer = request.client.host if request.client else 'unknown'
    limit(c,'register:'+digest(peer),10,3600)
    limit(c,'register-global',100,3600)
    with HASH_CAPACITY:encoded = HASHER.hash(password)
    with c:
        c.execute('BEGIN IMMEDIATE')
        if c.execute('SELECT id FROM auth_accounts WHERE username=?',(username,)).fetchone():
            raise HTTPException(409, 'That username is unavailable. Try another or sign in')
        aid = str(uuid.uuid4())
        c.execute('INSERT INTO auth_accounts VALUES(?,?,?,?,?)',(aid,username,encoded,None,time.time()))
    return aid


def login(c, username, password, request):
    peer = request.client.host if request.client else 'unknown'
    normalized = username.strip().lower()
    # Do not trust forwarded IP headers; a proxy shares this conservative budget.
    limit(c,'login-peer:'+digest(peer),60)
    limit(c,'login-user:'+digest(normalized),10)
    row = c.execute('SELECT * FROM auth_accounts WHERE username=?',(normalized,)).fetchone()
    try:
        with HASH_CAPACITY:valid = HASHER.verify(row['password_hash'] if row else DUMMY_HASH,password)
    except (VerificationError,InvalidHashError):
        valid = False
    if not row or not valid:
        raise HTTPException(401, 'Username or password is incorrect')
    return row['id']


def start_session(c, aid, request, response):
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(32)
    with c:
        old = request.cookies.get(COOKIE)
        if old:c.execute('DELETE FROM auth_sessions WHERE token_hash=?',(digest(old),))
        c.execute('DELETE FROM auth_sessions WHERE expires_at<?',(time.time(),))
        c.execute('INSERT INTO auth_sessions VALUES(?,?,?,?)',(digest(token),aid,csrf,time.time()+SESSION_SECONDS))
    response.set_cookie(COOKIE,token,max_age=SESSION_SECONDS,httponly=True,secure=bool(public_origin()),samesite='strict',path='/')
    row = c.execute('SELECT id,username,profile_id FROM auth_accounts WHERE id=?',(aid,)).fetchone()
    return {'authenticated':True,'account':dict(row),'csrf_token':csrf}


def logout(c, request, response):
    with c:c.execute('DELETE FROM auth_sessions WHERE token_hash=?',(digest(request.cookies.get(COOKIE,'')),))
    response.delete_cookie(COOKIE,path='/',httponly=True,secure=bool(public_origin()),samesite='strict')
    return {'authenticated':False}


def create_owned_profile(c, owner, alias, grade):
    """Account identity is the creation receipt: retries cannot create a second Explorer."""
    with c:
        c.execute('BEGIN IMMEDIATE')
        row = c.execute('SELECT profile_id FROM auth_accounts WHERE id=?',(owner['id'],)).fetchone()
        if row['profile_id']:
            from .store import profile
            existing = profile(c,row['profile_id'])
            if (existing['alias'],existing['grade']) != (alias,grade):
                raise HTTPException(409, 'This account already has an Explorer. Sign out to create another account')
            return row['profile_id']
        pid = str(uuid.uuid4())
        c.execute('INSERT INTO profiles VALUES(?,?,?,?,?)',(pid,alias,grade,'[]',0))
        c.execute('UPDATE auth_accounts SET profile_id=? WHERE id=?',(pid,owner['id']))
    return pid
