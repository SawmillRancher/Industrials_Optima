"""Data consistency checks on the normalised Fair Isaac data (run after extract.py; no raw downloads needed).

Checks: statement arithmetic (revenue - costs = operating income; + non-operating = pre-tax; - tax (+ disc ops) = net income),
segment summary vs operating income, Scores + Software segment revenue vs consolidated, interest split vs non-operating total,
non-GAAP bridge (model pre-tax items + derived tax effect) vs published non-GAAP net income, published non-GAAP EPS vs
non-GAAP net income / diluted shares, free cash flow (company definition) vs published, cash-flow and balance-sheet tie-outs,
Σ quarters = fiscal year for flows, and XBRL cross-checks (revenue, operating income, net income, total assets, operating
cash flow; earliest-filed facts)."""
import json, os
import normalize as nz
import xbrl

D = nz.run()
FAIL, NCHK = [], [0]
EXC = {}          # documented exceptions: (period, check) -> reason

def chk(p, name, a, b, tol=0.15):
    if a is None or b is None: return
    NCHK[0] += 1
    if abs(a - b) > tol:
        if (p, name) in EXC: return
        FAIL.append(f'{p}: {name} {a:,.3f} vs {b:,.3f} (diff {a - b:,.3f})')

def x(p): return D.get(p, {}).get('x', {})

FLOW = ['rev', 'cogs', 'rd', 'sga', 'opinc', 'ebt', 'tax', 'ni', 's_sc_rev', 's_sc_oi', 's_sw_oi', 's_corp', 's_sbc', 'int_net', 'cf_cfo', 'cf_capex', 'cf_bb',
        'ng_ni_pub', 'fcf_pub', 'k_b2b', 'k_b2c', 'k_plat', 'k_nonplat']

for p in nz.periods():
    v = x(p)
    if 'rev' not in v: FAIL.append(f'{p}: no data'); continue
    costs = sum(v.get(k) or 0 for k in ('cogs', 'rd', 'sga', 'amort_is', 'restr_is', 'oth_op'))
    chk(p, 'rev - costs = opinc', v['rev'] - costs, v['opinc'], 0.01)
    chk(p, 'opinc + nonop = ebt', v['opinc'] + v['nonop'], v['ebt'], 0.01)
    chk(p, 'ebt - tax + disc = ni', v['ebt'] - v['tax'] + v['disc'], v['ni'], 0.01)
    if 's_opinc' in v:
        seg = v.get('s_sc_oi', 0) + v.get('s_sw_oi', 0) + v.get('s_corp', 0) - v['s_sbc'] - v['s_amort'] - v['s_restr'] - v['s_gain'] - v['s_other']
        chk(p, 'segment summary = operating income', seg, v['opinc'], 0.01)
        chk(p, 'segment summary opinc = IS', v['s_opinc'], v['opinc'], 0.01)
    if 'int_net' in v: chk(p, 'interest split = non-operating', -v['int_net'] + v['oth_inc'], v['nonop'], 0.01)
    # non-GAAP
    if v.get('ng_ni_pub') is not None:
        items = sum(v.get(k) or 0 for k in ('adj_sbc', 'adj_amort', 'adj_restr', 'adj_gain')) + (v.get('adj_nonop') or 0)
        tax = v['ng_ni_pub'] - v['ni'] - items - (v.get('ng_co_etb') or 0) - (v.get('ng_co_taxd') or 0)
        chk(p, 'non-GAAP tax effect on items (ex excess tax benefit / discrete) within 0-45% of items', 0.0, max(0.0, abs(tax) - 0.45 * abs(items) - 1.0), 0.01)
        if not v.get('ng_net_fmt'):
            co = sum(v.get(f'ng_co_{c}') or 0 for c in ('sbc', 'amort', 'restr', 'gain'))
            chk(p, 'company pre-tax items = model items', co, items - (v.get('adj_nonop') or 0), 0.02)
        if v.get('sh_d'): chk(p, 'non-GAAP EPS = NI / diluted shares', v['ng_ni_pub'] / v['sh_d'], v['ng_eps_pub'], 0.0151)
    if v.get('sh_d') and v.get('eps_d') is not None: chk(p, 'diluted EPS = NI / shares', v['ni'] / v['sh_d'], v['eps_d'], 0.0151)
    # cash flow / FCF
    if 'cf_cfo' in v:
        chk(p, 'CF: flows = change in cash', v['cf_cfo'] + v['cf_cfi'] + v['cf_cff'] + v['cf_fx'], v['cf_end'] - v['cf_beg'], 0.01)
        if v.get('fcf_pub') is not None:
            fcf = v['cf_cfo'] + v['cf_capex'] + v['cf_capsw']
            chk(p, 'FCF (CFO - capex) = published + dividends deducted (FY2013-Q2/17 definition)', fcf, v['fcf_pub'] - (v.get('fcf_div') or 0), 0.02)
    if 'bs_ta' in v:
        chk(p, 'BS: TA = TL&E', v['bs_ta'], v['bs_tle'], 0.01)
        chk(p, 'BS: TL + equity = TL&E', v['bs_tl'] + v['bs_eq'], v['bs_tle'], 0.01)
        if 'cf_end' in v: chk(p, 'BS cash = CF ending cash', v['bs_cash'], v['cf_end'], 0.01)
    # segment revenue
    if v.get('s_sc_rev') is not None and v.get('k_b2b') is not None:
        chk(p, 'B2B + B2C = Scores', v['k_b2b'] + v['k_b2c'], v['s_sc_rev'], 0.02)
    if v.get('k_plat') is not None and v.get('rev_saas') is not None:
        chk(p, 'platform + non-platform = on-premises & SaaS', v['k_plat'] + v['k_nonplat'], v['rev_saas'], 0.02)
    if v.get('rev_scores_is') is not None and v.get('s_sc_rev') is not None:
        chk(p, 'Scores IS revenue line = Scores segment', v['rev_scores_is'], v['s_sc_rev'], 0.02)

# Σ quarters = fiscal year
for y in range(2013, 2026):
    for k in FLOW:
        qs = [x(f'Q{q}-{str(y)[2:]}').get(k) for q in (1, 2, 3, 4)]
        a = x(str(y)).get(k)
        if a is None or any(q is None for q in qs): continue
        chk(str(y), f'Σ quarters = FY [{k}]', sum(qs), a, 0.02)

# XBRL cross-checks (earliest-filed 10-K / 10-Q facts)
XB = [('rev', ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet']), ('opinc', ['OperatingIncomeLoss']),
      ('ni', ['NetIncomeLoss']), ('cf_cfo', ['NetCashProvidedByUsedInOperatingActivities'])]
for y in range(2010, 2026):
    for k, cs in XB:
        chk(str(y), f'XBRL {k}', x(str(y)).get(k), xbrl.first_of(cs, y, 'FY'), 0.02)
    chk(str(y), 'XBRL total assets', x(str(y)).get('bs_ta'), xbrl.value('Assets', y, 'I', 4), 0.02)
for y in range(2013, 2027):
    for q in (1, 2, 3):
        p = f'Q{q}-{str(y)[2:]}'
        for k, cs in XB[:3]:
            chk(p, f'XBRL {k}', x(p).get(k), xbrl.first_of(cs, y, 'Q', q), 0.02)
        chk(p, 'XBRL total assets', x(p).get('bs_ta'), xbrl.value('Assets', y, 'I', q), 0.02)

print(f'{NCHK[0]} checks, {len(FAIL)} failures')
for f in FAIL: print('  ', f)
print('\n'.join(nz.LOG))
