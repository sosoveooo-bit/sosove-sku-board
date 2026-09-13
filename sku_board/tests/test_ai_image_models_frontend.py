"""Image model defaults exercised in an isolated Node VM without network or storage I/O."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest


STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "Node.js is required for frontend model contract tests")
class AiImageModelsFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (STATIC_DIR / "app.js").read_text(encoding="utf-8-sig")

    def function(self, name):
        match = re.search(rf"(?m)^(?:async )?function {re.escape(name)}\(", self.source)
        self.assertIsNotNone(match, name)
        following = re.search(r"(?m)^(?:async )?function \w+\(", self.source[match.end():])
        end = match.end() + following.start() if following else len(self.source)
        return self.source[match.start():end]

    def constant(self, name):
        match = re.search(rf"(?m)^const {re.escape(name)} = ", self.source)
        self.assertIsNotNone(match, name)
        following = re.search(r"(?m)^const \w+ = ", self.source[match.end():])
        end = match.end() + following.start() if following else len(self.source)
        return self.source[match.start():end]

    def run_js(self, body, *, functions=(), setup="", constants=()):
        names = (
            "aiImageModelOptions", "aiImageDefaultModel", "aiImageConversationModelSelection",
            "aiImageConversationModelLocked", "applyAiImageModelDefaults", *functions,
        )
        source = "\n".join([
            *(self.constant(name) for name in (
                "AI_IMAGE_DEFAULT_MODEL", "AI_IMAGE_SUPPORTED_MODELS", "AI_IMAGE_MODEL_DEFAULTS_VERSION", *constants,
            )), *(self.function(name) for name in dict.fromkeys(names)),
        ])
        runner = """
const fs = require('fs'), vm = require('vm'), assert = require('assert/strict');
const fixture = JSON.parse(fs.readFileSync(0,'utf8'));
const context = vm.createContext({assert, console});
Promise.resolve(vm.runInContext(fixture.source + '\\n' + fixture.setup + '\\n(async()=>{\\n' + fixture.body + '\\n})()', context))
  .catch(error => { console.error(error.stack); process.exitCode=1; });
"""
        shared_setup = """
const state = {items: [], adLaunches:{options:{}}, aiImages:{model:'gpt-image-2', modelSelection:'default',conversations:[],activeId:''}};
function adLaunchOptions(){return state.adLaunches.options;}
function aiImageActiveConversation(){return state.aiImages.conversations.find(c=>c.id===state.aiImages.activeId)||null;}
let persisted=0;
"""
        if "persistAiImageState" not in functions:
            shared_setup += "function persistAiImageState(){persisted++;}\n"
        result = subprocess.run(
            [NODE, "-e", runner],
            input=json.dumps({"source": source, "setup": shared_setup + setup, "body": body}),
            capture_output=True, text=True, encoding="utf-8", timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_all_requested_and_existing_models_remain_selectable(self):
        self.run_js("""
const models=aiImageModelOptions({models:['gpt-image-2','custom-image','gpt-image-2'],model:'server-image'},'saved-image');
assert.equal(new Set(models).size,models.length);
for(const id of ['gpt-image-2','gpt-image-2.5','gpt-image-2.5-flare','gpt-image-2.5-sunburst','codex-gpt-image-2','auto','custom-image','server-image','saved-image']) assert.ok(models.includes(id),id);
assert.equal(models[0],'gpt-image-2');
assert.equal(models.some(model=>model.startsWith('acore/')),false);
const providerModels=aiImageModelOptions({models:['gpt-image-2','acore/gpt-image-2']});
assert.ok(providerModels.includes('acore/gpt-image-2'));
assert.equal(providerModels.includes('acore/nano-banana-2'),false);
assert.ok(aiImageModelOptions({models:['gpt-image-2']},'acore/nano-banana-2').includes('acore/nano-banana-2'));
assert.ok(aiImageModelOptions({models:['gpt-image-2'],model:'acore/nano-banana-pro'}).includes('acore/nano-banana-pro'));
assert.equal(aiImageModelOptions({models:null}).length,9);
assert.equal(aiImageModelOptions(null).length,9);
assert.equal(aiImageModelOptions({models:[]}).length,9);
""")

    def test_server_default_wins_over_builtin_and_partial_configuration_gets_full_list(self):
        self.run_js("""
