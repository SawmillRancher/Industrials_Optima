"""Harmonise the extracted Howmet data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m).

Basis policy (one policy, documented in the README):
  - Every period as originally reported in its own earnings release, except periods before the 1-Apr-2020 separation of Arconic
    Corporation: FY2019 and Q1-20 are the recast continuing-operations comparatives (P&L and segments only; no balance sheet;
    Q1-20 cash flow is consolidated incl. Arconic Corporation, as the company never segregated it).
  - Segment Adjusted EBITDA (the segment measure from Q1-22): 2021 from the 2022 release panels (company recast); 2019-2020 =
    segment operating profit + segment D&A (the identity behind the company's recast, proven on every 2021 period).
  - Q1-26 segment realignment (titanium alloy location moved from Engine Products to Engineered Structures): the company recast
    FY2024 and the 2025 quarters. 2025 quarters and FY2025 take the recast figures (all four quarters recast); FY2024 stays as
    reported with the recast figures in memo keys (*_rc); 2024 quarters were never recast.
  - End-market revenue (10-Q / 10-K note): 'gas turbines / other' for 2025 quarters from the 2026 10-Q comparatives.
Cash flow: releases give year-to-date statements; discrete quarters derived (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M).
Signs: costs positive; special items as added back (charges +, credits -); cash flow as presented.
"""
import json, glob, os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))
SEGK = ['ep', 'fs', 'es', 'fw']
Y0, YL, LQ = 2019, 2026, 3                    # first year, current year, last actual quarter

def N(x): return x or 0.0
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def periods():
    out = [str(Y0)]
    for y in range(Y0 + 1, YL + 1):
        out += [qk(y, q) for q in (1, 2, 3, 4) if not (y == YL and q > LQ)]
        if y < YL: out.append(str(y))
    return out

def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v
def x_(p, k): return DATA.get(p, {}).get('x', {}).get(k)

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

def item(items, rx):
    import re
    for l, v in items or []:
        if re.search(rx, l, re.I): return v
    return None

def apply_corrections():
    """documented overrides (manual_items.json 'corrections'): a figure is changed only where a later filing proves it."""
    for c in MAN.get('corrections', []):
        for p in c['periods']:
            for sec, kv in c['set'].items(): REC[p][sec].update(kv)
            REC[p]['notes'].append(c['note'])

