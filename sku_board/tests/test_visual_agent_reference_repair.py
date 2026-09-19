import json
import unittest
from copy import deepcopy
from unittest.mock import patch
from sku_board.tests import test_visual_agent_pipeline as fixture
from sku_board.visual_agents import scene_planner
from sku_board.visual_agents.scheduling import PlanningYield
from sku_board.visual_agents.store import Store
from sku_board.visual_agents.validation import plan_contract_issues


class ReferenceRepairTests(unittest.TestCase):
    setUp = fixture.PipelineTests.setUp
    run_plan = fixture.PipelineTests.run_plan

    def malformed_transport(self, settings, messages):
        result, latency = self.transport(settings, messages)
        if self.transport.calls[-1][0] == 'planning':
            data = json.loads(result)
            self.original = deepcopy(data['pages'])
            data['pages'][0]['sourceIds'] = []
            data['pages'][0]['referenceAssetIds'] = []
            data['pages'][3]['referenceAssetIds'] = ['unknown-asset']
            return json.dumps(data), latency
        return result, latency

    def state(self, result):
        return Store(self.tmp.name).get(self.actor['username'], 'plan', result['agentPlanId'])

    def test_only_invalid_pages_repaired_and_original_good_pages_preserved(self):
        actual_repair = scene_planner.repair_contract

        def repair(call, context, pages, issues):
            def model(stage, role, ctx, schema):
                self.assertEqual([p['page'] for p in ctx['pagesToRepair']], [1, 4])
                self.assertEqual(len(ctx['otherPages']), 6)
                self.assertIn('NOT certify', role)
                self.assertEqual(ctx['allowedReferences']['referenceAssetIds'], [context['assets'][0]['assetId']])
                return {'pages': [self.original[0], self.original[3]]}
            return actual_repair(model, context, pages, issues)

        with patch.object(fixture.engine, 'invoke_ai_director_chat', side_effect=self.malformed_transport), \
                patch.object(scene_planner, 'repair_contract', side_effect=repair) as correction:
            result = self.run_plan()
        self.assertTrue(result['companyPromptStatus']['ready'], result['director']['message'])
        correction.assert_called_once()
        self.assertEqual(self.state(result)['planning'], self.original)
        self.assertEqual(sum(s == 'planning' for s, _ in self.transport.calls), 1)

    def test_yield_saves_bad_draft_and_resume_does_not_regenerate_full_plan(self):
        with patch.object(fixture.engine, 'invoke_ai_director_chat', side_effect=self.malformed_transport), \
                patch.object(scene_planner, 'repair_contract', side_effect=PlanningYield('time slice')):
            first = self.run_plan()
        self.assertEqual(self.state(first)['planningDraft'][0]['sourceIds'], [])
        self.assertTrue(first['continuation']['autoContinue'])
        with patch.object(scene_planner, 'create', side_effect=AssertionError('full regeneration')), \
                patch.object(scene_planner, 'repair_contract', return_value=self.original):
            resumed = self.run_plan()
        self.assertTrue(resumed['companyPromptStatus']['ready'], resumed['director']['message'])
        self.assertEqual(sum(s == 'product' for s, _ in self.transport.calls), 1)

    def test_persistent_error_bounded_and_partial_repairs_persist(self):
        def still_bad(call, context, pages, issues):
            pages = deepcopy(pages)
            pages[0] = deepcopy(self.original[0])
            return pages
        with patch.object(fixture.engine, 'invoke_ai_director_chat', side_effect=self.malformed_transport), \
                patch.object(scene_planner, 'repair_contract', side_effect=still_bad) as correction:
            first = self.run_plan()
        correction.assert_called_once()
        self.assertFalse(first['companyPromptStatus']['ready'])
        self.assertIn('第 4 页', first['director']['message'])
        saved = self.state(first)
        self.assertEqual(saved['planningDraft'][0], self.original[0])
        self.assertEqual(saved['prompts'], {})
        def finish(call, context, pages, issues):
            self.assertEqual([i['page'] for i in issues], [4])
            return self.original
        with patch.object(scene_planner, 'create', side_effect=AssertionError('full regeneration')), \
                patch.object(scene_planner, 'repair_contract', side_effect=finish):
            self.assertTrue(self.run_plan()['companyPromptStatus']['ready'])

    def test_repair_rejects_unrequested_or_duplicate_page_numbers(self):
        self.run_plan()
        pages = self.state(self.run_plan())['planning']
        context = {'sources': [{'id': 'S1'}], 'product': {'facts': [{'id': 'F1'}]}, 'assets': []}
        with self.assertRaisesRegex(ValueError, '页码不匹配'):
            scene_planner.repair_contract(lambda *a: {'pages': [pages[1]]}, context, pages,
                                         [{'page': 1, 'reason': 'missing'}])

    def test_missing_reference_diagnostic_and_coverage_remain_strict(self):
        result = self.run_plan()
        pages = deepcopy(self.state(result)['planning'])
        ids = {a for p in pages for a in p['referenceAssetIds']}
        pages[0]['referenceAssetIds'] = []
        issues = plan_contract_issues(pages, 8, {'S1'}, {'F1'}, ids)
        self.assertEqual([i['page'] for i in issues], [1])
        self.assertIn('referenceAssetIds', issues[0]['reason'])
        pages[0] = deepcopy(pages[1])
        with self.assertRaisesRegex(ValueError, '编号'):
            plan_contract_issues(pages, 8, {'S1'}, {'F1'}, ids)

    def test_unindexable_saved_draft_can_recover_on_resume(self):
        with patch.object(scene_planner, 'create', return_value=[{'page': 1}]):
            first = self.run_plan()
        self.assertEqual(self.state(first)['planningDraft'], [{'page': 1}])
        resumed = self.run_plan()
        self.assertTrue(resumed['companyPromptStatus']['ready'], resumed['director']['message'])
        self.assertTrue(resumed['director']['productCacheHit'])
