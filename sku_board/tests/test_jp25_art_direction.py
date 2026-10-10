"""Regression tests for the real Japanese source loss and default render path.

All inputs and director responses are fixtures; no model/image calls or user data.
"""
from contextlib import ExitStack
import json
import unittest
from unittest.mock import patch

from sku_board import backend, jp25_art_direction, jp25_creative, jp25_source, jp25_workbench
from sku_board.tests import test_jp25_prompt_contract_regressions as fixtures


PRODUCT = "[Product] ダークインディゴのショートジャケットとハイウエストパンツ、スカーフ付き。"
BRIEF = """主なポイント
1. ショートジャケット＋ハイウエストパンツで、セットアップが脚の比例を引き伸ばす。スカーフ付き。
ジャケット丈がウエストラインの上で止まり、ハイウエストパンツが自然につながることで上半身の比率を抑えます。ペタンコ靴と合わせても、スタイルアップして見える一枚。
2. フレアワイドパンツで、腰・脚・ふくらはぎのラインを美しく。
ヒップから太ももにかけて程よいゆとりを持たせ、裾に向かってほんのり広がるデザイン。
3. ステッチ切り替えが、立体的で着痩せする輪郭を描く。
肩・胸元・脚に向かって伸びるコントラストステッチが、はっきりとした縦横の構造を形成。
サブポイント
·カーゴフラップポケットとファスナーのディテールが、上半身に立体感をプラス。
·ダークインディゴは視覚的に引き締まり、丈夫で飽きのこない色味。
·ジャケットはワンピースやスカートと、パンツはニットやシャツと合わせても。
·ショート丈ジャケットが腰・お腹まわりをカバーし、身長を圧迫しません。
·セットアップでデイリーなお出かけ、旅行、カジュアル通勤に。気負わず、でも様になる。
图片要求为：日本地区，日语，比例3:4。尺寸1500*2000。配色日式灰冷白色调。
严格注意模特脸部特征发型发色要一致。GLOBAL_USER_LOCK
"""


