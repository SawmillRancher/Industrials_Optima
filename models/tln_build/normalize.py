"""Harmonise the extracted Talen data (data/<tag>.json, see extract.py) into flat model keys: DATA[period]['x'][key] (USD m).

Basis: as originally reported — each period from the first filing that presents it (S-1 for FY2021-22, the two 2023 periods,
Q1-23 and Q1-24; then each 10-Q / 10-K and earnings release).
  * FY2023 = Predecessor (1-Jan..17-May-2023, Talen Energy Supply) + Successor (18-May..31-Dec-2023, Talen Energy Corporation
    after fresh-start accounting), summed as presented; the two periods are not comparable (noted in the workbook).
  * Q2-23 = 1-Apr..17-May (Predecessor) + 18-May..30-Jun (Successor), from the Q2-24 10-Q; Q3-23 from the Q3-24 10-Q.
  * Q4 = fiscal year - nine months (the releases give no three-month Q4 statement); Q4 weighted shares = 4 x FY - sum(Q1..Q3).
  * Cash flow is filed year to date; discrete quarters are derived (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M).
  * Non-GAAP: net income -> Adjusted EBITDA -> Adjusted Free Cash Flow reconciliations; the company's line items are grouped
    into categories (MTM, NDT, SBC, GAIN, IMPAIR, RESTR, ACQ, OTHER) and the original wording is kept in *_lab keys.
    Q4-25 is published as a three-month column; other Q4 = FY - 9M. FY2023 free-cash-flow items come from the Q4-24 release
    (first publication); Q1-23 free-cash-flow items = Predecessor period - (1-Apr..17-May) (derived).
  * Segments (PJM segment Adjusted EBITDA, "Other" segment): current basis, published from the FY2024 10-K (FY2022-24) and
    quarterly from the 2025 10-Qs (2024 comparatives); Q4 = FY - 9M.
Signs: costs positive; gains / income items positive; cash flow as presented."""
import json, glob, os
BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))
FY0, FYQ0, FYC, LASTQ = 2021, 2023, 2026, 3

def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def periods():
    out = [str(y) for y in range(FY0, FYC)]
    for y in range(FYQ0, FYC + 1):
        out += [qk(y, q) for q in (1, 2, 3, 4) if not (y == FYC and q > LASTQ)]
    return out
def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v
def X(p): return DATA.get(p, {}).get('x', {})

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

def comb(sec, plus, minus=()):
    """Linear combination of raw records (missing key in a part = 0 if any part has it)."""
    out = {}
    keys = set()
    for t in list(plus) + list(minus): keys |= {k for k, v in REC.get(t, {}).get(sec, {}).items() if isinstance(v, (int, float))}
    for k in keys:
        out[k] = sum(REC[t][sec].get(k, 0.0) or 0.0 for t in plus) - sum(REC[t][sec].get(k, 0.0) or 0.0 for t in minus)
    labs = {}
    for t in plus:
        for k, v in REC.get(t, {}).get(sec, {}).items():
            if isinstance(v, str): labs.setdefault(k, []).append(v)
    for k, v in labs.items(): out[k] = ' + '.join(v) if len(plus) > 1 else v[0]
    return out

IS_FLOW = ['cap_rev', 'en_rev', 'unr_rev', 'rev', 'fuel', 'nfa', 'unr_exp', 'en_exp', 'om', 'ga', 'dda', 'impair', 'restr_op', 'oth_op', 'oi', 'ndt', 'int', 'reorg',
           'consol', 'gain_sale', 'oth_nonop', 'ebt', 'tax', 'ni_tot', 'nci', 'ni', 'ga_sbc']
