import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import openpyxl
from recalc import recalc
from finish import live_panel, write_snapshots, inject_values
import make_leco

OUT = sys.argv[1]
work = os.path.join(os.path.dirname(OUT), 'work'); os.makedirs(work, exist_ok=True)
snap = {}
for sc in ('Bull', 'Bear'):
    p = os.path.join(work, f'LECO_{sc}.xlsx')
    make_leco.make(p, sc)
    snap[sc] = live_panel(recalc(p, os.path.join(work, 'rc')))
base = os.path.join(work, 'LECO_Base.xlsx')
M = make_leco.make(base, 'Base')
tmpl = openpyxl.load_workbook(make_leco.LM.TEMPLATE)['Bull-Base-Bear']
wb = openpyxl.load_workbook(base)
write_snapshots(wb, tmpl, snap['Bull'], snap['Bear'])
wb.calculation.fullCalcOnLoad = True
wb.save(base)
rc = recalc(base, os.path.join(work, 'rc'))
inject_values(base, rc, OUT)
json.dump(M.rows, open(OUT + '.rows.json', 'w'))
print('done', OUT, rc)
