const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict'), path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');
const revision = source.match(/const AI_VISUAL_DESIGN_REVISION = '([^']+)'/)[1];
const context = {
  AI_VISUAL_DESIGN_REVISION: revision,
  state: {aiImages: {conversations: []}},
  aiImageOptions: () => ({}), aiImageSkillConfig: () => ({}), aiImageDefaultModel: () => 'fixture',
  AI_IMAGE_MODEL_DEFAULTS_VERSION: 'fixture',
  syncAiImageStateFromConversation: () => {}, URL: {createObjectURL: () => 'blob:new-copy'},
};
vm.createContext(context);
for (const name of ['aiImageVisualDesignOutdated', 'renderVisualAgentDesignUpgrade', 'startVisualAgentDesignUpgrade', 'createAiImageConversation', 'aiImageCodSuiteNeedsPlanRefresh']) {
  const start = source.indexOf('function ' + name + '('), end = source.indexOf('\nfunction ', start + 1);
  assert.ok(start >= 0 && end > start, name);
  vm.runInContext(source.slice(start, end), context);
}
const old = {
  id: 'original', title: 'Garden', suiteKey: 'cod-country-landing-30', suiteCountry: 'DE',
  suitePlanVersion: 'same-wire-version', suitePlanSignature: 'original-signature',
  suitePages: [{page: 1, visualPipelineVersion: 'cod-visual-agents-v1', agentSpec: {visualDesign: {method: 'hero'}}}],
  director: {designRevision: 'old', productFacts: 'seller-confirmed product'},
  materials: [{id: 'image-to-keep'}], suiteRunId: 'keep-run', retryPageIndexes: [2, 3],
  activeOperationId: 'old-operation', status: 'partial',
  referenceImages: [{name: 'product.png', file: {fixture: true}, previewDataUrl: 'blob:original'}],
};
const snapshot = JSON.stringify(old);
assert.equal(context.aiImageVisualDesignOutdated(old), true);
assert.ok(context.renderVisualAgentDesignUpgrade(old).includes('另存 GitHub 版任务'));
assert.equal(context.renderVisualAgentDesignUpgrade({...old, suiteKey: 'jp-landing-page-25'}), '');
assert.equal(context.renderVisualAgentDesignUpgrade({...old, suiteKey: ''}), '');
assert.equal(context.aiImageVisualDesignOutdated({...old, suitePages: [{page: 1}]}), false, 'legacy path unchanged');
assert.ok(context.renderVisualAgentDesignUpgrade({...old, status: 'planning'}).includes('disabled'));
assert.throws(() => context.startVisualAgentDesignUpgrade({...old, remoteSummary: {running: 1}}), /当前/);
const currentPage = {...old.suitePages[0], agentDesignRevision: revision,
  agentSpec: {visualDesign: {buyingReason: 'daily use', benefitVisualization: 'real use action', informationHierarchy: ['main visual', 'use detail']}}};
const current = {...old, suitePages: [currentPage], director: {designRevision: revision}};
assert.equal(context.aiImageVisualDesignOutdated(current), true, 'all Agent revisions offer explicit GitHub migration');
assert.ok(context.renderVisualAgentDesignUpgrade(current).includes('GitHub 064a6b5'));
assert.throws(() => context.startVisualAgentDesignUpgrade({...current, director: {}, suitePages: [{page: 1}]}), /已经/);
assert.equal(context.aiImageVisualDesignOutdated({...current, suitePages: [{...currentPage, agentDesignRevision: 'older'}]}), true, 'page revision wins');
assert.equal(context.aiImageVisualDesignOutdated({...current, suitePages: [...current.suitePages, old.suitePages[0]]}), true, 'detect mixed/incomplete old design');
const next = context.startVisualAgentDesignUpgrade(old);
assert.equal(JSON.stringify(old), snapshot, 'source task, outputs, saved prompts and retries untouched');
assert.equal(next.productFacts, 'seller-confirmed product');
assert.equal(next.directorMode, 'review');
assert.ok(next.title.endsWith('GitHub版'));
assert.equal(next.status, 'draft');
assert.equal(next.materials.length, 0); assert.equal(next.suitePages.length, 0);
assert.equal(next.suiteRunId, ''); assert.equal(next.suitePlanSignature, '');
assert.equal(next.activeOperationId, undefined); assert.equal(next.retryPageIndexes, undefined);
assert.equal(next.referenceImages[0].file, old.referenceImages[0].file);
assert.equal(next.referenceImages[0].previewDataUrl, 'blob:new-copy');
assert.notEqual(next.referenceImages[0], old.referenceImages[0]);
assert.equal(context.state.aiImages.activeId, next.id);
// A design upgrade is opt-in; stable wire versions keep old retries and recovery usable.
assert.equal(context.aiImageCodSuiteNeedsPlanRefresh(old, {planVersion: 'same-wire-version'}), false);
assert.ok(source.includes('renderVisualAgentDesignUpgrade(conversation)+renderAiImageDirectorMonitor(conversation)'));
assert.ok(source.includes("event.target.closest('[data-agent-upgrade-design]')"));
console.log('GitHub COD migration: old/current Agent detection, explicit opt-in, preview-first, original outputs/retry preservation, zero network calls passed');
