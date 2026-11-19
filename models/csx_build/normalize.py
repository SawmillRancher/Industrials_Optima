"""Harmonise the extracted CSX data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m; volumes in
thousands of units; revenue per unit in $; shares in m; per share in $).

Basis: every period as originally reported in its own earnings release, with three documented exceptions:
  - Markets on the current basis (Chemicals / Agricultural & Food Products / Minerals / Automotive / Metals & Equipment / Forest
    Products / Fertilizers, introduced in the Q3-2016 release): Q3/15-Q2/16 and FY2015 are taken from the recast prior-year
    comparatives of the Q3-16 ... Q2-17 releases (flag m_recast). Earlier periods keep the legacy markets as memo keys (l_*).
  - Stock split: 3-for-1 on 28-Jun-2021. Shares, EPS and DPS from documents filed before that date are restated (x3 / /3).
  - Q4 = the fourth-quarter release three-month column (never FY - 9M); cash flow is year to date and de-cumulated here.
2006-2008 presentation: "Surface Transportation" expense lines plus a separate "Other Operating Income" line; the consolidated
operating income is used and other operating income is carried as a (negative) item in the other-operating-expense row.
53-week fiscal years: 2010 and 2016 (14-week fourth quarters); calendar quarters from 2017.
"""
import json, glob, os, re
import xbrl

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))
SPLITS = (('2011-06-01', 3.0), ('2021-06-28', 3.0))     # 3-for-1 effective 31-May-2011 (record date; shares distributed 15-Jun-2011) and 28-Jun-2021

def split_factor(date):
    """cumulative restatement factor for share counts in a document filed on `date` (x9 before Jun-2011, x3 Jun-2011 - Jun-2021, x1 after)."""
    f = 1.0
    for d, k in SPLITS:
        if date < d: f *= k
    return f

def N(x): return x or 0.0
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def fyq(p):
    if p.isdigit(): return int(p), 4
    return int('20' + p[-2:]), int(p[1])

def periods():
    out = [str(y) for y in range(2006, 2026)]
    for y in range(2013, 2027):
        out += [qk(y, q) for q in (1, 2, 3, 4) if (y, q) <= (2026, 3)]
    return out

def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

def sf(rec):
    """split factor for share counts in this record (by release date)."""
    return split_factor(rec['sources']['release_date'])

# ---------------------------------------------------------------- markets
CUR = {'chemicals': 'chem', 'agricultural and food products': 'agfood', 'minerals': 'minerals', 'automotive': 'auto',
       'metals and equipment': 'metals', 'forest products': 'forest', 'fertilizers': 'fert', 'total merchandise': 'merch',
       'intermodal': 'intermodal', 'coal': 'coal', 'trucking': 'trucking', 'other': 'other', 'total': 'total'}
LEG = {'agricultural products': 'ag', 'phosphates and fertilizers': 'phos', 'food and consumer': 'food', 'chemicals': 'chem',
       'automotive': 'auto', 'metals': 'metals', 'emerging markets': 'emerging', 'forest products': 'forest', 'minerals': 'minerals',
       'waste and equipment': 'waste', 'total merchandise': 'merch', 'coal': 'coal', 'coke and iron ore': 'coke', 'total coal': 'totcoal',
       'international': 'intl', 'domestic': 'dom', 'total intermodal': 'intermodal', 'total rail': 'rail', 'total': 'total',
       'total surface transportation': 'total', 'intermodal': 'intermodal', 'other': 'other'}
def clean_label(l): return re.sub(r'\s*\([a-z]\)', '', l.strip()).strip().lower()

def is_current_basis(rows):
    labs = {clean_label(l) for l, *_ in rows}
    return 'agricultural and food products' in labs

def put_mkt(p, rows, prefix, mapping, recast=False):
    seen_other = 0
    for lab, vol, rev, rpu in rows:
        L = clean_label(lab)
        k = mapping.get(L)
        if k is None: continue
        if k == 'other':
            seen_other += 1
            if prefix == 'l_' and seen_other == 1 and any(clean_label(x[0]) == 'total rail' for x in rows): k = 'railother'
            elif prefix == 'l_' and seen_other == 2: k = 'imother'
        put(p, f'{prefix}{k}_vol', vol); put(p, f'{prefix}{k}_rev', rev); put(p, f'{prefix}{k}_rpu', rpu if rpu else None)
    if recast: put(p, 'm_recast', 1)

