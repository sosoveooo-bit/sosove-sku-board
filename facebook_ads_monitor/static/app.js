const state = {
  payload: null,
  search: "",
  filter: "all",
  quick: "all",
  range: "last_7d",
  sortKey: "spend",
  sortDir: "desc",
  page: 1,
  pageSize: 50,
  pageCount: 1,
  currentAds: [],
  adIndex: new Map(),
  selectedAdId: "",
  autoSelectedAdId: "",
  detailOpen: false,
  autoRevealDetail: false,
  preferTopAd: false,
  loading: false,
  requestId: 0,
  abortController: null,
  backendOrders: "",
  autoRefreshTimer: null,
  operationLog: [],
  campaignNoOrderSpendThreshold: "",
  noOrderSpendCampaigns: [],
  pausingCampaignIds: new Set(),
  pausedCampaignIds: new Set(),
  qualityRoasThreshold: "2",
  qualityPurchaseThreshold: "1",
  qualityCampaigns: [],
  copyingCampaignIds: new Set(),
  copiedCampaignIds: new Set(),
};

const ACTION_LABELS = {
  all: "全部",
  scale: "放量",
  reduce: "降预算",
  fix_landing: "查承接",
  idle: "无消耗",
  watch: "观察",
  warning: "警告",
};

const ACTION_TONES = {
  scale: "good",
  reduce: "warn",
  fix_landing: "bad",
  idle: "muted",
  watch: "info",
};

document.addEventListener("DOMContentLoaded", () => {
  const initialRange = new URLSearchParams(window.location.search).get("range");
  if (initialRange) {
    state.range = normalizeRange(initialRange);
  }
  bindControls();
  initDisplayMode();
  syncRangeButtons();
  syncUrlRange();
  loadDashboard();
});

function bindControls() {
  const refresh = document.getElementById("refresh-btn");
  if (refresh) {
    refresh.addEventListener("click", () => {
      queueAutoAdReveal();
      addOperation("手动刷新当前范围");
      loadDashboard({ refresh: true });
    });
  }

  const sync = document.getElementById("sync-btn");
  if (sync) {
    sync.addEventListener("click", startSync);
  }

  const autoRefresh = document.getElementById("auto-refresh-select");
  if (autoRefresh) {
    autoRefresh.addEventListener("change", () => {
      scheduleAutoRefresh(Number(autoRefresh.value) || 0);
    });
  }

  const displayMode = document.getElementById("display-mode-select");
  if (displayMode) {
    displayMode.addEventListener("change", () => setDisplayMode(displayMode.value || "daily"));
  }

  document.querySelectorAll("[data-display-preset]").forEach((button) => {
    button.addEventListener("click", (event) => {
      const mode = button.dataset.displayPreset || "daily";
      setDisplayMode(mode);
      const select = document.getElementById("display-mode-select");
      if (select) select.value = mode;
      const targetId = button.dataset.scrollTarget || String(button.getAttribute("href") || "").replace(/^#/, "");
      if (targetId) {
        if (button.tagName === "A") event.preventDefault();
        document.getElementById(targetId)?.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  });

  const controlSearch = document.getElementById("control-search-input");
  if (controlSearch) {
    controlSearch.addEventListener("input", () => {
      state.search = controlSearch.value.trim();
      const mainSearch = document.getElementById("search-input");
      if (mainSearch) mainSearch.value = state.search;
      state.page = 1;
      queueAutoAdReveal();
      renderView();
    });
  }

  const controlAction = document.getElementById("control-action-filter");
  if (controlAction) {
    controlAction.addEventListener("change", () => {
      state.filter = controlAction.value || "all";
      state.page = 1;
      queueAutoAdReveal();
      syncFilterButtons();
      renderView();
    });
  }

  const controlSort = document.getElementById("control-sort-select");
  if (controlSort) {
    controlSort.addEventListener("change", () => {
      const [key, dir] = String(controlSort.value || "spend:desc").split(":");
      state.sortKey = key || "spend";
      state.sortDir = dir || "desc";
      state.page = 1;
      queueAutoAdReveal();
      renderView();
    });
  }

  const spendOnly = document.getElementById("control-spend-only");
  if (spendOnly) {
    spendOnly.addEventListener("change", () => {
      state.quick = spendOnly.checked ? "spent" : "all";
      state.page = 1;
      queueAutoAdReveal();
      syncQuickButtons();
      renderView();
    });
  }

  const clearFilters = document.getElementById("clear-filters-btn");
  if (clearFilters) {
    clearFilters.addEventListener("click", () => {
      resetAdNavigation();
      queueAutoAdReveal();
      renderView();
      addOperation("清空筛选");
    });
  }

  const backendOrders = document.getElementById("backend-orders-input");
  if (backendOrders) {
    backendOrders.addEventListener("input", () => {
      state.backendOrders = backendOrders.value.trim();
      saveBackendOrders();
      if (state.payload) renderReconciliation(state.payload);
    });
  }

  const noOrderSpendThreshold = document.getElementById("campaign-spend-threshold");
  if (noOrderSpendThreshold) {
    noOrderSpendThreshold.addEventListener("input", () => {
      state.campaignNoOrderSpendThreshold = noOrderSpendThreshold.value.trim();
      saveCampaignNoOrderSpendThreshold();
      if (state.payload) renderNoOrderSpendCampaigns(state.payload.tables?.ads || []);
    });
  }

  const checkNoOrderSpend = document.getElementById("check-no-order-spend-campaigns-btn");
  if (checkNoOrderSpend) {
    checkNoOrderSpend.addEventListener("click", () => {
      loadCampaignNoOrderSpendThreshold();
      renderNoOrderSpendCampaigns(state.payload?.tables?.ads || []);
      addOperation(`检查无单花费超过 ${formatCurrency(toNumber(state.campaignNoOrderSpendThreshold))} 的系列`);
    });
  }

  const pauseNoOrderSpend = document.getElementById("pause-no-order-spend-campaigns-btn");
  if (pauseNoOrderSpend) {
    pauseNoOrderSpend.addEventListener("click", () => {
      pauseNoOrderSpendCampaigns(state.noOrderSpendCampaigns);
    });
  }

  const qualityRoas = document.getElementById("quality-roas-threshold");
  if (qualityRoas) {
    qualityRoas.addEventListener("input", () => {
      state.qualityRoasThreshold = qualityRoas.value.trim();
      saveQualityCampaignThresholds();
      if (state.payload) renderQualityCampaigns(state.payload.tables?.ads || []);
    });
  }

  const qualityPurchase = document.getElementById("quality-purchase-threshold");
  if (qualityPurchase) {
    qualityPurchase.addEventListener("input", () => {
      state.qualityPurchaseThreshold = qualityPurchase.value.trim();
      saveQualityCampaignThresholds();
      if (state.payload) renderQualityCampaigns(state.payload.tables?.ads || []);
    });
  }

  const checkQuality = document.getElementById("check-quality-campaigns-btn");
  if (checkQuality) {
    checkQuality.addEventListener("click", () => {
      loadQualityCampaignThresholds();
      renderQualityCampaigns(state.payload?.tables?.ads || []);
      addOperation(`检查优质系列 · ROAS ${formatRatio(toNumber(state.qualityRoasThreshold))} / 购买 ${formatNumber(toNumber(state.qualityPurchaseThreshold))}`);
    });
  }

  const copyQuality = document.getElementById("copy-quality-campaigns-btn");
  if (copyQuality) {
    copyQuality.addEventListener("click", () => {
      copyQualityCampaigns(state.qualityCampaigns);
    });
  }

  const decisionActions = document.getElementById("decision-actions");
  if (decisionActions) {
    decisionActions.addEventListener("click", (event) => {
      const target = event.target.closest("[data-action-filter]");
      if (!target) return;
      const nextFilter = target.dataset.actionFilter || "all";
      if (nextFilter === "all") {
        resetAdNavigation();
      } else {
        state.filter = nextFilter;
        state.quick = nextFilter === "scale" ? "purchase" : "risk";
        state.page = 1;
        queueAutoAdReveal();
      }
      syncFilterButtons();
      syncQuickButtons();
      renderView();
    });
  }

  const operationActions = document.querySelector(".operation-actions");
  if (operationActions) {
    operationActions.addEventListener("click", (event) => {
      const target = event.target.closest("[data-action-filter]");
      if (!target) return;
      state.filter = target.dataset.actionFilter || "all";
      state.quick = state.filter === "scale" ? "purchase" : state.filter === "all" ? "all" : "risk";
      state.page = 1;
      queueAutoAdReveal();
      syncFilterButtons();
      syncQuickButtons();
      renderView();
      addOperation(`快捷筛选 · ${actionLabel(state.filter)}`);
    });
  }

  document.querySelectorAll("[data-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      state.filter = button.dataset.filter || "all";
      state.page = 1;
      queueAutoAdReveal();
      syncFilterButtons();
      renderView();
    });
  });

  document.querySelectorAll("[data-quick]").forEach((button) => {
    button.addEventListener("click", () => {
      state.quick = button.dataset.quick || "all";
      state.page = 1;
      queueAutoAdReveal();
      syncQuickButtons();
      renderView();
    });
  });

  const sortSelect = document.getElementById("ad-sort-select");
  if (sortSelect) {
    sortSelect.addEventListener("change", () => {
      const [key, dir] = String(sortSelect.value || "spend:desc").split(":");
      state.sortKey = key || "spend";
      state.sortDir = dir || "desc";
      state.page = 1;
      queueAutoAdReveal();
      renderView();
    });
  }

  const pageSizeSelect = document.getElementById("page-size-select");
  if (pageSizeSelect) {
    pageSizeSelect.addEventListener("change", () => {
      state.pageSize = Number(pageSizeSelect.value) || 50;
      state.page = 1;
      queueAutoAdReveal();
      renderView();
    });
  }

  const prevPage = document.getElementById("prev-page-btn");
  if (prevPage) {
    prevPage.addEventListener("click", () => {
      state.page = Math.max(1, state.page - 1);
      queueAutoAdReveal();
      renderView();
    });
  }

  const nextPage = document.getElementById("next-page-btn");
  if (nextPage) {
    nextPage.addEventListener("click", () => {
      state.page = Math.min(state.pageCount || 1, state.page + 1);
      queueAutoAdReveal();
      renderView();
    });
  }

  const adTable = document.getElementById("ad-table");
  if (adTable) {
    adTable.addEventListener("click", (event) => {
      const row = event.target.closest("tr[data-ad-id]");
      if (!row) return;
      state.selectedAdId = row.dataset.adId || "";
      state.autoSelectedAdId = "";
      state.detailOpen = true;
      renderAdDetail();
      renderAdTable(state.currentAds.slice((state.page - 1) * state.pageSize, state.page * state.pageSize));
    });
  }

  const priorityList = document.getElementById("priority-list");
  if (priorityList) {
    priorityList.addEventListener("click", (event) => {
      const target = event.target.closest("[data-ad-id]");
      if (!target) return;
      revealAdById(target.dataset.adId || "", { resetFilters: true });
    });
    priorityList.addEventListener("keydown", handleAdCardKeydown);
  }

  const scaleList = document.getElementById("scale-list");
  if (scaleList) {
    scaleList.addEventListener("click", (event) => {
      const target = event.target.closest("[data-ad-id]");
      if (!target) return;
      revealAdById(target.dataset.adId || "", { resetFilters: true });
    });
    scaleList.addEventListener("keydown", handleAdCardKeydown);
  }

  const closeDetail = document.getElementById("close-detail-btn");
  if (closeDetail) {
    closeDetail.addEventListener("click", closeAdDetail);
  }

  const drawer = document.getElementById("ad-detail-drawer");
  if (drawer) {
    drawer.addEventListener("click", (event) => {
      if (event.target === drawer) closeAdDetail();
    });
  }

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeAdDetail();
  });

  document.querySelectorAll("[data-range]").forEach((button) => {
    button.addEventListener("click", () => {
      const nextRange = normalizeRange(button.dataset.range);
      if (nextRange === state.range) {
        loadDashboard({ refresh: true });
        return;
      }
      state.range = nextRange;
      state.page = 1;
      state.selectedAdId = "";
      syncRangeButtons();
      syncUrlRange();
      loadDashboard();
    });
  });
}

