#!/usr/bin/env python3
"""Analyze TikTok ad CSV exports and print an action-oriented report."""

from __future__ import annotations

import argparse
import csv
import glob
import json
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


DEFAULT_EXPORTER = Path(r"C:\Users\Administrator\.qclaw\scripts\tiktok_export_all_ads.ps1")
DEFAULT_DATA_DIR = Path(r"C:\Users\Administrator\.qclaw\scripts")
TEXT_FIELDS = [
    "AccountName",
    "CampaignName",
    "AdgroupName",
    "AdName",
    "OperationStatus",
    "SecondaryStatus",
]
AD_ID_COLUMNS = ("ad_id", "adid", "ad id", "ad", "advertisement_id", "广告id", "广告ID", "素材id", "素材ID")
ORDER_ID_COLUMNS = ("order_id", "orderid", "order no", "订单id", "订单ID", "订单号")
REVENUE_COLUMNS = ("revenue", "amount", "total", "order_amount", "sales", "gmv", "销售额", "订单金额", "实收")
ORDER_COUNT_COLUMNS = ("orders", "order_count", "quantity", "qty", "订单数", "数量")
DATE_COLUMNS = ("date", "created_at", "paid_at", "order_date", "日期", "下单时间", "付款时间")
PAYMENT_STATUS_COLUMNS = (
    "payment_status", "payment status", "financial_status", "financial status", "pay_status",
    "status", "订单状态", "支付状态", "付款状态", "财务状态",
)
CHECKOUT_STATUS_COLUMNS = (
    "checkout_status", "checkout status", "checkout_state", "checkout state", "结账状态", "收银台状态",
)
FAILURE_REASON_COLUMNS = (
    "failure_reason", "payment_error", "error_message", "decline_reason", "失败原因", "支付失败原因", "错误信息",
)
CREATIVE_AD_ID_COLUMNS = ("ad_id", "adid", "ad id", "广告id", "广告ID", "素材id", "素材ID")
CREATIVE_FILE_COLUMNS = ("material_file", "file_name", "filename", "creative_name", "video_name", "素材文件", "素材名称", "视频文件")
CREATIVE_TYPE_COLUMNS = ("material_type", "creative_type", "type", "素材类型", "视频类型")
CREATIVE_ANGLE_COLUMNS = ("creative_angle", "angle", "selling_point", "卖点", "素材角度")
OPENING_HOOK_COLUMNS = ("opening_hook", "hook", "first_3_seconds", "开头卖点", "前三秒")
VIDEO_URL_COLUMNS = ("video_url", "material_url", "url", "视频链接", "素材链接")
CREATOR_COLUMNS = ("creator", "talent", "author", "达人", "拍摄人")
NOTE_COLUMNS = ("note", "notes", "remark", "备注")
ACTION_LABELS_CN = {
    "immediate_close": "立即关闭",
    "pause_observe": "暂停观察",
    "keep_small_run": "保留小跑",
    "copy_variant": "复制变体",
    "scale_observe": "放量观察",
    "fix_payment": "修复支付",
    "product_stop_test": "产品停止测试",
    "ignore_no_spend": "无消耗忽略",
    "watch": "继续观察",
}
MARKET_CODES = {
    "AE", "AR", "AT", "AU", "BE", "BR", "CA", "CH", "CL", "CO", "CZ", "DE", "DK", "EG", "ES", "FI",
    "FR", "GB", "GR", "HK", "HU", "ID", "IE", "IL", "IT", "JP", "KR", "MX", "MY", "NL", "NO", "NZ",
    "PH", "PL", "PT", "RO", "SA", "SE", "SG", "TH", "TR", "TW", "US", "VN", "ZA",
}

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


@dataclass
class RuleConfig:
    target_cpa: float | None
    stop_spend: float
    stop_clicks: int
    weak_ctr: float
    min_impressions_for_ctr: int
    retest_min_ctr: float
    retest_max_cpc: float
    retest_min_clicks: int
    min_scale_orders: int
    min_budget: float
    max_budget: float | None
    scale_budget_pct: float
    cpc_spike_multiplier: float
    spend_spike_multiplier: float
    order_drop_clicks: int


def to_float(value: Any) -> float:
    try:
        if value is None or value == "":
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def to_int(value: Any) -> int:
    try:
        if value is None or value == "":
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def repair_text(value: Any) -> str:
    text = str(value or "")
    if not text:
        return ""
    mojibake_marks = ("Ã", "Â", "ä", "å", "æ", "è", "é", "ç")
    if not any(mark in text for mark in mojibake_marks):
        return text
    for encoding in ("cp1252", "latin1"):
        try:
            repaired = text.encode(encoding).decode("utf-8")
        except UnicodeError:
            continue
        if sum("\u4e00" <= char <= "\u9fff" for char in repaired) > sum("\u4e00" <= char <= "\u9fff" for char in text):
            return repaired
    return text


def normalize_column_name(value: str) -> str:
    return re.sub(r"[\s_\-]+", "", str(value or "").strip().lower())


