#!/bin/zsh
# A real sound, cut from a video: sfx/<name>.wav (48 kHz mono, 3 ms fade-in, 40 ms fade-out).
# usage: zsh work/grab_sfx.sh <url> <start s> <duration s> <name>
# Find the first clean occurrence by ear or by RMS; check it against a second, independent upload of the same sound.
# Sites behind a Cloudflare CAPTCHA are not an option: look for another source. Check you may use the sound.
cd "$(dirname "$0")/.."
URL=$1; SS=$2; DUR=$3; NAME=$4
mkdir -p sfx work/dl
yt-dlp -q -x --audio-format wav -o "work/dl/$NAME.%(ext)s" "$URL"
ffmpeg -nostdin -v error -y -ss "$SS" -t "$DUR" -i "work/dl/$NAME.wav" -ac 1 -ar 48000 \
  -af "afade=t=in:d=0.003,afade=t=out:st=$(python3 -c "print(max(0,$DUR-0.04))"):d=0.04" "sfx/$NAME.wav"
echo "sfx/$NAME.wav"
