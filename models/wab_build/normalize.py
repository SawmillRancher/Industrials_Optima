"""Harmonise the extraction JSON into the model's data keys and run cross-checks.

- 2-for-1 split (June 2013): pre-split per-share data and share counts restated to the post-split basis.
- Cash flow: quarterly records carry year-to-date statements; discrete quarters derived (Q4 = FY − 9M).
- Derived 'other' lines so each statement section sums to its published subtotal.
- Bridges: operating-level items reconciled to the published adjusted operating income; EPS bridge split into
  pre-tax items / items below operating income / tax effect / discrete tax & NCI (table bridges) or per-share items
  (narrative bridges); EBITDA basis differences vs the company definition in force.
"""
import json
from fw import DATA, num, load_data

def N(x): return num(x) or 0.0
def r1(x): return None if x is None else round(x, 3)

LEGACY = [('spe', ('Specialty Products & Electronics', 'Freight Electronics & Specialty Products')),
          ('brake', ('Brake Products',)), ('reman', ('Remanufacturing, Overhaul & Build',)),
          ('transit', ('Transit Products', 'Other Transit Products')), ('other', ('Other',))]
CF_CORE = ['net_income', 'dda', 'sbc', 'wc_change', 'cfo', 'capex', 'acquisitions', 'cfi', 'debt_proceeds', 'debt_repay',
           'buyback', 'dividends', 'cff', 'fx', 'net_change']
CF_OPT = ['deferred_tax', 'proceeds_disp']
LOG = []

def qkeys(y):
    yy = str(y)[2:]
    return [f'Q{q}-{yy}' for q in (1, 2, 3, 4)]

def split_adjust(d):
    i = d['is']
    if i.get('per_share_basis') != 'pre_split': return
    for k in ('shares_basic', 'shares_diluted'):
        if num(i.get(k)) is not None: i[k] = num(i[k]) * 2
    for k in ('eps_basic', 'eps_dil', 'eps_cont_dil', 'dps'):
        if num(i.get(k)) is not None: i[k] = num(i[k]) / 2
    ng = d['ngaap']
    if num(ng.get('adj_eps_pub')) is not None: ng['adj_eps_pub'] = num(ng['adj_eps_pub']) / 2
    if num(ng.get('eps_bridge_start_ps')) is not None: ng['eps_bridge_start_ps'] = num(ng['eps_bridge_start_ps']) / 2
    ng['eps_bridge_lines'] = [[a, num(b) / 2 if num(b) is not None else b] for a, b in (ng.get('eps_bridge_lines') or [])]
    for row in ng.get('adj_table') or []:
        if isinstance(row[1], dict) and num(row[1].get('eps')) is not None: row[1]['eps'] = num(row[1]['eps']) / 2
    bs = d.get('bs') or {}
    if num(bs.get('shares_outstanding_end')) is not None:
        v = num(bs['shares_outstanding_end'])
        if v < 60: bs['shares_outstanding_end'] = v * 2
    ex = d.get('extra') or {}
    if num(ex.get('dps_declared')) is not None: ex['dps_declared'] = num(ex['dps_declared']) / 2
    i['per_share_basis'] = 'post_split (restated ×2 shares, ÷2 per share)'

def cf_derived(cf):
    """year-to-date (or FY) derived lines."""
    o = {k: num(cf.get(k)) for k in CF_CORE + CF_OPT}
    o['oth'] = N(o['cfo']) - N(o['net_income']) - N(o['dda']) - N(o['sbc']) - N(o['deferred_tax']) - N(o['wc_change']) if o['cfo'] is not None else None
    o['oinv'] = N(o['cfi']) - N(o['capex']) - N(o['acquisitions']) - N(o['proceeds_disp']) if o['cfi'] is not None else None
    o['ofin'] = N(o['cff']) - N(o['debt_proceeds']) - N(o['debt_repay']) - N(o['buyback']) - N(o['dividends']) if o['cff'] is not None else None
    o['cash_begin'] = num(cf.get('cash_begin')); o['cash_end'] = num(cf.get('cash_end'))
    o['ytd'] = num(cf.get('ytd_months'))
    return o

