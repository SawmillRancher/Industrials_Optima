"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, QEc, B1

def build_spec2(V0):
    S = add
    def e26f(key, q4):          # FY2026E flow = 9M actual (Q1-Q3/26) + Q4/26E estimate
        return lambda: f'={ACT(key)}+{q4()}'
    CHG = ('bs_settle', 'bs_oca', 'bs_onca')           # operating assets that move with revenue (collateral, escrow, litigation held)
    CHGL = ('bs_settle_l', 'bs_ocl')
    def wc_flow(base):
        return ('=' + ''.join(f'-({V(k)}-{base(k)})' for k in CHG) + ''.join(f'+({V(k)}-{base(k)})' for k in CHGL))
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 9M FY26 actual + Q4 estimate; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net income', 'line', 'm', data='cf_ni', flow=True, fc=lambda: f'={V("is_ni_tot")}', e26=e26f('cf_ni', lambda: QEc('is_ni_tot')))
    S('cf_adj', 'Non-cash items:', 'sub', 'gen')
    S('cf_dda', '  Depreciation & amortization', 'line', 'm', data='cf_dda', flow=True, fc=lambda: f'={V("is_dda")}', e26=e26f('cf_dda', lambda: QEc('is_dda')))
    S('cf_sbc', '  Share-based compensation', 'line', 'm', data='cf_sbc', flow=True, fc=lambda: f'={V("is_sbc")}', e26=e26f('cf_sbc', lambda: QEc('is_sbc')))
    S('cf_def', '  Deferred income taxes', 'line', 'm', data='cf_def', flow=True, e26=lambda: f'={ACT("cf_def")}+{V0["def_q4"]}', ae_in=V0['def_ae'],
      note='Forecast input (FY2026 9M −$638m includes the deferred tax benefits adjusted out of non-GAAP).')
    S('cf_wc', '  Client incentives, settlement, litigation & other operating items, net (derived)', 'line', 'm', data='cf_wc', flow=True,
      e26=lambda: '=' + ACT('cf_wc') + wc_flow(B1)[1:],
      ae=lambda: wc_flow(P),
      note=('History: net cash from operating activities − net income − D&A − share-based compensation − deferred taxes (client-incentive amortization and payments, '
            'settlement balances, accrued litigation, other). Forecast linked to the balance sheet: −Δ(settlement receivable, other current and non-current assets) '
            '+ Δ(settlement payable, other current liabilities); collateral, escrow and accrued litigation held.'))
    S('cf_cfo', 'Net cash provided by operating activities', 'line_b', 'm', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Purchases of property, equipment & technology', 'line', 'm', data='cf_capex', flow=True,
      e26=lambda: f'=-{PT("pt_capex")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='2026E: 9M actual $1,178m + Q4 estimate (point input). 2027E+: net revenue × capex %.')
    S('cf_acq', 'Acquisitions, net of cash acquired', 'line', 'm', data='cf_acq', flow=True,
      e26=lambda: f'={ACT("cf_acq")}', ae=lambda: f'=-{V("m_spend")}', note='FY2016: Visa Europe ($13.9bn up-front cash, net of cash acquired). 2026E = 9M actual. 2027E+: M&A lever.')
    S('cf_oinv', 'Investment securities, other investments & other investing, net (derived)', 'line', 'm', data='cf_oinv', flow=True,
      e26=lambda: f'={ACT("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Net cash provided by (used in) investing activities', 'line_b', 'm', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_bb', 'Repurchases of class A common stock', 'line', 'm', data='cf_bb', flow=True, e26=lambda: f'={ACT("cf_bb")}-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='2026E: 9M actual + Q4 scenario input ($28.4bn remaining authorization at 30-Jun-2026). 2027E+ = leverage plug (surplus cash returned until net debt / adjusted EBITDA reaches the target).')
    S('cf_div', 'Dividends paid', 'line', 'm', data='cf_div', flow=True,
      e26=lambda: f'={ACT("cf_div")}-{QEc("dps")}*{QEc("sh_dil")}', ae=lambda: f'=-{V("dps")}*{V("bb_beg")}',
      note='Dividends on class A and, on an as-converted basis, class B / C and preferred (dividend × as-converted shares).')
    S('cf_debt', 'Senior notes & commercial paper, net issuance / (repayment)', 'line', 'm', data='cf_debt', flow=True,
      e26=lambda: f'={ACT("cf_debt")}+({V("ds_total")}-{B1("ds_total")})', ae=lambda: f'={V("ds_net")}',
      note='Per the debt schedule: notes repaid at maturity and refinanced; commercial paper drawn or repaid to the minimum cash balance.')
    S('cf_ofin', 'Equity plans, withholding taxes, litigation escrow (to FY2018) & other financing, net (derived)', 'line', 'm', data='cf_ofin', flow=True,
      e26=lambda: f'={ACT("cf_ofin")}+{V0["ofin_q4"]}', ae_in=V0['ofin_ae'])
    S('cf_cff', 'Net cash provided by (used in) financing activities', 'line_b', 'm', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_bb")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of exchange rate changes on cash', 'line', 'm', data='cf_fx', flow=True, e26=lambda: f'={ACT("cf_fx")}', ae_in=0.0)
    S('cf_net', 'Net change in cash (incl. restricted cash and equivalents from FY2019)', 'line', 'm', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")}),"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}')
    S('cf_beg', 'Cash — beginning of period', 'line', 'm', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period (cash-flow basis)', 'line_b', 'm', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: beginning cash + CFO + CFI + CFF + FX = ending cash (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=1.01,0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},1)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")})<=1.01,0,ROUND(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")},1)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (model definition: CFO − purchases of property, equipment & technology; Visa publishes no FCF measure in its releases)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")},"")')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of net revenue', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / non-GAAP net income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of net revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note='2027E+ input: FY2021–25 3.0–3.7% of net revenue (technology investment).')
    S('capex_dep', '  Capex / D&A (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_dda")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE (as-converted class A shares)', 'section',
      note='SHARES — 2026E = Q4 from the 30-Jun-2026 as-converted share proxy; 2027E+ buybacks via the leverage plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = Q4)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans, net (m)', 'driver', 'm2', e26_in=V0['iss_q4'], ae_in=V0['iss_ae'])
    S('bb_beg', '  Beginning as-converted shares (m)', 'line', 'm1', e26_in=MAN['shares']['as_converted_2026_06_30_proxy'], ae=lambda: f'={P("bb_end")}',
      note=MAN['shares']['note'])
    S('bb_end', '  Ending as-converted shares (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since Q4/26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET (condensed, as in the releases)', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Jun-2026 balance sheet + Q4 flows; 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}-{V("bs_rc")}')
    S('bs_escrow', '  Restricted cash — U.S. litigation escrow', 'line', 'm', data='bs_escrow', bs=True, e26=lambda: f'={B1("bs_escrow")}', ae=lambda: f'={P("bs_escrow")}')
    S('bs_inv', '  Investment securities (current and non-current)', 'line', 'm', data='bs_inv', bs=True, e26=lambda: f'={B1("bs_inv")}', ae=lambda: f'={P("bs_inv")}',
      note='Held at the 30-Jun-2026 level (assumption).')
    S('bs_settle', '  Settlement receivable', 'line', 'm', data='bs_settle', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_settle")}')
    S('bs_collat', '  Customer collateral (asset; equal liability)', 'line', 'm', data='bs_collat', bs=True, e26=lambda: f'={B1("bs_collat")}', ae=lambda: f'={P("bs_collat")}')
    S('bs_oca', '  Accounts receivable, client incentives, prepaid & other current assets (derived)', 'line', 'm', data='bs_oca', bs=True,
      fc=lambda: f'={V("wc_rev")}*{V("wc_oca")}')
    S('bs_tca', 'Total current assets (incl. current investment securities)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")',
      note='Investment securities are shown in one line; the reported total current assets excludes the non-current portion.')
    S('bs_ppe', '  Property, equipment & technology, net', 'line', 'm', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-({V("cf_capex")}-{ACT("cf_capex")})-({QEc("is_dda")}-{QEc("d_int_am")})',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-({V("is_dda")}-{V("d_int_am")})+{V("m_spend")}*{V("m_ppe")}',
      note='Roll-forward: prior − capex (negative cash flow) − (D&A − finite-lived intangible amortization) + acquired PP&E / technology.')
    S('bs_gw', '  Goodwill', 'line', 'm', data='bs_gw', bs=True, e26=lambda: f'={B1("bs_gw")}', ae=lambda: f'={P("bs_gw")}+{V("m_spend")}*(1-{V("m_ppe")}-{V("m_intp")})')
    S('bs_int', '  Intangible assets, net (mostly indefinite-lived: Visa Europe customer relationships & reacquired rights, trade name)', 'line', 'm', data='bs_int', bs=True,
      e26=lambda: f'={B1("bs_int")}-{QEc("d_int_am")}', ae=lambda: f'={P("bs_int")}-{V("d_int_am")}+{V("m_spend")}*{V("m_intp")}',
      note='Roll-forward: prior − finite-lived amortization (10-K schedule) + acquired intangibles. Indefinite-lived intangibles (~$27bn) are not amortized.')
    S('bs_onca', '  Client incentives (non-current), deferred tax & other assets (derived)', 'line', 'm', data='bs_onca', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_onca")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_ppe")}:{V("bs_onca")}),"")')
    S('bs_l', 'LIABILITIES AND EQUITY', 'sub', 'gen')
    S('bs_settle_l', '  Settlement payable', 'line', 'm', data='bs_settle_l', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_settle_l")}')
    S('bs_collat_l', '  Customer collateral (liability)', 'line', 'm', data='bs_collat_l', bs=True, e26=lambda: f'={B1("bs_collat_l")}', ae=lambda: f'={P("bs_collat_l")}')
    S('bs_litig', '  Accrued litigation', 'line', 'm', data='bs_litig', bs=True, e26=lambda: f'={B1("bs_litig")}', ae=lambda: f'={P("bs_litig")}',
      note='Held (assumption): covered litigation is paid from the escrow; no new provisions forecast.')
    S('bs_std', '  Current maturities of debt & commercial paper', 'line', 'm', data='bs_std', bs=True, fc=lambda: f'={V("ds_rev")}+MIN({V("ds_notes")},{V("ds_mat")})')
    S('bs_ocl', '  Accounts payable, accrued compensation, client incentives & accrued liabilities (derived)', 'line', 'm', data='bs_ocl', bs=True,
      fc=lambda: f'={V("wc_rev")}*{V("wc_ocl")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_settle_l")}),SUM({V("bs_settle_l")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term debt', 'line', 'm', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_std")}')
    S('bs_ol', '  Deferred tax liabilities & other liabilities (derived)', 'line', 'm', data='bs_ol', bs=True,
      e26=lambda: f'={B1("bs_ol")}+({V("cf_def")}-{ACT("cf_def")})', ae=lambda: f'={P("bs_ol")}+{V("cf_def")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_settle_l")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_ol")}),"")')
    S('bs_eq', '  Equity (incl. preferred stock; FY2008–09 incl. temporary equity)', 'line', 'm', data='bs_te', bs=True,
      e26=lambda: (f'={B1("bs_eq")}+{QEc("is_ni_tot")}+({V("cf_div")}-{ACT("cf_div")})+({V("cf_bb")}-{ACT("cf_bb")})+{QEc("d_sbc")}+({V("cf_ofin")}-{ACT("cf_ofin")})'),
      ae=lambda: f'={P("bs_eq")}+{V("is_ni_tot")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_sbc")}+{V("cf_ofin")}',
      note='+ net income − dividends − repurchases + share-based compensation + equity-plan / other financing flows (OCI and FX translation held flat).')
    S('bs_nci', '  Non-controlling interests (none since FY2013; inside equity before)', 'line', 'm', e26=lambda: '=0', ae=lambda: '=0')
    S('bs_teq', 'Total equity', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")}+N({V("bs_nci")}),"")')
    S('bs_tle', 'TOTAL LIABILITIES AND EQUITY', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=1.01,0,ROUND({V("bs_ta")}-{V("bs_tle")},1)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=1.01,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},1)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs_ta', bs=True)
    S('bs_rc', '  Memo: restricted cash & equivalents in the cash-flow cash (CF ending cash − BS cash; litigation escrow, collateral; from FY2019)', 'memo', 'm', bs=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("cf_end")}),ISNUMBER({V("bs_cash")})),{V("cf_end")}-{V("bs_cash")},"")',
      e26=lambda: f'={B1("bs_rc")}', ae=lambda: f'={P("bs_rc")}',
      note='ASU 2016-18 (FY2019): the cash-flow statement includes restricted cash and equivalents (U.S. litigation escrow, customer collateral, other). Before FY2019 the CF reconciles cash and cash equivalents only. Forecast held at the 30-Jun-2026 level.')
    S('bs_chk_cash', '  Check: BS cash vs cash-flow ending cash, before FY2019 (should be 0; restricted cash memo from FY2019)', 'check', 'm',
      hist=lambda: (f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}-{V("cf_end")})<=1.01,0,ROUND({V("bs_cash")}-{V("cf_end")},1)),"")'
                    if CTX.col.year < 2019 else None),
      fc=lambda: f'=ROUND({V("bs_cash")}+{V("bs_rc")}-{V("cf_end")},1)')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & SETTLEMENT BALANCES', 'section', note='WORKING CAPITAL — forecast drivers (blue = input, fiscal-year-end ratios to net revenue)')
    S('wc_rev', '  Net revenue — annualised (quarters × 4)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    for k, lab, bk in (('settle', 'Settlement receivable % of net revenue', 'bs_settle'), ('oca', 'Other current assets % of net revenue', 'bs_oca'),
                       ('onca', 'Other non-current assets % of net revenue', 'bs_onca'), ('settle_l', 'Settlement payable % of net revenue', 'bs_settle_l'),
                       ('ocl', 'Other current liabilities % of net revenue', 'bs_ocl')):
        S(f'wc_{k}', f'  {lab}', 'pct', 'pct', hist=lambda bk=bk: f'=IFERROR({V(bk)}/{V("wc_rev")},"")', e26_in=V0['wc'][k], ae_in=V0['wc'][k],
          note=V0['wc']['note'] if k == 'settle' else None)
    S('wc_nwc', '  Operating NWC (settlement receivable + other operating assets − settlement payable − other current liabilities)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_settle")}),{V("bs_settle")}+{V("bs_oca")}+{V("bs_onca")}-{V("bs_settle_l")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of net revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppa_h', 'Acquisitions — consideration & purchase-price allocation (closing-period column)', 'sub', 'gen')
    for k, lab in [('cons', 'Accounting purchase consideration'), ('ca', 'Current assets acquired (incl. cash, settlement receivable)'),
                   ('nca', 'Non-current assets acquired'), ('intang', 'Intangible assets (customer relationships & reacquired rights)'), ('gw', 'Goodwill'),
                   ('cl', 'Current liabilities assumed'), ('ncl', 'Non-current liabilities assumed')]:
        S(f'ppa_{k}', f'  {lab}', 'sched', 'm', data=f'ppa_{k}', ppa=True)
    S('ppa_chk', '  Check: assets acquired − liabilities assumed − consideration (should be 0)', 'check', 'm',
      hist=lambda: (f'=IF(ISNUMBER({V("ppa_cons")}),ROUND(N({V("ppa_ca")})+N({V("ppa_nca")})+N({V("ppa_intang")})+N({V("ppa_gw")})'
                    f'-N({V("ppa_cl")})-N({V("ppa_ncl")})-{V("ppa_cons")},1),"")'))
    S('ppa_names', '  Deal closed in the period', 'text', 'gen', data='ppa_names', ppa=True, textdata=True)
    S('rf_h', 'Share pricing & amortization', 'sub', 'gen')
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.08)
    S('d_int_am', '  Finite-lived intangible amortization (10-K schedule; inside D&A)', 'sched', 'm', qe_in=16.0, e26=lambda: f'={QEc("d_int_am")}',
      ae_in=V0['int_am'], note='FY2025 10-K Note 8: $63m (FY26), $62m, $43m, $29m, $10m (FY30); FY31 $5m assumed. Q4/26E ~$16m.')
    S('ds_h', 'Debt schedule (senior notes repaid at maturity and refinanced; commercial paper drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (current maturities + commercial paper + long-term debt)', 'sched', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_rev")}', note=MAN['debt']['at_2026_06_30'])
    S('ds_notes', '  Senior notes (carrying value)', 'sched', 'm', e26=lambda: f'={B1("ds_total")}-{MAN["debt"]["cp_2026_06_30"]}-{V("ds_repay")}+{V("ds_iss")}',
      ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_iss', '  New notes issued (input)', 'sched', 'm', e26_in=V0['iss_notes'][FYC], ae_in={y: V0['iss_notes'][y] for y in range(FYC + 1, FYL + 1)},
      note=MAN['debt']['new_notes_note'])
    S('ds_repay', '  Notes repaid at maturity (input)', 'sched', 'm', e26_in=V0['repay'][FYC], ae_in={y: V0['repay'][y] for y in range(FYC + 1, FYL + 1)},
      note=MAN['debt']['maturities_note'])
    S('ds_mat', '  Maturities in the following fiscal year (current portion)', 'sched', 'm', e26_in=V0['mat'][FYC], ae_in={y: V0['mat'][y] for y in range(FYC + 1, FYL + 1)})
    S('ds_pre', '  BS cash before commercial paper (opening cash + CFO + CFI + buybacks, dividends, other financing + FX − notes repaid + issued)', 'sched', 'm',
      e26=lambda: (f'={B1("bs_cash")}+({V("cf_cfo")}-{ACT("cf_cfo")})+({V("cf_cfi")}-{ACT("cf_cfi")})+({V("cf_bb")}-{ACT("cf_bb")})+({V("cf_div")}-{ACT("cf_div")})'
                   f'+({V("cf_ofin")}-{ACT("cf_ofin")})+({V("cf_fx")}-{ACT("cf_fx")})-{V("ds_repay")}+{V("ds_iss")}'),
      ae=lambda: f'={P("bs_cash")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_bb")}+{V("cf_div")}+{V("cf_ofin")}+{V("cf_fx")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_min', '  Minimum cash balance', 'sched', 'm', e26_in=V0['min_cash'], ae_in=V0['min_cash'], note=V0['min_cash_note'])
    S('ds_rev', '  Commercial paper / incremental borrowing (year end; plug to the minimum cash balance)', 'sched', 'm',
      e26=lambda: f'=MAX(0,{MAN["debt"]["cp_2026_06_30"]}+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_rev")}+{V("ds_min")}-{V("ds_pre")})',
      note='$1.5bn commercial paper at 30-Jun-2026 (3.77%). Shortfalls below the minimum cash balance (e.g. buybacks up to the leverage target) are funded here — a proxy for commercial paper or new notes; surplus repays it.')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on opening senior notes %', 'sched', 'pct', ae_in=V0['r_notes'], note=V0['r_notes_note'])
    S('ds_r_rev', '  Interest rate on opening commercial paper %', 'sched', 'pct', ae_in=0.038, note='30-Jun-2026 weighted average 3.77%.')
    S('ds_fees', '  Other interest (hedging, fees, debt-cost amortization) ($m)', 'sched', 'm', ae_in=20.0)
    S('ds_r_cash', '  Investment income yield on opening cash & investment securities %', 'sched', 'pct', ae_in=V0['r_cash'], note=V0['r_cash_note'])
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / adjusted EBITDA, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / adjusted EBITDA (x) (scenario)', 'sched', 'x2', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end; debt − cash − investment securities)', 'sched', 'm',
      ae=lambda: f'={P("ds_total")}-{P("bs_cash")}-{P("bs_inv")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_ofin")}-{V("cf_fx")}')
    S('lev_tgt', '  Target net debt = target leverage × adjusted EBITDA', 'sched', 'm', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to target leverage', 'sched', 'm', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash beyond the leverage target is returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of net revenue', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_int', '  Interest expense ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_intexp")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted EBIT, full-cost)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT, full-cost (adjusted EBITDA − total D&A)', 'line', 'm', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate (non-GAAP)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("e_rate")}+0,0.18)')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity', 'line', 'm', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),{V("bs_teq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − cash − investment securities', 'line', 'm', ann=True,
      all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")}-{V("bs_inv")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Net revenue', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Net revenue / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-({V("bs_gw")}+{V("bs_int")}),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. current debt)', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})),"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income', 'line', 'm', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', 'Equity', 'line', 'm', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash − investment securities', 'line', 'm', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA (model definition)', 'line', 'm', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_gx', 'Total debt / adjusted EBITDA (x)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("ds_total")}/{V("r_adj")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted as-converted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    S('v_mc', 'Market capitalisation (USDm; class A price × as-converted shares)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Non-controlling interests (USDm)', 'line', 'm', e26=lambda: f'={V("bs_nci")}', ae=lambda: f'={V("bs_nci")}')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Net revenue', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted operating income', lambda: f'=IFERROR({V("v_ev")}/{V("o_adj")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (non-GAAP EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
