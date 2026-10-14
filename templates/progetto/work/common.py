"""Shared paths and helpers. Every script runs from the project root, wherever it is launched from."""
import json, os, shutil, subprocess, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
CFG = json.load(open("reel.json"))
FPS = 60
MODEL = os.environ.get("WHISPER_MODEL", "mlx-community/whisper-large-v3-turbo")


def whisper_bin():
    local = os.path.join(ROOT, ".venv", "bin", "mlx_whisper")
    return local if os.path.exists(local) else (shutil.which("mlx_whisper") or "mlx_whisper")


def whisper(wav, out_json=None, prompt=None, offset=0.0):
    """mlx_whisper with word timestamps -> list of {w, s, e} (seconds + offset); the raw result goes to out_json."""
    with tempfile.TemporaryDirectory() as d:
        cmd = [whisper_bin(), wav, "--model", MODEL, "--language", CFG.get("language", "it"), "--word-timestamps", "True",
               "--condition-on-previous-text", "False", "--output-format", "json", "--output-dir", d]
        if prompt:
            cmd += ["--initial-prompt", prompt]
        subprocess.run(cmd, check=True, capture_output=True)
        res = json.load(open(os.path.join(d, os.path.splitext(os.path.basename(wav))[0] + ".json")))
    if out_json:
        json.dump(res, open(out_json, "w"), ensure_ascii=False)
    return [dict(w=w["word"].strip(), s=round(offset + w["start"], 3), e=round(offset + w["end"], 3))
            for seg in res["segments"] for w in seg.get("words", [])]


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *args], check=True)


def stop_windows():
    """reel.json "stops": [{"from": "e ti darei", "until": "S03"}] -> [(t0, t1)] in timeline seconds.
    A stop is a dramatic beat: from the first word of the phrase to the start of that segment the music pauses and the picture
    turns black and white. Anchored on words, not seconds, so it follows any later change to the cuts."""
    stops = CFG.get("stops", [])
    if not stops:
        return []
    norm = lambda s: "".join(c for c in s.lower() if c.isalnum() or c in " '")
    words = [norm(w["w"]) for w in json.load(open("work/tl_words.json"))]
    times = [w["t0"] for w in json.load(open("work/tl_words.json"))]
    seg = {s["id"]: s["t0"] for s in json.load(open("work/plan.json"))["segments"]}
    out = []
    for s in stops:
        ph = norm(s["from"]).split()
        hits = [i for i in range(len(words) - len(ph) + 1) if words[i:i + len(ph)] == ph]
        if len(hits) != 1:
            raise SystemExit(f'stop "{s["from"]}": found {len(hits)} times in the cut, it must be once')
        out.append((times[hits[0]], seg[s["until"]]))
    return out