def get_by_alias(row: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    normalized = {normalize_column_name(key): key for key in row.keys()}
    for alias in aliases:
        key = normalized.get(normalize_column_name(alias))
        if key is not None:
            return row.get(key)
    return None


def normalize_payment_status(value: Any, checkout_value: Any = "") -> str:
    text = repair_text(value).strip().lower()
    checkout_text = repair_text(checkout_value).strip().lower()
    combined = " ".join(part for part in (text, checkout_text) if part)
    if not combined:
        return "unknown"
    if any(word in combined for word in ("paid", "success", "succeeded", "captured", "已支付", "支付成功", "付款成功")):
        return "paid"
    if any(word in combined for word in ("failed", "failure", "declined", "拒付", "失败", "支付失败", "付款失败")):
        return "payment_failed"
    if any(word in combined for word in ("abandoned", "checkout", "未付款", "未支付", "待支付", "pending", "处理中")):
        return "checkout_pending"
    if any(word in combined for word in ("cancel", "void", "refunded", "取消", "退款", "作废")):
        return "cancelled"
    return "unknown"


def detect_material_name(*values: str) -> str:
    for raw in values:
        text = repair_text(raw)
        if not text:
            continue
        if re.search(r"\.(mp4|mov|mkv|avi|jpg|jpeg|png|webp)$", text, re.IGNORECASE):
            return Path(text).name
        if re.search(r"[A-Za-z0-9_-]{8,}\.(mp4|mov|mkv|avi|jpg|jpeg|png|webp)$", text, re.IGNORECASE):
            return Path(text).name
    return repair_text(values[0] if values else "")


def guess_material_type(*values: str) -> str:
    text = " ".join(repair_text(value) for value in values if value)
    if re.search(r"\.(mp4|mov|mkv|avi)$", text, re.IGNORECASE):
        return "video"
    if re.search(r"\.(jpg|jpeg|png|webp)$", text, re.IGNORECASE):
        return "image"
    if re.search(r"直播|live", text, re.IGNORECASE):
        return "live"
    return "unknown"


def guess_creative_angle(product: str, campaign_name: str, ad_name: str) -> tuple[str, str]:
    text = " ".join([repair_text(product), repair_text(campaign_name), repair_text(ad_name)]).lower()
    rules = [
        (("懒人", "神器", "一键", "便捷", "省事"), ("convenience", "problem-solution")),
        (("高质", "升级", "升级高效", "品质"), ("quality", "premium")),
        (("热销", "爆款", "畅销", "销量"), ("social-proof", "bestseller")),
        (("显瘦", "阔腿", "修身", "显腿长"), ("fit-angle", "body-benefit")),
        (("透视", "潮牌", "设计感", "穿搭"), ("style-angle", "fashion")),
        (("牙齿", "炫白", "美白", "口腔"), ("result-angle", "beauty-result")),
        (("JP", "日本"), ("jp-market-angle", "local-market")),
    ]
    for keywords, result in rules:
        if any(keyword.lower() in text for keyword in keywords):
            return result
    return ("generic", "generic")


def estimate_opening_hook(product: str, ad_name: str, campaign_name: str) -> str:
    text = " ".join([repair_text(product), repair_text(ad_name), repair_text(campaign_name)]).lower()
    if any(word in text for word in ("懒人", "一键", "神器", "便捷")):
        return "problem-solution"
    if any(word in text for word in ("热销", "爆款", "销量")):
        return "social-proof"
    if any(word in text for word in ("高质", "升级", "品质")):
        return "quality-proof"
    if any(word in text for word in ("显瘦", "阔腿", "修身")):
        return "fit-proof"
    if any(word in text for word in ("透视", "设计感", "潮牌")):
        return "style-showcase"
    if any(word in text for word in ("牙齿", "美白", "炫白")):
        return "before-after"
    return "generic"


def normalize_creative_text(value: Any) -> str:
    text = repair_text(value)
    return text.strip()


def read_creative_tags(paths: list[str]) -> dict[str, dict[str, str]]:
    tags: dict[str, dict[str, str]] = {}
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            print(f"WARNING: missing creative tags CSV: {path}", file=sys.stderr)
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                ad_id = str(get_by_alias(row, CREATIVE_AD_ID_COLUMNS) or "").strip()
                if not ad_id:
                    continue
                tags[ad_id] = {
                    "material_name": normalize_creative_text(get_by_alias(row, CREATIVE_FILE_COLUMNS)),
                    "material_type": normalize_creative_text(get_by_alias(row, CREATIVE_TYPE_COLUMNS)),
                    "creative_angle": normalize_creative_text(get_by_alias(row, CREATIVE_ANGLE_COLUMNS)),
                    "opening_hook": normalize_creative_text(get_by_alias(row, OPENING_HOOK_COLUMNS)),
                    "video_url": normalize_creative_text(get_by_alias(row, VIDEO_URL_COLUMNS)),
                    "creator_tag": normalize_creative_text(get_by_alias(row, CREATOR_COLUMNS)),
                    "creative_note": normalize_creative_text(get_by_alias(row, NOTE_COLUMNS)),
                    "source_file": str(path),
                }
    return tags


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def iter_dates(start: date, end: date) -> list[date]:
    if end < start:
        raise SystemExit("--end-date must be on or after --start-date.")
    days: list[date] = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days


def date_window(args: argparse.Namespace) -> tuple[date | None, date | None]:
    if args.days:
        if args.start_date and args.end_date:
            return parse_date(args.start_date), parse_date(args.end_date)
        if args.start_date:
            start = parse_date(args.start_date)
            return start, start + timedelta(days=args.days - 1)
        end = parse_date(args.end_date) if args.end_date else date.today()
        return end - timedelta(days=args.days - 1), end
    if args.start_date or args.end_date:
        end = parse_date(args.end_date) if args.end_date else date.today()
        start = parse_date(args.start_date) if args.start_date else end
        return start, end
    return None, None


def daily_csv_path(data_dir: Path, day: date) -> Path:
    day_text = day.isoformat()
    return data_dir / f"tiktok_all_ads_{day_text}_to_{day_text}.csv"


def full_range_csv_path(data_dir: Path, start: date, end: date) -> Path:
    return data_dir / f"tiktok_all_ads_{start.isoformat()}_to_{end.isoformat()}.csv"


def run_exporter(exporter: Path, start: date, end: date) -> None:
    if not exporter.exists():
        raise SystemExit(f"Exporter not found: {exporter}")
    command = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(exporter),
        "-StartDate",
        start.isoformat(),
        "-EndDate",
        end.isoformat(),
    ]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise SystemExit(f"Exporter failed for {start}~{end}:\n{result.stderr or result.stdout}")


def collect_paths(args: argparse.Namespace) -> list[Path]:
    paths = [Path(path) for path in args.csv]
    if args.glob:
        paths.extend(Path(path) for path in glob.glob(args.glob))

    start, end = date_window(args)
    if start and end:
        data_dir = Path(args.data_dir)
        exporter = Path(args.exporter)
        window_days = iter_dates(start, end)

        if args.refresh:
            for day in window_days:
                run_exporter(exporter, day, day)
            if args.include_full_range:
                run_exporter(exporter, start, end)

        for day in window_days:
            path = daily_csv_path(data_dir, day)
            if path.exists():
                paths.append(path)
            elif not args.refresh:
                print(f"WARNING: missing daily CSV: {path}", file=sys.stderr)

        if args.include_full_range:
            path = full_range_csv_path(data_dir, start, end)
            if path.exists():
                paths.append(path)

    unique_paths = sorted({path.resolve() for path in paths if path.exists()})
    if not unique_paths:
        raise SystemExit("No CSV files found. Use --csv, --glob, or --days with existing exports or --refresh.")
    return unique_paths


def infer_date(row: dict[str, str], fallback: str) -> str:
    start_date = row.get("StartDate") or ""
    end_date = row.get("EndDate") or ""
    if start_date and end_date and start_date == end_date:
        return start_date
    if start_date and end_date:
        return f"{start_date}~{end_date}"
    return fallback


def clean_product_name(name: str) -> str:
    text = re.sub(r"\u300e[^\u300f]*\u300f", "", name or "")
    text = re.sub(r"\u3010[^\u3011]*\u3011", "", text)
    text = re.sub(r"\[[^\]]*\]", "", text)
    text = text.strip()
    if "#" in text:
        text = text.split("#")[-1]
    text = re.sub(r"^[A-Za-z]{1,5}-", "", text)
    text = re.sub(r"^\d+[_-]", "", text)
    return text.strip(" _-#") or "Unknown"


def extract_market(*values: str) -> str:
    text = " ".join(value or "" for value in values).upper()
    for match in re.finditer(r"(?:^|[#_\-\s])([A-Z]{2})(?=[#_\-\s])", text):
        code = match.group(1)
        if code in MARKET_CODES:
            return code
    return "Unknown"


def read_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                for field in TEXT_FIELDS:
                    row[field] = repair_text(row.get(field, ""))
                fallback = path.stem.replace("tiktok_all_ads_", "")
                row["SourceFile"] = str(path)
                row["Date"] = infer_date(row, fallback)
                row["SpendN"] = to_float(row.get("Spend"))
                row["ImpressionsN"] = to_int(row.get("Impressions"))
                row["ClicksN"] = to_int(row.get("Clicks"))
                row["ConversionN"] = to_float(row.get("Conversion"))
                row["Product"] = clean_product_name(row.get("CampaignName") or row.get("AdgroupName") or "")
                row["Market"] = extract_market(row.get("CampaignName", ""), row.get("AdgroupName", ""))
                rows.append(row)
    return rows


