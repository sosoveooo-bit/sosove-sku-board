const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),source=fs.readFileSync(path.join(root,'static/app.js'),'utf8');
function fn(name){const start=source.search(new RegExp(`^(?:async )?function ${name}\\(`,'m'));assert.ok(start>=0,name);const next=source.slice(start+1).search(/^(?:async )?function \w+\(/m);return source.slice(start,next<0?undefined:start+1+next);}
const ctx=vm.createContext({assert,console,FormData,setTimeout,clearTimeout});
vm.runInContext(fs.readFileSync(path.join(root,'static/jp25-workbench.js'),'utf8')+`
const config={key:'jp-landing-page-25',count:25,unit:'张',planVersion:'director-v35-editorial-craft-source-complete',planTitle:'日本25图'};
const AI_IMAGE_COMPANY_EFFECT_SUITE_KEYS=new Set(),AI_IMAGE_DIRECTOR_STAGES=[{label:'分析'},{label:'方案'},{label:'Prompt'},{label:'完成'}];
const window={setInterval:()=>1,clearInterval:()=>{},setTimeout:fn=>fn(),clearTimeout:()=>{}};
const state={auth:{user:{}},aiImages:{}},aiImageGenerationAbortController=null;
let apiCalls=0,failTransport=false,ready=false,c;
const warning='AI 导演没有返回方案正文（输出额度已耗尽）';
const payload={suitePages:Array.from({length:25},(_,i)=>({page:i+1})),suitePlanVersion:config.planVersion,director:{warning,status:'warning',source:'rules'}};
const aiImageSuiteConfig=()=>config,aiImageSuiteActive=()=>true,aiImageDirectorMode=()=>'company';
const loadAiImageConfig=async()=>{},setAiImageDirectorStage=()=>{},aiImageReferenceRoleKey=()=> 'product';
const syncAiImageStateFromConversation=()=>{},renderAiImageSidebar=()=>{},renderAiImageResults=()=>{};
const enforceAiImageCodSourceCoverage=()=>{},applyAiImageResolvedReferenceBindings=()=>{};
const aiImageSuitePlanSignature=()=> 'new-signature';
const aiImageCompanyPromptStatus=()=>({ready,readyCount:ready?25:0,missingPages:ready?[]:Array.from({length:25},(_,i)=>i+1)});
const api=async()=>{apiCalls++;if(failTransport)throw new Error(warning);return payload;};
const aiImageSavedPlanError=()=>false,esc=s=>String(s),aiImageMissingSuitePages=()=>[];
const aiImageActiveConversation=()=>c;
function reset(){apiCalls=0;ready=false;failTransport=false;c={id:'fixture',suiteKey:config.key,suitePlanVersion:'old-version',suitePlanSignature:'old-signature',suitePages:payload.suitePages,referenceImages:[],materials:Array.from({length:25},(_,i)=>({id:'old-'+i,suitePage:i+1})),remoteSummary:{succeeded:25,message:'已显示25/25',recoveryMessage:'套图已完整，无需继续同步。'}};}
`+['prepareAiImageSuitePlan','aiImageErrorDiagnosis','aiImageCurrentSuiteMaterials','renderAiImageRecoveryBlock'].map(fn).join('\n'),ctx);
Promise.resolve(vm.runInContext(`(async()=>{
reset();await assert.rejects(prepareAiImageSuitePlan(c,'product','brief'),/七层Prompt/);
assert.match(c.error,/AI 策划/);assert.match(c.error,/没有返回方案正文/);
assert.equal(c.materials.length,25);assert.equal(c.suitePlanSignature,'');
assert.equal(aiImageErrorDiagnosis(c.error).title,'AI 策划尚未完成');
assert.equal(aiImageCurrentSuiteMaterials(c).length,0);
const html=renderAiImageRecoveryBlock(c);assert.match(html,/历史图片/);assert.doesNotMatch(html,/套图已完整/);assert.ok(html.includes('0/25'));
reset();failTransport=true;await assert.rejects(prepareAiImageSuitePlan(c,'product','brief'),/没有返回方案正文/);
assert.match(c.error,/AI 策划/);assert.equal(c.materials.length,25);
assert.notEqual(c.director.stage,'complete');
reset();ready=true;await prepareAiImageSuitePlan(c,'product','brief');
assert.equal(c.error,'');assert.equal(c.suitePlanSignature,'new-signature');
c.materials[0].jp25Revision=JP25Workbench.revision(c,1);assert.equal(aiImageCurrentSuiteMaterials(c).length,1);
assert.equal(aiImageCurrentSuiteMaterials({...c,suiteKey:'cod-country-detail-12'}).length,25);
console.log('JP25 planning errors retain actual causes, preserve old images and count only current outputs.');
})()`,ctx)).catch(e=>{console.error(e);process.exitCode=1;});
