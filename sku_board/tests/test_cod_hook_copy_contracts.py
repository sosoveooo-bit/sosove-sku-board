"""COD hook selling copy must survive both isolated image submission paths."""

from contextlib import ExitStack
from io import BytesIO
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from sku_board import backend


STALE_COD_RESTORE_REASON = (
    "Stale assertion for the pre-restore five-Agent COD route. The COD "
    "country/detail planner was intentionally restored to the GitHub main "
    "revision (see docs/plans/2026-09-18-cod-github-restore.md); this "
    "expectation belongs to the removed behaviour and is kept for the rewrite."
)


class MockDispatchReached(RuntimeError):
    """Stop before any renderer, material store or live service is used."""


class CodHookCopyContractTests(unittest.TestCase):
    MARKER = "[COD hook selling-copy contract]"
    OIP_MARKER = "[MOCK OIP APPEND]"
    BRIEF = "多功能拧盖器；卖点：省力握柄、防滑接触面、悬挂收纳；重量500 g。产品结构与上传图一致。"
    MODEL = "gpt-image-2.5-sunburst"
    ACTOR = {"username": "hook-copy-test", "role": "admin"}

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        directory = self.stack.enter_context(tempfile.TemporaryDirectory(prefix="cod-hook-copy-"))
        self.data_dir = Path(directory)
        self.stack.enter_context(patch.dict(os.environ, {"SKU_BOARD_DATA_DIR": directory}))
        for name, value in (
            ("DATA_DIR", self.data_dir),
            ("DATA_FILE", self.data_dir / "board.json"),
            ("AD_LAUNCH_UPLOAD_DIR", self.data_dir / "uploads"),
            ("AI_DIRECTOR_SETTINGS_FILE", self.data_dir / "director.json"),
            ("AI_DIRECTOR_CACHE_FILE", self.data_dir / "director-cache.json"),
        ):
            self.stack.enter_context(patch.object(backend, name, value))
        self.stack.enter_context(patch("requests.sessions.Session.request", side_effect=AssertionError("Network disabled")))
        self.stack.enter_context(patch.object(backend, "ai_image_skill_config", return_value={}))
        self.stack.enter_context(patch.object(backend, "log_ai_image_error"))
        self.oip_enabled = self.stack.enter_context(patch.object(backend, "shared_ai_director_open_prompts_enabled", return_value=False))
        self.stack.enter_context(patch.object(backend, "chatgpt2api_image_tasks_enabled", return_value=True))
        self.dispatch = self.stack.enter_context(patch.object(
            backend, "generate_ai_image_tasks_with_transient_retry", side_effect=MockDispatchReached("MOCK_IMAGE_DISPATCH"),
        ))
        for name in ("invoke_ai_director_chat", "save_ai_image_outputs", "put_ai_director_cached_analysis", "generate_images_via_acore"):
            self.stack.enter_context(patch.object(backend, name, side_effect=AssertionError(f"Unexpected external/store operation: {name}")))
        # These cases isolate copy transport. The mandatory vision stage and
        # its failure/caching semantics are covered by the vision integration tests.
        self.stack.enter_context(patch("sku_board.cod_hook_vision.analyze", side_effect=self.synthetic_analysis))

    @staticmethod
    def synthetic_analysis(*, references, **_kwargs):
        from sku_board import cod_hook_vision
        count = len(references)
        records = [{"index": index, "role": "product", "productMatch": "confirmed", "variantId": f"v{index}",
                    "view": "front", "summary": "Visible product", "structure": ["Reference-confirmed outline"]}
                   for index in range(1, count + 1)]
        submitted = [{"index": index, "role": "auto", "roleSource": "auto"} for index in range(1, count + 1)]
        return cod_hook_vision._normalize({"productName": "Kitchen opener", "summary": "Observed product",
            "primaryReferenceIndex": 1, "references": records}, references, submitted, "fixture-director", "a" * 64)

    def payload(self, **overrides):
        value = {
            "templateKey": "codHook", "codHookType": "hook", "suiteCountry": "JP",
            "suiteBrief": self.BRIEF, "prompt": f"[Product] Exact kitchen opener.\n[Current user prompt]\n{self.BRIEF}",
            "model": self.MODEL, "size": "750x1000", "quality": "high", "count": 1,
        }
        value.update(overrides)
        return value

    def capture_dispatch(self, payload, *, reference_count=0):
        self.dispatch.reset_mock()
        with self.assertRaisesRegex(MockDispatchReached, "MOCK_IMAGE_DISPATCH"):
            if reference_count:
                files = {
                    f"reference{index}": SimpleNamespace(filename=f"fixture-{index}.png", file=BytesIO(f"reference-{index}".encode()))
                    for index in range(reference_count)
                }
                backend.generate_ad_launch_ai_image_edit(payload, files, self.ACTOR)
            else:
                backend.generate_ad_launch_ai_image(payload, self.ACTOR)
        self.dispatch.assert_called_once()
        self.assertEqual(self.dispatch.call_args.kwargs["model"], payload["model"])
        return self.dispatch.call_args.kwargs

    def test_plain_selling_points_default_to_requested_for_every_hook_type(self):
        for hook_type in ("hook", "effect", "promotion", "discount", "comparison", "priceBar"):
            with self.subTest(hook_type=hook_type):
                self.assertEqual(backend.ai_image_cod_hook_text_policy({"codHookType": hook_type}, self.BRIEF), "requested")

    def test_product_only_brief_uses_default_copy_without_claiming_reference_analysis(self):
        brief = "Copy the exact product from the reference."
        payload = self.payload(suiteBrief=brief)
        self.assertEqual(backend.ai_image_cod_hook_text_policy(payload, brief), "requested")
        instruction = backend.ai_image_cod_hook_policy_instruction(payload, brief)
        self.assertIn(self.MARKER, instruction)
        self.assertIn("textPolicy=requested", instruction)

    def test_explicit_no_text_brief_overrides_requested_copy_and_promotion(self):
        for brief in ("无字图片", "不要任何文字", "text-free product photo", "Don't add any text", "Omit the headline"):
            with self.subTest(brief=brief):
                payload = self.payload(textPolicy="requested", codHookType="promotion", suiteBrief=brief)
                self.assertEqual(backend.ai_image_cod_hook_text_policy(payload, brief), "none")
                instruction = backend.ai_image_cod_hook_policy_instruction(payload, brief)
                self.assertIn("textPolicy=none", instruction)

    def test_explicit_submitted_none_is_preserved_for_existing_requests(self):
        payload = self.payload(textPolicy="none")
        self.assertEqual(backend.ai_image_cod_hook_text_policy(payload, self.BRIEF), "none")
        instruction = backend.ai_image_cod_hook_policy_instruction(payload, self.BRIEF)
        self.assertIn("textPolicy=none", instruction)
        for reference_count in (0, 1):
            with self.subTest(reference_count=reference_count):
                sent = self.capture_dispatch(payload, reference_count=reference_count)
                self.assertIn("textPolicy=none", sent["prompt"])

    def test_headline_only_with_no_labels_is_not_mistaken_for_global_no_text(self):
        for brief in ("只要标题：便利な毎日；不要标签", "Only a headline: Easy opening. No labels."):
            with self.subTest(brief=brief):
                payload = self.payload(suiteBrief=brief)
                self.assertEqual(backend.ai_image_cod_hook_text_policy(payload, brief), "requested")
                self.assertIn(self.MARKER, backend.ai_image_cod_hook_policy_instruction(payload, brief))

    def test_standard_hooks_request_source_backed_copy_with_a_realistic_density_budget(self):
        for hook_type in ("hook", "effect", "promotion", "discount"):
            with self.subTest(hook_type=hook_type):
                payload = self.payload(codHookType=hook_type)
                instruction = backend.ai_image_cod_hook_policy_instruction(payload, self.BRIEF)
                self.assertIn("Selling-copy budget", instruction)
                self.assertIn("one prominent core-benefit headline", instruction)
                self.assertRegex(instruction, r"2[-–]3 distinct source-backed short supporting benefit callouts")
                self.assertRegex(instruction, r"1[-–]2 corresponding visual evidence details")
                self.assertIn("headline does not occupy", instruction)
                self.assertIn("actual available benefits when fewer are documented", instruction)
                self.assertIn("never fill the quota", instruction)
                self.assertIn("numbers, units, conditions", instruction)
                self.assertIn("style references provide visual direction, not product claims", instruction)
                self.assertIn("No invented certification, endorsement, performance figure", instruction)

    def test_comparison_retains_two_same_condition_panels_and_one_dimension(self):
        payload = self.payload(codHookType="comparison")
        instruction = backend.ai_image_cod_hook_policy_instruction(payload, self.BRIEF)
        self.assertIn("Comparison budget", instruction)
        self.assertIn("exactly two matched-condition panels", instruction)
        self.assertIn("same supplied difference", instruction)
        self.assertIn("no third panel", instruction)
        self.assertNotIn("Selling-copy budget", instruction)

    def test_price_bar_and_narrow_canvases_keep_compact_copy_instead_of_multi_benefit_rows(self):
        cases = (("priceBar", "750x1000"), ("hook", "750x100"), ("promotion", "750x150"), ("comparison", "750x100"))
        for hook_type, size in cases:
            with self.subTest(hook_type=hook_type, size=size):
                payload = self.payload(codHookType=hook_type, size=size)
                instruction = backend.ai_image_cod_hook_policy_instruction(payload, self.BRIEF)
                self.assertIn("Compact strip budget", instruction)
                self.assertIn("one compact row", instruction)
                self.assertIn("Add no multi-benefit labels", instruction)
                self.assertIn("omit every missing price, currency or offer", instruction)
                self.assertNotIn("Selling-copy budget", instruction)

    def test_price_only_and_title_only_budget_overrides_do_not_add_supports(self):
        cases = (
            ("文案只留价格：JPY 980；2件。不要标签", "Price-only request"),
            ("Price only: USD 12, quantity 2. No labels.", "Price-only request"),
            ("只要标题：便利な毎日；不要标签", "Title-only request"),
            ("Only a headline: Easy opening. No labels.", "Title-only request"),
        )
        for brief, expected in cases:
            with self.subTest(brief=brief):
                payload = self.payload(suiteBrief=brief)
                self.assertEqual(backend.ai_image_cod_hook_text_policy(payload, brief), "requested")
                instruction = backend.ai_image_cod_hook_policy_instruction(payload, brief)
                self.assertIn(expected, instruction)
                self.assertNotIn("Selling-copy budget", instruction)
                no_text = self.payload(suiteBrief=brief + "\n全部无字。")
                self.assertEqual(backend.ai_image_cod_hook_text_policy(no_text, no_text["suiteBrief"]), "none")

    def test_text_compiler_uses_actual_canvas_for_its_copy_budget(self):
        payload = self.payload(size="750x1000")
        prompt = backend.compile_ai_image_cod_hook_text_prompt(payload, payload["prompt"], "750x100")
        self.assertIn("750×100", prompt)
        self.assertIn("Compact strip budget", prompt)
        self.assertNotIn("Selling-copy budget", prompt)

    def test_long_user_brief_keeps_all_selling_points_and_exact_quantities(self):
        source = "产品细节与参考图保持一致。" * 400 + "完整中段卖点：500 g、15 cm、3个配件。" + "展示实际防滑接触面。" * 400 + "尾段要求：日文、去除背景杂物。"
        payload = self.payload(suiteBrief=source)
        prompt = backend.compile_ai_image_cod_hook_text_prompt(payload, payload["prompt"], payload["size"])
        self.assertIn(source, prompt)
        self.assertIn(self.MARKER, prompt)
        self.assertLessEqual(len(prompt), backend.AI_IMAGE_PROVIDER_PROMPT_LIMIT)

    def test_structured_original_user_section_survives_without_suite_brief(self):
        payload = self.payload()
        payload.pop("suiteBrief")
        prompt = backend.compile_ai_image_cod_hook_text_prompt(payload, payload["prompt"], payload["size"])
        self.assertIn(self.BRIEF, prompt)
        self.assertIn(self.MARKER, prompt)

    def test_selected_product_sources_survive_text_and_reference_dispatch(self):
        brief = "为所选商品制作日本噱头图。"
        sources = "防滑TPR握柄; 可悬挂收纳; 本体重量500 g"
        prompt = f"[Product] Exact manual opener.\n[Current user prompt]\n{brief}\n[COD hook selling-point sources] {sources}\n[Material and light] Soft light."
        payload = self.payload(prompt=prompt, suiteBrief=brief)
        for reference_count in (0, 1):
            with self.subTest(reference_count=reference_count):
                sent = self.capture_dispatch(payload, reference_count=reference_count)
                self.assertIn(sources, sent["prompt"])
                self.assertIn("textPolicy=requested", sent["prompt"])
                self.assertIn(self.MARKER, sent["prompt"])

    def test_oversized_hooks_stop_before_source_or_contract_is_cut(self):
        source = "A" * backend.AI_IMAGE_PROVIDER_PROMPT_LIMIT + "TAIL_SELLING_POINT"
        payload = self.payload(prompt=source, suiteBrief=source)
        for reference_count in (0, 1):
            with self.subTest(reference_count=reference_count), self.assertRaisesRegex(ValueError, "完整提示词超过"):
                if reference_count:
                    files = {"reference0": SimpleNamespace(filename="fixture.png", file=BytesIO(b"fixture"))}
                    backend.generate_ad_launch_ai_image_edit(payload, files, self.ACTOR)
                else:
                    backend.generate_ad_launch_ai_image(payload, self.ACTOR)
        self.dispatch.assert_not_called()
        self.assertEqual(payload["suiteBrief"], source)

    def test_text_and_reference_submissions_keep_the_same_visible_copy_contract(self):
        for reference_count in (0, 1):
            with self.subTest(reference_count=reference_count):
                payload = self.payload()
                sent = self.capture_dispatch(payload, reference_count=reference_count)
                self.assertIn(self.BRIEF, sent["prompt"])
                self.assertIn(self.MARKER, sent["prompt"])
                self.assertIn("textPolicy=requested", sent["prompt"])
                self.assertEqual(len(sent.get("reference_images") or []), reference_count)

    @unittest.skip(STALE_COD_RESTORE_REASON)
    def test_uploaded_hooks_use_product_analysis_and_text_hooks_keep_optional_oip(self):
        self.oip_enabled.return_value = True

        def enhancement(prompt, template_key, *references):
            self.assertEqual(template_key, "codHook")
            return prompt + f"\n{self.OIP_MARKER}\nSoft directional window lighting; preserve source content.", {"used": True}

        with patch.object(backend, "enhance_single_ai_image_prompt_with_open_prompts", side_effect=enhancement) as enhance:
            for reference_count in (0, 1):
                with self.subTest(reference_count=reference_count):
                    sent = self.capture_dispatch(self.payload(), reference_count=reference_count)
                    if reference_count:
                        self.assertNotIn(self.OIP_MARKER, sent["prompt"])
                        self.assertIn("[COD hook AI product identity]", sent["prompt"])
                    else:
                        self.assertGreater(sent["prompt"].rfind(self.MARKER), sent["prompt"].index(self.OIP_MARKER))
                    self.assertIn(self.BRIEF, sent["prompt"])
            self.assertEqual(enhance.call_count, 1)

    def test_actual_oip_append_keeps_source_beyond_its_director_context_budget(self):
        source = "当前产品事实保持。" * 1500 + "TAIL_SOURCE_COPY_500g_15cm"
        result_json = json.dumps({"visualEnhancement": {
            "camera": "Eye-level medium product shot.",
            "lighting": "Soft directional window lighting from the left.",
            "composition": "Retain the locked product and all approved source copy.",
        }})
        with (
            patch.object(backend, "load_ai_director_settings", return_value={"openImagePromptsEnabled": True, "visionEnabled": False}),
            patch.object(backend, "public_ai_director_settings", return_value={"enabled": True, "configured": True, "model": "fixture-director"}),
            patch.object(backend, "search_open_image_prompts", return_value={"referenceCount": 1, "references": [{
                "stableId": "fixture-oip", "sourcePrompt": "Soft natural light and true material texture.",
            }]}),
            patch.object(backend, "public_open_image_prompts_payload", return_value={"referenceCount": 1, "references": []}),
            patch.object(backend, "ai_director_reference_contact_sheet", return_value=None),
            patch.object(backend, "invoke_ai_director_chat", return_value=(result_json, 1)),
            patch.object(backend, "ai_director_last_call_info", return_value={"model": "fixture-director"}),
            patch.dict(os.environ, {"AI_IMAGE_SINGLE_PROMPT_BLUEPRINT_ENABLED": "1"}),
        ):
            result, metadata = backend.enhance_single_ai_image_prompt_with_open_prompts(source, "codHook")
        self.assertTrue(metadata["used"])
        self.assertTrue(result.startswith(source))
        self.assertIn("TAIL_SOURCE_COPY_500g_15cm", result)

    @unittest.skip(STALE_COD_RESTORE_REASON)
    def test_every_variant_keeps_source_copy_and_variant_reference_binding(self):
        payload = self.payload(count=3, productReferenceIndexes=json.dumps([1, 2]))
        sent = self.capture_dispatch(payload, reference_count=2)
        self.assertEqual(len(sent["prompts"]), 3)
        for index, prompt in enumerate(sent["prompts"]):
            with self.subTest(page=index + 1):
                self.assertIn(self.MARKER, prompt)
                self.assertIn(self.BRIEF, prompt)
                self.assertIn("textPolicy=requested", prompt)
                self.assertIn("[COD hook AI product identity]", prompt)
                routed = sent["reference_images_by_page"][index]
                self.assertEqual(len(routed), 1)
                self.assertEqual(routed[0][1], f"reference-{index % 2}".encode())

    def test_non_hook_templates_do_not_receive_or_rewrite_the_hook_contract(self):
        source = "[Product] Exact reference product.\n[Current user prompt]\n不加营销字，保留原有标签。"
        for template_key in ("main", "scene", "detail", ""):
            for reference_count in (0, 1):
                with self.subTest(template_key=template_key, reference_count=reference_count):
                    payload = self.payload(templateKey=template_key, prompt=source)
                    sent = self.capture_dispatch(payload, reference_count=reference_count)
                    if reference_count:
                        self.assertTrue(sent["prompt"].startswith(source + "\n"))
                        self.assertIn("[Reference product detail fidelity]", sent["prompt"])
                    else:
                        self.assertEqual(sent["prompt"], source)
                    self.assertNotIn(self.MARKER, sent["prompt"])


if __name__ == "__main__":
    unittest.main()
