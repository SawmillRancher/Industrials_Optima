"""Harmonise the extracted J.B. Hunt data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m).

Basis: every period as originally reported in its own earnings release, with two segment recasts taken from the following
year's release comparatives (flagged 'seg_recast'; the model puts a cell comment on each recast cell):
  - FY2006: Integrated Capacity Solutions (ICS) was separated from Truck in 2007; FY2006 segments from the FY2007 release.
  - FY2019 and Q1-Q4/19: Final Mile Services (FMS) was separated from Dedicated (DCS) in Q1-20; segment revenue, operating
    income and DCS / FMS statistics from the 2020 releases. DCS as originally reported is kept as memo keys (*_orig).
  2018 and earlier Dedicated figures include final-mile operations (never recast in the releases).
Correction: Q3-19 statement of earnings from the Q3-20 release comparative (= the Q3-19 10-Q): the Q3-19 release (17-Oct-2019)
pre-dated the $44.2m BNSF arbitration charges booked after the final award (8-K 30-Oct-2019).
Cash flow: XBRL company facts as first filed (10-Q / 10-K), year to date; discrete quarters derived (Q2 = H1 - Q1,
Q3 = 9M - H1, Q4 = FY - 9M). FY2006-07 from the FY2008 10-K (manual_items.json).
Per-share data: no stock split since May-2005. Basic shares: XBRL (Q4 = 4 x FY - sum of Q1-Q3); dividends per share: XBRL
(Q4 = FY - 9M).
Adjusting items: only items the company itself quantified in its releases (manual_items.json 'company_items').
"""
import json, glob, os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))
SEGS = ('jbi', 'dcs', 'ics', 'fms', 'jbt')
Y0, YQ0, YC, QC_LAST = 2006, 2013, 2026, 3

def N(x): return x or 0.0
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def periods():
    out = [str(y) for y in range(Y0, YC)]
    for y in range(YQ0, YC + 1):
        out += [qk(y, q) for q in (1, 2, 3, 4) if not (y == YC and q > QC_LAST)]
    return out

def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v
def x_(p, k): return DATA.get(p, {}).get('x', {}).get(k)

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

def nxt(p):
    """period one year later (source of the recast comparative)."""
    return str(int(p) + 1) if p.isdigit() else f'{p[:3]}{int(p[3:]) + 1:02d}'

RECAST = {'2006': 'ICS separated from Truck in 2007', '2019': 'FMS separated from DCS in Q1-20',
          'Q1-19': 'FMS separated from DCS in Q1-20', 'Q2-19': 'FMS separated from DCS in Q1-20',
          'Q3-19': 'FMS separated from DCS in Q1-20', 'Q4-19': 'FMS separated from DCS in Q1-20'}

IS_FROM_NEXT = {'Q3-19': MAN['corrections']['Q3-19']['model']}

