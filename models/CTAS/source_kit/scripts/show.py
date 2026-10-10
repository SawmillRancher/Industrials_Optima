import openpyxl,json,sys
wb=openpyxl.load_workbook(sys.argv[1],data_only=True); ws=wb['Model']
import os; R=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','rowmap.json')))
import mdl_core as M
cols=[p for p in M.PERIODS if (not p.is_q) or p.fy==2027]
keys=sys.argv[2].split(',')
print('%-14s'%'', ' '.join('%9s'%M.header(p)[-7:] for p in cols))
for k in keys:
    r=R[k]; vals=[]
    for p in cols:
        v=ws.cell(r,p.col).value
        if isinstance(v,(int,float)):
            vals.append('%9.3f'%v if abs(v)<5 else '%9.1f'%v)
        else: vals.append('%9s'%(str(v)[:9] if v is not None else ''))
    print('%-14s'%k[:14],' '.join(vals))
