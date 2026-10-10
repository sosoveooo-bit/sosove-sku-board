import unittest

from sku_board.cod_prompt_brief import localized_direction, planning_form


class CodPromptBriefTests(unittest.TestCase):
    def test_adapts_local_staging_to_selected_market(self):
        self.assertEqual(localized_direction("德国本土家庭厨房场景", "JP"), "日本本土家庭厨房场景")
        self.assertEqual(localized_direction("德国原产，德国本土包装", "JP"), "德国原产，德国本土包装")

    def test_does_not_mutate_form_or_change_product_origin(self):
        form = {"market": "JP", "style": "德国本土电商高密度排版", "points": ["德国原产"]}
        planned = planning_form(form)
        self.assertEqual(form["style"], "德国本土电商高密度排版")
        self.assertEqual(planned["style"], "日本本土电商高密度排版")
        self.assertEqual(planned["points"], ["德国原产"])


if __name__ == "__main__":
    unittest.main()
