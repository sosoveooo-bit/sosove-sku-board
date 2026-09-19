"""COD suite source/copy contracts in a Node VM with no browser or API I/O."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest


APP_JS = Path(__file__).resolve().parents[1] / "static" / "app.js"
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "Node.js is required for frontend contract tests")
class CodSuiteCopyFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = APP_JS.read_text(encoding="utf-8-sig")

    def function(self, name):
        match = re.search(rf"(?m)^(?:async )?function {re.escape(name)}\(", self.source)
        self.assertIsNotNone(match, name)
        following = re.search(r"(?m)^(?:async )?function \w+\(", self.source[match.end():])
        end = match.end() + following.start() if following else len(self.source)
        return self.source[match.start():end]

    def run_js(self, functions, body, *, setup=""):
        if "aiImageCodSuiteCopyInstruction" in functions or "aiImageCodSuiteBriefHasNoText" in functions:
            functions = list(dict.fromkeys([
                "aiImageCodHookCopyRestriction", "aiImageCodHookTextPolicy",
                "aiImageCodSuiteBriefHasNoText", *functions,
            ]))
        fixture = {
            "source": "\n".join(self.function(name) for name in functions),
            "setup": setup,
            "body": body,
        }
        runner = r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const f=JSON.parse(fs.readFileSync(0,'utf8'));
Promise.resolve(vm.runInNewContext(f.setup+'\n'+f.source+'\n'+f.body,{assert,console}))
  .catch(error=>{console.error(error.stack);process.exitCode=1;});
"""
        result = subprocess.run(
            [NODE, "-e", runner], input=json.dumps(fixture), capture_output=True,
            text=True, encoding="utf-8", timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    PROMPT_FUNCTIONS = [
        "aiImageProductContext", "aiImageCodSuiteCopyInstruction",
        "aiImageTemplateDirection", "aiImageTemplatePrompt",
    ]
    PROMPT_SETUP = """
function aiImageLockConfig(){return {label:'exact'};}
function aiImageCodHookTypeConfig(){return {key:'hook'};}
function aiImageCodCountryConfig(country){return country==='US' ? {label:'United States',language:'English',localization:'American local scenes'} : {label:'Japan',language:'Japanese'};}
function aiImageSkillConfig(){return {defaults:{},global:{}};}
function aiImageTemplateOptions(){return [];}
function aiImageReferenceRoleMap(){return '';}
function aiImageReferenceRoleKey(r){return r.role;}
function aiImageReferenceInstruction(mode,hasReferences,{genericProduct}){return genericProduct?'Exact generic product category':'Japanese garment';}
function aiImageCanvasInstruction(){return 'Fixture canvas';}
const AI_IMAGE_NO_ADDED_MARKS_RULE='No watermark';
const AI_IMAGE_LOCK_LEVELS=[{},{}];
const product={title:'Fixture jar opener',selling:{headline:'Source core',points:['Source A','Source B','Source C','Source D','Source E','Source F','Source G','Source A'],proof:'Source proof'}};
"""

    def test_both_suites_default_to_localized_visible_selling_copy(self):
        self.run_js(self.PROMPT_FUNCTIONS, r"""
for(const template of ['codKorea','codDetail']) {
 for(const hasReferences of [false,true]) {
  const prompt=aiImageTemplatePrompt(template,product,hasReferences,{userIntent:'防滑握把，便于收纳',country:'US',size:'750x1000'});
  assert.match(prompt,/\[COD suite selling-copy contract\] textPolicy=requested/);
  assert.match(prompt,/English only for added visible copy/);
  assert.match(prompt,/ready-made target-language title is not required/);
  assert.equal(prompt.includes('select exactly one primary message for this image and at most one directly supporting proof detail'),false);
  assert.equal(prompt.includes('at most one small supporting callout'),false);
  assert.equal(prompt.includes('Select the one point that best matches'),false);
 }
}
""", setup=self.PROMPT_SETUP)

    def test_full_deduplicated_sku_sources_survive_without_six_item_cap(self):
        self.run_js(self.PROMPT_FUNCTIONS, r"""
const tail='Product source tail '.repeat(140);
const source={title:'Fixture',selling:{headline:'Core',points:Array.from({length:18},(_,i)=>'Fact '+i).concat(['Fact 0']),proof:tail}};
for(const template of ['codKorea','codDetail']) {
 const prompt=aiImageTemplatePrompt(template,source,true,{userIntent:'完整原始文案末尾',country:'JP'});
 const match=prompt.match(/\[COD suite selling-point sources\]\n([^\n]+)/);
 assert.ok(match);
 const points=JSON.parse(match[1]);
 assert.equal(points.length,20);
 assert.equal(points[0],'Core');
 assert.equal(points[18],'Fact 17');
 assert.equal(points[19],tail.trim());
 assert.equal(points.filter(p=>p==='Fact 0').length,1);
 assert.equal(prompt.includes('完整原始文案末尾'),true);
}
""", setup=self.PROMPT_SETUP)

    def test_main_and_detail_copy_budgets_remain_separate(self):
        self.run_js(["aiImageCodSuiteCopyInstruction"], """
const main=aiImageCodSuiteCopyInstruction('codKorea','防滑握把');
assert.match(main,/3-5 distinct source-backed supporting benefits/);
assert.match(main,/1-2 direct visual proof areas/);
assert.match(main,/Main pages only/);
assert.match(main,/Detail pages keep one assigned source point/);
const detail=aiImageCodSuiteCopyInstruction('codDetail','防滑握把');
assert.match(detail,/one assigned source point/);
assert.match(detail,/concise localized explanation/);
assert.equal(detail.includes('3-5'),false);
assert.match(detail,/Source lists are complete planning facts/);
""")

    def test_explicit_global_text_free_overrides_suite_defaults(self):
        self.run_js(self.PROMPT_FUNCTIONS, r"""
for(const template of ['codKorea','codDetail']) {
 for(const brief of ['无字，只展示产品','不要添加任何文字','no visible text','text-free image','only a headline; do not add text']) {
  const contract=aiImageCodSuiteCopyInstruction(template,brief);
  assert.match(contract,/textPolicy=none/);
  assert.equal(contract.includes('3-5 distinct'),false);
  const prompt=aiImageTemplatePrompt(template,product,true,{userIntent:brief});
  assert.equal(prompt.includes('English only for added visible copy'),false);
  assert.equal(prompt.includes('textPolicy=requested'),false);
 }
}
""", setup=self.PROMPT_SETUP)

    def test_title_only_and_local_exclusions_keep_permitted_copy(self):
        self.run_js(["aiImageCodSuiteCopyInstruction"], """
for(const template of ['codKorea','codDetail']) {
 for(const brief of ['只要标题，不要标签','仅保留一句主标题','headline only; omit labels']) {
  const contract=aiImageCodSuiteCopyInstruction(template,brief);
  assert.match(contract,/textPolicy=requested/);
  assert.match(contract,/Title-only request/);
  assert.equal(contract.includes('3-5 distinct'),false);
 }
 for(const brief of ['不要价格，突出防滑握把','不要logo和水印','remove the price','no badges']) {
  assert.match(aiImageCodSuiteCopyInstruction(template,brief),/textPolicy=requested/);
 }
}
""")

    def test_unprinted_product_facts_do_not_disable_page_copy(self):
        self.run_js(["aiImageCodSuiteCopyInstruction"], """
for(const template of ['codKorea','codDetail']) {
 for(const brief of ['瓶身无字，防滑握把', '瓶身无文字，保留现有外观', '无字印花，柔软舒适', 'text-free packaging, ergonomic grip', 'without text on the bottle, soft grip', 'The garment has text-free fabric']) {
  assert.equal(aiImageCodSuiteBriefHasNoText(brief),false,brief);
  assert.match(aiImageCodSuiteCopyInstruction(template,brief),/textPolicy=requested/);
 }
 for(const brief of ['全图无字', '请生成无字图片', '本次所有图片无字。', '这套都无字', 'Create a text-free product image', '瓶身无字，整套无字', 'text-free packaging. Do not add text', "Don't add text", 'textless']) {
  assert.equal(aiImageCodSuiteBriefHasNoText(brief),true,brief);
  assert.match(aiImageCodSuiteCopyInstruction(template,brief),/textPolicy=none/);
 }
 assert.match(aiImageCodSuiteCopyInstruction(template,'瓶身无字，只要标题，不要标签'),/Title-only request/);
 assert.match(aiImageCodSuiteCopyInstruction(template,'text-free packaging, headline only; omit labels'),/Title-only request/);
}
""")

    def test_cod_detail_gets_generic_product_country_and_variant_binding(self):
        self.run_js(self.PROMPT_FUNCTIONS, r"""
const prompt=aiImageTemplatePrompt('codDetail',product,true,{userIntent:'精确保持开瓶器',country:'US',referenceRoles:[{role:'product'},{role:'product'}]});
assert.match(prompt,/United States; visible language: English/);
assert.match(prompt,/actual product category/);
assert.match(prompt,/Exact generic product category/);
assert.match(prompt,/\[Multi-product variant lock\]/);
assert.equal(prompt.includes('Japanese womenswear lifestyle advertisement'),false);
assert.equal(prompt.includes('The garment must be the visual priority'),false);
""", setup=self.PROMPT_SETUP)

    def test_unrelated_templates_keep_previous_single_image_budget(self):
        self.run_js(self.PROMPT_FUNCTIONS, r"""
for(const template of ['main','landing','amazonAplus','rakutenSuite']) {
 const prompt=aiImageTemplatePrompt(template,product,true,{userIntent:'fixture brief'});
 assert.equal(prompt.includes('[COD suite selling-copy contract]'),false);
 assert.equal(prompt.includes('[COD suite selling-point sources]'),false);
 assert.match(prompt,/select exactly one primary message/);
 assert.equal(prompt.includes('Source G'),false);
}
""", setup=self.PROMPT_SETUP)

    def test_per_page_transport_preserves_full_prompt_and_copy_plan(self):
        self.run_js(["aiImageUsesVisualAgents", "buildAiImageSuiteFormData"], """
for(const suiteKey of ['cod-country-landing-30','cod-country-detail-12']) {
 for(const page of [1,12]) {
 const prompt='[COD suite selling-point sources]\\n'+JSON.stringify(Array.from({length:18},(_,i)=>'Fact '+i))+'\\nUSER FINAL TAIL';
 const fullText='Exact source 5kg 85% '.repeat(80);
 const pages=[{page:12,textPolicy:'requested',sourceVerbatim:fullText}];
 const conversation={suiteKey,referenceImages:[{file:{},name:'product.png',role:'product'}],suitePages:pages,size:'750x1000'};
 const form=buildAiImageSuiteFormData(conversation,prompt,'user brief',page,'mock-run');
 assert.equal(form.get('prompt').startsWith(prompt),true);
 assert.equal(form.get('suiteBrief'),'user brief');
 assert.equal(form.get('companyEffectMode'),'true');
 assert.equal(JSON.parse(form.get('suitePlan'))[0].sourceVerbatim,fullText);
 assert.equal(JSON.parse(form.get('suitePlan'))[0].textPolicy,'requested');
 assert.equal(form.get('heroAB'),undefined,'COD should not opt into post-render AI hero selection');
 }
}
""", setup="""
class FormData {constructor(){this.values={};}append(k,v){this.values[k]=v;}get(k){return this.values[k];}}
function aiImageSuiteReferencesForPage(c){return c.referenceImages;}
function aiImageReferenceRoleKey(r){return r.role;}
function aiImageGenerationProfile(){return {key:'standard'};}
function aiImageDirectorMode(){return 'company';}
function aiImageSuiteCount(){return 22;}
function aiImageSuiteUsesGeneratedStyleAnchor(){return false;}
function aiImageReferenceBindings(){return [];}
""")

    def test_old_cod_plans_refresh_for_main_and_detail_retries_only(self):
        self.run_js(["aiImageCodSuiteNeedsPlanRefresh"], """
for(const [suiteKey,version] of [['cod-country-landing-30','cod-country-v27-unique-seven-layer-no-style-bitmap'],['cod-country-detail-12','cod-detail-v19-unique-seven-layer-no-style-bitmap']]) {
 for(const page of [1,8,12,22,30]) {
  assert.equal(aiImageCodSuiteNeedsPlanRefresh({suiteKey,suitePlanVersion:'legacy',retryPageIndexes:[page]}, {planVersion:version}),true);
 }
 assert.equal(aiImageCodSuiteNeedsPlanRefresh({suiteKey,suitePlanVersion:version},{planVersion:version}),false);
}
for(const suiteKey of ['jp-landing-page-25','amazon-jp-aplus-9','rakuten-jp-product-9','']) {
 assert.equal(aiImageCodSuiteNeedsPlanRefresh({suiteKey,suitePlanVersion:'legacy'},{planVersion:'new'}),false);
}
""")
        generation = self.function("generateAiImage")
        self.assertIn("aiImageCodSuiteNeedsPlanRefresh(conversation, suiteConfig)", generation)
        self.assertIn("|| requiresCodSuitePlanRefresh", generation)

    def test_single_page_retry_recompiles_current_sku_before_replanning(self):
        self.run_js(["regenerateAiImageSuitePage"], """
(async()=>{
 for(const [suiteKey,templateKey] of [['cod-country-landing-30','codKorea'],['cod-country-detail-12','codDetail']]) {
  current={suiteKey,templateKey,suitePlanVersion:'legacy',productSku:'fixture-sku',prompt:'OLD CROPPED PROMPT',userIntent:'Original explicit brief',materials:[{suitePage:12}],referenceImages:[{file:{},name:'product.png'}],suitePages:[{page:12}],size:'750x1000',suiteCountry:'US'};
  await assert.rejects(regenerateAiImageSuitePage(0),/fixture-plan-captured/);
  assert.equal(captured[0],current);
  assert.equal(captured[1],'NEW FULL SKU SOURCE PROMPT');
  assert.equal(captured[2],'Original explicit brief');
  assert.equal(compiled[0],templateKey);
  assert.equal(compiled[1].selling.points[11],'Source 11');
  assert.equal(compiled[3].userIntent,'Original explicit brief');
  assert.equal(compiled[3].country,'US');
  assert.equal(current.compiledIntent,current.userIntent);
 }
})()
""", setup="""
let current,captured,compiled;
const aiImageGenerationAbortController=null;
function aiImageActiveConversation(){return current;}
function aiImageSuiteActive(){return true;}
function aiImageSuiteCount(){return 30;}
function aiImageSuiteConfig(c){return {templateKey:c.templateKey,planVersion:'current'};}
function aiImageProductBySku(){return {selling:{points:Array.from({length:12},(_,i)=>'Source '+i)}};}
function aiImageTemplatePrompt(...args){compiled=args;return 'NEW FULL SKU SOURCE PROMPT';}
function showToast(){}
async function prepareAiImageSuitePlan(...args){captured=args;throw new Error('fixture-plan-captured');}
""")
        planner = self.function("prepareAiImageSuitePlan")
        self.assertIn("prompt = conversation.prompt || prompt;", planner)
        self.assertIn("aiImageSuitePlanSignature(conversation, prompt, effectiveIntent)", planner)


if __name__ == "__main__":
    unittest.main()
