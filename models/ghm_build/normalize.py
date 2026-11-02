"""Harmonise the extracted Graham data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m).

Basis: every period as originally reported in its own earnings release (statements, non-GAAP tables, orders / backlog, sales
by market and region). Exceptions, by source priority:
  - Sales by market on the current Defense / Space / Energy & Process basis (introduced in the FY2025 10-K): Defense and Space
    as published in each period's release grid (Defense split from FY2020 in the FY2021 releases' prior-year tables = latest
    presentation; Space = 0 before Barber-Nichols, FY2022); Energy & Process = net sales - Defense - Space (equals the
    company's figure wherever it publishes one). The legacy market split (refining / chemical & petrochemical / power /
    defense / space / other) is kept as memo keys exactly as published (USD m to one decimal in the release grids to FY2022;
    USD thousands in the Ex. 99.2 supplemental exhibits from FY2023; the 10-K / 10-Q revenue note where available).
  - Stock splits: shares and per-share data are restated for the 5-for-4 split (effective 3-Jan-2008) and the 2-for-1 split
    (effective 6-Oct-2008) by the release date (x2.5 for releases before 3-Jan-2008, x2 before 6-Oct-2008).
  - Operating profit: Q1 FY22 release presented no operating-loss line; derived as gross profit - SG&A - amortization - other.
Cash flow: releases give year-to-date statements; discrete quarters derived (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M).
Non-GAAP: items are grouped into model buckets (acq, amort, restr, impair, erp, sbc, oth, tax, taxd) per table (EBITDA,
adjusted net income, adjusted operating profit), with the company labels kept for cell comments.
"""
import json, glob, os, datetime as dt

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))

def N(x): return x or 0.0
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def fyq(p):
    if p.isdigit(): return int(p), 4
    return int('20' + p[-2:]), int(p[1])

def periods():
    out = [str(y) for y in range(2006, 2027)]
    for y in range(2013, 2028):
        out += [qk(y, q) for q in (1, 2, 3, 4) if not (y == 2027 and q > 1)]
    return out

def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

def split_factor(date):
    d = dt.date.fromisoformat(date)
    if d < dt.date(2008, 1, 3): return 2.5
    if d < dt.date(2008, 10, 6): return 2.0
    return 1.0

# non-GAAP categories -> model buckets
BUCKET = {'ACQ': 'acq', 'STEPUP': 'acq', 'AMORT': 'amort', 'RESTR': 'restr', 'TRANS': 'restr', 'IMPAIR': 'impair', 'BADDEBT': 'impair',
          'GAIN': 'impair', 'ERP': 'erp', 'SBC': 'sbc', 'BNBONUS': 'oth', 'ERC': 'oth', 'DEBT': 'oth', 'LEGAL': 'oth', 'OTHER': 'oth',
          'TAX': 'tax', 'TAXD': 'taxd'}
BUCKETS = ['acq', 'amort', 'restr', 'impair', 'erp', 'sbc', 'oth', 'tax', 'taxd']

def items_to_buckets(r):
    tot = {b: 0.0 for b in BUCKETS}; lab = {b: [] for b in BUCKETS}; net = False
    for it in r['items']:
        l, v, c = it[0], it[1], it[2]
        if 'nuclear' in l.lower() and c == 'OTHER': c = 'IMPAIR'
        b = BUCKET.get(c, 'oth')
        if v is None: continue
        tot[b] += v
        if abs(v) > 1e-9: lab[b].append(f'{l.strip("+- ")} {v:,.3f}')
        if len(it) > 3 and it[3] == 'net_of_tax': net = True
    return tot, lab, net

