import json
import unittest
from copy import deepcopy
from datetime import date
from unittest.mock import patch
from sku_board.tests import test_visual_agent_pipeline as fixture
from sku_board.visual_agents import market_context, market_feedback, adapter, pipeline
from sku_board.visual_agents.store import Store


def record():
    return {'country': 'TH', 'platform': 'Shopee', 'category': 'beauty',
            'observedAt': date.today().isoformat(), 'source': 'internal report test-1',
            'finding': 'One observed campaign, not a general country preference'}


def feedback():
    return {**record(), 'testId': 'test-1', 'comparisonContext': 'same audience and date; price unchanged',
            'variants': [{'direction': 'cool light', 'impressions': 1000, 'clicks': 50, 'conversions': 3},
                         {'direction': 'warm light', 'impressions': 1000, 'clicks': 70, 'conversions': 2}]}


class MarketTests(unittest.TestCase):
    def test_parse_and_separate_from_product_claims(self):
        brief = 'actual product facts\n【市场资料】'+json.dumps([record()])+'【/市场资料】'
        self.assertEqual(len(market_context.read_inputs({'suiteBrief': brief})['marketKnowledge']), 1)
        self.assertEqual(market_context.product_brief(brief), 'actual product facts')
        with self.assertRaises(ValueError):
            market_context.read_inputs({'suiteBrief': '【市场资料】missing close'})
        with self.assertRaises(ValueError):
            market_context.read_inputs({'marketKnowledge': '{}'})

    def test_scope_date_and_metrics(self):
        records = [record(), {**record(), 'country': 'JP'}, {**record(), 'category': 'apparel'},
                   {**record(), 'observedAt': '2000-01-01'}, {**record(), 'platform': 'Lazada'}]
        result = market_context.build({'marketKnowledge': records, 'marketFeedback': [feedback()]},
                                      'TH', 'Shopee', ['beauty'])
        self.assertEqual(len(result['evidence']), 1)
        self.assertEqual(len(result['excluded']), 4)
        self.assertEqual(result['feedback'][0]['variants'][0]['ctr'], .05)
        bad = feedback(); bad['variants'][0]['clicks'] = 1001
        self.assertFalse(market_context.build({'marketKnowledge': [], 'marketFeedback': [bad]},
                                           'TH', 'Shopee', ['beauty'])['feedback'])

    def test_review_keep_and_unknown_ids(self):
        context = {'feedback': [feedback()]}
        result = market_feedback.review(lambda *a: {'decision': 'keep', 'reason': 'insufficient evidence', 'testIds': []},
                                        {'original': 1}, {'original': 2}, context)
        self.assertEqual(result['strategy'], {'original': 1})
        with self.assertRaises(ValueError):
            market_feedback.review(lambda *a: {'decision': 'adjust', 'reason': 'invented', 'testIds': ['fake']}, {}, {}, context)


class PipelineMarketTests(unittest.TestCase):
    setUp = fixture.PipelineTests.setUp
    run_plan = fixture.PipelineTests.run_plan

    def test_default_no_feedback_cost_and_same_dna_on_every_page(self):
        result = self.run_plan()
        self.assertTrue(result['companyPromptStatus']['ready'], result['director']['message'])
        dna = result['director']['visualDNA']
        self.assertEqual(result['director']['feedbackReview']['decision'], 'skipped')
        self.assertEqual(sum(s == 'direction' for s, _ in self.transport.calls), 1)
        for page in result['suitePages']:
            self.assertEqual(page['agentPrompt']['visualDNAId'], dna['id'])
            self.assertIn(dna['id'], page['agentPrompt']['resolvedPrompt'])
        for stage, context in self.transport.calls:
            if stage in {'planning', 'prompts'}:
                self.assertEqual(context['visualDNA']['id'], dna['id'])
        self.assertIn('marketKnowledge', next(c for s,c in self.transport.calls if s == 'strategy'))

    def test_feedback_adjust_once_then_cached_and_submission_compatible(self):
        changes = {'marketFeedback': [feedback()], 'marketKnowledge': [record()], 'platform': 'Shopee'}
        def adjust(call, strategy, direction, context):
            direction = deepcopy(direction)
            direction['colorDirection'] = {'palette': ['#aabbcc'], 'rationale': 'test feedback'}
            return {'decision': 'adjust', 'reason': 'test-scoped finding', 'testIds': ['test-1'],
                    'strategy': strategy, 'direction': direction}
        with patch.object(market_feedback, 'review', side_effect=adjust) as review:
            result = self.run_plan(**changes)
            self.assertTrue(result['companyPromptStatus']['ready'], result['director']['message'])
            second = self.run_plan(**changes)
            self.assertEqual(review.call_count, 1)
        self.assertEqual(second['suitePages'], result['suitePages'])
        self.assertEqual(result['director']['visualDNA']['palette']['palette'], ['#aabbcc'])
        adapter.verify_submission(Store(self.tmp.name), 'fixture-user', result['suitePages'], self.payload,
                                  pipeline.assets_for(self.images))
        self.run_plan(marketKnowledge=[record()])
        self.assertEqual(sum(s == 'product' for s, _ in self.transport.calls), 1)

    def test_feedback_failure_resumes_without_repeating_analysis_or_direction(self):
        with patch.object(market_feedback, 'review', side_effect=TimeoutError('feedback timeout')):
            result = self.run_plan(marketFeedback=[feedback()])
        self.assertFalse(result['companyPromptStatus']['ready'])
        self.assertFalse(any(s == 'prompts' for s, _ in self.transport.calls))
        with patch.object(market_feedback, 'review', side_effect=lambda call,s,d,k: {
                'decision': 'keep', 'reason': 'uncertain data', 'testIds': [], 'strategy': s, 'direction': d}):
            result = self.run_plan(marketFeedback=[feedback()])
        self.assertTrue(result['companyPromptStatus']['ready'], result['director']['message'])
        self.assertEqual(sum(s == 'product' for s, _ in self.transport.calls), 1)
        self.assertEqual(sum(s == 'direction' for s, _ in self.transport.calls), 1)
