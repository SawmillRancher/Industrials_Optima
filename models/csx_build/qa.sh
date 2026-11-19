#!/bin/bash
# Rebuild, recalculate a scratch copy and run the QA tools. Usage: bash qa.sh [--snap --recalc]
# CSX_SRC points at the raw EDGAR downloads (only needed to re-extract; the build runs from the committed data/).
set -e
K=$(cd "$(dirname "$0")" && pwd)
export CSX_SRC=${CSX_SRC:-/tmp/csx_src}
SCR=${TMPDIR:-/tmp}
RECALC=${XLSX_RECALC:-/mnt/skills/public/xlsx/scripts/recalc.py}
cd "$K" && python3 build.py "$@"
cp ../CSX_Model.xlsx "$SCR/csx_rc.xlsx"
(cd "$(dirname "$RECALC")" && python3 "$RECALC" "$SCR/csx_rc.xlsx" 600 | head -5)
cd "$K/.." && python3 tools/inspect_model.py "$SCR/csx_rc.xlsx" | head -40
python3 tools/cyc.py CSX_Model.xlsx | tail -1
python3 tools/residue_scan.py CSX_Model.xlsx --extra Woodward WWD 382.17 | tail -2
