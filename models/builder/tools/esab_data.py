"""Load ESAB extraction JSONs (USD millions) into model series S[key][col_label]."""
import json, os, re
from collections import defaultdict

BASE = os.path.join(os.path.dirname(__file__), '..', 'esab', 'extract')
CFX = os.path.join(os.path.dirname(__file__), '..', 'colfax', 'extract', 'FABTECH.json')


def lab(p):
    if p.startswith('FY'):
        return int(p[2:])
    q, y = p.split('-')
    return f'{q}/{y[2:]}'


def fnum(x):
    return None if x is None else float(x)


def ssum(lst):
    return sum(float(v) for _, v in (lst or []) if v is not None)


SEGA = {'Americas': 'AM', 'EMEA & APAC': 'EA', 'EMEA and APAC': 'EA', 'Total': 'TOT', 'Consolidated': 'TOT'}


def seg_key(name):
    for k, v in SEGA.items():
        if name.strip().lower() == k.lower():
            return v
    if name.lower().startswith('america'):
        return 'AM'
    if 'emea' in name.lower():
        return 'EA'
    if name.lower().startswith(('total', 'consol')):
        return 'TOT'
    return None


def cat_adj(label):
    s = label.lower()
    if 'depreciation' in s:
        return 'da'
    if 'restructur' in s:
        return 'restr'
    if 'performance option' in s:
        return 'perf'
    if 'amortiz' in s or 'acquisition' in s or 'step up' in s or 'step-up' in s:
        return 'acq'
    if 'pension' in s:
        return 'pen'
    if 'separation' in s:
        return 'sep'
    return 'oth'


def load():
    P = {}
    for fn in sorted(os.listdir(BASE)):
        if re.match(r'(FY\d{4}|Q[1-4]-\d{4})\.json$', fn):
            P[fn[:-5]] = json.load(open(os.path.join(BASE, fn)))
    return P


def build():
    P = load()
    S = defaultdict(dict)

    def put(k, p, v):
        if v is not None:
            S[k][lab(p)] = float(v)

    for p, d in P.items():
        I = d.get('is') or {}
        if I:
            for k in ('net_sales', 'cogs', 'sga', 'restructuring', 'operating_income', 'interest_expense_other_net', 'pretax_cont',
                      'income_taxes', 'ni_cont', 'disc_ops', 'net_income', 'nci_income', 'ni_attrib', 'mcps_dividends', 'ni_common',
                      'eps_basic_cont', 'eps_diluted_cont', 'eps_basic', 'eps_diluted', 'shares_basic', 'shares_diluted', 'dps_declared'):
                put('is_' + k, p, I.get(k))
            put('is_othop', p, ssum(I.get('other_operating')))
            put('is_nonop_oth', p, ssum(I.get('pension_settlement_or_other_nonop')))
        B = d.get('bs')
        if B:
            for k in ('cash', 'ar', 'inventories', 'total_current_assets', 'ppe_net', 'goodwill', 'intangibles_net', 'rou_assets',
                      'total_assets', 'current_debt', 'ap', 'accrued_liabilities', 'total_current_liabilities', 'long_term_debt',
                      'total_liabilities', 'mcps', 'common_stock_apic', 'retained_earnings_or_net_parent_investment', 'aoci',
                      'total_esab_equity', 'nci_equity', 'total_equity', 'total_liabilities_and_equity', 'asbestos_insurance_assets',
                      'asbestos_liabilities_total', 'shares_outstanding_period_end'):
                put('bs_' + k, p, B.get(k))
        C = d.get('cf_ytd')
        if C:
            S['_cfytd'][lab(p)] = C
        PL = d.get('product_lines') or {}
        put('pl_equipment', p, PL.get('equipment'))
        put('pl_consumables', p, PL.get('consumables'))
        R = d.get('release') or {}
        seg = R.get('segments') or {}
        for name, x in seg.items():
            sk = seg_key(name)
            if not sk or not isinstance(x, dict):
                continue
            for f in ('net_sales', 'operating_income', 'restructuring', 'acq_amort_other', 'da_other', 'adj_ebitda', 'russia_adj_ebitda', 'core_adj_ebitda'):
                put(f'seg_{sk}_{f}', p, x.get(f))
            put(f'seg_{sk}_other_adj', p, ssum(x.get('other_adj')))
        put('russia_sales', p, R.get('russia_net_sales'))
        for blk, pre in (('sales_change', 'sc'), ('core_sales_change', 'csc')):
            for name, x in (R.get(blk) or {}).items():
                sk = seg_key(name)
                if not sk or not isinstance(x, dict):
                    continue
                for f in ('prior', 'organic', 'organic_pct', 'acquisitions', 'acquisitions_pct', 'fx', 'fx_pct', 'total', 'total_pct', 'current'):
                    put(f'{pre}_{sk}_{f}', p, x.get(f))
        ar = R.get('adj_ebitda_recon') or {}
        put('pub_adj_ebitda', p, ar.get('adj_ebitda'))
        put('pub_russia_ebitda', p, ar.get('russia'))
        put('pub_core_ebitda', p, ar.get('core_adj_ebitda'))
        for lbl, v in ar.get('items') or []:
            if v is None:
                continue
            k = 'ae_' + cat_adj(lbl)
            S[k][lab(p)] = S[k].get(lab(p), 0.0) + float(v)
        sp = R.get('acq_amort_split') or {}
        put('acq_txn', p, sp.get('transaction_diligence_integration'))
        put('acq_amort', p, sp.get('amortization_and_inventory_stepup'))
        put('acq_split_oth', p, ssum(sp.get('other')))
        an = R.get('adj_net_income') or {}
        put('pub_ni_cont_attrib', p, an.get('ni_cont_attrib_gaap'))
        for lbl, v in an.get('pretax_items') or []:
            if v is None:
                continue
            k = 'an_' + cat_adj(lbl)
            S[k][lab(p)] = S[k].get(lab(p), 0.0) + float(v)
        if an:
            put('an_taxeff', p, an.get('tax_effect'))
            put('an_discrete', p, an.get('discrete_tax'))
            put('an_other', p, ssum(an.get('other_items')))
            S['_an_other_items'][lab(p)] = an.get('other_items') or []
        put('pub_adj_ni', p, an.get('adjusted_net_income'))
        put('pub_russia_ni', p, an.get('russia'))
        put('pub_core_adj_ni', p, an.get('core_adjusted_net_income'))
        put('pub_eps_cont', p, R.get('eps_diluted_cont_gaap'))
        put('pub_adj_eps', p, R.get('adjusted_eps'))
        put('pub_core_adj_eps', p, R.get('core_adjusted_eps'))
        fc = R.get('adj_free_cash_flow') or {}
        put('pub_adj_fcf', p, fc.get('adj_fcf'))
        put('adj_fcf_items', p, ssum(fc.get('items')))
    return P, S


