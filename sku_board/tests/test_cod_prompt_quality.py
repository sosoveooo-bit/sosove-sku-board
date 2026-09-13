"""Prompt quality is tested with local fixtures; no configured model is called."""
from __future__ import annotations

import copy
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from sku_board import cod_prompt_atelier as atelier
from sku_board.cod_prompt_contract import normalize_form
from sku_board.cod_prompt_quality import assess, normalize_ai_issues
from sku_board.tests import test_cod_prompt_atelier as fixtures


def content(market="JP"):
    form = normalize_form({"product": "冷冻烤虾", "market": market, "main": 2, "detail": 2,
                           "points": ["整只大虾", "香辣烧烤"], "style": "高冲击COD，大标题、多宫格；奶油白红色"})
    outline = [{"page": number, "sourcePointIndexes": [1] if number % 2 else [2],
                "title": f"主题{number}", "focus": form["points"][(number - 1) % 2], "archetype": "benefit"}
               for number in range(1, 5)]
    pages = [{**entry, "headline": headline, "modelPrompt": f"冷冻烤虾第{entry['page']}页，{scene}，鲜红奶油白统一，实拍商品与当前场景相关道具，大字标题和结构图文排版。"}
             for entry, headline, scene in zip(outline, ["家族で楽しむ一皿", "手軽な食事の準備", "焼きえびの香ばしさ", "商品情報"],
                                                ["整虾大特写展现形状", "日本家庭厨房用餐场景", "自然质感细节放大", "产品规格用严谨表格显示"])]
    hooks = [{"source": form["points"][0], "variants": [
        {"type": "pain", "text": "献立に迷う夜に"}, {"type": "effect", "text": "一皿で食卓を華やかに"},
        {"type": "scene", "text": "家族で楽しむ焼きえび"}]},
        {"source": form["points"][1], "variants": [
            {"type": "pain", "text": "いつもの食事にひと工夫"}, {"type": "effect", "text": "香ばしさを楽しもう"},
            {"type": "scene", "text": "週末のおうちごはんに"}]}]
    return form, "冷冻烤虾专属统一红白高密度COD方案，静态商品摄影。", outline, pages, hooks


