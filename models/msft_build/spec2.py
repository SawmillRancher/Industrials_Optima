"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules (PPA, debt, finance leases,
liquidity-target buybacks), ratios, valuation. Forecast columns are annual (FY2027E = the four estimate quarters of the P&L;
balance sheet and cash flow at fiscal year end)."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, B1

def build_spec2(V0):
    S = add
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CASH FLOWS STATEMENTS', 'section',
      note='CASH FLOW — forecast logic (annual; FY2027E from the FY2027E P&L and the 30-Jun-2027 balance sheet; quarters = the releases\' three-month columns)')
    S('cf_ni', 'Net income', 'line', 'm', data='cf_ni', flow=True, fc=lambda: f'={V("is_ni")}')
    S('cf_adj', 'Adjustments to reconcile net income to net cash from operations:', 'sub', 'gen')
    S('cf_dda', '  Depreciation, amortization, and other', 'line', 'm', data='cf_dda', flow=True, fc=lambda: f'={V("is_dda")}',
      note='Q1 FY26 restated from the Q2 FY26 year-to-date statement ($4,914m reclassified to investment gains; manual_items.json).')
    S('cf_sbc', '  Stock-based compensation expense', 'line', 'm', data='cf_sbc', flow=True, fc=lambda: f'={V("is_sbc")}')
    S('cf_def', '  Deferred income taxes', 'line', 'm', data='cf_def', flow=True, e26_in=V0['def_tax'], ae_in=V0['def_tax'], note='Forecast input (assumption).')
    S('cf_wc', '  Investment (gains) losses, working capital & other operating items, net (derived)', 'line', 'm', data='cf_wc', flow=True,
      fc=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_inv")}-{P("bs_inv")})-({V("bs_oca")}-{P("bs_oca")})'
                  f'+({V("bs_ap")}-{P("bs_ap")})+({V("bs_ucr")}-{P("bs_ucr")})+({V("bs_ocl")}-{P("bs_ocl")})'),
      note=('History: net cash from operations − net income − D&A & other − stock-based compensation − deferred taxes (incl. investment gains / losses and '
            'unearned-revenue deferrals). Forecast linked to the balance sheet: −Δ(receivables, inventories, other current assets) + Δ(payables, unearned revenue, other current liabilities).'))
    S('cf_cfo', 'Net cash from operations', 'line_b', 'm', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Additions to property and equipment', 'line', 'm', data='cf_capex', flow=True,
      fc=lambda: f'=-({V("d_capex")}-{V("x_fl_add")})', note='Cash capex = capital expenditures incl. finance leases − finance-lease assets obtained (non-cash).')
    S('cf_acq', 'Acquisition of companies, net of cash acquired, and purchases of intangible and other assets', 'line', 'm', data='cf_acq', flow=True,
      fc=lambda: f'=-{V("m_spend")}', note='FY2017 LinkedIn; FY2022 Nuance; FY2024 Activision Blizzard (net of cash acquired). 2028E+: M&A lever.')
    S('cf_oinv', 'Purchases, maturities & sales of investments and other investing, net (derived)', 'line', 'm', data='cf_oinv', flow=True, e26_in=0.0, ae_in=0.0,
      note='Forecast nil: short-term investments held flat; all liquidity changes go through cash.')
    S('cf_cfi', 'Net cash used in investing', 'line_b', 'm', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_bb', 'Common stock repurchased', 'line', 'm', data='cf_bb', flow=True, fc=lambda: f'=-{V("lev_bb")}',
      note='Includes shares withheld for employee taxes. Forecast = liquidity-target plug (schedule below), with a scenario minimum.')
    S('cf_div', 'Common stock cash dividends paid', 'line', 'm', data='cf_div', flow=True, fc=lambda: f'=-{V("dps")}*{V("bb_beg")}',
      note='Forecast = dividends declared per share × beginning shares (the one-quarter payment lag is ignored).')
    S('cf_iss', 'Common stock issued', 'line', 'm', data='cf_iss', flow=True, e26_in=V0['stock_iss'], ae_in=V0['stock_iss'])
    S('cf_debt', 'Debt issued / (repaid), net (incl. short-term debt)', 'line', 'm', data='cf_debt', flow=True,
      fc=lambda: f'={V("ds_cp")}-{P("ds_cp")}-{V("ds_repay")}', note='Notes repaid at maturity (face); short-term borrowing drawn / repaid to the minimum liquidity balance.')
    S('cf_ofin', 'Other financing, net (incl. finance-lease principal; derived historically)', 'line', 'm', data='cf_ofin', flow=True,
      fc=lambda: f'=-{V("fl_prin")}', note='Forecast = finance-lease principal repayments (schedule below).')
    S('cf_cff', 'Net cash used in financing', 'line_b', 'm', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_bb")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of foreign exchange rates on cash and cash equivalents', 'line', 'm', data='cf_fx', flow=True, e26_in=0.0, ae_in=0.0)
    S('cf_net', 'Net change in cash and cash equivalents', 'line', 'm', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")}),"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}')
    S('cf_beg', 'Cash and cash equivalents, beginning of period', 'line', 'm', data='cf_beg', fc=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash and cash equivalents, end of period', 'line_b', 'm', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: beginning cash + CFO + CFI + CFF + FX = ending cash (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=1,0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},0)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")})<=1,0,ROUND(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")},0)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (model: net cash from operations − additions to property and equipment)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")},"")',
      note='Microsoft does not reconcile a free-cash-flow measure in its releases; model definition (labelled).')
    S('fcf_fl', '  FCF after finance-lease assets obtained (FCF − finance-lease right-of-use assets; annual)', 'line', 'm', ann=True,
      all=lambda: f'=IF(AND(ISNUMBER({V("fcf")}),ISNUMBER({V("x_fl_add")})),{V("fcf")}-{V("x_fl_add")},"")')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of revenue', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Additions to property and equipment % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")')
    S('capex_dep', '  Additions to property and equipment / D&A & other (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("d_dda")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — FY2027E from shares outstanding at 30-Jun-2026; buybacks via the liquidity-target plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', a26_in=round(16719 / 36, 2), e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})',
      note='FY2026A: $16,719m ÷ 36m shares repurchased under the program (10-K Note 15). FY2027E: current share price; then + appreciation.')
    S('bb_cash', '  Buyback cash deployed (USDm; incl. tax withholding)', 'line', 'm', a26=lambda: f'=-{V("cf_bb")}', e26=lambda: f'=-{V("cf_bb")}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh_a', '  Memo: shares repurchased under the program (m; 10-K)', 'memo', 'm1', a26_in=36.0)
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', a26=lambda: f'={V("bb_sh_a")}', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under employee plans (m)', 'driver', 'm2', e26_in=V0['iss_sh'], ae_in=V0['iss_sh'], note='FY2026 29m, FY2025 31m, FY2024 34m (10-K Note 15).')
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='FY2027E begins from shares outstanding at 30-Jun-2026 (7,427m; 7,425.5m on the 23-Jul-2026 10-K cover).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased from FY2027E (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'BALANCE SHEETS (condensed)', 'section', note='BS FORECAST — fiscal year ends; FY2027E from the 30-Jun-2026 balance sheet')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}')
    S('bs_sti', '  Short-term investments', 'line', 'm', data='bs_sti', bs=True, fc=lambda: f'={P("bs_sti")}')
    S('bs_ar', '  Accounts receivable, net', 'line', 'm', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_inv', '  Inventories', 'line', 'm', data='bs_inv', bs=True, fc=lambda: f'={P("bs_inv")}')
    S('bs_oca', '  Other current assets (incl. deferred taxes to FY2016; derived)', 'line', 'm', data='bs_oca', bs=True, fc=lambda: f'={P("bs_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_ppe', '  Property and equipment, net (incl. finance-lease assets)', 'line', 'm', data='bs_ppe', bs=True,
      fc=lambda: f'={P("bs_ppe")}+{V("d_capex")}-{V("d_dep")}+{V("m_spend")}*{V("m_ppe")}',
      note='Roll-forward: prior + capital expenditures incl. finance leases − depreciation + acquired PP&E.')
    S('bs_eqinv', '  Equity and other investments (incl. OpenAI equity-method investment)', 'line', 'm', data='bs_eqinv', bs=True, fc=lambda: f'={P("bs_eqinv")}')
    S('bs_gw', '  Goodwill', 'line', 'm', data='bs_gw', bs=True, fc=lambda: f'={P("bs_gw")}+{V("m_spend")}*(1-{V("m_ppe")}-{V("m_intp")})')
    S('bs_int', '  Intangible assets, net', 'line', 'm', data='bs_int', bs=True, fc=lambda: f'={P("bs_int")}-{V("d_amort")}+{V("m_spend")}*{V("m_intp")}',
      note='Roll-forward: prior − amortization + acquired intangibles (M&A lever).')
    S('bs_onca', '  Operating lease right-of-use assets & other long-term assets (derived)', 'line', 'm', data='bs_onca', bs=True, fc=lambda: f'={P("bs_onca")}')
    S('bs_ta', 'Total assets', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_ppe")}:{V("bs_onca")}),"")')
    S('bs_l', "LIABILITIES AND STOCKHOLDERS' EQUITY", 'sub', 'gen')
    S('bs_ap', '  Accounts payable', 'line', 'm', data='bs_ap', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_app")}')
    S('bs_cdebt', '  Short-term debt & current portion of long-term debt', 'line', 'm', data='bs_cdebt', bs=True,
      fc=lambda: f'=MIN({V("ds_notes")},{V("ds_mat")})+{V("ds_cp")}', note='Notes maturing in the following fiscal year + short-term borrowing.')
    S('bs_ucr', '  Short-term unearned revenue', 'line', 'm', data='bs_ucr', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_ucr")}')
    S('bs_ocl', '  Accrued compensation, income taxes & other current liabilities (derived)', 'line', 'm', data='bs_ocl', bs=True, fc=lambda: f'={P("bs_ocl")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_ap")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term debt', 'line', 'm', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_cdebt")}')
    S('bs_ol', '  Long-term income taxes, unearned revenue, deferred taxes, lease liabilities (incl. finance leases) & other (derived)', 'line', 'm', data='bs_ol', bs=True,
      fc=lambda: f'={P("bs_ol")}+{V("cf_def")}+({V("fl_liab")}-{P("fl_liab")})', note='Roll-forward: prior + deferred taxes + change in finance-lease liabilities.')
    S('bs_tl', 'Total liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_ol")}),"")')
    S('bs_eq', "  Total stockholders' equity", 'line', 'm', data='bs_eq', bs=True,
      fc=lambda: f'={P("bs_eq")}+{V("is_ni")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_sbc")}+{V("cf_iss")}',
      note='+ net income − dividends − repurchases + stock-based compensation + stock issued (other comprehensive income held flat; dividends paid ≈ declared).')
    S('bs_nci', '  Noncontrolling interests (none)', 'line', 'm', a26=lambda: '=0', e26=lambda: '=0', ae=lambda: '=0')
    S('bs_tle', "Total liabilities and stockholders' equity", 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_eq")}+N({V("bs_nci")}),"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=1,0,ROUND({V("bs_ta")}-{V("bs_tle")},0)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=1,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},0)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash vs cash-flow ending cash (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}-{V("cf_end")})<=1,0,ROUND({V("bs_cash")}-{V("cf_end")},0)),"")')
    S('bs_shares', '  Memo: shares outstanding at period end (m; balance-sheet caption)', 'memo', 'm1', data='bs_shares', bs=True, fc=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers at fiscal-year-end levels (blue = input)')
    S('wc_rev', '  Revenue — annualised (quarters × 4)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — receivables / revenue × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'],
      note=V0['wc']['note'])
    S('wc_ucr', '  Short-term unearned revenue % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ucr")}/{V("wc_rev")},"")', e26_in=V0['wc']['ucr'], ae_in=V0['wc']['ucr'])
    S('wc_app', '  Accounts payable % of revenue (incl. capex payables)', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_rev")},"")', e26_in=V0['wc']['ap'], ae_in=V0['wc']['ap'])
    S('wc_nwc', '  Operating NWC (receivables + inventories + other current assets − payables − unearned revenue − other current liabilities)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_inv")}+{V("bs_oca")}-{V("bs_ap")}-{V("bs_ucr")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppa_h', 'Acquisitions — consideration & purchase-price allocation (closing-quarter column)', 'sub', 'gen')
    for k, lab in [('cons', 'Consideration — net of cash acquired'), ('ca', 'Current assets acquired (short-term investments, receivables, other)'),
                   ('ppe', 'Property and equipment'), ('intang', 'Intangible assets'), ('gw', 'Goodwill'), ('onca', 'Other assets'),
                   ('cl', 'Current / other liabilities assumed'), ('debt', 'Debt assumed'), ('ncl', 'Deferred & long-term income taxes and other noncurrent liabilities')]:
        S(f'ppa_{k}', f'  {lab}', 'sched', 'm', data=f'ppa_{k}', ppa=True)
    S('ppa_chk', '  Check: assets acquired − liabilities assumed − consideration (should be 0)', 'check', 'm',
      hist=lambda: (f'=IF(ISNUMBER({V("ppa_cons")}),ROUND(N({V("ppa_ca")})+N({V("ppa_ppe")})+N({V("ppa_intang")})+N({V("ppa_gw")})+N({V("ppa_onca")})'
                    f'-N({V("ppa_cl")})-N({V("ppa_debt")})-N({V("ppa_ncl")})-{V("ppa_cons")},0),"")'))
    S('ppa_names', '  Deal closed in the period', 'text', 'gen', data='ppa_names', textdata=True)
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; stock awards)', 'sched', 'm1', ae_in=V0['dil'], note='FY2026: diluted 7,453m vs basic 7,429m.')
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.08)
    S('ds_h', 'Debt schedule (senior notes repaid at maturity at face; short-term borrowing drawn / repaid to a minimum liquidity balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (short-term + current portion + long-term; carrying value)', 'sched', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_cdebt")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_cp")}', note=MAN['debt']['note'])
    S('ds_notes', '  Senior notes (carrying value)', 'sched', 'm', data='debt_tot', fc=lambda: f'={P("ds_notes")}-{V("ds_repay")}')
    S('ds_repay', '  Notes repaid at maturity (face; input)', 'sched', 'm', e26_in=V0['repay'][FYC], ae_in={y: V0['repay'][y] for y in range(FYC + 1, FYL + 1)},
      note='10-K maturities (face): FY27 $9,250m, FY28 nil, FY29 $2,001m, FY30 nil, FY31 $500m, thereafter $34,385m. No refinancing assumed (net-cash balance sheet).')
    S('ds_mat', '  Maturities in the following fiscal year (current portion)', 'sched', 'm', e26_in=V0['mat'][FYC], ae_in={y: V0['mat'][y] for y in range(FYC + 1, FYL + 1)},
      note='FY2031E: FY2032 maturities are not split out in the 10-K ("thereafter"); set to nil (assumption).')
    S('ds_cp', '  Short-term borrowing / commercial paper (year end)', 'sched', 'm', e26=lambda: f'=MAX(0,{P("ds_cp")}+{V("lq_min")}-({V("lq_pre")}-{V("lev_bb")}))',
      ae=lambda: f'=MAX(0,{P("ds_cp")}+{V("lq_min")}-({V("lq_pre")}-{V("lev_bb")}))', hist=lambda: '=0' if CTX.col.year == 2026 and CTX.col.q is None else None,
      note='Drawn when liquidity after the minimum buyback falls below the minimum liquidity balance; repaid from surplus. Nil at 30-Jun-2026.')
    S('ds_r_debt', '  Interest rate on opening debt, net of capitalised interest %', 'sched', 'pct', ae_in=V0['r_debt'], note=V0['r_debt_note'])
    S('ds_r_cash', '  Interest & dividend yield on opening cash & short-term investments %', 'sched', 'pct', ae_in=V0['r_cash'], note=V0['r_cash_note'])
    S('fl_h', 'Finance leases (datacenters) — liabilities in other current / long-term liabilities', 'sub', 'gen')
    S('fl_liab', '  Finance-lease liabilities (year end)', 'sched', 'm', data='x_fl', ann=True, fc=lambda: f'={P("fl_liab")}+{V("x_fl_add")}-{V("fl_prin")}',
      note=MAN['debt']['fl_note'])
    S('fl_prin', '  Finance-lease principal repaid', 'sched', 'm', data='x_fl_prin', ann=True, fc=lambda: f'={P("fl_liab")}*{V("fl_prin_r")}')
    S('fl_prin_r', '  Principal repaid ÷ opening liabilities %', 'sched', 'pct', ann=True,
      hist=lambda: (f'=IF(AND(ISNUMBER({V("fl_prin")}),ISNUMBER({P("fl_liab")})),IFERROR({V("fl_prin")}/{P("fl_liab")},""),"")' if CTX.col.prior else None),
      e26_in=V0['fl_prin_r'], ae_in=V0['fl_prin_r'], note='FY2026 6.7% ($3,101m / $46,172m); FY2025 8.4%. Input.')
    S('fl_rate', '  Finance-lease interest rate on opening liabilities %', 'sched', 'pct', ae_in=MAN['debt']['fl_rate'], note='Weighted-average discount rate 4.5% (FY2026 10-K).')
    S('lq_h', 'Liquidity-target buybacks (net-cash balance sheet: repurchases plug to a target cash & short-term investment balance)', 'sub', 'gen')
    S('lq_open', '  Opening cash & short-term investments', 'sched', 'm', fc=lambda: f'={P("bs_cash")}+{P("bs_sti")}')
    S('lq_pre', '  Liquidity before buybacks & short-term borrowing (opening + CFO + CFI + dividends + stock issued + other financing + FX − notes repaid)', 'sched', 'm',
      fc=lambda: f'={V("lq_open")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_div")}+{V("cf_iss")}+{V("cf_ofin")}+{V("cf_fx")}-{V("ds_repay")}')
    S('lq_tgt', '  Target cash & short-term investments (scenario)', 'sched', 'm', fc=lambda: '=' + CH(SC['LIQ']), note=V0['liq_note'])
    S('lq_bbmin', '  Minimum share repurchases (scenario)', 'sched', 'm', fc=lambda: '=' + CH(SC['BBMIN']), note=V0['bbmin_note'])
    S('lev_bb', '  Share repurchases: MAX(minimum, liquidity before buybacks − target)', 'sched', 'm', fc=lambda: f'=MAX({V("lq_bbmin")},{V("lq_pre")}-{V("lq_tgt")})',
      note='Surplus liquidity above the target is returned via buybacks; feeds the cash-flow repurchase line.')
    S('lq_min', '  Minimum cash & short-term investments (short-term borrowing drawn below it)', 'sched', 'm', e26_in=V0['min_liq'], ae_in=V0['min_liq'])
    S('lq_end', '  Memo: cash & short-term investments at year end', 'memo_calc', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_cash")}+{V("bs_sti")},"")')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  D&A & other % of revenue', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_amort', '  Amortization of intangibles % of revenue (annual)', 'pct', 'pct', ann=True, all=ratio('d_amort', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted operating income; invested capital incl. finance-lease liabilities)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT, full-cost (= adjusted operating income)', 'line', 'm', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate (GAAP)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("is_etr")}+0,0.19)')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity', 'line', 'm', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt + finance-lease liabilities − cash − short-term investments', 'line', 'm', ann=True,
      all=lambda: f'=IFERROR({V("ds_total")}+N({V("fl_liab")})-{V("bs_cash")}-{V("bs_sti")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Revenue', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Revenue / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-({V("bs_gw")}+{V("bs_int")}),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. short-term debt)', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_cdebt")})),"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income', 'line', 'm', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Stockholders' equity", 'line', 'm', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt (incl. finance leases) = Total debt + finance-lease liabilities − cash − short-term investments', 'line', 'm', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA (model)', 'line', 'm', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_gx', 'Total debt (excl. finance leases) / EBITDA (x)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("ds_total")}/{V("r_ebitda")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', a26_in=V0['px'], e26=lambda: f'={P("v_px")}', ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', a26=lambda: f'={V("bs_shares")}+({LQ}{R["sh_dil"]}-{LQ}{R["sh_basic"]})',
      e26=lambda: f'={V("bb_end")}+({LQ}{R["sh_dil"]}-{LQ}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    vf = lambda f: dict(a26=f, e26=f, ae=f)
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', **vf(lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")'))
    S('v_nd', 'Net debt incl. finance leases (USDm)', 'line', 'm', **vf(lambda: f'={V("lv_nd")}'))
    S('v_nci', 'Noncontrolling interests (USDm)', 'line', 'm', **vf(lambda: f'=N({V("bs_nci")})'))
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', **vf(lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")'))
    S('v_eqinv', '  Memo: equity and other investments incl. OpenAI (carrying value; not deducted from EV)', 'memo_calc', 'm', **vf(lambda: f'={V("bs_eqinv")}'))
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Revenue', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted operating income', lambda: f'=IFERROR({V("v_ev")}/{V("o_adj")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', a26=f, e26=f, ae=f)
