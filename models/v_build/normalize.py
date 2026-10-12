"""Harmonise the extracted Visa data (data/<period>.json statements and KPIs, data/ngaap/<period>.json non-GAAP reconciliations)
into flat model keys: DATA[period]['x'][key] (USD m; shares m; per share USD).

Basis: every period as originally reported (Q1-Q3 from the 10-Q, identical to the release; annual from the 10-K).
  - Q4 three-month P&L: Q4 earnings release column where its tables are text (FY2013-17, FY2021+); FY2018-20 releases are slide
    images, so Q4 = fiscal year (10-K) - nine months (Q3 10-Q). Where both exist they are compared (LOG).
  - Cash flow: year-to-date statements; discrete quarters derived (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M). The cash-flow
    cash basis includes restricted cash and equivalents from FY2019 (ASU 2016-18) - BS cash vs CF cash differs by that amount.
  - 4-for-1 stock split effective 18-Mar-2015: shares x4 and per-share / 4 for every document filed before that date.
  - Class A EPS is reported on an as-converted basis: diluted class A shares include class B / C common and series A / B / C
    (UK&I / Europe) preferred on an as-converted basis, so net income / diluted class A shares = diluted EPS.
  - Non-GAAP: each period's own release, as first published (data/ngaap). Periods without a published reconciliation:
    adjusted = GAAP (flag 'adj_none').
  - DPS: quarterly dividend declared, from the release sentence announcing the next quarter's declaration ("declared a quarterly
    cash dividend of $x per share"); fiscal year = sum of the four quarters.
"""
import json, glob, os, re
import datetime as dt

BASE = os.path.dirname(os.path.abspath(__file__))
S = os.environ.get('V_SRC', '/tmp/v_src')
DATA, LOG, REC, NG = {}, [], {}, {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json'))) if os.path.exists(os.path.join(BASE, 'manual_items.json')) else {}
SPLIT = '2015-03-18'
FY0, FYQ0, FYC = 2008, 2013, 2026

def N(x): return x or 0.0
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def fyq(p):
    if p.isdigit(): return int(p), 4
    return int('20' + p[-2:]), int(p[1])

def periods():
    out = [str(y) for y in range(FY0, FYC)]
    for y in range(FYQ0, FYC + 1):
        out += [qk(y, q) for q in (1, 2, 3, 4) if not (y == FYC and q == 4)]
    return out

def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))
    for f in glob.glob(os.path.join(BASE, 'data', 'ngaap', '*.json')):
        NG[os.path.basename(f)[:-5]] = json.load(open(f))

def doc_date(url):
    """filing date of a source document (from the period index file names cached in _sources.json)."""
    return SRCDATE.get(url)
SRCDATE = {}

def split_factor(date):
    return 4.0 if date and date < SPLIT else 1.0

# ------------------------------------------------------------------ P&L
IS_K = ('rev_svc', 'rev_dp', 'rev_itr', 'rev_oth', 'rev_ci', 'rev_net', 'personnel', 'marketing', 'network', 'prof', 'dna', 'ga', 'litig',
        'opex', 'opinc', 'int_exp', 'nonop', 'ebt', 'tax')

def is_flat(i):
    """statement-of-operations dict (as extracted) -> model keys (costs positive, client incentives positive)."""
    o = {k: i.get(k) for k in IS_K}
    if o['rev_ci'] is not None: o['rev_ci'] = abs(o['rev_ci'])
    if o['rev_net'] is not None and o['rev_svc'] is not None:
        o['rev_gross'] = o['rev_svc'] + o['rev_dp'] + o['rev_itr'] + o['rev_oth']
    o['oth_op'] = sum(v for _, v in i.get('other_op', []) if v is not None)
    o['oth_op_labels'] = '; '.join(f'{l} {v:,.0f}' for l, v in i.get('other_op', []) if v)
    o['int_exp'] = -N(i.get('int_exp')) if i.get('int_exp') is not None else 0.0      # printed as (194) -> expense +194
    if o['nonop'] is None:                                                             # single-line presentations
        o['nonop'] = o['ebt'] - o['opinc'] if o['ebt'] is not None and o['opinc'] is not None else None
    o['inv_oth'] = o['nonop'] + o['int_exp'] if o['nonop'] is not None else None      # investment income & other (ex interest)
    ni_tot = i.get('ni_tot'); ni = i.get('ni')
    if ni is None: ni = ni_tot
    o['ni_tot'] = ni_tot if ni_tot is not None else ni
    o['ni'] = ni
    o['nci'] = (o['ni_tot'] - ni) if (o['ni_tot'] is not None and ni is not None) else 0.0
    for k in ('eps_b', 'eps_d', 'sh_b', 'sh_d'): o[k] = i.get(k)
    return o

