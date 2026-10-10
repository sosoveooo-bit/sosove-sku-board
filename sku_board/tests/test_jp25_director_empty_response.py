"""A 200 response containing only reasoning must not count as a usable plan."""
import unittest
from unittest.mock import Mock, patch
from sku_board import backend


class Jp25DirectorEmptyResponseTests(unittest.TestCase):
    def settings(self, **extra):
        return {"baseUrl": "http://director.test/v1", "apiKey": "test-only", "model": "deepseek-v4.1-flash",
                "fallbackModels": ["gpt-5.6-terra"], "timeout": 30, "_jp25CreativePlanning": True, **extra}

    def test_jp25_deepseek_reserves_output_for_the_actual_plan(self):
        response = Mock(ok=True)
        response.json.return_value = {"choices": [{"message": {"content": '{"pages":[]}'}, "finish_reason": "stop"}]}
        session = Mock(); session.post.return_value = response
        with patch("requests.Session", return_value=session):
            backend.invoke_ai_director_chat_once(self.settings(), [{"role": "user", "content": "Return JSON"}])
        self.assertEqual(session.post.call_args.kwargs["json"].get("thinking"), {"type": "disabled"})
        for settings in (self.settings(_jp25CreativePlanning=False), self.settings(model="gpt-5.6-terra")):
            with patch("requests.Session", return_value=session):
                backend.invoke_ai_director_chat_once(settings, [{"role": "user", "content": "Return JSON"}])
            self.assertNotIn("thinking", session.post.call_args.kwargs["json"])

    def test_reasoning_only_response_fails_over_instead_of_recording_success(self):
        empty = Mock(ok=True)
        empty.json.return_value = {"choices": [{"message": {"content": "", "reasoning_content": "private fixture reasoning"},
                                                 "finish_reason": "length"}],
                                  "usage": {"completion_tokens": 6500, "completion_tokens_details": {"reasoning_tokens": 6500}}}
        success = Mock(ok=True)
        success.json.return_value = {"choices": [{"message": {"content": '{"ok":true}'}, "finish_reason": "stop"}]}
        session = Mock(); session.post.side_effect = [empty, success]
        settings = self.settings()
        with patch("requests.Session", return_value=session):
            result, _ = backend.invoke_ai_director_chat(settings, [{"role": "user", "content": "Return JSON"}])
        self.assertEqual(result, '{"ok":true}')
        self.assertEqual([c.kwargs["json"]["model"] for c in session.post.call_args_list], ["deepseek-v4.1-flash", "gpt-5.6-terra"])
        self.assertTrue(settings["_lastDirectorCall"]["fallbackUsed"])
        self.assertNotIn("private fixture reasoning", str(settings["_lastDirectorCall"]))

    def test_empty_text_parts_and_truncated_jp25_json_are_not_usable(self):
        for content, finish in (("  ", "stop"), ([], "stop"), ([{"type": "text", "text": ""}], "stop"), ('{"pages":[', "length")):
            response = Mock(ok=True)
            response.json.return_value = {"choices": [{"message": {"content": content}, "finish_reason": finish}]}
            session = Mock(); session.post.return_value = response
            with self.subTest(content=content), patch("requests.Session", return_value=session):
                with self.assertRaisesRegex(ValueError, "正文|截断|内容"):
                    backend.invoke_ai_director_chat_once(self.settings(), [{"role": "user", "content": "Return JSON"}])
