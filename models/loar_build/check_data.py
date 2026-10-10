"""Consistency checks on the extracted data (statement arithmetic, quarter sums vs annual, end-market totals)."""
import json, glob, os
D = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob('data/*.json')}
def g(p, s, k): return (D.get(p, {}).get(s, {}) or {}).get(k)
def n(x): return x or 0.0
bad = []
def chk(name, a, b, tol=0.002):
    if a is None or b is None: return
    if abs(a - b) > tol: bad.append(f'{name}: {a:.3f} vs {b:.3f} ({a-b:+.3f})')
pers = sorted(D)
for p in pers:
    i = D[p].get('is', {}); ng = D[p].get('ng', {}); bs = D[p].get('bs', {}); em = D[p].get('em', {})
    if 'cogs' in i: chk(f'{p} gp', i['net_sales'] - i['cogs'], i['gp'])
    if 'sga' in i: chk(f'{p} op', i['gp'] - i['sga'] - i['trans'] + n(i.get('other_inc')), i['op_income'])
    if 'ebt' in i: chk(f'{p} ebt', i['op_income'] - i['interest'] - n(i.get('refi')), i['ebt'])
    if 'ebitda' in ng: chk(f'{p} ebitda', ng['op_income'] + ng['dep'] + ng['amort'] - n(ng.get('fx_gain')) * 0, ng['ebitda'], 0.01)
    if 'adj_ebitda' in ng:
        adj = sum(n(ng.get(k)) for k in ('inv_stepup', 'other_adj', 'trans', 'sbc', 'integ', 'covid', 'msa'))
        chk(f'{p} adj_ebitda', ng['ebitda'] + adj, ng['adj_ebitda'], 0.002)
    if 'ta' in bs and 'tle' in bs: chk(f'{p} bs', bs['ta'], bs['tle'])
    if em:
        tot = sum(n(em.get(k)) for k in em if k.endswith('_oem') or k.endswith('_am'))
        chk(f'{p} em vs total', tot, em.get('total'), 0.003)
        chk(f'{p} em vs sales', tot, i.get('net_sales'), 0.003)
for y in range(2022, 2026):
    yy = str(y)[2:]
    for s, ks in (('is', ['net_sales', 'gp', 'op_income', 'ni', 'interest']), ('ng', ['adj_ebitda', 'ebitda', 'dep', 'amort']),
                  ('em', ['com_oem', 'com_am', 'bj_oem', 'bj_am', 'def_oem', 'def_am', 'oth_oem', 'oth_am'])):
        for k in ks:
            qs = [g(f'Q{q}-{yy}', s, k) for q in (1, 2, 3, 4)]
            if all(v is not None for v in qs): chk(f'{y} {s}.{k} Σq', sum(qs), g(str(y), s, k), 0.003)
            else: bad.append(f'{y} {s}.{k} quarters missing {[q+1 for q,v in enumerate(qs) if v is None]}') if g(str(y), s, k) is not None else None
print('\n'.join(bad) or 'all checks pass')
for p in pers:
    i = D[p].get('is', {}); ng = D[p].get('ng', {})
    print(f"{p:6} sales {n(i.get('net_sales')):8.1f} op {n(i.get('op_income')):7.1f} ni {n(i.get('ni')):7.1f} adjEBITDA {n(ng.get('adj_ebitda')):7.1f}",
          'sections', sorted(k for k in D[p] if k not in ('period', 'sources')))
