"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules (PPAs, debt, capacity
monetization, leverage-targeted buybacks), ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, QEc, B1, tol, Y27

def build_spec2(V0):
    S = add
    yr = lambda d: {y: d[y] for y in range(FYC + 1, FYL + 1)}
    def e26f(key, q4):          # FY2026E flow = 9M actual (Q1-Q3/26) + Q4/26E estimate
        return lambda: f'={ACT(key)}+{q4()}'
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = nine months actual + Q4 estimate; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net income (loss)', 'line', 'm1', data='cf_ni', flow=True, fc=lambda: f'={V("is_nitot")}', e26=e26f('cf_ni', lambda: QEc('is_nitot')))
    S('cf_adj', 'Non-cash items:', 'sub', 'gen')
    S('cf_unr', '  Unrealized (gains) losses on derivative instruments', 'line', 'm1', data='cf_unr', flow=True, e26=lambda: f'={ACT("cf_unr")}', ae_in=0.0)
    S('cf_dda', '  Depreciation, amortization and accretion (net of acquired-contract amortization)', 'line', 'm1', data='cf_dda', flow=True,
      fc=lambda: f'={V("is_dda")}-{V("d_acl")}', e26=e26f('cf_dda', lambda: f'{QEc("is_dda")}-{QEc("d_acl")}'))
    S('cf_nfa', '  Nuclear fuel amortization', 'line', 'm1', data='cf_nfa', flow=True, fc=lambda: f'={V("is_nfa")}', e26=e26f('cf_nfa', lambda: QEc('is_nfa')))
    S('cf_ndt', '  Nuclear decommissioning trust funds (gain) loss, net', 'line', 'm1', data='cf_ndt', flow=True, fc=lambda: f'=-{V("is_ndt")}', e26=e26f('cf_ndt', lambda: f'-{QEc("is_ndt")}'))
    S('cf_def', '  Deferred income taxes', 'line', 'm1', data='cf_def', flow=True, e26=e26f('cf_def', lambda: f'{QEc("is_tax")}+{QEc("f_tax")}'),
      ae=lambda: f'={V("is_tax")}+{V("f_tax")}', note='Forecast = income tax expense − income taxes paid (Adjusted FCF line).')
    S('cf_sbc', '  Stock-based compensation', 'line', 'm1', data='cf_sbc', flow=True, fc=lambda: f'={V("d_sbc")}', e26=e26f('cf_sbc', lambda: QEc('d_sbc')),
      note='Shown separately from the FY2025 10-K (within other items before). Forecast awards are assumed equity-settled.')
    S('cf_ncoth', '  Gains on asset sales, impairments, restructuring & reorganization items; accretion of the capacity-monetization discount (forecast)', 'line', 'm1',
      data='cf_ncoth', flow=True, e26=lambda: f'={ACT("cf_ncoth")}+{V("dco_acc")}', ae=lambda: f'={V("dco_acc")}')
    S('cf_wc', '  Working capital & other operating items, net (derived)', 'line', 'm1', data='cf_wc', flow=True,
      e26=lambda: (f'={ACT("cf_wc")}-({V("bs_ar")}-{B1("bs_ar")})-({V("bs_inv")}-{B1("bs_inv")})+({V("bs_ap")}-{B1("bs_ap")})+({V("bs_accint")}-{B1("bs_accint")})'
                   f'+({V("bs_ocl")}-{B1("bs_ocl")})+({V("bs_pension")}-{B1("bs_pension")})'),
      ae=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_inv")}-{P("bs_inv")})+({V("bs_ap")}-{P("bs_ap")})+({V("bs_accint")}-{P("bs_accint")})'
                  f'+({V("bs_ocl")}-{P("bs_ocl")})+({V("bs_pension")}-{P("bs_pension")})'),
      note=('History: net cash from operations − the lines above (includes other non-cash items, collateral, the $500m cash settlement of stock awards in 2026 and pension contributions). '
            'Forecast linked to the balance sheet: −Δ(receivables, inventory) + Δ(payables, accrued interest, other current liabilities, pension obligations).'))
    S('cf_cfo', 'Net cash provided by (used in) operating activities', 'line_b', 'm1', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Property, plant and equipment expenditures', 'line', 'm1', data='cf_capex', flow=True,
      e26=lambda: f'={ACT("cf_capex")}+({QEc("f_capex")}-{V("cf_nfuel")}+{ACT("cf_nfuel")})-{PT("pt_gcapex")}',
      ae=lambda: f'={V("f_capex")}-{V("cf_nfuel")}-{V("capex_g")}',
      note='Forecast = capital expenditures, net of the Adjusted FCF definition (which include nuclear fuel) − nuclear fuel − growth / development / conversion capex (input below).')
    S('cf_nfuel', 'Nuclear fuel expenditures', 'line', 'm1', data='cf_nfuel', flow=True, e26=lambda: f'={ACT("cf_nfuel")}-{PT("pt_nfuel")}', ae_in=yr(V0['nfuel']))
    S('cf_ndtinv', 'Nuclear decommissioning trust funds investment purchases, net of sale proceeds', 'line', 'm1', data='cf_ndt_inv', flow=True, e26=lambda: f'={ACT("cf_ndtinv")}', ae_in=0.0)
    S('cf_acq', 'Acquisitions, net of cash acquired (Freedom & Guernsey Nov-2025; Cornerstone Jun-2026)', 'line', 'm1', data='cf_acq', flow=True, e26=lambda: f'={ACT("cf_acq")}', ae_in=0.0,
      note='No future acquisitions are assumed (no M&A lever: Talen\'s deals are large, discrete plant portfolios; capital allocation is benchmarked against buybacks).')
    S('cf_proc', 'Proceeds from the sale of assets', 'line', 'm1', data='cf_proceeds', flow=True, e26=lambda: f'={ACT("cf_proc")}', ae_in=0.0)
    S('cf_oinv', 'Other investing activities, net (derived)', 'line', 'm1', data='cf_oinv', flow=True, e26=lambda: f'={ACT("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Net cash provided by (used in) investing activities', 'line_b', 'm1', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_bb', 'Share repurchases', 'line', 'm1', data='cf_bb', flow=True, e26=lambda: f'={ACT("cf_bb")}-{PT("pt_asr")}-{PT("pt_bb")}', ae=lambda: f'=-{V("lev_bb")}',
      note='2026E: nine months actual + the $1.5bn accelerated share repurchase paid on 1-Oct-2026 + other Q4 repurchases (input). 2027E+ = leverage plug (surplus cash returned until net debt / Adjusted EBITDA reaches the target).')
    S('cf_debt', 'Net debt issuance / (repayment) (forecast; in debt & other financing historically)', 'line', 'm1',
      e26=lambda: f'={V("ds_total")}-{B1("ds_total")}', ae=lambda: f'={V("ds_net")}', note='Per the debt schedule: term-loan amortization, refinancing of maturities, revolver drawn or repaid to the minimum cash balance.')
    S('cf_dco', 'Capacity monetization: proceeds, net of discount / (repayments from PJM capacity settlements)', 'line', 'm1',
      e26=lambda: f'={V("dco_in")}-{V("dco_rep")}', ae=lambda: f'={V("dco_in")}-{V("dco_rep")}',
      note='1-Oct-2026: $1.5bn advanced less a $157m discount. Repaid by PJM directly to the counterparty from Jun-2027 to May-2029; shown here as a financing outflow against capacity revenue recognised in operations (model presentation).')
    S('cf_ofin', 'Debt & other financing, net (derived historically)', 'line', 'm1', data='cf_ofin', flow=True, e26=lambda: f'={ACT("cf_ofin")}', ae_in=0.0)
    S('cf_cff', 'Net cash provided by (used in) financing activities', 'line_b', 'm1', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_bb")}:{V("cf_ofin")})')
    S('cf_net', 'Net increase (decrease) in cash and restricted cash', 'line', 'm1', data='cf_net', flow=True, fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}')
    S('cf_beg', 'Cash and restricted cash — beginning of period', 'line', 'm1', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash and restricted cash — end of period', 'line_b', 'm1', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: CFO + CFI + CFF = change in cash; beginning + change = ending (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}-{V("cf_end")})<=0.6,0,ROUND({V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}-{V("cf_end")},1)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")})<=0.15,0,ROUND(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")},1)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Adjusted Free Cash Flow (company definition; reconciliation above)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("f_fcf")}),{V("f_fcf")},"")')
    S('fcf_g', '  Adjusted FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  Adjusted FCF % of energy and capacity revenues', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("fcf")}),IFERROR({V("fcf")}/({V("is_en")}+{V("is_cap")}),""),"")')
    S('fcf_ps', '  Adjusted FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_gaap', '  CFO − PP&E and nuclear fuel expenditures (GAAP-basis free cash flow, model memo)', 'line', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")}+{V("cf_nfuel")},"")')
    S('capex_h', 'Capex', 'sub', 'gen')
    S('capex_g', '  Growth, development & conversion capex outside the Adjusted FCF definition (input; positive = spend)', 'driver', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("cf_capex")}),ISNUMBER({V("f_capex")})),-({V("cf_capex")}+{V("cf_nfuel")})+{V("f_capex")},"")',
      e26=lambda: f'=-({V("cf_capex")}+{V("cf_nfuel")})+{V("f_capex")}', ae_in=yr(V0['gcapex']), note=V0['gcapex_note'])
    S('capex_dep', '  PP&E + nuclear fuel expenditures / (D&A + nuclear fuel amortization) (x)', 'line', 'x2',
      all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-({V("cf_capex")}+{V("cf_nfuel")})/({V("is_dda")}+{V("is_nfa")}),""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E = Q4 from shares outstanding at 30-Sep-2026 (ASR shares retired 1-Oct-2026); 2027E+ buybacks via the leverage plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = Q4, incl. the $1.5bn ASR)', 'line', 'm', e26=lambda: f'={PT("pt_asr")}+{PT("pt_bb")}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Shares repurchased (m; 2026E = ASR initial delivery + other Q4; 2027E incl. the ASR final settlement)', 'line', 'm2',
      e26=lambda: f'={PT("pt_asr_sh")}+IFERROR({PT("pt_bb")}/{V("bb_px")},0)',
      ae=lambda: (f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)+MAX(0,{PT("pt_asr")}/{V("bb_px", E26)}-{PT("pt_asr_sh")})' if Y27() else f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)'),
      note='ASR: 3,811,460 shares (80% of $1.5bn at $314.84) retired on 1-Oct-2026; the balance (total = $1.5bn ÷ average VWAP, approximated by the share-price input) is delivered at final settlement by Q1-2027 for no further cash.')
    S('bb_iss', '  Shares issued under equity plans (m)', 'driver', 'm2', e26_in=0.0, ae_in=V0['iss_ae'])
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from shares issued and outstanding at 30-Sep-2026 (Q3-26 10-Q balance sheet).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since Q4/26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET (condensed)', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Sep-2026 balance sheet + Q4 flows; 2027E+ from prior year end. Derivative balances are held flat (no mark-to-market forecast)')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents, incl. restricted cash', 'line', 'm1', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}')
    S('bs_ar', '  Accounts receivable', 'line', 'm1', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_inv', '  Inventory, net (fuel, materials & supplies)', 'line', 'm1', data='bs_inv', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_invp")}')
    S('bs_der_a', '  Derivative instruments (current + noncurrent)', 'line', 'm1', data='bs_der_a', bs=True, e26=lambda: f'={B1("bs_der_a")}', ae=lambda: f'={P("bs_der_a")}')
    S('bs_oca', '  Other current assets (incl. assets held for sale)', 'line', 'm1', data='bs_oca', bs=True, e26=lambda: f'={B1("bs_oca")}', ae=lambda: f'={P("bs_oca")}')
    S('bs_ppe', '  Property, plant and equipment, net (incl. nuclear fuel)', 'line', 'm1', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-({V("cf_capex")}-{ACT("cf_capex")})-({V("cf_nfuel")}-{ACT("cf_nfuel")})-{QEc("is_dda")}-{QEc("is_nfa")}',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("cf_nfuel")}-{V("is_dda")}-{V("is_nfa")}',
      note='Roll-forward: prior − capex and nuclear fuel expenditures (negative cash flows) − D&A − nuclear fuel amortization (ARO accretion is treated as depreciation; simplification).')
    S('bs_ndt', '  Nuclear decommissioning trust funds', 'line', 'm1', data='bs_ndt', bs=True, e26=lambda: f'={B1("bs_ndt")}+{QEc("is_ndt")}', ae=lambda: f'={P("bs_ndt")}+{V("is_ndt")}')
    S('bs_onca', '  Other noncurrent assets', 'line', 'm1', data='bs_onca', bs=True, e26=lambda: f'={B1("bs_onca")}', ae=lambda: f'={P("bs_onca")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_onca")}),"")')
    S('bs_l', "LIABILITIES AND EQUITY", 'sub', 'gen')
    S('bs_ap', '  Accounts payable and other accrued liabilities', 'line', 'm1', data='bs_ap', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_app")}')
    S('bs_accint', '  Accrued interest', 'line', 'm1', data='bs_accint', bs=True, e26=lambda: f'={PT("pt_accint")}', ae=lambda: f'={P("bs_accint")}*IFERROR(({V("is_int")}-{V("dco_acc")})/({P("is_int")}-{P("dco_acc")}),1)',
      note='2026E: year-end level after the November coupons (input). 2027E+: grows with cash interest expense.')
    S('bs_der_l', '  Derivative instruments (current + noncurrent)', 'line', 'm1', data='bs_der_l', bs=True, e26=lambda: f'={B1("bs_der_l")}', ae=lambda: f'={P("bs_der_l")}')
    S('bs_ocl', '  Other current liabilities (incl. stock-based compensation liabilities, liabilities held for sale)', 'line', 'm1', data='bs_ocl', bs=True,
      e26=lambda: f'={B1("bs_ocl")}', ae=lambda: f'={P("bs_ocl")}')
    S('bs_std', '  Revolving credit facility & long-term debt due within one year', 'line', 'm1', data='debt_st', bs=True, fc=lambda: f'={V("ds_rev")}+MIN({V("ds_notes")},{V("ds_mat")})')
    S('bs_ltd', '  Long-term debt', 'line', 'm1', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_std")}')
    S('bs_dco', '  Deferred capacity obligation (PJM capacity monetization, from 1-Oct-2026)', 'line', 'm1', e26=lambda: f'={V("dco_bal")}', ae=lambda: f'={V("dco_bal")}',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ap")}),0,"")')
    S('bs_pension', '  Postretirement benefit obligations', 'line', 'm1', data='bs_pension', bs=True,
      e26=lambda: f'=MAX(0,{B1("bs_pension")}+{QEc("f_pen")})', ae=lambda: f'=MAX(0,{P("bs_pension")}+{V("f_pen")})', note='Reduced by pension contributions (Adjusted FCF line); net periodic cost and remeasurements not forecast.')
    S('bs_aro', '  Asset retirement obligations and accrued environmental costs', 'line', 'm1', data='bs_aro', bs=True, e26=lambda: f'={B1("bs_aro")}', ae=lambda: f'={P("bs_aro")}')
    S('bs_dtl', '  Deferred income taxes', 'line', 'm1', data='bs_dtl', bs=True, e26=lambda: f'={B1("bs_dtl")}+({V("cf_def")}-{ACT("cf_def")})', ae=lambda: f'={P("bs_dtl")}+{V("cf_def")}')
    S('bs_acl', '  Acquired contract liabilities (fuel supply and capacity contracts)', 'line', 'm1', data='bs_acl', bs=True,
      e26=lambda: f'={B1("bs_acl")}-{QEc("d_acl")}', ae=lambda: f'={P("bs_acl")}-{V("d_acl")}')
    S('bs_oncl', '  Other noncurrent liabilities (incl. liabilities subject to compromise at 31-Dec-2022)', 'line', 'm1', data='bs_oncl', bs=True, e26=lambda: f'={B1("bs_oncl")}', ae=lambda: f'={P("bs_oncl")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_ap")}:{V("bs_oncl")}),"")')
    S('bs_eq', "  Stockholders' equity (member's equity before 17-May-2023)", 'line', 'm1', data='bs_eq', bs=True,
      e26=lambda: f'={B1("bs_eq")}+{QEc("is_ni")}+({V("cf_bb")}-{ACT("cf_bb")})+{QEc("d_sbc")}',
      ae=lambda: f'={P("bs_eq")}+{V("is_ni")}+{V("cf_bb")}+{V("cf_sbc")}',
      note='+ net income attributable − repurchases (shares are retired) + stock-based compensation (other comprehensive income held flat).')
    S('bs_nci', '  Noncontrolling interests', 'line', 'm1', data='bs_nci', bs=True, e26=lambda: f'={B1("bs_nci")}', ae=lambda: f'={P("bs_nci")}+{V("is_nci")}')
    S('bs_teq', 'Total equity', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")}+N({V("bs_nci")}),"")')
    S('bs_tle', "TOTAL LIABILITIES AND EQUITY", 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=0.6,0,ROUND({V("bs_ta")}-{V("bs_tle")},1)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm1', hist=lambda: tol(V('bs_ta'), V('bs_ta_pub')))
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm1', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash incl. restricted cash vs cash-flow ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}-{V("cf_end")})<=0.6,0,ROUND({V("bs_cash")}-{V("cf_end")},1)),"")')
    S('bs_rcash', '  Memo: of which restricted cash and cash equivalents', 'memo', 'm1', data='bs_rcash', bs=True)
    S('bs_shares', '  Memo: shares issued and outstanding at period end (m)', 'memo', 'm1', data='bs_shares', bs=True, e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input); ratios on energy and capacity revenues (unrealized derivative results excluded)')
    S('wc_rev', '  Energy and capacity revenues — annualised (quarters × 4)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_en")}),({V("is_en")}+{V("is_cap")})*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — receivables / revenues × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_invp', '  Inventory % of revenues', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_inv")}/{V("wc_rev")},"")', e26_in=V0['wc']['inv'], ae_in=V0['wc']['inv'])
    S('wc_app', '  Accounts payable & accrued liabilities % of revenues', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_rev")},"")', e26_in=V0['wc']['ap'], ae_in=V0['wc']['ap'],
      note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables + inventory − payables − accrued interest − other current liabilities)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_inv")}-{V("bs_ap")}-{V("bs_accint")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of revenues', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm1', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppa_h', 'Acquisitions — consideration & purchase-price allocation (closing-period column; provisional)', 'sub', 'gen')
    for k, lab in [('cons', 'Consideration (cash and shares), net of cash acquired'),
                   ('ca', 'Current assets acquired (receivables, inventory, other; excl. cash)'), ('ppe', 'Property, plant & equipment'),
                   ('intang', 'Intangible assets'), ('gw', 'Goodwill (none recognised)'),
                   ('onca', 'Other noncurrent assets'), ('cl', 'Current liabilities assumed (payables, current derivatives)'), ('debt', 'Debt assumed'),
                   ('ncl', 'Noncurrent liabilities assumed (acquired contract liabilities, deferred taxes, derivatives, ARO, other)')]:
        S(f'ppa_{k}', f'  {lab}', 'sched', 'm1', data=f'ppa_{k}', ppa=True)
    S('ppa_chk', '  Check: assets acquired − liabilities assumed − consideration (should be 0)', 'check', 'm1',
      hist=lambda: (f'=IF(ISNUMBER({V("ppa_cons")}),ROUND(N({V("ppa_ca")})+N({V("ppa_ppe")})+N({V("ppa_intang")})+N({V("ppa_gw")})+N({V("ppa_onca")})'
                    f'-N({V("ppa_cl")})-N({V("ppa_debt")})-N({V("ppa_ncl")})-{V("ppa_cons")},1),"")'))
    S('ppa_names', '  Deal closed in the period', 'text', 'gen', data='ppa_names', ppa=True, textdata=True)
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; RSUs / PSUs)', 'sched', 'm1', ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.08)
    S('ds_h', 'Debt schedule (term loans amortize 1% a year; notes refinanced at maturity; revolver drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (revolver + current portion + long-term debt; carrying value)', 'sched', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_rev")}', note=MAN['debt']['at_2026_09_30'])
    S('ds_notes', '  Term loans, unsecured notes & PEDFA bonds (long-term debt incl. current portion, carrying value)', 'sched', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")}-N({V("ds_rev")}),"")',
      e26=lambda: f'={B1("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}-{V("ds_swp")}')
    S('ds_iss', '  New notes issued (input)', 'sched', 'm1', e26_in=0.0, ae_in=yr(V0['iss_notes']), note='2031E: the $1.5bn 6.125% notes due 2031 and the TLB-2 balance are assumed refinanced (assumption).')
    S('ds_repay', '  Term-loan amortization and maturities repaid (input)', 'sched', 'm1', e26_in=V0['repay'][FYC], ae_in=yr(V0['repay']), note=V0['repay_note'])
    S('ds_mat', '  Maturities in the following year (current portion)', 'sched', 'm1', e26_in=V0['mat'][FYC], ae_in=yr(V0['mat']))
    S('ds_pre', '  Cash before revolver draws / repayments', 'sched', 'm1',
      e26=lambda: (f'={B1("bs_cash")}+({V("cf_cfo")}-{ACT("cf_cfo")})+({V("cf_cfi")}-{ACT("cf_cfi")})+({V("cf_bb")}-{ACT("cf_bb")})+{V("cf_dco")}'
                   f'+({V("cf_ofin")}-{ACT("cf_ofin")})-{V("ds_repay")}+{V("ds_iss")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_bb")}+{V("cf_dco")}+{V("cf_ofin")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_min', '  Minimum cash balance (incl. restricted cash)', 'sched', 'm1', e26_in=V0['min_cash'], ae_in=V0['min_cash'], note=V0['min_cash_note'])
    S('ds_rev', '  Revolving credit facility / incremental borrowings (period end)', 'sched', 'm1', data='bs_rcf',
      e26=lambda: f'=MAX(0,{B1("ds_rev")}+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_rev")}+{V("ds_min")}-{V("ds_pre")})',
      note='$1.35bn RCF (matures Dec-2029; undrawn at 30-Sep-2026). Shortfalls below the minimum cash balance are drawn; surplus repays the balance. Buybacks to the leverage target are debt-funded: any balance above the $1.35bn commitment stands for incremental term debt / notes (financing assumption; see the headroom memo).')
    S('ds_fixed', '  Of which not prepayable: unsecured notes and PEDFA bonds (carrying value, input)', 'sched', 'm1', ae_in=V0['ds_fixed'],
      note='Unsecured notes $6,690m and PEDFA bonds $131m less unamortized costs; the balance of long-term debt is the prepayable term loans (TLB-1 / TLB-2 / TLB-3, $2,868m at 30-Sep-2026).')
    S('ds_swp', '  Term-loan prepayment from surplus cash (cash sweep after buybacks)', 'sched', 'm1',
      ae=lambda: f'=MAX(0,MIN({P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}-{V("ds_fixed")},{V("ds_pre")}-{P("ds_rev")}-{V("ds_min")}))',
      note='Cash above the minimum balance (after scheduled repayments, buybacks to the leverage target and repayment of the revolver) prepays the term loans; nil while the leverage plug absorbs the surplus.')
    S('ds_head', '  Memo: revolver headroom vs the $1.35bn commitment (negative = would need other financing)', 'memo_calc', 'm1',
      e26=lambda: f'=1350-{V("ds_rev")}', ae=lambda: f'=1350-{V("ds_rev")}')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm1', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on opening long-term debt (carrying value) %', 'sched', 'pct', ae_in=V0['r_notes'], note=V0['r_notes_note'])
    S('ds_r_rev', '  Interest rate on opening revolver %', 'sched', 'pct', ae_in=0.055, note='RCF at Term SOFR + 1.50% after the May-2026 repricing (assumption ~5.5%).')
    S('ds_fees', '  Letter-of-credit / commitment fees and financing-cost amortization ($m)', 'sched', 'm1', ae_in=V0['fees'], note=V0['fees_note'])
    S('dco_h', 'PJM capacity monetization — deferred capacity obligation (1-Oct-2026; Q3-26 10-Q Note 3)', 'sub', 'gen')
    S('dco_in', '  Proceeds advanced, net of the $157m discount', 'sched', 'm1', e26_in=MAN['capacity']['monetization']['net'], ae_in=0.0, note=MAN['capacity']['monetization']['note'])
    S('dco_acc', '  Accretion of the discount (implied finance charge, in interest expense; effective-interest allocation — assumption)', 'sched', 'm1',
      e26_in=V0['dco_acc'][FYC], ae_in=yr(V0['dco_acc']), note=V0['dco_note'])
    S('dco_rep', '  Repayments from PJM capacity settlements (10-Q schedule)', 'sched', 'm1', e26_in=0.0, ae_in=yr(V0['dco_rep']))
    S('dco_bal', '  Deferred capacity obligation (period end)', 'sched', 'm1', e26=lambda: f'={V("dco_in")}+{V("dco_acc")}-{V("dco_rep")}',
      ae=lambda: f'={P("dco_bal")}+{V("dco_in")}+{V("dco_acc")}-{V("dco_rep")}')
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / Adjusted EBITDA, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / Adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end; incl. the deferred capacity obligation)', 'sched', 'm1',
      ae=lambda: f'={P("lv_nd")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_ofin")}+{V("dco_acc")}')
    S('lev_dco', '  Count the deferred capacity obligation in the leverage target? (1 = yes, 0 = no; input)', 'sched', 'gen', ae_in=0,
      note=('Assumption: 0 — the obligation is repaid by PJM from already-cleared capacity revenues and the company funded the ASR with it while restating its 3.5x net leverage target; '
            'set to 1 to delever on the wider definition first. Valuation net debt (EV bridge, DCF) always includes the obligation.'))
    S('lev_tgt', '  Target net debt = target leverage × Adjusted EBITDA (+ the deferred capacity obligation when it is not counted)', 'sched', 'm1',
      ae=lambda: f'={V("lev_min")}*{V("r_adj")}+(1-{V("lev_dco")})*{V("dco_bal")}')
    S('lev_bb', '  Share repurchases: plug to target leverage', 'sched', 'm1', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash beyond the leverage target is returned via buybacks; feeds the cash-flow repurchase line. $1.5bn remained under the repurchase program (to Dec-2028) after the ASR.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  D&A + nuclear fuel amortization % of energy and capacity revenues', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("is_dda_m")}),IFERROR({V("is_dda_m")}/({V("is_en")}+{V("is_cap")}),""),"")')
    S('hr_int', '  Interest expense ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted EBIT less stock compensation, restructuring and acquisition costs)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT less stock compensation, restructuring & acquisition costs', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("r_ebit")}-{V("r_cash")},"n/a")')
    S('ra_t', 'Tax rate (model assumption for NOPAT)', 'line', 'pct', ann=True, all=lambda: f'={V0["adj_rate"]}')
    S('ra_nopat', 'NOPAT = Adjusted EBIT (after excluded cash costs) × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity', 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),{V("bs_teq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt + deferred capacity obligation − cash (incl. restricted)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ds_total")}+N({V("bs_dco")})-{V("bs_cash")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT (after excluded cash costs) / Operating revenues', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Operating revenues / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm1', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Nuclear decommissioning trust funds and derivative assets (non-operating)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-({V("bs_ndt")}+{V("bs_der_a")}),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (payables, accrued interest, other current)', 'line', 'm1', ann=True,
      all=lambda: f'=IFERROR(-({V("bs_ap")}+{V("bs_accint")}+{V("bs_ocl")}),"n/a")')
    S('rn_nta', '  = Net tangible operating assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income attributable', 'line', 'm1', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Stockholders' equity", 'line', 'm1', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt + deferred capacity obligation − cash', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA', 'line', 'm1', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / Adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_gx', 'Net debt excl. the deferred capacity obligation / Adjusted EBITDA (x)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR(({V("lv_nd")}-N({V("bs_dco")}))/{V("lv_eb")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt incl. the deferred capacity obligation (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interests (USDm)', 'line', 'm', e26=lambda: f'={V("bs_nci")}', ae=lambda: f'={V("bs_nci")}')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Operating revenues', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted EBIT (model)', lambda: f'=IFERROR({V("v_ev")}/{V("r_ebit")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_evgw', '  EV per MWh generated ($/MWh)', lambda: f'=IFERROR({V("v_ev")}/{V("gen")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS, model definition)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  Adjusted FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_pfcf', '  Price / Adjusted FCF per share', lambda: f'=IFERROR({V("v_px")}/{V("fcf_ps")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy',) else ('m2' if k == 'v_evgw' else 'x'), e26=f, ae=f)
