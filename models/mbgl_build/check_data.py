"""Consistency checks on the extracted data (data/*.json). Whole-$m source data, so sums are checked to ±1 (company rounding).

- Income statement: revenue − expenses = operating profit; OP − other − interest = EBT; EBT − tax = NI.
- Segments: Σ segment revenue = revenue; Σ segment OP (incl. corporate) = OP; segment OP + D&A + SBC + items = segment Adjusted EBITDA;
  Σ segment Adjusted EBITDA = consolidated; subscription + non-subscription = revenue; U.S. + international = revenue.
- Adjusted EBITDA: NI + interest + tax + D&A + SBC + items = published (Form 10 reconciliation).
- Ex. 99.2 (FY2025 quarters, transcribed from slide images) vs the filed statements for Q1-25, Q2-25 and FY2025; Σ quarters = FY.
- Cash flow: CFO + CFI + CFF + FX = net change; beginning + net = ending. Balance sheet: TA = TL&E; components sum to totals.
- Free cash flow = CFO + capex (published). S&P Global Mobility segment: revenue − expenses = OP; OP + adjustments + amortization =
  adjusted OP; S&P Global revenue vs carve-out revenue (reported as an information line).
"""
import json, glob, os
HERE = os.path.dirname(os.path.abspath(__file__))
D = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(os.path.join(HERE, 'data', '*.json'))}
bad, n = [], [0]
def n0(x): return x or 0.0
def chk(name, a, b, tol=1.0):
    if a is None or b is None: return
    n[0] += 1
    if abs(a - b) > tol + 1e-9: bad.append(f'{name}: {a:.1f} vs {b:.1f} ({a - b:+.1f})')

def seg_items(s):
    return sum(n0(s.get(k)) for k in ('trans', 'sev', 'sev_oth', 'integ', 'acqdisp', 'legal', 'elt', 'other'))

