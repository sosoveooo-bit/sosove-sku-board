"use strict";
// Deterministic transport tests only: no model or image service is contacted.
const test = require("node:test");
const assert = require("node:assert/strict");
const {
  DEFAULT_FORM, normalizeForm, validateForm, contentSignature, totalCount,
  sortedPages, visiblePages, snapshotFresh, canUsePrompt, suiteComplete,
  fullPack, createController, safeImageUrl, actualDirectorModel, versionSelection, PAGE_DRAFTS_KEY, currentDrafts,
} = require("../static/cod-prompt-generator.js");

const copy = (value) => JSON.parse(JSON.stringify(value));
const tick = () => new Promise((resolve) => setImmediate(resolve));
function deferred() { let resolve, reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no; }); return { promise, resolve, reject }; }
function project(id = "A", product = "便携榨汁杯", extra = {}) {
  const form = normalizeForm({ product, main: 5, detail: 5, points: ["随行鲜榨", "USB充电"], ...extra.form });
  const pages = Array.from({ length: totalCount(form) }, (_, index) => ({ page: index + 1, section: index < form.main ? "main" : "detail", localIndex: index < form.main ? index + 1 : index + 1 - form.main, title: `${product}-${index + 1}`, focus: `${product}当前卖点`, headline: `見出し${index + 1}`, modelPrompt: `RAW ${product} #${index + 1}`, executionPrompt: `EXACT\n${product} #${index + 1}\ncustom palette\n提供的真实促销` }));
  return { id, name: product, revision: 1, currentRevision: 1, status: "complete", form, references: [{ index: 1, name: "product.png", role: "product", sha256: `${id}-digest`, previewUrl: "/fixture.png" }], versions: [{ revision: 1, status: "complete" }], masterPrompt: `MASTER ${product}`, sharedExecutionRequirements: `SHARED ${form.size}\nStatic images and same-SKU references`, outline: pages.map(({ modelPrompt, executionPrompt, ...page }) => page), suitePages: pages, hooks: [{ source: "随行鲜榨", variants: [{ type: "pain", text: "朝の手間が気になる？" }, { type: "effect", text: "毎日の一杯を手軽に" }, { type: "scene", text: "仕事の合間のリフレッシュに" }] }], director: { model: "mock-director", source: "model" }, fingerprint: `${id}-fingerprint`, materials: [], ...extra, form };
}
function harness(initial = project(), override = null, draftStorage = null) {
  const records = [], notices = [], timers = new Map(), docs = new Map([[initial.id, copy(initial)]]), queues = new Map();
  let timerId = 0;
  const request = async (path, options = {}) => {
    records.push({ path, ...options });
    if (override) { const result = override(path, options, docs); if (result !== undefined) return result; }
    if (path.endsWith("/projects")) return { ok: true, projects: [...docs.values()].map(({ id, name, revision, status }) => ({ id, name, revision, status })) };
    if (path.endsWith("/projects/upload")) {
      const form = JSON.parse(options.body.get("form")), id = options.body.get("projectId") || `new-${docs.size}`;
      const old = docs.get(id), revision = old ? old.revision + 1 : 1;
      const next = project(id, form.product, { form, revision, currentRevision: revision, status: "draft", suitePages: [], outline: [], masterPrompt: "", hooks: [] });
      if (options.body.get("referencesMode") === "replace") next.references = [];
      docs.set(id, next); return { ok: true, project: copy(next) };
    }
    const match = path.match(/\/projects\/([^/?]+)(?:\/([^?]+))?/), id = match?.[1], action = match?.[2];
    if (!id || !docs.has(id)) throw new Error("project missing");
    const old = docs.get(id);
    if (action === "generate") {
      const revision = options.json.mode === "resume" ? old.revision : old.revision + 1;
      const next = project(id, old.form.product, { form: old.form, revision, currentRevision: revision });
      docs.set(id, next); return { ok: true, project: copy(next) };
    }
    if (action === "cancel") { const next = { ...old, status: old.status === "complete" ? "complete" : "cancelled" }; docs.set(id, next); return { ok: true, project: copy(next) }; }
    if (action === "edit-page") {
      const next = copy(old); next.revision += 1; next.currentRevision = next.revision;
      const page = next.suitePages.find((page) => page.page === options.json.pageNumber);
      page.modelPrompt = options.json.modelPrompt; page.executionPrompt = `COMPILED\n${options.json.modelPrompt}`;
      docs.set(id, next); return { ok: true, project: copy(next) };
    }
    if (action === "render-queues") return { ok: true, queues: [...queues.values()].filter((queue) => queue.projectId === id && queue.revision === Number(path.match(/revision=(\d+)/)?.[1])) };
    if (action === "render-queue") {
      const { revision, mode, pageNumbers, ...settings } = options.json;
      const previous = [...queues.values()].find((queue) => queue.projectId === id && queue.revision === revision && JSON.stringify(queue.settings) === JSON.stringify(settings) && JSON.stringify(queue.pages.map((page) => page.page)) === JSON.stringify(pageNumbers));
      if (previous && (mode === "resume" || ["running", "queued"].includes(previous.status))) return { ok: true, queue: copy(previous) };
      const queue = { id: `queue-${queues.size + 1}`, projectId: id, revision, settings, status: "complete", pages: pageNumbers.map((page) => ({ page, status: "complete", jobId: `img-${page}` })), completed: pageNumbers.length, total: pageNumbers.length };
      old.materials.push(...pageNumbers.map((page) => ({ id: `img-${page}`, page, previewUrl: "/image.png", originRevision: revision })));
      queues.set(queue.id, queue); return { ok: true, queue: copy(queue) };
    }
    if (action?.startsWith("render-queues/")) {
      const [, queueId, operation] = action.split("/"), queue = queues.get(queueId);
      queue.status = operation === "cancel" ? "paused" : "running"; return { ok: true, queue: copy(queue) };
    }
    if (action === "review") { const next = { ...old, qualityReport: { source: options.json.mode, status: "warning", summary: "检查建议", issues: [{ page: 1, code: "repeat", severity: "warning", message: "重复钩子" }], repairablePages: [1] } }; docs.set(id, next); return { ok: true, project: copy(next) }; }
    if (action === "render") return { ok: true, projectId: id, revision: old.revision, materials: [{ id: `img-${options.json.pageNumber}`, page: options.json.pageNumber, previewUrl: "/image.png" }] };
    return { ok: true, project: copy(old) };
  };
  const app = createController({ request, notify: (message) => notices.push(message), initialForm: initial.form, draftStorage, schedule: (fn) => { timers.set(++timerId, fn); return timerId; }, unschedule: (id) => timers.delete(id) });
  return { app, records, notices, timers, docs, queues };
}

