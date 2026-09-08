"""Pure source inventory selection for COD country main images."""

from copy import deepcopy
import json
import unittest

from sku_board.cod_main_density import (
    build_supporting_points,
    normalize_supporting_points,
    support_instruction,
)


class CodMainDensityTests(unittest.TestCase):
    @staticmethod
    def point(source_id, title, description="", source_type="user", **extra):
        return {
            "sourceId": source_id,
            "title": title,
            "description": description,
            "sourceType": source_type,
            **extra,
        }

    def test_normalizer_keeps_five_records_and_original_source_text(self):
        records = [self.point(f"user:{index}", f"原文标题{index}，25cm", f"原文说明{index}\n完整条件。") for index in range(1, 7)]
        records[0]["extra"] = "not part of the contract"
        original = deepcopy(records)
        normalized = normalize_supporting_points(records)
        self.assertEqual(len(normalized), 5)
        self.assertEqual(normalized[0]["title"], records[0]["title"])
        self.assertEqual(normalized[0]["description"], records[0]["description"])
        self.assertEqual(set(normalized[0]), {"sourceId", "title", "description", "label", "sourceType"})
        self.assertEqual(records, original)
        self.assertEqual(normalized[0]["label"], records[0]["title"])

    def test_normalizer_rejects_missing_provenance_and_invalid_types(self):
        valid = self.point("user:1", "防滑握柄")
        for field, invalid in (("sourceId", ""), ("sourceId", 1), ("title", " "), ("title", 123), ("sourceType", "planner"), ("sourceType", "model_guess"), ("sourceType", []), ("sourceType", None)):
            with self.subTest(field=field, value=invalid):
                candidate = {**valid, field: invalid}
                with self.assertRaises(ValueError):
                    normalize_supporting_points([candidate])
        self.assertEqual(normalize_supporting_points(None), [])
        self.assertEqual(normalize_supporting_points([]), [])

    def test_normalizer_deduplicates_by_id_and_normalized_title(self):
        records = [
            self.point("user:1", "防滑握柄"),
            self.point("user:1", "another title with the same identity"),
            self.point("image:1:fact:1", "防滑 握柄。", source_type="image_observation"),
            self.point("user:2", "便于收纳"),
        ]
        result = normalize_supporting_points(records)
        self.assertEqual([point["sourceId"] for point in result], ["user:1", "user:2"])

    def test_labels_keep_important_quantities_even_at_the_end_of_long_titles(self):
        title = "这是用户给出的完整结构说明" * 6 + "，承重25kg"
        records = [self.point("user:1", title), self.point("user:2", "承重25kg", label="承重250kg")]
        normalized = normalize_supporting_points(records)
        self.assertIn("25kg", normalized[0]["label"])
        self.assertNotIn("250kg", normalized[1]["label"])
        self.assertIn("25kg", normalized[1]["label"])
        self.assertEqual(normalized[0]["title"], title)

    def test_primary_and_planning_placeholders_do_not_use_support_slots(self):
        primary = self.point("user:core", "稳定省力开盖", "握持更省力")
        candidates = [
            primary,
            self.point("user:duplicate", "稳定省力开盖。"),
            self.point("user:near", "稳定省力开盖更轻松"),
            self.point("planner:1", "核心使用效果"),
            self.point("planner:2", "省力或易用方式"),
            self.point("planner:3", "当前产品最核心"),
            self.point("planner:4", "遵循用户的画面要求"),
            self.point("user:grip", "防滑触点", "让握持稳定省力"),
            self.point("image:1:fact:1", "贴合手掌的曲面", "握持区域的可见曲线", "image_observation"),
        ]
        result = build_supporting_points(primary, candidates, 1)
        self.assertEqual({point["sourceId"] for point in result}, {"user:grip", "image:1:fact:1"})
        self.assertEqual(len(result), 2)

    def test_lexically_related_evidence_ranks_ahead_of_unrelated_source_points(self):
        primary = self.point("core", "防滑握持", "防滑接触帮助握持稳定")
        candidates = [
            self.point("user:color", "多种颜色", "可选外观配色"),
            self.point("user:storage", "收纳方便", "可以挂起存放"),
            self.point("user:contact", "防滑接触纹路", "帮助握持稳定"),
            self.point("user:curve", "握柄曲面", "改善握持接触"),
        ]
        result = build_supporting_points(primary, candidates, 1, limit=2)
        self.assertEqual({point["sourceId"] for point in result}, {"user:contact", "user:curve"})

    def test_same_relevance_candidates_rotate_but_remain_deterministic(self):
        primary = self.point("core", "便于日常使用", "日常使用")
        titles = ("整齐缝线", "织理清楚", "边缘包边", "完整拉链", "准确标签", "平整接缝", "金属扣件")
        candidates = [self.point(f"image:1:{index}", title, "原图中可见", "image_observation") for index, title in enumerate(titles)]
        first = build_supporting_points(primary, candidates, 1, limit=3)
        second = build_supporting_points(primary, candidates, 2, limit=3)
        self.assertEqual(first, build_supporting_points(primary, candidates, 1, limit=3))
        self.assertNotEqual([point["sourceId"] for point in first], [point["sourceId"] for point in second])
        self.assertTrue({point["sourceId"] for point in first + second} <= {point["sourceId"] for point in candidates})

    def test_near_duplicate_titles_do_not_pad_the_inventory(self):
        candidates = [
            self.point("user:1", "防滑握柄表面"),
            self.point("user:2", "防滑握柄表面设计"),
            self.point("user:3", "贴合手掌曲面"),
        ]
        selected = build_supporting_points(self.point("core", "日常开盖"), candidates, 1)
        self.assertEqual(len(selected), 2)
        self.assertIn("user:3", {point["sourceId"] for point in selected})

    def test_distinct_source_numbers_and_units_are_not_deduplicated_as_paraphrases(self):
        candidates = [
            self.point("user:1", "适用直径5cm"),
            self.point("user:2", "适用直径8cm"),
            self.point("user:3", "适用厚度5mm"),
            self.point("user:4", "适用厚度5cm"),
        ]
        selected = build_supporting_points(self.point("core", "适用范围"), candidates, 1)
        self.assertEqual(len(selected), 4)

    def test_limit_and_insufficient_inventory_never_create_filler(self):
        candidates = [self.point("user:1", "防滑纹路"), self.point("user:2", "曲面贴合")]
        primary = self.point("core", "省力开盖")
        original = deepcopy(candidates)
        self.assertEqual(len(build_supporting_points(primary, candidates, 1)), 2)
        self.assertEqual(len(build_supporting_points(primary, candidates, 1, limit=1)), 1)
        self.assertEqual(build_supporting_points(primary, [], 1), [])
        self.assertEqual(candidates, original)
        many = [self.point(f"user:{index}", f"规格{index}cm") for index in range(1, 9)]
        self.assertEqual(len(normalize_supporting_points(many, limit=20)), 5)

    def test_instruction_carries_complete_provenance_without_counting_the_primary(self):
        records = [self.point("user:1", "防滑接触", "完整原文说明\nFACT_TAIL"), self.point("image:2:fact:3", "曲面贴合", source_type="image_observation")]
        instruction = support_instruction(records)
        marker = "[COD MAIN SUPPORTING SOURCE DATA]\n"
        self.assertIn(marker, instruction)
        data = json.loads(instruction.split(marker, 1)[1])
        self.assertEqual(data["actualCount"], 2)
        self.assertEqual(len(data["points"]), 2)
        self.assertEqual(data["points"][0]["description"], records[0]["description"])
        self.assertIn("main headline is separate", instruction.lower())
        self.assertIn("approved inventory only", instruction.lower())
        self.assertIn("do not invent", instruction.lower())
        self.assertIn("FACT_TAIL", instruction)


if __name__ == "__main__":
    unittest.main()
