"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, ACT0, QEc, B1, YY

def build_spec2(V0):
    S = add
    def e26f(key, q4):          # 2026E flow = 9M actual (Q1-Q3/26) + Q4/26E estimate
        return lambda: f'={ACT(key)}+{q4()}'
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED CASH FLOW STATEMENT (condensed, as in the releases)', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 9M actual + Q4 estimate; quarters = discrete, derived from the year-to-date statements)')
    S('cf_ni', 'Net earnings', 'line', 'm', data='cf_ni', flow=True, fc=lambda: f'={V("is_ni")}', e26=e26f('cf_ni', lambda: QEc('is_ni')))
    S('cf_adj', 'Adjustments to reconcile net earnings to net cash provided by operating activities:', 'sub', 'gen')
    S('cf_dep', '  Depreciation and amortization', 'line', 'm', data='cf_dep', flow=True, fc=lambda: f'={V("is_dda")}', e26=e26f('cf_dep', lambda: QEc('is_dda')))
    S('cf_def', '  Deferred income tax expense', 'line', 'm', data='cf_def', flow=True, e26=lambda: f'={ACT("cf_def")}+{PT("pt_def")}', ae_in=V0['def_ae'],
      note='Q4/26E point estimate; 2027E+ input (2025 $194m, 2024 $12m, 2023 $64m; bonus depreciation). Feeds the deferred-tax liability roll-forward.')
    S('cf_impair', '  Goodwill impairment (non-cash)', 'line', 'm', data='cf_impair', flow=True, fc=lambda: f'={V("d_impair")}')
    S('cf_oth', '  Other operating activities — net, incl. working capital (derived)', 'line', 'm', data='cf_oth', flow=True,
      e26=lambda: f'={ACT("cf_oth")}+{QEc("is_sbc")}-{PT("pt_affil")}-({V("bs_oca")}-{B1("bs_oca")})+({V("bs_ocl")}-{B1("bs_ocl")})',
      ae=lambda: f'={V("is_sbc")}-{V("affil_g")}-({V("bs_oca")}-{P("bs_oca")})+({V("bs_ocl")}-{P("bs_ocl")})',
      note='History: CFO − net earnings − D&A − deferred taxes − impairment (release statements show other operating items and working capital as one line from 2010). Forecast: share-based compensation − retained equity earnings of affiliates (non-cash) − Δ other current assets + Δ other current liabilities.')
    S('cf_cfo', 'Net cash provided by operating activities', 'line_b', 'm', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_oth")})')
    S('cf_capex', 'Property additions', 'line', 'm', data='cf_capex', flow=True, e26=lambda: f'=-{PT("pt_capex")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='2026E: FY26 capital investment "less than $2.4bn" (Q3-26 10-Q; point estimate $2,350m). 2027E+: revenue × capex %.')
    S('cf_disp', 'Proceeds and advances from property dispositions', 'line', 'm', data='cf_disp', flow=True, e26=lambda: f'={ACT("cf_disp")}+{PT("pt_disp")}', ae_in=V0['disp_ae'],
      note='2025 $78m; 2024 $66m; 9M-26 $144m. Forecast input.')
    S('cf_sti', 'Short-term investments — purchases and sales, net', 'line', 'm', data='cf_sti', flow=True, e26=lambda: f'={ACT("cf_sti")}', ae_in=0.0,
      note='Forecast nil: the short-term investment balance is held at 30-Sep-2026 ($382m).')
    S('cf_acq', 'Business acquisitions, net of cash acquired', 'line', 'm', data='cf_acq', flow=True, e26=lambda: f'={ACT("cf_acq")}', ae=lambda: f'=-{V("m_spend")}',
      note='Quality Carriers $541m (Jul-2021); Pan Am cash $178m (Jun-2022); small trucking deals 2024–25. 2027E+: M&A lever (Base nil).')
    S('cf_oinv', 'Other investing activities — net (derived; insurance proceeds, Conrail, other)', 'line', 'm', data='cf_oinv', flow=True, e26=lambda: f'={ACT("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Net cash used in investing activities', 'line_b', 'm', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_bb', 'Shares repurchased', 'line', 'm', data='cf_bb', flow=True, e26=lambda: f'={ACT("cf_bb")}-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='2026E: 9M actual ($1,061m) + Q4 scenario input ($5.16bn authority remaining at 30-Sep-2026). 2027E+ = leverage plug (surplus cash returned until net debt / adjusted EBITDA reaches the target).')
    S('cf_div', 'Dividends paid', 'line', 'm', data='cf_div', flow=True, e26=lambda: f'={ACT("cf_div")}-{QEc("dps")}*{B1("bs_shares")}', ae=lambda: f'=-{V("dps")}*{V("bb_beg")}',
      note='DPS × beginning shares (no circularity with the buyback plug).')
    S('cf_debt_iss', 'Long-term debt issued (net of plug notes repaid)', 'line', 'm', data='cf_debt_iss', flow=True,
      e26=lambda: f'={ACT("cf_debt_iss")}+{V("ds_iss")}+({V("ds_pn")}-{B1("ds_pn")})', ae=lambda: f'={V("ds_iss")}+({V("ds_pn")}-{P("ds_pn")})',
      note='Per the debt schedule: maturities refinanced with new notes (input) + notes assumed issued to term out borrowings above the CP program (plug).')
    S('cf_debt_rep', 'Long-term debt repaid', 'line', 'm', data='cf_debt_rep', flow=True, e26=lambda: f'={ACT("cf_debt_rep")}-{V("ds_repay")}', ae=lambda: f'=-{V("ds_repay")}')
    S('cf_std', 'Commercial paper / short-term debt — net (forecast: plug to the minimum cash balance, up to the $1.0bn program)', 'line', 'm', data='cf_std', flow=True,
      e26=lambda: f'={ACT("cf_std")}+({V("ds_cp")}-{B1("ds_cp")})', ae=lambda: f'={V("ds_cp")}-{P("ds_cp")}')
    S('cf_ofin', 'Other financing activities — net (derived; stock options, excise tax, other)', 'line', 'm', data='cf_ofin', flow=True, e26=lambda: f'={ACT("cf_ofin")}', ae_in=V0['ofin_ae'])
    S('cf_cff', 'Net cash used in financing activities', 'line_b', 'm', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_bb")}:{V("cf_ofin")})')
    S('cf_net', 'Net increase (decrease) in cash and cash equivalents', 'line', 'm', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")},"")', fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}')
    S('cf_beg', 'Cash and cash equivalents at beginning of period', 'line', 'm', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash and cash equivalents at end of period', 'line_b', 'm', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: beginning cash + net change = ending cash (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=0.6,0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},0)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS(SUM({V("cf_ni")}:{V("cf_oth")})-{V("cf_cfo")})<=0.6,0,ROUND(SUM({V("cf_ni")}:{V("cf_oth")})-{V("cf_cfo")},0)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow before dividends (company definition: CFO − property additions + property disposition proceeds; + other investing to 2021)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")}+N({V("cf_disp")})+{"N(" + V("cf_oinv") + ")" if CTX.col.year <= 2021 else "0"},"")',
      note='Company FCF published from 2017. Definition to 2021: CFO − property additions + other investing activities (which then included disposition proceeds, excluding acquisitions and short-term investments); from 2022: CFO − property additions + proceeds and advances from property dispositions. Flag in the definition row.')
    S('fcf_pub', '  Company-published free cash flow (quarters derived from the year-to-date figures)', 'memo', 'm', data='cf_fcf_pub', flow=True)
    S('fcf_chk', '  Check: model vs company-published free cash flow (should be 0; 2020 ±30: other-investing classification in the company table)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("fcf_pub")}),IF(ABS({V("fcf")}-{V("fcf_pub")})<={"30.5" if CTX.col.year == 2020 else "0.6"},0,ROUND({V("fcf")}-{V("fcf_pub")},0)),"n/p")')
    S('fcf_def', '  Definition / basis (company free cash flow definition)', 'text', 'gen')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of revenue', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net earnings conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Property additions % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note='2027E+ input: 2025 20.6% (incl. the $440m Blue Ridge subdivision rebuild after Hurricane Helene), 2024 17.4%, 2019–23 14–15%; 9M-26 15.0%.')
    S('capex_dep', '  Property additions / D&A (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("dep")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E = Q4 from shares outstanding at 30-Sep-2026 (10-Q cover); 2027E+ buybacks via the leverage plug; repurchased shares are retired (excess over par to retained earnings)')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = Q4)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans (m)', 'driver', 'm2', e26_in=V0['iss_q4'], ae_in=V0['iss_ae'])
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from the Q3-26 10-Q cover-page count (1,843.4m).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since Q4/26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONDENSED CONSOLIDATED BALANCE SHEET (as in the releases)', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Sep-2026 balance sheet + Q4 flows; 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}')
    S('bs_sti', '  Short-term investments', 'line', 'm', data='bs_sti', bs=True, e26=lambda: f'={B1("bs_sti")}-({V("cf_sti")}-{ACT("cf_sti")})', ae=lambda: f'={P("bs_sti")}-{V("cf_sti")}')
    S('bs_oca', '  Other current assets (receivables, materials and supplies, other)', 'line', 'm', data='bs_oca', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_ocap")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_ppe', '  Properties — net', 'line', 'm', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-({V("cf_capex")}-{ACT("cf_capex")})-{QEc("dep")}-({V("cf_disp")}-{ACT("cf_disp")})',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-({V("dep")}-N({V("m_amort")}))+{V("m_spend")}*{V("m_ppe")}-{V("cf_disp")}',
      note='Roll-forward: prior − property additions (negative cash flow) − D&A (excl. acquired-intangible amortization, which runs through other long-term assets) − net book value of dispositions (assumed = proceeds; gains sit inside the purchased-services ratio) + acquired PP&E.')
    S('bs_affil', '  Investment in affiliates and other companies (Conrail, TTX and other)', 'line', 'm', data='bs_affil', bs=True,
      e26=lambda: f'={B1("bs_affil")}+{PT("pt_affil")}', ae=lambda: f'={P("bs_affil")}+{V("affil_g")}',
      note='Grows with retained equity earnings of affiliates (2025 +$114m; 9M-26 +$73m). Input.')
    S('bs_olta', '  Other long-term assets (goodwill & intangibles, operating lease assets, pension, other; derived)', 'line', 'm', data='bs_olta', bs=True,
      e26=lambda: f'={B1("bs_olta")}', ae=lambda: f'={P("bs_olta")}+{V("m_spend")}*(1-{V("m_ppe")})-N({V("m_amort")})')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_ppe")}:{V("bs_olta")}),"")')
    S('bs_l', "LIABILITIES AND SHAREHOLDERS' EQUITY", 'sub', 'gen')
    S('bs_cmltd', '  Current maturities of long-term debt and short-term debt (commercial paper)', 'line', 'm', data='bs_cmltd', bs=True, fc=lambda: f'={V("ds_cp")}+MIN({V("ds_notes")},{V("ds_mat")})',
      note='Forecast = commercial paper + notes maturing in the following year (10-K ladder).')
    S('bs_ocl', '  Other current liabilities (payables, labor and fringe, casualty reserves, taxes, other)', 'line', 'm', data='bs_ocl', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_oclp")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cmltd")}),{V("bs_cmltd")}+{V("bs_ocl")},"")')
    S('bs_ltd', '  Long-term debt', 'line', 'm', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_cmltd")}')
    S('bs_dit', '  Deferred income taxes — net', 'line', 'm', data='bs_dit', bs=True, e26=lambda: f'={B1("bs_dit")}+({V("cf_def")}-{ACT("cf_def")})', ae=lambda: f'={P("bs_dit")}+{V("cf_def")}',
      note='Roll-forward: prior + deferred income tax expense (cash-flow statement).')
    S('bs_oltl', '  Other long-term liabilities (casualty, environmental, pension, lease, other; derived)', 'line', 'm', data='bs_oltl', bs=True, e26=lambda: f'={B1("bs_oltl")}', ae=lambda: f'={P("bs_oltl")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cmltd")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_oltl")}),"")')
    S('bs_te', "  Total shareholders' equity (incl. non-controlling minority interest)", 'line', 'm', data='bs_te', bs=True,
      e26=lambda: f'={B1("bs_te")}+{QEc("is_ni")}+({V("cf_div")}-{ACT("cf_div")})+({V("cf_bb")}-{ACT("cf_bb")})+{QEc("is_sbc")}+({V("cf_ofin")}-{ACT("cf_ofin")})',
      ae=lambda: f'={P("bs_te")}+{V("is_ni")}+{V("cf_div")}+{V("cf_bb")}+{V("is_sbc")}+{V("cf_ofin")}',
      note='+ net earnings − dividends − repurchases (retired; excess over par to retained earnings) + share-based compensation + other financing (option proceeds, excise tax); OCI held flat.')
    S('bs_nci', '  Memo: non-controlling minority interest (within total equity; $2m–$15m)', 'memo', 'm', data='bs_nci', bs=True, fc=lambda: '=0')
    S('bs_tle', "TOTAL LIABILITIES AND SHAREHOLDERS' EQUITY", 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_te")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=0.6,0,ROUND({V("bs_ta")}-{V("bs_tle")},0)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=0.6,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},0)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash vs cash-flow ending cash (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}-{V("cf_end")})<=0.6,0,ROUND({V("bs_cash")}-{V("cf_end")},0)),"")')
    S('bs_shares', '  Memo: shares outstanding at period end (m; 10-K balance sheet / 10-Q cover page, split-adjusted)', 'memo', 'm1', data='bs_shares', bs=True, e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    S('bs_gwi', '  Memo: goodwill and other intangible assets — net (XBRL; inside other long-term assets)', 'memo', 'm', data='intang_gw', bs=True)
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input); the condensed releases give other current assets / liabilities only, so the drivers are % of revenue')
    S('wc_rev', '  Revenue — annualised (quarters × 4)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_ocap', '  Other current assets % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_oca")}/{V("wc_rev")},"")', e26_in=V0['wc']['oca'], ae_in=V0['wc']['oca'])
    S('wc_oclp', '  Other current liabilities % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")', e26_in=V0['wc']['ocl'], ae_in=V0['wc']['ocl'], note=V0['wc']['note'])
    S('wc_ar', '  Memo: accounts receivable — net (10-K / 10-Q XBRL)', 'memo', 'm', data='ar', bs=True)
    S('wc_dso', '  Memo: DSO — receivables / revenue × 365', 'memo_calc', 'd', all=lambda: f'=IF(ISNUMBER({V("wc_ar")}),IFERROR({V("wc_ar")}/{V("wc_rev")}*365,""),"")')
    S('wc_nwc', '  Operating NWC (other current assets − other current liabilities)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_oca")}),{V("bs_oca")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppe_h', 'Properties and affiliates roll-forward inputs', 'sub', 'gen')
    S('affil_g', '  Increase in investment in affiliates (USDm, input; retained equity earnings of Conrail / TTX, non-cash)', 'sched', 'm', ae_in=V0['affil_g'],
      note='2025 +$114m, 2024 +$112m, 9M-26 +$73m. Input $90m p.a.; deducted from other operating cash flow as a non-cash item.')
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive awards (m shares; diluted − basic weighted shares, 2026: 4m)', 'sched', 'm1', qe_in=V0['dil'], ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.07)
    S('ds_h', 'Debt schedule (notes repaid at maturity and refinanced; commercial paper drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (current maturities + commercial paper + long-term debt)', 'sched', 'm', hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),{V("bs_cmltd")}+{V("bs_ltd")},"")',
      fc=lambda: f'={V("ds_notes")}+{V("ds_pn")}+{V("ds_cp")}', note=MAN['debt']['at_2025_12_31'] + ' ' + MAN['debt']['at_2026_09_30'])
    S('ds_notes', '  Notes and finance leases (long-term debt incl. current maturities; excl. plug notes below)', 'sched', 'm', hist=lambda: f'=IF(ISNUMBER({V("ds_total")}),{V("ds_total")}-{V("ds_cp")},"")',
      e26=lambda: f'={B1("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_iss', '  New notes issued (input; 2027E+ = maturities refinanced)', 'sched', 'm', e26_in=V0['iss_notes'][FYC], ae_in={y: V0['iss_notes'][y] for y in range(FYC + 1, FYL + 1)},
      note=MAN['debt']['issues'] + ' Forecast: maturities refinanced at par with new notes (assumption; CSX targets an investment-grade profile and has refinanced every maturity since 2017).')
    S('ds_repay', '  Notes repaid at maturity (10-K ladder; input)', 'sched', 'm', e26_in=V0['repay'][FYC], ae_in={y: V0['repay'][y] for y in range(FYC + 1, FYL + 1)}, note=V0['repay_note'])
    S('ds_mat', '  Maturities in the following year (current portion)', 'sched', 'm', e26_in=V0['mat'][FYC], ae_in={y: V0['mat'][y] for y in range(FYC + 1, FYL + 1)})
    S('ds_pre', '  Cash before commercial paper (opening cash + CFO + CFI + buybacks, dividends, other financing − notes repaid + issued)', 'sched', 'm',
      e26=lambda: (f'={B1("bs_cash")}+({V("cf_cfo")}-{ACT("cf_cfo")})+({V("cf_cfi")}-{ACT("cf_cfi")})+({V("cf_bb")}-{ACT("cf_bb")})+({V("cf_div")}-{ACT("cf_div")})'
                   f'+({V("cf_ofin")}-{ACT("cf_ofin")})-{V("ds_repay")}+{V("ds_iss")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_bb")}+{V("cf_div")}+{V("cf_ofin")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_min', '  Minimum cash balance', 'sched', 'm', e26_in=V0['min_cash'], ae_in=V0['min_cash'], note='CSX held $0.6–1.5bn of cash at the last five year ends (2025: $670m plus $5m short-term investments). Input $800m.')
    S('ds_borrow', '  Borrowing required to hold the minimum cash balance (plug: opening borrowings + minimum cash − cash before borrowings)', 'sched', 'm', hist=lambda: '=0',
      e26=lambda: f'=MAX(0,{B1("ds_borrow")}+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_borrow")}+{V("ds_min")}-{V("ds_pre")})',
      note='Shortfalls below the minimum cash balance are borrowed; surplus repays the borrowings first, then funds buybacks via the leverage plug.')
    S('ds_cp', '  of which commercial paper (year end; up to the $1.0bn program)', 'sched', 'm', data='cf_std_bal', hist=lambda: '=0',
      fc=lambda: f'=MIN({V("ds_borrow")},1000)',
      note='$1.0bn commercial paper program backed by the $1.2bn revolver (Feb-2028); none outstanding at 30-Sep-2026 (historical balances sit inside current maturities, shown there).')
    S('ds_pn', '  of which notes assumed issued to term out borrowings above the CP program (financing assumption)', 'sched', 'm', hist=lambda: '=0',
      fc=lambda: f'={V("ds_borrow")}-{V("ds_cp")}',
      note='Any borrowing above the $1.0bn CP program is assumed refinanced with new senior notes at the new-issue coupon (CSX issued $0.55–0.9bn of notes in each of 2023–25).')
    S('ds_head', '  Memo: CP program headroom vs the $1.0bn limit', 'memo_calc', 'm', e26=lambda: f'=1000-{V("ds_cp")}', ae=lambda: f'=1000-{V("ds_cp")}')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on opening notes %', 'sched', 'pct', ae_in=V0['r_notes'], note='10-K: 4.4% average rate on notes at 31-Dec-2025; 2025 interest expense $844m on ~$18.7bn average debt (4.5%). Drifts up as 3.25–3.8% maturities are refinanced at ~5%.')
    S('ds_r_new', '  Coupon on new notes %', 'sched', 'pct', ae_in=0.05, e26_in=0.05, note='Mar/Oct-2025 5.05% notes due 2035; Sep-2024 4.90% due 2055; Sep-2023 5.20% due 2033.')
    S('ds_r_cp', '  Interest rate on opening commercial paper %', 'sched', 'pct', ae_in=0.045)
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / adjusted EBITDA, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end)', 'sched', 'm',
      ae=lambda: f'={P("ds_total")}-{P("cf_end")}-{P("bs_sti")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_ofin")}')
    S('lev_tgt', '  Target net debt = target leverage × adjusted EBITDA', 'sched', 'm', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to target leverage', 'sched', 'm', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash beyond the leverage target is returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  D&A % of revenue', 'pct', 'pct', all=ratio('dep', 'is_rev'))
    S('hr_int', '  Interest expense ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    S('hr_payout', '  Dividends + buybacks % of free cash flow', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("fcf")}),IFERROR(-({V("cf_div")}+{V("cf_bb")})/{V("fcf")},""),"")')
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted EBIT = adjusted operating income)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT (adjusted operating income)', 'line', 'm', ann=True, all=lambda: f'={V("r_aebit")}')
    S('ra_t', 'Effective tax rate (adjusted; bounded 15–40%)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(MIN(0.4,MAX(0.15,{V("e_rate")}+0)),0.245)')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity', 'line', 'm', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_te")}),{V("bs_te")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − cash − short-term investments', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")}-{V("bs_sti")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Revenue', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Revenue / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangible assets (XBRL where tagged; immaterial: $63m rail goodwill to 2020, $267m at 2025)', 'line', 'm', ann=True, all=lambda: f'=-N({V("bs_gwi")})')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (other current liabilities)', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-{V("bs_ocl")},"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net earnings', 'line', 'm', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Shareholders' equity", 'line', 'm', ann=True, all=lambda: f'={V("bs_te")}')
    S('roe', 'ROE = Net earnings / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash − short-term investments', 'line', 'm', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA', 'line', 'm', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_gx', 'Total debt / adjusted EBITDA (x)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("ds_total")}/{V("r_adj")},"n/a")')
    S('lv_q', 'Memo: net debt / LTM adjusted EBITDA at quarter ends (x)', 'line', 'x2', all=lambda: (f'=IFERROR(({V("ds_total")}-{V("bs_cash")}-{V("bs_sti")})/{V("r_lev_ltm")},"")' if CTX.col.q else None))
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+{V("ds_dil")}', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Non-controlling interests (USDm)', 'line', 'm', e26=lambda: f'={V("bs_nci")}', ae=lambda: f'={V("bs_nci")}')
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
