"""Step 9. One standalone HyperFrames composition per segment -> gfx/compositions/<id>.html.

Fill SCENES at the bottom for this reel. Every split/gfx segment without a scene gets the kinetic-type placeholder
(the spoken words landing one by one, with a small "segnaposto" tag), so the whole pipeline runs from day one:
replace every placeholder before delivery. Cam segments without a scene get no overlay.
Times are seconds from the segment start, taken from the words: t("S02", "milioni")."""
import html as H
import json, os, random, re, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PLAN = json.load(open(os.path.join(ROOT, "work", "plan.json")))
SEG = {s["id"]: s for s in PLAN["segments"]}
WORDS = json.load(open(os.path.join(ROOT, "work", "tl_words.json")))
_marks = os.path.join(HERE, "assets", "cap", "marks.json")
MARKS = {k: v["marks"] for k, v in json.load(open(_marks)).items()} if os.path.exists(_marks) else {}

HEAD = """<!doctype html>
<html lang="it">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<link rel="stylesheet" href="../assets/world.css" />
<script src="../assets/world.js"></script>
<style>{css}</style>
</head>
<body class="{cls}">
<div id="root" data-composition-id="{id}" data-start="0" data-duration="{dur}" data-width="1080" data-height="1920">
  <div class="bg clip" data-start="0" data-duration="{dur}"></div>
  <div class="world-mask clip" data-start="0" data-duration="{dur}" style="position:absolute;inset:0">
  <div id="world">
{body}
  </div>
  </div>
</div>
<script type="application/json" id="sfx">{sfx}</script>
<script>
  const tl = W.init("{id}");
  W.set({{ x: 0, y: 0, scale: 1 }});
{js}
</script>
</body>
</html>
"""

OVCSS = "\n  html, body { background: transparent !important; }\n"
norm = lambda s: re.sub(r"[^\w]", "", s.lower())


def words(sid):
    s = SEG[sid]
    return [dict(w, t=round(w["t0"] - s["t0"], 3)) for w in WORDS if s["t0"] <= w["t0"] < s["t1"]]


def t(sid, word, n=1):
    """segment time of the n-th spoken word starting with `word` (case and punctuation ignored)"""
    k = 0
    for w in words(sid):
        if norm(w["w"]).startswith(norm(word)):
            k += 1
            if k == n:
                return w["t"]
    raise KeyError(f"{word!r} (#{n}) not spoken in {sid}: {SEG[sid]['text']}")


def capture_block(name, cid="cap"):
    """a real page from work/shoot.mjs; drive it with W.capture('#cap', {...}).set / .move / .mark(MARKS[name][needle], at)"""
    return f"""    <div class="cap" id="{cid}">
      <div class="cap-bed"><div class="cap-page-bed"><img src="../assets/cap/{name}.png" /></div></div>
      <div class="cap-frame"><div class="cap-page"><img src="../assets/cap/{name}.png" /></div></div>
    </div>"""


def tex(d):
    """{name: LaTeX} -> {name: (svg, viewbox w, viewbox h)}. Equations always in full, never abbreviated."""
    out = json.loads(subprocess.run(["node", os.path.join(HERE, "tex2svg.cjs"), json.dumps(list(d.values()))],
                                    capture_output=True, check=True, text=True).stdout)
    res = {}
    for k, s in zip(d, out):
        vb = [float(x) for x in re.search(r'viewBox="([^"]+)"', s).group(1).split()]
        s = re.sub(r'^<svg[^>]*?(viewBox="[^"]+")', r'<svg xmlns="http://www.w3.org/2000/svg" \1', s, count=1)
        res[k] = (s, vb[2], vb[3])
    return res


def svg(t3, w=None, h=None):
    s, vw, vh = t3
    w = h * vw / vh if w is None else w
    h = w * vh / vw if h is None else h
    return s.replace("<svg ", f'<svg width="{w:.2f}" height="{h:.2f}" ', 1)


