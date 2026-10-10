"""Advisory prompt checks: findings are review leads, never efficacy/language proof.

This module does not mutate model-authored prompts. It deliberately checks only
visible-copy fields for scripts: technical image instructions may be Chinese.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any


LIMITATIONS = [
    "规则检查只能发现明确的文字、重复和绑定信号，不能证明当地语言自然或卖点真实。",
    "画面、促销可有强烈 COD 表现；涉及功效、认证、专家和数值的真实性仍须依据资料人工核实。",
]
_CJK = re.compile(r"[\u3400-\u9fff]")
_KANA = re.compile(r"[\u3040-\u30ff\uff66-\uff9f]")
_HANGUL = re.compile(r"[\u1100-\u11ff\uac00-\ud7af]")
_LATIN = re.compile(r"[A-Za-zÀ-ž]")
_CHINESE_HINT = re.compile(r"让你|无需|轻松|购买|你的|为您|告别|这款|专为|卖点|选购|货到")
_JP_MIXED_CHINESE = re.compile(r"整只|锁鲜|即食|空气炸锅|肉质|饱满|烧烤|独立包装|香辣")
_NUMBERING = re.compile(r"(?:第\s*\d+\s*[页張张]|(?<![A-Za-z])page\s*#?\s*\d+(?:\s*/\s*\d+)?(?!\d)|(?:主图|详情图|页面)\s*\d+)", re.I)
_QUANTITIES = {
    "屏幕英寸": re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)\s*(?:英寸|インチ|inches?(?![A-Za-z]))", re.I),
    "电池容量mAh": re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)\s*mAh\b", re.I),
}
_IDENTITY = re.compile(r"(?:当前唯一商品|商品名称|商品名|product\s*name)\s*[:：]\s*([^。\n；;]+)", re.I)
_REFERENCE = re.compile(r"(?:\bimage|参考图|参照画像)\s*#?\s*(\d+)", re.I)


def _normalized(text: Any, page_numbers: bool = False) -> str:
    value = str(text or "").casefold()
    if page_numbers:
        value = _NUMBERING.sub("[page]", value)
    return re.sub(r"[\s\W_]+", "", value)


def input_fingerprint(form: dict[str, Any], master: str, outline: list, pages: list, hooks: list,
                      references: list | None = None) -> str:
    """Bind a review to the exact saved content, not just a product's name."""
    prompt_form = {key: value for key, value in form.items() if key not in {"model", "quality", "generationProfile"}}
    payload = {"form": prompt_form, "master": master, "outline": outline, "pages": pages, "hooks": hooks,
               "references": references or []}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _script_warning(text: Any, market: str, product: str) -> str:
    value = str(text or "").strip()
    # A product/model name is not expected to be translated as a language test.
    value = value.replace(product, "") if product else value
    if len(value) < 4:
        return ""
    cjk, kana, hangul, latin = (len(pattern.findall(value)) for pattern in (_CJK, _KANA, _HANGUL, _LATIN))
    letters = cjk + kana + hangul + latin
    if market == "JP":
        if _JP_MIXED_CHINESE.search(value):
            return "日文可见文案夹杂中文商品/营销词，请按原意改写为自然日语。"
        if hangul >= 3:
            return "日文可见文案中出现较多韩文字母，请确认目标语言。"
        if not kana and (_CHINESE_HINT.search(value) or (latin >= 16 and latin > letters * .75)):
            return "此段可见文案可能仍是中文或英文，请核对是否需要自然日文改写。"
        # All-kanji Japanese titles (e.g. 商品情報 / 毎日健康管理) are valid.
    elif market == "KR":
        if not hangul and (cjk + kana >= 4 or latin >= 16):
            return "韩文可见文案没有韩文字母，可能尚未本土化；型号和专有名词可保留。"
    elif market in {"US", "DE"} and cjk + kana + hangul >= 4:
        return "英文/德文可见文案仍含较多中日韩文字，请核对是否为刻意保留的品牌名称。"
    return ""


