"""Regression coverage for server-backed COD main observation provenance."""

from copy import deepcopy
import hashlib
from io import BytesIO
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from sku_board import backend


class CodMainProvenanceTests(unittest.TestCase):
    PROMPT = "[Product] Exact manual kitchen opener."
    BRIEF = "主卖点：\n1. 省力开盖：正确握持打开瓶盖。"
    EVIDENCE_KEY = "a" * 64
    ORIGINAL_REFERENCE = b"original-reference-fixture"
    SERVER_FACTS = ("弧形握柄", "环形接触面", "可见防滑纹理")

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="cod-main-provenance-")
        self.addCleanup(temporary.cleanup)
        data_dir = Path(temporary.name)
        for name, value in (
            ("DATA_DIR", data_dir),
            ("DATA_FILE", data_dir / "board.json"),
            ("AI_DIRECTOR_SETTINGS_FILE", data_dir / "director.json"),
            ("AI_DIRECTOR_CACHE_FILE", data_dir / "cache.json"),
        ):
            self.start_patch(patch.object(backend, name, value))
        for name in (
            "invoke_ai_director_chat",
            "load_ai_director_settings",
            "put_ai_director_cached_analysis",
            "save_ai_image_outputs",
        ):
            self.start_patch(patch.object(backend, name, side_effect=AssertionError(f"Unexpected model/store operation: {name}")))
        self.cache = self.start_patch(patch.object(backend, "get_ai_director_cached_analysis", return_value=None))
        self.start_patch(patch("requests.sessions.Session.request", side_effect=AssertionError("Network disabled")))

    def start_patch(self, patcher):
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    @classmethod
    def input_digest(cls, brief=None):
        value = cls.BRIEF if brief is None else brief
        normalized = backend.normalize_ai_image_source_contract_text(value or cls.PROMPT, backend.AI_IMAGE_SUITE_BRIEF_LIMIT)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def server_analysis(self, **overrides):
        result = {
            "_codMainVisionUsed": True,
            "_codMainInputDigest": self.input_digest(),
            "_codMainEvidenceKey": self.EVIDENCE_KEY,
            "_codMainReferenceHashes": [hashlib.sha256(self.ORIGINAL_REFERENCE).hexdigest()],
            "productVisualDNA": {
                "shapeAnchors": list(self.SERVER_FACTS[:2]),
                "materialAnchors": [self.SERVER_FACTS[2]],
            },
        }
        result.update(overrides)
        return result

    def browser_plan(self, key=None):
        pages = backend.build_ai_image_suite_plan(
            self.PROMPT, self.BRIEF, "750x1000",
            suite_key=backend.AI_IMAGE_COD_SUITE_KEY, country="JP", count=30,
        )
        pages[0]["codMainRich"] = True
        pages[0]["codMainSupportingPoints"] = [{
            "sourceId": "image:shapeAnchors:777",
            "title": "浏览器伪造的双层缓冲结构",
            "description": "This value was not produced by the current server analysis",
            "label": "FDA認証",
            "sourceType": "image_observation",
        }]
        pages[0]["copyLabels"] = ["FDA認証"]
        if key is not None:
            pages[0]["codMainEvidenceKey"] = key
        return pages

    def compile(self, pages, brief=None):
        return backend.build_ai_image_suite_prompts(
            self.PROMPT, self.BRIEF if brief is None else brief, "750x1000",
            suite_key=backend.AI_IMAGE_COD_SUITE_KEY, country="JP", suite_count=30, plan=pages,
        )

    def assert_no_untrusted_observation(self, prompts, pages):
        observations = [
            point
            for page in pages
            for point in page.get("codMainSupportingPoints") or []
            if point["sourceType"] == "image_observation"
        ]
        self.assertEqual(observations, [])
        self.assertNotIn("FDA認証", "\n".join(prompts))
        self.assertNotIn("浏览器伪造的双层缓冲结构", "\n".join(prompts))
        self.assertFalse(pages[0].get("codMainEvidenceKey"))

    def test_browser_observation_without_server_key_is_discarded(self):
        pages = self.browser_plan()
        before = deepcopy(pages)
        prompts, compiled = self.compile(pages)
        self.assert_no_untrusted_observation(prompts, compiled)
        self.cache.assert_not_called()
        self.assertEqual(pages, before)

    def test_invalid_key_missing_cache_or_mismatched_input_cannot_reuse_observations(self):
        cases = (
            ("invalid-key", "not-a-server-key", None, self.BRIEF),
            ("cache-missing", self.EVIDENCE_KEY, None, self.BRIEF),
            ("digest-mismatch", self.EVIDENCE_KEY, self.server_analysis(_codMainInputDigest="b" * 64), self.BRIEF),
            ("vision-not-used", self.EVIDENCE_KEY, self.server_analysis(_codMainVisionUsed=False), self.BRIEF),
            ("brief-changed", self.EVIDENCE_KEY, self.server_analysis(), self.BRIEF + "\n背景：浅灰色。"),
        )
        for name, key, cache, brief in cases:
            with self.subTest(case=name):
                self.cache.reset_mock()
                self.cache.return_value = cache
                prompts, compiled = self.compile(self.browser_plan(key), brief)
                self.assert_no_untrusted_observation(prompts, compiled)
                if name == "invalid-key":
                    self.cache.assert_not_called()
                else:
                    self.cache.assert_any_call(self.EVIDENCE_KEY)

    def test_matching_server_inventory_rebuilds_labels_instead_of_trusting_browser_values(self):
        server = self.server_analysis()
        before_server = deepcopy(server)
        self.cache.return_value = server
        prompts, compiled = self.compile(self.browser_plan(self.EVIDENCE_KEY))
        inventory = compiled[0]["codMainSupportingPoints"]
        observed = [point for point in inventory if point["sourceType"] == "image_observation"]
        self.assertEqual({point["title"] for point in observed}, set(self.SERVER_FACTS))
        self.assertEqual(len(observed), 3)
        for point in observed:
            self.assertEqual(point["label"], point["title"])
            self.assertNotEqual(point["sourceId"], "image:shapeAnchors:777")
        self.assertEqual(compiled[0]["codMainEvidenceKey"], self.EVIDENCE_KEY)
        self.assertNotIn("FDA認証", "\n".join(prompts))
        self.assertNotIn("浏览器伪造的双层缓冲结构", "\n".join(prompts))
        for fact in self.SERVER_FACTS:
            self.assertIn(fact, prompts[0])
        self.assertEqual(server, before_server)

    def render_request(self, reference_bytes):
        fields = {
            "prompt": self.PROMPT,
            "model": "gpt-image-2",
            "mode": "edit",
            "size": "750x1000",
            "quality": "high",
            "count": 1,
            "suiteKey": backend.AI_IMAGE_COD_SUITE_KEY,
            "suiteCount": 30,
            "suiteCountry": "JP",
            "suiteBrief": self.BRIEF,
            "suitePlan": json.dumps(self.browser_plan(self.EVIDENCE_KEY), ensure_ascii=False),
            "suitePageIndexes": "[1]",
            "referenceBindings": json.dumps([{"role": "product", "name": "fixture.png"}]),
        }
        files = {"reference0": SimpleNamespace(filename="fixture.png", file=BytesIO(reference_bytes))}
        return fields, files

    def test_changed_product_reference_is_stopped_before_image_dispatch(self):
        self.cache.return_value = self.server_analysis()
        fields, files = self.render_request(b"different-product-reference-fixture")
        with patch.object(backend, "normalize_ai_image_request_fields", return_value=(
            self.PROMPT, "gpt-image-2", "750x1000", "high", 1, 10, 1,
        )), patch.object(backend, "read_ai_image_upload", return_value=("fixture.png", b"different-product-reference-fixture", "image/png")), patch.object(
            backend, "chatgpt2api_image_tasks_enabled", return_value=True,
        ), patch.object(backend, "generate_ai_image_tasks_with_transient_retry", side_effect=AssertionError("Unexpected image dispatch")) as dispatch, patch.object(
            backend, "generate_images_via_acore", side_effect=AssertionError("Unexpected alternate image dispatch"),
        ) as alternate:
            with self.assertRaisesRegex(ValueError, "参考图.*变化|重新策划"):
                backend.generate_ad_launch_ai_image_edit(fields, files, {"role": "admin"})
            dispatch.assert_not_called()
            alternate.assert_not_called()

    def test_matching_product_reference_reaches_only_the_mock_dispatch(self):
        self.cache.return_value = self.server_analysis()
        fields, files = self.render_request(self.ORIGINAL_REFERENCE)
        with patch.object(backend, "normalize_ai_image_request_fields", return_value=(
            self.PROMPT, "gpt-image-2", "750x1000", "high", 1, 10, 1,
        )), patch.object(backend, "read_ai_image_upload", return_value=("fixture.png", self.ORIGINAL_REFERENCE, "image/png")), patch.object(
            backend, "chatgpt2api_image_tasks_enabled", return_value=True,
        ), patch.object(backend, "generate_ai_image_tasks_with_transient_retry", side_effect=RuntimeError("MOCK_DISPATCH_REACHED")) as dispatch:
            with self.assertRaisesRegex(RuntimeError, "MOCK_DISPATCH_REACHED"):
                backend.generate_ad_launch_ai_image_edit(fields, files, {"role": "admin"})
            dispatch.assert_called_once()
            sent_prompts = "\n".join(dispatch.call_args.kwargs.get("prompts") or [])
            self.assertNotIn("FDA認証", sent_prompts)
            for fact in self.SERVER_FACTS:
                self.assertIn(fact, sent_prompts)


if __name__ == "__main__":
    unittest.main()
