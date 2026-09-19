import unittest
from sku_board import backend


class DirectorChainSpeedTests(unittest.TestCase):
    def test_cod_chain_only_uses_verified_gpt_peers(self):
        candidates = backend.ai_director_model_candidates({
            'model':'gpt-5.6-terra',
            'fallbackModels':['gemini-3-flash-agent','claude-sonnet-4-6','gpt-5.6-sol'],
        })
        self.assertEqual(candidates, ['gpt-5.6-terra','gpt-5.6-sol'])
        self.assertNotIn('gemini-3-flash-agent', candidates)
        self.assertNotIn('claude-sonnet-4-6', candidates)

    def test_sol_primary_fails_over_to_terra(self):
        self.assertEqual(backend.ai_director_model_candidates({
            'model':'gpt-5.6-sol','fallbackModels':['gemini-3-flash-agent','claude-sonnet-4-6']
        }), ['gpt-5.6-sol','gpt-5.6-terra'])

    def test_public_chain_matches_runtime_chain(self):
        public = backend.public_ai_director_settings({
            'enabled':True,'baseUrl':'https://fixture.example','apiKey':'fixture',
            'model':'gpt-5.6-terra','fallbackModels':['gemini-3-flash-agent','claude-sonnet-4-6','gpt-5.6-sol'],
            'timeout':120,
        })
        self.assertEqual(public['modelChain'], ['gpt-5.6-terra','gpt-5.6-sol'])
        self.assertEqual(public['fallbackModels'], ['gpt-5.6-sol'])


if __name__ == '__main__': unittest.main()