assert.equal(aiImageDefaultModel(),'gpt-image-2.5-sunburst');
state.adLaunches.options.aiImage={model:'gpt-image-2.5-flare',models:['gpt-image-2'],enabled:false,nodeCount:7};
const options=aiImageOptions().aiImage;
assert.equal(options.model,'gpt-image-2.5-flare');
assert.equal(options.nodeCount,7);
assert.equal(options.enabled,false);
assert.ok(options.models.includes('gpt-image-2.5-sunburst'));
assert.equal(aiImageDefaultModel(),'gpt-image-2.5-flare');
""", functions=("aiImageOptions",), setup="const AI_IMAGE_SIZE_PRESETS=[{value:'1024x1024'}];")

    def test_legacy_default_drafts_migrate_once_and_explicit_old_choice_is_kept(self):
        self.run_js("""
const draft={id:'ai-1',status:'draft',model:'gpt-image-2',prompt:'original prompt',suitePages:[{prompt:'page'}]};
state.aiImages.conversations=[draft];state.aiImages.activeId=draft.id;
assert.equal(applyAiImageModelDefaults(),true);
assert.equal(draft.model,'gpt-image-2.5-sunburst');
assert.equal(draft.modelSelection,'default');
assert.equal(draft.modelDefaultsVersion,AI_IMAGE_MODEL_DEFAULTS_VERSION);
assert.equal(draft.prompt,'original prompt');assert.equal(draft.suitePages[0].prompt,'page');
assert.equal(applyAiImageModelDefaults(),false);assert.equal(persisted,1);
draft.model='gpt-image-2';draft.modelSelection='explicit';
assert.equal(applyAiImageModelDefaults(),false);assert.equal(draft.model,'gpt-image-2');
""")

    def test_history_and_inflight_models_and_metadata_are_unchanged(self):
        self.run_js("""
const conversations=[
 {status:'generating'}, {status:'planning'}, {status:'reviewing'}, {status:'done'}, {status:'partial'},
 {status:'error',materials:[{model:'gpt-image-2',id:'original'}]},
 {status:'cancelled',suiteRunId:'submitted-run'},
 {status:'draft',remoteSummary:{running:2}},
 {status:'error',remoteSummary:{pending:[{page:1}]}},
 {status:'draft',previewDataUrls:['data:image/png;base64,original']},
].map((c,i)=>({id:'ai-'+i,model:'gpt-image-2',...c}));
const original=JSON.stringify(conversations);
state.aiImages.conversations=conversations;state.aiImages.activeId='ai-0';
assert.equal(applyAiImageModelDefaults(),false);
assert.equal(JSON.stringify(conversations),original);assert.equal(persisted,0);
assert.equal(state.aiImages.model,'gpt-image-2');
assert.equal(state.aiImages.modelSelection,'default');
""")

    def test_legacy_nondefault_models_are_preserved_as_explicit_choices(self):
        self.run_js("""
const selected=['auto','codex-gpt-image-2','acore/nano-banana-2','gpt-image-2.5-flare','custom-provider'];
state.aiImages.conversations=selected.map((model,i)=>({id:'ai-'+i,model,status:'draft'}));
applyAiImageModelDefaults();
assert.deepEqual(state.aiImages.conversations.map(c=>c.model),selected);
assert.ok(state.aiImages.conversations.every(c=>c.modelSelection==='explicit'));
""")

    def test_new_task_uses_server_default_not_old_history_and_respects_explicit_choice(self):
        self.run_js("""
state.adLaunches.options.aiImage={model:'gpt-image-2.5-sunburst'};
state.aiImages.model='gpt-image-2';state.aiImages.modelSelection='default';
let c=createAiImageConversation();assert.equal(c.model,'gpt-image-2.5-sunburst');assert.equal(c.modelSelection,'default');
state.adLaunches.options.aiImage.model='gpt-image-2.5-flare';
c=createAiImageConversation();assert.equal(c.model,'gpt-image-2.5-flare');
state.aiImages.model='gpt-image-2';state.aiImages.modelSelection='explicit';
c=createAiImageConversation();assert.equal(c.model,'gpt-image-2');assert.equal(c.modelSelection,'explicit');
c=createAiImageConversation({model:'acore/gpt-image-2'});assert.equal(c.model,'acore/gpt-image-2');assert.equal(c.modelSelection,'explicit');
""", functions=("createAiImageConversation",), setup="""
function aiImageOptions(){return {aiImage:state.adLaunches.options.aiImage};}
function aiImageSkillConfig(){return {defaults:{}};}
function syncAiImageStateFromConversation(c){state.aiImages.model=c.model;state.aiImages.modelSelection=c.modelSelection;}
""")

    def test_restore_roundtrip_migrates_only_draft_and_preserves_material_models(self):
        self.run_js("""
