"""Row specification part 2: cash flow, buybacks, balance sheet, working capital, schedules, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum

def h26(key):   # 1H/26 actual for a flow row
    return f'(BW{R[key]}+BX{R[key]})'

def build_spec2(V0):
    S = add
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 1H/26 actual + 2H estimate; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net earnings (total, incl. discontinued operations)', 'line', 'm', data='cf_ni', flow=True, cf=True, fc=lambda: f'={V("is_ni")}',
      e26=lambda: f'={h26("cf_ni")}+BY{R["is_ni"]}+BZ{R["is_ni"]}')
    S('cf_adj', 'Adjustments:', 'sub', 'gen')
    S('cf_dep', '  Depreciation', 'line', 'm', data='cf_dep', flow=True, cf=True, fc=lambda: f'={V("d_dep")}',
      e26=lambda: f'={h26("cf_dep")}+BY{R["d_dep"]}+BZ{R["d_dep"]}')
    S('cf_amort', '  Amortization of intangible assets', 'line', 'm', data='cf_amort', flow=True, cf=True, fc=lambda: f'={V("is_amort")}',
      e26=lambda: f'={h26("cf_amort")}+BY{R["is_amort"]}+BZ{R["is_amort"]}')
    S('cf_sbc', '  Stock-based compensation', 'line', 'm', data='cf_sbc', flow=True, cf=True, fc=lambda: f'={V("is_sbc")}',
      e26=lambda: f'={h26("cf_sbc")}+BY{R["is_sbc"]}+BZ{R["is_sbc"]}')
    S('cf_def', '  Change in deferred income taxes', 'line', 'm', data='cf_def', flow=True, cf=True,
      e26=lambda: f'=N({h26("cf_def")})+{V0["def_tax_2h"]}', ae_in=V0['def_tax_ae'],
      note='Deferred tax benefit as book amortization of acquired intangibles exceeds tax amortization (FY25 −$440m; FY24 −$483m). 2H/26 and 2027E+ inputs.')
    S('cf_oth', '  Impairments, investment (gains) losses, inventory step-up & other operating items, net (derived)', 'line', 'm', data='cf_oth', flow=True, cf=True,
      e26=lambda: f'={h26("cf_oth")}', ae_in=0.0,
      note='2026E = 1H/26 actual; forecast other adjustments (Masimo inventory step-up) treated as working-capital / cash items; 2027E+ nil.')
    S('cf_wc', '  Changes in operating assets & liabilities (working capital), net', 'line', 'm', data='cf_wc', flow=True, cf=True,
      e26=lambda: (f'={h26("cf_wc")}-({V("bs_ar")}-BX{R["bs_ar"]})-({V("bs_inv")}-BX{R["bs_inv"]})+({V("bs_ap")}-BX{R["bs_ap"]})'
                   f'+({V("bs_acc")}-BX{R["bs_acc"]})'),
      ae=lambda: f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_inv")}-{P("bs_inv")})+({V("bs_ap")}-{P("bs_ap")})+({V("bs_acc")}-{P("bs_acc")})'
                 f'-({V("m_spend")}*0)',
      note='Linked to the balance sheet: −Δ(receivables, inventories) + Δ(payables, accrued expenses). Acquired working capital (StatLab, M&A lever) is excluded via the acquisition line.')
    S('cf_cfo', 'Net cash provided by operating activities', 'line_b', 'm', data='cf_cfo', flow=True, cf=True,
      fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Payments for additions to property, plant & equipment', 'line', 'm', data='cf_capex', flow=True, cf=True,
      e26=lambda: f'=-{PT("pt_capex")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}', note='2026E: FY26 capex point estimate. 2027E+: sales × capex %.')
    S('cf_disp', 'Proceeds from sales of property, plant & equipment', 'line', 'm', data='cf_disp', flow=True, cf=True,
      e26=lambda: f'=N({h26("cf_disp")})', ae_in=0.0)
    S('cf_acq', 'Cash paid for acquisitions', 'line', 'm', data='cf_acq', flow=True, cf=True,
      e26=lambda: f'={h26("cf_acq")}-{V("st_price")}', ae=lambda: f'=-{V("m_spend")}',
      note='2026E = 1H/26 actual (Masimo $9.84bn net of cash acquired) + StatLab (assumed paid at closing, end-2026). 2027E+: M&A lever.')
    S('cf_divb', 'Proceeds from sales of businesses / product lines', 'line', 'm', data='cf_div_bus', flow=True, cf=True,
      e26=lambda: f'=N({h26("cf_divb")})', ae_in=0.0)
    S('cf_oinv', 'Investments & other investing activities, net (derived)', 'line', 'm', data='cf_oinv', flow=True, cf=True,
      e26=lambda: f'={h26("cf_oinv")}', ae_in=V0['oinv_ae'])
    S('cf_cfi', 'Net cash used in investing activities', 'line_b', 'm', data='cf_cfi', flow=True, cf=True,
      fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_stock', 'Proceeds from issuance of common stock (stock-based compensation)', 'line', 'm', data='cf_stock', flow=True, cf=True,
      e26=lambda: f'={h26("cf_stock")}', ae_in=V0['stock_ae'])
    S('cf_divs', 'Payment of dividends', 'line', 'm', data='cf_divs', flow=True, cf=True,
      e26=lambda: f'={h26("cf_divs")}-(BY{R["dps"]}*BY{R["sh_basic"]}+BZ{R["dps"]}*BZ{R["sh_basic"]})',
      ae=lambda: f'=-{V("dps")}*{V("bb_beg")}', note='2027E+: dividends per share × beginning shares outstanding (avoids circularity with buybacks).')
    S('cf_bb', 'Payments for repurchase of common stock', 'line', 'm', data='cf_bb', flow=True, cf=True,
      e26=lambda: f'=N({h26("cf_bb")})-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='2026E = 1H/26 actual + 2H scenario amount; 2027E+ = leverage plug (surplus cash returned via buybacks once net debt / Adjusted EBITDA reaches the scenario floor).')
    S('cf_debt', 'Borrowings / (repayments), net (notes, commercial paper, credit facilities)', 'line', 'm', data='cf_debt', flow=True, cf=True,
      e26=lambda: f'={h26("cf_debt")}+({V("ds_total")}-BX{R["ds_total"]})', ae=lambda: f'={V("ds_total")}-{P("ds_total")}',
      note='Forecast = change in total debt per the debt schedule (scheduled note maturities, refinancing, commercial paper to a minimum cash balance).')
    S('cf_ofin', 'Spin-off distributions, equity offerings & other financing, net (derived)', 'line', 'm', data='cf_ofin', flow=True, cf=True,
      e26=lambda: f'={h26("cf_ofin")}', ae_in=V0['ofin_ae'])
    S('cf_cff', 'Net cash provided by (used in) financing activities', 'line_b', 'm', data='cf_cff', flow=True, cf=True,
      fc=lambda: f'=SUM({V("cf_stock")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of exchange rate changes on cash', 'line', 'm', data='cf_fx', flow=True, cf=True, e26=lambda: f'={h26("cf_fx")}', ae_in=0.0)
    S('cf_net', 'Net change in cash and equivalents', 'line', 'm', data='cf_net', flow=True, cf=True,
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}')
    S('cf_beg', 'Cash — beginning of period', 'line', 'm', data='cf_beg', cf=True, e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period', 'line_b', 'm', data='cf_end', cf=True, fc=lambda: f'={V("cf_beg")}+{V("cf_net")}',
      note='Cash and equivalents as presented in each statement (some spin-off years include cash of discontinued operations).')
    S('cf_chk1', '  Check: CFO + CFI + CFF + FX = change in cash (should be 0; ±0.6 rounding)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),IF(ABS({V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")})-{V("cf_net")})<=0.6,0,ROUND({V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")})-{V("cf_net")},1)),"")')
    S('cf_chk2', '  Check: beginning cash + change = ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_net")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=0.6,0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},1)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('cf_cfoc', '  Memo: operating cash flow — company FCF basis (continuing operations where presented)', 'memo', 'm', data='fcf_cfo', flow=True, fc=lambda: f'={V("cf_cfo")}')
    S('fcf_capx', '  Memo: capital expenditures — company FCF basis', 'memo', 'm', data='fcf_capex', flow=True, fc=lambda: f'={V("cf_capex")}')
    S('fcf_dsp', '  Memo: proceeds from PP&E sales — company FCF basis (not in the 2010–12 definition)', 'memo', 'm', data='fcf_disp', flow=True, fc=lambda: f'=N({V("cf_disp")})')
    S('fcf', 'Free cash flow (company definition: operating cash flow − capex + PP&E disposals)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("cf_cfoc")}),{V("cf_cfoc")}+N({V("fcf_capx")})+N({V("fcf_dsp")}),"")',
      note='Danaher definition (non-GAAP): operating cash flow (continuing operations from 2023) − capex + proceeds from PP&E sales; components as in the company FCF table where published, else the cash-flow statement.')
    S('fcf_pub', '  Memo: free cash flow as published', 'memo', 'm', data='fcf_pub', flow=True)
    S('fcf_chk', '  Check: model FCF vs published (should be 0; differences = discontinued-operations cash flows)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("fcf_pub")}),IF(ABS({V("fcf")}-{V("fcf_pub")})<=1,0,ROUND({V("fcf")}-{V("fcf_pub")},0)),"n/p")')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of sales', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net earnings conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note='2027E+: input (2024 5.8%, 2025 4.7%; normalising after the bioprocessing capacity build-out).')
    S('capex_dda', '  Capex / depreciation (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("d_dep")},""),"")')
    blank()

    # ------------------------------------------------------------------ BUYBACKS
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E starts from shares outstanding at 26-Jun-2026; 2H/26 buyback per scenario')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})',
      note='2026E = current share price (valuation input); appreciates with the share-price input.')
    S('bb_cash', '  Buyback cash deployed (USDm)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}',
      note='2026E row = 2H/26 buyback only (1H/26 repurchases — $903m in Q2 — already in the Q2 share count).')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans (m)', 'driver', 'm2', e26_in=0.8, ae_in=1.8)
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'=BX{R["bs_shares"]}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from shares outstanding at 26-Jun-2026 (10-Q).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1',
      e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since 2H/26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET', 'section',
      note='BS FORECAST — 2026E rolled forward from the 26-Jun-2026 balance sheet (Q2/26) + 2H flows; 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and equivalents', 'line', 'm', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}')
    S('bs_ar', '  Trade accounts receivable, net', 'line', 'm', data='bs_ar', bs=True,
      fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365+{V("acq_wc")}', note='Receivables = annualised sales × DSO / 365.')
    S('bs_inv', '  Inventories', 'line', 'm', data='bs_inventories', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dio")}/365')
    S('bs_oca', '  Prepaid expenses & other current assets (incl. assets held for sale; derived)', 'line', 'm', data='bs_oca', bs=True,
      e26=lambda: f'=BX{R["bs_oca"]}', ae=lambda: f'={P("bs_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_ppe', '  Property, plant & equipment, net', 'line', 'm', data='bs_ppe', bs=True,
      e26=lambda: f'=BX{R["bs_ppe"]}-({V("cf_capex")}-{h26("cf_capex")})-(BY{R["d_dep"]}+BZ{R["d_dep"]})+{V("st_price")}*0.05',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("d_dep")}+{V("m_spend")}*{V("m_ppe")}',
      note='PP&E roll-forward: prior − capex (negative cash flow) − depreciation + acquired PP&E (StatLab 5% of price; M&A lever).')
    S('bs_onca', '  Other long-term assets (incl. ROU, investments; derived)', 'line', 'm', data='bs_onca', bs=True,
      e26=lambda: f'=BX{R["bs_onca"]}-({V("cf_oinv")}-{h26("cf_oinv")})', ae=lambda: f'={P("bs_onca")}-{V("cf_oinv")}',
      note='+ net investments (other investing cash flows).')
    S('bs_gw', '  Goodwill', 'line', 'm', data='bs_goodwill', bs=True,
      e26=lambda: f'=BX{R["bs_gw"]}+{V("st_price")}*(1-0.05-{V("st_intp")})',
      ae=lambda: f'={P("bs_gw")}+{V("m_spend")}*(1-{V("m_ppe")}-{V("m_intp")})')
    S('bs_int', '  Other intangible assets, net', 'line', 'm', data='bs_intangibles', bs=True,
      e26=lambda: f'=BX{R["bs_int"]}-(BY{R["is_amort"]}+BZ{R["is_amort"]})+{V("st_price")}*{V("st_intp")}',
      ae=lambda: f'={P("bs_int")}-{V("is_amort")}+{V("m_spend")}*{V("m_intp")}',
      note='Intangibles roll-forward: prior − amortization + acquired intangibles (StatLab; M&A lever).')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_ppe")}:{V("bs_int")}),"")')
    S('bs_l', "LIABILITIES AND STOCKHOLDERS' EQUITY", 'sub', 'gen')
    S('bs_cdebt', '  Notes payable & current portion of long-term debt', 'line', 'm', data='bs_st_debt', bs=True,
      fc=lambda: f'=MIN({V("ds_total")},-{nextc()}{R["ds_mat"]})', note="Forecast: next year's scheduled note maturities.")
    S('bs_ap', '  Trade accounts payable', 'line', 'm', data='bs_ap', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dpo")}/365')
    S('bs_acc', '  Accrued expenses & other liabilities', 'line', 'm', data='bs_accrued', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_accp")}')
    S('bs_ocl', '  Other current liabilities (liabilities of discontinued operations / held for sale; derived)', 'line', 'm', data='bs_ocl', bs=True,
      e26=lambda: f'=N(BX{R["bs_ocl"]})', ae=lambda: f'=N({P("bs_ocl")})')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_cdebt")}:{V("bs_ocl")}),"")')
    S('bs_oltl', '  Other long-term liabilities (incl. deferred taxes, pensions, leases; derived)', 'line', 'm', data='bs_oncl', bs=True,
      e26=lambda: f'=BX{R["bs_oltl"]}+({V("cf_def")}-N({h26("cf_def")}))', ae=lambda: f'={P("bs_oltl")}+{V("cf_def")}')
    S('bs_ltd', '  Long-term debt', 'line', 'm', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_cdebt")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+{V("bs_oltl")}+{V("bs_ltd")},"")')
    S('bs_e', "Stockholders' equity:", 'sub', 'gen')
    S('bs_pref', '  Preferred stock (mandatory convertible, 2019–2023)', 'line', 'm', data='bs_pref', bs=True, fc=lambda: '=0')
    S('bs_cap', '  Common stock & additional paid-in capital (derived)', 'line', 'm', data='bs_cap', bs=True,
      e26=lambda: f'=BX{R["bs_cap"]}+({V("cf_sbc")}-{h26("cf_sbc")})+({V("cf_stock")}-{h26("cf_stock")})+({V("cf_ofin")}-{h26("cf_ofin")})',
      ae=lambda: f'={P("bs_cap")}+{V("cf_sbc")}+{V("cf_stock")}+{V("cf_ofin")}',
      note='+ stock-based compensation + stock-plan proceeds + other financing (tax withholding on equity awards, debt costs).')
    S('bs_treas', '  Treasury stock', 'line', 'm', data='bs_treasury', bs=True,
      e26=lambda: f'=N(BX{R["bs_treas"]})+({V("cf_bb")}-N({h26("cf_bb")}))', ae=lambda: f'={P("bs_treas")}+{V("cf_bb")}',
      note='Repurchased shares held in treasury: + repurchases (negative).')
    S('bs_re', '  Retained earnings', 'line', 'm', data='bs_retained', bs=True,
      e26=lambda: f'=BX{R["bs_re"]}+BY{R["is_ni"]}+BZ{R["is_ni"]}+({V("cf_divs")}-{h26("cf_divs")})',
      ae=lambda: f'={P("bs_re")}+{V("is_ni")}+{V("cf_divs")}', note='+ net earnings − dividends.')
    S('bs_aoci', '  Accumulated other comprehensive income (loss)', 'line', 'm', data='bs_aoci', bs=True,
      e26=lambda: f'=BX{R["bs_aoci"]}+({V("cf_fx")}-{h26("cf_fx")})', ae=lambda: f'={P("bs_aoci")}')
    S('bs_weq', "Total Danaher stockholders' equity", 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cap")}),SUM({V("bs_pref")}:{V("bs_aoci")}),"")')
    S('bs_nci', '  Noncontrolling interests', 'line', 'm', data='bs_nci', bs=True, e26=lambda: f'=N(BX{R["bs_nci"]})', ae=lambda: f'=N({P("bs_nci")})')
    S('bs_teq', "Total stockholders' equity", 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_weq")}),{V("bs_weq")}+N({V("bs_nci")}),"")')
    S('bs_tle', "TOTAL LIABILITIES AND STOCKHOLDERS' EQUITY", 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E; ±0.6 rounding)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=0.6,0,ROUND({V("bs_ta")}-{V("bs_tle")},1)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=0.6,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},1)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash vs cash-flow ending cash (should be 0; differences = cash of discontinued operations / held for sale)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}-{V("cf_end")})<=0.6,0,ROUND({V("bs_cash")}-{V("cf_end")},1)),"")')
    S('bs_shares', '  Memo: common shares outstanding at period end (m)', 'memo', 'm1', data='bs_shares', bs=True,
      e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input)')
    S('wc_rev', '  Sales — annualised (quarters × 4)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_cogs', '  Cost of sales — annualised', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_cogs")}*{4 if CTX.col.q else 1},"")')
    S('acq_wc', '  Acquired receivables (StatLab, M&A lever; enters with the acquisition, not through operating cash flow)', 'line', 'm', e26_in=0.0, ae_in=0.0)
    S('wc_dso', '  DSO — receivables / sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")',
      e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_dio', '  Inventory days — inventories / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_inv")}/{V("wc_cogs")}*365,"")',
      e26_in=V0['wc']['dio'], ae_in=V0['wc']['dio'])
    S('wc_dpo', '  Payable days — payables / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_cogs")}*365,"")',
      e26_in=V0['wc']['dpo'], ae_in=V0['wc']['dpo'])
    S('wc_accp', '  Accrued expenses & other liabilities % of sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_acc")}/{V("wc_rev")},"")',
      e26_in=V0['wc']['acc'], ae_in=V0['wc']['acc'], note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables + inventories − payables − accrued expenses)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_inv")}-{V("bs_ap")}-N({V("bs_acc")}),"")')
    S('wc_nwc_p', '  NWC % of sales', 'pct', 'pct', all=lambda: f'=IFERROR({V("wc_nwc")}/{V("wc_rev")},"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm', all=lambda: (f'=IFERROR({V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppa_h', 'Masimo acquisition — consideration & preliminary purchase-price allocation (Q2-26 10-Q, closing-quarter column)', 'sub', 'gen')
    for k, lab in [('cons', 'Cash consideration, net of cash acquired'), ('stock', 'Replacement equity awards (non-cash consideration)'),
                   ('ar', 'Trade accounts receivable'), ('inv', 'Inventories (incl. fair-value step-up)'), ('ppe', 'Property, plant & equipment'),
                   ('int', 'Other intangible assets (technology, customer relationships, trade names)'), ('gw', 'Goodwill (Diagnostics)'),
                   ('ap', 'Trade accounts payable'), ('dtl', 'Deferred tax liabilities'), ('oth', 'Other assets & liabilities, net')]:
        S(f'ppa_{k}', f'  {lab}', 'sched', 'm', data=f'ppa_{k}', ppa=True)
    S('ppa_life', '  Weighted useful life of acquired intangibles (years; implied by amortization guidance)', 'sched', 'gen', data='ppa_life', ppa=True,
      note='Not disclosed. Implied by the FY26 amortization guidance (~$1.9bn incl. Masimo vs ~$1.7bn pre-deal schedule) and Q3 guidance (~$500m).')
    S('ppa_chk', '  Check: assets acquired − liabilities assumed − consideration (should be 0)', 'check', 'm1',
      hist=lambda: (f'=IF(ISNUMBER({V("ppa_cons")}),ROUND(N({V("ppa_ar")})+N({V("ppa_inv")})+N({V("ppa_ppe")})+N({V("ppa_int")})+N({V("ppa_gw")})'
                    f'+N({V("ppa_ap")})+N({V("ppa_dtl")})+N({V("ppa_oth")})-{V("ppa_cons")}-N({V("ppa_stock")}),0),"")'))
    S('rf_h', 'Asset roll-forwards & non-cash items', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares)', 'sched', 'm1', ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.07)
    S('ds_h', 'Debt schedule (scheduled note maturities + commercial paper / facilities to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (current + long-term)', 'sched', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_cdebt")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_fac")}', note=V0['debt_note'])
    S('ds_mat', '  Scheduled note maturities (input, negative)', 'sched', 'm', e26_in=V0['mat'][2026], ae_in={y: V0['mat'][y] for y in (2027, 2028, 2029, 2030)},
      note=V0['mat_note'])
    S('ds_refp', '  % of scheduled maturities refinanced (input)', 'sched', 'pct', e26_in=V0['refi_pct'][2026], ae_in={y: V0['refi_pct'][y] for y in (2027, 2028, 2029, 2030)},
      note='100% = maturity refinanced with new notes; otherwise repaid from cash / commercial paper.')
    S('ds_refi', '  Refinancing issuance', 'sched', 'm', e26=lambda: f'=-{V("ds_mat")}*{V("ds_refp")}', ae=lambda: f'=-{V("ds_mat")}*{V("ds_refp")}')
    S('ds_notes', '  Senior notes outstanding (year end)', 'sched', 'm', data='ds_notes', bs=True,
      e26=lambda: f'=BX{R["ds_notes"]}+{V("ds_mat")}+{V("ds_refi")}', ae=lambda: f'={P("ds_notes")}+{V("ds_mat")}+{V("ds_refi")}')
    S('ds_pre', '  Cash before commercial paper (opening cash + CFO + CFI + non-debt financing + FX + scheduled note flows)', 'sched', 'm',
      e26=lambda: (f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_stock")}+{V("cf_divs")}+{V("cf_bb")}+{V("cf_ofin")}+{V("cf_fx")}'
                   f'+{h26("cf_debt")}+(BX{R["ds_notes"]}-BX{R["ds_total"]})+{V("ds_mat")}+{V("ds_refi")}+BX{R["ds_total"]}-BX{R["ds_notes"]}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_stock")}+{V("cf_divs")}+{V("cf_bb")}+{V("cf_ofin")}+{V("cf_fx")}+{V("ds_mat")}+{V("ds_refi")}')
    S('ds_min', '  Minimum cash balance', 'sched', 'm', e26_in=V0['min_cash'], ae_in=V0['min_cash'])
    S('ds_fac', '  Commercial paper & credit facilities outstanding (year end)', 'sched', 'm', data='ds_fac', bs=True,
      e26=lambda: f'=MAX(0,BX{R["ds_fac"]}+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_fac")}+{V("ds_min")}-{V("ds_pre")})',
      note='Drawn / repaid so that cash = minimum balance; surplus cash first repays commercial paper, then accumulates (or funds buybacks via the leverage plug).')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm', e26=lambda: f'=IFERROR({V("ds_total")}-BV{R["ds_total"]},"")',
      ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on senior notes (opening balance) %', 'sched', 'pct', ae_in=V0['r_notes'], note=V0['r_notes_note'])
    S('ds_r_fac', '  Interest rate on commercial paper %', 'sched', 'pct', ae_in=V0['r_fac'])
    S('ds_r_cash', '  Interest income yield on opening cash %', 'sched', 'pct', ae_in=0.03)
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a minimum net debt / Adjusted EBITDA, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Minimum net debt / Adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end)', 'sched', 'm',
      ae=lambda: f'={P("ds_notes")}+{P("ds_fac")}-{P("cf_end")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_divs")}-{V("cf_stock")}-{V("cf_ofin")}-{V("cf_fx")}')
    S('lev_tgt', '  Target minimum net debt = min. leverage × Adjusted EBITDA', 'sched', 'm', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to minimum leverage', 'sched', 'm', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash beyond the leverage floor is returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of sales', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_amort', '  Amortization % of sales', 'pct', 'pct', all=ratio('is_amort', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on Adjusted EBIT, i.e. after acquired-intangible amortization)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT (Adjusted EBITDA − D&A)', 'line', 'm', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate (actual)', 'line', 'pct', ann=True, all=lambda: f'={V("is_etr")}')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity incl. NCI', 'line', 'm', ann=True, all=lambda: f'={V("bs_teq")}')
    S('ra_nd', '  Net debt = Total debt − Cash', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Sales', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Sales / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − effective tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & acquired intangible assets', 'line', 'm', ann=True, all=lambda: f'=-({V("bs_gw")}+{V("bs_int")})')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. debt)', 'line', 'm', ann=True, all=lambda: f'=-({V("bs_tcl")}-N({V("bs_cdebt")}))')
    S('rn_nta', '  = Net tangible assets', 'line', 'm', ann=True, all=lambda: f'=SUM({V("rn_ta")}:{V("rn_nibcl")})')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net earnings attributable to common stockholders', 'line', 'm', ann=True, all=lambda: f'={V("is_nic")}')
    S('roe_eq', "Danaher stockholders' equity", 'line', 'm', ann=True, all=lambda: f'={V("bs_weq")}')
    S('roe', 'ROE = Net earnings / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash', 'line', 'm', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA (model definition; 2026E pro forma Masimo full year)', 'line', 'm', ann=True, all=lambda: f'={V("r_adj_pf")}')
    S('lv_x', 'Net debt / Adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+(BX{R["sh_dil"]}-BX{R["sh_basic"]})',
      ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interests (USDm)', 'line', 'm', e26=lambda: f'=N({V("bs_nci")})', ae=lambda: f'=N({V("bs_nci")})')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")',
      ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Sales', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted operating profit', lambda: f'=IFERROR({V("v_ev")}/{V("o_adj")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted, continuing)', lambda: f'=IFERROR({V("v_px")}/{V("eps_cont")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        nf = 'pct' if k in ('v_fcfy', 'v_dy') else 'x'
        S(k, lab, 'line', nf, e26=f, ae=f)

_NEXT = {'CA': 'CB', 'CB': 'CC', 'CC': 'CD', 'CD': 'CE', 'CE': None}
def nextc():
    n = _NEXT.get(CTX.col.c)
    return n or 'CE'