def finalize_report(issues: list[dict[str, Any]], *, source: str = "rules", total: int = 0,
                    checked: int = 0, fingerprint: str = "", coverage: dict | None = None) -> dict[str, Any]:
    unique = {}
    for issue in issues:
        key = (issue.get("page", 0), issue.get("code"), issue.get("field"), issue.get("sourcePointIndex"), issue.get("message"))
        unique[key] = issue
    issues = sorted(unique.values(), key=lambda item: (item.get("page", 0), item.get("sourcePointIndex", 0), item.get("code", "")))
    pages = sorted({issue["page"] for issue in issues if issue.get("page", 0) > 0 and issue.get("severity") != "info"})
    hook_sources = sorted({issue["sourcePointIndex"] for issue in issues
                           if issue.get("field") == "hooks" and issue.get("sourcePointIndex") and issue.get("severity") != "info"})
    global_findings = any(issue.get("page", 0) == 0 and issue.get("field") != "hooks" and issue.get("severity") != "info" for issue in issues)
    warning_count = sum(issue.get("severity") != "info" for issue in issues)
    return {
        "status": "warning" if warning_count else "checked", "source": source, "advisory": True,
        "summary": f"已检查 {checked}/{total} 页，发现 {warning_count} 项待核对问题。" if warning_count
                   else f"已检查 {checked}/{total} 页，暂未发现本次检查可识别的问题；不代表语言或事实已获保证。",
        "issues": issues, "issueCount": len(issues), "warningCount": warning_count,
        "checkedPages": checked, "expectedPages": total, "inputFingerprint": fingerprint,
        "repairablePages": pages, "repairableHookSources": hook_sources,
        "requiresFullRegeneration": global_findings, "limitations": list(LIMITATIONS), "coverage": coverage or {},
    }


