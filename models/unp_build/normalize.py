"""Harmonise the extracted Union Pacific data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m).

Basis: every period as originally reported in its own earnings release, with these exceptions:
  - FY2006-07 revenue split and expense lines: FY2008 10-K re-presentation (manual_items 'recast_2006_2007'); totals unchanged.
  - 2018 business groups on the Bulk / Industrial / Premium basis: prior-year comparatives of the 2019 releases (seg_py), flagged.
  - Share-based compensation, shares outstanding: XBRL company facts (data/_xbrl.json).
Shares / per-share data before the 2-for-1 split of 27-May-2014 are restated (documents filed before 9-Jun-2014: shares x2, per-share / 2).
Cash flow: releases give year-to-date statements; discrete quarters derived (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M).
Adjusted measures: company 'Financial Performance' tables (manual_items 'adjusted_items'); other periods adjusted = GAAP.
"""
import json, glob, os
import xbrl

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))
SPLIT_DATE = '2014-06-09'

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

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_') and not k.startswith('nsc'): REC[k] = json.load(open(f))

GROUPS3 = ['bulk', 'industrial', 'premium']
SUBS = ['grain', 'fert', 'food', 'coalren', 'chemplas', 'metals', 'forest', 'energyspec', 'auto', 'intermodal']
LEG6 = ['ag', 'auto', 'chem', 'energy', 'indprod', 'intermodal']
LEG4 = ['ag', 'energy', 'industrial', 'premium']
CAT_ROW = {'ACQ': 'acq', 'IMPAIR': 'impair', 'GAIN': 'gain', 'OTHER': 'other', 'TAXREFORM': 'other'}

def split_factor(p):
    r = REC.get(p)
    d = (r or {}).get('sources', {}).get('release_date', '2099')
    return 2.0 if d < SPLIT_DATE else 1.0

