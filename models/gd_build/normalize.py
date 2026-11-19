"""Harmonise the extracted General Dynamics data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m).

Basis: every period as originally reported in its own earnings release (ASC 606 (adopted 1-Jan-2017, 2016 restated in the 2017
releases), ASU 2017-07 (2018), the 2020 change in accounting principle and the 2014 axle-business discontinued operations are
not recast; the restated comparatives are kept as *_py memo keys for cell comments). Segments follow the structure in force in
each period, mapped onto the current four: Aerospace, Marine Systems, Combat Systems and Technologies, where Technologies =
Information Systems and Technology (2006 - Q1-18) = Information Technology + Mission Systems (Q2-18 - 2019; both kept as memo
keys) = Technologies (2020+). Gulfstream deliveries: green deliveries to 2016 (release exhibits to 2009, 10-Q / 10-K MD&A
2010-16), outfitted deliveries from 2017 (ASC 606 recognises aircraft revenue at outfitted delivery). Cash flow: releases give
year-to-date statements; discrete quarters are derived (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M). Adjusted measures: GD
publishes none except free cash flow; the FY2012 / Q4-12 and FY2017 / Q4-17 one-off reconciliations are in manual_items.json."""
import json, glob, os

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

SEGS = ('aero', 'marine', 'combat', 'tech')
def seg_map(d):
    """segment dict in the structure in force -> current four segments (+ memo keys)."""
    out, memo = {}, {}
    for s in ('aero', 'marine', 'combat'):
        if s in d: out[s] = d[s]
    if 'tech' in d: out['tech'] = d['tech']; basis = 'tech'
    elif 'it' in d or 'ms' in d: out['tech'] = N(d.get('it')) + N(d.get('ms')); memo['it'] = d.get('it'); memo['ms'] = d.get('ms'); basis = 'it+ms'
    elif 'ist' in d: out['tech'] = d['ist']; memo['ist'] = d['ist']; basis = 'ist'
    else: basis = None
    return out, memo, basis