test("new form is blank and exact counts never jump from 5+5 to37", () => {
  assert.equal(DEFAULT_FORM.product, ""); assert.deepEqual(DEFAULT_FORM.points, []);
  const form = normalizeForm({ product: "烤虾", points: "整只大虾", main: 5, detail: 5 });
  assert.equal(totalCount(validateForm(form)), 10);
  assert.throws(() => validateForm({ ...form, main: 5.5 }), /整数/);
  assert.throws(() => validateForm({ ...form, detail: 41 }), /整数/);
});
test("render preferences are not product-content identity", () => {
  const form = project().form;
  assert.equal(contentSignature(form), contentSignature({ ...form, model: "different-image", quality: "medium", generationProfile: "fast" }));
  assert.notEqual(contentSignature(form), contentSignature({ ...form, style: "pink" }));
});
test("5+5 is sent as raw form and compact export has ten creative prompts", async () => {
  const { app, records } = harness();
  app.updateForm(normalizeForm({ product: "冷冻香辣烤虾", points: ["整只大虾"], main: 5, detail: 5, market: "DE" }));
  await app.generate();
  const saved = JSON.parse(records.find((record) => record.path.endsWith("/upload")).body.get("form"));
  assert.equal(saved.main, 5); assert.equal(saved.detail, 5); assert.equal(saved.market, "DE");
  assert.equal(sortedPages(app.state.project).length, 10); assert.ok(suiteComplete(app.state));
  const pack = fullPack(app.state);
  assert.equal((pack.match(/RAW /g) || []).length, 10); assert.ok(pack.startsWith("MASTER 冷冻香辣烤虾"));
  for (const page of app.state.project.suitePages) assert.ok(pack.includes(page.modelPrompt));
});
test("late A generation cannot overwrite new B; returned A revision is cancelled", async () => {
  const gate = deferred();
  const { app, records } = harness(project(), (path) => path.endsWith("/generate") ? gate.promise : undefined);
  await app.openProject("A"); const generating = app.generate(); await tick();
  app.updateForm({ ...app.state.form, product: "冷冻香辣烤虾", points: ["整只大虾"] });
  gate.resolve({ ok: true, project: project("A", "便携榨汁杯", { revision: 2, status: "generating" }) }); await generating; await tick();
  assert.equal(app.state.form.product, "冷冻香辣烤虾"); assert.equal(app.state.project, null);
  assert.ok(records.some((record) => record.path.endsWith("/A/cancel") && record.json.revision === 2));
});
test("same-name same-size replacement reference invalidates late old result", async () => {
  const gate = deferred();
  const { app } = harness(project(), (path) => path.endsWith("/generate") ? gate.promise : undefined);
  await app.openProject("A"); const generating = app.generate(); await tick();
  const file = new Blob(["new bytes"], { type: "image/png" }); Object.defineProperty(file, "name", { value: "product.png" });
  app.setReferences([file]); gate.resolve({ ok: true, project: project("A", "old output", { revision: 2 }) }); await generating;
  assert.equal(app.state.project.revision, 1); assert.equal(app.state.dirty, true);
  assert.equal(app.references()[0].file, file); assert.equal(canUsePrompt(app.state), false);
});
test("late A open cannot replace B already opened", async () => {
  const gate = deferred(), { app, docs } = harness(project(), (path) => path.endsWith("/projects/A") ? gate.promise : undefined);
  docs.set("B", project("B", "冷冻香辣烤虾")); const opening = app.openProject("A"); await app.openProject("B");
  gate.resolve({ ok: true, project: project() }); await opening;
  assert.equal(app.state.project.id, "B"); assert.equal(app.state.form.product, "冷冻香辣烤虾");
});
test("AI transport failure is visible and never creates template master/pages/hooks", async () => {
  const { app, notices } = harness(project(), (path) => { if (path.endsWith("/generate")) throw new Error("model unavailable"); });
  app.newProduct(); app.updateForm({ ...app.state.form, product: "新品", points: ["新卖点"] }); await app.generate();
  assert.match(app.state.error, /model unavailable/); assert.equal(app.state.project.masterPrompt, "");
  assert.deepEqual(app.state.project.suitePages, []); assert.deepEqual(app.state.project.hooks, []);
  assert.equal(canUsePrompt(app.state), false); assert.ok(notices.some((message) => /model unavailable/.test(message)));
});
test("server failed status stays failed, completed partial pages are preserved", async () => {
  const failed = project("A", "便携榨汁杯", { status: "partial", error: "batch3 failed" }); failed.suitePages = failed.suitePages.slice(0, 5);
  const { app } = harness(failed); await app.openProject("A");
  assert.equal(app.state.project.status, "partial"); assert.equal(app.state.project.error, "batch3 failed");
  assert.equal(app.state.project.suitePages.length, 5); assert.equal(suiteComplete(app.state), false);
  assert.equal(canUsePrompt(app.state, sortedPages(app.state.project)[0]), true);
});
test("changing render options preserves all prompts, refs and material history", async () => {
  const original = project(); original.materials = [{ id: "img1", page: 1, previewUrl: "/one.png" }];
  const { app } = harness(original); await app.openProject("A");
  const prior = app.state.project, token = app.state.token;
  app.updateForm({ ...app.state.form, quality: "medium", model: "another-render-model", generationProfile: "fast" });
  assert.equal(app.state.project, prior); assert.equal(app.state.token, token); assert.equal(app.state.dirty, false);
  assert.equal(app.state.project.materials.length, 1); assert.ok(suiteComplete(app.state));
});
test("filters select correct global pages and are preserved through input render updates", async () => {
  const { app } = harness(); await app.openProject("A"); app.setFilter("detail");
  assert.deepEqual(visiblePages(app.state.project, app.state.filter).map((page) => page.page), [6, 7, 8, 9, 10]);
  app.updateForm({ ...app.state.form, quality: "medium" }); assert.equal(app.state.filter, "detail");
});
test("any content edit blocks master, page, suite copy and render", async () => {
  const { app, records } = harness(); await app.openProject("A"); app.updateForm({ ...app.state.form, discount: "真实折扣" });
  assert.equal(snapshotFresh(app.state), false); assert.equal(canUsePrompt(app.state, sortedPages(app.state.project)[0]), false);
  assert.throws(() => fullPack(app.state), /尚未完成|修改/); await app.renderImages("current");
  assert.equal(records.filter((record) => record.path.endsWith("/render-queue")).length, 0);
});
test("rename archived product clears untouched old points/offers, preserves explicit new points", async () => {
  const old = project("A", "旧商品", { form: { points: ["旧卖点"], discount: "OLD", avoid: "旧品限制" } });
  const { app } = harness(old); await app.openProject("A"); app.updateForm({ ...app.state.form, product: "新品" });
  assert.deepEqual(app.state.form.points, []); assert.equal(app.state.form.discount, ""); assert.equal(app.state.form.avoid, ""); assert.equal(app.references().length, 0);
  await app.openProject("A"); app.updateForm({ ...app.state.form, product: "新品", points: ["新品卖点"], discount: "NEW" });
  assert.deepEqual(app.state.form.points, ["新品卖点"]); assert.equal(app.state.form.discount, "NEW");
});
test("failed project open restores all unsaved draft including local file", async () => {
  const { app } = harness(); await app.openProject("A"); app.updateForm({ ...app.state.form, points: ["手动输入未保存"] });
  const file = new Blob(["file"], { type: "image/png" }); Object.defineProperty(file, "name", { value: "new.png" }); app.setReferences([file]);
  await app.openProject("missing"); assert.equal(app.state.form.product, "便携榨汁杯");
  assert.deepEqual(app.state.form.points, ["手动输入未保存"]); assert.equal(app.references()[0].file, file); assert.equal(app.state.dirty, true);
});
test("failed manual page save preserves user's edit for retry", async () => {
  const { app } = harness(project(), (path) => { if (path.endsWith("/edit-page")) throw new Error("save failed"); });
  await app.openProject("A"); app.state.pageEditorKey = "A:1:1"; app.setPageEditor("new manual prompt"); await app.savePage("new manual prompt");
  assert.equal(app.state.pageEditorValue, "new manual prompt"); assert.equal(app.state.pageEditorDirty, true); assert.equal(app.state.project.revision, 1);
});
test("saved manual page uses exactly server compiled execution prompt", async () => {
  const { app } = harness(); await app.openProject("A"); await app.savePage("User verbatim\nピンク背景");
  assert.equal(app.state.project.revision, 2); assert.equal(app.state.project.suitePages[0].modelPrompt, "User verbatim\nピンク背景");
  assert.ok(fullPack(app.state, "standalone").includes("COMPILED\nUser verbatim\nピンク背景"));
});
test("render uses identity+settings only, never compiles/rewrites prompt in browser", async () => {
  const { app, records } = harness(); await app.openProject("A"); app.selectPage(6); app.updateForm({ ...app.state.form, quality: "medium", generationProfile: "fast" }); await app.renderImages("current"); await tick();
  const render = records.find((record) => record.path.endsWith("/render-queue"));
  assert.deepEqual(render.json, { revision: 1, mode: "resume", pageNumbers: [6], model: "gpt-image-2", quality: "medium", generationProfile: "fast" });
  assert.equal(app.state.project.materials[0].page, 6); assert.equal(app.state.rendering.completed, 1);
});
test("stop sends server cancellation and preserves partial pages", async () => {
  const partial = project("A", "便携榨汁杯", { status: "generating" }); partial.suitePages = partial.suitePages.slice(0, 3);
  const { app, records, timers } = harness(partial); await app.openProject("A"); assert.equal(timers.size, 1); await app.stop();
  assert.equal(app.state.project.status, "cancelled"); assert.equal(app.state.project.suitePages.length, 3); assert.equal(timers.size, 0);
  assert.ok(records.some((record) => record.path.endsWith("/cancel") && record.json.revision === 1));
});
test("late image after switch never appears under B", async () => {
  const gate = deferred(), { app, docs } = harness(project(), (path) => path.endsWith("/render-queue") ? gate.promise : undefined);
  docs.set("B", project("B", "烤虾")); await app.openProject("A"); const rendering = app.renderImages("suite"); await tick(); await app.openProject("B");
  gate.resolve({ ok: true, queue: { id: "late", projectId: "A", revision: 1, status: "running", pages: [{ page: 1, status: "running" }] } }); await rendering;
  assert.equal(app.state.project.id, "B"); assert.equal(app.state.project.materials.length, 0);
});
test("historical versions can export but cannot overwrite current history", async () => {
  const historical = project("A", "旧版", { revision: 1, currentRevision: 4 }); const { app, records } = harness(historical); await app.openProject("A", 1);
  assert.equal(app.state.historical, true); assert.ok(fullPack(app.state).includes("旧版")); await app.generate("fresh"); await app.savePage("changed");
  assert.equal(records.filter((record) => /\/(generate|edit-page)$/.test(record.path)).length, 0);
});
test("reference bindings stay 1-based and role changes force regeneration", async () => {
  const { app, records } = harness(); await app.openProject("A"); app.setReferenceRole(0, "detail"); await app.saveProject();
  const upload = records.find((record) => record.path.endsWith("/upload"));
  assert.equal(upload.body.get("referencesMode"), "keep"); assert.deepEqual(JSON.parse(upload.body.get("referenceBindings")), [{ index: 1, role: "detail" }]);
});
test("preview URLs reject script schemes without stripping valid authenticated paths", () => {
  assert.equal(safeImageUrl("javascript:alert(1)"), ""); assert.equal(safeImageUrl("//evil.test/image.png"), "");
  assert.equal(safeImageUrl("/api/project/ref/1"), "/api/project/ref/1");
});
test("single-page rewrite keeps selected P6 while its output is temporarily absent", async () => {
  const pending = project("A", "便携榨汁杯", { revision: 2, currentRevision: 2, status: "generating" });
  pending.suitePages = pending.suitePages.filter((page) => page.page !== 6);
  const { app } = harness(project(), (path) => path.endsWith("/generate") ? { ok: true, project: pending } : undefined);
  await app.openProject("A"); app.selectPage(6); await app.generate("page", "重写第六页");
  assert.equal(app.state.selectedPage, 6);
  assert.equal(sortedPages(app.state.project).find((page) => page.page === 6).executionPrompt, undefined);
  assert.equal(sortedPages(app.state.project).length, 10);
});
test("version selection follows newly accepted revisions, retaining browsing choice only for same revision", () => {
  assert.equal(versionSelection({ id: "A", revision: 2 }, "A", 1, "1"), "2");
  assert.equal(versionSelection({ id: "A", revision: 2 }, "A", 2, "1"), "1");
  assert.equal(versionSelection({ id: "B", revision: 4 }, "A", 2, "1"), "4");
});
test("model display distinguishes successful fallback from requested-but-unreturned model", () => {
  assert.equal(actualDirectorModel({ model: "requested-model", activeModel: "fallback-model", status: "ok" }), "fallback-model");
  assert.equal(actualDirectorModel({ model: "requested-model", status: "running" }), "");
  assert.equal(actualDirectorModel({ model: "requested-model", activeModel: "", status: "error" }), "");
});
test("stopping an old version after edits preserves new unsaved form and references", async () => {
  const { app } = harness(project("A", "便携榨汁杯", { status: "generating" }));
  await app.openProject("A"); app.updateForm({ ...app.state.form, points: ["当前新卖点"] });
  const file = new Blob(["new bytes"], { type: "image/png" }); Object.defineProperty(file, "name", { value: "current.png" });
  app.setReferences([file]); await app.stop();
  assert.equal(app.state.dirty, true); assert.deepEqual(app.state.form.points, ["当前新卖点"]);
  assert.equal(app.references()[0].file, file); assert.equal(canUsePrompt(app.state), false);
});
test("save-product cannot silently discard unsaved single-page editor text", async () => {
  const { app, records } = harness(); await app.openProject("A"); app.state.pageEditorKey = "A:1:1"; app.setPageEditor("unfinished manual text");
  await app.saveProject(); assert.equal(app.state.pageEditorValue, "unfinished manual text"); assert.equal(app.state.pageEditorDirty, true);
  assert.equal(records.filter((record) => record.path.endsWith("/upload")).length, 0);
});

