"""Refined story workflow tests. Groq is mocked; all students/databases are fictional."""
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


class DiscoveryFeedbackWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.db = str(Path(self.tmp.name) / 'fictional.db')
        override = patch.object(api, 'DB', self.db); override.start(); self.addCleanup(override.stop)
        env = patch.dict('os.environ', {'GROQ_API_KEY': 'synthetic-test-key', 'GROQ_MODEL': 'openai/gpt-oss-120b'})
        env.start(); self.addCleanup(env.stop)
        self.client = TestClient(api.app); self.addCleanup(self.client.close)
        self.pid = self.client.post('/api/profiles', json={'fictional_ack':True,'alias': 'Nova Fictional', 'grade': 11}).json()['profile']['id']
        self.base = f'/api/profiles/{self.pid}'
        for index, quest in enumerate(api.QUESTS): self.client.post(self.base + f'/quests/{index}', json={'option': next(iter(quest['options']))})
        self.model = patch('careerquest.discovery_guide.groq_discovery', side_effect=lambda grade, choices, model, preferences=None: guide.deterministic_summary(choices, preferences))
        self.provider = self.model.start(); self.addCleanup(self.model.stop)

    def state(self): return self.client.get(self.base).json()
    def generate(self, retry=False): return self.client.post(self.base + '/discovery-guide', json={'retry': retry})
    def revise(self, sid, verdict='Somewhat', correction='Explore art instead of science.', interests=None, retained=None):
        return self.client.post(self.base + f'/discovery-guide/{sid}/revise', json={'verdict': verdict, 'correction': correction, 'preferred_interests': interests or ['art'], 'retained_interest_ids': retained or []})

    def test_concise_story_optional_mission_and_exact_sources(self):
        item = self.generate().json()['latest']
        self.assertTrue(70 <= len(item['content']['summary'].split()) <= 110)
        self.assertLessEqual(len(item['content']['interest_clues']), 3)
        self.assertLessEqual(len(item['content']['what_you_could_try_next']), 1)
        self.assertIsInstance(item['content']['mini_mission'], dict)
        for answer in item['source_answers']: self.assertNotIn(answer['choice'], item['content']['summary'])
        self.assertEqual(item['diagnostics']['reason'], 'validated')
        self.assertEqual(item['recommendation_source'], 'groq')

    def test_valid_but_empty_model_worlds_use_labeled_catalogue_fallback(self):
        def empty(grade, choices, model, preferences=None):
            result = guide.deterministic_summary(choices, preferences); result['career_worlds'] = []; return result
        with patch('careerquest.discovery_guide.groq_discovery', side_effect=empty): item = self.generate().json()['latest']
        self.assertEqual(item['status'], 'groq')
        self.assertEqual(item['recommendation_source'], 'catalogue_fallback')
        self.assertEqual(item['diagnostics']['reason'], 'empty_model_worlds')
        self.assertTrue(item['content']['career_worlds'])
        self.assertTrue(all(w['world_id'] in guide.WORLD_IDS and w['choice_ids'] for w in item['content']['career_worlds']))

    def test_invalid_worlds_and_fabricated_choices_are_rejected_with_reason_codes(self):
        with connect(self.db) as c: choices = guide.snapshot(c, self.pid)[1]
        invalid = guide.deterministic_summary(choices); invalid['career_worlds'][0]['world_id'] = 'unsupported-world'
        with patch('careerquest.discovery_guide.groq_discovery', return_value=invalid): item = self.generate().json()['latest']
        self.assertEqual(item['status'], 'fallback'); self.assertEqual(item['diagnostics']['reason'], 'unsupported_world_or_evidence')
        self.assertNotIn('unsupported-world', [w['world_id'] for w in item['content']['career_worlds']])
        invalid = guide.deterministic_summary(choices); invalid['what_you_chose'][0]['choice'] = 'Won a competition'
        with patch('careerquest.discovery_guide.groq_discovery', return_value=invalid): item = self.generate(True).json()['latest']
        self.assertEqual(item['diagnostics']['reason'], 'fabricated_or_duplicate_choice')
        self.assertNotIn('Won a competition', json.dumps(item['content']))

    def test_yes_saves_agreement_without_confirming_or_awarding_points(self):
        item = self.generate().json()['latest']; before = self.state()
        response = self.client.post(self.base + f'/discovery-guide/{item["id"]}/feedback', json={'verdict': 'Yes'})
        self.assertEqual(response.status_code, 200); self.assertEqual(response.json()['latest']['feedback']['verdict'], 'Yes')
        self.assertEqual(self.state()['profile'], before['profile']); self.assertFalse(self.state()['confirmed'])
        self.assertEqual(self.state()['quest_answers'], before['quest_answers'])
        self.assertEqual(self.client.post(self.base + '/roadmap/propose', json={}).status_code, 409)

    def test_somewhat_requires_correction_and_preferences_atomically(self):
        item = self.generate().json()['latest']; before = self.state()
        self.assertEqual(self.revise(item['id'], correction=' ').status_code, 409)
        self.assertEqual(self.revise(item['id'], retained=['fabricated']).status_code, 409)
        self.assertEqual(self.revise(item['id'], retained=['technology', 'science', 'building']).status_code, 409)
        self.assertEqual(self.client.post(self.base + f'/discovery-guide/{item["id"]}/revise', json={'verdict': 'Somewhat', 'correction': 'Explore art', 'preferred_interests': []}).status_code, 422)
        self.assertEqual(self.state(), before)

    def test_somewhat_preserves_agreed_clues_and_revises_proposal_with_changes(self):
        original = self.generate().json()['latest']; before = self.state()
        response = self.revise(original['id'], retained=['technology']); self.assertEqual(response.status_code, 200)
        data = response.json(); item = data['latest']
        self.assertEqual(item['version'], 2); self.assertFalse(item['is_stale'])
        self.assertEqual({i['interest_id'] for i in item['content']['interest_clues']}, {'technology', 'art'})
        self.assertEqual(item['changes']['kept'], ['technology'])
        self.assertEqual(item['changes']['added'], ['art']); self.assertEqual(item['changes']['removed'], ['building', 'science'])
        self.assertTrue(data['history'][0]['recommendations_stale']); self.assertEqual(data['history'][0]['content'], original['content'])
        saved = self.state(); self.assertEqual(saved['quest_answers'], before['quest_answers'])
        self.assertEqual(saved['profile']['xp'], 60); self.assertFalse(saved['confirmed'])
        self.assertEqual(saved['profile_draft']['interests'], ['technology', 'art'])
        self.assertEqual(saved['profile_draft']['correction'], 'Explore art instead of science.')
        calls = self.provider.call_count
        repeated = self.revise(original['id'], retained=['technology']).json()
        self.assertEqual(repeated, data); self.assertEqual(self.provider.call_count, calls)
        with TestClient(api.app) as reload: self.assertEqual(reload.get(self.base).json()['discovery_guide'], data)

    def test_not_really_replaces_inference_and_preserves_confirmed_profile_and_plan(self):
        self.client.post(self.base + '/confirm', json={'interests': ['technology']})
        plan = self.client.post(self.base + '/roadmap/propose', json={}).json()['plan']
        self.client.post(self.base + '/roadmap/save', json={'plan': plan})
        item = self.generate().json()['latest']; before = self.state()
        response = self.revise(item['id'], verdict='Not really', correction='Prefer design.', interests=['design'], retained=['technology'])
        self.assertEqual(response.status_code, 200)
        fresh = response.json()['latest']
        self.assertEqual(fresh['preferences']['interests'], ['design']); self.assertEqual(fresh['preferences']['retained'], [])
        self.assertEqual([c['interest_id'] for c in fresh['content']['interest_clues']], ['design'])
        self.assertEqual([w['world_id'] for w in fresh['content']['career_worlds']], ['design'])
        self.assertTrue(all(i.startswith('preference:') for w in fresh['content']['career_worlds'] for i in w['choice_ids']))
        after = self.state(); self.assertEqual(after['quest_answers'], before['quest_answers'])
        self.assertEqual(after['profile'], before['profile']); self.assertEqual(after['profile_preferences'], before['profile_preferences'])
        self.assertEqual(after['latest_plan'], before['latest_plan']); self.assertFalse(after['confirmed'])
        for path, body in [('/explore', {'message': 'Explore careers'}), ('/roadmap/propose', {}), ('/roadmap/save', {'plan': plan})]:
            self.assertEqual(self.client.post(self.base + path, json=body).status_code, 409)

    def test_model_cannot_override_stated_preferences_with_old_quest_inferences(self):
        item = self.generate().json()['latest']
        def ignore_preferences(grade, choices, model, preferences=None): return guide.deterministic_summary(choices)
        with patch('careerquest.discovery_guide.groq_discovery', side_effect=ignore_preferences): fresh = self.revise(item['id'], verdict='Not really', interests=['design']).json()['latest']
        self.assertEqual(fresh['status'], 'fallback')
        self.assertEqual([c['interest_id'] for c in fresh['content']['interest_clues']], ['design'])
        self.assertTrue(all('design' == w['world_id'] for w in fresh['content']['career_worlds']))

    def test_three_revision_limit_and_manual_interests_still_work(self):
        item = self.generate().json()['latest']; original_answers = self.state()['quest_answers']
        for interest in ['art', 'science', 'design']:
            response = self.revise(item['id'], verdict='Not really', interests=[interest])
            self.assertEqual(response.status_code, 200); item = response.json()['latest']
        before = self.state(); count = self.provider.call_count
        self.assertEqual(self.revise(item['id'], verdict='Not really', interests=['nature']).status_code, 429)
        self.assertEqual(self.state(), before); self.assertEqual(self.provider.call_count, count)
        self.assertEqual(before['discovery_guide']['revisions_remaining'], 0)
        manual = self.client.post(self.base + '/draft', json={'interests': ['nature'], 'correction': 'Manual fictional preference', 'expected_version': before['profile_version']})
        self.assertEqual(manual.status_code, 200); self.assertEqual(manual.json()['profile_draft']['interests'], ['nature'])
        self.assertEqual(manual.json()['quest_answers'], original_answers); self.assertEqual(manual.json()['profile']['xp'], 60)
        self.assertFalse(manual.json()['confirmed']); self.assertEqual(self.provider.call_count, count)

    def test_profile_and_story_changes_archive_old_recommendations(self):
        old = self.generate().json()['latest']; raw = self.state()['quest_answers']
        newer = self.generate(True).json(); self.assertTrue(newer['history'][0]['recommendations_stale'])
        self.client.post(self.base + '/confirm', json={'interests': ['design']})
        changed = self.state(); self.assertTrue(changed['discovery_guide']['latest']['is_stale'])
        fresh = self.generate().json(); self.assertNotEqual(fresh['latest']['response_version'], old['response_version'])
        self.assertEqual([c['interest_id'] for c in fresh['latest']['content']['interest_clues']], ['design'])
        self.assertTrue(all(w['world_id'] == 'design' for w in fresh['latest']['content']['career_worlds']))
        self.assertEqual(self.state()['quest_answers'], raw)

    def test_empty_catalogue_unknown_preferences_and_provider_errors_are_honest(self):
        with patch('careerquest.discovery_guide.records', return_value=[]):
            item = self.generate().json()['latest']
            self.assertEqual(item['recommendation_source'], 'unavailable'); self.assertEqual(item['diagnostics']['reason'], 'empty_catalogue')
            self.assertEqual(item['content']['career_worlds'], []); self.provider.assert_not_called()
        item = self.generate(True).json()['latest']
        unknown = self.revise(item['id'], verdict='Not really', interests=['music']).json()['latest']
        self.assertEqual(unknown['preferences']['interests'], ['music'])
        self.assertEqual(unknown['recommendation_source'], 'unavailable'); self.assertEqual(unknown['content']['career_worlds'], [])
        self.assertTrue(70 <= len(unknown['content']['summary'].split()) <= 110)
        for exception in [TimeoutError(), json.JSONDecodeError('invalid', 'x', 0)]:
            with patch('careerquest.discovery_guide.groq_discovery', side_effect=exception):
                fallback = self.generate(True).json()['latest']; self.assertEqual(fallback['status'], 'fallback')
                self.assertEqual(fallback['preferences']['interests'], ['music'])
        self.assertEqual(self.state()['profile']['xp'], 60)

    def test_revision_prompt_uses_only_current_correction_and_authoritative_evidence(self):
        item = self.generate().json()['latest']
        self.model.stop()
        captured = []
        def response(request, timeout):
            body = json.loads(request.data); captured.append(body)
            context = json.loads(body['messages'][1]['content'])
            selection = guide.deterministic_summary(context['saved_choices'], context.get('stated_preferences'))
            return io.BytesIO(json.dumps({'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(selection)}}]}).encode())
        with patch('careerquest.discovery_guide.urllib.request.urlopen', side_effect=response):
            revised = self.revise(item['id'], retained=['technology']).json()['latest']
        self.assertEqual(revised['status'], 'groq')
        context = json.loads(captured[0]['messages'][1]['content'])
        self.assertEqual(context['stated_preferences']['correction'], 'Explore art instead of science.')
        self.assertEqual(context['stated_preferences']['interests'], ['technology', 'art'])
        self.assertNotIn('Nova Fictional', json.dumps(context)); self.assertNotIn('synthetic-test-key', json.dumps(captured))
        self.assertNotIn('roadmap', context); self.assertNotIn('profile_preferences', context)

    def test_manual_profile_keeps_all_preferences_beyond_three_displayed_clues(self):
        self.client.post(self.base + '/draft', json={'interests': ['music', 'dance', 'history', 'biology'], 'correction': 'Fictional manually edited interests'})
        item = self.generate().json()['latest']
        self.assertEqual(item['preferences']['interests'], ['music', 'dance', 'history', 'biology'])
        self.assertLessEqual(len(item['content']['interest_clues']), 3)
        self.assertTrue(item['content']['career_worlds'])
        self.assertTrue(all(w['world_id'] in ('bioengineering', 'environment') for w in item['content']['career_worlds']))

    def test_somewhat_can_keep_one_clue_without_inventing_new_preferences(self):
        item = self.generate().json()['latest']
        response = self.client.post(self.base + f'/discovery-guide/{item["id"]}/revise', json={'verdict': 'Somewhat', 'correction': 'Keep only technology for now.', 'retained_interest_ids': ['technology']})
        self.assertEqual(response.status_code, 200)
        fresh = response.json()['latest']
        self.assertEqual(fresh['preferences']['interests'], ['technology'])
        self.assertEqual(fresh['changes']['kept'], ['technology'])
        self.assertEqual(fresh['changes']['removed'], ['building', 'science'])