def read_order_rows(paths: list[str]) -> list[dict[str, Any]]:
    orders: list[dict[str, Any]] = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            print(f"WARNING: missing order CSV: {path}", file=sys.stderr)
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                ad_id = str(get_by_alias(row, AD_ID_COLUMNS) or "").strip()
                revenue = to_float(get_by_alias(row, REVENUE_COLUMNS))
                order_count = to_float(get_by_alias(row, ORDER_COUNT_COLUMNS)) or 1.0
                order_id = str(get_by_alias(row, ORDER_ID_COLUMNS) or "").strip()
                order_date = str(get_by_alias(row, DATE_COLUMNS) or "").strip()
                payment_status_raw = str(get_by_alias(row, PAYMENT_STATUS_COLUMNS) or "").strip()
                checkout_status_raw = str(get_by_alias(row, CHECKOUT_STATUS_COLUMNS) or "").strip()
                failure_reason = str(get_by_alias(row, FAILURE_REASON_COLUMNS) or "").strip()
                payment_status = normalize_payment_status(payment_status_raw, checkout_status_raw)
                orders.append(
                    {
                        "ad_id": ad_id,
                        "revenue": revenue,
                        "orders": order_count,
                        "order_id": order_id,
                        "date": order_date,
                        "payment_status": payment_status,
                        "payment_status_raw": payment_status_raw,
                        "checkout_status": checkout_status_raw,
                        "failure_reason": failure_reason,
                        "source_file": str(path),
                    }
                )
    return orders