const original={version:1,activeId:'ai-draft',conversations:[
 {id:'ai-draft',status:'draft',model:'gpt-image-2'},
 {id:'ai-completed',status:'done',model:'gpt-image-2',materials:[{id:'image',model:'gpt-image-2',providerModel:'gpt-image-2'}]},
 {id:'ai-explicit',status:'draft',model:'gpt-image-2',modelSelection:'explicit',modelDefaultsVersion:AI_IMAGE_MODEL_DEFAULTS_VERSION},
]};
saved=JSON.stringify(original);assert.equal(restoreAiImageState(),true);
applyAiImageModelDefaults();
const [draft,completed,explicit]=state.aiImages.conversations;
assert.equal(draft.model,'gpt-image-2.5-sunburst');
assert.equal(completed.model,'gpt-image-2');assert.equal(completed.materials[0].model,'gpt-image-2');assert.equal(completed.materials[0].providerModel,'gpt-image-2');
assert.equal(explicit.model,'gpt-image-2');
saved=JSON.stringify({...original,conversations:state.aiImages.conversations});
assert.equal(restoreAiImageState(),true);assert.equal(applyAiImageModelDefaults(),false);
assert.equal(state.aiImages.conversations[2].model,'gpt-image-2');
""", functions=("restoreAiImageState",), setup="""
const AI_IMAGE_STATE_STORAGE_KEY='fixture', AI_IMAGE_STATE_STORAGE_VERSION=1,AI_IMAGE_STATE_MAX_CONVERSATIONS=12;
const AI_IMAGE_GENERATION_PROFILES=[{key:'standard'}],AI_IMAGE_DIRECTOR_STAGES=[{key:'done'}];
let saved='null';const localStorage={getItem:()=>saved};
function aiImagePersistedMaterial(m){return {...m};}
function syncAiImageStateFromConversation(c){state.aiImages.model=c.model;state.aiImages.modelSelection=aiImageConversationModelSelection(c);}
""")

    def test_config_reload_follows_admin_default_without_overwriting_manual_model(self):
        self.run_js("""
const implicit={id:'ai-1',model:'gpt-image-2.5-sunburst',modelSelection:'default',status:'draft'};
const explicit={id:'ai-2',model:'gpt-image-2',modelSelection:'explicit',status:'draft'};
state.aiImages.conversations=[implicit,explicit];
state.adLaunches.options.aiImage={model:'gpt-image-2.5-flare'};
applyAiImageModelDefaults();
assert.equal(implicit.model,'gpt-image-2.5-flare');assert.equal(explicit.model,'gpt-image-2');
state.adLaunches.options.aiImage.model='gpt-image-2.5';
applyAiImageModelDefaults();assert.equal(implicit.model,'gpt-image-2.5');assert.equal(explicit.model,'gpt-image-2');
""")

    def test_real_compact_storage_and_restore_keep_explicit_old_model_after_refresh(self):
        self.run_js("""
