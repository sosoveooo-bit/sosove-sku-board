import json
import unittest
from copy import deepcopy
from unittest.mock import patch

from sku_board.tests import test_visual_agent_pipeline as fixture
from sku_board.visual_agents import planning_batches, scene_planner
from sku_board.visual_agents.structured_output import parse, StructuredOutputError, OutputTruncated
from sku_board.visual_agents.scheduling import PlanningYield
from sku_board.visual_agents.store import Store


class ParserBoundaryTests(unittest.TestCase):
    def test_truncated_outer_document_cannot_promote_nested_objects(self):
        for source in ('{"pages":[{"page":1}, {"page":2',
                       '{"metadata":{"pages":[{"page":1}]}, "tail":',
                       '```json\n{"pages":[{"page":1},',
                       '{"meta":{"name":"x"},"tail":'):
            with self.subTest(source=source), self.assertRaisesRegex(StructuredOutputError, '不完整'):
                parse(source, {'pages': []} if 'pages' in source else {'name': ''})

    def test_valid_preface_object_does_not_hide_later_complete_result(self):
        self.assertEqual(parse('note {"ignored":1}\n{"pages":[{"page":2}]}', {'pages': []}),
                         {'pages': [{'page': 2}]})

    def test_complete_wrappers_remain_compatible_but_truncated_wrappers_fail(self):
        for wrapper in ('data', 'result', 'output', 'response', 'plan', 'answer'):
            source = json.dumps({wrapper: {'pages': [{'page': 1}]}})
            self.assertEqual(parse(source, {'pages': []}), {'pages': [{'page': 1}]})
            with self.assertRaisesRegex(StructuredOutputError, '不完整'):
                parse(source[:-1], {'pages': []})


class PlanningBatchTests(unittest.TestCase):
    setUp = fixture.PipelineTests.setUp
    run_plan = fixture.PipelineTests.run_plan

    def state(self, result):
        return Store(self.tmp.name).get(self.actor['username'], 'plan', result['agentPlanId'])

    def test_30_pages_keep_global_context_and_are_saved_in_four_batches(self):
        result = self.run_plan(suiteCount=30)
        self.assertTrue(result['companyPromptStatus']['ready'], result['director']['message'])
        contexts = [ctx for stage, ctx in self.transport.calls if stage == 'planning']
        self.assertEqual([ctx['requestedPageNumbers'] for ctx in contexts],
                         [list(range(1,9)), list(range(9,17)), list(range(17,25)), list(range(25,31))])
        self.assertTrue(all(ctx['pageCount'] == 30 for ctx in contexts))
        self.assertEqual([len(ctx['existingPageSummaries']) for ctx in contexts], [0,8,16,24])
        self.assertEqual(contexts[0]['uncoveredSourceIds'], ['S1'])
        self.assertEqual(contexts[-1]['uncoveredSourceIds'], [])
        self.assertEqual(len(self.state(result)['planning']), 30)

    def test_length_stop_shrinks_without_retrying_same_large_request(self):
        attempted = []
        def transport(settings, messages):
            ctx = json.loads(messages[1]['content'][0]['text'])
            if messages[0]['content'].startswith('Plan all'):
                numbers = ctx['requestedPageNumbers']
                attempted.append(numbers)
                if len(numbers) > 4:
                    settings['_lastDirectorCall'] = {'finishReason': 'length', 'model': 'fixture'}
                    return '{"pages":[{"page":1}', 1
            return self.transport(settings, messages)
        with patch.object(fixture.engine, 'invoke_ai_director_chat', side_effect=transport):
            result = self.run_plan()
        self.assertTrue(result['companyPromptStatus']['ready'], result['director']['message'])
        self.assertEqual(attempted, [list(range(1,9)), list(range(1,5)), list(range(5,9))])
        state = self.state(result)
        self.assertEqual(state['planningBatchSize'], 4)
        truncated = [r for r in state['runs'] if r.get('finishReason') == 'length']
        self.assertEqual(len(truncated), 1)
        self.assertEqual(truncated[0]['formatAttempts'], 1)
        self.assertIn('长度上限', truncated[0]['formatError'])

    def test_repeated_length_stops_at_single_page_with_bounded_requests(self):
        attempted = []
        def transport(settings, messages):
            if messages[0]['content'].startswith('Plan all'):
                ctx = json.loads(messages[1]['content'][0]['text'])
                attempted.append(ctx['requestedPageNumbers'])
                settings['_lastDirectorCall'] = {'finishReason': 'length'}
                return '{"pages":[', 1
            return self.transport(settings, messages)
        with patch.object(fixture.engine, 'invoke_ai_director_chat', side_effect=transport):
            result = self.run_plan()
        self.assertEqual([len(n) for n in attempted], [8,4,2,1])
        self.assertIn('长度上限', result['director']['message'])
        self.assertNotIn('缺少阶段字段', result['director']['message'])
        self.assertEqual(self.state(result)['planningBatchSize'], 1)
        self.assertFalse(result['companyPromptStatus']['ready'])

    def test_time_slice_keeps_eight_specs_then_only_requests_missing_pages(self):
        def interrupted(settings, messages):
            ctx = json.loads(messages[1]['content'][0]['text'])
            if ctx.get('requestedPageNumbers', [0])[0] == 9:
                raise PlanningYield('fixture between batches')
            return self.transport(settings, messages)
        with patch.object(fixture.engine, 'invoke_ai_director_chat', side_effect=interrupted):
            first = self.run_plan(suiteCount=30)
        self.assertTrue(first['continuation']['autoContinue'])
        original = deepcopy(self.state(first)['planningDraft'])
        self.assertEqual([p['page'] for p in original], list(range(1,9)))
        before = len(self.transport.calls)
        result = self.run_plan(suiteCount=30)
        self.assertTrue(result['companyPromptStatus']['ready'], result['director']['message'])
        self.assertEqual(result['agentPlanId'], first['agentPlanId'])
        calls = self.transport.calls[before:]
        self.assertFalse(any(stage in {'product', 'strategy', 'direction'} for stage, _ in calls))
        self.assertEqual([p for stage, ctx in calls if stage == 'planning' for p in ctx['requestedPageNumbers']], list(range(9,31)))
        self.assertEqual(self.state(result)['planning'][:8], original)

    def test_partial_complete_json_saves_returned_pages_and_fills_only_missing(self):
        calls = []
        real = scene_planner.create
        def partial(call, context):
            calls.append(context['requestedPageNumbers'])
            pages = real(call, context)
            return pages[:2] if len(calls) == 1 else pages
        with patch.object(scene_planner, 'create', side_effect=partial):
            result = self.run_plan()
        self.assertTrue(result['companyPromptStatus']['ready'], result['director']['message'])
        self.assertEqual(calls, [list(range(1,9)), [3,4], [5,6,7,8]])

    def test_wrong_page_numbers_never_replace_previous_checkpoint(self):
        real = scene_planner.create
        def wrong(call, context):
            pages = real(call, context)
            if context['requestedPageNumbers'][0] == 9:
                pages[0]['page'] = 1
            return pages
        with patch.object(scene_planner, 'create', side_effect=wrong):
            result = self.run_plan(suiteCount=30)
        self.assertFalse(result['companyPromptStatus']['ready'])
        self.assertIn('超出本批', result['director']['message'])
        self.assertEqual([p['page'] for p in self.state(result)['planningDraft']], list(range(1,9)))