def do_pl(p):
    r = REC.get(p)
    if not r: LOG.append(f'{p}: no record'); return
    fy, q = fyq(p)
    i, n, k = r['is'], r['ngaap'], r['kpi']
    f = split_factor(r['sources']['release_date'])
    rev = i['rev']
    put(p, 'rev', rev)
    cogs = i['cogs'] + N(i.get('cogs_amort'))
    put(p, 'cogs', cogs); put(p, 'gp', rev - cogs); put(p, 'cogs_amort', N(i.get('cogs_amort')))
    put(p, 'sga', i['sga']); put(p, 'amort', N(i.get('sga_amort'))); put(p, 'restr', N(i.get('restr'))); put(p, 'impair', N(i.get('impair')))
    oth_op = N(i.get('oth_op')) + sum(v for _, v in i.get('other_op_lines', []))
    put(p, 'oth_op', oth_op); put(p, 'oth_op_labels', '; '.join(f'{l} {v:,.3f}' for l, v in i.get('other_op_lines', [])) or None)
    op = i.get('op_profit')
    if op is None:
        op = rev - cogs - i['sga'] - N(i.get('sga_amort')) - N(i.get('restr')) - N(i.get('impair')) - oth_op
        LOG.append(f'{p}: operating profit not on the face of the release statement; derived {op:.3f}'); put(p, 'op_derived', 1)
    put(p, 'op', op)
    # non-operating: signs as presented in the expense section (expense positive)
    int_inc = -N(i.get('int_inc')); int_exp = N(i.get('int_exp'))
    int_net = N(i.get('int_net')) if i.get('int_net') is not None else int_exp - int_inc
    put(p, 'int_inc', int_inc); put(p, 'int_exp', int_exp); put(p, 'int_net', int_net)
    put(p, 'int_net_presented', 1 if i.get('int_net') is not None else 0)
    nonop = N(i.get('oth_nonop')) + sum(v for _, v in i.get('nonop_lines', []))
    put(p, 'oth_nonop', nonop); put(p, 'oth_nonop_labels', '; '.join(f'{l} {v:,.3f}' for l, v in i.get('nonop_lines', [])) or None)
    put(p, 'ebt', i['ebt']); put(p, 'tax', i['tax']); put(p, 'ni', i['ni'])
    put(p, 'disc_ops', N(i.get('disc_ops')))
    for kk in ('eps_b', 'eps_d', 'dps'):
        if i.get(kk) is not None: put(p, kk, i[kk] / f)
    if i.get('dps') is None and fy >= 2023: put(p, 'dps', 0.0)
    put(p, 'sh_b', i['sh_b'] * f); put(p, 'sh_d', i['sh_d'] * f); put(p, 'split_factor', f)
    # non-GAAP
    for ty, pref in (('ebitda', 'eb'), ('adjni', 'an'), ('adjop', 'ao')):
        t = n.get(ty)
        if not t: continue
        tot, lab, net = items_to_buckets(t)
        for b in BUCKETS:
            put(p, f'{pref}_{b}', tot[b]); put(p, f'{pref}_{b}_lab', '; '.join(lab[b]) or None)
        put(p, f'{pref}_net_of_tax', 1 if net else 0)
        put(p, f'{pref}_start', t.get('start'))
    e = n.get('ebitda') or {}
    put(p, 'ebitda_pub', e.get('ebitda')); put(p, 'adj_ebitda_pub', e.get('adj_ebitda')); put(p, 'eb_dda', e.get('dda')); put(p, 'eb_int', e.get('int'))
    # where the statement combines interest and other non-operating items in one line, split them as the EBITDA reconciliation does
    if e.get('int') is not None and abs(nonop) < 1e-9 and abs(int_net - e['int']) > 0.0015 and i.get('int_net') is not None:
        put(p, 'oth_nonop', int_net - e['int']); put(p, 'int_net', e['int']); put(p, 'int_split', 1)
        LOG.append(f'{p}: statement line "{[l for l in i if l.startswith("int")]}" split into interest {e["int"]:.3f} (EBITDA reconciliation) and other {int_net - e["int"]:.3f}')
    a = n.get('adjni') or {}
    put(p, 'adj_ni_pub', a.get('adj_ni')); put(p, 'adj_eps_pub', None if a.get('adj_eps') is None else a['adj_eps'] / f)
    o = n.get('adjop') or {}
    put(p, 'adj_op_pub', o.get('adj_op'))
    # KPIs
    put(p, 'orders', k.get('orders')); put(p, 'backlog', k.get('backlog'))
    mk = k.get('sales_mkt') or {}
    note = r.get('mkt_note') or {}
    src = note if note else mk
    put(p, 'mkt_src', 'note' if note else ('grid_' + (k.get('sales_mkt_unit') or '') if mk else None))
    for m in ('refining', 'chem', 'power', 'defense', 'space', 'other', 'ep'):
        put(p, f'mk_{m}', src.get(m))
    put(p, 'mk_labels', json.dumps(k.get('sales_mkt_labels') or {}))
    # current basis (Defense / Space / Energy & Process)
    d = src.get('defense'); s = src.get('space'); ep = src.get('ep')
    pyk = ((r.get('py') or {}).get('kpi') or {}).get('sales_mkt') or {}
    if d is None and pyk.get('defense') is not None and fy >= 2020:
        d = pyk['defense']; s = pyk.get('space'); put(p, 'cb_recast', 1)
        LOG.append(f'{p}: Defense taken from the following year release table (latest presentation)')
    if d is not None and fy >= 2020:
        if s is None and fy <= 2021: s = 0.0
        if s is not None:
            put(p, 'cb_defense', d); put(p, 'cb_space', s)
            put(p, 'cb_ep', ep if ep is not None else rev - d - s)
    om = k.get('orders_mkt') or {}; bm = k.get('backlog_mkt') or {}
    for m in ('defense', 'space', 'ep', 'refining', 'chem', 'power', 'other'):
        put(p, f'om_{m}', om.get(m)); put(p, f'bm_{m}', bm.get(m))
    rg = k.get('sales_reg') or {}
    if rg.get('us') is not None:
        put(p, 'rg_us', rg['us']); put(p, 'rg_intl', rev - rg['us'] if rg.get('total') is None and k.get('sales_reg_unit') == 'k' else sum(v for kk, v in rg.items() if kk not in ('us', 'total')))
    # XBRL extras
    x = r.get('x') or {}
    if x.get('sh_out') is not None: put(p, 'bs_shares', x['sh_out'])
    elif x.get('sh_issued') is not None and x.get('sh_treasury') is not None: put(p, 'bs_shares', x['sh_issued'] - x['sh_treasury'])
    elif x.get('sh_issued') is not None: put(p, 'bs_shares', x['sh_issued'])
    if x.get('sh_cover'): put(p, 'sh_cover', x['sh_cover']['shares']); put(p, 'sh_cover_date', x['sh_cover']['date'])
    for kk in ('rev', 'ni', 'eps_d', 'ta', 'cfo_ytd'): put(p, f'xb_{kk}', x.get(kk))

