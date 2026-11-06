"""Self-checks on the normalised James Hardie data (normalize.run()):
  1. income-statement arithmetic (GP, EBIT, EBT, NI) per period
  2. segment net sales and segment EBIT sum to the group lines
  3. non-GAAP bridges: EBIT + items = Adjusted EBIT; NI + items = Adjusted NI (where the package prints the bridge)
  4. sum of quarters = fiscal year (FY2013 onward) for the main lines
  5. cash flow: begin + net change = end; end cash ties to the balance sheet
  6. balance sheet: assets = liabilities + equity; current/non-current sub-totals
  7. XBRL cross-check (company facts, as first filed) for the fiscal years with XBRL (FY2011 onward)
Prints every failure; exits 1 when any check outside the documented exceptions fails.
Usage: JHX_SRC=... python3 check_data.py [-v]"""
import sys, os, re
import normalize, xbrl

TOL = 0.16          # rounding of two one-decimal figures
VERBOSE = '-v' in sys.argv
FAILS, PASSES, SKIPS = [], 0, 0
# documented exceptions (period, check) -> reason; reported but not counted as failures
EXCEPT = {
    ('2013', 'SUMQ apac_ebit'): 'Q4 FY13 package restates FY13 Asia Pacific EBIT excluding New Zealand product liability expenses; Q1-Q3 FY13 as originally reported',
    ('2013', 'SUMQ tot_adj_ebit'): 'same reclassification (New Zealand product liability expenses, Q4 FY13 package) - Q1-Q3 as originally reported',
    ('2013', 'SUMQ tot_adj_ni'): 'same reclassification (New Zealand product liability expenses, Q4 FY13 package) - Q1-Q3 as originally reported',
    ('2013', 'SUMQ tot_adj_ebitda'): 'rounding of the restated FY13 D&A in the Q4 FY13 package (0.6)',
    ('2014', 'SUMQ apac_ebit'): 'rounding across the four as-reported quarters (0.3)',
    ('2018', 'SUMQ corp_ebit'): 'Q4 FY18 package excludes Fermacell acquisition costs (US$10.0m FY18, 4.7 in Q1-Q3) from General Corporate; Q1-Q3 as originally reported include them',
    ('2018', 'SUMQ tot_adj_ebit'): 'Q4 FY18 package excludes Fermacell acquisition costs (4.7 in Q1-Q3) from Adjusted EBIT; Q1-Q3 as originally reported',
    ('2018', 'SUMQ tot_adj_ni'): 'Q4 FY18 package excludes Fermacell acquisition costs (4.7 in Q1-Q3) from Adjusted net income; Q1-Q3 as originally reported',
    ('Q1-27', 'NG ni_cats'): 'Q1 FY27 bridge items derived as six months (Q2 FY27 release) less Q2; 0.9 of rounding across the eight derived items',
    ('Q1-27', 'NG adj_ni'): 'Q1 FY27 bridge items derived as six months (Q2 FY27 release) less Q2; 0.9 of rounding across the eight derived items',
    ('Q2-27', 'CF end=BS cash'): 'US$2.0m of cash sits in assets held for sale (Europe, discontinued operations) at 30-Sep-2026; the cash-flow statement includes it',
    ('2013', 'XBRL tax'): 'FY13 income tax was a benefit of 11.8 (EBT 33.7, NI 45.5); the 20-F XBRL fact is tagged with the opposite sign',
}

def fail(p, chk, msg): FAILS.append((p, chk, msg))
def ok():
    global PASSES; PASSES += 1
def check(p, chk, lhs, rhs, tol=TOL, note=''):
    global SKIPS
    if lhs is None or rhs is None: SKIPS += 1; return
    if abs(lhs - rhs) <= tol: ok()
    else: fail(p, chk, f'{lhs:.1f} vs {rhs:.1f} (diff {lhs - rhs:+.1f}) {note}')

def N(v): return v or 0.0

