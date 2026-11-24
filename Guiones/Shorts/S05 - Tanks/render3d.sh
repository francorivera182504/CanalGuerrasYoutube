#!/bin/bash
set -e
cd "$(dirname "$0")"
B="/c/Program Files/Blender Foundation/Blender 5.3/blender.exe"
for shot in hook cross stall crew; do
  "$B" -b -t 8 -P blender_tank.py -- --shot "$shot" --samples 32 --out "$(pwd -W)/render3d/$shot" > "render3d/_${shot}.log" 2>&1
done