def sub(a, b, keys):
    return {k: (a[k] - b[k]) if (a.get(k) is not None and b.get(k) is not None) else None for k in keys}

FLOWK = IS_K + ('rev_gross', 'oth_op', 'inv_oth', 'ni_tot', 'ni', 'nci')

def do_pl():
    for p in periods():
        r = REC.get(p)
        if not r: LOG.append(f'{p}: no record'); continue
        fy, q = fyq(p)
        sf = split_factor(SRCDATE.get(r['sources'].get('filing')) if p.isdigit() or q < 4 else r['sources'].get('release_date'))
        if p.isdigit() or q < 4:
            o = is_flat(r['is'])
            if not p.isdigit():
                put(p, 'is_src', '10-Q')
        else:
            a = is_flat(REC[str(fy)]['is']); n = is_flat(REC[qk(fy, 3)]['is_ytd'])
            der = sub(a, n, FLOWK)
            der['oth_op_labels'] = a['oth_op_labels']
            rel = r.get('is_rel')
            if rel:
                o = is_flat(rel)
                bad = [k for k in FLOWK if o.get(k) is not None and der.get(k) is not None and abs(o[k] - der[k]) > 1.01]
                if bad: LOG.append(f'{p}: Q4 release vs FY-9M differ: ' + ', '.join(f'{k} {o[k]} vs {der[k]}' for k in bad))
                put(p, 'is_src', 'Q4 release')
            else:
                o = der
                o['eps_d'] = o['eps_b'] = None
                o['sh_d'] = o['sh_b'] = None
                put(p, 'is_src', 'FY - 9M')
            sf = split_factor(r['sources'].get('release_date'))
        for k in FLOWK:
            put(p, k, o.get(k))
        put(p, 'oth_op_labels', o.get('oth_op_labels') or '')
        for k in ('eps_b', 'eps_d'):
            if o.get(k) is not None: put(p, k, o[k] / sf)
        for k in ('sh_b', 'sh_d'):
            if o.get(k) is not None: put(p, k, o[k] * sf)
        if sf != 1: put(p, 'split_adj', sf)
    # Q4 diluted shares where the release is an image (FY2018-20): 4 x FY weighted shares - Q1-Q3 (company weighting), EPS derived
    for y in range(FYQ0, FYC):
        p = qk(y, 4); x = DATA.get(p, {}).get('x', {})
        if x.get('sh_d') is None and DATA.get(str(y), {}).get('x', {}).get('sh_d') is not None:
            qs = [DATA[qk(y, q)]['x'].get('sh_d') for q in (1, 2, 3)]
            if None not in qs:
                put(p, 'sh_d', 4 * DATA[str(y)]['x']['sh_d'] - sum(qs))
                put(p, 'sh_d_derived', 1)
                LOG.append(f'{p}: diluted shares derived as 4 x FY - (Q1+Q2+Q3)')

# ------------------------------------------------------------------ non-GAAP
CATS = ['LITIG', 'EQINV', 'AMORT', 'ACQ', 'RESTR', 'VE', 'TAX', 'OTHER']
OPC = ['litig', 'amort', 'acq', 'restr', 've', 'other']          # operating-expense adjusting items (model rows)
NOPC = ['eqinv', 've', 'other']                                  # non-operating adjusting items

