#!/bin/zsh
# Step 10. Render compositions -> work/r/. No ids = every composition in gfx/compositions.
#   graphics: 240 fps, then tmix=frames=3 to 60 fps (real motion blur), plus a contact sheet <id>_sheet.jpg
#   overlays (<body class="ov">): 60 fps ProRes 4444 with alpha, <id>_ov.mov
# Env: WORKERS (default 4). Node "heap out of memory" or "Navigation timeout of 60000 ms" = too much at once:
# re-run that id alone. Never run more than 2-3 renders in parallel.
cd "$(dirname "$0")/.."
R=$PWD; W=${WORKERS:-4}; HF="hyperframes@0.8.143"
mkdir -p work/r
ids=("$@"); [[ ${#ids} -eq 0 ]] && ids=(${(f)"$(ls gfx/compositions/*.html | xargs -n1 basename | sed 's/\.html$//')"})
for id in $ids; do
  cd "$R/gfx"; rm -f "$R/work/r/$id.mp4" "$R/work/r/${id}_ov.mov" "$R/work/r/${id}_sheet.jpg"   # never write through a symlink
  if grep -q '<body class="ov">' compositions/$id.html; then
    npx --yes $HF render -c compositions/$id.html --fps 60 --format mov -w 1 -o "$R/work/r/${id}_ov.mov" --quiet > "$R/work/r/$id.log" 2>&1 < /dev/null || { echo "$id OV FAIL (see work/r/$id.log)"; continue; }
    echo "$id overlay"
  else
    NODE_OPTIONS=--max-old-space-size=12288 npx --yes $HF render -c compositions/$id.html --fps 240 --crf 14 -w $W -o "$R/work/r/${id}_240.mp4" --quiet > "$R/work/r/$id.log" 2>&1 < /dev/null || { echo "$id RENDER FAIL (see work/r/$id.log)"; continue; }
    ffmpeg -nostdin -v error -y -i "$R/work/r/${id}_240.mp4" -vf "tmix=frames=3,fps=60,format=yuv420p" -c:v libx264 -crf 12 -preset medium -r 60 "$R/work/r/$id.mp4"
    rm -f "$R/work/r/${id}_240.mp4"
    ffmpeg -nostdin -v error -y -i "$R/work/r/$id.mp4" -vf "select='not(mod(n\,15))',scale=216:384,tile=8x4" -frames:v 1 "$R/work/r/${id}_sheet.jpg"
    echo "$id $(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$R/work/r/$id.mp4") frames"
  fi
done
