#!/bin/zsh
# A meme GIF (as mp4) -> sprite sheet for W.gif(): gfx/assets/ext/<name>.jpg
# usage: zsh work/gif2sprite.sh input.mp4 name [fps=12] [frame width=540] [cols=6]
# prints the W.gif arguments: cols, frames, fps, frame width, frame height
cd "$(dirname "$0")/.."
IN=$1; NAME=$2; FPS=${3:-12}; FW=${4:-540}; COLS=${5:-6}
mkdir -p gfx/assets/ext
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
N=$(python3 -c "import math;print(int(math.floor($D*$FPS)))")
ROWS=$(( (N + COLS - 1) / COLS ))
ffmpeg -nostdin -v error -y -i "$IN" -vf "fps=$FPS,scale=$FW:-2,tile=${COLS}x${ROWS}" -frames:v 1 -q:v 3 "gfx/assets/ext/$NAME.jpg"
FH=$(python3 -c "from PIL import Image;im=Image.open('gfx/assets/ext/$NAME.jpg');print(im.height//$ROWS)")
echo "W.gif('#sel .g', $COLS, $N, $FPS, $FW, $FH, at, dur, 0)   // background-image: url(../assets/ext/$NAME.jpg)"
