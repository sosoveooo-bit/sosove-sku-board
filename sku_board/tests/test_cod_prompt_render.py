from contextlib import ExitStack
from io import BytesIO
from types import SimpleNamespace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PIL import Image

from sku_board import backend, cod_prompt_atelier as atelier, cod_prompt_render as render
from sku_board.cod_prompt_contract import compile_execution_prompt
from sku_board.tests.test_cod_prompt_contract import form_fixture, references_fixture


class CodPromptRenderTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(prefix="atelier-render-test-")
        self.addCleanup(self.temp.cleanup)
        store_patch = patch.object(atelier, "_root", return_value=Path(self.temp.name))
        store_patch.start()
        self.addCleanup(store_patch.stop)
        jobs_patch = patch.object(backend, "_AI_IMAGE_JOBS", {})
        jobs_patch.start()
        self.addCleanup(jobs_patch.stop)
        self.actor = {"username": "atelier-render-test", "role": "admin"}
        self.form = form_fixture()
        buffer = BytesIO()
        Image.new("RGB", (8, 8), "coral").save(buffer, "PNG")
        self.png = buffer.getvalue()
        self.references = [("reference.png", self.png, "image/png")]
        self.prompt = compile_execution_prompt(self.form, "EXACT AI MASTER #fffaf0; 20% OFF", {"page": 1, "modelPrompt": "EXACT PAGE: USB充电。A local German desk scene, unique diagonal headline and the supplied 20% OFF badge."}, references_fixture(self.png))
        self.spec = {"prompt": self.prompt, "form": self.form, "referenceImages": self.references, "fingerprint": "fingerprint-fixture"}

    def fields(self):
        return {"atelierProjectId": "a" * 32, "atelierRevision": 2, "atelierPageNumber": 1,
                "atelierFingerprint": "fingerprint-fixture", "prompt": self.prompt,
                "count": 1, "size": "750x1000", "model": "gpt-image-2", "quality": "medium"}

    def test_submission_uses_server_version_instead_of_client_prompt(self):
        with patch.object(atelier, "get_render_spec", return_value=self.spec), patch.object(backend, "start_ai_image_job", return_value={"ok": True, "pending": True, "jobId": "AIJ-EXAMPLE"}) as start:
            result = render.start_render("a" * 32, {"revision": 2, "pageNumber": 1, "prompt": "untrusted client rewrite"}, self.actor)
        self.assertEqual(result["revision"], 2)
        submitted = start.call_args.args[1]
        self.assertEqual(submitted["prompt"], self.prompt)
        self.assertNotIn("suiteKey", submitted)
        self.assertEqual(submitted["size"], "750x1000")

    def test_tampered_prompt_canvas_or_reference_is_rejected(self):
        with patch.object(atelier, "get_render_spec", return_value=self.spec):
            for replacement in ({"prompt": "old product"}, {"size": "1024x1024"}, {"atelierFingerprint": "old"}, {"suiteKey": "cod-country-landing-30"}):
                fields = {**self.fields(), **replacement}
                with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                    render.validate_execution(fields, self.actor, fields["prompt"])
        with self.assertRaises(ValueError):
            render.validate_references(self.spec, [("reference.png", b"different same-name image", "image/png")])

    def test_actual_generation_bypasses_legacy_compiler_and_preserves_sent_prompt(self):
        uploads = {"reference0": SimpleNamespace(filename="reference.png", file=BytesIO(self.png))}
        image_result = [(self.png, "image/png")]
        material = {"id": "image-fixture", "previewUrl": "/api/sku-board/ai-image-output/image-fixture"}
        with ExitStack() as stack:
            stack.enter_context(patch.object(atelier, "get_render_spec", return_value=self.spec))
            record = stack.enter_context(patch.object(atelier, "record_material", return_value={"ok": True}))
            legacy = stack.enter_context(patch.object(backend, "build_ai_image_suite_prompts", side_effect=AssertionError("Atelier may not call legacy planner")))
            enhancer = stack.enter_context(patch.object(backend, "enhance_single_ai_image_prompt_with_open_prompts", side_effect=AssertionError("Atelier may not rewrite the prompt")))
            stack.enter_context(patch.object(backend, "shared_ai_director_open_prompts_enabled", return_value=True))
            stack.enter_context(patch.object(backend, "normalize_ai_image_skill_meta", return_value={}))
            stack.enter_context(patch.object(backend, "chatgpt2api_image_tasks_enabled", return_value=True))
            transport = stack.enter_context(patch.object(backend, "generate_ai_image_tasks_with_transient_retry", return_value=image_result))
            stack.enter_context(patch.object(backend, "save_ai_image_outputs", return_value=([material], [material["previewUrl"]])))
            result = backend.generate_ad_launch_ai_image_edit(self.fields(), uploads, self.actor)
        self.assertFalse(legacy.called)
        self.assertFalse(enhancer.called)
        self.assertEqual(transport.call_args.kwargs["prompt"], self.prompt)
        self.assertEqual(transport.call_args.kwargs["quality"], "medium")
        self.assertEqual(transport.call_args.kwargs["size"], "750x1000")
        self.assertEqual(result["pageNumber"], 1)
        self.assertEqual(result["revision"], 2)
        self.assertTrue(record.called)


if __name__ == "__main__":
    unittest.main()
