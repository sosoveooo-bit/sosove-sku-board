"""Pure source parsers for COD promotion and customer-review content.

The caller supplies the brief; this module performs no I/O and creates no
marketing facts. A missing, disabled, invalid or ambiguous offer is ``{}``.
Review values are user-supplied text, not independently authenticated reviews.
"""

from decimal import Decimal, InvalidOperation
import re


_ASCII_WIDTH = {code: chr(code - 0xFEE0) for code in range(0xFF01, 0xFF5F)}
_ASCII_WIDTH[0x3000] = " "
_PROMOTION_DISABLED = re.compile(
    r"(?:不要|不需要|无需|无须|禁止|不得|取消|去掉|没有|无|不)\s*"
    r"(?:出现|显示|展示|添加|使用|制作|呈现|做)?\s*"
    r"(?:任何|所有|额外|相关的)?\s*(?:促销|折扣|优惠(?!券)|打折)"
    r"|(?:促销|折扣|优惠)\s*[:：]?\s*(?:禁用|取消|关闭|不显示|不展示|无|不要)"
    r"|\b(?:no|without|disable|remove|omit)\s+(?:(?:any|the)\s+)?(?:discounts?|promotions?|sales?)\b"
    r"|\b(?:do\s+not|don['’]t|never)\s+(?:show|add|include|display|use|create)\s+"
    r"(?:(?:any|the)\s+)?(?:discounts?|promotions?|sales?)\b"
    r"|(?:割引|セール)\s*(?:なし|は不要|を表示しない)"
    r"|할인\s*(?:표시\s*)?(?:없음|없이|하지\s*마(?:세요)?)",
    re.IGNORECASE,
)
_PERCENT = re.compile(r"(?<![0-9.,])(?P<value>[+-]?[0-9]+(?:[.,][0-9]+)?)\s*%")
_PROMOTION_PREFIX = re.compile(
    r"(?:\bdiscount|\bsale|促销|折扣|优惠|セール|割引|할인)"
    r"(?:\s*(?:up\s+to|maximum|of|最多|最高|最大(?:で)?|高达|可达|达|为|是|比例|幅度|최대|[:：=]))*\s*$",
    re.IGNORECASE,
)
_PROMOTION_SUFFIX = re.compile(r"\s*(?:OFF(?![A-Za-z])|割引|引き|할인)", re.IGNORECASE)
_MAXIMUM_PREFIX = re.compile(
    r"(?:up\s+to|maximum|max\.?|最大(?:で)?|最高|最多|高达|최대)\s*"
    r"(?:(?:优惠|折扣|促销|discount|sale)\s*)?[:：=]?\s*$",
    re.IGNORECASE,
)
_EXAMPLE_PREFIX = re.compile(
    r"(?:例如|比如|示例|样例|参考|for\s+example|e\.g\.|example|sample)\s*"
    r"(?:(?:促销|折扣|优惠|discount|offer)\s*)?[:：]?\s*$",
    re.IGNORECASE,
)
_EXAMPLE_SUFFIX = re.compile(
    r"\s*(?:OFF\s*)?(?:仅为|只是|作为|是|for\s+an?\s+)?(?:示例|样例|example|sample)",
    re.IGNORECASE,
)
_ZHE = re.compile(
    r"(?<![0-9.第])(?P<value>[+-]?[0-9]+(?:\.[0-9]+)?|[零〇一二两三四五六七八九十点]{1,6})"
    r"\s*折(?![叠页角])"
)
_CHINESE_DIGITS = {character: str(index) for index, character in enumerate("零一二三四五六七八九")}
_CHINESE_DIGITS.update({"〇": "0", "两": "2"})


def _decimal(value: str) -> Decimal | None:
    try:
        result = Decimal(value.replace(",", "."))
    except (InvalidOperation, ValueError):
        return None
    return result if result.is_finite() else None


def _zhe_price_fraction(value: str) -> Decimal | None:
    """Return the tenths-of-price value: 八五/八点五/8.5 all mean 8.5."""
    if re.fullmatch(r"[+-]?[0-9]+(?:\.[0-9]+)?", value):
        return _decimal(value)
    if value == "十":
        return Decimal(10)
    if "十" in value or value.count("点") > 1:
        return None
    if "点" in value:
        integer, fraction = value.split("点", 1)
        if len(integer) != 1 or not fraction:
            return None
        digits = _CHINESE_DIGITS.get(integer)
        decimals = "".join(_CHINESE_DIGITS.get(character, "") for character in fraction)
        return _decimal(f"{digits}.{decimals}") if digits is not None and len(decimals) == len(fraction) else None
    if not 1 <= len(value) <= 3 or any(character not in _CHINESE_DIGITS for character in value):
        return None
    digits = "".join(_CHINESE_DIGITS[character] for character in value)
    return _decimal(digits if len(digits) == 1 else f"{digits[0]}.{digits[1:]}")


