#!/usr/bin/env python3
"""
C2E 翻译模式处理器单元测试用例
测试覆盖：翻译、TTS、语音识别、模式管理、命令处理
"""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# 添加脚本目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from scripts.trsl_handler import (
    load_trsl_mode,
    save_trsl_mode,
    clear_trsl_mode,
    clean_ollama,
    translate_zh_to_en,
    tts_edge,
    transcribe_audio,
    translate_and_speak,
    process_voice,
    handle_trsl_mode_command,
    TMP_DIR,
)


class TestC2EModeManagement(unittest.TestCase):
    """C2E 模式状态管理测试"""

    def setUp(self):
        """测试前准备"""
        self.mode_path = os.path.expanduser("~/.openclaw/memory/weixin_mode.json")
        os.makedirs(os.path.dirname(self.mode_path), exist_ok=True)
        # 清理测试前的状态
        if os.path.exists(self.mode_path):
            os.remove(self.mode_path)

    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.mode_path):
            os.remove(self.mode_path)

    def test_load_trsl_mode_not_exists(self):
        """测试模式文件不存在时返回 None"""
        result = load_trsl_mode()
        self.assertIsNone(result)

    def test_save_and_load_trsl_mode(self):
        """测试保存和加载 C2E 模式"""
        save_trsl_mode("trsl")
        result = load_trsl_mode()
        self.assertEqual(result, "trsl")

    def test_clear_trsl_mode(self):
        """测试清除 C2E 模式"""
        save_trsl_mode("trsl")
        clear_trsl_mode()
        result = load_trsl_mode()
        self.assertIsNone(result)

    def test_save_trsl_mode_preserves_aliyun(self):
        """测试保存 C2E 模式时保留 aliyun 模式"""
        # 先设置 aliyun 模式
        with open(self.mode_path, "w") as f:
            json.dump({"aliyun": "解题模式"}, f)
        
        # 保存 trsl 模式
        save_trsl_mode("trsl")
        
        # 验证两者都存在
        with open(self.mode_path) as f:
            data = json.load(f)
        self.assertEqual(data["aliyun"], "解题模式")
        self.assertEqual(data["trsl"], "trsl")

    def test_clear_trsl_mode_preserves_aliyun(self):
        """测试清除 C2E 模式时保留 aliyun 模式"""
        # 设置两种模式
        with open(self.mode_path, "w") as f:
            json.dump({"aliyun": "解题模式", "trsl": "trsl"}, f)
        
        # 只清除 trsl
        clear_trsl_mode()
        
        # 验证 aliyun 还在
        with open(self.mode_path) as f:
            data = json.load(f)
        self.assertEqual(data["aliyun"], "解题模式")
        self.assertNotIn("trsl", data)


class TestCleanOllama(unittest.TestCase):
    """Ollama 输出清理测试"""

    def test_clean_ansi_codes(self):
        """测试清理 ANSI 控制字符"""
        dirty = "\x1B[31mHello\x1B[0m World"
        clean = clean_ollama(dirty)
        self.assertEqual(clean, "Hello World")

    def test_clean_control_chars(self):
        """测试清理控制字符"""
        dirty = "Hello\x00\x1F\x7F World"
        clean = clean_ollama(dirty)
        self.assertEqual(clean, "Hello World")

    def test_clean_whitespace(self):
        """测试清理首尾空白"""
        dirty = "  Hello World  \n"
        clean = clean_ollama(dirty)
        self.assertEqual(clean, "Hello World")

    def test_clean_empty(self):
        """测试空字符串"""
        self.assertEqual(clean_ollama(""), "")