def assess(form: dict[str, Any], master: str, outline: list[dict[str, Any]],
           pages: list[dict[str, Any]], hooks: list[dict[str, Any]],
           references: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Return specific, deterministic warnings without declaring a suite blocked."""
    issues: list[dict[str, Any]] = []
    total = int(form.get("main", 0)) + int(form.get("detail", 0))
    points = form.get("points", [])
    product = str(form.get("product", ""))
    market = str(form.get("market", ""))

    def add(page: int, code: str, message: str, field: str, **extra: Any) -> None:
        issues.append({"page": page, "code": code, "severity": "warning", "message": message, "field": field, **extra})

    if not master:
        add(0, "missing_master", "尚未生成总控提示词，请先继续或重新生成。", "masterPrompt")
    by_number = {item.get("page"): item for item in pages}
    for number in range(1, total + 1):
        if number not in by_number:
            add(number, "missing_page", "此页尚未生成，可继续生成补齐。", "modelPrompt")

    covered: set[int] = set()
    for entry in outline:
        page_number = entry.get("page", 0)
        for index in entry.get("sourcePointIndexes", []):
            if isinstance(index, int) and not isinstance(index, bool) and 1 <= index <= len(points):
                covered.add(index)
            else:
                add(page_number, "source_binding", "此页绑定了不存在的原始卖点编号，请核对页面来源。", "outline")
    missing_sources = sorted(set(range(1, len(points) + 1)) - covered)
    if missing_sources:
        add(0, "source_coverage", "页面大纲未覆盖原始卖点编号：" + "、".join(map(str, missing_sources)), "coverage")

    seen_prompts: dict[str, int] = {}
    seen_layouts: dict[str, list[int]] = {}
    for page in pages:
        number = int(page.get("page", 0))
        prompt = str(page.get("modelPrompt") or "")
        warning = _script_warning(page.get("headline"), market, product)
        if warning:
            add(number, "visible_language", warning, "headline")
        for label in page.get("copyLabels", []):
            warning = _script_warning(label, market, product)
            if warning:
                add(number, "visible_language", warning + f" 标签：{label}", "modelPrompt")
        normalized = _normalized(prompt, page_numbers=True)
        if len(normalized) >= 30:
            if normalized in seen_prompts:
                add(number, "repeated_prompt", f"与第 {seen_prompts[normalized]} 页提示词除页码/标点外相同，请改变本页的画面和销售任务。", "modelPrompt")
            else:
                seen_prompts[normalized] = number
        layout = _normalized(page.get("composition"), page_numbers=True)
        if len(layout) >= 16:
            seen_layouts.setdefault(layout, []).append(number)
        for identity in _IDENTITY.findall(prompt):
            if _normalized(identity) != _normalized(product) and product not in identity:
                add(number, "product_identity", f"提示词将商品名称标为“{identity[:100]}”，与当前商品不一致，请核对串品。", "modelPrompt")
        source_text = " ".join(str(point) for point in points) + " " + product
        for label, pattern in _QUANTITIES.items():
            source_values = set(pattern.findall(source_text))
            page_values = set(pattern.findall(prompt))
            if source_values and page_values and not page_values.issubset(source_values):
                add(number, "quantity_mismatch", f"{label}出现输入未提供的值 {', '.join(sorted(page_values - source_values))}；原始值为 {', '.join(sorted(source_values))}。若为对比示意请明确标注。", "modelPrompt")
        if references is not None:
            invalid_refs = sorted({int(index) for index in _REFERENCE.findall(prompt) if not 1 <= int(index) <= len(references)})
            if invalid_refs:
                add(number, "reference_binding", "提到了不存在的参考图编号：" + "、".join(map(str, invalid_refs)), "references")
    for numbers in seen_layouts.values():
        if len(numbers) >= 3:
            for number in numbers[1:]:
                add(number, "repeated_layout", f"第 {','.join(map(str, numbers))} 页使用完全相同的详细构图描述，请核对是否需要版式变化。", "modelPrompt")

    for identity in _IDENTITY.findall(master):
        if _normalized(identity) != _normalized(product) and product not in identity:
            add(0, "product_identity", f"总控标注商品名称“{identity[:100]}”，与当前商品不一致；需重新生成总控。", "masterPrompt")
    seen_hooks: dict[str, tuple[int, str]] = {}
    hook_covered = set()
    for hook in hooks:
        source = hook.get("source")
        if source not in points:
            add(0, "hook_source", "钩子来源不属于当前输入卖点，请重新生成钩子。", "hooks")
            continue
        source_index = points.index(source) + 1
        hook_covered.add(source)
        for variant in hook.get("variants", []):
            field_text, kind = variant.get("text", ""), str(variant.get("type", ""))
            warning = _script_warning(field_text, market, product)
            if warning:
                add(0, "visible_language", warning, "hooks", sourcePointIndex=source_index, hookType=kind)
            normalized = _normalized(field_text)
            if normalized and normalized in seen_hooks:
                prior_source, prior_type = seen_hooks[normalized]
                add(0, "identical_hook", f"此钩子与卖点 {prior_source} 的 {prior_type} 文案相同，三种角度应有不同表达。", "hooks", sourcePointIndex=source_index, hookType=kind)
            elif normalized:
                seen_hooks[normalized] = (source_index, kind)
    for index, source in enumerate(points, start=1):
        if source not in hook_covered and points.index(source) + 1 == index:
            add(0, "missing_hook", "此条原始卖点尚缺本土化钩子。", "hooks", sourcePointIndex=index)
    return finalize_report(issues, total=total, checked=len(by_number),
                           fingerprint=input_fingerprint(form, master, outline, pages, hooks, references),
                           coverage={"sourcePointCount": len(points), "coveredSourcePointIndexes": sorted(covered),
                                     "missingSourcePointIndexes": missing_sources,
                                     "referenceCount": len(references) if references is not None else None})


def normalize_ai_issues(raw: Any, *, allowed_pages: set[int], allowed_hook_sources: set[int],
                        global_allowed: bool) -> list[dict[str, Any]]:
    """Only accept scoped, actionable findings with a quote from reviewed text."""
    if not isinstance(raw, dict) or not isinstance(raw.get("issues"), list) or len(raw["issues"]) > 50:
        raise ValueError("AI 质检未返回有效 issues 数组（每批最多50项），已保存规则检查结果。")
    issues = []
    fields = {"masterPrompt", "outline", "headline", "modelPrompt", "hooks", "coverage", "references"}
    codes = {"ai_language", "ai_repetition", "ai_source_mismatch", "ai_claim_evidence", "ai_layout", "ai_reference"}
    for item in raw["issues"]:
        if not isinstance(item, dict):
            raise ValueError("AI 质检问题格式无效。")
        number = item.get("page")
        if isinstance(number, bool) or not isinstance(number, int) or number < 0:
            raise ValueError("AI 质检返回无效页码。")
        field, code = item.get("field"), item.get("code")
        if field not in fields or code not in codes:
            raise ValueError("AI 质检返回未知字段或问题类型。")
        if number and number not in allowed_pages:
            raise ValueError("AI 质检返回了本批次以外的页面问题。")
        if not number and field != "hooks" and not global_allowed:
            raise ValueError("AI 质检返回了本批次以外的总控问题。")
        if number and field in {"masterPrompt", "hooks", "coverage"}:
            raise ValueError("AI 质检的页面编号与字段范围不一致。")
        if not number and field in {"headline", "modelPrompt"}:
            raise ValueError("AI 质检的逐页问题必须指定对应页码。")
        message, evidence = item.get("message"), item.get("evidence")
        if not isinstance(message, str) or not message.strip() or len(message) > 1000:
            raise ValueError("AI 质检缺少可执行的问题说明。")
        if not isinstance(evidence, str) or not evidence.strip() or len(evidence) > 700:
            raise ValueError("AI 质检必须引用对应提示词中的证据，不能凭空断言。")
        normalized = {"page": number, "code": code, "field": field,
                      "severity": "info" if item.get("severity") == "info" else "warning",
                      "message": message.strip(), "evidence": evidence.strip()}
        if field == "hooks":
            source_index = item.get("sourcePointIndex")
            if number or isinstance(source_index, bool) or source_index not in allowed_hook_sources:
                raise ValueError("AI 质检钩子未绑定本批次的原始卖点。")
            normalized["sourcePointIndex"] = source_index
        issues.append(normalized)
    return issues
