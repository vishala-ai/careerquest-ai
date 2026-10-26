"""Bounded Discovery Agent tests: mocked model decisions, real LangGraph and SQLite."""
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from owned_client import TestClient
from careerquest import api, discovery_agent as agent, discovery_guide as guide
from careerquest.store import connect


def decision(action, question='none', worlds=None):
    return {'action': action, 'question_id': question, 'world_ids': worlds or []}


def policy(prompt, model):
    actions = prompt['available_actions']
    if 'ask_clarifying_question' in actions and not prompt['information_complete']:
        q = 'correction' if prompt['feedback']['verdict'] == 'Somewhat' and len(prompt['feedback']['correction']) < 3 else 'preferred_interests'
        return decision('ask_clarifying_question', q)
    if 'revise_discovery_story' in actions: return decision('revise_discovery_story')
    if 'suggest_career_worlds' in actions: return decision('suggest_career_worlds', worlds=prompt['approved_world_ids'][:3])
    return decision('request_profile_review')


class DiscoveryAgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.db = str(Path(self.temp.name)/'fictional.sqlite3')
        db = patch.object(api, 'DB', self.db); db.start(); self.addCleanup(db.stop)
        env = patch.dict('os.environ', {'GROQ_API_KEY': 'synthetic-test-key', 'GROQ_MODEL': 'openai/gpt-oss-120b'}); env.start(); self.addCleanup(env.stop)
        self.c = TestClient(api.app); self.addCleanup(self.c.close)
        self.pid = self.c.post('/api/profiles', json={'fictional_ack':True,'alias': 'Fictional Agent Explorer', 'grade': 11}).json()['profile']['id']
        self.base = f'/api/profiles/{self.pid}'
        for step, quest in enumerate(api.QUESTS): self.c.post(self.base+f'/quests/{step}', json={'option': next(iter(quest['options']))})
        self.real_selector = agent.groq_select_tool
        select = patch('careerquest.discovery_agent.groq_select_tool', side_effect=policy); self.selector = select.start(); self.addCleanup(select.stop)
        story = patch('careerquest.discovery_guide.groq_discovery', side_effect=lambda grade, choices, model, preferences=None: guide.deterministic_summary(choices, preferences)); self.story = story.start(); self.addCleanup(story.stop)

    def call(self, **body): return self.c.post(self.base+'/discovery-agent', json=body or {'event': 'discover'})
    def state(self): return self.c.get(self.base).json()
    def initial(self):
        response = self.call(); self.assertEqual(response.status_code, 200); return response.json()
    def feedback(self, initial, verdict='Not really', interests=None, correction='', retained=None):
        return self.call(event='feedback', story_id=initial['guide']['latest']['id'], verdict=verdict, preferred_interests=interests or [], correction=correction, retained_interest_ids=retained or [])

    def test_model_directed_graph_tools_sources_and_cached_reload(self):
        before = self.state(); result = self.initial(); trace = result['agent']['trace']
        self.assertEqual([d['action'] for d in trace], ['revise_discovery_story', 'suggest_career_worlds', 'request_profile_review'])
        self.assertEqual([d['method'] for d in trace], ['groq', 'groq', 'bounded_policy'])
        self.assertEqual(result['agent']['engine'], 'langgraph')
        self.assertTrue(result['agent']['pending_confirmation']); self.assertFalse(result['agent']['fallback_used'])
        for world in result['agent']['recommendations']:
            self.assertIn(world['world_id'], guide.WORLD_IDS); self.assertTrue(world['choice_ids']); self.assertFalse(world['live_verified'])
        calls = self.selector.call_count; self.assertEqual(self.call().json(), result); self.assertEqual(calls, self.selector.call_count)
        with TestClient(api.app) as reload: self.assertEqual(reload.get(self.base).json()['discovery_agent'], result['agent'])
        self.assertEqual(self.state()['profile'], before['profile']); self.assertEqual(self.state()['quest_answers'], before['quest_answers'])

    def test_model_can_choose_question_even_when_fixed_policy_would_revise(self):
        initial = self.initial()
        with patch('careerquest.discovery_agent.groq_select_tool', return_value=decision('ask_clarifying_question', 'keep_clues')):
            result = self.feedback(initial, interests=['design']).json()
        self.assertEqual(result['agent']['status'], 'awaiting_clarification')
        self.assertEqual(result['agent']['trace'][0]['method'], 'groq')
        self.assertEqual(result['agent']['question']['id'], 'keep_clues')
        self.assertEqual(len(result['guide']['history']), len(initial['guide']['history']))
        self.assertFalse(self.state()['confirmed'])

    def test_feedback_missing_information_persists_question_and_resumes(self):
        initial = self.initial(); before = self.state()
        first = self.feedback(initial).json(); question = first['agent']['question']
        self.assertEqual(question['id'], 'preferred_interests')
        self.assertEqual(first['agent']['status'], 'awaiting_clarification')
        self.assertEqual(self.call().json(), first)
        with TestClient(api.app) as restarted:
            saved = restarted.post(self.base+'/discovery-agent', json={'event': 'resume', 'session_id': first['agent']['session_id']}).json()
        self.assertEqual(saved, first)
        reply = self.call(event='clarify', session_id=first['agent']['session_id'], question_id=question['id'], preferred_interests=['design'])
        self.assertEqual(reply.status_code, 200)
        result = reply.json(); self.assertEqual(result['agent']['status'], 'pending_profile_confirmation')
        self.assertEqual(self.state()['profile_draft']['interests'], ['design'])
        self.assertTrue(all(w['world_id'] == 'design' for w in result['agent']['recommendations']))
        self.assertEqual(self.state()['quest_answers'], before['quest_answers']); self.assertEqual(self.state()['profile']['xp'], 60)
        self.assertFalse(self.state()['confirmed'])

    def test_somewhat_partial_feedback_two_question_cap_and_manual_escape(self):
        initial = self.initial()
        first = self.feedback(initial, verdict='Somewhat').json()
        self.assertEqual(first['agent']['question']['id'], 'correction')
        second = self.call(event='clarify', session_id=first['agent']['session_id'], question_id='correction', correction='I would prefer a different direction.').json()
        self.assertEqual(second['agent']['question']['id'], 'preferred_interests')
        self.assertEqual(second['agent']['clarifications_remaining'], 0)
        third = self.call(event='clarify', session_id=first['agent']['session_id'], question_id='preferred_interests', preferred_interests=['art']).json()
        self.assertEqual(third['agent']['status'], 'pending_profile_confirmation')
        self.assertEqual(sum(d['action'] == 'ask_clarifying_question' for d in third['agent']['trace']), 2)
        with patch('careerquest.discovery_agent.groq_select_tool', return_value=decision('ask_clarifying_question', 'preferred_interests')):
            exhausted = self.feedback(third, verdict='Not really').json()
        self.assertIsNone(exhausted['agent']['question']); self.assertTrue(exhausted['agent']['fallback_used'])
        self.assertEqual(exhausted['agent']['status'], 'pending_profile_confirmation')
        # Manual editing still uses the original draft API and cannot confirm a profile.
        current = self.state(); manual = self.c.post(self.base+'/draft', json={'interests': ['biology'], 'expected_version': current['profile_version']}).json()
        self.assertEqual(manual['profile_draft']['interests'], ['biology']); self.assertFalse(manual['confirmed'])

    def test_sufficient_somewhat_revises_and_preserves_kept_clue_and_history(self):
        initial = self.initial(); before = self.state()
        result = self.feedback(initial, verdict='Somewhat', interests=['art'], retained=['technology'], correction='Keep technology but explore art.').json()
        self.assertIsNone(result['agent']['question'])
        self.assertEqual(result['agent']['changes']['kept'], ['technology'])
        self.assertEqual(result['agent']['changes']['added'], ['art'])
        self.assertEqual({c['interest_id'] for c in result['guide']['latest']['content']['interest_clues']}, {'technology', 'art'})
        self.assertEqual(result['guide']['history'][0]['content'], initial['guide']['latest']['content'])
        self.assertTrue(result['guide']['history'][0]['recommendations_stale'])
        again = self.feedback(initial, verdict='Somewhat', interests=['art'], retained=['technology'], correction='Keep technology but explore art.')
        self.assertEqual(again.json(), result)
        self.assertEqual(self.state()['profile'], before['profile']); self.assertEqual(self.state()['quest_answers'], before['quest_answers'])

    def test_yes_is_explicit_policy_review_not_model_confirmation(self):
        initial = self.initial(); calls = self.selector.call_count
        result = self.feedback(initial, verdict='Yes').json()
        self.assertEqual(result['agent']['trace'][0]['action'], 'request_profile_review')
        self.assertEqual(result['agent']['trace'][0]['method'], 'bounded_policy')
        self.assertEqual(result['agent']['recommendations'], initial['agent']['recommendations'])
        self.assertEqual(self.selector.call_count, calls); self.assertFalse(self.state()['confirmed'])
        self.assertEqual(self.c.post(self.base+'/roadmap/propose', json={}).status_code, 409)
        confirmed = self.c.post(self.base+'/confirm', json={'interests': ['art']}).json()
        self.assertTrue(confirmed['confirmed']); self.assertTrue(confirmed['discovery_agent']['is_stale'])
        self.assertEqual(confirmed['discovery']['quest_xp'], 60)
        self.assertEqual(self.c.post(self.base+'/roadmap/propose', json={}).status_code, 200)

    def test_invalid_actions_inputs_and_world_ids_never_execute(self):
        with patch('careerquest.discovery_agent.groq_select_tool', return_value={'action': 'submit_application', 'question_id': 'none', 'world_ids': []}):
            result = self.initial()
        self.assertTrue(result['agent']['fallback_used'])
        self.assertTrue(all(d['action'] in agent.ACTIONS for d in result['agent']['trace']))
        self.assertNotIn('submit_application', json.dumps(result['agent']))
        self.assertEqual(self.call(event='discover', action='confirm_profile').status_code, 422)
        self.assertEqual(self.call(event='discover', profile_id='another').status_code, 422)
        with patch('careerquest.discovery_agent.groq_select_tool', return_value=decision('suggest_career_worlds', worlds=['invented-world'])):
            result = self.call(event='discover', retry=True, request_id='invalid-world').json()
        self.assertTrue(result['agent']['fallback_used'])
        self.assertTrue(all(w['world_id'] in guide.WORLD_IDS for w in result['agent']['recommendations']))
        with patch('careerquest.discovery_agent.groq_select_tool', return_value={'action': 'revise_discovery_story'}):
            malformed = self.call(event='discover', retry=True, request_id='missing-input-fields').json()
        self.assertEqual(malformed['agent']['trace'][0]['method'], 'bounded_policy_fallback')

    def test_model_errors_are_labeled_and_safe_http_status_is_saved(self):
        errors = [TimeoutError(), json.JSONDecodeError('bad', 'x', 0), HTTPError('https://api.groq.com', 429, 'synthetic rate limit', {}, None)]
        for index, error in enumerate(errors):
            with patch('careerquest.discovery_agent.groq_select_tool', side_effect=error):
                result = self.call(event='discover', retry=True, request_id=f'failure-{index}').json()
            self.assertTrue(result['agent']['fallback_used'])
            self.assertTrue(any(d['method'] == 'bounded_policy_fallback' for d in result['agent']['trace']))
            self.assertNotIn('synthetic-test-key', json.dumps(result))
        self.assertEqual(result['agent']['trace'][0]['error']['http_status'], 429)
        self.assertEqual(self.state()['profile']['xp'], 60)

    def test_stale_questions_and_recommendations_after_quest_or_profile_edit(self):
        initial = self.initial(); pending = self.feedback(initial).json()
        self.c.post(self.base+'/quests/0', json={'option': 'Sketch an invention', 'revise': True})
        before = self.state(); self.assertTrue(before['discovery_agent']['is_stale']); self.assertIsNone(before['discovery_agent']['question'])
        self.assertEqual(self.call(event='clarify', session_id=pending['agent']['session_id'], question_id='preferred_interests', preferred_interests=['art']).status_code, 409)
        self.assertEqual(self.state(), before)
        fresh = self.call().json(); self.assertFalse(fresh['agent']['is_stale'])
        current = self.state(); self.c.post(self.base+'/draft', json={'interests': ['design'], 'expected_version': current['profile_version']})
        self.assertTrue(self.state()['discovery_agent']['is_stale'])
        self.assertEqual(self.state()['profile']['xp'], 60)

    def test_profile_change_during_model_selection_prevents_stale_tool_execution(self):
        def change(prompt, model):
            self.c.post(self.base+'/quests/0', json={'option': 'Sketch an invention', 'revise': True})
            return decision('revise_discovery_story')
        with patch('careerquest.discovery_agent.groq_select_tool', side_effect=change): result = self.call()
        self.assertEqual(result.status_code, 409); self.story.assert_not_called()
        self.assertTrue(self.state()['discovery_agent']['is_stale'])
        # A stale turn does not hold a working lease or block a fresh invocation.
        self.assertEqual(self.call().status_code, 200)

    def test_three_revision_limit_includes_legacy_and_manual_still_available(self):
        result = self.initial()
        for interest in ['art', 'science', 'design']:
            result = self.feedback(result, interests=[interest]).json()
        before = self.state(); self.assertEqual(before['discovery_guide']['revisions_remaining'], 0)
        self.assertEqual(self.feedback(result, interests=['biology']).status_code, 429)
        self.assertEqual(self.state(), before)
        self.assertEqual(self.c.post(self.base+'/discovery-guide/'+result['guide']['latest']['id']+'/revise', json={'verdict': 'Not really', 'preferred_interests': ['biology']}).status_code, 429)
        self.assertEqual(self.c.post(self.base+'/draft', json={'interests': ['biology'], 'expected_version': before['profile_version']}).status_code, 200)
        self.assertFalse(self.state()['confirmed'])

    def test_unapproved_tool_output_is_blocked_without_sources(self):
        actual = agent.execute_tool
        def bad(c, state, decision):
            out = actual(c, state, decision)
            if decision['action'] == 'suggest_career_worlds': out['recommendations'][0]['world_id'] = 'fake-world'
            return out
        with patch('careerquest.discovery_agent.execute_tool', side_effect=bad): result = self.initial()
        self.assertEqual(result['agent']['status'], 'manual_edit')
        self.assertEqual(result['agent']['recommendations'], [])
        self.assertNotIn('fake-world', json.dumps(result['agent']))
        self.assertTrue(result['agent']['fallback_used'])

    def test_request_limit_and_no_partial_feedback_writes(self):
        initial = self.initial()
        for index in range(9):
            self.assertEqual(self.call(event='feedback', story_id=initial['guide']['latest']['id'], verdict='Yes', request_id=f'agreement-{index}').status_code, 200)
        before = self.state()
        self.assertEqual(self.call(event='feedback', story_id=initial['guide']['latest']['id'], verdict='Yes', request_id='over-limit').status_code, 429)
        self.assertEqual(self.state(), before)
        with connect(self.db) as c: self.assertEqual(c.execute('SELECT COUNT(*) FROM discovery_agent_turns').fetchone()[0], 10)

    def test_crash_after_story_write_resumes_in_new_process_without_duplicate_story_or_xp(self):
        script = '''import os,sys
from unittest.mock import patch
from careerquest import discovery_agent as a,discovery_guide as g
from careerquest.store import connect
c=connect(sys.argv[1])
a.groq_select_tool=lambda prompt,model:{'action':'revise_discovery_story','question_id':'none','world_ids':[]}
g.groq_discovery=lambda grade,choices,model,preferences=None:g.deterministic_summary(choices,preferences)
a.commit_tool_result=lambda *args,**kwargs:os._exit(73)
a.run_discovery_agent(c,sys.argv[2],a.AgentRequest(event='discover'))
'''
        child = subprocess.run([sys.executable, '-c', script, self.db, self.pid], cwd=str(Path(__file__).resolve().parents[1]), capture_output=True, text=True, timeout=15)
        self.assertEqual(child.returncode, 73, child.stderr)
        with connect(self.db) as c:
            session = c.execute('SELECT id FROM discovery_agent_sessions').fetchone()[0]
            self.assertEqual(c.execute('SELECT COUNT(*) FROM discovery_stories').fetchone()[0], 1)
            self.assertEqual(c.execute('SELECT status FROM discovery_agent_decisions').fetchone()[0], 'selected')
        self.story.reset_mock()
        resumed = self.call(event='resume', session_id=session)
        self.assertEqual(resumed.status_code, 200)
        self.story.assert_not_called()
        with connect(self.db) as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM discovery_stories').fetchone()[0], 1)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM discovery_agent_decisions').fetchone()[0], 3)
        self.assertEqual(self.state()['profile']['xp'], 60)
        self.assertEqual(resumed.json()['agent']['status'], 'pending_profile_confirmation')

    def test_missing_langgraph_is_explicit_service_fallback(self):
        with patch('careerquest.graph.build_discovery_graph', side_effect=ImportError): result = self.initial()
        self.assertEqual(result['agent']['engine'], 'bounded_service_fallback')
        self.assertEqual(result['engine'], 'bounded_service_fallback')

    def test_selector_contract_is_separate_and_strict(self):
        prompt = {'grade': 11, 'approved_world_ids': ['design'], 'available_actions': list(agent.ACTIONS), 'feedback': {'verdict': 'Not really', 'preferred_interests': ['design']}}
        payload = {'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(decision('suggest_career_worlds', worlds=['design']))}}]}
        with patch('careerquest.discovery_agent.urllib.request.urlopen', return_value=io.BytesIO(json.dumps(payload).encode())) as send:
            chosen = self.real_selector(prompt, 'openai/gpt-oss-120b')
        self.assertEqual(chosen['action'], 'suggest_career_worlds')
        body = json.loads(send.call_args.args[0].data)
        self.assertEqual(set(body['response_format']['json_schema']['schema']['properties']['action']['enum']), set(agent.ACTIONS))
        self.assertTrue(body['response_format']['json_schema']['strict'])
        self.assertEqual(send.call_args.kwargs['timeout'], 12)
        self.assertNotIn('Fictional Agent Explorer', send.call_args.args[0].data.decode())
        self.assertNotIn('synthetic-test-key', send.call_args.args[0].data.decode())

    def test_legacy_story_regeneration_stales_agent_recommendations_without_changing_profile(self):
        initial = self.initial()
        regenerated = self.c.post(self.base+'/discovery-guide', json={'retry': True}).json()['latest']
        self.assertNotEqual(regenerated['id'], initial['guide']['latest']['id'])
        self.assertTrue(self.state()['discovery_agent']['is_stale'])
        self.assertEqual(self.state()['discovery_agent']['recommendations'], [])
        self.assertEqual(self.call(event='resume', session_id=initial['agent']['session_id']).status_code, 409)
        refreshed = self.call().json()
        self.assertFalse(refreshed['agent']['is_stale'])
        self.assertEqual(refreshed['agent']['story_id'], regenerated['id'])
        self.assertEqual(len(refreshed['guide']['history']), 2)
        self.assertEqual(self.state()['profile']['xp'], 60)

    def test_declined_confirmed_profile_blocks_planning_during_clarification_and_preserves_plan(self):
        self.c.post(self.base+'/confirm', json={'interests': ['technology']})
        plan = self.c.post(self.base+'/roadmap/propose', json={}).json()['plan']
        self.c.post(self.base+'/roadmap/save', json={'plan': plan})
        initial = self.initial(); before = self.state()
        pending = self.feedback(initial).json()
        self.assertEqual(pending['agent']['status'], 'awaiting_clarification')
        after = self.state(); self.assertFalse(after['confirmed'])
        self.assertEqual(after['profile'], before['profile']); self.assertEqual(after['profile_preferences'], before['profile_preferences'])
        self.assertEqual(after['latest_plan'], before['latest_plan']); self.assertEqual(after['quest_answers'], before['quest_answers'])
        for path, body in [('/explore', {'message': 'Explore careers'}), ('/roadmap/propose', {}), ('/roadmap/save', {'plan': plan})]:
            self.assertEqual(self.c.post(self.base+path, json=body).status_code, 409)
        self.assertEqual(after['profile']['xp'], 70)

    def test_incomplete_explorer_and_cross_profile_resume_cannot_supply_tool_context(self):
        second = self.c.post('/api/profiles', json={'fictional_ack':True,'alias': 'Second Fictional Agent', 'grade': 9}).json()['profile']['id']
        self.assertEqual(self.c.post(f'/api/profiles/{second}/discovery-agent', json={'event': 'discover'}).status_code, 409)
        self.selector.assert_not_called()
        initial = self.initial()
        for step, quest in enumerate(api.QUESTS): self.c.post(f'/api/profiles/{second}/quests/{step}', json={'option': next(iter(quest['options']))})
        self.assertEqual(self.c.post(f'/api/profiles/{second}/discovery-agent', json={'event': 'resume', 'session_id': initial['agent']['session_id']}).status_code, 409)
        self.assertEqual(self.call(event='discover', source_choices=[{'choice':'invented'}]).status_code, 422)
