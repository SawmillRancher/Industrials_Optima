"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules (CSRA PPA, debt, buybacks), ratios,
valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, QEc, B1

def build_spec2(V0):
    S = add
    def e26f(key, q4):          # 2026E flow = 9M actual (Q1-Q3/26) + Q4/26E estimate
        return lambda: f'={ACT(key)}+{q4()}'
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 9M actual + Q4 estimate; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net earnings', 'line', 'm', data='cf_ni', flow=True, fc=lambda: f'={V("is_ni")}', e26=e26f('cf_ni', lambda: QEc('is_ni')))
    S('cf_adj', 'Adjustments to reconcile net earnings to net cash from operating activities:', 'sub', 'gen')
    S('cf_dda', '  Depreciation & amortization', 'line', 'm', data='cf_dda', flow=True, fc=lambda: f'={V("is_dda")}', e26=e26f('cf_dda', lambda: QEc('is_dda')))
    S('cf_sbc', '  Equity-based compensation expense', 'line', 'm', data='cf_sbc', flow=True, fc=lambda: f'={V("is_sbc")}', e26=e26f('cf_sbc', lambda: QEc('is_sbc')))
    S('cf_def', '  Deferred income tax provision', 'line', 'm', data='cf_def', flow=True, e26=lambda: f'={ACT("cf_def")}+{V0["def_q4"]}', ae_in=V0['def_ae'],
      note='Forecast input (FY2025 $256m; 9M-26 $335m, bonus depreciation / R&D expensing under the 2025 tax law).')
    S('cf_wc', '  Change in operating working capital (receivables, unbilled, inventories, payables, customer advances, other)', 'line', 'm', data='cf_wc', flow=True,
      e26=lambda: (f'={ACT("cf_wc")}-({V("bs_ar")}-{B1("bs_ar")})-({V("bs_unb")}-{B1("bs_unb")})-({V("bs_inv")}-{B1("bs_inv")})-({V("bs_oca")}-{B1("bs_oca")})'
                   f'+({V("bs_ap")}-{B1("bs_ap")})+({V("bs_adv")}-{B1("bs_adv")})+({V("bs_ocl")}-{B1("bs_ocl")})'),
      ae=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_unb")}-{P("bs_unb")})-({V("bs_inv")}-{P("bs_inv")})-({V("bs_oca")}-{P("bs_oca")})'
                  f'+({V("bs_ap")}-{P("bs_ap")})+({V("bs_adv")}-{P("bs_adv")})+({V("bs_ocl")}-{P("bs_ocl")})'),
      note=('History: Σ of the release working-capital lines (accounts receivable, unbilled receivables / contracts in process, inventories, accounts payable, customer advances and deposits, '
            'income taxes payable and other current liabilities). Forecast linked to the balance sheet: −Δ(receivables, unbilled, inventories, other current assets) + Δ(payables, advances, other current liabilities).'))
    S('cf_oth', '  Other operating items, net (derived: pension, impairments, discontinued-operations adjustments, other)', 'line', 'm', data='cf_oth', flow=True,
      e26=lambda: f'={ACT("cf_oth")}+{V0["oth_q4"]}', ae_in=V0['oth_cf_ae'],
      note='History = CFO − net earnings − D&A − equity-based compensation − deferred taxes − working capital (includes the Q4-12 non-cash impairments and the 2025 pension-related items). Forecast input.')
    S('cf_cfo', 'Net cash provided by operating activities', 'line_b', 'm', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_oth")})',
      note='Continuing operations (discontinued-operations cash flow shown separately, as GD presents it).')
    S('cf_capex', 'Capital expenditures', 'line', 'm', data='cf_capex', flow=True,
      e26=lambda: f'=-{PT("pt_capex")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='2026E: FY26 input (9M-26 $918m; FY2025 $1,161m; shipyard and Gulfstream capacity). 2027E+: revenue × capex %.')
    S('cf_acq', 'Business acquisitions, net of cash acquired', 'line', 'm', data='cf_acq', flow=True,
      e26=lambda: f'={ACT("cf_acq")}', ae=lambda: f'=-{V("m_spend")}', note='2018: CSRA ($9.7bn). 2027E+: M&A lever (Base nil).')
    S('cf_oinv', 'Other investing activities, net (asset sales, securities; derived)', 'line', 'm', data='cf_oinv', flow=True, e26=lambda: f'={ACT("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Net cash used by investing activities', 'line_b', 'm', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_div', 'Dividends paid', 'line', 'm', data='cf_div', flow=True,
      e26=lambda: f'={ACT("cf_div")}-{QEc("dps")}*{QEc("sh_basic")}', ae=lambda: f'=-{V("dps")}*{V("bb_beg")}',
      note='Q4/26E = Q4 DPS × Q4 basic shares; 2027E+ = DPS × beginning shares (no circularity with the buyback plug).')
    S('cf_bb', 'Purchases of common stock', 'line', 'm', data='cf_bb', flow=True, e26=lambda: f'={ACT("cf_bb")}-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='2026E: 9M actual ($604m) + Q4 scenario input. 2027E+ = leverage plug (surplus cash returned until net debt / adjusted EBITDA reaches the target; GD buys back to offset dilution and opportunistically).')
    S('cf_notes', 'Fixed-rate notes issued / (repaid), net', 'line', 'm', data='cf_notes', flow=True,
      e26=lambda: f'={ACT("cf_notes")}+{V("ds_iss")}-{V("ds_repay")}', ae=lambda: f'={V("ds_iss")}-{V("ds_repay")}',
      note='Per the debt schedule: notes repaid at maturity ($1,000m in 2026); maturities assumed refinanced with new notes (input).')
    S('cf_cp', 'Commercial paper / credit facility, net', 'line', 'm', data='cf_cp', flow=True,
      e26=lambda: f'={V("ds_cp")}-{B1("ds_cp")}', ae=lambda: f'={V("ds_cp")}-{P("ds_cp")}',
      note='Commercial paper drawn or repaid to the minimum cash balance (none outstanding since 2021).')
    S('cf_ofin', 'Other financing, net (option proceeds, finance leases, other; derived)', 'line', 'm', data='cf_ofin', flow=True,
      e26=lambda: f'={ACT("cf_ofin")}+{V0["ofin_q4"]}', ae_in=V0['ofin_ae'])
    S('cf_cff', 'Net cash used by financing activities', 'line_b', 'm', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_div")}:{V("cf_ofin")})')
    S('cf_disc', 'Net cash used by discontinued operations', 'line', 'm', data='cf_disc', flow=True, e26=lambda: f'={ACT("cf_disc")}', ae_in=0.0)
    S('cf_net', 'Net increase (decrease) in cash and equivalents', 'line', 'm', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_disc")}),"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_disc")}')
    S('cf_beg', 'Cash and equivalents at beginning of period', 'line', 'm', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash and equivalents at end of period', 'line_b', 'm', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: beginning cash + net change = ending cash (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},1),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),ROUND(SUM({V("cf_ni")}:{V("cf_oth")})-{V("cf_cfo")},1),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (company definition: net cash from operating activities − capital expenditures)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")},"")')
    S('fcf_pub', '  Company-published free cash flow', 'memo', 'm', data='fcf_pub', flow=True)
    S('fcf_chk', '  Check: model vs company-published free cash flow (should be 0; Q2-16 excluded, see comment)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("fcf_pub")}),ROUND({V("fcf")}-{V("fcf_pub")},1),"n/p")')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of revenue', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / net earnings conversion %', 'pct', 'pct', all=ratio('fcf', 'is_ni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note='2027E+ input: FY2023–25 2.0–2.2% of revenue (submarine industrial-base and Gulfstream investment), normalising toward 2.0%.')
    S('capex_dep', '  Capex / depreciation (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("d_dep")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E = Q4 from shares outstanding at 4-Oct-2026; 2027E+ buybacks via the leverage plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = Q4)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans (m)', 'driver', 'm2', e26_in=V0['iss_q4'], ae_in=V0['iss_ae'],
      note='Option exercises and restricted-stock vesting; shares outstanding rose ~0.2m in 9M-26 before buybacks.')
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from shares outstanding at 4-Oct-2026 (10-Q cover page, 270.2m).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since Q4/26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET (condensed, as in the releases)', 'section',
      note='BS FORECAST — 2026E rolled forward from the 4-Oct-2026 balance sheet + Q4 flows; 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and equivalents', 'line', 'm', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}')
    S('bs_ar', '  Accounts receivable', 'line', 'm', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_unb', '  Unbilled receivables (contracts in process to 2016)', 'line', 'm', data='bs_unbilled', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_unb")}/365',
      note='Contract assets (costs and estimated profits in excess of billings); the largest working-capital item after inventories.')
    S('bs_inv', '  Inventories', 'line', 'm', data='bs_inv', bs=True, fc=lambda: f'={V("wc_cost")}*{V("wc_dio")}/365')
    S('bs_oca', '  Other current assets', 'line', 'm', data='bs_oca', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_ocap")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_ppe', '  Property, plant and equipment, net', 'line', 'm', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-({V("cf_capex")}-{ACT("cf_capex")})-{QEc("d_dep")}',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("d_dep")}+{V("m_spend")}*{V("m_ppe")}',
      note='Roll-forward: prior − capex (negative cash flow) − depreciation + acquired PP&E.')
    S('bs_int', '  Intangible assets, net', 'line', 'm', data='bs_intang', bs=True,
      e26=lambda: f'={B1("bs_int")}-{QEc("d_amort")}+{V0["rou_q4"]}', ae=lambda: f'={P("bs_int")}-{V("d_amort")}+{V("m_spend")}*{V("m_intp")}+{V("rou_add")}',
      note='Roll-forward: prior − amortization + acquired intangibles (M&A lever) + finance-lease ROU additions (input; the amortization line includes finance-lease ROU amortization from 2019).')
    S('rou_add', '  Finance-lease right-of-use additions (input; offsets the ROU amortization inside the amortization line)', 'driver', 'm', ae_in=V0['rou_ae'])
    S('bs_gw', '  Goodwill', 'line', 'm', data='bs_gw', bs=True, e26=lambda: f'={B1("bs_gw")}', ae=lambda: f'={P("bs_gw")}+{V("m_spend")}*(1-{V("m_ppe")}-{V("m_intp")})')
    S('bs_oa', '  Other assets (pension, deferred taxes, operating-lease ROU, investments; derived)', 'line', 'm', data='bs_oa', bs=True, e26=lambda: f'={B1("bs_oa")}', ae=lambda: f'={P("bs_oa")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+{V("bs_ppe")}+{V("bs_int")}+{V("bs_gw")}+{V("bs_oa")},"")')
    S('bs_l', "LIABILITIES AND SHAREHOLDERS' EQUITY", 'sub', 'gen')
    S('bs_std', '  Short-term debt and current portion of long-term debt', 'line', 'm', data='bs_std', bs=True, fc=lambda: f'={V("ds_cp")}+MIN({V("ds_notes")},{V("ds_mat")})',
      note='Commercial paper + notes maturing in the next twelve months.')
    S('bs_ap', '  Accounts payable', 'line', 'm', data='bs_ap', bs=True, fc=lambda: f'={V("wc_cost")}*{V("wc_dpo")}/365')
    S('bs_adv', '  Customer advances and deposits', 'line', 'm', data='bs_adv', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_advp")}',
      note='Progress payments and Gulfstream deposits; drives the negative working capital of the shipbuilding and aircraft businesses.')
    S('bs_ocl', '  Other current liabilities', 'line', 'm', data='bs_ocl', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_oclp")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_std")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term debt', 'line', 'm', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_std")}')
    S('bs_ol', '  Other liabilities (pension / OPEB, deferred taxes, operating leases, other; derived)', 'line', 'm', data='bs_ol', bs=True,
      e26=lambda: f'={B1("bs_ol")}+({V("cf_def")}-{ACT("cf_def")})+({V("cf_oth")}-{ACT("cf_oth")})', ae=lambda: f'={P("bs_ol")}+{V("cf_def")}+{V("cf_oth")}+{V("rou_add")}',
      note='Roll-forward: prior + deferred taxes + other operating items (pension and other non-cash / accrual items, which sit in other liabilities) + finance-lease liabilities on new ROU assets.')
    S('bs_tl', 'Total liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+{V("bs_ltd")}+{V("bs_ol")},"")')
    S('bs_te', "Total shareholders' equity", 'line_b', 'm', data='bs_te', bs=True,
      e26=lambda: f'={B1("bs_te")}+{QEc("is_ni")}+({V("cf_div")}-{ACT("cf_div")})+({V("cf_bb")}-{ACT("cf_bb")})+{QEc("d_sbc")}+({V("cf_ofin")}-{ACT("cf_ofin")})',
      ae=lambda: f'={P("bs_te")}+{V("is_ni")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_sbc")}+{V("cf_ofin")}',
      note='+ net earnings − dividends − repurchases + equity-based compensation + option proceeds (other financing; AOCI held flat). GD has no noncontrolling interests.')
    S('bs_nci', '  Noncontrolling interests (none)', 'line', 'm', e26=lambda: '=0', ae=lambda: '=0', hist=lambda: '=0')
    S('bs_tle', "TOTAL LIABILITIES AND SHAREHOLDERS' EQUITY", 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_te")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),ROUND({V("bs_ta")}-{V("bs_tle")},1),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),ROUND({V("bs_ta")}-{V("bs_ta_pub")},1),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash vs cash-flow ending cash (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),ROUND({V("bs_cash")}-{V("cf_end")},1),"")')
    S('bs_shares', '  Memo: shares outstanding at period end (m; release financial information to 2018, 10-Q / 10-K cover page since)', 'memo', 'm1', data='shares_out', bs=True,
      e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input) at 4-Oct-2026 levels (see the customer-advances note)')
    S('wc_rev', '  Revenue — annualised (quarters × 4)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_cost', '  Operating costs — annualised', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_costs")}),{V("is_costs")}*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  Receivable days — accounts receivable / revenue × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', e26_in=V0['wc26']['dso'], ae_in=V0['wc']['dso'])
    S('wc_unb', '  Unbilled receivable days — unbilled / revenue × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_unb")}/{V("wc_rev")}*365,"")', e26_in=V0['wc26']['unb'], ae_in=V0['wc']['unb'])
    S('wc_dio', '  Inventory days — inventories / operating costs × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_inv")}/{V("wc_cost")}*365,"")', e26_in=V0['wc26']['dio'], ae_in=V0['wc']['dio'])
    S('wc_ocap', '  Other current assets % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_oca")}/{V("wc_rev")},"")', e26_in=V0['wc26']['oca'], ae_in=V0['wc']['oca'])
    S('wc_dpo', '  Payable days — accounts payable / operating costs × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_cost")}*365,"")', e26_in=V0['wc26']['dpo'], ae_in=V0['wc']['dpo'])
    S('wc_advp', '  Customer advances and deposits % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_adv")}/{V("wc_rev")},"")', e26_in=V0['wc26']['adv'], ae_in=V0['wc']['adv'],
      note=V0['wc']['note'])
    S('wc_oclp', '  Other current liabilities % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")', e26_in=V0['wc26']['ocl'], ae_in=V0['wc']['ocl'])
    S('wc_nwc', '  Operating NWC (receivables + unbilled + inventories + other current assets − payables − advances − other current liabilities)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_unb")}+{V("bs_inv")}+{V("bs_oca")}-{V("bs_ap")}-{V("bs_adv")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppa_h', 'Acquisitions — consideration & purchase-price allocation (closing-period column)', 'sub', 'gen')
    for k, lab in [('cons', 'Consideration — purchase price (cash, incl. target debt extinguished)'),
                   ('ca', 'Current assets acquired (cash, receivables, unbilled, other)'), ('ppe', 'Property, plant & equipment'),
                   ('intang', 'Intangible assets (customer contracts and relationships, technology)'), ('gw', 'Goodwill'),
                   ('onca', 'Other noncurrent assets'), ('cl', 'Current liabilities assumed'), ('debt', 'Debt assumed'),
                   ('ncl', 'Noncurrent liabilities assumed (deferred taxes, capital leases, other)')]:
        S(f'ppa_{k}', f'  {lab}', 'sched', 'm', data=f'ppa_{k}', ppa=True)
    S('ppa_chk', '  Check: assets acquired − liabilities assumed − consideration (should be 0)', 'check', 'm',
      hist=lambda: (f'=IF(ISNUMBER({V("ppa_cons")}),ROUND(N({V("ppa_ca")})+N({V("ppa_ppe")})+N({V("ppa_intang")})+N({V("ppa_gw")})+N({V("ppa_onca")})'
                    f'-N({V("ppa_cl")})-N({V("ppa_debt")})-N({V("ppa_ncl")})-{V("ppa_cons")},1),"")'))
    S('ppa_names', '  Deal closed in the period', 'text', 'gen', data='ppa_names', ppa=True, textdata=True)
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; options & restricted stock)', 'sched', 'm1', ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.07)
    S('ds_h', 'Debt schedule (fixed-rate notes repaid at maturity and refinanced per the input; commercial paper drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (short-term + long-term)', 'sched', 'm', hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")',
      fc=lambda: f'={V("ds_notes")}+{V("ds_cp")}', note=MAN['debt']['notes_text'])
    S('ds_notes', '  Fixed-rate notes & other debt (carrying value, incl. current portion)', 'sched', 'm', data='debt_notes',
      e26=lambda: f'={B1("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_iss', '  New notes issued (input)', 'sched', 'm', e26_in=0.0, ae_in={y: V0['iss_notes'].get(y, 0.0) for y in range(FYC + 1, FYL + 1)},
      note='2027E+: maturities assumed refinanced with new notes of the same amount (assumption; GD refinanced its 2025 maturities and repaid the 2026 ones from cash).')
    S('ds_repay', '  Notes repaid at maturity (input)', 'sched', 'm', e26_in=0.0, ae_in={y: V0['repay'][y] for y in range(FYC + 1, FYL + 1)}, note=V0['repay_note'])
    S('ds_mat', '  Maturities in the following year (current portion)', 'sched', 'm', e26_in=V0['mat'][FYC], ae_in={y: V0['mat'][y] for y in range(FYC + 1, FYL + 1)})
    S('ds_pre', '  Cash before commercial-paper draws / repayments (opening cash + CFO + CFI + dividends, buybacks, other financing, disc. ops − notes repaid + issued)', 'sched', 'm',
      e26=lambda: (f'={B1("bs_cash")}+({V("cf_cfo")}-{ACT("cf_cfo")})+({V("cf_cfi")}-{ACT("cf_cfi")})+({V("cf_div")}-{ACT("cf_div")})+({V("cf_bb")}-{ACT("cf_bb")})'
                   f'+({V("cf_ofin")}-{ACT("cf_ofin")})+({V("cf_disc")}-{ACT("cf_disc")})-{V("ds_repay")}+{V("ds_iss")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_ofin")}+{V("cf_disc")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_min', '  Minimum cash balance', 'sched', 'm', e26_in=V0['min_cash'], ae_in=V0['min_cash'], note='GD ran $1.2–2.3bn of year-end cash in 2022–25; $1.5bn minimum (assumption).')
    S('ds_cp', '  Commercial paper / credit facility (year end)', 'sched', 'm', data='debt_cp',
      e26=lambda: f'=MAX(0,{B1("ds_cp")}+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_cp")}+{V("ds_min")}-{V("ds_pre")})',
      note='$5bn committed credit facilities back the commercial-paper programme (none outstanding at 31-Dec-2025). Shortfalls below the minimum cash balance are drawn; surplus repays CP.')
    S('ds_head', '  Memo: credit-facility headroom vs the $5bn commitment (negative = would need other financing)', 'memo_calc', 'm',
      e26=lambda: f'=5000-{V("ds_cp")}', ae=lambda: f'=5000-{V("ds_cp")}')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on opening notes %', 'sched', 'pct', ae_in=V0['r_notes'], note=V0['r_notes_note'])
    S('ds_r_cp', '  Interest rate on opening commercial paper %', 'sched', 'pct', ae_in=0.045, note='Assumption (SOFR-based CP, ~4.5%).')
    S('ds_r_cash', '  Interest income yield on opening cash %', 'sched', 'pct', ae_in=V0['r_cash'], note=V0['r_cash_note'])
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / adjusted EBITDA, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end)', 'sched', 'm',
      ae=lambda: f'={P("ds_total")}-{P("cf_end")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_ofin")}-{V("cf_disc")}')
    S('lev_tgt', '  Target net debt = target leverage × adjusted EBITDA', 'sched', 'm', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to target leverage', 'sched', 'm', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash beyond the leverage target is returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of revenue', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_amort', '  Amortization % of revenue', 'pct', 'pct', all=ratio('d_amort', 'is_rev'))
    S('hr_int', '  Interest, net ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR(-{V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted EBIT, full-cost)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT (= adjusted operating earnings, full-cost)', 'line', 'm', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(MIN(0.4,MAX(0.15,{V("is_etr")}+0)),0.175)')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity', 'line', 'm', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_te")}),{V("bs_te")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − Cash', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")},"n/a")')
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
    S('roe_ni', 'Net earnings', 'line', 'm', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Shareholders' equity", 'line', 'm', ann=True, all=lambda: f'={V("bs_te")}')
    S('roe', 'ROE = Net earnings / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash', 'line', 'm', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA', 'line', 'm', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_gx', 'Total debt / equity % (company "debt-to-equity" definition)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ds_total")}/{V("bs_te")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interests (USDm; none)', 'line', 'm', e26=lambda: f'={V("bs_nci")}', ae=lambda: f'={V("bs_nci")}')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Revenue', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted operating earnings', lambda: f'=IFERROR({V("v_ev")}/{V("o_adj")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
