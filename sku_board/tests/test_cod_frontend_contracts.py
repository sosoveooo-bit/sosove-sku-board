"""COD frontend contracts exercised in an isolated Node VM, without browser I/O."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest


APP_JS = Path(__file__).resolve().parents[1] / "static" / "app.js"
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "Node.js is required for the isolated frontend contract tests")
class CodFrontendContractsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = APP_JS.read_text(encoding="utf-8-sig")

    def function(self, name):
        match = re.search(rf"(?m)^(?:async )?function {re.escape(name)}\(", self.source)
        self.assertIsNotNone(match, f"Missing frontend function: {name}")
        following = re.search(r"(?m)^(?:async )?function \w+\(", self.source[match.end():])
        end = match.end() + following.start() if following else len(self.source)
        return self.source[match.start():end]

    def constant(self, name):
        match = re.search(rf"(?m)^const {re.escape(name)} = ", self.source)
        self.assertIsNotNone(match, f"Missing frontend constant: {name}")
        following = re.search(r"(?m)^const \w+ = ", self.source[match.end():])
        end = match.end() + following.start() if following else len(self.source)
        return self.source[match.start():end]

    def run_js(self, functions, body, *, setup="", constants=()):
        source = "\n".join([*(self.constant(name) for name in constants), *(self.function(name) for name in functions)])
        runner = """
const fs = require('fs');
const vm = require('vm');
const assert = require('assert/strict');
const fixture = JSON.parse(fs.readFileSync(0, 'utf8'));
const context = vm.createContext({assert, console});
Promise.resolve(vm.runInContext(fixture.setup + '\\n' + fixture.source + '\\n(async () => {\\n' + fixture.body + '\\n})()', context))
  .catch(error => { console.error(error.stack); process.exitCode = 1; });
"""
        result = subprocess.run(
            [NODE, "-e", runner],
            input=json.dumps({"source": source, "setup": setup, "body": body}),
            capture_output=True, text=True, encoding="utf-8", timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    CONFIG_CONSTANTS = (
        "AI_IMAGE_COD_COUNT_OPTIONS", "AI_IMAGE_COD_DETAIL_COUNT_OPTIONS",
        "AI_IMAGE_SUITE_CONFIGS", "AI_IMAGE_SUITE_KEY_ALIASES",
    )

    def test_country_37_routes_fifteen_main_then_twenty_two_detail_pages(self):
        self.run_js(
            ["aiImageSuiteConfig", "aiImageCodPageIsMain"],
            """
const conversation = {suiteKey: 'cod-country-landing-30', suiteCount: 37};
const config = aiImageSuiteConfig(conversation);
assert.equal(config.mainCount, 15);
assert.equal(config.detailCount, 22);
assert.equal(aiImageCodPageIsMain(conversation, 9), true);
assert.equal(aiImageCodPageIsMain(conversation, 15), true);
assert.equal(aiImageCodPageIsMain(conversation, 16), false);
assert.equal(aiImageCodPageIsMain({...conversation, suiteCount: 30}, 9), false);
assert.equal(aiImageCodPageIsMain(conversation, 17, {section: 'main', sectionIndex: 15}), true);
assert.equal(aiImageCodPageIsMain(conversation, 4, {section: 'detail', sectionIndex: 1}), false);
assert.equal(aiImageCodPageIsMain(conversation, 17, {role: '主图15'}), true);
assert.equal(aiImageCodPageIsMain(conversation, 4, {role: '详情图01'}), false);
assert.equal(aiImageCodPageIsMain(conversation, 12, {sectionIndex: 2}), false);
""", constants=self.CONFIG_CONSTANTS,
        )

    def test_detail_suite_never_uses_main_page_reference_budget(self):
        self.run_js(
            ["aiImageSuiteConfig", "aiImageCodPageIsMain", "aiImageSuiteReferencesForPage"],
            """
