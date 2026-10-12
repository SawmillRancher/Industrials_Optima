"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, B1, chk, E

def build_spec2(V0):
    S = add
    def e26f(key, q):           # FY2026E flow = 1H26 actual (Q1-Q2/26) + Q3/Q4-26E estimates
        return lambda: f'={ACT(key)}+{SQE(q)}'
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 1H26 actual + 2H estimate; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net income (incl. noncontrolling interests)', 'line', 'm1', data='cf_ni', flow=True, fc=lambda: f'={V("is_nitot")}', e26=e26f('cf_ni', 'is_nitot'))
    S('cf_adj', 'Non-cash items:', 'sub', 'gen')
    S('cf_dna', '  Depreciation & amortization', 'line', 'm1', data='cf_dna', flow=True, fc=lambda: f'={V("is_dda")}', e26=e26f('cf_dna', 'is_dda'))
    S('cf_sbc', '  Stock-based compensation', 'line', 'm1', data='cf_sbc', flow=True, fc=lambda: f'={V("is_sbc")}', e26=e26f('cf_sbc', 'is_sbc'))
    S('cf_def', '  Deferred income taxes', 'line', 'm1', data='cf_def', flow=True, e26=lambda: f'={ACT("cf_def")}+{V0["def_2h"]}', ae_in=V0['def_ae'],
      note='Cash-flow statement. Forecast input.')
    S('cf_gain', '  Gains on divestitures / remeasurement (non-cash reversal; proceeds in investing)', 'line', 'm1', data='cf_gain', flow=True,
      e26=lambda: f'={ACT("cf_gain")}-{SQE("is_gain")}', ae=lambda: f'=-{V("is_gain")}')
    S('cf_wc', '  Working capital & other operating items, net (derived)', 'line', 'm1', data='cf_wc', flow=True,
      e26=lambda: (f'={ACT("cf_wc")}-({V("bs_ar")}-{B1("bs_ar")})-({V("bs_oca")}-{B1("bs_oca")})'
                   f'+({V("bs_ap")}-{B1("bs_ap")})+({V("bs_dr")}-{B1("bs_dr")})+({V("bs_ocl")}-{B1("bs_ocl")})'),
      ae=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_oca")}-{P("bs_oca")})'
                  f'+({V("bs_ap")}-{P("bs_ap")})+({V("bs_dr")}-{P("bs_dr")})+({V("bs_ocl")}-{P("bs_ocl")})'),
      note=('History: net cash from operating activities − net income − D&A − stock-based compensation − deferred taxes − gains (all other non-cash items and working-capital changes). '
            'Forecast linked to the balance sheet: −Δ(receivables, other current assets) + Δ(payables & accrued, deferred revenue, other current liabilities).'))
    S('cf_cfo', 'Net cash provided by operating activities', 'line_b', 'm1', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Capital additions', 'line', 'm1', data='cf_capex', flow=True,
      e26=lambda: f'=-{PT("pt_capex")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}', note=V0['capex_note'])
    S('cf_acq', 'Cash paid for acquisitions, net of cash acquired', 'line', 'm1', data='cf_acq', flow=True,
      e26=lambda: f'={ACT("cf_acq")}', ae=lambda: f'=-{V("m_spend")}', note='2026E = 1H actual. 2027E+: M&A lever.')
    S('cf_divest', 'Cash received upon business divestitures', 'line', 'm1', data='cf_divest', flow=True,
      e26=lambda: f'={ACT("cf_divest")}+{SQE("is_gain")}', ae=lambda: f'={V("is_gain")}',
      note='2026E: 1H actual (MA Regulatory Solutions / Learning Solutions) + 2H contingent consideration (assumed received in cash = the 2H gain).')
    S('cf_oinv', 'Other investing activities, net (investments, hedges, affiliates; derived)', 'line', 'm1', data='cf_oinv', flow=True, e26=lambda: f'={ACT("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Net cash provided by (used in) investing activities', 'line_b', 'm1', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_bb', 'Treasury shares (share repurchases)', 'line', 'm1', data='cf_bb', flow=True, e26=lambda: f'={ACT("cf_bb")}-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='2026E: 1H actual + 2H scenario input (FY26 guidance "up to $3.0bn"). 2027E+ = leverage plug (surplus cash returned until net debt / Adjusted Operating Income reaches the target).')
    S('cf_div', 'Dividends (to Moody\'s shareholders)', 'line', 'm1', data='cf_div', flow=True,
      e26=lambda: f'={ACT("cf_div")}-{SQE("dps")}*{E("bb_beg")}', ae=lambda: f'=-{V("dps")}*{V("bb_beg")}',
      note='Forecast = DPS × beginning shares (no circularity with plug-driven buybacks).')
    S('cf_eq', 'Stock-based compensation plans, net (proceeds − shares withheld for taxes)', 'line', 'm1', data='cf_stock', flow=True,
      e26=lambda: f'={ACT("cf_eq")}+{V0["eq_2h"]}', ae_in=V0['eq_ae'])
    S('cf_debt', 'Net debt issuance / (repayment) (notes, term loans, commercial paper)', 'line', 'm1', data='cf_debt', flow=True,
      e26=lambda: f'={V("ds_total")}-{B1("ds_total")}+{ACT("cf_debt")}', ae=lambda: f'={V("ds_net")}',
      note='History: issuance − repayment of notes / loans ± net commercial paper. Forecast per the debt schedule: notes repaid at maturity and refinanced (input); commercial paper to the minimum cash balance.')
    S('cf_ofin', 'Other financing, net (NCI dividends, debt costs, other; derived)', 'line', 'm1', data='cf_ofin', flow=True,
      e26=lambda: f'={ACT("cf_ofin")}', ae_in=0.0)
    S('cf_cff', 'Net cash provided by (used in) financing activities', 'line_b', 'm1', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_bb")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of exchange rate changes on cash (and other cash movements, e.g. 2019 held-for-sale reclassification)', 'line', 'm1', data='cf_fx', flow=True, e26=lambda: f'={ACT("cf_fx")}', ae_in=0.0)
    S('cf_net', 'Net change in cash and cash equivalents', 'line', 'm1', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")}),"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}')
    S('cf_beg', 'Cash — beginning of period', 'line', 'm1', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period', 'line_b', 'm1', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: CFO + CFI + CFF + FX = change in cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),{chk(V("cf_beg") + "+" + V("cf_net"), V("cf_end"), 1.5)},"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),{chk("SUM(" + V("cf_ni") + ":" + V("cf_wc") + ")", V("cf_cfo"))},"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free Cash Flow (company definition: CFO − capital additions)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")},"")')
    S('fcf_pub', '  Company-published Free Cash Flow', 'memo', 'm1', data='fcf_pub', flow=True)
    S('fcf_chk', '  Check: model vs company-published Free Cash Flow (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("fcf_pub")}),{chk(V("fcf"), V("fcf_pub"), 1.5)},"n/p")')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of revenue', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / Adjusted Operating Income %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note='2027E+ input (FY2022–25 4.2–5.2% of revenue; FY26 ~$450m incl. ~$100m of New York / London office relocations).')
    S('capex_dep', '  Capex / depreciation excl. acquired intangibles (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("d_dep")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E = 2H from shares outstanding at 30-Jun-2026; 2027E+ buybacks via the leverage plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = 2H)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans (m)', 'driver', 'm2', e26_in=V0['iss_2h'], ae_in=V0['iss_ae'])
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from shares outstanding at 30-Jun-2026 (Q2-26 10-Q).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since 30-Jun-2026 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET (condensed)', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Jun-2026 balance sheet + 2H flows; 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm1', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}')
    S('bs_sti', '  Short-term investments', 'line', 'm1', data='bs_sti', bs=True, e26=lambda: f'={B1("bs_sti")}', ae=lambda: f'={P("bs_sti")}')
    S('bs_ar', '  Accounts receivable, net', 'line', 'm1', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_oca', '  Other current assets (incl. assets held for sale)', 'line', 'm1', data='bs_oca', bs=True, e26=lambda: f'={B1("bs_oca")}', ae=lambda: f'={P("bs_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_ppe', '  Property and equipment, net (incl. capitalised software)', 'line', 'm1', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-({V("cf_capex")}-{ACT("cf_capex")})-{SQE("d_dep")}',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("d_dep")}+{V("m_spend")}*{V("m_ppe")}',
      note='Roll-forward: prior − capital additions (negative cash flow) − depreciation (excl. acquired intangibles) + acquired PP&E.')
    S('bs_gw', '  Goodwill', 'line', 'm1', data='bs_gw', bs=True, e26=lambda: f'={B1("bs_gw")}', ae=lambda: f'={P("bs_gw")}+{V("m_spend")}*(1-{V("m_ppe")}-{V("m_intp")})')
    S('bs_int', '  Intangible assets, net', 'line', 'm1', data='bs_int', bs=True,
      e26=lambda: f'={B1("bs_int")}-{SQE("d_amort")}', ae=lambda: f'={P("bs_int")}-{V("d_amort")}+{V("m_spend")}*{V("m_intp")}',
      note='Roll-forward: prior − amortization + acquired intangibles (M&A lever).')
    S('bs_onca', '  Operating lease ROU assets, deferred tax assets & other assets (derived)', 'line', 'm1', data='bs_onca', bs=True,
      e26=lambda: f'={B1("bs_onca")}', ae=lambda: f'={P("bs_onca")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_ppe")}:{V("bs_onca")}),"")')
    S('bs_l', "LIABILITIES AND SHAREHOLDERS' EQUITY", 'sub', 'gen')
    S('bs_ap', '  Accounts payable and accrued liabilities', 'line', 'm1', data='bs_ap', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_app")}')
    S('bs_std', '  Commercial paper, short-term borrowings & current portion of long-term debt', 'line', 'm1', data='bs_std', bs=True,
      fc=lambda: f'={V("ds_cp")}+MIN({V("ds_notes")},{V("ds_mat")})')
    S('bs_dr', '  Deferred revenue (current)', 'line', 'm1', data='bs_dr', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_drp")}')
    S('bs_ocl', '  Other current liabilities (current operating lease liabilities, other)', 'line', 'm1', data='bs_ocl', bs=True,
      e26=lambda: f'={B1("bs_ocl")}', ae=lambda: f'={P("bs_ocl")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_ap")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term debt', 'line', 'm1', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_std")}')
    S('bs_ol', '  Deferred revenue (non-current), deferred tax, uncertain tax positions, lease & other liabilities (derived)', 'line', 'm1', data='bs_ol', bs=True,
      e26=lambda: f'={B1("bs_ol")}+({V("cf_def")}-{ACT("cf_def")})', ae=lambda: f'={P("bs_ol")}+{V("cf_def")}')
    S('bs_tl', 'Total liabilities (incl. redeemable noncontrolling interest 2011–2014)', 'line_b', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_ol")}),"")')
    S('bs_eq', "  Total Moody's shareholders' equity (deficit)", 'line', 'm1', data='bs_eq', bs=True,
      e26=lambda: (f'={B1("bs_eq")}+{SQE("is_ni")}+({V("cf_div")}-{ACT("cf_div")})+({V("cf_bb")}-{ACT("cf_bb")})+{SQE("d_sbc")}+({V("cf_eq")}-{ACT("cf_eq")})'),
      ae=lambda: f'={P("bs_eq")}+{V("is_ni")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_sbc")}+{V("cf_eq")}',
      note='+ net income − dividends − repurchases + stock-based compensation + stock-plan cash (OCI / FX translation held flat).')
    S('bs_nci', '  Noncontrolling interests', 'line', 'm1', data='bs_nci', bs=True,
      e26=lambda: f'={B1("bs_nci")}+{SQE("is_nci")}', ae=lambda: f'={P("bs_nci")}+{V("is_nci")}',
      note='Forecast: + NCI share of net income (NCI dividends assumed nil; small).')
    S('bs_teq', "Total shareholders' equity (deficit)", 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")}+N({V("bs_nci")}),"")')
    S('bs_tle', "TOTAL LIABILITIES, NONCONTROLLING INTERESTS AND SHAREHOLDERS' EQUITY", 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),{chk(V("bs_ta"), V("bs_tle"), 1.5)},"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),{chk(V("bs_ta"), V("bs_ta_pub"), 1.5)},"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm1', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash vs cash-flow ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),{chk(V("bs_cash") + "+N(" + V("bs_rcash") + ")", V("cf_end"), 1.5)},"")')
    S('bs_rcash', '  Memo: restricted cash / held-for-sale cash in cash-flow cash (CF ending cash − BS cash)', 'memo', 'm1', data='bs_rcash', bs=True)
    S('bs_shares', '  Memo: shares outstanding at period end (m)', 'memo', 'm1', data='bs_shares', bs=True, e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input; year-end balances on full-year revenue)')
    S('wc_rev', '  Revenue — annualised (quarters × 4)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — receivables / revenue × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_drp', '  Deferred revenue (current) % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_dr")}/{V("wc_rev")},"")', e26_in=V0['wc']['dr'], ae_in=V0['wc']['dr'])
    S('wc_app', '  Accounts payable & accrued % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_rev")},"")',
      e26_in=V0['wc']['ap'], ae_in=V0['wc']['ap'], note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables + other current assets − payables & accrued − deferred revenue − other current liabilities)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_oca")}-{V("bs_ap")}-{V("bs_dr")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm1', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppa_h', 'Acquisitions — consideration & purchase-price allocation (closing-period column)', 'sub', 'gen')
    for k, lab in [('cons', 'Consideration — net assets acquired (net of cash acquired)'),
                   ('ca', 'Current assets acquired (receivables, other)'), ('ppe', 'Property & equipment'),
                   ('intang', 'Intangible assets (customer relationships, technology, trade names, data)'), ('gw', 'Goodwill'),
                   ('onca', 'Other non-current assets'), ('cl', 'Current liabilities assumed (incl. deferred revenue)'), ('debt', 'Debt assumed'),
                   ('ncl', 'Non-current liabilities assumed (deferred taxes, other)')]:
        S(f'ppa_{k}', f'  {lab}', 'sched', 'm1', data=f'ppa_{k}', ppa=True)
    S('ppa_chk', '  Check: assets acquired − liabilities assumed − consideration (should be 0)', 'check', 'm1',
      hist=lambda: (f'=IF(ISNUMBER({V("ppa_cons")}),ROUND(N({V("ppa_ca")})+N({V("ppa_ppe")})+N({V("ppa_intang")})+N({V("ppa_gw")})+N({V("ppa_onca")})'
                    f'-N({V("ppa_cl")})-N({V("ppa_debt")})-N({V("ppa_ncl")})-{V("ppa_cons")},0),"")'))
    S('ppa_names', '  Deal closed in the period', 'text', 'gen', data='ppa_names', ppa=True, textdata=True)
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; options, RSUs, PSUs)', 'sched', 'm1', ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.08)
    S('ds_h', 'Debt schedule (senior notes repaid at maturity and refinanced; commercial paper drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (short-term borrowings + current portion + long-term debt)', 'sched', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_cp")}', note=MAN['debt']['summary'])
    S('ds_notes', '  Senior notes & term loans (carrying value)', 'sched', 'm1', data='debt_lt',
      e26=lambda: f'={B1("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_iss', '  New notes issued (input)', 'sched', 'm1', e26_in=V0['iss_notes'][FYC], ae_in={y: V0['iss_notes'][y] for y in range(FYC + 1, FYL + 1)},
      note='2027E+: maturities refinanced plus ~$500m p.a. of incremental notes so that gross debt grows with Adjusted Operating Income at the leverage target instead of drawing commercial paper above the $1.25bn backstop (assumption; Moody\'s refinanced most maturities since 2010, but repaid the $700m 2025 notes from cash).')
    S('ds_repay', '  Notes repaid at maturity (input)', 'sched', 'm1', e26_in=V0['repay'][FYC], ae_in={y: V0['repay'][y] for y in range(FYC + 1, FYL + 1)},
      note=V0['repay_note'])
    S('ds_mat', '  Maturities in the following year (current portion)', 'sched', 'm1', e26_in=V0['mat'][FYC], ae_in={y: V0['mat'][y] for y in range(FYC + 1, FYL + 1)})
    S('ds_pre', '  Cash before commercial paper (opening cash + CFO + CFI + buybacks, dividends, equity, other financing + FX − notes repaid + issued)', 'sched', 'm1',
      e26=lambda: (f'={B1("bs_cash")}+({V("cf_cfo")}-{ACT("cf_cfo")})+({V("cf_cfi")}-{ACT("cf_cfi")})+({V("cf_bb")}-{ACT("cf_bb")})+({V("cf_div")}-{ACT("cf_div")})'
                   f'+({V("cf_eq")}-{ACT("cf_eq")})+({V("cf_ofin")}-{ACT("cf_ofin")})+({V("cf_fx")}-{ACT("cf_fx")})-{V("ds_repay")}+{V("ds_iss")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_bb")}+{V("cf_div")}+{V("cf_eq")}+{V("cf_ofin")}+{V("cf_fx")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_min', '  Minimum cash balance', 'sched', 'm1', e26_in=V0['min_cash'], ae_in=V0['min_cash'], note=V0['min_cash_note'])
    S('ds_cp', '  Commercial paper / revolver (year end)', 'sched', 'm1', data='debt_st',
      e26=lambda: f'=MAX(0,{B1("ds_cp")}+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_cp")}+{V("ds_min")}-{V("ds_pre")})',
      note=MAN['debt']['cp_note'])
    S('ds_head', f'  Memo: headroom vs the ${V0["rcf"]:,.0f}m revolving credit facility backing commercial paper (negative = would need other financing)', 'memo_calc', 'm1',
      e26=lambda: f'={V0["rcf"]}-{V("ds_cp")}', ae=lambda: f'={V0["rcf"]}-{V("ds_cp")}')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm1', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on opening notes %', 'sched', 'pct', ae_in=V0['r_notes'], note=V0['r_notes_note'])
    S('ds_r_cp', '  Interest rate on opening commercial paper %', 'sched', 'pct', ae_in=0.045)
    S('ds_fees', '  Interest on UTPs / tax liabilities, pension interest cost & fees ($m)', 'sched', 'm1', ae_in=V0['ds_fees'],
      note='1H26: UTP / tax-related interest $21m, pension interest component $14m (release interest table).')
    S('ds_r_cash', '  Interest income yield on opening cash %', 'sched', 'pct', ae_in=V0['r_cash'], note=V0['r_cash_note'])
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / Adjusted Operating Income, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / Adjusted Operating Income (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end)', 'sched', 'm1',
      ae=lambda: f'={P("ds_total")}-{P("cf_end")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_eq")}-{V("cf_ofin")}-{V("cf_fx")}')
    S('lev_tgt', '  Target net debt = target leverage × Adjusted Operating Income', 'sched', 'm1', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to target leverage', 'sched', 'm1', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash beyond the leverage target is returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of revenue', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_amort', '  Acquired-intangible amortization % of revenue', 'pct', 'pct', all=ratio('d_amort', 'is_rev'))
    S('hr_int', '  Net interest expense ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR(-{V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on Adjusted EBITA)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBITA (Adjusted Operating Income − depreciation)', 'line', 'm1', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate (adjusted)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("e_rate")}+0,0.24)')
    S('ra_nopat', 'NOPAT = Adjusted EBITA × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity (incl. NCI)', 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),{V("bs_teq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − cash − short-term investments', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")}-N({V("bs_sti")}),"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR(IF({V("ra_ic")}<0.25*{V("is_rev")},"n/m",{V("ra_nopat")}/{V("ra_ic")}),"n/a")',
      note='Book invested capital is small or negative after two decades of buybacks funded by debt (equity deficit 2007–11 and 2014–17); ROIC is shown as n/m where IC < 25% of revenue (model convention).')
    S('ra_mg', '  Margin = Adjusted EBITA / Revenue', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Revenue / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBITA × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm1', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangible assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-({V("bs_gw")}+{V("bs_int")}),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. short-term debt)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})),"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")',
      note='Net tangible assets are negative in most years (deferred revenue and accruals exceed tangible assets), so RONTA is not meaningful when NTA ≤ 0.')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', "Net income attributable to Moody's", 'line', 'm1', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Moody's shareholders' equity (deficit)", 'line', 'm1', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(IF({V("roe_eq")}>0,{V("roe_ni")}/{V("roe_eq")},"n/m"),"n/a")',
      note='n/m where shareholders\' equity is negative (deficit 2007–11 and 2014–17 after buybacks).')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash − short-term investments', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted Operating Income (= Adjusted EBITDA)', 'line', 'm1', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / Adjusted Operating Income (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_gx', 'Total debt / Adjusted Operating Income (x) — gross leverage', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("ds_total")}/{V("lv_eb")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+({LQ}{R["sh_dil"]}-{LQ}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interests (USDm)', 'line', 'm', e26=lambda: f'={V("bs_nci")}', ae=lambda: f'={V("bs_nci")}')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Revenue', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted Operating Income (Adjusted EBITDA)', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted EBITA', lambda: f'=IFERROR({V("v_ev")}/{V("r_ebit")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (adjusted diluted EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
