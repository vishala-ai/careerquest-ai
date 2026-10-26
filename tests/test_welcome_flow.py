"""First-time/returning API contract, with a separate synthetic database."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from owned_client import TestClient
from careerquest import api
from careerquest.store import connect


class WelcomeFlowTests(unittest.TestCase):
    def test_create_reload_first_quest_and_confirmation_keep_one_explorer(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(api,'DB',str(Path(directory)/'welcome.sqlite3')):
            with TestClient(api.app) as client:
                created=client.post('/api/profiles',json={'fictional_ack':True,'alias':'Fictional Welcome Demo','grade':10})
                self.assertEqual(created.status_code,200)
                state=created.json();pid=state['profile']['id'];base=f'/api/profiles/{pid}'
                self.assertEqual(state['profile']['xp'],0)
                self.assertEqual(state['quest_count'],0)
                self.assertEqual(state['events'],[])
                for _ in range(3):
                    self.assertEqual(client.get(base).json(),state)
            with TestClient(api.app) as client:
                self.assertEqual(client.get(base).json()['profile']['id'],pid)
                first=next(iter(api.QUESTS[0]['options']))
                self.assertEqual(client.post(base+'/quests/0',json={'option':first}).status_code,200)
                self.assertEqual(client.post(base+'/quests/0',json={'option':first}).status_code,409)
                self.assertEqual(client.get(base).json()['profile']['xp'],20)
                for step,quest in enumerate(api.QUESTS[1:],1):
                    self.assertEqual(client.post(base+f'/quests/{step}',json={'option':next(iter(quest['options']))}).status_code,200)
                for _ in range(2):
                    self.assertEqual(client.post(base+'/confirm',json={'interests':['science']}).status_code,200)
            with TestClient(api.app) as client:
                returned=client.get(base).json()
                self.assertTrue(returned['confirmed'])
                self.assertEqual(returned['quest_count'],3)
                self.assertEqual(returned['profile']['xp'],70)
            connection=connect(api.DB)
            try:self.assertEqual(connection.execute('SELECT COUNT(*) FROM profiles').fetchone()[0],1)
            finally:connection.close()
