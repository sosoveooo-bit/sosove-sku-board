"""Offline regressions for source-complete COD hook product recognition."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from sku_board import backend, cod_hook_vision as vision


class CodHookVisionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="cod-hook-vision-")
        self.addCleanup(temporary.cleanup)
        self.data_dir = Path(temporary.name)
        self.patch(patch.object(backend, "DATA_DIR", self.data_dir))
        self.patch(patch("requests.sessions.Session.request", side_effect=AssertionError("Network disabled")))
        self.settings = {
            "enabled": True, "baseUrl": "https://private.example.invalid/v1",
            "apiKey": "test-only-secret-key", "model": "gpt-5.6-terra",
            "fallbackModels": ["gpt-5.6-sol"], "visionEnabled": True, "timeout": 60,
        }
        self.loader = self.patch(patch.object(backend, "load_ai_director_settings", side_effect=lambda: deepcopy(self.settings)))
        self.converter = self.patch(patch.object(backend, "ai_director_reference_data_url", side_effect=lambda ref: "data:image/png;base64," + ref[1].hex()))
        self.invoke = self.patch(patch.object(backend, "invoke_ai_director_chat", side_effect=self.response))
        self.actor = {"username": "test-owner"}
        self.refs = [("front.png", b"original-front", "image/png"), ("back.png", b"original-back", "image/png")]
        self.brief = "日语噱头主图，卖点：宽松版型、前侧口袋、穿着方便。只根据当前图展示产品；不要价格。"
        self.payload = self.make_payload()

    def patch(self, patcher):
        value = patcher.start()
        self.addCleanup(patcher.stop)
        return value

    def make_payload(self, count=2):
        return {
            "productName": "宽松短袖外套", "summary": "按实际正背图识别的宽松外套。",
            "primaryReferenceIndex": 1, "uncertainties": ["成分待核实"],
            "references": [{
                "index": index, "role": "product" if index < 3 else "detail",
                "productMatch": "confirmed", "variantId": "khaki",
                "view": "front" if index == 1 else "back" if index == 2 else "close-up",
                "summary": "当前产品已见视图", "colors": ["卡其色"],
                "structure": ["前贴袋" if index == 1 else "背部直线接缝"],
                "materials": ["可见细微织纹"], "usage": [], "uncertainties": [],
            } for index in range(1, count + 1)],
        }

    def response(self, settings, messages):
        settings["_lastDirectorCall"] = {"model": "gpt-5.6-sol", "attempts": [{"model": "gpt-5.6-sol", "status": "ok"}]}
        return json.dumps(self.payload, ensure_ascii=False), 12

    def analyze(self, **kwargs):
        values = dict(actor=self.actor, brief=self.brief, references=self.refs, submitted_bindings=[], country="JP", hook_type="pain-point")
        values.update(kwargs)
        return vision.analyze(**values)

    def test_all_images_sent_individually_and_success_reports_actual_model(self):
        refs = [(str(index), bytes([index]), "image/png") for index in range(1, 17)]
        self.payload = self.make_payload(16)
        updates = []
        result = self.analyze(references=refs, progress=updates.append)
        messages = self.invoke.call_args.args[1]
        images = [item for item in messages[1]["content"] if item["type"] == "image_url"]
        self.assertEqual(len(images), 16)
        self.assertTrue(all(item["image_url"]["detail"] == "high" for item in images))
        self.assertEqual(self.converter.call_count, 16)
        self.assertEqual(result["referenceCount"], 16)
        self.assertEqual(result["model"], "gpt-5.6-sol")
        self.assertEqual(result["sourceModels"], ["gpt-5.6-sol"])
        self.assertEqual([item["status"] for item in updates], ["analyzing", "ready"])
        public = json.dumps(updates)
        self.assertNotIn(self.settings["baseUrl"], public)
        self.assertNotIn(self.settings["apiKey"], public)
        self.assertNotIn("_referenceHashes", public)

    def test_all_auto_default_bindings_including_first_are_reclassified(self):
        self.payload["references"][0].update(role="layout", productMatch="different", variantId="")
        self.payload["primaryReferenceIndex"] = 2
        result = self.analyze(submitted_bindings=[{"role": "product", "roleSource": "default"}, {"role": "layout", "roleSource": "auto"}])
        self.assertEqual(result["referenceBindings"][0]["role"], "layout")
        self.assertEqual(result["referenceBindings"][1]["role"], "product")
        self.assertEqual(result["primaryReferenceIndex"], 2)
        request = json.loads(self.invoke.call_args.args[1][1]["content"][0]["text"])
        self.assertTrue(all(item["role"] == "auto" for item in request["submittedRoleBindings"]))

    def test_manual_role_is_preserved_but_does_not_bypass_matching(self):
        self.payload["references"][1].update(role="detail", productMatch="different", variantId="other")
        result = self.analyze(submitted_bindings=[{}, {"role": "product", "roleSource": "manual"}])
        binding = result["referenceBindings"][1]
        self.assertEqual((binding["role"], binding["roleSource"], binding["productMatch"]), ("product", "manual", "different"))
        prepared = vision.prepare_generation("original prompt", result, self.refs, 1)
        self.assertEqual(prepared["sourceIndexesByOutput"], [[1]])

    def test_switching_a_manual_role_back_to_auto_clears_the_override(self):
        self.payload["references"][0].update(role="layout", productMatch="different", variantId="")
        self.payload["primaryReferenceIndex"] = 2
        result = self.analyze(submitted_bindings=[{"role": "auto", "roleSource": "manual"}])
        self.assertEqual(result["referenceBindings"][0]["role"], "layout")
        self.assertEqual(result["referenceBindings"][0]["roleSource"], "ai-director")

    def test_recognition_normalizes_role_and_match_whitespace_and_case(self):
        self.payload["references"][0].update(role="  PRODUCT ", productMatch=" Confirmed ")
        self.payload["references"][1].update(role=" STYLEset ", productMatch=" DIFFERENT ")
        result = self.analyze()
        first, second = result["referenceBindings"]
        self.assertEqual((first["role"], first["productMatch"]), ("product", "confirmed"))
        self.assertEqual((second["role"], second["productMatch"]), ("styleSet", "different"))
        self.assertEqual(vision.prepare_generation("prompt", result, self.refs, 1)["sourceIndexesByOutput"], [[1]])

    def test_confirmed_product_needs_visual_color_structure_or_surface_evidence(self):
        for facts in ({"colors": [], "structure": [], "materials": []}, {"colors": [], "structure": ["FDA certification"], "materials": ["100% cotton"]}):
            with self.subTest(facts=facts):
                self.payload = self.make_payload()
                self.payload["references"][0].update(**facts, summary="这是一张产品图片。")
                updates = []
                with self.assertRaisesRegex(vision.CodHookAnalysisError, "颜色、结构或表面细节"):
                    self.analyze(progress=updates.append)
                self.assertEqual([item["status"] for item in updates], ["analyzing", "failed"])
                self.assertEqual(list(self.data_dir.rglob("*.json")), [])

    def test_primary_index_must_be_an_integer_not_bool_float_or_text(self):
        for primary in (True, 1.0, "1"):
            with self.subTest(primary=primary):
                self.payload = self.make_payload()
                self.payload["primaryReferenceIndex"] = primary
                with self.assertRaisesRegex(vision.CodHookAnalysisError, "主产品图编号"):
                    self.analyze()
                self.assertEqual(list(self.data_dir.rglob("*.json")), [])

    def test_exact_result_reuses_cache_without_second_model_call(self):
        first = self.analyze()
        second = self.analyze()
        self.assertFalse(first["cached"])
        self.assertTrue(second["cached"])
        self.assertEqual(first["analysisKey"], second["analysisKey"])
        self.assertEqual(self.invoke.call_count, 1)
        saved = list(self.data_dir.rglob("*.json"))
        self.assertEqual(len(saved), 1)
        raw = saved[0].read_text(encoding="utf-8")
        self.assertNotIn(self.settings["apiKey"], raw)
        self.assertNotIn(self.settings["baseUrl"], raw)

    def test_cache_is_bound_to_owner_image_bytes_full_brief_roles_country_and_model(self):
        base = self.analyze()["analysisKey"]
        variants = [
            {"actor": {"username": "another-owner"}},
            {"references": [("front.png", b"DIFFERENT-BYTES-SAME-NAME", "image/png"), self.refs[1]]},
            {"brief": self.brief + "\n新增末尾卖点必须保留"},
            {"submitted_bindings": [{"role": "product", "roleSource": "manual"}]},
            {"country": "UK"}, {"hook_type": "comparison"},
        ]
        seen = {base}
        for values in variants:
            result = self.analyze(**values)
            self.assertFalse(result["cached"])
            self.assertNotIn(result["analysisKey"], seen)
            seen.add(result["analysisKey"])
        self.settings["model"] = "gpt-5.6-sol"
        self.assertNotIn(self.analyze()["analysisKey"], seen)
        self.settings["apiKey"] = "test-only-other-secret"
        self.assertFalse(self.analyze()["cached"])

    def test_expired_cache_is_reanalyzed(self):
        self.analyze()
        path = next(self.data_dir.rglob("*.json"))
        cache = json.loads(path.read_text(encoding="utf-8"))
        cache["createdAt"] = time.time() - vision.CACHE_TTL_SECONDS - 1
        path.write_text(json.dumps(cache), encoding="utf-8")
        self.assertFalse(self.analyze()["cached"])
        self.assertEqual(self.invoke.call_count, 2)

    def test_incomplete_duplicate_index_invalid_role_and_missing_product_fail_closed(self):
        for name in ("missing", "duplicate", "role", "match", "no-product", "primary"):
            with self.subTest(name=name):
                self.payload = self.make_payload()
                if name == "missing": self.payload["references"].pop()
                elif name == "duplicate": self.payload["references"][1]["index"] = 1
                elif name == "role": self.payload["references"][0]["role"] = "invented-role"
                elif name == "match": self.payload["references"][0].pop("productMatch")
                elif name == "no-product":
                    for item in self.payload["references"]: item["productMatch"] = "uncertain"
                else: self.payload["primaryReferenceIndex"] = 3
                updates = []
                with self.assertRaises(vision.CodHookAnalysisError):
                    self.analyze(progress=updates.append)
                self.assertEqual([item["status"] for item in updates], ["analyzing", "failed"])
                self.assertEqual(list(self.data_dir.rglob("*.json")), [])

    def test_disabled_missing_configuration_and_vision_off_fail_before_model_call(self):
        for key, value in (("enabled", False), ("apiKey", ""), ("visionEnabled", False)):
            previous = self.settings[key]
            with self.subTest(key=key):
                self.settings[key] = value
                with self.assertRaises(vision.CodHookAnalysisError):
                    self.analyze()
                self.invoke.assert_not_called()
            self.settings[key] = previous

    def test_model_failure_is_public_and_does_not_cache_or_emit_ready(self):
        self.invoke.side_effect = RuntimeError("HTTP 408 https://private.example.invalid/v1 Authorization: test-only-secret-key")
        updates = []
        with self.assertRaisesRegex(vision.CodHookAnalysisError, "图片尚未提交") as caught:
            self.analyze(progress=updates.append)
        self.assertNotIn("test-only-secret-key", str(caught.exception))
        self.assertNotIn("https://", str(caught.exception))
        self.assertEqual([item["status"] for item in updates], ["analyzing", "failed"])
        self.assertEqual(list(self.data_dir.rglob("*.json")), [])

    def test_bad_json_does_not_become_local_analysis(self):
        self.invoke.side_effect = None
        self.invoke.return_value = ("not json", 1)
        with self.assertRaises(vision.CodHookAnalysisError):
            self.analyze()
        self.assertEqual(list(self.data_dir.rglob("*.json")), [])

    def test_more_than_16_or_empty_uploads_are_rejected_without_slicing(self):
        for refs in ([], [self.refs[0]] * 17, [("empty.png", b"", "image/png")]):
            with self.subTest(count=len(refs)):
                with self.assertRaises(vision.CodHookAnalysisError):
                    self.analyze(references=refs)
        self.invoke.assert_not_called()

    def test_same_variant_front_back_is_one_variant_and_original_bytes_survive(self):
        analysis = self.analyze()
        prepared = vision.prepare_generation("COMPLETE ORIGINAL", analysis, self.refs, 3)
        self.assertEqual(prepared["variantIdsByOutput"], [["khaki"], ["khaki"], ["khaki"]])
        self.assertEqual(prepared["sourceIndexesByOutput"], [[1, 2]] * 3)
        self.assertEqual(prepared["referencesByOutput"], [self.refs] * 3)
        self.assertEqual(prepared["productReferenceIndexes"], [1, 2])
        self.assertTrue(all(prompt.startswith("COMPLETE ORIGINAL\n\n") for prompt in prepared["prompts"]))

    def test_twenty_outputs_supported_with_two_original_references(self):
        result = self.analyze()
        prepared = vision.prepare_generation("original", result, self.refs, 20)
        self.assertEqual(len(prepared["prompts"]), 20)
        self.assertEqual(prepared["referencesByOutput"], [self.refs] * 20)

    def test_multiple_true_variants_rotate_and_never_mix_colorways(self):
        self.payload = self.make_payload(4)
        self.refs.extend([("blue.png", b"blue-original", "image/png"), ("blue-detail.png", b"blue-detail", "image/png")])
        self.payload["references"][2].update(role="product", variantId="blue", colors=["蓝色"])
        self.payload["references"][3].update(role="detail", variantId="blue", colors=["蓝色"])
        analysis = self.analyze()
        prepared = vision.prepare_generation("全部卖点", analysis, self.refs, 4)
        self.assertEqual(prepared["sourceIndexesByOutput"], [[1, 2], [3, 4], [1, 2], [3, 4]])
        self.assertEqual(prepared["variantIdsByOutput"], [["khaki"], ["blue"], ["khaki"], ["blue"]])
        self.assertEqual(prepared["referencesByOutput"][1][0][1], b"blue-original")
        combined = vision.prepare_generation("所有配色一起展示", analysis, self.refs, 1)
        self.assertEqual(combined["variantIdsByOutput"], [["khaki", "blue"]])
        self.assertEqual(combined["sourceIndexesByOutput"], [[1, 2, 3, 4]])

    def test_layout_scene_styles_and_uncertain_mismatched_products_are_not_attached(self):
        self.refs = [(str(index), bytes([index]), "image/png") for index in range(1, 10)]
        self.payload = self.make_payload(9)
        roles = ["layout", "product", "detail", "usage", "package", "person", "styleSet", "scene", "product"]
        for item, role in zip(self.payload["references"], roles):
            item.update(role=role, summary="柔和侧光与适中间距" if role in {"layout", "styleSet", "scene"} else "真实产品细节")
        self.payload["references"][8]["productMatch"] = "uncertain"
        self.payload["primaryReferenceIndex"] = 2
        analysis = self.analyze()
        prepared = vision.prepare_generation("用户原文", analysis, self.refs, 1)
        self.assertEqual(prepared["sourceIndexesByOutput"], [[2, 3, 4, 5, 6]])
        self.assertIn('"referenceImage":1,"role":"product"', prepared["prompt"])
        self.assertIn('"uploadedSourceIndex":2', prepared["prompt"])
        self.assertIn("柔和侧光与适中间距", prepared["prompt"])
        self.assertEqual(prepared["referencesByOutput"][0][0], self.refs[1])

    def test_unanchored_detail_variant_becomes_uncertain_not_an_extra_product(self):
        self.payload["references"][1].update(role="detail", variantId="unproven-red")
        result = self.analyze()
        self.assertEqual(result["referenceBindings"][1]["productMatch"], "uncertain")
        prepared = vision.prepare_generation("original", result, self.refs, 2)
        self.assertEqual(prepared["sourceIndexesByOutput"], [[1], [1]])

    def test_full_brief_and_text_policy_not_compressed_or_replaced(self):
        original = ("第1点：保留双排扣和原色。\n" * 150) + "尾部原始文案：裾まで、自然な落ち感。\n[TEXT CONTRACT] textPolicy=none\n用户明确只改背景。"
        self.analyze(brief=original)
        sent = json.loads(self.invoke.call_args.args[1][1]["content"][0]["text"])
        self.assertEqual(sent["completeUserBrief"], original)
        prepared = vision.prepare_generation(original, self.analyze(brief=original), self.refs, 1)
        self.assertEqual(prepared["prompt"][:len(original)], original)
        self.assertEqual(prepared["prompt"].count("[TEXT CONTRACT] textPolicy=none"), 1)
        self.assertIn("Only an explicit user-requested change", prepared["prompt"])

    def test_hallucinated_certifications_composition_and_performance_not_identity_facts(self):
        self.payload["references"][0].update(materials=["可见织纹", "100% cotton", "ABS"], structure=["前贴袋", "FDA certification", "扭力5倍"])
        result = self.analyze()
        self.assertNotIn("100% cotton", result["materials"])
        self.assertNotIn("ABS", result["materials"])
        self.assertNotIn("FDA certification", result["structure"])
        self.assertIn("前贴袋", result["structure"])
        self.assertTrue(result["uncertainties"])
        final = vision.prepare_generation("用户的完整需求", result, self.refs, 1)["prompt"]
        self.assertNotIn("100% cotton", final)
        self.assertNotIn("扭力5倍", final)

    def test_changed_uploads_or_client_like_result_block_prepare_generation(self):
        result = self.analyze()
        with self.assertRaisesRegex(vision.CodHookAnalysisError, "已变化"):
            vision.prepare_generation("prompt", result, [("front.png", b"changed", "image/png"), self.refs[1]], 1)
        for analysis in ({"status": "ready", "source": "ai"}, {**result, "source": "local"}):
            with self.assertRaises(vision.CodHookAnalysisError):
                vision.prepare_generation("prompt", analysis, self.refs, 1)

    def test_over_budget_is_rejected_instead_of_cutting_original_text(self):
        with self.assertRaises(vision.CodHookAnalysisError):
            self.analyze(brief="x" * 64001)
        result = self.analyze()
        with self.assertRaisesRegex(vision.CodHookAnalysisError, "64000"):
            vision.prepare_generation("x" * 63999, result, self.refs, 1)

    def test_same_key_concurrent_requests_use_one_online_recognition(self):
        original = self.response
        def delayed(settings, messages):
            time.sleep(.06)
            return original(settings, messages)
        self.invoke.side_effect = delayed
        results, failures = [], []
        def work():
            try: results.append(self.analyze())
            except Exception as exc: failures.append(exc)
        threads = [threading.Thread(target=work) for _ in range(3)]
        for thread in threads: thread.start()
        for thread in threads: thread.join(timeout=2)
        self.assertEqual(failures, [])
        self.assertEqual(len(results), 3)
        self.assertEqual(self.invoke.call_count, 1)
        self.assertEqual(sum(bool(item["cached"]) for item in results), 2)


if __name__ == "__main__":
    unittest.main()
