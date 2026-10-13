"""Row specification part 2: FCF bridge, cash flow, share schedule, balance sheet, working capital, schedules (CPP PPA, debt,
leverage-targeted buybacks), ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, H2, B1, E

def build_spec2(V0):
    S = add
    MAN_ = MAN
    def e26f(key, h2):          # FY2026E flow = H1-26 actual + 2H-26E estimate
        return lambda: f'={ACT(key)}+{h2()}'
    def bs26(key):              # FY2026E balance = 30-Jun-2026 balance + 2H flows
        return B1(key)
    # ------------------------------------------------------------------ RECON 4: free cash flow
    S('sec_r4', 'RECONCILIATION: CASH FROM OPERATING ACTIVITIES → FREE CASH FLOW (company definition, as published)', 'section',
      note='FCF — CFOA (continuing) − gross additions to PP&E and internal-use software (+ dispositions of PP&E from the Q3-25 definition) + separation and Corporate restructuring cash')
    S('f_cfo', 'Cash from operating activities — continuing operations (GAAP)', 'line_b', 'm', all=lambda: f'={V("cf_cfo")}')
    S('f_capex', '  (+) Gross additions to PP&E and internal-use software', 'line', 'm', all=lambda: f'={V("cf_capex")}')
    S('f_disp', '  (+) Dispositions of PP&E (in the definition from the Q3-25 release)', 'line', 'm', data='fcf_ppe_disp', flow=True, e26=lambda: f'={V("cf_ppe_disp")}', ae=lambda: f'={V("cf_ppe_disp")}')
    S('f_sep', '  (+) Separation cash expenditures (added back)', 'line', 'm', flow=True, hist=lambda: f'=IF(ISNUMBER({V("f_pub")}),-{V("f_sep_d")},"")',
      e26=lambda: f'=-{ACT("f_sep_d")}+{H2("d_sep")}', ae=lambda: f'={V("d_sep")}', note='Forecast: separation and restructuring cash = expense (assumption).')
    S('f_restr', '  (+) Corporate & Other restructuring cash expenditures (added back)', 'line', 'm', flow=True, hist=lambda: f'=IF(ISNUMBER({V("f_pub")}),-{V("f_restr_d")},"")',
      e26=lambda: f'=-{ACT("f_restr_d")}+{H2("d_restr")}', ae=lambda: f'=MAX(0,{V("d_restr")})')
    S('fcf', '  = Free cash flow (model bridge)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("f_cfo")}),ISNUMBER({V("f_sep")})),{V("f_cfo")}+{V("f_capex")}+N({V("f_disp")})+{V("f_sep")}+{V("f_restr")},"")',
      note='Company definition in force each period (dispositions of PP&E added from the Q3-25 release, which re-presented 2024: FY2024 $6,203m vs $6,089m originally).')
    S('f_pub', '  Company-published free cash flow', 'memo', 'm', data='fcf_fcf', flow=True)
    S('f_chk', '  Check: model bridge vs company-published (should be 0; ±2 rounding)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("f_pub")}),ISNUMBER({V("fcf")})),IF(ABS({V("fcf")}-{V("f_pub")})<=2.01,0,ROUND({V("fcf")}-{V("f_pub")},0)),"n/p")')
    S('f_sep_d', '  Memo: separation cash expenditures (release, negative)', 'memo', 'm', data='fcf_sep', flow=True)
    S('f_restr_d', '  Memo: Corporate & Other restructuring cash expenditures (release, negative)', 'memo', 'm', data='fcf_restr', flow=True)
    S('f_def', '  Definition / basis (company FCF definition in force)', 'text', 'gen')
    S('cal_fcf_h', '  FY26 FCF guidance calibration (working capital):', 'sub', 'gen')
    S('cal_fcf_tgt', '  FY26 free cash flow guidance end-point (scenario)', 'memo', 'm', e26=lambda: '=' + CH(SC['out_fcf']),
      note='Company FY26 FCF guidance $8.9–9.2B (raised 16-Jul-2026).')
    S('cal_fcf_pre', '  FY26E FCF before the customer-advances plug (advances held at 30-Jun-2026)', 'line', 'm',
      e26=lambda: (f'={ACT("cf_cfo")}+{ACT("cf_capex")}+{ACT("cf_ppe_disp")}+{ACT("f_sep")}+{ACT("f_restr")}+{H2("is_ni")}+{H2("d_dep")}+{H2("d_amort")}-{H2("d_nonop")}-{PT("pt_pens_cash")}/2+{PT("pt_taxnet")}'
                   f'-({V("bs_ar")}-{B1("bs_ar")})-({V("bs_inv")}-{B1("bs_inv")})-({V("bs_ctr_a")}-{B1("bs_ctr_a")})+({V("bs_ap")}-{B1("bs_ap")})'
                   f'+({V("bs_sda")}-{B1("bs_sda")})+({V("bs_ocl")}-{B1("bs_ocl")})-{H2("g_rev")}*{PT("pt_capex")}+{H2("d_sep")}+{H2("d_restr")}'))
    S('cal_fcf_plug', '  FCF calibration: change in customer advances 30-Jun → 31-Dec-2026 (solved)', 'driver', 'm',
      e26=lambda: f'={V("cal_fcf_tgt")}-{V("cal_fcf_pre")}',
      note='Solves the 2H change in customer advances so that FY26 FCF = the guidance end-point for the active scenario (one designated plug; HII / CW / WCN precedent).')
    S('cal_fcf_chk', '  Check: FY26 FCF vs guidance end-point (should be 0)', 'check', 'm', e26=lambda: f'=ROUND({V("fcf")}-{V("cal_fcf_tgt")},0)')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of adjusted revenue', 'pct', 'pct', all=ratio('fcf', 'g_rev'))
    S('fcf_conv', '  FCF conversion (FCF / adjusted net income; company metric)', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    blank()

    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'STATEMENT OF CASH FLOWS (condensed; continuing operations + discontinued operations)', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = H1-26 actual + 2H estimate; quarters = discrete, derived from year-to-date statements; Q1/Q2-23 not presented on the GE Aerospace basis)')
    S('cf_ni', 'Net income (incl. discontinued operations)', 'line', 'm', data='cf_ni', flow=True, e26=e26f('cf_ni', lambda: H2('is_ni')), ae=lambda: f'={V("is_ni")}')
    S('cf_disc', '  (Income) loss from discontinued operations', 'line', 'm', data='cf_disc', flow=True, e26=lambda: f'={ACT("cf_disc")}', ae=lambda: f'=-{V("is_disc")}')
    S('cf_dep', '  Depreciation & amortization of PP&E', 'line', 'm', data='cf_dep', flow=True, e26=e26f('cf_dep', lambda: H2('d_dep')), ae=lambda: f'={V("d_dep")}')
    S('cf_amort', '  Amortization of intangible assets', 'line', 'm', data='cf_amort', flow=True, e26=e26f('cf_amort', lambda: H2('d_amort')), ae=lambda: f'={V("d_amort")}')
    S('cf_gw', '  Goodwill impairments', 'line', 'm', data='cf_gw_imp', flow=True, e26=lambda: f'={ACT("cf_gw")}', ae=lambda: f'={V("d_gw")}')
    S('cf_geq', '  (Gains) losses on equity securities', 'line', 'm', data='cf_geq', flow=True, e26=lambda: f'={ACT("cf_geq")}', ae=lambda: f'=-{V("d_geq")}')
    S('cf_pens', '  Principal pension / postretirement plans (non-cash benefit income reversed; employer contributions & benefit payments)', 'line', 'm',
      data='cf_pens', flow=True, e26=e26f('cf_pens', lambda: f'(-{H2("d_nonop")}-{PT("pt_pens_cash")}/2)'), ae=lambda: f'=-{V("d_nonop")}-{V("cf_pens_cash")}',
      note='Non-operating benefit income is non-cash (reversed here and reduces the net benefit liability); plus cash contributions / payments (input).')
    S('cf_tax', '  Provision for income taxes less cash taxes paid', 'line', 'm', data='cf_taxnet', flow=True, e26=lambda: f'={ACT("cf_tax")}+{PT("pt_taxnet")}', ae_in=V0['taxnet'],
      note='Cash taxes below the provision (tax attributes); input, offset in deferred income taxes (BS).')
    S('cf_wc', '  Changes in operating working capital (receivables, inventories, contract assets / liabilities, progress collections, payables, SD&A)', 'line', 'm',
      data='cf_wc', flow=True,
      e26=lambda: (f'={ACT("cf_wc")}-({V("bs_ar")}-{B1("bs_ar")})-({V("bs_inv")}-{B1("bs_inv")})-({V("bs_ctr_a")}-{B1("bs_ctr_a")})'
                   f'+({V("bs_ap")}-{B1("bs_ap")})+({V("bs_adv")}-{B1("bs_adv")})+({V("bs_sda")}-{B1("bs_sda")})+({V("bs_ocl")}-{B1("bs_ocl")})'),
      ae=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_inv")}-{P("bs_inv")})-({V("bs_ctr_a")}-{P("bs_ctr_a")})'
                  f'+({V("bs_ap")}-{P("bs_ap")})+({V("bs_adv")}-{P("bs_adv")})+({V("bs_sda")}-{P("bs_sda")})+({V("bs_ocl")}-{P("bs_ocl")})'),
      note='Forecast linked to the balance sheet (other current liabilities included).')
    S('cf_oth_op', '  All other operating activities (derived)', 'line', 'm', data='cf_oth_op', flow=True, e26=lambda: f'={ACT("cf_oth_op")}', ae_in=0.0)
    S('cf_cfo', 'Cash from operating activities — continuing operations', 'line_b', 'm', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_oth_op")})')
    S('cf_capex', 'Additions to PP&E and internal-use software', 'line', 'm', data='cf_capex', flow=True,
      e26=lambda: f'={ACT("cf_capex")}-{H2("g_rev")}*{PT("pt_capex")}', ae=lambda: f'=-{V("g_rev")}*{V("capex_pct")}',
      note='2H-26E and 2027E+: adjusted revenue × capex % (input; capex is not guided in the releases).')
    S('cf_ppe_disp', 'Dispositions of PP&E', 'line', 'm', data='cf_ppe_disp', flow=True, e26=lambda: f'={ACT("cf_ppe_disp")}', ae_in=0.0)
    S('cf_acq', 'Business acquisitions (net of cash acquired)', 'line', 'm', data='cf_acq', flow=True, e26=lambda: f'={ACT("cf_acq")}',
      ae=lambda: f'=-IF({V("cpp_cl")}>0,{V("cpp_on")}*{MAN_["cpp"]["price"]},0)-{V("m_spend")}',
      note='2027E: CPP $11.75bn at closing (toggle); plus the M&A lever.')
    S('cf_biz_disp', 'Business dispositions & sales of retained ownership interests (GE HealthCare, AerCap)', 'line', 'm', data='cf_biz_disp', flow=True,
      e26=lambda: f'={ACT("cf_biz_disp")}', ae_in=0.0)
    S('cf_ins_sec', 'Net (purchases) dispositions of insurance investment securities', 'line', 'm', data='cf_ins_sec', flow=True, e26=lambda: f'={ACT("cf_ins_sec")}', ae_in=0.0)
    S('cf_oinv', 'All other investing activities (incl. time deposits; derived)', 'line', 'm', data='cf_oinv', flow=True, e26=lambda: f'={ACT("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Cash from investing activities — continuing operations', 'line_b', 'm', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_debt', 'Net borrowings / (repayments) (short-term net, new issues, repayments)', 'line', 'm', data='cf_debt', flow=True,
      e26=lambda: f'={ACT("cf_debt")}+({V("ds_total")}-{B1("ds_total")})', ae=lambda: f'={V("ds_net")}')
    S('cf_div', 'Dividends paid to shareholders', 'line', 'm', data='cf_div', flow=True,
      e26=lambda: f'={ACT("cf_div")}-{Q3}{R["dps"]}*{Q3}{R["sh_basic"]}-{Q4}{R["dps"]}*{Q4}{R["sh_basic"]}', ae=lambda: f'=-{V("dps")}*{V("bb_beg")}',
      note='Dividends = DPS × shares (2027E+: beginning shares, avoiding circularity with plug-driven buybacks).')
    S('cf_pref', 'Redemption of preferred stock (2023)', 'line', 'm', data='cf_pref', flow=True, e26=lambda: f'={ACT("cf_pref")}', ae_in=0.0)
    S('cf_bb', 'Purchases of common stock for treasury', 'line', 'm', data='cf_bb', flow=True, e26=lambda: f'={ACT("cf_bb")}-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='2026E: H1 actual + 2H scenario input ($20bn authorization, Dec-2025; ~$18.0bn remaining at 30-Jun-2026). 2027E+ = leverage plug.')
    S('cf_ofin', 'All other financing activities (derived)', 'line', 'm', data='cf_ofin', flow=True, e26=lambda: f'={ACT("cf_ofin")}', ae_in=0.0)
    S('cf_cff', 'Cash from financing activities — continuing operations', 'line_b', 'm', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_debt")}:{V("cf_ofin")})')
    S('cf_discops', 'Cash from discontinued operations (operating + investing + financing)', 'line', 'm', data='cf_discops', flow=True,
      e26=lambda: f'={ACT("cf_discops")}', ae_in=0.0)
    S('cf_fx', 'Effect of currency exchange rate changes', 'line', 'm', data='cf_fx', flow=True, e26=lambda: f'={ACT("cf_fx")}', ae_in=0.0)
    S('cf_net', 'Increase (decrease) in cash, cash equivalents and restricted cash', 'line', 'm', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_discops")}+{V("cf_fx")},"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_discops")}+{V("cf_fx")}')
    S('cf_beg', 'Cash, cash equivalents and restricted cash — beginning (incl. discontinued operations)', 'line', 'm', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash, cash equivalents and restricted cash — end (incl. discontinued operations)', 'line_b', 'm', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_disc_cash', '  Less: cash of discontinued operations', 'line', 'm', data='cf_disc_cash', e26=lambda: f'={B1("cf_disc_cash")}', ae=lambda: f'={P("cf_disc_cash")}')
    S('cf_end_cont', 'Cash, cash equivalents and restricted cash — continuing operations', 'line_b', 'm', data='cf_end_cont', fc=lambda: f'={V("cf_end")}-{V("cf_disc_cash")}')
    S('cf_chk1', '  Check: beginning + change = ending cash (should be 0; ±2 rounding in derived quarters)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=2.01,0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},0)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS(SUM({V("cf_ni")}:{V("cf_oth_op")})-{V("cf_cfo")})<=1.01,0,ROUND(SUM({V("cf_ni")}:{V("cf_oth_op")})-{V("cf_cfo")},0)),"")')
    S('cf_pens_cash', '  Memo: pension / OPEB cash contributions & benefit payments (input, positive; drives the pension line above)', 'driver', 'm', ae_in=V0['pens_cash'])
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of adjusted revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("g_rev")},""),"")',
      ae_in=V0['capex_pct'], note='GE Aerospace capex 2.7–3.0% of adjusted revenue 2024–H1-26; 2027E+ includes CPP capacity investment (deck) — input.')
    S('capex_dep', '  Capex / depreciation (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("d_dep")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E = 2H from shares outstanding at 30-Jun-2026; 2027E+ buybacks via the leverage plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = 2H)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans (m)', 'driver', 'm2', e26_in=V0['iss_h2'], ae_in=V0['iss_ae'])
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from shares outstanding at 30-Jun-2026 (balance-sheet caption, Q2-26 10-Q).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since 30-Jun-2026 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'STATEMENT OF FINANCIAL POSITION (condensed; first GE Aerospace balance sheet 31-Dec-2023)', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Jun-2026 balance sheet + 2H flows; 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash, cash equivalents and restricted cash', 'line', 'm', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end_cont")}-{V("bs_rcash")}')
    S('bs_invsec_cur', '  Investment securities — current (equity stakes: GE HealthCare / AerCap 2023–24)', 'line', 'm', data='bs_invsec_cur', bs=True,
      e26=lambda: f'={B1("bs_invsec_cur")}', ae=lambda: f'={P("bs_invsec_cur")}')
    S('bs_ar', '  Current receivables', 'line', 'm', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_inv', '  Inventories, including deferred inventory costs', 'line', 'm', data='bs_inv', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dio")}/365')
    S('bs_ctr_a', '  Current contract assets', 'line', 'm', data='bs_ctr_a', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_ca")}')
    S('bs_oca', '  All other current assets & businesses held for sale (incl. time deposits >3 months)', 'line', 'm', data='bs_oca', bs=True,
      e26=lambda: f'={B1("bs_oca")}', ae=lambda: f'={P("bs_oca")}+{V("ppa_ca")}')
    S('bs_tca', 'Current assets', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_invsec', '  Investment securities (run-off insurance portfolio)', 'line', 'm', data='bs_invsec', bs=True, e26=lambda: f'={B1("bs_invsec")}', ae=lambda: f'={P("bs_invsec")}')
    S('bs_ppe', '  Property, plant and equipment – net (incl. operating-lease ROU)', 'line', 'm', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-({V("cf_capex")}-{ACT("cf_capex")})-{H2("d_dep")}',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("d_dep")}-{V("cf_ppe_disp")}+{V("ppa_ppe")}',
      note='Roll-forward: prior − capex (negative cash flow) − depreciation − disposals + acquired PP&E (CPP, M&A lever).')
    S('bs_gw', '  Goodwill', 'line', 'm', data='bs_gw', bs=True, e26=lambda: f'={B1("bs_gw")}', ae=lambda: f'={P("bs_gw")}+{V("ppa_gw")}')
    S('bs_int', '  Other intangible assets – net', 'line', 'm', data='bs_int', bs=True, e26=lambda: f'={B1("bs_int")}-{H2("d_amort")}',
      ae=lambda: f'={P("bs_int")}-{V("d_amort")}+{V("ppa_intang")}')
    S('bs_ctr_def', '  Contract and other deferred assets', 'line', 'm', data='bs_ctr_def', bs=True, e26=lambda: f'={B1("bs_ctr_def")}', ae=lambda: f'={P("bs_ctr_def")}')
    S('bs_oa', '  All other assets (incl. restricted cash, equity-method investments, prepaid pension; derived)', 'line', 'm', data='bs_oa', bs=True,
      e26=lambda: f'={B1("bs_oa")}', ae=lambda: f'={P("bs_oa")}')
    S('bs_dta', '  Deferred income taxes', 'line', 'm', data='bs_dta', bs=True, e26=lambda: f'={B1("bs_dta")}-{PT("pt_taxnet")}', ae=lambda: f'={P("bs_dta")}-{V("cf_tax")}')
    S('bs_disc_a', '  Assets of discontinued operations', 'line', 'm', data='bs_disc_a', bs=True, e26=lambda: f'={B1("bs_disc_a")}', ae=lambda: f'={P("bs_disc_a")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_invsec")}:{V("bs_disc_a")}),"")')
    S('bs_l', 'LIABILITIES AND EQUITY', 'sub', 'gen')
    S('bs_std', '  Short-term borrowings (incl. current portion of long-term debt)', 'line', 'm', data='bs_std', bs=True, fc=lambda: f'={V("ds_rev")}+MIN({V("ds_notes")},{V("ds_mat")})',
      note='Revolver / commercial paper plug + notes maturing in the following year.')
    S('bs_ap', '  Accounts payable (incl. supply-chain finance, revenue-sharing partners)', 'line', 'm', data='bs_ap', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dpo")}/365')
    S('bs_adv', '  Progress collections + contract liabilities and deferred income (customer advances)', 'line', 'm', flow=False, bs=True,
      hist=lambda: f'=IF(ISNUMBER({V("bs_prog")}),{V("bs_prog")}+{V("bs_ctr_l")},"")', e26=lambda: f'={B1("bs_adv")}+{V("cal_fcf_plug")}',
      ae=lambda: f'={V("wc_rev")}*{V("wc_adv")}',
      note='FY26E: 30-Jun-2026 level + the FCF-guidance plug (customer advances are the swing working-capital item: LTSA billings, progress collections). 2027E+: FY26E ratio to adjusted revenue.')
    S('bs_sda', '  Sales discounts and allowances', 'line', 'm', data='bs_sda', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_sda")}')
    S('bs_ocl', '  All other current liabilities & held for sale (derived)', 'line', 'm', data='bs_ocl', bs=True, e26=lambda: f'={B1("bs_ocl")}',
      ae=lambda: f'={V("wc_rev")}*{V("wc_ocl")}')
    S('bs_tcl', 'Current liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_std")}),{V("bs_std")}+SUM({V("bs_ap")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term borrowings', 'line', 'm', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_std")}')
    S('bs_insl', '  Insurance liabilities and annuity benefits', 'line', 'm', data='bs_insl', bs=True, e26=lambda: f'={B1("bs_insl")}', ae=lambda: f'={P("bs_insl")}')
    S('bs_comp', '  Non-current compensation and benefits (pension / OPEB)', 'line', 'm', data='bs_comp', bs=True,
      e26=lambda: f'={B1("bs_comp")}+({V("cf_pens")}-{ACT("cf_pens")})', ae=lambda: f'={P("bs_comp")}+{V("cf_pens")}')
    S('bs_ol', '  Deferred income, all other liabilities & discontinued operations (derived)', 'line', 'm', bs=True,
      hist=lambda: f'=IF(ISNUMBER({V("bs_ol_d")}),{V("bs_ol_d")},"")', e26=lambda: f'={B1("bs_ol")}', ae=lambda: f'={P("bs_ol")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_std")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_ol")}),"")')
    S('bs_eq', "  Total shareholders' equity", 'line', 'm', data='bs_eq', bs=True,
      e26=lambda: (f'={B1("bs_eq")}+{H2("is_ni_cc")}+{H2("is_disc")}+({V("cf_div")}-{ACT("cf_div")})+({V("cf_bb")}-{ACT("cf_bb")})+({V("cf_ofin")}-{ACT("cf_ofin")})'),
      ae=lambda: f'={P("bs_eq")}+{V("is_ni_cc")}+{V("is_disc")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_ofin")}',
      note='+ net income to common (incl. discontinued) − dividends − repurchases (treasury stock) + other financing (AOCI held flat).')
    S('bs_nci', '  Noncontrolling interests', 'line', 'm', data='bs_nci', bs=True, e26=lambda: f'={B1("bs_nci")}+{H2("is_nci")}', ae=lambda: f'={P("bs_nci")}+{V("is_nci")}')
    S('bs_teq', 'Total equity', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")}+N({V("bs_nci")}),"")')
    S('bs_tle', 'TOTAL LIABILITIES AND EQUITY', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=1.01,0,ROUND({V("bs_ta")}-{V("bs_tle")},0)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=1.01,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},0)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs_ta', bs=True)
    S('bs_prog', '  Memo: progress collections', 'memo', 'm', data='bs_prog', bs=True)
    S('bs_ctr_l', '  Memo: contract liabilities and deferred income (current)', 'memo', 'm', data='bs_ctr_l', bs=True)
    S('bs_ol_d', '  Memo: deferred income + all other liabilities + liabilities of discontinued operations (as reported)', 'memo', 'm', data='bs_ol_all', bs=True)
    S('bs_rcash', '  Memo: restricted cash outside the BS cash line (CF continuing cash − BS cash; held at 30-Jun-2026)', 'memo_calc', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("cf_end_cont")}),ISNUMBER({V("bs_cash_rep")})),{V("cf_end_cont")}-{V("bs_cash_rep")},"")',
      e26=lambda: f'={B1("bs_rcash")}', ae=lambda: f'={P("bs_rcash")}')
    S('bs_cash_rep', '  Memo: BS cash as reported', 'memo', 'm', data='bs_cash', bs=True)
    S('bs_chk_cash', '  Check: BS cash = CF continuing cash − restricted cash memo (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end_cont")}),ISNUMBER({V("bs_rcash")})),ROUND({V("bs_cash")}-{V("cf_end_cont")}+{V("bs_rcash")},0),"")')
    S('bs_shares', '  Memo: shares outstanding at period end (m; balance-sheet caption)', 'memo', 'm1', data='bs_shares', bs=True, e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input; fiscal-year-end levels)')
    S('wc_rev', '  Adjusted revenue — annualised (quarters × 4)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("g_rev")}),{V("g_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_cogs', '  Cost of equipment and services sold — annualised', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_cogs_eq")}),({V("is_cogs_eq")}+{V("is_cogs_sv")})*{4 if CTX.col.q else 1},"")',
)
    S('wc_dso', '  DSO — receivables / adjusted revenue × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_dio', '  Inventory days — inventories / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_inv")}/{V("wc_cogs")}*365,"")', e26_in=V0['wc']['dio'], ae_in=V0['wc']['dio'])
    S('wc_dpo', '  Payable days — payables / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_cogs")}*365,"")', e26_in=V0['wc']['dpo'], ae_in=V0['wc']['dpo'])
    S('wc_ca', '  Current contract assets % of adjusted revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ctr_a")}/{V("wc_rev")},"")', e26_in=V0['wc']['ca'], ae_in=V0['wc']['ca'])
    S('wc_adv', '  Customer advances (progress collections + contract liabilities) % of adjusted revenue', 'pct', 'pct',
      hist=lambda: f'=IFERROR({V("bs_adv")}/{V("wc_rev")},"")', e26=lambda: f'=IFERROR({V("bs_adv")}/{V("wc_rev")},"")', ae=lambda: f'={E("wc_adv")}',
      note='FY26E: output of the FCF calibration; 2027E+: held at the FY26E ratio.')
    S('wc_sda', '  Sales discounts and allowances % of adjusted revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_sda")}/{V("wc_rev")},"")', e26_in=V0['wc']['sda'], ae_in=V0['wc']['sda'])
    S('wc_ocl', '  Other current liabilities % of adjusted revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")',
      e26=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")', ae=lambda: f'={E("wc_ocl")}', note=V0['wc']['note'] + ' Other current liabilities: FY26E held at the 30-Jun-2026 level, then the FY26E ratio.')
    S('wc_nwc', '  Operating NWC (receivables + inventories + contract assets − payables − advances − SD&A − other current liabilities)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_inv")}+{V("bs_ctr_a")}-{V("bs_ap")}-{V("bs_adv")}-{V("bs_sda")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of adjusted revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppa_h', 'Acquisitions — consideration & purchase-price allocation (closing-year column; CPP assumed, M&A lever)', 'sub', 'gen')
    S('ppa_cons', '  Consideration (cash)', 'sched', 'm', ae=lambda: f'=-{V("cf_acq")}')
    S('ppa_ca', '  Net working capital acquired (assumption: 5% of CPP price)', 'sched', 'm', ae=lambda: f'=IF({V("cpp_cl")}>0,{V("cpp_on")}*{MAN_["cpp"]["price"]}*{V0["cpp_nwc"]},0)')
    S('ppa_ppe', '  Property, plant & equipment (CPP 15% of price; M&A lever % of spend)', 'sched', 'm',
      ae=lambda: f'=IF({V("cpp_cl")}>0,{V("cpp_on")}*{MAN_["cpp"]["price"]}*{V0["cpp_ppe"]},0)+{V("m_spend")}*{V("m_ppe")}')
    S('ppa_intang', '  Intangible assets (CPP 35% of price; M&A lever % of spend)', 'sched', 'm',
      ae=lambda: f'=IF({V("cpp_cl")}>0,{V("cpp_on")}*{MAN_["cpp"]["price"]}*{V0["cpp_intp"]},0)+{V("m_spend")}*{V("m_intp")}')
    S('ppa_gw', '  Goodwill (residual)', 'sched', 'm', ae=lambda: f'={V("ppa_cons")}-{V("ppa_ca")}-{V("ppa_ppe")}-{V("ppa_intang")}')
    S('ppa_chk', '  Check: assets acquired − consideration (should be 0)', 'check', 'm',
      ae=lambda: f'=ROUND({V("ppa_ca")}+{V("ppa_ppe")}+{V("ppa_intang")}+{V("ppa_gw")}-{V("ppa_cons")},0)')
    S('ppa_note', '  Deal', 'text', 'gen', ae=lambda: '="CPP (assumed close 30-Sep-2027; PPA illustrative — replace with the 10-Q allocation)"' if CTX.col.year == FYC + 1 else None)
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; stock options & RSUs)', 'sched', 'm1', ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.08)
    S('ds_h', 'Debt schedule (senior / subordinated notes repaid or refinanced at maturity; CPP acquisition debt; revolver / CP drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total borrowings (short-term + long-term)', 'sched', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_rev")}', note=MAN_['debt']['at_2026_06_30'])
    S('ds_notes', '  Notes and other term borrowings', 'sched', 'm', data='debt_tot',
      e26=lambda: f'={B1("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_iss', '  New notes issued (input; 2027E incl. ~$4.75bn CPP acquisition debt)', 'sched', 'm', e26_in=V0['iss_notes'][FYC],
      ae=lambda: f'={V0["iss_notes"][CTX.col.year]}+IF({V("cpp_cl")}>0,{V("cpp_on")}*{MAN_["cpp"]["new_debt"]},0)',
      note='CPP: $11.75bn financed with $7bn existing cash and new debt (8-K 8-Sep-2026). Maturities assumed refinanced (input).')
    S('ds_repay', '  Notes repaid at maturity (input)', 'sched', 'm', e26_in=V0['repay'][FYC], ae_in={y: V0['repay'][y] for y in range(FYC + 1, FYL + 1)},
      note=V0['repay_note'])
    S('ds_mat', '  Maturities in the following year (current portion)', 'sched', 'm', e26_in=V0['mat'][FYC], ae_in={y: V0['mat'][y] for y in range(FYC + 1, FYL + 1)})
    S('ds_pre', '  Cash before revolver / CP (opening cash + CFO + CFI + dividends, buybacks, other financing + discontinued + FX − notes repaid + issued − restricted & disc. cash change)', 'sched', 'm',
      e26=lambda: (f'={B1("cf_end_cont")}+({V("cf_cfo")}-{ACT("cf_cfo")})+({V("cf_cfi")}-{ACT("cf_cfi")})+({V("cf_div")}-{ACT("cf_div")})+({V("cf_bb")}-{ACT("cf_bb")})'
                   f'+({V("cf_ofin")}-{ACT("cf_ofin")})+({V("cf_discops")}-{ACT("cf_discops")})+({V("cf_fx")}-{ACT("cf_fx")})-{V("ds_repay")}+{V("ds_iss")}-{V("bs_rcash")}'),
      ae=lambda: (f'={P("cf_end_cont")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_ofin")}+{V("cf_discops")}+{V("cf_fx")}-{V("ds_repay")}+{V("ds_iss")}'
                  f'-{V("bs_rcash")}'))
    S('ds_min', '  Minimum cash balance (BS cash; assumption)', 'sched', 'm', e26_in=V0['min_cash'], ae_in=V0['min_cash'])
    S('ds_rev', '  Revolver / CP / incremental notes drawn (plug, year end)', 'sched', 'm', e26=lambda: f'=MAX(0,{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_rev")}+{V("ds_min")}-{V("ds_pre")})',
      note='$3.0bn revolving credit facility (2029), undrawn at 31-Dec-2025. Shortfalls below the minimum cash balance are drawn; surplus repays the plug first. '
           'Balances above the $3.0bn commitment are a financing assumption (new notes or commercial paper) — see the headroom memo.')
    S('ds_head', '  Memo: revolver headroom vs the $3.0bn commitment (negative = assumed new notes / CP)', 'memo_calc', 'm',
      e26=lambda: f'=3000-{V("ds_rev")}', ae=lambda: f'=3000-{V("ds_rev")}')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on opening notes %', 'sched', 'pct', ae_in=V0['r_notes'], note=V0['r_notes_note'])
    S('ds_r_rev', '  Interest rate on opening revolver / CP %', 'sched', 'pct', ae_in=0.045)
    S('ds_fees', '  Other financial charges (interest on tax deficiencies, customer advances, fees) ($m)', 'sched', 'm', ae_in=V0['fees'],
      note='Interest and other financial charges were $0.8bn in 2025 on ~$20bn of borrowings; H1-26 $444m.')
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / adjusted EBITDA, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end; BS cash basis)', 'sched', 'm',
      ae=lambda: f'={P("ds_total")}-{P("bs_cash")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_ofin")}-{V("cf_discops")}-{V("cf_fx")}')
    S('lev_tgt', '  Target net debt = target leverage × adjusted EBITDA (pro forma in the CPP closing year)', 'sched', 'm', ae=lambda: f'={V("lev_min")}*{V("r_adj_pf")}')
    S('lev_bb', '  Share repurchases: plug to target leverage', 'sched', 'm', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash beyond the leverage target is returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of adjusted revenue', 'pct', 'pct', all=ratio('is_dda', 'g_rev'))
    S('hr_int', '  Interest and other financial charges ÷ average total borrowings %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on operating profit, full-cost; insurance excluded)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Operating profit (adjusted EBIT, full-cost)', 'line', 'm', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Adjusted effective tax rate', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("e_rate")}+0,0.17)')
    S('ra_nopat', 'NOPAT = Operating profit × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity', 'line', 'm', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),{V("bs_teq")},"n/a")')
    S('ra_nd', '  Net debt = Total borrowings − Cash', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Operating profit / Adjusted revenue', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("g_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Adjusted revenue / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("g_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition (excl. the run-off insurance balance sheet)', 'sub', 'gen')
    S('rn_nopat', 'NOPAT', 'line', 'm', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-({V("bs_gw")}+{V("bs_int")}),"n/a")')
    S('rn_ins', '  − Insurance investment securities, cash, discontinued-operations assets', 'line', 'm', ann=True,
      all=lambda: f'=IFERROR(-({V("bs_invsec")}+{V("bs_cash")}+{V("bs_disc_a")}),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (current liabilities excl. borrowings)', 'line', 'm', ann=True,
      all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})),"n/a")')
    S('rn_nta', '  = Net tangible operating assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income from continuing operations to common', 'line', 'm', ann=True, all=lambda: f'={V("is_ni_cc")}')
    S('roe_eq', "Shareholders' equity", 'line', 'm', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total borrowings − cash', 'line', 'm', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA (pro forma in the CPP closing year)', 'line', 'm', ann=True, all=lambda: f'={V("r_adj_pf")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_gx', 'Total borrowings / adjusted EBITDA (x)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("ds_total")}/{V("lv_eb")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+({Q2}{R["sh_dil"]}-{Q2}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interests (USDm)', 'line', 'm', e26=lambda: f'={V("bs_nci")}', ae=lambda: f'={V("bs_nci")}')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")',
      note='Run-off insurance (investment securities vs insurance liabilities and annuity benefits) is excluded from net debt and from NOPAT (assumed self-funding; no capital contributions modelled).')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Adjusted revenue', lambda: f'=IFERROR({V("v_ev")}/{V("g_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA (pro forma)', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj_pf")},"n/a")'),
                      ('v_evop', '  EV / Operating profit', lambda: f'=IFERROR({V("v_ev")}/{V("o_op")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP continuing, diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