def build_cfq():
    years = sorted({int(k) for k in DATA if k.isdigit()})
    for y in years:
        if str(y) in DATA and DATA[str(y)].get('cf'):
            DATA[str(y)]['cfq'] = {k: v for k, v in cf_derived(DATA[str(y)]['cf']).items() if k != 'ytd'}
    for y in range(2013, 2027):
        prev = None
        for qi, k in enumerate(qkeys(y), start=1):
            d = DATA.get(k)
            if not d or not d.get('cf'): prev = None; continue
            cur = cf_derived(d['cf'])
            if qi == 4 and (cur['ytd'] or 12) != 12 and str(y) in DATA:
                cur = cf_derived(DATA[str(y)]['cf'])
            if cur['ytd'] not in (None, 3 * qi) and not (qi == 4 and cur['ytd'] in (None, 12)):
                LOG.append(f'{k}: cf ytd_months {cur["ytd"]} unexpected')
            if qi == 1:
                q = {kk: cur[kk] for kk in CF_CORE + CF_OPT + ['oth', 'oinv', 'ofin']}
                q['cash_begin'], q['cash_end'] = cur['cash_begin'], cur['cash_end']
            elif prev is None:
                q = None; LOG.append(f'{k}: no prior-quarter YTD cash flow — discrete quarter not derived')
            else:
                q = {}
                for kk in CF_CORE + ['oth', 'oinv', 'ofin']:
                    q[kk] = None if cur[kk] is None else cur[kk] - N(prev[kk])
                for kk in CF_OPT:
                    q[kk] = (cur[kk] - prev[kk]) if (cur[kk] is not None and prev[kk] is not None) else None
                # fold optional lines without both YTD values into the derived lines
                q['oth'] = N(q['cfo']) - N(q['net_income']) - N(q['dda']) - N(q['sbc']) - N(q['deferred_tax']) - N(q['wc_change'])
                q['oinv'] = N(q['cfi']) - N(q['capex']) - N(q['acquisitions']) - N(q['proceeds_disp'])
                q['cash_begin'], q['cash_end'] = prev['cash_end'], cur['cash_end']
            if q is not None:
                d['cfq'] = {kk: r1(v) for kk, v in q.items()}
            prev = cur
    # Q2-26: also keep in the quarter (discrete) — done above

def build_bsx():
    for k, d in DATA.items():
        bs = d.get('bs') if isinstance(d, dict) else None
        if not bs or k in ('outlook', 'acquisitions'): continue
        g = lambda f: num(bs.get(f))
        x = {}
        ar = g('receivables'); x['ar'] = None if ar is None else ar + N(g('unbilled'))
        tca = g('total_current_assets')
        if tca is not None and g('cash') is not None:
            x['oca'] = tca - N(g('cash')) - N(g('restricted_cash')) - N(x['ar']) - N(g('inventories'))
        ta = g('total_assets')
        if ta is not None and tca is not None:
            x['onca'] = ta - tca - N(g('ppe')) - N(g('goodwill')) - N(g('intangibles'))
        tcl = g('total_current_liab')
        if tcl is not None:
            x['ocl'] = tcl - N(g('ap')) - N(g('customer_deposits')) - N(g('accrued_comp')) - N(g('accrued_warranty')) - N(g('current_debt'))
        tl = g('total_liabilities')
        if tl is None and g('total_le') is not None and g('total_equity') is not None:
            tl = g('total_le') - g('total_equity'); x['tl_derived'] = tl
        if tl is not None and tcl is not None:
            x['oncl'] = tl - tcl - N(g('ltd')) - N(g('pension')) - N(g('deferred_tax'))
        cap = g('common_apic')
        if cap is None and g('wab_equity') is not None:
            cap = g('wab_equity') - N(g('treasury')) - N(g('retained')) - N(g('aoci'))
        x['cap'] = cap
        cfq = d.get('cfq') or {}
        ce = num((d.get('cf') or {}).get('cash_end'))
        if ce is not None and g('cash') is not None:
            x['rcf'] = round(ce - g('cash'), 3)
        # BS integrity
        if ta is not None and g('total_le') is not None and abs(ta - g('total_le')) > 0.6:
            LOG.append(f'{k}: BS TA {ta} vs TL&E {g("total_le")}')
        d['bsx'] = {kk: r1(v) for kk, v in x.items()}