def do_pl(p):
    r = REC.get(p)
    if not r: LOG.append(f'{p}: no record'); return
    i, s = r['is'], r['seg']
    put(p, 'rev', i['rev']); put(p, 'costs', i.get('costs')); put(p, 'oi', i['oi'])
    put(p, 'int', i.get('int')); put(p, 'oth', i.get('oth')); put(p, 'ebt', i.get('ebt')); put(p, 'tax', i.get('tax'))
    put(p, 'cont', i.get('cont')); put(p, 'disc', N(i.get('disc'))); put(p, 'ni', i['ni'])
    put(p, 'eps_b', i.get('eps_b_ni')); put(p, 'eps_d', i.get('eps_d_ni')); put(p, 'eps_d_cont', i.get('eps_d_cont'))
    put(p, 'sh_b', i.get('sh_b')); put(p, 'sh_d', i.get('sh_d'))
    x = r.get('x') or {}
    ex = r.get('extra') or {}
    if p.isdigit():                                  # annual DPS: 10-K selected data / text, else sum of the XBRL quarters
        put(p, 'dps', ex.get('dps_fy'))
    else:
        put(p, 'dps', x.get('dps'))
    put(p, 'ga', x.get('ga'))
    for k in ('oi_xbrl', 'ni_xbrl', 'rev_xbrl', 'ta_xbrl', 'cfo_xbrl'): put(p, k, x.get(k))
    # segments
    rev, memo_r, basis = seg_map(s['rev']); oi, memo_o, _ = seg_map(s['oi'])
    for k in SEGS: put(p, f'sr_{k}', rev.get(k)); put(p, f'so_{k}', oi.get(k))
    for k, v in memo_r.items(): put(p, f'sr_{k}', v)
    for k, v in memo_o.items(): put(p, f'so_{k}', v)
    put(p, 'so_corp', s['oi'].get('corp')); put(p, 'sr_tot', s['rev'].get('total')); put(p, 'so_tot', s['oi'].get('total'))
    put(p, 'seg_basis', basis)
    # backlog (period end)
    b = r.get('backlog') or {}
    for meas in ('funded', 'unfunded', 'total', 'pcv', 'tecv'):
        d = {k: v.get(meas) for k, v in b.items() if v.get(meas) is not None}
        m, memo, _ = seg_map(d)
        for k in SEGS: put(p, f'bl_{k}_{meas}', m.get(k))
        for k, v in memo.items(): put(p, f'bl_{k}_{meas}', v)
        put(p, f'bl_tot_{meas}', d.get('total'))
    # Gulfstream deliveries
    fy, q = fyq(p)
    d = r.get('deliv') or {}
    md = r.get('deliv_mdna') or []
    if d.get('basis') == 'green' and d.get('total_q') is not None:                        # 2006-2009 release exhibits (green)
        put(p, 'dl_green', d['total_ytd'] if p.isdigit() else d['total_q'])
        put(p, 'dl_outfitted', d.get('compl_total_ytd') if p.isdigit() else d.get('compl_total_q'))
        put(p, 'dl_large', d['large_ytd'] if p.isdigit() else d['large_q']); put(p, 'dl_mid', d['mid_ytd'] if p.isdigit() else d['mid_q'])
        put(p, 'dl_basis', 'green')
    elif d.get('basis') == 'outfitted' and d.get('total_q') is not None:                  # 2017+ release exhibits (outfitted, ASC 606)
        put(p, 'dl_outfitted', d['total_ytd'] if p.isdigit() else d['total_q'])
        put(p, 'dl_large', d['large_ytd'] if p.isdigit() else d['large_q']); put(p, 'dl_mid', d['mid_ytd'] if p.isdigit() else d['mid_q'])
        put(p, 'dl_basis', 'outfitted')
    elif d.get('green_total_q') is not None:                                               # FY2016 release quarterly table
        put(p, 'dl_green', d['green_total_ytd'] if p.isdigit() else d['green_total_q'])
        put(p, 'dl_outfitted', d['outfitted_total_ytd'] if p.isdigit() else d['outfitted_total_q']); put(p, 'dl_basis', 'green')
    elif md:                                                                               # 2010-2016 MD&A tables
        t = md[0]
        put(p, 'dl_green', t['green'][0]); put(p, 'dl_outfitted', (t.get('outfitted') or [None])[0]); put(p, 'dl_basis', 'green')
        put(p, 'dl_src', 'mdna')
    put(p, 'dl_preowned', d.get('preowned_ytd') if p.isdigit() else d.get('preowned_q'))
    put(p, 'aero_orders', d.get('aero_orders_ytd') if p.isdigit() else d.get('aero_orders_q'))
    # financial information
    f = r.get('fin') or {}
    fcf_pub = f.get('fcf_ytd') if p.isdigit() else f.get('fcf_q')
    if p in MAN['fcf_exceptions']:
        put(p, 'fcf_pub_exc', fcf_pub); put(p, 'fcf_exc_note', MAN['fcf_exceptions'][p]); fcf_pub = None
    put(p, 'fcf_pub', fcf_pub)
    sh = f.get('shares_out') or x.get('shares_cover') or x.get('shares_out')
    put(p, 'shares_out', sh)
    put(p, 'employees', (r.get('extra') or {}).get('employees') or f.get('employment'))
    put(p, 'rnd_q', f.get('rnd_q'))
    # prior-year comparative restated in the following year's release
    py = (r.get('py') or {})
    pi = py.get('is') or {}
    for k, kk in (('rev', 'rev'), ('oi', 'oi'), ('ni', 'ni'), ('eps_d_ni', 'eps_d')):
        if pi.get(k) is not None and i.get(k) is not None and abs(pi[k] - i[k]) > (0.005 if k.startswith('eps') else 0.6):
            put(p, f'{kk}_py', pi[k])
    ps = py.get('seg') or {}
    if ps.get('rev'):
        prev, _, pb = seg_map(ps['rev']); poi, _, _ = seg_map(ps['oi'])
        for k in SEGS:
            if prev.get(k) is not None and rev.get(k) is not None and abs(prev[k] - rev[k]) > 0.6: put(p, f'sr_{k}_py', prev[k])
            if poi.get(k) is not None and oi.get(k) is not None and abs(poi[k] - oi[k]) > 0.6: put(p, f'so_{k}_py', poi[k])
        if pb and pb != basis: put(p, 'seg_basis_py', pb)
    # company one-off non-GAAP reconciliations (FY2012 / Q4-12, FY2017 / Q4-17) and the items GD named but did not adjust
    a = MAN['adjusted'].get(p)
    cats = ['impair', 'disputes', 'restr', 'inv', 'debt', 'taxd']
    for c in cats: put(p, f'oa_{c}', 0.0)
    if a:
        for c in cats: put(p, f'oa_{c}', N(a.get(c)))
        put(p, 'oa_tax', N(a.get('tax'))); put(p, 'adj_ni_pub', a.get('adj_ni')); put(p, 'adj_eps_pub', a.get('adj_eps')); put(p, 'adj_sh', a.get('adj_sh'))
        put(p, 'adj_oi_pub', a.get('adj_oi'))
        put(p, 'oa_labels', a.get('labels'))
    else:
        put(p, 'oa_tax', 0.0)

