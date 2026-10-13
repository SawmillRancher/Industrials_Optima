"""Harmonise the extracted RBC Bearings data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m).

Basis: every period as originally reported (earnings release for quarters, 10-K for fiscal years). The FY2022 10-K/A (5-Aug-2022)
restated FY2020-FY2022 and their quarters for stock-based compensation that should have been expensed earlier (SG&A); the restated
figures are kept as memo keys (*_rs) and are not recast into the main lines.
Segments:
  - Aerospace & Defense / Industrial (from the Q3 FY22 release, after the Dodge acquisition): external sales from the releases,
    segment gross margin / SG&A / operating income from the 10-Q / 10-K segment note (Q4 = fiscal year - nine months). Periods before
    Q3 FY22 take the re-presented comparatives of the following year's documents where published (FY2021, Q3 FY21 - Q2 FY22);
    Q1-Q2 FY21 and earlier were never re-presented and stay blank.
  - Legacy segments (Roller / Plain / Ball / Other, 'Other' renamed Engineered Products from FY2016) through Q2 FY22: memo keys.
Adjusted measures (company definitions, in force in each period):
  - Adjusted operating income / gross margin: release reconciliations (FY2006+; nothing adjusted in FY2012 or Q1 FY15 - the
    releases show GAAP only, so adjusted = GAAP there).
  - Adjusted net income / EPS: FY2006 - Q1 FY23 'old' definition (GAAP net income + items, after tax, + discrete tax); from Q2 FY23
    the current definition, which also adds back M&A-related amortization, stock compensation and amortization of deferred finance
    fees (pre-tax) less their tax effect. The re-presented current-definition figures for Q1 FY22 - Q1 FY23 (next year's releases;
    restated GAAP base) are memo keys (e_pub_cur).
  - Adjusted EBITDA = operating income + D&A + stock compensation + operating adjusting items (published as 'adjusted operating income
    plus depreciation / amortization plus incentive stock compensation' from Q2 FY16, as Adjusted EBITDA from Q3 FY22).
Cash flow: 10-Q / 10-K statements are year to date; discrete quarters derived (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M)."""
import json, glob, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))
FY0, FYQ0, FYC = 2006, 2013, 2027

def N(x): return x or 0.0
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def fyq(p):
    if p.isdigit(): return int(p), 4
    return int('20' + p[-2:]), int(p[1])

def periods():
    out = [str(y) for y in range(FY0, FYC)]
    for y in range(FYQ0, FYC + 1):
        out += [qk(y, q) for q in (1, 2, 3, 4) if not (y == FYC and q > 1)]
    return out

def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v
def x_(p, k): return DATA.get(p, {}).get('x', {}).get(k)

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

OCAT = {'RESTR': 'restr', 'ACQ': 'acq', 'STEPUP': 'stepup', 'LEGAL': 'legal', 'GAIN': 'gain', 'IMPAIR': 'other', 'OTHER': 'other',
        'SBC': 'sbc', 'AMORT': 'other', 'FX': 'other', 'DEBT': 'other', 'TAX': 'other', 'PREF': 'other'}
OCATS = ['restr', 'acq', 'stepup', 'legal', 'gain', 'sbc', 'other']

