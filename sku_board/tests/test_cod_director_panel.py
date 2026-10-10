from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CodDirectorPanelTests(unittest.TestCase):
    def test_cod_prompt_page_exposes_the_shared_video_panel_model_controls(self) -> None:
        html = (ROOT / "static" / "cod-prompt-generator.html").read_text(encoding="utf-8")
        script = (ROOT / "static" / "cod-prompt-generator.js").read_text(encoding="utf-8")
        for control_id in (
            "cod-director-model",
            "cod-director-base-url",
            "cod-director-api-key",
            "cod-director-custom-model-input",
            "cod-director-save-btn",
            "cod-director-test-btn",
            "cod-director-read-btn",
            "cod-director-current-model",
        ):
            self.assertIn(f'id="{control_id}"', html)
        self.assertIn("/api/sku-board/ai-director-settings", script)
        self.assertIn("/api/sku-board/ai-director-test", script)
        self.assertIn("AI_DIRECTOR_MODEL_PRESETS", script)
        self.assertIn("视频提示词面板同款的模型选项", html)
        self.assertIn("手动配置 OpenAI 兼容节点", html)
        self.assertNotIn("<details class=\"cod-director-settings\"", html)


if __name__ == "__main__":
    unittest.main()
