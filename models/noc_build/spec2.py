"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, ACT0, QEc, B1, chk

def build_spec2(V0):
    S = add
    def e26f(key, q4):          # 2026E flow = 9M actual (Q1-Q3/26) + Q4/26E estimate
        return lambda: f'={ACT(key)}+{q4()}'
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 9M 2026 actual + Q4 estimate; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net earnings', 'line', 'm', data='cf_ni', flow=True, fc=lambda: f'={V("is_ni")}', e26=e26f('cf_ni', lambda: QEc('is_ni')))
    S('cf_adj', 'Adjustments to reconcile to net cash provided by operating activities:', 'sub', 'gen')
    S('cf_dda', '  Depreciation & amortization', 'line', 'm', data='cf_dda', flow=True, fc=lambda: f'={V("is_dda")}', e26=e26f('cf_dda', lambda: QEc('is_dda')))
    S('cf_sbc', '  Stock-based compensation', 'line', 'm', data='cf_sbc', flow=True, fc=lambda: f'={V("is_sbc")}', e26=e26f('cf_sbc', lambda: QEc('is_sbc')))
    S('cf_def', '  Deferred income taxes', 'line', 'm', data='cf_def', flow=True, e26=lambda: f'={ACT("cf_def")}+{PT("pt_def")}', ae_in=V0['def_ae'],
      note='2025 $548m (2024 −$582m); 9M 2026 $651m (Section 174 / bonus depreciation timing). Q4/26E point estimate; 2027E+ input (assumption, unwinding).')
    S('cf_pens', '  Pension & OPB: non-cash FAS (benefit) expense reversed and contributions (MTM, net periodic pension & OPB income, contributions, retiree benefits)', 'line', 'm', data='cf_pens', flow=True,
      e26=lambda: f'={ACT("cf_pens")}+{QEc("cf_pens_q")}', ae=lambda: f'=-{V("is_nonop")}-{V("is_mtm")}+{V("rc_svc")}-{V("cf_contrib")}',
      note=('History: sum of the cash-flow lines for MTM, net periodic pension & OPB income, pension & OPB contributions and (2009–20) retiree benefits (2009–15 from XBRL). '
            'Forecast: −(non-operating FAS benefit + MTM) + FAS service cost (expensed in costs, non-cash) − cash contributions.'))
    S('cf_pens_q', '  Q4/26E pension & OPB cash-flow items (helper: −non-operating FAS benefit + FAS service cost ÷ 4 − contributions)', 'memo_calc', 'm',
      qe=lambda: f'=-{V("is_nonop")}-{V("is_mtm")}+{V("rc_svc_in", E26)}/4-{PT("pt_contrib")}')
    S('cf_contrib', '  Pension & OPB cash contributions (input)', 'driver', 'm', e26=lambda: f'={ACT("cf_contrib")}+{PT("pt_contrib")}' if False else f'={PT("pt_contrib")}*4', ae_in=V0['contrib_ae'],
      note='2025 ~$130m, 9M 2026 $92m (mostly OPB; qualified pension plans overfunded). 2026E and 2027E+ inputs (assumption).')
    S('cf_gain', '  Gains on sales of businesses, B-21 loss provision and goodwill impairment (non-cash items as presented)', 'line', 'm', data='cf_gain', flow=True, fc=lambda: '=0', e26=lambda: f'={ACT("cf_gain")}')
    S('cf_wc', '  Working capital & other operating items, net (derived)', 'line', 'm', data='cf_wc', flow=True,
      e26=lambda: (f'={ACT("cf_wc")}-({V("bs_ar")}-{B1("bs_ar")})-({V("bs_unb")}-{B1("bs_unb")})-({V("bs_inv")}-{B1("bs_inv")})-({V("bs_oca")}-{B1("bs_oca")})'
                   f'+({V("bs_ap")}-{B1("bs_ap")})+({V("bs_accr")}-{B1("bs_accr")})+({V("bs_adv")}-{B1("bs_adv")})+({V("bs_ocl")}-{B1("bs_ocl")})'),
      ae=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_unb")}-{P("bs_unb")})-({V("bs_inv")}-{P("bs_inv")})-({V("bs_oca")}-{P("bs_oca")})'
                  f'+({V("bs_ap")}-{P("bs_ap")})+({V("bs_accr")}-{P("bs_accr")})+({V("bs_adv")}-{P("bs_adv")})+({V("bs_ocl")}-{P("bs_ocl")})'),
      note=('History: net cash from operations − net earnings − D&A − SBC − deferred taxes − pension items − gains (residual; 2009–15 releases use the direct method). '
            'Forecast linked to the balance sheet: −Δ(receivables, unbilled, inventoried costs, other current assets) + Δ(payables, accrued compensation, advances, other current liabilities).'))
    S('cf_cfo', 'Net cash provided by operating activities', 'line_b', 'm', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})-N({V("cf_pens_q")})-N({V("cf_contrib")})',
      note='Σ operating lines (the Q4 helper and contributions input rows are excluded from the sum).')
    S('cf_capex', 'Capital expenditures', 'line', 'm', data='cf_capex', flow=True, e26=lambda: f'=-{PT("pt_capex")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='2026E: input (9M $775m; 2025 $1,450m). 2027E+: sales × capex %.')
    S('cf_acq', 'Business acquisitions, net of cash acquired', 'line', 'm', data='cf_acq', flow=True, e26=lambda: f'={ACT("cf_acq")}', ae=lambda: f'=-{V("m_spend")}',
      note='Orbital ATK $7,657m (2018). 2027E+: M&A lever.')
    S('cf_divest', 'Proceeds from divestitures, sale of equipment to a customer and investments', 'line', 'm', data='cf_divest', flow=True, e26=lambda: f'={ACT("cf_divest")}', ae_in=0.0,
      note='IT services $3.4bn (2021); training services $333m (2025); sale of equipment to a customer $371m (Q3 2026); investments.')
    S('cf_oinv', 'Other investing activities, net (derived)', 'line', 'm', data='cf_oinv', flow=True, e26=lambda: f'={ACT("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Net cash used in investing activities', 'line_b', 'm', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_debt', 'Net debt issuance / (repayment) (notes, commercial paper and credit facilities)', 'line', 'm', data='cf_debt', flow=True,
      e26=lambda: f'={ACT("cf_debt")}+{V("ds_total")}-{B1("ds_total")}', ae=lambda: f'={V("ds_net")}',
      note='Per the debt schedule: maturities repaid and refinanced; commercial paper / revolver drawn or repaid to the minimum cash balance.')
    S('cf_div', 'Cash dividends paid', 'line', 'm', data='cf_div', flow=True, e26=lambda: f'={ACT("cf_div")}-{QEc("dps")}*{QEc("sh_basic")}', ae=lambda: f'=-{V("dps")}*{V("bb_beg")}',
      note='2027E+ = DPS × beginning shares (no circularity with the buyback plug).')
    S('cf_bb', 'Common stock repurchases', 'line', 'm', data='cf_bb', flow=True, e26=lambda: f'={ACT("cf_bb")}-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='2026E: 9M actual ($68m) + Q4 scenario input ($2.5bn authorization remaining at 30-Sep-2026). 2027E+ = max(minimum programme, leverage plug).')
    S('cf_eq', 'Employee stock plans, net (proceeds less taxes withheld)', 'line', 'm', data='cf_eq', flow=True, e26=lambda: f'={ACT("cf_eq")}+{V0["eq_q4"]}', ae_in=V0['eq_ae'])
    S('cf_ofin', 'Other financing activities, net (derived)', 'line', 'm', data='cf_ofin', flow=True, e26=lambda: f'={ACT("cf_ofin")}', ae_in=0.0)
    S('cf_cff', 'Net cash provided by (used in) financing activities', 'line_b', 'm', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_debt")}:{V("cf_ofin")})')
    S('cf_fx', 'Other (restricted cash reclassification; none in the forecast)', 'line', 'm', data='cf_fx', flow=True, fc=lambda: '=0')
    S('cf_net', 'Net change in cash and cash equivalents', 'line', 'm', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")}),"")', fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}')
    S('cf_beg', 'Cash — beginning of period', 'line', 'm', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period (cash flow basis; 2018–19 incl. restricted cash)', 'line_b', 'm', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: beginning cash + change = ending cash (should be 0; ±0.5 rounding)', 'check', 'm', all=lambda: chk(f'{V("cf_beg")}+{V("cf_net")}', V('cf_end'), cond=f'AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")}))'))
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0; ±0.5 rounding)', 'check', 'm',
      all=lambda: chk(f'SUM({V("cf_ni")}:{V("cf_wc")})-N({V("cf_pens_q")})-N({V("cf_contrib")})', V('cf_cfo'), cond=f'ISNUMBER({V("cf_ni")})'))
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (company definition: operating cash flow − capital expenditures)', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")},"")')
    S('fcf_pub', '  Company-published free cash flow', 'memo', 'm', data='fcf_pub', flow=True)
    S('fcf_chk', '  Check: model vs company-published free cash flow (should be 0; 2009–15 published figures are continuing operations)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("fcf_pub")}),{CTX.col.year}>=2016),IF(ABS({V("fcf")}-{V("fcf_pub")})<=0.6,0,ROUND({V("fcf")}-{V("fcf_pub")},1)),"n/p")')
    S('afcf', 'Adjusted free cash flow (company definition: FCF + proceeds from sale of equipment to a customer + after-tax discretionary pension contributions)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("fcf")}),{V("fcf")}+N({V("afcf_items")}),"")', note='2026 guidance $3.1–3.5bn on this definition (Q3 2026 release). Forecast items nil.')
    S('afcf_items', '  Adjusting items (derived: published adjusted FCF − FCF; forecast 0)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("afcf_pub")}),ISNUMBER({V("fcf")})),{V("afcf_pub")}-{V("fcf")},0)', fc=lambda: '=0')
    S('afcf_pub', '  Company-published adjusted free cash flow (incl. "before discretionary pension contributions" 2010–20)', 'memo', 'm', data='adj_fcf_pub', flow=True)
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of sales', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net earnings conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")', ae_in=V0['capex_pct'],
      note='2027E+ input: 2023–25 3.5–4.5% (capacity for solid rocket motors, B-21, Sentinel, microelectronics); normalising toward ~3%.')
    S('capex_dep', '  Capex / D&A (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("d_dda")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E = Q4 from shares outstanding at 30-Sep-2026; 2027E+ buybacks = max(minimum programme, leverage plug)')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = Q4)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans, net (m)', 'driver', 'm2', e26_in=V0['iss_q4'], ae_in=V0['iss_ae'])
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}', note='2026E begins from shares outstanding at 30-Sep-2026 (142.06m; 10-Q cover / XBRL).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since Q4/26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET (condensed, as in the releases)', 'section', note='BS FORECAST — 2026E rolled forward from the 30-Sep-2026 balance sheet + Q4 flows; 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}')
    S('bs_ar', '  Accounts receivable, net', 'line', 'm', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_unb', '  Unbilled receivables, net (contract assets; separate line from 2018)', 'line', 'm', data='bs_unb', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dunb")}/365')
    S('bs_inv', '  Inventoried costs, net', 'line', 'm', data='bs_inv', bs=True, fc=lambda: f'={V("wc_cos")}*{V("wc_dio")}/365')
    S('bs_oca', '  Prepaid expenses, deferred taxes (to 2015), held-for-sale and other current assets (derived)', 'line', 'm', data='bs_oca', bs=True, e26=lambda: f'={B1("bs_oca")}', ae=lambda: f'={P("bs_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_ppe', '  Property, plant & equipment, net', 'line', 'm', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-({V("cf_capex")}-{ACT("cf_capex")})-{QEc("d_dep")}', ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("d_dep")}+{V("m_spend")}*{V("m_ppe")}',
      note='Roll-forward: prior − capex (negative cash flow) − depreciation + acquired PP&E.')
    S('bs_rou', '  Operating lease right-of-use assets (2019+)', 'line', 'm', data='bs_rou', bs=True, e26=lambda: f'={B1("bs_rou")}', ae=lambda: f'={P("bs_rou")}')
    S('bs_gw', '  Goodwill', 'line', 'm', data='bs_gw', bs=True, e26=lambda: f'={B1("bs_gw")}', ae=lambda: f'={P("bs_gw")}+{V("m_spend")}*(1-{V("m_ppe")}-{V("m_intp")})')
    S('bs_int', '  Intangible assets, net (separate line 2010–12 and 2018–23; otherwise inside other non-current assets)', 'line', 'm', data='bs_int', bs=True,
      e26=lambda: f'={B1("bs_int")}', ae=lambda: f'={P("bs_int")}+{V("m_spend")}*{V("m_intp")}-N({V("m_amort")})',
      note='Purchased intangibles ($208m at 31-Dec-2025) are inside other non-current assets in the 2024+ releases; their amortization runs through that line in the forecast. Future-acquisition intangibles roll here.')
    S('bs_pens_a', '  Pension and other postretirement benefit plan assets (separate line 2009–12 and 2023+)', 'line', 'm', data='bs_pens_a', bs=True,
      e26=lambda: f'={B1("bs_pens_a")}-({V("cf_pens")}-{ACT("cf_pens")})', ae=lambda: f'={P("bs_pens_a")}-{V("cf_pens")}',
      note='Accretes by the non-cash FAS pension income and contributions reversed in the cash flow (prepaid pension asset).')
    S('bs_onca', '  Deferred tax assets & other non-current assets (incl. purchased intangibles where not separate; derived)', 'line', 'm', data='bs_onca', bs=True,
      e26=lambda: f'={B1("bs_onca")}-{QEc("d_amort")}', ae=lambda: f'={P("bs_onca")}-{V("d_amort")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_ppe")}:{V("bs_onca")}),"")')
    S('bs_l', "LIABILITIES AND SHAREHOLDERS' EQUITY", 'sub', 'gen')
    S('bs_ap', '  Trade accounts payable', 'line', 'm', data='bs_ap', bs=True, fc=lambda: f'={V("wc_cos")}*{V("wc_dpo")}/365')
    S('bs_accr', '  Accrued employee compensation', 'line', 'm', data='bs_accr', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_accr")}')
    S('bs_adv', '  Advance payments and billings in excess of costs incurred', 'line', 'm', data='bs_adv', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_adv")}')
    S('bs_std', '  Notes payable and current portion of long-term debt (inside other current liabilities from 2013; XBRL)', 'line', 'm', data='bs_std', bs=True, fc=lambda: f'={V("ds_rev")}+MIN({V("ds_notes")},{V("ds_mat")})',
      note='Forecast = commercial paper / revolver + notes maturing in the following year.')
    S('bs_ocl', '  Other current liabilities (derived)', 'line', 'm', data='bs_ocl', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_oclp")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_ap")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term debt, net of current portion', 'line', 'm', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_std")}')
    S('bs_pens_l', '  Pension and other postretirement benefit plan liabilities', 'line', 'm', data='bs_pens_l', bs=True, e26=lambda: f'={B1("bs_pens_l")}', ae=lambda: f'={P("bs_pens_l")}')
    S('bs_lease', '  Operating lease liabilities, non-current (2019+)', 'line', 'm', data='bs_lease', bs=True, e26=lambda: f'={B1("bs_lease")}', ae=lambda: f'={P("bs_lease")}')
    S('bs_oncl', '  Deferred tax and other non-current liabilities (derived)', 'line', 'm', data='bs_oncl', bs=True,
      e26=lambda: f'={B1("bs_oncl")}+({V("cf_def")}-{ACT("cf_def")})', ae=lambda: f'={P("bs_oncl")}+{V("cf_def")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_oncl")}),"")')
    S('bs_eq', "  Total shareholders' equity", 'line', 'm', data='bs_eq', bs=True,
      e26=lambda: f'={B1("bs_eq")}+{QEc("is_ni")}+({V("cf_div")}-{ACT("cf_div")})+({V("cf_bb")}-{ACT("cf_bb")})+{QEc("d_sbc")}+({V("cf_eq")}-{ACT("cf_eq")})',
      ae=lambda: f'={P("bs_eq")}+{V("is_ni")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_sbc")}+{V("cf_eq")}',
      note='+ net earnings − dividends − repurchases + stock-based compensation + employee stock plans (OCI held flat). Repurchased shares are retired.')
    S('bs_tle', "TOTAL LIABILITIES AND SHAREHOLDERS' EQUITY", 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_eq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm', all=lambda: chk(V('bs_ta'), V('bs_tle'), cond=f'ISNUMBER({V("bs_ta")})'))
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0; ±0.5 rounding)', 'check', 'm', hist=lambda: chk(V('bs_ta'), V('bs_ta_pub')))
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs_ta', bs=True)
    S('bs_restr', '  Memo: restricted cash in the cash-flow statement (2018–19; derived = CF ending cash − BS cash)', 'memo', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("cf_end")}),ISNUMBER({V("bs_cash")}),OR({CTX.col.year}=2018,{CTX.col.year}=2019)),{V("cf_end")}-{V("bs_cash")},0)', fc=lambda: '=0')
    S('bs_chk_cash', '  Check: BS cash (+ restricted cash 2018–19) vs cash-flow ending cash (should be 0; ±0.5 rounding)', 'check', 'm',
      all=lambda: chk(f'{V("bs_cash")}+N({V("bs_restr")})', V('cf_end'), cond=f'AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")}))'))
    S('bs_shares', '  Memo: shares outstanding at period end (m; XBRL)', 'memo', 'm1', data='bs_shares', bs=True, e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input); year-end ratios compared with year ends')
    S('wc_rev', '  Sales — annualised (quarters × 4)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_cos', '  Cost of sales — annualised', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_cos")}),{V("is_cos")}*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — accounts receivable / sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_dunb', '  Unbilled receivable days — unbilled / sales × 365 (2026E solved to the FCF guidance; 2027E+ held)', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_unb")}/{V("wc_rev")}*365,"")',
      e26=lambda: f'={V("cal_unb")}/{V("wc_rev")}*365', ae=lambda: f'={P("wc_dunb")}',
      note='2026E: days implied by the unbilled balance solved to the 2026 adjusted-FCF guidance (Group block). 2027E+: held at the 2026E level (assumption; 2025 year end 57 days, 2024 57 days).')
    S('wc_dio', '  Inventoried-cost days — inventoried costs / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_inv")}/{V("wc_cos")}*365,"")', e26_in=V0['wc']['dio'], ae_in=V0['wc']['dio'])
    S('wc_dpo', '  Payable days — trade payables / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_cos")}*365,"")', e26_in=V0['wc']['dpo'], ae_in=V0['wc']['dpo'])
    S('wc_accr', '  Accrued employee compensation % of sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_accr")}/{V("wc_rev")},"")', e26_in=V0['wc']['accr'], ae_in=V0['wc']['accr'])
    S('wc_adv', '  Advance payments & billings in excess of costs % of sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_adv")}/{V("wc_rev")},"")', e26_in=V0['wc']['adv'], ae_in=V0['wc']['adv'])
    S('wc_oclp', '  Other current liabilities % of sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")', e26_in=V0['wc']['ocl'], ae_in=V0['wc']['ocl'], note=V0['wc']['note'])
    S('wc_nwc', '  Trade working capital (receivables + unbilled + inventoried costs − payables − advances; company definition from Q4 2025)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_unb")}+{V("bs_inv")}-{V("bs_ap")}-{V("bs_adv")},"")')
    S('wc_nwc_p', '  Trade working capital % of sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  Δ trade working capital (y/y)', 'line', 'm', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions (no pending acquisitions: no PPA block; the M&A lever is unallocated)')
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; RSUs / PSUs)', 'sched', 'm1', ae_in=V0['dil'], note='Q3 2026: 142.4m diluted vs 142.1m basic (0.3m).')
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.08)
    S('ds_h', 'Debt schedule (senior notes repaid at maturity and refinanced; commercial paper / revolver drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (current portion + long-term debt)', 'sched', 'm', hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_rev")}',
      note=MAN['debt']['at_2026_09_30'])
    S('ds_notes', '  Senior notes and debentures (face, incl. current portion)', 'sched', 'm', e26=lambda: f'={B1("ds_total")}-{B1("ds_rev")}-{V("ds_repay")}+{V("ds_iss")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_iss', '  New notes issued (input)', 'sched', 'm', e26_in=0.0, ae=lambda: f'={V("ds_repay")}*{V("ds_refi")}', note='2027E+: scheduled maturities refinanced at the refinancing % (assumption).')
    S('ds_refi', '  % of maturities refinanced (input)', 'sched', 'pct', ae_in=V0['refi'])
    S('ds_repay', '  Notes repaid at maturity (input; FY2025 10-K maturity table)', 'sched', 'm', e26_in=V0['repay'][2026], ae_in={y: V0['repay'][y] for y in range(2027, 2032)}, note=V0['repay_note'])
    S('ds_mat', '  Maturities in the following year (current portion)', 'sched', 'm', e26_in=V0['mat'][2026], ae_in={y: V0['mat'][y] for y in range(2027, 2032)})
    S('ds_pre', '  Cash before commercial paper / revolver (opening cash + CFO + CFI + buybacks, dividends, equity, other financing − notes repaid + issued)', 'sched', 'm',
      e26=lambda: (f'={B1("bs_cash")}+({V("cf_cfo")}-{ACT("cf_cfo")})+({V("cf_cfi")}-{ACT("cf_cfi")})+({V("cf_bb")}-{ACT("cf_bb")})+({V("cf_div")}-{ACT("cf_div")})'
                   f'+({V("cf_eq")}-{ACT("cf_eq")})+({V("cf_ofin")}-{ACT("cf_ofin")})-{V("ds_repay")}+{V("ds_iss")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_bb")}+{V("cf_div")}+{V("cf_eq")}+{V("cf_ofin")}+{V("cf_fx")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_min', '  Minimum cash balance (input)', 'sched', 'm', e26_in=V0['min_cash'], ae_in=V0['min_cash'], note='Year-end cash 2021–25 $2.6–4.4bn; $2.0bn minimum (assumption).')
    S('ds_rev', '  Commercial paper / revolver outstanding (year end)', 'sched', 'm', hist=lambda: '=0',
      e26=lambda: f'=MAX(0,{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_rev")}+{V("ds_min")}-{V("ds_pre")})',
      note='$3.0bn revolving credit facility (matures Sep-2030) backing the commercial paper programme; none outstanding at 30-Sep-2026. Shortfalls below the minimum cash balance are drawn; surplus repays.')
    S('ds_head', '  Memo: headroom vs the $3.0bn facility (negative = would need other financing)', 'memo_calc', 'm', e26=lambda: f'=3000-{V("ds_rev")}', ae=lambda: f'=3000-{V("ds_rev")}')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm', e26=lambda: f'={V("ds_total")}-{B1("ds_total")}', ae=lambda: f'={V("ds_total")}-{P("ds_total")}')
    S('ds_r_notes', '  Interest rate on opening notes %', 'sched', 'pct', ae_in=V0['r_notes'], note=V0['r_notes_note'])
    S('ds_r_rev', '  Interest rate on opening commercial paper / revolver %', 'sched', 'pct', ae_in=0.045, note='SOFR-based commercial paper (assumption ~4.5%).')
    S('ds_fees', '  Debt-cost amortization, fees and other ($m)', 'sched', 'm', ae_in=20.0)
    S('ds_r_cash', '  Interest income yield on opening cash %', 'sched', 'pct', ae_in=0.035, note='Interest income is inside "Other, net"; ~3.5% on cash balances (assumption).')
    S('lev_h', 'Buybacks (2027E+): repurchases = max(minimum programme, plug to a target net debt / adjusted EBITDA)', 'sub', 'gen')
    S('lev_min', '  Target net debt / adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end)', 'sched', 'm', ae=lambda: f'={P("ds_total")}-{P("cf_end")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_eq")}-{V("cf_ofin")}-{V("cf_fx")}')
    S('lev_tgt', '  Target net debt = target leverage × adjusted EBITDA', 'sched', 'm', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_minbb', '  Minimum buyback programme (scenario, USDm)', 'sched', 'm', ae=lambda: '=' + CH(SC['BBMIN'][CTX.col.year]), note='2021–25 repurchases $1.2–3.7bn p.a.; $2.5bn remaining on the authorization at 30-Sep-2026.')
    S('lev_bb', '  Share repurchases = max(minimum programme, target-leverage plug)', 'sched', 'm', ae=lambda: f'=MAX({V("lev_minbb")},{V("lev_tgt")}-{V("lev_pre")},0)',
      note='Feeds the cash-flow repurchase line. Cash below the minimum balance is funded by commercial paper (debt schedule).')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_int', '  Interest expense ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")' if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    S('hr_cas', '  CAS pension cost % of sales (annual)', 'pct', 'pct', all=ratio('rc_cas', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted EBIT, full-cost)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT (model; after D&A)', 'line', 'm', ann=True, all=lambda: f'={V("r_aebit")}')
    S('ra_t', 'Effective tax rate', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(MIN(0.4,MAX(0.1,{V("is_etr")}+0)),0.17)')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', "  Total shareholders' equity", 'line', 'm', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − Cash', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Sales', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Sales / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-({V("bs_gw")}+N({V("bs_int")})),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. debt)', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})),"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net earnings', 'line', 'm', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Shareholders' equity", 'line', 'm', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net earnings / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash', 'line', 'm', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA (model)', 'line', 'm', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_gx', 'Total debt / adjusted EBITDA (x)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("ds_total")}/{V("lv_eb")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interests (USDm; none)', 'line', 'm', e26=lambda: '=0', ae=lambda: '=0')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Sales', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA (model)', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Segment operating income', lambda: f'=IFERROR({V("v_ev")}/{V("g_soi")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (MTM-adjusted EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
