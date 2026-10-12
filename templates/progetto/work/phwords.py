"""Step 2, stutter hunt. Re-transcribe short source windows with a prompt full of fillers, so Whisper also writes
false starts, fillers and repetitions, with tighter timestamps than the long pass.
usage: python work/phwords.py P01:0.8-11.3 P02:29-35.2   ->   work/phwords.json (merged), words in source seconds"""
import json, os, sys
from common import CFG, ffmpeg, whisper

os.makedirs("work/ph", exist_ok=True)
out = json.load(open("work/phwords.json")) if os.path.exists("work/phwords.json") else {}
for arg in sys.argv[1:]:
    k, rng = arg.split(":")
    a, b = (float(v) for v in rng.split("-"))
    wav = f"work/ph/{k}.wav"
    ffmpeg("-ss", str(a), "-t", str(b - a), "-i", CFG["source"], "-ac", "1", "-ar", "16000", wav)
    ws = whisper(wav, prompt=CFG["stutter_prompt"], offset=a)
    out[k] = ws
    print(k, " ".join(f"{w['w']}[{w['s']:.2f}-{w['e']:.2f}]" for w in ws))
json.dump(out, open("work/phwords.json", "w"), ensure_ascii=False)
