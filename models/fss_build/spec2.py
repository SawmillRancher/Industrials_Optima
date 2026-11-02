"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, QEc, B1

def build_spec2(V0):
    S = add
    def e26f(key, q4):          # 2026E flow = 9M actual (Q1-Q3/26) + Q4/26E estimate
        return lambda: f'={ACT(key)}+{q4()}'
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 9M 2026 actual + Q4 estimate; quarters = discrete, derived from year-to-date statements; as originally reported)')
    S('cf_ni', 'Net income', 'line', 'm1', data='cf_ni', flow=True, fc=lambda: f'={V("is_ni")}', e26=e26f('cf_ni', lambda: QEc('is_ni')))
    S('cf_adj', 'Adjustments:', 'sub', 'gen')
    S('cf_dda', '  Depreciation & amortization', 'line', 'm1', data='cf_dda', flow=True, fc=lambda: f'={V("is_dda")}', e26=e26f('cf_dda', lambda: QEc('is_dda')))
    S('cf_sbc', '  Stock-based compensation', 'line', 'm1', data='cf_sbc', flow=True, fc=lambda: f'={V("is_sbc")}', e26=e26f('cf_sbc', lambda: QEc('is_sbc')))
    S('cf_def', '  Deferred income taxes', 'line', 'm1', data='cf_deftax', flow=True, e26=lambda: f'={ACT("cf_def")}+{V0["def_q4"]}', ae_in=V0['def_ae'],
      note='Cash-flow statement (XBRL where the line is not shown). Forecast input.')
    S('cf_rent', '  Rental fleet net investment (forecast; inside working capital & other historically)', 'line', 'm1', e26_in=0.0,
      ae=lambda: f'=-{V("g_rev")}*{V("rent_pct")}',
      note='Federal Signal reports rental-equipment purchases and sales inside operating cash flow; the fleet is depreciated within D&A.')
    S('cf_wc', '  Working capital & other operating items, net (derived)', 'line', 'm1', data='cf_wc', flow=True,
      e26=lambda: (f'={ACT("cf_wc")}-({V("bs_ar")}-{B1("bs_ar")})-({V("bs_inv")}-{B1("bs_inv")})'
                   f'+({V("bs_ap")}-{B1("bs_ap")})+({V("bs_dep")}-{B1("bs_dep")})+({V("bs_ocl")}-{B1("bs_ocl")})'),
      ae=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_inv")}-{P("bs_inv")})'
                  f'+({V("bs_ap")}-{P("bs_ap")})+({V("bs_dep")}-{P("bs_dep")})+({V("bs_ocl")}-{P("bs_ocl")})'),
      note=('History: net cash from operating activities − net income − D&A − stock-based compensation − deferred taxes (includes rental-fleet flows, pension '
            'contributions, gains on disposals and operating cash flows of discontinued businesses). Forecast linked to the balance sheet.'))
    S('cf_cfo', 'Net cash provided by operating activities (continuing operations where shown separately, to 2017)', 'line_b', 'm1', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Purchases of properties & equipment', 'line', 'm1', data='cf_capex', flow=True,
      e26=lambda: f'=-{PT("pt_capex")}', ae=lambda: f'=-{V("g_rev")}*{V("capex_pct")}',
      note='2026E: point estimate (FY26 guidance $45–55m, FY25 release). 2027E+: net sales × capex %.')
    S('cf_acq', 'Payments for acquisition-related activity, net of cash acquired', 'line', 'm1', data='cf_acq', flow=True,
      e26=lambda: f'={ACT("cf_acq")}-{PT("pt_gvs")}', ae=lambda: f'=-{V("m_spend")}',
      note='2026E = 9M actual (Mega $45.0m, Western Technology $9.2m, New Way closing adjustments) + Global Vacuum Systems (~$29m, 28-Oct-2026). 2027E+: M&A lever.')
    S('cf_oinv', 'Other investing activities, net (disposal proceeds, divestitures; derived)', 'line', 'm1', data='cf_cfi_oth', flow=True, e26=lambda: f'={ACT("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Net cash used for investing activities (continuing operations where shown separately)', 'line_b', 'm1', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_bb', 'Purchases of treasury stock (share repurchases)', 'line', 'm1', data='cf_bb', flow=True, e26=lambda: f'={ACT("cf_bb")}-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='2026E: 9M actual + Q4 scenario input ($152.0m remaining under the March 2020 and April 2025 programs at 26-Sep-2026). 2027E+ = leverage plug.')
    S('cf_wh', 'Redemptions of common stock for withholding taxes (stock compensation)', 'line', 'm1', data='cf_withhold', flow=True,
      e26=lambda: f'={ACT("cf_wh")}+{V0["wh_q4"]}', ae_in=V0['wh_ae'])
    S('cf_div', 'Cash dividends paid to stockholders', 'line', 'm1', data='cf_div', flow=True,
      e26=lambda: f'={ACT("cf_div")}-{QEc("dps")}*{QEc("sh_basic")}', ae=lambda: f'=-{V("dps")}*{V("bb_beg")}')
    S('cf_eq', 'Proceeds from stock-based compensation activity', 'line', 'm1', data='cf_stock_iss', flow=True, e26=lambda: f'={ACT("cf_eq")}+{V0["eq_q4"]}', ae_in=V0['eq_ae'])
    S('cf_debt', 'Net borrowings / (repayments) — revolver, term loan & other debt', 'line', 'm1', data='cf_debt', flow=True,
      e26=lambda: f'={V("ds_total")}-{B1("ds_total")}+{ACT("cf_debt")}', ae=lambda: f'={V("ds_net")}',
      note='History: revolving-credit net, proceeds and payments of long-term borrowings. Forecast per the debt schedule (revolver to the minimum cash balance).')
    S('cf_ofin', 'Other financing, net (acquisition-related payments, fees, other; derived)', 'line', 'm1', data='cf_cff_oth', flow=True,
      e26=lambda: f'={ACT("cf_ofin")}', ae_in=0.0)
    S('cf_cff', 'Net cash provided by (used for) financing activities (continuing operations where shown separately)', 'line_b', 'm1', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_bb")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of exchange rate changes on cash', 'line', 'm1', data='cf_fx', flow=True, e26=lambda: f'={ACT("cf_fx")}', ae_in=0.0)
    S('cf_disc', 'Cash flows of discontinued operations shown separately (operating, investing and financing; derived)', 'line', 'm1', data='cf_disc_cf', flow=True, e26=lambda: f'={ACT("cf_disc")}', ae_in=0.0)
    S('cf_adjc', 'Cash basis difference (year-to-date statements on a different opening cash; Q4-16)', 'line', 'm1', data='cf_cashadj', flow=True, e26=lambda: f'={ACT("cf_adjc")}', ae_in=0.0)
    S('cf_net', 'Net change in cash and cash equivalents', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")})+N({V("cf_disc")})+N({V("cf_adjc")}),"")')
    S('cf_beg', 'Cash — beginning of period', 'line', 'm1', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period', 'line_b', 'm1', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: beginning cash + net change = ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=0.15,0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},1)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")})<=0.15,0,ROUND(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")},1)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (model definition: CFO − purchases of properties & equipment)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")},"")',
      note='Federal Signal publishes operating cash flow (no free-cash-flow measure); model definition.')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of net sales', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of net sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note='2027E+ input: FY2021–25 1.3–2.4% of net sales (FY2025 1.3%; FY26 guidance ~1.9%).')
    S('rent_pct', '  Rental fleet net investment % of net sales (input)', 'pct', 'pct', ae_in=V0['rent_pct'],
      note='Rental equipment, net rose from $108m (2021) to $213m (Sep-2026); assumption keeps the fleet growing with the depreciation charge.')
    S('capex_dep', '  (Capex + rental investment) / depreciation (x)', 'line', 'x2',
      all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR((-{V("cf_capex")}-N({V("cf_rent")}))/({V("d_dda")}-N({V("is_amort")})),""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E = Q4 from shares outstanding at 30-Sep-2026; 2027E+ buybacks via the leverage plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = Q4)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans, net of withholding (m)', 'driver', 'm2', e26_in=V0['iss_q4'], ae_in=V0['iss_ae'])
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from shares outstanding at 30-Sep-2026 (issued less treasury shares, Q3-26 10-Q balance sheet).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since Q4/26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET (condensed)', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Sep-2026 balance sheet + Q4 flows; 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm1', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}')
    S('bs_ar', '  Accounts receivable, net', 'line', 'm1', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_inv', '  Inventories', 'line', 'm1', data='bs_inv', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dio")}/365')
    S('bs_oca', '  Prepaid expenses & other current assets (incl. assets of discontinued operations; derived)', 'line', 'm1', data='bs_oca', bs=True,
      e26=lambda: f'={B1("bs_oca")}', ae=lambda: f'={P("bs_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_ppe', '  Properties & equipment and rental equipment, net', 'line', 'm1', data='bs_ppex', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-({V("cf_capex")}-{ACT("cf_capex")})-({QEc("d_dda")}-{QEc("d_amort")})+{PT("pt_gvs")}*{PT("pt_gvs_ppe")}',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("cf_rent")}-({V("d_dda")}-{V("d_amort")})+{V("m_spend")}*{V("m_ppe")}',
      note='Roll-forward: prior − capex (negative cash flow) − rental fleet investment − depreciation (D&A − amortization) + acquired PP&E.')
    S('bs_gw', '  Goodwill', 'line', 'm1', data='bs_gw', bs=True, e26=lambda: f'={B1("bs_gw")}+{PT("pt_gvs")}*(1-{PT("pt_gvs_ppe")}-{PT("pt_gvs_int")})',
      ae=lambda: f'={P("bs_gw")}+{V("m_spend")}*(1-{V("m_ppe")}-{V("m_intp")})')
    S('bs_int', '  Intangible assets, net', 'line', 'm1', data='bs_int', bs=True,
      e26=lambda: f'={B1("bs_int")}-{QEc("d_amort")}+{PT("pt_gvs")}*{PT("pt_gvs_int")}', ae=lambda: f'={P("bs_int")}-{V("d_amort")}+{V("m_spend")}*{V("m_intp")}',
      note='Roll-forward: prior − amortization + acquired intangibles (GVS 2026E: preliminary allocation not yet published — split assumed; M&A lever 2027E+).')
    S('bs_onca', '  Lease right-of-use, deferred tax & other assets (derived)', 'line', 'm1', data='bs_onca', bs=True,
      e26=lambda: f'={B1("bs_onca")}', ae=lambda: f'={P("bs_onca")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_ppe")}:{V("bs_onca")}),"")')
    S('bs_l', "LIABILITIES AND STOCKHOLDERS' EQUITY", 'sub', 'gen')
    S('bs_std', '  Short-term borrowings & current portion of long-term debt', 'line', 'm1', data='bs_std', bs=True, fc=lambda: f'={V("ds_cur")}')
    S('bs_ap', '  Accounts payable', 'line', 'm1', data='bs_ap', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dpo")}/365')
    S('bs_dep', '  Customer deposits', 'line', 'm1', data='bs_dep', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_depp")}')
    S('bs_ocl', '  Accrued & other current liabilities (incl. liabilities of discontinued operations; derived)', 'line', 'm1', data='bs_ocl', bs=True,
      fc=lambda: f'={V("wc_rev")}*{V("wc_oclp")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_std")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term borrowings & finance lease obligations', 'line', 'm1', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_std")}')
    S('bs_ol', '  Pension, lease, deferred tax & other long-term liabilities (derived)', 'line', 'm1', data='bs_oncl', bs=True,
      e26=lambda: f'={B1("bs_ol")}+({V("cf_def")}-{ACT("cf_def")})', ae=lambda: f'={P("bs_ol")}+{V("cf_def")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_ol")}),"")')
    S('bs_eq', "  Stockholders' equity", 'line', 'm1', data='bs_eq', bs=True,
      e26=lambda: (f'={B1("bs_eq")}+{QEc("is_ni")}+({V("cf_div")}-{ACT("cf_div")})+({V("cf_bb")}-{ACT("cf_bb")})+({V("cf_wh")}-{ACT("cf_wh")})'
                   f'+{QEc("d_sbc")}+({V("cf_eq")}-{ACT("cf_eq")})'),
      ae=lambda: f'={P("bs_eq")}+{V("is_ni")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_wh")}+{V("cf_sbc")}+{V("cf_eq")}',
      note='+ net income − dividends − repurchases − withholding redemptions + stock-based compensation + option proceeds (OCI / FX translation held flat).')
    S('bs_nci', '  Noncontrolling interests (none)', 'line', 'm1', hist=lambda: '=0' if CTX.col.kind in ('A', 'Q') and xget(pkey(CTX.col), 'bs_ta') is not None else None,
      e26=lambda: '=0', ae=lambda: '=0')
    S('bs_teq', 'Total equity', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")}+N({V("bs_nci")}),"")')
    S('bs_tle', "TOTAL LIABILITIES AND STOCKHOLDERS' EQUITY", 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=0.15,0,ROUND({V("bs_ta")}-{V("bs_tle")},1)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=0.15,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},1)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm1', data='bs_ta', bs=True)
    S('bs_cdisc', '  Memo: cash of discontinued operations included in cash-flow cash (2015)', 'memo', 'm1', data='cf_cash_disc', bs=True)
    S('bs_chk_cash', '  Check: BS cash (+ discontinued-operations cash) vs cash-flow ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}+N({V("bs_cdisc")})-{V("cf_end")})<=0.15,0,ROUND({V("bs_cash")}+N({V("bs_cdisc")})-{V("cf_end")},1)),"")')
    S('bs_shares', '  Memo: shares outstanding at period end (issued less treasury, m)', 'memo', 'm1', data='bs_shares', bs=True, e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input; fiscal-year-end levels)')
    S('wc_rev', '  Net sales — annualised (quarters × 4)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_cogs', '  Cost of sales — annualised', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_cogs")}*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — receivables / net sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_dio', '  Inventory days — inventories / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_inv")}/{V("wc_cogs")}*365,"")', e26_in=V0['wc']['dio'], ae_in=V0['wc']['dio'])
    S('wc_dpo', '  Payable days — payables / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_cogs")}*365,"")', e26_in=V0['wc']['dpo'], ae_in=V0['wc']['dpo'])
    S('wc_depp', '  Customer deposits % of net sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_dep")}/{V("wc_rev")},"")', e26_in=V0['wc']['dep'], ae_in=V0['wc']['dep'])
    S('wc_oclp', '  Accrued & other current liabilities % of net sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")',
      e26_in=V0['wc']['ocl'], ae_in=V0['wc']['ocl'], note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables + inventories + other current assets − payables − deposits − other current liabilities)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_inv")}+{V("bs_oca")}-{V("bs_ap")}-{V("bs_dep")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of net sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm1', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppa_h', 'Acquisitions — consideration & purchase-price allocation (closing-period column)', 'sub', 'gen')
    for k, lab in [('cons', 'Consideration (net of cash acquired; incl. estimated earn-outs)'),
                   ('ca', 'Current assets acquired (receivables, inventories, other)'), ('ppe', 'Properties & equipment (incl. finance-lease right-of-use)'),
                   ('intang', 'Intangible assets (customer relationships, trade names, other)'), ('gw', 'Goodwill'),
                   ('onca', 'Other noncurrent assets'), ('cl', 'Current liabilities assumed (payables, accrued, customer deposits)'), ('debt', 'Debt / finance leases assumed'),
                   ('ncl', 'Noncurrent liabilities assumed')]:
        S(f'ppa_{k}', f'  {lab}', 'sched', 'm1', data=f'ppa_{k}', ppa=True)
    S('ppa_chk', '  Check: assets acquired − liabilities assumed − consideration (should be 0)', 'check', 'm1',
      hist=lambda: (f'=IF(ISNUMBER({V("ppa_cons")}),ROUND(N({V("ppa_ca")})+N({V("ppa_ppe")})+N({V("ppa_intang")})+N({V("ppa_gw")})+N({V("ppa_onca")})'
                    f'-N({V("ppa_cl")})-N({V("ppa_debt")})-N({V("ppa_ncl")})-{V("ppa_cons")},1),"")'))
    S('ppa_names', '  Deal closed in the period', 'text', 'gen', data='ppa_names', ppa=True, textdata=True)
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; options & restricted stock)', 'sched', 'm1', ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.08)
    S('ds_h', 'Debt schedule (2025 Credit Agreement: $400m delayed-draw term loan + $1.1bn revolver, maturing 29-Oct-2030; revolver drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (current + long-term borrowings and finance leases, net of issuance costs)', 'sched', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_tl")}+{V("ds_rev")}', note=MAN['debt']['at_2026_09_30'])
    S('ds_tl', '  Term loan (2025 Credit Agreement)', 'sched', 'm1', data='debt_tl',
      e26=lambda: f'={B1("ds_tl")}-{V("ds_repay")}', ae=lambda: f'={P("ds_tl")}-{V("ds_repay")}')
    S('ds_repay', '  Term loan repayments (input; prepayable, matures Oct-2030 — refinancing assumed)', 'sched', 'm1', e26_in=0.0,
      ae_in={y: V0['tl_repay'].get(y, 0.0) for y in range(FYC + 1, FYL + 1)}, note=V0['tl_note'])
    S('ds_pre', '  Cash before revolver draws / repayments (opening cash + CFO + CFI + buybacks, withholding, dividends, equity, other financing + FX − term-loan repayments)', 'sched', 'm1',
      e26=lambda: (f'={B1("bs_cash")}+({V("cf_cfo")}-{ACT("cf_cfo")})+({V("cf_cfi")}-{ACT("cf_cfi")})+({V("cf_bb")}-{ACT("cf_bb")})+({V("cf_wh")}-{ACT("cf_wh")})'
                   f'+({V("cf_div")}-{ACT("cf_div")})+({V("cf_eq")}-{ACT("cf_eq")})+({V("cf_ofin")}-{ACT("cf_ofin")})+({V("cf_fx")}-{ACT("cf_fx")})-{V("ds_repay")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_bb")}+{V("cf_wh")}+{V("cf_div")}+{V("cf_eq")}+{V("cf_ofin")}+{V("cf_fx")}-{V("ds_repay")}')
    S('ds_min', '  Minimum cash balance', 'sched', 'm1', e26_in=V0['min_cash'], ae_in=V0['min_cash'])
    S('ds_rev', '  Revolver & finance leases, net of issuance costs (year end)', 'sched', 'm1', data='debt_rev',
      e26=lambda: f'=MAX(0,{B1("ds_rev")}+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_rev")}+{V("ds_min")}-{V("ds_pre")})',
      note='$1.1bn revolver ($44.3m drawn at 30-Sep-2026) + finance leases ($2.2m) − unamortized issuance costs ($1.2m). Shortfalls below the minimum cash balance are drawn; surplus repays the revolver.')
    S('ds_cur', '  Current portion (finance leases; input)', 'sched', 'm1', e26_in=0.4, ae_in=0.4)
    S('ds_head', '  Memo: revolver headroom vs the $1.1bn commitment (negative = would need other financing)', 'memo_calc', 'm1',
      e26=lambda: f'=1100-{V("ds_rev")}', ae=lambda: f'=1100-{V("ds_rev")}')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm1', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_tl', '  Interest rate on opening term loan %', 'sched', 'pct', ae_in=V0['r_tl'], note=V0['r_note'])
    S('ds_r_rev', '  Interest rate on opening revolver %', 'sched', 'pct', ae_in=V0['r_tl'])
    S('ds_fees', '  Commitment fees, letters of credit & issuance-cost amortization ($m)', 'sched', 'm1', ae_in=2.0)
    S('ds_r_cash', '  Interest income yield on opening cash %', 'sched', 'pct', ae_in=0.01)
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / adjusted EBITDA, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end)', 'sched', 'm1',
      ae=lambda: f'={P("ds_total")}-{P("cf_end")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_wh")}-{V("cf_div")}-{V("cf_eq")}-{V("cf_ofin")}-{V("cf_fx")}')
    S('lev_tgt', '  Target net debt = target leverage × adjusted EBITDA', 'sched', 'm1', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to target leverage', 'sched', 'm1', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Cash beyond the leverage target (after dividends and the M&A lever) is returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of net sales', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_amort', '  Amortization of intangibles % of net sales', 'pct', 'pct', all=ratio('d_amort', 'is_rev'))
    S('hr_int', '  Interest expense, net ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted EBIT, full-cost)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT, full-cost (adjusted EBITDA − D&A)', 'line', 'm1', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate (adjusted)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(MAX(0,MIN(0.4,{V("e_rate")}+0)),0.25)')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity', 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),{V("bs_teq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − Cash', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Net sales', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Net sales / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm1', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangible assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-({V("bs_gw")}+{V("bs_int")}),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. short-term debt)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})),"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income', 'line', 'm1', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Stockholders' equity", 'line', 'm1', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA', 'line', 'm1', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_ltm', 'Memo: net debt / LTM adjusted EBITDA (x) — quarter ends (company leverage basis: trailing-twelve-month EBITDA)', 'line', 'x2',
      all=lambda: (f'=IFERROR(({V("ds_total")}-{V("bs_cash")})/SUM({ltm(CTX.col)}),"")' if CTX.col.q and ltm(CTX.col) else None))
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interests (USDm)', 'line', 'm', e26=lambda: f'={V("bs_nci")}', ae=lambda: f'={V("bs_nci")}')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Net sales', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted EBIT', lambda: f'=IFERROR({V("v_ev")}/{V("r_ebit")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)

def ltm(col):
    """the four quarter columns ending at quarter column col (adjusted EBITDA row range pieces), or None."""
    y, q = col.year, col.q
    cs = []
    for i in range(4):
        qq = q - i; yy = y
        while qq < 1: qq += 4; yy -= 1
        if (yy, qq) not in QC: return None
        cs.append(f'{QC[(yy, qq)].c}{R["r_adj"]}')
    return ','.join(cs)