def do_markets(p):
    r = REC[p]; fy, q = fyq(p)
    rows = r.get('mkt') or []
    if not rows: LOG.append(f'{p}: no market table'); return
    if is_current_basis(rows):
        put_mkt(p, rows, 'm_', CUR)
    else:
        put_mkt(p, rows, 'l_', LEG)
        # recast current-basis comparatives from the following year's release
        nxt = REC.get(str(fy + 1) if p.isdigit() else qk(fy + 1, q))
        if nxt and nxt.get('py', {}).get('mkt') and is_current_basis(nxt['py']['mkt']):
            put_mkt(p, nxt['py']['mkt'], 'm_', CUR, recast=True)
            LOG.append(f'{p}: current-basis markets from the recast comparatives of the {nxt["period"]} release')
    x = DATA[p]['x']
    # aggregates on every basis: merchandise (incl. automotive before Q2-10), coal (total coal incl. coke & iron ore before Q2-10),
    # intermodal, trucking, other (rail other + intermodal other before Q2-10)
    if 'm_merch_rev' in x:
        for k in ('merch', 'coal', 'intermodal', 'trucking', 'other', 'total'):
            for s in ('vol', 'rev', 'rpu'):
                if f'm_{k}_{s}' in x: put(p, f'a_{k}_{s}', x[f'm_{k}_{s}'])
        put(p, 'a_basis', 'current')
    else:
        legacy_auto_out = 'l_rail_rev' in x        # 2006 - Q1/10 layout: automotive outside merchandise, intermodal split intl / dom
        mv = N(x.get('l_merch_vol')) + (N(x.get('l_auto_vol')) if legacy_auto_out else 0.0)
        mr = N(x.get('l_merch_rev')) + (N(x.get('l_auto_rev')) if legacy_auto_out else 0.0)
        put(p, 'a_merch_vol', mv); put(p, 'a_merch_rev', mr); put(p, 'a_merch_rpu', mr / mv * 1000 if mv else None)
        ck = 'totcoal' if 'l_totcoal_rev' in x else 'coal'
        put(p, 'a_coal_vol', x.get(f'l_{ck}_vol')); put(p, 'a_coal_rev', x.get(f'l_{ck}_rev')); put(p, 'a_coal_rpu', x.get(f'l_{ck}_rpu'))
        put(p, 'a_intermodal_vol', x.get('l_intermodal_vol')); put(p, 'a_intermodal_rev', x.get('l_intermodal_rev')); put(p, 'a_intermodal_rpu', x.get('l_intermodal_rpu'))
        oth = N(x.get('l_railother_rev')) if legacy_auto_out else N(x.get('l_other_rev'))      # intermodal "Other" is inside Total Intermodal
        put(p, 'a_other_rev', oth)
        put(p, 'a_total_vol', x.get('l_total_vol')); put(p, 'a_total_rev', x.get('l_total_rev')); put(p, 'a_total_rpu', x.get('l_total_rpu'))
        put(p, 'a_basis', 'legacy2006' if legacy_auto_out else ('legacy2013' if 'l_minerals_rev' in x else 'legacy2010'))
    # company-published total check helper
    put(p, 'mkt_total_pub', x.get('a_total_rev'))

