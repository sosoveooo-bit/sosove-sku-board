"""Regression coverage for JP25 source locks and localized point bindings.

All director output is an in-memory fixture.  These tests exercise the actual
planning/compiler functions without creating image jobs or using live caches.
"""

from copy import deepcopy
import unittest
from unittest.mock import patch

from sku_board import backend


class Jp25PromptContractRegressionTests(unittest.TestCase):
    PRODUCT_PROMPT = "[Product] Exact light-khaki short-sleeve tailored jacket."
    SOURCE_POINTS = (
        ("宽松袖口", "宽松袖口留出自然活动空间", "ゆったり袖口", "袖まわりにゆとり", "PROOF_SLEEVE: show the open cuff around a relaxed arm"),
        ("自然织理", "细密织理带有自然的亚麻外观", "自然な織り感", "自然な生地の表情", "PROOF_WEAVE: show the fine woven surface in raking light"),
        ("端正翻领", "翻领线条保持利落外观", "端正なラペル", "すっきりした襟元", "PROOF_LAPEL: show the reference lapel edge at chest height"),
        ("实用口袋", "两侧口袋便于放置日常小物", "便利なポケット", "小物をさっと収納", "PROOF_POCKET: show one small item resting inside the pocket"),
        ("方便叠穿", "前开式结构便于叠穿", "重ね着しやすい", "さっと羽織れる", "PROOF_LAYER: show the open front over a separate plain inner layer"),
    )
    SOURCE_LOCK_CASES = (
        (
            "non-fashion-selling-point",
            "[Product] Multifunction kitchen opener.",
            "卖点：\n1. 轻量手持：握持轻巧方便使用。",
            "selling_point",
        ),
        (
            "fashion-authority",
            "[Product] 日系宽松大摆吊带连衣裙。",
            "以下是我的卖点及需求：\n"
            "1. 【宽松裙摆】裙摆宽松便于日常活动。\n\n"
            "权威背书\n"
            "1. 日本語背書テーマ（提供済み根拠）(【来源背书】用户提供的原始说明。)",
            "authority",
        ),
    )

    def setUp(self) -> None:
        # Fail loudly if a future refactor escapes the in-memory test boundary.
        for name in (
            "invoke_ai_director_chat",
            "get_ai_director_cached_analysis",
            "put_ai_director_cached_analysis",
        ):
            patcher = patch.object(
                backend,
                name,
                side_effect=AssertionError(f"Unexpected external/store operation: {name}"),
            )
            patcher.start()
            self.addCleanup(patcher.stop)

    @classmethod
    def five_point_brief(cls) -> str:
        return "5 大主卖点\n" + "\n".join(
            f"【主卖点{index}：{title}】大白话解析：{description}。"
            for index, (title, description, *_rest) in enumerate(cls.SOURCE_POINTS, start=1)
        )

    @classmethod
    def model_points(cls, *, with_source_indexes: bool) -> list[dict]:
        points = []
        for index, (_title, _description, localized_title, label, evidence) in enumerate(cls.SOURCE_POINTS, start=1):
            point = {
                "title": localized_title,
                "description": label,
                "copyLabels": [label],
                "evidenceDirection": evidence,
            }
            if with_source_indexes:
                point["sourcePointIndex"] = index
            points.append(point)
        return points

    @staticmethod
    def attach_remote_layers(pages: list[dict]) -> list[dict]:
        result = deepcopy(pages)
        for page in result:
            page_number = int(page["page"])
            visual = dict(page.get("visualEnhancement") or {})
            visual.update({
                "shotConcept": f"REMOTE_SHOT_{page_number:02d}: exact product in a finished reference-led photograph",
                "camera": f"50mm eye-level camera; remote page {page_number} route",
                "lighting": f"5000K left window light; remote page {page_number} route",
            })
            visual["companyPromptLayers"] = {
                "taskAnchor": f"Create the assigned Japanese ecommerce page {page_number}",
                "emotionAnchor": "Calm everyday confidence",
                "visualNarrative": f"REMOTE_PAGE_{page_number:02d}: one finished product photograph with exact reference construction",
                "layoutAndCopy": "Product 65%; approved Japanese copy 25%; calm space 10%",
                "colorScheme": "#FCF9F4, #5A3C29, #E4D6C9",
                "styleDirection": "Japanese documentary ecommerce editorial photography",
                "hardConstraints": "Freeze product, approved copy, anatomy and reference identity",
            }
            page["visualEnhancement"] = visual
            page["creativePassSource"] = "remote"
        return result

    def assert_complete_remote_contract(self, pages: list[dict]) -> None:
        status = backend.ai_image_jp_company_prompt_status(pages, 25)
        self.assertTrue(status["ready"], status)
        self.assertEqual(status["readyCount"], 25)
        for page in pages:
            with self.subTest(page=page["page"]):
                self.assertIn(
                    f"REMOTE_PAGE_{int(page['page']):02d}",
                    page["visualEnhancement"]["companyPromptLayers"]["visualNarrative"],
                )

    def test_final_plan_and_compiler_keep_remote_layers_for_nonfashion_source_and_fashion_authority(self) -> None:
        for case_name, prompt, brief, expected_source_type in self.SOURCE_LOCK_CASES:
            with self.subTest(case=case_name):
                director_pages = []

                def finished_director(base_pages, *_args, **_kwargs):
                    completed = self.attach_remote_layers(base_pages)
                    director_pages.extend(deepcopy(completed))
                    return completed, {
                        "source": "model",
                        "status": "ok",
                        "creativePassComplete": True,
                        "creativePassStats": {
                            "requestedPages": 25,
                            "refinedPages": 25,
                            "companyPromptPages": 25,
                            "companyPromptComplete": True,
                            "complete": True,
                        },
                    }

                with patch.object(backend, "shared_ai_director_enabled", return_value=True), patch.object(
                    backend, "refine_ai_image_suite_plan_with_director", side_effect=finished_director,
                ):
                    result = backend.plan_ai_image_suite(
                        {
                            "suiteKey": backend.AI_IMAGE_LANDING_SUITE_KEY,
                            "suiteCount": 25,
                            "size": backend.AI_IMAGE_SUITE_SIZE,
                            "prompt": prompt,
                            "suiteBrief": brief,
                            "useDirector": True,
                        },
                        {"role": "admin"},
                    )

                self.assertTrue(any(page.get("sourcePointType") == expected_source_type for page in director_pages))
                self.assert_complete_remote_contract(director_pages)
                self.assert_complete_remote_contract(result["suitePages"])
                self.assertTrue(result["companyPromptStatus"]["ready"])
                self.assertTrue(result["director"]["companyPromptReady"])
                for before, after in zip(director_pages, result["suitePages"]):
                    for field in ("companyPromptLayers", "shotConcept", "camera", "lighting"):
                        self.assertEqual(
                            after["visualEnhancement"][field],
                            before["visualEnhancement"][field],
                        )

                prompts, compiled = backend.build_ai_image_suite_prompts(
                    prompt, brief, backend.AI_IMAGE_SUITE_SIZE,
                    suite_key=backend.AI_IMAGE_LANDING_SUITE_KEY,
                    plan=result["suitePages"], suite_count=25,
                )
                self.assert_complete_remote_contract(compiled)
                for index, final_prompt in enumerate(prompts, start=1):
                    self.assertIn(f"REMOTE_PAGE_{index:02d}", final_prompt)
                    self.assertIn("[COMPANY AI-AUTHORED SEVEN-LAYER PROMPT", final_prompt)

    def test_source_lock_is_idempotent_and_keeps_remote_contract(self) -> None:
        cases = [*self.SOURCE_LOCK_CASES, ("fashion-five-source-points", self.PRODUCT_PROMPT, self.five_point_brief(), "selling_point")]
        for case_name, prompt, brief, _source_type in cases:
            with self.subTest(case=case_name):
                pages = self.attach_remote_layers(backend.build_ai_image_suite_plan(
                    prompt, brief, suite_key=backend.AI_IMAGE_LANDING_SUITE_KEY, count=25,
                ))
                original = deepcopy(pages)
                once = backend.lock_ai_image_cod_source_point_coverage(
                    pages, prompt, brief, backend.AI_IMAGE_LANDING_SUITE_KEY,
                )
                twice = backend.lock_ai_image_cod_source_point_coverage(
                    once, prompt, brief, backend.AI_IMAGE_LANDING_SUITE_KEY,
                )
                third = backend.lock_ai_image_cod_source_point_coverage(
                    twice, prompt, brief, backend.AI_IMAGE_LANDING_SUITE_KEY,
                )
                self.assertEqual(pages, original, "Source locking must not mutate its input")
                self.assert_complete_remote_contract(once)
                self.assert_complete_remote_contract(twice)
                self.assertEqual(twice, once, "Repeated source locking must not append duplicate evidence or module instructions")
                self.assertEqual(third, twice)

    def assert_five_point_bindings(self, analysis: dict) -> None:
        brief = self.five_point_brief()
        pages = backend.build_ai_image_suite_plan(
            self.PRODUCT_PROMPT, brief,
            suite_key=backend.AI_IMAGE_LANDING_SUITE_KEY, count=25,
        )
        original = deepcopy(pages)
        mapped = backend.apply_ai_director_selling_points_to_pages(
            pages, analysis, self.PRODUCT_PROMPT, brief, backend.AI_IMAGE_LANDING_SUITE_KEY,
        )
        self.assertEqual(pages, original, "Localized enrichment must not mutate its input")
        source_pages = {int(page["sourcePointIndex"]): page for page in mapped if int(page.get("sourcePointIndex") or 0) > 0}
        self.assertEqual(set(source_pages), set(range(1, 6)))
        for source_index, (title, description, localized_title, label, evidence) in enumerate(self.SOURCE_POINTS, start=1):
            with self.subTest(sourcePointIndex=source_index):
                page = source_pages[source_index]
                self.assertEqual(page["focusTitle"], title)
                self.assertIn(description, page["focusDescription"])
                self.assertIn(title, page["sourcePointVerbatim"])
                self.assertIn(description, page["sourcePointVerbatim"])
                self.assertEqual(page.get("localizedSellingPointTitle"), localized_title)
                self.assertEqual(page.get("copyLabels"), [label])
                self.assertEqual(page.get("directorSellingPointEvidence"), evidence)
        # P3 has the second source point but still carries the old main:0 slot.
        p3 = mapped[2]
        self.assertEqual(p3["page"], 3)
        self.assertEqual(p3["sourcePointIndex"], 2)
        self.assertEqual(p3["focusTitle"], "自然织理")
        self.assertEqual(p3["localizedSellingPointTitle"], "自然な織り感")

        remote_pages = self.attach_remote_layers(mapped)
        prompts, compiled = backend.build_ai_image_suite_prompts(
            self.PRODUCT_PROMPT, brief, backend.AI_IMAGE_SUITE_SIZE,
            suite_key=backend.AI_IMAGE_LANDING_SUITE_KEY, plan=remote_pages, suite_count=25,
        )
        self.assertEqual(compiled[2]["localizedSellingPointTitle"], "自然な織り感")
        self.assertEqual(compiled[2]["copyLabels"], [self.SOURCE_POINTS[1][3]])
        current_line = next(line for line in prompts[2].splitlines() if line.startswith("[CURRENT PAGE — ONE SELLING POINT]"))
        copy_line = next(line for line in prompts[2].splitlines() if line.startswith("[VISIBLE COPY — exact Japanese]"))
        self.assertIn("自然な織り感", current_line)
        self.assertIn(self.SOURCE_POINTS[1][1], current_line)
        self.assertNotIn("宽松袖口", current_line)
        self.assertIn("自然な織り感", copy_line)
        self.assertIn(self.SOURCE_POINTS[1][3], copy_line)
        self.assertNotIn("ゆったり袖口", copy_line)
        self.assertNotIn(self.SOURCE_POINTS[0][3], copy_line)

    def test_explicit_source_indexes_survive_normalization_and_bind_out_of_order_model_points(self) -> None:
        points = self.model_points(with_source_indexes=True)
        model = {
            "productSummary": "Exact short-sleeve tailored jacket",
            "mainSellingPoints": [points[index] for index in (4, 2, 0, 3, 1)],
            "secondarySellingPoints": [],
        }
        analysis = backend.normalize_ai_director_analysis(
            model, self.PRODUCT_PROMPT, self.five_point_brief(), backend.AI_IMAGE_LANDING_SUITE_KEY,
        )
        self.assert_five_point_bindings(analysis)

    def test_legacy_cached_points_without_source_indexes_bind_in_source_order(self) -> None:
        # Mirrors the cached-analysis branch, where points are already normalized
        # and lack the sourcePointIndex added to newly authored model records.
        cached_analysis = {
            "productSummary": "Exact short-sleeve tailored jacket",
            "mainSellingPoints": self.model_points(with_source_indexes=False),
            "secondarySellingPoints": [],
            "globalRequirements": [],
            "factAudit": {"provided": [], "visible": [], "inferred": [], "blocked": []},
        }
        self.assert_five_point_bindings(cached_analysis)
        with self.subTest(cache_shape="localized-title-without-localized-description"):
            title_only = {
                "mainSellingPoints": [
                    {
                        "sourcePointIndex": index,
                        "title": title,
                        "description": description,
                        "localizedTitle": localized_title,
                    }
                    for index, (title, description, localized_title, *_rest) in enumerate(self.SOURCE_POINTS, start=1)
                ],
                "secondarySellingPoints": [],
            }
            pages = backend.build_ai_image_suite_plan(
                self.PRODUCT_PROMPT, self.five_point_brief(),
                suite_key=backend.AI_IMAGE_LANDING_SUITE_KEY, count=25,
            )
            mapped = backend.apply_ai_director_selling_points_to_pages(
                pages, title_only, self.PRODUCT_PROMPT, self.five_point_brief(), backend.AI_IMAGE_LANDING_SUITE_KEY,
            )
            for page in mapped:
                source_index = int(page.get("sourcePointIndex") or 0)
                if source_index > 0:
                    self.assertEqual(page["localizedSellingPointTitle"], self.SOURCE_POINTS[source_index - 1][2])
                    self.assertFalse(page.get("copyLabels"), "Chinese source descriptions are not approved Japanese labels")
            prompts, compiled = backend.build_ai_image_suite_prompts(
                self.PRODUCT_PROMPT, self.five_point_brief(), backend.AI_IMAGE_SUITE_SIZE,
                suite_key=backend.AI_IMAGE_LANDING_SUITE_KEY, plan=self.attach_remote_layers(mapped), suite_count=25,
            )
            self.assert_complete_remote_contract(compiled)
            copy_line = next(line for line in prompts[2].splitlines() if line.startswith("[VISIBLE COPY — exact Japanese]"))
            self.assertIn("自然な織り感", copy_line)
            self.assertNotIn(self.SOURCE_POINTS[1][1], copy_line)

    def test_partial_legacy_records_do_not_shift_later_translations_or_keep_stale_bindings(self) -> None:
        brief = self.five_point_brief()
        source_points = backend.extract_ai_image_jp_source_points(self.PRODUCT_PROMPT, brief)
        complete = self.model_points(with_source_indexes=False)
        # Source 2 is missing: source 3 must not be guessed as source 2.
        partial = [complete[index] for index in (0, 2, 3, 4)]
        self.assertEqual(backend.map_ai_director_jp_source_points(source_points, partial, []), {})
        pages = backend.build_ai_image_suite_plan(
            self.PRODUCT_PROMPT, brief, suite_key=backend.AI_IMAGE_LANDING_SUITE_KEY, count=25,
        )
        for page in pages:
            if int(page.get("sourcePointIndex") or 0) > 0:
                page["localizedSellingPointTitle"] = "以前の別テーマ"
                page["copyLabels"] = ["以前のラベル"]
                page["directorSellingPointEvidence"] = "OLD_OTHER_POINT_PROOF"
                page["headline"] = "以前の別テーマ"
        mapped = backend.apply_ai_director_selling_points_to_pages(
            pages, {"mainSellingPoints": partial, "secondarySellingPoints": []},
            self.PRODUCT_PROMPT, brief, backend.AI_IMAGE_LANDING_SUITE_KEY,
        )
        for page in mapped:
            if int(page.get("sourcePointIndex") or 0) > 0:
                for field in ("localizedSellingPointTitle", "copyLabels", "directorSellingPointEvidence"):
                    self.assertNotIn(field, page, (page["page"], field))
                self.assertNotEqual(page.get("headline"), "以前の別テーマ")
        # A cached/partial pass still needs a valid serialized plan after stale
        # copy is removed; losing a required headline used to discard all pages.
        round_trip = backend.normalize_ai_image_suite_plan(self.attach_remote_layers(mapped), 25)
        self.assertEqual(len(round_trip), 25)
        self.assert_complete_remote_contract(round_trip)

    def test_shuffled_secondary_records_use_global_source_indexes(self) -> None:
        detail_points = (
            ("整齐包边", "边缘包边平整清楚", "きれいな縁仕上げ", "端まで丁寧", "PROOF_EDGE: show the reference bound edge"),
            ("紧密缝线", "缝线排列均匀清楚", "整ったステッチ", "縫い目まで丁寧", "PROOF_SEAM: show the reference seam close up"),
        )
        brief = self.five_point_brief() + "\n次卖点\n" + "\n".join(
            f"[细节{index}：{title}]：{description}。"
            for index, (title, description, *_rest) in enumerate(detail_points, start=1)
        )
        source_points = backend.extract_ai_image_jp_source_points(self.PRODUCT_PROMPT, brief)
        self.assertEqual(len(source_points), 7)
        self.assertEqual([point["kind"] for point in source_points], ["main"] * 5 + ["detail"] * 2)
        secondary = [
            {
                "sourcePointIndex": index,
                "title": localized_title,
                "description": label,
                "copyLabels": [label],
                "evidenceDirection": evidence,
            }
            for index, (_title, _description, localized_title, label, evidence) in enumerate(detail_points, start=6)
        ]
        analysis = backend.normalize_ai_director_analysis(
            {
                "productSummary": "Exact short-sleeve tailored jacket",
                "mainSellingPoints": self.model_points(with_source_indexes=True),
                "secondarySellingPoints": list(reversed(secondary)),
            },
            self.PRODUCT_PROMPT, brief, backend.AI_IMAGE_LANDING_SUITE_KEY,
        )
        pages = backend.build_ai_image_suite_plan(
            self.PRODUCT_PROMPT, brief, suite_key=backend.AI_IMAGE_LANDING_SUITE_KEY, count=25,
        )
        mapped = backend.apply_ai_director_selling_points_to_pages(
            pages, analysis, self.PRODUCT_PROMPT, brief, backend.AI_IMAGE_LANDING_SUITE_KEY,
        )
        by_source = {int(page["sourcePointIndex"]): page for page in mapped if int(page.get("sourcePointIndex") or 0) > 0}
        for source_index, (title, description, localized_title, label, evidence) in enumerate(detail_points, start=6):
            with self.subTest(sourcePointIndex=source_index):
                page = by_source[source_index]
                self.assertEqual(page["focusTitle"], title)
                self.assertIn(description, page["sourcePointVerbatim"])
                self.assertEqual(page["localizedSellingPointTitle"], localized_title)
                self.assertEqual(page["copyLabels"], [label])
                self.assertEqual(page["directorSellingPointEvidence"], evidence)

    def test_duplicate_source_indexes_drop_ambiguous_records_instead_of_reassigning_them(self) -> None:
        source_points = backend.extract_ai_image_jp_source_points(self.PRODUCT_PROMPT, self.five_point_brief())
        points = self.model_points(with_source_indexes=True)
        points[2]["sourcePointIndex"] = 2
        mapped = backend.map_ai_director_jp_source_points(source_points, points, [])
        self.assertEqual(set(mapped), {1, 4, 5})
        for source_index in (1, 4, 5):
            self.assertEqual(mapped[source_index]["title"], self.SOURCE_POINTS[source_index - 1][2])
            self.assertEqual(mapped[source_index]["sourcePointIndex"], source_index)

    def test_changed_source_title_or_explanation_invalidates_only_its_old_remote_page(self) -> None:
        brief = self.five_point_brief()
        old_pages = self.attach_remote_layers(backend.build_ai_image_suite_plan(
            self.PRODUCT_PROMPT, brief, suite_key=backend.AI_IMAGE_LANDING_SUITE_KEY, count=25,
        ))
        old_pages[2]["localizedSellingPointTitle"] = self.SOURCE_POINTS[1][2]
        old_pages[2]["copyLabels"] = [self.SOURCE_POINTS[1][3]]
        old_pages[2]["directorSellingPointEvidence"] = self.SOURCE_POINTS[1][4]
        for old_text, new_text in (
            ("自然织理", "顺滑触感"),
            (self.SOURCE_POINTS[1][1], "细密织理呈现另一处明确的原文要求"),
        ):
            with self.subTest(changed=old_text):
                new_brief = brief.replace(old_text, new_text)
                locked = backend.lock_ai_image_cod_source_point_coverage(
                    old_pages, self.PRODUCT_PROMPT, new_brief, backend.AI_IMAGE_LANDING_SUITE_KEY,
                )
                status = backend.ai_image_jp_company_prompt_status(locked, 25)
                self.assertEqual(status["readyCount"], 24)
                self.assertEqual(status["missingPages"], [3])
                changed_page = locked[2]
                self.assertIn(new_text, changed_page["sourcePointVerbatim"])
                self.assertNotIn("companyPromptLayers", changed_page["visualEnhancement"])
                for field in ("localizedSellingPointTitle", "copyLabels", "directorSellingPointEvidence", "creativePassSource"):
                    self.assertNotIn(field, changed_page)
                for before, after in zip(old_pages, locked):
                    if int(after["page"]) != 3:
                        self.assertEqual(
                            before["visualEnhancement"]["companyPromptLayers"],
                            after["visualEnhancement"]["companyPromptLayers"],
                        )

    def test_removed_source_point_does_not_leave_its_remote_layers_on_a_support_page(self) -> None:
        brief = self.five_point_brief()
        pages = self.attach_remote_layers(backend.build_ai_image_suite_plan(
            self.PRODUCT_PROMPT, brief, suite_key=backend.AI_IMAGE_LANDING_SUITE_KEY, count=25,
        ))
        former_source_page = next(page for page in pages if int(page.get("sourcePointIndex") or 0) == 5)
        self.assertEqual(former_source_page["page"], 6)
        former_source_page["localizedSellingPointTitle"] = self.SOURCE_POINTS[4][2]
        former_source_page["copyLabels"] = [self.SOURCE_POINTS[4][3]]
        former_source_page["directorSellingPointEvidence"] = self.SOURCE_POINTS[4][4]
        reduced_brief = "\n".join(line for line in brief.splitlines() if "主卖点5：" not in line)
        locked = backend.lock_ai_image_cod_source_point_coverage(
            pages, self.PRODUCT_PROMPT, reduced_brief, backend.AI_IMAGE_LANDING_SUITE_KEY,
        )
        changed_page = locked[5]
        self.assertEqual(changed_page["sourcePointIndex"], 0)
        self.assertEqual(changed_page["sourcePointType"], "planner_support")
        self.assertNotIn("companyPromptLayers", changed_page.get("visualEnhancement") or {})
        for field in ("localizedSellingPointTitle", "copyLabels", "directorSellingPointEvidence", "creativePassSource", "sourcePointVerbatim"):
            self.assertNotIn(field, changed_page)
        status = backend.ai_image_jp_company_prompt_status(locked, 25)
        self.assertEqual(status["readyCount"], 24)
        self.assertEqual(status["missingPages"], [6])

    def test_model_added_performance_claim_is_removed_without_dropping_the_source_point(self) -> None:
        brief = self.five_point_brief()
        for contaminated_field in ("title", "description", "copyLabels", "evidenceDirection"):
            with self.subTest(field=contaminated_field):
                points = self.model_points(with_source_indexes=True)
                points[0][contaminated_field] = ["100%効果"] if contaminated_field == "copyLabels" else "100%効果"
                analysis = backend.normalize_ai_director_analysis(
                    {
                        "productSummary": "Exact short-sleeve tailored jacket",
                        "mainSellingPoints": points,
                        "secondarySellingPoints": [],
                    },
                    self.PRODUCT_PROMPT, brief, backend.AI_IMAGE_LANDING_SUITE_KEY,
                )
                by_source = {int(point["sourcePointIndex"]): point for point in analysis["mainSellingPoints"]}
                self.assertEqual(set(by_source), set(range(1, 6)))
                first = by_source[1]
                self.assertEqual(first["title"], self.SOURCE_POINTS[0][0])
                self.assertEqual(first["description"], self.SOURCE_POINTS[0][1])
                for field in ("localizedTitle", "localizedDescription", "copyLabels", "evidenceDirection"):
                    self.assertNotIn(field, first)
                self.assertEqual(by_source[2]["localizedTitle"], self.SOURCE_POINTS[1][2])

                pages = backend.build_ai_image_suite_plan(
                    self.PRODUCT_PROMPT, brief, suite_key=backend.AI_IMAGE_LANDING_SUITE_KEY, count=25,
                )
                mapped = backend.apply_ai_director_selling_points_to_pages(
                    pages, analysis, self.PRODUCT_PROMPT, brief, backend.AI_IMAGE_LANDING_SUITE_KEY,
                )
                source_page = next(page for page in mapped if int(page.get("sourcePointIndex") or 0) == 1)
                self.assertEqual(source_page["focusTitle"], self.SOURCE_POINTS[0][0])
                self.assertIn(self.SOURCE_POINTS[0][1], source_page["sourcePointVerbatim"])
                for field in ("localizedSellingPointTitle", "directorSellingPointEvidence", "copyLabels"):
                    self.assertNotIn("100%", str(source_page.get(field, "")))
                round_trip = backend.normalize_ai_image_suite_plan(self.attach_remote_layers(mapped), 25)
                self.assertEqual(len(round_trip), 25)
                self.assert_complete_remote_contract(round_trip)

    def test_localized_source_binding_leaves_other_suite_plans_unchanged(self) -> None:
        analysis = {"mainSellingPoints": self.model_points(with_source_indexes=True), "secondarySellingPoints": []}
        for suite_key in (
            backend.AI_IMAGE_AMAZON_APLUS_SUITE_KEY,
            backend.AI_IMAGE_RAKUTEN_SUITE_KEY,
            backend.AI_IMAGE_COD_SUITE_KEY,
        ):
            with self.subTest(suite=suite_key):
                pages = backend.build_ai_image_suite_plan(
                    self.PRODUCT_PROMPT, self.five_point_brief(), suite_key=suite_key,
                )
                before = deepcopy(pages)
                after = backend.apply_ai_director_selling_points_to_pages(
                    pages, analysis, self.PRODUCT_PROMPT, self.five_point_brief(), suite_key,
                )
                self.assertEqual(after, before)
                self.assertEqual(pages, before)


if __name__ == "__main__":
    unittest.main()
