"""Step 13. Audio: sfx + riser + music stems (full length) and the master -> edit/stems/*.wav, work/master_f.wav.
Few sounds, real ones. Synthesised here only the discreet UI sounds (click, pop, whoosh, typing, ticks, reel stop).
Anything recognisable (a notification, a famous meme sound) is a real sample in sfx/, never re-synthesised:
  {"t": 1.2, "type": "sample", "file": "sfx/name.wav", "db": -6}   ("db" relative to the voice peak)
  {"t": 1.2, "type": "soldi"}                                        = sfx/soldi.wav at -3 dB: the Shopify sale "cha-ching"
A sample that is missing is skipped with a warning: where no sound has been chosen, silence.
Music: reel.json "music" (or MUSIC=<file>) replaces the synthesised bed; either way it sits at -27 LUFS.
Master: -14 LUFS integrated, true peak <= -1 dBTP. Env: STEMS, MASTER."""
import glob, json, os, re, subprocess
import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.signal import butter, sosfilt, resample_poly
from common import CFG

SR = 48000
P = json.load(open("work/plan.json"))
END = P["END_s"]
N = int(round(END * SR))
rng = np.random.default_rng(7)
meter = pyln.Meter(SR)
STEMS = os.environ.get("STEMS", "edit/stems")
MASTER = os.environ.get("MASTER", "work/master_f.wav")
os.makedirs(STEMS, exist_ok=True)
voice, _ = sf.read("edit/stems/voice.wav")
VPK = np.abs(voice).max()
db = lambda x: 10 ** (x / 20)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)


def env(n, a, d):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / d)
    return e


def norm_peak(x, peak):
    return x / (np.abs(x).max() + 1e-12) * peak


# ------------------------------------------------------------------ sfx voices
def s_click():
    n = int(0.06 * SR); t = np.arange(n) / SR
    body = bp(rng.standard_normal(n), 2500, 7000) * env(n, 0.0005, 0.006)
    ping = np.sin(2 * np.pi * 3400 * t) * env(n, 0.0008, 0.012) * 0.5
    thump = np.sin(2 * np.pi * 180 * t) * env(n, 0.001, 0.015) * 0.4
    return body + ping + thump


def s_key(soft=1.0):
    n = int(0.05 * SR); t = np.arange(n) / SR
    f = 1800 + rng.uniform(-300, 300)
    tick = bp(rng.standard_normal(n), f, f * 2.6) * env(n, 0.0004, 0.005)
    thud = np.sin(2 * np.pi * (140 + rng.uniform(-15, 15)) * t) * env(n, 0.001, 0.012) * 0.6
    return (tick + thud) * soft


def s_pop():
    n = int(0.25 * SR); t = np.arange(n) / SR
    f = 150 * np.exp(-t / 0.05) + 72
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * env(n, 0.002, 0.07)
    air = lp(rng.standard_normal(n), 900) * env(n, 0.001, 0.02) * 0.35
    return body + air


def s_whoosh(var):
    # low, airy filtered noise, loudest exactly at its centre
    dur = [0.95, 0.85, 1.05, 0.9][var % 4]
    n = int(dur * SR); t = np.arange(n) / SR; c = dur / 2
    x = rng.standard_normal(n)
    shape = np.exp(-((t - c) / (dur * [0.22, 0.2, 0.25, 0.21][var % 4])) ** 2)
    # sweep: blend of a low band and a slightly higher band crossing at the centre
    lo = bp(x, 120, 700); hi = bp(x, 350, [1400, 1200, 1600, 1300][var % 4])
    k = np.clip((t - c * 0.6) / (c * 0.8), 0, 1)
    y = (lo * (1 - 0.5 * k) + hi * (0.4 + 0.5 * k)) * shape
    return lp(y, 2200), int(c * SR)


def s_reelstop():
    n = int(.3 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * 160 * t) * env(n, .001, .05) + bp(rng.standard_normal(n), 1500, 4500) * env(n, .0005, .01) * .6


def load(path):
    """a real sample, any format, as 48 kHz mono"""
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


SYNTH = {"click": s_click, "key": s_key, "pop": s_pop, "reelstop": s_reelstop}
LV = {"click": -10, "pop": -10, "whoosh": -9, "key": -16, "keys": -16, "ticks": -16, "spin": -18, "reelstop": -10, "soldi": -3}

# ------------------------------------------------------------------ events: the sfx list inside every composition
events = []
for f in sorted(glob.glob("gfx/compositions/*.html")):
    sid = os.path.basename(f)[:-5]
    seg = next((s for s in P["segments"] if s["id"] == sid), None)
    m = re.search(r'<script type="application/json" id="sfx">(.*?)</script>', open(f).read(), re.S)
    if seg is None or not m:
        continue
    for e in json.loads(m.group(1)):
        e = dict(e); e["t"] = round(seg["t0"] + e["t"], 3); e["seg"] = sid
        events.append(e)