const refs = [{id:'product',role:'product'}, {id:'detail',role:'detail'}, {id:'scene',role:'scene'}, {id:'layout',role:'layout'}];
const detail = {suiteKey:'cod-country-detail-12',suiteCount:22,referenceImages:refs,suitePages:[]};
for (let page=1; page<=8; page++) {
  assert.equal(aiImageCodPageIsMain(detail,page,{section:'main'}),false);
  assert.equal(aiImageSuiteReferencesForPage(detail,page).length,2);
}
const main = {suiteKey:'cod-country-landing-30',suiteCount:37,referenceImages:refs,suitePages:[]};
assert.equal(aiImageSuiteReferencesForPage(main,15).length,3);
assert.equal(aiImageSuiteReferencesForPage(main,16).length,2);
""",
            setup="""
const AI_IMAGE_SUITE_HERO_REFERENCE_LIMIT=5, AI_IMAGE_SUITE_PAGE_REFERENCE_LIMIT=3;
function aiImageSuiteGenerationReferences(c){return c.referenceImages;}
function aiImageReferenceRoleKey(r){return r?.role || '';}
function aiImageSuiteReferenceRoleScore(){return 0;}
""", constants=self.CONFIG_CONSTANTS,
        )

    def test_hook_text_policy_is_explicit_and_no_text_has_priority(self):
        self.run_js(["aiImageCodHookTextPolicy"], """
assert.equal(aiImageCodHookTextPolicy('放大产品，真实厨房场景','hook'),'none');
assert.equal(aiImageCodHookTextPolicy('加一句广告文案：便利な毎日','hook'),'requested');
assert.equal(aiImageCodHookTextPolicy('Add a headline: Easy every day','effect'),'requested');
assert.equal(aiImageCodHookTextPolicy('Write short Japanese ad copy','effect'),'requested');
assert.equal(aiImageCodHookTextPolicy('Copy the exact product from the reference','hook'),'none');
for (const type of ['promotion','priceBar','discount']) {
  assert.equal(aiImageCodHookTextPolicy('原价100，活动价80',type),'requested');
  assert.equal(aiImageCodHookTextPolicy('无字，只显示产品',type),'none');
  assert.equal(aiImageCodHookTextPolicy('text-free image',type),'none');
}
assert.equal(aiImageCodHookTextPolicy('不要标题和任何文案','comparison'),'none');
assert.equal(aiImageCodHookTextPolicy('不要添加任何文字','promotion'),'none');
assert.equal(aiImageCodHookTextPolicy('不显示任何额外标题','discount'),'none');
assert.equal(aiImageCodHookTextPolicy('Do not add any text','promotion'),'none');
assert.equal(aiImageCodHookTextPolicy("Don't add any text",'promotion'),'none');
assert.equal(aiImageCodHookTextPolicy('Remove any lettering','discount'),'none');
assert.equal(aiImageCodHookTextPolicy('Omit headline','comparison'),'none');
assert.equal(aiImageCodHookTextPolicy('Omit the headline','comparison'),'none');
assert.equal(aiImageCodHookTextPolicy('without any added text','priceBar'),'none');
assert.equal(aiImageCodHookTextPolicy('做前后对比，只展示效果','comparison'),'none');
""")

    def test_hook_prompt_keeps_same_policy_with_or_without_references(self):
        self.run_js(
            ["aiImageCodHookTextPolicy", "aiImageCodHookTypeConfig", "aiImageTemplatePrompt"],
            """
for (const hasReferences of [false,true]) {
  const plain = aiImageTemplatePrompt('codHook',{},hasReferences,{userIntent:'突出产品，真实厨房场景',codHookType:'hook'});
  assert.match(plain,/textPolicy=none/);
  assert.match(plain,/No split screens, grids or collages/);
  const compared = aiImageTemplatePrompt('codHook',{},hasReferences,{userIntent:'无字，只展示同条件痛点对比',codHookType:'comparison'});
  assert.match(compared,/textPolicy=none/);
  assert.match(compared,/matched two-panel comparison/);
  assert.equal(compared.includes('No split screens, grids or collages'),false);
  const copy = aiImageTemplatePrompt('codHook',{},hasReferences,{userIntent:'加标题：便利な毎日',codHookType:'effect'});
  assert.match(copy,/textPolicy=requested/);
}
""",
            setup="""
