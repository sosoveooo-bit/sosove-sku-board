"""JP25 workbench contracts; all external model/image calls are mocked."""
from copy import deepcopy
from io import BytesIO
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PIL import Image
from sku_board import backend, jp25_workbench as wb
from sku_board.tests import test_jp25_prompt_contract_regressions as fixtures


def image(size=(1500, 2000), color="white"):
    output = BytesIO()
    Image.new("RGB", size, color).save(output, format="PNG")
    return output.getvalue()


def upload(data):
    return SimpleNamespace(filename="fixture.png", file=BytesIO(data))


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        # Any unexpected model or paid generation call must fail this test.
        for name in ("invoke_ai_director_chat", "invoke_ai_director_chat_once", "generate_images_via_chatgpt2api_tasks"):
            mock = patch.object(backend, name, side_effect=AssertionError(f"Unexpected external call: {name}"))
            mock.start()
            self.addCleanup(mock.stop)

    def test_override_preserves_source_plan_and_source_evidence(self):
        page = {"page": 7, "headline": "元の見出し", "sourcePointIndex": 3, "sourcePointText": "宽松袖口", "textPolicy": "minimal"}
        before = deepcopy(page)
        prompt = wb.apply_prompt("Exact product. Headline 元の見出し. Evidence: wide cuffs.", page,
                                 {"pages": {"7": {"headline": "袖まわりにゆとり", "scene": "户外侧面", "goal": "袖口空间"}}})
        self.assertNotIn("元の見出し", prompt)
        self.assertIn("袖まわりにゆとり", prompt)
        self.assertIn("wide cuffs", prompt)
        self.assertIn("户外侧面", prompt)
        self.assertEqual(page, before)
        self.assertEqual(wb.apply_prompt("unchanged", page, {}), "unchanged")
        self.assertIn("text-free page", wb.apply_prompt("base", page, {"pages": {"7": {"textFree": True}}}))

    def test_invalid_adjustments_are_rejected_without_silent_truncation(self):
        for value in ('broken json', {"productNotes": "x" * 2001}, {"pages": {"26": {}}}, {"pages": []}):
            with self.subTest(value=str(value)[:40]), self.assertRaises(ValueError):
                wb.normalize(value)

    def test_actual_dimensions_and_pixel_duplicates(self):
        data = image((1152, 1536))
        rows = wb.inspect_images([("1.png", data, "image/png"), ("2.png", data, "image/png")], [1, 4])
        self.assertEqual(rows[0]["width"], 1152)
        self.assertFalse(rows[0]["sizePassed"])
        self.assertEqual(rows[0]["visualStatus"], "not_checked")
        self.assertIn("第 1 页", rows[1]["issues"][-1])

    def test_missing_or_duplicate_visual_response_never_passes(self):
        for payload in ({"results": []}, {"results": [{"page": 2, "status": "pass", "issues": []}]}):
            rows = [{"page": 1, "issues": [], "visualStatus": "not_checked"}]
            with self.assertRaises(ValueError): wb.merge_visual_report(rows, payload)
            self.assertEqual(rows[0]["visualStatus"], "not_checked")

    def test_report_auth_and_page_upload_validation(self):
        fields = {"suiteKey": backend.AI_IMAGE_LANDING_SUITE_KEY, "pageNumbers": "[1]", "suitePlan": '[{"page":1}]'}
        with self.assertRaises(ValueError): backend.inspect_jp25_images(fields, {}, {"role": "viewer"})
        with self.assertRaises(ValueError): backend.inspect_jp25_images(fields, {}, {"role": "admin"})
        with self.assertRaises(ValueError): backend.inspect_jp25_images({**fields, "pageNumbers": "[1,1]"}, {}, {"role": "admin"})

    def test_size_report_does_not_call_a_model(self):
        result = backend.inspect_jp25_images({"suiteKey": backend.AI_IMAGE_LANDING_SUITE_KEY, "pageNumbers": "[1]",
            "suitePlan": '[]'}, {"generated0": upload(image())}, {"role": "admin"})
        self.assertTrue(result["results"][0]["sizePassed"])
        self.assertFalse(result["visualChecked"])
        backend.invoke_ai_director_chat_once.assert_not_called()
        backend.generate_images_via_chatgpt2api_tasks.assert_not_called()

    def test_failed_visual_report_keeps_local_results_and_never_generates(self):
        fields = {"suiteKey": backend.AI_IMAGE_LANDING_SUITE_KEY, "pageNumbers": "[1]", "visualCheck": "true",
                  "suitePlan": '[{"page":1,"headline":"自然な織り感"}]'}
        settings = {"enabled": True, "baseUrl": "https://fixture.invalid", "apiKey": "test-only", "model": "fixture", "visionEnabled": True}
        for content in ("broken response", '{"results":[]}'):
            with patch.object(backend, "load_ai_director_settings", return_value=settings), patch.object(
                backend, "invoke_ai_director_chat_once", return_value=(content, 5)):
                result = backend.inspect_jp25_images(fields, {"generated0": upload(image()), "reference0": upload(image())}, {"role": "admin"})
            self.assertFalse(result["visualChecked"])
            self.assertTrue(result["warning"])
            self.assertEqual(result["results"][0]["visualStatus"], "not_checked")
        backend.generate_images_via_chatgpt2api_tasks.assert_not_called()

    def test_visual_report_uses_current_plan_and_exact_user_copy(self):
        fields = {"suiteKey": backend.AI_IMAGE_LANDING_SUITE_KEY, "pageNumbers": "[16]", "visualCheck": "true",
                  "suitePlan": '[{"page":16,"objective":"材质细节"}]',
                  "jp25Workbench": json.dumps({"pages": {"16": {"headline": "自然な織り感"}}})}
        settings = {"enabled": True, "baseUrl": "https://fixture.invalid", "apiKey": "test-only", "model": "fixture", "visionEnabled": True}
        with patch.object(backend, "load_ai_director_settings", return_value=settings), patch.object(backend,
            "invoke_ai_director_chat_once", return_value=(json.dumps({"results": [{"page": 16, "status": "pass", "issues": [], "observedCopy": "自然な織り感"}]}), 5)) as model:
            result = backend.inspect_jp25_images(fields, {"generated0": upload(image()), "reference0": upload(image())}, {"role": "admin"})
        self.assertTrue(result["visualChecked"])
        self.assertEqual(result["results"][0]["visualStatus"], "pass")
        self.assertIn("自然な織り感", json.dumps(model.call_args.args[1], ensure_ascii=False))

    def test_planner_cache_changes_with_global_locks_not_local_page_edits(self):
        payload = {"prompt": "Product", "suiteBrief": "商品"}
        with patch.object(backend, "load_ai_director_settings", return_value={"model": "fixture"}):
            base = backend.ai_image_jp25_plan_singleflight_key(payload, [], [])
            self.assertNotEqual(base, backend.ai_image_jp25_plan_singleflight_key({**payload, "jp25Workbench": {"styleNotes": "暖白"}}, [], []))
            self.assertEqual(base, backend.ai_image_jp25_plan_singleflight_key({**payload, "jp25Workbench": {"pages": {"1": {"scene": "户外"}}}}, [], []))

    def test_generation_receives_edits_preserves_seven_layers_and_original_refs(self):
        Fixtures = fixtures.Jp25PromptContractRegressionTests
        brief = Fixtures.five_point_brief()
        pages = Fixtures.attach_remote_layers(backend.build_ai_image_suite_plan(Fixtures.PRODUCT_PROMPT, brief, "1500x2000"))
        fields = {"prompt": Fixtures.PRODUCT_PROMPT, "mode": "edit", "model": "gpt-image-2", "size": "1500x2000",
                  "quality": "high", "count": "1", "suiteKey": backend.AI_IMAGE_LANDING_SUITE_KEY,
                  "suiteBrief": brief, "suitePlan": json.dumps(pages), "suitePageIndexes": "[1]",
                  "referenceBindings": '[{"index":1,"role":"product","filename":"fixture.png"}]',
                  "jp25Workbench": json.dumps({"pages": {"1": {"headline": "毎日の一着", "scene": "自然光の窓辺"}}})}
        fields["jp25Revision"] = "0123456789abcdef"
        before = deepcopy(pages)
        with patch.object(backend, "chatgpt2api_image_tasks_enabled", return_value=True), patch.object(backend,
            "generate_images_via_chatgpt2api_tasks", return_value={"outputs": [{"index": 0, "image": (image(), "image/png")}], "errors": [], "pending": [], "taskIds": [], "timedOut": False}) as generate, patch.object(
            backend, "save_ai_image_outputs", return_value=([{"id": "fixture-image", "name": "fixture.png"}], ["fixture-preview"])), patch.object(
            backend, "ai_image_programmatic_typography_enabled", return_value=False):
            result = backend.generate_ad_launch_ai_image_edit(fields, {"reference0": upload(image())}, {"role": "admin"})
        self.assertTrue(result["ok"])
        submitted = generate.call_args.kwargs["prompts"][0]
        self.assertIn("毎日の一着", submitted)
        self.assertIn("自然光の窓辺", submitted)
        self.assertIn("REMOTE_PAGE_01", submitted)
        self.assertIn("JP25 USER-EDITED DESIGN", submitted)
        self.assertEqual(generate.call_args.kwargs["reference_images"][0][0], "fixture.png")
        self.assertEqual(result["materials"][0]["jp25Revision"], "0123456789abcdef")
        self.assertEqual(result["materials"][0]["suiteHeadline"], "毎日の一着")
        self.assertEqual(pages, before)


if __name__ == "__main__": unittest.main()