class QualityRulesTests(unittest.TestCase):
    def test_natural_script_and_all_kanji_titles_do_not_claim_language_guarantee(self):
        inputs = content()
        original = copy.deepcopy(inputs)
        report = assess(*inputs)
        self.assertEqual(report["status"], "checked", report["issues"])
        self.assertEqual(inputs, original)
        self.assertTrue(report["advisory"])
        self.assertIn("不代表", report["summary"])
        self.assertEqual(report["repairablePages"], [])

    def test_language_check_only_targets_visible_fields(self):
        inputs = content()
        inputs[3][0]["headline"] = "This delicious product is perfect for dinner"
        inputs[3][1]["headline"] = "这款产品让你轻松做饭"
        report = assess(*inputs)
        self.assertEqual(report["repairablePages"], [1, 2])
        self.assertTrue(all(issue["field"] == "headline" for issue in report["issues"]))
        inputs[3][1]["headline"] = "毎日健康管理"
        self.assertNotIn(2, assess(*inputs)["repairablePages"])
        korean = content("KR")
        korean[3][0]["headline"] = "가족과 함께 즐기는 한 접시"
        self.assertNotIn(1, assess(*korean)["repairablePages"])

    def test_identical_hook_angles_and_cross_source_copy_are_actionable(self):
        inputs = content()
        inputs[4][0]["variants"][1]["text"] = inputs[4][0]["variants"][0]["text"]
        inputs[4][1]["variants"][1]["text"] = inputs[4][0]["variants"][0]["text"]
        report = assess(*inputs)
        self.assertEqual(report["repairableHookSources"], [1, 2])
        self.assertEqual(report["repairablePages"], [])
        self.assertFalse(report["requiresFullRegeneration"])

    def test_repeated_prompt_normalizes_page_markers_not_product_measurements(self):
        inputs = content()
        first = inputs[3][0]["modelPrompt"]
        inputs[3][1]["modelPrompt"] = first.replace("第1页", "第2页")
        inputs[3][2]["modelPrompt"] = first.replace("第1页", "Page 3")
        inputs[3][3]["modelPrompt"] = first.replace("第1页", "第4页") + " 保留真实商品重量30g。"
        report = assess(*inputs)
        repeated = [item["page"] for item in report["issues"] if item["code"] == "repeated_prompt"]
        self.assertEqual(repeated, [2, 3])

    def test_specific_identity_quantity_and_reference_mismatch_only(self):
        inputs = content()
        inputs[0]["points"].append("1.9英寸显示屏和300mAh电池")
        inputs[2][0]["sourcePointIndexes"].append(3)
        inputs[3][1]["modelPrompt"] += " 当前唯一商品：旧手表。屏幕2.1英寸，电池500mAh；Image9用于展示。"
        inputs[3][2]["modelPrompt"] += " 日本家庭厨房里的人物可以穿围裙或背包，不涉及其他商品功能。"
        report = assess(*inputs, references=[])
        codes = {item["code"] for item in report["issues"] if item["page"] == 2}
        self.assertEqual(codes, {"product_identity", "quantity_mismatch", "reference_binding"})
        self.assertNotIn(3, report["repairablePages"])

    def test_uncovered_sources_and_wrong_master_require_explicit_full_regeneration(self):
        inputs = content()
        inputs[2][:] = []
        inputs = (inputs[0], "当前唯一商品：旧手表。", *inputs[2:])
        report = assess(*inputs)
        self.assertTrue(report["requiresFullRegeneration"])
        self.assertEqual(report["coverage"]["missingSourcePointIndexes"], [1, 2])

    def test_reference_count_and_input_fingerprint_are_exact(self):
        inputs = content()
        reference = {"index": 1, "sha256": "a" * 64, "role": "product"}
        one = assess(*inputs, references=[reference])
        two = assess(*inputs, references=[{**reference, "role": "layout"}])
        self.assertNotEqual(one["inputFingerprint"], two["inputFingerprint"])
        self.assertEqual(one["coverage"]["referenceCount"], 1)
        inputs[0]["quality"] = "medium"
        self.assertEqual(one["inputFingerprint"], assess(*inputs, references=[reference])["inputFingerprint"])

    def test_ai_review_requires_scoped_fields_and_quoted_evidence(self):
        good = {"issues": [{"page": 2, "code": "ai_language", "field": "headline", "message": "改成自然日语", "evidence": "不自然"}]}
        self.assertEqual(normalize_ai_issues(good, allowed_pages={2}, allowed_hook_sources=set(), global_allowed=False)[0]["page"], 2)
        for change in ({"page": 99}, {"page": 0}, {"evidence": ""}, {"field": "masterPrompt"}, {"code": "delete_all"}):
            bad = {"issues": [{**good["issues"][0], **change}]}
            with self.assertRaises(ValueError):
                normalize_ai_issues(bad, allowed_pages={2}, allowed_hook_sources=set(), global_allowed=False)


class ReviewDirector(fixtures.FakeDirector):
    def __init__(self):
        super().__init__()
        self.review_hook = None

    def invoke_ai_director_chat(self, settings, messages):
        text = messages[-1]["content"]
        text = text[0]["text"] if isinstance(text, list) else text
        context = json.loads(text.split("CURRENT_PRODUCT_DATA_JSON:\n", 1)[1])
        if "reviewKind" not in context:
            return super().invoke_ai_director_chat(settings, messages)
        self.calls.append(("review", copy.deepcopy(context)))
        settings["_lastDirectorCall"] = {"requestedModel": settings["model"], "model": "review-exact-model",
                                        "fallbackUsed": True, "attempts": [{"model": "review-exact-model", "status": "ok"}]}
        result = self.review_hook(context, settings) if self.review_hook else {"issues": []}
        return json.dumps(result, ensure_ascii=False), 7


