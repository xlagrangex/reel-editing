"""Step 4. Voice track from cuts.json -> edit/stems/voice.wav (stereo, 24 bit, -14 LUFS, peaks <= -2 dBFS).
J-cut: each clip's audio starts 50 ms before its picture; the tail stays at full level until it reaches the noise
floor, then fades over 170 ms. Loudness is measured on the stereo file (a duplicated mono reads +3 LU in ebur128)."""
import json, os
import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.ndimage import minimum_filter1d, uniform_filter1d
from common import FPS

x, sr = sf.read("work/mic.wav"); x = x.astype(np.float64)
C = json.load(open("work/cuts.json"))
END = C[-1]["tl_f1"] / FPS; N = int(round(END * sr))
out = np.zeros(N)
W = int(0.01 * sr)
LEAD, FADE, FLOOR = 0.05, 0.17, -62


def rms_db(a, b):
    return 20 * np.log10(np.sqrt((x[a:b] ** 2).mean() + 1e-14))


for i, c in enumerate(C):
    T0, T1 = c["tl_f0"] / FPS, c["tl_f1"] / FPS
    a_tl0 = 0 if i == 0 else T0 - LEAD
    a_src0 = c["src_in"] - (T0 - a_tl0)
    if i == len(C) - 1:
        tail_end, fade_start = END, END - 0.06
    else:
        nxt = C[i + 1]
        next_onset = nxt["tl_f0"] / FPS + (nxt["src_on"] - nxt["src_in"])
        s_end = c["src_in"] + (T1 - T0)
        t = s_end
        while t < s_end + 0.4 and rms_db(int(t * sr), int(t * sr) + W) > FLOOR:
            t += 0.01
        fade_start = min(T1 + (t - s_end), next_onset - 0.02)
        tail_end = min(fade_start + FADE, next_onset)
    n = int(round((tail_end - a_tl0) * sr)); a = int(round(a_tl0 * sr)); sa = int(round(a_src0 * sr))
    seg = x[sa:sa + n].copy()
    env = np.ones(len(seg))
    fs = int(round((fade_start - a_tl0) * sr))
    if fs < len(seg):
        env[fs:] = np.cos(np.linspace(0, np.pi / 2, len(seg) - fs)) ** 2
    if i > 0:
        k = int(0.005 * sr); env[:k] *= np.linspace(0, 1, k)
    out[a:a + len(seg)] += seg * env

meter = pyln.Meter(sr)
st = lambda m: np.stack([m, m], 1)


def lim(m, ceil):
    c = 10 ** (ceil / 20); g0 = np.minimum(1, c / np.maximum(np.abs(m), 1e-9))
    L = int(0.004 * sr)
    g = uniform_filter1d(minimum_filter1d(g0, 2 * L + 1), 2 * L + 1)
    return m * np.minimum(g, minimum_filter1d(g0, 3))


m = out * 10 ** ((-14 - meter.integrated_loudness(st(out))) / 20)
for _ in range(6):
    m = lim(m, -2.0)
    m *= 10 ** ((-14 - meter.integrated_loudness(st(m))) / 20)
m = lim(m, -2.0)
os.makedirs("edit/stems", exist_ok=True)
sf.write("edit/stems/voice.wav", st(m), sr, subtype="PCM_24")
json.dump(dict(END=END, N=N), open("work/end.json", "w"))
print("voice LUFS %.2f  peak %.2f dBFS  END %.3f s" % (meter.integrated_loudness(st(m)), 20 * np.log10(np.abs(m).max()), END))