def do_pl(p):
    r = REC.get(p)
    if not r: LOG.append(f'{p}: no record'); return
    fy, q = fyq(p)
    i = r['is']; sf = split_factor(p)
    rc = MAN['recast_2006_2007'].get(p)
    for k in ('frt', 'oth_rev', 'rev', 'comp', 'fuel', 'psm', 'dep', 'rents', 'oth_exp', 'opex', 'oi'):
        v = rc[k] if rc else i.get(k)
        put(p, k, v)
    if rc:
        put(p, 'recast', 1)
        for k, src in (('l_swb', 'comp'), ('l_rents', 'rents'), ('l_dep', 'dep'), ('l_fuelut', 'fuel'), ('l_mats', 'mats'), ('l_pso', 'psm')):
            put(p, k, i.get(src))
    for k in ('oth_inc', 'int', 'ebt', 'tax', 'ni'): put(p, k, i.get(k))
    for k in ('eps_b', 'eps_d', 'dps'):
        if i.get(k) is not None: put(p, k, i[k] / sf)
    sh = {'sh_b': i.get('sh_b', r['ops'].get('sh_b')), 'sh_d': i.get('sh_d', r['ops'].get('sh_d'))}
    for k, v in sh.items():
        if v is not None: put(p, k, v * sf)
    if sf != 1.0: put(p, 'split_adj', 1)
    put(p, 'or_pub', i.get('or')); put(p, 'etr_pub', i.get('etr'))
    # business groups
    s, spy = r['seg'], r.get('seg_py', {})
    if 'bulk' in s:
        for g in GROUPS3 + SUBS + ['total']:
            for m in ('rev', 'cars', 'arpc'):
                put(p, f'g_{g}_{m}', s.get(g, {}).get(m))
    elif fy in (2018, 2019):
        for g in LEG4:
            for m in ('rev', 'cars', 'arpc'): put(p, f's4_{g}_{m}', s.get(g, {}).get(m))
        for m in ('rev', 'cars', 'arpc'): put(p, f'g_total_{m}', s.get('total', {}).get(m))
    else:
        for g in LEG6:
            for m in ('rev', 'cars', 'arpc'): put(p, f's6_{g}_{m}', s.get(g, {}).get(m))
        for m in ('rev', 'cars', 'arpc'): put(p, f'g_total_{m}', s.get('total', {}).get(m))
    if p in ('2006', '2007') or (fy <= 2007):
        put(p, 'frt', s.get('total', {}).get('rev') if not rc else rc['frt'])
    # 2019 on the Bulk / Industrial / Premium basis (with commodity sub-lines) from the 2020 releases' prior-year comparatives
    if fy == 2020 and 'bulk' in spy:
        tgt = '2019' if p.isdigit() else qk(2019, q)
        for g in GROUPS3 + SUBS:
            for m in ('rev', 'cars', 'arpc'): put(tgt, f'g_{g}_{m}', spy.get(g, {}).get(m))
        put(tgt, 'g3_recast', 1)
    # operating statistics
    o = r['ops']
    for k in ('gtm', 'emp', 'fuel_px', 'gallons', 'fuel_rate', 'rtm', 'speed', 'dwell', 'car_inv', 'velocity', 'train_len', 'wf_prod', 'loco_prod'):
        put(p, k, o.get(k))
    ex = r.get('extra') or {}
    put(p, 'fs_rev', ex.get('fuel_surcharge_rev'))
    # non-GAAP memo (TTM / point-in-time tables)
    ng = r.get('ngaap', {})
    for k in ('adj_ebitda_ttm', 'ebitda_ttm', 'adj_debt', 'lease_liab', 'lease_int_ttm', 'roic_pub', 'adj_lev_pub', 'debt_cap_pub', 'adj_debt_cap_pub'):
        put(p, k, ng.get(k))
    # adjusted items (company tables)
    a = MAN['adjusted_items'].get(p)
    tot = {c: 0.0 for c in ('acq', 'impair', 'gain', 'other')}; labels = {c: [] for c in tot}
    oth_inc_adj, tax_adj, ni_adj, eps_adj = 0.0, 0.0, 0.0, 0.0
    if a:
        for it in a['items']:
            c = CAT_ROW.get(it['cat'])
            if c: tot[c] += N(it.get('oi')); labels[c].append(f"{it['label']} {N(it.get('oi')):+.0f}")
            oth_inc_adj += N(it.get('oth_inc')); tax_adj += N(it.get('tax_exp')); ni_adj += N(it.get('ni')); eps_adj += N(it.get('eps'))
        pub = a['pub']
        put(p, 'adj_oi_pub', pub.get('adj_oi')); put(p, 'adj_ni_pub', pub.get('adj_ni')); put(p, 'adj_eps_pub', pub.get('adj_eps')); put(p, 'adj_or_pub', pub.get('adj_or'))
        put(p, 'adj_published', 1)
        put(p, 'adj_lab', '; '.join(f"{it['label']}: OI {N(it.get('oi')):+.0f}, other income {N(it.get('oth_inc')):+.0f}, tax {N(it.get('tax_exp')):+.0f}, NI {N(it.get('ni')):+.0f}, EPS {N(it.get('eps')):+.2f}" for it in a['items']) + f" [{a['src']}]")
        if a.get('derived'): put(p, 'adj_derived', 1)
        if a.get('retro'): put(p, 'adj_retro', 1)
    for c in tot:
        put(p, f'oa_{c}', tot[c]); put(p, f'oa_{c}_lab', '; '.join(labels[c]))
    put(p, 'oa_othinc', oth_inc_adj); put(p, 'oa_tax', tax_adj); put(p, 'oa_ni', ni_adj); put(p, 'oa_eps', eps_adj)
    # XBRL extras
    if fy >= 2009:
        sbc = xbrl.value('ShareBasedCompensation', fy, 'YTD', q) if not p.isdigit() else xbrl.value('ShareBasedCompensation', fy, 'FY')
        if sbc is None and not p.isdigit(): sbc = xbrl.value('AllocatedShareBasedCompensationExpense', fy, 'Q', q)
        if sbc is None and p.isdigit(): sbc = xbrl.value('AllocatedShareBasedCompensationExpense', fy, 'FY')
        put(p, 'sbc_src', sbc)
        so = xbrl.value('CommonStockSharesOutstanding', fy, 'I', q, scale=1e6)
        put(p, 'sh_out', so)

# ---------------------------------------------------------------- cash flow
def cf_ytd(fy, q):
    p = str(fy) if q == 4 else qk(fy, q)
    r = REC.get(p) or REC.get(qk(fy, q))
    if not r or not r.get('cf'): return None
    c = r['cf']
    o = {k: N(c.get(k)) for k in ('ni', 'dep', 'dtax', 'oth_op', 'cfo', 'capex', 'sti_buy', 'sti_mat', 'oth_inv', 'cfi', 'bb', 'div', 'debt_iss', 'debt_rep',
                                  'debt_exch', 'oth_fin', 'cff', 'net', 'fcf')}
    o['beg'], o['end'] = c.get('beg'), c.get('end')
    return o

