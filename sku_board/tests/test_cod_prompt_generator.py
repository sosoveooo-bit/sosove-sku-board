from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from sku_board import backend


def model_payload(product: str, count: int = 37, main_count: int = 15) -> dict:
    pages = []
    for page in range(1, count + 1):
        if page == 1:
            archetype = "产品首屏"
        elif page == 2:
            archetype = "四宫格痛点"
        elif page == 7:
            archetype = "公平对比"
        elif page == count:
            archetype = "产品信息"
        else:
            archetype = f"{product}卖点证明{page:02d}"
        pages.append(
            {
                "page": page,
                "section": "main" if page <= main_count else "detail",
                "title": f"{product}页面{page:02d}",
                "role": archetype,
                "pageArchetype": archetype,
                "objective": f"证明{product}的第{page}个当前商品购买理由",
                "focus": f"只表现{product}当前卖点{page}",
                "sellingPoint": f"{product}卖点{page}",
                "evidence": f"{product}真实产品证据{page}",
                "scene": f"日本本土且符合{product}真实用途的场景{page}",
                "pose": f"自然使用{product}的动作{page}",
                "composition": f"750x1000满幅构图{page}，无留白",
                "headline": f"商品訴求{page}",
                "visualTreatment": f"独立镜头路线{page}",
                "impactTreatment": f"夸张但真实的COD包装{page}",
                "contentDensity": "structured" if page in {2, 7, count} else "focused",
                "modelPrompt": f"当前唯一商品：{product}。第{page}页只展示本页卖点、真实场景、独立镜头、日文短文案、静态满幅画面。",
            }
        )
    return {
        "masterPrompt": f"当前唯一商品：{product}。这是只为{product}从零生成的日本COD落地页总控Prompt。",
        "creativeRationale": f"围绕{product}真实使用价值建立专属说服路径。",
        "pages": pages,
    }


class CodPromptGeneratorTests(unittest.TestCase):
    def generate(self, product: str, points: list[str]) -> dict:
        fields = {
            "promptGeneratorInput": json.dumps(
                {
                    "product": product,
                    "market": "JP",
                    "intensity": "cod",
                    "sellingPoints": points,
                    "promotions": {},
                    "allowPromo": True,
                    "allowMedical": True,
                    "style": "明亮、高密度、日本本土化",
                    "avoid": "不要动画、乱码或串品",
                    "referenceMap": "第一张为当前主商品",
                },
                ensure_ascii=False,
            ),
            "mainCount": "15",
            "detailCount": "22",
        }
        result = {
            "suiteKey": backend.AI_IMAGE_COD_SUITE_KEY,
            "suiteCount": 37,
            "size": "750x1000",
            "suiteCountry": "JP",
            "director": {
                "source": "model",
                "productSummary": product,
                "productVisualDNA": {"observableColors": ["#eeeeee"]},
            },
        }

        def fake_invoke(settings, messages):
            settings["_lastDirectorCall"] = {
                "requestedModel": "gpt-5.6-sol",
                "model": "gpt-5.6-sol",
                "fallbackUsed": False,
                "attempts": [],
            }
            return json.dumps(model_payload(product), ensure_ascii=False), 18

        settings = {
            "enabled": True,
            "baseUrl": "https://director.invalid/v1",
            "apiKey": "test-key",
            "model": "gpt-5.6-sol",
            "fallbackModels": [],
            "timeout": 60,
        }
        with patch.object(backend, "load_ai_director_settings", return_value=settings), patch.object(
            backend, "invoke_ai_director_chat", side_effect=fake_invoke
        ):
            return backend.generate_cod_prompt_blueprint_with_director(fields, result)

    def test_switching_products_rewrites_all_prompts_and_fingerprint(self) -> None:
        watch = self.generate("Watch4 Pro钢带手表", ["血糖趋势", "心率追踪"])
        shrimp = self.generate("冷冻香辣烤虾", ["整只大虾", "空气炸锅即食"])

        self.assertNotEqual(watch["fingerprint"], shrimp["fingerprint"])
        self.assertIn("Watch4 Pro钢带手表", watch["masterPrompt"])
        self.assertIn("冷冻香辣烤虾", shrimp["masterPrompt"])
        self.assertNotIn("Watch4", shrimp["masterPrompt"])
        self.assertEqual(len(shrimp["pages"]), 37)
        self.assertTrue(all("冷冻香辣烤虾" in page["modelPrompt"] for page in shrimp["pages"]))
        self.assertTrue(any(page["pageArchetype"] == "四宫格痛点" for page in shrimp["pages"][:15]))
        self.assertTrue(any(page["pageArchetype"] == "公平对比" for page in shrimp["pages"]))
        self.assertEqual(shrimp["pages"][-1]["pageArchetype"], "产品信息")

    def test_suite_plan_round_trip_keeps_model_authored_prompt(self) -> None:
        blueprint = self.generate("便携榨汁杯", ["随行鲜榨", "USB充电"])
        normalized = backend.normalize_ai_image_suite_plan(blueprint["pages"], 37)

        self.assertEqual(len(normalized), 37)
        self.assertIn("便携榨汁杯", normalized[0]["modelPrompt"])


if __name__ == "__main__":
    unittest.main()
