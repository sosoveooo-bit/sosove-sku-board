import http.client
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from server import Handler


class StudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def request(self, path, headers=None):
        conn = http.client.HTTPConnection(*self.server.server_address)
        conn.request('GET', path, headers=headers or {'Host': '127.0.0.1:8795'})
        res = conn.getresponse()
        body = res.read()
        conn.close()
        return res.status, body

    def test_home(self):
        code, body = self.request('/')
        self.assertEqual(code, 200)
        self.assertIn('对话创作室'.encode(), body)
        for key in ('cod-country-landing-30', 'jp-landing-page-25', 'cod-country-detail-12'):
            self.assertIn(('value="' + key + '"').encode(), body)

    def test_local_health(self):
        self.assertEqual(self.request('/health')[0], 200)

    def test_public_home_and_assets(self):
        for host in ('manage.sosove.ggff.net', 'manage.sosove.ggff.net:443'):
            for path in ('/', '/app.js', '/style.css', '/workflow.js', '/history-menu.js', '/history-menu.css', '/health'):
                with self.subTest(host=host, path=path):
                    self.assertEqual(self.request(path, {'Host': host})[0], 200)

    def test_public_origin(self):
        for host in ('manage.sosove.ggff.net', '127.0.0.1:8795'):
            self.assertEqual(self.request('/health', {
                'Host': host, 'Origin': 'https://manage.sosove.ggff.net',
            })[0], 200)

    def test_public_host_still_rejects_other_origins(self):
        for origin in ('https://example.com', 'https://manage.sosove.ggff.net.attacker.example',
                       'http://manage.sosove.ggff.net', 'null'):
            with self.subTest(origin=origin):
                self.assertEqual(self.request('/health', {
                    'Host': 'manage.sosove.ggff.net', 'Origin': origin,
                })[0], 403)

    def test_public_host_still_restricts_routes(self):
        self.assertEqual(self.request('/api/sku-board/users', {
            'Host': 'manage.sosove.ggff.net',
        })[0], 404)

    def test_no_arbitrary_proxy(self):
        self.assertEqual(self.request('/api/sku-board/users')[0], 404)

    def test_reject_external_origin(self):
        self.assertEqual(self.request('/health', {'Host':'127.0.0.1:8795', 'Origin':'https://example.com'})[0], 403)

    def test_reject_rebinding_host(self):
        self.assertEqual(self.request('/', {'Host':'attacker.example:8795'})[0], 403)


if __name__ == '__main__':
    unittest.main()
