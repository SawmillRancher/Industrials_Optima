"""Harmonise the extracted Meta data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m; shares and people in m).

Basis: every period as originally reported in its own earnings release (FY2009-2011: IPO prospectus). Later re-presentations are not
recast into the main rows (FY2011 marketing & sales / G&A reclassified in the FY2012 release; FY2016 recast for ASU 2016-09 in the 2017
releases; restricted cash added to the cash-flow statement from 2018, ASU 2016-18); the prior-year figures as presented a year later are
kept as *_py memo keys where they differ. Exceptions, by source:
  - Segments (Family of Apps / Reality Labs): first presented in the Q4-2021 release with FY2019-2020, Q4-2020 and the 2021 quarters
    recast; earlier periods are single-segment.
  - Ad impressions / price per ad y/y %: releases from Q4-2021; before that the 10-Q / 10-K MD&A ("number of ads delivered"; price per ad
    disclosed 2014-2018 and from Q4-2021). Not published for Q4s before 2021 (the 10-K gives the year).
  - Revenue by geography (billing address of the customer): 10-Q / 10-K notes from 2018.
  - Shares outstanding at the balance-sheet date: 10-Q / 10-K balance-sheet caption (Class A + Class B, millions).
Cash flow: the releases give three-month cash-flow statements for every quarter (no year-to-date derivation needed).
Non-GAAP: the company published non-GAAP costs / operating income / net income / EPS (excluding share-based compensation, related payroll
tax, amortization of intangibles from Q3-2014, and their tax effects) from the IPO to Q4-2016; free cash flow from Q2-2013. One-off items
the company quantified in later releases are in manual_items.json ('one_offs')."""
import json, glob, os
import xbrl

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))

def N(x): return x or 0.0
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def fyq(p):
    if p.isdigit(): return int(p), 4
    return int('20' + p[-2:]), int(p[1])

FY0, FYQ0, FYC = 2009, 2013, 2026
def periods():
    out = [str(y) for y in range(FY0, FYC)]
    for y in range(FYQ0, FYC + 1):
        out += [qk(y, q) for q in (1, 2, 3, 4) if not (y == FYC and q > 2)]
    return out

def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

def do_pl(p):
    r = REC.get(p)
    if not r: LOG.append(f'{p}: no record'); return
    i, n = r['is'], r.get('ngaap', {})
    put(p, 'rev', i['rev'])
    for k in ('cogs', 'rd', 'mm', 'ga', 'costs', 'oi', 'ebt', 'tax', 'ni', 'eps_b', 'eps_d', 'sh_b', 'sh_d'): put(p, k, i.get(k))
    io = i['io_net'] if 'io_net' in i else N(i.get('int_exp')) + N(i.get('oth'))
    put(p, 'io_net', io)
    put(p, 'ni_part', N(i.get('ni_part')))
    put(p, 'ni_common', i.get('ni_common', i['ni'] - N(i.get('ni_part'))))
    pe = MAN['pre_ipo_eps'].get(p)
    if pe:                                     # FY2009-11: two-class EPS from the prospectus EPS note (Class A diluted basis)
        put(p, 'sh_b', pe['sh_b']); put(p, 'sh_d', pe['sh_d']); put(p, 'ni_dil_realloc', pe['ni_dil'] - (i['ni'] - N(i.get('ni_part'))))
    else:
        put(p, 'ni_dil_realloc', 0.0)
    # revenue split
    seg = r.get('seg') or {}
    adv = seg.get('foa_adv', n.get('adv'))
    put(p, 'adv', adv)
    if adv is not None: put(p, 'oth_rev', i['rev'] - adv)
    for k in ('foa_adv', 'foa_oth', 'foa_rev', 'rl_rev', 'foa_oi', 'rl_oi'): put(p, k, seg.get(k))
    put(p, 'rev_exfx', n.get('rev_exfx')); put(p, 'adv_exfx', n.get('adv_exfx'))
    # company non-GAAP (IPO - Q4-2016)
    if n.get('ng_oi') is not None:
        put(p, 'ng_sbc', n.get('sbc_ng')); put(p, 'ng_payroll', N(n.get('payroll'))); put(p, 'ng_amort', N(n.get('amort')))
        put(p, 'ng_oi', n['ng_oi']); put(p, 'ng_ni', n.get('ng_ni')); put(p, 'ng_taxadj', n.get('tax_adj'))
        put(p, 'ng_sh', n.get('ng_sh')); put(p, 'ng_eps', n.get('ng_eps'))
    if n.get('fcf') is not None:
        put(p, 'fcf_pub', n['fcf']); put(p, 'fcf_cl', N(n.get('fcf_cl'))); put(p, 'fcf_flp', N(n.get('fcf_flp')))
    # KPIs (release text; 10-Q / 10-K MD&A for ad impressions / price per ad before Q4-2021)
    k, q10 = r.get('kpi') or {}, r.get('q10') or {}
    for kk in ('dau', 'mau', 'dap', 'map', 'headcount'): put(p, kk, k.get(kk))
    for kk in ('impr_g', 'price_g'):
        v = k.get(kk, q10.get(kk))
        put(p, kk, v)
    for kk in ('geo_usc', 'geo_eu', 'geo_ap', 'geo_row', 'sh_out'): put(p, kk, q10.get(kk))
    if not p.isdigit() and p[1] == '4' and q10.get('sh_out') is None:          # Q4: the 10-K balance sheet
        put(p, 'sh_out', (REC.get(str(fyq(p)[0]), {}).get('q10') or {}).get('sh_out'))
    # prior-year comparatives as presented a year later (restatement memo)
    fy, q = fyq(p)
    nxt = REC.get(str(fy + 1) if p.isdigit() else qk(fy + 1, q))
    if nxt and nxt.get('py', {}).get('is'):
        pi = nxt['py']['is']
        for kk in ('rev', 'cogs', 'rd', 'mm', 'ga', 'oi', 'ni'):
            if pi.get(kk) is not None and i.get(kk) is not None and abs(pi[kk] - i[kk]) > 0.5: put(p, kk + '_py', pi[kk])

