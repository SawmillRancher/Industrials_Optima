"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules (properties, debt, buybacks,
Union Pacific merger consideration), ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, ACT0, QEc, B1, Q3c, PQ3c

def build_spec2(V0):
    S = add
    def e26f(key, q4):          # 2026E flow = 9M actual (Q1-Q3/26) + Q4/26E estimate
        return lambda: f'={ACT(key)}+{q4()}'
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 9M actual + Q4 estimate; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net income', 'line', 'm', data='cf_ni', flow=True, fc=lambda: f'={V("is_ni")}', e26=e26f('cf_ni', lambda: QEc('is_ni')))
    S('cf_adj', 'Reconciliation of net income to net cash provided by operating activities:', 'sub', 'gen')
    S('cf_dep', '  Depreciation', 'line', 'm', data='cf_dep', flow=True, fc=lambda: f'={V("is_dep")}', e26=e26f('cf_dep', lambda: QEc('is_dep')),
      note='Cash-flow depreciation (includes amounts capitalised / in other items; differs from the income-statement line by a few $m in some years).')
    S('cf_deftax', '  Deferred income taxes', 'line', 'm', data='cf_deftax', flow=True, e26=lambda: f'={ACT("cf_deftax")}+{QEc("is_tax")}*{V("deftax_pct")}',
      ae=lambda: f'={V("is_tax")}*{V("deftax_pct")}', note='Forecast = share of the income tax provision (input): accelerated tax depreciation on properties.')
    S('deftax_pct', '  Deferred taxes % of income tax provision', 'pct', 'pct', hist=ratio('cf_deftax', 'is_tax'), qe_in=V0['deftax_pct'], e26_in=V0['deftax_pct'], ae_in=V0['deftax_pct'],
      note='2025 35% ($277m / $792m), 9M-26 26%; bonus depreciation. Input 25%.')
    S('cf_gains', '  Gains and losses on properties', 'line', 'm', data='cf_gains', flow=True, e26=lambda: f'={ACT("cf_gains")}+{QEc("cf_gains_q")}', ae_in=V0['gains_ae'],
      note='Operating-property sale gains sit in "Materials and other" (2024 railway line sales $433m). Forecast: recurring property gains (input; 2025 $253m, 9M-26 $19m).')
    S('cf_gains_q', '  Q4/26E property gains (input, negative = gain)', 'driver', 'm', qe_in=V0['gains_q4'])
    S('cf_wc', '  Changes in assets and liabilities affecting operations (receivables, materials & supplies, other current assets, current liabilities other than debt)', 'line', 'm', data='cf_wc', flow=True,
      e26=lambda: (f'={ACT("cf_wc")}-({V("bs_ar")}-{B1("bs_ar")})-({V("bs_ms")}-{B1("bs_ms")})-({V("bs_oca")}-{B1("bs_oca")})'
                   f'+({V("bs_ap")}-{B1("bs_ap")})+({V("bs_taxes")}-{B1("bs_taxes")})+({V("bs_ocl")}-{B1("bs_ocl")})'),
      ae=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_ms")}-{P("bs_ms")})-({V("bs_oca")}-{P("bs_oca")})'
                  f'+({V("bs_ap")}-{P("bs_ap")})+({V("bs_taxes")}-{P("bs_taxes")})+({V("bs_ocl")}-{P("bs_ocl")})'),
      note='History: the four "changes in assets and liabilities" lines. Forecast linked to the balance sheet: −Δ(receivables, materials & supplies, other current assets) + Δ(payables, taxes, other current liabilities).')
    S('cf_oth', '  Other – net (incl. equity earnings of affiliates, pension, incident liability payments; derived)', 'line', 'm', data='cf_oth', flow=True,
      e26=lambda: f'={ACT("cf_oth")}+{QEc("cf_oth_q")}', ae_in=V0['oth_ae'],
      note='Derived: operating cash flow less the itemised lines. Includes the Eastern Ohio incident liability settlements (current liability $609m at 31-Dec-2025) and equity earnings of Conrail / TTX. Forecast input.')
    S('cf_oth_q', '  Q4/26E other – net (input)', 'driver', 'm', qe_in=V0['oth_q4'])
    S('cf_cfo', 'Net cash provided by operating activities', 'line_b', 'm', data='cf_cfo', flow=True,
      fc=lambda: f'={V("cf_ni")}+{V("cf_dep")}+{V("cf_deftax")}+{V("cf_gains")}+{V("cf_wc")}+{V("cf_oth")}', note='Σ operating lines.')
    S('cf_capex', 'Property additions', 'line', 'm', data='cf_capex', flow=True,
      e26=lambda: f'=-{PT("pt_capex")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='2026E: "we expect property additions to approximate $2.1 billion" (Q3-26 10-Q). 2027E+: revenues × capex % (long-range plan $2.3–2.4bn p.a.).')
    S('cf_acq', 'Acquisition of assets (Cincinnati Southern Railway, 2024: $1,643m)', 'line', 'm', data='cf_acq', flow=True, e26=lambda: f'={ACT("cf_acq")}', ae_in=0.0)
    S('cf_propsales', 'Property sales and other transactions', 'line', 'm', data='cf_propsales', flow=True, e26=lambda: f'={ACT("cf_propsales")}+{QEc("cf_props_q")}', ae_in=V0['props_ae'],
      note='Proceeds from operating-property sales (2024 incl. $389m railway line sales; 9M-26 $273m). Forecast input.')
    S('cf_props_q', '  Q4/26E property sale proceeds (input)', 'driver', 'm', qe_in=V0['props_q4'])
    S('cf_inv', 'Investment purchases, sales and other transactions, net', 'line', 'm', data='cf_inv', flow=True, e26=lambda: f'={ACT("cf_inv")}', ae_in=V0['inv_ae'],
      note='Includes company-owned life insurance and short-term investments (2025: −$522m incl. COLI loan repayments). Forecast input.')
    S('cf_cfi', 'Net cash used in investing activities', 'line_b', 'm', data='cf_cfi', flow=True, fc=lambda: f'={V("cf_capex")}+{V("cf_acq")}+{V("cf_propsales")}+{V("cf_inv")}')
    S('cf_div', 'Dividends', 'line', 'm', data='cf_div', flow=True, e26=lambda: f'={ACT("cf_div")}-{QEc("dps")}*{QEc("sh_basic")}', ae=lambda: f'=-{V("dps")}*{V("bb_beg")}',
      note='Q4/26E = quarterly DPS × shares; 2027E+ = DPS × beginning shares (no circularity with the buyback plug).')
    S('cf_stock', 'Common stock transactions (issued – net)', 'line', 'm', data='cf_stock', flow=True, e26=lambda: f'={ACT("cf_stock")}', ae_in=V0['stock_ae'])
    S('cf_bb', 'Purchase and retirement of common stock', 'line', 'm', data='cf_bb', flow=True, e26=lambda: f'={ACT("cf_bb")}', ae=lambda: f'=-{V("lev_bb")}',
      note='Suspended under the Merger Agreement (none in 9M-26; $6.3bn authorization remaining). 2027E: nil through the assumed closing; from 2028E the leverage plug applies (standalone case; assumption).')
    S('cf_borrow', 'Proceeds from borrowings', 'line', 'm', data='cf_borrow', flow=True, e26=lambda: f'={ACT("cf_borrow")}+{V("ds_iss")}', ae=lambda: f'={V("ds_iss")}+MAX(0,{V("ds_cp")}-{P("ds_cp")})')
    S('cf_repay', 'Debt repayments', 'line', 'm', data='cf_repay', flow=True, e26=lambda: f'={ACT("cf_repay")}-{V("ds_repay_q4")}', ae=lambda: f'=-{V("ds_repay")}-MAX(0,{P("ds_cp")}-{V("ds_cp")})',
      note='Per the debt schedule: notes repaid at maturity (10-K maturity table), commercial paper / revolver drawn or repaid to the minimum cash balance.')
    S('cf_ofin', 'Other financing (derived; nil historically)', 'line', 'm', data='cf_ofin', flow=True, e26=lambda: f'={ACT("cf_ofin")}', ae_in=0.0)
    S('cf_cff', 'Net cash used in financing activities', 'line_b', 'm', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_div")}:{V("cf_ofin")})')
    S('cf_net', 'Net increase (decrease) in cash and cash equivalents', 'line', 'm', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")},"")', fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}')
    S('cf_beg', 'Cash and cash equivalents — beginning of period', 'line', 'm', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash and cash equivalents — end of period', 'line_b', 'm', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: beginning cash + net change = ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=0.6,0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},1)),"")')
    S('cf_chk2', '  Check: CFO = Σ operating lines (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS({V("cf_ni")}+{V("cf_dep")}+{V("cf_deftax")}+{V("cf_gains")}+{V("cf_wc")}+{V("cf_oth")}-{V("cf_cfo")})<=0.6,0,ROUND({V("cf_ni")}+{V("cf_dep")}+{V("cf_deftax")}+{V("cf_gains")}+{V("cf_wc")}+{V("cf_oth")}-{V("cf_cfo")},1)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (model definition: operating cash flow − property additions)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")},"")',
      note='NSC publishes no free-cash-flow measure in its releases; model definition. Property-sale proceeds are shown separately below.')
    S('fcf_ps_m', '  Free cash flow incl. property sale proceeds', 'memo_calc', 'm', all=lambda: f'=IF(ISNUMBER({V("fcf")}),{V("fcf")}+N({V("cf_propsales")}),"")')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of revenues', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Property additions % of revenues', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note='2027E+ input: ~$2.3–2.4bn p.a. in the long-range plan (16–18% of revenues; 2015–25 range 16–22%).')
    S('capex_dep', '  Property additions / depreciation (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_dep")},""),"")')
    S('lrp_capex', '  Memo: long-range plan capital expenditures (merger proxy; not guidance)', 'memo', 'm',
      e26_in=V0['lrp']['capex'][2026], ae_in={y: V0['lrp']['capex'][y] for y in range(2027, 2031)})
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — repurchases suspended while the Union Pacific merger is pending (Merger Agreement); standalone leverage plug from 2028E')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed ($m; 2026E = Q4)', 'line', 'm', e26_in=0.0, ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans (m)', 'driver', 'm2', e26_in=V0['iss_q4'], ae_in=V0['iss_ae'])
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from shares outstanding at 30-Sep-2026 (224.6m, balance-sheet caption).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_auth', '  Memo: remaining repurchase authorization ($m; $10bn program from Apr-2022, $6.3bn left at 30-Sep-2026)', 'memo', 'm',
      e26_in=6300.0, ae=lambda: f'=MAX(0,{P("bb_auth")}-{V("bb_cash")})')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET (condensed, as in the releases)', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Sep-2026 balance sheet + Q4 flows; 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}')
    S('bs_sti', '  Short-term investments (none since 2016)', 'line', 'm', data='bs_sti', bs=True, fc=lambda: '=0')
    S('bs_ar', '  Accounts receivable – net', 'line', 'm', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_ms', '  Materials and supplies', 'line', 'm', data='bs_ms', bs=True, fc=lambda: f'={V("wc_opex")}*{V("wc_dms")}/365')
    S('bs_oca', '  Other current assets (incl. current deferred income taxes to 2016; derived)', 'line', 'm', data='bs_oca', bs=True, e26=lambda: f'={B1("bs_oca")}', ae=lambda: f'={P("bs_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_inv', '  Investments (Conrail, TTX and other equity-method investments; company-owned life insurance)', 'line', 'm', data='bs_inv', bs=True,
      e26=lambda: f'={B1("bs_inv")}-({V("cf_inv")}-{ACT("cf_inv")})*0.5', ae=lambda: f'={P("bs_inv")}-{V("cf_inv")}*0.5',
      note='Roll-forward: prior + half of net investment outflows (the other half to other assets; assumption). Other income is treated as cash (equity earnings ≈ distributions).')
    S('bs_ppe', '  Properties less accumulated depreciation', 'line', 'm', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-({V("cf_capex")}-{ACT("cf_capex")})-{QEc("is_dep")}-({QEc("cf_props_q")}+{QEc("cf_gains_q")})',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("is_dep")}-({V("cf_propsales")}+{V("cf_gains")})',
      note='Roll-forward: prior + property additions − depreciation − book value of properties sold (= proceeds − gain).')
    S('bs_oa', '  Other assets (pension asset, operating-lease ROU, deferred charges; derived)', 'line', 'm', data='bs_oa', bs=True,
      e26=lambda: f'={B1("bs_oa")}-({V("cf_inv")}-{ACT("cf_inv")})*0.5-{QEc("cf_oth_q")}*0.5',
      ae=lambda: f'={P("bs_oa")}-{V("cf_inv")}*0.5-{V("cf_oth")}*0.5')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_inv")}:{V("bs_oa")}),"")')
    S('bs_l', "LIABILITIES AND STOCKHOLDERS' EQUITY", 'sub', 'gen')
    S('bs_ap', '  Accounts payable', 'line', 'm', data='bs_ap', bs=True, fc=lambda: f'={V("wc_opex")}*{V("wc_dpo")}/365')
    S('bs_std', '  Short-term debt (commercial paper / securitization)', 'line', 'm', data='bs_std', bs=True, fc=lambda: f'={V("ds_cp")}')
    S('bs_taxes', '  Income and other taxes', 'line', 'm', data='bs_taxes', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_taxp")}')
    S('bs_ocl', '  Other current liabilities (incl. current Eastern Ohio incident liability; derived)', 'line', 'm', data='bs_ocl', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_oclp")}')
    S('bs_cmltd', '  Current maturities of long-term debt', 'line', 'm', data='bs_cmltd', bs=True, fc=lambda: f'={V("ds_mat")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_ap")}:{V("bs_cmltd")}),"")')
    S('bs_ltd', '  Long-term debt', 'line', 'm', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_notes")}-{V("ds_mat")}')
    S('bs_ol', '  Other liabilities (pension / OPEB, casualty & environmental, leases, non-current incident liability; derived)', 'line', 'm', data='bs_ol', bs=True,
      e26=lambda: f'={B1("bs_ol")}+{QEc("cf_oth_q")}*0.5', ae=lambda: f'={P("bs_ol")}+{V("cf_oth")}*0.5')
    S('bs_dtl', '  Deferred income taxes', 'line', 'm', data='bs_dtl', bs=True, e26=lambda: f'={B1("bs_dtl")}+({V("cf_deftax")}-{ACT("cf_deftax")})', ae=lambda: f'={P("bs_dtl")}+{V("cf_deftax")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_dtl")}),"")')
    S('bs_teq', "Total stockholders' equity", 'line_b', 'm', data='bs_teq', bs=True,
      e26=lambda: (f'={B1("bs_teq")}+{QEc("is_ni")}+({V("cf_div")}-{ACT("cf_div")})+({V("cf_bb")}-{ACT("cf_bb")})+({V("cf_stock")}-{ACT("cf_stock")})'),
      ae=lambda: f'={P("bs_teq")}+{V("is_ni")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_stock")}',
      note=('+ net income − dividends − repurchases + stock transactions (AOCI held flat). Share-based compensation is not shown separately on NSC\'s cash-flow statement (it sits inside "Other – net"), '
            'so the forecast other-net input is taken net of it and no separate equity add-back is made. NSC retires repurchased shares (no treasury stock).'))
    S('bs_tle', "TOTAL LIABILITIES AND STOCKHOLDERS' EQUITY", 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=0.6,0,ROUND({V("bs_ta")}-{V("bs_tle")},1)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=0.6,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},1)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash vs cash-flow ending cash (should be 0; 2018–19 CF cash includes restricted cash — memo row)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}+N({V("bs_restr")})-{V("cf_end")})<=0.6,0,ROUND({V("bs_cash")}+N({V("bs_restr")})-{V("cf_end")},1)),"")')
    S('bs_restr', '  Memo: restricted cash in cash-flow cash (ASU 2016-18, 2018–2019; derived = CF ending cash − BS cash)', 'memo', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(AND({CTX.col.year}>=2018,{CTX.col.year}<=2019),{V("cf_end")}-{V("bs_cash")},0),"")')
    S('bs_shares', '  Memo: shares outstanding at period end (m; balance-sheet caption)', 'memo', 'm1', data='bs_shares', bs=True, e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    S('bs_eq_h', '  Equity components as reported (memo):', 'sub', 'gen')
    S('bs_cs', '    Common stock', 'memo', 'm', data='bs_cs', bs=True)
    S('bs_apic', '    Additional paid-in capital', 'memo', 'm', data='bs_apic', bs=True)
    S('bs_aoci', '    Accumulated other comprehensive loss', 'memo', 'm', data='bs_aoci', bs=True)
    S('bs_re', '    Retained income', 'memo', 'm', data='bs_re', bs=True)
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input); year ends compared with year ends')
    S('wc_rev', '  Revenues — annualised (quarters × 4)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_opex', '  Operating expenses excl. depreciation & special items — annualised', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_opex")}),({V("is_opex")}-{V("is_dep")}-{V("sp_tot")})*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — receivables / revenues × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_dms', '  Materials & supplies days (on cash operating expenses)', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ms")}/{V("wc_opex")}*365,"")', e26_in=V0['wc']['dms'], ae_in=V0['wc']['dms'])
    S('wc_dpo', '  Payable days (on cash operating expenses)', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_opex")}*365,"")', e26_in=V0['wc']['dpo'], ae_in=V0['wc']['dpo'])
    S('wc_taxp', '  Income and other taxes payable % of revenues', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_taxes")}/{V("wc_rev")},"")', e26_in=V0['wc']['taxp'], ae_in=V0['wc']['taxp'])
    S('wc_oclp', '  Other current liabilities % of revenues', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")', e26_in=V0['wc']['oclp'], ae_in=V0['wc']['oclp'], note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables + materials & supplies + other current assets − payables − taxes − other current liabilities)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_ms")}+{V("bs_oca")}-{V("bs_ap")}-{V("bs_taxes")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of revenues', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppe_h', 'Properties roll-forward', 'sub', 'gen')
    S('ppe_dep_rate', '  Depreciation rate on opening net properties %', 'sched', 'pct', hist=lambda: (f'=IFERROR({V("is_dep")}*{4 if CTX.col.q else 1}/{P("bs_ppe")},"")' if CTX.col.prior and not CTX.col.q else None),
      ae_in=V0['dep_rate'], note='2025: $1,393m ÷ $35,831m opening net properties = 3.9%. Input 2027E+.')
    S('ppe_g', '  Net properties y/y %', 'pct', 'pct', all=growth('bs_ppe'))
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; stock options, RSUs, PSUs)', 'sched', 'm1', ae_in=V0['dil'], note='Q3-26: diluted 225.2m vs basic ~224.6m.')
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.06)
    S('ds_h', 'Debt schedule (notes & debentures repaid at maturity per the 10-K maturity table; refinancing input; commercial paper / revolver to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (short-term debt + current maturities + long-term debt)', 'sched', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+N({V("bs_cmltd")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_cp")}', note=MAN['debt']['at_2025_12_31'])
    S('ds_notes', '  Notes, debentures & finance leases (carrying amount incl. current maturities)', 'sched', 'm', data='debt_lt_c',
      e26=lambda: f'={B1("ds_notes")}-{V("ds_repay_q4")}+{V("ds_iss")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_iss', '  New notes issued (input; 2027E+ = maturities refinanced × refinancing %)', 'sched', 'm', e26_in=0.0, ae=lambda: f'={V("ds_repay")}*{V("ds_refi")}',
      note='No new issuance assumed in Q4/26E (Merger Agreement restricts additional indebtedness). 2027E+: maturities refinanced per the refinancing % (assumption).')
    S('ds_refi', '  Refinancing % of maturities', 'sched', 'pct', ae_in=V0['refi'])
    S('ds_repay', '  Notes repaid at maturity (10-K maturity table)', 'sched', 'm', e26_in=0.0, ae_in={y: V0['mat'][y] for y in range(FYC + 1, FYL + 1)}, note=V0['repay_note'])
    S('ds_repay_q4', '  Q4/26E debt repayments (input; 9M-26 $618m)', 'sched', 'm', e26_in=V0['repay_q4'])
    S('ds_mat', '  Maturities in the following year (current maturities)', 'sched', 'm', e26_in=V0['mat'][2027], ae_in={y: V0['mat'].get(y + 1, V0['mat'][2030]) for y in range(FYC + 1, FYL + 1)})
    S('ds_pre', '  Cash before commercial-paper draws / repayments (opening cash + CFO + CFI + dividends, buybacks, stock, other financing − notes repaid + issued)', 'sched', 'm',
      e26=lambda: (f'={B1("bs_cash")}+({V("cf_cfo")}-{ACT("cf_cfo")})+({V("cf_cfi")}-{ACT("cf_cfi")})+({V("cf_div")}-{ACT("cf_div")})+({V("cf_bb")}-{ACT("cf_bb")})'
                   f'+({V("cf_stock")}-{ACT("cf_stock")})+({V("cf_ofin")}-{ACT("cf_ofin")})-{V("ds_repay_q4")}+{V("ds_iss")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_stock")}+{V("cf_ofin")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_min', '  Minimum cash balance', 'sched', 'm', e26_in=V0['min_cash'], ae_in=V0['min_cash'], note='NSC held $1.4–1.6bn of cash through 2024–26.')
    S('ds_cp', '  Commercial paper / revolver / securitization and assumed new debt (cash plug to the minimum cash balance, year end)', 'sched', 'm', data='bs_std',
      e26=lambda: f'=MAX(0,{B1("ds_cp")}+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_cp")}+{V("ds_min")}-{V("ds_pre")})',
      note='$800m revolver (Jan-2029), $800m commercial paper program, $400m receivables securitization: all undrawn at 31-Dec-2025. Shortfalls below the minimum cash balance are drawn; surplus repays.')
    S('ds_head', '  Memo: headroom vs the $800m revolver / CP program (negative = balance above the program = assumed new notes, a financing assumption)', 'memo_calc', 'm', e26=lambda: f'=800-{V("ds_cp")}', ae=lambda: f'=800-{V("ds_cp")}')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on opening notes & debentures %', 'sched', 'pct', ae_in=V0['r_notes'], note=V0['r_notes_note'])
    S('ds_r_cp', '  Interest rate on opening commercial paper / revolver %', 'sched', 'pct', ae_in=0.05)
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a maximum net debt / adjusted EBITDA from 2028E; nil while the merger is pending)', 'sub', 'gen')
    S('lev_min', '  Maximum net debt / adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end)', 'sched', 'm',
      ae=lambda: f'={P("ds_total")}-{P("cf_end")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_stock")}-{V("cf_ofin")}')
    S('lev_tgt', '  Target net debt = maximum leverage × adjusted EBITDA', 'sched', 'm', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_on', '  Buybacks active (1 = yes; 0 while the merger is pending — 2027E)', 'sched', 'gen', ae_in={y: (0 if y <= 2027 else 1) for y in range(FYC + 1, FYL + 1)})
    S('lev_cap', '  Maximum annual repurchases ($m, input; pacing of the catch-up once the restriction lapses)', 'sched', 'm', ae_in=V0['bb_cap'],
      note='NSC repurchased $0.5–3.1bn a year in 2015–25 ($3.1bn in 2022). Cap at $3.5bn p.a. so the 2028E catch-up to the leverage target is paced (assumption).')
    S('lev_bb', '  Share repurchases: plug to the leverage target (capped)', 'sched', 'm', ae=lambda: f'=MIN({V("lev_cap")},MAX(0,{V("lev_tgt")}-{V("lev_pre")}))*{V("lev_on")}',
      note='Surplus debt capacity up to the leverage target is returned via buybacks (standalone case), capped per year; feeds the cash-flow repurchase line.')
    S('inv_h', 'Other income & investments', 'sub', 'gen')
    S('inv_yield', '  Other income yield on opening investments %', 'sched', 'pct', hist=lambda: (f'=IFERROR({V("is_othinc")}/{P("bs_inv")},"")' if CTX.col.prior and not CTX.col.q else None), ae_in=V0['inv_yield'])
    S('othinc_oth', '  Other income — other (interest, rental; input $m)', 'sched', 'm', ae_in=V0['othinc_oth'])
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_int', '  Interest expense ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    S('hr_d2c', '  Debt-to-total-capitalization % (company metric: total debt ÷ (total debt + equity))', 'pct', 'pct',
      all=lambda: f'=IFERROR({V("ds_total")}/({V("ds_total")}+{V("bs_teq")}),"")', note='49.8% at 30-Sep-2026 and 52.4% at 31-Dec-2025 per the 10-Q.')
    blank()

    # ------------------------------------------------------------------ MERGER
    S('sec_mg', 'PENDING MERGER — ACQUISITION OF NSC BY UNION PACIFIC (agreement 28-Jul-2025; STB application 19-Dec-2025; shareholder approval 14-Nov-2025)', 'section',
      note=('MERGER CONSIDERATION — 1.0 UNP share + $88.82 cash per NSC share; subject to Surface Transportation Board approval; end date 28-Jan-2028; $2.5bn termination fees. '
            'The operating model is NSC standalone in all scenarios; this block values the consideration and the spread.'))
    S('mg_cash', '  Cash consideration per NSC share ($)', 'sched', 'm2', e26_in=MAN['merger']['cash_per_share'], note=MAN['merger']['consideration'] + ' (8-K 29-Jul-2025, Item 1.01).')
    S('mg_ratio', '  Exchange ratio (UNP shares per NSC share)', 'sched', 'm2', e26_in=MAN['merger']['exchange_ratio'])
    S('mg_unp', '  UNP share price ($) — input', 'sched', 'm2', e26_in=MAN['price']['unp_px'], note=MAN['price']['unp_src'])
    S('mg_val', '  Implied consideration per NSC share ($)', 'total', 'm2', e26=lambda: f'={V("mg_cash")}+{V("mg_ratio")}*{V("mg_unp")}')
    S('mg_prem', '  Implied consideration vs current NSC share price (premium / (discount))', 'pct', 'pct', e26=lambda: f'=IFERROR({V("mg_val")}/{V("v_px")}-1,"")')
    S('mg_eqv', '  Implied equity value of NSC ($m; consideration × diluted shares at period end)', 'line', 'm', e26=lambda: f'={V("mg_val")}*{V("v_sh")}')
    S('mg_ev', '  Implied enterprise value ($m; + year-end 2026E net debt)', 'line', 'm', e26=lambda: f'={V("mg_eqv")}+{V("v_nd")}')
    S('mg_ev_eb', '  Implied EV / 2026E adjusted EBITDA (x)', 'line', 'x', e26=lambda: f'=IFERROR({V("mg_ev")}/{V("r_adj")},"")')
    S('mg_ev_eb27', '  Implied EV / 2027E adjusted EBITDA (x)', 'line', 'x', e26=lambda: f'=IFERROR({V("mg_ev")}/{Y("r_adj", 2027)},"")')
    S('mg_close', '  Assumed closing date (model assumption; company: "by early 2027, subject to STB approval")', 'sched', 'gen', e26_in='2027-06-30', textdata=True,
      note=MAN['merger']['expected_close'] + ' Model assumption: 30-Jun-2027.')
    S('mg_days', '  Days from the valuation date to the assumed closing', 'sched', 'm', e26=lambda: f'=MAX(1,DATE(2027,6,30)-TODAY())')
    S('mg_divs', '  NSC dividends expected before closing ($; quarterly $1.35 × quarters to close)', 'sched', 'm2', e26=lambda: f'={QEc("dps")}*ROUNDDOWN({V("mg_days")}/91.3,0)')
    S('mg_spread', '  Gross spread: consideration + dividends to close − current price (%)', 'pct', 'pct', e26=lambda: f'=IFERROR(({V("mg_val")}+{V("mg_divs")})/{V("v_px")}-1,"")')
    S('mg_irr', '  Annualised spread to the assumed closing (%)', 'pct', 'pct', e26=lambda: f'=IFERROR((1+{V("mg_spread")})^(365/{V("mg_days")})-1,"")')
    S('mg_fee', '  Termination fee payable to NSC if regulatory approval fails ($m / $ per share)', 'sched', 'm', e26_in=MAN['merger']['termination_fee_usd_m'],
      note='$2.5bn payable by Union Pacific on termination for failure to obtain regulatory approvals by the end date (8-K 29-Jul-2025). The same fee is payable by either party on a change of recommendation / alternative proposal.')
    S('mg_fee_ps', '  Termination fee per NSC share ($)', 'sched', 'm2', e26=lambda: f'=IFERROR({V("mg_fee")}/{V("v_sh")},"")')
    S('mg_cost', '  Memo: cumulative merger-related expenses since announcement ($m)', 'memo_calc', 'm',
      e26=lambda: f'={Y("sp_merger", 2025)}+{V("sp_merger")}', ae=lambda: f'={P("mg_cost")}+{V("sp_merger")}')
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted income from railway operations)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT (= adjusted income from railway operations)', 'line', 'm', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(MIN(0.4,MAX(0.15,{V("is_etr")}+0)),0.24)')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', "  Total stockholders' equity", 'line', 'm', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),{V("bs_teq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − cash & short-term investments', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")}-N({V("bs_sti")}),"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Revenues', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Revenues / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangible assets (none: NSC carries no goodwill)', 'line', 'm', ann=True, all=lambda: '=0')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. short-term debt and current maturities)', 'line', 'm', ann=True,
      all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})-N({V("bs_cmltd")})),"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income', 'line', 'm', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Stockholders' equity", 'line', 'm', ann=True, all=lambda: f'={V("bs_teq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash & short-term investments', 'line', 'm', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA', 'line', 'm', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_gx', 'Total debt / adjusted EBITDA (x)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("ds_total")}/{V("r_adj")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+({Q3c("sh_dil")}-{Q3c("sh_basic")})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation ($m)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt ($m)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interests ($m; none)', 'line', 'm', e26=lambda: '=0', ae=lambda: '=0')
    S('v_ev', 'Enterprise value ($m)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Revenues', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted EBIT', lambda: f'=IFERROR({V("v_ev")}/{V("o_adj")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
    S('v_deal', '  Memo: Union Pacific consideration per NSC share ($; merger block) and premium to the current price', 'memo_calc', 'm2', e26=lambda: f'={V("mg_val")}')
    S('v_deal_p', '  Consideration premium / (discount) vs current price', 'memo_calc', 'pct', e26=lambda: f'={V("mg_prem")}')
