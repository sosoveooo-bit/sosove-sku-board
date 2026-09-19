import threading
import unittest
from unittest.mock import patch
from sku_board.tests import test_visual_agent_pipeline as fixture
from sku_board.visual_agents.store import Store, Busy
from sku_board.visual_agents import pipeline


class CacheTests(unittest.TestCase):
    setUp = fixture.PipelineTests.setUp
    run_plan = fixture.PipelineTests.run_plan

    def test_cross_store_lease_and_owner_isolation(self):
        a, b = Store(self.tmp.name), Store(self.tmp.name)
        with a.lease('alice', 'product-key'):
            with self.assertRaises(Busy):
                with b.lease('alice', 'product-key'):
                    pass
            with b.lease('bob', 'product-key'):
                pass
        with b.lease('alice', 'product-key'):
            pass

    def test_style_change_does_not_invalidate_product_analysis(self):
        assets = pipeline.assets_for(self.images + [('style.jpg', b'style-v1', 'image/jpeg')],
                                     [{'index': 1, 'role': 'product'}, {'index': 2, 'role': 'layout'}])
        other = pipeline.assets_for(self.images + [('style.jpg', b'style-v2', 'image/jpeg')],
                                    [{'index': 1, 'role': 'product'}, {'index': 2, 'role': 'styleSet'}])
        self.assertEqual(pipeline.product_intelligence.cache_key(assets, self.payload),
                         pipeline.product_intelligence.cache_key(other, self.payload))

    def test_partial_prompt_failure_resumes_without_repeating_other_agents(self):
        original = self.transport.__call__
        failed = False

        def respond(settings, messages):
            nonlocal failed
            if len([s for s, _ in self.transport.calls if s == 'prompts']) == 1 and not failed:
                failed = True
                raise TimeoutError('fixture stopped after first batch')
            return original(settings, messages)

        with patch.object(fixture.engine, 'invoke_ai_director_chat', side_effect=respond):
            partial = self.run_plan()
        self.assertEqual(partial['companyPromptStatus']['readyCount'], 3)
        result = self.run_plan()
        self.assertTrue(result['companyPromptStatus']['ready'])
        for stage in ('product', 'strategy', 'direction', 'planning'):
            self.assertEqual(sum(s == stage for s, _ in self.transport.calls), 1)
        resumed = [ctx['pages'] for s, ctx in self.transport.calls if s == 'prompts']
        self.assertEqual([p['page'] for p in resumed[1]], [4, 5, 6])

    def test_cancel_after_product_preserves_completed_analysis(self):
        original = self.transport.__call__

        def respond(settings, messages):
            if 'marketing strategist' in messages[0]['content']:
                raise fixture.engine.image_cancellation.OperationCancelled('fixture cancel')
            return original(settings, messages)

        with patch.object(fixture.engine, 'invoke_ai_director_chat', side_effect=respond):
            with self.assertRaises(fixture.engine.image_cancellation.OperationCancelled):
                self.run_plan()
        self.assertTrue(self.run_plan()['director']['productCacheHit'])