def do_oneoffs(p):
    """company-quantified one-off items (manual_items.json): pre-tax operating items (legal, restructuring / severance) and discrete tax
    items; the company's 'excluding' EPS where published."""
    oo = MAN['one_offs'].get(p)
    if oo is None and p.isdigit():                         # fiscal year = sum of the quarters' items (EPS 'excluding' only where stated)
        qs = [MAN['one_offs'].get(qk(int(p), q), {}) for q in (1, 2, 3, 4)]
        oo = {k: sum(q.get(k, 0.0) for q in qs) for k in ('legal', 'restr', 'tax')}
        te = [q.get('tax_effect') for q in qs if q.get('tax_effect') is not None]
        if te and all(any(q.get(k) for k in ('legal', 'restr')) <= (q.get('tax_effect') is not None) for q in qs): oo['tax_effect'] = sum(te)
    oo = oo or {}
    put(p, 'oo_legal', oo.get('legal', 0.0)); put(p, 'oo_restr', oo.get('restr', 0.0)); put(p, 'oo_tax', oo.get('tax', 0.0))
    put(p, 'oo_taxeff', oo.get('tax_effect'))
    if oo.get('adj_eps') is not None: put(p, 'oo_eps_pub', oo['adj_eps'])
    x = DATA.get(p, {}).get('x', {})
    put(p, 'e_pub', x.get('ng_eps', oo.get('adj_eps')))
    if oo.get('label'): put(p, 'oo_label', oo['label'])

def do_geo_q4():
    """Q4 revenue by geography = fiscal year (10-K) - nine months (Q1-Q3 10-Qs); noted in the model."""
    for y in range(FYQ0, FYC):
        a = DATA.get(str(y), {}).get('x', {}); q4 = DATA.get(qk(y, 4), {}).get('x')
        if q4 is None or q4.get('geo_usc') is not None or a.get('geo_usc') is None: continue
        qs = [DATA.get(qk(y, q), {}).get('x', {}) for q in (1, 2, 3)]
        if all(q.get('geo_usc') is not None for q in qs):
            for k in ('geo_usc', 'geo_eu', 'geo_ap', 'geo_row'): put(qk(y, 4), k, a[k] - sum(q[k] for q in qs))
            put(qk(y, 4), 'geo_q4_derived', 1)

def do_cf(p):
    r = REC.get(p)
    if not r or not r.get('cf'): LOG.append(f'{p}: no CF'); return
    c = r['cf']
    ni = c.get('ni', r['is']['ni'])
    put(p, 'cf_ni', ni); put(p, 'cf_dda', c['dda']); put(p, 'cf_sbc', c['sbc']); put(p, 'cf_def', N(c.get('def')))
    put(p, 'cf_wc', c['cfo'] - ni - c['dda'] - c['sbc'] - N(c.get('def'))); put(p, 'cf_cfo', c['cfo'])
    put(p, 'cf_capex', c['capex'] + N(c.get('ppe_proc'))); put(p, 'cf_ms', N(c.get('ms_net'))); put(p, 'cf_nme', N(c.get('nme'))); put(p, 'cf_acq', N(c.get('acq')))
    put(p, 'cf_oinv', c['cfi'] - c['capex'] - N(c.get('ppe_proc')) - N(c.get('ms_net')) - N(c.get('nme')) - N(c.get('acq'))); put(p, 'cf_cfi', c['cfi'])
    put(p, 'cf_bb', N(c.get('bb'))); put(p, 'cf_div', N(c.get('div'))); put(p, 'cf_netshare', N(c.get('netshare')))
    put(p, 'cf_debt', N(c.get('debt_iss')) + N(c.get('debt_rep'))); put(p, 'cf_lease', N(c.get('lease'))); put(p, 'cf_eqiss', N(c.get('eq_iss')))
    put(p, 'cf_ofin', c['cff'] - N(c.get('bb')) - N(c.get('div')) - N(c.get('netshare')) - N(c.get('debt_iss')) - N(c.get('debt_rep'))
        - N(c.get('lease')) - N(c.get('eq_iss')))
    put(p, 'cf_cff', c['cff']); put(p, 'cf_fx', N(c.get('fx')))
    put(p, 'cf_net', c['cfo'] + c['cfi'] + c['cff'] + N(c.get('fx')))
    put(p, 'cf_beg', c.get('beg')); put(p, 'cf_end', c.get('end'))

