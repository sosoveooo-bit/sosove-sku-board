"""COD hook automatic image-analysis UI contracts; no browser, model or network."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest


APP_JS = Path(__file__).resolve().parents[1] / "static" / "app.js"
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "Node.js is required for frontend contract tests")
class CodHookVisionFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = APP_JS.read_text(encoding="utf-8-sig")

    def function(self, name):
        match = re.search(rf"(?m)^(?:async )?function {re.escape(name)}\(", self.source)
        self.assertIsNotNone(match, name)
        following = re.search(r"(?m)^(?:async )?function \w+\(", self.source[match.end():])
        end = match.end() + following.start() if following else len(self.source)
        return self.source[match.start():end]

    def constant(self, name):
        match = re.search(rf"(?m)^const {re.escape(name)} = ", self.source)
        self.assertIsNotNone(match, name)
        following = re.search(r";\r?\n", self.source[match.end():])
        self.assertIsNotNone(following, name)
        return self.source[match.start():match.end() + following.end()]

    def run_js(self, body, *, functions=(), setup=""):
        source = "\n".join([
            self.constant("AI_IMAGE_REFERENCE_ROLES"),
            *(self.function(name) for name in dict.fromkeys([
                "aiImageCodHookReferenceInputs", "invalidateAiImageCodHookProductAnalysis",
                "aiImageCodHookReferenceSnapshot", "applyAiImageCodHookProductAnalysis",
                "aiImageReferenceRoleKey", "aiImageReferenceRoleLabel", "aiImageReferenceBindings",
                "renderAiImageCodHookProductAnalysis", *functions,
            ])),
        ])
        shared = r"""
