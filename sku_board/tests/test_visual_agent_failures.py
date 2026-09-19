import unittest
from sku_board.visual_agents.failures import describe


class FailureTests(unittest.TestCase):
    def test_empty_and_unknown(self):
        self.assertIsNone(describe(''))
        self.assertEqual(describe('missing scene')['codes'], ['planning'])

    def test_mixed_chain_keeps_all_causes(self):
        result = describe('HTTP 429 cooling down; unknown provider; The write operation timed out')
        self.assertEqual(set(result['codes']), {'model_route', 'rate_limit', 'connection'})
        self.assertFalse(result['automaticRetry'])
        self.assertEqual(len(result['actions']), 3)

    def test_no_secret_echo_in_advice(self):
        self.assertNotIn('secret-token', str(describe('SSLWantWriteError secret-token')))

    def test_payment_error_is_not_an_image_or_page_contract_failure(self):
        result = describe('AI 导演模型链均未成功：model-a：AI 导演返回错误（HTTP 402）：')
        self.assertEqual(result['codes'], ['billing'])
        self.assertFalse(result['automaticRetry'])
        self.assertIn('余额', result['actions'][0])