function aiImageProductContext(){return {title:'fixture product',subtitle:'',headline:'',points:[],proof:'',tags:[]};}
function aiImageLockConfig(){return {label:'exact'};}
function aiImageCodCountryConfig(){return {label:'Japan',language:'Japanese'};}
function aiImageSkillConfig(){return {defaults:{},global:{}};}
function aiImageReferenceRoleMap(){return '';}
function aiImageReferenceRoleKey(r){return r.role;}
function aiImageReferenceInstruction(){return 'Exact fixture product';}
function aiImageCanvasInstruction(){return 'Fixture canvas';}
function aiImageTemplateDirection(){return 'Fixture scene';}
const AI_IMAGE_NO_ADDED_MARKS_RULE='No watermark';
const AI_IMAGE_LOCK_LEVELS=[{},{}];
""", constants=("AI_IMAGE_COD_HOOK_TYPES",),
        )

    def test_incomplete_cod_coverage_preserves_full_user_input_and_stops_planning(self):
        self.run_js(
            ["enforceAiImageCodSourceCoverage", "prepareAiImageSuitePlan"],
            """
const conversation={suiteKey:'cod-country-landing-30',suiteCount:12,prompt:'FULL ORIGINAL PROMPT',userIntent:'FULL ORIGINAL SOURCE',referenceImages:[],materials:[]};
await assert.rejects(prepareAiImageSuitePlan(conversation,conversation.prompt,conversation.userIntent),/来源卖点覆盖不足/);
assert.equal(apiCalls,1,'Coverage failure must not start a local-plan fallback');
assert.equal(conversation.status,'error');
assert.equal(conversation.prompt,'FULL ORIGINAL PROMPT');
assert.equal(conversation.userIntent,'FULL ORIGINAL SOURCE');
assert.equal(conversation.suitePages,payload.suitePages);
assert.equal(conversation.director.sellingPointCoverage,payload.director.sellingPointCoverage);
assert.equal(conversation.suitePlanSignature,'');
assert.match(conversation.error,/10[/]14/);
assert.match(conversation.error,/缺失卖点/);
assert.equal(persisted,true);
""",
            setup="""
let apiCalls=0,persisted=false;
const payload={ok:true,suitePages:Array.from({length:12},(_,i)=>({page:i+1})),suitePlanVersion:'cod-country-v23-source-complete',director:{source:'model',sellingPointCoverage:{complete:false,total:14,assigned:10,missing:['缺失卖点']}}};
async function loadAiImageConfig(){}
function aiImageSuiteConfig(){return {key:'cod-country-landing-30',count:12,planVersion:'cod-country-v23-source-complete',planTitle:'COD fixture',unit:'图'};}
class FormData {append(){}set(){throw new Error('Unexpected local fallback');}}
const AI_IMAGE_COMPANY_EFFECT_SUITE_KEYS=new Set(['cod-country-landing-30']);
const AI_IMAGE_DIRECTOR_STAGES=[{key:'start',label:'start'},{key:'complete',label:'complete'}];
const aiImageGenerationAbortController=null;
const window={setInterval:()=>0,clearInterval:()=>{}};
function aiImageDirectorMode(){return 'company';}
function aiImageReferenceRoleKey(){return 'product';}
function setAiImageDirectorStage(){}
function aiImageJp25CompanyPromptStatus(){return {ready:false,readyCount:0};}
async function api(){apiCalls++;return payload;}
function syncAiImageStateFromConversation(){persisted=true;}
function renderAiImageSidebar(){}
function renderAiImageForm(){}
function renderAiImageResults(){}
""",
        )

    def test_coverage_guard_is_cod_only_and_requires_explicit_false(self):
        self.run_js(["enforceAiImageCodSourceCoverage"], """
for (const suiteKey of ['jp-landing-page-25','amazon-jp-aplus-9','rakuten-jp-product-9']) {
 const c={suiteKey};
 enforceAiImageCodSourceCoverage(c,{director:{sellingPointCoverage:{complete:false}}},{key:suiteKey});
 assert.deepEqual(c,{suiteKey});
}
for (const coverage of [{},{complete:true},{complete:undefined}]) {
 const c={suiteKey:'cod-country-detail-12'};
 enforceAiImageCodSourceCoverage(c,{director:{sellingPointCoverage:coverage}},{key:c.suiteKey});
 assert.deepEqual(c,{suiteKey:'cod-country-detail-12'});
}
""")

    def test_only_cod_versions_and_opt_in_social_proof_copy_change(self):
        self.run_js(["aiImageSuiteConfig"], """
