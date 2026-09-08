(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const STORAGE_KEY = "cod-prompt-atelier-v1";
  const MARKET = {
    JP: { label: "日本", language: "日文", scene: "东京、丸之内、涩谷、日式住宅、车站通勤与本土生活场景", palette: "象牙白、浅薄荷绿、不锈钢银、深炭灰，珊瑚红与暖金色作为COD强调色" },
    KR: { label: "韩国", language: "韩文", scene: "首尔商务街区、公寓、咖啡店、地铁与本土生活场景", palette: "象牙白、雾蓝、银灰、炭黑，珊瑚色作为强调色" },
    US: { label: "美国", language: "英文", scene: "城市公寓、办公室、健身房与通勤生活场景", palette: "暖白、钢灰、炭黑，橙红作为强调色" },
    DE: { label: "德国", language: "德文", scene: "柏林办公室、住宅、通勤与户外生活场景", palette: "暖白、雾灰、深蓝，砖红作为强调色" },
  };

  const SAMPLE = {
    product: "Watch4 Pro 钢带血糖手表",
    market: "JP",
    intensity: "cod",
    main: 15,
    detail: 22,
    size: "750x1000",
    model: "gpt-image-2",
    quality: "high",
    generationProfile: "standard",
    reference: "参考图2为钢带主款；参考图4为钢带辅助角度；参考图1、5为皮革变体；参考图3、6为硅胶变体，不能混用。",
    points: [
      "心血管领域专家指导的24小时健康趋势监测",
      "无创免扎针血糖趋势显示，每30分钟更新并同步App",
      "24小时心率追踪与异常变化提醒",
      "光电血氧趋势监测",
      "1.9英寸曲面无边大屏，强光下清晰显示",
      "商务不锈钢钢带，精密抛光，贴合手腕",
      "蓝牙通话、LINE、邮件和导航通知",
      "AI语音操作",
      "100种运动模式，覆盖跑步、游泳和高尔夫",
      "24小时云端趋势分析与静默SOS提醒",
    ].join("\n"),
    discount: "",
    salePrice: "",
    codText: "代引きOK",
    deadline: "",
    allowPromo: true,
    allowMedical: true,
    style: "明亮、不太暗；日本电商高密度排版；附带日本模特；页面无留白；COD视觉夸张。",
    avoid: "不要混合表带、不要动画、不要乱码、不要虚构证书或医生。",
  };

  const JP_HEADLINES = [
    ["心血管", "専門家の知見を、毎日の記録へ"],
    ["血糖", "血糖トレンドを、手元で可視化"],
    ["心率", "24時間、心拍をチェック"],
    ["血氧", "血中酸素の変化を見える化"],
    ["大屏", "1.9インチ、広く見やすく"],
    ["钢带", "手元に映える、スチールバンド"],
    ["通话", "通話も通知も、手元で"],
    ["语音", "話しかけるだけのスマート操作"],
    ["运动", "100種類のスポーツを記録"],
    ["云端", "毎日の変化をクラウドで確認"],
    ["SOS", "静かに知らせる、SOSサポート"],
  ];

  function readForm() {
    const product = $("product-name").value.trim() || "当前商品";
    return sanitizeFormForProduct({
      product,
      market: $("target-market").value,
      intensity: $("hook-intensity").value,
      main: clampNumber($("main-count").value, 1, 30, 15),
      detail: clampNumber($("detail-count").value, 1, 40, 22),
      size: $("canvas-size").value.trim() || "750x1000",
      model: $("render-model")?.value || SAMPLE.model,
      quality: $("render-quality")?.value || SAMPLE.quality,
      generationProfile: $("render-profile")?.value || SAMPLE.generationProfile,
      reference: $("reference-map").value.trim(),
      points: splitPoints($("selling-points").value, product),
      discount: $("discount").value.trim(),
      salePrice: $("sale-price").value.trim(),
      codText: $("cod-text").value.trim(),
      deadline: $("deadline").value.trim(),
      allowPromo: $("allow-promo").checked,
      allowMedical: $("allow-medical").checked,
      style: $("style-notes").value.trim(),
      avoid: $("avoid-notes").value.trim(),
    });
  }

  function sanitizeFormForProduct(form) {
    const result = { ...form, points: Array.isArray(form.points) ? [...form.points] : [] };
    const changedProduct = result.product && result.product !== SAMPLE.product;
    if (changedProduct && result.reference === SAMPLE.reference) result.reference = "";
    if (changedProduct && result.points.join("\n") === SAMPLE.points) result.points = [`突出${result.product}的核心购买理由、真实外观与使用价值`];
    if (changedProduct && result.avoid === SAMPLE.avoid) result.avoid = "不要混用不同SKU、规格或包装；不要动画、乱码、产品变形或虚构信息。";
    if (result.market !== "JP" && result.style === SAMPLE.style) {
      const market = MARKET[result.market] || MARKET.JP;
      result.style = `明亮、不太暗；${market.label}本土电商高密度排版；附带当地人物与使用场景；页面无留白；COD视觉夸张。`;
    }
    if (result.market !== "JP" && result.codText === SAMPLE.codText) result.codText = "";
    return result;
  }

  function clampNumber(value, min, max, fallback) {
    const number = Number(value);
    return Number.isFinite(number) ? Math.min(max, Math.max(min, Math.round(number))) : fallback;
  }

  function splitPoints(value, product = "当前商品") {
    const points = String(value || "").split(/[\n\r；;]+/).map((item) => item.trim()).filter(Boolean);
    return points.length ? points : [`突出${product}的核心购买理由、真实外观与使用价值`];
  }

  function esc(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
  }

  function japaneseHeadline(point, index) {
    const source = `${point || ""}`.toLowerCase();
    const hit = JP_HEADLINES.find(([key]) => source.includes(key.toLowerCase()));
    if (hit) return hit[1];
    const fallback = ["選ばれる理由を、ひとつずつ", "毎日に寄り添う、頼れる一品", "使い方も、実感もわかりやすく"];
    return fallback[index % fallback.length];
  }

  function pageHook(point, index, market) {
    if (market !== "JP") return pointTitle(point, "当前页面核心卖点");
    return japaneseHeadline(point, index);
  }

  function promoLine(form) {
    if (!form.allowPromo) return "不启用促销组件；用产品数字和卖点做视觉钩子。";
    const parts = [form.discount, form.salePrice, form.codText, form.deadline].filter(Boolean);
    return parts.length ? `允许使用用户提供的COD转化信息：${parts.join(" / ")}。` : "允许使用促销贴纸、静态CTA和大号数字；没有真实价格时不要虚构价格。";
  }

  function buildMasterPrompt(form, plan = null) {
    const aiMasterPrompt = typeof plan?.masterPrompt === "string" ? plan.masterPrompt.trim() : "";
    if (aiMasterPrompt && plan?.promptBlueprint?.source === "model") return aiMasterPrompt;
    const market = MARKET[form.market] || MARKET.JP;
    const total = form.main + form.detail;
    const intensity = form.intensity === "premium" ? "高级精品" : form.intensity === "bold" ? "夸张钩子" : "COD强转化";
    const points = form.points.map((item, index) => `${index + 1}. ${item}`).join("\n");
    const mainMap = makeMainPages(form).map((page) => `主图${String(page.index).padStart(2, "0")}：${page.title}｜${page.focus}`).join("\n");
    const detailMap = makeDetailPages(form).map((page) => `详情${String(page.index).padStart(2, "0")}：${page.title}｜${page.focus}`).join("\n");
    const director = plan?.director && typeof plan.director === "object" ? plan.director : null;
    const directedPages = Array.isArray(plan?.suitePages) ? plan.suitePages : [];
    const pageMap = directedPages.length
      ? directedPages.map((page, index) => `${page.page || index + 1}. ${page.role || "页面"}｜${page.title || page.focusTitle || "未命名"}｜目标：${page.objective || page.focus || "—"}｜场景：${page.scene || "—"}｜钩子：${page.headline || page.sellingPoint || "—"}`).join("\n")
      : `${mainMap}\n${detailMap}`;
    const aiDirectorSection = director
      ? `

[AI Director analysis — use this result as the current source of truth]
Analysis source: ${director.source === "model" ? "AI model" : "server rules"}.
Analysis model: ${director.model || directorConfig.model || "未配置"}.
Product summary: ${director.productSummary || "—"}.
Visual DNA: ${compactAnalysisValue(director.productVisualDNA, 900)}.
Selling-point coverage: ${compactAnalysisValue(director.sellingPointCoverage, 900)}.
Do not replace the AI-directed page roles with a generic repeated template.`
      : "";
    return `[Country-targeted COD landing-page director]
Target market: ${market.label} (${form.market}).
Visible language: ${market.language} only.
Image suite: ${form.main} main images + ${form.detail} detail images = ${total} images.
Current image index: {{CURRENT_PAGE}}.
Canvas: ${form.size}, vertical, full-bleed, no unfinished bottom area.
Render one finished static ecommerce image immediately. Do not output a plan or explanation.

[Product identity]
Product: ${form.product}.
Reference role map: ${form.reference || "Use the uploaded reference images as identity references; keep one exact SKU per page."}
Preserve exact product shape, color, materials, structure, packaging, labels, proportions, accessories and usage method. Never merge different variants.

[Source selling points — preserve the original meaning]
${points}

[COD creative direction]
Visual mode: ${intensity}.
Keep the product or result as the largest visual, but use rich COD merchandising: oversized numbers, bold color blocks, promotional stickers, ribbons, static arrows, comparison dividers, data cards, local model scenes and dramatic product close-ups.
${promoLine(form)}
Main image 02 must be the only 2x2 pain-point grid. Main image 07 must be the fair before/after comparison. Other pages can use layered evidence modules but must not become a repetitive card wall.

[Localized art direction]
${market.scene}。
Bright ${market.label} ecommerce-inspired information density, editorial product photography, strong hierarchy and local lifestyle realism.
Palette: ${market.palette}。
${form.style || "页面明亮、丰富、统一配色、夸张包装、无留白。"}

[Visible copy]
Use one short localized headline plus compact labels. All visible copy must use natural ${market.language} rather than literal Chinese translation.
Reserve a clean text-safe zone when exact text rendering is uncertain; never create random letters.

[Claims and evidence handling]
保留用户明确提供的产品卖点、规格与效果语义，但不要自行增加用户未提供的认证、机构、专家姓名、实验编号、效果数据或功能。
${form.allowMedical ? "如果当前产品确实包含健康类卖点，允许保留用户提供的原始语义和数字，但不得扩展为诊断或治疗承诺；非健康产品不得加入任何健康类内容。" : "健康类内容改为中性表达；非健康产品只使用当前商品卖点。"}

[Static image and quality]
No animation, GIF, video timeline or motion sequence. No distorted product, mixed variant, random copy, watermark or platform logo.
${form.avoid || "避免产品变形、SKU或规格串款、乱码和空白区域。"}
Every page must feel like a distinct conversion module while preserving the same product identity, model quality, palette family and ${market.label} visual grade.
[Page map]
${pageMap}${aiDirectorSection}`;
  }

  function renderMasterPrompt(form = currentForm, plan = suitePlanCache) {
    const output = $("master-output");
    if (output && form) output.textContent = buildMasterPrompt(form, plan);
    const mode = $("master-output-mode");
    if (!mode) return;
    const director = plan?.director && typeof plan.director === "object" ? plan.director : null;
    mode.textContent = plan?.promptBlueprint?.source === "model"
      ? `${plan.promptBlueprint.model || director?.promptRewriteModel || directorConfig.model || "AI 模型"} 已针对当前商品从零生成 · 指纹 ${plan.promptBlueprint.fingerprint || "—"}`
      : director?.source === "model"
        ? `${director.model || directorConfig.model || "AI 模型"} 已增强总控 · 可直接粘贴到 Cod / 图像模型`
      : director
        ? "服务器规则总控 · 可直接粘贴到 Cod / 图像模型"
        : "本地规则草稿；完成 AI 分析后自动增强 · 可直接粘贴到 Cod / 图像模型";
  }

  function buildSuiteBrief(form) {
    const market = MARKET[form.market] || MARKET.JP;
    const promo = [form.discount, form.salePrice, form.codText, form.deadline].filter(Boolean).join(" / ");
    return [
      `产品：${form.product}`,
      `目标市场：${market.label}（${form.market}），可见文案使用${market.language}`,
      `套图结构：主图${form.main}张 + 详情图${form.detail}张 = ${form.main + form.detail}张，画布${form.size}`,
      `核心卖点：${form.points.join("；")}`,
      promo ? `真实促销信息：${promo}` : "未提供真实价格、折扣或期限，不要编造促销数字",
      `视觉要求：${form.style || `明亮、统一配色、COD强转化、附带${market.label}本土人物和场景、无留白`}`,
      `参考图绑定：${form.reference || "第一张为主商品，其余由AI按文件名和画面自动识别"}`,
      `限制：${form.avoid || "静态画面，不要动画、乱码、变形或混用变体"}`,
    ].join("\n");
  }

  function buildPromptGeneratorInput(form) {
    return {
      product: form.product,
      market: form.market,
      intensity: form.intensity,
      sellingPoints: [...form.points],
      promotions: {
        discount: form.discount,
        salePrice: form.salePrice,
        codText: form.codText,
        deadline: form.deadline,
      },
      allowPromo: form.allowPromo,
      allowMedical: form.allowMedical,
      style: form.style,
      avoid: form.avoid,
      referenceMap: form.reference,
    };
  }

  function promptInputFingerprint(form) {
    return JSON.stringify({
      ...buildPromptGeneratorInput(form),
      main: form.main,
      detail: form.detail,
      size: form.size,
      references: referenceFiles.map((file) => ({ name: file.name, size: file.size, modified: file.lastModified })),
      directorModel: directorConfig.model,
      directorEnabled: directorConfig.enabled,
      directorConfigured: directorConfig.configured,
    });
  }

  function makeMainPages(form) {
    return createPageSet(form.main, "main", form);
  }

  function makeDetailPages(form) {
    return createPageSet(form.detail, "detail", form);
  }

  function pointTitle(point, fallback = "核心卖点") {
    const cleaned = String(point || "")
      .replace(/^\s*(?:\d+[.、)）:]?|[-*•])\s*/, "")
      .replace(/[（(][^）)]{0,36}[）)]/g, "")
      .split(/[，。；;：:\n]/)[0]
      .trim();
    return Array.from(cleaned || fallback).slice(0, 18).join("");
  }

  function adaptivePageBlueprint(form, section, index) {
    const localIndex = index + 1;
    const points = form.points.length ? form.points : [`突出${form.product}的核心购买理由`];
    if (section === "main") {
      if (localIndex === 1) return ["首屏英雄图", `建立${form.product}识别并放大最核心购买理由`, `完整${form.product}作为最大主体，结合目标市场人物或场景与用户提供的第一核心卖点`, points[0]];
      if (localIndex === 2) return ["四宫格痛点", `把${form.product}解决的四个购买痛点做成唯一一张2×2信息图`, points.slice(0, 4).map((point) => pointTitle(point)).join("、") || `${form.product}四个真实使用痛点`, `${form.product}解决的四个核心痛点`];
      if (localIndex === 3) return [pointTitle(points[0], "核心噱头"), `集中放大首要卖点：${points[0]}`, `${form.product}主体、卖点证据和一个强数字或醒目短句`, points[0]];
      if (localIndex === 7) return ["公平对比", `用同条件左右对比证明${form.product}的核心价值`, `传统方案或使用前状态 vs 使用${form.product}后的真实便利；不虚构效果数据`, points[0]];
      if (localIndex === form.main) return ["购买理由收束", `汇总${form.product}的主要购买理由并形成静态CTA`, `完整主商品、三组最强卖点、用户提供的真实促销信息和购买行动区`, points.slice(0, 3).join("；")];
      const point = points[(localIndex - 3) % points.length];
      return [pointTitle(point), `完整表现当前卖点：${point}`, `${form.product}作为主体，用产品细节、真实使用动作或结果证据表现该卖点`, point];
    }
    if (localIndex === 1) return ["产品外观总览", `完整展示${form.product}正面、侧面和关键结构`, `只使用当前主SKU，保持形状、颜色、材质、比例和配件一致`, points[0]];
    if (localIndex === 2) return ["结构与核心细节", `放大${form.product}最能证明品质或功能的局部`, `参考图可见结构、接口、纹理、工艺或核心组件微距`, points[0]];
    if (localIndex === form.detail) return ["产品信息收尾", `用${form.product}、包装、配件、规格和注意事项完成收尾`, `仅展示用户提供或参考图可确认的产品信息，不编造参数`, `${form.product}产品信息`];
    const point = points[(localIndex - 3 + points.length) % points.length];
    const archetypes = ["卖点证据", "材质工艺", "使用步骤", "本土场景", "局部特写", "效果说明", "规格信息"];
    const archetype = archetypes[(localIndex - 3) % archetypes.length];
    return [`${pointTitle(point)} · ${archetype}`, `深入解释卖点：${point}`, `以${form.product}真实局部、使用过程、场景动作或可验证信息建立证据`, point];
  }

  function createPageSet(count, section, form) {
    const result = [];
    for (let index = 0; index < count; index += 1) {
      const base = adaptivePageBlueprint(form, section, index);
      const globalIndex = section === "main" ? index + 1 : form.main + index + 1;
      const point = base[3] || form.points[(globalIndex - 1) % form.points.length];
      const title = base[0];
      const focus = base[1];
      const hook = pageHook(point, globalIndex - 1, form.market);
      const page = {
        index: globalIndex,
        section,
        localIndex: index + 1,
        title,
        focus,
        hook,
        evidence: base[2] || focus,
        sourcePoint: point,
      };
      page.prompt = buildPagePrompt(page, form);
      result.push(page);
    }
    return result;
  }

  function buildPagePrompt(page, form) {
    const market = MARKET[form.market] || MARKET.JP;
    const sectionLabel = page.section === "main" ? `主图${String(page.localIndex).padStart(2, "0")}` : `详情${String(page.localIndex).padStart(2, "0")}`;
    const extra = /四宫格/.test(page.title) ? "必须使用2×2四宫格，每格一个痛点，四格大小一致但层级清晰。" : /对比/.test(page.title) ? "必须使用左右公平对比，同一主体、同一镜头、同一比例和同一光线。" : "禁止复制相邻页的机位和信息区位置。";
    const labels = page.section === "main" ? "3至5个短标签、静态箭头或图标" : "2至4个短标签或一个局部证据模块";
    const scene = page.scene || market.scene;
    const composition = page.composition || `${form.size} vertical full-bleed；产品或结果占45%至70%；${labels}；无空白底部`;
    const treatment = page.impactTreatment || (form.intensity === "premium" ? "克制高级、材质真实、编辑式排版" : "COD强转化、夸张大数字、促销贴纸、斜切色带、静态数据卡和高对比层级");
    const localizedCopy = page.aiDirected
      ? `使用AI导演提供的${market.language}标题「${page.hook}」，其余文字保持短、粗、清晰，不生成长段落。`
      : `把“${page.sourcePoint || page.hook}”的含义改写成一句自然${market.language}短标题；中文只作为创作说明，不得出现在画面中。`;
    return `[${sectionLabel} · ${page.title}]
Goal: ${page.focus}。
Single page hook: ${page.hook}。
Product: ${form.product}。严格按照已绑定的参考图保持产品身份。
Scene: ${scene}，加入与本页卖点有关的目标市场生活道具和自然人物动作。
Evidence: ${page.evidence}。
${page.pose ? `Pose / action: ${page.pose}。\n` : ""}Composition: ${composition}。
Visual treatment: ${treatment}。
Localized copy: 所有可见文案只使用${market.language}；${localizedCopy}
${extra}
Static only: no animation, video UI, random text, watermark or distorted product.`;
  }

  function aiDirectedPages(form) {
    const planPages = Array.isArray(suitePlanCache?.suitePages) ? suitePlanCache.suitePages : [];
    if (planPages.length !== form.main + form.detail) return null;
    return planPages.map((source, index) => {
      const globalIndex = Number(source.page) || index + 1;
      const section = globalIndex <= form.main ? "main" : "detail";
      const localIndex = section === "main" ? globalIndex : globalIndex - form.main;
      const page = {
        index: globalIndex,
        section,
        localIndex,
        title: source.title || source.focusTitle || `${section === "main" ? "主图" : "详情"}${String(localIndex).padStart(2, "0")}`,
        focus: source.objective || source.focus || source.focusDescription || "当前页面核心购买理由",
        hook: source.headline || source.sellingPoint || pageHook(form.points[(globalIndex - 1) % form.points.length], globalIndex - 1, form.market),
        evidence: source.evidence || source.supportingDetail || source.focusDescription || "用参考图可确认的产品事实建立视觉证据",
        scene: source.scene || "",
        pose: source.pose || "",
        composition: source.composition || "",
        impactTreatment: source.impactTreatment || source.visualEnhancement?.impactTreatment || "",
        sourcePoint: source.sellingPoint || "",
        aiDirected: true,
        modelAuthored: Boolean(source.modelPrompt),
      };
      page.prompt = String(source.modelPrompt || "").trim() || buildPagePrompt(page, form);
      return page;
    }).sort((a, b) => a.index - b.index);
  }

  function storyboardPages(form) {
    return aiDirectedPages(form) || [...makeMainPages(form), ...makeDetailPages(form)];
  }

  function makeCopyCards(form) {
    const points = form.points.slice(0, 12);
    return points.map((point, index) => ({
      index: index + 1,
      source: point,
      headline: form.market === "JP" ? japaneseHeadline(point, index) : point,
      label: form.market === "JP" ? ["注目ポイント", "毎日の記録", "スマート管理"][index % 3] : "Primary hook",
    }));
  }

  function render(form) {
    const pages = storyboardPages(form);
    currentPages = pages;
    if (!pages.some((page) => page.index === selectedPage)) selectedPage = pages[0]?.index || 1;
    const market = MARKET[form.market] || MARKET.JP;
    const total = pages.length;
    $("output-title").textContent = `${form.product} · ${market.label} COD 套图`;
    $("stat-total").textContent = total;
    $("stat-hooks").textContent = form.points.length;
    $("stat-locale").textContent = form.market;
    $("stat-locale-label").textContent = `${market.language}可见文案`;
    $("stat-ratio").textContent = ratioLabel(form.size);
    $("all-count").textContent = total;
    $("main-count-label").textContent = form.main;
    $("detail-count-label").textContent = form.detail;
    renderMasterPrompt(form, suitePlanCache);
    $("page-list").innerHTML = pages.map((page) => `<article class="page-card ${page.section}${page.index === selectedPage ? " selected" : ""}${generatedMaterials.has(page.index) ? " generated" : ""}" data-section="${page.section}" data-page="${page.index}" tabindex="0" role="button" aria-label="选择第${page.index}页">
      <div class="page-card-header"><span class="page-index">${String(page.index).padStart(2, "0")}</span><span class="page-kind">${page.section === "main" ? "主图" : "详情"}</span></div>
      <h3>${esc(page.title)}</h3>
      <p>${esc(page.focus)}</p>
      <code>${esc(page.hook)}</code>
    </article>`).join("");
    $("copy-board").innerHTML = makeCopyCards(form).map((item) => `<article class="copy-card">
      <small>HOOK ${String(item.index).padStart(2, "0")} · ${esc(item.label)}</small>
      <strong>${esc(item.headline)}</strong>
      <p>${esc(item.source)}</p>
    </article>`).join("");
    bindPageFilters();
    renderReferencePreview();
    renderDirectorAnalysis(suitePlanCache);
    renderGenerationStatus();
    renderGeneratedGallery();
    saveDraft(form);
  }

  function ratioLabel(size) {
    const match = String(size).match(/(\d+)\s*[x×]\s*(\d+)/i);
    if (!match) return "—";
    const width = Number(match[1]);
    const height = Number(match[2]);
    if (!width || !height) return "—";
    const ratio = width / height;
    if (Math.abs(ratio - .75) < .03) return "3:4";
    if (Math.abs(ratio - 1) < .03) return "1:1";
    return `${width}:${height}`;
  }

  function saveDraft(form) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(form));
      $("saved-state").textContent = `已保存 ${new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}`;
    } catch (error) {
      $("saved-state").textContent = "仅本页有效";
    }
  }

  function loadDraft() {
    let saved = null;
    try { saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null"); } catch (error) { saved = null; }
    const raw = saved && typeof saved === "object" ? { ...SAMPLE, ...saved } : { ...SAMPLE };
    const form = sanitizeFormForProduct({ ...raw, points: splitPoints(Array.isArray(raw.points) ? raw.points.join("\n") : raw.points, raw.product || "当前商品") });
    $("product-name").value = form.product;
    $("target-market").value = form.market;
    $("hook-intensity").value = form.intensity;
    $("main-count").value = form.main;
    $("detail-count").value = form.detail;
    $("canvas-size").value = form.size;
    if ($("render-model")) $("render-model").value = form.model || SAMPLE.model;
    if ($("render-quality")) $("render-quality").value = form.quality || SAMPLE.quality;
    if ($("render-profile")) $("render-profile").value = form.generationProfile || SAMPLE.generationProfile;
    $("reference-map").value = form.reference;
    $("selling-points").value = form.points.join("\n");
    $("discount").value = form.discount || "";
    $("sale-price").value = form.salePrice || "";
    $("cod-text").value = form.codText || "";
    $("deadline").value = form.deadline || "";
    $("allow-promo").checked = form.allowPromo !== false;
    $("allow-medical").checked = form.allowMedical !== false;
    $("style-notes").value = form.style || "";
    $("avoid-notes").value = form.avoid || "";
    return form;
  }

  function bindPageFilters() {
    document.querySelectorAll(".page-filter-btn").forEach((button) => {
      button.onclick = () => {
        document.querySelectorAll(".page-filter-btn").forEach((item) => item.classList.toggle("active", item === button));
        const section = button.dataset.section;
        document.querySelectorAll(".page-card").forEach((card) => {
          card.hidden = section !== "all" && card.dataset.section !== section;
        });
      };
    });
    document.querySelectorAll(".page-card").forEach((card) => {
      const choose = () => {
        selectedPage = Number(card.dataset.page) || 1;
        document.querySelectorAll(".page-card").forEach((item) => item.classList.toggle("selected", item === card));
        const page = currentPages.find((item) => item.index === selectedPage);
        if ($("selected-page-label")) $("selected-page-label").textContent = page ? `${page.section === "main" ? "主图" : "详情"}${String(page.localIndex).padStart(2, "0")}` : `第${selectedPage}页`;
      };
      card.addEventListener("click", choose);
      card.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); choose(); } });
    });
  }

  function copyText(value) {
    if (navigator.clipboard?.writeText) return navigator.clipboard.writeText(value);
    const area = document.createElement("textarea");
    area.value = value; document.body.appendChild(area); area.select(); document.execCommand("copy"); area.remove();
    return Promise.resolve();
  }

  function toast(message) {
    let node = document.querySelector(".atelier-toast");
    if (!node) { node = document.createElement("div"); node.className = "atelier-toast"; document.body.appendChild(node); }
    node.textContent = message; node.classList.add("show");
    window.clearTimeout(toast.timer); toast.timer = window.setTimeout(() => node.classList.remove("show"), 1800);
  }

  function downloadText(form) {
    const pages = storyboardPages(form);
    const body = [buildMasterPrompt(form, suitePlanCache), "\n\n===== PAGE PROMPTS =====\n", ...pages.map((page) => `${page.prompt}\n\n`)].join("");
    const blob = new Blob([body], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a"); link.href = url; link.download = `${form.product.replace(/[^\w\u4e00-\u9fff-]+/g, "-")}-cod-prompts.txt`; link.click();
    URL.revokeObjectURL(url);
  }

  const GENERATION_SUITE_KEY = "cod-country-landing-30";
  const GENERATION_COUNT_OPTIONS = [8, 12, 16, 20, 24, 30, 37];
  let currentPages = [];
  let selectedPage = 1;
  let referenceFiles = [];
  let generatedMaterials = new Map();
  let generationState = { status: "idle", requested: 0, completed: 0, active: 0, errors: [], plan: null };
  let analysisState = { running: false, error: "" };
  let generationAbortController = null;
  let suitePlanCache = null;
  let suitePlanCacheKey = "";
  let directorConfig = { loaded: false, enabled: false, configured: false, model: "", fallbackModels: [], message: "" };

  function generationSuiteCount(form) {
    const total = form.main + form.detail;
    return GENERATION_COUNT_OPTIONS.includes(total) ? total : 37;
  }

  function renderReferencePreview() {
    const node = $("reference-preview");
    if (!node) return;
    if (!referenceFiles.length) {
      node.innerHTML = `<div class="reference-empty">尚未选择参考图。生图接口至少需要 1 张商品图。</div>`;
      return;
    }
    node.innerHTML = referenceFiles.map((file, index) => {
      const url = URL.createObjectURL(file);
      const html = `<div class="reference-thumb"><img src="${url}" alt="参考图${index + 1}"><span>${index + 1}</span><em>${esc(file.name)}</em></div>`;
      window.setTimeout(() => URL.revokeObjectURL(url), 3000);
      return html;
    }).join("");
  }

  function referenceRoleFromBrief(index, form) {
    const source = String(form?.reference || "");
    const segment = source.split(/[；;\n。]+/).find((clause) => {
      const match = clause.match(/(?:参考图|图片|image)\s*([0-9、,，\s和及]+)/i);
      return match && match[1].split(/[、,，\s和及]+/).filter(Boolean).map(Number).includes(index);
    }) || "";
    if (/主款|主商品|主产品|主体|hero|primary/i.test(segment)) return "product";
    if (/辅助|细节|角度|特写|结构|包装|detail/i.test(segment)) return "detail";
    if (/人物|模特|person|model/i.test(segment)) return "person";
    if (/使用|操作|佩戴|安装|usage|how.?to/i.test(segment)) return "usage";
    if (/排版|风格|场景|灵感|其他.*变体|不要混用|不得混用|排除|layout|style|scene|variant/i.test(segment)) return "layout";
    return index === 1 ? "product" : "auto";
  }

  function buildReferenceBindings(form = currentForm) {
    return referenceFiles.map((file, index) => ({
      index: index + 1,
      role: referenceRoleFromBrief(index + 1, form),
      filename: file.name,
      name: file.name,
      keywords: index === 0 ? "主商品；如果绑定说明指定其他图片，以绑定说明为准" : "由AI按绑定说明、文件名和画面自动识别",
    }));
  }

  function generationReferenceSet(form, plan = null) {
    const resolved = Array.isArray(plan?.resolvedReferenceBindings) ? plan.resolvedReferenceBindings : [];
    const bindings = resolved.length
      ? referenceFiles.map((file, index) => ({ ...(resolved.find((item) => Number(item.index) === index + 1) || {}), index: index + 1, name: file.name, filename: file.name, role: (resolved.find((item) => Number(item.index) === index + 1)?.role || "auto") }))
      : buildReferenceBindings(form);
    const explicitMap = /参考图|图片|image/i.test(String(form?.reference || ""));
    if (!explicitMap) return { files: referenceFiles, bindings };
    const selected = referenceFiles.map((file, index) => ({ file, binding: bindings[index] }))
      .filter((item) => ["product", "detail", "usage", "person"].includes(item.binding.role));
    if (!selected.length) return { files: referenceFiles, bindings };
    return {
      files: selected.map((item) => item.file),
      bindings: selected.map((item, index) => ({ ...item.binding, index: index + 1 })),
    };
  }

  function renderGenerationStatus() {
    const total = generationState.requested || generationSuiteCount(currentForm || SAMPLE);
    const completed = generationState.completed || 0;
    const active = generationState.active || 0;
    const percent = total ? Math.min(100, Math.round((completed / total) * 100)) : 0;
    const status = $("generation-status");
    const detail = $("generation-detail");
    const count = $("generation-count");
    const bar = $("generation-progress-bar");
    const currentBtn = $("generate-current-btn");
    const suiteBtn = $("generate-suite-btn");
    const analyzeBtn = $("analyze-ai-btn");
    const retryBtn = $("retry-failed-btn");
    const cancelBtn = $("cancel-generation-btn");
    if (!status || !detail || !count || !bar) return;
    count.textContent = analysisState.running ? "AI" : `${completed} / ${total}`;
    bar.style.width = analysisState.running ? "35%" : `${percent}%`;
    const page = currentPages.find((item) => item.index === selectedPage);
    const activeModel = imageModelLabel(currentForm?.model || "gpt-image-2");
    const activeProfile = generationProfileLabel(currentForm?.generationProfile || "standard");
    if (page && $("selected-page-label")) $("selected-page-label").textContent = `${page.section === "main" ? "主图" : "详情"}${String(page.localIndex).padStart(2, "0")}`;
    if (analysisState.running) {
      status.textContent = "AI Director 正在重写整套 Prompt…";
      detail.textContent = `正在调用 ${directorConfig.model || "GPT‑5.6‑sol"} 只依据当前商品重新生成总控与${total}页独立Prompt；不会复用上一商品内容。`;
    } else if (generationState.status === "running") {
      status.textContent = active ? `正在生成第 ${active} 页…` : "正在准备生图任务…";
      detail.textContent = `模型 ${activeModel} · ${activeProfile}策略 · 后台任务会自动轮询，已完成 ${completed}/${total}。`;
    } else if (generationState.status === "done") {
      status.textContent = `已完成 ${completed} 张真实成图`;
      detail.textContent = generationState.errors.length ? `模型 ${activeModel} · 有 ${generationState.errors.length} 张失败，可重新选择页面补图。` : `模型 ${activeModel} · 所有选定页面已生成，可在“成图结果”中查看和保存。`;
    } else if (generationState.status === "error") {
      status.textContent = "生图任务未完成";
      detail.textContent = generationState.errors[0] || "请检查登录状态、参考图和远端生图节点配置。";
    } else {
      status.textContent = referenceFiles.length ? "参考图已就绪，可生成Prompt或真实生图" : "可先生成整套文字 Prompt";
      detail.textContent = referenceFiles.length ? `当前模型 ${activeModel} · ${activeProfile}策略。可先让 GPT‑5.6‑sol 重写整套Prompt，再生成当前页或整套图片。` : `不上传图片也能先让 GPT‑5.6‑sol 生成整套Prompt；真实生图前再上传当前商品参考图。`;
    }
    if (currentBtn) currentBtn.disabled = Boolean(generationAbortController);
    if (suiteBtn) suiteBtn.disabled = Boolean(generationAbortController);
    if (analyzeBtn) analyzeBtn.disabled = Boolean(generationAbortController);
    if (retryBtn) retryBtn.hidden = !failedPageNumbers().length || Boolean(generationAbortController) || analysisState.running;
    if (cancelBtn) cancelBtn.hidden = !generationAbortController;
  }

  function imageModelLabel(model = "") {
    const value = String(model || "");
    const labels = {
      "gpt-image-2": "GPT Image 2",
      "codex-gpt-image-2": "Codex GPT Image 2",
      auto: "自动选择可用模型",
    };
    if (labels[value]) return labels[value];
    if (value.startsWith("acore/")) return `Acore · ${value.slice("acore/".length)}`;
    return value || "未指定模型";
  }

  function generationProfileLabel(profile = "") {
    return ({ fast: "快速", standard: "标准", quality: "精审" }[String(profile)] || "标准");
  }

  function setModelConfigStatus(message, warning = false) {
    const node = $("model-config-status");
    if (!node) return;
    node.textContent = message;
    node.classList.toggle("is-warning", Boolean(warning));
  }

  function setDirectorConfigStatus(message, warning = false) {
    const node = $("director-config-status");
    if (!node) return;
    node.textContent = message;
    node.classList.toggle("is-warning", Boolean(warning));
  }

  function setDirectorModelDisplay(model, source, warning = false) {
    const card = $("director-model-display");
    const value = $("director-model-value");
    const detail = $("director-model-source");
    if (value) value.textContent = model || "未配置";
    if (detail) detail.textContent = source || "套图生成前会先读取此模型的分析结果";
    if (card) card.classList.toggle("is-warning", Boolean(warning));
  }

  function readSavedRenderPreference(key) {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
      return saved && typeof saved === "object" ? String(saved[key] || "") : "";
    } catch (error) {
      return "";
    }
  }

  function fillSelect(select, values, selected, labeler = (value) => value) {
    if (!select || !Array.isArray(values) || !values.length) return selected;
    const options = [...new Set(values.map((value) => String(value || "").trim()).filter(Boolean))];
    if (!options.length) return selected;
    const next = options.includes(selected) ? selected : options[0];
    select.innerHTML = options.map((value) => `<option value="${esc(value)}">${esc(labeler(value))}</option>`).join("");
    select.value = next;
    return next;
  }

  async function loadImageConfig() {
    try {
      const payload = await apiRequest("/api/sku-board/ai-image-config");
      const config = payload?.aiImage && typeof payload.aiImage === "object" ? payload.aiImage : {};
      const director = config.director && typeof config.director === "object" ? config.director : {};
      directorConfig = {
        loaded: true,
        enabled: Boolean(director.enabled),
        configured: Boolean(director.configured),
        model: String(director.model || ""),
        fallbackModels: Array.isArray(director.fallbackModels) ? director.fallbackModels : [],
        message: String(director.message || ""),
      };
      const models = Array.isArray(config.models) ? config.models : [];
      const qualities = Array.isArray(config.qualities) ? config.qualities : [];
      const savedModel = readSavedRenderPreference("model");
      const savedQuality = readSavedRenderPreference("quality");
      const configuredModel = String(config.model || "");
      const modelPreference = savedModel && models.includes(savedModel) ? savedModel : configuredModel;
      if (models.length) fillSelect($("render-model"), models, modelPreference || models[0], imageModelLabel);
      if (qualities.length) fillSelect($("render-quality"), qualities, savedQuality || $("render-quality")?.value || qualities[0], (value) => ({ auto: "自动", low: "低质", medium: "平衡", high: "高质" }[value] || value));
      const nodeCount = Number(config.nodeCount || config.nodes?.length || 0);
      if (config.enabled && nodeCount) {
        setModelConfigStatus(`已读取服务器配置 · ${nodeCount} 个生图节点 · 当前 ${imageModelLabel($("render-model")?.value || configuredModel || "gpt-image-2")}；最终质量由模型和策略共同决定`);
      } else {
        setModelConfigStatus("未检测到可用生图节点；提示词仍可编排，真实出图前请先在 SKU Board 配置 AI 生图服务", true);
      }
      if (directorConfig.enabled && directorConfig.configured && directorConfig.model) {
        const fallback = directorConfig.fallbackModels.length ? ` · 备援 ${directorConfig.fallbackModels.join(" / ")}` : "";
        setDirectorModelDisplay(directorConfig.model, `已启用 · ${fallback ? `自动备援：${directorConfig.fallbackModels.join(" / ")}` : "无备援"}`);
        setDirectorConfigStatus(`AI 分析模型已启用 · ${directorConfig.model}${fallback}；套图编排会先调用该模型分析产品、噱头和参考图`);
      } else {
        setDirectorModelDisplay(directorConfig.model || "未配置", directorConfig.model ? "已读取模型名称，但 AI DIRECTOR 尚未启用或 API 地址/密钥不完整" : "请在主 SKU Board 的 AI DIRECTOR 中配置模型", true);
        setDirectorConfigStatus("AI 分析模型未启用或未完成配置；当前可用本地规则编排，想用 GPT‑5.6‑sol 请在 SKU Board 的 AI DIRECTOR 中启用", true);
      }
      currentForm = readForm();
      saveDraft(currentForm);
      renderGenerationStatus();
    } catch (error) {
      const authError = error?.status === 401 || error?.status === 403;
      setModelConfigStatus(authError ? "未登录或暂无 AI 生图权限；当前使用默认模型，登录后会读取服务器配置" : "暂未读取到服务器模型配置；当前使用默认 GPT Image 2，生成失败时请检查 AI 生图节点", true);
      setDirectorModelDisplay(authError ? "无法读取配置" : "读取失败", authError ? "请先登录主 SKU Board，页面才能显示 AI Director 模型" : "请检查服务器和 AI Director 配置", true);
      setDirectorConfigStatus(authError ? "未登录或暂无 AI 导演配置读取权限；请先登录主 SKU Board" : "暂未读取到 AI 分析模型配置；当前使用本地规则编排", true);
    }
  }

  function compactAnalysisValue(value, limit = 520) {
    if (value == null || value === "") return "—";
    if (typeof value === "string") return value.slice(0, limit);
    try {
      return JSON.stringify(value, null, 2).slice(0, limit);
    } catch (error) {
      return String(value).slice(0, limit);
    }
  }

  function directorAnalysisText(plan = suitePlanCache) {
    if (!plan) return "尚未运行 AI Director 分析";
    const director = plan.director && typeof plan.director === "object" ? plan.director : {};
    const pages = Array.isArray(plan.suitePages) ? plan.suitePages : [];
    const lines = [
      `分析来源：${director.source === "model" ? "AI 模型" : "服务器本地规则"}`,
      `分析模型：${director.model || directorConfig.model || "未配置"}`,
      `Prompt生成：${plan.promptBlueprint?.source === "model" ? `AI从零生成（${plan.promptBlueprint.model || director.promptRewriteModel || "—"} / 指纹 ${plan.promptBlueprint.fingerprint || "—"}）` : "本地规则草稿"}`,
      `产品总结：${director.productSummary || "—"}`,
      `产品视觉 DNA：${compactAnalysisValue(director.productVisualDNA, 700)}`,
      `套图页数：${pages.length}（主图${currentForm?.main || 0} + 详情${currentForm?.detail || 0}）`,
      "页面顺序：",
      ...pages.map((page) => `${page.page || "?"}. ${page.title || page.focusTitle || "未命名"}｜${page.objective || page.focus || "—"}｜日文钩子：${page.headline || page.sellingPoint || "—"}`),
    ];
    if (director.warning) lines.splice(2, 0, `警告：${director.warning}`);
    return lines.join("\n");
  }

  function renderDirectorAnalysis(plan = suitePlanCache) {
    const summary = $("analysis-summary");
    const pageList = $("analysis-page-list");
    const meta = $("analysis-meta");
    if (!summary || !pageList || !meta) return;
    if (!plan) {
      meta.textContent = directorConfig.model ? `等待调用 ${directorConfig.model} 分析` : "尚未运行 GPT‑5.6‑sol 分析";
      summary.innerHTML = `<div class="analysis-empty"><strong>先分析，再生图</strong><small>上传参考图后点击“先用 AI 分析”，可先查看 GPT‑5.6‑sol 对产品、噱头和页面顺序的判断。</small></div>`;
      pageList.innerHTML = "";
      return;
    }
    const director = plan.director && typeof plan.director === "object" ? plan.director : {};
    const pages = Array.isArray(plan.suitePages) ? plan.suitePages : [];
    const model = director.model || directorConfig.model || "未配置";
    const fromModel = director.source === "model";
    meta.textContent = plan.promptBlueprint?.source === "model"
      ? `AI原创整套Prompt · ${plan.promptBlueprint.model || director.promptRewriteModel || model} · 商品指纹 ${plan.promptBlueprint.fingerprint || "—"} · ${pages.length}页`
      : `${fromModel ? "AI 模型分析" : "服务器本地规则"} · ${model} · ${pages.length}页脚本已生成`;
    const dna = compactAnalysisValue(director.productVisualDNA, 680);
    const coverage = compactAnalysisValue(director.sellingPointCoverage, 680);
    summary.innerHTML = [
      `<article class="analysis-summary-card wide"><span>PRODUCT SUMMARY</span><strong>${esc(director.productSummary || "未返回产品总结")}</strong>${director.warning ? `<p class="analysis-warning">${esc(director.warning)}</p>` : ""}</article>`,
      plan.promptBlueprint?.creativeRationale ? `<article class="analysis-summary-card wide"><span>NEW PROMPT ROUTE</span><strong>${esc(plan.promptBlueprint.creativeRationale)}</strong><p>本次只绑定商品：${esc(plan.promptBlueprint.product || currentForm?.product || "当前商品")}</p></article>` : "",
      `<article class="analysis-summary-card"><span>VISUAL DNA</span><p>${esc(dna)}</p></article>`,
      `<article class="analysis-summary-card"><span>SELLING-POINT COVERAGE</span><p>${esc(coverage)}</p></article>`,
    ].join("");
    pageList.innerHTML = pages.map((page, index) => `<article class="analysis-page-card">
      <header><span>${String(page.page || index + 1).padStart(2, "0")}</span><span>${esc(page.role || (index < (currentForm?.main || 0) ? "主图" : "详情图"))}</span></header>
      <strong>${esc(page.title || page.focusTitle || "未命名页面")}</strong>
      <p>${esc(page.objective || page.focus || page.focusDescription || "")}</p>
      <code>${esc(page.headline || page.sellingPoint || "")}</code>
    </article>`).join("");
  }

  function renderGeneratedGallery() {
    const gallery = $("generated-gallery");
    const tabCount = $("result-tab-count");
    if (!gallery) return;
    const materials = [...generatedMaterials.entries()].sort((a, b) => a[0] - b[0]);
    if (tabCount) tabCount.textContent = String(materials.length);
    if (!materials.length) {
      gallery.innerHTML = `<div class="gallery-empty"><span>○</span><strong>还没有成图</strong><small>上传参考图后，点击“生成当前页”或“直接生成整套”</small></div>`;
      return;
    }
    const errors = generationState.errors.length
      ? `<div class="generation-error">${generationState.errors.map((message) => esc(message)).join("<br>")}</div>`
      : "";
    gallery.innerHTML = errors + materials.map(([pageNumber, material]) => {
      const url = material.previewUrl || material.previewDataUrl || material.remoteUrl || "";
      const page = currentPages.find((item) => item.index === Number(pageNumber));
      const label = page ? `${page.section === "main" ? "主图" : "详情"}${String(page.localIndex).padStart(2, "0")}` : `第${pageNumber}页`;
      return `<article class="generated-card"><a href="${esc(url)}" target="_blank" rel="noopener"><img src="${esc(url)}" alt="${esc(label)}"></a><div class="generated-meta"><div><strong>${esc(label)}</strong><small>${esc(page?.title || material.name || "AI 生成")}</small></div><a class="generated-download" href="${esc(url)}" target="_blank" rel="noopener" download>保存</a></div></article>`;
    }).join("");
  }

  async function apiRequest(path, options = {}) {
    const response = await fetch(path, { ...options, credentials: "same-origin" });
    const raw = await response.text();
    let payload = {};
    try { payload = raw ? JSON.parse(raw) : {}; } catch (error) { throw new Error(`服务返回异常（HTTP ${response.status}）`); }
    if (!response.ok || payload.ok === false) {
      const message = typeof payload.error === "string" ? payload.error : payload.error?.message;
      const error = new Error(message || `请求失败（HTTP ${response.status}）`);
      error.status = response.status;
      throw error;
    }
    return payload;
  }

  async function waitForImageJob(payload) {
    let current = payload;
    let attempts = 0;
    while (current?.pending && current.jobId) {
      if (generationAbortController?.signal.aborted) throw new Error("已取消生图");
      if (attempts > 360) throw new Error("生图任务等待超时，请稍后在 SKU Board 中恢复任务");
      await new Promise((resolve) => window.setTimeout(resolve, 2200));
      current = await apiRequest(`/api/sku-board/ai-image-jobs/${encodeURIComponent(current.jobId)}`, { signal: generationAbortController?.signal });
      attempts += 1;
      if ($("generation-detail")) $("generation-detail").textContent = current.message || "远端生图任务处理中…";
    }
    return current;
  }

  function buildLocalSuitePlan(form, suiteCount) {
    const market = MARKET[form.market] || MARKET.JP;
    const pages = [...makeMainPages(form), ...makeDetailPages(form)].slice(0, suiteCount);
    return pages.map((page) => ({
      page: page.index,
      title: page.title,
      role: `${page.section === "main" ? "主图" : "详情图"}${String(page.localIndex).padStart(2, "0")}`,
      objective: page.focus,
      focus: `${page.title}：${page.focus}`,
      focusTitle: page.title,
      focusDescription: page.focus,
      sellingPoint: page.hook,
      evidence: page.evidence,
      scene: (MARKET[form.market] || MARKET.JP).scene,
      pose: page.section === "main" ? `${market.label}本土人物自然使用、手持或展示产品，动作必须符合当前商品的真实使用方式` : "产品特写或与卖点相关的真实使用动作",
      composition: page.section === "main" ? `产品占画面45%至70%，高密度${market.label}电商信息排版，满幅无留白` : "产品局部占主体，搭配2至4个短标签或一个证据模块",
      headline: page.hook,
      size: form.size,
      pageArchetype: page.title,
      impactTreatment: "COD强转化、夸张大数字、静态色带和促销贴纸；保持一个清晰主视觉",
      textPolicy: "requested",
      contentDensity: page.title === "四宫格痛点" ? "structured" : "focused",
    }));
  }

  function buildDirectorSuitePlanFormData(form, suiteCount) {
    const formData = new FormData();
    formData.append("prompt", buildMasterPrompt(form));
    formData.append("suiteBrief", buildSuiteBrief(form));
    formData.append("promptGeneratorInput", JSON.stringify(buildPromptGeneratorInput(form)));
    formData.append("size", form.size);
    formData.append("suiteKey", GENERATION_SUITE_KEY);
    formData.append("suiteCount", String(suiteCount));
    formData.append("mainCount", String(form.main));
    formData.append("detailCount", String(form.detail));
    formData.append("suiteCountry", form.market);
    formData.append("useDirector", "true");
    formData.append("companyEffectMode", "true");
    formData.append("forceReanalyze", "true");
    formData.append("fullPromptRewrite", "true");
    const bindings = buildReferenceBindings(form);
    formData.append("referenceBindings", JSON.stringify(bindings));
    formData.append("referenceUploadCount", String(referenceFiles.length));
    referenceFiles.slice(0, 16).forEach((file, index) => formData.append(`reference${index}`, file, file.name));
    return formData;
  }

  async function ensureSuitePlan(form, options = {}) {
    const suiteCount = generationSuiteCount(form);
    const cacheKey = promptInputFingerprint(form);
    const force = Boolean(options.force);
    if (!force && suitePlanCache && suitePlanCacheKey === cacheKey) return suitePlanCache;
    if (force) {
      suitePlanCache = null;
      suitePlanCacheKey = "";
    }
    if ($("generation-status")) $("generation-status").textContent = directorConfig.enabled && directorConfig.configured ? "GPT‑5.6‑sol 正在从零重写整套 Prompt…" : "正在编译页面脚本…";
    if ($("generation-detail")) $("generation-detail").textContent = directorConfig.enabled && directorConfig.configured
      ? `使用 ${directorConfig.model || "GPT‑5.6‑sol"} 只依据当前商品、卖点、国家与参考图，重新生成总控和全部${suiteCount}页Prompt。`
      : "AI 分析模型未启用，将使用服务器本地规则编排；想用 GPT‑5.6‑sol 请先在 SKU Board 的 AI DIRECTOR 中启用。";
    let remoteError = null;
    try {
      const payload = await apiRequest("/api/sku-board/ai-image-suite-plan-upload", {
        method: "POST",
        body: buildDirectorSuitePlanFormData(form, suiteCount),
        signal: generationAbortController?.signal,
      });
      const pages = Array.isArray(payload.suitePages) ? payload.suitePages : [];
      if (pages.length !== suiteCount) throw new Error("AI 导演返回的页面数量不完整");
      if (directorConfig.enabled && directorConfig.configured && payload.promptBlueprint?.source !== "model") {
        throw new Error("AI Director没有返回当前商品的完整原创Prompt套图");
      }
      suitePlanCache = {
        ...payload,
        suitePages: pages,
        suiteCount: Number(payload.suiteCount) || suiteCount,
        resolvedReferenceBindings: payload.resolvedReferenceBindings || buildReferenceBindings(form),
        director: payload.director || { source: "rules", message: "使用服务器规则编排" },
      };
      suitePlanCacheKey = cacheKey;
      generationState.plan = suitePlanCache;
      renderDirectorAnalysis(suitePlanCache);
      renderMasterPrompt(form, suitePlanCache);
      const source = suitePlanCache.promptBlueprint?.source === "model"
        ? `已由 ${suitePlanCache.promptBlueprint.model || suitePlanCache.director?.promptRewriteModel || directorConfig.model || "GPT‑5.6‑sol"} 从零生成当前商品整套Prompt`
        : suitePlanCache.director?.source === "model"
          ? `已完成 ${suitePlanCache.director.model || directorConfig.model || "GPT‑5.6‑sol"} 分析`
          : "已完成服务器规则编排";
      setDirectorConfigStatus(source + "；现在复制或按逐页脚本生成图片", suitePlanCache.promptBlueprint?.source !== "model");
      return suitePlanCache;
    } catch (error) {
      remoteError = error;
      if (error?.name === "AbortError" || error?.status === 401 || error?.status === 403) throw error;
      if ($("generation-detail")) $("generation-detail").textContent = `AI 分析暂时不可用（${error.message || "服务异常"}），改用本地规则继续生成。`;
    }
    const pages = buildLocalSuitePlan(form, suiteCount);
    if (!pages.length) throw remoteError || new Error("没有可生成的页面计划");
    suitePlanCache = { suitePages: pages, suiteCount, resolvedReferenceBindings: buildReferenceBindings(form), director: { source: "local-rules", message: "AI 导演异常，已使用本地规则编排", warning: remoteError?.message || "" } };
    suitePlanCacheKey = cacheKey;
    generationState.plan = suitePlanCache;
    renderDirectorAnalysis(suitePlanCache);
    renderMasterPrompt(form, suitePlanCache);
    setDirectorConfigStatus(`AI 分析模型暂时不可用，已改用本地规则；${remoteError?.message || "可稍后重试"}`, true);
    return suitePlanCache;
  }

  async function analyzeSuiteOnly() {
    if (generationAbortController || analysisState.running) return;
    const form = readForm();
    currentForm = form;
    analysisState = { running: true, error: "" };
    generationAbortController = new AbortController();
    renderGenerationStatus();
    activateAnalysisTab();
    try {
      const plan = await ensureSuitePlan(form, { force: true });
      render(form);
      renderDirectorAnalysis(plan);
      activateAnalysisTab();
      toast(plan.promptBlueprint?.source === "model"
        ? `已为「${form.product}」重新生成整套Prompt`
        : plan.director?.source === "model"
          ? `已完成 ${plan.director.model || "GPT‑5.6‑sol"} 分析`
          : "已完成本地规则草稿");
    } catch (error) {
      analysisState.error = error.message || "AI 分析失败";
      setDirectorModelDisplay("分析失败", analysisState.error, true);
      setDirectorConfigStatus(analysisState.error, true);
      toast("AI 分析失败，请查看模型状态");
    } finally {
      analysisState.running = false;
      generationAbortController = null;
      renderGenerationStatus();
    }
  }

  function buildGenerationFormData(form, pageNumber, plan, runId) {
    const formData = new FormData();
    const suiteCount = Number(plan.suiteCount) || generationSuiteCount(form);
    const referenceSet = generationReferenceSet(form, plan);
    const generationFiles = referenceSet.files;
    const bindings = referenceSet.bindings.length ? referenceSet.bindings : (plan.resolvedReferenceBindings || buildReferenceBindings(form));
    const productIndexes = bindings.filter((item) => item.role === "product").map((item) => Number(item.index)).filter(Boolean);
    const generationProfile = form.generationProfile || "standard";
    const model = form.model || "gpt-image-2";
    const quality = form.quality || (generationProfile === "fast" ? "medium" : "high");
    formData.append("prompt", buildMasterPrompt(form, plan));
    formData.append("mode", "edit");
    formData.append("model", model);
    formData.append("size", form.size);
    formData.append("quality", quality);
    formData.append("generationProfile", generationProfile);
    formData.append("count", "1");
    formData.append("lockLevel", "strict");
    formData.append("suiteKey", GENERATION_SUITE_KEY);
    formData.append("suiteCount", String(suiteCount));
    formData.append("suiteCountry", form.market);
    formData.append("suiteRunId", runId);
    formData.append("suiteBrief", buildSuiteBrief(form));
    formData.append("suitePlan", JSON.stringify(plan.suitePages || []));
    formData.append("suitePageIndexes", JSON.stringify([pageNumber]));
    formData.append("productReferenceIndexes", JSON.stringify(productIndexes.length ? productIndexes : [1]));
    formData.append("referenceBindings", JSON.stringify(bindings));
    formData.append("referenceUploadCount", String(generationFiles.length));
    generationFiles.forEach((file, index) => formData.append(`reference${index}`, file, file.name));
    return formData;
  }

  async function generateOnePage(form, pageNumber, plan, runId) {
    generationState.active = pageNumber;
    renderGenerationStatus();
    const submitted = await apiRequest("/api/sku-board/ad-launch-ai-image-edit", {
      method: "POST",
      body: buildGenerationFormData(form, pageNumber, plan, runId),
      signal: generationAbortController?.signal,
    });
    const payload = await waitForImageJob(submitted);
    const materials = Array.isArray(payload.materials) ? payload.materials : payload.material ? [payload.material] : [];
    const material = materials.find((item) => Number(item.suitePage) === pageNumber) || materials[0];
    if (!material) throw new Error(`第${pageNumber}页没有返回图片`);
    material.suitePage = pageNumber;
    generatedMaterials.set(pageNumber, material);
    generationState.completed += 1;
    generationState.active = 0;
    render(currentForm);
    activateResultsTab();
  }

  function failedPageNumbers() {
    return [...new Set(generationState.errors
      .map((message) => Number(String(message).match(/第\s*(\d+)\s*页/)?.[1] || 0))
      .filter(Boolean))].sort((a, b) => a - b);
  }

  async function generateImages(mode) {
    if (generationAbortController) return;
    const form = readForm();
    currentForm = form;
    if (!referenceFiles.length) { toast("请先上传至少一张商品参考图"); return; }
    const localPages = currentPages.length ? currentPages : [...makeMainPages(form), ...makeDetailPages(form)];
    const requestedPages = mode === "current"
      ? [selectedPage]
      : mode === "failed"
        ? failedPageNumbers()
        : localPages.map((page) => page.index);
    if (mode === "failed" && !requestedPages.length) {
      toast("当前没有失败页需要补图");
      return;
    }
    generationAbortController = new AbortController();
    generationState = { status: "running", requested: requestedPages.length, completed: 0, active: 0, errors: [], plan: null };
    renderGenerationStatus();
    try {
      const plan = await ensureSuitePlan(form);
      render(form);
      const suiteCount = Number(plan.suiteCount) || generationSuiteCount(form);
      const pages = requestedPages.filter((page) => page >= 1 && page <= suiteCount);
      generationState.requested = pages.length;
      if (!pages.length) throw new Error("当前页码不在生图套图范围内");
      const runId = typeof crypto !== "undefined" && crypto.getRandomValues
        ? Array.from(crypto.getRandomValues(new Uint8Array(6))).map((value) => value.toString(16).padStart(2, "0")).join("")
        : `${Date.now().toString(16)}${Math.random().toString(16).slice(2)}`.replace(/[^a-f0-9]/gi, "").slice(0, 12).padEnd(12, "0");
      let cursor = 0;
      const worker = async () => {
        while (cursor < pages.length) {
          const page = pages[cursor]; cursor += 1;
          try {
            await generateOnePage(form, page, plan, runId);
          } catch (error) {
            if (generationAbortController?.signal.aborted) throw error;
            generationState.errors.push(`第${page}页：${error.message || "生成失败"}`);
            generationState.active = 0;
            renderGenerationStatus();
            renderGeneratedGallery();
          }
        }
      };
      await Promise.all(Array.from({ length: Math.min(3, pages.length) }, () => worker()));
      generationState.status = generationState.completed ? "done" : "error";
    } catch (error) {
      generationState.status = "error";
      if (!generationState.errors.length || generationState.errors[0] !== error.message) generationState.errors.unshift(error.message || "生图失败");
    } finally {
      generationState.active = 0;
      generationAbortController = null;
      renderGenerationStatus();
      renderGeneratedGallery();
      render(currentForm);
      if (generationState.status === "done") toast(`已生成 ${generationState.completed} 张真实图片`);
      else toast("生图未完成，请查看状态提示");
    }
  }

  function activateResultsTab() {
    const tab = document.querySelector('.output-tab[data-tab="results"]');
    if (!tab) return;
    document.querySelectorAll(".output-tab").forEach((item) => item.classList.toggle("active", item === tab));
    document.querySelectorAll(".tab-content").forEach((content) => content.classList.toggle("active", content.id === "tab-results"));
  }

  function activateAnalysisTab() {
    const tab = document.querySelector('.output-tab[data-tab="analysis"]');
    if (!tab) return;
    document.querySelectorAll(".output-tab").forEach((item) => item.classList.toggle("active", item === tab));
    document.querySelectorAll(".tab-content").forEach((content) => content.classList.toggle("active", content.id === "tab-analysis"));
  }

  let promptRefreshTimer = 0;
  function invalidatePromptSuite(nextForm, reason = "input") {
    const hadGeneratedPrompt = Boolean(suitePlanCache);
    suitePlanCache = null;
    suitePlanCacheKey = "";
    generationState.plan = null;
    analysisState.error = "";
    if (hadGeneratedPrompt || generatedMaterials.size) generatedMaterials.clear();
    currentForm = nextForm;
    render(currentForm);
    if (hadGeneratedPrompt && reason !== "silent") {
      setDirectorConfigStatus("商品资料已变化，旧Prompt已失效；点击“AI重新生成整套Prompt”创建当前商品的新版本", true);
    }
  }

  function schedulePromptSuiteInvalidation(reason = "input") {
    window.clearTimeout(promptRefreshTimer);
    promptRefreshTimer = window.setTimeout(() => invalidatePromptSuite(readForm(), reason), 220);
  }

  let currentForm = null;
  document.addEventListener("DOMContentLoaded", () => {
    currentForm = loadDraft();
    render(currentForm);
    $("generate-btn").addEventListener("click", analyzeSuiteOnly);
    $("reset-btn").addEventListener("click", () => {
      generationAbortController?.abort();
      localStorage.removeItem(STORAGE_KEY);
      referenceFiles = [];
      generatedMaterials.clear();
      analysisState = { running: false, error: "" };
      generationState = { status: "idle", requested: 0, completed: 0, active: 0, errors: [], plan: null };
      suitePlanCache = null; suitePlanCacheKey = "";
      currentForm = loadDraft(); render(currentForm); toast("已恢复 Watch4 Pro 示例");
    });
    $("copy-master-btn").addEventListener("click", () => copyText($("master-output").textContent).then(() => toast("总控 Prompt 已复制")));
    $("copy-pages-btn").addEventListener("click", () => copyText(storyboardPages(currentForm).map((page) => page.prompt).join("\n\n")).then(() => toast("逐页 Prompt 已复制")));
    $("download-btn").addEventListener("click", () => { downloadText(currentForm); toast("TXT 已下载"); });
    $("analyze-ai-btn").addEventListener("click", analyzeSuiteOnly);
    $("generate-current-btn").addEventListener("click", () => generateImages("current"));
    $("generate-suite-btn").addEventListener("click", () => generateImages("suite"));
    $("retry-failed-btn").addEventListener("click", () => generateImages("failed"));
    $("cancel-generation-btn").addEventListener("click", () => {
      if (!generationAbortController) return;
      const cancellingAnalysis = analysisState.running;
      generationAbortController.abort();
      if (cancellingAnalysis) {
        analysisState.error = "已停止 AI Director 分析";
        setDirectorConfigStatus(analysisState.error, true);
      } else {
        generationState.status = "error";
        generationState.errors.unshift("已停止当前生图任务；已经返回的成图仍会保留。");
      }
      renderGenerationStatus(); renderGeneratedGallery();
    });
    $("clear-results-btn").addEventListener("click", () => {
      if (!generatedMaterials.size) { toast("当前没有可清空的成图"); return; }
      generatedMaterials.delete(selectedPage);
      render(currentForm);
      toast(`已清空第${selectedPage}页成图`);
    });
    $("copy-analysis-btn").addEventListener("click", () => copyText(directorAnalysisText()).then(() => toast("AI 分析摘要已复制")));
    const fileInput = $("reference-files");
    const dropzone = document.querySelector(".upload-dropzone");
    const acceptReferenceFiles = (files) => {
      referenceFiles = Array.from(files || []).filter((file) => /^image\/(jpeg|png|webp)$/i.test(file.type)).slice(0, 12);
      suitePlanCache = null; suitePlanCacheKey = "";
      if (referenceFiles.length && !generationAbortController) generatedMaterials.clear();
      if (referenceFiles.length && !generationAbortController) generationState = { status: "idle", requested: 0, completed: 0, active: 0, errors: [], plan: null };
      currentForm = readForm();
      render(currentForm);
      if (referenceFiles.length) toast(`已载入 ${referenceFiles.length} 张参考图`);
    };
    fileInput?.addEventListener("change", () => acceptReferenceFiles(fileInput.files));
    dropzone?.addEventListener("dragover", (event) => { event.preventDefault(); dropzone.classList.add("dragover"); });
    dropzone?.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
    dropzone?.addEventListener("drop", (event) => { event.preventDefault(); dropzone.classList.remove("dragover"); acceptReferenceFiles(event.dataTransfer.files); });
    const promptSourceIds = [
      "product-name", "target-market", "hook-intensity", "main-count", "detail-count", "canvas-size",
      "reference-map", "selling-points", "discount", "sale-price", "cod-text", "deadline",
      "allow-promo", "allow-medical", "style-notes", "avoid-notes",
    ];
    promptSourceIds.forEach((id) => {
      const input = $(id);
      if (!input) return;
      input.addEventListener(input.matches("select,input[type=checkbox]") ? "change" : "input", () => schedulePromptSuiteInvalidation("input"));
    });
    document.querySelectorAll(".small-copy-btn[data-copy-target]").forEach((button) => button.addEventListener("click", () => copyText($(button.dataset.copyTarget).textContent).then(() => toast("已复制"))));
    document.querySelectorAll(".output-tab").forEach((tab) => tab.addEventListener("click", () => {
      document.querySelectorAll(".output-tab").forEach((item) => item.classList.toggle("active", item === tab));
      document.querySelectorAll(".tab-content").forEach((content) => content.classList.toggle("active", content.id === `tab-${tab.dataset.tab}`));
    }));
    ["product-name", "target-market", "hook-intensity", "main-count", "detail-count", "canvas-size", "reference-map", "selling-points", "discount", "sale-price", "cod-text", "deadline", "style-notes", "avoid-notes", "allow-promo", "allow-medical", "render-model", "render-quality", "render-profile"].forEach((id) => {
      const identityField = ["product-name", "target-market", "main-count", "detail-count", "canvas-size", "reference-map", "selling-points", "style-notes", "avoid-notes"].includes(id);
      const update = () => {
        currentForm = readForm(); suitePlanCache = null; suitePlanCacheKey = "";
        if (identityField && !generationAbortController) {
          generatedMaterials.clear();
          generationState = { status: "idle", requested: 0, completed: 0, active: 0, errors: [], plan: null };
        }
        render(currentForm);
      };
      $(id).addEventListener("input", update);
      $(id).addEventListener("change", update);
    });
    loadImageConfig();
  });
})();
