from __future__ import annotations

import csv
import datetime as dt
import importlib.util
import json
import os
import re
import subprocess
import sys
import threading
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

PACKAGE_DIR = Path(__file__).resolve().parent


def _configured_path(env_name: str, default: Path) -> Path:
    """Resolve a deployment-specific path, preferring the environment."""
    value = (os.environ.get(env_name) or "").strip()
    return Path(value) if value else default


# The puller and its token file live outside this repository. Point these at
# your own checkout instead of relying on a machine-specific default.
SKILL_ROOT = _configured_path("FB_ADS_SKILL_ROOT", PACKAGE_DIR.parent)
PULL_SCRIPT = _configured_path(
    "FB_ADS_PULL_SCRIPT", SKILL_ROOT / "scripts" / "fb_pull_report.py"
)
TOKEN_PATH = _configured_path("FB_ADS_TOKEN_PATH", PACKAGE_DIR / "fb_token.txt")
DEFAULT_REPORT_ROOT = PACKAGE_DIR / "reports" / "fb_pull_report"
REPORT_ROOT = _configured_path("FB_ADS_REPORT_ROOT", DEFAULT_REPORT_ROOT)
DAILY_ANALYSIS_PATH = PACKAGE_DIR / "reports" / "daily" / "latest.json"
SUPPORTED_RANGES = {"today", "yesterday", "last_7d", "last_30d", "last_90d", "maximum"}
DEFAULT_RANGE = "last_7d"
DEFAULT_PULL_TIMEOUT_SECONDS = int(os.environ.get("FB_ADS_PULL_TIMEOUT_SECONDS", "1800"))
PULL_JOB_LOCK = threading.Lock()
PULL_JOBS: dict[str, dict[str, Any]] = {}
API_SETTINGS = {
    "apiVersion": "v22.0",
    "actionReportTime": "conversion",
    "useUnifiedAttributionSetting": True,
    "dateSource": "date_preset",
    "timezone": "Asia/Shanghai",
    "levels": ["account", "campaign", "adset", "ad"],
    "purchasePolicy": "canonical_action_alias",
}


def is_complete_report_dir(path: Path) -> bool:
    return (
        path.is_dir()
        and (path / "summary.json").exists()
        and (path / "account_summary.csv").exists()
    )


def latest_report_dir(root: Path = REPORT_ROOT) -> Path:
    if not root.exists():
        raise FileNotFoundError(f"report root not found: {root}")
    candidates = [p for p in root.iterdir() if is_complete_report_dir(p)]
    if not candidates:
        raise FileNotFoundError(f"no Facebook report found under: {root}")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def report_dirs(root: Path = REPORT_ROOT) -> list[Path]:
    if not root.exists():
        return []
    return sorted([p for p in root.iterdir() if is_complete_report_dir(p)], key=lambda p: p.stat().st_mtime, reverse=True)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as fp:
        return list(csv.DictReader(fp))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_daily_analysis() -> dict[str, Any]:
    if not DAILY_ANALYSIS_PATH.exists():
        return {}
    data = read_json(DAILY_ANALYSIS_PATH)
    return {
        "generatedAt": data.get("generatedAt"),
        "ranges": data.get("ranges") or [],
        "comparisons": data.get("comparisons") or {},
        "reportPath": str(DAILY_ANALYSIS_PATH),
    }


def dependency_status() -> dict[str, Any]:
    packages = ["requests"]
    return {
        "python": sys.executable,
        "packages": {name: importlib.util.find_spec(name) is not None for name in packages},
    }


def report_freshness(report_dir: Path, generated_at: str | None, source_mode: str) -> dict[str, Any]:
    now = dt.datetime.now()
    parsed = parse_datetime(generated_at)
    fallback = dt.datetime.fromtimestamp(report_dir.stat().st_mtime) if report_dir.exists() else None
    timestamp = parsed or fallback
    age_minutes = round((now - timestamp).total_seconds() / 60, 1) if timestamp else None
    is_stale = bool(age_minutes is not None and age_minutes > 90 and source_mode == "cache")
    return {
        "generatedAt": generated_at or (fallback.isoformat(timespec="seconds") if fallback else ""),
        "ageMinutes": age_minutes,
        "isStale": is_stale,
        "mode": source_mode,
        "checkedAt": now.isoformat(timespec="seconds"),
    }


