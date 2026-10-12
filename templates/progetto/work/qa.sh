#!/bin/zsh
# Step 15. QA on the delivery: contact sheet at 1 fps, junction sheet (frames f-1 and f at every segment start),
# loudness of every stem and of the final. Then look at the sheets, and extract FULL frames at the start and end of
# every push/zoom: the framed object must be centred and fully inside the 1080 px.
cd "$(dirname "$0")/.."
OUT=${1:-edit/final.mp4}; mkdir -p work/qa
ROWS=$(python3 -c "import json,math;print(math.ceil(json.load(open('work/plan.json'))['END_s']/10))")
ffmpeg -nostdin -v error -y -i "$OUT" -vf "fps=1,scale=216:384,tile=10x$ROWS" -frames:v 1 work/qa/sheet.jpg
python3 - "$OUT" <<'PY'
import json, subprocess, sys
P = json.load(open("work/plan.json"))
fs = [f for s in P["segments"][1:] for f in (s["f0"] - 1, s["f0"])]
sel = "+".join(f"eq(n\\,{f})" for f in fs)
subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", sys.argv[1], "-vf", f"select='{sel}',scale=216:384,tile=8x{(len(fs) + 7) // 8}",
                "-fps_mode", "passthrough", "-frames:v", "1", "work/qa/junctions.jpg"], check=True)
print("junctions:", len(fs) // 2, "cuts")
PY
zsh work/meas.sh edit/stems/*.wav "$OUT"
echo "sheets: work/qa/sheet.jpg work/qa/junctions.jpg"