def do_ng():
    for p in periods():
        g = NG.get(p)
        x = DATA.get(p, {}).get('x', {})
        sf = split_factor(g.get('release_date')) if g else 1.0
        op = {c: 0.0 for c in OPC}; nop = {c: 0.0 for c in NOPC}; lab = {c: [] for c in set(OPC) | set(NOPC) | {'tax'}}
        tax = 0.0
        if g and g.get('published') and g.get('adjusted') and g['adjusted'].get('ni') is not None:
            for it in g['items']:
                c = (it.get('cat') or 'OTHER').upper(); cl = c.lower()
                pre_op = -it['opex'] if it.get('opex') not in (None,) else None
                pre_no = it.get('nonop')
                if pre_op is None and pre_no is None and it.get('ebt') is not None:   # FY2008-style pre-tax table
                    if it.get('where') == 'nonop': pre_no = it['ebt']
                    else: pre_op = it['ebt']
                if c == 'TAX':
                    tax += -N(it.get('ni')) if it.get('tax') is None else N(it.get('tax'))
                    lab['tax'].append(it['label']); continue
                if c == 'EQINV': cl = 'eqinv'
                if pre_op:
                    k = cl if cl in OPC else 'other'; op[k] += pre_op; lab[k].append(it['label'])
                if pre_no:
                    k = cl if cl in NOPC else 'other'; nop[k] += pre_no; lab[k].append(it['label'])
                if it.get('tax') is not None: tax += it['tax']
            a = g['adjusted']
            put(p, 'adj_ni_pub', a['ni']); put(p, 'adj_eps_pub', a['eps'] / sf if a.get('eps') is not None else None)
            put(p, 'adj_opex_pub', a.get('opex')); put(p, 'adj_tax_pub', a.get('tax'))
            put(p, 'adj_basis', 'published')
            put(p, 'adj_def', g.get('definition') or '')
            # tax effect of the items: published adjusted NI - GAAP NI - pre-tax items (covers tax-only items and FY2008-style tables)
            pre = sum(op.values()) + sum(nop.values())
            put(p, 'ng_taxeff', a['ni'] - N(x.get('ni')) - pre)
        else:
            put(p, 'adj_basis', 'none'); put(p, 'adj_none', 1)
        for c in OPC: put(p, f'oa_{c}', op[c]); put(p, f'oa_{c}_lab', '; '.join(dict.fromkeys(lab[c])))
        for c in NOPC: put(p, f'na_{c}', nop[c]); put(p, f'na_{c}_lab', '; '.join(dict.fromkeys(lab[c])))
        put(p, 'tax_items_lab', '; '.join(dict.fromkeys(lab['tax'])))
        if x.get('adj_basis') == 'none' or not (g and g.get('published')):
            put(p, 'ng_taxeff', 0.0)

# ------------------------------------------------------------------ cash flow
CFK = ('ni', 'dna', 'sbc', 'deftax', 'cfo', 'capex', 'acq', 'cfi', 'bb', 'div', 'debt_iss', 'debt_rep', 'cp', 'cff', 'fx', 'net')

def cf_ytd(fy, q):
    r = REC.get(str(fy)) if q == 4 else REC.get(qk(fy, q))
    if not r or not r.get('cf') or r['cf'].get('cfo') is None: return None
    c = r['cf']
    o = {k: N(c.get(k)) for k in CFK}
    o['beg'], o['end'] = c.get('beg'), c.get('end')
    return o

def cf_lines(c):
    o = {'cf_ni': c['ni'], 'cf_dda': c['dna'], 'cf_sbc': c['sbc'], 'cf_def': c['deftax']}
    o['cf_wc'] = c['cfo'] - c['ni'] - c['dna'] - c['sbc'] - c['deftax']
    o['cf_cfo'] = c['cfo']; o['cf_capex'] = c['capex']; o['cf_acq'] = c['acq']
    o['cf_oinv'] = c['cfi'] - c['capex'] - c['acq']; o['cf_cfi'] = c['cfi']
    o['cf_bb'] = c['bb']; o['cf_div'] = c['div']; o['cf_debt'] = c['debt_iss'] + c['debt_rep'] + c['cp']
    o['cf_ofin'] = c['cff'] - c['bb'] - c['div'] - o['cf_debt']; o['cf_cff'] = c['cff']; o['cf_fx'] = c['fx']
    o['cf_net'] = c['cfo'] + c['cfi'] + c['cff'] + c['fx']
    return o

