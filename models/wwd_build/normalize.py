"""Harmonise the extracted Woodward data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m).

Basis: every period as originally reported in its own earnings release (the FY2016 cost-line reclassification and the FY2018
pension-cost reclassification (ASU 2017-07), which moved FY2018 segment earnings in the FY2019 release, are not recast; the
restated comparatives are kept as *_py memo keys). Exceptions, by source priority:
  - Sales by primary market (10-Q / 10-K revenue note, from FY2019): Aerospace as reported; Industrial markets on the current
    basis (power generation / transportation / oil & gas, introduced in the FY2023 10-K) from the latest filing that presents
    the period (FY2021-22 annual from the FY2023 10-K; FY2023 quarters from the FY2024 10-Qs); the earlier basis
    (reciprocating engines / industrial turbines / renewables) is kept as legacy memo keys.
  - D&A: release EBIT / EBITDA reconciliations (depreciation + amortization of intangibles).
  - Share-based compensation, deferred income taxes, shares outstanding (issued less treasury): XBRL company facts.
Cash flow: releases give year-to-date statements; discrete quarters derived (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M).
Adjusted measures: published from Q2 FY2018 (adjusted EPS, EBIT, EBITDA); quarters with no adjusting items show
adjusted = GAAP. FY2011-FY2017: no adjusted measures published (EBIT / EBITDA / FCF only) - adjusted = GAAP, flagged.
"""
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

def periods():
    out = [str(y) for y in range(2011, 2026)]
    for y in range(2021, 2027):
        out += [qk(y, q) for q in (1, 2, 3, 4) if not (y == 2026 and q == 4)]
    return out

def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

# adjusting-item categories -> model lines
MCAT = {'RESTR': 'restr', 'ACQ': 'acq', 'STEPUP': 'pa', 'AMORT': 'pa', 'GAIN': 'gain', 'SWAP': 'gain', 'IMPAIR': 'impair',
        'OTHER': 'other', 'PENSION': 'other', 'LEGAL': 'other'}
OCATS = ['restr', 'acq', 'pa', 'gain', 'impair', 'other']

