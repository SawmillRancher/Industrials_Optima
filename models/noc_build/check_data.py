"""Consistency checks on the normalised Northrop Grumman data: statement arithmetic, segment sums and the reconciliation to operating
income, published non-GAAP figures, EPS, cash-flow and balance-sheet tie-outs, XBRL cross-checks and quarters vs years."""
import json, os
import normalize
D = normalize.run()
REC = normalize.REC
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok = [], [0]
def chk(name, a, b, tol=0.6):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol: bad.append(f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})')
CUR = ['as', 'ds', 'ms', 'ss']
for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    r = REC.get(p, {}); xb = r.get('x') or {}
    # income statement
    if v.get('cos') is not None:
        chk(f'{p} OI identity', v['rev'] - v['cos'] - v['ga'] - n(v.get('oth_op')), v['oi'])
    chk(f'{p} EBT identity', v['oi'] - n(v.get('int_exp')) + n(v.get('int_inc')) + n(v.get('nonop_fas')) + n(v.get('mtm')) + n(v.get('oth_nonop')), v.get('ebt'))
    if v.get('cont_ops') is not None: chk(f'{p} tax identity', v['ebt'] - v['tax'], v['cont_ops'])
    chk(f'{p} NI identity', n(v.get('cont_ops')) + n(v.get('disc_ops')), v.get('ni'))
    if v.get('sh_d'): chk(f'{p} EPS', (v['ni'] + n(v.get('eps_num_adj'))) / v['sh_d'], v.get('eps_d'), 0.0101 if v['ni'] >= 0 else 0.03)
    # XBRL cross-checks (first filed): 2007-08 XBRL comparatives are the TASC-recast values, skipped
    fy = int(p) if p.isdigit() else int('20' + p[-2:])
    if fy >= 2009 and not v.get('recast_mtm_2018'):
        chk(f'{p} XBRL sales', v.get('rev'), xb.get('rev')); chk(f'{p} XBRL OI', v.get('oi'), xb.get('oi')); chk(f'{p} XBRL NI', v.get('ni'), xb.get('ni'))
        chk(f'{p} XBRL EPS', v.get('eps_d'), xb.get('eps_d'), 0.0101); chk(f'{p} XBRL TA', v.get('bs_ta'), xb.get('ta'))
    # segments: current structure
    if v.get('cur_as_s') is not None:
        chk(f'{p} cur seg sales', sum(v[f'cur_{k}_s'] for k in CUR) + n(v.get('cur_elim_s')), v.get('seg_total_sales') if v.get('cur_basis') == 'as reported' else v.get('rev'))
        chk(f'{p} cur seg OI', sum(v[f'cur_{k}_oi'] for k in CUR) + n(v.get('cur_elim_oi')), v.get('cur_seg_oi'))
        if v.get('cur_basis') == 'as reported': chk(f'{p} cur seg OI pub', v.get('cur_seg_oi'), v.get('seg_oi_pub'))
    for blk, keys in (('l16', ['aer', 'inn', 'mis', 'tsv']), ('l09', ['aer', 'ele', 'inf', 'shp', 'tec']), ('l06', ['ins', 'aer', 'ele', 'shp', 'oth'])):
        if v.get(f'{blk}_seg_oi') is not None:
            chk(f'{p} {blk} sales', sum(n(v.get(f'{blk}_{k}_s')) for k in keys) + n(v.get(f'{blk}_elim_s')), v.get('rev'))
            chk(f'{p} {blk} OI', sum(n(v.get(f'{blk}_{k}_oi')) for k in keys) + n(v.get(f'{blk}_elim_oi')), v.get(f'{blk}_seg_oi'))
    chk(f'{p} seg total sales', v.get('seg_total_sales'), v.get('rev'))
    if v.get('seg_oi_pub') is not None:
        gain = 0.0 if (v.get('rc_intang') is not None and v.get('rc_other_unalloc') is not None) else n(v.get('rc_gain')) + n(v.get('rc_divest'))
        chk(f'{p} recon to OI', v['seg_oi_pub'] + n(v.get('rc_fascas')) + n(v.get('rc_unalloc')) + gain + n(v.get('rc_royalty')) + n(v.get('rc_other')), v['oi'])
        if abs(n(v.get('rc_other'))) > 0.6 and not v.get('rc_other_lab'): bad.append(f"{p} recon: unlabelled residual {v['rc_other']:+.1f}")
    # published adjusted EPS vs model (MTM: diluted EPS - MTM net of tax per share; pension-adjusted: diluted EPS + after-tax adjustment per share)
    if v.get('adj_def') == 'MTM' and v.get('mtm_net_pub') is not None and v.get('sh_d'):
        chk(f'{p} MTM-adj EPS', (v['ni'] + v['mtm_net_pub']) / v['sh_d'] if v.get('mtm_adj_ni_pub') is None else v['mtm_adj_ni_pub'] / v['sh_d'], v['adj_eps_pub'], 0.03)
    if v.get('adj_def') == 'PENSION' and v.get('pens_adj_ps') is not None:
        base = v.get('eps_d_cont') if v.get('adj_eps_basis') == 'continuing operations' and v.get('eps_d_cont') is not None else v['eps_d']
        chk(f'{p} pension-adj EPS', base + v['pens_adj_ps'], v['adj_eps_pub'], 0.0101)
    # cash flow
    if v.get('cf_cfo') is not None:
        chk(f'{p} CF sum', v['cf_ni'] + v['cf_dda'] + v['cf_sbc'] + v['cf_def'] + n(v.get('cf_pens')) + n(v.get('cf_gain')) + v['cf_wc'], v['cf_cfo'])
        chk(f'{p} cash roll', n(v.get('cf_beg')) + v['cf_net'] + n(v.get('cf_fx')), v.get('cf_end'))
        if v.get('fcf_pub') is not None and fy >= 2016: chk(f'{p} FCF', v['cf_cfo'] + v['cf_capex'], v['fcf_pub'])
        if fy not in (2018, 2019): chk(f'{p} cash vs BS', v.get('cf_end'), v.get('bs_cash'))
        if fy >= 2009 and p.isdigit(): chk(f'{p} XBRL CFO', v['cf_cfo'], xb.get('cfo_ytd'))
    # balance sheet
    chk(f'{p} BS', v.get('bs_ta'), v.get('bs_tle'))
    if v.get('bs_tl') is not None: chk(f'{p} BS TL+E', v['bs_tl'] + n(v.get('bs_eq')), v.get('bs_tle'))
