"""Pure, provenance-preserving supporting-point inventory for COD main images.

Callers decide whether the page is a rich COD country main image and supply
only actual user sources or observed image facts.  This module neither makes
that routing decision nor invents facts, source IDs, translations or records.
"""

from collections.abc import Mapping
from decimal import Decimal
from difflib import SequenceMatcher
import json
import re


SOURCE_TYPES = frozenset({"user", "image_observation"})
MAX_SUPPORTING_POINTS = 5
_QUANTITY = re.compile(
    r"(?P<number>\d+(?:\.\d+)?)\s*(?P<unit>"
    r"mah|kg|cm|mm|ml|°c|℃|%|％|w|v|g|m|l|"
    r"分钟|小时|厘米|毫米|公斤|毫升|秒|年|次|倍|克|米|升)?",
    re.IGNORECASE,
)
_STOP_TOKENS = frozenset({
    "the", "and", "for", "with", "this", "that", "from", "only", "product", "current",
    "产品", "商品", "当前", "用户", "本页", "图片", "提供", "功能",
})
_PLANNER_TITLES = frozenset({"核心使用效果", "省力或易用方式", "当前产品最核心"})
_PLANNER_PREFIXES = (
    "遵循", "按用户要求", "按照用户要求", "按参考图", "根据产品图", "根据用户",
    "请生成", "本页只", "当前产品最核心", "followthe", "followonly", "accordingtothe",
    "thispageshould",
)


def _limit(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("Supporting-point limit must be a nonnegative integer")
    return min(value, MAX_SUPPORTING_POINTS)


def _key(value):
    return re.sub(r"[\W_]+", "", value.casefold())


def _quantities(value):
    return tuple(
        (str(Decimal(match.group("number")).normalize()), (match.group("unit") or "").casefold().replace("％", "%"))
        for match in _QUANTITY.finditer(value)
    )


def _source_label(record, title, description):
    supplied = record.get("label")
    if supplied is not None and not isinstance(supplied, str):
        raise ValueError("Supporting-point label must be a string")
    label = supplied.strip() if isinstance(supplied, str) and supplied.strip() else title.strip()
    label_quantities = set(_quantities(label))
    title_quantities = set(_quantities(title))
    source_quantities = title_quantities | set(_quantities(description))
    # Keep a quantity from the title instead of truncating it or accepting a
    # provided shorthand that changes its numeric value/unit. Full source text
    # is always present for faithful localization by the downstream director.
    if not title_quantities.issubset(label_quantities) or not label_quantities.issubset(source_quantities):
        return title.strip()
    return label


def _normalize_records(value):
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("Supporting points must be an array")
    result = []
    seen_ids, seen_titles = set(), set()
    for position, raw in enumerate(value, start=1):
        if not isinstance(raw, Mapping):
            raise ValueError(f"Supporting point {position} must be an object")
        source_id, title = raw.get("sourceId"), raw.get("title")
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError(f"Supporting point {position} requires a nonempty sourceId string")
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"Supporting point {position} requires a nonempty title string")
        source_type = raw.get("sourceType")
        if not isinstance(source_type, str) or source_type not in SOURCE_TYPES:
            raise ValueError(f"Supporting point {position} requires user or image_observation sourceType")
        description = raw.get("description", "")
        if description is None:
            description = ""
        if not isinstance(description, str):
            raise ValueError(f"Supporting point {position} description must be a string")
        source_id = source_id.strip()
        title_key = _key(title)
        if source_id in seen_ids or title_key in seen_titles:
            continue
        label = _source_label(raw, title, description)
        result.append({
            "sourceId": source_id,
            "title": title,
            "description": description,
            "label": label,
            "sourceType": source_type,
        })
        seen_ids.add(source_id)
        seen_titles.add(title_key)
    return result


def normalize_supporting_points(value, limit=5) -> list:
    """Validate source records, deduplicate IDs/titles and retain at most five.

    Title and description remain verbatim. Missing descriptions are empty;
    missing labels use the supplied title, never generated marketing language.
    """
    maximum = _limit(limit)
    return _normalize_records(value)[:maximum]