# ================================================================ default: kinetic type (placeholder)
def kinetic(sid):
    s = SEG[sid]; ws = words(sid)
    split = s["layout"] == "split"
    chars = sum(len(w["w"]) + 1 for w in ws)
    size = 104 if chars < 40 else 88 if chars < 70 else 72 if chars < 110 else 60
    key = max(range(len(ws)), key=lambda i: len(norm(ws[i]["w"]))) if ws else -1
    spans = "".join(f'<span id="w{i}" class="kw{" accent" if i == key else ""}">{H.escape(w["w"])}</span>' for i, w in enumerate(ws))
    top, hgt = (60, 820) if split else (200, 1080)
    css = f"""
  #kin {{ position: absolute; left: 80px; right: 80px; top: {top}px; height: {hgt}px; display: flex; flex-wrap: wrap; align-content: center; justify-content: center;
    gap: 0 0.3em; font-weight: 800; font-size: {size}px; line-height: 1.1; letter-spacing: -0.025em; text-align: center; }}
  .kw {{ display: inline-block; filter: blur(0px); }}
  #tag {{ position: absolute; left: 48px; top: {top - 30}px; font-weight: 700; font-size: 24px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-2); }}
"""
    js = "\n".join(f"  tl.fromTo('#w{i}', {{ opacity: 0, y: 34, filter: 'blur(12px)' }}, {{ opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.3, ease: 'power3.out' }}, {max(0, w['t'] - 0.06):.3f});"
                   for i, w in enumerate(ws))
    js = f"  gsap.set('.kw', {{ opacity: 0 }});\n{js}\n  W.glide(W.frame(540, {top + hgt / 2:.0f}, 1.04, 540, {top + hgt / 2:.0f}), 0, {s['dur']});"
    return dict(cls="split" if split else "", sfx=[], css=css,
                body=f'    <div id="tag">segnaposto · {sid}</div>\n    <div id="kin">{spans}</div>', js=js)


# ================================================================ example: questions that stack up (split)
def domande(sid, items, push=True):
    """items = [(html, t_land)]; mark the key word with <u>word</u>: it gets the gradient and an underline drawn
    0.4 s after its card lands. Earlier cards are demoted when the next one lands; the last one is the hero."""
    cards, js = [], ["  gsap.set('.dq', { opacity: 0 });"]
    for i, (txt, at) in enumerate(items):
        txt = re.sub(r"<u>(.*?)</u>", r'<span class="ulw"><span class="accent">\1</span><span class="ul"></span></span>', txt)
        hero = " hero" if i == len(items) - 1 else ""
        cards.append(f'      <div id="d{i}" class="card dq{hero}"><div class="n">{i + 1}</div><div class="t">{txt}</div></div>')
        js.append(f"  W.land('#d{i}', {at:.3f});")
        if i:
            js.append(f"  W.demote('#d{i - 1}', {at + 0.05:.3f});")
        js.append(f"  tl.fromTo('#d{i} .ul', {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.45, ease: 'power3.out' }}, {at + 0.4:.3f});")
    if push:
        js.append(f"  W.push(W.frame(540, 640, 1.06, 540, 600), {items[-1][1] + 0.2:.3f}, 1.5);")
    css = """
  #stack { position: absolute; left: 70px; right: 70px; top: 40px; height: 860px; display: flex; flex-direction: column; justify-content: center; gap: 26px; }
  #stack .card { position: relative; display: flex; align-items: center; gap: 30px; padding: 40px 52px; }
  .dq .n { flex: none; width: 66px; height: 66px; border-radius: 50%; background: var(--band); color: var(--accent); font-weight: 800; font-size: 34px;
    display: flex; align-items: center; justify-content: center; }
  .dq .t { font-weight: 800; font-size: 56px; line-height: 1.12; letter-spacing: -0.02em; }
  .ulw { position: relative; display: inline-block; }
  .ulw .ul { position: absolute; left: 0; right: 0; bottom: -6px; height: 9px; border-radius: 5px; background: var(--grad); transform: scaleX(0); transform-origin: 0 50%; }
"""
    return dict(cls="split", sfx=[{"t": at, "type": "pop"} for _, at in items], css=css,
                body='    <div id="stack">\n' + "\n".join(cards) + "\n    </div>", js="\n".join(js))


