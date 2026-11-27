#!/bin/bash
# Render completo de las tomas 3D (1080x1920). Uso: bash render3d.sh [shots...]
cd "$(dirname "$0")"; B="C:/Program Files/Blender Foundation/Blender 5.3/blender.exe"; P="$(cygpath -w "$PWD")"; mkdir -p render3d
for s in ${@:-hook}; do
  "$B" -b -t 10 -P blender_doss.py -- --shot $s --out "$P/render3d/$s" --samples 24 > render3d/_$s.log 2>&1; echo "$s $(tail -1 render3d/_$s.log)"
done
echo ALL3D DONE
