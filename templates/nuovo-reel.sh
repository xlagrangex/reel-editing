#!/bin/zsh
# New reel project from the template.
# usage: zsh nuovo-reel.sh <project folder> <footage file>
# Copies templates/progetto, writes the footage path into reel.json and prints the local install commands
# (everything stays inside the project: .venv and node_modules, nothing system-wide).
set -e
SKILL="$(cd "$(dirname "$0")" && pwd)"
DST=$1; SRC=$2
[[ -n $DST && -n $SRC ]] || { echo "usage: zsh nuovo-reel.sh <project folder> <footage file>"; exit 1; }
[[ -e $DST ]] && { echo "$DST exists already"; exit 1; }
cp -R "$SKILL/progetto" "$DST"
mkdir -p "$DST"/{work,edit/stems,sfx,music}
python3 - "$DST/reel.json" "$(cd "$(dirname "$SRC")" && pwd)/$(basename "$SRC")" <<'PY'
import json, sys
p, src = sys.argv[1:]
c = json.load(open(p)); c["source"] = src
json.dump(c, open(p, "w"), indent=2, ensure_ascii=False)
PY
echo "project: $DST"
echo "install (local only):"
echo "  cd \"$DST\" && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
echo "  (cd gfx && npm install)    # MathJax for LaTeX equations"
echo "  npm install                # puppeteer-core, only for page captures"
echo "music: generate your own track into music/ and set reel.json \"music\" (see references/musica.md)"
