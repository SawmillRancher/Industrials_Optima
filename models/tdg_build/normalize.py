"""Harmonise the extracted TransDigm data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m).

Basis policy:
  - Statement of income, EBITDA / EBITDA As Defined and adjusted-net-income bridges, balance sheet and cash flow: as originally
    reported in each period's own earnings release (income statement, non-GAAP) and 10-Q / 10-K (balance sheet, cash flow).
  - Segments (Power & Control, Airframe, Non-aviation) and net sales by end market: the latest filing that presents the period
    (the following fiscal year's 10-Q / 10-K comparative where one exists; FY2011 from the FY2013 10-K). This applies the FY2018
    reclassification of a business from Power & Control to Non-aviation to FY2017, and the FY2020 allocation of the FY2019
    Esterline businesses to the end markets, consistently. Where the recast basis also removed later-discontinued businesses
    (Esterline, FY2019), the difference to consolidated sales / EBITDA As Defined as originally reported is a derived
    'basis difference' row in the model.
  - Segment data is not published before FY2011 (one reportable segment) and end-market data not before FY2017 (annual) /
    Q1 FY2018 (quarterly).
Fourth quarters: income statement and non-GAAP from the Q4 release three-month column; segment, end-market and organic data
are derived as fiscal year (10-K) less the three quarters (noted). Cash flow: year-to-date statements; discrete quarters derived.
Units: thousands to fiscal 2019 and millions from fiscal 2020 in the source documents; stored in millions."""
import json, glob, os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))
FY0, FYQ0, FYL = 2006, 2013, 2026

def N(x): return x or 0.0
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def fyq(p):
    if p.isdigit(): return int(p), 4
    return int('20' + p[-2:]), int(p[1])

def periods():
    out = [str(y) for y in range(FY0, FYL + 1)]
    for y in range(FYQ0, FYL + 1):
        out += [qk(y, q) for q in (1, 2, 3, 4)]
    return out

def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v
def x_(p, k): return DATA.get(p, {}).get('x', {}).get(k)

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

# EBITDA As Defined adjusting-item categories -> model rows
MCAT = {'ACQ': 'acq', 'STEPUP': 'acq', 'SBC': 'sbc', 'DEBT': 'refin', 'GAIN': 'gain', 'OTHER': 'other', 'IMPAIR': 'other',
        'IPO': 'other', 'DISC': 'disc', 'AMORT': 'acq', 'TAX': 'other'}
OCATS = ['acq', 'sbc', 'refin', 'restr', 'gain', 'other', 'disc']
def item_cat(it):
    L = it['label'].lower()
    if 'covid' in L or '737 max' in L or 'restructuring' in L: return 'restr'
    if 'discontinued' in L: return 'disc'
    if 'ipo related option vesting' in L or 'deferred compensation' in L: return 'sbc'
    return MCAT.get(it['cat'], 'other')

def do_pl(p):
    r = REC.get(p)
    if not r: LOG.append(f'{p}: no record'); return
    i = r['is']; e = (r.get('ngaap') or {}).get('ebitda') or {}; a = (r.get('ngaap') or {}).get('adj') or {}
    rev = i['rev']; gp = i.get('gp', rev - i['cogs'])
    put(p, 'rev', rev); put(p, 'cogs', rev - gp); put(p, 'gp', gp)
    put(p, 'sga', i.get('sga')); put(p, 'amort_is', N(i.get('amort')))
    oth_op = sum(v for _, v in i.get('other_op_lines', [])) + N(i.get('refin_op'))
    put(p, 'oth_op', oth_op)
    put(p, 'oth_op_labels', '; '.join([f'{l} {v:,.1f}' for l, v in i.get('other_op_lines', [])] + ([f"Refinancing costs {i['refin_op']:,.1f}"] if i.get('refin_op') else [])))
    put(p, 'oi', i['oi'])
    put(p, 'int_net', i['int_net']); put(p, 'refin', N(i.get('refin')))
    below = N(i.get('other')) + N(i.get('gain')) + sum(v for _, v in i.get('below_oi_lines', []))
    put(p, 'oth_exp', below)
    put(p, 'ebt', i['ebt']); put(p, 'tax', i['tax'])
    ni_cont = i.get('ni_cont', i['ebt'] - i['tax'])
    put(p, 'ni_cont', ni_cont)
    put(p, 'disc', N(i.get('disc')))
    ni = i.get('ni', ni_cont + N(i.get('disc')))
    put(p, 'ni', ni)
    nci = -N(i.get('nci'))                        # income statement shows "Less: net income attributable to NCI" as a negative
    put(p, 'nci', nci); put(p, 'ni_td', ni - nci)
    div_part = -N(a.get('div_part'))              # dividends paid on participating securities (two-class method)
    put(p, 'div_part', div_part)
    put(p, 'eps_d', i.get('eps_d')); put(p, 'sh_d', i.get('sh_d')); put(p, 'sh_b', i.get('sh_b'))
    put(p, 'dps', i.get('dps'))
    put(p, 'sh_adj', a.get('sh_adj')); put(p, 'sh_part', a.get('sh_part')); put(p, 'sh_common', a.get('sh_common'))
    # EBITDA -> EBITDA As Defined (release)
    put(p, 'd_dda', e.get('dda')); put(p, 'ebitda_pub', e.get('ebitda_pub')); put(p, 'ebitda_ad_pub', e.get('ebitda_ad_pub'))
    put(p, 'ebitda_label', e.get('ebitda_label'))
    tot = {c: 0.0 for c in OCATS}; labs = {c: [] for c in OCATS}
    for it in e.get('items', []):
        c = item_cat(it); tot[c] += it['val']
        if abs(it['val']) > 1e-9: labs[c].append(f"{it['label']} {it['val']:,.1f}")
    for c in OCATS:
        put(p, f'oa_{c}', tot[c]); put(p, f'oa_{c}_lab', '; '.join(labs[c]))
    if e.get('realigned'): LOG.append(f'{p}: EBITDA rows realigned {e["realigned"]}')
    # adjusted net income (release)
    put(p, 'adj_start', a.get('start')); put(p, 'adj_start_label', a.get('start_label'))
    put(p, 'adj_gross', a.get('gross_adj')); put(p, 'adj_backlog', N(a.get('backlog_amort'))); put(p, 'adj_tax', a.get('tax_adj'))
    put(p, 'adj_ni_pub', a.get('adj_ni_pub')); put(p, 'adj_eps_pub', a.get('adj_eps_pub')); put(p, 'eps_div_equiv', a.get('eps_div_equiv'))
    # difference between the company's start line and continuing operations incl. NCI (start from income attributable to TD Group)
    if a.get('start') is not None: put(p, 'adj_start_diff', a['start'] - ni_cont)
    o = r.get('organic')
    if o and o.get('org_sales') is not None:
        put(p, 'org_sales', o['org_sales']); put(p, 'acq_sales', o.get('acq_sales', rev - o['org_sales']) if o.get('acq_sales') is not None else rev - o['org_sales'])