async function loadDashboard(options = {}) {
  const request = beginRequest();
  setStatus(`正在拉取 ${humanRange(state.range)} 数据`);
  clearError();

  try {
    const payload = await fetchJson(metricsPath(Boolean(options.refresh)), { signal: request.signal });
    if (request.id !== state.requestId) return;
    state.payload = payload;
    renderStatic(payload);
    renderView();
  } catch (error) {
    if (error.name === "AbortError") return;
    showError(error.message || "加载失败");
    setStatus("加载失败");
    renderDataHealthBanner(null, error.message || "加载失败");
  } finally {
    endRequest(request.id);
  }
}

async function fetchJson(path, options = {}) {
  const response = await fetch(path, {
    headers: { Accept: "application/json" },
    ...options,
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok || data.ok === false) {
    throw new Error(data.error || response.statusText);
  }
  return data;
}

function startSync() {
  const mode = document.getElementById("sync-mode-select")?.value || "cache";
  const previousRange = state.range;
  if (mode === "today") {
    state.range = "today";
    state.page = 1;
    state.selectedAdId = "";
    syncRangeButtons();
    syncUrlRange();
  }
  const shouldRefresh = mode !== "cache";
  setSyncStatus(shouldRefresh ? "正在实时拉取" : "正在读取缓存");
  queueAutoAdReveal();
  addOperation(`${mode === "cache" ? "读取缓存" : "实时同步"} · ${humanRange(state.range)}`);
  loadDashboard({ refresh: shouldRefresh }).finally(() => {
    setSyncStatus(`完成 · ${humanRange(state.range)}`);
    if (mode === "today" && previousRange !== state.range) syncRangeButtons();
  });
}

function scheduleAutoRefresh(interval) {
  if (state.autoRefreshTimer) {
    clearInterval(state.autoRefreshTimer);
    state.autoRefreshTimer = null;
  }
  if (!interval) {
    setSyncStatus("自动刷新已关闭");
    addOperation("关闭自动刷新");
    return;
  }
  state.autoRefreshTimer = setInterval(() => {
    addOperation(`自动刷新 · ${humanRange(state.range)}`);
    queueAutoAdReveal();
    loadDashboard({ refresh: state.range === "today" });
  }, interval);
  setSyncStatus(`自动刷新 ${formatDuration(interval)}`);
  addOperation(`开启自动刷新 ${formatDuration(interval)}`);
}

function initDisplayMode() {
  const saved = localStorage.getItem("fb_dashboard_display_mode") || "daily";
  const select = document.getElementById("display-mode-select");
  if (select) select.value = saved;
  setDisplayMode(saved, { persist: false });
}

function setDisplayMode(mode, options = {}) {
  const safeMode = ["daily", "settings", "detail", "all"].includes(mode) ? mode : "daily";
  document.body.dataset.displayMode = safeMode;
  if (options.persist !== false) {
    localStorage.setItem("fb_dashboard_display_mode", safeMode);
  }
}

function setSyncStatus(text) {
  setText("sync-status", text || "-");
}

function addOperation(text) {
  const stamp = new Intl.DateTimeFormat("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(new Date());
  state.operationLog.unshift({ stamp, text });
  state.operationLog = state.operationLog.slice(0, 8);
  renderOperationLog();
}

function renderOperationLog() {
  const mount = document.getElementById("operation-log");
  if (!mount) return;
  if (!state.operationLog.length) {
    mount.innerHTML = `<li><span>-</span><strong>等待操作</strong></li>`;
    return;
  }
  mount.innerHTML = state.operationLog
    .map((item) => `<li><span>${escapeHtml(item.stamp)}</span><strong>${escapeHtml(item.text)}</strong></li>`)
    .join("");
}

function formatDuration(ms) {
  const minutes = Math.round(ms / 60000);
  return `${formatNumber(minutes)} 分钟`;
}

function resetAdNavigation() {
  state.search = "";
  state.filter = "all";
  state.quick = "all";
  state.page = 1;
  state.sortKey = "spend";
  state.sortDir = "desc";
  state.selectedAdId = "";
  state.autoSelectedAdId = "";
  state.detailOpen = false;
  state.autoRevealDetail = true;
  state.preferTopAd = true;
  syncFilterButtons();
  syncQuickButtons();
  syncSearchInput();
}

function revealAdById(adId, options = {}) {
  const id = String(adId || "");
  if (!id || !state.payload) return;
  if (options.resetFilters) {
    state.search = "";
    state.filter = "all";
    state.quick = "all";
    syncFilterButtons();
    syncQuickButtons();
    syncSearchInput();
  }

  const query = normalizeText(state.search);
  const sorted = sortRows(
    (state.payload.tables?.ads || [])
      .filter((row) => matchesSearch(adSearchText(row), query))
      .filter((row) => matchesAdFilter(row, state.filter))
      .filter((row) => matchesQuickFilter(row, state.quick)),
  );
  const index = sorted.findIndex((row) => adRowId(row) === id);
  if (index < 0) return;

  state.page = Math.max(1, Math.floor(index / state.pageSize) + 1);
  state.selectedAdId = id;
  state.autoSelectedAdId = "";
  state.detailOpen = true;
  state.autoRevealDetail = false;
  state.preferTopAd = false;
  renderView();
  scrollRowIntoView(id);
}

function scrollRowIntoView(adId) {
  const row = document.querySelector(`tr[data-ad-id="${cssEscape(adId)}"]`);
  if (!row) return;
  row.scrollIntoView({ block: "center", behavior: "smooth" });
}

function handleAdCardKeydown(event) {
  if (!["Enter", " "].includes(event.key)) return;
  const target = event.target.closest("[data-ad-id]");
  if (!target) return;
  event.preventDefault();
  revealAdById(target.dataset.adId || "", { resetFilters: true });
}

function metricsPath(refresh = false) {
  const params = new URLSearchParams();
  params.set("range", state.range);
  if (refresh) {
    params.set("refresh", "1");
  }
  return `/api/metrics?${params.toString()}`;
}

function beginRequest() {
  state.requestId += 1;
  if (state.abortController) {
    state.abortController.abort();
  }
  state.abortController = new AbortController();
  state.loading = true;
  const refresh = document.getElementById("refresh-btn");
  if (refresh) {
    refresh.disabled = true;
    refresh.textContent = `拉取 ${humanRange(state.range)}`;
  }
  return { id: state.requestId, signal: state.abortController.signal };
}

function endRequest(id) {
  if (id !== state.requestId) return;
  state.loading = false;
  state.abortController = null;
  const refresh = document.getElementById("refresh-btn");
  if (refresh) {
    refresh.disabled = false;
    refresh.textContent = "刷新当前范围";
  }
}

function renderStatic(payload) {
  const source = payload.source || {};
  setText("report-name", source.reportName || "-");
  setText("report-range", source.rangeLabel || humanRange(source.range));
  setText("report-time", formatDateTime(source.generatedAt));
  setText("report-dir", source.reportDir || "-");
  setText("api-version", source.apiVersion || "-");
  setText("source-mode", sourceModeLabel(source.sourceMode));
  renderKpis(payload.summary || {});
  renderDecisionBanner(payload);
  renderDecisionActions(payload);
  renderCompareStrip(payload);
  loadBackendOrders();
  loadCampaignNoOrderSpendThreshold();
  loadQualityCampaignThresholds();
  renderTrustPanel(payload);
  renderReconciliation(payload);
  renderFreshnessGrid(payload);
  renderDataHealthBanner(payload);
  renderDailyOps(payload);
  renderOperationLog();
  syncRangeButtons();
  syncUrlRange();
  syncSearchInput();
}

function renderView() {
  if (!state.payload) return;
  const view = buildView(state.payload);
  renderFunnel(view.funnel);
  renderActionBreakdown(view.actionBreakdown);
  renderAccountTable(view.accounts);
  renderAggregateTable("campaign-table", view.campaigns, "Campaign");
  renderAggregateTable("adset-table", view.adsets, "Adset");
  renderAggregateTable("family-table", view.families, "素材家族");
  renderPriorityList(view.priority);
  renderScaleList(view.scaleAds);
  renderAdTable(view.pageAds);
  renderFindingGrid(view.findings);
  renderAdPager(view);
  renderAdDetail();
  renderStatus(view);
  renderScopeChip(view);
  renderControlSummary(view);
  syncControlPanel();
}

function buildView(payload) {
  const tables = payload.tables || {};
  const query = normalizeText(state.search);
  const ads = (tables.ads || [])
    .filter((row) => matchesSearch(adSearchText(row), query))
    .filter((row) => matchesAdFilter(row, state.filter))
    .filter((row) => matchesQuickFilter(row, state.quick));
  const findings = (tables.findings || [])
    .filter((row) => matchesSearch(findingSearchText(row), query))
    .filter((row) => matchesFindingFilter(row, state.filter));
  const accounts = (tables.accounts || []).filter((row) => matchesSearch(accountSearchText(row), query));
  const sortedAds = sortRows(ads);
  state.currentAds = sortedAds;
  state.adIndex = new Map(sortedAds.map((row) => [String(row.ad_id || row.ad_name || ""), row]));
  const pageCount = Math.max(1, Math.ceil(sortedAds.length / state.pageSize));
  state.pageCount = pageCount;
  if (state.page > pageCount) {
    state.page = pageCount;
  }
  if (state.page < 1) {
    state.page = 1;
  }
  const start = (state.page - 1) * state.pageSize;
  const pageAds = sortedAds.slice(start, start + state.pageSize);
  const firstPageAdId = pageAds[0] ? adRowId(pageAds[0]) : "";
  const selectedOnPage = pageAds.some((row) => adRowId(row) === String(state.selectedAdId));
  if (!pageAds.length) {
    state.selectedAdId = "";
    state.autoSelectedAdId = "";
    state.detailOpen = false;
  } else if (state.preferTopAd || (state.selectedAdId && !selectedOnPage)) {
    state.selectedAdId = firstPageAdId;
    state.detailOpen = state.autoRevealDetail;
    state.autoSelectedAdId = state.detailOpen ? firstPageAdId : "";
  } else if (state.autoRevealDetail) {
    state.detailOpen = true;
    state.autoSelectedAdId = state.autoSelectedAdId || String(state.selectedAdId);
  }
  state.preferTopAd = false;

  return {
    ads: sortedAds,
    pageAds,
    findings,
    accounts: accounts.slice().sort((a, b) => toNumber(b.spend) - toNumber(a.spend)),
    campaigns: aggregate(sortedAds, "campaign_name").slice(0, 80),
    adsets: aggregate(sortedAds, "adset_name").slice(0, 80),
    families: aggregate(sortedAds, "family").slice(0, 80),
    funnel: buildFunnel(sortedAds, accounts),
    actionBreakdown: buildActionBreakdown(sortedAds),
    priority: buildPriorityItems(sortedAds, findings),
    scaleAds: sortedAds
      .filter((row) => row.action === "scale")
      .sort((a, b) => toNumber(b.purchase) - toNumber(a.purchase) || toNumber(b.roas) - toNumber(a.roas))
      .slice(0, 10),
    totalAds: (tables.ads || []).length,
    filteredAds: sortedAds.length,
    totalFindings: (tables.findings || []).length,
    pageCount,
    page: state.page,
    pageSize: state.pageSize,
  };
}

function renderKpis(summary) {
  const cards = {
    spend: {
      value: formatCurrency(summary.spend),
      note: `ROAS ${formatRatio(summary.roas)} · CPC ${formatCurrency(summary.cpc)}`,
    },
    purchase: {
      value: formatNumber(summary.purchase),
      note: `点击 ${formatNumber(summary.clicks)}`,
    },
    roas: {
      value: formatRatio(summary.roas),
      note: `收入 ${formatCurrency(summary.purchase_value)}`,
    },
    cpa: {
      value: formatCurrency(summary.cpa),
      note: `${formatNumber(summary.purchase)} 次购买`,
    },
    ctr: {
      value: formatPercent(summary.ctr),
      note: `展示 ${formatNumber(summary.impressions)}`,
    },
    warning: {
      value: formatNumber(summary.warning),
      note: `${formatNumber(summary.critical)} critical`,
      negative: toNumber(summary.warning) > 0 || toNumber(summary.critical) > 0,
    },
    opportunity: {
      value: formatNumber(summary.opportunity),
      note: `放量 ${formatNumber(summary.scale)}`,
    },
    ads: {
      value: formatNumber(summary.ads),
      note: `账户 ${formatNumber(summary.accounts)}`,
    },
  };

  Object.entries(cards).forEach(([key, data]) => {
    const node = document.querySelector(`[data-kpi="${key}"]`);
    if (!node) return;
    const strong = node.querySelector("strong");
    const small = node.querySelector("small");
    if (strong) strong.textContent = data.value;
    if (small) {
      small.textContent = data.note;
      small.classList.toggle("negative", Boolean(data.negative));
    }
  });
}

function renderDecisionBanner(payload) {
  const mount = document.getElementById("decision-banner");
  if (!mount) return;
  const summary = payload.summary || {};
  const boards = payload.boards || {};
  const warningCount = toNumber(summary.warning) + toNumber(summary.critical);
  const scaleCount = toNumber(summary.scale);
  const reduceCount = toNumber(summary.reduce);
  const fixCount = toNumber(summary.fix_landing);
  const roas = toNumber(summary.roas);

  let tone = "warn";
  let kicker = "继续观察";
  let title = "先看动作表，再决定是否加预算";
  let note = `当前 ROAS ${formatRatio(roas)}，有 ${formatNumber(scaleCount)} 个放量候选、${formatNumber(reduceCount)} 个降预算候选。`;

  if (fixCount > 0 || warningCount >= 30) {
    tone = "bad";
    kicker = "先修问题";
    title = "先处理承接和风险广告，再谈放量";
    note = `警告 ${formatNumber(warningCount)} 条，查承接候选 ${formatNumber(fixCount)} 个。优先看点击无加购、低 ROAS 和花费集中的广告。`;
  } else if (roas >= 2.5 && scaleCount > reduceCount) {
    tone = "good";
    kicker = "可小步放量";
    title = "保留胜出素材，小步加预算";
    note = `整体 ROAS ${formatRatio(roas)}，购买 ${formatNumber(summary.purchase)} 次。放量先从低频高 ROAS 素材开始，不要一次性猛推。`;
  } else if (toNumber(summary.purchase) === 0 && toNumber(summary.clicks) > 0) {
    tone = "warn";
    kicker = "缺订单信号";
    title = "点击已经有了，先查漏斗断点";
    note = "没有购买信号前，重点看落地页、结账和支付承接，不建议直接加预算。";
  }

  const nextItems = [
    nextItemFromAd("放量候选", boards.scale?.[0]),
    nextItemFromAd("降预算", boards.risk?.[0]),
    nextItemFromAd("查承接", boards.noAtc?.[0]),
  ].filter(Boolean);

  const chips = [
    ["花费", formatCurrency(summary.spend)],
    ["购买", formatNumber(summary.purchase)],
    ["ROAS", formatRatio(summary.roas)],
    ["警告", formatNumber(warningCount)],
    ["放量", formatNumber(scaleCount)],
    ["降预算", formatNumber(reduceCount)],
  ];

  mount.dataset.tone = tone;
  mount.innerHTML = `
    <div class="decision-copy">
      <span class="decision-kicker ${tone}">${escapeHtml(kicker)}</span>
      <strong>${escapeHtml(title)}</strong>
      <p>${escapeHtml(note)}</p>
    </div>
    <div class="decision-stack">
      <div class="decision-chip-row">
        ${chips
          .map(
            ([label, value]) => `
              <span class="decision-chip">
                ${escapeHtml(label)}
                <strong>${escapeHtml(value)}</strong>
              </span>
            `,
          )
          .join("")}
      </div>
      <div class="decision-next-row">
        ${nextItems
          .map(
            (item) => `
              <div class="decision-next">
                <span>${escapeHtml(item.label)}</span>
                <strong>${escapeHtml(item.text)}</strong>
              </div>
            `,
          )
          .join("")}
      </div>
    </div>
  `;
}

function renderDecisionActions(payload) {
  const mount = document.getElementById("decision-actions");
  if (!mount) return;
  const summary = payload.summary || {};
  const actions = [
    { label: "看放量", filter: "scale", count: summary.scale, tone: "good" },
    { label: "看降预算", filter: "reduce", count: summary.reduce, tone: "warn" },
    { label: "看承接", filter: "fix_landing", count: summary.fix_landing, tone: "bad" },
    { label: "看风险", filter: "warning", count: summary.warning, tone: "bad" },
    { label: "回到全部", filter: "all", count: summary.ads, tone: "info" },
  ];

  mount.innerHTML = actions
    .map(
      (item) => `
        <button type="button" class="decision-action ${escapeHtml(item.tone)}" data-action-filter="${escapeHtml(item.filter)}">
          <span>${escapeHtml(item.label)}</span>
          <strong>${formatNumber(item.count)}</strong>
        </button>
      `,
    )
    .join("");
}

function renderCompareStrip(payload) {
  const mount = document.getElementById("compare-strip");
  if (!mount) return;
  const comparison = payload.daily?.comparisons?.today_vs_yesterday;
  if (!comparison) {
    mount.hidden = true;
    mount.innerHTML = "";
    return;
  }

  const fields = [
    ["花费", comparison.spend],
    ["购买", comparison.purchase],
    ["ROAS", comparison.roas],
    ["CPA", comparison.cpa],
    ["CTR", comparison.ctr],
    ["点击", comparison.clicks],
  ];

  const html = fields
    .filter(([, item]) => item)
    .map(([label, item]) => `
      <div class="compare-item">
        <span>${escapeHtml(label)}</span>
        <strong>${escapeHtml(compareValue(label, item.current))}</strong>
        <small>${escapeHtml(compareDelta(item))}</small>
      </div>
    `)
    .join("");

  mount.hidden = !html;
  mount.innerHTML = html;
}

function renderTrustPanel(payload) {
  renderFreshnessCard(payload);
  renderApiContractCard(payload);
}

function renderFreshnessCard(payload) {
  const mount = document.getElementById("freshness-card");
  if (!mount) return;
  const source = payload.source || {};
  const freshness = source.freshness || {};
  const system = payload.system || {};
  const deps = system.dependencies?.packages || {};
  const mode = sourceModeLabel(source.sourceMode);
  const age = freshness.ageMinutes === null || freshness.ageMinutes === undefined ? "-" : `${formatNumber(freshness.ageMinutes)} 分钟前`;
  const depOk = Object.values(deps).every(Boolean);
  const tone = freshness.isStale || !depOk ? "bad" : source.sourceMode === "pulled" ? "good" : "warn";
  mount.dataset.tone = tone;
  mount.innerHTML = `
    <span>数据状态</span>
    <strong>${escapeHtml(mode)} · ${escapeHtml(age)}</strong>
    <small>报表 ${escapeHtml(source.reportName || "-")} · 账户 ${formatNumber(system.activeAccountCount || 0)} / ${formatNumber(system.accountCount || 0)} · requests ${depOk ? "OK" : "缺失"}</small>
  `;
}

function renderApiContractCard(payload) {
  const mount = document.getElementById("api-contract-card");
  if (!mount) return;
  const settings = payload.apiSettings || {};
  const source = payload.source || {};
  mount.dataset.tone = "info";
  mount.innerHTML = `
    <span>FB API 口径</span>
    <strong>${escapeHtml(settings.actionReportTime || "-")} · ${settings.useUnifiedAttributionSetting ? "统一归因" : "默认归因"}</strong>
    <small>${escapeHtml(source.apiVersion || settings.apiVersion || "-")} · ${escapeHtml(settings.timezone || "-")} · ${escapeHtml((settings.levels || []).join("/"))}</small>
  `;
}

function renderReconciliation(payload) {
  const input = document.getElementById("backend-orders-input");
  const summary = document.getElementById("reconcile-summary");
  const detail = document.getElementById("reconcile-detail");
  const card = document.getElementById("reconcile-card");
  if (!summary || !detail || !card) return;
  if (input && input.value !== state.backendOrders) input.value = state.backendOrders;
  const fbOrders = toNumber(payload.summary?.purchase);
  const backendOrders = state.backendOrders === "" ? null : toNumber(state.backendOrders);
  if (backendOrders === null) {
    card.dataset.tone = "info";
    summary.textContent = `FB ${formatNumber(fbOrders)} 单`;
    detail.textContent = "输入店铺后台订单数，自动计算 FB 归因差异";
    return;
  }
  const gap = backendOrders - fbOrders;
  const gapRate = backendOrders ? (gap / backendOrders) * 100 : 0;
  card.dataset.tone = Math.abs(gapRate) >= 10 ? "bad" : Math.abs(gapRate) >= 5 ? "warn" : "good";
  summary.textContent = `后台 ${formatNumber(backendOrders)} / FB ${formatNumber(fbOrders)}`;
  detail.textContent = `差异 ${gap >= 0 ? "+" : ""}${formatNumber(gap)} 单，差异率 ${gap >= 0 ? "+" : ""}${formatPercent(gapRate)}`;
}

function renderFreshnessGrid(payload) {
  const mount = document.getElementById("freshness-grid");
  if (!mount) return;
  const source = payload.source || {};
  const freshness = source.freshness || {};
  const system = payload.system || {};
  const items = [
    ["数据模式", sourceModeLabel(source.sourceMode)],
    ["报表时间", formatDateTime(freshness.generatedAt || source.generatedAt)],
    ["缓存年龄", freshness.ageMinutes === null || freshness.ageMinutes === undefined ? "-" : `${formatNumber(freshness.ageMinutes)} 分钟`],
    ["活跃账户", `${formatNumber(system.activeAccountCount || 0)} / ${formatNumber(system.accountCount || 0)}`],
  ];
  mount.innerHTML = items
    .map(([label, value]) => `<div class="mini-stat"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`)
    .join("");
}

function renderDataHealthBanner(payload, errorMessage = "") {
  const mount = document.getElementById("data-health-banner");
  if (!mount) return;
  if (!payload) {
    mount.dataset.tone = "bad";
    mount.innerHTML = `
      <div><strong>数据读取失败</strong><span>${escapeHtml(errorMessage || "请检查本地服务后重新同步。")}</span></div>
      <button type="button" data-health-sync>重新同步</button>
    `;
  } else {
    const source = payload.source || {};
    const freshness = source.freshness || {};
    const system = payload.system || {};
    const ageMinutes = freshness.ageMinutes;
    const stale = freshness.isStale === true || (ageMinutes !== null && ageMinutes !== undefined && toNumber(ageMinutes) > 180);
    const live = source.sourceMode === "live" || source.sourceMode === "refresh";
    const modeText = live ? "实时数据" : "缓存数据";
    const ageText = ageMinutes === null || ageMinutes === undefined ? "更新时间未知" : `缓存 ${formatNumber(ageMinutes)} 分钟`;
    mount.dataset.tone = stale ? "warn" : "good";
    mount.innerHTML = `
      <div>
        <strong>${stale ? "数据较旧，建议立即同步" : `${modeText}已就绪`}</strong>
        <span>${escapeHtml(source.rangeLabel || humanRange(source.range))} · ${escapeHtml(formatDateTime(freshness.generatedAt || source.generatedAt))} · ${escapeHtml(ageText)} · 活跃账户 ${formatNumber(system.activeAccountCount || 0)} / ${formatNumber(system.accountCount || 0)}</span>
      </div>
      ${stale ? '<button type="button" data-health-sync>立即同步</button>' : ""}
    `;
  }
  mount.querySelector("[data-health-sync]")?.addEventListener("click", startSync);
}

function renderControlSummary(view) {
  const summary = document.getElementById("filtered-summary");
  const selected = document.getElementById("selected-count");
  if (summary) {
    summary.textContent = `${formatNumber(view.filteredAds)} / ${formatNumber(view.totalAds)} 条广告`;
  }
  if (selected) {
    selected.textContent = state.detailOpen ? "当前已打开 1 条广告详情" : "当前未打开详情";
  }
}

function syncControlPanel() {
  const controlSearch = document.getElementById("control-search-input");
  if (controlSearch && controlSearch.value !== state.search) controlSearch.value = state.search;
  const controlAction = document.getElementById("control-action-filter");
  if (controlAction) controlAction.value = state.filter;
  const controlSort = document.getElementById("control-sort-select");
  if (controlSort) controlSort.value = `${state.sortKey}:${state.sortDir}`;
  const spendOnly = document.getElementById("control-spend-only");
  if (spendOnly) spendOnly.checked = state.quick === "spent";
}

function renderDailyOps(payload) {
  const summary = payload.summary || {};
  const boards = payload.boards || {};
  const ads = payload.tables?.ads || [];
  const warningCount = toNumber(summary.warning) + toNumber(summary.critical);
  const scaleCount = toNumber(summary.scale);
  const reduceCount = toNumber(summary.reduce);
  const fixCount = toNumber(summary.fix_landing);
  let title = "先处理风险，再看放量";
  let note = `当前 ${formatNumber(scaleCount)} 条放量、${formatNumber(reduceCount)} 条降预算、${formatNumber(fixCount)} 条查承接。`;
  if (scaleCount > reduceCount && toNumber(summary.roas) >= 2.5) {
    title = "有放量机会，但保持小步测试";
    note = `整体 ROAS ${formatRatio(summary.roas)}，优先从有购买且 CPA 稳定的广告开始。`;
  }
  if (fixCount > 0 || warningCount >= 20) {
    title = "今天先修承接和低效消耗";
    note = `警告 ${formatNumber(warningCount)} 条，查承接 ${formatNumber(fixCount)} 条，先别盲目加预算。`;
  }
  setText("daily-verdict-title", title);
  setText("daily-verdict-note", note);
  renderDailyPriority(summary);
  renderDailyChanges(payload);
  renderDailyCandidates(boards);
  renderDailyActionTable(ads);
  renderDailyFamilyGroups(ads);
  renderNoOrderSpendCampaigns(ads);
  renderQualityCampaigns(ads);
}

function renderDailyPriority(summary) {
  const mount = document.getElementById("daily-priority-list");
  if (!mount) return;
  const items = [
    ["查承接", summary.fix_landing, "点击多但加购/购买弱"],
    ["降预算", summary.reduce, "已有花费但 ROAS 偏低"],
    ["放量", summary.scale, "有购买且 ROAS 达标"],
    ["警告", toNumber(summary.warning) + toNumber(summary.critical), "需要先排查"],
  ];
  mount.innerHTML = items
    .map(([label, value, desc]) => `<div class="daily-priority-item"><strong>${escapeHtml(label)} · ${formatNumber(value)}</strong><span>${escapeHtml(desc)}</span></div>`)
    .join("");
}

function renderDailyChanges(payload) {
  const mount = document.getElementById("daily-change-list");
  if (!mount) return;
  const comparison = payload.daily?.comparisons?.today_vs_yesterday;
  if (!comparison) {
    mount.innerHTML = emptyBlock("暂无 today/yesterday 对比");
    return;
  }
  const fields = [
    ["花费", comparison.spend],
    ["购买", comparison.purchase],
    ["ROAS", comparison.roas],
    ["CPA", comparison.cpa],
  ];
  mount.innerHTML = fields
    .filter(([, item]) => item)
    .map(([label, item]) => `<div class="daily-change"><span>${escapeHtml(label)}</span><strong>${escapeHtml(compareValue(label, item.current))}</strong><small>${escapeHtml(compareDelta(item))}</small></div>`)
    .join("");
}

function renderDailyCandidates(boards) {
  const mount = document.getElementById("daily-candidate-list");
  if (!mount) return;
  const rows = [
    ...(boards.scale || []).slice(0, 3).map((row) => ({ label: "放量", row })),
    ...(boards.risk || []).slice(0, 3).map((row) => ({ label: "止损", row })),
    ...(boards.noAtc || []).slice(0, 3).map((row) => ({ label: "承接", row })),
  ];
  if (!rows.length) {
    mount.innerHTML = emptyBlock("暂无候选");
    return;
  }
  mount.innerHTML = rows
    .map(({ label, row }) => `<button class="daily-candidate" type="button" data-ad-id="${escapeHtml(adRowId(row))}"><strong>${escapeHtml(label)} · ${escapeHtml(compactText(row.ad_name || row.ad_id, 42))}</strong><span>${formatCurrency(row.spend)} · ${formatNumber(row.purchase)} 单 · ${formatRatio(row.roas)}</span></button>`)
    .join("");
  mount.querySelectorAll("[data-ad-id]").forEach((button) => {
    button.addEventListener("click", () => revealAdById(button.dataset.adId || "", { resetFilters: true }));
  });
}

function renderDailyActionTable(ads) {
  const mount = document.getElementById("daily-action-table");
  const summary = document.getElementById("daily-action-summary");
  if (!mount) return;
  const rows = ads
    .filter((row) => ["scale", "reduce", "fix_landing"].includes(row.action))
    .slice()
    .sort((a, b) => actionPriority(a.action) - actionPriority(b.action) || toNumber(b.spend) - toNumber(a.spend))
    .slice(0, 12);
  if (summary) {
    summary.textContent = `共 ${formatNumber(rows.length)} 条优先处理广告，点击行可在广告动作表中继续查看详情。`;
  }
  if (!rows.length) {
    mount.innerHTML = `<tr><td colspan="5" class="empty">暂无优先动作</td></tr>`;
    return;
  }
  mount.innerHTML = rows
    .map((row, index) => `
      <tr>
        <td data-label="优先级">P${index + 1}</td>
        <td data-label="广告"><strong>${escapeHtml(compactText(row.ad_name || row.ad_id, 46))}</strong><span class="muted">${escapeHtml(row.ad_id || "-")}</span></td>
        <td data-label="关键数据">${formatCurrency(row.spend)} · ${formatNumber(row.purchase)} 单 · ${formatRatio(row.roas)}</td>
        <td data-label="判断原因">${escapeHtml(actionReason(row))}</td>
        <td data-label="建议动作">${actionPill(row.action, row.action_label)}</td>
      </tr>
    `)
    .join("");
}

function renderDailyFamilyGroups(ads) {
  const mount = document.getElementById("daily-family-groups");
  if (!mount) return;
  const groups = aggregate(ads, "family").slice(0, 6);
  if (!groups.length) {
    mount.innerHTML = emptyBlock("暂无素材家族数据");
    return;
  }
  mount.innerHTML = groups
    .map((row) => `<div class="family-chip"><strong>${escapeHtml(compactText(row.name, 44))}</strong><span>${formatCurrency(row.spend)} · ${formatNumber(row.purchase)} 单 · ${formatRatio(row.roas)}</span></div>`)
    .join("");
}

function renderNoOrderSpendCampaigns(ads) {
  const summary = document.getElementById("campaign-spend-summary");
  const list = document.getElementById("no-order-spend-campaign-list");
  const input = document.getElementById("campaign-spend-threshold");
  if (!summary || !list) return;
  if (input && input.value !== state.campaignNoOrderSpendThreshold) input.value = state.campaignNoOrderSpendThreshold;

  if (state.campaignNoOrderSpendThreshold === "") {
    state.noOrderSpendCampaigns = [];
    summary.textContent = "输入阈值后检查";
    list.innerHTML = `<p class="empty">按当前口径：系列花费达到阈值，且购买数为 0，就提示关闭。</p>`;
    updateNoOrderSpendPauseButton();
    return;
  }

  const threshold = toNumber(state.campaignNoOrderSpendThreshold);
  const campaigns = buildCampaignSpendRows(ads)
    .filter((row) => row.purchase <= 0 && row.spend >= threshold && row.spend > 0)
    .sort((a, b) => b.spend - a.spend)
    .slice(0, 12);
  state.noOrderSpendCampaigns = campaigns;

  summary.textContent = `${formatNumber(campaigns.length)} 个系列无单花费超过 ${formatCurrency(threshold)}`;
  if (!campaigns.length) {
    list.innerHTML = `<p class="empty">当前没有花费达标且 0 购买的系列。</p>`;
    updateNoOrderSpendPauseButton(campaigns);
    return;
  }

  list.innerHTML = campaigns
    .map(
      (row) => {
        const isPaused = row.id && state.pausedCampaignIds.has(row.id);
        const isPausing = row.id && state.pausingCampaignIds.has(row.id);
        const disabled = !row.id || isPaused || isPausing ? "disabled" : "";
        const buttonText = isPaused ? "已关闭" : isPausing ? "关闭中" : "关闭系列";
        return `
          <article class="no-order-spend-campaign">
            <button class="no-order-spend-focus" type="button" data-campaign-focus="${escapeHtml(row.name)}">
              <strong>建议关闭 · ${escapeHtml(compactText(row.name, 50))}</strong>
              <span>花费 ${formatCurrency(row.spend)} · 购买 ${formatNumber(row.purchase)} · 收入 ${formatCurrency(row.revenue)} · 广告 ${formatNumber(row.ads)}</span>
            </button>
            <button class="campaign-pause-btn" type="button" data-pause-campaign-id="${escapeHtml(row.id || "")}" data-pause-campaign-name="${escapeHtml(row.name)}" ${disabled}>${buttonText}</button>
          </article>
        `;
      },
    )
    .join("");

  updateNoOrderSpendPauseButton(campaigns);

  list.querySelectorAll("[data-campaign-focus]").forEach((button) => {
    button.addEventListener("click", () => focusCampaign(button.dataset.campaignFocus || ""));
  });
  list.querySelectorAll("[data-pause-campaign-id]").forEach((button) => {
    button.addEventListener("click", () => {
      const campaignId = button.dataset.pauseCampaignId || "";
      const campaign = state.noOrderSpendCampaigns.find((row) => row.id === campaignId);
      pauseNoOrderSpendCampaigns(campaign ? [campaign] : []);
    });
  });
}

function closeableNoOrderSpendCampaigns(campaigns = state.noOrderSpendCampaigns) {
  const seen = new Set();
  return (campaigns || []).filter((row) => {
    const campaignId = String(row.id || "").trim();
    if (!campaignId || seen.has(campaignId)) return false;
    if (state.pausedCampaignIds.has(campaignId) || state.pausingCampaignIds.has(campaignId)) return false;
    seen.add(campaignId);
    return true;
  });
}

function updateNoOrderSpendPauseButton(campaigns = state.noOrderSpendCampaigns) {
  const button = document.getElementById("pause-no-order-spend-campaigns-btn");
  if (!button) return;
  const targets = closeableNoOrderSpendCampaigns(campaigns);
  button.disabled = !targets.length || state.pausingCampaignIds.size > 0;
  button.textContent = targets.length > 0 ? `关闭 ${formatNumber(targets.length)} 个系列` : "关闭系列";
}

async function pauseNoOrderSpendCampaigns(campaigns = state.noOrderSpendCampaigns) {
  const targets = closeableNoOrderSpendCampaigns(campaigns);
  if (!targets.length) {
    showError("当前没有可关闭的系列，可能缺少 campaign_id 或已经关闭。");
    return;
  }

  const preview = targets
    .slice(0, 5)
    .map((row) => `- ${compactText(row.name, 48)} · 花费 ${formatCurrency(row.spend)} · 购买 ${formatNumber(row.purchase)}`)
    .join("\n");
  const more = targets.length > 5 ? `\n...另有 ${formatNumber(targets.length - 5)} 个系列` : "";
  const confirmed = window.confirm(
    `确认关闭 ${formatNumber(targets.length)} 个系列？\n${preview}${more}\n\n关闭后这些 Facebook Campaign 状态会变为 PAUSED。`,
  );
  if (!confirmed) return;

  const campaignIds = targets.map((row) => row.id);
  campaignIds.forEach((id) => state.pausingCampaignIds.add(id));
  clearError();
  setSyncStatus(`正在关闭 ${formatNumber(campaignIds.length)} 个系列`);
  renderNoOrderSpendCampaigns(state.payload?.tables?.ads || []);

  try {
    const result = await fetchJson("/api/campaigns/pause", {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({ campaignIds, confirm: "PAUSE_CAMPAIGNS" }),
    });
    const rows = result.results || [];
    const successIds = rows.filter((row) => row.ok).map((row) => String(row.campaignId || ""));
    successIds.forEach((id) => state.pausedCampaignIds.add(id));

    const failed = rows.filter((row) => !row.ok);
    if (failed.length) {
      showError(`有 ${formatNumber(failed.length)} 个系列关闭失败：${failed.map((row) => row.error || row.campaignId).join("；")}`);
    }
    addOperation(`关闭系列完成 · 成功 ${formatNumber(result.pausedCount || 0)} / 失败 ${formatNumber(result.failedCount || 0)}`);
    setSyncStatus(`关闭完成 · 成功 ${formatNumber(result.pausedCount || 0)}`);

    if (successIds.length) {
      queueAutoAdReveal();
      await loadDashboard({ refresh: true });
    }
  } catch (error) {
    showError(error.message || "关闭系列失败");
    addOperation(`关闭系列失败 · ${error.message || "未知错误"}`);
    setSyncStatus("关闭系列失败");
  } finally {
    campaignIds.forEach((id) => state.pausingCampaignIds.delete(id));
    renderNoOrderSpendCampaigns(state.payload?.tables?.ads || []);
  }
}

function renderQualityCampaigns(ads) {
  const summary = document.getElementById("quality-campaign-summary");
  const list = document.getElementById("quality-campaign-list");
  const roasInput = document.getElementById("quality-roas-threshold");
  const purchaseInput = document.getElementById("quality-purchase-threshold");
  if (!summary || !list) return;
  if (roasInput && roasInput.value !== state.qualityRoasThreshold) roasInput.value = state.qualityRoasThreshold;
  if (purchaseInput && purchaseInput.value !== state.qualityPurchaseThreshold) purchaseInput.value = state.qualityPurchaseThreshold;

  if (state.qualityRoasThreshold === "" || state.qualityPurchaseThreshold === "") {
    state.qualityCampaigns = [];
    summary.textContent = "输入阈值后检查";
    list.innerHTML = `<p class="empty">按当前口径：系列 ROAS 达标，且购买数达标，就进入复制候选。</p>`;
    updateQualityCopyButton();
    return;
  }

  const roasThreshold = toNumber(state.qualityRoasThreshold);
  const purchaseThreshold = toNumber(state.qualityPurchaseThreshold);
  const campaigns = buildCampaignSpendRows(ads)
    .filter((row) => row.purchase >= purchaseThreshold && row.roas >= roasThreshold && row.spend > 0)
    .sort((a, b) => b.purchase - a.purchase || b.roas - a.roas || b.revenue - a.revenue)
    .slice(0, 10);
  state.qualityCampaigns = campaigns;

  summary.textContent = `${formatNumber(campaigns.length)} 个优质系列可复制`;
  if (!campaigns.length) {
    list.innerHTML = `<p class="empty">当前没有达到 ROAS 和购买阈值的系列。</p>`;
    updateQualityCopyButton(campaigns);
    return;
  }

  list.innerHTML = campaigns
    .map((row) => {
      const isCopied = row.id && state.copiedCampaignIds.has(row.id);
      const isCopying = row.id && state.copyingCampaignIds.has(row.id);
      const disabled = !row.id || isCopied || isCopying ? "disabled" : "";
      const buttonText = isCopied ? "已复制" : isCopying ? "复制中" : "复制系列";
      return `
        <article class="quality-campaign">
          <button class="quality-campaign-focus" type="button" data-campaign-focus="${escapeHtml(row.name)}">
            <strong>优质系列 · ${escapeHtml(compactText(row.name, 50))}</strong>
            <span>ROAS ${formatRatio(row.roas)} · 购买 ${formatNumber(row.purchase)} · 收入 ${formatCurrency(row.revenue)} · 花费 ${formatCurrency(row.spend)}</span>
          </button>
          <button class="campaign-copy-btn" type="button" data-copy-campaign-id="${escapeHtml(row.id || "")}" data-copy-campaign-name="${escapeHtml(row.name)}" ${disabled}>${buttonText}</button>
        </article>
      `;
    })
    .join("");

  updateQualityCopyButton(campaigns);

  list.querySelectorAll("[data-campaign-focus]").forEach((button) => {
    button.addEventListener("click", () => focusCampaign(button.dataset.campaignFocus || ""));
  });
  list.querySelectorAll("[data-copy-campaign-id]").forEach((button) => {
    button.addEventListener("click", () => {
      const campaignId = button.dataset.copyCampaignId || "";
      const campaign = state.qualityCampaigns.find((row) => row.id === campaignId);
      copyQualityCampaigns(campaign ? [campaign] : []);
    });
  });
}

function copyableQualityCampaigns(campaigns = state.qualityCampaigns) {
  const seen = new Set();
  return (campaigns || []).filter((row) => {
    const campaignId = String(row.id || "").trim();
    if (!campaignId || seen.has(campaignId)) return false;
    if (state.copiedCampaignIds.has(campaignId) || state.copyingCampaignIds.has(campaignId)) return false;
    seen.add(campaignId);
    return true;
  });
}

function updateQualityCopyButton(campaigns = state.qualityCampaigns) {
  const button = document.getElementById("copy-quality-campaigns-btn");
  if (!button) return;
  const targets = copyableQualityCampaigns(campaigns);
  button.disabled = !targets.length || state.copyingCampaignIds.size > 0;
  button.textContent = targets.length > 0 ? `复制 ${formatNumber(targets.length)} 个系列` : "复制系列";
}

async function copyQualityCampaigns(campaigns = state.qualityCampaigns) {
  const targets = copyableQualityCampaigns(campaigns);
  if (!targets.length) {
    showError("当前没有可复制的优质系列，可能缺少 campaign_id 或已经复制。");
    return;
  }

  const preview = targets
    .slice(0, 5)
    .map((row) => `- ${compactText(row.name, 48)} · ROAS ${formatRatio(row.roas)} · 购买 ${formatNumber(row.purchase)}`)
    .join("\n");
  const more = targets.length > 5 ? `\n...另有 ${formatNumber(targets.length - 5)} 个系列` : "";
  const confirmed = window.confirm(
    `确认复制 ${formatNumber(targets.length)} 个优质系列？\n${preview}${more}\n\n复制出来的新 Campaign 默认 PAUSED，检查后再手动启用。`,
  );
  if (!confirmed) return;

  const campaignIds = targets.map((row) => row.id);
  campaignIds.forEach((id) => state.copyingCampaignIds.add(id));
  clearError();
  setSyncStatus(`正在复制 ${formatNumber(campaignIds.length)} 个优质系列`);
  renderQualityCampaigns(state.payload?.tables?.ads || []);

  try {
    const result = await fetchJson("/api/campaigns/copy", {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({
        campaignIds,
        confirm: "COPY_CAMPAIGNS",
        renameSuffix: campaignCopySuffix(),
        statusOption: "PAUSED",
        deepCopy: true,
      }),
    });
    const rows = result.results || [];
    const successIds = rows.filter((row) => row.ok).map((row) => String(row.campaignId || ""));
    successIds.forEach((id) => state.copiedCampaignIds.add(id));

    const failed = rows.filter((row) => !row.ok);
    if (failed.length) {
      showError(`有 ${formatNumber(failed.length)} 个系列复制失败：${failed.map((row) => row.error || row.campaignId).join("；")}`);
    }
    addOperation(`复制优质系列完成 · 成功 ${formatNumber(result.copiedCount || 0)} / 失败 ${formatNumber(result.failedCount || 0)}`);
    setSyncStatus(`复制完成 · 成功 ${formatNumber(result.copiedCount || 0)}`);
  } catch (error) {
    showError(error.message || "复制系列失败");
    addOperation(`复制系列失败 · ${error.message || "未知错误"}`);
    setSyncStatus("复制系列失败");
  } finally {
    campaignIds.forEach((id) => state.copyingCampaignIds.delete(id));
    renderQualityCampaigns(state.payload?.tables?.ads || []);
  }
}

function campaignCopySuffix() {
  const date = new Date();
  const pad = (value) => String(value).padStart(2, "0");
  return ` - QUALITY_COPY_${date.getFullYear()}${pad(date.getMonth() + 1)}${pad(date.getDate())}_${pad(date.getHours())}${pad(date.getMinutes())}`;
}

function buildCampaignSpendRows(ads) {
  const buckets = new Map();
  (ads || []).forEach((row) => {
    const id = String(row.campaign_id || "").trim();
    const name = row.campaign_name || id || "-";
    const key = id || name;
    if (!buckets.has(key)) {
      buckets.set(key, { id, name, spend: 0, revenue: 0, purchase: 0, ads: 0 });
    }
    const item = buckets.get(key);
    if (!item.id && id) item.id = id;
    if ((!item.name || item.name === "-") && name) item.name = name;
    item.spend += toNumber(row.spend);
    item.revenue += toNumber(row.purchase_value);
    item.purchase += toNumber(row.purchase);
    item.ads += 1;
  });
  return [...buckets.values()].map((row) => ({
    ...row,
    roas: row.spend ? row.revenue / row.spend : 0,
  }));
}

function focusCampaign(campaignName) {
  if (!campaignName) return;
  state.search = campaignName;
  state.filter = "all";
  state.quick = "all";
  state.page = 1;
  queueAutoAdReveal();
  syncFilterButtons();
  syncQuickButtons();
  syncSearchInput();
  renderView();
  addOperation(`查看无单花费系列 · ${compactText(campaignName, 36)}`);
}

function campaignNoOrderSpendThresholdKey() {
  return `fbCampaignNoOrderSpendThreshold:${state.range}`;
}

function loadCampaignNoOrderSpendThreshold() {
  try {
    state.campaignNoOrderSpendThreshold =
      localStorage.getItem(campaignNoOrderSpendThresholdKey()) ||
      localStorage.getItem(`fbCampaignProfitThreshold:${state.range}`) ||
      state.campaignNoOrderSpendThreshold ||
      "";
  } catch {
    state.campaignNoOrderSpendThreshold = state.campaignNoOrderSpendThreshold || "";
  }
  const input = document.getElementById("campaign-spend-threshold");
  if (input) input.value = state.campaignNoOrderSpendThreshold;
}

function saveCampaignNoOrderSpendThreshold() {
  try {
    if (state.campaignNoOrderSpendThreshold === "") {
      localStorage.removeItem(campaignNoOrderSpendThresholdKey());
    } else {
      localStorage.setItem(campaignNoOrderSpendThresholdKey(), state.campaignNoOrderSpendThreshold);
    }
  } catch {
    // Local storage can be unavailable in restricted browser contexts.
  }
}

function qualityCampaignThresholdsKey() {
  return `fbQualityCampaignThresholds:${state.range}`;
}

function loadQualityCampaignThresholds() {
  try {
    const saved = localStorage.getItem(qualityCampaignThresholdsKey());
    if (saved) {
      const data = JSON.parse(saved);
      state.qualityRoasThreshold = String(data.roas ?? state.qualityRoasThreshold ?? "2");
      state.qualityPurchaseThreshold = String(data.purchase ?? state.qualityPurchaseThreshold ?? "1");
    } else {
      state.qualityRoasThreshold = state.qualityRoasThreshold || "2";
      state.qualityPurchaseThreshold = state.qualityPurchaseThreshold || "1";
    }
  } catch {
    state.qualityRoasThreshold = state.qualityRoasThreshold || "2";
    state.qualityPurchaseThreshold = state.qualityPurchaseThreshold || "1";
  }
  const roasInput = document.getElementById("quality-roas-threshold");
  const purchaseInput = document.getElementById("quality-purchase-threshold");
  if (roasInput) roasInput.value = state.qualityRoasThreshold;
  if (purchaseInput) purchaseInput.value = state.qualityPurchaseThreshold;
}

function saveQualityCampaignThresholds() {
  try {
    localStorage.setItem(
      qualityCampaignThresholdsKey(),
      JSON.stringify({
        roas: state.qualityRoasThreshold,
        purchase: state.qualityPurchaseThreshold,
      }),
    );
  } catch {
    // Local storage can be unavailable in restricted browser contexts.
  }
}

function actionPriority(action) {
  return { fix_landing: 1, reduce: 2, scale: 3, watch: 4, idle: 5 }[action] || 9;
}

function backendOrdersKey() {
  return `fbBackendOrders:${state.range}`;
}

function loadBackendOrders() {
  try {
    state.backendOrders = localStorage.getItem(backendOrdersKey()) || "";
  } catch {
    state.backendOrders = "";
  }
  const input = document.getElementById("backend-orders-input");
  if (input) input.value = state.backendOrders;
}

function saveBackendOrders() {
  try {
    if (state.backendOrders === "") {
      localStorage.removeItem(backendOrdersKey());
    } else {
      localStorage.setItem(backendOrdersKey(), state.backendOrders);
    }
  } catch {
    // Local storage can be unavailable in restricted browser contexts.
  }
}

function renderScopeChip(view) {
  const mount = document.getElementById("scope-chip");
  if (!mount) return;
  const parts = [
    `范围 ${humanRange(state.range)}`,
    state.search ? `搜索 ${state.search}` : "",
    state.filter !== "all" ? `动作 ${actionLabel(state.filter)}` : "",
    state.quick !== "all" ? `快捷 ${quickFilterLabel(state.quick)}` : "",
    `排序 ${state.sortKey}:${state.sortDir}`,
    `第 ${formatNumber(view.page)} / ${formatNumber(view.pageCount)} 页`,
  ].filter(Boolean);
  mount.hidden = !parts.length;
  mount.textContent = parts.join(" · ");
}

function nextItemFromAd(label, row) {
  if (!row) return null;
  return {
    label,
    text: `${compactText(row.ad_name || row.ad_id, 34)} · ${formatCurrency(row.spend)} · ${formatRatio(row.roas)}`,
  };
}

function renderFunnel(steps) {
  const mount = document.getElementById("funnel");
  if (!mount) return;
  if (!steps.length) {
    mount.innerHTML = emptyBlock("暂无漏斗数据");
    return;
  }
  mount.innerHTML = steps
    .map((step, index) => {
      const share = clamp(toNumber(step.share), 0, 100);
      return `
        <div class="funnel-step">
          <div class="funnel-head">
            <span>${escapeHtml(step.label)}</span>
            <strong>${formatNumber(step.value)}</strong>
          </div>
          <div class="funnel-track"><span style="--width:${share}%"></span></div>
          <div class="funnel-foot">
            <small>${index ? `上一步 ${formatPercent(step.previous_rate)}` : "起点 100%"}</small>
            <small>峰值占比 ${formatPercent(step.share)}</small>
          </div>
        </div>
      `;
    })
    .join("");
}

function renderActionBreakdown(items) {
  const mount = document.getElementById("action-breakdown");
  if (!mount) return;
  if (!items.length) {
    mount.innerHTML = emptyBlock("暂无动作数据");
    return;
  }
  mount.innerHTML = items
    .map(
      (item) => `
        <div class="meter-row" data-tone="${escapeHtml(item.tone)}">
          <div class="meter-head">
            <span>${escapeHtml(item.label)}</span>
            <strong>${formatNumber(item.value)} · ${formatPercent(item.share)}</strong>
          </div>
          <div class="meter-track"><span style="--width:${clamp(item.share, 0, 100)}%"></span></div>
        </div>
      `,
    )
    .join("");
}

function renderAccountTable(rows) {
  const html = rows
    .map(
      (row) => `
        <tr>
          <td data-label="账户"><strong>${escapeHtml(row.account_name || row.account_id || "-")}</strong></td>
          <td data-label="花费">${formatCurrency(row.spend)}</td>
          <td data-label="购买">${formatNumber(row.purchase)}</td>
          <td data-label="ROAS">${formatRatio(row.roas)}</td>
          <td data-label="点击">${formatNumber(row.clicks)}</td>
          <td data-label="警告">${formatNumber(row.warning)}</td>
          <td data-label="机会">${formatNumber(row.opportunity)}</td>
        </tr>
      `,
    )
    .join("");
  renderTable("account-table", html, 7);
}

function renderAggregateTable(id, rows, label) {
  const html = rows
    .map(
      (row) => `
        <tr>
          <td data-label="${escapeHtml(label)}"><strong>${escapeHtml(row.name || "-")}</strong></td>
          <td data-label="广告数">${formatNumber(row.ads)}</td>
          <td data-label="花费">${formatCurrency(row.spend)}</td>
          <td data-label="购买">${formatNumber(row.purchase)}</td>
          <td data-label="ROAS">${formatRatio(row.roas)}</td>
          <td data-label="CPA">${formatCurrency(row.cpa)}</td>
          <td data-label="CTR">${formatPercent(row.ctr)}</td>
        </tr>
      `,
    )
    .join("");
  renderTable(id, html, 7);
}

function renderPriorityList(items) {
  const mount = document.getElementById("priority-list");
  if (!mount) return;
  if (!items.length) {
    mount.innerHTML = emptyBlock("暂无优先处理项");
    return;
  }
  mount.innerHTML = items
    .slice(0, 10)
    .map(
      (item) => `
        <div class="signal-card ${escapeHtml(item.tone)}" ${item.adId ? `data-ad-id="${escapeHtml(item.adId)}" role="button" tabindex="0"` : ""}>
          <strong>${escapeHtml(item.title)}</strong>
          <span>${escapeHtml(item.detail)}</span>
        </div>
      `,
    )
    .join("");
}

function renderScaleList(rows) {
  const mount = document.getElementById("scale-list");
  if (!mount) return;
  if (!rows.length) {
    mount.innerHTML = emptyBlock("暂无放量候选");
    return;
  }
  mount.innerHTML = rows
    .map(
      (row) => `
        <div class="signal-card good" data-ad-id="${escapeHtml(adRowId(row))}" role="button" tabindex="0">
          <strong>${escapeHtml(compactText(row.ad_name || row.ad_id, 54))}</strong>
          <span>${escapeHtml(row.account_name || "-")} · ${formatCurrency(row.spend)} · ${formatNumber(row.purchase)} 单 · ${formatRatio(row.roas)}</span>
        </div>
      `,
    )
    .join("");
}

function renderAdTable(rows) {
  const html = rows
    .map(
      (row) => `
        <tr data-ad-id="${escapeHtml(adRowId(row))}" class="${state.detailOpen && adRowId(row) === String(state.selectedAdId) ? rowClass(row) : ""}">
          <td data-label="广告">
            <strong>${escapeHtml(row.ad_name || row.ad_id || "-")}</strong>
            <span class="muted">${escapeHtml(row.ad_id || "-")}</span>
          </td>
          <td data-label="账户">${escapeHtml(row.account_name || "-")}</td>
          <td data-label="素材家族">${escapeHtml(row.family || "-")}</td>
          <td data-label="花费">${formatCurrency(row.spend)}</td>
          <td data-label="购买">${formatNumber(row.purchase)}</td>
          <td data-label="ROAS">${formatRatio(row.roas)}</td>
          <td data-label="CPA">${formatCurrency(row.cpa)}</td>
          <td data-label="ATC">${formatNumber(row.add_to_cart)}</td>
          <td data-label="动作">${actionPill(row.action, row.action_label)}</td>
        </tr>
      `,
    )
    .join("");
  renderTable("ad-table", html, 9);
}

function renderFindingGrid(rows) {
  const mount = document.getElementById("finding-list");
  if (!mount) return;
  if (!rows.length) {
    mount.innerHTML = emptyBlock("暂无符合筛选的诊断");
    return;
  }
  mount.innerHTML = rows
    .slice(0, 72)
    .map((row) => {
      const level = String(row.level || "info").toLowerCase();
      const title = row.name || row.entity || row.entity_id || "诊断";
      const stats = [
        row.category || row.level,
        row.action ? actionLabel(row.action) : "",
        toNumber(row.spend) ? formatCurrency(row.spend) : "",
        toNumber(row.roas) ? formatRatio(row.roas) : "",
      ].filter(Boolean);
      return `
        <article class="finding-card ${escapeHtml(level)}">
          <span>${escapeHtml(level.toUpperCase())}</span>
          <strong>${escapeHtml(compactText(title, 76))}</strong>
          <p>${escapeHtml(compactText(row.reason || row.category || "-", 140))}</p>
          <div class="finding-meta">${stats.map((item) => `<small>${escapeHtml(item)}</small>`).join("")}</div>
        </article>
      `;
    })
    .join("");
}

function renderTable(id, html, colspan) {
  const node = document.getElementById(id);
  if (!node) return;
  node.innerHTML = html || `<tr><td colspan="${colspan}" class="empty">暂无符合筛选的数据</td></tr>`;
}

function buildPriorityItems(ads, findings) {
  const severity = { critical: 5, warning: 4, opportunity: 3, info: 1 };
  const findingItems = findings
    .slice()
    .sort((a, b) => (severity[b.level] || 0) - (severity[a.level] || 0) || toNumber(b.spend) - toNumber(a.spend))
    .slice(0, 8)
    .map((row) => ({
      tone: row.level || row.tone || "info",
      title: row.name || row.entity || row.entity_id || "诊断",
      detail: `${row.category || row.level || "-"} · ${compactText(row.reason || "-", 92)}`,
      adId: row.entity_id ? String(row.entity_id) : "",
    }));

  const riskItems = ads
    .filter((row) => ["reduce", "fix_landing"].includes(row.action))
    .slice()
    .sort((a, b) => toNumber(b.spend) - toNumber(a.spend))
    .slice(0, 6)
    .map((row) => ({
      tone: row.tone || ACTION_TONES[row.action] || "warn",
      title: `${actionLabel(row.action)} · ${compactText(row.ad_name || row.ad_id, 54)}`,
      detail: `${row.account_name || "-"} · ${formatCurrency(row.spend)} · ${formatRatio(row.roas)} · 点击 ${formatNumber(row.link_clicks || row.clicks)}`,
      adId: adRowId(row),
    }));

  return [...findingItems, ...riskItems].slice(0, 10);
}

function buildActionBreakdown(ads) {
  const total = ads.length || 1;
  const counts = ads.reduce((acc, row) => {
    const action = row.action || "watch";
    acc[action] = (acc[action] || 0) + 1;
    return acc;
  }, {});
  return ["scale", "reduce", "fix_landing", "watch", "idle"]
    .filter((action) => counts[action])
    .map((action) => ({
      action,
      label: actionLabel(action),
      value: counts[action],
      share: (counts[action] / total) * 100,
      tone: ACTION_TONES[action] || "info",
    }));
}

function buildFunnel(ads, accounts) {
  const impressions = sum(ads, "impressions") || sum(accounts, "impressions");
  const clicks =
    ads.reduce((total, row) => total + Math.max(toNumber(row.inline_link_clicks), toNumber(row.clicks)), 0) ||
    sum(accounts, "clicks");
  const atc = sum(ads, "add_to_cart");
  const checkout = sum(ads, "checkout");
  const purchase = sum(ads, "purchase") || sum(accounts, "purchase");
  const steps = [
    ["展示", impressions],
    ["点击", clicks],
    ["加购", atc],
    ["结账", checkout],
    ["购买", purchase],
  ];
  const top = Math.max(...steps.map(([, value]) => value), 1);
  return steps.map(([label, value], index) => ({
    label,
    value,
    share: top ? (value / top) * 100 : 0,
    previous_rate: index ? percentage(value, steps[index - 1][1]) : 100,
  }));
}

function aggregate(rows, key) {
  const buckets = new Map();
  rows.forEach((row) => {
    const name = row[key] || "-";
    if (!buckets.has(name)) {
      buckets.set(name, {
        name,
        ads: 0,
        spend: 0,
        impressions: 0,
        clicks: 0,
        purchase: 0,
        purchase_value: 0,
        add_to_cart: 0,
      });
    }
    const bucket = buckets.get(name);
    bucket.ads += 1;
    bucket.spend += toNumber(row.spend);
    bucket.impressions += toNumber(row.impressions);
    bucket.clicks += toNumber(row.clicks);
    bucket.purchase += toNumber(row.purchase);
    bucket.purchase_value += toNumber(row.purchase_value);
    bucket.add_to_cart += toNumber(row.add_to_cart);
  });

  return [...buckets.values()]
    .map((row) => ({
      ...row,
      roas: row.spend ? row.purchase_value / row.spend : 0,
      cpa: row.purchase ? row.spend / row.purchase : 0,
      ctr: percentage(row.clicks, row.impressions),
    }))
    .sort((a, b) => b.spend - a.spend);
}

function matchesAdFilter(row, filter) {
  if (filter === "all") return true;
  if (filter === "warning") {
    return ["warn", "bad"].includes(String(row.tone || ACTION_TONES[row.action] || ""));
  }
  return row.action === filter;
}

function matchesFindingFilter(row, filter) {
  if (filter === "all") return true;
  if (filter === "warning") {
    return ["critical", "warning", "opportunity"].includes(String(row.level || "").toLowerCase()) ||
      ["warn", "bad"].includes(String(row.tone || "").toLowerCase());
  }
  return row.action === filter;
}

function matchesSearch(text, query) {
  return !query || normalizeText(text).includes(query);
}

function adSearchText(row) {
  return [
    row.account_name,
    row.campaign_name,
    row.adset_name,
    row.ad_name,
    row.ad_id,
    row.family,
    row.action_label,
    row.effective_status,
  ].join(" ");
}

function findingSearchText(row) {
  return [
    row.account_name,
    row.level,
    row.entity,
    row.category,
    row.name,
    row.entity_id,
    row.reason,
    row.action,
    row.family,
  ].join(" ");
}

function accountSearchText(row) {
  return [row.account_name, row.account_id, row.preset].join(" ");
}

function syncRangeButtons() {
  document.querySelectorAll("[data-range]").forEach((button) => {
    button.classList.toggle("active", button.dataset.range === state.range);
  });
}

function syncUrlRange() {
  const params = new URLSearchParams(window.location.search);
  params.set("range", state.range);
  const nextUrl = `${window.location.pathname}?${params.toString()}`;
  window.history.replaceState({}, "", nextUrl);
}

function syncFilterButtons() {
  document.querySelectorAll("[data-filter]").forEach((button) => {
    button.classList.toggle("active", button.dataset.filter === state.filter);
  });
}

function syncQuickButtons() {
  document.querySelectorAll("[data-quick]").forEach((button) => {
    button.classList.toggle("active", button.dataset.quick === state.quick);
  });
}

function matchesQuickFilter(row, filter) {
  if (filter === "all") return true;
  if (filter === "spent") return toNumber(row.spend) > 0;
  if (filter === "purchase") return toNumber(row.purchase) > 0;
  if (filter === "no_purchase") return toNumber(row.spend) > 0 && toNumber(row.purchase) === 0;
  if (filter === "risk") {
    return ["reduce", "fix_landing"].includes(row.action) ||
      ["warn", "bad"].includes(String(row.tone || ACTION_TONES[row.action] || "").toLowerCase());
  }
  return true;
}

function sortRows(rows) {
  const direction = state.sortDir === "asc" ? 1 : -1;
  return rows.slice().sort((a, b) => {
    const left = sortValue(a, state.sortKey, state.sortDir);
    const right = sortValue(b, state.sortKey, state.sortDir);
    if (left !== right) return left > right ? direction : -direction;
    return toNumber(b.spend) - toNumber(a.spend);
  });
}

function sortValue(row, key, direction) {
  if (key === "clicks") return Math.max(toNumber(row.inline_link_clicks), toNumber(row.link_clicks), toNumber(row.clicks));
  if (key === "cpa" && direction === "asc") {
    return toNumber(row.purchase) > 0 ? toNumber(row.cpa) : Number.POSITIVE_INFINITY;
  }
  return toNumber(row[key]);
}

function renderAdPager(view) {
  const info = document.getElementById("ad-page-info");
  const prev = document.getElementById("prev-page-btn");
  const next = document.getElementById("next-page-btn");
  const sortSelect = document.getElementById("ad-sort-select");
  const pageSizeSelect = document.getElementById("page-size-select");
  const pageStart = view.filteredAds ? (view.page - 1) * view.pageSize + 1 : 0;
  const pageEnd = Math.min(view.page * view.pageSize, view.filteredAds);

  if (info) {
    info.textContent = `第 ${formatNumber(view.page)} / ${formatNumber(view.pageCount)} 页 · ${formatNumber(pageStart)}-${formatNumber(pageEnd)} / ${formatNumber(view.filteredAds)}`;
  }
  if (prev) prev.disabled = view.page <= 1;
  if (next) next.disabled = view.page >= view.pageCount;
  if (sortSelect) sortSelect.value = `${state.sortKey}:${state.sortDir}`;
  if (pageSizeSelect) pageSizeSelect.value = String(state.pageSize);
}

function renderAdDetail() {
  const drawer = document.getElementById("ad-detail-drawer");
  const title = document.getElementById("detail-title");
  const body = document.getElementById("detail-body");
  if (!drawer || !title || !body) return;

  if (!state.detailOpen) {
    drawer.hidden = true;
    document.body.classList.remove("detail-open");
    return;
  }

  let row = state.adIndex.get(String(state.selectedAdId));
  if (!row && state.currentAds.length) {
    row = state.currentAds[0];
    state.selectedAdId = row.ad_id || row.ad_name || "";
  }
  if (!row) {
    drawer.hidden = true;
    document.body.classList.remove("detail-open");
    return;
  }

  drawer.hidden = false;
  document.body.classList.add("detail-open");
  title.textContent = compactText(row.ad_name || row.ad_id || "未命名广告", 60);

  const effectMetrics = [
    ["花费", row.spend, formatCurrency],
    ["购买", row.purchase, formatNumber],
    ["收入", row.purchase_value, formatCurrency],
    ["ROAS", row.roas, formatRatio],
    ["CPA", row.cpa, formatCurrency],
    ["CTR", row.ctr, formatPercent],
  ];
  const funnelMetrics = [
    ["展示", row.impressions, formatNumber],
    ["点击", Math.max(toNumber(row.inline_link_clicks), toNumber(row.link_clicks), toNumber(row.clicks)), formatNumber],
    ["落地页", row.landing_page_view, formatNumber],
    ["加购", row.add_to_cart, formatNumber],
    ["结账", row.checkout, formatNumber],
    ["支付信息", row.add_payment_info, formatNumber],
  ];
  const statusFields = [
    ["账户", row.account_name || row.account_id],
    ["Campaign", row.campaign_name || row.campaign_id],
    ["Adset", row.adset_name || row.adset_id],
    ["素材家族", row.family],
    ["投放状态", firstFilled(row, ["effective_status", "status", "configured_status"])],
    ["学习状态", firstFilled(row, ["learning_status", "delivery_info"])],
    ["日预算", formatMaybeCurrency(firstFilled(row, ["daily_budget", "budget", "adset_daily_budget"]))],
    ["优化目标", firstFilled(row, ["optimization_goal", "objective"])],
  ];

  body.innerHTML = `
    <div class="detail-summary">
      <div>
        <span>建议动作</span>
        ${actionPill(row.action, row.action_label)}
      </div>
      <p>${escapeHtml(actionReason(row))}</p>
    </div>
    <div class="detail-metrics">
      ${effectMetrics.map(([label, value, formatter]) => detailMetric(label, value, formatter)).join("")}
    </div>
    <section class="detail-section">
      <h3>漏斗</h3>
      <div class="detail-metrics compact">
        ${funnelMetrics.map(([label, value, formatter]) => detailMetric(label, value, formatter)).join("")}
      </div>
    </section>
    <section class="detail-section">
      <h3>投放信息</h3>
      <div class="detail-fields">
        ${statusFields.map(([label, value]) => detailField(label, value)).join("")}
        ${detailField("广告 ID", row.ad_id || "-")}
      </div>
    </section>
  `;
}

function closeAdDetail() {
  if (!state.detailOpen) return;
  state.autoRevealDetail = false;
  state.preferTopAd = false;
  state.autoSelectedAdId = "";
  state.detailOpen = false;
  renderAdDetail();
  renderAdTable(state.currentAds.slice((state.page - 1) * state.pageSize, state.page * state.pageSize));
}

function detailMetric(label, value, formatter) {
  return `
    <div class="detail-metric">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(formatter(value))}</strong>
    </div>
  `;
}

function detailField(label, value) {
  const text = value === null || value === undefined || value === "" ? "-" : String(value);
  return `
    <div class="detail-field">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(text)}</strong>
    </div>
  `;
}

function actionReason(row) {
  const purchase = toNumber(row.purchase);
  const spend = toNumber(row.spend);
  const roas = toNumber(row.roas);
  const clicks = Math.max(toNumber(row.inline_link_clicks), toNumber(row.link_clicks), toNumber(row.clicks));
  const atc = toNumber(row.add_to_cart);
  if (row.action === "scale") return `已有 ${formatNumber(purchase)} 次购买且 ROAS ${formatRatio(roas)}，适合小步测试加预算。`;
  if (row.action === "fix_landing") return `点击 ${formatNumber(clicks)} 次但加购为 ${formatNumber(atc)}，优先检查落地页、价格和结账承接。`;
  if (row.action === "reduce") return `已有花费 ${formatCurrency(spend)}，但 ROAS ${formatRatio(roas)} 偏低，先降预算或换素材。`;
  if (row.action === "idle") return "当前没有明显消耗，先观察投放状态和预算是否正常。";
  return `当前花费 ${formatCurrency(spend)}，ROAS ${formatRatio(roas)}，暂时保持观察。`;
}

function firstFilled(row, keys) {
  for (const key of keys) {
    const value = row[key];
    if (value !== null && value !== undefined && value !== "") return value;
  }
  return "-";
}

function formatMaybeCurrency(value) {
  if (value === "-" || value === null || value === undefined || value === "") return "-";
  const number = Number(value);
  return Number.isFinite(number) ? formatCurrency(number) : String(value);
}

function sourceModeLabel(value) {
  const map = {
    cache: "缓存报表",
    pulled: "实时拉取",
    direct: "指定报表",
  };
  return map[value] || value || "-";
}

function renderStatus(view) {
  const parts = [
    `范围 ${humanRange(state.range)}`,
    `广告 ${formatNumber(view.ads.length)} / ${formatNumber(view.totalAds)}`,
    `诊断 ${formatNumber(view.findings.length)} / ${formatNumber(view.totalFindings)}`,
  ];
  if (state.search) parts.push(`搜索 “${state.search}”`);
  if (state.filter !== "all") parts.push(`筛选 ${ACTION_LABELS[state.filter] || state.filter}`);
  if (state.quick !== "all") parts.push(`快捷 ${quickFilterLabel(state.quick)}`);
  parts.push(`第 ${formatNumber(view.page)} 页`);
  setStatus(parts.join(" · "));
}

function quickFilterLabel(value) {
  return {
    spent: "有花费",
    purchase: "有购买",
    no_purchase: "花费无购买",
    risk: "高风险",
  }[value] || value;
}

function queueAutoAdReveal() {
  state.autoRevealDetail = false;
  state.preferTopAd = false;
  state.autoSelectedAdId = "";
  state.detailOpen = false;
}

function adRowId(row) {
  return String(row?.ad_id || row?.ad_name || "");
}

function rowClass(row) {
  const classes = ["selected"];
  if (adRowId(row) === String(state.autoSelectedAdId)) {
    classes.push("auto-selected");
  }
  return classes.join(" ");
}

function syncSearchInput() {
  const search = document.getElementById("search-input");
  if (search && search.value !== state.search) {
    search.value = state.search;
  }
}

function compareValue(label, value) {
  if (value === null || value === undefined || value === "") return "-";
  if (["花费", "spend", "CPA"].includes(label)) return formatCurrency(value);
  if (label === "CTR") return formatPercent(value);
  if (label === "ROAS") return formatRatio(value);
  return formatNumber(value);
}

function compareDelta(item) {
  if (!item) return "-";
  const delta = toNumber(item.delta);
  const percent = item.pct;
  const prefix = delta > 0 ? "+" : "";
  const deltaText = `${prefix}${formatNumber(delta)}`;
  if (percent === null || percent === undefined) return deltaText;
  return `${deltaText} (${prefix}${formatNumber(percent)}%)`;
}

function cssEscape(value) {
  if (window.CSS && typeof window.CSS.escape === "function") {
    return window.CSS.escape(String(value));
  }
  return String(value).replace(/["\\]/g, "\\$&");
}

function actionPill(action, label) {
  const tone = ACTION_TONES[action] || "info";
  return `<span class="pill ${escapeHtml(tone)}">${escapeHtml(label || actionLabel(action))}</span>`;
}

function actionLabel(action) {
  return ACTION_LABELS[action] || String(action || "-").replaceAll("_", " ");
}

function normalizeRange(value) {
  const allowed = new Set(["today", "yesterday", "last_7d", "last_30d"]);
  const range = String(value || "").trim();
  return allowed.has(range) ? range : "last_7d";
}

function humanRange(value) {
  const map = {
    today: "今天",
    yesterday: "昨天",
    last_1d: "近 1 天",
    last_3d: "近 3 天",
    last_7d: "近 7 天",
    last_14d: "近 14 天",
    last_28d: "近 28 天",
    last_30d: "近 30 天",
  };
  return map[value] || value || "-";
}

function emptyBlock(text) {
  return `<p class="empty">${escapeHtml(text)}</p>`;
}

function setStatus(text) {
  setText("status-text", text || "-");
}

function showError(message) {
  const panel = document.getElementById("error-panel");
  if (!panel) return;
  panel.textContent = message || "加载失败";
  panel.hidden = false;
}

function clearError() {
  const panel = document.getElementById("error-panel");
  if (!panel) return;
  panel.textContent = "";
  panel.hidden = true;
}

function sum(rows, key) {
  return (rows || []).reduce((total, row) => total + toNumber(row[key]), 0);
}

function percentage(part, whole) {
  return whole ? (part / whole) * 100 : 0;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function toNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

function formatCurrency(value) {
  if (value === null || value === undefined || value === "") return "-";
  const number = toNumber(value);
  return `$${new Intl.NumberFormat("en-US", {
    maximumFractionDigits: number >= 100 ? 0 : 2,
  }).format(number)}`;
}

function formatNumber(value) {
  if (value === null || value === undefined || value === "") return "-";
  const number = toNumber(value);
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(number);
}

function formatPercent(value) {
  if (value === null || value === undefined || value === "") return "-";
  return `${new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(toNumber(value))}%`;
}

function formatRatio(value) {
  if (value === null || value === undefined || value === "") return "-";
  return `${new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(toNumber(value))}x`;
}

function formatDateTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function compactText(value, maxLength = 80) {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  if (text.length <= maxLength) return text || "-";
  return `${text.slice(0, maxLength - 1)}…`;
}

function normalizeText(value) {
  return String(value || "").toLowerCase().trim();
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setText(id, value) {
  const node = document.getElementById(id);
  if (node) node.textContent = value;
}
