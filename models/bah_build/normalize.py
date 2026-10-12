"""Harmonise the extracted Booz Allen data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m).

Basis: every period as originally reported in its own earnings release (Q4 / fiscal-year release for the annual columns, each
quarter's release for the quarterly columns). Exceptions:
  - Revenue by customer: 10-Q / 10-K revenue note as filed for the period (FY2017-18 from the FY2019 10-K comparatives, the first
    filing that presents them; Q4 = fiscal year - nine months). National Security = Defense + Intelligence; Civil & Commercial =
    Civil + Global Commercial (Global Commercial reported separately to FY2024, inside Civil from FY2025).
  - Weighted shares and the two-class earnings for diluted EPS: XBRL company facts (as first filed); Q4 diluted shares from the release.
  - Deferred income taxes in the quarterly cash flow: XBRL (the quarterly releases fold them into working capital).
Cash flow: releases give year-to-date statements; discrete quarters derived (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M).
Adjusting items: three company bridges, each rebuilt from its own release table (adjusted operating income, published to Q3 FY2025;
adjusted EBITDA; adjusted net income / EPS) with the items mapped to model categories.
"""
import json, glob, os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))
OCATS = ['acq', 'restr', 'legal', 'covid', 'sbc', 'fin', 'other']          # operating items (inside operating income)
CATMAP = {'ACQ': 'acq', 'RESTR': 'restr', 'LEGAL': 'legal', 'COVID': 'covid', 'SBC': 'sbc', 'OTHER': 'other'}

def N(x): return x or 0.0
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def fyq(p):
    if p.isdigit(): return int(p), 4
    return int('20' + p[-2:]), int(p[1])

def periods():
    out = [str(y) for y in range(2012, 2027)]
    for y in range(2022, 2028):
        out += [qk(y, q) for q in (1, 2, 3, 4) if not (y == 2027 and q > 1)]
    return out

def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

def op_cat(label, cat):
    """model category of an operating adjusting item (inside operating income)."""
    if cat == 'DEBT': return 'fin'                      # financing transaction costs (in G&A)
    return CATMAP.get(cat, 'other')

def do_pl(p):
    r = REC.get(p)
    if not r: LOG.append(f'{p}: no record'); return
    i, n, x = r['is'], r['ngaap'], r.get('x') or {}
    rev = i['rev']
    put(p, 'rev', rev); put(p, 'cost_rev', i['cost_rev']); put(p, 'bill', i['bill']); put(p, 'ga', i['ga']); put(p, 'da', i['da'])
    put(p, 'restr', N(i.get('restr')))
    known = i['cost_rev'] + i['bill'] + i['ga'] + i['da'] + N(i.get('restr'))
    put(p, 'oth_op', round(i['tot_costs'] - known, 6))
    put(p, 'oi', i['oi']); put(p, 'int_exp', i['int_exp']); put(p, 'oth_inc', i['oth'])
    put(p, 'ebt', i['ebt']); put(p, 'tax', i['tax']); put(p, 'ni', i['ni'])
    # NCI income: net income - net income attributable to common stockholders (the release sign of the NCI line varies by year)
    nci = round(i['ni'] - i['ni_common'], 6) if i.get('ni_common') is not None else -N(i.get('nci'))
    put(p, 'nci', nci)
    put(p, 'ni_c', i.get('ni_common', i['ni'] - nci))
    put(p, 'eps_b', i.get('eps_b')); put(p, 'eps_d', i.get('eps_d'))
    put(p, 'sh_b', i.get('sh_b')); put(p, 'sh_d', i.get('sh_d'))
    if i.get('earn_dil') is not None:
        put(p, 'earn_dil', i['earn_dil']); put(p, 'alloc', round(DATA[p]['x']['ni_c'] - i['earn_dil'], 6))
    put(p, 'dps', x.get('x_dps', i.get('dps')))
    put(p, 'rev_xb', rev - i['bill'])
    # ---------------- non-GAAP
    put(p, 'rev_xb_pub', n.get('rev_xb_pub'))
    put(p, 'ebitda_pub', n.get('ebitda_pub')); put(p, 'adj_ebitda_pub', n.get('adj_ebitda_pub'))
    eb = n.get('ebitda_bridge') or {}
    put(p, 'ebitda_start', eb.get('start'))
    # start-line basis: the company bridges start from net income attributable to common stockholders or from consolidated net income
    if eb.get('start') is not None: put(p, 'eb_nci', round(eb['start'] - DATA[p]['x']['ni_c'], 6))
    tot = {c: 0.0 for c in OCATS}; lab = {c: [] for c in OCATS}
    for l, v, c in (n.get('adj_ebitda') or {}).get('items', []):
        k = op_cat(l, c); tot[k] += v
        if abs(v) > 1e-9: lab[k].append(f'{l} {v:,.1f}')
    for c in OCATS:
        put(p, f'eb_{c}', tot[c]); put(p, f'eb_{c}_lab', '; '.join(lab[c]))
    # adjusted operating income (company measure, to Q3 FY2025)
    ao = n.get('adj_oi')
    if ao and ao.get('total') is not None:
        put(p, 'adj_oi_pub', ao['total'])
        put(p, 'ao_amort', sum(v for l, v, c in ao['items'] if c == 'AMORT'))
        put(p, 'ao_op', sum(v for l, v, c in ao['items'] if c != 'AMORT'))
    # adjusted net income
    an = n.get('adj_ni') or {}
    if an.get('total') is not None:
        a = {'amort': 0.0, 'nonop': 0.0, 'tax': 0.0, 'taxd': 0.0, 'op': 0.0}; labs = {k: [] for k in a}
        for l, v, c in an['items']:
            k = 'amort' if c == 'AMORT' else 'tax' if c == 'TAX' else 'taxd' if c == 'TAXD' else \
                'nonop' if (c in ('GAIN',) or (c == 'DEBT' and 'financing transaction' not in l.lower())) else 'op'
            a[k] += v
            if abs(v) > 1e-9: labs[k].append(f'{l} {v:,.1f}')
        for k, v in a.items():
            put(p, f'an_{k}', v); put(p, f'an_{k}_lab', '; '.join(labs[k]))
        put(p, 'an_start', an['start']); put(p, 'an_nci', round(an['start'] - DATA[p]['x']['ni_c'], 6))
        put(p, 'adj_ni_pub', an['total']); put(p, 'adj_eps_pub', n.get('adj_eps_pub')); put(p, 'adj_sh', n.get('adj_sh'))
    put(p, 'fcf_pub', n.get('fcf_pub'))
    put(p, 'twoclass_note', n.get('twoclass_note'))
    # ---------------- revenue by customer
    c = dict(r.get('cust') or {})
    if c.get('civ') is None and c.get('def') is not None and c.get('cc') is not None:
        c['civ'] = c['cc']          # FY2026 10-K: Civil and Commercial reported as one customer type
    for k in ('def', 'intel', 'civ', 'com', 'ns', 'cc'):
        put(p, f'c_{k}', c.get(k))
    # ---------------- operating data
    for k, v in (r.get('op') or {}).items(): put(p, k, v)

