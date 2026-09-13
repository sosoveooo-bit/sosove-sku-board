from copy import deepcopy
import unittest
from unittest.mock import patch

from sku_board import backend


class HookSavedResultRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.query = {"analysisKey": "a" * 64, "model": "gpt-image-2.5-sunburst", "count": "5", "size": "750x1000"}
        self.actor = {"username": "alice", "role": "ops"}
        self.jobs = {}
        guard = patch.object(backend, "_AI_IMAGE_JOBS", self.jobs)
        guard.start()
        self.addCleanup(guard.stop)

    def add(self, job_id, owner="alice", created=1, **changes):
        material = {"id": "test-image", "model": self.query["model"], "sizePreset": self.query["size"]}
        result = {"templateKey": "codHook", "requestedCount": 5, "returnedCount": 1,
                  "materials": [material], "previewDataUrls": ["/test/image.png"],
                  "productAnalysis": {"status": "ready", "analysisKey": self.query["analysisKey"]}}
        result.update(changes)
        self.jobs[job_id] = {"id": job_id, "owner": owner, "status": "success", "createdTs": created, "result": result}

    def test_latest_exact_owned_result_is_read_without_generation_or_mutation(self):
        self.add("older")
        self.add("newer", created=2)
        before = deepcopy(self.jobs)
        with patch("requests.sessions.Session.request", side_effect=AssertionError("No network")), patch.object(
            backend, "generate_ai_image_tasks_with_transient_retry", side_effect=AssertionError("No image submission")
        ):
            result = backend.recover_saved_cod_hook_result(self.query, self.actor)
        self.assertTrue(result["found"])
        self.assertEqual(result["jobId"], "newer")
        result["materials"][0]["id"] = "caller-edit"
        self.assertEqual(self.jobs, before)

    def test_other_accounts_are_not_returned_even_to_an_admin_lookup(self):
        self.add("other", owner="bob")
        for role in ("ops", "admin"):
            self.assertFalse(backend.recover_saved_cod_hook_result(self.query, {"username": "alice", "role": role})["found"])

    def test_changed_analysis_model_canvas_count_or_template_do_not_match(self):
        self.add("candidate")
        for changes in ({"analysisKey": "b" * 64}, {"model": "gpt-image-2"}, {"size": "1024x1024"}, {"count": "1"}):
            self.assertFalse(backend.recover_saved_cod_hook_result({**self.query, **changes}, self.actor)["found"])
        self.jobs["candidate"]["result"]["templateKey"] = "main"
        self.assertFalse(backend.recover_saved_cod_hook_result(self.query, self.actor)["found"])

    def test_invalid_input_or_account_has_no_global_latest_task_lookup(self):
        self.add("candidate")
        for changes in ({"analysisKey": ""}, {"analysisKey": "../foreign"}, {"model": ""}, {"size": ""}, {"count": "0"}):
            with self.assertRaises(ValueError):
                backend.recover_saved_cod_hook_result({**self.query, **changes}, self.actor)
        with self.assertRaises(ValueError):
            backend.recover_saved_cod_hook_result(self.query, {"username": "alice", "role": "viewer"})


if __name__ == "__main__":
    unittest.main()
