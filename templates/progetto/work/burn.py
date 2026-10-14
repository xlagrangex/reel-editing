"""Step 14. Final pass without a browser: base.mp4 + subtitles + cover (frame 0) drawn with PIL, muxed with the master
-> edit/final.mp4. Theme: Plus Jakarta Sans ExtraBold, tight; navy ink on the white panel and graphics; on the footage
white with a soft, evident shadow (never a black outline), highlight words in the blue gradient with a thin white rim.
Each block settles in from 0.92 to 1.0 scale over 0.1 s.
reel.json "stops": black and white from the phrase to the next segment (the music pauses there too, audio.py).
Env: BASE, MASTER, OUT; DARK="S04,S07@5.0" = footage-style subtitles on graphic segments shot on a photo
("@5.0" = only blocks starting in the first 5.0 s of that segment)."""
import json, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from common import CFG, stop_windows

W, H, FPS = 1080, 1920, 60
FONT = "gfx/assets/fonts/PlusJakartaSans-800-latin.woff2"
INK, WHITE = (12, 31, 63), (255, 255, 255)
GRAD = [(0.0, (10, 63, 214)), (0.5, (27, 116, 255)), (1.0, (42, 169, 245))]
CY = {"split": 948, "cam": 1400, "gfx": 1400}
P = json.load(open("work/plan.json"))
END = P["END_frames"]
BASE = os.environ.get("BASE", "work/base.mp4")
MASTER = os.environ.get("MASTER", "work/master_f.wav")
OUT = os.environ.get("OUT", "edit/final.mp4")
DARK = {}
for e in filter(None, os.environ.get("DARK", "").split(",")):
    sid, _, cut = e.partition("@")
    DARK[sid] = float(cut) if cut else 1e9
SEG_T0 = {s["id"]: s["t0"] for s in P["segments"]}
B = json.load(open("work/subs.json"))


def is_dark(b):
    return b["layout"] == "cam" or (b["seg"] in DARK and b["a"] - SEG_T0[b["seg"]] < DARK[b["seg"]])


def gradient(w, h, stops):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    t = np.clip((x / max(w, 1) + y / max(h, 1)) / 2, 0, 1)      # 135 degrees
    out = np.zeros((h, w, 3), np.float32)
    for (t0, c0), (t1, c1) in zip(stops[:-1], stops[1:]):
        m = (t >= t0) & (t <= t1)
        k = ((t - t0) / (t1 - t0))[m][:, None]
        out[m] = np.array(c0) * (1 - k) + np.array(c1) * k
    return out


def text_mask(text, size, track):
    f = ImageFont.truetype(FONT, size)
    adv = [f.getlength(c) + track * size + (0.08 * size if c == " " else 0) for c in text]   # tight letters, open word gaps
    w = int(sum(adv) - track * size) + 4
    asc, desc = f.getmetrics()
    m = Image.new("L", (w, asc + desc + 4), 0)
    d = ImageDraw.Draw(m)
    x = 2
    for c, a in zip(text, adv):
        d.text((x, 2), c, font=f, fill=255)
        x += a
    return m


def over(dst, rgb, a):
    """composite a colour layer with alpha a over an RGBA float image"""
    da = dst[..., 3]
    oa = a + da * (1 - a)
    dst[..., :3] = (rgb * a[..., None] + dst[..., :3] * (da * (1 - a))[..., None]) / np.maximum(oa, 1e-6)[..., None]
    dst[..., 3] = oa


