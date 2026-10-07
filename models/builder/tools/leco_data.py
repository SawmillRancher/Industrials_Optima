"""Load LECO extraction JSONs into model series: S[key][col_label] (USD m unless noted)."""
import json, os, re
from collections import defaultdict

BASE = os.path.join(os.path.dirname(__file__), '..', 'leco', 'extract')
SPLIT_YEARS = set(range(2006, 2011))   # 2-for-1 split May-2011: per-share /2, shares x2 for FY2006–FY2010


def lab(p):
    """'Q1-2013' -> 'Q1/13'; 'FY2013' -> 2013"""
    if p.startswith('FY'):
        return int(p[2:])
    q, y = p.split('-')
    return f'{q}/{y[2:]}'


def num(x):
    return None if x is None else float(x)


def m(x):
    return None if x is None else float(x) / 1000.0


def ssum(lst):
    if not lst:
        return 0.0
    return sum(float(v) for _, v in lst if v is not None)


CATS = [
    ('ven', r'venezuel|deconsolidat|remeasurement|devaluation|highly inflationary|argentin'),
    ('inv', r'step.?up|inventor(y|ies).*(fair value|step)|acquired inventor'),
    ('txn', r'transaction|acquisition.related|acquisition.*integration|integration cost|acquisition cost|deal cost'),
    ('pen', r'pension|retirement plan|annuit'),
    ('rat', r'rationali|impairment|restructur|russia|severance|exit|asset write'),
    ('gain', r'gain|bargain|disposal|sale of (land|property|ireland|real estate|facility)'),
]


