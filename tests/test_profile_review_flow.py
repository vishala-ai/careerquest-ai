"""One dedicated profile review: mocked Groq, real API/graph/SQLite, fictional only."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from owned_client import TestClient
from careerquest import api, discovery_guide as guide
from careerquest.store import connect


def routing(prompt, model):
    action = next((a for a in ('revise_discovery_story', 'suggest_career_worlds') if a in prompt['available_actions']), 'request_profile_review')
    return {'action': action, 'question_id': 'none', 'world_ids': prompt['approved_world_ids'][:3] if action == 'suggest_career_worlds' else []}


class ProfileReviewFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.path = str(Path(self.temp.name)/'fictional.sqlite3')
        for p in (patch.object(api, 'DB', self.path),
                  patch.dict('os.environ', {'GROQ_API_KEY': 'synthetic-test-key'}),
                  patch('careerquest.discovery_agent.groq_select_tool', side_effect=routing),
                  patch('careerquest.discovery_guide.groq_discovery', side_effect=lambda grade, choices, model, preferences=None: guide.deterministic_summary(choices, preferences))):
            p.start(); self.addCleanup(p.stop)
        self.c = TestClient(api.app); self.addCleanup(self.c.close)
        student = self.c.post('/api/profiles', json={'fictional_ack':True,'alias': 'Fictional Profile Review', 'grade': 9}).json()
        self.pid = student['profile']['id']; self.base = '/api/profiles/'+self.pid
        for step, quest in enumerate(api.QUESTS): self.c.post(self.base+f'/quests/{step}', json={'option': next(iter(quest['options']))})
        self.initial = self.c.post(self.base+'/discovery-agent', json={'event': 'discover'}).json()

    def state(self): return self.c.get(self.base).json()
    def confirm(self, state=None, sid=None, verdict='Yes'):
        state = state or self.state()
        return self.c.post(self.base+'/confirm', json={**state['discovery_outcome']['proposed_profile'], 'review_verdict': verdict, 'review_story_id': sid, 'expected_version': state['profile_version']})

    def test_preview_and_returning_reads_do_not_confirm_or_award_xp(self):
        before = self.state()
        for _ in range(2):
            result = self.c.post(self.base+'/discovery-agent', json={'event': 'discover'}).json()
            self.assertEqual(result['guide']['latest']['id'], self.initial['guide']['latest']['id'])
            self.assertEqual(self.state(), before)
        self.assertEqual(before['profile']['xp'], 60); self.assertFalse(before['confirmed'])
        self.assertIsNone(before['discovery_handoff']['active'])

    def test_yes_receipt_is_separate_from_single_explicit_confirmation(self):
        sid = self.initial['guide']['latest']['id']
        receipt = self.c.post(self.base+'/discovery-agent', json={'event': 'feedback', 'story_id': sid, 'verdict': 'Yes'})
        self.assertEqual(receipt.status_code, 200); self.assertFalse(self.state()['confirmed'])
        self.assertEqual(self.state()['profile']['xp'], 60)
        final = self.confirm(sid=sid).json()
        self.assertEqual(final['profile_preferences']['review_feedback']['verdict'], 'Yes')
        self.assertEqual(final['profile_preferences']['review_feedback']['source'], 'explorer_profile')
        self.assertEqual(final['profile_preferences']['review_feedback']['story_id'], sid)
        self.assertEqual(final['profile']['xp'], 70); self.assertTrue(final['confirmed'])
        self.assertEqual(final['discovery_handoff']['active']['profile_version'], final['profile_version'])
        replay = self.confirm(final, sid=sid)
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.json(), final)

    def test_somewhat_keeps_agreed_interests_and_requires_review_of_new_story(self):
        self._revision('Somewhat', ['technology'], ['art'], {'technology', 'art'})

    def test_not_really_uses_new_preferences_without_overwriting_choices(self):
        self._revision('Not really', [], ['art'], {'art'})

    def _revision(self, verdict, retained, preferred, expected):
        raw = self.state()['quest_answers']; old_sid = self.initial['guide']['latest']['id']
        revised = self.c.post(self.base+'/discovery-agent', json={'event': 'feedback', 'story_id': old_sid, 'verdict': verdict, 'retained_interest_ids': retained, 'preferred_interests': preferred, 'correction': 'For this fictional explorer, explore art.'})
        self.assertEqual(revised.status_code, 200); proposal = revised.json()
        self.assertEqual(set(proposal['outcome']['proposed_profile']['interests']), expected)
        state = self.state(); self.assertFalse(state['confirmed']); self.assertEqual(state['profile']['xp'], 60)
        self.assertEqual(state['quest_answers'], raw); self.assertEqual(len(state['discovery_guide']['history']), 2)
        self.assertEqual(self.confirm(state, sid=old_sid).status_code, 422)
        self.assertEqual(self.confirm(state, verdict=verdict).status_code, 409)
        self.assertEqual(self.c.post(self.base+'/explore', json={'message': 'Explore careers'}).status_code, 409)
        final = self.confirm(state, sid=proposal['guide']['latest']['id']).json()
        self.assertTrue(final['confirmed']); self.assertEqual(final['quest_answers'], raw)
        self.assertTrue(all(w in guide.WORLD_IDS for w in final['discovery_handoff']['active']['suggested_world_ids']))

    def test_manual_revision_persists_feedback_and_is_reviewed_before_confirmation(self):
        original = self.state(); sid = self.initial['guide']['latest']['id']
        draft = self.c.post(self.base+'/draft', json={'interests': ['art'], 'learning_style': 'Creative activities', 'goal': 'Try a mini-project', 'correction': 'A fictional preference for art.', 'review_verdict': 'Not really', 'review_story_id': sid, 'expected_version': original['profile_version']})
        self.assertEqual(draft.status_code, 200); draft = draft.json()
        self.assertFalse(draft['confirmed']); self.assertEqual(draft['profile']['xp'], 60)
        self.assertEqual(draft['profile_draft']['review_feedback']['verdict'], 'Not really')
        changes = draft['profile_draft']['review_feedback']['changes']
        self.assertEqual(changes['added'], ['art']); self.assertEqual(changes['removed'], ['technology', 'science', 'building'])
        self.assertEqual({d['field'] for d in changes['details']}, {'Preferred activities', 'Exploration goal'})
        self.assertEqual(draft['quest_answers'], original['quest_answers'])
        revised = self.c.post(self.base+'/discovery-agent', json={'event': 'discover'}).json()
        self.assertEqual(revised['outcome']['proposed_profile']['interests'], ['art'])
        self.assertIsNone(revised['guide']['latest']['feedback']); self.assertFalse(self.state()['confirmed'])
        final = self.confirm(sid=revised['guide']['latest']['id']).json()
        self.assertEqual(final['discovery_handoff']['active']['suggested_world_ids'], ['design'])
        with connect(self.path) as c:
            old = json.loads(c.execute("SELECT payload FROM events WHERE profile_id=? AND kind='profile_drafted' ORDER BY rowid LIMIT 1", (self.pid,)).fetchone()[0])
        self.assertEqual(old['review_feedback']['verdict'], 'Not really')

    def test_reload_and_fresh_process_keep_manual_review_corrections(self):
        self.c.post(self.base+'/draft', json={'interests': ['art'], 'correction': 'Fictional saved correction.', 'review_verdict': 'Somewhat'})
        expected = self.state()['profile_draft']
        with TestClient(api.app) as reloaded: self.assertEqual(reloaded.get(self.base).json()['profile_draft'], expected)
        script = 'import json,sys; from careerquest.store import connect; from careerquest.profiles import review_state; c=connect(sys.argv[1]); print(json.dumps(review_state(c,sys.argv[2])["profile_draft"]))'
        result = subprocess.run([sys.executable, '-c', script, self.path, self.pid], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), expected)

    def test_confirmed_profile_edit_preserves_handoff_and_plan_then_blocks_research(self):
        self.confirm(sid=self.initial['guide']['latest']['id'])
        plan = self.c.post(self.base+'/roadmap/propose', json={}).json()['plan']
        self.c.post(self.base+'/roadmap/save', json={'plan': plan}); before = self.state()
        self.c.post(self.base+'/draft', json={**before['profile_preferences'], 'start_edit': True})
        edited = self.state(); self.assertFalse(edited['confirmed'])
        self.assertEqual(edited['profile']['xp'], before['profile']['xp'])
        self.assertIsNone(edited['discovery_handoff']['active']); self.assertEqual(edited['latest_plan'], before['latest_plan'])
        self.assertEqual(self.c.post(self.base+'/roadmap/propose', json={}).status_code, 409)
        self.assertEqual(self.c.post(self.base+'/explore', json={'message': 'Explore careers'}).status_code, 409)

    def test_stale_review_source_cannot_partially_save_a_draft(self):
        old = self.initial['guide']['latest']['id']
        self.c.post(self.base+'/draft', json={'interests': ['art']}); before = self.state()
        result = self.c.post(self.base+'/draft', json={'interests': ['science'], 'review_verdict': 'Not really', 'review_story_id': old})
        self.assertEqual(result.status_code, 409); self.assertEqual(self.state(), before)


if __name__ == '__main__': unittest.main()
