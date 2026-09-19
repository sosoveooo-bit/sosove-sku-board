"""Offline shot-allocation, saved-plan and director-batch regressions."""
from contextlib import ExitStack
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from sku_board import backend, cod_visual_diversity as diversity


class CodVisualDiversityTests(unittest.TestCase):
    def setUp(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        for target in ('requests.sessions.Session.request', 'urllib.request.urlopen'):
            stack.enter_context(patch(target, side_effect=AssertionError('Unexpected network call')))
        self.model = stack.enter_context(patch.object(
            backend, 'invoke_ai_director_chat', side_effect=AssertionError('Unexpected model call')))

    def pages(self, count=8):
        return [{'page': n, 'country': 'DE', 'focusTitle': '庭院的阴凉角落',
                 'focusDescription': '让庭院空间更有层次', 'headline': 'Gartenfreude',
                 'scene': 'A woman in the same garden', 'pose': 'woman holding the same pot',
                 'visualEnhancement': {
                     'camera': 'Eye level 50mm medium portrait of the pot',
                     'spatialPlan': 'Center pot and woman at right with title above and badges at left',
                     'actionDirection': 'A woman touches the plant with one hand',
                     'companyPromptLayers': {field: (
                         'A woman kneels next to a green potted plant in the garden, with the pot centered, '
                         'her face at upper right and marketing labels in a left column.'
                         if field == 'visualNarrative' else 'Product-specific offline page direction')
                         for field in backend.AI_IMAGE_JP_COMPANY_PROMPT_LAYER_FIELDS},
                 }} for n in range(1, count + 1)]

    def test_allocation_is_stable_non_mutating_and_varies_adjacent_axes(self):
        pages = self.pages(30)
        original = deepcopy(pages)
        records = diversity.contracts(pages)
        self.assertEqual(records, diversity.contracts(pages))
        self.assertEqual(pages, original)
        combinations = {(r['shotScale'], r['viewpoint'], r['copyPlacement']) for r in records}
        self.assertEqual(len(combinations), 30)
        for before, after in zip(records, records[1:]):
            changes = sum(before[k] != after[k] for k in ('shotScale', 'viewpoint', 'copyPlacement'))
            self.assertGreaterEqual(changes, 2)
        self.model.assert_not_called()

    def test_evidence_family_limits_choices_not_inherited_scene(self):
        sources = ['柔软纹理', '清洗步骤', '配色', '结构原理', '亲子互动', '规格参数']
        pages = [{'page': i, 'focusDescription': source, 'scene': 'woman holding product'}
                 for i, source in enumerate(sources, 1)]
        records = diversity.contracts(pages)
        self.assertEqual([r['evidenceFamily'] for r in records],
                         ['macro', 'process', 'color', 'mechanism', 'lifestyle', 'specification'])
        for record in records:
            self.assertIn(record['shotScale'], diversity.SCALES[record['evidenceFamily']])
        self.assertEqual(records[0]['peopleIntent'], 'product-led-no-decorative-portrait')
        self.assertEqual(records[4]['peopleIntent'], 'interaction-required-by-source')

    def test_repetition_ignores_headline_and_color_swaps(self):
        pages = self.pages(2)
        pages[1]['headline'] = 'A different headline'
        layers = pages[1]['visualEnhancement']['companyPromptLayers']
        layers['visualNarrative'] = layers['visualNarrative'].replace('green', 'purple')
        self.assertEqual(diversity.repeated_designs(pages), {2: [1]})
        self.assertEqual(diversity.contracts(pages)[1]['repeatedDesignPages'], [1])

    def test_shared_palette_alone_is_not_repetition(self):
        pages = [{'page': n, 'visualEnhancement': {'companyPromptLayers': {
            'colorScheme': 'Same cream and green palette', 'styleDirection': 'German garden photography'}}}
            for n in (1, 2)]
        self.assertEqual(diversity.repeated_designs(pages), {})

    def test_planning_batches_share_whole_suite_allocation(self):
        pages = self.pages()
        records = diversity.contracts(pages)
        analysis = {'_codVisualDiversity': records, '_suitePageCount': len(pages)}
        for subset in (pages[:3], pages[3:6]):
            messages = backend.build_ai_director_page_refinement_messages(
                subset, analysis, backend.AI_IMAGE_COD_SUITE_KEY, 'DE')
            text = '\n'.join(m['content'] for m in messages if isinstance(m['content'], str))
            matrix_text = text.split('[COD WHOLE-SUITE SHOT ALLOCATION]\n')[1].split('\n')[0]
            matrix = json.loads(matrix_text)
            self.assertEqual(len(matrix), 8)
            self.assertEqual([r['shotScale'] for r in matrix], [r['shotScale'] for r in records])
            self.assertNotIn('"localPrevisualization"', text)
            self.assertIn('inheritedSceneSuggestions', text)
            self.assertIn('Explicit user camera, scene, layout and people instructions take priority', text)
        self.model.assert_not_called()

    def test_current_saved_country_and_detail_plans_get_contract_in_final_prompt(self):
        brief = '主卖点：\n1. 庭院装饰：阴凉角落的真实使用。\n2. 配色：按参考图保持真实颜色。'
        for suite in (backend.AI_IMAGE_COD_SUITE_KEY, backend.AI_IMAGE_COD_DETAIL_SUITE_KEY):
            with self.subTest(suite=suite):
                pages = backend.build_ai_image_suite_plan('庭院植物', brief, '750x1000',
                    suite_key=suite, country='DE', count=24)
                for page in pages:
                    page['visualEnhancement'] = deepcopy(self.pages(1)[0]['visualEnhancement'])
                original = deepcopy(pages)
                prompts, _ = backend.build_ai_image_suite_prompts('庭院植物', brief, '750x1000',
                    suite_key=suite, country='DE', suite_count=24, plan=pages)
                self.assertEqual(pages, original)
                for prompt in prompts:
                    self.assertIn('[COD PAGE VISUAL DIVERSITY', prompt)
                    self.assertIn('[COD ARTWORK LANGUAGE BOUNDARY', prompt)
                    self.assertIn(brief, prompt)
                    self.assertIn('preserve all assigned supporting benefits', prompt)
                    if 'has_human=true' in prompt:
                        self.assertIn('Human presence is permitted, not mandatory', prompt)
                self.assertIn('"repeatedDesignPages":[1]', prompts[1])
        self.model.assert_not_called()

    def test_no_text_and_explicit_user_locks_outrank_auto_allocation(self):
        record = diversity.contracts(self.pages(1))[0]
        prompt = backend.ai_image_cod_company_remote_authored_execution_prompt(
            self.pages(1)[0], 'product', 24, '不要任何文字；所有图保持俯拍，无人物。',
            diversity_contract=record)
        self.assertIn('No visible added text', prompt)
        self.assertIn('when text-free ignore copy placement entirely', prompt)
        self.assertIn('Explicit user camera, scene, layout and people instructions take priority', prompt)
        self.assertIn('不要任何文字；所有图保持俯拍，无人物。', prompt)

    def test_non_cod_director_has_no_diversity_contract(self):
        messages = backend.build_ai_director_page_refinement_messages(
            self.pages(1), {}, backend.AI_IMAGE_LANDING_SUITE_KEY, 'JP')
        text = '\n'.join(m['content'] for m in messages if isinstance(m['content'], str))
        self.assertNotIn('[COD WHOLE-SUITE SHOT ALLOCATION]', text)


if __name__ == '__main__':
    unittest.main()
