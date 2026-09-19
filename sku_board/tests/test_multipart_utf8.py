import cgi
import io
import json
import unittest
from types import SimpleNamespace
from email.message import Message
from sku_board.server import SkuBoardHandler


def body_for(value):
    boundary = 'fixture-upload-boundary'
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="suitePlan"\r\n\r\n'.encode()
            + value + f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="reference0"; filename="参照図.png"\r\nContent-Type: image/png\r\n\r\n'.encode()
            + b'\x89PNG\r\n\x00\xfffixture-bytes' + f'\r\n--{boundary}--\r\n'.encode())
    headers = Message()
    headers['Content-Type'] = 'multipart/form-data; boundary=' + boundary
    headers['Content-Length'] = str(len(body))
    return body, headers


class MultipartUtf8Tests(unittest.TestCase):
    def test_64k_character_split_and_spillover_roundtrip(self):
        # JSON.stringify sends a long single physical line, with escaped newlines.
        pages = [{'page': 5, 'agentPrompt': {'resolvedPrompt': '日本語 สีไทย 中文 🎨\n' * 12000}}]
        encoded = json.dumps(pages, ensure_ascii=False, separators=(',', ':')).encode()
        body, headers = body_for(encoded)
        old = cgi.FieldStorage(fp=io.BytesIO(body), environ={'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE': headers['Content-Type'], 'CONTENT_LENGTH': str(len(body))})
        self.assertNotEqual(old['suitePlan'].value, encoded.decode(), 'fixture must reproduce old CGI corruption')
        fields, files = SkuBoardHandler.read_multipart_body(SimpleNamespace(headers=headers, rfile=io.BytesIO(body)))
        self.assertEqual(json.loads(fields['suitePlan']), pages)
        self.assertEqual(files['reference0'].filename, '参照図.png')
        self.assertEqual(files['reference0'].file.read(), b'\x89PNG\r\n\x00\xfffixture-bytes')
        files['reference0'].file.close()

    def test_small_and_empty_fields(self):
        for value in ('', '日本語\r\nภาษาไทย\n🎨', '{"page":1}'):
            body, headers = body_for(value.encode())
            fields, files = SkuBoardHandler.read_multipart_body(SimpleNamespace(headers=headers, rfile=io.BytesIO(body)))
            self.assertEqual(fields['suitePlan'], value)
            files['reference0'].file.close()

    def test_invalid_utf8_is_reported_not_silently_replaced(self):
        body, headers = body_for(b'bad-utf8-\xff')
        with self.assertRaises(UnicodeDecodeError):
            SkuBoardHandler.read_multipart_body(SimpleNamespace(headers=headers, rfile=io.BytesIO(body)))