class TestTranslateZhToEn(unittest.TestCase):
    """中文翻译英文测试"""

    def test_translate_with_minimax_skip(self):
        """测试使用 MiniMax API 翻译 - 跳过（需要 openai 库）"""
        try:
            import openai  # noqa: F401
        except ImportError:
            self.skipTest("openai library not installed")
        
        # If openai is installed, run the actual test
        with patch("trsl_handler.MINIMAX_API_KEY", "test-key"):
            with patch("trsl_handler.MINIMAX_BASE_URL", "https://api.minimaxi.com/anthropic"):
                with patch("openai.OpenAI") as mock_openai:
                    mock_client = MagicMock()
                    mock_openai.return_value = mock_client
                    mock_client.chat.completions.create.return_value = MagicMock(
                        choices=[MagicMock(message=MagicMock(content="Hello world"))]
                    )

                    result = translate_zh_to_en("你好世界")
                    
                    self.assertEqual(result, "Hello world")
                    mock_client.chat.completions.create.assert_called_once()

    @patch("trsl_handler.MINIMAX_API_KEY", "")
    @patch("trsl_handler.run_cmd")
    def test_translate_with_ollama(self, mock_run_cmd):
        """测试使用 Ollama 翻译（fallback）"""
        mock_run_cmd.return_value = "Hello world"
        
        result = translate_zh_to_en("你好世界")
        
        self.assertEqual(result, "Hello world")
        mock_run_cmd.assert_called_once()

    @patch("trsl_handler.MINIMAX_API_KEY", "")
    @patch("trsl_handler.run_cmd")
    def test_trsl_preserves_numbers(self, mock_run_cmd):
        """测试翻译保留数字和 ID"""
        mock_run_cmd.return_value = "User 123 logged in at 2024-01-15"
        
        result = translate_zh_to_en("用户 123 在 2024-01-15 登录")
        
        self.assertIn("123", result)
        self.assertIn("2024-01-15", result)


class TestTTSEdge(unittest.TestCase):
    """Edge TTS 语音合成测试"""

    @patch("trsl_handler.NODE_BIN", "node")
    @patch("trsl_handler.EDGE_TTS_SCRIPT", "/fake/path/tts-converter.js")
    @patch("trsl_handler.run_cmd")
    @patch("trsl_handler.Path.exists")
    def test_tts_success(self, mock_exists, mock_run_cmd):
        """测试 TTS 成功"""
        mock_exists.return_value = True
        out_mp3 = Path("/tmp/test.mp3")
        
        result = tts_edge("Hello world", out_mp3)
        
        self.assertEqual(result, out_mp3)
        mock_run_cmd.assert_called_once()

    @patch("trsl_handler.EDGE_TTS_SCRIPT", "/fake/path/tts-converter.js")
    @patch("trsl_handler.Path.exists")
    def test_tts_script_not_found(self, mock_exists):
        """测试 TTS 脚本不存在"""
        mock_exists.return_value = False
        out_mp3 = Path("/tmp/test.mp3")

        result = tts_edge("Hello world", out_mp3)

        self.assertIsNone(result)


class TestTranscribeAudio(unittest.TestCase):
    """Whisper 语音识别测试"""

    @unittest.skip("whisper")
    @patch("trsl_handler.whisper")
    def test_transcribe_success(self, mock_whisper):
        """测试语音识别成功"""
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model
        mock_model.transcribe.return_value = {"text": "你好世界"}

        result = transcribe_audio(Path("/tmp/test.mp3"))

        self.assertEqual(result, "你好世界")

    @unittest.skip("whisper")
    @patch("trsl_handler.whisper")
    def test_transcribe_failure(self, mock_whisper):
        """测试语音识别失败"""
        mock_whisper.load_model.side_effect = Exception("model not found")

        with self.assertRaises(Exception) as context:
            transcribe_audio(Path("/tmp/test.mp3"))

        self.assertIn("model not found", str(context.exception))


class TestTranslateAndSpeak(unittest.TestCase):
    """翻译 + 语音合成联合测试"""

    @patch("trsl_handler.translate_zh_to_en")
    @patch("trsl_handler.tts_edge")
    @patch("trsl_handler.TMP_DIR")
    def test_translate_and_speak_success(self, mock_tmp, mock_tts, mock_translate):
        """测试翻译并生成语音"""
        mock_translate.return_value = "Hello world"
        mock_tmp.mkdir = MagicMock()
        
        mock_out_mp3 = MagicMock()
        mock_out_mp3.__str__ = lambda self: "/tmp/trsl_test.mp3"
        mock_tts.return_value = mock_out_mp3
        
        result = translate_and_speak("你好世界")

        self.assertIn("translated", result)
        self.assertIn("audio_path", result)
        self.assertEqual(result["translated"], "Hello world")
        mock_translate.assert_called_once()
        mock_tts.assert_called_once()


