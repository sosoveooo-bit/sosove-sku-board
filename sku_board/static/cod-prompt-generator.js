(() => {
  "use strict";
  const API = "/api/sku-board/cod-atelier";
  const STORAGE_KEY = "cod-prompt-atelier-v2";
  const PAGE_DRAFTS_KEY = "cod-prompt-atelier-page-drafts-v1";
  const LEGACY_STORAGE_KEY = "cod-prompt-atelier-v1";
  const EXPORT_MODE_VERSION = "single-page-v1";
  const DEFAULT_FORM = Object.freeze({ product: "", market: "JP", intensity: "cod", main: 15, detail: 22, size: "750x1000", model: "gpt-image-2", quality: "high", generationProfile: "standard", reference: "", points: [], discount: "", salePrice: "", codText: "", deadline: "", allowPromo: true, allowMedical: true, style: "", avoid: "" });
  const MARKET = { JP: { label: "日本", language: "日文" }, KR: { label: "韩国", language: "韩文" }, US: { label: "美国", language: "英文" }, DE: { label: "德国", language: "德文" } };
  const STATUS = { draft: "等待生成", planning: "AI 正在分析与规划", generating: "AI 正在分批生成", reviewing: "AI 正在检查提示词", complete: "整套已完成", partial: "部分完成，可继续补齐", error: "AI 生成失败", cancelled: "已停止，已完成页保留" };
  const QUEUE_STATUS = { queued: "后台排队中", running: "后台生成中", paused: "已暂停", partial: "部分完成", complete: "本轮已完成", error: "队列失败", needs_attention: "任务结果待核实" };
  const ROLE_LABELS = { product: "主 SKU / 产品", detail: "产品细节", person: "人物参考", usage: "使用场景", layout: "版式参考" };
  const RENDER_KEYS = ["model", "quality", "generationProfile"];
  function splitPoints(value) { return (Array.isArray(value) ? value : String(value || "").split(/[\n\r；;]+/)).map((point) => String(point).trim()).filter(Boolean); }
  function normalizeForm(value = {}) {
    const form = { ...DEFAULT_FORM, ...value };
    Object.keys(DEFAULT_FORM).filter((key) => typeof DEFAULT_FORM[key] === "string").forEach((key) => { form[key] = String(form[key] ?? DEFAULT_FORM[key]).trim(); });
    form.points = splitPoints(form.points);
    form.main = Number(form.main); form.detail = Number(form.detail);
    form.allowPromo = form.allowPromo !== false; form.allowMedical = form.allowMedical !== false;
    return form;
  }
  function validateForm(form) {
    if (!form.product) throw new Error("请先填写当前商品名称。");
    if (!Number.isInteger(form.main) || form.main < 1 || form.main > 30) throw new Error("主图数量请填写 1–30 的整数。");
    if (!Number.isInteger(form.detail) || form.detail < 1 || form.detail > 40) throw new Error("详情数量请填写 1–40 的整数。");
    if (!/^\d+\s*[x×]\s*\d+$/i.test(form.size)) throw new Error("画布尺寸请填写宽×高，例如 750x1000。");
    if (!form.points.length) throw new Error("请至少填写一条当前商品的真实卖点或噱头。");
    return form;
  }
  function contentSignature(form) { const normalized = normalizeForm(form); return JSON.stringify(Object.keys(DEFAULT_FORM).filter((key) => !RENDER_KEYS.includes(key)).map((key) => [key, normalized[key]])); }
  function totalCount(form) { return Number(form.main) + Number(form.detail); }
  function isRunning(project) { return ["planning", "generating", "reviewing"].includes(project?.status); }
  function queueRunning(queue) { return ["queued", "running"].includes(queue?.status); }
  function draftKey(project, page) { return project?.id ? `${project.id}:${Number(project.revision)}:${Number(page)}` : ""; }
  function currentDrafts(state) { return Object.values(state.pageDrafts || {}).filter((draft) => draft.projectId === state.project?.id && Number(draft.revision) === Number(state.project?.revision)); }
  function hasPageDraft(state, page) { return Boolean(state.pageDrafts?.[draftKey(state.project, page)]); }
  function sortedPages(project) {
    const pages = new Map((Array.isArray(project?.outline) ? project.outline : []).map((page) => [Number(page.page), page]));
    (Array.isArray(project?.suitePages) ? project.suitePages : []).forEach((page) => pages.set(Number(page.page), { ...pages.get(Number(page.page)), ...page }));
    return [...pages.values()].sort((a, b) => Number(a.page) - Number(b.page));
  }
  function visiblePages(project, section = "all") { return sortedPages(project).filter((page) => section === "all" || page.section === section); }
  function snapshotFresh(state) { return Boolean(state.project && !state.dirty && contentSignature(state.form) === contentSignature(state.project.form)); }
  function canUsePrompt(state, page = null) {
    if (!snapshotFresh(state) || state.busy || isRunning(state.project)) return false;
    if (page ? hasPageDraft(state, page.page) || Number(page.page) === state.selectedPage && state.pageEditorDirty : currentDrafts(state).length || state.pageEditorDirty) return false;
    return page ? Boolean(page.modelPrompt && page.executionPrompt) : Boolean(state.project.masterPrompt);
  }
  function suiteComplete(state) {
    const pages = sortedPages(state.project);
    return canUsePrompt(state) && state.project.status === "complete" && pages.length === totalCount(state.form) && pages.every((page, index) => Number(page.page) === index + 1 && page.modelPrompt && page.executionPrompt);
  }
  function pageLabel(page) { return page ? `${page.section === "main" ? "主图" : "详情"}${String(page.localIndex || page.page).padStart(2, "0")}` : "未选页面"; }
  function fullPack(state, mode = state.exportMode || "compact") {
    if (!suiteComplete(state)) throw new Error("整套提示词尚未完成，或输入已修改；请完成当前版本后再复制整套。");
    if (mode === "standalone") return sortedPages(state.project).map((page) => `===== ${pageLabel(page)} · ${page.title || ""} · 独立执行版 =====\n${page.executionPrompt}`).join("\n\n");
    const shared = state.project.sharedExecutionRequirements;
    if (!shared) throw new Error("此旧版本没有共享执行要求快照，请改选“逐张独立版”导出，或生成新版本后使用整套导入版。");
    return [state.project.masterPrompt, "\n===== SHARED EXECUTION REQUIREMENTS / 全套执行要求（仅一次） =====", String(shared), "\n===== PAGE CREATIVE PROMPTS / 逐页创意（共同遵循上方总控与要求） =====", ...sortedPages(state.project).map((page) => `\n===== ${pageLabel(page)} · ${page.title || ""} =====\n${page.modelPrompt}`)].join("\n");
  }
  function materialEntries(project) {
    const value = project?.materials;
    if (Array.isArray(value)) return value.map((material, index) => [Number(material.pageNumber || material.suitePage || material.page || index + 1), material]);
    return value && typeof value === "object" ? Object.entries(value).flatMap(([key, material]) => (Array.isArray(material) ? material : [material]).filter(Boolean).map((item) => [Number(item.pageNumber || item.suitePage || item.page || key), item])) : [];
  }
  function errorText(value) { return typeof value === "string" ? value : value?.message || (value ? JSON.stringify(value) : ""); }
  function actualDirectorModel(director = {}) { return director.activeModel || director.actualModel || (director.source === "model" && director.status !== "running" ? director.model : "") || ""; }
  function versionSelection(project, previousProject, previousRevision, chosen) { return previousProject === project?.id && Number(previousRevision) === Number(project?.revision) && chosen ? chosen : String(project?.revision || ""); }

  // Every callback is scoped to both a local request token and a saved revision.
  // Late responses can remain archived, but cannot repaint a different product.
  function createController({ request, notify = () => {}, changed = () => {}, schedule = setTimeout, unschedule = clearTimeout, draftStorage = null, initialForm = DEFAULT_FORM } = {}) {
    const state = { form: normalizeForm(initialForm), project: null, projects: [], dirty: false, token: 0, busy: "", error: "", notice: "", referencesMode: "replace", localReferences: [], referenceRoles: [], referenceSequence: 0, selectedPage: 1, filter: "all", pageEditorDirty: false, pageEditorValue: "", pageEditorKey: "", pageEditorSource: "saved", pageDrafts: Object.create(null), draftError: "", exportMode: "compact", historical: false, rendering: null, queues: [], queueId: "", queueError: "", queueTimer: null, queueBusy: false, redoConfirmation: null, hiddenGallery: false, config: null, configError: "", directorConfig: null, directorConfigError: "", libraryError: "", pollTimer: null };
    let queueReadSequence = 0;
    try {
      const stored = JSON.parse(draftStorage?.getItem(PAGE_DRAFTS_KEY) || "{}");
      Object.entries(stored || {}).forEach(([key, draft]) => { if (draft && typeof draft.value === "string" && key === draftKey({ id: draft.projectId, revision: draft.revision }, draft.page)) state.pageDrafts[key] = draft; });
    } catch (_) { state.draftError = "单页草稿读取失败；服务器已保存版本未受影响。"; }
    function persistPageDrafts() {
      try { if (!draftStorage?.setItem) throw new Error("local storage unavailable"); draftStorage.setItem(PAGE_DRAFTS_KEY, JSON.stringify(state.pageDrafts)); state.draftError = ""; }
      catch (_) { state.draftError = "本地草稿存储失败，文字暂保留在本页内存；请保存或复制后再关闭网页。"; }
    }
    function syncEditor() {
      const key = draftKey(state.project, state.selectedPage);
      const page = sortedPages(state.project).find((item) => Number(item.page) === state.selectedPage);
      const draft = state.pageDrafts[key];
      if (state.pageEditorKey === key && (state.pageEditorDirty || state.pageEditorValue === (page?.modelPrompt || ""))) return;
      state.pageEditorKey = key; state.pageEditorValue = draft?.value ?? page?.modelPrompt ?? "";
      state.pageEditorDirty = Boolean(draft); state.pageEditorSource = draft ? "restored" : "saved";
    }
    const emit = () => { syncEditor(); changed(state); };
    const scope = () => ({ token: state.token, id: state.project?.id || "", revision: Number(state.project?.revision || 0) });
    const current = (context) => context.token === state.token && context.id === (state.project?.id || "") && context.revision === Number(state.project?.revision || 0);
    function resetEditor() { state.pageEditorDirty = false; state.pageEditorValue = ""; state.pageEditorKey = ""; state.pageEditorSource = "saved"; }
    function quietCancel(project) {
      if (!project?.id || !project?.revision) return Promise.resolve();
      return request(`${API}/projects/${encodeURIComponent(project.id)}/cancel`, { method: "POST", json: { revision: project.revision } }).catch(() => {});
    }
    function invalidate(cancel = true) {
      const previous = state.project;
      if (state.pollTimer != null) unschedule(state.pollTimer);
      if (state.queueTimer != null) unschedule(state.queueTimer);
      queueReadSequence += 1;
      state.pollTimer = null; state.token += 1;
      if (cancel && isRunning(previous)) void quietCancel(previous);
      // Render runs belong to the server snapshot: changing products never cancels them.
      state.queueTimer = null; state.queues = []; state.queueId = ""; state.queueError = ""; state.queueBusy = false; state.redoConfirmation = null;
      state.busy = ""; state.rendering = null; state.error = ""; resetEditor();
    }
    function start(kind) {
      if (state.busy) throw new Error("请先等待或停止当前提示词任务。");
      const editor = kind === "editing" ? { pageEditorValue: state.pageEditorValue, pageEditorDirty: state.pageEditorDirty, pageEditorKey: state.pageEditorKey } : null;
      invalidate(false);
      if (editor) Object.assign(state, editor);
      state.busy = kind;
      const context = scope(); emit(); return context;
    }
    function accept(project, context, { keepForm = false } = {}) {
      if (!current(context)) return false;
      if (!project?.id || !Number.isInteger(Number(project.revision))) throw new Error("服务器没有返回有效的商品版本。");
      if (context.id && project.id !== context.id) throw new Error("返回商品与当前请求不一致，已拒绝载入。");
      const preferences = Object.fromEntries(RENDER_KEYS.map((key) => [key, state.form[key]]));
      state.project = project;
      if (!keepForm) state.form = normalizeForm({ ...project.form, ...preferences });
      state.referencesMode = "keep"; state.localReferences = [];
      state.referenceRoles = (project.references || []).map((reference) => reference.role || "product");
      state.dirty = false; state.error = ""; state.hiddenGallery = false;
      state.historical = Boolean(project.currentRevision && Number(project.revision) < Number(project.currentRevision));
      if (context.revision !== Number(project.revision)) { resetEditor(); state.queues = []; state.queueId = ""; state.rendering = null; }
      context.id = project.id; context.revision = Number(project.revision);
      if (!sortedPages(project).some((page) => Number(page.page) === state.selectedPage)) state.selectedPage = Number(sortedPages(project)[0]?.page || 1);
      const index = state.projects.findIndex((item) => item.id === project.id);
      const summary = { id: project.id, name: project.name || project.form?.product, revision: project.currentRevision || project.revision, status: project.status, updatedAt: project.updatedAt };
      if (index >= 0) state.projects[index] = { ...state.projects[index], ...summary }; else state.projects.unshift(summary);
      return true;
    }
    function handleError(error, context) {
      if (!current(context)) return;
      state.error = String(error?.message || error); state.busy = "";
      emit(); notify(state.error);
    }
    function schedulePoll(context) {
      if (!current(context) || !isRunning(state.project)) return;
      state.pollTimer = schedule(async () => {
        state.pollTimer = null;
        try {
          const payload = await request(`${API}/projects/${encodeURIComponent(context.id)}?revision=${context.revision}`);
          if (!current(context)) return;
          if (Number(payload.project?.revision) !== context.revision) throw new Error("轮询返回了不同版本，已停止回写。");
          const wasReviewing = state.project.status === "reviewing";
          accept(payload.project, context, { keepForm: true }); emit();
          if (isRunning(state.project)) schedulePoll(context);
          else if (wasReviewing) notify(state.project.qualityReport?.status === "error" ? "AI 质检未完整完成，请查看报告中的错误与已完成建议。" : "提示词质检完成，请查看具体页码与建议。");
          else if (state.project.status === "complete") notify("当前商品整套 AI Prompt 已完成。");
          else if (state.project.error) notify(errorText(state.project.error));
        } catch (error) { handleError(error, context); }
      }, 1400);
    }
    function updateForm(value) {
      const next = normalizeForm(value);
      if (contentSignature(next) === contentSignature(state.form)) { state.form = next; state.redoConfirmation = null; emit(); return; }
      const productChanged = next.product !== state.form.product;
      const previousProduct = state.project?.form;
      invalidate();
      if (productChanged) {
        if (previousProduct) {
          if (JSON.stringify(next.points) === JSON.stringify(splitPoints(previousProduct.points))) next.points = [];
          ["discount", "salePrice", "codText", "deadline", "avoid"].forEach((key) => { if (next[key] === String(previousProduct[key] || "")) next[key] = ""; });
        }
        state.project = null; state.historical = false; state.localReferences = []; state.referenceRoles = []; state.referencesMode = "replace"; next.reference = "";
        state.notice = "已切换新商品。旧项目仍在商品库；请更新卖点、促销并重新上传当前商品参考图。";
      } else state.notice = "商品输入已修改，旧版提示词仅供查看；重新生成前不能复制或生图。";
      state.form = next; state.dirty = true; state.selectedPage = 1; emit();
    }
    function newProduct() {
      const preferences = Object.fromEntries(["market", "intensity", "main", "detail", "size", ...RENDER_KEYS].map((key) => [key, state.form[key]]));
      invalidate(); state.project = null; state.form = normalizeForm(preferences); state.localReferences = []; state.referenceRoles = []; state.referencesMode = "replace"; state.dirty = false; state.historical = false; state.selectedPage = 1;
      state.notice = "新商品草稿：重新填写产品与卖点。旧商品存档未改动。"; emit();
    }
    function setReferences(files) {
      invalidate(); state.referencesMode = "replace";
      state.localReferences = Array.from(files || []).slice(0, 12).map((file) => ({ file, role: "product", key: ++state.referenceSequence }));
      state.referenceRoles = state.localReferences.map((reference) => reference.role);
      state.dirty = true; state.notice = "参考图已替换，旧版已过期；服务器会按图片内容重新绑定。"; emit();
    }
    function setReferenceRole(index, role) {
      if (!ROLE_LABELS[role]) return;
      invalidate(); state.referenceRoles[index] = role;
      if (state.localReferences[index]) state.localReferences[index].role = role;
      state.dirty = true; state.notice = "参考图用途已改变，需要重新生成提示词。"; emit();
    }
    function references() {
      if (state.referencesMode === "replace") return state.localReferences.map((reference, index) => ({ ...reference, index: index + 1, name: reference.file.name, size: reference.file.size, mime: reference.file.type, role: state.referenceRoles[index] || reference.role }));
      return (state.project?.references || []).map((reference, index) => ({ ...reference, role: state.referenceRoles[index] || reference.role || "product" }));
    }
    function uploadBody() {
      const body = new FormData(); body.append("form", JSON.stringify(state.form));
      if (state.project) { body.append("projectId", state.project.id); body.append("revision", String(state.project.revision)); }
      body.append("referencesMode", state.referencesMode);
      body.append("referenceBindings", JSON.stringify(references().map((reference, index) => ({ index: index + 1, role: reference.role }))));
      if (state.referencesMode === "replace") state.localReferences.forEach((reference, index) => body.append(`reference${index}`, reference.file, reference.file.name));
      return body;
    }
    function requireCurrentVersion() { if (state.historical) throw new Error("这是历史版本，可复制或生图；请从版本菜单打开最新版本后再修改。旧版不会被覆盖。"); }
    async function saveWithin(context) {
      validateForm(state.form); requireCurrentVersion();
      if (snapshotFresh(state)) return state.project;
      const payload = await request(`${API}/projects/upload`, { method: "POST", body: uploadBody() });
      if (!current(context)) return null;
      accept(payload.project, context); state.notice = "商品与参考图已存入独立版本。"; return state.project;
    }
    async function saveProject() {
      let context;
      try {
        if (state.pageEditorDirty) throw new Error("当前页还有未保存修改，请先点击“保存单页修改”。");
        context = start("saving"); const project = await saveWithin(context); if (!project || !current(context)) return; state.busy = ""; emit(); notify("商品与参考图已保存。");
      }
      catch (error) { if (context) handleError(error, context); else notify(error.message); }
    }
    async function listProjects() {
      try { const payload = await request(`${API}/projects`); state.projects = Array.isArray(payload.projects) ? payload.projects : []; state.libraryError = ""; }
      catch (error) { state.libraryError = error.message; }
      emit(); return state.projects;
    }
    async function openProject(id, revision = null, { draft = null } = {}) {
      if (!id) { notify("请先选择一个已保存商品。"); return; }
      const previous = Object.fromEntries(["form", "project", "dirty", "localReferences", "referenceRoles", "referencesMode", "notice", "historical", "selectedPage", "pageEditorValue", "pageEditorDirty", "pageEditorKey"].map((key) => [key, state[key]]));
      invalidate(); state.project = null; state.dirty = true; state.busy = "loading"; state.form = normalizeForm({ ...state.form, product: "" }); state.localReferences = []; state.referenceRoles = []; state.referencesMode = "replace"; state.notice = "正在读取商品存档…";
      const context = scope(); emit();
      try {
        const payload = await request(`${API}/projects/${encodeURIComponent(id)}${revision ? `?revision=${encodeURIComponent(revision)}` : ""}`);
        if (!current(context)) return;
        if (payload.project?.id !== id || revision && Number(payload.project?.revision) !== Number(revision)) throw new Error("商品存档版本不匹配，已拒绝载入。");
        accept(payload.project, context); state.busy = "";
        state.notice = state.historical ? `正在查看历史 v${revision}，可复制或生图；修改请打开最新版本。` : "已恢复商品、参考图、提示词与成图。";
        if (draft?.dirty && draft.form?.product === state.form.product) {
          state.form = normalizeForm(draft.form); state.dirty = true;
          if (draft.referencesMode === "replace") { state.referencesMode = "replace"; state.localReferences = []; state.referenceRoles = []; }
          else if (Array.isArray(draft.referenceRoles)) state.referenceRoles = draft.referenceRoles;
          state.notice = "已恢复未保存文字草稿。旧版不可执行；未保存的本地图片需重新上传。";
        }
        emit(); if (!state.dirty) schedulePoll(context);
        void refreshQueues(context);
      } catch (error) {
        if (!current(context)) return;
        Object.assign(state, previous);
        state.busy = ""; state.error = error.message; state.notice = "读取未成功，原先的商品与未保存输入已保留。";
        emit(); notify(error.message);
      }
    }
    async function generate(mode = "fresh", instruction = "") {
      let context;
      const pageNumber = state.selectedPage;
      try {
        requireCurrentVersion();
        if (isRunning(state.project) && !state.dirty) throw new Error("AI 正在生成此版本，请等待或先停止。");
        if (currentDrafts(state).length || state.pageEditorDirty) throw new Error("这个版本还有单页草稿；请先保存修改，或在对应页明确放弃草稿。");
        if (mode !== "fresh" && !snapshotFresh(state)) throw new Error("输入已修改，请重新生成整套；补齐和单页重写只针对当前已保存版本。");
        context = start(mode === "page" || mode === "repair" ? "rewriting" : "submitting");
        if (mode === "fresh" && !await saveWithin(context)) return;
        if (!current(context)) return;
        const payload = await request(`${API}/projects/${encodeURIComponent(context.id)}/generate`, { method: "POST", json: { revision: context.revision, mode, ...(mode === "page" ? { pageNumber, instruction } : {}) } });
        if (!current(context)) { if (payload.project && isRunning(payload.project)) void quietCancel(payload.project); return; }
        accept(payload.project, context); state.busy = ""; resetEditor();
        state.notice = mode === "resume" ? "只补未完成 Prompt，已完成页保留。" : mode === "repair" ? "正在新版本中只修复质检标记的页面与钩子，其他内容保持不变。" : mode === "page" ? "正在重写选中页，旧版本仍可打开。" : "已启动新一套原创 Prompt：先分析规划，再分批完成逐页内容。";
        emit(); schedulePoll(context); void refreshQueues(context);
      } catch (error) { if (context) handleError(error, context); else notify(error.message); }
    }
    async function stop() {
      const project = state.project;
      const draft = state.dirty ? Object.fromEntries(["form", "dirty", "localReferences", "referenceRoles", "referencesMode"].map((key) => [key, state[key]])) : null;
      invalidate(false);
      if (!project) { state.notice = "已停止接收当前请求。"; emit(); return; }
      state.busy = "stopping"; const context = scope(); emit();
      try {
        const payload = await request(`${API}/projects/${encodeURIComponent(project.id)}/cancel`, { method: "POST", json: { revision: project.revision } });
        if (!current(context)) return;
        accept(payload.project, context, { keepForm: true });
        if (draft) Object.assign(state, draft);
        state.busy = "";
        state.notice = "已停止提示词后续生成，已完成页保留；独立的后台生图队列不受影响。"; emit(); void refreshQueues(context);
      } catch (error) { handleError(error, context); }
    }
    async function savePage(modelPrompt) {
      let context;
      try {
        requireCurrentVersion();
        if (!snapshotFresh(state) || isRunning(state.project)) throw new Error("商品输入有修改或当前版本仍在生成，请先完成整套。");
        if (!String(modelPrompt || "").trim()) throw new Error("当前页 Prompt 不能为空。");
        const pageNumber = state.selectedPage, savedDraftKey = draftKey(state.project, pageNumber); context = start("editing");
        const payload = await request(`${API}/projects/${encodeURIComponent(context.id)}/edit-page`, { method: "POST", json: { revision: context.revision, pageNumber, modelPrompt } });
        if (!current(context)) return;
        accept(payload.project, context);
        if (state.pageDrafts[savedDraftKey]?.value === modelPrompt) { delete state.pageDrafts[savedDraftKey]; persistPageDrafts(); }
        state.busy = ""; resetEditor(); state.notice = "单页修改已另存版本。其他未保存单页草稿仍留在原版本，可打开原版本恢复。"; emit(); notify("当前页已保存为新版本。"); void refreshQueues(context);
      } catch (error) { if (context) handleError(error, context); else notify(error.message); }
    }
    function setPageEditor(value) {
      const page = sortedPages(state.project).find((item) => Number(item.page) === state.selectedPage), key = draftKey(state.project, state.selectedPage);
      if (!key || !page) return;
      state.pageEditorKey = key; state.pageEditorValue = String(value); state.pageEditorDirty = state.pageEditorValue !== (page.modelPrompt || ""); state.pageEditorSource = "editing";
      if (state.pageEditorDirty) state.pageDrafts[key] = { projectId: state.project.id, revision: Number(state.project.revision), page: state.selectedPage, value: state.pageEditorValue, sourceModelPrompt: state.pageDrafts[key]?.sourceModelPrompt ?? page.modelPrompt ?? "", updatedAt: new Date().toISOString() };
      else delete state.pageDrafts[key];
      persistPageDrafts(); emit();
    }
    function discardPageDraft() { const key = draftKey(state.project, state.selectedPage); delete state.pageDrafts[key]; persistPageDrafts(); resetEditor(); state.notice = "已放弃本页未保存草稿，恢复此版本的已保存 Prompt；服务器版本未改动。"; emit(); }
    function selectPage(number) { state.selectedPage = Number(number); state.redoConfirmation = null; resetEditor(); emit(); }
    function setFilter(section) { state.filter = ["all", "main", "detail"].includes(section) ? section : "all"; emit(); }
    function queueSnapshot(queue) {
      if (!queue) return null;
      const pages = Array.isArray(queue.pages) ? queue.pages : [];
      return { ...queue, running: queueRunning(queue), requested: pages.map((page) => Number(page.page)), completed: Number(queue.completed ?? queue.counts?.completed ?? 0), total: Number(queue.total ?? queue.counts?.total ?? pages.length), active: Number(pages.find((page) => ["running", "submitted", "pending"].includes(page.status))?.page || 0), errors: pages.filter((page) => ["error", "failed"].includes(page.status)).map((page) => ({ page: Number(page.page), message: errorText(page.error) || "本页任务失败" })) };
    }
    function acceptQueues(queues, context, preferId = "") {
      if (!current(context)) return false;
      if (!Array.isArray(queues)) throw new Error("服务器未返回有效的后台队列列表。");
      if (queues.some((queue) => queue.projectId !== context.id || Number(queue.revision) !== context.revision)) throw new Error("后台队列不属于当前商品版本，已拒绝显示。");
      state.queues = queues.slice().sort((a, b) => String(b.updatedAt || b.createdAt || "").localeCompare(String(a.updatedAt || a.createdAt || "")));
      const selected = state.queues.find((queue) => queue.id === (preferId || state.queueId)) || state.queues.find(queueRunning) || state.queues[0];
      state.queueId = selected?.id || ""; state.rendering = queueSnapshot(selected); state.queueError = "";
      return true;
    }
    function scheduleQueuePoll(context) {
      if (!current(context) || !state.queues.some(queueRunning)) return;
      if (state.queueTimer != null) unschedule(state.queueTimer);
      state.queueTimer = schedule(() => { state.queueTimer = null; void refreshQueues(context); }, 2400);
    }
    async function refreshQueues(context = scope()) {
      if (!context.id || !current(context)) return;
      const readSequence = ++queueReadSequence;
      try {
        const payload = await request(`${API}/projects/${encodeURIComponent(context.id)}/render-queues?revision=${context.revision}`);
        if (!current(context) || readSequence !== queueReadSequence) return;
        acceptQueues(payload.queues, context); emit();
        const latest = await request(`${API}/projects/${encodeURIComponent(context.id)}?revision=${context.revision}`);
        if (!current(context) || readSequence !== queueReadSequence) return;
        if (latest.project?.id !== context.id || Number(latest.project?.revision) !== context.revision) throw new Error("成图存档返回了不同商品版本。");
        // Refresh results only; never replace typed inputs, reference files, or a page draft.
        state.project.materials = latest.project.materials || [];
        emit(); scheduleQueuePoll(context);
      } catch (error) { if (current(context) && readSequence === queueReadSequence) { state.queueError = error.message; emit(); scheduleQueuePoll(context); } }
    }
    function selectQueue(id) { const queue = state.queues.find((item) => item.id === id); if (queue) { state.queueId = id; state.rendering = queueSnapshot(queue); state.redoConfirmation = null; emit(); } }
    function renderSettings() { return Object.fromEntries(RENDER_KEYS.map((key) => [key, state.form[key]])); }
    function requestRedo(mode = "current") {
      if (!snapshotFresh(state) || state.queueBusy) return;
      const pageNumbers = mode === "retry" ? (state.rendering?.errors || []).map((item) => item.page) : [state.selectedPage];
      if (!pageNumbers.length) { notify("当前没有可明确重试的失败页；结果待核实的任务不会自动重提。"); return; }
      state.redoConfirmation = { ...scope(), pageNumbers, settings: renderSettings() }; emit();
    }
    async function confirmRedo() {
      const confirmation = state.redoConfirmation;
      if (!confirmation || !current(confirmation) || JSON.stringify(confirmation.settings) !== JSON.stringify(renderSettings())) { state.redoConfirmation = null; emit(); notify("版本或生图设置已变化，请重新确认。"); return; }
      const pages = confirmation.pageNumbers.slice(); state.redoConfirmation = null;
      await renderImages("redo", pages);
    }
    async function renderImages(mode = "current", confirmedPages = null) {
      const context = scope();
      try {
        if (state.queueBusy) return;
        const page = sortedPages(state.project).find((item) => Number(item.page) === state.selectedPage);
        if (!canUsePrompt(state, page)) throw new Error("当前版本或选中页未就绪，或存在未保存修改。请完成 Prompt 后再生图。");
        if (!references().length) throw new Error("真实生图需要当前商品参考图；请上传并重新生成提示词。");
        if (mode === "suite" && !suiteComplete(state)) throw new Error("整套尚未完成，可先对已完成页单独生图。");
        if (mode === "retry" || mode === "redo" && !confirmedPages) { requestRedo(mode === "retry" ? "retry" : "current"); return; }
        const pageNumbers = mode === "suite" ? sortedPages(state.project).map((item) => Number(item.page)) : mode === "redo" ? confirmedPages : [state.selectedPage];
        if (!pageNumbers.length || pageNumbers.some((number) => { const requestedPage = sortedPages(state.project).find((item) => Number(item.page) === number); return !requestedPage || !canUsePrompt(state, requestedPage); })) throw new Error("所选页面有未保存草稿或未完成的 Prompt，请先处理。");
        state.queueBusy = true; state.queueError = ""; queueReadSequence += 1; emit();
        const payload = await request(`${API}/projects/${encodeURIComponent(context.id)}/render-queue`, { method: "POST", json: { revision: context.revision, mode: mode === "redo" ? "redo" : "resume", pageNumbers, ...renderSettings() } });
        if (!current(context)) return;
        queueReadSequence += 1; acceptQueues([payload.queue, ...state.queues.filter((queue) => queue.id !== payload.queue?.id)], context, payload.queue?.id);
        state.queueBusy = false; state.notice = mode === "redo" ? "已确认重生成：新任务可能计费，旧图仍保留。" : "后台队列已保存：已完成或进行中的任务会复用，关闭页面后未完成任务仍由本地服务处理。"; emit();
        void refreshQueues(context);
      } catch (error) { if (current(context)) { state.queueBusy = false; state.queueError = error.message; emit(); notify(error.message); } }
    }
    async function queueAction(action, id = state.queueId) {
      const context = scope();
      if (!context.id || !id || state.queueBusy || !["resume", "cancel"].includes(action)) return;
      try {
        state.queueBusy = true; queueReadSequence += 1; emit();
        const payload = await request(`${API}/projects/${encodeURIComponent(context.id)}/render-queues/${encodeURIComponent(id)}/${action}`, { method: "POST", json: { revision: context.revision } });
        if (!current(context)) return;
        queueReadSequence += 1; acceptQueues([payload.queue, ...state.queues.filter((queue) => queue.id !== payload.queue?.id)], context, payload.queue?.id);
        state.queueBusy = false; state.notice = action === "cancel" ? "已停止此队列后续提交；已提交供应商的任务仍可能完成并计费。已完成图片保留。" : "只继续尚未提交的任务，不会自动重试失败或结果不明的页。"; emit(); void refreshQueues(context);
      } catch (error) { if (current(context)) { state.queueBusy = false; state.queueError = error.message; emit(); notify(error.message); } }
    }
    async function review(mode = "rules") {
      let context;
      try {
        if (!canUsePrompt(state)) throw new Error("请先保存单页草稿并完成当前版本，再检查提示词。");
        context = start("reviewing");
        const payload = await request(`${API}/projects/${encodeURIComponent(context.id)}/review`, { method: "POST", json: { revision: context.revision, mode: mode === "ai" ? "ai" : "rules" } });
        if (!current(context)) return;
        accept(payload.project, context, { keepForm: true }); state.busy = "";
        state.notice = mode === "ai" ? "AI 检查已启动；报告是修改建议，不代表语言或宣称已获人工验证。" : "规则检查已完成；只能识别结构和文本信号，不能保证本土语言自然度。"; emit(); schedulePoll(context); void refreshQueues(context);
      } catch (error) { if (context) handleError(error, context); else notify(error.message); }
    }
    async function archiveImages() {
      const context = scope(); if (!context.id || state.queueBusy) return;
      try {
        state.queueBusy = true; emit();
        const payload = await request(`${API}/projects/${encodeURIComponent(context.id)}/archive-images`, { method: "POST", json: { revision: context.revision } });
        if (!current(context)) return;
        if (payload.project?.id === context.id && Number(payload.project?.revision) === context.revision) state.project.materials = payload.project.materials || [];
        state.queueBusy = false;
        state.notice = payload.message || "已尝试长期保存此版本仍可读取的成图。";
        if (Array.isArray(payload.errors) && payload.errors.length) state.notice += "；" + payload.errors.map((item) => `第${item.page || "—"}页：${item.message || "原图不可用"}`).join("；");
        emit(); void refreshQueues(context);
      } catch (error) { if (current(context)) { state.queueBusy = false; state.queueError = error.message; emit(); notify(error.message); } }
    }
    return { state, updateForm, newProduct, setReferences, setReferenceRole, references, saveProject, listProjects, openProject, generate, stop, savePage, setPageEditor, discardPageDraft, selectPage, setFilter, renderImages, refreshQueues, selectQueue, queueAction, requestRedo, confirmRedo, review, archiveImages, emit, scope, current };
  }

  function esc(value) { return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char])); }
  function safeImageUrl(value) { const url = String(value || ""); return /^(?:https?:\/\/|blob:|data:image\/(?:png|jpe?g|webp);base64,|\/(?!\/))/i.test(url) ? url : ""; }
  function ratioLabel(size) {
    const match = String(size).match(/^(\d+)\s*[x×]\s*(\d+)$/i);
    if (!match || !Number(match[1]) || !Number(match[2])) return "—";
    const gcd = (a, b) => b ? gcd(b, a % b) : a;
    const divisor = gcd(Number(match[1]), Number(match[2])); return `${Number(match[1]) / divisor}:${Number(match[2]) / divisor}`;
  }
  const exported = { DEFAULT_FORM, PAGE_DRAFTS_KEY, normalizeForm, validateForm, contentSignature, totalCount, sortedPages, visiblePages, snapshotFresh, canUsePrompt, suiteComplete, fullPack, materialEntries, draftKey, currentDrafts, hasPageDraft, createController, safeImageUrl, actualDirectorModel, versionSelection };
  if (typeof module !== "undefined" && module.exports) module.exports = exported;
  if (typeof document === "undefined") return;

  const $ = (id) => document.getElementById(id);
  const FIELDS = { product: "product-name", market: "target-market", intensity: "hook-intensity", main: "main-count", detail: "detail-count", size: "canvas-size", reference: "reference-map", points: "selling-points", discount: "discount", salePrice: "sale-price", codText: "cod-text", deadline: "deadline", allowPromo: "allow-promo", allowMedical: "allow-medical", style: "style-notes", avoid: "avoid-notes", model: "render-model", quality: "render-quality", generationProfile: "render-profile" };
  let app, toastTimer;
  let previewUrls = [], previewKey = "", uiReady = false, restoringDraft = true;
  const setText = (id, value) => { if ($(id)) $(id).textContent = value; };
  const disabled = (id, value) => { if ($(id)) $(id).disabled = Boolean(value); };
  const hidden = (id, value) => { if ($(id)) $(id).hidden = Boolean(value); };
  function toast(message) {
    let node = document.querySelector(".atelier-toast");
    if (!node) { node = document.createElement("div"); node.className = "atelier-toast"; node.setAttribute("role", "status"); document.body.appendChild(node); }
    node.textContent = message; node.classList.add("show");
    clearTimeout(toastTimer); toastTimer = setTimeout(() => node.classList.remove("show"), 4500);
  }
  async function apiRequest(path, options = {}) {
    const { json, ...requestOptions } = options;
    if (json !== undefined) { requestOptions.body = JSON.stringify(json); requestOptions.headers = { ...requestOptions.headers, "Content-Type": "application/json" }; }
    const response = await fetch(path, { ...requestOptions, credentials: "same-origin" });
    let payload;
    try { payload = JSON.parse(await response.text()); } catch (_) { throw new Error(`服务器返回异常（HTTP ${response.status}），请检查本地服务。`); }
    if (!response.ok || payload.ok === false) {
      const error = new Error([401, 403].includes(response.status) ? "请先登录主 SKU Board，并确认有此功能的访问权限。" : errorText(payload.error) || `请求失败（HTTP ${response.status}）`);
      error.status = response.status; throw error;
    }
    return payload;
  }
  function readForm() {
    const value = {};
    Object.entries(FIELDS).forEach(([key, id]) => { const input = $(id); if (input) value[key] = input.type === "checkbox" ? input.checked : input.value; });
    return normalizeForm(value);
  }
  function writeForm(form) {
    Object.entries(FIELDS).forEach(([key, id]) => {
      const input = $(id); if (!input) return;
      if (input.type === "checkbox") input.checked = Boolean(form[key]);
      else if (document.activeElement !== input) {
        const value = key === "points" ? form.points.join("\n") : String(form[key] ?? "");
        if (input.value !== value) input.value = value;
      }
    });
  }
  function readDraft() {
    try {
      const currentDraft = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
      if (currentDraft?.form) {
        // Older drafts defaulted to a multi-page blob that most image tools
        // cannot execute.  Migrate once; a deliberate later user choice is
        // persisted with the new version marker.
        return { ...currentDraft, exportMode: currentDraft.exportModeVersion === EXPORT_MODE_VERSION ? currentDraft.exportMode : "standalone", exportModeVersion: EXPORT_MODE_VERSION };
      }
      const legacy = JSON.parse(localStorage.getItem(LEGACY_STORAGE_KEY) || "null");
      if (legacy && typeof legacy === "object") return { form: normalizeForm(legacy), dirty: true, legacy: true };
    } catch (_) { /* Invalid local storage never blocks server archives. */ }
    return { form: normalizeForm(), dirty: false };
  }
  function saveDraft(state) {
    if (state.busy === "loading" || restoringDraft) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ form: state.form, projectId: state.project?.id || "", revision: state.project?.revision || null, historical: state.historical, dirty: state.dirty, selectedPage: state.selectedPage, exportMode: state.exportMode, exportModeVersion: EXPORT_MODE_VERSION, referencesMode: state.referencesMode, referenceRoles: state.referenceRoles }));
      setText("saved-state", state.draftError || (currentDrafts(state).length ? `本地暂存 ${currentDrafts(state).length} 页草稿 · 尚未提交` : state.project && !state.dirty ? `商品已存档 · v${state.project.revision}` : "文字草稿已保存 · 图片需保存商品"));
    } catch (_) { setText("saved-state", "本地存储不可用；请保存商品到服务器"); }
  }
  function selectedPage(state) { return sortedPages(state.project).find((page) => Number(page.page) === state.selectedPage); }
  function displayStatus(state) {
    if (state.busy === "loading") return "正在打开商品版本";
    if (state.busy === "saving") return "正在保存商品与参考图";
    if (state.busy === "stopping") return "正在停止服务器任务";
    if (state.busy === "reviewing") return "正在提交质量检查";
    if (state.busy) return "正在提交当前任务";
    if (state.error) return "请求失败 · 不会使用模板替代";
    if (!state.project) return state.form.product ? "新商品草稿 · 等待 AI 生成" : "新商品 · 请填写产品与卖点";
    if (state.dirty) return "输入已修改 · 旧版已过期";
    return STATUS[state.project.status] || state.project.status || "商品已保存";
  }
  function renderProjectControls(state) {
    const select = $("project-select");
    if (select) {
      const desired = select.value || state.project?.id || "";
      const html = `<option value="">选择已保存商品</option>` + state.projects.map((project) => `<option value="${esc(project.id)}">${esc(project.name || "未命名商品")} · v${esc(project.revision)} · ${esc(STATUS[project.status] || project.status || "")}</option>`).join("");
      if (select.innerHTML !== html) { select.innerHTML = html; select.value = desired; }
    }
    const versions = $("project-version");
    if (versions) {
      const summaries = Array.isArray(state.project?.versions) ? state.project.versions : [];
      const desired = versionSelection(state.project, versions.dataset.project, versions.dataset.viewRevision, versions.value);
      const html = summaries.length ? summaries.slice().sort((a, b) => Number(b.revision) - Number(a.revision)).map((version) => `<option value="${Number(version.revision)}">v${Number(version.revision)} · ${esc(STATUS[version.status] || version.status || "")}${Number(version.revision) === Number(state.project.revision) ? " · 当前查看" : ""}</option>`).join("") : `<option value="">保存后查看版本</option>`;
      if (versions.innerHTML !== html) { versions.innerHTML = html; versions.value = summaries.some((version) => String(version.revision) === desired) ? desired : String(state.project?.revision || ""); }
      versions.dataset.project = state.project?.id || "";
      versions.dataset.viewRevision = String(state.project?.revision || "");
    }
    const previousDrafts = Object.values(state.pageDrafts).filter((draft) => draft.projectId === state.project?.id && Number(draft.revision) !== Number(state.project?.revision));
    setText("project-draft-note", previousDrafts.length ? `还有 ${previousDrafts.length} 页未保存草稿留在 ${[...new Set(previousDrafts.map((draft) => `v${draft.revision}`))].join("、")}，打开相应历史版本可恢复查看与复制。` : "单页编辑会在本机按商品、版本、页码暂存，切页或换品不会清除。");
    setText("project-status", [displayStatus(state), state.project ? `v${state.project.revision} · 指纹 ${String(state.project.fingerprint || "待生成").slice(0, 16)}` : "", state.error || errorText(state.project?.error) || state.notice, state.draftError, state.libraryError ? `商品库：${state.libraryError}` : ""].filter(Boolean).join(" · "));
    if ($("project-status")) $("project-status").dataset.status = state.error || state.dirty ? "warning" : state.project?.status || "draft";
    disabled("save-project-btn", state.historical || state.busy || state.pageEditorDirty || isRunning(state.project) && !state.dirty);
    disabled("load-project-btn", state.busy === "loading"); disabled("load-version-btn", !state.project || state.busy === "loading");
  }
  function renderReferences(state) {
    const node = $("reference-preview"); if (!node) return;
    const refs = app.references();
    const key = JSON.stringify([state.project?.id, state.project?.revision, state.referencesMode, refs.map((reference) => [reference.key, reference.name, reference.sha256, reference.role])]);
    if (key === previewKey) return;
    previewKey = key; previewUrls.forEach((url) => URL.revokeObjectURL(url)); previewUrls = [];
    node.innerHTML = refs.length ? refs.map((reference, index) => {
      let url;
      if (reference.file) { url = URL.createObjectURL(reference.file); previewUrls.push(url); }
      else url = safeImageUrl(reference.previewUrl) || `${API}/projects/${encodeURIComponent(state.project.id)}/references/${reference.index || index + 1}?revision=${state.project.revision}`;
      return `<div class="reference-thumb"><img src="${esc(url)}" alt="参考图${index + 1}：${esc(reference.name)}"><span>${index + 1}</span><em title="${esc(reference.name)}">${esc(reference.name)}</em><label class="reference-role" for="reference-role-${index}">用途<select id="reference-role-${index}" data-reference-index="${index}"${state.historical ? " disabled" : ""}>${Object.entries(ROLE_LABELS).map(([role, label]) => `<option value="${role}"${reference.role === role ? " selected" : ""}>${label}</option>`).join("")}</select></label></div>`;
    }).join("") + `<button class="text-btn reference-remove-btn" type="button" id="remove-references-btn"${state.historical ? " disabled" : ""}>清空当前参考图（保留已存档历史）</button>` : `<div class="reference-empty">尚未绑定当前商品参考图。可先生成文字 Prompt；真实生图前需上传并保存。</div>`;
    node.querySelectorAll("select[data-reference-index]").forEach((select) => select.addEventListener("change", () => app.setReferenceRole(Number(select.dataset.referenceIndex), select.value)));
    $("remove-references-btn")?.addEventListener("click", () => { if ($("reference-files")) $("reference-files").value = ""; app.setReferences([]); });
  }
  function renderPromptStatus(state) {
    const project = state.project, total = totalCount(state.form), ready = sortedPages(project).filter((page) => page.executionPrompt).length;
    setText("prompt-progress-label", `${displayStatus(state)} · ${ready} / ${Number.isFinite(total) ? total : "—"} 页${project?.progress?.stage ? ` · ${project.progress.stage}` : ""}`);
    const director = project?.director || {}, configuredDirector = state.directorConfig || {}, actualModel = actualDirectorModel(director), configuredModel = configuredDirector.model || state.config?.director?.model || "", requestedModel = director.requestedModel || director.model || configuredModel;
    setText("director-model-value", actualModel || requestedModel || (state.configError ? "无法读取配置" : "未配置"));
    setText("director-model-source", actualModel ? `此版本最近完成阶段实际模型${director.fallbackUsed ? " · 使用了备援模型" : ""}` : requestedModel ? "请求/配置模型；当前阶段尚未成功返回" : state.directorConfigError || state.configError || "请在此处配置 AI DIRECTOR 模型");
    setText("director-config-status", director.warning || state.directorConfigError || state.configError || (configuredModel ? `配置：${configuredModel}${configuredDirector.fallbackModels?.length ? ` · 备援：${configuredDirector.fallbackModels.join(" / ")}` : ""}。失败会保留错误与已完成页，不会自动套模板。` : "未配置 AI 分析模型；不能生成新 Prompt。"));
    $("director-model-display")?.classList.toggle("is-warning", Boolean(state.configError || state.directorConfigError || !actualModel && !configuredModel));
    setText("master-output-mode", state.dirty && project?.masterPrompt ? "输入已变更：以下为过期版本，仅供查看，复制与生图已禁用。" : project?.masterPrompt ? `AI 原创总控 · ${actualModel || "模型待确认"} · v${project.revision} · 指纹 ${String(project.fingerprint || "—").slice(0, 16)}` : "尚无 AI 总控。填写商品资料后生成；此处不会用固定模板替代。");
    if ($("master-output-mode")) $("master-output-mode").title = project?.fingerprint || "";
    setText("master-output", project?.masterPrompt || "当前商品还没有生成总控 Prompt。点击“AI 重新生成整套 Prompt”开始。");
    const unavailable = state.historical || state.busy || isRunning(project) && !state.dirty;
    disabled("generate-btn", unavailable); disabled("analyze-ai-btn", unavailable);
    hidden("resume-prompts-btn", !project || !["partial", "error", "cancelled"].includes(project.status));
    disabled("resume-prompts-btn", state.historical || state.dirty || state.busy || currentDrafts(state).length || state.pageEditorDirty);
    hidden("cancel-generation-btn", !state.busy && !isRunning(project));
    disabled("cancel-generation-btn", state.busy === "stopping" || state.busy === "loading"); hidden("local-draft-btn", true);
    disabled("copy-master-btn", !canUsePrompt(state)); disabled("copy-suite-btn", !suiteComplete(state)); disabled("download-btn", !suiteComplete(state));
    if ($("export-mode") && $("export-mode").value !== state.exportMode) $("export-mode").value = state.exportMode;
    setText("export-mode-help", state.exportMode === "standalone" ? "逐张独立版：每次复制一页，包含完整执行合同，直接粘贴到单张生图工具。" : state.project?.masterPrompt && !state.project.sharedExecutionRequirements ? "这是较早的存档，缺少共享要求快照；请选择逐张独立版，或生成新版本后使用整套规划。" : "整套规划版：总控与共享要求各一次，后接逐页创意，适合支持批处理的工作流；单张生图请复制当前页执行版。");
    disabled("copy-pages-btn", !canUsePrompt(state) || !visiblePages(project, state.filter).some((page) => page.executionPrompt));
    document.querySelectorAll(".small-copy-btn[data-copy-target]").forEach((button) => { button.disabled = !canUsePrompt(state); });
  }
  function renderPages(state) {
    const pages = sortedPages(state.project), list = $("page-list");
    if (list) {
      list.innerHTML = pages.length ? pages.map((page) => `<article class="page-card ${esc(page.section)}${Number(page.page) === state.selectedPage ? " selected" : ""}${page.executionPrompt ? "" : " is-pending"}" data-section="${esc(page.section)}" data-page="${Number(page.page)}" tabindex="0" role="button" aria-pressed="${Number(page.page) === state.selectedPage}" aria-label="选择${esc(pageLabel(page))}"${state.filter !== "all" && page.section !== state.filter ? " hidden" : ""}><div class="page-card-header"><span class="page-index">${String(page.page).padStart(2, "0")}</span><span class="page-kind${hasPageDraft(state, page.page) ? " has-draft" : ""}">${esc(pageLabel(page))} · ${hasPageDraft(state, page.page) ? "本地草稿" : page.executionPrompt ? "已就绪" : "待补齐"}</span></div><h3>${esc(page.title || "等待 AI 页面主题")}</h3><p>${esc(page.focus || page.objective || "")}</p>${page.headline ? `<code>${esc(page.headline)}</code>` : ""}</article>`).join("") : `<div class="analysis-empty"><strong>当前商品尚无分镜</strong><small>AI 会根据商品重新分配页面主题，不会套用上一件商品的固定页。</small></div>`;
      list.querySelectorAll(".page-card").forEach((card) => {
        const choose = () => app.selectPage(Number(card.dataset.page)); card.addEventListener("click", choose);
        card.addEventListener("keydown", (event) => { if (["Enter", " "].includes(event.key)) { event.preventDefault(); choose(); } });
      });
    }
    document.querySelectorAll(".page-filter-btn").forEach((button) => { button.classList.toggle("active", button.dataset.section === state.filter); button.setAttribute("aria-pressed", String(button.dataset.section === state.filter)); });
    const page = selectedPage(state);
    setText("selected-prompt-title", page ? `${pageLabel(page)} · ${page.title || "单页 Prompt"}${state.pageEditorDirty ? " · 尚未保存" : ""}` : "选择一页查看与编辑 Prompt");
    if ($("page-prompt-editor") && $("page-prompt-editor").value !== state.pageEditorValue) $("page-prompt-editor").value = state.pageEditorValue;
    disabled("page-prompt-editor", state.historical || !page?.modelPrompt || !snapshotFresh(state) || isRunning(state.project) || state.busy);
    setText("page-draft-status", state.draftError || (state.pageEditorDirty ? `${state.pageEditorSource === "restored" ? "已恢复" : "已暂存"}本机草稿 · ${state.project?.name || state.form.product} / v${state.project?.revision} / 第${state.selectedPage}页。${state.historical ? "历史版本草稿可复制，不能覆盖存档。" : "保存后才会更新实际执行 Prompt。"}` : page?.modelPrompt ? `显示服务器已保存的 v${state.project.revision}；本页当前没有未保存草稿。` : "选择已完成页后可编辑，修改自动暂存在本机。"));
    if ($("page-draft-status")) $("page-draft-status").dataset.dirty = String(state.pageEditorDirty);
    disabled("discard-page-draft-btn", !state.pageEditorDirty || state.busy); disabled("copy-page-draft-btn", !state.pageEditorDirty);
    setText("page-execution-output", page?.executionPrompt || "此页尚未生成完整执行 Prompt。保存的执行内容会原样用于复制、TXT 与实际生图。");
    disabled("save-page-prompt-btn", state.historical || !state.pageEditorDirty || !snapshotFresh(state) || isRunning(state.project) || state.busy);
    disabled("rewrite-page-btn", state.historical || !page || !snapshotFresh(state) || isRunning(state.project) || state.busy || currentDrafts(state).length || state.pageEditorDirty);
    disabled("copy-selected-page-btn", !canUsePrompt(state, page)); disabled("copy-execution-btn", !canUsePrompt(state, page)); setText("selected-page-label", pageLabel(page));
  }
  function renderHooks(state) {
    const board = $("copy-board"); if (!board) return;
    const hooks = Array.isArray(state.project?.hooks) ? state.project.hooks : [], labels = { pain: "痛点型", effect: "效果型", scene: "场景型" };
    board.innerHTML = hooks.length ? hooks.map((hook, index) => `<article class="copy-card"><small>HOOK ${String(index + 1).padStart(2, "0")} · 来源卖点</small><p>${esc(hook.source)}</p>${(hook.variants || []).filter((variant) => labels[variant.type]).map((variant) => `<div class="hook-variant"><small>${labels[variant.type]}</small><strong>${esc(variant.text)}</strong></div>`).join("")}${state.dirty ? `<small>输入已改动 · 此组文案已过期</small>` : ""}</article>`).join("") : `<div class="analysis-empty"><strong>等待当前商品的本土化钩子</strong><small>AI 将按真实卖点生成痛点型、效果型与场景型文案。这里不使用固定词库。</small></div>`;
  }
  function formatValue(value) { return value == null || value === "" ? "等待 AI 返回" : typeof value === "string" ? value : JSON.stringify(value, null, 2); }
  function analysisText(state) {
    if (!state.project) return "";
    const director = state.project.director || {};
    return [`商品：${state.project.name || state.form.product}`, `版本：${state.project.revision}`, `实际模型：${actualDirectorModel(director) || "尚未返回"}`, `状态：${STATUS[state.project.status] || state.project.status}`, `指纹：${state.project.fingerprint || "—"}`, `分析：${JSON.stringify(director, null, 2)}`, `页面规划：${JSON.stringify(state.project.outline || [], null, 2)}`].join("\n");
  }
  function renderAnalysis(state) {
    const director = state.project?.director || {};
    setText("analysis-meta", state.project ? `v${state.project.revision} · ${actualDirectorModel(director) || "模型未成功返回"} · ${STATUS[state.project.status] || state.project.status}${state.dirty ? " · 输入已修改" : ""}` : "尚未运行当前商品分析");
    const summary = $("analysis-summary");
    if (summary) summary.innerHTML = state.project && (state.project.masterPrompt || Object.keys(director).length) ? `<article class="analysis-summary-card wide"><span>PRODUCT SUMMARY</span><strong>${esc(state.project.productSummary || director.productSummary || state.project.name || "等待分析结果")}</strong>${state.project.error ? `<p class="analysis-warning">${esc(errorText(state.project.error))}</p>` : ""}</article><article class="analysis-summary-card"><span>VISUAL DNA</span><p>${esc(formatValue(state.project.visualDNA || director.productVisualDNA))}</p></article><article class="analysis-summary-card"><span>SELLING-POINT COVERAGE</span><p>${esc(formatValue(director.sellingPointCoverage || state.project.outline?.map((page) => `${pageLabel(page)}：${page.focus || page.title || ""}`)))}</p></article>` : `<div class="analysis-empty"><strong>分析当前商品，而非固定套版</strong><small>生成后显示实际模型、视觉方向、卖点覆盖与页面顺序；失败会保留真实错误。</small></div>`;
    if ($("analysis-page-list")) $("analysis-page-list").innerHTML = sortedPages(state.project).map((page) => `<article class="analysis-page-card"><header><span>${String(page.page).padStart(2, "0")}</span><span>${esc(pageLabel(page))}</span></header><strong>${esc(page.title || "待生成")}</strong><p>${esc(page.focus || page.objective || "")}</p><code>${esc(page.headline || "")}</code></article>`).join("");
    disabled("copy-analysis-btn", !canUsePrompt(state));
  }
  function renderQuality(state) {
    const report = state.project?.qualityReport, issues = Array.isArray(report?.issues) ? report.issues : [];
    const source = report?.source === "ai" ? "AI 辅助检查" : "本地规则检查";
    const busy = isRunning(state.project) || state.busy, ready = canUsePrompt(state);
    setText("quality-badge", report ? `${source} · ${report.status === "reviewing" ? "检查中" : report.status === "error" ? "未完整完成" : issues.length ? `${issues.length} 项建议` : "未发现已检查类型的问题"}` : "尚未检查");
    setText("quality-summary", report?.summary || "检查重复钩子、卖点对应、页面重复与语言信号。先运行无模型费用的规则检查，需要时再选择 AI 检查。");
    setText("quality-limits", report?.source === "ai" ? "AI 意见仍可能遗漏或误判，不是母语人工审校或功效认证。检查建议不会自动禁止复制或生图。" : "规则只能识别结构和文本信号，不能判断日文是否地道或画面最终质量。检查建议不会自动禁止复制或生图。");
    setText("quality-meta", report ? `当前 v${state.project.revision} · ${report.checkedAt || "等待结果"}${report.director?.activeModel ? ` · 实际检查模型：${report.director.activeModel}` : ""}${report.status === "reviewing" && report.reviewTotal ? ` · 已检查 ${report.reviewCompleted || 0}/${report.reviewTotal} 页` : ""}${report.requiresFullRegeneration ? " · 存在整套层面问题，请重新生成整套后检查" : ""}` : "");
    setText("quality-error", errorText(report?.error)); hidden("quality-error", !report?.error);
    disabled("review-rules-btn", !ready || busy); disabled("review-ai-btn", !ready || busy);
    const repairable = (report?.repairablePages?.length || 0) + (report?.repairableHookSources?.length || 0);
    disabled("repair-quality-btn", !ready || busy || state.historical || !repairable || report?.requiresFullRegeneration);
    const list = $("quality-issues");
    if (list) {
      list.innerHTML = issues.map((issue) => `<article class="quality-issue"><div class="quality-issue-heading"><span>${issue.severity === "info" ? "建议" : "需留意"} · ${esc(issue.code || "内容检查")}</span>${Number(issue.page) > 0 ? `<button class="small-copy-btn" type="button" data-quality-page="${Number(issue.page)}">查看第 ${Number(issue.page)} 页</button>` : `<span>${issue.field === "hooks" || issue.field?.startsWith("hooks") ? "钩子文案" : "整套内容"}</span>`}</div><p>${esc(issue.message || "请结合原始卖点检查此内容。")}</p>${issue.field ? `<small>检查字段：${esc(issue.field)}</small>` : ""}</article>`).join("");
      list.querySelectorAll("[data-quality-page]").forEach((button) => button.addEventListener("click", () => { app.setFilter("all"); app.selectPage(Number(button.dataset.qualityPage)); selectTab("pages"); $("selected-prompt-title")?.scrollIntoView({ block: "nearest" }); }));
    }
  }
  function renderGallery(state) {
    const entries = materialEntries(state.project).sort((a, b) => a[0] - b[0]); setText("result-tab-count", entries.length);
    const gallery = $("generated-gallery"); if (!gallery) return;
    const errors = state.rendering?.errors || [];
    gallery.innerHTML = (errors.length ? `<div class="generation-error">${errors.map((error) => `第${error.page}页：${esc(error.message)}`).join("<br>")}</div>` : "") + (!entries.length || state.hiddenGallery ? `<div class="gallery-empty"><span>○</span><strong>${state.hiddenGallery ? "已暂时收起成图" : "当前版本尚无成图"}</strong><small>${state.hiddenGallery ? "服务器存档未删除，点击显示可恢复。" : "完成提示词并绑定当前商品图后，可逐页或整套生成。"}</small></div>` : entries.map(([pageNumber, material]) => {
      const url = safeImageUrl(material.assetUrl || material.previewUrl || material.previewDataUrl || material.remoteUrl || material.url), downloadUrl = safeImageUrl(material.downloadUrl) || url, page = sortedPages(state.project).find((item) => Number(item.page) === pageNumber);
      const permanent = material.archiveStatus === "archived" || material.storage === "project-permanent", originRevision = Number(material.originRevision || material.revision || state.project.revision);
      return `<article class="generated-card">${url ? `<a href="${esc(url)}" target="_blank" rel="noopener"><img src="${esc(url)}" alt="${esc(pageLabel(page))}，生成自v${originRevision}" loading="lazy"></a>` : `<p>图片记录已保留，预览暂不可用</p>`}<div class="generated-meta"><div><strong>${esc(pageLabel(page))} · 生成自 v${originRevision}</strong><small>${esc(page?.title || material.name || "AI 成图")}${originRevision !== Number(state.project.revision) ? ` · 当前查看 v${state.project.revision} 沿用` : ""}${state.dirty ? " · 旧版成图" : ""}</small><small class="asset-status${permanent ? " permanent" : ""}">${permanent ? "已长期保存在本机项目" : "仅历史链接 · 尚未长期保存"}${material.archiveError ? `：${esc(errorText(material.archiveError))}` : ""}</small></div>${downloadUrl ? `<a class="generated-download" href="${esc(downloadUrl)}" target="_blank" rel="noopener" download>保存</a>` : ""}</div></article>`;
    }).join(""));
    setText("clear-results-btn", state.hiddenGallery ? "显示已存档成图" : "暂时收起成图");
    disabled("archive-images-btn", !entries.length || state.queueBusy);
    const zip = $("download-images-btn"); if (zip) { zip.href = state.project ? `${API}/projects/${encodeURIComponent(state.project.id)}/images.zip?revision=${state.project.revision}` : "#"; zip.setAttribute("aria-disabled", String(!entries.length)); }
  }
  function renderImageStatus(state) {
    const rendering = state.rendering, total = rendering?.total || totalCount(state.form), complete = rendering?.completed ?? new Set(materialEntries(state.project).map(([page]) => page)).size;
    setText("generation-status", state.queueBusy ? "正在提交后台队列操作" : rendering ? `${QUEUE_STATUS[rendering.status] || rendering.status} · v${rendering.revision}${rendering.active ? ` / 第 ${rendering.active} 页` : ""}` : state.dirty && state.project ? "旧版图片保留 · 等待新 Prompt" : materialEntries(state.project).length ? "成图已存档" : "等待当前商品 Prompt 与参考图");
    setText("generation-detail", rendering?.status === "needs_attention" ? "存在提交结果不明的任务。请先核实供应商结果，系统不会自动重提并重复计费。" : "后台队列随本地服务运行，关闭本网页或切换商品不影响队列；关闭本地服务会中断运行，重开后可恢复尚未提交页。已完成与进行中任务会复用。");
    setText("queue-error", state.queueError || errorText(rendering?.error)); hidden("queue-error", !(state.queueError || rendering?.error));
    setText("queue-settings", rendering ? `此轮设置：${rendering.settings?.model || "默认模型"} / ${rendering.settings?.quality || "默认质量"} / ${rendering.settings?.generationProfile || "默认策略"}。修改上方设置只影响新提交，不改变已保存队列。` : "生成与继续不会重画已有页；需要新图时使用“重新生成”，并明确确认可能计费。");
    setText("generation-count", `${complete} / ${Number.isFinite(total) ? total : "—"}`);
    if ($("generation-progress-bar")) $("generation-progress-bar").style.width = `${total ? Math.min(100, Math.round(complete / total * 100)) : 0}%`;
    const ready = canUsePrompt(state, selectedPage(state)) && app.references().length && !state.queueBusy;
    disabled("generate-current-btn", !ready); disabled("generate-suite-btn", !ready || !suiteComplete(state)); disabled("retry-failed-btn", !ready || !rendering?.errors?.length || rendering.running); hidden("retry-failed-btn", !rendering?.errors?.length);
    disabled("redo-current-btn", !ready || rendering?.running); disabled("refresh-queues-btn", !state.project || state.queueBusy);
    disabled("resume-image-queue-btn", !rendering || rendering.running || state.queueBusy || !["paused", "partial", "error"].includes(rendering.status));
    hidden("resume-image-queue-btn", !rendering || !["paused", "partial", "error"].includes(rendering.status));
    disabled("cancel-image-queue-btn", !rendering?.running || state.queueBusy); hidden("cancel-image-queue-btn", !rendering?.running);
    hidden("redo-confirmation", !state.redoConfirmation);
    setText("redo-confirmation-text", state.redoConfirmation ? `确认重生成第 ${state.redoConfirmation.pageNumbers.join("、")} 页？这会创建新的生图任务，可能再次计费；旧图不会删除。` : "");
    disabled("confirm-redo-btn", state.queueBusy);
    const select = $("image-queue-select");
    if (select) { const html = state.queues.length ? state.queues.map((queue) => `<option value="${esc(queue.id)}">${esc(QUEUE_STATUS[queue.status] || queue.status)} · ${Number(queue.completed ?? queue.counts?.completed ?? 0)}/${Number(queue.total ?? queue.counts?.total ?? queue.pages?.length ?? 0)}页 · ${esc(queue.settings?.quality || "默认质量")} · ${esc(String(queue.id).slice(-8))}</option>`).join("") : `<option value="">此版本尚无后台队列</option>`; if (select.innerHTML !== html) select.innerHTML = html; select.value = state.queueId; }
    const queuePages = $("image-queue-pages"); if (queuePages) queuePages.innerHTML = (rendering?.pages || []).map((page) => `<span class="queue-page-state" data-status="${esc(page.status)}" title="${esc(errorText(page.error) || page.jobId || page.status)}">${Number(page.page)} · ${esc({ queued: "待提交", waiting: "待提交", pending: "处理中", submitted: "已提交", running: "处理中", complete: "完成", completed: "完成", failed: "失败", error: "失败", skipped: "已复用", cancelled: "已暂停", needs_attention: "待核实" }[page.status] || page.status)}</span>`).join("");
    const countSpan = $("generate-suite-btn")?.querySelector("span"); if (countSpan) countSpan.textContent = `${state.form.main} + ${state.form.detail}`;
  }
  function render(state) {
    if (!uiReady) return;
    writeForm(state.form);
    const market = MARKET[state.form.market] || { label: state.form.market, language: "当地语言" };
    setText("output-title", state.form.product ? `${state.form.product} · ${market.label} COD 套图` : "新商品 · 专属 AI Prompt");
    setText("stat-total", Number.isFinite(totalCount(state.form)) ? totalCount(state.form) : "—"); setText("stat-hooks", state.form.points.length); setText("stat-locale", state.form.market); setText("stat-locale-label", `${market.language}可见文案`); setText("stat-ratio", ratioLabel(state.form.size)); setText("stat-size-label", state.form.size.replace(/[x×]/i, " × "));
    setText("all-count", totalCount(state.form)); setText("main-count-label", state.form.main); setText("detail-count-label", state.form.detail); setText("pages-tab-label", `${totalCount(state.form)}页分镜`); setText("copy-tab-label", `${market.language}钩子文案`);
    renderProjectControls(state); renderReferences(state); renderPages(state); renderPromptStatus(state); renderHooks(state); renderAnalysis(state); renderQuality(state); renderGallery(state); renderImageStatus(state); saveDraft(state);
  }
  async function copyText(value) {
    if (navigator.clipboard?.writeText) return navigator.clipboard.writeText(value);
    const area = document.createElement("textarea"); area.value = value; document.body.appendChild(area); area.select();
    const copied = document.execCommand("copy"); area.remove(); if (!copied) throw new Error("浏览器未允许复制，请手动选择 Prompt 复制。");
  }
  async function guardedCopy(kind) {
    try {
      const state = app.state; let text;
      if (kind === "suite") text = fullPack(state);
      else if (kind === "draft") text = state.pageEditorDirty ? state.pageEditorValue : "";
      else {
        const page = selectedPage(state);
        if (!canUsePrompt(state, kind === "page" ? page : null)) throw new Error("当前 Prompt 已过期、未保存或未完成，不能复制。");
        if (kind === "master") text = state.project.masterPrompt;
        else if (kind === "page") text = page.executionPrompt;
        else if (kind === "analysis") text = analysisText(state);
        else text = visiblePages(state.project, state.filter).filter((item) => item.executionPrompt).map((item) => `===== ${pageLabel(item)} =====\n${item.executionPrompt}`).join("\n\n");
      }
      if (!text) throw new Error("当前列表没有已完成的 Prompt。");
      await copyText(text); toast(kind === "suite" ? `已复制${state.exportMode === "standalone" ? "逐张独立版" : "整套导入版"} Prompt。` : kind === "draft" ? "已复制本地未保存草稿；这不是已保存执行版。" : "已复制当前版本内容。");
    } catch (error) { toast(error.message); }
  }
  function downloadPack() {
    try {
      const state = app.state, body = fullPack(state), url = URL.createObjectURL(new Blob([body], { type: "text/plain;charset=utf-8" })), link = document.createElement("a");
      link.href = url; link.download = `${state.form.product.replace(/[<>:"/\\|?*]+/g, "-")}-v${state.project.revision}-${state.exportMode === "standalone" ? "逐张独立版" : "整套导入版"}.txt`; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (error) { toast(error.message); }
  }
  function selectTab(name) {
    document.querySelectorAll(".output-tab").forEach((tab) => { tab.classList.toggle("active", tab.dataset.tab === name); tab.setAttribute("aria-selected", String(tab.dataset.tab === name)); });
    document.querySelectorAll(".tab-content").forEach((content) => content.classList.toggle("active", content.id === `tab-${name}`));
  }
  const AI_DIRECTOR_MODEL_PRESETS = ["deepseek-v4.1-flash", "gpt-5.6-terra", "gpt-5.6-sol", "gemini-3-flash-agent", "claude-sonnet-4-6"];
  function directorModelOptions(director = {}) {
    return Array.from(new Set([
      ...AI_DIRECTOR_MODEL_PRESETS,
      ...(Array.isArray(director.availableModels) ? director.availableModels : []),
      ...(Array.isArray(director.customModels) ? director.customModels : []),
      director.model,
    ].filter((model) => typeof model === "string" && model.trim()).map((model) => model.trim())));
  }
  function renderDirectorSettings() {
    if (!app) return;
    const director = app.state.directorConfig || {}, select = $("cod-director-model"), dirty = Boolean(director.formDirty);
    if (select) {
      const selected = dirty ? (select.value || director.model || AI_DIRECTOR_MODEL_PRESETS[0]) : (director.model || AI_DIRECTOR_MODEL_PRESETS[0]);
      select.innerHTML = directorModelOptions(director).map((model) => `<option value="${esc(model)}">${esc(model)}</option>`).join("");
      select.value = directorModelOptions(director).includes(selected) ? selected : (director.model || AI_DIRECTOR_MODEL_PRESETS[0]);
    }
    if (!dirty) {
      if ($("cod-director-base-url")) $("cod-director-base-url").value = director.baseUrl || "";
      if ($("cod-director-timeout")) $("cod-director-timeout").value = String(director.timeout || 60);
      if ($("cod-director-api-key")) {
        $("cod-director-api-key").value = "";
        $("cod-director-api-key").placeholder = director.apiKeyConfigured ? "已保存密钥，留空则保持不变" : "输入 API 密钥";
      }
      if ($("cod-director-enabled")) $("cod-director-enabled").checked = Boolean(director.enabled);
      if ($("cod-director-vision")) $("cod-director-vision").checked = director.visionEnabled !== false;
    }
    const configured = Boolean(director.configured), active = configured && Boolean(director.enabled), stateEl = $("cod-director-config-state");
    if (stateEl) stateEl.textContent = director.loading ? "读取中" : director.testing ? "检测中" : director.saving ? "保存中" : active ? `${director.model || "已配置"} · 已启用` : configured ? "已配置 · 未启用" : "未配置";
    const currentModel = $("cod-director-current-model");
    if (currentModel) currentModel.textContent = director.model || (select?.value || "—");
    const message = $("cod-director-settings-message");
    if (message) {
      message.className = director.status === "error" ? "error" : director.status === "ok" ? "ok" : "";
      message.textContent = director.message || (director.baseUrl && !director.secureTransport ? "当前 API 使用 HTTP，密钥传输未加密；密钥仅保存在服务端。" : "使用视频提示词面板同款的模型选项和 OpenAI 兼容配置格式；这里的模型负责分析商品和生成生图 Prompt，实际图片仍使用下方生图模型。");
    }
    const busy = Boolean(director.loading || director.testing || director.saving);
    disabled("cod-director-save-btn", busy);
    disabled("cod-director-test-btn", busy || !configured && !dirty);
    disabled("cod-director-add-model-btn", busy);
    disabled("cod-director-custom-model-input", busy);
  }
  function markDirectorDirty() {
    if (!app) return;
    const current = app.state.directorConfig || {};
    app.state.directorConfig = { ...current, formDirty: true, status: "unknown", message: "有未保存的模型配置修改" };
    renderDirectorSettings(); app.emit();
  }
  function addCodDirectorCustomModel() {
    const director = app?.state.directorConfig || {}, input = $("cod-director-custom-model-input"), model = input?.value.trim() || "";
    if (!model || model.length > 120 || /[\s\x00-\x1f\x7f]/u.test(model)) { toast("请输入 1–120 个字符的完整模型 ID，去除空格、换行和控制字符"); input?.focus(); return; }
    const customModels = Array.from(new Set([...(Array.isArray(director.customModels) ? director.customModels : []), director.model, model].filter((candidate) => candidate && !AI_DIRECTOR_MODEL_PRESETS.includes(candidate))));
    if (customModels.length > 50) { toast("自定义模型最多保存 50 个"); return; }
    app.state.directorConfig = { ...director, model, customModels, formDirty: true, status: "unknown", message: `已选用 ${model}，点击“保存配置”后生效。` };
    if (input) input.value = "";
    renderDirectorSettings(); app.emit(); toast("已添加并选用，请点击保存配置");
  }
  function directorSettingsFormPayload() {
    const director = app?.state.directorConfig || {}, model = $("cod-director-model")?.value.trim() || director.model || "";
    const fallbacks = Array.from(new Set(Array.isArray(director.fallbackModels) ? director.fallbackModels : ["gpt-5.6-terra", "gpt-5.6-sol"])).filter((candidate) => candidate && candidate !== model);
    return {
      enabled: Boolean($("cod-director-enabled")?.checked), baseUrl: $("cod-director-base-url")?.value.trim() || "", model,
      customModels: Array.isArray(director.customModels) ? [...director.customModels] : [], fallbackModels: fallbacks,
      apiKey: $("cod-director-api-key")?.value.trim() || "", timeout: Number($("cod-director-timeout")?.value || 60),
      visionEnabled: Boolean($("cod-director-vision")?.checked), openImagePromptsEnabled: director.openImagePromptsEnabled !== false,
      reviewEnabled: false,
    };
  }
  async function loadDirectorConfig(silent = true) {
    if (!app) return null;
    const existing = app.state.directorConfig || {};
    app.state.directorConfig = { ...existing, loading: true };
    renderDirectorSettings();
    try {
      const payload = await apiRequest("/api/sku-board/ai-director-settings");
      const keepDirty = Boolean(app.state.directorConfig?.formDirty);
      app.state.directorConfig = keepDirty ? { ...app.state.directorConfig, loading: false } : { ...(payload.director || {}), loading: false, status: "unknown", message: "", formDirty: false };
      app.state.directorConfigError = "";
      renderDirectorSettings(); app.emit();
      if (!silent && !keepDirty) toast(app.state.directorConfig.configured ? "AI DIRECTOR 配置已加载" : "AI DIRECTOR 尚未配置");
      return app.state.directorConfig;
    } catch (error) {
      app.state.directorConfig = { ...app.state.directorConfig, loading: false, status: "error", message: error.message };
      app.state.directorConfigError = error.message; renderDirectorSettings(); app.emit();
      if (!silent) toast(error.message);
      return null;
    }
  }
  async function saveDirectorConfig() {
    const director = app?.state.directorConfig || {};
    if (!director.formDirty && director.configured) { toast("当前模型配置已保存"); return director; }
    app.state.directorConfig = { ...director, saving: true, message: "正在保存 AI DIRECTOR 配置…" }; renderDirectorSettings();
    try {
      const payload = await apiRequest("/api/sku-board/ai-director-settings", { method: "POST", json: directorSettingsFormPayload() });
      app.state.directorConfig = { ...(payload.director || {}), saving: false, status: "ok", message: `配置已生效：${payload.director?.model || "当前模型"}`, formDirty: false };
      app.state.directorConfigError = ""; renderDirectorSettings(); app.emit(); toast(app.state.directorConfig.message); return app.state.directorConfig;
    } catch (error) {
      app.state.directorConfig = { ...app.state.directorConfig, saving: false, status: "error", message: error.message, formDirty: true }; renderDirectorSettings(); app.emit(); toast(error.message); return null;
    }
  }
  async function testDirectorConfig() {
    if (!app) return;
    if (app.state.directorConfig?.formDirty && !await saveDirectorConfig()) return;
    app.state.directorConfig = { ...(app.state.directorConfig || {}), testing: true, message: "正在连接 AI DIRECTOR 模型…" }; renderDirectorSettings();
    try {
      const payload = await apiRequest("/api/sku-board/ai-director-test", { method: "POST", json: {} });
      app.state.directorConfig = { ...(payload.director || {}), testing: false, status: "ok", message: `${payload.director?.message || "AI DIRECTOR 连接正常"}${payload.director?.latencyMs ? ` · ${payload.director.latencyMs}ms` : ""}`, formDirty: false };
      renderDirectorSettings(); app.emit(); toast(app.state.directorConfig.message);
    } catch (error) {
      app.state.directorConfig = { ...(app.state.directorConfig || {}), testing: false, status: "error", message: error.message }; renderDirectorSettings(); app.emit(); toast(error.message);
    }
  }
  async function loadConfig() {
    try {
      const payload = await apiRequest("/api/sku-board/ai-image-config"), config = payload.aiImage || {};
      app.state.config = config; app.state.configError = "";
      const preference = app.state.form, labels = { "gpt-image-2": "GPT Image 2", "codex-gpt-image-2": "Codex GPT Image 2", auto: "自动", high: "高质", medium: "平衡", low: "低质" };
      [["render-model", config.models, preference.model, "model"], ["render-quality", config.qualities, preference.quality, "quality"]].forEach(([id, values, currentValue, key]) => {
        if (!$(id) || !Array.isArray(values) || !values.length) return;
        const options = [...new Set([...values, currentValue].filter(Boolean).map(String))];
        $(id).innerHTML = options.map((value) => `<option value="${esc(value)}">${esc(labels[value] || value)}</option>`).join(""); $(id).value = currentValue || config[key] || options[0];
      });
      const nodes = Number(config.nodeCount || config.nodes?.length || 0);
      setText("model-config-status", config.enabled && nodes ? `服务器已配置 ${nodes} 个生图节点。所选模型、质量和策略不会重新改写提示词。` : "尚未检测到可用生图节点；已生成的文字 Prompt 仍可复制导出。");
    } catch (error) { app.state.configError = error.message; setText("model-config-status", error.message); }
    app.emit();
  }
  function bindUI() {
    Object.values(FIELDS).forEach((id) => { const input = $(id); if (input) input.addEventListener(input.type === "checkbox" || input.tagName === "SELECT" ? "change" : "input", () => app.updateForm(readForm())); });
    const click = (id, handler) => $(id)?.addEventListener("click", handler);
    ["cod-director-model", "cod-director-base-url", "cod-director-timeout", "cod-director-api-key", "cod-director-enabled", "cod-director-vision"].forEach((id) => {
      const input = $(id); if (input) input.addEventListener(input.type === "checkbox" || input.tagName === "SELECT" ? "change" : "input", markDirectorDirty);
    });
    click("cod-director-add-model-btn", addCodDirectorCustomModel); click("cod-director-read-btn", () => void loadDirectorConfig(false)); click("cod-director-save-btn", () => void saveDirectorConfig()); click("cod-director-test-btn", () => void testDirectorConfig());
    $("cod-director-custom-model-input")?.addEventListener("keydown", (event) => { if (event.key === "Enter") { event.preventDefault(); if (!event.isComposing) addCodDirectorCustomModel(); } });
    click("new-product-btn", () => app.newProduct()); click("reset-btn", () => app.newProduct()); click("save-project-btn", () => app.saveProject());
    click("load-project-btn", () => app.openProject($("project-select")?.value)); click("load-version-btn", () => app.openProject(app.state.project?.id, Number($("project-version")?.value)));
    click("generate-btn", () => { selectTab("master"); void app.generate("fresh"); }); click("analyze-ai-btn", () => { selectTab("master"); void app.generate("fresh"); }); click("resume-prompts-btn", () => app.generate("resume")); click("cancel-generation-btn", () => app.stop());
    [["copy-master-btn", "master"], ["copy-suite-btn", "suite"], ["copy-pages-btn", "pages"], ["copy-analysis-btn", "analysis"], ["copy-selected-page-btn", "page"], ["copy-execution-btn", "page"]].forEach(([id, kind]) => click(id, () => guardedCopy(kind)));
    $("export-mode")?.addEventListener("change", (event) => { app.state.exportMode = event.target.value === "standalone" ? "standalone" : "compact"; app.emit(); });
    click("download-btn", downloadPack); click("save-page-prompt-btn", () => app.savePage($("page-prompt-editor")?.value || "")); click("rewrite-page-btn", () => app.generate("page", $("page-rewrite-notes")?.value || "")); $("page-prompt-editor")?.addEventListener("input", (event) => app.setPageEditor(event.target.value));
    click("discard-page-draft-btn", () => app.discardPageDraft()); click("copy-page-draft-btn", () => guardedCopy("draft"));
    click("review-rules-btn", () => app.review("rules")); click("review-ai-btn", () => app.review("ai")); click("repair-quality-btn", () => app.generate("repair"));
    click("generate-current-btn", () => { selectTab("results"); void app.renderImages("current"); }); click("generate-suite-btn", () => { selectTab("results"); void app.renderImages("suite"); }); click("retry-failed-btn", () => app.renderImages("retry")); click("clear-results-btn", () => { app.state.hiddenGallery = !app.state.hiddenGallery; app.emit(); });
    click("redo-current-btn", () => app.requestRedo("current")); click("confirm-redo-btn", () => app.confirmRedo()); click("dismiss-redo-btn", () => { app.state.redoConfirmation = null; app.emit(); });
    click("refresh-queues-btn", () => app.refreshQueues()); click("resume-image-queue-btn", () => app.queueAction("resume")); click("cancel-image-queue-btn", () => app.queueAction("cancel"));
    $("image-queue-select")?.addEventListener("change", (event) => app.selectQueue(event.target.value));
    click("archive-images-btn", () => app.archiveImages()); $("download-images-btn")?.addEventListener("click", (event) => { if (!materialEntries(app.state.project).length) event.preventDefault(); });
    document.querySelectorAll(".small-copy-btn[data-copy-target]").forEach((button) => button.addEventListener("click", () => guardedCopy("master")));
    document.querySelectorAll(".page-filter-btn").forEach((button) => button.addEventListener("click", () => app.setFilter(button.dataset.section)));
    document.querySelectorAll(".output-tab").forEach((tab) => tab.addEventListener("click", () => selectTab(tab.dataset.tab)));
    const files = $("reference-files"), dropzone = document.querySelector(".upload-dropzone");
    const acceptFiles = (list) => {
      const all = Array.from(list || []), accepted = all.filter((file) => ["image/jpeg", "image/png", "image/webp"].includes(file.type));
      if (all.length !== accepted.length) toast("仅支持 JPG、PNG 与 WEBP，其它文件已忽略。");
      if (accepted.length > 12) toast("最多绑定 12 张参考图，本次使用前 12 张。");
      if (accepted.length) app.setReferences(accepted);
    };
    files?.addEventListener("change", () => { acceptFiles(files.files); files.value = ""; });
    dropzone?.addEventListener("dragover", (event) => { event.preventDefault(); dropzone.classList.add("dragover"); }); dropzone?.addEventListener("dragleave", () => dropzone.classList.remove("dragover")); dropzone?.addEventListener("drop", (event) => { event.preventDefault(); dropzone.classList.remove("dragover"); acceptFiles(event.dataTransfer.files); });
    window.addEventListener("beforeunload", (event) => { if (app.state.referencesMode === "replace" && app.state.localReferences.length || app.state.draftError && Object.keys(app.state.pageDrafts).length) { event.preventDefault(); event.returnValue = ""; } });
  }
  document.addEventListener("DOMContentLoaded", async () => {
    const stored = readDraft(); let pageStorage;
    try { pageStorage = localStorage; } catch (_) { pageStorage = { getItem: () => "{}", setItem: () => { throw new Error("unavailable"); } }; }
    app = createController({ request: apiRequest, notify: toast, changed: render, initialForm: stored.form, draftStorage: pageStorage }); app.state.dirty = Boolean(stored.dirty);
    app.state.selectedPage = Math.max(1, Number(stored.selectedPage) || 1); app.state.exportMode = stored.exportMode === "compact" ? "compact" : "standalone";
    if (stored.legacy) app.state.notice = "已迁移之前保存的文字输入。旧模板结果未继承，请重新生成当前商品 AI Prompt。";
    uiReady = true; bindUI(); app.emit();
    const initialToken = app.state.token;
    const configPromise = Promise.all([loadConfig(), loadDirectorConfig()]); await app.listProjects();
    if (stored.projectId && app.state.token === initialToken) await app.openProject(stored.projectId, stored.historical ? stored.revision : null, { draft: stored });
    await configPromise; restoringDraft = false; app.emit();
  });
})();
