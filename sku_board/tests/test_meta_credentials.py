from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sku_board import backend


class MetaCredentialStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.original = {
            "DATA_DIR": backend.DATA_DIR,
            "DATA_FILE": backend.DATA_FILE,
            "META_CREDENTIAL_FILE": backend.META_CREDENTIAL_FILE,
            "META_CREDENTIAL_KEY_FILE": backend.META_CREDENTIAL_KEY_FILE,
        }
        backend.DATA_DIR = Path(self.temp.name)
        backend.DATA_FILE = backend.DATA_DIR / "sku_board.json"
        backend.META_CREDENTIAL_FILE = backend.DATA_DIR / "meta_credentials.json"
        backend.META_CREDENTIAL_KEY_FILE = backend.DATA_DIR / "meta_credentials.key"
        self.previous_key = os.environ.get("SKU_BOARD_CREDENTIAL_ENCRYPTION_KEY")
        os.environ["SKU_BOARD_CREDENTIAL_ENCRYPTION_KEY"] = "test-meta-credential-encryption-key-0123456789"

    def tearDown(self) -> None:
        for key, value in self.original.items():
            setattr(backend, key, value)
        if self.previous_key is None:
            os.environ.pop("SKU_BOARD_CREDENTIAL_ENCRYPTION_KEY", None)
        else:
            os.environ["SKU_BOARD_CREDENTIAL_ENCRYPTION_KEY"] = self.previous_key
        self.temp.cleanup()

    def record(self, credential_id: str = "MC-TEST") -> dict:
        return {
            "id": credential_id,
            "name": "JP System User",
            "credentialType": "system",
            "token": "EAAB-test-token-must-never-appear-in-browser-response",
            "active": True,
            "status": "ready",
            "identity": {"id": "123", "name": "Meta System User"},
            "assets": {
                "businesses": [{"id": "bm-1", "name": "JP BM"}],
                "adAccounts": [
                    {
                        "accountId": "act_123456",
                        "accountName": "JP Ads",
                        "numericId": "123456",
                        "credentialId": credential_id,
                    }
                ],
                "pages": [],
                "instagramActors": [],
            },
            "lastValidatedAt": "2026-07-16T00:00:00+00:00",
            "lastSyncedAt": "2026-07-16T00:00:00+00:00",
            "lastError": "",
            "createdAt": "2026-07-16T00:00:00+00:00",
            "updatedAt": "2026-07-16T00:00:00+00:00",
            "createdBy": "管理员",
        }

    def admin(self) -> dict:
        return {"id": "admin", "username": "admin", "name": "管理员", "role": "admin", "active": True}

    def test_store_is_encrypted_and_public_metadata_redacts_token(self) -> None:
        record = self.record()
        backend.save_meta_credential_store({"version": 1, "credentials": [record]})

        raw = backend.META_CREDENTIAL_FILE.read_text(encoding="utf-8")
        self.assertIn("ciphertext", raw)
        self.assertNotIn(record["token"], raw)

        loaded = backend.load_meta_credential_store()
        self.assertEqual(loaded["credentials"][0]["token"], record["token"])
        public = backend.public_meta_credential(loaded["credentials"][0])
        self.assertNotIn("token", public)
        self.assertNotIn(record["token"], str(public))
        self.assertIn("••••••", public["tokenMasked"])

    def test_binding_resolves_credential_and_restricts_unassigned_operator(self) -> None:
        record = self.record()
        backend.save_meta_credential_store({"version": 1, "credentials": [record]})
        backend.save_board(
            {
                "items": [],
                "users": [backend.build_auth_user("operator", "运营", "ops", "12345678")],
                "metaAssetBindings": [],
                "createdAt": backend.now_iso(),
            }
        )

        result = backend.bind_meta_ad_account(
            {"accountId": "act_123456", "credentialId": "MC-TEST", "assignedUsernames": ["operator"]}, self.admin()
        )
        self.assertTrue(result["ok"])
        operator = {"id": "operator", "username": "operator", "name": "运营", "role": "ops", "active": True}
        resolved = backend.resolve_meta_credential_for_account("123456", operator)
        self.assertEqual(resolved["id"], "MC-TEST")
        self.assertEqual(resolved["token"], record["token"])

        board = backend.load_board()
        board["metaAssetBindings"][0]["assignedUsernames"] = []
        backend.save_board(board)
        with self.assertRaisesRegex(ValueError, "没有使用"):
            backend.resolve_meta_credential_for_account("act_123456", operator)

    def test_meta_catalog_only_exposes_assigned_asset_to_operator(self) -> None:
        record = self.record()
        backend.save_meta_credential_store({"version": 1, "credentials": [record]})
        backend.save_board(
            {
                "items": [],
                "users": [backend.build_auth_user("operator", "运营", "ops", "12345678")],
                "metaAssetBindings": [
                    {
                        "accountId": "act_123456",
                        "accountName": "JP Ads",
                        "credentialId": "MC-TEST",
                        "assignedUsernames": ["operator"],
                    }
                ],
                "createdAt": backend.now_iso(),
            }
        )
        operator = {"id": "operator", "username": "operator", "name": "运营", "role": "ops", "active": True}
        assets = backend.meta_asset_catalog(operator)
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0]["credentialName"], "JP System User")
        self.assertNotIn("token", assets[0])

    def test_system_credential_asset_detail_and_selected_account_scope_hide_unselected_assets(self) -> None:
        record = self.record()
        record["selectedAccountIds"] = ["act_123456"]
        record["selectedPageIds"] = ["page-1"]
        record["assets"]["pages"] = [{"id": "page-1", "name": "JP Page"}]
        record["assets"]["adAccounts"].append(
            {
                "accountId": "act_987654",
                "accountName": "Unselected Ads",
                "numericId": "987654",
                "credentialId": "MC-TEST",
            }
        )
        backend.save_meta_credential_store({"version": 1, "credentials": [record]})
        backend.save_board({"items": [], "users": [], "metaAssetBindings": [], "createdAt": backend.now_iso()})

        detail = backend.public_meta_credential_assets(record)
        self.assertNotIn("token", str(detail))
        self.assertTrue(detail["adAccounts"][0]["selected"])
        self.assertFalse(detail["adAccounts"][1]["selected"])
        self.assertTrue(detail["pages"][0]["selected"])
        catalog = backend.meta_asset_catalog(self.admin())
        self.assertEqual([item["accountId"] for item in catalog], ["act_123456"])

    def test_system_user_token_uses_business_system_user_access_tokens_edge(self) -> None:
        calls = []

        def fake_graph_request(method, endpoint, token, params=None, data=None, timeout=45):
            calls.append({"method": method, "endpoint": endpoint, "token": token, "data": data, "timeout": timeout})
            return {"access_token": "EAAB-system-token"}

        with patch.object(backend, "meta_graph_request", side_effect=fake_graph_request):
            result = backend.generate_meta_system_user_token(
                "bm-1",
                "system-user-1",
                "EAAB-personal-token",
                ["act_123456"],
                ["page-1"],
            )

        self.assertEqual(result, "EAAB-system-token")
        self.assertEqual(calls[0]["endpoint"], "bm-1/system_user_access_tokens")
        self.assertEqual(calls[0]["data"]["system_user_id"], "system-user-1")
        self.assertIn("123456", calls[0]["data"]["asset"])
        self.assertIn("page-1", calls[0]["data"]["asset"])
        self.assertIn("ads_read", calls[0]["data"]["scope"])

    def test_launch_identity_must_belong_to_credential_assets(self) -> None:
        credential = self.record()
        credential["assets"]["pages"] = [{"id": "page-1", "name": "JP Page"}]
        credential["assets"]["instagramActors"] = [{"id": "ig-1", "pageId": "page-1", "name": "JP IG"}]
        credential["selectedPageIds"] = ["page-1"]

        backend.validate_meta_launch_identity(credential, "page-1", "ig-1")
        with self.assertRaisesRegex(ValueError, "主页"):
            backend.validate_meta_launch_identity(credential, "page-2", "")
        with self.assertRaisesRegex(ValueError, "Instagram"):
            backend.validate_meta_launch_identity(credential, "page-1", "ig-2")

    def test_force_oauth_does_not_fallback_to_existing_server_token(self) -> None:
        with patch.dict(os.environ, {"META_APP_ID": "", "META_APP_SECRET": ""}, clear=False):
            with self.assertRaisesRegex(ValueError, "系统登录通道"):
                backend.start_meta_oauth({"forceOAuth": True}, self.admin())

    def test_asset_sync_derives_business_from_ad_account_metadata(self) -> None:
        record = self.record()
        record["token"] = "EAAB-valid-test-token"

        def fake_graph_request(method, endpoint, token, params=None, data=None, timeout=45):
            if endpoint == "me":
                return {"id": "123", "name": "Meta User"}
            return {"data": []}

        ad_rows = [{
            "id": "act_123456",
            "account_id": "123456",
            "name": "JP Ads",
            "business": {"id": "bm-1", "name": "Bluefocus"},
        }]
        with patch.object(backend, "meta_graph_request", side_effect=fake_graph_request), patch.object(
            backend,
            "meta_optional_collection",
            side_effect=[(ad_rows, ""), ([], ""), ([], "")],
        ):
            backend.sync_meta_credential_assets(record)

        self.assertEqual(record["assets"]["businesses"], [{"id": "bm-1", "name": "Bluefocus"}])


if __name__ == "__main__":
    unittest.main()
