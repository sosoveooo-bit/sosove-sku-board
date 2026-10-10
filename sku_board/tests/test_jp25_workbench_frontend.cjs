// Exercise the real frontend orchestration with fake I/O. No live app or model calls.
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const workbench = fs.readFileSync(path.join(root, 'static/jp25-workbench.js'), 'utf8');
const source = fs.readFileSync(path.join(root, 'static/app.js'), 'utf8');
function fn(name) {
  const start = source.search(new RegExp(`^(?:async )?function ${name}\\(`, 'm'));
  assert.ok(start >= 0, name);
  const next = source.slice(start + 1).search(/^(?:async )?function \w+\(/m);
  return source.slice(start, next < 0 ? undefined : start + 1 + next);
}
const context = vm.createContext({ console, assert, AbortController, performance, structuredClone, FormData, Blob, File, setTimeout, clearTimeout });
vm.runInContext(workbench + `
const fields = new Map();
const $ = key => key === '[data-jp25-workbench]' ? null : fields.get(key) || fields.set(key, {value:'', textContent:'',disabled:false, focus(){}}).get(key);
let c, calls = [], planCalls = 0, aiImageGenerationAbortController = null, aiImageGenerationStartedAt = 0;
const state = {auth:{user:{role:'admin'}},aiImages:{director:{model:'fixture'},mode:'edit'}};
const config = {count:25,unit:'张',size:'1500x2000',label:'日本25图',planVersion:'v-test'};
const profile = {key:'standard',quality:'high',maxRetries:0,autoRetryCycles:0};
const canUseAiImages=()=>true, ensureAiImageConversation=()=>c, aiImageActiveConversation=()=>c;
const aiImageSkillConfig=()=>({id:'fixture',version:'fixture'}), aiImagePromptIsStructured=()=>true;
const aiImageSuiteKeyFromIntent=()=>'', aiImageCodCountryActive=()=>false, aiImageDefaultModel=()=>'fixture';
const aiImageSuiteConfig=()=>config, aiImageSuiteCount=()=>25, aiImageSuiteActive=()=>true;
const aiImageGenerationProfile=()=>profile, aiImageProductBySku=()=>({}), aiImageTemplatePrompt=()=>'structured prompt';
const aiImageDirectorMode=()=>'company', aiImageCompanyPromptStatus=()=>({ready:true});
const aiImageCodSuiteNeedsPlanRefresh=()=>false, aiImageReferenceRoleKey=(r)=>r.role||'product';
const syncAiImageStateFromConversation=()=>{}, renderAiImageSidebar=()=>{}, renderAiImageForm=()=>{}, renderAiImageResults=()=>{};
const persistAiImageState=()=>{}, aiImageSuiteMaterialFile=async()=>new File(['fixture'],'fixture.png',{type:'image/png'});
const createAiImageSuiteRunId=()=>'fixture-run', showToast=()=>{}, aiImageRendererLabel=()=>'fixture';
const aiImageUsesVisualAgents=()=>false, aiImageSuiteReferencesForPage=()=>c.referenceImages, aiImageReferenceBindings=()=>[];
const syncAiImageSavedPlan=async()=>{}, aiImageGenerationNodeForPage=()=>({}), aiImageGenerationWorkerCount=()=>3;
const aiImageSuiteUsesGeneratedStyleAnchor=()=>false, updateAiImageSuiteProgress=()=>{};
const throwIfAiImageGenerationAborted=()=>{}, aiImageConversationTitle=()=>'', loadAiImageHealth=async()=>{};
const aiImageSuitePayloadError=()=>'', aiImageSavedPlanError=()=>false, aiImageSuiteTransientError=()=>false, aiImageSuiteQuotaError=()=>false;
const isAiImageGenerationAborted=e=>e.name==='AbortError', recoverRecentAiImageSuite=async()=>({});
const waitForAiImageJob=async p=>p;
let failPage = 0, reportRequests = 0;
const api=async(url,options)=>{
  if(url==='/api/sku-board/jp25-report'){
    reportRequests++;
    return {results:JSON.parse(options.body.get('pageNumbers')).map(n=>({page:n,width:1500,height:2000,pixelHash:'hash-'+n,issues:[],visualStatus:'not_checked'}))};
  }
  assert.equal(url,'/api/sku-board/ad-launch-ai-image-edit');
  const n=JSON.parse(options.body.get('suitePageIndexes'))[0];
  calls.push({n,form:options.body});
  if(n===failPage) throw new Error('mock provider unavailable');
  return {materials:[{suitePage:n,id:'output-'+n+'-'+calls.length,jp25Revision:options.body.get('jp25Revision')}],suitePlanVersion:config.planVersion};
};
const mergeAiImageSuitePayload=(conv,payload)=>{
 const byPage=new Map(conv.materials.map(m=>[m.suitePage,m]));
 payload.materials.forEach(m=>byPage.set(m.suitePage,m)); conv.materials=[...byPage.values()]; return payload.materials;
};
const prepareAiImageSuitePlan=async(conv,prompt,intent)=>{
 planCalls++; conv.suitePages=Array.from({length:25},(_,i)=>({page:i+1,title:'第'+(i+1)+'页',headline:'自然な着心地',textPolicy:i===0?'none':'minimal',scene:i===0?'full body':i===10?'macro detail':'scene '+i}));
 conv.suitePlanVersion=config.planVersion;
 conv.suitePlanSignature=aiImageSuitePlanSignature(conv,prompt,intent);
};
function reset(){
 c={id:'ai-fixture',suiteKey:'jp-landing-page-25',suitePages:[],materials:[],previewDataUrls:[],referenceImages:[{file:new File(['fixture'],'original.png',{type:'image/png'}),name:'original.png',role:'product'}],model:'fixture',quality:'high'};
 calls=[];planCalls=0;failPage=0;
 $('#ai-image-intent').value='日本商品';$('#ai-image-prompt').value='';$('#ai-image-model').value='fixture';
}
` + ['aiImageSuitePlanSignature', 'buildAiImageSuiteFormData', 'generateAiImageSuitePages', 'validateAiImageModeInputs', 'generateAiImage', 'handleJp25Action'].map(fn).join('\n'), context);
const tests = `
reset();
await generateAiImage(null,{jp25Action:'plan'});
assert.equal(planCalls,1);assert.equal(calls.length,0);assert.equal(c.status,'planned');assert.equal(aiImageGenerationAbortController,null);
await generateAiImage(null,{jp25Action:'sample'});
assert.equal(planCalls,1);assert.deepEqual(calls.map(x=>x.n).sort((a,b)=>a-b),[1,2,11]);
assert.equal(c.status,'sampled');assert.equal(c.materials.length,3);
assert.ok(calls.every(x=>x.form.get('heroAB')===null),'Sample stage must not request an extra hero candidate');
assert.equal(JP25Workbench.remaining(c).length,22);
const sampleIds=c.materials.map(m=>m.id);
await generateAiImage(null,{jp25Action:'remaining'});
assert.equal(planCalls,1);assert.equal(calls.length,25);assert.equal(c.materials.length,25);assert.equal(c.status,'done');
assert.ok(sampleIds.every(id=>c.materials.some(m=>m.id===id)),'Continuation must preserve completed samples');
assert.equal(new Set(calls.map(x=>x.n)).size,25);
const previousFirst=c.materials.find(m=>m.suitePage===1).id;
c.jp25Workbench={pages:{1:{headline:'新しい見出し',scene:'窓辺'}}};
assert.deepEqual(JP25Workbench.remaining(c),[1]);
failPage=1;
await generateAiImage(null,{jp25Action:'remaining'});
assert.equal(calls.length,26);assert.notEqual(c.status,'done');
assert.equal(c.materials.find(m=>m.suitePage===1).id,previousFirst,'Failed regeneration preserves the old image');
assert.deepEqual(JP25Workbench.remaining(c),[1]);
failPage=0;
await generateAiImage(null,{jp25Action:'remaining'});
assert.equal(calls.length,27);assert.notEqual(c.materials.find(m=>m.suitePage===1).id,previousFirst);
assert.equal(JSON.parse(calls.at(-1).form.get('jp25Workbench')).pages[1].headline,'新しい見出し');
assert.equal(planCalls,1,'A local page adjustment does not re-plan the whole suite');
const reloaded=JSON.parse(JSON.stringify(c));
assert.equal(JP25Workbench.remaining(reloaded).length,0,'Saved revisions survive reload');
c.jp25Workbench.styleNotes='低彩度で自然光';
await generateAiImage(null,{jp25Action:'plan'});
assert.equal(planCalls,2);assert.equal(calls.length,27);assert.equal(c.materials.length,25);
assert.equal(JP25Workbench.remaining(c).length,25,'Global plan change invalidates old outputs without deleting them');
const duplicates=JP25Workbench.deduplicate([{page:1,pixelHash:'same',issues:[],visualStatus:'not_checked'},{page:16,pixelHash:'same',issues:[],visualStatus:'pass'}]);
assert.ok(duplicates[1].issues.length);assert.equal(duplicates[1].visualStatus,'needs_review');
const safe=JP25Workbench.render({...c,jp25Workbench:{productNotes:'<img src=x onerror=alert(1)>'}});
assert.ok(!safe.includes('<img src=x'));assert.ok(safe.includes('&lt;img'));
assert.equal(JP25Workbench.render({suiteKey:'cod-country-detail-12'}),'');
reset();
await generateAiImage(null,{jp25Action:'all'});
assert.equal(calls.length,25);assert.equal(c.status,'done');
const outputIds=c.materials.map(m=>m.id);
await handleJp25Action('size-report');
assert.equal(reportRequests,5);assert.equal(c.jp25Report.results.length,25);
assert.equal(calls.length,25,'Report action never submits new images');
assert.deepEqual(c.materials.map(m=>m.id),outputIds,'Report action never replaces outputs');
assert.equal(JP25Workbench.reports.size,0);
assert.equal(c.jp25Report.key,JP25Workbench.reportKey(c));
console.log('JP25 frontend: plan-only, 3 samples, 22-page continuation, stale page retry, save/reload, global edits, safe rendering and full generation passed.');
`;
Promise.resolve(vm.runInContext(`(async()=>{${tests}})()`, context)).catch(e => {console.error(e);process.exitCode=1;});
