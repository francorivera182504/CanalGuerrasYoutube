#!/bin/bash
set -e
cd "$(dirname "$0")"
B="/c/Program Files/Blender Foundation/Blender 5.3/blender.exe"
for shot in night hook ram blast; do
  "$B" -b -t 8 -P blender_nazaire.py -- --shot "$shot" --samples 32 > "render3d/_${shot}.log" 2>&1
done
