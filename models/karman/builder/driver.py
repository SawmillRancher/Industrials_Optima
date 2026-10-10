import subprocess, glob, json, sys, openpyxl
import build, sheets
import os
RECALC = os.environ.get('RECALC_PY') or glob.glob('/root/.claude/skills/synced/*/xlsx/scripts/recalc.py')[0]  # LibreOffice-based recalculation script
def recalc(f):
    out = subprocess.run(['python3', RECALC, f, '300'], capture_output=True, text=True).stdout
    i = out.find('{'); return json.loads(out[i:])
snap = {}
for scen in ('Bull', 'Bear'):
    f = '/tmp/krmn_snap_%s.xlsx' % scen
    build.main(f, scen)
    print(scen, recalc(f).get('status'))
    ws = openpyxl.load_workbook(f, data_only=True)['Bull-Base-Bear']
    d = {}
    for r in range(9, 48):
        for c in range(3, 13):
            v = ws.cell(r, c).value
            if isinstance(v, (int, float)):
                d[(r, c)] = v
    snap[scen] = d
sheets.SNAP.update(snap)
out = sys.argv[1] if len(sys.argv) > 1 else 'KRMN_Model.xlsx'
build.main(out, 'Base')
print('final', json.dumps(recalc(out))[:3000])
