"""COD hook visible-selling-copy contracts, exercised without a browser or API."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest


APP_JS = Path(__file__).resolve().parents[1] / "static" / "app.js"
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "Node.js is required for frontend contract tests")
class CodHookCopyFrontendTests(unittest.TestCase):
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
        following = re.search(r"(?m)^const \w+ = ", self.source[match.end():])
        end = match.end() + following.start() if following else len(self.source)
        return self.source[match.start():end]

    def run_js(self, body, *, prompt=False, setup=""):
        functions = ["aiImageCodHookCopyRestriction", "aiImageCodHookTextPolicy", "aiImageCodHookCopyInstruction"]
        constants = []
        if prompt:
            functions += ["aiImageCodHookTypeConfig", "aiImageTemplatePrompt"]
            constants.append("AI_IMAGE_COD_HOOK_TYPES")
            setup = self.PROMPT_SETUP + "\n" + setup
        fixture = {
            "source": "\n".join([*(self.constant(name) for name in constants), *(self.function(name) for name in functions)]),
            "setup": setup,
            "body": body,
        }
        runner = r"""
const fs=require('fs'), vm=require('vm'), assert=require('assert/strict');
const f=JSON.parse(fs.readFileSync(0,'utf8'));
vm.runInNewContext(f.setup+'\n'+f.source+'\n'+f.body,{assert,console});
"""
        result = subprocess.run(
            [NODE, "-e", runner], input=json.dumps(fixture),
            capture_output=True, text=True, encoding="utf-8", timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    PROMPT_SETUP = """
function aiImageProductContext(){return {title:'fixture product',subtitle:'',headline:'Core source',points:['source1','source2','source3','source4','source5','source6','source7'],proof:'source proof',tags:[]};}
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
"""

    def test_all_hook_types_default_to_visible_copy_without_title_keyword(self):
        self.run_js("""
for(const type of ['hook','effect','comparison','promotion','priceBar','discount']) {
  for(const brief of ['', '防滑握把，省力开盖，真实厨房场景', 'Copy the exact product from the reference']) {
    assert.equal(aiImageCodHookTextPolicy(brief,type),'requested');
  }
}
assert.equal(aiImageCodHookTextPolicy('不要价格，突出防滑握把','hook'),'requested');
""")

    def test_global_text_free_request_keeps_highest_priority(self):
        self.run_js("""
for(const type of ['hook','effect','comparison','promotion','priceBar','discount']) {
  for(const brief of ['无字，只展示产品', '不要添加任何文字', 'no visible text', 'text-free image', 'only a headline; do not add text', '只标题，不加文字']) {
    assert.equal(aiImageCodHookTextPolicy(brief,type),'none');
    const contract=aiImageCodHookCopyInstruction(brief,type);
    assert.match(contract,/textPolicy=none/);
    assert.equal(contract.includes('Selling-copy budget:'),false);
  }
}
""")

    def test_only_title_and_only_price_survive_local_label_exclusions(self):
        self.run_js("""
for(const brief of ['只要标题，不要标签', '仅保留一句主标题', 'headline only; omit labels', 'Only a headline']) {
  assert.equal(aiImageCodHookCopyRestriction(brief),'titleOnly');
  assert.equal(aiImageCodHookTextPolicy(brief),'requested');
  assert.match(aiImageCodHookCopyInstruction(brief),/Title-only request/);
  assert.equal(aiImageCodHookCopyInstruction(brief).includes('Selling-copy budget:'),false);
}
for(const brief of ['文案只留价格就行', '只留价格，不要标签', 'only prices; omit headline', 'price only']) {
  assert.equal(aiImageCodHookCopyRestriction(brief),'priceOnly');
  assert.equal(aiImageCodHookTextPolicy(brief),'requested');
  assert.match(aiImageCodHookCopyInstruction(brief,'hook','750x100'),/Price-only request/);
  assert.match(aiImageCodHookCopyInstruction(brief,'hook','750x100'),/one compact row/);
}
// Preserve the old interpretation of an unqualified omission request.
assert.equal(aiImageCodHookTextPolicy('Omit the headline'),'none');
""")

    def test_regular_hook_copy_is_sourced_localized_and_not_padded(self):
        self.run_js("""