# ---------------------------------------------------------------- income statement
def do_pl(p):
    r = REC.get(p)
    if not r: LOG.append(f'{p}: no record'); return
    i = r['is']; f = sf(r)
    put(p, 'rev', i['rev']); put(p, 'labor', i['labor']); put(p, 'pso', i['mso']); put(p, 'fuel', i['fuel']); put(p, 'dep', i['dep'])
    put(p, 'rents', i['rents']); put(p, 'inland', N(i.get('inland')))
    put(p, 'gain_disp', N(i.get('gain_disp'))); put(p, 'impair', N(i.get('impair'))); put(p, 'restr', N(i.get('restr')))
    oth = N(i.get('conrail')) + sum(v for _, v in i.get('other_exp_lines', [])) - N(i.get('oth_oi'))
    labels = (['Conrail Rents, Fees and Services'] if i.get('conrail') else []) + [l for l, v in i.get('other_exp_lines', []) if v] + \
             (['Other Operating Income (Expense) (shown below Surface Transportation operating income; negative = income)'] if i.get('oth_oi') else [])
    put(p, 'oth_exp', oth); put(p, 'oth_exp_lab', '; '.join(labels))
    put(p, 'tot_exp', i['tot_exp'] - N(i.get('oth_oi')))        # consolidated total expense (2006-08: surface transportation expense - other operating income)
    put(p, 'oi', i['oi']); put(p, 'oth_inc', N(i.get('oth_inc'))); put(p, 'int_exp', -N(i.get('int_exp'))); put(p, 'debt_rep', -N(i.get('debt_rep')))
    put(p, 'ebt', i['ebt']); put(p, 'tax', -N(i.get('tax'))); put(p, 'disc_ops', N(i.get('disc_ops')))
    put(p, 'cont_ops', i['ebt'] + N(i.get('tax'))); put(p, 'ni', i['ni'])
    sh = i.get('sh_d')
    if sh is not None:
        if i.get('sh_unit') == 'thousands': sh = sh / 1000.0
        put(p, 'sh_d', sh * f)
    if i.get('eps_d') is not None: put(p, 'eps_d', i['eps_d'] / f)
    if i.get('eps_cont') is not None: put(p, 'eps_cont', i['eps_cont'] / f)
    put(p, 'op_margin_pub', i['op_margin'] / 100.0 if i.get('op_margin') is not None else None)
    put(p, 'oi_restated', MAN['restated_2017_asu_2017_07']['oi_restated'].get(p))
    put(p, 'split_factor', f)
    # dividends per share
    fy, q = fyq(p)
    dps = i.get('dps')
    if dps is not None: put(p, 'dps', dps / f); put(p, 'dps_src', 'release')
    else:
        C = ['CommonStockDividendsPerShareCashPaid', 'CommonStockDividendsPerShareDeclared']
        def xq(kind, k=None):            # XBRL per-share fact restated for splits by its own filing date
            for c in C:
                r_ = xbrl.value(c, fy, kind, k, with_filed=True)
                if r_ is not None: return r_[0] / split_factor(r_[1])
            return None
        if p.isdigit():
            v = xq('FY')
            if v is None:
                qs = [xq('Q', k) for k in (1, 2, 3, 4)]
                v = sum(qs) if all(z is not None for z in qs) else None
        else:
            v = xq('Q', q)
            if v is None and q == 4:
                a = xq('FY'); qs = [xq('Q', k) for k in (1, 2, 3)]
                if a is not None and all(z is not None for z in qs): v = a - sum(qs)
        if v is not None:
            put(p, 'dps', v); put(p, 'dps_src', 'xbrl')
    # memo operating data
    fu = r.get('fuel') or {}
    put(p, 'fuel_gal', fu.get('gallons')); put(p, 'fuel_ppg', fu.get('ppg')); put(p, 'fuel_loco', fu.get('loco'))
    if fu.get('loco') is not None: put(p, 'fuel_nonloco', i['fuel'] - fu['loco'])
    fs = r.get('fsc') or {}
    put(p, 'fsc_rev', fs.get('fsc')); put(p, 'fsc_lag', fs.get('lag'))
    co = r.get('coal') or {}
    put(p, 'coal_dom', co.get('domestic')); put(p, 'coal_exp', co.get('export')); put(p, 'coal_tons', co.get('total'))
    em = r.get('emp') or {}
    put(p, 'emp_avg', em.get('avg_total'))
    st = r.get('stats') or {}
    put(p, 'rtm', st.get('rtm')); put(p, 'gtm', st.get('gtm')); put(p, 'velocity', st.get('velocity')); put(p, 'dwell', st.get('dwell'))
    put(p, 'fuel_eff', st.get('fuel_eff'))
    sg = r.get('seg') or {}
    if sg.get('rev'):
        put(p, 'seg_rail_rev', sg['rev']['rail']); put(p, 'seg_im_rev', sg['rev']['intermodal'])
        if sg.get('oi'): put(p, 'seg_rail_oi', sg['oi']['rail']); put(p, 'seg_im_oi', sg['oi']['intermodal'])
    put(p, 'fcf_pub_ytd', r.get('fcf_pub'))      # company FCF is printed year to date; de-cumulated in do_cf
    x = r.get('x') or {}
    put(p, 'sbc', x.get('sbc')); put(p, 'x_oi', x.get('oi')); put(p, 'x_ni', x.get('ni')); put(p, 'x_rev', x.get('rev')); put(p, 'x_ta', x.get('ta'))
    fy_, q_ = fyq(p)
    if fy_ >= 2009:                      # XBRL cross-checks only where the 10-K / 10-Q itself was tagged (2009+); earlier facts are restated comparatives
        xe = xbrl.value('EarningsPerShareDiluted', fy_, 'FY' if p.isdigit() else 'Q', None if p.isdigit() else q_, with_filed=True)
        if xe: put(p, 'x_eps', xe[0] / split_factor(xe[1]))
    else:
        for k in ('x_oi', 'x_ni', 'x_rev', 'x_ta'): DATA[p]['x'].pop(k, None)
    put(p, 'employees_ye', x.get('employees'))
    put(p, 'goodwill', x.get('goodwill')); put(p, 'intang_gw', x.get('intang_gw')); put(p, 'ar', x.get('ar'))
    # company adjusting items (manual_items.json, categorised; pre-tax amounts; EPS items as published, split-adjusted here)
    a = MAN['adjusting_items'].get(p)
    if a:
        put(p, 'adj_pub', 1)
        put(p, 'oa_impair', N(a.get('impair_pre'))); put(p, 'oa_restr', N(a.get('restr_pre'))); put(p, 'oa_gain', N(a.get('gain_pre'))); put(p, 'oa_other', N(a.get('other_pre')))
        put(p, 'oa_nonop', N(a.get('nonop_pre'))); put(p, 'oa_tax', N(a.get('tax_items'))); put(p, 'oa_basis', N(a.get('basis_pre')))
        put(p, 'oa_lab', a.get('label'))
        if a.get('adj_oi_pub') is not None: put(p, 'adj_oi_pub', a['adj_oi_pub'])
        if a.get('adj_ni_pub') is not None: put(p, 'adj_ni_pub', a['adj_ni_pub'])
        if a.get('adj_eps_pub') is not None: put(p, 'adj_eps_pub', a['adj_eps_pub'] / f)
        if a.get('adj_eps_cont_pub') is not None: put(p, 'adj_eps_pub', a['adj_eps_cont_pub'] / f)
    else:
        for k in ('oa_impair', 'oa_restr', 'oa_gain', 'oa_other', 'oa_nonop', 'oa_tax', 'oa_basis'): put(p, k, 0.0)