# ---------------------------------------------------------------- segments / end markets (latest filing presenting the period)
SEGK = ('pc', 'af', 'na', 'es')
EMK = ('pc_coem', 'pc_caft', 'pc_def', 'af_coem', 'af_caft', 'af_def', 'na', 'pc_est', 'af_est', 'es')
def seg_src(p):
    r = REC.get(p) or {}
    for k in ('seg_py', 'seg_py2', 'seg'):
        s = r.get(k)
        if s and any(s.get(f'{g}_ebitda') is not None for g in SEGK): return s, k
    return None, None
def em_src(p):
    r = REC.get(p) or {}
    for k in ('em_py', 'em_py2', 'em'):
        s = r.get(k)
        if s and s.get('pc_coem') is not None: return s, k
    return None, None

def seg_sales(s, em, g):
    if s.get(f'{g}_sales') is not None: return s[f'{g}_sales']
    if em is not None:
        if g == 'na': return em.get('na')
        if g == 'es': return em.get('es')
        if em.get(f'{g}_tot') is not None: return em[f'{g}_tot']
    return None

def do_seg_period(p):
    s, sk = seg_src(p); em, ek = em_src(p)
    if s:
        if sk != 'seg': put(p, 'seg_basis', 'recast (following year filing)')
        # segment sales for legacy formats sit in the end-market table of the same filing
        em_same = (REC.get(p) or {}).get({'seg_py': 'em_py', 'seg_py2': 'em_py2', 'seg': 'em'}[sk]) or {}
        for g in SEGK:
            v = seg_sales(s, em_same if em_same else em, g)
            if v is None and g != 'es' and em is not None: v = seg_sales({}, em, g)
            put(p, f'sg_{g}_rev', v); put(p, f'sg_{g}_eb', s.get(f'{g}_ebitda'))
        put(p, 'sg_corp', s.get('corp'))
    if em:
        if ek != 'em': put(p, 'em_basis', 'recast (following year filing)')
        for k in EMK: put(p, f'em_{k}', em.get(k))

def derive_q4(y, keys):
    """Q4 = fiscal year - Q1 - Q2 - Q3 for keys present in all four records (noted)."""
    a = str(y); qs = [qk(y, q) for q in (1, 2, 3)]
    for k in keys:
        va = x_(a, k); vq = [x_(q, k) for q in qs]
        if va is None or any(v is None for v in vq): continue
        if x_(qk(y, 4), k) is None:
            put(qk(y, 4), k, va - sum(vq))
            DATA[qk(y, 4)]['x'].setdefault('_q4_derived', []).append(k)

# ---------------------------------------------------------------- cash flow
CFK = ('ni', 'dep', 'amort', 'amort_debt', 'refin', 'gain', 'sbc', 'deferred_tax', 'cfo', 'capex', 'acq', 'divest', 'cfi',
       'stock_proc', 'dividends', 'buyback', 'cff', 'fx')
def cf_ytd(fy, q):
    p = str(fy) if q == 4 else qk(fy, q)
    r = REC.get(p)
    if not r or not r.get('cf'): return None
    c = r['cf']
    o = {k: N(c.get(k)) for k in CFK}
    o['beg'], o['end'] = c.get('beg'), c.get('end')
    return o

