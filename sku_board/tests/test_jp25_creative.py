"""Pure JP25 photography-plan contracts: no runtime config, storage or model I/O."""

from copy import deepcopy
import json
import unittest

from sku_board.jp25_creative import (
    apply_photography_plan,
    build_photography_plan_messages,
    normalize_photography_plan,
    suite_manifest,
)


class Jp25CreativeTests(unittest.TestCase):
    def pages(self, count=25):
        return [
            {
                "page": page,
                "sourcePointIndex": page,
                "focus": f"原文卖点{page}：保留单位与条件",
                "focusTitle": f"原文卖点{page}",
                "focusDescription": f"原文说明{page}",
                "sourcePointVerbatim": f"【原文卖点{page}】\n完整说明{page}，含数值25cm。",
                "localizedSellingPointTitle": f"こだわり{page}",
                "headline": f"こだわり{page}",
                "copyLabels": [f"ラベル{page}"],
                "textPolicy": "requested",
                "scene": "OLD_LOCAL_SCENE",
                "pose": "OLD_LOCAL_POSE",
                "composition": "OLD_LOCAL_COMPOSITION",
                "role": "OLD_LOCAL_STANDING_ROLE",
                "hasHuman": True,
                "productTruthSummary": "Exact reference garment",
                "primaryVariantReferenceIndex": 2,
                "referenceBindings": [{"index": 2, "role": "product"}],
                "companyModulePlan": [{"id": "photo"}, {"id": "copy"}],
                "visualEnhancement": {
                    "shotConcept": "OLD_LOCAL_SHOT",
                    "modulePlan": "Existing photo and copy modules only",
                    "materialRendering": "Exact supplied weave",
                    "companyPromptLayers": {"taskAnchor": f"EXISTING_SEVEN_LAYER_{page}"},
                },
            }
            for page in range(1, count + 1)
        ]

    def payload(self, count=25):
        return {
            "visualBible": {
                "mood": "Calm confident Japanese editorial photography",
                "lighting": "Soft directional daylight with coherent white balance",
                "palette": "#F4F0E8 background, #39404A text, #B98B68 accent",
            },
            "pages": [
                {
                    "page": page,
                    "scene": f"ORIGINAL_SCENE_{page:02d}",
                    "action": f"ORIGINAL_ACTION_{page:02d}",
                    "camera": f"ORIGINAL_CAMERA_{page:02d}",
                    "lighting": f"ORIGINAL_LIGHT_{page:02d}",
                    "layout": f"ORIGINAL_LAYOUT_{page:02d}: photograph 75%, copy 25%",
                    "evidenceTreatment": f"ORIGINAL_PROOF_{page:02d}",
                }
                for page in range(1, count + 1)
            ],
        }

    def test_messages_freeze_complete_source_and_copy_but_omit_old_local_photography(self):
        pages = self.pages()
        full_requirement = "明确要求：在办公室站立展示。" + "完整用户要求，" * 1000 + "GLOBAL_TAIL_MARKER"
        for page in pages:
            page["promptGlobalConstraints"] = full_requirement
        analysis = {
            "productSummary": "Exact linen-look jacket",
            "productVisualDNA": {"shapeAnchors": ["Exact lapel", "Two pockets"]},
            "referenceAnalysis": {"product": "Observed garment", "layout": "REFERENCE_LAYOUT_MARKER"},
            "referenceBreakdown": [{"index": 1, "role": "person", "useAs": "identity-only"}],
            "globalRequirements": ["保持参考人物身份"],
            "photographyGlobalRequirements": "USER_EXPLICIT_CAMERA_AND_ACTION",
            "factAudit": {"visible": [{"claim": "Two pockets"}]},
        }
        before_pages, before_analysis = deepcopy(pages), deepcopy(analysis)
        messages = build_photography_plan_messages(pages, analysis)
        self.assertEqual([message["role"] for message in messages], ["system", "user"])
        self.assertTrue(messages[1]["content"].startswith("[JP25 GLOBAL PHOTOGRAPHY PLAN]\n"))
        context = json.loads(messages[1]["content"].split("\n", 1)[1])
        self.assertEqual(context["requestedPageNumbers"], list(range(1, 26)))
        self.assertEqual(len(context["pages"]), 25)
        for original, contract in zip(pages, context["pages"]):
            for key in ("page", "sourcePointIndex", "focus", "focusTitle", "focusDescription", "sourcePointVerbatim", "headline", "copyLabels"):
                self.assertEqual(contract[key], original[key])
        combined = "\n".join(message["content"] for message in messages)
        for marker in ("GLOBAL_TAIL_MARKER", "USER_EXPLICIT_CAMERA_AND_ACTION", "REFERENCE_LAYOUT_MARKER", "保持参考人物身份"):
            self.assertIn(marker, combined)
        for old_marker in ("OLD_LOCAL_SCENE", "OLD_LOCAL_POSE", "OLD_LOCAL_COMPOSITION", "OLD_LOCAL_SHOT", "OLD_LOCAL_STANDING_ROLE", "[Locked pages]"):
            self.assertNotIn(old_marker, combined)
        self.assertEqual(combined.count("GLOBAL_TAIL_MARKER"), 1)
        self.assertIn("Chinese", messages[0]["content"])
        self.assertIn("Japanese", messages[0]["content"])
        self.assertEqual(pages, before_pages)
        self.assertEqual(analysis, before_analysis)

    def test_global_context_uses_25_page_stages_even_for_a_page_subset(self):
        pages = self.pages()
        messages = build_photography_plan_messages(pages, {})
        context = json.loads(messages[1]["content"].split("\n", 1)[1])
        expected = ["problem-solution"] * 5 + ["benefit-deepening"] * 5 + ["localized-trust"] * 5 + ["proof-and-craft"] * 7 + ["commitment-close"] * 3
        self.assertEqual([page["narrativeStage"] for page in context["pages"]], expected)
        self.assertEqual([page["section"] for page in context["pages"]], ["main"] * 10 + ["detail"] * 15)
        self.assertIs(context["responseShape"]["pages"][0]["hasHuman"], False)
        for contract in context["pages"]:
            self.assertNotIn("hasHuman", contract)
            self.assertNotIn("role", contract)
        pages[14]["narrativeStage"] = "commitment-close"
        subset = build_photography_plan_messages([pages[14]], {})
        subset_context = json.loads(subset[1]["content"].split("\n", 1)[1])
        self.assertEqual(subset_context["pages"][0]["narrativeStage"], "localized-trust")

    def test_normalizer_orders_all_pages_and_drops_content_overrides(self):
        pages = self.pages()
        payload = self.payload()
        payload["pages"].reverse()
        payload["pages"][0].update({"focus": "MODEL_CHANGED_SOURCE", "sourcePointIndex": 999, "headline": "NEW_COPY", "modulePlan": "invented badge"})
        payload["visualBible"]["productIdentity"] = "MODEL_CHANGED_PRODUCT"
        payload["extra"] = "IGNORED"
        before = deepcopy(payload)
        plan = normalize_photography_plan(payload, pages)
        self.assertEqual(set(plan), {"visualBible", "pages"})
        self.assertEqual(set(plan["visualBible"]), {"mood", "lighting", "palette"})
        self.assertEqual([page["page"] for page in plan["pages"]], list(range(1, 26)))
        for page in plan["pages"]:
            self.assertEqual(set(page), {"page", "scene", "action", "camera", "lighting", "layout", "evidenceTreatment"})
        self.assertEqual(payload, before)

    def test_normalizer_rejects_missing_duplicate_or_unrequested_pages(self):
        for damage in ("missing", "duplicate", "foreign"):
            with self.subTest(damage=damage):
                payload = self.payload()
                if damage == "missing":
                    payload["pages"].pop()
                elif damage == "duplicate":
                    payload["pages"][-1]["page"] = 1
                else:
                    payload["pages"][-1]["page"] = 26
                with self.assertRaises(ValueError):
                    normalize_photography_plan(payload, self.pages())

    def test_normalizer_requires_all_six_nonempty_photography_strings(self):
        for field in ("scene", "action", "camera", "lighting", "layout", "evidenceTreatment"):
            for invalid in (None, "", "  \n ", [], 123):
                with self.subTest(field=field, invalid=invalid):
                    payload = self.payload()
                    payload["pages"][12][field] = invalid
                    with self.assertRaises(ValueError):
                        normalize_photography_plan(payload, self.pages())

    def test_normalizer_requires_a_complete_string_visual_bible(self):
        for field in ("mood", "lighting", "palette"):
            with self.subTest(field=field):
                payload = self.payload()
                payload["visualBible"].pop(field)
                with self.assertRaises(ValueError):
                    normalize_photography_plan(payload, self.pages())

    def test_invalid_requested_or_returned_page_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            normalize_photography_plan(self.payload(), [])
        requested = self.pages()
        requested[1]["page"] = 1
        with self.assertRaises(ValueError):
            normalize_photography_plan(self.payload(), requested)
        for invalid in (True, 1.5, 0, -1, "not-a-page"):
            with self.subTest(page=invalid):
                payload = self.payload()
                payload["pages"][0]["page"] = invalid
                with self.assertRaises(ValueError):
                    normalize_photography_plan(payload, self.pages())

    def test_numeric_string_page_ids_are_normalized_without_merging_duplicates(self):
        payload = self.payload()
        payload["pages"][0]["page"] = " 1 "
        normalized = normalize_photography_plan(payload, self.pages())
        self.assertEqual(normalized["pages"][0]["page"], 1)
        payload["pages"][1]["page"] = "1"
        with self.assertRaises(ValueError):
            normalize_photography_plan(payload, self.pages())

    def test_apply_updates_only_photography_and_deep_copies_frozen_fields(self):
        pages = self.pages()
        plan = normalize_photography_plan(self.payload(), pages)
        before_pages, before_plan = deepcopy(pages), deepcopy(plan)
        result = apply_photography_plan(pages, plan)
        for original, creative, updated in zip(pages, plan["pages"], result):
            self.assertEqual(updated["scene"], creative["scene"])
            self.assertEqual(updated["pose"], creative["action"])
            self.assertEqual(updated["composition"], creative["layout"])
            visual = updated["visualEnhancement"]
            for field, source in (("shotConcept", "scene"), ("actionDirection", "action"), ("camera", "camera"), ("lighting", "lighting"), ("spatialPlan", "layout"), ("composition", "layout"), ("evidenceDirection", "evidenceTreatment")):
                self.assertEqual(visual[field], creative[source])
            self.assertEqual(updated["photographyPlanSource"], "remote")
            for field in ("sourcePointIndex", "focus", "focusTitle", "focusDescription", "sourcePointVerbatim", "headline", "localizedSellingPointTitle", "copyLabels", "referenceBindings", "hasHuman", "primaryVariantReferenceIndex", "productTruthSummary", "companyModulePlan"):
                self.assertEqual(updated[field], original[field])
            for field in ("companyPromptLayers", "modulePlan", "materialRendering"):
                self.assertEqual(visual[field], original["visualEnhancement"][field])
        result[0]["visualEnhancement"]["companyPromptLayers"]["taskAnchor"] = "changed result"
        result[0]["copyLabels"].append("changed result")
        result[0]["referenceBindings"][0]["role"] = "changed result"
        self.assertEqual(pages, before_pages)
        self.assertEqual(plan, before_plan)

    def test_apply_rejects_incomplete_plans_instead_of_leaving_local_pages(self):
        payload = self.payload()
        payload["pages"].pop(4)
        with self.assertRaises(ValueError):
            apply_photography_plan(self.pages(), payload)

    def test_optional_human_presence_preserves_false_through_normalize_apply_and_manifest(self):
        for has_human in (False, True):
            with self.subTest(hasHuman=has_human):
                pages = self.pages()
                pages[2]["hasHuman"] = not has_human
                payload = self.payload()
                payload["pages"][2]["hasHuman"] = has_human
                plan = normalize_photography_plan(payload, pages)
                self.assertIs(plan["pages"][2]["hasHuman"], has_human)
                applied = apply_photography_plan(pages, plan)
                self.assertIs(applied[2]["hasHuman"], has_human)
                self.assertIs(applied[0]["hasHuman"], pages[0]["hasHuman"])
                self.assertIs(pages[2]["hasHuman"], not has_human)
                decoded = json.loads(suite_manifest(plan))
                self.assertIs(decoded["pages"][2]["hasHuman"], has_human)
                self.assertNotIn("hasHuman", decoded["pages"][0])

    def test_explicit_human_presence_requires_boolean_not_truthy_coercion(self):
        for invalid in (0, 1, "false", "true", None, []):
            with self.subTest(hasHuman=invalid):
                payload = self.payload()
                payload["pages"][0]["hasHuman"] = invalid
                with self.assertRaises(ValueError):
                    normalize_photography_plan(payload, self.pages())

    def test_manifest_keeps_the_whole_suite_without_padding_or_unknown_fields(self):
        payload = self.payload()
        payload["pages"][0]["focus"] = "UNTRUSTED_OVERRIDE"
        manifest = suite_manifest(payload)
        decoded = json.loads(manifest)
        self.assertEqual(len(decoded["pages"]), 25)
        self.assertEqual(decoded["visualBible"], payload["visualBible"])
        self.assertIn("ORIGINAL_SCENE_01", manifest)
        self.assertIn("ORIGINAL_PROOF_25", manifest)
        self.assertNotIn("UNTRUSTED_OVERRIDE", manifest)
        self.assertNotIn("\n", manifest)
        self.assertNotIn('":[ ', manifest)


if __name__ == "__main__":
    unittest.main()