def cf_discrete(S):
    Y = S['_cfytd']
    keys = ['net_income', 'da', 'sbc', 'deferred_taxes', 'noncash_restructuring_impairment_gains', 'disc_ops_cash', 'cfo',
            'capex', 'acquisitions', 'proceeds_asset_sales', 'cfi', 'debt_proceeds', 'debt_repayments', 'revolver_net',
            'dividends_paid', 'buybacks', 'equity_issuance', 'net_transfers_to_parent', 'cff', 'fx_effect', 'net_change_cash']

    def flat(C):
        o = {k: float(C.get(k) or 0.0) for k in keys}
        o['wc'] = ssum(C.get('wc_changes'))
        o['cash_begin'] = C.get('cash_begin'); o['cash_end'] = C.get('cash_end')
        return o
    D = {l: flat(C) for l, C in Y.items()}
    out = defaultdict(dict)
    for l, v in D.items():
        if isinstance(l, int):
            for k, x in v.items():
                out[k][l] = x
            continue
        q, yy = l.split('/'); qn = int(q[1])
        prev = D.get(f'Q{qn-1}/{yy}') if qn > 1 else None
        for k, x in v.items():
            if qn == 1:
                out[k][l] = x
            elif prev is None:
                continue
            elif k == 'cash_begin':
                out[k][l] = prev['cash_end']
            elif k == 'cash_end':
                out[k][l] = x
            else:
                out[k][l] = x - prev[k]
    for l, v in D.items():
        if isinstance(l, int):
            n = D.get(f'Q3/{str(l)[2:]}')
            if n is None:
                continue
            q4 = f'Q4/{str(l)[2:]}'
            for k, x in v.items():
                if k == 'cash_begin':
                    out[k][q4] = n['cash_end']
                elif k == 'cash_end':
                    out[k][q4] = x
                else:
                    out[k][q4] = x - n[k]
    return {k: {l: (None if x is None else float(x)) for l, x in d.items()} for k, d in out.items()}


def colfax():
    if not os.path.exists(CFX):
        return {}
    return json.load(open(CFX))
