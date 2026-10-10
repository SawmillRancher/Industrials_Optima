"""Derived historical series for the LECO model (bridges, derived BS/CF lines)."""
import re

CATS = ['rat', 'txn', 'inv', 'pen', 'ven', 'gain', 'oth']


def prep(S, lay_labels):
    def g(k, l):
        return S.get(k, {}).get(l)

    labels = set()
    for k in ('is_sales', 'bs_ta_rep', 'cf_cfo'):
        labels |= set(S.get(k, {}).keys())

    # --- published adjusted OI: 2006-2008 not tabulated by the company (derived from release text) -> n/p
    for y in (2006, 2007, 2008):
        S['pub_adj_oi'].pop(y, None)

    # --- EBIT-level special items (pre-tax)
    for l in labels:
        has_pre = l in S.get('_has_pretax', {})
        src = 'sp_' if has_pre else 'oi_'
        vals = {c: (g(src + c, l) or 0.0) for c in CATS}
        tot = sum(vals.values())
        target = g('seg_sp_total', l)
        if target is not None and abs(target - tot) > 0.05:
            vals['oth'] += target - tot
        if not any(abs(v) > 1e-9 for v in vals.values()) and target is None and g('pub_adj_ni', l) is None:
            continue
        for c in CATS:
            S.setdefault('eb_' + c, {})[l] = vals[c]
        # OI-level items default to 0 where any recon exists
        if g('pub_adj_oi', l) is not None or has_pre or target is not None:
            for c in CATS:
                S.setdefault('oi_' + c, {}).setdefault(l, 0.0)

    # --- adjusted net income bridge
    for l in labels:
        ni = g('is_ni_rep', l)
        pub = g('pub_adj_ni', l)
        if ni is None or pub is None:
            continue
        sp_tot = sum((g('eb_' + c, l) or 0.0) for c in CATS)
        taxonly = g('sp_taxonly', l) or 0.0
        oth = S.get('_other_items', {}).get(l) or []
        nci = sum(v / 1000.0 for lbl, v in oth if v is not None and re.search(r'non.?controlling|minority', lbl.lower()))
        S.setdefault('eps_nci', {})[l] = nci
        if l in S.get('_has_pretax', {}) and g('sp_taxeff', l) is not None:
            S.setdefault('eps_taxeff', {})[l] = g('sp_taxeff', l)
        else:
            # after-tax-only disclosure: tax effect = published adjusted NI − NI − pre-tax items − tax-only − NCI share
            S.setdefault('eps_taxeff', {})[l] = pub - ni - sp_tot - taxonly - nci
            S.setdefault('_taxeff_derived', {})[l] = 1
        S.setdefault('eps_taxonly', {})[l] = taxonly

    # --- dividends: Q4 = FY − Q1..Q3 where Q4 missing
    for y in range(2013, 2026):
        q4 = f'Q4/{str(y)[2:]}'
        if g('dps', q4) is None and g('dps', y) is not None:
            qs = [g('dps', f'Q{q}/{str(y)[2:]}') for q in (1, 2, 3)]
            if None not in qs:
                S['dps'][q4] = round(g('dps', y) - sum(qs), 4)
        if g('sh_out', q4) is None and g('sh_out', y) is not None:
            S['sh_out'][q4] = g('sh_out', y)
        # Q4 balance sheet = FY balance sheet
        for k in list(S.keys()):
            if k.startswith('bs_') and g(k, y) is not None and g(k, q4) is None:
                S[k][q4] = g(k, y)

    # --- balance-sheet derived lines
    for l in set(S.get('bs_ta_rep', {}).keys()):
        tca, cash, ar, inv = g('bs_tca', l), g('bs_cash', l), g('bs_ar', l), g('bs_inv', l)
        if None not in (tca, cash, ar, inv):
            S.setdefault('bs_oca', {})[l] = tca - cash - ar - inv
        ta, ppe, gw = g('bs_ta_rep', l), g('bs_ppe', l), g('bs_gw', l)
        if None not in (ta, tca, ppe):
            S.setdefault('bs_onca', {})[l] = ta - tca - ppe - (gw or 0.0)
        tcl, std, ap, accr = g('bs_tcl', l), g('bs_std', l), g('bs_ap', l), g('bs_accr', l)
        if None not in (tcl, ap):
            S.setdefault('bs_ocl', {})[l] = tcl - (std or 0.0) - ap - (accr or 0.0)
        tl, ltd = g('bs_tl', l), g('bs_ltd', l)
        if None not in (tl, tcl):
            S.setdefault('bs_oncl', {})[l] = tl - tcl - (ltd or 0.0)
        le = g('bs_le', l)
        parts = [g(k, l) for k in ('bs_cs', 'bs_re', 'bs_aoci', 'bs_treas')]
        if le is not None and None not in parts:
            diff = le - sum(parts)
            if abs(diff) > 0.05:
                S['bs_cs'][l] = parts[0] + diff
                S.setdefault('_eq_adj', {})[l] = diff

    # --- cash-flow derived lines
    for l in set(S.get('cf_cfo', {}).keys()):
        f = lambda k: g('cf_' + k, l) or 0.0
        S.setdefault('cf_oth', {})[l] = f('cfo') - (f('net_income_incl_nci') + f('da') + f('sbc') + f('deferred_taxes') + f('ratg') + f('wc'))
        S.setdefault('cf_oinv', {})[l] = f('cfi') - (f('capex') + f('acquisitions') + f('proceeds'))
        S.setdefault('cf_ofin', {})[l] = f('cff') - (f('st_borrowings_net') + f('lt_borrowings') + f('lt_repayments') + f('dividends_paid') + f('buybacks') + f('options_proceeds'))
    return S
