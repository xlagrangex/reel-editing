#!/bin/zsh
# Step 7. Face track without installing anything: one frame in four at 540x960 -> macOS Vision (system swift)
# -> work/ft/faces.txt ("00001.jpg cx cy w h", normalised, top-left origin). ~7000 frames take ~20 s.
cd "$(dirname "$0")/.."
rm -rf work/ft && mkdir -p work/ft
ffmpeg -nostdin -v error -i work/cam.mp4 -vf "select='not(mod(n\,4))',scale=540:960" -fps_mode passthrough -q:v 3 work/ft/%05d.jpg
swift work/faces.swift work/ft
echo "faces: $(grep -vc nan work/ft/faces.txt) found / $(grep -c . work/ft/faces.txt) sampled"