def run():
    D = normalize.run()
    x = lambda p, k: D.get(p, {}).get('x', {}).get(k)
    pers = [p for p in normalize.periods() if p in D]
    # 1. income statement
    for p in pers:
        if x(p, 'rev') is None: continue
        check(p, 'IS gp', x(p, 'rev') - N(x(p, 'cogs')), x(p, 'gp'))
        if x(p, 'op') is not None and x(p, 'sga') is not None:
            opc = x(p, 'gp') - x(p, 'sga') - N(x(p, 'rd')) - N(x(p, 'restr')) - N(x(p, 'acq_exp')) - N(x(p, 'impair')) - N(x(p, 'sci')) - N(x(p, 'other_op')) - N(x(p, 'asb_adj'))
            check(p, 'IS ebit', opc, x(p, 'op'))
        if x(p, 'ebt') is not None and x(p, 'op') is not None:
            check(p, 'IS ebt', x(p, 'op') - N(x(p, 'int_net')) - N(x(p, 'onop')) - N(x(p, 'debt_ext')), x(p, 'ebt'))
        if x(p, 'ebt') is not None and x(p, 'tax') is not None and x(p, 'ni_cont') is not None:
            check(p, 'IS ni', x(p, 'ebt') - x(p, 'tax'), x(p, 'ni_cont'))
        if x(p, 'ni') is not None and x(p, 'ni_cont') is not None:
            check(p, 'IS ni_total', x(p, 'ni_cont') + N(x(p, 'disc')) + N(x(p, 'cum_eff')), x(p, 'ni'))
        if x(p, 'eps_d') is not None and x(p, 'sh_d') and x(p, 'ni') is not None and not x(p, 'eps_derived'):
            check(p, 'IS eps', x(p, 'ni') / x(p, 'sh_d'), x(p, 'eps_d'), tol=0.011)
    # 2. segments
    for p in pers:
        fy, q = normalize.fyq(p)
        segs = [s for s in ('na', 'dra', 'apac', 'eu', 'int', 'oth') if x(p, f'{s}_rev') is not None]
        if 'int' in segs: segs = [s for s in segs if s not in ('apac', 'eu')]      # FY17-18: International = Asia Pacific + Europe
        if x(p, 'recast_cont'): segs = [s for s in segs if s != 'eu']              # Q1 FY27 recast to continuing operations (Europe discontinued)
        if segs and x(p, 'rev') is not None and (fy >= 2009 or len(segs) >= 2):
            check(p, 'SEG rev', sum(x(p, f'{s}_rev') for s in segs), x(p, 'rev'), note=f'segs={segs}')
        esegs = [s for s in ('na', 'dra', 'apac', 'eu', 'int', 'oth', 'rd', 'corp') if x(p, f'{s}_ebit') is not None]
        if 'int' in esegs: esegs = [s for s in esegs if s not in ('apac', 'eu')]
        if esegs and x(p, 'op') is not None and 'corp' in esegs:
            tot = sum(x(p, f'{s}_ebit') for s in esegs)
            # the segment EBIT tables show General Corporate before the asbestos adjustments and, by era, before AICF SG&A,
            # ASIC / NZ weathertightness items, impairments, SCI and acquisition costs; from FY2026 the FS reconciliation
            # 'General Corporate' includes them. Accept when EBIT - sum(segments) is explained by a subset of those lines.
            resid = x(p, 'op') - tot
            lines = [('asb', -N(x(p, 'asb_adj'))), ('aicf', -N(x(p, 'aicf_sga'))),
                     ('impair', -N(x(p, 'impair'))), ('sci', -N(x(p, 'sci'))), ('acq', -N(x(p, 'acq_exp'))), ('restr', -N(x(p, 'restr'))), ('oth', -N(x(p, 'other_op')))]
            # plus the bridge items the package lists between EBIT and Adjusted EBIT (AICF SG&A, ASIC, NZ weathertightness, stamp duty ...)
            for it in (x(p, 'ebit_items_def') or x(p, 'ebit_items') or []):
                if it[1] and not re.search(r'^Asbestos', it[0]): lines.append(('item:' + it[0][:20], -abs(it[1]))); lines.append(('item+:' + it[0][:20], abs(it[1])))
            items = [(k, v) for k, v in lines if abs(v) > 0.05][:12]
            best = None
            for m in range(1 << len(items)):
                ssum = sum(v for i, (k, v) in enumerate(items) if m >> i & 1)
                if best is None or abs(resid - ssum) < abs(resid - best[0]): best = (ssum, [k for i, (k, v) in enumerate(items) if m >> i & 1])
            if best is None: best = (0.0, [])
            # several one-decimal lines are added here (segments, R&D, corporate, asbestos, AICF ...): 1.2 covers their rounding
            check(p, 'SEG ebit', tot + best[0], x(p, 'op'), tol=1.2, note=f'segs={esegs} resid={resid:+.1f} via {best[1]}')
    # 3. bridges
    for p in pers:
        items = x(p, 'ebit_items_def') or x(p, 'ebit_items')
        if items and x(p, 'op') is not None and x(p, 'tot_adj_ebit') is not None and not x(p, 'tot_adj_ebit_src'):
            s = sum(N(it[1]) for it in items)
            cand = [x(p, 'op') + s, x(p, 'op') - s]
            best = min(cand, key=lambda v: abs(v - x(p, 'tot_adj_ebit')))
            check(p, 'NG adj_ebit', best, x(p, 'tot_adj_ebit'), tol=0.3, note='items=' + ';'.join(it[0][:24] for it in items))
        items = x(p, 'ni_items')
        if items and x(p, 'ni') is not None and x(p, 'tot_adj_ni') is not None and not x(p, 'tot_adj_ni_src'):
            s = sum(N(it[1]) for it in items)
            # FY27 bridges start from net income from continuing operations
            cand = [x(p, 'ni') + s, x(p, 'ni') - s] + ([x(p, 'ni_cont') + s] if x(p, 'ni_cont') is not None else [])
            best = min(cand, key=lambda v: abs(v - x(p, 'tot_adj_ni')))
            check(p, 'NG adj_ni', best, x(p, 'tot_adj_ni'), tol=0.3, note='items=' + ';'.join(it[0][:24] for it in items))
        # FY09-FY20 'Adjusted EBITDA' = EBIT + D&A (asbestos included); 'Adjusted EBITDA excluding Asbestos' is the ex-asbestos line
        if x(p, 'tot_adj_ebitda') is not None and x(p, 'op') is not None and x(p, 'tot_dna') is not None and normalize.fyq(p)[0] <= 2020:
            check(p, 'NG ebitda', x(p, 'op') + x(p, 'tot_dna'), x(p, 'tot_adj_ebitda'), tol=0.3)
        if x(p, 'tot_adj_ebitda_ex_asb') is not None and x(p, 'tot_adj_ebitda') is not None and normalize.fyq(p)[0] <= 2020:
            check(p, 'NG ebitda_ex_asb', x(p, 'tot_adj_ebitda') + N(x(p, 'asb_adj')) + N(x(p, 'aicf_sga')), x(p, 'tot_adj_ebitda_ex_asb'), tol=0.3)
    # 3b. bridge categories: NI + pre-tax categories + tax category = published adjusted NI (FY09+; FY06-08 items are after tax)
    for p in pers:
        if x(p, 'tot_adj_ni') is None or x(p, 'ni_it_labels') is None or normalize.fyq(p)[0] <= 2008: continue
        s = sum(v for k, v in D[p]['x'].items() if k.startswith('ni_it_') and not k.endswith('_labels'))
        base = x(p, 'ni_cont') if x(p, 'ni_cont') is not None else x(p, 'ni')
        cand = [base + s] + ([x(p, 'ni') + s] if x(p, 'ni') is not None else [])
        check(p, 'NG ni_cats', min(cand, key=lambda v: abs(v - x(p, 'tot_adj_ni'))), x(p, 'tot_adj_ni'), tol=0.3)
    # 4. quarters -> year
    for y in range(2013, 2027):
        fy = str(y)
        for k in ('rev', 'gp', 'op', 'ebt', 'tax', 'ni', 'asb_adj', 'na_rev', 'apac_rev', 'eu_rev', 'dra_rev', 'na_ebit', 'apac_ebit', 'eu_ebit', 'dra_ebit', 'corp_ebit', 'rd_ebit',
                  'tot_adj_ebit', 'tot_adj_ni', 'tot_adj_ebitda', 'cf_cfo', 'cf_capex', 'cf_dna', 'cf_bb', 'cf_div', 'cf_aicf', 'na_vol', 'apac_vol'):
            qs = [x(normalize.qk(y, q), k) for q in (1, 2, 3, 4)]
            if x(fy, k) is None or any(v is None for v in qs): continue
            if x(normalize.qk(y, 4), 'q4_derived') and k not in ('cf_cfo', 'cf_capex', 'cf_dna', 'cf_bb', 'cf_div', 'cf_aicf'): continue   # Q4 = FY - 9M by construction
            check(fy, f'SUMQ {k}', sum(qs), x(fy, k), tol=0.3)
    # 5. cash flow
    for p in pers:
        if x(p, 'cf_cfo') is None: continue
        if x(p, 'cf_beg') is not None and x(p, 'cf_end') is not None:
            check(p, 'CF beg+net=end', x(p, 'cf_beg') + x(p, 'cf_net'), x(p, 'cf_end'))
        if x(p, 'cf_end') is not None and x(p, 'bs_cash') is not None:
            basis = x(p, 'cf_basis') or ''
            bs = x(p, 'bs_cash') + (N(x(p, 'bs_restr')) + N(x(p, 'bs_restr_asb')) if 'restricted' in basis else 0.0)
            check(p, 'CF end=BS cash', x(p, 'cf_end'), bs, note=f'basis={basis!r}')
    # 6. balance sheet
    for p in pers:
        if x(p, 'bs_ta') is None: continue
        if x(p, 'bs_eq') is None or x(p, 'bs_tl') is None: fail(p, 'BS a=l+e', f"missing equity/liabilities (eq={x(p, 'bs_eq')}, tl={x(p, 'bs_tl')})")
        else: check(p, 'BS a=l+e', x(p, 'bs_tl') + x(p, 'bs_eq'), x(p, 'bs_ta'))
        check(p, 'BS tle', x(p, 'bs_tle'), x(p, 'bs_ta'))
        if x(p, 'bs_tca') is not None:
            check(p, 'BS tca', N(x(p, 'bs_cash')) + N(x(p, 'bs_restr')) + N(x(p, 'bs_restr_asb')) + N(x(p, 'bs_inv_asb')) + N(x(p, 'bs_ar')) + N(x(p, 'bs_inv')) + N(x(p, 'bs_oca')) + N(x(p, 'bs_hfs')), x(p, 'bs_tca'), tol=max(TOL, abs(N(x(p, 'bs_inv_asb'))) + 0.2))
        for k in ('bs_oca', 'bs_onca', 'bs_ocl', 'bs_onl'):
            if x(p, k) is not None and x(p, k) < -0.05: fail(p, 'BS plug<0', f'{k} = {x(p, k):.1f}')
    # 7. XBRL
    for y in range(2011, 2027):
        fy = str(y)
        for k, cs, kind in (('rev', ['Revenues', 'SalesRevenueNet', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueGoodsNet'], 'FY'),
                            ('op', ['OperatingIncomeLoss'], 'FY'), ('ni', ['NetIncomeLoss', 'ProfitLoss'], 'FY'), ('eps_d', ['EarningsPerShareDiluted'], 'FY'),
                            ('cf_cfo', ['NetCashProvidedByUsedInOperatingActivities'], 'FY'), ('bs_ta', ['Assets'], 'I'), ('cf_capex', ['PaymentsToAcquirePropertyPlantAndEquipment'], 'FY'),
                            ('bs_eq', ['StockholdersEquity'], 'I'), ('tax', ['IncomeTaxExpenseBenefit'], 'FY'), ('sh_d', ['WeightedAverageNumberOfDilutedSharesOutstanding'], 'FY')):
            v = xbrl.first_of(cs, y, kind, 4 if kind == 'I' else None)
            if v is None or x(fy, k) is None: continue
            if k == 'sh_d' and v > 1e5: v = v / 1e6
            if k == 'cf_capex': v = -abs(v)
            check(fy, f'XBRL {k}', x(fy, k), v, tol=(0.011 if k == 'eps_d' else 0.16 if k != 'sh_d' else 0.06))
    for y in (2026, 2027):
        for q in (1, 2, 3):
            p = normalize.qk(y, q)
            if x(p, 'rev') is None: continue
            for k, cs in (('rev', ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax']), ('op', ['OperatingIncomeLoss']), ('ni', ['NetIncomeLoss', 'ProfitLoss'])):
                v = xbrl.first_of(cs, y, 'Q', q)
                if v is None: continue
                # FY26 quarters were 6-K periods: the first XBRL for them is the FY27 10-Q comparative (continuing operations, ex Europe)
                kk = k + '_rc' if y == 2026 and x(p, k + '_rc') is not None else k
                if kk == 'ni_rc' and x(p, 'ni_total_rc') is not None: kk = 'ni_total_rc'
                if x(p, 'recast_cont') and x(p, k + '_orig') is not None: kk = k + '_orig'     # XBRL = as originally reported (10-Q); model = recast
                check(p, f'XBRL {kk}', x(p, kk), v)
    # report
    print(f'checks: {PASSES} pass, {len(FAILS)} fail, {SKIPS} skipped (missing inputs)')
    hard = 0
    for p, chk, msg in FAILS:
        exc = EXCEPT.get((p, chk))
        tag = 'EXCEPTION' if exc else 'FAIL'
        if not exc: hard += 1
        print(f'{tag:9} {p:6} {chk:18} {msg}' + (f'  -- {exc}' if exc else ''))
    return hard

if __name__ == '__main__':
    sys.exit(1 if run() else 0)