def parse_datetime(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    text = str(value).strip()
    for candidate in (text, text.replace("Z", "+00:00")):
        try:
            parsed = dt.datetime.fromisoformat(candidate)
            if parsed.tzinfo:
                return parsed.astimezone().replace(tzinfo=None)
            return parsed
        except ValueError:
            continue
    return None


def number(value: Any) -> float:
    try:
        if value in (None, ""):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def integer(value: Any) -> int:
    return int(round(number(value)))


def pct(part: float, whole: float) -> float:
    return (part / whole * 100) if whole else 0.0


def sanitize_range_name(value: str | None) -> str:
    name = (value or "").strip()
    if name in SUPPORTED_RANGES:
        return name
    return DEFAULT_RANGE


def human_range_name(value: str | None) -> str:
    return {
        "today": "今天",
        "yesterday": "昨天",
        "last_7d": "近 7 天",
        "last_30d": "近 30 天",
        "last_90d": "近 90 天",
        "maximum": "最大范围",
    }.get(sanitize_range_name(value), value or DEFAULT_RANGE)


def report_meta_path(report_dir: Path) -> Path:
    return report_dir / "meta.json"


def read_report_meta(report_dir: Path) -> dict[str, Any]:
    return read_json(report_meta_path(report_dir))


def write_report_meta(report_dir: Path, meta: dict[str, Any]) -> None:
    write_json(report_meta_path(report_dir), meta)


def infer_report_range(report_dir: Path) -> str:
    meta = read_report_meta(report_dir)
    if meta.get("requestedRange"):
        return str(meta.get("requestedRange"))
    account_summary = read_csv(report_dir / "account_summary.csv")
    presets = {str(row.get("preset") or "").strip() for row in account_summary if row.get("preset")}
    if len(presets) == 1:
        return presets.pop()
    return DEFAULT_RANGE


def cached_report_dir(requested_range: str) -> Path | None:
    requested_range = sanitize_range_name(requested_range)
    for report_dir in report_dirs():
        meta = read_report_meta(report_dir)
        if meta.get("requestedRange") == requested_range:
            return report_dir
        if requested_range in SUPPORTED_RANGES:
            account_summary = read_csv(report_dir / "account_summary.csv")
            if account_summary:
                presets = {str(row.get("preset") or "").strip() for row in account_summary if row.get("preset")}
                if presets == {requested_range}:
                    return report_dir
    return None


def run_skill_pull(requested_range: str, timeout_seconds: int | None = None, levels: str | None = None) -> Path:
    requested_range = sanitize_range_name(requested_range)
    if not TOKEN_PATH.exists():
        raise FileNotFoundError(f"token file not found: {TOKEN_PATH}")
    if not PULL_SCRIPT.exists():
        raise FileNotFoundError(f"pull script not found: {PULL_SCRIPT}")
    cmd = [
        sys.executable,
        str(PULL_SCRIPT),
        "--token-path",
        str(TOKEN_PATH),
        "--date-preset",
        requested_range,
        "--no-auto-backfill",
        "--output-dir",
        str(REPORT_ROOT),
        "--levels",
        levels or "account,campaign,adset,ad",
    ]
    result = subprocess.run(
        cmd,
        cwd=str(SKILL_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout_seconds or DEFAULT_PULL_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        stderr = redact_token_text(result.stderr or "")
        stdout = redact_token_text(result.stdout or "")
        message = stderr or stdout or f"fb pull failed with exit code {result.returncode}"
        raise RuntimeError(message.strip())

    report_dir = latest_report_dir()
    write_report_meta(
        report_dir,
        {
            "requestedRange": requested_range,
            "requestedAt": dt.datetime.now().isoformat(timespec="seconds"),
            "source": "facebook_bm_ads",
        },
    )
    return report_dir


def pull_job_snapshot(requested_range: str) -> dict[str, Any] | None:
    requested_range = sanitize_range_name(requested_range)
    with PULL_JOB_LOCK:
        job = PULL_JOBS.get(requested_range)
        return dict(job) if job else None


def start_background_pull(requested_range: str) -> dict[str, Any]:
    requested_range = sanitize_range_name(requested_range)
    now = dt.datetime.now().isoformat(timespec="seconds")
    with PULL_JOB_LOCK:
        existing = PULL_JOBS.get(requested_range)
        if existing and existing.get("status") == "running":
            return dict(existing)

        job = {
            "range": requested_range,
            "status": "running",
            "startedAt": now,
            "completedAt": "",
            "reportName": "",
            "reportDir": "",
            "error": "",
        }
        PULL_JOBS[requested_range] = job

    def worker() -> None:
        try:
            report_dir = run_skill_pull(requested_range)
            update = {
                "status": "completed",
                "completedAt": dt.datetime.now().isoformat(timespec="seconds"),
                "reportName": report_dir.name,
                "reportDir": str(report_dir),
                "error": "",
            }
        except Exception as exc:
            update = {
                "status": "failed",
                "completedAt": dt.datetime.now().isoformat(timespec="seconds"),
                "error": redact_token_text(str(exc)),
            }
        with PULL_JOB_LOCK:
            current = PULL_JOBS.setdefault(requested_range, {"range": requested_range})
            current.update(update)

    thread = threading.Thread(target=worker, name=f"fb-pull-{requested_range}", daemon=True)
    thread.start()
    return pull_job_snapshot(requested_range) or job


TOKEN_PATTERN = re.compile(
    r"(?i)\b(access_token\s*[:=]\s*)"
    r"(?:\"[^\"]*\"|'[^']*'|[^\s&\"'\)\],;]+)"
)


def redact_token_text(text: str) -> str:
    """Replace the value of any access_token occurrence, not just its prefix.

    Provider errors echo the failing request, so the secret itself has to be
    stripped before the message reaches a log or an API response.
    """
    cleaned = TOKEN_PATTERN.sub(r"\1<redacted>", str(text))
    return re.sub(r"(?i)\b(EAA[A-Za-z0-9]{20,})", "<redacted>", cleaned)


def read_access_token() -> str:
    if not TOKEN_PATH.exists():
        raise FileNotFoundError(f"token file not found: {TOKEN_PATH}")
    text = TOKEN_PATH.read_text(encoding="utf-8-sig").strip()
    if not text:
        raise ValueError("token file is empty")
    if text.startswith("{"):
        data = json.loads(text)
        token = str(data.get("access_token") or data.get("token") or "").strip()
        if token:
            return token
    if "access_token=" in text:
        parsed = parse_qs(text.lstrip("?"))
        token = (parsed.get("access_token") or [""])[0].strip()
        if token:
            return token
    return text.splitlines()[0].strip()


def normalize_campaign_ids(campaign_ids: Any) -> list[str]:
    if not isinstance(campaign_ids, list):
        raise ValueError("campaignIds must be a list")
    normalized: list[str] = []
    for raw_id in campaign_ids:
        campaign_id = str(raw_id or "").strip()
        if not campaign_id:
            continue
        if not campaign_id.isdigit():
            raise ValueError(f"invalid campaign id: {campaign_id}")
        if campaign_id not in normalized:
            normalized.append(campaign_id)
    if not normalized:
        raise ValueError("no campaign ids provided")
    if len(normalized) > 20:
        raise ValueError("最多一次关闭 20 个系列，请分批操作")
    return normalized


def pause_campaigns(campaign_ids: Any, confirm: str | None = None) -> dict[str, Any]:
    if confirm != "PAUSE_CAMPAIGNS":
        raise ValueError("missing confirmation for pausing campaigns")

    import requests

    token = read_access_token()
    ids = normalize_campaign_ids(campaign_ids)
    api_version = API_SETTINGS["apiVersion"]
    results: list[dict[str, Any]] = []

    for campaign_id in ids:
        try:
            response = requests.post(
                f"https://graph.facebook.com/{api_version}/{campaign_id}",
                data={"access_token": token, "status": "PAUSED"},
                timeout=30,
            )
            try:
                data = response.json()
            except ValueError:
                data = {}

            error = data.get("error") if isinstance(data, dict) else None
            if not response.ok or error:
                message = ""
                if isinstance(error, dict):
                    message = str(error.get("message") or error.get("error_user_msg") or "")
                message = message or response.reason or "Facebook API request failed"
                results.append(
                    {
                        "campaignId": campaign_id,
                        "ok": False,
                        "error": redact_token_text(message),
                    }
                )
                continue

            results.append({"campaignId": campaign_id, "ok": True})
        except requests.RequestException as exc:
            results.append(
                {
                    "campaignId": campaign_id,
                    "ok": False,
                    "error": redact_token_text(str(exc)),
                }
            )

    paused_count = len([item for item in results if item.get("ok")])
    failed_count = len(results) - paused_count
    return {
        "ok": True,
        "status": "PAUSED",
        "pausedCount": paused_count,
        "failedCount": failed_count,
        "results": results,
    }


def copy_campaigns(
    campaign_ids: Any,
    confirm: str | None = None,
    rename_suffix: str | None = None,
    status_option: str = "PAUSED",
    deep_copy: bool = True,
) -> dict[str, Any]:
    if confirm != "COPY_CAMPAIGNS":
        raise ValueError("missing confirmation for copying campaigns")

    import requests

    token = read_access_token()
    ids = normalize_campaign_ids(campaign_ids)
    if len(ids) > 10:
        raise ValueError("最多一次复制 10 个系列，请分批操作")

    normalized_status = str(status_option or "PAUSED").strip().upper()
    if normalized_status not in {"PAUSED", "ACTIVE", "INHERITED_FROM_SOURCE"}:
        raise ValueError("invalid status option")

    suffix = str(rename_suffix or "").strip()
    if len(suffix) > 80:
        raise ValueError("rename suffix is too long")

    api_version = API_SETTINGS["apiVersion"]
    results: list[dict[str, Any]] = []

    for campaign_id in ids:
        data: dict[str, Any] = {
            "access_token": token,
            "status_option": normalized_status,
            "deep_copy": "true" if deep_copy else "false",
        }
        if suffix:
            data["rename_options"] = json.dumps({"rename_suffix": suffix}, ensure_ascii=False)

        try:
            response = requests.post(
                f"https://graph.facebook.com/{api_version}/{campaign_id}/copies",
                data=data,
                timeout=60,
            )
            try:
                payload = response.json()
            except ValueError:
                payload = {}

            error = payload.get("error") if isinstance(payload, dict) else None
            if not response.ok or error:
                message = ""
                if isinstance(error, dict):
                    message = str(error.get("message") or error.get("error_user_msg") or "")
                message = message or response.reason or "Facebook API request failed"
                results.append(
                    {
                        "campaignId": campaign_id,
                        "ok": False,
                        "error": redact_token_text(message),
                    }
                )
                continue

            copied_id = ""
            if isinstance(payload, dict):
                copied_id = str(payload.get("copied_campaign_id") or payload.get("id") or "").strip()
            results.append({"campaignId": campaign_id, "copiedCampaignId": copied_id, "ok": True})
        except requests.RequestException as exc:
            results.append(
                {
                    "campaignId": campaign_id,
                    "ok": False,
                    "error": redact_token_text(str(exc)),
                }
            )

    copied_count = len([item for item in results if item.get("ok")])
    failed_count = len(results) - copied_count
    return {
        "ok": True,
        "statusOption": normalized_status,
        "deepCopy": bool(deep_copy),
        "copiedCount": copied_count,
        "failedCount": failed_count,
        "results": results,
    }


def with_numbers(row: dict[str, Any]) -> dict[str, Any]:
    numeric_keys = [
        "spend",
        "impressions",
        "reach",
        "frequency",
        "clicks",
        "inline_link_clicks",
        "ctr",
        "cpc",
        "cpm",
        "purchase",
        "purchase_value",
        "roas",
        "cpa",
        "add_to_cart",
        "checkout",
        "add_payment_info",
        "view_content",
        "landing_page_view",
        "warning",
        "opportunity",
        "critical",
        "info",
    ]
    out = dict(row)
    for key in numeric_keys:
        if key in out:
            out[key] = number(out.get(key))
    return out


def account_dirs(report_dir: Path) -> list[Path]:
    return sorted([p for p in report_dir.iterdir() if p.is_dir() and p.name.startswith("act_")])


def load_level_rows(report_dir: Path, level: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for account_dir in account_dirs(report_dir):
        rows.extend(with_numbers(row) for row in read_csv(account_dir / f"{level}.csv"))
    return rows


def creative_family(ad_name: str) -> str:
    parts = [part.strip() for part in str(ad_name or "").split("#") if part.strip()]
    if len(parts) >= 2:
        return "#".join(parts[:2])
    return str(ad_name or "未命名素材")[:48]


def action_for_ad(row: dict[str, Any]) -> str:
    spend = number(row.get("spend"))
    roas = number(row.get("roas"))
    purchase = number(row.get("purchase"))
    atc = number(row.get("add_to_cart"))
    clicks = max(number(row.get("inline_link_clicks")), number(row.get("clicks")))
    if purchase >= 2 and roas >= 3:
        return "scale"
    if purchase == 0 and atc == 0 and clicks >= 20:
        return "fix_landing"
    if purchase >= 1 and spend >= 20 and 0 < roas < 2.5:
        return "reduce"
    if spend == 0:
        return "idle"
    return "watch"


def action_label(action: str) -> str:
    return {
        "scale": "放量",
        "fix_landing": "查承接",
        "reduce": "降预算",
        "idle": "无消耗",
        "watch": "观察",
    }.get(action, "观察")


def action_tone(action: str) -> str:
    return {
        "scale": "good",
        "fix_landing": "bad",
        "reduce": "warn",
        "idle": "muted",
        "watch": "info",
    }.get(action, "info")


def normalize_ad(row: dict[str, Any]) -> dict[str, Any]:
    out = with_numbers(row)
    action = action_for_ad(out)
    out["family"] = creative_family(str(out.get("ad_name") or ""))
    out["action"] = action
    out["action_label"] = action_label(action)
    out["tone"] = action_tone(action)
    out["link_clicks"] = max(number(out.get("inline_link_clicks")), number(out.get("clicks")))
    out["atc_rate"] = pct(number(out.get("add_to_cart")), out["link_clicks"])
    out["purchase_rate"] = pct(number(out.get("purchase")), out["link_clicks"])
    return out


def aggregate(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for row in rows:
        label = str(row.get(key) or "-")
        bucket = buckets.setdefault(
            label,
            {
                "name": label,
                "spend": 0.0,
                "impressions": 0.0,
                "clicks": 0.0,
                "link_clicks": 0.0,
                "purchase": 0.0,
                "purchase_value": 0.0,
                "add_to_cart": 0.0,
                "ads": 0,
            },
        )
        bucket["spend"] += number(row.get("spend"))
        bucket["impressions"] += number(row.get("impressions"))
        bucket["clicks"] += number(row.get("clicks"))
        bucket["link_clicks"] += number(row.get("link_clicks"))
        bucket["purchase"] += number(row.get("purchase"))
        bucket["purchase_value"] += number(row.get("purchase_value"))
        bucket["add_to_cart"] += number(row.get("add_to_cart"))
        bucket["ads"] += 1
    for bucket in buckets.values():
        bucket["roas"] = bucket["purchase_value"] / bucket["spend"] if bucket["spend"] else 0.0
        bucket["cpa"] = bucket["spend"] / bucket["purchase"] if bucket["purchase"] else 0.0
        bucket["ctr"] = pct(bucket["clicks"], bucket["impressions"])
    return sorted(buckets.values(), key=lambda item: item["spend"], reverse=True)


def enrich_findings(findings: list[dict[str, Any]], ads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ads_by_id = {str(row.get("ad_id")): row for row in ads if row.get("ad_id")}
    enriched: list[dict[str, Any]] = []
    for finding in findings:
        out = dict(finding)
        ad = ads_by_id.get(str(finding.get("entity_id")))
        if ad:
            out.update(
                {
                    "spend": number(ad.get("spend")),
                    "roas": number(ad.get("roas")),
                    "purchase": number(ad.get("purchase")),
                    "clicks": number(ad.get("clicks")),
                    "add_to_cart": number(ad.get("add_to_cart")),
                    "family": ad.get("family"),
                    "action": ad.get("action"),
                    "tone": ad.get("tone"),
                }
            )
        else:
            out.update({"spend": 0, "roas": 0, "purchase": 0, "clicks": 0, "add_to_cart": 0})
        enriched.append(out)
    level_weight = {"critical": 4, "warning": 3, "opportunity": 2, "info": 1}
    return sorted(
        enriched,
        key=lambda item: (level_weight.get(str(item.get("level")), 0), number(item.get("spend"))),
        reverse=True,
    )


def build_funnel(ads: list[dict[str, Any]], accounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    impressions = sum(number(row.get("impressions")) for row in ads) or sum(number(row.get("impressions")) for row in accounts)
    clicks = sum(max(number(row.get("inline_link_clicks")), number(row.get("clicks"))) for row in ads) or sum(number(row.get("clicks")) for row in accounts)
    atc = sum(number(row.get("add_to_cart")) for row in ads)
    checkout = sum(number(row.get("checkout")) for row in ads)
    purchase = sum(number(row.get("purchase")) for row in ads) or sum(number(row.get("purchase")) for row in accounts)
    steps = [
        ("展示", impressions),
        ("点击", clicks),
        ("加购", atc),
        ("结账", checkout),
        ("购买", purchase),
    ]
    top = max([value for _, value in steps] or [1])
    return [
        {
            "label": label,
            "value": value,
            "share": pct(value, top),
            "previous_rate": pct(value, steps[index - 1][1]) if index else 100,
        }
        for index, (label, value) in enumerate(steps)
    ]


def summarize(accounts: list[dict[str, Any]], ads: list[dict[str, Any]], findings: list[dict[str, Any]]) -> dict[str, Any]:
    spend = sum(number(row.get("spend")) for row in accounts)
    impressions = sum(number(row.get("impressions")) for row in accounts)
    clicks = sum(number(row.get("clicks")) for row in accounts)
    purchase = sum(number(row.get("purchase")) for row in accounts)
    purchase_value = sum(number(row.get("purchase_value")) for row in ads)
    if not purchase_value:
        purchase_value = sum(number(row.get("roas")) * number(row.get("spend")) for row in accounts)
    level_counts = Counter(str(row.get("level") or "info") for row in findings)
    action_counts = Counter(str(row.get("action") or "watch") for row in ads)
    return {
        "spend": spend,
        "impressions": impressions,
        "clicks": clicks,
        "purchase": purchase,
        "purchase_value": purchase_value,
        "roas": purchase_value / spend if spend else 0.0,
        "cpa": spend / purchase if purchase else 0.0,
        "ctr": pct(clicks, impressions),
        "cpc": spend / clicks if clicks else 0.0,
        "accounts": len(accounts),
        "ads": len(ads),
        "critical": level_counts.get("critical", 0),
        "warning": level_counts.get("warning", 0),
        "opportunity": level_counts.get("opportunity", 0),
        "info": level_counts.get("info", 0),
        "scale": action_counts.get("scale", 0),
        "reduce": action_counts.get("reduce", 0),
        "fix_landing": action_counts.get("fix_landing", 0),
        "watch": action_counts.get("watch", 0),
    }


def build_dashboard_payload(
    report: str | None = None,
    range_name: str | None = None,
    refresh: bool = False,
    refresh_mode: str = "blocking",
) -> dict[str, Any]:
    report_dir: Path
    source_mode = "cache"
    source_warning = ""
    refresh_job: dict[str, Any] | None = None
    selected_range = sanitize_range_name(range_name)
    if report:
        report_dir = REPORT_ROOT / report
        if not is_complete_report_dir(report_dir):
            raise FileNotFoundError(f"report not found: {report_dir}")
        source_mode = "direct"
        selected_range = infer_report_range(report_dir)
    else:
        cached = cached_report_dir(selected_range)
        if refresh:
            if refresh_mode == "background" and cached:
                refresh_job = start_background_pull(selected_range)
                report_dir = cached
                source_mode = "cache_refreshing"
                source_warning = (
                    "\u5237\u65b0\u5df2\u5728\u540e\u53f0\u6267\u884c\uff0c"
                    "\u672c\u6b21\u5148\u4f7f\u7528\u6700\u8fd1\u5b8c\u6574\u62a5\u8868\u3002"
                )
            else:
                try:
                    report_dir = run_skill_pull(selected_range)
                    source_mode = "pulled"
                except Exception as exc:
                    if not cached:
                        raise
                    report_dir = cached
                    source_mode = "cache_fallback"
                    source_warning = (
                        "\u5237\u65b0\u5931\u8d25\uff0c"
                        "\u5df2\u4f7f\u7528\u6700\u8fd1\u5b8c\u6574\u62a5\u8868\uff1a"
                        f"{redact_token_text(str(exc))}"
                    )
        elif cached:
            report_dir = cached
        else:
            try:
                report_dir = run_skill_pull(selected_range)
                source_mode = "pulled"
            except Exception:
                fallback = latest_report_dir()
                if infer_report_range(fallback) != selected_range:
                    raise
                report_dir = fallback
                source_mode = "cache_fallback"
                source_warning = (
                    "\u672a\u80fd\u5237\u65b0\u62c9\u53d6\uff0c"
                    "\u5df2\u4f7f\u7528\u6700\u8fd1\u5b8c\u6574\u62a5\u8868\u3002"
                )

    raw_summary = read_json(report_dir / "summary.json")
    account_summary = [with_numbers(row) for row in read_csv(report_dir / "account_summary.csv")]
    if not account_summary:
        account_summary = load_level_rows(report_dir, "account")
    ads = [normalize_ad(row) for row in load_level_rows(report_dir, "ad")]
    findings = enrich_findings([dict(row) for row in read_csv(report_dir / "findings.csv")], ads)
    if not findings:
        findings = enrich_findings(raw_summary.get("findings", []), ads)

    summary = summarize(account_summary, ads, findings)
    families = aggregate(ads, "family")
    campaigns = aggregate(ads, "campaign_name")
    adsets = aggregate(ads, "adset_name")
    accounts = sorted(account_summary, key=lambda row: number(row.get("spend")), reverse=True)

    top_scale = sorted(
        [row for row in ads if row.get("action") == "scale"],
        key=lambda row: (number(row.get("purchase")), number(row.get("roas"))),
        reverse=True,
    )[:24]
    top_risk = sorted(
        [row for row in ads if row.get("action") == "reduce"],
        key=lambda row: number(row.get("spend")),
        reverse=True,
    )[:24]
    no_atc = sorted(
        [row for row in ads if row.get("action") == "fix_landing"],
        key=lambda row: number(row.get("link_clicks")),
        reverse=True,
    )[:24]

    category_counts = Counter(str(item.get("category") or "-") for item in findings)
    level_counts = Counter(str(item.get("level") or "info") for item in findings)

    generated_at = raw_summary.get("generated_at", "")
    return {
        "source": {
            "reportDir": str(report_dir),
            "reportName": report_dir.name,
            "generatedAt": generated_at,
            "apiVersion": raw_summary.get("api_version", ""),
            "range": selected_range if selected_range else infer_report_range(report_dir),
            "rangeLabel": human_range_name(selected_range if selected_range else infer_report_range(report_dir)),
            "sourceMode": source_mode,
            "warning": source_warning,
            "refreshJob": refresh_job or pull_job_snapshot(selected_range),
            "availableRanges": available_ranges(),
            "freshness": report_freshness(report_dir, generated_at, source_mode),
        },
        "apiSettings": API_SETTINGS,
        "system": {
            "dependencies": dependency_status(),
            "tokenConfigured": TOKEN_PATH.exists(),
            "pullScriptConfigured": PULL_SCRIPT.exists(),
            "accountCount": len(accounts),
            "activeAccountCount": len([row for row in accounts if number(row.get("spend")) > 0 or number(row.get("purchase")) > 0]),
        },
        "summary": summary,
        "counts": {
            "levels": dict(level_counts),
            "categories": dict(category_counts),
        },
        "funnel": build_funnel(ads, account_summary),
        "tables": {
            "accounts": accounts,
            "families": families[:80],
            "campaigns": campaigns[:80],
            "adsets": adsets[:80],
            "ads": sorted(ads, key=lambda row: number(row.get("spend")), reverse=True)[:500],
            "findings": findings[:300],
        },
        "boards": {
            "scale": top_scale,
            "risk": top_risk,
            "noAtc": no_atc,
            "warnings": [item for item in findings if item.get("level") == "warning"][:120],
            "opportunities": [item for item in findings if item.get("level") == "opportunity"][:120],
        },
        "daily": load_daily_analysis(),
    }


def available_ranges() -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for report_dir in report_dirs():
        requested_range = infer_report_range(report_dir)
        item = buckets.setdefault(
            requested_range,
            {"range": requested_range, "label": human_range_name(requested_range), "count": 0, "latest": ""},
        )
        item["count"] += 1
        if not item["latest"]:
            item["latest"] = report_dir.name
    return sorted(buckets.values(), key=lambda item: item["range"])
