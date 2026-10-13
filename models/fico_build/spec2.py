"""Row specification part 2: cash flow, share schedule (incl. the June-2026 ASR), balance sheet, working capital, debt schedule,
leverage-targeted buybacks, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, QEc, B1, CHK

def build_spec2(V0):
    S = add
    def e26f(key, q4):          # FY2026E flow = 9M actual (Q1-Q3/26) + Q4/26E estimate
        return lambda: f'={ACT(key)}+{q4()}'
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONDENSED CONSOLIDATED STATEMENTS OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 9M FY26 actual + Q4 estimate; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net income', 'line', 'm1', data='cf_ni', flow=True, fc=lambda: f'={V("is_ni")}', e26=e26f('cf_ni', lambda: QEc('is_ni')))
    S('cf_adj', 'Non-cash items:', 'sub', 'gen')
    S('cf_dda', '  Depreciation & amortization', 'line', 'm1', data='cf_dda', flow=True, fc=lambda: f'={V("is_dda")}', e26=e26f('cf_dda', lambda: QEc('is_dda')))
    S('cf_sbc', '  Share-based compensation', 'line', 'm1', data='cf_sbc', flow=True, fc=lambda: f'={V("is_sbc")}', e26=e26f('cf_sbc', lambda: QEc('is_sbc')))
    S('cf_wc', '  Changes in operating assets & liabilities and other, net (derived)', 'line', 'm1', data='cf_wc', flow=True,
      e26=lambda: (f'={ACT("cf_wc")}-({V("bs_ar")}-{B1("bs_ar")})-({V("bs_oca")}-{B1("bs_oca")})+({V("bs_ap")}-{B1("bs_ap")})+({V("bs_accomp")}-{B1("bs_accomp")})'
                   f'+({V("bs_defrev")}-{B1("bs_defrev")})+({V("bs_ocl")}-{B1("bs_ocl")})'),
      ae=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_oca")}-{P("bs_oca")})+({V("bs_ap")}-{P("bs_ap")})+({V("bs_accomp")}-{P("bs_accomp")})'
                  f'+({V("bs_defrev")}-{P("bs_defrev")})+({V("bs_ocl")}-{P("bs_ocl")})'),
      note=('History: net cash from operating activities − net income − D&A − share-based compensation (deferred taxes and other non-cash items included). '
            'Forecast linked to the balance sheet: −Δ(receivables, other current assets) + Δ(payables & accrued, accrued compensation, deferred revenue, other).'))
    S('cf_cfo', 'Net cash provided by operating activities', 'line_b', 'm1', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Purchases of property and equipment', 'line', 'm1', data='cf_capex', flow=True,
      e26=lambda: f'={ACT("cf_capex")}-{PT("pt_capex")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}')
    S('cf_capsw', 'Capitalized internal-use software costs (separate line from FY2024)', 'line', 'm1', data='cf_capsw', flow=True,
      e26=lambda: f'={ACT("cf_capsw")}-{PT("pt_capsw")}', ae=lambda: f'=-{V("is_rev")}*{V("capsw_pct")}')
    S('cf_acq', 'Cash paid for acquisitions, net of cash acquired', 'line', 'm1', data='cf_acq', flow=True, e26=lambda: f'={ACT("cf_acq")}', ae=lambda: f'=-{V("m_spend")}')
    S('cf_divest', 'Proceeds from product-line asset sales & business divestitures', 'line', 'm1', data='cf_divest', flow=True, e26=lambda: f'={ACT("cf_divest")}', ae_in=0.0)
    S('cf_oinv', 'Marketable securities & other investing, net (derived)', 'line', 'm1', data='cf_oinv', flow=True, e26=lambda: f'={ACT("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Net cash used in investing activities', 'line_b', 'm1', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_bb', 'Repurchases of common stock', 'line', 'm1', data='cf_bb', flow=True, e26=lambda: f'={ACT("cf_bb")}-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='2026E: 9M actual (incl. the $1.5bn ASR prepaid in June 2026) + Q4 scenario input. 2027E+ = leverage plug (surplus cash returned until net debt / adjusted EBITDA reaches the target).')
    S('cf_div', 'Dividends paid', 'line', 'm1', data='cf_div', flow=True, e26=lambda: f'={ACT("cf_div")}', ae_in=0.0)
    S('cf_stock', 'Proceeds from issuance of stock under employee stock plans', 'line', 'm1', data='cf_stock', flow=True,
      e26=lambda: f'={ACT("cf_stock")}+{V0["stock_q4"]}', ae_in=V0['stock_ae'])
    S('cf_taxw', 'Taxes paid related to net share settlement of equity awards', 'line', 'm1', data='cf_taxw', flow=True,
      e26=lambda: f'={ACT("cf_taxw")}+{V0["taxw_q4"]}', ae=lambda: f'=-{V("is_sbc")}*{V("taxw_pct")}',
      note='Withholding taxes on vesting awards (mostly in Q1). 2027E+: % of share-based compensation (input).')
    S('cf_debt', 'Debt issued / (repaid), net — revolver, term loans, senior notes', 'line', 'm1', data='cf_debt', flow=True,
      e26=lambda: f'={ACT("cf_debt")}+({V("ds_total")}-{B1("ds_total")})', ae=lambda: f'={V("ds_net")}',
      note='Per the debt schedule: term-loan amortization, notes repaid at maturity / refinanced, revolver drawn or repaid to the minimum cash balance.')
    S('cf_ofin', 'Other financing, net (derived; incl. debt issuance costs)', 'line', 'm1', data='cf_ofin', flow=True, e26=lambda: f'={ACT("cf_ofin")}', ae_in=0.0)
    S('cf_cff', 'Net cash provided by (used in) financing activities', 'line_b', 'm1', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_bb")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of exchange rate changes on cash', 'line', 'm1', data='cf_fx', flow=True, e26=lambda: f'={ACT("cf_fx")}', ae_in=0.0)
    S('cf_net', 'Net change in cash and cash equivalents', 'line', 'm1', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")}),"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}')
    S('cf_beg', 'Cash — beginning of period', 'line', 'm1', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period', 'line_b', 'm1', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: beginning cash + net change = ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=0.15,0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},1)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")})<=0.15,0,ROUND(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")},1)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (company definition: CFO − capital expenditures incl. capitalized software)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")}+N({V("cf_capsw")}),"")')
    S('fcf_pub', '  Company-published free cash flow', 'memo', 'm1', data='fcf_pub', flow=True)
    S('fcf_div', '  of which: dividends paid deducted in the published figure (FY2013–Q2/17 definition)', 'memo', 'm1', data='fcf_div', flow=True)
    S('fcf_chk', '  Check: model vs company-published free cash flow + dividends deducted (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("fcf_pub")}),IF(ABS({V("fcf")}-({V("fcf_pub")}-N({V("fcf_div")})))<=0.15,0,ROUND({V("fcf")}-({V("fcf_pub")}-N({V("fcf_div")})),1)),"n/p")')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of revenue', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / non-GAAP net income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_tot', '  Capital expenditures incl. capitalized software (USDm)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),{V("cf_capex")}+N({V("cf_capsw")}),"")')
    S('capex_pct', '  Purchases of PP&E % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note='2027E+ input (FY2024–9M FY26 0.1–0.5%).')
    S('capsw_pct', '  Capitalized internal-use software % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capsw")}),IFERROR(-{V("cf_capsw")}/{V("is_rev")},""),"")',
      ae_in=V0['capsw_pct'], note='2027E+ input (FY2025 1.5%; 9M FY26 1.4%).')
    S('capex_dep', '  Capex incl. software / D&A (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("capex_tot")}),IFERROR(-{V("capex_tot")}/{V("d_dda")},""),"")')
    S('taxw_pct', '  Taxes on net share settlement % of share-based compensation', 'pct', 'pct',
      all=lambda: f'=IF(ISNUMBER({V("cf_taxw")}),IFERROR(-{V("cf_taxw")}/{V("d_sbc")},""),"")', ae_in=V0['taxw_pct'],
      note='FY2023 62%, FY2024 93%, FY2025 131% (share price at vesting). Input (assumption).')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E = Q4 from shares outstanding at 30-Jun-2026 (incl. the ASR final delivery); 2027E+ buybacks via the leverage plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})',
      note='Q4/26E at the share-price input (Q3 FY26 average repurchase price $1,148.84); 2027E+ grows at the appreciation input.')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = Q4)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_asr', '  ASR final delivery (m shares; prepaid in June 2026, no cash)', 'driver', 'm2', e26_in=V0['asr_final'], ae_in=0.0,
      note='$1.5bn ASR (5-Jun-2026): 1,055,103 initial shares ≈ 80% of the expected total; the remaining ~20% (≈0.264m) is assumed delivered at settlement in Q4 FY26 at the initial reference price (assumption; final count set by the VWAP).')
    S('bb_iss', '  Shares issued under equity plans (m)', 'driver', 'm2', e26_in=V0['iss_q4'], ae_in=V0['iss_ae'])
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from shares outstanding at 30-Jun-2026 (21.597m, Q3 FY26 10-Q).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}-{V("bb_asr")}+{V("bb_iss")}',
      ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}-{V("bb_asr")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=lambda: f'=IFERROR(({V("bb_sh")}+{V("bb_asr")})/{V("bb_beg")},0)', ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since Q4/26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}+{V("bb_asr")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONDENSED CONSOLIDATED BALANCE SHEET (as in the releases)', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Jun-2026 balance sheet + Q4 flows; 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm1', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}')
    S('bs_mkt', '  Marketable securities (current and noncurrent)', 'line', 'm1', data='bs_mkt', bs=True, e26=lambda: f'={B1("bs_mkt")}', ae=lambda: f'={P("bs_mkt")}')
    S('bs_ar', '  Accounts receivable, net', 'line', 'm1', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_oca', '  Prepaid expenses & other current assets (derived)', 'line', 'm1', data='bs_oca', bs=True, e26=lambda: f'={B1("bs_oca")}', ae=lambda: f'={P("bs_oca")}')
    S('bs_ppe', '  Property and equipment, net (incl. capitalized internal-use software)', 'line', 'm1', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-({V("cf_capex")}-{ACT("cf_capex")})-({V("cf_capsw")}-{ACT("cf_capsw")})-{QEc("d_dep")}',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("cf_capsw")}-{V("d_dep")}+{V("m_spend")}*{V("m_ppe")}',
      note='Roll-forward: prior − capex − capitalized software (negative cash flows) − depreciation & software amortization + acquired PP&E.')
    S('bs_gw', '  Goodwill & intangible assets, net', 'line', 'm1', data='bs_gw', bs=True,
      e26=lambda: f'={B1("bs_gw")}-{QEc("d_amort")}', ae=lambda: f'={P("bs_gw")}-{V("d_amort")}+{V("m_spend")}*(1-{V("m_ppe")})',
      note='Roll-forward: prior − amortization + acquisition spend (excl. PP&E) from the M&A lever.')
    S('bs_onca', '  Operating lease right-of-use assets, deferred taxes & other assets (derived)', 'line', 'm1', data='bs_onca', bs=True,
      e26=lambda: f'={B1("bs_onca")}', ae=lambda: f'={P("bs_onca")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_onca")}),"")')
    S('bs_l', "LIABILITIES AND STOCKHOLDERS' EQUITY (DEFICIT)", 'sub', 'gen')
    S('bs_ap', '  Accounts payable and other accrued liabilities', 'line', 'm1', data='bs_ap', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_app")}')
    S('bs_accomp', '  Accrued compensation and employee benefits', 'line', 'm1', data='bs_accomp', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_acp")}')
    S('bs_defrev', '  Deferred revenue', 'line', 'm1', data='bs_defrev', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_drp")}')
    S('bs_std', '  Current maturities on debt (incl. senior convertible notes FY2006–07)', 'line', 'm1', data='bs_std', bs=True,
      fc=lambda: f'={V("ds_mat")}', note='Term-loan installments and notes due in the following fiscal year (revolver borrowings are classified as long-term).')
    S('bs_ocl', '  Other current liabilities (derived)', 'line', 'm1', data='bs_ocl', bs=True, e26=lambda: f'={B1("bs_ocl")}', ae=lambda: f'={P("bs_ocl")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_ap")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term debt (revolver, term loan, senior notes; net of issuance costs)', 'line', 'm1', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_std")}')
    S('bs_ol', '  Operating lease liabilities & other liabilities (derived)', 'line', 'm1', data='bs_ol', bs=True,
      e26=lambda: f'={B1("bs_ol")}', ae=lambda: f'={P("bs_ol")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_ol")}),"")')
    S('bs_eq', "  Stockholders' equity (deficit)", 'line', 'm1', data='bs_eq', bs=True,
      e26=lambda: (f'={B1("bs_eq")}+{QEc("is_ni")}+{QEc("d_sbc")}+({V("cf_bb")}-{ACT("cf_bb")})+({V("cf_div")}-{ACT("cf_div")})+({V("cf_stock")}-{ACT("cf_stock")})'
                   f'+({V("cf_taxw")}-{ACT("cf_taxw")})'),
      ae=lambda: f'={P("bs_eq")}+{V("is_ni")}+{V("cf_sbc")}+{V("cf_bb")}+{V("cf_div")}+{V("cf_stock")}+{V("cf_taxw")}',
      note='+ net income + share-based compensation − repurchases − dividends + stock-plan proceeds − withholding taxes (OCI / FX translation held flat; the ASR settlement is a reclassification within equity).')
    S('bs_tle', "TOTAL LIABILITIES AND STOCKHOLDERS' EQUITY (DEFICIT)", 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_eq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=0.15,0,ROUND({V("bs_ta")}-{V("bs_tle")},1)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm1', hist=CHK('bs_ta', 'bs_ta_pub'))
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm1', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash vs cash-flow ending cash (should be 0)', 'check', 'm1', all=CHK('bs_cash', 'cf_end'))
    S('bs_shares', '  Memo: shares outstanding at period end (m; XBRL, as first filed)', 'memo', 'm1', data='bs_shares', bs=True, e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input; set at fiscal year-end levels)')
    S('wc_rev', '  Revenue — annualised (quarters × 4)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — receivables / revenue × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_app', '  Payables & other accrued % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_rev")},"")', e26_in=V0['wc']['ap'], ae_in=V0['wc']['ap'])
    S('wc_acp', '  Accrued compensation % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_accomp")}/{V("wc_rev")},"")', e26_in=V0['wc']['acc'], ae_in=V0['wc']['acc'])
    S('wc_drp', '  Deferred revenue % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_defrev")}/{V("wc_rev")},"")', e26_in=V0['wc']['dr'], ae_in=V0['wc']['dr'],
      note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables + other current assets − payables, accrued compensation, deferred revenue, other current liabilities)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_oca")}-{V("bs_ap")}-{V("bs_accomp")}-{V("bs_defrev")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm1', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; options & RSUs)', 'sched', 'm1', ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=V0['pxg'])
    S('ds_h', 'Debt schedule (senior notes and term loan repaid at maturity / per amortization; revolver drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (current maturities + long-term debt; carrying value)', 'sched', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_tl")}+{V("ds_rev")}',
      note=MAN['debt_2026_06_30']['source'])
    S('ds_notes', '  Senior notes (carrying value; 30-Jun-2026 = total debt − term loan − revolver)', 'sched', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("ds_tl")}),ISNUMBER({V("ds_rev")})),{V("ds_total")}-{V("ds_tl")}-{V("ds_rev")},"")',
      e26=lambda: f'={B1("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}+{V("ds_termout")}',
      note='$900m 4.00% due 15-Jun-2028; $1.5bn 6.00% due 15-May-2033; $1.0bn 6.25% due 15-Sep-2034 (the 5.25% 2018 notes were redeemed 26-Mar-2026).')
    S('ds_iss', '  New senior notes issued (input)', 'sched', 'm1', e26_in=0.0, ae_in={y: V0['iss_notes'].get(y, 0.0) for y in range(FYC + 1, FYL + 1)},
      note='FY2028: assumed refinancing of the June-2028 notes and the term-loan balance due May-2028 with new notes (assumption).')
    S('ds_repay', '  Senior notes repaid at maturity (input)', 'sched', 'm1', e26_in=0.0, ae_in={y: V0['repay_notes'].get(y, 0.0) for y in range(FYC + 1, FYL + 1)})
    S('ds_tl', '  Term loan (June-2026, $1.5bn; SOFR + 1.50–2.25%)', 'sched', 'm1', data='debt_tl',
      e26=lambda: f'={B1("ds_tl")}-{V("ds_tlr")}', ae=lambda: f'={P("ds_tl")}-{V("ds_tlr")}')
    S('ds_tlr', '  Term-loan amortization / repayment (input)', 'sched', 'm1', e26_in=V0['tl_rep'][FYC], ae_in={y: V0['tl_rep'].get(y, 0.0) for y in range(FYC + 1, FYL + 1)},
      note=MAN['debt_2026_06_30']['term_loan']['amortization'] + '.')
    S('ds_mat', '  Maturities in the following fiscal year (current maturities)', 'sched', 'm1', e26_in=V0['mat'][FYC], ae_in={y: V0['mat'][y] for y in range(FYC + 1, FYL + 1)})
    S('ds_pre', '  Cash before revolver draws / repayments (opening cash + CFO + CFI + buybacks, stock plans, withholding, other + FX − debt repaid + issued)', 'sched', 'm1',
      e26=lambda: (f'={B1("bs_cash")}+({V("cf_cfo")}-{ACT("cf_cfo")})+({V("cf_cfi")}-{ACT("cf_cfi")})+({V("cf_bb")}-{ACT("cf_bb")})+({V("cf_div")}-{ACT("cf_div")})'
                   f'+({V("cf_stock")}-{ACT("cf_stock")})+({V("cf_taxw")}-{ACT("cf_taxw")})+({V("cf_ofin")}-{ACT("cf_ofin")})+({V("cf_fx")}-{ACT("cf_fx")})'
                   f'-{V("ds_repay")}+{V("ds_iss")}-{V("ds_tlr")}'),
      ae=lambda: (f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_bb")}+{V("cf_div")}+{V("cf_stock")}+{V("cf_taxw")}+{V("cf_ofin")}+{V("cf_fx")}'
                  f'-{V("ds_repay")}+{V("ds_iss")}-{V("ds_tlr")}'))
    S('ds_min', '  Minimum cash balance', 'sched', 'm1', e26_in=V0['min_cash'], ae_in=V0['min_cash'])
    S('ds_rev_pre', '  Revolver needed before term-out (shortfall below the minimum cash balance drawn; surplus repays)', 'sched', 'm1',
      e26=lambda: f'=MAX(0,{B1("ds_rev")}+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_rev")}+{V("ds_min")}-{V("ds_pre")})')
    S('ds_rev_cap', '  Revolver balance kept at or below (term-out threshold; input)', 'sched', 'm1', ae_in=V0['rev_cap'])
    S('ds_termout', '  New senior notes issued to term out revolver draws above the threshold (financing assumption)', 'sched', 'm1', e26_in=0.0,
      ae=lambda: f'=MAX(0,{V("ds_rev_pre")}-{V("ds_rev_cap")})',
      note='Financing assumption: leverage-targeted buybacks are funded partly with debt; draws above the threshold are refinanced with new senior notes so the revolver stays within its $1.0bn commitment.')
    S('ds_rev', '  Revolving line of credit (year end)', 'sched', 'm1', data='debt_rev',
      e26=lambda: f'={V("ds_rev_pre")}', ae=lambda: f'={V("ds_rev_pre")}-{V("ds_termout")}',
      note='$1.0bn unsecured revolver (matures 13-May-2030, assumed extended); $710m drawn at 30-Jun-2026 (5.643%).')
    S('ds_head', '  Memo: revolver headroom vs the $1.0bn commitment (negative = would need other financing)', 'memo_calc', 'm1',
      e26=lambda: f'=1000-{V("ds_rev")}', ae=lambda: f'=1000-{V("ds_rev")}')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm1', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on opening senior notes %', 'sched', 'pct', ae_in=V0['r_notes'], note=V0['r_notes_note'])
    S('ds_r_tl', '  Interest rate on opening term loan %', 'sched', 'pct', ae_in=V0['r_tl'], note='30-Jun-2026: 5.863% (SOFR + margin); assumed to ease with SOFR.')
    S('ds_r_rev', '  Interest rate on opening revolver %', 'sched', 'pct', ae_in=V0['r_rev'], note='30-Jun-2026 weighted average 5.643%.')
    S('ds_fees', '  Credit-agreement fees & financing-cost amortization ($m)', 'sched', 'm1', ae_in=V0['fees'])
    S('ds_r_cash', '  Interest income yield on opening cash %', 'sched', 'pct', ae_in=V0['r_cash'])
    S('cov_x', '  Memo: total debt / adjusted EBITDA (x) vs the credit-agreement covenant (4.5x to Dec-2026, 4.0x to Dec-2027, 3.5x thereafter)', 'memo_calc', 'x2',
      e26=lambda: f'=IFERROR({V("ds_total")}/{V("r_adj")},"")', ae=lambda: f'=IFERROR({V("ds_total")}/{V("r_adj")},"")')
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / adjusted EBITDA, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end)', 'sched', 'm1',
      ae=lambda: f'={P("ds_total")}-{P("cf_end")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_stock")}-{V("cf_taxw")}-{V("cf_ofin")}-{V("cf_fx")}')
    S('lev_tgt', '  Target net debt = target leverage × adjusted EBITDA', 'sched', 'm1', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to target leverage', 'sched', 'm1', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash and debt capacity beyond the leverage target are returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of revenue', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_int', '  Net interest expense ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted EBITA after SBC)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBITA after SBC (adjusted EBITDA − depreciation − SBC)', 'line', 'm1', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Tax rate (non-GAAP)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("e_rate")}+0,0.25)')
    S('ra_nopat', 'NOPAT = Adjusted EBITA × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt (net of marketable securities)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', "  Total stockholders' equity (deficit)", 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − cash − marketable securities', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")}-N({V("bs_mkt")}),"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR(IF({V("ra_ic")}>0,{V("ra_nopat")}/{V("ra_ic")},"n/m"),"n/a")')
    S('ra_mg', '  Margin = Adjusted EBITA / Revenue', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Revenue / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBITA × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm1', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangible assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-{V("bs_gw")},"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. current debt)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})),"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR(IF({V("rn_nta")}>0,{V("rn_nopat")}/{V("rn_nta")},"n/m"),"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income', 'line', 'm1', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Stockholders' equity (deficit)", 'line', 'm1', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net income / Equity (n/m when equity is a deficit, FY2021+)', 'line', 'pct', ann=True,
      all=lambda: f'=IFERROR(IF({V("roe_eq")}>0,{V("roe_ni")}/{V("roe_eq")},"n/m"),"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash − marketable securities', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA', 'line', 'm1', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_gx', 'Total debt / adjusted EBITDA (x)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("ds_total")}/{V("r_adj")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interests (USDm; none)', 'line', 'm', e26_in=0.0, ae_in=0.0)
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Revenue', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Non-GAAP operating income', lambda: f'=IFERROR({V("v_ev")}/{V("o_adj")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (non-GAAP EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
