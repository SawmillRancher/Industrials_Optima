"""Consistency checks on the normalised L3Harris data: statement arithmetic, segment build vs consolidated revenue / operating
income, non-GAAP EPS bridge vs published, adjusted EBIT (2019-21) and EBITDA (2023+) vs published, cash-flow and balance-sheet
tie-outs, quarters vs fiscal years, and a cross-check of revenue / net income / total assets / operating cash flow against the
XBRL company facts (as first filed). Tolerances reflect whole-million publication (+/-1; sums of quarters +/-2)."""
import json, os
import normalize, xbrl
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok = [], [0]
def chk(name, a, b, tol=1.01):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol: bad.append(f'{name}: {a:.2f} vs {b:.2f} ({a - b:+.2f})')
CORP = ('amort', 'fascas', 'restr', 'acq', 'gain', 'impair', 'other')
AC = ('amort', 'restr', 'acq', 'gain', 'impair', 'oth', 'nonop')
for p in normalize.periods():
    v = x(p)
    if not v or v.get('rev') is None: bad.append(f'{p}: no data'); continue
    oi = v['rev'] - v['cogs'] - v['sga'] - n(v.get('oth_op'))
    chk(f'{p} op income', oi, v['oi'])
    ebt = v['oi'] + v['nonop_pens'] + v['nonop_oth'] - v['int_net']
    chk(f'{p} ebt', ebt, v['ebt'])
    chk(f'{p} cont ops', v['ebt'] - v['tax'], v['cont'])
    chk(f'{p} net income', v['cont'] + v['disc'] - v['nci'], v['ni'])
    if v.get('sh_d'): chk(f'{p} gaap eps', (v['ni'] - v['pref_div']) / v['sh_d'], v.get('eps_d'), 0.0201)
    cur = v.get('sr_sms') is not None
    if cur:
        segrev = v['sr_sms'] + v['sr_csd'] + v['sr_ms'] + v['sr_inter']; segoi = v['so_sms'] + v['so_csd'] + v['so_ms']
    else:
        segrev = sum(n(v.get(f'lr_{k}')) for k in ('rf', 'ins', 'gcs', 'ex', 'cn', 'cs', 'sis', 'es', 'ims', 'sas', 'avs', 'ar')) + n(v.get('lr_elim'))
        segoi = sum(n(v.get(f'lo_{k}')) for k in ('rf', 'ins', 'gcs', 'ex', 'cn', 'cs', 'sis', 'es', 'ims', 'sas', 'avs', 'ar'))
    chk(f'{p} segment revenue', segrev + n(v.get('sr_other')), v['rev'])
    chk(f'{p} segment OI - corporate', segoi - sum(n(v.get(f'c_{c}')) for c in CORP), v['oi'])
    if not cur: chk(f'{p} segment OI published', segoi, v.get('seg_oi_pub'))
    if cur and p[-2:] in ('25', '24'):      # legacy (as originally reported) segments must also tie to revenue
        lrev = sum(n(v.get(f'lr_{k}')) for k in ('cs', 'ims', 'sas', 'ar')) + n(v.get('lr_elim'))
        chk(f'{p} legacy segment revenue', lrev + n(v.get('sr_other_orig')), v['rev'], 2)
    items = sum(n(v.get('a_' + c)) for c in AC)
    if v.get('e_pub') is not None:
        adjni = v['cont'] - v['nci'] - v['pref_div'] + items + v['a_tax'] + v['a_nci'] + v['a_round']
        chk(f'{p} non-GAAP EPS', adjni / v['sh_d'], v['e_pub'], 0.0101)
        if abs(v['a_round']) > 0.03 * v['sh_d'] + 1: bad.append(f"{p}: per-share rounding line {v['a_round']:.1f} exceeds +/-$0.03 x shares")
    if v.get('adj_ebit_pub') is not None:
        chk(f'{p} adjusted EBIT', v['oi'] + n(v.get('c_amort')) + sum(n(v.get('a_' + c)) for c in ('restr', 'acq', 'gain', 'impair', 'oth')) + v['nonop_pens'] + v['nonop_oth'] + n(v.get('a_nonop')), v['adj_ebit_pub'])
    if v.get('ebitda_pub') is not None and v.get('cf_da') is not None:
        chk(f'{p} EBITDA', v['ni_tot'] + v['tax'] + v['int_net'] + v['cf_da'], v['ebitda_pub'])
    if v.get('cf_cfo') is not None:
        chk(f'{p} cash', v['cf_beg'] + v['cf_net'], v['cf_end'])
        if v.get('bs_cash') is not None and abs(n(v.get('bs_cash_adj'))) > 1.01: bad.append(f"{p}: CF ending cash − BS cash = {v['bs_cash_adj']:.0f} (held-for-sale / restricted cash memo)")
    else: bad.append(f'{p}: no cash flow')
    if v.get('bs_ta') is not None: chk(f'{p} balance sheet', v['bs_ta'], v['bs_tle'])
    else: bad.append(f'{p}: no balance sheet')
    # XBRL cross-check (as first filed)
    r = normalize.REC[p]; end = r['period_end']
    m = {'TP19': 6}.get(p, 12 if p.isdigit() else 3)
    for key, concepts, mm in (('rev', ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet'], m), ('ni', ['NetIncomeLoss'], m), ('bs_ta', ['Assets'], 0)):
        if p in ('Q4-19',) or (p.startswith('Q4')): continue          # Q4 is not tagged on a three-month basis
        xvv = xbrl.xv(concepts, end, mm)
        if xvv is not None: chk(f'{p} XBRL {key}', v.get(key), xvv)
QS = ['rev', 'cogs', 'sga', 'oi', 'ebt', 'tax', 'ni', 'nonop_pens', 'int_net', 'seg_oi_pub', 'c_amort', 'cf_cfo', 'cf_capex', 'cf_bb', 'cf_div', 'cf_da', 'k_orders',
      'sr_sms', 'sr_csd', 'sr_ms', 'so_sms', 'so_csd', 'so_ms']
for y in range(2020, 2026):
    yy = str(y)[2:]
    for k in QS:
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        if y == 2024 and k == 'seg_oi_pub': continue      # FY2024 annual on the recast three-segment basis; quarters as originally reported
        if all(q is not None for q in qs): chk(f'FY{y} {k} sum-q', sum(qs), x(str(y)).get(k), 2.01 if k != 'k_orders' else 250)
        elif x(str(y)).get(k) is not None and k not in ('k_orders',) and not (y == 2024 and k[:3] in ('sr_', 'so_')): bad.append(f'FY{y} {k}: quarters missing {[i + 1 for i, q in enumerate(qs) if q is None]}')
for k in QS:
    qs = [x(p).get(k) for p in ('Q3-19', 'Q4-19')]
    if all(q is not None for q in qs): chk(f'TP19 {k} sum-q', sum(qs), x('TP19').get(k), 2.01)
KNOWN = {
    '2013 XBRL rev': 'the earliest XBRL fact tagged Revenues for FY2013 (420.3) is a component line, not consolidated revenue; the face statement (5,111.7) is used',   # documented exceptions (README "Data corrections and known exceptions")
    '2013: per-share rounding': 'FY2013 EPS under the two-class method (participating securities): published continuing EPS 4.16 vs 4.19 computed',
    '2014 gaap eps': 'two-class method (participating securities)',
    'FY2020 sga sum-q': 'quarterly impairment / COVID charges shown on separate lines in the 10-K',
    'FY2021 nonop_pens sum-q': 'rounding of quarterly non-operating income splits',
    'FY2021 cf_capex sum-q': '10-K shows gross additions; Q1-Q2 releases net of PP&E sale proceeds',
    'FY2022 cogs sum-q': 'Q1-22 cost of revenue / ESA reclassified in later 2022 filings (713 -> 745)', 'FY2022 sga sum-q': 'same reclassification',
    'FY2023 cogs sum-q': 'quarterly reclassifications between cost of revenue and G&A / impairment lines in the 10-K', 'FY2023 sga sum-q': 'same',
    'FY2024 sga sum-q': 'quarterly impairment lines folded into G&A in the 10-K', 'FY2024 cogs sum-q': 'same'}
exp = [b for b in bad if any(b.startswith(k) for k in KNOWN)]
bad = [b for b in bad if b not in exp]
print('\n'.join(bad) or 'all checks pass')
print('known exceptions:'); print('\n'.join('  ' + e + '  <- ' + next(v for k, v in KNOWN.items() if e.startswith(k)) for e in exp))
print(f'{ok[0]} checks, {len(bad)} issues')