def do_pl(p):
    r = REC.get(p)
    if not r: LOG.append(f'{p}: no record'); return
    i = r['is']
    if p in IS_FROM_NEXT:                    # release issued before a charge booked in the 10-Q: statement from the next year's comparative
        i = REC[nxt(p)]['py']['is']; put(p, 'is_restated', IS_FROM_NEXT[p]); LOG.append(f'{p}: statement of earnings from the {nxt(p)} release comparative')
    for k in ('rev_xfuel', 'fuel_rev', 'rev', 'pt', 'sw', 'fuel', 'da', 'supplies', 'ins', 'ga', 'taxlic', 'comm', 'opex', 'oi', 'net_int', 'ebt', 'tax', 'ni',
              'sh_d', 'eps_d'):
        put(p, k, i.get(k))
    put(p, 'equity_loss', N(i.get('equity_loss')))
    x = dict(r.get('x') or {}); x.update({k: v for k, v in MAN['x_manual'].get(p, {}).items() if k not in ('source', 'note')})
    put(p, 'sh_b', x.get('sh_b') if x.get('sh_b') is not None else i.get('sh_b'))
    put(p, 'eps_b', x.get('eps_b') if x.get('eps_b') is not None else i.get('eps_b'))
    put(p, 'dps', x.get('dps_paid') if x.get('dps_paid') is not None else x.get('dps'))
    put(p, 'x_oi', x.get('oi')); put(p, 'x_ni', x.get('ni'))
    put(p, 'bs_gwint', x.get('gwint'))
    # segments (recast periods take the following year's comparative)
    s, st = r['seg'], r['stat']
    if p in RECAST:
        n = REC[nxt(p)]['py']
        put(p, 'seg_recast', RECAST[p])
        put(p, 'dcs_rev_orig', s.get('rev_dcs')); put(p, 'dcs_oi_orig', s.get('oi_dcs'))
        put(p, 'jbt_rev_orig', s.get('rev_jbt')); put(p, 'jbt_oi_orig', s.get('oi_jbt'))
        put(p, 'dcs_trucks_orig', st.get('dcs_trucks_avg'))
        s, st = n['seg'], n['stat']
        LOG.append(f'{p}: segments from the {nxt(p)} release comparatives ({RECAST[p]})')
    for g in SEGS:
        put(p, f'sr_{g}', s.get(f'rev_{g}')); put(p, f'so_{g}', s.get(f'oi_{g}'))
    put(p, 'sr_elim', s.get('rev_elim')); put(p, 'so_other', s.get('oi_other'))
    K = 1000.0
    for src, dst, sc in (('jbi_loads', 'jbi_loads', K), ('jbi_rpl', 'jbi_rpl_pub', 1), ('jbi_loh', 'jbi_loh', 1), ('jbi_trucks_avg', 'jbi_trucks', 1),
                         ('jbi_trailing_eop', 'jbi_trailing', 1), ('dcs_loads', 'dcs_loads', K), ('dcs_trucks_avg', 'dcs_trucks', 1), ('dcs_rptw', 'dcs_rptw', 1),
                         ('ics_loads', 'ics_loads', K), ('ics_rpl', 'ics_rpl_pub', 1), ('ics_gpm', 'ics_gpm', 100.0), ('ics_emp', 'ics_emp', 1),
                         ('fms_stops', 'fms_stops', K), ('fms_trucks_avg', 'fms_trucks', 1), ('jbt_loads', 'jbt_loads', K), ('jbt_rpl', 'jbt_rpl_pub', 1),
                         ('jbt_loh', 'jbt_loh', 1), ('jbt_trucks_avg', 'jbt_trucks', 1)):
        v = st.get(src)
        if v is not None: put(p, dst, v / sc)
    # balance sheet
    b = r['bs']
    ta = b.get('ta') if b.get('ta') is not None else b['tca'] + b['ppe'] + b['oa']
    put(p, 'bs_cash', b['cash']); put(p, 'bs_ar', b['ar']); put(p, 'bs_oca', b['tca'] - b['cash'] - b['ar'])
    put(p, 'bs_ppe', b['ppe']); put(p, 'bs_ppe_gross', b['ppe_gross']); put(p, 'bs_accdep', b['accdep']); put(p, 'bs_oa', b['oa']); put(p, 'bs_ta', ta)
    put(p, 'bs_std', N(b.get('debt_cur'))); put(p, 'bs_ap', b['ap']); put(p, 'bs_claims', b['claims'])
    put(p, 'bs_oacc', b['tcl'] - N(b.get('debt_cur')) - b['ap'] - b['claims'])
    put(p, 'bs_ltd', b['ltd']); put(p, 'bs_oltl', N(b.get('lt_claims')) + b['oltl']); put(p, 'bs_lt_claims', b.get('lt_claims'))
    put(p, 'bs_dit', b['dit']); put(p, 'bs_eq', b['eq'])
    put(p, 'bs_tle', b['tcl'] + b['ltd'] + N(b.get('lt_claims')) + b['oltl'] + b['dit'] + b['eq'])
    put(p, 'bs_shares', b.get('shares'))
    # company-quantified items
    put(p, 'oa_items', 0.0); put(p, 'oa_after', None); put(p, 'oa_taxd', 0.0)

def do_items():
    for it in MAN['company_items']['items']:
        p = it['period']
        tgt = [p] + ([f'20{p[-2:]}'] if p.startswith('Q') else [])
        for t in tgt:
            put(t, 'oa_items', N(x_(t, 'oa_items')) + it['pre'])
            put(t, 'oa_taxd', N(x_(t, 'oa_taxd')) + it['tax_discrete'])
            if it['after'] is not None and t == p: put(t, 'oa_after', N(x_(t, 'oa_after')) + it['after'])
            lab = x_(t, 'oa_lab')
            put(t, 'oa_lab', (lab + ' | ' if lab else '') + it['label'])

