"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, H2, B1, E26a

def build_spec2(V0):
    S = add
    def e26f(key, q4):          # 2026E flow = 1H26 actual + 2H26 estimate
        return lambda: f'={ACT(key)}+{q4()}'
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENTS OF CASH FLOWS (condensed)', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 1H26 actual + 2H estimate; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net earnings / (loss)', 'line', 'm1', data='cf_ni', flow=True, fc=lambda: f'={V("is_ni")}', e26=e26f('cf_ni', lambda: H2('is_ni')))
    S('cf_adj', 'Non-cash items:', 'sub', 'gen')
    S('cf_dda', '  Depreciation and amortization', 'line', 'm1', data='cf_dda', flow=True, fc=lambda: f'={V("d_dda")}', e26=e26f('cf_dda', lambda: H2('d_dda')))
    S('cf_sbc', '  Share-based plans expense', 'line', 'm1', data='cf_sbc', flow=True, fc=lambda: f'={V("d_sbc")}', e26=e26f('cf_sbc', lambda: H2('d_sbc')))
    S('cf_401k', '  Treasury shares issued for 401(k) contributions', 'line', 'm1', data='cf_401k', flow=True, fc=lambda: f'={V("d_401k")}', e26=e26f('cf_401k', lambda: H2('d_401k')))
    S('cf_pens', '  Pension and other postretirement plans', 'line', 'm1', data='cf_pens', flow=True, e26=lambda: f'={ACT("cf_pens")}+{V0["pens_2h"]}', ae_in=V0['pens_cf'],
      note='Expense / income less contributions and benefit payments (non-cash FAS/CAS recovery, non-operating pension). Forecast input (assumption); offsets the pension & retiree-health liabilities.')
    S('cf_onc', '  Other non-cash items (reach-forward losses, gains on dispositions, impairments, other; derived)', 'line', 'm1', data='cf_onc', flow=True,
      e26=lambda: f'={ACT("cf_onc")}-{H2("is_gain")}', ae=lambda: f'=-{V("is_gain")}',
      note='History: operating cash flow − the lines above and below (includes 777X / 767 reach-forward losses 2024–25 and the −$9.7bn 2025 divestiture gain).')
    S('cf_wc', '  Working capital & other operating items (receivables, inventories, advances, payables, accrued, taxes, financing receivables)', 'line', 'm1', data='cf_wc', flow=True,
      e26=lambda: (f'={ACT("cf_wc")}-({V("bs_ar")}-{B1("bs_ar")})-({V("bs_inv")}-{B1("bs_inv")})-({V("bs_oca")}-{B1("bs_oca")})'
                   f'+({V("bs_ap")}-{B1("bs_ap")})+({V("bs_adv")}-{B1("bs_adv")})+({V("bs_ocl")}-{B1("bs_ocl")})'),
      ae=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_inv")}-{P("bs_inv")})-({V("bs_oca")}-{P("bs_oca")})'
                  f'+({V("bs_ap")}-{P("bs_ap")})+({V("bs_adv")}-{P("bs_adv")})+({V("bs_ocl")}-{P("bs_ocl")})'),
      note='Forecast linked to the balance sheet: −Δ(receivables, inventories, other current assets) + Δ(payables, advances & progress billings, other current liabilities).')
    S('cf_cfo', 'Net cash provided / (used) by operating activities', 'line_b', 'm1', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Payments for property, plant and equipment', 'line', 'm1', data='cf_capex', flow=True,
      e26=lambda: f'=-{PT("pt_capex")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='2026E: point estimate (1H26 $2.0bn; investments in Charleston and St. Louis sites, 737 North Line). 2027E+: revenues × capex %.')
    S('cf_acq', 'Acquisitions, net of cash acquired', 'line', 'm1', data='cf_acq', flow=True, e26=lambda: f'={ACT("cf_acq")}', ae=lambda: f'=-{V("m_spend")}',
      note='FY2025: Spirit AeroSystems ($1.2bn cash; total consideration $8.4bn incl. $4.7bn of Boeing shares). 2027E+: M&A lever.')
    S('cf_divest', 'Proceeds from dispositions', 'line', 'm1', data='cf_divest', flow=True, e26=lambda: f'={ACT("cf_divest")}', ae_in=0.0,
      note='FY2025: Digital Aviation Solutions (Jeppesen, ForeFlight, AerData, OzRunways) to Thoma Bravo, $10.55bn (closed 31-Oct-2025).')
    S('cf_invnet', 'Net (contributions to) / proceeds from investments (short-term and other investments)', 'line', 'm1', data='cf_invnet', flow=True,
      e26=lambda: f'={ACT("cf_invnet")}-({V("bs_sti")}-{B1("bs_sti")})', ae=lambda: f'=-({V("bs_sti")}-{P("bs_sti")})')
    S('cf_oinv', 'Other investing activities (PP&E disposals, supplier notes, distribution rights; derived)', 'line', 'm1', data='cf_oinv', flow=True, e26=lambda: f'={ACT("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Net cash provided / (used) by investing activities', 'line_b', 'm1', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_debt', 'New borrowings less debt repayments', 'line', 'm1', data='cf_debt', flow=True,
      e26=lambda: f'={ACT("cf_debt")}+{V("ds_total")}-{B1("ds_total")}', ae=lambda: f'={V("ds_net")}',
      note='Per the debt schedule: maturities repaid, refinancing input, revolver / commercial paper drawn or repaid to the minimum cash balance.')
    S('cf_bb', 'Common shares repurchased', 'line', 'm1', data='cf_bb', flow=True, e26=lambda: f'={ACT("cf_bb")}-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='No repurchases since Q1-2020. 2027E+ = leverage plug (surplus cash returned once net debt / adjusted EBITDA is below the scenario target).')
    S('cf_div', 'Dividends paid (common; mandatory convertible preferred from Q1-25)', 'line', 'm1', data='cf_div', flow=True,
      e26=lambda: f'={ACT("cf_div")}-{H2("is_pref")}', ae=lambda: f'=-{V("dps")}*{V("bb_beg")}-{V("is_pref")}')
    S('cf_eq', 'Common / preferred stock issuance and stock options exercised', 'line', 'm1', data='cf_eq', flow=True, e26=lambda: f'={ACT("cf_eq")}', ae_in=0.0,
      note='FY2024: $18.2bn common (112.5m shares at $143) + $5.66bn 6.00% mandatory convertible preferred (net of costs), Oct-2024.')
    S('cf_ofin', 'Other financing activities (employee taxes on share-based payments, distribution-rights financing, other; derived)', 'line', 'm1', data='cf_ofin', flow=True,
      e26=lambda: f'={ACT("cf_ofin")}', ae_in=0.0)
    S('cf_cff', 'Net cash provided / (used) by financing activities', 'line_b', 'm1', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_debt")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of exchange rate changes on cash', 'line', 'm1', data='cf_fx', flow=True, e26=lambda: f'={ACT("cf_fx")}', ae_in=0.0)
    S('cf_net', 'Net increase / (decrease) in cash (incl. restricted from 2018)', 'line', 'm1', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")}),"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}')
    S('cf_beg', 'Cash — beginning of period', 'line', 'm1', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period (incl. restricted cash from 2018)', 'line_b', 'm1', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_restr', '  Memo: restricted cash included in investments (cash-flow statement "less restricted cash" line)', 'memo', 'm1', data='cf_restr', bs=True,
      e26=lambda: f'={B1("cf_restr")}', ae=lambda: f'={P("cf_restr")}',
      note='ASU 2016-18 (2018): the cash-flow statement includes restricted cash (in Investments). Forecast held at the 30-Jun-2026 level.')
    S('cf_chk1', '  Check: beginning cash + CFO + CFI + CFF + FX = ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},1),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),ROUND(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")},1),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (company definition: operating cash flow − payments for PP&E)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")},"")')
    S('fcf_pub', '  Company-published free cash flow', 'memo', 'm1', data='fcf_pub', flow=True)
    S('fcf_chk', '  Check: model vs company-published free cash flow (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("fcf_pub")}),ROUND({V("fcf")}-{V("fcf_pub")},1),"n/p")')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of revenues', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / core earnings conversion %', 'pct', 'pct', all=lambda: f'=IF(AND(ISNUMBER({V("fcf")}),N({V("e_coreni")})>0),IFERROR({V("fcf")}/{V("e_coreni")},""),"n/m")')
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / adjusted EBITDA %', 'pct', 'pct', all=lambda: f'=IF(AND(ISNUMBER({V("fcf")}),N({V("r_adj")})>0),IFERROR({V("fcf")}/{V("r_adj")},""),"n/m")')
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of revenues', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")', ae_in=V0['capex_pct'],
      note='2027E+ input: elevated for the 737 North Line, 787 Charleston expansion and 777X; normalising toward 3%.')
    S('capex_dda', '  Capex / D&A (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("d_dda")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE SCHEDULE (buybacks, 401(k) treasury-share issuance, preferred conversion)', 'section',
      note='SHARES — 2026E = 2H from shares outstanding at 30-Jun-2026; 2027E+ buybacks via the leverage plug; preferred converts Oct-2027')
    S('bb_px', '  Avg buyback / issuance price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = 2H)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_k401', '  Treasury shares issued for 401(k) contributions (m)', 'line', 'm2', e26=lambda: f'=IFERROR({H2("d_401k")}/{V("bb_px")},0)',
      ae=lambda: f'=IFERROR({V("d_401k")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans (m)', 'driver', 'm2', e26_in=V0['iss_2h'], ae_in=V0['iss_ae'])
    S('bb_mcps', '  Common shares issued on conversion of the mandatory convertible preferred (m)', 'line', 'm2', e26_in=0.0,
      ae=lambda: (f'={V("mc_sh")}' if CTX.col.year == 2027 else '=0'),
      note='5.75m preferred shares convert on ~15-Oct-2027 into 5.8280–6.9940 common shares each (10-K): minimum ratio above $171.59, maximum below $142.98.')
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from shares outstanding at 30-Jun-2026 (1,012.3m issued − treasury shares; balance-sheet caption).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_k401")}+{V("bb_iss")}+{V("bb_mcps")}',
      ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_k401")}+{V("bb_iss")}+{V("bb_mcps")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since 2H26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED STATEMENTS OF FINANCIAL POSITION (condensed)', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Jun-2026 balance sheet + 2H flows; 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm1', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}-{V("cf_restr")}')
    S('bs_sti', '  Short-term and other investments', 'line', 'm1', data='bs_sti', bs=True, e26=lambda: f'={B1("bs_sti")}', ae=lambda: f'={P("bs_sti")}',
      note='Held at the 30-Jun-2026 level (assumption); counted with cash in net debt.')
    S('bs_ar', '  Accounts receivable and unbilled receivables, net', 'line', 'm1', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_inv', '  Inventories', 'line', 'm1', data='bs_inv', bs=True,
      e26=lambda: f'={B1("bs_inv")}+{V("cal_cfo_pre")}+{V("cf_capex")}-{V("cal_fcf")}',
      ae=lambda: f'={V("wc_cogs")}*{V("wc_dio")}/365',
      note='2026E: solved so that 2026 free cash flow = the scenario target (UNVERIFIED $1–3bn); 2027E+: inventory days on cost of sales (737 / 787 / 777X inventory unwind).')
    S('bs_oca', '  Current customer financing, deferred / income taxes, held for sale & other current assets', 'line', 'm1', data='bs_oca', bs=True,
      e26=lambda: f'={B1("bs_oca")}', ae=lambda: f'={P("bs_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_ppe', '  Property, plant and equipment, net', 'line', 'm1', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-({V("cf_capex")}-{ACT("cf_capex")})-({H2("d_dda")}-{V0["amort_2h"]})',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-({V("d_dda")}-{V("d_amort_sch")})+{V("m_spend")}*{V("m_ppe")}',
      note='Roll-forward: prior − capex (negative cash flow) − depreciation (D&A − intangible amortization) + acquired PP&E.')
    S('bs_gw', '  Goodwill', 'line', 'm1', data='bs_gw', bs=True, e26=lambda: f'={B1("bs_gw")}', ae=lambda: f'={P("bs_gw")}+{V("m_spend")}*(1-{V("m_ppe")}-{V("m_intp")})',
      note='Spirit AeroSystems provisional goodwill $10.0bn (BCA), Dec-2025.')
    S('bs_int', '  Acquired intangible assets, net', 'line', 'm1', data='bs_int', bs=True,
      e26=lambda: f'={B1("bs_int")}-{V0["amort_2h"]}', ae=lambda: f'=MAX(0,{P("bs_int")}-{V("d_amort_sch")}+{V("m_spend")}*{V("m_intp")})')
    S('bs_onca', '  Customer financing, deferred taxes, investments, pension assets & other assets (derived)', 'line', 'm1', data='bs_onca', bs=True,
      e26=lambda: f'={B1("bs_onca")}', ae=lambda: f'={P("bs_onca")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_ppe")}:{V("bs_onca")}),"")')
    S('bs_l', 'LIABILITIES AND EQUITY', 'sub', 'gen')
    S('bs_ap', '  Accounts payable', 'line', 'm1', data='bs_ap', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dpo")}/365')
    S('bs_adv', '  Advances and progress billings (advances and billings in excess of related costs)', 'line', 'm1', data='bs_adv', bs=True,
      fc=lambda: f'={V("wc_rev")}*{V("wc_advp")}')
    S('bs_std', '  Short-term debt and current portion of long-term debt', 'line', 'm1', data='bs_std', bs=True, fc=lambda: f'={V("ds_rev")}+MIN({V("ds_notes")},{V("ds_mat")})',
      note='Revolver / commercial paper + scheduled maturities in the following year.')
    S('bs_ocl', '  Accrued liabilities & other current liabilities', 'line', 'm1', data='bs_ocl', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_oclp")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_ap")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term debt', 'line', 'm1', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_std")}')
    S('bs_pens', '  Accrued pension plan liability, net & accrued retiree health care', 'line', 'm1', data='bs_pens', bs=True,
      e26=lambda: f'={B1("bs_pens")}+({V("cf_pens")}-{ACT("cf_pens")})', ae=lambda: f'={P("bs_pens")}+{V("cf_pens")}')
    S('bs_ol', '  Deferred taxes, non-current income taxes & other long-term liabilities (derived)', 'line', 'm1', data='bs_ol', bs=True,
      e26=lambda: f'={B1("bs_ol")}', ae=lambda: f'={P("bs_ol")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_ol")}),"")')
    S('bs_eq', "  Total shareholders' equity / (deficit) (incl. mandatory convertible preferred)", 'line', 'm1', data='bs_eq', bs=True,
      e26=lambda: (f'={B1("bs_eq")}+{H2("is_niattr")}+({V("cf_div")}-{ACT("cf_div")})+({V("cf_bb")}-{ACT("cf_bb")})+{H2("d_sbc")}+{H2("d_401k")}+({V("cf_eq")}-{ACT("cf_eq")})'),
      ae=lambda: f'={P("bs_eq")}+{V("is_niattr")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_sbc")}+{V("cf_401k")}+{V("cf_eq")}',
      note='+ net earnings attributable − dividends (common & preferred) − repurchases + share-based plans + 401(k) treasury shares + issuance (AOCI held flat). Deficit 2018–Q2-25.')
    S('bs_nci', '  Noncontrolling interests', 'line', 'm1', data='bs_nci', bs=True, e26=lambda: f'={B1("bs_nci")}+{H2("is_nci")}', ae=lambda: f'={P("bs_nci")}+{V("is_nci")}')
    S('bs_teq', 'Total equity / (deficit)', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")}+N({V("bs_nci")}),"")')
    S('bs_tle', 'TOTAL LIABILITIES AND EQUITY', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),ROUND({V("bs_ta")}-{V("bs_tle")},1),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),ROUND({V("bs_ta")}-{V("bs_ta_pub")},1),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm1', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash vs cash-flow ending cash less restricted cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),ROUND({V("bs_cash")}-({V("cf_end")}-N({V("cf_restr")})),1),"")')
    S('bs_shares', '  Memo: shares outstanding at period end (issued less treasury, m)', 'memo', 'm1', data='bs_shares', bs=True, e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input; year-end levels)')
    S('wc_rev', '  Revenues — annualised (quarters × 4)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_cogs', '  Cost of products & services — annualised', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_cogs")}*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  Receivable days (incl. unbilled) — receivables / revenues × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")',
      e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_dio', '  Inventory days — inventories / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_inv")}/{V("wc_cogs")}*365,"")',
      e26=lambda: f'=IFERROR({V("bs_inv")}/{V("wc_cogs")}*365,"")', ae_in=V0['dio'],
      note='2026E: output of the free-cash-flow solve. 2027E+: input path declining as 737-7/-10 and 777X inventory is delivered (YE25 363 days; 2018: 281 days). Assumption.')
    S('wc_dpo', '  Payable days — payables / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_cogs")}*365,"")', e26_in=V0['wc']['dpo'], ae_in=V0['wc']['dpo'])
    S('wc_advp', '  Advances & progress billings % of revenues', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_adv")}/{V("wc_rev")},"")', e26_in=V0['wc']['adv'], ae_in=V0['advp'],
      note='Customer advances fund the order book (backlog $715bn at 30-Jun-2026); drifting down as deliveries catch up with pre-delivery payments (input).')
    S('wc_oclp', '  Accrued & other current liabilities % of revenues', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")',
      e26_in=V0['wc']['ocl'], ae_in=V0['wc']['ocl'], note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables + inventories + other current assets − payables − advances − other current liabilities)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_inv")}+{V("bs_oca")}-{V("bs_ap")}-N({V("bs_adv")})-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of revenues', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm1', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('cal_h2', '2026 free-cash-flow solve (2026E column)', 'sub', 'gen')
    S('cal_cfo_pre', '  Operating cash flow before the 2H26 change in inventories (helper)', 'sched', 'm1',
      e26=lambda: (f'={V("cf_ni")}+{V("cf_dda")}+{V("cf_sbc")}+{V("cf_401k")}+{V("cf_pens")}+{V("cf_onc")}+{ACT("cf_wc")}-({V("bs_ar")}-{B1("bs_ar")})-({V("bs_oca")}-{B1("bs_oca")})'
                   f'+({V("bs_ap")}-{B1("bs_ap")})+({V("bs_adv")}-{B1("bs_adv")})+({V("bs_ocl")}-{B1("bs_ocl")})'),
      note='Closed-form solve: year-end inventories = 30-Jun-2026 inventories + this helper + capex − free-cash-flow target (no circularity).')
    S('cal_dinv', '  Implied 2H26 change in inventories (solved)', 'sched', 'm1', e26=lambda: f'={V("bs_inv")}-{B1("bs_inv")}')
    S('ppa_h', 'Acquisitions — consideration & purchase-price allocation (closing-period column)', 'sub', 'gen')
    for k, lab in [('cons', 'Consideration — total fair value (incl. shares, settled loans / advances, debt repaid)'), ('cash', 'Cash acquired'),
                   ('ca', 'Receivables, unbilled receivables & inventories'), ('ppe', 'Property, plant & equipment'), ('intang', 'Acquired intangible assets'), ('gw', 'Goodwill'),
                   ('onca', 'Other assets & other'), ('cl', 'Accounts payable, accrued liabilities (incl. $1,065m off-market contracts) & advances'),
                   ('debt', 'Debt assumed (short-term and long-term)'), ('ncl', 'Other long-term liabilities')]:
        S(f'ppa_{k}', f'  {lab}', 'sched', 'm1', data=f'ppa_{k}', ppa=True)
    S('ppa_chk', '  Check: assets acquired − liabilities assumed − consideration (should be 0)', 'check', 'm1',
      hist=lambda: (f'=IF(ISNUMBER({V("ppa_cons")}),ROUND({nsum(["ppa_cash", "ppa_ca", "ppa_ppe", "ppa_intang", "ppa_gw", "ppa_onca"])}'
                    f'-N({V("ppa_cl")})-N({V("ppa_debt")})-N({V("ppa_ncl")})-{V("ppa_cons")},1),"")'))
    S('ppa_names', '  Deal closed in the period', 'text', 'gen', data='ppa_names', ppa=True, textdata=True)
    S('rf_h', 'Share count, preferred conversion & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; stock units, options)', 'sched', 'm1', ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback / issuance pricing)', 'sched', 'pct', ae_in=0.08)
    S('mc_sh', '  Common shares on conversion of the mandatory convertible preferred (m)', 'sched', 'm2',
      e26=lambda: f'=5.75*IF({V("v_px")}>=1000/5.828,5.828,IF({V("v_px")}<=1000/6.994,6.994,1000/{V("v_px")}))',
      ae=lambda: (f'=5.75*IF({V("bb_px")}>=1000/5.828,5.828,IF({V("bb_px")}<=1000/6.994,6.994,1000/{V("bb_px")}))' if CTX.col.year == 2027 else '=0'),
      note='5,750,000 shares × conversion rate (5.8280 at ≥ $171.59; 6.9940 at ≤ $142.98; $1,000 ÷ price in between). 2026E: at the current price (valuation share count); 2027E: at the conversion-date price.')
    S('ds_h', 'Debt schedule (notes & term loans repaid at maturity, refinancing input; revolver / commercial paper drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (short-term + long-term)', 'sched', 'm1', hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")',
      fc=lambda: f'={V("ds_notes")}+{V("ds_rev")}', note=V0['debt_note'])
    S('ds_notes', '  Notes, term loans, finance leases & other debt', 'sched', 'm1', hist=lambda: f'={V("ds_total")}',
      e26=lambda: f'={B1("ds_total")}-{V("ds_repay")}+{V("ds_iss")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_repay', '  Scheduled repayments (input)', 'sched', 'm1', e26_in=V0['repay'][FYC], ae_in={y: V0['repay'][y] for y in range(FYC + 1, FYL + 1)}, note=V0['repay_note'])
    S('ds_refi', '  % of repayments refinanced with new debt (input)', 'sched', 'pct', e26_in=0.0, ae_in=V0['refi'])
    S('ds_iss', '  New debt issued', 'sched', 'm1', e26=lambda: f'={V("ds_repay")}*{V("ds_refi")}', ae=lambda: f'={V("ds_repay")}*{V("ds_refi")}')
    S('ds_mat', '  Maturities in the following year (current portion)', 'sched', 'm1', e26_in=V0['mat'][FYC], ae_in={y: V0['mat'][y] for y in range(FYC + 1, FYL + 1)})
    S('ds_pre', '  Cash before revolver draws / repayments (opening cash + CFO + CFI + buybacks, dividends, equity, other financing + FX − repaid + issued)', 'sched', 'm1',
      e26=lambda: (f'={B1("cf_end")}+({V("cf_cfo")}-{ACT("cf_cfo")})+({V("cf_cfi")}-{ACT("cf_cfi")})+({V("cf_bb")}-{ACT("cf_bb")})+({V("cf_div")}-{ACT("cf_div")})'
                   f'+({V("cf_eq")}-{ACT("cf_eq")})+({V("cf_ofin")}-{ACT("cf_ofin")})+({V("cf_fx")}-{ACT("cf_fx")})-{V("ds_repay")}+{V("ds_iss")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_bb")}+{V("cf_div")}+{V("cf_eq")}+{V("cf_ofin")}+{V("cf_fx")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_min', '  Minimum cash balance (cash flow basis, incl. restricted)', 'sched', 'm1', e26_in=V0['min_cash'], ae_in=V0['min_cash'])
    S('ds_rev', '  Revolver / commercial paper (year end)', 'sched', 'm1', hist=lambda: '=0',
      e26=lambda: f'=MAX(0,N({B1("ds_rev")})+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_rev")}+{V("ds_min")}-{V("ds_pre")})',
      note='$10.0bn unused revolving credit lines at 30-Jun-2026 (Q2-26 10-Q; $3.0bn 364-day to Aug-2026, $3.0bn to Aug-2028, $4.0bn to May-2029). Shortfalls below the minimum cash balance are drawn; surplus repays.')
    S('ds_head', '  Memo: revolver headroom vs the $7.0bn multi-year commitments (negative = would need other financing)', 'memo_calc', 'm1',
      e26=lambda: f'=7000-{V("ds_rev")}', ae=lambda: f'=7000-{V("ds_rev")}')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm1', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on opening notes & term loans %', 'sched', 'pct', ae_in=V0['r_notes'], note=V0['r_notes_note'])
    S('ds_r_rev', '  Interest rate on opening revolver / commercial paper %', 'sched', 'pct', ae_in=0.05)
    S('ds_r_cash', '  Yield on opening cash & short-term investments %', 'sched', 'pct', ae_in=V0['yield'], note=V0['yield_note'])
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / adjusted EBITDA, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end; debt − cash − short-term investments)', 'sched', 'm1',
      ae=lambda: f'={P("ds_total")}-{P("bs_cash")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_eq")}-{V("cf_ofin")}-{V("cf_fx")}-{V("bs_sti")}')
    S('lev_tgt', '  Target net debt = target leverage × adjusted EBITDA', 'sched', 'm1', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to target leverage', 'sched', 'm1', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash beyond the leverage target is returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  D&A % of revenues', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_int', '  Interest and debt expense ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted EBIT = core operating earnings excl. divestiture gains)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT (core operating earnings excl. gains on dispositions)', 'line', 'm1', ann=True, all=lambda: f'={V("r_ebit")}-{V("r_gain")}')
    S('ra_t', 'Tax rate (statutory 21% from 2018; 35% before)', 'line', 'pct', ann=True, all=lambda: '=0.21' if CTX.col.year >= 2018 else '=0.35')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity / (deficit)', 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),{V("bs_teq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − cash − short-term investments', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")}-{V("bs_sti")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR(IF({V("ra_ic")}>0,{V("ra_nopat")}/{V("ra_ic")},"n/m"),"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Revenues', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Revenues / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR(IF({V("ra_ic")}>0,{V("is_rev")}/{V("ra_ic")},"n/m"),"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm1', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & acquired intangible assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-({V("bs_gw")}+{V("bs_int")}),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total current liabilities excl. short-term debt)', 'line', 'm1', ann=True,
      all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})),"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net earnings attributable', 'line', 'm1', ann=True, all=lambda: f'={V("is_niattr")}')
    S('roe_eq', "Shareholders' equity / (deficit)", 'line', 'm1', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net earnings / Equity (n/m when equity ≤ 0)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(IF({V("roe_eq")}>0,{V("roe_ni")}/{V("roe_eq")},"n/m"),"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash − short-term investments', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA (model)', 'line', 'm1', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x) (n/m when EBITDA ≤ 0)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR(IF({V("lv_eb")}>0,{V("lv_nd")}/{V("lv_eb")},"n/m"),"n/a")')
    S('lv_gx', 'Total debt / adjusted EBITDA (x)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR(IF({V("lv_eb")}>0,{V("ds_total")}/{V("lv_eb")},"n/m"),"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m; 2026E incl. preferred conversion shares)', 'line', 'm1',
      e26=lambda: f'={V("bb_end")}+{V0["dil_e26"]}+{V("mc_sh")}', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm; debt − cash − short-term investments)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_pens', 'Pension & retiree health liabilities, net (debt-like, pre-tax)', 'line', 'm', e26=lambda: f'={V("bs_pens")}', ae=lambda: f'={V("bs_pens")}',
      note='Unfunded pension plan liability + accrued retiree health care (balance sheet). Included in EV and the DCF equity bridge.')
    S('v_nci', 'Noncontrolling interests (USDm)', 'line', 'm', e26=lambda: f'={V("bs_nci")}', ae=lambda: f'={V("bs_nci")}')
    S('v_dl', 'Debt-like items: pension & retiree health liabilities + noncontrolling interests (USDm)', 'line', 'm',
      e26=lambda: f'={V("v_pens")}+{V("v_nci")}', ae=lambda: f'={V("v_pens")}+{V("v_nci")}')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_pens")}+{V("v_nci")},"n/a")',
      ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_pens")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Revenues', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR(IF({V("r_adj")}>0,{V("v_ev")}/{V("r_adj")},"n/m"),"n/a")'),
                      ('v_evop', '  EV / Core operating earnings', lambda: f'=IFERROR(IF({V("o_core")}>0,{V("v_ev")}/{V("o_core")},"n/m"),"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR(IF({V("eps_dil")}>0,{V("v_px")}/{V("eps_dil")},"n/m"),"n/a")'),
                      ('v_pea', '  P / E (core EPS)', lambda: f'=IFERROR(IF({V("e_eps")}>0,{V("v_px")}/{V("e_eps")},"n/m"),"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
