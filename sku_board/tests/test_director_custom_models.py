import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from sku_board import backend, image_cancellation


class DirectorCustomModelTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.file = Path(temporary.name) / 'director.json'
        for context in (
            patch.object(backend, 'DATA_DIR', Path(temporary.name)),
            patch.object(backend, 'AI_DIRECTOR_SETTINGS_FILE', self.file),
            patch.dict(os.environ, {}, clear=True),
        ):
            context.start()
            self.addCleanup(context.stop)

    def save(self, **changes):
        return backend.save_ai_director_settings(changes, {'role': 'admin'})['director']

    def test_catalog_includes_deepseek_without_changing_primary_or_fallbacks(self):
        current = backend.load_ai_director_settings()
        public = backend.public_ai_director_settings(current)
        self.assertIn('deepseek-v4.1-flash', public['availableModels'])
        self.assertEqual(public['model'], 'gpt-5.6-terra')
        self.assertEqual(public['modelChain'], ['gpt-5.6-terra', 'gpt-5.6-sol'])
        self.assertNotIn('deepseek-v4.1-flash', current['fallbackModels'])

    def test_custom_names_survive_save_reload_and_primary_switch(self):
        self.save(model='Vendor/Model-v2:latest', customModels=['Vendor/Model-v2:latest', 'my-alias'])
        second = self.save(model='deepseek-v4.1-flash')
        self.assertEqual(second['customModels'], ['Vendor/Model-v2:latest', 'my-alias'])
        reloaded = backend.get_ai_director_settings({'role': 'admin'})['director']
        self.assertEqual(reloaded['customModels'], second['customModels'])
        self.assertIn('Vendor/Model-v2:latest', reloaded['availableModels'])
        self.assertEqual(reloaded['model'], 'deepseek-v4.1-flash')

    def test_old_unknown_primary_remains_selectable_and_is_remembered(self):
        self.file.write_text(json.dumps({'model': 'Legacy/Custom-Name', 'timeout': 120}), encoding='utf-8')
        public = backend.get_ai_director_settings({'role': 'admin'})['director']
        self.assertIn('Legacy/Custom-Name', public['availableModels'])
        self.assertEqual(public['customModels'], ['Legacy/Custom-Name'])
        self.save(model='gpt-5.6-sol')  # Older clients can omit customModels.
        self.assertEqual(backend.load_ai_director_settings()['customModels'], ['Legacy/Custom-Name'])

    def test_ids_trim_deduplicate_and_keep_exact_case_without_alias_rewrite(self):
        public = self.save(model=' Vendor/Model ', customModels=[
            'Vendor/Model', ' Vendor/Model ', 'vendor/model', 'deepseek-v4.1-flash', 'gpt-5.6-sol',
        ])
        self.assertEqual(public['model'], 'Vendor/Model')
        self.assertEqual(public['customModels'], ['Vendor/Model', 'vendor/model'])
        self.assertEqual(public['availableModels'].count('Vendor/Model'), 1)

    def test_rejects_invalid_model_fields_without_replacing_saved_settings(self):
        self.save(model='gpt-5.6-sol')
        before = self.file.read_bytes()
        for changes in (
            {'model': ''}, {'model': 3}, {'model': 'with space'}, {'model': 'a\nb'},
            {'model': 'x' * 121}, {'customModels': 'not-a-list'}, {'customModels': [None]},
            {'customModels': ['has\x00control']}, {'customModels': ['x' * 121]},
            {'customModels': [f'model-{n}' for n in range(51)]},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.save(**changes)
            self.assertEqual(self.file.read_bytes(), before)

    def test_selected_custom_model_counts_toward_limit(self):
        models = [f'custom-{n}' for n in range(50)]
        self.assertEqual(len(self.save(model=models[0], customModels=models)['customModels']), 50)
        with self.assertRaisesRegex(ValueError, '50'):
            self.save(model='one-more')

    def test_permissions_secret_and_shared_runtime_boundaries(self):
        self.save(model='deepseek-v4.1-flash', apiKey='private-fixture-key', baseUrl='https://fixture.invalid/v1',
                  enabled=True, customModels=['my-custom-model'])
        public = self.save(apiKey='')
        self.assertEqual(backend.load_ai_director_settings()['apiKey'], 'private-fixture-key')
        self.assertNotIn('private-fixture-key', json.dumps(public))
        for operation in (
            lambda: backend.get_ai_director_settings({'role': 'ops'}),
            lambda: backend.save_ai_director_settings({'customModels': ['denied']}, {'role': 'ops'}),
        ):
            with self.assertRaisesRegex(ValueError, '只有管理员'):
                operation()
        shared = backend.shared_ai_director_runtime_settings()
        for key in ('apiKey', 'baseUrl', 'customModels', 'availableModels'):
            self.assertNotIn(key, shared)

    def test_saving_catalog_does_not_call_ai_or_expand_runtime_chain(self):
        with patch.object(backend, 'invoke_ai_director_chat') as ai:
            before = self.save(model='gpt-5.6-sol', fallbackModels=['gpt-5.6-terra'])
            after = self.save(customModels=['custom-A', 'custom-B'])
            ai.assert_not_called()
        self.assertEqual(after['modelChain'], before['modelChain'])
        self.assertEqual(after['fallbackModels'], before['fallbackModels'])

    def test_selected_model_reaches_existing_request_unchanged(self):
        for model in ('deepseek-v4.1-flash', 'Vendor/Exact-ID:latest'):
            with self.subTest(model=model):
                self.save(model=model, apiKey='fixture', baseUrl='https://fixture.invalid/v1', enabled=True)
                settings = backend.load_ai_director_settings()
                session = MagicMock()
                response = MagicMock(ok=True)
                response.json.return_value = {'choices': [{'message': {'content': '{"ok":true}'}}]}
                with patch('requests.Session', return_value=session), patch.object(image_cancellation, 'post', return_value=response) as post:
                    result, _ = backend.invoke_ai_director_chat(settings, [{'role': 'user', 'content': 'Return json.'}])
                self.assertEqual(result, '{"ok":true}')
                self.assertEqual(post.call_count, 1)
                self.assertEqual(post.call_args.kwargs['json']['model'], model)


if __name__ == '__main__':
    unittest.main()
