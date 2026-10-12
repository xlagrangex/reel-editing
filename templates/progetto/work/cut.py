"""Step 3. Explicit source spans (reel.json "spans": [id, start, end, label, optional end override]) -> work/cuts.json.
Stuttered words stay outside the spans. Inside a span: onset at the first 10 ms window >= -45 dB, end on RMS
(-35/-32 dB), internal pauses > 250 ms (< -50 dB) split into separate pieces, 40-50 ms lead-in.
Then CHECK every onset on the RMS profile: a span must not start on the tail of a discarded word."""
import json
import numpy as np, soundfile as sf
from common import CFG, FPS

x, sr = sf.read("work/mic.wav"); x = x.astype(np.float64)
W = int(0.01 * sr)
TH, LOW = -35, -32


def db_at(t0, t1):
    seg = x[int(t0 * sr):int(t1 * sr)]; n = len(seg) // W
    return 20 * np.log10(np.sqrt((seg[: n * W].reshape(n, W) ** 2).mean(1) + 1e-14))


clips = []
for sp in CFG["spans"]:
    pid, s, e, lab = sp[:4]
    ovr = sp[4] if len(sp) > 4 else None          # a word that ends softly under -35 dB gets truncated by the RMS rule
    d = db_at(s, e)
    i1 = np.where(d >= TH)[0][-1]
    i0 = np.where(d >= -45)[0][0]
    j = np.where(d >= LOW)[0][-1]
    if i1 - j <= 15:
        j = i1
    if ovr:
        j = int(round((ovr - s) / 0.01)) - 1
    voiced = d >= -50; pieces = []; a = i0; k = i0
    while k <= j:
        if not voiced[k]:
            m = k
            while m <= j and not voiced[m]:
                m += 1
            if m - k > 25:
                pieces.append((a, k)); a = m
            k = m
        else:
            k += 1
    pieces.append((a, j + 1))
    for pi, (a, b) in enumerate(pieces):
        clips.append(dict(ph=pid, label=lab, piece=pi, src_on=round(s + a * 0.01, 3), src_off=round(s + b * 0.01, 3)))

t = 0.0
for i, c in enumerate(clips):
    pre = 0.04 if i == 0 else 0.05
    post = 0.2 if i == len(clips) - 1 else 0.04
    sin, sout = c["src_on"] - pre, c["src_off"] + post
    f_in = round(t * FPS); dur = round((sout - sin) * FPS)
    c.update(src_in=round(sin, 4), tl_f0=f_in, tl_f1=f_in + dur)
    t = (f_in + dur) / FPS
json.dump(clips, open("work/cuts.json", "w"), indent=1)
print("clips", len(clips), "END", clips[-1]["tl_f1"], "frames = %.3f s" % (clips[-1]["tl_f1"] / FPS))
for c in clips:
    print(f"{c['ph']}.{c['piece']} src {c['src_on']:.2f}-{c['src_off']:.2f}  tl {c['tl_f0'] / FPS:.2f}-{c['tl_f1'] / FPS:.2f}  {c['label']}")
    a = c["src_on"]
    prof = db_at(max(0.0, a - 0.2), a + 0.1)
    print("    onset RMS (-200..+100 ms, 20 ms):", " ".join(f"{v:.0f}" for v in prof[::2]))
