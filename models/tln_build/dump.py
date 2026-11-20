"""Print selected Model rows (annual + 2026 quarter columns) from a recalculated workbook: python3 dump.py <file> [key ...]"""
import sys, openpyxl
import fw, build
from spec import build_spec, scen_layout
from spec2 import build_spec2
scen_layout(build.V0); build_spec(build.V0); build_spec2(build.V0); fw.number_rows(8)
ws = openpyxl.load_workbook(sys.argv[1], data_only=True)['Model']
keys = sys.argv[2:] or [r.key for r in fw.SPEC if r.arch not in ('blank', 'section', 'block', 'sub', 'text')]
cols = [c for c in fw.COLS if c.kind != 'Q' or c.year == 2026]
print(' ' * 34 + ''.join(f'{str(c.label):>9}' for c in cols))
for k in keys:
    r = fw.R[k]; out = []
    for c in cols:
        v = ws[f'{c.c}{r}'].value
        out.append(f'{v:9.1f}' if isinstance(v, (int, float)) and abs(v) >= 10 else (f'{v:9.3f}' if isinstance(v, (int, float)) else f'{str(v or ""):>9}'[:9]))
    print(f'{k:10}{(ws.cell(r, 2).value or "")[:23]:24}' + ''.join(out))
