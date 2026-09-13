import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sku_board import backend, market_localization


class MarketLockTests(unittest.TestCase):
    def test_every_market_has_localized_direction(self):
        self.assertEqual(set(market_localization.SCENES), set(backend.AI_IMAGE_COD_COUNTRY_PROFILES))
        for code in market_localization.SCENES:
            with self.subTest(code=code):
                first = backend.ai_image_cod_market_localization(code, 1)
                second = backend.ai_image_cod_market_localization(code, 2)
                self.assertTrue(first['casting'])
                self.assertNotEqual(first['scene'], second['scene'])
                self.assertIn('Selected market=' + code, first['instruction'])
                self.assertIn(market_localization.COPY[code], first['instruction'])
                self.assertIn('preserve explicitly supplied person identity', first['instruction'])

    def test_remote_authored_prompt_receives_lock_before_layers(self):
        layers = {key: 'Fixture authored scene and product proof' for key in backend.AI_IMAGE_JP_COMPANY_PROMPT_LAYER_FIELDS}
        for key in (backend.AI_IMAGE_COD_SUITE_KEY, backend.AI_IMAGE_COD_DETAIL_SUITE_KEY):
            for code in market_localization.SCENES:
                with self.subTest(suite=key, code=code):
                    page = {'page': 1, 'country': code, 'focusTitle': 'Fixture benefit',
                            'focusDescription': 'Exact material and use method',
                            'visualEnhancement': {'companyPromptLayers': layers}}
                    prompt = backend.ai_image_cod_company_remote_authored_execution_prompt(
                        page, 'Reference product unchanged', 22, 'Reference styling from Korea', suite_key=key, country=code)
                    self.assertIn('Selected market=' + code, prompt)
                    self.assertLess(prompt.index('Selected market='), prompt.index('Fixture authored'))

    def test_other_country_plan_is_rejected(self):
        for key, count in ((backend.AI_IMAGE_COD_SUITE_KEY, 8), (backend.AI_IMAGE_COD_DETAIL_SUITE_KEY, 12)):
            plan = backend.build_ai_image_suite_plan('A jar opener', '主卖点：轻松开盖', suite_key=key, country='KR', count=count)
            with self.assertRaisesRegex(ValueError, '市场与所选国家不一致'):
                backend.build_ai_image_suite_prompts('A jar opener', '主卖点：轻松开盖', suite_key=key,
                                                     country='TH', suite_count=count, plan=plan)

    def test_analysis_and_per_page_director_share_selected_market(self):
        for key, count in ((backend.AI_IMAGE_COD_SUITE_KEY, 8), (backend.AI_IMAGE_COD_DETAIL_SUITE_KEY, 12)):
            for code in market_localization.SCENES:
                with self.subTest(suite=key, code=code):
                    pages = backend.build_ai_image_suite_plan('A jar opener', '主卖点：轻松开盖', suite_key=key, country=code, count=count)
                    analysis = backend.build_ai_director_messages(pages, 'A jar opener', '参考韩国排版，保留产品卖点', key, code, None, False, reference_image_count=0)
                    refinement = backend.build_ai_director_page_refinement_messages(pages[:2], {}, key, code)
                    self.assertIn('Selected market=' + code, analysis[1]['content'])
                    self.assertIn('Selected market=' + code, refinement[1]['content'])

    def test_old_same_market_metadata_gets_refreshed(self):
        key = backend.AI_IMAGE_COD_SUITE_KEY
        plan = backend.build_ai_image_suite_plan('A jar opener', '主卖点：轻松开盖', suite_key=key, country='TH', count=8)
        for page in plan:
            page['marketLocalization'] = 'obsolete wrong direction'
        prompts, _ = backend.build_ai_image_suite_prompts('A jar opener', '主卖点：轻松开盖', suite_key=key,
                                                         country='TH', suite_count=8, plan=plan)
        self.assertTrue(all('Selected market=TH' in prompt for prompt in prompts))
        self.assertTrue(all('obsolete wrong direction' not in prompt for prompt in prompts))


if __name__ == '__main__':
    unittest.main()
