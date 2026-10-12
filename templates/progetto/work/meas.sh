#!/bin/sh
for f in "$@"; do printf "%s: " "$f"; ffmpeg -nostats -i "$f" -af ebur128=peak=true -f null - 2>&1 | awk '/Summary/{s=1} s&&/I:/{printf "I=%s LUFS ",$2} s&&/Peak:/{printf "TP=%s dBTP\n",$2}'; done