def do_pl(p):
    r = REC[p]; i, s, n = r['is'], r['seg'], r['ngaap']
    y = r['year']
    for k in ('rev', 'cogs', 'sga', 'rd', 'da', 'oi', 'ebt', 'tax', 'ni', 'eps_b', 'eps_d', 'sh_b', 'sh_d', 'sh_out'): put(p, k, i.get(k))
    put(p, 'restr', N(i.get('restr'))); put(p, 'int', i.get('int')); put(p, 'loss_debt', N(i.get('loss_debt'))); put(p, 'oth', N(i.get('oth')))
    cont = i.get('cont', i['ni'])
    put(p, 'cont', cont); put(p, 'disc', N(i.get('disc'))); put(p, 'eps_d_cont', i.get('eps_d_cont', i.get('eps_d')))
    # segments
    rc25 = y == 2025
    tot = 0.0
    for g in SEGK:
        def gv(k):
            v = s.get(f'{g}_{k}')
            if rc25 and s.get(f'{g}_{k}_rc') is not None: v = s[f'{g}_{k}_rc']
            return v
        tps, da = gv('tps'), gv('da')
        eb = gv('ebitda')
        if eb is None and s.get(f'{g}_op') is not None:
            eb = s[f'{g}_op'] + da; put(p, 'seg_ebitda_derived', 1)
        put(p, f'{g}_rev', tps); put(p, f'{g}_da', da); put(p, f'{g}_ebitda', eb); put(p, f'{g}_capex', gv('capex')); put(p, f'{g}_restr', gv('restr'))
        put(p, f'{g}_inter', N(gv('inter')))
        tot += eb
        if rc25 and s.get(f'{g}_tps_rc') is not None:
            put(p, f'{g}_rev_orig', s[f'{g}_tps']); put(p, f'{g}_ebitda_orig', s.get(f'{g}_ebitda')); put(p, 'seg_recast', 1)
        if y == 2024 and r['q'] is None:
            for k, kk in (('tps', 'rev'), ('ebitda', 'ebitda')):
                if s.get(f'{g}_{k}_rc') is not None: put(p, f'{g}_{kk}_rc', s[f'{g}_{k}_rc'])
        if y not in (2024, 2025) or (y == 2024 and r['q']):
            for k in ('tps', 'ebitda'):
                if s.get(f'{g}_{k}_rc') is not None: LOG.append(f'{p}: {g}_{k} later re-presented {s[f"{g}_{k}"]} -> {s[f"{g}_{k}_rc"]} (not applied)')
    put(p, 'seg_ebitda_tot', tot)
    put(p, 'rev_oth', i['rev'] - sum(x_(p, f'{g}_rev') for g in SEGK))       # corporate / rounding outside the segments (derived)
    if s.get('tot_ebitda') is not None: put(p, 'seg_ebitda_tot_pub', s['tot_ebitda'])
    put(p, 'corp_rep', abs(s['corp']) if s.get('corp') is not None else None)
    # special items / adjusted measures
    oi, da = i['oi'], i['da']
    adj_oi, adj_eb = n.get('adj_oi'), n.get('adj_ebitda')
    sp_op = (adj_oi - oi) if adj_oi is not None else (adj_eb - oi - da)
    put(p, 'sp_restr', N(i.get('restr'))); put(p, 'sp_oth_op', sp_op - N(i.get('restr')))
    put(p, 'adj_oi_pub', adj_oi); put(p, 'adj_ebitda_pub', adj_eb)
    in_da = (adj_oi + da - adj_eb) if (adj_oi is not None and adj_eb is not None) else 0.0      # special items recorded in D&A (accelerated depreciation)
    put(p, 'sp_in_da', in_da)
    put(p, 'corp_adj', tot - (oi + da + sp_op - in_da))   # adjusted corporate expense excl. D&A and special items (derived)
    if i.get('eps_total_computed'): put(p, 'eps_total_computed', 1)
    items = n.get('items') or []
    pre = item(items, r'^subtotal: pre-tax special items')
    if pre is None: pre = N(item(items, r'^restructuring')) + N(item(items, r'^(total )?other special items'))
    put(p, 'sp_nonop', pre - sp_op)
    put(p, 'sp_tax', n['adj_ni'] - cont - pre)
    put(p, 'adj_ni_pub', n['adj_ni']); put(p, 'adj_eps_pub', n.get('adj_eps')); put(p, 'adj_sh', n.get('adj_sh'))
    put(p, 'sp_labels', '; '.join(f'{l} {v:,.0f}' for l, v in items if abs(v) > 1e-9))
    put(p, 'sp_op_labels', '; '.join(f'{l} {v:,.0f}' for l, v in (n.get('oi_items') or []) if abs(v) > 1e-9))
    o = (n.get('organic') or {})
    for g in SEGK + ['tot']:
        if g in o:
            put(p, f'{g}_gorg', o[g]['g_org']); put(p, f'{g}_ad', o[g]['ad']); put(p, f'{g}_ad_py', o[g]['py_ad'])
    em = r.get('em') or {}
    for k in ('ca', 'df', 'ct', 'io', 'gt', 'tot'): put(p, f'em_{k}', em.get(k))

# ---------------------------------------------------------------- cash flow
CFK = ['ni', 'da', 'deftax', 'restr', 'sbc', 'cfo', 'capex', 'acq', 'divest', 'sold_rec', 'cfi', 'bb', 'div', 'st_change', 'debt_add', 'debt_pay',
       'debt_costs', 'debt_prem', 'cff', 'fx']
def cf_lines(c):
    v = {k: N(c.get(k)) for k in CFK}
    o = {'cf_ni': v['ni'], 'cf_da': v['da'], 'cf_def': v['deftax'], 'cf_restr': v['restr'], 'cf_sbc': v['sbc']}
    o['cf_wc'] = v['cfo'] - v['ni'] - v['da'] - v['deftax'] - v['restr'] - v['sbc']
    o['cf_cfo'] = v['cfo']; o['cf_capex'] = v['capex']; o['cf_acq'] = v['acq']; o['cf_divest'] = v['divest']; o['cf_soldrec'] = v['sold_rec']
    o['cf_oinv'] = v['cfi'] - v['capex'] - v['acq'] - v['divest'] - v['sold_rec']; o['cf_cfi'] = v['cfi']
    o['cf_bb'] = v['bb']; o['cf_div'] = v['div']
    o['cf_debt'] = v['st_change'] + v['debt_add'] + v['debt_pay'] + v['debt_costs'] + v['debt_prem']
    o['cf_ofin'] = v['cff'] - v['bb'] - v['div'] - o['cf_debt']; o['cf_cff'] = v['cff']; o['cf_fx'] = v['fx']
    o['cf_net'] = v['cfo'] + v['cfi'] + v['cff'] + v['fx']
    return o