class Jp25ArtDirectionTests(unittest.TestCase):
    def setUp(self):
        stack = self.enterContext(ExitStack())
        for target in ("requests.sessions.Session.request", "urllib.request.urlopen"):
            stack.enter_context(patch(target, side_effect=AssertionError("No real network allowed")))
        for name in ("invoke_ai_director_chat", "get_ai_director_cached_analysis", "put_ai_director_cached_analysis"):
            stack.enter_context(patch.object(backend, name, side_effect=AssertionError("No model/cache I/O allowed")))

    def pages(self):
        return backend.build_ai_image_suite_plan(PRODUCT, BRIEF, suite_key=backend.AI_IMAGE_LANDING_SUITE_KEY, count=25)

    def test_japanese_paragraphs_remain_three_main_and_five_detail_points(self):
        points = backend.extract_ai_image_jp_source_points(PRODUCT, BRIEF)
        self.assertEqual(len(points), 8)
        self.assertEqual([p["kind"] for p in points], ["main"] * 3 + ["detail"] * 5)
        self.assertIn("で、セットアップ", points[0]["title"])
        self.assertIn("ペタンコ靴と合わせても", points[0]["description"])
        self.assertIn(points[0]["description"], points[0]["sourceVerbatim"])
        self.assertIn("と、パンツはニット", points[5]["title"])
        self.assertNotIn("GLOBAL_USER_LOCK", json.dumps(points))
        self.assertEqual(jp25_source.structured_points("卖点：\n1. 纯棉面料：保持舒适。"), [])
        self.assertTrue(backend.extract_ai_image_jp_source_points("", "卖点：\n1. 纯棉面料：保持舒适。"))

    def test_full_source_binding_and_default_craft_reach_every_final_prompt(self):
        points = backend.extract_ai_image_jp_source_points(PRODUCT, BRIEF)
        pages = self.pages()
        bound = {p["sourcePointIndex"]: p for p in pages if p.get("sourcePointIndex", 0) > 0}
        self.assertEqual(set(bound), set(range(1, 9)))
        for index, point in enumerate(points, 1):
            self.assertEqual(bound[index]["focusTitle"], point["title"])
            self.assertIn(point["sourceVerbatim"], bound[index]["sourcePointVerbatim"])
        authored = fixtures.Jp25PromptContractRegressionTests.attach_remote_layers(pages)
        prompts, compiled = backend.build_ai_image_suite_prompts(
            PRODUCT, BRIEF, backend.AI_IMAGE_SUITE_SIZE,
            suite_key=backend.AI_IMAGE_LANDING_SUITE_KEY, plan=authored, suite_count=25)
        self.assertEqual(len(prompts), 25)
        for page, prompt in zip(compiled, prompts):
            self.assertIn("[JP25 EDITORIAL FINISH " + jp25_art_direction.VERSION, prompt)
            self.assertIn("GLOBAL_USER_LOCK", prompt)
            self.assertIn("[COMPANY AI-AUTHORED SEVEN-LAYER PROMPT", prompt)
            self.assertIn("half-page slogan", prompt)
            self.assertIn("white haze", prompt)
            if page.get("sourcePointIndex", 0) > 0:
                self.assertIn(backend.clean_ai_image_suite_text(page["sourcePointVerbatim"], 2600), prompt)
        # Empty workbench inputs must no longer be necessary to activate the defaults.
        self.assertIn("JP25 EDITORIAL FINISH", jp25_workbench.apply_prompt(prompts[0], compiled[0], {}))

    def test_shared_craft_survives_plan_serialization_and_page_refinement(self):
        pages = self.pages()
        bible = {"mood": "Quiet catalogue", "lighting": "Soft key with negative fill", "palette": "Cool white and indigo",
                 "typography": "CUSTOM_TYPE_MARKER: precise Japanese serif", "layoutSystem": "CUSTOM_LAYOUT_MARKER: compact aligned title",
                 "materialTreatment": "CUSTOM_MATERIAL_MARKER: fine denim relief"}
        plan = {"visualBible": bible, "pages": [{"page": p["page"], "scene": "Reference-supported setting",
            "action": "Show the named source feature", "camera": "Close view at product height", "lighting": "Soft side key",
            "layout": "Product first, short aligned headline", "evidenceTreatment": "Inspect exact construction"} for p in pages]}
        applied = jp25_creative.apply_photography_plan(pages, plan)
        normalized = backend.normalize_ai_image_suite_plan(applied, suite_count=25)
        self.assertEqual(normalized[0]["jp25DesignVersion"], jp25_art_direction.VERSION)
        for marker in ("CUSTOM_TYPE_MARKER", "CUSTOM_LAYOUT_MARKER", "CUSTOM_MATERIAL_MARKER"):
            self.assertIn(marker, normalized[0]["jp25ArtDirection"])
        messages = backend.build_ai_director_page_refinement_messages(
            normalized[:3], {"_jp25PhotographyPlan": plan}, backend.AI_IMAGE_LANDING_SUITE_KEY, "JP", {})
        text = json.dumps(messages, ensure_ascii=False)
        self.assertIn("JP25 EDITORIAL CRAFT", text)
        self.assertIn("CUSTOM_TYPE_MARKER", text)
        final = backend.ai_image_jp_company_remote_authored_execution_prompt(
            fixtures.Jp25PromptContractRegressionTests.attach_remote_layers(normalized)[0], PRODUCT, 25, BRIEF, is_fashion_product=True)
        self.assertIn("CUSTOM_TYPE_MARKER", final)
        planner = json.dumps(jp25_creative.build_photography_plan_messages(pages, {}))
        self.assertIn("MAIN 1-10", planner)
        self.assertIn("DETAIL 11-25", planner)


if __name__ == "__main__":
    unittest.main()