def table_rows(ng):
    t = [r for r in (ng.get('adj_table') or []) if isinstance(r, list) and len(r) == 2 and isinstance(r[1], dict)]
    if len(t) < 2: return None, None, None
    return t[0][1], t[-1][1], t[1:-1]

def build_bridges():
    for k, d in DATA.items():
        if k in ('outlook', 'acquisitions') or not isinstance(d, dict) or 'ngaap' not in d: continue
        ng, i = d['ngaap'], d['is']
        it = ng.setdefault('items', {}) or {}
        ng['items'] = it
        x = d.setdefault('x', {})
        # other operating lines
        x['othop'] = sum(N(b) for _, b in (i.get('other_op_lines') or [])) or None
        # D&A
        dda = num(ng.get('ebitda_dda'))
        if dda is None: dda = num((d.get('cfq') or {}).get('dda'))
        x['dda'] = dda
        rep, adj, mid = table_rows(ng)
        op_detail = ['restructuring', 'inventory_pa', 'transaction', 'amortization', 'contract', 'litigation', 'other_op']
        if rep is not None and num(adj.get('eps')) is not None:
            opi = N(adj.get('op')) - N(rep.get('op'))
            s = sum(N(it.get(f)) for f in op_detail)
            if abs(opi - s) > 0.5:
                it['other_op'] = N(it.get('other_op')) + (opi - s)
                LOG.append(f'{k}: op-level items residual {opi - s:+.1f} moved to other_op')
            x['e_nonop'] = N(adj.get('int_other')) - N(rep.get('int_other'))
            taxd = N(adj.get('tax')) - N(rep.get('tax'))
            disc = N(it.get('discrete_tax'))
            ncid = N(adj.get('nci')) - N(rep.get('nci'))
            x['e_tax'] = taxd - disc
            x['e_disc'] = disc + ncid
            if ng.get('adj_op_pub') is None and num(adj.get('op')) is not None: ng['adj_op_pub'] = num(adj['op'])
            # tie: reported NI + items = adjusted NI
            chk = N(rep.get('ni_wab')) + opi + x['e_nonop'] + taxd + ncid - N(adj.get('ni_wab'))
            if abs(chk) > 0.6: LOG.append(f'{k}: adj table does not tie by {chk:+.1f}')
            x['e_ps_in'] = None
        elif num(ng.get('adj_eps_pub')) is not None:
            lines = ng.get('eps_bridge_lines') or []
            diff = num(ng['adj_eps_pub']) - N(i.get('eps_dil'))
            s = sum(N(b) for _, b in lines) if lines else None
            x['e_ps_in'] = s if (s is not None and abs(s - diff) <= 0.015) else diff
            if s is not None and abs(s - diff) > 0.015:
                LOG.append(f'{k}: per-share bridge lines {s:+.2f} vs adj − GAAP EPS {diff:+.2f}; using the difference')
            if ng.get('adj_op_pub') is not None:
                s = sum(N(it.get(f)) for f in op_detail)
                opi = num(ng['adj_op_pub']) - N(i.get('op_income'))
                if abs(opi - s) > 0.5:
                    it['other_op'] = N(it.get('other_op')) + (opi - s)
                    LOG.append(f'{k}: op-level items residual {opi - s:+.1f} (narrative bridge) moved to other_op')
        else:
            x['e_ps_in'] = None
        # EBITDA
        eb = num(ng.get('ebitda_pub')); aeb = num(ng.get('adj_ebitda_pub'))
        if eb is not None:
            model = N(i.get('op_income')) + N(i.get('other_inc')) + N(dda)
            b = eb - model
            x['r_basis'] = round(b, 3) if abs(b) > 1.0 else 0.0
        if aeb is not None:
            restr, inv, trans = N(it.get('restructuring')), N(it.get('inventory_pa')), N(it.get('transaction'))
            x['r_restr'], x['r_inv'], x['r_trans'] = restr, inv, trans
            x['r_oth'] = round(aeb - (eb if eb is not None else 0) - restr - inv - trans, 3)

