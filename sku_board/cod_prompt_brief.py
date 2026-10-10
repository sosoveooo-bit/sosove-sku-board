"""Resolve local scene directions without changing product facts or saved input."""
from __future__ import annotations

import copy
import re
from typing import Any


_MARKET_COUNTRIES = {"JP": "日本", "KR": "韩国", "US": "美国", "DE": "德国"}
_LOCAL_DIRECTION = re.compile(
    r"(?P<country>日本|韩国|美国|德国)\s*(?P<direction>(?:本土|当地|本地)?(?:"
    r"电商(?:高密度)?排版|家庭(?:厨房|餐桌)(?:场景)?|厨房场景|餐桌场景|"
    r"(?:人物|模特)(?:与使用)?场景))"
)


def localized_direction(value: str, market: str) -> str:
    """Only adapt explicit local staging; never replace an origin or brand name."""
    target = _MARKET_COUNTRIES.get(market)
    if not target:
        return value

    def adapt(match: re.Match) -> str:
        prefix = value[max(0, match.start() - 8):match.start()]
        if re.search(r"(?:不要|禁止|避免|排除|不使用|非)\s*$", prefix):
            return match.group(0)
        return target + match.group("direction")

    return _LOCAL_DIRECTION.sub(adapt, value)


def planning_form(form: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(form)
    result["style"] = localized_direction(form.get("style", ""), form["market"])
    result["points"] = [localized_direction(point, form["market"]) for point in form["points"]]
    return result


QUALITY_DIRECTION = (
    "The selected form.market controls local people, use scenes and added artwork language. "
    "A different country mentioned only as a local staging/style direction must be adapted to this market; "
    "preserve genuine supplied product origin, brand names and original package markings. "
    "Separate product facts from scene/style requests in form.points: staging is not an ingredient, feature, certification or benefit. "
    "Never invent packaging geometry, printed packaging text, ingredients, garnish, accessories, processing, nutrition values, "
    "cooking temperatures/times, storage duration or origin when the brief/references do not supply them. "
    "If product/detail/package references are absent, keep product appearance provisional and use supplied descriptions only. "
    "User claims are not verified evidence: do not turn an unsupported nutrition/health claim into a badge, chart, test, "
    "certification or unqualified factual guarantee. Use an evidenced benefit instead and note missing confirmation in productSummary. "
    "Translate meaning as a native ecommerce copywriter, never transliterate Chinese planning phrases into artwork. "
    "For JP copy, do not embed Chinese words such as 整只, 锁鲜, 即食 or 空气炸锅 inside Japanese; "
    "use idiomatic Japanese, short complete phrases and avoid unexplained Chinese marketing terms. "
    "Only the current page's headline and copyLabels are approved artwork copy. "
    "No page number, source index, model ID or planning note may appear in the artwork. "
)