def do_bs(p):
    r = REC.get(p)
    if not r or not r.get('bs'): return
    b = r['bs']
    ta, tca = b['ta'], b['tca']
    gwi = N(b.get('gw')) + N(b.get('intang'))
    put(p, 'bs_cash', b['cash']); put(p, 'bs_ms', N(b.get('ms'))); put(p, 'bs_ar', b['ar'])
    put(p, 'bs_oca', tca - b['cash'] - N(b.get('ms')) - b['ar']); put(p, 'bs_tca', tca)
    put(p, 'bs_nme', N(b.get('nme'))); put(p, 'bs_ppe', b['ppe']); put(p, 'bs_rou', N(b.get('rou'))); put(p, 'bs_gw', gwi)
    put(p, 'bs_onca', ta - tca - N(b.get('nme')) - b['ppe'] - N(b.get('rou')) - gwi); put(p, 'bs_ta', ta)
    clc = N(b.get('clc'))
    put(p, 'bs_ap', b['ap']); put(p, 'bs_std', clc); put(p, 'bs_ocl', b['tcl'] - b['ap'] - clc); put(p, 'bs_tcl', b['tcl'])
    ltd = N(b.get('ltd')) + N(b.get('cll'))
    put(p, 'bs_ltd', ltd); put(p, 'bs_oll', N(b.get('oln')))
    tl = b.get('tl')
    te = b['te'] if b.get('te') is not None else b['tle'] - tl
    put(p, 'bs_ol', ta - te - b['tcl'] - ltd - N(b.get('oln')))
    put(p, 'bs_eq', te); put(p, 'bs_tle', b['tle'])
    put(p, 'debt_tot', clc + ltd); put(p, 'debt_notes', N(b.get('ltd'))); put(p, 'debt_cl', clc + N(b.get('cll')))

def do_xbrl(p):
    """XBRL company facts (earliest-filed 10-K / 10-Q fact): interest income, interest expense (net of capitalized interest), dividends
    declared per share (from Q1-2024). Q4 = fiscal year - nine months."""
    fy, q = fyq(p)
    def get(concepts):
        if p.isdigit(): return xbrl.first_of(concepts, fy, 'FY')
        if q < 4: return xbrl.first_of(concepts, fy, 'Q', q)
        a = xbrl.first_of(concepts, fy, 'FY'); n9 = xbrl.first_of(concepts, fy, 'YTD', 3)
        return a - n9 if a is not None and n9 is not None else None
    put(p, 'x_intinc', get(['InvestmentIncomeInterest']))
    put(p, 'x_intexp', get(['InterestExpenseNonoperating', 'InterestExpense']))
    iq = MAN.get('debt', {}).get('interest_q2_26', {})             # Q1/Q2-26: 10-Q MD&A interest table (not tagged quarterly)
    if p == 'Q2-26': put(p, 'x_intinc', iq['interest_income']); put(p, 'x_intexp', iq['interest_expense'])
    if p == 'Q1-26': put(p, 'x_intinc', iq['h1_interest_income'] - iq['interest_income']); put(p, 'x_intexp', iq['h1_interest_expense'] - iq['interest_expense'])
    d = get(['CommonStockDividendsPerShareDeclared'])
    put(p, 'dps', d if d is not None else (0.0 if fy < 2024 else None))

def run():
    load()
    for p in periods():
        do_pl(p); do_oneoffs(p); do_cf(p); do_bs(p); do_xbrl(p)
    do_geo_q4()
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: round(x[k], 1) if isinstance(x.get(k), float) else x.get(k) for k in
                  ('rev', 'adv', 'oi', 'ni', 'eps_d', 'sh_d', 'cf_cfo', 'cf_end', 'bs_cash', 'bs_ta', 'sh_out', 'impr_g', 'price_g', 'fcf_pub', 'ng_eps')})
    print('\n'.join(LOG))
