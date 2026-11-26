#!/bin/bash
# uso: render3d.sh still|anim [tomas...]
B="/c/Program Files/Blender Foundation/Blender 5.3/blender.exe"
cd "$(dirname "$0")"; MODE=$1; shift
SHOTS=${@:-"hook_iran hormuz levant67 iran_jets fordow natanz redsea_ship"}
for s in $SHOTS; do
  mkdir -p "render3d/$s"; D="$(cygpath -w "$PWD/render3d/$s")"
  if [ "$MODE" = still ]; then
    F=$(python -c "import json;n=json.load(open('shots.json'))['$s']['frames'];print(f'{n//3},{2*n//3}')")
    "$B" -b -P blender_kit.py -- --shot $s --out "$D" --still $F > "render3d/_$s.log" 2>&1
  else
    rm -f render3d/$s/f_*.png; "$B" -b -P blender_kit.py -- --shot $s --out "$D" > "render3d/_$s.log" 2>&1
  fi
  echo "$s $(date +%T) $(grep -c FIN render3d/_$s.log)"
done
