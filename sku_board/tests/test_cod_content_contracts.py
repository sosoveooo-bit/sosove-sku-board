"""Public COD planning/compilation regressions using synthetic source contracts."""

from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from sku_board import backend


class CodContentContractTests(unittest.TestCase):
    PRODUCT_PROMPT = "[Product] Exact compact kitchen tool from the supplied reference."
    CAPACITY_ERROR = r"(?i)(卖点|来源|内容|容量|不足|待补|完整|source|coverage|capacity|content)"

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="cod-content-contract-")
        self.addCleanup(temporary.cleanup)
        data_dir = Path(temporary.name)
        for name, value in (
            ("DATA_DIR", data_dir),
            ("DATA_FILE", data_dir / "board.json"),
            ("AI_DIRECTOR_SETTINGS_FILE", data_dir / "director.json"),
            ("AI_DIRECTOR_CACHE_FILE", data_dir / "cache.json"),
        ):
            patcher = patch.object(backend, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        for name in (
            "invoke_ai_director_chat",
            "load_ai_director_settings",
            "get_ai_director_cached_analysis",
            "put_ai_director_cached_analysis",
            "save_ai_image_outputs",
        ):
            patcher = patch.object(backend, name, side_effect=AssertionError(f"Unexpected model/store operation: {name}"))
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(backend, "public_ai_director_settings", return_value={
            "enabled": False, "configured": False, "model": "fixture-director", "reviewEnabled": False,
        })
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("requests.sessions.Session.request", side_effect=AssertionError("Network disabled in COD contract tests"))
        patcher.start()
        self.addCleanup(patcher.stop)

    @staticmethod
    def source_brief(detail_count=12):
        titles = [f"SOURCE_MAIN_{index:02d}" for index in range(1, 6)]
        titles += [f"SOURCE_DETAIL_{index:02d}" for index in range(1, detail_count + 1)]
        lines = ["目标国家日本；保留当前商品结构。", "5 大主卖点"]
        lines.extend(
            f"【主卖点{index}：SOURCE_MAIN_{index:02d}】大白话解析：FACT_MAIN_{index:02d}。"
            for index in range(1, 6)
        )
        lines.append("次卖点")
        lines.extend(
            f"[细节{index}：SOURCE_DETAIL_{index:02d}]：FACT_DETAIL_{index:02d}。"
            for index in range(1, detail_count + 1)
        )
        return "\n".join(lines), titles

    def plan(self, suite_key, count, brief):
        return backend.plan_ai_image_suite(
            {
                "suiteKey": suite_key,
                "suiteCount": count,
                "suiteCountry": "JP",
                "size": "750x1000",
                "prompt": self.PRODUCT_PROMPT,
                "suiteBrief": brief,
                "useDirector": False,
            },
            {"role": "admin"},
        )

    def test_combined_structured_titles_do_not_create_duplicate_heading_sources(self):
        brief = (
            "5 大主卖点\n【主卖点1：轻巧便携、易用省力】大白话解析：保持正确使用。\n"
            "次卖点\n[细节1：整齐包边/紧密缝线]：保持原始结构。"
        )
        main, detail = backend.extract_ai_image_cod_kr_points(self.PRODUCT_PROMPT, brief, preserve_all_source=True)
        supplied = [point["title"] for point in [*main, *detail] if point.get("sourceProvided")]
        self.assertEqual(supplied, ["轻巧便携", "易用省力", "整齐包边", "紧密缝线"])
        result = self.plan(backend.AI_IMAGE_COD_SUITE_KEY, 20, brief)
        self.assertEqual(result["director"]["sellingPointCoverage"]["total"], 4)
        self.assertTrue(result["director"]["sellingPointCoverage"]["complete"])

    def test_global_visual_requirements_do_not_inflate_source_coverage(self):
        brief, titles = self.source_brief()
        brief += "\n背景：浅灰色\n模特要求：成年女性\n文字语言：日语\n画面尺寸：750x1000"
        main, detail = backend.extract_ai_image_cod_kr_points(self.PRODUCT_PROMPT, brief, preserve_all_source=True)
        supplied = [point["title"] for point in [*main, *detail] if point.get("sourceProvided")]
        self.assertEqual(supplied, titles)
        result = self.plan(backend.AI_IMAGE_COD_SUITE_KEY, 20, brief)
        self.assertEqual(result["director"]["sellingPointCoverage"]["total"], 17)
        self.assertTrue(result["director"]["sellingPointCoverage"]["complete"])

    def assert_complete_source_plan_and_prompts(self, suite_key, count):
        brief, expected_titles = self.source_brief()
        result = self.plan(suite_key, count, brief)
        coverage = result["director"]["sellingPointCoverage"]
        self.assertEqual(coverage["total"], 17)
        self.assertEqual(coverage["assigned"], 17)
        self.assertTrue(coverage["complete"], coverage)
        self.assertEqual(coverage["missing"], [])
        pages = result["suitePages"]
        self.assertEqual(len(pages), count)
        assigned = [page for page in pages if int(page.get("sourcePointIndex") or 0) > 0]
        self.assertEqual({page["focusTitle"] for page in assigned}, set(expected_titles))
        self.assertEqual({int(page["sourcePointIndex"]) for page in assigned}, set(range(1, 18)))
        prompts, compiled = backend.build_ai_image_suite_prompts(
            self.PRODUCT_PROMPT, brief, "750x1000",
            suite_key=suite_key, country="JP", suite_count=count, plan=pages,
        )
        self.assertEqual(len(prompts), count)
        self.assertEqual(len(compiled), count)
        for title in expected_titles:
            with self.subTest(source=title):
                index = next(index for index, page in enumerate(compiled) if page.get("focusTitle") == title)
                self.assertGreater(int(compiled[index].get("sourcePointIndex") or 0), 0)
                self.assertIn(title, compiled[index]["sourcePointVerbatim"])
                self.assertIn(title, prompts[index])
        self.assertIn("SOURCE_DETAIL_12", "\n".join(prompts))

    def test_country_thirty_and_thirty_seven_keep_all_seventeen_explicit_points(self):
        for count in (30, 37):
            with self.subTest(count=count):
                self.assert_complete_source_plan_and_prompts(backend.AI_IMAGE_COD_SUITE_KEY, count)

    def test_detail_twenty_two_keeps_all_seventeen_explicit_points(self):
        self.assert_complete_source_plan_and_prompts(backend.AI_IMAGE_COD_DETAIL_SUITE_KEY, 22)

    def test_short_suites_report_all_unassigned_points_instead_of_a_complete_green_status(self):
        for suite_key in (backend.AI_IMAGE_COD_SUITE_KEY, backend.AI_IMAGE_COD_DETAIL_SUITE_KEY):
            for count, detail_count in ((12, 12), (16, 12), (20, 18)):
                with self.subTest(suite=suite_key, count=count):
                    brief, expected_titles = self.source_brief(detail_count)
                    self.assertGreater(len(expected_titles), count)
                    try:
                        result = self.plan(suite_key, count, brief)
                    except ValueError as exc:
                        self.assertRegex(str(exc), self.CAPACITY_ERROR)
                        continue
                    coverage = result["director"]["sellingPointCoverage"]
                    self.assertEqual(coverage["total"], len(expected_titles))
                    self.assertFalse(coverage["complete"], coverage)
                    self.assertTrue(coverage["missing"], coverage)
                    self.assertEqual(coverage["assigned"] + len(coverage["missing"]), len(expected_titles))
                    self.assertGreaterEqual(len(coverage["missing"]), len(expected_titles) - count)

    def test_incomplete_source_contract_is_stopped_before_any_image_dispatch(self):
        for suite_key in (backend.AI_IMAGE_COD_SUITE_KEY, backend.AI_IMAGE_COD_DETAIL_SUITE_KEY):
            for count, detail_count in ((12, 12), (16, 12), (20, 18)):
                with self.subTest(suite=suite_key, count=count):
                    brief, _titles = self.source_brief(detail_count)
                    # A stale or independently submitted page plan must be checked
                    # against the current full brief again at the public endpoint.
                    stale_pages = backend.build_ai_image_suite_plan(
                        self.PRODUCT_PROMPT, "Target country JP; preserve the reference product.",
                        "750x1000", suite_key=suite_key, country="JP", count=count,
                    )
                    fields = {
                        "prompt": self.PRODUCT_PROMPT,
                        "model": "gpt-image-2",
                        "mode": "edit",
                        "size": "750x1000",
                        "quality": "high",
                        "count": 1,
                        "suiteKey": suite_key,
                        "suiteCount": count,
                        "suiteCountry": "JP",
                        "suiteBrief": brief,
                        "suitePlan": json.dumps(stale_pages, ensure_ascii=False),
                        "suitePageIndexes": "[1]",
                        "referenceBindings": json.dumps([{"role": "product", "name": "fixture.png"}]),
                    }
                    upload = SimpleNamespace(filename="fixture.png", file=BytesIO(b"fixture-upload"))
                    with patch.object(backend, "normalize_ai_image_request_fields", return_value=(
                        self.PRODUCT_PROMPT, "gpt-image-2", "750x1000", "high", 1, 10, 1,
                    )), patch.object(backend, "read_ai_image_upload", return_value=("fixture.png", b"fixture-image", "image/png")), patch.object(
                        backend, "chatgpt2api_image_tasks_enabled", return_value=True,
                    ), patch.object(backend, "generate_ai_image_tasks_with_transient_retry", side_effect=AssertionError("Unexpected image dispatch")) as dispatch, patch.object(
                        backend, "generate_images_via_acore", side_effect=AssertionError("Unexpected alternate image dispatch"),
                    ) as alternate_dispatch:
                        with self.assertRaisesRegex(ValueError, self.CAPACITY_ERROR):
                            backend.generate_ad_launch_ai_image_edit(fields, {"reference0": upload}, {"role": "admin"})
                        dispatch.assert_not_called()
                        alternate_dispatch.assert_not_called()

    def test_country_page_nine_stays_main_for_37_and_explicit_12_plus_18(self):
        for count, split_brief, expected_main in ((37, "日本市场商品介绍。", 15), (30, "主图12张，详情18张。", 12)):
            with self.subTest(count=count, split=split_brief):
                result = self.plan(backend.AI_IMAGE_COD_SUITE_KEY, count, split_brief)
                page_nine = result["suitePages"][8]
                self.assertEqual(page_nine["section"], "主图")
                self.assertEqual(int(page_nine["sectionIndex"]), 9)
                prompts, compiled = backend.build_ai_image_suite_prompts(
                    self.PRODUCT_PROMPT, split_brief, "750x1000",
                    suite_key=backend.AI_IMAGE_COD_SUITE_KEY, country="JP", suite_count=count, plan=result["suitePages"],
                )
                self.assertIn(f"Main image 9 of {expected_main}", prompts[8])
                self.assertNotIn("Detail image 1 of", prompts[8])
                self.assertEqual(compiled[8]["section"], "主图")
                self.assertEqual(int(compiled[8]["sectionIndex"]), 9)
                self.assertTrue(compiled[8]["codMainRich"])
                self.assertIn("[COD MAIN SUPPORT CONTRACT]", prompts[8])
                self.assertIn("[COD main core-and-support lock]", prompts[8])
                self.assertIn("exact compact kitchen tool", prompts[8].lower())
                self.assertFalse(compiled[expected_main].get("codMainRich", False))
                self.assertIn(f"Detail image 1 of {count - expected_main}", prompts[expected_main])
                self.assertNotIn("[COD MAIN SUPPORT CONTRACT]", prompts[expected_main])

    def test_cod_batch_narrative_stages_use_the_actual_suite_page_count(self):
        for suite_key, count in ((backend.AI_IMAGE_COD_SUITE_KEY, 30), (backend.AI_IMAGE_COD_SUITE_KEY, 37), (backend.AI_IMAGE_COD_DETAIL_SUITE_KEY, 22)):
            pages = backend.build_ai_image_suite_plan(
                self.PRODUCT_PROMPT, "日本市场商品说明。", "750x1000",
                suite_key=suite_key, country="JP", count=count,
            )
            analysis = {"productSummary": "Exact reference product", "_suitePageCount": count}
            for target_page in (5, 6, 12, 18):
                with self.subTest(suite=suite_key, count=count, page=target_page):
                    start = ((target_page - 1) // 5) * 5
                    batch = pages[start:start + 5]
                    messages = backend.build_ai_director_page_refinement_messages(batch, analysis, suite_key, "JP")
                    content = messages[-1]["content"]
                    marker = "[Locked pages]\n"
                    self.assertIn(marker, content)
                    compact_pages, _end = json.JSONDecoder().raw_decode(content.split(marker, 1)[1])
                    compact = next(page for page in compact_pages if int(page["page"]) == target_page)
                    self.assertEqual(
                        compact["narrativeStage"],
                        backend.ai_image_company_narrative_stage(target_page, count),
                    )

    def test_other_suite_counts_and_source_boundaries_are_unchanged(self):
        for suite_key, expected_count in (
            (backend.AI_IMAGE_LANDING_SUITE_KEY, 25),
            (backend.AI_IMAGE_AMAZON_APLUS_SUITE_KEY, 9),
            (backend.AI_IMAGE_RAKUTEN_SUITE_KEY, 9),
        ):
            with self.subTest(suite=suite_key):
                pages = backend.build_ai_image_suite_plan(
                    self.PRODUCT_PROMPT, "Show the reference product for the Japanese market.", suite_key=suite_key,
                )
                before = deepcopy(pages)
                self.assertEqual(len(pages), expected_count)
                self.assertEqual([page["page"] for page in pages], list(range(1, expected_count + 1)))
                prompts, compiled = backend.build_ai_image_suite_prompts(
                    self.PRODUCT_PROMPT, "Show the reference product for the Japanese market.",
                    backend.ai_image_suite_config(suite_key)["size"], suite_key=suite_key, plan=pages, suite_count=expected_count,
                )
                self.assertEqual(len(prompts), expected_count)
                self.assertEqual(len(compiled), expected_count)
                self.assertEqual(pages, before)


if __name__ == "__main__":
    unittest.main()
