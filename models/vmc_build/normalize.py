"""Normalize agent JSON records into one consistent shape and run cross-checks."""
import json, glob, os
from fw import DATA, num, get

def first(*vals):
    for v in vals:
        if num(v) is not None: return num(v)
    return None

def normalize():
    for f in glob.glob(os.path.join(os.path.dirname(__file__), 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        DATA[k] = json.load(open(f))
    out = {}
    for k, d in DATA.items():
        if k == 'outlook': continue
        ng = d.setdefault('ngaap', {}) or {}
        seg = d.setdefault('seg', {}) or {}
        is_ = d.setdefault('is', {}) or {}
        x = first(ng.get('ebitda_bridge_disc_ops'), ng.get('ebitda_bridge_disc_ops_addback'), ng.get('ebitda_bridge_disc_ops_aftertax'))
        ni, tax, it, dda, pub = (num(is_.get('ni_vulcan')), first(ng.get('ebitda_bridge_tax'), is_.get('tax')),
                                 num(is_.get('interest')), num(seg.get('total_dda')), num(ng.get('ebitda_pub')))
        if x is not None and None not in (ni, tax, it, dda, pub):
            base = ni + tax + it + dda
            if abs(base - x - pub) < abs(base + x - pub): x = -x
        ng['ebitda_disc_at'] = x
        if ng.get('ebitda_bridge_tax') is None and pub is not None:
            ng['ebitda_bridge_tax'] = is_.get('tax')
        it_ps, st_ps, dil = num(ng.get('eps_items_after_tax_ps')), num(ng.get('eps_bridge_start_ps')), num(is_.get('eps_dil'))
        if it_ps is not None or num(ng.get('adj_eps_pub')) is not None:
            adj = (it_ps or 0) + ((st_ps - dil) if (st_ps is not None and dil is not None) else 0)
            ng['e_items_incl'] = round(adj, 4)
        r = num(ng.get('roic_pub'))
        if r is not None and abs(r) > 1: ng['roic_pub'] = r / 100
        out[k] = d
    # Vulcan 2007-09 EBITDA excluded discontinued operations (after tax); FY2008 release EBITDA also preceded the goodwill impairment
    for y in ('2007', '2008', '2009'):
        d = DATA[y]
        if d['ngaap'].get('ebitda_disc_at') is None and num(d['is'].get('disc_ops')) is not None:
            d['ngaap']['ebitda_disc_at'] = -num(d['is']['disc_ops'])
    ai = DATA['2008']['ngaap'].setdefault('adj_items', {}) or {}
    if not num(ai.get('impairment')):
        ai['impairment'] = 252.7
        DATA['2008']['ngaap']['adj_items'] = ai
    return out

def checks(verbose=True):
    issues = []
    def chk(k, name, a, b, tol=0.25):
        if a is None or b is None: return
        if abs(a - b) > tol: issues.append((k, name, round(a - b, 2), round(a, 1), round(b, 1)))
    for k, d in sorted(DATA.items()):
        if k == 'outlook': continue
        s, i, n, cf, bs = d.get('seg') or {}, d.get('is') or {}, d.get('ngaap') or {}, d.get('cf') or {}, d.get('bs') or {}
        g = lambda dd, f: num(dd.get(f))
        segrev = [g(s, x) for x in ('agg_rev', 'asph_rev', 'conc_rev', 'cem_rev', 'calc_rev', 'other_seg_rev')]
        if g(s, 'agg_rev') is not None:
            tot = sum(v or 0 for v in segrev) + (g(s, 'interseg_total') or 0) + (g(s, 'delivery_rev') or 0)
            chk(k, 'seg rev', tot, g(i, 'total_rev'))
        seggp = [g(s, x) for x in ('agg_gp', 'asph_gp', 'conc_gp', 'cem_gp', 'calc_gp', 'other_seg_gp')]
        if g(s, 'agg_gp') is not None: chk(k, 'seg gp', sum(v or 0 for v in seggp), g(i, 'gp'))
        segdda = [g(s, x) for x in ('agg_dda', 'asph_dda', 'conc_dda', 'cem_dda', 'calc_dda', 'other_seg_dda', 'other_dda')]
        if g(s, 'agg_dda') is not None: chk(k, 'seg dda', sum(v or 0 for v in segdda), g(s, 'total_dda'))
        if g(i, 'total_rev') is not None and g(i, 'cost_of_rev') is not None:
            chk(k, 'gp', g(i, 'total_rev') - g(i, 'cost_of_rev'), g(i, 'gp'))
        op = (g(i, 'gp') or 0) - (g(i, 'sag') or 0) + (g(i, 'gain_sale') or 0) + (g(i, 'other_op') or 0)
        chk(k, 'op', op, g(i, 'op_earnings'))
        if g(i, 'op_earnings') is not None:
            chk(k, 'ebt', g(i, 'op_earnings') + (g(i, 'nonop') or 0) - (g(i, 'interest') or 0), g(i, 'ebt'))
        if g(i, 'ebt') is not None and g(i, 'tax') is not None:
            chk(k, 'cont', g(i, 'ebt') - g(i, 'tax'), g(i, 'cont_ops'))
        if g(i, 'cont_ops') is not None:
            chk(k, 'ne', g(i, 'cont_ops') + (g(i, 'disc_ops') or 0), g(i, 'net_earnings'))
        if g(i, 'net_earnings') is not None:
            chk(k, 'ni', g(i, 'net_earnings') - (g(i, 'nci') or 0), g(i, 'ni_vulcan'))
        if g(n, 'ebitda_pub') is not None and g(i, 'ni_vulcan') is not None:
            e = g(i, 'ni_vulcan') + (num(n.get('ebitda_bridge_tax')) or 0) + (g(i, 'interest') or 0) + (g(s, 'total_dda') or 0) + (num(n.get('ebitda_disc_at')) or 0)
            chk(k, 'ebitda', e, g(n, 'ebitda_pub'), 0.35)
        if g(n, 'adj_ebitda_pub') is not None and g(n, 'ebitda_pub') is not None:
            ai = n.get('adj_items') or {}
            tot = sum(num(v) or 0 for kk, v in ai.items() if kk != 'other_label')
            chk(k, 'adj ebitda', g(n, 'ebitda_pub') + tot, g(n, 'adj_ebitda_pub'), 0.35)
        if g(n, 'adj_eps_pub') is not None and g(i, 'eps_dil') is not None:
            e = g(i, 'eps_dil') + (num(n.get('e_items_incl')) or 0) + (num(n.get('eps_discrete_tax_ps')) or 0)
            chk(k, 'adj eps', e, g(n, 'adj_eps_pub'), 0.015)
        if cf:
            fo = ['net_earnings', 'dda', 'noncash_lease', 'gain_sale', 'pension_contrib', 'sbc', 'deferred_tax', 'wc_change', 'other_op']
            chk(k, 'cfo', sum(num(cf.get(x)) or 0 for x in fo), num(cf.get('cfo')))
            fi = ['capex', 'proceeds_ppe', 'proceeds_bus', 'acquisitions', 'other_inv']
            chk(k, 'cfi', sum(num(cf.get(x)) or 0 for x in fi), num(cf.get('cfi')))
            ff = ['debt_proceeds', 'debt_repay', 'buyback', 'dividends', 'stock_proceeds', 'other_fin']
            chk(k, 'cff', sum(num(cf.get(x)) or 0 for x in ff), num(cf.get('cff')))
            if num(cf.get('cfo')) is not None:
                chk(k, 'net chg', num(cf['cfo']) + num(cf['cfi']) + num(cf['cff']) + (num(cf.get('fx')) or 0), num(cf.get('net_change')))
                chk(k, 'cash end', num(cf.get('cash_begin')) + num(cf.get('net_change')), num(cf.get('cash_end')))
        if bs:
            ca = ['cash', 'restricted_cash', 'ar_net', 'inventories', 'other_current', 'assets_held_for_sale']
            chk(k, 'tca', sum(num(bs.get(x)) or 0 for x in ca), num(bs.get('total_current_assets')))
            nca = ['invest_lt_rec', 'ppe_net', 'rou_assets', 'goodwill', 'intangibles', 'other_noncurrent']
            chk(k, 'ta', (num(bs.get('total_current_assets')) or 0) + sum(num(bs.get(x)) or 0 for x in nca), num(bs.get('total_assets')))
            cl = ['current_maturities', 'short_term_debt', 'payables', 'other_current_liab', 'liab_held_for_sale']
            chk(k, 'tcl', sum(num(bs.get(x)) or 0 for x in cl), num(bs.get('total_current_liab')))
            ncl = ['ltd', 'deferred_tax', 'deferred_revenue', 'lt_lease', 'other_noncurrent_liab']
            chk(k, 'tl', (num(bs.get('total_current_liab')) or 0) + sum(num(bs.get(x)) or 0 for x in ncl), num(bs.get('total_liabilities')))
            eq = ['common_stock', 'capital_excess', 'retained_earnings', 'aoci', 'treasury_stock']
            chk(k, 'veq', sum(num(bs.get(x)) or 0 for x in eq), num(bs.get('total_vulcan_equity')))
            chk(k, 'tle', (num(bs.get('total_liabilities')) or 0) + (num(bs.get('total_equity')) or 0), num(bs.get('total_liab_equity')))
            chk(k, 'bal', num(bs.get('total_assets')), num(bs.get('total_liab_equity')))
    if verbose:
        for x in issues: print('ISSUE', x)
    return issues

if __name__ == '__main__':
    normalize(); checks()
