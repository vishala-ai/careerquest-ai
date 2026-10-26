"""Synthetic-only final Discovery outcome and confirmation-bound handoffs.

Groq responses are mocked. Real LangGraph, FastAPI and SQLite are exercised.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from owned_client import TestClient
from careerquest import api, discovery_guide as guide
from careerquest.store import connect


def model_policy(prompt, model):
    actions = prompt['available_actions']
    action = next((a for a in ('revise_discovery_story', 'suggest_career_worlds') if a in actions), 'request_profile_review')
    return {'action': action, 'question_id': 'none', 'world_ids': prompt['approved_world_ids'][:3] if action == 'suggest_career_worlds' else []}


class DiscoveryHandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name) / 'fictional.sqlite3')
        for patcher in (
            patch.object(api, 'DB', self.path),
            patch.dict('os.environ', {'GROQ_API_KEY': 'synthetic-test-key', 'GROQ_MODEL': 'openai/gpt-oss-120b'}),
            patch('careerquest.discovery_agent.groq_select_tool', side_effect=model_policy),
            patch('careerquest.discovery_guide.groq_discovery', side_effect=lambda grade, choices, model, preferences=None: guide.deterministic_summary(choices, preferences)),
        ):
            patcher.start(); self.addCleanup(patcher.stop)
        self.client = TestClient(api.app); self.addCleanup(self.client.close)
        self.pid = self.client.post('/api/profiles', json={'fictional_ack':True,'alias': 'Fictional Handoff Explorer', 'grade': 10}).json()['profile']['id']
        self.base = f'/api/profiles/{self.pid}'
        for step, quest in enumerate(api.QUESTS):
            self.assertEqual(self.client.post(self.base + f'/quests/{step}', json={'option': next(iter(quest['options']))}).status_code, 200)

    def state(self): return self.client.get(self.base).json()
    def discover(self):
        response = self.client.post(self.base + '/discovery-agent', json={'event': 'discover'})
        self.assertEqual(response.status_code, 200); return response.json()
    def confirm(self, **overrides):
        values = self.state()['discovery_outcome']['proposed_profile'] | overrides
        return self.client.post(self.base + '/confirm', json=values)
    def handoff(self): return self.state()['discovery_handoff']['active']

    def test_four_part_outcome_is_concise_editable_and_evidence_grounded(self):
        result = self.discover(); outcome = result['outcome']
        self.assertTrue(70 <= len(outcome['story']['summary'].split()) <= 110)
        self.assertEqual(outcome['proposed_profile']['interests'], ['technology', 'science', 'building'])
        self.assertTrue(outcome['pending_confirmation']); self.assertIsNotNone(outcome['next_mission'])
        self.assertLessEqual(len(outcome['career_worlds']), 3)
        ids = {e['id'] for e in outcome['evidence_references']}
        for world in outcome['career_worlds']:
            self.assertIn(world['world_id'], guide.WORLD_IDS)
            self.assertTrue(set(world['choice_ids']) <= ids); self.assertTrue(world['explanation'])
        self.assertIsNone(self.handoff()); self.assertFalse(self.state()['confirmed'])

    def test_incomplete_explorer_has_no_final_outcome_or_personalized_handoff(self):
        student = self.client.post('/api/profiles', json={'fictional_ack':True,'alias': 'Fictional Beginner', 'grade': 9}).json()
        base = '/api/profiles/' + student['profile']['id']
        self.assertIsNone(student['discovery_outcome']); self.assertIsNone(student['discovery_handoff']['active'])
        choice = next(iter(api.QUESTS[0]['options']))
        partial = self.client.post(base + '/quests/0', json={'option': choice}).json()
        self.assertIsNone(partial['discovery_outcome']); self.assertEqual(partial['profile']['xp'], 20)
        self.assertEqual(self.client.post(base + '/confirm', json={'interests': ['art']}).status_code, 409)
        self.assertEqual(self.client.get(base + '/career-worlds').status_code, 409)

    def test_explicit_confirmation_creates_complete_handoff_without_extra_quest_xp(self):
        proposal = self.discover()['outcome']; original = self.state()['quest_answers']
        response = self.confirm(); self.assertEqual(response.status_code, 200)
        state = response.json(); handoff = state['discovery_handoff']['active']
        for key in ('id', 'version', 'student_id', 'profile_version', 'selected_interests', 'suggested_world_ids', 'evidence_references', 'timestamp', 'confirmation_event_id'):
            self.assertIn(key, handoff)
        self.assertEqual(handoff['student_id'], self.pid); self.assertEqual(handoff['profile_version'], state['profile_version'])
        self.assertEqual(handoff['selected_interests'], proposal['proposed_profile']['interests'])
        self.assertEqual(handoff['story'], proposal['story']); self.assertEqual(handoff['next_mission'], proposal['next_mission'])
        self.assertEqual(state['quest_answers'], original); self.assertEqual(state['profile']['xp'], 70)
        ids = {r['id'] for r in handoff['evidence_references']}
        for world in handoff['career_worlds']: self.assertTrue(set(world['choice_ids']) <= ids)
        self.assertEqual(self.client.get(self.base + '/career-worlds').json()['handoff_id'], handoff['id'])

    def test_yes_feedback_does_not_create_handoff_or_bypass_confirmation(self):
        initial = self.discover()
        feedback = self.client.post(self.base + '/discovery-agent', json={'event': 'feedback', 'story_id': initial['guide']['latest']['id'], 'verdict': 'Yes'})
        self.assertEqual(feedback.status_code, 200); self.assertTrue(feedback.json()['outcome']['pending_confirmation'])
        self.assertIsNone(self.handoff()); self.assertEqual(self.state()['profile']['xp'], 60)
        for suffix, body in (('/explore', {'message': 'Explore careers'}), ('/roadmap/propose', {}), ('/roadmap/save', {'plan': {}})):
            self.assertEqual(self.client.post(self.base + suffix, json=body).status_code, 409)
        self.assertEqual(self.client.get(self.base + '/career-worlds').status_code, 409)
        self.assertEqual(self.client.get('/api/career-worlds').status_code, 200)

    def test_invalid_or_unsupported_selected_worlds_reject_without_writes(self):
        before = self.state()
        for ids, interests in ((['invented-world'], ['science']), (['software'], ['art']), (['design', 'design'], ['art'])):
            self.assertEqual(self.confirm(selected_world_ids=ids, interests=interests).status_code, 422)
            self.assertEqual(self.state(), before)

    def test_invalid_persisted_model_candidate_cannot_cross_confirmation(self):
        self.discover()
        with connect(self.path) as c:
            row = c.execute('SELECT * FROM discovery_agent_sessions WHERE profile_id=?', (self.pid,)).fetchone()
            state = json.loads(row['state']); state['recommendations'] = [{'world_id': 'invented-world'}]
            c.execute('UPDATE discovery_agent_sessions SET state=? WHERE id=?', (json.dumps(state), row['id']))
        result = self.confirm(); self.assertEqual(result.status_code, 200)
        handoff = result.json()['discovery_handoff']['active']
        self.assertNotIn('invented-world', handoff['suggested_world_ids'])
        self.assertEqual(handoff['recommendation_method'], 'deterministic_catalogue')

    def test_somewhat_keeps_agreed_interest_and_stores_correction_separately(self):
        self._feedback_case('Somewhat', ['art'], ['technology'], 'Keep technology, but explore art instead of science.', {'art', 'technology'})

    def test_not_really_uses_stated_preferences_over_original_inference(self):
        self._feedback_case('Not really', ['art'], [], 'I prefer art and want a new direction.', {'art'})
        self.assertEqual(self.handoff()['suggested_world_ids'], ['design'])

    def _feedback_case(self, verdict, interests, retained, correction, expected):
        original = self.discover(); raw = self.state()['quest_answers']
        response = self.client.post(self.base + '/discovery-agent', json={'event': 'feedback', 'story_id': original['guide']['latest']['id'], 'verdict': verdict, 'preferred_interests': interests, 'retained_interest_ids': retained, 'correction': correction})
        self.assertEqual(response.status_code, 200); result = response.json()
        self.assertEqual(set(result['outcome']['proposed_profile']['interests']), expected)
        self.assertEqual(result['outcome']['proposed_profile']['correction'], correction)
        self.assertEqual(len(result['guide']['history']), 2); self.assertEqual(self.state()['quest_answers'], raw)
        self.assertIsNone(self.handoff()); self.assertFalse(self.state()['confirmed'])
        state = self.confirm().json(); handoff = state['discovery_handoff']['active']
        self.assertEqual(set(handoff['selected_interests']), expected); self.assertEqual(state['quest_answers'], raw)
        self.assertTrue(any(r['kind'] == 'story_feedback' and r['correction'] == correction for r in handoff['evidence_references']))
        self.assertTrue(any(r['kind'] == 'student_correction' and r['text'] == correction for r in handoff['evidence_references']))

    def test_unsure_profile_has_no_forced_world_and_all_worlds_remain_open(self):
        self.discover()
        state = self.confirm(interests=[], not_sure=True, goal='Not sure yet').json()
        handoff = state['discovery_handoff']['active']
        self.assertTrue(state['confirmed']); self.assertTrue(handoff['exploratory'])
        self.assertEqual(handoff['suggested_world_ids'], [])
        personalized = self.client.get(self.base + '/career-worlds').json()
        self.assertEqual(personalized['career_worlds'], [])
        self.assertEqual({w['world_id'] for w in personalized['all_worlds']}, guide.WORLD_IDS)

    def test_custom_interest_without_catalogue_match_is_valid_and_unforced(self):
        self.assertEqual(self.confirm(interests=['fictional paper weaving'], correction='I choose paper weaving.').status_code, 200)
        self.assertEqual(self.handoff()['selected_interests'], ['fictional paper weaving'])
        self.assertEqual(self.handoff()['suggested_world_ids'], [])

    def test_manual_edits_do_not_promote_a_story_from_different_interests(self):
        old = self.discover()['outcome']['story']
        self.confirm(interests=['art'], correction='Art is my preferred direction.')
        handoff = self.handoff()
        self.assertEqual(handoff['suggested_world_ids'], ['design'])
        self.assertIsNone(handoff['story']); self.assertIsNone(handoff['next_mission'])
        self.assertEqual(handoff['source_story_id'], old['id'])

    def test_profile_changes_invalidate_personalization_preserve_versions_and_plans(self):
        self.discover(); self.confirm(); first = self.handoff()
        plan = self.client.post(self.base + '/roadmap/propose', json={}).json()['plan']
        self.client.post(self.base + '/roadmap/save', json={'plan': plan})
        self.client.post(self.base + '/draft', json={'interests': ['art'], 'correction': 'Explore art now.', 'start_edit': True})
        state = self.state(); self.assertIsNone(state['discovery_handoff']['active'])
        self.assertTrue(state['discovery_handoff']['latest']['is_stale']); self.assertEqual(state['latest_plan']['version'], 1)
        self.assertEqual(self.client.get(self.base + '/career-worlds').status_code, 409)
        self.assertEqual(self.client.post(self.base + '/roadmap/propose', json={}).status_code, 409)
        state = self.confirm().json(); second = state['discovery_handoff']['active']
        self.assertEqual(second['version'], first['version'] + 1); self.assertGreater(second['profile_version'], first['profile_version'])
        self.assertEqual(second['suggested_world_ids'], ['design']); self.assertEqual(state['latest_plan']['content'], plan)
        archived = dict(state['discovery_handoff']['history'][0]); archived.pop('is_stale')
        prior = dict(first); prior.pop('is_stale'); self.assertEqual(archived, prior)

    def test_changed_quest_invalidates_handoff_without_duplicate_xp(self):
        self.confirm(); before = self.state()
        self.client.post(self.base + '/quests/0', json={'option': list(api.QUESTS[0]['options'])[1], 'revise': True})
        after = self.state(); self.assertFalse(after['confirmed']); self.assertIsNone(self.handoff())
        self.assertEqual(after['profile']['xp'], before['profile']['xp'])
        self.assertEqual(self.client.get(self.base + '/career-worlds').status_code, 409)
        self.assertEqual(self.client.get('/api/career-worlds').status_code, 200)

    def test_confirmation_retry_is_idempotent_and_opt_out_is_versioned_without_xp(self):
        self.discover(); self.confirm(); before = self.state()
        self.confirm(); self.assertEqual(self.state(), before)
        after = self.confirm(selected_world_ids=[]).json()
        self.assertEqual(len(after['discovery_handoff']['history']), 2)
        self.assertEqual(after['profile']['xp'], before['profile']['xp'])
        self.assertEqual(after['discovery_handoff']['active']['suggested_world_ids'], [])
        self.assertEqual(after['discovery_outcome']['career_worlds'], [])

    def test_concurrent_confirmation_does_not_duplicate_handoff_or_xp(self):
        def confirm_once(_):
            with TestClient(api.app) as client:
                return client.post(self.base + '/confirm', json={'interests': ['art'], 'expected_version': 1}).status_code
        with ThreadPoolExecutor(max_workers=2) as executor:
            self.assertEqual(list(executor.map(confirm_once, range(2))), [200, 200])
        state = self.state()
        self.assertEqual(state['profile']['xp'], 70)
        self.assertEqual(state['confirmation_version'], 1)
        self.assertEqual(len(state['discovery_handoff']['history']), 1)

    def test_handoff_survives_fresh_process_without_model_or_new_writes(self):
        self.discover(); self.confirm(); expected = self.state()['discovery_handoff']
        code = 'import json,sys; from careerquest.store import connect; from careerquest.discovery_handoff import handoff_state; c=connect(sys.argv[1]); print(json.dumps(handoff_state(c,sys.argv[2]),sort_keys=True)); c.close()'
        result = subprocess.run([sys.executable, '-c', code, self.path, self.pid], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout), expected)
        with TestClient(api.app) as fresh: self.assertEqual(fresh.get(self.base).json()['discovery_handoff'], expected)

    def test_handoff_failure_rolls_back_confirmation_and_xp(self):
        before = self.state()
        with patch('careerquest.discovery_handoff.persist', side_effect=RuntimeError('Synthetic storage outage')):
            with self.assertRaises(RuntimeError): self.confirm()
        self.assertEqual(self.state(), before)

    def test_empty_catalogue_does_not_invent_worlds(self):
        with patch('careerquest.discovery_guide.approved_worlds', return_value=[]):
            self.assertEqual(self.confirm().status_code, 200)
            self.assertEqual(self.handoff()['suggested_world_ids'], [])
            self.assertEqual(self.client.get('/api/career-worlds').json(), [])

    def test_legacy_confirmation_is_not_backfilled_until_explicit_reconfirmation(self):
        self.confirm()
        with connect(self.path) as c: c.execute('DELETE FROM discovery_handoffs')
        before = self.state(); self.assertTrue(before['confirmed']); self.assertIsNone(self.handoff())
        self.assertEqual(self.client.get(self.base + '/career-worlds').status_code, 409)
        after = self.confirm().json()
        self.assertEqual(after['profile']['xp'], before['profile']['xp'])
        self.assertEqual(after['confirmation_version'], before['confirmation_version'])
        self.assertIsNotNone(after['discovery_handoff']['active'])


if __name__ == '__main__': unittest.main()
