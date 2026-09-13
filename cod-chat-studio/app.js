'use strict';
const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const F=window.StudioFlow;
let db,user,config,sessions=[],current,busy=false,paused=false,historyUI,cancelSending=false;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const isEngineUnavailable=e=>e?.payload?.code==='ENGINE_UNAVAILABLE'||/本地引擎连接中断/.test(e?.payload?.error||'');

async function api(path,options={}) {
  if(options.method==='POST'&&['ai-image-suite-plan-upload','ad-launch-ai-image-edit'].includes(path)&&options.body instanceof FormData){
    current.activeOperationId=current.activeOperationId||crypto.randomUUID().replaceAll('-','');
    options.body.set('operationId',current.activeOperationId);await save();
  }
  const r=await fetch('/api/sku-board/'+path,options);
  const d=await r.json();
  if(d.cancelled){const error=Error(d.message||'任务已取消');error.name='AbortError';error.payload=d;throw error;}
  if(!r.ok||d.ok===false){const e=Error(d.error||d.message||`请求失败 ${r.status}`);e.payload=d;throw e;}
  return d;
}
function openDB(){return new Promise((resolve,reject)=>{const r=indexedDB.open('cod-chat-studio-v1',1);r.onupgradeneeded=()=>r.result.createObjectStore('sessions',{keyPath:'id'});r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});}
function save(record=current){return new Promise((resolve,reject)=>{const t=db.transaction('sessions','readwrite');t.objectStore('sessions').put(record);t.oncomplete=resolve;t.onabort=()=>reject(t.error||Error('会话保存失败'));t.onerror=()=>reject(t.error);});}
async function message(text,role='ai'){current.messages.push({role,text});await save();render();}
function status(text){$('#status').textContent=text;}
function newSession(suiteKey){const mode=F.suite({suiteKey});return {id:crypto.randomUUID(),owner:user?.username||'',title:'新的产品创作',suiteKey:mode.key,messages:[],files:[],pages:[],jobs:{},brief:'',country:mode.country||'JP',count:mode.count,autoGenerate:true,phase:'等待产品'};}
function fresh(suiteKey=current?.suiteKey){current=newSession(suiteKey);sessions.unshift(current);render();}
async function changeHistory(action,id,value){
  if(busy||cancelSending)throw Error('当前正在处理任务，请结束或暂停后再操作历史对话。');
  const target=sessions.find(s=>s.id===id&&s.owner===user?.username);
  if(!user||!target)throw Error('该对话已不存在，请刷新历史列表。');
  if(!['rename','favorite','delete'].includes(action))throw Error('未知历史操作');
  const title=String(value||'').trim();
  if(action==='rename'&&(!title||title.length>80))throw Error('请输入1–80个字符的名称。');
  busy=true;render();
  try{
    if(action==='delete'){
      const remaining=sessions.filter(s=>s.id!==id),isCurrent=current?.id===id;
      const replacement=isCurrent?(remaining[0]||newSession(target.suiteKey)):current;
      await new Promise((resolve,reject)=>{
        const tx=db.transaction('sessions','readwrite'),store=tx.objectStore('sessions');store.delete(id);
        if(isCurrent&&!remaining.length)store.put(replacement);
        tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);tx.onabort=()=>reject(tx.error||Error('删除未完成'));
      });
      sessions=remaining;if(!sessions.length)sessions.push(replacement);
      if(isCurrent){current=replacement;$('#input').value='';}
      status('已删除该浏览器中的对话记录；后台图片文件与任务保留。');
    }else{
      const updated={...target,...(action==='rename'?{title,customTitle:true}:{favorite:!target.favorite})};
      await save(updated);Object.assign(target,updated);
      status(action==='rename'?'对话已重命名。':target.favorite?'已收藏，显示在历史列表前面。':'已取消收藏。');
    }
  }finally{busy=false;render();}
}
async function switchSuite(key){
  if(busy||cancelSending||!user){render();return;}
  const mode=F.suite({suiteKey:key});if(mode.key===F.suite(current).key)return;
  if(F.hasContent(current)){await save();fresh(mode.key);status(`旧对话已保留，已新建「${mode.label}」对话。请上传参考图并填写需求。`);}
  else{Object.assign(current,{suiteKey:mode.key,count:mode.count,country:mode.country||current.country||'JP'});status(`已切换到${mode.label}，已上传参考图保留。`);}
  await save();render();
}
function imageURL(value){try{const u=new URL(value,location.origin);if(u.protocol==='data:'&&value.startsWith('data:image/'))return value;if(u.origin===location.origin&&u.pathname.startsWith('/api/sku-board/ai-image-output/'))return u.href;if(u.hostname==='127.0.0.1'&&u.port==='8793'&&u.pathname.startsWith('/api/sku-board/ai-image-output/'))return u.pathname+u.search;if(u.protocol==='https:')return u.href;}catch{}return '';}
function filterHistory(){const query=$('#searchHistory').value.trim().toLowerCase();document.querySelectorAll('[data-history-id]').forEach(row=>{row.hidden=!row.textContent.toLowerCase().includes(query);row.classList.toggle('active',row.dataset.historyId===current?.id);});}
function attachThumbs(target,removable=false){
  target.replaceChildren();current.files.forEach((file,index)=>{const wrap=document.createElement('span');wrap.className='reference-thumb';const img=document.createElement('img');const u=URL.createObjectURL(file);img.src=u;img.alt=file.name;img.onload=()=>URL.revokeObjectURL(u);img.onerror=()=>URL.revokeObjectURL(u);wrap.append(img);
    if(removable&&!busy&&!current.pages.length){const b=document.createElement('button');b.textContent='×';b.dataset.removeFile=index;b.setAttribute('aria-label','移除 '+file.name);wrap.append(b);}target.append(wrap);});
}
function render(){
  if(!current)return;
  historyUI?.close(false);
  document.body.classList.toggle('has-messages',current.messages.length>0);
  const mode=F.suite(current);
  $('#suite').value=mode.key;$('#suite').disabled=busy||cancelSending||!user;
  $('#suiteHint').textContent=mode.hint+' · 市场以下拉框为准，参考文案不会自动改国家';
  $('#input').placeholder=`上传图片，直接描述产品、卖点、市场与风格。\n当前${mode.label}：共${current.count}张。可写“先出方案”，或填写卖点后直接生成。`;
  $('.settings > span').textContent=mode.size.replace('x',' × ')+' · 高质量';
  $('#count').min=mode.counts?Math.min(...mode.counts):mode.min;$('#count').max=mode.counts?Math.max(...mode.counts):mode.max;
  $('#count').title=mode.hint;
  $('#history').innerHTML=[...sessions].sort((a,b)=>Number(!!b.favorite)-Number(!!a.favorite)).map(s=>`<div class="history-row" data-history-id="${esc(s.id)}"><button class="history-open" data-session="${esc(s.id)}" title="${esc(s.title)}" ${busy?'disabled':''}><small class="history-mode">${s.favorite?'★ 已收藏 · ':''}${esc(F.suite(s).label)}</small><span class="history-title">${esc(s.title)}</span></button><button class="history-more" data-history-menu="${esc(s.id)}" aria-label="对话菜单：${esc(s.title)}" aria-haspopup="menu" ${busy?'disabled':''}>⋯</button></div>`).join('');
  $('#messages').innerHTML=current.messages.map(m=>`<div class="bubble ${m.role==='ai'?'ai':'user'}">${esc(m.text)}</div>`).join('');
  $('#country').innerHTML=F.markets.map(m=>`<option value="${esc(m.code)}">${esc(m.label)}</option>`).join('');
  $('#country').value=current.country;$('#count').value=current.count;
  $('#country').disabled=busy||current.pages.length>0||!!mode.country;$('#count').disabled=busy||current.pages.length>0||mode.counts?.length===1;
  $('#autoGenerate').checked=current.autoGenerate===true;$('#autoGenerate').disabled=busy;
  attachThumbs($('#files'),true);
  const ready=F.readyCount(current.pages),done=Object.values(current.jobs).filter(j=>j.state==='完成').length;
  $('#workflow').innerHTML=current.brief?`<strong>${esc(current.phase||'方案处理中')}</strong><span>参考图 ${current.files.length} 张</span><span>线上 Brief ${ready}/${current.count}</span><span>图片 ${done}/${current.count}</span>`:'';
  $('#plan').innerHTML=renderPlan();
  $('#results').innerHTML=Object.entries(current.jobs).map(([page,j])=>`<article class="result"><strong>第 ${esc(page)} 页 · ${esc(j.state)}</strong>${j.url?`<a href="${esc(imageURL(j.url))}" target="_blank" rel="noopener"><img src="${esc(imageURL(j.url))}" alt="第${esc(page)}页成图" loading="lazy"></a>`:''}<p>${esc(j.error||j.message||'')}</p><p class="job-id">${esc(j.id||'')}</p>${j.id&&j.state!=='完成'?`<button data-sync="${esc(page)}" ${busy?'disabled':''}>同步已有任务</button>`:''}${['失败','完成'].includes(j.state)?`<button data-retry="${esc(page)}" ${busy?'disabled':''}>${j.state==='完成'?'按本页要求重生成':'重试此页'}</button>`:''}${j.state==='待核对'&&!j.id?'<p>提交结果不明确，请到原面板核对任务；本页暂不重复提交。</p>':''}</article>`).join('');
  $('#send').disabled=busy||cancelSending||!user;$('#send').textContent=current.autoGenerate?'发送并制作 ↗':'发送并分析 ↗';
  $('#upload').disabled=busy||current.pages.length>0||!user;$('#new').disabled=busy||cancelSending||!user;
  $('#pause').hidden=!busy;filterHistory();
  $('#cancelTask').disabled=!user||cancelSending||(!current.activeOperationId&&!Object.values(current.jobs).some(j=>j.id));
  $('#cancelStatus').textContent=current.cancelMessage||'刷新页面不会取消后台任务';
}
function renderPlan(){
  if(!current.pages.length)return '';
  const d=current.director||{},a=F.style(current.brief,d,current.pages),ready=F.readyCount(current.pages);
  const table=current.pages.map(p=>{const v=p.visualEnhancement||{},l=v.companyPromptLayers||{},complete=F.readyCount([p])===1;return `<tr><td>${esc(p.page)}</td><td>${esc(p.title||p.role||p.section||'产品展示')}</td><td>${esc(p.sourcePointVerbatim||p.focusDescription||p.sellingPoint||p.focus||p.headline||'待返回来源卖点')}</td><td>${esc(complete?(v.shotConcept||l.visualNarrative):'本页来源已整理，等待线上 AI 创作画面方案')}<span class="row-status">${complete?'线上摄影 Brief 已返回':'待续写 · 非最终方案'}</span></td></tr>`;}).join('');
  const previews=current.prompts||[];
  const analysed=['model','cache'].includes(d.source);
  return `<section class="analysis-card"><h3>产品分析</h3><p>${esc(analysed?(d.productSummary||'产品分析摘要待返回'):'已整理输入内容，线上产品分析尚未完成。')}</p><small>${esc(d.activeModel||d.model||'当前导演模型')} · ${analysed?(d.cacheHit?'复用匹配缓存':'线上分析已返回'):'等待线上分析'} · 参考图拆解记录 ${Array.isArray(d.referenceBreakdown)?d.referenceBreakdown.length:0} 张</small></section>
    <h2>落地页方案 <small>${current.pages.length} 张</small></h2><div class="plan-table-wrap"><table class="plan-table"><thead><tr><th>#</th><th>类型</th><th>核心卖点／原文</th><th>画面方向</th></tr></thead><tbody>${table}</tbody></table></div>
    <section class="anchor-card"><h3>风格锚点 <small>文字化 · 非首图位图</small></h3><div class="swatches">${a.colors.map(hex=>`<span class="swatch"><i style="background:${hex}"></i>${hex}</span>`).join('')}</div><p><b>配色：</b>${esc(a.colorText)}</p><p><b>字体、质感与风格：</b>${esc(a.direction)}</p><small>${esc(a.source)}<br>${esc(a.rule)}</small></section>
    <div class="summary-line">线上 Brief ${ready}/${current.count} · 编译提示词 ${previews.length}/${current.count} · ${esc(current.promptNote||'方案完整后编译')}</div>
    ${current.localPlanReuse?'<p class="summary-line">本次复用当前完整方案，没有新增导演请求。</p>':current.planTimings?`<p class="summary-line">${current.planTimings.compileOnly?'本次仅本地编译，未调用AI':`上次上游策划 ${(current.planTimings.upstreamMs/1000).toFixed(1)}秒${d.creativePassStats?.wallTimeMs&&!d.cacheHit?`（其中逐页创作 ${(d.creativePassStats.wallTimeMs/1000).toFixed(1)}秒）`:''}`} · 本地编译 ${(current.planTimings.compileMs/1000).toFixed(1)}秒${current.planTimings.compileCacheHit?' · 命中编译缓存':''}</p>`:''}
    ${d.creativePassStats?.budgetExhausted?`<p class="warning">本轮导演处理时限已到，等待下一轮续写${d.creativePassStats.deferredPageNumbers?.length||0}页。这不是额度不足；已完成的线上 Brief 已保留。</p>`:''}
    ${d.creativePassWarning?`<details class="warning"><summary>查看本轮导演异常详情</summary><p>${esc(d.creativePassWarning)}</p></details>`:''}
    ${!current.ready&&d.creativePassStats?.requestErrors?.length?`<details class="warning"><summary>查看实际请求与重试记录</summary>${d.creativePassStats.requestErrors.map(e=>`<p>第${esc((e.pages||[]).join('、'))}页：${esc(e.message)}</p>`).join('')}</details>`:''}${current.compileError?`<p class="warning">${esc(current.compileError)}</p>`:''}
    ${F.needsMarketRefresh(current)?'<p class="warning">这套方案早于市场锁定更新或市场已变化。图片与原提示词已保留，请点击“更新市场方案”重新策划后再提交新图片；已有任务仍可同步。</p>':''}
    ${current.compileErrorId?`<small>编译错误编号：${esc(current.compileErrorId)} · ${esc(current.compileErrorCode||'')}</small>`:''}
    <div class="plan-actions"><button id="continuePlan" ${busy?'disabled':''}>${F.needsMarketRefresh(current)?'更新市场方案':current.ready?'复用完整方案':'继续缺页策划'}</button>${current.ready&&!current.compiledReady?`<button id="retryCompile" ${busy||F.needsMarketRefresh(current)?'disabled':''}>重试本地编译（不调用AI）</button>`:''}<button id="replan" ${busy?'disabled':''}>重新AI策划</button><button id="generate" ${busy||!current.ready||!current.compiledReady||F.needsMarketRefresh(current)?'disabled':''}>生成／同步未完成页</button><button id="exportPrompts" ${!previews.length?'disabled':''}>下载方案与提示词</button></div>
    ${current.pages.map(p=>{const prompt=previews.find(x=>Number(x.page)===Number(p.page))?.prompt;return `<details class="prompt-details"><summary>第 ${esc(p.page)} 张 · ${esc(p.headline||p.title||p.focus||'产品展示')} · 查看提示词</summary>${prompt?`<button data-copy="${esc(p.page)}">复制本页提示词</button><pre>${esc(prompt)}</pre>`:'<p>等待完整线上 Brief 编译，本页未使用本地模板代替。</p>'}<label>本页补充要求<textarea data-edit="${esc(p.page)}" ${busy?'disabled':''}>${esc(p.chatInstruction||'')}</textarea></label></details>`;}).join('')}`;
}
function form(){const f=new FormData();for(const [k,v] of Object.entries({prompt:current.brief,suiteBrief:current.brief,...F.requestSettings(current),useDirector:'true',companyEffectMode:'true',forceReanalyze:'false'}))f.append(k,String(v));current.files.forEach((file,i)=>f.append('reference'+i,file,file.name));return f;}
async function plan(force=false){
  const signature=await F.inputFingerprint(current);
  if(!force&&F.canReusePlan(current,signature)){
    current.localPlanReuse=true;current.phase='方案已复用';
    await message('产品参考图、原始需求、市场、模式和页数未变化，直接复用完整方案与提示词，不再调用导演。');
    const remaining=F.remaining(current);if(!paused&&remaining.length&&F.canAutoGenerate(current))await generate(remaining);
    return;
  }
  current.localPlanReuse=false;
  if(force){current.ready=false;current.compiledReady=false;}
  let best=force?0:F.readyCount(current.pages),stagnant=0;
  for(let round=1;round<=5&&!paused;round++){
    current.phase=`线上策划 · 第${round}轮`;await save();render();
    const started=Date.now();const timer=setInterval(()=>status(`线上AI正在分析与编写 Brief，已等待 ${Math.round((Date.now()-started)/1000)} 秒。当前本轮未返回，可点击暂停后续步骤。`),1000);
    const request=form();if(force&&round===1)request.set('forceReanalyze','true');
    let d;try{d=await api('ai-image-suite-plan-upload',{method:'POST',body:request});}finally{clearInterval(timer);}
    const count=Number(d.suiteCount)||current.count;
    const expected=F.requestSettings(current);
    const wrongPageMarket=(d.suitePages||[]).some(p=>p.country&&p.country!==expected.suiteCountry);
    if(wrongPageMarket||(d.suiteKey&&d.suiteKey!==expected.suiteKey)||count!==current.count||(d.size&&d.size!==expected.size)||(d.suiteCountry&&d.suiteCountry!==expected.suiteCountry)){
      current.autoGenerate=false;current.ready=false;current.compiledReady=false;
      throw Error('引擎返回的模式、页数、尺寸或市场与当前设置不一致，已暂停；原有方案与图片保留，请核对后续写。');
    }
    const edits=new Map(current.pages.map(p=>[p.page,p.chatInstruction]));
    current.pages=(d.suitePages||[]).map(p=>({...p,chatInstruction:edits.get(p.page)||''}));
    current.count=count;current.director=d.director;current.planVersion=d.suitePlanVersion;
    current.marketLockVersion=F.marketLockVersion;current.plannedCountry=current.country;
    current.ready=d.companyPromptStatus?.ready===true&&d.director?.sellingPointCoverage?.complete!==false;
    current.compiledReady=d.studioCompiledReady===true;
    current.planInputSignature=signature;current.planTimings=d.studioTimings||null;
    current.prompts=d.studioPromptPreview||[];current.promptNote=d.studioPromptNote||'';current.compileError=d.studioCompileError||'';
    current.compileErrorCode=d.studioCompileErrorCode||'';current.compileErrorId=d.studioCompileErrorId||'';
    const completed=F.readyCount(current.pages);current.phase=current.ready?'方案已完成':'继续缺页策划';
    await message(`第${round}轮已返回：线上 Brief ${completed}/${current.count} 页。${current.ready?'产品分析、逐页方案和风格锚点已整理在下方。':d.director?.creativePassStats?.budgetExhausted?'本轮时限已到，已完成页保留，下一轮使用新的时限继续缺页；这不代表模型额度不足。':'保留已完成页，下一轮只续写缺失内容。'}`);
    if(current.ready||d.director?.sellingPointCoverage?.complete===false)break;
    stagnant=completed>best?0:stagnant+1;best=Math.max(best,completed);
    if(stagnant>=2){await message('连续两轮没有新增完整页面，已停止自动续写。方案已保留，可稍后继续。');break;}
  }
  if(!paused&&F.canAutoGenerate(current)){await message('方案与提示词已完整，按已开启的自动生图设置开始逐页提交。');await generate(F.remaining(current));}
  else if(!paused&&current.ready)await message(current.compiledReady?'方案已完成，点击“生成／同步未完成页”开始生图。':'逐页提示词编译还未完成，自动生图已暂停。');
}
async function retryCompile(){
  if(!current.ready||F.needsMarketRefresh(current))throw Error('请先完成当前市场的线上方案，再重试本地编译。');
  current.phase='仅重试本地编译';current.localPlanReuse=false;await save();render();
  const request={...F.requestSettings(current),prompt:current.brief,suiteBrief:current.brief,
    suitePages:current.pages,suitePlanVersion:current.planVersion};
  const result=await api('studio-compile',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request)});
  current.compiledReady=result.studioCompiledReady===true;
  current.compileError=result.studioCompileError||'';current.compileErrorCode=result.studioCompileErrorCode||'';current.compileErrorId=result.studioCompileErrorId||'';
  current.planTimings=result.studioTimings||null;
  if(current.compiledReady){
    current.prompts=result.studioPromptPreview||[];current.promptNote=result.studioPromptNote||'';
    current.planInputSignature=await F.inputFingerprint(current);current.phase='方案与提示词已完成';
    await message('本地编译已完成，没有调用AI策划，也未自动提交生图。点击“生成／同步未完成页”即可继续。');
  }else{current.phase='本地编译待修复';await message(current.compileError||'本地编译尚未完成，方案已保留。');}
}
async function poll(page){
  const j=current.jobs[page];if(!j?.id)throw Error('本页没有任务编号，请到原面板核对提交结果。');
  for(let i=0;i<180&&!paused;i++){
    let d;try{d=await api('ai-image-jobs/'+encodeURIComponent(j.id));}catch(e){j.state=F.classifyError(e);j.error=e.message;await save();render();return;}
    if(d.pending){j.state='生成中';j.message=d.message;await save();render();await sleep(4000);continue;}
    const m=d.materials?.[0]||d.material;const url=m?.previewUrl||m?.previewDataUrl||d.previewDataUrls?.[0]||d.previewDataUrl;
    j.state=url?'完成':d.suiteSummary?.failed?'失败':'待核对';j.url=url||'';j.message=d.message;
    j.actualPrompt=m?.prompt||'';await save();render();return;
  }
  j.state='待同步';j.message=paused?'后续步骤已暂停，后台图片任务继续运行。':'本轮等待结束，保留后台任务，点击同步取回结果。';await save();render();
}
async function syncSubmittedJobs(){
  const targets=Object.entries(current.jobs)
    .map(([page,j])=>({page:Number(page),state:j.state,id:j.id}))
    .filter(x=>x.id&&x.state!=='完成')
    .sort((a,b)=>a.page-b.page);
  if(!targets.length){status('当前没有可同步的进行中任务。');return;}
  current.phase='同步已提交任务';await save();render();
  for(const item of targets){
    if(paused)break;
    try{await poll(item.page);}catch(_){}
  }
  current.phase='等待处理';await save();render();
  const done=Object.values(current.jobs).filter(j=>j.state==='完成').length;
  const total=Object.keys(current.jobs).length;
  status(`同步完成：${done}/${total} 页已完成。`);
}
async function generate(pages){
  if(F.needsMarketRefresh(current))throw Error('请先点击“更新市场方案”，采用当前国家的线上导演方案后再生成；已有任务可继续同步。');
  if(!current.ready||!current.compiledReady)throw Error('请先完成线上方案和提示词编译。旧任务可先点击续写方案。');
  config=(await api('ai-image-config')).aiImage;
  if(!config?.model)throw Error('请在原面板配置生图模型。');
  current.phase='逐页生图';await save();
  for(const page of pages){
    if(paused)break;
    const previous=current.jobs[page];
    if(previous&&!['完成','失败','已取消'].includes(previous.state)){if(previous.id)await poll(page);else status(`第${page}页提交结果待核对，暂不重复提交。`);continue;}
    const p=current.pages.find(x=>Number(x.page)===Number(page));const f=form();
    // Keep the original source stable. This field carries only the user's page edit.
    if(p?.chatInstruction)f.set('suiteReviewInstruction',p.chatInstruction);
    const runId=previous?crypto.randomUUID().replace(/-/g,'').slice(0,12):current.id.replace(/-/g,'').slice(0,12);
    for(const [k,v]of Object.entries({mode:'edit',model:config.model,quality:'high',count:'1',lockLevel:'exact',generationProfile:'standard',suiteRunId:runId,suitePlan:JSON.stringify(current.pages),suitePageIndexes:JSON.stringify([Number(page)])}))f.set(k,v);
    current.jobs[page]={state:'提交中',runId,previous:previous?.url?{url:previous.url,id:previous.id}:undefined};
    await save();render();
    try{
      const d=await api('ad-launch-ai-image-edit',{method:'POST',body:f});
      if(!d.jobId)throw Error('提交返回缺少任务编号，请到原面板核对，暂不重复提交。');
      current.jobs[page]={...current.jobs[page],id:d.jobId,state:'排队中'};
      await save();await poll(page);
    }catch(e){
      current.jobs[page]={...current.jobs[page],state:isEngineUnavailable(e)?'待同步':'待核对',error:e.message};
      await save();render();
      if(!isEngineUnavailable(e)){break;}
      return;
    }
  }
  const done=Object.values(current.jobs).filter(j=>j.state==='完成').length;
  current.phase=done===current.count?'图片已完成':paused?'已暂停':'部分完成';
  await message(`本轮图片已返回 ${done}/${current.count} 张。${done===current.count?'可以逐张查看图片，或下载提示词。':'已提交的任务保留编号；待同步页先同步，明确失败页可重试。'}`);
}
async function run(fn){if(busy)return;busy=true;paused=false;current.activeOperationId=crypto.randomUUID().replaceAll('-','');current.cancelMessage='';render();status('处理中…');try{await fn();if(paused)status(current.cancelMessage||'后续步骤已暂停。');else status(current.compileError||'本轮处理结束。');}catch(e){current.phase=e.name==='AbortError'?'已停止后续处理':'等待处理';status(e.message);}finally{busy=false;await save().catch(()=>status('会话保存失败，请保持页面打开并检查浏览器存储。'));render();}}
async function cancelCurrentTask(){
  if(cancelSending||!current||!user)return;
  const target=current;paused=true;cancelSending=true;
  target.cancelMessage='正在通知后台取消，请等待确认。';await save(target);render();
  try{
    const jobIds=Object.values(target.jobs).filter(j=>j.id&&!['完成','失败','已取消'].includes(j.state)).map(j=>j.id);
    const result=await api('ai-image-cancel',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({operationId:target.activeOperationId,jobIds})});
    target.cancelMessage=result.message;target.cancelRequested=true;
    for(const j of Object.values(target.jobs)){if(jobIds.includes(j.id)){j.cancelRequested=true;j.state='待同步';}}
  }catch(e){target.cancelMessage='取消尚未确认：'+e.message+'。后台可能仍在运行，请再次点击取消。';}
  finally{cancelSending=false;await save(target);render();status(target.cancelMessage);}
}
async function submit(){
  const text=$('#input').value.trim();if(!text)throw Error('请输入产品需求或“开始生成”。');
  if(/^(开始生成|确认生成|生成图片|继续生成|继续|续写方案|继续策划|只补失败的图片)[。！!\s]*$/.test(text)&&current.pages.length){$('#input').value='';await message(text,'user');if(!current.ready||/策划|续写/.test(text))await plan();else await generate(F.remaining(current));return;}
  if(!current.files.length)throw Error('请先上传产品参考图。');
  const edit=text.match(/第\s*(\d+)\s*[张页图]/);
  if(edit&&current.pages.length){const p=current.pages.find(p=>Number(p.page)===Number(edit[1]));if(!p)throw Error('这个页码不在当前方案中。');$('#input').value='';p.chatInstruction=text;await message(text,'user');await message(`已记录第${edit[1]}页要求。点击该页重生成应用修改；其他页面保持不变。`);return;}
  if(current.pages.length)throw Error('修改整套需求请新建对话；修改某页请注明“第几张”。');
  const settings=F.infer(text,current);Object.assign(current,settings);
  if(/只(?:要|做|生成)?方案|先(?:看|出|给|做)(?:一下)?方案|确认后(?:再)?(?:开始)?生成/.test(text))current.autoGenerate=false;
  current.brief=text;if(!current.customTitle)current.title=text.slice(0,24);$('#input').value='';
  await message(text,'user');await message(`已收到 ${current.files.length} 张参考图。使用「${F.suite(current).label}」，按 ${current.country} 市场、${current.count} 页进行产品分析与逐页创作。${current.autoGenerate?'完整方案返回后自动生图。':'本次先展示方案，等待确认。'}`);
  await plan();
}
function exportPrompts(){const a=F.style(current.brief,current.director,current.pages),mode=F.suite(current);const output=[current.title,`创作模式：${mode.label} · ${current.count}张 · ${mode.size}`,'原始需求：',current.brief,'风格锚点：',JSON.stringify(a,null,2),...(current.prompts||[]).map(p=>`\n第${p.page}张\n${p.prompt}`)].join('\n');const u=URL.createObjectURL(new Blob([output],{type:'text/plain;charset=utf-8'}));const link=document.createElement('a');link.href=u;link.download=mode.label+'-方案与提示词.txt';link.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}
$('#loginForm').onsubmit=async e=>{e.preventDefault();try{await api('login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.fromEntries(new FormData(e.target)))});e.target.reset();await init();}catch(e){status(e.message);}};
$('#upload').onchange=async e=>{const files=[...e.target.files];if(current.files.length+files.length>8)return status('每个任务最多上传8张参考图。');if(files.some(f=>f.size>6*1024*1024))return status('单张参考图请控制在6MB以内。');current.files.push(...files);await save();render();e.target.value='';};
$('#new').onclick=()=>{if(!busy){fresh();save();}};
$('#suite').onchange=()=>switchSuite($('#suite').value).catch(e=>{status(e.message);render();});
$('#send').onclick=()=>run(submit);
$('#pause').onclick=()=>{paused=true;status('已请求暂停：等待当前请求返回并保存后停止，已提交图片仍在后台生成。');};
$('#cancelTask').onclick=cancelCurrentTask;
document.addEventListener('change',async e=>{if(busy||e.target.id==='suite'||e.target.closest('#historyDialog'))return;if(e.target.id==='country'&&!current.pages.length&&!F.suite(current).country)current.country=e.target.value;if(e.target.id==='count'&&!current.pages.length){try{current.count=F.validateSettings({...current,count:Number(e.target.value)}).count;}catch(error){status(error.message);render();return;}}if(e.target.id==='autoGenerate')current.autoGenerate=e.target.checked;if(e.target.dataset.edit){const p=current.pages.find(p=>String(p.page)===e.target.dataset.edit);p.chatInstruction=e.target.value;}await save();});
document.addEventListener('click',async e=>{
  const b=e.target.closest('button');if(!b)return;
  if(b.dataset.session&&!busy&&!cancelSending){current=sessions.find(s=>s.id===b.dataset.session);render();}
  if(b.id==='continuePlan')run(plan);
  if(b.id==='retryCompile')run(retryCompile);
  if(b.id==='replan'&&!busy&&confirm('重新调用AI策划会消耗导演额度。已有图片保留，新方案完成前暂缓重生成。继续吗？'))run(()=>plan(true));
  if(b.id==='generate')run(()=>generate(F.remaining(current)));
  if(b.dataset.sync)run(()=>poll(b.dataset.sync));
  if(b.dataset.retry)run(()=>generate([Number(b.dataset.retry)]));
  if(b.dataset.removeFile!==undefined&&!busy&&!current.pages.length){current.files.splice(Number(b.dataset.removeFile),1);await save();render();}
  if(b.id==='exportPrompts')exportPrompts();
  if(b.dataset.copy){const p=current.prompts?.find(p=>String(p.page)===b.dataset.copy);if(p)try{await navigator.clipboard.writeText(p.prompt);status('本页提示词已复制。');}catch{status('浏览器未允许剪贴板，请在展开的提示词中手动复制。');}}
  if(b.dataset.starter&&!busy){$('#input').value=b.dataset.starter;$('#input').focus();}
});
$('#searchHistory').addEventListener('input',filterHistory);
$('#fold').onclick=()=>document.body.classList.add('collapsed');$('#unfold').onclick=()=>document.body.classList.remove('collapsed');
if(matchMedia('(max-width:600px)').matches)document.body.classList.add('collapsed');
$('#creations').onclick=()=>{if(!Object.keys(current?.jobs||{}).length)$('#results').innerHTML='<div class="result-empty">当前对话还没有生成图片。</div>';$('#results').scrollIntoView({block:'start'});};
$('#promptLibrary').onclick=()=>{if(busy)return;$('.intro').style.display='block';$('.intro').scrollIntoView({block:'start'});status('选择提示词起点只填入输入框，不会提交。');};
$('#input').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();if(!$('#send').disabled)$('#send').click();}});
window.addEventListener('beforeunload',e=>{if(busy){e.preventDefault();e.returnValue='';}});
async function init(){
  try{
    db=db||await openDB();
    const auth=await api('session');
    user=auth.user;
    $('#login').hidden=!!user;
    $('#identity').textContent=user?`${user.username} · 本地已连接`:'请登录';
    sessions=await new Promise((resolve,reject)=>{const r=db.transaction('sessions').objectStore('sessions').getAll();r.onsuccess=()=>resolve(r.result.filter(s=>s.owner===user?.username));r.onerror=()=>reject(r.error);});
    current=sessions[0];
    if(!current)fresh();
    render();
    const needSync=Object.values(current?.jobs||{}).some(j=>j?.id&&j.state&&j.state!=='完成');
    if(needSync)run(syncSubmittedJobs);
  }catch(e){status(e.message);}
}
if(window.StudioHistory)historyUI=window.StudioHistory.create({getSession:id=>sessions.find(s=>s.id===id&&s.owner===user?.username),available:()=>!!user&&!busy,change:changeHistory,status});
init();
