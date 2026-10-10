"""Offline regressions: Chinese sources must not become literal German artwork."""
from contextlib import ExitStack
from copy import deepcopy
import unittest
from unittest.mock import patch

from sku_board import backend, cod_copy_locale


class CodCopyLocaleTests(unittest.TestCase):
    def setUp(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        for target in ('requests.sessions.Session.request', 'urllib.request.urlopen'):
            stack.enter_context(patch(target, side_effect=AssertionError('Unexpected network call')))
        self.director = stack.enter_context(patch.object(
            backend, 'invoke_ai_director_chat', side_effect=AssertionError('Unexpected AI call')))

    def page(self):
        return {
            'page': 15, 'country': 'DE', 'size': '750x1000',
            'headline': '拯救花园里的阴暗死角',
            'localizedSellingPointTitle': '拯救花园里的阴暗死角',
            'focusDescription': '完整来源描述：用于庭院阴凉角落。',
            'sourcePointVerbatim': '拯救花园里的阴暗死角：完整来源描述。',
            'copyLabels': ['方便种植', '庭院装饰', '25 cm', 'Für den Garten'],
            'visualEnhancement': {'companyPromptLayers': {
                field: ('Headline: 「拯救花园里的阴暗死角」' if field == 'layoutAndCopy'
                        else 'Specific product photography direction')
                for field in backend.AI_IMAGE_JP_COMPANY_PROMPT_LAYER_FIELDS
            }},
        }

    def compile(self, page=None, brief='庭院植物卖点原文。', **kwargs):
        return backend.ai_image_cod_company_remote_authored_execution_prompt(
            page or self.page(), 'Exact reference product', 24, brief, **kwargs)

    def test_chinese_title_is_source_not_approved_literal(self):
        page = self.page()
        before = deepcopy(page)
        prompt = self.compile(page)
        self.assertNotIn('Use this approved localized headline exactly: 「拯救', prompt)
        self.assertIn('INTERNAL COPY SOURCES TO LOCALIZE', prompt)
        self.assertIn('拯救花园里的阴暗死角', prompt)
        self.assertIn('Use one concise natural', prompt)
        self.assertIn('Approved short labels only: 25 cm / Für den Garten.', prompt)
        self.assertIn('方便种植', prompt)
        self.assertIn('庭院装饰', prompt)
        self.assertEqual(page, before)
        self.director.assert_not_called()

    def test_director_localized_headline_wins_over_stale_chinese(self):
        page = self.page()
        page['visualEnhancement']['localizedHeadline'] = 'Schönheit für schattige Gartenecken'
        prompt = self.compile(page)
        self.assertIn('Use this approved localized headline exactly: 「Schönheit für schattige Gartenecken」', prompt)

    def test_saved_country_and_detail_plans_recompile_without_ai(self):
        brief = '主卖点：\n1. 拯救花园里的阴暗死角：用于庭院阴凉角落。'
        for suite in (backend.AI_IMAGE_COD_SUITE_KEY, backend.AI_IMAGE_COD_DETAIL_SUITE_KEY):
            with self.subTest(suite=suite):
                pages = backend.build_ai_image_suite_plan(
                    '庭院植物', brief, '750x1000', suite_key=suite, country='DE', count=24)
                for page in pages:
                    page['visualEnhancement'] = deepcopy(self.page()['visualEnhancement'])
                    page['headline'] = self.page()['headline']
                    page['localizedSellingPointTitle'] = self.page()['headline']
                prompts, _ = backend.build_ai_image_suite_prompts(
                    '庭院植物', brief, '750x1000', suite_key=suite,
                    country='DE', suite_count=24, plan=pages)
                self.assertTrue(prompts)
                for prompt in prompts:
                    self.assertIn('[COD ARTWORK LANGUAGE BOUNDARY', prompt)
                    self.assertNotIn('Use this approved localized headline exactly: 「拯救', prompt)
        self.director.assert_not_called()

    def test_boundary_covers_layer_quotes_original_brief_and_master_reference(self):
        brief = '请原样使用中文标题与全部卖点。'
        prompt = self.compile(brief=brief, has_style_anchor=True)
        self.assertIn(brief, prompt)
        self.assertIn('seven layers or original brief does not approve', prompt)
        self.assertIn('Style/master reference text is not approved copy', prompt)
        self.assertGreater(prompt.index('[FINAL ARTWORK LANGUAGE]'), prompt.index(brief))

    def test_main_support_inventory_preserved(self):
        page = self.page()
        page['section'] = 'main'
        page['codMainRich'] = True
        page['codMainSupportingPoints'] = [
            {'sourceId': f'user:{i}', 'title': f'辅助卖点{i}',
             'description': f'完整条件{i}：25 cm', 'sourceType': 'user'}
            for i in range(1, 6)
        ]
        prompt = self.compile(page)
        for point in page['codMainSupportingPoints']:
            self.assertIn(point['title'], prompt)
            self.assertIn(point['description'], prompt)

    def test_script_filter_preserves_cjk_markets_and_numeric_labels(self):
        cases = [('DE', '中文标题', False), ('KR', '中文标题', False),
                 ('CN', '方便收纳', True), ('CN', '毎日の収納', False),
                 ('CN', 'Easy storage', False), ('CN', '수납', False),
                 ('TH', '中文标题', False), ('JP', '庭園の彩り', True),
                 ('TW', '庭園裝飾', True), ('HK', '庭園裝飾', True),
                 ('KR', '정원 장식', True), ('TH', 'สวนสวย', True)]
        for country, value, expected in cases:
            with self.subTest(country=country):
                self.assertEqual(cod_copy_locale.literal_copy(value, country), expected)
        for country in ('DE', 'KR', 'JP', 'TH'):
            self.assertTrue(cod_copy_locale.literal_copy('25 cm', country, numeric=True))

    def test_china_reaches_all_three_cod_generators_without_foreign_copy_fallback(self):
        brief = '主卖点：方便收纳、操作简单。'
        language = 'Simplified Chinese used in mainland China'
        self.assertEqual(backend.normalize_ai_image_cod_country('cn'), 'CN')
        for suite in (backend.AI_IMAGE_COD_SUITE_KEY, backend.AI_IMAGE_COD_DETAIL_SUITE_KEY):
            with self.subTest(suite=suite):
                prompts, pages = backend.build_ai_image_suite_prompts(
                    '家用收纳盒', brief, '750x1000', suite_key=suite, country='CN', suite_count=12)
                self.assertTrue(prompts)
                self.assertTrue(all(page['country'] == 'CN' for page in pages))
                self.assertTrue(all(page['countryLabel'] == '中国' for page in pages))
                self.assertTrue(all(language in prompt for prompt in prompts))
        hook = backend.compile_ai_image_cod_hook_text_prompt(
            {'suiteBrief': brief, 'suiteCountry': 'CN', 'codHookType': 'hook'}, '', '750x1000')
        self.assertIn('所有可见文案只能使用简体中文', hook)
        self.assertIn('Selected market=CN', hook)
        page = self.page()
        page['country'] = 'CN'
        prompt = self.compile(page)
        self.assertIn('Use this approved localized headline exactly: 「拯救花园里的阴暗死角」', prompt)
        self.assertIn(language, prompt)
        self.assertNotIn('Chinese or Japanese writing must not appear', prompt)
        self.director.assert_not_called()

    def test_no_text_policy_does_not_request_translation(self):
        prompt = self.compile(brief='不要任何文字')
        self.assertIn('No visible added text', prompt)
        self.assertNotIn('[COD ARTWORK LANGUAGE BOUNDARY', prompt)
        self.assertNotIn('[INTERNAL COPY SOURCES TO LOCALIZE', prompt)

    def test_restricted_copy_modes_do_not_add_source_labels(self):
        for mode in ('titleOnly', 'priceOnly'):
            with self.subTest(mode=mode), patch.object(backend, 'ai_image_cod_suite_copy_mode', return_value=mode):
                prompt = self.compile()
                self.assertNotIn('Approved short labels only:', prompt)
                if mode == 'titleOnly':
                    self.assertIn('"supportingLabelSources":[]', prompt)
                else:
                    self.assertNotIn('[INTERNAL COPY SOURCES TO LOCALIZE', prompt)
                self.assertIn('does not authorize extra text', prompt)


if __name__ == '__main__':
    unittest.main()
