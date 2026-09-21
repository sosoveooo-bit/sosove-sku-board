const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {File} = require('node:buffer');
const source = fs.readFileSync(require('node:path').join(__dirname, '../static/app.js'), 'utf8');
const context = {
  FormData,
  aiImageSuiteReferencesForPage: c => c.referenceImages.slice(0, 1),
  aiImageReferenceRoleKey: r => r.role,
  aiImageGenerationProfile: () => ({key: 'standard'}),
  aiImageSuiteCount: () => 8,
  aiImageDirectorMode: () => 'company',
  aiImageSuiteUsesGeneratedStyleAnchor: () => true,
  aiImageReferenceBindings: refs => refs.map((r, i) => ({index: i + 1, role: r.role})),
  aiImageSuiteGenerationReferences: () => { throw Error('Agent review must exit before reading images'); },
};
vm.createContext(context);
vm.runInContext(source.slice(source.indexOf('function aiImageUsesVisualAgents('),
  source.indexOf('function updateAiImageSuiteProgress(')), context);
const reviewStart = source.indexOf('async function reviewAiImageSuitePageNumbers(');
const reviewEnd = source.indexOf('\nfunction ', reviewStart);
vm.runInContext(source.slice(reviewStart, reviewEnd), context);
const reference = (name, role) => ({name, role, file: new File([name], name, {type: 'image/png'})});
const conversation = {
  suiteKey: 'cod-country-landing-30', suiteCountry: 'TH', size: '750x1000', model: 'fixture',
  productFacts: '实际商品：护理棒；规格：15ml',
  referenceImages: [reference('product.png', 'product'), reference('detail.png', 'detail'), reference('style.png', 'style')],
  suitePages: [{page: 1, visualPipelineVersion: 'cod-visual-agents-v1'}],
};
const form = context.buildAiImageSuiteFormData(conversation, 'prompt', 'brief', 1, 'fixture', reference('anchor.png', 'style'));
assert.equal(form.get('visualPipelineVersion'), 'cod-visual-agents-v1');
assert.equal(form.get('productFacts'), conversation.productFacts);
assert.equal(form.get('referenceUploadCount'), '3');
assert.equal(form.get('reference2').name, 'style.png');
assert.equal(form.get('heroAB'), null);
assert.equal(form.get('suiteStyleAnchor'), null);
const edit = context.buildAiImageSuiteFormData(conversation, 'prompt', 'brief', 1, 'fixture', null, 'fix copy', reference('edit.png', 'product'));
assert.equal(edit.get('referenceUploadCount'), '1');
assert.equal(edit.get('reference0').name, 'edit.png');
assert.equal(edit.get('suiteEditSource'), 'true');
const legacy = context.buildAiImageSuiteFormData({...conversation, suitePages: [{page: 1}]}, 'prompt', 'brief', 1, 'fixture');
assert.equal(legacy.get('referenceUploadCount'), '1');
// COD suites never request hero A/B selection: one render per page, no post-render pick.
assert.equal(legacy.get('heroAB'), null);
context.reviewAiImageSuitePageNumbers(conversation, [1]).then(result => {
  assert.equal(result.status, 'skipped');
  console.log('Agent references, direct edit, legacy submission and zero-review dispatch passed');
}).catch(error => { console.error(error); process.exitCode = 1; });
