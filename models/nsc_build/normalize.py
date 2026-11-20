"""Harmonise the extracted Norfolk Southern data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m; units in
thousands; revenue per unit in $; shares in m).

Basis: every period as originally reported in its own earnings release (statements of income, balance sheet, year-to-date cash flow).
Exceptions, by source priority:
  - FY2006-07 operating-expense classification: the FY2008 10-K recast 2006-07 into the five classifications used since 2008
    (compensation & benefits; purchased services & rents; fuel; depreciation; materials & other); the model uses that recast for the
    expense lines (totals unchanged) and keeps the original seven-line presentation as memo keys.
  - Revenues by commodity group: the three groups (merchandise, intermodal, coal) are on the income statement throughout; the
    merchandise sub-groups, units and revenue per unit come from the 10-Q / 10-K MD&A tables (Q4 = year - nine months; Q4 revenue
    per unit derived as revenue / units).
  - Share-based compensation, deferred taxes (cash-flow statement), dividends declared per share and shares outstanding: XBRL
    company facts where the releases omit them.
Cash flow: releases give year-to-date statements; discrete quarters derived (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M).
Adjusted measures: NSC publishes reconciliations only when items exist (2017 tax reform, 2020 locomotive / investment impairments,
2023+ Eastern Ohio incident, 2024 railway line sales / restructuring / shareholder advisory costs / deferred-tax adjustment,
2025+ merger-related expenses). Other periods: adjusted = GAAP, flagged.
"""
import json, glob, os, re
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
        if not k.startswith('_'): REC[k] = json.load(open(f))

# adjusting-item categories (company reconciliation labels -> model lines)
CAT = [('MERGER', r'merger'), ('EOI', r'eastern ohio|incident'), ('RESTR', r'restructuring'), ('GAIN', r'railway line sales|line sales'),
       ('ADVIS', r'shareholder advisory'), ('TAXD', r'tax reform|deferred tax|tax adjustment'), ('IMPAIR', r'locomotive|impairment|asset disposal')]
def cat(lab):
    L = lab.lower()
    return next((c for c, p in CAT if re.search(p, L)), 'OTHER')

GROUPS = ['coal', 'merch', 'im', 'total', 'chem', 'agr', 'metals', 'auto', 'paper', 'forest']

