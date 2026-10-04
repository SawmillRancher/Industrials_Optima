import json, datetime as dt
import os
D=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sources', 'companyfacts_CIK0002040127.json')))['facts']['us-gaap']
def _facts(tag, unit=None):
    if tag not in D: return {}
    u=D[tag]['units']; unit=unit or list(u.keys())[0]
    out={}
    for x in sorted(u[unit], key=lambda x:x['filed']):
        out[(x.get('start'),x['end'])]=x['val']   # latest filed wins
    return out
# period definitions
Q={'Q1/24':('2024-01-01','2024-03-31'),'Q2/24':('2024-04-01','2024-06-30'),'Q3/24':('2024-07-01','2024-09-30'),'Q4/24':('2024-10-01','2024-12-31'),
   'Q1/25':('2025-01-01','2025-03-31'),'Q2/25':('2025-04-01','2025-06-30'),'Q3/25':('2025-07-01','2025-09-30'),'Q4/25':('2025-10-01','2025-12-31'),
   'Q1/26':('2026-01-01','2026-03-31'),'Q2/26':('2026-04-01','2026-06-30')}
FY={'2022':('2022-01-01','2022-12-31'),'2023':('2023-01-01','2023-12-31'),'2024':('2024-01-01','2024-12-31'),'2025':('2025-01-01','2025-12-31')}
H={'1H/24':('2024-01-01','2024-06-30'),'1H/25':('2025-01-01','2025-06-30'),'1H/26':('2026-01-01','2026-06-30')}
def flow(tag, p, unit=None):
    f=_facts(tag,unit)
    if p in FY: return f.get(FY[p])
    if p in H: 
        v=f.get(H[p])
        if v is None:
            a=flow(tag,'Q1/'+p[-2:]); b=flow(tag,'Q2/'+p[-2:])
            v=None if a is None or b is None else a+b
        return v
    s,e=Q[p]
    if (s,e) in f: return f[(s,e)]
    y=s[:4]; ys=y+'-01-01'
    if (ys,e) in f:
        cur=f[(ys,e)]
        if s==ys: return cur
        prev_end=(dt.date.fromisoformat(s)-dt.timedelta(days=1)).isoformat()
        if (ys,prev_end) in f: return cur-f[(ys,prev_end)]
    return None
def inst(tag, p, unit=None):
    f=_facts(tag,unit)
    end = FY[p][1] if p in FY else (H[p][1] if p in H else Q[p][1])
    return f.get((None,end))
