import unittest
from unittest.mock import patch
from pathlib import Path
from sku_board import backend, cod_visual_routes


class SourceDrivenTests(unittest.TestCase):
    def test_stale_false_flag_still_blocks_incomplete_pages(self):
        for suite in backend.AI_IMAGE_COD_COUNTRY_SUITE_KEYS:
            with self.subTest(suite=suite), patch.object(backend, "generate_images_via_chatgpt2api_tasks") as provider:
                with self.assertRaisesRegex(ValueError, "七层Prompt"):
                    backend.generate_ad_launch_ai_image_edit({
                        "prompt":"Exact product", "suiteBrief":"主卖点：柔软触感", "mode":"edit",
                        "model":"gpt-image-2", "size":"750x1000", "count":"1", "suiteKey":suite,
                        "suitePageIndexes":"[1]", "companyEffectMode":"false",
                    }, {}, {"role":"admin"})
                provider.assert_not_called()

    def page(self, number=1):
        return {"page": number, "country": "JP", "headline": "触感を楽しむ", "focusDescription": "柔软触感",
                "sourcePointVerbatim": "完整来源卖点", "size": "750x1000", "visualEnhancement": {
                    "companyPromptLayers": {k: ('A close macro photograph of the source product.' if k=='visualNarrative' else 'Specific page direction') for k in backend.AI_IMAGE_JP_COMPANY_PROMPT_LAYER_FIELDS}}}

    def test_source_not_generic_scene_selects_family(self):
        pages=[{"page":1,"focusDescription":"柔软纹理","scene":"母女桌面"},
               {"page":2,"focusDescription":"六色色彩","scene":"母女桌面"},
               {"page":3,"focusDescription":"亲子互动","scene":"母女桌面"}]
        self.assertEqual([r['evidenceFamily'] for r in cod_visual_routes.assignments(pages)],['macro','color','lifestyle'])

    def test_original_brief_is_present_unabridged(self):
        original='用户卖点原文甲乙丙。'*1100
        out=backend.ai_image_cod_company_remote_authored_execution_prompt(self.page(),'real source product',3,original)
        self.assertIn(original,out)
        self.assertTrue(out.startswith('[COMPANY COD EXECUTION]'))
        self.assertLess(out.index('Finished-photograph'),out.index(original))

    def test_generic_headline_is_not_frozen(self):
        page=self.page(); page['headline']=backend.AI_IMAGE_JP_HEADLINES[2]
        out=backend.ai_image_cod_company_remote_authored_execution_prompt(page,'product',3,'柔软触感')
        self.assertNotIn('「'+page['headline']+'」',out)

    def test_visual_headline_survives_normalization(self):
        self.assertEqual(backend.normalize_ai_director_visual_enhancement({'localizedHeadline':'ふわっと立体に'})['localizedHeadline'],'ふわっと立体に')

    def test_non_cod_versions_unchanged(self):
        self.assertEqual(backend.AI_IMAGE_RAKUTEN_PLAN_VERSION,'rakuten-fashion-commerce-v10-textfree-1500')
        self.assertEqual(backend.AI_IMAGE_AMAZON_APLUS_PLAN_VERSION,'amazon-aplus-v8-quality-optimization')

    def test_render_guard_does_not_depend_on_mode_flag(self):
        source=Path(backend.__file__).read_text(encoding='utf-8')
        guard=source.split('company_prompt_execution = (',1)[1].split('style_anchor_requested =',1)[0]
        self.assertNotIn('fields.get("companyEffectMode")',guard)
        self.assertIn('ai_image_company_prompt_status',guard)
