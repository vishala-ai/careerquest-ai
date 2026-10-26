import os
import tempfile
import time
import unittest
import uuid
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from careerquest import api,auth
from careerquest.store import connect,create_profile

PASSWORD='Demo passphrase with curiosity 42'


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=str(Path(self.tmp.name)/'isolated.sqlite3')
        db=patch.object(api,'DB',self.path);db.start();self.addCleanup(db.stop)
        env=patch.dict(os.environ,{'CAREERQUEST_ENV':'local','CAREERQUEST_PUBLIC_ORIGIN':'','DATABASE_URL':'','REPLIT_DEPLOYMENT':'0','CAREERQUEST_DEV_TOOLS':'0'});env.start();self.addCleanup(env.stop)
        self.c=self.client()
    def client(self):
        c=TestClient(api.app,base_url='http://127.0.0.1',client=('127.0.0.1',45000));self.addCleanup(c.close);return c
    def register(self,c=None,username='demo_alias'):
        c=c or self.c
        r=c.post('/api/auth/register',json={'username':username,'password':PASSWORD,'demo_ack':True},headers={'x-cq-request':'1'})
        self.assertEqual(r.status_code,200,r.text);c.headers['x-csrf-token']=r.json()['csrf_token'];return r
    def create(self,c=None):
        c=c or self.c
        r=c.post('/api/profiles',json={'alias':'Orbit Alias','grade':11,'fictional_ack':True,'creation_key':str(uuid.uuid4())})
        self.assertEqual(r.status_code,200,r.text);return r.json()
    def test_registration_hashes_password_and_cookie_holds_only_random_session(self):
        response=self.register();self.assertNotIn(PASSWORD,response.text)
        cookie=response.headers['set-cookie'];self.assertIn('HttpOnly',cookie);self.assertIn('SameSite=strict',cookie)
        with connect(self.path) as c:
            row=c.execute('SELECT * FROM auth_accounts').fetchone();self.assertTrue(row['password_hash'].startswith('$argon2id$'))
            self.assertTrue(auth.HASHER.verify(row['password_hash'],PASSWORD))
            session=c.execute('SELECT * FROM auth_sessions').fetchone();self.assertNotEqual(session['token_hash'],self.c.cookies.get(auth.COOKIE))
        self.assertTrue(self.c.get('/api/auth/session').json()['authenticated'])
    def test_all_profile_routes_and_pdf_are_private_without_a_session(self):
        for route in api.app.routes:
            path=getattr(route,'path','')
            if '/api/profiles' not in path:continue
            path=path.replace('{pid}','unknown').replace('{step}','0').replace('{sid}','story').replace('{wid}','software').replace('{eid}','research').replace('{mid}','milestone').replace('{cid}','portfolio')
            for method in route.methods-{'HEAD','OPTIONS'}:
                self.assertEqual(self.c.request(method,path,json={} if method=='POST' else None).status_code,401,(method,path))
    def test_one_explorer_per_account_retry_and_parallel_creation_no_xp_or_confirmation(self):
        self.register();body={'alias':'Orbit Alias','grade':11,'fictional_ack':True}
        with ThreadPoolExecutor(max_workers=5) as pool:replies=list(pool.map(lambda _:self.c.post('/api/profiles',json=body),range(5)))
        self.assertTrue(all(r.status_code==200 for r in replies));self.assertEqual(len({r.json()['profile']['id'] for r in replies}),1)
        state=replies[0].json();self.assertEqual(state['profile']['xp'],0);self.assertEqual(state['events'],[]);self.assertFalse(state['confirmed'])
        self.assertEqual(self.c.post('/api/profiles',json=body|{'alias':'Another Alias'}).status_code,409)
    def test_cross_account_read_write_pdf_and_legacy_routes_return_404(self):
        self.register();pid=self.create()['profile']['id'];other=self.client();self.register(other,'other_alias')
        for suffix,method,body in [('', 'GET',None),('/quests/0','POST',{'option':'Build a mini-app'}),('/confirm','POST',{}),('/explore','POST',{'message':'Explore careers'}),('/career-discovery','GET',None),('/career-portfolio/versions/one/pdf','GET',None)]:
            self.assertEqual(other.request(method,'/api/profiles/'+pid+suffix,json=body).status_code,404)
        self.assertEqual(other.get('/api/profiles').status_code,404)
    def test_legacy_profiles_cannot_be_claimed_through_registration_or_creation_keys(self):
        with connect(self.path) as c:pid=create_profile(c,'Existing Alias',12,request_key='existing-key')
        self.register();self.assertEqual(self.c.get('/api/profiles/'+pid).status_code,404)
        r=self.c.post('/api/auth/register',json={'username':'claim_attempt','password':PASSWORD,'demo_ack':True,'profile_id':pid},headers={'x-cq-request':'1'})
        self.assertEqual(r.status_code,422);self.assertNotIn(PASSWORD,r.text)
        self.assertNotEqual(self.create()['profile']['id'],pid)
    def test_logout_revokes_session_and_login_restores_progress_after_restart(self):
        self.register();state=self.create();pid=state['profile']['id'];base='/api/profiles/'+pid
        self.assertEqual(self.c.post(base+'/quests/0',json={'option':next(iter(api.QUESTS[0]['options']))}).status_code,200)
        old_token=self.c.cookies.get(auth.COOKIE);self.assertEqual(self.c.post('/api/auth/logout',json={}).status_code,200)
        self.assertEqual(self.c.get(base,headers={'cookie':'cq_session='+old_token}).status_code,401)
        fresh=self.client();r=fresh.post('/api/auth/login',json={'username':' DEMO_ALIAS ','password':PASSWORD},headers={'x-cq-request':'1'})
        self.assertEqual(r.status_code,200);self.assertEqual(r.json()['account']['profile_id'],pid)
        self.assertNotEqual(fresh.cookies.get(auth.COOKIE),old_token)
        saved=fresh.get(base).json();self.assertEqual(saved['quest_count'],1);self.assertEqual(saved['profile']['xp'],20)
        fresh.headers['x-csrf-token']=r.json()['csrf_token'];self.assertEqual(fresh.post(base+'/quests/0',json={'option':next(iter(api.QUESTS[0]['options']))}).status_code,409)
    def test_session_expiry_and_csrf_origin_guards(self):
        self.register();pid=self.create()['profile']['id']
        self.assertEqual(self.c.post('/api/auth/logout',json={},headers={'x-csrf-token':''}).status_code,403)
        self.assertEqual(self.c.post('/api/auth/logout',json={},headers={'origin':'https://evil.example'}).status_code,403)
        self.assertEqual(self.c.get('/api/profiles/'+pid,headers={'sec-fetch-site':'cross-site'}).status_code,403)
        with connect(self.path) as c:c.execute('UPDATE auth_sessions SET expires_at=?',(time.time()-1,))
        self.assertEqual(self.c.get('/api/profiles/'+pid).status_code,401)
    def test_login_errors_are_generic_and_limited_across_clients(self):
        self.register()
        for username in ('demo_alias','does_not_exist'):
            r=self.c.post('/api/auth/login',json={'username':username,'password':'wrong'},headers={'x-cq-request':'1'})
            self.assertEqual(r.status_code,401);self.assertEqual(r.json()['detail'],'Username or password is incorrect')
        fresh=self.client()
        for _ in range(9):fresh.post('/api/auth/login',json={'username':'does_not_exist','password':'wrong'},headers={'x-cq-request':'1'})
        self.assertEqual(fresh.post('/api/auth/login',json={'username':'does_not_exist','password':'wrong'},headers={'x-cq-request':'1'}).status_code,429)
    def test_validation_does_not_echo_password_and_signup_requires_acknowledgment(self):
        for body in ({'username':'x','password':PASSWORD,'demo_ack':True},{'username':'valid_alias','password':'short','demo_ack':True},{'username':'valid_alias','password':PASSWORD,'demo_ack':False},{'username':'valid_alias','password':PASSWORD,'unexpected':PASSWORD}):
            r=self.c.post('/api/auth/register',json=body,headers={'x-cq-request':'1'});self.assertEqual(r.status_code,422);self.assertNotIn(PASSWORD,r.text)
        self.assertEqual(self.c.post('/api/auth/register',json={'username':'valid_alias','password':PASSWORD,'demo_ack':True}).status_code,403)
    def test_public_configuration_fails_closed_and_secure_cookie_is_used(self):
        with patch.dict(os.environ,{'CAREERQUEST_ENV':'production'}):
            with self.assertRaises(RuntimeError):auth.check_configuration()
        with patch.dict(os.environ,{'CAREERQUEST_PUBLIC_ORIGIN':'https://demo.example','CAREERQUEST_ENV':'production'}):
            with self.assertRaises(RuntimeError):auth.check_configuration()
        with patch.dict(os.environ,{'CAREERQUEST_PUBLIC_ORIGIN':'https://demo.example'}):
            c=TestClient(api.app,base_url='https://demo.example');self.addCleanup(c.close)
            r=self.register(c);self.assertIn('Secure',r.headers['set-cookie']);self.assertIn('max-age=',r.headers['strict-transport-security'])
            self.assertEqual(c.get('/api/auth/session',headers={'host':'evil.example'}).status_code,400)
    def test_unconfirmed_account_cannot_bypass_personalization_gates(self):
        self.register();base='/api/profiles/'+self.create()['profile']['id']
        for suffix,body in [('/worlds/software/explore',{}),('/roadmap/propose',{}),('/confirm',{'interests':['science']})]:self.assertEqual(self.c.post(base+suffix,json=body).status_code,409)
    def test_host_assignment_and_reset_keep_history_and_revoke_sessions(self):
        from scripts.account_admin import main
        with connect(self.path) as c:
            auth.initialize(c);pid=create_profile(c,'Existing Alias',10)
        with patch.dict(os.environ,{'CAREERQUEST_DB':self.path}),patch('getpass.getpass',return_value=PASSWORD),patch('sys.argv',['account_admin.py','assign','--username','host_assigned','--profile-id',pid]):main()
        r=self.c.post('/api/auth/login',json={'username':'host_assigned','password':PASSWORD},headers={'x-cq-request':'1'});self.assertEqual(r.status_code,200)
        self.assertEqual(r.json()['account']['profile_id'],pid);before=self.c.get('/api/profiles/'+pid).json()
        with patch.dict(os.environ,{'CAREERQUEST_DB':self.path}),patch('getpass.getpass',return_value='Replacement demo passphrase 99'),patch('sys.argv',['account_admin.py','reset','--username','host_assigned']):main()
        self.assertEqual(self.c.get('/api/profiles/'+pid).status_code,401)
        r=self.c.post('/api/auth/login',json={'username':'host_assigned','password':'Replacement demo passphrase 99'},headers={'x-cq-request':'1'});self.assertEqual(r.status_code,200)
        self.assertEqual(self.c.get('/api/profiles/'+pid).json(),before)
    def test_chunked_or_oversized_requests_are_rejected_before_processing(self):
        response=self.c.post('/api/auth/login',content=iter([b'x'*40000,b'y'*40000]),headers={'x-cq-request':'1','content-type':'application/json'})
        self.assertEqual(response.status_code,413)
        for value in ('invalid','-1'):
            self.assertEqual(self.c.post('/api/auth/login',content=b'{}',headers={'content-length':value,'x-cq-request':'1'}).status_code,400)
    def test_explicit_sqlite_path_never_uses_an_inherited_cloud_database(self):
        path=str(Path(self.tmp.name)/'storage-boundary.sqlite3')
        code="from careerquest.store import connect,create_profile,profile; c=connect("+repr(path)+"); pid=create_profile(c,'Storage Boundary Alias',11); assert profile(c,pid)['xp']==0; c.close()"
        env=dict(os.environ,DATABASE_URL='postgresql://unreachable.invalid/must_not_connect')
        result=subprocess.run([sys.executable,'-c',code],env=env,capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr);self.assertTrue(Path(path).is_file())