for p, d in sorted(D.items()):
    i, sg, ng, cf, bs, mx = (d.get(k, {}) for k in ('is', 'seg', 'ng', 'cf', 'bs', 'mix'))
    if i:
        if 'opex' in i:
            da = n0(i.get('dep')) + n0(i.get('amort')) if 'dep' in i else i.get('da')
            chk(f'{p} OP', i['rev'] - i['opex'] - i['sga'] - da, i['op'])
        chk(f'{p} EBT', i['op'] - n0(i.get('othinc_exp')) - i['int'], i['ebt'])
        chk(f'{p} NI', i['ebt'] - i['tax'], i['ni'])
        if i.get('eps_dil'): chk(f'{p} EPS', i['ni'] / i['sh_dil'], i['eps_dil'], 0.0051)
    if sg and i:
        cfx, b2b, corp = sg.get('cfx', {}), sg.get('b2b', {}), sg.get('corp', {})
        chk(f'{p} Σ seg revenue', n0(cfx.get('rev')) + n0(b2b.get('rev')), i['rev'])
        if 'op' in cfx: chk(f'{p} Σ seg OP', cfx['op'] + b2b['op'] + corp['op'], i['op'])
        for nm, s in (('CARFAX', cfx), ('B2B', b2b), ('corp', corp)):
            if 'adj' in s and 'op' in s:
                da = s['da'] if 'da' in s and 'amort' not in s else n0(s.get('amort')) + n0(s.get('dep'))
                chk(f'{p} {nm} seg adj EBITDA build', s['op'] + da + n0(s.get('sbc')) + seg_items(s), s['adj'])
            if 'adjop' in s:
                chk(f'{p} {nm} adj OP build', s['op'] + n0(s.get('amort')) + seg_items(s), s['adjop'])
            if 'sub' in s: chk(f'{p} {nm} sub + non-sub', s['sub'] + s['nsub'], s['rev'])
            if 'us' in s: chk(f'{p} {nm} US + intl', s['us'] + s['intl'], s['rev'])
            if 'texp' in s and 'rev' in s: chk(f'{p} {nm} rev − exp', s['rev'] - s['texp'], s['op'])
            if 'opex' in s and 'texp' in s: chk(f'{p} {nm} opex+sga+da', s['opex'] + s['sga'] + s['da'], s['texp'])
        if 'adj' in cfx: chk(f'{p} Σ seg adj EBITDA', cfx['adj'] + b2b['adj'] + corp['adj'], ng.get('adj_ebitda'))
    if mx:
        chk(f'{p} mix sub', mx['sub'] + mx['nsub'], mx['rev']); chk(f'{p} mix US', mx['us'] + mx['intl'], mx['rev'])
        chk(f'{p} mix rev vs IS', mx['rev'], i.get('rev'))
    if ng.get('ebitda_da') is not None:
        items = sum(seg_items(sg.get(s, {})) for s in ('cfx', 'b2b', 'corp'))
        sbc = sum(n0(sg.get(s, {}).get('sbc')) for s in ('cfx', 'b2b', 'corp'))
        chk(f'{p} adj EBITDA recon', i['ni'] + ng['ebitda_int'] + i['tax'] + ng['ebitda_da'] + sbc + items, ng['adj_ebitda'])
    if 'ex992' in d:
        x = d['ex992']
        for k in ('rev', 'opex', 'sga', 'op', 'int', 'ebt', 'tax', 'ni'):
            if k in i and p not in ('Q3-25', 'Q4-25'): chk(f'{p} Ex.99.2 {k} vs filing', x[k], i[k])
        if 'dep' in i and p not in ('Q3-25', 'Q4-25'): chk(f'{p} Ex.99.2 D&A vs filing', x['da'], i['dep'] + i['amort'])
    if cf:
        chk(f'{p} CF sum', cf['cfo'] + cf['cfi'] + cf['cff'] + cf['fx'], cf['net'])
        chk(f'{p} cash roll', cf['cash_begin'] + cf['net'], cf['cash_end'])
        if ng.get('fcf') is not None and cf['ytd_months'] in (3, 12): chk(f'{p} FCF', cf['cfo'] + cf['capex'], ng['fcf'])
        if ng.get('fcf_h1') is not None: chk(f'{p} FCF 1H', cf['cfo'] + cf['capex'], ng['fcf_h1'])
    if bs:
        chk(f'{p} BS TA=TL&E', bs['ta'], bs['tle'])
        chk(f'{p} BS TL+TE', bs['tl'] + bs['teq'], bs['tle'])
        chk(f'{p} BS TCA', bs['cash'] + bs['due_from_c'] + bs['ar'] + bs['prepaid'], bs['tca'])
        chk(f'{p} BS TA', bs['tca'] + bs['ppe'] + bs['rou'] + bs['gw'] + bs['intang'] + n0(bs.get('due_from_nc')) + bs['onca'], bs['ta'])
        chk(f'{p} BS TCL', bs['ap'] + bs['due_to_c'] + bs['accr'] + bs['unearned'] + bs['ocl'], bs['tcl'])
        chk(f'{p} BS TL', bs['tcl'] + bs['lease'] + bs['dtl'] + bs['due_to_nc'] + n0(bs.get('ltd')) + bs['oncl'], bs['tl'])
        chk(f'{p} BS TE', bs['pci'] + bs['aoci'], bs['teq'])
        if cf: chk(f'{p} BS cash vs CF', bs['cash'], cf['cash_end'])
    sp = d.get('spgi')
    if sp and 'exp' in sp:
        chk(f'{p} SPGI rev − exp', sp['rev'] - sp['exp'], sp['op'])
        if 'adj_op' in sp: chk(f'{p} SPGI adj OP', sp['op'] + sp['ng_adj'] + sp['amort'], sp['adj_op'])
        chk(f'{p} SPGI sub + non-sub', sp['sub'] + sp['nsub'], sp['rev'])

# Σ quarters = FY (2025: four quarters on the carve-out basis)
for k in ('rev', 'opex', 'sga', 'op', 'int', 'tax', 'ni'):
    qs = [D[f'Q{q}-25']['is'].get(k) for q in (1, 2, 3, 4)]
    chk(f'2025 Σq {k}', sum(qs), D['2025']['is'][k], 2.0)
for s in ('cfx', 'b2b'):
    chk(f'2025 Σq {s} rev', sum(D[f'Q{q}-25']['seg'][s]['rev'] for q in (1, 2, 3, 4)), D['2025']['seg'][s]['rev'])
chk('2025 Σq adj EBITDA', sum(D[f'Q{q}-25']['ng']['adj_ebitda'] for q in (1, 2, 3, 4)), D['2025']['ng']['adj_ebitda'])
for y in (2023, 2024, 2025):
    qs = [D.get(f'Q{q}-{str(y)[2:]}', {}).get('spgi', {}).get('rev') for q in (1, 2, 3, 4)]
    if all(v is not None for v in qs): chk(f'{y} SPGI Σq revenue', sum(qs), D[str(y)]['spgi']['rev'])

print(f'{n[0]} checks; {len(bad)} exceptions')
print('\n'.join(bad) or 'all checks pass')
print('\nS&P Global Mobility segment revenue vs carve-out revenue (information):')
for p in sorted(D, key=lambda k: (k[-2:] if '-' in k else k[2:], k)):
    sp, i = D[p].get('spgi', {}), D[p].get('is', {})
    if sp.get('rev') is not None and i.get('rev') is not None:
        print(f'  {p:6} SPGI {sp["rev"]:7.0f}  MBGL {i["rev"]:7.0f}  diff {i["rev"] - sp["rev"]:+.0f}')
