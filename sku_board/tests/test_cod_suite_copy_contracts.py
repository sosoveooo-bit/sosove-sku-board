"""COD country/detail copy survives old plans, source mapping and review.

These regressions stop at prompt/message production. They use synthetic sources,
an isolated data directory and blocked network/model/image operations.
"""

from contextlib import ExitStack
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sku_board import backend


class CodSuiteCopyContractTests(unittest.TestCase):
    PRODUCT = "[Product] Exact blue kitchen utensil tray from product reference 1."
    BRIEF = (
        "主卖点：\n"
        "1. 排水孔：DRAIN_SOURCE，保持原孔位。\n"
        "2. 方便收纳：STORAGE_SOURCE，餐具整齐放置。\n"
        "3. 圆角边缘：EDGE_SOURCE，展示实际圆角。\n"
        "4. 清洗方便：CLEAN_SOURCE，按实际维护方式。\n"
        "目标市场：日本。\n"
    )
    SUITES = (
        (backend.AI_IMAGE_COD_SUITE_KEY, 12),
        (backend.AI_IMAGE_COD_DETAIL_SUITE_KEY, 12),
    )
    ACTOR = {"username": "cod-suite-copy-fixture", "role": "admin"}
    COPY_MARKER = "[COD suite selling-copy contract"
    NO_TEXT_MARKER = "[No-added-text execution lock — highest text priority]"

    def setUp(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        directory = stack.enter_context(tempfile.TemporaryDirectory(prefix="cod-suite-copy-"))
        data = Path(directory)
        stack.enter_context(patch.dict(os.environ, {"SKU_BOARD_DATA_DIR": directory}))
        for name, path in {
            "DATA_DIR": data,
            "DATA_FILE": data / "board.json",
            "AI_DIRECTOR_SETTINGS_FILE": data / "director.json",
            "AI_DIRECTOR_CACHE_FILE": data / "cache.json",
            "AI_IMAGE_JOBS_FILE": data / "jobs.json",
            "AI_IMAGE_ERROR_LOG": data / "errors.log",
        }.items():
            stack.enter_context(patch.object(backend, name, path))
        for target in ("requests.sessions.Session.request", "urllib.request.urlopen"):
            stack.enter_context(patch(target, side_effect=AssertionError("Unexpected external request")))
        for name in (
            "invoke_ai_director_chat", "load_ai_director_settings", "put_ai_director_cached_analysis",
            "save_ai_image_outputs", "generate_ai_image_tasks_with_transient_retry", "generate_images_via_acore",
        ):
            stack.enter_context(patch.object(backend, name, side_effect=AssertionError(f"Unexpected model/store operation: {name}")))
        stack.enter_context(patch.object(backend, "get_ai_director_cached_analysis", return_value=None))
        stack.enter_context(patch.object(backend, "public_ai_director_settings", return_value={
            "enabled": False, "configured": False, "model": "fixture-director", "reviewEnabled": False,
        }))
        stack.enter_context(patch.object(backend, "ai_director_reference_data_url", return_value="data:image/png;base64,Zml4dHVyZQ=="))

    def compile(self, key, count, *, brief=None, plan=None, product=None):
        return backend.build_ai_image_suite_prompts(
            self.PRODUCT if product is None else product,
            self.BRIEF if brief is None else brief,
            "750x1000", suite_key=key, country="JP", suite_count=count, plan=plan,
        )

    def plan(self, key, count, *, brief=None, product=None, use_director=False):
        return backend.plan_ai_image_suite({
            "suiteKey": key, "suiteCount": count, "suiteCountry": "JP", "size": "750x1000",
            "prompt": self.PRODUCT if product is None else product,
            "suiteBrief": self.BRIEF if brief is None else brief,
            "useDirector": use_director,
        }, self.ACTOR)

    @staticmethod
    def message_text(messages):
        parts = []
        for message in messages:
            content = message.get("content")
            if isinstance(content, str):
                parts.append(content)
            elif isinstance(content, list):
                parts.extend(item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text")
        return "\n".join(parts)

    def review_payload(self, key, count, pages):
        messages = backend.build_ai_image_suite_review_messages(
            key, "JP", 78, pages,
            ("reference.png", b"synthetic source", "image/png"),
            [(f"page-{page['page']}.png", b"synthetic output", "image/png") for page in pages],
            suite_count=count,
        )
        text = self.message_text(messages)
        decoded, _end = json.JSONDecoder().raw_decode(text.split("[Locked page plan]", 1)[1].lstrip())
        return decoded, text

    def assert_visible_source_pages(self, prompts, pages):
        assigned = [page for page in pages if int(page.get("sourcePointIndex") or 0) > 0]
        self.assertEqual(len(assigned), 4)
        for page in assigned:
            self.assertEqual(page["textPolicy"], "requested", f"P{page['page']} suppressed source copy")
            self.assertIn(self.COPY_MARKER, prompts[page["page"] - 1])
            self.assertNotIn(self.NO_TEXT_MARKER, prompts[page["page"] - 1])
            self.assertTrue(page.get("sourcePointVerbatim"))
        for source in ("DRAIN_SOURCE", "STORAGE_SOURCE", "EDGE_SOURCE", "CLEAN_SOURCE"):
            self.assertTrue(any(source in page["sourcePointVerbatim"] for page in assigned))
            self.assertIn(source, "\n".join(prompts))

    def test_new_country_and_detail_plans_have_visible_source_copy_without_an_opt_in(self):
        for key, count in self.SUITES:
            with self.subTest(suite=key):
                result = self.plan(key, count)
                self.assertTrue(result["director"]["sellingPointCoverage"]["complete"])
                prompts, pages = self.compile(key, count, plan=result["suitePages"])
                self.assert_visible_source_pages(prompts, pages)
                if key == backend.AI_IMAGE_COD_SUITE_KEY:
                    self.assertTrue(pages[0].get("codMainRich"))
                    self.assertEqual(len(pages[0]["codMainSupportingPoints"]), 3)
                else:
                    self.assertFalse(any(page.get("codMainRich") for page in pages))
                    self.assertNotIn("[COD MAIN SUPPORT CONTRACT]", "\n".join(prompts))

    def test_unmarked_cached_none_pages_are_rebound_to_current_cod_copy_defaults(self):
        for key, count in self.SUITES:
            with self.subTest(suite=key):
                original = backend.build_ai_image_suite_plan(self.PRODUCT, self.BRIEF, "750x1000", suite_key=key, country="JP", count=count)
                for page in original:
                    page["textPolicy"] = "none"
                    page.pop("codCopyPolicyVersion", None)
                    page.pop("codCopyPolicy", None)
                before = deepcopy(original)
                normalized = backend.normalize_ai_image_suite_plan(json.dumps(original, ensure_ascii=False), count)
                prompts, pages = self.compile(key, count, plan=normalized)
                self.assert_visible_source_pages(prompts, pages)
                self.assertEqual(original, before, "Copy rebinding mutated the submitted plan")

    def test_current_no_text_request_overrides_an_older_requested_plan_in_both_suites(self):
        for key, count in self.SUITES:
            _prompts, old_pages = self.compile(key, count)
            for exclusion in ("全部无字。", "不要任何文字。", "Text-free product images.", "Don't add any text."):
                with self.subTest(suite=key, exclusion=exclusion):
                    prompts, pages = self.compile(key, count, brief=self.BRIEF + exclusion, plan=old_pages)
                    self.assertTrue(all(page["textPolicy"] == "none" for page in pages))
                    self.assertTrue(all(self.NO_TEXT_MARKER in prompt for prompt in prompts))
                    self.assertFalse(any(page.get("codMainRich") for page in pages))
                    self.assertFalse(any(item.get("id") == "SOURCE_HEADLINE" for page in pages for item in page.get("companyModulePlan") or []))

    def test_changing_a_marked_no_text_plan_back_to_ordinary_selling_graphics_restores_copy(self):
        for key, count in self.SUITES:
            with self.subTest(suite=key):
                _prompts, no_text_pages = self.compile(key, count, brief=self.BRIEF + "全部无字。")
                self.assertTrue(all(page["textPolicy"] == "none" for page in no_text_pages))
                normalized = backend.normalize_ai_image_suite_plan(json.dumps(no_text_pages, ensure_ascii=False), count)
                prompts, pages = self.compile(key, count, plan=normalized)
                self.assert_visible_source_pages(prompts, pages)

    def test_title_only_preserves_the_headline_without_creating_a_support_label_row(self):
        for key, count in self.SUITES:
            _prompts, old_pages = self.compile(key, count)
            for restriction in ("只要标题：使いやすい毎日；不要标签。", "Only a headline: Easy daily use. No labels."):
                with self.subTest(suite=key, restriction=restriction):
                    prompts, pages = self.compile(key, count, brief=self.BRIEF + restriction, plan=old_pages)
                    self.assertTrue(all(page["textPolicy"] == "requested" for page in pages))
                    self.assertTrue(all("Title-only" in prompt for prompt in prompts))
                    self.assertFalse(any(page.get("codMainRich") or page.get("codMainSupportingPoints") or page.get("copyLabels") for page in pages))
                    self.assertNotIn("SUPPORTING_BENEFITS", json.dumps([page.get("companyModulePlan") for page in pages]))
                    self.assertTrue(all(self.NO_TEXT_MARKER not in prompt for prompt in prompts))

    def test_final_copy_policy_survives_json_and_reviewer_has_no_brief(self):
        for key, count in self.SUITES:
            for restriction, expected in (("", "requested"), ("全部无字。", "none"), ("只要标题；不要标签。", "requested")):
                with self.subTest(suite=key, restriction=restriction):
                    _prompts, pages = self.compile(key, count, brief=self.BRIEF + restriction)
                    normalized = backend.normalize_ai_image_suite_plan(json.dumps(pages, ensure_ascii=False), count)
                    source_page = next(page for page in normalized if int(page.get("sourcePointIndex") or 0) == 1)
                    reviewed, _text = self.review_payload(key, count, [source_page])
                    self.assertEqual(reviewed[0]["textPolicy"], expected)
                    expected_mode = "titleOnly" if "只要标题" in restriction else expected
                    self.assertEqual(reviewed[0]["codCopyPolicy"], expected_mode)
                    self.assertIn(self.COPY_MARKER, reviewed[0]["copyInstruction"])
                    if expected_mode == "titleOnly":
                        self.assertIn("Title-only", reviewed[0]["copyInstruction"])
                    self.assertIn("DRAIN_SOURCE", reviewed[0]["sourcePointVerbatim"])

    def test_analysis_and_second_pass_directors_receive_the_same_resolved_copy_contract(self):
        for key, count in self.SUITES:
            for restriction, expected_mode in (("", "requested"), ("全部无字。", "none"), ("只要标题；不要标签。", "titleOnly")):
                with self.subTest(suite=key, restriction=restriction):
                    brief = self.BRIEF + restriction
                    _prompts, pages = self.compile(key, count, brief=brief)
                    source_page = next(page for page in pages if int(page.get("sourcePointIndex") or 0) == 1)
                    first_pass = backend.build_ai_director_messages(pages, self.PRODUCT, brief, key, "JP", None, False)
                    second_pass = backend.build_ai_director_page_refinement_messages([source_page], {}, key, "JP")
                    for messages, marker in ((first_pass, "[Locked page roles]"), (second_pass, "[Locked pages]")):
                        message_text = self.message_text(messages)
                        payload, _end = json.JSONDecoder().raw_decode(message_text.split(marker, 1)[1].lstrip())
                        selected = next(page for page in payload if page["page"] == source_page["page"])
                        self.assertEqual(selected["codCopyPolicy"], expected_mode)
                        self.assertEqual(selected["textPolicy"], "none" if expected_mode == "none" else "requested")
                        self.assertIn(self.COPY_MARKER, selected["copyInstruction"])

    def test_remote_and_cached_director_pages_cannot_reintroduce_unmarked_none(self):
        for key, count in self.SUITES:
            for source in ("model", "cache"):
                with self.subTest(suite=key, source=source):
                    def stale_result(base_pages, *args, **kwargs):
                        changed = deepcopy(base_pages)
                        for page in changed:
                            page["textPolicy"] = "none"
                            page.pop("codCopyPolicy", None)
                            page.pop("codCopyPolicyVersion", None)
                        return changed, {"source": source, "status": "ready", "visionUsed": False, "cacheHit": source == "cache"}

                    with (
                        patch.object(backend, "shared_ai_director_enabled", return_value=True),
                        patch.object(backend, "refine_ai_image_suite_plan_with_director", side_effect=stale_result) as refine,
                    ):
                        result = self.plan(key, count, use_director=True)
                    refine.assert_called_once()
                    assigned = [page for page in result["suitePages"] if int(page.get("sourcePointIndex") or 0) > 0]
                    self.assertTrue(all(page["textPolicy"] == "requested" for page in assigned))
                    prompts, pages = self.compile(key, count, plan=result["suitePages"])
                    self.assert_visible_source_pages(prompts, pages)

    def test_legacy_generated_text_free_instructions_are_removed_without_losing_the_photography(self):
        for key, count in self.SUITES:
            with self.subTest(suite=key):
                _prompts, old_pages = self.compile(key, count)
                source_page = next(page for page in old_pages if int(page.get("sourcePointIndex") or 0) == 1)
                source_page["textPolicy"] = "none"
                source_page.pop("codCopyPolicy", None)
                source_page.pop("codCopyPolicyVersion", None)
                source_page["modelPrompt"] = "SOFT_SIDE_LIGHT_SOURCE. No added text. Keep the frame text-free. Preserve the exact product."
                source_page["visualEnhancement"] = {
                    **source_page.get("visualEnhancement", {}),
                    "shotConcept": "VISIBLE_PRODUCT_SOURCE. Create a text-free image.",
                    "riskControls": ["Add no headline, label or callout.", "Retain the original product shape."],
                }
                original_source = source_page["sourcePointVerbatim"]
                prompts, pages = self.compile(key, count, plan=old_pages)
                final_page = pages[source_page["page"] - 1]
                final_prompt = prompts[source_page["page"] - 1]
                self.assertEqual(final_page["textPolicy"], "requested")
                self.assertEqual(final_page["sourcePointVerbatim"], original_source)
                self.assertIn("SOFT_SIDE_LIGHT_SOURCE", final_page["modelPrompt"])
                self.assertIn("VISIBLE_PRODUCT_SOURCE", final_prompt)
                for old_instruction in ("No added text.", "Keep the frame text-free.", "Create a text-free image.", "Add no headline, label or callout."):
                    self.assertNotIn(old_instruction, final_prompt)
                self.assertIn(self.COPY_MARKER, final_prompt)

    def test_supplied_reviews_and_discount_keep_structural_copy_without_inventing_more(self):
        brief = self.BRIEF + '\n优惠15%OFF\n用户评价：\n1. 「日常の収納に使っています。」\n'
        prompts, pages = self.compile(backend.AI_IMAGE_COD_DETAIL_SUITE_KEY, 22, brief=brief)
        for archetype in ("本地促销页", "好评反馈页"):
            page = next(page for page in pages if page.get("pageArchetype") == archetype)
            self.assertEqual(page["textPolicy"], "essential")
            self.assertNotIn(self.NO_TEXT_MARKER, prompts[page["page"] - 1])
        feedback = next(page for page in pages if page.get("pageArchetype") == "好评反馈页")
        self.assertEqual(feedback["reviewQuotes"], ["日常の収納に使っています。"])
        self.assertIn("日常の収納に使っています。", prompts[feedback["page"] - 1])
        self.assertNotIn("four short feedback items", "\n".join(prompts))

    def test_both_suites_keep_selected_product_source_blocks_next_to_the_current_brief(self):
        sources = ["SKU排水孔：SKU_DRAIN_SOURCE，孔位保持不变。", "SKU圆角边缘：SKU_EDGE_SOURCE，保留原圆角。"]
        product = self.PRODUCT + "\n[COD suite selling-point sources]\n" + json.dumps(sources, ensure_ascii=False) + "\n[Material and light] Soft diffuse daylight."
        brief = "主卖点：\n1. 方便收纳：CURRENT_STORAGE_SOURCE。\n目标市场：日本。\n背景：浅色厨房。"
        for key, count in self.SUITES:
            with self.subTest(suite=key):
                result = self.plan(key, count, brief=brief, product=product)
                self.assertTrue(result["director"]["sellingPointCoverage"]["complete"])
                prompts, pages = self.compile(key, count, brief=brief, product=product, plan=result["suitePages"])
                assigned = [page for page in pages if int(page.get("sourcePointIndex") or 0) > 0]
                for source in ("SKU_DRAIN_SOURCE", "SKU_EDGE_SOURCE", "CURRENT_STORAGE_SOURCE"):
                    self.assertTrue(any(source in page.get("sourcePointVerbatim", "") for page in assigned), source)
                    self.assertIn(source, "\n".join(prompts))
                self.assertEqual(len(assigned), 3)

    def test_selected_product_plain_source_blocks_do_not_require_visible_copy_opt_in(self):
        sources = ["排水结构 SKU_SOURCE_A", "圆角结构 SKU_SOURCE_B", "分隔收纳 SKU_SOURCE_C"]
        product = self.PRODUCT + "\n[COD suite selling-point sources]\n" + json.dumps(sources, ensure_ascii=False)
        for key, count in self.SUITES:
            with self.subTest(suite=key):
                prompts, pages = self.compile(key, count, brief="目标市场：日本。背景：浅色厨房。", product=product)
                assigned = [page for page in pages if int(page.get("sourcePointIndex") or 0) > 0]
                self.assertEqual(len(assigned), 3)
                self.assertTrue(all(page["textPolicy"] == "requested" for page in assigned))
                for source in sources:
                    self.assertIn(source, "\n".join(prompts))

    def test_non_cod_page_policy_semantics_and_clean_catalog_remain_unchanged(self):
        for key in (backend.AI_IMAGE_LANDING_SUITE_KEY, backend.AI_IMAGE_AMAZON_APLUS_SUITE_KEY, backend.AI_IMAGE_RAKUTEN_SUITE_KEY):
            with self.subTest(suite=key):
                self.assertEqual(backend.ai_image_page_text_policy("添加文字", {"textPolicy": "none", "section": "main"}, key), "none")
                self.assertEqual(backend.ai_image_page_text_policy("全部无字", {"textPolicy": "requested", "section": "main"}, key), "requested")
        self.assertEqual(backend.ai_image_page_text_policy("", {"cleanCatalogMode": True}, backend.AI_IMAGE_RAKUTEN_SUITE_KEY), "none")
        self.assertEqual(backend.ai_image_cod_hook_text_policy({"textPolicy": "none"}, self.BRIEF), "none")

    def test_product_facts_about_unprinted_surfaces_do_not_suppress_the_whole_ad_copy(self):
        facts = (
            "瓶身无字，方便自行贴标签。",
            "无字印花，保留真实面料纹理。",
            "包装无文字，保持原外观。",
            "Supplied product has text-free packaging.",
        )
        for key, count in self.SUITES:
            for fact in facts:
                with self.subTest(suite=key, fact=fact):
                    brief = self.BRIEF.replace("保持原孔位。", "保持原孔位；" + fact)
                    prompts, pages = self.compile(key, count, brief=brief)
                    self.assert_visible_source_pages(prompts, pages)
                    source_page = next(page for page in pages if int(page.get("sourcePointIndex") or 0) == 1)
                    self.assertIn(fact, source_page["sourcePointVerbatim"])
                    if key == backend.AI_IMAGE_COD_SUITE_KEY:
                        self.assertTrue(source_page.get("codMainRich"))
                        self.assertTrue(source_page.get("codMainSupportingPoints"))
                        self.assertIn("[COD MAIN SUPPORT CONTRACT]", prompts[source_page["page"] - 1])
                    _no_text_prompts, no_text_pages = self.compile(key, count, brief=brief + "本次所有图片无字。", plan=pages)
                    self.assertTrue(all(page["textPolicy"] == "none" for page in no_text_pages))

    def test_empty_current_brief_recompiles_stamped_none_as_default_but_review_keeps_the_stamp(self):
        sources = ["排水孔 DRAIN_SOURCE", "方便收纳 STORAGE_SOURCE", "圆角边缘 EDGE_SOURCE", "清洗方便 CLEAN_SOURCE"]
        product = self.PRODUCT + "\n[COD suite selling-point sources]\n" + json.dumps(sources, ensure_ascii=False)
        for key, count in self.SUITES:
            with self.subTest(suite=key):
                _prompts, old_pages = self.compile(key, count, product=product, brief="全部图片无字。")
                self.assertTrue(all(page["textPolicy"] == "none" for page in old_pages))
                normalized = backend.normalize_ai_image_suite_plan(json.dumps(old_pages, ensure_ascii=False), count)
                reviewed, _text = self.review_payload(key, count, [normalized[0]])
                self.assertEqual(reviewed[0]["textPolicy"], "none")
                self.assertEqual(reviewed[0]["codCopyPolicy"], "none")
                prompts, pages = self.compile(key, count, product=product, brief="", plan=normalized)
                self.assert_visible_source_pages(prompts, pages)
                if key == backend.AI_IMAGE_COD_SUITE_KEY:
                    self.assertTrue(pages[0].get("codMainRich"))
                    self.assertEqual(len(pages[0]["codMainSupportingPoints"]), 3)


if __name__ == "__main__":
    unittest.main()
