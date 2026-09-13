const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('../sku_board/static/app.js','utf8');
const start=source.indexOf('async function cancelAiImageGeneration() {');
const end=source.indexOf('async function generateAiImageSuitePages(',start);
const sandbox={aiImageGenerationAbortController:null,persistAiImageState(){},renderAiImageForm(){},showToast(){}};
const ctx=vm.createContext(sandbox);vm.runInContext(source.slice(start,end),ctx);
(async()=>{
  for(const refreshed of [false,true]){
    const conversation={id:'fixture',status:'planning',activeOperationId:'a'.repeat(32),jobId:'AIJ-FIXTURE'};
    let aborted=false,request;
    sandbox.aiImageActiveConversation=()=>conversation;
    sandbox.aiImageGenerationAbortController=refreshed?null:{operationId:'a'.repeat(32),abort(){aborted=true;}};
    sandbox.api=async(path,options)=>{request={path,...options};return {message:'已记录取消，已发出的请求仍可能执行'};};
    await vm.runInContext('cancelAiImageGeneration()',ctx);
    assert.equal(aborted,!refreshed);assert.equal(request.path,'/api/sku-board/ai-image-cancel');
    assert.equal(request.signal,undefined);assert.equal(JSON.parse(request.body).operationId,'a'.repeat(32));
    assert.equal(conversation.cancelRequested,true);
  }
  console.log('original panel cancellation: live controller and refreshed conversation both notify backend without an aborted signal');
})().catch(e=>{console.error(e);process.exitCode=1;});
