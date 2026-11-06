"""Row specification part 2: Europe divestiture, cash flow, asbestos / AICF schedule, share schedule, balance sheet, working capital,
schedules (PPA, debt, leverage-targeted buybacks), ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, H1, H1P, QE2, LQ

def closes(year): return f'({PT("pt_close")}={year})'

def build_spec2(V0):
    S = add
    # ------------------------------------------------------------------ EUROPE DIVESTITURE
    S('sec_dv', 'EUROPE DIVESTITURE — DISCONTINUED OPERATIONS (fermacell sale to Holcim, €840m ≈ US$980m, announced 20-Aug-2026; European fibre cement to be closed)', 'section',
      note='EUROPE — discontinued operations from the Q2 FY27 release; closing assumed in the fiscal year set in the point-estimate table (2028 = Q1 FY28, i.e. 1H CY2027 as announced)')
    S('dv_rev_q1', '  Memo: Europe net sales as originally reported in Q1 FY27 (segment, before the recast)', 'memo', 'm1', data='man:misc:eu_rev_q1')
    S('dv_disc', '  Income from discontinued operations, net of tax (Europe operating result until closing; gain on sale in the closing year)', 'line', 'm1', data='disc', flow=True,
      qe=lambda: f'={PT("pt_disc")}+IF(AND({closes(2027)},{CTX.col.q}=4),{V("dv_gain")},0)',
      ae=lambda: f'=IF({closes(CTX.col.year)},{V("dv_gain")},0)',
      note='Q3–Q4/27E: point estimate per quarter (H1 FY27: 13.7 and 1.2 after €-fibre-cement closure costs). Closing year: gain on sale; no operating result thereafter.')
    S('dv_proc', '  Sale proceeds (US$m; €840m at the announcement rate; input)', 'line', 'm1', flow=True,
      qe=lambda: f'=IF(AND({closes(2027)},{CTX.col.q}=4),{PT("pt_proceeds")},0)', ae=lambda: f'=IF({closes(CTX.col.year)},{PT("pt_proceeds")},0)',
      note='Company: ~US$600m of the proceeds to debt repayment (model: cash sweep to the term loans in the closing year, debt schedule). Exchange rate at completion not hedged in the model.')
    S('dv_na', '  Net assets held for sale (assets 939.7 − liabilities 210.6 at 30-Sep-2026)', 'line', 'm1', qe=lambda: f'={LQ("bs_hfs")}-{LQ("bs_lhfs")}',
      e26=lambda: f'={LQ("bs_hfs")}-{LQ("bs_lhfs")}', ae=lambda: f'={P("dv_na")}', note='Carried at the 30-Sep-2026 balance until closing.')
    S('dv_gain', '  Gain on sale (proceeds − net assets; tax-free under the Irish participation exemption — company expectation, unverified)', 'line', 'm1', flow=True,
      qe=lambda: f'=IF(AND({closes(2027)},{CTX.col.q}=4),{V("dv_proc")}-{V("dv_na")},0)', ae=lambda: f'=IF({closes(CTX.col.year)},{V("dv_proc")}-{V("dv_na")},0)')
    S('dv_close', '  Closing fiscal year (input: 2028 = Q1 FY28; 2027 = inside Q4 FY27)', 'driver', 'gen', e26=lambda: f'={PT("pt_close")}')
    blank()

    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS (total company; FY2019+ cash includes restricted cash)', 'section',
      note='CASH FLOW — forecast logic (annual; 2027E = H1 FY27 actual + Q3–Q4 estimate; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net income (incl. discontinued operations)', 'line', 'm1', data='cf_ni', flow=True, e26=lambda: f'={H1("cf_ni")}+{QE2("is_ni")}', ae=lambda: f'={V("is_ni")}')
    S('cf_adj', 'Non-cash items:', 'sub', 'gen')
    S('cf_dna', '  Depreciation & amortization', 'line', 'm1', data='cf_dna', flow=True, e26=lambda: f'={H1("cf_dna")}+{QE2("d_dna")}', ae=lambda: f'={V("d_dna")}')
    S('cf_def', '  Deferred income taxes', 'line', 'm1', data='cf_def', flow=True, e26=lambda: f'={H1("cf_def")}-{QE2("d_amort")}*{V("cf_def_rate")}', ae=lambda: f'=-{V("d_amort")}*{V("cf_def_rate")}',
      note='Forecast: deferred tax benefit on the book amortization of the AZEK intangibles (DTL unwind) at the rate below.')
    S('cf_sbc', '  Share-based compensation', 'line', 'm1', data='cf_sbc', flow=True, e26=lambda: f'={H1("cf_sbc")}+{QE2("d_sbc")}', ae=lambda: f'={V("d_sbc")}')
    S('cf_asb', '  Asbestos adjustments (non-cash)', 'line', 'm1', data='cf_asb', flow=True, e26=lambda: f'={H1("cf_asb")}+{QE2("d_asb")}', ae=lambda: f'={V("d_asb")}')
    S('cf_claims', '  Claims and handling costs paid — asbestos (AICF; inside operating cash flow)', 'line', 'm1', data='cf_claims', flow=True,
      e26=lambda: f'={H1("cf_claims")}-{QE2("as_claims")}', ae=lambda: f'=-{V("as_claims")}', note='Linked to the asbestos / AICF schedule.')
    S('cf_wc', '  Other non-cash items & changes in operating assets and liabilities (derived)', 'line', 'm1', data='cf_wc', flow=True,
      e26=lambda: (f'={H1("cf_wc")}-({V("bs_ar")}-{LQ("bs_ar")})-({V("bs_inv")}-{LQ("bs_inv")})-({V("bs_oca")}-{LQ("bs_oca")})'
                   f'+({V("bs_ap")}-{LQ("bs_ap")})+({V("bs_ocl")}-{LQ("bs_ocl")})-{V("dv_gain")}'),
      ae=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_inv")}-{P("bs_inv")})-({V("bs_oca")}-{P("bs_oca")})'
                  f'+({V("bs_ap")}-{P("bs_ap")})+({V("bs_ocl")}-{P("bs_ocl")})-{V("dv_gain")}'),
      note='Historical residual (CFO − listed items). Forecast: −Δ(receivables, inventories, other current assets) + Δ(payables, other current liabilities) − non-cash gain on the Europe sale.')
    S('cf_cfo', 'Net cash provided by operating activities', 'line_b', 'm1', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_def_rate', '    DTL unwind rate on AZEK amortization (deferred tax line driver)', 'driver', 'pct', e26_in=V0['def_rate'], ae_in=V0['def_rate'])
    S('cf_capex', 'Purchases of property, plant & equipment', 'line', 'm1', data='cf_capex', flow=True,
      e26=lambda: f'=-{PT("pt_capex_pct")}*{V("is_rev")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='2027E: planning assumption 6–7% of net sales (mid-point); 2028E+: net sales × capex %.')
    S('cf_capint', 'Capitalized interest', 'line', 'm1', data='cf_capint', flow=True, e26=lambda: f'={H1("cf_capint")}', ae_in=0.0)
    S('cf_ppesale', 'Proceeds from the sale of property, plant & equipment (FY2026: Fontana, CA site)', 'line', 'm1', data='cf_ppesale', flow=True, e26=lambda: f'={H1("cf_ppesale")}', ae_in=0.0)
    S('cf_acq', 'Acquisition of businesses, net of cash acquired (FY2026: AZEK cash consideration incl. debt repaid, net of cash)', 'line', 'm1', data='cf_acq', flow=True,
      e26=lambda: f'={H1("cf_acq")}', ae=lambda: f'=-{V("m_spend")}', note='2028E+: M&A lever.')
    S('cf_dvp', 'Proceeds from the sale of businesses, net of cash disposed (Europe / fermacell)', 'line', 'm1',
      e26=lambda: f'={V("dv_proc")}-IF({closes(2027)},N({LQ("bs_hfs_cash")}),0)', ae=lambda: f'={V("dv_proc")}-IF({closes(CTX.col.year)},N({LQ("bs_hfs_cash")}),0)',
      note='Closing year: proceeds less the cash inside the held-for-sale group (US$2.0m at 30-Sep-2026).')
    S('cf_asb_inv', 'Restricted investments — asbestos (purchases net of proceeds)', 'line', 'm1', data='cf_asb_inv', flow=True, e26=lambda: f'={H1("cf_asb_inv")}', ae_in=0.0)
    S('cf_oinv', 'Other investing activities, net (derived)', 'line', 'm1', data='cf_oinv', flow=True, e26=lambda: f'={H1("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Net cash used in investing activities', 'line_b', 'm1', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_bb', 'Repurchases of ordinary shares', 'line', 'm1', data='cf_bb', flow=True, e26=lambda: f'={H1("cf_bb")}-{CH(SC["bb27"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='2027E: H1 actual (nil) + Q3–Q4 scenario input (US$250m authorization to 20-Aug-2027). 2028E+ = leverage plug (surplus cash returned once net debt / Adjusted EBITDA is at the target).')
    S('cf_div', 'Dividends paid', 'line', 'm1', data='cf_div', flow=True, e26=lambda: f'={H1("cf_div")}', ae=lambda: f'=-{V("dps")}*{V("bb_beg")}')
    S('cf_eq', 'Proceeds from equity plans, net (derived historically with other financing)', 'line', 'm1', data='cf_eq', flow=True, e26=lambda: f'={H1("cf_eq")}+{V0["eq_h2"]}', ae_in=V0['eq_ae'])
    S('cf_debt', 'Net debt issuance / (repayment) (forecast; included in other financing historically)', 'line', 'm1', e26=lambda: f'={V("ds_net")}', ae=lambda: f'={V("ds_net")}',
      note='Per the debt schedule: term-loan amortization, prepayments from surplus cash, refinancing at maturity, revolver to the minimum cash balance.')
    S('cf_ofin', 'Debt, equity-plan & other financing, net (derived historically; FY2026: AZEK financing)', 'line', 'm1', data='cf_ofin', flow=True, e26=lambda: f'={H1("cf_ofin")}', ae_in=0.0)
    S('cf_cff', 'Net cash provided by (used in) financing activities', 'line_b', 'm1', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_bb")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of exchange rate changes on cash', 'line', 'm1', data='cf_fx', flow=True, e26=lambda: f'={H1("cf_fx")}', ae_in=0.0)
    S('cf_net', 'Increase (decrease) in cash', 'line', 'm1', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")}),"")', fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}')
    S('cf_beg', 'Cash — beginning of period (cash-flow statement basis)', 'line', 'm1', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period (cash-flow statement basis; incl. restricted cash from FY2019)', 'line_b', 'm1', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_bflag', '  Memo: cash-flow statement cash includes restricted cash (1 = yes, from FY2019 / ASU 2016-18)', 'driver', 'gen', data='cf_restr_flag', fc=lambda: '=1')
    S('cf_chk1', '  Check: CFO + CFI + CFF + FX = change in cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=0.15,0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},1)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")})<=0.15,0,ROUND(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")},1)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (company definition: operating cash flow − purchases of PP&E + proceeds from the sale of PP&E)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")}+N({V("cf_ppesale")}),"")',
      note='Company definition (FY2025+ releases): net cash provided by operating activities − purchases of PP&E + proceeds from the sale of PP&E (FY2026: US$108.2m Fontana site).')
    S('fcf_pub', '  Company-published free cash flow (from FY2025)', 'memo', 'm1', data='fcf_pub', flow=True)
    S('fcf_chk', '  Check: model vs company-published free cash flow (should be 0; ±0.5 rounding)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("fcf_pub")}),IF(ABS({V("fcf")}-{V("fcf_pub")})<=0.5,0,ROUND({V("fcf")}-{V("fcf_pub")},1)),"n/p")')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of net sales', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / Adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of net sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note='2028E+ input (FY2022–26: 8–12% of net sales during the capacity build-out; FY27 planning assumption 6–7%).')
    S('capex_dep', '  Capex / depreciation & other amortization (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("d_dep")},""),"")')
    blank()

    # ------------------------------------------------------------------ ASBESTOS / AICF
    S('sec_as', 'ASBESTOS — AMENDED AND RESTATED FINAL FUNDING AGREEMENT (AFFA) / ASBESTOS INJURIES COMPENSATION FUND (AICF) SCHEDULE', 'section',
      note='ASBESTOS — liability recognised undiscounted and uninflated (KPMG actuarial central estimate); annual AFFA contribution = 35% of the prior-year free cash flow (as defined); claims paid by the consolidated fund (operating cash flow)')
    S('as_liab', '  Asbestos liability (current + non-current; period end)', 'sched', 'm1', data='bs_asb_total', bs=True,
      e26=lambda: f'={LQ("as_liab")}-{QE2("as_claims")}+{QE2("d_asb")}', ae=lambda: f'={P("as_liab")}-{V("as_claims")}+{V("d_asb")}',
      note='Roll-forward: opening − claims paid + asbestos adjustments (P&L; actuarial, FX). US$1,008.6m at 31-Mar-2026 (A$-denominated).')
    S('as_claims', '  Claims and handling costs paid (cash)', 'sched', 'm1', data='as_claims', flow=True,
      qe=lambda: f'=({PT("pt_claims")}-{H1("as_claims")})/2', ae_in=V0['claims'], note=V0['claims_note'])
    S('as_adj', '  Asbestos adjustments (P&L)', 'sched', 'm1', all=lambda: f'=N({V("d_asb")})')
    S('as_ins', '  Insurance receivable — asbestos (current + non-current; period end)', 'sched', 'm1', data='bs_ins_asb_total', bs=True, e26=lambda: f'={LQ("as_ins")}', ae=lambda: f'={P("as_ins")}')
    S('as_cash', '  AICF restricted cash & short-term investments (period end)', 'sched', 'm1', data='bs_aicf_cash', bs=True,
      e26=lambda: f'={LQ("as_cash")}+({V("as_contrib")}-{H1("as_contrib")})-{QE2("as_claims")}-{QE2("d_aicf_int")}',
      ae=lambda: f'={P("as_cash")}+{V("as_contrib")}-{V("as_claims")}-{V("d_aicf_int")}',
      note='Roll-forward: opening + AFFA contribution + interest income − claims paid. The fund is consolidated (restricted cash sits inside the cash-flow statement cash; investments in investing activities).')
    S('as_contrib', '  AFFA contribution paid to AICF (cash; supplemental disclosure)', 'sched', 'm1', data='cf_aicf', flow=True,
      e26=lambda: f'={PT("pt_contrib")}', ae=lambda: f'=0.35*MAX(0,{P("fcf")})',
      note='FY27: A$128.2m (≈US$93m at the 31-Mar-2026 rate; US$22.2m paid in H1). 2028E+: 35% × prior-year free cash flow (model; the AFFA formula uses net operating cash flow as defined, in A$).')
    S('as_net', '  Net unfunded asbestos liability (liability − insurance receivable − AICF cash & investments; debt-like in the EV bridge)', 'sched', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("as_liab")}),{V("as_liab")}-N({V("as_ins")})-N({V("as_cash")}),"")')
    S('as_dta', '  Deferred tax asset — asbestos (period end)', 'sched', 'm1', data='bs_dta_asb', bs=True, e26=lambda: f'={LQ("as_dta")}', ae=lambda: f'={P("as_dta")}')
    S('as_net_at', '  Memo: net unfunded liability after the deferred tax asset', 'memo_calc', 'm1', all=lambda: f'=IF(ISNUMBER({V("as_net")}),{V("as_net")}-N({V("as_dta")}),"")')
    S('as_yield', '  AICF investment yield (interest income on opening cash & investments) %', 'sched', 'pct', ae_in=V0['as_yield'])
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2027E starts from shares outstanding at 30-Sep-2026 (Q3–Q4 buybacks); 2028E+ buybacks via the leverage plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2027E = Q3–Q4)', 'line', 'm', e26=lambda: f'={CH(SC["bb27"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans (m)', 'driver', 'm2', e26_in=V0['iss_e26'], ae_in=V0['iss_ae'])
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={LQ("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2027E begins from ordinary shares outstanding at 30-Sep-2026 (Q2 FY27 10-Q balance sheet).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since Q3/27 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET (condensed, as in the filings)', 'section',
      note='BS FORECAST — 2027E rolled forward from the 30-Sep-2026 balance sheet + Q3–Q4 flows; 2028E+ from prior year end; Europe held-for-sale balances removed at closing')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm1', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}-{V("bs_restr")}-{V("bs_restr_asb")}-IF({V("bs_hfs")}>0,N({LQ("bs_hfs_cash")}),0)',
      note='Cash-flow statement cash less restricted cash and the cash inside the Europe held-for-sale group (until closing).')
    S('bs_restr', '  Restricted cash (other; FY2026 Q1: AZEK notes escrow US$1.7bn)', 'line', 'm1', data='bs_restr', bs=True, e26=lambda: f'={LQ("bs_restr")}', ae=lambda: f'={P("bs_restr")}')
    S('bs_restr_asb', '  Restricted cash — asbestos (AICF)', 'line', 'm1', data='bs_restr_asb', bs=True, fc=lambda: f'={V("as_cash")}-{V("bs_inv_asb")}')
    S('bs_inv_asb', '  Restricted short-term investments — asbestos (AICF)', 'line', 'm1', data='bs_inv_asb', bs=True, e26=lambda: f'={LQ("bs_inv_asb")}', ae=lambda: f'={P("bs_inv_asb")}')
    S('bs_ar', '  Accounts and other receivables, net', 'line', 'm1', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_inv', '  Inventories', 'line', 'm1', data='bs_inv', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dio")}/365')
    S('bs_oca', '  Prepaid expenses & other current assets (incl. current insurance receivable / deferred taxes — asbestos; derived)', 'line', 'm1', data='bs_oca', bs=True,
      e26=lambda: f'={LQ("bs_oca")}', ae=lambda: f'={P("bs_oca")}')
    S('bs_hfs', '  Assets held for sale (Europe from 30-Sep-2026; earlier: Fontana / other sites)', 'line', 'm1', data='bs_hfs', bs=True,
      e26=lambda: f'=IF({closes(2027)},0,{LQ("bs_hfs")})', ae=lambda: f'=IF({PT("pt_close")}<={CTX.col.year},0,{P("bs_hfs")})')
    S('bs_tca', 'Total current assets', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_hfs")}),"")')
    S('bs_ppe', '  Property, plant & equipment, net', 'line', 'm1', data='bs_ppe', bs=True,
      e26=lambda: f'={LQ("bs_ppe")}-({V("cf_capex")}-{H1("cf_capex")})-({V("cf_capint")}-{H1("cf_capint")})-{QE2("d_dep")}',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("cf_capint")}-({V("d_dep")}-N({V("m_amort")}))+{V("m_spend")}*{V("m_ppe")}',
      note='Roll-forward: prior − capex (negative cash flow) − capitalized interest − depreciation & other amortization (excl. future-acquisition intangible amortization, which reduces intangibles) + acquired PP&E.')
    S('bs_rou', '  Operating & finance lease right-of-use assets', 'line', 'm1', data='bs_rou', bs=True, e26=lambda: f'={LQ("bs_rou")}', ae=lambda: f'={P("bs_rou")}')
    S('bs_gw', '  Goodwill', 'line', 'm1', data='bs_gw', bs=True, e26=lambda: f'={LQ("bs_gw")}', ae=lambda: f'={P("bs_gw")}+{V("m_spend")}*(1-{V("m_ppe")}-{V("m_intp")})')
    S('bs_int', '  Intangible assets, net', 'line', 'm1', data='bs_int', bs=True,
      e26=lambda: f'={LQ("bs_int")}-{QE2("d_amort")}', ae=lambda: f'={P("bs_int")}-{V("d_amort")}-N({V("m_amort")})+{V("m_spend")}*{V("m_intp")}',
      note='Roll-forward: prior − AZEK intangible amortization (− future-acquisition amortization) + acquired intangibles (M&A lever).')
    S('bs_ins_asb', '  Insurance receivable — asbestos (non-current)', 'line', 'm1', data='bs_ins_asb', bs=True, fc=lambda: f'={V("as_ins")}*IFERROR({LQ("bs_ins_asb")}/{LQ("as_ins")},1)')
    S('bs_dta', '  Deferred income taxes', 'line', 'm1', data='bs_dta', bs=True, e26=lambda: f'={LQ("bs_dta")}', ae=lambda: f'={P("bs_dta")}')
    S('bs_dta_asb', '  Deferred income taxes — asbestos', 'line', 'm1', data='bs_dta_asb', bs=True, fc=lambda: f'={V("as_dta")}')
    S('bs_ato', '  Deposit with the Australian Taxation Office (FY2011–12 tax dispute)', 'line', 'm1', data='bs_ato', bs=True, fc=lambda: '=0')
    S('bs_onca', '  Other non-current assets (derived)', 'line', 'm1', data='bs_onca', bs=True, e26=lambda: f'={LQ("bs_onca")}', ae=lambda: f'={P("bs_onca")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_ppe")}:{V("bs_onca")}),"")')
    S('bs_l', "LIABILITIES AND SHAREHOLDERS' EQUITY", 'sub', 'gen')
    S('bs_ap', '  Accounts payable, accrued liabilities & accrued payroll', 'line', 'm1', data='bs_ap', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dpo")}/365')
    S('bs_std', '  Short-term debt / current portion of long-term debt', 'line', 'm1', data='bs_std', bs=True, fc=lambda: f'=MIN({V("ds_total")},{V("ds_mat")})',
      note='Term-loan amortization due in the next fiscal year.')
    S('bs_asb_c', '  Asbestos liability — current', 'line', 'm1', data='bs_asb_c', bs=True, fc=lambda: f'={V("as_liab")}*IFERROR({LQ("bs_asb_c")}/{LQ("as_liab")},0.13)')
    S('bs_lhfs', '  Liabilities held for sale (Europe)', 'line', 'm1', data='bs_lhfs', bs=True,
      e26=lambda: f'=IF({closes(2027)},0,{LQ("bs_lhfs")})', ae=lambda: f'=IF({PT("pt_close")}<={CTX.col.year},0,{P("bs_lhfs")})')
    S('bs_ocl', '  Other current liabilities (incl. income taxes payable, warranty, current leases; derived)', 'line', 'm1', data='bs_ocl', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_oclp")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_ap")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term debt', 'line', 'm1', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_std")}')
    S('bs_asb_nc', '  Asbestos liability — non-current', 'line', 'm1', data='bs_asb_nc', bs=True, fc=lambda: f'={V("as_liab")}-{V("bs_asb_c")}')
    S('bs_dtl', '  Deferred income taxes (liability; AZEK intangibles)', 'line', 'm1', data='bs_dtl', bs=True,
      e26=lambda: f'={LQ("bs_dtl")}+({V("cf_def")}-{H1("cf_def")})', ae=lambda: f'={P("bs_dtl")}+{V("cf_def")}')
    S('bs_onl', '  Other non-current liabilities (leases, warranty, pensions, workers compensation; derived)', 'line', 'm1', data='bs_onl', bs=True, e26=lambda: f'={LQ("bs_onl")}', ae=lambda: f'={P("bs_onl")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_onl")}),"")')
    S('bs_eq', "  Shareholders' equity (deficit)", 'line', 'm1', data='bs_eq', bs=True,
      e26=lambda: (f'={LQ("bs_eq")}+{QE2("is_ni")}+({V("cf_div")}-{H1("cf_div")})+({V("cf_bb")}-{H1("cf_bb")})+({V("cf_sbc")}-{H1("cf_sbc")})+({V("cf_eq")}-{H1("cf_eq")})'),
      ae=lambda: f'={P("bs_eq")}+{V("is_ni")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_sbc")}+{V("cf_eq")}',
      note='+ net income − dividends − repurchases + share-based compensation + equity-plan proceeds (currency translation held flat).')
    S('bs_tle', "TOTAL LIABILITIES AND SHAREHOLDERS' EQUITY", 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_eq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=0.15,0,ROUND({V("bs_ta")}-{V("bs_tle")},1)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=0.15,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},1)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm1', data='bs_ta', bs=True)
    S('bs_hfs_cash', '  Memo: cash inside assets held for sale (Europe)', 'memo', 'm1', data='man:misc:hfs_cash', fc=lambda: f'=IF({V("bs_hfs")}>0,N({LQ("bs_hfs_cash")}),0)')
    S('bs_chk_cash', '  Check: BS cash (+ restricted cash where the cash-flow statement includes it, + held-for-sale cash) vs cash-flow ending cash (should be 0)', 'check', 'm1',
      all=lambda: (f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}+IF(N({V("cf_bflag")})=1,{V("bs_restr")}+{V("bs_restr_asb")},0)+N({V("bs_hfs_cash")})-{V("cf_end")})<=0.15,0,'
                   f'ROUND({V("bs_cash")}+IF(N({V("cf_bflag")})=1,{V("bs_restr")}+{V("bs_restr_asb")},0)+N({V("bs_hfs_cash")})-{V("cf_end")},1)),"")'))
    S('bs_shares', '  Memo: ordinary shares outstanding at period end (m)', 'memo', 'm1', data='bs_shares', bs=True, e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input) on fiscal-year-end balances')
    S('wc_rev', '  Net sales — annualised (quarters × 4)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_cogs', '  Cost of goods sold — annualised', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_cogs")}*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — receivables / net sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_dio', '  Inventory days — inventories / cost of goods sold × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_inv")}/{V("wc_cogs")}*365,"")', e26_in=V0['wc']['dio'], ae_in=V0['wc']['dio'])
    S('wc_dpo', '  Payable days — payables & accrued / cost of goods sold × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_cogs")}*365,"")', e26_in=V0['wc']['dpo'], ae_in=V0['wc']['dpo'])
    S('wc_oclp', '  Other current liabilities % of net sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")', e26_in=V0['wc']['ocl'], ae_in=V0['wc']['ocl'], note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables + inventories + other current assets − payables − other current liabilities)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_inv")}+{V("bs_oca")}-{V("bs_ap")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of net sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm1', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppa_h', 'AZEK acquisition — consideration & purchase-price allocation (closing-period column; FY2026 10-K Note 2)', 'sub', 'gen')
    for k, lab in [('cons', 'Total consideration (cash US$4,249.9m incl. AZEK debt repaid US$437.8m; 148.9m shares at US$26.82 = US$3,992.5m; replacement awards US$151.1m)'),
                   ('cash', 'Cash acquired'), ('ar', 'Accounts receivable'), ('inv', 'Inventories (incl. US$47.9m fair-value step-up)'), ('prepaid', 'Prepaid expenses & other current assets'),
                   ('ppe', 'Property, plant & equipment'), ('intang', 'Intangible assets (customer relationships 2,830.0 / 18y; trade names 330.0 / 5–15y; technology 210.0 / 10y)'),
                   ('gw', 'Goodwill (not tax-deductible)'), ('onca', 'Other non-current assets (incl. lease right-of-use)'), ('ap', 'Accounts payable & accrued liabilities assumed'),
                   ('ocl', 'Other current liabilities assumed'), ('dtl', 'Deferred tax liabilities assumed (on the intangibles)'), ('oncl', 'Other non-current liabilities assumed')]:
        S(f'ppa_{k}', f'  {lab}', 'sched', 'm1', data=f'ppa_{k}', ppa=True)
    S('ppa_chk', '  Check: assets acquired − liabilities assumed − consideration (should be 0)', 'check', 'm1',
      hist=lambda: (f'=IF(ISNUMBER({V("ppa_cons")}),ROUND(N({V("ppa_cash")})+N({V("ppa_ar")})+N({V("ppa_inv")})+N({V("ppa_prepaid")})+N({V("ppa_ppe")})+N({V("ppa_intang")})+N({V("ppa_gw")})+N({V("ppa_onca")})'
                    f'-N({V("ppa_ap")})-N({V("ppa_ocl")})-N({V("ppa_dtl")})-N({V("ppa_oncl")})-{V("ppa_cons")},1),"")'))
    S('ppa_names', '  Deal closed in the period', 'text', 'gen', data='ppa_names', ppa=True, textdata=True)
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; RSUs / performance awards)', 'sched', 'm1', ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.08)
    S('ds_h', 'Debt schedule (senior notes refinanced at maturity; term loans A-1 / A-2 amortize, prepaid from surplus cash; US$1.0bn revolver drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (short-term + long-term debt, net of financing costs)', 'sched', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_tla")}+{V("ds_rev")}', note=V0['debt_note'])
    S('ds_notes', '  Senior notes (5.875% 2031 US$700m + 6.125% 2032 US$1,000m; net of US$28.0m unamortized costs)', 'sched', 'm1', e26_in=V0['notes_sep26'],
      ae=lambda: f'={P("ds_notes")}+{V("ds_refi")}-{V("ds_nrep")}', note='30-Sep-2026 balance net of all unamortized financing costs (10-Q Note 8). 5.000% 2028 notes (US$400m) redeemed 25-Jun-2026.')
    S('ds_refi', '  New notes issued (refinancing; input)', 'sched', 'm1', ae_in=V0['refi'], note='2029E: Term Loan A-1 (US$650m, due 2028) refinanced with notes; 2031E: 2031 notes (US$700m, Jan-2031) refinanced.')
    S('ds_nrep', '  Notes repaid at maturity (input)', 'sched', 'm1', ae_in=V0['nrep'])
    S('ds_tla0', '  Term loans at 30-Sep-2026 (A-1 US$650.0m due 2028; A-2 US$1,695.3m due 2030)', 'sched', 'm1', e26_in=V0['tla_sep26'])
    S('ds_tla', '  Term loans A-1 / A-2 (year end)', 'sched', 'm1', e26=lambda: f'={V("ds_tla0")}-{V("ds_sched")}-{V("ds_prepay")}', ae=lambda: f'={P("ds_tla")}-{V("ds_sched")}-{V("ds_prepay")}')
    S('ds_sched', '  Scheduled term-loan repayments (A-2 amortization ~US$54.7m a year; A-1 US$650m at maturity FY2029; A-2 maturity Oct-2030 assumed extended / refinanced — financing assumption)', 'sched', 'm1',
      e26_in=V0['tla_sched'][2027], ae=lambda: f'=MIN({P("ds_tla")},{V0["tla_sched"][CTX.col.year]})')
    S('ds_mat', '  Debt maturing in the following fiscal year (current portion)', 'sched', 'm1', e26_in=V0['mat'][2027], ae=lambda: f'=MIN({V("ds_tla")},{V0["mat"][CTX.col.year]})')
    S('ds_pre', '  Cash before prepayments, buybacks and revolver (opening cash + CFO + CFI + dividends, equity, other financing + FX − scheduled repayments ± notes − restricted cash)', 'sched', 'm1',
      e26=lambda: (f'={LQ("cf_end")}+({V("cf_cfo")}-{H1("cf_cfo")})+({V("cf_cfi")}-{H1("cf_cfi")})+({V("cf_div")}-{H1("cf_div")})+({V("cf_eq")}-{H1("cf_eq")})'
                   f'+({V("cf_ofin")}-{H1("cf_ofin")})+({V("cf_fx")}-{H1("cf_fx")})-{V("ds_sched")}-{V("bs_restr")}-{V("bs_restr_asb")}'),
      ae=lambda: (f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_div")}+{V("cf_eq")}+{V("cf_ofin")}+{V("cf_fx")}-{V("ds_sched")}-{V("ds_nrep")}+{V("ds_refi")}'
                  f'-{V("bs_restr")}-{V("bs_restr_asb")}'))
    S('ds_min', '  Minimum (unrestricted) cash balance', 'sched', 'm1', e26_in=V0['min_cash'], ae_in=V0['min_cash'])
    S('ds_prepay', '  Term-loan prepayments from surplus cash (cash sweep after buybacks; 2027E input)', 'sched', 'm1', e26_in=V0['prepay_27'],
      ae=lambda: f'=MAX(0,MIN({P("ds_tla")}-{V("ds_sched")},{V("ds_pre")}-{V("bb_cash")}-{V("ds_min")}))',
      note='Deleveraging priority (net leverage < 2.0x by Q2 FY28; ~US$600m of the Europe proceeds to debt): all cash above the minimum balance after buybacks prepays the term loans.')
    S('ds_rev', '  Revolving credit facility (US$1.0bn; year end)', 'sched', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("ds_total")}),ISNUMBER({V("ds_notes")})),{V("ds_total")}-{V("ds_notes")}-{V("ds_tla")},"")',
      e26=lambda: f'=MAX(0,0+{V("ds_min")}-({V("ds_pre")}-{V("bb_cash")}-{V("ds_prepay")}))', ae=lambda: f'=MAX(0,{P("ds_rev")}+{V("ds_min")}-({V("ds_pre")}-{V("bb_cash")}-{V("ds_prepay")}))',
      note='Undrawn at 30-Sep-2026 (US$993.2m available). Shortfalls below the minimum cash balance are drawn; surplus repays the revolver.')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm1', e26=lambda: f'={V("ds_total")}-{LQ("ds_total")}', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on opening senior notes %', 'sched', 'pct', ae_in=V0['r_notes'], note='5.875% / 6.125% coupons; refinancing assumed near the current coupons.')
    S('ds_r_tla', '  Interest rate on opening term loans % (SOFR + margin)', 'sched', 'pct', ae_in=V0['r_tla'], note='Weighted-average interest rate on total debt 5.7% at 30-Sep-2026 (10-Q).')
    S('ds_r_rev', '  Interest rate on opening revolver %', 'sched', 'pct', ae_in=V0['r_rev'])
    S('ds_fees', '  Commitment fees & financing-cost amortization ($m)', 'sched', 'm1', ae_in=V0['fees'])
    S('ds_r_cash', '  Interest income yield on opening unrestricted cash %', 'sched', 'pct', ae_in=0.03)
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / Adjusted EBITDA, 2028E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / Adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end; prepayments do not change net debt)', 'sched', 'm1',
      ae=lambda: (f'={P("ds_total")}-{P("bs_cash")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_eq")}-{V("cf_ofin")}-{V("cf_fx")}'
                  f'+({V("bs_restr")}+{V("bs_restr_asb")}-{P("bs_restr")}-{P("bs_restr_asb")})'))
    S('lev_tgt', '  Target net debt = target leverage × Adjusted EBITDA', 'sched', 'm1', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to target leverage (capped at the cash available above the minimum balance — no revolver-funded buybacks)', 'sched', 'm1',
      ae=lambda: f'=MAX(0,MIN({V("lev_tgt")}-{V("lev_pre")},{V("ds_pre")}-{V("ds_min")}))',
      note='Surplus beyond the leverage target is returned via buybacks, limited to the cash generated in the year (free cash flow + Europe proceeds − scheduled repayments); the rest prepays the term loans. Feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of net sales', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_int', '  Interest, net ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    S('hr_lease', '  Memo: lease liabilities (operating + finance; period end)', 'memo', 'm1', data='bs_lease', bs=True)
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on Adjusted EBITA after share-based compensation)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBITA after SBC (Adjusted EBITDA − SBC add-back − depreciation & other amortization)', 'line', 'm1', ann=True, all=lambda: f'={V("r_ebita")}')
    S('ra_t', 'Effective tax rate (adjusted)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("e_rate")}+0,0.22)')
    S('ra_nopat', 'NOPAT = Adjusted EBITA × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', "  Shareholders' equity", 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − Cash (unrestricted)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBITA / Net sales', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Net sales / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBITA × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm1', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangible assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-({V("bs_gw")}+{V("bs_int")}),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. short-term debt)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})),"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income', 'line', 'm1', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Shareholders' equity", 'line', 'm1', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA (model)', 'line', 'm1', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / Adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")',
      note='Company target: net leverage below 2.0x by the end of Q2 FY28 (30-Sep-2027). FY2026 3.2x on the year-end balance (pro forma AZEK ~2.9x).')
    S('lv_asb', 'Net debt + net unfunded asbestos liability / Adjusted EBITDA (x)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR(({V("lv_nd")}+{V("as_net")})/{V("lv_eb")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+({Q2}{R["sh_dil"]}-{Q2}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_asb', 'Net unfunded asbestos liability (debt-like; USDm)', 'line', 'm', e26=lambda: f'={V("as_net")}', ae=lambda: f'={V("as_net")}',
      note='Liability − insurance receivable − AICF cash & investments (pre-tax; the related deferred tax asset is shown in the asbestos schedule).')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_asb")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_asb")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Net sales', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted EBIT (full cost)', lambda: f'=IFERROR({V("v_ev")}/{V("r_ebit")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted, continuing)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dilc")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
