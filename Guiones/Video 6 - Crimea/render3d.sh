#!/bin/bash
# Renderiza las 4 tomas del puente una tras otra
B="/c/Program Files/Blender Foundation/Blender 5.3/blender.exe"
cd "$(dirname "$0")"
for spec in "hook 130 28" "nov26 128 69" "oct22 190 69" "fly 676 1"; do
  set -- $spec
  date +%T; echo "== $1"
  rm -rf "render3d/$1"; "$B" -b -P blender_puente.py -- --shot $1 --frames $2 --fall $3 > "render3d/_$1.log" 2>&1
done
date +%T; echo FIN
