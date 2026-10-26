"""Groq routing contract tests; no real credentials or network calls."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from careerquest.agent import ALLOWED, groq_choose, run
from careerquest.store import connect, create_profile, latest_plan


class GroqTests(unittest.TestCase):
    def setUp(self):
        self.person = {'alias': 'Synthetic Alias', 'grade': 11, 'interests': ['science']}
        self.env = patch.dict('os.environ', {'GROQ_API_KEY': 'synthetic-test-key', 'GROQ_MODEL': ''})
        self.env.start()
        self.addCleanup(self.env.stop)

    def response(self, content):
        return io.BytesIO(json.dumps({'choices': [{'message': {'content': content}}]}).encode())

    def test_request_contract_and_minimal_prompt(self):
        with patch('careerquest.agent.urllib.request.urlopen', return_value=self.response('{"action":"research_college"}')) as send:
            self.assertEqual(groq_choose('Explore majors', self.person), 'research_college')
        request = send.call_args.args[0]
        self.assertEqual(request.full_url, 'https://api.groq.com/openai/v1/chat/completions')
        self.assertEqual(request.get_header('Authorization'), 'Bearer synthetic-test-key')
        self.assertEqual(request.get_header('User-agent'), 'CareerQuest/0.2.0')
        self.assertEqual(send.call_args.kwargs['timeout'], 12)
        body = json.loads(request.data)
        self.assertEqual(body['model'], 'openai/gpt-oss-120b')
        output = body['response_format']['json_schema']
        self.assertTrue(output['strict'])
        self.assertEqual(set(output['schema']['properties']['action']['enum']), ALLOWED)
        self.assertEqual(body['reasoning_effort'], 'low')
        for action in ALLOWED:
            self.assertIn(action, body['messages'][0]['content'])
        prompt = json.loads(body['messages'][1]['content'])
        self.assertEqual(prompt, {'question': 'Explore majors', 'grade': 11, 'interests': ['science']})
        self.assertNotIn('synthetic-test-key', request.data.decode())
        self.assertNotIn('Synthetic Alias', request.data.decode())

    def test_configurable_model(self):
        with patch.dict('os.environ', {'GROQ_MODEL': 'openai/gpt-oss-20b'}):
            with patch('careerquest.agent.urllib.request.urlopen', return_value=self.response('{"action":"ask_question"}')) as send:
                groq_choose('Hello', self.person)
        body = json.loads(send.call_args.args[0].data)
        self.assertEqual(body['model'], 'openai/gpt-oss-20b')
        output = body['response_format']['json_schema']
        self.assertTrue(output['strict'])
        self.assertEqual(set(output['schema']['properties']['action']['enum']), ALLOWED)
        self.assertEqual(body['reasoning_effort'], 'low')

    def test_explicit_llama_override_uses_json_object_mode(self):
        with patch('careerquest.agent.urllib.request.urlopen', return_value=self.response('{"action":"research_careers"}')) as send:
            groq_choose('Explore careers', self.person, model='llama-3.3-70b-versatile')
        body = json.loads(send.call_args.args[0].data)
        self.assertEqual(body['model'], 'llama-3.3-70b-versatile')
        self.assertEqual(body['response_format'], {'type': 'json_object'})
        self.assertNotIn('reasoning_effort', body)

    def test_invalid_actions_rejected(self):
        for content in ('{"action":"submit_application"}', '{"action":"reflect","extra":true}', '[]', '{"action":[]}', 'not json'):
            with self.subTest(content=content):
                with patch('careerquest.agent.urllib.request.urlopen', return_value=self.response(content)):
                    with self.assertRaises(ValueError):
                        groq_choose('Explore careers', self.person)

    def test_missing_key_never_sends_request(self):
        with patch.dict('os.environ', {'GROQ_API_KEY': ''}):
            with patch('careerquest.agent.urllib.request.urlopen') as send:
                with self.assertRaises(RuntimeError):
                    groq_choose('Hello', self.person)
                send.assert_not_called()

    def test_core_groq_trace_and_run_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            connection = connect(Path(directory) / 'synthetic.db')
            try:
                pid = create_profile(connection)
                with patch('careerquest.agent.urllib.request.urlopen', return_value=self.response('{"action":"research_college"}')):
                    result = run(connection, pid, 'Explore careers', use_groq=True)
                self.assertEqual(result['action'], 'research_college')
                self.assertEqual(result['trace'][0]['method'], 'groq')
                self.assertIsNotNone(connection.execute('SELECT id FROM runs WHERE id=?', (result['run_id'],)).fetchone())
                self.assertIsNone(latest_plan(connection, pid))
                self.assertNotIn('synthetic-test-key', json.dumps(result))
            finally:
                connection.close()

    def test_core_failures_use_policy_without_saving_plan(self):
        errors = [TimeoutError(), HTTPError('https://api.groq.com', 401, 'Unauthorized', {}, None),
                  HTTPError('https://api.groq.com', 429, 'Rate limited', {}, None), ValueError('Invalid action')]
        for error in errors:
            with self.subTest(error=type(error).__name__), tempfile.TemporaryDirectory() as directory:
                connection = connect(Path(directory) / 'synthetic.db')
                self.addCleanup(connection.close)
                pid = create_profile(connection)
                with patch('careerquest.agent.groq_choose', side_effect=error):
                    result = run(connection, pid, 'Create my roadmap', use_groq=True)
                self.assertEqual(result['action'], 'create_plan')
                self.assertEqual(result['trace'][0]['method'], 'bounded_policy_fallback')
                self.assertEqual(result['trace'][0]['status'], 'model_unavailable')
                self.assertIsNone(latest_plan(connection, pid))
                self.assertNotIn('synthetic-test-key', json.dumps(result))
                connection.close()

    def test_default_policy_never_calls_groq(self):
        with tempfile.TemporaryDirectory() as directory:
            connection = connect(Path(directory) / 'synthetic.db')
            try:
                pid = create_profile(connection)
                with patch('careerquest.agent.groq_choose') as model:
                    result = run(connection, pid, 'Explore careers')
                model.assert_not_called()
                self.assertEqual(result['trace'][0]['method'], 'bounded_policy')
            finally:
                connection.close()


if __name__ == '__main__':
    unittest.main()
