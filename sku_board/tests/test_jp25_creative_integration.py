"""JP25 shared-photography integration contracts, with all I/O mocked.

These tests inspect real director messages and the page-refinement orchestrator.
They never submit an image, contact a model, or use the panel's persisted data.
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


class Jp25CreativeIntegrationTests(unittest.TestCase):
    LEGACY_FREEZE = (
        "The product analysis and locked page plan below are final content contracts. "
        "Refine execution only; keep product, color, variant, person, language, scene category, "
        "action, selling point, page role, page count and visible wording unchanged."
    )
    LEGACY_WORD_LIMIT = "Keep every string under 32 words."

    def setUp(self) -> None:
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        data_dir = Path(self.stack.enter_context(tempfile.TemporaryDirectory(prefix="jp25-creative-test-")))
        self.stack.enter_context(patch.dict(os.environ, {
            "SKU_BOARD_DATA_DIR": str(data_dir),
            "AI_DIRECTOR_JP25_REFINEMENT_WORKERS": "1",
            "AI_DIRECTOR_JP25_REFINEMENT_BATCH_SIZE": "3",
            "AI_DIRECTOR_JP25_SINGLE_PAGE_RETRIES": "0",
        }))
        for name, value in {
            "DATA_DIR": data_dir,
            "AI_DIRECTOR_SETTINGS_FILE": data_dir / "director-settings.json",
            "AI_DIRECTOR_CACHE_FILE": data_dir / "director-cache.json",
            "AI_IMAGE_JOBS_FILE": data_dir / "image-jobs.json",
            "AI_IMAGE_ERROR_LOG": data_dir / "image-errors.log",
        }.items():
            self.stack.enter_context(patch.object(backend, name, value))
        for target in ("requests.sessions.Session.request", "urllib.request.urlopen"):
            self.stack.enter_context(patch(target, side_effect=AssertionError("Unexpected real network call")))
        for name in (
            "invoke_ai_director_chat",
            "get_ai_director_cached_analysis",
            "put_ai_director_cached_analysis",
        ):
            self.stack.enter_context(patch.object(
                backend, name, side_effect=AssertionError(f"Unexpected external/store operation: {name}"),
            ))

    @staticmethod
    def pages() -> list[dict]:
        return [
            {
                "page": number,
                "role": f"Product evidence page {number}",
                "objective": f"Prove SOURCE_POINT_{number:02d}",
                "focus": f"SOURCE_POINT_{number:02d}: complete supplied explanation",
                "focusTitle": f"SOURCE_POINT_{number:02d}",
                "focusDescription": f"EXACT_SOURCE_DESCRIPTION_{number:02d}",
                "sourcePointIndex": number,
                "sourcePointKind": "main" if number <= 5 else "detail",
                "sourcePointType": "selling_point",
                "sourcePointVerbatim": f"VERBATIM_SOURCE_POINT_{number:02d}: unchanged source meaning",
                "sellingPoint": f"SOURCE_POINT_{number:02d}: complete supplied explanation",
                "evidence": f"SOURCE_EVIDENCE_{number:02d}",
                "headline": f"承認済みの見出し{number}",
                "localizedSellingPointTitle": f"承認済みの見出し{number}",
                "copyLabels": [f"ラベル{number}"],
                "scene": f"LOCAL_SCENE_{number:02d}",
                "pose": f"LOCAL_ACTION_{number:02d}",
                "composition": f"LOCAL_LAYOUT_{number:02d}",
                "pageArchetype": "product proof",
                "inspirationArchetype": "product",
                "size": "1500x2000",
                "textPolicy": "requested",
                "productTruthSummary": "EXACT_PRODUCT_IDENTITY_MARKER",
                "visualEnhancement": {
                    "shotConcept": f"LOCAL_PREVIS_{number:02d}",
                    "camera": "Local suggested 50mm lens",
                    "lighting": "Local suggested daylight",
                },
            }
            for number in range(1, 26)
        ]

    @staticmethod
    def photography_plan() -> dict:
        return {
            "visualBible": {
                "mood": "BIBLE_MOOD_MARKER: quiet confident Japanese editorial",
                "lighting": "BIBLE_LIGHT_MARKER: warm side light with soft shadow",
                "palette": "BIBLE_PALETTE_MARKER: #C6AE83, #FBF6EF, #37342F",
            },
            "pages": [
                {
                    "page": number,
                    "scene": f"GLOBAL_ROUTE_{number:02d}: independent Japanese room zone",
                    "action": f"One source-correct interaction for page {number}",
                    "camera": f"Camera route {number}: eye-level diagonal view",
                    "lighting": f"Light route {number}: side illumination with grounded shadow",
                    "layout": f"Layout route {number}: product right, headline lower left",
                    "evidenceTreatment": f"Evidence route {number}: show the exact current source point",
                }
                for number in range(1, 26)
            ],
        }

    @classmethod
    def analysis(cls, *, with_plan: bool = True) -> dict:
        result = {
            "productSummary": "EXACT_PRODUCT_IDENTITY_MARKER",
            "productVisualDNA": {
                "shapeAnchors": ["EXACT_PRODUCT_SHAPE_MARKER"],
                "materialAnchors": ["EXACT_PRODUCT_MATERIAL_MARKER"],
                "observableColors": ["#C6AE83"],
            },
            "referenceAnalysis": {"product": "Exact reference-confirmed construction"},
            "referenceBreakdown": [],
            "marketResearch": {},
            "globalRequirements": ["Keep supplied source wording and product identity unchanged"],
        }
        if with_plan:
            result["_jp25PhotographyPlan"] = cls.photography_plan()
        return result

    @staticmethod
    def remote_enhancement(number: int) -> dict:
        return {
            "shotConcept": f"REMOTE_PAGE_{number:02d}: the exact source-bound product photograph",
            "evidenceDirection": "Show the current source point with a real product detail",
            "actionDirection": "One simple source-correct interaction",
            "camera": "50mm lens at chest height",
            "lighting": "Soft directional side light",
            "spatialPlan": "Product right, exact Japanese headline lower left",
            "companyPromptLayers": {
                "taskAnchor": f"Create the exact approved page {number}",
                "emotionAnchor": "Quiet confidence",
                "visualNarrative": f"REMOTE_PAGE_{number:02d}: an already-finished reference-correct photograph",
                "layoutAndCopy": "Use the approved Japanese headline and exact product",
                "colorScheme": "#C6AE83, #FBF6EF, #37342F",
                "styleDirection": "Japanese editorial product photography",
                "hardConstraints": "Freeze source meaning, approved copy and exact product identity",
            },
        }

    @staticmethod
    def refinement_settings() -> dict:
        return {
            "model": "fixture-director",
            "fallbackModels": [],
            "timeout": 120,
            "_jp25CreativePlanning": True,
        }

    @staticmethod
    def message_text(messages: list[dict]) -> str:
        fragments = []
        for message in messages:
            content = message.get("content")
            if isinstance(content, str):
                fragments.append(content)
            elif isinstance(content, list):
                fragments.extend(
                    item.get("text", "") for item in content
                    if isinstance(item, dict) and item.get("type") == "text"
                )
        return "\n".join(fragments)

    @classmethod
    def json_section(cls, messages: list[dict], marker: str):
        message_text = cls.message_text(messages)
        if marker not in message_text:
            raise AssertionError(f"Director message omitted {marker}")
        value, _end = json.JSONDecoder().raw_decode(message_text.split(marker, 1)[1].lstrip())
        return value

    def build_messages(self, numbers: tuple[int, ...], *, suite_key: str | None = None) -> list[dict]:
        pages = self.pages()
        return backend.build_ai_director_page_refinement_messages(
            [pages[number - 1] for number in numbers],
            self.analysis(),
            suite_key or backend.AI_IMAGE_LANDING_SUITE_KEY,
            "JP",
            {},
        )

    def test_three_page_batch_narrative_stages_use_the_whole_twenty_five_page_suite(self) -> None:
        for numbers in ((1, 2, 3), (9, 10, 11), (13, 14, 15)):
            with self.subTest(batch=numbers):
                locked = self.json_section(self.build_messages(numbers), "[Locked pages]")
                self.assertEqual([page["page"] for page in locked], list(numbers))
                for page in locked:
                    self.assertEqual(
                        page["narrativeStage"],
                        backend.ai_image_company_narrative_stage(page["page"], 25),
                        f"P{page['page']} stage depends on total suite length, not batch length",
                    )

    def test_single_page_split_keeps_p3_p10_p15_at_their_original_narrative_stages(self) -> None:
        for number in (3, 10, 15):
            with self.subTest(page=number):
                locked = self.json_section(self.build_messages((number,)), "[Locked pages]")
                self.assertEqual(locked[0]["page"], number)
                self.assertEqual(
                    locked[0]["narrativeStage"],
                    backend.ai_image_company_narrative_stage(number, 25),
                )

    def test_every_batch_receives_all_routes_and_the_shared_visual_bible(self) -> None:
        for numbers in ((1, 2, 3), (10,), (13, 14, 15)):
            with self.subTest(batch=numbers):
                message_text = self.message_text(self.build_messages(numbers))
                missing = [f"GLOBAL_ROUTE_{number:02d}" for number in range(1, 26) if f"GLOBAL_ROUTE_{number:02d}" not in message_text]
                self.assertEqual(missing, [], "A batch must see the other pages' photography assignments")
                for marker in ("BIBLE_MOOD_MARKER", "BIBLE_LIGHT_MARKER", "BIBLE_PALETTE_MARKER"):
                    self.assertIn(marker, message_text)

    def test_jp25_frees_local_scene_and_action_without_relaxing_source_or_product_locks(self) -> None:
        numbers = (3, 10, 15)
        messages = self.build_messages(numbers)
        message_text = self.message_text(messages)
        for old_rule in (
            self.LEGACY_FREEZE,
            self.LEGACY_WORD_LIMIT,
            "while preserving the locked action category and supplied operation",
        ):
            with self.subTest(removed_rule=old_rule):
                self.assertFalse(old_rule in message_text, f"JP25 still carries the obsolete rule: {old_rule}")
        locked = self.json_section(messages, "[Locked pages]")
        originals = self.pages()
        for page in locked:
            original = originals[page["page"] - 1]
            for field in ("sourcePointVerbatim", "sellingPoint", "headline", "copyLabels", "productTruthSummary"):
                self.assertEqual(page[field], original[field], f"P{page['page']} changed {field}")
        analysis = self.json_section(messages, "[Product analysis]")
        self.assertEqual(analysis["productSummary"], "EXACT_PRODUCT_IDENTITY_MARKER")
        self.assertEqual(analysis["productVisualDNA"]["shapeAnchors"], ["EXACT_PRODUCT_SHAPE_MARKER"])

    def test_non_jp_suites_keep_prompt_rules_with_suite_aware_cod_batch_stages(self) -> None:
        for suite_key, narrative_total in (
            (backend.AI_IMAGE_AMAZON_APLUS_SUITE_KEY, 3),
            (backend.AI_IMAGE_RAKUTEN_SUITE_KEY, 3),
            (backend.AI_IMAGE_COD_SUITE_KEY, 30),
            (backend.AI_IMAGE_COD_DETAIL_SUITE_KEY, 22),
        ):
            with self.subTest(suite=suite_key):
                messages = self.build_messages((1, 2, 3), suite_key=suite_key)
                message_text = self.message_text(messages)
                self.assertIn(self.LEGACY_FREEZE, message_text)
                self.assertIn(self.LEGACY_WORD_LIMIT, message_text)
                self.assertNotIn("GLOBAL_ROUTE_25", message_text)
                self.assertNotIn("BIBLE_MOOD_MARKER", message_text)
                locked = self.json_section(messages, "[Locked pages]")
                self.assertEqual([page["page"] for page in locked], [1, 2, 3])
                for page in locked:
                    self.assertEqual(
                        page["narrativeStage"],
                        backend.ai_image_company_narrative_stage(page["page"], narrative_total),
                    )

    def test_global_photography_plan_runs_once_and_partial_cache_resumes_only_missing_page(self) -> None:
        events: list[tuple[str, tuple[int, ...]]] = []
        first_round = True
        all_pages = self.pages()

        def model_fixture(_settings, messages):
            text = self.message_text(messages)
            if "[JP25 GLOBAL PHOTOGRAPHY PLAN]" in text:
                events.append(("global", tuple(range(1, 26))))
                return json.dumps(self.photography_plan()), 10
            locked = self.json_section(messages, "[Locked pages]")
            numbers = tuple(page["page"] for page in locked)
            events.append(("pages", numbers))
            for number in range(1, 26):
                self.assertIn(f"GLOBAL_ROUTE_{number:02d}", text)
            self.assertIn("BIBLE_MOOD_MARKER", text)
            return json.dumps({
                "pages": [
                    {"page": number, "visualEnhancement": self.remote_enhancement(number)}
                    for number in numbers if not (first_round and number == 10)
                ],
            }), 5

        with patch.object(backend, "invoke_ai_director_chat", side_effect=model_fixture):
            partial, _latency = backend.refine_ai_director_page_visuals(
                self.refinement_settings(), all_pages, self.analysis(with_plan=False),
                backend.AI_IMAGE_LANDING_SUITE_KEY, "JP", {},
            )
            self.assertTrue(events, "The planning pipeline made no model calls")
            self.assertEqual(events[0][0], "global", "Shared photography must precede every page pass")
            self.assertEqual(sum(kind == "global" for kind, _numbers in events), 1)
            self.assertEqual(partial["_jp25PhotographyPlan"]["visualBible"], self.photography_plan()["visualBible"])
            self.assertEqual(len(partial["_jp25PhotographyPlan"]["pages"]), 25)
            self.assertEqual(partial["_creativePassStats"]["companyPromptPages"], 24)
            self.assertEqual(partial["_creativePassStats"]["photographyPlanPages"], 25)
            self.assertEqual(partial["_creativePassStats"]["photographyPlanSource"], "model")
            self.assertNotIn("10", partial["pageVisualEnhancements"])
            cached_successes = deepcopy(partial["pageVisualEnhancements"])

            events.clear()
            first_round = False
            completed, _latency = backend.refine_ai_director_page_visuals(
                self.refinement_settings(), all_pages, partial,
                backend.AI_IMAGE_LANDING_SUITE_KEY, "JP", {},
            )

        self.assertEqual(events, [("pages", (10,))], "A cached photography plan and successful pages must not be regenerated")
        self.assertEqual(completed["_jp25PhotographyPlan"], partial["_jp25PhotographyPlan"])
        self.assertTrue(completed["_creativePassStats"]["companyPromptComplete"])
        self.assertEqual(completed["_creativePassStats"]["photographyPlanPages"], 25)
        self.assertEqual(completed["_creativePassStats"]["photographyPlanSource"], "cache")
        for key, enhancement in cached_successes.items():
            self.assertEqual(completed["pageVisualEnhancements"][key], enhancement)

    def test_existing_shared_plan_is_available_when_resuming_a_single_missing_page(self) -> None:
        cached = self.analysis()
        cached["pageVisualEnhancements"] = {
            str(number): self.remote_enhancement(number)
            for number in range(1, 26) if number != 15
        }
        captured = []

        def model_fixture(_settings, messages):
            captured.append(deepcopy(messages))
            self.assertNotIn("[JP25 GLOBAL PHOTOGRAPHY PLAN]", self.message_text(messages))
            locked = self.json_section(messages, "[Locked pages]")
            self.assertEqual([page["page"] for page in locked], [15])
            return json.dumps({"pages": [{"page": 15, "visualEnhancement": self.remote_enhancement(15)}]}), 5

        with patch.object(backend, "invoke_ai_director_chat", side_effect=model_fixture):
            completed, _latency = backend.refine_ai_director_page_visuals(
                self.refinement_settings(), self.pages(), cached,
                backend.AI_IMAGE_LANDING_SUITE_KEY, "JP", {},
            )

        self.assertEqual(len(captured), 1)
        message_text = self.message_text(captured[0])
        for number in range(1, 26):
            self.assertIn(f"GLOBAL_ROUTE_{number:02d}", message_text)
        self.assertIn("BIBLE_LIGHT_MARKER", message_text)
        self.assertEqual(
            self.json_section(captured[0], "[Locked pages]")[0]["narrativeStage"],
            backend.ai_image_company_narrative_stage(15, 25),
        )
        self.assertTrue(completed["_creativePassStats"]["companyPromptComplete"])
        self.assertEqual(completed["_creativePassStats"]["photographyPlanSource"], "cache")

    def test_online_geometry_survives_source_lock_serialization_and_final_prompt_compilation(self) -> None:
        cases = (
            (
                "generic-source",
                "[Product] Multifunction kitchen opener.",
                "卖点：\n1. 轻量手持：握持轻巧方便使用。",
            ),
            (
                "fashion-source-and-authority",
                "[Product] 日系宽松大摆吊带连衣裙。",
                "以下是我的卖点及需求：\n1. 【宽松裙摆】裙摆宽松便于日常活动。\n\n"
                "权威背书\n1. 日本語背書テーマ（提供済み根拠）(【来源背书】用户提供的原始说明。)",
            ),
        )
        for case, product_prompt, brief in cases:
            with self.subTest(case=case):
                base_pages = backend.build_ai_image_suite_plan(
                    product_prompt, brief, suite_key=backend.AI_IMAGE_LANDING_SUITE_KEY, count=25,
                )
                original_pages = deepcopy(base_pages)
                plan = self.photography_plan()
                for route in plan["pages"]:
                    number = route["page"]
                    route.update({
                        "scene": f"SCENE_P{number:02d}: a specific quiet Japanese room zone",
                        "action": f"ACTION_P{number:02d}: one reference-correct product interaction",
                        "camera": f"CAMERA_P{number:02d}: 85mm low diagonal viewpoint",
                        "lighting": f"LIGHT_P{number:02d}: warm side light with soft shadow",
                        "layout": f"LAYOUT_P{number:02d}: product at right, small headline below left",
                    })
                page_visuals = {}
                for route in plan["pages"]:
                    number = route["page"]
                    layers = self.remote_enhancement(number)["companyPromptLayers"]
                    layers["visualNarrative"] = f"{route['scene']}; {route['action']}; exact product identity"
                    layers["layoutAndCopy"] = f"{route['layout']}; keep the approved Japanese copy"
                    page_visuals[str(number)] = {"companyPromptLayers": layers}
                analysis = {
                    **self.analysis(with_plan=False),
                    "_jp25PhotographyPlan": plan,
                    "pageVisualEnhancements": page_visuals,
                    "inspirationBlueprint": {
                        "camera": "STALE_INSPIRATION_CAMERA",
                        "lighting": "STALE_INSPIRATION_LIGHT",
                        "spatialPlan": "STALE_INSPIRATION_LAYOUT",
                    },
                }
                planned = backend.jp25_creative.apply_photography_plan(base_pages, plan)
                enhanced = backend.apply_ai_director_visual_enhancements(planned, analysis)
                locked = backend.lock_ai_image_cod_source_point_coverage(
                    enhanced, product_prompt, brief, backend.AI_IMAGE_LANDING_SUITE_KEY,
                )
                roundtripped = backend.normalize_ai_image_suite_plan(json.loads(json.dumps(locked)), 25)
                self.assertEqual(len(roundtripped), 25)
                prompts, compiled = backend.build_ai_image_suite_prompts(
                    product_prompt, brief, backend.AI_IMAGE_SUITE_SIZE,
                    suite_key=backend.AI_IMAGE_LANDING_SUITE_KEY,
                    plan=roundtripped, suite_count=25,
                )
                self.assertEqual(base_pages, original_pages, "The online geometry pipeline mutated the input source plan")
                self.assertEqual(len(prompts), 25)
                for stage, pages in (
                    ("global-plan", planned), ("per-page-enhancement", enhanced),
                    ("source-lock", locked), ("serialization", roundtripped), ("compiler", compiled),
                ):
                    for page, route, original in zip(pages, plan["pages"], original_pages):
                        with self.subTest(case=case, stage=stage, page=page["page"]):
                            self.assertEqual(page["photographyPlanSource"], "remote")
                            self.assertEqual(page["scene"], route["scene"])
                            self.assertEqual(page["pose"], route["action"])
                            self.assertEqual(page["composition"], route["layout"])
                            self.assertEqual(page["visualEnhancement"]["camera"], route["camera"])
                            self.assertEqual(page["visualEnhancement"]["lighting"], route["lighting"])
                            if stage != "global-plan":
                                self.assertEqual(page["visualEnhancement"]["companyPromptLayers"], page_visuals[str(page["page"])]["companyPromptLayers"])
                            if int(original.get("sourcePointIndex") or 0) > 0:
                                self.assertEqual(page["sourcePointVerbatim"], original["sourcePointVerbatim"])
                                self.assertEqual(page["focusTitle"], original["focusTitle"])
                for number, prompt in enumerate(prompts, 1):
                    with self.subTest(case=case, compiled_prompt=number):
                        self.assertIn("[ONLINE PHOTOGRAPHY AUTHORITY]", prompt)
                        self.assertIn("[AI planned layout — content validation only]", prompt)
                        self.assertNotIn("[Company module construction contract — compact]", prompt)
                        self.assertIn(f"SCENE_P{number:02d}", prompt)
                        self.assertIn(f"ACTION_P{number:02d}", prompt)
                        self.assertIn(f"CAMERA_P{number:02d}", prompt)
                        self.assertIn(f"LIGHT_P{number:02d}", prompt)
                        self.assertIn(f"LAYOUT_P{number:02d}", prompt)

    def test_non_jp_refinement_never_starts_global_photography_even_with_flag_enabled(self) -> None:
        calls = []

        def model_fixture(_settings, messages):
            message_text = self.message_text(messages)
            self.assertNotIn("[JP25 GLOBAL PHOTOGRAPHY PLAN]", message_text)
            self.assertNotIn("BIBLE_MOOD_MARKER", message_text)
            self.assertIn(self.LEGACY_WORD_LIMIT, message_text)
            locked = self.json_section(messages, "[Locked pages]")
            calls.append([page["page"] for page in locked])
            return json.dumps({
                "pages": [{"page": page["page"], "visualEnhancement": self.remote_enhancement(page["page"])} for page in locked],
            }), 5

        with patch.object(backend, "invoke_ai_director_chat", side_effect=model_fixture):
            backend.refine_ai_director_page_visuals(
                self.refinement_settings(), self.pages()[:3], self.analysis(),
                backend.AI_IMAGE_AMAZON_APLUS_SUITE_KEY, "JP", {},
            )
        self.assertEqual(calls, [[1, 2, 3]])

    def test_online_true_side_tungsten_prompt_has_no_legacy_view_or_daylight_override(self) -> None:
        product_prompt = "[Product] Exact khaki linen jacket apparel product."
        brief = "卖点：\n1. 自然织理：细密织理带有自然的亚麻外观。"
        base_pages = backend.build_ai_image_suite_plan(
            product_prompt, brief, suite_key=backend.AI_IMAGE_LANDING_SUITE_KEY, count=25,
        )
        plan = self.photography_plan()
        target_page = 2
        plan["pages"][target_page - 1].update({"camera": "true-side", "lighting": "3000K tungsten"})
        page_visuals = {
            str(number): {"companyPromptLayers": self.remote_enhancement(number)["companyPromptLayers"]}
            for number in range(1, 26)
        }
        page_visuals[str(target_page)]["companyPromptLayers"]["visualNarrative"] = (
            "One true-side view under 3000K tungsten, preserving the exact reference-confirmed jacket"
        )
        enhanced = backend.apply_ai_director_visual_enhancements(base_pages, {
            **self.analysis(with_plan=False),
            "_jp25PhotographyPlan": plan,
            "pageVisualEnhancements": page_visuals,
        })
        online_page = enhanced[target_page - 1]
        topology = backend.ai_image_jp_company_apparel_topology_lock(online_page)
        optics = backend.ai_image_jp_fine_fabric_optics_instruction(online_page)
        self.assertNotIn("Keep the reference-confirmed front or front-three-quarter construction readable", topology)
        self.assertNotIn("Directional daylight keeps", optics)
        self.assertIn("only reference-supported", topology)
        self.assertIn("an unknown surface is not invented", topology)

        prompts, compiled = backend.build_ai_image_suite_prompts(
            product_prompt, brief, backend.AI_IMAGE_SUITE_SIZE,
            suite_key=backend.AI_IMAGE_LANDING_SUITE_KEY,
            plan=enhanced, suite_count=25,
        )
        self.assertEqual(compiled[target_page - 1]["visualEnhancement"]["camera"], "true-side")
        self.assertEqual(compiled[target_page - 1]["visualEnhancement"]["lighting"], "3000K tungsten")
        final_prompt = prompts[target_page - 1]
        self.assertIn("true-side", final_prompt)
        self.assertIn("3000K tungsten", final_prompt)
        self.assertIn("only reference-supported", final_prompt)
        self.assertIn("an unknown surface is not invented", final_prompt)
        self.assertNotIn("Directional daylight keeps", final_prompt)
        self.assertNotIn("Keep the reference-confirmed front or front-three-quarter construction readable", final_prompt)

    def test_non_online_topology_and_material_helpers_keep_their_existing_rules(self) -> None:
        page = self.pages()[1]
        page["visualEnhancement"].update({"camera": "true-side", "lighting": "3000K tungsten"})
        self.assertNotIn("photographyPlanSource", page)
        topology = backend.ai_image_jp_company_apparel_topology_lock(page)
        optics = backend.ai_image_jp_fine_fabric_optics_instruction(page)
        self.assertIn("Keep the reference-confirmed front or front-three-quarter construction readable", topology)
        self.assertIn("Directional daylight keeps", optics)


if __name__ == "__main__":
    unittest.main()
