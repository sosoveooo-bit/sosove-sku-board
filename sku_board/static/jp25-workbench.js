/* JP25-only planning controls. Pure helpers also run in the offline contract tests. */
const JP25Workbench = (() => {
  const active = (c) => c?.suiteKey === "jp-landing-page-25";
  const globalFields = { productNotes: 2000, identityNotes: 1200, styleNotes: 1600 };
  const pageFields = { headline: 160, scene: 700, goal: 700 };
  const drafts = new Map();
  const reports = new Map();
  const html = (v) => String(v ?? "").replace(/[&<>"']/g, s => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[s]));
  const readable = (v) => Array.isArray(v) ? v.map(readable).filter(Boolean).join("；")
    : v && typeof v === "object" ? readable(v.claim || v.description || v.summary || Object.values(v)) : String(v || "");
  function normalize(value = {}) {
    const out = {};
    for (const [key, max] of Object.entries(globalFields)) {
      const text = String(value[key] || "").trim();
      if (text.length > max) throw new Error(`锁定说明过长，最多 ${max} 字符`);
      if (text) out[key] = text;
    }
    for (let page = 1; page <= 25; page++) {
      const raw = value.pages?.[page] || {}, item = {};
      for (const [key, max] of Object.entries(pageFields)) {
        const text = String(raw[key] || "").trim();
        if (text.length > max) throw new Error(`第 ${page} 页调整过长，最多 ${max} 字符`);
        if (text) item[key] = text;
      }
      if (raw.textFree === true) item.textFree = true;
      if (Object.keys(item).length) (out.pages ||= {})[page] = item;
    }
    return out;
  }
  const globals = (c) => Object.fromEntries(Object.entries(normalize(c.jp25Workbench)).filter(([k]) => k !== "pages"));
  function fingerprint(value) {
    const text = JSON.stringify(value);
    let a = 2166136261, b = 3339675911;
    for (let i = 0; i < text.length; i++) {
      a = Math.imul(a ^ text.charCodeAt(i), 16777619);
      b = Math.imul(b ^ text.charCodeAt(i), 2246822519);
    }
    return [a, b].map(n => (n >>> 0).toString(16).padStart(8, "0")).join("");
  }
  const revision = (c, page) => fingerprint([c.suitePlanSignature, c.suitePlanVersion, c.jp25PlanEpoch || "",
    c.model, c.quality, globals(c), normalize(c.jp25Workbench).pages?.[page] || {}]);
  const current = (c, m) => Boolean(m?.jp25Revision && m.jp25Revision === revision(c, Number(m.suitePage)));
  const remaining = (c) => Array.from({ length: 25 }, (_, i) => i + 1)
    .filter(n => !(c.materials || []).some(m => Number(m.suitePage) === n && current(c, m)));
  function samples(c) {
    const pages = (c.suitePages || []).filter(p => Number(p.page) >= 1 && Number(p.page) <= 25);
    const text = p => readable([p.role, p.title, p.focusSlot, p.focus, p.objective, p.scene, p.shotType, p.visualEnhancement?.shotConcept]);
    const chosen = [];
    const pick = (match) => {
      const p = pages.find(p => !chosen.includes(Number(p.page)) && match(p)) || pages.find(p => !chosen.includes(Number(p.page)));
      if (p) chosen.push(Number(p.page));
    };
    pick(p => /full.body|全身|全体|head.to.toe/i.test(text(p)));
    pick(p => /macro|close.up|detail|特写|细节|細部|接写/i.test(text(p)));
    pick(p => !c.jp25Workbench?.pages?.[p.page]?.textFree && p.textPolicy !== "none"
      && Boolean(c.jp25Workbench?.pages?.[p.page]?.headline || p.headline || p.localizedSellingPointTitle));
    return chosen;
  }
  function adoptLegacy(c) {
    // Establish the current baseline once, before edits. Do not adopt unsigned images after an edit.
    if (c.jp25BaselineAdopted || Object.keys(normalize(c.jp25Workbench)).length) return;
    for (const m of c.materials || []) if (!m.jp25Revision) m.jp25Revision = revision(c, Number(m.suitePage));
    c.jp25BaselineAdopted = true;
  }
  function readDraft(c, root) {
    const value = structuredClone(drafts.get(c.id) || c.jp25Workbench || {});
    for (const input of root.querySelectorAll("[data-jp25-field]")) {
      const page = input.dataset.jp25Page;
      const target = page ? ((value.pages ||= {})[page] ||= {}) : value;
      target[input.dataset.jp25Field] = input.type === "checkbox" ? input.checked : input.value;
    }
    const normalized = normalize(value);
    drafts.set(c.id, normalized);
    return normalized;
  }
  function save(c, root) {
    adoptLegacy(c);
    const value = root ? readDraft(c, root) : drafts.get(c.id) || c.jp25Workbench || {};
    const changed = JSON.stringify(normalize(value)) !== JSON.stringify(normalize(c.jp25Workbench));
    c.jp25Workbench = normalize(value);
    drafts.delete(c.id);
    if (changed) c.jp25Report = null;
    return changed;
  }
  function deduplicate(rows) {
    const byHash = new Map();
    for (const r of rows) {
      if (!r.pixelHash) continue;
      const previous = byHash.get(r.pixelHash);
      if (previous) {
        const issue = `与第 ${previous.page} 页像素完全相同`;
        if (!r.issues.includes(issue)) r.issues.push(issue);
        r.visualStatus = r.visualStatus === "pass" ? "needs_review" : r.visualStatus;
      } else byHash.set(r.pixelHash, r);
    }
    return rows;
  }
  function reportKey(c) {
    return fingerprint((c.materials || []).map(m => [m.id, m.suitePage, m.jp25Revision, revision(c, Number(m.suitePage))]));
  }
  function render(c) {
    if (!active(c)) return "";
    adoptLegacy(c);
    const config = drafts.get(c.id) || normalize(c.jp25Workbench);
    const busy = ["planning", "generating"].includes(c.status) || reports.has(c.id);
    const disabled = busy ? "disabled" : "";
    const pages = c.suitePages || [], selected = samples(c), missing = remaining(c);
    const audit = c.director?.factAudit || {};
    const dna = c.director?.productVisualDNA || pages[0]?.companyCreativeLogic?.productVisualDNA;
    const input = (key, label, placeholder, page = "") => `<label>${label}<textarea data-jp25-field="${key}" ${page ? `data-jp25-page="${page}"` : ""} maxlength="${(page ? pageFields : globalFields)[key]}" rows="2" placeholder="${html(placeholder)}" ${disabled}>${html((page ? config.pages?.[page] : config)?.[key] || "")}</textarea></label>`;
    const fact = (label, value, fallback) => `<div><strong>${label}</strong><p>${html(readable(value) || fallback)}</p></div>`;
    const report = c.jp25Report;
    const staleReport = report && report.key !== reportKey(c);
    return `<section class="jp25-workbench" data-jp25-workbench aria-label="日本25图方案工作台">
      <header><div><span class="jp25-eyebrow">JAPAN · 25 IMAGES</span><h3>先定方案，再看样图</h3><p>10 张主图 + 15 张详情图 · V35 精修视觉方案 · 按卖点设计镜头与排版</p></div><span class="jp25-count">${pages.length}/25 页方案</span></header>
      ${pages.length && c.suitePlanVersion !== "director-v35-editorial-craft-source-complete" ? `<p class="jp25-help">当前仍是旧版方案。点击「只做方案」或「先试 3 张」将重新策划；旧成图会保留。</p>` : ""}
      <div class="jp25-actions">
        <button type="button" class="ghost-btn" data-jp25-action="plan" ${disabled}>只做方案</button>
        <button type="button" class="primary-btn" data-jp25-action="sample" ${disabled}>先试 3 张</button>
        <button type="button" class="ghost-btn" data-jp25-action="remaining" ${disabled}>继续剩余图片</button>
        <button type="button" class="ghost-btn" data-jp25-action="all" ${disabled}>生成整套 25 图</button>
      </div>
      <p class="jp25-help">只做方案会调用导演模型；试样按全身展示、细节、带字卖点优先选 3 页。继续生成会跳过当前方案已完成的图片。${c.materials?.length ? `当前 ${25 - missing.length}/25 张与已保存方案一致。` : ""}</p>
      <details class="jp25-locks" ${pages.length ? "" : "open"}><summary>商品、人物与视觉锁定 <small>全局调整会重新策划整套</small></summary>
        <div class="jp25-facts">${fact("用户提供的事实", audit.provided, "待从商品资料整理")}${fact("AI 从原图识别 · 请核对", audit.visible || dna, "待上传原图并策划")}${fact("推断 / 待核实 · 不直接写入文案", [audit.inferred, audit.blocked], "没有依据的数字、评价与承诺不补写")}</div>
        ${dna ? `<details><summary>查看商品外观识别</summary><p class="jp25-help">${html(readable(dna))}</p></details>` : ""}
        <div class="jp25-fields">${input("productNotes", "商品锁定补充", "填写已确认的结构、颜色、材质；未知信息留空")}${input("identityNotes", "人物锁定补充", "沿用哪张人物原图；保持脸型、发型等特征")}${input("styleNotes", "整套视觉与日文风格", "色板、光线、留白、字体氛围和日文语气")}</div>
      </details>
      ${pages.length ? `<details class="jp25-overview" ${c.materials?.length ? "" : "open"}><summary>25 页方案总览 <small>展开单页编辑日文、用途与场景</small></summary><div class="jp25-plan-list">${pages.map(p => {
        const n = Number(p.page), edit = config.pages?.[n] || {}, material = (c.materials || []).find(m => Number(m.suitePage) === n);
        const copy = edit.textFree || (!edit.headline && p.textPolicy === "none") ? "纯画面 · 不加文字" : edit.headline || p.headline || p.localizedSellingPointTitle || "按原方案文案";
        return `<details class="jp25-page"><summary><b>${String(n).padStart(2, "0")}</b><span><strong>${html(p.title || p.focus || `第 ${n} 页`)}</strong><small>${html(copy)}</small></span><em>${n <= 10 ? "主图" : "详情"}${selected.includes(n) ? " · 试样" : ""}${material ? current(c, material) ? " · 已生成" : " · 待更新" : ""}</em></summary>
          <p class="jp25-help">用途：${html(edit.goal || p.objective || p.focus || p.role || "见原方案")}<br>场景：${html(edit.scene || p.scene || p.visualEnhancement?.shotConcept || "见原方案")}</p>
          <div class="jp25-fields">${input("headline", "日文标题覆盖", p.headline || "留空沿用原方案", n)}${input("goal", "本页表达什么", p.objective || p.focus || "留空沿用原方案", n)}${input("scene", "本页场景 / 镜头调整", p.scene || "留空沿用原方案", n)}</div>
          <label class="jp25-checkbox"><input type="checkbox" data-jp25-field="textFree" data-jp25-page="${n}" ${edit.textFree ? "checked" : ""} ${disabled}>本页使用纯画面，不添加文字</label></details>`;
      }).join("")}</div></details>` : `<div class="jp25-empty">上传商品参考图、填写需求后，可先做方案，也可直接试样或生成整套。</div>`}
      <div class="jp25-save"><button type="button" class="ghost-btn" data-jp25-action="save" ${disabled}>保存调整</button><small data-jp25-dirty>${drafts.has(c.id) ? "有未保存调整" : "逐页调整只影响对应页；留空表示沿用原方案。生成前会自动保存。"}</small></div>
      <details class="jp25-report" ${report || reports.has(c.id) ? "open" : ""}><summary>独立成图检查 <small>只出报告，不自动重绘</small></summary>
        <p class="jp25-help">尺寸与完全重复检查无需模型；视觉检查会调用导演模型，核对原图、日文与卖点，仅供人工复核。</p>
        <div class="jp25-actions"><button type="button" class="ghost-btn" data-jp25-action="size-report" ${busy || !c.materials?.length ? "disabled" : ""}>检查尺寸与重复</button><button type="button" class="ghost-btn" data-jp25-action="visual-report" ${busy || !c.materials?.length ? "disabled" : ""}>加做视觉检查</button>${reports.has(c.id) ? `<button type="button" class="ghost-btn" data-jp25-action="cancel-report">停止检查</button>` : ""}${report ? `<button type="button" class="ghost-btn" data-jp25-action="export-report">导出报告</button>` : ""}</div>
        ${reports.has(c.id) ? `<p role="status">正在检查 ${report?.results?.length || 0}/${c.materials?.length || 0} 张…</p>` : ""}
        ${report ? `<p class="jp25-help">${html(report.checkedAt || "")}${staleReport ? " · 方案或成图已变化，请重新检查" : ""}</p>${report.warning ? `<p role="status">${html(report.warning)}</p>` : ""}<div class="jp25-report-rows">${(report.results || []).map(r => `<div><b>第 ${r.page} 页</b><span>${r.width ? `${r.width}×${r.height}` : "尺寸未确认"} · ${r.visualStatus === "pass" ? "视觉未发现问题" : r.visualStatus === "needs_review" ? "需要复核" : "视觉未检查"}</span><p>${html(r.issues?.join("；") || "尺寸检查未发现问题")}</p>${r.observedCopy ? `<small>识别文字：${html(r.observedCopy)}</small>` : ""}</div>`).join("")}</div>` : ""}
      </details>
    </section>`;
  }
  return { active, normalize, globals, revision, current, remaining, samples, adoptLegacy, readDraft, save, deduplicate, reportKey, render, reports };
})();
if (typeof module !== "undefined") module.exports = JP25Workbench;
