"""Step 6. Picture track from cuts.json -> work/cam.mp4 (60 fps, frame-exact cuts, no audio)."""
import json
from common import CFG, FPS, ffmpeg

C = json.load(open("work/cuts.json"))
args, fc = [], []
for i, c in enumerate(C):
    n = c["tl_f1"] - c["tl_f0"]
    args += ["-ss", "%.4f" % c["src_in"], "-t", "%.4f" % (n / FPS + 0.2), "-i", CFG["source"]]
    fc.append(f"[{i}:v]fps={FPS},trim=end_frame={n},setpts=PTS-STARTPTS,format=yuv420p[v{i}]")
fc.append("".join(f"[v{i}]" for i in range(len(C))) + f"concat=n={len(C)}:v=1:a=0[out]")
ffmpeg(*args, "-filter_complex", ";".join(fc), "-map", "[out]", "-an", "-c:v", "libx264", "-crf", "10", "-preset", "fast", "-r", str(FPS), "work/cam.mp4")
print("work/cam.mp4", sum(c["tl_f1"] - c["tl_f0"] for c in C), "frames")
