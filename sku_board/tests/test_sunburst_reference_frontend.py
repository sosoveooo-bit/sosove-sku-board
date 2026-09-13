"""Original-upload reference contracts exercised without browser or network I/O."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest


APP_JS = Path(__file__).resolve().parents[1] / "static" / "app.js"
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "Node.js is required for reference selection tests")
class SunburstReferenceFrontendTests(unittest.TestCase):
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
        self.assertIsNotNone(following, f"Unterminated constant: {name}")
        end = match.end() + following.end()
        return self.source[match.start():end]

    def run_js(self, body, *, functions=(), setup=""):
        constants = (
            "AI_IMAGE_REFERENCE_ROLES", "AI_IMAGE_JP_GENERATION_REFERENCE_ROLES",
            "AI_IMAGE_SUITE_HERO_REFERENCE_LIMIT", "AI_IMAGE_SUITE_PAGE_REFERENCE_LIMIT",
            "AI_IMAGE_SUITE_REFERENCE_ROLE_KEYWORDS",
        )
        names = (
            "aiImageReferenceRoleKey", "normalizeAiImageReferenceRoles",
            "aiImageSuiteGenerationReferences", "aiImageSuiteReferenceRoleScore",
            "aiImageSuiteReferencesForPage", *functions,
        )
        source = "\n".join([
            *(self.constant(name) for name in constants),
            *(self.function(name) for name in dict.fromkeys(names)),
        ])
        shared = """
function aiImageDefaultReferenceRole(index){return index===0?'product':'auto';}
function aiImageCodPageIsMain(c,page,p={}){
  return c.suiteKey==='cod-country-landing-30'&&p.section!=='detail'&&page<=8;
}
function makeReference(name,role){
  const file={name,type:'image/png',size:4,bytes:[1,2,3,4]};
  return {id:name,name,role,file,roleSource:'manual'};
}
function fixture(suiteKey='jp-landing-page-25'){
  return {suiteKey,model:'gpt-image-2.5-sunburst',referenceImages:[
    makeReference('product-A.png','product'),makeReference('style.png','layout'),
    makeReference('product-B.png','product'),makeReference('detail.png','detail'),
  ],suitePages:[]};
}
"""
        runner = """
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const fixture=JSON.parse(fs.readFileSync(0,'utf8'));
const context=vm.createContext({assert,console});
Promise.resolve(vm.runInContext(fixture.source+'\\n'+fixture.setup+'\\n(async()=>{\\n'+fixture.body+'\\n})()',context))
  .catch(error=>{console.error(error.stack);process.exitCode=1;});
"""
        result = subprocess.run(
            [NODE, "-e", runner],
            input=json.dumps({"source": source, "setup": shared + setup, "body": body}),
            capture_output=True, text=True, encoding="utf-8", timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_jp25_primary_variant_uses_original_index_before_style_filter(self):
        self.run_js("""
for(const model of ['gpt-image-2.5-sunburst','gpt-image-2']){
  const c=fixture();c.model=model;
  c.suitePages=[{primaryVariantReferenceIndex:3,hasHuman:false}];
  const selected=aiImageSuiteReferencesForPage(c,1);
  assert.equal(selected[0].file,c.referenceImages[2].file);
  assert.deepEqual(selected.map(r=>r.name),['product-B.png','detail.png']);
  assert.equal(selected.some(r=>r.role==='layout'||r.role==='styleSet'),false);
}
""")

    def test_rakuten_primary_variant_survives_filtered_original_index(self):
        self.run_js("""
const c=fixture('rakuten-jp-product-9');
c.suitePages[2]={primaryVariantReferenceIndex:3,hasHuman:false};
c.suitePages[7]={primaryVariantReferenceIndex:3,hasHuman:false};
assert.deepEqual(aiImageSuiteReferencesForPage(c,3).map(r=>r.name),['product-B.png']);
assert.deepEqual(aiImageSuiteReferencesForPage(c,8).map(r=>r.name),['product-B.png','detail.png']);
assert.equal(aiImageSuiteReferencesForPage(c,8)[0].file,c.referenceImages[2].file);
""")

    def test_cod_explicit_primary_variant_precedes_automatic_rotation(self):
        self.run_js("""
