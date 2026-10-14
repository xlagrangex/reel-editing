"""Step 11. Frame-by-frame compositor -> work/base.mp4.
split: graphic panel on top, full-width face card from y 1010 with rounded top corners (r 75), never a cutout head.
split -> cam expands the card (10 frames, ease in-out); cam -> split collapses it (12 frames, ease-out).
Inside cam segments the punch-in toggles 1.0 / 1.1 at every jump cut (or at the longest pause if there is none).
Graphic segments are hard cuts. Env: RDIR (renders, default work/r), BASE (output)."""
import json, os, subprocess
import numpy as np, cv2
from scipy import ndimage

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")
W, H = 1080, 1920
CARD_TOP, R = 1010, 75
S_SPLIT, FACE_IN_CARD = 1.05, (540, 1480)
PUNCH = 1.1
RDIR = os.environ.get("RDIR", "work/r")
BASE = os.environ.get("BASE", "work/base.mp4")
N_EXP, N_COL = 10, 12
PLAN = json.load(open("work/plan.json"))
SEGS = PLAN["segments"]
END = PLAN["END_frames"]
WORDS = json.load(open("work/tl_words.json"))
CUTS = sorted({c["tl_f0"] for c in json.load(open("work/cuts.json"))})


def face_track():
    rows = [l.split() for l in open("work/ft/faces.txt").read().split("\n") if l.strip()]
    fr = np.array([(int(r[0][:5]) - 1) * 4 for r in rows])
    xy = np.array([[float(r[1]) * W, float(r[2]) * H] for r in rows])
    ok = ~np.isnan(xy[:, 0])
    full = np.stack([np.interp(np.arange(END), fr[ok], xy[ok, k]) for k in (0, 1)], 1)
    # smooth inside each clip only, so the face point jumps with the footage at a cut
    out = full.copy()
    bounds = CUTS + [END]
    for a, b in zip(bounds[:-1], bounds[1:]):
        if b - a > 3:
            out[a:b] = ndimage.gaussian_filter1d(full[a:b], 6, axis=0, mode="nearest")
    return out


def reader(path, ch=3):
    p = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24" if ch == 3 else "rgba", "-"], stdout=subprocess.PIPE)
    n = W * H * ch
    last = None
    try:
        while True:
            b = p.stdout.read(n)
            if len(b) == n:
                last = np.frombuffer(b, np.uint8).reshape(H, W, ch)
            yield last          # a graphic shorter than its segment holds its last frame
    finally:
        p.kill(); p.wait()


def corner_patch():
    y, x = np.mgrid[0:R, 0:R].astype(np.float32) + 0.5
    d = np.hypot(R - x, R - y)
    return np.clip(R - d + 0.5, 0, 1)        # 1 inside the rounded corner, antialiased


CP = corner_patch()
ease_io = lambda t: 0.5 - 0.5 * np.cos(np.pi * t)
ease_out = lambda t: 1 - (1 - t) ** 3


def transform(s, F, target, top):
    """scale s about the origin, face point F lands on target, clamped so the footage covers the card."""
    dx, dy = target[0] - F[0] * s, target[1] - F[1] * s
    dx = min(0.0, max(W - W * s, dx))
    dy = min(float(top), max(H - H * s, dy))
    return s, dx, dy


def check_inputs():
    # cam.mp4 and faces.txt are built from cuts.json: a stale copy slides the face against the voice after the first changed cut
    for p in ("work/cam.mp4", "work/ft/faces.txt"):
        if os.path.getmtime(p) < os.path.getmtime("work/cuts.json"):
            raise SystemExit(f"{p} is older than work/cuts.json: run work/build_cam.py, then work/faces.sh")
    n = int(subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries", "stream=nb_read_packets",
                            "-of", "csv=p=0", "work/cam.mp4"], capture_output=True, text=True, check=True).stdout.strip())
    last = max((int(l.split()[0][:5]) - 1) * 4 for l in open("work/ft/faces.txt") if l.strip())
    if n != END or not END - 8 < last < END:
        raise SystemExit(f"cam.mp4 has {n} frames, faces.txt ends at frame {last}, plan has {END}: run work/build_cam.py, then work/faces.sh")


