const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm'), assert = require('node:assert/strict');
const source = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');
const html = fs.readFileSync(path.join(__dirname, '../static/index.html'), 'utf8');
const fields = new Map();
const element = (id) => {
  if (!fields.has(id)) fields.set(id, {value: '', checked: false, handlers: {},
    addEventListener(type, handler) { this.handlers[type] = handler; }, focus() { this.focused = true; }});
  return fields.get(id);
};
const initial = {model: 'gpt-5.6-sol', customModels: [], fallbackModels: ['gpt-5.6-terra'],
  baseUrl: 'https://fixture.invalid/v1', timeout: 120, configured: true, enabled: true, loaded: true, secureTransport: true};
let admin = true;
const toasts = [], requests = [];
const context = {
  state: {aiImages: {director: {...initial}}}, $: element, isAdmin: () => admin,
  esc: (value) => String(value ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;'),
  showToast: (message) => toasts.push(message), loadAiImageConfig: async () => {},
};
vm.createContext(context);
for (const name of ['AI_DIRECTOR_MODELS', 'AI_DIRECTOR_DEFAULT_FALLBACK_MODELS']) {
  const line = source.split('\n').find((line) => line.startsWith(`const ${name} = `));
  assert.ok(line); vm.runInContext(line, context);
}
for (const name of ['mergeAiDirectorState', 'aiDirectorModelOptions', 'renderAiDirectorModelOptions',
  'addAiDirectorCustomModel', 'bindAiDirectorCustomModelEvents', 'renderAiDirectorSettings',
  'aiDirectorSettingsFormPayload', 'saveAiDirectorSettings', 'loadAiDirectorSettings']) {
  const match = new RegExp(`^(?:async )?function ${name}\\(`, 'm').exec(source);
  assert.ok(match, name);
  const following = /\n(?:async )?function /.exec(source.slice(match.index + match[0].length));
  assert.ok(following, name);
  vm.runInContext(source.slice(match.index, match.index + match[0].length + following.index), context);
}
function selectInput(name) { element('#ai-director-custom-model').value = name; context.addAiDirectorCustomModel(); }
const plain = (value) => JSON.parse(JSON.stringify(value));

(async () => {
  context.renderAiDirectorSettings();
  assert.equal(element('#ai-director-model').value, 'gpt-5.6-sol');
  assert.ok(element('#ai-director-model').innerHTML.includes('deepseek-v4.1-flash'));
  selectInput('  Vendor/Exact-ID:latest  ');
  assert.equal(element('#ai-director-model').value, 'Vendor/Exact-ID:latest');
  assert.deepEqual(plain(context.state.aiImages.director.customModels), ['Vendor/Exact-ID:latest']);
  assert.deepEqual(plain(context.aiDirectorSettingsFormPayload().fallbackModels), ['gpt-5.6-terra']);
  assert.equal(requests.length, 0);
  selectInput('Vendor/Exact-ID:latest');
  assert.equal(context.state.aiImages.director.customModels.length, 1);
  selectInput('deepseek-v4.1-flash');
  assert.equal(context.state.aiImages.director.customModels.length, 1);
  selectInput('with space');
  assert.equal(element('#ai-director-model').value, 'deepseek-v4.1-flash');
  for (const name of ['a\nb', 'x'.repeat(121), 'bad\x00name', '']) selectInput(name);
  assert.equal(context.state.aiImages.director.model, 'deepseek-v4.1-flash');
  selectInput('vendor/"<model>');
  assert.ok(element('#ai-director-model').innerHTML.includes('vendor/&quot;&lt;model&gt;'));
  assert.ok(!element('#ai-director-model').innerHTML.includes('vendor/"<model>'));

  context.bindAiDirectorCustomModelEvents();
  element('#ai-director-custom-model').value = 'entered-model';
  let prevented = false;
  element('#ai-director-custom-model').handlers.keydown({key: 'Enter', preventDefault() {prevented = true;}});
  assert.equal(prevented, true);
  assert.equal(context.state.aiImages.director.model, 'entered-model');
  assert.equal(requests.length, 0);

  const draft = JSON.stringify(context.state.aiImages.director.customModels);
  context.api = async () => ({director: initial});
  await context.loadAiDirectorSettings(true);
  assert.equal(JSON.stringify(context.state.aiImages.director.customModels), draft);
  assert.equal(element('#ai-director-model').value, 'entered-model');
  element('#ai-director-base-url').value = 'https://draft.invalid/v1';
  context.renderAiDirectorSettings();
  assert.equal(element('#ai-director-base-url').value, 'https://draft.invalid/v1');

  context.api = async (url, options) => {
    requests.push({url, body: JSON.parse(options.body)});
    return {director: {...initial, ...requests.at(-1).body}};
  };
  await context.saveAiDirectorSettings(true);
  assert.equal(requests.length, 1);
  assert.equal(requests[0].url, '/api/sku-board/ai-director-settings');
  assert.equal(requests[0].body.model, 'entered-model');
  assert.deepEqual(requests[0].body.fallbackModels, ['gpt-5.6-terra']);
  assert.ok(requests[0].body.customModels.includes('Vendor/Exact-ID:latest'));
  assert.equal(context.state.aiImages.director.formDirty, false);
  context.renderAiDirectorSettings();
  assert.equal(element('#ai-director-model').value, 'entered-model');

  context.state.aiImages.director = {...initial, model: 'old-custom-primary'};
  context.renderAiDirectorSettings();
  assert.ok(element('#ai-director-model').innerHTML.includes('old-custom-primary'));
  selectInput('new-custom');
  assert.ok(context.state.aiImages.director.customModels.includes('old-custom-primary'));
  admin = false;
  const before = JSON.stringify(context.state.aiImages.director);
  selectInput('not-admin');
  assert.equal(JSON.stringify(context.state.aiImages.director), before);
  context.renderAiDirectorSettings();
  assert.equal(element('#ai-director-settings').hidden, true);
  admin = true;
  context.state.aiImages.director = {...initial, saving: true};
  selectInput('while-saving');
  assert.equal(context.state.aiImages.director.model, 'gpt-5.6-sol');
  context.renderAiDirectorSettings();
  assert.equal(element('#ai-director-add-model-btn').disabled, true);
  context.state.aiImages.director = {...initial, customModels: Array.from({length: 50}, (_, n) => `custom-${n}`)};
  selectInput('one-more');
  assert.equal(context.state.aiImages.director.model, 'gpt-5.6-sol');
  assert.ok(toasts.at(-1).includes('50'));
  assert.ok(html.includes('value="deepseek-v4.1-flash"'));
  assert.ok(html.includes('id="ai-director-add-model-btn" type="button"'));
  assert.equal((source.match(/  bindAiDirectorCustomModelEvents\(\);/g) || []).length, 1);
  console.log('Custom director UI: catalog, exact IDs, dedup, escaped options, Enter, save/reload, draft refresh, permissions, limit, no extra AI requests passed');
})().catch((error) => {console.error(error); process.exitCode = 1;});
