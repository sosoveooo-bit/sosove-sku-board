(function(root){
  const marketLockVersion='selected-market-v1-20260912';
  function needsMarketRefresh(state){return !!state.pages?.length&&suite(state).key!=='jp-landing-page-25'&&(state.marketLockVersion!==marketLockVersion||state.plannedCountry!==state.country);}
  const markets=Object.freeze([
    ['KR','韩国 / 韩文'],['JP','日本 / 日文'],['US','美国 / 英语'],['GB','英国 / 英语'],
    ['DE','德国 / 德语'],['HU','匈牙利 / 匈牙利语'],['PL','波兰 / 波兰语'],
    ['ES','西班牙 / 西班牙语'],['MX','墨西哥 / 西班牙语'],['FR','法国 / 法语'],
    ['CZ','捷克 / 捷克语'],['TW','台湾 / 繁体中文'],['HK','香港 / 香港繁体中文'],
    ['TH','泰国 / 泰文'],['VN','越南 / 越南文'],['MY','马来西亚 / 马来文'],
    ['SG','新加坡 / 英文'],['PH','菲律宾 / 英文'],['ID','印度尼西亚 / 印尼文'],
  ].map(([code,label])=>Object.freeze({code,label})));
  const suites=Object.freeze({
    'cod-country-landing-30':Object.freeze({key:'cod-country-landing-30',label:'COD 国家专区',count:14,size:'750x1000',min:8,max:30,hint:'8–30 张 · 按目标市场策划主图与落地页'}),
    'jp-landing-page-25':Object.freeze({key:'jp-landing-page-25',label:'日本产品落地页25图',count:25,size:'1500x2000',country:'JP',counts:[25],hint:'固定日本 / 日语 · 25 张 · 使用日本落地页导演流程'}),
    'cod-country-detail-12':Object.freeze({key:'cod-country-detail-12',label:'COD详情图',count:22,size:'750x1000',counts:[12,16,20,22],hint:'支持 12、16、20、22 张 · 使用独立详情页导演流程'}),
  });
  function suite(state={}){const mode=suites[state.suiteKey||'cod-country-landing-30'];if(!mode)throw Error('未知创作模式，请新建对话选择模式。');return mode;}
  function hasContent(state){return !!(state.brief||state.messages?.length||state.pages?.length||Object.keys(state.jobs||{}).length);}
  function validateSettings(state){
    const mode=suite(state),count=Number(state.count??mode.count),country=state.country||mode.country||'JP';
    if(!markets.some(m=>m.code===country))throw Error('请选择列表中的目标市场。');
    if(!Number.isInteger(count)||(mode.counts?!mode.counts.includes(count):(count<mode.min||count>mode.max))){
      throw Error(mode.counts?`${mode.label}支持 ${mode.counts.join('、')} 张，请调整页数。`:'当前 COD 引擎支持8–30页，请调整页数。');
    }
    if(mode.country&&country!==mode.country)throw Error('日本产品落地页25图固定面向日本 / 日语；其他市场请使用 COD 模式。');
    return {count,country};
  }
  function requestSettings(state){const mode=suite(state),settings=validateSettings(state);return {suiteKey:mode.key,suiteCount:settings.count,suiteCountry:settings.country,size:mode.size};}
  async function inputFingerprint(state){
    const hashes=await Promise.all((state.files||[]).map(async file=>{
      const digest=await crypto.subtle.digest('SHA-256',await file.arrayBuffer());
      return [file.name,file.type,Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join('')];
    }));
    const bytes=new TextEncoder().encode(JSON.stringify(['studio-input-v1',marketLockVersion,state.brief,requestSettings(state),hashes]));
    const digest=await crypto.subtle.digest('SHA-256',bytes);
    return Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join('');
  }
  function canReusePlan(state,signature){
    return state.ready===true&&state.compiledReady===true&&!needsMarketRefresh(state)&&
      state.planInputSignature===signature&&state.pages?.length===state.count&&readyCount(state.pages)===state.count&&
      state.prompts?.length===state.count&&new Set(state.prompts.map(p=>Number(p.page))).size===state.count&&
      state.pages.every(p=>state.prompts.some(x=>Number(x.page)===Number(p.page)));
  }
  const fields=['taskAnchor','emotionAnchor','visualNarrative','layoutAndCopy','colorScheme','styleDirection','hardConstraints'];
  function infer(text, defaults){
    const mode=suite(defaults);
    let count=Number(defaults.count)||mode.count, country=defaults.country||mode.country||'JP';
    const main=mode.key==='cod-country-landing-30'
      ? text.match(/(?:(?:主图|轮播图)\s*[:：]?\s*(\d+)\s*[张页]?|(\d+)\s*张\s*(?:主图|轮播图))/)
      : text.match(/主图\s*[:：]?\s*(\d+)\s*[张页]?/);
    const detail=mode.key==='cod-country-landing-30'
      ? text.match(/(?:详情(?:图|页)?\s*[:：]?\s*(\d+)\s*[张页]?|(\d+)\s*张\s*详情(?:图|页)?)/)
      : text.match(/详情(?:图|页)?\s*[:：]?\s*(\d+)\s*[张页]?/);
    const total=text.match(/(?:共|总计|总共|合计|一套|生成|制作)\s*(\d+)\s*[张页]/);
    if(main&&detail)count=Number(main[1]||main[2])+Number(detail[1]||detail[2]);else if(total)count=Number(total[1]);else if(main)count=Number(main[1]||main[2]);else if(detail)count=Number(detail[1]||detail[2]);
    // The visible selector owns the market; reference-country mentions are not commands.
    return validateSettings({...defaults,count,country});
  }
  function readyCount(pages){return (pages||[]).filter(p=>fields.every(f=>p.visualEnhancement?.companyPromptLayers?.[f])).length;}
  function style(brief,director,pages){
    const layers=(pages||[]).map(p=>p.visualEnhancement?.companyPromptLayers).find(l=>l?.colorScheme&&l?.styleDirection);
    const explicit=[...new Set((brief||'').match(/#[0-9a-fA-F]{6}\b/g)||[])];
    const colors=explicit.length?explicit:[...new Set((layers?.colorScheme||'').match(/#[0-9a-fA-F]{6}\b/g)||[])];
    return {colors,colorText:layers?.colorScheme||'等待 AI 返回整套配色',direction:layers?.styleDirection||'等待 AI 返回风格描述',
      source:layers?'来自线上逐页 AI Brief'+(explicit.length?'；色值优先使用用户原文':''):'等待线上风格信息',
      rule:'统一配色、字体调性和材质表现；每页独立构图。后续页面不附加第1张成图。',
      dna:director?.productVisualDNA||{}};
  }
  function canAutoGenerate(state){return state.autoGenerate===true&&state.ready===true&&state.compiledReady===true;}
  function remaining(state){return state.pages.map(p=>Number(p.page)).filter(p=>state.jobs[p]?.state!=='完成');}
  function classifyError(error){
    if(error?.payload?.cancelled)return '已取消';
    if(error?.payload?.code==='ENGINE_UNAVAILABLE'||/本地引擎连接中断/.test(error?.payload?.error||'')){
      return '待同步';
    }
    return error.payload?.status==='error'&&!error.payload?.outcomeUncertain?'失败':'待核对';
  }
  const api={inputFingerprint,canReusePlan,marketLockVersion,needsMarketRefresh,markets,suites,suite,hasContent,validateSettings,requestSettings,infer,readyCount,style,canAutoGenerate,remaining,classifyError};
  if(typeof module!=='undefined')module.exports=api;else root.StudioFlow=api;
})(typeof window!=='undefined'?window:globalThis);
