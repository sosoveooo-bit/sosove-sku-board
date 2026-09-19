import json
import unittest
from unittest.mock import patch
from sku_board.tests import test_visual_agent_pipeline as fixture
from sku_board.visual_agents.structured_output import parse, StructuredOutputError
from sku_board import backend as engine


class ParseTests(unittest.TestCase):
    def test_fenced_and_prefaced_and_double_encoded(self):
        for value in ('```json\n{"name":"valid"}\n```', 'reason {"wrong":1}\n{"name":"valid"}',
                      json.dumps('{"name":"valid"}')):
            self.assertEqual(parse(value, {'name': ''}), {'name': 'valid'})

    def test_array_pages_only(self):
        self.assertEqual(parse('[{"page":1}]', {'pages': []}), {'pages': [{'page': 1}]})
        with self.assertRaises(StructuredOutputError):
            parse('[{"page":1}]', {'visualTheme': ''})

    def test_truncated_or_missing_content_not_fabricated(self):
        for value in ('', 'I will plan this now.', '{"name":"unfinished', '{"meta":{"name":"x"},"required":', '{"name":null}'):
            with self.assertRaises(StructuredOutputError):
                parse(value, {'name': '', 'required': ''})


class RecoveryTests(unittest.TestCase):
    setUp = fixture.PipelineTests.setUp
    run_plan = fixture.PipelineTests.run_plan

    def test_direction_format_retry_once_and_prior_stages_reused(self):
        count = 0
        def flaky(settings, messages):
            nonlocal count
            if 'creative director' in messages[0]['content']:
                count += 1
                self.assertTrue(settings['_jsonObject'])
                if count == 1:
                    return 'Here is my design approach.', 1
                self.assertTrue(settings['_singleModel'])
            return self.transport(settings, messages)
        with patch.object(engine, 'invoke_ai_director_chat', side_effect=flaky):
            result = self.run_plan()
        self.assertTrue(result['companyPromptStatus']['ready'], result['director']['message'])
        self.assertEqual(count, 2)
        self.assertEqual(sum(s == 'product' for s,c in self.transport.calls), 1)
        direction = next(r for r in result['director']['runs'] if r['stage'] == 'direction')
        self.assertEqual(direction['formatAttempts'], 2)
        self.assertIn('outputHash', direction)

    def test_repeated_bad_format_stops_and_keeps_product_strategy(self):
        count = 0
        def bad(settings, messages):
            nonlocal count
            if 'creative director' in messages[0]['content']:
                count += 1
                return '', 1
            return self.transport(settings, messages)
        with patch.object(engine, 'invoke_ai_director_chat', side_effect=bad):
            result = self.run_plan()
        self.assertEqual(count, 2)
        self.assertFalse(result['companyPromptStatus']['ready'])
        self.assertIn('空正文', result['director']['message'])
        resumed = self.run_plan()
        self.assertTrue(resumed['companyPromptStatus']['ready'])
        self.assertEqual(sum(s == 'strategy' for s,c in self.transport.calls), 1)


class TransportTests(unittest.TestCase):
    def test_json_instruction_survives_system_to_instructions_conversion(self):
        from copy import deepcopy
        for content in ('Plan pages.', [{'type': 'text', 'text': 'Plan pages.'},
                                       {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,fixture'}}]):
            messages = [{'role': 'system', 'content': 'Return JSON.'}, {'role': 'user', 'content': content}]
            original = deepcopy(messages)
            prepared = engine.ai_director_json_messages(messages)
            user_text = prepared[1]['content']
            if isinstance(user_text, list):
                self.assertEqual(user_text[:-1], content)
                user_text = user_text[-1]['text']
            self.assertIn('json object', user_text)
            self.assertEqual(messages, original)
            self.assertEqual(engine.ai_director_json_messages(prepared), prepared)

    def test_wrapped_json_input_error_retries_once_without_format_option(self):
        error = ValueError("AI 导演返回错误（HTTP 502）：Response input messages must contain the word 'json' "
                           "in some form to use 'text.format' of type 'json_object'.")
        for outcomes in ([error, ('{"ok":true}', 1)], [error, error]):
            settings = {'model': 'fixture', '_jsonObject': True, '_singleModel': True,
                        '_disableStreamRetry': True, 'timeout': 30}
            with patch.object(engine, 'invoke_ai_director_chat_once', side_effect=outcomes) as once:
                if isinstance(outcomes[1], Exception):
                    with self.assertRaises(ValueError):
                        engine.invoke_ai_director_chat(settings, [])
                else:
                    engine.invoke_ai_director_chat(settings, [])
            self.assertEqual(once.call_count, 2)
            self.assertTrue(once.call_args_list[0].args[0]['_jsonObject'])
            self.assertFalse(once.call_args_list[1].args[0]['_jsonObject'])
            self.assertIn('json object', once.call_args_list[1].args[1][-1]['content'])

    def test_unrelated_gateway_and_billing_errors_do_not_disable_format(self):
        for status in (402, 502, 401):
            settings = {'model': 'fixture', '_jsonObject': True, '_singleModel': True,
                        '_disableStreamRetry': True, 'timeout': 30}
            with patch.object(engine, 'invoke_ai_director_chat_once',
                              side_effect=ValueError(f'HTTP {status}: upstream error')) as once:
                with self.assertRaises(ValueError):
                    engine.invoke_ai_director_chat(settings, [])
            self.assertEqual(once.call_count, 1)
            self.assertTrue(settings['_jsonObject'])

    def test_json_only_opt_in_and_finish_reason(self):
        from unittest.mock import MagicMock
        response = MagicMock(ok=True)
        response.json.return_value = {'choices':[{'message':{'content':'{"ok":true}'},'finish_reason':'stop'}]}
        base = {'apiKey':'fixture','model':'fixture','baseUrl':'https://fixture.invalid','timeout':5}
        with patch.object(engine.image_cancellation, 'post', return_value=response) as post:
            settings = {**base, '_jsonObject':True}
            engine.invoke_ai_director_chat_once(settings, [])
            self.assertEqual(post.call_args.kwargs['json']['response_format'], {'type':'json_object'})
            self.assertIn('json object', post.call_args.kwargs['json']['messages'][-1]['content'])
            self.assertEqual(settings['_responseFinishReason'], 'stop')
            engine.invoke_ai_director_chat_once(base, [])
            self.assertNotIn('response_format', post.call_args.kwargs['json'])

    def test_explicit_format_rejection_has_one_compatibility_retry(self):
        settings = {'model':'fixture','_jsonObject':True,'_singleModel':True,'timeout':30}
        with patch.object(engine, 'invoke_ai_director_chat_once', side_effect=[
                ValueError('AI 导演返回错误（HTTP 400）：response_format not supported'), ('{"ok":true}',1)]) as once:
            content,_ = engine.invoke_ai_director_chat(settings, [])
        self.assertEqual(once.call_count,2)
        self.assertTrue(once.call_args_list[0].args[0]['_jsonObject'])
        self.assertFalse(once.call_args_list[1].args[0]['_jsonObject'])