# ---------------------------------------------------------------- cash flow
def cf_ytd(p):
    r = REC.get(p)
    if not r or not r.get('cf'): return None
    c = r['cf']
    o = {k: N(c.get(k)) for k in ('ni', 'dep', 'deftax', 'impair', 'cfo', 'capex', 'sti_buy', 'sti_sell', 'disp', 'acq', 'cfi', 'bb', 'div',
                                   'debt_iss', 'debt_rep', 'std_net', 'options', 'cff', 'net')}
    o['beg'], o['end'] = c.get('beg'), c.get('end')
    o['fcf_pub'] = r.get('fcf_pub')
    return o

def cf_lines(c):
    o = {'cf_ni': c['ni'], 'cf_dep': c['dep'], 'cf_def': c['deftax'], 'cf_impair': c['impair']}
    o['cf_oth'] = c['cfo'] - c['ni'] - c['dep'] - c['deftax'] - c['impair']
    o['cf_cfo'] = c['cfo']; o['cf_capex'] = c['capex']; o['cf_disp'] = c['disp']; o['cf_sti'] = c['sti_buy'] + c['sti_sell']; o['cf_acq'] = c['acq']
    o['cf_oinv'] = c['cfi'] - c['capex'] - c['disp'] - o['cf_sti'] - c['acq']; o['cf_cfi'] = c['cfi']
    o['cf_bb'] = c['bb']; o['cf_div'] = c['div']; o['cf_debt_iss'] = c['debt_iss']; o['cf_debt_rep'] = c['debt_rep']; o['cf_std'] = c['std_net']
    o['cf_ofin'] = c['cff'] - c['bb'] - c['div'] - c['debt_iss'] - c['debt_rep'] - c['std_net']; o['cf_cff'] = c['cff']
    o['cf_net'] = c['cfo'] + c['cfi'] + c['cff']
    o['cf_fcf_pub'] = c['fcf_pub']
    o['cf_std_bal'] = None
    return o