def _source_clause(brief: str, start: int, end: int) -> str:
    separators = "\r\n;；。!?！？"
    left = max((brief.rfind(separator, 0, start) for separator in separators), default=-1) + 1
    boundaries = [position for separator in separators if (position := brief.find(separator, end)) >= 0]
    right = min(boundaries) if boundaries else len(brief)
    return brief[left:right].strip()


def promotion_contract(brief: str) -> dict:
    """Extract one explicitly supplied percentage-off offer without defaults.

    Return ``percent`` (int/float), canonical ``percentText``, neutral ``label``,
    original ``sourceText``, ``sourceType`` and ``isMaximum``. The numeric value
    is percentage *off*, so 8折 becomes 20. Repeated equivalent offers are fine;
    conflicting percentages return an empty contract rather than choosing one.
    An instruction excluding prices does not disable a supplied discount.
    """
    if not isinstance(brief, str) or not brief.strip():
        return {}
    normalized = brief.translate(_ASCII_WIDTH)
    if _PROMOTION_DISABLED.search(normalized):
        return {}
    candidates = []
    for match in _PERCENT.finditer(normalized):
        before = normalized[max(0, match.start() - 80):match.start()]
        after = normalized[match.end():match.end() + 32]
        if not _PROMOTION_PREFIX.search(before) and not _PROMOTION_SUFFIX.match(after):
            continue
        if _EXAMPLE_PREFIX.search(before) or _EXAMPLE_SUFFIX.match(after):
            continue
        percent = _decimal(match.group("value"))
        if percent is not None and 0 < percent <= 100:
            candidates.append((match.start(), match.end(), percent, "percent_off"))
    for match in _ZHE.finditer(normalized):
        before = normalized[max(0, match.start() - 80):match.start()]
        after = normalized[match.end():match.end() + 32]
        if _EXAMPLE_PREFIX.search(before) or _EXAMPLE_SUFFIX.match(after):
            continue
        fraction = _zhe_price_fraction(match.group("value"))
        if fraction is not None and 0 <= fraction < 10:
            candidates.append((match.start(), match.end(), Decimal(100) - fraction * 10, "chinese_zhe"))
    if not candidates or len({item[2] for item in candidates}) != 1:
        return {}
    start, end, percent, source_type = min(candidates, key=lambda item: item[0])
    percent_text = format(percent, "f")
    if "." in percent_text:
        percent_text = percent_text.rstrip("0").rstrip(".")
    return {
        "percent": int(percent) if percent == percent.to_integral_value() else float(percent),
        "percentText": percent_text,
        "label": f"{percent_text}% OFF",
        "sourceText": _source_clause(brief, start, end),
        "sourceType": source_type,
        "isMaximum": bool(_MAXIMUM_PREFIX.search(normalized[max(0, start - 40):start])),
    }