events.sort(key=lambda e: e["t"])

sfx = np.zeros(N)
wv = 0
for e in events:
    typ = e["type"]
    i0 = int(round(e["t"] * SR))
    if typ in ("keys", "ticks", "spin"):
        pk = VPK * db(LV[typ])
        step = {"keys": 0.075, "ticks": 0.05, "spin": 0.045}[typ]
        k = 0; t = e["t"]
        while t < e["t"] + e["dur"]:
            s = norm_peak(s_key(), pk * (0.85 + 0.15 * ((k * 7) % 5) / 4) * (0.8 if typ == "ticks" else 1))
            j = int(round(t * SR)); sfx[j:j + len(s)] += s[: max(0, min(len(s), N - j))]
            t += step * (1 + 0.25 * np.sin(k * 1.7)); k += 1
        continue
    if typ == "whoosh":                          # centred on its event time: put it at the middle of a whip
        s, ci = s_whoosh(wv); wv += 1
        s = norm_peak(s, VPK * db(LV[typ])); i0 -= ci
    elif typ in ("sample", "soldi"):
        path = e.get("file", "sfx/soldi.wav")
        if not os.path.exists(path):
            print(f"WARN {e['seg']} @{e['t']:.2f}s: {path} missing -> silence")
            continue
        s = norm_peak(load(path), VPK * db(e.get("db", LV.get(typ, -6))))
    elif typ in SYNTH:
        s = norm_peak(SYNTH[typ](), VPK * db(e.get("db", LV[typ])))
    else:
        print(f"WARN {e['seg']} @{e['t']:.2f}s: unknown sound '{typ}' -> silence")
        continue
    a = max(i0, 0); s = s[a - i0:]
    sfx[a:a + len(s)] += s[: max(0, min(len(s), N - a))]
json.dump(events, open(STEMS + "/sfx_events.json", "w"), indent=0)

# ------------------------------------------------------------------ riser: ends exactly on the hook seam (start of the 2nd segment)
SEAM = CFG.get("riser_at") or (P["segments"][1]["t0"] if len(P["segments"]) > 1 else 0)
riser = np.zeros(N)
if SEAM > 2.8:
    RD = 2.6
    n = int(RD * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n)
    fc = 180 * (1 + 7 * (t / RD) ** 2.2)
    y = np.zeros(n); blk = 2400
    for b in range(0, n, blk):                       # time-varying band from 180 Hz up to ~1.4 kHz
        seg = bp(x[max(0, b - 4800):b + blk], fc[b] * 0.6, fc[b] * 1.6)[-min(blk, n - b):]
        y[b:b + len(seg)] = seg
    sub = np.sin(2 * np.pi * np.cumsum(55 + 55 * (t / RD) ** 2) / SR) * 0.6
    r = (y + sub) * (t / RD) ** 2.4
    r[-int(0.008 * SR):] *= np.linspace(1, 0, int(0.008 * SR))
    r = norm_peak(r, VPK * db(-14))
    riser = np.zeros(N); a = int(round((SEAM - RD) * SR)); riser[a:a + n] = r[: N - a]
# ------------------------------------------------------------------ music: warm minimal electronic, 110 BPM
BPM = 110; beat = 60 / BPM; T0 = 1 / 60
music = np.zeros((N, 2))
tt = np.arange(N) / SR


def note(f):
    return 440 * 2 ** ((f - 69) / 12)


