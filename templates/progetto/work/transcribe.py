"""Step 1. Mic audio from the footage + word-level transcript -> work/transcript.json, work/words.json.
Whisper skips whole passages (20-60 s holes happen): every voiced region with no words is printed as UNCOVERED,
re-transcribe those with phwords.py before planning the cut."""
import json
import numpy as np, soundfile as sf
from common import CFG, ffmpeg, whisper

ffmpeg("-i", CFG["source"], "-vn", "-ac", "1", "-ar", "48000", "work/mic.wav")
ffmpeg("-i", CFG["source"], "-vn", "-ac", "1", "-ar", "16000", "work/mic16k.wav")
words = whisper("work/mic16k.wav", "work/transcript.json")
json.dump(words, open("work/words.json", "w"), ensure_ascii=False, indent=0)

x, sr = sf.read("work/mic16k.wav")
w = int(0.01 * sr); n = len(x) // w
db = 20 * np.log10(np.sqrt((x[: n * w].reshape(n, w) ** 2).mean(1) + 1e-12))
sp = db > -35
reg, i = [], 0
while i < n:
    if sp[i]:
        j = i
        while j < n and sp[j]:
            j += 1
        if reg and i - reg[-1][1] < 40:
            reg[-1][1] = j
        else:
            reg.append([i, j])
        i = j
    else:
        i += 1
reg = [(a / 100, b / 100) for a, b in reg if b - a >= 20]
print("noise floor p10 %.1f dB, p50 %.1f dB" % tuple(np.percentile(db, [10, 50])))
for a, b in reg:
    ws = [w for w in words if w["e"] > a - 0.05 and w["s"] < b + 0.05]
    tag = "UNCOVERED " if not ws else ""
    print(f"{tag}[{a:7.2f}-{b:7.2f}] " + " ".join(f"{w['w']}@{w['s']:.2f}" for w in ws))
