import os
import sys
import unittest
import json
import argparse
from urllib import request, parse, error

# Configuration: target server
HOST = os.environ.get('TEST_SERVER_HOST', 'localhost')
PORT = int(os.environ.get('TEST_SERVER_PORT', '8000'))
BASE_URL = f'http://{HOST}:{PORT}'

# Default verbosity (override in __main__)
VERBOSITY = 2

class TestJinja2EvalWeb(unittest.TestCase):
    def setUp(self):
        # Reset server state before each test
        # Restore default max_entries
        self.http_request('POST', '/settings', {'section': 'history', 'max_entries': '1000'})
        # Clear history
        self.http_request('POST', '/history/clear')
        if VERBOSITY >= 3:
            print(f"Starting test: {self.id()}")

    def tearDown(self):
        if VERBOSITY >= 3:
            print('-' * 80)

    def http_request(self, method, path, data=None):
        url = f"{BASE_URL}{path}"
        encoded = parse.urlencode(data).encode() if data else None
        try:
            req = request.Request(url, data=encoded, method=method)
            with request.urlopen(req) as resp:
                content = resp.read().decode()
                ctype = resp.getheader('Content-Type')
                try:
                    parsed = json.loads(content)
                except json.JSONDecodeError:
                    parsed = content
                if VERBOSITY >= 3:
                    print(f"REQUEST: method={method}, path={path}, data={data}")
                    print(f"RESPONSE: status={resp.status}, content-type={ctype}, body={parsed}")
                return resp.status, ctype, parsed
        except error.HTTPError as e:
            if VERBOSITY >= 3:
                print(f"REQUEST: method={method}, path={path}, data={data}")
                print(f"HTTPError: status={e.code}")
            return e.code, None, None

    def test_root_endpoint(self):
        status, ctype, body = self.http_request('GET', '/')
        self.assertEqual(status, 200)
        self.assertIn('text/html', ctype)
        self.assertTrue(isinstance(body, str) and len(body) > 0)

    def test_render_and_history(self):
        status, _, body = self.http_request('POST', '/render', {'json': '{"a":2}', 'expr': '{{ data.a * 3 }}'})
        self.assertEqual(status, 200)
        self.assertEqual(body, 6)
        _, _, history = self.http_request('GET', '/history')
        self.assertIsInstance(history, list)
        self.assertEqual(len(history), 1)
        entry = history[0]
        self.assertEqual(entry['input'], '{"a":2}')
        self.assertEqual(entry['expr'], '{{ data.a * 3 }}')

    def test_history_size_and_maxsize(self):
        # Add entries
        for i in range(2):
            self.http_request('POST', '/render', {'json': f'{{"v":{i}}}', 'expr': '{{ data.v }}'})
        _, _, size_before = self.http_request('GET', '/history/size')
        self.assertEqual(size_before.get('size'), 2)
        _, _, maxsize = self.http_request('GET', '/history/maxsize')
        self.assertIn('max_size', maxsize)
        self.assertIsInstance(maxsize['max_size'], int)

    def test_history_clear(self):
        # Populate history
        for i in range(3):
            self.http_request('POST', '/render', {'json': f'{{"x":{i}}}', 'expr': '{{ data.x }}'})
        _, _, size_before = self.http_request('GET', '/history/size')
        self.assertEqual(size_before.get('size'), 3)
        status, _, clear_resp = self.http_request('POST', '/history/clear', {'count': '2'})
        self.assertEqual(status, 200)
        self.assertEqual(clear_resp.get('cleared'), 2)
        self.assertEqual(clear_resp.get('size'), 1)
        status, _, clear_all = self.http_request('POST', '/history/clear')
        self.assertEqual(status, 200)
        self.assertEqual(clear_all.get('cleared'), 1)
        self.assertEqual(clear_all.get('size'), 0)

    def test_settings_read_and_write(self):
        # Read default settings
        status, _, all_settings = self.http_request('GET', '/settings')
        self.assertEqual(status, 200)
        self.assertIn('history', all_settings)
        self.assertEqual(all_settings['history']['max_entries'], '1000')
        # Update max_entries
        status, _, updated = self.http_request('POST', '/settings', {'section': 'history', 'max_entries': '5'})
        self.assertEqual(status, 200)
        self.assertEqual(updated['history']['max_entries'], '5')
        _, _, maxsize2 = self.http_request('GET', '/history/maxsize')
        self.assertEqual(maxsize2.get('max_size'), 5)
        # Create and read user section
        status, _, user_sec = self.http_request('POST', '/settings', {'section': 'user', 'theme': 'dark'})
        self.assertEqual(status, 200)
        self.assertEqual(user_sec['user']['theme'], 'dark')
        _, _, fetched = self.http_request('GET', '/settings?section=user')
        self.assertEqual(fetched.get('theme'), 'dark')

    def test_404_for_invalid(self):
        status, _, _ = self.http_request('GET', '/invalid_path')
        self.assertEqual(status, 404)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run Jinja2 Eval Web tests')
    parser.add_argument('-v', '--verbosity', type=int, default=2,
                        help='Verbosity level for unittest (default: 2)')
    args = parser.parse_args()
    VERBOSITY = args.verbosity
    unittest.main(argv=[sys.argv[0]], verbosity=args.verbosity)