# ================================================================ example: the number hits the jackpot (gfx or split)
def numero(sid, value, at, stop_at, label="", layout=None, seed=7):
    """A strong number said out loud: it lands at `at` already spinning, the digits stop one at a time and the last
    one stops at `stop_at` (the word that says the number), then it turns to the gradient with rays behind and a push.
    No slot machine, no "jackpot" word. The money sound is the Shopify sale "cha-ching" in sfx/soldi.wav (shipped)."""
    lay = layout or SEG[sid]["layout"]
    cy = 470 if lay == "split" else 760
    size = min(176, int(900 / (0.64 * len(value))))
    hgt = int(size * 1.08)
    rnd = random.Random(seed)
    nd = sum(ch.isdigit() for ch in value)
    cols, stops, k = [], [], 0
    for ch in value:
        if not ch.isdigit():
            cols.append(f'<span class="sep">{H.escape(ch)}</span>'); continue
        n = 30 + 4 * k
        strip = "".join(f"<i>{rnd.randint(0, 9)}</i>" for _ in range(n)) + f"<i>{ch}</i>"
        cols.append(f'<span class="dg"><span class="sp" id="sp{k}">{strip}</span></span>')
        stops.append(round(max(at + 0.5 + 0.05 * k, stop_at - 0.18 * (nd - 1 - k)), 3)); k += 1
    last = stops[-1]
    css = f"""
  #num {{ position: absolute; left: 0; right: 0; top: {cy - hgt / 2:.0f}px; height: {hgt}px; display: flex; justify-content: center;
    font-weight: 800; font-size: {size}px; letter-spacing: -0.02em; color: var(--text); }}
  #num .dg {{ display: inline-block; height: {hgt}px; overflow: hidden; }}
  #num .sp {{ display: block; }}
  #num i {{ display: block; height: {hgt}px; line-height: {hgt}px; font-style: normal; text-align: center; }}
  #num .sep {{ line-height: {hgt}px; }}
  #num.gold i, #num.gold .sep {{ background: var(--grad); -webkit-background-clip: text; background-clip: text; color: transparent; }}
  #rays {{ position: absolute; left: -260px; top: {cy - 800:.0f}px; width: 1600px; height: 1600px; border-radius: 50%; opacity: 0;
    background: repeating-conic-gradient(rgba(42, 169, 245, 0.16) 0deg 9deg, rgba(42, 169, 245, 0) 9deg 22deg);
    -webkit-mask-image: radial-gradient(circle, #000 18%, transparent 62%); mask-image: radial-gradient(circle, #000 18%, transparent 62%); }}
  #lab {{ position: absolute; left: 0; right: 0; top: {cy + hgt / 2 + 30:.0f}px; text-align: center; font-weight: 700; font-size: 44px; color: var(--text-2); letter-spacing: -0.01em; }}
"""
    body = f"""    <div id="rays"></div>
    <div id="numw" style="position:absolute;inset:0"><div id="num">{''.join(cols)}</div></div>
    <div id="lab">{H.escape(label)}</div>"""
    js = f"""
  const STOPS = {json.dumps(stops)}, H = {hgt}, AT = {at};
  gsap.set(['#num', '#lab'], {{ opacity: 0 }});
  W.land('#num', AT, {{ dy: 30 }});
  for (let i = 0; i < STOPS.length; i++) {{
    const sp = document.getElementById('sp' + i), m = sp.children.length - 1, o = {{ p: 0.5 / m }}, T = STOPS[i];
    const upd = function () {{ gsap.set(sp, {{ y: -o.p * m * H }}); }};
    gsap.set(sp, {{ filter: 'blur(5px)' }});
    upd();
    tl.fromTo(o, {{ p: 0.5 / m }}, {{ p: (m - 2) / m, duration: T - 0.45 - AT, ease: 'none', immediateRender: true, onUpdate: upd }}, AT);
    tl.to(o, {{ p: 1, duration: 0.45, ease: 'power2.out', onUpdate: upd }}, T - 0.45);
    tl.to(sp, {{ filter: 'blur(0px)', duration: 0.2 }}, T - 0.22);
    tl.fromTo(sp, {{ scale: 1 }}, {{ scale: 1.12, duration: 0.07, yoyo: true, repeat: 1 }}, T);
  }}
  tl.set('#num', {{ attr: {{ class: 'gold' }} }}, {last + 0.1});
  tl.fromTo('#rays', {{ opacity: 0, rotation: 0 }}, {{ opacity: 1, rotation: 25, duration: 2.4, ease: 'power1.out' }}, {last + 0.1});
  tl.fromTo('#num', {{ scale: 1 }}, {{ scale: 1.08, duration: 0.12, yoyo: true, repeat: 1, ease: 'power2.out' }}, {last + 0.1});
  W.land('#lab', {last + 0.35}, {{ dy: 20 }});
  W.push(W.frame(540, {cy}, 1.08, 540, {cy}), {last + 0.1}, 1.6);"""
    sfx = [{"t": at, "type": "spin", "dur": round(last - at, 2)}] + [{"t": s, "type": "reelstop"} for s in stops] + [{"t": round(last + 0.12, 3), "type": "soldi"}]
    return dict(cls="split" if lay == "split" else "", sfx=sfx, css=css, body=body, js=js)