# ---------------------------------------------------------------- cash flow
def cf_ytd(fy, q):
    p = str(fy) if q == 4 and REC.get(str(fy)) else qk(fy, q)
    r = REC.get(p) or REC.get(qk(fy, q))
    if not r or not r.get('cf'): return None
    c = r['cf']
    o = {k: N(c.get(k)) for k in ('dep', 'amort', 'sbc', 'deferred_tax', 'capex', 'acq', 'div', 'bb', 'notes_proc', 'notes_rep', 'cp', 'cfi', 'cff', 'net',
                                   'excess_tax', 'disc_adj', 'impair', 'cfo_disc', 'disc_cash', 'options', 'asset_sales', 'sec_buy', 'sec_sell', 'disc_proceeds')}
    o['ni'] = c.get('ni'); o['beg'], o['end'] = c.get('beg'), c.get('end')
    o['cfo'] = c.get('cfo_cont') if c.get('cfo_cont') is not None else c.get('cfo')
    o['wc'] = sum(N(c.get(k)) for k in ('wc_ar', 'wc_unbilled', 'wc_inv', 'wc_ap', 'wc_adv', 'wc_tax', 'wc_ocl', 'wc_oca', 'wc_ol'))
    o['disc'] = N(c.get('disc_cash')) + N(c.get('cfo_disc'))
    return o

def cf_lines(c):
    o = {'cf_ni': c['ni'], 'cf_dda': c['dep'] + c['amort'], 'cf_dep': c['dep'], 'cf_amort': c['amort'], 'cf_sbc': c['sbc'], 'cf_def': c['deferred_tax'], 'cf_wc': c['wc']}
    o['cf_oth'] = c['cfo'] - c['ni'] - o['cf_dda'] - c['sbc'] - c['deferred_tax'] - c['wc']
    o['cf_cfo'] = c['cfo']; o['cf_capex'] = c['capex']; o['cf_acq'] = c['acq']
    o['cf_oinv'] = c['cfi'] - c['capex'] - c['acq']; o['cf_cfi'] = c['cfi']
    o['cf_div'] = c['div']; o['cf_bb'] = c['bb']; o['cf_notes'] = c['notes_proc'] + c['notes_rep']; o['cf_cp'] = c['cp']
    o['cf_ofin'] = c['cff'] - c['div'] - c['bb'] - o['cf_notes'] - c['cp']; o['cf_cff'] = c['cff']
    o['cf_disc'] = c['disc']
    o['cf_net'] = c['cfo'] + c['cfi'] + c['cff'] + c['disc']
    return o