# ---------------------------------------------------------------- cash flow
def cf_ytd(fy, q):
    p = str(fy) if q == 4 and REC.get(str(fy)) else qk(fy, q)
    r = REC.get(p) or REC.get(qk(fy, q))
    if not r or not r.get('cf'): return None
    c = r['cf']
    o = {k: N(c.get(k)) for k in ('cfo', 'dep', 'amort', 'pens_amort', 'sbc', 'deftax', 'gain_ppe', 'cont_cons', 'capex', 'capex_proc', 'acq',
                                  'inv_purch', 'inv_red', 'cfi', 'debt_borrow', 'debt_repay', 'fin_lease', 'div', 'stock_iss', 'stock_cost',
                                  'withhold', 'bb', 'cff', 'fx', 'net')}
    o['ni'] = c.get('ni') if c.get('ni') is not None else (r['is'] or {}).get('ni')
    o['net'] = c.get('net')
    o['beg'], o['end'] = c.get('beg'), c.get('end')
    return o

def cf_lines(c):
    o = {'cf_ni': c['ni'], 'cf_dep': c['dep'], 'cf_amort': c['amort'], 'cf_pens': c['pens_amort'], 'cf_sbc': c['sbc'], 'cf_def': c['deftax'],
         'cf_oth': c['gain_ppe'] + c['cont_cons']}
    o['cf_wc'] = c['cfo'] - sum(o.values())
    o['cf_cfo'] = c['cfo']; o['cf_capex'] = c['capex'] + c['capex_proc']; o['cf_acq'] = c['acq']; o['cf_invest'] = c['inv_purch'] + c['inv_red']
    o['cf_oinv'] = c['cfi'] - o['cf_capex'] - c['acq'] - o['cf_invest']; o['cf_cfi'] = c['cfi']
    o['cf_debt'] = c['debt_borrow'] + c['debt_repay'] + c['fin_lease']; o['cf_div'] = c['div']; o['cf_stock'] = c['stock_iss'] + c['stock_cost']
    o['cf_withhold'] = c['withhold']; o['cf_bb'] = c['bb']
    o['cf_ofin'] = c['cff'] - o['cf_debt'] - c['div'] - o['cf_stock'] - c['withhold'] - c['bb']; o['cf_cff'] = c['cff']; o['cf_fx'] = c['fx']
    flows = c['cfo'] + c['cfi'] + c['cff'] + c['fx']
    # FY2019-20: the statement deducts the change in cash classified within assets held for sale before the cash total
    o['cf_hfs'] = round(c['net'] - flows, 6) if c.get('net') is not None and abs(c['net'] - flows) > 0.0015 else 0.0
    o['cf_net'] = flows + o['cf_hfs']
    return o