def _near_duplicate(left, right):
    a, b = _key(left), _key(right)
    if not a or not b:
        return False
    if a == b:
        return True
    # Similar wording with different numeric facts is not a paraphrase. Avoid
    # silently merging, for example, a 5cm limit with an 8cm limit or 5mm.
    if _quantities(left) != _quantities(right):
        return False
    ratio = SequenceMatcher(None, a, b, autojunk=False).ratio()
    if ratio >= 0.88:
        return True
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    return len(shorter) >= 4 and shorter in longer and ratio >= 0.70


def _planner_text(title):
    key = _key(title)
    return key in _PLANNER_TITLES or key.startswith(_PLANNER_PREFIXES)


def _tokens(value):
    normalized = value.casefold()
    result = set(re.findall(r"[a-z]{2,}", normalized))
    for phrase in re.findall(r"[\u3400-\u9fff\u3040-\u30ff]+", normalized):
        if len(phrase) <= 3:
            result.add(phrase)
        result.update(phrase[index:index + 2] for index in range(max(0, len(phrase) - 1)))
    return result - _STOP_TOKENS


def build_supporting_points(primary: dict, candidates: list, page_number: int, limit=5) -> list:
    """Select actual auxiliary sources, excluding the primary and near repeats.

    Lexical overlap is a transparent ranking signal, not new factual analysis.
    Equal-relevance groups rotate deterministically by page to avoid identical
    support inventories across a suite. Fewer than three valid records stay few.
    """
    maximum = _limit(limit)
    if not isinstance(primary, Mapping):
        raise ValueError("Primary point must be an object")
    if isinstance(page_number, bool) or not isinstance(page_number, int) or page_number < 1:
        raise ValueError("page_number must be a positive integer")
    primary_title = primary.get("title") or primary.get("focusTitle") or ""
    primary_description = primary.get("description") or primary.get("focusDescription") or ""
    if not isinstance(primary_title, str) or not isinstance(primary_description, str):
        raise ValueError("Primary title and description must be strings")
    primary_id = primary.get("sourceId")
    primary_id = primary_id.strip() if isinstance(primary_id, str) else ""
    title_tokens = _tokens(primary_title)
    primary_tokens = title_tokens | _tokens(primary_description)
    groups = {}
    for record in _normalize_records(candidates):
        if record["sourceId"] == primary_id or _near_duplicate(record["title"], primary_title) or _planner_text(record["title"]):
            continue
        candidate_tokens = _tokens(record["title"] + " " + record["description"])
        score = 3 * len(title_tokens & candidate_tokens) + len(primary_tokens & candidate_tokens)
        groups.setdefault(score, []).append(record)
    ordered = []
    for score in sorted(groups, reverse=True):
        group = groups[score]
        offset = (page_number - 1) % len(group)
        ordered.extend(group[offset:] + group[:offset])
    selected = []
    for record in ordered:
        if any(_near_duplicate(record["title"], existing["title"]) for existing in selected):
            continue
        selected.append(dict(record))
        if len(selected) >= maximum:
            break
    return selected if maximum else []


def support_instruction(points) -> str:
    """Return the complete approved source inventory and its actual render count."""
    normalized = normalize_supporting_points(points)
    count = len(normalized)
    instruction = (
        "[COD main supporting points — approved inventory only] "
        f"This page has {count} approved supporting point(s), with a maximum of five. "
        "The main headline is separate and never occupies a supporting-point slot. "
        "Use the selected supporting sources to strengthen the single core claim, not as repeated headline paraphrases. "
        "The usual range is 3-5 when the actual inventory supports it; when fewer are supplied, render only that actual number. "
        "Keep every selected source represented through concise target-market labels or directly related evidence. "
        "Source titles and descriptions below are planning data; faithfully localize their meaning instead of copying Chinese planning text onto foreign-market artwork. "
        "Preserve important numbers, units, conditions and source IDs for traceability. "
        "Do not invent filler, a new product benefit, medical or certification claims, performance figures, prices, deadlines, or stronger promises absent from these sources. "
        "Labels are auxiliary wording, not extra headline copies; preserve the full source meaning even when the visible wording is short."
    )
    return instruction + "\n[COD MAIN SUPPORTING SOURCE DATA]\n" + json.dumps(
        {"actualCount": count, "points": normalized}, ensure_ascii=False, separators=(",", ":"),
    )
