import unittest
from unittest.mock import Mock
from plan_preview import text_fields, enrich_plan


class PreviewTests(unittest.TestCase):
    def test_studio_markets_match_engine(self):
        import sys
        from pathlib import Path
        root = str(Path(__file__).parent.parent)
        if root not in sys.path:
            sys.path.insert(0, root)
        from sku_board import backend
        codes = ['KR','JP','US','GB','DE','HU','PL','ES','MX','FR','CZ','TW','HK','TH','VN','MY','SG','PH','ID']
        self.assertEqual(set(codes), set(backend.AI_IMAGE_COD_COUNTRY_PROFILES))
        for code in codes:
            self.assertEqual(backend.normalize_ai_image_cod_country(code), code)
            self.assertTrue(backend.ai_image_cod_country_profile(code)['visibleLanguage'])

    def test_new_modes_match_existing_engine_contracts(self):
        import sys
        from pathlib import Path
        root = str(Path(__file__).parent.parent)
        if root not in sys.path:
            sys.path.insert(0, root)
        from sku_board import backend
        for key, count, size in [('jp-landing-page-25', 25, '1500x2000'),
                                 ('cod-country-detail-12', 22, '750x1000')]:
            with self.subTest(key=key):
                self.assertEqual(backend.normalize_ai_image_suite_key(key), key)
                self.assertEqual(backend.ai_image_suite_config(key)['size'], size)
                self.assertEqual(backend.normalize_ai_image_suite_count(key, count), count)
                self.assertTrue(backend.ai_image_company_effect_suite(key))
                pages = backend.build_ai_image_suite_plan('A real ceramic cup', '卖点：圆润杯口', size,
                                                         suite_key=key, country='JP', count=count)
                self.assertEqual(len(pages), count)
        for count in (12, 16, 20, 22):
            self.assertEqual(backend.normalize_ai_image_suite_count('cod-country-detail-12', count), count)

    def test_compiler_routes_all_modes(self):
        for key, count, size in [('cod-country-landing-30', 14, '750x1000'),
                                 ('jp-landing-page-25', 25, '1500x2000'),
                                 ('cod-country-detail-12', 22, '750x1000')]:
            with self.subTest(key=key):
                engine = Mock()
                pages = [{'page': page} for page in range(1, count + 1)]
                engine.build_ai_image_suite_prompts.return_value = (['compiled'] * count, pages)
                engine.ai_image_company_prompt_status.return_value = {'ready': True}
                result = {'ok': True, 'companyPromptStatus': {'ready': True}, 'suiteKey': key,
                          'suiteCount': count, 'suitePages': pages, 'size': size, 'suiteCountry': 'JP'}
                out = enrich_plan(result, {'prompt': '原始卖点', 'suiteBrief': '原始卖点'}, engine)
                self.assertEqual(len(out['studioPromptPreview']), count)
                args = engine.build_ai_image_suite_prompts.call_args
                self.assertEqual(args.kwargs['suite_key'], key)
                self.assertEqual(args.kwargs['suite_count'], count)
                self.assertEqual(args.args[2], size)
                self.assertFalse(args.kwargs['has_style_anchor'])

    def test_real_engine_keeps_14_pages_and_legacy_37(self):
        import sys
        from pathlib import Path
        root=str(Path(__file__).parent.parent)
        if root not in sys.path:
            sys.path.insert(0,root)
        from sku_board import backend
        self.assertEqual(backend.normalize_ai_image_suite_count(backend.AI_IMAGE_COD_SUITE_KEY,14),14)
        self.assertEqual(backend.normalize_ai_image_suite_count(backend.AI_IMAGE_COD_SUITE_KEY,37),37)
        self.assertEqual(len(backend.build_ai_image_suite_plan('A real ceramic cup','卖点：圆润杯口',suite_key=backend.AI_IMAGE_COD_SUITE_KEY,country='JP',count=14)),14)

    def test_multipart_ignores_files(self):
        body=b'--boundary\r\nContent-Disposition: form-data; name="suiteBrief"\r\n\r\nexact source\r\n--boundary\r\nContent-Disposition: form-data; name="reference0"; filename="x.png"\r\n\r\nimage\r\n--boundary--\r\n'
        self.assertEqual(text_fields('multipart/form-data; boundary=boundary',body),{'suiteBrief':'exact source'})

    def test_partial_plan_does_not_compile(self):
        engine=Mock()
        result={'ok':True,'companyPromptStatus':{'ready':False}}
        self.assertIs(enrich_plan(result,{},engine),result)
        engine.build_ai_image_suite_prompts.assert_not_called()

    def test_compiler_gets_exact_source_and_no_bitmap(self):
        engine=Mock()
        engine.build_ai_image_suite_prompts.return_value=(['compiled'],[{'page':1}])
        engine.ai_image_company_prompt_status.return_value={'ready':True}
        result={'ok':True,'companyPromptStatus':{'ready':True},'suiteKey':'cod-country-landing-30','suiteCount':1,'suitePages':[{'page':1}]}
        out=enrich_plan(result,{'prompt':'source','suiteBrief':'unchanged source'},engine)
        self.assertTrue(out['studioCompiledReady'])
        self.assertEqual(out['studioPromptPreview'][0]['prompt'],'compiled')
        self.assertEqual(engine.build_ai_image_suite_prompts.call_args.args[1],'unchanged source')
        self.assertFalse(engine.build_ai_image_suite_prompts.call_args.kwargs['has_style_anchor'])
