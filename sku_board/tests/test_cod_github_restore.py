"""Offline routing regressions for the scoped GitHub COD restoration."""
import json
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from sku_board import backend


class CodGithubRestoreTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for target in ('requests.sessions.Session.request', 'urllib.request.urlopen'):
            self.stack.enter_context(patch(target, side_effect=AssertionError('Unexpected external request')))
        self.stack.enter_context(patch.object(backend, 'can_use_ai_image', return_value=True))
        self.stack.enter_context(patch.object(backend, 'shared_ai_director_enabled', return_value=False))
        self.stack.enter_context(patch.object(backend, 'public_ai_director_settings', return_value={'enabled': False}))
        self.agent = self.stack.enter_context(patch.object(backend.visual_pipeline, 'run',
                                                          side_effect=AssertionError('Old Agent route selected')))
        self.model = self.stack.enter_context(patch.object(backend, 'invoke_ai_director_chat',
                                                          side_effect=AssertionError('Unexpected model request')))

    def test_cod_new_and_stale_browser_requests_use_github_planner(self):
        brief = ('主卖点：\n1. 防滑握柄：握持稳定。\n2. 省力开盖：便于日常使用。\n'
                 '3. 小巧收纳：节省厨房空间。\n4. 清洁方便：表面易擦拭。\n'
                 '5. 多场景使用：用于家庭厨房。\n6. 轻便结构：方便拿取。')
        for suite, count in ((backend.AI_IMAGE_COD_SUITE_KEY, 24),
                             (backend.AI_IMAGE_COD_DETAIL_SUITE_KEY, 12)):
            for stale_agent_flag in (False, True):
                with self.subTest(suite=suite, stale_agent_flag=stale_agent_flag):
                    payload = {'suiteKey': suite, 'suiteCount': count, 'suiteCountry': 'DE',
                               'size': '750x1000', 'prompt': '厨房开盖工具', 'suiteBrief': brief,
                               'useDirector': False}
                    if stale_agent_flag:
                        payload['visualPipelineVersion'] = 'cod-visual-agents-v1'
                    result = backend.plan_ai_image_suite(payload, {'username': 'offline-fixture'})
                    self.assertEqual(len(result['suitePages']), count)
                    self.assertNotIn('visualPipelineVersion', result)
                    self.assertTrue(all('agentSpec' not in page for page in result['suitePages']))
                    if suite == backend.AI_IMAGE_COD_SUITE_KEY:
                        self.assertTrue(any(len(p.get('codMainSupportingPoints', [])) >= 3
                                            for p in result['suitePages']))
        self.agent.assert_not_called()
        self.model.assert_not_called()

    def test_historical_agent_prompt_submission_keeps_compatibility(self):
        pages = [{'page': 1, 'visualPipelineVersion': 'cod-visual-agents-v1'}]
        with patch.object(backend.visual_adapter, 'normalize_pages', return_value=pages), \
             patch.object(backend.visual_adapter, 'compile_pages', return_value=(['saved prompt'], pages)) as compile_saved:
            prompts, result = backend.build_ai_image_suite_prompts(
                'original', 'original', suite_key=backend.AI_IMAGE_COD_SUITE_KEY,
                suite_count=24, country='DE', plan=pages)
        self.assertEqual(prompts, ['saved prompt'])
        self.assertEqual(result, pages)
        compile_saved.assert_called_once()
        self.model.assert_not_called()

    def test_incomplete_github_prompt_still_stops_before_image_dispatch(self):
        payload = {'suiteKey': backend.AI_IMAGE_COD_SUITE_KEY, 'suiteCount': 24,
                   'suiteCountry': 'DE', 'size': '750x1000', 'prompt': '厨房工具',
                   'suiteBrief': '主卖点：\n1. 防滑握柄：握持稳定。', 'useDirector': False}
        planned = backend.plan_ai_image_suite(payload, {'username': 'offline-fixture'})
        fields = {**payload, 'suitePlan': json.dumps(planned['suitePages']),
                  'suitePageIndexes': '[0]', 'mode': 'edit', 'count': 1, 'model': 'gpt-image-2'}
        with patch.object(backend, 'normalize_ai_image_request_fields',
                          return_value=('厨房工具', 'gpt-image-2', '750x1000', 'high', 1, 10, 1)), \
             patch.object(backend, 'generate_ai_image_tasks_with_transient_retry') as dispatch:
            with self.assertRaisesRegex(ValueError, '七层Prompt'):
                backend.generate_ad_launch_ai_image_edit(fields, {}, {'role': 'admin'})
        dispatch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
