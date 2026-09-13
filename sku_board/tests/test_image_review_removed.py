import unittest
from pathlib import Path
from unittest.mock import patch
from sku_board import backend


class ReviewRemovedTests(unittest.TestCase):
    def test_legacy_endpoint_never_calls_model(self):
        with patch.object(backend, "can_use_ai_image", return_value=True), patch.object(backend, "invoke_ai_director_chat") as model:
            result = backend.review_ai_image_suite({}, {}, {})
            self.assertEqual(result["status"], "disabled")
            self.assertFalse(result["reviewed"])
            model.assert_not_called()

    def test_ui_generation_has_no_review_calls(self):
        root = Path(backend.__file__).parent
        js = (root / "static/app.js").read_text(encoding="utf-8")
        html = (root / "static/index.html").read_text(encoding="utf-8")
        self.assertNotIn("await reviewAiImageSuitePageNumbers(", js)
        self.assertNotIn('review: "key"', js)
        self.assertNotIn('review: "all"', js)
        self.assertNotIn('id="ai-director-review-enabled"', html)
        self.assertNotIn('id="ai-director-review-threshold"', html)