assert.equal(AI_IMAGE_SUITE_CONFIGS['jp-landing-page-25'].planVersion,'director-v33-online-photography-plan');
assert.equal(AI_IMAGE_SUITE_CONFIGS['cod-country-landing-30'].planVersion,'cod-country-v24-rich-main-support');
assert.equal(AI_IMAGE_SUITE_CONFIGS['cod-country-detail-12'].planVersion,'cod-detail-v16-source-backed');
const detail=aiImageSuiteConfig({suiteKey:'cod-country-detail-12',suiteCount:22});
assert.equal(detail.mainCount,0);
assert.equal(detail.detailCount,22);
assert.match(detail.planHint,/有资料/);
assert.equal(detail.planHint.includes('5个主卖点'),false);
assert.equal(detail.planHint,'按品类编排 22 张详情图，完整覆盖已提供卖点、颜色/规格、产品证据与使用场景；促销、背书和好评有资料才启用');
for (const count of [30,37]) {
  const country=aiImageSuiteConfig({suiteKey:'cod-country-landing-30',suiteCount:count});
  assert.match(country.planHint,/1个核心卖点/);
  assert.match(country.planHint,/3–5个有来源的辅助卖点/);
  assert.match(country.planHint,/1–2处证据/);
  assert.match(country.planHint,/详情仍单点展开/);
  assert.ok(country.planHint.includes(`${count===37 ? 15 : 8} 张主图 + 22 张详情图`));
}
for (const key of ['jp-landing-page-25','amazon-jp-aplus-9','rakuten-jp-product-9']) {
  assert.equal(aiImageSuiteConfig({suiteKey:key}).planHint,AI_IMAGE_SUITE_CONFIGS[key].planHint);
}
""", constants=self.CONFIG_CONSTANTS)

        # Evaluate the actual monitor-card expression, not a copied routing
        # function, so a broader company-mode branch cannot hide the COD hint.
        monitor = self.function("renderAiImageDirectorMonitor")
        card_start = monitor.index('label: companyEffectSuite && !jpCreativeDirector ? "平台内容 Prompt 执行"')
        hint_match = re.search(r"\bhint:\s*(.*?)\s*,\s*\n\s*\}", monitor[card_start:], re.DOTALL)
        self.assertIsNotNone(hint_match)
        self.run_js([], """
const richHint='主图保留核心原文并加入有来源的辅助清单；详情继续单点展开，数字、单位、对象和条件保持对应';
const platformHint='每页保留平台模块职责、产品证据与文案策略，再由二次导演单独编排镜头；不把页面改成通用模板';
const sourceHint='任务保留完整原文，每页只绑定对应卖点；数字、单位、对象、用法和背书主题进入最终提交Prompt';
assert.equal(monitorHint('cod-country-landing-30',true,false),richHint);
assert.equal(monitorHint('cod-country-landing-30',false,false),richHint);
for (const key of ['cod-country-detail-12','amazon-jp-aplus-9','rakuten-jp-product-9']) {
  assert.equal(monitorHint(key,true,false),platformHint);
}
assert.equal(monitorHint('jp-landing-page-25',true,true),sourceHint);
assert.equal(monitorHint('ordinary-image',false,false),sourceHint);
""", setup="function monitorHint(key,companyEffectSuite,jpCreativeDirector){const suiteConfig={key};return (" + hint_match.group(1) + ");}")
        index_html = (APP_JS.parent / "index.html").read_text(encoding="utf-8-sig")
        self.assertIn('<script src="/static/app.js?v=20260908-cod-rich-main-v9"></script>', index_html)
        self.assertIn('为每页分配一个卖点、场景、构图和参考图', index_html)

    def test_hook_dispatch_sends_policy_on_both_api_paths(self):
        generated = self.function("generateAiImage")
        self.assertIn('formData.append("textPolicy",', generated)
        self.assertRegex(generated, r'"?textPolicy"?:\s*aiImageCodHookTextPolicy\(')
        self.assertIn('aiImageCodHookTextPolicy(effectiveIntent, conversation.codHookType', generated)


if __name__ == "__main__":
    unittest.main()