def do_pl(p):
    r = REC.get(p)
    if not r: LOG.append(f'{p}: no record'); return
    fy, q = fyq(p)
    i = r['is']
    for k in ('rev_coal', 'rev_merch', 'rev_im', 'rev', 'comp', 'psr', 'fuel', 'dep', 'mat', 'merger', 'restr', 'eoi', 'loss_disp',
              'opex', 'oi', 'oth_inc', 'int', 'ebt', 'tax', 'tax_cur', 'tax_def', 'ni', 'eps_b', 'eps_d', 'sh_b', 'sh_d'):
        put(p, k, i.get(k))
    for k in ('merger', 'restr', 'eoi', 'loss_disp'):
        if i.get(k) is None: put(p, k, 0.0)
    # FY2006-07: original seven-line expense presentation kept as memo; five-line classification from the FY2008 10-K recast
    if i.get('conrail') is not None or i.get('claims') is not None:
        for k in ('psr', 'conrail', 'claims', 'oth_opex', 'mat'):
            if i.get(k) is not None: put(p, f'orig_{k}', i[k])
        rc = r.get('is_recast')
        if rc:
            for k in ('comp', 'psr', 'fuel', 'dep', 'mat'): put(p, k, rc.get(k))
            put(p, 'opex_recast_basis', 1)
            if abs(N(rc.get('opex')) - N(i.get('opex'))) > 0.5: LOG.append(f'{p}: recast opex total {rc.get("opex")} vs original {i.get("opex")}')
        else:
            put(p, 'psr', N(i.get('psr')) + N(i.get('conrail'))); put(p, 'mat', N(i.get('claims')) + N(i.get('oth_opex')))
            LOG.append(f'{p}: no FY2008 10-K recast found; purchased services & rents = materials, services & rents + Conrail rents; materials & other = casualties + other')
    put(p, 'oth_opex_lines', '; '.join(f'{l} {v:,.0f}' for l, v in i.get('other_lines', []) if v))
    # market groups
    mg = r.get('mg') or {}
    for meas in ('rev', 'units', 'rpu'):
        for g in GROUPS:
            v = (mg.get(meas) or {}).get(g)
            if v is not None: put(p, f'mg_{meas}_{g}', v)
    if mg.get('units') and not mg.get('rpu'):
        for g in GROUPS:
            u = mg['units'].get(g); rv = (mg.get('rev') or {}).get(g)
            if u and rv is not None: put(p, f'mg_rpu_{g}', round(rv * 1000.0 / u, 1))
        put(p, 'mg_rpu_derived', 1)
    if mg.get('rev') and mg['rev'].get('merch') is None and all(mg['rev'].get(k) is not None for k in ('chem', 'agr', 'metals', 'auto')):
        put(p, 'mg_rev_merch', sum(mg['rev'][k] for k in ('chem', 'agr', 'metals', 'auto', 'paper', 'forest') if mg['rev'].get(k) is not None))
    kpi = r.get('kpi') or {}
    for k, v in (kpi.get('coal_tons') or {}).items(): put(p, 'coal_' + k.replace(' ', '_'), v)
    for k, v in (kpi.get('im_units') or {}).items(): put(p, 'im_' + k, v)
    od = kpi.get('opex_detail') or {}
    for k, kk in (('purchased services', 'od_ps'), ('equipment rents', 'od_rents'), ('materials', 'od_mat'), ('claims', 'od_claims'), ('other', 'od_other')):
        if od.get(k) is not None: put(p, kk, od[k])
    if r.get('fsc') is not None: put(p, 'fsc', r['fsc'])
    # non-GAAP
    ng = r.get('ngaap')
    if ng:
        for k in ('adj_oi_pub', 'adj_or_pub', 'adj_eps_pub', 'adj_ni_pub', 'adj_opex_pub', 'fsc_pub', 'rev_xfsc_pub'): put(p, k, ng.get(k))
        if ng.get('adj_or_pub') is not None: put(p, 'adj_or_pub', ng['adj_or_pub'] / 100.0)
        items = [it for it in ng['items'] if it['after'] and it['after'].startswith('income from railway')]
        put(p, 'adj_items_oi', sum(it['value'] for it in items))
        put(p, 'adj_items_lab', '; '.join(f"{it['label'].strip()} {it['value']:+,.0f}" for it in items))
        eps_items = [it for it in ng['items'] if it['after'] and it['after'].startswith('diluted earnings')]
        put(p, 'adj_items_eps', sum(it['value'] for it in eps_items) if eps_items else None)
        put(p, 'adj_items_eps_lab', '; '.join(f"{it['label'].strip()} {it['value']:+.2f}" for it in eps_items))
        put(p, 'adj_src', ng.get('source'))
    put(p, 'adj_published', 1 if ng else 0)
    # XBRL extras
    x = r.get('x') or {}
    put(p, 'dps', x.get('dps_q')); put(p, 'sh_out_xb', x.get('sh_out')); put(p, 'oi_xb', x.get('oi_xb')); put(p, 'ni_xb', x.get('ni_xb'))
    if i.get('sh_b') is None and x.get('sh_b_xb'): put(p, 'sh_b', x['sh_b_xb']); put(p, 'sh_b_src', 'xbrl')
    if i.get('eps_b') is None and x.get('eps_b_xb'): put(p, 'eps_b', x['eps_b_xb'])

# ---------------------------------------------------------------- cash flow
def cf_ytd(fy, q):
    p = str(fy) if q == 4 and fy <= 2025 else qk(fy, q)
    r = REC.get(p) or REC.get(qk(fy, q))
    if not r or not r.get('cf'): return None
    c = r['cf']
    o = {k: N(c.get(k)) for k in ('ni', 'dep', 'deftax', 'gains', 'conrail_eq', 'ar_chg', 'ms_chg', 'oca_chg', 'cl_chg', 'oth_chg', 'cfo',
                                   'capex', 'acq', 'prop_sales', 'inv_purch', 'inv_sales', 'cfi', 'div', 'stock', 'bb', 'borrow', 'repay', 'cff', 'net')}
    o['beg'], o['end'] = c.get('beg'), c.get('end')
    x = r.get('x') or {}
    o['sbc'] = N(x.get('sbc_ytd'))
    return o

