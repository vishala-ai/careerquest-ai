"""Shared discovery state, edit integrity, source history and reconfirmation gates."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from owned_client import TestClient
from careerquest import api
from careerquest.discovery import discovery_state
from careerquest.store import connect


class DiscoveryFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.database=patch.object(api,'DB',str(Path(self.temp.name)/'discovery.sqlite3'));self.database.start()
        self.client=TestClient(api.app)
        self.initial=self.client.post('/api/profiles',json={'fictional_ack':True,'alias':'Fictional Discovery Demo','grade':11}).json()
        self.pid=self.initial['profile']['id'];self.base=f'/api/profiles/{self.pid}'
    def tearDown(self):
        self.client.close();self.database.stop();self.temp.cleanup()
    def get(self):return self.client.get(self.base).json()
    def complete(self):
        for step,quest in enumerate(api.QUESTS):
            self.assertEqual(self.client.post(self.base+f'/quests/{step}',json={'option':next(iter(quest['options']))}).status_code,200)
    def test_all_three_states_reload_and_explicit_reward_receipts(self):
        self.assertEqual(self.initial['discovery']['first_incomplete'],0)
        self.assertEqual(self.initial['discovery']['quest_xp'],0)
        self.client.post(self.base+'/quests/0',json={'option':'Build a mini-app'})
        partial=self.get();self.assertEqual(partial['discovery']['first_incomplete'],1)
        self.assertEqual(partial['discovery']['quest_xp'],20)
        self.assertEqual(partial['quest_answers'][0]['payload']['xp_awarded'],20)
        with TestClient(api.app) as reloaded:self.assertEqual(reloaded.get(self.base).json(),partial)
        for step in (1,2):self.client.post(self.base+f'/quests/{step}',json={'option':next(iter(api.QUESTS[step]['options']))})
        completed=self.get();self.assertIsNone(completed['discovery']['first_incomplete'])
        self.assertEqual(completed['discovery']['quest_xp'],60)
        self.assertEqual(len(completed['discovery']['xp_events']),3)
        self.assertEqual(self.client.post(self.base+'/quests/0',json={'option':'Build a mini-app'}).status_code,409)
        repeated=self.client.post(self.base+'/quests/0',json={'option':'Build a mini-app','revise':True}).json()
        self.assertEqual(repeated,completed)
    def test_edit_preserves_confirmed_profile_and_all_plans_until_reconfirmation(self):
        self.complete();self.client.post(self.base+'/confirm',json={'interests':['technology','science']})
        for _ in range(2):
            proposal=self.client.post(self.base+'/roadmap/propose',json={}).json()['plan']
            self.client.post(self.base+'/roadmap/save',json={'plan':proposal})
        before=self.get()
        connection=connect(api.DB)
        try:plans_before=[tuple(row) for row in connection.execute('SELECT id,version,content,created_at FROM plans ORDER BY version')]
        finally:connection.close()
        # Cancelling in the client performs no mutation; reads leave all state unchanged.
        self.assertEqual(self.get(),before)
        edited=self.client.post(self.base+'/quests/0',json={'option':'Sketch an invention','revise':True}).json()
        self.assertFalse(edited['confirmed']);self.assertEqual(edited['profile']['interests'],before['profile']['interests'])
        self.assertEqual(edited['profile_preferences'],before['profile_preferences'])
        self.assertEqual(edited['latest_plan'],before['latest_plan'])
        self.assertEqual(edited['profile']['xp'],before['profile']['xp'])
        self.assertEqual(edited['discovery']['quest_xp'],60)
        self.assertEqual(edited['quest_answers'][0]['payload']['xp_awarded'],0)
        for path,body in [('/explore',{'message':'Explore careers'}),('/roadmap/propose',{}),('/roadmap/save',{'plan':proposal})]:
            self.assertEqual(self.client.post(self.base+path,json=body).status_code,409)
        self.assertEqual(self.client.post(self.base+'/quests/0',json={'option':'Sketch an invention','revise':True}).json(),edited)
        with TestClient(api.app) as reloaded:self.assertEqual(reloaded.get(self.base).json(),edited)
        connection=connect(api.DB)
        try:self.assertEqual([tuple(row) for row in connection.execute('SELECT id,version,content,created_at FROM plans ORDER BY version')],plans_before)
        finally:connection.close()
        confirmed=self.client.post(self.base+'/confirm',json={'interests':['art'],'expected_version':edited['profile_version']}).json()
        self.assertTrue(confirmed['confirmed'])
        self.assertEqual(confirmed['profile_preferences']['quest_answers'][0]['choice'],'Sketch an invention')
        self.assertEqual(confirmed['discovery']['quest_xp'],60)
        self.assertEqual(self.client.post(self.base+'/roadmap/propose',json={}).status_code,200)
        self.assertEqual(confirmed['latest_plan'],before['latest_plan'])
    def test_legacy_reward_projection_never_rewrites_history_or_counts_revision_xp(self):
        event={'id':f'{self.pid}:quest:0','kind':'quest_completed','payload':{'quest':0,'choice':'Build a mini-app'}}
        revision={'id':'revision','kind':'quest_revised','payload':{'quest':0,'choice':'Sketch an invention','xp_awarded':0}}
        history=[event,revision];before=json.dumps(history,sort_keys=True)
        result=discovery_state(self.pid,history,[revision])
        self.assertEqual(result['quest_xp'],20);self.assertEqual(len(result['xp_events']),1)
        self.assertEqual(json.dumps(history,sort_keys=True),before)
        unknown={**event,'id':'unknown-imported-event'}
        self.assertIsNone(discovery_state(self.pid,[unknown],[unknown])['quest_xp'])

    def test_reward_receipts_and_answers_survive_recent_event_window(self):
        self.complete();self.client.post(self.base+'/confirm',json={'interests':['technology']})
        for _ in range(31):
            self.client.post(self.base+'/reflect',json={'message':'Fictional discovery reflection'})
        state=self.get()
        self.assertEqual(len(state['events']),30)
        self.assertFalse(any(event['kind']=='quest_completed' for event in state['events']))
        self.assertEqual(len(state['quest_answers']),3)
        self.assertEqual(state['discovery']['quest_xp'],60)
        self.assertEqual(len(state['discovery']['xp_events']),3)
