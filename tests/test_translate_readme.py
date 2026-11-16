"""Regression tests for Markdown syntax that must survive translation."""

import sys
import types
import unittest
from unittest.mock import patch


# The translation helpers do not need a real DeepL client for these tests.
deepl_stub = types.ModuleType("deepl")
deepl_stub.Translator = object
with patch.dict(sys.modules, {"deepl": deepl_stub}):
    from scripts.translate_readme import translate_line


class FakeTranslator:
    def __init__(self):
        self.calls = []

    def translate_text(self, text, **kwargs):
        self.calls.append(text)
        return types.SimpleNamespace(text=f"translated: {text}")


class GitHubAlertTests(unittest.TestCase):
    def test_alert_markers_are_not_sent_to_deepl(self):
        translator = FakeTranslator()
        for alert_type in ("NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION"):
            with self.subTest(alert_type=alert_type):
                line = f"> [!{alert_type}]\n"
                self.assertEqual(translate_line(translator, line, "JA", "EN-US"), line)
        self.assertEqual(translator.calls, [])

    def test_alert_body_is_translated_without_losing_blockquote(self):
        translator = FakeTranslator()
        self.assertEqual(
            translate_line(translator, "> 本文\n", "JA", "EN-US"),
            "> translated: 本文\n",
        )
        self.assertEqual(translator.calls, ["本文"])


if __name__ == "__main__":
    unittest.main()
