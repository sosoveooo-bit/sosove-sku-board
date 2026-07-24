from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sku_board import backend


class MetaAdAnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.original = (backend.DATA_DIR, backend.DATA_FILE, backend._META_AD_ANALYSIS_MODULE)
        backend.DATA_DIR = Path(self.temp.name)
        backend.DATA_FILE = backend.DATA_DIR / "sku_board.json"
        backend._META_AD_ANALYSIS_MODULE = None
        backend.save_board(
            {
                "items": [
                    {
                        "sku": "1001",
                        "title": "日本牛仔裤",
                        "tags": [],
                        "ad": {},
                        "design": {},
                        "weeklyTasks": [],
                        "notes": [],
                        "feedback": [],
                        "refresh": {},
                    }
                ],
                "users": [],
                "metaAssetBindings": [],
                "createdAt": backend.now_iso(),
            }
        )

    def tearDown(self) -> None:
        backend.DATA_DIR, backend.DATA_FILE, backend._META_AD_ANALYSIS_MODULE = self.original
        self.temp.cleanup()

    def rows(self) -> list[dict]:
        return [
            {
                "account_id": "act_1",
                "account_name": "JP Ads",
                "campaign_id": "c1",
                "campaign_name": "JP_牛仔裤",
                "adset_id": "s1",
                "adset_name": "JP broad",
                "ad_id": "a1",
                "ad_name": "1001-video-angle.mp4",
                "date_start": "2026-07-10",
                "date_stop": "2026-07-16",
                "spend": 20,
                "impressions": 2000,
                "clicks": 100,
                "inline_link_clicks": 90,
                "purchase": 5,
                "purchase_value": 150,
                "credential_id": "mc1",
                "credential_name": "System",
            },
            {
                "account_id": "act_1",
                "account_name": "JP Ads",
                "campaign_id": "c1",
                "campaign_name": "JP_牛仔裤",
                "adset_id": "s1",
                "adset_name": "JP broad",
                "ad_id": "a2",
                "ad_name": "no-order.mp4",
                "date_start": "2026-07-10",
                "date_stop": "2026-07-16",
                "spend": 10,
                "impressions": 2000,
                "clicks": 40,
                "inline_link_clicks": 35,
                "purchase": 0,
                "purchase_value": 0,
                "credential_id": "mc1",
                "credential_name": "System",
            },
        ]

    def test_blank_environment_path_uses_bundled_analysis_skill(self) -> None:
        with patch.dict(os.environ, {"SKU_BOARD_META_AD_ANALYSIS_SCRIPT": ""}):
            script_path = backend.meta_ad_analysis_script_path()

        self.assertEqual(script_path, backend.META_AD_ANALYSIS_SCRIPT)
        self.assertTrue(script_path.is_file())
        self.assertTrue(callable(backend.load_meta_ad_analysis_module().build_report))

    def test_meta_rows_are_analyzed_with_skill_decisions(self) -> None:
        with patch.object(
            backend,
            "meta_credential_insight_rows",
            return_value=(
                self.rows(),
                {
                    "mode": "test",
                    "warning": "",
                    "accounts": 2,
                    "accountCatalog": [
                        {"accountId": "act_1", "accountName": "JP Ads", "businessId": "bm-jp", "businessName": "JP BC", "credentialId": "mc1", "credentialName": "System"},
                        {"accountId": "act_2", "accountName": "KR Ads", "businessId": "bm-kr", "businessName": "KR BC", "credentialId": "mc2", "credentialName": "System KR"},
                    ],
                },
            ),
        ):
            result = backend.analyze_meta_ads(
                {"range": "last_7d", "usePlatformPurchase": "true"},
                {"role": "ops", "username": "operator", "name": "运营"},
            )

        report = result["report"]
        self.assertEqual(result["source"]["platform"], "Meta")
        self.assertEqual(report["summary"]["platform_purchase_events"], 5)
        self.assertEqual(report["summary"]["platform_purchase_value"], 150)
        self.assertEqual(report["summary"]["platform_roas"], 5.0)
        actions = {item["AdId"]: item["recommended_action"] for item in report["action_table"]}
        self.assertEqual(actions["a1"], "scale_observe")
        self.assertEqual(actions["a2"], "immediate_close")
        self.assertEqual(report["scale_ads"][0]["AdId"], "a1")
        self.assertIn("a2", {item["AdId"] for item in report["stop_ads"]})
        self.assertEqual(report["action_table"][0]["sku"], "1001")
        self.assertEqual({item["AdvertiserId"] for item in report["accounts"]}, {"1", "2"})
        self.assertEqual(report["accounts"][-1]["AccountName"], "KR Ads")
        self.assertIn("Meta Purchase", result["warning"])

    def test_platform_purchase_can_be_disabled_and_permission_is_checked(self) -> None:
        with patch.object(
            backend,
            "meta_credential_insight_rows",
            return_value=(self.rows(), {"mode": "test", "warning": "", "accounts": 1}),
        ):
            result = backend.analyze_meta_ads(
                {"range": "last_7d", "usePlatformPurchase": "false"},
                {"role": "selection", "username": "selection", "name": "选品"},
            )

        summary = result["report"]["summary"]
        self.assertIsNone(summary["actual_orders"])
        self.assertEqual(summary["platform_purchase_events"], 5)
        with self.assertRaisesRegex(ValueError, "只有管理员"):
            backend.analyze_meta_ads(
                {"range": "last_7d"},
                {"role": "designer", "username": "designer", "name": "设计"},
            )


if __name__ == "__main__":
    unittest.main()