for(const suiteKey of ['cod-country-landing-30','cod-country-detail-12']){
  const c=fixture(suiteKey);
  c.suitePages[1]={primaryVariantReferenceIndex:1,hasHuman:false};
  const selected=aiImageSuiteReferencesForPage(c,2);
  assert.equal(selected[0].file,c.referenceImages[0].file);
  assert.equal(selected[0].name,'product-A.png');
  assert.ok(selected.length<=(suiteKey==='cod-country-landing-30'?3:2));
}
""")

    def test_cod_unspecified_or_invalid_primary_keeps_existing_color_rotation(self):
        self.run_js("""
for(const invalid of [undefined,0,-1,2,99,1.5,'not-an-index']){
  const c=fixture('cod-country-landing-30');
  c.suitePages[1]={primaryVariantReferenceIndex:invalid,hasHuman:false};
  assert.equal(aiImageSuiteReferencesForPage(c,2)[0].name,'product-B.png');
}
const c=fixture('cod-country-landing-30');
assert.deepEqual([2,3,4,5].map(page=>aiImageSuiteReferencesForPage(c,page)[0].name),
  ['product-B.png','product-A.png','product-B.png','product-A.png']);
""")

    def test_cod_first_image_keeps_complete_range_and_existing_budget(self):
        self.run_js("""
const c=fixture('cod-country-landing-30');
c.referenceImages=[...['A','B','C','D','E'].map(n=>makeReference('product-'+n+'.png','product')),
  makeReference('style.png','layout'),makeReference('detail.png','detail')];
c.suitePages[0]={primaryVariantReferenceIndex:3,hasHuman:false};
const selected=aiImageSuiteReferencesForPage(c,1);
assert.deepEqual(selected.map(r=>r.name),['product-A.png','product-B.png','product-C.png','product-D.png','style.png']);
assert.equal(selected.length,AI_IMAGE_SUITE_HERO_REFERENCE_LIMIT);
""")

    def test_selected_references_keep_original_file_identity_and_inputs_unchanged(self):
        self.run_js("""
const c=fixture();
c.referenceImages[0].name=c.referenceImages[2].name='same-name.png';
c.referenceImages[0].file.name=c.referenceImages[2].file.name='same-name.png';
c.suitePages=[{primaryVariantReferenceIndex:3,hasHuman:false}];
const before=JSON.stringify(c.referenceImages),original=c.referenceImages[2].file;
const selected=aiImageSuiteReferencesForPage(c,1);
assert.notEqual(c.referenceImages[0].file,original);
assert.equal(selected[0].file,original);
assert.equal(selected[0].file.bytes,original.bytes);
assert.equal(JSON.stringify(c.referenceImages),before);
""")

    def test_selected_original_file_is_submitted_directly_in_multipart_form(self):
        self.run_js("""
const c=fixture('cod-country-detail-12');
c.suitePages[1]={primaryVariantReferenceIndex:1,hasHuman:false};
c.size='750x1000';c.quality='high';c.lockLevel='exact';
const original=c.referenceImages[0].file;
const form=buildAiImageSuiteFormData(c,'original complete prompt','original brief',2,'run');
assert.equal(form.get('reference0'),original);
assert.equal(form.get('quality'),'high');
assert.equal(form.get('model'),'gpt-image-2.5-sunburst');
assert.deepEqual(JSON.parse(form.get('productReferenceIndexes')),[1]);
assert.equal(JSON.parse(form.get('referenceBindings'))[0].role,'product');
""", functions=("aiImageReferenceBindings", "buildAiImageSuiteFormData"), setup="""
class FormData{
  constructor(){this.fields=[];}
  append(name,value,filename){this.fields.push({name,value,filename});}
  get(name){return this.fields.find(field=>field.name===name)?.value;}
}
function aiImageGenerationProfile(){return {key:'quality'};}
function aiImageSuiteCount(){return 22;}
function aiImageSuiteUsesGeneratedStyleAnchor(){return false;}
""")


if __name__ == "__main__":
    unittest.main()
