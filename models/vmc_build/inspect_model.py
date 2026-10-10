"""Inspect a recalculated VMC model: check rows and key lines."""
import sys, openpyxl
from fw import COLS, ANN, QC, HC
f = sys.argv[1] if len(sys.argv) > 1 else 'VMC_calc.xlsx'
wb = openpyxl.load_workbook(f, data_only=True)
ws = wb['Model']
labels = {ws.cell(r, 2).value: r for r in range(1, ws.max_row + 1) if ws.cell(r, 2).value}
rows_by_label = {}
for r in range(8, ws.max_row + 1):
    lab = ws.cell(r, 2).value
    if lab: rows_by_label[r] = lab.strip()
# 1) errors anywhere
errs = []
for wsx in wb:
    for row in wsx.iter_rows():
        for c in row:
            if isinstance(c.value, str) and c.value.startswith('#'):
                errs.append(f'{wsx.title}!{c.coordinate}={c.value}')
print('errors', len(errs), errs[:40])
# 2) checks
for r, lab in rows_by_label.items():
    if (lab.lower().startswith('check') and 'margin' not in lab.lower()) or 'tie-out' in lab.lower():
        bad = []
        for col in COLS:
            v = ws[f'{col.c}{r}'].value
            if isinstance(v, (int, float)) and abs(v) > (0.011 if 'EPS' in lab else 0.15):
                bad.append(f'{col.label}:{v}')
        if bad: print(f'CHECK r{r} {lab[:70]} -> {len(bad)} bad: {bad[:14]}')
# 3) key lines
show = sys.argv[2:] if len(sys.argv) > 2 else []
cols = [ANN[y] for y in (2006, 2010, 2015, 2019, 2023, 2024, 2025)] + [QC[(2025, 3)], QC[(2025, 4)], HC[2026], QC[(2026, 3)], QC[(2026, 4)]] + [ANN[y] for y in range(2026, 2031)]
def fmt(v):
    if isinstance(v, float): return f'{v:,.3f}' if abs(v) < 10 else f'{v:,.1f}'
    return str(v)
for r, lab in rows_by_label.items():
    if show and not any(s.lower() in lab.lower() for s in show): continue
    if not show: continue
    print(f'r{r} {lab[:60]:60s}', ' | '.join(f'{c.label}:{fmt(ws[f"{c.c}{r}"].value)}' for c in cols))