def x_(p, k): return DATA.get(p, {}).get('x', {}).get(k)

def do_cf():
    for y in range(FY0, FYC):
        a = cf_ytd(y, 4)
        if not a: LOG.append(f'{y}: no annual CF'); continue
        for k, v in cf_lines(a).items(): put(str(y), k, v)
        put(str(y), 'cf_beg', a['beg']); put(str(y), 'cf_end', a['end'])
    for y in range(FYQ0, FYC + 1):
        prev = None
        for q in (1, 2, 3, 4):
            if y == FYC and q == 4: break
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

# ------------------------------------------------------------------ balance sheet
def do_bs(p):
    r = REC.get(p)
    if not r or not r.get('bs') or r['bs'].get('ta') is None: return
    b = r['bs']
    tca, ta = b['tca'], b['ta']
    put(p, 'bs_cash', b['cash']); put(p, 'bs_escrow', N(b.get('escrow')))
    put(p, 'bs_inv', N(b.get('inv_cur')) + N(b.get('inv_nc')))
    put(p, 'bs_settle', N(b.get('settle_rec'))); put(p, 'bs_collat', N(b.get('collat_a')))
    put(p, 'bs_oca', tca - b['cash'] - N(b.get('escrow')) - N(b.get('inv_cur')) - N(b.get('settle_rec')) - N(b.get('collat_a')))
    put(p, 'bs_ppe', b['ppe']); put(p, 'bs_gw', b['gw']); put(p, 'bs_int', b['intang'])
    put(p, 'bs_onca', ta - tca - N(b.get('inv_nc')) - b['ppe'] - b['gw'] - b['intang']); put(p, 'bs_ta', ta)
    tcl = b['tcl']; std = N(b.get('std'))
    put(p, 'bs_settle_l', N(b.get('settle_pay'))); put(p, 'bs_collat_l', N(b.get('collat_l'))); put(p, 'bs_litig', N(b.get('litig_acc')))
    put(p, 'bs_std', std)
    put(p, 'bs_ocl', tcl - N(b.get('settle_pay')) - N(b.get('collat_l')) - N(b.get('litig_acc')) - std)
    put(p, 'bs_ltd', N(b.get('ltd'))); put(p, 'bs_ol', b['tl'] - tcl - N(b.get('ltd')))
    put(p, 'bs_tl', b['tl']); put(p, 'bs_te', b['te']); put(p, 'bs_tle', b['tle']); put(p, 'bs_tcl', tcl); put(p, 'bs_tca', tca)
    put(p, 'debt_tot', std + N(b.get('ltd')))

def do_q4_bs():
    for y in range(FYQ0, FYC):
        a = DATA.get(str(y), {}).get('x', {})
        for k, v in list(a.items()):
            if k.startswith('bs_') or k == 'debt_tot': put(qk(y, 4), k, v)

# ------------------------------------------------------------------ KPIs and dividends
def do_kpi():
    for p in periods():
        r = REC.get(p) or {}
        k = r.get('kpi') or {}
        fy, q = fyq(p)
        if p.isdigit() or q < 4:
            for a in ('pv', 'pv_us', 'pv_intl', 'ptx'): put(p, 'k_' + a, k.get(a))
        else:
            A = REC.get(str(fy), {}).get('kpi') or {}; Q3 = REC.get(qk(fy, 3), {}).get('kpi') or {}
            for a in ('pv', 'pv_us', 'pv_intl', 'ptx'):
                if A.get(a) is not None and Q3.get(a + '_9m') is not None: put(p, 'k_' + a, A[a] - Q3[a + '_9m'])