# ================================================================ example: light chips over the full face (cam)
def chip(sid, items):
    """items = [(text, at, x, y)]: small pills that pop over the full face. Keep them in the top area, off the face,
    never half the screen. Rendered with alpha (ProRes 4444) and laid over the footage by compose.py."""
    body, js = [], []
    for i, (txt, at, x, y) in enumerate(items):
        body.append(f'    <div id="c{i}" class="chip" style="left:{x}px;top:{y}px">{txt}</div>')
        js.append(f"  tl.fromTo('#c{i}', {{ opacity: 0, scale: 0.4, rotation: 5 }}, {{ opacity: 1, scale: 1, rotation: 2, duration: 0.35, ease: 'back.out(2.2)' }}, {at:.3f});")
    js.insert(0, "  gsap.set('.chip', { opacity: 0 });")
    js.append(f"  tl.to('.chip', {{ opacity: 0, scale: 0.9, duration: 0.2 }}, {SEG[sid]['dur'] - 0.25:.3f});")
    return dict(cls="ov", sfx=[{"t": at, "type": "pop"} for _, at, _, _ in items], css=OVCSS, body="\n".join(body), js="\n".join(js))


# ================================================================ this reel's scenes
SCENES = {}
# SCENES["S01"] = domande("S01", [("ci sta <u>superando</u>?", t("S01", "superando") - 0.3), ("o ci mostra i nostri <u>limiti</u>?", t("S01", "limiti") - 0.4)])
# SCENES["S04"] = numero("S04", "30.000.000", t("S04", "stima"), t("S04", "milioni") + 0.1, label="stima")
# SCENES["S05"] = chip("S05", [("🥜 Noccioline", t("S05", "noccioline"), 560, 160)])


def build():
    out = os.path.join(HERE, "compositions")
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        if f.endswith(".html"):
            os.remove(os.path.join(out, f))
    for s in PLAN["segments"]:
        sc = SCENES.get(s["id"])
        if sc is None:
            if s["layout"] == "cam":
                continue
            sc = kinetic(s["id"])
            print("placeholder", s["id"])
        doc = HEAD.format(id=s["id"], dur=s["dur"], cls=sc["cls"], css=sc["css"], body=sc["body"], js=sc["js"], sfx=json.dumps(sc["sfx"]))
        if sc["cls"] == "ov":
            doc = doc.replace(f'<div class="bg clip" data-start="0" data-duration="{s["dur"]}"></div>', "")
        open(os.path.join(out, f"{s['id']}.html"), "w").write(doc)
        print("wrote", s["id"], s["layout"], s["dur"])


if __name__ == "__main__":
    build()