def build_misc():
    for k, d in DATA.items():
        if k in ('outlook', 'acquisitions') or not isinstance(d, dict) or 'seg' not in d: continue
        xl = {}
        for key, labs in LEGACY:
            v = [num(b) for a, b in (d['seg'].get('legacy_pl') or []) if a in labs]
            v = [z for z in v if z is not None]
            if v: xl[key] = sum(v)
        d['xl'] = xl
        if d['is'].get('dps') is None and d.get('extra', {}).get('dps_declared') is not None:
            d['is']['dps'] = num(d['extra']['dps_declared'])
    # debt split at 30-Jun-26 (facilities vs notes & term loans) from the 10-Q debt note
    o = DATA.get('outlook', {}).get('debt_q2_26', {})
    q = DATA['Q2-26'].setdefault('x', {})
    fac = 638.0 + 400.0   # revolver drawn + receivables securitization (10-Q debt note)
    tot = N(DATA['Q2-26']['bs'].get('current_debt')) + N(DATA['Q2-26']['bs'].get('ltd'))
    q['fac'] = fac; q['notes'] = round(tot - fac, 1)
    # PPA by closing quarter
    acq = DATA.get('acquisitions', {})
    deals = acq.get('acquisitions') if isinstance(acq, dict) else acq
    return deals

def run():
    load_data()
    for k, d in DATA.items():
        if isinstance(d, dict) and 'is' in d: split_adjust(d)
    build_cfq(); build_bsx(); build_bridges(); deals = build_misc()
    checks()
    return deals

def checks():
    for k, d in sorted(DATA.items()):
        if not isinstance(d, dict) or 'is' not in d: continue
        i, s = d['is'], d['seg']
        if num(s.get('frt_rev')) is not None and num(s.get('trn_rev')) is not None and num(i.get('net_sales')) is not None:
            if abs(N(s['frt_rev']) + N(s['trn_rev']) - N(i['net_sales'])) > 0.6: LOG.append(f'{k}: segments vs net sales')
        op = N(i.get('gp')) - N(i.get('sga')) - N(i.get('eng')) - N(i.get('amort')) - N(d.get('x', {}).get('othop'))
        if num(i.get('op_income')) is not None and abs(op - N(i['op_income'])) > 0.6: LOG.append(f'{k}: IS op income {op:.1f} vs {i["op_income"]}')
        cq = d.get('cfq')
        if cq and cq.get('cfo') is not None:
            t = N(cq['cfo']) + N(cq['cfi']) + N(cq['cff']) + N(cq['fx']) - N(cq['net_change'])
            if abs(t) > 0.6: LOG.append(f'{k}: CF sections vs net change {t:+.1f}')
            if cq.get('cash_begin') is not None and abs(N(cq['cash_begin']) + N(cq['net_change']) - N(cq['cash_end'])) > 0.6:
                LOG.append(f'{k}: cash roll {N(cq["cash_begin"]) + N(cq["net_change"]) - N(cq["cash_end"]):+.1f}')

if __name__ == '__main__':
    run()
    print('\n'.join(LOG) or 'no issues')