def x_(p, k): return DATA.get(p, {}).get('x', {}).get(k)

def do_cf():
    for y in range(2006, 2027):
        p = str(y); a = cf_ytd(y, 4)
        if not a: LOG.append(f'{p}: no annual CF'); continue
        for k, v in cf_lines(a).items(): put(p, k, v)
        put(p, 'cf_beg', a['beg']); put(p, 'cf_end', a['end'])
    for y in range(2013, 2028):
        prev = None
        for q in (1, 2, 3, 4):
            if y == 2027 and q > 1: break
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
    ta, tca, tcl = b['ta'], b['tca'], b['tcl']
    cash, invest, ar, unb, inv = b['cash'], N(b.get('invest')), N(b.get('ar')), N(b.get('unbilled')), N(b.get('inv'))
    put(p, 'bs_cash', cash); put(p, 'bs_invest', invest); put(p, 'bs_ar', ar); put(p, 'bs_unb', unb); put(p, 'bs_inv', inv)
    put(p, 'bs_oca', tca - cash - invest - ar - unb - inv); put(p, 'bs_tca', tca)
    ppe, pen, rou, gw, intang = N(b.get('ppe')), N(b.get('pension_asset')), N(b.get('rou')), N(b.get('gw')), N(b.get('intang'))
    put(p, 'bs_ppe', ppe); put(p, 'bs_pen', pen); put(p, 'bs_rou', rou); put(p, 'bs_gw', gw); put(p, 'bs_int', intang)
    put(p, 'bs_onca', ta - tca - ppe - pen - rou - gw - intang); put(p, 'bs_ta', ta)
    std, ap, acc, aco, dep, opl = N(b.get('std')), N(b.get('ap')), N(b.get('accr_comp')), N(b.get('accr_oth')), N(b.get('deposits')), N(b.get('oplease_cl'))
    put(p, 'bs_std', std); put(p, 'bs_ap', ap); put(p, 'bs_accc', acc); put(p, 'bs_acco', aco); put(p, 'bs_dep', dep); put(p, 'bs_opl', opl)
    put(p, 'bs_ocl', tcl - std - ap - acc - aco - dep - opl); put(p, 'bs_tcl', tcl)
    ltd, opln = N(b.get('ltd')), N(b.get('oplease_ncl'))
    tl = b['tl'] if b.get('tl') is not None else b['tle'] - b['eq']
    put(p, 'bs_ltd', ltd); put(p, 'bs_opln', opln); put(p, 'bs_ol', tl - tcl - ltd - opln); put(p, 'bs_tl', tl)
    put(p, 'bs_eq', b['eq']); put(p, 'bs_tle', b['tle'])
    put(p, 'debt_tot', std + ltd)

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
                  ('rev', 'op', 'ni', 'eps_d', 'sh_d', 'adj_ebitda_pub', 'adj_eps_pub', 'cf_cfo', 'cf_wc', 'bs_ta', 'bs_shares', 'debt_tot', 'cb_defense', 'cb_ep', 'orders', 'backlog')})
    print('\n'.join(LOG))
