"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, QEc, QEa, B1, chk0

def build_spec2(V0):
    S = add
    yr = lambda: CTX.col.year
    first_ae = lambda: CTX.col.year == FYC + 1
    def e26f(key, q4):          # 2026E flow = nine months actual (carried in the Q3/26 column) + Q4/26E estimate
        return lambda: f'={ACT(key)}+{q4()}'
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note=('CASH FLOW — forecast logic (annual; 2026E = nine months actual + Q4 estimate). Legacy quarters are discrete, derived from year-to-date statements. '
            'Calendar basis: only nine-month statements are published (not recast for discontinued operations) — they sit in the Q3/25 and Q3/26 columns (cell comments).'))
    S('cf_ni', 'Net income', 'line', 'm', data='cf_ni', flow=True, ae=lambda: f'={V("is_ni")}', e26=e26f('cf_ni', lambda: QEc('is_ni')))
    S('cf_adj', 'Non-cash items:', 'sub', 'gen')
    S('cf_da', '  Depreciation and amortization', 'line', 'm', data='cf_da', flow=True, ae=lambda: f'={V("is_da")}', e26=e26f('cf_da', lambda: QEc('is_da')))
    S('cf_noncash', '  Other non-cash items, net (MTM adjustments, impairments, gains, deferred taxes, share-based compensation; derived)', 'line', 'm', data='cf_noncash', flow=True,
      e26=lambda: f'={ACT("cf_noncash")}+{QEc("d_sbc")}+{V("ds_def")}+{QEc("o_gain")}',
      ae=lambda: f'={V("d_sbc")}+{V("ds_def")}-{V("is_inv")}',
      note=('History: cash from operations − net income − D&A − changes in operating assets and liabilities. Forecast: share-based compensation + deferred taxes '
            '− non-cash gains (Q4/26E: the FedEx Supply Chain gain is reclassified to investing proceeds).'))
    S('cf_wc', '  Changes in operating assets and liabilities, net', 'line', 'm', data='cf_wc', flow=True,
      e26=lambda: (f'={ACT("cf_wc")}-({V("bs_ar")}-{B1("bs_ar")})+({V("bs_ap")}-{B1("bs_ap")})+({V("bs_accsal")}-{B1("bs_accsal")})'
                   f'+({V("bs_ocl")}-({B1("bs_ocl")}-{V("sc_cl")}))-{V("ds_pens")}'),
      ae=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})+({V("bs_ap")}-{P("bs_ap")})+({V("bs_accsal")}-{P("bs_accsal")})+({V("bs_ocl")}-{P("bs_ocl")})-{V("ds_pens")}'),
      note=('Forecast linked to the balance sheet: −Δ receivables + Δ(payables incl. customer tariff refunds, accrued salaries, accrued & other) − voluntary pension contributions '
            '(schedule). The $2.7bn of IEEPA tariff refunds held for customers at 30-Sep-2026 flows out through payables (assumption: by the end of 2027).'))
    S('cf_cfo', 'Cash provided by operating activities', 'line_b', 'm', data='cf_cfo', flow=True, fc=lambda: f'={V("cf_ni")}+{V("cf_da")}+{V("cf_noncash")}+{V("cf_wc")}')
    S('cf_capex', 'Capital expenditures', 'line', 'm', data='cf_capex', flow=True,
      e26=lambda: f'={ACT("cf_capex")}-({PT("pt_capex")}-{Q3}{R["cf_capex9"]})', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note=('2026E: nine months actual (incl. FedEx Freight to 31-May) + Q4 = guided ~$3.9bn (continuing operations) − nine-month continuing capex $2,859m. '
            '2027E+: revenue × capex %.'))
    S('cf_capex9', '  Memo: capital expenditures of continuing operations, nine months (release, with the income statement)', 'memo', 'm', data='capex_9m')
    S('cf_acq', 'Business acquisitions & equity-method investments (InPost consortium stake, Q2/26)', 'line', 'm', data='cf_acq', flow=True,
      e26=lambda: f'={ACT("cf_acq")}', ae_in=0.0)
    S('cf_oinv', 'Other investing activities, net (asset dispositions, investments; forecast: divestiture & FedEx Freight stake proceeds)', 'line', 'm', data='cf_oinv', flow=True,
      e26=lambda: f'={ACT("cf_oinv")}+{V("sc_proc")}', ae=lambda: f'={P("bs_sti")}-{V("bs_sti")}',
      note=('2026E: nine months actual + $1.4bn FedEx Supply Chain proceeds (1-Oct-2026). 2027E: sale of the retained FedEx Freight stake at its 30-Sep-2026 carrying value '
            '($3,254m; ASSUMPTION — the company expects to monetise it within 12 months, subject to market conditions).'))
    S('cf_cfi', 'Cash used in investing activities', 'line_b', 'm', data='cf_cfi', flow=True, fc=lambda: f'={V("cf_capex")}+{V("cf_acq")}+{V("cf_oinv")}')
    S('cf_debt', 'Debt issuances less repayments, net (incl. short-term borrowings)', 'line', 'm', data='cf_debt', flow=True,
      e26=lambda: f'={ACT("cf_debt")}+({V("ds_total")}-{B1("ds_total")})', ae=lambda: f'={V("ds_net")}',
      note='Forecast per the debt schedule: notes repaid at maturity and refinanced; commercial paper drawn or repaid to the minimum cash balance.')
    S('cf_div', 'Dividends paid', 'line', 'm', data='cf_div', flow=True,
      e26=lambda: f'={ACT("cf_div")}-{QEc("dps")}*{QEc("sh_basic")}', ae=lambda: f'=-{V("dps")}*{V("bb_beg")}')
    S('cf_bb', 'Purchases of common stock (treasury stock)', 'line', 'm', data='cf_bb', flow=True, e26=lambda: f'={ACT("cf_bb")}-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='2026E: nine months actual + Q4 scenario input ($4.3bn left on the 2026 program at 30-Sep-2026). 2027E+ = leverage plug (surplus cash returned until net debt / adjusted EBITDA reaches the target).')
    S('cf_iss', 'Proceeds from stock issuances (equity plans)', 'line', 'm', data='cf_iss', flow=True, e26=lambda: f'={ACT("cf_iss")}+{V0["iss_q4"]}', ae_in=V0['iss_ae'])
    S('cf_ofin', 'Other financing activities, net (derived; 2026: distribution attributable to the spin-off)', 'line', 'm', data='cf_ofin', flow=True,
      e26=lambda: f'={ACT("cf_ofin")}', ae_in=0.0)
    S('cf_cff', 'Cash provided by (used in) financing activities', 'line_b', 'm', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_debt")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of exchange rate changes on cash', 'line', 'm', data='cf_fx', flow=True, e26=lambda: f'={ACT("cf_fx")}', ae_in=0.0)
    S('cf_net', 'Net change in cash and cash equivalents', 'line', 'm', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")}),"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}')
    S('cf_beg', 'Cash — beginning of period (calendar nine months: incl. cash of discontinued operations)', 'line', 'm', data='cf_beg',
      e26=lambda: f'={Q3}{R["cf_beg"]}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period', 'line_b', 'm', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: CFO + CFI + CFF + FX = change in cash (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),{chk0(V("cf_beg") + "+" + V("cf_net"), V("cf_end"), 1.01)},"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),{chk0(V("cf_ni") + "+" + V("cf_da") + "+" + V("cf_noncash") + "+" + V("cf_wc"), V("cf_cfo"), 1.01)},"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (model: cash from operations − capital expenditures)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")},"")',
      note='Model definition (FedEx reports an "adjusted free cash flow" in presentations; no reconciliation table is filed with the releases).')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of revenue', 'pct', 'pct', all=lambda: f'=IF(AND(ISNUMBER({V("fcf")}),ISNUMBER({V("is_rev")})),IFERROR({V("fcf")}/{V("is_rev")},""),"")' if not (CTX.col.basis == 'C' and CTX.col.kind == 'Q') else None)
    S('fcf_conv', '  FCF / adjusted net income conversion %', 'pct', 'pct', all=lambda: f'=IF(AND(ISNUMBER({V("fcf")}),ISNUMBER({V("e_adjni")})),IFERROR({V("fcf")}/{V("e_adjni")},""),"")' if not (CTX.col.basis == 'C' and CTX.col.kind == 'Q') else None)
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=lambda: f'=IF(AND(ISNUMBER({V("fcf")}),ISNUMBER({V("sh_dil")})),IFERROR({V("fcf")}/{V("sh_dil")},""),"")' if not (CTX.col.basis == 'C' and CTX.col.kind == 'Q') else None)
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of revenue', 'pct', 'pct',
      all=lambda: (f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")' if not (CTX.col.basis == 'C' and CTX.col.kind == 'Q') else None),
      ae_in=V0['capex_pct'], note='2027E+ input: 2026 guidance ~$3.9bn (4.2% of revenue; fleet and facility modernisation, Network 2.0 automation); FY2022–26 5–7% incl. FedEx Freight.')
    S('capex_dep', '  Capex / depreciation & amortization (x)', 'line', 'x2',
      all=lambda: (f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("cf_da")},""),"")' if not (CTX.col.basis == 'C' and CTX.col.kind == 'Q') else None))
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E = Q4 from shares outstanding at 26-Oct-2026 (10-Q cover); 2027E+ buybacks via the leverage plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = Q4)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans (m)', 'driver', 'm2', e26_in=V0['ish_q4'], ae_in=V0['ish_ae'])
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from shares outstanding at 26-Oct-2026 (cover page of the Form 10-Q for the quarter ended 30-Sep-2026).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since Q4/26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET (condensed, as in the releases)', 'section',
      note=('BS FORECAST — 2026E rolled forward from the 30-Sep-2026 balance sheet + Q4 flows; 2027E+ from prior year end. Calendar-basis balance sheets are published '
            'only for 31-Dec-2024, 31-Dec-2025 and 30-Sep-2026.'))
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}')
    S('bs_ar', '  Receivables, less allowances', 'line', 'm', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_sti', '  Short-term investment (retained 19.9% FedEx Freight stake, at fair value)', 'line', 'm', data='bs_sti', bs=True,
      e26=lambda: f'={B1("bs_sti")}', ae_in=0.0, note='Held at the 30-Sep-2026 fair value to year-end 2026; assumed sold at that value in 2027E (assumption).')
    S('bs_oca', '  Spare parts, prepaid & other current assets (incl. assets of discontinued operations / held for sale; derived)', 'line', 'm', data='bs_oca', bs=True,
      e26=lambda: f'={B1("bs_oca")}-{V("sc_ca")}', ae=lambda: f'={P("bs_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{nsum(["bs_cash", "bs_ar", "bs_sti", "bs_oca"])},"")')
    S('bs_ppe', '  Net property and equipment', 'line', 'm', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}+({PT("pt_capex")}-{Q3}{R["cf_capex9"]})-{QEc("is_da")}',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("is_da")}',
      note='Roll-forward: prior + capex − depreciation & amortization.')
    S('bs_rou', '  Operating lease right-of-use assets, net (from FY2020, ASC 842)', 'line', 'm', data='bs_rou', bs=True, e26=lambda: f'={B1("bs_rou")}', ae=lambda: f'={P("bs_rou")}',
      note='Held flat with the operating lease liabilities (rent stays an operating cost; leases are not treated as debt).')
    S('bs_gw', '  Goodwill (shown with other assets from the 28-Oct-2026 presentation)', 'line', 'm', data='bs_gw', bs=True, fc=lambda: '=0')
    S('bs_eqm', '  Equity-method investment (37% of the InPost consortium vehicle, from Q2/26)', 'line', 'm', data='bs_eqm', bs=True, e26=lambda: f'={B1("bs_eqm")}', ae=lambda: f'={P("bs_eqm")}',
      note='Held at cost (no equity earnings recognised to 30-Sep-2026; none forecast — assumption).')
    S('bs_onca', '  Other assets (incl. goodwill from Q3/26, non-current assets of discontinued operations; derived)', 'line', 'm', data='bs_onca', bs=True,
      e26=lambda: f'={B1("bs_onca")}-{V("sc_nca")}', ae=lambda: f'={P("bs_onca")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+{nsum(["bs_ppe", "bs_rou", "bs_gw", "bs_eqm", "bs_onca"])},"")')
    S('bs_l', "LIABILITIES AND COMMON STOCKHOLDERS' INVESTMENT", 'sub', 'gen')
    S('bs_std', '  Current portion of long-term debt & short-term borrowings', 'line', 'm', data='bs_std', bs=True, fc=lambda: f'={V("ds_rev")}+MIN({V("ds_notes")},{V("ds_mat")})',
      note='30-Sep-2026: $2,051m from the Form 10-Q note on accrued and other liabilities (the release shows it inside "Accrued and other liabilities").')
    S('bs_ap', '  Accounts (and notes) payable (incl. IEEPA tariff refunds held for customers from 2026)', 'line', 'm', data='bs_ap', bs=True,
      fc=lambda: f'={V("wc_rev")}*{V("wc_app")}+{V("ds_tariff")}')
    S('bs_accsal', '  Accrued salaries and employee benefits', 'line', 'm', data='bs_accsal', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_salp")}')
    S('bs_ocl', '  Accrued expenses, current operating lease liabilities & other current liabilities (derived)', 'line', 'm', data='bs_ocl', bs=True,
      fc=lambda: f'={V("wc_rev")}*{V("wc_oclp")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ocl")}),{nsum(["bs_std", "bs_ap", "bs_accsal", "bs_ocl"])},"")')
    S('bs_ltd', '  Long-term debt, less current portion', 'line', 'm', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_std")}')
    S('bs_lease_nc', '  Operating lease liabilities (non-current)', 'line', 'm', data='bs_lease_nc', bs=True, e26=lambda: f'={B1("bs_lease_nc")}', ae=lambda: f'={P("bs_lease_nc")}')
    S('bs_dtl', '  Deferred income taxes', 'line', 'm', data='bs_dtl', bs=True, e26=lambda: f'={B1("bs_dtl")}+{V("ds_def")}', ae=lambda: f'={P("bs_dtl")}+{V("ds_def")}')
    S('bs_pens', '  Pension, postretirement healthcare & other benefit obligations (in other liabilities from Q3/26)', 'line', 'm', data='bs_pens', bs=True, fc=lambda: '=0')
    S('bs_selfins', '  Self-insurance accruals', 'line', 'm', data='bs_selfins', bs=True, e26=lambda: f'={B1("bs_selfins")}', ae=lambda: f'={P("bs_selfins")}')
    S('bs_oltl', '  Other long-term liabilities (incl. liabilities of discontinued operations; derived)', 'line', 'm', data='bs_oltl', bs=True,
      e26=lambda: f'={B1("bs_oltl")}-{V("sc_ncl")}-{V("ds_pens")}', ae=lambda: f'={P("bs_oltl")}-{V("ds_pens")}',
      note='Forecast: prior − liabilities sold with FedEx Supply Chain − voluntary pension contributions.')
    S('bs_tl', 'Total liabilities', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ocl")}),{V("bs_tcl")}+{nsum(["bs_ltd", "bs_lease_nc", "bs_dtl", "bs_pens", "bs_selfins", "bs_oltl"])},"")')
    S('bs_eq', "  Common stockholders' investment", 'line', 'm', data='bs_eq', bs=True,
      e26=lambda: (f'={B1("bs_eq")}+{QEc("is_ni")}-{QEc("dps")}*{QEc("sh_basic")}-{V("bb_cash")}+{QEc("d_sbc")}+{V0["iss_q4"]}'),
      ae=lambda: f'={P("bs_eq")}+{V("is_ni")}+{V("cf_div")}+{V("cf_bb")}+{V("d_sbc")}+{V("cf_iss")}',
      note='+ net income − dividends − repurchases + share-based compensation + stock issuances (other comprehensive income held flat).')
    S('bs_tle', "TOTAL LIABILITIES AND COMMON STOCKHOLDERS' INVESTMENT", 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_eq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),{chk0(V("bs_ta"), V("bs_tle"), 1.01)},"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),{chk0(V("bs_ta"), V("bs_ta_pub"), 1.01)},"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs_ta', bs=True)
    S('bs_rcash', '  Memo: restricted cash (in cash-flow ending cash, not in cash and cash equivalents; Q3 FY26)', 'memo', 'm', data='bs_rcash', bs=True)
    S('bs_chk_cash', '  Check: BS cash (+ restricted cash) vs cash-flow ending cash (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),{chk0(V("bs_cash") + "+N(" + V("bs_rcash") + ")", V("cf_end"), 1.01)},"")')
    S('bs_shares', '  Memo: shares outstanding (10-K / 10-Q cover page, shortly after the period end; m)', 'memo', 'm1', data='bs_shares', bs=True,
      e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input); FedEx has no cost of goods sold, so all ratios are on revenue')
    S('wc_rev', '  Revenue — annualised (quarters × 4)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — receivables / revenue × 365', 'line', 'd', hist=lambda: f'=IF(ISNUMBER({V("bs_ar")}),IFERROR({V("bs_ar")}/{V("wc_rev")}*365,""),"")', e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_app', '  Accounts payable % of revenue (excl. customer tariff refunds)', 'pct', 'pct',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ap")}),IFERROR({V("bs_ap")}/{V("wc_rev")},""),"")', e26_in=V0['wc']['ap'], ae_in=V0['wc']['ap'])
    S('wc_salp', '  Accrued salaries & employee benefits % of revenue', 'pct', 'pct',
      hist=lambda: f'=IF(ISNUMBER({V("bs_accsal")}),IFERROR({V("bs_accsal")}/{V("wc_rev")},""),"")', e26_in=V0['wc']['sal'], ae_in=V0['wc']['sal'])
    S('wc_oclp', '  Accrued & other current liabilities % of revenue', 'pct', 'pct',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ocl")}),IFERROR({V("bs_ocl")}/{V("wc_rev")},""),"")', e26_in=V0['wc']['ocl'], ae_in=V0['wc']['ocl'], note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables − payables − accrued salaries − accrued & other)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}-N({V("bs_ap")})-N({V("bs_accsal")})-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dcf', '  Change in operating assets & liabilities for the DCF (cash-flow line excl. the pass-through of customer tariff refunds)', 'line', 'm',
      e26=lambda: f'={V("cf_wc")}', ae=lambda: f'={V("cf_wc")}+({P("ds_tariff")}-{V("ds_tariff")})',
      note='The $2.7bn of tariff refunds held for customers is excluded from net debt, so its payout is excluded from unlevered free cash flow as well.')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('sc_h', 'FedEx Supply Chain — sold to CMA CGM Group on 1-Oct-2026 (Form 10-Q, Notes 1 and 14)', 'sub', 'gen')
    S('sc_proc', '  Cash proceeds ($m)', 'sched', 'm', e26_in=V0['sc']['proc'], note=MAN['supply_chain_sale']['note'] + ' Proceeds $1.4bn, net of ~$35m transaction costs expensed in Q3/26.')
    S('sc_ca', '  Current assets held for sale at 30-Sep-2026 (in prepaid expenses and other)', 'sched', 'm', e26_in=V0['sc']['ca'])
    S('sc_nca', '  Non-current assets held for sale (in goodwill and other assets)', 'sched', 'm', e26_in=V0['sc']['nca'])
    S('sc_cl', '  Current liabilities held for sale (in accrued and other liabilities)', 'sched', 'm', e26_in=V0['sc']['cl'])
    S('sc_ncl', '  Non-current liabilities held for sale (in other liabilities)', 'sched', 'm', e26_in=V0['sc']['ncl'])
    S('sc_nav', '  Net assets held for sale', 'sched', 'm', e26=lambda: f'={V("sc_ca")}+{V("sc_nca")}-{V("sc_cl")}-{V("sc_ncl")}')
    S('sc_tax', '  Income tax on the gain ($m; ASSUMPTION nil — a $263m deferred tax benefit on the tax-over-book basis was already recorded in Q3/26)', 'sched', 'm', e26_in=0.0)
    S('sc_chk', '  Check: proceeds − net assets − gain (should be 0)', 'check', 'm', e26=lambda: f'=ROUND({V("sc_proc")}-{V("sc_nav")}+{QEc("o_gain")},0)')
    S('rf_h', 'Share count, taxes, pensions & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; options & restricted stock units)', 'sched', 'm1', ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.08)
    S('ds_def', '  Deferred income taxes (cash-flow add-back; $m)', 'sched', 'm', e26_in=0.0, ae_in=V0['def_ae'],
      note='Input (assumption): bonus depreciation keeps cash taxes below book taxes; 2026E = Q4 only.')
    S('ds_pens', '  Voluntary pension contributions ($m; 2026E = Q4)', 'sched', 'm', e26_in=V0['pens_q4'], ae_in=V0['pens_ae'],
      note='Calendar-2026 guidance $475m of contributions (28-Oct-2026); Q4 portion and 2027E+ amounts are assumptions. Reduce other long-term liabilities.')
    S('ds_tariff', '  IEEPA tariff refunds held for customers (in accounts payable; $m)', 'sched', 'm', e26_in=V0['tariff'][FYC], ae_in={y: V0['tariff'].get(y, 0.0) for y in range(FYC + 1, FYL + 1)},
      note=MAN['tariff_refunds']['note'] + ' ASSUMPTION: still held at year-end 2026, fully refunded during 2027. Deducted from cash in net debt.')
    S('ds_h', 'Debt schedule (notes repaid at maturity and refinanced; commercial paper drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (current portion + long-term debt, incl. finance leases)', 'sched', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_rev")}', note=MAN['debt']['at_2026_09_30'])
    S('ds_notes', '  Senior notes & finance leases (long-term debt incl. current portion)', 'sched', 'm',
      e26=lambda: f'={B1("ds_total")}-{V("ds_repay")}+{V("ds_iss")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_iss', '  New notes issued (input)', 'sched', 'm', e26_in=0.0, ae_in={y: V0['iss_notes'].get(y, 0.0) for y in range(FYC + 1, FYL + 1)},
      note='2027E+: maturities assumed refinanced with new notes (assumption). The $1.1bn / €1.1bn / €0.9bn notes of 14-Sep-2026 are already in the 30-Sep-2026 balance.')
    S('ds_repay', '  Notes repaid at maturity (input)', 'sched', 'm', e26_in=0.0, ae_in={y: V0['repay'][y] for y in range(FYC + 1, FYL + 1)}, note=V0['repay_note'])
    S('ds_mat', '  Maturities in the following year (current portion)', 'sched', 'm', e26_in=V0['mat'][FYC], ae_in={y: V0['mat'][y] for y in range(FYC + 1, FYL + 1)})
    S('ds_pre', '  Cash before commercial paper (opening cash + CFO + CFI + buybacks, dividends, issuances, other financing + FX − notes repaid + issued)', 'sched', 'm',
      e26=lambda: (f'={B1("bs_cash")}+({V("cf_cfo")}-{ACT("cf_cfo")})+({V("cf_cfi")}-{ACT("cf_cfi")})+({V("cf_bb")}-{ACT("cf_bb")})+({V("cf_div")}-{ACT("cf_div")})'
                   f'+({V("cf_iss")}-{ACT("cf_iss")})+({V("cf_ofin")}-{ACT("cf_ofin")})+({V("cf_fx")}-{ACT("cf_fx")})-{V("ds_repay")}+{V("ds_iss")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_bb")}+{V("cf_div")}+{V("cf_iss")}+{V("cf_ofin")}+{V("cf_fx")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_min', '  Minimum cash balance (excl. customer tariff refunds held)', 'sched', 'm', e26_in=V0['min_cash'], ae_in=V0['min_cash'])
    S('ds_rev', '  Commercial paper / credit agreements drawn (year end)', 'sched', 'm',
      e26=lambda: f'=MAX(0,{V("ds_min")}+{V("ds_tariff")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_rev")}+{V("ds_min")}+{V("ds_tariff")}-{V("ds_pre")})',
      note='$3.5bn of credit agreements ($1.75bn to Mar-2028, $1.75bn to Mar-2030) back the commercial paper program; nothing drawn at 30-Sep-2026. Shortfalls below the minimum cash balance are drawn; surplus repays.')
    S('ds_head', '  Memo: headroom vs the $3.5bn credit agreements (negative = would need other financing)', 'memo_calc', 'm',
      e26=lambda: f'=3500-{V("ds_rev")}', ae=lambda: f'=3500-{V("ds_rev")}')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm', e26=lambda: f'={V("ds_total")}-{B1("ds_total")}', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on opening notes & finance leases %', 'sched', 'pct', ae_in=V0['r_notes'], note=V0['r_notes_note'])
    S('ds_r_rev', '  Interest rate on opening commercial paper %', 'sched', 'pct', ae_in=0.045, note='Assumption (short-term rates; no commercial paper outstanding at 30-Sep-2026).')
    S('ds_r_cash', '  Interest income yield on opening cash %', 'sched', 'pct', ae_in=V0['r_cash'], note='Assumption: Q3/26 net interest expense of $66m against ~$180m of gross interest implies ~$115m of quarterly interest income on $8–13bn of cash.')
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / adjusted EBITDA, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end; debt − cash − short-term investment + tariff refunds held)', 'sched', 'm',
      ae=lambda: (f'={P("ds_total")}-{P("cf_end")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_iss")}-{V("cf_ofin")}-{V("cf_fx")}-{V("bs_sti")}+{V("ds_tariff")}'))
    S('lev_tgt', '  Target net debt = target leverage × adjusted EBITDA', 'sched', 'm', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to target leverage', 'sched', 'm', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash beyond the leverage target is returned via buybacks; feeds the cash-flow repurchase line. Amounts above the $4.3bn left on the 2026 program assume new authorizations.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_da', '  D&A % of revenue', 'pct', 'pct', all=ratio('is_da', 'is_rev'))
    S('hr_int', '  Net interest expense ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR(-{V("is_int")}/AVERAGE({V("ds_total")},{CTX.col.prior}{R["ds_total"]}),"")' if (CTX.col.prior and not CTX.col.q) else None))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted operating income; invested capital excludes operating leases and the InPost stake)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    A_ = dict(ann=True)
    S('ra_ebit', 'Adjusted EBIT (adjusted operating income)', 'line', 'm', all=lambda: f'={V("r_ebit")}', **A_)
    S('ra_t', 'Effective tax rate (adjusted)', 'line', 'pct', all=lambda: f'=IFERROR(MAX(0.15,MIN(0.4,{V("e_rate")}+0)),0.235)', **A_)
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")', **A_)
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt − equity-method investment', 'line', 'm', all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")}-N({V("bs_eqm")}),"n/a")', **A_)
    S('ra_eq', "  Common stockholders' investment", 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")},"n/a")', **A_)
    S('ra_nd', '  Net debt = Total debt − cash − short-term investment + customer tariff refunds held', 'line', 'm',
      all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")}-N({V("bs_sti")})+N({V("ds_tariff")}),"n/a")', **A_)
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")', **A_)
    S('ra_mg', '  Margin = Adjusted EBIT / Revenue', 'line', 'pct', all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")', **A_)
    S('ra_to', '  Capital turnover = Revenue / IC', 'line', 'x2', all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")', **A_)
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")', **A_)
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")', **A_)
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', all=lambda: f'={V("ra_nopat")}', **A_)
    S('rn_ta', '  Total assets', 'line', 'm', all=lambda: f'={V("bs_ta")}', **A_)
    S('rn_gw', '  − Goodwill, cash, short-term & equity-method investments', 'line', 'm',
      all=lambda: f'=IFERROR(-(N({V("bs_gw")})+{V("bs_cash")}+N({V("bs_sti")})+N({V("bs_eqm")})),"n/a")', **A_)
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. current debt)', 'line', 'm', all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})),"n/a")', **A_)
    S('rn_nta', '  = Net tangible operating assets', 'line', 'm', all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")', **A_)
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")', **A_)
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income', 'line', 'm', all=lambda: f'={V("is_ni")}', **A_)
    S('roe_eq', "Common stockholders' investment", 'line', 'm', all=lambda: f'={V("bs_eq")}', **A_)
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")', **A_)
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt (total debt − cash − short-term investment + customer tariff refunds held)', 'line', 'm', all=lambda: f'={V("ra_nd")}', **A_)
    S('lv_eb', 'Adjusted EBITDA (model)', 'line', 'm', all=lambda: f'={V("r_adj")}', **A_)
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")', **A_)
    S('lv_gx', 'Total debt / adjusted EBITDA (x) (company covenant measure: 1.9x at 30-Sep-2026 on the credit-agreement definition; limit 3.5x)', 'line', 'x2',
      all=lambda: f'=IFERROR({V("ds_total")}/{V("r_adj")},"n/a")', **A_)
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Less: equity-method investment at carrying value (InPost; no noncontrolling interests) (USDm)', 'line', 'm', e26=lambda: f'=-N({V("bs_eqm")})', ae=lambda: f'=-N({V("bs_eqm")})')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Revenue', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted operating income', lambda: f'=IFERROR({V("v_ev")}/{V("o_adj")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
