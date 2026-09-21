import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from sku_board import backend as engine
from sku_board.visual_agents import contracts, pipeline, adapter
from sku_board.visual_agents.store import Store


SUBJECTS = ['羽毛托举', '台面拆解', '窗边阅读', '户外遮阳', '针织纹理', '接口连接', '手部握持', '箱内收纳',
            '桌面测量', '瓶口封装', '侧面轮廓', '布料垂坠', '抽屉整理', '手腕佩戴', '厨房操作', '口袋便携',
            '行李平铺', '局部缝线', '餐桌布置', '清洗过程', '包装清单', '操作流程', '双面结构', '床头使用',
            '参数排版', '材料对照', '书桌安装', '出门准备', '配件组合', '用途总结']


class Transport:
    def __init__(self):
        self.calls = []
        self.fail = None

    def __call__(self, settings, messages):
        role = messages[0]['content']
        context = json.loads(messages[1]['content'][0]['text'])
        stage = ('product' if role.startswith('Analyze the actual') else
                 'strategy' if 'marketing strategist' in role else
                 'direction' if 'creative director' in role else
                 'planning' if role.startswith('Plan all') else 'prompts')
        self.calls.append((stage, context))
        if self.fail == stage:
            raise TimeoutError('fixture upstream timeout')
        if stage == 'product':
            data = {'productSummary': '蓝色护理棒与白色涂抹头', 'categories': ['beauty'],
                    'facts': [{'id': 'F1', 'statement': '白色涂抹头', 'assetIds': [context['assets'][0]['assetId']], 'status': 'observed'}],
                    'productVisualDNA': {'shape': 'blue cylinder, white applicator, black cap'},
                    'referenceBreakdown': [], 'audienceProfiles': [], 'consumerPsychology': [],
                    'coreSellingPoints': [], 'prohibitedVisualDirections': ['no invented electrical controls'], 'missingInformation': [],
                    'identityAssessment': {'declaredProduct': '护理棒', 'sellingForm': '完整护理棒',
                                           'status': 'clear', 'conflicts': [], 'question': ''}}
        elif stage == 'strategy':
            data = {'positioning': '方便操作的日常护理', 'purchaseReasons': [], 'conversionPriorities': [],
                    'emotionalTriggers': [], 'objectionResponses': [], 'salesNarrative': [], 'assumptions': []}
        elif stage == 'direction':
            data = {'visualTheme': '实际使用与结构说明', 'colorDirection': {'palette': ['#135AAC']},
                    'typographyDirection': 'clear hierarchy', 'modelStrategy': 'people only when useful',
                    'sceneStrategy': 'different practical views', 'photographyStyle': 'real skin',
                    'representationStrategy': [], 'campaignInvariants': [], 'pageVariationPolicy': 'independent composition'}
        elif stage == 'planning':
            sources = context['sources']
            data = {'pages': [{'page': i + 1, 'purpose': name + '说明', 'userPsychology': '了解实际操作与选择依据',
                               'sourceIds': [sources[i % len(sources)]['id']], 'factIds': ['F1'],
                               'scene': name, 'composition': SUBJECTS[-i - 1] + '非对称空间关系',
                               'copyDirection': '简洁的本地语言说明', 'evidenceMethod': name + '实际依据',
                               'referenceAssetIds': [context['assets'][0]['assetId']], 'difference': name + '独立表达'}
                              for i, name in enumerate(SUBJECTS[:context['pageCount']])]}
            for i, page in enumerate(data['pages']):
                page['visualDesign'] = {
                    'primarySubject': ['product', 'detail', 'environment'][i % 3],
                    'method': ['hero', 'macro', 'demonstration'][i % 3],
                    'layoutFamily': ['single', 'split', 'editorial'][i % 3],
                    'humanRole': 'none', 'visualHook': page['scene'] + '实际演示',
                    'referenceReason': '产品原图用于准确呈现结构',
                    'buyingReason': '了解具体使用价值', 'benefitVisualization': page['scene'] + '解释使用价值',
                    'informationHierarchy': ['主体画面优先', '标题清晰可读', '辅助细节说明'],
                }
            if context.get('requestedPageNumbers'):
                data['pages'] = [p for p in data['pages'] if p['page'] in context['requestedPageNumbers']]
        else:
            language = 'ดูแลผิว' if context['selectedCountry'] == 'TH' else '毎日のケア'
            data = {'pages': [{'page': p['page'], 'creativeInstruction':
                               f"Create this distinct finished ecommerce photograph: {p['scene']}. "
                               f"Use this specific hierarchy: {p['composition']}. Preserve the blue cylinder and "
                               f"white applicator. Show the source-backed activity at realistic scale. Visible headline: {language}",
                               'exactCopy': [{'text': language, 'role': 'headline', 'sourceIds': p['sourceIds']}],
                               'negativeInstructions': ['No invented controls.']} for p in context['pages']]}
        return json.dumps(data, ensure_ascii=False), 5


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.transport = Transport()
        for patcher in (patch.object(engine, 'DATA_DIR', Path(self.tmp.name)),
                        patch.object(engine, 'invoke_ai_director_chat', side_effect=self.transport),
                        patch.object(engine, 'load_ai_director_settings', return_value={'enabled': True, 'baseUrl': 'fixture', 'apiKey': 'fixture', 'model': 'fixture'}),
                        patch.object(engine, 'ai_director_reference_data_url', return_value='data:image/png;base64,fixture')):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.payload = {'suiteKey': 'cod-country-landing-30', 'suiteCount': 8, 'suiteCountry': 'TH', 'size': '750x1000',
                        'suiteBrief': '展示护理棒的使用方式和可见结构，丰富的泰语图文。', 'visualPipelineVersion': contracts.VERSION}
        self.actor = {'username': 'fixture-user', 'role': 'admin'}
        self.images = [('product.png', b'product-bytes', 'image/png')]

    def run_plan(self, **changes):
        # Exercise the Agent pipeline directly. The HTTP planning route now uses
        # the GitHub COD planner; these tests cover the Agent stage contracts.
        return pipeline.run(engine, {**self.payload, **changes}, self.actor, self.images)

    def test_complete_flow_and_persistent_product_cache(self):
        first = self.run_plan()
        self.assertTrue(first['companyPromptStatus']['ready'], first['director']['message'])
        self.assertEqual([s for s, _ in self.transport.calls][:4], ['product', 'strategy', 'direction', 'planning'])
        calls = len(self.transport.calls)
        second = self.run_plan()
        self.assertEqual(len(self.transport.calls), calls)
        self.assertTrue(second['director']['productCacheHit'])
        self.assertEqual(first['suitePages'], second['suitePages'])

    def test_market_count_and_replanning_do_not_reanalyze_images(self):
        self.run_plan()
        for changes in ({'suiteCountry': 'JP'}, {'suiteCount': 30}, {'forceReanalyze': True}, {'suiteBrief': '换成暖色风格'}):
            result = self.run_plan(**changes)
            self.assertTrue(result['companyPromptStatus']['ready'], result['director']['message'])
        self.assertEqual(sum(s == 'product' for s, _ in self.transport.calls), 1)
        self.assertEqual(len(Store(self.tmp.name).get('fixture-user', 'product', result['director']['productAnalysisId'])['data']['facts']), 1)

    def test_downstream_failure_keeps_product_and_resumes(self):
        self.transport.fail = 'strategy'
        first = self.run_plan()
        self.assertFalse(first['companyPromptStatus']['ready'])
        self.assertFalse(first['director']['sellingPointCoverage']['checked'])
        self.assertIsNone(first['director']['sellingPointCoverage']['complete'])
        self.assertGreater(first['director']['sellingPointCoverage']['total'], 0)
        self.transport.fail = None
        self.assertTrue(self.run_plan()['companyPromptStatus']['ready'])
        self.assertEqual(sum(s == 'product' for s, _ in self.transport.calls), 1)

    def test_first_failed_analysis_is_not_cached(self):
        self.transport.fail = 'product'
        self.assertFalse(self.run_plan()['companyPromptStatus']['ready'])
        self.transport.fail = None
        self.assertTrue(self.run_plan()['companyPromptStatus']['ready'])
        self.assertEqual(sum(s == 'product' for s, _ in self.transport.calls), 2)

    def test_rename_reference_and_account_isolation(self):
        self.run_plan()
        self.images[0] = ('renamed.png', b'product-bytes', 'image/png')
        self.assertTrue(self.run_plan()['director']['productCacheHit'])
        self.actor = {'username': 'another-user', 'role': 'admin'}
        self.assertFalse(self.run_plan()['director']['productCacheHit'])

    def test_changed_product_and_force_analysis(self):
        self.run_plan()
        self.images[0] = ('product.png', b'other-sku', 'image/png')
        self.assertFalse(self.run_plan()['director']['productCacheHit'])
        self.assertFalse(self.run_plan(forceProductAnalysis=True)['director']['productCacheHit'])
        self.assertEqual(sum(s == 'product' for s, _ in self.transport.calls), 3)

    def test_compiler_and_stored_contract_no_legacy_layout(self):
        result = self.run_plan()
        pages = result['suitePages']
        normalized = engine.normalize_ai_image_suite_plan(json.dumps(pages), 8)
        self.assertEqual(pages, normalized)
        prompts, compiled = engine.build_ai_image_suite_prompts('', self.payload['suiteBrief'], '750x1000',
            suite_key=self.payload['suiteKey'], plan=pages, country='TH', suite_count=8)
        self.assertEqual(prompts, [p['agentPrompt']['resolvedPrompt'] for p in pages])
        self.assertNotIn('companyPromptLayers', compiled[0])
        self.assertFalse(any('Company module construction contract' in p for p in prompts))
        adapter.verify_submission(Store(self.tmp.name), 'fixture-user', pages, self.payload, pipeline.assets_for(self.images))
        tampered = deepcopy(pages)
        tampered[0]['agentPrompt']['resolvedPrompt'] = 'different image'
        with self.assertRaises(ValueError):
            adapter.verify_submission(Store(self.tmp.name), 'fixture-user', tampered, self.payload)
        with self.assertRaises(ValueError):
            adapter.verify_submission(Store(self.tmp.name), 'another-user', pages, self.payload)
        with self.assertRaises(ValueError):
            adapter.verify_submission(Store(self.tmp.name), 'fixture-user', pages, {**self.payload, 'suiteBrief': 'changed'})

    def test_no_post_generation_ai_entry_in_pipeline(self):
        result = self.run_plan(suiteCount=30)
        self.assertTrue(result['companyPromptStatus']['ready'], result['director']['message'])
        self.assertEqual(len({p['agentPrompt']['promptHash'] for p in result['suitePages']}), 30)
        self.assertTrue(set(s for s, _ in self.transport.calls) <= set(contracts.STAGES))

    def test_old_requests_do_not_enter_new_pipeline(self):
        with patch.object(pipeline, 'run', side_effect=AssertionError('new pipeline used')):
            result = engine.plan_ai_image_suite({**self.payload, 'visualPipelineVersion': '', 'useDirector': False}, self.actor)
        self.assertNotIn('visualPipelineVersion', result)


if __name__ == '__main__':
    unittest.main()
