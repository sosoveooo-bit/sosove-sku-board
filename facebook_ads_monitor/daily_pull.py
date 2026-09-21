from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import traceback
from pathlib import Path
from typing import Any

from facebook_ads_monitor.backend import (
    build_dashboard_payload,
    human_range_name,
    number,
    redact_token_text,
    sanitize_range_name,
)

DEFAULT_RANGES = ["yesterday", "today", "last_7d", "last_30d"]
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "reports" / "daily"


def parse_ranges(value: str | None) -> list[str]:
    if not value:
        return DEFAULT_RANGES
    ranges = [sanitize_range_name(part.strip()) for part in value.split(",") if part.strip()]
    seen: set[str] = set()
    unique: list[str] = []
    for item in ranges:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique or DEFAULT_RANGES


def run_daily_pull(ranges: list[str], output_dir: Path, refresh: bool) -> dict[str, Any]:
    generated_at = dt.datetime.now().isoformat(timespec="seconds")
    run_id = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = output_dir / run_id
    reports: dict[str, Any] = {}
    errors: list[dict[str, str]] = []

    for range_name in ranges:
        try:
            payload = build_dashboard_payload(range_name=range_name, refresh=refresh)
            reports[range_name] = summarize_payload(payload)
        except Exception as exc:  # Keep partial results when one range fails.
            errors.append(
                {
                    "range": range_name,
                    "error": redact_token_text(str(exc)),
                    "traceback": redact_token_text(traceback.format_exc(limit=4)),
                }
            )

    result = {
        "ok": not errors,
        "generatedAt": generated_at,
        "refresh": refresh,
        "ranges": ranges,
        "reports": reports,
        "comparisons": build_comparisons(reports),
        "errors": errors,
    }
    write_outputs(result, run_dir, output_dir)
    return result


def summarize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary") or {}
    boards = payload.get("boards") or {}
    tables = payload.get("tables") or {}
    findings = tables.get("findings") or []
    source = payload.get("source") or {}

    scale = to_int(summary.get("scale"))
    reduce = to_int(summary.get("reduce"))
    fix_landing = to_int(summary.get("fix_landing"))
    warning = to_int(summary.get("warning")) + to_int(summary.get("critical"))

    return {
        "source": {
            "range": source.get("range"),
            "rangeLabel": source.get("rangeLabel"),
            "reportName": source.get("reportName"),
            "reportDir": source.get("reportDir"),
            "generatedAt": source.get("generatedAt"),
            "sourceMode": source.get("sourceMode"),
        },
        "decision": decision_text(summary),
        "summary": {
            "spend": round(number(summary.get("spend")), 2),
            "purchase": round(number(summary.get("purchase")), 2),
            "purchase_value": round(number(summary.get("purchase_value")), 2),
            "roas": round(number(summary.get("roas")), 4),
            "cpa": round(number(summary.get("cpa")), 4),
            "ctr": round(number(summary.get("ctr")), 4),
            "cpc": round(number(summary.get("cpc")), 4),
            "ads": to_int(summary.get("ads")),
            "accounts": to_int(summary.get("accounts")),
            "scale": scale,
            "reduce": reduce,
            "fix_landing": fix_landing,
            "warning": warning,
        },
        "topScale": compact_ads(boards.get("scale") or [], limit=8),
        "topRisk": compact_ads(boards.get("risk") or [], limit=8),
        "topNoAtc": compact_ads(boards.get("noAtc") or [], limit=8),
        "topFindings": compact_findings(findings, limit=10),
    }


def decision_text(summary: dict[str, Any]) -> str:
    roas = number(summary.get("roas"))
    purchase = number(summary.get("purchase"))
    scale = number(summary.get("scale"))
    reduce = number(summary.get("reduce"))
    fix_landing = number(summary.get("fix_landing"))
    warning = number(summary.get("warning")) + number(summary.get("critical"))

    if fix_landing > 0 or warning >= 30:
        return "先处理承接和风险广告，再考虑放量。"
    if roas >= 2.5 and scale > reduce:
        return "保留胜出素材，可小步测试加预算。"
    if purchase == 0 and number(summary.get("clicks")) > 0:
        return "有点击但缺购买，优先检查落地页、结账和支付链路。"
    return "继续观察，先按广告动作表处理重点项。"


