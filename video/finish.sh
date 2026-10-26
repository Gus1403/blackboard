#!/usr/bin/env bash
# After `node capture.mjs all`: join chunks, normalise narration (-16 LUFS speech, -1.5 dBTP), mux, write SRT.
# Writes final.mp4 (H.264 + AAC 192k, faststart) and final.srt; each appears only when complete.
set -euo pipefail
cd "$(dirname "$0")"
python3 tts.py --verify >/dev/null   # timeline.json and narration.wav must come from one complete tts.py run
for f in chunks/list.txt narration.wav timeline.json; do
  [ -s "$f" ] || { echo "finish.sh: missing $f (run tts.py and node capture.mjs all first)" >&2; exit 1; }
done
ffmpeg -y -v error -f concat -safe 0 -i chunks/list.txt -c copy video_only.mp4
# two-pass loudnorm on the narration
J=$(ffmpeg -hide_banner -i narration.wav -af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g(){ echo "$J" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
if [ "$(g input_i)" = "-inf" ]; then   # silent narration: nothing to normalise
  ffmpeg -y -v error -i narration.wav -af aresample=48000 narration_norm.wav
else
  ffmpeg -y -v error -i narration.wav -af "loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,aresample=48000" narration_norm.wav
fi
ffmpeg -y -v error -i video_only.mp4 -i narration_norm.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart -f mp4 .final.tmp.mp4
python3 - <<'PY'
import json, os
tl=json.load(open('timeline.json'))
def ts(x):
    h=int(x//3600);m=int(x%3600//60);s=x%60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s%1)*1000)):03d}".replace(",1000",",999")
n=0;out=[]
for sc in tl['scenes']:
    for c in sc['subs']:
        n+=1;out.append(f"{n}\n{ts(sc['start']+c['s'])} --> {ts(sc['start']+c['e']+0.3)}\n{c['text']}\n")
open('.final.tmp.srt','w').write("\n".join(out))
os.replace('.final.tmp.srt','final.srt')
PY
mv -f .final.tmp.mp4 final.mp4
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate -of compact final.mp4
ffmpeg -hide_banner -i final.mp4 -af ebur128=peak=true -f null - 2>&1 | grep -A2 -E "Integrated loudness|True peak" | grep -E "I:|Peak:" || true
