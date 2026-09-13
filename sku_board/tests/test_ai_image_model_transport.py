"""Image model IDs must survive every ChatGPT2API transport unchanged."""

from contextlib import ExitStack
from io import BytesIO
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from sku_board import backend


NEW_MODELS = (
    "gpt-image-2.5",
    "gpt-image-2.5-flare",
    "gpt-image-2.5-sunburst",
)
DEFAULT_MODEL = "gpt-image-2.5-sunburst"
LEGACY_MODELS = ("gpt-image-2", "codex-gpt-image-2", "auto")
IMAGE = (b"transport-test-image", "image/png")
NODE = {
    "id": "transport-fixture",
    "name": "Transport fixture",
    "rootUrl": "https://image.example.invalid",
    "baseUrl": "https://image.example.invalid/v1",
    "authKey": "fixture-token",
}
ACTOR = {"username": "transport-test", "role": "admin"}


def response(body):
    result = Mock(
        ok=True, status_code=200, reason="OK",
        headers={"Content-Type": "application/json"}, text=json.dumps(body),
    )
    result.json.return_value = body
    return result


def fake_save(images, prompt, model, quality, size):
    materials = [
        {"id": f"AI-TEST{index}", "model": model, "prompt": prompt}
        for index, _ in enumerate(images)
    ]
    return materials, [f"/test-image-{index}.png" for index in range(len(images))]


class AiImageModelTransportTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        directory = self.stack.enter_context(tempfile.TemporaryDirectory(prefix="image-model-transport-"))
        self.data_dir = Path(directory)
        self.stack.enter_context(patch.dict(os.environ, {"SKU_BOARD_DATA_DIR": directory}))
        os.environ.pop("CHATGPT2API_IMAGE_MODEL", None)
        self.stack.enter_context(patch.object(backend, "DATA_DIR", self.data_dir))
        self.stack.enter_context(patch.object(backend, "AD_LAUNCH_UPLOAD_DIR", self.data_dir / "uploads"))
        self.stack.enter_context(patch("requests.sessions.Session.request", side_effect=AssertionError("Network disabled in model transport tests")))
        self.stack.enter_context(patch.object(backend, "log_ai_image_error"))
        self.stack.enter_context(patch.object(backend, "ai_image_skill_config", return_value={}))
        self.stack.enter_context(patch.object(backend, "shared_ai_director_open_prompts_enabled", return_value=False))

    def config(self):
        with (
            patch.object(backend, "public_chatgpt2api_service_nodes", return_value=[dict(NODE)]),
            patch.object(backend, "public_acore_image_service_node", return_value={"id": "giikin-acore"}),
            patch.object(backend, "public_linkfox_cloth_skill_runtime", return_value={}),
            patch.object(backend, "open_image_prompts_status", return_value={}),
            patch.object(backend, "shared_ai_director_runtime_settings", return_value={}),
        ):
            return backend.ad_launch_ai_image_config()

    def test_model_picker_exposes_new_and_existing_provider_ids(self):
        config = self.config()
        for model in (*NEW_MODELS, *LEGACY_MODELS):
            self.assertIn(model, config["models"])
        self.assertEqual(len(config["models"]), len(set(config["models"])))
        self.assertEqual(config["models"][-3:], [
            "acore/gpt-image-2", "acore/nano-banana-2", "acore/nano-banana-pro",
        ])
        self.assertEqual(config["model"], DEFAULT_MODEL)

    def test_explicit_selected_model_survives_request_normalization(self):
        for model in (*NEW_MODELS, *LEGACY_MODELS, "acore/gpt-image-2"):
            with self.subTest(model=model):
                normalized = backend.normalize_ai_image_request_fields({"prompt": "Photograph the exact product.", "model": model})
                self.assertEqual(normalized[1], model)
                self.assertEqual(backend.is_acore_image_model(model), model.startswith("acore/"))

    def test_missing_or_blank_model_uses_sunburst(self):
        for payload_model in (None, "", "  "):
            for env_model in (None, "", "  "):
                with self.subTest(payload_model=payload_model, env_model=env_model), patch.dict(os.environ, {}):
                    if env_model is None:
                        os.environ.pop("CHATGPT2API_IMAGE_MODEL", None)
                    else:
                        os.environ["CHATGPT2API_IMAGE_MODEL"] = env_model
                    normalized = backend.normalize_ai_image_request_fields({"prompt": "Product photo", "model": payload_model})
                    self.assertEqual(normalized[1], DEFAULT_MODEL)
                    self.assertEqual(self.config()["model"], DEFAULT_MODEL)

    def test_explicit_environment_default_does_not_override_request_choice(self):
        with patch.dict(os.environ, {"CHATGPT2API_IMAGE_MODEL": "  gpt-image-2.5-flare  "}):
            self.assertEqual(self.config()["model"], "gpt-image-2.5-flare")
            self.assertEqual(backend.normalize_ai_image_request_fields({"prompt": "Product photo"})[1], "gpt-image-2.5-flare")
            for model in (*NEW_MODELS, *LEGACY_MODELS):
                self.assertEqual(backend.normalize_ai_image_request_fields({"prompt": "Product photo", "model": model})[1], model)

    def task_submit(self, model, editing):
        session = Mock()
        submitted = {}

        def post(endpoint, **kwargs):
            body = kwargs["data" if editing else "json"]
            submitted.update({"endpoint": endpoint, **kwargs})
            submitted["task_id"] = body["client_task_id"]
            return response({"id": submitted["task_id"]})

        def get(_endpoint, **_kwargs):
            return response({"items": [{
                "id": submitted["task_id"], "status": "success",
                "images": [{"b64_json": "aW1hZ2U="}],
            }]})

        session.post.side_effect = post
        session.get.side_effect = get
        with (
            patch("requests.Session", return_value=session),
            patch.object(backend, "image_bytes_list_from_chatgpt2api_response", return_value=[IMAGE]),
        ):
            result = backend._generate_images_via_chatgpt2api_tasks_single(
                prompt="Photograph the exact product.", model=model, size="1024x1024", count=1,
                reference_images=[("reference.png", b"reference", "image/png")] if editing else None,
                service_node=dict(NODE),
            )
        self.assertEqual(result, [IMAGE])
        session.post.assert_called_once()
        session.close.assert_called_once()
        return submitted

    def test_async_json_generation_transmits_selected_model(self):
        for model in (*NEW_MODELS, *LEGACY_MODELS, ""):
            with self.subTest(model=model):
                submitted = self.task_submit(model, editing=False)
                self.assertEqual(submitted["json"]["model"], model or DEFAULT_MODEL)
                self.assertTrue(submitted["endpoint"].endswith("/api/image-tasks/generations"))
                self.assertNotIn("files", submitted)

    def test_async_multipart_edit_transmits_selected_model(self):
        for model in (*NEW_MODELS, *LEGACY_MODELS, ""):
            with self.subTest(model=model):
                submitted = self.task_submit(model, editing=True)
                self.assertEqual(submitted["data"]["model"], model or DEFAULT_MODEL)
                self.assertTrue(submitted["endpoint"].endswith("/api/image-tasks/edits"))
                self.assertEqual(submitted["files"][0][0], "image")
                self.assertNotIn("json", submitted)

    def sync_generate(self, model, *, editing=False, inpaint=False, task_unavailable=False):
        payload = {"prompt": "Photograph the exact product.", "size": "1024x1024", "count": 1}
        if model is not None:
            payload["model"] = model
        files = {"reference0": SimpleNamespace(filename="product.png", file=BytesIO(b"reference"))}
        if inpaint:
            payload["mode"] = "inpaint"
            files["mask"] = SimpleNamespace(filename="mask.png", file=BytesIO(b"mask"))
        with (
            patch.object(backend, "chatgpt2api_image_tasks_enabled", return_value=task_unavailable),
            patch.object(backend, "generate_ai_image_tasks_with_transient_retry", side_effect=backend.ImageTaskApiUnavailable("fixture endpoint is absent")) as async_request,
            patch.object(backend, "chatgpt2api_auth_key", return_value="fixture-token"),
            patch.object(backend, "chatgpt2api_base_url", return_value=NODE["baseUrl"]),
            patch("requests.post", return_value=response({"data": [{"b64_json": "aW1hZ2U="}]})) as post,
            patch.object(backend, "image_bytes_list_from_chatgpt2api_response", return_value=[IMAGE]),
            patch.object(backend, "save_ai_image_outputs", side_effect=fake_save) as save,
        ):
            if editing:
                result = backend.generate_ad_launch_ai_image_edit(payload, files, ACTOR)
            else:
                result = backend.generate_ad_launch_ai_image(payload, ACTOR)
        expected_model = model or DEFAULT_MODEL
        self.assertTrue(result["ok"])
        self.assertEqual(result["material"]["model"], expected_model)
        self.assertEqual(save.call_args.args[2], expected_model)
        if task_unavailable and not inpaint:
            self.assertEqual(async_request.call_args.kwargs["model"], expected_model)
        else:
            async_request.assert_not_called()
        post.assert_called_once()
        return post.call_args

    def test_sync_json_generation_keeps_selected_or_default_model(self):
        for model in (*NEW_MODELS, "gpt-image-2", None):
            with self.subTest(model=model):
                call = self.sync_generate(model)
                self.assertEqual(call.kwargs["json"]["model"], model or DEFAULT_MODEL)
                self.assertTrue(call.args[0].endswith("/images/generations"))

    def test_sync_multipart_edit_keeps_selected_or_default_model(self):
        for model in (*NEW_MODELS, "gpt-image-2", None):
            with self.subTest(model=model):
                call = self.sync_generate(model, editing=True)
                self.assertEqual(call.kwargs["data"]["model"], model or DEFAULT_MODEL)
                self.assertTrue(call.args[0].endswith("/images/edits"))
                self.assertEqual(call.kwargs["files"][0][0], "image")

    def test_inpainting_preserves_sunburst_and_mask(self):
        call = self.sync_generate(DEFAULT_MODEL, editing=True, inpaint=True)
        self.assertEqual(call.kwargs["data"]["model"], DEFAULT_MODEL)
        self.assertEqual([item[0] for item in call.kwargs["files"]], ["image", "mask"])

    def test_generation_task_api_unavailable_keeps_model_when_using_sync_endpoint(self):
        for model in NEW_MODELS:
            with self.subTest(model=model):
                call = self.sync_generate(model, task_unavailable=True)
                self.assertEqual(call.kwargs["json"]["model"], model)

    def test_edit_task_api_unavailable_keeps_model_when_using_sync_endpoint(self):
        for model in NEW_MODELS:
            with self.subTest(model=model):
                call = self.sync_generate(model, editing=True, task_unavailable=True)
                self.assertEqual(call.kwargs["data"]["model"], model)

    def test_transient_retry_retains_model_and_page_identity(self):
        with (
            patch.dict(os.environ, {"CHATGPT2API_IMAGE_TRANSIENT_RETRIES": "1"}),
            patch.object(backend, "generate_images_via_chatgpt2api_tasks", side_effect=[ValueError("HTTP 503 fixture busy"), [IMAGE]]) as generate,
            patch.object(backend, "ai_image_retryable_error", return_value=True),
            patch("time.sleep"),
        ):
            result = backend.generate_ai_image_tasks_with_transient_retry(
                actor=ACTOR, prompt="Product photo", model=DEFAULT_MODEL, size="750x1000", count=1,
                prompts=["Page 7 product evidence"], page_indexes=[6], suite_run_id="abcdef123456",
            )
        self.assertEqual(result, [IMAGE])
        self.assertEqual(generate.call_count, 2)
        for call in generate.call_args_list:
            self.assertEqual(call.kwargs["model"], DEFAULT_MODEL)
            self.assertEqual(call.kwargs["page_indexes"], [6])
            self.assertEqual(call.kwargs["suite_run_id"], "abcdef123456")

    def test_saved_output_metadata_keeps_selected_model(self):
        with (
            patch.object(backend, "prune_ai_image_output_files"),
            patch.object(backend, "ai_image_remote_storage_enabled", return_value=False),
            patch.object(backend, "cache_ai_image_preview"),
            patch.object(backend, "ai_image_output_delete_token", return_value="fixture-delete-token"),
        ):
            for model in (*NEW_MODELS, "gpt-image-2", ""):
                with self.subTest(model=model):
                    materials, _ = backend.save_ai_image_outputs([IMAGE], "Product photo", model, "high", "1024x1024")
                    self.assertEqual(materials[0]["model"], model or DEFAULT_MODEL)
                    self.assertTrue(Path(materials[0]["path"]).is_relative_to(self.data_dir))

    def test_recovered_mixed_models_use_each_task_model_instead_of_new_default(self):
        task_models = [
            ({"model": "gpt-image-2"}, "gpt-image-2"),
            ({"modelId": "gpt-image-2.5-flare"}, "gpt-image-2.5-flare"),
            ({"parameters": {"model": "gpt-image-2.5"}}, "gpt-image-2.5"),
            ({"request": {"model": "codex-gpt-image-2"}}, "codex-gpt-image-2"),
            ({}, "unknown"),
        ]
        tasks = [{
            "id": f"sosove-abcdef123456-p{index:02d}-r000001-a1",
            "mode": "edit", "status": "success", "size": "1500x2000",
            "images": [{"b64_json": "aW1hZ2U="}], **fields,
        } for index, (fields, _model) in enumerate(task_models, start=1)]
        with (
            patch.dict(os.environ, {"CHATGPT2API_IMAGE_MODEL": DEFAULT_MODEL}),
            patch.object(backend, "chatgpt2api_service_nodes", return_value=[dict(NODE)]),
            patch("requests.get", return_value=response({"items": tasks})),
            patch.object(backend, "build_ai_image_suite_prompts", return_value=(["Product photo"] * 25, [{"page": index} for index in range(1, 26)])),
            patch.object(backend, "image_bytes_list_from_chatgpt2api_response", return_value=[IMAGE]),
            patch.object(backend, "ai_image_remote_outputs_ready", return_value=True),
            patch.object(backend, "save_ai_image_outputs", side_effect=fake_save),
            patch.object(backend, "decorate_ai_image_suite_materials"),
            patch.object(backend, "generate_ai_image_tasks_with_transient_retry") as generate,
            patch("requests.post") as post,
        ):
            result = backend.recover_recent_ai_image_suite(
                ACTOR, run_id="abcdef123456", suite_key=backend.AI_IMAGE_LANDING_SUITE_KEY, suite_count=25,
            )
        self.assertEqual([item["model"] for item in result["materials"]], [model for _fields, model in task_models])
        generate.assert_not_called()
        post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
