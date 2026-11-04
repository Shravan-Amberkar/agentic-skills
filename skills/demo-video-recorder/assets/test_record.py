"""Unit tests for record.py's script validation and ffmpeg command (no browser, no model).

    python3 -m unittest discover -s assets -p 'test_*.py'
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import record  # noqa: E402


def script(**kw):
    s = {"url": "http://127.0.0.1:8000/", "steps": [{"say": "Hello.", "actions": [{"click": "#go"}]}]}
    s.update(kw)
    return s


class Validate(unittest.TestCase):
    def test_defaults_filled(self):
        s = record.validate(script())
        self.assertEqual(s["voice"], "am_michael")
        self.assertEqual(s["lang"], "en-us")
        self.assertEqual(s["output"], "demo.mp4")

    def test_lang_follows_voice_prefix(self):
        self.assertEqual(record.validate(script(voice="bf_emma"))["lang"], "en-gb")
        self.assertEqual(record.validate(script(voice="hf_alpha"))["lang"], "hi")

    def test_rejects_missing_narration(self):
        with self.assertRaises(record.ScriptError):
            record.validate(script(steps=[{"caption": "x"}]))

    def test_rejects_bad_url_and_empty_steps(self):
        with self.assertRaises(record.ScriptError):
            record.validate(script(url="localhost:8000"))
        with self.assertRaises(record.ScriptError):
            record.validate(script(steps=[]))

    def test_rejects_unknown_and_ambiguous_actions(self):
        for bad in ({"tap": "#x"}, {"click": "#x", "hover": "#y"}, {"click": "#x", "colour": "red"}):
            with self.assertRaises(record.ScriptError, msg=bad):
                record.validate(script(steps=[{"say": "a", "actions": [bad]}]))

    def test_rejects_unknown_top_level_but_allows_notes(self):
        with self.assertRaises(record.ScriptError):
            record.validate(script(fps=30))
        record.validate(script(_note="fine"))

    def test_example_script_is_valid(self):
        record.load_script(Path(__file__).resolve().parent / "example-script.json")


class Target(unittest.TestCase):
    def test_default_is_two_minutes(self):
        self.assertEqual(record.validate(script())["target_seconds"], 120)

    def test_custom_and_invalid_targets(self):
        self.assertEqual(record.validate(script(target_seconds=45))["target_seconds"], 45)
        for bad in (0, -5, "60", True):
            with self.assertRaises(record.ScriptError, msg=bad):
                record.validate(script(target_seconds=bad))

    def test_fit_messages(self):
        self.assertTrue(record.fit(125, 120).startswith("on target"))
        self.assertIn("OVER target by 30s", record.fit(150, 120))
        self.assertIn("cut ~78 words", record.fit(150, 120))
        self.assertIn("UNDER target", record.fit(30, 60))


class Models(unittest.TestCase):
    def test_every_file_comes_from_the_pinned_release(self):
        # Regression: the URLs once pointed at model-files-v1.0 while the onnx checksum was
        # model-files-v1.1's, so every fresh download failed verification.
        self.assertRegex(record.MODEL_RELEASE, r"^https://github\.com/[^/]+/[^/]+/releases/download/[^/]+/$")
        self.assertEqual(set(record.MODEL_FILES), {"kokoro-v1.0.onnx", "voices-v1.0.bin"})
        for sha in record.MODEL_FILES.values():
            self.assertRegex(sha, r"^[0-9a-f]{64}$")


class Ffmpeg(unittest.TestCase):
    def test_trims_video_and_places_clips(self):
        args = record.ffmpeg_args(Path("v.webm"), [(Path("a.wav"), 0.0), (Path("b.wav"), 7.25)], 1.5, 20.0, Path("o.mp4"))
        self.assertEqual(args[args.index("-ss") + 1], "1.500")
        fc = args[args.index("-filter_complex") + 1]
        self.assertIn("[1:a]adelay=0|0[a0]", fc)
        self.assertIn("[2:a]adelay=7250|7250[a1]", fc)
        self.assertIn("amix=inputs=2:normalize=0", fc)
        self.assertEqual(args[-3:], ["-t", "20.00", "o.mp4"])


if __name__ == "__main__":
    unittest.main()