def cat(label):
    s = label.lower()
    for k, rx in CATS:
        if re.search(rx, s):
            return k
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
    notes = defaultdict(list)

    def put(key, p, v):
        if v is not None:
            S[key][lab(p)] = v

    for p, d in P.items():
        year = int(p[-4:])
        split = 2.0 if year in SPLIT_YEARS else 1.0
        I = d.get('is') or {}
        # ---------------- income statement ----------------
        if I:
            put('is_sales', p, m(I.get('net_sales')))
            put('is_cogs', p, m(I.get('cogs')))
            put('is_sga', p, m(I.get('sga')))
            put('is_rat', p, m(I.get('rationalization')) or 0.0)
            oo = ssum(I.get('other_operating'))
            put('is_othop', p, oo / 1000.0)
            put('is_oi_rep', p, m(I.get('operating_income')))
            ii = num(I.get('interest_income')); ie = num(I.get('interest_expense'))
            if I.get('interest_expense_is_net'):
                put('is_int_net', p, m(ie) - (m(ii) or 0.0) if ii else m(ie))
                put('is_int_inc', p, m(ii))
            else:
                put('is_int_inc', p, m(ii))
                put('is_int_gross', p, m(ie))
                put('is_int_net', p, (m(ie) or 0.0) - (m(ii) or 0.0))
            put('is_eq', p, m(I.get('equity_earnings')) or 0.0)
            put('is_oth', p, m(I.get('other_income')) or 0.0)
            put('is_pretax_rep', p, m(I.get('pretax_income')))
            put('is_tax', p, m(I.get('income_taxes')))
            put('is_nci', p, m(I.get('nci_income')) or 0.0)
            put('is_ni_rep', p, m(I.get('net_income')))
            put('eps_b_rep', p, None if I.get('eps_basic') is None else I['eps_basic'] / split)
            put('eps_d_rep', p, None if I.get('eps_diluted') is None else I['eps_diluted'] / split)
            put('sh_b', p, None if I.get('shares_basic') is None else I['shares_basic'] / 1000.0 * split)
            put('sh_d', p, None if I.get('shares_diluted') is None else I['shares_diluted'] / 1000.0 * split)
            put('dps', p, None if I.get('dps_declared') is None else I['dps_declared'] / split)
        # ---------------- balance sheet ----------------
        B = d.get('bs')
        if B:
            put('bs_cash', p, m(B.get('cash')))
            put('bs_ar', p, m(B.get('ar')))
            put('bs_inv', p, m(B.get('inventories')))
            put('bs_tca', p, m(B.get('total_current_assets')))
            put('bs_ppe', p, m(B.get('ppe_net')))
            put('bs_gw', p, m(B.get('goodwill')))
            put('bs_ta_rep', p, m(B.get('total_assets')))
            put('bs_std', p, (m(B.get('short_term_debt')) or 0.0) + (m(B.get('current_ltd')) or 0.0))
            put('bs_ap', p, m(B.get('trade_ap')))
            put('bs_accr', p, m(B.get('accrued_employee_comp')))
            put('bs_tcl', p, m(B.get('total_current_liabilities')))
            put('bs_ltd', p, m(B.get('long_term_debt')) or 0.0)
            tle = m(B.get('total_liabilities_and_equity'))
            te = m(B.get('total_equity'))
            le = m(B.get('total_leco_equity'))
            nci = m(B.get('nci_equity')) or 0.0
            if te is None and le is not None:
                te = le + nci
            if le is None and te is not None:
                le = te - nci
            tl = m(B.get('total_liabilities'))
            if tl is None and tle is not None and te is not None:
                tl = tle - te
            put('bs_tl', p, tl)
            cs = (m(B.get('common_shares')) or 0.0) + (m(B.get('apic')) or 0.0)
            put('bs_cs', p, cs)
            put('bs_re', p, m(B.get('retained_earnings')))
            put('bs_aoci', p, m(B.get('aoci')))
            put('bs_treas', p, m(B.get('treasury_shares')) or 0.0)
            put('bs_le', p, le)
            put('bs_nci', p, nci)
            put('bs_tle_rep', p, tle)
            so = B.get('shares_outstanding_period_end')
            if so is not None:
                put('sh_out', p, so / 1000.0 * split)
        # ---------------- cash flow (YTD) ----------------
        C = d.get('cf_ytd')
        if C:
            S['_cfytd'][lab(p)] = C
        # ---------------- release ----------------
        R = d.get('release') or {}
        seg = R.get('segments_current_basis')
        if seg:
            for sk in ('AW', 'IW', 'HPG', 'CORP', 'CONS'):
                x = seg.get(sk) or {}
                for f in ('net_sales', 'inter_segment', 'total_sales', 'ebit', 'special_items', 'adj_ebit'):
                    if x.get(f) is not None:
                        put(f'seg_{sk}_{f}', p, m(x[f]))
        leg = R.get('segments_legacy_basis')
        if leg and leg.get('segments'):
            for name, x in leg['segments'].items():
                for f in ('net_sales', 'total_sales', 'ebit', 'special_items', 'adj_ebit'):
                    if x.get(f) is not None:
                        S[f'legacy::{name}::{f}'][lab(p)] = m(x[f])
        sc = R.get('sales_change') or {}
        rows = sc.get('rows') or {}
        basis = sc.get('basis')
        alias = {'Americas Welding': 'AW', 'International Welding': 'IW', 'The Harris Products Group': 'HPG',
                 'Harris Products Group': 'HPG', 'Consolidated': 'CONS'}
        for name, x in rows.items():
            sk = alias.get(name)
            if sk is None:
                continue
            if sk != 'CONS' and basis != 'current':
                continue
            for f in ('prior', 'volume', 'price', 'acquisitions', 'divestitures', 'fx', 'current'):
                if x.get(f) is not None:
                    put(f'sc_{sk}_{f}', p, m(x[f]))
            for f in ('volume_pct', 'price_pct', 'acquisitions_pct', 'divestitures_pct', 'fx_pct', 'total_pct'):
                if x.get(f) is not None:
                    put(f'sc_{sk}_{f}', p, x[f] / 100.0)
        # non-GAAP
        ao = R.get('adj_operating_income') or {}
        if ao.get('adjusted_operating_income') is not None:
            put('pub_adj_oi', p, m(ao['adjusted_operating_income']))
        for lbl, v in ao.get('items') or []:
            if v is None:
                continue
            k = f'oi_{cat(lbl)}'
            S[k][lab(p)] = S[k].get(lab(p), 0.0) + v / 1000.0
            notes[k].append((lab(p), lbl))
        an = R.get('adj_net_income') or {}
        pre = an.get('pretax_items') or []
        for lbl, v in pre:
            if v is None:
                continue
            k = f'sp_{cat(lbl)}'
            S[k][lab(p)] = S[k].get(lab(p), 0.0) + v / 1000.0
            notes[k].append((lab(p), lbl))
        if pre:
            S['_has_pretax'][lab(p)] = 1
        if an.get('tax_effect') is not None:
            put('sp_taxeff', p, m(an['tax_effect']))
        to = ssum(an.get('tax_only_items'))
        put('sp_taxonly', p, to / 1000.0 if an else None)
        oth = an.get('other_items') or []
        S['_other_items'][lab(p)] = oth
        if an.get('adjusted_net_income') is not None:
            put('pub_adj_ni', p, m(an['adjusted_net_income']))
        if R.get('adjusted_eps_diluted') is not None:
            put('pub_adj_eps', p, R['adjusted_eps_diluted'] / split)
        if R.get('special_items_per_share') is not None:
            put('pub_sp_ps', p, R['special_items_per_share'] / split)
        ae = (R.get('adj_ebit_recon') or {}).get('adjusted_ebit')
        cons = (seg or {}).get('CONS') if seg else None
        lcons = None
        if leg and leg.get('segments'):
            for name, x in leg['segments'].items():
                if name.lower().startswith('consolidated') or name.lower() == 'total':
                    lcons = x
        if ae is None and cons and cons.get('adj_ebit') is not None:
            ae = cons['adj_ebit']
        if ae is None and lcons and lcons.get('adj_ebit') is not None:
            ae = lcons['adj_ebit']
        put('pub_adj_ebit', p, m(ae))
        eb = None
        if cons and cons.get('ebit') is not None:
            eb = cons['ebit']
        elif lcons and lcons.get('ebit') is not None:
            eb = lcons['ebit']
        put('pub_ebit', p, m(eb))
        if cons and cons.get('special_items') is not None:
            put('seg_sp_total', p, m(cons['special_items']))
        elif lcons and lcons.get('special_items') is not None:
            put('seg_sp_total', p, m(lcons['special_items']))
        put('pub_fcf', p, m(R.get('free_cash_flow')))
        put('pub_cashconv', p, None if R.get('cash_conversion_pct') is None else R['cash_conversion_pct'] / 100.0)
        put('pub_roic', p, None if R.get('roic_reported_pct') is None else R['roic_reported_pct'] / 100.0)
        put('pub_adj_roic', p, None if R.get('adjusted_roic_pct') is None else R['adjusted_roic_pct'] / 100.0)
        put('pub_adj_etr', p, None if R.get('adjusted_effective_tax_rate') is None else R['adjusted_effective_tax_rate'] / 100.0)
    return P, S, notes