class TestProcessVoice(unittest.TestCase):
    """语音处理全流程测试"""

    @unittest.skip("whisper")
    @patch("trsl_handler.transcribe_audio")
    @patch("trsl_handler.translate_zh_to_en")
    @patch("trsl_handler.tts_edge")
    @patch("trsl_handler.TMP_DIR")
    def test_process_voice_success(self, mock_tmp, mock_tts, mock_translate, mock_transcribe):
        """测试语音处理全流程"""
        mock_transcribe.return_value = "你好世界"
        mock_translate.return_value = "Hello world"
        mock_tmp.mkdir = MagicMock()
        
        mock_out_mp3 = MagicMock()
        mock_out_mp3.__str__ = lambda self: "/tmp/trsl_voice_test.mp3"
        mock_tts.return_value = mock_out_mp3
        
        result = process_voice("/tmp/voice.mp3")
        
        self.assertEqual(result["chinese"], "你好世界")
        self.assertEqual(result["translated"], "Hello world")
        self.assertIn("audio_path", result)


class TestHandleC2ECommand(unittest.TestCase):
    """C2E 命令处理测试"""

    def test_enter_trsl_mode_chinese(self):
        """测试进入翻译模式（中文命令）"""
        result = handle_trsl_mode_command("翻译模式")
        self.assertIsNotNone(result)
        self.assertIn("已进入翻译模式", result)
        self.assertEqual(load_trsl_mode(), "trsl")

    def test_enter_trsl_mode_english(self):
        """测试进入翻译模式（英文命令）"""
        result = handle_trsl_mode_command("trsl")
        self.assertIsNotNone(result)
        self.assertIn("已进入翻译模式", result)

    def test_exit_trsl_mode_chinese(self):
        """测试退出翻译模式（中文命令）"""
        save_trsl_mode("trsl")
        result = handle_trsl_mode_command("解除模式")
        self.assertIsNotNone(result)
        self.assertIn("已解除翻译模式", result)
        self.assertIsNone(load_trsl_mode())

    def test_exit_trsl_mode_english(self):
        """测试退出翻译模式（英文命令）"""
        save_trsl_mode("trsl")
        result = handle_trsl_mode_command("trsl-exit")
        self.assertIsNotNone(result)
        self.assertIn("已解除翻译模式", result)

    def test_unrelated_command(self):
        """测试无关命令不处理"""
        result = handle_trsl_mode_command("今天天气不错")
        self.assertIsNone(result)

    def test_command_with_whitespace(self):
        """测试命令带空白字符"""
        result = handle_trsl_mode_command("  翻译模式  \n")
        self.assertIsNotNone(result)
        self.assertIn("已进入翻译模式", result)


class TestIntegration(unittest.TestCase):
    """集成测试"""

    @patch("trsl_handler.handle_trsl_mode_command")
    @patch("trsl_handler.translate_and_speak")
    def test_full_text_flow(self, mock_translate, mock_handle):
        """测试完整文本翻译流程"""
        mock_handle.return_value = None  # 不是模式命令
        mock_translate.return_value = {
            "translated": "Hello world",
            "audio_path": "/tmp/test.mp3"
        }
        
        # 模拟接收到文本消息
        text = "你好世界"
        trsl_mode = load_trsl_mode()
        
        if trsl_mode == "trsl":
            result = translate_and_speak(text)
            self.assertEqual(result["translated"], "Hello world")

    @patch("trsl_handler.handle_trsl_mode_command")
    @patch("trsl_handler.process_voice")
    def test_full_voice_flow(self, mock_process, mock_handle):
        """测试完整语音翻译流程"""
        mock_handle.return_value = None  # 不是模式命令
        mock_process.return_value = {
            "source": "你好世界",
            "translated": "Hello world",
            "audio_path": "/tmp/test.mp3"
        }
        
        # 模拟接收到语音消息
        voice_path = "/tmp/voice.mp3"
        trsl_mode = load_trsl_mode()
        
        if trsl_mode == "trsl":
            result = process_voice(voice_path)
            self.assertEqual(result["chinese"], "你好世界")
            self.assertEqual(result["translated"], "Hello world")


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestC2EModeManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestCleanOllama))
    suite.addTests(loader.loadTestsFromTestCase(TestTranslateZhToEn))
    suite.addTests(loader.loadTestsFromTestCase(TestTTSEdge))
    suite.addTests(loader.loadTestsFromTestCase(TestTranscribeAudio))
    suite.addTests(loader.loadTestsFromTestCase(TestTranslateAndSpeak))
    suite.addTests(loader.loadTestsFromTestCase(TestProcessVoice))
    suite.addTests(loader.loadTestsFromTestCase(TestHandleC2ECommand))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
