"""Self-checks for one extracted period record (models/rtx_build/data/<period>.json). Usage: python3 check_record.py <file> [...]"""
import json, sys

def N(x): return 0.0 if x is None or isinstance(x, str) else float(x)
def has(d, k): return d is not None and d.get(k) is not None and not isinstance(d.get(k), str)

def check(path):
    r = json.load(open(path)); out = []
    def chk(name, a, b, tol=1.0):
        if a is None or b is None: return
        if abs(a - b) > tol: out.append(f'  FAIL {name}: {a:,.3f} vs {b:,.3f} ({a - b:+,.3f})')
    i = r.get('is') or {}
    if has(i, 'sales'):
        op = N(i.get('sales')) - N(i.get('cogs')) - N(i.get('rnd')) - N(i.get('sga')) + N(i.get('other_income')) + sum(N(v) for _, v in i.get('other_op_lines') or [])
        chk('IS op_profit', op, i.get('op_profit'))
        if has(i, 'cogs_products') and has(i, 'cogs_services'): chk('IS cogs = products + services', N(i['cogs_products']) + N(i['cogs_services']), i.get('cogs'))
        if has(i, 'sales_products') and has(i, 'sales_services'): chk('IS sales = products + services', N(i['sales_products']) + N(i['sales_services']), i.get('sales'))
        intr = N(i.get('interest_exp_net')) if has(i, 'interest_exp_net') else N(i.get('interest_exp')) - N(i.get('interest_inc'))
        ebt = N(i.get('op_profit')) + N(i.get('nonservice_pension')) - intr + N(i.get('other_nonop'))
        if has(i, 'ebt'):
            if abs(ebt - N(i['ebt'])) > 1 and has(i, 'nci') and not has(i, 'cont_ops') and abs(ebt - N(i['ebt']) - N(i.get('nci'))) <= 1:
                out.append('  note: ebt is after minority interests (pre-SFAS 160 presentation) — fine if 2006-2008')
            else: chk('IS ebt', ebt, i.get('ebt'))
            base = i.get('cont_ops') if has(i, 'cont_ops') else i.get('net_income')
            if has(i, 'cont_ops') or not has(i, 'nci') or has(i, 'ni_parent') and abs(N(i['net_income']) - N(i['ni_parent'])) > 0.5:
                chk('IS ebt - tax = cont_ops / net income', N(i['ebt']) - N(i.get('tax')), base)
            else:
                chk('IS ebt - tax - minority = net income (pre-SFAS 160)', N(i['ebt']) - N(i.get('tax')) - N(i.get('nci')), base, 1.0) if abs(N(i['ebt']) - N(i.get('tax')) - N(base)) > 1 else None
        if has(i, 'cont_ops') and has(i, 'disc_ops'): chk('IS cont + disc = net income', N(i['cont_ops']) + N(i['disc_ops']), i.get('net_income'))
        if has(i, 'ni_parent') and has(i, 'nci') and abs(N(i['net_income']) - N(i['ni_parent'])) > 0.5: chk('IS NI - NCI = NI parent', N(i['net_income']) - N(i['nci']), i.get('ni_parent'))
        if has(i, 'ni_parent') and has(i, 'shares_diluted') and has(i, 'eps_dil'): chk('IS EPS diluted', N(i['ni_parent']) / N(i['shares_diluted']), i['eps_dil'], 0.015)
    s = r.get('seg') or {}
    if s.get('segments'):
        ss = sum(N(x.get('sales')) for x in s['segments']); so = sum(N(x.get('op_profit')) for x in s['segments'])
        if has(s, 'total_seg_sales'): chk('SEG total segment sales', ss, s['total_seg_sales'])
        if has(s, 'total_seg_op'): chk('SEG total segment OP', so, s['total_seg_op'])
        cs = ss + N(s.get('elim_sales')); chk('SEG sales + elim = consolidated', cs, s.get('consol_sales'))
        if has(i, 'sales'): chk('SEG consolidated sales = IS sales', cs, i['sales'])
        co = so + N(s.get('elim_op')) + N(s.get('corp_op')) + N(s.get('fas_cas')) + N(s.get('acq_acct_adj'))
        chk('SEG OP + elim + corp (+ FAS/CAS + acq adj) = consolidated OP', co, s.get('consol_op'))
        if has(i, 'op_profit'): chk('SEG consolidated OP = IS OP', co, i['op_profit'])
        for x in s['segments']:
            if has(x, 'adj_op') and has(x, 'op_profit') and (has(x, 'restr') or has(x, 'other_items')):
                chk(f'SEG {x["name"]} adj OP = OP + restr - other items', N(x['op_profit']) + N(x.get('restr')) - N(x.get('other_items')), x['adj_op'])
    n = r.get('ngaap') or {}
    if n.get('eps_bridge') and has(n, 'eps_bridge_start') and has(n, 'adj_eps_pub'):
        chk('NGAAP eps bridge', N(n['eps_bridge_start']) + sum(N(v) for _, v in n['eps_bridge']), n['adj_eps_pub'], 0.0101)
    if has(n, 'adj_ni_pub') and has(i, 'shares_diluted') and has(n, 'adj_eps_pub'): chk('NGAAP adj NI / shares = adj EPS', N(n['adj_ni_pub']) / N(i['shares_diluted']), n['adj_eps_pub'], 0.015)
    if has(n, 'adj_op_pub') and has(s, 'consol_op') and (has(n, 'restr_total') or has(n, 'acq_acct_adj_total') or has(n, 'sig_items_op_total')):
        chk('NGAAP adj OP = OP + restr - acq adj - sig items', N(s['consol_op']) + N(n.get('restr_total')) - N(n.get('acq_acct_adj_total')) - N(n.get('sig_items_op_total')), n['adj_op_pub'])
    if has(n, 'fcf_pub'):
        c = r.get('cf') or {}
        if has(c, 'cfo') and has(c, 'capex') and c.get('ytd_months') in (3, 12): chk('NGAAP FCF = CFO + capex (same period)', N(c['cfo']) + N(c['capex']), n['fcf_pub'])
    c = r.get('cf') or {}
    if has(c, 'cfo'):
        chk('CF cfo + cfi + cff + fx = net change', N(c['cfo']) + N(c.get('cfi')) + N(c.get('cff')) + N(c.get('fx')) + sum(N(v) for v in (c.get('disc_ops_cf') or {}).values()), c.get('net_change'))
        chk('CF begin + net change = end', N(c.get('cash_begin')) + N(c.get('net_change')), c.get('cash_end'))
        adj = N(c.get('ni')) + N(c.get('dda')) + N(c.get('deferred_tax')) + N(c.get('sbc')) + N(c.get('pension_noncash')) + N(c.get('k401_match')) + N(c.get('pension_contrib')) + N(c.get('wc_total')) + N(c.get('other_op'))
        chk('CF cfo = ni + adjustments', adj, c['cfo'])
        inv = N(c.get('capex')) + N(c.get('acq')) + N(c.get('divest')) + N(c.get('other_intang')) + N(c.get('customer_financing')) + N(c.get('other_inv'))
        if has(c, 'cfi'): chk('CF cfi = sum of lines', inv, c['cfi'])
        fin = N(c.get('debt_issue')) + N(c.get('debt_repay')) + N(c.get('cp_change')) + N(c.get('st_debt_change')) + N(c.get('dividends')) + N(c.get('nci_dividends')) + N(c.get('buyback')) + N(c.get('other_fin'))
        if has(c, 'cff'): chk('CF cff = sum of lines', fin, c['cff'])
    b = r.get('bs') or {}
    if has(b, 'ta'):
        chk('BS ta = tle', N(b['ta']), b.get('tle'))
        tca = sum(N(b.get(k)) for k in ('cash', 'ar', 'contract_assets', 'inventory', 'other_ca'))
        if has(b, 'tca'): chk('BS current assets', tca, b['tca'])
        ta = N(b.get('tca')) + sum(N(b.get(k)) for k in ('customer_financing', 'ppe', 'rou', 'goodwill', 'intangibles', 'other_nca'))
        chk('BS total assets = components', ta, b['ta'])
        tcl = sum(N(b.get(k)) for k in ('st_debt', 'ap', 'accrued_comp', 'other_accrued', 'contract_liabilities', 'ltd_current'))
        if has(b, 'tcl'): chk('BS current liabilities', tcl, b['tcl'])
        tl = N(b.get('tcl')) + sum(N(b.get(k)) for k in ('ltd', 'lease_ltl', 'pension_obl', 'other_ncl'))
        if has(b, 'tl'): chk('BS total liabilities', tl, b['tl'])
        eq = sum(N(b.get(k)) for k in ('common_stock', 'treasury', 'retained', 'aoci'))
        if has(b, 'equity_parent') and has(b, 'common_stock'): chk('BS parent equity = components', eq, b['equity_parent'])
        if has(b, 'te'): chk('BS total equity', N(b.get('equity_parent')) + N(b.get('nci')), b['te'])
        chk('BS tl + redeemable NCI + equity = tle', N(b.get('tl')) + N(b.get('redeemable_nci')) + N(b.get('te') if has(b, 'te') else N(b.get('equity_parent')) + N(b.get('nci'))), b.get('tle'))
        if has(c, 'cash_end') and has(b, 'cash'):
            ce = N(c['cash_end']) - N(c.get('restricted_cash'))
            if abs(ce - N(b['cash'])) > 1: out.append(f'  note: BS cash {N(b["cash"]):,.0f} vs CF ending cash {N(c["cash_end"]):,.0f} (restricted {N(c.get("restricted_cash")):,.0f}) — explain in notes if not restricted cash')
    cu = r.get('cust') or {}
    for segn, rows in cu.items():
        if not isinstance(rows, dict): continue
        ext = sum(N(v) for k, v in rows.items() if k not in ('Inter-segment sales', 'Products', 'Services', 'Business segment sales', 'Consolidated net sales') and not k.lower().startswith('total'))
        segsales = next((N(x.get('sales')) for x in (s.get('segments') or []) if x.get('name') == segn), None)
        if segsales is not None and ext: chk(f'CUST {segn}: customer rows + inter-segment = segment sales', ext + N(rows.get('Inter-segment sales')), segsales)
        if has(rows, 'Products') and has(rows, 'Services') and ext: chk(f'CUST {segn}: products + services = customer rows', N(rows['Products']) + N(rows['Services']), ext)
    print(path, 'OK' if not out else f'{len(out)} issue(s)')
    for o in out: print(o)
    return not out

if __name__ == '__main__':
    ok = all([check(p) for p in sys.argv[1:]])
    sys.exit(0 if ok else 1)
