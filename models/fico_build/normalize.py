"""Harmonise the extracted Fair Isaac data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m).

Basis: every period as originally reported in its own documents (release for the income statement, balance sheet, cash flow
and non-GAAP table; 10-Q / 10-K for the segment operating-income summary, interest split and revenue KPIs). FY2006-FY2012
annual figures come from the 10-K; FY2013+ annual statements from the Q4 release twelve-month column.
  - Q4 items not in the Q4 release (segment revenue / operating income, unallocated items, interest split, KPIs) = fiscal
    year (10-K) - nine months. The nine months come from the Q3 10-Q year-to-date block, or - when the 10-K re-presents the
    segments (FY2021 Scores / Software) - from the following year's Q3 10-Q prior-year year-to-date column.
  - Segments: Scores = 'Scoring Solutions' (FY2006-09, product-line segments; flagged legacy basis) / 'Scores' (FY2010+).
    Software = consolidated revenue - Scores (Strategy Machine Solutions + Professional Services + Analytic Software Tools to
    FY2009; Applications + Tools / Decision Management Software FY2010-Q3/21; Software from FY2021 10-K).
  - Revenue KPIs: B2B / B2C Scores and platform / non-platform software, first published in the FY2021 10-K (FY2019-21) and
    the FY2022 10-Qs (FY2021 quarter comparatives); each period from the first filing that presents it.
  - Non-GAAP: published from Q1 FY2013. FY2013-Q2/16 items were shown net of tax, so the model bridge uses the pre-tax
    items from the income statement / segment summary and derives the tax effect = published non-GAAP net income - net
    income - pre-tax items. FY2006-FY2012: no non-GAAP measures published (adjusted = GAAP; flagged).
Cash flow: releases give year-to-date statements; discrete quarters derived (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M).
"""
import json, glob, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json'))) if os.path.exists(os.path.join(BASE, 'manual_items.json')) else {}

def N(x): return x or 0.0
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def fyq(p):
    if p.isdigit(): return int(p), 4
    return int('20' + p[-2:]), int(p[1])

def periods():
    out = [str(y) for y in range(2006, 2026)]
    for y in range(2013, 2027):
        out += [qk(y, q) for q in (1, 2, 3, 4) if not (y == 2026 and q == 4)]
    return out

def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v

def x_(p, k): return DATA.get(p, {}).get('x', {}).get(k)

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

# ---------------------------------------------------------------- segment summary -> flat keys
SC_NAMES = ('Scores', 'Scoring Solutions')
LEG = {'Applications': 'app', 'Tools': 'tools', 'Decision Management Software': 'dms', 'Strategy Machine Solutions': 'sms',
       'Professional Services': 'pserv', 'Analytic Software Tools': 'tools', 'Software': None, 'Scores': None, 'Scoring Solutions': None}

def item_cat(lab):
    l = lab.lower()
    if 'share-based' in l or 'stock-based' in l: return 'sbc'
    if 'amortization' in l: return 'amort'
    if re.search(r'restructuring|impairment|acquisition', l): return 'restr'
    if re.search(r'gain|loss', l): return 'gain'
    return 'other'

def seg_flat(s):
    """{'sc_rev','sc_oi','sw_oi','corp','sbc','amort','restr','gain','other','opinc', legacy rev/oi} from a segment summary block."""
    if not s or s.get('opinc') is None: return None
    o = {'sbc': 0.0, 'amort': 0.0, 'restr': 0.0, 'gain': 0.0, 'other': 0.0}
    rev = dict(s.get('rev') or [])
    sw_oi = 0.0
    for name, v in s['segs']:
        if name in SC_NAMES:
            o['sc_oi'] = v
            if name in rev: o['sc_rev'] = rev[name]
        else:
            sw_oi += v
            lk = LEG.get(name)
            if lk:
                o[f'leg_{lk}_oi'] = v
                if name in rev: o[f'leg_{lk}_rev'] = rev[name]
    o['sw_oi'] = sw_oi
    o['corp'] = N(s.get('corp'))
    for lab, v in s['items']:
        c = item_cat(lab); o[c] += -v              # items shown as reductions of operating income -> cost positive (gains negative)
    o['opinc'] = s['opinc']
    o['segnames'] = '; '.join(n for n, _ in s['segs'])
    return o