_REVIEW_LABEL = (
    r"真实(?:用户|客户|买家)?(?:评价|评论)|实际(?:评价|评论)|"
    r"(?:用户|客户|顾客|买家)(?:评价|评论)|(?:评价|评论)原文|"
    r"(?:(?:real|actual|verified)\s+)?(?:(?:customer|user|buyer)\s+)?"
    r"(?:reviews?|testimonials?)(?:\s+(?:data|quotes?))?|"
    r"実際のレビュー|お客様の声|お客様レビュー|購入者レビュー|"
    r"(?:실제\s*)?(?:고객|구매자)\s*(?:후기|리뷰)"
)
_REVIEW_HEADING = re.compile(
    rf"^\s*(?:#{{1,6}}\s*)?(?:\*\*|__)?(?:【)?(?:{_REVIEW_LABEL})(?:】)?(?:\*\*|__)?"
    r"\s*(?:[（(]\s*\d+\s*(?:条|reviews?)?\s*[）)])?\s*(?:[:：]\s*(?P<body>.*))?$",
    re.IGNORECASE,
)
_REVIEW_ITEM = re.compile(
    r"^\s*(?:[-*•>]\s+|\d{1,3}\s*[.)、）:：]\s*|(?:评价|评论|Review)\s*\d+\s*[:：]\s*)",
    re.IGNORECASE,
)
_REVIEW_REQUEST = re.compile(
    r"^(?:请|帮我|需要|添加|生成|编写|写|做|create\b|generate\b|write\b|add\b|make\b)"
    r".{0,80}(?:好评|评价|评论|反馈|体验卡|reviews?|testimonials?|feedback)",
    re.IGNORECASE,
)
_REVIEW_ABSENT = re.compile(
    r"^(?:暂无(?:资料|评价|评论)?|未提供(?:真实)?(?:评价|评论|资料)?|待补充|待提供|待采集"
    r"|没有(?:真实)?(?:用户)?(?:评价|评论)(?:数据|资料)?|无(?:资料|评价|评论)?"
    r"|none|n/?a|not\s+available|no\s+reviews?(?:\s+yet)?)"
    r"(?:\s*[,，;；:：-]\s*(?:稍后(?:提供|补充)|待(?:补充|提供|采集)|pending|to\s+be\s+provided))?\s*[。.!！]?$",
    re.IGNORECASE,
)
_REVIEW_COUNT_ONLY = re.compile(
    r"^(?:\d+\s*条\s*(?:好评|评价|评论)|\d+\s+(?:positive\s+)?reviews?)\s*[。.!！]?$",
    re.IGNORECASE,
)
_OTHER_SECTION = re.compile(
    r"^(?:#{1,6}\s+|(?:产品|商品)?(?:卖点|规格|参数|尺寸|价格|售价|促销|折扣|优惠|使用方法|文案|"
    r"设计要求|图片要求|需求|限制|备注|说明|其他说明)\s*[:：]|"
    r"(?:product\s+(?:benefits|features|specifications|details)|promotion|discount|price|pricing|"
    r"restrictions|requirements|notes|specifications|size(?:\s+info)?)\s*:)",
    re.IGNORECASE,
)
_QUOTED = re.compile(
    r'“(?P<curly>[^”]*)”|「(?P<japanese>[^」]*)」|『(?P<japanese_double>[^』]*)』|'
    r'"(?P<double>[^\"]*)"|(?<!\w)\'(?P<single>[^\']*)\'(?!\w)'
)
_QUOTE_SEPARATORS = re.compile(r"^[\s,，;；、|.。!！?？-]*$")


def _has_review_text(value: str) -> bool:
    check = value.strip()
    pairs = {"(": ")", "（": "）", "[": "]", "【": "】"}
    while len(check) >= 2 and pairs.get(check[0]) == check[-1]:
        check = check[1:-1].strip()
    return bool(check) and not (
        _REVIEW_REQUEST.search(check) or _REVIEW_ABSENT.fullmatch(check) or _REVIEW_COUNT_ONLY.fullmatch(check)
    )


def _review_row(row: str) -> list[str]:
    body = _REVIEW_ITEM.sub("", row, count=1).strip()
    if not _has_review_text(body):
        return []
    quoted = list(_QUOTED.finditer(body))
    if quoted:
        residue = _QUOTED.sub("", body)
        if _QUOTE_SEPARATORS.fullmatch(residue):
            values = [next(value for value in match.groups() if value is not None) for match in quoted]
            return [value for value in values if _has_review_text(value)]
        if len(quoted) == 1:
            match = quoted[0]
            prefix, suffix = body[:match.start()], body[match.end():]
            attribution = re.fullmatch(r"[^:：\n]{1,60}\s*[:：]\s*", prefix)
            if attribution and _QUOTE_SEPARATORS.fullmatch(suffix):
                value = next(value for value in match.groups() if value is not None)
                return [value] if _has_review_text(value) else []
    # A provided plain-text record can contain its own quotes/contractions.
    # Retain the whole supplied record instead of extracting an inner adjective.
    return [body]


def review_quotes(brief: str) -> list[str]:
    """Read actual entries inside explicitly labelled review-data sections.

    Supports numbered/bulleted records, plain records, common quotation marks,
    inline quoted lists and basic Markdown headings. Returns source order and
    the supplied count without inventing or deduplicating entries. Numbering,
    enclosing quotes and a simple ``author: quoted text`` wrapper are removed;
    the quote wording/punctuation is retained. An unrelated heading ends the
    section; after a blank separator only explicitly marked entries continue it.
    Requests such as "add four reviews" and placeholders are not source data.
    """
    if not isinstance(brief, str) or not brief.strip():
        return []
    result: list[str] = []
    active = False
    separated = False
    for raw_line in brief.splitlines():
        line = raw_line.strip()
        heading = _REVIEW_HEADING.fullmatch(line)
        if heading:
            active, separated = True, False
            if heading.group("body"):
                result.extend(_review_row(heading.group("body")))
            continue
        if not active:
            continue
        if not line:
            separated = True
            continue
        if _OTHER_SECTION.search(line) or line.endswith((":", "：")) or line in {"---", "___"}:
            active = False
            continue
        explicitly_marked = bool(_REVIEW_ITEM.match(line)) or line.startswith(('"', "'", "“", "「", "『"))
        if separated and not explicitly_marked:
            active = False
            continue
        result.extend(_review_row(line))
        separated = False
    return result
