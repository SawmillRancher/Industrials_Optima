"""Harmonise the extracted JSON (data/<period>.json) into flat model keys (DATA[period]['x'][key]).

Basis: carve-out (combined) statements of the Mobility business of S&P Global as filed by Mobility Global (Form 10, 10-Q,
8-K Ex. 99.1 / 99.2), each period as originally reported (no recasts exist yet). Pre-2025 quarters are not published on the
carve-out basis and stay empty in the main rows; the S&P Global Mobility segment (memo keys sp_*) fills them for context.

- Cash flow: the 10-Q gives six months year to date, so Q2 = 1H − Q1. Q3-25 / Q4-25 cash flow is not published (only FY2025),
  so those columns stay empty.
- Adjusting items are grouped into the model rows (SBC; separation / stand-up transaction costs; severance, integration,
  acquisition & disposition, ELT transition, legal recovery and other) with the company's wording kept as a label string
  (cell comment on the total-items cell).
- Balance sheet: Q4 columns carry the year-end balance sheet (31-Dec-2023 from the first Form 10 draft; 2024-25 from the
  Form 10); Mar-2026 and Jun-2026 from the Form 10 / 10-Q. Mar-2025, Jun-2025 and Sep-2025 balance sheets were never published.
"""
import json, glob, os
BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG = {}, []
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))

def N(x): return x or 0.0
def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        DATA[os.path.basename(f)[:-5]] = json.load(open(f))
def g(p, s, k=None):
    d = DATA.get(p, {}).get(s)
    if d is None: return None
    return d if k is None else d.get(k)
def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def periods():
    out = [str(y) for y in range(2022, 2026)]
    for y in range(2023, 2027):
        out += [qk(y, q) for q in (1, 2, 3, 4) if not (y == 2026 and q > 2)]
    return out

ITEMS = ('sev', 'sev_oth', 'integ', 'acqdisp', 'legal', 'elt', 'other')
def do_is(p):
    i = g(p, 'is')
    if not i: return
    for k in ('rev', 'opex', 'sga', 'op', 'int', 'ebt', 'tax', 'ni', 'eps_basic', 'eps_dil', 'sh_basic', 'sh_dil'):
        put(p, k, i.get(k))
    if 'dep' in i:
        put(p, 'dep', i['dep']); put(p, 'amort', i['amort']); put(p, 'da', i['dep'] + i['amort'])
    else:
        put(p, 'da', i.get('da'))
    put(p, 'othinc', -N(i.get('othinc_exp')) if 'othinc_exp' in i else 0.0)   # income = +

def do_seg(p):
    sg = g(p, 'seg')
    if not sg: return
    tot = {'sbc': 0.0, 'trans': 0.0, 'oth': 0.0}; seen = False
    for s in ('cfx', 'b2b', 'corp'):
        d = sg.get(s, {})
        for k in ('rev', 'sub', 'nsub', 'us', 'intl', 'op', 'adj', 'adjop', 'opex', 'sga', 'sbc'):
            put(p, f'{s}_{k}', d.get(k))
        if 'amort' in d: put(p, f'{s}_da', N(d.get('amort')) + N(d.get('dep'))); put(p, f'{s}_amort', d['amort'])
        elif 'da' in d: put(p, f'{s}_da', d['da'])
        if 'op' in d and 'adj' in d:
            seen = True
            items = sum(N(d.get(k)) for k in ITEMS)
            put(p, f'{s}_trans', N(d.get('trans'))); put(p, f'{s}_oth', items)
            put(p, f'{s}_items', N(d.get('trans')) + items)
            tot['sbc'] += N(d.get('sbc')); tot['trans'] += N(d.get('trans')); tot['oth'] += items
    if seen:
        put(p, 'sbc', tot['sbc']); put(p, 'trans', tot['trans']); put(p, 'oth_items', tot['oth'])
    lab = g(p, 'ng', 'labels')
    if lab: put(p, 'items_lab', lab)

def do_ng(p):
    ng = g(p, 'ng') or {}
    put(p, 'adj_pub', ng.get('adj_ebitda'))
    sg = g(p, 'seg') or {}
    put(p, 'adjop_pub', ng.get('adjop_total'))     # company total column (segments may differ by $1m rounding)
    fcf = ng.get('fcf')
    put(p, 'fcf_pub', fcf)
    mx = g(p, 'mix')
    if mx:
        for k in ('sub', 'nsub', 'us', 'intl'): put(p, f'mix_{k}', mx[k])
    elif sg.get('cfx', {}).get('sub') is not None and sg.get('b2b', {}).get('sub') is not None:
        put(p, 'mix_sub', sg['cfx']['sub'] + sg['b2b']['sub']); put(p, 'mix_nsub', sg['cfx']['nsub'] + sg['b2b']['nsub'])