const draft={id:'ai-draft',model:'gpt-image-2',status:'draft',referenceImages:[{name:'product.png',file:{size:10},role:'product'}]};
const completed={id:'ai-completed',model:'gpt-image-2',status:'done',materials:[
  {id:'AI-AABBCCDDEE',model:'gpt-image-2',providerModel:'gpt-image-2',previewDataUrl:'data:image/png;base64,fixture'}
]};
state.aiImages.conversations=[draft,completed];state.aiImages.activeId=draft.id;
assert.equal(applyAiImageModelDefaults(),true);
assert.equal(draft.model,'gpt-image-2.5-sunburst');
// This is the exact update payload used by the model select's change handler.
updateAiImageConversation({model:'gpt-image-2',modelSelection:'explicit',modelDefaultsVersion:AI_IMAGE_MODEL_DEFAULTS_VERSION});
const stored=JSON.parse(storage.get(AI_IMAGE_STATE_STORAGE_KEY));
assert.equal(stored.conversations[0].model,'gpt-image-2');
assert.equal(stored.conversations[0].modelSelection,'explicit');
assert.equal(stored.conversations[0].modelDefaultsVersion,AI_IMAGE_MODEL_DEFAULTS_VERSION);
assert.equal(stored.conversations[0].referenceImages.length,0);
assert.equal(stored.conversations[0].referenceMeta[0].name,'product.png');
assert.equal(stored.conversations[1].materials[0].previewDataUrl,'/api/sku-board/ai-image-output/AI-AABBCCDDEE');
state.aiImages.conversations=[];state.aiImages.activeId='';state.aiImages.model=AI_IMAGE_DEFAULT_MODEL;state.aiImages.modelSelection='default';
assert.equal(restoreAiImageState(),true);
assert.equal(state.aiImages.model,'gpt-image-2');assert.equal(state.aiImages.modelSelection,'explicit');
assert.equal(aiImageActiveConversation().modelDefaultsVersion,AI_IMAGE_MODEL_DEFAULTS_VERSION);
assert.equal(applyAiImageModelDefaults(),false);
state.adLaunches.options.aiImage={model:'gpt-image-2.5-flare'};
assert.equal(applyAiImageModelDefaults(),false);
assert.equal(aiImageActiveConversation().model,'gpt-image-2');
assert.equal(state.aiImages.conversations[1].model,'gpt-image-2');
assert.equal(state.aiImages.conversations[1].materials[0].model,'gpt-image-2');
assert.equal(state.aiImages.conversations[1].materials[0].providerModel,'gpt-image-2');
assert.ok(persisted>=3);
""", functions=(
            "aiImageStoredPreviewUrl", "aiImagePersistedMaterial", "aiImagePersistedConversation",
            "persistAiImageState", "restoreAiImageState", "syncAiImageStateFromConversation",
            "updateAiImageConversation", "ensureAiImageConversation",
        ), constants=(
            "AI_IMAGE_STATE_STORAGE_KEY", "AI_IMAGE_STATE_STORAGE_VERSION", "AI_IMAGE_STATE_MAX_CONVERSATIONS",
        ), setup="""
const AI_IMAGE_GENERATION_PROFILES=[{key:'standard'}],AI_IMAGE_DIRECTOR_STAGES=[{key:'done'}];
const storage=new Map(),localStorage={getItem:key=>storage.get(key)||null,setItem:(key,value)=>{storage.set(key,value);persisted++;}};
function aiImageDirectorMode(c){return c.directorMode||'fast';}
function aiImageGenerationProfile(c){return {key:c.generationProfile||'standard'};}
function aiImageConversationTitle(){return 'fixture';}
function renderAiImageForm(){}
function renderAiImageSidebar(){}
""")

    def test_ad_launch_tracks_server_default_until_user_selects_model(self):
        self.run_js("""
assert.equal(aiImageAdLaunchModel(),'gpt-image-2.5-sunburst');
state.adLaunches.options.aiImage={model:'gpt-image-2.5-flare'};
assert.equal(aiImageAdLaunchModel(),'gpt-image-2.5-flare');
select.dataset.modelSelection='explicit';select.value='gpt-image-2';
assert.equal(aiImageAdLaunchModel(),'gpt-image-2');
""", functions=("aiImageAdLaunchModel",), setup="const select={value:'gpt-image-2',dataset:{}};function $(){return select;}")

    def test_model_provider_routing_is_unchanged(self):
        self.run_js("""
for(const model of ['gpt-image-2','gpt-image-2.5','gpt-image-2.5-flare','gpt-image-2.5-sunburst'])assert.equal(aiImageModelProvider(model),'chatgpt2api');
assert.equal(aiImageModelProvider('acore/gpt-image-2'),'acore');
""", functions=("aiImageModelProvider",))

    def test_form_bindings_options_and_fallbacks_use_shared_defaults(self):
        self.assertIn('aiImageModelOptions(options.aiImage, currentModel)', self.function("renderAiImageForm"))
        self.assertIn('aiImageModelOptions(options.aiImage, currentAiModel)', self.function("renderAdLaunchForm"))
        self.assertIn('if (payload.aiImage) applyAiImageModelDefaults();', self.function("loadAiImageConfig"))
        self.assertIn('if (payload.options?.aiImage) applyAiImageModelDefaults();', self.function("updateAdLaunchPayload"))
        self.assertIn('model: event.target.value, modelSelection: "explicit"', self.source)
        self.assertNotIn('|| "gpt-image-2"', self.source)
        self.assertIn('/static/app.js?v=20260911-jp25-no-anchor-v1', (STATIC_DIR / "index.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
