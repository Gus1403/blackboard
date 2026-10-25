"""HTTP contract for workspace-local lesson video and byte-range static delivery."""

import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("bridge", Path(__file__).resolve().parents[1] / "board/bridge.py")
bridge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge)


class LessonVideoHTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.one = root / "one" / "learn"
        self.two = root / "two" / "learn"
        for wsp, title, media in ((self.one, "First", b"ABCDEFGHIJ"),
                                   (self.two, "Second", b"0123456789")):
            (wsp / "lessons/assets").mkdir(parents=True)
            (wsp / "reference").mkdir()
            (wsp / "lessons/0012-lesson.md").write_text(f"# {title}\n\nA line.\n", encoding="utf-8")
            (wsp / "lessons/assets/0012-lecture.mp4").write_bytes(media)
        self.write_manifest(self.one)
        self.write_manifest(self.two)
        self.state = {"ws": str(self.one), "current": "0012", "workspaces": {
            "one": {"path": str(self.one), "current": "0012"},
            "two": {"path": str(self.two), "current": "0012"}}}
        state_patch = patch.object(bridge, "state", return_value=self.state)
        discovery_patch = patch.object(bridge, "discovered", return_value=[])
        state_patch.start(); discovery_patch.start()
        self.addCleanup(state_patch.stop)
        self.addCleanup(discovery_patch.stop)

    def write_manifest(self, wsp, **changes):
        source = (wsp / "lessons/0012-lesson.md").read_bytes()
        manifest = {"version": 1, "lessonId": "0012", "lessonSha256": hashlib.sha256(source).hexdigest(),
                    "video": "0012-lecture.mp4", "duration": 10, "captionsBurnedIn": True,
                    "segments": [{"id": "intro", "label": "Introduction", "start": 0, "end": 5,
                                  "line": 1, "step": None, "practice": None},
                                 {"id": "example", "label": "Example", "start": 5, "end": 10,
                                  "line": 3, "step": None, "practice": {"pauseAt": 7, "revealAt": 8}}]}
        manifest.update(changes)
        (wsp / "reference/video-0012.json").write_text(json.dumps(manifest), encoding="utf-8")

    def request(self, path, method="GET", headers=None):
        client, server = socket.socketpair()
        try:
            request = f"{method} {path} HTTP/1.0\r\nHost: localhost\r\n"
            request += "".join(f"{key}: {value}\r\n" for key, value in (headers or {}).items()) + "\r\n"
            client.sendall(request.encode("ascii"))
            client.shutdown(socket.SHUT_WR)
            bridge.H(server, ("127.0.0.1", 0), object())
            server.close()
            raw = bytearray()
            while part := client.recv(65536):
                raw.extend(part)
            head, body = bytes(raw).split(b"\r\n\r\n", 1)
            lines = head.decode("iso-8859-1").split("\r\n")
            code = int(lines[0].split()[1])
            response_headers = dict(line.split(": ", 1) for line in lines[1:])
            return code, response_headers, body
        finally:
            server.close()
            client.close()

    def test_manifest_is_tied_to_lesson_and_workspace(self):
        for slug, expected in (("one", b"ABCDEFGHIJ"), ("two", b"0123456789")):
            with self.subTest(slug=slug):
                code, _, body = self.request(f"/api/lesson-video?id=0012&ws={slug}")
                data = json.loads(body)
                self.assertEqual(code, 200)
                self.assertTrue(data["available"])
                self.assertTrue(data["mappingValid"])
                self.assertEqual(data["segments"][1]["line"], 3)
                self.assertEqual(data["videoUrl"], f"/w/{slug}/assets/0012-lecture.mp4")
                self.assertNotIn(self.tmp.name, body.decode())
                self.assertEqual(self.request(data["videoUrl"])[2], expected)

    def test_absent_stale_and_invalid_manifests(self):
        path = self.one / "reference/video-0012.json"
        path.unlink()
        self.assertEqual(json.loads(self.request("/api/lesson-video?id=0012&ws=one")[2]), {"available": False})
        self.write_manifest(self.one)
        (self.one / "lessons/0012-lesson.md").write_text("# Changed\n", encoding="utf-8")
        stale = json.loads(self.request("/api/lesson-video?id=0012&ws=one")[2])
        self.assertTrue(stale["available"])
        self.assertFalse(stale["mappingValid"])
        self.assertEqual(self.request(stale["videoUrl"])[2], b"ABCDEFGHIJ")
        self.write_manifest(self.one, video="../../two/learn/lessons/assets/0012-lecture.mp4")
        invalid = json.loads(self.request("/api/lesson-video?id=0012&ws=one")[2])
        self.assertFalse(invalid["available"])
        self.assertIn("error", invalid)
        self.assertNotIn(self.tmp.name, json.dumps(invalid))
        self.write_manifest(self.one, segments=[{"id": "wrong", "label": "Wrong", "start": 0,
                                                 "end": 10, "line": 0}])
        self.assertFalse(json.loads(self.request("/api/lesson-video?id=0012&ws=one")[2])["available"])
        self.write_manifest(self.one, segments=[{"id": "wrong", "label": "Wrong", "start": 0,
                                                 "end": 10, "line": 99}])
        self.assertFalse(json.loads(self.request("/api/lesson-video?id=0012&ws=one")[2])["available"])
        self.write_manifest(self.one, lessonId="0013")
        self.assertFalse(json.loads(self.request("/api/lesson-video?id=0012&ws=one")[2])["available"])
        self.assertFalse(json.loads(self.request("/api/lesson-video?id=0012&ws=unknown")[2])["available"])

    def test_static_ranges_and_head(self):
        path = "/w/one/assets/0012-lecture.mp4"
        cases = (("bytes=2-5", 206, b"CDEF", "bytes 2-5/10"),
                 ("bytes=7-", 206, b"HIJ", "bytes 7-9/10"),
                 ("bytes=-3", 206, b"HIJ", "bytes 7-9/10"),
                 ("bytes=0-999", 206, b"ABCDEFGHIJ", "bytes 0-9/10"),
                 ("bytes=99-", 416, b"", "bytes */10"),
                 ("bytes=5-2", 416, b"", "bytes */10"),
                 ("bytes=-0", 416, b"", "bytes */10"),
                 ("bytes=1-2,4-5", 416, b"", "bytes */10"))
        for header, status, expected, content_range in cases:
            with self.subTest(header=header):
                code, headers, body = self.request(path, headers={"Range": header})
                self.assertEqual((code, body), (status, expected))
                self.assertEqual(headers["Accept-Ranges"], "bytes")
                self.assertEqual(headers["Content-Range"], content_range)
                self.assertEqual(int(headers["Content-Length"]), len(expected))
                head_code, head_headers, head_body = self.request(path, "HEAD", {"Range": header})
                self.assertEqual((head_code, head_body), (status, b""))
                self.assertEqual(head_headers, headers)
        code, headers, body = self.request(path, "HEAD")
        self.assertEqual((code, body), (200, b""))
        self.assertEqual(headers["Content-Length"], "10")
        self.assertEqual(self.request("/w/one/assets/missing.mp4")[0], 404)
        (self.one / "lessons/assets/note.txt").write_text("small note")
        self.assertEqual(self.request("/w/one/assets/note.txt")[2], b"small note")
        self.assertEqual(self.request("/w/one/assets/note.txt", headers={"Range": "bytes=-4"})[2], b"note")

    def test_head_event_stream_is_rejected_for_both_routes(self):
        # HEAD must return promptly instead of entering the infinite SSE loop.
        for path in ("/events?id=0012", "/w/one/events?id=0012"):
            with self.subTest(path=path):
                code, _, body = self.request(path, "HEAD")
                self.assertEqual((code, body), (405, b""))

    def test_asset_symlink_cannot_escape_workspace(self):
        escaped = self.one / "lessons/assets/escape.mp4"
        escaped.symlink_to(self.two / "lessons/assets/0012-lecture.mp4")
        self.assertEqual(self.request("/w/one/assets/escape.mp4")[0], 404)


if __name__ == "__main__":
    unittest.main()
