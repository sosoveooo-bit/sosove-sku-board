import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from sku_board import backend


class AdLaunchDraftTests(unittest.TestCase):
    def test_incomplete_draft_is_saved_and_publish_validation_is_deferred(self) -> None:
        actor = {"username": "admin", "name": "管理员", "role": "admin"}
        board = {"items": [], "adLaunches": [], "users": []}
        payload = {
            "accountId": "act_TEST",
            "credentialId": "cred_TEST",
            "pageId": "",
            "name": "",
            "headline": "",
            "primaryText": "",
            "linkUrl": "",
            "campaignMode": "create",
            "adsetMode": "create",
            "dailyBudget": 10,
            "countries": ["JP"],
            "batchCount": 1,
            "material": {
                "path": str(Path("sku_board/static/index.html").resolve()),
                "name": "draft-test.png",
                "type": "image",
            },
        }

        with patch.object(backend, "load_board", return_value=board), \
            patch.object(backend, "save_board"), \
            patch.object(
                backend,
                "resolve_meta_credential_for_account",
                return_value={"id": "cred_TEST", "name": "测试凭证"},
            ), \
            patch.object(backend, "validate_meta_launch_identity"), \
            patch.object(backend, "enrich_ad_launch", side_effect=lambda launch, actor=None: deepcopy(launch)), \
            patch.object(backend, "list_ad_launches", return_value={"launches": [], "summary": {}, "options": {}}):
            result = backend.create_ad_launch(payload, actor)

        launch = result["launch"]
        self.assertEqual(result["created"], 1)
        self.assertEqual(launch["status"], "ready")
        self.assertEqual(launch["accountId"], "act_TEST")
        self.assertEqual(launch["name"], "")

        with self.assertRaisesRegex(ValueError, "Facebook Page ID"):
            backend.validate_ad_launch_ready(launch)

    def test_ad_launch_form_does_not_use_native_required_validation_for_drafts(self) -> None:
        html = Path("sku_board/static/index.html").read_text(encoding="utf-8")
        form_start = html.index('<form id="ad-launch-form"')
        form_end = html.index("</form>", form_start)
        form = html[form_start:form_end]

        self.assertIn("novalidate", form.split(">", 1)[0])
        for field_id in (
            "ad-launch-name",
            "ad-launch-headline",
            "ad-launch-primary-text",
            "ad-launch-link-url",
        ):
            field_start = form.index(f'id="{field_id}"')
            field_end = form.find(">", field_start)
            self.assertNotIn(" required", form[field_start:field_end])


if __name__ == "__main__":
    unittest.main()