def do_cf():
    for y in range(Y0 + 1, YL + 1):
        prev = None
        for q in (1, 2, 3, 4):
            p = qk(y, q)
            if p not in REC: break
            c = REC[p]['cf']; lc = cf_lines(c)
            d = lc if q == 1 else {k: lc[k] - prev[0][k] for k in lc}
            beg = c.get('beg') if q == 1 else prev[1]
            if beg is None and q == 1: beg = c['end'] - lc['cf_net']
            for k, v in d.items(): put(p, k, v)
            put(p, 'cf_beg', beg); put(p, 'cf_end', c['end'])
            prev = (lc, c['end'])
            put(p, 'fcf_pub', REC[p]['ngaap'].get('fcf')); put(p, 'fcf_label', REC[p]['ngaap'].get('fcf_label'))
        p = str(y)
        if p in REC:
            c = REC[p]['cf']
            for k, v in cf_lines(c).items(): put(p, k, v)
            beg = c.get('beg'); put(p, 'cf_beg', beg if beg is not None else c['end'] - x_(p, 'cf_net')); put(p, 'cf_end', c['end'])
            put(p, 'fcf_pub', REC[p]['ngaap'].get('fcf')); put(p, 'fcf_label', REC[p]['ngaap'].get('fcf_label'))
    for p in periods():
        v = DATA[p]['x']
        if v.get('cf_cfo') is None: continue
        if v.get('fcf_pub') is not None: put(p, 'fcf_oth', v['fcf_pub'] - v['cf_cfo'] - v['cf_capex'] - v['cf_soldrec'])
        if v.get('sh_b'): put(p, 'dps', -v['cf_div'] / v['sh_b'])

# ---------------------------------------------------------------- balance sheet
def do_bs(p):
    b = REC[p].get('bs')
    if not b: return
    ar = b['ar'] + N(b.get('oth_rec'))
    put(p, 'bs_cash', b['cash']); put(p, 'bs_ar', ar); put(p, 'bs_inv', b['inv']); put(p, 'bs_oca', b['tca'] - b['cash'] - ar - b['inv'])
    put(p, 'bs_tca', b['tca']); put(p, 'bs_ppe', b['ppe']); put(p, 'bs_gw', b['gw']); put(p, 'bs_int', b['intang'])
    put(p, 'bs_onca', b['ta'] - b['tca'] - b['ppe'] - b['gw'] - b['intang']); put(p, 'bs_ta', b['ta'])
    std = N(b.get('std')) + N(b.get('cltd'))
    put(p, 'bs_ap', b['ap']); put(p, 'bs_std', std); put(p, 'bs_ocl', b['tcl'] - b['ap'] - std); put(p, 'bs_tcl', b['tcl'])
    put(p, 'bs_ltd', b['ltd']); pen = b['pension'] + N(b.get('opeb')); put(p, 'bs_pen', pen)
    put(p, 'bs_ol', b['tl'] - b['tcl'] - b['ltd'] - pen); put(p, 'bs_tl', b['tl'])
    nci = N(b.get('nci'))
    put(p, 'bs_eq', b['teq'] - nci); put(p, 'bs_nci', nci); put(p, 'bs_teq', b['teq']); put(p, 'bs_tle', b['tle']); put(p, 'bs_pref', N(b.get('pref')))
    put(p, 'debt_tot', std + b['ltd'])
    cp = N(b.get('std')) if REC[p]['year'] >= 2026 else 0.0          # commercial paper ('Short-term borrowings' line, from 2026)
    put(p, 'debt_cp', cp); put(p, 'debt_notes', std + b['ltd'] - cp)
    so = REC[p]['is'].get('sh_out')
    if so is None and REC[p]['q'] is None: so = REC[qk(REC[p]['year'], 4)]['is'].get('sh_out')
    put(p, 'bs_shares', so)

def run():
    if DATA: return DATA
    load(); apply_corrections()
    for p in periods():
        do_pl(p); do_bs(p)
    do_cf()
    for p in periods():
        v = DATA[p]['x']
        if v.get('cf_end') is not None and v.get('bs_cash') is not None: put(p, 'bs_restricted', v['cf_end'] - v['bs_cash'])
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        v = DATA[p]['x']
        print(p, {k: (round(v[k], 2) if isinstance(v.get(k), float) else v.get(k)) for k in
                  ('rev', 'oi', 'seg_ebitda_tot', 'corp_adj', 'corp_rep', 'sp_restr', 'sp_oth_op', 'sp_nonop', 'sp_tax', 'adj_ni_pub', 'cf_cfo', 'cf_wc', 'fcf_pub', 'fcf_oth', 'dps', 'bs_restricted', 'bs_shares')})
    print('\n'.join(LOG))
