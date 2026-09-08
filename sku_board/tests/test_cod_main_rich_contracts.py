"""Country-COD main-image support contracts across normalization and rendering.

All product points and images are synthetic; runtime calls and real panel data
are excluded. COD details and JP25 deliberately keep their prior content budget.
"""

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


class CodMainRichContractTests(unittest.TestCase):
    PRODUCT = "[Product] Exact blue kitchen utensil tray from the supplied product reference."
    SOURCES = (
        ("水切りしやすい設計", "DRAINAGE_SOURCE: retain the supplied drainage-hole layout"),
        ("丸みのある縁", "EDGE_SOURCE: retain the rounded edge shown by the product"),
        ("仕切りで整理", "DIVIDER_SOURCE: separate utensils with the supplied dividers"),
        ("すっきり省スペース", "STORAGE_SOURCE: fit the described kitchen storage space"),
        ("軽く持ち運べる", "CARRY_SOURCE: hold and move the supplied compact tray"),
        ("さっと洗える", "CLEAN_SOURCE: clean the supplied product with its stated care method"),
    )

    def setUp(self) -> None:
        stack = ExitStack()
        self.addCleanup(stack.close)
        data = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix="cod-main-rich-")))
        stack.enter_context(patch.dict(os.environ, {"SKU_BOARD_DATA_DIR": str(data)}))
        for name, path in {
            "DATA_DIR": data,
            "DATA_FILE": data / "board.json",
            "AI_DIRECTOR_SETTINGS_FILE": data / "director.json",
            "AI_DIRECTOR_CACHE_FILE": data / "cache.json",
            "AI_IMAGE_ERROR_LOG": data / "errors.log",
        }.items():
            stack.enter_context(patch.object(backend, name, path))
        for target in ("requests.sessions.Session.request", "urllib.request.urlopen"):
            stack.enter_context(patch(target, side_effect=AssertionError("Unexpected external request")))
        for name in ("invoke_ai_director_chat", "get_ai_director_cached_analysis", "put_ai_director_cached_analysis", "save_ai_image_outputs"):
            stack.enter_context(patch.object(backend, name, side_effect=AssertionError(f"Unexpected model/store operation: {name}")))
        stack.enter_context(patch.object(backend, "ai_director_reference_data_url", return_value="data:image/png;base64,Zml4dHVyZQ=="))

    @classmethod
    def brief(cls, count: int = 6, extra: str = "") -> str:
        return "\n".join([
            "主卖点：",
            *(f"{index}. {title}：{description}。" for index, (title, description) in enumerate(cls.SOURCES[:count], 1)),
            extra,
        ])

    def compile(self, *, brief: str | None = None, count: int = 37, suite_key: str | None = None, plan=None):
        return backend.build_ai_image_suite_prompts(
            self.PRODUCT, self.brief() if brief is None else brief, "750x1000",
            suite_key=suite_key or backend.AI_IMAGE_COD_SUITE_KEY,
            country="JP", suite_count=count, plan=plan,
        )

    def base_plan(self, brief: str | None = None) -> list[dict]:
        source = self.brief() if brief is None else brief
        pages = backend.build_ai_image_suite_plan(
            self.PRODUCT, source, "750x1000",
            suite_key=backend.AI_IMAGE_COD_SUITE_KEY, country="JP", count=37,
        )
        return backend.lock_ai_image_cod_source_point_coverage(pages, self.PRODUCT, source, backend.AI_IMAGE_COD_SUITE_KEY)

    @staticmethod
    def supports(page: dict) -> list[dict]:
        value = page.get("codMainSupportingPoints")
        if not isinstance(value, list):
            raise AssertionError(f"P{page.get('page')} omitted the approved support list")
        return value

    @staticmethod
    def message_text(messages: list[dict]) -> str:
        result = []
        for message in messages:
            content = message.get("content")
            if isinstance(content, str):
                result.append(content)
            elif isinstance(content, list):
                result.extend(item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text")
        return "\n".join(result)

    def review_messages(self, pages: list[dict], suite_key: str, suite_count: int) -> list[dict]:
        reference = ("source.png", b"synthetic source", "image/png")
        images = [(f"page-{page['page']}.png", b"synthetic output", "image/png") for page in pages]
        return backend.build_ai_image_suite_review_messages(
            suite_key, "JP", 78, pages, reference, images, suite_count=suite_count,
        )

    def test_five_supports_and_labels_survive_normalization_without_using_the_headline_as_a_slot(self) -> None:
        pages = self.base_plan()
        main = pages[0]
        approved = [
            {"sourceId": f"user:{number}", "title": title, "description": description, "label": title, "sourceType": "user"}
            for number, (title, description) in enumerate(self.SOURCES[1:], 2)
        ]
        main.update({"codMainRich": True, "codMainSupportingPoints": approved, "copyLabels": [point["label"] for point in approved]})
        original = deepcopy(pages)
        normalized = backend.normalize_ai_image_suite_plan(json.dumps(pages, ensure_ascii=False), 37)
        self.assertEqual(len(normalized), 37)
        self.assertTrue(normalized[0].get("codMainRich"))
        self.assertEqual(self.supports(normalized[0]), approved)
        self.assertEqual(normalized[0]["copyLabels"], [point["label"] for point in approved])
        self.assertNotIn(main["headline"], normalized[0]["copyLabels"])
        self.assertNotIn(main["focusTitle"], [point["title"] for point in self.supports(normalized[0])])
        _prompts, compiled = self.compile(plan=normalized)
        self.assertEqual(len(self.supports(compiled[0])), 5)
        self.assertEqual(len(compiled[0]["copyLabels"]), 5)
        self.assertNotIn(compiled[0]["headline"], compiled[0]["copyLabels"])
        self.assertEqual(pages, original)

    def test_public_pipeline_enriches_country_p15_but_keeps_p16_as_detail(self) -> None:
        prompts, pages = self.compile()
        self.assertEqual(len(pages), 37)
        for number in (1, 9, 15):
            with self.subTest(main_page=number):
                self.assertTrue(pages[number - 1].get("codMainRich"))
                self.assertTrue(3 <= len(self.supports(pages[number - 1])) <= 5)
                self.assertIn("[COD MAIN SUPPORT CONTRACT]", prompts[number - 1])
        self.assertFalse(pages[15].get("codMainRich", False))
        self.assertFalse(pages[15].get("codMainSupportingPoints"))
        self.assertNotIn("[COD MAIN SUPPORT CONTRACT]", prompts[15])
        self.assertNotIn("SUPPORTING_BENEFITS", json.dumps(pages[15].get("companyModulePlan") or []))

    def test_final_main_prompt_and_modules_share_the_approved_support_budget(self) -> None:
        prompts, pages = self.compile()
        main, prompt = pages[0], prompts[0]
        approved = self.supports(main)
        self.assertEqual(len(approved), 5)
        self.assertIn("[COD MAIN SUPPORT CONTRACT]", prompt)
        self.assertEqual(prompt.count("[COD MAIN SUPPORTING SOURCE DATA]"), 1)
        self.assertRegex(prompt, r"3\s*[-–]\s*5")
        for point in approved:
            self.assertIn(point["title"], prompt)
            self.assertIn(point["sourceId"], prompt)
        modules = main.get("companyModulePlan") or []
        self.assertIn("SUPPORTING_BENEFITS", [item.get("id") for item in modules])
        module_text = json.dumps(modules, ensure_ascii=False)
        self.assertRegex(module_text, r"(?i)(?:1\s*[-–]\s*2|one\s+or\s+two).{0,65}(?:proof|evidence)")
        for old_rule in (
            "do not introduce a different page's selling point",
            "add no neighboring benefit",
            "Do not import another page benefit",
            "one primary selling point per page and at most one directly supporting detail",
            "exactly one source-provided selling point visibly executed",
        ):
            with self.subTest(obsolete_rule=old_rule):
                self.assertFalse(old_rule.lower() in prompt.lower(), f"Rich main prompt retained a conflicting rule: {old_rule}")

    def test_repeated_source_lock_and_json_roundtrip_preserve_support_provenance(self) -> None:
        brief = self.brief()
        pages = backend.apply_ai_image_cod_main_density(
            self.base_plan(brief), self.PRODUCT, brief, backend.AI_IMAGE_COD_SUITE_KEY,
        )
        baseline = deepcopy(pages)
        once = backend.lock_ai_image_cod_source_point_coverage(pages, self.PRODUCT, brief, backend.AI_IMAGE_COD_SUITE_KEY)
        twice = backend.lock_ai_image_cod_source_point_coverage(once, self.PRODUCT, brief, backend.AI_IMAGE_COD_SUITE_KEY)
        normalized = backend.normalize_ai_image_suite_plan(json.loads(json.dumps(twice)), 37)
        for stage, values in (("first lock", once), ("second lock", twice), ("JSON", normalized)):
            with self.subTest(stage=stage):
                self.assertEqual(len(values), 37)
                for number in (1, 9, 15):
                    self.assertEqual(self.supports(values[number - 1]), self.supports(baseline[number - 1]))
                    self.assertEqual(values[number - 1].get("copyLabels"), baseline[number - 1].get("copyLabels"))
                    for point in self.supports(values[number - 1]):
                        self.assertTrue(point["sourceId"])
                        self.assertIn(point["sourceType"], {"user", "image_observation"})
        self.assertEqual(pages, baseline, "Source locking mutated the supplied plan")

    def test_reviewer_receives_all_approved_supports_and_labels_with_the_same_permission(self) -> None:
        _prompts, pages = self.compile()
        text = self.message_text(self.review_messages([pages[0]], backend.AI_IMAGE_COD_SUITE_KEY, 37))
        payload, _end = json.JSONDecoder().raw_decode(text.split("[Locked page plan]", 1)[1].lstrip())
        self.assertTrue(payload[0].get("codMainRich"))
        self.assertEqual(payload[0].get("codMainSupportingPoints"), self.supports(pages[0]))
        self.assertEqual(payload[0].get("copyLabels"), pages[0]["copyLabels"])
        self.assertEqual(len(payload[0]["copyLabels"]), 5)
        self.assertIn("[COD MAIN SUPPORT CONTRACT]", text)
        self.assertRegex(text, r"(?i)approved.{0,60}support")

    def test_cod_detail_and_jp25_do_not_receive_the_country_main_support_contract(self) -> None:
        for suite_key, count in ((backend.AI_IMAGE_COD_DETAIL_SUITE_KEY, 22), (backend.AI_IMAGE_LANDING_SUITE_KEY, 25)):
            with self.subTest(suite=suite_key):
                prompts, pages = self.compile(count=count, suite_key=suite_key)
                self.assertFalse(any(page.get("codMainRich") or page.get("codMainSupportingPoints") for page in pages))
                self.assertNotIn("[COD MAIN SUPPORT CONTRACT]", "\n".join(prompts))
                self.assertNotIn("SUPPORTING_BENEFITS", json.dumps([page.get("companyModulePlan") or [] for page in pages]))
                review = self.message_text(self.review_messages([pages[0]], suite_key, count))
                self.assertNotIn("[COD MAIN SUPPORT CONTRACT]", review)
                self.assertRegex(review, r"(?i)(?:assigned|one|primary).{0,60}(?:selling.point|message)")

    def test_explicit_text_free_or_low_density_request_disables_rich_main_copy(self) -> None:
        for request in ("无字，只展示产品", "信息不要太多，画面简洁，少文字"):
            with self.subTest(request=request):
                brief = self.brief(extra=request)
                prompts, pages = self.compile(brief=brief)
                self.assertFalse(any(page.get("codMainRich") for page in pages[:15]))
                self.assertNotIn("[COD MAIN SUPPORT CONTRACT]", "\n".join(prompts[:15]))
                self.assertNotIn("SUPPORTING_BENEFITS", json.dumps([page.get("companyModulePlan") or [] for page in pages[:15]]))
                if "无字" in request:
                    self.assertTrue(all(page.get("textPolicy") == "none" for page in pages[:15]))
                    self.assertRegex(prompts[0], r"(?i)(?:text-free|textPolicy=NONE|no visible text)")

    def test_two_real_sources_do_not_turn_into_five_generic_support_claims(self) -> None:
        brief = self.brief(count=2)
        _prompts, pages = self.compile(brief=brief)
        source_titles = {title for title, _description in self.SOURCES[:2]}
        for page in pages[:15]:
            supporting = page.get("codMainSupportingPoints") or []
            self.assertLessEqual(len(supporting), 2)
            for point in supporting:
                self.assertEqual(point["sourceType"], "user")
                self.assertIn(point["title"], source_titles)
                self.assertNotEqual(point["title"], page.get("focusTitle"))
                self.assertNotRegex(point["label"], r"(?i)^(?:根据|展示|严格|保持|请|show\b|use\b|derive\b|extract\b)")
        self.assertEqual(len(pages[0].get("codMainSupportingPoints") or []), 1, "Keep the one actual auxiliary source without padding to three or five")


if __name__ == "__main__":
    unittest.main()
