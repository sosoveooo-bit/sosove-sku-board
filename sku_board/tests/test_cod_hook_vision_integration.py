"""Offline integration checks for mandatory COD hook upload recognition."""

import base64
from contextlib import ExitStack
from copy import deepcopy
from io import BytesIO
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from sku_board import backend, cod_hook_vision


class DispatchReached(RuntimeError):
    """End an integration request at the mocked image-provider boundary."""


class CodHookVisionIntegrationTests(unittest.TestCase):
    ACTOR = {"username": "hook-vision-owner", "role": "ops"}
    MODEL = "gpt-image-2.5-sunburst"
    BRIEF = "日语噱头主图；产品保持上传的宽松外套款式；卖点：前贴袋、简洁翻领、卷边袖口。不要价格；完整末尾标记HOOK-END-922。"
    SKU_POINT = "商品档案原始卖点：两侧前贴袋；标签资料原文SOURCE-SKU-922。"

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        directory = self.stack.enter_context(tempfile.TemporaryDirectory(prefix="cod-hook-vision-integration-"))
        self.data_dir = Path(directory)
        self.stack.enter_context(patch.dict(os.environ, {"SKU_BOARD_DATA_DIR": directory}))
        for name, path in (
            ("DATA_DIR", self.data_dir),
            ("DATA_FILE", self.data_dir / "board.json"),
            ("AD_LAUNCH_UPLOAD_DIR", self.data_dir / "uploads"),
            ("AI_DIRECTOR_SETTINGS_FILE", self.data_dir / "director.json"),
            ("AI_DIRECTOR_CACHE_FILE", self.data_dir / "director-cache.json"),
            ("AI_IMAGE_JOBS_FILE", self.data_dir / "image-jobs.json"),
        ):
            self.stack.enter_context(patch.object(backend, name, path))
        self.stack.enter_context(patch("requests.sessions.Session.request", side_effect=AssertionError("Network disabled")))
        self.stack.enter_context(patch.object(backend, "ai_image_skill_config", return_value={}))
        self.stack.enter_context(patch.object(backend, "log_ai_image_error"))
        self.stack.enter_context(patch.object(backend, "chatgpt2api_image_tasks_enabled", return_value=True))
        self.oip_enabled = self.stack.enter_context(patch.object(backend, "shared_ai_director_open_prompts_enabled", return_value=True))
        self.oip = self.stack.enter_context(patch.object(backend, "enhance_single_ai_image_prompt_with_open_prompts", side_effect=AssertionError("Unexpected OIP enhancement")))
        self.acore = self.stack.enter_context(patch.object(backend, "generate_images_via_acore", side_effect=AssertionError("Unexpected Acore dispatch")))
        self.dispatch = self.stack.enter_context(patch.object(backend, "generate_ai_image_tasks_with_transient_retry", side_effect=DispatchReached("IMAGE_DISPATCH")))
        self.save_outputs = self.stack.enter_context(patch.object(backend, "save_ai_image_outputs", side_effect=AssertionError("Unexpected image storage")))
        self.settings = {
            "enabled": True, "baseUrl": "https://fixture-director.invalid/v1",
            "apiKey": "fixture-private-key-922", "model": "gpt-5.6-terra",
            "fallbackModels": ["gpt-5.6-sol"], "visionEnabled": True,
            "openImagePromptsEnabled": True, "timeout": 60,
        }
        self.stack.enter_context(patch.object(backend, "load_ai_director_settings", side_effect=lambda: deepcopy(self.settings)))
        self.stack.enter_context(patch.object(backend, "ai_director_reference_data_url", side_effect=lambda ref: "data:image/png;base64," + base64.b64encode(ref[1]).decode("ascii")))
        self.response = self.analysis_payload()
        self.invoke = self.stack.enter_context(patch.object(backend, "invoke_ai_director_chat", side_effect=self.director_response))
        self.refs = [(f"reference-{index}.png", f"ORIGINAL-BYTES-{index}".encode(), "image/png") for index in range(1, 7)]

    def analysis_payload(self):
        records = []
        for index, role, variant, view, color in (
            (1, "layout", "", "layout", ""),
            (2, "product", "khaki", "front", "卡其色"),
            (3, "product", "khaki", "back", "卡其色"),
            (4, "detail", "khaki", "close-up", "卡其色"),
            (5, "product", "blue", "front", "蓝色"),
            (6, "usage", "khaki", "worn", "卡其色"),
        ):
            records.append({
                "index": index, "role": role, "productMatch": "different" if index == 1 else "confirmed",
                "variantId": variant, "view": view,
                "summary": "文字位于主体上方的版式" if index == 1 else f"已看清的外套视图 {index}",
                "colors": [color] if color else [],
                "structure": ["简洁翻领、前贴袋"] if index in (2, 5) else ["直线背缝"] if index == 3 else [],
                "materials": ["可见细微织纹"] if index == 4 else [],
                "usage": ["手臂自然下垂，袖口不遮挡产品轮廓"] if index == 6 else [],
                "uncertainties": [],
            })
        return {"productName": "宽松短袖外套", "summary": "两款颜色，同款正背视图分组。", "primaryReferenceIndex": 2, "references": records, "uncertainties": ["背面细节以已上传视图为准。"]}

    def director_response(self, settings, messages):
        settings["_lastDirectorCall"] = {"model": "gpt-5.6-sol", "attempts": [{"model": "gpt-5.6-sol", "status": "ok"}]}
        return json.dumps(self.response, ensure_ascii=False), 12

    def fields(self, **overrides):
        fields = {
            "templateKey": "codHook", "codHookType": "hook", "suiteCountry": "JP",
            "suiteBrief": self.BRIEF,
            "prompt": f"[Product]\nCurrent jacket.\n[COD hook selling-point sources]\n{self.SKU_POINT}\n[Current user prompt]\n{self.BRIEF}",
            "model": self.MODEL, "mode": "edit", "size": "750x1000", "quality": "high", "count": 2,
            "referenceBindings": json.dumps([{"index": index, "role": "product" if index == 1 else "detail", "roleSource": "default"} for index in range(1, 7)]),
            "productReferenceIndexes": "[1,4]",
        }
        fields.update(overrides)
        return fields

    def uploads(self, refs=None):
        refs = refs if refs is not None else self.refs
        return {f"reference{index}": SimpleNamespace(filename=name, file=BytesIO(data)) for index, (name, data, _mime) in enumerate(refs, 1)}

    def capture(self, *, fields=None, refs=None, actor=None, progress=None):
        self.dispatch.reset_mock()
        with self.assertRaisesRegex(DispatchReached, "IMAGE_DISPATCH"):
            backend.generate_ad_launch_ai_image_edit(fields or self.fields(), self.uploads(refs), actor or self.ACTOR, progress_callback=progress)
        self.dispatch.assert_called_once()
        return self.dispatch.call_args.kwargs

    def install_job(self):
        job_id = "AIJ-ABCDEF01234567"
        job = {"id": job_id, "owner": self.ACTOR["username"], "role": self.ACTOR["role"], "actor": deepcopy(self.ACTOR), "payload": self.fields(), "mode": "edit", "status": "queued", "files": [], "createdAt": backend.now_iso(), "updatedAt": backend.now_iso()}
        self.stack.enter_context(patch.object(backend, "_AI_IMAGE_JOBS", {job_id: job}))
        self.stack.enter_context(patch.object(backend, "_AI_IMAGE_JOB_THREADS", set()))
        self.stack.enter_context(patch.object(backend, "save_ai_image_jobs_locked"))
        self.stack.enter_context(patch.object(backend, "prune_ai_image_jobs"))
        self.stack.enter_context(patch.object(backend, "delete_ai_image_job_files"))
        self.stack.enter_context(patch.object(backend, "open_ai_image_job_files", side_effect=lambda _job: self.uploads()))
        return job_id

    def test_edit_entry_uses_online_variants_and_exact_originals_not_browser_guesses(self):
        updates = []
        sent = self.capture(progress=updates.append)
        self.invoke.assert_called_once()
        self.oip.assert_not_called()
        self.assertEqual(sent["model"], self.MODEL)
        self.assertEqual(sent["page_indexes"], [0, 1])
        self.assertEqual(sent["reference_images_by_page"], {0: [self.refs[index - 1] for index in (2, 3, 4, 6)], 1: [self.refs[4]]})
        self.assertEqual(len(sent["prompts"]), 2)
        for prompt in sent["prompts"]:
            self.assertIn(self.BRIEF, prompt)
            self.assertIn(self.SKU_POINT, prompt)
            self.assertIn("textPolicy=requested", prompt)
            self.assertIn("[COD hook AI product identity]", prompt)
            self.assertIn('"referenceImage":1', prompt)
            self.assertNotIn("[COD complete-range binding", prompt)
        self.assertEqual([entry["status"] for entry in updates], ["analyzing", "ready"])
        self.assertEqual(updates[-1]["primaryReferenceIndex"], 2)
        self.assertEqual(updates[-1]["model"], "gpt-5.6-sol")

    def test_disabled_vision_incomplete_json_and_model_errors_never_dispatch_images(self):
        original_settings, original_response = deepcopy(self.settings), deepcopy(self.response)
        for case in ("disabled", "vision-off", "missing-reference", "model-error"):
            with self.subTest(case=case):
                self.settings = deepcopy(original_settings)
                self.response = deepcopy(original_response)
                self.invoke.reset_mock()
                self.invoke.side_effect = self.director_response
                self.dispatch.reset_mock()
                if case == "disabled":
                    self.settings["enabled"] = False
                elif case == "vision-off":
                    self.settings["visionEnabled"] = False
                elif case == "missing-reference":
                    self.response["references"].pop()
                else:
                    self.invoke.side_effect = RuntimeError("HTTP 408 https://fixture-director.invalid/v1 fixture-private-key-922")
                updates = []
                with self.assertRaises(cod_hook_vision.CodHookAnalysisError) as raised:
                    backend.generate_ad_launch_ai_image_edit(self.fields(), self.uploads(), self.ACTOR, progress_callback=updates.append)
                self.dispatch.assert_not_called()
                self.acore.assert_not_called()
                self.assertEqual([item["status"] for item in updates], ["analyzing", "failed"])
                if case in ("disabled", "vision-off"):
                    self.invoke.assert_not_called()
                self.assertNotIn(self.settings["apiKey"], str(raised.exception))
                self.assertNotIn(self.settings["baseUrl"], str(raised.exception))

    def test_completed_materials_expose_only_public_analysis_and_original_source_mapping(self):
        self.dispatch.side_effect = None
        self.dispatch.return_value = [(b"GENERATED-KHAKI", "image/png"), (b"GENERATED-BLUE", "image/png")]
        self.save_outputs.side_effect = lambda images, *_args: ([{"id": f"fixture-output-{index}", "previewUrl": f"/fixture/{index}.png"} for index, _image in enumerate(images)], [f"/fixture/{index}.png" for index in range(len(images))])
        result = backend.generate_ad_launch_ai_image_edit(self.fields(), self.uploads(), self.ACTOR)
        self.assertTrue(result["ok"])
        self.assertEqual(result["productAnalysis"]["status"], "ready")
        self.assertEqual(result["resolvedReferenceBindings"][0]["role"], "layout")
        materials = result["materials"]
        self.assertEqual([item["referenceSourceIndexes"] for item in materials], [[2, 3, 4, 6], [5]])
        self.assertEqual([item["productVariantIds"] for item in materials], [["khaki"], ["blue"]])
        self.assertEqual([item["referenceCount"] for item in materials], [4, 1])
        for record in [result, *materials]:
            self.assertFalse(any(key.startswith("_") for key in record["productAnalysis"]))
            serialized = json.dumps(record, ensure_ascii=False)
            self.assertNotIn("_referenceHashes", serialized)
            self.assertNotIn(self.settings["apiKey"], serialized)
            self.assertNotIn(self.settings["baseUrl"], serialized)

    def test_generation_entry_reuses_owner_scoped_analysis_but_reanalyzes_changed_bytes(self):
        self.capture()
        progress = []
        self.capture(progress=progress.append)
        self.assertEqual(self.invoke.call_count, 1)
        self.assertTrue(progress[-1]["cached"])
        changed = list(self.refs)
        changed[1] = (changed[1][0], b"CHANGED-PRODUCT-SAME-FILENAME", changed[1][2])
        self.capture(refs=changed)
        self.assertEqual(self.invoke.call_count, 2)
        self.capture(actor={"username": "another-hook-owner", "role": "ops"})
        self.assertEqual(self.invoke.call_count, 3)

    def test_job_analysis_failure_retains_failed_stage_and_account_visibility(self):
        job_id = self.install_job()
        self.invoke.side_effect = RuntimeError("HTTP 408 https://fixture-director.invalid/v1 fixture-private-key-922")
        backend.run_ai_image_job(job_id)
        self.dispatch.assert_not_called()
        public = backend.get_ai_image_job(job_id, self.ACTOR)
        self.assertFalse(public["ok"])
        self.assertEqual(public["productAnalysis"]["status"], "failed")
        self.assertNotIn(self.settings["apiKey"], json.dumps(public))
        with self.assertRaises(ValueError):
            backend.get_ai_image_job(job_id, {"username": "another-owner", "role": "ops"})
        self.assertEqual(backend.get_ai_image_job(job_id, {"username": "admin-fixture", "role": "admin"})["productAnalysis"]["status"], "failed")

    def test_render_failure_keeps_analysis_ready_in_pending_and_error_polls(self):
        job_id = self.install_job()
        pending = []

        def fail_render(**_kwargs):
            pending.append(backend.get_ai_image_job(job_id, self.ACTOR))
            raise RuntimeError("MOCK_RENDER_FAILED")

        self.dispatch.side_effect = fail_render
        backend.run_ai_image_job(job_id)
        self.assertEqual(len(pending), 1)
        self.assertTrue(pending[0]["pending"])
        self.assertEqual(pending[0]["productAnalysis"]["status"], "ready")
        public = backend.get_ai_image_job(job_id, self.ACTOR)
        self.assertFalse(public["ok"])
        self.assertEqual(public["productAnalysis"]["status"], "ready")
        self.assertIn("MOCK_RENDER_FAILED", public["error"])
        public["productAnalysis"]["structure"].append("MUTATED-CLIENT-COPY")
        self.assertNotIn("MUTATED-CLIENT-COPY", backend.get_ai_image_job(job_id, self.ACTOR)["productAnalysis"]["structure"])

    def test_other_single_image_and_text_only_hook_paths_keep_their_existing_behavior(self):
        self.oip_enabled.return_value = False
        sent = self.capture(fields=self.fields(templateKey="main"))
        self.assertNotIn("[COD hook AI product identity]", sent["prompt"])
        self.assertIsNone(sent["reference_images_by_page"])
        with self.assertRaisesRegex(DispatchReached, "IMAGE_DISPATCH"):
            backend.generate_ad_launch_ai_image(self.fields(mode="text"), self.ACTOR)
        self.invoke.assert_not_called()
        self.oip.assert_not_called()


if __name__ == "__main__":
    unittest.main()
