"""Row specification part 2: cash flow, share schedule, balance sheet (incl. the 1-Jul-2026 Mobility spin-off), working capital,
schedules, ratios, valuation. Forecast columns are FY2026E (30-Jun-2026 balance sheet + 2H flows) and 2027E-2031E."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, H2, B1, EA

def build_spec2(V0):
    S = add
    MB, GS = V0['mob'], V0['geo']
    def e26f(key, h2):              # FY2026E flow = 1H actual (as reported, incl. Mobility) + 2H estimate
        return lambda: f'={ACT(key)}+{h2()}'
    def mob(k): return MB.get(k, 0.0)
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS (as reported — includes Mobility to 30-Jun-2026)', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 1H-26 actual + 2H estimate; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net income (incl. noncontrolling interests and discontinued operations)', 'line', 'm', data='cf_ni', flow=True,
      fc=lambda: f'={V("is_nic")}', e26=e26f('cf_ni', lambda: H2('is_nic')))
    S('cf_adj', 'Non-cash items:', 'sub', 'gen')
    S('cf_dep', '  Depreciation', 'line', 'm', data='cf_dep', flow=True, fc=lambda: f'={V("is_dep")}', e26=e26f('cf_dep', lambda: H2('is_dep')))
    S('cf_amort', '  Amortization of intangibles', 'line', 'm', data='cf_amort', flow=True, fc=lambda: f'={V("is_amort")}', e26=e26f('cf_amort', lambda: H2('is_amort')))
    S('cf_sbc', '  Stock-based compensation', 'line', 'm', data='cf_sbc', flow=True, fc=lambda: f'={V("d_sbc")}', e26=e26f('cf_sbc', lambda: H2('d_sbc')))
    S('cf_def', '  Deferred income taxes', 'line', 'm', data='cf_def', flow=True, e26=lambda: f'={ACT("cf_def")}+{V0["def_2h"]}', ae_in=V0['def_ae'],
      note='XBRL (10-K / 10-Q cash-flow statements). Forecast input (amortization-driven deferred-tax unwind).')
    S('cf_gain', '  (Gain) on dispositions (reclassified to investing proceeds; forecast)', 'line', 'm', e26=lambda: f'=-{H2("is_gain")}', ae=lambda: f'=-{V("is_gain")}')
    S('cf_wc', '  Working capital & other operating items, net (derived)', 'line', 'm', data='cf_wc', flow=True,
      e26=lambda: (f'={ACT("cf_wc")}-({V("bs_ar")}-({B1("bs_ar")}-{mob("ar")}))+({V("bs_ap")}-({B1("bs_ap")}-{mob("ap")}))+({V("bs_acc")}-({B1("bs_acc")}-{mob("accrued")}))'
                   f'+({V("bs_unr")}-({B1("bs_unr")}-{mob("unearned")}))+({V("bs_ocl")}-({B1("bs_ocl")}-{mob("ocl")}-{GS["liab"]}))+({V("bs_taxp")}-({B1("bs_taxp")}-{mob("tax_pay")}))'),
      ae=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})+({V("bs_ap")}-{P("bs_ap")})+({V("bs_acc")}-{P("bs_acc")})+({V("bs_unr")}-{P("bs_unr")})+({V("bs_ocl")}-{P("bs_ocl")})'
                  f'+({V("bs_taxp")}-{P("bs_taxp")})'),
      note=('History: cash from operations − net income − D&A − SBC − deferred taxes (incl. gains, other non-cash items). Forecast linked to the balance sheet: −Δ receivables + Δ(payables, '
            'accrued compensation, unearned revenue, taxes payable, other current liabilities); 2026E excludes the balances that left with Mobility and the geoscience portfolio.'))
    S('cf_cfo', 'Cash provided by operating activities', 'line_b', 'm', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Capital expenditures', 'line', 'm', data='cf_capex', flow=True,
      e26=lambda: f'={ACT("cf_capex")}-{PT("pt_capex2h")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='2026E: 1H actual + 2H point estimate (FY26 guidance $190–210m continuing operations). 2027E+: revenue × capex %.')
    S('cf_acq', 'Acquisitions, net of cash acquired', 'line', 'm', data='cf_acq', flow=True, e26=lambda: f'={ACT("cf_acq")}-{V0["acq_2h"]}', ae=lambda: f'=-{V("m_spend")}',
      note='2026E: 1H actual (Enertel AI) + 2H input (Agusto & Co., datacenterHawk: not material, price undisclosed — assumption). 2027E+: M&A lever.')
    S('cf_divest', 'Proceeds from dispositions, net', 'line', 'm', data='cf_divest', flow=True,
      e26=lambda: f'={ACT("cf_divest")}+{H2("is_gain")}+{GS["nav"]}', ae=lambda: f'={V("is_gain")}',
      note='2026E: 1H actual (EDM / thinkFolio) + geoscience portfolio sale to SLB (assumption: proceeds = net assets held for sale + modelled gain; terms not disclosed).')
    S('cf_oinv', 'Other investing activities, net (short-term investments; derived)', 'line', 'm', data='cf_oinv', flow=True, e26=lambda: f'={ACT("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Cash provided by (used for) investing activities', 'line_b', 'm', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_bb', 'Repurchase of treasury shares', 'line', 'm', data='cf_bb', flow=True, e26=lambda: f'={ACT("cf_bb")}-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='2026E: 1H actual ($1.5bn ASRs) + 2H scenario input (company expects >$7bn of 2026 repurchases). 2027E+ = leverage plug (surplus cash returned until net debt / adjusted EBITDA reaches the target).')
    S('cf_div', 'Dividends paid to shareholders', 'line', 'm', data='cf_div', flow=True,
      e26=lambda: f'={ACT("cf_div")}-{H2("dps")}*{B1("bs_shares")}', ae=lambda: f'=-{V("dps")}*{V("bb_beg")}')
    S('cf_ncid', 'Distributions to noncontrolling interest holders', 'line', 'm', data='cf_ncid', flow=True,
      e26=lambda: f'={ACT("cf_ncid")}-{H2("is_nci")}', ae=lambda: f'=-{V("is_nci")}', note='Forecast: NCI income distributed in full (CME Group share of S&P DJI).')
    S('cf_debt', 'Net debt issuance / (repayment) (forecast; included in other financing historically)', 'line', 'm',
      e26=lambda: f'={V("ds_total")}-({B1("ds_total")}-{MB["notes"]})', ae=lambda: f'={V("ds_net")}',
      note='Per the debt schedule: notes repaid / refinanced at maturity; commercial paper drawn or repaid to the minimum cash balance. 2026E excludes the $1,981m Mobility notes (left with Mobility Global).')
    S('cf_spin', 'Cash transferred with Mobility Global at the spin-off (1-Jul-2026)', 'line', 'm', e26=lambda: f'=-{mob("cash")}', ae_in=0.0,
      note='Mobility\'s own cash (31-Mar-2026 pro forma $121m; assumption until the Q3-26 10-Q). The $1,974m net distribution to S&P Global was already in cash at 30-Jun-2026 (Mobility note proceeds).')
    S('cf_ofin', 'Debt & other financing, net (derived historically: debt, share-plan withholding, excise tax, contingent consideration)', 'line', 'm', data='cf_ofin', flow=True,
      e26=lambda: f'={ACT("cf_ofin")}', ae_in=0.0)
    S('cf_cff', 'Cash provided by (used for) financing activities', 'line_b', 'm', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_bb")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of exchange rate changes on cash', 'line', 'm', data='cf_fx', flow=True, e26=lambda: f'={ACT("cf_fx")}', ae_in=0.0)
    S('cf_net', 'Net change in cash, cash equivalents and restricted cash', 'line', 'm', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")}),"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}')
    S('cf_beg', 'Cash — beginning of period', 'line', 'm', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period', 'line_b', 'm', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: beginning cash + CFO + CFI + CFF + FX = ending cash (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=1.01,0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},0)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),IF(ABS(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")})<=1.01,0,ROUND(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")},0)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (company definition: CFO − capex − distributions to noncontrolling interests)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")}+N({V("cf_ncid")}),"")')
    S('fcf_pub', '  Company-published free cash flow', 'memo', 'm', data='fcf_pub', flow=True)
    S('fcf_chk', '  Check: model vs company-published free cash flow (should be 0; ±2 rounding)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("fcf_pub")}),ISNUMBER({V("fcf")})),IF(ABS({V("fcf")}-{V("fcf_pub")})<=2.01,0,ROUND({V("fcf")}-{V("fcf_pub")},0)),"n/p")')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of revenue', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note='2027E+ input: FY2023–25 1.3–1.5% of revenue; FY26 guidance ~$200m (~1.4%).')
    S('capex_dep', '  Capex / depreciation (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("d_dep")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E = 2H from shares outstanding at 30-Jun-2026; 2027E+ buybacks via the leverage plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = 2H)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under employee plans (m)', 'driver', 'm2', e26_in=V0['iss_2h'], ae_in=V0['iss_ae'])
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from actual shares outstanding at 30-Jun-2026 (294.8m, Q2-26 release).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since 2H-26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET (condensed; as reported — includes Mobility to 30-Jun-2026)', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Jun-2026 balance sheet + 2H flows − Mobility net assets distributed (1-Jul-2026) − geoscience portfolio sold; 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash, cash equivalents and restricted cash', 'line', 'm', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}')
    S('bs_ar', '  Accounts receivable, net', 'line', 'm', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_oca', '  Prepaid & other current assets, assets held for sale', 'line', 'm', data='bs_oca', bs=True,
      e26=lambda: f'={B1("bs_oca")}-{mob("oca")}-{GS["assets"]}', ae=lambda: f'={P("bs_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_ppe', '  Property and equipment, net', 'line', 'm', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-{mob("ppe")}-({V("cf_capex")}-{ACT("cf_capex")})-{H2("d_dep")}', ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("d_dep")}',
      note='Roll-forward: prior − capex (negative cash flow) − depreciation (2026E also − Mobility PP&E).')
    S('bs_rou', '  Right of use assets', 'line', 'm', data='bs_rou', bs=True, e26=lambda: f'={B1("bs_rou")}-{mob("rou")}', ae=lambda: f'={P("bs_rou")}')
    S('bs_gw', '  Goodwill', 'line', 'm', data='bs_gw', bs=True, e26=lambda: f'={B1("bs_gw")}-{mob("gw")}-({V("cf_acq")}-{ACT("cf_acq")})', ae=lambda: f'={P("bs_gw")}+{V("m_spend")}*(1-{V("m_intp")})')
    S('bs_int', '  Other intangible assets, net', 'line', 'm', data='bs_int', bs=True,
      e26=lambda: f'={B1("bs_int")}-{mob("int")}-{H2("d_amort")}', ae=lambda: f'={P("bs_int")}-{V("d_amort")}+{V("m_spend")}*{V("m_intp")}',
      note='Roll-forward: prior − deal-related amortization + acquired intangibles (M&A lever); 2026E also − Mobility intangibles.')
    S('bs_eqi', '  Equity investments in unconsolidated subsidiaries', 'line', 'm', data='bs_eqi', bs=True, fc=lambda: f'={P("bs_eqi")}', e26=lambda: f'={B1("bs_eqi")}')
    S('bs_onca', '  Other non-current assets (derived)', 'line', 'm', data='bs_onca', bs=True, e26=lambda: f'={B1("bs_onca")}-{mob("onca")}', ae=lambda: f'={P("bs_onca")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_ppe")}:{V("bs_onca")}),"")')
    S('bs_l', 'LIABILITIES AND EQUITY', 'sub', 'gen')
    S('bs_ap', '  Accounts payable', 'line', 'm', data='bs_ap', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_app")}')
    S('bs_acc', '  Accrued compensation and contributions to retirement plans', 'line', 'm', data='bs_acc', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_accp")}')
    S('bs_std', '  Short-term debt (commercial paper + current maturities)', 'line', 'm', data='bs_std', bs=True, fc=lambda: f'={V("ds_rev")}+MIN({V("ds_notes")},{V("ds_mat")})')
    S('bs_taxp', '  Income taxes currently payable', 'line', 'm', data='bs_taxp', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_taxp")}')
    S('bs_unr', '  Unearned revenue', 'line', 'm', data='bs_unr', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_unr")}')
    S('bs_ocl', '  Other current liabilities, liabilities held for sale (derived)', 'line', 'm', data='bs_ocl', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_oclp")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_ap")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term debt', 'line', 'm', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_std")}')
    S('bs_lease', '  Lease liabilities — non-current', 'line', 'm', data='bs_lease', bs=True, e26=lambda: f'={B1("bs_lease")}-{mob("lease")}', ae=lambda: f'={P("bs_lease")}')
    S('bs_dtl', '  Deferred tax liability — non-current', 'line', 'm', data='bs_dtl', bs=True,
      e26=lambda: f'={B1("bs_dtl")}-{mob("dtl")}+({V("cf_def")}-{ACT("cf_def")})', ae=lambda: f'={P("bs_dtl")}+{V("cf_def")}')
    S('bs_onl', '  Pension, other postretirement benefits & other non-current liabilities (derived)', 'line', 'm', data='bs_onl', bs=True,
      e26=lambda: f'={B1("bs_onl")}-{mob("pension")}-{mob("onl")}', ae=lambda: f'={P("bs_onl")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_onl")}),"")')
    S('bs_rnci', '  Redeemable noncontrolling interests (CME Group 27% of S&P DJI; held flat)', 'line', 'm', data='bs_rnci', bs=True,
      e26=lambda: f'={B1("bs_rnci")}', ae=lambda: f'={P("bs_rnci")}')
    S('bs_eq', '  Total equity — controlling interests', 'line', 'm', data='bs_eq', bs=True,
      e26=lambda: (f'={B1("bs_eq")}+{H2("is_nicattr")}+({V("cf_div")}-{ACT("cf_div")})+({V("cf_bb")}-{ACT("cf_bb")})+{H2("d_sbc")}-{V("sp_eq")}'),
      ae=lambda: f'={P("bs_eq")}+{V("is_ni")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_sbc")}',
      note='+ net income attributable − dividends − repurchases + stock-based compensation (OCI, redemption-value changes of redeemable NCI and share-plan withholding held flat); 2026E − Mobility net assets distributed.')
    S('bs_nci', '  Total equity — noncontrolling interests', 'line', 'm', data='bs_nci', bs=True, e26=lambda: f'={B1("bs_nci")}', ae=lambda: f'={P("bs_nci")}')
    S('bs_teq', 'Total equity (incl. redeemable NCI)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")}+N({V("bs_nci")})+N({V("bs_rnci")}),"")')
    S('bs_tle', 'TOTAL LIABILITIES AND EQUITY', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=1.01,0,ROUND({V("bs_ta")}-{V("bs_tle")},0)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=1.01,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},0)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash vs cash-flow ending cash (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}-{V("cf_end")})<=1.01,0,ROUND({V("bs_cash")}-{V("cf_end")},0)),"")')
    S('bs_shares', '  Memo: shares outstanding at period end (m)', 'memo', 'm1', data='bs_shares', bs=True, e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()
    S('sp_h', 'Mobility spin-off (1-Jul-2026) — net assets distributed (31-Mar-2026 pro forma balances; replace with the Q3-26 10-Q)', 'sub', 'gen')
    S('sp_ta', '  Mobility assets (incl. cash $121m)', 'sched', 'm', e26_in=MB['ta'], note=MAN['mobility_spin']['source'])
    S('sp_tl', '  Mobility liabilities (excl. debt)', 'sched', 'm', e26_in=MB['tl'])
    S('sp_notes', '  Mobility senior notes transferred (carrying amount 30-Jun-2026)', 'sched', 'm', e26_in=MB['notes'])
    S('sp_eq', '  = Equity reduction (net assets distributed to shareholders)', 'sched', 'm', e26=lambda: f'={V("sp_ta")}-{V("sp_tl")}-{V("sp_notes")}', note=MAN['mobility_spin']['model'])
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input; fiscal-year-end balances, ex-Mobility, on pro forma FY2025 revenue)')
    S('wc_rev', '  Revenue — annualised (quarters × 4)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — receivables / revenue × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_unr', '  Unearned revenue % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_unr")}/{V("wc_rev")},"")', e26_in=V0['wc']['unr'], ae_in=V0['wc']['unr'])
    S('wc_app', '  Accounts payable % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_rev")},"")', e26_in=V0['wc']['ap'], ae_in=V0['wc']['ap'])
    S('wc_accp', '  Accrued compensation % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_acc")}/{V("wc_rev")},"")', e26_in=V0['wc']['acc'], ae_in=V0['wc']['acc'])
    S('wc_taxp', '  Income taxes payable % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_taxp")}/{V("wc_rev")},"")', e26_in=V0['wc']['taxp'], ae_in=V0['wc']['taxp'])
    S('wc_oclp', '  Other current liabilities % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")',
      e26_in=V0['wc']['ocl'], ae_in=V0['wc']['ocl'], note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables + other current assets − payables − accrued − taxes − unearned − other current liabilities)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_oca")}-{V("bs_ap")}-{V("bs_acc")}-{V("bs_taxp")}-{V("bs_unr")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppa_h', 'Acquisitions — consideration & purchase-price allocation (closing-period column)', 'sub', 'gen')
    for k, lab in [('cons', 'Consideration (fair value, incl. shares issued)'), ('ca', 'Current assets acquired (incl. cash)'), ('ppe', 'Property & equipment and other non-current assets'),
                   ('intang', 'Intangible assets'), ('gw', 'Goodwill'), ('cl', 'Current liabilities assumed (incl. unearned revenue)'), ('debt', 'Debt assumed'),
                   ('ncl', 'Non-current liabilities assumed (deferred taxes, other)'), ('nci', 'Noncontrolling interests')]:
        S(f'ppa_{k}', f'  {lab}', 'sched', 'm', data=f'ppa_{k}', ppa=True)
    S('ppa_chk', '  Check: assets acquired − liabilities assumed − NCI − consideration (should be 0)', 'check', 'm',
      hist=lambda: (f'=IF(ISNUMBER({V("ppa_cons")}),ROUND(N({V("ppa_ca")})+N({V("ppa_ppe")})+N({V("ppa_intang")})+N({V("ppa_gw")})'
                    f'-N({V("ppa_cl")})-N({V("ppa_debt")})-N({V("ppa_ncl")})-N({V("ppa_nci")})-{V("ppa_cons")},0),"")'))
    S('ppa_names', '  Deal closed in the period', 'text', 'gen', data='ppa_names', ppa=True, textdata=True)
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; options & RSUs)', 'sched', 'm1', ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.08)
    S('ds_h', 'Debt schedule (senior notes repaid at maturity and refinanced; commercial paper drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (short-term + long-term)', 'sched', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_rev")}', note=MAN['debt_2026_06_30']['facility'])
    S('ds_notes', '  Senior notes (carrying amount, incl. current maturities; ex-Mobility notes)', 'sched', 'm', data='debt_notes',
      e26=lambda: f'={B1("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}',
      note='30-Jun-2026: $15,170m total debt − $825m commercial paper − $1,981m Mobility notes = $12,364m of S&P Global notes (10-Q Note 4).')
    S('ds_iss', '  New notes issued (2026E input; 2027E+ = maturities refinanced + prior year-end CP above $500m termed out)', 'sched', 'm', e26_in=V0['iss_notes'][FYC],
      ae=lambda: f'={V("ds_repay")}+MAX(0,{P("ds_rev")}-500)',
      note='Assumption: maturities refinanced in full; commercial paper above $500m at the prior year end is termed out into new notes, so CP stays within the $2.0bn facility.')
    S('ds_repay', '  Notes repaid at maturity (input)', 'sched', 'm', e26_in=V0['repay'][FYC], ae_in={y: V0['repay'][y] for y in range(FYC + 1, FYL + 1)}, note=V0['repay_note'])
    S('ds_mat', '  Maturities in the following year (current portion)', 'sched', 'm', e26_in=V0['mat'][FYC], ae_in={y: V0['mat'][y] for y in range(FYC + 1, FYL + 1)})
    S('ds_pre', '  Cash before commercial-paper draws / repayments (opening cash + CFO + CFI + buybacks, dividends, NCI, spin, other financing + FX − notes repaid + issued)', 'sched', 'm',
      e26=lambda: (f'={B1("bs_cash")}+({V("cf_cfo")}-{ACT("cf_cfo")})+({V("cf_cfi")}-{ACT("cf_cfi")})+({V("cf_bb")}-{ACT("cf_bb")})+({V("cf_div")}-{ACT("cf_div")})'
                   f'+({V("cf_ncid")}-{ACT("cf_ncid")})+{V("cf_spin")}+({V("cf_ofin")}-{ACT("cf_ofin")})+({V("cf_fx")}-{ACT("cf_fx")})-{V("ds_repay")}+{V("ds_iss")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_bb")}+{V("cf_div")}+{V("cf_ncid")}+{V("cf_spin")}+{V("cf_ofin")}+{V("cf_fx")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_min', '  Minimum cash balance', 'sched', 'm', e26_in=V0['min_cash'], ae_in=V0['min_cash'])
    S('ds_rev', '  Commercial paper (year end)', 'sched', 'm', data='debt_cp',
      e26=lambda: f'=MAX(0,{B1("ds_rev")}+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_rev")}+{V("ds_min")}-{V("ds_pre")})',
      note='$2.0bn CP program backed by the $2.0bn credit facility (to Dec-2029); $825m outstanding at 30-Jun-2026. Shortfalls below the minimum cash balance are drawn; surplus repays CP.')
    S('ds_head', '  Memo: CP headroom vs the $2.0bn facility (negative = would need term debt)', 'memo_calc', 'm', e26=lambda: f'=2000-{V("ds_rev")}', ae=lambda: f'=2000-{V("ds_rev")}')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on opening notes %', 'sched', 'pct', ae_in=V0['r_notes'], note=V0['r_notes_note'])
    S('ds_r_rev', '  Interest rate on opening commercial paper %', 'sched', 'pct', ae_in=0.042, note='Assumption: US commercial paper ~4.0–4.5%.')
    S('ds_fees', '  Commitment fees & financing-cost amortization ($m)', 'sched', 'm', ae_in=10.0)
    S('ds_r_cash', '  Interest income yield on opening cash %', 'sched', 'pct', ae_in=0.03, note='Assumption: ~3% on cash balances (interest expense is reported net of interest income).')
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / adjusted EBITDA, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end)', 'sched', 'm',
      ae=lambda: f'={P("ds_total")}-{P("cf_end")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_ncid")}-{V("cf_spin")}-{V("cf_ofin")}-{V("cf_fx")}')
    S('lev_tgt', '  Target net debt = target leverage × adjusted EBITDA', 'sched', 'm', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to target leverage', 'sched', 'm', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash beyond the leverage target is returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  D&A % of revenue', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_amort', '  Deal-related amortization % of revenue', 'pct', 'pct', all=ratio('d_amort', 'is_rev'))
    S('hr_int', '  Interest expense, net ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted EBITA less cash adjusting costs; standard basis)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBITA less severance / acquisition / disposition / legal cash costs', 'line', 'm', ann=True,
      all=lambda: f'=IFERROR({V("r_ebit")}-N({V("r_cash")}),"n/a")')
    S('ra_t', 'Effective tax rate (adjusted)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("e_rate")}+0,0.225)')
    S('ra_nopat', 'NOPAT = Adjusted EBITA × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity (incl. redeemable NCI) + Net debt', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity incl. redeemable NCI', 'line', 'm', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),{V("bs_teq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − Cash', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBITA / Revenue', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Revenue / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBITA × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-({V("bs_gw")}+{V("bs_int")}),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. short-term debt)', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})),"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA (n/m where NTA < NOPAT: unearned revenue and goodwill leave almost no net tangible assets)', 'total', 'pct', ann=True,
      all=lambda: f'=IFERROR(IF({V("rn_nta")}>{V("rn_nopat")},{V("rn_nopat")}/{V("rn_nta")},"n/m"),"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income attributable', 'line', 'm', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', 'Equity — controlling interests', 'line', 'm', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash', 'line', 'm', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA (model)', 'line', 'm', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_gx', 'Total debt / adjusted EBITDA (x)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("ds_total")}/{V("r_adj")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+({Q2}{R["sh_dil"]}-{Q2}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Redeemable & other noncontrolling interests (USDm)', 'line', 'm', e26=lambda: f'={V("bs_rnci")}+{V("bs_nci")}', ae=lambda: f'={V("bs_rnci")}+{V("bs_nci")}')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Revenue', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted OP', lambda: f'=IFERROR({V("v_ev")}/{V("o_adj")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted, continuing)', lambda: f'=IFERROR({V("v_px")}/{V("eps_cont")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
