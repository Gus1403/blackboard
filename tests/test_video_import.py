"""Import boundary tests for existing lesson media and reviewed maps."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin" / "lesson_video.py"
SPEC = importlib.util.spec_from_file_location("lesson_video_importer", CLI)
importer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(importer)


class VideoImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.workspace = root / "course" / "learn"
        (self.workspace / "lessons").mkdir(parents=True)
        self.lesson = self.workspace / "lessons" / "0013-example.md"
        self.lesson.write_text("# Example\n\nFirst line.\n\nTry this.\n", encoding="utf-8")
        self.records = self.workspace / "learning-records" / "quiz-log.jsonl"
        self.records.parent.mkdir()
        self.records.write_text('{"score":5}\n', encoding="utf-8")
        self.other = self.workspace / "lessons" / "0012-other.md"
        self.other.write_text("Other lesson\n", encoding="utf-8")
        self.media = root / "source.mp4"
        self.media.write_bytes(b"MP4 source bytes")
        self.mapping = root / "reviewed.json"
        self.manifest = {
            "version": 1, "lessonId": "0013", "lessonSha256": hashlib.sha256(self.lesson.read_bytes()).hexdigest(),
            "video": "0013-lecture.mp4", "duration": 10.0, "captionsBurnedIn": True,
            "segments": [
                {"id": "intro", "label": "First idea", "start": 0, "end": 5, "line": 1, "step": None, "practice": None},
                {"id": "try", "label": "Try this", "start": 5, "end": 10, "line": 5,
                 "step": None, "practice": {"pauseAt": 6, "revealAt": 8}},
            ],
        }
        self.base_manifest = json.loads(json.dumps(self.manifest))
        self.save_map()
        self.fake_bin = root / "bin"
        self.fake_bin.mkdir()
        probe = self.fake_bin / "ffprobe"
        probe.write_text(f"#!{sys.executable}\nimport json\nprint(json.dumps({{'streams': [{{'codec_type': 'video'}}], 'format': {{'duration': '10.0'}}}}))\n")
        probe.chmod(0o755)
        self.env = dict(os.environ, PATH=f"{self.fake_bin}{os.pathsep}{os.environ.get('PATH', '')}")

    def save_map(self):
        self.mapping.write_text(json.dumps(self.manifest), encoding="utf-8")

    def run_cli(self, command, *extra):
        argv = [sys.executable, str(CLI), command, "--workspace", str(self.workspace), "--lesson", "0013"]
        if command != "status":
            argv += ["--video", str(self.media), "--map", str(self.mapping)]
        return subprocess.run(argv + list(extra), text=True, capture_output=True, env=self.env)

    def assert_preserved(self):
        self.assertEqual(self.lesson.read_text(), "# Example\n\nFirst line.\n\nTry this.\n")
        self.assertEqual(self.records.read_text(), '{"score":5}\n')
        self.assertEqual(self.other.read_text(), "Other lesson\n")

    def test_import_dry_run_repeat_and_status(self):
        preview = self.run_cli("import", "--dry-run")
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertEqual(json.loads(preview.stdout)["result"], "dry-run")
        self.assertFalse((self.workspace / "reference").exists())
        imported = self.run_cli("import")
        self.assertEqual(imported.returncode, 0, imported.stderr)
        self.assertEqual(json.loads(imported.stdout)["result"], "imported")
        self.assertEqual((self.workspace / "lessons/assets/0013-lecture.mp4").read_bytes(), self.media.read_bytes())
        self.assertEqual((self.workspace / "reference/video-0013.json").read_bytes(), self.mapping.read_bytes())
        again = self.run_cli("import")
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(json.loads(again.stdout)["result"], "unchanged")
        state = self.run_cli("status")
        self.assertEqual(state.returncode, 0, state.stderr)
        self.assertTrue(json.loads(state.stdout)["mappingValid"])
        self.assert_preserved()

    def test_invalid_maps_and_duration_leave_workspace_untouched(self):
        cases = [
            ("hash", lambda m: m.update(lessonSha256="0" * 64), "lessonSha256"),
            ("line", lambda m: m["segments"][1].update(line=99), "board validator"),
            ("overlap", lambda m: m["segments"][1].update(start=4), "board validator"),
            ("gate", lambda m: m["segments"][1]["practice"].update(revealAt=11), "board validator"),
            ("schema", lambda m: m.update(extra=True), "board validator"),
            ("duration", lambda m: m.update(duration=12), "duration"),
            ("id", lambda m: m.update(lessonId="0012"), "lessonId"),
            ("filename", lambda m: m.update(video="../escape.mp4"), "map video"),
        ]
        for name, change, message in cases:
            with self.subTest(name=name):
                self.manifest = json.loads(json.dumps(self.base_manifest))
                change(self.manifest)
                self.save_map()
                rejected = self.run_cli("import")
                self.assertNotEqual(rejected.returncode, 0)
                self.assertIn(message, rejected.stderr)
                self.assertFalse((self.workspace / "reference").exists())
                self.assertFalse((self.workspace / "lessons/assets").exists())
                self.assert_preserved()

    def test_conflict_and_replace_keep_durable_backups(self):
        self.assertEqual(self.run_cli("import").returncode, 0)
        target = self.workspace / "lessons/assets/0013-lecture.mp4"
        target.write_bytes(b"older media")
        old_map = self.workspace / "reference/video-0013.json"
        old_map.write_text('{"old":true}', encoding="utf-8")
        denied = self.run_cli("import")
        self.assertNotEqual(denied.returncode, 0)
        self.assertIn("--replace", denied.stderr)
        self.assertEqual(target.read_bytes(), b"older media")
        replaced = self.run_cli("import", "--replace")
        self.assertEqual(replaced.returncode, 0, replaced.stderr)
        backups = [Path(p) for p in json.loads(replaced.stdout)["backups"]]
        self.assertEqual(len(backups), 2)
        self.assertEqual({p.read_bytes() for p in backups}, {b"older media", b'{"old":true}'})
        self.assertEqual(target.read_bytes(), self.media.read_bytes())
        self.assert_preserved()

    def test_import_requires_ffprobe_without_writing(self):
        self.env["PATH"] = ""
        rejected = self.run_cli("import")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("ffprobe is required", rejected.stderr)
        self.assertFalse((self.workspace / "reference").exists())
        self.assertFalse((self.workspace / "lessons/assets").exists())
        self.assert_preserved()

    def test_second_publish_failure_rolls_back_first_file(self):
        bridge = importer.board_bridge()
        self.assertEqual(self.run_cli("import").returncode, 0)
        target = self.workspace / "lessons/assets/0013-lecture.mp4"
        target.write_bytes(b"old media")
        old_map = self.workspace / "reference/video-0013.json"
        old_map.write_bytes(b"old map")
        original_replace = os.replace
        calls = 0

        def fail_second_publish(src, dst):
            nonlocal calls
            if Path(dst) in (target, old_map):
                calls += 1
                if calls == 2:
                    raise OSError("simulated second publish failure")
            return original_replace(src, dst)

        with patch.dict(os.environ, PATH=self.env["PATH"]):
            with patch.object(importer.os, "replace", side_effect=fail_second_publish):
                with self.assertRaisesRegex(OSError, "simulated"):
                    importer.install(bridge, self.workspace, "0013", self.media, self.mapping, True, False)
        self.assertEqual(target.read_bytes(), b"old media")
        self.assertEqual(old_map.read_bytes(), b"old map")
        self.assertEqual(list(self.workspace.rglob(".lesson-video-*")), [])
        self.assertEqual(list(self.workspace.rglob("*.bak-*")), [])
        self.assert_preserved()


if __name__ == "__main__":
    unittest.main()
