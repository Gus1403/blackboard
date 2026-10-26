# Import an existing lesson video

Use this when the MP4 already exists and its lesson to video map has been reviewed. The importer does not create a map or judge whether its explanations match the lesson. Review every segment against the video and lesson first, especially practice pauses and reveal times.

```sh
python3 bin/lesson_video.py validate --workspace /path/to/course/learn --lesson 0013 --video /path/to/final.mp4 --map /path/to/reviewed-video-0013.json
python3 bin/lesson_video.py import --workspace /path/to/course/learn --lesson 0013 --video /path/to/final.mp4 --map /path/to/reviewed-video-0013.json --dry-run
python3 bin/lesson_video.py import --workspace /path/to/course/learn --lesson 0013 --video /path/to/final.mp4 --map /path/to/reviewed-video-0013.json
python3 bin/lesson_video.py status --workspace /path/to/course/learn --lesson 0013
```

`import` requires `ffprobe` on `PATH` to check the MP4's video stream and duration. `validate` checks duration when `ffprobe` is available; it reports when that check is skipped. The map's duration must be within 0.5 seconds of the MP4. An identical repeat import is a no-op. If an installed file differs, import stops; pass `--replace` only after reviewing the conflict. Replacement retains timestamp-independent unique `.bak-...` files beside the replaced files and reports their paths. The importer never edits lessons or learning records.

The map is JSON with exactly these top-level keys:

```json
{
  "version": 1,
  "lessonId": "0013",
  "lessonSha256": "<SHA-256 of the entire current lesson Markdown file, as bytes>",
  "video": "0013-lecture.mp4",
  "duration": 10.0,
  "captionsBurnedIn": true,
  "segments": [
    {"id": "opening", "label": "Opening idea", "start": 0, "end": 5, "line": 1, "step": null, "practice": null},
    {"id": "try-it", "label": "Try it", "start": 5, "end": 10, "line": 12, "step": null,
     "practice": {"pauseAt": 6, "revealAt": 8}}
  ]
}
```

`line` is a 1-based line in the original lesson source, not a rendered block ID. Times are seconds; intervals are ascending, do not overlap, and use an exclusive `end`. Covering the whole MP4 is preferred. Use `step` only where a verified derivation step is supported; otherwise use `null`. A practice gate's `pauseAt` and `revealAt` must both fall inside its segment, with the pause before the reveal. The map hash must match the current lesson exactly. The board's installed manifest validator enforces this structure during validation and import.
