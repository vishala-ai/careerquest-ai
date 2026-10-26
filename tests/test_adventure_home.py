"""Backend persistence contract consumed by Adventure Home; isolated records only."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from owned_client import TestClient
from careerquest import api
from careerquest.store import connect


class AdventureHomePersistenceTests(unittest.TestCase):
    def test_returning_progress_is_persisted_and_client_flags_cannot_unlock_planning(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(api, 'DB', str(Path(directory)/'home.sqlite3')):
            with TestClient(api.app) as client:
                state=client.post('/api/profiles',json={'fictional_ack':True,'alias':'Fictional Orbit','grade':10,'xp':999,'confirmed':True,'quest_complete':True}).json()
                pid=state['profile']['id']; base=f'/api/profiles/{pid}'
                self.assertEqual(state['profile']['xp'],0)
                self.assertFalse(state['confirmed'])
                for path,body in [('/explore',{'message':'Explore careers'}),('/roadmap/propose',{}),('/roadmap/save',{'plan':{}})]:
                    self.assertEqual(client.post(base+path,json=body).status_code,409)
                option=next(iter(api.QUESTS[0]['options']))
                client.post(base+'/quests/0',json={'option':option})
                self.assertEqual(client.post(base+'/quests/0',json={'option':option}).status_code,409)
            # New client and fresh SQLite connections: resume saved progress.
            with TestClient(api.app) as client:
                resumed=client.get(base).json()
                self.assertEqual(resumed['quest_count'],1)
                self.assertEqual(resumed['profile']['xp'],20)
                self.assertEqual(resumed['profile']['alias'],'Fictional Orbit')
                for step,quest in enumerate(api.QUESTS[1:],1):
                    client.post(base+f'/quests/{step}',json={'option':next(iter(quest['options']))})
                client.post(base+'/confirm',json={'interests':['technology']})
                client.post(base+'/explore',json={'message':'Explore technology careers','simulate_failure':True})
                self.assertEqual(client.get(base).json()['research_count'],0)
                client.post(base+'/explore',json={'message':'Explore technology careers'})
                self.assertEqual(client.get(base).json()['research_count'],1)
                proposal=client.post(base+'/roadmap/propose',json={}).json()['plan']
                self.assertIsNone(client.get(base).json()['latest_plan'])
                client.post(base+'/roadmap/save',json={'plan':proposal})
            with TestClient(api.app) as client:
                saved=client.get(base).json()
                self.assertTrue(saved['confirmed'])
                self.assertEqual(saved['latest_plan']['version'],1)
                self.assertEqual(saved['research_count'],1)
                xp=saved['profile']['xp']
                for _ in range(3):
                    self.assertEqual(client.get(base).json()['profile']['xp'],xp)
                client.post(base+'/draft',json={'interests':['design'],'start_edit':True,'expected_version':saved['profile_version']})
                edited=client.get(base).json()
                self.assertFalse(edited['confirmed'])
                self.assertIsNotNone(edited['profile_preferences'])
                self.assertEqual(edited['latest_plan']['version'],1)
                for path,body in [('/explore',{'message':'Explore careers'}),('/roadmap/propose',{}),('/roadmap/save',{'plan':proposal})]:
                    self.assertEqual(client.post(base+path,json=body).status_code,409)
                self.assertEqual(client.get(base).json()['profile']['xp'],xp)

    def test_legacy_missing_nickname_is_returned_without_changing_records(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(api, 'DB', str(Path(directory)/'home.sqlite3')):
            with TestClient(api.app) as client:
                state=client.post('/api/profiles',json={'fictional_ack':True,'alias':'Fictional Fixture','grade':9}).json()
                pid=state['profile']['id']
                with connect(api.DB) as connection:
                    connection.execute('UPDATE profiles SET alias=? WHERE id=?',('',pid))
                self.assertEqual(client.get(f'/api/profiles/{pid}').json()['profile']['alias'],'')