def summarize_orders_by_ad(order_rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    by_ad: dict[str, dict[str, float]] = defaultdict(
        lambda: {"orders": 0.0, "revenue": 0.0, "failed_payments": 0.0, "checkout_attempts": 0.0}
    )
    for order in order_rows:
        ad_id = str(order.get("ad_id") or "").strip()
        if not ad_id:
            continue
        count = to_float(order.get("orders")) or 1.0
        status = str(order.get("payment_status") or "unknown")
        if status == "paid":
            by_ad[ad_id]["orders"] += count
            by_ad[ad_id]["revenue"] += to_float(order.get("revenue"))
        elif status == "payment_failed":
            by_ad[ad_id]["failed_payments"] += count
            by_ad[ad_id]["checkout_attempts"] += count
        elif status == "checkout_pending":
            by_ad[ad_id]["checkout_attempts"] += count
        else:
            by_ad[ad_id]["orders"] += count
            by_ad[ad_id]["revenue"] += to_float(order.get("revenue"))
    return dict(by_ad)


def order_totals(order_rows: list[dict[str, Any]]) -> dict[str, float]:
    paid_rows = [order for order in order_rows if str(order.get("payment_status") or "unknown") in {"paid", "unknown"}]
    failed_rows = [order for order in order_rows if str(order.get("payment_status") or "") == "payment_failed"]
    checkout_rows = [
        order for order in order_rows
        if str(order.get("payment_status") or "") in {"payment_failed", "checkout_pending"}
    ]
    return {
        "orders": round(sum(to_float(order.get("orders")) or 1.0 for order in paid_rows), 4),
        "revenue": round(sum(to_float(order.get("revenue")) for order in paid_rows), 2),
        "failed_payments": round(sum(to_float(order.get("orders")) or 1.0 for order in failed_rows), 4),
        "checkout_attempts": round(sum(to_float(order.get("orders")) or 1.0 for order in checkout_rows), 4),
    }


def metric(rows: list[dict[str, Any]]) -> dict[str, Any]:
    spend = sum(row["SpendN"] for row in rows)
    impressions = sum(row["ImpressionsN"] for row in rows)
    clicks = sum(row["ClicksN"] for row in rows)
    conversions = sum(row["ConversionN"] for row in rows)
    return {
        "spend": round(spend, 2),
        "impressions": impressions,
        "clicks": clicks,
        "conversions": round(conversions, 4),
        "ctr_pct": round(clicks / impressions * 100, 2) if impressions else 0,
        "cpc": round(spend / clicks, 2) if clicks else None,
        "cpm": round(spend / impressions * 1000, 2) if impressions else None,
        "platform_cpa": round(spend / conversions, 2) if conversions else None,
    }


def add_profit_metrics(item: dict[str, Any], orders: float | None, revenue: float | None, gross_margin: float | None) -> None:
    spend = float(item.get("spend") or 0)
    item["attributed_orders"] = round(orders, 4) if orders is not None else None
    item["attributed_revenue"] = round(revenue, 2) if revenue is not None else None
    item["attributed_cpa"] = round(spend / orders, 2) if orders and orders > 0 else None
    item["attributed_roas"] = round(revenue / spend, 4) if revenue is not None and spend > 0 else None
    item["attributed_gross_profit"] = (
        round(revenue * gross_margin, 2)
        if revenue is not None and gross_margin is not None
        else None
    )
    item["attributed_contribution_profit"] = (
        round(item["attributed_gross_profit"] - spend, 2)
        if item.get("attributed_gross_profit") is not None
        else None
    )


def add_business_metrics(summary: dict[str, Any], args: argparse.Namespace, totals: dict[str, float] | None = None) -> None:
    totals = totals or {}
    actual_orders = args.actual_orders if args.actual_orders is not None else totals.get("orders")
    actual_revenue = args.actual_revenue if args.actual_revenue is not None else totals.get("revenue")
    gross_margin = args.gross_margin
    if actual_revenue is None and args.avg_order_value is not None and actual_orders:
        actual_revenue = round(args.avg_order_value * actual_orders, 2)
    if gross_margin is None and args.avg_order_value and args.product_cost is not None:
        gross_margin = round((args.avg_order_value - args.product_cost - args.shipping_cost) / args.avg_order_value, 4)

    summary["actual_orders"] = actual_orders
    summary["actual_revenue"] = actual_revenue
    summary["gross_margin"] = gross_margin
    summary["avg_order_value"] = args.avg_order_value
    summary["product_cost"] = args.product_cost
    summary["shipping_cost"] = args.shipping_cost
    summary["failed_payments"] = totals.get("failed_payments", 0.0)
    summary["checkout_attempts"] = totals.get("checkout_attempts", 0.0)
    summary["actual_cpa"] = (
        round(summary["spend"] / actual_orders, 2)
        if actual_orders and actual_orders > 0
        else None
    )
    summary["roas"] = (
        round(actual_revenue / summary["spend"], 4)
        if actual_revenue is not None and summary["spend"] > 0
        else None
    )
    summary["gross_profit"] = (
        round(actual_revenue * gross_margin, 2)
        if actual_revenue is not None and gross_margin is not None
        else None
    )
    summary["contribution_profit"] = (
        round(summary["gross_profit"] - summary["spend"], 2)
        if summary.get("gross_profit") is not None
        else None
    )
    summary["break_even_cpa"] = (
        round((actual_revenue / actual_orders) * gross_margin, 2)
        if actual_revenue is not None and actual_orders and actual_orders > 0 and gross_margin is not None
        else None
    )
    summary["profit_status"] = (
        "profitable" if summary.get("contribution_profit") is not None and summary["contribution_profit"] >= 0
        else "loss" if summary.get("contribution_profit") is not None
        else "unknown"
    )
    summary["tracking_mismatch"] = (
        actual_orders is not None and round(summary["conversions"], 4) != round(actual_orders, 4)
    )


def group_rows(
    rows: list[dict[str, Any]],
    keys: list[str],
    attribution_by_ad: dict[str, dict[str, float]] | None = None,
    gross_margin: float | None = None,
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(str(row.get(key, "")) for key in keys)].append(row)

    output: list[dict[str, Any]] = []
    for key_values, group in groups.items():
        item = {key: key_values[idx] for idx, key in enumerate(keys)}
        item.update(metric(group))
        if attribution_by_ad is not None:
            ad_ids = {str(row.get("AdId") or "").strip() for row in group}
            attr_orders = sum(attribution_by_ad.get(ad_id, {}).get("orders", 0.0) for ad_id in ad_ids)
            attr_revenue = sum(attribution_by_ad.get(ad_id, {}).get("revenue", 0.0) for ad_id in ad_ids)
            attr_failed_payments = sum(attribution_by_ad.get(ad_id, {}).get("failed_payments", 0.0) for ad_id in ad_ids)
            attr_checkout_attempts = sum(attribution_by_ad.get(ad_id, {}).get("checkout_attempts", 0.0) for ad_id in ad_ids)
            add_profit_metrics(item, attr_orders, attr_revenue, gross_margin)
            item["attributed_failed_payments"] = round(attr_failed_payments, 4)
            item["attributed_checkout_attempts"] = round(attr_checkout_attempts, 4)
        item["spend_days"] = sum(
            1 for report_date in {row["Date"] for row in group}
            if sum(row["SpendN"] for row in group if row["Date"] == report_date) > 0
        )
        item["click_days"] = sum(
            1 for report_date in {row["Date"] for row in group}
            if sum(row["ClicksN"] for row in group if row["Date"] == report_date) > 0
        )
        output.append(item)

    output.sort(key=lambda item: (item["spend"], item["clicks"]), reverse=True)
    return output


def classify_ad(item: dict[str, Any], actual_orders_total: float | None, rules: RuleConfig) -> str:
    spend = float(item["spend"])
    clicks = int(item["clicks"])
    impressions = int(item["impressions"])
    ctr = float(item["ctr_pct"])
    cpc = item["cpc"] if item["cpc"] is not None else 0
    platform_conversions = float(item["conversions"])
    attr_orders = item.get("attributed_orders")
    attr_failed_payments = float(item.get("attributed_failed_payments") or 0)
    attr_checkout_attempts = float(item.get("attributed_checkout_attempts") or 0)
    no_real_orders = actual_orders_total == 0
    no_known_orders = actual_orders_total is None and platform_conversions == 0
    has_known_orders = actual_orders_total is not None and actual_orders_total > 0

    if attr_failed_payments > 0:
        return "payment_failure"
    if attr_checkout_attempts > 0 and (attr_orders is None or attr_orders == 0):
        return "checkout_no_order"
    if has_known_orders and platform_conversions > 0:
        return "order_signal_check"
    if has_known_orders and platform_conversions == 0:
        if rules.target_cpa and spend >= rules.target_cpa:
            return "spend_leak_target_cpa"
        if spend >= rules.stop_spend or clicks >= rules.stop_clicks:
            return "likely_no_order_spend_leak"
        if clicks >= max(10, rules.stop_clicks // 2):
            return "post_click_problem"
        if impressions >= rules.min_impressions_for_ctr and ctr < rules.weak_ctr:
            return "weak_hook"
        if ctr >= rules.retest_min_ctr and cpc and cpc <= rules.retest_max_cpc and clicks >= rules.retest_min_clicks:
            return "small_retest_only"
        return "watch"

    if no_real_orders and rules.target_cpa and spend >= rules.target_cpa:
        return "hard_stop_target_cpa"
    if no_real_orders and (spend >= rules.stop_spend or clicks >= rules.stop_clicks):
        return "hard_stop"
    if no_real_orders and spend >= max(2.0, rules.stop_spend / 2):
        return "stop_loss"
    if no_real_orders and clicks >= max(10, rules.stop_clicks // 2):
        return "post_click_problem"
    if no_known_orders and (spend >= rules.stop_spend or clicks >= rules.stop_clicks):
        return "needs_order_check"
    if impressions >= rules.min_impressions_for_ctr and ctr < rules.weak_ctr:
        return "weak_hook"
    if no_real_orders and ctr >= rules.retest_min_ctr and cpc and cpc <= rules.retest_max_cpc and clicks >= rules.retest_min_clicks:
        return "small_retest_only"
    if platform_conversions > 0 and actual_orders_total is None:
        return "platform_conversion_check"
    return "insufficient_data"


def classify_group(item: dict[str, Any], actual_orders_total: float | None, rules: RuleConfig) -> str:
    spend = float(item["spend"])
    clicks = int(item["clicks"])
    impressions = int(item["impressions"])
    ctr = float(item["ctr_pct"])
    cpc = item["cpc"] if item["cpc"] is not None else 0
    conversions = float(item["conversions"])
    attr_failed_payments = float(item.get("attributed_failed_payments") or 0)
    attr_checkout_attempts = float(item.get("attributed_checkout_attempts") or 0)
    is_product_group = "Product" in item

    if attr_failed_payments > 0:
        return "fix_payment"
    if attr_checkout_attempts > 0 and conversions == 0:
        return "pause_observe"
    if conversions > 0 and actual_orders_total != 0:
        return "keep_test_order_signal"
    if actual_orders_total == 0 or conversions == 0:
        if is_product_group and spend >= rules.stop_spend * 2 and clicks >= rules.stop_clicks:
            return "product_stop_test"
        if spend >= rules.stop_spend or clicks >= rules.stop_clicks:
            return "pause_observe"
        if clicks >= max(10, rules.stop_clicks // 2):
            return "pause_observe"
        if impressions >= rules.min_impressions_for_ctr and ctr < rules.weak_ctr:
            return "immediate_close"
        if ctr >= rules.retest_min_ctr and cpc and cpc <= rules.retest_max_cpc and clicks >= rules.retest_min_clicks:
            return "copy_variant"
    return "watch"


def enrich_creative_fields(item: dict[str, Any], creative_tags: dict[str, dict[str, str]] | None = None) -> None:
    creative_tags = creative_tags or {}
    tag = creative_tags.get(str(item.get("AdId") or "").strip(), {})
    angle, angle_group = guess_creative_angle(
        str(item.get("Product") or ""),
        str(item.get("CampaignName") or ""),
        str(item.get("AdName") or ""),
    )
    item["material_name"] = tag.get("material_name") or detect_material_name(str(item.get("AdName") or ""))
    item["material_type"] = tag.get("material_type") or guess_material_type(str(item.get("AdName") or ""))
    item["creative_angle"] = tag.get("creative_angle") or angle
    item["creative_angle_group"] = tag.get("creative_angle_group") or angle_group
    item["opening_hook"] = tag.get("opening_hook") or estimate_opening_hook(
        str(item.get("Product") or ""),
        str(item.get("AdName") or ""),
        str(item.get("CampaignName") or ""),
    )
    item["video_url"] = tag.get("video_url") or ""
    item["creator_tag"] = tag.get("creator_tag") or ""
    item["creative_note"] = tag.get("creative_note") or ""


def recommend_ad_action(item: dict[str, Any], rules: RuleConfig) -> tuple[str, str]:
    classification = str(item.get("classification") or "")
    spend = float(item.get("spend") or 0)
    clicks = int(item.get("clicks") or 0)
    conversions = float(item.get("conversions") or 0)
    attr_orders = item.get("attributed_orders")
    attr_failed_payments = float(item.get("attributed_failed_payments") or 0)
    attr_checkout_attempts = float(item.get("attributed_checkout_attempts") or 0)
    contribution = item.get("attributed_contribution_profit")

    if attr_failed_payments > 0:
        return "fix_payment", "checkout/payment failure exists; fix payment channel before spending more"
    if attr_checkout_attempts > 0 and not attr_orders:
        return "pause_observe", "checkout intent exists but paid order is not confirmed"
    if attr_orders is not None and attr_orders > 0:
        if contribution is not None and contribution < 0:
            return "keep_small_run", "has attributed order but contribution profit is still negative"
        if attr_orders >= rules.min_scale_orders:
            return "scale_observe", f"has {attr_orders:g} attributed orders; raise budget slowly"
        return "keep_small_run", f"has {attr_orders:g} attributed order signal; not enough orders to scale"
    if classification == "order_signal_check" or (conversions > 0 and attr_orders is None):
        return "keep_small_run", "platform conversion signal exists; confirm real order attribution before scaling"
    if classification in {"hard_stop_target_cpa", "hard_stop", "stop_loss", "spend_leak_target_cpa", "likely_no_order_spend_leak"}:
        return "immediate_close", "meaningful spend/clicks without order signal"
    if classification in {"post_click_problem", "needs_order_check"}:
        return "pause_observe", "clicks are coming in but purchase intent is not proven"
    if classification == "checkout_no_order":
        return "pause_observe", "checkout intent exists but paid order is not confirmed"
    if classification == "weak_hook":
        return "immediate_close", "weak hook/CTR signal"
    if classification == "small_retest_only":
        return "copy_variant", "cheap clicks and CTR signal, but no order proof yet"
    if spend == 0 and clicks == 0:
        return "ignore_no_spend", "no delivery"
    return "watch", "insufficient signal"


def suggest_budget(item: dict[str, Any], rules: RuleConfig) -> tuple[str, str, int | None, str]:
    action = str(item.get("recommended_action") or "watch")
    spend = float(item.get("spend") or 0)
    spend_days = max(1, int(item.get("spend_days") or 1))
    avg_daily_spend = round(spend / spend_days, 2)
    current_estimate = max(avg_daily_spend, rules.min_budget)
    if rules.max_budget is not None:
        current_estimate = min(current_estimate, rules.max_budget)

    if action in {"immediate_close", "product_stop_test"}:
        return ("0", "0", None, "close now; rebuild creative/product before spending again")
    if action == "pause_observe":
        return ("0 or minimum", str(rules.min_budget), rules.order_drop_clicks, "pause or run minimum budget only after landing/offer fix")
    if action == "fix_payment":
        return ("0 or minimum", str(rules.min_budget), rules.order_drop_clicks, "fix checkout/payment first; restart with minimum budget only")
    if action == "keep_small_run":
        budget = current_estimate
        return (f"{budget:.2f}", f"{budget:.2f}", rules.order_drop_clicks, "keep budget flat; do not scale before more orders")
    if action == "copy_variant":
        budget = rules.min_budget
        return (f"{budget:.2f}", f"{budget:.2f}", max(10, rules.order_drop_clicks // 2), "duplicate into 1-2 variants; stop quickly if no order")
    if action == "scale_observe":
        budget = round(current_estimate * (1 + rules.scale_budget_pct), 2)
        if rules.max_budget is not None:
            budget = min(budget, rules.max_budget)
        return (f"{budget:.2f}", f"{budget:.2f}", rules.order_drop_clicks, "increase slowly and check every day")
    if action == "ignore_no_spend":
        return ("0", "0", None, "ignore until delivery starts")
    return (f"{rules.min_budget:.2f}", f"{rules.min_budget:.2f}", rules.order_drop_clicks, "watch with minimum budget only")


def suggest_stop_spend(item: dict[str, Any], rules: RuleConfig) -> str:
    action = str(item.get("recommended_action") or "watch")
    if action in {"immediate_close", "product_stop_test", "ignore_no_spend"}:
        return "0"
    if action == "copy_variant":
        return f"{max(rules.min_budget, min(rules.stop_spend, rules.target_cpa or rules.stop_spend)):.2f}"
    if action in {"pause_observe", "fix_payment", "watch"}:
        return f"{rules.target_cpa or rules.stop_spend:.2f}"
    cpa = item.get("attributed_cpa") or item.get("platform_cpa") or rules.target_cpa
    if cpa:
        return f"{float(cpa):.2f}"
    return f"{rules.stop_spend:.2f}"


def suggest_scale_condition(item: dict[str, Any], rules: RuleConfig) -> str:
    action = str(item.get("recommended_action") or "watch")
    if action == "scale_observe":
        return f"scale only while attributed orders stay >= {rules.min_scale_orders} and CPA is acceptable"
    if action == "keep_small_run":
        return "do not scale until another paid order confirms the same ad"
    if action == "copy_variant":
        return "copy 1-2 variants; keep only variants with paid order signal"
    if action == "fix_payment":
        return "restart only after payment success rate is confirmed"
    if action == "pause_observe":
        return "restart only after landing page, offer, or payment issue is fixed"
    if action == "immediate_close":
        return "do not restart unchanged; rebuild creative or offer first"
    return "collect more signal before scaling"


def add_budget_and_action_fields(item: dict[str, Any], rules: RuleConfig) -> None:
    action = str(item.get("recommended_action") or "watch")
    item["action_label_cn"] = ACTION_LABELS_CN.get(action, action)
    tomorrow_budget, max_test_budget, stop_after_clicks, budget_note = suggest_budget(item, rules)
    item["tomorrow_budget_suggestion"] = tomorrow_budget
    item["max_test_budget"] = max_test_budget
    item["stop_after_clicks_without_order"] = stop_after_clicks
    item["stop_after_spend_without_order"] = suggest_stop_spend(item, rules)
    item["scale_condition"] = suggest_scale_condition(item, rules)
    item["budget_note"] = budget_note


def anomaly_alerts(item: dict[str, Any], avg_cpc: float | None, avg_daily_spend: float, rules: RuleConfig) -> list[str]:
    alerts: list[str] = []
    cpc = item.get("cpc")
    spend = float(item.get("spend") or 0)
    clicks = int(item.get("clicks") or 0)
    conversions = float(item.get("conversions") or 0)
    attr_orders = item.get("attributed_orders")
    attr_failed_payments = float(item.get("attributed_failed_payments") or 0)
    attr_checkout_attempts = float(item.get("attributed_checkout_attempts") or 0)
    ctr = float(item.get("ctr_pct") or 0)
    no_paid_order = attr_orders is None or attr_orders == 0
    if cpc is not None and avg_cpc and cpc > avg_cpc * rules.cpc_spike_multiplier:
        alerts.append("cpc_spike")
    if avg_daily_spend > 0 and spend > avg_daily_spend * rules.spend_spike_multiplier and conversions == 0:
        alerts.append("spend_spike_no_order")
    if clicks >= rules.order_drop_clicks and conversions == 0:
        alerts.append("order_drop_after_clicks")
    if clicks >= rules.order_drop_clicks and no_paid_order and conversions > 0:
        alerts.append("platform_conversion_without_attributed_order")
    if attr_failed_payments > 0:
        alerts.append("payment_failed")
    if attr_checkout_attempts > 0 and no_paid_order:
        alerts.append("checkout_no_paid_order")
    if spend > 0 and clicks == 0:
        alerts.append("spend_no_click")
    if ctr >= 10 and clicks >= rules.order_drop_clicks and no_paid_order:
        alerts.append("high_ctr_no_paid_order")
    if ctr < rules.weak_ctr and int(item.get("impressions") or 0) >= rules.min_impressions_for_ctr:
        alerts.append("ctr_too_low")
    item["anomaly_alerts"] = ",".join(alerts)
    return alerts


def build_report(
    rows: list[dict[str, Any]],
    args: argparse.Namespace,
    order_rows: list[dict[str, Any]] | None = None,
    creative_tags: dict[str, dict[str, str]] | None = None,
) -> dict[str, Any]:
    order_rows = order_rows or []
    creative_tags = creative_tags or {}
    attribution_by_ad = summarize_orders_by_ad(order_rows) if order_rows else None
    totals = order_totals(order_rows) if order_rows else None
    effective_actual_orders = args.actual_orders if args.actual_orders is not None else (totals or {}).get("orders")
    derived_target_cpa = args.target_cpa
    if derived_target_cpa is None and args.avg_order_value is not None:
        if args.gross_margin is not None:
            derived_target_cpa = round(args.avg_order_value * args.gross_margin, 2)
        elif args.product_cost is not None:
            derived_target_cpa = round(args.avg_order_value - args.product_cost - args.shipping_cost, 2)
    rules = RuleConfig(
        target_cpa=derived_target_cpa,
        stop_spend=args.stop_spend,
        stop_clicks=args.stop_clicks,
        weak_ctr=args.weak_ctr,
        min_impressions_for_ctr=args.min_impressions_for_ctr,
        retest_min_ctr=args.retest_min_ctr,
        retest_max_cpc=args.retest_max_cpc,
        retest_min_clicks=args.retest_min_clicks,
        min_scale_orders=args.min_scale_orders,
        min_budget=args.min_budget,
        max_budget=args.max_budget,
        scale_budget_pct=args.scale_budget_pct,
        cpc_spike_multiplier=args.cpc_spike_multiplier,
        spend_spike_multiplier=args.spend_spike_multiplier,
        order_drop_clicks=args.order_drop_clicks,
    )
    for row in rows:
        enrich_creative_fields(row, creative_tags=creative_tags)

    by_day = group_rows(rows, ["Date"], attribution_by_ad, args.gross_margin)
    by_account = group_rows(rows, ["AdvertiserId", "AccountName"], attribution_by_ad, args.gross_margin)
    by_market = group_rows(rows, ["Market"], attribution_by_ad, args.gross_margin)
    by_product = group_rows(rows, ["Product"], attribution_by_ad, args.gross_margin)
    by_creative = group_rows(
        rows,
        ["creative_angle_group", "creative_angle", "material_type", "opening_hook", "Product"],
        attribution_by_ad,
        args.gross_margin,
    )
    by_campaign = group_rows(
        rows,
        ["AdvertiserId", "AccountName", "CampaignId", "CampaignName", "Product"],
        attribution_by_ad,
        args.gross_margin,
    )
    by_ad = group_rows(
        rows,
        [
            "AdvertiserId",
            "AccountName",
            "Market",
            "CampaignId",
            "CampaignName",
            "Product",
            "AdgroupId",
            "AdgroupName",
            "AdId",
            "AdName",
            "OperationStatus",
            "SecondaryStatus",
        ],
        attribution_by_ad,
        args.gross_margin,
    )

    active_ads = [item for item in by_ad if item["spend"] > 0 or item["clicks"] > 0 or item["impressions"] > 0]
    for item in active_ads:
        enrich_creative_fields(item, creative_tags=creative_tags)
        item["classification"] = classify_ad(item, effective_actual_orders, rules)
        action, reason = recommend_ad_action(item, rules)
        item["recommended_action"] = action
        item["action_reason"] = reason
        add_budget_and_action_fields(item, rules)
    for item in by_account:
        item["action"] = classify_group(item, effective_actual_orders, rules)
    for item in by_market:
        item["action"] = classify_group(item, effective_actual_orders, rules)
    for item in by_product:
        item["action"] = classify_group(item, effective_actual_orders, rules)
    for item in by_creative:
        item["action"] = classify_group(item, effective_actual_orders, rules)
    for item in by_campaign:
        item["action"] = classify_group(item, effective_actual_orders, rules)

    summary = metric(rows)
    add_business_metrics(summary, args, totals)
    summary["target_cpa"] = rules.target_cpa
    avg_daily_spend = summary["spend"] / max(1, len([day for day in by_day if day["spend"] > 0]))
    avg_cpc = summary.get("cpc")
    for item in active_ads:
        anomaly_alerts(item, avg_cpc, avg_daily_spend, rules)
    summary["anomaly_ads"] = len([item for item in active_ads if item.get("anomaly_alerts")])
    summary["active_ads"] = len(active_ads)
    summary["active_spend_ads"] = len([item for item in active_ads if item["spend"] > 0])
    summary["source_files"] = sorted({row["SourceFile"] for row in rows})
    summary["order_source_files"] = sorted({str(order.get("source_file")) for order in order_rows if order.get("source_file")})
    summary["attributed_order_ads"] = len(attribution_by_ad or {})

    spend_leak_labels = {
        "hard_stop_target_cpa",
        "hard_stop",
        "stop_loss",
        "post_click_problem",
        "weak_hook",
        "needs_order_check",
        "spend_leak_target_cpa",
        "likely_no_order_spend_leak",
    }
    order_signal_labels = {"order_signal_check", "platform_conversion_check"}
    payment_issue_labels = {"payment_failure", "checkout_no_order"}
    return {
        "summary": summary,
        "settings": rules.__dict__,
        "days": by_day,
        "accounts": [item for item in by_account if item["spend"] > 0 or item["clicks"] > 0 or item["impressions"] > 0],
        "markets": [item for item in by_market if item["spend"] > 0 or item["clicks"] > 0 or item["impressions"] > 0][:20],
        "products": [item for item in by_product if item["spend"] > 0][:20],
        "creative_angles": [item for item in by_creative if item["spend"] > 0][:20],
        "campaigns": [item for item in by_campaign if item["spend"] > 0][:20],
        "active_ads": active_ads,
        "spend_leaks": [item for item in active_ads if item["classification"] in spend_leak_labels][:30],
        "stop_ads": [item for item in active_ads if item["classification"] in spend_leak_labels][:30],
        "order_signal_ads": [item for item in active_ads if item["classification"] in order_signal_labels][:15],
        "payment_issue_ads": [item for item in active_ads if item["classification"] in payment_issue_labels][:15],
        "retest_candidates": [item for item in active_ads if item["classification"] == "small_retest_only"][:15],
        "tracking_mismatch": summary["tracking_mismatch"],
        "action_table": active_ads,
    }


def compact_text(value: Any, limit: int = 48) -> str:
    text = str(value or "")
    return text if len(text) <= limit else text[: max(0, limit - 3)] + "..."


def verdict(summary: dict[str, Any]) -> str:
    if summary.get("actual_orders") == 0:
        return "keep_paused"
    if summary.get("tracking_mismatch"):
        return "fix_tracking_before_scaling"
    if summary["conversions"] == 0:
        return "no_conversion_signal"
    return "review_before_scaling"


def print_markdown(report: dict[str, Any]) -> None:
    summary = report["summary"]
    print("# TikTok Ads Analysis")
    print()
    verdict_label = verdict(summary)
    verdict_text = {
        "keep_paused": "Verdict: keep paused. Spend and clicks have not produced real orders.",
        "fix_tracking_before_scaling": "Verdict: fix tracking/order reconciliation before scaling.",
        "no_conversion_signal": "Verdict: no proven conversion signal. Do not scale yet.",
        "review_before_scaling": "Verdict: review ad-level order attribution before scaling.",
    }[verdict_label]
    print(verdict_text)
    print()
    print(
        f"Spend: {summary['spend']} | Impressions: {summary['impressions']} | "
        f"Clicks: {summary['clicks']} | CTR: {summary['ctr_pct']}% | CPC: {summary['cpc']} | "
        f"Platform conversions: {summary['conversions']} | Actual orders: {summary.get('actual_orders')} | "
        f"Actual CPA: {summary.get('actual_cpa')}"
    )
    if summary.get("actual_revenue") is not None or summary.get("gross_margin") is not None:
        print(
            f"Revenue: {summary.get('actual_revenue')} | ROAS: {summary.get('roas')} | "
            f"Gross profit: {summary.get('gross_profit')} | Contribution profit: {summary.get('contribution_profit')} | "
            f"Break-even CPA: {summary.get('break_even_cpa')}"
        )
    if summary.get("target_cpa") is not None:
        print(f"Target/derived CPA: {summary.get('target_cpa')} | Profit status: {summary.get('profit_status')}")
    if summary.get("failed_payments") or summary.get("checkout_attempts"):
        print(
            f"Payment issues: failed payments {summary.get('failed_payments')} | "
            f"checkout attempts without paid order {summary.get('checkout_attempts')}"
        )
    if summary.get("tracking_mismatch"):
        print("Tracking warning: platform conversions do not match actual orders.")
    if summary.get("order_source_files"):
        print(f"Order attribution files: {len(summary['order_source_files'])} | Attributed ad IDs: {summary.get('attributed_order_ads')}")
    if summary.get("anomaly_ads"):
        print(f"Anomaly alerts: {summary.get('anomaly_ads')}")
    print()
    print("## Action Summary")
    action_counts: dict[str, int] = defaultdict(int)
    for ad in report["action_table"]:
        action_counts[str(ad.get("recommended_action") or "watch")] += 1
    for action, count in sorted(action_counts.items()):
        print(f"- {action}: {count}")
    print()
    print("## Creative Angles")
    for creative in report["creative_angles"][:8]:
        print(
            f"- {compact_text(creative['creative_angle_group'], 22)} / {compact_text(creative['creative_angle'], 22)} | "
            f"{compact_text(creative['material_type'], 10)} | {compact_text(creative['opening_hook'], 18)} | "
            f"spend {creative['spend']}, clicks {creative['clicks']}, CTR {creative['ctr_pct']}%, "
            f"CPC {creative['cpc']}, orders {creative.get('attributed_orders', creative['conversions'])} | {creative['action']}"
        )
    print()
    print("## Daily Trend")
    for day_item in sorted(report["days"], key=lambda item: item["Date"]):
        print(
            f"- {day_item['Date']}: spend {day_item['spend']}, clicks {day_item['clicks']}, "
            f"CTR {day_item['ctr_pct']}%, CPC {day_item['cpc']}, conversions {day_item['conversions']}"
        )
    print()
    print("## Accounts")
    for account in report["accounts"][:8]:
        print(
            f"- {account['AdvertiserId']} | {compact_text(account['AccountName'])}: spend {account['spend']}, clicks {account['clicks']}, "
            f"CTR {account['ctr_pct']}%, CPC {account['cpc']}, conversions {account['conversions']} | {account['action']}"
        )
    print()
    print("## Markets")
    for market in report["markets"][:8]:
        print(
            f"- {market['Market']}: spend {market['spend']}, clicks {market['clicks']}, "
            f"CTR {market['ctr_pct']}%, CPC {market['cpc']}, conversions {market['conversions']} | {market['action']}"
        )
    print()
    print("## Products")
    for product in report["products"][:8]:
        print(
            f"- {compact_text(product['Product'])}: spend {product['spend']}, clicks {product['clicks']}, "
            f"CTR {product['ctr_pct']}%, CPC {product['cpc']}, conversions {product['conversions']} | {product['action']}"
        )
    print()
    print("## Order Signal Ads")
    for ad in report["order_signal_ads"][:10]:
        print(
            f"- {ad['AdId']} | {ad['Market']} | {compact_text(ad['Product'], 28)} | spend {ad['spend']}, "
            f"clicks {ad['clicks']}, CTR {ad['ctr_pct']}%, CPC {ad['cpc']}, "
            f"conversions {ad['conversions']}, attr orders {ad.get('attributed_orders')}, "
            f"CPA {ad.get('attributed_cpa')}, ROAS {ad.get('attributed_roas')} | {ad.get('recommended_action')} | "
            f"{ad.get('action_label_cn')} | {ad.get('budget_note')}"
        )
    if report["payment_issue_ads"]:
        print()
        print("## Payment Or Checkout Issue Ads")
        for ad in report["payment_issue_ads"][:10]:
            print(
                f"- {ad['AdId']} | {ad['Market']} | {compact_text(ad['Product'], 28)} | spend {ad['spend']}, "
                f"clicks {ad['clicks']}, failed payments {ad.get('attributed_failed_payments')}, "
                f"checkout attempts {ad.get('attributed_checkout_attempts')} | {ad.get('recommended_action')} | "
                f"{ad.get('budget_note')} | alerts {ad.get('anomaly_alerts')}"
            )
    print()
    print("## Stop Or Rebuild Ads")
    for ad in report["stop_ads"][:12]:
        print(
            f"- {ad['AdId']} | {ad['Market']} | {compact_text(ad['Product'], 28)} | spend {ad['spend']}, "
            f"clicks {ad['clicks']}, CTR {ad['ctr_pct']}%, CPC {ad['cpc']}, "
            f"conversions {ad['conversions']} | {ad.get('recommended_action')} | {ad.get('action_label_cn')} | "
            f"{ad.get('action_reason')} | budget {ad.get('tomorrow_budget_suggestion')} | alerts {ad.get('anomaly_alerts')}"
        )
    if report["retest_candidates"]:
        print()
        print("## Retest Candidates")
        for ad in report["retest_candidates"][:10]:
            print(
                f"- {ad['AdId']} | {ad['Market']} | {compact_text(ad['Product'], 28)} | spend {ad['spend']}, "
                f"clicks {ad['clicks']}, CTR {ad['ctr_pct']}%, CPC {ad['cpc']} | {ad.get('action_reason')} | "
                f"budget {ad.get('tomorrow_budget_suggestion')} | alerts {ad.get('anomaly_alerts')}"
            )
    print()
    print("## Action Table")
    for ad in report["action_table"][:12]:
        print(
            f"- {ad['AdId']} | {compact_text(ad['material_name'], 20)} | {ad['material_type']} | {ad['creative_angle_group']} / {ad['opening_hook']} | "
            f"{ad['action_label_cn']} | tomorrow {ad['tomorrow_budget_suggestion']} | "
            f"stop_clicks@{ad['stop_after_clicks_without_order']} | stop_spend@{ad['stop_after_spend_without_order']} | "
            f"scale: {ad['scale_condition']} | alerts {ad['anomaly_alerts']}"
        )


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze TikTok ad export CSV files.")
    source = parser.add_argument_group("data source")
    source.add_argument("--csv", nargs="*", default=[], help="CSV file path(s).")
    source.add_argument("--glob", default="", help="Glob pattern for CSV files.")
    source.add_argument("--days", type=int, default=0, help="Analyze the latest N days from local exports.")
    source.add_argument("--start-date", default="", help="Start date YYYY-MM-DD.")
    source.add_argument("--end-date", default="", help="End date YYYY-MM-DD. Defaults to today for --days.")
    source.add_argument("--refresh", action="store_true", help="Run the local TikTok exporter for each daily file first.")
    source.add_argument("--include-full-range", action="store_true", help="Also include/export the full range CSV.")
    source.add_argument("--exporter", default=str(DEFAULT_EXPORTER), help="Path to tiktok_export_all_ads.ps1.")
    source.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR), help="Directory containing TikTok export CSVs.")

    business = parser.add_argument_group("business metrics")
    business.add_argument("--actual-orders", type=float, default=None, help="Real store order count for the window.")
    business.add_argument("--actual-revenue", type=float, default=None, help="Real revenue for the window.")
    business.add_argument("--orders-csv", nargs="*", default=[], help="Optional order export CSV(s) with ad_id and revenue columns for ad-level attribution.")
    business.add_argument("--creative-tags-csv", nargs="*", default=[], help="Optional creative tags CSV(s) with ad_id, material_name, material_type, creative_angle, opening_hook, and video_url.")
    business.add_argument("--avg-order-value", type=float, default=None, help="Average order value. Used to derive revenue and break-even CPA.")
    business.add_argument("--product-cost", type=float, default=None, help="Per-order product cost. Used with AOV to estimate margin.")
    business.add_argument("--shipping-cost", type=float, default=0.0, help="Per-order shipping/fulfillment cost used with product cost.")
    business.add_argument("--gross-margin", type=float, default=None, help="Gross margin as decimal, e.g. 0.55.")
    business.add_argument("--target-cpa", type=float, default=None, help="Target or break-even CPA for hard-stop logic.")

    rules = parser.add_argument_group("rules")
    rules.add_argument("--stop-spend", type=float, default=5.0, help="Stop-loss spend threshold when actual orders are zero.")
    rules.add_argument("--stop-clicks", type=int, default=30, help="Stop-loss click threshold when actual orders are zero.")
    rules.add_argument("--weak-ctr", type=float, default=0.7, help="Weak hook CTR threshold in percent.")
    rules.add_argument("--min-impressions-for-ctr", type=int, default=1000, help="Minimum impressions before weak CTR judgment.")
    rules.add_argument("--retest-min-ctr", type=float, default=1.5, help="Minimum CTR percent for small retest candidates.")
    rules.add_argument("--retest-max-cpc", type=float, default=0.35, help="Maximum CPC for small retest candidates.")
    rules.add_argument("--retest-min-clicks", type=int, default=3, help="Minimum clicks for small retest candidates.")
    rules.add_argument("--min-scale-orders", type=int, default=5, help="Minimum attributed orders before a scale_carefully action.")
    rules.add_argument("--min-budget", type=float, default=1.0, help="Minimum recommended budget for keep/test items.")
    rules.add_argument("--max-budget", type=float, default=None, help="Optional maximum recommended budget cap.")
    rules.add_argument("--scale-budget-pct", type=float, default=0.25, help="Budget increase pct for scale_observe.")
    rules.add_argument("--cpc-spike-multiplier", type=float, default=1.5, help="Alert when CPC exceeds this multiplier of account average.")
    rules.add_argument("--spend-spike-multiplier", type=float, default=1.5, help="Alert when spend exceeds this multiplier of average daily spend without orders.")
    rules.add_argument("--order-drop-clicks", type=int, default=20, help="Alert when clicks reach this threshold without orders.")

    output = parser.add_argument_group("output")
    output.add_argument("--json-out", default="", help="Optional path for JSON output.")
    output.add_argument("--classified-csv-out", default="", help="Optional CSV output for classified active ads.")
    output.add_argument("--markdown", action="store_true", help="Print Markdown instead of JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = collect_paths(args)
    rows = read_rows(paths)
    order_rows = read_order_rows(args.orders_csv)
    creative_tags = read_creative_tags(args.creative_tags_csv)
    report = build_report(rows, args, order_rows, creative_tags)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.classified_csv_out:
        fields = [
            "AdvertiserId",
            "AccountName",
            "Market",
            "CampaignId",
            "CampaignName",
            "Product",
            "AdgroupId",
            "AdgroupName",
            "AdId",
            "AdName",
            "material_name",
            "material_type",
            "creative_angle",
            "creative_angle_group",
            "opening_hook",
            "video_url",
            "creator_tag",
            "creative_note",
            "spend",
            "impressions",
            "clicks",
            "conversions",
            "ctr_pct",
            "cpc",
            "cpm",
            "platform_cpa",
            "attributed_orders",
            "attributed_revenue",
            "attributed_failed_payments",
            "attributed_checkout_attempts",
            "attributed_cpa",
            "attributed_roas",
            "attributed_gross_profit",
            "attributed_contribution_profit",
            "classification",
            "recommended_action",
            "action_label_cn",
            "action_reason",
            "tomorrow_budget_suggestion",
            "max_test_budget",
            "stop_after_clicks_without_order",
            "stop_after_spend_without_order",
            "scale_condition",
            "budget_note",
            "anomaly_alerts",
            "OperationStatus",
            "SecondaryStatus",
        ]
        write_csv(Path(args.classified_csv_out), report["active_ads"], fields)

    if args.markdown:
        print_markdown(report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
