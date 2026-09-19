import json
import unittest
from copy import deepcopy
from unittest.mock import patch
from sku_board.tests import test_visual_agent_pipeline as fixture
from sku_board.visual_agents import adapter, product_intelligence
from sku_board.visual_agents.store import Store
from sku_board.visual_agents.validation import internal_copy, validate_prompt, design_issues


class CommercialContentTests(unittest.TestCase):
    setUp = fixture.PipelineTests.setUp
    run_plan = fixture.PipelineTests.run_plan

    def test_first_analysis_receives_description_and_seller_clarification(self):
        brief = '商品是植物根茎，不是装饰品。按描述设计德国落地页。'
        self.run_plan(suiteBrief=brief, productFacts='售卖形态：裸根；交付：三支根茎')
        ctx = next(c for s, c in self.transport.calls if s == 'product')
        self.assertEqual(ctx['userBrief'], brief)
        self.assertIn('裸根', ctx['productFacts'])

    def test_campaign_changes_reuse_analysis_but_product_correction_changes_cache(self):
        first = self.run_plan(productFacts='规格：护理棒 15ml')
        self.run_plan(productFacts='规格：护理棒 15ml', suiteCountry='JP', suiteCount=12,
                      suiteBrief='换暖色背景，改为日语')
        self.assertEqual(sum(s == 'product' for s, _ in self.transport.calls), 1)
        second = self.run_plan(productFacts='规格：护理棒 30ml')
        self.assertEqual(sum(s == 'product' for s, _ in self.transport.calls), 2)
        self.assertNotEqual(first['director']['productAnalysisId'], second['director']['productAnalysisId'])
        self.assertIsNotNone(Store(self.tmp.name).get(self.actor['username'], 'plan', first['agentPlanId']))

    def test_legacy_identity_conflict_reuses_analysis_without_confirmation_gate(self):
        def respond(settings, messages):
            response, latency = self.transport(settings, messages)
            if self.transport.calls[-1][0] == 'product':
                data = json.loads(response)
                data['identityAssessment'] = {'declaredProduct': '玉簪花', 'sellingForm': '待确认',
                    'status': 'needs_confirmation', 'conflicts': ['描述与参考图呈现的形态不同'],
                    'question': '买家收到的是根茎还是装饰插枝？'}
                return json.dumps(data), latency
            return response, latency
        with patch.object(fixture.engine, 'invoke_ai_director_chat', side_effect=respond):
            self.transport.fail = 'strategy'
            first = self.run_plan()
            store = Store(self.tmp.name)
            cached = deepcopy(store.get(self.actor['username'], 'product', first['director']['productAnalysisId']))
            self.transport.fail = None
            second = self.run_plan()
        self.assertFalse(first['companyPromptStatus']['ready'])
        self.assertTrue(second['companyPromptStatus']['ready'], second['director']['message'])
        self.assertNotIn('identityAssessment', second['director'])
        self.assertEqual(second['director']['stages']['product']['status'], 'cached')
        self.assertEqual(sum(s == 'product' for s, _ in self.transport.calls), 1)
        self.assertEqual(cached, store.get(self.actor['username'], 'product', first['director']['productAnalysisId']))
        product_context = next(c['product'] for s, c in self.transport.calls if s == 'strategy')
        self.assertNotIn('identityAssessment', product_context)
        self.assertIn('描述与参考图呈现的形态不同', product_context['missingInformation'])
        self.assertEqual(first['agentPlanId'], second['agentPlanId'])

    def test_product_analysis_no_longer_requires_identity_form_contract(self):
        def respond(settings, messages):
            response, latency = self.transport(settings, messages)
            if self.transport.calls[-1][0] == 'product':
                data = json.loads(response)
                data.pop('identityAssessment')
                return json.dumps(data), latency
            return response, latency
        with patch.object(fixture.engine, 'invoke_ai_director_chat', side_effect=respond):
            result = self.run_plan()
        self.assertTrue(result['companyPromptStatus']['ready'], result['director']['message'])
        self.assertNotIn('identityAssessment', product_intelligence.SCHEMA)

    def test_legacy_confirmation_notes_are_not_silently_treated_as_facts(self):
        original = {'facts': [{'id': 'F1', 'status': 'uncertain'}], 'missingInformation': ['色数存在差异'],
                    'identityAssessment': {'status': 'needs_confirmation', 'conflicts': ['色数存在差异', '发货形态待明确']}}
        snapshot = deepcopy(original)
        view = product_intelligence.for_planning(original)
        self.assertEqual(original, snapshot)
        self.assertNotIn('identityAssessment', view)
        self.assertEqual(view['missingInformation'], ['色数存在差异', '发货形态待明确'])
        self.assertEqual(view['facts'][0]['status'], 'uncertain')

    def test_internal_copy_repaired_only_on_affected_page(self):
        def respond(settings, messages):
            response, latency = self.transport(settings, messages)
            stage, ctx = self.transport.calls[-1]
            if stage == 'prompts' and not ctx.get('repairFeedback'):
                data = json.loads(response)
                for page in data['pages']:
                    if page['page'] == 1:
                        page['exactCopy'][0]['text'] = 'nicht dokumentiert'
                        page['creativeInstruction'] += ' nicht dokumentiert'
                return json.dumps(data), latency
            return response, latency
        with patch.object(fixture.engine, 'invoke_ai_director_chat', side_effect=respond):
            result = self.run_plan()
        self.assertTrue(result['companyPromptStatus']['ready'], result['director']['message'])
        repairs = [c for s, c in self.transport.calls if s == 'prompts' and c.get('repairFeedback')]
        self.assertEqual(len(repairs), 1)
        self.assertEqual([p['page'] for p in repairs[0]['pages']], [1])
        self.assertIn('内部核查', repairs[0]['repairFeedback'][0]['error'])

    def test_real_german_leakage_patterns_and_consumer_instructions(self):
        for value in ('Nicht belegt', 'nicht dokumentiert', 'Durch die Bilder gestützt', '资料缺失', 'evidence ledger'):
            self.assertTrue(internal_copy(value), value)
        for value in ('Nur zur äußeren Anwendung.', 'Pflanzkübel nicht enthalten.',
                      'Vor Gebrauch Anleitung lesen.', '避免接触眼睛', '规格：15ml'):
            self.assertFalse(internal_copy(value), value)

    def test_plan_requires_commercial_visual_decisions(self):
        result = self.run_plan()
        specs = [deepcopy(p['agentSpec']) for p in result['suitePages']]
        del specs[2]['visualDesign']['benefitVisualization']
        self.assertEqual([i['page'] for i in design_issues(specs)], [3])
        specs[2]['visualDesign']['benefitVisualization'] = '实际使用动作展示价值'
        specs[5]['copyDirection'] = 'Nicht belegt: 内部核查内容'
        self.assertEqual([i['page'] for i in design_issues(specs)], [6])

    def test_submission_rejects_changed_facts_but_accepts_old_client_omission(self):
        result = self.run_plan(productFacts='规格：15ml\n交付：护理棒')
        store = Store(self.tmp.name)
        adapter.verify_submission(store, self.actor['username'], result['suitePages'], self.payload)
        adapter.verify_submission(store, self.actor['username'], result['suitePages'],
                                  {**self.payload, 'productFacts': '规格：15ml\r\n交付：护理棒'})
        with self.assertRaisesRegex(ValueError, '已变化'):
            adapter.verify_submission(store, self.actor['username'], result['suitePages'],
                                      {**self.payload, 'productFacts': '规格：30ml'})

    def test_final_prompt_separates_renderable_copy_from_internal_context(self):
        result = self.run_plan()
        for page in result['suitePages']:
            self.assertIn('[Text boundary]', page['agentPrompt']['resolvedPrompt'])
            self.assertIn('internal, not image text', page['agentPrompt']['resolvedPrompt'])
