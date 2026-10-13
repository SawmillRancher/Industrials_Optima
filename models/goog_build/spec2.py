"""Row specification part 2: cash flow, share schedule, mandatory convertible preferred, balance sheet, working capital, schedules,
ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, H2, B1

def build_spec2(V0):
    S = add
    def e26f(key, src):          # FY2026E flow = 1H26 actual + 2H26 estimate (Q3E + Q4E of the income-statement driver)
        return lambda: f'={ACT(key)}+{H2(src)}'
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENTS OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 1H26 actual + 2H26 estimate; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net income', 'line', 'm', data='cf_ni', flow=True, e26=e26f('cf_ni', 'is_ni'), ae=lambda: f'={V("is_ni")}')
    S('cf_adj', 'Adjustments:', 'sub', 'gen')
    S('cf_dda', '  Depreciation & amortization (as presented)', 'line', 'm', data='cf_dda', flow=True, e26=e26f('cf_dda', 'd_dda'), ae=lambda: f'={V("d_dda")}')
    S('cf_sbc', '  Stock-based compensation expense', 'line', 'm', data='cf_sbc', flow=True, e26=e26f('cf_sbc', 'd_sbc'), ae=lambda: f'={V("d_sbc")}')
    S('cf_def', '  Deferred income taxes', 'line', 'm', data='cf_def', flow=True, e26=lambda: f'={ACT("cf_def")}+{PT("pt_def")}', ae_in=V0['def_ae'],
      note='Forecast input (2H26E point estimate; 2027E+ assumption).')
    S('cf_gl', '  (Gain) loss on debt and equity securities, net', 'line', 'm', data='cf_gl', flow=True, e26=lambda: f'={ACT("cf_gl")}-{H2("d_eqg")}', ae=lambda: f'=-{V("d_eqg")}')
    S('cf_wc', '  Changes in working capital & other operating items, net (derived)', 'line', 'm', data='cf_wc', flow=True,
      e26=lambda: (f'={ACT("cf_wc")}-({V("bs_ar")}-{B1("bs_ar")})-({V("bs_oca")}-{B1("bs_oca")}+{V("dv_hfs")})'
                   f'+({V("bs_ap")}-{B1("bs_ap")})+({V("bs_ocl")}-{B1("bs_ocl")})'),
      ae=lambda: f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_oca")}-{P("bs_oca")})+({V("bs_ap")}-{P("bs_ap")})+({V("bs_ocl")}-{P("bs_ocl")})',
      note=('History: net cash from operations − net income − D&A − stock-based compensation − deferred taxes − securities (gains) losses (includes other non-cash items). '
            'Forecast linked to the balance sheet: −Δ(receivables, other current assets ex GFiber held for sale) + Δ(payables, other current liabilities).'))
    S('cf_cfo', 'Net cash provided by operating activities', 'line_b', 'm', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Purchases of property & equipment', 'line', 'm', data='cf_capex', flow=True,
      e26=lambda: f'=-{PT("pt_capex")}', ae=lambda: f'=-{CH(SC["CAPEX"][CTX.col.year])}',
      note='2026E: mid-point of the 2026 capex outlook of $195–205bn (UNVERIFIED — Q2-26 earnings call, not filed on EDGAR; 1H26 actual $80.6bn per the 10-Q). 2027E+: scenario lever ($m; "increase significantly in 2027", call, unverified).')
    S('cf_acq', 'Acquisitions, net of cash acquired, and purchases of intangible assets', 'line', 'm', data='cf_acq', flow=True,
      e26=lambda: f'={ACT("cf_acq")}', ae=lambda: f'=-{V("m_spend")}', note='2026E = 1H actual (Wiz $29.5bn and Intersect $5.9bn less cash acquired). 2027E+: M&A lever.')
    S('cf_divest', 'Proceeds from divestitures', 'line', 'm', data='cf_divest', flow=True, e26=lambda: f'={ACT("cf_divest")}+{V("dv_cash")}', ae=lambda: f'={V("dv_cash")}')
    S('cf_oinv', 'Marketable & non-marketable securities and other investing, net (derived; forecast = marketable securities sold / (bought))', 'line', 'm', data='cf_oinv', flow=True,
      e26=lambda: f'={ACT("cf_oinv")}-({V("bs_msec")}-{B1("bs_msec")})', ae=lambda: f'=-({V("bs_msec")}-{P("bs_msec")})',
      note='Forecast: marketable securities are the liquidity buffer — sold to keep balance-sheet cash at the minimum before commercial paper is drawn; surplus cash is invested. New non-marketable investments not modelled.')
    S('cf_cfi', 'Net cash used in investing activities', 'line_b', 'm', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_bb', 'Repurchases of stock (Class A and Class C)', 'line', 'm', data='cf_bb', flow=True, e26=lambda: f'={ACT("cf_bb")}-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='No repurchases in 1H26 ($69.5bn left on the Apr-2025 $70bn authorization). 2H26E: scenario input. 2027E+: plug to the net-debt / adjusted EBITDA target (net-cash floor).')
    S('cf_div', 'Dividend payments (common + preferred)', 'line', 'm', data='cf_div', flow=True,
      e26=lambda: f'={ACT("cf_div")}-{Q3E}{R["dps"]}*{Q3E}{R["sh_basic"]}-{Q4E}{R["dps"]}*{Q4E}{R["sh_basic"]}-{V("mc_divc")}',
      ae=lambda: f'=-{V("dps")}*{V("bb_beg")}-{V("mc_divc")}', note='Common: DPS × shares (beginning shares 2027E+, no circularity with buybacks). Preferred: cash dividends per the MCPS schedule.')
    S('cf_sbcnet', 'Net payments related to stock-based award activities (tax withholding)', 'line', 'm', data='cf_sbcnet', flow=True,
      e26=lambda: f'={ACT("cf_sbcnet")}-{H2("d_sbc")}*{V0["sbcnet_r"]}', ae=lambda: f'=-{V("d_sbc")}*{V("ds_sbcnet")}')
    S('cf_eqiss', 'Issuance of common & preferred stock, ATM and minority interests (net)', 'line', 'm', data='cf_eqiss', flow=True,
      e26=lambda: f'={ACT("cf_eqiss")}', ae=lambda: f'={V("ds_atm")}',
      note='Jun-2026: common $30.5bn (public offering + Berkshire Hathaway private placement) + mandatory convertible preferred $19.1bn; minority investments in Other Bets (Waymo) $3.8bn in 1H26. 2027E+: ATM issuance input.')
    S('cf_debt', 'Net debt issuance (repayment)', 'line', 'm', data='cf_debt', flow=True,
      e26=lambda: f'={ACT("cf_debt")}+({V("ds_total")}-{B1("ds_total")})', ae=lambda: f'={V("ds_net")}',
      note='Per the debt schedule: notes repaid at maturity and refinanced; commercial paper drawn or repaid to the minimum cash balance.')
    S('cf_ofin', 'Other financing activities, net (derived)', 'line', 'm', data='cf_ofin', flow=True, e26=lambda: f'={ACT("cf_ofin")}', ae_in=0.0)
    S('cf_cff', 'Net cash provided by (used in) financing activities', 'line_b', 'm', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_bb")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of exchange-rate changes on cash', 'line', 'm', data='cf_fx', flow=True, e26=lambda: f'={ACT("cf_fx")}', ae_in=0.0)
    S('cf_net', 'Net increase (decrease) in cash (incl. restricted cash from 2018)', 'line', 'm', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")}),"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}')
    S('cf_beg', 'Cash — beginning of period', 'line', 'm', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period', 'line_b', 'm', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: beginning cash + CFO + CFI + CFF + FX = ending cash (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=1,0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},0)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")})<=1,0,ROUND(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")},0)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (company definition: CFO − purchases of property & equipment)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")},"")')
    S('fcf_pub', '  Company-published free cash flow (quarterly releases)', 'memo', 'm', data='fcf_pub', flow=True)
    S('fcf_chk', '  Check: model vs company-published free cash flow (should be 0; Q3-16 release predates a $29m 10-Q revision)', 'check', 'm',
      hist=lambda: (f'=IF(ISNUMBER({V("fcf_pub")}),IF(ABS({V("fcf")}-{V("fcf_pub")})<=1,0,ROUND({V("fcf")}-{V("fcf_pub")},0)),"n/p")' if pkey(CTX.col) != 'Q3-16' else '="exception"'))
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of revenues', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net income %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of revenues', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")')
    S('capex_dep', '  Capex / depreciation (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("d_dep")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE SCHEDULE — BUYBACKS, EQUITY-PLAN ISSUANCE AND PREFERRED CONVERSION', 'section',
      note='SHARES — 2026E from shares outstanding at 30-Jun-2026 (2H only); 2027E+ buybacks via the leverage plug')
    S('bb_px', '  Avg buyback / reference share price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = 2H)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans, net of withholding (m)', 'driver', 'm2', e26_in=V0['iss_2h'], ae_in=V0['iss_ae'],
      note='FY2025: shares outstanding fell 123m with ~240m repurchased → ~117m net issuance. 2H26E 60m; 2027E+ 120m p.a. (assumption).')
    S('bb_conv', '  Shares issued on conversion of the mandatory convertible preferred (m; May-2029)', 'line', 'm2', e26_in=0.0,
      ae=lambda: f'=IF({CTX.col.year}=2029,{V("mc_sh")},0)')
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from Class A + B + C shares outstanding at 30-Jun-2026 (Q2-26 10-Q).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}+{V("bb_conv")}',
      ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}+{V("bb_conv")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('mc_h', '6.25% Mandatory convertible preferred (Series A / B; issued 5-Jun-2026; converts ~15-May-2029)', 'sub', 'gen')
    S('mc_liq', '  Liquidation preference outstanding ($m; 19m shares × $1,000)', 'sched', 'm', e26_in=19000.0, ae=lambda: f'=IF({CTX.col.year}>=2029,0,{P("mc_liq")})')
    S('mc_rate', '  Conversion rate per preferred share (average of Series A / B bands: 2.263 min – 2.829 max; 1,000 ÷ price in between)', 'sched', 'gen',
      e26=lambda: f'=MAX(2.263,MIN(2.829,1000/{V("bb_px")}))', ae=lambda: f'=MAX(2.263,MIN(2.829,1000/{V("bb_px")}))',
      note='Series A converts into 2.2520–2.8160 Class A shares, Series B into 2.2740–2.8420 Class C shares, depending on the 20-day VWAP before 15-May-2029 (Q2-26 10-Q Note 11). Capped calls (cap ~$528–533) ignored, as in GAAP EPS.')
    S('mc_sh', '  Conversion shares at the forecast price (m)', 'sched', 'm1', e26=lambda: f'=19*{V("mc_rate")}', ae=lambda: f'=19*{V("mc_rate")}')
    S('mc_shd', '  If-converted shares in diluted EPS (m; 2029 weighted to 15-May)', 'sched', 'm1', ae=lambda: f'=IF({CTX.col.year}<2029,{V("mc_sh")},IF({CTX.col.year}=2029,{V("mc_sh")}*4.5/12,0))')
    S('mc_div', '  Preferred dividends accrued (income statement; 6.25% × $19.0bn)', 'sched', 'm', ae=lambda: f'=IF({CTX.col.year}<2029,1187.5,IF({CTX.col.year}=2029,1187.5*4.5/12,0))')
    S('mc_divc', '  Preferred dividends paid in cash (15 Feb / May / Aug / Nov; first $12.15 on 15-Aug-2026)', 'sched', 'm',
      e26_in=V0['pref_cash_2h'], ae=lambda: f'=IF({CTX.col.year}<2029,1187.5,IF({CTX.col.year}=2029,593.75,0))')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEETS (condensed)', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Jun-2026 balance sheet + 2H flows; 2027E+ from the prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}-{V("bs_restr")}')
    S('bs_msec', '  Marketable securities', 'line', 'm', data='bs_msec', bs=True,
      e26=lambda: f'=MAX(0,{V("ds_pre")}+{V("ds_cp")}-{B1("ds_cp")}-{V("ds_min")})', ae=lambda: f'=MAX(0,{V("ds_pre")}+{V("ds_cp")}-{P("ds_cp")}-{V("ds_min")})',
      note='Forecast = liquidity above the minimum cash balance (cash + marketable securities before commercial paper, less minimum cash).')
    S('bs_ar', '  Accounts receivable, net', 'line', 'm', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_oca', '  Other current assets (incl. held-for-sale GFiber assets in 2026; derived)', 'line', 'm', data='bs_oca', bs=True,
      e26=lambda: f'={B1("bs_oca")}-{V("dv_hfs")}', ae=lambda: f'={P("bs_oca")}*{V("is_rev")}/{P("is_rev")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_nmsec', '  Non-marketable securities (equity stakes; equity-method & other long-term investments)', 'line', 'm', data='bs_nmsec', bs=True,
      e26=lambda: f'={B1("bs_nmsec")}', ae=lambda: f'={P("bs_nmsec")}', note='Held flat (no forecast mark-to-market gains).')
    S('bs_ppe', '  Property & equipment, net (incl. finance-lease right-of-use assets from 2019)', 'line', 'm', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-({V("cf_capex")}-{ACT("cf_capex")})-{H2("d_dep")}',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("d_dep")}', note='Roll-forward: prior − capex (negative cash flow) − depreciation.')
    S('bs_gw', '  Goodwill', 'line', 'm', data='bs_gw', bs=True, e26=lambda: f'={B1("bs_gw")}', ae=lambda: f'={P("bs_gw")}+{V("m_spend")}*(1-{V("m_intp")})')
    S('bs_onca', '  Other non-current assets (intangibles, operating-lease ROU, deferred taxes, other; derived)', 'line', 'm', data='bs_onca', bs=True,
      e26=lambda: f'={B1("bs_onca")}-{H2("d_amort")}+{V("dv_noncash")}', ae=lambda: f'={P("bs_onca")}-{V("d_amort")}+{V("m_spend")}*{V("m_intp")}',
      note='Intangible assets are on the face of the balance sheet to 2022 and inside other non-current assets from 2023. Roll-forward: − amortization + acquired intangibles + GFiber note / equity interest (2026).')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_nmsec")}:{V("bs_onca")}),"")')
    S('bs_l', "LIABILITIES AND STOCKHOLDERS' EQUITY", 'sub', 'gen')
    S('bs_ap', '  Accounts payable', 'line', 'm', data='bs_ap', bs=True, fc=lambda: f'=-{V("cf_capex")}*{V("wc_apc")}')
    S('bs_std', '  Short-term debt: commercial paper + current portion of long-term debt', 'line', 'm', data='bs_std', bs=True,
      fc=lambda: f'={V("ds_cp")}+MIN({V("ds_notes")},{V("ds_mat")})', note='Current portion of long-term debt sits in accrued expenses & other current liabilities on the face from 2020; shown here with short-term debt.')
    S('bs_ocl', '  Accrued compensation, accrued expenses (incl. legal & regulatory accruals), revenue share, deferred revenue & other current (derived)', 'line', 'm',
      data='bs_ocl', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_oclp")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_ap")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term debt', 'line', 'm', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_std")}')
    S('bs_ol', '  Other long-term liabilities (income taxes payable, deferred taxes, operating-lease liabilities, other; derived)', 'line', 'm', data='bs_ol', bs=True,
      e26=lambda: f'={B1("bs_ol")}+({V("cf_def")}-{ACT("cf_def")})', ae=lambda: f'={P("bs_ol")}+{V("cf_def")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_ol")}),"")')
    S('bs_pref', '  Series A / B mandatory convertible preferred stock & APIC (net of the capped-call premium)', 'line', 'm', data='bs_pref', bs=True,
      e26=lambda: f'={B1("bs_pref")}', ae=lambda: f'=IF({V("mc_liq")}>0,{P("bs_pref")},0)')
    S('bs_eq', "  Common stockholders' equity (Class A / B / C stock & APIC, AOCI, retained earnings)", 'line', 'm', data='bs_eq', bs=True,
      e26=lambda: (f'={B1("bs_eq")}+{H2("is_ni")}+({V("cf_div")}-{ACT("cf_div")})+({V("cf_bb")}-{ACT("cf_bb")})+{H2("d_sbc")}'
                   f'+({V("cf_sbcnet")}-{ACT("cf_sbcnet")})+({V("cf_eqiss")}-{ACT("cf_eqiss")})'),
      ae=lambda: f'={P("bs_eq")}+{V("is_ni")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_sbc")}+{V("cf_sbcnet")}+{V("cf_eqiss")}+({P("bs_pref")}-{V("bs_pref")})',
      note='+ net income − dividends (common and preferred, as paid) − repurchases + stock-based compensation − tax withholding on awards + issuance + preferred converted (AOCI held flat).')
    S('bs_teq', "Total stockholders' equity", 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")}+N({V("bs_pref")}),"")')
    S('bs_tle', "TOTAL LIABILITIES AND STOCKHOLDERS' EQUITY", 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=1,0,ROUND({V("bs_ta")}-{V("bs_tle")},0)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=1,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},0)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs_ta', bs=True)
    S('bs_restr', '  Memo: cash-flow cash − balance-sheet cash (restricted cash from 2018; Motorola held-for-sale cash Q1–Q3/14)', 'memo_calc', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("cf_end")}),ISNUMBER({V("bs_cash")})),{V("cf_end")}-{V("bs_cash")},"")',
      e26=lambda: f'={B1("bs_restr")}', ae=lambda: f'={P("bs_restr")}', note='Forecast: held at the 30-Jun-2026 difference.')
    S('bs_shares', '  Memo: shares outstanding at period end (Class A + B + C, m; split-adjusted)', 'memo', 'm1', data='bs_shares', bs=True,
      e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input; year-end levels)')
    S('wc_rev', '  Revenues — annualised (quarters × 4)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — receivables / revenues × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_apc', '  Accounts payable % of annual capex (payables are dominated by technical-infrastructure vendors)', 'pct', 'pct',
      hist=lambda: (f'=IFERROR({V("bs_ap")}/(-{V("cf_capex")}*{4 if CTX.col.q else 1}),"")'), e26_in=V0['wc']['apc'], ae_in=V0['wc']['apc'])
    S('wc_oclp', '  Other current liabilities % of revenues', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")',
      e26_in=V0['wc']['ocl'], ae_in=V0['wc']['ocl'], note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables + other current assets − payables − other current liabilities)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_oca")}-{V("bs_ap")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of revenues', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppa_h', 'Acquisitions — consideration & purchase-price allocation (closing-quarter column)', 'sub', 'gen')
    for k, lab in [('cons', 'Consideration (total purchase price)'), ('ppe', 'Property & equipment'), ('intang', 'Intangible assets (technology, customer relationships, trade names)'),
                   ('gw', 'Goodwill'), ('nl', 'Net other assets (liabilities) assumed, incl. cash acquired'), ('debt', 'Debt assumed')]:
        S(f'ppa_{k}', f'  {lab}', 'sched', 'm', data=f'ppa_{k}', ppa=True)
    S('ppa_chk', '  Check: assets acquired − liabilities assumed − consideration (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("ppa_cons")}),ROUND(N({V("ppa_ppe")})+N({V("ppa_intang")})+N({V("ppa_gw")})+N({V("ppa_nl")})+N({V("ppa_debt")})-{V("ppa_cons")},0),"")')
    S('ppa_names', '  Deals closed in the period', 'text', 'gen', data='ppa_names', ppa=True, textdata=True)
    S('rf_h', 'Share count, pricing & capital returns', 'sub', 'gen')
    S('ds_dil', '  Dilutive RSUs and other contingently issuable shares (m)', 'sched', 'm1', ae_in=V0['dil'], note='Q2-26: 142m RSU / contingent shares in diluted EPS.')
    S('ds_pxg', '  Share-price appreciation % (buyback pricing, preferred conversion)', 'sched', 'pct', ae_in=0.08)
    S('ds_sbcnet', '  Net payments for stock-based award activities % of stock-based compensation', 'sched', 'pct', ae_in=V0['sbcnet_r'],
      note='FY2025 57% ($14.2bn / $25.0bn); 1H26 82% (higher share price at vesting).')
    S('ds_atm', '  At-the-market common stock issuance ($m; $40bn program, Jun-2026)', 'sched', 'm', ae_in=V0['atm'],
      note='Program intended primarily to meet tax obligations on employee equity grants; none sold at 30-Jun-2026. Forecast input (assumption: nil).')
    S('ds_h', 'Debt schedule (senior notes repaid at maturity and refinanced; commercial paper drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (short-term debt + current portion + long-term debt)', 'sched', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_cp")}', note=MAN['capital']['debt_2026_06_30'])
    S('ds_cp', '  Commercial paper / credit facilities drawn (plug)', 'sched', 'm', data='bs_cp', bs=True,
      e26=lambda: f'=MAX(0,{B1("ds_cp")}+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_cp")}+{V("ds_min")}-{V("ds_pre")})',
      note='$25bn commercial-paper program (nil outstanding at 30-Jun-2026); $11.7bn credit facilities ($1.3bn drawn, inside long-term debt).')
    S('ds_notes', '  Senior notes & other long-term debt (incl. current portion)', 'sched', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("ds_total")}),{V("ds_total")}-N({V("ds_cp")}),"")',
      e26=lambda: f'={B1("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_iss', '  New notes issued (input; 2H26E nil, 2027E+ refinance maturities)', 'sched', 'm', e26_in=0.0, ae=lambda: f'={V("ds_repay")}')
    S('ds_repay', '  Notes repaid at maturity (input)', 'sched', 'm', e26_in=V0['repay'][FYC], ae_in={y: V0['repay'][y] for y in range(FYC + 1, FYL + 1)}, note=V0['repay_note'])
    S('ds_mat', '  Maturities in the following year (current portion)', 'sched', 'm', e26_in=V0['mat'][FYC], ae_in={y: V0['mat'][y] for y in range(FYC + 1, FYL + 1)})
    S('ds_pre', '  Liquidity before commercial paper (opening cash + marketable securities + CFO + capex, M&A, divestitures + buybacks, dividends, award payments, issuance, other + FX − repaid + issued)', 'sched', 'm',
      e26=lambda: (f'={B1("cf_end")}-{V("bs_restr")}+{B1("bs_msec")}+({V("cf_cfo")}-{ACT("cf_cfo")})+({V("cf_capex")}-{ACT("cf_capex")})+({V("cf_acq")}-{ACT("cf_acq")})+({V("cf_divest")}-{ACT("cf_divest")})'
                   f'+({V("cf_bb")}-{ACT("cf_bb")})+({V("cf_div")}-{ACT("cf_div")})+({V("cf_sbcnet")}-{ACT("cf_sbcnet")})+({V("cf_eqiss")}-{ACT("cf_eqiss")})+({V("cf_ofin")}-{ACT("cf_ofin")})'
                   f'+({V("cf_fx")}-{ACT("cf_fx")})-{V("ds_repay")}+{V("ds_iss")}'),
      ae=lambda: (f'={V("cf_beg")}-{V("bs_restr")}+{P("bs_msec")}+{V("cf_cfo")}+{V("cf_capex")}+{V("cf_acq")}+{V("cf_divest")}+{V("cf_bb")}+{V("cf_div")}+{V("cf_sbcnet")}'
                  f'+{V("cf_eqiss")}+{V("cf_ofin")}+{V("cf_fx")}-{V("ds_repay")}+{V("ds_iss")}'))
    S('ds_min', '  Minimum cash balance (balance-sheet cash; marketable securities are drawn down first)', 'sched', 'm', e26_in=V0['min_cash'], ae_in=V0['min_cash'])
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on opening notes %', 'sched', 'pct', ae_in=V0['r_notes'], note=V0['r_notes_note'])
    S('ds_r_cp', '  Interest rate on opening commercial paper %', 'sched', 'pct', ae_in=0.042)
    S('ds_r_cash', '  Interest income yield on opening cash + marketable securities %', 'sched', 'pct', ae_in=V0['yield'], note=V0['yield_note'])
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / adjusted EBITDA; negative target = net-cash floor; 2027E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / adjusted EBITDA (x) (scenario)', 'sched', 'x2', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end; debt − cash − marketable securities)', 'sched', 'm',
      ae=lambda: (f'={P("ds_total")}-{P("bs_cash")}-{P("bs_msec")}-{V("cf_cfo")}-{V("cf_capex")}-{V("cf_acq")}-{V("cf_divest")}-{V("cf_div")}-{V("cf_sbcnet")}'
                  f'-{V("cf_eqiss")}-{V("cf_ofin")}-{V("cf_fx")}'))
    S('lev_tgt', '  Target net debt = target leverage × adjusted EBITDA', 'sched', 'm', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to the target', 'sched', 'm', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus liquidity beyond the target is returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of revenues', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_int', '  Interest expense ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("d_intexp")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted EBIT; invested capital excludes non-marketable equity stakes)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT (= adjusted operating income)', 'line', 'm', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Tax rate (GAAP effective; 18% where not meaningful)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(IF(AND({V("is_etr")}>0.05,{V("is_etr")}<0.4),{V("is_etr")},0.18),0.18)')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt − Non-marketable securities', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")}-{V("bs_nmsec")},"n/a")')
    S('ra_eq', '  Total equity (incl. preferred)', 'line', 'm', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),{V("bs_teq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − Cash − Marketable securities', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")}-{V("bs_msec")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Revenues', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Revenues / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill, cash, marketable & non-marketable securities', 'line', 'm', ann=True,
      all=lambda: f'=IFERROR(-({V("bs_gw")}+{V("bs_cash")}+{V("bs_msec")}+{V("bs_nmsec")}),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. short-term debt)', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})),"n/a")')
    S('rn_nta', '  = Net operating tangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income', 'line', 'm', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Common stockholders' equity", 'line', 'm', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash − marketable securities (negative = net cash)', 'line', 'm', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA', 'line', 'm', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_gx', 'Total debt / adjusted EBITDA (x)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("ds_total")}/{V("r_adj")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — GOOG (Class C), applied to all classes', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m; incl. RSUs and preferred if-converted to May-2029)', 'line', 'm',
      e26=lambda: f'={V("bb_end")}+({Q2}{R["sh_dil"]}-{Q2}{R["sh_basic"]}-16)+{V("mc_sh")}', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})+IF({V("mc_liq")}>0,{V("mc_sh")},0)')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm; negative = net cash)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_stake', 'Less: non-marketable equity securities at carrying value (USDm)', 'line', 'm', e26=lambda: f'=-{V("bs_nmsec")}', ae=lambda: f'=-{V("bs_nmsec")}',
      note='Equity stakes (non-marketable and equity-method investments) are outside invested capital and deducted from EV at carrying value (UBER lesson); fair values may differ.')
    S('v_ev', 'Enterprise value (USDm; operating)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_stake")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_stake")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Revenues', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted EBIT', lambda: f'=IFERROR({V("v_ev")}/{V("o_adj")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS, model)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
