from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch
from sku_board import backend as b, cod_rich_graphics as rich


class RichGraphicTests(unittest.TestCase):
    def test_example_types_are_content_driven(self):
        fixtures=[(1,'核心卖点','overview'),(2,'三个条件下的前后对比','comparison'),
                  (3,'多场景使用：阅读、日常活动、手机','scenes'),(4,'结构原理与实际连接','mechanism'),
                  (5,'材质纹理细节','material'),(6,'正确使用步骤','steps'),(7,'产品规格参数','parameters')]
        for number,source,kind in fixtures:
            with self.subTest(kind=kind):
                page={'page':number,'sourcePointVerbatim':source}
                self.assertEqual(rich.select(page),kind)
                modules=rich.modules(page)
                self.assertEqual(len(modules),4)
                self.assertEqual(len({m['id'] for m in modules}),4)
                self.assertEqual(sum(m['weight']=='DOMINANT' for m in modules),1)

    def test_other_suites_and_restricted_copy_unchanged(self):
        page={'page':3,'focusTitle':'多场景使用','country':'TH','textPolicy':'requested','codCopyPolicy':'requested'}
        for key in (b.AI_IMAGE_COD_DETAIL_SUITE_KEY,b.AI_IMAGE_LANDING_SUITE_KEY,b.AI_IMAGE_RAKUTEN_SUITE_KEY,b.AI_IMAGE_AMAZON_APLUS_SUITE_KEY):
            result=b.apply_ai_image_company_module_plans([page],key)[0]
            self.assertFalse(any(m['id'].startswith('RICH_') for m in result.get('companyModulePlan',[])))

    def test_rich_brief_overrides_recipe_minimal_but_not_user_minimal(self):
        page={'page':15,'role':'lifestyle macro','contentDensity':'minimal'}
        self.assertEqual(b.ai_image_page_content_density(page,b.AI_IMAGE_COD_SUITE_KEY,'画面丰富，冲击力强'),'structured')
        self.assertEqual(b.ai_image_page_content_density(page,b.AI_IMAGE_COD_DETAIL_SUITE_KEY,'画面丰富，冲击力强'),'minimal')
        self.assertNotEqual(b.ai_image_page_content_density(page,b.AI_IMAGE_COD_SUITE_KEY,'无字，画面丰富'),'structured')
        for restriction in ({'textPolicy':'none'},{'codCopyPolicy':'titleOnly'},{'codCopyPolicy':'priceOnly'}, {'contentDensity':'minimal'}):
            result=b.apply_ai_image_company_module_plans([{**page,**restriction}],b.AI_IMAGE_COD_SUITE_KEY)[0]
            self.assertFalse(any(m['id'].startswith('RICH_') for m in result.get('companyModulePlan',[])))

    def test_rich_plan_reaches_director_budget_and_final_prompt(self):
        key=b.AI_IMAGE_COD_SUITE_KEY
        page={'page':3,'focusTitle':'多场景使用','focus':'多场景使用','country':'TH','textPolicy':'requested',
              'sourcePointVerbatim':'三种使用场景','headline':'ใช้งานได้หลากหลาย'}
        original=deepcopy(page)
        result=b.apply_ai_image_company_module_plans([page],key)[0]
        self.assertEqual(page,original)
        self.assertEqual(result['contentDensity'],'structured')
        budget=b.ai_image_page_content_budget_instruction(result,key,'画面丰富')
        self.assertIn('RICH COD GRAPHIC TYPE',budget)
        self.assertNotIn('at most one',budget)
        messages=b.build_ai_director_page_refinement_messages([result],{},key,'TH')
        self.assertIn('Three to six',messages[1]['content'])
        self.assertIn('not a one-photo limit',messages[1]['content'])
        result['visualEnhancement']={'companyPromptLayers':{f:'Complete fixture '+f for f in b.AI_IMAGE_JP_COMPANY_PROMPT_LAYER_FIELDS}}
        prompt=b.ai_image_cod_company_remote_authored_execution_prompt(result,'Exact product',30,'画面丰富',suite_key=key,country='TH')
        self.assertIn('RICH COD GRAPHIC TYPE',prompt)
        self.assertIn('selected market',prompt.lower())

    def test_real_thirty_page_source_round_trip_keeps_rich_regions(self):
        brief=(Path(__file__).parent/'fixtures/cod_unnumbered_skincare.txt').read_text(encoding='utf-8')
        key=b.AI_IMAGE_COD_SUITE_KEY
        pages=b.build_ai_image_suite_plan('skincare cream stick',brief,'750x1000',suite_key=key,country='TH',count=30)
        pages=b.apply_ai_image_company_module_plans(pages,key)
        for page in pages:
            page['visualEnhancement']={'localizedHeadline':'ดูแลผิว','companyPromptLayers':{f:f'Page {page["page"]} fixture {f}' for f in b.AI_IMAGE_JP_COMPANY_PROMPT_LAYER_FIELDS}}
        with patch.object(b,'ai_image_cod_duplicate_company_prompt_pages',return_value={'duplicatePages':[],'duplicatePairs':[]}):
            prompts,result=b.build_ai_image_suite_prompts('skincare cream stick',brief,'750x1000',suite_key=key,country='TH',suite_count=30,plan=pages)
        self.assertEqual(len(prompts),30)
        b.require_ai_image_cod_source_coverage(result,'skincare cream stick',brief,key)
        self.assertTrue(all('RICH COD GRAPHIC TYPE' in prompt for prompt in prompts))
        self.assertGreaterEqual(len({rich.select(page) for page in result}),5)


if __name__=='__main__':unittest.main()