def cf_lines(c):
    o = {'cf_ni': c['ni'], 'cf_dda': c['dep'] + c['amort'], 'cf_amdebt': c['amort_debt'] + c['refin'], 'cf_sbc': c['sbc'],
         'cf_def': c['deferred_tax'], 'cf_gain': c['gain']}
    o['cf_wc'] = c['cfo'] - sum(o.values())
    o['cf_cfo'] = c['cfo']; o['cf_capex'] = c['capex']; o['cf_acq'] = c['acq']
    o['cf_oinv'] = c['cfi'] - c['capex'] - c['acq']; o['cf_cfi'] = c['cfi']
    o['cf_stock'] = c['stock_proc']; o['cf_div'] = c['dividends']; o['cf_bb'] = c['buyback']
    o['cf_ofin'] = c['cff'] - c['stock_proc'] - c['dividends'] - c['buyback']; o['cf_cff'] = c['cff']; o['cf_fx'] = c['fx']
    o['cf_net'] = c['cfo'] + c['cfi'] + c['cff'] + c['fx']
    return o

def do_cf():
    for y in range(FY0, FYL + 1):
        a = cf_ytd(y, 4)
        if not a: LOG.append(f'{y}: no annual CF'); continue
        for k, v in cf_lines(a).items(): put(str(y), k, v)
        put(str(y), 'cf_beg', a['beg']); put(str(y), 'cf_end', a['end'])
    for y in range(FYQ0, FYL + 1):
        prev = None
        for q in (1, 2, 3, 4):
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
    cash, rc = b['cash'], N(b.get('rcash'))
    put(p, 'bs_cash', cash); put(p, 'bs_rcash', rc); put(p, 'bs_ar', b['ar']); put(p, 'bs_inv', b['inv'])
    put(p, 'bs_oca', tca - cash - rc - b['ar'] - b['inv']); put(p, 'bs_tca', tca)
    put(p, 'bs_ppe', b['ppe']); put(p, 'bs_gw', b['gw']); put(p, 'bs_int', b['intang'])
    put(p, 'bs_onca', ta - tca - b['ppe'] - b['gw'] - b['intang']); put(p, 'bs_ta', ta)
    cltd, std = N(b.get('cltd')), N(b.get('std'))
    put(p, 'bs_cltd', cltd); put(p, 'bs_std', std); put(p, 'bs_ap', b['ap'])
    put(p, 'bs_ocl', b['tcl'] - cltd - std - b['ap']); put(p, 'bs_tcl', b['tcl'])
    ltd = N(b.get('ltd')); put(p, 'bs_ltd', ltd)
    tle = b['tle']; rnci = N(b.get('rnci')); nci = N(b.get('nci'))
    te = b.get('te', b.get('eq_td'))
    if b.get('eq_td') is not None and b.get('nci') is not None and abs(b['eq_td'] + nci - te) > 0.6: te = b['eq_td'] + nci
    eq_td = b.get('eq_td', te - nci)
    if b.get('eq_td') is None: eq_td = te - nci
    tl = tle - te - rnci
    put(p, 'bs_deftax', N(b.get('deftax'))); put(p, 'bs_oncl', tl - b['tcl'] - ltd - N(b.get('deftax'))); put(p, 'bs_tl', tl)
    put(p, 'bs_rnci', rnci); put(p, 'bs_eq', eq_td); put(p, 'bs_nci', te - eq_td); put(p, 'bs_teq', te); put(p, 'bs_tle', tle)
    put(p, 'debt_tot', cltd + std + ltd)
    si, st = b.get('shares_issued'), b.get('shares_treasury')
    if si is not None: put(p, 'bs_shares', si - N(st))

def apply_corrections():
    for c in MAN.get('corrections', []):
        put(c['period'], c['key'], c['value'])
        LOG.append(f"{c['period']} {c['key']}: correction -> {c['value']} ({c['reason'][:60]})")

def run():
    load()
    for p in periods():
        if p in REC:
            do_pl(p); do_bs(p); do_seg_period(p)
    for y in range(FYQ0, FYL + 1):
        # organic data for Q4 FY2017 / FY2019 not derived: the 10-K year is on the discontinued-operations basis, the quarters as first reported
        derive_q4(y, [f'sg_{g}_rev' for g in SEGK] + [f'sg_{g}_eb' for g in SEGK] + ['sg_corp'] + [f'em_{k}' for k in EMK] + ([] if y in (2017, 2019) else ['org_sales', 'acq_sales']))
    do_cf()
    apply_corrections()
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: round(x[k], 1) if isinstance(x.get(k), float) else x.get(k) for k in
                  ('rev', 'ni', 'ebitda_ad_pub', 'adj_eps_pub', 'sg_pc_rev', 'sg_es_rev', 'em_pc_coem', 'org_sales', 'cf_cfo', 'cf_wc', 'bs_ta', 'bs_shares', 'debt_tot')})
    print('\n'.join(LOG))