def seg_diff(a, b):
    """a - b for numeric keys present in both."""
    if a is None or b is None or a.get('segnames') != b.get('segnames'): return None
    return {k: round(a[k] - b[k], 6) for k in a if k in b and isinstance(a[k], float)} | {'segnames': a['segnames']}

def seg_sum(blocks):
    if any(b is None for b in blocks) or len({b['segnames'] for b in blocks}) != 1: return None
    keys = set.intersection(*[set(k for k in b if isinstance(b[k], float)) for b in blocks])
    return {k: round(sum(b[k] for b in blocks), 6) for k in keys} | {'segnames': blocks[0]['segnames']}

def do_seg():
    for p in periods():
        r = REC.get(p) or {}
        fy, q = fyq(p)
        s = None
        if p.isdigit() or q < 4:
            s = seg_flat(r.get('seg'))
            if s and 'sc_rev' not in s and not p.isdigit() and q > 1:      # current-quarter revenue table missing: YTD - prior YTD
                ytd = seg_flat(r.get('seg_ytd')); prev = seg_flat((REC.get(qk(fy, q - 1)) or {}).get('seg_ytd' if q == 3 else 'seg'))
                if ytd and prev and 'sc_rev' in ytd and 'sc_rev' in prev:
                    s['sc_rev'] = round(ytd['sc_rev'] - prev['sc_rev'], 6); LOG.append(f'{p}: segment revenue = YTD - prior YTD')
                    for k in list(ytd):
                        if k.startswith('leg_') and k.endswith('_rev') and k in prev: s[k] = round(ytd[k] - prev[k], 6)
        else:
            fyrec = seg_flat((REC.get(str(fy)) or {}).get('seg'))
            nine = seg_flat((REC.get(qk(fy, 3)) or {}).get('seg_ytd'))
            s = seg_diff(fyrec, nine)
            src = 'FY (10-K) - 9M (Q3 10-Q)'
            if s is None:
                nine = seg_flat((REC.get(qk(fy + 1, 3)) or {}).get('seg_ytd_py'))
                s = seg_diff(fyrec, nine); src = 'FY (10-K) - 9M re-presented (following year Q3 10-Q prior-year column)'
            if s is None:
                s = seg_diff(fyrec, seg_sum([seg_flat((REC.get(qk(fy, k)) or {}).get('seg')) for k in (1, 2, 3)])); src = 'FY - (Q1 + Q2 + Q3)'
            if s is None: LOG.append(f'{p}: no segment derivation'); continue
            put(p, 'seg_src', src)
        if not s: LOG.append(f'{p}: no segment summary'); continue
        for k, v in s.items(): put(p, 's_' + k if k != 'segnames' else 'segnames', v)
        if s.get('sc_rev') is not None and x_(p, 'rev') is not None: put(p, 's_sw_rev', round(x_(p, 'rev') - s['sc_rev'], 6))

# ---------------------------------------------------------------- interest split
def int_flat(i):
    if not i: return None
    if i.get('int_net') is not None: net = -i['int_net']
    elif i.get('int_exp') is not None: net = -(i['int_exp'] + N(i.get('int_inc')))
    else: return None
    return {'int': net, 'oth': N(i.get('oth'))}

