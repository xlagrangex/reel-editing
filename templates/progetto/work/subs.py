"""Step 12. Subtitle blocks from the edited voice transcript -> work/subs.json.
1-3 words per block, broken on punctuation, pauses > 250 ms, segment changes and capitalised words. Highlights
(bigger, in the gradient) every 2-3 blocks, never two in a row, only on the words listed in reel.json "subs":
  fix          {"heard": "written"}  Whisper mistakes; "" drops the word (a slip that should not be read)
  keywords     words worth a highlight (lowercase)
  pairs        [["30", "milioni"]]   two words highlighted together
  keep_caps    capitalised words that do NOT start a new block (brand names, "AI")
  skip_segments  segments without subtitles (a title page that already spells the words out)"""
import json, re
from common import CFG

C = CFG.get("subs", {})
FIX = C.get("fix", {}); KEY = {k.lower() for k in C.get("keywords", [])}
PAIR = {tuple(p) for p in C.get("pairs", [])}; CAPS = set(C.get("keep_caps", []))
d = json.load(open("work/voice_tr.json")); P = json.load(open("work/plan.json"))
raw = [dict(w=w["word"].strip(), a=w["start"], b=w["end"]) for s in d["segments"] for w in s["words"]]
ws = []
for w in raw:                                   # Whisper splits elisions and compounds into separate tokens
    if ws and (w["w"].startswith("'") or w["w"].startswith("-")):
        ws[-1]["w"] += w["w"]; ws[-1]["b"] = w["b"]
    else:
        ws.append(dict(w))
for w in ws:
    core = re.sub(r"[,.!?]+$", "", w["w"])
    w["punct"] = bool(re.search(r"[,.?!]$", w["w"]))
    w["t"] = FIX.get(core, core)
ws = [w for w in ws if w["t"]]
for k in range(len(ws) - 2, -1, -1):           # an elision fixed by hand ("Le" -> "L'") glues to the next word
    if ws[k]["t"].endswith("'"):
        ws[k]["t"] += ws[k + 1]["t"]; ws[k]["b"] = ws[k + 1]["b"]; ws[k]["punct"] = ws[k + 1]["punct"]; del ws[k + 1]
SEGS = P["segments"]


def lay(t):
    for s in SEGS:
        if s["t0"] <= max(t, 0) < s["t1"]:
            return s["layout"], s["id"]
    return SEGS[-1]["layout"], SEGS[-1]["id"]


def is_key(i):
    lo = ws[i]["t"].lower(); nxt = ws[i + 1]["t"].lower() if i + 1 < len(ws) else ""
    return lo in KEY or (lo, nxt) in PAIR


blocks = []; i = 0; since = 0; last_hl = False
while i < len(ws):
    hl = False; n = 1
    if is_key(i) and since >= 2 and not last_hl:
        hl = True
        n = 2 if (ws[i]["t"].lower(), ws[i + 1]["t"].lower() if i + 1 < len(ws) else "") in PAIR else 1
    if not hl:
        while n < 3 and i + n < len(ws):
            prev, cur = ws[i + n - 1], ws[i + n]
            if prev["punct"] or cur["a"] - prev["b"] > 0.25:
                break
            if lay(cur["a"] + 0.12)[1] != lay(ws[i]["a"] + 0.01)[1]:
                break
            if cur["t"][:1].isupper() and cur["t"] not in CAPS:
                break
            if is_key(i + n) and since + 1 >= 2:
                break
            if len(" ".join(x["t"] for x in ws[i:i + n + 1])) > 18:
                break
            n += 1
    grp = ws[i:i + n]
    blocks.append(dict(text=" ".join(x["t"] for x in grp), a=grp[0]["a"], b=grp[-1]["b"], hl=hl))
    since, last_hl = (0, True) if hl else (since + 1, False)
    i += n

END = P["END_s"]
for k, bk in enumerate(blocks):                 # a block stays until the next one starts (max 1.2 s after its last word)
    nx = blocks[k + 1]["a"] if k + 1 < len(blocks) else END
    if k == 0:
        bk["a"] = max(bk["a"], 0.017)            # frame 0 is the cover
    bk["b"] = min(nx, bk["b"] + 1.2, END)
    for sg in SEGS:
        if bk["a"] < sg["t0"] <= bk["a"] + 0.12:
            bk["a"] = sg["t0"]
    bk["layout"], bk["seg"] = lay(bk["a"] + 0.01)
    bk["b"] = min(bk["b"], next(s for s in SEGS if s["id"] == bk["seg"])["t1"])
merged = []
for bk in blocks:
    if merged and not bk["hl"] and not merged[-1]["hl"] and bk["b"] - bk["a"] < 0.15 and merged[-1]["seg"] == bk["seg"]:
        merged[-1]["text"] += " " + bk["text"]; merged[-1]["b"] = bk["b"]
    else:
        merged.append(bk)
blocks = [b for b in merged if b["seg"] not in set(C.get("skip_segments", []))]
json.dump(blocks, open("work/subs.json", "w"), indent=0, ensure_ascii=False)
print(len(blocks), "blocks,", sum(b["hl"] for b in blocks), "highlights")
print(" | ".join("*" + b["text"] + "*" if b["hl"] else b["text"] for b in blocks))
