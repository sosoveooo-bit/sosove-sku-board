"""Keep a partially completed hook image bound to its original planned variant."""

import unittest

from sku_board import backend
from sku_board.tests import test_cod_hook_vision_integration as _vision_fixtures


STALE_COD_RESTORE_REASON = (
    "Stale assertion for the pre-restore five-Agent COD route. The COD "
    "country/detail planner was intentionally restored to the GitHub main "
    "revision (see docs/plans/2026-09-18-cod-github-restore.md); this "
    "expectation belongs to the removed behaviour and is kept for the rewrite."
)


class HookPartialResultMetadataTests(unittest.TestCase):
    def setUp(self):
        # Compose the existing offline fixture rather than inherit its test
        # methods: this module adds one end-to-end assertion, not duplicate runs.
        self.fixture = _vision_fixtures.CodHookVisionIntegrationTests(
            "test_completed_materials_expose_only_public_analysis_and_original_source_mapping"
        )
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()

    @unittest.skip(STALE_COD_RESTORE_REASON)
    def test_second_hook_image_keeps_its_own_prompt_variant_and_sources_when_first_fails(self):
        fixture = self.fixture
        blue_image = (b"GENERATED-BLUE-SECOND-PAGE", "image/png")
        fixture.dispatch.side_effect = None
        fixture.dispatch.return_value = {
            "outputs": [{
                "index": 1, "taskId": "fixture-blue-task", "image": blue_image,
                "nodeId": "fixture-blue-node", "nodeName": "Blue node", "nodeLatencyMs": 12,
            }],
            "errors": [{
                "index": 0, "taskId": "fixture-khaki-task", "message": "Fixture first-page failure",
                "nodeId": "fixture-khaki-node", "nodeName": "Khaki node",
            }],
            "pending": [],
            "taskIds": ["fixture-khaki-task", "fixture-blue-task"],
            "nodeResults": [{"nodeId": "fixture-blue-node", "success": True}],
            "timedOut": False,
        }
        fixture.save_outputs.side_effect = lambda images, *_args: (
            [{"id": f"fixture-partial-{position}", "previewUrl": f"/fixture/partial-{position}.png"}
             for position, _image in enumerate(images)],
            [f"/fixture/partial-{position}.png" for position in range(len(images))],
        )

        result = backend.generate_ad_launch_ai_image_edit(fixture.fields(), fixture.uploads(), fixture.ACTOR)

        fixture.dispatch.assert_called_once()  # No automatic replacement render.
        fixture.save_outputs.assert_called_once()
        self.assertEqual(fixture.save_outputs.call_args.args[0], [blue_image])
        self.assertTrue(result["ok"])
        self.assertEqual(result["requestedCount"], 2)
        self.assertEqual(result["returnedCount"], 1)
        self.assertEqual(len(result["materials"]), 1)
        material = result["materials"][0]
        self.assertEqual(material["hookImageNumber"], 2)
        self.assertEqual(material["referenceSourceIndexes"], [5])
        self.assertEqual(material["productVariantIds"], ["blue"])
        self.assertEqual(material["variantReferenceIndex"], 5)
        self.assertEqual(material["referenceCount"], 1)
        submitted_prompts = fixture.dispatch.call_args.kwargs["prompts"]
        self.assertEqual(material["prompt"], submitted_prompts[1])
        self.assertNotEqual(material["prompt"], submitted_prompts[0])
        self.assertIn('"uploadedSourceIndex":5', material["prompt"])
        self.assertEqual(result["productAnalysis"]["status"], "ready")

        summary = result["suiteSummary"]
        self.assertTrue(summary["partial"])
        self.assertEqual(summary["requested"], 2)
        self.assertEqual(summary["attempted"], 2)
        self.assertEqual(summary["succeeded"], 1)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["running"], 0)
        self.assertEqual(summary["errors"][0]["index"], 0)


if __name__ == "__main__":
    unittest.main()