def x_(p, k): return DATA.get(p, {}).get('x', {}).get(k)

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
    put(p, 'bs_cash', b['cash']); put(p, 'bs_ar', b['ar']); put(p, 'bs_unbilled', b['unbilled']); put(p, 'bs_inv', b['inv'])
    put(p, 'bs_oca', b['tca'] - b['cash'] - b['ar'] - b['unbilled'] - b['inv']); put(p, 'bs_tca', b['tca'])
    put(p, 'bs_ppe', b['ppe']); put(p, 'bs_intang', b['intang']); put(p, 'bs_gw', b['gw'])
    ta = b.get('ta') if b.get('ta') is not None else b['tca'] + b['tnca']
    put(p, 'bs_oa', ta - b['tca'] - b['ppe'] - b['intang'] - b['gw']); put(p, 'bs_ta', ta)
    put(p, 'bs_std', N(b.get('std'))); put(p, 'bs_ap', b['ap']); put(p, 'bs_adv', b['adv'])
    put(p, 'bs_ocl', b['tcl'] - N(b.get('std')) - b['ap'] - b['adv']); put(p, 'bs_tcl', b['tcl'])
    put(p, 'bs_ltd', b['ltd']); put(p, 'bs_ol', b['tncl'] - b['ltd']); put(p, 'bs_tl', b['tcl'] + b['tncl'])
    te = b.get('te') if b.get('te') is not None else ta - b['tcl'] - b['tncl']
    put(p, 'bs_te', te); put(p, 'bs_tle', b.get('tle') if b.get('tle') is not None else b['tcl'] + b['tncl'] + te)
    put(p, 'debt_tot', N(b.get('std')) + b['ltd'])
    put(p, 'debt_cp', 0.0 if p in ('Q3-26',) else None)          # commercial paper: none outstanding at 4-Oct-2026 (10-Q); history not split in the release
    put(p, 'debt_notes', N(b.get('std')) + b['ltd'] if p == 'Q3-26' else None)

def do_q4():
    """Q4 values published only as full-year figures: FY - 9M (Gulfstream deliveries from the MD&A tables 2010-16; dividends declared per share)."""
    for y in range(2013, 2026):
        p4, p3, pf = qk(y, 4), qk(y, 3), str(y)
        x4, x3, xf = DATA.get(p4, {}).get('x', {}), DATA.get(p3, {}).get('x', {}), DATA.get(pf, {}).get('x', {})
        if x4.get('dl_src') == 'mdna':
            md3 = (REC.get(p3) or {}).get('deliv_mdna') or []
            ytd = md3[1] if len(md3) > 1 else None
            if ytd and xf.get('dl_green') is not None:
                put(p4, 'dl_green', xf['dl_green'] - ytd['green'][0])
                if xf.get('dl_outfitted') is not None and ytd.get('outfitted'): put(p4, 'dl_outfitted', xf['dl_outfitted'] - ytd['outfitted'][0])
                put(p4, 'dl_note', 'Q4 = full year (10-K MD&A) - nine months (Q3 10-Q MD&A)')
        if xf.get('dps') is None:
            qs = [DATA.get(qk(y, q), {}).get('x', {}).get('dps') for q in (1, 2, 3, 4)]
            if all(v is not None for v in qs): put(pf, 'dps', sum(qs)); put(pf, 'dps_note', 'sum of the four quarterly declarations (XBRL)')
        if x4.get('dps') is None and xf.get('dps') is not None:
            qs = [DATA.get(qk(y, q), {}).get('x', {}).get('dps') for q in (1, 2, 3)]
            if all(v is not None for v in qs): put(p4, 'dps', round(xf['dps'] - sum(qs), 4)); put(p4, 'dps_note', 'Q4 = full year - nine months')

def run():
    load()
    for p in periods():
        do_pl(p); do_bs(p)
    do_cf(); do_q4()
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: round(x[k], 1) if isinstance(x.get(k), float) else x.get(k) for k in
                  ('rev', 'oi', 'ni', 'eps_d', 'sh_d', 'sr_tech', 'seg_basis', 'bl_tot_total', 'dl_green', 'dl_outfitted', 'fcf_pub', 'cf_cfo', 'cf_wc', 'bs_ta', 'shares_out', 'debt_tot', 'dps')})
    print('\n'.join(LOG))
