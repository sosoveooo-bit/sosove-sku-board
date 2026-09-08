"""Compile source-backed COD commerce pages without model/network or panel data."""

from contextlib import ExitStack
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from sku_board import backend


class CodCommerceIntegrationTests(unittest.TestCase):
    PRODUCT = "[Product] Exact blue kitchen utensil tray with drainage holes."
    CORE_BRIEF = (
        "主卖点：\n"
        "1. 排水孔：ORIGINAL_DRAINAGE_PROOF，孔位保持原样。\n"
        "2. 方便收纳：ORIGINAL_STORAGE_PROOF，餐具整齐放置。\n"
    )
    QUOTES = ["放在厨房很顺手。", "擦洗很方便。"]

    def setUp(self) -> None:
        stack = ExitStack()
        self.addCleanup(stack.close)
        data_dir = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix="cod-commerce-integration-")))
        stack.enter_context(patch.dict(os.environ, {"SKU_BOARD_DATA_DIR": str(data_dir)}))
        for name, path in {
            "DATA_DIR": data_dir,
            "AI_DIRECTOR_SETTINGS_FILE": data_dir / "settings.json",
            "AI_DIRECTOR_CACHE_FILE": data_dir / "director-cache.json",
            "AI_IMAGE_JOBS_FILE": data_dir / "jobs.json",
            "AI_IMAGE_ERROR_LOG": data_dir / "errors.log",
        }.items():
            stack.enter_context(patch.object(backend, name, path))
        for target in ("requests.sessions.Session.request", "urllib.request.urlopen"):
            stack.enter_context(patch(target, side_effect=AssertionError("Unexpected network call")))
        for name in ("invoke_ai_director_chat", "get_ai_director_cached_analysis", "put_ai_director_cached_analysis"):
            stack.enter_context(patch.object(backend, name, side_effect=AssertionError(f"Unexpected external/store operation: {name}")))

    def compile(self, brief: str, plan=None):
        return backend.build_ai_image_suite_prompts(
            self.PRODUCT, brief, "750x1000",
            suite_key=backend.AI_IMAGE_COD_DETAIL_SUITE_KEY,
            country="JP", suite_count=22, plan=plan,
        )

    @classmethod
    def review_section(cls, quotes=None) -> str:
        values = cls.QUOTES if quotes is None else quotes
        return "用户评价：\n" + "\n".join(f'{number}. 「{quote}」' for number, quote in enumerate(values, 1))

    def assert_original_product_points(self, prompts, pages) -> None:
        self.assertEqual(len(prompts), 22)
        self.assertEqual(len(pages), 22)
        combined = "\n".join(prompts)
        for marker in ("ORIGINAL_DRAINAGE_PROOF", "ORIGINAL_STORAGE_PROOF"):
            self.assertIn(marker, combined)
            self.assertTrue(any(marker in str(page.get("sourcePointVerbatim", "")) for page in pages), marker)

    @staticmethod
    def page_of_archetype(pages, archetype):
        matches = [page for page in pages if page.get("pageArchetype") == archetype]
        if len(matches) != 1:
            raise AssertionError(f"Expected exactly one {archetype}; found {len(matches)}")
        return matches[0]

    def assert_no_default_seventy_percent(self, text: str) -> None:
        self.assertIsNone(re.search(r"70\s*[%％]\s*OFF", text, re.IGNORECASE), "An unsupplied 70% offer reached the final prompt")

    def test_missing_commerce_sources_compile_product_and_use_pages_without_default_claims(self) -> None:
        prompts, pages = self.compile(self.CORE_BRIEF)
        self.assert_original_product_points(prompts, pages)
        self.assertEqual(pages[0]["pageArchetype"], "产品首屏")
        self.page_of_archetype(pages, "使用场景页")
        self.assertFalse(any(page.get("pageArchetype") in {"本地促销页", "好评反馈页"} for page in pages))
        self.assertFalse(any(page.get("promotionContract") or page.get("reviewQuotes") for page in pages))
        combined = "\n".join(prompts)
        self.assert_no_default_seventy_percent(combined)
        self.assertNotIn("お客様の声", combined)
        self.assertNotIn("[Positive feedback page — required]", combined)
        self.assertNotIn("[Source-backed feedback page]", combined)
        self.assertNotIn("[Source-backed promotion — required]", combined)

    def test_supplied_arbitrary_discounts_reach_final_prompt_without_added_urgency_or_maximum(self) -> None:
        for source, percent_text in (("促销：15%OFF", "15"), ("Sale discount 33.5%", "33.5"), ("活动打8折", "20")):
            with self.subTest(source=source):
                prompts, pages = self.compile(self.CORE_BRIEF + "\n" + source)
                self.assert_original_product_points(prompts, pages)
                promotion = self.page_of_archetype(pages, "本地促销页")
                self.assertEqual(promotion["promotionContract"]["percentText"], percent_text)
                self.assertEqual(promotion["headline"], f"{percent_text}%OFF")
                final_prompt = prompts[int(promotion["page"]) - 1]
                self.assertIn(f"{percent_text}% OFF", final_prompt)
                self.assertNotIn("今だけ", final_prompt)
                self.assertIsNone(re.search(r"最大\s*[0-9]+(?:\.[0-9]+)?\s*[%％]", final_prompt))
                self.assert_no_default_seventy_percent(final_prompt)

    def test_price_exclusion_does_not_remove_a_supplied_discount(self) -> None:
        prompts, pages = self.compile(self.CORE_BRIEF + "\n不要价格，优惠15%")
        promotion = self.page_of_archetype(pages, "本地促销页")
        self.assertEqual(promotion["promotionContract"]["percentText"], "15")
        self.assertIn("15% OFF", prompts[promotion["page"] - 1])

    def test_supplied_maximum_qualifier_survives_japanese_headline_and_final_offer(self) -> None:
        for source, percent_text in (("最大20%OFF", "20"), ("Up to 25% OFF", "25"), ("最多优惠33.5%", "33.5")):
            with self.subTest(source=source):
                prompts, pages = self.compile(self.CORE_BRIEF + "\n" + source)
                promotion = self.page_of_archetype(pages, "本地促销页")
                contract = promotion["promotionContract"]
                self.assertTrue(contract["isMaximum"])
                self.assertEqual(contract["percentText"], percent_text)
                self.assertEqual(promotion["headline"], f"最大{percent_text}%OFF")
                final_prompt = prompts[promotion["page"] - 1]
                self.assertRegex(final_prompt, rf"(?i)up\s+to\s+{re.escape(percent_text)}%\s*OFF")
                self.assertIn(contract["sourceText"], final_prompt)
                self.assertNotIn("今だけ", final_prompt)
                self.assert_original_product_points(prompts, pages)

    def test_membership_quantity_and_explicit_end_date_terms_are_not_lost(self) -> None:
        for source in ("会员专享15%OFF", "满2件优惠25%", "指定商品33.5%OFF，活动至2026年9月30日"):
            with self.subTest(source=source):
                prompts, pages = self.compile(self.CORE_BRIEF + "\n" + source)
                promotion = self.page_of_archetype(pages, "本地促销页")
                contract = promotion["promotionContract"]
                self.assertFalse(contract["isMaximum"])
                self.assertEqual(contract["sourceText"], source)
                self.assertIn(source, prompts[promotion["page"] - 1])

    def test_explicit_no_promotion_overrides_a_numeric_source(self) -> None:
        for restriction in ("不要促销", "不显示折扣", "No discount", "Don't include promotions"):
            with self.subTest(restriction=restriction):
                prompts, pages = self.compile(self.CORE_BRIEF + f"\nSale discount 15%.\n{restriction}")
                self.assertEqual(pages[0]["pageArchetype"], "产品首屏")
                self.assertFalse(any(page.get("promotionContract") for page in pages))
                self.assertNotIn("[Source-backed promotion — required]", "\n".join(prompts))
                self.assert_original_product_points(prompts, pages)

    def test_two_actual_quotes_remain_two_in_page_modules_and_final_prompt(self) -> None:
        prompts, pages = self.compile(self.CORE_BRIEF + "\n" + self.review_section())
        self.assert_original_product_points(prompts, pages)
        feedback = self.page_of_archetype(pages, "好评反馈页")
        self.assertEqual(feedback["reviewQuotes"], self.QUOTES)
        final_prompt = prompts[feedback["page"] - 1]
        for quote in self.QUOTES:
            self.assertIn(quote, final_prompt)
        self.assertIn("Use exactly 2 excerpts", final_prompt)
        self.assertIsNone(re.search(r"exactly\s+(?:four|4)\b", final_prompt, re.IGNORECASE))
        self.assertFalse("four short feedback items" in final_prompt, "The text-policy tail still requires four feedback items")
        self.assertNotIn("四条短评论", final_prompt)
        self.assertNotIn("四张等比例体验卡", final_prompt)
        modules = json.dumps(feedback.get("companyModulePlan") or [], ensure_ascii=False)
        self.assertNotIn("Exactly four", modules)
        self.assertIn("supplied 2 review excerpts", modules)

    def test_requests_and_placeholders_do_not_enable_customer_voices(self) -> None:
        for source in ("添加好评页，写4条好评", '真实评价："暂无"', "用户评价：请根据卖点生成四条反馈"):
            with self.subTest(source=source):
                prompts, pages = self.compile(self.CORE_BRIEF + "\n" + source)
                self.assertFalse(any(page.get("reviewQuotes") for page in pages))
                self.assertFalse(any(page.get("pageArchetype") == "好评反馈页" for page in pages))
                self.assertNotIn("[Source-backed feedback page]", "\n".join(prompts))
                self.assertNotIn("お客様の声", "\n".join(prompts))

    def test_promotion_and_review_metadata_survive_json_normalization_and_recompilation(self) -> None:
        brief = self.CORE_BRIEF + "\n优惠33.5%\n" + self.review_section()
        prompts, pages = self.compile(brief)
        original = deepcopy(pages)
        normalized = backend.normalize_ai_image_suite_plan(json.dumps(pages, ensure_ascii=False), 22)
        self.assertEqual(len(normalized), 22)
        before_offer = self.page_of_archetype(pages, "本地促销页")
        before_reviews = self.page_of_archetype(pages, "好评反馈页")
        self.assertEqual(self.page_of_archetype(normalized, "本地促销页")["promotionContract"], before_offer["promotionContract"])
        self.assertEqual(self.page_of_archetype(normalized, "好评反馈页")["reviewQuotes"], before_reviews["reviewQuotes"])
        replay_prompts, replay_pages = self.compile(brief, plan=normalized)
        self.assertEqual(pages, original, "Serialization/compilation mutated its input")
        self.assertEqual(self.page_of_archetype(replay_pages, "本地促销页")["promotionContract"], before_offer["promotionContract"])
        self.assertEqual(self.page_of_archetype(replay_pages, "好评反馈页")["reviewQuotes"], self.QUOTES)
        self.assert_original_product_points(replay_prompts, replay_pages)
        self.assertIn("33.5% OFF", replay_prompts[before_offer["page"] - 1])
        self.assertIn("Use exactly 2 excerpts", replay_prompts[before_reviews["page"] - 1])

    def test_stale_commerce_pages_do_not_render_after_their_source_is_removed(self) -> None:
        for source in ("优惠15%", self.review_section()):
            with self.subTest(source=source):
                _prompts, pages = self.compile(self.CORE_BRIEF + "\n" + source)
                with self.assertRaises(ValueError):
                    self.compile(self.CORE_BRIEF, plan=pages)

    def test_changed_offer_percentage_or_conditions_require_replanning_instead_of_mixing_old_copy(self) -> None:
        for old_source, current_source in (
            ("优惠15%", "优惠33.5%"),
            ("会员专享15%OFF", "全场15%OFF"),
            ("最大20%OFF", "20%OFF"),
        ):
            with self.subTest(old_source=old_source, current_source=current_source):
                _prompts, old_pages = self.compile(self.CORE_BRIEF + "\n" + old_source)
                stored_plan = backend.normalize_ai_image_suite_plan(json.dumps(old_pages, ensure_ascii=False), 22)
                self.assertEqual(len(stored_plan), 22)
                with self.assertRaises(ValueError):
                    self.compile(self.CORE_BRIEF + "\n" + current_source, plan=stored_plan)

    def test_changed_review_quotes_require_replanning_even_when_the_count_is_the_same(self) -> None:
        _prompts, old_pages = self.compile(self.CORE_BRIEF + "\n" + self.review_section())
        stored_plan = backend.normalize_ai_image_suite_plan(json.dumps(old_pages, ensure_ascii=False), 22)
        replacement_quotes = ["放在抽屉里很整齐。", "取用餐具更方便。"]
        self.assertEqual(len(replacement_quotes), len(self.QUOTES))
        with self.assertRaises(ValueError):
            self.compile(self.CORE_BRIEF + "\n" + self.review_section(replacement_quotes), plan=stored_plan)


if __name__ == "__main__":
    unittest.main()