CH = [[53, 57, 60, 64], [57, 60, 64, 67], [50, 53, 57, 60, 64], [48, 52, 55, 59]]   # Fmaj7 Am7 Dm9 Cmaj7
BASS = [41, 45, 38, 36]
bar = 4 * beat
nbars = int(np.ceil((END - T0) / bar)) + 1
pad = np.zeros(N); bass = np.zeros(N); kick = np.zeros(N); hat = np.zeros(N); rim = np.zeros(N)
for b in range(nbars):
    st = T0 + b * bar
    ch = CH[(b // 2) % 4]; i0 = int(st * SR); L = int(2 * bar * SR) if b % 2 == 0 else 0
    if L:
        m = min(L, N - i0)
        if m > 0:
            t2 = np.arange(m) / SR
            sig = np.zeros(m)
            for k, mn in enumerate(ch):
                for det in (-0.06, 0.06):
                    f = note(mn) * 2 ** (det / 12)
                    sig += np.sin(2 * np.pi * f * t2 + k) * 0.6 + np.sin(2 * np.pi * 2 * f * t2) * 0.12
            a = np.minimum(1, t2 / 0.6) * np.minimum(1, (L / SR - t2) / 0.5)
            pad[i0:i0 + m] += sig * a
    for q in range(4):
        bt = st + q * beat; j = int(bt * SR)
        if j >= N: break
        m = min(int(0.4 * SR), N - j); t2 = np.arange(m) / SR
        if q in (0, 2) or (q == 3 and b % 2 == 1):          # soft kick
            f = 48 + 70 * np.exp(-t2 / 0.03)
            kick[j:j + m] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t2 / 0.16)
        if q in (1, 3):                                      # soft rim/clap, very low
            mm = min(int(0.12 * SR), N - j)
            rim[j:j + mm] += bp(rng.standard_normal(mm), 900, 2500) * np.exp(-np.arange(mm) / SR / 0.03)
        for h in (0.5,):                                     # off-beat hat
            jh = int((bt + h * beat) * SR)
            if jh < N:
                mm = min(int(0.06 * SR), N - jh)
                hat[jh:jh + mm] += hp(rng.standard_normal(mm), 7000) * np.exp(-np.arange(mm) / SR / 0.015)
        # bass: root on beats 1 and the "and" of 3
        for bo in ((0.0, 1.2) if q == 0 else ((0.5, 0.9) if q == 2 else ())):
            if not bo: continue
        if q in (0, 2):
            jb = int((bt + (0 if q == 0 else 0.5 * beat)) * SR); mb = min(int(beat * 1.3 * SR), N - jb)
            if mb > 0:
                tb = np.arange(mb) / SR; fb = note(BASS[(b // 2) % 4])
                bass[jb:jb + mb] += (np.sin(2 * np.pi * fb * tb) + 0.25 * np.sin(2 * np.pi * 2 * fb * tb)) * np.minimum(1, tb / 0.01) * np.exp(-tb / 0.45)
pad = lp(pad, 1400, 2) * 0.22
bass = lp(bass, 400, 2) * 0.55
mono = pad + bass + kick * 0.7 + rim * 0.06 + hat * 0.05
# gentle stereo width on the pad and hats only
side = lp(np.roll(pad, int(0.012 * SR)), 1400) * 0.25 + np.roll(hat, int(0.004 * SR)) * 0.02
music[:, 0] = mono + side; music[:, 1] = mono - side
music[: int(T0 * SR)] = 0
dc = int(0.005 * SR); s0 = int(T0 * SR); music[s0:s0 + dc] *= np.linspace(0, 1, dc)[:, None]
fo = int(0.8 * SR); music[-fo:] *= np.linspace(1, 0, fo)[:, None]
music *= db(-27 - meter.integrated_loudness(music))
MUSIC = os.environ.get("MUSIC") or CFG.get("music")
if MUSIC:
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", MUSIC, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    m = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    music = np.zeros((N, 2)); L = min(N, len(m)); music[:L] = m[:L]
    fo = int(1.2 * SR); music[-fo:] *= np.linspace(1, 0, fo)[:, None]
    music *= db(-27 - meter.integrated_loudness(music))

st = lambda m: np.stack([m, m], 1)
sf.write(STEMS + "/sfx.wav", st(sfx), SR, subtype="PCM_24")
sf.write(STEMS + "/riser.wav", st(riser), SR, subtype="PCM_24")
sf.write(STEMS + "/music.wav", music, SR, subtype="PCM_24")

# ------------------------------------------------------------------ master: plain sum, transparent limiter only if needed
mix = voice[:N] + st(sfx) + st(riser) + music
# true-peak estimate via 4x oversampling
from scipy.signal import resample_poly
tp = 20 * np.log10(np.abs(resample_poly(mix, 4, 1, axis=0)).max())
print("pre-limit integrated", round(meter.integrated_loudness(mix), 2), "true peak", round(tp, 2))
if tp > -1.0:
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    c = db(-1.3); a = np.abs(mix).max(1)
    g = np.minimum(1, c / np.maximum(a, 1e-9)); L = int(0.003 * SR)
    g = uniform_filter1d(minimum_filter1d(g, 2 * L + 1), 2 * L + 1)
    g = np.minimum(g, minimum_filter1d(np.minimum(1, c / np.maximum(a, 1e-9)), 3))
    mix = mix * g[:, None]
    print("limiter applied; max gain reduction dB", round(20 * np.log10(g.min()), 2))
sf.write(MASTER.replace("_f", ""), mix, SR, subtype="PCM_24")
# delivery master: integrated -14 LUFS, true peak kept under -1 dBTP
g = db(-14 - meter.integrated_loudness(mix))
mf = mix * g
tpf = 20 * np.log10(np.abs(resample_poly(mf, 4, 1, axis=0)).max())
if tpf > -1.0:
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    c = db(-1.4); a = np.abs(mf).max(1); L = int(0.003 * SR)
    gg = uniform_filter1d(minimum_filter1d(np.minimum(1, c / np.maximum(a, 1e-9)), 2 * L + 1), 2 * L + 1)
    mf = mf * gg[:, None]
sf.write(MASTER, mf, SR, subtype="PCM_24")
print("events", len(events), "| master", MASTER)