CFK = ('ni', 'da', 'sbc', 'gain', 'deftax', 'cfo', 'capex', 'sale', 'acq', 'cfi', 'bb', 'div', 'cff')
def cf_ytd(y, q, annual=False):
    p = str(y) if annual else qk(y, q)
    man = MAN['cf_manual'].get(p, {}) if annual else {}
    c = dict((REC.get(p) or {}).get('cf') or {})
    c.update({k: v for k, v in man.items() if k not in ('source', 'note')})
    if 'cfo' not in c: return None
    return {k: N(c.get(k)) for k in CFK}

def cf_put(p, c, beg, end):
    put(p, 'cf_ni', c['ni']); put(p, 'cf_da', c['da']); put(p, 'cf_sbc', c['sbc']); put(p, 'cf_gain', c['gain']); put(p, 'cf_def', c['deftax'])
    put(p, 'cf_wc', c['cfo'] - c['ni'] - c['da'] - c['sbc'] - c['gain'] - c['deftax']); put(p, 'cf_cfo', c['cfo'])
    put(p, 'cf_capex', -c['capex']); put(p, 'cf_sale', c['sale']); put(p, 'cf_acq', -c['acq'])
    put(p, 'cf_oinv', c['cfi'] + c['capex'] - c['sale'] + c['acq']); put(p, 'cf_cfi', c['cfi'])
    put(p, 'cf_bb', -c['bb']); put(p, 'cf_div', -c['div']); put(p, 'cf_ofin', c['cff'] + c['bb'] + c['div']); put(p, 'cf_cff', c['cff'])
    put(p, 'cf_net', c['cfo'] + c['cfi'] + c['cff']); put(p, 'cf_beg', beg); put(p, 'cf_end', end)

def do_cf():
    for y in range(Y0, YC):
        c = cf_ytd(y, 4, True)
        if not c: LOG.append(f'{y}: no annual cash flow'); continue
        beg = REC[str(y - 1)]['bs']['cash'] if str(y - 1) in REC else MAN['cf_manual'][str(y)]['beg']
        cf_put(str(y), c, beg, REC[str(y)]['bs']['cash'])
    for y in range(YQ0, YC + 1):
        prev = None
        for q in (1, 2, 3, 4):
            if y == YC and q > QC_LAST: break
            c = cf_ytd(y, q)
            if q == 4 and c is None: c = cf_ytd(y, 4, True)
            if c is None: LOG.append(f'{qk(y, q)}: no cash flow'); prev = None; continue
            d = c if q == 1 else ({k: c[k] - prev[k] for k in CFK} if prev else None)
            prev = c
            if d is None: continue
            pb = str(y - 1) if q == 1 else qk(y, q - 1)
            cf_put(qk(y, q), d, REC[pb]['bs']['cash'], REC[qk(y, q)]['bs']['cash'])

def do_derived():
    for y in range(YQ0, YC):
        qs = [qk(y, q) for q in (1, 2, 3)]
        fy = str(y)
        if x_(qk(y, 4), 'sh_b') is None and all(x_(q, 'sh_b') is not None for q in qs) and x_(fy, 'sh_b') is not None:
            put(qk(y, 4), 'sh_b', 4 * x_(fy, 'sh_b') - sum(x_(q, 'sh_b') for q in qs)); put(qk(y, 4), 'sh_b_derived', 1)
        if x_(qk(y, 4), 'dps') is None and all(x_(q, 'dps') is not None for q in qs) and x_(fy, 'dps') is not None:
            put(qk(y, 4), 'dps', x_(fy, 'dps') - sum(x_(q, 'dps') for q in qs))

def do_debt():
    d = MAN['debt']; p = qk(YC, QC_LAST)
    put(p, 'debt_st', d['revolver']); put(p, 'debt_lt', x_(p, 'bs_std') + x_(p, 'bs_ltd') - d['revolver'])

_done = False
def run():
    global _done
    if _done: return DATA
    load()
    for p in periods(): do_pl(p)
    do_items(); do_cf(); do_derived(); do_debt()
    _done = True
    return DATA

if __name__ == '__main__':
    run()
    print('\n'.join(LOG))
    print(len(DATA), 'periods')