# ---------------------------------------------------------------- statement of operations + non-GAAP
def do_pl(p):
    r = REC.get(p)
    if not r or not r.get('is'): LOG.append(f'{p}: no statement of operations'); return
    fy, q = fyq(p); i = r['is']
    for k in ('rev', 'cogs', 'gp', 'sga', 'oth', 'oi', 'ebt', 'tax', 'ni', 'eps_b', 'eps_d', 'sh_b', 'sh_d'):
        put(p, k, i.get(k))
    put(p, 'int', N(i.get('int'))); put(p, 'loe', N(i.get('loe'))); put(p, 'onop', N(i.get('onop')))
    pref = abs(N(i.get('pref'))) + abs(N(i.get('pref_part')))
    put(p, 'pref', pref); put(p, 'ni_c', i['ni'] - pref)
    put(p, 'dps', N(i.get('dps')))
    ng = r.get('ng') or {}
    # operating items (pre-tax) from the operating-income reconciliation
    oi = ng.get('oi'); tot = {c: 0.0 for c in OCATS}; lab = {c: [] for c in OCATS}
    if oi:
        for l, v, c in oi['items']:
            cc = OCAT.get(c, 'other'); tot[cc] += v
            if v: lab[cc].append(f'{l} {v:,.1f}')
        put(p, 'adj_oi_pub', oi['adj'])
    elif not ng.get('ni'):
        put(p, 'adj_oi_pub', i['oi']); put(p, 'adj_none', 1)          # no reconciliation published: adjusted = GAAP
    for c in OCATS:
        put(p, f'oa_{c}', tot[c]); put(p, f'oa_{c}_lab', '; '.join(lab[c]))
    gm = ng.get('gm')
    put(p, 'ga_tot', sum(v for _, v, _ in gm['items']) if gm else 0.0)
    if gm: put(p, 'adj_gm_pub', gm['adj'])
    # net income -> adjusted net income (definition in force)
    ni = ng.get('ni'); cur = None
    if ni:
        cats = [c for _, _, c in ni['items']]
        cur = 'AMORT' in cats
        put(p, 'e_def', 'current' if cur else 'old')
        op_lab = {l.lower() for l, _, _ in (oi or {}).get('items', [])}
        e = dict(amort=0.0, sbc=0.0, dff=0.0, oth=0.0, taxpub=0.0); olab = []
        for l, v, c in ni['items']:
            ll = l.lower()
            if c == 'AMORT': e['amort'] += v
            elif c == 'SBC' and cur: e['sbc'] += v
            elif c == 'DEBT' and 'deferred finance' in ll: e['dff'] += v
            elif c == 'TAX': e['taxpub'] += v
            elif oi and (ll in op_lab or c in ('RESTR', 'ACQ', 'STEPUP', 'LEGAL', 'SBC')) and c not in ('FX', 'DEBT', 'PREF'):
                continue                                              # operating item: taken pre-tax from the operating reconciliation
            elif c == 'PREF': continue
            else:
                e['oth'] += v
                if v: olab.append(f'{l} {v:,.2f}')
        if cur:                                                   # published only under the current definition
            put(p, 'ea_amort', e['amort']); put(p, 'ea_sbc', e['sbc']); put(p, 'ea_dff', e['dff'])
        put(p, 'ea_oth', e['oth'])
        put(p, 'ea_oth_lab', '; '.join(olab))
        put(p, 'adj_ni_pub', ni['adj'])
        put(p, 'adj_pref', abs(N(ni.get('pref'))))
        put(p, 'adj_nic_pub', ni.get('adj_c', ni['adj'] - abs(N(ni.get('pref')))))
        put(p, 'e_pub', ni.get('eps_d')); put(p, 'e_sh', ni.get('sh_d', i.get('sh_d')))
        put(p, 'e_lab', '; '.join(f'{l} {v:,.2f}' for l, v, _ in ni['items'] if v))
    elif x_(p, 'adj_none'):
        put(p, 'e_def', 'none'); put(p, 'adj_ni_pub', i['ni']); put(p, 'adj_nic_pub', i['ni'] - pref); put(p, 'adj_pref', pref)
        put(p, 'e_sh', i.get('sh_d'))
        put(p, 'ea_oth', 0.0)
    # old-definition adjusted EPS as originally published, and the current definition where re-presented (memo)
    if ni and not cur: put(p, 'e_pub_old', ni.get('eps_d'))
    new = ng.get('new'); pyng = ((r.get('py') or {}).get('ng') or {})
    if cur: put(p, 'e_pub_cur', ni.get('eps_d'))
    elif new: put(p, 'e_pub_cur', new.get('eps_d'))
    elif (pyng.get('new') or {}).get('eps_d') is not None: put(p, 'e_pub_cur', pyng['new']['eps_d'])
    elif pyng.get('ni') and 'AMORT' in [c for _, _, c in pyng['ni']['items']]: put(p, 'e_pub_cur', pyng['ni'].get('eps_d'))
    # EBITDA (company figures)
    put(p, 'ebitda_pub', ng.get('ebitda')); put(p, 'adj_ebitda_pub', ng.get('adj_ebitda'))
    if ng.get('adj_ebitda') is None and ng.get('proxy_ebitda') is not None: put(p, 'adj_ebitda_pub', ng['proxy_ebitda']); put(p, 'adj_ebitda_proxy', 1)
    sel = ng.get('sel') or {}
    put(p, 'dda_rel', sel.get('dda')); put(p, 'backlog', sel.get('backlog', ng.get('backlog_text')))
    if ng.get('outlook'): put(p, 'outlook', ng['outlook'])
    # segments: current basis (Aerospace & Defense / Industrial) and legacy
    ss = ng.get('seg_sales') or {}
    pss = ((r.get('py') or {}).get('seg_sales') or {})
    if 'aero' in ss: put(p, 's_aero', ss['aero']); put(p, 's_ind', ss['ind'])
    elif 'aero' in pss:
        put(p, 's_aero', pss['aero']); put(p, 's_ind', pss['ind']); put(p, 's_recast', 1)
    for k in ('plain', 'roller', 'ball', 'other', 'eng'):
        v = ss.get(k)
        if v is None and p == '2006': v = ((r.get('segn') or {}).get('sales') or {}).get(k)
        if v is not None: put(p, 'l_' + ('other' if k == 'eng' else k), v)