def compact_ads(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    compacted: list[dict[str, Any]] = []
    for row in rows[:limit]:
        compacted.append(
            {
                "ad_id": row.get("ad_id"),
                "ad_name": row.get("ad_name"),
                "account_name": row.get("account_name"),
                "campaign_name": row.get("campaign_name"),
                "family": row.get("family"),
                "action": row.get("action"),
                "action_label": row.get("action_label"),
                "spend": round(number(row.get("spend")), 2),
                "purchase": round(number(row.get("purchase")), 2),
                "roas": round(number(row.get("roas")), 4),
                "cpa": round(number(row.get("cpa")), 4),
                "clicks": round(max(number(row.get("inline_link_clicks")), number(row.get("clicks"))), 2),
                "add_to_cart": round(number(row.get("add_to_cart")), 2),
            }
        )
    return compacted


def compact_findings(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    compacted: list[dict[str, Any]] = []
    for row in rows[:limit]:
        compacted.append(
            {
                "level": row.get("level"),
                "category": row.get("category"),
                "name": row.get("name") or row.get("entity"),
                "reason": row.get("reason"),
                "action": row.get("action"),
                "spend": round(number(row.get("spend")), 2),
                "roas": round(number(row.get("roas")), 4),
            }
        )
    return compacted


def build_comparisons(reports: dict[str, Any]) -> dict[str, Any]:
    comparisons: dict[str, Any] = {}
    if "today" in reports and "yesterday" in reports:
        comparisons["today_vs_yesterday"] = compare_reports(reports["today"], reports["yesterday"])
    return comparisons


def compare_reports(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_summary = left.get("summary") or {}
    right_summary = right.get("summary") or {}
    return {
        metric: compare_metric(left_summary.get(metric), right_summary.get(metric))
        for metric in ["spend", "purchase", "purchase_value", "roas", "cpa", "ctr", "ads"]
    }


def compare_metric(current: Any, baseline: Any) -> dict[str, float | None]:
    current_num = number(current)
    baseline_num = number(baseline)
    delta = current_num - baseline_num
    pct = (delta / baseline_num * 100) if baseline_num else None
    return {
        "current": round(current_num, 4),
        "baseline": round(baseline_num, 4),
        "delta": round(delta, 4),
        "pct": round(pct, 2) if pct is not None else None,
    }


def write_outputs(result: dict[str, Any], run_dir: Path, output_dir: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_text = json.dumps(result, ensure_ascii=False, indent=2)
    markdown_text = build_markdown(result)

    (run_dir / "analysis.json").write_text(json_text, encoding="utf-8")
    (run_dir / "analysis.md").write_text(markdown_text, encoding="utf-8")
    (output_dir / "latest.json").write_text(json_text, encoding="utf-8")
    (output_dir / "latest.md").write_text(markdown_text, encoding="utf-8")


def build_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Facebook Ads Daily Analysis",
        "",
        f"- 生成时间: {result.get('generatedAt')}",
        f"- 拉取模式: {'刷新 Facebook 数据' if result.get('refresh') else '读取本地缓存'}",
        f"- 状态: {'成功' if result.get('ok') else '部分失败'}",
        "",
    ]

    for range_name in result.get("ranges", []):
        report = (result.get("reports") or {}).get(range_name)
        if not report:
            continue
        summary = report.get("summary") or {}
        source = report.get("source") or {}
        lines.extend(
            [
                f"## {source.get('rangeLabel') or human_range_name(range_name)}",
                "",
                f"- 决策: {report.get('decision')}",
                f"- 报表: {source.get('reportName') or '-'}",
                f"- 花费: {money(summary.get('spend'))}",
                f"- 购买: {num(summary.get('purchase'))}",
                f"- ROAS: {ratio(summary.get('roas'))}",
                f"- CPA: {money(summary.get('cpa'))}",
                f"- 广告: {num(summary.get('ads'))}",
                f"- 放量/降预算/查承接/警告: {num(summary.get('scale'))} / {num(summary.get('reduce'))} / {num(summary.get('fix_landing'))} / {num(summary.get('warning'))}",
                "",
            ]
        )
        append_ad_section(lines, "放量候选", report.get("topScale") or [])
        append_ad_section(lines, "降预算风险", report.get("topRisk") or [])
        append_ad_section(lines, "点击无加购", report.get("topNoAtc") or [])
        append_finding_section(lines, report.get("topFindings") or [])

    comparison = (result.get("comparisons") or {}).get("today_vs_yesterday")
    if comparison:
        lines.extend(["## 今天 vs 昨天", ""])
        for key, label in [
            ("spend", "花费"),
            ("purchase", "购买"),
            ("roas", "ROAS"),
            ("cpa", "CPA"),
            ("ctr", "CTR"),
        ]:
            item = comparison.get(key) or {}
            lines.append(
                f"- {label}: {compare_value(key, item.get('current'))} / 昨天 {compare_value(key, item.get('baseline'))} / 变化 {compare_delta(key, item)}"
            )
        lines.append("")

    if result.get("errors"):
        lines.extend(["## 错误", ""])
        for error in result.get("errors") or []:
            lines.append(f"- {error.get('range')}: {error.get('error')}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def append_ad_section(lines: list[str], title: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    lines.extend([f"### {title}", ""])
    for row in rows:
        name = compact_text(row.get("ad_name") or row.get("ad_id"), 64)
        lines.append(
            f"- {name} | {money(row.get('spend'))} | 购买 {num(row.get('purchase'))} | ROAS {ratio(row.get('roas'))} | {row.get('action_label') or row.get('action') or '-'}"
        )
    lines.append("")


def append_finding_section(lines: list[str], rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    lines.extend(["### 主要诊断", ""])
    for row in rows:
        name = compact_text(row.get("name") or row.get("category") or "诊断", 54)
        reason = compact_text(row.get("reason") or row.get("category") or "-", 84)
        lines.append(f"- [{row.get('level') or 'info'}] {name}: {reason}")
    lines.append("")


def compare_value(metric: str, value: Any) -> str:
    if metric in {"spend", "cpa"}:
        return money(value)
    if metric in {"roas"}:
        return ratio(value)
    if metric in {"ctr"}:
        return percent(value)
    return num(value)


def compare_delta(metric: str, item: dict[str, Any]) -> str:
    delta = item.get("delta")
    pct_value = item.get("pct")
    label = compare_value(metric, delta)
    if pct_value is None:
        return label
    sign = "+" if number(pct_value) > 0 else ""
    return f"{label} ({sign}{pct_value}%)"


def money(value: Any) -> str:
    return f"${number(value):,.2f}"


def num(value: Any) -> str:
    return f"{number(value):,.0f}"


def ratio(value: Any) -> str:
    return f"{number(value):.2f}x"


def percent(value: Any) -> str:
    return f"{number(value):.2f}%"


def compact_text(value: Any, max_length: int) -> str:
    text = " ".join(str(value or "-").split())
    if len(text) <= max_length:
        return text
    return text[: max_length - 1] + "…"


def to_int(value: Any) -> int:
    return int(round(number(value)))


def main() -> int:
    parser = argparse.ArgumentParser(description="Pull and analyze Facebook ads data for the dashboard.")
    parser.add_argument("--ranges", default=",".join(DEFAULT_RANGES), help="Comma-separated ranges to refresh.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for daily analysis outputs.")
    parser.add_argument("--no-refresh", action="store_true", help="Use cached reports instead of pulling fresh data.")
    args = parser.parse_args()

    result = run_daily_pull(
        ranges=parse_ranges(args.ranges),
        output_dir=Path(args.output_dir),
        refresh=not args.no_refresh,
    )
    latest = Path(args.output_dir) / "latest.md"
    print(f"Daily FB analysis written to: {latest}")
    if result.get("errors"):
        for error in result.get("errors") or []:
            print(f"ERROR {error.get('range')}: {error.get('error')}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
