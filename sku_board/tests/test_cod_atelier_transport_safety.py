from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import patch

from sku_board import backend


class AtelierTransportSafetyTests(unittest.TestCase):
    def test_atelier_uncertain_transport_has_one_attempt(self):
        with patch.object(backend, "generate_images_via_chatgpt2api_tasks", side_effect=ValueError("connection timeout")) as dispatch:
            with self.assertRaises(ValueError):
                backend.generate_ai_image_tasks_with_transient_retry(actor={"role": "designer"}, prompt="[Atelier page 1/10] saved prompt", model="gpt-image-2", size="750x1000", count=1)
        self.assertEqual(dispatch.call_count, 1)

    def test_atelier_single_page_never_hedges_on_second_paid_node(self):
        nodes = [{"id": "test-a", "name": "Test A"}, {"id": "test-b", "name": "Test B"}]
        with ExitStack() as stack:
            stack.enter_context(patch.object(backend, "chatgpt2api_service_nodes", return_value=nodes))
            stack.enter_context(patch.object(backend, "reserve_ai_image_generation_nodes", return_value=([0], nodes[:1])))
            stack.enter_context(patch.object(backend, "record_ai_image_node_runtime"))
            single = stack.enter_context(patch.object(backend, "_generate_images_via_chatgpt2api_tasks_single", side_effect=ValueError("connection timeout")))
            with self.assertRaises(ValueError):
                backend._dispatch_images_via_chatgpt2api_tasks(prompt="[Atelier page 1/10] saved prompt", model="gpt-image-2", size="750x1000", count=1)
        self.assertEqual(single.call_count, 1)

    def test_completed_job_keeps_durable_identity_after_compaction(self):
        payload = {"atelierProjectId": "p", "atelierRevision": 2, "atelierPageNumber": 3, "atelierRequestKey": "request", "atelierOwner": "owner", "atelierQueueId": "queue", "atelierOutcomeUncertain": True, "prompt": "large content"}
        result = backend.compact_ai_image_job_for_storage({"status": "error", "owner": "test", "role": "designer", "payload": payload})
        for field in payload:
            if field != "prompt":
                self.assertEqual(result["payload"][field], payload[field])

    def test_restart_resumes_only_queued_atelier_and_rechecks_actor(self):
        now = time.time()
        actor = {"username": "allowed", "role": "designer", "active": True}
        entries = {}
        for index, (status, owner) in enumerate((("running", "allowed"), ("queued", "allowed"), ("queued", "disabled")), 1):
            job_id = f"AIJ-{index:014X}"
            entries[job_id] = {"id": job_id, "status": status, "owner": owner, "role": "designer", "mode": "edit", "payload": {"atelierProjectId": "project"}, "actor": {"username": owner, "role": "designer"}, "files": [], "createdTs": now}
        with TemporaryDirectory(prefix="atelier-restart-safety-") as directory, ExitStack() as stack:
            stack.enter_context(patch.object(backend, "AI_IMAGE_JOBS_FILE", Path(directory) / "jobs.json"))
            stack.enter_context(patch.object(backend, "_AI_IMAGE_JOBS", {}))
            stack.enter_context(patch.object(backend, "_AI_IMAGE_JOB_THREADS", set()))
            stack.enter_context(patch.object(backend, "load_ai_image_jobs", return_value=entries))
            stack.enter_context(patch.object(backend, "load_board", return_value={}))
            stack.enter_context(patch.object(backend, "find_user", side_effect=lambda board, owner: actor if owner == "allowed" else {**actor, "username": owner, "active": False}))
            start = stack.enter_context(patch.object(backend, "start_ai_image_job_worker", return_value=True))
            result = backend.resume_ai_image_jobs()
            uncertain = backend.get_ai_image_job("AIJ-00000000000001", actor)
            disabled = backend._AI_IMAGE_JOBS["AIJ-00000000000003"]
        self.assertEqual(result["resumed"], 1)
        self.assertEqual(start.call_args.args[0], "AIJ-00000000000002")
        self.assertTrue(uncertain["outcomeUncertain"])
        self.assertEqual(disabled["status"], "error")


if __name__ == "__main__":
    unittest.main()