def cf_lines(c):
    o = {'cf_ni': c['ni'], 'cf_dep': c['dep'], 'cf_deftax': c['deftax'], 'cf_gains': c['gains'], 'cf_sbc': c['sbc']}
    o['cf_wc'] = c['ar_chg'] + c['ms_chg'] + c['oca_chg'] + c['cl_chg']
    o['cf_oth'] = c['cfo'] - c['ni'] - c['dep'] - c['deftax'] - c['gains'] - o['cf_wc']          # other - net, Conrail equity earnings, residual
    o['cf_cfo'] = c['cfo']; o['cf_capex'] = c['capex']; o['cf_acq'] = c['acq']; o['cf_propsales'] = c['prop_sales']
    o['cf_inv'] = c['cfi'] - c['capex'] - c['acq'] - c['prop_sales']                                # investment purchases / sales & other, net
    o['cf_cfi'] = c['cfi']; o['cf_div'] = c['div']; o['cf_stock'] = c['stock']; o['cf_bb'] = c['bb']
    o['cf_borrow'] = c['borrow']; o['cf_repay'] = c['repay']
    o['cf_ofin'] = c['cff'] - c['div'] - c['stock'] - c['bb'] - c['borrow'] - c['repay']
    o['cf_cff'] = c['cff']; o['cf_net'] = c['cfo'] + c['cfi'] + c['cff']
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
    cash = N(b.get('cash')); sti = N(b.get('sti'))
    if b.get('cash_incl_sti') and r.get('cf') and r['cf'].get('end') is not None and r['cf']['ytd_months'] == 12:
        sti = round(cash - r['cf']['end'], 6); cash = r['cf']['end']
        put(p, 'bs_cash_split_note', 'Balance sheet shows cash, cash equivalents and short-term investments as one line; split using the cash-flow statement ending cash (derived).')
    put(p, 'bs_cash', cash); put(p, 'bs_sti', sti); put(p, 'bs_ar', b['ar']); put(p, 'bs_ms', N(b.get('ms')))
    put(p, 'bs_oca', b['tca'] - cash - sti - b['ar'] - N(b.get('ms'))); put(p, 'bs_tca', b['tca'])
    put(p, 'bs_inv', N(b.get('inv'))); put(p, 'bs_ppe', b['ppe']); put(p, 'bs_oa', b['ta'] - b['tca'] - N(b.get('inv')) - b['ppe']); put(p, 'bs_ta', b['ta'])
    put(p, 'bs_ap', b['ap']); put(p, 'bs_std', N(b.get('std'))); put(p, 'bs_cmltd', N(b.get('cmltd'))); put(p, 'bs_taxes', N(b.get('taxes_pay')))
    put(p, 'bs_ocl', b['tcl'] - b['ap'] - N(b.get('std')) - N(b.get('cmltd')) - N(b.get('taxes_pay'))); put(p, 'bs_tcl', b['tcl'])
    put(p, 'bs_ltd', b['ltd']); put(p, 'bs_dtl', N(b.get('dtl'))); put(p, 'bs_ol', b['tl'] - b['tcl'] - b['ltd'] - N(b.get('dtl'))); put(p, 'bs_tl', b['tl'])
    put(p, 'bs_teq', b['teq']); put(p, 'bs_tle', b['tle'])
    for k in ('cs', 'apic', 'aoci', 're'): put(p, 'bs_' + k, b.get(k))
    so = b.get('shares_out') or (r.get('x') or {}).get('sh_out')
    put(p, 'bs_shares', so)
    put(p, 'debt_tot', N(b.get('std')) + N(b.get('cmltd')) + b['ltd'])

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
                  ('rev', 'oi', 'ni', 'eps_d', 'sh_d', 'mg_units_total', 'mg_rpu_total', 'adj_oi_pub', 'cf_cfo', 'cf_wc', 'bs_ta', 'bs_shares', 'debt_tot', 'dps')})
    print('\n'.join(LOG))