def cf_discrete(S):
    """Turn YTD cash-flow dicts into discrete-period series."""
    Y = S['_cfytd']
    keys = ['net_income_incl_nci', 'da', 'sbc', 'deferred_taxes', 'cfo', 'capex', 'acquisitions', 'cfi',
            'st_borrowings_net', 'lt_borrowings', 'lt_repayments', 'options_proceeds', 'buybacks', 'dividends_paid',
            'cff', 'fx_effect', 'net_change_cash']

    def flat(C):
        out = {k: (C.get(k) or 0.0) for k in keys}
        out['ratg'] = (C.get('rationalization_impairment_noncash') or 0.0) + (C.get('gains_losses_on_disposals') or 0.0)
        out['wc'] = ssum(C.get('wc_changes'))
        out['proceeds'] = (C.get('proceeds_asset_sales') or 0.0) + (C.get('proceeds_business_sales') or 0.0)
        out['cash_begin'] = C.get('cash_begin'); out['cash_end'] = C.get('cash_end')
        return out
    D = {}
    for lbl, C in Y.items():
        D[lbl] = flat(C)
    out = defaultdict(dict)
    for lbl, v in D.items():
        if isinstance(lbl, int):
            for k, x in v.items():
                out[k][lbl] = x
            continue
        q, yy = lbl.split('/')
        qn = int(q[1])
        if qn == 1:
            for k, x in v.items():
                out[k][lbl] = x
            continue
        prev = D.get(f'Q{qn-1}/{yy}')
        if prev is None:
            continue
        for k, x in v.items():
            if k == 'cash_begin':
                out[k][lbl] = prev['cash_end']
            elif k == 'cash_end':
                out[k][lbl] = x
            else:
                out[k][lbl] = x - prev[k]
    # Q4 = FY - 9M
    for lbl, v in D.items():
        if isinstance(lbl, int):
            n = D.get(f'Q3/{str(lbl)[2:]}')
            if n is None:
                continue
            q4 = f'Q4/{str(lbl)[2:]}'
            for k, x in v.items():
                if k == 'cash_begin':
                    out[k][q4] = n['cash_end']
                elif k == 'cash_end':
                    out[k][q4] = x
                else:
                    out[k][q4] = x - n[k]
    return {k: {l: (None if x is None else x / 1000.0) for l, x in d.items()} for k, d in out.items()}
