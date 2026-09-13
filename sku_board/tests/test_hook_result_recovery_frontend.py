"""Read-only COD hook result recovery contracts in an isolated Node VM."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest


APP_JS = Path(__file__).resolve().parents[1] / "static" / "app.js"
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "Node.js is required for frontend contract tests")
class CodHookResultRecoveryFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = APP_JS.read_text(encoding="utf-8-sig")

    def function(self, name):
        match = re.search(rf"(?m)^(?:async )?function {re.escape(name)}\(", self.source)
        self.assertIsNotNone(match, name)
        following = re.search(r"(?m)^(?:async )?function \w+\(", self.source[match.end():])
        end = match.end() + following.start() if following else len(self.source)
        return self.source[match.start():end]

    def run_js(self, body):
        source = "\n".join(self.function(name) for name in (
            "aiImageCodHookCanRecover", "aiImageCodHookRecoveryInputKey",
            "aiImageCodHookReferenceSnapshot", "recoverAiImageCodHookResults",
            "renderAiImageErrorBlock",
        ))
        setup = r"""
let aiImageCodHookRecoveryRequest=null;
const key='a'.repeat(64), calls=[],toasts=[],saves=[],rendered=[];
const state={auth:{user:{username:'fixture',role:'admin'}}};
let permitted=true,loginCount=0,response=null;
let apiImpl=async()=>response;
let current;
const fields={'#ai-image-intent':{value:'Exact user input'},'#ai-image-prompt':{value:'Exact compiled prompt'}};
function $(selector){return fields[selector] || null;}
function aiImageActiveConversation(){return current;}
function aiImageDefaultModel(){return 'gpt-image-2.5-sunburst';}
function canUseAiImages(){return permitted;}
function openLoginDialog(){loginCount++;}
function showToast(message){toasts.push(message);}
function syncAiImageStateFromConversation(c){saves.push(c);}
function renderAiImageSidebar(){rendered.push('sidebar');}
function renderAiImageForm(){rendered.push('form');}
function renderAiImageResults(){rendered.push('results');}
function esc(value){return String(value).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function aiImageErrorDiagnosis(){return {title:'Fixture error',reason:'Fixture reason',advice:['Keep current input'],actions:['recover-suite','retry']};}
async function api(path,options){calls.push({path,options});return apiImpl(path,options);}
function fixture(){return {id:'ai-fixture',templateKey:'codHook',status:'error',error:'Image result missing',
  prompt:'Exact compiled prompt',userIntent:'Exact user input',compiledIntent:'Exact user input',productSku:'SKU-fixture',
  model:'gpt-image-2.5-sunburst',count:5,size:'750x1000',quality:'high',mode:'edit',lockLevel:'exact',
  codHookType:'hook',suiteKey:'',suiteCountry:'TH',codHookAnalysisRevision:3,
  referenceImages:[{id:'ref-A',name:'A.png',role:'product',roleSource:'ai-director',keywords:'keep blue',file:{name:'A.png'}}],
  maskImage:null,materials:[],previewDataUrls:[],remoteSummary:{message:'Original error summary'},
  productAnalysis:{source:'ai',status:'ready',analysisKey:key,colors:['Blue'],referenceBindings:[{index:1,role:'product'}]}};}
function result(count=5){return {ok:true,found:true,requestedCount:5,returnedCount:count,jobId:'saved-job',message:'Saved matching result',
  productAnalysis:{...current.productAnalysis,cached:true},
  materials:Array.from({length:count},(_,index)=>({id:'AI-'+index,previewUrl:'/api/sku-board/ai-image-output/fixture-'+index,model:current.model})),
  previewDataUrls:Array.from({length:count},(_,index)=>'/api/sku-board/ai-image-output/fixture-'+index)};}
function deferred(){let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return {promise,resolve,reject};}
current=fixture();
"""
        runner = r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const fixture=JSON.parse(fs.readFileSync(0,'utf8'));
const context=vm.createContext({assert,console,URLSearchParams,URL});
Promise.resolve(vm.runInContext(fixture.setup+'\n'+fixture.source+'\n(async()=>{\n'+fixture.body+'\n})()',context))
  .catch(error=>{console.error(error.stack);process.exitCode=1;});
"""
        completed = subprocess.run(
            [NODE, "-e", runner], input=json.dumps({"source": source, "setup": setup, "body": body}),
            text=True, encoding="utf-8", capture_output=True, timeout=20,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_recovery_button_is_only_offered_for_ready_failed_hook_analysis(self):
        self.run_js(r"""
const html=renderAiImageErrorBlock('Image result missing',current);
assert.ok(html.includes('data-ai-error-action="recover-hook"'));
assert.ok(html.includes('找回已生成图片'));
assert.ok(html.includes('此操作只找回图片'));
assert.equal(html.includes('data-ai-error-action="recover-suite"'),false);
assert.ok(html.includes('data-ai-error-action="retry"'));
for(const change of [{templateKey:'codKorea'},{templateKey:'codDetail'},{templateKey:'landing'},
  {status:'done'},{status:'partial'},{status:'generating'},{productAnalysis:{status:'ready'}},
  {productAnalysis:{status:'failed',analysisKey:key}},{productAnalysis:{status:'ready',analysisKey:'<unsafe>'}}]){
  const candidate={...current,...change};
  assert.equal(aiImageCodHookCanRecover(candidate),false);
  assert.equal(renderAiImageErrorBlock('Error',candidate).includes('data-ai-error-action="recover-hook"'),false);
}
""")

    def test_success_reads_get_with_exact_filters_and_preserves_inputs_and_references(self):
        self.run_js(r"""
response=result();
const refs=current.referenceImages,mask=current.maskImage;
const originalInput=aiImageCodHookRecoveryInputKey(current);
const payload=await recoverAiImageCodHookResults();
assert.equal(payload,response);
assert.equal(calls.length,1);
assert.equal(calls[0].options.method,'GET');
assert.equal(calls[0].options.cache,'no-store');
assert.equal('body' in calls[0].options,false);
const url=new URL(calls[0].path,'http://fixture.invalid');
assert.equal(url.pathname,'/api/sku-board/ai-image-hook-recovery');
assert.deepEqual([...url.searchParams.keys()].sort(),['analysisKey','count','model','size']);
assert.equal(url.searchParams.get('analysisKey'),key);
assert.equal(url.searchParams.get('model'),'gpt-image-2.5-sunburst');
assert.equal(url.searchParams.get('count'),'5');
assert.equal(url.searchParams.get('size'),'750x1000');
assert.equal(current.status,'done');assert.equal(current.error,'');assert.equal(current.jobId,'saved-job');
assert.equal(current.materials.length,5);assert.equal(current.previewDataUrls.length,5);
assert.equal(current.remoteSummary.succeeded,5);assert.equal(current.remoteSummary.partial,false);
assert.equal(current.remoteSummary.running,0);assert.equal(current.productAnalysis.cached,true);
assert.equal(aiImageCodHookRecoveryInputKey(current),originalInput);
assert.equal(current.referenceImages,refs);assert.equal(current.maskImage,mask);
assert.equal(saves.length,1);assert.ok(rendered.includes('sidebar'));assert.ok(rendered.includes('form'));
assert.equal(aiImageCodHookRecoveryRequest,null);
""")

    def test_not_found_is_read_only_and_does_not_rewrite_failure_or_trigger_generation(self):
        self.run_js(r"""
const before=JSON.stringify(current);
response={ok:true,found:false,message:'No matching saved result'};
assert.equal(await recoverAiImageCodHookResults(),response);
assert.equal(JSON.stringify(current),before);assert.equal(saves.length,0);
assert.deepEqual(toasts,['No matching saved result']);
assert.equal(calls.length,1);assert.equal(calls[0].options.method,'GET');
assert.equal(aiImageCodHookRecoveryRequest,null);
""")

    def test_other_templates_unready_analysis_and_permission_failures_never_call_api(self):
        self.run_js(r"""
for(const templateKey of ['codKorea','codDetail','landing','rakuten','main']){
  current={...fixture(),templateKey};assert.equal(await recoverAiImageCodHookResults(),null);
}
current=fixture();current.productAnalysis.status='failed';
assert.equal(await recoverAiImageCodHookResults(),null);
current=fixture();state.auth.user=null;
assert.equal(await recoverAiImageCodHookResults(),null);assert.equal(loginCount,1);
state.auth.user={username:'fixture',role:'customer'};permitted=false;
assert.equal(await recoverAiImageCodHookResults(),null);
assert.equal(calls.length,0);assert.equal(saves.length,0);
""")

    def test_double_click_shares_no_second_request_and_busy_button_is_disabled(self):
        self.run_js(r"""
const pending=deferred();response=result();apiImpl=()=>pending.promise;
const first=recoverAiImageCodHookResults();
assert.equal(calls.length,1);
const html=renderAiImageErrorBlock('Error',current);
assert.ok(html.includes('data-ai-error-action="recover-hook" disabled'));
assert.ok(html.includes('正在查询已保存图片'));
assert.equal(await recoverAiImageCodHookResults(),null);
assert.equal(calls.length,1);
pending.resolve(response);await first;
assert.equal(current.status,'done');assert.equal(aiImageCodHookRecoveryRequest,null);
""")

    def test_changed_inputs_or_reference_files_drop_stale_success(self):
        self.run_js(r"""
const changes=[c=>c.prompt+=' changed',c=>c.userIntent+=' changed',c=>c.compiledIntent+=' changed',
  c=>c.productSku='other',c=>c.model='other-model',c=>c.count=3,c=>c.size='1500x1500',
  c=>c.quality='medium',c=>c.mode='text',c=>c.lockLevel='strict',c=>c.codHookType='price',
  c=>c.suiteCountry='JP',c=>c.codHookAnalysisRevision++,c=>c.productAnalysis.analysisKey='b'.repeat(64),
  c=>c.referenceImages[0].role='layout',c=>c.referenceImages[0].keywords='changed',
  c=>c.referenceImages[0].file={name:'A.png'},c=>c.referenceImages.push({id:'B',file:{name:'B.png'}}),
  c=>c.maskImage={file:{name:'mask.png'}},c=>c.status='generating',c=>c.templateKey='codDetail',
  c=>fields['#ai-image-intent'].value+=' unsaved',c=>fields['#ai-image-prompt'].value+=' unsaved'];
for(const change of changes){
  current=fixture();fields['#ai-image-intent'].value='Exact user input';fields['#ai-image-prompt'].value='Exact compiled prompt';
  const pending=deferred(),payload=result();apiImpl=()=>pending.promise;
  const job=recoverAiImageCodHookResults();change(current);const afterEdit=JSON.stringify(current);
  pending.resolve(payload);assert.equal(await job,null);
  assert.equal(JSON.stringify(current),afterEdit);assert.equal(aiImageCodHookRecoveryRequest,null);
}
assert.equal(saves.length,0);assert.equal(toasts.length,0);
""")

    def test_account_or_conversation_switch_drops_stale_reply_without_selecting_old_task(self):
        self.run_js(r"""
for(const action of ['task','same-id-new-object','account']){
  current=fixture();state.auth.user={username:'fixture',role:'admin'};
  const old=current,before=JSON.stringify(old),pending=deferred(),payload=result();apiImpl=()=>pending.promise;
  const job=recoverAiImageCodHookResults();
  if(action==='task')current={...fixture(),id:'ai-other'};
  if(action==='same-id-new-object')current=fixture();
  if(action==='account')state.auth.user={username:'another',role:'admin'};
  const selected=current;pending.resolve(payload);assert.equal(await job,null);
  assert.equal(JSON.stringify(old),before);assert.equal(current,selected);assert.equal(aiImageCodHookRecoveryRequest,null);
}
assert.equal(saves.length,0);assert.equal(toasts.length,0);
""")

    def test_partial_saved_result_retains_actual_count_and_uses_material_preview(self):
        self.run_js(r"""
response=result(2);delete response.previewDataUrls;
await recoverAiImageCodHookResults();
assert.equal(current.status,'partial');assert.equal(current.remoteSummary.partial,true);
assert.equal(current.remoteSummary.requestedCount,5);assert.equal(current.remoteSummary.returnedCount,2);
assert.equal(current.remoteSummary.failed,3);assert.equal(current.remoteSummary.running,0);
assert.deepEqual(current.previewDataUrls,current.materials.map(material=>material.previewUrl));
assert.equal(current.count,5);
""")

    def test_mismatched_or_empty_saved_result_keeps_original_error_and_input(self):
        self.run_js(r"""
for(const type of ['analysis','analysis-state','count','empty']){
  current=fixture();const before=JSON.stringify(current);response=result();
  if(type==='analysis')response.productAnalysis.analysisKey='b'.repeat(64);
  if(type==='analysis-state')response.productAnalysis.status='failed';
  if(type==='count')response.requestedCount=7;
  if(type==='empty')response.materials=[];
  await recoverAiImageCodHookResults();assert.equal(JSON.stringify(current),before);
}
assert.equal(saves.length,0);assert.equal(calls.length,4);
assert.ok(calls.every(call=>call.options.method==='GET'));
""")

    def test_lookup_error_never_replaces_generation_error_or_submits_a_retry(self):
        self.run_js(r"""
const before=JSON.stringify(current);
apiImpl=async()=>{throw new Error('Read failed');};
assert.equal(await recoverAiImageCodHookResults(),null);
assert.equal(JSON.stringify(current),before);assert.equal(saves.length,0);
assert.deepEqual(toasts,['Read failed']);assert.equal(calls.length,1);assert.equal(calls[0].options.method,'GET');
assert.equal(aiImageCodHookRecoveryRequest,null);
""")

    def test_error_action_is_wired_without_posting_or_invoking_generation(self):
        recovery = self.function("recoverAiImageCodHookResults")
        self.assertIn('method: "GET"', recovery)
        self.assertNotIn('method: "POST"', recovery)
        for forbidden in ("generateAiImage(", "generateMissingAiImage", "recoverRecentAiImageSuite(", "waitForAiImageJob("):
            self.assertNotIn(forbidden, recovery)
        self.assertRegex(self.source, r'action === "recover-hook"\)\s*\{\s*recoverAiImageCodHookResults\(\)')


if __name__ == "__main__":
    unittest.main()