function memoryStorage() { const data = new Map(); return { getItem: (key) => data.get(key) || null, setItem: (key, value) => data.set(key, value), data }; }
test("switching pages preserves distinct local drafts and restores unsaved state", async () => {
  const store = memoryStorage(), { app } = harness(project(), null, store); await app.openProject("A");
  app.setPageEditor("第1页未保存\n日文や韓文"); app.selectPage(2); app.setPageEditor("第2页未保存"); app.selectPage(1);
  assert.equal(app.state.pageEditorValue, "第1页未保存\n日文や韓文"); assert.equal(app.state.pageEditorDirty, true); assert.equal(app.state.pageEditorSource, "restored");
  app.selectPage(2); assert.equal(app.state.pageEditorValue, "第2页未保存");
  assert.equal(currentDrafts(app.state).length, 2); assert.equal(Object.keys(JSON.parse(store.getItem(PAGE_DRAFTS_KEY))).length, 2);
});
test("page drafts survive new product, reopen and a fresh controller (reload)", async () => {
  const store = memoryStorage(), { app, docs } = harness(project(), null, store); docs.set("B", project("B", "烤虾"));
  await app.openProject("A"); app.setPageEditor("A第1页草稿"); await app.openProject("B"); app.setPageEditor("B第1页草稿"); app.newProduct(); await app.openProject("A");
  assert.equal(app.state.pageEditorValue, "A第1页草稿");
  const reloaded = harness(project(), null, store); await reloaded.app.openProject("A");
  assert.equal(reloaded.app.state.pageEditorValue, "A第1页草稿"); assert.equal(reloaded.app.state.pageEditorDirty, true);
  assert.equal(Object.keys(JSON.parse(store.getItem(PAGE_DRAFTS_KEY))).length, 2);
});
test("drafts are isolated by revision and never silently copied onto a new revision", async () => {
  const store = memoryStorage(), { app, docs } = harness(project(), null, store); await app.openProject("A"); app.selectPage(2); app.setPageEditor("v1的P2草稿");
  app.selectPage(1); app.setPageEditor("保存P1"); await app.savePage("保存P1"); app.selectPage(2);
  assert.equal(app.state.project.revision, 2); assert.equal(app.state.pageEditorDirty, false); assert.notEqual(app.state.pageEditorValue, "v1的P2草稿");
  docs.set("A", project("A", "便携榨汁杯", { currentRevision: 2 })); await app.openProject("A", 1);
  assert.equal(app.state.pageEditorValue, "v1的P2草稿"); assert.equal(app.state.historical, true);
});
test("explicit discard clears only selected draft and restores saved source", async () => {
  const store = memoryStorage(), { app } = harness(project(), null, store); await app.openProject("A"); app.setPageEditor("P1改动"); app.selectPage(2); app.setPageEditor("P2改动"); app.selectPage(1); app.discardPageDraft();
  assert.equal(app.state.pageEditorDirty, false); assert.equal(app.state.pageEditorValue, app.state.project.suitePages[0].modelPrompt); assert.equal(currentDrafts(app.state).length, 1);
  app.selectPage(2); assert.equal(app.state.pageEditorValue, "P2改动");
});
test("localStorage quota failure retains in-memory text and produces explicit warning", async () => {
  const store = { getItem: () => null, setItem: () => { throw new Error("quota"); } }, { app } = harness(project(), null, store);
  await app.openProject("A"); app.setPageEditor("不能丢失的内容"); app.selectPage(2); app.selectPage(1);
  assert.equal(app.state.pageEditorValue, "不能丢失的内容"); assert.match(app.state.draftError, /存储失败/);
});
test("draft on another page blocks whole export but not saved single-page execution", async () => {
  const { app } = harness(); await app.openProject("A"); app.setPageEditor("P1草稿"); app.selectPage(2);
  assert.equal(canUsePrompt(app.state, sortedPages(app.state.project)[1]), true); assert.equal(suiteComplete(app.state), false); assert.throws(() => fullPack(app.state));
});
test("compact export has master and shared hard requirements exactly once", async () => {
  const source = project(); source.suitePages.forEach((page) => { page.executionPrompt = `${source.masterPrompt}\n${source.sharedExecutionRequirements}\n${page.modelPrompt}`; });
  const { app } = harness(source); await app.openProject("A");
  const compact = fullPack(app.state), independent = fullPack(app.state, "standalone");
  assert.equal(compact.split(source.masterPrompt).length - 1, 1); assert.equal(compact.split(source.sharedExecutionRequirements).length - 1, 1);
  assert.equal(independent.split(source.masterPrompt).length - 1, 10); assert.equal(independent.split(source.sharedExecutionRequirements).length - 1, 10);
  source.suitePages.forEach((page) => assert.ok(independent.includes(page.executionPrompt)));
});
test("old snapshots without shared requirements stay available in exact standalone export", async () => {
  const { app } = harness(project("A", "历史品", { sharedExecutionRequirements: "" })); await app.openProject("A");
  assert.throws(() => fullPack(app.state), /逐张独立版/); assert.ok(fullPack(app.state, "standalone").includes(app.state.project.suitePages[0].executionPrompt));
});
test("background queue submissions use one request, not browser per-page loops", async () => {
  const { app, records } = harness(); await app.openProject("A"); await app.renderImages("suite"); await tick();
  assert.equal(records.filter((record) => record.path.endsWith("/render-queue")).length, 1);
  assert.equal(records.filter((record) => record.path.endsWith("/render")).length, 0); assert.equal(app.state.rendering.total, 10);
});
test("double submit in-flight is deduped locally and repeat resume reuses completed run", async () => {
  const gate = deferred(), base = harness(project(), (path) => path.endsWith("/render-queue") ? gate.promise : undefined);
  await base.app.openProject("A"); const first = base.app.renderImages("current"); await base.app.renderImages("current");
  assert.equal(base.records.filter((record) => record.path.endsWith("/render-queue")).length, 1);
  gate.resolve({ ok: true, queue: { id: "saved", projectId: "A", revision: 1, status: "running", pages: [{ page: 1, status: "running" }] } }); await first;
  const { app, queues, docs } = harness(); await app.openProject("A"); await app.renderImages("suite"); await tick(); const count = docs.get("A").materials.length;
  await app.renderImages("suite"); await tick(); assert.equal(queues.size, 1); assert.equal(docs.get("A").materials.length, count);
});
test("switching products does not cancel durable image runs; reopening observes queue", async () => {
  const { app, docs, queues, records } = harness(); docs.set("B", project("B", "烤虾")); await app.openProject("A");
  queues.set("active", { id: "active", projectId: "A", revision: 1, status: "running", pages: [{ page: 1, status: "running" }], completed: 0, total: 1 }); await app.refreshQueues();
  assert.equal(app.state.rendering.running, true); await app.openProject("B"); await tick(); assert.equal(app.state.rendering, null);
  assert.equal(records.filter((record) => record.path.endsWith("/cancel")).length, 0);
  await app.openProject("A"); await tick(); assert.equal(app.state.rendering.id, "active");
});
test("explicit queue cancel preserves completed images and is independent of prompt cancellation", async () => {
  const { app, queues, records } = harness(); await app.openProject("A");
  queues.set("active", { id: "active", projectId: "A", revision: 1, status: "running", pages: [{ page: 1, status: "complete" }, { page: 2, status: "running" }], completed: 1, total: 2 }); await app.refreshQueues();
  await app.queueAction("cancel"); await tick(); assert.equal(app.state.rendering.status, "paused"); assert.equal(app.state.rendering.completed, 1);
  assert.ok(records.some((record) => record.path.endsWith("/render-queues/active/cancel"))); assert.equal(records.filter((record) => record.path.endsWith("/A/cancel")).length, 0);
});
test("failed pages require explicit paid-redo confirmation, unknown pages excluded", async () => {
  const { app, queues, records } = harness(); await app.openProject("A");
  queues.set("partial", { id: "partial", projectId: "A", revision: 1, status: "partial", settings: { model: "gpt-image-2", quality: "high", generationProfile: "standard" }, pages: [{ page: 1, status: "complete" }, { page: 2, status: "error", error: "known failure" }, { page: 3, status: "needs_attention" }], completed: 1, total: 3 }); await app.refreshQueues();
  await app.renderImages("retry"); assert.equal(records.filter((record) => record.path.endsWith("/render-queue")).length, 0); assert.deepEqual(app.state.redoConfirmation.pageNumbers, [2]);
  await app.confirmRedo(); const submitted = records.find((record) => record.path.endsWith("/render-queue")); assert.equal(submitted.json.mode, "redo"); assert.deepEqual(submitted.json.pageNumbers, [2]);
});
test("changing product or render settings invalidates pending paid redo confirmation", async () => {
  const { app, records } = harness(); await app.openProject("A"); app.requestRedo(); app.updateForm({ ...app.state.form, quality: "medium" }); await app.confirmRedo();
  assert.equal(records.filter((record) => record.path.endsWith("/render-queue")).length, 0); app.requestRedo(); app.newProduct(); await app.confirmRedo();
  assert.equal(records.filter((record) => record.path.endsWith("/render-queue")).length, 0);
});
test("late queue GET cannot replace newly submitted queue state", async () => {
  const gate = deferred(); let holds = true;
  const { app, queues } = harness(project(), (path) => holds && path.includes("/render-queues?") ? gate.promise : undefined);
  await app.openProject("A"); holds = false; await app.renderImages("current"); await tick(); const id = app.state.rendering.id;
  gate.resolve({ ok: true, queues: [] }); await tick(); assert.equal(app.state.rendering.id, id); assert.equal(queues.size, 1);
});
test("rules warnings are advisory and repair routes only to explicit repair mode", async () => {
  const { app, records } = harness(); await app.openProject("A"); await app.review("rules");
  assert.equal(app.state.project.qualityReport.source, "rules"); assert.equal(canUsePrompt(app.state), true); assert.ok(fullPack(app.state));
  await app.generate("repair"); assert.equal(records.find((record) => record.path.endsWith("/generate")).json.mode, "repair");
});
test("late AI review cannot replace a different product", async () => {
  const gate = deferred(), { app, docs } = harness(project(), (path) => path.endsWith("/review") ? gate.promise : undefined); docs.set("B", project("B", "烤虾"));
  await app.openProject("A"); const reviewing = app.review("ai"); await app.openProject("B"); gate.resolve({ ok: true, project: project("A", "便携榨汁杯", { status: "reviewing" }) }); await reviewing;
  assert.equal(app.state.project.id, "B"); assert.equal(app.state.project.qualityReport, undefined);
});
test("invalid manual-save response never removes locally persisted draft", async () => {
  const store = memoryStorage(), { app } = harness(project(), (path) => path.endsWith("/edit-page") ? { ok: true, project: project("B", "错误商品") } : undefined, store);
  await app.openProject("A"); app.setPageEditor("保留这个草稿"); await app.savePage("保留这个草稿"); app.selectPage(2); app.selectPage(1);
  assert.equal(app.state.pageEditorValue, "保留这个草稿"); assert.equal(currentDrafts(app.state).length, 1); assert.equal(app.state.project.id, "A");
});
test("queue result refresh never overwrites local form/reference/page edits", async () => {
  const { app } = harness(); await app.openProject("A"); app.setPageEditor("本页草稿"); app.updateForm({ ...app.state.form, style: "未保存配色" });
  const file = new Blob(["pending"], { type: "image/png" }); Object.defineProperty(file, "name", { value: "new-product.png" }); app.setReferences([file]); await app.refreshQueues();
  assert.equal(app.state.form.style, "未保存配色"); assert.equal(app.state.pageEditorValue, "本页草稿"); assert.equal(app.references()[0].file, file); assert.equal(app.state.dirty, true);
});
test("missing localStorage does not falsely claim persistent page drafts", async () => {
  const { app } = harness(); await app.openProject("A"); app.setPageEditor("当前修改只能保留在内存");
  assert.match(app.state.draftError, /存储失败/);
  app.selectPage(2); app.selectPage(1); assert.equal(app.state.pageEditorValue, "当前修改只能保留在内存");
});
test("archive failures show exact unavailable pages instead of generic success", async () => {
  const { app } = harness(project(), (path) => path.endsWith("/archive-images") ? { ok: true, project: project(), archived: 0, message: "0张图片已长期保存", errors: [{ page: 2, message: "原图已过期" }] } : undefined);
  await app.openProject("A"); await app.archiveImages(); assert.match(app.state.notice, /第2页：原图已过期/);
});
