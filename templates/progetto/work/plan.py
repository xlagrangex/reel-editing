"""Step 8. Segment plan -> work/plan.json + work/tl_words.json (words on the timeline = transcript of the edited voice).
reel.json "segments": [id, layout, start key "<span id>.<piece>", label]; a segment runs to the next one's start.
Layouts: split (graphic panel on top, face card below), cam (full face, light overlays allowed), gfx (full graphic).
Rules checked here: hook in split, outro on camera, <= ~8 s per segment, never the same layout twice in a row."""
import json
from common import CFG, FPS

C = json.load(open("work/cuts.json"))
T = json.load(open("work/voice_tr.json"))
tw = [dict(w=w["word"].strip(), t0=round(w["start"], 3), t1=round(w["end"], 3)) for s in T["segments"] for w in s["words"]]
json.dump(tw, open("work/tl_words.json", "w"), indent=0, ensure_ascii=False)
J = {f"{c['ph']}.{c['piece']}": c["tl_f0"] for c in C}
END = C[-1]["tl_f1"]
S = CFG["segments"]
segs = []
for i, (sid, lay, k, lab) in enumerate(S):
    a = J[k]; b = J[S[i + 1][2]] if i + 1 < len(S) else END
    text = " ".join(x["w"] for x in tw if a / FPS <= x["t0"] < b / FPS)
    segs.append(dict(id=sid, layout=lay, f0=a, f1=b, t0=round(a / FPS, 3), t1=round(b / FPS, 3), dur=round((b - a) / FPS, 3), label=lab, text=text))
json.dump(dict(END_frames=END, END_s=END / FPS, segments=segs), open("work/plan.json", "w"), indent=1, ensure_ascii=False)
for s in segs:
    print(f"{s['id']:4} {s['layout']:5} {s['t0']:7.3f}-{s['t1']:7.3f} ({s['dur']:5.2f}s) {s['text']}")
warn = []
if segs[0]["layout"] != "split":
    warn.append("the hook is not a split")
if segs[-1]["layout"] != "cam":
    warn.append("the outro is not on camera")
warn += [f"{s['id']} lasts {s['dur']:.1f} s (> 8)" for s in segs if s["dur"] > 8.5]
warn += [f"{a['id']} and {b['id']} are both {a['layout']}" for a, b in zip(segs, segs[1:]) if a["layout"] == b["layout"]]
for w in warn:
    print("WARN", w)