def do_int():
    for p in periods():
        r = REC.get(p) or {}
        fy, q = fyq(p)
        nonop = sum(v for _, v in (r.get('is') or {}).get('nonop', []) if v)
        if p.isdigit() and fy <= 2012:          # 10-K income statement lines
            ii = dict((l, v) for l, v in r['is']['nonop'])
            net = -(N(ii.get('Interest expense')) + N(ii.get('Interest income')))
            o = {'int': net, 'oth': round(nonop + net, 6)}
        elif p.isdigit() or q < 4:
            o = int_flat(r.get('int'))
        else:
            a = int_flat((REC.get(str(fy)) or {}).get('int'))
            ytd = int_flat((REC.get(qk(fy, 3)) or {}).get('int_ytd'))
            if ytd is None:
                parts = [int_flat((REC.get(qk(fy, k)) or {}).get('int')) for k in (1, 2, 3)]
                ytd = None if any(x is None for x in parts) else {k: sum(x[k] for x in parts) for k in ('int', 'oth')}
            o = None if a is None or ytd is None else {k: a[k] - ytd[k] for k in a}
        if o is None: LOG.append(f'{p}: no interest split'); continue
        # the split must reproduce the income-statement non-operating total
        if abs(-o['int'] + o['oth'] - nonop) > 0.002: LOG.append(f'{p}: interest split {-o["int"] + o["oth"]:.3f} vs IS non-operating {nonop:.3f}')
        put(p, 'int_net', o['int']); put(p, 'oth_inc', round(nonop + o['int'], 6))

# ---------------------------------------------------------------- KPIs (B2B / B2C Scores; platform / non-platform software)
KK = ('b2b', 'b2c', 'plat', 'nonplat')
def do_kpi():
    got = {}
    def setk(p, k, v, src):
        if v is None or (p, k) in got: return
        got[(p, k)] = src; put(p, f'k_{k}', v)
    for y in range(2019, 2026):
        for src_y, col in ((y, 'cur'), (y + 1, 'py'), (y + 2, 'py2')):
            k_ = (REC.get(str(src_y)) or {}).get('kpi') or {}
            for k in KK: setk(str(y), k, k_.get(f'{k}_{col}'), f'{src_y} 10-K')
    for y in range(2021, 2027):
        for q in (1, 2, 3):
            p = qk(y, q)
            for src, col in ((p, 'cur'), (qk(y + 1, q), 'py')):
                k_ = (REC.get(src) or {}).get('kpi') or {}
                for k in KK: setk(p, k, k_.get(f'{k}_{col}'), src)
        if y <= 2025:
            p = qk(y, 4)
            for k in KK:
                fyv = x_(str(y), f'k_{k}')
                nine = ((REC.get(qk(y, 3)) or {}).get('kpi') or {}).get(f'{k}_ytd')
                if nine is None: nine = ((REC.get(qk(y + 1, 3)) or {}).get('kpi') or {}).get(f'{k}_ytd_py')
                if fyv is not None and nine is not None: setk(p, k, round(fyv - nine, 6), 'FY - 9M')

# ---------------------------------------------------------------- P&L
NG_CAT = [(r'cost-method investment', 'NONOP'), (r'share-based|stock-based', 'SBC'), (r'amortization', 'AMORT'), (r'restructuring|impairment|acquisition', 'RESTR'),
          (r'gain', 'GAIN'), (r'income tax adjustments', 'TAX'), (r'excess tax benefit', 'ETB'),
          (r'valuation allowance|tax reserves|foreign tax credit|tax cuts', 'TAXD')]
def ng_cat(lab):
    for p, c in NG_CAT:
        if re.search(p, lab, re.I): return c
    return 'OTHER'