def is_rec(p):
    y = int(p) if p.isdigit() else int('20' + p[-2:]); q = None if p.isdigit() else int(p[1])
    yy = str(y)[2:]
    if p == '2023': return comb('is', ['P23', 'S23']), 'Predecessor (1-Jan..17-May) + Successor (18-May..31-Dec), S-1'
    if p == 'Q2-23': return comb('is', ['P23b', 'S23a']), 'Predecessor (1-Apr..17-May) + Successor (18-May..30-Jun), Q2-24 10-Q'
    if p == 'Q4-23': return comb('is', ['P23', 'S23'], ['Q1-23', 'P23b', 'S23a', 'Q3-23']), 'FY2023 - Q1 - Q2 - Q3 (derived)'
    if q == 4: return comb('is', [str(y)], [f'9M-{yy}']), 'fiscal year - nine months (derived)'
    return dict(REC[p]['is']), None

def do_is(p):
    r, note = is_rec(p)
    if note: put(p, 'is_note', note)
    for k in IS_FLOW:
        if k in r or k in ('impair', 'restr_op', 'reorg', 'consol', 'gain_sale', 'nci'): put(p, k, float(r.get(k, 0.0) or 0.0))
    if 'ni_tot' not in r: put(p, 'ni_tot', r['ni'] + (r.get('nci') or 0.0))
    if 'ni' not in r: put(p, 'ni', r['ni_tot'] - (r.get('nci') or 0.0))     # single net-income line (no noncontrolling interest in the period)
    x = X(p)
    put(p, 'unr', x['unr_rev'] + x['unr_exp']); put(p, 'unr_exp_cost', -x['unr_exp'])
    put(p, 'impair_restr', x['impair'] + x['restr_op'])
    put(p, 'reorg_consol', x['reorg'] + x['consol'])
    put(p, 'en_margin_gaap', x['en_rev'] - x['fuel'])
    # per share (Successor only)
    y = int(p) if p.isdigit() else int('20' + p[-2:]); q = None if p.isdigit() else int(p[1])
    if q == 4 and y >= 2024:
        fy = REC[str(y)]['is']; qs = [REC[qk(y, i)]['is'] for i in (1, 2, 3)]
        sb = 4 * fy['sh_b'] - sum(z['sh_b'] for z in qs); sd = 4 * fy['sh_d'] - sum(z['sh_d'] for z in qs)
        put(p, 'sh_b', sb); put(p, 'sh_d', max(sb, sd) if X(p)['ni'] >= 0 else sb)      # loss quarter: diluted = basic
        put(p, 'sh_note', 'Q4 weighted shares = 4 x FY - sum(Q1..Q3) (derived); Q4 EPS not published')
    elif p == '2023':
        s = REC['S23']['is']
        for k in ('sh_b', 'sh_d', 'eps_b', 'eps_d'): put(p, k, s.get(k))
        put(p, 'sh_note', 'Successor period only (18-May..31-Dec-2023): EPS $2.27 basic / $2.26 diluted on net income attributable of $134m; no per-share data for the Predecessor')
    elif p == 'Q3-23' or (y >= 2024 and q != 4):
        for k in ('sh_b', 'sh_d', 'eps_b', 'eps_d'): put(p, k, r.get(k))

CF_KEYS = ['ni', 'unr', 'dda', 'nfa', 'ndt', 'def', 'sbc', 'gain', 'impair', 'restr', 'reorg', 'cfo', 'capex', 'nfuel', 'ndt_inv', 'acq', 'proceeds', 'cfi', 'bb', 'cff', 'net']
def cf_ytd(y, m):
    yy = str(y)[2:]
    if y == 2023:
        t = {3: ['Q1-23'], 6: ['P23', 'S23a'], 9: ['P23', 'S23c'], 12: ['P23', 'S23']}[m]
    else:
        t = [{3: f'Q1-{yy}', 6: f'H1-{yy}', 9: f'9M-{yy}', 12: str(y)}[m]]
    if any(not REC.get(k, {}).get('cf') for k in t): return None
    r = comb('cf', t)
    r['beg'] = REC[t[0]]['cf']['beg']; r['end'] = REC[t[-1]]['cf']['end']
    return r