let conversation={templateKey:'codHook',referenceImages:[]};
function ensureAiImageConversation(){return conversation;}
function aiImageSuiteActive(c){return Boolean(c.suiteKey);}
function aiImageSuiteConfig(){return null;}
function syncAiImageStateFromConversation(){}
function renderAiImageReferences(){}
function renderAiImageResults(){}
function esc(value){return String(value).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function reference(name,role='auto',roleSource='auto'){
  return {id:name,name,role,roleSource,roleScope:'codHook',file:{name,type:'image/png',size:4}};
}
function ready(){return {status:'ready',source:'ai',model:'fixture-vision-model',productName:'Bottle opener',summary:'Visible reference product',
  colors:['Black / red'],structure:['Four grip rings'],materials:['Visible rubber texture'],usage:['Grip the lid'],uncertainties:['Hidden reverse side'],
  primaryReferenceIndex:2,referenceCount:2,referenceBindings:[{index:1,role:'layout',roleSource:'ai-director',view:'layout only'},
  {index:2,role:'product',roleSource:'ai-director',variantId:'black-red',view:'front'}],message:'Product references identified'};}
"""
        runner = r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const fixture=JSON.parse(fs.readFileSync(0,'utf8'));
const context=vm.createContext({assert,console});
Promise.resolve(vm.runInContext(fixture.setup+'\n'+fixture.source+'\n(async()=>{\n'+fixture.body+'\n})()',context))
  .catch(error=>{console.error(error.stack);process.exitCode=1;});
"""
        result = subprocess.run(
            [NODE, "-e", runner], input=json.dumps({"source": source, "setup": shared + setup, "body": body}),
            capture_output=True, text=True, encoding="utf-8", timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_hook_auto_defaults_are_scoped_and_other_defaults_stay_unchanged(self):
        self.run_js("""
for(let index=0;index<8;index++) assert.equal(aiImageDefaultReferenceRole(index),'auto');
const first=reference('first-style.png');
assert.equal(aiImageReferenceRoleKey(first,0),'auto');
first.role='layout';first.roleSource='manual';
assert.equal(aiImageReferenceRoleKey(first,0),'layout');
delete first.roleScope;
assert.equal(aiImageReferenceRoleKey(first,0),'product');
conversation={templateKey:'main'};
assert.deepEqual([0,1,2,3,4].map(aiImageDefaultReferenceRole),['product','detail','scene','person','layout']);
conversation={templateKey:'landing',suiteKey:'jp-landing-page-25'};
assert.deepEqual([0,1,2,3].map(aiImageDefaultReferenceRole),['product','auto','auto','auto']);
""", functions=("aiImageDefaultReferenceRole",))

    def test_old_default_roles_reset_to_auto_but_explicit_manual_roles_survive(self):
        self.run_js("""
const images=[reference('A','product','default'),reference('B','scene','default'),reference('C','detail','ai-director'),reference('D','usage','manual')];
const snapshot=JSON.stringify(images),files=images.map(item=>item.file);
const next=aiImageCodHookReferenceInputs(images);
assert.deepEqual(next.map(item=>item.role),['auto','auto','auto','usage']);
assert.deepEqual(next.map(item=>item.roleSource),['auto','auto','auto','manual']);
assert.ok(next.every(item=>item.roleScope==='codHook'));
assert.ok(next.every((item,index)=>item.file===files[index]));
assert.equal(JSON.stringify(images),snapshot);
""")

    def test_hook_bindings_preserve_explicit_intent_without_changing_other_payloads(self):
        self.run_js("""
const images=aiImageCodHookReferenceInputs([reference('A','layout','manual'),reference('B')]);
const bindings=aiImageReferenceBindings(images);
assert.equal(bindings[0].role,'layout');assert.equal(bindings[0].roleSource,'manual');
assert.equal(bindings[1].role,'auto');assert.equal(bindings[1].roleSource,'auto');
const ordinary={...reference('C','scene','manual')};delete ordinary.roleScope;
const oldBindings=aiImageReferenceBindings([ordinary,ordinary]);
assert.equal(oldBindings[0].role,'product');assert.equal(oldBindings[1].role,'scene');
assert.equal('roleSource' in oldBindings[1],false);
""")

    def test_analysis_progress_is_real_and_reference_updates_do_not_rebuild_prompt(self):
        self.run_js("""
conversation.referenceImages=[reference('layout.png'),reference('product.png')];
conversation.prompt='Unchanged complete prompt';
const snapshot=aiImageCodHookReferenceSnapshot(conversation);
assert.equal(applyAiImageCodHookProductAnalysis(conversation,{productAnalysis:{status:'analyzing',source:'ai',message:'Inspecting references'}},snapshot),true);
assert.equal(conversation.productAnalysis.status,'analyzing');
assert.deepEqual(conversation.referenceImages.map(item=>item.role),['auto','auto']);
assert.equal(applyAiImageCodHookProductAnalysis(conversation,{productAnalysis:ready()},snapshot),true);
assert.deepEqual(conversation.referenceImages.map(item=>item.role),['layout','product']);
assert.equal(conversation.prompt,'Unchanged complete prompt');
assert.equal(aiImageReferenceRoleKey(conversation.referenceImages[0],0),'layout');
// Polling repeatedly after resolved roles also uses the same upload snapshot.
assert.equal(applyAiImageCodHookProductAnalysis(conversation,{materials:[{productAnalysis:ready()}]},snapshot),true);
""")

    def test_manual_reference_role_is_not_silently_relabelled(self):
        self.run_js("""
conversation.referenceImages=[reference('manual','person','manual'),reference('product')];
assert.equal(applyAiImageCodHookProductAnalysis(conversation,{productAnalysis:ready()}),true);
assert.equal(conversation.referenceImages[0].role,'person');
assert.equal(conversation.referenceImages[0].roleSource,'manual');
assert.equal(conversation.referenceImages[1].role,'product');
""")

    def test_changed_uploads_or_revision_reject_stale_analysis(self):
        self.run_js("""
conversation.referenceImages=[reference('A'),reference('B')];
let snapshot=aiImageCodHookReferenceSnapshot(conversation);
conversation.referenceImages[1]={...conversation.referenceImages[1],file:{name:'B',size:4}};
assert.equal(applyAiImageCodHookProductAnalysis(conversation,{productAnalysis:ready()},snapshot),false);
snapshot=aiImageCodHookReferenceSnapshot(conversation);
invalidateAiImageCodHookProductAnalysis(conversation);
assert.equal(applyAiImageCodHookProductAnalysis(conversation,{productAnalysis:ready()},snapshot),false);
assert.equal(conversation.productAnalysis,null);
conversation.templateKey='codDetail';
assert.equal(applyAiImageCodHookProductAnalysis(conversation,{productAnalysis:ready()}),false);
""")

    def test_ready_card_is_escaped_and_shows_actual_reference_facts(self):
        self.run_js("""
const analysis=ready();analysis.productName='<img src=x onerror=alert(1)>';
analysis.structure.push('<script>unsafe()</script>');
conversation.productAnalysis=analysis;
conversation.referenceImages=[reference('A'),reference('B')];
const html=renderAiImageCodHookProductAnalysis(conversation);
for(const expected of ['AI产品识别完成','Black / red','Four grip rings','Visible rubber texture','Grip the lid','Hidden reverse side','排版风格','black-red','fixture-vision-model'])assert.ok(html.includes(expected),expected);
assert.equal(html.includes('<script>'),false);
assert.equal(html.includes('<img src=x'),false);
assert.ok(html.includes('&lt;img'));
assert.ok(html.includes('aria-live="polite"'));
""")

    def test_pending_failed_and_untrusted_results_never_claim_analysis_success(self):
        self.run_js("""
conversation.referenceImages=[reference('A')];
for(const analysis of [undefined,{...ready(),status:'analyzing'},{...ready(),status:'failed'},{...ready(),source:'local'}]){
 conversation.productAnalysis=analysis;
 const html=renderAiImageCodHookProductAnalysis(conversation);
 assert.equal(html.includes('AI产品识别完成'),false);
 assert.equal(html.includes('Four grip rings'),false);
}
conversation.productAnalysis={source:'ai',status:'failed',message:'fixture model timeout'};
assert.match(renderAiImageCodHookProductAnalysis(conversation),/产品识别失败，已暂停生图/);
assert.equal(applyAiImageCodHookProductAnalysis(conversation,{productAnalysis:{...ready(),source:'local'}}),false);
conversation.templateKey='landing';
assert.equal(renderAiImageCodHookProductAnalysis(conversation),'');
""")

    def test_invalidation_and_reference_limit_are_hook_only(self):
        self.run_js("""
conversation.referenceImages=Array.from({length:17},(_,index)=>reference(String(index)));
conversation.productAnalysis=ready();
assert.throws(()=>validateAiImageModeInputs(conversation),/最多16张/);
assert.equal(conversation.referenceImages.length,17);
invalidateAiImageCodHookProductAnalysis(conversation);
assert.equal(conversation.productAnalysis,null);
conversation.templateKey='main';conversation.productAnalysis=ready();
assert.doesNotThrow(()=>validateAiImageModeInputs(conversation));
invalidateAiImageCodHookProductAnalysis(conversation);
assert.equal(conversation.productAnalysis.status,'ready');
""", functions=("validateAiImageModeInputs",))

    def test_job_progress_delivers_initial_pending_and_final_analysis(self):
        self.run_js("""
const updates=[],messages=[];
const final=await waitForAiImageJob({ok:true,pending:true,jobId:'fixture-job',message:'Analyzing',productAnalysis:{source:'ai',status:'analyzing'}},
 {onPending:message=>messages.push(message),onProgress:payload=>updates.push(payload)});
assert.equal(updates.length,2);
assert.equal(updates[0].productAnalysis.status,'analyzing');
assert.equal(updates[1].productAnalysis.status,'ready');
assert.equal(final,updates[1]);
assert.deepEqual(messages,['Analyzing']);
assert.equal((await waitForAiImageJob({ok:true,pending:false})).ok,true);
""",
                    functions=("waitForAiImageJob",), setup="""
async function waitForAiImageRetry(){}
async function api(path){assert.equal(path,'/api/sku-board/ai-image-jobs/fixture-job');return {ok:true,pending:false,productAnalysis:ready()};}
""")

    def test_error_response_keeps_analysis_metadata_for_a_truthful_pause_card(self):
        self.run_js("""
let error;
try{await api('/api/sku-board/ai-image-jobs/fixture');}catch(caught){error=caught;}
assert.equal(error.status,422);
assert.equal(error.productAnalysis.status,'failed');
assert.equal(error.productAnalysis.source,'ai');
assert.equal(applyAiImageCodHookProductAnalysis(conversation,error),true);
assert.equal(conversation.productAnalysis.status,'failed');
""", functions=("api",), setup="""
class FormData{}
async function fetch(){return {status:422,text:async()=>JSON.stringify({ok:false,error:'Fixture analysis failed',productAnalysis:{status:'failed',source:'ai',message:'Fixture analysis failed'}})};}
""")

    def test_generation_and_mutation_entrypoints_use_the_hook_contract(self):
        generated = self.function("generateAiImage")
        self.assertIn("const codHookReferenceSnapshot = conversation.templateKey", generated)
        self.assertIn("applyAiImageCodHookProductAnalysis(conversation, progress, codHookReferenceSnapshot)", generated)
        self.assertIn("applyAiImageCodHookProductAnalysis(conversation, error, codHookReferenceSnapshot)", generated)
        self.assertIn("invalidateAiImageCodHookProductAnalysis(conversation)", generated)
        for name in ("addAiImageReferences", "removeAiImageReference", "clearAiImageReferences", "setAiImageReferenceRole", "setAiImageReferenceKeyword"):
            self.assertIn("invalidateAiImageCodHookProductAnalysis(conversation)", self.function(name))
        self.assertEqual(self.function("renderAiImageResults").count("${hookProductAnalysisBlock}"), 2)
        self.assertIn('template.key === "codHook"', self.function("applyAiImageTemplate"))


if __name__ == "__main__":
    unittest.main()
