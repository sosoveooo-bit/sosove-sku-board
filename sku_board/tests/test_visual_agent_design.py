import unittest
from copy import deepcopy
from unittest.mock import patch
from sku_board.tests import test_visual_agent_pipeline as fixture
from sku_board.visual_agents import scene_planner
from sku_board.visual_agents.design_knowledge import for_product, reference_catalog
from sku_board.visual_agents.validation import design_issues


def specs(count=8):
    return [{'page': i + 1, 'scene': name, 'composition': name + ' arrangement', 'sourceIds': ['S1'],
             'purpose': name, 'visualDesign': {'primarySubject': 'person', 'method': 'demonstration',
             'layoutFamily': 'single', 'humanRole': 'portrait', 'visualHook': name,
             'referenceReason': 'matching usage photograph', 'buyingReason': 'explain everyday usability',
             'benefitVisualization': name + ' explains use',
             'informationHierarchy': ['large action photograph', 'readable local headline']}}
            for i, name in enumerate(['reading at desk', 'walking outdoors', 'cooking dinner', 'packing luggage',
                                      'phone call', 'applying cream', 'checking package', 'resting on sofa'][:count])]


class DesignTests(unittest.TestCase):
    def test_category_selection_is_not_fixed_pages(self):
        for category in ('beauty', 'supplements', 'apparel', 'home', 'electronics'):
            result = for_product({'categories': [category]})
            self.assertEqual(result['categoryChoices'][0]['category'], category)
            self.assertNotIn('pages', result)
        self.assertEqual(for_product({'categories': ['unknown widget']})['categoryChoices'], [])

    def test_reference_observations_and_explicit_roles(self):
        product = {'referenceBreakdown': [{'assetId': 'a', 'role': 'usage', 'observations': 'hand applies product'}]}
        catalog = reference_catalog(product, [{'assetId': 'a', 'role': 'auto'}, {'assetId': 'b', 'role': 'style'}])
        self.assertEqual(len(catalog), 1)
        self.assertEqual(catalog[0]['role'], 'usage')
        self.assertIn('hand', catalog[0]['observations'])
        self.assertEqual(reference_catalog(product, [{'assetId': 'a', 'role': 'packaging'}])[0]['role'], 'packaging')

    def test_semantic_labels_detect_same_portraits_despite_different_prose(self):
        issues = design_issues(specs())
        self.assertIn(3, [i['page'] for i in issues])
        self.assertIn(8, [i['page'] for i in issues])
        self.assertEqual(design_issues(specs(), allow_uniform=True), [])

    def test_invalid_design_and_actual_duplicate(self):
        pages = specs(2)
        pages[1]['scene'], pages[1]['composition'] = pages[0]['scene'], pages[0]['composition']
        self.assertEqual(design_issues(pages)[0]['page'], 2)
        pages[0]['visualDesign']['method'] = 'arbitrary synonym'
        self.assertEqual(design_issues(pages)[0]['page'], 1)

    def test_repair_keeps_untouched_pages_and_sources(self):
        pages = specs(3)
        replacement = deepcopy(pages[2])
        replacement['scene'] = 'new actual scene'
        calls = []
        def call(stage, role, context, schema):
            calls.append(context)
            return {'pages': [replacement]}
        result = scene_planner.repair(call, {}, pages, [{'page': 3, 'reason': 'repetition'}])
        self.assertEqual(result[:2], pages[:2])
        self.assertEqual(len(calls[0]['pagesToRepair']), 1)
        replacement['sourceIds'] = ['invented']
        with self.assertRaises(ValueError):
            scene_planner.repair(call, {}, pages, [{'page': 3}])


class PipelineDesignTests(unittest.TestCase):
    setUp = fixture.PipelineTests.setUp
    run_plan = fixture.PipelineTests.run_plan

    def test_targeted_repair_failure_retains_draft_and_product(self):
        original_create = scene_planner.create
        saved = {}
        def repeated(call, context):
            pages = original_create(call, context)
            saved['good'] = deepcopy(pages)
            for page in pages[:3]:
                page['visualDesign'] = deepcopy(pages[0]['visualDesign'])
            return pages
        with patch.object(scene_planner, 'create', side_effect=repeated), patch.object(
                scene_planner, 'repair', side_effect=TimeoutError('repair timeout')) as repair:
            first = self.run_plan()
            self.assertFalse(first['companyPromptStatus']['ready'])
            self.assertEqual(repair.call_count, 1)
            self.assertEqual(repair.call_args.args[3][0]['page'], 3)
        def repaired(call, context, pages, issues):
            self.assertEqual([i['page'] for i in issues], [3, 4, 7])
            numbers = {i['page'] for i in issues}
            return [saved['good'][p['page'] - 1] if p['page'] in numbers else p for p in pages]
        with patch.object(scene_planner, 'repair', side_effect=repaired):
            result = self.run_plan()
        self.assertTrue(result['companyPromptStatus']['ready'], result['director']['message'])
        self.assertEqual(sum(s == 'product' for s, _ in self.transport.calls), 1)
        self.assertEqual(sum(s == 'planning' for s, _ in self.transport.calls), 1)

    def test_unresolved_repair_is_bounded_and_skips_prompts(self):
        original_create = scene_planner.create
        def repeated(call, context):
            pages = original_create(call, context)
            for page in pages:
                page['visualDesign'] = deepcopy(pages[0]['visualDesign'])
            return pages
        with patch.object(scene_planner, 'create', side_effect=repeated), patch.object(
                scene_planner, 'repair', side_effect=lambda call, context, pages, issues: pages) as repair:
            result = self.run_plan()
        self.assertFalse(result['companyPromptStatus']['ready'])
        self.assertEqual(repair.call_count, 1)
        self.assertFalse(any(s == 'prompts' for s, _ in self.transport.calls))

    def test_context_and_revision_preserve_product_cache(self):
        first = self.run_plan()
        self.assertTrue(first['companyPromptStatus']['ready'], first['director']['message'])
        planning = next(c for stage, c in self.transport.calls if stage == 'planning')
        self.assertEqual(planning['designKnowledge']['categoryChoices'][0]['category'], 'beauty')
        prompt = next(c for stage, c in self.transport.calls if stage == 'prompts')
        selected = {a for p in prompt['pages'] for a in p['referenceAssetIds']}
        self.assertEqual({a['assetId'] for a in prompt['assets']}, selected)
        with patch('sku_board.visual_agents.pipeline.REVISION', 'test-new-creative-version'):
            result = self.run_plan()
        self.assertTrue(result['companyPromptStatus']['ready'])
        self.assertEqual(sum(s == 'product' for s, _ in self.transport.calls), 1)
        self.assertEqual(sum(s == 'planning' for s, _ in self.transport.calls), 2)
