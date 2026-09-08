import unittest

from sku_board import backend


class CodHookBackendContractTests(unittest.TestCase):
    def test_explicit_no_text_overrides_submitted_policy_and_promotion_type(self):
        for brief in ("Don't add any text", "Don’t include text", "Remove any lettering", "Omit the headline", "无字图片"):
            with self.subTest(brief=brief):
                policy = backend.ai_image_cod_hook_text_policy(
                    {"textPolicy": "requested", "codHookType": "promotion"}, brief,
                )
                self.assertEqual(policy, "none")

    def test_no_reference_requirement_does_not_change_hook_text_policy(self):
        cases = (
            ("Copy the exact product from the reference", "hook", "none"),
            ("Write short Japanese ad copy", "effect", "requested"),
            ("活动折扣15%", "discount", "requested"),
        )
        for brief, hook_type, expected in cases:
            with self.subTest(brief=brief):
                payload = {"suiteBrief": brief, "codHookType": hook_type, "suiteCountry": "JP"}
                self.assertEqual(backend.ai_image_cod_hook_text_policy(payload, brief), expected)
                policy = backend.ai_image_cod_hook_policy_instruction(payload, brief)
                text_prompt = backend.compile_ai_image_cod_hook_text_prompt(payload, brief, "750x1000")
                self.assertIn(policy, text_prompt)
                self.assertIn(f"textPolicy={expected}", policy)

    def test_textfree_comparison_keeps_exactly_two_panels(self):
        payload = {"suiteBrief": "无字，展示同条件前后对比", "codHookType": "comparison", "suiteCountry": "JP"}
        prompt = backend.compile_ai_image_cod_hook_text_prompt(payload, payload["suiteBrief"], "750x1000")
        self.assertIn("textPolicy=none", prompt)
        self.assertIn("requested two-panel comparison", prompt)
        self.assertNotIn("不要拼图、宫格、分屏", prompt)
        self.assertNotIn("one dominant product/result in one continuous", prompt)
