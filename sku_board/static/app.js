const state = {
  items: [],
  filters: { q: "", status: "", owner: "", profit: "", action: "" },
  ownersLoaded: false,
  selected: null,
  view: "board",
  auth: {
    user: null,
    users: [],
    roles: {},
    loaded: false,
  },
  metaCredentials: {
    loaded: false,
    loading: false,
    credentials: [],
    bindings: [],
    assets: [],
    assetDetails: [],
    users: [],
    summary: {},
    oauthConfigured: false,
    oauthReady: false,
    oauthMode: "unconfigured",
    bindingCredentialId: "",
    bindingBusinessId: "",
    bindingAccountId: "",
    systemWizard: { sourceCredentialId: "", businessId: "", accountIds: [], pageIds: [] },
  },
  shopline: {
    loaded: false,
    loading: false,
    products: [],
    source: { mode: "unknown", error: "" },
    connector: { missing: [] },
    selected: new Set(),
    query: "",
    status: "active",
  },
  designTasks: {
    loaded: false,
    tasks: [],
    summary: {},
    options: {},
    canCreate: false,
    filters: { status: "", owner: "", q: "" },
  },
  facebookBinding: {
    loaded: false,
    loading: false,
    sku: "",
    accounts: [],
    campaigns: [],
    query: "",
    range: "last_7d",
  },
  adLaunches: {
    loaded: false,
    loading: false,
    launches: [],
    summary: {},
    options: { products: [], accounts: [], campaigns: [], adsets: [], ctas: {}, defaults: {} },
    material: null,
    materialMode: "single_image",
    filters: { q: "", range: "last_7d" },
    step: 0,
    saving: false,
  },
  metaAnalysis: {
    loaded: false,
    loading: false,
    payload: null,
    filters: { range: "last_7d", action: "", q: "", businessId: "", accountId: "" },
    settings: { usePlatformPurchase: true, targetCpa: "", stopSpend: 5, stopClicks: 30 },
  },
  aiImages: {
    configLoaded: false,
    configLoading: false,
    material: null,
    materials: [],
    previewDataUrl: "",
    previewDataUrls: [],
    prompt: "",
    productSku: "",
    mode: "text",
    lockLevel: "strict",
    model: "gpt-image-2",
    size: "1024x1024",
    quality: "auto",
    count: 1,
    suiteKey: "",
    suiteCount: 0,
    suiteCountry: "KR",
    suiteRunId: "",
    suitePlanVersion: "",
    suitePages: [],
    directorMode: "fast",
    generationProfile: "standard",
    remoteSummary: {},
    recoveryLoading: false,
    settingsOpen: false,
    activeId: "",
    conversations: [],
    referenceImages: [],
    maskImage: null,
    health: {
      status: "unknown",
      message: "尚未检测服务",
      latencyMs: 0,
      checkedAt: "",
      baseUrl: "",
      loading: false,
    },
    director: {
      loaded: false,
      loading: false,
      saving: false,
      testing: false,
      enabled: false,
      configured: false,
      baseUrl: "",
      model: "gpt-5.6-terra",
      timeout: 60,
      visionEnabled: true,
      openImagePromptsEnabled: true,
      reviewEnabled: true,
      reviewThreshold: 78,
      apiKeyConfigured: false,
      secureTransport: false,
      status: "unknown",
      message: "",
      formDirty: false,
    },
  },
};

const AD_LAUNCH_STEPS = ["campaign", "audience", "creative", "review"];
const META_ANALYSIS_ACTION_LABELS = {
  keep_test_order_signal: "购买信号",
  scale_observe: "放量观察",
  keep_small_run: "保留小跑",
  copy_variant: "复制变体",
  immediate_close: "立即关闭",
  pause_observe: "暂停观察",
  fix_payment: "修复支付",
  product_stop_test: "产品停止测试",
  ignore_no_spend: "无消耗忽略",
  watch: "继续观察",
};
const AI_IMAGE_SIZE_PRESETS = [
  { value: "1024x1024", label: "1:1", hint: "方图" },
  { value: "1024x1536", label: "2:3", hint: "竖版" },
  { value: "1536x1024", label: "3:2", hint: "横版" },
  { value: "1024x1792", label: "9:16", hint: "Reels" },
  { value: "1792x1024", label: "16:9", hint: "横屏" },
  { value: "768x1024", label: "3:4", hint: "商品图" },
  { value: "1024x768", label: "4:3", hint: "场景图" },
  { value: "750x1000", label: "3:4", hint: "COD国家落地页" },
  { value: "750x150", label: "750×150", hint: "COD促销横条" },
  { value: "750x100", label: "750×100", hint: "COD价格横条" },
  { value: "970x600", label: "970:600", hint: "Amazon A+" },
  { value: "1200x1200", label: "1:1", hint: "乐天商品图" },
  { value: "1500x2000", label: "3:4", hint: "落地页" },
  { value: "auto", label: "auto", hint: "自动" },
];
const AI_IMAGE_COUNT_PRESETS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
const AI_IMAGE_COD_COUNT_OPTIONS = [8, 12, 16, 20, 24, 30];
const AI_IMAGE_COD_DETAIL_COUNT_OPTIONS = [12, 16, 20, 22];
const AI_IMAGE_COD_HOOK_TYPES = [
  { key: "hook", label: "单独噱头", instruction: "Create a pure hook image with one oversized product or result visual and one short localized hook headline. Do not add a price strip, discount badge or promotion module." },
  { key: "promotion", label: "促销图", instruction: "Create a strong local-market promotion image with the product as the largest subject, one campaign headline and one bold promotion badge or activity block. Use only promotion wording supplied by the user." },
  { key: "priceBar", label: "价格条", instruction: "Create one full-width localized ecommerce price bar, not a poster containing a small bar. Render the exact currency, original price, sale price and discount supplied by the user and do not invent missing numbers. Keep every glyph, currency mark, full price, quantity label, product and action cue completely visible. Use a 12-pixel top-and-bottom safe zone on 750x100 and an 18-pixel safe zone on 750x150. Nothing may touch, cross or disappear beyond the canvas edges. The main sale-price numerals should occupy 38-52% of the usable canvas height and the product/result visual 62-78%, leaving enough room for complete display. Fill the entire width with deliberate design and strong contrast." },
  { key: "discount", label: "折扣徽章", instruction: "Create one bold discount-badge image. Use the exact OFF percentage or discount wording from the user prompt, keep one badge only, and make the product/result larger than the badge." },
  { key: "comparison", label: "痛点对比", instruction: "Create one dramatic two-panel pain-point or before-and-after comparison using the same subject, camera, scale and condition. Compare only the single difference supplied by the user." },
  { key: "effect", label: "效果卖点", instruction: "Create one high-impact product-result image focused on the supplied effect selling point, using a dominant realistic result, local use scene or product-specific macro proof." },
];
const AI_IMAGE_STATE_STORAGE_KEY = "sosove.sku-board.ai-image-state.v1";
const AI_IMAGE_STATE_STORAGE_VERSION = 1;
const AI_IMAGE_STATE_MAX_CONVERSATIONS = 12;
const AI_IMAGE_SUITE_WORKER_COUNT = 4;
const AI_IMAGE_SUITE_PAGE_REFERENCE_LIMIT = 5;
const AI_IMAGE_SUITE_HERO_REFERENCE_LIMIT = 5;
const AI_IMAGE_SUITE_MAX_RETRIES = 2;
const AI_IMAGE_SUITE_AUTO_RETRY_CYCLES = 2;
const AI_IMAGE_SUITE_REVIEW_BATCH_SIZE = 4;
const AI_IMAGE_SUITE_REVIEW_WORKER_COUNT = 2;
const AI_IMAGE_SUITE_REVIEW_MAX_RETRIES = 1;
const AI_IMAGE_JP_GENERATION_REFERENCE_ROLES = new Set(["product", "detail", "usage", "person"]);
const AI_IMAGE_REFERENCE_ROLES = [
  { key: "product", label: "主商品", instruction: "Use as the exact product identity source." },
  { key: "detail", label: "产品细节", instruction: "Use only for observable construction, texture and detail evidence." },
  { key: "usage", label: "使用方式", instruction: "Use only for the natural operation, wearing or usage action." },
  { key: "scene", label: "场景参考", instruction: "Use only for environment, location, props, lighting and atmosphere; do not copy its product or clothing." },
  { key: "person", label: "人物参考", instruction: "Use as the exact identity source for face, hair, age impression, skin tone and body proportions. Clothing, accessories, pose, crop and background may change only when the current user prompt explicitly requests it." },
  { key: "bag", label: "包袋参考", instruction: "Use as the exact bag source. Preserve its shape, material, color, hardware, strap and visible construction unless the current user prompt explicitly changes one attribute." },
  { key: "hat", label: "帽子参考", instruction: "Use as the exact hat source. Preserve its shape, material, brim, crown and construction; apply an explicitly requested color change without redesigning it." },
  { key: "shoes", label: "鞋履参考", instruction: "Use as the exact shoes source. Preserve shoe category, silhouette, color, sole, laces, material and construction." },
  { key: "jewelry", label: "首饰参考", instruction: "Use as the exact jewelry source. Preserve its type, scale, shape, material, color and wearing position." },
  { key: "accessory", label: "穿搭配饰", instruction: "Use as the exact requested styling item source, such as glasses, belt or scarf. Preserve the item's visible identity and place it naturally on the model." },
  { key: "layout", label: "排版风格", instruction: "Use only for composition, spacing, palette and typography rhythm." },
  { key: "styleSet", label: "系列风格参考", instruction: "Use only for the full-page visual system: palette, headline scale, information density, module shapes, callout rhythm, image-to-text ratio, macro or result presentation and cross-page pacing. Do not copy its product, people, text, logos, claims, badges or certifications." },
  { key: "package", label: "包装与配件", instruction: "Use only for confirmed packaging and accessories. In the 模特换装/搭配 template, an item explicitly named by filename in the current user prompt is an exact styling source and must be worn or carried as requested." },
];
const AI_IMAGE_DIRECTOR_STAGES = [
  { key: "cache", label: "读取产品缓存" },
  { key: "analysis", label: "分析产品图与卖点" },
  { key: "storyboard", label: "编排平台分镜" },
  { key: "validation", label: "校验导演脚本" },
  { key: "complete", label: "完成" },
];
const AI_IMAGE_DIRECTOR_MODES = [
  { key: "fast", label: "极速生成", hint: "分析后直接出图" },
  { key: "review", label: "审核方案", hint: "确认分镜后出图" },
];
const AI_DIRECTOR_MODELS = ["gpt-5.6-terra", "gpt-5.6-sol"];
const AI_IMAGE_GENERATION_PROFILES = [
  { key: "fast", label: "极速", hint: "最多8路智能并发 · 中质 · 跳过质检", workers: 8, perNode: 3, quality: "medium", review: "off", maxRetries: 1, autoRetryCycles: 1 },
  { key: "standard", label: "标准", hint: "最多6路智能并发 · 高质 · 重点页质检", workers: 6, perNode: 2, quality: "high", review: "key", maxRetries: 2, autoRetryCycles: 1 },
  { key: "quality", label: "精审", hint: "最多4路稳态并发 · 高质 · 全套质检", workers: 4, perNode: 2, quality: "high", review: "all", maxRetries: 2, autoRetryCycles: 2 },
];
const AI_IMAGE_SUITE_CONFIGS = {
  "jp-landing-page-25": {
    key: "jp-landing-page-25",
    count: 25,
    size: "1500x2000",
    unit: "页",
    label: "日本产品落地页 25图",
    planTitle: "日本产品落地页 25图品牌导演脚本",
    planHint: "创意总监模式：先成像、三层读图、加载日本市场调研，再为固定10张主图+15张详情图生成逐页摄影brief与人物硬约束",
    templateKey: "landing",
    planVersion: "director-v24-company-photography-density",
    marketResearchVersion: "jp-market-research-2026-07-30-v1",
    promptPlaceholder: "填写产品名称、全部颜色/规格、3个核心卖点、5个子卖点和特殊要求；系统会分析全部商品图、模特图与版式图并生成固定25张日本落地页",
    resultClass: "landing",
    anchorPrefix: "landing-page",
    sizeLocked: true,
    monitor: {
      eyebrow: "JAPAN LANDING DIRECTOR",
      ariaLabel: "日本落地页导演监控",
      description: "监控10张主图、15张详情图、三层参考分析、日本市场调研、先成像后落字、人物硬约束、完整Prompt送达与本土化质检。",
      planLabel: "10 主图 + 15 详情",
      sizeLabel: "落地页尺寸",
      sizeHint: "1500×2000 竖版画布自动锁定",
      complianceLabel: "日本落地页规则",
      complianceHint: "少·大·准日文、简单手势、真实肤质、精确商品",
    },
  },
  "amazon-jp-aplus-9": {
    key: "amazon-jp-aplus-9",
    count: 9,
    size: "970x600",
    unit: "图",
    label: "Amazon日本站 A+ 9图",
    planTitle: "Amazon A+ 9图导演脚本",
    planHint: "根据当前产品动态生成横版卖点、结构、场景、规格与维护模块",
    templateKey: "amazonAplus",
    planVersion: "amazon-aplus-v7-all-optimization",
    promptPlaceholder: "填写当前产品名称、主卖点、次卖点、规格和特殊要求；系统会动态生成 9 张 Amazon日本站 A+ 模块图",
    resultClass: "amazon",
    anchorPrefix: "amazon-aplus",
    sizeLocked: true,
    monitor: {
      eyebrow: "AMAZON A+ DIRECTOR",
      ariaLabel: "Amazon A+ 导演监控",
      description: "监控 9 模块完整度、视觉一致性与 Amazon A+ 生成规则。",
      sizeLabel: "A+ 尺寸",
      sizeHint: "横版画布自动锁定",
      complianceLabel: "A+ 合规规则",
      complianceHint: "禁价格、评价与 Amazon UI",
    },
  },
  "rakuten-jp-product-9": {
    key: "rakuten-jp-product-9",
    count: 9,
    size: "1200x1200",
    unit: "图",
    label: "乐天日本站 9图",
    planTitle: "乐天日本站 9图导演脚本",
    planHint: "根据当前产品动态生成方图卖点、结构、场景、规格与维护内容",
    templateKey: "rakutenSuite",
    planVersion: "rakuten-director-v6-all-optimization",
    promptPlaceholder: "填写当前产品名称、主卖点、次卖点、规格和特殊要求；系统会动态生成 9 张乐天日本站商品图",
    resultClass: "rakuten",
    anchorPrefix: "rakuten-product",
    sizeLocked: true,
    monitor: {
      eyebrow: "RAKUTEN JP DIRECTOR",
      ariaLabel: "乐天日本站导演监控",
      description: "监控 9 张商品图完整度、视觉一致性与乐天内容规则。",
      sizeLabel: "乐天尺寸",
      sizeHint: "1200×1200 方图自动锁定",
      complianceLabel: "乐天内容规则",
      complianceHint: "禁虚假价格、排名与乐天 UI",
    },
  },
  "cod-country-landing-30": {
    key: "cod-country-landing-30",
    count: 30,
    size: "750x1000",
    unit: "图",
    label: "COD国家落地页 30图",
    planTitle: "COD国家落地页 30图导演脚本",
    planHint: "按参考落地页逻辑生成一图一卖点、一图一效果的 8 张主图与 22 张详情图",
    templateKey: "codKorea",
    planVersion: "cod-country-v18-all-optimization",
    promptPlaceholder: "填写当前产品名称、主卖点、次卖点和特殊要求；系统会结合产品图按所选国家生成8张主图与22张详情图",
    resultClass: "cod-country",
    anchorPrefix: "cod-country-landing",
    sizeLocked: true,
    countConfigurable: true,
    countOptions: AI_IMAGE_COD_COUNT_OPTIONS,
    monitor: {
      eyebrow: "COUNTRY COD DIRECTOR",
      ariaLabel: "COD国家落地页导演监控",
      description: "监控原始卖点视觉化、颜色/规格覆盖、8 张主图、22 张详情图、场景机位去重与国家本土化规则。",
      planLabel: "8 主图 + 22 详情",
      sizeLabel: "COD 尺寸",
      sizeHint: "750×1000 竖图自动锁定",
      complianceLabel: "国家落地页规则",
      complianceHint: "原始卖点直接进入夸张视觉演绎，覆盖全部颜色规格、场景机位去重",
    },
  },
  "cod-country-detail-12": {
    key: "cod-country-detail-12",
    count: 22,
    size: "750x1000",
    unit: "图",
    label: "COD详情图 22张",
    planTitle: "COD详情图 22张导演脚本",
    planHint: "促销→背书→痛点→全面海报→主卖点→次卖点→多角度/场景→好评→收尾",
    templateKey: "codDetail",
    planVersion: "cod-detail-v13-all-optimization",
    promptPlaceholder: "填写当前产品名称、全部颜色/规格、主卖点、次卖点、使用效果和背书；系统会按品类与国家生成动态COD详情图",
    resultClass: "cod-country",
    anchorPrefix: "cod-country-detail",
    sizeLocked: true,
    countConfigurable: true,
    countOptions: AI_IMAGE_COD_DETAIL_COUNT_OPTIONS,
    monitor: {
      eyebrow: "COUNTRY COD DETAIL DIRECTOR",
      ariaLabel: "COD详情图导演监控",
      description: "监控原始卖点视觉化、颜色/规格覆盖、动态详情序列、促销、背书、主次卖点、场景机位去重与国家本土化规则。",
      planLabel: "动态详情图 · 含促销、背书与好评",
      sizeLabel: "详情图尺寸",
      sizeHint: "750×1000 竖图自动锁定",
      complianceLabel: "COD详情图规则",
      complianceHint: "原始卖点直接进入夸张视觉演绎，覆盖全部颜色规格、场景机位去重",
    },
  },
};
const AI_IMAGE_SUITE_KEY_ALIASES = {
  "jp-landing-page-10": "jp-landing-page-25",
  "jp-landing-page-32": "jp-landing-page-25",
  "amazon-jp-aplus-7": "amazon-jp-aplus-9",
  "cod-kr-landing-30": "cod-country-landing-30",
};
const AI_IMAGE_COD_COUNTRIES = [
  { value: "KR", label: "韩国", language: "韩文" },
  { value: "JP", label: "日本", language: "日文" },
  { value: "DE", label: "德国", language: "德语" },
  { value: "HU", label: "匈牙利", language: "匈牙利语" },
  { value: "PL", label: "波兰", language: "波兰语" },
  { value: "ES", label: "西班牙", language: "西班牙语" },
  { value: "MX", label: "墨西哥", language: "西班牙语" },
  { value: "FR", label: "法国", language: "法语" },
  { value: "CZ", label: "捷克", language: "捷克语" },
  { value: "TW", label: "台湾", language: "繁体中文" },
  { value: "HK", label: "香港", language: "香港繁体中文" },
  { value: "TH", label: "泰国", language: "泰文" },
  { value: "VN", label: "越南", language: "越南文" },
  { value: "MY", label: "马来西亚", language: "马来文" },
  { value: "SG", label: "新加坡", language: "英文" },
  { value: "PH", label: "菲律宾", language: "英文" },
  { value: "ID", label: "印度尼西亚", language: "印尼文" },
];
let aiImageAccountRefreshPromise = null;
let aiImageRecoveryTimer = null;
let aiImageGenerationAbortController = null;
let aiImageGenerationStartedAt = 0;
const AI_IMAGE_MODES = [
  { key: "text", label: "文生图", hint: "文字创作" },
  { key: "edit", label: "参考图翻新", hint: "锁定商品" },
  { key: "inpaint", label: "局部重绘", hint: "原图 + 蒙版" },
  { key: "compose", label: "多图合成", hint: "2 张以上参考" },
];
const AI_IMAGE_PROMPT_TEMPLATES = [
  { key: "main", label: "日系穿搭广告", size: "1024x1536", count: 4 },
  { key: "scene", label: "非白底场景", size: "1024x1536", count: 4 },
  { key: "model", label: "模特上身", size: "1024x1536", count: 4 },
  { key: "virtualTryOn", label: "模特换装/搭配", size: "1024x1536", count: 1, mode: "compose" },
  { key: "poster", label: "Rakuten 单张海报", size: "1024x1536", count: 2 },
  { key: "landing", label: "日本产品落地页 25图", size: "1500x2000", count: 25, mode: "edit", suiteKey: "jp-landing-page-25" },
  { key: "amazonAplus", label: "Amazon A+专区", size: "970x600", count: 9, mode: "edit", suiteKey: "amazon-jp-aplus-9" },
  { key: "rakutenSuite", label: "乐天专区", size: "1200x1200", count: 9, mode: "edit", suiteKey: "rakuten-jp-product-9" },
  { key: "codKorea", label: "COD国家专区", size: "750x1000", count: 30, mode: "edit", suiteKey: "cod-country-landing-30" },
  { key: "codDetail", label: "COD详情图", size: "750x1000", count: 22, mode: "edit", suiteKey: "cod-country-detail-12" },
  { key: "codHook", label: "COD噱头生图", size: "750x1000", count: 1, mode: "text" },
  { key: "facebook", label: "FB 投放主图", size: "1024x1024", count: 4 },
  { key: "detail", label: "商品细节", size: "1024x1024", count: 3 },
  { key: "reels", label: "9:16封面", size: "1024x1792", count: 4 },
  { key: "refresh", label: "参考图翻新", size: "1024x1536", count: 2, mode: "edit" },
  { key: "inpaint", label: "局部换景", size: "1024x1536", count: 2, mode: "inpaint" },
  { key: "compose", label: "多图搭配", size: "1024x1536", count: 2, mode: "compose" },
];
const AI_IMAGE_LOCK_LEVELS = [
  { key: "standard", label: "标准", hint: "允许轻微优化", instruction: "Preserve the garment category, main color, print and overall silhouette." },
  { key: "strict", label: "严格", hint: "锁定版型细节", instruction: "Preserve the exact garment category, silhouette, cut, proportions, color, print, pattern, fabric appearance, neckline, sleeve length, closures, seams, pockets, hem and visible branding. Do not redesign the garment." },
  { key: "exact", label: "完全锁定", hint: "商品优先", instruction: "Reproduce the product as faithfully as possible. Product identity overrides scene, pose and styling instructions. Keep every visible garment feature unchanged." },
];
const AI_IMAGE_NO_ADDED_MARKS_RULE = "Do not add a store logo, corner bug, watermark, signature, creator credit, source label, platform UI, QR code or any other branding to the artwork. Never render SOSOVE, SKU BOARD, Dakin AI, ChatGPT, OpenAI, GPT-image, a model name or a backend/service name anywhere in the layout. Only retain a wordmark when those exact letters are physically printed, engraved or attached to the reference product; keep it on the product only and never repeat it as page branding.";
const AI_IMAGE_SKILL_FALLBACK = {
  id: "gpt-image2-sosove",
  name: "GPT-Image2 SOSOVE",
  version: "内置",
  loaded: false,
  defaults: { lockLevel: "strict", templateKey: "main", size: "1024x1536" },
  modes: AI_IMAGE_MODES,
  templates: AI_IMAGE_PROMPT_TEMPLATES,
  lockLevels: AI_IMAGE_LOCK_LEVELS,
  global: {},
};
const AI_IMAGE_RESULT_TAGS = [
  { key: "ready", label: "可投放" },
  { key: "revise", label: "需修改" },
  { key: "reject", label: "废图" },
  { key: "main", label: "主图" },
  { key: "detail", label: "细节图" },
  { key: "poster", label: "海报图" },
  { key: "cover", label: "视频封面" },
];
const AD_LAUNCH_GENDER_LABELS = { all: "全部", male: "男", female: "女" };
const AD_LAUNCH_PLACEMENT_LABELS = {
  facebook_feed: "Facebook Feed",
  instagram_feed: "Instagram Feed",
  instagram_reels: "Instagram Reels",
  stories: "Stories",
  audience_network: "Audience Network",
};
const AD_LAUNCH_MATERIAL_MODES = {
  single_image: {
    label: "单图",
    accept: "image/*",
    type: "image",
    guidance: ["推荐长宽比：1:1", "推荐尺寸：1080 x 1080 像素", "最小尺寸：600 x 600 像素", "图片文字内容不超过 20% 效果更佳"],
  },
  carousel: {
    label: "轮播图",
    accept: "image/*",
    type: "image",
    guidance: ["建议上传方图素材，可连续保存多条草稿", "推荐尺寸：1080 x 1080 像素", "每张图突出一个卖点或一个搭配场景"],
  },
  video: {
    label: "视频",
    accept: "video/*",
    type: "video",
    guidance: ["推荐比例：9:16 或 1:1", "建议前 3 秒出现上身效果或核心痛点", "支持 mp4 / mov / webm"],
  },
  post: {
    label: "现有帖子",
    accept: "image/*,video/*",
    type: "post",
    guidance: ["可上传现有帖子的素材版本", "保存草稿后仍会按素材广告创建", "后续可继续接入 Meta 帖子 ID"],
  },
  dynamic: {
    label: "动态广告",
    accept: "image/*,video/*",
    type: "dynamic",
    guidance: ["适合商品目录或多素材测试", "当前会保存为素材草稿", "开启多素材广告可批量生成多个草稿"],
  },
};

const $ = (selector) => document.querySelector(selector);
const tbody = $("#sku-tbody");
const drawer = $("#detail-drawer");
const toast = $("#toast");

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function money(value) {
  const n = Number(value || 0);
  const sign = n < 0 ? "-" : "";
  return `${sign}$${Math.abs(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function num(value, digits = 0) {
  return Number(value || 0).toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function sellingConfidenceLabel(value) {
  if (value === "high") return "高";
  if (value === "medium") return "中";
  if (value === "low") return "低";
  return "";
}

function isAutoSelling(selling = {}) {
  return selling.source === "shopline_auto";
}

function sellingAutoBadge(selling = {}) {
  if (!isAutoSelling(selling)) return "";
  const confidence = sellingConfidenceLabel(selling.confidence);
  return `<span class="selling-auto-badge" title="由商品标题、分类、标签和描述自动识别">自动识别${confidence ? ` · ${confidence}` : ""}</span>`;
}

function sellingSignalTags(selling = {}) {
  const signals = Array.isArray(selling.matchedSignals) ? selling.matchedSignals.slice(0, 3) : [];
  return signals.map((signal) => `<span class="selling-signal">${esc(signal)}</span>`).join("");
}

function sellingPointTags(points = []) {
  return points.map((point) => `<span class="tag selling-point-tag">${esc(point)}</span>`).join("");
}

function pct(done, total) {
  if (!total) return 0;
  return Math.max(0, Math.min(100, Math.round((Number(done || 0) / Number(total || 1)) * 100)));
}

function toneClass(tone) {
  if (tone === "good") return "good";
  if (tone === "danger") return "danger";
  if (tone === "warn") return "warn";
  if (tone === "info") return "info";
  return "muted";
}

function rowTone(item) {
  const type = item.diagnosis?.primary?.type;
  if (type === "stop" || type === "loss") return "is-danger";
  if (type === "scale") return "is-good";
  if (["material", "refresh", "creative", "landing"].includes(type)) return "is-warn";
  return "";
}

function buildQuery() {
  const params = new URLSearchParams();
  Object.entries(state.filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  return params.toString();
}

function exportCsv() {
  const query = buildQuery();
  const anchor = document.createElement("a");
  anchor.href = `/api/sku-board/export.csv${query ? `?${query}` : ""}`;
  anchor.download = "sku-board-export.csv";
  anchor.rel = "noopener";
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  showToast("CSV 已开始导出");
}

function productPrice(product) {
  const currency = product.currency || "JPY";
  const price = Number(product.price || 0);
  return `${currency} ${price.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
}

function isAdmin() {
  return state.auth.user?.role === "admin";
}

function roleLabel(role) {
  return state.auth.roles?.[role] || { admin: "管理员", ops: "运营", selection: "选品", designer: "设计", customer: "客户" }[role] || role || "未知";
}

function roleOptions(selected = "designer") {
  const roles = Object.keys(state.auth.roles || {}).length
    ? state.auth.roles
    : { admin: "管理员", ops: "运营", selection: "选品", designer: "设计", customer: "客户" };
  return Object.entries(roles)
    .map(([value, label]) => `<option value="${esc(value)}" ${value === selected ? "selected" : ""}>${esc(label)}</option>`)
    .join("");
}

function shortDate(value) {
  if (!value) return "暂无";
  return String(value).replace("T", " ").slice(0, 16);
}

function designAssignableUsers() {
  return (state.auth.users || []).filter((user) => user.active !== false && ["admin", "ops", "designer"].includes(user.role));
}

function designOwnerOptions(currentOwner) {
  const users = designAssignableUsers();
  const current = currentOwner || "未分配";
  const hasCurrent = users.some((user) => user.name === current);
  const leading = hasCurrent ? "" : `<option value="${esc(current)}">${esc(current)}</option>`;
  return `${leading}${users
    .map((user) => `<option value="${esc(user.name)}" ${user.name === current ? "selected" : ""}>${esc(user.name)} · ${esc(user.roleLabel || user.role)}</option>`)
    .join("")}`;
}

function isDesignTaskCreator() {
  return ["admin", "selection"].includes(state.auth.user?.role);
}

function isDesignTaskManager() {
  return ["admin", "ops", "selection"].includes(state.auth.user?.role);
}

function canManageFacebookAds() {
  return ["admin", "ops", "selection"].includes(state.auth.user?.role);
}

function canUseAiImages() {
  return ["admin", "ops", "selection", "designer", "customer"].includes(state.auth.user?.role);
}

function facebookBinding(ad = {}) {
  return ad.facebookBinding && typeof ad.facebookBinding === "object" ? ad.facebookBinding : {};
}

function hasFacebookBinding(ad = {}) {
  const binding = facebookBinding(ad);
  return Boolean(binding.accountId && (binding.campaignId || binding.campaignName));
}

function facebookBindingText(ad = {}) {
  const binding = facebookBinding(ad);
  if (!hasFacebookBinding(ad)) return "未绑定系列";
  const account = binding.accountName || binding.accountId || "广告户";
  const campaign = binding.campaignName || binding.campaignId || "系列";
  return `${account} / ${campaign}`;
}

function facebookSourceText(ad = {}) {
  const source = ad.source || {};
  if (source.type !== "facebook_api") return "";
  const matched = source.matchedAds ? ` · ${source.matchedAds} 条广告` : "";
  const range = source.rangeLabel || source.range || "FB";
  return `${range}${matched}`;
}

function mapOptions(map = {}, selected = "", fallback = "") {
  const entries = Object.entries(map);
  const base = fallback ? `<option value="">${esc(fallback)}</option>` : "";
  return `${base}${entries
    .map(([value, label]) => `<option value="${esc(value)}" ${value === selected ? "selected" : ""}>${esc(label)}</option>`)
    .join("")}`;
}

function userOptions(users = [], selected = "", fallback = "请选择") {
  return `<option value="">${esc(fallback)}</option>${users
    .map((user) => `<option value="${esc(user.username)}" ${user.username === selected ? "selected" : ""}>${esc(user.name)} · ${esc(user.roleLabel || user.role)}</option>`)
    .join("")}`;
}

function productOptions(products = [], selected = "") {
  return `<option value="">不关联商品</option>${products
    .map((item) => `<option value="${esc(item.sku)}" ${item.sku === selected ? "selected" : ""}>${esc(item.title)} · ${esc(item.sku)}</option>`)
    .join("")}`;
}

function renderAuth() {
  const user = state.auth.user;
  $("#login-open-btn").hidden = Boolean(user);
  $("#auth-user-chip").hidden = !user;
  $("#logout-btn").hidden = !user;
  $("#auth-user-chip").textContent = user ? `${user.name} · ${user.roleLabel || user.role}` : "";
  renderLoginUsers();
  renderDashboardGate();
  renderAccountPanel();
  renderMetaCredentialPanel();
  renderDesignTaskPanel();
  renderAdLaunchPanel();
  renderAiImagePanel();
}

function clearBoardData() {
  state.items = [];
  state.selected = null;
  $("#summary-main").textContent = "-";
  $("#summary-count").textContent = "登录后查看";
  $("#summary-spend").textContent = "-";
  $("#summary-profit").textContent = "-";
  $("#summary-profit").style.color = "";
  $("#summary-roas").textContent = "ROAS -";
  $("#summary-tasks").textContent = "-";
  $("#summary-materials").textContent = "素材缺口 -";
  $("#summary-refresh").textContent = "-";
  $("#summary-feedback").textContent = "反馈缺失 -";
  $("#filtered-count").textContent = "-";
  $("#source-line").textContent = "请先登录";
  $("#insight-headline").textContent = "登录后查看智能建议。";
  $("#insight-grid").innerHTML = "";
  tbody.innerHTML = `<tr><td colspan="10"><div class="empty-state">请先登录后查看看板信息</div></td></tr>`;
  $("#material-kpis").innerHTML = "";
  $("#material-review-list").innerHTML = emptyCard("请先登录后查看素材复盘");
  $("#feedback-kpis").innerHTML = "";
  $("#feedback-stream").innerHTML = emptyCard("请先登录后查看投放反馈");
  $("#feedback-watch-list").innerHTML = "";
  $("#task-kpis").innerHTML = "";
  $("#task-suggestion-list").innerHTML = emptyCard("请先登录后查看系统建议");
  $("#task-open-list").innerHTML = "";
  $("#task-done-list").innerHTML = "";
  $("#task-priority-list").innerHTML = "";
}

function renderDashboardGate() {
  const loggedIn = Boolean(state.auth.user);
  const loginGate = $("#dashboard-login-required");
  if (loginGate) loginGate.hidden = loggedIn;
  document.querySelector(".nav-tabs").hidden = !loggedIn;
  document.querySelectorAll(".top-actions > :not(.auth-strip)").forEach((node) => {
    node.hidden = !loggedIn;
  });
  document.querySelectorAll(".summary-grid, .control-band, .insight-panel, .board-panel, .workspace-panel").forEach((panel) => {
    panel.hidden = !loggedIn;
  });
  if (!loggedIn) clearBoardData();
  else setActiveView(state.view);
}

function renderLoginUsers() {
  const select = $("#login-username");
  if (!select) return;
  select.innerHTML = (state.auth.users || [])
    .map((user) => `<option value="${esc(user.username)}">${esc(user.name)} · ${esc(user.roleLabel || user.role)}</option>`)
    .join("");
  if (!select.value && state.auth.users?.length) select.value = state.auth.users[0].username;
}

async function loadSession() {
  const payload = await api("/api/sku-board/session");
  state.auth.user = payload.user || null;
  state.auth.users = payload.users || [];
  state.auth.roles = payload.roles || state.auth.roles;
  state.auth.loaded = true;
  renderAuth();
}

function openLoginDialog() {
  $("#login-error").hidden = true;
  $("#login-password").value = "";
  renderLoginUsers();
  $("#login-dialog").showModal();
}

function closeLoginDialog() {
  const dialog = $("#login-dialog");
  if (dialog.open) dialog.close();
}

function openImagePreview(src, title) {
  const dialog = $("#image-preview-dialog");
  const previewImage = $("#image-preview-img");
  dialog.classList.remove("is-strip");
  const syncPreviewLayout = () => {
    const isStrip = previewImage.naturalWidth > 0
      && previewImage.naturalHeight > 0
      && previewImage.naturalWidth / previewImage.naturalHeight >= 4;
    dialog.classList.toggle("is-strip", isStrip);
  };
  previewImage.onload = syncPreviewLayout;
  previewImage.onerror = () => dialog.classList.remove("is-strip");
  previewImage.src = src || "/static/assets/glasses-square.svg";
  $("#image-preview-img").alt = title || "商品图片";
  $("#image-preview-title").textContent = title || "商品图片";
  if (previewImage.complete) syncPreviewLayout();
  dialog.showModal();
}

function closeImagePreview() {
  const dialog = $("#image-preview-dialog");
  if (dialog.open) dialog.close();
}

async function login() {
  const errorEl = $("#login-error");
  errorEl.hidden = true;
  const payload = await api("/api/sku-board/login", {
    method: "POST",
    body: JSON.stringify({
      username: $("#login-username").value,
      password: $("#login-password").value,
    }),
  });
  state.auth.user = payload.user || null;
  state.auth.users = payload.users || state.auth.users;
  state.auth.roles = payload.roles || state.auth.roles;
  closeLoginDialog();
  renderAuth();
  await loadBoard();
  if (state.view === "designTasks") {
    await loadDesignTasks();
  }
  if (state.view === "adLaunches") {
    await loadAdLaunches();
  }
  if (state.view === "metaCredentials" && isAdmin()) {
    await loadMetaCredentials(true);
  }
  if (state.view === "aiImages") {
    await loadAdLaunches();
    if (isAdmin()) await loadAiDirectorSettings(true);
    await loadAiImageHealth(true);
  }
  await resumePersistedAiImageSuite().catch(() => {});
  showToast(`已登录：${state.auth.user?.name || ""}`);
}

async function logout() {
  await api("/api/sku-board/logout", { method: "POST", body: JSON.stringify({}) });
  if (aiImageRecoveryTimer) {
    window.clearTimeout(aiImageRecoveryTimer);
    aiImageRecoveryTimer = null;
  }
  state.auth.user = null;
  state.designTasks.loaded = false;
  state.designTasks.tasks = [];
  state.designTasks.summary = {};
  state.designTasks.canCreate = false;
  state.adLaunches.loaded = false;
  state.adLaunches.launches = [];
  state.adLaunches.summary = {};
  state.adLaunches.material = null;
  state.metaCredentials = { loaded: false, loading: false, credentials: [], bindings: [], assets: [], assetDetails: [], users: [], summary: {}, oauthConfigured: false, oauthReady: false, oauthMode: "unconfigured", bindingCredentialId: "", bindingBusinessId: "", bindingAccountId: "", systemWizard: { sourceCredentialId: "", businessId: "", accountIds: [], pageIds: [] } };
  state.aiImages.health = { status: "unknown", message: "尚未检测服务", latencyMs: 0, checkedAt: "", baseUrl: "", loading: false };
  state.aiImages.director = { loaded: false, loading: false, enabled: false, configured: false, baseUrl: "", model: "gpt-5.6-terra", timeout: 60, visionEnabled: true, openImagePromptsEnabled: true, apiKeyConfigured: false, secureTransport: false, status: "unknown", message: "", formDirty: false };
  renderAuth();
  showToast("已退出登录");
}

function renderAccountPanel() {
  const loginRequired = $("#account-login-required");
  const workspace = $("#account-workspace");
  if (!loginRequired || !workspace) return;

  const loggedIn = Boolean(state.auth.user);
  loginRequired.hidden = loggedIn;
  workspace.hidden = !loggedIn;
  $("#account-role").innerHTML = roleOptions("designer");

  const admin = isAdmin();
  $("#account-create-form").classList.toggle("is-disabled", !admin);
  $("#account-create-form").querySelectorAll("input, select, button").forEach((field) => {
    field.disabled = !admin;
  });
  renderAccountUsers();
}

function renderAccountUsers() {
  const list = $("#account-users-list");
  if (!list) return;
  const users = state.auth.users || [];
  $("#account-count").textContent = `${users.length} 个账号`;
  if (!state.auth.user) {
    list.innerHTML = "";
    return;
  }
  if (!users.length) {
    list.innerHTML = emptyCard("暂无账号");
    return;
  }
  list.innerHTML = users
    .map((user) => {
      const active = user.active !== false;
      const adminControls = isAdmin()
        ? `
          <div class="account-user-actions">
            <input type="password" data-account-reset-input="${esc(user.username)}" placeholder="新密码" />
            <button class="mini-btn" data-account-reset="${esc(user.username)}" type="button">重置</button>
            <button class="ghost-btn ${active ? "danger" : ""}" data-account-active="${esc(user.username)}" data-account-next-active="${active ? "false" : "true"}" type="button">${active ? "停用" : "启用"}</button>
            <button class="ghost-btn danger" data-account-delete="${esc(user.username)}" data-account-delete-name="${esc(user.name)}" type="button">删除</button>
          </div>`
        : "";
      return `
        <article class="account-user-card ${active ? "" : "inactive"}">
          <div>
            <strong>${esc(user.username)}</strong>
            <p>${esc(user.name)} · ${esc(roleLabel(user.role))} · ${active ? "已启用" : "已停用"}</p>
            <small>最近登录 ${esc(shortDate(user.lastLoginAt))} · 密码更新 ${esc(shortDate(user.passwordUpdatedAt))}</small>
          </div>
          ${adminControls}
        </article>`;
    })
    .join("");
}

async function loadAccountUsers() {
  if (!state.auth.user) {
    openLoginDialog();
    return;
  }
  const payload = await api("/api/sku-board/users");
  state.auth.users = payload.users || state.auth.users;
  state.auth.roles = payload.roles || state.auth.roles;
  renderAccountPanel();
}

async function createAccount() {
  const payload = await api("/api/sku-board/users", {
    method: "POST",
    body: JSON.stringify({
      username: $("#account-username").value.trim(),
      name: $("#account-name").value.trim(),
      role: $("#account-role").value,
      password: $("#account-password").value,
    }),
  });
  state.auth.users = payload.users || state.auth.users;
  state.auth.roles = payload.roles || state.auth.roles;
  $("#account-create-form").reset();
  $("#account-role").innerHTML = roleOptions("designer");
  renderAccountPanel();
  showToast("账号已创建");
}

async function changeMyPassword() {
  const payload = await api("/api/sku-board/users/password", {
    method: "POST",
    body: JSON.stringify({
      currentPassword: $("#account-current-password").value,
      newPassword: $("#account-new-password").value,
    }),
  });
  state.auth.user = payload.user || state.auth.user;
  state.auth.users = payload.users || state.auth.users;
  $("#account-password-form").reset();
  renderAccountPanel();
  showToast("密码已更新");
}

async function resetAccountPassword(username) {
  const input = document.querySelector(`[data-account-reset-input="${CSS.escape(username)}"]`);
  const password = input?.value || "";
  await api(`/api/sku-board/users/${encodeURIComponent(username)}/reset-password`, {
    method: "POST",
    body: JSON.stringify({ password }),
  }).then((payload) => {
    state.auth.users = payload.users || state.auth.users;
    if (input) input.value = "";
    renderAccountPanel();
    showToast("密码已重置");
  });
}

async function setAccountActive(username, active) {
  const payload = await api(`/api/sku-board/users/${encodeURIComponent(username)}/active`, {
    method: "POST",
    body: JSON.stringify({ active }),
  });
  state.auth.users = payload.users || state.auth.users;
  renderAccountPanel();
  showToast(active ? "账号已启用" : "账号已停用");
}

async function deleteAccount(username) {
  const payload = await api(`/api/sku-board/users/${encodeURIComponent(username)}`, {
    method: "DELETE",
    body: JSON.stringify({}),
  });
  state.auth.users = payload.users || state.auth.users;
  renderAccountPanel();
  showToast("账号已删除");
}

function metaCredentialStatusLabel(status = "pending") {
  return {
    ready: "可用",
    warning: "部分资产受限",
    error: "校验失败",
    pending: "待校验",
  }[status] || "待校验";
}

function updateMetaCredentialPayload(payload = {}) {
  state.metaCredentials.credentials = payload.credentials || [];
  state.metaCredentials.bindings = payload.bindings || [];
  state.metaCredentials.assetDetails = payload.assetDetails || [];
  state.metaCredentials.users = payload.users || state.auth.users || [];
  state.metaCredentials.summary = payload.summary || {};
  state.metaCredentials.oauthConfigured = Boolean(payload.oauthConfigured);
  state.metaCredentials.oauthReady = Boolean(payload.oauthReady ?? payload.oauthConfigured);
  state.metaCredentials.oauthMode = payload.oauthMode || "unconfigured";
  state.metaCredentials.loaded = true;
}

function renderMetaCredentialPanel() {
  const loginRequired = $("#meta-credential-login-required");
  const adminRequired = $("#meta-credential-admin-required");
  const workspace = $("#meta-credential-workspace");
  if (!loginRequired || !adminRequired || !workspace) return;
  const loggedIn = Boolean(state.auth.user);
  const admin = isAdmin();
  loginRequired.hidden = loggedIn;
  adminRequired.hidden = !loggedIn || admin;
  workspace.hidden = !loggedIn || !admin;
  $("#meta-binding-open-btn").disabled = !admin;
  if (!loggedIn || !admin) return;

  const oauthStatus = $("#meta-oauth-status");
  if (oauthStatus) {
    const statusMap = {
      server_oauth: ["系统登录通道已就绪，点击后直接跳转 Facebook。", "ready"],
      company_gateway: ["公司登录通道已就绪，授权后自动回传个号资产。", "ready"],
      system_token: ["系统已有旧凭证可同步；新增个号将使用独立 Facebook 授权入口。", "ready"],
      unconfigured: ["系统登录通道尚未接通，请联系管理员配置后台连接。", "warning"],
    };
    const [message, tone] = statusMap[state.metaCredentials.oauthMode] || statusMap.unconfigured;
    oauthStatus.textContent = message;
    oauthStatus.dataset.tone = tone;
  }

  const summary = state.metaCredentials.summary || {};
  $("#meta-credential-kpis").innerHTML = [
    kpiCard("已接入凭证", summary.credentials || 0, "个人授权 + 系统用户"),
    kpiCard("可用凭证", summary.ready || 0, "可用于拉数与投放"),
    kpiCard("广告账户", summary.adAccounts || 0, "已从 Meta 同步"),
    kpiCard("已完成分配", summary.boundAccounts || 0, "已绑定到凭证"),
  ].join("");
  $("#meta-credential-count").textContent = `${(state.metaCredentials.credentials || []).length} 个凭证`;
  const list = $("#meta-credential-list");
  const credentials = state.metaCredentials.credentials || [];
  if (!credentials.length) {
    list.innerHTML = emptyCard("还没有 Meta 凭证。点击“添加新的 Facebook 个号”进入授权并同步资产。");
    return;
  }
  const bindingsByCredential = new Map();
  (state.metaCredentials.bindings || []).forEach((binding) => {
    const key = binding.credentialId || "";
    bindingsByCredential.set(key, [...(bindingsByCredential.get(key) || []), binding]);
  });
  list.innerHTML = credentials.map((credential) => {
    const assets = credential.assets || {};
    const linked = bindingsByCredential.get(credential.id) || [];
    const active = credential.active !== false;
    const linkedText = linked.length ? `已绑定 ${linked.length} 个广告户` : "广告户尚未分配";
    return `
      <article class="meta-credential-card ${active ? "" : "inactive"}">
        <div class="meta-credential-head">
          <div>
            <span class="panel-kicker">${esc(credential.credentialTypeLabel || credential.credentialType || "Meta")}</span>
            <h4>${esc(credential.name || "未命名凭证")}</h4>
            <p>${esc(credential.identity?.name || credential.identity?.id || "尚未读取 Meta 身份")} · ${esc(linkedText)}</p>
          </div>
          <span class="meta-credential-status ${esc(credential.status || "pending")}">${esc(active ? metaCredentialStatusLabel(credential.status) : "已停用")}</span>
        </div>
        <div class="meta-credential-assets">
          <span><strong>${Number(assets.adAccounts || 0)}</strong>广告户</span>
          <span><strong>${Number(assets.businesses || 0)}</strong>BM</span>
          <span><strong>${Number(assets.pages || 0)}</strong>主页</span>
          <span><strong>${Number(assets.instagramActors || 0)}</strong>IG 账号</span>
        </div>
        <div class="meta-credential-meta">
          <code>${esc(credential.tokenMasked || "••••••")}</code>
          <small>上次校验：${esc(shortDate(credential.lastValidatedAt) || "未校验")}</small>
          <small>资产同步：${esc(shortDate(credential.lastSyncedAt) || "未同步")}</small>
          ${credential.lastError ? `<small title="${esc(credential.lastError)}">状态：${esc(credential.lastError)}</small>` : ""}
        </div>
        <div class="meta-credential-actions">
          <button class="mini-btn" data-meta-credential-validate="${esc(credential.id)}" type="button">校验</button>
          <button class="mini-btn" data-meta-credential-sync="${esc(credential.id)}" type="button">同步资产</button>
          <button class="ghost-btn" data-meta-credential-bind="${esc(credential.id)}" type="button">分配广告户</button>
          <button class="ghost-btn ${active ? "danger" : ""}" data-meta-credential-active="${esc(credential.id)}" data-meta-credential-next-active="${active ? "false" : "true"}" type="button">${active ? "停用" : "启用"}</button>
          <button class="ghost-btn danger" data-meta-credential-delete="${esc(credential.id)}" data-meta-credential-name="${esc(credential.name)}" type="button">删除</button>
        </div>
      </article>
    `;
  }).join("");
}

async function loadMetaCredentials(silent = false) {
  if (!state.auth.user || !isAdmin()) {
    renderMetaCredentialPanel();
    return;
  }
  state.metaCredentials.loading = true;
  try {
    const [credentialsPayload, assetsPayload] = await Promise.all([
      api("/api/sku-board/meta-credentials"),
      api("/api/sku-board/meta-assets"),
    ]);
    updateMetaCredentialPayload(credentialsPayload);
    state.metaCredentials.assets = assetsPayload.accounts || [];
    if (!silent) showToast("Meta 凭证已刷新");
  } finally {
    state.metaCredentials.loading = false;
    renderMetaCredentialPanel();
  }
}

async function createMetaCredential() {
  const payload = await api("/api/sku-board/meta-credentials", {
    method: "POST",
    body: JSON.stringify({
      name: $("#meta-credential-name").value.trim(),
      credentialType: $("#meta-credential-type").value,
      token: $("#meta-credential-token").value.trim(),
    }),
  });
  updateMetaCredentialPayload(payload);
  $("#meta-credential-form").reset();
  await loadMetaCredentials(true);
  showToast(payload.credential?.status === "error" ? "凭证已保存，但 Meta 校验失败，请检查 Token 和权限" : "凭证已加密保存并完成资产同步");
}

async function validateMetaCredential(credentialId) {
  const payload = await api(`/api/sku-board/meta-credentials/${encodeURIComponent(credentialId)}/validate`, { method: "POST", body: JSON.stringify({}) });
  updateMetaCredentialPayload(payload);
  await loadMetaCredentials(true);
  showToast(payload.credential?.status === "error" ? "校验未通过，请检查凭证" : "Meta 凭证校验完成");
}

async function syncMetaCredential(credentialId) {
  const payload = await api(`/api/sku-board/meta-credentials/${encodeURIComponent(credentialId)}/sync`, { method: "POST", body: JSON.stringify({}) });
  updateMetaCredentialPayload(payload);
  await loadMetaCredentials(true);
  showToast(payload.credential?.status === "error" ? "同步失败，请查看凭证状态" : "Meta 资产已同步");
}

async function setMetaCredentialActive(credentialId, active) {
  const payload = await api(`/api/sku-board/meta-credentials/${encodeURIComponent(credentialId)}/active`, {
    method: "POST",
    body: JSON.stringify({ active }),
  });
  updateMetaCredentialPayload(payload);
  renderMetaCredentialPanel();
  showToast(active ? "凭证已启用" : "凭证已停用，绑定广告户将无法投放");
}

async function deleteMetaCredential(credentialId, name) {
  if (!window.confirm(`删除凭证“${name || credentialId}”吗？该凭证关联的广告户分配也会一并解除。`)) return;
  const payload = await api(`/api/sku-board/meta-credentials/${encodeURIComponent(credentialId)}`, { method: "DELETE", body: JSON.stringify({}) });
  updateMetaCredentialPayload(payload);
  await loadMetaCredentials(true);
  showToast("Meta 凭证已删除");
}

async function startMetaOAuth() {
  const button = $("#meta-credential-oauth-btn");
  const originalText = button?.textContent || "添加新的 Facebook 个号";
  if (button) {
    button.disabled = true;
    button.textContent = "正在连接 Facebook…";
  }
  let payload;
  try {
    payload = await api("/api/sku-board/meta-credentials/oauth", { method: "POST", body: JSON.stringify({ name: "", forceOAuth: true }) });
  } catch (error) {
    if (button) {
      button.disabled = false;
      button.textContent = originalText;
    }
    throw error;
  }
  if (payload.credential) {
    updateMetaCredentialPayload(payload);
    await loadMetaCredentials(true);
    showToast(payload.credential.status === "error" ? "系统凭证已读取，请检查凭证状态和 Meta 权限" : "Facebook 个号及资产已自动同步");
    if (button) {
      button.disabled = false;
      button.textContent = originalText;
    }
    return;
  }
  const popup = window.open(payload.authorizationUrl, "sku-board-meta-oauth", "popup=yes,width=760,height=780,resizable=yes,scrollbars=yes");
  if (!popup) {
    if (button) {
      button.disabled = false;
      button.textContent = originalText;
    }
    throw new Error("浏览器阻止了 Meta 授权窗口，请允许弹窗后重试");
  }
  window.setTimeout(() => {
    if (button) {
      button.disabled = false;
      button.textContent = originalText;
    }
  }, 1200);
}

async function syncExistingMetaConnection() {
  const button = $("#meta-credential-existing-sync-btn");
  const originalText = button?.textContent || "同步已有系统连接";
  if (button) {
    button.disabled = true;
    button.textContent = "正在同步已有连接…";
  }
  try {
    const payload = await api("/api/sku-board/meta-credentials/oauth", {
      method: "POST",
      body: JSON.stringify({ name: "", reuseExisting: true }),
    });
    if (payload.credential) {
      updateMetaCredentialPayload(payload);
      await loadMetaCredentials(true);
      showToast(payload.credential.status === "error" ? "已有凭证已读取，请检查 Meta 权限" : "已有 Facebook 资产已同步");
      return;
    }
    showToast("系统返回了新的 Facebook 授权入口");
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = originalText;
    }
  }
}

function metaBindingCredentials() {
  return (state.metaCredentials.credentials || []).filter((credential) => credential.active !== false && Number(credential.assets?.adAccounts || 0) > 0);
}

function closeMetaBindingDialog() {
  const dialog = $("#meta-binding-dialog");
  if (dialog?.open) dialog.close();
}

function openMetaBindingDialog(credentialId = "") {
  const credentials = metaBindingCredentials();
  if (!credentials.length) {
    showToast("请先添加并同步一个可用的 Meta 凭证");
    return;
  }
  state.metaCredentials.bindingCredentialId = credentialId && credentials.some((item) => item.id === credentialId) ? credentialId : credentials[0].id;
  state.metaCredentials.bindingBusinessId = "";
  state.metaCredentials.bindingAccountId = "";
  renderMetaBindingDialog();
  $("#meta-binding-dialog").showModal();
}

function renderMetaBindingDialog() {
  const credentialSelect = $("#meta-binding-credential");
  const businessSelect = $("#meta-binding-business");
  const accountSelect = $("#meta-binding-account");
  if (!credentialSelect || !businessSelect || !accountSelect) return;
  const credentials = metaBindingCredentials();
  if (!credentials.some((item) => item.id === state.metaCredentials.bindingCredentialId)) {
    state.metaCredentials.bindingCredentialId = credentials[0]?.id || "";
  }
  credentialSelect.innerHTML = credentials.map((credential) => `<option value="${esc(credential.id)}" ${credential.id === state.metaCredentials.bindingCredentialId ? "selected" : ""}>${esc(credential.name)} · ${esc(credential.credentialTypeLabel || credential.credentialType)}</option>`).join("");
  const credentialAssets = (state.metaCredentials.assets || []).filter((asset) => asset.credentialId === state.metaCredentials.bindingCredentialId);
  const businessGroups = new Map();
  credentialAssets.forEach((asset) => {
    const businessId = asset.businessId || "__unassigned__";
    if (!businessGroups.has(businessId)) businessGroups.set(businessId, asset.businessName || "未分组 BC");
  });
  if (state.metaCredentials.bindingBusinessId && !businessGroups.has(state.metaCredentials.bindingBusinessId)) {
    state.metaCredentials.bindingBusinessId = "";
  }
  if (!state.metaCredentials.bindingBusinessId) state.metaCredentials.bindingBusinessId = Array.from(businessGroups.keys())[0] || "";
  businessSelect.innerHTML = businessGroups.size
    ? Array.from(businessGroups.entries()).map(([id, name]) => `<option value="${esc(id)}" ${id === state.metaCredentials.bindingBusinessId ? "selected" : ""}>${esc(name)} · ${esc(id === "__unassigned__" ? "未分组" : id)}</option>`).join("")
    : `<option value="">该凭证未同步到 BC</option>`;
  const assets = credentialAssets.filter((asset) => !state.metaCredentials.bindingBusinessId || (asset.businessId || "__unassigned__") === state.metaCredentials.bindingBusinessId);
  if (!assets.some((asset) => asset.accountId === state.metaCredentials.bindingAccountId)) {
    state.metaCredentials.bindingAccountId = assets[0]?.accountId || "";
  }
  accountSelect.innerHTML = assets.length
    ? assets.map((asset) => `<option value="${esc(asset.accountId)}" ${asset.accountId === state.metaCredentials.bindingAccountId ? "selected" : ""}>${esc(asset.accountName || asset.accountId)} · ${esc(asset.accountId)}</option>`).join("")
    : `<option value="">该凭证未同步到广告户</option>`;
  const asset = assets.find((item) => item.accountId === state.metaCredentials.bindingAccountId) || {};
  const binding = (state.metaCredentials.bindings || []).find((item) => item.accountId === asset.accountId) || {};
  $("#meta-binding-account-info").textContent = asset.accountId
    ? `广告户：${asset.accountName || asset.accountId} · 币种 ${asset.currency || "-"} · 时区 ${asset.timezone || "-"} · BM ${asset.businessName || "未返回"}`
    : "请先同步凭证资产后再分配广告户。";
  const assigned = new Set(binding.assignedUsernames || []);
  const users = (state.metaCredentials.users || state.auth.users || []).filter((user) => ["ops", "selection"].includes(user.role) && user.active !== false);
  $("#meta-binding-users").innerHTML = users.length
    ? users.map((user) => `<label><input type="checkbox" data-meta-binding-user="${esc(user.username)}" ${assigned.has(user.username) ? "checked" : ""} />${esc(user.name)} · ${esc(user.roleLabel || user.role)}</label>`).join("")
    : `<span class="account-help">当前还没有可分配的运营或选品账号。</span>`;
  $("#meta-binding-save-btn").disabled = !asset.accountId;
}

async function saveMetaBinding() {
  const accountId = $("#meta-binding-account").value;
  const credentialId = $("#meta-binding-credential").value;
  const assignedUsernames = Array.from(document.querySelectorAll("[data-meta-binding-user]:checked")).map((input) => input.dataset.metaBindingUser);
  const payload = await api("/api/sku-board/meta-asset-bindings", {
    method: "POST",
    body: JSON.stringify({ accountId, credentialId, assignedUsernames }),
  });
  updateMetaCredentialPayload(payload);
  await loadMetaCredentials(true);
  closeMetaBindingDialog();
  showToast("广告户凭证和团队权限已保存");
}

function metaWizardPersonalCredentials() {
  return (state.metaCredentials.credentials || []).filter((credential) => credential.credentialType === "personal" && credential.active !== false && credential.status !== "error");
}

function metaWizardDetail(credentialId = "") {
  return (state.metaCredentials.assetDetails || []).find((item) => item.credentialId === credentialId) || { businesses: [], adAccounts: [], pages: [], instagramActors: [] };
}

function closeMetaSystemWizard() {
  const dialog = $("#meta-system-wizard-dialog");
  if (dialog?.open) dialog.close();
}

function openMetaSystemWizard() {
  const personalCredentials = metaWizardPersonalCredentials();
  if (!personalCredentials.length) {
    showToast("请先添加一个个人授权凭证并同步资产，再创建系统凭证");
    return;
  }
  const current = state.metaCredentials.systemWizard || {};
  const sourceCredentialId = personalCredentials.some((item) => item.id === current.sourceCredentialId)
    ? current.sourceCredentialId
    : personalCredentials[0].id;
  const detail = metaWizardDetail(sourceCredentialId);
  const businessId = (detail.businesses || []).some((item) => item.id === current.businessId)
    ? current.businessId
    : detail.businesses?.[0]?.id || "";
  const accounts = metaWizardAccounts(detail, businessId);
  state.metaCredentials.systemWizard = {
    sourceCredentialId,
    businessId,
    accountIds: current.accountIds?.length ? current.accountIds : accounts.map((item) => item.accountId),
    pageIds: current.pageIds?.length ? current.pageIds : (detail.pages || []).map((item) => item.id),
  };
  $("#meta-system-wizard-name").value = "";
  $("#meta-system-wizard-token").value = "";
  $("#meta-system-policy").checked = false;
  renderMetaSystemWizard();
  $("#meta-system-wizard-dialog").showModal();
}

function metaWizardAccounts(detail = {}, businessId = "") {
  const all = detail.adAccounts || [];
  const scoped = all.filter((item) => !businessId || !item.businessId || item.businessId === businessId);
  return scoped.length || !businessId ? scoped : all;
}

function renderMetaSystemWizard() {
  const personalSelect = $("#meta-system-wizard-personal");
  const businessSelect = $("#meta-system-wizard-business");
  if (!personalSelect || !businessSelect) return;
  const wizard = state.metaCredentials.systemWizard || {};
  const personalCredentials = metaWizardPersonalCredentials();
  if (!personalCredentials.some((item) => item.id === wizard.sourceCredentialId)) {
    wizard.sourceCredentialId = personalCredentials[0]?.id || "";
  }
  personalSelect.innerHTML = personalCredentials.length
    ? personalCredentials.map((credential) => `<option value="${esc(credential.id)}" ${credential.id === wizard.sourceCredentialId ? "selected" : ""}>${esc(credential.name)} · ${esc(credential.identity?.name || "已授权个号")}</option>`).join("")
    : `<option value="">请先添加个人授权凭证</option>`;
  const detail = metaWizardDetail(wizard.sourceCredentialId);
  const businesses = detail.businesses || [];
  if (!businesses.some((item) => item.id === wizard.businessId)) wizard.businessId = businesses[0]?.id || "";
  businessSelect.innerHTML = businesses.length
    ? businesses.map((business) => `<option value="${esc(business.id)}" ${business.id === wizard.businessId ? "selected" : ""}>${esc(business.name || business.id)} · ${esc(business.id)}</option>`).join("")
    : `<option value="">该个号尚未同步到 BM</option>`;
  const accounts = metaWizardAccounts(detail, wizard.businessId);
  const accountSet = new Set(wizard.accountIds || []);
  const visibleAccountIds = new Set(accounts.map((item) => item.accountId));
  wizard.accountIds = (wizard.accountIds || []).filter((id) => visibleAccountIds.has(id));
  if (!wizard.accountIds.length && accounts.length) wizard.accountIds = accounts.map((item) => item.accountId);
  const selectedAccounts = new Set(wizard.accountIds || []);
  $("#meta-system-wizard-accounts").innerHTML = accounts.length
    ? accounts.map((account) => `
      <label><input type="checkbox" data-meta-system-account="${esc(account.accountId)}" ${selectedAccounts.has(account.accountId) ? "checked" : ""} />
        <span><strong>${esc(account.accountName || account.accountId)}</strong><small>${esc(account.accountId)} · ${esc(account.businessName || "当前 BM")}</small></span>
      </label>`).join("")
    : emptyCard("当前 BM 未同步到广告户，请先在个人凭证中同步资产。");
  const pages = detail.pages || [];
  const pageSet = new Set(wizard.pageIds || []);
  wizard.pageIds = (wizard.pageIds || []).filter((id) => pages.some((item) => item.id === id));
  if (!wizard.pageIds.length && pages.length) wizard.pageIds = pages.map((item) => item.id);
  const selectedPages = new Set(wizard.pageIds || []);
  $("#meta-system-wizard-pages").innerHTML = pages.length
    ? pages.map((page) => `
      <label><input type="checkbox" data-meta-system-page="${esc(page.id)}" ${selectedPages.has(page.id) ? "checked" : ""} />
        <span><strong>${esc(page.name || page.id)}</strong><small>Page ID · ${esc(page.id)}</small></span>
      </label>`).join("")
    : emptyCard("该个号未同步到公共主页，无法创建可投放的系统凭证；请先同步个号资产。");
  $("#meta-system-account-all").checked = Boolean(accounts.length) && wizard.accountIds.length === accounts.length;
  $("#meta-system-page-all").checked = Boolean(pages.length) && wizard.pageIds.length === pages.length;
  $("#meta-system-wizard-hint").textContent = `当前个号已同步 ${accounts.length} 个广告户、${pages.length} 个主页。提交后会按所选 BM 和资产自动创建系统凭证；已有 System User Token 时也可直接复用。`;
  $("#meta-system-wizard-save-btn").disabled = !wizard.sourceCredentialId || !wizard.businessId || !wizard.accountIds.length || !wizard.pageIds.length;
}

function setMetaWizardSelection(kind, value, checked) {
  const wizard = state.metaCredentials.systemWizard;
  const key = kind === "account" ? "accountIds" : "pageIds";
  const current = new Set(wizard[key] || []);
  if (checked) current.add(value);
  else current.delete(value);
  wizard[key] = [...current];
  renderMetaSystemWizard();
}

async function createSystemCredentialFromWizard(event) {
  event.preventDefault();
  const wizard = state.metaCredentials.systemWizard;
  const button = $("#meta-system-wizard-save-btn");
  const label = button.textContent;
  button.disabled = true;
  button.textContent = "创建并同步中…";
  try {
    const payload = await api("/api/sku-board/meta-credentials/system-wizard", {
      method: "POST",
      body: JSON.stringify({
        name: $("#meta-system-wizard-name").value.trim(),
        sourceCredentialId: wizard.sourceCredentialId,
        businessId: wizard.businessId,
        accountIds: wizard.accountIds || [],
        pageIds: wizard.pageIds || [],
        token: $("#meta-system-wizard-token").value.trim(),
        policyConfirmed: Boolean($("#meta-system-policy").checked),
      }),
    });
    updateMetaCredentialPayload(payload);
    await loadMetaCredentials(true);
    closeMetaSystemWizard();
    showToast(payload.credential?.status === "error" ? "系统凭证已保存，但需检查 Token 权限" : "系统凭证已创建，广告户已同步绑定");
  } finally {
    button.disabled = false;
    button.textContent = label;
  }
}

const designTaskFallbackOptions = {
  statuses: { pending: "待接单", working: "设计中", review: "待审核", revision: "需修改", done: "已完成", paused: "已暂停" },
  priorities: { urgent: "加急", normal: "普通", low: "低优先" },
  templates: { custom: "自定义需求", product_page: "商品页素材", ad_creative: "广告图/视频", main_visual: "主图/详情页", refresh: "素材翻新" },
  scopes: { all: "全部素材库", product: "指定商品", shooting: "拍摄/实拍", ad: "投放素材", page: "承接页素材" },
  deliveries: { both: "图片 + 剪辑", image: "图片 +1", video: "剪辑 +1", none: "不计入进度" },
};

function designTaskOptions() {
  return {
    statuses: state.designTasks.options.statuses || designTaskFallbackOptions.statuses,
    priorities: state.designTasks.options.priorities || designTaskFallbackOptions.priorities,
    templates: state.designTasks.options.templates || designTaskFallbackOptions.templates,
    scopes: state.designTasks.options.scopes || designTaskFallbackOptions.scopes,
    deliveries: state.designTasks.options.deliveries || designTaskFallbackOptions.deliveries,
    designers: state.designTasks.options.designers || designAssignableUsers().filter((user) => user.role === "designer"),
    customers: state.designTasks.options.customers || (state.auth.users || []).filter((user) => user.role === "customer"),
    products: state.designTasks.options.products || state.items.map((item) => ({ sku: item.sku, title: item.title, image: item.image, owner: item.owner })),
  };
}

function updateDesignTaskPayload(payload) {
  state.designTasks.tasks = payload.tasks || state.designTasks.tasks;
  state.designTasks.summary = payload.summary || state.designTasks.summary;
  state.designTasks.options = payload.options || state.designTasks.options;
  state.designTasks.canCreate = Boolean(payload.canCreate);
  state.designTasks.loaded = true;
}

async function loadDesignTasks() {
  if (!state.auth.user) {
    state.designTasks.loaded = false;
    state.designTasks.tasks = [];
    renderDesignTaskPanel();
    return;
  }
  const payload = await api("/api/sku-board/design-tasks");
  updateDesignTaskPayload(payload);
  renderDesignTaskPanel();
}

function renderDesignTaskPanel() {
  const loginRequired = $("#design-task-login-required");
  const workspace = $("#design-task-workspace");
  if (!loginRequired || !workspace) return;
  const loggedIn = Boolean(state.auth.user);
  loginRequired.hidden = loggedIn;
  workspace.hidden = !loggedIn;
  if (!loggedIn) return;

  renderDesignTaskForm();
  renderDesignTaskFilters();
  renderDesignTaskKpis();
  renderDesignTaskList();
}

function renderDesignTaskForm() {
  const form = $("#design-task-form");
  if (!form) return;
  const options = designTaskOptions();
  const canCreate = isDesignTaskCreator() && state.designTasks.canCreate;
  const currentCustomer = $("#design-task-customer")?.value || "";
  const currentProduct = $("#design-task-product")?.value || "";
  const currentAssignee = $("#design-task-assignee")?.value || "";
  const currentTemplate = $("#design-task-template")?.value || "custom";
  const currentPriority = $("#design-task-priority")?.value || "normal";
  const currentScope = $("#design-task-scope")?.value || "all";
  const currentDelivery = $("#design-task-delivery")?.value || "both";

  $("#design-task-customer").innerHTML = userOptions(options.customers, currentCustomer, "手动客户名");
  $("#design-task-product").innerHTML = productOptions(options.products, currentProduct);
  $("#design-task-assignee").innerHTML = userOptions(options.designers, currentAssignee, "请选择设计");
  $("#design-task-template").innerHTML = mapOptions(options.templates, currentTemplate);
  $("#design-task-priority").innerHTML = mapOptions(options.priorities, currentPriority);
  $("#design-task-scope").innerHTML = mapOptions(options.scopes, currentScope);
  $("#design-task-delivery").innerHTML = mapOptions(options.deliveries, currentDelivery);
  form.classList.toggle("is-disabled", !canCreate);
  form.querySelectorAll("input, select, textarea, button").forEach((field) => {
    field.disabled = !canCreate;
  });
}

function renderDesignTaskFilters() {
  const options = designTaskOptions();
  const statusSelect = $("#design-task-status-filter");
  const ownerSelect = $("#design-task-owner-filter");
  const status = state.designTasks.filters.status;
  const owner = state.designTasks.filters.owner;
  statusSelect.innerHTML = mapOptions(options.statuses, status, "全部任务");
  ownerSelect.innerHTML = userOptions(options.designers, owner, "全部设计");
  statusSelect.value = status;
  ownerSelect.value = owner;
  $("#design-task-search").value = state.designTasks.filters.q;
}

function renderDesignTaskKpis() {
  const summary = state.designTasks.summary || {};
  const counts = summary.statusCounts || {};
  $("#design-task-kpis").innerHTML = [
    kpiCard("任务总数", summary.total || 0, "当前可见"),
    kpiCard("未完成", summary.open || 0, `待接单 ${counts.pending || 0}`),
    kpiCard("加急任务", summary.urgentOpen || 0, "选品优先盯"),
    kpiCard("已逾期", summary.overdue || 0, "未完成且过期"),
  ].join("");
}

function filteredDesignTasks() {
  const { status, owner, q } = state.designTasks.filters;
  const query = q.trim().toLowerCase();
  return (state.designTasks.tasks || []).filter((task) => {
    if (status && task.status !== status) return false;
    if (owner && task.assigneeUsername !== owner) return false;
    if (!query) return true;
    const haystack = [
      task.id,
      task.title,
      task.productName,
      task.productSku,
      task.customerName,
      task.assigneeName,
      task.requirements,
      task.scriptCopy,
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(query);
  });
}

function renderDesignTaskList() {
  const list = $("#design-task-list");
  if (!list) return;
  const tasks = filteredDesignTasks();
  list.innerHTML = tasks.length ? tasks.map(renderDesignTaskCard).join("") : emptyCard("当前没有客户设计任务");
}

function renderDesignTaskCard(task) {
  const options = designTaskOptions();
  const canUpdate = task.canUpdate !== false;
  const canManageTask = isDesignTaskManager();
  const canDelete = Boolean(task.canDelete);
  const productImage = task.productImage || "/static/assets/sosove-logo.jpeg";
  const statusTone = task.status === "done" ? "good" : task.status === "revision" ? "warn" : task.overdue ? "danger" : "info";
  const assetButton = task.assetLink
    ? `<a class="quick-btn design-task-link-btn" href="${esc(task.assetLink)}" target="_blank" rel="noopener">打开成片</a>`
    : "";
  return `
    <article class="design-task-card ${task.overdue ? "overdue" : ""}" data-design-task-card="${esc(task.id)}">
      <div class="design-task-card-head">
        <button class="review-image-btn design-task-image-btn" data-preview-image="${esc(productImage)}" data-preview-title="${esc(task.productName || task.title)}" type="button">
          <img src="${esc(productImage)}" alt="${esc(task.productName || task.title)}" loading="lazy" />
        </button>
        <div>
          <div class="stack-card-head">
            <h4>${esc(task.title)}</h4>
            <span class="action-badge ${toneClass(statusTone)}">${esc(task.statusLabel)}</span>
          </div>
          <p>${esc(task.productName || "未关联商品")} ${task.productSku ? `· ${esc(task.productSku)}` : ""}</p>
          <div class="stack-card-meta">
            <span class="metric-pill">${esc(task.customerName || "客户")}</span>
            <span class="metric-pill blue">${esc(task.assigneeName || "未分配")}</span>
            <span class="metric-pill amber">${esc(task.priorityLabel || "普通")}</span>
            <span class="metric-pill">${esc(task.templateLabel || "自定义需求")}</span>
            <span class="metric-pill teal">${esc(task.deliveryTypeLabel || "不计入进度")}</span>
            ${task.dueDate ? `<span class="metric-pill ${task.overdue ? "amber" : ""}">截止 ${esc(task.dueDate)}</span>` : ""}
            ${task.progressSyncedAt ? `<span class="metric-pill blue">已同步 ${esc(shortDate(task.progressSyncedAt))}</span>` : ""}
          </div>
        </div>
      </div>
      <div class="design-task-copy">
        <div>
          <strong>设计要求</strong>
          <p>${esc(task.requirements || "暂无要求")}</p>
        </div>
        <div>
          <strong>脚本文案</strong>
          <p>${esc(task.scriptCopy || "暂无脚本")}</p>
        </div>
      </div>
      <div class="design-task-progress">
        <label>状态
          <select data-design-task-status="${esc(task.id)}" ${canUpdate ? "" : "disabled"}>
            ${mapOptions(options.statuses, task.status)}
          </select>
        </label>
        <label>成片链接
          <input data-design-task-link="${esc(task.id)}" value="${esc(task.assetLink || "")}" placeholder="剪映导出链接 / 云盘地址" ${canUpdate ? "" : "disabled"} />
        </label>
        <label>计入进度
          <select data-design-task-delivery="${esc(task.id)}" ${canUpdate && canManageTask && !task.progressSyncedAt ? "" : "disabled"}>
            ${mapOptions(options.deliveries, task.deliveryType || "none")}
          </select>
        </label>
        <label class="wide">交付备注
          <textarea data-design-task-note="${esc(task.id)}" placeholder="客户提交说明，或管理员复核意见" ${canUpdate ? "" : "disabled"}>${esc(task.deliveryNote || "")}</textarea>
        </label>
      </div>
      <div class="design-task-actions">
        <div class="design-task-history">${renderDesignTaskHistory(task)}</div>
        <div>
          ${assetButton}
          <button class="primary-btn" data-design-task-save="${esc(task.id)}" type="button" ${canUpdate ? "" : "disabled"}>保存进度</button>
          ${canDelete ? `<button class="ghost-btn danger" data-design-task-delete="${esc(task.id)}" data-design-task-title="${esc(task.title)}" type="button">删除</button>` : ""}
        </div>
      </div>
    </article>
  `;
}

function renderDesignTaskHistory(task) {
  const history = task.history || [];
  if (!history.length) return `<span>暂无流转记录</span>`;
  const latest = history[0];
  return `<span>${esc(latest.actor || "系统")} · ${esc(latest.text || "")} · ${esc(shortDate(latest.createdAt))}</span>`;
}

function setDesignTaskFilter(key, value) {
  state.designTasks.filters[key] = value;
  renderDesignTaskFilters();
  renderDesignTaskList();
}

function prefillDesignTaskFromProduct() {
  const sku = $("#design-task-product").value;
  const product = designTaskOptions().products.find((item) => item.sku === sku);
  if (!product) return;
  const title = $("#design-task-title");
  const requirements = $("#design-task-requirements");
  if (!title.value.trim()) title.value = `${product.title} 设计素材`;
  if (!requirements.value.trim()) {
    requirements.value = `请围绕 ${product.title} 做一组可投放设计素材，突出主卖点、上身效果和细节质感。`;
  }
}

async function createDesignTask(event) {
  event.preventDefault();
  if (!state.auth.user) {
    openLoginDialog();
    return;
  }
  if (!isDesignTaskCreator()) {
    showToast("只有管理员或选品账号可以下单");
    return;
  }
  const customerUsername = $("#design-task-customer").value;
  const customerName = $("#design-task-customer-name").value.trim();
  const payload = await api("/api/sku-board/design-tasks", {
    method: "POST",
    body: JSON.stringify({
      customerUsername,
      customerName,
      productSku: $("#design-task-product").value,
      assigneeUsername: $("#design-task-assignee").value,
      template: $("#design-task-template").value,
      priority: $("#design-task-priority").value,
      title: $("#design-task-title").value.trim(),
      materialScope: $("#design-task-scope").value,
      deliveryType: $("#design-task-delivery").value,
      dueDate: $("#design-task-due-date").value,
      requirements: $("#design-task-requirements").value.trim(),
      scriptCopy: $("#design-task-script").value.trim(),
    }),
  });
  updateDesignTaskPayload(payload);
  $("#design-task-form").reset();
  renderDesignTaskPanel();
  showToast("客户设计任务已下发");
}

async function saveDesignTask(taskId) {
  const card = document.querySelector(`[data-design-task-card="${CSS.escape(taskId)}"]`);
  if (!card) return;
  const payload = await api(`/api/sku-board/design-tasks/${encodeURIComponent(taskId)}`, {
    method: "PATCH",
    body: JSON.stringify({
      status: card.querySelector(`[data-design-task-status="${CSS.escape(taskId)}"]`)?.value || "pending",
      assetLink: card.querySelector(`[data-design-task-link="${CSS.escape(taskId)}"]`)?.value.trim() || "",
      deliveryType: card.querySelector(`[data-design-task-delivery="${CSS.escape(taskId)}"]`)?.value || "none",
      deliveryNote: card.querySelector(`[data-design-task-note="${CSS.escape(taskId)}"]`)?.value.trim() || "",
    }),
  });
  updateDesignTaskPayload(payload);
  if (payload.progressSynced) {
    await loadBoard();
  } else {
    renderDesignTaskPanel();
  }
  showToast(payload.progressMessage || "设计任务进度已保存");
}

async function deleteDesignTask(taskId) {
  const payload = await api(`/api/sku-board/design-tasks/${encodeURIComponent(taskId)}`, {
    method: "DELETE",
    body: JSON.stringify({}),
  });
  updateDesignTaskPayload(payload);
  renderDesignTaskPanel();
  showToast("设计任务已删除");
}

function updateAdLaunchPayload(payload) {
  state.adLaunches.launches = payload.launches || [];
  state.adLaunches.summary = payload.summary || {};
  state.adLaunches.options = payload.options || state.adLaunches.options;
  state.adLaunches.loaded = true;
  if (payload.options?.source?.warning || payload.warning) {
    showToast(payload.options?.source?.warning || payload.warning);
  }
}

function adLaunchOptions() {
  return state.adLaunches.options || { products: [], accounts: [], campaigns: [], adsets: [], ctas: {}, defaults: {} };
}

function mergeLocalMetaAccountsIntoAdLaunchOptions(payload = {}) {
  const accounts = Array.isArray(payload.accounts) ? payload.accounts : [];
  if (!accounts.length) return;
  state.adLaunches.options = {
    ...adLaunchOptions(),
    accounts,
  };
}

function aiImageOptions() {
  const options = adLaunchOptions();
  return {
    products: options.products?.length
      ? options.products
      : state.items.map((item) => ({ sku: item.sku, title: item.title, image: item.image, owner: item.owner })),
    aiImage: options.aiImage || {
      enabled: true,
      model: "gpt-image-2",
      models: ["gpt-image-2", "codex-gpt-image-2", "auto", "acore/gpt-image-2", "acore/nano-banana-2", "acore/nano-banana-pro"],
      sizes: AI_IMAGE_SIZE_PRESETS.map((item) => item.value),
      qualities: ["auto", "low", "medium", "high"],
      maxCount: 10,
    },
  };
}

function setAiImageQuickEntryLoading(loading) {
  const section = $("#ai-image-quick-entry");
  if (!section) return;
  section.classList.toggle("is-loading", Boolean(loading));
  section.querySelectorAll("[data-ai-quick-template]").forEach((button) => {
    button.disabled = Boolean(loading);
  });
}

async function loadAiImageConfig(silent = false) {
  if (!state.auth.user || !canUseAiImages()) return null;
  state.aiImages.configLoading = true;
  setAiImageQuickEntryLoading(true);
  try {
    const payload = await api("/api/sku-board/ai-image-config");
    state.adLaunches.options = {
      ...adLaunchOptions(),
      products: Array.isArray(payload.products) ? payload.products : adLaunchOptions().products,
      aiImage: payload.aiImage || adLaunchOptions().aiImage,
    };
    const sharedDirector = payload.aiImage?.director;
    if (sharedDirector && typeof sharedDirector === "object") {
      state.aiImages.director = {
        ...(state.aiImages.director || {}),
        ...sharedDirector,
        loaded: isAdmin() ? Boolean(state.aiImages.director?.loaded) : true,
        loading: false,
        formDirty: false,
      };
    }
    state.aiImages.configLoaded = Boolean(payload.aiImage);
    state.aiImages.configLoading = false;
    setAiImageQuickEntryLoading(false);
    renderAiImagePanel();
    if (!silent) showToast(`AI 生图配置已加载 · Skill v${aiImageSkillConfig().version || "内置"}`);
    return payload;
  } catch (error) {
    state.aiImages.configLoaded = false;
    state.aiImages.configLoading = false;
    setAiImageQuickEntryLoading(false);
    renderAiImagePanel();
    if (!silent) showToast(error.message);
    return null;
  }
}

function aiImageModelProvider(model = "") {
  return String(model || "").startsWith("acore/") ? "acore" : "chatgpt2api";
}

function aiImageModelLabel(model = "") {
  const value = String(model || "");
  return aiImageModelProvider(value) === "acore" ? `公司 · ${value.slice("acore/".length)}` : value;
}

function aiImageProviderLabel(model = "") {
  return aiImageModelProvider(model) === "acore" ? "Giikin Acore 公司生图" : "ChatGPT2API";
}

function aiImageSkillConfig() {
  const skill = aiImageOptions().aiImage?.skill;
  return skill && typeof skill === "object" ? { ...AI_IMAGE_SKILL_FALLBACK, ...skill } : AI_IMAGE_SKILL_FALLBACK;
}

function aiImageModeOptions() {
  const modes = aiImageSkillConfig().modes;
  return Array.isArray(modes) && modes.length ? modes : AI_IMAGE_MODES;
}

function aiImageTemplateOptions() {
  const templates = aiImageSkillConfig().templates;
  return Array.isArray(templates) && templates.length ? templates : AI_IMAGE_PROMPT_TEMPLATES;
}

function aiImageLockOptions() {
  const levels = aiImageSkillConfig().lockLevels;
  return Array.isArray(levels) && levels.length ? levels : AI_IMAGE_LOCK_LEVELS;
}

function aiImageLockConfig(lockLevel = "strict") {
  return aiImageLockOptions().find((item) => item.key === lockLevel) || aiImageLockOptions()[0] || AI_IMAGE_LOCK_LEVELS[1];
}

function aiImageLockDisplay(lockLevel = "strict") {
  const label = aiImageLockConfig(lockLevel).label || lockLevel;
  return String(label).endsWith("锁定") ? String(label) : `${label}锁定`;
}

function aiImageSizeLabel(size) {
  return {
    "1024x1024": "1:1 · 1024",
    "1024x1536": "2:3 · 1024x1536",
    "1536x1024": "3:2 · 1536x1024",
    "1024x1792": "9:16 · 1024x1792",
    "1792x1024": "16:9 · 1792x1024",
    "768x1024": "3:4 · 768x1024",
    "1024x768": "4:3 · 1024x768",
    auto: "auto",
  }[size] || size;
}

function aiImageProductBySku(sku) {
  const optionProduct = aiImageOptions().products.find((item) => item.sku === sku) || {};
  const boardProduct = state.items.find((item) => item.sku === sku) || {};
  return { ...optionProduct, ...boardProduct };
}

function aiImageProductContext(product = {}) {
  const selling = product.selling || {};
  const points = Array.isArray(selling.points) ? selling.points : [];
  const tags = Array.isArray(product.tags) ? product.tags : [];
  return {
    title: product.title || "the current product",
    subtitle: product.subtitle || "",
    headline: selling.headline || "",
    points,
    tags,
    proof: selling.proof || "",
  };
}

function aiImageModeConfig(modeKey = "text") {
  return aiImageModeOptions().find((item) => item.key === modeKey) || aiImageModeOptions()[0] || AI_IMAGE_MODES[0];
}

function aiImageModeLabel(modeKey = "text") {
  return aiImageModeConfig(modeKey).label;
}

function aiImagePromptIsStructured(value = "") {
  return String(value).includes("[Canvas]") && String(value).includes("[Product]") && String(value).includes("[Negative constraints]");
}

function aiImageIntentLooksLikeSuite(value = "") {
  return Boolean(aiImageSuiteKeyFromIntent(value));
}

function aiImageSuiteKeyFromIntent(value = "") {
  const source = String(value || "").toLowerCase();
  const codDetailSignal = source.includes("cod详情图")
    || source.includes("cod 详情图")
    || source.includes("cod detail")
    || source.includes("cod详情页")
    || source.includes("cod 详情页");
  if (codDetailSignal) return "cod-country-detail-12";
  const codSignal = source.includes("cod国家")
    || source.includes("国家cod")
    || source.includes("cod country")
    || source.includes("cod韩国")
    || source.includes("韩国cod")
    || source.includes("cod 韩国")
    || source.includes("cod落地页")
    || source.includes("主图8张")
    || source.includes("主图 8 张")
    || source.includes("详情22张")
    || source.includes("详情 22 张");
  if (codSignal) return "cod-country-landing-30";
  const amazonSignal = source.includes("amazon") || source.includes("亚马逊") || source.includes("a+内容") || source.includes("a+ 页面") || source.includes("a+专区");
  if (amazonSignal) return "amazon-jp-aplus-9";
  const rakutenSignal = source.includes("rakuten") || source.includes("乐天") || source.includes("楽天") || source.includes("楽天市場");
  const rakutenSuiteSignal = source.includes("乐天专区")
    || source.includes("楽天专区")
    || source.includes("rakuten suite")
    || source.includes("乐天9张")
    || source.includes("乐天 9 张")
    || source.includes("楽天9枚")
    || (rakutenSignal && (source.includes("整套商品图") || source.includes("商品图套图") || source.includes("9张商品图") || source.includes("9 张商品图")));
  if (rakutenSuiteSignal) return "rakuten-jp-product-9";
  const landingSignal = source.includes("落地页") || source.includes("landing page") || source.includes("一整套") || source.includes("套图");
  const countSignal = /(?:8|10|12|16|20|24|25|30|32)\s*(?:张|页)/.test(source)
    || source.includes("二十五张") || source.includes("三十二张") || source.includes("十张") || source.includes("十页");
  const pageSignal = source.includes("一张图片一个卖点") || source.includes("一个卖点一张") || source.includes("图片顺序");
  return landingSignal && (countSignal || pageSignal) ? "jp-landing-page-25" : "";
}

function aiImageSuiteConfig(value = {}) {
  const key = typeof value === "string" ? value : value?.suiteKey || "";
  const config = AI_IMAGE_SUITE_CONFIGS[AI_IMAGE_SUITE_KEY_ALIASES[key] || key] || null;
  if (!config || typeof value === "string") return config;
  if (config.key === "cod-country-detail-12") {
    const requestedCount = Number(value?.suiteCount || value?.count || config.count);
    const count = AI_IMAGE_COD_DETAIL_COUNT_OPTIONS.includes(requestedCount) ? requestedCount : config.count;
    return {
      ...config,
      count,
      label: `COD详情图 ${count}张`,
      planTitle: `COD详情图 ${count}张动态导演脚本`,
      planHint: `按品类生成全颜色/规格覆盖、促销、背书、痛点、全面海报、5个主卖点、${Math.max(0, count - 12)}个次卖点、多角度/场景、好评与收尾`,
      monitor: {
        ...config.monitor,
        description: `监控 ${count} 张详情图的原始卖点视觉化、颜色/规格覆盖、场景机位去重、促销、背书、主次卖点与国家本土化规则。`,
      },
    };
  }
  if (config.key !== "cod-country-landing-30") return config;
  const requestedCount = Number(value?.suiteCount || value?.count || config.count);
  const count = AI_IMAGE_COD_COUNT_OPTIONS.includes(requestedCount) ? requestedCount : config.count;
  const mainCount = Math.min(8, count);
  const detailCount = Math.max(count - mainCount, 0);
  const breakdown = detailCount ? `${mainCount} 张主图 + ${detailCount} 张详情图` : `${mainCount} 张主图`;
  return {
    ...config,
    count,
    label: `COD国家落地页 ${count}图`,
    planTitle: `COD国家落地页 ${count}图导演脚本`,
    planHint: `按目标国家生成 ${breakdown}，覆盖产品颜色/规格并让场景机位逐页变化`,
    promptPlaceholder: `填写当前产品名称、全部颜色/规格、主卖点、次卖点和特殊要求；系统会结合产品图按所选国家生成 ${breakdown}`,
    monitor: {
      ...config.monitor,
      description: `监控 ${breakdown}、原始卖点视觉化、全颜色/规格覆盖、场景机位去重、产品一致性与国家本土化规则。`,
      planLabel: breakdown,
    },
  };
}

function aiImageSuiteActive(conversation = {}) {
  return Boolean(aiImageSuiteConfig(conversation));
}

function aiImageSuiteCount(conversation = {}) {
  return Number(aiImageSuiteConfig(conversation)?.count || 0);
}

function aiImageSuiteUnit(conversation = {}) {
  return aiImageSuiteConfig(conversation)?.unit || "张";
}

function aiImageSuiteResultClass(conversation = {}) {
  return aiImageSuiteConfig(conversation)?.resultClass || "";
}

function aiImageCodCountryActive(conversation = {}) {
  return ["cod-country-landing-30", "cod-country-detail-12"].includes(aiImageSuiteConfig(conversation)?.key || "")
    || conversation.templateKey === "codHook";
}

function aiImageCodCountryConfig(value = "KR") {
  return AI_IMAGE_COD_COUNTRIES.find((country) => country.value === value) || AI_IMAGE_COD_COUNTRIES[0];
}

function aiImageCodHookTypeConfig(value = "hook") {
  return AI_IMAGE_COD_HOOK_TYPES.find((item) => item.key === value) || AI_IMAGE_COD_HOOK_TYPES[0];
}

function aiImageCanvasInstruction(size = "1024x1024") {
  const map = {
    "1024x1024": "square 1:1 canvas, balanced mobile-feed composition",
    "1024x1536": "vertical 2:3 canvas, full ecommerce fashion composition",
    "1536x1024": "horizontal 3:2 canvas, wide advertising composition",
    "1024x1792": "vertical 9:16 canvas, keep important content inside mobile safe areas",
    "1792x1024": "horizontal 16:9 canvas, cinematic advertising composition",
    "768x1024": "vertical 3:4 product canvas",
    "1024x768": "horizontal 4:3 lifestyle scene canvas",
    "750x1000": "exact 750 by 1000 pixel vertical 3:4 country-targeted COD landing-page image with full-bleed design and no white outer margin",
    "750x150": "exact 750 by 150 pixel ultra-wide COD promotion strip whose background fills the complete width edge to edge; keep every foreground element fully inside an 18-pixel top-and-bottom safe zone, one horizontal reading line, no clipped text or product, no centered miniature banner and no unused side bands",
    "750x100": "exact 750 by 100 pixel ultra-wide COD price strip whose background fills the complete width edge to edge; keep every foreground element fully inside a 12-pixel top-and-bottom safe zone, one horizontal reading line, no clipped currency, price, quantity label, text or product, no centered miniature banner and no unused side bands",
    "970x600": "exact 970 by 600 pixel horizontal Amazon Japan A+ content asset",
    "1200x1200": "exact 1200 by 1200 pixel square Rakuten Japan product-page image",
    "1500x2000": "exact 1500 by 2000 pixel vertical 3:4 Japanese ecommerce landing-page canvas",
    auto: "choose the most effective ecommerce advertising canvas",
  };
  return map[size] || `${size} pixel ecommerce advertising canvas`;
}

function aiImageReferenceInstruction(mode = "text", hasReferences = false, { genericProduct = false } = {}) {
  if (mode === "inpaint") {
    return "Image 1 is the source image and the uploaded mask defines the only editable area. Change only the masked region. Keep every unmasked pixel unchanged. Blend the edited area seamlessly with matching perspective, light, grain and shadows.";
  }
  if (mode === "compose") {
    if (genericProduct) {
      return "Use reference image 1 as the exact product identity. Follow the reference role map for every later image. Never merge products, borrow unsupported parts from another item or change the product category.";
    }
    return "Use reference image 1 as the product identity and follow the reference role map for every later image. Combine only the requested styling, usage, scene, layout or accessory cues into one coherent photograph. Never merge garments or transfer another garment onto the main product.";
  }
  if (mode === "edit" || hasReferences) {
    if (genericProduct) {
      return "Reference image 1 is the product source. First identify its real category, shape, parts, materials, proportions, controls, connections, packaging and visible branding. Preserve those exact attributes; change only scene, camera, lighting, localized usage and advertising layout requested by the user.";
    }
    return "Reference image 1 defines the product identity. Change only the requested background, model pose, camera, lighting and advertising layout.";
  }
  if (genericProduct) {
    return "Create a commercially realistic product image from the current product description. Keep the actual product category, construction, materials and use method clear and believable.";
  }
  return "Create a commercially realistic Japanese womenswear image with a clearly readable garment silhouette and believable fabric behavior.";
}

function aiImageTemplateDirection(templateKey, productName, size = "") {
  if (templateKey === "codHook" && ["750x150", "750x100"].includes(size)) {
    return `one standalone country-targeted COD ecommerce strip at exactly ${size} pixels. Design directly on the ultra-wide strip and fill the entire 750-pixel width from the left edge to the right edge; never create a square or vertical poster and then shrink it into a centered banner. Build one single-row composition: product or result zone uses about 20-25% of the width, the headline and exact price zone uses about 48-55%, and the quantity, specification or action cue uses about 20-25%. Keep every foreground element inside the internal safe zone: 12 pixels at the top and bottom for 750x100, or 18 pixels for 750x150. The background alone may bleed to the edges. Show complete glyphs, currency marks, prices, quantity labels, products and buttons; no element may be cropped, hidden behind another element or extend beyond the canvas. Limit 750x100 to one compact line and remove decorative copy before reducing required information. Before final rendering, audit all four boundaries and correct every clipped element. If the provider uses a square or taller fallback canvas, place one complete ultra-wide banner in a clearly bounded central horizontal band so it can be extracted intact. No centered miniature banner, gray placeholder bands, empty side margins, tall poster, full-body model, stacked card wall, multi-row landing page or tiny paragraph text`;
  }
  const configured = aiImageTemplateOptions().find((item) => item.key === templateKey)?.direction;
  if (configured) return `${configured}${templateKey === "detail" ? ` for ${productName}` : ""}`;
  const directions = {
    main: "Japanese womenswear lifestyle advertisement, Japanese woman age 25-35 wearing the product, natural confident pose, refined Tokyo editorial styling, layered real-world setting with depth, warm gray and muted green environment, premium but approachable ecommerce photography",
    scene: "non-white lifestyle scene in a bright Japanese apartment, cafe terrace or quiet Tokyo street, visible furniture or architecture, foreground and background layers, natural lived-in details, realistic depth, the product remains the clear focal point",
    model: "full-body or three-quarter model wearing the product, natural standing or walking pose, coordinated daily outfit visible from head to toe, accurate fit around waist, shoulders and hem, vertical Japanese catalog photography",
    virtualTryOn: "one coherent photorealistic full-body fashion photograph assembled from the explicitly assigned references. Preserve the exact identity, face, hair, age impression, skin tone and body proportions from 人物参考. Use every 主商品 image as an exact garment or wearable-product source, and use 包袋参考, 帽子参考, 鞋履参考, 首饰参考, 穿搭配饰 and explicitly named 包装与配件 as exact item sources. Use 场景参考 for the requested environment. Every input image is source-only: extract the assigned person or item, discard its original frame and non-selected background, and never display any reference as a separate tile, inset, thumbnail, cutout card or side-by-side panel. Expand a cropped person reference into a believable head-to-toe pose when requested, with natural anatomy, contact, scale, occlusion, fabric behavior and shadows. Return one standalone single-camera scene, never a grid or collage",
    detail: `premium ecommerce detail study for ${productName}, macro and medium close-up views of fabric texture, stitching, waist, neckline, sleeve, hem and construction, tactile material rendering on a warm light-gray textile surface`,
    facebook: "Facebook and Instagram feed ad creative, immediate focal point, product benefit readable at first glance, strong subject-background separation, energetic asymmetric composition, room for optional copy overlay, conversion-focused fashion photography",
    poster: "information-rich Japanese Rakuten fashion poster, large model on the right with full product silhouette, designed advertising area on the left, layered editorial panels, color swatch blocks, size badge shapes and benefit callouts, warm light-gray paper texture, red and gold accent shapes, use intentional blank label areas instead of fake readable text",
    landing: "fixed 25-image Japanese mature-womenswear landing page, exact 1500x2000 full-bleed vertical assets, 10 main images followed by 15 detail images: brand hero, three core selling points, five secondary selling points, fair pain-point comparison, brand philosophy, 2x2 four-pain grid, solution, eight matching deep-proof pages, comprehensive comparison, material and craft, verified size plus complete real colors, and quality close; exact garment identity, Japanese women age 35-55, documentary daylight; hero pages use one photograph plus approved copy, ordinary pages use one photograph plus at most one planned proof inset, and only comparison, pain-grid and size/color pages use structured layouts",
    amazonAplus: "coordinated nine-module Amazon Japan A+ product content set, exact 970x600 horizontal assets, dynamic product-category analysis, product-first information hierarchy, restrained localized lifestyle or professional photography, structure, materials, use cases, specifications, compatibility and maintenance proof, generous safe margins, no prices, promotions, reviews, ratings, Amazon logos or interface elements",
    rakutenSuite: "coordinated nine-image Rakuten Japan product-page set, exact 1200x1200 square assets, dynamic product-category analysis, strong mobile-thumbnail recognition, information-rich but disciplined Japanese marketplace layout, realistic localized lifestyle or professional photography, structure, materials, use cases, specifications and maintenance proof, no fabricated prices, rankings, reviews, Rakuten logos or interface elements",
    codKorea: "coordinated country-targeted COD landing-page image suite with up to eight conversion-focused main images followed by product-specific detail images, exact 750x1000 full-bleed vertical assets, country-localized language, people, scenes, palette and ecommerce hierarchy, dynamic product-category analysis from the reference image and current prompt, pain-point comparisons, static steps and a final product-information image, no prices, animation, platform UI, fabricated data or white outer margins",
    codHook: "one standalone country-targeted COD hook image, exact 750x1000 full-bleed vertical asset, built directly from the user's single hook prompt and the uploaded product reference. Use one dominant product or result visual, a bold local-market visual hook, clear product-specific evidence, dramatic but believable perspective, strong contrast and localized people, scene and copy. Keep the hook focused on one point; do not turn it into a suite, contact sheet, generic poster or platform interface.",
    reels: "9:16 Reels cover, dynamic centered fashion pose, visual movement in fabric and hair, clear face and garment, strong top-middle focal point, generous safe areas for later title overlay, mobile-first composition",
    refresh: "refresh the supplied ecommerce photo into a current premium Japanese fashion campaign, improve environment, pose, lighting, depth and commercial polish while keeping the product exactly recognizable",
    inpaint: "repair or replace only the masked area according to the user intent, preserve the original product and all unmasked content, seamless photorealistic integration",
    compose: "build one believable Japanese fashion advertising photograph from the supplied references, prioritize the exact product from image 1, then borrow only pose, scene and mood from the remaining images",
  };
  return directions[templateKey] || directions.main;
}

function productAiPrompt(product = {}, options = {}) {
  return aiImageTemplatePrompt(options.templateKey || "main", product, Boolean(options.hasReferences), {
    mode: options.mode || "text",
    size: options.size || "1024x1536",
    userIntent: options.userIntent || "",
    lockLevel: options.lockLevel || aiImageSkillConfig().defaults?.lockLevel || "strict",
    country: options.country || "KR",
    codHookType: options.codHookType || "hook",
    referenceRoles: options.referenceRoles || [],
  });
}

function aiImageTemplatePrompt(templateKey, product = {}, hasReferences = false, options = {}) {
  const context = aiImageProductContext(product);
  const isCountryCod = templateKey === "codKorea";
  const isCodHook = templateKey === "codHook";
  const isJapanLanding = templateKey === "landing";
  const isVirtualTryOn = templateKey === "virtualTryOn";
  const codHookType = aiImageCodHookTypeConfig(options.codHookType || "hook");
  const isGenericProductSuite = ["landing", "amazonAplus", "rakutenSuite", "codKorea", "codHook"].includes(templateKey);
  const productName = context.title || (isCodHook && !hasReferences ? "the product described in the current user prompt" : isGenericProductSuite ? "the product shown in reference image 1" : "the current product");
  const mode = options.mode || (hasReferences ? "edit" : "text");
  const lockLevel = options.lockLevel || aiImageSkillConfig().defaults?.lockLevel || "strict";
  const lock = aiImageLockConfig(lockLevel);
  const targetCountry = (isCountryCod || isCodHook) ? aiImageCodCountryConfig(options.country || "KR") : null;
  const globalRules = aiImageSkillConfig().global || {};
  const userIntent = String(options.userIntent || "").trim();
  const explicitNoVisibleText = /(?:不要|无需|不需要|禁止|去掉|移除|无)(?:添加|出现|显示|保留|任何)?[\s、，,:：-]{0,3}(?:文字|文案|标题|标语|字幕|标签)|(?:纯|只要)(?:画面|图片|场景|产品图|模特图).{0,8}(?:无字|无文字)|\b(?:no|without)\s+(?:added\s+)?(?:text|copy|headline|caption|label)s?\b/i.test(userIntent);
  const userPromptFidelityRule = [
    "[User-prompt fidelity lock — highest content priority] The current user prompt is the binding content contract for this image.",
    "Preserve every explicit product, category, color or specification, target country, visible language, person identity or casting, scene, action, camera intent, composition, visual style, palette, typography, selling point, requested text, quantity rule and exclusion from that prompt.",
    "The selected template may organize the fixed canvas, reference roles, product consistency and visual hierarchy only. It must not replace, weaken, generalize, reinterpret or contradict an explicit user requirement. Use template defaults only where the user prompt is silent.",
    "Product-reference identity and the selected canvas remain locked. Before rendering, correct any changed product, omitted requirement, invented feature, wrong language, substituted scene or conflicting template default.",
    userIntent ? `[Current user prompt — verbatim]\n${userIntent}` : "[Current user prompt] No separate production brief was entered; follow the selected template and uploaded references without inventing product facts.",
  ].join("\n");
  const sellingPoints = [context.headline, ...context.points, context.proof].filter(Boolean).slice(0, 6);
  const styleTags = context.tags.filter(Boolean).slice(0, 6);
  const productDescription = [productName, context.subtitle, styleTags.length ? `style tags: ${styleTags.join(", ")}` : ""].filter(Boolean).join("; ");
  const productRule = isGenericProductSuite
    ? `${productDescription}. Treat ${hasReferences ? "the uploaded product images and current user prompt" : "the current user prompt"} as the only product source. Identify the actual product category before composing; the complete product, its key parts and real use method must remain easy to inspect.`
    : `${productDescription}. The garment must be the visual priority and its shape, fit and fabric must remain easy to inspect.`;
  const genericLockRules = {
    standard: "Preserve the product category, main color, overall form and recognizable construction. Minor presentation cleanup is allowed only when product recognition is unchanged.",
    strict: "Preserve the exact product category, shape, proportions, color, materials, parts, controls, connections, surface details, packaging and visible branding. Do not redesign the product or add unsupported components.",
    exact: "Reproduce the product from every reference assigned as 主商品 as faithfully as possible. When several 主商品 references show different colors, patterns, packages or specification variants, treat all of them as exact product sources rather than using only reference image 1. Product identity overrides scene and styling instructions.",
  };
  const consistencyRule = isGenericProductSuite
    ? genericLockRules[lockLevel] || genericLockRules.strict
    : lock.instruction || AI_IMAGE_LOCK_LEVELS[1].instruction;
  const materialRule = isGenericProductSuite
    ? "Photorealistic, category-accurate materials and surface texture, believable product physics and results, realistic skin when people appear, soft directional light, natural shadows and polished local ecommerce color grading."
    : globalRules.materialAndLight || "Photorealistic fabric texture, accurate folds and seams, soft directional daylight with controlled fill light, realistic skin, natural shadows, premium Japanese ecommerce color grading.";
  const layoutRule = isVirtualTryOn
    ? "One coherent edge-to-edge full-body fashion photograph with one model, one continuous camera view and one continuous scene. Keep the complete head, hands, outfit, bag and shoes visible with natural scale and spacing."
    : isGenericProductSuite
    ? "Clear product-first hierarchy, complete product visibility, category-appropriate proof, strong first-glance recognition, readable localized information zones and polished full-bleed ecommerce composition."
    : globalRules.advertisingLayout || "Clear visual hierarchy, complete garment silhouette, useful negative space, strong first-glance product recognition, polished commercial finish.";
  const sellingPointRule = isVirtualTryOn
    ? "[Virtual styling output] Create exactly one clean finished full-body model scene. Apply every garment and styling replacement explicitly requested by filename or selected role. Preserve every unspecified person or outfit attribute. No advertising text, benefit cards, comparison panels or product cutout insets."
    : sellingPoints.length
    ? `[Candidate selling points for AI ranking — source only] ${sellingPoints.join("; ")}. Select the one point that best matches the current user prompt; do not render this whole list as separate labels or modules.`
    : isGenericProductSuite
    ? "[Selling-point selection] Use the current user prompt as the source of truth. Select one dominant benefit for this image and prove it with one category-appropriate detail, use action or result."
    : "[Selling points] Show flattering fit, wearable comfort and premium material through the image rather than text.";
  const negativeRule = isVirtualTryOn
    ? "No unrequested face, hairstyle, age, skin tone or body-proportion change. No omitted requested item, leftover replaced garment or accessory, item duplication, product redesign, unsupported color change, warped anatomy, fused limbs, floating clothing, wrong item scale, plastic skin, text, logo, watermark, split screen, before-and-after panel, grid, contact sheet, collage, card, inset or duplicate model."
    : isGenericProductSuite
    ? "No plain white outer background, isolated floating cutout, generic empty studio, product redesign, changed color, invented part, wrong use method, distorted anatomy, extra fingers or limbs, plastic skin, random letters, fake logo, watermark, frame or collage border."
    : globalRules.negativeConstraints || "No plain white background, no isolated floating product cutout, no generic empty studio, no product redesign, no changed color or pattern, no distorted anatomy, no extra fingers or limbs, no warped garment, no plastic skin, no random letters, no fake logo, no watermark, no frame or collage border.";
  const codHookRule = isCodHook
    ? `[COD hook mode] Selected creative type: ${codHookType.label}. ${codHookType.instruction} Generate each requested output as one finished standalone image from the current single prompt. Preserve the user's intended selling point and exact supplied promotion or price text. Keep the product as the dominant subject, use one main hook only, and do not add unrelated claims, generic filler copy or repeated benefit cards.`
    : "";
  const codHookTextRule = isCodHook
    ? explicitNoVisibleText
      ? "[COD hook text policy — highest text priority] Create a text-free hook image and communicate the selected point through the product, result, scene, action and composition only."
      : `[COD visible-copy lock — highest text priority] This is a finished ${targetCountry?.label || "local-market"} COD selling graphic. Render one short, prominent ${targetCountry?.language || "localized"} headline derived only from the current user prompt, plus the one exact hook, promotion, discount or price element required by the selected creative type. Keep copy few, large and readable; omit paragraphs, filler labels and invented claims.`
    : "";
  const singleImageContentBudgetRule = isVirtualTryOn
    ? ""
    : isCodHook
    ? "[AI single-image content budget — highest layout priority] Read the complete user prompt first, select exactly one dominant hook, and keep the product or result as the largest visual. Visible copy may contain one short headline plus the one hook, promotion or price element explicitly requested by the selected COD hook type. Do not add another selling point, paragraph, badge row, icon row, card wall, comparison collection or unrelated inset."
    : "[AI single-image content budget — highest layout priority] Read the complete user prompt and candidate selling points, then select exactly one primary message for this image and at most one directly supporting proof detail. Use one dominant product, model or result visual covering most of the canvas, one short headline and at most one small supporting callout. Do not visualize every supplied selling point, repeat the prompt as copy, or add paragraphs, badge rows, icon rows, card walls or unrelated insets.";
  const referenceRoleMap = aiImageReferenceRoleMap(options.referenceRoles || [], hasReferences);
  const productReferenceIndexes = (options.referenceRoles || [])
    .map((reference, index) => ({ index: index + 1, role: aiImageReferenceRoleKey(reference, index) }))
    .filter((item) => item.role === "product")
    .map((item) => item.index);
  const personReferenceIndexes = (options.referenceRoles || [])
    .map((reference, index) => ({ index: index + 1, role: aiImageReferenceRoleKey(reference, index) }))
    .filter((item) => item.role === "person")
    .map((item) => item.index);
  const multiProductVariantRule = (isCountryCod || isCodHook || isJapanLanding) && productReferenceIndexes.length > 1
    ? `[Multi-product variant lock] Reference images ${productReferenceIndexes.join(", ")} are separate documented product colors, patterns, packages or specification variants. Inspect and preserve every one. Reference image 1 is not the only color source. Across the requested outputs, rotate the exact variants so each appears; when only one output is requested, show the complete real range in one designed product lineup.`
    : "";
  const hasExternalStyleSet = (options.referenceRoles || []).some((reference, index) => aiImageReferenceRoleKey(reference, index) === "styleSet");
  const virtualTryOnRule = isVirtualTryOn
    ? `[Virtual styling binding — highest priority] The reference role map, filenames and current user prompt jointly define an exact item-to-image contract. Garment or wearable-product sources: reference image${productReferenceIndexes.length > 1 ? "s" : ""} ${productReferenceIndexes.join(", ") || "assigned as 主商品"}. Identity source: reference image${personReferenceIndexes.length > 1 ? "s" : ""} ${personReferenceIndexes.join(", ") || "assigned as 人物参考"}. Apply requested layers in this order: scene, person identity and proportions, garments, shoes, bag, hat, then earrings or other jewelry. For every requested replacement, copy the assigned source item's exact category, shape, proportions, color, print, material, hardware and construction; only make an attribute change such as recoloring when explicitly requested. All uploaded images are source-only and must disappear into the final composite: never reproduce their original rectangular frame, source background, border or image boundary, and never place a reference beside the model as a tile, product cutout, thumbnail, card or comparison panel. Preserve the model's identity and every unspecified item. The prompt may explicitly replace accessories, change the scene, complete a cropped body, or adapt the pose so all products are visible. Integrate all layers with realistic fit, scale, perspective, occlusion, contact and cast shadows. Output exactly one continuous full-body photograph with one model and one camera view; no grid, split screen, collage, card, inset or duplicated view.`
    : "";
  const referenceInstruction = isVirtualTryOn
    ? "Use the selected role and filename of every reference as a binding instruction. 主商品 supplies exact garments or wearable products; 人物参考 supplies identity; 场景参考 supplies the environment; 包袋参考, 帽子参考, 鞋履参考, 首饰参考 and 穿搭配饰 supply exact styling items. For backward compatibility, explicitly named 包装与配件 images also supply exact requested styling items."
    : aiImageReferenceInstruction(mode, hasReferences, { genericProduct: isGenericProductSuite });
  const sections = [
    userPromptFidelityRule,
    `[Canvas] ${aiImageCanvasInstruction(options.size || "1024x1536")}.`,
    targetCountry ? `[Target market] ${targetCountry.label}; visible language: ${targetCountry.language}. Localize people, scenes, layout, color and copy for this market.` : "",
    `[Product] ${productRule}`,
    `[Product consistency: ${lock.label || lockLevel}] ${consistencyRule}`,
    `[Reference rules] ${referenceInstruction}`,
    referenceRoleMap ? `[Reference role map] ${referenceRoleMap}` : "",
    virtualTryOnRule,
    multiProductVariantRule,
    hasExternalStyleSet ? "[External style-set lock] References assigned as 系列风格参考 control only the suite visual system: palette, visual hierarchy, headline scale, information density, module shapes, callout rhythm, image-to-text ratio, macro or result presentation and cross-page pacing. Reference image 1 remains the exact product source. Never import another product, person, text, logo, badge, certification or claim from style-set references. Generated suite page 1 must adapt this visual DNA as the shared style anchor; later pages inherit that anchor while using clearly different compositions." : "",
    `[Scene and model] ${aiImageTemplateDirection(templateKey, productName, options.size || "")}.`,
    codHookTextRule,
    codHookRule,
    singleImageContentBudgetRule,
    sellingPointRule,
    `[Material and light] ${materialRule}`,
    `[Advertising layout] ${layoutRule}`,
    `[No added marks] ${AI_IMAGE_NO_ADDED_MARKS_RULE}`,
    `[Negative constraints] ${negativeRule}`,
  ];
  return sections.filter(Boolean).join("\n");
}

function adLaunchValue(selector, fallback = "") {
  const el = $(selector);
  if (!el) return fallback;
  return el.value || fallback;
}

function splitAdLaunchList(value, { uppercase = false, splitWhitespace = false } = {}) {
  const pattern = splitWhitespace ? /[,，\s\n;；]+/ : /[,，\n;；]+/;
  const seen = new Set();
  return String(value || "")
    .split(pattern)
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => (uppercase ? item.toUpperCase() : item))
    .filter((item) => {
      const key = item.toLowerCase();
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
}

function checkedAdLaunchValue(name, fallback = "") {
  return document.querySelector(`input[name="${name}"]:checked`)?.value || fallback;
}

function selectedAdLaunchPlacements() {
  return Array.from(document.querySelectorAll("[data-ad-launch-placement]:checked")).map((input) => input.dataset.adLaunchPlacement);
}

function adLaunchMaterialMode() {
  return state.adLaunches.materialMode || "single_image";
}

function adLaunchMaterialConfig() {
  return AD_LAUNCH_MATERIAL_MODES[adLaunchMaterialMode()] || AD_LAUNCH_MATERIAL_MODES.single_image;
}

function setAdLaunchMaterialMode(mode) {
  state.adLaunches.materialMode = AD_LAUNCH_MATERIAL_MODES[mode] ? mode : "single_image";
  const config = adLaunchMaterialConfig();
  document.querySelectorAll("[data-ad-launch-material-tab]").forEach((button) => {
    const active = button.dataset.adLaunchMaterialTab === state.adLaunches.materialMode;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", active ? "true" : "false");
  });
  const fileInput = $("#ad-launch-file");
  if (fileInput) {
    fileInput.accept = config.accept;
    fileInput.value = "";
  }
  renderAdLaunchMaterial();
  renderAdLaunchMaterialGuidance();
  renderAdLaunchPreview();
}

function adLaunchPlacementMode() {
  return checkedAdLaunchValue("ad-launch-placement-mode", "advantage");
}

function setAdLaunchRadio(name, value) {
  document.querySelectorAll(`input[name="${name}"]`).forEach((input) => {
    input.checked = input.value === value;
  });
}

function adLaunchDraftSnapshot() {
  const account = selectedAdLaunchAccount();
  const campaign = selectedAdLaunchCampaign();
  const adset = selectedAdLaunchAdset();
  const campaignMode = adLaunchValue("#ad-launch-campaign-mode", "create");
  const adsetMode = adLaunchValue("#ad-launch-adset-mode", "create");
  return {
    productSku: adLaunchValue("#ad-launch-product"),
    accountId: account.accountId || adLaunchValue("#ad-launch-account"),
    accountName: account.accountName || adLaunchValue("#ad-launch-account"),
    credentialId: account.credentialId || "",
    credentialName: account.credentialName || (account.credentialId ? account.credentialId : "旧版全局 Token"),
    campaignMode,
    campaignName: campaignMode === "select" ? campaign.campaignName || "" : adLaunchValue("#ad-launch-campaign-name"),
    objective: adLaunchValue("#ad-launch-objective", "OUTCOME_TRAFFIC"),
    adsetMode,
    adsetName: adsetMode === "select" ? adset.adsetName || "" : adLaunchValue("#ad-launch-adset-name"),
    dailyBudget: Number(adLaunchValue("#ad-launch-daily-budget", 10) || 0),
    optimizationGoal: adLaunchValue("#ad-launch-optimization", "LINK_CLICKS"),
    countries: splitAdLaunchList(adLaunchValue("#ad-launch-countries", "JP"), { uppercase: true, splitWhitespace: true }),
    regions: splitAdLaunchList(adLaunchValue("#ad-launch-regions")),
    cities: splitAdLaunchList(adLaunchValue("#ad-launch-cities")),
    languages: splitAdLaunchList(adLaunchValue("#ad-launch-languages")),
    gender: checkedAdLaunchValue("ad-launch-gender", "all"),
    ageMin: Number(adLaunchValue("#ad-launch-age-min", 18) || 18),
    ageMax: Number(adLaunchValue("#ad-launch-age-max", 65) || 65),
    advancedAudience: Boolean($("#ad-launch-advanced-audience")?.checked),
    interestInclude: splitAdLaunchList(adLaunchValue("#ad-launch-interest-include")),
    interestExclude: splitAdLaunchList(adLaunchValue("#ad-launch-interest-exclude")),
    audienceSeed: adLaunchValue("#ad-launch-audience-seed"),
    placementMode: adLaunchPlacementMode(),
    placements: selectedAdLaunchPlacements(),
    materialMode: adLaunchMaterialMode(),
    multiMaterial: Boolean($("#ad-launch-multi-material")?.checked),
    advantageCreative: Boolean($("#ad-launch-advantage-creative")?.checked),
    creativeOrder: checkedAdLaunchValue("ad-launch-creative-order", "left_to_right"),
    materialName: state.adLaunches.material?.name || "",
    materialType: state.adLaunches.material?.type || adLaunchMaterialConfig().type,
    pageId: adLaunchValue("#ad-launch-page-id"),
    igId: adLaunchValue("#ad-launch-ig-id"),
    adName: adLaunchValue("#ad-launch-name"),
    headline: adLaunchValue("#ad-launch-headline"),
    primaryText: adLaunchValue("#ad-launch-primary-text"),
    linkUrl: adLaunchValue("#ad-launch-link-url"),
    cta: adLaunchValue("#ad-launch-cta", "SHOP_NOW"),
    previewType: adLaunchValue("#ad-launch-preview-type", "feed"),
    pixelId: adLaunchValue("#ad-launch-pixel-id"),
    conversionEvent: adLaunchValue("#ad-launch-conversion-event", "PURCHASE"),
    batchCount: Number(adLaunchValue("#ad-launch-batch-count", 1) || 1),
  };
}

function adLaunchEstimateAudience(snapshot) {
  const countryPop = {
    JP: 124000000,
    US: 258000000,
    CA: 31500000,
    AU: 21500000,
    GB: 56000000,
    DE: 70000000,
    FR: 56000000,
    KR: 43000000,
    TW: 19500000,
    HK: 6100000,
    SG: 4600000,
  };
  const countries = snapshot.countries.length ? snapshot.countries : ["JP"];
  let base = countries.reduce((sum, country) => sum + (countryPop[country] || 12000000), 0) * 0.58;
  const ageMin = Math.max(13, Math.min(65, snapshot.ageMin || 18));
  const ageMax = Math.max(ageMin, Math.min(65, snapshot.ageMax || 65));
  base *= Math.max(0.18, (ageMax - ageMin + 1) / 53);
  if (snapshot.gender !== "all") base *= 0.52;
  if (snapshot.regions.length) base *= Math.max(0.22, 0.72 - snapshot.regions.length * 0.08);
  if (snapshot.cities.length) base *= Math.max(0.08, 0.38 - snapshot.cities.length * 0.04);
  if (snapshot.languages.length) base *= Math.max(0.32, 0.9 - snapshot.languages.length * 0.08);
  if (snapshot.placementMode === "manual") {
    base *= Math.max(0.35, Math.min(1, snapshot.placements.length * 0.2));
  } else {
    base *= 1.06;
  }
  if (snapshot.advancedAudience) base *= 1.08;
  if (snapshot.interestInclude.length) base *= Math.max(0.18, 0.8 - snapshot.interestInclude.length * 0.08);
  if (snapshot.interestExclude.length) base *= Math.max(0.7, 1 - snapshot.interestExclude.length * 0.04);
  return Math.max(10000, Math.round(base / 10000) * 10000);
}

function formatAudienceSize(value) {
  if (value >= 100000000) return `约 ${(value / 100000000).toFixed(1)} 亿人`;
  if (value >= 10000) return `约 ${Math.round(value / 10000).toLocaleString("en-US")} 万人`;
  return `约 ${value.toLocaleString("en-US")} 人`;
}

function adLaunchSummaryRow(label, value) {
  return `<span><strong>${esc(label)}</strong>${esc(value || "-")}</span>`;
}

function renderAdLaunchMaterialGuidance() {
  const target = $("#ad-launch-material-guidance");
  if (!target) return;
  const config = adLaunchMaterialConfig();
  target.innerHTML = `
    <strong>${esc(config.label)}素材规范</strong>
    ${config.guidance.map((item) => `<span>${esc(item)}</span>`).join("")}
  `;
}

function ctaText(value) {
  const ctas = adLaunchOptions().ctas || {};
  return ctas[value] || { SHOP_NOW: "Shop Now", LEARN_MORE: "Learn More", SIGN_UP: "Sign Up", CONTACT_US: "Contact Us" }[value] || value || "Shop Now";
}

function renderAdLaunchPreview() {
  const card = $("#ad-launch-preview-card");
  if (!card) return;
  const snapshot = adLaunchDraftSnapshot();
  const material = state.adLaunches.material;
  const warning = $("#ad-launch-material-warning");
  if (warning) {
    const missing = [];
    if (!material) missing.push("上传素材");
    if (!snapshot.headline) missing.push("广告标题");
    if (!snapshot.primaryText) missing.push("正文文案");
    if (!snapshot.linkUrl) missing.push("推广网址");
    warning.textContent = missing.length ? `请先${missing.join("、")}。` : "素材和文案已就绪，可以进入下一步保存草稿。";
    warning.classList.toggle("is-ready", missing.length === 0);
  }
  const previewTone = snapshot.previewType === "story" ? "story" : snapshot.previewType === "reels" ? "reels" : "feed";
  const materialLabel = material ? `${material.type || snapshot.materialType} · ${material.name}` : `${AD_LAUNCH_MATERIAL_MODES[snapshot.materialMode]?.label || "素材"}待上传`;
  const headline = snapshot.headline || "广告标题会显示在这里";
  const body = snapshot.primaryText || "正文文案会显示在这里，建议写清楚痛点、主卖点和行动引导。";
  const url = snapshot.linkUrl || "https://sosove.com/products/...";
  card.className = `ad-preview-card ${previewTone}`;
  card.innerHTML = `
    <div class="ad-preview-page">
      <span class="brand-mark mini"><img src="/static/assets/sosove-logo.jpeg" alt="SOSOVE" /></span>
      <div>
        <strong>SOSOVE</strong>
        <small>${esc(snapshot.previewType === "feed" ? "Sponsored" : "Ad preview")}</small>
      </div>
    </div>
    <p>${esc(body)}</p>
    <div class="ad-preview-media ${material ? "has-material" : ""}">
      <strong>${esc(materialLabel)}</strong>
      <span>${esc(snapshot.multiMaterial ? "多素材广告已开启" : AD_LAUNCH_MATERIAL_MODES[snapshot.materialMode]?.guidance?.[0] || "上传后显示素材")}</span>
    </div>
    <div class="ad-preview-link">
      <small>${esc(url.replace(/^https?:\/\//, "").slice(0, 42))}</small>
      <strong>${esc(headline)}</strong>
      <button type="button">${esc(ctaText(snapshot.cta))}</button>
    </div>
  `;
}

function renderAdLaunchLiveSummary() {
  const summary = $("#ad-launch-live-summary");
  if (!summary) return;
  const snapshot = adLaunchDraftSnapshot();
  const placements = snapshot.placementMode === "advantage"
    ? "进阶版位"
    : (snapshot.placements.map((placement) => AD_LAUNCH_PLACEMENT_LABELS[placement] || placement).join(" / ") || "未选择");
  summary.innerHTML = [
    adLaunchSummaryRow("商品", snapshot.productSku || "不关联"),
    adLaunchSummaryRow("广告户", snapshot.accountName),
    adLaunchSummaryRow("投放凭证", snapshot.credentialName),
    adLaunchSummaryRow("系列", `${snapshot.campaignMode === "create" ? "新建" : "已有"} · ${snapshot.campaignName || "-"}`),
    adLaunchSummaryRow("广告组", `${snapshot.adsetMode === "create" ? "新建" : "已有"} · ${snapshot.adsetName || "-"}`),
    adLaunchSummaryRow("预算", `${money(snapshot.dailyBudget)}/day`),
    adLaunchSummaryRow("素材", `${AD_LAUNCH_MATERIAL_MODES[snapshot.materialMode]?.label || "素材"} · ${snapshot.materialName || "未上传"}`),
    adLaunchSummaryRow("版位", placements),
    adLaunchSummaryRow("批量", `${Math.max(1, Math.min(20, snapshot.batchCount || 1))} 条草稿`),
  ].join("");

  const estimate = adLaunchEstimateAudience(snapshot);
  const estimateEl = $("#ad-launch-estimated-size");
  const copyEl = $("#ad-launch-estimated-copy");
  const needle = $("#ad-launch-estimate-needle");
  if (estimateEl) estimateEl.textContent = formatAudienceSize(estimate);
  if (copyEl) {
    const level = estimate < 800000 ? "偏窄，适合精准测试" : estimate > 60000000 ? "偏宽，适合宽泛冷启动" : "适中，适合素材测试";
    copyEl.textContent = level;
  }
  if (needle) {
    const ratio = Math.max(0, Math.min(1, Math.log10(estimate) / 8.2));
    needle.style.transform = `rotate(${Math.round(-58 + ratio * 116)}deg)`;
  }
  const audience = $("#ad-launch-audience-summary");
  if (audience) {
    audience.innerHTML = [
      adLaunchSummaryRow("地区", snapshot.countries.join(", ") || "JP"),
      adLaunchSummaryRow("省市", [...snapshot.regions, ...snapshot.cities].join(", ") || "全部"),
      adLaunchSummaryRow("语言", snapshot.languages.join(", ") || "不限"),
      adLaunchSummaryRow("性别", AD_LAUNCH_GENDER_LABELS[snapshot.gender] || "全部"),
      adLaunchSummaryRow("年龄", `${snapshot.ageMin || 18}-${snapshot.ageMax || 65}`),
      adLaunchSummaryRow("兴趣", snapshot.interestInclude.join(", ") || "宽泛"),
    ].join("");
  }
  renderAdLaunchPreview();
}

function updateAdLaunchStepUI() {
  const max = AD_LAUNCH_STEPS.length - 1;
  state.adLaunches.step = Math.max(0, Math.min(max, Number(state.adLaunches.step || 0)));
  document.querySelectorAll("[data-ad-launch-step-panel]").forEach((panel) => {
    panel.hidden = Number(panel.dataset.adLaunchStepPanel) !== state.adLaunches.step;
  });
  document.querySelectorAll("[data-ad-launch-step-jump]").forEach((button) => {
    const index = Number(button.dataset.adLaunchStepJump);
    button.classList.toggle("active", index === state.adLaunches.step);
    button.classList.toggle("done", index < state.adLaunches.step);
    button.setAttribute("aria-pressed", index === state.adLaunches.step ? "true" : "false");
  });
  const prev = $("#ad-launch-prev-btn");
  const next = $("#ad-launch-next-btn");
  const save = $("#ad-launch-save-btn");
  const canCreate = canManageFacebookAds();
  if (prev) prev.disabled = !canCreate || state.adLaunches.step === 0;
  if (next) {
    next.hidden = state.adLaunches.step === max;
    next.disabled = !canCreate;
  }
  if (save) {
    save.hidden = state.adLaunches.step !== max;
    save.disabled = !canCreate;
  }
  renderAdLaunchLiveSummary();
}

function setAdLaunchStep(nextStep) {
  state.adLaunches.step = Math.max(0, Math.min(AD_LAUNCH_STEPS.length - 1, Number(nextStep || 0)));
  updateAdLaunchStepUI();
}

async function loadAdLaunches(refresh = false) {
  if (!state.auth.user) {
    state.adLaunches.loaded = false;
    state.adLaunches.launches = [];
    renderAdLaunchPanel();
    return;
  }
  const params = new URLSearchParams({ range: state.adLaunches.filters.range || "last_7d" });
  if (refresh) params.set("refresh", "true");
  const localAssetsPromise = api("/api/sku-board/meta-assets")
    .then((assetsPayload) => {
      mergeLocalMetaAccountsIntoAdLaunchOptions(assetsPayload);
      renderAdLaunchPanel();
      return assetsPayload;
    })
    .catch(() => null);
  const payload = await api(`/api/sku-board/ad-launches?${params.toString()}`);
  const localAssets = await localAssetsPromise;
  updateAdLaunchPayload(payload);
  mergeLocalMetaAccountsIntoAdLaunchOptions(localAssets || {});
  renderAdLaunchPanel();
  renderAiImagePanel();
}

function renderAdLaunchPanel() {
  const loginRequired = $("#ad-launch-login-required");
  const workspace = $("#ad-launch-workspace");
  if (!loginRequired || !workspace) return;
  const loggedIn = Boolean(state.auth.user);
  loginRequired.hidden = loggedIn;
  workspace.hidden = !loggedIn;
  if (!loggedIn) return;
  renderAdLaunchForm();
  renderAdLaunchKpis();
  renderAdLaunchList();
}

function renderAiImagePanel() {
  const loginRequired = $("#ai-image-login-required");
  const workspace = $("#ai-image-workspace");
  const quickEntry = $("#ai-image-quick-entry");
  if (!loginRequired || !workspace) return;
  const loggedIn = Boolean(state.auth.user);
  const allowed = loggedIn && canUseAiImages();
  loginRequired.hidden = allowed;
  workspace.hidden = !allowed;
  if (quickEntry) quickEntry.hidden = !allowed;
  const loginButton = loginRequired.querySelector("[data-open-login-from-ai-image]");
  if (!allowed) {
    loginRequired.querySelector("strong").textContent = loggedIn ? "当前账号无权限" : "请先登录";
    loginRequired.querySelector("p").textContent = loggedIn ? "管理员、运营、选品、设计可以使用 AI 生图；设计账号只负责做图，不会获得广告投放权限。" : "登录后可以按商品生成投放图片素材。";
    if (loginButton) loginButton.hidden = loggedIn;
    return;
  }
  if (loginButton) loginButton.hidden = false;
  ensureAiImageConversation();
  renderAiImageSidebar();
  renderAiImageForm();
  renderAiImageHealth();
  renderAiImageResults();
  renderAiImageReferences();
}

function aiImageHealthLabel(status) {
  return {
    ok: "服务正常",
    warning: "需注意",
    timeout: "连接超时",
    error: "连接失败",
    disabled: "未配置",
    checking: "检测中",
    unknown: "未检测",
  }[status] || "未检测";
}

function aiImageHealthTone(status) {
  if (status === "ok") return "ok";
  if (status === "warning") return "warning";
  if (status === "timeout" || status === "error") return "error";
  if (status === "checking") return "checking";
  return "unknown";
}

function renderAiImageNodeList(health = {}) {
  const list = $("#ai-image-node-list");
  if (!list) return;
  const configuredNodes = adLaunchOptions().aiImage?.nodes || [];
  const sourceNodes = Array.isArray(health.nodes) && health.nodes.length ? health.nodes : configuredNodes;
  if (!sourceNodes.length) {
    list.innerHTML = `<div class="ai-image-node-empty">${health.loading ? "正在读取节点配置..." : "还没有配置生图服务节点"}</div>`;
    return;
  }
  const fullCheck = Boolean(health.loading && !health.nodeLoadingId);
  list.innerHTML = `
    <div class="ai-image-node-list-head">
      <span>生图服务节点</span>
      <small>${esc(sourceNodes.length)} 个节点 · 密钥已隐藏 · 支持独立检测</small>
    </div>
    ${sourceNodes.map((node, index) => {
      const nodeId = node.id || `node-${index + 1}`;
      const nodeChecking = Boolean(health.loading && (fullCheck || health.nodeLoadingId === nodeId));
      const status = nodeChecking ? "checking" : (node.status || "unknown");
      const total = Number(node.accountPoolTotal || 0);
      const ready = Number(node.accountPoolReady || 0);
      const models = Array.isArray(node.models) ? node.models.filter(Boolean) : [];
      const generation = node.generation || {};
      const httpMeta = Number(node.httpStatus || 0) ? `HTTP ${Number(node.httpStatus)}` : "未返回 HTTP 状态";
      const timeMeta = node.checkedAt ? shortDate(node.checkedAt) : "等待检测";
      const address = node.rootUrl || node.baseUrl || "未配置地址";
      return `
        <article class="ai-image-node-card ${aiImageHealthTone(status)}">
          <div class="ai-image-node-main">
            <div class="ai-image-node-title">
              <strong>${esc(node.name || `生图节点 ${index + 1}`)}</strong>
              <span>${esc(aiImageHealthLabel(status))}</span>
            </div>
            <code title="${esc(address)}">${esc(address)}</code>
            <small>${esc(httpMeta)} · ${esc(Number(node.latencyMs || 0))}ms · ${esc(timeMeta)}</small>
            <div class="ai-image-node-facts">
              <span>账号池 <b>${total ? `${ready}/${total} 可用` : "待查询"}</b></span>
              <span>模型 <b>${esc(models.length ? models.slice(0, 3).join(" · ") : "待查询")}</b></span>
              <span>生成表现 <b>${Number(generation.attempts || 0) ? `${esc(generation.successRate || 0)}% · ${esc(formatAiImageDuration(generation.averageLatencyMs || 0))}` : "待统计"}</b></span>
            </div>
            <p>${esc(nodeChecking ? "正在查询任务通道、模型和账号池状态..." : (node.message || "点击右侧按钮检测当前节点。"))}</p>
          </div>
          <button class="mini-btn" type="button" data-ai-image-node-check="${esc(nodeId)}" ${health.loading ? "disabled" : ""}>${nodeChecking ? "检测中..." : "检测节点"}</button>
        </article>
      `;
    }).join("")}
  `;
}

function renderAiImageHealth() {
  const card = $("#ai-image-health-card");
  if (!card) return;
  const health = state.aiImages.health || {};
  const status = health.loading ? "checking" : (health.status || "unknown");
  card.className = `ai-image-health-card ${aiImageHealthTone(status)}`;
  $("#ai-image-health-label").textContent = aiImageHealthLabel(status);
  $("#ai-image-health-message").textContent = health.loading
    ? (health.nodeLoadingId ? "正在检测指定的生图服务节点..." : "正在并行检测全部生图服务节点...")
    : (health.message || "点击检测服务，确认域名、密钥和服务是否可用。");
  const poolMeta = ["remote_account_pool", "multi_node_account_pool"].includes(health.dispatchMode)
    ? ` · ${health.dispatchMode === "multi_node_account_pool" ? `服务节点 ${Number(health.configuredNodeCount || health.nodeCount || 0)} 个 · ` : ""}账号池 ${Number(health.accountPoolReady || 0)}/${Number(health.accountPoolTotal || 0)} 可用 · 自动调度`
    : "";
  $("#ai-image-health-meta").textContent = health.checkedAt
    ? `${health.baseUrl || "服务"} · ${health.latencyMs || 0}ms${poolMeta} · ${shortDate(health.checkedAt)}`
    : (health.baseUrl || "不会触发生图扣费");
  const button = $("#ai-image-health-btn");
  if (button) {
    button.disabled = Boolean(health.loading);
    button.textContent = health.loading ? "检测中..." : "检测服务";
  }
  renderAiImageNodeList(health);
}

async function loadAiImageHealth(silent = false, nodeId = "") {
  if (!state.auth.user || !canUseAiImages()) return;
  const previous = state.aiImages.health || {};
  state.aiImages.health = { ...previous, loading: true, nodeLoadingId: nodeId };
  renderAiImageHealth();
  try {
    const query = nodeId ? `?nodeId=${encodeURIComponent(nodeId)}` : "";
    const payload = await api(`/api/sku-board/ai-image-health${query}`);
    const incoming = payload.health || {};
    if (nodeId) {
      const configuredNodes = adLaunchOptions().aiImage?.nodes || [];
      const currentNodes = Array.isArray(previous.nodes) && previous.nodes.length ? previous.nodes : configuredNodes;
      const merged = new Map(currentNodes.map((node) => [node.id, node]));
      (incoming.nodes || []).forEach((node) => merged.set(node.id, node));
      const nodes = [...merged.values()];
      state.aiImages.health = {
        ...previous,
        ...incoming,
        nodes,
        nodeCount: nodes.length,
        configuredNodeCount: Number(incoming.configuredNodeCount || previous.configuredNodeCount || nodes.length),
        healthyNodeCount: nodes.filter((node) => node.status === "ok").length,
        accountPoolTotal: nodes.reduce((sum, node) => sum + Number(node.accountPoolTotal || 0), 0),
        accountPoolReady: nodes.reduce((sum, node) => sum + Number(node.accountPoolReady || 0), 0),
        loading: false,
        nodeLoadingId: "",
      };
    } else {
      state.aiImages.health = { ...incoming, loading: false, nodeLoadingId: "" };
    }
    if (!silent) showToast(state.aiImages.health.message || "AI 生图服务检测完成");
  } catch (error) {
    state.aiImages.health = {
      ...state.aiImages.health,
      status: "error",
      message: error.message,
      latencyMs: 0,
      checkedAt: new Date().toISOString(),
      loading: false,
      nodeLoadingId: "",
    };
    if (!silent) showToast(error.message);
  }
  renderAiImageHealth();
}

function mergeAiDirectorState(payload = {}) {
  state.aiImages.director = {
    ...(state.aiImages.director || {}),
    ...payload,
    loaded: true,
    loading: false,
  };
  return state.aiImages.director;
}

function renderAiDirectorSettings() {
  const section = $("#ai-director-settings");
  if (!section) return;
  const director = state.aiImages.director || {};
  const admin = isAdmin();
  section.hidden = !admin;
  if (!admin) return;
  if (!director.formDirty) {
    $("#ai-director-base-url").value = director.baseUrl || "";
    $("#ai-director-model").value = director.model || "gpt-5.6-terra";
    $("#ai-director-timeout").value = String(director.timeout || 60);
    $("#ai-director-enabled").checked = Boolean(director.enabled);
    $("#ai-director-vision").checked = director.visionEnabled !== false;
    $("#ai-director-open-prompts").checked = director.openImagePromptsEnabled !== false;
    $("#ai-director-review-enabled").checked = director.reviewEnabled !== false;
    $("#ai-director-review-threshold").value = String(director.reviewThreshold || 78);
    $("#ai-director-api-key").value = "";
  }
  const fallbackModels = Array.isArray(director.fallbackModels) ? director.fallbackModels.filter(Boolean) : [];
  const modelChain = [director.model || "gpt-5.6-terra", ...fallbackModels];
  const fallbackNote = $("#ai-director-fallback-note");
  if (fallbackNote) {
    const timeoutNote = director.attemptTimeout
      ? `；每个模型最多 ${director.attemptTimeout} 秒，整条链最多 ${director.totalTimeout || director.attemptTimeout} 秒`
      : "";
    fallbackNote.textContent = fallbackModels.length
      ? `主模型异常、超时或无有效内容时自动切换：${fallbackModels.join(" → ")}${timeoutNote}`
      : `主模型异常后将自动切换备用模型${timeoutNote}`;
  }
  $("#ai-director-api-key").placeholder = director.apiKeyConfigured
    ? "已保存密钥，留空则保持不变"
    : "输入 API 密钥";
  const stateEl = $("#ai-director-config-state");
  const busy = director.loading || director.saving || director.testing;
  const configured = Boolean(director.configured);
  const active = configured && director.enabled;
  stateEl.className = `ai-director-config-state ${active ? (director.secureTransport ? "ok" : "warning") : ""}`;
  stateEl.textContent = director.loading
    ? "读取中"
    : director.testing
    ? "检测中"
    : director.saving
    ? "保存中"
    : active
    ? `${modelChain.join(" → ")}${director.secureTransport ? " · 自动切换已启用" : " · HTTP · 自动切换"}`
    : configured
    ? "已配置 · 未启用"
    : "未配置";
  const message = $("#ai-director-settings-message");
  message.className = director.status === "error" ? "error" : director.status === "ok" ? "ok" : "";
  message.textContent = director.message
    || (!director.secureTransport && director.baseUrl
      ? "当前 API 使用 HTTP，密钥传输未加密。密钥仅保存在服务端。"
      : "密钥仅保存在服务端；Open Image Prompts 完整案例只交给AI导演提炼视觉蓝图，原提示词与参考图保持锁定。");
  $("#ai-director-save-btn").disabled = busy;
  $("#ai-director-test-btn").disabled = busy || !configured && !director.formDirty;
}

async function loadAiDirectorSettings(silent = false) {
  if (!isAdmin()) return null;
  state.aiImages.director = { ...(state.aiImages.director || {}), loading: true };
  renderAiDirectorSettings();
  try {
    const payload = await api("/api/sku-board/ai-director-settings");
    const director = mergeAiDirectorState({
      ...(payload.director || {}),
      status: "unknown",
      message: "",
      formDirty: false,
    });
    renderAiDirectorSettings();
    if (!silent) showToast(director.configured ? "AI 导演配置已加载" : "AI 导演尚未配置");
    return director;
  } catch (error) {
    mergeAiDirectorState({ status: "error", message: error.message, formDirty: false });
    renderAiDirectorSettings();
    if (!silent) showToast(error.message);
    return null;
  }
}

function aiDirectorSettingsFormPayload() {
  const model = $("#ai-director-model")?.value.trim() || "";
  return {
    enabled: Boolean($("#ai-director-enabled")?.checked),
    baseUrl: $("#ai-director-base-url")?.value.trim() || "",
    model,
    fallbackModels: AI_DIRECTOR_MODELS.filter((candidate) => candidate !== model),
    apiKey: $("#ai-director-api-key")?.value.trim() || "",
    timeout: Number($("#ai-director-timeout")?.value || 60),
    visionEnabled: Boolean($("#ai-director-vision")?.checked),
    openImagePromptsEnabled: Boolean($("#ai-director-open-prompts")?.checked),
    reviewEnabled: Boolean($("#ai-director-review-enabled")?.checked),
    reviewThreshold: Number($("#ai-director-review-threshold")?.value || 78),
  };
}

async function saveAiDirectorSettings(silent = false) {
  if (!isAdmin()) {
    showToast("只有管理员可以修改 AI 导演配置");
    return null;
  }
  state.aiImages.director = { ...(state.aiImages.director || {}), saving: true, message: "正在保存导演配置..." };
  renderAiDirectorSettings();
  try {
    const payload = await api("/api/sku-board/ai-director-settings", {
      method: "POST",
      body: JSON.stringify(aiDirectorSettingsFormPayload()),
    });
    const director = mergeAiDirectorState({
      ...(payload.director || {}),
      saving: false,
      status: "ok",
      message: "AI 导演配置已保存",
      formDirty: false,
    });
    // Refresh the shared runtime returned by /ai-image-config as well. This
    // keeps the administrator form, generation workspace and other-role view
    // on the same model chain immediately after a website save.
    await loadAiImageConfig(true);
    renderAiDirectorSettings();
    if (!silent) showToast("AI 导演配置已保存");
    return director;
  } catch (error) {
    state.aiImages.director = { ...(state.aiImages.director || {}), saving: false, status: "error", message: error.message };
    renderAiDirectorSettings();
    if (!silent) showToast(error.message);
    return null;
  }
}

async function testAiDirectorConnection() {
  if (!isAdmin()) return;
  if (state.aiImages.director?.formDirty) {
    const saved = await saveAiDirectorSettings(true);
    if (!saved) return;
  }
  state.aiImages.director = { ...(state.aiImages.director || {}), testing: true, message: "正在连接导演模型..." };
  renderAiDirectorSettings();
  try {
    const payload = await api("/api/sku-board/ai-director-test", {
      method: "POST",
      body: JSON.stringify({}),
    });
    const director = mergeAiDirectorState({
      ...(payload.director || {}),
      testing: false,
      status: "ok",
      message: `${payload.director?.message || "AI 导演连接正常"}${payload.director?.latencyMs ? ` · ${payload.director.latencyMs}ms` : ""}`,
      formDirty: false,
    });
    renderAiDirectorSettings();
    showToast(director.message);
  } catch (error) {
    state.aiImages.director = { ...(state.aiImages.director || {}), testing: false, status: "error", message: error.message };
    renderAiDirectorSettings();
    showToast(error.message);
  }
}

async function recoverRecentAiImageSuite(silent = false, runId = "") {
  if (!state.auth.user) {
    openLoginDialog();
    return null;
  }
  if (!canUseAiImages()) {
    showToast("只有管理员、运营、选品或设计可以恢复远端套图");
    return null;
  }
  if (state.aiImages.recoveryLoading) return null;
  state.aiImages.recoveryLoading = true;
  const button = $("#ai-image-recover-btn");
  const originalText = button?.textContent || "恢复远端套图";
  if (button) {
    button.disabled = true;
    button.textContent = "同步中...";
  }
  try {
    const activeConversation = aiImageActiveConversation();
    const suiteRunId = runId || activeConversation?.suiteRunId || "";
    const knownPages = (activeConversation?.materials || []).map((material) => Number(material.suitePage || 0)).filter(Boolean);
    const payload = await api("/api/sku-board/ai-image-recover", {
      method: "POST",
      body: JSON.stringify({ suiteRunId, knownPages, suiteKey: activeConversation?.suiteKey || "", suiteCount: activeConversation?.suiteCount || activeConversation?.count || 0, suiteCountry: activeConversation?.suiteCountry || "KR" }),
    });
    const recoveredSuiteKey = payload.suiteKey || activeConversation?.suiteKey || "jp-landing-page-25";
    const recoveredCountry = payload.suiteCountry || activeConversation?.suiteCountry || "KR";
    const suiteConfig = aiImageSuiteConfig({ suiteKey: recoveredSuiteKey, suiteCount: payload.suiteCount }) || AI_IMAGE_SUITE_CONFIGS["jp-landing-page-25"];
    const recoveredPreviews = payload.previewDataUrls?.length ? payload.previewDataUrls : [payload.previewDataUrl].filter(Boolean);
    const recoveredMaterials = (payload.materials || []).map((material, index) => ({
      ...material,
      previewDataUrl: recoveredPreviews[index] || "",
    }));
    let conversation = activeConversation;
    let createdRecoveryConversation = false;
    const hasUnrelatedWork = conversation && (!aiImageSuiteActive(conversation) || conversation.suiteKey !== recoveredSuiteKey)
      && (conversation.materials?.length || conversation.userIntent || conversation.prompt);
    if (!conversation || hasUnrelatedWork) {
      conversation = createAiImageConversation({
        title: `恢复的远端${suiteConfig.label}`,
        prompt: "",
        userIntent: `恢复远端已生成的${suiteConfig.label}图片`,
        compiledIntent: "",
        mode: "edit",
        lockLevel: "exact",
        templateKey: suiteConfig.templateKey,
        suiteKey: recoveredSuiteKey,
        suiteCount: suiteConfig.count,
        suiteCountry: recoveredCountry,
        count: suiteConfig.count,
        size: suiteConfig.size,
        quality: "high",
      });
      createdRecoveryConversation = true;
    }
    conversation.suiteKey = recoveredSuiteKey;
    conversation.suiteCount = suiteConfig.count;
    conversation.suiteCountry = recoveredCountry;
    conversation.suiteRunId = payload.suiteRunId || suiteRunId || conversation.suiteRunId || "";
    conversation.suitePlanVersion = payload.suitePlanVersion || conversation.suitePlanVersion || suiteConfig.planVersion;
    conversation.suitePages = conversation.suitePages?.length === suiteConfig.count ? conversation.suitePages : (payload.suitePages || []);
    conversation.remoteSummary = payload.suiteSummary || {};
    conversation.mode = "edit";
    conversation.templateKey = suiteConfig.templateKey;
    conversation.lockLevel = "exact";
    conversation.count = suiteConfig.count;
    conversation.size = payload.suiteSummary?.size || recoveredMaterials[0]?.sizePreset || conversation.size || suiteConfig.size;
    conversation.quality = "high";
    const materialByPage = new Map((conversation.materials || []).map((material) => [Number(material.suitePage || 0), material]));
    recoveredMaterials.forEach((material) => materialByPage.set(Number(material.suitePage || 0), material));
    const mergedMaterials = Array.from(materialByPage.values()).filter((material) => material.suitePage).sort((a, b) => Number(a.suitePage) - Number(b.suitePage));
    conversation.materials = mergedMaterials;
    conversation.previewDataUrls = mergedMaterials.map((material) => material.previewDataUrl || material.previewUrl || "");
    conversation.error = "";
    const summary = conversation.remoteSummary;
    summary.succeeded = mergedMaterials.length;
    summary.partial = mergedMaterials.length < suiteConfig.count;
    summary.message = `已显示 ${mergedMaterials.length}/${suiteConfig.count} ${suiteConfig.unit}；${Number(summary.running || 0)} ${suiteConfig.unit}仍在生成，${Number(summary.failed || 0)} ${suiteConfig.unit}失败`;
    conversation.status = mergedMaterials.length === suiteConfig.count && !summary.running && !summary.failed ? "done" : "partial";
    if (createdRecoveryConversation) conversation.title = `恢复的远端${suiteConfig.label}`;
    conversation.updatedAt = new Date().toISOString();
    syncAiImageStateFromConversation(conversation);
    renderAiImageSidebar();
    renderAiImageForm();
    renderAiImageResults();
    scheduleAiImageSuiteRecovery(conversation);
    if (!silent) showToast(summary.message || `已恢复 ${mergedMaterials.length}/${suiteConfig.count} ${suiteConfig.unit}`);
    return payload;
  } catch (error) {
    if (!silent) showToast(error.message);
    throw error;
  } finally {
    state.aiImages.recoveryLoading = false;
    if (button) {
      button.disabled = false;
      button.textContent = originalText;
    }
  }
}

function scheduleAiImageSuiteRecovery(conversation = {}) {
  if (aiImageRecoveryTimer) {
    window.clearTimeout(aiImageRecoveryTimer);
    aiImageRecoveryTimer = null;
  }
  const summary = conversation.remoteSummary || {};
  if (!state.auth.user || !aiImageSuiteActive(conversation) || !conversation.suiteRunId || !Number(summary.running || 0)) return;
  const scheduledRunId = conversation.suiteRunId;
  aiImageRecoveryTimer = window.setTimeout(() => {
    const activeConversation = aiImageActiveConversation();
    if (activeConversation?.suiteRunId !== scheduledRunId || !state.auth.user) return;
    recoverRecentAiImageSuite(true, scheduledRunId).catch(() => {});
  }, 8000);
}

async function resumePersistedAiImageSuite() {
  const conversation = aiImageActiveConversation();
  if (!state.auth.user || !conversation || !aiImageSuiteActive(conversation) || !conversation.suiteRunId) return;
  if (!["generating", "partial"].includes(conversation.status)) return;
  await recoverRecentAiImageSuite(true, conversation.suiteRunId);
}

function aiImageMissingSuitePages(conversation = {}) {
  const existing = new Set((conversation.materials || []).map((material) => Number(material.suitePage || 0)).filter(Boolean));
  return Array.from({ length: aiImageSuiteCount(conversation) }, (_, index) => index + 1).filter((page) => !existing.has(page));
}

async function generateMissingAiImageSuitePages() {
  const conversation = aiImageActiveConversation();
  if (!conversation || !aiImageSuiteActive(conversation)) {
    showToast("请先打开一个套图任务");
    return;
  }
  const missingPages = aiImageMissingSuitePages(conversation);
  if (!missingPages.length) {
    showToast(`${aiImageSuiteConfig(conversation)?.label || "套图"}已经完整`);
    return;
  }
  if (!(conversation.referenceImages || []).some((item) => item.file)) {
    showToast(`补生成缺失${aiImageSuiteUnit(conversation)}需要重新上传产品主图`);
    $("#ai-image-reference-file").click();
    return;
  }
  conversation.retryPageIndexes = missingPages;
  await generateAiImage(new Event("submit"));
}

async function regenerateAiImageSuitePageWithoutMarks(index = 0) {
  const conversation = aiImageActiveConversation();
  const material = conversation?.materials?.[Number(index)];
  if (!conversation || !material || !aiImageSuiteActive(conversation)) {
    showToast("请先打开一张已生成的套图");
    return;
  }
  const page = Number(material.suitePage || 0);
  if (!Number.isInteger(page) || page < 1 || page > aiImageSuiteCount(conversation)) {
    showToast("未能识别这张套图的页码");
    return;
  }
  if (!(conversation.referenceImages || []).some((item) => item.file)) {
    showToast("去角标重做需要重新上传产品主图");
    $("#ai-image-reference-file").click();
    return;
  }
  if (!conversation.prompt || !(conversation.suitePages || []).length) {
    showToast("当前套图缺少原始提示词或导演分镜，无法安全重做");
    return;
  }
  const button = document.querySelector(`[data-ai-remove-mark-index="${Number(index)}"]`);
  if (button) {
    button.disabled = true;
    button.textContent = "重做中...";
  }
  conversation.suiteRunId = createAiImageSuiteRunId();
  aiImageGenerationAbortController = new AbortController();
  aiImageGenerationStartedAt = performance.now();
  conversation.status = "generating";
  conversation.error = "";
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  renderAiImageSidebar();
  renderAiImageForm();
  renderAiImageResults();
  const status = $("#ai-image-status");
  if (status) status.textContent = `正在按无角标规则重做第 ${page} ${aiImageSuiteUnit(conversation)}`;
  try {
    await generateAiImageSuitePages({
      conversation,
      prompt: conversation.prompt,
      effectiveIntent: conversation.userIntent || "",
      targetPages: [page],
      forcePages: [page],
      button,
      startedAt: performance.now(),
    });
    showToast(`第 ${page} ${aiImageSuiteUnit(conversation)}已按无角标规则重做`);
  } catch (error) {
    conversation.status = isAiImageGenerationAborted(error) ? "cancelled" : "partial";
    conversation.error = isAiImageGenerationAborted(error) ? "" : error.message || "去角标重做失败";
    conversation.updatedAt = new Date().toISOString();
    syncAiImageStateFromConversation(conversation);
    renderAiImageSidebar();
    renderAiImageForm();
    renderAiImageResults();
    if (!isAiImageGenerationAborted(error)) throw error;
  } finally {
    aiImageGenerationAbortController = null;
    aiImageGenerationStartedAt = 0;
    if (button) {
      button.disabled = false;
      button.textContent = "去角标重做";
    }
    renderAiImageForm();
  }
}

async function regenerateAiImageSuitePage(index = 0, options = {}) {
  const conversation = aiImageActiveConversation();
  const material = conversation?.materials?.[Number(index)];
  const userEditPrompt = String(options.instruction || "").trim();
  const isPromptEdit = Boolean(userEditPrompt);
  if (!conversation || !material || !aiImageSuiteActive(conversation)) {
    showToast("请先打开一张已生成的套图");
    return;
  }
  if (aiImageGenerationAbortController || conversation.status === "generating") {
    showToast("当前已有生图任务在运行，请先完成或取消当前任务");
    return;
  }
  const page = Number(material.suitePage || 0);
  if (!Number.isInteger(page) || page < 1 || page > aiImageSuiteCount(conversation)) {
    showToast("未能识别这张套图的页码");
    return;
  }
  if (!isPromptEdit && !(conversation.referenceImages || []).some((item) => item.file)) {
    showToast("重做本页需要重新上传产品主图");
    $("#ai-image-reference-file").click();
    return;
  }
  if (!conversation.prompt || !(conversation.suitePages || []).length) {
    showToast("当前套图缺少原始提示词或导演分镜，无法重做");
    return;
  }
  const suiteConfig = aiImageSuiteConfig(conversation);
  if (!isPromptEdit && suiteConfig && conversation.suitePlanVersion !== suiteConfig.planVersion) {
    showToast("检测到旧版导演分镜，正在按最新商品事实锁重新策划");
    await prepareAiImageSuitePlan(
      conversation,
      conversation.prompt,
      conversation.userIntent || "",
    );
  }
  let editSource = null;
  let editInstruction = "";
  if (isPromptEdit) {
    const currentPageFile = await aiImageSuiteMaterialFile(conversation, material, Number(index));
    editSource = {
      file: currentPageFile,
      name: currentPageFile.name,
    };
    conversation.pageEditPrompts = { ...(conversation.pageEditPrompts || {}), [page]: userEditPrompt };
    editInstruction = `This is a direct current-page image edit. The supplied final generated page is the edit base and this request has highest priority over its old page-plan wording. Preserve all unspecified product, person, scene, composition and text layout. Change only: ${userEditPrompt}`;
  }
  const buttonSelector = isPromptEdit ? `[data-ai-edit-index="${Number(index)}"]` : `[data-ai-retry-index="${Number(index)}"]`;
  const button = document.querySelector(buttonSelector);
  if (button) {
    button.disabled = true;
    button.textContent = isPromptEdit ? "修改中..." : "重做中...";
  }
  conversation.suiteRunId = createAiImageSuiteRunId();
  conversation.status = "generating";
  conversation.error = "";
  conversation.updatedAt = new Date().toISOString();
  aiImageGenerationAbortController = new AbortController();
  aiImageGenerationStartedAt = performance.now();
  syncAiImageStateFromConversation(conversation);
  renderAiImageSidebar();
  renderAiImageForm();
  renderAiImageResults();
  const startedAt = performance.now();
  try {
    await generateAiImageSuitePages({
      conversation,
      prompt: conversation.prompt,
      effectiveIntent: conversation.userIntent || "",
      targetPages: [page],
      forcePages: [page],
      button,
      startedAt,
      pageInstructions: isPromptEdit ? new Map([[page, editInstruction]]) : new Map(),
      pageEditSources: editSource ? new Map([[page, editSource]]) : new Map(),
    });
    showToast(isPromptEdit ? `第 ${page} ${aiImageSuiteUnit(conversation)}已按提示修改` : `第 ${page} ${aiImageSuiteUnit(conversation)}已重新生成`);
  } catch (error) {
    if (!isAiImageGenerationAborted(error)) {
      conversation.status = "partial";
      conversation.error = error.message || "本页重做失败";
    }
    conversation.updatedAt = new Date().toISOString();
    syncAiImageStateFromConversation(conversation);
    renderAiImageSidebar();
    renderAiImageForm();
    renderAiImageResults();
    if (!isAiImageGenerationAborted(error)) throw error;
  } finally {
    aiImageGenerationAbortController = null;
    aiImageGenerationStartedAt = 0;
    if (button) {
      button.disabled = false;
      button.textContent = isPromptEdit ? "按提示修改" : "重做本页";
    }
    renderAiImageForm();
  }
}

function aiImageMaterialEditPromptKey(material = {}, index = 0, suiteActive = false) {
  return suiteActive ? String(Number(material.suitePage || index + 1)) : `image-${Number(index)}`;
}

async function editAiImageMaterialByPrompt(index = 0, instruction = "") {
  const conversation = aiImageActiveConversation();
  const materialIndex = Number(index);
  const material = conversation?.materials?.[materialIndex];
  const userEditPrompt = String(instruction || "").trim();
  if (!conversation || !material) {
    showToast("请先打开一张已生成的图片");
    return;
  }
  if (!userEditPrompt) {
    showToast("请先填写这张图片需要修改的内容");
    return;
  }
  if (aiImageSuiteActive(conversation)) {
    await regenerateAiImageSuitePage(materialIndex, { instruction: userEditPrompt });
    return;
  }
  if (aiImageGenerationAbortController || conversation.status === "generating") {
    showToast("当前已有生图任务在运行，请先完成或取消当前任务");
    return;
  }
  const currentImage = await aiImageSuiteMaterialFile(conversation, material, materialIndex);
  const editKey = aiImageMaterialEditPromptKey(material, materialIndex, false);
  conversation.pageEditPrompts = { ...(conversation.pageEditPrompts || {}), [editKey]: userEditPrompt };
  const editPrompt = [
    "[Direct current-image edit — highest priority] Use the supplied current finished image as the exact edit base.",
    `[Requested change] ${userEditPrompt}`,
    "Preserve every unspecified product feature, person identity, face, body, pose, hands, scene, crop, perspective, lighting, background, composition, typography position and image dimensions.",
    "When changing text, remove the old text completely and render only the requested replacement in the same logical area. When the user asks to regenerate the image or scene, keep all explicitly preserved subjects and product identity while creating a coherent new result.",
    "Return one finished photorealistic ecommerce image only. No explanation, plan, contact sheet, before-after board, duplicate frame, logo or watermark.",
  ].join("\n");
  const button = document.querySelector(`[data-ai-edit-index="${materialIndex}"]`);
  if (button) {
    button.disabled = true;
    button.textContent = "修改中...";
  }
  conversation.status = "generating";
  conversation.error = "";
  conversation.updatedAt = new Date().toISOString();
  aiImageGenerationAbortController = new AbortController();
  aiImageGenerationStartedAt = performance.now();
  syncAiImageStateFromConversation(conversation);
  renderAiImageSidebar();
  renderAiImageForm();
  renderAiImageResults();
  try {
    const formData = new FormData();
    formData.append("prompt", editPrompt);
    formData.append("mode", "edit");
    formData.append("model", conversation.model || material.model || "gpt-image-2");
    formData.append("size", material.sizePreset || conversation.size || "1024x1536");
    formData.append("quality", conversation.quality === "low" ? "medium" : conversation.quality || "high");
    formData.append("count", "1");
    formData.append("skillId", conversation.skillId || "gpt-image2-sosove");
    formData.append("skillVersion", conversation.skillVersion || aiImageSkillConfig().version || "内置");
    formData.append("lockLevel", "exact");
    formData.append("templateKey", "directImageEdit");
    formData.append("reference0", currentImage, currentImage.name || `image-${materialIndex + 1}.png`);
    const payload = await api("/api/sku-board/ad-launch-ai-image-edit", {
      method: "POST",
      body: formData,
      signal: aiImageGenerationAbortController.signal,
    });
    const { materials } = aiImageMaterialsFromPayload(payload);
    const editedMaterial = materials[0];
    if (!editedMaterial?.previewDataUrl) throw new Error("图片修改完成后没有返回预览图");
    conversation.materials[materialIndex] = {
      ...material,
      ...editedMaterial,
      previewDataUrl: editedMaterial.previewDataUrl,
      reviewTag: material.reviewTag || "",
      aiReview: null,
      directEditPrompt: userEditPrompt,
    };
    conversation.previewDataUrls = conversation.materials.map((item) => item.previewDataUrl || "");
    conversation.status = "done";
    conversation.error = "";
    conversation.updatedAt = new Date().toISOString();
    syncAiImageStateFromConversation(conversation);
    renderAiImageSidebar();
    renderAiImageForm();
    renderAiImageResults();
    showToast(`第 ${materialIndex + 1} 张图片已按提示修改`);
  } catch (error) {
    if (!isAiImageGenerationAborted(error)) {
      conversation.status = "done";
      conversation.error = error.message || "图片修改失败";
      showToast(conversation.error);
    } else {
      conversation.status = "done";
      conversation.error = "";
    }
    conversation.updatedAt = new Date().toISOString();
    syncAiImageStateFromConversation(conversation);
    renderAiImageSidebar();
    renderAiImageForm();
    renderAiImageResults();
  } finally {
    aiImageGenerationAbortController = null;
    aiImageGenerationStartedAt = 0;
  }
}

function renderAiImageForm() {
  const form = $("#ai-image-form");
  if (!form) return;
  const options = aiImageOptions();
  const conversation = ensureAiImageConversation();
  const currentProduct = conversation.productSku || state.aiImages.productSku || $("#ai-image-product")?.value || "";
  const currentMode = conversation.mode || state.aiImages.mode || "text";
  const currentLock = conversation.lockLevel || state.aiImages.lockLevel || aiImageSkillConfig().defaults?.lockLevel || "strict";
  const currentModel = conversation.model || state.aiImages.model || options.aiImage?.model || "gpt-image-2";
  const currentSize = conversation.size || state.aiImages.size || "1024x1024";
  const currentQuality = conversation.quality || state.aiImages.quality || "auto";
  const suiteActive = aiImageSuiteActive(conversation);
  const suiteConfig = aiImageSuiteConfig(conversation);
  const codHookActive = conversation.templateKey === "codHook";
  const virtualTryOnActive = conversation.templateKey === "virtualTryOn";
  const activeTemplate = aiImageTemplateOptions().find((item) => item.key === conversation.templateKey) || null;
  const currentCount = virtualTryOnActive ? 1 : Number(suiteConfig?.count || conversation.count || state.aiImages.count || 1);
  const currentCountry = conversation.suiteCountry || state.aiImages.suiteCountry || "KR";
  const currentCodHookType = aiImageCodHookTypeConfig(conversation.codHookType || "hook");
  $("#ai-image-product").innerHTML = productOptions(options.products || [], currentProduct);
  $("#ai-image-product").value = currentProduct;
  const countryControl = $("#ai-image-country-control");
  const countrySelect = $("#ai-image-country");
  if (countryControl && countrySelect) {
    countryControl.hidden = !aiImageCodCountryActive(conversation);
    countrySelect.innerHTML = AI_IMAGE_COD_COUNTRIES
      .map((country) => `<option value="${esc(country.value)}" ${country.value === currentCountry ? "selected" : ""}>${esc(country.label)} · ${esc(country.language)}</option>`)
      .join("");
    countrySelect.value = currentCountry;
  }
  const codHookTypeControl = $("#ai-image-cod-hook-type-control");
  const codHookTypeSelect = $("#ai-image-cod-hook-type");
  if (codHookTypeControl && codHookTypeSelect) {
    codHookTypeControl.hidden = !codHookActive;
    codHookTypeSelect.innerHTML = AI_IMAGE_COD_HOOK_TYPES
      .map((item) => `<option value="${esc(item.key)}" ${item.key === currentCodHookType.key ? "selected" : ""}>${esc(item.label)}</option>`)
      .join("");
    codHookTypeSelect.value = currentCodHookType.key;
  }
  $("#ai-image-model").innerHTML = (options.aiImage?.models || ["gpt-image-2", "codex-gpt-image-2"])
    .map((model) => `<option value="${esc(model)}" ${model === currentModel ? "selected" : ""}>${esc(aiImageModelLabel(model))}</option>`)
    .join("");
  if ($("#ai-image-quality")) $("#ai-image-quality").value = currentQuality;
  if ($("#ai-image-size")) $("#ai-image-size").value = currentSize;
  const intentField = $("#ai-image-intent");
  const nextIntent = conversation.userIntent || "";
  if (intentField.value !== nextIntent) intentField.value = nextIntent;
  const promptField = $("#ai-image-prompt");
  const nextPrompt = conversation.prompt || state.aiImages.prompt || "";
  if (promptField.value !== nextPrompt) {
    promptField.value = nextPrompt;
    promptField.scrollTop = 0;
  }
  $("#ai-image-active-title").textContent = aiImageConversationTitle(conversation);
  $("#ai-image-status").textContent = aiImageStatusText(options, conversation);
  $("#ai-image-settings-panel").hidden = !state.aiImages.settingsOpen;
  $("#ai-image-settings-btn").setAttribute("aria-expanded", state.aiImages.settingsOpen ? "true" : "false");
  renderAiDirectorSettings();
  renderAiImageSkill(conversation);
  renderAiImageLocks(currentLock, conversation);
  renderAiImageModes(conversation);
  renderAiImageDirectorModes(conversation);
  renderAiImageGenerationProfiles(conversation);
  renderAiImageSizePresets(currentSize, suiteConfig);
  renderAiImageCountPresets(currentCount, options.aiImage?.maxCount || 10, suiteConfig, virtualTryOnActive ? "固定 1 张完整场景图" : "");
  renderAiImageTemplates(conversation);
  const refCount = conversation.referenceImages?.length || 0;
  const hasMask = Boolean(conversation.maskImage);
  $("#ai-image-upload-btn").textContent = virtualTryOnActive ? "上传商品/配饰图" : suiteActive || codHookActive ? "上传产品图片" : currentMode === "inpaint" ? "上传原图" : currentMode === "compose" ? "添加合成图" : "上传参考图";
  const modelUploadButton = $("#ai-image-model-upload-btn");
  if (modelUploadButton) modelUploadButton.hidden = !virtualTryOnActive;
  const usageUploadButton = $("#ai-image-usage-upload-btn");
  if (usageUploadButton) usageUploadButton.hidden = conversation.suiteKey !== "jp-landing-page-25";
  const styleSetUploadButton = $("#ai-image-style-set-upload-btn");
  if (styleSetUploadButton) styleSetUploadButton.hidden = virtualTryOnActive || !suiteActive || currentMode === "inpaint";
  $("#ai-image-mask-btn").hidden = currentMode !== "inpaint";
  $("#ai-image-mask-btn").textContent = hasMask ? "更换蒙版" : "上传蒙版";
  $("#ai-image-intent").placeholder = suiteActive
    ? suiteConfig.promptPlaceholder
    : codHookActive
    ? `输入${currentCodHookType.label}提示词，例如：产品放大，韩国本土场景，韩文短标题；价格条请同时填写币种、原价和活动价`
    : virtualTryOnActive
    ? "写明每个文件要替换什么，例如：换白衬衣、黑色帽子、白鞋和指定包，使用场景参考，输出单张完整全身图"
    : currentMode === "inpaint"
    ? "描述蒙版区域要改成什么，例如：把背景换成东京街景，衣服保持不变"
    : "用中文描述画面、模特、场景和要突出的卖点";
  const promptReady = aiImagePromptIsStructured(nextPrompt);
  $("#ai-image-prompt-meta").textContent = `${promptReady ? "已编译" : "待编译"} · ${nextPrompt.length} 字符`;
  const countrySummary = aiImageCodCountryActive(conversation) ? ` · ${aiImageCodCountryConfig(currentCountry).label}` : "";
  const codHookTypeSummary = codHookActive ? ` · ${currentCodHookType.label}` : "";
  const directorModeLabel = suiteActive ? AI_IMAGE_DIRECTOR_MODES.find((mode) => mode.key === aiImageDirectorMode(conversation))?.label || "极速生成" : "";
  const generationProfile = suiteActive ? aiImageGenerationProfile(conversation) : null;
  const generationProfileLabel = generationProfile?.label || "";
  const effectiveQualityLabel = generationProfile?.key === "fast" ? "中质加速" : aiImageQualityLabel(currentQuality);
  $("#ai-image-dock-summary").textContent = `${suiteConfig?.label || activeTemplate?.label || aiImageModeLabel(currentMode)}${countrySummary}${codHookTypeSummary}${directorModeLabel ? ` · ${directorModeLabel}` : ""}${generationProfileLabel ? ` · ${generationProfileLabel}策略` : ""} · ${aiImageLockDisplay(currentLock)} · ${effectiveQualityLabel} · ${aiImageSizeLabel(currentSize)} · ${suiteActive ? `整套${suiteConfig.count}${suiteConfig.unit}` : `${currentCount}张`}${refCount ? ` · 参考图${refCount}` : ""}${hasMask ? " · 蒙版" : ""}`;
  const generateButton = $("#ai-image-generate-btn");
  if (generateButton && conversation.status === "generating") {
    generateButton.disabled = !aiImageGenerationAbortController;
    generateButton.textContent = aiImageGenerationAbortController ? "取消生成" : "生成中...";
  } else if (generateButton) {
    const planCurrent = suiteActive && conversation.suitePlanSignature === aiImageSuitePlanSignature(conversation, nextPrompt, nextIntent);
    generateButton.textContent = suiteActive
      ? aiImageDirectorMode(conversation) === "review"
        ? planCurrent && conversation.status === "planned"
          ? `确认方案并生成${suiteConfig.count}${suiteConfig.unit}`
          : `分析并查看${suiteConfig.count}${suiteConfig.unit}方案`
        : `生成整套${suiteConfig.count}${suiteConfig.unit}`
      : "生成";
  }
  renderAiImageReferences();
  renderAiImagePreflight(conversation);
}

function prefillAiImagePrompt(force = false) {
  const sku = $("#ai-image-product")?.value || "";
  const conversation = ensureAiImageConversation();
  conversation.productSku = sku;
  state.aiImages.productSku = sku;
  const product = aiImageProductBySku(sku);
  if (!product) return;
  const currentPrompt = $("#ai-image-prompt").value.trim();
  if (force || !currentPrompt || aiImagePromptIsStructured(currentPrompt)) {
    rebuildAiImagePromptFromSkill(conversation, { force: true });
    conversation.title = aiImageConversationTitle(conversation);
    conversation.updatedAt = new Date().toISOString();
    syncAiImageStateFromConversation(conversation);
    renderAiImageSidebar();
    renderAiImageForm();
    renderAiImageResults();
  }
}

function aiImageActiveConversation() {
  return state.aiImages.conversations.find((conversation) => conversation.id === state.aiImages.activeId) || null;
}

function ensureAiImageConversation(seed = {}) {
  let conversation = aiImageActiveConversation();
  if (conversation) return conversation;
  conversation = createAiImageConversation(seed);
  return conversation;
}

function createAiImageConversation(seed = {}) {
  const options = aiImageOptions();
  const skill = aiImageSkillConfig();
  const conversation = {
    id: `ai-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
    title: seed.title || "新的生图任务",
    prompt: seed.prompt ?? state.aiImages.prompt ?? "",
    productSku: seed.productSku ?? state.aiImages.productSku ?? "",
    mode: seed.mode ?? state.aiImages.mode ?? "text",
    lockLevel: seed.lockLevel ?? state.aiImages.lockLevel ?? skill.defaults?.lockLevel ?? "strict",
    model: seed.model ?? state.aiImages.model ?? options.aiImage?.model ?? "gpt-image-2",
    size: seed.size ?? state.aiImages.size ?? "1024x1024",
    quality: seed.quality ?? state.aiImages.quality ?? "auto",
    count: Number(seed.count ?? state.aiImages.count ?? 1),
    suiteKey: seed.suiteKey ?? state.aiImages.suiteKey ?? "",
    suiteCount: Number(seed.suiteCount ?? state.aiImages.suiteCount ?? 0),
    suiteCountry: seed.suiteCountry ?? state.aiImages.suiteCountry ?? "KR",
    suiteRunId: seed.suiteRunId ?? state.aiImages.suiteRunId ?? "",
    suitePlanVersion: seed.suitePlanVersion ?? state.aiImages.suitePlanVersion ?? "",
    suitePages: seed.suitePages || [],
    suitePlanSignature: seed.suitePlanSignature || "",
    directorMode: seed.directorMode || state.aiImages.directorMode || "fast",
    generationProfile: seed.generationProfile || state.aiImages.generationProfile || "standard",
    director: seed.director || {},
    review: seed.review || {},
    pageEditPrompts: seed.pageEditPrompts || {},
    remoteSummary: seed.remoteSummary || {},
    templateKey: seed.templateKey || skill.defaults?.templateKey || "main",
    codHookType: seed.codHookType || "hook",
    userIntent: seed.userIntent || "",
    compiledIntent: seed.compiledIntent || "",
    promptManuallyEdited: Boolean(seed.promptManuallyEdited),
    skillId: skill.id || "gpt-image2-sosove",
    skillVersion: skill.version || "内置",
    materials: [],
    previewDataUrls: [],
    referenceImages: seed.referenceImages || [],
    maskImage: seed.maskImage || null,
    suiteStyleAnchorFile: null,
    status: "draft",
    error: "",
    seconds: 0,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
  state.aiImages.conversations.unshift(conversation);
  state.aiImages.activeId = conversation.id;
  syncAiImageStateFromConversation(conversation);
  return conversation;
}

function syncAiImageStateFromConversation(conversation) {
  if (!conversation) return;
  state.aiImages.activeId = conversation.id;
  state.aiImages.prompt = conversation.prompt || "";
  state.aiImages.productSku = conversation.productSku || "";
  state.aiImages.mode = conversation.mode || "text";
  state.aiImages.lockLevel = conversation.lockLevel || "strict";
  state.aiImages.model = conversation.model || "gpt-image-2";
  state.aiImages.size = conversation.size || "1024x1024";
  state.aiImages.quality = conversation.quality || "auto";
  state.aiImages.count = Number(conversation.count || 1);
  state.aiImages.suiteKey = conversation.suiteKey || "";
  state.aiImages.suiteCount = Number(conversation.suiteCount || 0);
  state.aiImages.suiteCountry = conversation.suiteCountry || "KR";
  state.aiImages.suiteRunId = conversation.suiteRunId || "";
  state.aiImages.suitePlanVersion = conversation.suitePlanVersion || "";
  state.aiImages.suitePages = conversation.suitePages || [];
  state.aiImages.directorMode = aiImageDirectorMode(conversation);
  state.aiImages.generationProfile = aiImageGenerationProfile(conversation).key;
  state.aiImages.remoteSummary = conversation.remoteSummary || {};
  state.aiImages.materials = conversation.materials || [];
  state.aiImages.previewDataUrls = conversation.previewDataUrls || [];
  state.aiImages.referenceImages = conversation.referenceImages || [];
  state.aiImages.maskImage = conversation.maskImage || null;
  state.aiImages.material = state.aiImages.materials[0] || null;
  state.aiImages.previewDataUrl = state.aiImages.previewDataUrls[0] || "";
  persistAiImageState();
}

function aiImageConversationTitle(conversation = {}) {
  const product = aiImageOptions().products.find((item) => item.sku === conversation.productSku);
  if (conversation.templateKey === "virtualTryOn" && !conversation.userIntent && !product?.title) return "模特换装/搭配";
  const source = (conversation.userIntent || product?.title || conversation.prompt || conversation.title || "新的生图任务").trim();
  return source.length > 24 ? `${source.slice(0, 24)}...` : source;
}

function aiImageStatusText(options, conversation = {}) {
  const mode = aiImageModeLabel(conversation.mode || "text");
  const suiteConfig = aiImageSuiteConfig(conversation);
  const countryLabel = aiImageCodCountryActive(conversation) ? aiImageCodCountryConfig(conversation.suiteCountry || "KR").label : "";
  const taskLabel = suiteConfig ? `${suiteConfig.label}${countryLabel ? ` · ${countryLabel}` : ""}` : conversation.templateKey === "virtualTryOn" ? "模特换装/搭配" : mode;
  const unit = suiteConfig?.unit || "张";
  if (conversation.status === "planning") return `${taskLabel}正在分析商品与编排分镜`;
  if (conversation.status === "planned") return `${taskLabel}方案已就绪，等待确认`;
  if (conversation.status === "generating") return conversation.remoteSummary?.message || `${taskLabel}生成中 ${conversation.count || 1} ${unit}`;
  if (conversation.status === "done") return `${taskLabel}已生成 ${conversation.materials?.length || 0} ${unit}`;
  if (conversation.status === "partial") return `${taskLabel}已显示 ${conversation.materials?.length || 0}/${suiteConfig?.count || conversation.count || 1} ${unit}`;
  if (conversation.status === "error") return "生成失败";
  return options.aiImage?.enabled
    ? `已连接 ${aiImageProviderLabel(conversation.model || options.aiImage?.model || "gpt-image-2")}`
    : "未配置生图服务";
}

function aiImageQualityLabel(value) {
  return { auto: "自动", low: "低质", medium: "中质", high: "高质" }[value] || value || "自动";
}

function aiImageFileSize(value) {
  const size = Number(value || 0);
  if (!size) return "-";
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(0)} KB`;
  return `${(size / 1024 / 1024).toFixed(2)} MB`;
}

function renderAiImageSidebar() {
  const list = $("#ai-image-task-list");
  if (!list) return;
  if (!state.aiImages.conversations.length) {
    list.innerHTML = `<div class="ai-image-task-empty">还没有生图任务</div>`;
    return;
  }
  list.innerHTML = state.aiImages.conversations
    .map((conversation) => {
      const active = conversation.id === state.aiImages.activeId;
      const count = conversation.materials?.length || 0;
      const suiteConfig = aiImageSuiteConfig(conversation);
      const badge = conversation.status === "generating" ? "生成中" : conversation.status === "error" ? "失败" : count ? `${count}${suiteConfig?.unit || "张"}` : "草稿";
      const countryLabel = aiImageCodCountryActive(conversation) ? aiImageCodCountryConfig(conversation.suiteCountry || "KR").label : "";
      const modeLabel = suiteConfig ? `${suiteConfig.label}${countryLabel ? ` · ${countryLabel}` : ""}` : aiImageModeLabel(conversation.mode || "text");
      return `
        <div class="ai-image-task-card ${active ? "active" : ""}">
          <button type="button" data-ai-conversation="${esc(conversation.id)}">
            <strong>${esc(aiImageConversationTitle(conversation))}</strong>
            <span>${esc(modeLabel)} · ${esc(badge)} · ${esc(shortDate(conversation.updatedAt || conversation.createdAt))}</span>
          </button>
          <button class="icon-btn" type="button" data-ai-conversation-delete="${esc(conversation.id)}" aria-label="删除任务">×</button>
        </div>
      `;
    })
    .join("");
}

function renderAiImageSizePresets(currentSize, suiteConfig = null) {
  const container = $("#ai-image-size-presets");
  if (!container) return;
  const allowed = new Set(aiImageOptions().aiImage?.sizes || AI_IMAGE_SIZE_PRESETS.map((item) => item.value));
  const sizeLocked = Boolean(suiteConfig?.sizeLocked);
  container.innerHTML = AI_IMAGE_SIZE_PRESETS.filter((item) => (allowed.has(item.value) || item.value === currentSize) && (!suiteConfig || (sizeLocked ? item.value === suiteConfig.size : item.value !== "auto")))
    .map((item) => `
      <button class="ai-image-option ${item.value === currentSize ? "active" : ""}" data-ai-size="${esc(item.value)}" type="button">
        <strong>${esc(item.label)}</strong>
        <span>${esc(item.hint)}</span>
      </button>
    `)
    .join("");
}

function renderAiImageCountPresets(currentCount, maxCount = 10, suiteConfig = null, fixedCountLabel = "") {
  const container = $("#ai-image-count-presets");
  if (!container) return;
  container.classList.toggle("cod-count-options", Boolean(suiteConfig?.countConfigurable));
  container.classList.toggle("landing-count-options", false);
  if (fixedCountLabel) {
    container.innerHTML = `<button class="ai-image-count active" type="button" disabled>${esc(fixedCountLabel)}</button>`;
    return;
  }
  if (suiteConfig) {
    if (suiteConfig.countConfigurable) {
      container.innerHTML = suiteConfig.countOptions
        .map((count) => `<button class="ai-image-count ${count === currentCount ? "active" : ""}" data-ai-count="${count}" type="button">${count}张</button>`)
        .join("");
      return;
    }
    container.innerHTML = `<button class="ai-image-count active" type="button" disabled>整套${suiteConfig.count}${suiteConfig.unit}</button>`;
    return;
  }
  const safeMax = Math.max(1, Math.min(Number(maxCount || 10), 10));
  container.innerHTML = AI_IMAGE_COUNT_PRESETS.filter((count) => count <= safeMax)
    .map((count) => `<button class="ai-image-count ${count === currentCount ? "active" : ""}" data-ai-count="${count}" type="button">${count}张</button>`)
    .join("");
}

function renderAiImageSkill(conversation) {
  const skill = aiImageSkillConfig();
  $("#ai-image-skill-name").textContent = `${skill.name || "GPT-Image2 SOSOVE"} · v${skill.version || "内置"}`;
  $("#ai-image-skill-meta").textContent = skill.loaded
    ? `动态配置 · ${skill.updatedAt || "已加载"}`
    : `内置回退${skill.error ? ` · ${skill.error}` : ""}`;
}

function renderAiImageLocks(currentLock, conversation = {}) {
  const strip = $("#ai-image-lock-strip");
  if (!strip) return;
  const genericProductHints = {
    standard: "锁定类别与主外观",
    strict: "锁定部件与材质",
    exact: "完全锁定产品身份",
  };
  const genericProductSuite = aiImageSuiteActive(conversation);
  strip.innerHTML = aiImageLockOptions().map((level) => `
    <button class="ai-image-lock-btn ${currentLock === level.key ? "active" : ""}" data-ai-lock="${esc(level.key)}" type="button" aria-pressed="${currentLock === level.key ? "true" : "false"}">
      <strong>${esc(level.label)}</strong>
      <span>${esc(genericProductSuite ? genericProductHints[level.key] || level.hint || "" : level.hint || "")}</span>
    </button>
  `).join("");
}

function setAiImageLockLevel(lockLevel) {
  if (!aiImageLockOptions().some((item) => item.key === lockLevel)) return;
  const conversation = ensureAiImageConversation();
  conversation.lockLevel = lockLevel;
  rebuildAiImagePromptFromSkill(conversation);
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  renderAiImageSidebar();
  renderAiImageForm();
  renderAiImageResults();
}

function aiImagePreflight(conversation) {
  const mode = conversation.mode || "text";
  const suiteActive = aiImageSuiteActive(conversation);
  const suiteConfig = aiImageSuiteConfig(conversation);
  const references = conversation.referenceImages || [];
  const skill = aiImageSkillConfig();
  const prompt = conversation.prompt || "";
  const intent = (conversation.userIntent || "").trim();
  const items = [
    { tone: skill.loaded ? "ok" : "warning", label: skill.loaded ? `Skill v${skill.version}` : "Skill 回退配置" },
    { tone: conversation.productSku ? "ok" : "warning", label: conversation.productSku ? "已关联商品" : "未关联商品" },
    { tone: "ok", label: aiImageLockDisplay(conversation.lockLevel || "strict") },
  ];
  if (suiteActive) items.push({ tone: "ok", label: `${suiteConfig.count}${suiteConfig.unit}顺序已锁定 · ${suiteConfig.size}` });
  if (aiImageCodCountryActive(conversation)) {
    const country = aiImageCodCountryConfig(conversation.suiteCountry || "KR");
    items.push({ tone: "ok", label: `目标国家 ${country.label} · ${country.language}` });
  }
  let blocked = false;
  if (conversation.templateKey === "virtualTryOn") {
    const productReady = references.some((reference, index) => reference.file && aiImageReferenceRoleKey(reference, index) === "product");
    const personReady = references.some((reference, index) => reference.file && aiImageReferenceRoleKey(reference, index) === "person");
    items.push({ tone: productReady ? "ok" : "error", label: productReady ? "衣服产品图已添加" : "缺少衣服产品图" });
    items.push({ tone: personReady ? "ok" : "error", label: personReady ? "模特图片已添加" : "缺少模特图片" });
    blocked = blocked || !productReady || !personReady;
  } else if (mode === "edit") {
    const ready = references.length >= 1;
    items.push({ tone: ready ? "ok" : "error", label: ready ? `${suiteActive ? "产品主图" : "参考图"} ${references.length} 张` : suiteActive ? "缺少产品主图" : "缺少参考图" });
    blocked = blocked || !ready;
  } else if (mode === "compose") {
    const ready = references.length >= 2;
    items.push({ tone: ready ? "ok" : "error", label: ready ? `合成图 ${references.length} 张` : "需要至少 2 张图" });
    blocked = blocked || !ready;
  } else if (mode === "inpaint") {
    const sourceReady = references.length === 1;
    const maskReady = Boolean(conversation.maskImage);
    items.push({ tone: sourceReady ? "ok" : "error", label: sourceReady ? "原图已添加" : "需要 1 张原图" });
    items.push({ tone: maskReady ? "ok" : "error", label: maskReady ? "蒙版已添加" : "缺少 PNG 蒙版" });
    blocked = blocked || !sourceReady || !maskReady;
  } else {
    items.push({ tone: "ok", label: "无需参考图" });
  }
  const promptCurrent = aiImagePromptIsStructured(prompt) && conversation.compiledIntent === intent;
  if (!intent && !prompt) {
    items.push({ tone: "error", label: "填写创作需求" });
    blocked = true;
  } else {
    items.push({ tone: promptCurrent ? "ok" : "warning", label: promptCurrent ? "专业提示词已更新" : "生成时自动更新提示词" });
  }
  return { items, blocked };
}

function renderAiImagePreflight(conversation) {
  const container = $("#ai-image-preflight");
  if (!container) return;
  const status = aiImagePreflight(conversation);
  container.innerHTML = status.items.map((item) => `<span class="ai-image-preflight-item ${esc(item.tone)}">${esc(item.label)}</span>`).join("");
  const button = $("#ai-image-generate-btn");
  if (button && conversation.status !== "generating") button.disabled = status.blocked;
}

function renderAiImageModes(conversation) {
  const strip = $("#ai-image-mode-strip");
  if (!strip) return;
  const currentMode = conversation.mode || "text";
  strip.innerHTML = aiImageModeOptions().map((mode) => `
    <button class="ai-image-mode-btn ${currentMode === mode.key ? "active" : ""}" data-ai-mode="${esc(mode.key)}" type="button">
      <strong>${esc(mode.label)}</strong>
      <span>${esc(mode.hint)}</span>
    </button>
  `).join("");
}

function aiImageDirectorMode(conversation = {}) {
  return AI_IMAGE_DIRECTOR_MODES.some((mode) => mode.key === conversation.directorMode) ? conversation.directorMode : "fast";
}

function renderAiImageDirectorModes(conversation) {
  const strip = $("#ai-image-director-mode-strip");
  if (!strip) return;
  const suiteActive = aiImageSuiteActive(conversation);
  strip.hidden = !suiteActive;
  if (!suiteActive) {
    strip.innerHTML = "";
    return;
  }
  const current = aiImageDirectorMode(conversation);
  strip.innerHTML = `
    <span>导演流程</span>
    <div>
      ${AI_IMAGE_DIRECTOR_MODES.map((mode) => `
        <button class="${current === mode.key ? "active" : ""}" type="button" data-ai-director-mode="${esc(mode.key)}">
          <strong>${esc(mode.label)}</strong>
          <small>${esc(mode.hint)}</small>
        </button>
      `).join("")}
    </div>
  `;
}

function setAiImageDirectorMode(modeKey = "fast") {
  if (!AI_IMAGE_DIRECTOR_MODES.some((mode) => mode.key === modeKey)) return;
  const conversation = ensureAiImageConversation();
  conversation.directorMode = modeKey;
  if (!(conversation.materials || []).length && Array.isArray(conversation.suitePages) && conversation.suitePages.length === aiImageSuiteCount(conversation)) {
    conversation.status = modeKey === "review" ? "planned" : "draft";
  }
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  renderAiImageForm();
  renderAiImageResults();
}

function aiImageGenerationProfile(conversation = {}) {
  const key = conversation.generationProfile || state.aiImages.generationProfile || "standard";
  return AI_IMAGE_GENERATION_PROFILES.find((profile) => profile.key === key)
    || AI_IMAGE_GENERATION_PROFILES.find((profile) => profile.key === "standard");
}

function renderAiImageGenerationProfiles(conversation) {
  const strip = $("#ai-image-generation-profile-strip");
  if (!strip) return;
  const suiteActive = aiImageSuiteActive(conversation);
  strip.hidden = !suiteActive;
  if (!suiteActive) {
    strip.innerHTML = "";
    return;
  }
  const current = aiImageGenerationProfile(conversation).key;
  strip.innerHTML = `
    <span>生成策略</span>
    <div>
      ${AI_IMAGE_GENERATION_PROFILES.map((profile) => `
        <button class="${current === profile.key ? "active" : ""}" type="button" data-ai-generation-profile="${esc(profile.key)}">
          <strong>${esc(profile.label)}</strong>
          <small>${esc(profile.hint)}</small>
        </button>
      `).join("")}
    </div>
  `;
}

function setAiImageGenerationProfile(profileKey = "standard") {
  const profile = AI_IMAGE_GENERATION_PROFILES.find((item) => item.key === profileKey);
  if (!profile) return;
  const conversation = ensureAiImageConversation();
  conversation.generationProfile = profile.key;
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  renderAiImageForm();
  renderAiImageResults();
  showToast(`已切换为${profile.label}生成策略`);
}

function aiImageGenerationNodes(conversation = ensureAiImageConversation()) {
  const healthNodes = Array.isArray(state.aiImages.health?.nodes) ? state.aiImages.health.nodes : [];
  const configuredNodes = adLaunchOptions().aiImage?.nodes || [];
  const provider = aiImageModelProvider(conversation.model || state.aiImages.model || "gpt-image-2");
  const matchesProvider = (node) => String(node?.provider || "chatgpt2api") === provider;
  if (healthNodes.length) {
    const healthyNodes = healthNodes.filter((node) => node && node.id && matchesProvider(node) && ["ok", "warning"].includes(String(node.status || "").toLowerCase()));
    if (healthyNodes.length) return healthyNodes;
  }
  return configuredNodes.filter((node) => node && node.id && matchesProvider(node));
}

function aiImageGenerationWorkerCount(conversation = {}, pageCount = 1) {
  const profile = aiImageGenerationProfile(conversation);
  const nodes = aiImageGenerationNodes(conversation);
  const nodeCount = Math.max(1, nodes.length || Number(state.aiImages.health?.healthyNodeCount || 0) || 1);
  const perNode = Math.max(1, Number(profile.perNode || 1));
  const readyAccounts = Number(state.aiImages.health?.accountPoolReady || 0);
  const accountCapacity = readyAccounts > 0 ? readyAccounts : nodeCount * perNode;
  return Math.max(1, Math.min(
    Number(profile.workers || 1),
    AI_IMAGE_SUITE_WORKER_COUNT,
    nodeCount * perNode,
    accountCapacity,
    Math.max(1, Number(pageCount || 1)),
  ));
}

function aiImageGenerationNodeForPage(page = 1) {
  const nodes = aiImageGenerationNodes();
  if (!nodes.length) return { id: "", name: "自动调度" };
  return nodes[(Math.max(1, Number(page || 1)) - 1) % nodes.length];
}

function formatAiImageDuration(milliseconds = 0) {
  const seconds = Math.max(0, Math.round(Number(milliseconds || 0) / 1000));
  if (!seconds) return "--";
  if (seconds < 60) return `${seconds}秒`;
  const minutes = Math.floor(seconds / 60);
  const remain = seconds % 60;
  return remain ? `${minutes}分${remain}秒` : `${minutes}分钟`;
}

function aiImageSuitePlanSignature(conversation, prompt = "", intent = "") {
  const references = (conversation.referenceImages || []).map((reference, index) => ({
    index,
    name: reference.name || "",
    size: Number(reference.size || reference.file?.size || 0),
    lastModified: Number(reference.file?.lastModified || 0),
    role: aiImageReferenceRoleKey(reference, index),
    keywords: String(reference.keywords || "").trim().slice(0, 240),
  }));
  return JSON.stringify({
    productSku: conversation.productSku || "",
    suiteKey: conversation.suiteKey || "",
    suiteCount: aiImageSuiteCount(conversation),
    country: conversation.suiteCountry || "KR",
    size: conversation.size || "",
    directorModel: state.aiImages.director?.model || "",
    prompt: String(prompt || "").trim(),
    intent: String(intent || "").trim(),
    references,
  });
}

function rebuildAiImagePromptFromSkill(conversation, { force = false } = {}) {
  const rawPrompt = (conversation.prompt || $("#ai-image-prompt")?.value || "").trim();
  const intentFieldValue = $("#ai-image-intent")?.value.trim() || "";
  if (!force && !rawPrompt && !intentFieldValue && !conversation.userIntent) return false;
  if (!force && rawPrompt && !aiImagePromptIsStructured(rawPrompt)) return false;
  const userIntent = intentFieldValue || conversation.userIntent || (aiImagePromptIsStructured(rawPrompt) ? "" : rawPrompt);
  const product = aiImageProductBySku(conversation.productSku || $("#ai-image-product")?.value || "");
  const skill = aiImageSkillConfig();
  conversation.userIntent = userIntent;
  conversation.prompt = aiImageTemplatePrompt(conversation.templateKey || "main", product, Boolean(conversation.referenceImages?.length), {
    mode: conversation.mode || "text",
    size: conversation.size || "1024x1536",
    userIntent,
    lockLevel: conversation.lockLevel || skill.defaults?.lockLevel || "strict",
    country: conversation.suiteCountry || "KR",
    codHookType: conversation.codHookType || "hook",
    referenceRoles: conversation.referenceImages || [],
  });
  conversation.compiledIntent = userIntent;
  conversation.promptManuallyEdited = false;
  conversation.skillId = skill.id || "gpt-image2-sosove";
  conversation.skillVersion = skill.version || "内置";
  return true;
}

function setAiImageMode(modeKey) {
  if (!aiImageModeOptions().some((item) => item.key === modeKey)) return;
  const conversation = ensureAiImageConversation();
  if (conversation.templateKey === "virtualTryOn" && modeKey !== "compose") {
    showToast("模特换装/搭配会自动使用多图合成模式");
    return;
  }
  conversation.mode = modeKey;
  if (aiImageSuiteActive(conversation) && modeKey !== "edit") {
    conversation.suiteKey = "";
    conversation.suitePlanVersion = "";
    conversation.suitePages = [];
    conversation.suitePlanSignature = "";
    conversation.suiteStyleAnchorFile = null;
  }
  rebuildAiImagePromptFromSkill(conversation);
  conversation.title = aiImageConversationTitle(conversation);
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  renderAiImageSidebar();
  renderAiImageForm();
  renderAiImageResults();
}

function renderAiImageTemplates(conversation) {
  const strip = $("#ai-image-template-strip");
  if (!strip) return;
  strip.innerHTML = `
    <span>模板</span>
    ${aiImageTemplateOptions().map((template) => `
      <button class="ai-image-template-btn ${conversation.templateKey === template.key ? "active" : ""}" data-ai-template="${esc(template.key)}" type="button">
        ${esc(template.label)}
      </button>
    `).join("")}
  `;
}

function applyAiImageTemplate(templateKey) {
  const template = aiImageTemplateOptions().find((item) => item.key === templateKey) || aiImageTemplateOptions()[0] || AI_IMAGE_PROMPT_TEMPLATES[0];
  const conversation = ensureAiImageConversation();
  const skill = aiImageSkillConfig();
  const product = aiImageProductBySku(conversation.productSku || $("#ai-image-product")?.value || "");
  const rawPrompt = (conversation.prompt || $("#ai-image-prompt")?.value || "").trim();
  const userIntent = $("#ai-image-intent")?.value.trim() || conversation.userIntent || (aiImagePromptIsStructured(rawPrompt) ? "" : rawPrompt);
  if (template.mode) conversation.mode = template.mode;
  conversation.suiteKey = template.suiteKey || "";
  conversation.suiteCount = template.suiteKey ? template.count : 0;
  if (aiImageCodCountryActive(conversation)) conversation.suiteCountry = conversation.suiteCountry || "KR";
  conversation.suitePlanVersion = "";
  conversation.suitePages = [];
  conversation.suitePlanSignature = "";
  conversation.suiteStyleAnchorFile = null;
  conversation.review = {};
  if (conversation.suiteKey) conversation.lockLevel = "exact";
  if (template.key === "codHook") conversation.lockLevel = conversation.referenceImages?.length ? "exact" : "strict";
  if (template.key === "virtualTryOn") {
    conversation.mode = "compose";
    conversation.lockLevel = "exact";
    conversation.count = 1;
  }
  const prompt = aiImageTemplatePrompt(template.key, product, Boolean(conversation.referenceImages?.length), {
    mode: conversation.mode || "text",
    size: template.size || conversation.size || "1024x1536",
    userIntent,
    lockLevel: conversation.lockLevel || "strict",
    country: conversation.suiteCountry || "KR",
    codHookType: conversation.codHookType || "hook",
    referenceRoles: conversation.referenceImages || [],
  });
  conversation.prompt = prompt;
  conversation.userIntent = userIntent;
  conversation.compiledIntent = userIntent;
  conversation.promptManuallyEdited = false;
  conversation.skillId = skill.id || "gpt-image2-sosove";
  conversation.skillVersion = skill.version || "内置";
  conversation.templateKey = template.key;
  conversation.size = template.size || conversation.size || "1024x1024";
  conversation.count = template.count || conversation.count || 1;
  if (template.key === "poster" || conversation.suiteKey) conversation.quality = "high";
  conversation.title = aiImageConversationTitle(conversation);
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  renderAiImageSidebar();
  renderAiImageForm();
  renderAiImageResults();
  const intentField = $("#ai-image-intent");
  intentField.focus();
  intentField.setSelectionRange(intentField.value.length, intentField.value.length);
}

function startAiImageQuickWorkflow(templateKey) {
  const skill = aiImageSkillConfig();
  const quickTitles = {
    landing: "新的落地页任务",
    codDetail: "新的 COD 国家详情图任务",
    refresh: "新的复刻 / 本地化任务",
    main: "新的创意生图任务",
  };
  createAiImageConversation({
    title: quickTitles[templateKey] || "新的生图任务",
    prompt: "",
    userIntent: "",
    compiledIntent: "",
    productSku: "",
    mode: "text",
    lockLevel: skill.defaults?.lockLevel || "strict",
    templateKey: skill.defaults?.templateKey || "main",
    suiteKey: "",
    suiteCount: 0,
    suiteCountry: "JP",
    suitePages: [],
    materials: [],
    previewDataUrls: [],
    referenceImages: [],
    maskImage: null,
  });
  renderAiImageForm();
  applyAiImageTemplate(templateKey);
  const conversation = aiImageActiveConversation();
  if (conversation) {
    conversation.title = quickTitles[templateKey] || conversation.title;
    if (["landing", "codDetail"].includes(templateKey)) conversation.suiteCountry = "JP";
    syncAiImageStateFromConversation(conversation);
    renderAiImageSidebar();
    renderAiImageResults();
  }
  document.querySelector("#ai-image-workspace")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function setAiImageSuiteCountry(countryCode = "KR") {
  const country = aiImageCodCountryConfig(countryCode);
  const conversation = ensureAiImageConversation();
  conversation.suiteCountry = country.value;
  conversation.suitePages = [];
  conversation.suitePlanVersion = "";
  conversation.suitePlanSignature = "";
  conversation.suiteStyleAnchorFile = null;
  conversation.review = {};
  conversation.remoteSummary = {};
  conversation.materials = [];
  conversation.previewDataUrls = [];
  conversation.status = "draft";
  conversation.error = "";
  rebuildAiImagePromptFromSkill(conversation, { force: true });
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  renderAiImageSidebar();
  renderAiImageForm();
  renderAiImageResults();
}

function setAiImageCodHookType(type = "hook") {
  const conversation = ensureAiImageConversation();
  const config = aiImageCodHookTypeConfig(type);
  conversation.codHookType = config.key;
  conversation.compiledIntent = "";
  conversation.materials = [];
  conversation.previewDataUrls = [];
  conversation.remoteSummary = {};
  conversation.status = "draft";
  conversation.error = "";
  rebuildAiImagePromptFromSkill(conversation, { force: true });
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  renderAiImageSidebar();
  renderAiImageForm();
  renderAiImageResults();
}

function setAiImageSuiteCount(count = 22) {
  const conversation = ensureAiImageConversation();
  const suiteConfig = aiImageSuiteConfig(conversation);
  if (!suiteConfig?.countConfigurable) return;
  const nextCount = Number(count);
  if (!(suiteConfig.countOptions || []).includes(nextCount)) return;
  conversation.suiteCount = nextCount;
  conversation.count = nextCount;
  conversation.suitePages = [];
  conversation.suitePlanVersion = "";
  conversation.suitePlanSignature = "";
  conversation.suiteStyleAnchorFile = null;
  conversation.retryPageIndexes = [];
  conversation.review = {};
  conversation.remoteSummary = {};
  conversation.materials = [];
  conversation.previewDataUrls = [];
  conversation.status = "draft";
  conversation.error = "";
  rebuildAiImagePromptFromSkill(conversation, { force: true });
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  renderAiImageSidebar();
  renderAiImageForm();
  renderAiImageResults();
}

function aiImageDefaultReferenceRole(index = 0) {
  return ["product", "detail", "scene", "person"][index] || "layout";
}

function aiImagePrimaryUploadReferenceRole() {
  const conversation = ensureAiImageConversation();
  return conversation.suiteKey === "jp-landing-page-25" ? "product" : "";
}

function aiImageReferenceRoleKey(reference = {}, index = 0) {
  if (index === 0) return "product";
  const key = String(reference?.role || "").trim();
  return AI_IMAGE_REFERENCE_ROLES.some((role) => role.key === key) ? key : aiImageDefaultReferenceRole(index);
}

function aiImageReferenceRoleLabel(key = "product") {
  return AI_IMAGE_REFERENCE_ROLES.find((role) => role.key === key)?.label || "参考图";
}

function aiImageReferenceRoleInstruction(key = "product") {
  return AI_IMAGE_REFERENCE_ROLES.find((role) => role.key === key)?.instruction || "Use this image only according to its selected reference role.";
}

function aiImageReferenceKeywordPlaceholder(key = "") {
  if (key === "scene") return "场景关键词：东京街道、日式公寓、自然光";
  if (key === "person") return "人物关键词：日本女性、40代、自然站姿";
  if (key === "bag") return "包袋要求：替换原包、保持银色五金";
  if (key === "hat") return "帽子要求：戴在人物头上、改成黑色";
  if (key === "shoes") return "鞋履要求：替换原鞋、完整露出";
  if (key === "jewelry") return "首饰要求：作为耳环佩戴、保持原尺寸";
  if (["accessory", "package"].includes(key)) return "配饰要求：写明替换对象、佩戴位置或颜色";
  if (key === "layout") return "排版关键词：左文右图、大标题、留白克制";
  if (key === "styleSet") return "风格关键词：浅绿功效页、大标题、微距效果、对比模块";
  return "补充关键词（可选）";
}

function aiImageReferenceKeywordHint(key = "") {
  if (key === "scene") return "描述地点、光线、氛围与道具";
  if (key === "person") return "描述年龄感、发型、体型与动作";
  if (["bag", "hat", "shoes", "jewelry", "accessory", "package"].includes(key)) return "描述替换谁、佩戴位置、需要保留或修改的属性";
  if (key === "layout") return "描述单张构图、留白、标题区与图文位置";
  if (key === "styleSet") return "描述整套配色、信息层级、模块形状与呈现效果";
  return "补充该参考图需要提取的特征";
}

function aiImageReferenceRoleMap(references = [], hasReferences = false) {
  const items = Array.isArray(references) ? references : [];
  if (!items.length && !hasReferences) return "";
  const resolved = items.length ? items : [{ role: "product" }];
  const roleKeys = [];
  const imageMap = resolved.map((reference, index) => {
    const roleKey = aiImageReferenceRoleKey(reference, index);
    if (!roleKeys.includes(roleKey)) roleKeys.push(roleKey);
    const fileName = String(reference.name || reference.file?.name || "")
      .replace(/[\r\n\[\];]/g, " ")
      .replace(/"/g, "'")
      .trim()
      .slice(0, 120);
    const keywords = String(reference.keywords || "").trim().slice(0, 240);
    const fileText = fileName ? ` [file="${fileName}"]` : "";
    const keywordText = keywords ? ` (${keywords})` : "";
    return `Image ${index + 1}=${aiImageReferenceRoleLabel(roleKey)}${fileText}${keywordText}`;
  }).join("; ");
  const roleRules = roleKeys.map((roleKey) => `${aiImageReferenceRoleLabel(roleKey)}: ${aiImageReferenceRoleInstruction(roleKey)}`).join(" ");
  return `${imageMap}. Role rules: ${roleRules}`;
}

function normalizeAiImageReferenceRoles(references = []) {
  return references.map((reference, index) => ({
    ...reference,
    role: aiImageReferenceRoleKey(reference, index),
    keywords: String(reference.keywords || "").trim().slice(0, 240),
  }));
}

function setAiImageReferenceRole(id, roleKey) {
  const conversation = ensureAiImageConversation();
  const referenceIndex = (conversation.referenceImages || []).findIndex((reference) => reference.id === id);
  if (referenceIndex < 1 || !AI_IMAGE_REFERENCE_ROLES.some((role) => role.key === roleKey)) return;
  conversation.referenceImages[referenceIndex].role = roleKey;
  conversation.referenceImages = normalizeAiImageReferenceRoles(conversation.referenceImages);
  rebuildAiImagePromptFromSkill(conversation, { force: true });
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  renderAiImageForm();
  renderAiImageResults();
}

function setAiImageReferenceKeyword(id, keywords) {
  const conversation = ensureAiImageConversation();
  const reference = (conversation.referenceImages || []).find((item) => item.id === id);
  if (!reference) return;
  reference.keywords = String(keywords || "").trim().slice(0, 240);
  conversation.referenceImages = normalizeAiImageReferenceRoles(conversation.referenceImages);
  rebuildAiImagePromptFromSkill(conversation, { force: true });
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  renderAiImageForm();
  renderAiImageResults();
}

function renderAiImageReferences() {
  const strip = $("#ai-image-reference-strip");
  if (!strip) return;
  const conversation = ensureAiImageConversation();
  const references = conversation.referenceImages || [];
  const mask = conversation.maskImage || null;
  const mode = conversation.mode || "text";
  const virtualTryOnActive = conversation.templateKey === "virtualTryOn";
  strip.hidden = !references.length && !mask;
  if (!references.length && !mask) {
    strip.innerHTML = "";
    return;
  }
  strip.innerHTML = `
    <div class="ai-image-reference-head">
      <strong>输入素材 ${references.length} 张 · 不限数量${mask ? " · 蒙版已添加" : ""}</strong>
      <button class="ghost-btn" type="button" data-ai-reference-clear>清空</button>
    </div>
    ${mode !== "inpaint" ? `<p class="ai-image-reference-guide">${esc(virtualTryOnActive
      ? "搭配顺序：上传商品/服装图和人物图，再把其余图片分别设为包袋、帽子、鞋履、首饰或场景参考。系统按文件名逐件替换，人物参考锁定脸部与身材；提示词可要求完整全身、换场景或只改某件配饰。固定输出 1 张连续场景图，不生成宫格。"
      : "其他产品的成套页面请选择“系列风格参考”，系统只提取配色、标题层级、信息密度、模块形状和呈现效果；商品、人物、文字、Logo 与数据不会作为当前产品内容。")}</p>` : ""}
    <div class="ai-image-reference-list">
      ${references.map((item, index) => {
        const roleKey = aiImageReferenceRoleKey(item, index);
        return `
        <div class="ai-image-reference-card">
          <img src="${esc(item.previewDataUrl)}" alt="${esc(item.name || "参考图")}" />
          <b>${esc(mode === "inpaint" ? "原图" : aiImageReferenceRoleLabel(roleKey))}</b>
          <span>${esc(item.name || "参考图")}</span>
          ${mode !== "inpaint" ? `
            <select data-ai-reference-role="${esc(item.id)}" aria-label="${esc(item.name || `参考图 ${index + 1}`)}的用途" ${index === 0 ? "disabled" : ""}>
              ${AI_IMAGE_REFERENCE_ROLES.map((role) => `<option value="${esc(role.key)}" ${role.key === roleKey ? "selected" : ""}>${esc(role.label)}</option>`).join("")}
            </select>
            ${(["scene", "person", "bag", "hat", "shoes", "jewelry", "accessory", "package", "layout", "styleSet"].includes(roleKey)) ? `
              <input type="text" value="${esc(item.keywords || "")}" data-ai-reference-keywords="${esc(item.id)}" maxlength="240" placeholder="${esc(aiImageReferenceKeywordPlaceholder(roleKey))}" aria-label="${esc(aiImageReferenceRoleLabel(roleKey))}关键词" />
              <small class="ai-image-reference-keyword-hint">${esc(aiImageReferenceKeywordHint(roleKey))}</small>
            ` : ""}
          ` : ""}
          <button class="icon-btn" type="button" data-ai-reference-remove="${esc(item.id)}" aria-label="删除参考图">×</button>
        </div>
      `;
      }).join("")}
      ${mask ? `
        <div class="ai-image-reference-card ai-image-mask-card">
          <img src="${esc(mask.previewDataUrl)}" alt="局部重绘蒙版" />
          <b>编辑蒙版</b>
          <span>${esc(mask.name || "mask.png")}</span>
          <button class="icon-btn" type="button" data-ai-mask-remove aria-label="删除蒙版">×</button>
        </div>
      ` : ""}
    </div>
  `;
}

function addAiImageReferences(files = [], options = {}) {
  const conversation = ensureAiImageConversation();
  const current = conversation.referenceImages || [];
  const selected = Array.from(files).filter((file) => file.type.startsWith("image/"));
  if (!selected.length) {
    showToast("请选择 jpg/png/webp 图片");
    return;
  }
  const requestedRole = String(options.role || "").trim();
  if (requestedRole === "styleSet" && !current.length) {
    showToast("请先上传主商品图，再添加系列风格参考");
    return;
  }
  const maxReferences = conversation.mode === "inpaint" ? 1 : Number.POSITIVE_INFINITY;
  const room = Math.max(0, maxReferences - current.length);
  if (!room) {
    showToast("局部重绘只需要 1 张原图");
    return;
  }
  selected.slice(0, room).forEach((file) => {
    const index = current.length;
    current.push({
      id: `ref-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      previewDataUrl: URL.createObjectURL(file),
      role: requestedRole && AI_IMAGE_REFERENCE_ROLES.some((role) => role.key === requestedRole)
        ? requestedRole
        : aiImageDefaultReferenceRole(index),
      keywords: "",
    });
  });
  conversation.referenceImages = normalizeAiImageReferenceRoles(current);
  conversation.restoreNotice = "";
  const suiteActive = aiImageSuiteActive(conversation);
  if (conversation.templateKey === "virtualTryOn") conversation.mode = "compose";
  else if (conversation.mode === "text") conversation.mode = suiteActive ? "edit" : current.length >= 2 ? "compose" : "edit";
  if (conversation.mode === "edit" && current.length >= 2 && !suiteActive) conversation.mode = "compose";
  rebuildAiImagePromptFromSkill(conversation);
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  renderAiImageForm();
  renderAiImageSidebar();
  renderAiImageResults();
  if (Number.isFinite(maxReferences) && selected.length > room) showToast(`已添加前 ${maxReferences} 张图片`);
}

function removeAiImageReference(id) {
  const conversation = ensureAiImageConversation();
  const references = conversation.referenceImages || [];
  const target = references.find((item) => item.id === id);
  if (target?.previewDataUrl?.startsWith("blob:")) URL.revokeObjectURL(target.previewDataUrl);
  conversation.referenceImages = normalizeAiImageReferenceRoles(references.filter((item) => item.id !== id));
  if (conversation.mode === "compose" && conversation.referenceImages.length < 2) conversation.mode = conversation.referenceImages.length ? "edit" : "text";
  rebuildAiImagePromptFromSkill(conversation);
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  renderAiImageForm();
  renderAiImageSidebar();
  renderAiImageResults();
}

function clearAiImageReferences() {
  const conversation = ensureAiImageConversation();
  (conversation.referenceImages || []).forEach((item) => {
    if (item.previewDataUrl?.startsWith("blob:")) URL.revokeObjectURL(item.previewDataUrl);
  });
  conversation.referenceImages = [];
  if (conversation.maskImage?.previewDataUrl?.startsWith("blob:")) URL.revokeObjectURL(conversation.maskImage.previewDataUrl);
  conversation.maskImage = null;
  if (conversation.mode !== "text") conversation.mode = aiImageSuiteActive(conversation) ? "edit" : "text";
  rebuildAiImagePromptFromSkill(conversation);
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  renderAiImageForm();
  renderAiImageSidebar();
  renderAiImageResults();
}

function addAiImageMask(files = []) {
  const file = Array.from(files).find((item) => item.type === "image/png" || item.name.toLowerCase().endsWith(".png"));
  if (!file) {
    showToast("蒙版请上传 PNG 图片");
    return;
  }
  if (file.size > 25 * 1024 * 1024) {
    showToast("蒙版不能超过 25MB");
    return;
  }
  const conversation = ensureAiImageConversation();
  if (conversation.maskImage?.previewDataUrl?.startsWith("blob:")) URL.revokeObjectURL(conversation.maskImage.previewDataUrl);
  conversation.maskImage = {
    id: `mask-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
    file,
    name: file.name,
    size: file.size,
    type: file.type || "image/png",
    previewDataUrl: URL.createObjectURL(file),
  };
  conversation.mode = "inpaint";
  rebuildAiImagePromptFromSkill(conversation);
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  renderAiImageForm();
  renderAiImageSidebar();
  renderAiImageResults();
}

function removeAiImageMask() {
  const conversation = ensureAiImageConversation();
  if (conversation.maskImage?.previewDataUrl?.startsWith("blob:")) URL.revokeObjectURL(conversation.maskImage.previewDataUrl);
  conversation.maskImage = null;
  rebuildAiImagePromptFromSkill(conversation);
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  renderAiImageForm();
  renderAiImageSidebar();
  renderAiImageResults();
}

function aiImageStoredPreviewUrl(material = {}) {
  const previewUrl = String(material.previewUrl || material.previewDataUrl || "");
  if (previewUrl.startsWith("/api/sku-board/ai-image-output/")) return previewUrl;
  const materialId = String(material.id || "").toUpperCase();
  if (/^AI-[A-F0-9]{10}$/.test(materialId)) {
    const remoteUrl = String(material.remoteUrl || (/^https?:\/\//i.test(previewUrl) ? previewUrl : ""));
    const remoteQuery = remoteUrl ? `?remote=${encodeURIComponent(remoteUrl)}` : "";
    return `/api/sku-board/ai-image-output/${materialId}${remoteQuery}`;
  }
  return /^https?:\/\//i.test(previewUrl) ? previewUrl : "";
}

function aiImageReferenceBindings(references = []) {
  return (Array.isArray(references) ? references : []).map((reference, index) => ({
    index: index + 1,
    role: aiImageReferenceRoleKey(reference, index),
    name: String(reference.name || reference.file?.name || "")
      .replace(/[\r\n\[\];]/g, " ")
      .trim()
      .slice(0, 120),
    keywords: String(reference.keywords || "").trim().slice(0, 240),
  }));
}

function aiImagePersistedMaterial(material = {}) {
  const { previewDataUrl, ...rest } = material;
  const storedPreviewUrl = aiImageStoredPreviewUrl(material);
  return {
    ...rest,
    previewUrl: storedPreviewUrl || rest.previewUrl || "",
    previewDataUrl: storedPreviewUrl,
  };
}

function aiImagePersistedConversation(conversation = {}) {
  const materials = (conversation.materials || []).map(aiImagePersistedMaterial);
  const referenceMeta = (conversation.referenceImages || []).map((item) => ({
    name: item.name || "参考图",
    size: Number(item.size || item.file?.size || 0),
    role: item.role || "product",
  }));
  return {
    ...conversation,
    materials,
    previewDataUrls: materials.map((material) => material.previewDataUrl || material.previewUrl || ""),
    referenceImages: [],
    maskImage: null,
    suiteStyleAnchorFile: null,
    referenceMeta,
    restoreNotice: referenceMeta.length ? "刷新后已恢复任务进度；如需补图、重做或继续生图，请重新上传产品参考图。" : conversation.restoreNotice || "",
  };
}

function persistAiImageState() {
  try {
    const conversations = (state.aiImages.conversations || [])
      .slice(0, AI_IMAGE_STATE_MAX_CONVERSATIONS)
      .map(aiImagePersistedConversation);
    localStorage.setItem(AI_IMAGE_STATE_STORAGE_KEY, JSON.stringify({
      version: AI_IMAGE_STATE_STORAGE_VERSION,
      activeId: state.aiImages.activeId || "",
      conversations,
    }));
  } catch (error) {
    console.warn("Unable to persist AI image state", error);
  }
}

function restoreAiImageState() {
  try {
    const stored = JSON.parse(localStorage.getItem(AI_IMAGE_STATE_STORAGE_KEY) || "null");
    if (!stored || stored.version !== AI_IMAGE_STATE_STORAGE_VERSION || !Array.isArray(stored.conversations)) return false;
    const conversations = stored.conversations
      .filter((item) => item && typeof item === "object" && String(item.id || "").startsWith("ai-"))
      .slice(0, AI_IMAGE_STATE_MAX_CONVERSATIONS)
      .map((item) => {
        const materials = Array.isArray(item.materials) ? item.materials.map(aiImagePersistedMaterial) : [];
        return {
          ...item,
          materials,
          previewDataUrls: materials.map((material) => material.previewDataUrl || material.previewUrl || ""),
          referenceImages: [],
          maskImage: null,
          suiteStyleAnchorFile: null,
          suiteCount: Number(item.suiteCount || 0),
          count: Number(item.count || 1),
          generationProfile: AI_IMAGE_GENERATION_PROFILES.some((profile) => profile.key === item.generationProfile) ? item.generationProfile : "standard",
          restoreNotice: item.restoreNotice || (item.referenceMeta?.length ? "刷新后已恢复任务进度；如需补图、重做或继续生图，请重新上传产品参考图。" : ""),
        };
      });
    if (!conversations.length) return false;
    state.aiImages.conversations = conversations;
    state.aiImages.activeId = conversations.some((item) => item.id === stored.activeId) ? stored.activeId : conversations[0].id;
    syncAiImageStateFromConversation(aiImageActiveConversation());
    return true;
  } catch (error) {
    console.warn("Unable to restore AI image state", error);
    return false;
  }
}

function revokeAiImageReferenceUrls(conversation) {
  (conversation?.referenceImages || []).forEach((item) => {
    if (item.previewDataUrl?.startsWith("blob:")) URL.revokeObjectURL(item.previewDataUrl);
  });
  if (conversation?.maskImage?.previewDataUrl?.startsWith("blob:")) URL.revokeObjectURL(conversation.maskImage.previewDataUrl);
}

function aiImageErrorDiagnosis(message = "") {
  const lower = String(message || "").toLowerCase();
  const activeModel = aiImageActiveConversation()?.model || state.aiImages.model || "gpt-image-2";
  const providerLabel = aiImageProviderLabel(activeModel);
  const isAcore = aiImageModelProvider(activeModel) === "acore";
  if (lower.includes("no available image quota") || lower.includes("image quota") || lower.includes("生图额度")) {
    return {
      title: "部分生图账号额度不足",
      reason: "远端账号池没有足够额度完成全部页面，但已经成功的页面仍可恢复并显示。",
      advice: ["先点“恢复远端套图”取回成功页", "仍在运行的页面稍后可以继续同步", "补充远端生图账号额度后，只重做缺失页"],
      actions: ["recover-suite"],
    };
  }
  if (lower.includes("cloudflare") || lower.includes("524")) {
    return {
      title: "Cloudflare 生成超时",
      reason: "远端生成超过 Cloudflare 同步请求时限，网关返回了 524。普通生图和参考图现已自动改用异步任务通道。",
      advice: ["刷新面板后再重试", "先点“检测服务”确认异步任务通道可用", "若只有局部重绘失败，请检查远端服务或将 API 域名设为仅 DNS"],
      actions: ["count-one", "retry"],
    };
  }
  if (lower.includes("timeout") || lower.includes("\u8d85\u65f6") || lower.includes("timed out")) {
    return {
      title: "\u751f\u56fe\u670d\u52a1\u54cd\u5e94\u8d85\u65f6",
      reason: isAcore
        ? `当前${providerLabel}任务超过等待阈值；重试仍会使用已选择的公司模型。`
        : "\u5f53\u524d\u8282\u70b9\u8d85\u8fc7\u7b49\u5f85\u9608\u503c\uff1b\u9762\u677f\u4f1a\u628a\u8be5\u8282\u70b9\u4e34\u65f6\u964d\u7ea7\uff0c\u5e76\u628a\u5931\u8d25\u9875\u81ea\u52a8\u5207\u6362\u5230\u5176\u4ed6\u670d\u52a1\u8282\u70b9\u7eed\u8dd1\u3002",
      advice: isAcore
        ? ["点击重试会继续使用当前公司模型", "套图已完成的页面会保留，只补失败页", "远端任务仍在运行时可点击恢复远端套图取回结果"]
        : ["\u70b9\u51fb\u91cd\u8bd5\u4f1a\u4ece\u5176\u4ed6\u5065\u5eb7\u8282\u70b9\u7ee7\u7eed\u5f53\u524d\u9875", "\u5957\u56fe\u5df2\u5b8c\u6210\u7684\u9875\u9762\u4f1a\u4fdd\u7559\uff0c\u53ea\u8865\u5931\u8d25\u9875", "\u8fdc\u7aef\u4efb\u52a1\u4ecd\u5728\u8fd0\u884c\u65f6\u53ef\u70b9\u51fb\u6062\u590d\u8fdc\u7aef\u5957\u56fe\u53d6\u56de\u7ed3\u679c"],
      actions: ["recover-suite", "retry"],
    };
  }
  if (lower.includes("please retry") || lower.includes("try again") || lower.includes("稍后重试") || lower.includes("稍後重試") || lower.includes("server busy") || lower.includes("temporarily unavailable")) {
    return {
      title: isAcore ? "公司生图服务暂时繁忙" : "远端生图节点正在切换账号",
      reason: isAcore
        ? `${providerLabel}暂时繁忙；点击重试仍会使用当前公司模型，本次已完成页面会继续保留。`
        : "远端账号池短暂繁忙时会返回“请稍后重试”。面板会自动改走其他节点；本次未完成页面可继续补图。",
      advice: isAcore
        ? ["稍等片刻后重试当前公司模型", "已完成图片会保留，只补失败页面", "若持续发生，使用错误编号在 ai_image_errors.log 中定位任务"]
        : ["点击重试会优先避开刚刚失败的节点", "已完成图片会保留，只补失败页面", "若持续发生，使用错误编号在 ai_image_errors.log 中定位节点"],
      actions: ["recover-suite", "retry"],
    };
  }
  if (lower.includes("too many") || lower.includes("rate") || lower.includes("429") || lower.includes("限流")) {
    return {
      title: "请求太频繁或账号限流",
      reason: "当前账号池可能被限流，或者一次生成数量过多。",
      advice: ["减少生成数量", "稍等几分钟再试", `检查 ${providerLabel} 服务状态`],
      actions: ["count-one", "retry"],
    };
  }
  if (lower.includes("image") && (lower.includes("required") || lower.includes("empty") || lower.includes("参考图"))) {
    return {
      title: "参考图没有正确上传",
      reason: "图生图需要至少一张 jpg/png/webp 参考图。",
      advice: ["重新上传参考图", "图片不要超过 25MB", "不需要参考图时先清空参考图"],
      actions: ["clear-reference"],
    };
  }
  if (lower.includes("auth") || lower.includes("401") || lower.includes("403") || lower.includes("key")) {
    return {
      title: "接口密钥或权限异常",
      reason: `${providerLabel}密钥可能不对，或者远端接口拒绝访问。`,
      advice: [`检查 .env 里的 ${isAcore ? "ACORE_IMAGE_AUTH_KEY" : "CHATGPT2API_AUTH_KEY"}`, "确认服务端密钥与面板配置一致"],
      actions: ["retry"],
    };
  }
  if (lower.includes("content") || lower.includes("policy") || lower.includes("filter") || lower.includes("违规")) {
    return {
      title: "提示词可能被拦截",
      reason: "远端内容审核或模型策略拒绝了这次生成。",
      advice: ["减少敏感描述", "保留商品、场景、风格，删除夸张词", "换一个模板再试"],
      actions: ["retry"],
    };
  }
  return {
    title: "生成服务返回错误",
    reason: "面板已收到失败信息，但需要看具体错误文本判断。",
    advice: ["先点重试", "如果仍失败，查看本地 ai_image_errors.log", `确认 ${providerLabel} 服务能打开`],
    actions: ["retry"],
  };
}

function renderAiImageErrorBlock(message = "") {
  const diagnosis = aiImageErrorDiagnosis(message);
  const actionButtons = diagnosis.actions.map((action) => {
    const labels = { retry: "重试", "count-one": "改成1张", "clear-reference": "清空参考图", "recover-suite": "恢复远端套图" };
    return `<button class="ghost-btn" type="button" data-ai-error-action="${esc(action)}">${esc(labels[action] || action)}</button>`;
  }).join("");
  return `
    <div class="ai-image-alert">
      <div>
        <strong>${esc(diagnosis.title)}</strong>
        <p>${esc(diagnosis.reason)}</p>
      </div>
      <small>${esc(message || "生成失败")}</small>
      <ul>
        ${diagnosis.advice.map((item) => `<li>${esc(item)}</li>`).join("")}
      </ul>
      <div class="ai-image-alert-actions">${actionButtons}</div>
    </div>
  `;
}

function renderAiImageDirectorMonitor(conversation = {}) {
  const suiteConfig = aiImageSuiteConfig(conversation);
  const monitorConfig = suiteConfig?.monitor;
  if (!monitorConfig) return "";
  const countryConfig = aiImageCodCountryActive(conversation) ? aiImageCodCountryConfig(conversation.suiteCountry || "KR") : null;
  const detailSuite = suiteConfig.key === "cod-country-detail-12";
  const codExpressive = aiImageCodCountryActive(conversation);
  const jpCreativeDirector = suiteConfig.key === "jp-landing-page-25";
  const monitorEyebrow = countryConfig ? `${countryConfig.value} COD${detailSuite ? " DETAIL" : ""} DIRECTOR` : monitorConfig.eyebrow;
  const monitorAriaLabel = countryConfig ? `COD${countryConfig.label}${detailSuite ? "详情图" : "落地页"}导演监控` : monitorConfig.ariaLabel;
  const monitorDescription = countryConfig
    ? `${monitorConfig.description.replace("国家本土化", `${countryConfig.label}本土化`)}`
    : monitorConfig.description;
  const summary = conversation.remoteSummary || {};
  const review = conversation.review || {};
  const pageStates = summary.pageStates || {};
  const completedPages = new Set((conversation.materials || [])
    .map((material) => Number(material.suitePage || 0))
    .filter((page) => page >= 1 && page <= suiteConfig.count));
  const stateEntries = Object.entries(pageStates);
  const activePages = stateEntries.filter(([, status]) => ["running", "retrying", "reviewing", "quality-retry", "pending", "queued"].includes(status));
  const failedPages = stateEntries.filter(([, status]) => status === "failed");
  const completeCount = completedPages.size;
  const runningCount = Math.max(Number(summary.running || 0), activePages.length);
  const failedCount = Math.max(Number(summary.failed || 0), failedPages.length);
  const remainingCount = Math.max(0, suiteConfig.count - completeCount);
  const progress = Math.round((completeCount / suiteConfig.count) * 100);
  const planReady = Array.isArray(conversation.suitePages) && conversation.suitePages.length === suiteConfig.count;
  const referenceReady = Boolean(conversation.referenceImages?.length);
  const sizeReady = conversation.size === suiteConfig.size;
  const anchorReady = completedPages.has(1);
  const health = state.aiImages.health || {};
  const poolReady = ["remote_account_pool", "multi_node_account_pool"].includes(health.dispatchMode);
  const poolTone = poolReady ? "ready" : health.loading ? "active" : health.status === "error" ? "danger" : "waiting";
  const poolValue = poolReady
    ? `${Number(health.nodeCount || 0) > 1 ? `${health.nodeCount} 个节点 · ` : ""}${Number(health.accountPoolTotal || 0) ? `${health.accountPoolTotal} 个账号 · ` : ""}自动调度`
    : health.loading
    ? "正在检测"
    : health.status === "error"
    ? "服务连接异常"
    : "等待服务检测";
  const statusTone = conversation.status === "done"
    ? "ready"
    : conversation.status === "error"
    ? "danger"
    : ["planning", "generating"].includes(conversation.status)
    ? "active"
    : conversation.status === "partial"
    ? "warning"
    : "waiting";
  const statusLabel = {
    ready: `${suiteConfig.count} 图监控完成`,
    danger: "发现生成异常",
    active: "导演监控运行中",
    warning: "套图尚未完整",
    waiting: planReady ? "导演脚本已就绪" : "等待开始策划",
  }[statusTone];
  const firstRole = conversation.suitePages?.[0]?.role || (detailSuite ? "商品介绍" : "第 1 图");
  const lastRole = conversation.suitePages?.[suiteConfig.count - 1]?.role || (detailSuite ? "产品信息收尾" : "品牌收尾");
  const directorRun = conversation.director || {};
  const inspirationRun = directorRun.inspiration || aiImageSkillConfig().inspirationLibraryRuntime || {};
  const inspirationBlueprintCount = Number(
    directorRun.blueprintReferenceCount || inspirationRun.blueprintReferenceCount || 0,
  );
  const inspirationBlueprintReady = inspirationRun.integrationMode === "full-prompt-blueprint" || inspirationBlueprintCount > 0;
  const blockedClaimCount = Array.isArray(directorRun.factAudit?.blocked) ? directorRun.factAudit.blocked.length : 0;
  const sellingPointCoverage = directorRun.sellingPointCoverage || {};
  const sellingPointTotal = Number(sellingPointCoverage.total || 0);
  const sellingPointAssigned = Number(sellingPointCoverage.assigned || 0);
  const sellingPointMissing = Array.isArray(sellingPointCoverage.missing) ? sellingPointCoverage.missing : [];
  const directorConfig = state.aiImages.director || {};
  const referenceAnalysis = directorRun.referenceAnalysis || {};
  const referenceBreakdown = Array.isArray(directorRun.referenceBreakdown) ? directorRun.referenceBreakdown : [];
  const expectedReferenceAnalysisCount = Number(
    directorRun.referenceImageCount || conversation.referenceImages?.length || 0,
  );
  const marketResearchRun = directorRun.marketResearch || {};
  const companyCreativePages = (conversation.suitePages || []).filter((page) => page.companyCreativeLogic?.version);
  const productVisualDNA = directorRun.productVisualDNA
    || companyCreativePages[0]?.companyCreativeLogic?.productVisualDNA
    || {};
  const productDnaColors = Array.from(new Set([
    ...(Array.isArray(productVisualDNA.observableColors) ? productVisualDNA.observableColors : []),
    productVisualDNA.backgroundColor,
    productVisualDNA.accentColor,
    productVisualDNA.textColor,
  ].filter((color) => /^#[0-9a-f]{6}$/i.test(String(color || "")))));
  const productDnaAnchorCount = ["shapeAnchors", "materialAnchors", "labelAnchors"]
    .reduce((total, field) => total + (Array.isArray(productVisualDNA[field]) ? productVisualDNA[field].length : 0), 0);
  const companyNarrativeStages = new Set(companyCreativePages
    .map((page) => page.companyCreativeLogic?.narrativeStage)
    .filter(Boolean));
  const mappedPromptPages = companyCreativePages.filter((page) => {
    const mapping = page.companyCreativeLogic?.analysisPromptMapping || {};
    return mapping.product && mapping.layout && mapping.copy !== undefined && mapping.realism;
  }).length;
  const moduleBlueprintPages = (conversation.suitePages || []).filter((page) => (
    Array.isArray(page.companyModulePlan) && page.companyModulePlan.length >= 4
  ));
  const companyModuleCount = moduleBlueprintPages.reduce((total, page) => total + page.companyModulePlan.length, 0);
  const referenceAnalysisCount = ["product", "layout", "informationArchitecture"]
    .filter((field) => String(referenceAnalysis[field] || "").trim()).length;
  const previsualizedPages = (conversation.suitePages || []).filter((page) => {
    const visual = page.visualEnhancement || {};
    return visual.emotionAnchor && visual.shotConcept && visual.camera && visual.lighting
      && visual.spatialPlan && visual.modulePlan && Array.isArray(visual.riskControls);
  }).length;
  const humanPages = (conversation.suitePages || []).filter((page) => page.hasHuman === true).length;
  const marketResearchVersion = marketResearchRun.version || suiteConfig.marketResearchVersion || "";
  const generationProfile = aiImageGenerationProfile(conversation);
  const directorTone = ["model", "cache"].includes(directorRun.source)
    ? "ready"
    : directorRun.source === "pending" || directorRun.status === "running"
    ? "active"
    : directorRun.status === "warning"
    ? "warning"
    : planReady
    ? "ready"
    : directorConfig.enabled && directorConfig.configured
    ? "active"
    : "waiting";
  const directorValue = directorRun.source === "model"
    ? directorRun.model || "AI 模型"
    : directorRun.source === "cache"
    ? "产品缓存 · 已复用"
    : directorRun.source === "pending"
    ? directorRun.message || "导演分析中"
    : directorRun.status === "warning"
    ? "模型异常 · 已回退"
    : planReady
    ? "本地规则导演"
    : directorConfig.enabled && directorConfig.configured
    ? `等待 ${directorConfig.model || "AI 模型"}`
    : "本地规则待命";
  const directorStageIndex = Number.isFinite(Number(directorRun.stageIndex))
    ? Number(directorRun.stageIndex)
    : directorRun.stage === "complete" || planReady
    ? AI_IMAGE_DIRECTOR_STAGES.length - 1
    : 0;
  const reviewEnabled = directorConfig.reviewEnabled !== false && generationProfile.review !== "off";
  const reviewTone = review.status === "reviewing"
    ? "active"
    : review.status === "complete" && Number(review.failed || 0) > 0
    ? "warning"
    : review.status === "complete"
    ? "ready"
    : review.status === "warning"
    ? "warning"
    : reviewEnabled
    ? "waiting"
    : "waiting";
  const reviewValue = review.status === "reviewing"
    ? `正在质检 ${Number(review.reviewed || 0)}/${completeCount}`
    : review.status === "complete"
    ? `${Number(review.passed || 0)} 通过 · ${Number(review.failed || 0)} 待修正`
    : review.status === "warning"
    ? "质检异常 · 已保留原图"
    : reviewEnabled
    ? generationProfile.review === "key"
      ? `标准策略：重点页按 ${Number(directorConfig.reviewThreshold || 78)} 分检查`
      : `成图后按 ${Number(directorConfig.reviewThreshold || 78)} 分检查`
    : generationProfile.review === "off" ? "极速策略：跳过成图质检" : "管理员已关闭";
  const checks = [
    {
      tone: planReady ? "ready" : conversation.status === "generating" ? "active" : "waiting",
      label: monitorConfig.planLabel || `${suiteConfig.count} 模块脚本`,
      value: planReady ? "顺序已锁定" : "等待导演策划",
      hint: `${firstRole}至${lastRole}`,
    },
    {
      tone: directorTone,
      label: "AI 产品导演",
      value: directorValue,
      hint: directorRun.source === "model"
        ? `${directorRun.visionUsed ? "产品图 + 提示词" : "提示词"} · ${Number(directorRun.latencyMs || 0)}ms`
        : directorRun.source === "cache"
        ? `${Number(directorRun.analysisCounts?.main || 0)} 主卖点 · ${Number(directorRun.analysisCounts?.secondary || 0)} 次卖点 · 0ms`
        : directorRun.warning || "模型失败时自动使用本地规则",
    },
    ...(jpCreativeDirector ? [
      {
        tone: referenceAnalysisCount === 3 || planReady ? "ready" : "waiting",
        label: "三层参考分析",
        value: referenceAnalysisCount === 3 ? "产品 / 排版 / 信息架构已读透" : planReady ? "本地三层骨架已加载" : "等待识别参考图",
        hint: "提取HEX与材质、模块密度与留白、卖点证据层级",
      },
      {
        tone: expectedReferenceAnalysisCount > 0 && referenceBreakdown.length === expectedReferenceAnalysisCount
          ? "ready"
          : planReady ? "warning" : "waiting",
        label: "逐图三层解剖",
        value: `${referenceBreakdown.length}/${expectedReferenceAnalysisCount || conversation.referenceImages?.length || 0} 张参考图已逐张分析`,
        hint: "每张分别记录产品事实、排版骨架、信息架构、用途与禁止迁移项",
      },
      {
        tone: productDnaColors.length ? "ready" : planReady ? "warning" : "waiting",
        label: "产品视觉 DNA",
        value: productDnaColors.length ? productDnaColors.join(" / ") : "等待提取产品色彩基因",
        hint: `${productDnaAnchorCount} 项形状/材质/标签锚点 · 色板从产品与参考图生长`,
      },
      {
        tone: companyNarrativeStages.size === 5 ? "ready" : planReady ? "warning" : "waiting",
        label: "整套叙事弧线",
        value: `${companyNarrativeStages.size}/5 阶段已覆盖`,
        hint: "问题解决 → 卖点深挖 → 本土信任 → 证据工艺 → 决策收尾",
      },
      {
        tone: mappedPromptPages === suiteConfig.count ? "ready" : planReady ? "warning" : "waiting",
        label: "分析→Prompt映射",
        value: `${mappedPromptPages}/${suiteConfig.count} 页已建立映射`,
        hint: "产品、受众、背景、版式、文案、语言、真实感逐项进入当前页Prompt",
      },
      {
        tone: moduleBlueprintPages.length === suiteConfig.count ? "ready" : planReady ? "warning" : "waiting",
        label: "公司式模块施工图",
        value: `${moduleBlueprintPages.length}/${suiteConfig.count} 页 · ${companyModuleCount} 个模块`,
        hint: "每个模块明确 Visual / Content / Position / Weight / Container",
      },
      {
        tone: suiteConfig.planVersion === "director-v24-company-photography-density" ? "ready" : "waiting",
        label: "公司式短 Prompt 执行",
        value: "正向成片 Brief · 单页 ≤ 7800 字符",
        hint: "先写具体场景与当前卖点，再写模块施工图；移除重复规则和整套卖点干扰",
      },
      {
        tone: marketResearchVersion ? "ready" : "waiting",
        label: "日本市场调研",
        value: marketResearchVersion ? `本地权威档案 · ${marketResearchVersion}` : "等待加载市场档案",
        hint: "Rakuten商品摄影、商品同一性与W3C/JIS日文组版规则",
      },
      {
        tone: previsualizedPages === suiteConfig.count ? "ready" : planReady ? "warning" : "waiting",
        label: "先成像后落字",
        value: `${previsualizedPages}/${suiteConfig.count} 页摄影预演`,
        hint: "先形成完整成片，再写焦段、光线、动作与文案",
      },
      {
        tone: previsualizedPages === suiteConfig.count ? "ready" : planReady ? "warning" : "waiting",
        label: "摄影与空间规划",
        value: previsualizedPages ? `${previsualizedPages} 页已锁定焦段/光向/百分比分区` : "等待逐页导演brief",
        hint: "相邻页机位、景别、光向、场景和信息区不重复",
      },
      {
        tone: planReady ? "ready" : "waiting",
        label: "密度与防翻车",
        value: planReady ? "首图2模块 · 普通页最多3模块 · 专用页结构锁定" : "等待结构编排",
        hint: "同页模块只证明同一卖点；少大准日文、简单手势、真实肤质",
      },
      {
        tone: humanPages === 24 ? "ready" : planReady ? "warning" : "waiting",
        label: "人物页硬约束",
        value: planReady ? `${humanPages}/25 页已声明 has_human` : "等待识别人物页",
        hint: "单模特、40代日本女性、真实毛孔、简单手势与自然解剖",
      },
      {
        tone: planReady ? "ready" : "waiting",
        label: "完整Prompt送达",
        value: planReady ? "逐页最高 24,000 字符直送生图节点" : "等待逐页Prompt编译",
        hint: "保留尾部商品锁、人物锁、质检门与防翻车约束",
      },
    ] : []),
    {
      tone: referenceReady ? "ready" : "danger",
      label: "商品主图",
      value: referenceReady ? `已锁定 ${conversation.referenceImages.length} 张` : "缺少产品参考",
      hint: "保持类别、颜色、部件与材质",
    },
    {
      tone: sizeReady ? "ready" : "warning",
      label: monitorConfig.sizeLabel,
      value: sizeReady ? suiteConfig.size : `当前 ${conversation.size || "未设置"}`,
      hint: monitorConfig.sizeHint,
    },
    {
      tone: anchorReady ? "ready" : conversation.status === "generating" ? "active" : "waiting",
      label: "视觉母版",
      value: anchorReady ? "第 1 图已建立" : conversation.status === "generating" ? "正在建立" : "等待第 1 图",
      hint: "统一后续配色与节奏",
    },
    {
      tone: "ready",
      label: countryConfig ? `${countryConfig.label}${detailSuite ? "COD详情图" : "落地页"}规则` : monitorConfig.complianceLabel,
      value: "生成规则已注入",
      hint: monitorConfig.complianceHint,
    },
    {
      tone: inspirationRun.ready ? "ready" : inspirationRun.installed ? "warning" : "waiting",
      label: "灵感检索 Skill",
      value: inspirationRun.ready
        ? inspirationBlueprintReady
          ? `Open Image Prompts · ${inspirationBlueprintCount} 条完整蓝图`
          : `Open Image Prompts · ${Number(inspirationRun.referenceCount || 0)} 条标签参考`
        : inspirationRun.installed
        ? "Open Image Prompts · 等待数据"
        : "Open Image Prompts · 待安装",
      hint: inspirationRun.ready
        ? inspirationBlueprintReady
          ? `${inspirationRun.taxonomyVersion || "oip-visual-v2"} · 完整提示词仅供AI导演提炼 · 原提示词与参考图锁定`
          : `${inspirationRun.taxonomyVersion || "oip-visual-v2"} · 视觉标签参考 · 原提示词内容保持`
        : inspirationRun.message || "本地只读提示词参考库",
    },
    ...(codExpressive ? [{
      tone: sellingPointTotal && sellingPointAssigned >= sellingPointTotal ? "ready" : planReady ? "warning" : "waiting",
      label: "卖点图片覆盖",
      value: sellingPointTotal ? `${sellingPointAssigned}/${sellingPointTotal} 项已分配独立图片` : "等待卖点分析",
      hint: sellingPointMissing.length
        ? `当前图片数量仍缺：${sellingPointMissing.slice(0, 3).join("、")}${sellingPointMissing.length > 3 ? "等" : ""}`
        : "主卖点优先，其次逐项覆盖次卖点；AI导演只增强证据，不替换原始卖点",
    }] : []),
    {
      tone: codExpressive ? (blockedClaimCount ? "ready" : planReady ? "ready" : "waiting") : blockedClaimCount ? "warning" : planReady ? "ready" : "waiting",
      label: codExpressive ? "COD卖点视觉化" : "商品事实锁定",
      value: codExpressive ? (blockedClaimCount ? `${blockedClaimCount} 项已纳入夸张视觉编排` : planReady ? "全部卖点已编排" : "等待产品分析") : blockedClaimCount ? `${blockedClaimCount} 项已中性改写` : planReady ? "未发现高风险声明" : "等待产品分析",
      hint: codExpressive ? "原始卖点进入对比、结果、结构、场景与图标演绎" : "敏感、认证、数值与背书表达会自动转为中性产品展示",
    },
    {
      tone: poolTone,
      label: "远端账号池",
      value: poolValue,
      hint: "自动分配、重试与恢复",
    },
    {
      tone: reviewTone,
      label: "成图 AI 质检",
      value: reviewValue,
      hint: review.warning || "检查商品一致性、卖点、文字、畸变、留白与合规",
    },
  ];
  return `
    <section class="ai-image-director-monitor ${esc(suiteConfig.resultClass || "")}" aria-label="${esc(monitorAriaLabel)}">
      <header class="ai-image-director-monitor-head">
        <div>
          <span>${esc(monitorEyebrow)}</span>
          <strong>导演监控</strong>
          <p>${esc(monitorDescription)}</p>
        </div>
        <div class="ai-image-director-state ${esc(statusTone)}"><i></i><span>${esc(statusLabel)}</span></div>
      </header>
      <div class="ai-image-director-overview">
        <div class="ai-image-director-progress">
          <div>
            <strong>${completeCount}/${suiteConfig.count}</strong>
            <span>模块已完成</span>
          </div>
          <div class="ai-image-generation-progress" aria-label="${esc(monitorAriaLabel)}进度">
            <i style="width:${progress}%"></i>
          </div>
        </div>
        <div class="ai-image-director-metrics">
          <span><b>${runningCount}</b>生成或排队</span>
          <span><b>${remainingCount}</b>尚未完成</span>
          <span class="${failedCount ? "danger" : ""}"><b>${failedCount}</b>失败</span>
        </div>
      </div>
      <div class="ai-image-director-stages" aria-label="导演策划阶段">
        ${AI_IMAGE_DIRECTOR_STAGES.map((stage, index) => {
          const stageState = index < directorStageIndex ? "complete" : index === directorStageIndex ? (directorRun.stage === "complete" ? "complete" : "active") : "waiting";
          return `<span class="${stageState}"><i></i><b>${esc(stage.label)}</b></span>`;
        }).join("")}
      </div>
      <div class="ai-image-review-overview ${reviewTone}">
        <span>AI 质检</span>
        <b>${Number(review.reviewed || 0)}</b><small>已检查</small>
        <b>${Number(review.passed || 0)}</b><small>通过</small>
        <b>${Number(review.failed || 0)}</b><small>未通过</small>
        <b>${Number(review.retried || 0)}</b><small>已补图</small>
      </div>
      <div class="ai-image-director-checks">
        ${checks.map((check) => `
          <div class="ai-image-director-check ${esc(check.tone)}">
            <i></i>
            <div>
              <strong>${esc(check.label)}</strong>
              <span>${esc(check.value)}</span>
              <small>${esc(check.hint)}</small>
            </div>
          </div>
        `).join("")}
      </div>
    </section>
  `;
}

function renderAiImageRecoveryBlock(conversation = {}) {
  const summary = conversation.remoteSummary || {};
  if (conversation.status === "generating") return "";
  if (!aiImageSuiteActive(conversation) || (!summary.succeeded && !summary.running && !summary.failed)) return "";
  const suiteConfig = aiImageSuiteConfig(conversation);
  const suiteCount = suiteConfig.count;
  const suiteUnit = suiteConfig.unit;
  const succeeded = Number(summary.succeeded || conversation.materials?.length || 0);
  const running = Number(summary.running || 0);
  const failed = Number(summary.failed || 0);
  const missingPages = aiImageMissingSuitePages(conversation);
  const message = summary.message || `已恢复 ${succeeded}/${suiteCount} ${suiteUnit}；${running} ${suiteUnit}仍在生成，${failed} ${suiteUnit}失败`;
  return `
    <div class="ai-image-alert partial">
      <div>
        <strong>远端套图同步结果</strong>
        <p>${esc(message)}</p>
        <div class="ai-image-recovery-stats">
          <span>已显示 ${succeeded}</span>
          <span>生成中 ${running}</span>
          <span>失败 ${failed}</span>
        </div>
      </div>
      <div class="ai-image-recovery-actions">
        <button class="ghost-btn" type="button" data-ai-error-action="recover-suite">${running ? "继续同步" : "再次检查"}</button>
        ${missingPages.length ? `<button class="primary-btn" type="button" data-ai-error-action="fill-missing">补齐缺失${missingPages.length}${suiteUnit}</button>` : ""}
      </div>
    </div>
  `;
}

function renderAiImageFactAudit(conversation = {}) {
  if (!aiImageSuiteActive(conversation)) return "";
  const director = conversation.director || {};
  const audit = director.factAudit || {};
  const provided = Array.isArray(audit.provided) ? audit.provided : [];
  const visible = Array.isArray(audit.visible) ? audit.visible : [];
  const inferred = Array.isArray(audit.inferred) ? audit.inferred : [];
  const blocked = Array.isArray(audit.blocked) ? audit.blocked : [];
  if (!director.productSummary && !provided.length && !visible.length && !inferred.length && !blocked.length) return "";
  const safeFacts = [...visible, ...provided];
  const reviewMode = aiImageDirectorMode(conversation) === "review";
  const codExpressive = aiImageCodCountryActive(conversation);
  const blockedState = codExpressive
    ? (blocked.length ? `${blocked.length} 项已纳入视觉编排` : "全部卖点已编排")
    : (blocked.length ? `${blocked.length} 项已中性改写` : "事实检查通过");
  return `
    <section class="ai-image-fact-audit ${blocked.length && !codExpressive ? "warning" : "ready"}" aria-label="${codExpressive ? "COD卖点视觉化" : "商品事实锁定"}">
      <header>
        <div>
          <span>${codExpressive ? "COD CLAIM VISUAL MODE" : "PRODUCT FACT LOCK"}</span>
          <strong>${codExpressive ? "COD卖点视觉化" : "商品事实锁定"}</strong>
          ${director.productSummary ? `<p>${esc(director.productSummary)}</p>` : ""}
        </div>
        <div class="ai-image-fact-audit-state ${blocked.length && !codExpressive ? "warning" : "ready"}">${esc(blockedState)}</div>
      </header>
      <div class="ai-image-fact-audit-metrics">
        <span><b>${safeFacts.length}</b>${codExpressive ? "卖点证据" : "可用于文案"}</span>
        <span><b>${inferred.length}</b>${codExpressive ? "构图增强" : "仅用于构图"}</span>
        <span class="${blocked.length && !codExpressive ? "danger" : ""}"><b>${blocked.length}</b>${codExpressive ? "夸张视觉主题" : "已中性改写"}</span>
      </div>
      ${blocked.length ? `
        <div class="ai-image-fact-blocked">
          <strong>${codExpressive ? "已纳入夸张视觉脚本" : "已从生图提示中隔离"}</strong>
          <p>${codExpressive ? "这些原始卖点会进入对比、结果、结构、场景、专家感画面与图标演绎，导演会为每个主题分配对应图片。" : "这些表达会自动换成材质、结构、场景和使用过程描述，生图提示不会直接发送原始敏感词。"}</p>
          <ul>${blocked.slice(0, 8).map((item) => `<li><b>${esc(item.claim || (codExpressive ? "待演绎卖点" : "需中性改写的表达"))}</b><span>${esc(codExpressive ? "已锁定为 COD 视觉主题" : (item.reason || "已转为中性产品展示"))}</span></li>`).join("")}</ul>
          ${blocked.length > 8 ? `<small>${codExpressive ? `另有 ${blocked.length - 8} 项已纳入整套卖点分镜` : `另有 ${blocked.length - 8} 项已一并写入生图与复检禁用清单`}</small>` : ""}
        </div>
      ` : ""}
      ${(safeFacts.length || inferred.length) ? `
        <details ${reviewMode ? "open" : ""}>
          <summary>查看可用事实与构图推断</summary>
          <div class="ai-image-fact-groups">
            <div>
              <strong>可用于文案</strong>
              <ul>${safeFacts.slice(0, 12).map((item) => `<li>${esc(item.claim || "")}</li>`).join("") || "<li>暂无已确认事实</li>"}</ul>
            </div>
            <div>
              <strong>仅用于构图</strong>
              <ul>${inferred.slice(0, 10).map((item) => `<li>${esc(item.claim || "")}</li>`).join("") || "<li>暂无构图推断</li>"}</ul>
            </div>
          </div>
        </details>
      ` : ""}
    </section>
  `;
}

function renderAiImageSuitePlan(conversation = {}) {
  if (!aiImageSuiteActive(conversation) || !Array.isArray(conversation.suitePages) || !conversation.suitePages.length) return "";
  const suiteConfig = aiImageSuiteConfig(conversation);
  const materialByPage = new Map((conversation.materials || []).map((material) => [Number(material.suitePage || 0), material]));
  const materialPages = new Set([...materialByPage.keys()].filter(Boolean));
  const pageStates = conversation.remoteSummary?.pageStates || {};
  const pageMeta = conversation.remoteSummary?.pageMeta || {};
  const generationProfile = aiImageGenerationProfile(conversation);
  const completedCount = materialPages.size;
  const activeCount = Object.values(pageStates).filter((status) => ["running", "retrying", "reviewing", "quality-retry"].includes(status)).length;
  const failedCount = Object.values(pageStates).filter((status) => ["failed", "review-failed"].includes(status)).length;
  const etaMs = Number(conversation.remoteSummary?.etaMs || 0);
  const averagePageMs = Number(conversation.remoteSummary?.averagePageMs || 0);
  const liveProgress = conversation.status === "generating" || activeCount > 0;
  const liveSummary = `
    <div class="ai-image-suite-live-summary">
      <span><small>生成策略</small><strong>${esc(generationProfile.label)}</strong></span>
      <span><small>完成进度</small><strong>${completedCount}/${suiteConfig.count}</strong></span>
      <span><small>并行任务</small><strong>${activeCount}</strong></span>
      <span><small>平均单张</small><strong>${esc(formatAiImageDuration(averagePageMs))}</strong></span>
      <span><small>预计剩余</small><strong>${esc(formatAiImageDuration(etaMs))}</strong></span>
      <span class="${failedCount ? "warning" : ""}"><small>需处理</small><strong>${failedCount}</strong></span>
    </div>
  `;
  const planGrid = `
    <div class="ai-image-suite-plan-grid">
      ${conversation.suitePages.map((page) => {
        const pageNumber = Number(page.page || 0);
        const liveState = pageStates[pageNumber] || "";
        const stateValue = ["reviewing", "quality-retry", "review-failed"].includes(liveState) ? liveState : materialPages.has(pageNumber) ? "success" : liveState || "planned";
        const stateLabel = { success: "已完成", running: "生成中", retrying: "重试中", reviewing: "AI质检中", "quality-retry": "按质检补图", "review-failed": "需人工确认", pending: "待同步", failed: "失败", cancelled: "已取消", queued: "排队中", planned: "已策划" }[stateValue] || "已策划";
        const material = materialByPage.get(pageNumber) || {};
        const meta = pageMeta[pageNumber] || {};
        const nodeName = material.nodeName || meta.nodeName || aiImageGenerationNodeForPage(pageNumber).name || "自动调度";
        const elapsedMs = Number(material.generationMs || meta.elapsedMs || (["running", "retrying", "quality-retry"].includes(stateValue) && meta.startedAt ? Date.now() - Number(meta.startedAt) : 0));
        const attempt = Number(meta.attempt || 0);
        const densityLabel = { minimal: "简洁", focused: "聚焦", structured: "结构化" }[page.contentDensity] || "聚焦";
        return `
          <article class="ai-image-suite-plan-item ${esc(stateValue)}">
            <span class="ai-image-suite-plan-number">${String(pageNumber).padStart(2, "0")}</span>
            <div>
              <small>${esc(page.role || `第${pageNumber}${suiteConfig.unit}`)}</small>
              <strong>${esc(page.headline || page.title || `第${pageNumber}${suiteConfig.unit}`)}</strong>
              <p>${esc(page.focus || "")}</p>
              <div class="ai-image-suite-live-meta">
                <span>NODE <b>${esc(nodeName)}</b></span>
                <span>内容 <b>${esc(densityLabel)}</b></span>
                <span>${esc(stateLabel)}</span>
                <span>${elapsedMs ? `耗时 ${esc(formatAiImageDuration(elapsedMs))}` : "等待计时"}</span>
                ${attempt > 1 ? `<span>第 ${attempt} 次</span>` : ""}
              </div>
              <details>
                <summary>${esc(stateLabel)} · 查看画面设计</summary>
                <span><b>证据</b>${esc(page.evidence || "")}</span>
                <span><b>场景</b>${esc(page.scene || "")}</span>
                <span><b>动作</b>${esc(page.pose || "")}</span>
                <span><b>构图</b>${esc(page.composition || "")}</span>
                ${page.pageArchetype ? `<span><b>页面类型</b>${esc(page.pageArchetype)}</span>` : ""}
                ${page.sellingPoint ? `<span><b>本页卖点</b>${esc(page.sellingPoint)}</span>` : ""}
                ${page.displayEffect ? `<span><b>展示效果</b>${esc(page.displayEffect)}</span>` : ""}
                ${page.visualTreatment ? `<span><b>视觉分镜</b>${esc(page.visualTreatment)}</span>` : ""}
                ${page.impactTreatment ? `<span><b>冲击表现</b>${esc(page.impactTreatment)}</span>` : ""}
              </details>
            </div>
          </article>
        `;
      }).join("")}
    </div>
  `;
  const reviewMode = aiImageDirectorMode(conversation) === "review";
  return `
    <section class="ai-image-suite-plan ${esc(aiImageSuiteResultClass(conversation))}" aria-label="${esc(suiteConfig.planTitle)}">
      <header class="ai-image-suite-plan-head">
        <div>
          <span>DIRECTOR ${esc(conversation.suitePlanVersion || "V2")}</span>
          <strong>${esc(suiteConfig.planTitle)}</strong>
        </div>
        <small>${esc(suiteConfig.planHint)} · ${esc(generationProfile.label)}策略${etaMs ? ` · 预计 ${esc(formatAiImageDuration(etaMs))}` : ""}</small>
      </header>
      ${liveSummary}
      ${reviewMode || liveProgress ? planGrid : `
        <details class="ai-image-suite-plan-compact">
          <summary>${suiteConfig.count}${suiteConfig.unit}分镜已编排 · 展开查看</summary>
          ${planGrid}
        </details>
      `}
    </section>
  `;
}

function renderAiImageResults() {
  const container = $("#ai-image-results");
  if (!container) return;
  const conversation = ensureAiImageConversation();
  const prompt = (conversation.prompt || "").trim();
  const intent = (conversation.userIntent || "").trim();
  const materials = conversation.materials || [];
  const suiteActive = aiImageSuiteActive(conversation);
  const suiteConfig = aiImageSuiteConfig(conversation);
  const suiteCount = suiteConfig?.count || Number(conversation.count || 1);
  const suiteCountryLabel = aiImageCodCountryActive(conversation) ? aiImageCodCountryConfig(conversation.suiteCountry || "KR").label : "";
  const modeLabel = suiteConfig ? `${suiteConfig.label}${suiteCountryLabel ? ` · ${suiteCountryLabel}` : ""}` : aiImageModeLabel(conversation.mode || "text");
  const providerLabel = aiImageProviderLabel(conversation.model || state.aiImages.model || "gpt-image-2");
  const unit = suiteConfig?.unit || "张";
  const promptBlock = prompt
    ? `
      <article class="ai-image-prompt-card">
        <span>${esc(modeLabel)} · ${esc(aiImageLockDisplay(conversation.lockLevel || "strict"))} · Skill v${esc(conversation.skillVersion || aiImageSkillConfig().version || "内置")}${conversation.referenceImages?.length ? ` · 参考图 ${conversation.referenceImages.length} 张` : ""}${conversation.maskImage ? " · 蒙版" : ""} · ${esc(conversation.count || 1)} ${unit} · ${esc(aiImageSizeLabel(conversation.size || "1024x1024"))}</span>
        <p>${esc(intent || "已使用专业提示词生成")}</p>
        <details>
          <summary>查看专业提示词</summary>
          <pre>${esc(prompt)}</pre>
        </details>
      </article>
    `
    : "";
  const errorBlock = conversation.status === "error" ? renderAiImageErrorBlock(conversation.error || "请稍后重试") : "";
  const recoveryBlock = renderAiImageRecoveryBlock(conversation);
  const directorMonitorBlock = renderAiImageDirectorMonitor(conversation);
  const factAuditBlock = renderAiImageFactAudit(conversation);
  const suitePlanBlock = renderAiImageSuitePlan(conversation);
  const restoreNoticeBlock = conversation.restoreNotice ? `<div class="ai-image-alert"><div><strong>任务进度已恢复</strong><p>${esc(conversation.restoreNotice)}</p></div></div>` : "";
  if (!materials.length && conversation.status !== "generating") {
    container.innerHTML = `
      ${promptBlock}
      ${errorBlock}
      ${recoveryBlock}
      ${directorMonitorBlock}
      ${factAuditBlock}
      ${suitePlanBlock}
      ${restoreNoticeBlock}
      <div class="ai-image-empty">
        <strong>${conversation.status === "partial" ? "远端任务仍在处理中" : conversation.status === "cancelled" ? "本次生成已取消" : conversation.status === "planning" ? "正在分析商品与编排分镜" : conversation.status === "planned" ? "导演方案已就绪" : "先输入画面，再生成素材"}</strong>
        <p>${conversation.status === "partial" ? `点击继续同步，完成的${unit}会自动出现在这里。` : conversation.status === "cancelled" ? "已完成的图片仍然保留，可以点击重做本页或重新生成整套。" : conversation.status === "planning" ? "正在完成事实核验、卖点整理和分镜校验。" : conversation.status === "planned" ? "确认商品事实锁定和分镜后，再开始整套生图。" : "这里会显示批量生成结果，每张图都可以放大、下载，或者直接加入素材投放。"}</p>
      </div>
    `;
    return;
  }
  const suiteSummary = conversation.remoteSummary || {};
  const suiteProgress = Math.max(0, Math.min(100, Math.round((Number(suiteSummary.succeeded || 0) / suiteCount) * 100)));
  const loadingBlock = conversation.status === "generating"
    ? `
      <div class="ai-image-generating">
        <span class="ai-image-generating-spinner"></span>
        <div class="ai-image-generating-copy">
          <strong>${suiteActive ? esc(suiteSummary.message || `正在通过${providerLabel}分批生成整套${suiteConfig.label}`) : `正在调用 ${esc(providerLabel)} 执行${esc(modeLabel)}，生成 ${esc(conversation.count || 1)} 张图片`}</strong>
          ${suiteActive ? `
            <small>完成 ${esc(suiteSummary.succeeded || 0)}/${suiteCount} · 生成或待恢复 ${esc(suiteSummary.running || 0)} · 失败 ${esc(suiteSummary.failed || 0)}</small>
            <div class="ai-image-generation-progress" aria-label="${esc(suiteConfig.label)}生成进度"><i style="width:${suiteProgress}%"></i></div>
          ` : ""}
        </div>
      </div>
    `
    : "";
  container.innerHTML = `
    ${promptBlock}
    ${errorBlock}
    ${recoveryBlock}
    ${loadingBlock}
    ${directorMonitorBlock}
    ${factAuditBlock}
    ${suitePlanBlock}
    ${restoreNoticeBlock}
    <div class="ai-image-result-grid ${suiteActive ? "suite" : ""} ${esc(aiImageSuiteResultClass(conversation))}">
      ${materials.map((material, index) => renderAiImageResultCard(material, index, conversation)).join("")}
    </div>
  `;
}

function renderAiImageResultCard(material, index, conversation) {
  const preview = conversation.previewDataUrls?.[index] || material.previewDataUrl || material.previewUrl || "";
  const suiteActive = aiImageSuiteActive(conversation);
  const suiteConfig = aiImageSuiteConfig(conversation);
  const title = material.suiteTitle || material.name || `AI 图片 ${index + 1}`;
  const suitePage = Number(material.suitePage || index + 1);
  const pagePlan = suiteActive ? (conversation.suitePages || []).find((page) => Number(page.page) === suitePage) : null;
  const pageLabel = suiteActive ? `第 ${material.suitePage || index + 1} ${suiteConfig.unit}/${suiteConfig.count}` : `图片 ${index + 1}/${conversation.materials?.length || 1}`;
  const activeTag = material.reviewTag || "";
  const aiReview = material.aiReview || null;
  const canRedoWithoutMark = suiteActive && Boolean((conversation.referenceImages || []).some((item) => item.file));
  const canPromptEdit = Boolean(preview);
  const editPromptKey = aiImageMaterialEditPromptKey(material, index, suiteActive);
  const savedEditPrompt = String(conversation.pageEditPrompts?.[editPromptKey] || "");
  const pixelWidth = Number(material.pixelWidth || 0);
  const pixelHeight = Number(material.pixelHeight || 0);
  const isStrip = pixelWidth > 0 && pixelHeight > 0 && pixelWidth / pixelHeight >= 4;
  const thumbAspect = pixelWidth > 0 && pixelHeight > 0 ? `style="aspect-ratio:${pixelWidth}/${pixelHeight}"` : "";
  const lockedPageContent = pagePlan
    ? [pagePlan.focus, pagePlan.scene, pagePlan.pose, pagePlan.composition, pagePlan.headline].filter(Boolean).join("\n")
    : conversation.userIntent || "";
  const visualEnhancement = pagePlan?.visualEnhancement || material.singlePromptBlueprint?.visualEnhancement || {};
  const finalPrompt = material.prompt || "";
  const meta = [
    material.model || conversation.model || "gpt-image-2",
    material.sizePreset || conversation.size || "auto",
    material.storage === "remote" ? `远端存储${material.remoteNodeName ? ` · ${material.remoteNodeName}` : ""}` : material.storage === "local-temporary" ? "服务器临时文件 · 24小时清理" : "",
    material.skillVersion ? `Skill v${material.skillVersion}` : "",
    material.lockLevel ? aiImageLockDisplay(material.lockLevel) : "",
    activeTag ? aiImageResultTagLabel(activeTag) : "",
    aiImageFileSize(material.size),
  ].filter(Boolean).join(" · ");
  return `
    <article class="ai-image-result-card ${isStrip ? "is-strip" : ""} ${aiReview ? (aiReview.passed ? "review-pass" : "review-fail") : ""}">
      <button class="ai-image-result-thumb" type="button" data-ai-preview-index="${index}" ${thumbAspect} ${preview ? "" : "disabled"}>
        ${preview ? `<img src="${esc(preview)}" alt="${esc(title)}" loading="lazy" decoding="async" />` : `<span>图片已保存</span>`}
      </button>
      <div class="ai-image-result-meta">
        <span>${esc(pageLabel)}</span>
        <strong>${esc(title)}</strong>
        ${(material.suiteHeadline || pagePlan?.headline) ? `<em class="ai-image-result-headline">${esc(material.suiteHeadline || pagePlan.headline)}</em>` : ""}
        ${material.suiteFocus ? `<p class="ai-image-result-focus">${esc(material.suiteFocus)}</p>` : ""}
        <small>${esc(meta)}</small>
      </div>
      ${aiReview ? `
        <div class="ai-image-quality-review ${aiReview.passed ? "pass" : "fail"}">
          <div>
            <span>AI 质检</span>
            <strong>${Number(aiReview.score || 0)} 分 · ${aiReview.passed ? "通过" : "需确认"}</strong>
            <small>第 ${Number(aiReview.attempt || 1)} 次检查</small>
          </div>
          ${aiReview.issues?.length ? `<ul>${aiReview.issues.map((issue) => `<li>${esc(issue)}</li>`).join("")}</ul>` : `<p>${aiReview.passed ? "商品、卖点、文字与画面检查通过" : "复检后仍建议人工确认"}</p>`}
        </div>
      ` : ""}
      <details class="ai-image-prompt-diff">
        <summary>提示词保护与增强对照</summary>
        <div class="ai-image-prompt-diff-grid">
          <section class="locked">
            <span>原始内容锁定</span>
            <pre>${esc(conversation.userIntent || "使用当前专业提示词")}</pre>
          </section>
          <section class="page-lock">
            <span>当前图片任务</span>
            <pre>${esc(lockedPageContent || "单图任务")}</pre>
          </section>
          <section class="enhancement">
            <span>AI导演 / Open Image Prompts增强</span>
            <pre>${esc(Object.keys(visualEnhancement).length ? JSON.stringify(visualEnhancement, null, 2) : "本图使用模板摄影规则")}</pre>
          </section>
          <section class="final">
            <span>最终提交提示词</span>
            <pre>${esc(finalPrompt || conversation.prompt || "")}</pre>
          </section>
        </div>
      </details>
      <div class="ai-image-result-tags">
        ${AI_IMAGE_RESULT_TAGS.map((tag) => `
          <button class="${activeTag === tag.key ? "active" : ""}" type="button" data-ai-tag-index="${index}" data-ai-tag="${esc(tag.key)}">
            ${esc(tag.label)}
          </button>
        `).join("")}
      </div>
      <div class="ai-image-inline-edit">
        <label for="ai-image-edit-${index}">
          <span>按提示修改本图</span>
          <small>以当前成图为底图，可修改文字、数字、颜色、背景、人物、商品细节，或按新要求重新生成</small>
        </label>
        <textarea id="ai-image-edit-${index}" data-ai-edit-prompt-index="${index}" maxlength="360" placeholder="例如：图片中70%OFF改成50%OFF；保留商品和排版，把背景换成东京街头；按当前商品重新生成一版。">${esc(savedEditPrompt)}</textarea>
        <div>
          <span>未提到的商品、人物、场景和版式将继续保留</span>
          <button class="primary-btn" type="button" data-ai-edit-index="${index}" ${canPromptEdit ? "" : "disabled"}>按提示修改</button>
        </div>
      </div>
      <div class="ai-image-result-actions">
        <button class="ghost-btn" type="button" data-ai-preview-index="${index}" ${preview ? "" : "disabled"}>放大</button>
        <button class="ghost-btn" type="button" data-ai-download-index="${index}" ${preview ? "" : "disabled"}>下载</button>
        ${suiteActive ? `<button class="ghost-btn" type="button" data-ai-remove-mark-index="${index}" title="使用原商品图重新生成本张，移除未请求的角标或水印" ${canRedoWithoutMark ? "" : "disabled"}>去角标重做</button>` : ""}
        ${suiteActive ? `<button class="ghost-btn" type="button" data-ai-retry-index="${index}" title="只重新生成当前页" ${canRedoWithoutMark ? "" : "disabled"}>重做本页</button>` : ""}
        <button class="ghost-btn" type="button" data-ai-poster-index="${index}" ${preview ? "" : "disabled"}>套海报</button>
        <button class="primary-btn" type="button" data-ai-send-index="${index}">加入素材投放</button>
        ${/^AI-[A-F0-9]{10}$/.test(String(material.id || "").toUpperCase()) ? `<button class="ghost-btn danger" type="button" data-ai-delete-index="${index}">删除图片</button>` : ""}
      </div>
    </article>
  `;
}

function aiImageResultTagLabel(key) {
  return AI_IMAGE_RESULT_TAGS.find((tag) => tag.key === key)?.label || "";
}

function setAiImageResultTag(index = 0, tagKey = "") {
  const conversation = aiImageActiveConversation();
  const material = conversation?.materials?.[Number(index)];
  if (!material) return;
  const nextTag = material.reviewTag === tagKey ? "" : tagKey;
  material.reviewTag = nextTag;
  material.reviewTagLabel = aiImageResultTagLabel(nextTag);
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  renderAiImageResults();
}

function loadImageElement(src) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.crossOrigin = "anonymous";
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("图片加载失败，无法套海报版式"));
    image.src = src;
  });
}

function drawCoverImage(ctx, image, x, y, width, height) {
  const scale = Math.max(width / image.width, height / image.height);
  const drawWidth = image.width * scale;
  const drawHeight = image.height * scale;
  ctx.drawImage(image, x + (width - drawWidth) / 2, y + (height - drawHeight) / 2, drawWidth, drawHeight);
}

function drawContainImage(ctx, image, x, y, width, height) {
  const scale = Math.min(width / image.width, height / image.height);
  const drawWidth = image.width * scale;
  const drawHeight = image.height * scale;
  ctx.drawImage(image, x + (width - drawWidth) / 2, y + (height - drawHeight) / 2, drawWidth, drawHeight);
}

function wrapCanvasText(ctx, text, x, y, maxWidth, lineHeight, maxLines = 3) {
  const chars = String(text || "").replace(/\s+/g, " ").split("");
  let line = "";
  let lines = 0;
  chars.forEach((char) => {
    const test = line + char;
    if (ctx.measureText(test).width > maxWidth && line) {
      if (lines < maxLines) ctx.fillText(line, x, y + lines * lineHeight);
      line = char;
      lines += 1;
    } else {
      line = test;
    }
  });
  if (line && lines < maxLines) ctx.fillText(line, x, y + lines * lineHeight);
}

function aiPosterCopy(product = {}) {
  const context = aiImageProductContext(product);
  const isSkirt = /スカート|skirt|裙/i.test([context.title, ...context.tags].join(" "));
  const main = isSkirt ? "おしゃれで快適な" : "毎日をきれいに見せる";
  const productLine = isSkirt ? "Aラインロングスカート" : (context.title || "大人の上品アイテム").slice(0, 16);
  const points = context.points.length ? context.points : ["体型をすっきりカバー", "脚ラインをきれいに整える"];
  return {
    top: "ゆったりシルエットが",
    red: isSkirt ? "立体感のあるAライン" : "上品に見える美シルエット",
    main,
    productLine,
    bullets: points.slice(0, 2),
    colors: ["#f3eee6", "#111111", "#3a3a3a", "#4b2f22"],
    badge: isSkirt ? "-5kg\n着痩せる" : "細見え\n上品見え",
  };
}

async function uploadAiPosterBlob(blob, filename) {
  const formData = new FormData();
  formData.append("file", blob, filename);
  return api("/api/sku-board/ad-launch-materials", {
    method: "POST",
    body: formData,
  });
}

async function createAiPosterLayout(index = 0) {
  const conversation = aiImageActiveConversation();
  const material = conversation?.materials?.[Number(index)];
  const preview = conversation?.previewDataUrls?.[Number(index)] || material?.previewDataUrl || material?.previewUrl || "";
  if (!conversation || !material || !preview) {
    showToast("请先生成一张可预览的图片");
    return;
  }
  const button = document.querySelector(`[data-ai-poster-index="${Number(index)}"]`);
  const originalText = button?.textContent || "";
  if (button) {
    button.disabled = true;
    button.textContent = "排版中...";
  }
  try {
    const sourceImage = await loadImageElement(preview);
    const canvas = document.createElement("canvas");
    canvas.width = 900;
    canvas.height = 1200;
    const ctx = canvas.getContext("2d");
    const product = aiImageProductBySku(conversation.productSku);
    const copy = aiPosterCopy(product);

    ctx.fillStyle = "#e9e9e5";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "rgba(255,255,255,0.36)";
    ctx.fillRect(0, 0, 360, canvas.height);
    drawCoverImage(ctx, sourceImage, 280, 0, 620, 1200);
    const gradient = ctx.createLinearGradient(260, 0, 520, 0);
    gradient.addColorStop(0, "rgba(233,233,229,0.9)");
    gradient.addColorStop(1, "rgba(233,233,229,0)");
    ctx.fillStyle = gradient;
    ctx.fillRect(250, 0, 300, 1200);

    ctx.textAlign = "left";
    ctx.fillStyle = "#1b1b1b";
    ctx.font = "700 25px 'Yu Gothic', 'Microsoft YaHei', sans-serif";
    ctx.fillText(copy.top, 86, 82);
    ctx.fillStyle = "#b4232a";
    ctx.font = "800 34px 'Yu Gothic', 'Microsoft YaHei', sans-serif";
    ctx.fillText(copy.red, 38, 124);
    ctx.strokeStyle = "rgba(205, 170, 60, 0.65)";
    ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.moveTo(24, 84);
    ctx.quadraticCurveTo(44, 108, 24, 134);
    ctx.moveTo(320, 84);
    ctx.quadraticCurveTo(300, 108, 320, 134);
    ctx.stroke();

    ctx.fillStyle = "#111";
    ctx.font = "900 48px 'Yu Mincho', 'Yu Gothic', serif";
    ctx.fillText(copy.main, 34, 238);
    ctx.fillStyle = "#8b5b64";
    ctx.font = "700 44px Georgia, 'Yu Mincho', serif";
    wrapCanvasText(ctx, copy.productLine, 34, 305, 300, 52, 2);

    ctx.fillStyle = "#1f1f1f";
    ctx.font = "500 31px 'Yu Mincho', 'Microsoft YaHei', serif";
    wrapCanvasText(ctx, `${copy.bullets[0] || "体型をすっきりカバー"}、`, 34, 420, 310, 44, 2);
    wrapCanvasText(ctx, copy.bullets[1] || "脚ラインをきれいに整える", 34, 505, 310, 44, 2);

    ctx.fillStyle = "#111";
    ctx.font = "italic 34px Georgia, serif";
    ctx.fillText("4 Colors", 64, 660);
    copy.colors.forEach((color, colorIndex) => {
      const col = colorIndex % 2;
      const row = Math.floor(colorIndex / 2);
      const x = 56 + col * 98;
      const y = 690 + row * 102;
      ctx.fillStyle = color;
      ctx.fillRect(x, y, 70, 82);
      ctx.strokeStyle = "rgba(0,0,0,0.16)";
      ctx.lineWidth = 2;
      ctx.strokeRect(x, y, 70, 82);
    });

    ctx.fillStyle = "rgba(38,38,38,0.88)";
    ctx.beginPath();
    ctx.arc(155, 1000, 78, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(70, 1065, 50, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#fff";
    ctx.font = "700 56px Georgia, serif";
    ctx.fillText("XL", 115, 1020);
    ctx.font = "700 44px Georgia, serif";
    ctx.fillText("S", 48, 1082);

    ctx.fillStyle = "#fff9e9";
    ctx.strokeStyle = "#dd8a35";
    ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.ellipse(760, 1070, 105, 72, -0.18, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#141414";
    ctx.textAlign = "center";
    ctx.font = "800 48px Georgia, serif";
    const badgeLines = copy.badge.split("\n");
    ctx.fillText(badgeLines[0], 760, 1060);
    ctx.font = "700 30px 'Yu Gothic', sans-serif";
    ctx.fillText(badgeLines[1] || "", 760, 1102);

    ctx.fillStyle = "rgba(255,255,255,0.88)";
    ctx.fillRect(0, 1168, 900, 32);
    ctx.fillStyle = "#9a7b58";
    ctx.font = "700 17px 'Yu Gothic', sans-serif";
    ctx.textAlign = "left";
    ctx.fillText("SOSOVE", 24, 1191);

    const previewDataUrl = canvas.toDataURL("image/png");
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
    if (!blob) throw new Error("海报导出失败");
    const payload = await uploadAiPosterBlob(blob, `sosove-rakuten-poster-${Date.now()}.png`);
    const posterMaterial = {
      ...payload.material,
      previewDataUrl,
      source: "ai-poster-layout",
      sourceMode: "poster_layout",
      baseMaterialId: material.id,
      reviewTag: "poster",
      reviewTagLabel: aiImageResultTagLabel("poster"),
    };
    conversation.materials.push(posterMaterial);
    conversation.previewDataUrls.push(previewDataUrl);
    conversation.updatedAt = new Date().toISOString();
    syncAiImageStateFromConversation(conversation);
    renderAiImageResults();
    showToast("日系海报已生成并保存为素材");
  } catch (error) {
    showToast(error.message);
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = originalText || "套海报";
    }
  }
}

function createAiImageSuiteRunId() {
  if (window.crypto?.getRandomValues) {
    const bytes = new Uint8Array(6);
    window.crypto.getRandomValues(bytes);
    return Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("");
  }
  return `${Date.now().toString(16)}${Math.random().toString(16).slice(2)}`.replace(/[^0-9a-f]/g, "").slice(-12).padStart(12, "0");
}

function aiImageSuiteTransientError(message = "") {
  const source = String(message || "").toLowerCase();
  const permanentMarkers = [
    "no available image quota",
    "insufficient_quota",
    "quota exceeded",
    "content policy",
    "safety system",
    "moderation",
    "unauthorized",
    "forbidden",
    "invalid auth",
    "authentication failed",
    "unsupported size",
    "额度不足",
    "余额不足",
    "内容策略",
    "审核拒绝",
    "违规",
  ];
  if (permanentMarkers.some((marker) => source.includes(marker))) return false;
  return [
    "could not resolve host",
    "getaddrinfo",
    "name resolution",
    "temporary failure",
    "http/2 stream",
    "internal_error",
    "internal error",
    "please retry",
    "try again",
    "retry later",
    "稍后重试",
    "稍後重試",
    "server busy",
    "serverbusy",
    "temporarily unavailable",
    "too many open files",
    "connection reset",
    "connection aborted",
    "connection refused",
    "remote disconnected",
    "timed out",
    "timeout",
    "\u8d85\u65f6",
    "\u751f\u56fe\u8d85\u65f6",
    "image_poll_timeout_secs",
    "image generation failed",
    "image task returned no image data",
    "no image result",
    "upstream completed without generating images",
    "\u6ca1\u6709\u8fd4\u56de\u56fe\u7247",
    "\u56fe\u50cf\u751f\u6210\u8fc7\u7a0b\u4e2d\u51fa\u73b0\u4e86\u9519\u8bef",
    "\u65e0\u6cd5\u751f\u6210\u8fd9\u5f20\u56fe\u7247",
    "image generation encountered an error",
    "service unavailable",
    "bad gateway",
    "gateway timeout",
    "http 502",
    "http 503",
    "http 504",
    "http 524",
    "http 530",
    "dns",
    "连接异步生图任务接口失败",
    "提交超时",
  ].some((marker) => source.includes(marker));
}

function aiImageSuiteQuotaError(message = "") {
  const source = String(message || "").toLowerCase();
  return source.includes("no available image quota")
    || source.includes("没有可用生图额度")
    || source.includes("无可用图片额度");
}

async function refreshAiImageAccountPool() {
  if (aiImageAccountRefreshPromise) return aiImageAccountRefreshPromise;
  aiImageAccountRefreshPromise = api("/api/sku-board/ai-image-accounts-refresh", {
    method: "POST",
    body: JSON.stringify({}),
  });
  try {
    return await aiImageAccountRefreshPromise;
  } finally {
    aiImageAccountRefreshPromise = null;
  }
}

function aiImageSuitePayloadError(payload = {}) {
  const errors = Array.isArray(payload.suiteSummary?.errors) ? payload.suiteSummary.errors : [];
  const describe = (item, depth = 0) => {
    if (item == null) return "";
    if (typeof item === "string" || typeof item === "number" || typeof item === "boolean") return String(item).trim();
    if (depth > 3) return "";
    if (Array.isArray(item)) return item.map((entry) => describe(entry, depth + 1)).filter(Boolean).join("；");
    if (typeof item !== "object") return "";
    const primary = [item.message, item.detail, item.reason, item.error, item.error?.message]
      .map((entry) => describe(entry, depth + 1))
      .find(Boolean);
    const trace = [item.nodeName || item.node, item.taskId, item.requestId].filter(Boolean).join(" / ");
    if (primary) return trace ? `${trace}：${primary}` : primary;
    try {
      const compact = JSON.stringify(item);
      return compact && compact !== "{}" ? compact.slice(0, 360) : "";
    } catch (error) {
      return "";
    }
  };
  return errors.map((item) => describe(item) || "远端图片任务失败").filter(Boolean).join("；");
}

function aiImageMaterialsFromPayload(payload = {}) {
  const previews = payload.previewDataUrls?.length ? payload.previewDataUrls : [payload.previewDataUrl].filter(Boolean);
  const materials = (payload.materials?.length ? payload.materials : [payload.material].filter(Boolean)).map((material, index) => ({
    ...material,
    previewDataUrl: previews[index] || material.previewDataUrl || material.previewUrl || "",
  }));
  return { materials, previews };
}

function mergeAiImageSuitePayload(conversation, payload = {}) {
  const { materials } = aiImageMaterialsFromPayload(payload);
  const materialByPage = new Map((conversation.materials || [])
    .filter((material) => Number(material.suitePage || 0))
    .map((material) => [Number(material.suitePage), material]));
  materials.forEach((material) => {
    const page = Number(material.suitePage || 0);
    if (page) materialByPage.set(page, material);
  });
  if (materials.some((material) => Number(material.suitePage) === 1)) conversation.suiteStyleAnchorFile = null;
  conversation.materials = Array.from(materialByPage.values()).sort((a, b) => Number(a.suitePage) - Number(b.suitePage));
  conversation.previewDataUrls = conversation.materials.map((material) => material.previewDataUrl || material.previewUrl || "");
  conversation.skillId = payload.skillId || conversation.skillId;
  conversation.skillVersion = payload.skillVersion || conversation.skillVersion;
  conversation.lockLevel = payload.lockLevel || conversation.lockLevel;
  conversation.suiteKey = payload.suiteKey || conversation.suiteKey || "jp-landing-page-25";
  conversation.suiteCount = Number(payload.suiteCount || conversation.suiteCount || conversation.count || 0);
  conversation.suiteCountry = payload.suiteCountry || conversation.suiteCountry || "KR";
  const suiteConfig = aiImageSuiteConfig(conversation) || AI_IMAGE_SUITE_CONFIGS["jp-landing-page-25"];
  conversation.count = suiteConfig.count;
  conversation.suiteRunId = payload.suiteRunId || conversation.suiteRunId || "";
  conversation.suitePlanVersion = payload.suitePlanVersion || conversation.suitePlanVersion || suiteConfig.planVersion;
  conversation.suitePages = payload.suitePages || conversation.suitePages || [];
  return materials;
}

function setAiImageDirectorStage(conversation, stageIndex = 0, message = "") {
  const safeIndex = Math.max(0, Math.min(AI_IMAGE_DIRECTOR_STAGES.length - 1, Number(stageIndex || 0)));
  conversation.director = {
    ...(conversation.director || {}),
    source: conversation.director?.source || "pending",
    status: safeIndex >= AI_IMAGE_DIRECTOR_STAGES.length - 1 ? "ok" : "running",
    stage: AI_IMAGE_DIRECTOR_STAGES[safeIndex].key,
    stageIndex: safeIndex,
    message: message || AI_IMAGE_DIRECTOR_STAGES[safeIndex].label,
  };
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  renderAiImageSidebar();
  renderAiImageResults();
}

async function prepareAiImageSuitePlan(conversation, prompt, effectiveIntent) {
  // Always pull the administrator-owned shared runtime immediately before a
  // real director run. Long-lived browser sessions must not keep an older
  // model/enable state after another administrator changes the configuration.
  await loadAiImageConfig(true);
  const suiteConfig = aiImageSuiteConfig(conversation);
  if (!suiteConfig) throw new Error("不支持的套图类型");
  const formData = new FormData();
  formData.append("prompt", prompt);
  formData.append("suiteBrief", effectiveIntent);
  formData.append("size", conversation.size);
  formData.append("suiteKey", conversation.suiteKey);
  formData.append("suiteCount", String(suiteConfig.count));
  formData.append("suiteCountry", conversation.suiteCountry || "KR");
  formData.append("useDirector", "true");
  const directorReferences = (conversation.referenceImages || []).filter((reference) => reference.file).slice(0, 16);
  directorReferences.forEach((reference, index) => {
    formData.append(`reference${index}`, reference.file, reference.name || `reference-${index + 1}.jpg`);
  });
  formData.append("referenceBindings", JSON.stringify(directorReferences.map((reference, index) => ({
    index: index + 1,
    filename: reference.name || `reference-${index + 1}.jpg`,
    role: aiImageReferenceRoleKey(reference, index),
  }))));
  conversation.status = "planning";
  conversation.director = { source: "pending", status: "running", cacheHit: false, stage: "cache", stageIndex: 0, message: "正在读取产品分析缓存" };
  setAiImageDirectorStage(conversation, 0, "正在读取产品分析缓存");
  let stageIndex = 0;
  const stageTimer = window.setInterval(() => {
    if (stageIndex >= AI_IMAGE_DIRECTOR_STAGES.length - 2) return;
    stageIndex += 1;
    setAiImageDirectorStage(conversation, stageIndex, AI_IMAGE_DIRECTOR_STAGES[stageIndex].label);
  }, 4500);
  let payload;
  try {
    payload = await api("/api/sku-board/ai-image-suite-plan-upload", {
      method: "POST",
      body: formData,
      signal: aiImageGenerationAbortController?.signal,
    });
  } catch (error) {
    const status = Number(error?.status || 0);
    const canUseRules = error?.name !== "AbortError" && (!status || status >= 500);
    if (!canUseRules) {
      conversation.status = "error";
      conversation.director = {
        ...(conversation.director || {}),
        source: "rules",
        status: "warning",
        stage: "complete",
        stageIndex: AI_IMAGE_DIRECTOR_STAGES.length - 1,
        message: "导演策划失败",
        warning: error.message,
      };
      renderAiImageResults();
      throw error;
    }
    // A reverse proxy may end a long vision/director request with 524. Retry
    // only the deterministic local plan so image generation can continue.
    formData.set("useDirector", "false");
    payload = await api("/api/sku-board/ai-image-suite-plan-upload", {
      method: "POST",
      body: formData,
      signal: aiImageGenerationAbortController?.signal,
    });
    conversation.director = {
      ...(conversation.director || {}),
      source: "rules",
      status: "warning",
      stage: "complete",
      stageIndex: AI_IMAGE_DIRECTOR_STAGES.length - 1,
      message: "远端导演超时，已切换本地导演并继续生图",
      warning: error.message,
    };
  } finally {
    window.clearInterval(stageTimer);
  }
  if (!Array.isArray(payload.suitePages) || payload.suitePages.length !== suiteConfig.count) {
    conversation.status = "error";
    conversation.director = {
      ...(conversation.director || {}),
      status: "warning",
      stage: "complete",
      stageIndex: AI_IMAGE_DIRECTOR_STAGES.length - 1,
      message: "导演脚本校验未通过",
    };
    renderAiImageResults();
    throw new Error(`${suiteConfig.planTitle}生成不完整，请重试`);
  }
  conversation.suiteKey = payload.suiteKey || conversation.suiteKey;
  conversation.suiteCount = Number(payload.suiteCount || suiteConfig.count);
  conversation.count = conversation.suiteCount;
  conversation.suiteCountry = payload.suiteCountry || conversation.suiteCountry || "KR";
  conversation.suitePages = payload.suitePages;
  conversation.suitePlanVersion = payload.suitePlanVersion || suiteConfig.planVersion;
  conversation.suitePlanSignature = aiImageSuitePlanSignature(conversation, prompt, effectiveIntent);
  conversation.director = {
    ...(payload.director || { source: "rules", status: "unknown", message: "使用本地规则导演策划" }),
    stage: "complete",
    stageIndex: AI_IMAGE_DIRECTOR_STAGES.length - 1,
  };
  conversation.remoteSummary = {
    requested: suiteConfig.count,
    attempted: 0,
    succeeded: conversation.materials?.length || 0,
    running: 0,
    failed: 0,
    partial: true,
    message: `${suiteConfig.planTitle}已完成${conversation.director?.source === "model" ? ` · ${conversation.director.model}` : conversation.director?.source === "cache" ? " · 产品缓存" : " · 本地规则"}，准备生成第1${suiteConfig.unit}视觉母版`,
  };
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  renderAiImageSidebar();
  renderAiImageResults();
  return payload.suitePages;
}

async function aiImageSuiteStyleAnchorFile(conversation) {
  const heroIndex = (conversation.materials || []).findIndex((material) => Number(material.suitePage || 0) === 1);
  if (heroIndex < 0) return null;
  const heroMaterial = conversation.materials[heroIndex] || {};
  const source = heroMaterial.previewDataUrl || heroMaterial.previewUrl || conversation.previewDataUrls?.[heroIndex] || "";
  if (!source) return null;
  if (conversation.suiteStyleAnchorFile?.source === source && conversation.suiteStyleAnchorFile?.file) {
    return conversation.suiteStyleAnchorFile;
  }
  try {
    const response = await fetch(source);
    const blob = await response.blob();
    const mime = blob.type || heroMaterial.mime || "image/png";
    const extension = mime.includes("jpeg") ? "jpg" : mime.includes("webp") ? "webp" : "png";
    const prefix = aiImageSuiteConfig(conversation)?.anchorPrefix || "landing-page";
    const anchor = {
      source,
      name: `${prefix}-style-anchor.${extension}`,
      file: new File([blob], `${prefix}-style-anchor.${extension}`, { type: mime }),
    };
    conversation.suiteStyleAnchorFile = anchor;
    return anchor;
  } catch (error) {
    console.warn("Unable to prepare suite style anchor", error);
    return null;
  }
}

async function aiImageSuiteMaterialFile(conversation, material, fallbackIndex = 0) {
  const materialIndex = (conversation.materials || []).indexOf(material);
  const source = material.previewDataUrl || material.previewUrl || conversation.previewDataUrls?.[materialIndex >= 0 ? materialIndex : fallbackIndex] || "";
  if (!source) throw new Error(`第 ${material.suitePage || fallbackIndex + 1} 图缺少可质检预览`);
  const response = await fetch(source);
  if (!response.ok) throw new Error(`读取第 ${material.suitePage || fallbackIndex + 1} 图失败`);
  const blob = await response.blob();
  const mime = blob.type || material.mime || "image/png";
  const extension = mime.includes("jpeg") ? "jpg" : mime.includes("webp") ? "webp" : "png";
  return new File([blob], `suite-page-${String(material.suitePage || fallbackIndex + 1).padStart(2, "0")}.${extension}`, { type: mime });
}

function applyAiImageSuiteReviewResults(conversation, results = [], attempt = 1) {
  const resultByPage = new Map((results || []).map((result) => [Number(result.page), { ...result, attempt }]));
  conversation.materials = (conversation.materials || []).map((material) => {
    const reviewResult = resultByPage.get(Number(material.suitePage || 0));
    return reviewResult ? { ...material, aiReview: reviewResult } : material;
  });
  conversation.previewDataUrls = conversation.materials.map((material) => material.previewDataUrl || material.previewUrl || "");
}

function summarizeAiImageSuiteReview(conversation, overrides = {}) {
  const reviewedMaterials = (conversation.materials || []).filter((material) => material.aiReview);
  const passed = reviewedMaterials.filter((material) => material.aiReview?.passed).length;
  const failed = reviewedMaterials.filter((material) => material.aiReview && !material.aiReview.passed).length;
  conversation.review = {
    ...(conversation.review || {}),
    reviewed: reviewedMaterials.length,
    passed,
    failed,
    ...overrides,
  };
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  renderAiImageSidebar();
  renderAiImageResults();
  return conversation.review;
}

function aiImageSuiteUsesGeneratedStyleAnchor(conversation = {}) {
  return conversation.suiteKey !== "jp-landing-page-25";
}

async function reportAiImageQualityTelemetry(conversation, results = []) {
  const entries = (results || []).map((result) => {
    const material = (conversation.materials || []).find((item) => Number(item.suitePage) === Number(result.page));
    return {
      nodeId: material?.nodeId || material?.remoteNodeId || "",
      score: Number(result.score || 0),
      passed: Boolean(result.passed),
      suiteKey: conversation.suiteKey || "",
      page: Number(result.page || 0),
    };
  }).filter((entry) => entry.nodeId);
  if (!entries.length) return;
  try {
    await api("/api/sku-board/ai-image-quality-telemetry", {
      method: "POST",
      body: JSON.stringify({ entries }),
    });
  } catch (error) {
    console.warn("Unable to report image quality telemetry", error);
  }
}

async function reviewAiImageSuitePageNumbers(conversation, pageNumbers = [], attempt = 1) {
  const productReferences = aiImageSuiteGenerationReferences(conversation).slice(0, 12);
  if (!productReferences.length || !pageNumbers.length) return { reviewed: false, results: [], status: "skipped" };
  const allResults = [];
  let threshold = Number(state.aiImages.director?.reviewThreshold || 78);
  const batches = [];
  for (let cursor = 0; cursor < pageNumbers.length; cursor += AI_IMAGE_SUITE_REVIEW_BATCH_SIZE) {
    batches.push(pageNumbers.slice(cursor, cursor + AI_IMAGE_SUITE_REVIEW_BATCH_SIZE));
  }
  let batchCursor = 0;
  let stoppedPayload = null;
  summarizeAiImageSuiteReview(conversation, {
    status: "reviewing",
    currentPages: pageNumbers,
    message: `正在分批质检 ${pageNumbers.length} 张成图`,
    threshold,
  });
  const reviewWorker = async () => {
    while (batchCursor < batches.length && !stoppedPayload) {
      throwIfAiImageGenerationAborted();
      const batchPages = batches[batchCursor];
      batchCursor += 1;
    const batchMaterials = batchPages.map((page) => (conversation.materials || []).find((material) => Number(material.suitePage) === page)).filter(Boolean);
    if (batchMaterials.length !== batchPages.length) continue;
    const generatedFiles = await Promise.all(batchMaterials.map((material, index) => aiImageSuiteMaterialFile(conversation, material, index)));
    const formData = new FormData();
    formData.append("suiteKey", conversation.suiteKey);
    formData.append("suiteCount", String(aiImageSuiteCount(conversation)));
    formData.append("suiteCountry", conversation.suiteCountry || "KR");
    formData.append("size", conversation.size);
    formData.append("prompt", conversation.prompt || "");
    formData.append("suiteBrief", conversation.userIntent || "");
    formData.append("suitePlan", JSON.stringify(conversation.suitePages || []));
    formData.append("pageIndexes", JSON.stringify(batchPages));
    productReferences.forEach((reference, index) => {
      formData.append(`reference${index}`, reference.file, reference.name || `product-reference-${index + 1}.jpg`);
    });
    generatedFiles.forEach((file, index) => formData.append(`generated${index}`, file, file.name));
    const payload = await api("/api/sku-board/ai-image-suite-review", {
      method: "POST",
      body: formData,
      signal: aiImageGenerationAbortController?.signal,
    });
    threshold = Number(payload.threshold || threshold);
    if (!payload.reviewed) {
        stoppedPayload = payload;
        break;
    }
    applyAiImageSuiteReviewResults(conversation, payload.results || [], attempt);
    allResults.push(...(payload.results || []));
    summarizeAiImageSuiteReview(conversation, {
      status: "reviewing",
      model: payload.model || conversation.review?.model || "",
      latencyMs: Number(conversation.review?.latencyMs || 0) + Number(payload.latencyMs || 0),
      threshold,
      message: payload.message || "成图质检进行中",
    });
    }
  };
  await Promise.all(Array.from({ length: Math.min(AI_IMAGE_SUITE_REVIEW_WORKER_COUNT, batches.length) }, () => reviewWorker()));
  if (stoppedPayload) {
    summarizeAiImageSuiteReview(conversation, {
      status: stoppedPayload.status === "disabled" ? "disabled" : "warning",
      warning: stoppedPayload.warning || stoppedPayload.message || "AI 质检暂不可用",
      message: stoppedPayload.message || "AI 质检暂不可用",
      threshold,
    });
    return { reviewed: false, results: allResults, status: stoppedPayload.status || "warning", warning: stoppedPayload.warning || stoppedPayload.message || "" };
  }
  allResults.sort((a, b) => Number(a.page) - Number(b.page));
  await reportAiImageQualityTelemetry(conversation, allResults);
  return { reviewed: true, results: allResults, status: "ok", threshold };
}

const AI_IMAGE_SUITE_REFERENCE_ROLE_KEYWORDS = {
  detail: ["detail", "material", "texture", "construction", "macro", "spec", "\u7ec6\u8282", "\u6750\u8d28", "\u9762\u6599", "\u5de5\u827a", "\u53c2\u6570"],
  usage: ["usage", "use", "operation", "wearing", "action", "\u4f7f\u7528", "\u64cd\u4f5c", "\u7a7f\u7740", "\u4f69\u6234"],
  scene: ["scene", "lifestyle", "outdoor", "home", "office", "commute", "\u573a\u666f", "\u6237\u5916", "\u901a\u52e4", "\u5ba4\u5185", "\u5bb6\u5ead"],
  person: ["model", "person", "portrait", "doctor", "expert", "\u6a21\u7279", "\u4eba\u7269", "\u7528\u6237", "\u533b\u5e08", "\u4e13\u5bb6"],
  package: ["package", "accessory", "size", "dimension", "specification", "\u5305\u88c5", "\u914d\u4ef6", "\u5c3a\u5bf8", "\u89c4\u683c", "\u4ea7\u54c1\u4fe1\u606f"],
  layout: ["layout", "hero", "promotion", "review", "comparison", "\u6392\u7248", "\u9996\u56fe", "\u4fc3\u9500", "\u597d\u8bc4", "\u5bf9\u6bd4"],
  styleSet: ["visual system", "style", "campaign", "series", "\u7cfb\u5217", "\u98ce\u683c", "\u89c6\u89c9"],
};

function aiImageSuiteReferenceRoleScore(roleKey, pagePlanText = "") {
  return (AI_IMAGE_SUITE_REFERENCE_ROLE_KEYWORDS[roleKey] || [])
    .reduce((score, keyword) => score + (pagePlanText.includes(keyword) ? 1 : 0), 0);
}

function aiImageSuiteGenerationReferences(conversation = {}) {
  const references = normalizeAiImageReferenceRoles(
    (conversation.referenceImages || []).filter((reference) => reference.file),
  );
  if (conversation.suiteKey !== "jp-landing-page-25") return references;
  return references.filter((reference, index) => AI_IMAGE_JP_GENERATION_REFERENCE_ROLES.has(aiImageReferenceRoleKey(reference, index)));
}

function aiImageSuiteReferencesForPage(conversation = {}, page = 1) {
  const references = aiImageSuiteGenerationReferences(conversation);
  const japaneseLanding = conversation.suiteKey === "jp-landing-page-25";
  const products = references.filter((reference, index) => aiImageReferenceRoleKey(reference, index) === "product");
  const productSources = products.length ? products : references.slice(0, 1);
  const personSources = references.filter((reference, index) => aiImageReferenceRoleKey(reference, index) === "person");
  const pagePlan = conversation.suitePages?.[page - 1] || {};
  const hasHuman = pagePlan.hasHuman !== false;
  const selected = [];
  const add = (reference) => {
    if (reference && !selected.includes(reference)) selected.push(reference);
  };

  if (japaneseLanding && Number(page) === 24) {
    productSources.slice(0, AI_IMAGE_SUITE_HERO_REFERENCE_LIMIT).forEach(add);
    return selected;
  }
  if (japaneseLanding) {
    add(productSources[(Math.max(1, Number(page)) - 1) % Math.max(1, productSources.length)]);
    if (japaneseLanding && hasHuman) add(personSources[0]);
  } else if (references.length <= AI_IMAGE_SUITE_PAGE_REFERENCE_LIMIT) {
    return references;
  } else if (page === 1) {
    productSources.slice(0, 4).forEach(add);
    const supplements = references.filter((reference) => !selected.includes(reference));
    const preferred = supplements.find((reference) => ["styleSet", "layout"].includes(reference.role))
      || supplements[0];
    add(preferred);
    return selected.slice(0, AI_IMAGE_SUITE_HERO_REFERENCE_LIMIT);
  } else {
    add(productSources[(Math.max(1, Number(page)) - 1) % productSources.length]);
  }

  const pagePlanText = JSON.stringify(pagePlan).toLowerCase();
  const supplemental = references
    .map((reference, index) => ({ reference, role: reference.role, index }))
    .filter((item) => item.role !== "product" && !selected.includes(item.reference));
  supplemental.sort((left, right) => {
    const scoreDifference = aiImageSuiteReferenceRoleScore(right.role, pagePlanText)
      - aiImageSuiteReferenceRoleScore(left.role, pagePlanText);
    if (scoreDifference) return scoreDifference;
    const pageOffset = Math.max(0, Number(page) - 2);
    return ((left.index - pageOffset + references.length) % references.length)
      - ((right.index - pageOffset + references.length) % references.length);
  });
  supplemental
    .filter((item) => item.role !== "person" || hasHuman)
    .slice(0, Math.max(0, AI_IMAGE_SUITE_PAGE_REFERENCE_LIMIT - selected.length))
    .forEach((item) => add(item.reference));
  return selected.slice(0, AI_IMAGE_SUITE_PAGE_REFERENCE_LIMIT);
}

function buildAiImageSuiteFormData(conversation, prompt, effectiveIntent, page, runId, styleAnchor = null, reviewInstruction = "", editSource = null) {
  const formData = new FormData();
  const allReferences = (conversation.referenceImages || []).filter((reference) => reference.file);
  const references = editSource?.file ? [] : aiImageSuiteReferencesForPage(conversation, page);
  const requestPrompt = references.length && references.length < allReferences.length
    ? aiImageTemplatePrompt(conversation.templateKey || "main", aiImageProductBySku(conversation.productSku), true, {
      mode: conversation.mode,
      size: conversation.size,
      userIntent: effectiveIntent,
      lockLevel: conversation.lockLevel,
      country: conversation.suiteCountry || "KR",
      codHookType: conversation.codHookType || "hook",
      referenceRoles: references,
    })
    : prompt;
  formData.append("prompt", requestPrompt);
  formData.append("mode", "edit");
  formData.append("model", conversation.model);
  formData.append("size", conversation.size);
  formData.append("quality", conversation.quality);
  formData.append("generationProfile", aiImageGenerationProfile(conversation).key);
  formData.append("count", "1");
  formData.append("skillId", conversation.skillId);
  formData.append("skillVersion", conversation.skillVersion);
  formData.append("lockLevel", conversation.lockLevel);
  formData.append("suiteKey", conversation.suiteKey);
  formData.append("suiteCount", String(aiImageSuiteCount(conversation)));
  formData.append("suiteCountry", conversation.suiteCountry || "KR");
  formData.append("suiteRunId", runId);
  formData.append("suiteBrief", effectiveIntent);
  formData.append("suitePlan", JSON.stringify(conversation.suitePages || []));
  formData.append("suitePageIndexes", JSON.stringify([page]));
  if (page === 1 && aiImageGenerationProfile(conversation).key !== "fast" && !reviewInstruction && !editSource?.file) {
    formData.append("heroAB", "true");
  }
  if (reviewInstruction) formData.append("suiteReviewInstruction", reviewInstruction);
  const activeStyleAnchor = editSource?.file || !aiImageSuiteUsesGeneratedStyleAnchor(conversation) ? null : styleAnchor;
  const productReferenceIndexes = references
    .map((reference, index) => ({ reference, index: index + 1, role: aiImageReferenceRoleKey(reference, index) }))
    .filter((item) => item.role === "product")
    .map((item) => item.index);
  formData.append("productReferenceIndexes", JSON.stringify(productReferenceIndexes));
  formData.append("referenceBindings", JSON.stringify(aiImageReferenceBindings(references)));
  formData.append("referenceUploadCount", String(references.length + (activeStyleAnchor?.file && page !== 1 ? 1 : 0) + (editSource?.file ? 1 : 0)));
  references.forEach((reference, index) => {
    formData.append(`reference${index}`, reference.file, reference.name);
  });
  if (activeStyleAnchor?.file && page !== 1) {
    formData.append(`reference${references.length}`, activeStyleAnchor.file, activeStyleAnchor.name || "suite-style-anchor.png");
    formData.append("suiteStyleAnchor", "true");
  }
  if (editSource?.file) {
    const editReferenceIndex = references.length + (activeStyleAnchor?.file && page !== 1 ? 1 : 0);
    formData.append(`reference${editReferenceIndex}`, editSource.file, editSource.name || `suite-page-${page}-edit-source.png`);
    formData.append("suiteEditSource", "true");
  }
  return formData;
}

function updateAiImageSuiteProgress(conversation, progress, button) {
  const suiteConfig = aiImageSuiteConfig(conversation);
  const suiteCount = suiteConfig.count;
  const suiteUnit = suiteConfig.unit;
  const generationProfile = aiImageGenerationProfile(conversation);
  const pageEntries = Object.entries(progress.pageStates || {});
  const activePages = pageEntries.filter(([, status]) => ["running", "retrying", "reviewing", "quality-retry"].includes(status)).map(([page]) => Number(page));
  const retryingPages = pageEntries.filter(([, status]) => status === "retrying").map(([page]) => Number(page));
  const pendingPages = pageEntries.filter(([, status]) => status === "pending").map(([page]) => Number(page));
  const failedPages = pageEntries.filter(([, status]) => status === "failed").map(([page]) => Number(page));
  const attempted = pageEntries.filter(([, status]) => !["queued", "missing"].includes(status)).length;
  const succeeded = conversation.materials?.length || 0;
  const completedDurations = Object.entries(progress.pageMeta || {})
    .filter(([page, meta]) => progress.pageStates?.[page] === "success" && Number(meta?.elapsedMs || 0) > 0)
    .map(([, meta]) => Number(meta.elapsedMs));
  const averagePageMs = completedDurations.length
    ? Math.round(completedDurations.reduce((sum, value) => sum + value, 0) / completedDurations.length)
    : 0;
  const remainingPages = pageEntries.filter(([, status]) => ["queued", "running", "retrying", "quality-retry"].includes(status)).length;
  const workerCount = aiImageGenerationWorkerCount(conversation, remainingPages || 1);
  const etaMs = averagePageMs && remainingPages ? Math.ceil(remainingPages / workerCount) * averagePageMs : 0;
  const activeText = activePages.length ? `，正在生成第 ${activePages.join("、")} ${suiteUnit}` : "";
  const retryText = retryingPages.length ? `，自动重试第 ${retryingPages.join("、")} ${suiteUnit}` : "";
  const reviewText = conversation.review?.status === "reviewing" ? `，AI质检 ${Number(conversation.review.reviewed || 0)} 张` : "";
  const pendingText = pendingPages.length ? `，${pendingPages.length} ${suiteUnit}待远端恢复` : "";
  const failedText = failedPages.length ? `，${failedPages.length} ${suiteUnit}失败` : "";
  const etaText = etaMs ? `，预计还需 ${formatAiImageDuration(etaMs)}` : "";
  const cycleText = progress.autoRetryCycle ? `自动补齐第 ${progress.autoRetryCycle} 轮：` : "";
  const message = `${cycleText}已完成 ${succeeded}/${suiteCount}${activeText}${retryText}${reviewText}${pendingText}${failedText}${etaText}`;
  conversation.remoteSummary = {
    ...(conversation.remoteSummary || {}),
    requested: suiteCount,
    attempted,
    succeeded,
    running: activePages.length + pendingPages.length,
    failed: failedPages.length,
    partial: succeeded < suiteCount,
    timedOut: pendingPages.length > 0,
    pending: pendingPages.map((page) => ({ page, status: "running" })),
    errors: progress.errors || [],
    pageStates: { ...(progress.pageStates || {}) },
    pageMeta: { ...(progress.pageMeta || {}) },
    averagePageMs,
    etaMs,
    generationProfile: generationProfile.key,
    generationProfileLabel: generationProfile.label,
    message,
    suiteRunId: conversation.suiteRunId || "",
    reviewReviewed: Number(conversation.review?.reviewed || 0),
    reviewPassed: Number(conversation.review?.passed || 0),
    reviewFailed: Number(conversation.review?.failed || 0),
  };
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  if (button) {
    button.disabled = !aiImageGenerationAbortController;
    button.textContent = aiImageGenerationAbortController
      ? `取消生成 · ${succeeded}/${suiteCount}`
      : (progress.autoRetryCycle ? `补齐中 ${succeeded}/${suiteCount}` : `生成中 ${succeeded}/${suiteCount}`);
  }
  const status = $("#ai-image-status");
  if (status) status.textContent = message;
  renderAiImageSidebar();
  renderAiImageResults();
}

function aiImageGenerationAbortError() {
  const error = new Error("AI 生图已取消");
  error.name = "AbortError";
  return error;
}

function isAiImageGenerationAborted(error = null) {
  return Boolean(aiImageGenerationAbortController?.signal?.aborted || error?.name === "AbortError");
}

function throwIfAiImageGenerationAborted() {
  if (isAiImageGenerationAborted()) throw aiImageGenerationAbortError();
}

function waitForAiImageRetry(milliseconds, signal = aiImageGenerationAbortController?.signal) {
  if (signal?.aborted) return Promise.reject(aiImageGenerationAbortError());
  return new Promise((resolve, reject) => {
    const timer = window.setTimeout(() => {
      signal?.removeEventListener("abort", onAbort);
      resolve();
    }, milliseconds);
    const onAbort = () => {
      window.clearTimeout(timer);
      signal?.removeEventListener("abort", onAbort);
      reject(aiImageGenerationAbortError());
    };
    signal?.addEventListener("abort", onAbort, { once: true });
  });
}

async function waitForAiImageJob(payload, { signal, onPending } = {}) {
  let current = payload || {};
  let pollCount = 0;
  while (current?.pending && current.jobId) {
    if (signal?.aborted) throw aiImageGenerationAbortError();
    onPending?.(current.message || "远端生图任务处理中");
    await waitForAiImageRetry(Math.min(3000, 1100 + pollCount * 80), signal);
    current = await api(`/api/sku-board/ai-image-jobs/${encodeURIComponent(current.jobId)}`, { signal });
    pollCount += 1;
  }
  return current;
}

function cancelAiImageGeneration() {
  const controller = aiImageGenerationAbortController;
  const conversation = aiImageActiveConversation();
  if (!controller || !conversation || conversation.status !== "generating") return false;
  controller.abort();
  const suiteConfig = aiImageSuiteConfig(conversation);
  const completed = conversation.materials?.length || 0;
  const total = suiteConfig?.count || conversation.count || 1;
  conversation.status = "cancelled";
  conversation.error = "";
  conversation.remoteSummary = {
    ...(conversation.remoteSummary || {}),
    cancelled: true,
    partial: completed < total,
    running: 0,
    pageStates: Object.fromEntries(Object.entries(conversation.remoteSummary?.pageStates || {}).map(([page, status]) => [
      page,
      ["queued", "running", "retrying", "reviewing", "quality-retry", "pending"].includes(status) ? "cancelled" : status,
    ])),
    message: `已取消生成，已保留 ${completed}/${total} ${suiteConfig?.unit || "张"}`,
  };
  conversation.seconds = Math.max(0.1, (performance.now() - aiImageGenerationStartedAt) / 1000);
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  renderAiImageSidebar();
  renderAiImageForm();
  renderAiImageResults();
  showToast(conversation.remoteSummary.message);
  return true;
}

async function generateAiImageSuitePages({ conversation, prompt, effectiveIntent, targetPages, forcePages = [], button, startedAt, pageInstructions = new Map(), pageEditSources = new Map() }) {
  const suiteConfig = aiImageSuiteConfig(conversation);
  const suiteCount = suiteConfig.count;
  const suiteUnit = suiteConfig.unit;
  const generationProfile = aiImageGenerationProfile(conversation);
  const runId = conversation.suiteRunId || createAiImageSuiteRunId();
  conversation.suiteRunId = runId;
  const existingPages = new Set((conversation.materials || []).map((material) => Number(material.suitePage || 0)).filter(Boolean));
  const safeTargetPages = Array.from(new Set(targetPages.map(Number)))
    .filter((page) => page >= 1 && page <= suiteCount)
    .sort((a, b) => a - b);
  const targetSet = new Set(safeTargetPages);
  const forcedPageSet = new Set(forcePages.map(Number));
  const progress = {
    pageStates: Object.fromEntries(Array.from({ length: suiteCount }, (_, index) => {
      const page = index + 1;
      return [page, existingPages.has(page) ? "success" : targetSet.has(page) ? "queued" : "missing"];
    })),
    errors: [],
    retryablePages: new Set(),
    autoRetryCycle: 0,
    pageMeta: Object.fromEntries(Array.from({ length: suiteCount }, (_, index) => {
      const page = index + 1;
      const node = aiImageGenerationNodeForPage(page);
      return [page, {
        nodeId: node.id || "",
        nodeName: node.name || "自动调度",
        attempt: 0,
        startedAt: 0,
        finishedAt: 0,
        elapsedMs: 0,
        message: existingPages.has(page) ? "已有成图" : targetSet.has(page) ? "等待调度" : "未加入本次任务",
      }];
    })),
  };
  let styleAnchor = aiImageSuiteUsesGeneratedStyleAnchor(conversation)
    ? await aiImageSuiteStyleAnchorFile(conversation)
    : null;
  updateAiImageSuiteProgress(conversation, progress, button);

  const runPage = async (page, options = {}) => {
    throwIfAiImageGenerationAborted();
    const requestedInstruction = String(pageInstructions.get(page) || "").trim();
    const qualityInstruction = String(options.reviewInstruction || "").trim();
    const reviewInstruction = [requestedInstruction, qualityInstruction].filter(Boolean).join(" ").trim();
    const editSource = options.editSource || pageEditSources.get(page) || null;
    progress.retryablePages.delete(page);
    let completed = false;
    for (let attempt = 0; attempt <= generationProfile.maxRetries; attempt += 1) {
      throwIfAiImageGenerationAborted();
      const pageMeta = progress.pageMeta[page] || {};
      const predictedNode = aiImageGenerationNodeForPage(page);
      pageMeta.nodeId = pageMeta.nodeId || predictedNode.id || "";
      pageMeta.nodeName = pageMeta.nodeName || predictedNode.name || "自动调度";
      pageMeta.attempt = attempt + 1;
      pageMeta.startedAt = Date.now();
      pageMeta.finishedAt = 0;
      pageMeta.elapsedMs = 0;
      pageMeta.message = attempt ? `第 ${attempt + 1} 次生成` : reviewInstruction ? "按质检意见补图" : "已提交生成";
      progress.pageMeta[page] = pageMeta;
      progress.pageStates[page] = attempt ? "retrying" : reviewInstruction ? "quality-retry" : "running";
      updateAiImageSuiteProgress(conversation, progress, button);
      try {
        const submittedPayload = await api("/api/sku-board/ad-launch-ai-image-edit", {
          method: "POST",
          body: buildAiImageSuiteFormData(conversation, prompt, effectiveIntent, page, runId, page === 1 ? null : styleAnchor, reviewInstruction, editSource),
          signal: aiImageGenerationAbortController?.signal,
        });
        const payload = await waitForAiImageJob(submittedPayload, {
          signal: aiImageGenerationAbortController?.signal,
          onPending: (message) => {
            pageMeta.message = message;
            updateAiImageSuiteProgress(conversation, progress, button);
          },
        });
        const returnedMaterials = mergeAiImageSuitePayload(conversation, payload);
        const returnedMaterial = returnedMaterials.find((material) => Number(material.suitePage) === page);
        if (returnedMaterial) {
          pageMeta.nodeId = returnedMaterial.nodeId || pageMeta.nodeId;
          pageMeta.nodeName = returnedMaterial.nodeName || pageMeta.nodeName;
          pageMeta.finishedAt = Date.now();
          pageMeta.elapsedMs = Number(returnedMaterial.generationMs || 0) || Math.max(1, pageMeta.finishedAt - pageMeta.startedAt);
          pageMeta.message = "生成完成";
          progress.pageStates[page] = "success";
          completed = true;
          break;
        }
        const pending = Array.isArray(payload.suiteSummary?.pending) && payload.suiteSummary.pending.length > 0;
        const message = aiImageSuitePayloadError(payload) || payload.suiteSummary?.message || "远端没有返回图片";
        if (pending) {
          pageMeta.finishedAt = Date.now();
          pageMeta.elapsedMs = Math.max(1, pageMeta.finishedAt - pageMeta.startedAt);
          pageMeta.message = "远端仍在生成，可稍后恢复";
          progress.pageStates[page] = "pending";
          progress.retryablePages.add(page);
          completed = true;
          break;
        }
        const transient = aiImageSuiteTransientError(message);
        if (attempt < generationProfile.maxRetries && aiImageSuiteQuotaError(message)) {
          progress.pageStates[page] = "retrying";
          updateAiImageSuiteProgress(conversation, progress, button);
          await refreshAiImageAccountPool();
          await waitForAiImageRetry(2000);
          continue;
        }
        if (attempt < generationProfile.maxRetries && transient) {
          await waitForAiImageRetry(1500 * (attempt + 1));
          continue;
        }
        progress.pageStates[page] = "failed";
        pageMeta.finishedAt = Date.now();
        pageMeta.elapsedMs = Math.max(1, pageMeta.finishedAt - pageMeta.startedAt);
        pageMeta.message = message;
        progress.errors.push({ page, message });
        if (transient) progress.retryablePages.add(page);
        completed = true;
        break;
      } catch (error) {
        if (isAiImageGenerationAborted(error)) throw error;
        const message = error.message || "生成失败";
        const transient = aiImageSuiteTransientError(message);
        if (attempt < generationProfile.maxRetries && aiImageSuiteQuotaError(message)) {
          progress.pageStates[page] = "retrying";
          updateAiImageSuiteProgress(conversation, progress, button);
          await refreshAiImageAccountPool();
          await waitForAiImageRetry(2000);
          continue;
        }
        if (attempt < generationProfile.maxRetries && transient) {
          await waitForAiImageRetry(1500 * (attempt + 1));
          continue;
        }
        progress.pageStates[page] = "failed";
        pageMeta.finishedAt = Date.now();
        pageMeta.elapsedMs = Math.max(1, pageMeta.finishedAt - pageMeta.startedAt);
        pageMeta.message = message;
        progress.errors.push({ page, message });
        if (transient) progress.retryablePages.add(page);
        completed = true;
        break;
      }
    }
    if (!completed) {
      progress.pageStates[page] = "failed";
      const pageMeta = progress.pageMeta[page] || {};
      pageMeta.finishedAt = Date.now();
      pageMeta.elapsedMs = Math.max(1, pageMeta.finishedAt - Number(pageMeta.startedAt || pageMeta.finishedAt));
      pageMeta.message = "自动重试后仍未生成";
      progress.pageMeta[page] = pageMeta;
      progress.errors.push({ page, message: "自动重试后仍未生成" });
      progress.retryablePages.add(page);
    }
    updateAiImageSuiteProgress(conversation, progress, button);
    return progress.pageStates[page] === "success";
  };

  const runPageBatch = async (pages, reviewInstructions = new Map()) => {
    let cursor = 0;
    const worker = async () => {
      while (cursor < pages.length) {
        throwIfAiImageGenerationAborted();
        const page = pages[cursor];
        cursor += 1;
        await runPage(page, { reviewInstruction: reviewInstructions.get(page) || "", editSource: pageEditSources.get(page) || null });
      }
    };
    const workerCount = aiImageGenerationWorkerCount(conversation, pages.length);
    await Promise.all(Array.from({ length: workerCount }, () => worker()));
  };

  const runDirectedPageBatch = async (pages) => {
    throwIfAiImageGenerationAborted();
    const orderedPages = Array.from(new Set(pages)).sort((a, b) => a - b);
    const hasHero = () => (conversation.materials || []).some((material) => Number(material.suitePage) === 1);
    if (orderedPages.includes(1) && (!hasHero() || forcedPageSet.has(1))) {
      await runPage(1, { editSource: pageEditSources.get(1) || null });
    }
    styleAnchor = aiImageSuiteUsesGeneratedStyleAnchor(conversation)
      ? await aiImageSuiteStyleAnchorFile(conversation)
      : null;
    await runPageBatch(orderedPages.filter((page) => page !== 1));
  };

  await runDirectedPageBatch(safeTargetPages);
  for (let cycle = 1; cycle <= generationProfile.autoRetryCycles; cycle += 1) {
    throwIfAiImageGenerationAborted();
    const retryPages = Array.from(progress.retryablePages)
      .filter((page) => !(conversation.materials || []).some((material) => Number(material.suitePage) === page))
      .sort((a, b) => a - b);
    if (!retryPages.length) break;
    progress.retryablePages.clear();
    progress.errors = progress.errors.filter((item) => !retryPages.includes(Number(item.page)));
    retryPages.forEach((page) => { progress.pageStates[page] = "queued"; });
    progress.autoRetryCycle = cycle;
    updateAiImageSuiteProgress(conversation, progress, button);
    await waitForAiImageRetry(3000);
    await runDirectedPageBatch(retryPages);
  }
  progress.autoRetryCycle = 0;
  let qualityFailedPages = [];
  const reviewEnabled = state.aiImages.director?.reviewEnabled !== false && generationProfile.review !== "off";
  const keyReviewPages = new Set([1, 2, 3, Math.ceil(suiteCount / 2), suiteCount]);
  const reviewTargetPages = safeTargetPages.filter((page) =>
    (conversation.materials || []).some((material) => Number(material.suitePage) === page)
    && (generationProfile.review === "all" || keyReviewPages.has(page))
  );
  if (reviewEnabled && reviewTargetPages.length) {
    try {
      reviewTargetPages.forEach((page) => { progress.pageStates[page] = "reviewing"; });
      conversation.review = {
        ...(conversation.review || {}),
        status: "reviewing",
        reviewed: 0,
        passed: 0,
        failed: 0,
        retried: 0,
        warning: "",
      };
      updateAiImageSuiteProgress(conversation, progress, button);
      const firstReview = await reviewAiImageSuitePageNumbers(conversation, reviewTargetPages, 1);
      if (firstReview.reviewed) {
        firstReview.results.forEach((result) => {
          progress.pageStates[result.page] = result.passed ? "success" : "review-failed";
        });
        qualityFailedPages = firstReview.results.filter((result) => !result.passed).map((result) => Number(result.page));
        for (let reviewRetry = 1; reviewRetry <= AI_IMAGE_SUITE_REVIEW_MAX_RETRIES && qualityFailedPages.length; reviewRetry += 1) {
          const instructionMap = new Map(firstReview.results
            .filter((result) => qualityFailedPages.includes(Number(result.page)))
            .map((result) => [Number(result.page), result.retryInstruction || "修正本页质检问题后重新生成"]));
          qualityFailedPages.forEach((page) => { progress.pageStates[page] = "quality-retry"; });
          summarizeAiImageSuiteReview(conversation, {
            status: "reviewing",
            retried: Number(conversation.review?.retried || 0) + qualityFailedPages.length,
            message: `正在按质检意见补生成第 ${qualityFailedPages.join("、")} 图`,
          });
          updateAiImageSuiteProgress(conversation, progress, button);
          await runPageBatch(qualityFailedPages, instructionMap);
          const regeneratedPages = qualityFailedPages.filter((page) => progress.pageStates[page] === "success");
          if (regeneratedPages.length) {
            regeneratedPages.forEach((page) => { progress.pageStates[page] = "reviewing"; });
            updateAiImageSuiteProgress(conversation, progress, button);
            const retryReview = await reviewAiImageSuitePageNumbers(conversation, regeneratedPages, reviewRetry + 1);
            if (retryReview.reviewed) {
              retryReview.results.forEach((result) => {
                progress.pageStates[result.page] = result.passed ? "success" : "review-failed";
              });
            } else {
              const originalByPage = new Map(firstReview.results.map((result) => [Number(result.page), result]));
              const fallbackResults = regeneratedPages.map((page) => ({
                ...(originalByPage.get(page) || { page, score: 0, issues: [] }),
                page,
                passed: false,
                issues: [...(originalByPage.get(page)?.issues || []), "补图完成，但复检服务暂不可用"].slice(0, 6),
                retryInstruction: "",
              }));
              applyAiImageSuiteReviewResults(conversation, fallbackResults, reviewRetry + 1);
              regeneratedPages.forEach((page) => { progress.pageStates[page] = "review-failed"; });
            }
          }
          qualityFailedPages = (conversation.materials || [])
            .filter((material) => material.aiReview && !material.aiReview.passed)
            .map((material) => Number(material.suitePage))
            .filter((page) => reviewTargetPages.includes(page));
          Object.entries(progress.pageStates)
            .filter(([, status]) => status === "review-failed")
            .map(([page]) => Number(page))
            .forEach((page) => {
              if (reviewTargetPages.includes(page) && !qualityFailedPages.includes(page)) qualityFailedPages.push(page);
            });
        }
        qualityFailedPages.forEach((page) => { progress.pageStates[page] = "review-failed"; });
        summarizeAiImageSuiteReview(conversation, {
          status: "complete",
          message: qualityFailedPages.length
            ? `${qualityFailedPages.length} 张复检后仍需人工确认`
            : generationProfile.review === "all" ? "全套成图 AI 质检已通过" : "重点页面 AI 质检已通过",
        });
      }
    } catch (error) {
      summarizeAiImageSuiteReview(conversation, {
        status: "warning",
        warning: error.message,
        message: "AI 质检异常，已保留原成图且不会继续补图",
      });
    }
  }
  const missingPages = aiImageMissingSuitePages(conversation);
  const pendingPages = Object.entries(progress.pageStates).filter(([, status]) => status === "pending").map(([page]) => Number(page));
  const failedPages = Object.entries(progress.pageStates).filter(([, status]) => status === "failed").map(([page]) => Number(page));
  conversation.remoteSummary = {
    ...(conversation.remoteSummary || {}),
    succeeded: conversation.materials.length,
    running: pendingPages.length,
    failed: failedPages.length,
    partial: missingPages.length > 0,
    timedOut: pendingPages.length > 0,
    pending: pendingPages.map((page) => ({ page, status: "running" })),
    errors: progress.errors,
    pageStates: { ...progress.pageStates },
    reviewReviewed: Number(conversation.review?.reviewed || 0),
    reviewPassed: Number(conversation.review?.passed || 0),
    reviewFailed: Number(conversation.review?.failed || 0),
    message: missingPages.length
      ? `已显示 ${conversation.materials.length}/${suiteCount} ${suiteUnit}；仍缺第 ${missingPages.join("、")} ${suiteUnit}${pendingPages.length ? "，可稍后继续同步" : ""}`
      : qualityFailedPages.length
      ? `${suiteConfig.label}已全部生成；${qualityFailedPages.length} 张自动补图后仍需人工确认`
      : `${suiteConfig.label} ${suiteCount}${suiteUnit}已全部生成`,
  };
  conversation.status = missingPages.length
    ? (conversation.materials.length || pendingPages.length ? "partial" : "error")
    : qualityFailedPages.length
    ? "partial"
    : "done";
  conversation.error = conversation.status === "error" ? (progress.errors[0]?.message || `${suiteConfig.label}生成失败`) : "";
  conversation.seconds = Math.max(0.1, (performance.now() - startedAt) / 1000);
  conversation.title = aiImageConversationTitle(conversation);
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  $("#ai-image-status").textContent = conversation.remoteSummary.message;
  renderAiImageSidebar();
  renderAiImageForm();
  renderAiImageResults();
  loadAiImageHealth(true).catch(() => {});
  showToast(conversation.remoteSummary.message);
}

function validateAiImageModeInputs(conversation) {
  const mode = conversation.mode || "text";
  const references = conversation.referenceImages || [];
  const suiteConfig = aiImageSuiteConfig(conversation);
  if (conversation.templateKey === "virtualTryOn") {
    const hasProduct = references.some((reference, index) => reference.file && aiImageReferenceRoleKey(reference, index) === "product");
    const hasPerson = references.some((reference, index) => reference.file && aiImageReferenceRoleKey(reference, index) === "person");
    if (!hasProduct) throw new Error("模特换装/搭配需要先上传服装或商品图");
    if (!hasPerson) throw new Error("模特换装/搭配需要上传一张人物参考图");
  }
  if (suiteConfig && !references.length) throw new Error(`${suiteConfig.label}需要先上传 1 张清晰的产品主图`);
  if (mode === "edit" && !references.length) throw new Error("参考图翻新需要先上传至少 1 张商品图");
  if (mode === "compose" && references.length < 2) throw new Error("多图合成需要上传至少 2 张参考图");
  if (mode === "inpaint") {
    if (references.length !== 1) throw new Error("局部重绘需要且只需要 1 张原图");
    if (!conversation.maskImage?.file) throw new Error("局部重绘需要上传 PNG 蒙版");
  }
}

async function generateAiImage(event) {
  event?.preventDefault();
  if (!state.auth.user) {
    openLoginDialog();
    return;
  }
  if (aiImageGenerationAbortController && aiImageActiveConversation()?.status === "generating") {
    cancelAiImageGeneration();
    return;
  }
  if (!canUseAiImages()) {
    showToast("只有管理员、运营、选品或设计可以使用 AI 生图");
    return;
  }
  const conversation = ensureAiImageConversation();
  const skill = aiImageSkillConfig();
  const intent = $("#ai-image-intent").value.trim();
  let prompt = $("#ai-image-prompt").value.trim();
  if (!intent && !prompt) {
    showToast("请先填写创作需求");
    $("#ai-image-intent").focus();
    return;
  }
  conversation.productSku = $("#ai-image-product").value || "";
  conversation.mode = conversation.mode || state.aiImages.mode || "text";
  conversation.lockLevel = conversation.lockLevel || state.aiImages.lockLevel || skill.defaults?.lockLevel || "strict";
  const intentChangedNow = intent !== String(conversation.userIntent || "").trim();
  const promptChangedNow = prompt !== String(conversation.prompt || "").trim();
  const manualPromptWins = Boolean(
    prompt
    && !aiImagePromptIsStructured(prompt)
    && (promptChangedNow || (conversation.promptManuallyEdited && !intentChangedNow)),
  );
  const effectiveIntent = manualPromptWins
    ? prompt
    : intent || (!aiImagePromptIsStructured(prompt) ? prompt : conversation.userIntent || "");
  conversation.userIntent = effectiveIntent;
  const inferredSuiteKey = aiImageSuiteKeyFromIntent(effectiveIntent);
  if (!aiImageSuiteActive(conversation) && inferredSuiteKey) {
    const inferredSuiteConfig = aiImageSuiteConfig(inferredSuiteKey);
    conversation.suiteKey = inferredSuiteKey;
    conversation.suitePages = [];
    conversation.suitePlanVersion = "";
    conversation.suitePlanSignature = "";
    conversation.suiteStyleAnchorFile = null;
    conversation.templateKey = inferredSuiteConfig.templateKey;
    conversation.suiteCount = inferredSuiteConfig.count;
    conversation.mode = "edit";
    conversation.lockLevel = "exact";
  }
  if (conversation.templateKey === "codHook") {
    conversation.mode = (conversation.referenceImages || []).some((reference) => reference.file) ? "edit" : "text";
    conversation.lockLevel = conversation.mode === "edit" ? "exact" : "strict";
  }
  if (conversation.templateKey === "virtualTryOn") {
    conversation.mode = "compose";
    conversation.lockLevel = "exact";
    conversation.count = 1;
  }
  const suiteConfig = aiImageSuiteConfig(conversation);
  if (aiImageCodCountryActive(conversation)) {
    conversation.suiteCountry = $("#ai-image-country")?.value || conversation.suiteCountry || state.aiImages.suiteCountry || "KR";
  }
  conversation.model = $("#ai-image-model").value || "gpt-image-2";
  conversation.size = suiteConfig?.size || state.aiImages.size || $("#ai-image-size").value || "1024x1024";
  conversation.quality = suiteConfig
    ? (aiImageGenerationProfile(conversation).quality || "high")
    : $("#ai-image-quality")?.value || state.aiImages.quality || "auto";
  if (suiteConfig) conversation.suiteCount = suiteConfig.count;
  conversation.count = conversation.templateKey === "virtualTryOn"
    ? 1
    : suiteConfig?.count || Number(state.aiImages.count || conversation.count || 1);
  const needsCompile = !aiImagePromptIsStructured(prompt)
    || !prompt.includes("[User-prompt fidelity lock — highest content priority]")
    || conversation.compiledIntent !== effectiveIntent
    || conversation.skillVersion !== (skill.version || "内置")
    || conversation.templateKey === "codHook"
    || aiImageSuiteActive(conversation);
  if (needsCompile) {
    const product = aiImageProductBySku(conversation.productSku);
    prompt = aiImageTemplatePrompt(conversation.templateKey || "main", product, Boolean(conversation.referenceImages?.length), {
      mode: conversation.mode,
      size: conversation.size,
      userIntent: effectiveIntent,
      lockLevel: conversation.lockLevel,
      country: conversation.suiteCountry || "KR",
      codHookType: conversation.codHookType || "hook",
      referenceRoles: conversation.referenceImages || [],
    });
  }
  conversation.prompt = prompt;
  conversation.compiledIntent = effectiveIntent;
  conversation.promptManuallyEdited = false;
  conversation.skillId = skill.id || "gpt-image2-sosove";
  conversation.skillVersion = skill.version || "内置";
  try {
    validateAiImageModeInputs(conversation);
  } catch (error) {
    showToast(error.message);
    renderAiImageForm();
    return;
  }
  const retryPageIndexes = aiImageSuiteActive(conversation) && Array.isArray(conversation.retryPageIndexes)
    ? [...conversation.retryPageIndexes]
    : [];
  const retryMissingPages = retryPageIndexes.length > 0;
  const existingMaterials = retryMissingPages ? [...(conversation.materials || [])] : [];
  const button = $("#ai-image-generate-btn");
  const original = button.textContent;
  const planSignature = suiteConfig ? aiImageSuitePlanSignature(conversation, prompt, effectiveIntent) : "";
  let planCurrent = Boolean(
    suiteConfig
    && conversation.suitePages?.length === suiteConfig.count
    && conversation.suitePlanSignature === planSignature
    && conversation.suitePlanVersion === suiteConfig.planVersion,
  );
  let plannedThisRun = false;
  if (suiteConfig && !retryMissingPages && !planCurrent) {
    button.disabled = true;
    button.textContent = `策划${suiteConfig.count}${suiteConfig.unit}...`;
    $("#ai-image-status").textContent = `正在生成${suiteConfig.planTitle}，不消耗生图额度`;
    try {
      await prepareAiImageSuitePlan(conversation, prompt, effectiveIntent);
    } catch (error) {
      if (isAiImageGenerationAborted(error)) {
        conversation.status = "cancelled";
        conversation.error = "";
        conversation.remoteSummary = {
          ...(conversation.remoteSummary || {}),
          cancelled: true,
          message: "已取消导演规划",
        };
        syncAiImageStateFromConversation(conversation);
        renderAiImageSidebar();
        renderAiImageForm();
        renderAiImageResults();
        return;
      }
      button.disabled = false;
      button.textContent = original;
      $("#ai-image-status").textContent = "套图策划失败";
      showToast(error.message);
      return;
    }
    plannedThisRun = true;
    planCurrent = true;
  }
  if (suiteConfig && !retryMissingPages && aiImageDirectorMode(conversation) === "review") {
    const approvalReady = planCurrent && conversation.status === "planned" && !plannedThisRun;
    if (!approvalReady) {
      conversation.status = "planned";
      conversation.error = "";
      conversation.remoteSummary = {
        ...(conversation.remoteSummary || {}),
        message: `${suiteConfig.planTitle}已完成，等待确认后开始生图`,
      };
      conversation.updatedAt = new Date().toISOString();
      syncAiImageStateFromConversation(conversation);
      renderAiImageSidebar();
      renderAiImageForm();
      renderAiImageResults();
      button.disabled = false;
      $("#ai-image-status").textContent = "导演方案已就绪，确认后开始生图";
      showToast("导演方案已完成，请确认事实锁定与分镜");
      return;
    }
  }
  if (aiImageSuiteActive(conversation) && !retryMissingPages) {
    conversation.suiteRunId = createAiImageSuiteRunId();
    conversation.suiteStyleAnchorFile = null;
  }
  aiImageGenerationAbortController = new AbortController();
  aiImageGenerationStartedAt = performance.now();
  conversation.status = "generating";
  conversation.error = "";
  if (!retryMissingPages) {
    conversation.materials = [];
    conversation.previewDataUrls = [];
    conversation.review = {};
  }
  conversation.updatedAt = new Date().toISOString();
  syncAiImageStateFromConversation(conversation);
  renderAiImageSidebar();
  renderAiImageForm();
  renderAiImageResults();
  button.disabled = false;
  button.textContent = retryMissingPages ? `补图中 ${retryPageIndexes.length}${suiteConfig?.unit || "张"}...` : suiteConfig ? "整套生成中..." : "生成中...";
  if (aiImageGenerationAbortController) button.textContent = "取消生成";
  $("#ai-image-status").textContent = retryMissingPages
    ? `正在补生成第 ${retryPageIndexes.join("、")} ${suiteConfig.unit}`
    : suiteConfig
    ? `正在通过远端账号池分批生成 ${suiteConfig.label}（${suiteConfig.count}${suiteConfig.unit}）`
    : `正在调用 ${aiImageProviderLabel(conversation.model || "gpt-image-2")}`;
  const startedAt = performance.now();
  try {
    const references = conversation.referenceImages || [];
    const productReferenceIndexes = references
      .map((reference, index) => ({ reference, index: index + 1, role: aiImageReferenceRoleKey(reference, index) }))
      .filter((item) => item.reference?.file && item.role === "product")
      .map((item) => item.index);
    const mode = conversation.mode || "text";
    if (suiteConfig) {
      await generateAiImageSuitePages({
        conversation,
        prompt,
        effectiveIntent,
        targetPages: retryMissingPages ? retryPageIndexes : Array.from({ length: suiteConfig.count }, (_, index) => index + 1),
        button,
        startedAt,
      });
      return;
    }
    let payload;
    if (mode !== "text") {
      const formData = new FormData();
      formData.append("prompt", prompt);
      formData.append("mode", mode);
      formData.append("model", conversation.model);
      formData.append("size", conversation.size);
      formData.append("quality", conversation.quality);
      formData.append("count", String(conversation.count));
      formData.append("skillId", conversation.skillId);
      formData.append("skillVersion", conversation.skillVersion);
      formData.append("lockLevel", conversation.lockLevel);
      formData.append("templateKey", conversation.templateKey || "");
      formData.append("useDirector", state.aiImages.director?.enabled && state.aiImages.director?.openImagePromptsEnabled !== false ? "true" : "false");
      formData.append("codHookType", conversation.codHookType || "hook");
      formData.append("suiteCountry", conversation.suiteCountry || "KR");
      formData.append("productReferenceIndexes", JSON.stringify(productReferenceIndexes));
      formData.append("referenceBindings", JSON.stringify(aiImageReferenceBindings(references)));
      formData.append("suiteKey", conversation.suiteKey || "");
      formData.append("suiteBrief", effectiveIntent);
      if (retryMissingPages) formData.append("suitePageIndexes", JSON.stringify(retryPageIndexes));
      references.forEach((reference, index) => {
        formData.append(`reference${index}`, reference.file, reference.name);
      });
      if (mode === "inpaint" && conversation.maskImage?.file) {
        formData.append("mask", conversation.maskImage.file, conversation.maskImage.name || "mask.png");
      }
      payload = await api("/api/sku-board/ad-launch-ai-image-edit", {
        method: "POST",
        body: formData,
        signal: aiImageGenerationAbortController?.signal,
      });
    } else {
      payload = await api("/api/sku-board/ad-launch-ai-image", {
        method: "POST",
        signal: aiImageGenerationAbortController?.signal,
        body: JSON.stringify({
          prompt,
          mode,
          model: conversation.model,
          size: conversation.size,
          quality: conversation.quality,
          count: conversation.count,
          skillId: conversation.skillId,
          skillVersion: conversation.skillVersion,
          lockLevel: conversation.lockLevel,
          templateKey: conversation.templateKey || "",
          useDirector: Boolean(state.aiImages.director?.enabled && state.aiImages.director?.openImagePromptsEnabled !== false),
          codHookType: conversation.codHookType || "hook",
          suiteCountry: conversation.suiteCountry || "KR",
          suiteKey: conversation.suiteKey || "",
          suiteBrief: effectiveIntent,
        }),
      });
    }
    payload = await waitForAiImageJob(payload, {
      signal: aiImageGenerationAbortController?.signal,
      onPending: (message) => {
        $("#ai-image-status").textContent = message;
      },
    });
    const previews = payload.previewDataUrls?.length ? payload.previewDataUrls : [payload.previewDataUrl].filter(Boolean);
    const materials = (payload.materials?.length ? payload.materials : [payload.material].filter(Boolean)).map((material, index) => ({
      ...material,
      previewDataUrl: previews[index] || material.previewDataUrl || material.previewUrl || "",
    }));
    if (retryMissingPages) {
      const materialByPage = new Map(existingMaterials.map((material) => [Number(material.suitePage || 0), material]));
      materials.forEach((material) => materialByPage.set(Number(material.suitePage || 0), material));
      conversation.materials = Array.from(materialByPage.values()).filter((material) => material.suitePage).sort((a, b) => Number(a.suitePage) - Number(b.suitePage));
      conversation.previewDataUrls = conversation.materials.map((material) => material.previewDataUrl || material.previewUrl || "");
    } else {
      conversation.materials = materials;
      conversation.previewDataUrls = previews;
    }
    conversation.skillId = payload.skillId || conversation.skillId;
    conversation.skillVersion = payload.skillVersion || conversation.skillVersion;
    conversation.lockLevel = payload.lockLevel || conversation.lockLevel;
    conversation.suiteKey = payload.suiteKey || conversation.suiteKey || "";
    conversation.suitePages = payload.suitePages || conversation.suitePages || [];
    conversation.remoteSummary = payload.suiteSummary || {};
    if (aiImageSuiteActive(conversation)) {
      const activeSuiteConfig = aiImageSuiteConfig(conversation);
      const missingAfterGeneration = aiImageMissingSuitePages(conversation);
      conversation.remoteSummary.succeeded = conversation.materials.length;
      conversation.remoteSummary.partial = missingAfterGeneration.length > 0;
      conversation.remoteSummary.message = missingAfterGeneration.length
        ? `已显示 ${conversation.materials.length}/${activeSuiteConfig.count} ${activeSuiteConfig.unit}，仍缺第 ${missingAfterGeneration.join("、")} ${activeSuiteConfig.unit}`
        : `${activeSuiteConfig.label} ${activeSuiteConfig.count}${activeSuiteConfig.unit}已全部生成`;
    }
    conversation.status = conversation.remoteSummary.partial ? "partial" : "done";
    conversation.seconds = Math.max(0.1, (performance.now() - startedAt) / 1000);
    conversation.title = aiImageConversationTitle(conversation);
    conversation.updatedAt = new Date().toISOString();
    syncAiImageStateFromConversation(conversation);
    const resultUnit = aiImageSuiteUnit(conversation);
    $("#ai-image-status").textContent = `已生成 ${conversation.materials.length} ${resultUnit}`;
    renderAiImageSidebar();
    renderAiImageForm();
    renderAiImageResults();
    showToast(aiImageSuiteActive(conversation)
      ? (conversation.remoteSummary.message || `${aiImageSuiteConfig(conversation).label}已生成 ${materials.length} ${resultUnit}`)
      : `AI 图片已生成 ${materials.length} 张`);
  } catch (error) {
    if (isAiImageGenerationAborted(error)) {
      conversation.status = "cancelled";
      conversation.error = "";
      const suite = aiImageSuiteConfig(conversation);
      const completed = conversation.materials?.length || 0;
      const total = suite?.count || conversation.count || 1;
      conversation.remoteSummary = {
        ...(conversation.remoteSummary || {}),
        cancelled: true,
        partial: completed < total,
        running: 0,
        pageStates: Object.fromEntries(Object.entries(conversation.remoteSummary?.pageStates || {}).map(([page, status]) => [
          page,
          ["queued", "running", "retrying", "reviewing", "quality-retry", "pending"].includes(status) ? "cancelled" : status,
        ])),
        message: `已取消生成，已保留 ${completed}/${total} ${suite?.unit || "张"}`,
      };
      conversation.seconds = Math.max(0.1, (performance.now() - startedAt) / 1000);
      conversation.updatedAt = new Date().toISOString();
      syncAiImageStateFromConversation(conversation);
      renderAiImageSidebar();
      renderAiImageForm();
      renderAiImageResults();
      return;
    }
    if (aiImageSuiteActive(conversation)) {
      try {
        const recovered = await recoverRecentAiImageSuite(true, conversation.suiteRunId || "");
        const recoveredCount = Number(recovered?.returnedCount || 0);
        const runningCount = Number(recovered?.suiteSummary?.running || 0);
        if (recoveredCount || runningCount) {
          const activeSuiteConfig = aiImageSuiteConfig(conversation);
          showToast(recovered?.suiteSummary?.message || `已恢复 ${recoveredCount}/${activeSuiteConfig.count} ${activeSuiteConfig.unit}`);
          return;
        }
      } catch (recoveryError) {
        console.warn("AI suite recovery failed", recoveryError);
      }
    }
    conversation.status = "error";
    conversation.error = error.message;
    conversation.updatedAt = new Date().toISOString();
    syncAiImageStateFromConversation(conversation);
    $("#ai-image-status").textContent = "生成失败";
    renderAiImageSidebar();
    renderAiImageForm();
    renderAiImageResults();
    showToast(error.message);
  } finally {
    conversation.retryPageIndexes = [];
    aiImageGenerationAbortController = null;
    aiImageGenerationStartedAt = 0;
    button.disabled = false;
    button.textContent = original;
    renderAiImageForm();
  }
}

async function sendAiImageToAdLaunch(index = 0) {
  const conversation = aiImageActiveConversation();
  const material = conversation?.materials?.[Number(index)] || state.aiImages.material;
  const previewDataUrl = conversation?.previewDataUrls?.[Number(index)] || material?.previewDataUrl || material?.previewUrl || "";
  if (!material) {
    showToast("请先生成一张图片");
    return;
  }
  let launchMaterial = material;
  if (!material.path) {
    if (!previewDataUrl) throw new Error("这张图片缺少可读取的远程地址");
    const response = await fetch(previewDataUrl);
    if (!response.ok) throw new Error(`读取远程图片失败（HTTP ${response.status}）`);
    const blob = await response.blob();
    const mime = blob.type || material.mime || "image/png";
    if (!mime.startsWith("image/")) throw new Error("远程地址没有返回有效图片");
    const extension = mime.includes("jpeg") ? "jpg" : mime.includes("webp") ? "webp" : "png";
    const filename = material.name || `ai-image-${Number(index) + 1}.${extension}`;
    const formData = new FormData();
    formData.append("file", blob, filename);
    const payload = await api("/api/sku-board/ad-launch-materials", {
      method: "POST",
      body: formData,
    });
    launchMaterial = payload.material;
  }
  state.adLaunches.material = { ...launchMaterial, previewDataUrl };
  state.adLaunches.materialMode = "single_image";
  state.adLaunches.step = 2;
  setActiveView("adLaunches");
  window.setTimeout(() => {
    if ($("#ad-launch-product") && (conversation?.productSku || state.aiImages.productSku)) {
      $("#ad-launch-product").value = conversation?.productSku || state.aiImages.productSku;
      prefillAdLaunchFromProduct();
    }
    setAdLaunchMaterialMode("single_image");
    setAdLaunchStep(2);
  }, 0);
  showToast("已送到素材投放");
}

function previewAiImage(index = 0) {
  const conversation = aiImageActiveConversation();
  const material = conversation?.materials?.[Number(index)];
  const preview = conversation?.previewDataUrls?.[Number(index)] || material?.previewDataUrl || material?.previewUrl || "";
  if (!preview) {
    showToast("这张图片没有可预览的数据");
    return;
  }
  openImagePreview(preview, material?.name || `AI 图片 ${Number(index) + 1}`);
}

async function downloadAiImage(index = 0) {
  const conversation = aiImageActiveConversation();
  const material = conversation?.materials?.[Number(index)];
  const preview = conversation?.previewDataUrls?.[Number(index)] || material?.previewDataUrl || material?.previewUrl || "";
  if (!preview) {
    showToast("这张图片没有可下载的预览数据");
    return;
  }
  const response = await fetch(preview);
  if (!response.ok) throw new Error(`下载图片失败（HTTP ${response.status}）`);
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  try {
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.download = material?.name || `ai-image-${Number(index) + 1}.png`;
    anchor.rel = "noopener";
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    showToast("图片已开始下载");
  } finally {
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
  }
}

function setAiImageConversation(id) {
  const conversation = state.aiImages.conversations.find((item) => item.id === id);
  if (!conversation) return;
  syncAiImageStateFromConversation(conversation);
  renderAiImageSidebar();
  renderAiImageForm();
  renderAiImageResults();
}

function aiImageDeleteDescriptor(material = {}) {
  return {
    id: material.id || "",
    storage: material.storage || "",
    remoteUrl: material.remoteUrl || material.previewUrl || "",
    remotePath: material.remotePath || "",
    remoteNodeId: material.remoteNodeId || "",
    deleteToken: material.deleteToken || "",
  };
}

async function deleteAiImageMaterials(materials = []) {
  const deletable = materials.filter((material) => /^AI-[A-F0-9]{10}$/.test(String(material?.id || "").toUpperCase()));
  if (!deletable.length) return { deletedIds: [], failedIds: [], errors: [] };
  const combined = { deletedIds: [], failedIds: [], errors: [] };
  for (let offset = 0; offset < deletable.length; offset += 100) {
    const payload = await api("/api/sku-board/ai-image-outputs", {
      method: "DELETE",
      body: JSON.stringify({ materials: deletable.slice(offset, offset + 100).map(aiImageDeleteDescriptor) }),
    });
    combined.deletedIds.push(...(payload.deletedIds || []));
    combined.failedIds.push(...(payload.failedIds || []));
    combined.errors.push(...(payload.errors || []));
  }
  return combined;
}

function removeAiImageMaterialsFromConversation(conversation, deletedIds = []) {
  const ids = new Set(deletedIds.map((value) => String(value || "").toUpperCase()));
  conversation.materials = (conversation.materials || []).filter((material) => !ids.has(String(material.id || "").toUpperCase()));
  conversation.previewDataUrls = conversation.materials.map((material) => material.previewDataUrl || material.previewUrl || "");
  conversation.updatedAt = new Date().toISOString();
}

async function deleteAiImageMaterial(index = 0) {
  const conversation = aiImageActiveConversation();
  const material = conversation?.materials?.[Number(index)];
  if (!conversation || !material) return;
  if (!window.confirm(`确定删除这张图片吗？\n${material.suiteTitle || material.name || material.id}\n远端 ${material.provider === "acore" ? "Giikin Acore" : "ChatGPT2API"} 中的原图也会删除。`)) return;
  const result = await deleteAiImageMaterials([material]);
  if (!result.deletedIds.length) throw new Error(result.errors[0]?.message || "图片删除失败");
  removeAiImageMaterialsFromConversation(conversation, result.deletedIds);
  syncAiImageStateFromConversation(conversation);
  renderAiImageSidebar();
  renderAiImageResults();
  showToast("图片及远端文件已删除");
}

async function deleteAiImageConversation(id) {
  const index = state.aiImages.conversations.findIndex((item) => item.id === id);
  if (index < 0) return;
  const conversation = state.aiImages.conversations[index];
  const materialCount = (conversation.materials || []).filter((material) => /^AI-[A-F0-9]{10}$/.test(String(material?.id || "").toUpperCase())).length;
  if (!window.confirm(`确定删除这个生图任务吗？${materialCount ? `\n将同时删除 ${materialCount} 张远端生成图片。` : ""}`)) return;
  if (materialCount) {
    const result = await deleteAiImageMaterials(conversation.materials || []);
    if (result.failedIds.length) {
      removeAiImageMaterialsFromConversation(conversation, result.deletedIds);
      syncAiImageStateFromConversation(conversation);
      renderAiImageSidebar();
      renderAiImageResults();
      throw new Error(`已删除 ${result.deletedIds.length} 张，仍有 ${result.failedIds.length} 张删除失败：${result.errors[0]?.message || "远端服务异常"}`);
    }
  }
  revokeAiImageReferenceUrls(conversation);
  state.aiImages.conversations.splice(index, 1);
  if (state.aiImages.activeId === id) {
    state.aiImages.activeId = state.aiImages.conversations[0]?.id || "";
  }
  ensureAiImageConversation();
  syncAiImageStateFromConversation(aiImageActiveConversation());
  renderAiImageSidebar();
  renderAiImageForm();
  renderAiImageResults();
}

async function clearAiImageConversations() {
  if (!window.confirm("确定清空 AI 生图记录吗？所有任务对应的远端生成图片也会删除。")) return;
  const materials = state.aiImages.conversations.flatMap((conversation) => conversation.materials || []);
  const result = await deleteAiImageMaterials(materials);
  if (result.failedIds.length) {
    state.aiImages.conversations.forEach((conversation) => removeAiImageMaterialsFromConversation(conversation, result.deletedIds));
    syncAiImageStateFromConversation(aiImageActiveConversation());
    renderAiImagePanel();
    throw new Error(`已删除 ${result.deletedIds.length} 张，仍有 ${result.failedIds.length} 张删除失败：${result.errors[0]?.message || "远端服务异常"}`);
  }
  state.aiImages.conversations.forEach(revokeAiImageReferenceUrls);
  state.aiImages.conversations = [];
  state.aiImages.activeId = "";
  ensureAiImageConversation({ prompt: "", userIntent: "", mode: "text", count: 1, suiteKey: "", suiteCountry: "KR", suitePages: [], referenceImages: [], maskImage: null });
  renderAiImagePanel();
  showToast("生图记录和远端图片已清空");
}

function updateAiImageConversation(updates = {}) {
  const conversation = ensureAiImageConversation();
  Object.assign(conversation, updates, { updatedAt: new Date().toISOString() });
  conversation.title = aiImageConversationTitle(conversation);
  syncAiImageStateFromConversation(conversation);
  renderAiImageForm();
  renderAiImageSidebar();
}

function renderAdLaunchForm() {
  const form = $("#ad-launch-form");
  if (!form) return;
  const options = adLaunchOptions();
  const canCreate = canManageFacebookAds();
  const currentProduct = $("#ad-launch-product")?.value || "";
  const currentAccount = $("#ad-launch-account")?.value || "";
  const currentCampaign = $("#ad-launch-campaign")?.value || "";
  const currentAdset = $("#ad-launch-adset")?.value || "";
  $("#ad-launch-product").innerHTML = productOptions(options.products || [], currentProduct);
  $("#ad-launch-cta").innerHTML = mapOptions(options.ctas || { SHOP_NOW: "Shop Now" }, $("#ad-launch-cta")?.value || "SHOP_NOW");
  $("#ad-launch-objective").innerHTML = mapOptions(options.objectives || { OUTCOME_TRAFFIC: "Traffic" }, $("#ad-launch-objective")?.value || "OUTCOME_TRAFFIC");
  $("#ad-launch-optimization").innerHTML = mapOptions(options.optimizations || { LINK_CLICKS: "Link Clicks" }, $("#ad-launch-optimization")?.value || "LINK_CLICKS");
  $("#ad-launch-conversion-event").innerHTML = mapOptions(options.conversionEvents || { PURCHASE: "Purchase" }, $("#ad-launch-conversion-event")?.value || "PURCHASE");
  $("#ad-launch-ai-model").innerHTML = (options.aiImage?.models || ["gpt-image-2", "codex-gpt-image-2"])
    .map((model) => `<option value="${esc(model)}" ${model === ($("#ad-launch-ai-model")?.value || options.aiImage?.model || "gpt-image-2") ? "selected" : ""}>${esc(aiImageModelLabel(model))}</option>`)
    .join("");
  $("#ad-launch-ai-size").innerHTML = (options.aiImage?.sizes || ["1024x1024", "1024x1536", "1536x1024"])
    .map((size) => `<option value="${esc(size)}" ${size === ($("#ad-launch-ai-size")?.value || "1024x1024") ? "selected" : ""}>${esc(size)}</option>`)
    .join("");
  const adLaunchProvider = aiImageProviderLabel($("#ad-launch-ai-model")?.value || options.aiImage?.model || "gpt-image-2");
  $("#ad-launch-ai-status").textContent = options.aiImage?.enabled
    ? `已连接 ${adLaunchProvider}${Number(options.aiImage?.nodeCount || 1) > 1 ? ` · ${options.aiImage.nodeCount} 个服务节点` : ""}`
    : "未配置生图服务";
  $("#ad-launch-countries").value = $("#ad-launch-countries").value || options.defaults?.country || "JP";
  $("#ad-launch-daily-budget").value = $("#ad-launch-daily-budget").value || options.defaults?.dailyBudget || 10;
  $("#ad-launch-naming-rule").value = $("#ad-launch-naming-rule").value || "{sku}-{country}-{date}-{material}";
  renderAdLaunchTargetSelects(currentAccount, currentCampaign, currentAdset);
  renderAdLaunchIdentitySelects(
    $("#ad-launch-page-id")?.value || options.defaults?.pageId || "",
    $("#ad-launch-ig-id")?.value || options.defaults?.instagramActorId || "",
  );
  setAdLaunchMaterialMode(state.adLaunches.materialMode || "single_image");
  form.classList.toggle("is-disabled", !canCreate);
  form.querySelectorAll("input, select, textarea, button").forEach((field) => {
    field.disabled = !canCreate;
  });
  if (canCreate) updateAdLaunchModeFields();
  updateAdLaunchStepUI();
}

function renderAdLaunchTargetSelects(selectedAccount = "", selectedCampaign = "", selectedAdset = "") {
  const options = adLaunchOptions();
  const accounts = options.accounts || [];
  const accountSelect = $("#ad-launch-account");
  const campaignSelect = $("#ad-launch-campaign");
  const adsetSelect = $("#ad-launch-adset");
  if (!accountSelect || !campaignSelect || !adsetSelect) return;
  const accountGroups = new Map();
  accounts.forEach((account) => {
    const groupKey = `${account.businessName || account.businessId || "未分组 BC"} · ${account.credentialName || account.credentialId || "Meta 凭证"}`;
    if (!accountGroups.has(groupKey)) accountGroups.set(groupKey, []);
    accountGroups.get(groupKey).push(account);
  });
  const accountOptions = Array.from(accountGroups.entries()).map(([groupName, groupAccounts]) => `
    <optgroup label="${esc(groupName)}">
      ${groupAccounts.map((account) => `<option value="${esc(account.accountId)}" ${account.accountId === selectedAccount ? "selected" : ""}>${esc(account.accountName || account.accountId)} · ${esc(account.businessName || "BM 未标记")} · ${esc(account.accountId)}</option>`).join("")}
    </optgroup>
  `).join("");
  accountSelect.innerHTML = `<option value="">选择要投放的广告户</option>${accountOptions}`;
  const accountId = accountSelect.value || selectedAccount;
  const campaigns = (options.campaigns || []).filter((campaign) => !accountId || campaign.accountId === accountId);
  campaignSelect.innerHTML = `<option value="">选择系列</option>${campaigns
    .map((campaign) => `<option value="${esc(campaign.key)}" ${campaign.key === selectedCampaign ? "selected" : ""}>${esc(campaign.campaignName)} · ${money(campaign.spend)}</option>`)
    .join("")}`;
  const campaign = campaigns.find((item) => item.key === (campaignSelect.value || selectedCampaign));
  const adsets = (options.adsets || []).filter((adset) => {
    if (accountId && adset.accountId !== accountId) return false;
    if (campaign && (adset.campaignId || adset.campaignName) !== (campaign.campaignId || campaign.campaignName)) return false;
    return true;
  });
  adsetSelect.innerHTML = `<option value="">选择广告组</option>${adsets
    .map((adset) => `<option value="${esc(adset.key)}" ${adset.key === selectedAdset ? "selected" : ""}>${esc(adset.adsetName)} · ${money(adset.spend)} · ${esc(adset.ads || 0)} 条广告</option>`)
    .join("")}`;
  renderAdLaunchSelectedAccountInfo(accountId);
}

function renderAdLaunchSelectedAccountInfo(accountId = "") {
  const info = $("#ad-launch-account-info");
  if (!info) return;
  const account = (adLaunchOptions().accounts || []).find((item) => item.accountId === accountId);
  if (!account) {
    info.className = "ad-launch-account-info is-empty";
    info.textContent = "请选择广告户；后续系列、广告组、主页和凭证都会按此广告户联动。";
    return;
  }
  const assigned = account.bound ? `已分配：${(account.assignedUsernames || []).join(", ") || "管理员"}` : "尚未分配团队账号";
  info.className = "ad-launch-account-info is-ready";
  info.innerHTML = [
    `<strong>${esc(account.accountName || account.accountId)}</strong>`,
    `<span>BM：${esc(account.businessName || account.businessId || "未标记")}</span>`,
    `<span>凭证：${esc(account.credentialName || account.credentialId || "-")}</span>`,
    `<span>${esc(assigned)}</span>`,
  ].join("");
}

function renderAdLaunchIdentitySelects(selectedPageId = "", selectedInstagramActorId = "") {
  const options = adLaunchOptions();
  const pageSelect = $("#ad-launch-page-id");
  const instagramSelect = $("#ad-launch-ig-id");
  const accountId = $("#ad-launch-account")?.value || "";
  if (!pageSelect || !instagramSelect) return;
  const account = (options.accounts || []).find((item) => item.accountId === accountId) || {};
  const credentialId = account.credentialId || "";
  const pages = (options.pages || []).filter((item) => !credentialId || !item.credentialId || item.credentialId === credentialId);
  const actors = (options.instagramActors || []).filter((item) => !credentialId || !item.credentialId || item.credentialId === credentialId);
  const fallbackPageId = selectedPageId || options.defaults?.pageId || "";
  const fallbackInstagramActorId = selectedInstagramActorId || options.defaults?.instagramActorId || "";
  const pageOptions = [`<option value="">请选择已绑定主页</option>`];
  pages.forEach((page) => {
    pageOptions.push(`<option value="${esc(page.id)}" ${page.id === fallbackPageId ? "selected" : ""}>${esc(page.name || page.id)} · ${esc(page.id)}</option>`);
  });
  if (fallbackPageId && !pages.some((page) => page.id === fallbackPageId)) {
    pageOptions.push(`<option value="${esc(fallbackPageId)}" selected>默认主页 · ${esc(fallbackPageId)}</option>`);
  }
  pageSelect.innerHTML = pageOptions.join("");
  if (!fallbackPageId && !pages.length) pageSelect.options[0].textContent = "未同步主页，请先在凭证中心绑定";

  const instagramOptions = [`<option value="">不绑定 Instagram 账号</option>`];
  actors.forEach((actor) => {
    const label = actor.username ? `@${actor.username}` : (actor.name || actor.id);
    instagramOptions.push(`<option value="${esc(actor.id)}" ${actor.id === fallbackInstagramActorId ? "selected" : ""}>${esc(label)} · ${esc(actor.id)}</option>`);
  });
  if (fallbackInstagramActorId && !actors.some((actor) => actor.id === fallbackInstagramActorId)) {
    instagramOptions.push(`<option value="${esc(fallbackInstagramActorId)}" selected>默认 Instagram · ${esc(fallbackInstagramActorId)}</option>`);
  }
  instagramSelect.innerHTML = instagramOptions.join("");
}

function updateAdLaunchModeFields() {
  const campaignMode = $("#ad-launch-campaign-mode")?.value || "create";
  const adsetMode = $("#ad-launch-adset-mode")?.value || "create";
  $("#ad-launch-campaign-create").hidden = campaignMode !== "create";
  $("#ad-launch-campaign-select-wrap").hidden = campaignMode !== "select";
  $("#ad-launch-adset-create").hidden = adsetMode !== "create";
  $("#ad-launch-adset-select-wrap").hidden = adsetMode !== "select";
  if (campaignMode === "create" && !$("#ad-launch-campaign-name").value.trim()) {
    const base = $("#ad-launch-name").value.trim() || $("#ad-launch-product").value || "SOSOVE";
    $("#ad-launch-campaign-name").value = `${base}-系列`;
  }
  if (adsetMode === "create" && !$("#ad-launch-adset-name").value.trim()) {
    $("#ad-launch-adset-name").value = `${$("#ad-launch-countries").value || "JP"}-素材测试`;
  }
  const manualPlacement = adLaunchPlacementMode() === "manual";
  const placementList = $("#ad-launch-placement-list");
  if (placementList) placementList.classList.toggle("is-muted", !manualPlacement);
  document.querySelectorAll("[data-ad-launch-placement]").forEach((input) => {
    input.disabled = !manualPlacement;
  });
  renderAdLaunchLiveSummary();
}

function selectedAdLaunchAccount() {
  const accountId = $("#ad-launch-account")?.value || "";
  return (adLaunchOptions().accounts || []).find((account) => account.accountId === accountId) || {};
}

function selectedAdLaunchCampaign() {
  const key = $("#ad-launch-campaign")?.value || "";
  return (adLaunchOptions().campaigns || []).find((campaign) => campaign.key === key) || {};
}

function selectedAdLaunchAdset() {
  const key = $("#ad-launch-adset")?.value || "";
  return (adLaunchOptions().adsets || []).find((adset) => adset.key === key) || {};
}

function renderAdLaunchMaterial() {
  const material = state.adLaunches.material;
  const box = $("#ad-launch-material-preview");
  if (!box) return;
  const config = adLaunchMaterialConfig();
  if (!material) {
    box.innerHTML = `
      <div class="ad-launch-upload-empty">
        <strong>${esc(config.label)}素材待上传</strong>
        <span>支持 ${esc(config.accept.replaceAll("image/*", "图片").replaceAll("video/*", "视频"))}，也可以复用素材库里的历史素材。</span>
      </div>
    `;
    renderAdLaunchMaterialGuidance();
    renderAdLaunchPreview();
    renderAdLaunchLiveSummary();
    return;
  }
  const sizeMb = material.size ? `${(Number(material.size) / 1024 / 1024).toFixed(2)} MB` : "-";
  box.innerHTML = `
    <div class="ad-launch-uploaded-file">
      ${material.previewDataUrl ? `<img class="ad-launch-material-thumb" src="${esc(material.previewDataUrl)}" alt="${esc(material.name || "素材")}" />` : ""}
      <span class="action-badge ${material.type === "video" ? "info" : "good"}">${esc(material.type || config.type)}</span>
      <strong>${esc(material.name)}</strong>
      <small>${esc(sizeMb)} · ${esc(material.id || "素材库")}</small>
      <button class="ghost-btn danger" data-ad-launch-clear-material type="button">移除</button>
    </div>
  `;
  renderAdLaunchMaterialGuidance();
  renderAdLaunchPreview();
  renderAdLaunchLiveSummary();
}

function prefillAdLaunchFromProduct() {
  const sku = $("#ad-launch-product").value;
  const product = (adLaunchOptions().products || []).find((item) => item.sku === sku);
  if (!product) return;
  const date = new Date().toISOString().slice(5, 10).replace("-", "");
  if (!$("#ad-launch-name").value.trim()) $("#ad-launch-name").value = `${product.sku}-${date}-素材测试`;
  if (!$("#ad-launch-campaign-name").value.trim()) $("#ad-launch-campaign-name").value = `${product.sku}-JP-素材测试-${date}`;
  if (!$("#ad-launch-adset-name").value.trim()) $("#ad-launch-adset-name").value = `JP-宽泛-${date}`;
  if (!$("#ad-launch-headline").value.trim()) $("#ad-launch-headline").value = product.title;
  if (!$("#ad-launch-primary-text").value.trim()) {
    $("#ad-launch-primary-text").value = `${product.title}\n围绕主卖点做素材测试，突出上身效果、细节质感和日常穿搭场景。`;
  }
  if (!$("#ad-launch-ai-prompt").value.trim()) {
    $("#ad-launch-ai-prompt").value = productAiPrompt(product, {
      templateKey: "facebook",
      mode: "text",
      size: $("#ad-launch-ai-size")?.value || "1024x1024",
    });
  }
  if (!$("#ad-launch-link-url").value.trim()) {
    const base = adLaunchOptions().defaults?.linkBase || "https://sosove.com/products/";
    $("#ad-launch-link-url").value = `${base}${encodeURIComponent(product.sku)}`;
  }
  updateAdLaunchModeFields();
}

function pickAdLaunchMaterialFromLibrary() {
  const launch = (state.adLaunches.launches || []).find((item) => item.material?.path || item.material?.id);
  if (!launch?.material) {
    showToast("素材库里还没有可复用素材，请先上传一个素材");
    return;
  }
  state.adLaunches.material = { ...launch.material };
  if (launch.material.type === "video") state.adLaunches.materialMode = "video";
  else if (adLaunchMaterialMode() === "video") state.adLaunches.materialMode = "single_image";
  setAdLaunchMaterialMode(state.adLaunches.materialMode);
  showToast(`已选择素材：${launch.material.name || launch.material.id}`);
}

function clearAdLaunchMaterial() {
  state.adLaunches.material = null;
  const fileInput = $("#ad-launch-file");
  if (fileInput) fileInput.value = "";
  renderAdLaunchMaterial();
  showToast("已移除当前素材");
}

function adLaunchMaterialPayload() {
  if (!state.adLaunches.material) return null;
  const { previewDataUrl, ...material } = state.adLaunches.material;
  return material;
}

async function uploadAdLaunchMaterial() {
  const file = $("#ad-launch-file").files?.[0];
  if (!file) {
    showToast("请先选择剪辑好的视频或图片");
    return;
  }
  const config = adLaunchMaterialConfig();
  if (config.type === "image" && !file.type.startsWith("image/")) {
    showToast("当前素材类型需要上传图片");
    return;
  }
  if (config.type === "video" && !file.type.startsWith("video/")) {
    showToast("当前素材类型需要上传视频");
    return;
  }
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch("/api/sku-board/ad-launch-materials", {
    method: "POST",
    body: formData,
  });
  const payload = await response.json();
  if (!payload.ok) throw new Error(payload.error || "素材上传失败");
  state.adLaunches.material = payload.material;
  renderAdLaunchMaterial();
  if (!$("#ad-launch-name").value.trim()) {
    $("#ad-launch-name").value = file.name.replace(/\.[^.]+$/, "");
  }
  showToast("素材已上传");
}

async function generateAdLaunchAiImage() {
  if (!state.auth.user) {
    openLoginDialog();
    return;
  }
  if (!canManageFacebookAds()) {
    showToast("只有管理员、运营或选品可以生成投放图片");
    return;
  }
  const prompt = $("#ad-launch-ai-prompt").value.trim();
  if (!prompt) {
    showToast("请先填写 AI 生图提示词");
    $("#ad-launch-ai-prompt").focus();
    return;
  }
  const button = $("#ad-launch-ai-generate-btn");
  const original = button.textContent;
  button.disabled = true;
  button.textContent = "生成中...";
  $("#ad-launch-ai-status").textContent = `正在调用 ${aiImageProviderLabel($("#ad-launch-ai-model").value || "gpt-image-2")}`;
  try {
    const payload = await api("/api/sku-board/ad-launch-ai-image", {
      method: "POST",
      body: JSON.stringify({
        prompt,
        model: $("#ad-launch-ai-model").value || "gpt-image-2",
        size: $("#ad-launch-ai-size").value || "1024x1024",
      }),
    });
    state.adLaunches.material = { ...payload.material, previewDataUrl: payload.previewDataUrl || "" };
    if (adLaunchMaterialMode() === "video") {
      state.adLaunches.materialMode = "single_image";
    }
    setAdLaunchMaterialMode(state.adLaunches.materialMode || "single_image");
    if (!$("#ad-launch-name").value.trim()) {
      $("#ad-launch-name").value = (payload.material?.name || "ai-image").replace(/\.[^.]+$/, "");
    }
    $("#ad-launch-ai-status").textContent = "已生成并选中";
    showToast("AI 图片已生成，可以直接保存投放草稿");
  } catch (error) {
    $("#ad-launch-ai-status").textContent = "生成失败";
    showToast(error.message);
  } finally {
    button.disabled = false;
    button.textContent = original;
  }
}

async function createAdLaunch(event) {
  event.preventDefault();
  if (state.adLaunches.saving) return;
  const saveButton = $("#ad-launch-save-btn");
  const originalSaveText = saveButton?.textContent || "保存投放草稿";
  state.adLaunches.saving = true;
  if (saveButton) {
    saveButton.disabled = true;
    saveButton.textContent = "保存中…";
    saveButton.setAttribute("aria-busy", "true");
  }
  try {
    if (!state.auth.user) {
      openLoginDialog();
      return;
    }
    if (!canManageFacebookAds()) {
      showToast("只有管理员、运营或选品可以创建素材投放");
      return;
    }
    const account = selectedAdLaunchAccount();
    if (!account.accountId) {
      setAdLaunchStep(0);
      $("#ad-launch-account")?.focus();
      showToast("请先选择要投放的广告户");
      return;
    }
    if (!state.adLaunches.material) {
      await uploadAdLaunchMaterial();
      if (!state.adLaunches.material) return;
    }
    const campaign = selectedAdLaunchCampaign();
    const adset = selectedAdLaunchAdset();
    const campaignMode = $("#ad-launch-campaign-mode").value || "create";
    const adsetMode = $("#ad-launch-adset-mode").value || "create";
    const payload = await api("/api/sku-board/ad-launches", {
    method: "POST",
    body: JSON.stringify({
      sku: $("#ad-launch-product").value,
      accountId: account.accountId || $("#ad-launch-account").value,
      accountName: account.accountName || "",
      credentialId: account.credentialId || "",
      credentialName: account.credentialName || "",
      campaignMode,
      campaignId: campaignMode === "select" ? (campaign.campaignId || adset.campaignId || "") : "",
      campaignName: campaignMode === "select" ? (campaign.campaignName || adset.campaignName || "") : $("#ad-launch-campaign-name").value.trim(),
      objective: $("#ad-launch-objective").value,
      adsetMode,
      adsetId: adsetMode === "select" ? (adset.adsetId || "") : "",
      adsetName: adsetMode === "select" ? (adset.adsetName || "") : $("#ad-launch-adset-name").value.trim(),
      dailyBudget: Number($("#ad-launch-daily-budget").value || 0),
      optimizationGoal: $("#ad-launch-optimization").value,
      billingEvent: "IMPRESSIONS",
      bidStrategy: "LOWEST_COST_WITHOUT_CAP",
      countries: splitAdLaunchList($("#ad-launch-countries").value, { uppercase: true, splitWhitespace: true }),
      regions: splitAdLaunchList($("#ad-launch-regions").value),
      cities: splitAdLaunchList($("#ad-launch-cities").value),
      languages: splitAdLaunchList($("#ad-launch-languages").value),
      gender: checkedAdLaunchValue("ad-launch-gender", "all"),
      ageMin: Number($("#ad-launch-age-min").value || 18),
      ageMax: Number($("#ad-launch-age-max").value || 65),
      advancedAudience: Boolean($("#ad-launch-advanced-audience").checked),
      interestInclude: splitAdLaunchList($("#ad-launch-interest-include").value),
      interestExclude: splitAdLaunchList($("#ad-launch-interest-exclude").value),
      audienceSeed: $("#ad-launch-audience-seed").value.trim(),
      placementMode: adLaunchPlacementMode(),
      placements: selectedAdLaunchPlacements(),
      materialMode: adLaunchMaterialMode(),
      multiMaterial: Boolean($("#ad-launch-multi-material").checked),
      advantageCreative: Boolean($("#ad-launch-advantage-creative").checked),
      creativeOrder: checkedAdLaunchValue("ad-launch-creative-order", "left_to_right"),
      pixelId: $("#ad-launch-pixel-id").value.trim(),
      conversionEvent: $("#ad-launch-conversion-event").value,
      batchCount: Number($("#ad-launch-batch-count").value || 1),
      namingRule: $("#ad-launch-naming-rule").value.trim(),
      pageId: $("#ad-launch-page-id").value.trim(),
      instagramActorId: $("#ad-launch-ig-id").value.trim(),
      name: $("#ad-launch-name").value.trim(),
      headline: $("#ad-launch-headline").value.trim(),
      primaryText: $("#ad-launch-primary-text").value.trim(),
      linkUrl: $("#ad-launch-link-url").value.trim(),
      cta: $("#ad-launch-cta").value,
      note: $("#ad-launch-note").value.trim(),
      material: adLaunchMaterialPayload(),
    }),
    });
    updateAdLaunchPayload(payload);
    $("#ad-launch-form").reset();
    state.adLaunches.material = null;
    state.adLaunches.materialMode = "single_image";
    state.adLaunches.step = 0;
    renderAdLaunchPanel();
    showToast(payload.created > 1 ? `已保存 ${payload.created} 条投放草稿` : "投放草稿已保存，右侧可创建暂停广告");
  } finally {
    state.adLaunches.saving = false;
    if (saveButton) {
      saveButton.disabled = false;
      saveButton.textContent = originalSaveText;
      saveButton.removeAttribute("aria-busy");
    }
  }
}

function renderAdLaunchKpis() {
  const summary = state.adLaunches.summary || {};
  $("#ad-launch-kpis").innerHTML = [
    kpiCard("投放记录", summary.total || 0, "当前可见"),
    kpiCard("待创建", summary.draft || 0, "草稿 / 待创建"),
    kpiCard("Meta 暂停", summary.paused || 0, "可人工上线"),
    kpiCard("投放中", summary.active || 0, `失败 ${summary.failed || 0}`),
  ].join("");
}

function filteredAdLaunches() {
  const query = state.adLaunches.filters.q.trim().toLowerCase();
  return (state.adLaunches.launches || []).filter((launch) => {
    if (!query) return true;
    return [
      launch.id,
      launch.name,
      launch.sku,
      launch.productTitle,
      launch.accountName,
      launch.campaignName,
      launch.adsetName,
      launch.material?.name,
      launch.meta?.adId,
      launch.meta?.creativeId,
    ]
      .join(" ")
      .toLowerCase()
      .includes(query);
  });
}

function renderAdLaunchList() {
  const list = $("#ad-launch-list");
  if (!list) return;
  const launches = filteredAdLaunches();
  list.innerHTML = launches.length ? launches.map(renderAdLaunchCard).join("") : emptyCard("还没有素材投放记录");
}

function renderAdLaunchCard(launch) {
  const material = launch.material || {};
  const meta = launch.meta || {};
  const tone = launch.status === "active" ? "good" : launch.status === "failed" ? "danger" : launch.status === "paused" ? "warn" : "info";
  const materialModeLabel = AD_LAUNCH_MATERIAL_MODES[launch.materialMode]?.label || (material.type === "video" ? "视频" : "素材");
  const placementText = launch.placementMode === "manual"
    ? (launch.placements || []).map((placement) => AD_LAUNCH_PLACEMENT_LABELS[placement] || placement).join(" / ")
    : "进阶版位";
  const audienceText = `${esc((launch.countries || []).join(",") || "JP")} · ${esc(AD_LAUNCH_GENDER_LABELS[launch.gender] || "全部")} · ${esc(launch.ageMin || 18)}-${esc(launch.ageMax || 65)}`;
  const publishButton = launch.canPublish
    ? `<button class="primary-btn" data-ad-launch-publish="${esc(launch.id)}" type="button">创建暂停广告</button>`
    : "";
  const activateButton = launch.canActivate
    ? `<button class="primary-btn danger" data-ad-launch-activate="${esc(launch.id)}" type="button">上线投放</button>`
    : "";
  const pauseButton = launch.canPause
    ? `<button class="ghost-btn danger" data-ad-launch-pause="${esc(launch.id)}" type="button">暂停广告</button>`
    : "";
  return `
    <article class="ad-launch-card" data-ad-launch-card="${esc(launch.id)}">
      <div class="ad-launch-card-head">
        <div>
          <span class="panel-kicker">${esc(launch.id)} · ${esc(material.type || "material")}</span>
          <h4>${esc(launch.name || "未命名广告")}</h4>
          <p>${esc(launch.productTitle || launch.sku || "未关联商品")}</p>
        </div>
        <span class="action-badge ${toneClass(tone)}">${esc(launch.statusLabel || launch.status)}</span>
      </div>
      <div class="ad-launch-meta-grid">
        <span><strong>广告户</strong>${esc(launch.accountName || launch.accountId || "-")}</span>
        <span><strong>投放凭证</strong>${esc(launch.credentialName || meta.credentialName || "待绑定")}</span>
        <span><strong>系列</strong>${esc(launch.campaignId ? launch.campaignName || launch.campaignId : `新建 · ${launch.campaignName || "-"}`)}</span>
        <span><strong>广告组</strong>${esc(launch.adsetId ? launch.adsetName || launch.adsetId : `新建 · ${launch.adsetName || "-"}`)}</span>
        <span><strong>受众</strong>${audienceText}</span>
        <span><strong>版位</strong>${esc(placementText || "-")}</span>
        <span><strong>素材</strong>${esc(`${materialModeLabel} · ${material.name || "-"}`)}</span>
      </div>
      <div class="ad-launch-copy">
        <strong>${esc(launch.headline || "无标题")}</strong>
        <p>${esc(launch.primaryText || "暂无正文文案")}</p>
      </div>
      <div class="stack-card-meta">
        <span class="metric-pill">Page ${esc(launch.pageId || "-")}</span>
        <span class="metric-pill">${esc(launch.ctaLabel || launch.cta || "CTA")}</span>
        <span class="metric-pill">${esc((launch.countries || []).join(",") || "JP")} · ${money(launch.dailyBudget || 0)}/day</span>
        <span class="metric-pill">${esc((launch.languages || []).join(",") || "语言不限")}</span>
        <span class="metric-pill">${esc(launch.objective || "OUTCOME_TRAFFIC")} / ${esc(launch.optimizationGoal || "LINK_CLICKS")}</span>
        <span class="metric-pill blue">Ad ${esc(meta.adId || "未创建")}</span>
        <span class="metric-pill amber">Creative ${esc(meta.creativeId || "未创建")}</span>
      </div>
      ${meta.lastError ? `<div class="ad-launch-error">${esc(meta.lastError)}</div>` : ""}
      ${launch.credentialIssue ? `<div class="ad-launch-error">凭证状态：${esc(launch.credentialIssue)}</div>` : ""}
      <div class="design-task-actions">
        <small>创建 ${esc(shortDate(launch.createdAt))} · 更新 ${esc(shortDate(launch.updatedAt))}</small>
        <div>
          ${publishButton}
          ${activateButton}
          ${pauseButton}
          ${launch.canDelete ? `<button class="ghost-btn danger" data-ad-launch-delete="${esc(launch.id)}" type="button">删除</button>` : ""}
        </div>
      </div>
    </article>
  `;
}

async function publishAdLaunch(launchId) {
  const launch = state.adLaunches.launches.find((item) => item.id === launchId);
  if (!window.confirm(`将创建真实 Meta 广告，但状态为暂停，不会直接上线。\n${launch?.name || launchId}`)) return;
  const payload = await api(`/api/sku-board/ad-launches/${encodeURIComponent(launchId)}/publish`, {
    method: "POST",
    body: JSON.stringify({ confirm: "CREATE_PAUSED_AD" }),
  });
  updateAdLaunchPayload(payload);
  renderAdLaunchPanel();
  showToast("Meta 暂停广告已创建");
}

async function setAdLaunchStatus(launchId, status) {
  const active = status === "ACTIVE";
  const confirmText = active ? "确认上线这个真实 Meta 广告？上线后可能开始花费。" : "确认暂停这个 Meta 广告？";
  if (!window.confirm(confirmText)) return;
  const payload = await api(`/api/sku-board/ad-launches/${encodeURIComponent(launchId)}/status`, {
    method: "POST",
    body: JSON.stringify({ status, confirm: active ? "ACTIVATE_AD" : "PAUSE_AD" }),
  });
  updateAdLaunchPayload(payload);
  renderAdLaunchPanel();
  showToast(active ? "广告已上线" : "广告已暂停");
}

async function deleteAdLaunch(launchId) {
  const launch = state.adLaunches.launches.find((item) => item.id === launchId);
  if (!window.confirm(`删除这条素材投放记录？\n${launch?.name || launchId}`)) return;
  const payload = await api(`/api/sku-board/ad-launches/${encodeURIComponent(launchId)}`, {
    method: "DELETE",
    body: JSON.stringify({}),
  });
  updateAdLaunchPayload(payload);
  renderAdLaunchPanel();
  showToast("素材投放记录已删除");
}


function metaAnalysisActionLabel(action) {
  return META_ANALYSIS_ACTION_LABELS[action] || action || "继续观察";
}

function metaAnalysisActionTone(action) {
  if (action === "scale_observe") return "good";
  if (["immediate_close", "product_stop_test"].includes(action)) return "danger";
  if (["pause_observe", "copy_variant", "fix_payment"].includes(action)) return "warn";
  if (action === "keep_small_run") return "info";
  return "muted";
}

function metaAnalysisReason(ad = {}) {
  const action = ad.recommended_action || "watch";
  const classification = ad.classification || "";
  if (action === "scale_observe") return `已出现 ${num(ad.attributed_orders ?? ad.conversions)} 个购买信号，可小步加预算并继续盯 CPA。`;
  if (action === "keep_small_run") return `已有购买事件，但样本还不够稳定，预算先保持不变。`;
  if (action === "copy_variant") return "CTR、CPC 有可测信号，复制 1–2 个新素材角度，小预算快速验证。";
  if (action === "fix_payment") return "出现结账或支付异常，先修复支付链路再恢复预算。";
  if (action === "pause_observe") return "点击已产生，但购买意图仍未验证；暂停后检查承接页、价格和支付。";
  if (action === "immediate_close" && classification === "weak_hook") return "曝光已足够但 CTR 偏低，首屏或前三秒吸引力不足，建议停掉并重做素材。";
  if (action === "immediate_close") return "花费或点击达到止损线，仍未出现购买信号，建议立即关闭。";
  if (action === "ignore_no_spend") return "当前没有消耗，先检查广告状态、受众和审核结果。";
  return "数据量还少，继续用最低预算收集信号。";
}

function metaAnalysisAlertLabel(value) {
  const labels = {
    cpc_spike: "CPC 突增",
    spend_spike_no_order: "花费突增无单",
    order_drop_after_clicks: "点击后无购买",
    platform_conversion_without_attributed_order: "平台转化待核单",
    payment_failed: "支付失败",
    checkout_no_paid_order: "结账未付款",
    spend_no_click: "有花费无点击",
    high_ctr_no_paid_order: "高 CTR 无付款",
    ctr_too_low: "CTR 过低",
  };
  return labels[value] || value;
}

function metaAnalysisSettingsFromControls() {
  const settings = state.metaAnalysis.settings;
  settings.usePlatformPurchase = Boolean($("#meta-analysis-use-purchase")?.checked);
  settings.targetCpa = $("#meta-analysis-target-cpa")?.value.trim() || "";
  settings.stopSpend = Number($("#meta-analysis-stop-spend")?.value || 5);
  settings.stopClicks = Number($("#meta-analysis-stop-clicks")?.value || 30);
  state.metaAnalysis.filters.range = $("#meta-analysis-range")?.value || "last_7d";
}

function metaAnalysisQuery() {
  metaAnalysisSettingsFromControls();
  const params = new URLSearchParams({
    range: state.metaAnalysis.filters.range,
    usePlatformPurchase: state.metaAnalysis.settings.usePlatformPurchase ? "true" : "false",
    stopSpend: String(state.metaAnalysis.settings.stopSpend || 5),
    stopClicks: String(state.metaAnalysis.settings.stopClicks || 30),
  });
  if (state.metaAnalysis.settings.targetCpa !== "") params.set("targetCpa", state.metaAnalysis.settings.targetCpa);
  return params.toString();
}

async function loadMetaAnalysis(force = false) {
  if (!state.auth.user || !canManageFacebookAds()) {
    renderMetaAnalysisPanel();
    return;
  }
  if (state.metaAnalysis.loading) return;
  if (state.metaAnalysis.loaded && !force) {
    renderMetaAnalysisPanel();
    return;
  }
  state.metaAnalysis.loading = true;
  renderMetaAnalysisPanel();
  try {
    state.metaAnalysis.payload = await api(`/api/sku-board/meta-ad-analysis?${metaAnalysisQuery()}`);
    state.metaAnalysis.loaded = true;
  } finally {
    state.metaAnalysis.loading = false;
    renderMetaAnalysisPanel();
  }
}

function metaAnalysisAds() {
  return state.metaAnalysis.payload?.report?.action_table || [];
}

function metaAnalysisAccountKey(value) {
  return String(value || "").toLowerCase().replace(/\s+/g, "").replace(/^act_/, "");
}

function metaAnalysisAccountCatalog() {
  const byId = new Map();
  const sourceAccounts = state.metaAnalysis.payload?.source?.accountCatalog || [];
  sourceAccounts.forEach((account) => {
    const key = metaAnalysisAccountKey(account.accountId);
    if (!key) return;
    byId.set(key, {
      ...account,
      accountId: account.accountId,
      AdvertiserId: account.accountId,
      AccountName: account.accountName || account.accountId,
      businessId: account.businessId || "",
      businessName: account.businessName || "未分组 BC",
      spend: 0,
      impressions: 0,
      clicks: 0,
      conversions: 0,
      ctr_pct: 0,
      action: "watch",
    });
  });
  metaAnalysisAccountsFromReport().forEach((account) => {
    const key = metaAnalysisAccountKey(account.AdvertiserId || account.accountId);
    if (!key) return;
    byId.set(key, { ...(byId.get(key) || {}), ...account, accountId: account.accountId || account.AdvertiserId });
  });
  return Array.from(byId.values()).sort((a, b) => Number(b.spend || 0) - Number(a.spend || 0) || String(a.AccountName || "").localeCompare(String(b.AccountName || "")));
}

function metaAnalysisAccountsFromReport() {
  return state.metaAnalysis.payload?.report?.accounts || [];
}

function filteredMetaAnalysisAds() {
  const query = state.metaAnalysis.filters.q.trim().toLowerCase();
  const action = state.metaAnalysis.filters.action;
  const accountId = state.metaAnalysis.filters.accountId;
  return metaAnalysisAds().filter((ad) => {
    if (accountId && metaAnalysisAccountKey(ad.AdvertiserId) !== metaAnalysisAccountKey(accountId)) return false;
    if (state.metaAnalysis.filters.businessId && String(ad.businessId || "") !== state.metaAnalysis.filters.businessId) return false;
    if (action === "__stop__" && !["immediate_close", "product_stop_test"].includes(ad.recommended_action)) return false;
    if (action === "__material__" && !["weak_hook", "small_retest_only"].includes(ad.classification) && !String(ad.anomaly_alerts || "").includes("ctr_too_low")) return false;
    if (action === "__anomaly__" && !String(ad.anomaly_alerts || "").trim()) return false;
    if (action && !action.startsWith("__") && ad.recommended_action !== action) return false;
    if (!query) return true;
    return [ad.AccountName, ad.CampaignName, ad.AdgroupName, ad.AdName, ad.AdId, ad.Product, ad.sku]
      .join(" ")
      .toLowerCase()
      .includes(query);
  });
}

function metaAnalysisAccounts() {
  return metaAnalysisAccountCatalog();
}

function metaAnalysisSelectedAccount() {
  const accountId = state.metaAnalysis.filters.accountId;
  return accountId ? metaAnalysisAccounts().find((account) => metaAnalysisAccountKey(account.AdvertiserId || account.accountId) === metaAnalysisAccountKey(accountId)) || null : null;
}

function renderMetaAnalysisBusinessFilter() {
  const select = $("#meta-analysis-business-filter");
  if (!select) return;
  const groups = new Map();
  metaAnalysisAccounts().forEach((account) => {
    const id = String(account.businessId || "__unassigned__");
    if (!groups.has(id)) groups.set(id, account.businessName || "未分组 BC");
  });
  if (state.metaAnalysis.filters.businessId && !groups.has(state.metaAnalysis.filters.businessId)) {
    state.metaAnalysis.filters.businessId = "";
    state.metaAnalysis.filters.accountId = "";
  }
  select.innerHTML = `<option value="">全部 BC（${groups.size}）</option>${Array.from(groups.entries()).map(([id, name]) => `<option value="${esc(id)}">${esc(name)} · ${esc(id === "__unassigned__" ? "未分组" : id)}</option>`).join("")}`;
  select.value = state.metaAnalysis.filters.businessId;
}

function renderMetaAnalysisAccountFilter() {
  const select = $("#meta-analysis-account-filter");
  if (!select) return;
  const allAccounts = metaAnalysisAccounts();
  const accounts = allAccounts.filter((account) => !state.metaAnalysis.filters.businessId || String(account.businessId || "__unassigned__") === state.metaAnalysis.filters.businessId);
  if (state.metaAnalysis.filters.accountId && !accounts.some((account) => metaAnalysisAccountKey(account.AdvertiserId || account.accountId) === metaAnalysisAccountKey(state.metaAnalysis.filters.accountId))) {
    state.metaAnalysis.filters.accountId = "";
  }
  if (state.metaAnalysis.filters.accountId && !allAccounts.some((account) => metaAnalysisAccountKey(account.AdvertiserId || account.accountId) === metaAnalysisAccountKey(state.metaAnalysis.filters.accountId))) {
    state.metaAnalysis.filters.accountId = "";
  }
  select.innerHTML = `<option value="">全部广告户（${accounts.length}）</option>${accounts.map((account) => {
    const id = String(account.accountId || account.AdvertiserId || "");
    const name = account.AccountName || id || "Meta 广告户";
    const status = Number(account.spend || 0) > 0 ? "有数据" : "暂无数据";
    return `<option value="${esc(id)}">${esc(name)} · ${esc(id)} · ${status}</option>`;
  }).join("")}`;
  select.value = state.metaAnalysis.filters.accountId;
}

function metaAnalysisVisibleSummary() {
  const ads = filteredMetaAnalysisAds();
  const spend = ads.reduce((sum, ad) => sum + Number(ad.spend || 0), 0);
  const impressions = ads.reduce((sum, ad) => sum + Number(ad.impressions || 0), 0);
  const clicks = ads.reduce((sum, ad) => sum + Number(ad.clicks || 0), 0);
  const purchases = ads.reduce((sum, ad) => sum + Number(ad.attributed_orders ?? ad.conversions ?? 0), 0);
  const purchaseValue = ads.reduce((sum, ad) => sum + Number(ad.attributed_revenue || 0), 0);
  return {
    spend,
    impressions,
    clicks,
    platform_purchase_events: purchases,
    platform_purchase_value: purchaseValue,
    platform_roas: spend > 0 ? purchaseValue / spend : null,
    platform_cpa: purchases > 0 ? spend / purchases : null,
    ctr_pct: impressions > 0 ? clicks / impressions * 100 : 0,
    cpc: clicks > 0 ? spend / clicks : null,
    cpm: impressions > 0 ? spend / impressions * 1000 : null,
    anomaly_ads: ads.filter((ad) => String(ad.anomaly_alerts || "").trim()).length,
    active_spend_ads: ads.filter((ad) => Number(ad.spend || 0) > 0).length,
    visible_ads: ads.length,
  };
}

function renderMetaAnalysisKpis() {
  const target = $("#meta-analysis-kpis");
  if (!target) return;
  const summary = metaAnalysisVisibleSummary();
  const account = metaAnalysisSelectedAccount();
  const scope = account?.AccountName || "全部广告户";
  target.innerHTML = [
    kpiCard("广告花费", money(summary.spend || 0), `${scope} · ${num(summary.active_spend_ads || 0)} 条有消耗`),
    kpiCard("购买事件", num(summary.platform_purchase_events || 0, 1), `购买金额 ${money(summary.platform_purchase_value || 0)}`),
    kpiCard("Meta ROAS", summary.platform_roas == null ? "-" : Number(summary.platform_roas).toFixed(2), `CPA ${summary.platform_cpa == null ? "-" : money(summary.platform_cpa)}`),
    kpiCard("CTR", `${Number(summary.ctr_pct || 0).toFixed(2)}%`, `CPC ${summary.cpc == null ? "-" : money(summary.cpc)}`),
    kpiCard("CPM", summary.cpm == null ? "-" : money(summary.cpm), `${num(summary.impressions || 0)} 次曝光`),
    kpiCard("异常广告", num(summary.anomaly_ads || 0), `${num(summary.clicks || 0)} 次点击`),
  ].join("");
}

function metaAnalysisConclusionCard(label, count, note, action, tone) {
  return `<button class="ad-analysis-conclusion ${toneClass(tone)}" data-meta-analysis-action="${esc(action)}" type="button">
    <span>${esc(label)}</span><strong>${esc(count)}</strong><small>${esc(note)}</small>
  </button>`;
}

function renderMetaAnalysisConclusions() {
  const target = $("#meta-analysis-conclusions");
  if (!target) return;
  const ads = filteredMetaAnalysisAds();
  const countAction = (action) => ads.filter((ad) => ad.recommended_action === action).length;
  const stopCount = ads.filter((ad) => ["immediate_close", "product_stop_test"].includes(ad.recommended_action)).length;
  const materialCount = ads.filter((ad) => ["weak_hook", "small_retest_only"].includes(ad.classification) || String(ad.anomaly_alerts || "").includes("ctr_too_low")).length;
  const anomalyCount = ads.filter((ad) => String(ad.anomaly_alerts || "").trim()).length;
  target.innerHTML = [
    metaAnalysisConclusionCard("建议止损", stopCount, "达到花费/点击止损线", "__stop__", "danger"),
    metaAnalysisConclusionCard("放量观察", countAction("scale_observe"), "有购买样本，小步加预算", "scale_observe", "good"),
    metaAnalysisConclusionCard("保留小跑", countAction("keep_small_run"), "有信号，样本仍不足", "keep_small_run", "info"),
    metaAnalysisConclusionCard("补素材", materialCount, "弱钩子或可复制变体", "__material__", "warn"),
    metaAnalysisConclusionCard("异常广告", anomalyCount, "CPC、花费或转化异常", "__anomaly__", "warn"),
  ].join("");
}

function renderMetaAnalysisAccounts() {
  const target = $("#meta-analysis-accounts");
  if (!target) return;
  const accounts = metaAnalysisAccounts().filter((account) => !state.metaAnalysis.filters.businessId || String(account.businessId || "__unassigned__") === state.metaAnalysis.filters.businessId);
  target.innerHTML = accounts.length ? accounts.map((account) => {
    const accountId = String(account.accountId || account.AdvertiserId || "");
    const selected = metaAnalysisAccountKey(state.metaAnalysis.filters.accountId) === metaAnalysisAccountKey(accountId);
    return `
    <button class="ad-analysis-account-row ${selected ? "is-selected" : ""}" data-meta-analysis-account="${esc(accountId)}" type="button">
      <div><strong>${esc(account.AccountName || account.AdvertiserId || "Meta 广告户")}</strong><small>${esc(account.businessName || "未分组 BC")} · ${esc(account.credentialName || "未识别凭证")}</small><small>${esc(account.AdvertiserId || account.accountId || "")}</small></div>
      <div><span>${money(account.spend || 0)}</span><small>花费</small></div>
      <div><span>${Number(account.ctr_pct || 0).toFixed(2)}%</span><small>CTR</small></div>
      <div><span>${num(account.conversions || 0, 1)}</span><small>购买</small></div>
      <span class="action-badge ${toneClass(metaAnalysisActionTone(account.action))}">${esc(metaAnalysisActionLabel(account.action))}</span>
    </button>`;
  }).join("") : emptyCard("当前范围没有广告户消耗数据");
}

function renderMetaAnalysisTable() {
  const target = $("#meta-analysis-table-body");
  if (!target) return;
  const ads = filteredMetaAnalysisAds();
  $("#meta-analysis-row-count").textContent = `${ads.length} 条广告`;
  target.innerHTML = ads.length ? ads.map((ad) => {
    const action = ad.recommended_action || "watch";
    const alerts = String(ad.anomaly_alerts || "").split(",").filter(Boolean);
    const orders = ad.attributed_orders ?? ad.conversions ?? 0;
    const roas = ad.attributed_roas;
    return `<tr>
      <td><div class="ad-analysis-account-cell"><strong>${esc(ad.AccountName || "Meta 广告户")}</strong><small>${esc(ad.AdvertiserId || "")}</small></div></td>
      <td><div class="ad-analysis-ad-cell"><strong>${esc(ad.AdName || ad.AdId || "未命名广告")}</strong><span>${esc(ad.Product || "未识别商品")}${ad.sku ? ` · ${esc(ad.sku)}` : ""}</span><small>${esc(ad.AccountName || "")} / ${esc(ad.CampaignName || "")} / ${esc(ad.AdId || "")}</small></div></td>
      <td><strong>${money(ad.spend || 0)}</strong><small class="table-submetric">CPA ${ad.attributed_cpa == null ? (ad.platform_cpa == null ? "-" : money(ad.platform_cpa)) : money(ad.attributed_cpa)}</small></td>
      <td><strong>${num(ad.impressions || 0)}</strong><small class="table-submetric">${num(ad.clicks || 0)} 点击</small></td>
      <td><strong>${Number(ad.ctr_pct || 0).toFixed(2)}%</strong><small class="table-submetric">${ad.cpc == null ? "-" : money(ad.cpc)}</small></td>
      <td><strong>${num(orders, 1)}</strong><small class="table-submetric">ROAS ${roas == null ? "-" : Number(roas).toFixed(2)}</small></td>
      <td><span class="action-badge ${toneClass(metaAnalysisActionTone(action))}">${esc(metaAnalysisActionLabel(action))}</span>${alerts.length ? `<div class="ad-analysis-alerts">${alerts.map((item) => `<span>${esc(metaAnalysisAlertLabel(item))}</span>`).join("")}</div>` : ""}</td>
      <td><p class="ad-analysis-reason">${esc(metaAnalysisReason(ad))}</p></td>
      <td><strong>${esc(ad.tomorrow_budget_suggestion || "-")}</strong><small class="table-submetric">无单花费 ${esc(ad.stop_after_spend_without_order || "-")} / 点击 ${esc(ad.stop_after_clicks_without_order ?? "-")}</small></td>
    </tr>`;
  }).join("") : `<tr><td colspan="9"><div class="empty-state">当前筛选下没有广告数据</div></td></tr>`;
}

function renderMetaAnalysisPanel() {
  const panel = $("#ad-analysis-panel");
  if (!panel) return;
  const canRead = Boolean(state.auth.user && canManageFacebookAds());
  panel.querySelectorAll("input, select, button").forEach((field) => {
    field.disabled = !canRead || state.metaAnalysis.loading;
  });
  renderMetaAnalysisBusinessFilter();
  renderMetaAnalysisAccountFilter();
  $("#meta-analysis-business-filter").value = state.metaAnalysis.filters.businessId;
  $("#meta-analysis-range").value = state.metaAnalysis.filters.range;
  $("#meta-analysis-action-filter").value = state.metaAnalysis.filters.action;
  $("#meta-analysis-search").value = state.metaAnalysis.filters.q;
  $("#meta-analysis-use-purchase").checked = state.metaAnalysis.settings.usePlatformPurchase;
  $("#meta-analysis-target-cpa").value = state.metaAnalysis.settings.targetCpa;
  $("#meta-analysis-stop-spend").value = state.metaAnalysis.settings.stopSpend;
  $("#meta-analysis-stop-clicks").value = state.metaAnalysis.settings.stopClicks;
  const status = $("#meta-analysis-status");
  if (!canRead) {
    status.textContent = "管理员、运营、选品账号可以读取已分配的 Meta 广告户并运行广告分析。";
  } else if (state.metaAnalysis.loading) {
    status.textContent = "正在读取全部已绑定广告户，并运行止损、放量和素材判断规则…";
  } else if (state.metaAnalysis.payload) {
    const source = state.metaAnalysis.payload.source || {};
    const account = metaAnalysisSelectedAccount();
    const business = state.metaAnalysis.filters.businessId ? $("#meta-analysis-business-filter")?.selectedOptions?.[0]?.textContent : "全部 BC";
    const accountCount = (source.accountCatalog || []).length || source.accounts || 0;
    status.textContent = `${state.metaAnalysis.payload.rangeLabel || "当前范围"} · ${business || "全部 BC"} · ${account?.AccountName || "全部广告户"} · 已识别 ${num(accountCount)} 个广告户 · ${num(source.rows || 0)} 条明细 · 当前显示 ${num(filteredMetaAnalysisAds().length)} 条 · ${state.metaAnalysis.payload.warning || "分析完成"}`;
  } else {
    status.textContent = "点击“刷新并分析”，系统会读取凭证中心中的 Meta 广告户。";
  }
  renderMetaAnalysisKpis();
  renderMetaAnalysisConclusions();
  renderMetaAnalysisAccounts();
  renderMetaAnalysisTable();
}


function openShoplineDialog() {
  $("#shopline-dialog").showModal();
  if (!state.shopline.loaded) {
    loadShoplineProducts().catch((error) => showToast(error.message));
    return;
  }
  renderShoplineProducts();
}

function closeShoplineDialog() {
  const dialog = $("#shopline-dialog");
  if (dialog.open) dialog.close();
}

async function loadShoplineProducts() {
  state.shopline.loading = true;
  $("#shopline-status").textContent = "正在从 Shopline 读取商品...";
  $("#shopline-products").innerHTML = emptyCard("正在读取 Shopline 商品");
  try {
    const payload = await api("/api/sku-board/shopline-products");
    state.shopline.loaded = true;
    state.shopline.products = payload.products || [];
    state.shopline.source = payload.source || { mode: "unknown", error: "" };
    state.shopline.connector = payload.connector || { missing: [] };
    state.shopline.selected = new Set();
  } catch (error) {
    state.shopline.loaded = false;
    state.shopline.products = [];
    state.shopline.source = { mode: "error", error: error.message };
    state.shopline.connector = { missing: [] };
    throw error;
  } finally {
    state.shopline.loading = false;
    renderShoplineProducts();
  }
}

function filteredShoplineProducts() {
  const query = state.shopline.query.trim().toLowerCase();
  const status = state.shopline.status;
  return state.shopline.products.filter((product) => {
    if (status && product.status !== status) return false;
    if (!query) return true;
    return [
      product.sku,
      product.title,
      product.category,
      product.status,
      ...(product.tags || []),
    ]
      .join(" ")
      .toLowerCase()
      .includes(query);
  });
}

function renderShoplineProducts() {
  const mode = state.shopline.source?.mode || "unknown";
  const live = mode === "live";
  const missing = state.shopline.connector?.productImportMissing || state.shopline.connector?.missing || [];
  const products = filteredShoplineProducts();
  const activeCount = state.shopline.products.filter((product) => product.status === "active").length;
  const draftCount = state.shopline.products.filter((product) => product.status === "draft").length;
  const selectedCount = state.shopline.selected.size;
  const statusText = live
    ? `已连接 Shopline，读取到 ${state.shopline.products.length} 个商品，上架 ${activeCount} 个，草稿 ${draftCount} 个`
    : mode === "error"
    ? `Shopline 读取失败：${state.shopline.source?.error || "接口异常"}`
    : `当前未连接真实 Shopline，缺少：${missing.length ? missing.join("、") : "接口配置"}`;

  $("#shopline-status").textContent = statusText;
  $("#shopline-hint").innerHTML = live
    ? `<span class="action-badge good">真实数据</span><span>默认只显示上架商品；可切换到全部状态。勾选后导入，已存在 SKU 会更新商品图、标题、库存和价格。</span>`
    : mode === "error"
    ? `<span class="action-badge danger">读取失败</span><span>${esc(state.shopline.source?.error || "请检查 Shopline 配置和网络")}</span>`
    : `<span class="action-badge warn">预览模式</span><span>请先配置 SHOPLINE_API_BASE_URL、SHOPLINE_ACCESS_TOKEN、SHOPLINE_PRODUCTS_ENDPOINT，再导入真实商品。</span>`;

  $("#shopline-import-selected-btn").disabled = !live || selectedCount === 0;
  $("#shopline-import-selected-btn").textContent = selectedCount ? `导入选中 ${selectedCount}` : "导入选中";
  $("#shopline-select-all-btn").disabled = !live || !products.length;

  if (!products.length) {
    $("#shopline-products").innerHTML = emptyCard(state.shopline.loading ? "正在读取 Shopline 商品" : "没有匹配的商品");
    return;
  }

  $("#shopline-products").innerHTML = products.map((product) => {
    const checked = state.shopline.selected.has(product.key) ? "checked" : "";
    const disabled = live ? "" : "disabled";
    const image = product.imageUrl || "/static/assets/glasses-square.svg";
    const preview = product.sellingPreview || {};
    const previewPoints = Array.isArray(preview.points) ? preview.points.slice(0, 3) : [];
    return `
      <label class="shopline-product-card ${product.exists ? "exists" : ""}">
        <input type="checkbox" data-shopline-pick="${esc(product.key)}" ${checked} ${disabled} />
        <img src="${esc(image)}" alt="${esc(product.title)}" onerror="this.src='/static/assets/glasses-square.svg'" />
        <span>
          <strong>${esc(product.title)}</strong>
          <small>${esc(product.sku)} · ${esc(product.category || "未分类")} · ${productPrice(product)}</small>
          <small>库存 ${esc(product.inventory)} · ${esc(product.status || "active")}</small>
          <small class="shopline-selling-preview">卖点：${esc(preview.headline || "导入后自动识别")}</small>
          ${previewPoints.length ? `<span class="shopline-preview-tags">${previewPoints.map((point) => `<i>${esc(point)}</i>`).join("")}</span>` : ""}
        </span>
        <em>${product.exists ? "更新已有" : "新增"}</em>
      </label>`;
  }).join("");
}

async function importSelectedShoplineProducts() {
  const skus = Array.from(state.shopline.selected);
  if (!skus.length) {
    showToast("先勾选要导入的商品");
    return;
  }
  try {
    $("#shopline-import-selected-btn").disabled = true;
    $("#shopline-import-selected-btn").textContent = "正在导入...";
    const payload = await api("/api/sku-board/import-shopline", {
      method: "POST",
      body: JSON.stringify({ skus }),
    });
    closeShoplineDialog();
    await loadBoard();
    showToast(`Shopline 导入完成：新增 ${payload.created || 0}，更新 ${payload.updated || 0}`);
  } catch (error) {
    renderShoplineProducts();
    showToast(error.message);
  }
}

async function loadBoard() {
  const query = buildQuery();
  const response = await fetch(`/api/sku-board${query ? `?${query}` : ""}`);
  const payload = await response.json();
  if (!payload.ok) throw new Error(payload.error || "读取失败");
  state.items = payload.items || [];
  render(payload);
}

function render(payload) {
  if (payload.filters?.users) {
    state.auth.users = payload.filters.users;
  }
  renderSummary(payload.summary, payload.filteredSummary);
  renderOwners(payload.filters?.owners || []);
  renderInsights(payload.insights);
  renderRows(payload.items || []);
  renderMaterials(payload.items || []);
  renderFeedback(payload.items || []);
  renderTasks(payload.items || []);
  $("#filtered-count").textContent = payload.filteredSummary?.count ?? 0;
  $("#source-line").textContent = `数据文件：${payload.source?.updatedAt || "未保存"}`;
  syncButtonState();
  renderAccountPanel();
  renderDesignTaskPanel();
  renderAdLaunchPanel();
  renderAiImagePanel();
  setActiveView(state.view);
}

function renderOwners(owners) {
  const select = $("#owner-filter");
  const current = select.value;
  select.innerHTML = `<option value="">全部</option>${owners.map((owner) => `<option value="${esc(owner)}">${esc(owner)}</option>`).join("")}`;
  select.value = current;
}

function renderSummary(summary) {
  const counts = summary.statusCounts || {};
  const totals = summary.totals || {};
  $("#summary-main").textContent = counts.main ?? 0;
  $("#summary-count").textContent = `全部 ${summary.count ?? 0} 款 / 测试 ${counts.test ?? 0}`;
  $("#summary-spend").textContent = money(totals.spend);
  $("#summary-profit").textContent = money(totals.profit);
  $("#summary-profit").style.color = Number(totals.profit || 0) >= 0 ? "var(--teal)" : "var(--red)";
  $("#summary-roas").textContent = `ROAS ${num(totals.roas, 2)}`;
  $("#summary-tasks").textContent = totals.tasksOpen ?? 0;
  $("#summary-materials").textContent = `素材缺口 ${totals.materialGap ?? 0} · 建议 ${totals.suggestedTasks ?? 0}`;
  $("#summary-refresh").textContent = totals.refreshGap ?? 0;
  $("#summary-feedback").textContent = `反馈缺失 ${totals.feedbackMissing ?? 0}`;
}

function renderInsights(insights = {}) {
  $("#insight-headline").textContent = insights.headline || "暂无建议";
  const groups = [
    ["stop", "止损优先", "danger"],
    ["scale", "可放量", "good"],
    ["material", "素材缺口", "warn"],
    ["refresh", "翻新建议", "info"],
  ];
  $("#insight-grid").innerHTML = groups
    .map(([key, label, tone]) => {
      const items = insights[key] || [];
      const body = items.length
        ? items
            .map(
              (item) => `
                <li>
                  <span><strong>${esc(item.title)}</strong><br>${esc(item.reason)}</span>
                  <span>${money(item.profit)}</span>
                </li>`
            )
            .join("")
        : `<li><span>暂无</span><span>-</span></li>`;
      return `
        <article class="insight-card">
          <h3><i class="dot ${tone}"></i>${label}</h3>
          <ul>${body}</ul>
        </article>`;
    })
    .join("");
}

function renderRows(items) {
  if (!items.length) {
    tbody.innerHTML = `<tr><td colspan="10"><div class="empty-state">没有匹配的 SKU</div></td></tr>`;
    return;
  }
  tbody.innerHTML = items.map(renderRow).join("");
}

function renderRow(item) {
  const metrics = item.metrics || {};
  const selling = item.selling || {};
  const design = item.design || {};
  const ad = item.ad || {};
  const refresh = item.refresh || {};
  const primary = item.diagnosis?.primary || {};
  const notes = (item.notes || []).slice(0, 2);
  const feedback = (item.feedback || []).slice(0, 2);
  const refreshGap = Math.max(Number(refresh.suggested || 0) - Number(refresh.current || 0), 0);
  const canAutoSelling = Boolean(item.shopline);
  return `
    <tr class="${rowTone(item)}" data-sku="${esc(item.sku)}">
      <td>
        <select class="status-select" data-status-sku="${esc(item.sku)}">
          ${statusOptions(item.status)}
        </select>
      </td>
      <td>
        <div class="product-cell">
          <button class="product-image-btn" data-preview-image="${esc(item.image)}" data-preview-title="${esc(item.title)}" type="button" aria-label="放大查看 ${esc(item.title)}">
            <img src="${esc(item.image)}" alt="${esc(item.title)}" />
          </button>
          <div>
            <span class="sku-code">${esc(item.sku)}</span>
            <button class="product-title link-reset" data-open-sku="${esc(item.sku)}" type="button">${esc(item.title)}</button>
            <button class="delete-sku-btn" data-delete-sku="${esc(item.sku)}" data-delete-title="${esc(item.title)}" type="button">删除</button>
            <div class="mini-metrics">
              <span class="metric-pill">${num(ad.clicks)} 点击</span>
              <span class="metric-pill blue">${num(ad.cvr, 2)}% CVR</span>
              <span class="metric-pill amber">★ ${esc(item.priority)}</span>
            </div>
          </div>
        </div>
      </td>
      <td class="selling-cell">
        <div class="selling-headline ${isAutoSelling(selling) ? "auto" : ""}">
          <span class="rank-pill">${esc(selling.rank || 1)}</span>
          <span class="selling-title-text">${esc(selling.headline)}</span>
        </div>
        <div class="selling-meta-row">
          ${sellingAutoBadge(selling)}
          ${sellingSignalTags(selling)}
          ${canAutoSelling ? `<button class="mini-btn selling-auto-btn" data-selling-auto-sku="${esc(item.sku)}" type="button">重新识别</button>` : ""}
        </div>
        <div class="pill-row selling-points">${sellingPointTags(selling.points || [])}</div>
        <div class="selling-proof">${esc(selling.proof || "暂无评价依据")}</div>
      </td>
      <td class="design-cell">
        <div class="owner-row">
          <select class="design-owner-select" data-design-owner-sku="${esc(item.sku)}" ${state.auth.user ? "" : "disabled"} title="${state.auth.user ? "分配设计负责人" : "登录后可分配"}">
            ${designOwnerOptions(design.owner || item.owner)}
          </select>
          <span class="owner-chip star-chip">★ ${esc(design.score || 0)}</span>
        </div>
        <div class="progress-stack">
          ${progressLine("图", design.imagesDone, design.imagesTarget, item.sku, "image")}
          ${progressLine("剪", design.videosDone, design.videosTarget, item.sku, "video")}
        </div>
      </td>
      <td class="ad-cell">
        <div class="ad-card ${hasFacebookBinding(ad) ? "bound" : ""}">
          <strong>${money(metrics.spend)}</strong>
          <small>收入 ${money(metrics.revenue)} · ${metrics.orders || 0} 单</small>
          <div class="pill-row">${(ad.platforms || []).map((platform) => `<span class="platform-pill">${esc(platform)}</span>`).join("")}</div>
          <small class="ad-binding-line">${esc(facebookBindingText(ad))}</small>
          ${facebookSourceText(ad) ? `<small class="ad-source-line">${esc(facebookSourceText(ad))}</small>` : ""}
          <button class="quick-btn ad-bind-btn" data-facebook-bind-sku="${esc(item.sku)}" type="button">${hasFacebookBinding(ad) ? "换系列" : "绑定系列"}</button>
        </div>
      </td>
      <td class="task-cell">
        <div class="task-list">
          ${(item.weeklyTasks || []).map((task) => taskButton(item.sku, task)).join("")}
        </div>
      </td>
      <td class="note-cell">
        <div class="note-list">
          ${notes.length ? notes.map((note) => `<p><strong>${esc(note.author || "我")}</strong> ${esc(note.text)}</p>`).join("") : "<p>暂无备注</p>"}
        </div>
        <button class="quick-btn" data-note-sku="${esc(item.sku)}" type="button">+ 加备注</button>
      </td>
      <td class="profit-cell">
        <div class="profit-card ${esc(metrics.profitState)}">
          <strong>${money(metrics.profit)}</strong>
          <small>ROAS ${num(metrics.roas, 2)} · CPA ${money(metrics.cpa)}</small>
          <span class="action-badge ${toneClass(primary.tone)}">${esc(primary.label)}</span>
        </div>
      </td>
      <td class="feedback-cell">
        <div class="feedback-icons">
          ${(item.diagnosis?.actions || []).slice(0, 4).map((action) => `<span class="feedback-chip">${esc(action.label)}</span>`).join("")}
        </div>
        <div class="feedback-list">
          ${feedback.length ? feedback.map((entry) => `<p>${esc(entry.text)}</p>`).join("") : "<p>暂无反馈</p>"}
        </div>
        <button class="quick-btn" data-feedback-sku="${esc(item.sku)}" type="button">+ 加反馈</button>
      </td>
      <td class="refresh-cell">
        <button class="refresh-button" data-refresh-sku="${esc(item.sku)}" type="button">翻新 ×${refreshGap || 1}</button>
        <div class="refresh-meta">当前 ${esc(refresh.current || 0)} / 建议 ${esc(refresh.suggested || 0)}</div>
        <div class="refresh-meta">${esc(refresh.reason || "暂无翻新理由")}</div>
      </td>
    </tr>
  `;
}

function statusOptions(current) {
  const options = [
    ["main", "主推"],
    ["test", "测试"],
    ["paused", "暂停"],
    ["dropped", "下架"],
  ];
  return options.map(([value, label]) => `<option value="${value}" ${value === current ? "selected" : ""}>${label}</option>`).join("");
}

function progressLine(label, done, total, sku = "", kind = "") {
  const doneNum = Number(done || 0);
  const width = pct(done, total);
  const addTitle = kind === "image" ? "登记完成 1 张图片素材" : "登记完成 1 条剪辑素材";
  const minusTitle = kind === "image" ? "撤回 1 张图片素材" : "撤回 1 条剪辑素材";
  const disabledMinus = !state.auth.user || doneNum <= 0;
  const actions = sku && kind
    ? `<div class="design-progress-actions">
        <button class="design-progress-btn decrease" data-design-progress-sku="${esc(sku)}" data-design-progress-kind="${esc(kind)}" data-design-progress-delta="-1" type="button" title="${esc(minusTitle)}" ${disabledMinus ? "disabled" : ""}>-</button>
        <button class="design-progress-btn" data-design-progress-sku="${esc(sku)}" data-design-progress-kind="${esc(kind)}" data-design-progress-delta="1" type="button" title="${esc(addTitle)}" ${state.auth.user ? "" : "disabled"}>+</button>
      </div>`
    : "";
  return `
    <div class="progress-line">
      <span>${esc(label)}</span>
      <div class="bar"><span style="width:${width}%"></span></div>
      <strong>${esc(done || 0)}/${esc(total || 0)}</strong>
      ${actions}
    </div>`;
}

function taskButton(sku, task) {
  const done = Number(task.done || 0);
  const total = Number(task.total || 0);
  const complete = total > 0 && done >= total;
  return `
    <button class="task-pill ${complete ? "done" : ""}" data-task-sku="${esc(sku)}" data-task-id="${esc(task.id)}" data-task-done="${esc(done)}" data-task-total="${esc(total)}" type="button">
      <span>${esc(task.label)}</span>
      <strong>${esc(done)}/${esc(total)}</strong>
    </button>`;
}

function kpiCard(label, value, note = "") {
  return `<article class="workspace-kpi"><span>${esc(label)}</span><strong>${esc(value)}</strong><small>${esc(note)}</small></article>`;
}

function emptyCard(text) {
  return `<div class="empty-card">${esc(text)}</div>`;
}

function renderMaterials(items) {
  const imageDone = items.reduce((sum, item) => sum + Number(item.design?.imagesDone || 0), 0);
  const imageTarget = items.reduce((sum, item) => sum + Number(item.design?.imagesTarget || 0), 0);
  const videoDone = items.reduce((sum, item) => sum + Number(item.design?.videosDone || 0), 0);
  const videoTarget = items.reduce((sum, item) => sum + Number(item.design?.videosTarget || 0), 0);
  const materialGap = items.reduce((sum, item) => sum + Number(item.materialGap || 0), 0);
  const refreshGap = items.reduce((sum, item) => {
    const refresh = item.refresh || {};
    return sum + Math.max(Number(refresh.suggested || 0) - Number(refresh.current || 0), 0);
  }, 0);

  $("#material-kpis").innerHTML = [
    kpiCard("图片交付", `${imageDone}/${imageTarget}`, `缺口 ${Math.max(imageTarget - imageDone, 0)}`),
    kpiCard("剪辑交付", `${videoDone}/${videoTarget}`, `缺口 ${Math.max(videoTarget - videoDone, 0)}`),
    kpiCard("素材总缺口", materialGap, "图 + 剪辑"),
    kpiCard("翻新缺口", refreshGap, "建议补新角度"),
  ].join("");

  const sorted = [...items].sort((a, b) => (b.materialGap || 0) - (a.materialGap || 0));
  $("#material-review-list").innerHTML = sorted.length
    ? sorted.map(renderMaterialCard).join("")
    : emptyCard("当前筛选下没有 SKU");
}

function renderMaterialCard(item) {
  const design = item.design || {};
  const refresh = item.refresh || {};
  const refreshGap = Math.max(Number(refresh.suggested || 0) - Number(refresh.current || 0), 0);
  const autoReview = renderMaterialAutoReview(item);
  return `
    <article class="review-card">
      <button class="review-image-btn" data-preview-image="${esc(item.image)}" data-preview-title="${esc(item.title)}" type="button" aria-label="放大查看 ${esc(item.title)}">
        <img src="${esc(item.image)}" alt="${esc(item.title)}" />
      </button>
      <div>
        <h3>${esc(item.title)}</h3>
        <p>${esc(design.notes || refresh.reason || "暂无素材备注")}</p>
        ${reviewMeter("图片", design.imagesDone, design.imagesTarget)}
        ${reviewMeter("剪辑", design.videosDone, design.videosTarget)}
        <div class="review-actions">
          <span class="action-badge ${item.materialGap > 0 ? "warn" : "good"}">缺口 ${esc(item.materialGap || 0)}</span>
          <span class="action-badge ${refreshGap > 0 ? "info" : "muted"}">翻新 ${esc(refreshGap)}</span>
          <button class="quick-btn" data-open-sku="${esc(item.sku)}" type="button">查看 SKU</button>
        </div>
        ${autoReview}
      </div>
    </article>
  `;
}

function renderMaterialAutoReview(item) {
  const actions = (item.diagnosis?.actions || []).filter((action) => action.type !== "watch").slice(0, 4);
  const suggestions = item.recommendedTasks || [];
  if (!actions.length && !suggestions.length) return "";
  return `
    <div class="auto-review-box">
      <div class="auto-review-head">
        <strong>自动复盘</strong>
        ${suggestions.length ? `<button class="mini-btn" data-suggested-task-sku="${esc(item.sku)}" type="button">补入任务</button>` : `<span>暂无新任务</span>`}
      </div>
      ${actions.length ? `<ul>${actions.map((action) => `<li><span class="action-badge ${toneClass(action.tone)}">${esc(action.label)}</span><p>${esc(action.reason)}</p></li>`).join("")}</ul>` : ""}
      ${suggestions.length ? `<div class="suggestion-chip-row">${suggestions.slice(0, 4).map((task) => `<span>${esc(task.label)} ×${esc(task.total || 1)}</span>`).join("")}</div>` : ""}
    </div>
  `;
}

function reviewMeter(label, done, total) {
  return `
    <div class="review-meter">
      <span>${esc(label)}</span>
      <div class="bar"><span style="width:${pct(done, total)}%"></span></div>
      <strong>${esc(done || 0)}/${esc(total || 0)}</strong>
    </div>`;
}

function renderFeedback(items) {
  const feedbackEntries = items.flatMap((item) =>
    (item.feedback || []).map((entry) => ({ item, entry }))
  );
  const missing = items.filter((item) => !(item.feedback || []).length);
  const stopOrLoss = items.filter((item) => ["stop", "loss"].includes(item.diagnosis?.primary?.type));
  const scale = items.filter((item) => (item.diagnosis?.actions || []).some((action) => action.type === "scale"));

  $("#feedback-kpis").innerHTML = [
    kpiCard("已有反馈", feedbackEntries.length, `${items.length} 个 SKU`),
    kpiCard("缺反馈 SKU", missing.length, "需要投手补复盘"),
    kpiCard("止损/亏损", stopOrLoss.length, "优先处理"),
    kpiCard("放量线索", scale.length, "可复制或加预算"),
  ].join("");

  $("#feedback-stream").innerHTML = feedbackEntries.length
    ? feedbackEntries.map(({ item, entry }) => renderFeedbackCard(item, entry)).join("")
    : emptyCard("当前没有投放反馈，建议先从亏损 SKU 补起");

  const watchItems = [...missing, ...stopOrLoss]
    .filter((item, index, arr) => arr.findIndex((candidate) => candidate.sku === item.sku) === index)
    .slice(0, 12);
  $("#feedback-watch-list").innerHTML = watchItems.length
    ? watchItems.map(renderFeedbackWatchCard).join("")
    : emptyCard("当前没有待补反馈或重点风险");
}

function renderFeedbackCard(item, entry) {
  const primary = item.diagnosis?.primary || {};
  return `
    <article class="stack-card">
      <div class="stack-card-head">
        <h4>${esc(item.title)}</h4>
        <span class="action-badge ${toneClass(primary.tone)}">${esc(primary.label || "观察")}</span>
      </div>
      <p>${esc(entry.text)}</p>
      <div class="stack-card-meta">
        <span class="metric-pill">${esc(item.owner || "未分配")}</span>
        <span class="metric-pill blue">ROAS ${num(item.metrics?.roas, 2)}</span>
        <span class="metric-pill amber">${money(item.metrics?.profit)}</span>
      </div>
      <button class="quick-btn" data-open-sku="${esc(item.sku)}" type="button">打开详情</button>
    </article>
  `;
}

function renderFeedbackWatchCard(item) {
  const primary = item.diagnosis?.primary || {};
  return `
    <article class="stack-card">
      <div class="stack-card-head">
        <h4>${esc(item.title)}</h4>
        <span class="action-badge ${toneClass(primary.tone)}">${esc(primary.label || "补反馈")}</span>
      </div>
      <p>${esc(primary.reason || "缺少投放反馈，需要补充复盘。")}</p>
      <div class="stack-card-meta">
        <span class="metric-pill">${esc(item.sku)}</span>
        <span class="metric-pill blue">${money(item.metrics?.spend)} 花费</span>
      </div>
      <button class="quick-btn" data-feedback-sku="${esc(item.sku)}" type="button">+ 加反馈</button>
    </article>
  `;
}

function renderTasks(items) {
  const allTasks = items.flatMap((item) =>
    (item.weeklyTasks || []).map((task) => ({ item, task }))
  );
  const suggestedTasks = items.flatMap((item) =>
    (item.recommendedTasks || []).map((task) => ({ item, task }))
  );
  const openTasks = allTasks.filter(({ task }) => Number(task.done || 0) < Number(task.total || 0));
  const doneTasks = allTasks.filter(({ task }) => Number(task.total || 0) > 0 && Number(task.done || 0) >= Number(task.total || 0));
  const priorityItems = items.filter((item) => item.taskStats?.open || (item.recommendedTasks || []).length || ["stop", "material", "refresh", "creative", "landing"].includes(item.diagnosis?.primary?.type));

  $("#task-kpis").innerHTML = [
    kpiCard("任务总数", allTasks.length, "当前筛选"),
    kpiCard("未完成", openTasks.length, "点击任务可推进"),
    kpiCard("已完成", doneTasks.length, "本周交付"),
    kpiCard("系统建议", suggestedTasks.length, "可一键补入"),
  ].join("");

  $("#task-suggestion-list").innerHTML = suggestedTasks.length
    ? suggestedTasks.map(({ item, task }) => renderSuggestedTaskCard(item, task)).join("")
    : emptyCard("当前没有新的系统建议");
  $("#task-open-list").innerHTML = openTasks.length
    ? openTasks.map(({ item, task }) => renderTaskCard(item, task)).join("")
    : emptyCard("当前没有未完成任务");
  $("#task-done-list").innerHTML = doneTasks.length
    ? doneTasks.map(({ item, task }) => renderTaskCard(item, task)).join("")
    : emptyCard("当前没有已完成任务");
  $("#task-priority-list").innerHTML = priorityItems.length
    ? priorityItems.map(renderPriorityTaskCard).join("")
    : emptyCard("当前没有优先任务");
}

function renderSuggestedTaskCard(item, task) {
  return `
    <article class="stack-card suggested-task-card">
      <div class="stack-card-head">
        <h4>${esc(task.label)}</h4>
        <span class="action-badge ${toneClass(task.tone)}">建议</span>
      </div>
      <p>${esc(item.title)}</p>
      <p>${esc(task.reason || "系统根据广告表现、素材缺口或复盘缺口生成。")}</p>
      <div class="stack-card-meta">
        <span class="metric-pill">${esc(item.sku)}</span>
        <span class="metric-pill blue">任务量 ${esc(task.total || 1)}</span>
        <span class="metric-pill amber">${money(item.metrics?.spend)} 花费</span>
      </div>
      <button class="quick-btn" data-suggested-task-sku="${esc(item.sku)}" type="button">补入该 SKU</button>
    </article>
  `;
}

function renderTaskCard(item, task) {
  const done = Number(task.done || 0);
  const total = Number(task.total || 0);
  return `
    <article class="stack-card">
      <div class="stack-card-head">
        <h4>${esc(task.label)}</h4>
        <button class="task-pill ${done >= total ? "done" : ""}" data-task-sku="${esc(item.sku)}" data-task-id="${esc(task.id)}" data-task-done="${esc(done)}" data-task-total="${esc(total)}" type="button">
          <span>推进</span><strong>${esc(done)}/${esc(total)}</strong>
        </button>
      </div>
      <p>${esc(item.title)}</p>
      <div class="review-meter">
        <span>进度</span>
        <div class="bar"><span style="width:${pct(done, total)}%"></span></div>
        <strong>${esc(done)}/${esc(total)}</strong>
      </div>
      <button class="quick-btn" data-open-sku="${esc(item.sku)}" type="button">打开 SKU</button>
    </article>
  `;
}

function renderPriorityTaskCard(item) {
  const primary = item.diagnosis?.primary || {};
  const suggestions = item.recommendedTasks || [];
  return `
    <article class="stack-card">
      <div class="stack-card-head">
        <h4>${esc(item.title)}</h4>
        <span class="action-badge ${toneClass(primary.tone)}">${esc(primary.label || "优先")}</span>
      </div>
      <p>${esc(primary.reason || "需要本周跟进。")}</p>
      <div class="stack-card-meta">
        <span class="metric-pill">任务 ${esc(item.taskStats?.done || 0)}/${esc(item.taskStats?.total || 0)}</span>
        <span class="metric-pill amber">素材缺口 ${esc(item.materialGap || 0)}</span>
      </div>
      ${suggestions.length ? `<div class="suggestion-chip-row">${suggestions.slice(0, 3).map((task) => `<span>${esc(task.label)} ×${esc(task.total || 1)}</span>`).join("")}</div>` : ""}
      ${suggestions.length ? `<button class="quick-btn" data-suggested-task-sku="${esc(item.sku)}" type="button">补入建议任务</button>` : ""}
      <button class="quick-btn" data-open-sku="${esc(item.sku)}" type="button">查看详情</button>
    </article>
  `;
}

function findItem(sku) {
  return state.items.find((item) => item.sku === sku);
}

function openDrawer(sku) {
  const item = findItem(sku);
  if (!item) return;
  state.selected = item;
  $("#drawer-sku").textContent = item.sku;
  $("#drawer-title").textContent = item.title;
  const metrics = item.metrics || {};
  const actions = item.diagnosis?.actions || [];
  const notes = item.notes || [];
  const feedback = item.feedback || [];
  $("#drawer-body").innerHTML = `
    <section class="drawer-section">
      <h3>经营表现</h3>
      <div class="summary-grid" style="grid-template-columns: repeat(3, 1fr); margin:0;">
        <article class="summary-card"><span>花费</span><strong>${money(metrics.spend)}</strong><small>${metrics.orders || 0} 单</small></article>
        <article class="summary-card"><span>收入</span><strong>${money(metrics.revenue)}</strong><small>ROAS ${num(metrics.roas, 2)}</small></article>
        <article class="summary-card"><span>利润</span><strong style="color:${metrics.profit >= 0 ? "var(--teal)" : "var(--red)"}">${money(metrics.profit)}</strong><small>CPA ${money(metrics.cpa)}</small></article>
      </div>
    </section>
    <section class="drawer-section">
      <h3>动作判断</h3>
      <div class="pill-row">${actions.map((action) => `<span class="action-badge ${toneClass(action.tone)}">${esc(action.label)}</span>`).join("")}</div>
      <div class="note-list" style="margin-top:10px;">${actions.map((action) => `<p>${esc(action.reason)}</p>`).join("")}</div>
    </section>
    <section class="drawer-section">
      <h3>备注记录</h3>
      <div class="note-list drawer-history">
        ${notes.length ? notes.slice(0, 6).map((note) => `<p><strong>${esc(note.author || "我")}</strong> ${esc(note.text)}</p>`).join("") : "<p>暂无备注</p>"}
      </div>
    </section>
    <section class="drawer-section">
      <h3>投放反馈记录</h3>
      <div class="feedback-list drawer-history">
        ${feedback.length ? feedback.slice(0, 6).map((entry) => `<p>${esc(entry.text)}</p>`).join("") : "<p>暂无投放反馈</p>"}
      </div>
    </section>
    <section class="drawer-section">
      <div class="drawer-section-title">
        <h3>主卖点</h3>
        ${item.shopline ? `<button class="mini-btn selling-auto-btn" data-drawer-selling-auto="${esc(item.sku)}" type="button">重新识别</button>` : ""}
      </div>
      <p class="drawer-selling-headline">${esc(item.selling?.headline || "")}</p>
      <div class="selling-meta-row">
        ${sellingAutoBadge(item.selling || {})}
        ${sellingSignalTags(item.selling || {})}
      </div>
      <div class="pill-row" style="margin-top:10px;">${sellingPointTags(item.selling?.points || [])}</div>
      <p class="drawer-selling-proof">${esc(item.selling?.proof || "暂无评价依据")}</p>
    </section>
    <section class="drawer-section">
      <h3>快速编辑</h3>
      <div class="drawer-edit-grid">
        <label>商品名 <input id="edit-title" value="${esc(item.title)}" /></label>
        <label>负责人 <input id="edit-owner" value="${esc(item.owner)}" /></label>
        <label>设计负责人 <select id="edit-design-owner" ${state.auth.user ? "" : "disabled"}>${designOwnerOptions(item.design?.owner || item.owner)}</select></label>
        <label>优先级 <input id="edit-priority" type="number" min="1" max="5" value="${esc(item.priority || 1)}" /></label>
        <label>主卖点排序 <input id="edit-rank" type="number" min="1" max="9" value="${esc(item.selling?.rank || 1)}" /></label>
        <label class="wide">主卖点标题 <input id="edit-headline" value="${esc(item.selling?.headline || "")}" /></label>
        <label class="wide">卖点标签 <input id="edit-points" value="${esc((item.selling?.points || []).join(", "))}" /></label>
        <label class="wide">评价/证据 <input id="edit-proof" value="${esc(item.selling?.proof || "")}" /></label>
        <label>花费 <input id="edit-spend" type="number" step="0.01" value="${esc(item.ad?.spend || 0)}" /></label>
        <label>收入 <input id="edit-revenue" type="number" step="0.01" value="${esc(item.ad?.revenue || 0)}" /></label>
        <label>订单 <input id="edit-orders" type="number" value="${esc(item.ad?.orders || 0)}" /></label>
        <label>点击 <input id="edit-clicks" type="number" value="${esc(item.ad?.clicks || 0)}" /></label>
        <label>图完成 <input id="edit-images-done" type="number" value="${esc(item.design?.imagesDone || 0)}" /></label>
        <label>图目标 <input id="edit-images-target" type="number" value="${esc(item.design?.imagesTarget || 0)}" /></label>
        <label>剪完成 <input id="edit-videos-done" type="number" value="${esc(item.design?.videosDone || 0)}" /></label>
        <label>剪目标 <input id="edit-videos-target" type="number" value="${esc(item.design?.videosTarget || 0)}" /></label>
        <label>成本 <input id="edit-product-cost" type="number" step="0.01" value="${esc(item.ad?.productCost || 0)}" /></label>
        <label>运费 <input id="edit-shipping" type="number" step="0.01" value="${esc(item.ad?.shipping || 0)}" /></label>
        <label>手续费 <input id="edit-fees" type="number" step="0.01" value="${esc(item.ad?.fees || 0)}" /></label>
        <label>翻新建议 <input id="edit-refresh-suggested" type="number" value="${esc(item.refresh?.suggested || 0)}" /></label>
        <label class="wide">投放系列 <input id="edit-top-campaign" value="${esc(item.ad?.topCampaign || "")}" /></label>
        <label class="wide">翻新理由 <input id="edit-refresh-reason" value="${esc(item.refresh?.reason || "")}" /></label>
      </div>
      <button class="primary-btn" data-drawer-save="${esc(item.sku)}" type="button" style="margin-top:12px;">保存编辑</button>
    </section>
    <section class="drawer-section">
      <h3>新增备注</h3>
      <textarea id="drawer-note-input" placeholder="记录商品、设计、投放、承接页或复盘信息"></textarea>
      <button class="primary-btn" data-drawer-note="${esc(item.sku)}" type="button" style="margin-top:10px;">保存备注</button>
    </section>
    <section class="drawer-section">
      <h3>新增投放反馈</h3>
      <textarea id="drawer-feedback-input" placeholder="例如：点击高但加购低，先换首屏卖点"></textarea>
      <button class="primary-btn" data-drawer-feedback="${esc(item.sku)}" type="button" style="margin-top:10px;">保存反馈</button>
    </section>
  `;
  drawer.hidden = false;
}

async function api(path, options = {}) {
  const headers = options.body instanceof FormData
    ? { ...(options.headers || {}) }
    : { "Content-Type": "application/json", ...(options.headers || {}) };
  const response = await fetch(path, {
    ...options,
    headers,
  });
  const raw = await response.text();
  let payload;
  try {
    payload = raw ? JSON.parse(raw) : {};
  } catch (error) {
    const preview = raw.replace(/\s+/g, " ").slice(0, 220);
    const serviceError = new Error(`服务返回异常（HTTP ${response.status}）：${preview || "空响应"}`);
    serviceError.status = response.status;
    serviceError.path = path;
    throw serviceError;
  }
  if (!payload.ok) {
    const remoteError = typeof payload.error === "string"
      ? payload.error.trim()
      : payload.error && typeof payload.error === "object"
      ? (payload.error.message || payload.error.detail || JSON.stringify(payload.error))
      : "";
    const requestId = String(payload.requestId || "").trim();
    const fallback = `请求失败（HTTP ${response.status}，接口 ${path}）`;
    const error = new Error(remoteError || fallback);
    error.status = response.status;
    error.path = path;
    error.requestId = requestId;
    if (requestId) error.message = `${error.message}（错误编号：${requestId}）`;
    throw error;
  }
  return payload;
}

async function patchItem(sku, payload) {
  await api(`/api/sku-board/items/${encodeURIComponent(sku)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
  await loadBoard();
}

async function postAction(sku, action, payload) {
  await api(`/api/sku-board/items/${encodeURIComponent(sku)}/${action}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  await loadBoard();
}

async function deleteSku(sku) {
  await api(`/api/sku-board/items/${encodeURIComponent(sku)}`, {
    method: "DELETE",
    body: JSON.stringify({}),
  });
  await loadBoard();
}

async function deleteAllSkus(confirmText) {
  await api("/api/sku-board/items", {
    method: "DELETE",
    body: JSON.stringify({ confirm: confirmText }),
  });
  await loadBoard();
}

async function addSuggestedWeeklyTasks(sku = "") {
  const payload = await api("/api/sku-board/suggested-weekly-tasks", {
    method: "POST",
    body: JSON.stringify(sku ? { sku } : {}),
  });
  await loadBoard();
  showToast(payload.message || "建议任务已补入");
}

async function assignDesignOwner(sku, owner) {
  await api(`/api/sku-board/items/${encodeURIComponent(sku)}/design-owner`, {
    method: "POST",
    body: JSON.stringify({ owner }),
  });
  await loadBoard();
}

async function updateDesignProgress(sku, kind, delta = 1) {
  if (!state.auth.user) {
    showToast("请先登录后再更新素材进度");
    openLoginDialog();
    return;
  }
  const payload = await api(`/api/sku-board/items/${encodeURIComponent(sku)}/design-progress`, {
    method: "POST",
    body: JSON.stringify({ kind, delta }),
  });
  await loadBoard();
  showToast(payload.message || "素材进度已更新");
}

async function syncFacebookAds() {
  if (!state.auth.user) {
    showToast("请先登录后再同步 FB 广告");
    openLoginDialog();
    return;
  }
  const button = $("#sync-facebook-btn");
  const range = $("#facebook-range-select").value || "last_7d";
  const original = button.textContent;
  button.disabled = true;
  button.textContent = "同步中...";
  try {
    const payload = await api("/api/sku-board/facebook-ads-sync", {
      method: "POST",
      body: JSON.stringify({ range, refresh: true }),
    });
    await loadBoard();
    showToast(`FB 同步完成：更新 ${payload.updated || 0} 个商品，匹配 ${payload.matchedAds || 0} 条广告`);
    if (payload.warning) window.setTimeout(() => showToast(payload.warning), 500);
  } finally {
    button.disabled = false;
    button.textContent = original;
  }
}

function closeFacebookBindingDialog() {
  const dialog = $("#facebook-binding-dialog");
  if (dialog.open) dialog.close();
}

async function openFacebookBindingDialog(sku) {
  if (!state.auth.user) {
    showToast("请先登录后再绑定 FB 系列");
    openLoginDialog();
    return;
  }
  if (!canManageFacebookAds()) {
    showToast("只有管理员、运营或选品可以绑定 FB 系列");
    return;
  }
  state.facebookBinding.sku = sku;
  state.facebookBinding.query = "";
  $("#facebook-binding-search").value = "";
  $("#facebook-binding-dialog").showModal();
  renderFacebookBindingDialog(true);
  if (!state.facebookBinding.loaded) {
    await loadFacebookCampaignOptions(false);
  } else {
    renderFacebookBindingDialog();
  }
}

async function loadFacebookCampaignOptions(refresh = false) {
  const range = $("#facebook-range-select").value || state.facebookBinding.range || "last_7d";
  state.facebookBinding.loading = true;
  state.facebookBinding.range = range;
  renderFacebookBindingDialog(true);
  try {
    const params = new URLSearchParams({ range });
    if (refresh) params.set("refresh", "true");
    const payload = await api(`/api/sku-board/facebook-campaigns?${params.toString()}`);
    state.facebookBinding.accounts = payload.accounts || [];
    state.facebookBinding.campaigns = payload.campaigns || [];
    state.facebookBinding.loaded = true;
    if (payload.warning) showToast(payload.warning);
  } finally {
    state.facebookBinding.loading = false;
    renderFacebookBindingDialog();
  }
}

function currentFacebookBindingItem() {
  return findItem(state.facebookBinding.sku) || {};
}

function filteredFacebookCampaigns(accountId) {
  const query = state.facebookBinding.query.trim().toLowerCase();
  return (state.facebookBinding.campaigns || []).filter((campaign) => {
    if (accountId && campaign.accountId !== accountId) return false;
    if (!query) return true;
    return [campaign.campaignName, campaign.campaignId, campaign.accountName, campaign.accountId]
      .join(" ")
      .toLowerCase()
      .includes(query);
  });
}

function campaignOptionLabel(campaign) {
  return `${campaign.campaignName} · ${money(campaign.spend)} · ${campaign.orders || 0} 单 · ROAS ${num(campaign.roas, 2)}`;
}

function renderFacebookBindingDialog(loading = false) {
  const dialog = $("#facebook-binding-dialog");
  if (!dialog?.open) return;
  const item = currentFacebookBindingItem();
  const ad = item.ad || {};
  const binding = facebookBinding(ad);
  $("#facebook-binding-subtitle").textContent = item.sku ? `${item.title} · ${item.sku}` : "选择广告户和对应系列";
  $("#facebook-binding-current").textContent = hasFacebookBinding(ad)
    ? `当前绑定：${facebookBindingText(ad)}`
    : "当前未绑定系列，FB 同步会退回自动匹配。";

  const accountSelect = $("#facebook-binding-account");
  const previousAccount = accountSelect.value || binding.accountId || "";
  const accounts = state.facebookBinding.accounts || [];
  accountSelect.innerHTML = `<option value="">全部广告户</option>${accounts
    .map((account) => `<option value="${esc(account.accountId)}" ${account.accountId === previousAccount ? "selected" : ""}>${esc(account.accountName)} · ${esc(account.accountId)} · ${account.campaigns || 0} 系列</option>`)
    .join("")}`;
  accountSelect.value = accounts.some((account) => account.accountId === previousAccount) ? previousAccount : "";

  const campaignSelect = $("#facebook-binding-campaign");
  const previousCampaign = campaignSelect.value || (binding.accountId ? `${binding.accountId}::${binding.campaignId || binding.campaignName}`.toLowerCase() : "");
  const campaigns = filteredFacebookCampaigns(accountSelect.value);
  campaignSelect.innerHTML = campaigns.length
    ? campaigns.map((campaign) => `<option value="${esc(campaign.key)}" ${campaign.key === previousCampaign ? "selected" : ""}>${esc(campaignOptionLabel(campaign))}</option>`).join("")
    : `<option value="">${loading || state.facebookBinding.loading ? "正在读取系列..." : "没有可选系列"}</option>`;
  if (campaigns.some((campaign) => campaign.key === previousCampaign)) campaignSelect.value = previousCampaign;

  renderFacebookBindingPreview();
}

function selectedFacebookCampaign() {
  const key = $("#facebook-binding-campaign").value;
  return (state.facebookBinding.campaigns || []).find((campaign) => campaign.key === key);
}

function renderFacebookBindingPreview() {
  const campaign = selectedFacebookCampaign();
  const preview = $("#facebook-binding-preview");
  if (!campaign) {
    preview.innerHTML = `<div class="empty-card">请选择一个系列</div>`;
    return;
  }
  preview.innerHTML = `
    <article class="facebook-campaign-preview">
      <span class="panel-kicker">${esc(campaign.accountName)} · ${esc(campaign.accountId)}</span>
      <h3>${esc(campaign.campaignName)}</h3>
      <div class="stack-card-meta">
        <span class="metric-pill blue">${money(campaign.spend)} 花费</span>
        <span class="metric-pill">${esc(campaign.orders || 0)} 单</span>
        <span class="metric-pill amber">ROAS ${num(campaign.roas, 2)}</span>
        <span class="metric-pill">${esc(campaign.ads || 0)} 条广告</span>
      </div>
    </article>
  `;
}

async function saveFacebookBinding() {
  const campaign = selectedFacebookCampaign();
  if (!campaign) {
    showToast("请选择要绑定的 FB 系列");
    return;
  }
  await api(`/api/sku-board/items/${encodeURIComponent(state.facebookBinding.sku)}/facebook-binding`, {
    method: "POST",
    body: JSON.stringify({ binding: campaign }),
  });
  closeFacebookBindingDialog();
  await loadBoard();
  showToast("FB 系列已绑定");
}

async function clearFacebookBinding() {
  await api(`/api/sku-board/items/${encodeURIComponent(state.facebookBinding.sku)}/facebook-binding`, {
    method: "POST",
    body: JSON.stringify({ clear: true }),
  });
  closeFacebookBindingDialog();
  await loadBoard();
  showToast("FB 系列绑定已解除");
}

function showToast(message) {
  toast.textContent = message;
  toast.hidden = false;
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => {
    toast.hidden = true;
  }, 2600);
}

function setFilter(key, value) {
  state.filters[key] = value;
  loadBoard().catch((error) => showToast(error.message));
}

function setActiveView(view) {
  state.view = view || "board";
  document.body.dataset.activeView = state.view;
  const aiWorkspaceActive = state.view === "aiImages";
  const brandEyebrow = document.querySelector(".brand-lockup .eyebrow");
  const brandTitle = document.querySelector(".brand-lockup h1");
  if (brandEyebrow) brandEyebrow.textContent = aiWorkspaceActive ? "SOSOVE / AI Creative" : "SOSOVE / SKU Board";
  if (brandTitle) brandTitle.textContent = aiWorkspaceActive ? "AI 创意工坊" : "主推品作战看板";
  document.title = aiWorkspaceActive ? "SOSOVE AI 创意工坊" : "SOSOVE 主推品作战看板";
  document.querySelectorAll("[data-view]").forEach((button) => {
    const active = button.dataset.view === state.view;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  });
  if (!state.auth.user) {
    const loginGate = $("#dashboard-login-required");
    if (loginGate) loginGate.hidden = false;
    document.querySelector(".board-panel").hidden = true;
    document.querySelectorAll("[data-panel]").forEach((panel) => {
      panel.hidden = true;
    });
    return;
  }
  const showBoard = state.view === "board";
  document.querySelector(".board-panel").hidden = !showBoard;
  document.querySelectorAll("[data-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.panel !== state.view;
  });
  if (state.view === "accounts" && state.auth.user) {
    loadAccountUsers().catch((error) => showToast(error.message));
  }
  if (state.view === "metaCredentials") {
    if (state.auth.user && isAdmin()) {
      loadMetaCredentials(true).catch((error) => showToast(error.message));
    } else {
      renderMetaCredentialPanel();
    }
  }
  if (state.view === "designTasks") {
    if (state.auth.user) {
      loadDesignTasks().catch((error) => showToast(error.message));
    } else {
      renderDesignTaskPanel();
    }
  }
  if (state.view === "adLaunches") {
    if (state.auth.user) {
      loadAdLaunches(false).catch((error) => showToast(error.message));
    } else {
      renderAdLaunchPanel();
    }
  }
  if (state.view === "adAnalysis") {
    if (state.auth.user) {
      loadMetaAnalysis(false).catch((error) => {
        renderMetaAnalysisPanel();
        showToast(error.message);
      });
    } else {
      renderMetaAnalysisPanel();
    }
  }
  if (state.view === "aiImages") {
    if (state.auth.user) {
      Promise.all([
        loadAiImageConfig(true),
        isAdmin() && !state.aiImages.director?.loaded ? loadAiDirectorSettings(true) : Promise.resolve(null),
        !state.aiImages.health?.checkedAt ? loadAiImageHealth(true) : Promise.resolve(null),
      ])
        .then(() => renderAiImagePanel())
        .catch((error) => {
          renderAiImagePanel();
          showToast(error.message);
        });
    } else {
      renderAiImagePanel();
    }
  }
}

function closeSkuDialog() {
  const dialog = $("#sku-dialog");
  if (dialog.open) dialog.close();
}

function syncButtonState() {
  document.querySelectorAll("[data-action-filter]").forEach((button) => {
    const active = button.dataset.actionFilter === state.filters.action;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  });
  document.querySelectorAll("[data-jump-action]").forEach((button) => {
    button.setAttribute("aria-pressed", button.dataset.jumpAction === state.filters.action ? "true" : "false");
  });
}

function bindEvents() {
  $("#login-open-btn").addEventListener("click", openLoginDialog);
  $("#logout-btn").addEventListener("click", () => logout().catch((error) => showToast(error.message)));
  $("#login-form").addEventListener("submit", (event) => {
    event.preventDefault();
    login().catch((error) => {
      const errorEl = $("#login-error");
      errorEl.textContent = error.message;
      errorEl.hidden = false;
    });
  });
  document.querySelectorAll("[data-login-close]").forEach((button) => {
    button.addEventListener("click", closeLoginDialog);
  });
  document.querySelectorAll("[data-image-preview-close]").forEach((button) => {
    button.addEventListener("click", closeImagePreview);
  });
  document.querySelectorAll("[data-facebook-binding-close]").forEach((button) => {
    button.addEventListener("click", closeFacebookBindingDialog);
  });
  document.querySelectorAll("[data-meta-binding-close]").forEach((button) => {
    button.addEventListener("click", closeMetaBindingDialog);
  });
  document.querySelectorAll("[data-meta-system-wizard-close]").forEach((button) => {
    button.addEventListener("click", closeMetaSystemWizard);
  });
  $("#image-preview-dialog").addEventListener("click", (event) => {
    if (event.target === $("#image-preview-dialog")) closeImagePreview();
  });
  $("#facebook-binding-dialog").addEventListener("click", (event) => {
    if (event.target === $("#facebook-binding-dialog")) closeFacebookBindingDialog();
  });
  $("#meta-binding-dialog").addEventListener("click", (event) => {
    if (event.target === $("#meta-binding-dialog")) closeMetaBindingDialog();
  });
  $("#meta-system-wizard-dialog").addEventListener("click", (event) => {
    if (event.target === $("#meta-system-wizard-dialog")) closeMetaSystemWizard();
  });
  $("#facebook-binding-account").addEventListener("change", () => renderFacebookBindingDialog());
  $("#facebook-binding-campaign").addEventListener("change", renderFacebookBindingPreview);
  $("#facebook-binding-search").addEventListener("input", debounce((event) => {
    state.facebookBinding.query = event.target.value.trim();
    renderFacebookBindingDialog();
  }, 160));
  $("#facebook-binding-refresh-btn").addEventListener("click", () => loadFacebookCampaignOptions(true).catch((error) => showToast(error.message)));
  $("#facebook-binding-save-btn").addEventListener("click", () => saveFacebookBinding().catch((error) => showToast(error.message)));
  $("#facebook-binding-clear-btn").addEventListener("click", () => clearFacebookBinding().catch((error) => showToast(error.message)));
  $("[data-open-login-from-account]").addEventListener("click", openLoginDialog);
  $("[data-open-login-from-meta-credential]").addEventListener("click", openLoginDialog);
  $("[data-open-login-from-dashboard]").addEventListener("click", openLoginDialog);
  $("[data-open-login-from-design-task]").addEventListener("click", openLoginDialog);
  $("[data-open-login-from-ad-launch]").addEventListener("click", openLoginDialog);
  $("[data-open-login-from-ai-image]").addEventListener("click", openLoginDialog);
  $("#account-refresh-btn").addEventListener("click", () => loadAccountUsers().catch((error) => showToast(error.message)));
  $("#account-create-form").addEventListener("submit", (event) => {
    event.preventDefault();
    createAccount().catch((error) => showToast(error.message));
  });
  $("#account-password-form").addEventListener("submit", (event) => {
    event.preventDefault();
    changeMyPassword().catch((error) => showToast(error.message));
  });
  $("#meta-credential-refresh-btn").addEventListener("click", () => loadMetaCredentials(false).catch((error) => showToast(error.message)));
  $("#meta-system-wizard-open-btn").addEventListener("click", () => openMetaSystemWizard());
  $("#meta-binding-open-btn").addEventListener("click", () => openMetaBindingDialog());
  $("#meta-credential-existing-sync-btn").addEventListener("click", () => syncExistingMetaConnection().catch((error) => showToast(error.message)));
  $("#meta-credential-form").addEventListener("submit", (event) => {
    event.preventDefault();
    createMetaCredential().catch((error) => showToast(error.message));
  });
  $("#meta-credential-oauth-btn").addEventListener("click", () => startMetaOAuth().catch((error) => showToast(error.message)));
  $("#meta-credential-list").addEventListener("click", (event) => {
    const validateButton = event.target.closest("[data-meta-credential-validate]");
    if (validateButton) {
      validateMetaCredential(validateButton.dataset.metaCredentialValidate).catch((error) => showToast(error.message));
      return;
    }
    const syncButton = event.target.closest("[data-meta-credential-sync]");
    if (syncButton) {
      syncMetaCredential(syncButton.dataset.metaCredentialSync).catch((error) => showToast(error.message));
      return;
    }
    const bindButton = event.target.closest("[data-meta-credential-bind]");
    if (bindButton) {
      openMetaBindingDialog(bindButton.dataset.metaCredentialBind);
      return;
    }
    const activeButton = event.target.closest("[data-meta-credential-active]");
    if (activeButton) {
      setMetaCredentialActive(activeButton.dataset.metaCredentialActive, activeButton.dataset.metaCredentialNextActive === "true").catch((error) => showToast(error.message));
      return;
    }
    const deleteButton = event.target.closest("[data-meta-credential-delete]");
    if (deleteButton) {
      deleteMetaCredential(deleteButton.dataset.metaCredentialDelete, deleteButton.dataset.metaCredentialName).catch((error) => showToast(error.message));
    }
  });
  $("#meta-binding-credential").addEventListener("change", (event) => {
    state.metaCredentials.bindingCredentialId = event.target.value;
    state.metaCredentials.bindingBusinessId = "";
    state.metaCredentials.bindingAccountId = "";
    renderMetaBindingDialog();
  });
  $("#meta-binding-business").addEventListener("change", (event) => {
    state.metaCredentials.bindingBusinessId = event.target.value;
    state.metaCredentials.bindingAccountId = "";
    renderMetaBindingDialog();
  });
  $("#meta-binding-account").addEventListener("change", (event) => {
    state.metaCredentials.bindingAccountId = event.target.value;
    renderMetaBindingDialog();
  });
  $("#meta-binding-save-btn").addEventListener("click", () => saveMetaBinding().catch((error) => showToast(error.message)));
  $("#meta-system-wizard-form").addEventListener("submit", (event) => createSystemCredentialFromWizard(event).catch((error) => showToast(error.message)));
  $("#meta-system-wizard-personal").addEventListener("change", (event) => {
    const sourceCredentialId = event.target.value;
    const detail = metaWizardDetail(sourceCredentialId);
    state.metaCredentials.systemWizard = {
      sourceCredentialId,
      businessId: detail.businesses?.[0]?.id || "",
      accountIds: metaWizardAccounts(detail, detail.businesses?.[0]?.id || "").map((item) => item.accountId),
      pageIds: (detail.pages || []).map((item) => item.id),
    };
    renderMetaSystemWizard();
  });
  $("#meta-system-wizard-business").addEventListener("change", (event) => {
    const wizard = state.metaCredentials.systemWizard;
    wizard.businessId = event.target.value;
    wizard.accountIds = metaWizardAccounts(metaWizardDetail(wizard.sourceCredentialId), wizard.businessId).map((item) => item.accountId);
    renderMetaSystemWizard();
  });
  $("#meta-system-account-all").addEventListener("change", (event) => {
    const wizard = state.metaCredentials.systemWizard;
    const accounts = metaWizardAccounts(metaWizardDetail(wizard.sourceCredentialId), wizard.businessId);
    wizard.accountIds = event.target.checked ? accounts.map((item) => item.accountId) : [];
    renderMetaSystemWizard();
  });
  $("#meta-system-page-all").addEventListener("change", (event) => {
    const wizard = state.metaCredentials.systemWizard;
    const pages = metaWizardDetail(wizard.sourceCredentialId).pages || [];
    wizard.pageIds = event.target.checked ? pages.map((item) => item.id) : [];
    renderMetaSystemWizard();
  });
  $("#meta-system-wizard-accounts").addEventListener("change", (event) => {
    const input = event.target.closest("[data-meta-system-account]");
    if (input) setMetaWizardSelection("account", input.dataset.metaSystemAccount, input.checked);
  });
  $("#meta-system-wizard-pages").addEventListener("change", (event) => {
    const input = event.target.closest("[data-meta-system-page]");
    if (input) setMetaWizardSelection("page", input.dataset.metaSystemPage, input.checked);
  });
  window.addEventListener("message", (event) => {
    if (event.origin !== window.location.origin || event.data?.type !== "sku-board-meta-oauth") return;
    if (event.data.ok) {
      loadMetaCredentials(true).then(() => showToast("个人 Meta 授权已完成")).catch((error) => showToast(error.message));
    } else {
      showToast("Meta 授权失败，请查看授权窗口提示");
    }
  });
  $("#account-users-list").addEventListener("click", (event) => {
    const resetButton = event.target.closest("[data-account-reset]");
    if (resetButton) {
      resetAccountPassword(resetButton.dataset.accountReset).catch((error) => showToast(error.message));
      return;
    }
    const activeButton = event.target.closest("[data-account-active]");
    if (activeButton) {
      const active = activeButton.dataset.accountNextActive === "true";
      setAccountActive(activeButton.dataset.accountActive, active).catch((error) => showToast(error.message));
      return;
    }
    const deleteButton = event.target.closest("[data-account-delete]");
    if (deleteButton) {
      const username = deleteButton.dataset.accountDelete;
      const name = deleteButton.dataset.accountDeleteName || username;
      if (!window.confirm(`确定删除这个账号吗？\n${name}（${username}）\n删除后这个账号不能再登录。`)) return;
      deleteAccount(username).catch((error) => showToast(error.message));
    }
  });
  $("#design-task-refresh-btn").addEventListener("click", () => loadDesignTasks().then(() => showToast("设计任务已刷新")).catch((error) => showToast(error.message)));
  $("#design-task-form").addEventListener("submit", (event) => createDesignTask(event).catch((error) => showToast(error.message)));
  $("#design-task-product").addEventListener("change", prefillDesignTaskFromProduct);
  $("#design-task-status-filter").addEventListener("change", (event) => setDesignTaskFilter("status", event.target.value));
  $("#design-task-owner-filter").addEventListener("change", (event) => setDesignTaskFilter("owner", event.target.value));
  $("#design-task-search").addEventListener("input", debounce((event) => setDesignTaskFilter("q", event.target.value.trim()), 180));
  $("#design-task-list").addEventListener("click", (event) => {
    const saveButton = event.target.closest("[data-design-task-save]");
    if (saveButton) {
      saveDesignTask(saveButton.dataset.designTaskSave).catch((error) => showToast(error.message));
      return;
    }
    const deleteButton = event.target.closest("[data-design-task-delete]");
    if (deleteButton) {
      const title = deleteButton.dataset.designTaskTitle || deleteButton.dataset.designTaskDelete;
      if (!window.confirm(`确定删除这个设计任务吗？\n${title}`)) return;
      deleteDesignTask(deleteButton.dataset.designTaskDelete).catch((error) => showToast(error.message));
    }
  });
  $("#task-auto-fill-btn").addEventListener("click", () => addSuggestedWeeklyTasks("").catch((error) => showToast(error.message)));
  $("#ai-image-refresh-btn").addEventListener("click", () => Promise.all([
    loadAdLaunches(true),
    loadAiImageHealth(true),
    isAdmin() ? loadAiDirectorSettings(true) : Promise.resolve(null),
  ]).then(() => showToast("AI 生图配置已刷新")).catch((error) => showToast(error.message)));
  $("#ai-image-recover-btn").addEventListener("click", () => recoverRecentAiImageSuite(false).catch(() => {}));
  $("#ai-image-health-btn").addEventListener("click", () => loadAiImageHealth(false));
  $("#ai-image-node-list").addEventListener("click", (event) => {
    const button = event.target.closest("[data-ai-image-node-check]");
    if (!button) return;
    loadAiImageHealth(false, button.dataset.aiImageNodeCheck || "").catch((error) => showToast(error.message));
  });
  $("#ai-image-form").addEventListener("submit", (event) => generateAiImage(event).catch((error) => showToast(error.message)));
  $("#ai-image-country").addEventListener("change", (event) => setAiImageSuiteCountry(event.target.value));
  $("#ai-image-cod-hook-type").addEventListener("change", (event) => setAiImageCodHookType(event.target.value));
  $("#ai-image-new-btn").addEventListener("click", () => {
    const skill = aiImageSkillConfig();
    createAiImageConversation({ prompt: "", userIntent: "", compiledIntent: "", productSku: "", mode: "text", lockLevel: skill.defaults?.lockLevel || "strict", templateKey: skill.defaults?.templateKey || "main", suiteKey: "", suiteCountry: "KR", suitePages: [], materials: [], previewDataUrls: [], referenceImages: [], maskImage: null });
    renderAiImagePanel();
    $("#ai-image-intent").focus();
  });
  $("#ai-image-clear-btn").addEventListener("click", () => {
    clearAiImageConversations().catch((error) => showToast(error.message));
  });
  $("#ai-image-upload-btn").addEventListener("click", () => $("#ai-image-reference-file").click());
  $("#ai-image-reference-file").addEventListener("change", (event) => {
    addAiImageReferences(event.target.files || [], { role: aiImagePrimaryUploadReferenceRole() });
    event.target.value = "";
  });
  $("#ai-image-model-upload-btn")?.addEventListener("click", () => {
    const conversation = ensureAiImageConversation();
    const hasProduct = (conversation.referenceImages || []).some((reference, index) => aiImageReferenceRoleKey(reference, index) === "product");
    if (!hasProduct) {
      showToast("请先上传衣服产品图，再上传模特图片");
      return;
    }
    $("#ai-image-model-reference-file").click();
  });
  $("#ai-image-model-reference-file")?.addEventListener("change", (event) => {
    addAiImageReferences(event.target.files || [], { role: "person" });
    event.target.value = "";
  });
  $("#ai-image-usage-upload-btn")?.addEventListener("click", () => {
    const conversation = ensureAiImageConversation();
    const hasProduct = (conversation.referenceImages || []).some((reference, index) => aiImageReferenceRoleKey(reference, index) === "product");
    if (!hasProduct) {
      showToast("请先上传产品白底图，再上传当前商品的模特上身图");
      return;
    }
    $("#ai-image-usage-reference-file").click();
  });
  $("#ai-image-usage-reference-file")?.addEventListener("change", (event) => {
    addAiImageReferences(event.target.files || [], { role: "usage" });
    event.target.value = "";
  });
  $("#ai-image-style-set-upload-btn")?.addEventListener("click", () => {
    const conversation = ensureAiImageConversation();
    if (!conversation.referenceImages?.length) {
      showToast("请先上传主商品图，再添加系列风格参考");
      return;
    }
    $("#ai-image-style-set-file").click();
  });
  $("#ai-image-style-set-file")?.addEventListener("change", (event) => {
    addAiImageReferences(event.target.files || [], { role: "styleSet" });
    event.target.value = "";
  });
  $("#ai-image-mask-btn").addEventListener("click", () => $("#ai-image-mask-file").click());
  $("#ai-image-mask-file").addEventListener("change", (event) => {
    addAiImageMask(event.target.files || []);
    event.target.value = "";
  });
  $("#ai-image-reference-strip").addEventListener("click", (event) => {
    const clearButton = event.target.closest("[data-ai-reference-clear]");
    if (clearButton) {
      clearAiImageReferences();
      return;
    }
    const removeButton = event.target.closest("[data-ai-reference-remove]");
    if (removeButton) removeAiImageReference(removeButton.dataset.aiReferenceRemove);
    const removeMaskButton = event.target.closest("[data-ai-mask-remove]");
    if (removeMaskButton) removeAiImageMask();
  });
  $("#ai-image-reference-strip").addEventListener("change", (event) => {
    const roleSelect = event.target.closest("[data-ai-reference-role]");
    if (roleSelect) {
      setAiImageReferenceRole(roleSelect.dataset.aiReferenceRole, roleSelect.value);
      return;
    }
    const keywordInput = event.target.closest("[data-ai-reference-keywords]");
    if (keywordInput) setAiImageReferenceKeyword(keywordInput.dataset.aiReferenceKeywords, keywordInput.value);
  });
  $("#ai-image-settings-btn").addEventListener("click", () => {
    state.aiImages.settingsOpen = !state.aiImages.settingsOpen;
    renderAiImageForm();
    if (state.aiImages.settingsOpen && isAdmin() && !state.aiImages.director?.loaded) {
      loadAiDirectorSettings(true).catch((error) => showToast(error.message));
    }
  });
  $("#ai-director-save-btn").addEventListener("click", () => saveAiDirectorSettings(false));
  $("#ai-director-test-btn").addEventListener("click", () => testAiDirectorConnection());
  ["#ai-director-base-url", "#ai-director-model", "#ai-director-timeout", "#ai-director-api-key", "#ai-director-enabled", "#ai-director-vision", "#ai-director-open-prompts", "#ai-director-review-enabled", "#ai-director-review-threshold"].forEach((selector) => {
    const field = $(selector);
    const eventName = field?.type === "checkbox" || field?.tagName === "SELECT" ? "change" : "input";
    field?.addEventListener(eventName, () => {
      const director = { ...(state.aiImages.director || {}), formDirty: true, message: "配置尚未保存", status: "unknown" };
      if (selector === "#ai-director-model") {
        director.model = field.value;
        director.fallbackModels = AI_DIRECTOR_MODELS.filter((candidate) => candidate !== field.value);
      }
      state.aiImages.director = director;
      renderAiDirectorSettings();
    });
  });
  $("#ai-image-task-list").addEventListener("click", (event) => {
    const deleteButton = event.target.closest("[data-ai-conversation-delete]");
    if (deleteButton) {
      deleteAiImageConversation(deleteButton.dataset.aiConversationDelete).catch((error) => showToast(error.message));
      return;
    }
    const taskButton = event.target.closest("[data-ai-conversation]");
    if (taskButton) setAiImageConversation(taskButton.dataset.aiConversation);
  });
  $("#ai-image-results").addEventListener("click", (event) => {
    const errorActionButton = event.target.closest("[data-ai-error-action]");
    if (errorActionButton) {
      const action = errorActionButton.dataset.aiErrorAction;
      if (action === "retry") {
        generateAiImage(new Event("submit")).catch((error) => showToast(error.message));
      } else if (action === "count-one") {
        updateAiImageConversation({ count: 1 });
        renderAiImageResults();
        showToast("已改成生成 1 张");
      } else if (action === "clear-reference") {
        clearAiImageReferences();
      } else if (action === "recover-suite") {
        recoverRecentAiImageSuite(false).catch(() => {});
      } else if (action === "fill-missing") {
        generateMissingAiImageSuitePages().catch((error) => showToast(error.message));
      }
      return;
    }
    const tagButton = event.target.closest("[data-ai-tag-index]");
    if (tagButton) {
      setAiImageResultTag(tagButton.dataset.aiTagIndex, tagButton.dataset.aiTag);
      return;
    }
    const removeMarkButton = event.target.closest("[data-ai-remove-mark-index]");
    if (removeMarkButton) {
      regenerateAiImageSuitePageWithoutMarks(removeMarkButton.dataset.aiRemoveMarkIndex).catch((error) => showToast(error.message));
      return;
    }
    const editPageButton = event.target.closest("[data-ai-edit-index]");
    if (editPageButton) {
      const editIndex = Number(editPageButton.dataset.aiEditIndex || 0);
      const editField = document.querySelector(`[data-ai-edit-prompt-index="${editIndex}"]`);
      const instruction = String(editField?.value || "").trim();
      if (!instruction) {
        showToast("请先填写这张图片需要修改的内容");
        editField?.focus();
        return;
      }
      editAiImageMaterialByPrompt(editIndex, instruction).catch((error) => showToast(error.message));
      return;
    }
    const retryPageButton = event.target.closest("[data-ai-retry-index]");
    if (retryPageButton) {
      regenerateAiImageSuitePage(retryPageButton.dataset.aiRetryIndex).catch((error) => showToast(error.message));
      return;
    }
    const previewButton = event.target.closest("[data-ai-preview-index]");
    if (previewButton) {
      previewAiImage(previewButton.dataset.aiPreviewIndex);
      return;
    }
    const downloadButton = event.target.closest("[data-ai-download-index]");
    if (downloadButton) {
      downloadAiImage(downloadButton.dataset.aiDownloadIndex).catch((error) => showToast(error.message));
      return;
    }
    const deleteImageButton = event.target.closest("[data-ai-delete-index]");
    if (deleteImageButton) {
      deleteAiImageMaterial(deleteImageButton.dataset.aiDeleteIndex).catch((error) => showToast(error.message));
      return;
    }
    const posterButton = event.target.closest("[data-ai-poster-index]");
    if (posterButton) {
      createAiPosterLayout(posterButton.dataset.aiPosterIndex).catch((error) => showToast(error.message));
      return;
    }
    const sendButton = event.target.closest("[data-ai-send-index]");
    if (sendButton) {
      sendAiImageToAdLaunch(sendButton.dataset.aiSendIndex).catch((error) => showToast(error.message));
    }
  });
  $("#ai-image-results").addEventListener("input", (event) => {
    const editField = event.target.closest("[data-ai-edit-prompt-index]");
    if (!editField) return;
    const conversation = aiImageActiveConversation();
    const material = conversation?.materials?.[Number(editField.dataset.aiEditPromptIndex || 0)];
    if (!conversation || !material) return;
    const editIndex = Number(editField.dataset.aiEditPromptIndex || 0);
    const editKey = aiImageMaterialEditPromptKey(material, editIndex, aiImageSuiteActive(conversation));
    conversation.pageEditPrompts = {
      ...(conversation.pageEditPrompts || {}),
      [editKey]: String(editField.value || "").slice(0, 360),
    };
    conversation.updatedAt = new Date().toISOString();
    persistAiImageState();
  });
  $("#ai-image-template-strip").addEventListener("click", (event) => {
    const templateButton = event.target.closest("[data-ai-template]");
    if (templateButton) applyAiImageTemplate(templateButton.dataset.aiTemplate);
  });
  $("#ai-image-quick-entry").addEventListener("click", (event) => {
    const quickButton = event.target.closest("[data-ai-quick-template]");
    if (quickButton) startAiImageQuickWorkflow(quickButton.dataset.aiQuickTemplate);
  });
  $("#ai-image-mode-strip").addEventListener("click", (event) => {
    const modeButton = event.target.closest("[data-ai-mode]");
    if (modeButton) setAiImageMode(modeButton.dataset.aiMode);
  });
  $("#ai-image-director-mode-strip").addEventListener("click", (event) => {
    const modeButton = event.target.closest("[data-ai-director-mode]");
    if (modeButton) setAiImageDirectorMode(modeButton.dataset.aiDirectorMode);
  });
  $("#ai-image-generation-profile-strip").addEventListener("click", (event) => {
    const profileButton = event.target.closest("[data-ai-generation-profile]");
    if (profileButton) setAiImageGenerationProfile(profileButton.dataset.aiGenerationProfile);
  });
  $("#ai-image-lock-strip").addEventListener("click", (event) => {
    const lockButton = event.target.closest("[data-ai-lock]");
    if (lockButton) setAiImageLockLevel(lockButton.dataset.aiLock);
  });
  $("#ai-image-size-presets").addEventListener("click", (event) => {
    const button = event.target.closest("[data-ai-size]");
    if (!button) return;
    const conversation = ensureAiImageConversation();
    conversation.size = button.dataset.aiSize;
    rebuildAiImagePromptFromSkill(conversation);
    conversation.updatedAt = new Date().toISOString();
    syncAiImageStateFromConversation(conversation);
    renderAiImageForm();
    renderAiImageSidebar();
    renderAiImageResults();
  });
  $("#ai-image-count-presets").addEventListener("click", (event) => {
    const button = event.target.closest("[data-ai-count]");
    if (!button) return;
    const conversation = ensureAiImageConversation();
    if (conversation.templateKey === "virtualTryOn") {
      showToast("模特换装/搭配固定生成 1 张完整场景图");
      return;
    }
    if (aiImageSuiteConfig(conversation)?.countConfigurable) {
      setAiImageSuiteCount(button.dataset.aiCount);
      return;
    }
    updateAiImageConversation({ count: Number(button.dataset.aiCount || 1) });
    renderAiImageResults();
  });
  $("#ai-image-product").addEventListener("change", (event) => {
    updateAiImageConversation({ productSku: event.target.value });
    prefillAiImagePrompt(false);
  });
  $("#ai-image-product-prompt-btn").addEventListener("click", () => prefillAiImagePrompt(true));
  $("#ai-image-intent").addEventListener("input", debounce((event) => {
    const conversation = ensureAiImageConversation();
    conversation.userIntent = event.target.value.trim();
    conversation.promptManuallyEdited = false;
    conversation.title = aiImageConversationTitle(conversation);
    conversation.updatedAt = new Date().toISOString();
    syncAiImageStateFromConversation(conversation);
    renderAiImageSidebar();
    renderAiImagePreflight(conversation);
    $("#ai-image-prompt-meta").textContent = `${conversation.compiledIntent === conversation.userIntent ? "已编译" : "待更新"} · ${(conversation.prompt || "").length} 字符`;
  }, 120));
  $("#ai-image-prompt").addEventListener("input", debounce((event) => {
    const conversation = ensureAiImageConversation();
    conversation.prompt = event.target.value;
    conversation.promptManuallyEdited = true;
    conversation.title = aiImageConversationTitle(conversation);
    conversation.updatedAt = new Date().toISOString();
    syncAiImageStateFromConversation(conversation);
    renderAiImageSidebar();
    renderAiImagePreflight(conversation);
    $("#ai-image-prompt-meta").textContent = `${aiImagePromptIsStructured(conversation.prompt) ? "已编辑" : "非结构化"} · ${conversation.prompt.length} 字符`;
  }, 120));
  $("#ai-image-model").addEventListener("change", (event) => {
    updateAiImageConversation({ model: event.target.value });
  });
  $("#ai-image-quality").addEventListener("change", (event) => {
    updateAiImageConversation({ quality: event.target.value });
  });
  $("#ad-launch-refresh-btn").addEventListener("click", () => loadAdLaunches(true).then(() => showToast("素材投放数据已刷新")).catch((error) => showToast(error.message)));
  $("#ad-launch-form").addEventListener("submit", (event) => createAdLaunch(event).catch((error) => showToast(error.message)));
  $("#ad-launch-form").addEventListener("input", debounce(updateAdLaunchModeFields, 120));
  $("#ad-launch-form").addEventListener("change", updateAdLaunchModeFields);
  document.querySelectorAll("[data-ad-launch-step-jump]").forEach((button) => {
    button.addEventListener("click", () => setAdLaunchStep(button.dataset.adLaunchStepJump));
  });
  $("#ad-launch-prev-btn").addEventListener("click", () => setAdLaunchStep(state.adLaunches.step - 1));
  $("#ad-launch-next-btn").addEventListener("click", () => setAdLaunchStep(state.adLaunches.step + 1));
  document.querySelectorAll("[data-ad-launch-material-tab]").forEach((button) => {
    button.addEventListener("click", () => setAdLaunchMaterialMode(button.dataset.adLaunchMaterialTab));
  });
  $("#ad-launch-upload-btn").addEventListener("click", () => $("#ad-launch-file").click());
  $("#ad-launch-library-btn").addEventListener("click", pickAdLaunchMaterialFromLibrary);
  $("#ad-launch-ai-generate-btn").addEventListener("click", () => generateAdLaunchAiImage().catch((error) => showToast(error.message)));
  $("#ad-launch-product").addEventListener("change", prefillAdLaunchFromProduct);
  $("#ad-launch-file").addEventListener("change", () => uploadAdLaunchMaterial().catch((error) => showToast(error.message)));
  $("#ad-launch-account").addEventListener("change", () => {
    renderAdLaunchTargetSelects($("#ad-launch-account").value, "", "");
    renderAdLaunchIdentitySelects();
    updateAdLaunchModeFields();
  });
  $("#ad-launch-campaign").addEventListener("change", () => {
    renderAdLaunchTargetSelects($("#ad-launch-account").value, $("#ad-launch-campaign").value, "");
    updateAdLaunchModeFields();
  });
  $("#ad-launch-campaign-mode").addEventListener("change", updateAdLaunchModeFields);
  $("#ad-launch-adset-mode").addEventListener("change", updateAdLaunchModeFields);
  $("#ad-launch-name").addEventListener("input", debounce(updateAdLaunchModeFields, 120));
  $("#ad-launch-countries").addEventListener("input", debounce(updateAdLaunchModeFields, 120));
  $("#ad-launch-range").addEventListener("change", (event) => {
    state.adLaunches.filters.range = event.target.value;
    loadAdLaunches(false).catch((error) => showToast(error.message));
  });
  $("#ad-launch-search").addEventListener("input", debounce((event) => {
    state.adLaunches.filters.q = event.target.value.trim();
    renderAdLaunchList();
  }, 160));
  $("#ad-launch-list").addEventListener("click", (event) => {
    const publishButton = event.target.closest("[data-ad-launch-publish]");
    if (publishButton) {
      publishAdLaunch(publishButton.dataset.adLaunchPublish).catch((error) => showToast(error.message));
      return;
    }
    const activateButton = event.target.closest("[data-ad-launch-activate]");
    if (activateButton) {
      setAdLaunchStatus(activateButton.dataset.adLaunchActivate, "ACTIVE").catch((error) => showToast(error.message));
      return;
    }
    const pauseButton = event.target.closest("[data-ad-launch-pause]");
    if (pauseButton) {
      setAdLaunchStatus(pauseButton.dataset.adLaunchPause, "PAUSED").catch((error) => showToast(error.message));
      return;
    }
    const deleteButton = event.target.closest("[data-ad-launch-delete]");
    if (deleteButton) {
      deleteAdLaunch(deleteButton.dataset.adLaunchDelete).catch((error) => showToast(error.message));
    }
  });
  $("#ad-launch-form").addEventListener("click", (event) => {
    if (event.target.closest("[data-ad-launch-clear-material]")) {
      clearAdLaunchMaterial();
    }
  });
  $("#meta-analysis-refresh-btn").addEventListener("click", () => loadMetaAnalysis(true).then(() => showToast("广告分析已刷新")).catch((error) => showToast(error.message)));
  $("#meta-analysis-range").addEventListener("change", (event) => {
    state.metaAnalysis.filters.range = event.target.value;
    state.metaAnalysis.loaded = false;
    loadMetaAnalysis(true).catch((error) => showToast(error.message));
  });
  $("#meta-analysis-use-purchase").addEventListener("change", (event) => {
    state.metaAnalysis.settings.usePlatformPurchase = event.target.checked;
    state.metaAnalysis.loaded = false;
    loadMetaAnalysis(true).catch((error) => showToast(error.message));
  });
  $("#meta-analysis-account-filter").addEventListener("change", (event) => {
    state.metaAnalysis.filters.accountId = event.target.value;
    renderMetaAnalysisPanel();
  });
  $("#meta-analysis-business-filter").addEventListener("change", (event) => {
    state.metaAnalysis.filters.businessId = event.target.value;
    state.metaAnalysis.filters.accountId = "";
    renderMetaAnalysisPanel();
  });
  $("#meta-analysis-search").addEventListener("input", debounce((event) => {
    state.metaAnalysis.filters.q = event.target.value.trim();
    renderMetaAnalysisTable();
  }, 160));
  $("#meta-analysis-action-filter").addEventListener("change", (event) => {
    state.metaAnalysis.filters.action = event.target.value;
    renderMetaAnalysisTable();
  });
  $("#meta-analysis-conclusions").addEventListener("click", (event) => {
    const button = event.target.closest("[data-meta-analysis-action]");
    if (!button) return;
    state.metaAnalysis.filters.action = button.dataset.metaAnalysisAction || "";
    renderMetaAnalysisPanel();
  });
  $("#meta-analysis-accounts").addEventListener("click", (event) => {
    const button = event.target.closest("[data-meta-analysis-account]");
    if (!button) return;
    const accountId = button.dataset.metaAnalysisAccount || "";
    state.metaAnalysis.filters.accountId = state.metaAnalysis.filters.accountId === accountId ? "" : accountId;
    renderMetaAnalysisPanel();
  });
  $("#search-input").addEventListener("input", debounce((event) => setFilter("q", event.target.value.trim()), 220));
  $("#status-filter").addEventListener("change", (event) => setFilter("status", event.target.value));
  $("#owner-filter").addEventListener("change", (event) => setFilter("owner", event.target.value));
  $("#profit-filter").addEventListener("change", (event) => setFilter("profit", event.target.value));
  $("#action-filter").addEventListener("change", (event) => setFilter("action", event.target.value));
  $("#clear-filter-btn").addEventListener("click", () => {
    state.filters = { q: "", status: "", owner: "", profit: "", action: "" };
    $("#search-input").value = "";
    $("#status-filter").value = "";
    $("#owner-filter").value = "";
    $("#profit-filter").value = "";
    $("#action-filter").value = "";
    syncButtonState();
    loadBoard().catch((error) => showToast(error.message));
  });
  $("#refresh-board-btn").addEventListener("click", () => loadBoard().then(() => showToast("看板已刷新")).catch((error) => showToast(error.message)));
  $("#export-csv-btn").addEventListener("click", exportCsv);
  $("#import-shopline-btn").addEventListener("click", openShoplineDialog);
  $("#sync-facebook-btn").addEventListener("click", () => syncFacebookAds().catch((error) => showToast(error.message)));
  $("#delete-all-btn").addEventListener("click", async () => {
    const confirmText = window.prompt("这会删除看板里的全部商品。请输入：删除全部");
    if (confirmText !== "删除全部") {
      showToast("已取消清空商品");
      return;
    }
    try {
      const before = state.items.length;
      await deleteAllSkus(confirmText);
      drawer.hidden = true;
      showToast(`已删除全部商品：${before} 个`);
    } catch (error) {
      showToast(error.message);
    }
  });
  $("#shopline-refresh-btn").addEventListener("click", () => loadShoplineProducts().catch((error) => showToast(error.message)));
  $("#shopline-select-all-btn").addEventListener("click", () => {
    filteredShoplineProducts().forEach((product) => state.shopline.selected.add(product.key));
    renderShoplineProducts();
  });
  $("#shopline-import-selected-btn").addEventListener("click", () => importSelectedShoplineProducts());
  $("#shopline-search").addEventListener("input", (event) => {
    state.shopline.query = event.target.value;
    renderShoplineProducts();
  });
  $("#shopline-status-filter").addEventListener("change", (event) => {
    state.shopline.status = event.target.value;
    state.shopline.selected = new Set(
      Array.from(state.shopline.selected).filter((key) => {
        const product = state.shopline.products.find((item) => item.key === key);
        return product && (!state.shopline.status || product.status === state.shopline.status);
      })
    );
    renderShoplineProducts();
  });
  $("#shopline-products").addEventListener("change", (event) => {
    const checkbox = event.target.closest("[data-shopline-pick]");
    if (!checkbox) return;
    if (checkbox.checked) state.shopline.selected.add(checkbox.dataset.shoplinePick);
    else state.shopline.selected.delete(checkbox.dataset.shoplinePick);
    renderShoplineProducts();
  });
  document.querySelectorAll("[data-shopline-close]").forEach((button) => {
    button.addEventListener("click", closeShoplineDialog);
  });
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => setActiveView(button.dataset.view));
  });
  document.querySelectorAll("[data-action-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      $("#action-filter").value = button.dataset.actionFilter;
      syncButtonState();
      setFilter("action", button.dataset.actionFilter);
    });
  });
  document.querySelectorAll("[data-jump-action]").forEach((button) => {
    button.addEventListener("click", () => {
      $("#action-filter").value = button.dataset.jumpAction;
      state.filters.action = button.dataset.jumpAction;
      syncButtonState();
      setActiveView("board");
      loadBoard().catch((error) => showToast(error.message));
    });
  });
  $("#add-sku-btn").addEventListener("click", () => $("#sku-dialog").showModal());
  document.querySelectorAll("[data-dialog-close]").forEach((button) => {
    button.addEventListener("click", closeSkuDialog);
  });
  $("#sku-form").addEventListener("submit", handleSkuSubmit);
  $("#drawer-close-btn").addEventListener("click", () => {
    drawer.hidden = true;
  });
  drawer.addEventListener("click", (event) => {
    if (event.target === drawer) drawer.hidden = true;
  });
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    if (!drawer.hidden) drawer.hidden = true;
    closeSkuDialog();
    closeShoplineDialog();
    closeLoginDialog();
    closeImagePreview();
    closeMetaBindingDialog();
    closeMetaSystemWizard();
    closeFacebookBindingDialog();
  });
  tbody.addEventListener("change", handleTableChange);
  tbody.addEventListener("click", handleTableClick);
  document.querySelectorAll(".workspace-panel").forEach((panel) => {
    panel.addEventListener("click", handleWorkspaceClick);
  });
  $("#drawer-body").addEventListener("click", handleDrawerClick);
}

async function handleSkuSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const submitter = event.submitter;
  if (submitter?.value === "cancel") {
    $("#sku-dialog").close();
    return;
  }
  const data = Object.fromEntries(new FormData(form).entries());
  try {
    await api("/api/sku-board/items", { method: "POST", body: JSON.stringify(data) });
    $("#sku-dialog").close();
    form.reset();
    await loadBoard();
    showToast("SKU 已添加");
  } catch (error) {
    showToast(error.message);
  }
}

async function handleWorkspaceClick(event) {
  const actionable = event.target.closest(
    "[data-preview-image], [data-open-sku], [data-note-sku], [data-feedback-sku], [data-refresh-sku], [data-task-sku], [data-delete-sku], [data-facebook-bind-sku], [data-design-progress-sku], [data-suggested-task-sku]"
  );
  if (!actionable) return;
  await handleTableClick(event);
}

async function handleTableChange(event) {
  const designSelect = event.target.closest("[data-design-owner-sku]");
  if (designSelect) {
    if (!state.auth.user) {
      showToast("请先登录后再分配设计负责人");
      openLoginDialog();
      await loadBoard();
      return;
    }
    try {
      await assignDesignOwner(designSelect.dataset.designOwnerSku, designSelect.value);
      showToast(`已分配给 ${designSelect.value}`);
    } catch (error) {
      showToast(error.message);
      await loadBoard();
    }
    return;
  }

  const select = event.target.closest("[data-status-sku]");
  if (!select) return;
  try {
    await patchItem(select.dataset.statusSku, { status: select.value });
    showToast("状态已更新");
  } catch (error) {
    showToast(error.message);
  }
}

async function handleTableClick(event) {
  const previewButton = event.target.closest("[data-preview-image]");
  if (previewButton) {
    openImagePreview(previewButton.dataset.previewImage, previewButton.dataset.previewTitle);
    return;
  }

  const deleteButton = event.target.closest("[data-delete-sku]");
  if (deleteButton) {
    const sku = deleteButton.dataset.deleteSku;
    const title = deleteButton.dataset.deleteTitle || sku;
    if (!window.confirm(`确定删除这个商品吗？\n${title}\nSKU：${sku}`)) return;
    try {
      await deleteSku(sku);
      if (state.selected?.sku === sku) drawer.hidden = true;
      showToast("商品已删除");
    } catch (error) {
      showToast(error.message);
    }
    return;
  }

  const facebookBindButton = event.target.closest("[data-facebook-bind-sku]");
  if (facebookBindButton) {
    openFacebookBindingDialog(facebookBindButton.dataset.facebookBindSku).catch((error) => showToast(error.message));
    return;
  }

  const openButton = event.target.closest("[data-open-sku]");
  if (openButton) {
    openDrawer(openButton.dataset.openSku);
    return;
  }

  const sellingAutoButton = event.target.closest("[data-selling-auto-sku]");
  if (sellingAutoButton) {
    try {
      await postAction(sellingAutoButton.dataset.sellingAutoSku, "selling-auto", {});
      showToast("主卖点已重新识别");
    } catch (error) {
      showToast(error.message);
    }
    return;
  }

  const noteButton = event.target.closest("[data-note-sku]");
  if (noteButton) {
    const text = window.prompt("添加备注");
    if (!text) return;
    try {
      await postAction(noteButton.dataset.noteSku, "notes", { text });
      showToast("备注已保存");
    } catch (error) {
      showToast(error.message);
    }
    return;
  }

  const feedbackButton = event.target.closest("[data-feedback-sku]");
  if (feedbackButton) {
    const text = window.prompt("添加投放反馈");
    if (!text) return;
    try {
      await postAction(feedbackButton.dataset.feedbackSku, "feedback", { text });
      showToast("反馈已保存");
    } catch (error) {
      showToast(error.message);
    }
    return;
  }

  const refreshButton = event.target.closest("[data-refresh-sku]");
  if (refreshButton) {
    try {
      await postAction(refreshButton.dataset.refreshSku, "refresh", { count: 1 });
      showToast("已记录 1 组翻新");
    } catch (error) {
      showToast(error.message);
    }
    return;
  }

  const designProgressButton = event.target.closest("[data-design-progress-sku]");
  if (designProgressButton) {
    try {
      const delta = Number(designProgressButton.dataset.designProgressDelta || 1);
      await updateDesignProgress(designProgressButton.dataset.designProgressSku, designProgressButton.dataset.designProgressKind, delta);
    } catch (error) {
      showToast(error.message);
    }
    return;
  }

  const suggestedTaskButton = event.target.closest("[data-suggested-task-sku]");
  if (suggestedTaskButton) {
    try {
      await addSuggestedWeeklyTasks(suggestedTaskButton.dataset.suggestedTaskSku);
    } catch (error) {
      showToast(error.message);
    }
    return;
  }

  const taskButtonEl = event.target.closest("[data-task-sku]");
  if (taskButtonEl) {
    const done = Number(taskButtonEl.dataset.taskDone || 0);
    const total = Number(taskButtonEl.dataset.taskTotal || 0);
    const next = done >= total ? 0 : done + 1;
    try {
      await patchItem(taskButtonEl.dataset.taskSku, { taskId: taskButtonEl.dataset.taskId, done: next });
      showToast("任务进度已更新");
    } catch (error) {
      showToast(error.message);
    }
  }
}

async function handleDrawerClick(event) {
  const sellingAutoButton = event.target.closest("[data-drawer-selling-auto]");
  if (sellingAutoButton) {
    try {
      await postAction(sellingAutoButton.dataset.drawerSellingAuto, "selling-auto", {});
      openDrawer(sellingAutoButton.dataset.drawerSellingAuto);
      showToast("主卖点已重新识别");
    } catch (error) {
      showToast(error.message);
    }
    return;
  }

  const saveButton = event.target.closest("[data-drawer-save]");
  if (saveButton) {
    const sku = saveButton.dataset.drawerSave;
    const payload = {
      title: $("#edit-title").value.trim(),
      owner: $("#edit-owner").value.trim(),
      priority: Number($("#edit-priority").value || 1),
      selling: {
        rank: Number($("#edit-rank").value || 1),
        headline: $("#edit-headline").value.trim(),
        points: $("#edit-points").value.trim(),
        proof: $("#edit-proof").value.trim(),
      },
      ad: {
        spend: Number($("#edit-spend").value || 0),
        revenue: Number($("#edit-revenue").value || 0),
        orders: Number($("#edit-orders").value || 0),
        clicks: Number($("#edit-clicks").value || 0),
        productCost: Number($("#edit-product-cost").value || 0),
        shipping: Number($("#edit-shipping").value || 0),
        fees: Number($("#edit-fees").value || 0),
        topCampaign: $("#edit-top-campaign").value.trim(),
      },
      design: {
        ...(state.auth.user ? { owner: $("#edit-design-owner")?.value || "" } : {}),
        imagesDone: Number($("#edit-images-done").value || 0),
        imagesTarget: Number($("#edit-images-target").value || 0),
        videosDone: Number($("#edit-videos-done").value || 0),
        videosTarget: Number($("#edit-videos-target").value || 0),
      },
      refresh: {
        suggested: Number($("#edit-refresh-suggested").value || 0),
        reason: $("#edit-refresh-reason").value.trim(),
      },
    };
    try {
      await patchItem(sku, payload);
      showToast("SKU 编辑已保存");
      openDrawer(sku);
    } catch (error) {
      showToast(error.message);
    }
    return;
  }

  const noteButton = event.target.closest("[data-drawer-note]");
  if (noteButton) {
    const input = $("#drawer-note-input");
    if (!input.value.trim()) return;
    try {
      await postAction(noteButton.dataset.drawerNote, "notes", { text: input.value.trim() });
      showToast("备注已保存");
      openDrawer(noteButton.dataset.drawerNote);
    } catch (error) {
      showToast(error.message);
    }
    return;
  }

  const feedbackButton = event.target.closest("[data-drawer-feedback]");
  if (feedbackButton) {
    const input = $("#drawer-feedback-input");
    if (!input.value.trim()) return;
    try {
      await postAction(feedbackButton.dataset.drawerFeedback, "feedback", { text: input.value.trim() });
      showToast("反馈已保存");
      openDrawer(feedbackButton.dataset.drawerFeedback);
    } catch (error) {
      showToast(error.message);
    }
  }
}

function debounce(fn, wait) {
  let timer = 0;
  return (...args) => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => fn(...args), wait);
  };
}

restoreAiImageState();
bindEvents();
loadSession()
  .catch((error) => showToast(error.message))
  .finally(() => {
    if (!state.auth.user) {
      renderDashboardGate();
      return;
    }
    loadBoard()
      .then(() => resumePersistedAiImageSuite().catch(() => {}))
      .catch((error) => {
        tbody.innerHTML = `<tr><td colspan="10"><div class="empty-state">${esc(error.message)}</div></td></tr>`;
        showToast(error.message);
      });
  });
