"""Offline contracts for the Facebook ads monitor.

Every test runs without network access and without a real report directory;
report fixtures are written into a temporary directory instead.
"""
from __future__ import annotations

import contextlib
import csv
import json
import os
import importlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from facebook_ads_monitor import backend


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8", newline="")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class PathConfigurationTests(unittest.TestCase):
    """Deployment paths come from the environment, never from a fixed machine."""

    def test_paths_are_overridable_by_environment(self) -> None:
        env = {
            "FB_ADS_SKILL_ROOT": "/srv/fb-skill",
            "FB_ADS_PULL_SCRIPT": "/srv/fb-skill/pull.py",
            "FB_ADS_TOKEN_PATH": "/srv/fb/token.txt",
            "FB_ADS_REPORT_ROOT": "/srv/fb/reports",
        }
        with reloaded_backend(env) as module:
            self.assertEqual(module.SKILL_ROOT, Path("/srv/fb-skill"))
            self.assertEqual(module.PULL_SCRIPT, Path("/srv/fb-skill/pull.py"))
            self.assertEqual(module.TOKEN_PATH, Path("/srv/fb/token.txt"))
            self.assertEqual(module.REPORT_ROOT, Path("/srv/fb/reports"))

    def test_defaults_stay_inside_the_package(self) -> None:
        blanked = {
            "FB_ADS_SKILL_ROOT": "",
            "FB_ADS_PULL_SCRIPT": "",
            "FB_ADS_TOKEN_PATH": "",
            "FB_ADS_REPORT_ROOT": "",
        }
        with reloaded_backend(blanked) as module:
            package = Path(module.__file__).resolve().parent
            self.assertTrue(module.TOKEN_PATH.is_relative_to(package))
            self.assertTrue(module.REPORT_ROOT.is_relative_to(package))

    def test_source_has_no_machine_specific_paths(self) -> None:
        source = (Path(backend.__file__).resolve()).read_text(encoding="utf-8")
        self.assertNotIn("C:\\Users", source)
        self.assertNotIn(".openclaw", source)


@contextlib.contextmanager
def reloaded_backend(env: dict[str, str]):
    """Reload the module under a patched environment, then restore it.

    Module-level paths are resolved at import time, so the reload is the only
    way to observe them. Restoring afterwards keeps the global module state
    from leaking into the other tests.
    """
    with patch.dict(os.environ, env, clear=False):
        module = importlib.reload(backend)
        try:
            yield module
        finally:
            importlib.reload(backend)


class RangeTests(unittest.TestCase):
    def test_unknown_range_falls_back_to_default(self) -> None:
        self.assertEqual(backend.sanitize_range_name("nonsense"), backend.DEFAULT_RANGE)
        self.assertEqual(backend.sanitize_range_name(None), backend.DEFAULT_RANGE)
        self.assertEqual(backend.sanitize_range_name("  today "), "today")

    def test_labels_are_human_readable(self) -> None:
        self.assertEqual(backend.human_range_name("last_7d"), "近 7 天")
        self.assertEqual(backend.human_range_name("yesterday"), "昨天")


class AdDecisionTests(unittest.TestCase):
    def test_scale_requires_purchases_and_roas(self) -> None:
        self.assertEqual(backend.action_for_ad({"purchase": "2", "roas": "3.2"}), "scale")
        # One purchase with no spend recorded is not yet a scale decision.
        self.assertEqual(backend.action_for_ad({"purchase": "1", "roas": "9"}), "idle")
        self.assertEqual(
            backend.action_for_ad({"purchase": "1", "roas": "9", "spend": "15"}),
            "watch",
        )

    def test_click_without_conversion_is_a_landing_page_problem(self) -> None:
        action = backend.action_for_ad({"purchase": "0", "add_to_cart": "0", "clicks": "25"})
        self.assertEqual(action, "fix_landing")
        self.assertEqual(backend.action_label(action), "查承接")

    def test_spend_with_weak_roas_is_reduced(self) -> None:
        self.assertEqual(
            backend.action_for_ad({"purchase": "1", "spend": "40", "roas": "1.4"}),
            "reduce",
        )

    def test_zero_spend_is_idle(self) -> None:
        self.assertEqual(backend.action_for_ad({"spend": "0"}), "idle")

    def test_family_groups_creatives_by_prefix(self) -> None:
        self.assertEqual(
            backend.creative_family("634258#creator#hash"),
            "634258#creator",
        )
        self.assertEqual(backend.creative_family(""), "未命名素材")

    def test_normalize_ad_adds_rates_and_labels(self) -> None:
        row = backend.normalize_ad(
            {
                "ad_name": "1#a#h",
                "spend": "30",
                "purchase": "3",
                "roas": "4",
                "inline_link_clicks": "100",
                "add_to_cart": "10",
            }
        )
        self.assertEqual(row["family"], "1#a")
        self.assertEqual(row["action"], "scale")
        self.assertEqual(row["action_label"], "放量")
        self.assertEqual(row["tone"], "good")
        self.assertAlmostEqual(row["atc_rate"], 10.0)
        self.assertAlmostEqual(row["purchase_rate"], 3.0)


