"""Deterministic Atelier state/transport tests; these never call a live model."""

from __future__ import annotations

import copy
import json
import tempfile
import threading
import unittest
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from sku_board import cod_prompt_atelier as atelier
from sku_board.cod_prompt_contract import compile_execution_prompt


ACTOR = {"username": "atelier-test", "role": "designer"}
OTHER = {"username": "another-user", "role": "admin"}


def form(product="冷冻香辣烤虾", main=5, detail=5, market="DE"):
    return {"product": product, "market": market, "main": main, "detail": detail,
            "size": "750x1000", "points": ["整只大虾", "香辣烧烤"], "style": "奶油白与鲜红，丰富排版",
            "allowPromo": True, "salePrice": "€19.99", "codText": "Nachnahme"}


def image_upload(color="red", name="same-name.png"):
    from PIL import Image

    output = BytesIO()
    Image.new("RGB", (2, 2), color).save(output, format="PNG")
    return SimpleNamespace(filename=name, file=BytesIO(output.getvalue()))


class ImmediateThread:
    """Make normal transport tests synchronous without changing worker logic."""

    def __init__(self, target, args, **kwargs):
        self.target, self.args = target, args

    def start(self):
        self.target(*self.args)


class FakeDirector:
    def __init__(self):
        self.settings = {"enabled": True, "model": "gpt-5.6-sol", "baseUrl": "https://test.invalid/v1",
                         "apiKey": "never-expose-test-secret", "visionEnabled": True}
        self.calls = []
        self.hook = None
        self.contact_sheets = []

    def can_use_ai_image(self, actor):
        return actor.get("role") in {"admin", "designer"}

    def load_ai_director_settings(self):
        return copy.deepcopy(self.settings)

    def public_ai_director_settings(self, settings):
        return {"model": settings["model"], "enabled": True, "configured": True}

    def read_ai_image_upload(self, item, label):
        return item.filename, item.file.read(), "image/png"

    def ai_director_reference_contact_sheet(self, originals, **kwargs):
        self.contact_sheets.append(originals)
        return originals[0]

    def ai_director_reference_data_url(self, reference):
        return "data:image/png;base64,fake-reference-for-mocked-transport-only"

    def parse_ai_director_json(self, content):
        return json.loads(content)

    @staticmethod
    def outline(context):
        current = context["form"]
        total = current["main"] + current["detail"]
        pages = []
        for number in range(1, total + 1):
            archetype = ("product-info" if number == total else "pain-grid" if number == 2 and current["main"] >= 2
                         else "comparison" if number == 3 and total >= 4 else "scene")
            pages.append({"page": number, "title": f"{current['product']} 页面 {number}",
                          "focus": current["points"][(number - 1) % len(current["points"])],
                          "headline": f"{current['market']} Produkt {number}", "archetype": archetype,
                          "sourcePointIndexes": list(range(1, len(current["points"]) + 1)) if number == 1 else []})
        return {"masterPrompt": f"本套只展示{current['product']}，{current['style']}，当地人物真实使用场景，COD冲击效果。",
                "productSummary": current["product"], "visualDNA": {"palette": current["style"]},
                "outline": pages,
                "hooks": [{"source": point, "variants": [{"type": kind, "text": f"{current['market']} {point} {kind}"}
                           for kind in ("pain", "effect", "scene")]} for point in list(dict.fromkeys(current["points"]))[:12]]}

    @staticmethod
    def hooks(context):
        return {"hooks": [{"sourcePointIndex": source["sourcePointIndex"], "source": "原始卖点",
                           "variants": [{"type": kind, "text": f"{context['form']['market']} {source['source']} {kind}"}
                           for kind in ("pain", "effect", "scene")]} for source in context["requestedHookSources"]]}

    @staticmethod
    def pages(context):
        return {"pages": [{**entry, "modelPrompt":
                  f"{context['form']['product']} 第{entry['page']}页：围绕{entry['focus']}，产品大特写、当地人物使用镜头、"
                  f"三层图文信息排版，保留奶油白和鲜红配色，自然当地语言标题，当前参考图结构一致。"
                  f"修订要求：{context.get('rewriteInstruction', '')}"} for entry in context["outline"]]}

    def invoke_ai_director_chat(self, settings, messages):
        content = messages[-1]["content"]
        content = content[0]["text"] if isinstance(content, list) else content
        context = json.loads(content.split("CURRENT_PRODUCT_DATA_JSON:\n", 1)[1])
        stage = "hooks" if "requestedHookSources" in context else "pages" if "outline" in context else "outline"
        self.calls.append((stage, copy.deepcopy(context)))
        settings["_lastDirectorCall"] = {"requestedModel": settings["model"], "model": settings["model"],
                                         "fallbackUsed": False, "attempts": [{"model": settings["model"], "status": "ok"}]}
        result = self.hook(stage, context, settings) if self.hook else None
        if result is None:
            result = self.outline(context) if stage == "outline" else self.hooks(context) if stage == "hooks" else self.pages(context)
        return (result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)), 12


class AtelierTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="cod-atelier-test-")
        self.director = FakeDirector()
        self.root_patch = patch.object(atelier, "_root", return_value=Path(self.directory.name))
        self.backend_patch = patch.object(atelier, "_backend", return_value=self.director)
        self.thread_patch = patch.object(atelier.threading, "Thread", ImmediateThread)
        self.root_patch.start()
        self.backend_patch.start()
        self.thread_patch.start()
        with atelier._LOCK:
            atelier._RUNS.clear()

    def tearDown(self):
        self.thread_patch.stop()
        self.backend_patch.stop()
        self.root_patch.stop()
        self.directory.cleanup()

    def save(self, current_form=None, project=None, image=False, color="red", roles=None):
        fields = {"form": json.dumps(current_form or form(), ensure_ascii=False)}
        if project:
            fields.update(projectId=project["id"], revision=project["revision"])
        if roles:
            fields["referenceBindings"] = json.dumps(roles)
        files = {"reference0": image_upload(color)} if image else {}
        if image:
            fields["referencesMode"] = "replace"
        return atelier.save_project_upload(fields, files, ACTOR)["project"]

    def generate(self, project, mode="fresh", **kwargs):
        started = atelier.start_generation(project["id"], {"revision": project["revision"], "mode": mode, **kwargs}, ACTOR)
        return atelier.get_project(project["id"], ACTOR, started["project"]["revision"])["project"]

    def test_saved_project_is_private_and_original_references_are_integrity_checked(self):
        project = self.save(image=True)
        self.assertEqual(project["references"][0]["index"], 1)
        self.assertIn("?revision=1", project["references"][0]["previewUrl"])
        self.assertEqual(atelier.list_projects(OTHER)["projects"], [])
        with self.assertRaises(ValueError):
            atelier.get_project(project["id"], OTHER)
        with self.assertRaises(ValueError):
            atelier.read_reference(project["id"], 1, OTHER)
        data, mime = atelier.read_reference(project["id"], 1, ACTOR)
        self.assertTrue(data.startswith(b"\x89PNG"))
        self.assertEqual(mime, "image/png")
        with self.assertRaises(ValueError):
            atelier.get_project("../../other", ACTOR)
        with self.assertRaises(PermissionError):
            atelier.list_projects({"username": "nobody", "role": "viewer"})

    def test_same_name_new_image_or_role_creates_new_fingerprint_and_preserves_old(self):
        first = self.save(image=True, color="red")
        second = self.save(project=first, image=True, color="blue")
        self.assertEqual(first["references"][0]["name"], second["references"][0]["name"])
        self.assertNotEqual(first["fingerprint"], second["fingerprint"])
        old_bytes, _ = atelier.read_reference(first["id"], 1, ACTOR, revision=1)
        new_bytes, _ = atelier.read_reference(first["id"], 1, ACTOR, revision=2)
        self.assertNotEqual(old_bytes, new_bytes)
        third = self.save(project=second, roles=[{"index": 1, "role": "layout"}])
        self.assertNotEqual(second["fingerprint"], third["fingerprint"])
        with self.assertRaises(ValueError):
            self.save(project=first)

    def test_batches_respect_five_plus_five_and_exact_execution_prompt(self):
        project = self.generate(self.save(image=True))
        self.assertEqual(project["status"], "complete", project["error"])
        self.assertEqual([len(context["outline"]) for stage, context in self.director.calls if stage == "pages"], [5, 5])
        self.assertEqual(len(project["suitePages"]), 10)
        self.assertEqual(project["suitePages"][-1]["archetype"], "product-info")
        self.assertEqual(project["director"]["activeModel"], "gpt-5.6-sol")
        spec = atelier.get_render_spec(project["id"], project["revision"], 1, ACTOR)
        self.assertEqual(spec["prompt"], project["suitePages"][0]["executionPrompt"])
        self.assertEqual(spec["prompt"], compile_execution_prompt(project["form"], project["masterPrompt"], project["suitePages"][0], project["references"]))
        self.assertIn("€19.99", spec["prompt"])
        self.assertNotIn("血糖", "\n".join(page["executionPrompt"] for page in project["suitePages"]))
        self.assertEqual({variant["type"] for variant in project["hooks"][0]["variants"]}, {"pain", "effect", "scene"})
        self.assertNotIn("never-expose-test-secret", json.dumps(project))
        self.assertNotIn("https://test.invalid", json.dumps(project))

    def test_maximum_seventy_pages_have_small_batches(self):
        project = self.generate(self.save(form(main=30, detail=40)))
        self.assertEqual(project["status"], "complete", project["error"])
        self.assertEqual(len(project["suitePages"]), 70)
        batches = [context for stage, context in self.director.calls if stage == "pages"]
        self.assertEqual(len(batches), 14)
        self.assertTrue(all(len(context["outline"]) <= 5 for context in batches))

    def test_sixty_source_hooks_are_batched_and_duplicate_input_is_not_lost(self):
        inputs = form(main=30, detail=40)
        inputs["points"] = [f"当前新品专属卖点 {number}" for number in range(1, 60)] + ["当前新品专属卖点 1"]
        project = self.generate(self.save(inputs))
        self.assertEqual(project["status"], "complete", project["error"])
        self.assertEqual(project["form"]["points"], inputs["points"])
        self.assertEqual(len(project["hooks"]), 59)
        hook_batches = [context["requestedHookSources"] for stage, context in self.director.calls if stage == "hooks"]
        self.assertEqual([len(batch) for batch in hook_batches], [12, 12, 12, 11])
        covered = {source for page in project["outline"] for source in page["sourcePointIndexes"]}
        self.assertEqual(covered, set(range(1, 61)))

    def test_partial_hook_batch_is_saved_and_resume_requests_only_missing_sources(self):
        inputs = form()
        inputs["points"] = [f"新品专属卖点 {number}" for number in range(1, 16)]

        def missing_hook(stage, context, settings):
            if stage == "hooks":
                hooks = self.director.hooks(context)
                hooks["hooks"] = hooks["hooks"][:1]
                return hooks

        self.director.hook = missing_hook
        partial = self.generate(self.save(inputs))
        self.assertEqual(partial["status"], "partial")
        self.assertEqual(len(partial["hooks"]), 13)
        self.assertEqual(partial["suitePages"], [])
        self.director.calls.clear()
        self.director.hook = None
        completed = self.generate(partial, "resume")
        self.assertEqual(completed["status"], "complete", completed["error"])
        self.assertEqual(self.director.calls[0][0], "hooks")
        self.assertEqual([source["sourcePointIndex"] for source in self.director.calls[0][1]["requestedHookSources"]], [14, 15])
        self.assertEqual(len(completed["hooks"]), 15)

    def test_partial_batch_is_saved_and_resume_only_fills_missing_pages(self):
        def broken_batch(stage, context, settings):
            if stage == "pages" and context["outline"][0]["page"] == 6:
                value = self.director.pages(context)
                value["pages"] = value["pages"][:2]
                return value

        self.director.hook = broken_batch
        partial = self.generate(self.save())
        self.assertEqual(partial["status"], "partial")
        self.assertEqual([page["page"] for page in partial["suitePages"]], list(range(1, 8)))
        self.director.calls.clear()
        self.director.hook = None
        completed = self.generate(partial, "resume")
        self.assertEqual(completed["revision"], partial["revision"])
        self.assertEqual(completed["status"], "complete", completed["error"])
        self.assertEqual([stage for stage, _ in self.director.calls], ["pages"])
        self.assertEqual([page["page"] for page in self.director.calls[0][1]["outline"]], [8, 9, 10])

    def test_model_failure_has_no_template_fallback_and_redacts_configuration(self):
        def fail(stage, context, settings):
            raise ValueError(f"failure {settings['apiKey']} {settings['baseUrl']} Bearer secret-token")

        self.director.hook = fail
        project = self.generate(self.save())
        self.assertEqual(project["status"], "error")
        self.assertEqual(project["masterPrompt"], "")
        self.assertEqual(project["suitePages"], [])
        self.assertEqual(len(self.director.calls), 1)
        self.assertNotIn("never-expose-test-secret", project["error"])
        self.assertNotIn("secret-token", project["error"])
        self.assertNotIn("https://test.invalid", project["error"])

    def test_unconfigured_director_does_not_create_generation_version(self):
        project = self.save()
        self.director.settings["enabled"] = False
        with self.assertRaises(ValueError):
            self.generate(project)
        current = atelier.get_project(project["id"], ACTOR)["project"]
        self.assertEqual(current["revision"], project["revision"])
        self.assertEqual(self.director.calls, [])

    def test_server_restart_marks_running_revision_recoverable(self):
        project = self.generate(self.save())
        owner = atelier._owner(ACTOR)
        with atelier._LOCK:
            document = atelier._read(owner, project["id"])
            version = atelier._version(document)
            version["suitePages"] = version["suitePages"][:5]
            version["status"] = "generating"
            version["_runId"] = "dead-worker-id"
            version["progress"] = {"stage": "pages", "completed": 5, "total": 10}
            atelier._write(owner, document)
        interrupted = atelier.get_project(project["id"], ACTOR)["project"]
        self.assertEqual(interrupted["status"], "partial")
        self.assertIn("服务重启", interrupted["error"])
        self.director.calls.clear()
        completed = self.generate(interrupted, "resume")
        self.assertEqual(completed["status"], "complete", completed["error"])
        self.assertEqual([stage for stage, _ in self.director.calls], ["pages"])

    def test_manual_edit_is_new_version_and_ai_single_page_rewrite_is_local(self):
        original = self.generate(self.save())
        exact_prompt = "这是一条手动修改后的商品图提示词：保持奶油白和鲜红配色，放大当前烤虾，加入德国家庭厨房使用场景和分层文案。"
        edited = atelier.edit_page(original["id"], {"revision": original["revision"], "pageNumber": 3, "modelPrompt": exact_prompt}, ACTOR)["project"]
        self.assertEqual(edited["revision"], original["revision"] + 1)
        self.assertEqual(edited["suitePages"][2]["modelPrompt"], exact_prompt)
        self.assertEqual(edited["suitePages"][0], original["suitePages"][0])
        historical = atelier.get_project(original["id"], ACTOR, original["revision"])["project"]
        self.assertEqual(historical["suitePages"][2], original["suitePages"][2])
        self.assertEqual(historical["currentRevision"], edited["revision"])
        self.director.calls.clear()
        rewritten = self.generate(edited, "page", pageNumber=4, instruction="改成庭院烧烤场景")
        self.assertEqual(rewritten["status"], "complete", rewritten["error"])
        self.assertEqual(len(self.director.calls), 1)
        self.assertEqual([page["page"] for page in self.director.calls[0][1]["outline"]], [4])
        self.assertIn("庭院烧烤", rewritten["suitePages"][3]["modelPrompt"])
        self.assertEqual(rewritten["suitePages"][2], edited["suitePages"][2])

    def test_archived_render_spec_and_gallery_are_bound_to_original_version(self):
        original = self.generate(self.save(image=True))
        current = self.save(form(product="柔软家居拖鞋"), project=original)
        spec = atelier.get_render_spec(original["id"], original["revision"], 1, ACTOR)
        self.assertIn("烤虾", spec["prompt"])
        stored = atelier.record_material(original["id"], original["revision"], 1,
                 {"id": "AI-EXAMPLE", "previewUrl": "/preview/example.png", "apiKey": "secret", "path": "private-path"}, ACTOR)["project"]
        self.assertEqual(stored["materials"][0]["revision"], original["revision"])
        self.assertNotIn("apiKey", stored["materials"][0])
        self.assertNotIn("path", stored["materials"][0])
        latest = atelier.get_project(current["id"], ACTOR)["project"]
        self.assertEqual(latest["materials"], [])
        self.assertEqual(latest["masterPrompt"], "")
        self.assertEqual(latest["form"]["product"], "柔软家居拖鞋")

    def test_real_worker_late_response_cannot_overwrite_changed_product(self):
        self.thread_patch.stop()
        entered, released, finished = threading.Event(), threading.Event(), threading.Event()
        original_worker = atelier._generation_worker

        def observed_worker(*args):
            try:
                original_worker(*args)
            finally:
                finished.set()

        def block(stage, context, settings):
            if stage == "outline":
                entered.set()
                if not released.wait(5):
                    raise AssertionError("test worker was not released")

        self.director.hook = block
        project = self.save()
        with patch.object(atelier, "_generation_worker", side_effect=observed_worker):
            running = atelier.start_generation(project["id"], {"revision": project["revision"], "mode": "fresh"}, ACTOR)["project"]
            try:
                self.assertTrue(entered.wait(5))
                replacement = self.save(form(product="轻便旅行背包"), project=running)
            finally:
                released.set()
                self.assertTrue(finished.wait(5))
        latest = atelier.get_project(project["id"], ACTOR)["project"]
        self.assertEqual(latest["revision"], replacement["revision"])
        self.assertEqual(latest["form"]["product"], "轻便旅行背包")
        self.assertEqual(latest["suitePages"], [])
        self.assertEqual(latest["status"], "draft")
        old = atelier.get_project(project["id"], ACTOR, running["revision"])["project"]
        self.assertEqual(old["status"], "cancelled")
        self.assertEqual(old["masterPrompt"], "")

    def test_cancel_during_second_batch_preserves_first_five(self):
        self.thread_patch.stop()
        entered, released, finished = threading.Event(), threading.Event(), threading.Event()
        original_worker = atelier._generation_worker

        def observed_worker(*args):
            try:
                original_worker(*args)
            finally:
                finished.set()

        def block(stage, context, settings):
            if stage == "pages" and context["outline"][0]["page"] == 6:
                entered.set()
                if not released.wait(5):
                    raise AssertionError("test worker was not released")

        self.director.hook = block
        project = self.save()
        with patch.object(atelier, "_generation_worker", side_effect=observed_worker):
            running = atelier.start_generation(project["id"], {"revision": project["revision"], "mode": "fresh"}, ACTOR)["project"]
            try:
                self.assertTrue(entered.wait(5))
                cancelled = atelier.cancel_generation(project["id"], {"revision": running["revision"]}, ACTOR)["project"]
            finally:
                released.set()
                self.assertTrue(finished.wait(5))
        self.assertEqual(cancelled["status"], "cancelled")
        latest = atelier.get_project(project["id"], ACTOR)["project"]
        self.assertEqual(len(latest["suitePages"]), 5)
        self.assertEqual(latest["status"], "cancelled")


if __name__ == "__main__":
    unittest.main()
