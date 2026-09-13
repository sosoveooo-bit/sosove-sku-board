import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import Mock, patch
import server
from plan_preview import load_engine, compile_existing_plan


class CompilerRuntimeTests(unittest.TestCase):
    def test_actual_engine_compiles_complete_thai_plan(self):
        engine=load_engine()
        layers={key:'A complete Thai-market fixture photograph.' for key in engine.AI_IMAGE_JP_COMPANY_PROMPT_LAYER_FIELDS}
        pages=engine.build_ai_image_suite_plan('Ceramic cup','圆润杯口','750x1000',suite_key=engine.AI_IMAGE_COD_SUITE_KEY,country='TH',count=14)
        for page in pages:
            page['visualEnhancement']={'companyPromptLayers':dict(layers)}
        with patch.object(engine,'ai_image_cod_duplicate_company_prompt_pages',return_value={'duplicatePages':[],'duplicatePairs':[]}):
            result=compile_existing_plan({'suiteKey':'cod-country-landing-30','suiteCount':14,'suiteCountry':'TH',
                'size':'750x1000','suitePages':pages,'prompt':'Ceramic cup','suiteBrief':'圆润杯口'})
        self.assertTrue(result['studioCompiledReady'])
        self.assertEqual(len(result['studioPromptPreview']),14)
        self.assertTrue(all('Selected market=TH' in p['prompt'] for p in result['studioPromptPreview']))

    def test_dependency_error_is_actionable_not_replan_advice(self):
        with patch.object(server.logging.Logger,'error'):
            result=server.compile_failure(ModuleNotFoundError('missing dependency',name='cryptography'))
        self.assertEqual(result['studioCompileErrorCode'],'COMPILER_DEPENDENCY_MISSING')
        self.assertIn('cryptography',result['studioCompileError'])
        self.assertIn('无需重新AI策划',result['studioCompileError'])
        self.assertFalse(result['studioCompiledReady'])
        self.assertEqual(len(result['studioCompileErrorId']),12)

    def test_unknown_error_does_not_expose_sensitive_message(self):
        with patch.object(server.logging.Logger,'error'):
            result=server.compile_failure(RuntimeError('secret fixture should stay local'))
        self.assertNotIn('secret fixture',result['studioCompileError'])

    def test_compile_route_checks_auth_and_never_calls_director(self):
        local=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        threading.Thread(target=local.serve_forever,daemon=True).start()
        real_connection=http.client.HTTPConnection
        try:
            for user,expected in ((None,401),({'role':'customer'},403),({'username':'fixture','role':'admin'},200)):
                upstream=Mock();response=Mock(status=200)
                response.read.return_value=json.dumps({'ok':True,'user':user}).encode()
                upstream.getresponse.return_value=response
                conn=real_connection(*local.server_address)
                with patch.object(server.http.client,'HTTPConnection',return_value=upstream), \
                     patch.object(server,'compile_existing_plan',return_value={'ok':True,'studioCompiledReady':True,'studioPromptPreview':[]}) as compile_call:
                    conn.request('POST','/api/sku-board/studio-compile',body=b'{"suitePages":[]}',
                                 headers={'Host':'127.0.0.1:8795','Cookie':'fixture-cookie','Content-Type':'application/json'})
                    result=conn.getresponse();body=result.read();self.assertEqual(result.status,expected)
                    self.assertEqual(upstream.request.call_count,1)
                    self.assertEqual(upstream.request.call_args.args,('GET','/api/sku-board/session'))
                    if expected==200:
                        compile_call.assert_called_once_with({'suitePages':[]})
                        self.assertTrue(json.loads(body)['studioTimings']['compileOnly'])
                    else:compile_call.assert_not_called()
                conn.close()
        finally:local.shutdown();local.server_close()


if __name__=='__main__':unittest.main()
