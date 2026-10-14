"""Picture/voice sync check, on the picture: the face on screen must be the source frame of the word being heard.
In every full-face segment it lines up the final (1x) with cam.mp4 by their motion over 2 s (jump cuts, mouth, head: overlays and the
1.1 punch-in do not move with them), then checks cam.mp4 against the source at the time cuts.json maps it to.
Both best offsets must be 0. A voice-vs-voice check cannot see a stale cam.mp4: this one can.
usage: python work/synccheck.py [FINAL] (default edit/final.mp4)"""
import json, os, subprocess, sys
import numpy as np

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")
FPS = 60
FINAL = sys.argv[1] if len(sys.argv) > 1 else "edit/final.mp4"
CUTS = json.load(open("work/cuts.json"))
PLAN = json.load(open("work/plan.json"))
SRC = json.load(open("reel.json"))["source"]
END = PLAN["END_frames"]
K = [-210, -60, -12, 0, 12, 60, 210]
HALF, LAG = 60, 210


def frames(path, t, n, w=90, h=160):
    b = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{max(t, 0):.4f}", "-i", path, "-frames:v", str(n),
                        "-vf", f"scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(b, np.uint8).reshape(-1, h, w).astype(np.float32)


def motion(fr):
    # face band, below the top overlays and above the subtitles; spikes clipped: a punch-in toggle or a jump cut is one frame of
    # huge motion that only one of the two videos has, and it would drag the correlation onto itself
    m = np.abs(np.diff(fr[:, 50:110], axis=0)).mean(axis=(1, 2))
    return np.minimum(m, 3 * np.median(m))


def src_time(f):
    c = next(c for c in CUTS if c["tl_f0"] <= f < c["tl_f1"])
    return c["src_in"] + (f - c["tl_f0"]) / FPS


bad = 0
for s in [s for s in PLAN["segments"] if s["layout"] == "cam"]:
    f = (s["f0"] + s["f1"]) // 2
    lo, hi = max(f - HALF - LAG, 0), min(f + HALF + LAG, END - 1)
    mf = motion(frames(FINAL, (f - HALF) / FPS - 0.001, 2 * HALF + 1))
    mc = motion(frames("work/cam.mp4", lo / FPS - 0.001, hi - lo + 1))
    lags = [k for k in range(-LAG, LAG + 1) if lo <= f - HALF + k and f + HALF + k <= hi]
    r = {k: float(np.corrcoef(mf, mc[f - HALF + k - lo:f + HALF + k - lo])[0, 1]) for k in lags}
    k1 = max(r, key=r.get)
    cam = frames("work/cam.mp4", f / FPS - 0.001, 1)[0]
    d = {k: float(np.abs(cam - frames(SRC, src_time(f) + k / FPS, 1)[0]).mean()) for k in K}
    k2 = min(d, key=d.get)
    bad += (k1 != 0) + (k2 != 0 or d[0] > 1.5)          # the right source frame differs by < 0.5 here, a wrong one by > 10
    print(f"{s['id']:4} {f / FPS:6.2f} s  final~cam motion best {k1:+4d} f (r {r[k1]:.2f}, next-best lag r {max(v for k, v in r.items() if abs(k - k1) > 3):.2f})"
          f"  cam~source best {k2:+d} f (diff {d[k2]:.1f}, others >= {sorted(d.values())[1]:.1f})")
print("SYNC OK" if not bad else f"SYNC FAIL: {bad} checks off by more than 0 frames")
sys.exit(1 if bad else 0)
