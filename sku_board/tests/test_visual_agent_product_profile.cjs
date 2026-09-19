const fs=require('node:fs'), vm=require('node:vm'), assert=require('node:assert/strict'), path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
const context={
  esc:x=>String(x??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;'),
  aiImagePersistedMaterial:m=>({...m}),
  aiImageSuiteConfig:()=>({count:24}),
  aiImageCodCompanyPromptStatus:()=>({readyCount:0}),
};
vm.createContext(context);
for(const name of ['aiImagePersistedConversation','aiImageErrorDiagnosis','renderAgentDecisionCards','renderVisualAgentMonitor']){
  const start=source.indexOf('function '+name+'('),end=source.indexOf('\nfunction ',start+1);
  assert.ok(start>=0&&end>start);vm.runInContext(source.slice(start,end),context);
}
for(const removed of ['renderVisualAgentProductProfile','saveVisualAgentProductFacts','data-agent-product-facts',
  'data-agent-save-product-facts','产品身份与交付资料','保存产品资料，准备重新策划'])assert.ok(!source.includes(removed),removed);
const diagnosis=context.aiImageErrorDiagnosis('AI 策划尚未完成：ValueError: 产品身份待确认：旧版问题');
assert.ok(diagnosis.title.startsWith('AI 策划'));
assert.equal(JSON.stringify(diagnosis.actions),'["retry"]');
assert.ok(diagnosis.reason.includes('已移除'));
const existing={suiteKey:'cod-country-landing-30',status:'error',id:'original',materials:[{id:'kept-image'}],
  productFacts:'legacy facts retained for saved-plan compatibility',suitePages:[{page:1}],suiteRunId:'saved-run',
  director:{stages:{product:{status:'needs_confirmation'}},
    failureAdvice:{codes:['product_identity'],actions:['请填写产品身份与交付资料']}},
  referenceImages:[{name:'product.png',file:{},previewDataUrl:'blob:original'}]};
const snapshot=JSON.stringify(existing);
const html=context.renderVisualAgentMonitor(existing);
assert.ok(!html.includes('请填写产品身份与交付资料'));assert.ok(!html.includes('待确认商品'));
assert.ok(html.includes('待续接'));
const persisted=context.aiImagePersistedConversation(existing);
assert.equal(JSON.stringify(existing),snapshot);
assert.equal(persisted.productFacts,existing.productFacts);
assert.equal(persisted.materials[0].id,'kept-image');assert.equal(persisted.suiteRunId,'saved-run');
assert.equal(persisted.suitePages[0].page,1);
// Hidden legacy data remains compatible with saved requests; no editor or new workflow.
assert.ok(source.includes("formData.append('productFacts',facts)"));
assert.ok(source.includes('if (facts !== undefined) formData.append("productFacts", facts)'));
assert.ok(source.includes('productFacts: conversation.productFacts ?? conversation.director.productFacts'));
console.log('Product profile removed: no UI or handlers; old confirmation can resume; cached instructions cleaned; saved tasks and API compatibility preserved');