def do_cf(p):
    y = int(p) if p.isdigit() else int('20' + p[-2:]); q = None if p.isdigit() else int(p[1])
    cur = cf_ytd(y, 12 if q is None else 3 * q)
    if cur is None: return
    prev = cf_ytd(y, 3 * (q - 1)) if q and q > 1 else None
    if q and q > 1 and prev is None: return
    def g(k): return (cur.get(k, 0.0) or 0.0) - ((prev.get(k, 0.0) or 0.0) if prev else 0.0)
    for k in CF_KEYS: put(p, 'cf_' + k, g(k))
    put(p, 'cf_beg', prev['end'] if prev else cur['beg']); put(p, 'cf_end', cur['end'])
    x = X(p)
    put(p, 'cf_ncoth', x['cf_gain'] + x['cf_impair'] + x['cf_restr'] + x['cf_reorg'])
    put(p, 'cf_wc', x['cf_cfo'] - x['cf_ni'] - x['cf_unr'] - x['cf_dda'] - x['cf_nfa'] - x['cf_ndt'] - x['cf_def'] - x['cf_sbc'] - x['cf_ncoth'])
    put(p, 'cf_oinv', x['cf_cfi'] - x['cf_capex'] - x['cf_nfuel'] - x['cf_ndt_inv'] - x['cf_acq'] - x['cf_proceeds'])
    put(p, 'cf_ofin', x['cf_cff'] - x['cf_bb'])

def do_bs(p):
    src = p
    if not p.isdigit() and p[1] == '4': src = '20' + p[-2:]            # Q4 balance sheet = fiscal year end
    b = REC.get(src, {}).get('bs')
    if not b: return
    g = lambda k: b.get(k, 0.0) or 0.0
    put(p, 'bs_cash', g('cash') + g('rcash')); put(p, 'bs_rcash', g('rcash')); put(p, 'bs_ar', g('ar')); put(p, 'bs_inv', g('inv'))
    put(p, 'bs_der_a', g('der_ca') + g('der_nca')); put(p, 'bs_oca', g('oca') + g('ahs')); put(p, 'bs_ppe', g('ppe')); put(p, 'bs_ndt', g('ndt'))
    put(p, 'bs_onca', g('onca')); put(p, 'bs_ta', g('ta'))
    put(p, 'bs_ap', g('ap')); put(p, 'bs_accint', g('accint')); put(p, 'bs_der_l', g('der_cl') + g('der_ncl'))
    put(p, 'bs_ocl', g('ocl') + g('lhs') + g('sbc_liab')); put(p, 'bs_sbc_liab', g('sbc_liab'))
    put(p, 'debt_st', g('rcf') + g('cpltd')); put(p, 'bs_rcf', g('rcf')); put(p, 'bs_ltd', g('ltd')); put(p, 'bs_lstc', g('lstc'))
    put(p, 'bs_pension', g('pension')); put(p, 'bs_aro', g('aro')); put(p, 'bs_dtl', g('dtl')); put(p, 'bs_acl', g('acl'))
    put(p, 'bs_oncl', g('oncl') + g('lstc')); put(p, 'bs_tl', g('tl')); put(p, 'bs_eq', g('eq')); put(p, 'bs_nci', g('nci')); put(p, 'bs_teq', g('teq') if 'teq' in b else g('eq'))
    put(p, 'bs_tle', g('tle')); put(p, 'bs_tca', g('tca')); put(p, 'bs_tcl', g('tcl'))
    put(p, 'bs_shares', MAN['shares_out'].get(src))

