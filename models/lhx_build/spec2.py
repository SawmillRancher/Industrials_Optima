"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, QEc, B1, tol

def build_spec2(V0):
    S = add
    def e26f(key, q4):          # FY2026E flow = 9M actual (Q1-Q3/26) + Q4/26E estimate
        return lambda: f'={ACT(key)}+{q4()}'
    ann = lambda: 4 if CTX.col.q else (2 if CTX.col.tp else 1)      # annualisation factor of the column
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 9M actual + Q4 estimate; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net income', 'line', 'm', data='cf_ni', flow=True, fc=lambda: f'={V("is_nitot")}', e26=e26f('cf_ni', lambda: QEc('is_nitot')))
    S('cf_adj', 'Non-cash items:', 'sub', 'gen')
    S('cf_dda', '  Depreciation & amortization', 'line', 'm', data='cf_da', flow=True, fc=lambda: f'={V("is_dda")}', e26=e26f('cf_dda', lambda: QEc('is_dda')))
    S('cf_sbc', '  Share-based compensation & share-based matching contributions', 'line', 'm', data='cf_sbc', flow=True, fc=lambda: f'={V("is_sbc")}',
      e26=e26f('cf_sbc', lambda: QEc('is_sbc')))
    S('cf_def', '  Deferred income taxes', 'line', 'm', data='cf_def', flow=True, e26=lambda: f'={ACT("cf_def")}+{V0["def_q4"]}', ae_in=V0['def_ae'],
      note='Forecast input (2025–26 benefit from the restored expensing of domestic R&D and bonus depreciation; normalising).')
    S('cf_pens', '  Pension: net periodic benefit income, net of contributions (non-cash income reversed)', 'line', 'm', data='cf_pens', flow=True,
      e26=lambda: f'={ACT("cf_pens")}-{QEc("is_pens")}*{V0["pens_cf_ratio"]}', ae=lambda: f'=-{V("is_pens")}*{V0["pens_cf_ratio"]}',
      note=V0['pens_cf_note'])
    S('cf_wc', '  Working capital & other operating items, net (derived)', 'line', 'm', data='cf_wc', flow=True,
      e26=lambda: f'={PT("pt_cfo")}-{V("cf_ni")}-{V("cf_dda")}-{V("cf_sbc")}-{V("cf_def")}-{V("cf_pens")}',
      ae=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_ca")}-{P("bs_ca")})-({V("bs_inv")}-{P("bs_inv")})-({V("bs_oca")}-{P("bs_oca")})'
                  f'+({V("bs_ap")}-{P("bs_ap")})+({V("bs_cl")}-{P("bs_cl")})+({V("bs_ocl")}-{P("bs_ocl")})'),
      note=('History: net cash from operations − the lines above (receivables, contract assets / liabilities, inventories, payables, taxes, gains and other items). '
            '2026E: solved so that FY26 cash from operations = the $3.6bn guidance (contract assets are the balance-sheet offset). '
            '2027E+: linked to the balance sheet: −Δ(receivables, contract assets, inventories, other current assets) + Δ(payables, contract liabilities, other current liabilities).'))
    S('cf_cfo', 'Net cash provided by operating activities', 'line_b', 'm', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Capital expenditures (additions of property, plant & equipment)', 'line', 'm', data='cf_capex', flow=True,
      e26=lambda: f'=-{PT("pt_capex")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}', note=V0['capex_note'])
    S('cf_acq', 'Business acquisitions, net of cash acquired', 'line', 'm', data='cf_acq', flow=True,
      e26=lambda: f'={ACT("cf_acq")}', ae=lambda: f'=-{V("m_spend")}', note='2027E+: M&A lever.')
    S('cf_divest', 'Proceeds from sales of businesses, net', 'line', 'm', data='cf_divest', flow=True, e26=lambda: f'={ACT("cf_divest")}', ae_in=0.0,
      note='2026E = 9M actual (Space Technology disposal group, 60% sold 3-Aug-2026: $539m). No further divestitures assumed.')
    S('cf_oinv', 'Other investing activities, net (PP&E disposals, short-term investments, other; derived)', 'line', 'm', data='cf_oinv', flow=True,
      e26=lambda: f'={ACT("cf_oinv")}', ae_in=0.0, note='Q3-26 includes the purchase of $550m of short-term investments (held flat in the forecast; counted as cash in net debt).')
    S('cf_cfi', 'Net cash provided by (used in) investing activities', 'line_b', 'm', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_bb', 'Repurchases of common stock', 'line', 'm', data='cf_bb', flow=True, e26=lambda: f'={ACT("cf_bb")}-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note=V0['bb_note'])
    S('cf_div', 'Cash dividends paid', 'line', 'm', data='cf_div', flow=True,
      e26=lambda: f'={ACT("cf_div")}-{QEc("dps")}*{QEc("sh_basic")}', ae=lambda: f'=-{V("dps")}*{V("bb_beg")}',
      note='2027E+: dividend per share × beginning shares (not circular with the buyback plug).')
    S('cf_debt', 'Net debt issuance / (repayment) (long-term debt and commercial paper)', 'line', 'm', data='cf_debt', flow=True,
      e26=lambda: f'={V("ds_total")}-{B1("ds_total")}+{ACT("cf_debt")}', ae=lambda: f'={V("ds_net")}',
      note='Per the debt schedule: notes repaid at maturity or refinanced (input); commercial paper drawn or repaid to the minimum cash balance.')
    S('cf_ofin', 'Other financing, net (stock options, subsidiary preferred stock issuance in Q2-26, tax withholding; derived)', 'line', 'm', data='cf_ofin', flow=True,
      e26=lambda: f'={ACT("cf_ofin")}', ae_in=V0['ofin_ae'])
    S('cf_cff', 'Net cash provided by (used in) financing activities', 'line_b', 'm', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_bb")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of exchange rate changes on cash', 'line', 'm', data='cf_fx', flow=True, e26=lambda: f'={ACT("cf_fx")}', ae_in=0.0)
    S('cf_net', 'Net change in cash and cash equivalents', 'line', 'm', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")}),"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}')
    S('cf_beg', 'Cash — beginning of period', 'line', 'm', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period', 'line_b', 'm', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: CFO + CFI + CFF + FX = change in cash (should be 0; ±1 rounding)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),{tol(V("cf_beg") + "+" + V("cf_net"), V("cf_end"), 1.01)},"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),{tol("SUM(" + V("cf_ni") + ":" + V("cf_wc") + ")", V("cf_cfo"), 0.6)},"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (company definition from Q3-26: CFO − capital expenditures)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")},"")',
      note='Model definition held constant across periods; the company\'s (adjusted) free cash flow definitions of each period are in the two rows below.')
    S('fcf_pub', '  Company-published free cash flow / adjusted free cash flow (definition in force)', 'memo', 'm', data='fcf_pub', flow=True)
    S('fcf_diff', '  Definition difference: company-published − model (PP&E disposal proceeds, cash merger / LHX NeXt / pension items excluded by the company)', 'memo_calc', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("fcf_pub")}),ISNUMBER({V("fcf")})),{V("fcf_pub")}-{V("fcf")},"n/p")')
    S('fcf_def', '  Definition / basis (company free cash flow definition)', 'text', 'gen')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of revenue', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / non-GAAP net income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note=V0['capex_pct_note'])
    S('capex_dep', '  Capex / depreciation & other amortization (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("d_dep")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E = Q4 from shares outstanding at 2-Oct-2026; 2027E+ buybacks via the leverage plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = Q4)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans & defined contribution matching (m)', 'driver', 'm2', e26_in=V0['iss_q4'], ae_in=V0['iss_ae'], note=V0['iss_note'])
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from shares issued and outstanding at 2-Oct-2026 (Q3-26 10-Q).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since Q4/26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET (condensed, as in the releases)', 'section',
      note='BS FORECAST — 2026E rolled forward from the 2-Oct-2026 balance sheet + Q4 flows; 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}')
    S('bs_stinv', '  Short-term investments (from Q3-26)', 'line', 'm', data='bs_stinv', bs=True, e26=lambda: f'={B1("bs_stinv")}', ae=lambda: f'={P("bs_stinv")}')
    S('bs_ar', '  Receivables, net', 'line', 'm', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_ca', '  Contract assets (unbilled)', 'line', 'm', data='bs_ca', bs=True,
      e26=lambda: (f'={B1("bs_ca")}-(({V("cf_wc")}-{ACT("cf_wc")})+({V("bs_ar")}-{B1("bs_ar")})+({V("bs_inv")}-{B1("bs_inv")})+({V("bs_oca")}-{B1("bs_oca")})'
                   f'-({V("bs_ap")}-{B1("bs_ap")})-({V("bs_cl")}-{B1("bs_cl")})-({V("bs_ocl")}-{B1("bs_ocl")}))'),
      ae=lambda: f'={V("wc_rev")}*{V("wc_cad")}/365',
      note='2026E: balance-sheet offset of the cash-from-operations calibration (Q4 working-capital inflow not explained by the other lines). 2027E+: days of revenue.')
    S('bs_inv', '  Inventories, net', 'line', 'm', data='bs_inv', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dio")}/365')
    S('bs_oca', '  Other current assets incl. assets held for sale (derived)', 'line', 'm', data='bs_oca', bs=True, e26=lambda: f'={B1("bs_oca")}', ae=lambda: f'={P("bs_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_ppe', '  Property, plant & equipment, net', 'line', 'm', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-({V("cf_capex")}-{ACT("cf_capex")})-{QEc("d_dep")}*{V0["ppe_dep_share"]}',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("d_dep")}*{V0["ppe_dep_share"]}+{V("m_spend")}*{V("m_ppe")}',
      note=V0['ppe_note'])
    S('bs_gw', '  Goodwill', 'line', 'm', data='bs_gw', bs=True, e26=lambda: f'={B1("bs_gw")}', ae=lambda: f'={P("bs_gw")}+{V("m_spend")}*(1-{V("m_ppe")}-{V("m_intp")})')
    S('bs_int', '  Intangible assets, net', 'line', 'm', data='bs_int', bs=True,
      e26=lambda: f'={B1("bs_int")}-{QEc("d_amort")}+{QEc("seg_other")}', ae=lambda: f'={P("bs_int")}-{V("d_amort")}+{V("seg_other")}+{V("m_spend")}*{V("m_intp")}',
      note='Roll-forward: prior − acquisition-related amortization − program investment asset amortization (a reduction of revenue) + acquired intangibles (M&A lever).')
    S('bs_onca', '  Deferred income taxes & other non-current assets (pension assets, lease right-of-use, investments; derived)', 'line', 'm', data='bs_onca', bs=True,
      e26=lambda: f'={B1("bs_onca")}-({V("cf_pens")}-{ACT("cf_pens")})-{QEc("d_dep")}*(1-{V0["ppe_dep_share"]})',
      ae=lambda: f'={P("bs_onca")}-{V("cf_pens")}-{V("d_dep")}*(1-{V0["ppe_dep_share"]})',
      note='Forecast: + non-cash pension income (accretes the net pension asset; plans overfunded, no material contributions) − other amortization (capitalized software and other assets).')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_ppe")}:{V("bs_onca")}),"")')
    S('bs_l', 'LIABILITIES, MEZZANINE EQUITY AND EQUITY', 'sub', 'gen')
    S('bs_std', '  Short-term debt & current portion of long-term debt', 'line', 'm', data='bs_std', bs=True, fc=lambda: f'={V("ds_cp")}+MIN({V("ds_notes")},{V("ds_mat")})')
    S('bs_ap', '  Accounts payable', 'line', 'm', data='bs_ap', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dpo")}/365')
    S('bs_cl', '  Contract liabilities (advance payments & unearned income)', 'line', 'm', data='bs_cl', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_clp")}')
    S('bs_ocl', '  Compensation & benefits, other current liabilities incl. liabilities held for sale (derived)', 'line', 'm', data='bs_ocl', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_oclp")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_std")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term debt, net (less current portion)', 'line', 'm', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_std")}')
    S('bs_ol', '  Deferred income taxes, defined benefit plans & other non-current liabilities (incl. subsidiary preferred-stock derivatives; derived)', 'line', 'm', data='bs_ol', bs=True,
      e26=lambda: f'={B1("bs_ol")}+({V("cf_def")}-{ACT("cf_def")})', ae=lambda: f'={P("bs_ol")}+{V("cf_def")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_ol")}),"")')
    S('bs_mezz', '  Mezzanine equity: redeemable subsidiary Series A convertible preferred stock (DoW, Apr-2026)', 'line', 'm', data='bs_mezz', bs=True,
      e26=lambda: f'={B1("bs_mezz")}+{QEc("is_pref")}', ae=lambda: f'={P("bs_mezz")}+{V("is_pref")}', note=V0['mezz_note'])
    S('bs_eq', "  Shareholders' equity", 'line', 'm', data='bs_eq', bs=True,
      e26=lambda: (f'={B1("bs_eq")}+{QEc("is_ni")}-{QEc("is_pref")}+({V("cf_div")}-{ACT("cf_div")})+({V("cf_bb")}-{ACT("cf_bb")})+{QEc("d_sbc")}+({V("cf_ofin")}-{ACT("cf_ofin")})'),
      ae=lambda: f'={P("bs_eq")}+{V("is_ni")}-{V("is_pref")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_sbc")}+{V("cf_ofin")}',
      note='+ net income − deemed dividends on the subsidiary preferred stock − dividends − repurchases + share-based compensation + other financing (OCI / FX translation held flat).')
    S('bs_nci', '  Noncontrolling interests', 'line', 'm', data='bs_nci', bs=True, e26=lambda: f'={B1("bs_nci")}', ae=lambda: f'={P("bs_nci")}')
    S('bs_teq', 'Total equity', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")}+N({V("bs_nci")}),"")')
    S('bs_tle', 'TOTAL LIABILITIES, MEZZANINE EQUITY AND EQUITY', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+N({V("bs_mezz")})+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),{tol(V("bs_ta"), V("bs_tle"), 1.01)},"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),{tol(V("bs_ta"), V("bs_ta_pub"), 1.01)},"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash vs cash-flow ending cash (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),{tol(V("bs_cash") + "+N(" + V("bs_cash_adj") + ")", V("cf_end"), 1.01)},"")')
    S('bs_cash_adj', '  Memo: cash in the cash-flow statement but outside balance-sheet cash (held-for-sale / restricted cash)', 'memo', 'm', data='bs_cash_adj', bs=True)
    S('bs_shares', '  Memo: shares outstanding at period end (m)', 'memo', 'm1', data='bs_shares', bs=True, e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    S('bs_ncipref', '  Memo: noncontrolling interests + subsidiary preferred stock (mezzanine + conversion-feature & warrant liabilities)', 'memo', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),N({V("bs_nci")})+N({V("bs_mezz")})+N({V("bs_prefd")}),"")')
    S('bs_prefd', '  Memo: subsidiary preferred-stock conversion feature & warrants (derivative liabilities at fair value, inside other non-current liabilities)', 'memo', 'm',
      data='bs_prefd', bs=True, e26=lambda: f'={B1("bs_prefd")}', ae=lambda: f'={P("bs_prefd")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input; fiscal year-end levels)')
    S('wc_rev', '  Revenue — annualised (quarters × 4)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{ann()},"")')
    S('wc_cogs', '  Cost of revenue — annualised', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_cogs")}*{ann()},"")')
    S('wc_dso', '  DSO — receivables / revenue × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_cad', '  Contract-asset days — contract assets / revenue × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ca")}/{V("wc_rev")}*365,"")',
      e26=lambda: f'=IFERROR({V("bs_ca")}/{V("wc_rev")}*365,"")', ae=lambda: f'={V("wc_cad", E26)}',
      note='2026E: output of the cash-from-operations calibration; 2027E+: held at the 2026E level.')
    S('wc_dio', '  Inventory days — inventories / cost of revenue × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_inv")}/{V("wc_cogs")}*365,"")', e26_in=V0['wc']['dio'], ae_in=V0['wc']['dio'])
    S('wc_dpo', '  Payable days — payables / cost of revenue × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_cogs")}*365,"")', e26_in=V0['wc']['dpo'], ae_in=V0['wc']['dpo'])
    S('wc_clp', '  Contract liabilities % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_cl")}/{V("wc_rev")},"")', e26_in=V0['wc']['cl'], ae_in=V0['wc']['cl'])
    S('wc_oclp', '  Other current liabilities % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")',
      e26_in=V0['wc']['ocl'], ae_in=V0['wc']['ocl'], note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables + contract assets + inventories + other current assets − payables − contract liabilities − other current liabilities)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+N({V("bs_ca")})+{V("bs_inv")}+{V("bs_oca")}-{V("bs_ap")}-N({V("bs_cl")})-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppa_h', 'Acquisitions — consideration & purchase-price allocation (closing-period column)', 'sub', 'gen')
    for k, lab in [('cons', 'Consideration — net assets acquired (net of cash acquired)'),
                   ('ca', 'Current assets acquired (receivables, contract assets, inventories, other)'), ('ppe', 'Property, plant & equipment'),
                   ('intang', 'Intangible assets (customer relationships, technology, trade names)'), ('gw', 'Goodwill'),
                   ('onca', 'Other non-current assets'), ('cl', 'Current liabilities assumed'), ('debt', 'Debt assumed'),
                   ('ncl', 'Non-current liabilities assumed (deferred taxes, pensions, other)')]:
        S(f'ppa_{k}', f'  {lab}', 'sched', 'm', data=f'ppa_{k}', ppa=True)
    S('ppa_chk', '  Check: assets acquired − liabilities assumed − consideration (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: (f'=IF(ISNUMBER({V("ppa_cons")}),{tol("N(" + V("ppa_ca") + ")+N(" + V("ppa_ppe") + ")+N(" + V("ppa_intang") + ")+N(" + V("ppa_gw") + ")+N(" + V("ppa_onca") + ")-N(" + V("ppa_cl") + ")-N(" + V("ppa_debt") + ")-N(" + V("ppa_ncl") + ")", V("ppa_cons"), 1.01)},"")'))
    S('ppa_names', '  Deal closed in the period', 'text', 'gen', data='ppa_names', ppa=True, textdata=True)
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; options, RSUs & PSUs)', 'sched', 'm1', ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.08)
    S('ds_h', 'Debt schedule (fixed-rate notes repaid at maturity or refinanced; commercial paper drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (short-term debt + current portion + long-term debt)', 'sched', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_cp")}', note=V0['debt_note'])
    S('ds_notes', '  Long-term debt incl. current portion (fixed-rate notes, finance leases)', 'sched', 'm', data='debt_lt',
      e26=lambda: f'={B1("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_iss', '  New notes issued (input)', 'sched', 'm', e26_in=V0['iss_notes'][FYC], ae_in={y: V0['iss_notes'].get(y, 0.0) for y in range(FYC + 1, FYL + 1)},
      note=V0['iss_notes_note'])
    S('ds_repay', '  Notes repaid at maturity (input)', 'sched', 'm', e26_in=V0['repay'][FYC], ae_in={y: V0['repay'][y] for y in range(FYC + 1, FYL + 1)},
      note=V0['repay_note'])
    S('ds_mat', '  Maturities in the following fiscal year (current portion)', 'sched', 'm', e26_in=V0['mat'][FYC], ae_in={y: V0['mat'][y] for y in range(FYC + 1, FYL + 1)})
    S('ds_pre', '  Cash before commercial-paper draws / repayments (opening cash + CFO + CFI + buybacks, dividends, other financing + FX − notes repaid + issued)', 'sched', 'm',
      e26=lambda: (f'={B1("bs_cash")}+({V("cf_cfo")}-{ACT("cf_cfo")})+({V("cf_cfi")}-{ACT("cf_cfi")})+({V("cf_bb")}-{ACT("cf_bb")})+({V("cf_div")}-{ACT("cf_div")})'
                   f'+({V("cf_ofin")}-{ACT("cf_ofin")})+({V("cf_fx")}-{ACT("cf_fx")})-{V("ds_repay")}+{V("ds_iss")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_bb")}+{V("cf_div")}+{V("cf_ofin")}+{V("cf_fx")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_min', '  Minimum cash balance', 'sched', 'm', e26_in=V0['min_cash'], ae_in=V0['min_cash'], note=V0['min_cash_note'])
    S('ds_cp', '  Commercial paper / short-term debt (period end)', 'sched', 'm', data='debt_st',
      e26=lambda: f'=MAX(0,{B1("ds_cp")}+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_cp")}+{V("ds_min")}-{V("ds_pre")})',
      note='Commercial paper programme ($2.5bn, backed by the 2025 Five-Year Credit Facility to Feb-2030; nil outstanding at 2-Oct-2026). Shortfalls below the minimum cash balance are drawn; surplus repays it.')
    S('ds_head', '  Memo: commercial paper headroom vs the $2.5bn programme (negative = would need other financing)', 'memo_calc', 'm',
      e26=lambda: f'=2500-{V("ds_cp")}', ae=lambda: f'=2500-{V("ds_cp")}')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_debt', '  Interest rate on opening debt %', 'sched', 'pct', ae_in=V0['r_debt'], note=V0['r_debt_note'])
    S('ds_r_cash', '  Interest income yield on opening cash & short-term investments %', 'sched', 'pct', ae_in=V0['r_cash'], note=V0['r_cash_note'])
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / adjusted EBITDA, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end)', 'sched', 'm',
      ae=lambda: f'={P("ds_total")}-{P("cf_end")}-{P("bs_stinv")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_ofin")}-{V("cf_fx")}')
    S('lev_tgt', '  Target net debt = target leverage × adjusted EBITDA', 'sched', 'm', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to target leverage', 'sched', 'm', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash beyond the leverage target is returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of revenue', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_amort', '  Acquisition-related amortization % of revenue', 'pct', 'pct', all=ratio('d_amort', 'is_rev'))
    S('hr_int', '  Net interest expense ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_int")}*{ann()}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    def ltm():
        if CTX.col.tp and not CTX.col.q: return None
        if not CTX.col.q: return f'={V("r_adj")}'
        cs = _ltm_cols(CTX.col)
        if not cs: return None
        refs = ','.join(f'{c}{R["r_adj"]}' for c in cs)
        return f'=IF(COUNT({refs})=4,SUM({refs}),"")'
    S('hr_ltm', '  LTM adjusted EBITDA (quarter columns: trailing four quarters)', 'line', 'm', all=ltm)
    S('hr_lev', '  Net debt / LTM adjusted EBITDA (x)', 'line', 'x2',
      all=lambda: f'=IF(AND(ISNUMBER({V("hr_ltm")}),ISNUMBER({V("ds_total")})),IFERROR(({V("ds_total")}-{V("bs_cash")}-N({V("bs_stinv")}))/{V("hr_ltm")},""),"")')
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted EBIT, full-cost; 2H19 transition period not annualised)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT, full-cost (adjusted EBITDA − total D&A)', 'line', 'm', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate (GAAP; 21% where distorted)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(IF(AND({V("is_etr")}>0.05,{V("is_etr")}<0.4),{V("is_etr")},0.21),0.21)')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + subsidiary preferred + Net debt', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity + subsidiary preferred stock (mezzanine + derivative liabilities)', 'line', 'm', ann=True,
      all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),{V("bs_teq")}+N({V("bs_mezz")})+N({V("bs_prefd")}),"n/a")')
    S('ra_nd', '  Net debt = Total debt − cash − short-term investments', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")}-N({V("bs_stinv")}),"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Revenue', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Revenue / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-({V("bs_gw")}+{V("bs_int")}),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. short-term debt)', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})),"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income attributable', 'line', 'm', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Shareholders' equity", 'line', 'm', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash − short-term investments', 'line', 'm', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA (model)', 'line', 'm', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_gx', 'Net debt / EBITDA (x) — company "net debt leverage ratio" definition (EBITDA incl. non-operating income)', 'line', 'x2', ann=True,
      all=lambda: f'=IFERROR({V("lv_nd")}/{V("r_ebitda")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interests + subsidiary preferred stock (mezzanine + derivative liabilities; USDm)', 'line', 'm', e26=lambda: f'={V("bs_ncipref")}', ae=lambda: f'={V("bs_ncipref")}')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Revenue', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted operating income (EBITA)', lambda: f'=IFERROR({V("v_ev")}/{V("o_adj")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (non-GAAP EPS, model rebuild)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)

def _ltm_cols(col):
    """columns of the trailing four quarters ending at col (None if not all four are in the model)."""
    out = []
    y, q = col.year, col.q
    for _ in range(4):
        if (y, q) not in QC: return None
        out.append(QC[(y, q)].c)
        q -= 1
        if q == 0: y, q = y - 1, 4
    return out
