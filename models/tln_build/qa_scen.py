"""QA helper: rebuild copies of the workbook with the switch on Bull and Bear, recalculate, run inspect_model and print the
ordering of revenue / Adjusted EBITDA / EPS / price target / DCF value. Usage: python3 qa_scen.py <workdir>"""
import openpyxl, subprocess, json, sys, os
import fw
S = sys.argv[1]; RC = os.environ.get('XLSX_RECALC', '/mnt/skills/public/xlsx/scripts/recalc.py')
OUT = os.path.join(os.path.dirname(fw.BASE), 'TLN_Model.xlsx'); files = []
for sc in ('Bull', 'Bear'):
    wb = openpyxl.load_workbook(OUT); wb['Model'][f'{fw.NOTE}2'] = sc; p = f'{S}/tln_{sc}.xlsx'; wb.save(p)
    out = subprocess.run(['python3', RC, p, '300'], capture_output=True, text=True, cwd=os.path.dirname(RC))
    print(sc, json.loads(out.stdout).get('status'), subprocess.run(['python3', os.path.join(fw.BASE, 'inspect_model.py'), p], capture_output=True, text=True).stdout.strip().split('\n')[-1])
for f in (f'{S}/tln_Bull.xlsx', OUT, f'{S}/tln_Bear.xlsx'):
    wb = openpyxl.load_workbook(f, data_only=True); b = wb['Bull-Base-Bear']; d = wb['DCF']
    print(os.path.basename(f)[:14], 'rev', [round(b[c + '9'].value) for c in 'CDH'], 'EBITDA', [round(b[c + '12'].value) for c in 'CDEFGH'], 'EPS', [round(b[c + '23'].value, 1) for c in 'CDH'],
          'PT', [round(b[c + '27'].value) for c in 'GH'], 'DCF', round(d['C51'].value), 'lev', [round(b[c + '39'].value, 2) for c in 'CDH'])