class RepairBatchTests(unittest.TestCase):
    def test_large_repair_commits_each_batch_and_shrinks_on_truncation(self):
        pages = [{'page': n, 'marker': 'original'} for n in range(1,31)]
        issues = [{'page': n, 'reason': 'fix'} for n in range(1,31)]
        attempts, snapshots, sizes = [], [], []
        def repair(call, context, current, subset):
            numbers = [p['page'] for p in subset]
            attempts.append(numbers)
            if len(numbers) > 4:
                raise OutputTruncated('length')
            return [{**p, 'marker': 'fixed'} if p['page'] in numbers else p for p in current]
        result = planning_batches.repair(repair, None, {}, pages, issues,
            lambda p: snapshots.append(deepcopy(p)), 8, sizes.append)
        self.assertEqual(sizes, [4])
        self.assertEqual(len(snapshots), 8)
        self.assertEqual(sum(p['marker'] == 'fixed' for p in snapshots[0]), 4)
        self.assertTrue(all(p['marker'] == 'fixed' for p in result))
        self.assertTrue(all(p['marker'] == 'original' for p in pages))

    def test_later_repair_failure_keeps_first_successful_batch(self):
        pages = [{'page': n} for n in range(1,18)]
        snapshots = []
        def repair(call, context, current, subset):
            if subset[0]['page'] > 8:
                raise PlanningYield('later slice')
            return [{**p, 'fixed': p['page'] <= 8} for p in current]
        with self.assertRaises(PlanningYield):
            planning_batches.repair(repair, None, {}, pages, [{'page': p['page']} for p in pages], snapshots.append)
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(sum(p['fixed'] for p in snapshots[0]), 8)


if __name__ == '__main__':
    unittest.main()