for(const type of ['hook','effect','promotion','discount']) {
 const contract=aiImageCodHookCopyInstruction('防滑握把，易清洁',type);
 assert.match(contract,/2-3 distinct source-backed short supporting benefit callouts/);
 assert.match(contract,/1-2 corresponding visual evidence/);
 assert.match(contract,/headline does not occupy/);
 assert.match(contract,/actual available benefits when fewer/);
 assert.match(contract,/Faithfully localize the meaning/);
 assert.match(contract,/No invented certification/);
 assert.match(contract,/ready-made target-language title is not required/);
}
""")

    def test_compact_strips_keep_single_row_and_missing_price_exclusions(self):
        self.run_js("""
for(const type of ['hook','effect','comparison','promotion','priceBar','discount']) {
 for(const size of ['750x100','750x150']) {
   const contract=aiImageCodHookCopyInstruction('防滑握把',type,size);
   assert.match(contract,/Compact strip budget/);
   assert.match(contract,/one compact row/);
   assert.match(contract,/omit every missing price/);
   assert.equal(contract.includes('2-3 distinct'),false);
 }
}
assert.match(aiImageCodHookCopyInstruction('原价100，活动价80','priceBar'),/Compact strip budget/);
""")

    def test_comparison_copy_stays_on_one_matched_difference(self):
        self.run_js("""
const contract=aiImageCodHookCopyInstruction('同条件开瓶对比','comparison');
assert.match(contract,/exactly two matched-condition panels/);
assert.match(contract,/same supplied difference/);
assert.match(contract,/no other comparison dimension/);
assert.equal(contract.includes('2-3 distinct'),false);
""")

    def test_compiled_hook_has_visible_copy_and_no_conflicting_single_point_veto(self):
        self.run_js("""
const brief='省力开瓶。防滑握把。易清洁。用户末尾原文保持。';
for(const hasReferences of [false,true]) {
 const prompt=aiImageTemplatePrompt('codHook',{},hasReferences,{userIntent:brief,codHookType:'hook',country:'JP',size:'750x1000'});
 assert.match(prompt,/textPolicy=requested/);
 assert.match(prompt,/2-3 distinct source-backed/);
 assert.match(prompt,/Use Japanese only for added visible copy/);
 assert.equal(prompt.includes(brief),true);
 assert.equal(prompt.includes('source7'),true);
 assert.equal(prompt.split('[COD hook selling-copy contract]').length-1,1);
 assert.equal(prompt.includes('Do not add another selling point'),false);
 assert.equal(prompt.includes('headline only when explicitly requested'),false);
 assert.equal(prompt.includes('Use only explicitly requested headline/copy'),false);
 const compared=aiImageTemplatePrompt('codHook',{},hasReferences,{userIntent:'同条件开瓶对比',codHookType:'comparison'});
 assert.match(compared,/matched two-panel comparison/);
 assert.equal(compared.includes('No split screens, grids or collages'),false);
}
""", prompt=True)

    def test_non_hook_templates_keep_their_previous_content_budget(self):
        self.run_js("""
for(const template of ['main','landing','amazonAplus','rakutenSuite']) {
 const prompt=aiImageTemplatePrompt(template,{},true,{userIntent:'fixture brief'});
 assert.equal(prompt.includes('[COD hook selling-copy contract]'),false);
 assert.equal(prompt.includes('2-3 distinct source-backed'),false);
 assert.match(prompt,/select exactly one primary message/);
}
""", prompt=True)

    def test_both_transports_and_existing_hook_recompile_use_current_policy(self):
        generated = self.function("generateAiImage")
        self.assertIn('formData.append("textPolicy", aiImageCodHookTextPolicy(effectiveIntent, conversation.codHookType || "hook"))', generated)
        self.assertIn('textPolicy: aiImageCodHookTextPolicy(effectiveIntent, conversation.codHookType || "hook")', generated)
        compile_block = generated[generated.index("const needsCompile ="):generated.index("if (needsCompile)")]
        self.assertIn('|| conversation.templateKey === "codHook"', compile_block)


if __name__ == "__main__":
    unittest.main()