def do_pl(p):
    r = REC.get(p)
    if not r or not r.get('is'): LOG.append(f'{p}: no income statement'); return
    fy, q = fyq(p)
    i = r['is']
    put(p, 'rev', i['rev'])
    rl = {l: v for l, v in i['rev_lines']}
    if 'On-premises and SaaS software' in rl:
        put(p, 'rev_saas', rl['On-premises and SaaS software']); put(p, 'rev_ps', rl.get('Professional services')); put(p, 'rev_scores_is', rl.get('Scores'))
    put(p, 'rev_lines', '; '.join(f'{l} {v:,.1f}' for l, v in i['rev_lines']))
    put(p, 'cogs', i.get('cogs')); put(p, 'rd', i.get('rd')); put(p, 'sga', i.get('sga'))
    put(p, 'amort_is', N(i.get('amort'))); put(p, 'restr_is', N(i.get('restr')))
    put(p, 'oth_op', sum(v for _, v in i['other_op']))
    if i['other_op']: put(p, 'oth_op_lab', '; '.join(f'{l} {v:,.1f}' for l, v in i['other_op']))
    put(p, 'opinc', i['opinc']); put(p, 'nonop', sum(v for _, v in i['nonop'] if v))
    put(p, 'ebt', i['ebt']); put(p, 'tax', i.get('tax')); put(p, 'disc', N(i.get('disc'))); put(p, 'ni', i['ni'])
    put(p, 'cont', i['ni'] - N(i.get('disc')))
    for k in ('eps_b', 'eps_d', 'eps_d_cont', 'sh_b', 'sh_d', 'dps'): put(p, k, i.get(k))
    # non-GAAP (published from Q1 FY2013)
    g = r.get('ng')
    published = fy >= 2013
    put(p, 'ng_basis', 'published' if published and g else 'none')
    if published and g and g.get('ni_pub') is not None:
        put(p, 'ng_ni_pub', g['ni_pub']); put(p, 'ng_eps_pub', g['eps_pub'])
        net_fmt = any('net of tax' in l for l, _ in g['items'])
        put(p, 'ng_net_fmt', 1 if net_fmt else 0)
        cats = {}
        for l, v in g['items']:
            c = ng_cat(l); cats[c] = cats.get(c, 0.0) + N(v)
        for c, v in cats.items(): put(p, f'ng_co_{c.lower()}', v)
        put(p, 'ng_labels', '; '.join(f'{l} {v:,.1f}' for l, v in g['items']))
        if g.get('fcf_pub') is not None: put(p, 'fcf_pub', g['fcf_pub'])
        fl = dict((l, v) for l, v in (g.get('fcf_lines') or []))
        put(p, 'fcf_div', fl.get('Dividends paid', 0.0))      # FY2013-Q2/17 definition also deducted dividends paid

def do_ng_items():
    """pre-tax adjusting items used in the model bridge = the unallocated items of the segment summary (SBC, amortization,
    restructuring / acquisition / impairment, gains on product-line and business sales); 'other' = realized gain on a
    cost-method investment (non-operating, FY2018-19, company item only)."""
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        if 'rev' not in x: continue
        for k in ('sbc', 'amort', 'restr', 'gain'): put(p, f'adj_{k}', x.get(f's_{k}'))
        if x.get('ng_basis') == 'published':
            # non-operating items the company adjusted (realized gain on cost-method investment, FY2018-19)
            put(p, 'adj_nonop', N(x.get('ng_co_nonop')))

# ---------------------------------------------------------------- cash flow
def cf_ytd(fy, q):
    p = str(fy) if q == 4 else qk(fy, q)
    r = REC.get(p)
    if not r or not r.get('cf'): return None
    c = r['cf']
    o = {k: N(c.get(k)) for k in ('ni', 'dda', 'sbc', 'cfo', 'capex', 'capsw', 'acq', 'divest', 'cfi', 'bb', 'div', 'stock', 'taxw', 'debt', 'cff', 'fx')}
    o['beg'], o['end'] = c.get('beg'), c.get('end')
    return o

def cf_lines(c):
    o = {'cf_ni': c['ni'], 'cf_dda': c['dda'], 'cf_sbc': c['sbc']}
    o['cf_wc'] = c['cfo'] - c['ni'] - c['dda'] - c['sbc']
    o['cf_cfo'] = c['cfo']; o['cf_capex'] = c['capex']; o['cf_capsw'] = c['capsw']; o['cf_acq'] = c['acq']; o['cf_divest'] = c['divest']
    o['cf_oinv'] = c['cfi'] - c['capex'] - c['capsw'] - c['acq'] - c['divest']; o['cf_cfi'] = c['cfi']
    o['cf_bb'] = c['bb']; o['cf_div'] = c['div']; o['cf_stock'] = c['stock']; o['cf_taxw'] = c['taxw']; o['cf_debt'] = c['debt']
    o['cf_ofin'] = c['cff'] - c['bb'] - c['div'] - c['stock'] - c['taxw'] - c['debt']; o['cf_cff'] = c['cff']; o['cf_fx'] = c['fx']
    o['cf_net'] = c['cfo'] + c['cfi'] + c['cff'] + c['fx']
    return o