# quarters vs years
for y in range(2013, 2026):
    yy = str(y)[2:]
    for k in ('rev', 'oi', 'ni', 'tax', 'ebt', 'int_exp', 'nonop_fas', 'mtm', 'cf_cfo', 'cf_capex', 'cf_bb', 'cf_div', 'cf_dda', 'cf_sbc', 'rc_fascas', 'rc_unalloc',
              'cur_as_s', 'cur_ds_s', 'cur_ms_s', 'cur_ss_s', 'cur_seg_oi', 'l09_aer_s', 'l16_aer_s', 'ga', 'cos'):
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        if all(q is not None for q in qs) and x(str(y)).get(k) is not None:
            tol = 1.6 if k.startswith('cur_') else 0.6
            chk(f'FY{y} {k} sum-q', sum(qs), x(str(y)).get(k), tol)
        elif x(str(y)).get(k) is not None and k in ('rev', 'oi', 'ni', 'cf_cfo'): bad.append(f'FY{y} {k}: quarters missing {[i + 1 for i, q in enumerate(qs) if q is None]}')
EXPECTED = {
    'FY2019 cur_seg_oi sum-q': 'the 2019 quarters recast on the 2020 segment structure in the 2020 releases sum to $3,967m segment operating income vs $3,978m for the year in the Q4 2020 release and FY2020 10-K (company recast; the $11m sits in unallocated corporate expense)',
    'FY2019 rc_unalloc sum-q': 'counterpart of the segment operating income difference above (same $11m)',
}
exp = [b for b in bad if b.split(':')[0] in EXPECTED]
bad = [b for b in bad if b.split(':')[0] not in EXPECTED]
print('\n'.join(bad) or 'all checks pass')
for b in exp: print('documented exception:', b, '--', EXPECTED[b.split(':')[0]])
print(f'{ok[0]} checks, {len(bad)} issues')
if normalize.LOG: print('\nLOG:\n' + '\n'.join(normalize.LOG))
