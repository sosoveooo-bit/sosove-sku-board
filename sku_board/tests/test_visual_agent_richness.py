import json
import re
import unittest
from pathlib import Path
from unittest.mock import patch

from sku_board.tests import test_visual_agent_pipeline as fixture
from sku_board.visual_agents import adapter, pipeline
from sku_board.visual_agents.design_knowledge import REVISION, for_product
from sku_board.visual_agents.store import Store


class RichVisualExecutionTests(unittest.TestCase):
    setUp = fixture.PipelineTests.setUp
    run_plan = fixture.PipelineTests.run_plan

    def test_composition_survives_prompt_author_summary_for_every_page(self):
        result = self.run_plan()
        self.assertTrue(result['companyPromptStatus']['ready'])
        for page in result['suitePages']:
            prompt = page['agentPrompt']['resolvedPrompt']
            prefix = '[Page visual execution; internal art direction, not visible copy] '
            execution = json.loads(prompt.split(prefix, 1)[1].split('\n', 1)[0])
            spec = page['agentSpec']
            self.assertEqual(execution['scene'], spec['scene'])
            self.assertEqual(execution['composition'], spec['composition'])
            self.assertEqual(execution['informationHierarchy'], spec['visualDesign']['informationHierarchy'])
            self.assertEqual(execution['benefitVisualization'], spec['visualDesign']['benefitVisualization'])
            self.assertNotIn('sourceIds', execution)
            self.assertEqual(page['agentDesignRevision'], REVISION)
        # No new creative stage or image-review call for richness.
        self.assertEqual([s for s, _ in self.transport.calls],
                         ['product', 'strategy', 'direction', 'planning', 'prompts', 'prompts', 'prompts'])
        self.assertEqual(result['director']['designRevision'], REVISION)

    def test_new_design_revision_reuses_product_and_preserves_old_plan_submission(self):
        old = self.run_plan()
        store = Store(self.tmp.name)
        previous = store.get(self.actor['username'], 'plan', old['agentPlanId'])
        with patch.object(pipeline, 'REVISION', 'test-next-design-revision'):
            new = self.run_plan()
        self.assertNotEqual(old['agentPlanId'], new['agentPlanId'])
        self.assertEqual(old['director']['productAnalysisId'], new['director']['productAnalysisId'])
        self.assertEqual(sum(s == 'product' for s, _ in self.transport.calls), 1)
        self.assertEqual(previous, store.get(self.actor['username'], 'plan', old['agentPlanId']))
        self.assertEqual(new['suitePages'][0]['agentDesignRevision'], 'test-next-design-revision')
        adapter.verify_submission(store, self.actor['username'], old['suitePages'], self.payload)

    def test_legacy_checkpoint_is_not_relabelled_as_current_revision(self):
        result = self.run_plan()
        store = Store(self.tmp.name)
        state = store.get(self.actor['username'], 'plan', result['agentPlanId'])
        state.pop('designRevision')
        self.assertTrue(all('agentDesignRevision' not in p for p in adapter.pages_from_state(state, self.payload)))

    def test_minimal_and_text_free_spec_stays_minimal_no_global_panel_template(self):
        spec = {'scene': 'Single product on white; no props or people.',
                'composition': 'One centered packshot, no supporting panels, no text.',
                'visualDesign': {'benefitVisualization': 'Accurate silhouette and material finish.',
                                 'informationHierarchy': ['Product dominates.', 'Clean white margin.']}}
        authored = {'creativeInstruction': 'A white-background product photograph.',
                    'exactCopy': [], 'negativeInstructions': []}
        prompt = adapter.compile_prompt(authored, {'productVisualDNA': {'shape': 'cylinder'}}, 'DE', '750x1000', page_spec=spec)
        self.assertIn(spec['composition'], prompt)
        self.assertIn('[Exact visible copy] []', prompt)
        self.assertNotIn('split-screen', prompt)
        legacy = adapter.compile_prompt(authored, {'productVisualDNA': {}}, 'DE', '750x1000')
        self.assertNotIn('[Page visual execution', legacy)

    def test_category_independent_policy_and_browser_revision_agree(self):
        for category in ('beauty', 'supplements', 'apparel', 'home', 'electronics', 'garden', 'unknown'):
            policy = for_product({'categories': [category]})
            self.assertIn('Explicit white-background, minimal or text-free requests take precedence', policy['richnessRule'])
            self.assertNotIn('pages', policy)
        source = (Path(__file__).parents[1] / 'static' / 'app.js').read_text(encoding='utf-8')
        browser_revision = re.search(r"const AI_VISUAL_DESIGN_REVISION = '([^']+)'", source).group(1)
        self.assertEqual(browser_revision, REVISION)