def do_cf():
    for y in range(2006, 2026):
        p = str(y); a = cf_ytd(y, 4)
        if not a: LOG.append(f'{p}: no annual CF'); continue
        for k, v in cf_lines(a).items(): put(p, k, v)
        put(p, 'cf_beg', a['beg']); put(p, 'cf_end', a['end'])
    for y in range(2013, 2027):
        prev = None
        for q in (1, 2, 3, 4):
            if y == 2026 and q == 4: break
            p = qk(y, q)
            cur = cf_ytd(y, q)
            if cur is None: LOG.append(f'{p}: no YTD CF'); prev = None; continue
            lc = cf_lines(cur)
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
    cash, mkc, mkl = b['cash'], N(b.get('mkt_cur')), N(b.get('mkt_lt'))
    put(p, 'bs_cash', cash); put(p, 'bs_mkt', mkc + mkl); put(p, 'bs_ar', b['ar']); put(p, 'bs_oca', tca - cash - mkc - b['ar'])
    put(p, 'bs_tca', tca); put(p, 'bs_ppe', b['ppe']); put(p, 'bs_gw', b['gw'])
    put(p, 'bs_onca', ta - tca - b['ppe'] - b['gw'] - mkl); put(p, 'bs_ta', ta)
    std = N(b.get('std'))
    put(p, 'bs_ap', b['ap']); put(p, 'bs_accomp', N(b.get('accomp'))); put(p, 'bs_defrev', N(b.get('defrev'))); put(p, 'bs_std', std)
    put(p, 'bs_ocl', b['tcl'] - b['ap'] - N(b.get('accomp')) - N(b.get('defrev')) - std); put(p, 'bs_tcl', b['tcl'])
    ltd = N(b.get('ltd'))
    tl = b.get('tl') if b.get('tl') is not None else b['tle'] - b['eq']
    put(p, 'bs_ltd', ltd); put(p, 'bs_ol', tl - b['tcl'] - ltd); put(p, 'bs_tl', tl)
    put(p, 'bs_eq', b['eq']); put(p, 'bs_tle', b['tle'])
    put(p, 'debt_tot', std + ltd)

def do_shares():
    """shares outstanding at period end (XBRL dei / us-gaap CommonStockSharesOutstanding, as first filed) where available."""
    f = os.path.join(BASE, 'data', '_xbrl.json')
    if not os.path.exists(f): return
    xb = json.load(open(f))
    for p, v in (xb.get('shares_out') or {}).items(): put(p, 'bs_shares', v)

def run():
    load()
    for p in periods():
        do_pl(p); do_bs(p)
    do_seg(); do_int(); do_kpi(); do_ng_items(); do_cf(); do_shares()
    # debt components at 30-Jun-2026 (Q3 FY26 10-Q Note 6): term loan and revolver at face; notes = total carrying - both
    d = MAN.get('debt_2026_06_30', {})
    if d: put('Q3-26', 'debt_tl', d['term_loan']['balance']); put('Q3-26', 'debt_rev', d['revolver']['drawn'])
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: round(x[k], 1) if isinstance(x.get(k), float) else x.get(k) for k in
                  ('rev', 's_sc_rev', 's_sc_oi', 's_sw_oi', 's_corp', 's_sbc', 'int_net', 'oth_inc', 'ni', 'ng_ni_pub', 'cf_cfo', 'cf_wc', 'bs_ta', 'k_b2b', 'k_plat')})
    print('\n'.join(LOG))
