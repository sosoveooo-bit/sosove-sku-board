from io import BytesIO
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import zipfile

from PIL import Image
from sku_board import backend, cod_prompt_atelier as atelier, cod_prompt_assets as assets
from sku_board.cod_prompt_render import archive_results
from sku_board.tests.test_cod_prompt_contract import form_fixture


class AtelierAssetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="atelier-assets-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = patch.object(atelier, "_root", return_value=self.root / "projects")
        self.store.start()
        self.addCleanup(self.store.stop)
        self.actor = {"username": "asset-test", "role": "designer"}
        self.form = form_fixture()
        project = atelier.save_project_upload({"form": json.dumps(self.form)}, {}, self.actor)["project"]
        self.project_id = project["id"]
        self.owner = atelier._owner(self.actor)
        with atelier._LOCK:
            document = atelier._read(self.owner, self.project_id)
            version = atelier._version(document)
            version["suitePages"] = [{"page": 1, "modelPrompt": "saved page", "executionPrompt": "saved execution"}]
            version["outline"] = [{"page": 1}, {"page": 2}]
            version["masterPrompt"] = "saved master"
            atelier._write(self.owner, document)
        stream = BytesIO()
        Image.new("RGB", (8, 8), "coral").save(stream, "PNG")
        self.png = stream.getvalue()
        self.material = {"id": "AI-0123456789", "name": "test.png", "page": 1, "storage": "local-temporary", "previewUrl": "/api/sku-board/ai-image-output/AI-0123456789"}

    def archive(self):
        return assets.archive_material(self.project_id, 1, 1, self.material, self.actor, self.png)

    def test_permanent_original_survives_without_shared_output_cache(self):
        material = self.archive()
        self.assertEqual(material["storage"], "project-permanent")
        self.assertEqual(material["archiveStatus"], "archived")
        self.assertNotIn("path", material)
        with patch.object(backend, "read_ai_image_output", side_effect=AssertionError("No temporary cache dependency")):
            content, mime = assets.read_asset(self.project_id, material["assetId"], self.actor, 1)
        self.assertEqual(content, self.png)
        self.assertEqual(mime, "image/png")
        project = atelier.get_project(self.project_id, self.actor)["project"]
        self.assertEqual(project["materials"][0]["assetId"], material["assetId"])

    def test_assets_enforce_owner_version_and_content_hash(self):
        material = self.archive()
        for actor, revision, digest in (({"username": "other", "role": "admin"}, 1, material["assetId"]), (self.actor, 99, material["assetId"]), (self.actor, 1, "../bad")):
            with self.assertRaises(ValueError):
                assets.read_asset(self.project_id, digest, actor, revision)
        path = assets._path(self.owner, self.project_id, material["assetId"], ".png")
        path.write_bytes(b"corrupted fixture")
        with self.assertRaisesRegex(ValueError, "校验失败"):
            assets.read_asset(self.project_id, material["assetId"], self.actor, 1)

    def test_zip_has_origin_version_manifest_and_marks_missing_pages(self):
        self.archive()
        stream, filename = assets.image_zip(self.project_id, 1, self.actor)
        try:
            with zipfile.ZipFile(stream) as archive:
                manifest = json.loads(archive.read("manifest.json"))
                self.assertFalse(manifest["complete"])
                self.assertEqual(manifest["pagesWithoutImage"], [2])
                self.assertEqual(manifest["included"][0]["originRevision"], 1)
                self.assertEqual(archive.read(manifest["included"][0]["file"]), self.png)
        finally:
            stream.close()
        self.assertEqual(filename, "atelier-v1-images.zip")

    def test_archiver_does_not_claim_success_for_invalid_image(self):
        fields = {"atelierProjectId": self.project_id, "atelierRevision": 1, "atelierPageNumber": 1, "atelierFingerprint": "fixture"}
        warning = archive_results(fields, self.actor, [self.material], [(b"not an image", "image/png")])
        self.assertIn("长期存档失败", warning)
        material = atelier.get_project(self.project_id, self.actor)["project"]["materials"][0]
        self.assertEqual(material["archiveStatus"], "failed")

    def test_referenced_legacy_images_are_exempt_from_temporary_cleanup(self):
        atelier.record_material(self.project_id, 1, 1, self.material, self.actor)
        uploads = self.root / "temporary-outputs"
        uploads.mkdir()
        referenced = uploads / "AI-0123456789.png"
        unrelated = uploads / "AI-9876543210.png"
        for path in (referenced, unrelated):
            path.write_bytes(self.png)
            os.utime(path, (time.time() - 3 * 86400,) * 2)
        with patch.object(backend, "AD_LAUNCH_UPLOAD_DIR", uploads), patch.object(backend, "AI_IMAGE_THUMBNAIL_DIR", self.root / "thumbs"), patch.object(backend, "load_board", return_value={"adLaunches": []}), patch.object(backend, "_AI_IMAGE_OUTPUT_LAST_CLEANUP_TS", 0), patch.dict(os.environ, {"AI_IMAGE_OUTPUT_TTL_SECONDS": "86400"}):
            result = backend.prune_ai_image_output_files(force=True)
        self.assertTrue(referenced.exists())
        self.assertFalse(unrelated.exists())
        self.assertEqual(result["removed"], 1)

    def test_migration_reads_only_materials_already_owned_by_project(self):
        with self.assertRaisesRegex(ValueError, "没有这张"):
            assets.archive_material(self.project_id, 1, 1, self.material, self.actor)
        atelier.record_material(self.project_id, 1, 1, self.material, self.actor)
        with patch.object(backend, "read_ai_image_output", return_value=(self.png, "image/png")):
            result = assets.archive_existing(self.project_id, {"revision": 1}, self.actor)
        self.assertEqual(result["archived"], 1)
        self.assertEqual(result["errors"], [])

    def test_corrupt_project_pauses_cleanup_without_breaking_generation(self):
        path = atelier._directory(self.owner, self.project_id) / "project.json"
        path.write_text("[]", encoding="utf-8")
        with self.assertRaises(ValueError):
            assets.protected_legacy_material_ids()
        with patch.object(backend, "_AI_IMAGE_OUTPUT_LAST_CLEANUP_TS", 0):
            result = backend.prune_ai_image_output_files(force=True)
        self.assertEqual(result, {"removed": 0, "bytes": 0})

    def test_unavailable_old_image_keeps_record_with_visible_failure(self):
        atelier.record_material(self.project_id, 1, 1, self.material, self.actor)
        with patch.object(backend, "read_ai_image_output", side_effect=ValueError("原图已过期")):
            result = assets.archive_existing(self.project_id, {"revision": 1}, self.actor)
        self.assertEqual(result["archived"], 0)
        self.assertEqual(result["errors"][0]["page"], 1)
        self.assertEqual(result["project"]["materials"][0]["archiveStatus"], "failed")
        self.assertIn("原图已过期", result["project"]["materials"][0]["archiveError"])


if __name__ == "__main__":
    unittest.main()
