// Isolated browser fixtures: no real account, AI request or persisted user data.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
  const browser=await chromium.launch({headless:true});
  try{
    const page=await browser.newPage({viewport:{width:1280,height:900}});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    let compilePosts=0;
    let cancelPosts=0;
    await page.route('**/api/sku-board/**',route=>{
      if(new URL(route.request().url()).pathname==='/api/sku-board/ai-image-cancel'){
        cancelPosts++;assert.equal(route.request().postDataJSON().operationId,'a'.repeat(32));
        return route.fulfill({json:{ok:true,cancelRequested:true,message:'取消已记录 fixture；上游可能仍在执行'}});
      }
      if(new URL(route.request().url()).pathname==='/api/sku-board/studio-compile'){
        compilePosts++;const request=route.request().postDataJSON();
        return route.fulfill({json:{ok:true,studioCompiledReady:true,
          studioPromptPreview:request.suitePages.map(p=>({page:p.page,prompt:'local compiler fixture'})),
          studioTimings:{compileOnly:true,upstreamMs:0,compileMs:5}}});
      }
      if(new URL(route.request().url()).pathname==='/api/sku-board/session')
        return route.fulfill({json:{ok:true,user:{username:'isolated-ui-test'}}});
      errors.push('Unexpected API request: '+route.request().url());return route.abort();
    });
    await page.goto('http://127.0.0.1:8795/');
    await page.waitForFunction(()=>!document.querySelector('#suite').disabled);
    assert.equal(await page.locator('#suite option').count(),3);
    assert.equal(await page.locator('#country option').count(),19);
    assert.equal(await page.locator('#count').inputValue(),'14');
    await page.selectOption('#suite','jp-landing-page-25');
    await page.waitForFunction(()=>document.querySelector('#count').value==='25');
    assert.equal(await page.locator('#country').inputValue(),'JP');
    assert.equal(await page.locator('#country').isDisabled(),true);
    assert.equal(await page.locator('#count').isDisabled(),true);
    assert.match(await page.locator('.settings > span').innerText(),/1500 × 2000/);
    await page.screenshot({path:process.env.STUDIO_SCREENSHOT||'test-suite-selector.png',fullPage:true});
    await page.selectOption('#suite','cod-country-detail-12');
    await page.waitForFunction(()=>document.querySelector('#count').value==='22');
    assert.equal(await page.locator('#country').isDisabled(),false);
    assert.equal(await page.locator('#count').isDisabled(),false);
    await page.locator('#count').fill('12');await page.locator('#count').blur();
    await page.selectOption('#country','US');
    await page.reload();
    await page.waitForFunction(()=>!document.querySelector('#suite').disabled);
    assert.equal(await page.locator('#suite').inputValue(),'cod-country-detail-12');
    assert.equal(await page.locator('#count').inputValue(),'12');
    assert.equal(await page.locator('#country').inputValue(),'US');
    for(const key of ['cod-country-detail-12','cod-country-landing-30']){
      await page.selectOption('#suite',key);
      for(const country of ['KR','JP','US','GB','DE','HU','PL','ES','MX','FR','CZ','TW','HK','TH','VN','MY','SG','PH','ID']){
        await page.selectOption('#country',country);
        assert.equal(await page.evaluate(()=>form().get('suiteCountry')),country);
      }
    }
    await page.reload();await page.waitForFunction(()=>!document.querySelector('#suite').disabled);
    assert.equal(await page.locator('#country').inputValue(),'ID');
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    await page.locator('#fold').click();
    await page.evaluate(()=>{
      current.pages=[{page:1,title:'测试缺页提示'}];current.ready=false;
      current.director={creativePassStats:{budgetExhausted:true,deferredPageNumbers:[2,3],
        requestErrors:[{pages:[2],message:'fixture HTTP 408 stream disconnected'}]}};
      render();
    });
    assert.match(await page.locator('#plan').innerText(),/这不是额度不足/);
    await page.getByText('查看实际请求与重试记录',{exact:true}).click();
    assert.match(await page.locator('#plan').innerText(),/fixture HTTP 408/);
    await page.evaluate(async()=>{
      const layers=Object.fromEntries(['taskAnchor','emotionAnchor','visualNarrative','layoutAndCopy','colorScheme','styleDirection','hardConstraints'].map(k=>[k,'complete fixture']));
      current.pages=Array.from({length:current.count},(_,i)=>({page:i+1,visualEnhancement:{companyPromptLayers:layers}}));
      current.prompts=current.pages.map(p=>({page:p.page,prompt:'compiled fixture'}));
      current.ready=true;current.compiledReady=true;current.autoGenerate=false;
      current.marketLockVersion=F.marketLockVersion;current.plannedCountry=current.country;
      current.director={source:'model',creativePassStats:{wallTimeMs:12000}};
      current.planTimings={upstreamMs:13000,compileMs:30,compileCacheHit:false};
      current.planInputSignature=await F.inputFingerprint(current);render();
    });
    assert.match(await page.locator('#plan').innerText(),/上次上游策划 13.0秒/);
    await page.locator('#continuePlan').click();
    await page.waitForFunction(()=>!document.querySelector('#send').disabled);
    assert.match(await page.locator('#plan').innerText(),/没有新增导演请求/);
    page.once('dialog',dialog=>dialog.dismiss());await page.locator('#replan').click();
    await page.evaluate(()=>{current.compiledReady=false;current.autoGenerate=true;current.compileError='dependency fixture';render();});
    await page.locator('#retryCompile').click();
    await page.waitForFunction(()=>!document.querySelector('#send').disabled);
    assert.equal(compilePosts,1);
    assert.match(await page.locator('#plan').innerText(),/本次仅本地编译，未调用AI/);
    assert.equal(await page.locator('#generate').isDisabled(),false);
    await page.evaluate(()=>{current.activeOperationId='a'.repeat(32);busy=true;render();});
    assert.equal(await page.locator('#cancelTask').isDisabled(),false);
    await page.locator('#cancelTask').click();
    await page.waitForFunction(()=>document.querySelector('#cancelStatus').textContent.includes('取消已记录'));
    assert.equal(cancelPosts,1);
    await page.evaluate(()=>{busy=false;});await page.reload();
    await page.waitForFunction(()=>!document.querySelector('#suite').disabled);
    assert.match(await page.locator('#cancelStatus').innerText(),/取消已记录/);
    assert.deepEqual(errors,[]);
    console.log('browser: three modes, JP locks, detail settings, reload persistence, mobile width and no paid API calls passed');
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
