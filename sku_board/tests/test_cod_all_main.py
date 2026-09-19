"""Country main-only mode leaves the separate detail suite and saved sections intact."""
from copy import deepcopy
import unittest
from unittest.mock import patch
from sku_board import backend


class AllMainTests(unittest.TestCase):
    BRIEF = '主卖点：\n1. 庭院装饰：用于阴凉角落。\n2. 多种颜色：按照参考图配色。\n3. 易于种植：按说明种植。\n4. 便于搭配：适用于庭院布置。\n5. 叶片纹理：叶片细节清晰。'

    def test_all_supported_country_counts_are_main_including_legacy_split_text(self):
        with patch.object(backend, 'invoke_ai_director_chat', side_effect=AssertionError('No model calls')):
            for count in (8, 12, 24, 30, 37):
                for suffix in ('', '\n10张主图＋20张详情图'):
                    with self.subTest(count=count,suffix=suffix):
                        brief = self.BRIEF + suffix
                        self.assertEqual(backend.ai_image_cod_country_section_counts(brief,count),(count,0))
                        pages = backend.build_ai_image_suite_plan('植物',brief,'750x1000',
                            suite_key=backend.AI_IMAGE_COD_SUITE_KEY,country='DE',count=count)
                        self.assertEqual(len(pages),count)
                        self.assertTrue(all(p['section']=='主图' for p in pages))
                        self.assertTrue(all(p['role'].startswith('主图') for p in pages))
                        self.assertEqual([int(p['sectionIndex']) for p in pages],list(range(1,count+1)))
                        _, compiled = backend.build_ai_image_suite_prompts('植物',brief,'750x1000',
                            suite_key=backend.AI_IMAGE_COD_SUITE_KEY,country='DE',suite_count=count,plan=pages)
                        self.assertTrue(all(p.get('codMainRich') for p in compiled))
                        self.assertTrue(all(3<=len(p.get('codMainSupportingPoints',[]))<=5 for p in compiled))

    def test_separate_detail_and_saved_explicit_sections_remain_detail(self):
        self.assertFalse(backend.ai_image_cod_page_is_main({'page':1},backend.AI_IMAGE_COD_DETAIL_SUITE_KEY))
        old={'page':16,'section':'详情','sectionIndex':'1'}
        before=deepcopy(old)
        self.assertFalse(backend.ai_image_cod_page_is_main(old))
        self.assertEqual(old,before)
