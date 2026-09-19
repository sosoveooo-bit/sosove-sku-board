const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname, '../static/app.js'), 'utf8');
let requests = [];
let syncFailure = false;
const fresh = [{page: 1, agentPrompt: {resolvedPrompt: 'saved'}}];
const context = {
  aiImageUsesVisualAgents: c => c.agent,
  aiImageSuiteCount: () => 1,
  aiImageGenerationAbortController: null,
  syncAiImageStateFromConversation(){},
  api: async (path, options) => {
    requests.push({path, body: JSON.parse(options.body)});
    if (syncFailure) throw Error('动态方案尚未完整');
    return {ok: true, suitePages: fresh, companyPromptStatus: {ready: true}};
  },
};
vm.createContext(context);
vm.runInContext(source.slice(source.indexOf('function aiImageSavedPlanError('),
  source.indexOf('async function generateAiImageSuitePages(')), context);
(async () => {
  const c = {agent:true,suiteKey:'cod-country-landing-30',suitePages:[{page:1,old:true}],size:'750x1000',suiteCountry:'JP'};
  await context.syncAiImageSavedPlan(c,'original brief');
  assert.equal(c.suitePages, fresh);
  assert.equal(requests.length,1);
  assert.equal(requests[0].body.suiteBrief,'original brief');
  assert.equal(requests[0].path,'/api/sku-board/visual-agent-plan-sync');
  await context.syncAiImageSavedPlan({agent:false},'legacy');
  assert.equal(requests.length,1);
  const start = source.indexOf('async function generateAiImageSuitePages(');
  vm.runInContext(source.slice(start, source.indexOf('\nasync function ',start+1)), context);
  syncFailure = true;
  await assert.rejects(context.generateAiImageSuitePages({conversation:c,effectiveIntent:'brief'}), /尚未完整/);
  assert.ok(requests.every(r => r.path.endsWith('plan-sync')));
  syncFailure = false;
  let submissions=0;
  Object.assign(context, {
    aiImageSuiteConfig:()=>({count:24,unit:'图'}),
    aiImageGenerationProfile:()=>({maxRetries:2,autoRetryCycles:2}),
    createAiImageSuiteRunId:()=> 'run',
    aiImageGenerationNodeForPage:()=>({}),
    aiImageSuiteUsesGeneratedStyleAnchor:()=>false,
    updateAiImageSuiteProgress(){},throwIfAiImageGenerationAborted(){},
    buildAiImageSuiteFormData:()=> new Object(),
    isAiImageGenerationAborted:()=>false,
    aiImageSuiteTransientError:()=>false,aiImageSuiteQuotaError:()=>false,
    aiImageGenerationWorkerCount:()=>3,
    api:async path=> {
      if(path.endsWith('plan-sync')) return {suitePages:fresh,companyPromptStatus:{ready:true}};
      submissions++;
      throw Error('动态页面内容与已保存版本不同：第 1 页 agentPrompt');
    },
  });
  await assert.rejects(context.generateAiImageSuitePages({conversation:c,effectiveIntent:'brief',targetPages:Array.from({length:24},(_,i)=>i+1)}), /agentPrompt/);
  assert.equal(submissions,1,'shared plan failure must stop the other 23 jobs and all retries');
  console.log('Saved-plan preflight, legacy bypass and suite fail-fast passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
