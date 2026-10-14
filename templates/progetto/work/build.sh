#!/bin/zsh
# Rebuild everything downstream of the plan, after editing gfx/gen.py or reel.json segments.
# After changing reel.json spans run cut.py, voice.py, build_cam.py, faces.sh and plan.py first (compose.py stops otherwise):
# compositions -> renders -> compositor -> subtitles -> audio -> final -> QA.
# usage: zsh work/build.sh [segment ids to re-render; none = all]
set -e
cd "$(dirname "$0")/.."
PY=.venv/bin/python; [[ -x $PY ]] || PY=python3
$PY gfx/gen.py
zsh work/render.sh "$@"
$PY work/compose.py
$PY work/subs.py
$PY work/audio.py
$PY work/burn.py
zsh work/qa.sh
