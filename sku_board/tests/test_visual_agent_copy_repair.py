import json
import unittest
from unittest.mock import patch
from sku_board.tests import test_visual_agent_pipeline as fixture
from sku_board.visual_agents.validation import identity_label
from sku_board.visual_agents.store import Store


class CopyRepairTests(unittest.TestCase):
    setUp = fixture.PipelineTests.setUp
    run_plan = fixture.PipelineTests.run_plan

    def test_only_grounded_package_labels_allowed(self):
        dna = {'identityLocks': ['Topacme wordmark.', 'Product descriptor reads 3D Relief Art Pen.']}
        for text in ('Topacme', '3D Relief Art Pen'):
            self.assertTrue(identity_label(text, 'label', dna))
            self.assertFalse(identity_label(text, 'headline', dna))
        for text in ('Top', 'OtherBrand', 'Best quality', '未翻译中文', ''):
            self.assertFalse(identity_label(text, 'label', dna))

    def test_one_bad_page_repaired_without_regenerating_good_pages(self):
        def transport(settings, messages):
            result, latency = self.transport(settings, messages)
            ctx = self.transport.calls[-1][1]
            if self.transport.calls[-1][0] == 'prompts' and not ctx.get('repairFeedback'):
                data = json.loads(result)
                for p in data['pages']:
                    if p['page'] == 1:
                        p['exactCopy'][0]['text'] = 'English marketing headline'
                        p['creativeInstruction'] += ' English marketing headline'
                result = json.dumps(data)
            return result, latency
        with patch.object(fixture.engine, 'invoke_ai_director_chat', side_effect=transport):
            result = self.run_plan()
        self.assertTrue(result['companyPromptStatus']['ready'], result['director']['message'])
        repairs = [c for s, c in self.transport.calls if s == 'prompts' and c.get('repairFeedback')]
        self.assertEqual(len(repairs), 1)
        self.assertEqual([p['page'] for p in repairs[0]['pages']], [1])
        state = Store(self.tmp.name).get(self.actor['username'], 'plan', result['agentPlanId'])
        self.assertEqual(state['promptDrafts'], {})

    def test_persistent_bad_copy_stops_after_one_repair_and_keeps_good_pages(self):
        def transport(settings, messages):
            result, latency = self.transport(settings, messages)
            if self.transport.calls[-1][0] == 'prompts':
                data = json.loads(result)
                for p in data['pages']:
                    if p['page'] == 1:
                        p['exactCopy'][0]['text'] = 'Wrong language'
                        p['creativeInstruction'] += ' Wrong language'
                result = json.dumps(data)
            return result, latency
        with patch.object(fixture.engine, 'invoke_ai_director_chat', side_effect=transport):
            result = self.run_plan()
        self.assertEqual(result['companyPromptStatus']['readyCount'], 2)
        self.assertEqual(sum(s == 'prompts' for s, c in self.transport.calls), 2)
        state = Store(self.tmp.name).get(self.actor['username'], 'plan', result['agentPlanId'])
        self.assertIn('1', state['promptDrafts'])
        resumed = self.run_plan()
        self.assertTrue(resumed['companyPromptStatus']['ready'])
