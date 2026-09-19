import hashlib
import json
import ssl
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import MagicMock, patch

import requests
from urllib3 import PoolManager

from sku_board import backend, image_cancellation
from sku_board.director_transport import DirectorHTTPAdapter, DirectorUploadTimeout, _UploadTimeoutMixin
from sku_board.visual_agents.failures import describe


class FakeSocket:
    def __init__(self):
        self.timeouts = []

    def settimeout(self, value):
        self.timeouts.append(value)


class FakeConnection:
    def __init__(self):
        self.sock = None
        self.timeout = 0.05
        self.sent = []
        self.closed = False

    def connect(self):
        self.connect_timeout = self.timeout
        self.sock = FakeSocket()

    def request(self, method, url, body):
        self.sock.settimeout(self.timeout)
        self.send(body)

    def send(self, chunk):
        self.sent.append(chunk)

    def getresponse(self):
        return self.timeout

    def close(self):
        self.closed = True


class Connection(_UploadTimeoutMixin, FakeConnection):
    _director_write_timeout = 1.0


class DirectorUploadTests(unittest.TestCase):
    def test_connect_upload_read_are_separate_and_bytes_unchanged(self):
        c = Connection()
        body = b'abc' * 50000
        c.request('POST', '/', body)
        self.assertEqual(c.connect_timeout, 0.05)
        self.assertGreater(c.sock.timeouts[-1], 0.8)
        self.assertEqual(c.timeout, 0.05)
        self.assertEqual(b''.join(c.sent), body)
        self.assertTrue(all(len(x) <= 65536 for x in c.sent))
        self.assertIsNone(c._upload_deadline)
        c.timeout = 10.0  # read timeout set by pool
        c._director_deadline = time.monotonic() + 0.5
        self.assertLessEqual(c.getresponse(), 0.5)

    def test_write_errors_classified_and_socket_closed(self):
        for error in (TimeoutError('The write operation timed out'), ssl.SSLWantWriteError(3, 'write')):
            c = Connection()
            with patch.object(FakeConnection, 'send', side_effect=error):
                with self.assertRaises(DirectorUploadTimeout):
                    c.request('POST', '/', b'body')
            self.assertTrue(c.closed)
            self.assertIsNone(c._upload_deadline)

    def test_deadline_and_cancellation_end_upload_before_send(self):
        c = Connection()
        c._director_deadline = time.monotonic() - 1
        with self.assertRaises(DirectorUploadTimeout):
            c.request('POST', '/', b'body')
        self.assertEqual(c.sent, [])
        c = Connection()
        with patch.object(image_cancellation, 'check', side_effect=image_cancellation.OperationCancelled('cancelled')):
            with self.assertRaises(image_cancellation.OperationCancelled):
                c.request('POST', '/', b'body')
        self.assertTrue(c.closed)

    def test_adapter_and_proxy_pools_do_not_patch_global_connections(self):
        original = dict(PoolManager().pool_classes_by_scheme)
        a = DirectorHTTPAdapter(write_timeout=90)
        b = DirectorHTTPAdapter(write_timeout=20)
        for manager in (a.poolmanager, a.proxy_manager_for('http://127.0.0.1:9999')):
            self.assertEqual(manager.pool_classes_by_scheme['https'].ConnectionCls._director_write_timeout, 90)
        self.assertEqual(b.poolmanager.pool_classes_by_scheme['https'].ConnectionCls._director_write_timeout, 20)
        self.assertEqual(original, PoolManager().pool_classes_by_scheme)
        self.assertEqual(a.max_retries.total, 0)
        with requests.Session() as session:
            session.mount('https://', a)
            self.assertTrue(session.verify)
        b.close()

    def test_backend_uses_new_adapter_but_same_protocol(self):
        session = MagicMock()
        response = MagicMock(ok=True)
        response.json.return_value = {'choices': [{'message': {'content': '{"ok":true}'}}]}
        with patch('requests.Session', return_value=session), patch.object(image_cancellation, 'post', return_value=response) as post:
            content, _ = backend.invoke_ai_director_chat_once({
                'apiKey': 'fixture', 'model': 'fixture', 'baseUrl': 'https://fixture.invalid/v1', 'timeout': 120,
            }, [{'role': 'user', 'content': 'fixture'}])
        self.assertEqual(content, '{"ok":true}')
        adapter = session.mount.call_args_list[0].args[1]
        self.assertIsInstance(adapter, DirectorHTTPAdapter)
        self.assertGreater(adapter.write_timeout, post.call_args.kwargs['timeout'][0])
        self.assertEqual(post.call_args.kwargs['timeout'][1], 120)
        self.assertFalse(session.trust_env)
        self.assertNotIn('verify', post.call_args.kwargs)
        self.assertEqual(post.call_args.kwargs['json']['model'], 'fixture')
        session.close.assert_called_once()

    def test_upload_does_not_consume_the_separate_read_window_but_obeys_chain_deadline(self):
        settings = {'apiKey': 'fixture', 'model': 'fixture', 'baseUrl': 'https://fixture.invalid/v1',
                    'timeout': 120, '_transportDeadline': time.monotonic() + 200}
        response = MagicMock(ok=True)
        response.json.return_value = {'choices': [{'message': {'content': '{"ok":true}'}}]}
        session = MagicMock()
        with patch('requests.Session', return_value=session), patch.object(image_cancellation, 'post', return_value=response):
            backend.invoke_ai_director_chat_once(settings, [])
        adapter = session.mount.call_args_list[0].args[1]
        self.assertGreater(adapter.deadline - time.monotonic(), 180)
        self.assertLessEqual(adapter.deadline, settings['_transportDeadline'])
        self.assertEqual(set(settings['_lastDirectorTransport']), {'uploadComplete', 'elapsedMs'})

    def test_upload_metrics_are_body_free(self):
        c = Connection()
        c._director_stats = {}
        c.request('POST', '/', b'private-product-bytes')
        self.assertEqual(set(c._director_stats), {'uploadComplete', 'uploadMs'})
        self.assertTrue(c._director_stats['uploadComplete'])
        self.assertNotIn('private', json.dumps(c._director_stats))

    def test_failed_upload_is_endpoint_failure_not_another_model_upload(self):
        for error in ('AI 导演上传超时：图片请求未发送完成',
                      "AI 导演连接失败：SSLError(SSLWantWriteError('write'))"):
            settings = {'model': 'gpt-5.6-terra', '_disableStreamRetry': True, 'timeout': 120}
            with patch.object(backend, 'invoke_ai_director_chat_once', side_effect=ValueError(error)) as call:
                with self.assertRaisesRegex(ValueError, '接口传输未完成'):
                    backend.invoke_ai_director_chat(settings, [])
            self.assertEqual(call.call_count, 1)
            self.assertEqual(len(settings['_lastDirectorCall']['attempts']), 1)
            self.assertIn('connection', describe(error)['codes'])

    def test_real_local_post_preserves_content_length_and_json(self):
        observed = {}
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers['Content-Length']))
                observed.update(body=body, transfer=self.headers.get('Transfer-Encoding'))
                result = b'{"ok":true}'
                self.send_response(200)
                self.send_header('Content-Length', str(len(result)))
                self.end_headers()
                self.wfile.write(result)

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        payload = {'messages': [{'image': 'a' * (700 * 1024)}]}
        try:
            with requests.Session() as session:
                session.trust_env = False
                session.mount('http://', DirectorHTTPAdapter(write_timeout=2, deadline=time.monotonic() + 5))
                response = session.post(f'http://127.0.0.1:{server.server_port}/', json=payload, timeout=(0.2, 2))
                self.assertEqual(response.json(), {'ok': True})
            self.assertIsNone(observed['transfer'])
            self.assertEqual(json.loads(observed['body']), payload)
            expected = requests.Request('POST', 'http://fixture', json=payload).prepare().body
            self.assertEqual(hashlib.sha256(observed['body']).digest(), hashlib.sha256(expected).digest())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