def block_image(text, hl, dark):
    """dark = on the footage: soft, evident drop shadow instead of an outline; highlight words also get a thin white rim.
    light = on the white panel / graphics: plain ink, gradient on highlights."""
    size = 86 if hl else 72
    m = text_mask(text, size, -0.02)
    if m.width > 980:                                   # a long block shrinks instead of touching the edges
        size = int(size * 980 / m.width); m = text_mask(text, size, -0.02)
    pad = 40
    w, h = m.width + 2 * pad, m.height + 2 * pad
    mask = Image.new("L", (w, h), 0); mask.paste(m, (pad, pad))
    a = np.asarray(mask, np.float32) / 255
    if hl:
        fill = gradient(w, h, GRAD)
    else:
        fill = np.empty((h, w, 3), np.float32); fill[:] = WHITE if dark else INK
    rgba = np.zeros((h, w, 4), np.float32)
    if dark:
        rim = mask.filter(ImageFilter.MaxFilter(7)) if hl else mask
        sh = Image.new("L", (w, h), 0); sh.paste(rim, (0, 7))
        sha = np.asarray(sh.filter(ImageFilter.GaussianBlur(11)), np.float32) / 255
        over(rgba, np.array(INK, np.float32), np.clip(sha * 1.5, 0, 1) * 0.72)
        if hl:
            ra = np.asarray(rim.filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255
            over(rgba, np.array(WHITE, np.float32), ra)
    over(rgba, fill, a)
    return rgba


def cover_image():
    bx, by, bw, bh, r = 50, 262, 980, 341, 30
    img = np.zeros((H, W, 4), np.float32)
    # soft shadow
    sh = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sh).rounded_rectangle((bx, by + 30, bx + bw, by + bh + 30), r, fill=60)
    sh = np.asarray(sh.filter(ImageFilter.GaussianBlur(40)), np.float32) / 255
    img[..., :3] = (12, 40, 100); img[..., 3] = sh * 0.6
    outer = Image.new("L", (W, H), 0); ImageDraw.Draw(outer).rounded_rectangle((bx, by, bx + bw, by + bh), r, fill=255)
    inner = Image.new("L", (W, H), 0); ImageDraw.Draw(inner).rounded_rectangle((bx + 4, by + 4, bx + bw - 4, by + bh - 4), r - 4, fill=255)
    oa = np.asarray(outer, np.float32) / 255; ia = np.asarray(inner, np.float32) / 255
    g = np.zeros((H, W, 3), np.float32); g[by:by + bh, bx:bx + bw] = gradient(bw, bh, GRAD)
    col = g * (1 - ia[..., None]) + 255 * ia[..., None]
    img[..., :3] = col * oa[..., None] + img[..., :3] * (1 - oa[..., None])
    img[..., 3] = oa + img[..., 3] * (1 - oa)
    # title lines from reel.json "cover": {"lines": [...], "accent": "word"}; the accent word goes in the gradient
    lines, accent = CFG["cover"]["lines"], CFG["cover"].get("accent", "")
    size = 110 if max(len(l) for l in lines) <= 14 else 92 if max(len(l) for l in lines) <= 17 else 76
    f = ImageFont.truetype(FONT, size); tr = -0.03 * size
    gap = size * 1.09
    for li, line in enumerate(lines):
        cy = by + bh / 2 + (li - (len(lines) - 1) / 2) * gap
        m = text_mask(line, size, -0.03)
        a = np.asarray(m, np.float32) / 255
        x0 = int(W / 2 - m.width / 2); y0 = int(cy - m.height / 2)
        fill = np.empty(a.shape + (3,), np.float32); fill[:] = INK
        k = line.find(accent) if accent else -1
        if k >= 0:
            adv = lambda c: f.getlength(c) + tr + (0.08 * size if c == " " else 0)
            xa = 2 + sum(adv(c) for c in line[:k]); xb = xa + sum(adv(c) for c in accent)
            gx = gradient(int(xb - xa) + 2, a.shape[0], GRAD)
            fill[:, int(xa):int(xa) + gx.shape[1]] = gx[:, : fill.shape[1] - int(xa)]
        reg = img[y0:y0 + a.shape[0], x0:x0 + a.shape[1]]
        reg[..., :3] = fill * a[..., None] + reg[..., :3] * (1 - a[..., None])
        reg[..., 3] = a + reg[..., 3] * (1 - a)
    return img


def paste(frame, rgba, cx, cy, s=1.0):
    if s != 1.0:
        im = Image.fromarray(np.clip(rgba * [1, 1, 1, 255], 0, 255).astype(np.uint8), "RGBA")
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)
        rgba = np.asarray(im, np.float32) / [1, 1, 1, 255]
    h, w = rgba.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb:
        return
    src = rgba[ya - y0:yb - y0, xa - x0:xb - x0]
    a = src[..., 3:4]
    dst = frame[ya:yb, xa:xb].astype(np.float32)
    frame[ya:yb, xa:xb] = np.clip(src[..., :3] * a + dst * (1 - a), 0, 255).astype(np.uint8)


def main():
    imgs = []
    for b in B:
        f0, f1 = int(round(b["a"] * FPS)), int(round(b["b"] * FPS))
        imgs.append((f0, f1, block_image(b["text"], b["hl"], is_dark(b)), CY[b["layout"]]))
    cover = cover_image()
    bw = [(int(round(t0 * FPS)), int(round(t1 * FPS))) for t0, t1 in stop_windows()]
    src = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-i", BASE, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    out = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-i", MASTER, "-map", "0:v", "-map", "1:a", "-frames:v", str(END),
                            "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", "120", "-bf", "2",
                            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                            "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
    n = W * H * 3
    k = 0
    for f in range(END):
        buf = src.stdout.read(n)
        if len(buf) < n:
            break
        fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
        if any(a <= f < b for a, b in bw):
            y = fr.astype(np.float32) @ np.array([0.2126, 0.7152, 0.0722], np.float32)      # Rec.709 luma
            fr[:] = np.clip((y - 128) * 1.08 + 128, 0, 255).astype(np.uint8)[:, :, None]    # a touch of contrast
        if f == 0:
            paste(fr, cover, W / 2, H / 2)
        while k < len(imgs) and imgs[k][1] <= f:
            k += 1
        for f0, f1, im, cy in imgs[k:k + 2]:
            if f0 <= f < f1:
                s = 0.92 + 0.08 * min(1, (f - f0) / 6) ** 0.5
                paste(fr, im, W / 2, cy, s)
        out.stdin.write(fr.tobytes())
    out.stdin.close(); out.wait(); src.kill()


if __name__ == "__main__":
    main()
