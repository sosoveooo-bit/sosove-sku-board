import json
import unittest
from unittest.mock import patch
from sku_board.tests import test_visual_agent_pipeline as fixture
from sku_board.visual_agents import pipeline


class ReachedImageProvider(Exception):
    pass


class CompatibilityTests(unittest.TestCase):
    setUp = fixture.PipelineTests.setUp

    def run_plan(self, **changes):
        # Build a historical Agent checkpoint directly. New HTTP planning now
        # uses GitHub's COD route; these tests cover saved-plan compatibility.
        return pipeline.run(fixture.engine, {**self.payload, **changes}, self.actor, self.images)

    def test_real_upload_stream_is_read_once_for_validation_and_dispatch(self):
        import io
        from types import SimpleNamespace
        result = self.run_plan()
        fields = {**self.payload, 'suitePlan': json.dumps(result['suitePages']), 'suitePageIndexes': '[1]',
                  'model': 'gpt-image-2', 'mode': 'edit', 'quality': 'high', 'count': '1',
                  'prompt': self.payload['suiteBrief']}
        name, data, mime = self.images[0]
        upload = SimpleNamespace(filename=name, file=io.BytesIO(data), type=mime)
        with patch.object(fixture.engine, 'chatgpt2api_image_tasks_enabled', return_value=True), \
                patch.object(fixture.engine, 'generate_ai_image_tasks_with_transient_retry', side_effect=ReachedImageProvider) as provider:
            with self.assertRaises(ReachedImageProvider):
                fixture.engine.generate_ad_launch_ai_image_edit(fields, {'reference0': upload}, self.actor)
        self.assertEqual(provider.call_args.kwargs['reference_images_by_page'][0], self.images)
        self.assertEqual(upload.file.tell(), len(data))

    def test_existing_image_submission_receives_independent_prompt_and_references(self):
        result = self.run_plan()
        fields = {**self.payload, 'suitePlan': json.dumps(result['suitePages']), 'suitePageIndexes': '[1]',
                  'model': 'gpt-image-2', 'mode': 'edit', 'quality': 'high', 'count': '1',
                  'prompt': self.payload['suiteBrief']}
        captured = {}

        def image_provider(**kwargs):
            captured.update(kwargs)
            raise ReachedImageProvider()

        before = len(self.transport.calls)
        with patch.object(fixture.engine, 'read_ai_image_upload', return_value=self.images[0]), \
                patch.object(fixture.engine, 'chatgpt2api_image_tasks_enabled', return_value=True), \
                patch.object(fixture.engine, 'generate_ai_image_tasks_with_transient_retry', side_effect=image_provider):
            with self.assertRaises(ReachedImageProvider):
                fixture.engine.generate_ad_launch_ai_image_edit(fields, {'reference0': object()}, self.actor)
        self.assertEqual(len(self.transport.calls), before)
        self.assertEqual(captured['prompts'][0], result['suitePages'][0]['agentPrompt']['resolvedPrompt'])
        self.assertEqual(captured['page_indexes'], [0])
        self.assertEqual(captured['reference_images_by_page'][0], self.images)

    def test_detail_count_and_old_function_paths_preserved(self):
        result = self.run_plan(suiteKey='cod-country-detail-12', suiteCount=22)
        self.assertTrue(result['companyPromptStatus']['ready'], result['director']['message'])
        self.assertEqual(len(result['suitePages']), 22)
        self.assertTrue(all(p['section'] == 'detail' for p in result['suitePages']))
        with patch.object(pipeline, 'run', side_effect=AssertionError('unexpected new flow')):
            old = fixture.engine.plan_ai_image_suite({**self.payload, 'suiteKey': 'jp-landing-page-25',
                                                       'suiteCount': 25, 'size': '1500x2000', 'useDirector': False}, self.actor)
        self.assertEqual(old['suiteKey'], 'jp-landing-page-25')

    def test_style_assets_do_not_reach_image_provider_and_hero_is_single(self):
        style = ('style.png', b'style-only', 'image/png')
        product = self.images[0]
        self.images = [style, product, ('detail.png', b'detail-view', 'image/png')]
        bindings = [{'index': 1, 'role': 'style'}, {'index': 2, 'role': 'product'}, {'index': 3, 'role': 'detail'}]
        result = pipeline.run(fixture.engine, self.payload, self.actor, self.images, bindings)
        self.assertTrue(result['companyPromptStatus']['ready'], result['director']['message'])
        fields = {**self.payload, 'suitePlan': json.dumps(result['suitePages']), 'suitePageIndexes': '[1]',
                  'model': 'gpt-image-2', 'mode': 'edit', 'quality': 'high', 'count': '1',
                  'prompt': self.payload['suiteBrief'], 'referenceBindings': json.dumps(bindings), 'heroAB': 'true'}
        captured = {}
        def provider(**kwargs):
            captured.update(kwargs)
            raise ReachedImageProvider()
        with patch.object(fixture.engine, 'read_ai_image_upload', side_effect=lambda item, *args: item), \
                patch.object(fixture.engine, 'chatgpt2api_image_tasks_enabled', return_value=True), \
                patch.object(fixture.engine, 'generate_ai_image_tasks_with_transient_retry', side_effect=provider):
            with self.assertRaises(ReachedImageProvider):
                fixture.engine.generate_ad_launch_ai_image_edit(fields,
                    {f'reference{i}': image for i, image in enumerate(self.images)}, self.actor)
        self.assertEqual(len(captured['prompts']), 1)
        self.assertEqual(captured['reference_images_by_page'][0], [product])

    def test_changed_reference_rejected_before_provider(self):
        result = self.run_plan()
        fields = {**self.payload, 'suitePlan': json.dumps(result['suitePages']), 'suitePageIndexes': '[1]',
                  'model': 'gpt-image-2', 'mode': 'edit', 'quality': 'high', 'count': '1', 'prompt': self.payload['suiteBrief']}
        with patch.object(fixture.engine, 'read_ai_image_upload', return_value=('x.png', b'changed-product', 'image/png')), \
                patch.object(fixture.engine, 'generate_ai_image_tasks_with_transient_retry') as provider:
            with self.assertRaisesRegex(ValueError, '参考图已变化'):
                fixture.engine.generate_ad_launch_ai_image_edit(fields, {'reference0': object()}, self.actor)
        provider.assert_not_called()
