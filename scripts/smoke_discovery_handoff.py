"""Explicit live Groq Discovery outcome -> confirmed handoff smoke (fictional DB)."""
import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from careerquest import api, discovery_guide as guide


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not args.live: parser.error('Pass --live to send fictional saved choices to the configured Groq model')
    result = {'check': 'LIVE Groq Discovery outcome and confirmed handoff', 'model_responses_mocked': False}
    if not os.getenv('GROQ_API_KEY', '').strip():
        result.update(status='skipped', reason='Groq key is not configured')
    else:
        with tempfile.TemporaryDirectory(prefix='careerquest-handoff-live-') as directory, patch.object(api, 'DB', str(Path(directory)/'fictional.sqlite3')), TestClient(api.app) as client:
            student = client.post('/api/profiles', json={'fictional_ack': True, 'alias': 'Fictional Handoff Smoke', 'grade': 10}).json()
            base = '/api/profiles/' + student['profile']['id']
            for step, quest in enumerate(api.QUESTS):
                assert client.post(base+f'/quests/{step}', json={'option': next(iter(quest['options']))}).status_code == 200
            raw = client.get(base).json()['quest_answers']
            response = client.post(base+'/discovery-agent', json={'event': 'discover'})
            assert response.status_code == 200, response.status_code
            data = response.json(); outcome = data['outcome']; trace = data['agent']['trace']
            assert outcome['story'] and 70 <= len(outcome['story']['summary'].split()) <= 110
            assert outcome['proposed_profile'] and outcome['next_mission']
            assert all(w['world_id'] in guide.WORLD_IDS and w['choice_ids'] for w in outcome['career_worlds'])
            assert client.get(base+'/career-worlds').status_code == 409
            confirmed = client.post(base+'/confirm', json=outcome['proposed_profile'])
            assert confirmed.status_code == 200, confirmed.status_code
            state = confirmed.json(); handoff = state['discovery_handoff']['active']
            assert handoff['story'] == outcome['story'] and handoff['profile_version'] == state['profile_version']
            assert state['quest_answers'] == raw and state['profile']['xp'] == 70
            assert client.post(base+'/confirm', json=outcome['proposed_profile']).json()['discovery_handoff']['active'] == handoff
            assert client.get(base+'/career-worlds').json()['handoff_id'] == handoff['id']
            live = sum(d['method'] == 'groq' for d in trace)
            result.update(status='passed' if live and outcome['story']['status'] == 'groq' else 'failed',
                model=outcome['story']['model'], generation_status=outcome['story']['status'], live_model_decisions=live,
                actions=[{'action': d['action'], 'method': d['method'], 'status': d['status'], 'error': d['error']} for d in trace],
                engine=data['agent']['engine'], fallback_used=data['agent']['fallback_used'],
                story_word_count=len(outcome['story']['summary'].split()), handoff_version=handoff['version'],
                profile_version=handoff['profile_version'], world_ids=handoff['suggested_world_ids'],
                confirmation_gate=409, quest_answers_unchanged=True, xp=state['profile']['xp'], idempotent_confirmation=True,
                database='temporary fictional SQLite; normal database untouched')
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    return 1 if result['status'] == 'failed' else 0


if __name__ == '__main__': raise SystemExit(main())
