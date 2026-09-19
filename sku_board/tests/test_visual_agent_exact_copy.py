import json
import unittest
from copy import deepcopy
from unittest.mock import patch

from sku_board.tests import test_visual_agent_pipeline as fixture
from sku_board.visual_agents import adapter, dynamic_prompt
from sku_board.visual_agents.contracts import digest
from sku_board.visual_agents.store import Store
from sku_board.visual_agents.validation import validate_prompt


class ExactCopyContractTests(unittest.TestCase):
    def setUp(self):
        self.spec = {'page': 1, 'sourceIds': ['S1']}
        self.prompt = {
            'page': 1,
            'creativeInstruction': 'Create an independent garden photograph. Place the headline in the open sky, '
                'the support copy in a quiet cream panel and the label beside the real product. Use morning light.',
            'exactCopy': [{'text': 'Mehr Farbe im Garten', 'role': 'headline', 'sourceIds': ['S1']}],
            'negativeInstructions': ['No invented product features.'],
        }
        self.product = {'productVisualDNA': {'shape': 'green leaves'}}

    def validate(self, value, country='DE'):
        return validate_prompt(value, self.spec, country, fixture.engine.cod_source_input.localized_copy)

    def test_separate_copy_is_valid_and_compiles_into_authoritative_text_block(self):
        before = deepcopy(self.prompt)
        value = self.validate(self.prompt)
        result = adapter.compile_prompt(value, self.product, 'DE', '750x1000')
        block = result.split('[Exact visible copy] ', 1)[1].split('\n\n[Text boundary]', 1)[0]
        self.assertEqual(json.loads(block), self.prompt['exactCopy'])
        self.assertIn('list is authoritative', result)
        self.assertEqual(self.prompt, before)
        self.assertNotIn(self.prompt['exactCopy'][0]['text'], self.prompt['creativeInstruction'])

    def test_native_copy_quotes_newlines_and_backslashes_preserved(self):
        for country, text in (
            ('DE', '„Mehr Farbe“ – schöne Blätter\nFür den Garten: "Grün" \\ Pflege'),
            ('TH', 'ดูแลผิว\nทุกวัน'),
            ('JP', '毎日の「ケア」\n自然な使い心地'),
            ('KR', '매일 편안하게\n자연스러운 사용감'),
        ):
            with self.subTest(country=country):
                value = deepcopy(self.prompt)
                value['exactCopy'][0]['text'] = text
                self.validate(value, country)
                result = adapter.compile_prompt(value, self.product, country, '750x1000')
                block = result.split('[Exact visible copy] ', 1)[1].split('\n\n[Text boundary]', 1)[0]
                self.assertEqual(json.loads(block)[0]['text'], text)

    def test_real_copy_errors_are_still_rejected(self):
        for changes in (
            {'text': '未翻译中文'}, {'text': 'nicht dokumentiert'}, {'text': '   '},
            {'sourceIds': ['S2']}, {'sourceIds': [{}]}, {'role': []},
        ):
            value = deepcopy(self.prompt)
            value['exactCopy'][0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.validate(value)
        for changes in ({'page': True}, {'page': 2}, {'creativeInstruction': 'short'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.validate({**self.prompt, **changes})

    def test_no_text_page_and_legacy_inline_text_both_remain_valid(self):
        self.validate({**self.prompt, 'exactCopy': []})
        self.validate({**self.prompt, 'creativeInstruction': self.prompt['creativeInstruction'] + ' Mehr Farbe im Garten'})

    def test_author_contract_explains_compiler_ownership_without_more_calls(self):
        calls = []
        def call(stage, role, context, schema):
            calls.append(stage)
            self.assertIn('compiler appends exactCopy', role)
            self.assertNotIn('Include each exactCopy text verbatim', role)
            return {'pages': [self.prompt]}
        self.assertEqual(dynamic_prompt.create(call, {}), [self.prompt])
        self.assertEqual(calls, ['prompts'])


class ExactCopyResumeTests(unittest.TestCase):
    setUp = fixture.PipelineTests.setUp
    run_plan = fixture.PipelineTests.run_plan

    def prepare_old_checkpoint(self):
        first = self.run_plan()
        store = Store(self.tmp.name)
        state = store.get(self.actor['username'], 'plan', first['agentPlanId'])
        for n in (1, 2, 3):
            value = state['prompts'].pop(str(n))
            value = {k: value[k] for k in ('page', 'creativeInstruction', 'exactCopy', 'negativeInstructions')}
            for item in value['exactCopy']:
                value['creativeInstruction'] = value['creativeInstruction'].replace(item['text'], 'headline from exactCopy')
            state.setdefault('promptDrafts', {})[str(n)] = {
                'page': n, 'error': '准确文案未完整写入本页 Prompt', 'draft': value,
            }
        state['error'] = 'ValueError: 准确文案未完整写入本页 Prompt'
        state['stages']['prompts']['status'] = 'waiting'
        with store.db() as db:
            self.campaign_key = db.execute("SELECT key FROM artifacts WHERE kind='campaign'").fetchone()[0]
        self.save_checkpoint(store, state)
        return first, store, state

    def save_checkpoint(self, store, state):
        store.put(self.actor['username'], 'campaign', self.campaign_key, state)
        store.put(self.actor['username'], 'plan', state['planId'], state)

    def test_model_can_keep_copy_separate_without_repair_request(self):
        def transport(settings, messages):
            result, latency = self.transport(settings, messages)
            if self.transport.calls[-1][0] == 'prompts':
                data = json.loads(result)
                for value in data['pages']:
                    for item in value['exactCopy']:
                        value['creativeInstruction'] = value['creativeInstruction'].replace(item['text'], 'headline from exactCopy')
                return json.dumps(data, ensure_ascii=False), latency
            return result, latency
        with patch.object(fixture.engine, 'invoke_ai_director_chat', side_effect=transport):
            result = self.run_plan()
        self.assertTrue(result['companyPromptStatus']['ready'], result['director']['message'])
        self.assertEqual(sum(stage == 'prompts' for stage, _ in self.transport.calls), 3)
        for page in result['suitePages']:
            p = page['agentPrompt']
            self.assertIn(p['exactCopy'][0]['text'], p['resolvedPrompt'])
            self.assertNotIn(p['exactCopy'][0]['text'], p['creativeInstruction'])

    def test_old_drafts_resume_locally_without_ai_or_changing_complete_pages(self):
        first, store, state = self.prepare_old_checkpoint()
        kept = deepcopy(state['prompts'])
        product_before = store.get(self.actor['username'], 'product', state['productKey'])
        with patch.object(fixture.engine, 'invoke_ai_director_chat', side_effect=AssertionError('extra model request')) as model:
            result = self.run_plan()
        model.assert_not_called()
        self.assertTrue(result['companyPromptStatus']['ready'], result['director']['message'])
        self.assertEqual(result['agentPlanId'], first['agentPlanId'])
        saved = store.get(self.actor['username'], 'plan', result['agentPlanId'])
        self.assertEqual(saved['promptDrafts'], {})
        self.assertEqual(saved['error'], '')
        self.assertEqual(saved['planning'], state['planning'])
        self.assertEqual(saved['requestHash'], state['requestHash'])
        self.assertEqual(store.get(self.actor['username'], 'product', state['productKey']), product_before)
        for key, value in kept.items():
            self.assertEqual(saved['prompts'][key], value)
        for value in saved['prompts'].values():
            self.assertEqual(value['promptHash'], digest(value['resolvedPrompt']))
        adapter.verify_submission(store, self.actor['username'], result['suitePages'], self.payload)

    def test_only_still_invalid_draft_goes_back_to_model(self):
        _, store, state = self.prepare_old_checkpoint()
        state['promptDrafts']['2']['draft']['exactCopy'][0]['text'] = 'Wrong language'
        self.save_checkpoint(store, state)
        previous_calls = len(self.transport.calls)
        result = self.run_plan()
        self.assertTrue(result['companyPromptStatus']['ready'], result['director']['message'])
        calls = self.transport.calls[previous_calls:]
        self.assertEqual([stage for stage, _ in calls], ['prompts'])
        context = calls[0][1]
        self.assertEqual([page['page'] for page in context['pages']], [2])
        self.assertIn('语言不匹配', context['repairFeedback'][0]['error'])


if __name__ == '__main__':
    unittest.main()