def segnote(p):
    """segment gross margin / SG&A / operating income (current basis) for period p; Q4 = fiscal year - nine months."""
    fy, q = fyq(p)
    def get(rec, key='segn', py=False):
        if not rec: return None
        d = ((rec.get('py') or {}).get(key) if py else rec.get(key))
        return d if d and 'aero' in (d.get('sales') or {}) else None
    if q < 4 or p.isdigit():
        own = get(REC.get(p)); src = own or get(REC.get(p), py=True)
        return src, (own is None and src is not None)
    fyd = get(REC.get(str(fy))) or get(REC.get(str(fy)), py=True)
    q3 = get(REC.get(qk(fy, 3)), 'segn_ytd') or get(REC.get(qk(fy, 3)), 'segn_ytd', py=True)
    if not fyd or not q3: return None, False
    out = {h: {s: fyd[h][s] - q3.get(h, {}).get(s, 0.0) for s in fyd[h]} for h in fyd if h in q3}
    return out, True

def do_seg(p):
    d, derived = segnote(p)
    if not d: return
    for h, k in (('gm', 'gm'), ('sga', 'sga'), ('oi', 'soi')):
        if derived and h != 'gm' and not fyq(p)[1] == 4: continue      # re-presented SG&A / OI carry the 10-K/A stock-comp restatement
        for s in ('aero', 'ind', 'corp'):
            v = (d.get(h) or {}).get(s)
            if v is not None: put(p, f'{k}_{s}', v)
    if x_(p, 's_aero') is None and d.get('sales'):
        put(p, 's_aero', d['sales']['aero']); put(p, 's_ind', d['sales']['ind']); put(p, 's_recast', 1)

# ---------------------------------------------------------------- cash flow
FIN_EQ = r'proceeds from (the )?(sale|issuance) of (common |preferred |mandatory )?|initial public offering|exercise of|proceeds from sale of stock|issuance of (common|preferred|mandatory)'
FIN_BB = r'^(repurchase|purchase of treasury|tax withholding|shares withheld|payments? (for|of) (taxes|employee taxes))'
FIN_DIV = r'dividend'

def cf_ytd(fy, q):
    p = str(fy) if q == 4 else qk(fy, q)
    r = REC.get(p)
    if not r or not r.get('cf'): return None
    c = r['cf']; raw = c['lines_raw']
    labs = [l for l, _ in raw]
    def idx(pat):
        for j, l in enumerate(labs):
            if re.search(pat, l, re.I): return j
        return None
    jo, ji, jf = idx(r'^Net cash[^|]*operating'), idx(r'^Net cash[^|]*investing'), idx(r'^Net cash[^|]*financing')
    o = {k: N(c.get(k)) for k in ('ni', 'deftax', 'cfo', 'capex', 'acq', 'cfi', 'cff', 'fx', 'net')}
    o['beg'], o['end'] = c.get('beg'), c.get('end')
    o['dda'] = c['dda'] if c.get('dda') is not None else N(c.get('dep')) + N(c.get('amort'))
    o['sbc'] = N(c.get('sbc'))
    fin = raw[ji + 1:jf] if ji is not None and jf is not None else []
    o['eq'] = sum(v for l, v in fin if re.search(FIN_EQ, l, re.I))
    o['bb'] = sum(v for l, v in fin if re.search(FIN_BB, l, re.I))
    o['div'] = sum(v for l, v in fin if re.search(FIN_DIV, l, re.I))
    inv = raw[jo + 1:ji] if jo is not None and ji is not None else []
    o['capex'] = sum(v for l, v in inv if re.search(r'^(Capital expenditures|Purchases? of property|Property, plant)', l, re.I))
    o['acq'] = sum(v for l, v in inv if re.search(r'acqui|purchase of business', l, re.I))
    return o

