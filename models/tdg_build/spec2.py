"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules, ratios, valuation.
Forecast columns are annual (FY2027E = the sum of its quarters for flows; balances rolled from 30-Sep-2026); quarters are blank."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum

def build_spec2(V0):
    S = add
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; quarters = discrete, derived from the year-to-date statements in the 10-Q / 10-K)')
    S('cf_ni', 'Net income', 'line', 'm1', data='cf_ni', flow=True, fc=lambda: f'={V("is_ni")}')
    S('cf_adj', 'Non-cash items:', 'sub', 'gen')
    S('cf_dda', '  Depreciation & amortization (incl. product certification costs)', 'line', 'm1', data='cf_dda', flow=True, fc=lambda: f'={V("is_dda")}')
    S('cf_amdebt', '  Amortization of debt issuance costs / discount & non-cash refinancing costs', 'line', 'm1', data='cf_amdebt', flow=True, fc=lambda: f'={V("ds_amdebt")}')
    S('cf_sbc', '  Non-cash stock & deferred compensation expense', 'line', 'm1', data='cf_sbc', flow=True, fc=lambda: f'={V("is_sbc")}')
    S('cf_def', '  Deferred income taxes', 'line', 'm1', data='cf_def', flow=True, fc_in=V0['def_ae'], note='Forecast input (FY2026 $48m; FY2024–25 ±$10m).')
    S('cf_gain', '  (Gain) / loss on sale of businesses', 'line', 'm1', data='cf_gain', flow=True, fc=lambda: '=0')
    S('cf_wc', '  Working capital & other operating items, net (derived)', 'line', 'm1', data='cf_wc', flow=True,
      fc=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_inv")}-{P("bs_inv")})-({V("bs_oca")}-{P("bs_oca")})'
                  f'+({V("bs_ap")}-{P("bs_ap")})+({V("bs_ocl")}-{P("bs_ocl")})'),
      note=('History: net cash from operating activities − the lines above (includes inventory step-up, foreign-exchange and other non-cash items). '
            'Forecast linked to the balance sheet: −Δ(receivables, inventories, prepaid & other) + Δ(payables, accrued & other current liabilities).'))
    S('cf_cfo', 'Net cash provided by operating activities', 'line_b', 'm1', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Capital expenditures', 'line', 'm1', data='cf_capex', flow=True, fc=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='Not guided. Forecast: net sales × capex % (FY2024–26 2.1–2.6%).')
    S('cf_acq', 'Acquisition of businesses, net of cash acquired', 'line', 'm1', data='cf_acq', flow=True, fc=lambda: f'=-{V("m_spend")}',
      note='FY2026: Simmonds $757m, JPE / VSA $2,142m, P&I $1,058m, other bolt-ons $434m. FY2027E: Extant asset purchase ~$240m (8-K 21-Sep-2026). 2028E+: M&A lever.')
    S('cf_oinv', 'Other investing activities, net (derived; incl. divestiture proceeds)', 'line', 'm1', data='cf_oinv', flow=True, fc_in=0.0)
    S('cf_cfi', 'Net cash used in investing activities', 'line_b', 'm1', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_stock', 'Proceeds from exercise of stock options', 'line', 'm1', data='cf_stock', flow=True, fc_in=V0['stock_ae'])
    S('cf_div', 'Special dividends and dividend-equivalent payments', 'line', 'm1', data='cf_div', flow=True,
      e27=lambda: f'=-{Y("is_divp", 2027)}', ae=lambda: f'=-{V("lev_cr")}*{V("lev_spd")}',
      note='FY2027E: the $54m of dividend-equivalent payments accrued at 30-Sep-2026. 2028E+: special-dividend share of the leverage-targeted capital return (scenario split).')
    S('cf_bb', 'Repurchases of common stock', 'line', 'm1', data='cf_bb', flow=True,
      e27=lambda: f'=-{CH(SC["bb27"])}', ae=lambda: f'=-{V("lev_cr")}*(1-{V("lev_spd")})',
      note='FY2027E: scenario input ($3,038m remaining on the repurchase program at 30-Sep-2026). 2028E+ = buyback share of the leverage plug (surplus capacity returned until net debt / EBITDA As Defined reaches the target).')
    S('cf_debt', 'Net debt issuance / (repayment) (forecast; historically within debt & other financing)', 'line', 'm1',
      fc=lambda: f'={V("ds_iss")}-{V("ds_repay")}+({V("ds_rev")}-{P("ds_rev")})',
      note='Per the debt schedule: maturities refinanced with new notes, term-loan amortization repaid, incremental borrowings drawn to the minimum cash balance.')
    S('cf_ofin', 'Debt & other financing, net (derived historically)', 'line', 'm1', data='cf_ofin', flow=True, fc_in=0.0)
    S('cf_cff', 'Net cash provided by (used in) financing activities', 'line_b', 'm1', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_stock")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of exchange-rate changes on cash', 'line', 'm1', data='cf_fx', flow=True, fc_in=0.0)
    S('cf_net', 'Net change in cash (incl. restricted cash)', 'line', 'm1', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")}),"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}')
    S('cf_beg', 'Cash — beginning of period', 'line', 'm1', data='cf_beg', fc=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period (incl. restricted cash from FY2019)', 'line_b', 'm1', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: CFO + CFI + CFF + FX = change in cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=0.15,0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},1)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")})<=0.15,0,ROUND(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")},1)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (model definition: CFO − capital expenditures; TransDigm publishes no FCF measure)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")},"")')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of net sales', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per share ($)', 'line', 'ps', all=ratio('fcf', 'sh_d'))
    S('fcf_eb', '  FCF / EBITDA As Defined %', 'pct', 'pct', all=ratio('fcf', 'r_ad'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of net sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")', fc_in=V0['capex_pct'])
    S('capex_dep', '  Capex / depreciation & other amortization (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("d_dep")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — FY2027E from shares outstanding at 30-Sep-2026; 2028E+ buybacks via the leverage plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e27=lambda: f'={Y("v_px", 2026)}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm)', 'line', 'm', fc=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', fc=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued on option exercises (m)', 'driver', 'm2', fc_in=V0['iss_ae'])
    S('bb_beg', '  Beginning common shares outstanding (m)', 'line', 'm1', fc=lambda: f'={P("bs_shares")}',
      note='FY2027E begins from common shares outstanding at 30-Sep-2026 (issued 62,984,285 less treasury 8,406,114; FY2026 10-K).')
    S('bb_end', '  Ending common shares outstanding (m)', 'line', 'm1', fc=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', fc=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since FY2027E (m)', 'memo', 'm1', e27=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET (condensed)', 'section', note='BS FORECAST — rolled forward from the prior fiscal year end (FY2027E from 30-Sep-2026)')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm1', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}-{V("bs_rcash")}')
    S('bs_rcash', '  Restricted cash (note-redemption escrow; Q2 FY2019, Q2 FY2023, Q2 FY2024)', 'line', 'm1', data='bs_rcash', bs=True, fc_in=0.0)
    S('bs_ar', '  Trade accounts receivable — net', 'line', 'm1', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_inv', '  Inventories — net', 'line', 'm1', data='bs_inv', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dio")}/365')
    S('bs_oca', '  Prepaid expenses & other current assets (derived)', 'line', 'm1', data='bs_oca', bs=True, fc=lambda: f'={P("bs_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_ppe', '  Property, plant & equipment — net', 'line', 'm1', data='bs_ppe', bs=True,
      fc=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("d_dep")}+{V("m_spend")}*{V("m_ppe")}', note='Roll-forward: prior − capex (negative cash flow) − depreciation & other amortization + acquired PP&E.')
    S('bs_gw', '  Goodwill', 'line', 'm1', data='bs_gw', bs=True, fc=lambda: f'={P("bs_gw")}+{V("m_spend")}*(1-{V("m_ppe")}-{V("m_intp")})')
    S('bs_int', '  Other intangible assets — net', 'line', 'm1', data='bs_int', bs=True,
      fc=lambda: f'={P("bs_int")}-{V("d_amort")}+{V("m_spend")}*{V("m_intp")}', note='Roll-forward: prior − amortization + acquired intangibles (M&A lever).')
    S('bs_onca', '  Other non-current assets (derived)', 'line', 'm1', data='bs_onca', bs=True, fc=lambda: f'={P("bs_onca")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_ppe")}:{V("bs_onca")}),"")')
    S('bs_l', "LIABILITIES, REDEEMABLE NCI AND STOCKHOLDERS' EQUITY (DEFICIT)", 'sub', 'gen')
    S('bs_cltd', '  Current portion of long-term debt', 'line', 'm1', data='bs_cltd', bs=True, fc=lambda: f'=MIN({V("ds_notes")},{V("ds_mat")})')
    S('bs_std', '  Short-term borrowings — trade receivable securitization facility', 'line', 'm1', data='bs_std', bs=True, fc=lambda: f'={P("bs_std")}',
      note='$1,000m facility (amended 10-Jul-2026; matures 9-Jul-2027, annual extensions); held at the 30-Sep-2026 balance (assumption: renewed).')
    S('bs_ap', '  Accounts payable', 'line', 'm1', data='bs_ap', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dpo")}/365')
    S('bs_ocl', '  Accrued & other current liabilities (derived; FY2024 incl. the $75 special dividend payable)', 'line', 'm1', data='bs_ocl', bs=True,
      fc=lambda: f'={V("wc_rev")}*{V("wc_oclp")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cltd")}),SUM({V("bs_cltd")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term debt', 'line', 'm1', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_cltd")}-{V("bs_std")}')
    S('bs_deftax', '  Deferred income taxes', 'line', 'm1', data='bs_deftax', bs=True, fc=lambda: f'={P("bs_deftax")}+{V("cf_def")}')
    S('bs_oncl', '  Other non-current liabilities (derived)', 'line', 'm1', data='bs_oncl', bs=True, fc=lambda: f'={P("bs_oncl")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cltd")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_oncl")}),"")')
    S('bs_rnci', '  Redeemable noncontrolling interests (temporary equity; JPE / VSA / P&I from FY2026)', 'line', 'm1', data='bs_rnci', bs=True, fc=lambda: f'={P("bs_rnci")}',
      note='Held flat (assumption; NCI income is retained in the NCI line below).')
    S('bs_eq', "  TD Group stockholders' equity (deficit)", 'line', 'm1', data='bs_eq', bs=True,
      fc=lambda: f'={P("bs_eq")}+{V("is_ni_td")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_sbc")}+{V("cf_stock")}',
      note='+ net income attributable to TD Group − dividends / dividend equivalents − repurchases + stock compensation + option proceeds (OCI held flat). FY2027E: the $54m of dividend equivalents accrued at 30-Sep-2026 is charged here (simplification).')
    S('bs_nci', '  Noncontrolling interests', 'line', 'm1', data='bs_nci', bs=True, fc=lambda: f'={P("bs_nci")}+{V("is_nci")}')
    S('bs_teq', "Total stockholders' equity (deficit)", 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")}+N({V("bs_nci")}),"")')
    S('bs_tle', "TOTAL LIABILITIES, REDEEMABLE NCI AND STOCKHOLDERS' EQUITY", 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+N({V("bs_rnci")})+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=0.15,0,ROUND({V("bs_ta")}-{V("bs_tle")},1)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=0.15,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},1)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm1', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash + restricted cash vs cash-flow ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}+N({V("bs_rcash")})-{V("cf_end")})<=0.15,0,ROUND({V("bs_cash")}+N({V("bs_rcash")})-{V("cf_end")},1)),"")')
    S('bs_ncit', '  Memo: noncontrolling interests incl. redeemable (deducted in EV)', 'memo_calc', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_nci")}),{V("bs_nci")}+N({V("bs_rnci")}),"")')
    S('bs_shares', '  Memo: common shares outstanding at period end (issued less treasury, m)', 'memo', 'm1', data='bs_shares', bs=True, fc=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input; fiscal-year-end levels)')
    S('wc_rev', '  Net sales — annualised (quarters × 4)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_cogs', '  Cost of sales — annualised', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_cogs")}*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — receivables / net sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', fc_in=V0['wc']['dso'])
    S('wc_dio', '  Inventory days — inventories / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_inv")}/{V("wc_cogs")}*365,"")', fc_in=V0['wc']['dio'])
    S('wc_dpo', '  Payable days — payables / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_cogs")}*365,"")', fc_in=V0['wc']['dpo'])
    S('wc_oclp', '  Accrued & other current liabilities % of net sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")',
      fc_in=V0['wc']['ocl'], note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables + inventories + prepaid & other − payables − accrued & other)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_inv")}+{V("bs_oca")}-{V("bs_ap")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of net sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm1', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppa_h', 'Acquisitions — consideration & purchase-price allocation (closing-period column; FY2026 deals)', 'sub', 'gen')
    for k, lab in [('cons', 'Consideration — cash paid, net of cash acquired'), ('gw', 'Goodwill'),
                   ('intang', 'Other intangible assets (technology, customer relationships, trade names, backlog)'),
                   ('onet', 'Other net assets acquired incl. working capital, deferred taxes and redeemable NCI (derived = consideration − goodwill − intangibles)')]:
        S(f'ppa_{k}', f'  {lab}', 'sched', 'm1', data=f'ppa_{k}', ppa=True)
    S('ppa_chk', '  Check: goodwill + intangibles + other net assets − consideration (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("ppa_cons")}),ROUND(N({V("ppa_gw")})+N({V("ppa_intang")})+N({V("ppa_onet")})-{V("ppa_cons")},1),"")')
    S('ppa_names', '  Deal closed in the period', 'text', 'gen', data='ppa_names', ppa=True, textdata=True)
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_part', '  Vested options deemed participating securities (m shares; two-class method)', 'sched', 'm1', fc_in=V0['part'],
      note='1.6m at Q4 FY2026 (1.7m FY2026 average); held flat.')
    S('ds_partp', '  Participating share of dividends (participating options / total two-class shares)', 'sched', 'pct', fc_in=V0['partp'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', fc_in=0.08)
    S('ds_h', 'Debt schedule (notes and term loans at carrying value; maturities refinanced with new notes; incremental borrowings to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (current portion + securitization + long-term debt; carrying value)', 'sched', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_cltd")})+N({V("bs_std")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_rev")}', note=MAN['debt']['at_2026_09_30'])
    S('ds_notes', '  Notes, term loans, securitization, finance leases & other (carrying value)', 'sched', 'm1',
      hist=lambda: f'={V("ds_total")}', fc=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}+{V("ds_amdebt")}')
    S('ds_iss', '  New notes issued to refinance maturities (input)', 'sched', 'm1', fc_in={y: V0['refi'][y] for y in range(FYC, FYL + 1)},
      note='Assumption: every note / tranche maturity is refinanced at maturity with new notes (TransDigm has refinanced every maturity since its 2006 IPO).')
    S('ds_repay', '  Scheduled repayments: term-loan amortization + note / tranche maturities (input)', 'sched', 'm1', fc_in={y: V0['repay'][y] for y in range(FYC, FYL + 1)},
      note=MAN['debt']['maturities_note'])
    S('ds_mat', '  Scheduled principal due in the following fiscal year (current portion)', 'sched', 'm1', fc_in={y: V0['mat'][y] for y in range(FYC, FYL + 1)})
    S('ds_amdebt', '  Non-cash interest: amortization of debt issuance costs / discount (accretes to carrying value)', 'sched', 'm1', fc_in=V0['amdebt'])
    S('ds_pre', '  Cash before incremental borrowings (opening cash + CFO + CFI + option proceeds + dividends + buybacks + other + FX − repayments + issuance)', 'sched', 'm1',
      fc=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_stock")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_ofin")}+{V("cf_fx")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_min', '  Minimum cash balance', 'sched', 'm1', fc_in=V0['min_cash'], note='TransDigm held $2.3–6.3bn of cash at FY2023–26 year ends. Minimum $1.5bn (assumption).')
    S('ds_rev', '  Incremental borrowings (year end): revolver / securitization / new term debt to the minimum cash balance', 'sched', 'm1',
      e27=lambda: f'=MAX(0,{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_rev")}+{V("ds_min")}-{V("ds_pre")})',
      note='Shortfalls below the minimum cash balance are borrowed; surplus repays incremental borrowings. Amounts above the $910m revolver ($865m available) are assumed new notes / term loans (financing assumption).')
    S('ds_head', '  Memo: revolver capacity remaining vs the $865m available (negative = assumed new term debt)', 'memo_calc', 'm1', fc=lambda: f'=865-{V("ds_rev")}')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm1', fc=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on opening notes, term loans & securitization (net of hedges) %', 'sched', 'pct', fc_in=V0['r_notes'], note=V0['r_notes_note'])
    S('ds_r_rev', '  Interest rate on opening incremental borrowings %', 'sched', 'pct', fc_in=0.0675, note='2035 secured notes issued 28-Sep-2026 at 6.750%.')
    S('ds_r_cash', '  Interest income yield on opening cash %', 'sched', 'pct', fc_in=0.037, note='Assumption (money-market yields; US Treasury data not reachable from the build environment).')
    S('lev_h', 'Leverage-targeted capital return (special dividends + buybacks plug to a target net debt / EBITDA As Defined, 2028E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / EBITDA As Defined (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before capital return (year end)', 'sched', 'm1',
      ae=lambda: f'={P("ds_total")}-{P("cf_end")}+{V("ds_amdebt")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_stock")}-{V("cf_ofin")}-{V("cf_fx")}')
    S('lev_tgt', '  Target net debt = target leverage × EBITDA As Defined', 'sched', 'm1', ae=lambda: f'={V("lev_min")}*{V("r_ad")}')
    S('lev_cr', '  Capital return: plug to target leverage (special dividends + buybacks)', 'sched', 'm1', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Capacity up to the leverage target is returned; feeds the dividend and repurchase lines of the cash-flow statement.')
    S('lev_spd', '  Special-dividend share of the capital return (input)', 'sched', 'pct', ae_in=V0['spd'],
      note='TransDigm alternates between special dividends (FY2013–25: $7.65–$90 per share) and buybacks (record $2.75bn in FY2026); 50% assumption.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of net sales', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_amort', '  Amortization of intangibles % of net sales', 'pct', 'pct', all=ratio('d_amort', 'is_rev'))
    S('hr_int', '  Interest expense — net ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted EBIT, full-cost; tax at the effective rate bounded 15–35%)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT, full-cost (EBITDA As Defined − total D&A)', 'line', 'm1', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate (bounded 15–35%)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(MIN(0.35,MAX(0.15,{V("is_etr")})),0.23)')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt + NCI incl. redeemable', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")}+N({V("bs_rnci")}),"n/a")')
    S('ra_eq', '  Total equity (deficit)', 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),{V("bs_teq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − cash (incl. restricted)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")}-N({V("bs_rcash")}),"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Net sales', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Net sales / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm1', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & other intangible assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-({V("bs_gw")}+{V("bs_int")}),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. debt)', 'line', 'm1', ann=True,
      all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_cltd")})-N({V("bs_std")})),"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income attributable to TD Group', 'line', 'm1', ann=True, all=lambda: f'={V("is_ni_td")}')
    S('roe_eq', "TD Group stockholders' equity (deficit)", 'line', 'm1', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net income / Equity (n/m while equity is a deficit)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(IF({V("roe_eq")}>0,{V("roe_ni")}/{V("roe_eq")},"n/m"),"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'EBITDA As Defined', 'line', 'm1', ann=True, all=lambda: f'={V("r_ad")}')
    S('lv_x', 'Net debt / EBITDA As Defined (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_gx', 'Gross debt / EBITDA As Defined (x)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("ds_total")}/{V("lv_eb")},"n/a")')
    S('lv_ic', 'EBITDA As Defined / interest expense — net (x)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_eb")}/{V("is_int")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', a26_in=V0['px'], fc=lambda: f'={P("v_px")}')
    S('v_sh', 'Shares at period end (m; common + participating options)', 'line', 'm1', a26=lambda: f'={V("bs_shares")}+{V0["part"]}', fc=lambda: f'={V("bb_end")}+N({V("ds_part")})')
    for k, lab, f in [('v_mc', 'Market capitalisation (USDm)', lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")'),
                      ('v_nd', 'Net debt (USDm)', lambda: f'={V("lv_nd")}'),
                      ('v_nci', 'Noncontrolling interests incl. redeemable (USDm)', lambda: f'={V("bs_ncit")}'),
                      ('v_ev', 'Enterprise value (USDm)', lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')]:
        S(k, lab, 'line_b' if k == 'v_ev' else 'line', 'm', a26=f, fc=f)
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Net sales', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / EBITDA As Defined', lambda: f'=IFERROR({V("v_ev")}/{V("r_ad")},"n/a")'),
                      ('v_evop', '  EV / Adjusted EBIT (full-cost)', lambda: f'=IFERROR({V("v_ev")}/{V("r_ebit")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP)', lambda: f'=IFERROR({V("v_px")}/{V("eps_d")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield (special dividends)', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', a26=f, fc=f)
