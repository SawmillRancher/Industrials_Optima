"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, QEc, B1

def build_spec2(V0):
    S = add
    def e26f(key, q4):          # 2026E flow = 9M actual (Q1-Q3/26) + Q4/26E estimate
        return lambda: f'={ACT(key)}+{q4()}'
    Q425 = QC[(2025, 4)].c
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 9M 2026 actual + Q4 estimate; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net income (incl. NCI; from continuing operations where the statement starts there)', 'line', 'm', data='cf_ni_start', flow=True,
      fc=lambda: f'={V("is_cont")}', e26=e26f('cf_ni', lambda: QEc('is_cont')))
    S('cf_adj', 'Adjustments to reconcile net income to operating cash flow:', 'sub', 'gen')
    S('cf_dda', '  Depreciation and amortization', 'line', 'm', data='cf_dda', flow=True, fc=lambda: f'={V("is_dda")}', e26=e26f('cf_dda', lambda: QEc('is_dda')))
    S('cf_def', '  Deferred income tax provision', 'line', 'm', data='cf_def', flow=True, e26=lambda: f'={ACT("cf_def")}+{V0["def_q4"]}', ae_in=V0['def_ae'],
      note='Forecast input (assumption): R&D capitalisation (IRC 174) reversals and pension deferred taxes have driven swings.')
    S('cf_sbc', '  Stock compensation cost', 'line', 'm', data='cf_sbc', flow=True, fc=lambda: f'={V("is_sbc")}', e26=e26f('cf_sbc', lambda: QEc('is_sbc')))
    S('cf_pens', '  Net periodic pension and postretirement income (non-cash)', 'line', 'm', data='cf_pens', flow=True,
      e26=lambda: f'={ACT("cf_pens")}-{QEc("is_nsp")}+{V0["svc_q4"]}', ae=lambda: f'=-{V("is_nsp")}+{V0["svc_ae"]}',
      note='Reverses non-service pension income (non-cash) net of pension service cost. Forecast = −non-service pension income + service cost (input; 9M 2026 ~$128m).')
    S('cf_k401', '  Share-based 401(k) matching contributions (non-cash)', 'line', 'm', data='cf_k401', flow=True,
      e26=lambda: f'={ACT("cf_k401")}*4/3', ae=lambda: f'={V("is_rev")}*{V0["k401_pct"]}', note='Matching contributions paid in RTX shares since 2024 (equity). 2027E+: % of net sales (2026 ~0.65%).')
    S('cf_contrib', '  Pension contributions', 'line', 'm', data='cf_contrib', flow=True, e26=lambda: f'={ACT("cf_contrib")}', ae_in=V0['contrib'],
      note='Shown separately to 2025; 2026 funding (~$0.3bn incl. benefits paid directly, FY2025 10-K) sits in other operating lines. 2027E+: input (plans ~101% funded).')
    S('cf_wc', '  Change in working capital (receivables, contract assets, inventory, other current assets, payables & accrued, contract liabilities)', 'line', 'm', data='cf_wc', flow=True,
      e26=lambda: f'={V("cal_wcx")}-({V("bs_cac")}-{B1("bs_cac")})',
      ae=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_cac")}-{P("bs_cac")})-({V("bs_inv")}-{P("bs_inv")})-({V("bs_oca")}-{P("bs_oca")})'
                  f'+({V("bs_ap")}-{P("bs_ap")})+({V("bs_clc")}-{P("bs_clc")})+({V("bs_accr")}-{P("bs_accr")})'),
      note='History as presented. Forecast linked to the balance sheet: −Δ(receivables, contract assets, inventory, other current assets) + Δ(payables & accrued, contract liabilities). 2026E: contract assets solved to the FCF outlook (Group block).')
    S('cf_oth', '  Other operating activities, net (derived)', 'line', 'm', data='cf_oth', flow=True, e26=lambda: f'={ACT("cf_oth")}', ae_in=V0['oth_op'],
      note='History: CFO − net income − the lines above (includes pension contributions and other items shown separately in some years). 2027E+ input (2023–25 average about −$120m; assumption).')
    S('cf_cfo', 'Net cash flows provided by operating activities (continuing operations)', 'line_b', 'm', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_oth")})')
    S('cf_capex', 'Capital expenditures', 'line', 'm', data='cf_capex', flow=True,
      e26=lambda: f'={ACT("cf_capex")}+{Q425}{R["cf_capex"]}*IFERROR({ACT("cf_capex")}/{ACT0x("cf_capex")},1)', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='2026E: 9M actual + Q4-25 × 9M y/y ratio (no capex figure in the SEC-filed outlook; assumption). 2027E+: net sales × capex %.')
    S('cf_acq', 'Acquisitions of businesses, net of cash acquired', 'line', 'm', data='cf_acq', flow=True, e26=lambda: f'={ACT("cf_acq")}', ae=lambda: f'=-{V("m_spend")}',
      note='Rockwell Collins (Nov-2018) and Goodrich (Jul-2012) cash consideration; Raytheon merger (Apr-2020) was all-stock (cash acquired shown as an inflow). 2027E+: M&A lever.')
    S('cf_divest', 'Dispositions of businesses', 'line', 'm', data='cf_divest', flow=True, e26=lambda: f'={ACT("cf_divest")}', ae_in=0.0,
      note='e.g. 2015 Sikorsky ($9bn; in discontinued operations), 2024 CIS ($1.3bn) and Hoist & Winch, 2025 actuation (~$1.8bn). No pending disposals in the forecast.')
    S('cf_oinv', 'Other investing activities (collaboration intangibles, customer financing, derivatives, other; derived)', 'line', 'm', data='cf_oinv', flow=True,
      e26=lambda: f'={ACT("cf_oinv")}*4/3', ae=lambda: f'=-{V("is_rev")}*{V0["oinv_pct"]}',
      note='Mainly increases in collaboration and other intangible assets (Pratt & Whitney program payments, software). Forecast % of net sales (assumption).')
    S('cf_cfi', 'Net cash flows used in investing activities', 'line_b', 'm', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_debt', 'Net change in debt (issuance − repayment of long-term debt, commercial paper, short-term borrowings)', 'line', 'm', data='cf_debt', flow=True,
      e26=lambda: f'={ACT("cf_debt")}+({V("ds_total")}-{B1("ds_total")})', ae=lambda: f'={V("ds_net")}',
      note='Per the debt schedule: notes repaid at maturity, part refinanced (input); commercial paper drawn or repaid to the minimum cash balance.')
    S('cf_div', 'Dividends paid on common stock', 'line', 'm', data='cf_div', flow=True,
      e26=lambda: f'={ACT("cf_div")}-{V0["dps_paid_q4"]}*{B1("bs_shares")}', ae=lambda: f'=-{V("dps")}*{V("bb_beg")}',
      note='2026E: Q4 payment of the $0.73 dividend declared in Q2-26 × shares outstanding at 30-Sep-2026. 2027E+: DPS × beginning shares (no circularity with buybacks).')
    S('cf_bb', 'Repurchase of common stock', 'line', 'm', data='cf_bb', flow=True, e26=lambda: f'={ACT("cf_bb")}-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note=('2026E: 9M actual (nil) + Q4 scenario input (~$0.6bn left on the Oct-2023 $11bn authorization). 2027E+ = leverage plug (surplus cash returned until net debt / adjusted EBITDA '
            'reaches the target). The 10-Q flags an executive order that may limit buybacks for underperforming defense contractors.'))
    S('cf_ofin', 'Other financing activities (NCI distributions, employee stock plans, other; derived)', 'line', 'm', data='cf_ofin', flow=True,
      e26=lambda: f'={ACT("cf_ofin")}-{QEc("is_nci")}', ae=lambda: f'=-{V("is_nci")}', note='Forecast: distributions to noncontrolling interests = NCI earnings (NCI balance flat).')
    S('cf_cff', 'Net cash flows used in financing activities', 'line_b', 'm', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_debt")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of foreign exchange rate changes on cash', 'line', 'm', data='cf_fx', flow=True, e26=lambda: f'={ACT("cf_fx")}', ae_in=0.0)
    S('cf_disc', 'Net cash flows from discontinued operations (Sikorsky 2015; Otis & Carrier 2020; earlier UTC disposals)', 'line', 'm', data='cf_disc', flow=True, fc=lambda: '=0')
    S('cf_net', 'Net change in cash, cash equivalents and restricted cash', 'line', 'm', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")})+N({V("cf_disc")}),"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}+{V("cf_disc")}')
    S('cf_beg', 'Cash — beginning of period (incl. restricted cash where the statement includes it)', 'line', 'm', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period', 'line_b', 'm', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: beginning cash + CFO + CFI + CFF + FX + discontinued = ending cash (should be 0; ±1 rounding)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=1.5,0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},0)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS(SUM({V("cf_ni")}:{V("cf_oth")})-{V("cf_cfo")})<=1.5,0,ROUND(SUM({V("cf_ni")}:{V("cf_oth")})-{V("cf_cfo")},0)),"")')
    S('cf_rc', '  Memo: restricted cash and cash held for sale in the cash-flow total (CF ending cash − BS cash; derived)', 'memo_calc', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("cf_end")}),ISNUMBER({V("bs_cash")})),{V("cf_end")}-{V("bs_cash")},"")', e26=lambda: f'={B1("cf_rc")}', ae=lambda: f'={P("cf_rc")}',
      note='ASU 2016-18: the cash-flow statement includes restricted cash from 2018 (and held-for-sale cash in disposal years); held at the last actual in the forecast.')
    S('cf_rc_pub', '  Memo: restricted cash as printed in the cash-flow statement', 'memo', 'm', data='cf_restr')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (company definition: CFO − capital expenditures)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")},"")')
    S('fcf_pub', '  Company-published free cash flow', 'memo', 'm', data='fcf_pub', flow=True)
    S('fcf_chk', '  Check: model vs company-published free cash flow (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("fcf_pub")}),IF(ABS({V("fcf")}-{V("fcf_pub")})<=1.5,0,ROUND({V("fcf")}-{V("fcf_pub")},0)),"n/p")')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of net sales', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of net sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note='2027E+ input: 2024–26 ~3.0–3.3% of sales (GTF MRO, munitions capacity), easing toward ~3%.')
    S('capex_dep', '  Capex / depreciation & other amortization (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("d_dep")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E = Q4 from shares outstanding at 30-Sep-2026 (10-Q cover); 2027E+ buybacks via the leverage plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = Q4)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under employee plans and the 401(k) match (m)', 'driver', 'm2', e26_in=V0['iss_q4'], ae_in=V0['iss_ae'],
      note='9M 2026: +7.2m shares outstanding with no repurchases (equity plans and share-based 401(k) matching). Input.')
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from shares outstanding at the Q3-26 10-Q cover date (1,349.4m).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since Q4/26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET (condensed, as in the releases)', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Sep-2026 balance sheet + Q4 flows; 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}-{V("cf_rc")}')
    S('bs_ar', '  Accounts receivable, net', 'line', 'm', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_cac', '  Contract assets, net (ASC 606, from 2018; "contracts in progress" in inventories before)', 'line', 'm', data='bs_cac', bs=True,
      e26=lambda: f'={B1("bs_cac")}+{V("cal_cfo_pre")}-{V("cal_cfo_req")}', ae=lambda: f'={V("wc_rev")}*{V("wc_cad")}/365',
      note='2026E: solved so 2026E free cash flow = the outlook end-point (designated working-capital plug; Group block). 2027E+: days of net sales.')
    S('bs_inv', '  Inventory, net (incl. contracts in progress before 2018)', 'line', 'm', data='bs_inv', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dio")}/365')
    S('bs_oca', '  Other current assets (incl. assets held for sale)', 'line', 'm', data='bs_oca', bs=True, e26=lambda: f'={B1("bs_oca")}', ae=lambda: f'={P("bs_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_cfa', '  Customer financing assets', 'line', 'm', data='bs_cfa', bs=True, e26=lambda: f'={B1("bs_cfa")}', ae=lambda: f'={P("bs_cfa")}')
    S('bs_ppe', '  Fixed assets, net', 'line', 'm', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-({V("cf_capex")}-{ACT("cf_capex")})-{QEc("d_dep")}-({V("cf_oinv")}-{ACT("cf_oinv")})',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("d_dep")}-{V("cf_oinv")}+{V("m_spend")}*{V("m_ppe")}',
      note='Roll-forward: prior + capex − (depreciation & other amortization − amortization of other intangibles, assumed equal to their additions in other investing) + acquired PP&E.')
    S('bs_rou', '  Operating lease right-of-use assets (from 2019)', 'line', 'm', data='bs_rou', bs=True, e26=lambda: f'={B1("bs_rou")}', ae=lambda: f'={P("bs_rou")}')
    S('bs_gw', '  Goodwill', 'line', 'm', data='bs_gw', bs=True, e26=lambda: f'={B1("bs_gw")}', ae=lambda: f'={P("bs_gw")}+{V("m_spend")}*(1-{V("m_ppe")}-{V("m_intp")})')
    S('bs_int', '  Intangible assets, net', 'line', 'm', data='bs_int', bs=True,
      e26=lambda: f'={B1("bs_int")}-{QEc("d_acq")}', ae=lambda: f'={P("bs_int")}-{V("d_acq")}+{V("m_spend")}*{V("m_intp")}',
      note='Roll-forward: prior − acquisition accounting amortization + acquired intangibles (M&A lever); collaboration / software intangibles net flat.')
    S('bs_onca', '  Other assets (incl. prepaid pension, deferred taxes; derived)', 'line', 'm', data='bs_onca', bs=True,
      e26=lambda: f'={B1("bs_onca")}-({V("cf_pens")}-{ACT("cf_pens")})-({V("cf_contrib")}-{ACT("cf_contrib")})', ae=lambda: f'={P("bs_onca")}-{V("cf_pens")}-{V("cf_contrib")}',
      note='Forecast: the net pension asset accretes with non-cash pension income and contributions (CW / HII practice).')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_cfa")}:{V("bs_onca")}),"")')
    S('bs_l', 'LIABILITIES, REDEEMABLE NONCONTROLLING INTEREST AND EQUITY', 'sub', 'gen')
    S('bs_std', '  Short-term borrowings (incl. commercial paper)', 'line', 'm', data='bs_std', bs=True, fc=lambda: f'={V("ds_cp")}')
    S('bs_ap', '  Accounts payable', 'line', 'm', data='bs_ap', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dpo")}/365')
    S('bs_clc', '  Contract liabilities (customer advances; from 2018)', 'line', 'm', data='bs_clc', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_clp")}')
    S('bs_ltdc', '  Long-term debt currently due', 'line', 'm', data='bs_ltdc', bs=True, fc=lambda: f'=MIN({V("ds_notes")},{V("ds_mat")})')
    S('bs_accr', '  Accrued employee compensation & other accrued liabilities (derived)', 'line', 'm', data='bs_accr', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_acp")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_std")}:{V("bs_accr")}),"")')
    S('bs_ltd', '  Long-term debt', 'line', 'm', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_notes")}-{V("bs_ltdc")}')
    S('bs_lease', '  Operating lease liabilities, non-current (from 2019)', 'line', 'm', data='bs_lease', bs=True, e26=lambda: f'={B1("bs_lease")}', ae=lambda: f'={P("bs_lease")}')
    S('bs_pens', '  Future pension and postretirement benefit obligations', 'line', 'm', data='bs_pens', bs=True, e26=lambda: f'={B1("bs_pens")}', ae=lambda: f'={P("bs_pens")}')
    S('bs_oncl', '  Other long-term liabilities (incl. deferred taxes; derived)', 'line', 'm', data='bs_oncl', bs=True,
      e26=lambda: f'={B1("bs_oncl")}+({V("cf_def")}-{ACT("cf_def")})+({V("cf_oth")}-{ACT("cf_oth")})', ae=lambda: f'={P("bs_oncl")}+{V("cf_def")}+{V("cf_oth")}',
      note='Forecast: + deferred tax provision + other operating items (non-cash accruals / settlements against long-term liabilities).')
    S('bs_tl', 'Total liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_oncl")}),"")')
    S('bs_rnci', '  Redeemable noncontrolling interest', 'line', 'm', data='bs_rnci', bs=True, e26=lambda: f'={B1("bs_rnci")}', ae=lambda: f'={P("bs_rnci")}')
    S('bs_eq', "  Shareowners' equity", 'line', 'm', data='bs_eq', bs=True,
      e26=lambda: (f'={B1("bs_eq")}+{QEc("is_ni")}+({V("cf_div")}-{ACT("cf_div")})+({V("cf_bb")}-{ACT("cf_bb")})+{QEc("d_sbc")}+({V("cf_k401")}-{ACT("cf_k401")})'),
      ae=lambda: f'={P("bs_eq")}+{V("is_ni")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_sbc")}+{V("cf_k401")}',
      note='+ net income attributable − dividends − repurchases + stock compensation + share-based 401(k) match (OCI held flat). Repurchases go to treasury stock.')
    S('bs_nci', '  Noncontrolling interest', 'line', 'm', data='bs_nci', bs=True,
      e26=lambda: f'={B1("bs_nci")}+{QEc("is_nci")}+({V("cf_ofin")}-{ACT("cf_ofin")})', ae=lambda: f'={P("bs_nci")}+{V("is_nci")}+{V("cf_ofin")}')
    S('bs_teq', 'Total equity', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")}+N({V("bs_nci")}),"")')
    S('bs_tle', 'TOTAL LIABILITIES, REDEEMABLE NCI AND EQUITY', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+N({V("bs_rnci")})+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=1.5,0,ROUND({V("bs_ta")}-{V("bs_tle")},0)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=1.5,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},0)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash + restricted cash (where printed) vs cash-flow ending cash (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("cf_rc_pub")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}+{V("cf_rc_pub")}-{V("cf_end")})<=1.5,0,ROUND({V("bs_cash")}+{V("cf_rc_pub")}-{V("cf_end")},0)),"")',
      fc=lambda: f'=IF(ABS({V("bs_cash")}+{V("cf_rc")}-{V("cf_end")})<=1.5,0,ROUND({V("bs_cash")}+{V("cf_rc")}-{V("cf_end")},0))')
    S('bs_shares', '  Memo: shares of common stock outstanding (10-Q / 10-K cover, m)', 'memo', 'm1', data='bs_shares', bs=True, e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input, fiscal-year-end levels)')
    S('wc_rev', '  Net sales — annualised (quarters × 4)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_cogs', '  Cost of sales — annualised', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_cogs")}*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — receivables / net sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_cad', '  Contract-asset days — contract assets / net sales × 365', 'line', 'd', hist=lambda: f'=IF(ISNUMBER({V("bs_cac")}),IFERROR({V("bs_cac")}/{V("wc_rev")}*365,""),"")',
      e26=lambda: f'=IFERROR({V("bs_cac")}/{V("wc_rev")}*365,"")', ae=lambda: f'={P("wc_cad")}', note='2026E is an output of the FCF calibration; 2027E+ held at the 2026E level (no release of the 2026 build assumed).')
    S('wc_dio', '  Inventory days — inventory / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_inv")}/{V("wc_cogs")}*365,"")', e26_in=V0['wc']['dio'], ae_in=V0['wc']['dio'])
    S('wc_dpo', '  Payable days — accounts payable / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_cogs")}*365,"")', e26_in=V0['wc']['dpo'], ae_in=V0['wc']['dpo'])
    S('wc_clp', '  Contract liabilities % of net sales', 'pct', 'pct', hist=lambda: f'=IF(ISNUMBER({V("bs_clc")}),IFERROR({V("bs_clc")}/{V("wc_rev")},""),"")', e26_in=V0['wc']['clp'], ae_in=V0['wc']['clp'])
    S('wc_acp', '  Accrued & other current liabilities % of net sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_accr")}/{V("wc_rev")},"")', e26_in=V0['wc']['acp'], ae_in=V0['wc']['acp'], note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables + contract assets + inventory + other current assets − payables − contract liabilities − accrued)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+N({V("bs_cac")})+{V("bs_inv")}+{V("bs_oca")}-{V("bs_ap")}-N({V("bs_clc")})-{V("bs_accr")},"")')
    S('wc_nwc_p', '  NWC % of net sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    S('cal_h', '2026E free cash flow calibration (contract assets are the designated plug)', 'sub', 'gen')
    S('cal_wcx', '  2026E working-capital change excluding contract assets (9M actual + Q4 change in the other working-capital lines)', 'line', 'm',
      e26=lambda: (f'={ACT("cf_wc")}-({V("bs_ar")}-{B1("bs_ar")})-({V("bs_inv")}-{B1("bs_inv")})-({V("bs_oca")}-{B1("bs_oca")})'
                   f'+({V("bs_ap")}-{B1("bs_ap")})+({V("bs_clc")}-{B1("bs_clc")})+({V("bs_accr")}-{B1("bs_accr")})'))
    S('cal_cfo_pre', '  2026E CFO before the contract-asset plug', 'line', 'm',
      e26=lambda: f'={V("cf_ni")}+{V("cf_dda")}+{V("cf_def")}+{V("cf_sbc")}+{V("cf_pens")}+{V("cf_k401")}+{V("cf_contrib")}+{V("cal_wcx")}+{V("cf_oth")}')
    S('cal_cfo_req', '  2026E CFO required = FCF outlook end-point − capital expenditures', 'line', 'm', e26=lambda: f'={V("cal_fcf")}-{V("cf_capex")}')
    S('cal_fcf_chk', '  Check: 2026E free cash flow vs outlook end-point (should be 0)', 'check', 'm', e26=lambda: f'=ROUND({V("fcf")}-{V("cal_fcf")},0)')
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppa_h', 'Major acquisitions — consideration & purchase-price allocation (closing-period column)', 'sub', 'gen')
    for k, lab in [('cons', 'Consideration (cash + equity issued; net of cash acquired where stated)'), ('ca', 'Current assets acquired (receivables, contract assets, inventories, other)'),
                   ('ppe', 'Fixed assets'), ('intang', 'Intangible assets (customer relationships, tradenames, technology)'), ('gw', 'Goodwill'), ('onca', 'Other assets'),
                   ('cl', 'Current liabilities assumed'), ('debt', 'Debt assumed'), ('ncl', 'Other liabilities assumed (pensions, deferred taxes, other)'), ('nci', 'Noncontrolling interest')]:
        S(f'ppa_{k}', f'  {lab}', 'sched', 'm', data=f'ppa_{k}', ppa=True)
    S('ppa_chk', '  Check: assets acquired − liabilities assumed − NCI − consideration (should be 0)', 'check', 'm',
      hist=lambda: (f'=IF(ISNUMBER({V("ppa_cons")}),ROUND(N({V("ppa_ca")})+N({V("ppa_ppe")})+N({V("ppa_intang")})+N({V("ppa_gw")})+N({V("ppa_onca")})'
                    f'-N({V("ppa_cl")})-N({V("ppa_debt")})-N({V("ppa_ncl")})-N({V("ppa_nci")})-{V("ppa_cons")},0),"")'))
    S('ppa_names', '  Deal closed in the period', 'text', 'gen', data='ppa_names', ppa=True, textdata=True)
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; stock appreciation rights, RSUs, PSUs)', 'sched', 'm1', ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.07)
    S('ds_h', 'Debt schedule (notes repaid at maturity, part refinanced; commercial paper / revolver drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (short-term borrowings + long-term debt incl. current portion)', 'sched', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+N({V("bs_ltdc")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_cp")}', note=MAN['debt']['q4_26_maturities'])
    S('ds_notes', '  Long-term debt (notes, term loan, finance leases; carrying amount)', 'sched', 'm', data='debt_lt',
      e26=lambda: f'={B1("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_repay', '  Notes / term loan repaid at maturity (input; Q3-26 10-Q debt table)', 'sched', 'm', e26_in=V0['repay'][FYC], ae_in={y: V0['repay'][y] for y in range(FYC + 1, FYL + 1)},
      note='Remaining 2026: $2,869m (2.650% $719m, SOFR + 1.225% term loan $900m, 5.750% $1,250m); 2027 $2,917m; 2028 $3,470m; 2029 $914m; 2030 $1,570m; 2031 $2,000m.')
    S('ds_refi', '  Share of maturities refinanced with new notes (input)', 'sched', 'pct', e26_in=0.0, ae_in=V0['refi'],
      note='Assumption: half of 2027E+ maturities refinanced, the rest repaid from free cash flow (deleveraging after the 2023 ASR funding).')
    S('ds_iss', '  New notes issued', 'sched', 'm', e26_in=0.0, ae=lambda: f'={V("ds_repay")}*{V("ds_refi")}')
    S('ds_mat', '  Maturities in the following year (current portion at year end)', 'sched', 'm', e26_in=V0['mat'][FYC], ae_in={y: V0['mat'][y] for y in range(FYC + 1, FYL + 1)})
    S('ds_pre', '  Cash before commercial-paper draws / repayments (opening cash + CFO + CFI + dividends, buybacks, other financing, FX, discontinued − notes repaid + issued)', 'sched', 'm',
      e26=lambda: (f'={B1("cf_end")}+({V("cf_cfo")}-{ACT("cf_cfo")})+({V("cf_cfi")}-{ACT("cf_cfi")})+({V("cf_bb")}-{ACT("cf_bb")})+({V("cf_div")}-{ACT("cf_div")})'
                   f'+({V("cf_ofin")}-{ACT("cf_ofin")})+({V("cf_fx")}-{ACT("cf_fx")})-{V("ds_repay")}+{V("ds_iss")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_bb")}+{V("cf_div")}+{V("cf_ofin")}+{V("cf_fx")}+{V("cf_disc")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_min', '  Minimum cash balance (cash-flow basis)', 'sched', 'm', e26_in=V0['min_cash'], ae_in=V0['min_cash'],
      note='Assumption: RTX held $5–9bn of cash in 2023–26; $6.0bn floor.')
    S('ds_cp', '  Commercial paper / incremental borrowings to the minimum cash balance (year end)', 'sched', 'm', data='debt_st',
      e26=lambda: f'=MAX(0,{B1("ds_cp")}+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_cp")}+{V("ds_min")}-{V("ds_pre")})',
      note=MAN['debt']['revolver'] + (' Shortfalls below the minimum cash balance are drawn; surplus repays this line first. Balances above the $5.0bn commercial-paper / revolver capacity '
                                       '(headroom memo below) are a financing assumption: they would be termed out with new notes at a similar rate.'))
    S('ds_head', '  Memo: headroom vs the $5.0bn revolving credit agreement (negative = would need other financing)', 'memo_calc', 'm',
      e26=lambda: f'=5000-{V("ds_cp")}', ae=lambda: f'=5000-{V("ds_cp")}')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on opening long-term debt %', 'sched', 'pct', ae_in=V0['r_notes'], note=V0['r_notes_note'])
    S('ds_r_cp', '  Interest rate on opening commercial paper %', 'sched', 'pct', ae_in=0.045)
    S('ds_fees', '  Other interest expense (tax-related interest, finance leases, fees; $m)', 'sched', 'm', ae_in=V0['int_other'],
      note='Assumption calibrated so 2027E interest expense, net is close to the 2026 run-rate (9M 2026 $1,188m).')
    S('ds_r_cash', '  Interest income yield on opening cash %', 'sched', 'pct', ae_in=V0['r_cash'])
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / adjusted EBITDA, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end)', 'sched', 'm',
      ae=lambda: (f'={P("ds_total")}-({P("cf_end")}-{P("cf_rc")})-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_ofin")}-{V("cf_fx")}-{V("cf_disc")}'))
    S('lev_tgt', '  Target net debt = target leverage × adjusted EBITDA', 'sched', 'm', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to target leverage', 'sched', 'm', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash beyond the leverage target is returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of net sales', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_acq', '  Acquisition accounting amortization % of net sales', 'pct', 'pct', all=ratio('d_acq', 'is_rev'))
    S('hr_int', '  Interest expense, net ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted EBIT: before acquired-intangible amortization, after stock compensation)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT (adjusted operating profit)', 'line', 'm', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate (adjusted)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("e_rate")}+0,0.21)')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + redeemable NCI + Net debt', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity (incl. NCI and redeemable NCI)', 'line', 'm', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),{V("bs_teq")}+N({V("bs_rnci")}),"n/a")')
    S('ra_nd', '  Net debt = Total debt − Cash', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Net sales', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Net sales / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-({V("bs_gw")}+{V("bs_int")}),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. short-term and current debt)', 'line', 'm', ann=True,
      all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})-N({V("bs_ltdc")})),"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income attributable to common shareowners', 'line', 'm', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Shareowners' equity", 'line', 'm', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash', 'line', 'm', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA (model definition)', 'line', 'm', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_gx', 'Total debt / adjusted EBITDA (x)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("ds_total")}/{V("r_adj")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interests incl. redeemable NCI (USDm)', 'line', 'm', e26=lambda: f'={V("bs_nci")}+N({V("bs_rnci")})', ae=lambda: f'={V("bs_nci")}+N({V("bs_rnci")})')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Net sales', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted operating profit', lambda: f'=IFERROR({V("v_ev")}/{V("o_adj")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)

def ACT0x(key): return f'SUM({PQ1}{R[key]}:{PQ3}{R[key]})'
