from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch
from sku_board import backend as b, cod_source_input as source

BRIEF=(Path(__file__).parent/'fixtures/cod_unnumbered_skincare.txt').read_text(encoding='utf-8')
KEY=b.AI_IMAGE_COD_SUITE_KEY


class UnnumberedSourcesTests(unittest.TestCase):
    def test_real_ten_points_keep_original_paragraphs_and_split(self):
        pairs=source.unnumbered_points(BRIEF)
        self.assertEqual(len(pairs),10)
        self.assertEqual(pairs[0]['title'],'提拉紧致，改善面部松垮')
        self.assertEqual(pairs[9]['title'],'搭配性强，轻松融入原有护肤流程')
        for pair in pairs:self.assertIn(pair['sourceVerbatim'],BRIEF)
        self.assertNotIn('依据',pairs[-1]['description'])
        main,detail=b.extract_ai_image_cod_kr_points('',BRIEF,preserve_all_source=True,suite_key=KEY)
        supplied=[p for p in main+detail if p['sourceProvided']]
        self.assertEqual([p['title'] for p in supplied],[p['title'] for p in pairs])
        self.assertEqual(len(supplied),10)
        self.assertEqual(b.ai_image_cod_country_section_counts(BRIEF,30),(10,20))

    def test_detail_and_legacy_parser_not_changed(self):
        a=b.extract_ai_image_cod_kr_points('',BRIEF,preserve_all_source=True)
        d=b.extract_ai_image_cod_kr_points('',BRIEF,preserve_all_source=True,suite_key=b.AI_IMAGE_COD_DETAIL_SUITE_KEY)
        self.assertEqual(a,d)
        self.assertEqual(sum(p.get('sourceProvided') is True for p in a[0]+a[1]),0)

    def test_layout_requirements_and_one_off_prose_are_not_facts(self):
        self.assertEqual(source.unnumbered_points('配色统一\n请使用浅蓝色背景，整体丰富。\n尺寸要求\n输出三比四竖图。'),[])
        self.assertEqual(source.unnumbered_points('单个短句\n这是一段普通介绍。'),[])
        numbered='主卖点：\n1. 防滑\n2. 耐用'
        self.assertEqual(b.extract_ai_image_cod_kr_points('',numbered,preserve_all_source=True),
            b.extract_ai_image_cod_kr_points('',numbered,preserve_all_source=True,suite_key=KEY))

    def test_actual_page_plan_binds_all_sources_before_and_after_analysis(self):
        pages=b.build_ai_image_suite_plan('Blue skincare cream stick',BRIEF,'750x1000',suite_key=KEY,country='TH',count=30)
        self.assertEqual(len(pages),30)
        self.assertEqual(sum(p['section']=='主图' for p in pages),10)
        self.assertEqual({int(p.get('sourcePointIndex',0)) for p in pages if p.get('sourcePointIndex')},set(range(1,11)))
        b.require_ai_image_cod_source_coverage(pages,'Blue skincare cream stick',BRIEF,KEY)
        coverage=b.ai_image_cod_source_point_coverage(pages,'Blue skincare cream stick',BRIEF,KEY)
        self.assertEqual((coverage['total'],coverage['assigned']),(10,10))
        analysis={'mainSellingPoints':[{'title':'ดูแลผิวกระชับ','description':'ดูแลผิว','sourcePointIndex':1,'copyLabels':['中文内部标签','ผิวกระชับ']}], 'secondarySellingPoints':[]}
        after=b.apply_ai_director_selling_points_to_pages(pages,analysis,'Blue skincare cream stick',BRIEF,KEY)
        b.require_ai_image_cod_source_coverage(after,'Blue skincare cream stick',BRIEF,KEY)
        for page in after:
            if page.get('headline'):self.assertTrue(source.localized_copy(page['headline'],'TH'))
        old=deepcopy(pages)
        for page in old:page.pop('sourcePointIndex',None)
        with self.assertRaisesRegex(ValueError,'原始段落卖点'):
            b.require_ai_image_cod_source_coverage(old,'Blue skincare cream stick',BRIEF,KEY)

    def test_thai_copy_replaces_internal_chinese_placeholder(self):
        layers={field:'Fixture '+field for field in b.AI_IMAGE_JP_COMPANY_PROMPT_LAYER_FIELDS}
        layers['layoutAndCopy']='Place “ผิวดูกระชับ” at upper-left; product 65%.'
        page={'page':1,'country':'TH','headline':'泰国本土化 · 核心使用效果','focusTitle':'提拉紧致',
              'copyLabels':['中文内部标签','ผิวกระชับ'],'visualEnhancement':{'companyPromptLayers':layers}}
        self.assertEqual(source.headline(page,'TH'),'ผิวดูกระชับ')
        prompt=b.ai_image_cod_company_remote_authored_execution_prompt(page,'skincare cream stick',30,BRIEF,suite_key=KEY,country='TH')
        exact=next(line for line in prompt.splitlines() if line.startswith('[EXACT VISIBLE COPY'))
        self.assertIn('ผิวดูกระชับ',exact);self.assertNotIn('泰国本土化',exact);self.assertNotIn('中文内部标签',exact)
        self.assertIn(BRIEF,prompt)

    def test_30_page_compile_preserves_sources_and_native_titles(self):
        pages=b.build_ai_image_suite_plan('skincare cream stick',BRIEF,'750x1000',suite_key=KEY,country='TH',count=30)
        for page in pages:
            page['visualEnhancement']={'localizedHeadline':'ดูแลผิวกระชับ','companyPromptLayers':{
                field:f'Unique page {page["page"]} '+field for field in b.AI_IMAGE_JP_COMPANY_PROMPT_LAYER_FIELDS}}
        with patch.object(b,'ai_image_cod_duplicate_company_prompt_pages',return_value={'duplicatePages':[],'duplicatePairs':[]}):
            prompts,result=b.build_ai_image_suite_prompts('skincare cream stick',BRIEF,'750x1000',suite_key=KEY,country='TH',suite_count=30,plan=pages)
        self.assertEqual(len(prompts),30)
        b.require_ai_image_cod_source_coverage(result,'skincare cream stick',BRIEF,KEY)
        for prompt in prompts:
            self.assertIn(BRIEF,prompt)
            exact=next(line for line in prompt.splitlines() if line.startswith('[EXACT VISIBLE COPY'))
            self.assertNotIn('本土化',exact)
        for point in source.unnumbered_points(BRIEF):
            self.assertTrue(any(point['title'] in p.split('[ORIGINAL USER REQUIREMENTS')[0] for p in prompts))


if __name__=='__main__':unittest.main()
