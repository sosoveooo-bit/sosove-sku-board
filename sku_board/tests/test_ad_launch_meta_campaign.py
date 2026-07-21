import unittest
from unittest.mock import patch

from sku_board import backend


class AdLaunchMetaCampaignTests(unittest.TestCase):
    def test_adset_budget_campaign_explicitly_disables_budget_sharing(self) -> None:
        launch = {
            "accountId": "act_TEST",
            "campaignId": "",
            "campaignName": "Panel Test Campaign",
            "objective": "OUTCOME_TRAFFIC",
            "name": "Panel Test Ad",
        }
        credential = {"id": "cred_TEST"}

        with patch.object(backend, "meta_api_post", return_value={"id": "campaign_TEST"}) as post:
            campaign_id = backend.create_launch_campaign_if_needed(launch, credential)

        self.assertEqual(campaign_id, "campaign_TEST")
        request_data = post.call_args.args[1]
        self.assertEqual(request_data["status"], "PAUSED")
        self.assertEqual(request_data["is_adset_budget_sharing_enabled"], "false")

    def test_targeting_explicitly_enables_advantage_audience(self) -> None:
        targeting = backend.ad_launch_targeting(
            {
                "countries": ["JP"],
                "ageMin": 25,
                "ageMax": 55,
                "gender": "female",
                "advancedAudience": True,
                "placementMode": "advantage",
            }
        )

        self.assertEqual(targeting["targeting_automation"], {"advantage_audience": 1})

    def test_targeting_explicitly_disables_advantage_audience(self) -> None:
        targeting = backend.ad_launch_targeting(
            {
                "countries": ["JP"],
                "advancedAudience": False,
                "placementMode": "manual",
                "placements": ["facebook_feed"],
            }
        )

        self.assertEqual(targeting["targeting_automation"], {"advantage_audience": 0})


if __name__ == "__main__":
    unittest.main()
