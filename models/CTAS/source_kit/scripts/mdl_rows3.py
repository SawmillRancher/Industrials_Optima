"""Row definitions part 3: cash flow, buybacks, balance sheet, working capital, schedules (UniFirst PPA, D&A split,
debt & leverage), ratio analysis and valuation. Forecast for these blocks is annual (FY2027E–FY2031E)."""
from mdl_core import Row, BYNAME, prior_year
import curated as C

def build_part3(S, H, X):
    def hv(*keys, neg=False):
        def f(p):
            h = H.get(p.name, {})
            for k in keys:
                v = h.get(k)
                if isinstance(v, (int, float)):
                    return -v if neg else v
            return None
        return f
    def has(p, k): return isinstance(H.get(p.name, {}).get(k), (int, float))
    def hsum(*keys, neg=False):
        def f(p):
            h = H.get(p.name, {})
            vals = [h.get(k) for k in keys if isinstance(h.get(k), (int, float))]
            if not any(isinstance(h.get(k), (int, float)) for k in keys): return None
            s = sum(vals)
            return -s if neg else s
        return f
    def hf(tpl, k):
        return lambda p: tpl if has(p, k) else None
    def ratio(n, d):
        return '=IF(AND(ISNUMBER({%s}),ISNUMBER({%s})),IFERROR({%s}/{%s},""),"")' % (n, d, n, d)
    def yoy(k):
        def f(p):
            if prior_year(p) is None: return None
            return '=IF(AND(ISNUMBER({%s}),ISNUMBER({%s@py})),IFERROR({%s}/{%s@py}-1,""),"")' % (k, k, k, k)
        return f
    SC = X['scn']
    add = S.add
    A = lambda tpl: dict(f27=tpl, fa=tpl)        # annual-only forecast

    # ---------------- cash flow
    add(Row(None, 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'sec', note='CASH FLOW — forecast logic (annual; FY2027E = full year incl. Q1/27 actual; historical quarters = discrete, derived from year-to-date statements)'))
    add(Row('cf_ni', 'Net income', 'line', 'n1', h=hf('={is_ni}', 'cf_cfo'), **A('={is_ni}')))
    add(Row(None, 'Adjustments:', 'head'))
    add(Row('cf_da', '  Depreciation & amortization', 'line', 'n1', h=hf('={is_da}', 'cf_cfo'), **A('={is_da}')))
    add(Row('cf_sbc', '  Stock-based compensation', 'line', 'n1', h=hv('cf_sbc'), **A('={is_sbc}')))
    add(Row('cf_dtax', '  Deferred income taxes', 'line', 'n1', h=hv('cf_deftax'), **A('=-({unf_amort}+{unf_ppe_dep@abs}*{unf_on}+{ma_amort})*{dtl_rate@abs}'),
            note='Forecast: unwind of the deferred tax liability on UniFirst PPA amortization/step-up depreciation and future-M&A intangibles (book > tax).'))
    add(Row('cf_onc', '  Other non-cash items, net (derived; gains on sales, impairments, Shred-it)', 'line', 'n1',
            h=hf('={cf_cfo}-SUM({cf_ni},{cf_da},{cf_sbc},{cf_dtax},{cf_wc})', 'cf_cfo'), **A('=0')))
    add(Row('cf_wc', '  Changes in operating assets & liabilities, net (incl. capitalized contract cost additions)', 'line', 'n1', h=hv('cf_wc'),
            **A('=-{wc_dnwc}-{sch_cc}'), note='Linked to the balance sheet: −ΔNWC (ex acquired working capital) − additions to capitalized contract costs (assumed = their amortization; cash-neutral within D&A).'))
    add(Row('cf_cfo', 'Net cash provided by operating activities', 'total', 'n1', h=hv('cf_cfo'), **A('=SUM({cf_ni},{cf_da},{cf_sbc},{cf_dtax},{cf_onc},{cf_wc})'), cagr=True))
    add(Row('cf_capex', 'Capital expenditures', 'line', 'n1', h=hv('cf_capex'), **A('=-{is_rev}*{capex_pct}')))
    add(Row('cf_acq', 'Acquisitions of businesses, net of cash acquired', 'line', 'n1', h=hv('cf_acq'),
            f27='=-({ppa_cash@$P:FY2027}-{ppa_cashacq@$P:FY2027})*{unf_on}', fa='=-{ma_spend}',
            note='FY2027E: UniFirst cash consideration $2,825.7m less cash acquired $73.5m (net of $84m seller costs paid at close; 424B3). FY28E+: M&A lever.'))
    add(Row('cf_div_pr', 'Proceeds from divestitures & sales of assets/investments', 'line', 'n1', h=hv('cf_divest'), **A('=0')))
    add(Row('cf_ioth', 'Purchases of investments & other investing, net (derived)', 'line', 'n1',
            h=hf('={cf_cfi}-SUM({cf_capex},{cf_acq},{cf_div_pr})', 'cf_cfi'), **A('=0')))
    add(Row('cf_cfi', 'Net cash used in investing activities', 'key', 'n1', h=hv('cf_cfi'), **A('=SUM({cf_capex},{cf_acq},{cf_div_pr},{cf_ioth})')))
    def borrow(p):
        h = H.get(p.name, {})
        if 'cf_cff' not in h: return None
        return h.get('cf_debt_iss', 0) + max(h.get('cf_cp', 0), 0)
    def repay(p):
        h = H.get(p.name, {})
        if 'cf_cff' not in h: return None
        return h.get('cf_debt_rep', 0) + min(h.get('cf_cp', 0), 0)
    add(Row('cf_borrow', 'Proceeds from issuance of debt (incl. commercial paper, net)', 'line', 'n1', h=borrow,
            **A('={debt_refi}+{debt_unf}+MAX(0,{debt_facnet})')))
    add(Row('cf_repay', 'Repayments of debt (incl. commercial paper, net)', 'line', 'n1', h=repay,
            **A('=MIN(0,{debt_facnet})+{debt_mat}'), note='Net issuance / (repayment) = change in total debt per the debt schedule.'))
    add(Row('cf_div', 'Dividends paid', 'line', 'n1', h=hv('cf_div'),
            f27='=-({dps}*{bb_beg}+{dps@P:FY2027Q4}*{bb_unf})', fa='=-{dps}*{bb_beg}',
            note='Dividends per share × beginning shares outstanding (avoids circularity with buybacks); FY27E + one quarter on the UniFirst consideration shares.'))
    add(Row('cf_bb', 'Repurchases of common stock', 'line', 'n1', h=hv('cf_buyback'), **A('=-{bb_cash}')))
    add(Row('cf_opt', 'Proceeds from exercise of stock-based compensation awards', 'line', 'n1', h=hv('cf_opt'), **A('=0')))
    add(Row('cf_foth', 'Other financing activities, net (derived; financing fees, shares withheld for taxes)', 'line', 'n1',
            h=hf('={cf_cff}-SUM({cf_borrow},{cf_repay},{cf_div},{cf_bb},{cf_opt})', 'cf_cff'), **A('=0')))
    add(Row('cf_cff', 'Net cash used in financing activities', 'key', 'n1', h=hv('cf_cff'), **A('=SUM({cf_borrow},{cf_repay},{cf_div},{cf_bb},{cf_opt},{cf_foth})')))
    add(Row('cf_fx', 'Effect of exchange rate changes on cash', 'line', 'n1', h=hv('cf_fx'), **A('=0')))
    add(Row('cf_chg', 'Net increase (decrease) in cash', 'line', 'n1', h=hf('=SUM({cf_cfo},{cf_cfi},{cf_cff},{cf_fx})', 'cf_cfo'), **A('=SUM({cf_cfo},{cf_cfi},{cf_cff},{cf_fx})')))
    add(Row('cf_beg', 'Cash — beginning of period', 'line', 'n1', h=hv('cf_cash_beg'), f27='={bs_cash@P:FY2026}', fa='={cf_end@pa}'))
    add(Row('cf_end', 'Cash — end of period', 'key', 'n1', h=hv('cf_cash_end'), **A('={cf_beg}+{cf_chg}')))
    add(Row('chk_cf', '  Check: beginning cash + change = ending cash (should be 0)', 'check', 'n1', h=hf('=ROUND({cf_beg}+{cf_chg}-{cf_end},1)', 'cf_cfo'), **A('=ROUND({cf_beg}+{cf_chg}-{cf_end},1)')))
    add(Row('chk_cfbs', '  Check: balance-sheet cash vs cash-flow ending cash (should be 0)', 'check', 'n1',
            h=lambda p: '=ROUND({bs_cash}-{cf_end},1)' if (has(p, 'cf_cash_end') and has(p, 'bs_cash')) else None, **A('=ROUND({bs_cash}-{cf_end},1)')))
    add(Row(None, '(Memo)', 'head'))
    add(Row('fcf', 'Free cash flow (operating cash flow − capital expenditures; company definition)', 'total', 'n1',
            h=hf('={cf_cfo}+{cf_capex}', 'cf_cfo'), **A('={cf_cfo}+{cf_capex}'), cagr=True))
    add(Row('fcf_pub', '  Company-published free cash flow', 'memo', 'n1', h=lambda p: C.FCF_PUB.get(p.name)))
    add(Row('fcf_chk', '  Check: model vs company-published free cash flow (should be 0)', 'check', 'n1',
            h=hf('=IF(ISNUMBER({fcf_pub}),ROUND({fcf}-{fcf_pub},1),"n/p")', 'cf_cfo')))
    add(Row('fcf_g', '  FCF y/y %', 'yoy', 'p1', h=lambda p: (yoy('fcf')(p) if has(p, 'cf_cfo') and prior_year(p) is not None and has(prior_year(p), 'cf_cfo') else None),
            **A('=IFERROR({fcf}/{fcf@pa}-1,"")')))
    add(Row('fcf_m', '  FCF % of revenues', 'pct', 'p1', h=hf(ratio('fcf', 'is_rev'), 'cf_cfo'), **A(ratio('fcf', 'is_rev'))))
    add(Row('fcf_conv', '  FCF / adjusted income from continuing operations conversion %', 'pct', 'p1', h=hf(ratio('fcf', 'a_ni'), 'cf_cfo'), **A(ratio('fcf', 'a_ni'))))
    add(Row('fcf_ps', '  FCF per diluted share ($)', 'line', 'n2', h=hf(ratio('fcf', 'sh_d'), 'cf_cfo'), **A(ratio('fcf', 'sh_d'))))
    add(Row(None, 'Capex ratios', 'head'))
    add(Row('capex_pct', '  Capex % of revenues', 'pct', 'p1', h=hf('=IFERROR(-{cf_capex}/{is_rev},"")', 'cf_capex'), fa='={capex_in@abs}', f27='={capex27_in@abs}',
            note='FY2026 3.5%; UniFirst ~6.3% of revenue (FY25 $154m) → FY27E 3.7%, FY28E+ 3.9% input (incl. integration/automation investment).'))
    add(Row('capex_da', '  Capex / D&A (x)', 'line', 'x2', h=hf('=IFERROR(-{cf_capex}/{is_da},"")', 'cf_capex'), **A('=IFERROR(-{cf_capex}/{is_da},"")')))
    S.blank()

    # ---------------- buyback schedule
    add(Row(None, 'SHARE BUYBACK SCHEDULE', 'sec', note='SHARES — FY2027E includes ~14.07m UniFirst consideration shares at closing (0.7720 per UNF share; 424B3 pro forma count)'))
    add(Row('bb_px', '  Avg buyback price ($)', 'line', 'n2', f27='={px@$P:FY2027}', fa='={bb_px@pa}*(1+{px_g_in@abs})', note='FY27E = current share price (valuation input); appreciates with the share-price input.'))
    add(Row('bb_cash', '  Buyback cash deployed (USDm)', 'line', 'n1', h=lambda p: (-H[p.name]['cf_buyback'] if (not p.is_q and has(p, 'cf_buyback')) else None),
            f27='=-{cf_bb@P:FY2027Q1}+{bb27_in@abs}', fa='={lev_bb}',
            note='FY27E: Q1/27 actual $315.7m + $229m executed to 22-Sep-2026 (release) and paused thereafter pending the UniFirst close (input). FY28E+: leverage plug (debt schedule).'))
    add(Row('bb_sh', '  Implied shares repurchased (m)', 'line', 'n1', **A('=IFERROR({bb_cash}/{bb_px},0)')))
    add(Row('bb_iss', '  Shares issued under equity plans (m)', 'line', 'n1', **A('={sh_iss_in@abs}')))
    add(Row('bb_unf', '  UniFirst consideration shares issued (m)', 'line', 'n1', f27='={unf_sh@abs}*{unf_on}', fa='=0'))
    add(Row('bb_beg', '  Beginning shares outstanding (m)', 'line', 'n1', f27='={so@P:FY2026}', fa='={bb_end@pa}', note='FY2027E begins from shares outstanding at 31-May-2026 (400.1m; 10-K/release balance sheet).'))
    add(Row('bb_end', '  Ending shares outstanding (m)', 'key', 'n1', **A('={bb_beg}-{bb_sh}+{bb_iss}+{bb_unf}')))
    add(Row('bb_pctr', '  % of shares repurchased', 'pct', 'p1', **A('=IFERROR({bb_sh}/{bb_beg},"")')))
    S.blank()

    # ---------------- balance sheet
    add(Row(None, 'CONSOLIDATED BALANCE SHEET', 'sec', note='BS FORECAST — FY2027E rolled forward from the 31-May-2026 balance sheet + UniFirst preliminary purchase-price allocation (424B3; Cintas 28-Feb-2026 pro forma basis)'))
    add(Row(None, 'ASSETS', 'head'))
    add(Row('bs_cash', '  Cash and cash equivalents', 'line', 'n1', h=hv('bs_cash'), **A('={cf_end}')))
    add(Row('bs_mkt', '  Marketable securities (to FY2018)', 'line', 'n1', h=hv('bs_mktsec'), **A('={bs_mkt@pa}')))
    add(Row('bs_ar', '  Accounts receivable, net', 'line', 'n1', h=hv('bs_ar'), **A('={wc_rev}*{wc_dso}/365')))
    add(Row('bs_inv', '  Inventories, net', 'line', 'n1', h=hv('bs_inv'), **A('={wc_cogs}*{wc_dio}/365')))
    add(Row('bs_unif', '  Uniforms and other rental items in service', 'line', 'n1', h=hv('bs_uniforms'), **A('={wc_revu}*{wc_unif}'),
            note='Cintas-specific working-capital asset: garments in service are capitalised and amortised into cost of rental (~18 months).'))
    add(Row('bs_oca', '  Prepaid & other current assets (incl. income taxes receivable, current deferred taxes, held for sale)', 'line', 'n1',
            h=hsum('bs_prepaid', 'bs_ca_taxes', 'bs_ca_deftax', 'bs_ca_hfs'), **A('={wc_rev}*{wc_oca}')))
    add(Row('bs_tca', 'Total current assets', 'key', 'n1', h=hf('=SUM({bs_cash},{bs_mkt},{bs_ar},{bs_inv},{bs_unif},{bs_oca})', 'bs_ta'), **A('=SUM({bs_cash},{bs_mkt},{bs_ar},{bs_inv},{bs_unif},{bs_oca})')))
    add(Row('bs_ppe', '  Property and equipment, net', 'line', 'n1', h=hv('bs_ppe'), **A('={bs_ppe@pa}-{cf_capex}-{sch_dep}+{ppa_ppe@$P:FY2027}*IF({unf_on}*COLUMN()=COLUMN({unf_on@$P:FY2027}),1,0)'),
            note='Roll-forward: prior + capex − depreciation (+ UniFirst PP&E at fair value in FY2027E).'))
    add(Row('bs_invest', '  Investments (long-term)', 'line', 'n1', h=hv('bs_invest'), **A('={bs_invest@pa}')))
    add(Row('bs_gw', '  Goodwill', 'line', 'n1', h=hv('bs_gw'), **A('={bs_gw@pa}+{ppa_gw@$P:FY2027}*IF({unf_on}*COLUMN()=COLUMN({unf_on@$P:FY2027}),1,0)+N({ma_spend})*N({ma_gw_pct})'),
            note='FY2027E: + UniFirst preliminary goodwill $2,854.3m (424B3). FY28E+: + M&A spend × goodwill %.'))
    add(Row('bs_svc', '  Service contracts & other intangibles, net', 'line', 'n1', h=hv('bs_svc'),
            **A('={bs_svc@pa}+{ppa_int@$P:FY2027}*IF({unf_on}*COLUMN()=COLUMN({unf_on@$P:FY2027}),1,0)+N({ma_spend})*(1-N({ma_gw_pct}))-{sch_amort}'),
            note='+ UniFirst customer relationships $1,241m (15y) & trade names $50m (3y) − amortization (legacy + PPA + M&A).'))
    add(Row('bs_rou', '  Operating lease right-of-use assets (FY2020+)', 'line', 'n1', h=hv('bs_rou'), **A('={bs_rou@pa}+{ppa_rou@$P:FY2027}*IF({unf_on}*COLUMN()=COLUMN({unf_on@$P:FY2027}),1,0)')))
    add(Row('bs_oa', '  Other assets, net (incl. capitalized contract costs, long-term held for sale)', 'line', 'n1', h=hsum('bs_oth_assets', 'bs_nca_hfs'),
            **A('={bs_oa@pa}+{ppa_oa@$P:FY2027}*IF({unf_on}*COLUMN()=COLUMN({unf_on@$P:FY2027}),1,0)')))
    add(Row('bs_ta', 'TOTAL ASSETS', 'total', 'n1', h=hf('=SUM({bs_tca},{bs_ppe},{bs_invest},{bs_gw},{bs_svc},{bs_rou},{bs_oa})', 'bs_ta'),
            **A('=SUM({bs_tca},{bs_ppe},{bs_invest},{bs_gw},{bs_svc},{bs_rou},{bs_oa})'), cagr=True))
    add(Row(None, 'LIABILITIES AND EQUITY', 'head'))
    add(Row('bs_ap', '  Accounts payable', 'line', 'n1', h=hv('bs_ap'), **A('={wc_cogs}*{wc_dpo}/365')))
    add(Row('bs_acomp', '  Accrued compensation & related liabilities', 'line', 'n1', h=hv('bs_accr_comp'), **A('={wc_rev}*{wc_acomp}')))
    add(Row('bs_aliab', '  Accrued liabilities (current)', 'line', 'n1', h=hv('bs_accr_liab'), **A('={wc_rev}*{wc_aliab}')))
    add(Row('bs_ocl', '  Income taxes current, current deferred taxes & liabilities held for sale', 'line', 'n1', h=hsum('bs_cl_taxes', 'bs_cl_deftax', 'bs_cl_hfs'), **A('={bs_ocl@pa}')))
    add(Row('bs_cll', '  Operating lease liabilities, current', 'line', 'n1', h=hv('bs_cl_lease'), **A('={bs_cll@pa}+{ppa_cll@$P:FY2027}*IF({unf_on}*COLUMN()=COLUMN({unf_on@$P:FY2027}),1,0)')))
    add(Row('bs_dst', '  Debt due within one year', 'line', 'n1', h=hv('bs_debt_st'), **A('=MIN({debt_tot},-N({debt_mat_next}))'),
            note="Forecast: next fiscal year's scheduled note maturities."))
    add(Row('bs_tcl', 'Total current liabilities', 'key', 'n1', h=hf('=SUM({bs_ap},{bs_acomp},{bs_aliab},{bs_ocl},{bs_cll},{bs_dst})', 'bs_ta'), **A('=SUM({bs_ap},{bs_acomp},{bs_aliab},{bs_ocl},{bs_cll},{bs_dst})')))
    add(Row('bs_dlt', '  Debt due after one year', 'line', 'n1', h=hv('bs_debt_lt'), **A('={debt_tot}-{bs_dst}')))
    add(Row('bs_dtl', '  Deferred income taxes', 'line', 'n1', h=hv('bs_deftax'), **A('={bs_dtl@pa}+{cf_dtax}+{ppa_dtl@$P:FY2027}*IF({unf_on}*COLUMN()=COLUMN({unf_on@$P:FY2027}),1,0)')))
    add(Row('bs_lll', '  Operating lease liabilities (long-term)', 'line', 'n1', h=hv('bs_lt_lease'), **A('={bs_lll@pa}+{ppa_lll@$P:FY2027}*IF({unf_on}*COLUMN()=COLUMN({unf_on@$P:FY2027}),1,0)')))
    add(Row('bs_lta', '  Accrued liabilities (long-term)', 'line', 'n1', h=hv('bs_lt_accr'), **A('={bs_lta@pa}+{ppa_lta@$P:FY2027}*IF({unf_on}*COLUMN()=COLUMN({unf_on@$P:FY2027}),1,0)')))
    add(Row('bs_tl', 'Total liabilities', 'key', 'n1', h=hf('=SUM({bs_tcl},{bs_dlt},{bs_dtl},{bs_lll},{bs_lta})', 'bs_ta'), **A('=SUM({bs_tcl},{bs_dlt},{bs_dtl},{bs_lll},{bs_lta})')))
    add(Row(None, "Shareholders' equity:", 'head'))
    add(Row('bs_cs', '  Common stock & paid-in capital', 'line', 'n1', h=hsum('bs_cs', 'bs_apic'),
            **A('={bs_cs@pa}+{cf_sbc}+{cf_opt}+{ppa_eq@$P:FY2027}*IF({unf_on}*COLUMN()=COLUMN({unf_on@$P:FY2027}),1,0)'),
            note='+ stock-based compensation + option proceeds; FY2027E + UniFirst share consideration ($2,526.0m at the 424B3 price of $179.17).'))
    add(Row('bs_re', '  Retained earnings', 'line', 'n1', h=hv('bs_re'), **A('={bs_re@pa}+{is_ni}+{cf_div}')))
    add(Row('bs_ts', '  Treasury stock', 'line', 'n1', h=hv('bs_treas'), **A('={bs_ts@pa}+{cf_bb}'), note='Cintas holds repurchased shares in treasury (cost).'))
    add(Row('bs_aoci', '  Accumulated other comprehensive income (loss)', 'line', 'n1', h=hv('bs_aoci'), **A('={bs_aoci@pa}')))
    add(Row('bs_te', "Total shareholders' equity", 'total', 'n1', h=hf('=SUM({bs_cs},{bs_re},{bs_ts},{bs_aoci})', 'bs_ta'), **A('=SUM({bs_cs},{bs_re},{bs_ts},{bs_aoci})'), cagr=True))
    add(Row('bs_tle', 'TOTAL LIABILITIES AND EQUITY', 'total', 'n1', h=hf('={bs_tl}+{bs_te}', 'bs_ta'), **A('={bs_tl}+{bs_te}')))
    add(Row('chk_bs', 'BS tie-out check (TA − TL&E)', 'check', 'n1', h=hf('=ROUND({bs_ta}-{bs_tle},1)', 'bs_ta'), **A('=ROUND({bs_ta}-{bs_tle},1)')))
    add(Row('chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'n1', h=hf('=ROUND({bs_ta}-{bs_ta_rep},1)', 'bs_ta')))
    add(Row('bs_ta_rep', '  Memo: total assets as reported', 'memo', 'n1', h=hv('bs_ta'), level=1))
    def so(p):
        v = H.get(p.name, {}).get('bs_so_label')
        if not isinstance(v, (int, float)): return None
        return v / 1e6 if v > 2e6 else v / 1000.0
    add(Row('so', '  Memo: common shares outstanding at period end (m; split-adjusted)', 'memo', 'n1', h=so, fa='={bb_end}', f27='={bb_end}'))
    S.blank()

    # ---------------- working capital
    add(Row(None, 'WORKING CAPITAL & CASH CONVERSION', 'sec', note='WORKING CAPITAL — forecast drivers (blue = input)'))
    add(Row('wc_rev', '  Revenues — pro forma full-year basis (FY2027E incl. UniFirst pre-closing)', 'line', 'n1', h=hf('={is_rev}', 'bs_ta'),
            f27='={is_rev}+{unf_rr}*(365-{unf_days})/365*{unf_on}', fa='={is_rev}',
            note='FY2027E adds UniFirst sales for the pre-closing days so year-end working capital is sized on a full-year combined basis.'))
    add(Row('wc_revu', '  UR&FS-line revenues — pro forma basis', 'line', 'n1', h=hf('={is_rev_u}', 'bs_ta'),
            f27='={is_rev_u}+{unf_rr}*{unf_rent_sh@abs}*(365-{unf_days})/365*{unf_on}', fa='={is_rev_u}'))
    add(Row('wc_cogs', '  Cost of sales — pro forma basis', 'line', 'n1', h=hf('={is_cogs}', 'bs_ta'),
            f27='={is_cogs}+{unf_rr}*(1-{unf_gmp})*(365-{unf_days})/365*{unf_on}', fa='={is_cogs}'))
    def wcr(key, lab, tpl, fmt, inp, note=None):
        add(Row(key, lab, 'pct' if fmt == 'p1' else 'line', fmt, h=lambda p, tpl=tpl: (('=IFERROR(' + tpl + ',"n/a")') if (has(p, 'bs_ta') and (not p.is_q)) else None),
                fa='={%s@pa}' % key, f27='={%s@abs}' % inp, note=note))
    wcr('wc_dso', '  DSO — receivables / revenues × 365', '{bs_ar}/{wc_rev}*365', 'd0', 'dso_in')
    wcr('wc_dio', '  Inventory days — inventories / cost of sales × 365', '{bs_inv}/{wc_cogs}*365', 'd0', 'dio_in')
    wcr('wc_unif', '  Uniforms & rental items in service % of UR&FS-line revenues', '{bs_unif}/{wc_revu}', 'p1', 'unif_in')
    wcr('wc_oca', '  Prepaid & other current assets % of revenues', '{bs_oca}/{wc_rev}', 'p1', 'oca_in')
    wcr('wc_dpo', '  Payable days — payables / cost of sales × 365', '{bs_ap}/{wc_cogs}*365', 'd0', 'dpo_in')
    wcr('wc_acomp', '  Accrued compensation % of revenues', '{bs_acomp}/{wc_rev}', 'p1', 'acomp_in')
    wcr('wc_aliab', '  Accrued liabilities (current) % of revenues', '{bs_aliab}/{wc_rev}', 'p1', 'aliab_in',
        note='Forecast inputs set at FY2026 levels (annual columns; quarterly ratios distorted by annualisation).')
    add(Row('wc_nwc', '  Operating NWC (receivables + inventories + garments in service + other CA − payables − accrued − other CL)', 'line', 'n1',
            h=hf('={bs_ar}+{bs_inv}+{bs_unif}+{bs_oca}-{bs_ap}-{bs_acomp}-{bs_aliab}-{bs_ocl}', 'bs_ta'),
            **A('={bs_ar}+{bs_inv}+{bs_unif}+{bs_oca}-{bs_ap}-{bs_acomp}-{bs_aliab}-{bs_ocl}')))
    add(Row('wc_nwcp', '  NWC % of revenues', 'pct', 'p1', h=lambda p: ratio('wc_nwc', 'wc_rev') if (has(p, 'bs_ta') and not p.is_q) else None, **A(ratio('wc_nwc', 'wc_rev'))))
    add(Row('wc_dnwc', '  ΔNWC (y/y, excl. working capital acquired with UniFirst)', 'line', 'n1',
            h=lambda p: '={wc_nwc}-{wc_nwc@py}' if (not p.is_q and prior_year(p) is not None and has(p, 'bs_ta') and has(prior_year(p), 'bs_ta')) else None,
            f27='={wc_nwc}-{wc_nwc@pa}-{ppa_nwc@$P:FY2027}*{unf_on}', fa='={wc_nwc}-{wc_nwc@pa}'))
    S.blank()

    # ---------------- schedules
    add(Row(None, 'BALANCE SHEET FORECAST SCHEDULES', 'sec', note='BS FORECAST SCHEDULES — explicit driver assumptions'))
    add(Row(None, 'UniFirst acquisition — consideration & preliminary purchase-price allocation (424B3 filed 11-May-2026, unaudited pro forma; Cintas price $179.17)', 'sub'))
    ppa = X['ppa']
    for k, lab, v, note in ppa:
        add(Row(k, lab, 'sched', 'n1', f27=v, note=note))
    add(Row('ppa_chk', '  Check: assets acquired − liabilities assumed + goodwill − consideration (should be 0)', 'check', 'n1',
            f27='=ROUND({ppa_cashacq}+{ppa_nwc_a}+{ppa_ppe}+{ppa_int}+{ppa_rou}+{ppa_oa}+{ppa_gw}-{ppa_nwc_l}-{ppa_cll}-{ppa_dtl}-{ppa_lll}-{ppa_lta}-{ppa_cash}-{ppa_eq},1)'))
    add(Row(None, 'Asset roll-forwards: D&A split (BS integrity)', 'sub'))
    add(Row('sch_dep', '  Depreciation (PP&E)', 'sched', 'n1', **A('={da_leg}*{dep_sh_in@abs}+{unf_rev}*{unf_da_pct}+{unf_ppe_dep@abs}*{unf_on}+N({ma_rev})*0.015'),
            note='Legacy depreciation = 62% of legacy D&A (FY2026: depreciation $318.6m of $512.8m); + UniFirst standalone D&A & step-up; + M&A.'))
    add(Row('sch_amort_leg', '  Amortization of legacy acquired intangibles (service contracts)', 'sched', 'n1', f27='={amort_leg_in@abs}', fa='={sch_amort_leg@pa}*0.9',
            note='FY2026 10-K intangible amortization schedule; declines as acquired customer lists roll off (−10% p.a.).'))
    add(Row('sch_amort', '  Amortization of intangibles — total (legacy + UniFirst PPA + M&A)', 'sched', 'n1', **A('={sch_amort_leg}+{unf_amort}+N({ma_amort})')))
    add(Row('sch_cc', '  Amortization of capitalized contract costs (= additions; cash-neutral)', 'sched', 'n1', **A('={is_da}-{sch_dep}-{sch_amort}'),
            note='Residual of total D&A (ASC 340-40 commissions; additions assumed equal to amortization → other assets flat).'))
    add(Row(None, 'Debt schedule (scheduled note maturities + UniFirst acquisition debt + commercial paper / revolver to a minimum cash balance)', 'sub'))
    add(Row('debt_tot', '  Total debt (current + long-term)', 'sched', 'n1', h=lambda p: (H[p.name].get('bs_debt_st', 0) + H[p.name].get('bs_debt_lt', 0)) if has(p, 'bs_ta') else None,
            **A('={debt_notes}+{debt_fac}'), note='31-May-2026: $2,436.6m face — 3.70% $1,000m due FY2027, 4.20% $400m due 1-May-2028, 4.00% $800m due FY2032, 6.15% $236.6m due FY2037; no CP or revolver drawings (FY2026 10-K).'))
    add(Row('debt_mat', '  Scheduled note maturities (input, negative)', 'sched', 'n1', f27='={mat27_in@abs}', fa=lambda p: {2028: '={mat28_in@abs}', 2029: '=0', 2030: '=0', 2031: '=0'}[p.fy]))
    add(Row('debt_mat_next', "  Next year's maturities (for current portion)", 'sched', 'n1', f27='={debt_mat@P:FY2028}', fa=lambda p: '={debt_mat@P:FY%d}' % (p.fy + 1) if p.fy < 2031 else '=0', level=1))
    add(Row('debt_refpct', '  % of scheduled maturities refinanced (input)', 'sched', 'p1', **A('={refi_in@abs}')))
    add(Row('debt_refi', '  Refinancing issuance', 'sched', 'n1', **A('=-{debt_mat}*{debt_refpct}')))
    add(Row('debt_unf', '  UniFirst acquisition debt issued (permanent financing)', 'sched', 'n1', f27='={unf_debt@abs}*{unf_on}', fa='=0',
            note='$2.8bn permanent financing assumed in the 424B3 pro forma (5.0% rate; $19.5m issuance costs); $2.85bn bridge committed (now $1.6bn after the new $2.0bn revolver). No notes issued yet per EDGAR.'))
    add(Row('debt_notes', '  Senior notes & term debt outstanding (year end)', 'sched', 'n1', f27='={debt_tot@P:FY2026}+{debt_mat}+{debt_refi}+{debt_unf}', fa='={debt_notes@pa}+{debt_mat}+{debt_refi}+{debt_unf}'))
    add(Row('debt_cpre', '  Cash before CP / revolver (opening cash + CFO + CFI + dividends + buybacks + notes flows − opening CP)', 'sched', 'n1',
            **A('={cf_beg}+{cf_cfo}+{cf_cfi}+{cf_div}+{cf_bb}+{cf_opt}+{debt_mat}+{debt_refi}+{debt_unf}-{debt_fac@pa}')))
    add(Row('debt_mincash', '  Minimum cash balance', 'sched', 'n1', **A('={mincash_in@abs}')))
    add(Row('debt_fac', '  Commercial paper / revolver outstanding (year end)', 'sched', 'n1', h=lambda p: 0.0 if p.name == 'FY2026' else None,
            **A('=MAX(0,{debt_mincash}-{debt_cpre})'), note='Drawn/repaid so that cash = minimum balance; surplus cash accumulates (and funds the leverage-targeted buyback).'))
    add(Row('debt_facnet', '  Net CP / revolver issuance / (repayment)', 'sched', 'n1', **A('={debt_fac}-{debt_fac@pa}')))
    add(Row('debt_rate', '  Interest rate on senior notes & term debt (opening balance) %', 'sched', 'p1', fa='={notes_rate_in@abs}',
            note='FY2028E: ~$2.6bn legacy notes at ~4.4% (refinanced 2027s at ~4.75%) + $2.8bn acquisition debt at 5.0% → ~4.8% blended.'))
    add(Row('debt_frate', '  Interest rate on CP / revolver %', 'sched', 'p1', fa='={fac_rate_in@abs}'))
    add(Row('debt_yield', '  Interest income yield on opening cash %', 'sched', 'p1', fa='={cash_yld_in@abs}'))
    add(Row('debt_ie', '  Interest expense (FY28E+)', 'sched', 'n1', fa='={debt_notes@pa}*{debt_rate}+{debt_fac@pa}*{debt_frate}'))
    add(Row('debt_ii', '  Interest income (FY28E+)', 'sched', 'n1', fa='={cf_beg}*{debt_yield}'))
    add(Row(None, 'Leverage-targeted buybacks (repurchases plug to a target net debt / Adjusted EBITDA)', 'sub'))
    add(Row('lev_min', '  Target net debt / Adjusted EBITDA (x) (scenario)', 'sched', 'x2', fa=lambda p: '=' + SC('LEV', p),
            note='Cintas historically ~1.0–1.5x; 1.5x net leverage at the UniFirst close (deal 8-K). Buybacks resume once leverage falls to the target.'))
    add(Row('lev_nd0', '  Net debt before buybacks (year end)', 'sched', 'n1', fa='={nd@pa}-({cf_cfo}+{cf_cfi}+{cf_div}+{cf_opt})'))
    add(Row('lev_tgt', '  Target net debt = target leverage × Adjusted EBITDA', 'sched', 'n1', fa='={lev_min}*{adj_ebitda}'))
    add(Row('lev_bb', '  Share repurchases: plug to target leverage', 'sched', 'n1', fa='=MAX(0,{lev_tgt}-{lev_nd0})',
            note='Feeds the cash-flow repurchase line; zero while leverage is above target.'))
    add(Row(None, 'Other inputs', 'sub'))
    add(Row('dil_sec', '  Dilutive securities (m shares)', 'sched', 'n1', **A('={dil_in@abs}')))
    add(Row('px', '  Share price ($) — current (valuation input)', 'sched', 'n2', f27='={px_in@abs}', fa='={px@pa}*(1+{px_g_in@abs})'))
    S.blank()

    # ---------------- ratio analysis
    add(Row(None, 'RATIO ANALYSIS', 'sec', note='RETURNS — annual columns (NOPAT on adjusted EBIT)'))
    ann = lambda tpl: (lambda p: tpl if (not p.is_q and has(p, 'bs_ta') and has(p, 'cf_dep')) else None)
    AA = lambda tpl: dict(h=ann(tpl), f27=tpl, fa=tpl)
    add(Row(None, 'DuPont decomposition of ROIC', 'head'))
    add(Row('r_ebit', 'Adjusted EBIT (Adjusted EBITDA − D&A)', 'line', 'n1', **AA('={adj_ebit}')))
    add(Row('r_tax', 'Effective tax rate (actual)', 'pct', 'p1', **AA('={is_etr}')))
    add(Row('r_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'n1', **AA('={r_ebit}*(1-{r_tax})')))
    add(Row('r_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'n1', **AA('={bs_te}+{nd}')))
    add(Row('r_eq', '  Total equity', 'line', 'n1', **AA('={bs_te}')))
    add(Row('nd', '  Net debt = Total debt − cash & marketable securities', 'line', 'n1',
            h=lambda p: '={debt_tot}-{bs_cash}-N({bs_mkt})' if has(p, 'bs_ta') else None, **A('={debt_tot}-{bs_cash}-N({bs_mkt})')))
    add(Row('roic', 'ROIC = NOPAT / IC', 'total', 'p1', **AA('=IFERROR({r_nopat}/{r_ic},"")')))
    add(Row('r_m', '  Margin = Adjusted EBIT / Revenues', 'pct', 'p1', **AA('=IFERROR({r_ebit}/{is_rev},"")')))
    add(Row('r_t', '  Capital turnover = Revenues / IC', 'line', 'x2', **AA('=IFERROR({is_rev}/{r_ic},"")')))
    add(Row('r_tb', '  Tax burden = (1 − effective tax rate)', 'pct', 'p1', **AA('=1-{r_tax}')))
    add(Row('r_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'check', 'n2', **AA('=IFERROR(ROUND({r_m}*{r_t}*{r_tb}-{roic},4),"")')))
    add(Row(None, 'RONTA decomposition', 'head'))
    add(Row('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'n1', **AA('={r_nopat}')))
    add(Row('rn_ta', '  Total assets', 'line', 'n1', **AA('={bs_ta}')))
    add(Row('rn_gw', '  − Goodwill & acquired intangible assets', 'line', 'n1', **AA('=-({bs_gw}+{bs_svc})')))
    add(Row('rn_ncl', '  − Non-interest-bearing current liabilities (total CL excl. debt)', 'line', 'n1', **AA('=-({bs_tcl}-{bs_dst})')))
    add(Row('rn_nta', '  = Net tangible assets', 'line', 'n1', **AA('=SUM({rn_ta},{rn_gw},{rn_ncl})')))
    add(Row('ronta', 'RONTA = NOPAT / NTA', 'total', 'p1', **AA('=IFERROR({rn_nopat}/{rn_nta},"")')))
    add(Row(None, 'Return on Equity (ROE)', 'head'))
    add(Row('roe_ni', 'Net income', 'line', 'n1', **AA('={is_ni}')))
    add(Row('roe_eq', "Shareholders' equity", 'line', 'n1', **AA('={bs_te}')))
    add(Row('roe', 'ROE = Net income / Equity', 'total', 'p1', **AA('=IFERROR({roe_ni}/{roe_eq},"")')))
    add(Row(None, 'Leverage', 'head'))
    add(Row('lv_nd', 'Net debt = Total debt − cash', 'line', 'n1', **AA('={nd}')))
    add(Row('lv_eb', 'Adjusted EBITDA (FY2027E pro forma for UniFirst full year)', 'line', 'n1', **AA('={adj_ebitda_pf}')))
    add(Row('lev', 'Net debt / Adjusted EBITDA (x)', 'total', 'x2', **AA('=IFERROR({lv_nd}/{lv_eb},"n/a")')))
    S.blank()

    # ---------------- valuation
    add(Row(None, 'VALUATION', 'sec', note=X['val_note']))
    V = lambda tpl: dict(f27=tpl, fa=tpl)
    add(Row('v_px', 'Share price ($) — current', 'sched', 'n2', **V('={px@$P:FY2027}')))
    add(Row('v_sh', 'Diluted shares at period end (m)', 'line', 'n1', **V('={bb_end}+{dil_sec}')))
    add(Row('v_mc', 'Market capitalisation (USDm)', 'line', 'n0', **V('={v_px}*{v_sh}')))
    add(Row('v_nd', 'Net debt (USDm)', 'line', 'n0', **V('={nd}')))
    add(Row('v_ev', 'Enterprise value (USDm)', 'total', 'n0', **V('={v_mc}+{v_nd}')))
    add(Row(None, 'Multiples', 'head'))
    add(Row('v_evs', '  EV / Revenues (FY2027E pro forma)', 'line', 'x1', **V('=IFERROR({v_ev}/{wc_rev},"n/a")')))
    add(Row('v_eveb', '  EV / Adjusted EBITDA (FY2027E pro forma)', 'line', 'x1', **V('=IFERROR({v_ev}/{adj_ebitda_pf},"n/a")')))
    add(Row('v_evebit', '  EV / Adjusted EBIT', 'line', 'x1', **V('=IFERROR({v_ev}/{adj_ebit},"n/a")')))
    add(Row('v_evic', '  EV / IC', 'line', 'x1', **V('=IFERROR({v_ev}/{r_ic},"n/a")')))
    add(Row('v_pe', '  P / E (GAAP diluted, continuing ops)', 'line', 'x1', **V('=IFERROR({v_px}/{eps_dc},"n/a")')))
    add(Row('v_ape', '  P / E (adjusted EPS)', 'line', 'x1', **V('=IFERROR({v_px}/{a_eps},"n/a")')))
    add(Row('v_fcfy', '  FCF yield', 'pct', 'p1', **V('=IFERROR({fcf}/{v_mc},"n/a")')))
    add(Row('v_dy', '  Dividend yield', 'pct', 'p1', **V('=IFERROR({dps}/{v_px},"n/a")')))
