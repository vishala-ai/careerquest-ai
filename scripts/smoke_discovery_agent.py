"""One explicit live Student Discovery Agent feedback/resume smoke; fictional DB only."""
import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from careerquest import api, discovery_agent as agent, discovery_guide as guide


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not args.live: parser.error('Pass --live to make explicit Groq requests')
    evidence = {'check': 'LIVE Student Discovery Agent selection/resume', 'initial_story_setup_mocked': True, 'routing_mocked': False}
    if not os.getenv('GROQ_API_KEY', '').strip():
        evidence.update(status='skipped', reason='Groq key is not configured')
    else:
        with tempfile.TemporaryDirectory(prefix='careerquest-agent-live-') as directory, patch.object(api, 'DB', str(Path(directory)/'fictional.sqlite3')), TestClient(api.app) as client:
            pid = client.post('/api/profiles', json={'fictional_ack': True, 'alias': 'Comet Fictional Agent', 'grade': 11}).json()['profile']['id']
            base = f'/api/profiles/{pid}'
            for step, quest in enumerate(api.QUESTS): assert client.post(base+f'/quests/{step}', json={'option': next(iter(quest['options']))}).status_code == 200
            before = client.get(base).json()
            with patch('careerquest.discovery_guide.groq_discovery', side_effect=lambda grade, choices, model, preferences=None: guide.deterministic_summary(choices, preferences)):
                initial = client.post(base+'/discovery-guide', json={}).json()['latest']
            response = client.post(base+'/discovery-agent', json={'event': 'feedback', 'story_id': initial['id'], 'verdict': 'Not really', 'correction': 'Those suggestions do not feel right. Help me explore a new direction.'})
            assert response.status_code == 200, response.status_code
            result = response.json(); answers = 0
            while result['agent']['question'] and answers < agent.MAX_CLARIFICATIONS:
                q = result['agent']['question']
                body = {'event': 'clarify', 'session_id': result['agent']['session_id'], 'question_id': q['id']}
                body.update({'correction': 'I would prefer to explore design.'} if q['id'] == 'correction' else {'preferred_interests': ['design']})
                response = client.post(base+'/discovery-agent', json=body)
                assert response.status_code == 200, response.status_code
                result = response.json(); answers += 1
            after = client.get(base).json(); trace = result['agent']['trace']
            assert all(d['action'] in agent.ACTIONS for d in trace)
            assert after['profile']['xp'] == 60 and after['quest_answers'] == before['quest_answers'] and not after['confirmed']
            assert client.post(base+'/roadmap/propose', json={}).status_code == 409
            assert all(w['world_id'] in guide.WORLD_IDS and w['choice_ids'] for w in result['agent']['recommendations'])
            replay = client.post(base+'/discovery-agent', json={'event': 'resume', 'session_id': result['agent']['session_id']}).json()
            assert replay == result
            live = sum(d['method'] == 'groq' for d in trace)
            latest = result['guide']['latest']
            evidence.update(status='passed' if live else 'failed', model=trace[0]['model'], engine=result['agent']['engine'], actions=[{'action': d['action'], 'method': d['method'], 'status': d['status'], 'error': d['error']} for d in trace],
                            live_model_decisions=live, clarifications_answered=answers, terminal_status=result['agent']['status'],
                            generated_new_story=latest['id'] != initial['id'], followup_generation_status=latest['status'] if latest['id'] != initial['id'] else 'initial_mock_only',
                            world_ids=[w['world_id'] for w in result['agent']['recommendations']], fallback_used=result['agent']['fallback_used'],
                            confirmed=after['confirmed'], xp=after['profile']['xp'], quest_answers_unchanged=True, cached_resume=True, roadmap_gate=409,
                            database='temporary fictional SQLite; normal database untouched')
    print(json.dumps(evidence, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(evidence, indent=2)+'\n')
    return 1 if evidence['status'] == 'failed' else 0


if __name__ == '__main__': raise SystemExit(main())