def do_pl(p):
    r = REC.get(p)
    if not r: LOG.append(f'{p}: no record'); return
    fy, q = fyq(p)
    i, s, n = r['is'], r['seg'], r['ngaap']
    rev = i['rev']
    put(p, 'rev', rev); put(p, 'cogs', i['cogs']); put(p, 'gp', rev - i['cogs'])
    put(p, 'sga', i.get('sga')); put(p, 'rd', i.get('rd')); put(p, 'amort_is', N(i.get('amort'))); put(p, 'restr', N(i.get('restr')))
    put(p, 'oth_op', sum(v for _, v in i.get('other_lines', [])))
    put(p, 'oth_op_labels', '; '.join(f'{l} {v:,.1f}' for l, v in i.get('other_lines', [])))
    put(p, 'oth_inc', -N(i.get('oth')))
    put(p, 'int_exp', i['int_exp']); put(p, 'int_inc', -N(i.get('int_inc')))
    put(p, 'ebt', i['ebt']); put(p, 'tax', i['tax']); put(p, 'ni', i['ni'])
    put(p, 'nci', N(i.get('nci')) if i.get('ni_tot') is not None and i.get('ni_tot') != i['ni'] else 0.0)
    ebit = i['ni'] + i['tax'] + i['int_exp'] + N(i.get('int_inc'))       # release shows interest income as a negative cost
    put(p, 'ebit', ebit)
    for k in ('eps_b', 'eps_d', 'dps'): put(p, k, i.get(k))
    put(p, 'sh_b', i.get('sh_b')); put(p, 'sh_d', i.get('sh_d'))
    # segments
    put(p, 'sr_aero', s['sales_aero']); put(p, 'sr_ind', s['sales_ind']); put(p, 'se_aero', s['earn_aero']); put(p, 'se_ind', s['earn_ind'])
    put(p, 'nonseg', s['nonseg']); put(p, 'ind_name', s.get('ind_name'))
    py = (REC.get(p, {}).get('py') or {}).get('seg') or {}
    for k, kk in (('earn_aero', 'se_aero_py'), ('earn_ind', 'se_ind_py'), ('nonseg', 'nonseg_py')):
        if py.get(k) is not None and abs(py[k] - s[k]) > 0.05: put(p, kk, py[k])
    # sales by primary market
    em, emp, emp2 = r.get('em') or {}, r.get('em_py') or {}, r.get('em_py2') or {}
    for k in ('com_oem', 'com_aft', 'def_oem', 'def_aft'): put(p, f'em_{k}', em.get(k))
    src = em if 'pg' in em else (emp if 'pg' in emp else (emp2 if 'pg' in emp2 else {}))
    for k in ('pg', 'trans', 'og'): put(p, f'em_{k}', src.get(k))
    if src and src is not em: put(p, 'em_ind_recast', 1); LOG.append(f'{p}: Industrial markets from the following year\'s filing (recast)')
    for k in ('recip', 'ind_turb', 'renew'): put(p, f'em_{k}', em.get(k))
    # non-GAAP
    put(p, 'ebit_pub', n.get('ebit_pub')); put(p, 'ebitda_pub', n.get('ebitda_pub'))
    put(p, 'd_dep', n.get('dep')); put(p, 'd_amort', n.get('amort'))
    put(p, 'fcf_pub', n.get('fcf_pub')); put(p, 'adj_fcf_pub', n.get('adj_fcf_pub'))
    put(p, 'adj_nonseg_pub', n.get('adj_nonseg_pub'))
    a = n.get('adj')
    published = (fy, q) >= (2018, 2) if not p.isdigit() else fy >= 2018
    if a:
        tot = {c: 0.0 for c in OCATS}; tax = 0.0; labels = {c: [] for c in OCATS}
        for it in a['items']:
            if it['cat'] in ('TAX', 'TAXD'):
                tax += N(it['net'])
            else:
                c = MCAT.get(it['cat'], 'other'); tot[c] += N(it['pre'])
                if it['pre']: labels[c].append(it['label'])
                if a['fmt'] == 'a': tax += N(it['net']) - N(it['pre'])
        for c in OCATS:
            put(p, f'oa_{c}', tot[c]); put(p, f'oa_{c}_lab', '; '.join(dict.fromkeys(labels[c])))
        put(p, 'oa_tax', tax)
        put(p, 'adj_ni_pub', a['adj_ni']); put(p, 'e_pub', a['adj_eps'])
        put(p, 'adj_ebit_pub', n.get('adj_ebit_pub')); put(p, 'adj_ebitda_pub', n.get('adj_ebitda_pub'))
        # adjustments already in D&A (L'Orange backlog amortization): items in adjusted EBIT not in adjusted EBITDA
        if n.get('adj_ebitda_pub') is not None and n.get('ebitda_pub') is not None:
            put(p, 'oa_in_dda', round(sum(tot.values()) - (n['adj_ebitda_pub'] - n['ebitda_pub']), 6))
    else:
        for c in OCATS: put(p, f'oa_{c}', 0.0)
        put(p, 'oa_tax', 0.0); put(p, 'oa_in_dda', 0.0)
        if published:
            put(p, 'adj_ni_pub', i['ni']); put(p, 'e_pub', i['eps_d'])
            put(p, 'adj_ebit_pub', n.get('adj_ebit_pub', n.get('ebit_pub'))); put(p, 'adj_ebitda_pub', n.get('adj_ebitda_pub', n.get('ebitda_pub')))
            put(p, 'adj_none', 1)
    put(p, 'adj_basis', 'published' if published else 'none')

# ---------------------------------------------------------------- cash flow
def cf_ytd(fy, q):
    p = str(fy) if q == 4 and fy <= 2025 and REC.get(str(fy)) else qk(fy, q)
    r = REC.get(p) or REC.get(qk(fy, q))
    if not r or not r.get('cf'): return None
    c = r['cf']
    o = {k: N(c.get(k)) for k in ('cfo', 'capex', 'acq', 'divest', 'cfi', 'div', 'bb', 'stock_iss', 'cff', 'fx', 'net')}
    o['beg'], o['end'] = c.get('beg'), c.get('end')
    x = r.get('x') or {}
    o['sbc'] = N(x.get('sbc_ytd')); o['def'] = N(x.get('deftax_ytd'))
    return o

