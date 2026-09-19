import json
import unittest
from copy import deepcopy
from unittest.mock import patch
from sku_board.tests import test_visual_agent_pipeline as fixture
from sku_board.visual_agents import adapter
from sku_board.visual_agents.store import Store


class SubmissionSyncTests(unittest.TestCase):
    def setUp(self):
        fixture.PipelineTests.setUp(self)
        logger = patch.object(fixture.engine, 'log_ai_image_error')
        logger.start()
        self.addCleanup(logger.stop)
    run_plan = fixture.PipelineTests.run_plan
    def test_stale_client_restored_without_models_and_tampering_still_rejected(self):
        result = self.run_plan()
        stale = deepcopy(result['suitePages'])
        stale[0]['agentPrompt']['creativeInstruction'] = 'stale browser value'
        request = {**self.payload, 'suitePages': stale}
        with patch.object(fixture.engine, 'invoke_ai_director_chat', side_effect=AssertionError('No AI calls')):
            synced = fixture.engine.sync_visual_agent_plan(request, self.actor)
        self.assertEqual(synced['suitePages'], result['suitePages'])
        self.assertTrue(synced['synchronized'])
        self.assertEqual(synced['differences'], [{'page': 1, 'fields': ['agentPrompt']}])
        store = Store(fixture.engine.DATA_DIR)
        with self.assertRaisesRegex(ValueError, 'agentPrompt'):
            adapter.verify_submission(store, self.actor['username'], stale, self.payload)
        adapter.verify_submission(store, self.actor['username'], synced['suitePages'], self.payload)

    def test_sync_enforces_account_and_request(self):
        result = self.run_plan()
        request = {**self.payload, 'suitePages': result['suitePages']}
        for changed in ({'suiteBrief': 'changed'}, {'suiteCountry': 'KR'}, {'size': '1024x1024'}, {'suiteCount': 20}):
            with self.assertRaisesRegex(ValueError, '已变化'):
                fixture.engine.sync_visual_agent_plan({**request, **changed}, self.actor)
        with self.assertRaisesRegex(ValueError, '账号'):
            fixture.engine.sync_visual_agent_plan(request, {**self.actor, 'username': 'another-user'})

    def test_form_upload_crlf_and_json_lf_are_same_request(self):
        brief = self.payload['suiteBrief'] + '\r\n第二行产品需求\r\n第三行'
        result = self.run_plan(suiteBrief=brief)
        request = {**self.payload, 'suiteBrief': brief.replace('\r\n', '\n'), 'suitePages': result['suitePages']}
        synced = fixture.engine.sync_visual_agent_plan(request, self.actor)
        adapter.verify_submission(Store(fixture.engine.DATA_DIR), self.actor['username'], synced['suitePages'], request)
        with self.assertRaisesRegex(ValueError, '已变化'):
            fixture.engine.sync_visual_agent_plan({**request, 'suiteBrief': request['suiteBrief'] + '新增需求'}, self.actor)

    def test_partial_and_mixed_plans_never_dispatched(self):
        self.transport.fail = 'prompts'
        result = self.run_plan()
        request = {**self.payload, 'suitePages': result['suitePages']}
        with self.assertRaisesRegex(ValueError, '尚未完整'):
            fixture.engine.sync_visual_agent_plan(request, self.actor)
        request['suitePages'][0]['agentPlanId'] = 'other-plan'
        with self.assertRaisesRegex(ValueError, '版本混用'):
            fixture.engine.sync_visual_agent_plan(request, self.actor)

    def test_synced_plan_reaches_existing_provider_without_ai(self):
        from sku_board.tests.test_visual_agent_compatibility import ReachedImageProvider
        result = self.run_plan()
        stale = deepcopy(result['suitePages'])
        stale[-1]['agentSpec']['scene'] = 'old scene'
        before = len(self.transport.calls)
        synced = fixture.engine.sync_visual_agent_plan({**self.payload, 'suitePages': stale}, self.actor)
        fields = {**self.payload, 'suitePlan': json.dumps(synced['suitePages']), 'suitePageIndexes': '[1]',
                  'model': 'gpt-image-2', 'mode': 'edit', 'quality': 'high', 'count': '1',
                  'prompt': self.payload['suiteBrief']}
        with patch.object(fixture.engine, 'read_ai_image_upload', return_value=self.images[0]), \
                patch.object(fixture.engine, 'chatgpt2api_image_tasks_enabled', return_value=True), \
                patch.object(fixture.engine, 'generate_ai_image_tasks_with_transient_retry', side_effect=ReachedImageProvider) as provider:
            with self.assertRaises(ReachedImageProvider):
                fixture.engine.generate_ad_launch_ai_image_edit(fields, {'reference0': object()}, self.actor)
        self.assertEqual(len(self.transport.calls), before)
        self.assertEqual(provider.call_args.kwargs['prompts'][0], result['suitePages'][0]['agentPrompt']['resolvedPrompt'])
