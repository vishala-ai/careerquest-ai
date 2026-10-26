"""Explicit live Groq smoke test, using only a temporary fictional database.

Run: .venv/bin/python scripts/smoke_discovery_guide.py --live
Does not print credentials, mutate the normal database, or save a roadmap.
"""
import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from careerquest import api


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Explicitly authorize one live Groq generation request')
    parser.add_argument('--output', type=Path, help='Optional sanitized JSON evidence output')
    args = parser.parse_args()
    if not args.live:
        parser.error('Pass --live to make the explicitly labeled network request')
    result = {'check': 'LIVE Groq Discovery Guide smoke test', 'mocked': False}
    if not os.getenv('GROQ_API_KEY', '').strip():
        result.update(status='skipped', reason='GROQ_API_KEY is not configured')
    else:
        with tempfile.TemporaryDirectory(prefix='careerquest-guide-live-') as directory, patch.object(api, 'DB', str(Path(directory) / 'fictional.sqlite3')), TestClient(api.app) as client:
            initial = client.post('/api/profiles', json={'fictional_ack': True, 'alias': 'Comet Fictional Smoke', 'grade': 10}).json()
            base = '/api/profiles/' + initial['profile']['id']
            for step, quest in enumerate(api.QUESTS):
                assert client.post(base + f'/quests/{step}', json={'option': next(iter(quest['options']))}).status_code == 200
            response = client.post(base + '/discovery-guide', json={})
            assert response.status_code == 200, response.status_code
            item = response.json()['latest']
            restored = client.get(base).json()
            assert restored['profile']['xp'] == 60 and not restored['confirmed']
            assert client.post(base + '/roadmap/propose', json={}).status_code == 409
            # Cache replay and feedback deliberately do not cause another model request.
            assert client.post(base + '/discovery-guide', json={}).json()['latest']['id'] == item['id']
            feedback = client.post(base + f'/discovery-guide/{item["id"]}/feedback', json={'verdict': 'Somewhat', 'correction': 'Fictional explorer wants to keep exploring.'})
            assert feedback.status_code == 200
            after = client.get(base).json()
            assert after['profile']['xp'] == 60 and not after['confirmed']
            result.update(status='passed' if item['status'] == 'groq' else 'failed',
                          generation_status=item['status'], model=item['model'], error_type=item['error_type'],
                          story=item['content'], quest_xp=after['discovery']['quest_xp'],
                          confirmed=after['confirmed'], feedback_persisted=after['discovery_guide']['latest']['feedback']['verdict'],
                          history_count=len(after['discovery_guide']['history']), cached_replay=True,
                          roadmap_gate=409, database='temporary fictional database; normal records untouched')
    print(json.dumps(result, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    return 1 if result['status'] == 'failed' else 0


if __name__ == '__main__':
    raise SystemExit(main())
