"""Strict setup and durable creation receipts, using only isolated fictional data."""
import tempfile,unittest,uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from owned_client import TestClient
from careerquest import api
from careerquest.store import connect

class ExplorerSetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        override=patch.object(api,'DB',str(Path(self.tmp.name)/'fictional.sqlite3'));override.start();self.addCleanup(override.stop)
        self.client=TestClient(api.app);self.addCleanup(self.client.close)
        self.body={'alias':'  Fictional Compass  ','grade':9,'fictional_ack':True,'creation_key':str(uuid.uuid4())}
    def count(self):
        with connect(api.DB) as c:return c.execute('SELECT COUNT(*) FROM profiles').fetchone()[0]
    def test_invalid_setup_cannot_write_a_profile(self):
        invalid=[{'alias':''},{'alias':'  '},{'alias':'x'},{'alias':'x'*41},{'grade':8},{'grade':13},{'grade':'9'},{'grade':True},{'fictional_ack':False},{'fictional_ack':None},{'fictional_ack':1},{'fictional_ack':'true'},{'creation_key':'bad-key'}]
        for change in invalid:
            with self.subTest(change=change):self.assertEqual(self.client.post('/api/profiles',json=self.body|change).status_code,422)
        for field in ['alias','grade','fictional_ack']:
            body=self.body.copy();del body[field]
            with self.subTest(missing=field):self.assertEqual(self.client.post('/api/profiles',json=body).status_code,422)
        self.assertEqual(self.count(),0)
    def test_repeat_retry_and_restart_return_same_profile_without_rewards_or_confirmation(self):
        first=self.client.post('/api/profiles',json=self.body).json();pid=first['profile']['id']
        self.assertEqual(first['profile']['alias'],'Fictional Compass')
        self.assertEqual(first['profile']['xp'],0);self.assertFalse(first['confirmed']);self.assertEqual(first['events'],[])
        for _ in range(3):self.assertEqual(self.client.post('/api/profiles',json=self.body).json(),first)
        with TestClient(api.app) as restarted:
            self.assertEqual(restarted.post('/api/profiles',json=self.body).json(),first)
            self.assertEqual(restarted.get('/api/profiles/'+pid).json(),first)
            self.assertEqual(restarted.post('/api/profiles/'+pid+'/confirm',json={'interests':['art']}).status_code,409)
            self.assertEqual(restarted.post('/api/profiles/'+pid+'/worlds/software/explore',json={}).status_code,409)
        self.assertEqual(self.count(),1)
    def test_parallel_duplicate_submits_are_atomic(self):
        with ThreadPoolExecutor(max_workers=5) as pool:
            replies=list(pool.map(lambda _:self.client.post('/api/profiles',json=self.body),range(5)))
        self.assertTrue(all(r.status_code==200 for r in replies));self.assertEqual(len({r.json()['profile']['id'] for r in replies}),1);self.assertEqual(self.count(),1)
    def test_reusing_a_receipt_for_different_values_is_rejected(self):
        self.assertEqual(self.client.post('/api/profiles',json=self.body).status_code,200)
        for change in [{'alias':'Other Fictional'},{'grade':12}]:self.assertEqual(self.client.post('/api/profiles',json=self.body|change).status_code,409)
        self.assertEqual(self.count(),1)
    def test_switching_reads_preserve_existing_progress_and_never_lists_global_records(self):
        first=self.client.post('/api/profiles',json=self.body).json()['profile']['id'];base='/api/profiles/'+first
        self.client.post(base+'/quests/0',json={'option':next(iter(api.QUESTS[0]['options']))})
        before=self.client.get(base).json()
        second=self.client.post('/api/profiles',json=self.body|{'alias':'Second Fictional','grade':12,'creation_key':str(uuid.uuid4())}).json()
        for _ in range(2):
            self.assertEqual(self.client.get(base).json(),before)
            self.assertEqual(self.client.get('/api/profiles/'+second['profile']['id']).json(),second)
        self.assertEqual(before['profile']['xp'],20);self.assertEqual(second['profile']['xp'],0)
        self.assertEqual(self.client.get('/api/profiles').status_code,404)
