"""Real localhost HTTP, isolated users/store and no external model requests."""
import json
from io import BytesIO
import zipfile
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from tempfile import TemporaryDirectory
import threading
import unittest
from unittest.mock import patch
from pathlib import Path

from sku_board import server, cod_prompt_atelier as atelier, cod_prompt_assets as assets, cod_prompt_queue as queues
from sku_board.tests.test_cod_prompt_contract import form_fixture


class CodAtelierHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = TemporaryDirectory(prefix="cod-atelier-http-")
        cls.store_patch = patch.object(atelier, "_root", return_value=Path(cls.folder.name))
        cls.auth_patch = patch.object(server, "auth_state", side_effect=lambda token: {
            "user": {"username": token, "role": "admin" if token != "viewer-test" else "viewer"} if token else None
        })
        cls.store_patch.start()
        cls.auth_patch.start()
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.SkuBoardHandler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(2)
        cls.auth_patch.stop()
        cls.store_patch.stop()
        cls.folder.cleanup()

    def request(self, method, suffix="", payload=None, *, actor="owner-test", multipart=False):
        headers = {"Cookie": f"sku_board_session={actor}"} if actor else {}
        if multipart:
            boundary = "AtelierBoundaryFixture"
            body = f'--{boundary}\r\nContent-Disposition: form-data; name="form"\r\n\r\n{json.dumps(payload, ensure_ascii=False)}\r\n--{boundary}--\r\n'.encode()
            headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        else:
            body = json.dumps(payload or {}, ensure_ascii=False).encode() if method == "POST" else None
            headers["Content-Type"] = "application/json"
        connection = HTTPConnection(*self.httpd.server_address, timeout=5)
        try:
            connection.request(method, "/api/sku-board/cod-atelier/projects" + suffix, body=body, headers=headers)
            response = connection.getresponse()
            status, result = response.status, json.loads(response.read())
            return status, result
        finally:
            connection.close()

    def test_authentication_and_role_are_required(self):
        self.assertEqual(self.request("GET", actor="")[0], 401)
        self.assertEqual(self.request("GET", actor="viewer-test")[0], 403)
        self.assertEqual(self.request("POST", "/upload", form_fixture(), actor="", multipart=True)[0], 401)

    def test_upload_read_listing_and_owner_isolation(self):
        status, result = self.request("POST", "/upload", form_fixture(), multipart=True)
        self.assertEqual(status, 200, result)
        project = result["project"]
        self.assertEqual(project["form"]["main"] + project["form"]["detail"], 10)
        status, loaded = self.request("GET", "/" + project["id"])
        self.assertEqual(status, 200)
        self.assertEqual(loaded["project"]["fingerprint"], project["fingerprint"])
        status, other = self.request("GET", "/" + project["id"], actor="other-test")
        self.assertEqual(status, 400)
        self.assertFalse(other["ok"])
        _, listing = self.request("GET")
        self.assertTrue(any(item["id"] == project["id"] for item in listing["projects"]))

    def test_disabled_director_stops_with_error_not_local_template(self):
        _, result = self.request("POST", "/upload", form_fixture(), multipart=True)
        project = result["project"]
        with patch.object(atelier, "_director_settings", side_effect=ValueError("AI未配置，不会使用模板")):
            status, failure = self.request("POST", "/" + project["id"] + "/generate", {"revision": project["revision"], "mode": "fresh"})
        self.assertEqual(status, 400)
        self.assertIn("不会使用模板", failure["error"])
        _, current = self.request("GET", "/" + project["id"])
        self.assertEqual(current["project"]["suitePages"], [])
        self.assertEqual(current["project"]["status"], "draft")

    def test_unsaved_reference_render_and_invalid_identifiers_fail_closed(self):
        _, result = self.request("POST", "/upload", form_fixture(), multipart=True)
        project = result["project"]
        status, failure = self.request("POST", "/" + project["id"] + "/render", {"revision": 1, "pageNumber": 1})
        self.assertEqual(status, 400)
        self.assertFalse(failure["ok"])
        self.assertEqual(self.request("GET", "/not-a-project")[0], 400)

    def test_quality_review_and_shared_export_requirements_route(self):
        _, result = self.request("POST", "/upload", form_fixture(), multipart=True)
        project = result["project"]
        self.assertIn("Delivery requirements", project["sharedExecutionRequirements"])
        actor = {"username": "owner-test", "role": "admin"}
        owner = atelier._owner(actor)
        with atelier._LOCK:
            document = atelier._read(owner, project["id"])
            version = atelier._version(document)
            version["masterPrompt"] = "当前商品便携榨汁杯，本土市场画面"
            version["outline"] = [{"page": 1, "focus": "便携", "sourcePointIndexes": [1, 2]}]
            version["suitePages"] = [{"page": 1, "headline": "Fresh juice", "focus": "便携", "modelPrompt": "当前商品在本土场景展示。"}]
            atelier._write(owner, document)
        status, result = self.request("POST", "/" + project["id"] + "/review", {"revision": 1, "mode": "rules"})
        self.assertEqual(status, 200)
        self.assertEqual(result["project"]["qualityReport"]["source"], "rules")
        self.assertTrue(result["project"]["qualityReport"]["advisory"])

    def test_queue_routes_pass_exact_project_revision_and_action(self):
        _, result = self.request("POST", "/upload", form_fixture(), multipart=True)
        project_id = result["project"]["id"]
        fake = {"ok": True, "queue": {"id": "a"*32, "projectId": project_id, "revision": 1, "status": "queued"}}
        with patch.object(queues, "start_queue", return_value=fake) as start:
            status, _ = self.request("POST", "/" + project_id + "/render-queue", {"revision": 1, "mode": "resume", "pageNumbers": [1]})
        self.assertEqual(status, 200)
        self.assertEqual(start.call_args.args[0], project_id)
        self.assertEqual(start.call_args.args[1]["pageNumbers"], [1])
        with patch.object(queues, "cancel_queue", return_value=fake) as cancel:
            status, _ = self.request("POST", "/" + project_id + "/render-queues/" + "a"*32 + "/cancel", {"revision": 1})
        self.assertEqual(status, 200)
        self.assertEqual(cancel.call_args.args[1], "a"*32)

    def test_permanent_assets_and_zip_require_project_owner(self):
        from PIL import Image
        _, result = self.request("POST", "/upload", form_fixture(), multipart=True)
        project_id = result["project"]["id"]
        actor = {"username": "owner-test", "role": "admin"}
        owner = atelier._owner(actor)
        with atelier._LOCK:
            document = atelier._read(owner, project_id)
            version = atelier._version(document)
            version["suitePages"] = [{"page": 1, "executionPrompt": "current saved prompt"}]
            atelier._write(owner, document)
        png = BytesIO()
        Image.new("RGB", (4, 4), "coral").save(png, "PNG")
        material = assets.archive_material(project_id, 1, 1, {"id": "AI-0000000001", "page": 1}, actor, png.getvalue())
        for suffix, mime in ((f"/assets/{material['assetId']}?revision=1", "image/png"), ("/images.zip?revision=1", "application/zip")):
            connection = HTTPConnection(*self.httpd.server_address, timeout=5)
            try:
                connection.request("GET", "/api/sku-board/cod-atelier/projects/" + project_id + suffix, headers={"Cookie": "sku_board_session=owner-test"})
                response = connection.getresponse()
                self.assertEqual(response.status, 200)
                self.assertIn(mime, response.getheader("Content-Type"))
                content = response.read()
                if mime == "application/zip":
                    with zipfile.ZipFile(BytesIO(content)) as zipped:
                        self.assertIn("manifest.json", zipped.namelist())
                else:
                    self.assertEqual(content, png.getvalue())
            finally:
                connection.close()
        status, _ = self.request("GET", f"/{project_id}/assets/{material['assetId']}?revision=1", actor="other-test")
        self.assertEqual(status, 400)


if __name__ == "__main__":
    unittest.main()