CATS = ['MTM', 'NDT', 'SBC', 'GAIN', 'IMPAIR', 'RESTR', 'ACQ', 'OTHER']
NGK = ['ni', 'int', 'tax', 'dda', 'nfa'] + CATS + ['adj_ebitda']
FK = ['f_capex', 'f_int', 'f_tax', 'f_pension', 'adj_fcf']
def ng_rec(p):
    y = int(p) if p.isdigit() else int('20' + p[-2:]); q = None if p.isdigit() else int(p[1]); yy = str(y)[2:]
    if p == '2023':
        r = comb('ng', ['P23', 'S23']); f = comb('ng', ['P23x', 'S23x'])
        for k in FK: r[k] = f[k]
        return r
    if p == 'Q2-23': return comb('ng', ['P23b', 'S23a'])
    if p == 'Q1-23':
        r = dict(REC['Q1-23']['ng']); a, b = REC['P23x']['ng'], REC['P23b']['ng']
        for k in FK: r[k] = a[k] - b[k]
        r['fcf_note'] = 'Q1-23 Adjusted FCF items = Predecessor period (1-Jan..17-May, Q4-24 release) - 1-Apr..17-May (Q2-24 release); derived'
        return r
    if p == 'Q4-23':
        r = comb('ng', ['P23', 'S23'], ['Q1-23', 'P23b', 'S23a', 'Q3-23']); f = comb('ng', ['P23x', 'S23x'], ['P23x', 'S23a', 'Q3-23'])
        for k in FK: r[k] = f[k]
        return r
    if p == 'Q1-24':
        r = dict(REC['Q1-24']['ng']); a, b = REC['H1-24']['ng'], REC['Q2-24']['ng']
        for k in FK: r[k] = a[k] - b[k]
        r['fcf_note'] = 'Q1-24 Adjusted FCF items = six months - Q2 (Q2-24 release); derived (the S-1 gives Adjusted EBITDA only)'
        return r
    if q == 4 and p in REC and REC[p].get('ng') and y >= 2025: return dict(REC[p]['ng'])
    if q == 4: return comb('ng', [str(y)], [f'9M-{yy}'])
    return dict(REC[p]['ng'])
def do_ng(p):
    if p in ('2021', '2022') or True:
        r = ng_rec(p)
    for k in NGK:
        if k in r or k in CATS: put(p, 'ng_' + k, float(r.get(k, 0.0) or 0.0))
    for k in CATS:
        if r.get(k + '_lab'): put(p, f'ng_{k}_lab', r[k + '_lab'])
    for k in FK:
        if k in r: put(p, k, r[k])
    if r.get('fcf_note'): put(p, 'fcf_note', r['fcf_note'])
    x = X(p)
    put(p, 'ng_items', sum(x['ng_' + k] for k in CATS))
    put(p, 'ng_dda_diff', x['dda'] - x['ng_dda'])
    put(p, 'ng_int_diff', x['ng_int'] - x['int'])
    put(p, 'adj_ebitda_pub', x['ng_adj_ebitda'])
    if 'adj_fcf' in x: put(p, 'adj_fcf_pub', x['adj_fcf'])

def do_seg(p):
    y = int(p) if p.isdigit() else int('20' + p[-2:]); q = None if p.isdigit() else int(p[1]); yy = str(y)[2:]
    if p == '2023': r = comb('seg', ['P23', 'S23'])
    elif q == 4 and y >= 2024: r = comb('seg', [str(y)], [f'9M-{yy}'])
    else: r = REC.get(p, {}).get('seg') or {}
    if 'pjm' not in r: return
    put(p, 'seg_pjm', r['pjm']); put(p, 'seg_other', r.get('other', 0.0))

def do_ops(p):
    y = int(p) if p.isdigit() else int('20' + p[-2:]); q = None if p.isdigit() else int(p[1])
    o = REC.get(p, {}).get('ops') or {}
    for k in ('gen_twh', 'carbon_free', 'cap_factor'): put(p, k, o.get(k))

def run():
    if DATA: return DATA
    load()
    for p in periods():
        do_is(p); do_cf(p); do_bs(p); do_ng(p); do_seg(p); do_ops(p)
        srcs = []
        for t in ([p] if p in REC else []) + (['P23', 'S23'] if p == '2023' else []):
            srcs += REC[t]['sources']
        DATA[p]['sources'] = srcs
    return DATA

if __name__ == '__main__':
    d = run()
    for p in periods():
        x = d[p]['x']; print(p, x.get('rev'), x.get('oi'), x.get('ni'), x.get('adj_ebitda_pub'), x.get('adj_fcf_pub'), x.get('cf_cfo'), x.get('bs_ta'), x.get('gen_twh'), x.get('seg_pjm'), x.get('sh_d'))
