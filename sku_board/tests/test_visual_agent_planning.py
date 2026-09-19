import unittest
from copy import deepcopy
from sku_board.tests import test_visual_agent_pipeline as fixture
from sku_board.visual_agents.validation import validate_plan, validate_prompt


class PlanningTests(unittest.TestCase):
    setUp = fixture.PipelineTests.setUp
    run_plan = fixture.PipelineTests.run_plan

    def test_duplicate_layout_and_unknown_sources_rejected(self):
        result = self.run_plan()
        specs = [deepcopy(p['agentSpec']) for p in result['suitePages']]
        sources = {s for p in specs for s in p['sourceIds']}
        assets = {s for p in specs for s in p['referenceAssetIds']}
        specs[1]['scene'] = specs[0]['scene']
        specs[1]['composition'] = specs[0]['composition']
        with self.assertRaisesRegex(ValueError, '过近'):
            validate_plan(specs, 8, sources, {'F1'}, assets)
        specs[1]['sourceIds'] = ['invented-source']
        with self.assertRaisesRegex(ValueError, '未知引用'):
            validate_plan(specs, 8, sources, {'F1'}, assets)

    def test_wrong_market_and_missing_copy_field_rejected_but_inline_duplication_optional(self):
        result = self.run_plan()
        page = result['suitePages'][0]
        prompt = deepcopy(page['agentPrompt'])
        prompt['exactCopy'][0]['text'] = '한국어'
        with self.assertRaisesRegex(ValueError, '语言'):
            validate_prompt(prompt, page['agentSpec'], 'TH', fixture.engine.cod_source_input.localized_copy)
        prompt['exactCopy'][0]['text'] = 'คำอธิบายอื่น'
        self.assertNotIn('คำอธิบายอื่น', prompt['creativeInstruction'])
        validate_prompt(prompt, page['agentSpec'], 'TH', fixture.engine.cod_source_input.localized_copy)
        del prompt['exactCopy']
        with self.assertRaisesRegex(ValueError, '缺少字段'):
            validate_prompt(prompt, page['agentSpec'], 'TH', fixture.engine.cod_source_input.localized_copy)