class TokenTests(unittest.TestCase):
    def test_redaction_masks_query_and_header_forms(self) -> None:
        for raw in (
            "https://graph.facebook.com/v22.0/x?access_token=SECRET",
            "access_token: SECRET",
            "access_token : SECRET",
            "access_token=SECRET&fields=spend",
        ):
            cleaned = backend.redact_token_text(raw)
            self.assertNotIn("SECRET", cleaned)
            self.assertIn("<redacted>", cleaned)

    def test_redaction_masks_a_bare_provider_token(self) -> None:
        raw = "request failed for EAA" + "a" * 40
        cleaned = backend.redact_token_text(raw)
        self.assertNotIn("a" * 40, cleaned)
        self.assertIn("<redacted>", cleaned)

    def test_token_file_is_read_from_the_configured_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            token_file = Path(temp) / "token.txt"
            token_file.write_text("fixture-token-value\n", encoding="utf-8")
            with patch.object(backend, "TOKEN_PATH", token_file):
                self.assertEqual(backend.read_access_token(), "fixture-token-value")

    def test_token_file_supports_json_and_query_forms(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            token_file = Path(temp) / "token.txt"
            token_file.write_text(json.dumps({"access_token": "from-json"}), encoding="utf-8")
            with patch.object(backend, "TOKEN_PATH", token_file):
                self.assertEqual(backend.read_access_token(), "from-json")
            token_file.write_text("?access_token=from-query", encoding="utf-8")
            with patch.object(backend, "TOKEN_PATH", token_file):
                self.assertEqual(backend.read_access_token(), "from-query")

    def test_missing_token_file_reports_the_configured_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            missing = Path(temp) / "absent.txt"
            with patch.object(backend, "TOKEN_PATH", missing):
                with self.assertRaises(FileNotFoundError) as caught:
                    backend.read_access_token()
            self.assertIn("absent.txt", str(caught.exception))

    def test_empty_token_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            token_file = Path(temp) / "token.txt"
            token_file.write_text("   \n", encoding="utf-8")
            with patch.object(backend, "TOKEN_PATH", token_file):
                with self.assertRaises(ValueError):
                    backend.read_access_token()


class CampaignGuardTests(unittest.TestCase):
    def test_campaign_ids_must_be_numeric_and_unique(self) -> None:
        self.assertEqual(backend.normalize_campaign_ids([1, "2", "2"]), ["1", "2"])
        with self.assertRaises(ValueError):
            backend.normalize_campaign_ids(["abc"])
        with self.assertRaises(ValueError):
            backend.normalize_campaign_ids([])
        with self.assertRaises(ValueError):
            backend.normalize_campaign_ids("123")

    def test_campaign_batch_is_capped(self) -> None:
        with self.assertRaises(ValueError):
            backend.normalize_campaign_ids([str(n) for n in range(21)])

    def test_destructive_calls_require_confirmation(self) -> None:
        with self.assertRaises(ValueError):
            backend.pause_campaigns(["123"])
        with self.assertRaises(ValueError):
            backend.pause_campaigns(["123"], confirm="yes")
        with self.assertRaises(ValueError):
            backend.copy_campaigns(["123"])

    def test_copy_guards_reject_bad_status_and_long_suffix(self) -> None:
        with patch.object(backend, "read_access_token", return_value="fixture-token"):
            with self.assertRaises(ValueError):
                backend.copy_campaigns(["123"], confirm="COPY_CAMPAIGNS", status_option="WRONG")
            with self.assertRaises(ValueError):
                backend.copy_campaigns(
                    ["123"], confirm="COPY_CAMPAIGNS", rename_suffix="x" * 81
                )


class ReportReadingTests(unittest.TestCase):
    def make_report(self, root: Path, name: str = "20260101_000000", preset: str = "last_7d") -> Path:
        report_dir = root / name
        account = report_dir / "act_000000000000000"
        account.mkdir(parents=True)
        (report_dir / "summary.json").write_text("{}", encoding="utf-8")
        write_csv(
            report_dir / "account_summary.csv",
            [{"account_name": "示例账户", "preset": preset, "spend": "100", "purchase": "4"}],
        )
        write_csv(
            account / "ad.csv",
            [
                {
                    "ad_name": "1#creator#hash",
                    "campaign_name": "camp",
                    "adset_name": "adset",
                    "spend": "30",
                    "purchase": "3",
                    "roas": "4",
                    "inline_link_clicks": "100",
                    "add_to_cart": "10",
                }
            ],
        )
        return report_dir

    def test_complete_report_detection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report_dir = self.make_report(root)
            self.assertTrue(backend.is_complete_report_dir(report_dir))
            self.assertFalse(backend.is_complete_report_dir(root / "missing"))

    def test_range_is_inferred_from_meta_then_csv(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report_dir = self.make_report(root, preset="last_30d")
            self.assertEqual(backend.infer_report_range(report_dir), "last_30d")
            backend.write_report_meta(report_dir, {"requestedRange": "today"})
            self.assertEqual(backend.infer_report_range(report_dir), "today")

    def test_missing_report_root_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(FileNotFoundError):
                backend.latest_report_dir(Path(temp) / "absent")

    def test_empty_report_root_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(FileNotFoundError):
                backend.latest_report_dir(Path(temp))

    def test_dashboard_payload_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_report(root)
            with reloaded_backend({"FB_ADS_REPORT_ROOT": str(root)}) as module:
                payload = module.build_dashboard_payload(range_name="last_7d")
            self.assertEqual(payload["source"]["sourceMode"], "cache")
            self.assertEqual(payload["source"]["range"], "last_7d")
            self.assertIn("summary", payload)
            self.assertIn("tables", payload)
            self.assertIn("boards", payload)
            self.assertEqual(payload["tables"]["ads"][0]["action"], "scale")
            self.assertEqual(payload["daily"], {})

    def test_direct_report_selection_uses_the_named_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_report(root, name="chosen")
            with reloaded_backend({"FB_ADS_REPORT_ROOT": str(root)}) as module:
                payload = module.build_dashboard_payload(report="chosen")
                self.assertEqual(payload["source"]["sourceMode"], "direct")
                self.assertEqual(payload["source"]["reportName"], "chosen")
                with self.assertRaises(FileNotFoundError):
                    module.build_dashboard_payload(report="absent")

    def test_available_ranges_bucket_by_preset(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_report(root, name="a", preset="last_7d")
            self.make_report(root, name="b", preset="last_7d")
            self.make_report(root, name="c", preset="today")
            with reloaded_backend({"FB_ADS_REPORT_ROOT": str(root)}) as module:
                ranges = {item["range"]: item for item in module.available_ranges()}
            self.assertEqual(ranges["last_7d"]["count"], 2)
            self.assertEqual(ranges["last_7d"]["label"], "近 7 天")
            self.assertEqual(ranges["today"]["count"], 1)


class AggregateTests(unittest.TestCase):
    def test_aggregate_sums_by_key(self) -> None:
        rows = [
            backend.with_numbers({"family": "a", "spend": "10", "purchase": "1"}),
            backend.with_numbers({"family": "a", "spend": "5", "purchase": "2"}),
            backend.with_numbers({"family": "b", "spend": "7", "purchase": "0"}),
        ]
        result = {item["name"]: item for item in backend.aggregate(rows, "family")}
        self.assertEqual(result["a"]["spend"], 15.0)
        self.assertEqual(result["a"]["purchase"], 3.0)
        self.assertEqual(result["b"]["spend"], 7.0)
        self.assertEqual(result["a"]["ads"], 2)


class HealthTests(unittest.TestCase):
    def test_dependency_status_reports_known_packages(self) -> None:
        status = backend.dependency_status()
        self.assertIn("requests", status["packages"])
        self.assertIsInstance(status["python"], str)


if __name__ == "__main__":
    unittest.main()