def cf_lines(c, ni, dda):
    o = {'cf_ni': ni, 'cf_dda': dda, 'cf_sbc': c['sbc'], 'cf_def': c['def']}
    o['cf_wc'] = c['cfo'] - ni - dda - c['sbc'] - c['def']
    o['cf_cfo'] = c['cfo']; o['cf_capex'] = c['capex']; o['cf_acq'] = c['acq']; o['cf_divest'] = c['divest']
    o['cf_oinv'] = c['cfi'] - c['capex'] - c['acq'] - c['divest']; o['cf_cfi'] = c['cfi']
    o['cf_bb'] = c['bb']; o['cf_div'] = c['div']; o['cf_stock'] = c['stock_iss']
    o['cf_ofin'] = c['cff'] - c['bb'] - c['div'] - c['stock_iss']; o['cf_cff'] = c['cff']; o['cf_fx'] = c['fx']
    o['cf_net'] = c['cfo'] + c['cfi'] + c['cff'] + c['fx']
    return o

def x_(p, k): return DATA.get(p, {}).get('x', {}).get(k)

def do_cf():
    for y in range(2011, 2026):
        p = str(y); a = cf_ytd(y, 4)
        if not a: LOG.append(f'{p}: no annual CF'); continue
        dda = N(x_(p, 'd_dep')) + N(x_(p, 'd_amort'))
        for k, v in cf_lines(a, x_(p, 'ni'), dda).items(): put(p, k, v)
        put(p, 'cf_beg', a['beg']); put(p, 'cf_end', a['end'])
    for y in range(2021, 2027):
        prev, ni_c, dda_c = None, 0.0, 0.0
        for q in (1, 2, 3, 4):
            if y == 2026 and q == 4: break
            p = qk(y, q)
            cur = cf_ytd(y, q)
            ni_c += x_(p, 'ni'); dda_c += N(x_(p, 'd_dep')) + N(x_(p, 'd_amort'))
            if cur is None: LOG.append(f'{p}: no YTD CF'); prev = None; continue
            lc = cf_lines(cur, ni_c, dda_c)
            if q == 1: d = lc; beg = cur['beg']
            else:
                if prev is None: continue
                d = {k: lc[k] - prev[0][k] for k in lc}; beg = prev[1]
            for k, v in d.items(): put(p, k, v)
            put(p, 'cf_beg', beg); put(p, 'cf_end', cur['end'])
            prev = (lc, cur['end'])

# ---------------------------------------------------------------- balance sheet
def do_bs(p):
    r = REC.get(p)
    if not r or not r.get('bs'): return
    b = r['bs']
    ta, tca = b['ta'], b['tca']
    put(p, 'bs_cash', b['cash']); put(p, 'bs_ar', b['ar']); put(p, 'bs_inv', b['inv']); put(p, 'bs_oca', tca - b['cash'] - b['ar'] - b['inv'])
    put(p, 'bs_tca', tca); put(p, 'bs_ppe', b['ppe']); put(p, 'bs_gw', b['gw']); put(p, 'bs_int', b['intang'])
    put(p, 'bs_onca', ta - tca - b['ppe'] - b['gw'] - b['intang']); put(p, 'bs_ta', ta)
    std = N(b.get('std')) + N(b.get('cltd'))
    put(p, 'bs_ap', b['ap']); put(p, 'bs_std', std); put(p, 'bs_ocl', b['tcl'] - b['ap'] - std); put(p, 'bs_tcl', b['tcl'])
    put(p, 'bs_ltd', N(b.get('ltd')))
    teq = b['tle'] - b['tl'] if b.get('tl') is not None else b['eq']
    nci = N(b.get('nci')) if b.get('nci') is not None and b.get('te') is not None and b['te'] != b.get('eq') else 0.0
    put(p, 'bs_ol', ta - teq - b['tcl'] - N(b.get('ltd')))
    put(p, 'bs_eq', teq - nci); put(p, 'bs_nci', nci); put(p, 'bs_teq', teq); put(p, 'bs_tle', b['tle'])
    x = r.get('x') or {}
    if x.get('sh_issued') is not None and x.get('sh_treasury') is not None: put(p, 'bs_shares', x['sh_issued'] - x['sh_treasury'])
    put(p, 'debt_tot', std + N(b.get('ltd')))
    put(p, 'debt_st', N(b.get('std'))); put(p, 'debt_lt', N(b.get('cltd')) + N(b.get('ltd')))

def run():
    load()
    for p in periods():
        do_pl(p); do_bs(p)
    do_cf()
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: round(x[k], 1) if isinstance(x.get(k), float) else x.get(k) for k in
                  ('rev', 'ebit', 'ni', 'adj_ebit_pub', 'e_pub', 'sh_d', 'cf_cfo', 'cf_wc', 'bs_ta', 'bs_shares', 'debt_tot', 'em_pg')})
    print('\n'.join(LOG))
