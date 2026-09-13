const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const F=require('./workflow.js');
const marketCodes=['KR','JP','US','GB','DE','HU','PL','ES','MX','FR','CZ','TW','HK','TH','VN','MY','SG','PH','ID'];
assert.deepEqual(F.markets.map(m=>m.code),marketCodes);
for(const country of marketCodes){
  for(const suiteKey of ['cod-country-landing-30','cod-country-detail-12']){
    const state={suiteKey,country,count:22};
    assert.equal(F.requestSettings(state).suiteCountry,country);
    assert.equal(F.infer('产品卖点：结实耐用',state).country,country);
  }
}
assert.throws(()=>F.validateSettings({country:'UNKNOWN'}),/目标市场/);
assert.equal(F.suite({}).key,'cod-country-landing-30');
assert.equal(F.suite({suiteKey:'jp-landing-page-25'}).size,'1500x2000');
assert.deepEqual(F.infer('日本市场，主图10张，详情15张',{suiteKey:'jp-landing-page-25',count:25,country:'JP'}),{count:25,country:'JP'});
assert.throws(()=>F.infer('共14张',{suiteKey:'jp-landing-page-25',count:25,country:'JP'}),/25/);
assert.equal(F.infer('美国市场',{suiteKey:'jp-landing-page-25',count:25,country:'JP'}).country,'JP');
assert.deepEqual(F.infer('详情16张，英国市场',{suiteKey:'cod-country-detail-12',count:22,country:'JP'}),{count:16,country:'JP'});
assert.throws(()=>F.infer('详情14张',{suiteKey:'cod-country-detail-12',count:22,country:'JP'}),/12.*16.*20.*22/);
assert.throws(()=>F.suite({suiteKey:'unknown'}),/模式/);
assert.equal(F.hasContent({files:[{}]}),false);
assert.equal(F.hasContent({brief:'原文'}),true);
assert.equal(F.hasContent({jobs:{1:{id:'existing'}}}),true);
assert.deepEqual(F.infer('日本市场，主图8张，详情22张',{count:14,country:'US'}),{count:30,country:'US'});
assert.deepEqual(F.infer('生成14张，英国市场',{count:30,country:'JP'}),{count:14,country:'JP'});
for(const country of marketCodes){
  assert.equal(F.infer('泰国市场，参考韩国日本美国英国图片排版',{country,count:22}).country,country);
}
assert.equal(F.needsMarketRefresh({pages:[{}],country:'TH'}),true);
assert.equal(F.needsMarketRefresh({pages:[{}],country:'TH',plannedCountry:'KR',marketLockVersion:F.marketLockVersion}),true);
assert.equal(F.needsMarketRefresh({pages:[{}],country:'TH',plannedCountry:'TH',marketLockVersion:F.marketLockVersion}),false);
assert.throws(()=>F.infer('共100张',{}),/8–30/);
assert.equal(F.canAutoGenerate({autoGenerate:true,ready:true,compiledReady:false}),false);
assert.equal(F.classifyError({payload:{status:'error',outcomeUncertain:true}}),'待核对');
assert.equal(F.classifyError({payload:{status:'error',outcomeUncertain:false}}),'失败');
assert.deepEqual(F.style('背景#f1eff0',{},[]).colors,['#f1eff0']);
const node=()=>({addEventListener(){},classList:{toggle(){},add(){},remove(){}},value:'',disabled:false,hidden:false,style:{}});
const elements=new Map();
const context=vm.createContext({window:{StudioFlow:F,addEventListener(){}},document:{querySelector:s=>{if(!elements.has(s))elements.set(s,node());return elements.get(s);},addEventListener(){}},matchMedia:()=>({matches:false}),setTimeout,clearTimeout,setInterval,clearInterval,console,FormData,URL,Blob,crypto:require('node:crypto').webcrypto});
vm.runInContext(fs.readFileSync('./app.js','utf8').replace(/init\(\);\s*$/,''),context);
vm.runInContext('globalThis.originalGenerate=generate;',context);
const layers={};for(const k of ['taskAnchor','emotionAnchor','visualNarrative','layoutAndCopy','colorScheme','styleDirection','hardConstraints'])layers[k]='fixture';
context.fixture={page:1,visualEnhancement:{companyPromptLayers:layers}};
async function run(){
 const file=(content,name='product.png')=>Object.assign(new Blob([content],{type:'image/png'}),{name});
 const inputState={brief:'完整卖点',country:'TH',count:22,suiteKey:'cod-country-detail-12',files:[file('abc')]};
 const signature=await F.inputFingerprint(inputState);
 assert.equal(await F.inputFingerprint({...inputState,files:[file('abc')]}),signature);
 for(const changed of [{brief:'新卖点'},{country:'KR'},{count:12},{files:[file('abcd')]},{files:[file('abc','detail.png')]}])
   assert.notEqual(await F.inputFingerprint({...inputState,...changed}),signature);
 await vm.runInContext(`(async()=>{
   save=async()=>{};render=()=>{};message=async()=>{};status=()=>{};
   current={pages:[],jobs:{},files:[],brief:'产品卖点',count:8,country:'JP',autoGenerate:true};
   globalThis.calls=0;globalThis.generated=[];
   api=async()=>{calls++;return {suiteCount:8,suitePages:Array.from({length:8},(_,i)=>({...fixture,page:i+1})),companyPromptStatus:{ready:true},director:{sellingPointCoverage:{complete:true}},studioCompiledReady:true,studioPromptPreview:[{page:1,prompt:'fixture'}]};};
   generate=async pages=>{generated=pages;};
   await plan();
 })()`,context);
 assert.equal(context.calls,1);assert.equal(context.generated.length,8);
 await vm.runInContext(`(async()=>{current={pages:[],jobs:{},files:[],brief:'test',count:8,autoGenerate:true};paused=false;calls=0;generated=[];api=async()=>{calls++;return {suiteCount:8,suitePages:[],companyPromptStatus:{ready:false},director:{}}};await plan();})()`,context);
 assert.equal(context.calls,2);assert.equal(context.generated.length,0);
 await vm.runInContext(`(async()=>{current={pages:[],jobs:{},files:[],brief:'test',count:8,autoGenerate:false};paused=false;generated=[];api=async()=>({suiteCount:8,suitePages:[fixture],companyPromptStatus:{ready:true},studioCompiledReady:true,director:{}});await plan();})()`,context);
 assert.equal(context.generated.length,0);
 for(const [key,count,country,size] of [
   ['cod-country-landing-30',14,'US','750x1000'],
   ['jp-landing-page-25',25,'JP','1500x2000'],
   ['cod-country-detail-12',22,'GB','750x1000'],
 ]){
   context.modeFixture={key,count,country,size};
   await vm.runInContext(`(async()=>{
     const m=modeFixture;paused=false;
     current={suiteKey:m.key,files:[],brief:'逐字保留卖点 #abcdef',count:m.count,country:m.country,pages:[],jobs:{},autoGenerate:false,id:crypto.randomUUID()};
     globalThis.planRequests=[];
     api=async(path,options)=>{planRequests.push(Object.fromEntries(options.body));return {suiteKey:m.key,suiteCount:m.count,size:m.size,suiteCountry:m.country,suitePages:[fixture],companyPromptStatus:{ready:true},studioCompiledReady:true,director:{}};};
     await plan();await plan();
     globalThis.imageRequests=[];
     api=async(path,options)=>{
       if(path==='ai-image-config')return {aiImage:{model:'fixture-image'}};
       if(path==='ad-launch-ai-image-edit'){imageRequests.push(Object.fromEntries(options.body));return {jobId:'fixture-job'};}
       return {material:{previewUrl:'https://example.com/fixture.png'}};
     };
     await originalGenerate([1]);await originalGenerate([1]);
   })()`,context);
   for(const request of [...context.planRequests,...context.imageRequests]){
     assert.equal(request.suiteKey,key);assert.equal(request.size,size);
     assert.equal(request.suiteCountry,country);assert.equal(request.suiteCount,String(count));
     assert.equal(request.prompt,'逐字保留卖点 #abcdef');
     assert.equal(request.suiteBrief,request.prompt);
     assert.equal(request.companyEffectMode,'true');
   }
   assert.equal(context.imageRequests.length,2);
   assert.deepEqual(JSON.parse(context.imageRequests[0].suitePageIndexes),[1]);
 }
 await vm.runInContext(`(async()=>{
   current={suiteKey:'jp-landing-page-25',count:25,country:'JP',files:[],pages:[fixture],jobs:{1:{state:'完成',url:'original'}},ready:true,compiledReady:true};
   api=async()=>({suiteKey:'cod-country-landing-30',suiteCount:25,suitePages:[]});
   globalThis.mismatchStopped=false;try{await plan();}catch(e){mismatchStopped=true;}
   globalThis.preservedPageCount=current.pages.length;globalThis.preservedURL=current.jobs[1].url;
   globalThis.blockedReady=current.ready;
 })()`,context);
 assert.equal(context.mismatchStopped,true);assert.equal(context.preservedPageCount,1);
 assert.equal(context.preservedURL,'original');assert.equal(context.blockedReady,false);
 await vm.runInContext(`(async()=>{
   user={username:'fixture'};busy=false;sessions=[];
   current={id:'old',brief:'原有需求',suiteKey:'cod-country-landing-30',files:[],messages:[],pages:[fixture],jobs:{1:{id:'original-job'}}};
   sessions.push(current);await switchSuite('jp-landing-page-25');
   globalThis.switched={length:sessions.length,oldJob:sessions[1].jobs[1].id,key:current.suiteKey,count:current.count,country:current.country};
   current.files=[{name:'kept.png'}];await switchSuite('cod-country-detail-12');
   globalThis.emptySwitch={length:sessions.length,count:current.count,file:current.files[0].name};
   busy=true;await switchSuite('jp-landing-page-25');globalThis.busyKey=current.suiteKey;busy=false;
 })()`,context);
 assert.equal(context.switched.length,2);assert.equal(context.switched.oldJob,'original-job');
 assert.equal(context.switched.key,'jp-landing-page-25');assert.equal(context.switched.count,25);
 assert.equal(context.emptySwitch.length,2);assert.equal(context.emptySwitch.count,22);assert.equal(context.emptySwitch.file,'kept.png');
 assert.equal(context.busyKey,'cod-country-detail-12');
 await vm.runInContext(`(async()=>{
   paused=false;current={suiteKey:'cod-country-landing-30',country:'TH',count:8,files:[],brief:'完整来源',pages:Array.from({length:8},(_,i)=>({...fixture,page:i+1})),
     jobs:{},ready:true,compiledReady:true,autoGenerate:false,marketLockVersion:F.marketLockVersion,plannedCountry:'TH',prompts:Array.from({length:8},(_,i)=>({page:i+1,prompt:'fixture'}))};
   current.planInputSignature=await F.inputFingerprint(current);
   globalThis.cacheCalls=0;api=async()=>{cacheCalls++;throw Error('Unexpected director request');};
   await plan();globalThis.reused=current.localPlanReuse;
   globalThis.forceFlags=[];
   api=async(path,options)=>{
     forceFlags.push(options.body.get('forceReanalyze'));const complete=forceFlags.length>1;
     return {suiteKey:current.suiteKey,suiteCountry:'TH',suiteCount:8,size:'750x1000',
       suitePages:Array.from({length:complete?8:3},(_,i)=>({...fixture,page:i+1})),
       companyPromptStatus:{ready:complete},studioCompiledReady:complete,director:{}};
   };
   await plan(true);
 })()`,context);
 assert.equal(context.cacheCalls,0);assert.equal(context.reused,true);
 assert.deepEqual(Array.from(context.forceFlags),['true','false']);
 await vm.runInContext(`(async()=>{
   current.ready=true;current.compiledReady=false;current.autoGenerate=true;
   globalThis.compileOnlyCalls=[];
   api=async(path,options)=>{compileOnlyCalls.push({path,body:JSON.parse(options.body)});
     return {studioCompiledReady:true,studioPromptPreview:current.pages.map(p=>({page:p.page,prompt:'compiled'})),studioTimings:{compileOnly:true,compileMs:1,upstreamMs:0}};};
   await retryCompile();globalThis.compileRestored=current.compiledReady;
 })()`,context);
 assert.equal(context.compileOnlyCalls.length,1);assert.equal(context.compileOnlyCalls[0].path,'studio-compile');
 assert.equal(context.compileOnlyCalls[0].body.suiteBrief,'完整来源');assert.equal(context.compileRestored,true);
 console.log('workflow: inference, source colors, safe auto-run, error classification, bounded continuation and manual approval passed');
 console.log('suite routing: three modes, plan/continue/generate/retry, mismatch guard, legacy defaults and session isolation passed');
 console.log('speed: exact input/file fingerprint, complete-plan zero-call reuse, and force-only-first-round passed');
}
run().catch(e=>{console.error(e);process.exitCode=1});
