import unittest
from copy import deepcopy
from sku_board import backend, cod_campaign_art as art


class CampaignArtTests(unittest.TestCase):
    def test_source_specific_routes_and_variation(self):
        points=['提拉紧致，改善面部松垮','焕亮匀肤','淡化细纹干纹','胶原蛋白生成','修护弹性',
                '多效合一精简','清爽亲肤质地','早晚双用','温和配方熟龄肌友好','搭配原有护肤流程']
        pages=[{'page':i+1,'sourcePointVerbatim':point,'scene':'固定韩国桌面模板'} for i,point in enumerate(points)]
        before=deepcopy(pages);routes=art.routes(pages)
        self.assertEqual([r['family'] for r in routes],['contour','tone','lines','mechanism','mechanism','simplification','texture','routine','audience','procedure'])
        self.assertNotEqual(routes[3]['layoutSuggestion'],routes[4]['layoutSuggestion'])
        self.assertEqual(pages,before)
        self.assertNotIn('韩国桌面',str(routes))

    def test_unknown_product_does_not_receive_skincare_recipe(self):
        result=art.routes([{'page':1,'sourcePointVerbatim':'厨房拧盖器省力开盖'}])[0]
        self.assertEqual(result['productCategory'],'kitchen')
        self.assertEqual(result['family'],'handling')
        self.assertNotIn('skin',result['evidence'])

    def test_only_country_suite_enabled(self):
        for key in (backend.AI_IMAGE_COD_DETAIL_SUITE_KEY,backend.AI_IMAGE_LANDING_SUITE_KEY,
                    backend.AI_IMAGE_AMAZON_APLUS_SUITE_KEY,backend.AI_IMAGE_RAKUTEN_SUITE_KEY):
            self.assertEqual(art.instruction([{'page':1}],key),'')

    def test_categories_use_distinct_product_evidence(self):
        examples=[('连衣裙','弹力面料','apparel','texture','garment'),
                  ('厨房拧盖器','省力开盖','kitchen','handling','grip'),
                  ('护肤精华','提拉紧致','beauty','contour','applicator'),
                  ('蓝牙耳机','充电续航','electronics','function','ports'),
                  ('家居收纳盒','容量收纳','household','capacity','room'),
                  ('户外帐篷','耐用防水','outdoor','durability','outdoor'),
                  ('宠物梳子','使用步骤','pet','procedure','pet'),
                  ('婴儿奶瓶','材质','baby','texture','caregiver'),
                  ('护腰按摩器','正确操作','wellness','procedure','ergonomic'),
                  ('饰品项链','产品信息','accessory','information','clasp'),
                  ('茶叶','包装清单','food','information','serving')]
        for product,point,category,family,word in examples:
            with self.subTest(product=product):
                page={'page':1,'sourcePointVerbatim':point}
                result=art.routes([page],product)[0]
                self.assertEqual(result['productCategory'],category);self.assertEqual(result['family'],family)
                prompt=art.instruction([page],art.KEY,product)
                self.assertIn(word,prompt)
                if category!='beauty':self.assertNotIn('face-contour close-up',prompt)

    def test_ambiguous_product_is_not_forced_into_a_category(self):
        self.assertEqual(art.category([],'宠物衣服和护肤面霜')[0],'mixed')
        self.assertEqual(art.category([],'无明确资料的商品')[0],'generic')
        result=art.routes([{'page':1,'focusTitle':'弹性轮廓'}],'未知商品')[0]
        self.assertEqual(result['family'],'texture');self.assertNotIn('skin',result['evidence'])

    def test_vision_summary_precedes_reference_style_mentions(self):
        page={'page':1,'focusTitle':'弹力面料','scene':'皮肤护理广告'}
        result=art.routes([page],'参考护肤精华海报',{'productSummary':'Exact relaxed-fit dress with woven fabric'})[0]
        self.assertEqual(result['productCategory'],'apparel')
        self.assertEqual(result['family'],'texture')

    def test_batch_partition_does_not_reset_layout_positions(self):
        pages=[{'page':i,'focusTitle':'弹力面料'} for i in range(1,10)]
        whole=art.routes(pages,'连衣裙')
        parts=art.routes(pages[3:6],'连衣裙')
        self.assertEqual([r['layoutSuggestion'] for r in parts],[r['layoutSuggestion'] for r in whole[3:6]])

    def test_full_chain_uses_vision_category_without_new_model_call(self):
        key=backend.AI_IMAGE_COD_SUITE_KEY
        pages=backend.build_ai_image_suite_plan('Exact dress','卖点：弹力面料','750x1000',suite_key=key,country='TH',count=8)
        request=backend.build_ai_director_page_refinement_messages(pages[:3],{'productSummary':'Exact dress'},key,'TH')
        self.assertIn('Category suggestion=apparel',request[1]['content'])
        self.assertNotIn('face-contour close-up',request[1]['content'])
        page=deepcopy(pages[0]);page['productTruthSummary']='Exact dress'
        page['visualEnhancement']={'companyPromptLayers':{field:'Complete fixture '+field for field in backend.AI_IMAGE_JP_COMPANY_PROMPT_LAYER_FIELDS}}
        prompt=backend.ai_image_cod_company_remote_authored_execution_prompt(page,'Exact dress',8,'卖点：弹力面料',suite_key=key,country='TH')
        self.assertIn('Category suggestion=apparel',prompt)

    def test_online_analysis_refinement_and_compiler_receive_direction(self):
        key=backend.AI_IMAGE_COD_SUITE_KEY
        pages=backend.build_ai_image_suite_plan('Blue skincare applicator','卖点：提拉紧致','750x1000',suite_key=key,country='TH',count=8)
        analysis=backend.build_ai_director_messages(pages,'Blue skincare applicator','卖点：提拉紧致',key,'TH',None,False,reference_image_count=0)
        refinement=backend.build_ai_director_page_refinement_messages(pages[:3],{'_codCampaignArt':art.routes(pages)},key,'TH')
        for messages in (analysis,refinement):self.assertIn(art.VERSION,messages[1]['content'])
        page=deepcopy(pages[1]);page['visualEnhancement']={'companyPromptLayers':{field:'Complete fixture '+field for field in backend.AI_IMAGE_JP_COMPANY_PROMPT_LAYER_FIELDS}}
        prompt=backend.ai_image_cod_company_remote_authored_execution_prompt(page,'Exact product',8,'卖点：提拉紧致',suite_key=key,country='TH')
        self.assertIn(art.VERSION,prompt);self.assertIn('Selected market=TH',prompt)
        other=backend.ai_image_cod_company_remote_authored_execution_prompt(page,'Exact product',12,'卖点：提拉紧致',suite_key=backend.AI_IMAGE_COD_DETAIL_SUITE_KEY,country='TH')
        self.assertNotIn(art.VERSION,other)

    def test_reference_claims_are_not_imported(self):
        text=art.instruction([{'page':1,'focusTitle':'清爽质地'}],art.KEY)
        for claim in ('97.8%','4.9/5','80%','Celsiora','3 days'):
            self.assertNotIn(claim,text)
        self.assertIn('no-text requirements override',text)
        self.assertIn('Never invent or copy doctor credentials',text)


if __name__=='__main__':unittest.main()