def do_spgi(p):
    sp = g(p, 'spgi')
    if not sp: return
    if p == '2022':
        put(p, 'sp_rev', sp['rev_pf']); put(p, 'sp_op', sp['op_pf']); put(p, 'sp_adjop', sp['adj_op_pf']); put(p, 'sp_rev_rep', sp['rev_reported'])
        return
    for k in ('rev', 'exp', 'op', 'ng_adj', 'amort', 'adj_op', 'sub', 'nsub'):
        put(p, f'sp_{k}', sp.get(k))

# ---------------------------------------------------------------- cash flow
def cf_lines(c):
    o = {'cf_ni': c['ni'], 'cf_dda': c['dep'] + c['amort'], 'cf_sbc': c['sbc'], 'cf_def': c['def_tax'], 'cf_oth': c['prov'] + c['restr'],
         'cf_cfo': c['cfo'], 'cf_capex': c['capex'], 'cf_acq': c['acq'], 'cf_cfi': c['cfi'], 'cf_par': c['transfers'], 'cf_notes': c['notes'],
         'cf_cff': c['cff'], 'cf_fx': c['fx']}
    o['cf_wc'] = c['cfo'] - o['cf_ni'] - o['cf_dda'] - o['cf_sbc'] - o['cf_def'] - o['cf_oth']
    o['cf_oinv'] = c['cfi'] - c['capex'] - c['acq']
    o['cf_ofin'] = c['cff'] - c['transfers'] - c['notes']
    o['cf_net'] = c['cfo'] + c['cfi'] + c['cff'] + c['fx']
    return o

def do_cf():
    for y in (2023, 2024, 2025):
        c = g(str(y), 'cf')
        for k, v in cf_lines(c).items(): put(str(y), k, v)
        put(str(y), 'cf_beg', c['cash_begin']); put(str(y), 'cf_end', c['cash_end'])
    for y in (2025, 2026):
        q1, h1 = g(qk(y, 1), 'cf'), g(qk(y, 2), 'cf')
        a, b = cf_lines(q1), cf_lines(h1)
        for k, v in a.items(): put(qk(y, 1), k, v)
        put(qk(y, 1), 'cf_beg', q1['cash_begin']); put(qk(y, 1), 'cf_end', q1['cash_end'])
        for k in b: put(qk(y, 2), k, b[k] - a[k])
        put(qk(y, 2), 'cf_beg', q1['cash_end']); put(qk(y, 2), 'cf_end', h1['cash_end'])
        LOG.append(f'{qk(y, 2)} cash flow = 1H − Q1')

# ---------------------------------------------------------------- balance sheet
def do_bs(p, src):
    b = g(src, 'bs')
    if not b: return
    put(p, 'bs_cash', b['cash']); put(p, 'bs_ar', b['ar']); put(p, 'bs_oca', b['due_from_c'] + b['prepaid'])
    put(p, 'bs_ppe', b['ppe']); put(p, 'bs_gw', b['gw']); put(p, 'bs_int', b['intang'])
    put(p, 'bs_onca', b['rou'] + N(b.get('due_from_nc')) + b['onca']); put(p, 'bs_ta', b['ta'])
    put(p, 'bs_ap', b['ap']); put(p, 'bs_unearned', b['unearned']); put(p, 'bs_ocl', b['due_to_c'] + b['accr'] + b['ocl'])
    put(p, 'bs_ltd', N(b.get('ltd'))); put(p, 'bs_dtl', b['dtl']); put(p, 'bs_oncl', b['lease'] + b['due_to_nc'] + b['oncl'])
    put(p, 'bs_eq', b['teq']); put(p, 'bs_tle', b['tle'])
    put(p, 'bs_rp_debt', b['due_to_nc'])

def run():
    load()
    for p in periods():
        do_is(p); do_seg(p); do_ng(p); do_spgi(p)
    do_cf()
    for p in periods():
        if p.startswith('Q4-'): do_bs(p, '20' + p[-2:])
        elif p.isdigit(): do_bs(p, p)
        else: do_bs(p, p)
    for p in ('Q2-26',):
        put(p, 'bs_shares', MAN['shares']['out_2026_07_01'])
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, len(x), {k: x[k] for k in ('rev', 'op', 'ni', 'adj_pub', 'adjop_pub', 'cf_cfo', 'cf_wc', 'bs_ta', 'sp_rev', 'sp_adj_op') if k in x})
    print('\n'.join(LOG))
