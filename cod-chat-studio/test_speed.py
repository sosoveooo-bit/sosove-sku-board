import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sku_board import backend
import plan_preview
from test_director_budget import response


class CompileCacheTests(unittest.TestCase):
    def setUp(self):
        plan_preview._compiled.clear()

    def tearDown(self):
        plan_preview._compiled.clear()

    def test_exact_compile_reuse_and_no_shared_mutable_result(self):
        result={'ok':True,'companyPromptStatus':{'ready':True},'suiteKey':'cod-country-detail-12',
                'suiteCount':1,'suiteCountry':'TH','size':'750x1000','suitePages':[{'page':1}]}
        fields={'prompt':'完整产品描述','suiteBrief':'完整原文卖点'}
        with patch.object(backend,'build_ai_image_suite_prompts',return_value=(['compiled'],[{'page':1}])) as compile_call, \
             patch.object(backend,'ai_image_company_prompt_status',return_value={'ready':True}):
            first=plan_preview.enrich_plan(deepcopy(result),fields)
            self.assertFalse(first['studioCompileCacheHit'])
            first['studioPromptPreview'][0]['prompt']='changed by caller'
            second=plan_preview.enrich_plan(deepcopy(result),fields)
            self.assertTrue(second['studioCompileCacheHit'])
            self.assertEqual(second['studioPromptPreview'][0]['prompt'],'compiled')
            self.assertEqual(compile_call.call_count,1)
            plan_preview.enrich_plan(deepcopy(result),{**fields,'suiteBrief':'不同原文'})
            changed=deepcopy(result);changed['suitePages'][0]['headline']='新文案'
            plan_preview.enrich_plan(changed,fields)
            self.assertEqual(compile_call.call_count,3)

    def test_cache_bound(self):
        result={'ok':True,'companyPromptStatus':{'ready':True},'suiteKey':'cod-country-detail-12',
                'suiteCount':1,'suitePages':[{'page':1}]}
        with patch.object(backend,'build_ai_image_suite_prompts',return_value=(['compiled'],[{'page':1}])), \
             patch.object(backend,'ai_image_company_prompt_status',return_value={'ready':True}):
            for i in range(10):plan_preview.enrich_plan(deepcopy(result),{'suiteBrief':str(i)})
        self.assertEqual(len(plan_preview._compiled),8)


class WorkerDefaultsTests(unittest.TestCase):
    def test_default_three_and_congestion_two(self):
        import os
        for suite in (backend.AI_IMAGE_COD_SUITE_KEY,backend.AI_IMAGE_LANDING_SUITE_KEY):
            for congested,expected in ((False,3),(True,2)):
                with self.subTest(suite=suite,congested=congested), patch.dict(os.environ,{},clear=True), \
                     patch.object(backend,'build_ai_director_page_refinement_messages',side_effect=lambda pages,*a,**kw:pages), \
                     patch.object(backend,'invoke_ai_director_chat',side_effect=lambda settings,pages:response(pages)), \
                     patch.object(backend,'ai_image_cod_duplicate_company_prompt_pages',return_value={'duplicatePages':[],'duplicatePairs':[]}):
                    pages=[{'page':i} for i in range(1,10)]
                    out,_=backend.refine_ai_director_page_visuals({'model':'fixture','timeout':60},pages,
                        {'_creativePassStats':{'congestionDetected':congested}},suite,'JP',None)
                    self.assertEqual(out['_creativePassStats']['parallelWorkers'],expected)
                    self.assertTrue(out['_creativePassStats']['companyPromptComplete'])


if __name__=='__main__':unittest.main()
