import unittest
from unittest.mock import patch

from sku_board import backend


class CodDirectorDeadlineTests(unittest.TestCase):
    def test_expired_round_does_not_start_another_model(self):
        settings = {"model": "fixture", "timeout": 120, "_absoluteDeadline": 99}
        with (
            patch.object(backend, "ai_director_model_candidates", return_value=["fixture"]),
            patch.object(backend.time, "monotonic", return_value=100),
            patch.object(backend, "invoke_ai_director_chat_once") as request,
        ):
            with self.assertRaises(ValueError):
                backend.invoke_ai_director_chat(settings, [])
            request.assert_not_called()

    def test_remaining_round_budget_caps_attempt(self):
        settings = {"model": "fixture", "timeout": 120, "_absoluteDeadline": 120}
        with (
            patch.object(backend, "ai_director_model_candidates", return_value=["fixture"]),
            patch.object(backend.time, "monotonic", return_value=100),
            patch.object(backend, "invoke_ai_director_chat_once", return_value=('{}', 1)) as request,
        ):
            backend.invoke_ai_director_chat(settings, [])
            self.assertEqual(request.call_args.args[0]["timeout"], 20)
