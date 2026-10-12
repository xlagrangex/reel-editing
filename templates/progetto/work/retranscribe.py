"""Step 5. Transcribe the EDITED voice with the stutter prompt -> work/voice_tr.json, then read it all:
no repetitions, no passage of meaning lost.
Whisper collapses identical repetitions ("ma hey... ma hey" comes out once), so this also flags the suspects:
a piece shorter than 1.2 s, or a word longer than 0.8 s. For each flag, re-transcribe the SOURCE around that piece
(a 3 s clip with phwords.py) and compare with the next piece."""
import json
from common import CFG, FPS, whisper

words = whisper("edit/stems/voice.wav", "work/voice_tr.json", prompt=CFG["stutter_prompt"])
C = json.load(open("work/cuts.json"))
print(" ".join(w["w"] for w in words), "\n")
for i, c in enumerate(C):
    a, b = c["tl_f0"] / FPS, c["tl_f1"] / FPS
    ws = [w for w in words if a - 0.05 <= w["s"] < b]
    if b - a < 1.2:
        print(f"SHORT PIECE {c['ph']}.{c['piece']} {a:.2f}-{b:.2f} ({b - a:.2f} s): {' '.join(w['w'] for w in ws)}")
for w in words:
    if w["e"] - w["s"] > 0.8:
        print(f"LONG WORD '{w['w']}' {w['s']:.2f}-{w['e']:.2f} ({w['e'] - w['s']:.2f} s)")