def main():
    check_inputs()
    face = face_track()
    cam = reader("work/cam.mp4")
    out = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "60", "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "12", "-pix_fmt", "yuv420p", BASE], stdin=subprocess.PIPE)
    yy = np.arange(H, dtype=np.float32)[:, None]
    prev_panel = None
    log = []
    for i, seg in enumerate(SEGS):
        lay, f0, f1 = seg["layout"], seg["f0"], seg["f1"]
        prev = SEGS[i - 1]["layout"] if i else None
        g = reader(f"{RDIR}/{seg['id']}.mp4") if lay != "cam" else None
        ovp = f"{RDIR}/{seg['id']}_ov.mov"
        ov = reader(ovp, 4) if lay == "cam" and os.path.exists(ovp) else None   # light stickers over the full face
        inner = [c for c in CUTS if f0 < c < f1]
        if lay == "cam" and not inner and f1 - f0 > 210:
            # no jump cut to hide: punch in on the longest pause in the middle of the segment
            ws = [w for w in WORDS if f0 / 60 + 0.3 * (f1 - f0) / 60 < w["t0"] < f0 / 60 + 0.7 * (f1 - f0) / 60]
            prevw = {id(b): a for a, b in zip(WORDS[:-1], WORDS[1:])}
            best = max(ws, key=lambda w: w["t0"] - prevw[id(w)]["t1"]) if ws else None
            if best:
                inner = [int(round(best["t0"] * 60)) - 2]
        for f in range(f0, f1):
            c = next(cam)
            gf = next(g) if g is not None else None
            if lay == "gfx":
                out.stdin.write(gf.tobytes()); continue
            k = f - f0
            F = face[f]
            if lay == "split":
                p = 1 - ease_out(min(1, (k + 1) / N_COL)) if prev == "cam" and k < N_COL else 0.0
                panel = gf
                punch = 1.0
            else:
                p = ease_io(min(1, (k + 1) / N_EXP)) if prev == "split" and k < N_EXP else 1.0
                panel = prev_panel if prev == "split" else None
                punch = PUNCH if sum(1 for c_ in inner if c_ <= f) % 2 else 1.0
            top = CARD_TOP * (1 - p)
            ss, sx, sy = transform(S_SPLIT, F, FACE_IN_CARD, CARD_TOP)
            fs, fx, fy = transform(punch, F, F, 0)
            s, dx, dy = ss + (fs - ss) * p, sx + (fx - sx) * p, sy + (fy - sy) * p
            M = np.float32([[s, 0, dx], [0, s, dy]])
            foot = cv2.warpAffine(c, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            if p >= 1:
                o = foot
            else:
                a = np.clip(yy - top + 0.5, 0, 1).repeat(W, 1)
                t0 = int(np.floor(top))
                if t0 + R <= H:
                    patch = a[t0:t0 + R, :R] * CP; a[t0:t0 + R, :R] = patch
                    a[t0:t0 + R, W - R:] = a[t0:t0 + R, W - R:] * CP[:, ::-1]
                bgp = panel.astype(np.float32) if panel is not None else np.zeros((H, W, 3), np.float32)
                if lay == "cam":
                    bgp = bgp + (255 - bgp) * 0.6 * p   # the panel being covered fades to white
                o = bgp * (1 - a[..., None]) + foot.astype(np.float32) * a[..., None]
                o = np.clip(o, 0, 255).astype(np.uint8)
            if ov is not None:
                ofr = next(ov)
                if ofr is not None:
                    a = ofr[..., 3:4].astype(np.float32) / 255
                    o = np.clip(ofr[..., :3] * a + o.astype(np.float32) * (1 - a), 0, 255).astype(np.uint8)
            out.stdin.write(o.tobytes())
            if lay == "split":
                prev_panel = gf
        if g is not None:
            g.close()
        if ov is not None:
            ov.close()
        log.append(f"{seg['id']} {lay} {f0}-{f1} punch-cuts {len(inner)}")
        print(log[-1], flush=True)
    out.stdin.close(); out.wait()


if __name__ == "__main__":
    main()