KEYS = ['cf_ni', 'cf_dep', 'cf_dtax', 'cf_oth', 'cf_cfo', 'cf_capex', 'cf_sti', 'cf_oinv', 'cf_cfi', 'cf_bb', 'cf_div', 'cf_debt_iss', 'cf_debt_rep', 'cf_ofin', 'cf_cff', 'cf_net', 'fcf_pub']
def cf_lines(c):
    o = {'cf_ni': c['ni'], 'cf_dep': c['dep'], 'cf_dtax': c['dtax'], 'cf_oth': c['cfo'] - c['ni'] - c['dep'] - c['dtax'], 'cf_cfo': c['cfo'],
         'cf_capex': c['capex'], 'cf_sti': c['sti_buy'] + c['sti_mat'], 'cf_cfi': c['cfi']}
    o['cf_oinv'] = c['cfi'] - c['capex'] - o['cf_sti']
    o['cf_bb'] = c['bb']; o['cf_div'] = c['div']; o['cf_debt_iss'] = c['debt_iss']; o['cf_debt_rep'] = c['debt_rep'] + c['debt_exch']; o['cf_cff'] = c['cff']
    o['cf_ofin'] = c['cff'] - c['bb'] - c['div'] - c['debt_iss'] - o['cf_debt_rep']
    o['cf_net'] = c['cfo'] + c['cfi'] + c['cff']
    o['fcf_pub'] = c['cfo'] + c['cfi'] + c['div']
    return o

def do_cf():
    for y in range(2006, 2026):
        p = str(y); a = cf_ytd(y, 4)
        if not a: LOG.append(f'{p}: no annual CF'); continue
        for k, v in cf_lines(a).items(): put(p, k, v)
        put(p, 'cf_beg', a['beg']); put(p, 'cf_end', a['end'])
        if a['end'] is None and a['beg'] is None:   # 2005-07 releases: no cash balances in the CF; use the balance sheet
            b = REC[p]['bs']; put(p, 'cf_end', b.get('cash'))
            pb = REC.get(str(y - 1), {}).get('bs', {}); put(p, 'cf_beg', pb.get('cash'))
    for y in range(2013, 2027):
        prev = None
        for q in (1, 2, 3, 4):
            if y == 2026 and q == 4: break
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
    # SBC: YTD -> discrete
    for y in range(2013, 2027):
        prev = 0.0
        for q in (1, 2, 3, 4):
            if y == 2026 and q == 4: break
            p = qk(y, q); v = DATA.get(p, {}).get('x', {}).get('sbc_src')
            if v is None: prev = None; continue
            ytd = xbrl.value('ShareBasedCompensation', y, 'YTD', q)
            if ytd is not None and prev is not None: put(p, 'sbc', ytd - prev); prev = ytd
            else: put(p, 'sbc', v); prev = None
    for y in range(2009, 2026):
        v = DATA.get(str(y), {}).get('x', {}).get('sbc_src')
        if v is not None: put(str(y), 'sbc', v)

# ---------------------------------------------------------------- balance sheet
def do_bs(p):
    r = REC.get(p)
    if not r or not r.get('bs'): return
    b = r['bs']
    put(p, 'bs_cash', b.get('cash')); put(p, 'bs_sti', N(b.get('sti'))); put(p, 'bs_oca', b.get('oca')); put(p, 'bs_inv', b.get('inv')); put(p, 'bs_ppe', b.get('ppe'))
    put(p, 'bs_rou', N(b.get('rou'))); put(p, 'bs_oa', N(b.get('oa')) + N(b.get('rou'))); put(p, 'bs_ta', b.get('ta'))
    put(p, 'bs_std', b.get('std')); put(p, 'bs_ocl', b.get('ocl')); put(p, 'bs_ltd', b.get('ltd')); put(p, 'bs_olease', N(b.get('olease')))
    put(p, 'bs_dtl', b.get('dtl')); put(p, 'bs_oltl', N(b.get('oltl')) + N(b.get('olease')))
    put(p, 'bs_tl', b.get('tl') if b.get('tl') is not None else (b['tle'] - b['eq'] if b.get('tle') is not None and b.get('eq') is not None else None))
    put(p, 'bs_eq', b.get('eq')); put(p, 'bs_tle', b.get('tle'))
    ce = DATA.get(p, {}).get('x', {}).get('cf_end')
    if ce is not None and b.get('cash') is not None: put(p, 'cash_restricted', round(ce - b['cash'], 3))
    put(p, 'debt_tot', N(b.get('std')) + N(b.get('ltd')))

def run():
    load()
    for p in periods():
        do_pl(p)
    do_cf()
    for p in periods():
        do_bs(p)
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: round(x[k], 2) if isinstance(x.get(k), float) else x.get(k) for k in
                  ('rev', 'oi', 'ni', 'eps_d', 'sh_d', 'g_bulk_rev', 'g_total_cars', 'cf_cfo', 'cf_oth', 'cf_end', 'bs_ta', 'debt_tot', 'sbc', 'sh_out', 'adj_eps_pub', 'fs_rev')})
    print('\n'.join(LOG))
