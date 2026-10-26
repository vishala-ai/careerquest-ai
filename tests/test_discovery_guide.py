"""Discovery Guide contract and SQLite integrity tests. All Groq calls are mocked."""
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from owned_client import TestClient
from careerquest import api, discovery_guide as guide
from careerquest.store import connect


class DiscoveryGuideTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = str(Path(self.temp.name) / 'fictional.sqlite3')
        self.patch = patch.object(api, 'DB', self.db); self.patch.start(); self.addCleanup(self.patch.stop)
        self.env = patch.dict('os.environ', {'GROQ_API_KEY': 'synthetic-test-key', 'GROQ_MODEL': 'openai/gpt-oss-120b'})
        self.env.start(); self.addCleanup(self.env.stop)
        self.client = TestClient(api.app); self.addCleanup(self.client.close)
        self.pid = self.client.post('/api/profiles', json={'fictional_ack':True,'alias': 'Fictional Guide Explorer', 'grade': 10}).json()['profile']['id']
        self.base = f'/api/profiles/{self.pid}'
        self.complete()

    def complete(self):
        for step, quest in enumerate(api.QUESTS):
            self.client.post(self.base + f'/quests/{step}', json={'option': next(iter(quest['options']))})

    def state(self): return self.client.get(self.base).json()

    def selection(self):
        with connect(self.db) as c:
            choices = guide.snapshot(c, self.pid)[1]
        return guide.deterministic_summary(choices)

    def reply(self, selection=None, finish='stop'):
        content = json.dumps(selection if selection is not None else self.selection())
        return io.BytesIO(json.dumps({'choices': [{'finish_reason': finish, 'message': {'content': content}}]}).encode())

    def generate(self, retry=False):
        return self.client.post(self.base + '/discovery-guide', json={'retry': retry})

    def test_valid_groq_contract_minimal_data_and_no_action_contract_change(self):
        before = self.state()
        with patch('careerquest.discovery_guide.urllib.request.urlopen', return_value=self.reply()) as send:
            response = self.generate()
        self.assertEqual(response.status_code, 200)
        item = response.json()['latest']; self.assertEqual(item['status'], 'groq')
        self.assertEqual(item['model'], 'openai/gpt-oss-120b')
        body = json.loads(send.call_args.args[0].data)
        self.assertEqual(body['model'], item['model']); self.assertEqual(send.call_args.kwargs['timeout'], 18)
        self.assertEqual(body['response_format']['json_schema']['name'], 'discovery_guide')
        self.assertTrue(body['response_format']['json_schema']['strict'])
        context = json.loads(body['messages'][1]['content'])
        self.assertEqual(set(context), {'grade', 'saved_choices', 'themes', 'activities', 'approved_worlds'})
        self.assertEqual(context['grade'], 10)
        self.assertNotIn('Fictional Guide Explorer', json.dumps(context))
        self.assertNotIn('synthetic-test-key', json.dumps(body))
        self.assertNotIn('profile_preferences', context)
        self.assertEqual(item['source_answers'], context['saved_choices'])
        self.assertEqual(self.state()['profile'], before['profile'])
        self.assertFalse(self.state()['confirmed'])
        for world in item['content']['career_worlds']:
            self.assertIn(world['world_id'], guide.WORLD_IDS); self.assertTrue(world['choice_ids'])
        with patch('careerquest.discovery_guide.groq_discovery') as model:
            self.assertEqual(self.generate().json(), response.json()); model.assert_not_called()
        with TestClient(api.app) as reload:
            self.assertEqual(reload.get(self.base).json()['discovery_guide'], response.json())

    def test_malformed_json_timeout_and_refusal_are_labeled_fallback(self):
        errors = [TimeoutError(), ValueError('malformed'), RuntimeError('missing credential')]
        for error in errors:
            with self.subTest(error=type(error).__name__), patch('careerquest.discovery_guide.groq_discovery', side_effect=error):
                item = self.generate(retry=True).json()['latest']
                self.assertEqual(item['status'], 'fallback'); self.assertEqual(item['error_type'], type(error).__name__)
                self.assertTrue(item['content']['what_you_chose'])
        for raw in ('not json', '{"choices":[{"finish_reason":"length","message":{"content":"{}"}}]}'):
            with patch('careerquest.discovery_guide.urllib.request.urlopen', return_value=io.BytesIO(raw.encode())):
                self.assertEqual(self.generate(retry=True).json()['latest']['status'], 'fallback')
        self.assertEqual(self.state()['profile']['xp'], 60)

    def test_invalid_world_choice_evidence_and_unrestricted_claims_rejected(self):
        cases = []
        invalid = self.selection(); invalid['career_worlds'][0]['world_id'] = 'invented-world'; cases.append(invalid)
        invalid = self.selection(); invalid['what_you_chose'][0]['choice'] = 'Won a science award'; cases.append(invalid)
        invalid = self.selection(); invalid['career_worlds'][0]['choice_ids'] = ['invented-id']; cases.append(invalid)
        invalid = self.selection(); invalid['what_this_might_suggest'][0]['text'] = 'You have 99% career fit'; cases.append(invalid)
        invalid = self.selection(); invalid['what_you_chose'][1] = copy.deepcopy(invalid['what_you_chose'][0]); cases.append(invalid)
        with connect(self.db) as c: choices = guide.snapshot(c, self.pid)[1]
        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(ValueError): guide.validate_output(value, choices)
        # Even a mocked provider bypassing JSON parsing is validated again before persistence.
        with patch('careerquest.discovery_guide.groq_discovery', return_value=cases[1]):
            item = self.generate().json()['latest']
            self.assertEqual(item['status'], 'fallback')
            self.assertNotIn('Won a science award', json.dumps(item))

    def test_world_support_must_match_catalogue_tags_and_max_three(self):
        value = self.selection()
        value['career_worlds'] = [{'world_id': 'design', 'choice_ids': [value['what_you_chose'][1]['choice_id']]}]
        with connect(self.db) as c: choices = guide.snapshot(c, self.pid)[1]
        with self.assertRaises(ValueError): guide.validate_output(value, choices)
        value = self.selection(); value['career_worlds'] *= 4
        with self.assertRaises(ValueError): guide.validate_output(value, choices)

    def test_feedback_persists_without_confirming_profile_or_awarding_xp(self):
        with patch('careerquest.discovery_guide.groq_discovery', side_effect=TimeoutError()): item = self.generate().json()['latest']
        path = self.base + f'/discovery-guide/{item["id"]}/feedback'
        before = self.state()
        for verdict in ('Yes', 'Somewhat', 'Not really'):
            response = self.client.post(path, json={'verdict': verdict, 'correction': 'Fictional correction: explore art'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['latest']['feedback']['verdict'], verdict)
        self.assertEqual(self.client.post(path, json={'verdict': 'Other'}).status_code, 422)
        self.assertEqual(self.client.post(path, json={'verdict': 'Yes', 'correction': 'x' * 501}).status_code, 422)
        current = self.state(); self.assertFalse(current['confirmed'])
        self.assertEqual(current['profile'], before['profile']); self.assertEqual(current['events'], before['events'])
        with connect(self.db) as c:
            count = c.execute('SELECT COUNT(*) FROM discovery_feedback').fetchone()[0]
        self.client.post(path, json={'verdict': 'Not really', 'correction': 'Fictional correction: explore art'})
        with connect(self.db) as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM discovery_feedback').fetchone()[0], count)
        for endpoint, body in [('/roadmap/propose', {}), ('/roadmap/save', {'plan': {}}), ('/explore', {'message': 'Explore careers'})]:
            self.assertEqual(self.client.post(self.base + endpoint, json=body).status_code, 409)
        with TestClient(api.app) as reload:
            self.assertEqual(reload.get(self.base).json()['discovery_guide']['latest']['feedback']['verdict'], 'Not really')

    def test_quest_revision_stales_story_preserves_profile_plans_xp_and_history(self):
        self.client.post(self.base + '/confirm', json={'interests': ['technology']})
        plan = self.client.post(self.base + '/roadmap/propose', json={}).json()['plan']
        self.client.post(self.base + '/roadmap/save', json={'plan': plan})
        with patch('careerquest.discovery_guide.groq_discovery', return_value=self.selection()): old = self.generate().json()['latest']
        self.client.post(self.base + f'/discovery-guide/{old["id"]}/feedback', json={'verdict': 'Yes'})
        before = self.state()
        self.client.post(self.base + '/quests/0', json={'option': 'Sketch an invention', 'revise': True})
        edited = self.state(); self.assertTrue(edited['discovery_guide']['latest']['is_stale'])
        self.assertFalse(edited['confirmed']); self.assertEqual(edited['profile'], before['profile'])
        self.assertEqual(edited['profile_preferences'], before['profile_preferences'])
        self.assertEqual(edited['latest_plan'], before['latest_plan'])
        self.assertEqual(self.client.post(self.base + f'/discovery-guide/{old["id"]}/feedback', json={'verdict': 'Somewhat'}).status_code, 409)
        with patch('careerquest.discovery_guide.groq_discovery', return_value=self.selection()): fresh = self.generate().json()
        self.assertEqual(fresh['latest']['version'], 2); self.assertFalse(fresh['latest']['is_stale'])
        self.assertNotEqual(fresh['latest']['response_version'], old['response_version'])
        self.assertEqual(fresh['history'][0]['content'], old['content'])
        self.assertEqual(fresh['history'][0]['feedback']['verdict'], 'Yes')
        self.assertEqual(fresh['latest']['source_answers'][0]['choice'], 'Sketch an invention')
        self.assertEqual(self.state()['discovery']['quest_xp'], 60)
        self.assertEqual(self.client.post(self.base + '/roadmap/propose', json={}).status_code, 409)
        self.client.post(self.base + '/confirm', json={'interests': ['art'], 'expected_version': edited['profile_version']})
        self.assertEqual(self.client.post(self.base + '/roadmap/propose', json={}).status_code, 200)

    def test_profile_and_global_request_limits_persist_and_cache_costs_nothing(self):
        with patch('careerquest.discovery_guide.groq_discovery', side_effect=TimeoutError()) as model:
            for _ in range(5): self.assertEqual(self.generate(retry=True).status_code, 200)
            limited = self.generate(retry=True); self.assertEqual(limited.status_code, 429)
            self.assertEqual(limited.headers['Retry-After'], '3600')
            self.assertEqual(self.generate().status_code, 200); self.assertEqual(model.call_count, 5)
        with TestClient(api.app) as reload:
            self.assertEqual(reload.post(self.base + '/discovery-guide', json={'retry': True}).status_code, 429)
        # Seed only request records in this temporary DB to exercise the global cap.
        with connect(self.db) as c:
            for index in range(25):
                c.execute('INSERT INTO discovery_stories SELECT ?,profile_id,?,response_version,source_answers,status,model,content,error_type,created_at FROM discovery_stories LIMIT 1', (f'limit-{index}', index + 6))
        new = self.client.post('/api/profiles', json={'fictional_ack':True,'alias': 'Second Fictional Explorer', 'grade': 9}).json()['profile']['id']
        for step, quest in enumerate(api.QUESTS): self.client.post(f'/api/profiles/{new}/quests/{step}', json={'option': next(iter(quest['options']))})
        with patch('careerquest.discovery_guide.groq_discovery') as model:
            self.assertEqual(self.client.post(f'/api/profiles/{new}/discovery-guide', json={}).status_code, 429); model.assert_not_called()

    def test_no_generation_for_incomplete_student_or_untrusted_context(self):
        new = self.client.post('/api/profiles', json={'fictional_ack':True,'alias': 'New Fictional Explorer', 'grade': 9}).json()['profile']['id']
        with patch('careerquest.discovery_guide.groq_discovery') as model:
            self.assertEqual(self.client.post(f'/api/profiles/{new}/discovery-guide', json={}).status_code, 409)
            self.assertEqual(self.generate().status_code, 200)  # Invalid mocked output becomes safe fallback.
            self.assertEqual(model.call_count, 1)
        self.assertEqual(self.client.post(self.base + '/discovery-guide', json={'grade': 12, 'nickname': 'Untrusted'}).status_code, 422)
        self.assertEqual(self.client.post('/api/profiles/missing/discovery-guide', json={}).status_code, 404)

    def test_inflight_generation_deduplicates_and_changed_answers_remain_stale(self):
        def change_during_generation(*args):
            self.assertEqual(self.generate().status_code, 409)
            self.client.post(self.base + '/quests/0', json={'option': 'Sketch an invention', 'revise': True})
            return original
        original = self.selection()
        with patch('careerquest.discovery_guide.groq_discovery', side_effect=change_during_generation):
            result = self.generate().json()
        self.assertTrue(result['latest']['is_stale'])
        self.assertEqual(self.state()['quest_answers'][0]['payload']['choice'], 'Sketch an invention')
        with patch('careerquest.discovery_guide.groq_discovery', return_value=self.selection()):
            self.assertFalse(self.generate().json()['latest']['is_stale'])

    def test_provider_rejects_oversized_output_and_missing_key_without_leaking(self):
        with connect(self.db) as c: choices = guide.snapshot(c, self.pid)[1]
        with patch('careerquest.discovery_guide.urllib.request.urlopen', return_value=io.BytesIO(b'x' * 48001)):
            with self.assertRaises(ValueError): guide.groq_discovery(10, choices, 'openai/gpt-oss-120b')
        with patch.dict('os.environ', {'GROQ_API_KEY': ''}), patch('careerquest.discovery_guide.urllib.request.urlopen') as send:
            item = self.generate().json()['latest']; self.assertEqual(item['status'], 'fallback'); send.assert_not_called()
        self.assertNotIn('synthetic-test-key', json.dumps(item))

    def test_feedback_rate_limit(self):
        with patch('careerquest.discovery_guide.groq_discovery', return_value=self.selection()): item = self.generate().json()['latest']
        path = self.base + f'/discovery-guide/{item["id"]}/feedback'
        for index in range(20): self.assertEqual(self.client.post(path, json={'verdict': 'Somewhat', 'correction': f'Fictional correction {index}'}).status_code, 200)
        self.assertEqual(self.client.post(path, json={'verdict': 'Yes'}).status_code, 429)


if __name__ == '__main__': unittest.main()
