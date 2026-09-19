import unittest
from unittest.mock import patch
from sku_board.tests import test_visual_agent_pipeline as fixture
from sku_board.visual_agents.scheduling import required_window, progress_key
from sku_board import backend as engine


class SchedulingTests(unittest.TestCase):
    def test_window_uses_history_and_fits_fresh_budget(self):
        self.assertGreaterEqual(required_window('prompts', [], 240),75)
        self.assertGreater(required_window('prompts', [{'stage':'prompts','status':'complete','latencyMs':100000}],240),100)
        self.assertLess(required_window('planning', [], 90),90)

    def test_progress_ignores_status_and_failure_logs(self):
        self.assertEqual(progress_key({'prompts':{'1':'done'}}),progress_key({'prompts':{'1':'done'},'error':'timeout','runs':[1],'updatedAt':1}))
        self.assertNotEqual(progress_key({'strategy':{'positioning':'new'}}),progress_key({}))


class ResumeTests(unittest.TestCase):
    setUp=fixture.PipelineTests.setUp
    run_plan=fixture.PipelineTests.run_plan

    def test_24_pages_finish_across_windows_without_repeating_stages(self):
        now=[0.0]
        launches=[]
        def delayed(settings,messages):
            result=self.transport(settings,messages)
            stage=self.transport.calls[-1][0]
            remaining=settings['_absoluteDeadline']-now[0]
            launches.append((stage,remaining))
            now[0]+={'product':50,'strategy':40,'direction':50,'planning':110,'prompts':45}[stage]
            return result
        with patch('sku_board.visual_agents.pipeline.time.monotonic',side_effect=lambda:now[0]),patch.object(engine,'invoke_ai_director_chat',side_effect=delayed):
            for round_number in range(6):
                result=self.run_plan(suiteCount=24)
                if result['companyPromptStatus']['ready']:
                    break
                self.assertTrue(result['continuation']['autoContinue'])
                self.assertEqual(result['director']['creativePassWarning'],'')
            else:
                self.fail('did not finish within bounded continuation rounds')
        for stage in ('product','strategy','direction'):
            self.assertEqual(sum(s==stage for s,c in self.transport.calls),1)
        plans = [c['requestedPageNumbers'] for s, c in self.transport.calls if s == 'planning']
        self.assertEqual(plans, [list(range(1,9)), list(range(9,17)), list(range(17,25))])
        self.assertEqual(sum(s=='prompts' for s,c in self.transport.calls),8)
        self.assertTrue(all(remaining>=75 for stage,remaining in launches))
        self.assertEqual(result['companyPromptStatus']['readyCount'],24)

    def test_no_progress_does_not_auto_loop(self):
        def exhausted(settings,messages):
            if 'creative director' in messages[0]['content']:
                raise engine.DirectorBudgetExhausted('request budget exhausted')
            return self.transport(settings,messages)
        with patch.object(engine,'invoke_ai_director_chat',side_effect=exhausted):
            first=self.run_plan()
            second=self.run_plan()
        self.assertTrue(first['continuation']['autoContinue'])
        self.assertFalse(second['continuation']['autoContinue'])
        self.assertFalse(second['companyPromptStatus']['ready'])
