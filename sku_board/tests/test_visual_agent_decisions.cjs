const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
// The panel always ships a renderer. The studio only carries one in the full
// developer layout, so exercise every copy that actually exists instead of
// assuming a sibling checkout directory.
const candidates=[
  path.join(__dirname,'../static/app.js'),
  path.join(__dirname,'../../cod-chat-studio/app.js'),
  path.join(__dirname,'../../../cod-chat-studio/app.js'),
];
const files=[];
for(const candidate of candidates){
  if(!fs.existsSync(candidate))continue;
  if(!fs.readFileSync(candidate,'utf8').includes('function renderAgentDecisionCards('))continue;
  if(!files.includes(candidate))files.push(candidate);
}
assert.ok(files.length,'no renderAgentDecisionCards implementation found');
for(const file of files){
  const source=fs.readFileSync(file,'utf8');
  const start=source.indexOf('function renderAgentDecisionCards(');
  const end=source.indexOf('\nfunction ',start+1);
  const context={esc:x=>String(x??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;')};
  vm.createContext(context);vm.runInContext(source.slice(start,end),context);
  assert.equal(context.renderAgentDecisionCards({},[]),'');
  const html=context.renderAgentDecisionCards({productIntelligence:{facts:[{statement:'<script>',status:'supplied'}]},strategy:{positioning:'test',purchaseReasons:[{reason:'reason'}]},failureAdvice:{actions:['check route']}},[{page:1,agentSpec:{purpose:'purpose',visualDesign:{method:'macro'},composition:'split'}}]);
  assert.ok(html.includes('营销决策'));assert.ok(html.includes('逐页分镜'));assert.ok(html.includes('微距'));
  assert.ok(html.includes('&lt;script&gt;'));assert.ok(!html.includes('<script>'));
  assert.ok(html.includes('check route'));
  const marketHtml=context.renderAgentDecisionCards({marketKnowledge:{evidence:[{platform:'test',observedAt:'2026-09-18',finding:'<unsafe>',source:'source'}],feedback:[],excluded:[{record:1,reason:'wrong market'}]},feedbackReview:{decision:'skipped',reason:'no data'},visualDNA:{id:'shared-id',palette:{palette:['#aabbcc']},typography:'readable',castingPolicy:'optional',photographicLanguage:'natural'}},[]);
  assert.ok(marketHtml.includes('市场资料'));assert.ok(marketHtml.includes('wrong market'));
  assert.ok(marketHtml.includes('shared-id'));assert.ok(marketHtml.includes('未触发额外调用'));
  assert.ok(!marketHtml.includes('<unsafe>'));
}
console.log('Decision-card renderers ('+files.length+' file(s)): empty state, structured decisions, storyboard, escaping passed');