# ---------------------------------------------------------------- cash flow
CFK = ('ni', 'da', 'sbc', 'deftax', 'cfo', 'capex', 'acq', 'cfi', 'iss', 'opt', 'bb', 'div', 'cff')
def cf_ytd(p):
    r = REC.get(p)
    if not r or not r.get('cf'): return None
    c = r['cf']; x = r.get('x') or {}
    o = {k: N(c.get(k)) for k in CFK}
    if c.get('deftax') is None: o['deftax'] = N(x.get('x_deftax'))
    if c.get('sbc') is None: o['sbc'] = N(x.get('x_sbc'))
    o['beg'], o['end'] = c.get('beg'), c.get('end')
    return o

def cf_lines(c):
    o = {'cf_ni': c['ni'], 'cf_dda': c['da'], 'cf_sbc': c['sbc'], 'cf_def': c['deftax']}
    o['cf_wc'] = c['cfo'] - c['ni'] - c['da'] - c['sbc'] - c['deftax']
    o['cf_cfo'] = c['cfo']; o['cf_capex'] = c['capex']; o['cf_acq'] = c['acq']
    o['cf_oinv'] = c['cfi'] - c['capex'] - c['acq']; o['cf_cfi'] = c['cfi']
    o['cf_bb'] = c['bb']; o['cf_div'] = c['div']; o['cf_stock'] = c['iss'] + c['opt']
    o['cf_ofin'] = c['cff'] - c['bb'] - c['div'] - c['iss'] - c['opt']; o['cf_cff'] = c['cff']
    o['cf_net'] = c['cfo'] + c['cfi'] + c['cff']
    return o

def x_(p, k): return DATA.get(p, {}).get('x', {}).get(k)

def do_cf():
    for y in range(2012, 2027):
        p = str(y); a = cf_ytd(p)
        if not a: LOG.append(f'{p}: no annual CF'); continue
        for k, v in cf_lines(a).items(): put(p, k, v)
        put(p, 'cf_beg', a['beg']); put(p, 'cf_end', a['end'])
    for y in range(2022, 2028):
        prev = None
        for q in (1, 2, 3, 4):
            if y == 2027 and q > 1: break
            p = qk(y, q)
            cur = cf_ytd(p)
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
    put(p, 'bs_cash', b['cash']); put(p, 'bs_ar', b['ar']); put(p, 'bs_oca', tca - b['cash'] - b['ar']); put(p, 'bs_tca', tca)
    put(p, 'bs_ppe', b['ppe']); put(p, 'bs_rou', N(b.get('rou'))); put(p, 'bs_int', b['intang']); put(p, 'bs_gw', b['gw'])
    put(p, 'bs_onca', ta - tca - b['ppe'] - N(b.get('rou')) - b['intang'] - b['gw']); put(p, 'bs_ta', ta)
    put(p, 'bs_std', b['cltd']); put(p, 'bs_ap', b['ap']); put(p, 'bs_acc', b['acc_comp'])
    put(p, 'bs_ocl', b['tcl'] - b['cltd'] - b['ap'] - b['acc_comp']); put(p, 'bs_tcl', b['tcl'])
    put(p, 'bs_ltd', b['ltd']); put(p, 'bs_lease', N(b.get('lease_lt')))
    put(p, 'bs_ol', b['tl'] - b['tcl'] - b['ltd'] - N(b.get('lease_lt'))); put(p, 'bs_tl', b['tl'])
    teq = b['tle'] - b['tl']
    eq = b.get('eq', teq)
    put(p, 'bs_eq', eq); put(p, 'bs_nci', round(teq - eq, 6)); put(p, 'bs_teq', teq); put(p, 'bs_tle', b['tle'])
    x = r.get('x') or {}
    put(p, 'bs_shares', x.get('x_sh_out'))
    put(p, 'debt_tot', b['cltd'] + b['ltd'])

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
                  ('rev', 'oi', 'ni_c', 'alloc', 'adj_ebitda_pub', 'adj_eps_pub', 'cf_cfo', 'cf_wc', 'bs_ta', 'c_ns', 'c_cc', 'bl_total')})
    print('\n'.join(LOG))
