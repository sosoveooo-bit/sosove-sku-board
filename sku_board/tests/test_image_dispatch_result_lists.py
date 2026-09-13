"""Offline regression checks for image lists returned by non-suite node tasks.

The real single-node worker returns a list when ``allow_partial=False``.  COD
hook requests still provide per-image prompts, so the multi-node merger must
support this shape rather than silently dropping successful paid results.
"""

from contextlib import ExitStack, nullcontext
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from sku_board import backend


class ImageDispatchResultListTests(unittest.TestCase):
    MODEL = "gpt-image-2.5-sunburst"
    ACTOR = {"username": "dispatch-list-fixture", "role": "ops"}

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        directory = self.stack.enter_context(tempfile.TemporaryDirectory(prefix="dispatch-result-lists-"))
        data_dir = Path(directory)
        self.stack.enter_context(patch.dict(os.environ, {
            "SKU_BOARD_DATA_DIR": directory,
            "CHATGPT2API_HEDGE_NODE_COUNT": "2",
            "CHATGPT2API_IMAGE_TRANSIENT_RETRIES": "1",
        }))
        for name, path in {
            "DATA_DIR": data_dir,
            "DATA_FILE": data_dir / "board.json",
            "AI_IMAGE_ERROR_LOG": data_dir / "errors.log",
            "AI_DIRECTOR_SETTINGS_FILE": data_dir / "director.json",
        }.items():
            self.stack.enter_context(patch.object(backend, name, path))
        for target in ("requests.sessions.Session.request", "urllib.request.urlopen"):
            self.stack.enter_context(patch(target, side_effect=AssertionError("External network disabled")))
        self.stack.enter_context(patch.object(backend, "log_ai_image_error"))
        self.stack.enter_context(patch.object(backend, "record_ai_image_node_runtime"))
        self.stack.enter_context(patch.object(backend, "await_ai_image_health_monitor_ready"))
        self.stack.enter_context(patch.object(backend, "ai_image_request_slot", side_effect=lambda _actor: nullcontext()))
        self.stack.enter_context(patch.object(
            backend, "reserve_ai_image_generation_nodes",
            side_effect=lambda nodes, indexes: ([position % len(nodes) for position in range(len(indexes))], []),
        ))

    @staticmethod
    def nodes(count):
        return [
            {
                "id": f"node-{index}", "name": f"Fixture node {index}",
                "rootUrl": f"https://node-{index}.example.invalid",
                "baseUrl": f"https://node-{index}.example.invalid/v1", "authKey": "fixture-only",
            }
            for index in range(count)
        ]

    @staticmethod
    def image(index):
        return (f"image-for-page-{index}".encode(), "image/png")

    def request(self, indexes):
        return {
            "prompt": "COD hook fixture with verified product references",
            "model": self.MODEL, "size": "750x1000", "count": len(indexes),
            "prompts": [f"Original prompt for page {index}" for index in indexes],
            "page_indexes": list(indexes), "allow_partial": False,
            "reference_images": [("product.png", b"product-fixture", "image/png")],
            "reference_images_by_page": {
                index: [(f"reference-{index}.png", f"source-{index}".encode(), "image/png")]
                for index in indexes
            },
        }

    def list_worker(self, **kwargs):
        self.assertFalse(kwargs["allow_partial"])
        self.assertEqual(kwargs["model"], self.MODEL)
        for index, prompt in zip(kwargs["page_indexes"], kwargs["prompts"]):
            self.assertEqual(prompt, f"Original prompt for page {index}")
            self.assertEqual(kwargs["reference_images_by_page"][index][0][1], f"source-{index}".encode())
        return [self.image(index) for index in kwargs["page_indexes"]]

    def dispatch(self, indexes, *, node_count=7, worker=None, allow_partial=False, transient_retry=False):
        request = self.request(indexes)
        request["allow_partial"] = allow_partial
        with (
            patch.object(backend, "chatgpt2api_service_nodes", return_value=self.nodes(node_count)),
            patch.object(backend, "_generate_images_via_chatgpt2api_tasks_single", side_effect=worker or self.list_worker) as single,
        ):
            if transient_retry:
                result = backend.generate_ai_image_tasks_with_transient_retry(actor=self.ACTOR, **request)
            else:
                result = backend._dispatch_images_via_chatgpt2api_tasks(**request)
        return result, single

    def assert_images_match_pages(self, result, indexes):
        self.assertIsInstance(result, dict)
        self.assertEqual([item["index"] for item in result["outputs"]], sorted(indexes))
        self.assertEqual([item["image"] for item in result["outputs"]], [self.image(index) for index in sorted(indexes)])
        self.assertFalse(result["errors"])
        self.assertFalse(result["pending"])
        for item in result["outputs"]:
            self.assertTrue(item["nodeId"].startswith("node-"))
            self.assertTrue(item["nodeName"].startswith("Fixture node "))

    def test_five_hook_prompts_keep_all_successful_node_image_lists(self):
        result, single = self.dispatch(range(5))
        self.assertEqual(single.call_count, 5)
        self.assert_images_match_pages(result, range(5))
        self.assertEqual(len(result["nodeResults"]), 5)
        self.assertTrue(all(item["success"] for item in result["nodeResults"]))

    def test_reverse_node_completion_still_orders_images_by_original_page(self):
        events = [threading.Event() for _ in range(6)]
        events[-1].set()
        completed = []
        lock = threading.Lock()

        def reverse_worker(**kwargs):
            index = kwargs["page_indexes"][0]
            self.assertTrue(events[index + 1].wait(timeout=5), "Fixture worker order timed out")
            images = self.list_worker(**kwargs)
            with lock:
                completed.append(index)
            events[index].set()
            return images

        result, _ = self.dispatch(range(5), worker=reverse_worker)
        self.assertEqual(completed, [4, 3, 2, 1, 0])
        self.assert_images_match_pages(result, range(5))

    def test_non_contiguous_page_indexes_are_preserved_not_renumbered(self):
        indexes = [10, 4, 37, 21, 9]
        result, _ = self.dispatch(indexes)
        self.assert_images_match_pages(result, indexes)
        actual_nodes = {item["index"]: item["nodeId"] for item in result["outputs"]}
        self.assertEqual(actual_nodes, {index: f"node-{position}" for position, index in enumerate(indexes)})

    def test_two_images_per_node_group_keep_both_original_positions(self):
        result, single = self.dispatch(range(6), node_count=3)
        self.assertEqual(single.call_count, 3)
        self.assertEqual(sorted(tuple(call.kwargs["page_indexes"]) for call in single.call_args_list), [(0, 3), (1, 4), (2, 5)])
        self.assert_images_match_pages(result, range(6))
        self.assertEqual({item["index"]: item["nodeId"] for item in result["outputs"]}, {index: f"node-{index % 3}" for index in range(6)})

    def test_structured_partial_results_keep_outputs_errors_pending_and_task_ids(self):
        def structured_worker(**kwargs):
            self.assertTrue(kwargs["allow_partial"])
            success, pending, failed = kwargs["page_indexes"]
            return {
                "outputs": [{"index": success, "taskId": f"task-{success}", "image": self.image(success)}],
                "pending": [{"index": pending, "taskId": f"task-{pending}", "status": "running"}],
                "errors": [{"index": failed, "taskId": f"task-{failed}", "message": "fixture terminal error"}],
                "taskIds": [f"task-{index}" for index in kwargs["page_indexes"]], "timedOut": True,
            }

        result, _ = self.dispatch(range(6), node_count=2, worker=structured_worker, allow_partial=True)
        self.assertEqual([item["index"] for item in result["outputs"]], [0, 1])
        self.assertEqual([item["image"] for item in result["outputs"]], [self.image(0), self.image(1)])
        self.assertEqual(sorted(item["index"] for item in result["pending"]), [2, 3])
        self.assertEqual(sorted(item["index"] for item in result["errors"]), [4, 5])
        self.assertEqual(sorted(result["taskIds"]), [f"task-{index}" for index in range(6)])
        self.assertTrue(result["timedOut"])
        self.assertTrue(all(item["nodeId"] in {"node-0", "node-1"} for key in ("outputs", "pending", "errors") for item in result[key]))

    def test_empty_image_lists_produce_an_explicit_error(self):
        with self.assertRaises(ValueError):
            self.dispatch(range(5), worker=lambda **_kwargs: [])

    def test_short_image_lists_produce_an_explicit_error_without_guessing_page(self):
        def short_worker(**kwargs):
            return self.list_worker(**kwargs)[:-1]

        with self.assertRaises(ValueError):
            self.dispatch(range(6), node_count=2, worker=short_worker)

    def test_one_short_group_never_assigns_ambiguous_bytes_to_any_page(self):
        def mixed_worker(**kwargs):
            images = self.list_worker(**kwargs)
            return images[-1:] if kwargs["service_node"]["id"] == "node-0" else images

        try:
            result, _ = self.dispatch(range(4), node_count=2, worker=mixed_worker)
        except ValueError:
            return  # Explicit failure also satisfies the no-guessed-page contract.
        self.assertEqual([item["index"] for item in result["outputs"]], [1, 3])
        self.assertEqual([item["image"] for item in result["outputs"]], [self.image(1), self.image(3)])
        self.assertTrue(result["errors"])
        self.assertTrue(any(item["nodeId"] == "node-0" for item in result["errors"]))

    def test_empty_lists_do_not_trigger_blind_paid_resubmission(self):
        with (
            patch.object(backend, "chatgpt2api_service_nodes", return_value=self.nodes(2)),
            patch.object(backend, "_generate_images_via_chatgpt2api_tasks_single", return_value=[]) as single,
        ):
            with self.assertRaises(ValueError):
                backend.generate_ai_image_tasks_with_transient_retry(actor=self.ACTOR, **self.request(range(4)))
        self.assertEqual(single.call_count, 2)

    def test_single_configured_node_keeps_existing_success_list_contract(self):
        result, single = self.dispatch(range(5), node_count=1)
        self.assertEqual(result, [self.image(index) for index in range(5)])
        self.assertEqual(single.call_count, 1)

    def test_single_hedged_page_keeps_existing_success_list_contract(self):
        result, single = self.dispatch([9], node_count=2)
        self.assertEqual(result, [self.image(9)])
        self.assertEqual(single.call_count, 1)


if __name__ == "__main__":
    unittest.main()
