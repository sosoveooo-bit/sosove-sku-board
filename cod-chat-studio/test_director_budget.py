import json
import os
import sys
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sku_board import backend


def response(pages):
    return json.dumps({'pages': [
        {'page': p['page'], 'visualEnhancement': {'shotConcept': f"Photograph {p['page']}",
          'companyPromptLayers': {key: f"Page {p['page']} complete {key}" for key in backend.AI_IMAGE_JP_COMPANY_PROMPT_LAYER_FIELDS}}}
        for p in pages]}), 100


class DirectorBudgetTests(unittest.TestCase):
    def test_expired_budget_does_not_claim_models_failed(self):
        settings={'model':'fixture-a','fallbackModels':['fixture-b'], 'timeout':60, '_absoluteDeadline':1}
        with patch.object(backend.time, 'monotonic', return_value=10), patch.object(backend,'invoke_ai_director_chat_once') as call:
            with self.assertRaises(backend.DirectorBudgetExhausted):
                backend.invoke_ai_director_chat(settings, [])
        call.assert_not_called()
        self.assertEqual(settings['_lastDirectorCall']['attempts'], [])
        self.assertTrue(settings['_lastDirectorCall']['budgetExhausted'])

    def setup_refinement(self, stack, clock):
        stack.enter_context(patch.dict(os.environ, {'AI_DIRECTOR_COD_REFINEMENT_BATCH_SIZE':'3',
            'AI_DIRECTOR_COD_REFINEMENT_WORKERS':'1', 'AI_DIRECTOR_COD_REFINEMENT_TOTAL_TIMEOUT':'120'}, clear=False))
        stack.enter_context(patch.object(backend.time,'monotonic',side_effect=lambda:clock[0]))
        stack.enter_context(patch.object(backend,'build_ai_director_page_refinement_messages',side_effect=lambda pages,*args,**kwargs:pages))
        stack.enter_context(patch.object(backend,'ai_image_cod_duplicate_company_prompt_pages',return_value={'duplicatePages':[],'duplicatePairs':[]}))

    def test_checkpoints_and_next_round_only_missing_pages(self):
        clock=[0]
        pages=[{'page':i,'country':'TH'} for i in range(1,10)]
        settings={'model':'fixture','timeout':60,'_directorCacheKey':'isolated-test'}
        calls=[]
        def invoke(settings,batch):
            calls.append([p['page'] for p in batch]);clock[0]+=50
            return response(batch)
        with ExitStack() as stack:
            self.setup_refinement(stack,clock)
            stack.enter_context(patch.object(backend,'invoke_ai_director_chat',side_effect=invoke))
            saved=stack.enter_context(patch.object(backend,'put_ai_director_cached_analysis'))
            first,_=backend.refine_ai_director_page_visuals(settings,pages,{},backend.AI_IMAGE_COD_SUITE_KEY,'TH',None)
            self.assertEqual(calls,[[1,2,3],[4,5,6]])
            self.assertEqual(first['_creativePassStats']['deferredPageNumbers'],[7,8,9])
            self.assertTrue(first['_creativePassStats']['budgetExhausted'])
            self.assertEqual(saved.call_count,2)
            self.assertEqual(len(saved.call_args.args[1]['pageVisualEnhancements']),6)
            clock[0]=0;calls.clear()
            second,_=backend.refine_ai_director_page_visuals(settings,pages,first,backend.AI_IMAGE_COD_SUITE_KEY,'TH',None)
            self.assertEqual(calls,[[7,8,9]])
            self.assertTrue(second['_creativePassStats']['companyPromptComplete'])
            self.assertFalse(second['_creativePassStats']['budgetExhausted'])

    def test_split_retries_do_not_starve_untouched_batches(self):
        clock=[0];pages=[{'page':i,'country':'TH'} for i in range(1,10)];calls=[]
        def invoke(settings,batch):
            ids=[p['page'] for p in batch];calls.append(ids)
            if ids==[1,2,3]: raise ValueError('HTTP 408 stream disconnected')
            return response(batch)
        with ExitStack() as stack:
            self.setup_refinement(stack,clock)
            stack.enter_context(patch.object(backend,'invoke_ai_director_chat',side_effect=invoke))
            result,_=backend.refine_ai_director_page_visuals({'model':'fixture','timeout':60},pages,{},backend.AI_IMAGE_COD_SUITE_KEY,'TH',None)
        self.assertEqual(calls[:3],[[1,2,3],[4,5,6],[7,8,9]])
        self.assertTrue(result['_creativePassStats']['companyPromptComplete'])
        self.assertIn('408',result['_creativePassStats']['requestErrors'][0]['message'])


if __name__=='__main__': unittest.main()