def cf_lines(c):
    o = {'cf_ni': c['ni'], 'cf_dda': c['dda'], 'cf_sbc': c['sbc'], 'cf_def': c['deftax']}
    o['cf_wc'] = c['cfo'] - c['ni'] - c['dda'] - c['sbc'] - c['deftax']
    o['cf_cfo'] = c['cfo']; o['cf_capex'] = c['capex']; o['cf_acq'] = c['acq']
    o['cf_oinv'] = c['cfi'] - c['capex'] - c['acq']; o['cf_cfi'] = c['cfi']
    o['cf_bb'] = c['bb']; o['cf_div'] = c['div']; o['cf_eq'] = c['eq']
    o['cf_ofin'] = c['cff'] - c['bb'] - c['div'] - c['eq']; o['cf_cff'] = c['cff']; o['cf_fx'] = c['fx']
    o['cf_net'] = c['cfo'] + c['cfi'] + c['cff'] + c['fx']
    return o

def do_cf():
    for y in range(FY0, FYC):
        a = cf_ytd(y, 4)
        if not a: LOG.append(f'{y}: no annual CF'); continue
        for k, v in cf_lines(a).items(): put(str(y), k, v)
        put(str(y), 'cf_beg', a['beg']); put(str(y), 'cf_end', a['end'])
    for y in range(FYQ0, FYC + 1):
        prev = None
        for q in (1, 2, 3, 4):
            if y == FYC and q > 1: break
            p = qk(y, q); cur = cf_ytd(y, q)
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
    b = r['bs']; ta, tca = b['ta'], b['tca']
    put(p, 'bs_cash', b['cash']); put(p, 'bs_ar', b['ar']); put(p, 'bs_inv', b['inv']); put(p, 'bs_oca', tca - b['cash'] - b['ar'] - b['inv'])
    put(p, 'bs_tca', tca); put(p, 'bs_ppe', b['ppe']); put(p, 'bs_gw', N(b.get('gw'))); put(p, 'bs_int', N(b.get('intang')))
    put(p, 'bs_onca', ta - tca - b['ppe'] - N(b.get('gw')) - N(b.get('intang'))); put(p, 'bs_ta', ta)
    std = N(b.get('std')) + N(b.get('cltd'))
    put(p, 'bs_ap', b['ap']); put(p, 'bs_std', std); put(p, 'bs_ocl', b['tcl'] - b['ap'] - std); put(p, 'bs_tcl', b['tcl'])
    put(p, 'bs_ltd', N(b.get('ltd')))
    teq = b['teq']
    put(p, 'bs_ol', ta - teq - b['tcl'] - N(b.get('ltd')))
    put(p, 'bs_eq', teq); put(p, 'bs_tle', b['tle'])
    put(p, 'debt_tot', std + N(b.get('ltd')))

def do_manual():
    for p, d in MAN.get('restated', {}).items():
        if isinstance(d, dict):
            for k, v in d.items(): put(p, k, v)
    for p, v in MAN.get('shares_out', {}).items():
        if isinstance(v, (int, float)): put(p, 'bs_shares', v)
    for p, v in MAN.get('vacco_sales', {}).items():
        if isinstance(v, (int, float)): put(p, 'vacco', v)

def do_xbrl():
    import xbrl
    for p in periods():
        fy, q = fyq(p)
        iss = xbrl.value('CommonStockSharesIssued', fy, 'I', q) or xbrl.value('CommonStockSharesOutstanding', fy, 'I', q)
        tr = xbrl.value('TreasuryStockCommonShares', fy, 'I', q) or xbrl.value('TreasuryStockShares', fy, 'I', q)
        if iss is not None and tr is not None: put(p, 'bs_shares', iss - tr)

def run():
    if DATA: return DATA
    load()
    for p in periods():
        do_pl(p); do_bs(p); do_seg(p)
    do_cf(); do_manual(); do_xbrl()
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: round(x[k], 1) if isinstance(x.get(k), float) else x.get(k) for k in
                  ('rev', 's_aero', 's_ind', 'gm_aero', 'oi', 'adj_oi_pub', 'ni', 'e_def', 'e_pub', 'e_pub_cur', 'adj_ebitda_pub', 'cf_cfo', 'cf_wc', 'bs_ta', 'debt_tot')})
    print('\n'.join(LOG))