DIVRE = re.compile(r'(?:declared (?:a|an increase to Visa.s)|increased (?:the|Visa.s|the Company.s)) quarterly (?:cash )?dividend[^$]{0,60}?\$\s*([\d.]+)', re.I)
def do_dps():
    idx = json.load(open(os.path.join(S, 'period_index.json'))) if os.path.exists(os.path.join(S, 'period_index.json')) else {}
    cache = os.path.join(BASE, 'data', '_dps.json')
    if idx:
        dec = {}
        for k, e in idx.items():
            if not k.startswith('Q') or not e.get('release_txt'): continue
            t = ''
            for f in (e.get('release_txt'), e.get('release_hidden_txt')):
                if f:
                    for d in ('txt', 'txt_hidden'):
                        fp = os.path.join(S, d, f)
                        if os.path.exists(fp): t += open(fp).read()
            m = DIVRE.search(re.sub(r'\s+', ' ', t))
            if m:
                fy, q = int('20' + k[3:]), int(k[1])
                nq = (fy + (q == 4), 1 if q == 4 else q + 1)          # declared after the quarter -> next fiscal quarter
                dec[qk(*nq)] = [float(m.group(1)), e['release_date'], e['release']]
        json.dump(dec, open(cache, 'w'), indent=1)
    dec = json.load(open(cache)) if os.path.exists(cache) else {}
    for p, (v, d, u) in dec.items():
        put(p, 'dps', v / split_factor(d)); put(p, 'dps_src', u)
    # fallback: XBRL dividends-declared-per-share fact ending at the quarter end (Visa tags the quarterly rate in every context)
    import xbrl
    qend = {1: (-1, 12, 31), 2: (0, 3, 31), 3: (0, 6, 30), 4: (0, 9, 30)}
    for y in range(FYQ0, FYC + 1):
        for q in (1, 2, 3, 4):
            p = qk(y, q)
            if p not in periods() or x_(p, 'dps') is not None: continue
            dy, m, d = qend[q]; end = f'{y + dy}-{m:02d}-{d:02d}'
            fs = [f for c in ('CommonStockDividendsPerShareDeclared', 'CommonStockDividendsPerShareCashPaid') for f in xbrl.facts().get(c, [])
                  if f.get('end') == end and f.get('form') in ('10-Q', '10-K')]
            if fs:
                f = min(fs, key=lambda f: f['filed'])
                put(p, 'dps', f['val'] / split_factor(f['filed'])); put(p, 'dps_src', f'XBRL CommonStockDividendsPerShareDeclared (quarterly rate), filed {f["filed"]}')
                LOG.append(f'{p}: DPS from XBRL quarterly-rate fact (no release sentence)')
    for y in range(FYQ0, FYC):
        qs = [x_(qk(y, q), 'dps') for q in (1, 2, 3, 4)]
        if None not in qs: put(str(y), 'dps', sum(qs))
    for y in range(FY0, FYC):          # 10-K selected financial data (FY2008-FY2017); cross-check vs sum of quarters
        r = REC.get(str(y)) or {}
        if r.get('dps_10k') is not None:
            v = r['dps_10k'] / split_factor(SRCDATE.get(r['sources'].get('filing')))
            if x_(str(y), 'dps') is None: put(str(y), 'dps', v)
            elif abs(x_(str(y), 'dps') - v) > 0.006: LOG.append(f'{y}: DPS sum of quarters {x_(str(y), "dps")} vs 10-K {v}')

def run():
    load()
    src = os.path.join(BASE, 'filings.csv')
    if os.path.exists(src):
        import csv
        for r in csv.DictReader(open(src)): SRCDATE[r['url']] = r['filing_date']
    do_pl(); do_ng()
    for p in periods(): do_bs(p)
    do_q4_bs(); do_cf(); do_kpi(); do_dps()
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: round(x[k], 2) if isinstance(x.get(k), float) else x.get(k) for k in
                  ('rev_net', 'opinc', 'ni', 'eps_d', 'sh_d', 'adj_ni_pub', 'adj_eps_pub', 'cf_cfo', 'bs_ta', 'k_pv', 'k_ptx', 'dps')})
    print('\n'.join(LOG))
