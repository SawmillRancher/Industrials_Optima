"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules, ratios, valuation.
Forecast columns: annual only (2026E = 1H/26 actual + 2H estimate; the Q3/Q4-26E columns are not filled below the income statement)."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, H1, B1, QA

def build_spec2(V0):
    S = add
    def h2(key): return f'({V(key)}-{H1(key)})'          # 2H/26E flow inside a 2026E column
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENTS OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 1H/26 actual + 2H estimate; quarters as published — three-month statements in every release)')
    S('cf_ni', 'Net income', 'line', 'm', data='cf_ni', flow=True, fc=lambda: f'={V("is_ni")}')
    S('cf_adj', 'Non-cash items:', 'sub', 'gen')
    S('cf_dda', '  Depreciation and amortization', 'line', 'm', data='cf_dda', flow=True, fc=lambda: f'={V("is_dda")}')
    S('cf_sbc', '  Share-based compensation', 'line', 'm', data='cf_sbc', flow=True, fc=lambda: f'={V("is_sbc")}')
    S('cf_def', '  Deferred income taxes', 'line', 'm', data='cf_def', flow=True, e26=lambda: f'={H1("cf_def")}', ae_in=0.0,
      note='2H/26E and 2027E+: nil (assumption; the 2025-26 valuation-allowance charge and release were non-cash and are not forecast).')
    S('cf_wc', '  Working capital and other operating items, net (derived)', 'line', 'm', data='cf_wc', flow=True,
      e26=lambda: (f'={H1("cf_wc")}-({V("bs_ar")}-{B1("bs_ar")})-({V("bs_oca")}-{B1("bs_oca")})+({V("bs_ap")}-{B1("bs_ap")})+({V("bs_ocl")}-{B1("bs_ocl")})'),
      ae=lambda: f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_oca")}-{P("bs_oca")})+({V("bs_ap")}-{P("bs_ap")})+({V("bs_ocl")}-{P("bs_ocl")})',
      note=('History: net cash from operating activities − net income − D&A − share-based compensation − deferred taxes (incl. unrealized investment gains / losses '
            'and other non-cash items). Forecast linked to the balance sheet: −Δ(receivables, other current assets) + Δ(payables, accrued and other current liabilities).'))
    S('cf_cfo', 'Net cash provided by operating activities', 'line_b', 'm', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Purchases of property and equipment (net of proceeds relating to property and equipment, 2022–23)', 'line', 'm', data='cf_capex', flow=True,
      e26=lambda: f'=-({PT("pt_capex")}+{V("cf_lease")})', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='2026E: guidance mid-point ($130–145bn, incl. principal payments on finance leases) less finance-lease principal. 2027E+: revenue × capex % (scenario lever).')
    S('cf_ms', 'Marketable securities — purchases, sales and maturities, net', 'line', 'm', data='cf_ms', flow=True, e26=lambda: f'={H1("cf_ms")}', ae_in=0.0,
      note='Forecast: portfolio held at the 30-Jun-2026 level (assumption).')
    S('cf_nme', 'Purchases of non-marketable equity investments', 'line', 'm', data='cf_nme', flow=True, e26=lambda: f'={H1("cf_nme")}', ae_in=0.0,
      note='2025: Scale AI ($14.3bn) among $18.3bn of purchases. Forecast: none assumed after 1H/26.')
    S('cf_acq', 'Acquisitions of businesses and intangible assets', 'line', 'm', data='cf_acq', flow=True, e26=lambda: f'={H1("cf_acq")}', ae=lambda: f'=-{V("m_spend")}')
    S('cf_oinv', 'Other investing activities (incl. held-for-sale assets; derived)', 'line', 'm', data='cf_oinv', flow=True, e26=lambda: f'={H1("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Net cash used in investing activities', 'line_b', 'm', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_bb', 'Repurchases of Class A common stock', 'line', 'm', data='cf_bb', flow=True, e26=lambda: f'={H1("cf_bb")}-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='2026E: 1H actual (nil) + 2H scenario input. 2027E+: leverage plug (cash returned while net debt / adjusted EBITDA is below the ceiling).')
    S('cf_div', 'Payments for dividends and dividend equivalents', 'line', 'm', data='cf_div', flow=True,
      e26=lambda: f'={H1("cf_div")}-{QA(Q3E, "dps")}*{QA(Q3E, "sh_basic")}-{QA(Q4E, "dps")}*{QA(Q4E, "sh_basic")}', ae=lambda: f'=-{V("dps")}*{V("bb_beg")}',
      note='Dividends = DPS × shares (2027E+: beginning shares, so not circular with plug-driven buybacks).')
    S('cf_netshare', 'Taxes paid related to net share settlement of equity awards', 'line', 'm', data='cf_netshare', flow=True,
      e26=lambda: f'={H1("cf_netshare")}-({V("d_sbc")}-{H1("d_sbc")})*{V0["ns_r"]}', ae=lambda: f'=-{V("d_sbc")}*{V0["ns_r"]}',
      note=f'Forecast: share-based compensation × {V0["ns_r"]:.0%} (FY2025 ratio of net-share-settlement taxes to share-based compensation).')
    S('cf_debt', 'Long-term debt issued / (repaid), net', 'line', 'm', data='cf_debt', flow=True,
      e26=lambda: f'={H1("cf_debt")}+{V("ds_total")}-{B1("ds_total")}', ae=lambda: f'={V("ds_net")}',
      note='Per the debt schedule: notes repaid at maturity and refinanced; commercial paper / incremental notes drawn or repaid to the minimum cash balance.')
    S('cf_lease', 'Principal payments on finance (capital) leases', 'line', 'm', data='cf_lease', flow=True, e26=lambda: f'=2*{H1("cf_lease")}', ae_in=V0['lease'],
      note='2026E: 2 × 1H actual (assumption). 2027E+: input (part of the company\'s capital-expenditure measure).')
    S('cf_eqiss', 'Proceeds from issuance of common / preferred stock (IPO 2012)', 'line', 'm', data='cf_eqiss', flow=True, e26=lambda: f'={H1("cf_eqiss")}', ae_in=0.0)
    S('cf_ofin', 'Other financing activities (derived)', 'line', 'm', data='cf_ofin', flow=True, e26=lambda: f'={H1("cf_ofin")}', ae_in=0.0)
    S('cf_cff', 'Net cash provided by (used in) financing activities', 'line_b', 'm', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_bb")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of exchange rate changes on cash', 'line', 'm', data='cf_fx', flow=True, e26=lambda: f'={H1("cf_fx")}', ae_in=0.0)
    S('cf_net', 'Net change in cash, cash equivalents and restricted cash', 'line', 'm', flow=True,
      all=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")}),"")')
    S('cf_beg', 'Cash — beginning of period (incl. restricted cash from 2018)', 'line', 'm', data='cf_beg', fc=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period (incl. restricted cash from 2018)', 'line_b', 'm', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: beginning cash + CFO + CFI + CFF + FX = ending cash (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},1),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),ROUND(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")},1),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('capex_all', 'Capital expenditures incl. principal payments on finance leases (company measure from 2019; model before)', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),-{V("cf_capex")}-N({V("cf_lease")}),"")')
    S('cf_capex_all', '  Capex incl. finance leases (negative, for the DCF)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("capex_all")}),-{V("capex_all")},"")')
    S('fcf_cl', '  Memo: property and equipment acquired under capital leases (deducted in the company FCF, 2013–14)', 'memo', 'm', data='fcf_cl', flow=True)
    S('fcf', 'Free cash flow (company definition in force)', 'total', 'm', flow=True, hist=lambda: FCF(CTX.col),
      fc=lambda: f'={V("cf_cfo")}+{V("cf_capex")}+{V("cf_lease")}')
    S('fcf_pub', '  Company-published free cash flow', 'memo', 'm', data='fcf_pub', flow=True)
    S('fcf_chk', '  Check: model vs company-published free cash flow (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("fcf_pub")}),ROUND({V("fcf")}-{V("fcf_pub")},1),"n/p")')
    S('fcf_def', '  Definition / basis (free cash flow)', 'text', 'gen')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of revenue', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net income (current definition) %', 'pct', 'pct', all=ratio('fcf', 'e_curni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Purchases of property and equipment % of revenue', 'pct', 'pct',
      all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")', ae=lambda: '=' + CH(SC['CAPEX'][CTX.col.year]),
      note='2027E+: scenario lever (AI data centers and servers; company capital-expenditure guidance only for the current year).')
    S('capex_all_pct', '  Capex incl. finance leases % of revenue', 'pct', 'pct', all=ratio('capex_all', 'is_rev'))
    S('capex_dda', '  Capex incl. finance leases / D&A (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("capex_all")}),IFERROR({V("capex_all")}/{V("d_dda")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E = 2H from shares outstanding at 30-Jun-2026; 2027E+ buybacks via the leverage plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = 2H)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans, net of shares withheld for taxes (m)', 'driver', 'm2', e26_in=V0['iss_2h'], ae_in=V0['iss_ae'],
      note=V0['iss_note'])
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from Class A + Class B shares outstanding at 30-Jun-2026 (Q2-26 10-Q balance sheet).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since 2H/26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONDENSED CONSOLIDATED BALANCE SHEETS', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Jun-2026 balance sheet + 2H flows; 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}-{V("bs_rcash")}')
    S('bs_ms', '  Marketable securities', 'line', 'm', data='bs_ms', bs=True, e26=lambda: f'={B1("bs_ms")}-{h2("cf_ms")}', ae=lambda: f'={P("bs_ms")}-{V("cf_ms")}')
    S('bs_ar', '  Accounts receivable, net', 'line', 'm', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_oca', '  Prepaid expenses and other current assets (incl. restricted cash; income tax refundable 2012)', 'line', 'm', data='bs_oca', bs=True,
      e26=lambda: f'={B1("bs_oca")}', ae=lambda: f'={P("bs_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_nme', '  Non-marketable equity investments (separate line from 2020)', 'line', 'm', data='bs_nme', bs=True,
      e26=lambda: f'={B1("bs_nme")}-{h2("cf_nme")}', ae=lambda: f'={P("bs_nme")}-{V("cf_nme")}')
    S('bs_ppe', '  Property and equipment, net', 'line', 'm', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-{h2("cf_capex")}-{h2("cf_lease")}-({V("d_dda")}-{H1("d_dda")})',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("cf_lease")}-({V("d_dda")}-{V("m_amort")})',
      note='Roll-forward: prior − purchases of P&E (negative cash flow) + finance-lease additions (assumed = principal paid) − depreciation.')
    S('bs_rou', '  Operating lease right-of-use assets (from 2019)', 'line', 'm', data='bs_rou', bs=True, e26=lambda: f'={B1("bs_rou")}', ae=lambda: f'={P("bs_rou")}',
      note='Held flat with the lease liabilities (operating lease cost sits inside costs and expenses).')
    S('bs_gw', '  Goodwill and intangible assets, net', 'line', 'm', data='bs_gw', bs=True,
      e26=lambda: f'={B1("bs_gw")}-{h2("cf_acq")}', ae=lambda: f'={P("bs_gw")}-{V("cf_acq")}-{V("m_amort")}')
    S('bs_onca', '  Other assets (incl. long-term restricted cash; derived)', 'line', 'm', data='bs_onca', bs=True, e26=lambda: f'={B1("bs_onca")}', ae=lambda: f'={P("bs_onca")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_nme")}:{V("bs_onca")}),"")')
    S('bs_l', "LIABILITIES AND STOCKHOLDERS' EQUITY", 'sub', 'gen')
    S('bs_ap', '  Accounts payable', 'line', 'm', data='bs_ap', bs=True, fc=lambda: f'={V("capex_all")}*{V("wc_app")}')
    S('bs_std', '  Current portion of capital lease obligations (to 2018)', 'line', 'm', data='bs_std', bs=True, fc=lambda: '=0')
    S('bs_ocl', '  Accrued expenses and other current liabilities (incl. partners payable, deferred revenue, operating lease liabilities)', 'line', 'm',
      data='bs_ocl', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_oclp")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_ap")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term debt (senior notes from 2022; term loan 2010; capital leases to 2018)', 'line', 'm', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}')
    S('bs_oll', '  Operating lease liabilities, non-current (from 2019)', 'line', 'm', data='bs_oll', bs=True, e26=lambda: f'={B1("bs_oll")}', ae=lambda: f'={P("bs_oll")}')
    S('bs_ol', '  Long-term income taxes and other liabilities (derived)', 'line', 'm', data='bs_ol', bs=True,
      e26=lambda: f'={B1("bs_ol")}+{h2("cf_def")}', ae=lambda: f'={P("bs_ol")}+{V("cf_def")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_ol")}),"")')
    S('bs_eq', "  Stockholders' equity (incl. convertible preferred stock pre-IPO)", 'line', 'm', data='bs_eq', bs=True,
      e26=lambda: (f'={B1("bs_eq")}+{h2("cf_ni")}+{h2("cf_div")}+{h2("cf_bb")}+{h2("cf_sbc")}+{h2("cf_netshare")}+{h2("cf_eqiss")}'),
      ae=lambda: f'={P("bs_eq")}+{V("cf_ni")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_sbc")}+{V("cf_netshare")}+{V("cf_eqiss")}',
      note='+ net income − dividends − repurchases + share-based compensation − taxes on net share settlement + stock issued (OCI held flat). Repurchased shares are retired.')
    S('bs_tle', "TOTAL LIABILITIES AND STOCKHOLDERS' EQUITY", 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_eq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),ROUND({V("bs_ta")}-{V("bs_tle")},1),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),ROUND({V("bs_ta")}-{V("bs_ta_pub")},1),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs_ta', bs=True)
    S('bs_rcash', '  Memo: restricted cash (cash-flow cash − balance-sheet cash; in prepaid / other assets; cash-flow statement includes it from 2018)', 'memo_calc', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("cf_end")}),ISNUMBER({V("bs_cash")})),{V("cf_end")}-{V("bs_cash")},"")', e26=lambda: f'={B1("bs_rcash")}', ae=lambda: f'={P("bs_rcash")}',
      note='Held at the 30-Jun-2026 level in the forecast ($13.8bn, mostly long-term).')
    S('bs_chk_cash', '  Check: BS cash + restricted cash vs cash-flow ending cash (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),ROUND({V("bs_cash")}+{V("bs_rcash")}-{V("cf_end")},1),"")')
    S('bs_shares', '  Memo: Class A + Class B shares outstanding at period end (m)', 'memo', 'm', data='sh_out', bs=True, e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    S('bs_cms', '  Memo: cash, cash equivalents and marketable securities', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_cash")}+{V("bs_ms")},"")')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input; year-end levels)')
    S('wc_rev', '  Revenue — annualised (quarters × 4)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — receivables / revenue × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_app', '  Accounts payable % of capex incl. finance leases (capex payables dominate)', 'pct', 'pct',
      hist=lambda: f'=IFERROR({V("bs_ap")}/({V("capex_all")}*{4 if CTX.col.q else 1}),"")', e26_in=V0['wc']['app'], ae_in=V0['wc']['app'])
    S('wc_oclp', '  Accrued expenses and other current liabilities % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")',
      e26_in=V0['wc']['ocl'], ae_in=V0['wc']['ocl'], note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables + other current assets − payables − accrued and other current liabilities)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_oca")}-{V("bs_ap")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppa_h', 'Acquisitions: none pending; future deals via the M&A lever (goodwill and intangibles). Historical purchase-price allocations (WhatsApp, Oculus 2014) are in the 10-K notes.', 'sub', 'gen')
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; RSUs)', 'sched', 'm1', ae_in=V0['dil'], note='Q2/26 diluted − basic weighted shares (~23m).')
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.08)
    S('ds_h', 'Debt schedule (senior notes repaid at maturity and refinanced; commercial paper / incremental notes drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (senior notes + commercial paper / incremental notes; capital leases to 2018)', 'sched', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_cp")}', note=MAN['debt']['at_2026_06_30'])
    S('ds_notes', '  Senior notes (carrying amount; term loan 2010; capital leases to 2018)', 'sched', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")',
      e26=lambda: f'={B1("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_iss', '  New notes issued (input; refinancing of maturities)', 'sched', 'm', e26_in=0.0, ae=lambda: f'={V("ds_repay")}*{V0["refi"]}',
      note=f'2027E+: maturities refinanced with new notes ({V0["refi"]:.0%}; assumption). The May-2026 $25bn issue is in the 30-Jun-2026 balance.')
    S('ds_repay', '  Notes repaid at maturity (input)', 'sched', 'm', e26_in=0.0, ae_in=V0['repay'], note=V0['repay_note'])
    S('ds_pre', '  Cash before CP draws / repayments (opening cash + CFO + CFI + buybacks, dividends, other financing + FX − notes repaid + issued)', 'sched', 'm',
      e26=lambda: (f'={B1("bs_cash")}+{h2("cf_cfo")}+{h2("cf_cfi")}+{h2("cf_bb")}+{h2("cf_div")}+{h2("cf_netshare")}+{h2("cf_lease")}+{h2("cf_eqiss")}+{h2("cf_ofin")}'
                   f'+{h2("cf_fx")}-{V("ds_repay")}+{V("ds_iss")}'),
      ae=lambda: (f'={P("bs_cash")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_bb")}+{V("cf_div")}+{V("cf_netshare")}+{V("cf_lease")}+{V("cf_eqiss")}+{V("cf_ofin")}+{V("cf_fx")}'
                  f'-{V("ds_repay")}+{V("ds_iss")}'))
    S('ds_min', '  Minimum cash and cash equivalents (excl. marketable securities)', 'sched', 'm', e26_in=V0['min_cash'], ae_in=V0['min_cash'], note=V0['min_note'])
    S('ds_cp', '  Commercial paper / incremental notes (year end; plug to minimum cash)', 'sched', 'm', hist=lambda: '=0',
      e26=lambda: f'=MAX(0,{B1("ds_cp")}+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_cp")}+{V("ds_min")}-{V("ds_pre")})',
      note='Financing assumption: shortfalls below the minimum cash balance are funded with commercial paper / new notes; surplus repays them (Meta has no CP programme disclosed).')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm', e26=lambda: f'=IFERROR({V("ds_total")}-{B1("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_debt', '  Interest rate on opening debt, net of capitalized interest %', 'sched', 'pct', ae_in=V0['r_debt'], note=V0['r_debt_note'])
    S('ds_r_cash', '  Interest income yield on opening cash and marketable securities %', 'sched', 'pct', ae_in=V0['r_cash'], note=V0['r_cash_note'])
    S('lev_h', 'Leverage-capped buybacks (repurchases plug to a maximum net debt / adjusted EBITDA, 2027E+; net debt = debt − cash − marketable securities)', 'sub', 'gen')
    S('lev_min', '  Maximum net debt / adjusted EBITDA (x) (scenario)', 'sched', 'x2', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end)', 'sched', 'm',
      ae=lambda: (f'={P("ds_total")}-{P("bs_cash")}-{P("bs_ms")}-{V("cf_cfo")}-({V("cf_cfi")}-{V("cf_ms")})-{V("cf_div")}-{V("cf_netshare")}-{V("cf_lease")}'
                  f'-{V("cf_eqiss")}-{V("cf_ofin")}-{V("cf_fx")}'))
    S('lev_tgt', '  Maximum net debt = ceiling × adjusted EBITDA', 'sched', 'm', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to the leverage ceiling', 'sched', 'm', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash beyond the ceiling is returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  D&A % of revenue', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_yld', '  Interest income ÷ average cash and marketable securities % (annual)', 'pct', 'pct', ann=True,
      all=lambda: (f'=IFERROR({V("d_intinc")}/AVERAGE({V("bs_cms")},{P("bs_cms")}),"")' if CTX.col.prior else None))
    S('hr_int', '  Interest expense ÷ average total debt % (annual; net of capitalized interest)', 'pct', 'pct', ann=True,
      all=lambda: (f'=IFERROR({V("d_intexp")}/AVERAGE({V("ds_total")},{P("ds_total")}),"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted EBIT, current definition, full-cost)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT, full-cost (current definition)', 'line', 'm', ann=True, all=lambda: f'={V("r_aebit")}')
    S('ra_t', 'Effective tax rate (adjusted, current definition)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("e_rate")}+0,0.16)')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', "  Total stockholders' equity", 'line', 'm', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − cash − marketable securities', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")}-{V("bs_ms")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Revenue', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Revenue / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-{V("bs_gw")},"n/a")')
    S('rn_cash', '  − Cash and marketable securities', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-{V("bs_cms")},"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total current liabilities excl. capital leases)', 'line', 'm', ann=True,
      all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})),"n/a")')
    S('rn_nta', '  = Net tangible operating assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income', 'line', 'm', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Stockholders' equity", 'line', 'm', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt (negative = net cash)', 'line', 'm', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA (model)', 'line', 'm', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_gx', 'Total debt / adjusted EBITDA (x)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("ds_total")}/{V("r_adj")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm', e26=lambda: f'={V("bb_end")}+({QA(Q2, "sh_dil")}-{QA(Q2, "sh_basic")})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm; negative = net cash; operating and finance leases excluded)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interests (none)', 'line', 'm', e26=lambda: '=0', ae=lambda: '=0')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Revenue', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA (model)', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted income from operations (current definition)', lambda: f'=IFERROR({V("v_ev")}/{V("o_cur")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS, current definition)', lambda: f'=IFERROR({V("v_px")}/{V("e_cureps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)

def FCF(col):
    """company FCF definition in force: CFO − purchases of P&E (net of P&E proceeds 2022-23) − P&E acquired under capital leases (2013-14)
    − principal payments on finance leases (from 2019)."""
    y = col.year
    base = f'{V("cf_cfo")}+{V("cf_capex")}'
    if y >= 2019: return f'=IF(ISNUMBER({V("cf_cfo")}),{base}+{V("cf_lease")},"")'
    return f'=IF(ISNUMBER({V("cf_cfo")}),{base}+N({V("fcf_cl")}),"")'
