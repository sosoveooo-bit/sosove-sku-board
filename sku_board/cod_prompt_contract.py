"""Pure contracts for Atelier; never re-plan a model-authored page at render time."""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any


MARKETS = {"JP": ("日本", "日文"), "KR": ("韩国", "韩文"), "US": ("美国", "英文"), "DE": ("德国", "德文")}
ROLES = {"auto", "product", "detail", "usage", "person", "layout", "scene", "package", "other"}
MAX_PROMPT = 16000


def _text(value: Any, label: str, limit: int = 1200, required: bool = False) -> str:
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise ValueError(f"{label}必须是文字")
    result = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    if "\x00" in result or len(result) > limit:
        raise ValueError(f"{label}过长或包含无效字符（最多{limit}字）")
    if required and not result:
        raise ValueError(f"请填写{label}")
    return result


def _integer(value: Any, label: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not re.fullmatch(r"\d+", str(value)):
        raise ValueError(f"{label}须为{minimum}至{maximum}的整数")
    number = int(value)
    if not minimum <= number <= maximum:
        raise ValueError(f"{label}须为{minimum}至{maximum}的整数")
    return number


def _boolean(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    return value if isinstance(value, bool) else str(value).lower() in {"1", "true", "yes", "on"}


def normalize_form(raw: Any) -> dict[str, Any]:
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (ValueError, TypeError) as exc:
            raise ValueError("商品资料JSON无法解析") from exc
    if not isinstance(raw, dict):
        raise ValueError("缺少商品资料")
    points = raw.get("points", raw.get("sellingPoints", []))
    if isinstance(points, str):
        points = [part.strip() for part in re.split(r"[\r\n]+", points) if part.strip()]
    if not isinstance(points, list) or not 1 <= len(points) <= 60:
        raise ValueError("请填写1至60条真实商品卖点，每行一条")
    market = str(raw.get("market", "JP")).upper()
    if market not in MARKETS:
        raise ValueError("请选择支持的目标国家")
    size = str(raw.get("size", "750x1000")).lower().replace("×", "x").replace(" ", "")
    match = re.fullmatch(r"(\d{3,4})x(\d{3,4})", size)
    if not match or any(not 256 <= int(n) <= 4096 for n in match.groups()):
        raise ValueError("画布格式须为宽x高，两个边长均为256至4096，例如750x1000")
    intensity = str(raw.get("intensity", "cod"))
    if intensity not in {"cod", "bold", "premium"}:
        raise ValueError("视觉强度无效")
    promos = raw.get("promotions") if isinstance(raw.get("promotions"), dict) else {}
    return {
        "product": _text(raw.get("product"), "当前商品名称", 320, True),
        "market": market, "intensity": intensity,
        "main": _integer(raw.get("main", 15), "主图数量", 1, 30),
        "detail": _integer(raw.get("detail", 22), "详情数量", 1, 40),
        "size": size,
        "points": [_text(point, f"第{i+1}条卖点", 2000, True) for i, point in enumerate(points)],
        "reference": _text(raw.get("reference", raw.get("referenceMap", "")), "参考图说明", 2400),
        "style": _text(raw.get("style", ""), "视觉要求", 2400),
        "avoid": _text(raw.get("avoid", ""), "限制要求", 1600),
        "allowPromo": _boolean(raw.get("allowPromo")),
        "allowMedical": _boolean(raw.get("allowMedical")),
        **{key: _text(raw.get(key, promos.get(key, "")), key, 320) for key in ("discount", "salePrice", "codText", "deadline")},
        "model": _text(raw.get("model", "gpt-image-2"), "生图模型", 120),
        "quality": str(raw.get("quality", "high")) if raw.get("quality", "high") in {"auto", "low", "medium", "high"} else "high",
        "generationProfile": str(raw.get("generationProfile", "standard")) if raw.get("generationProfile", "standard") in {"fast", "standard", "quality"} else "standard",
    }


def content_form(form: dict[str, Any]) -> dict[str, Any]:
    """Changing image delivery settings never invalidates a prompt version."""
    return {key: value for key, value in normalize_form(form).items() if key not in {"model", "quality", "generationProfile"}}


def fingerprint(form: dict[str, Any], references: list[dict[str, Any]]) -> str:
    identities = []
    for index, ref in enumerate(references, 1):
        digest = str(ref.get("sha256", ""))
        if not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("参考图缺少有效内容指纹，请重新上传")
        role = str(ref.get("role", "auto"))
        if role not in ROLES:
            raise ValueError("参考图角色无效")
        identities.append({"index": index, "sha256": digest, "role": role})
    canonical = json.dumps({"version": 1, "form": content_form(form), "references": identities}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def canonical_archetype(value: str) -> str:
    if re.search(r"四宫格|pain[-_ ]?grid|2\s*[×x]\s*2", value, re.I):
        return "pain-grid"
    if re.search(r"产品信息|商品信息|product[-_ ]?info|specification", value, re.I):
        return "product-info"
    if re.search(r"对比|comparison|before[-_ ]?after", value, re.I):
        return "comparison"
    return value


def validate_hooks(raw: Any, form: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(raw, list) or not raw:
        raise ValueError("AI没有返回当前商品的本土化钩子")
    hooks = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError("AI钩子格式无效")
        source = _text(item.get("source", item.get("sourcePoint", "")), "钩子来源卖点", 2000, True)
        # The index is an explicit reference to the input, never inferred by
        # approximate text matching across different products.
        source_index = item.get("sourcePointIndex")
        if source_index is not None:
            source = form["points"][_integer(source_index, "钩子来源编号", 1, len(form["points"])) - 1]
        elif source not in form["points"]:
            raise ValueError("AI钩子未绑定输入中的原始卖点")
        variants = item.get("variants", [])
        if not isinstance(variants, list):
            raise ValueError("AI钩子缺少类型列表")
        normalized = []
        for variant in variants:
            if not isinstance(variant, dict) or variant.get("type") not in {"pain", "effect", "scene"}:
                raise ValueError("AI钩子须区分痛点、效果和场景类型")
            normalized.append({"type": variant["type"], "text": _text(variant.get("text"), "当地语言钩子", 240, True)})
        if {v["type"] for v in normalized} != {"pain", "effect", "scene"} or len(normalized) != 3:
            raise ValueError("每条卖点须有痛点、效果和场景三个钩子")
        hooks.append({"source": source, "variants": normalized})
    if len({item["source"] for item in hooks}) != len(hooks):
        raise ValueError("AI钩子重复绑定同一卖点")
    return hooks


def normalize_outline(raw: Any, form: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("AI策划结果须为JSON对象")
    master = _text(raw.get("masterPrompt"), "AI总控Prompt", 8000, True)
    pages = raw.get("outline")
    total = form["main"] + form["detail"]
    if not isinstance(pages, list) or len(pages) != total:
        raise ValueError(f"AI主题列表须完整返回{total}页")
    normalized = {}
    for item in pages:
        if not isinstance(item, dict):
            raise ValueError("AI页面主题格式无效")
        page = _integer(item.get("page"), "页码", 1, total)
        if page in normalized:
            raise ValueError("AI主题列表出现重复页码")
        section = "main" if page <= form["main"] else "detail"
        title = _text(item.get("title"), "页面标题", 260, True)
        focus = _text(item.get("focus", item.get("objective", "")), "页面卖点", 1400, True)
        normalized[page] = {
            "page": page, "section": section,
            "localIndex": page if section == "main" else page - form["main"],
            "title": title, "focus": focus,
            "objective": _text(item.get("objective", focus), "页面目标", 1400, True),
            "headline": _text(item.get("headline", ""), "当地语言标题", 240),
            "archetype": canonical_archetype(_text(item.get("archetype", item.get("pageArchetype", title)), "页面类型", 240, True)),
            "sourcePointIndexes": [_integer(i, "卖点编号", 1, len(form["points"])) for i in item.get("sourcePointIndexes", [])] if isinstance(item.get("sourcePointIndexes", []), list) else [],
        }
    result_pages = [normalized[i] for i in range(1, total + 1)]
    coverage = {i for page in result_pages for i in page["sourcePointIndexes"]}
    missing = sorted(set(range(1, len(form["points"]) + 1)) - coverage)
    if missing:
        raise ValueError("AI主题列表遗漏原始卖点：" + "、".join(str(i) for i in missing))
    if form["main"] >= 2 and not any(p["archetype"] == "pain-grid" for p in result_pages[:form["main"]]):
        raise ValueError("AI主题列表缺少主图四宫格痛点页")
    if total >= 4 and not any(p["archetype"] == "comparison" for p in result_pages):
        raise ValueError("AI主题列表缺少公平对比页")
    if result_pages[-1]["archetype"] != "product-info":
        raise ValueError("AI最后一页须为当前产品信息")
    return {
        "masterPrompt": master, "outline": result_pages,
        "hooks": validate_hooks(raw.get("hooks"), form),
        "productSummary": _text(raw.get("productSummary", form["product"]), "产品总结", 1800),
        "visualDNA": raw.get("visualDNA", {}) if isinstance(raw.get("visualDNA", {}), (dict, str)) else {},
    }


def normalize_page(raw: Any, outline_entry: dict[str, Any], form: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict) or raw.get("page") != outline_entry["page"]:
        raise ValueError("AI逐页响应与当前请求页码不一致")
    prompt = _text(raw.get("modelPrompt"), "逐页Prompt", 5000, True)
    if len(prompt) < 40:
        raise ValueError("AI逐页Prompt过短，缺少可执行的画面信息")
    result = {**outline_entry, "modelPrompt": prompt}
    for key in ("headline", "evidence", "scene", "pose", "composition", "visualTreatment", "impactTreatment"):
        if key in raw:
            result[key] = _text(raw[key], key, 1400 if key != "headline" else 240)
    return result


def shared_execution_requirements(form: dict[str, Any], references: list[dict[str, Any]]) -> str:
    """Shared delivery rules, included once in compact whole-suite exports."""
    reference_map = "; ".join(f"Image {i}={ref.get('role', 'auto')}" for i, ref in enumerate(references, 1))
    offer = {key: form.get(key, "") for key in ("discount", "salePrice", "codText", "deadline") if form.get(key)}
    offer_rule = (
        "允许使用以下用户提供的促销字段，不增加其他优惠条件：" + json.dumps(offer, ensure_ascii=False)
        if form.get("allowPromo", True) and offer
        else "未提供优惠数据，不编造价格、折扣、期限或配送承诺；可用静态CTA和产品价值做转化。"
        if form.get("allowPromo", True)
        else "本次关闭促销组件；不显示促销价格、折扣、货到付款徽标或限时优惠。"
    )
    identity = (
        "仅product/detail/usage/package参考图确认商品结构与用法；person仅锁定所指定人物；layout/scene仅参考构图风格，不能转移其中的商品、身份、文字或标志。"
        if references else "本次没有商品参考图，产品外观细节待实际参考图确认；不编造不可见结构。"
    )
    lines = [
        "[Delivery requirements]",
        f"当前唯一商品：{form['product']}。画布严格为{form['size']}，设计铺满四边，保留可读安全边距，不留下未完成的空白区域。",
        f"目标市场：{MARKETS[form['market']][0]}；可见文案只使用自然{MARKETS[form['market']][1]}。只表现本页指定主题，保留总控的统一配色和当前页构图。",
        "[User art direction] " + form["style"] if form.get("style") else "配色与镜头遵循本次AI总控和当前商品，保持整套视觉一致。",
        f"参考图编号与角色：{reference_map or '无'}。{identity}",
        offer_rule,
        "保留可证实的商品事实与用户的视觉创意；用户提供的宣传说法不等于验证证明。不编造医生推荐、机构认证、实验数据、诊疗承诺、评论或功能。需要证据的主张未核实前不得伪装为已验证事实。",
        "健康相关内容仅作有依据的日常信息表达，不能作为诊断、治疗、用药依据或医疗保障。" if form.get("allowMedical", True) and re.search(r"健康|血糖|血氧|心率|医疗|治[疗癒]|health|medical", form["product"] + " ".join(form["points"]), re.I) else "" if form.get("allowMedical", True) else "本次不使用健康、医疗诊断或治疗类宣传内容。",
        "[User exclusions] " + form["avoid"] if form.get("avoid") else "不混用SKU，不重设计商品，不添加乱码、水印或平台背书。",
    ]
    return "\n".join(line for line in lines if line)


def compile_execution_prompt(form: dict[str, Any], master: str, page: dict[str, Any], references: list[dict[str, Any]]) -> str:
    """Canonical single-page export/provider text with AI creative preserved."""
    master = _text(master, "总控Prompt", 8000, True)
    local = _text(page.get("modelPrompt"), "逐页Prompt", 5000, True)
    page_number = _integer(page.get("page"), "页码", 1, form["main"] + form["detail"])
    result = "\n".join([
        f"[Atelier page {page_number}/{form['main'] + form['detail']}] 直接生成这一页的一张完整静态电商图，不生成整套缩略图、动画、视频或网页截图。",
        "[AI suite master — preserved verbatim]", master,
        "[AI current page — preserved verbatim]", local,
        shared_execution_requirements(form, references),
    ])
    if len(result) > MAX_PROMPT:
        raise ValueError("执行Prompt超过长度限制，请缩短当前页内容后重试")
    return result