class QualityIntegrationTests(unittest.TestCase):
    save = fixtures.AtelierTests.save
    generate = fixtures.AtelierTests.generate

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="atelier-quality-test-")
        self.director = ReviewDirector()
        self.root_patch = patch.object(atelier, "_root", return_value=Path(self.directory.name))
        self.backend_patch = patch.object(atelier, "_backend", return_value=self.director)
        self.thread_patch = patch.object(atelier.threading, "Thread", fixtures.ImmediateThread)
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

    def review(self, project, mode="rules"):
        atelier.review_project(project["id"], {"revision": project["revision"], "mode": mode}, fixtures.ACTOR)
        return atelier.get_project(project["id"], fixtures.ACTOR)["project"]

    def set_report_issues(self, project, issues):
        with atelier._LOCK:
            document = atelier._read(atelier._owner(fixtures.ACTOR), project["id"])
            version = atelier._version(document)
            report = atelier.finalize_report(issues, source="ai", total=len(version["suitePages"]), checked=len(version["suitePages"]),
                                            fingerprint=atelier._content_fingerprint(version))
            version["qualityReport"] = report
            atelier._write(atelier._owner(fixtures.ACTOR), document)

    def test_rules_available_without_model_do_not_alter_saved_prompts_or_counts(self):
        project = self.generate(self.save())
        self.assertEqual(project["status"], "complete")
        self.assertEqual(project["qualityReport"]["source"], "rules")
        self.director.settings["enabled"] = False
        self.director.calls.clear()
        result = self.review(project)
        self.assertEqual(result["revision"], project["revision"])
        self.assertEqual(result["suitePages"], project["suitePages"])
        self.assertEqual(result["progress"]["completed"], 10)
        self.assertEqual(self.director.calls, [])

    def test_manual_new_version_rechecks_without_modifying_original(self):
        project = self.generate(self.save())
        old_fingerprint = project["qualityReport"]["inputFingerprint"]
        edited = atelier.edit_page(project["id"], {"revision": project["revision"], "pageNumber": 2,
                 "modelPrompt": project["suitePages"][0]["modelPrompt"]}, fixtures.ACTOR)["project"]
        self.assertNotEqual(edited["qualityReport"]["inputFingerprint"], old_fingerprint)
        self.assertIn(2, edited["qualityReport"]["repairablePages"])
        self.assertEqual(atelier.get_project(project["id"], fixtures.ACTOR, project["revision"])["project"]["qualityReport"], project["qualityReport"])

    def test_ai_review_batches_exact_metadata_and_no_mutation(self):
        project = self.generate(self.save(fixtures.form(main=30, detail=40)))
        self.director.calls.clear()
        result = self.review(project, "ai")
        batches = [context for stage, context in self.director.calls if stage == "review"]
        self.assertEqual(len(batches), 16)
        self.assertTrue(all(len(context["reviewPages"]) <= 5 and len(context["reviewHooks"]) <= 12 for context in batches))
        self.assertEqual(result["qualityReport"]["source"], "ai")
        self.assertEqual(result["qualityReport"]["director"]["activeModel"], "review-exact-model")
        self.assertTrue(result["qualityReport"]["director"]["fallbackUsed"])
        self.assertEqual(result["suitePages"], project["suitePages"])
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["revision"], project["revision"])
        self.assertEqual(result["progress"], project["progress"])

    def test_invalid_ai_evidence_marks_review_failed_but_preserves_complete_generation(self):
        project = self.generate(self.save())
        self.director.review_hook = lambda context, settings: {"issues": [{"page": 0, "code": "ai_source_mismatch", "field": "masterPrompt",
              "message": "捏造的错误", "evidence": "不存在的内容"}]} if context["reviewKind"] == "suite" else {"issues": []}
        result = self.review(project, "ai")
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["qualityReport"]["status"], "error")
        self.assertIn("证据", result["qualityReport"]["error"])
        self.assertEqual(result["masterPrompt"], project["masterPrompt"])

    def test_repair_only_flagged_pages_and_hook_sources_in_new_version(self):
        project = self.generate(self.save(image=True))
        issues = [{"page": 3, "code": "ai_layout", "severity": "warning", "field": "modelPrompt", "message": "厨房改成庭院烧烤，围绕本页卖点"},
                  {"page": 0, "code": "identical_hook", "severity": "warning", "field": "hooks", "message": "三种角度不同表达", "sourcePointIndex": 2}]
        self.set_report_issues(project, issues)
        self.director.calls.clear()
        repaired = self.generate(project, "repair")
        self.assertEqual(repaired["status"], "complete", repaired["error"])
        self.assertEqual(repaired["revision"], project["revision"] + 1)
        self.assertEqual([(stage, [item["page"] for item in context.get("outline", [])]) for stage, context in self.director.calls], [("hooks", []), ("pages", [3])])
        for index in range(10):
            if index != 2:
                self.assertEqual(repaired["suitePages"][index], project["suitePages"][index])
        self.assertEqual(repaired["hooks"][0], project["hooks"][0])
        self.assertEqual(repaired["masterPrompt"], project["masterPrompt"])
        self.assertEqual(self.director.calls[-1][1]["repairFindings"][0]["page"], 3)
        self.assertEqual(repaired["repair"]["sourceRevision"], project["revision"])

    def test_hook_only_repair_does_not_rewrite_any_pages(self):
        project = self.generate(self.save())
        self.set_report_issues(project, [{"page": 0, "code": "identical_hook", "severity": "warning", "field": "hooks", "message": "文案不同表达", "sourcePointIndex": 1}])
        self.director.calls.clear()
        repaired = self.generate(project, "repair")
        self.assertEqual([stage for stage, _ in self.director.calls], ["hooks"])
        self.assertEqual(repaired["suitePages"], project["suitePages"])

    def test_global_report_and_stale_report_cannot_silently_regenerate_whole_suite(self):
        project = self.generate(self.save())
        self.set_report_issues(project, [{"page": 0, "code": "ai_source_mismatch", "severity": "warning", "field": "masterPrompt", "message": "全局串品"}])
        self.director.calls.clear()
        with self.assertRaisesRegex(ValueError, "重新生成整套"):
            self.generate(project, "repair")
        self.assertEqual(self.director.calls, [])
        with atelier._LOCK:
            owner = atelier._owner(fixtures.ACTOR)
            document = atelier._read(owner, project["id"])
            atelier._version(document)["qualityReport"]["inputFingerprint"] = "old"
            atelier._write(owner, document)
        with self.assertRaisesRegex(ValueError, "过期"):
            self.generate(project, "repair")

    def test_repair_failure_can_resume_only_the_missing_target_with_original_advice(self):
        project = self.generate(self.save())
        self.set_report_issues(project, [{"page": 3, "code": "ai_layout", "severity": "warning", "field": "modelPrompt", "message": "本页增加真实厨房动作"}])

        def broken(stage, context, settings):
            if stage == "pages":
                return {"pages": []}

        self.director.hook = broken
        partial = self.generate(project, "repair")
        self.assertEqual(partial["status"], "partial")
        self.assertEqual(len(partial["suitePages"]), 9)
        self.assertEqual(partial["qualityReport"]["repairablePages"], sorted(set(partial["qualityReport"]["repairablePages"])))
        self.director.hook = None
        self.director.calls.clear()
        completed = self.generate(partial, "resume")
        self.assertEqual(completed["status"], "complete")
        self.assertEqual([entry["page"] for entry in self.director.calls[0][1]["outline"]], [3])
        self.assertEqual(self.director.calls[0][1]["repairFindings"][0]["message"], "本页增加真实厨房动作")
        self.assertEqual(completed["suitePages"][0], project["suitePages"][0])

    def test_ai_review_valid_page_and_hook_evidence_is_retained_and_repairable(self):
        project = self.generate(self.save())

        def review(context, settings):
            if context["reviewPages"] and context["reviewPages"][0]["page"] == 1:
                return {"issues": [{"page": 1, "code": "ai_language", "severity": "warning", "field": "headline",
                        "message": "此标题应改写为自然德语，保留具体产品卖点。", "evidence": context["reviewPages"][0]["headline"]}]}
            if context["reviewHooks"]:
                source = context["reviewHooks"][0]
                return {"issues": [{"page": 0, "code": "ai_source_mismatch", "severity": "warning", "field": "hooks",
                        "sourcePointIndex": source["sourcePointIndex"], "message": "围绕这一条原始卖点改写场景钩子。",
                        "evidence": source["variants"][0]["text"]}]}
            return {"issues": []}

        self.director.review_hook = review
        result = self.review(project, "ai")
        self.assertEqual(result["qualityReport"]["status"], "warning")
        self.assertEqual(result["qualityReport"]["source"], "ai")
        self.assertIn(1, result["qualityReport"]["repairablePages"])
        self.assertIn(1, result["qualityReport"]["repairableHookSources"])
        self.assertFalse(result["qualityReport"]["requiresFullRegeneration"])

    def test_ai_review_ownership_and_revision_guards(self):
        project = self.generate(self.save())
        with self.assertRaises(ValueError):
            atelier.review_project(project["id"], {"revision": project["revision"], "mode": "rules"}, fixtures.OTHER)
        current = self.save(fixtures.form(product="旅行背包"), project=project)
        with self.assertRaisesRegex(ValueError, "已更新"):
            self.review(project)
        self.assertEqual(atelier.get_project(current["id"], fixtures.ACTOR)["project"]["qualityReport"]["status"], "not_checked")

    def test_orphaned_review_restores_complete_prompts_and_retryable_quality(self):
        project = self.generate(self.save())
        with atelier._LOCK:
            owner = atelier._owner(fixtures.ACTOR)
            document = atelier._read(owner, project["id"])
            current = atelier._version(document)
            current["_reviewPriorStatus"] = current["status"]
            current["_reviewPriorProgress"] = copy.deepcopy(current["progress"])
            current["status"] = "reviewing"
            current["progress"]["stage"] = "reviewing"
            current["_runId"] = "dead-review-worker"
            atelier._write(owner, document)
        result = atelier.get_project(project["id"], fixtures.ACTOR)["project"]
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["qualityReport"]["status"], "error")
        self.assertEqual(result["suitePages"], project["suitePages"])

    def test_cancelled_review_late_response_never_overwrites_report(self):
        project = self.generate(self.save())
        self.thread_patch.stop()
        entered, released, finished = threading.Event(), threading.Event(), threading.Event()
        original = atelier._review_worker

        def observe(*args):
            try:
                original(*args)
            finally:
                finished.set()

        def block(context, settings):
            entered.set()
            if not released.wait(5):
                raise AssertionError("test did not release reviewer")
            return {"issues": []}

        self.director.review_hook = block
        with patch.object(atelier, "_review_worker", side_effect=observe):
            started = atelier.review_project(project["id"], {"revision": project["revision"], "mode": "ai"}, fixtures.ACTOR)["project"]
            try:
                self.assertEqual(started["status"], "reviewing")
                self.assertTrue(entered.wait(5))
                cancelled = atelier.cancel_generation(project["id"], {"revision": project["revision"]}, fixtures.ACTOR)["project"]
            finally:
                released.set()
                self.assertTrue(finished.wait(5))
        result = atelier.get_project(project["id"], fixtures.ACTOR)["project"]
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["qualityReport"], cancelled["qualityReport"])

    def test_ai_review_late_response_cannot_replace_changed_product(self):
        project = self.generate(self.save())
        self.thread_patch.stop()
        entered, released, finished = threading.Event(), threading.Event(), threading.Event()
        original = atelier._review_worker

        def observe(*args):
            try:
                original(*args)
            finally:
                finished.set()

        def block(context, settings):
            entered.set()
            if not released.wait(5):
                raise AssertionError("test did not release reviewer")
            return {"issues": []}

        self.director.review_hook = block
        with patch.object(atelier, "_review_worker", side_effect=observe):
            running = atelier.review_project(project["id"], {"revision": project["revision"], "mode": "ai"}, fixtures.ACTOR)["project"]
            try:
                self.assertTrue(entered.wait(5))
                replacement = self.save(fixtures.form(product="轻便旅行背包"), project=running)
            finally:
                released.set()
                self.assertTrue(finished.wait(5))
        current = atelier.get_project(project["id"], fixtures.ACTOR)["project"]
        self.assertEqual(current["revision"], replacement["revision"])
        self.assertEqual(current["qualityReport"]["status"], "not_checked")
        self.assertEqual(current["suitePages"], [])


if __name__ == "__main__":
    unittest.main()
