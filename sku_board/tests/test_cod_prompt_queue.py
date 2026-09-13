"""Render recovery and duplicate-submit tests. No live model/provider is used."""
from __future__ import annotations

import copy
import json
import tempfile
import threading
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from sku_board import backend, cod_prompt_atelier as atelier, cod_prompt_queue as queue, cod_prompt_render as render
from sku_board.cod_prompt_contract import compile_execution_prompt
from sku_board.tests.test_cod_prompt_atelier import image_upload
from sku_board.tests.test_cod_prompt_contract import form_fixture


ACTOR = {"username": "queue-owner", "role": "designer", "active": True}
OTHER = {"username": "different-owner", "role": "admin", "active": True}


class CodPromptQueueTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.directory = self.stack.enter_context(tempfile.TemporaryDirectory(prefix="atelier-queue-test-"))
        self.stack.enter_context(patch.object(atelier, "_root", return_value=Path(self.directory)))
        self.jobs = {}
        self.stack.enter_context(patch.object(backend, "_AI_IMAGE_JOBS", self.jobs))
        self.users = [copy.deepcopy(ACTOR), copy.deepcopy(OTHER)]
        self.stack.enter_context(patch.object(backend, "load_board", side_effect=lambda: {"users": self.users}))
        self.submissions = []
        self.job_status = "success"
        self.raise_after_persist = False
        self.raise_before_persist = False
        self.stack.enter_context(patch.object(backend, "start_ai_image_job", side_effect=self.submit))
        self.workers = []
        tests = self

        class ManualThread:
            def __init__(self, target, args, **kwargs):
                self.target, self.args = target, args

            def start(self):
                tests.workers.append(self)

        self.stack.enter_context(patch.object(queue, "_THREAD_FACTORY", ManualThread))
        self.stack.enter_context(patch.object(queue, "_POLL_SECONDS", 0))
        with queue._LOCK:
            queue._RUNS.clear()

    def tearDown(self):
        with queue._LOCK:
            queue._RUNS.clear()
        self.stack.close()

    def submit(self, mode, fields, actor, files):
        self.submissions.append((copy.deepcopy(fields), [(name, item.file.read()) for name, item in files.items()]))
        if self.raise_before_persist:
            raise OSError("test storage issue before job creation")
        job_id = f"AIJ-{len(self.submissions):014X}"
        self.jobs[job_id] = {
            "id": job_id, "owner": actor["username"], "payload": copy.deepcopy(fields),
            "status": self.job_status, "result": {"materials": [{"id": "asset-" + job_id}]},
            "error": "confirmed provider failure" if self.job_status == "error" else "",
        }
        if self.raise_after_persist:
            raise OSError("test interrupted response after persisted job")
        return {"ok": True, "pending": True, "jobId": job_id, "status": "queued"}

    def project(self, actor=ACTOR, product="便携榨汁杯", pages=3):
        form = form_fixture(product=product, main=1, detail=pages - 1)
        saved = atelier.save_project_upload({"form": form}, {"reference0": image_upload()}, actor)["project"]
        owner = atelier._owner(actor)
        with atelier._LOCK:
            document = atelier._read(owner, saved["id"])
            version = atelier._version(document)
            version["masterPrompt"] = f"{product} master unique bright COD style"
            version["status"] = "complete"
            version["suitePages"] = []
            for number in range(1, pages + 1):
                page = {"page": number, "modelPrompt": f"{product} 独立页面 {number} only supplied reference, scene, large title and unique angle"}
                page["executionPrompt"] = compile_execution_prompt(form, version["masterPrompt"], page, version["references"])
                version["suitePages"].append(page)
            atelier._write(owner, document)
        return atelier.get_project(saved["id"], actor)["project"]

    def start(self, project, actor=ACTOR, **options):
        return queue.start_queue(project["id"], {"revision": project["revision"], **options}, actor)["queue"]

    def run_workers(self):
        while self.workers:
            worker = self.workers.pop(0)
            worker.target(*worker.args)

    def latest(self, project, actor=ACTOR):
        return queue.list_queues(project["id"], actor, project["revision"])["queues"][0]

    def raw(self, project, run_id):
        return queue._read(atelier._owner(ACTOR), project["id"], run_id)

    def test_duplicate_clicks_share_one_run_and_submit_each_page_once(self):
        project = self.project()
        first = self.start(project)
        repeated = self.start(project)
        redo_while_running = self.start(project, mode="redo")
        self.assertEqual(first["id"], repeated["id"])
        self.assertEqual(first["id"], redo_while_running["id"])
        self.assertEqual(len(self.workers), 1)
        self.run_workers()
        final = self.latest(project)
        self.assertEqual(final["status"], "complete")
        self.assertEqual(final["completed"], 3)
        self.assertEqual([fields["atelierPageNumber"] for fields, _refs in self.submissions], [1, 2, 3])
        self.assertEqual(len({fields["atelierRequestKey"] for fields, _refs in self.submissions}), 3)
        self.assertEqual(self.start(project)["id"], first["id"])
        self.assertEqual(len(self.submissions), 3)

    def test_concurrent_start_and_direct_render_are_idempotent(self):
        project = self.project()
        results, errors = [], []
        gate = threading.Barrier(4)

        def click():
            try:
                gate.wait(timeout=3)
                results.append(self.start(project, pageNumbers=[1])["id"])
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=click) for _ in range(3)]
        for thread in threads:
            thread.start()
        gate.wait(timeout=3)
        for thread in threads:
            thread.join(timeout=3)
            self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(len(set(results)), 1)
        self.assertEqual(len(self.workers), 1)
        self.run_workers()
        self.assertEqual(len(self.submissions), 1)

        direct_results = []
        threads = [threading.Thread(target=lambda: direct_results.append(render.start_render(
            project["id"], {"revision": 1, "pageNumber": 2}, ACTOR))) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=3)
            self.assertFalse(thread.is_alive())
        self.assertEqual(len({value["jobId"] for value in direct_results}), 1)
        self.assertEqual(len(self.submissions), 2)

    def test_known_terminal_failures_are_not_blindly_retried_on_resume(self):
        project = self.project()
        self.job_status = "error"
        first = self.start(project)
        self.run_workers()
        self.assertEqual(self.latest(project)["status"], "error")
        self.assertEqual(len(self.submissions), 3)
        queue.resume_queue(project["id"], first["id"], {"revision": 1}, ACTOR)
        self.start(project)
        self.run_workers()
        self.assertEqual(len(self.submissions), 3)
        self.job_status = "success"
        redo = self.start(project, mode="redo", pageNumbers=[2])
        self.assertNotEqual(redo["id"], first["id"])
        self.run_workers()
        self.assertEqual(len(self.submissions), 4)
        self.assertEqual(self.latest(project)["status"], "complete")

    def test_completed_subset_is_reused_when_resuming_the_entire_suite(self):
        project = self.project()
        first = self.start(project, pageNumbers=[1])
        self.run_workers()
        # Even if the shared backend cache has expired, the durable page receipt
        # says it finished. The suite does not create a new page-1 request.
        self.jobs.clear()
        whole = self.start(project)
        self.assertNotEqual(whole["id"], first["id"])
        self.assertEqual(whole["pages"][0]["status"], "complete")
        self.assertEqual(whole["pages"][0]["reusedFromQueueId"], first["id"])
        self.run_workers()
        self.assertEqual([fields["atelierPageNumber"] for fields, _refs in self.submissions], [1, 2, 3])
        self.assertEqual(self.latest(project)["status"], "complete")
        self.assertEqual(self.latest(project)["completed"], 3)

    def test_failed_and_uncertain_subset_are_not_retried_via_larger_selection(self):
        project = self.project()
        self.raise_before_persist = True
        self.start(project, pageNumbers=[1])
        self.run_workers()
        self.raise_before_persist = False
        whole = self.start(project)
        self.assertEqual(whole["pages"][0]["status"], "needs_attention")
        self.run_workers()
        self.assertEqual(len(self.submissions), 1)
        self.assertEqual(self.latest(project)["status"], "needs_attention")

    def test_job_persisted_then_submit_throws_is_recovered_without_second_charge(self):
        project = self.project()
        self.raise_after_persist = True
        run = self.start(project, pageNumbers=[1])
        self.run_workers()
        final = self.latest(project)
        self.assertEqual(final["status"], "complete")
        self.assertEqual(len(self.submissions), 1)
        again = render.start_render(project["id"], queue._payload(self.raw(project, run["id"]), self.raw(project, run["id"])["pages"][0]), ACTOR)
        self.assertTrue(again["reusedJob"])
        self.assertEqual(len(self.submissions), 1)

    def test_uncertain_submission_and_expired_receipt_never_resubmit(self):
        project = self.project()
        self.raise_before_persist = True
        run = self.start(project)
        self.run_workers()
        self.assertEqual(self.latest(project)["status"], "needs_attention")
        self.assertEqual(self.latest(project)["pages"][0]["status"], "needs_attention")
        self.raise_before_persist = False
        queue.resume_queue(project["id"], run["id"], {"revision": 1}, ACTOR)
        self.run_workers()
        self.assertEqual(len(self.submissions), 1)
        self.assertEqual(self.latest(project)["status"], "needs_attention")
        with self.assertRaises(render.SubmissionUncertainError):
            saved = self.raw(project, run["id"])
            render.start_render(project["id"], queue._payload(saved, saved["pages"][0]), ACTOR)
        self.assertEqual(len(self.submissions), 1)

    def test_direct_receipt_survives_short_lived_job_cache(self):
        project = self.project()
        request = {"revision": 1, "pageNumber": 1}
        render.start_render(project["id"], request, ACTOR)
        self.jobs.clear()
        with self.assertRaises(render.SubmissionUncertainError):
            render.start_render(project["id"], request, ACTOR)
        self.assertEqual(len(self.submissions), 1)

    def test_restart_reuses_submitting_job_and_processes_never_submitted_pages(self):
        project = self.project()
        run = self.start(project)
        raw = self.raw(project, run["id"])
        raw["status"] = "running"
        raw["pages"][0]["status"] = "submitting"
        queue._write(raw)
        render.start_render(project["id"], queue._payload(raw, raw["pages"][0]), ACTOR)
        with queue._LOCK:
            queue._RUNS.clear()
        self.workers.clear()
        counts = queue.resume_queues_on_startup()
        self.assertEqual(counts["resumed"], 1)
        self.run_workers()
        self.assertEqual(self.latest(project)["status"], "complete")
        self.assertEqual(len(self.submissions), 3)

    def test_restart_missing_submitting_job_stops_not_charges_again(self):
        project = self.project()
        run = self.start(project)
        raw = self.raw(project, run["id"])
        raw["status"] = "running"
        raw["pages"][0]["status"] = "submitting"
        queue._write(raw)
        queue._RUNS.clear()
        self.workers.clear()
        queue.resume_queues_on_startup()
        self.run_workers()
        self.assertEqual(self.latest(project)["status"], "needs_attention")
        self.assertEqual(self.submissions, [])

    def test_outcome_uncertain_backend_restart_marker_stops_remaining_pages(self):
        project = self.project()
        run = self.start(project)
        raw = self.raw(project, run["id"])
        result = render.start_render(project["id"], queue._payload(raw, raw["pages"][0]), ACTOR)
        raw["pages"][0].update(status="running", jobId=result["jobId"], requestKey=result["requestKey"])
        queue._write(raw)
        self.jobs[result["jobId"]].update(status="error", atelierOutcomeUncertain=True)
        self.run_workers()
        self.assertEqual(self.latest(project)["status"], "needs_attention")
        self.assertEqual(len(self.submissions), 1)

    def test_closing_browser_is_not_needed_for_worker_to_finish(self):
        project = self.project(pages=4)
        self.start(project)
        # No GET, browser callback, next-page submission or followup is made.
        self.run_workers()
        document = json.loads(next((Path(self.directory) / atelier._owner(ACTOR) / project["id"] / "render-queues").glob("*.json")).read_text("utf-8"))
        self.assertEqual(document["status"], "complete")
        self.assertEqual(len(self.submissions), 4)

    def test_cancel_before_submission_is_persistent_and_explicit_resume_runs(self):
        project = self.project()
        run = self.start(project)
        queue.cancel_queue(project["id"], run["id"], {"revision": 1}, ACTOR)
        self.run_workers()
        self.assertEqual(self.submissions, [])
        self.assertEqual(self.latest(project)["status"], "paused")
        counts = queue.resume_queues_on_startup()
        self.assertEqual(counts["resumed"], 0)
        queue.resume_queue(project["id"], run["id"], {"revision": 1}, ACTOR)
        self.run_workers()
        self.assertEqual(len(self.submissions), 3)

    def test_resume_at_worker_exit_is_not_lost(self):
        project = self.project()
        run = self.start(project)
        queue.cancel_queue(project["id"], run["id"], {"revision": 1}, ACTOR)
        original_settle = queue._settle
        raced = []

        def resume_after_settle(record):
            original_settle(record)
            if not raced:
                raced.append(True)
                queue.resume_queue(project["id"], run["id"], {"revision": 1}, ACTOR)

        with patch.object(queue, "_settle", side_effect=resume_after_settle):
            self.run_workers()
        self.assertEqual(self.latest(project)["status"], "complete")
        self.assertEqual(len(self.submissions), 3)

    def test_cancel_keeps_polling_submitted_page_but_submits_no_more(self):
        project = self.project()
        self.job_status = "running"
        run = self.start(project)
        observed = threading.Event()
        original_get = render.get_render_job

        def observe(*args, **kwargs):
            observed.set()
            return original_get(*args, **kwargs)

        worker = self.workers.pop(0)
        with patch.object(render, "get_render_job", side_effect=observe):
            thread = threading.Thread(target=worker.target, args=worker.args)
            thread.start()
            try:
                self.assertTrue(observed.wait(timeout=3))
                stopped = queue.cancel_queue(project["id"], run["id"], {"revision": 1}, ACTOR)
                self.assertTrue(stopped["queue"]["cancelRequested"])
                for job in self.jobs.values():
                    job["status"] = "success"
                thread.join(timeout=3)
                self.assertFalse(thread.is_alive())
            finally:
                for job in self.jobs.values():
                    job["status"] = "success"
                thread.join(timeout=3)
        self.assertEqual(len(self.submissions), 1)
        final = self.latest(project)
        self.assertEqual(final["status"], "paused")
        self.assertEqual(final["completed"], 1)

    def test_old_versions_remain_bound_when_a_new_product_version_is_saved(self):
        project = self.project()
        run = self.start(project)
        atelier.save_project_upload({"projectId": project["id"], "revision": 1,
                                     "form": form_fixture(product="另一款户外帐篷"), "referencesMode": "keep"}, {}, ACTOR)
        self.run_workers()
        final = queue.list_queues(project["id"], ACTOR, 1)["queues"][0]
        self.assertEqual(final["id"], run["id"])
        self.assertEqual(final["status"], "complete")
        self.assertTrue(all(fields["atelierRevision"] == 1 and "便携榨汁杯" in fields["prompt"] for fields, _refs in self.submissions))
        self.assertEqual(queue.list_queues(project["id"], ACTOR, 2)["queues"], [])

    def test_editing_only_page_two_reuses_completed_unchanged_pages_across_versions(self):
        project = self.project()
        original = self.start(project)
        self.run_workers()
        edited = atelier.edit_page(project["id"], {"revision": 1, "pageNumber": 2,
                    "modelPrompt": "第二页仅修改为全新的暖色充电场景，保留当前商品实物结构。"}, ACTOR)["project"]
        resumed = self.start(edited)
        self.assertEqual([page["status"] for page in resumed["pages"]], ["complete", "queued", "complete"])
        self.assertEqual(resumed["pages"][0]["reusedOriginRevision"], 1)
        self.assertEqual(resumed["pages"][2]["reusedOriginQueueId"], original["id"])
        self.run_workers()
        self.assertEqual([fields["atelierPageNumber"] for fields, _refs in self.submissions], [1, 2, 3, 2])
        self.assertEqual(self.latest(edited)["completed"], 3)
        self.assertEqual(self.latest(edited)["status"], "complete")
        self.assertEqual(self.submissions[-1][0]["atelierRevision"], 2)

    def test_cross_version_reuse_preserves_original_revision_through_multiple_edits(self):
        project = self.project()
        original = self.start(project)
        self.run_workers()
        for revision in (1, 2):
            project = atelier.edit_page(project["id"], {"revision": revision, "pageNumber": 2,
                "modelPrompt": f"第二页新的独立构图 {revision}，其他页面不改变。"}, ACTOR)["project"]
            self.start(project)
            self.run_workers()
        final = self.latest(project)
        self.assertEqual(final["pages"][0]["reusedOriginRevision"], 1)
        self.assertEqual(final["pages"][0]["reusedOriginQueueId"], original["id"])
        self.assertEqual([fields["atelierPageNumber"] for fields, _refs in self.submissions], [1, 2, 3, 2, 2])

    def test_changed_master_or_references_or_settings_prevent_cross_version_reuse(self):
        for change in ("master", "references", "settings"):
            with self.subTest(change=change):
                project = self.project(product=f"便携榨汁杯-{change}")
                self.start(project)
                self.run_workers()
                before_count = len(self.submissions)
                owner = atelier._owner(ACTOR)
                if change == "references":
                    next_version = atelier.save_project_upload({"projectId": project["id"], "revision": 1,
                            "form": project["form"], "referencesMode": "replace"},
                            {"reference0": image_upload(color="blue")}, ACTOR)["project"]
                    with atelier._LOCK:
                        doc = atelier._read(owner, project["id"])
                        version = atelier._version(doc)
                        version["masterPrompt"] = doc["revisions"][0]["masterPrompt"]
                        version["suitePages"] = copy.deepcopy(doc["revisions"][0]["suitePages"])
                        version["status"] = "complete"
                        for page in version["suitePages"]:
                            page["executionPrompt"] = compile_execution_prompt(version["form"], version["masterPrompt"], page, version["references"])
                        atelier._write(owner, doc)
                else:
                    next_version = atelier.edit_page(project["id"], {"revision": 1, "pageNumber": 2,
                        "modelPrompt": "仅改变第二页的充电场景镜头与文字构图。"}, ACTOR)["project"]
                    if change == "master":
                        with atelier._LOCK:
                            doc = atelier._read(owner, project["id"])
                            version = atelier._version(doc)
                            version["masterPrompt"] = "完全改变整套商品的总控风格及卖点呈现。"
                            for page in version["suitePages"]:
                                page["executionPrompt"] = compile_execution_prompt(version["form"], version["masterPrompt"], page, version["references"])
                            atelier._write(owner, doc)
                resumed = self.start(next_version, **({"quality": "low"} if change == "settings" else {}))
                self.assertTrue(all(page["status"] == "queued" for page in resumed["pages"]))
                self.run_workers()
                self.assertEqual(len(self.submissions) - before_count, 3)

    def test_unresolved_old_version_cannot_be_repaid_by_silent_version_switch(self):
        project = self.project()
        self.raise_before_persist = True
        self.start(project, pageNumbers=[1])
        self.run_workers()
        edited = atelier.edit_page(project["id"], {"revision": 1, "pageNumber": 2,
                    "modelPrompt": "第二页改为新的充电台面场景。"}, ACTOR)["project"]
        self.raise_before_persist = False
        with self.assertRaisesRegex(ValueError, "原版本"):
            self.start(edited)
        self.assertEqual(len(self.submissions), 1)
        self.start(edited, mode="redo", pageNumbers=[1])
        self.run_workers()
        self.assertEqual(len(self.submissions), 2)

    def test_changed_settings_need_distinct_run_and_resume_cannot_mutate_snapshot(self):
        project = self.project()
        first = self.start(project, quality="medium")
        with self.assertRaisesRegex(ValueError, "已有"):
            self.start(project, quality="high")
        self.run_workers()
        second = self.start(project, quality="high")
        self.assertNotEqual(first["id"], second["id"])
        with self.assertRaises(ValueError):
            queue.resume_queue(project["id"], second["id"], {"revision": 1, "quality": "low"}, ACTOR)
        self.run_workers()
        self.assertEqual([fields["quality"] for fields, _refs in self.submissions], ["medium"] * 3 + ["high"] * 3)

    def test_saved_prompt_drift_is_blocked_before_any_provider_submission(self):
        project = self.project()
        self.start(project)
        owner = atelier._owner(ACTOR)
        with atelier._LOCK:
            doc = atelier._read(owner, project["id"])
            doc["revisions"][0]["suitePages"][0]["executionPrompt"] = "tampered"
            atelier._write(owner, doc)
        self.run_workers()
        self.assertEqual(self.latest(project)["status"], "needs_attention")
        self.assertEqual(self.submissions, [])

    def test_all_read_action_paths_and_job_reads_are_owner_scoped(self):
        project = self.project()
        run = self.start(project)
        for action in (
            lambda: queue.list_queues(project["id"], OTHER),
            lambda: queue.start_queue(project["id"], {"revision": 1}, OTHER),
            lambda: queue.resume_queue(project["id"], run["id"], {"revision": 1}, OTHER),
            lambda: queue.cancel_queue(project["id"], run["id"], {"revision": 1}, OTHER),
        ):
            with self.assertRaises((ValueError, PermissionError)):
                action()
        self.run_workers()
        own_job = next(iter(self.jobs))
        with self.assertRaises((ValueError, PermissionError)):
            render.get_render_job(project["id"], own_job, OTHER)
        serialized = json.dumps(self.latest(project), ensure_ascii=False)
        self.assertNotIn("_actor", serialized)
        self.assertNotIn("_owner", serialized)
        self.assertNotIn("_pageSnapshots", serialized)

    def test_restart_checks_current_user_not_just_persisted_role(self):
        project = self.project()
        self.start(project)
        queue._RUNS.clear()
        self.workers.clear()
        self.users[0]["active"] = False
        counts = queue.resume_queues_on_startup()
        self.assertEqual(counts["paused"], 1)
        self.assertEqual(counts["resumed"], 0)
        self.assertEqual(self.submissions, [])
        record = self.latest(project)
        self.assertEqual(record["status"], "paused")
        private = self.raw(project, record["id"])
        self.assertEqual(set(private["_actor"]), {"username", "role"})

    def test_one_run_per_project_and_two_per_user_limit(self):
        projects = [self.project(product=f"测试商品 {index}") for index in range(3)]
        self.start(projects[0], pageNumbers=[1])
        with self.assertRaisesRegex(ValueError, "已有"):
            self.start(projects[0], pageNumbers=[2])
        self.start(projects[1])
        with self.assertRaisesRegex(ValueError, "两个"):
            self.start(projects[2])
        self.assertEqual(len(self.workers), 2)
        self.run_workers()

    def test_invalid_queue_inputs_do_not_submit(self):
        project = self.project()
        for bad in ({"revision": None}, {"pageNumbers": []}, {"pageNumbers": [1, 1]}, {"pageNumbers": [99]},
                    {"pageNumbers": [True]}, {"mode": "quietly-redo"}, {"quality": "unknown"}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.start(project, **bad)
        with self.assertRaises(ValueError):
            queue.resume_queue(project["id"], "../elsewhere", {}, ACTOR)
        self.assertEqual(self.submissions, [])
        self.assertEqual(self.workers, [])

    def test_compacted_completed_job_keeps_idempotent_identity(self):
        project = self.project()
        result = render.start_render(project["id"], {"revision": 1, "pageNumber": 1}, ACTOR)
        job_id = result["jobId"]
        self.jobs[job_id] = backend.compact_ai_image_job_for_storage(self.jobs[job_id])
        again = render.start_render(project["id"], {"revision": 1, "pageNumber": 1}, ACTOR)
        self.assertEqual(again["jobId"], job_id)
        self.assertTrue(again["reusedJob"])
        self.assertEqual(len(self.submissions), 1)


if __name__ == "__main__":
    unittest.main()