def do_cf():
    for y in range(2006, 2026):
        p = str(y); a = cf_ytd(p)
        if not a: LOG.append(f'{p}: no annual CF'); continue
        for k, v in cf_lines(a).items(): put(p, k, v)
        put(p, 'cf_beg', a['beg']); put(p, 'cf_end', a['end'])
    for y in range(2013, 2027):
        prev = None
        for q in (1, 2, 3, 4):
            if (y, q) > (2026, 3): break
            p = qk(y, q); cur = cf_ytd(p)
            if cur is None: LOG.append(f'{p}: no YTD CF'); prev = None; continue
            lc = cf_lines(cur)
            if q == 1: d = lc; beg = cur['beg']
            else:
                if prev is None: continue
                d = {k: (lc[k] - prev[0][k]) if (lc[k] is not None and prev[0][k] is not None) else None for k in lc}; beg = prev[1]
            for k, v in d.items(): put(p, k, v)
            put(p, 'cf_beg', beg); put(p, 'cf_end', cur['end'])
            prev = (lc, cur['end'])

# ---------------------------------------------------------------- balance sheet
def do_bs(p):
    r = REC.get(p)
    if not r or not r.get('bs'): return
    b = r['bs']; x = DATA[p]['x']
    ta = b['ta']
    if b.get('cash') is not None:
        cash, sti = b['cash'], N(b.get('sti'))
    else:                                   # 2010 - Q2/13 releases combine cash and short-term investments; cash from the cash-flow statement
        cash = x.get('cf_end'); sti = N(b.get('cash_sti')) - N(cash)
        put(p, 'bs_cash_combined', 1)
    put(p, 'bs_cash', cash); put(p, 'bs_sti', sti)
    tca = b.get('tca')
    if tca is None:                         # condensed: other current assets printed
        oca = next((v for l, v in b['lines_raw'] if l.lower().startswith('other current assets')), None)
        tca = N(cash) + sti + N(oca)
    else:
        oca = tca - N(cash) - sti
    put(p, 'bs_oca', oca); put(p, 'bs_tca', tca)
    put(p, 'bs_ppe', b['ppe']); affil = N(b.get('affil')) + N(b.get('conrail')); put(p, 'bs_affil', affil)
    put(p, 'bs_olta', ta - tca - b['ppe'] - affil); put(p, 'bs_ta', ta)
    cmltd = N(b.get('cmltd')) + N(b.get('std'))
    tcl = b.get('tcl')
    if tcl is None:
        ocl = next((v for l, v in b['lines_raw'] if l.lower().startswith('other current liabilities')), None)
        tcl = cmltd + N(ocl)
    else:
        ocl = tcl - cmltd
    put(p, 'bs_cmltd', cmltd); put(p, 'bs_ocl', ocl); put(p, 'bs_tcl', tcl)
    put(p, 'bs_ltd', b['ltd']); put(p, 'bs_dit', N(b.get('dit')))
    te = b['te']; tl = b.get('tl') if b.get('tl') is not None else b['tle'] - te
    put(p, 'bs_oltl', tl - tcl - b['ltd'] - N(b.get('dit'))); put(p, 'bs_tl', tl)
    put(p, 'bs_te', te); put(p, 'bs_nci', N(b.get('nci'))); put(p, 'bs_tle', b['tle'])
    put(p, 'debt_tot', cmltd + b['ltd'])
    xx = r.get('x') or {}
    sh = xx.get('sh_out') or xx.get('sh_out_cover')
    if sh is not None:
        put(p, 'bs_shares', sh * sf(r))
        put(p, 'bs_shares_src', 'balance sheet' if xx.get('sh_out') else f"cover page {xx.get('sh_out_cover_date')}")

def run():
    load()
    for p in periods():
        if p not in REC: LOG.append(f'{p}: missing'); continue
        do_pl(p); do_markets(p)
    do_cf()
    for p in periods():
        if p in REC: do_bs(p)
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: (round(x[k], 2) if isinstance(x.get(k), float) else x.get(k)) for k in
                  ('rev', 'oi', 'ni', 'eps_d', 'sh_d', 'dps', 'a_basis', 'm_chem_rev', 'm_recast', 'cf_cfo', 'cf_oth', 'bs_cash', 'bs_ta', 'debt_tot', 'bs_shares', 'fuel_gal', 'emp_avg')})
    print('\n'.join(LOG))
