"""Source-product fidelity reaches the real transport, without remote generation.

All provider calls, image persistence and suite planning are local fixtures. The
public request handlers and the async/sync multipart builders remain exercised.
"""

from contextlib import ExitStack
from copy import deepcopy
from io import BytesIO
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from sku_board import backend, cod_prompt_render


MODEL = "gpt-image-2.5-sunburst"
MARKER = "[Reference product detail fidelity]"
RAW_PROMPT = (
    "Photograph the uploaded product, including its small clasp and stitched seams.\n"
    "[Visible copy] 軽やかな着心地 / ゆったりシルエット\n"
    "[User request] Change only the background to #fcf9f4."
)
PRODUCT_BYTES = b"ORIGINAL-PRODUCT-BYTES\x00\xffnot-a-thumbnail"
RESULT_IMAGE = (b"mock-provider-result", "image/png")
ACTOR = {"username": "sunburst-fidelity-test", "role": "admin"}
NODE = {
    "id": "sunburst-fixture", "name": "Local test fixture",
    "rootUrl": "https://image.example.invalid",
    "baseUrl": "https://image.example.invalid/v1", "authKey": "fixture-token",
}


def response(body):
    result = Mock(
        ok=True, status_code=200, reason="OK",
        headers={"Content-Type": "application/json"}, text=json.dumps(body),
    )
    result.json.return_value = body
    return result


def fake_save(images, prompt, model, quality, size):
    materials = [
        {"id": f"AI-TEST-{index}", "prompt": prompt, "model": model, "quality": quality}
        for index, _ in enumerate(images)
    ]
    return materials, [f"/test-output-{index}.png" for index, _ in enumerate(images)]


class SunburstProductFidelityTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        directory = self.stack.enter_context(tempfile.TemporaryDirectory(prefix="sunburst-fidelity-"))
        root = Path(directory)
        self.stack.enter_context(patch.dict(os.environ, {"SKU_BOARD_DATA_DIR": directory}))
        for name, value in {
            "DATA_DIR": root, "DATA_FILE": root / "board.json",
            "AI_DIRECTOR_SETTINGS_FILE": root / "director.json",
            "AI_DIRECTOR_CACHE_FILE": root / "cache.json",
            "AD_LAUNCH_UPLOAD_DIR": root / "uploads",
            "AI_IMAGE_ERROR_LOG": root / "image-errors.log",
        }.items():
            self.stack.enter_context(patch.object(backend, name, value))
        self.stack.enter_context(patch("requests.sessions.Session.request", side_effect=AssertionError("Network disabled")))
        self.stack.enter_context(patch("urllib.request.urlopen", side_effect=AssertionError("Network disabled")))
        for name in ("invoke_ai_director_chat", "get_ai_director_cached_analysis", "put_ai_director_cached_analysis"):
            self.stack.enter_context(patch.object(backend, name, side_effect=AssertionError(f"Unexpected model/cache operation: {name}")))
        self.stack.enter_context(patch.object(backend, "log_ai_image_error"))
        self.stack.enter_context(patch.object(backend, "ai_image_skill_config", return_value={}))
        self.stack.enter_context(patch.object(backend, "shared_ai_director_open_prompts_enabled", return_value=False))
        self.stack.enter_context(patch.object(backend, "save_ai_image_outputs", side_effect=fake_save))
        self.stack.enter_context(patch.object(backend, "ai_image_programmatic_typography_enabled", return_value=False))
        self.stack.enter_context(patch.object(backend, "ai_image_remote_outputs_ready", return_value=True))

    @staticmethod
    def upload(name, content):
        return SimpleNamespace(filename=name, file=BytesIO(content))

    def generate(self, *, async_api=False, text_only=False, overrides=None, references=None, suite=False, atelier=False):
        fields = {
            "prompt": RAW_PROMPT, "model": MODEL, "size": "1024x1024",
            "quality": "auto", "count": 1,
        }
        if suite:
            fields.update({
                "suiteKey": backend.AI_IMAGE_COD_DETAIL_SUITE_KEY,
                "suiteCount": 20, "suitePageIndexes": "[1]", "suiteCountry": "JP",
            })
        fields.update(overrides or {})
        originals = references if references is not None else [("product.png", PRODUCT_BYTES, "image/png")]
        files = {f"reference{index}": self.upload(name, content) for index, (name, content, _mime) in enumerate(originals)}
        if fields.get("mode") == "inpaint":
            files["mask"] = self.upload("mask.png", b"MASK-ORIGINAL-BYTES")
        submitted = []
        task_ids = []

        def submit(endpoint, **kwargs):
            captured = {"endpoint": endpoint, **kwargs}
            submitted.append(captured)
            body = kwargs.get("data", kwargs.get("json", {}))
            if "client_task_id" in body:
                task_ids.append(body["client_task_id"])
                return response({"id": body["client_task_id"]})
            return response({"data": [{"b64_json": "aW1hZ2U="}]})

        def poll(_endpoint, **_kwargs):
            return response({"items": [
                {"id": task_id, "status": "success", "images": [{"b64_json": "aW1hZ2U="}]}
                for task_id in task_ids
            ]})

        def run_async(**kwargs):
            # Keep the production multipart builder and reference binding alive;
            # only the node scheduler/retry layer and HTTP responses are fixtures.
            kwargs.pop("actor", None)
            kwargs.pop("node_affinity_key", None)
            return backend._generate_images_via_chatgpt2api_tasks_single(service_node=dict(NODE), **kwargs)

        session = Mock()
        session.post.side_effect = submit
        session.get.side_effect = poll
        with ExitStack() as stack:
            stack.enter_context(patch.object(backend, "chatgpt2api_image_tasks_enabled", return_value=async_api))
            stack.enter_context(patch.object(backend, "chatgpt2api_auth_key", return_value="fixture-token"))
            stack.enter_context(patch.object(backend, "chatgpt2api_base_url", return_value=NODE["baseUrl"]))
            stack.enter_context(patch.object(backend, "generate_ai_image_tasks_with_transient_retry", side_effect=run_async))
            stack.enter_context(patch.object(backend, "image_bytes_list_from_chatgpt2api_response", return_value=[RESULT_IMAGE]))
            stack.enter_context(patch("requests.Session", return_value=session))
            stack.enter_context(patch("requests.post", side_effect=submit))
            if fields.get("suiteKey"):
                count = backend.normalize_ai_image_suite_count(fields["suiteKey"], fields.get("suiteCount"))
                pages = [
                    {"page": index + 1, "title": f"Page {index + 1}", "focus": f"Page {index + 1}", "pageArchetype": "lifestyle", "hasHuman": True}
                    for index in range(count)
                ]
                pages[0]["primaryVariantReferenceIndex"] = int(fields.get("fixturePrimaryIndex", 1))
                prompts = [f"{RAW_PROMPT}\n[Page identity] {index + 1}" for index in range(count)]
                stack.enter_context(patch.object(backend, "build_ai_image_suite_prompts", return_value=(prompts, pages)))
                stack.enter_context(patch.object(backend, "require_ai_image_cod_source_coverage"))
                stack.enter_context(patch.object(backend, "ai_image_jp_company_prompt_status", return_value={"ready": True}))
            if atelier:
                fields.update({
                    "atelierProjectId": "a" * 32, "atelierRevision": 1,
                    "atelierPageNumber": 1, "atelierFingerprint": "local-fixture-fingerprint",
                })
                spec = {"prompt": fields["prompt"], "referenceImages": originals}
                stack.enter_context(patch.object(cod_prompt_render, "validate_execution", return_value=spec))
                stack.enter_context(patch.object(cod_prompt_render, "archive_results", return_value=""))
            if text_only:
                result = backend.generate_ad_launch_ai_image(fields, ACTOR)
            else:
                result = backend.generate_ad_launch_ai_image_edit(fields, files, ACTOR)
        self.assertTrue(result["ok"])
        self.assertEqual(len(submitted), 1)
        return submitted[0], result

    @staticmethod
    def body(request):
        return request.get("data", request.get("json", {}))

    def assert_product_bytes(self, request, expected=None):
        actual = [item[1] for item in request["files"] if item[0] == "image"]
        self.assertEqual(actual, expected or [("product.png", PRODUCT_BYTES, "image/png")])

    def test_sync_reference_request_upgrades_auto_and_preserves_product_original(self):
        request, result = self.generate()
        body = self.body(request)
        self.assertTrue(request["endpoint"].endswith("/images/edits"))
        self.assertEqual(body["model"], MODEL)
        self.assertEqual(body["quality"], "high")
        self.assert_product_bytes(request)
        self.assertIn(RAW_PROMPT, body["prompt"])
        self.assertEqual(body["prompt"].count(MARKER), 1)
        self.assertEqual(result["material"]["quality"], "high")

    def test_detail_helper_is_append_only_and_idempotent(self):
        decorated = backend.ai_image_sunburst_product_detail_prompt(RAW_PROMPT)
        self.assertTrue(decorated.startswith(RAW_PROMPT + "\n"))
        self.assertEqual(backend.ai_image_sunburst_product_detail_prompt(decorated), decorated)
        self.assertEqual(decorated.count(MARKER), 1)
        for required in ("silhouette", "relative dimensions", "component counts", "color", "material", "physically printed"):
            self.assertIn(required, decorated)
        self.assertIn("permitted marketing copy", decorated)
        self.assertIn("layout, style and scene references control presentation only", decorated)

    def test_explicit_product_edits_remain_in_prompt_with_only_named_change_allowed(self):
        current_request = "把主商品改为蓝色，只替换左侧扣子；所有其他结构与原图一致。"
        request, _ = self.generate(overrides={"prompt": current_request})
        prompt = self.body(request)["prompt"]
        self.assertTrue(prompt.startswith(current_request + "\n"))
        self.assertIn("apply only that named change and preserve every unspecified feature", prompt)

    def test_detail_contract_over_limit_stops_instead_of_truncating_source_text(self):
        original = "x" * backend.AI_IMAGE_PROVIDER_PROMPT_LIMIT
        with self.assertRaisesRegex(ValueError, "完整提示词过长"):
            backend.ai_image_sunburst_product_detail_prompt(original)

    def test_async_reference_request_keeps_same_model_quality_bytes_and_text(self):
        request, result = self.generate(async_api=True)
        body = self.body(request)
        self.assertTrue(request["endpoint"].endswith("/api/image-tasks/edits"))
        self.assertEqual(body["model"], MODEL)
        self.assertEqual(body["quality"], "high")
        self.assert_product_bytes(request)
        self.assertIn(RAW_PROMPT, body["prompt"])
        self.assertEqual(body["prompt"].count(MARKER), 1)
        self.assertEqual(result["material"]["model"], MODEL)

    def test_explicit_quality_is_preserved_on_both_transports(self):
        for async_api in (False, True):
            for quality in ("low", "medium", "high"):
                with self.subTest(async_api=async_api, quality=quality):
                    request, _ = self.generate(async_api=async_api, overrides={"quality": quality})
                    self.assertEqual(self.body(request)["quality"], quality)
                    self.assertIn(MARKER, self.body(request)["prompt"])

    def test_non_target_models_keep_auto_and_receive_no_new_fidelity_clause(self):
        for model in ("gpt-image-2", "gpt-image-2.5", "gpt-image-2.5-flare", "codex-gpt-image-2", "auto"):
            for async_api in (False, True):
                with self.subTest(model=model, async_api=async_api):
                    request, _ = self.generate(async_api=async_api, overrides={"model": model})
                    body = self.body(request)
                    self.assertEqual(body["model"], model)
                    self.assertEqual(body.get("quality", "auto"), "auto")
                    self.assertNotIn(MARKER, body["prompt"])
                    self.assert_product_bytes(request)

    def test_text_only_generation_has_no_reference_lock_or_quality_promotion(self):
        for async_api in (False, True):
            with self.subTest(async_api=async_api):
                request, _ = self.generate(async_api=async_api, text_only=True)
                body = self.body(request)
                self.assertNotIn("files", request)
                self.assertEqual(body["model"], MODEL)
                self.assertEqual(body.get("quality", "auto"), "auto")
                self.assertNotIn(MARKER, body["prompt"])

    def test_no_reference_edit_stops_before_provider_dispatch(self):
        with self.assertRaisesRegex(ValueError, "上传参考图片"):
            self.generate(references=[])

    def test_inpaint_keeps_mask_rule_and_original_auto_quality(self):
        request, result = self.generate(overrides={"mode": "inpaint"})
        self.assertNotIn(MARKER, self.body(request)["prompt"])
        self.assertEqual(self.body(request).get("quality", "auto"), "auto")
        self.assertEqual([item[0] for item in request["files"]], ["image", "mask"])
        self.assertEqual(request["files"][1][1], ("mask.png", b"MASK-ORIGINAL-BYTES", "image/png"))
        self.assert_product_bytes(request)
        self.assertTrue(result["maskUsed"])

    def test_frozen_atelier_prompt_remains_byte_for_byte_without_new_lock(self):
        for async_api in (False, True):
            with self.subTest(async_api=async_api):
                request, _ = self.generate(async_api=async_api, atelier=True)
                self.assertEqual(self.body(request)["prompt"], RAW_PROMPT)
                self.assertEqual(self.body(request).get("quality", "auto"), "auto")
                self.assert_product_bytes(request)

    def test_direct_completed_page_edit_has_only_old_page_and_no_product_lock(self):
        completed = ("completed-page.png", b"COMPLETED-PAGE-ORIGINAL", "image/png")
        for async_api in (False, True):
            with self.subTest(async_api=async_api):
                request, _ = self.generate(
                    async_api=async_api, suite=True, overrides={"suiteEditSource": True},
                    references=[("product.png", PRODUCT_BYTES, "image/png"), completed],
                )
                self.assert_product_bytes(request, [completed])
                self.assertNotIn(MARKER, self.body(request)["prompt"])

    def test_suite_page_prompts_receive_the_lock_instead_of_only_base_prompt(self):
        for async_api in (False, True):
            with self.subTest(async_api=async_api):
                request, result = self.generate(async_api=async_api, suite=True)
                self.assertEqual(self.body(request)["prompt"].count(MARKER), 1)
                self.assertIn("[Page identity] 1", self.body(request)["prompt"])
                self.assertIn("軽やかな着心地 / ゆったりシルエット", self.body(request)["prompt"])
                self.assertIn(MARKER, result["material"]["prompt"])

    def test_suite_fast_profile_retains_medium_quality(self):
        request, _ = self.generate(suite=True, overrides={"generationProfile": "fast"})
        self.assertEqual(self.body(request)["quality"], "medium")

    def test_single_fast_profile_keeps_explicit_quality_or_auto(self):
        for quality in ("auto", "low", "medium", "high"):
            with self.subTest(quality=quality):
                request, _ = self.generate(overrides={"generationProfile": "fast", "quality": quality})
                self.assertEqual(self.body(request).get("quality", "auto"), quality)

    def test_explicit_style_or_person_only_references_are_not_product_sources(self):
        for role in ("layout", "scene", "person"):
            with self.subTest(role=role):
                request, _ = self.generate(overrides={"referenceBindings": json.dumps([
                    {"index": 1, "role": role, "name": "fixture.png"},
                ])})
                self.assertEqual(self.body(request).get("quality", "auto"), "auto")
                self.assertNotIn(MARKER, self.body(request)["prompt"])

    def test_standalone_direct_image_edit_preserves_original_prompt_and_quality(self):
        request, _ = self.generate(overrides={"templateKey": "directImageEdit"})
        self.assertEqual(self.body(request)["prompt"], RAW_PROMPT)
        self.assertEqual(self.body(request).get("quality", "auto"), "auto")

    @staticmethod
    def crowded_references():
        roles = ("product", "person", "person", "usage", "usage", "detail", "detail", "product", "layout")
        refs = [(f"{role}-{index}.png", f"ORIGINAL-{role}-{index}".encode(), "image/png") for index, role in enumerate(roles, start=1)]
        bindings = [{"index": index, "role": role, "name": refs[index - 1][0]} for index, role in enumerate(roles, start=1)]
        return refs, bindings

    def test_jp25_crowded_human_page_reserves_a_detail_original(self):
        references, bindings = self.crowded_references()
        before = deepcopy((references, bindings))
        selected = backend.ai_image_jp25_page_reference_indexes(
            {"page": 1, "hasHuman": True, "pageArchetype": "lifestyle", "primaryVariantReferenceIndex": 8},
            references, bindings, max_images=4,
        )
        self.assertEqual(selected[0], 8)
        self.assertLessEqual(len(selected), 4)
        self.assertTrue(set(selected) & {6, 7}, selected)
        self.assertTrue(set(selected) & {2, 3}, selected)
        self.assertTrue(set(selected) & {4, 5}, selected)
        self.assertNotIn(9, selected)
        self.assertEqual((references, bindings), before)

    def test_jp25_transport_uses_four_originals_including_detail_and_remapped_numbering(self):
        references, bindings = self.crowded_references()
        for async_api in (False, True):
            with self.subTest(async_api=async_api):
                request, _ = self.generate(
                    async_api=async_api, references=references, overrides={
                        "suiteKey": backend.AI_IMAGE_LANDING_SUITE_KEY,
                        "suiteCount": 25, "suitePageIndexes": "[1]", "fixturePrimaryIndex": 8,
                        "referenceBindings": json.dumps(bindings),
                    },
                )
                sent = [item[1] for item in request["files"] if item[0] == "image"]
                self.assertEqual(len(sent), 4)
                self.assertEqual(sent[0], references[7])
                self.assertTrue(any(item in references[5:7] for item in sent), sent)
                self.assertNotIn(references[8], sent)
                self.assertTrue(all(item in references for item in sent))
                prompt = self.body(request)["prompt"]
                self.assertIn(MARKER, prompt)
                self.assertIn("Image 1=主商品", prompt)
                self.assertIn('file="product-8.png"', prompt)
                self.assertIn("source upload 8", prompt)


if __name__ == "__main__":
    unittest.main()
