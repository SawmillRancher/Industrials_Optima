"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules (NCR Atleos purchase accounting,
debt, leverage-targeted buybacks), ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, QEc, B1, tol

PPA = [('cash', 'Cash and cash equivalents acquired'), ('rcash', 'Restricted cash acquired'), ('ar', 'Accounts receivable'),
       ('oca', 'Inventories, prepaid expenses and other current assets'), ('rou', 'Right-of-use assets'), ('ppe', 'Property and equipment'),
       ('intang', 'Identifiable intangible assets (customer relationships, developed technology, trade name)'), ('onca', 'Deferred tax assets and other noncurrent assets'),
       ('debt', 'Debt assumed (long-term debt incl. current maturities)'), ('ap', 'Accounts payable'), ('ocl', 'Accrued, contract and settlement liabilities'),
       ('ret', 'Accrued pension costs and other retirement benefits'), ('lease', 'Lease liabilities'), ('ol', 'Deferred tax liabilities and other liabilities')]
PPA_A = ('cash', 'rcash', 'ar', 'oca', 'rou', 'ppe', 'intang', 'onca')
PPA_L = ('debt', 'ap', 'ocl', 'ret', 'lease', 'ol')

def build_spec2(V0):
    S = add
    def e26f(key, q4):          # 2026E flow = 9M actual (Q1-Q3/26) + Q4/26E estimate
        return lambda: f'={ACT(key)}+{q4()}'
    T = lambda k: f'{V("nc_tgl")}*{V("ppa_" + k)}'          # acquired balance (closing-year column)
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 9M 2026 actual + Q4 estimate; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net income (incl. noncontrolling interests)', 'line', 'm1', data='cf_ni', flow=True,
      fc=lambda: f'={V("is_cont")}+{V("is_disc")}', e26=e26f('cf_ni', lambda: f'{QEc("is_cont")}+{QEc("is_disc")}'))
    S('cf_adj', 'Non-cash items:', 'sub', 'gen')
    S('cf_dda', '  Depreciation and amortization', 'line', 'm1', data='cf_da', flow=True, fc=lambda: f'={V("is_dda")}', e26=e26f('cf_dda', lambda: QEc('is_dda')))
    S('cf_sbc', '  Share-based compensation expense', 'line', 'm1', data='cf_sbc', flow=True, fc=lambda: f'={V("is_sbc")}', e26=e26f('cf_sbc', lambda: QEc('is_sbc')))
    S('cf_def', '  Deferred income taxes', 'line', 'm1', data='cf_def', flow=True, e26=lambda: f'={ACT("cf_def")}+{V0["def_q4"]}',
      ae=lambda: f'={V("cf_def_in")}-{V("nc_amort")}*{V("ds_dtl")}',
      note='Forecast = input − deferred-tax-liability unwind on the NCR Atleos acquired-intangible amortization (stock-and-cash merger: the step-up is not tax-deductible).')
    S('cf_def_in', '  Deferred income taxes — legacy input', 'driver', 'm1', ae_in=V0['def_ae'])
    S('cf_wc', '  Working capital & other operating items, net (derived)', 'line', 'm1', data='cf_oop', flow=True,
      e26=lambda: f'={ACT("cf_wc")}+{V("wc_q4")}',
      ae=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")}-{T("ar")})-({V("bs_oca")}-{P("bs_oca")}-{T("oca")})'
                  f'+({V("bs_ap")}-{P("bs_ap")}-{T("ap")})+({V("bs_ocl")}-{P("bs_ocl")}-{T("ocl")})'),
      note=('History: net cash from operations − net income − D&A − share-based compensation − deferred taxes (includes restricted cash held for customers, customer obligations, '
            'retirement funding, gains / losses and discontinued operations). 2026E: 9M actual + Q4 calibration to the free-cash-flow framework. '
            '2027E+: −Δ(receivables, other current assets) + Δ(payables, other current liabilities), excluding the NCR Atleos balances acquired.'))
    S('wc_q4', '  Q4/26E working capital & other operating items (solved so that 2026E free cash flow = conversion guidance × adjusted EBITDA)', 'driver', 'm1',
      e26=lambda: (f'={CH(SC["out_fcf"])}*{V("r_adj")}-{ACT("fcf")}-({QEc("is_cont")}+{QEc("is_disc")}+{QEc("is_dda")}+{QEc("is_sbc")}+{V0["def_q4"]})'
                   f'-({V("cf_capex")}-{ACT("cf_capex")})-({V("cf_ppe")}-{ACT("cf_ppe")})'),
      note='Calibration: 2026 framework free cash flow conversion 40–45% of adjusted EBITDA (Bull / Base / Bear = 45% / 42.5% / 40%). The offset is in accrued and other current liabilities on the balance sheet.')
    S('cf_cfo', 'Net cash provided by operating activities', 'line_b', 'm1', data='cf_cfo', flow=True,
      e26=lambda: f'={V("cf_ni")}+{V("cf_dda")}+{V("cf_sbc")}+{V("cf_def")}+{V("cf_wc")}', ae=lambda: f'={V("cf_ni")}+{V("cf_dda")}+{V("cf_sbc")}+{V("cf_def")}+{V("cf_wc")}')
    S('cf_capex', 'Capital expenditures', 'line', 'm1', data='cf_capex', flow=True,
      e26=lambda: f'={ACT("cf_capex")}-{PT("pt_capex")}', ae=lambda: f'=-({V("is_rev")}-N({V("nc_rev")}))*{V("capex_pct")}-N({V("nc_rev")})*N({V("nc_capex")})',
      note='2026E: 9M actual + Q4 point estimate. 2027E+: legacy revenues × capex % + NCR Atleos revenues × its capex %.')
    S('cf_acq', 'Acquisitions, net of cash acquired', 'line', 'm1', data='cf_acq', flow=True,
      e26=lambda: f'={ACT("cf_acq")}', ae=lambda: f'=-{V("nc_tgl")}*({V("ppa_cashcons")}-{V("ppa_cash")}-{V("ppa_rcash")})',
      note='2027E: NCR Atleos cash consideration net of cash and restricted cash acquired (the cash-flow statement reconciles cash incl. restricted cash).')
    S('cf_ppe', 'Cash proceeds from sale of property and equipment', 'line', 'm1', data='cf_ppe', flow=True, e26=lambda: f'={ACT("cf_ppe")}', ae_in=V0['ppe_sale'])
    S('cf_oinv', 'Other investing activities, net (marketable securities, economic hedges, deconsolidations; derived)', 'line', 'm1', data='cf_oinv', flow=True, e26=lambda: f'={ACT("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Net cash used in investing activities', 'line_b', 'm1', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_bb', 'Repurchase shares of Brink\'s common stock', 'line', 'm1', data='cf_bb', flow=True, e26=lambda: f'={ACT("cf_bb")}-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='2026E: 9M actual + Q4 scenario input ($720m left on the 2025 Repurchase Program at 30-Sep-2026). 2027E+ = leverage plug (surplus cash returned once net debt / adjusted EBITDA is below the threshold).')
    S('cf_div', 'Dividends to shareholders of Brink\'s', 'line', 'm1', data='cf_div', flow=True,
      e26=lambda: f'={ACT("cf_div")}-{QEc("dps")}*{V0["cover_sh"]}', ae=lambda: f'=-{V("dps")}*({V("bb_beg")}+{V("bb_deal")})',
      note='DPS × beginning shares (+ NCR Atleos consideration shares), so dividends are not circular with plug-driven buybacks.')
    S('cf_divnci', 'Dividends to noncontrolling interests', 'line', 'm1', data='cf_divnci', flow=True, e26=lambda: f'={ACT("cf_divnci")}', ae_in=V0['divnci'])
    S('cf_debt', 'Net debt issuance / (repayment) (forecast; in "debt and other financing" historically)', 'line', 'm1',
      e26=lambda: f'={V("ds_total")}-{B1("ds_total")}', ae=lambda: f'={V("ds_total")}-{P("ds_total")}-{V("nc_tgl")}*{V("ppa_debt")}',
      note='Per the debt schedule: change in total debt (excluding the NCR Atleos debt assumed, which is not a cash flow).')
    S('cf_ofin', 'Debt and other financing, net (derived historically; forecast: tax withholdings on share-based compensation, debt costs)', 'line', 'm1', data='cf_ofin', flow=True,
      e26=lambda: f'={ACT("cf_ofin")}', ae_in=V0['ofin'])
    S('cf_cff', 'Net cash provided by (used in) financing activities', 'line_b', 'm1', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_bb")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of exchange rate changes on cash', 'line', 'm1', data='cf_fx', flow=True, e26=lambda: f'={ACT("cf_fx")}', ae_in=0.0)
    S('cf_net', 'Net change in cash, cash equivalents and restricted cash', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+N({V("cf_cfi")})+N({V("cf_cff")})+N({V("cf_fx")}),"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}')
    S('cf_repr', 'Re-presentation of opening cash between filings (derived; Q2/16)', 'memo', 'm1', data='cf_repr', flow=True,
      note='Q2/16: the six-month cash-flow statement opens at $181.9m, while the Q1/16 statement closed at $186.8m from an opening $198.3m (31-Dec-2015 as first filed).')
    S('cf_beg', 'Cash — beginning of period (cash and cash equivalents to 2017; incl. restricted cash from 2018)', 'line', 'm1', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period', 'line_b', 'm1', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: beginning cash + CFO + CFI + CFF + FX = ending cash (should be 0; ±0.3)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_cfi")})),{tol(V("cf_beg") + "+" + V("cf_net") + "+N(" + V("cf_repr") + ")", V("cf_end"), 0.3)},"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_wc")}),{tol(V("cf_ni") + "+" + V("cf_dda") + "+N(" + V("cf_sbc") + ")+N(" + V("cf_def") + ")+" + V("cf_wc"), V("cf_cfo"), 0.25)},"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf_adj', '  Customer-cash and other adjustments (company definition; derived = published free cash flow − CFO − capex − proceeds from property sales)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("fcf_pub")}),ROUND({V("fcf_pub")}-{V("cf_cfo")}-{V("cf_capex")}-{V("cf_ppe")},1),"")', e26=lambda: f'={ACT("fcf_adj")}', ae_in=0.0,
      note='Company: exclude changes in restricted cash held for customers and certain customer obligations; add proceeds from lessor debt financing; exclude NCR Atleos acquisition cash costs (2026). Forecast: nil.')
    S('fcf', 'Free cash flow before dividends (company definition where published; otherwise CFO − capex + property-sale proceeds)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")}+N({V("cf_ppe")})+N({V("fcf_adj")}),"")')
    S('fcf_pub', '  Company-published free cash flow before dividends', 'memo', 'm1', data='fcf_pub', flow=True)
    S('fcf_chk', '  Check: model vs company-published free cash flow (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("fcf_pub")}),{tol(V("fcf"), V("fcf_pub"))},"n/p")')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of revenues', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / non-GAAP income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / adjusted EBITDA % (company "free cash flow conversion")', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of revenues (legacy)', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note='FY2025 3.9%; 9M 2026 2.7% (armored vehicles increasingly financed by lessors). 2027E+ input.')
    S('capex_dep', '  Capex / D&A (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("d_dda")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E = Q4 from the shares outstanding on the 10-Q cover (30-Oct-2026); 2027E+ buybacks via the leverage plug; NCR Atleos consideration shares at closing')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = Q4)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans (m)', 'driver', 'm2', e26_in=0.0, ae_in=V0['iss_ae'])
    S('bb_deal', '  Shares issued to NCR Atleos stockholders (0.1574 per share; ~11.6m, 424B3)', 'line', 'm2', e26_in=0.0,
      ae=lambda: f'={V("nc_tgl")}*{V("ppa_shares")}')
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26_in=V0['cover_sh'], ae=lambda: f'={P("bb_end")}',
      note='2026E begins from the 41,200,799 shares outstanding at 30-Oct-2026 (Q3-26 10-Q cover).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}+{V("bb_deal")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}+{V("bb_deal")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since Q4/26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET (condensed)', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Sep-2026 balance sheet + Q4 flows; 2027E+ from prior year end (+ NCR Atleos balances at fair value in the closing year)')
    def acq(k, flat=False):          # prior balance + acquired, grown with pro forma organic revenue growth
        return (lambda: f'={P("bs_" + k)}+{T(k)}') if flat else (lambda: f'=({P("bs_" + k)}+{T(k)})*(1+{V("wc_g")})')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm1', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}-{V("bs_rcash")}')
    S('bs_rcash', '  Restricted cash (shown separately from 2018)', 'line', 'm1', data='bs_rcash', bs=True, e26=lambda: f'={B1("bs_rcash")}', ae=acq('rcash', True))
    S('bs_ar', '  Accounts receivable, net', 'line', 'm1', data='bs_ar', bs=True, e26=lambda: f'={B1("bs_ar")}', ae=acq('ar'))
    S('bs_oca', '  Prepaid expenses and other current assets (derived; incl. NCR Atleos inventories from closing)', 'line', 'm1', data='bs_oca', bs=True, e26=lambda: f'={B1("bs_oca")}', ae=acq('oca'))
    S('bs_tca', 'Total current assets', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_cash")}+N({V("bs_rcash")})+{V("bs_ar")}+{V("bs_oca")},"")')
    S('bs_rou', '  Right-of-use assets, net (from 2019)', 'line', 'm1', data='bs_rou', bs=True, e26=lambda: f'={B1("bs_rou")}', ae=acq('rou', True))
    S('bs_ppe', '  Property and equipment, net', 'line', 'm1', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-({V("cf_capex")}-{ACT("cf_capex")})-({QEc("d_dda")}-{QEc("d_amort")})',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("cf_ppe")}-({V("d_dda")}-{V("d_amort")})+{T("ppe")}',
      note='Roll-forward: prior − capex (negative cash flow) − disposals − depreciation (D&A excl. acquisition amortization) + NCR Atleos property and equipment.')
    S('bs_gw', '  Goodwill', 'line', 'm1', data='bs_gw', bs=True, e26=lambda: f'={B1("bs_gw")}', ae=lambda: f'={P("bs_gw")}+{V("nc_tgl")}*{V("ppa_gw")}')
    S('bs_int', '  Other intangibles, net', 'line', 'm1', data='bs_int', bs=True,
      e26=lambda: f'={B1("bs_int")}-{QEc("d_amort")}', ae=lambda: f'={P("bs_int")}-{V("d_amort")}+{T("intang")}',
      note='Roll-forward: prior − amortization of acquisition-related intangibles + NCR Atleos identifiable intangibles.')
    S('bs_onca', '  Deferred tax assets and other assets (derived)', 'line', 'm1', data='bs_onca', bs=True, e26=lambda: f'={B1("bs_onca")}', ae=acq('onca', True))
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+N({V("bs_rou")})+{V("bs_ppe")}+{V("bs_gw")}+N({V("bs_int")})+{V("bs_onca")},"")')
    S('bs_l', 'LIABILITIES AND EQUITY', 'sub', 'gen')
    S('bs_std', '  Short-term borrowings and current maturities of long-term debt', 'line', 'm1', data='bs_std', bs=True, fc=lambda: f'=MIN({V("ds_total")},{V("ds_cur")})')
    S('bs_ap', '  Accounts payable', 'line', 'm1', data='bs_ap', bs=True, e26=lambda: f'={B1("bs_ap")}', ae=acq('ap'))
    S('bs_ocl', '  Accrued liabilities, restricted cash held for customers and other current liabilities (derived)', 'line', 'm1', data='bs_ocl', bs=True,
      e26=lambda: f'={B1("bs_ocl")}+{V("wc_q4")}', ae=acq('ocl'), note='2026E: 30-Sep-2026 balance + the Q4 working-capital calibration (free-cash-flow framework).')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_std")}+{V("bs_ap")}+{V("bs_ocl")},"")')
    S('bs_ltd', '  Long-term debt', 'line', 'm1', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_std")}')
    S('bs_ret', '  Accrued pension costs and retirement benefits other than pensions', 'line', 'm1', data='bs_ret', bs=True, e26=lambda: f'={B1("bs_ret")}', ae=acq('ret', True))
    S('bs_lease', '  Lease liabilities (noncurrent; from 2019)', 'line', 'm1', data='bs_lease', bs=True, e26=lambda: f'={B1("bs_lease")}', ae=acq('lease', True))
    S('bs_ol', '  Deferred tax liabilities and other liabilities (derived)', 'line', 'm1', data='bs_ol', bs=True,
      e26=lambda: f'={B1("bs_ol")}+({V("cf_def")}-{ACT("cf_def")})', ae=lambda: f'={P("bs_ol")}+{V("cf_def")}+{T("ol")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+{V("bs_ltd")}+{V("bs_ret")}+N({V("bs_lease")})+{V("bs_ol")},"")')
    S('bs_eq', '  Brink\'s shareholders\' equity', 'line', 'm1', data='bs_eq', bs=True,
      e26=lambda: (f'={B1("bs_eq")}+{QEc("is_ni")}+({V("cf_div")}-{ACT("cf_div")})+({V("cf_bb")}-{ACT("cf_bb")})+{QEc("d_sbc")}'),
      ae=lambda: f'={P("bs_eq")}+{V("is_ni")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_sbc")}+{V("cf_ofin")}+{V("nc_tgl")}*({V("ppa_stock")}+{V("ppa_awards")})',
      note='+ net income − dividends − repurchases + share-based compensation − tax withholdings on awards (other financing) + shares and converted awards issued for NCR Atleos (OCI / currency translation held flat).')
    S('bs_nci', '  Noncontrolling interests', 'line', 'm1', data='bs_nci', bs=True,
      e26=lambda: f'={B1("bs_nci")}+{QEc("is_nci")}', ae=lambda: f'={P("bs_nci")}+{V("is_nci")}+{V("cf_divnci")}')
    S('bs_teq', 'Total equity', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")}+N({V("bs_nci")}),"")')
    S('bs_tle', 'TOTAL LIABILITIES AND EQUITY', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),{tol(V("bs_ta"), V("bs_tle"), 0.25)},"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),{tol(V("bs_ta"), V("bs_ta_pub"), 0.25)},"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm1', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash (+ restricted cash from 2018) vs cash-flow ending cash (should be 0)', 'check', 'm1',
      all=lambda: (f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),{tol(V("bs_cash") + "+N(" + V("bs_rcash") + ")-N(" + V("bs_cash_m") + ")", V("cf_end"), 0.25)},"")'))
    S('bs_cash_m', '  Memo: BS cash + restricted cash − cash per the cash-flow statement (held-for-sale or re-presented balances; derived)', 'memo', 'm1', data='bs_cash_diff', bs=True)
    S('bs_shares', '  Memo: shares outstanding at period end (m)', 'memo', 'm1', data='bs_shares', bs=True, e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — year-end balances vs revenues; forecast balances grow with pro forma organic revenue growth (NCR Atleos balances added at closing)')
    S('wc_rev', '  Revenues — annualised (quarters × 4)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_pf', '  Prior-year revenues, pro forma for NCR Atleos in the closing year', 'line', 'm1',
      ae=lambda: f'={P("is_rev")}+IF({P("nc_tgl")}=0,{V("nc_tgl")}*{P("nc_sa_rev")},0)')
    S('wc_g', '  Pro forma revenue growth % (drives working-capital balances)', 'pct', 'pct', ae=lambda: f'=IFERROR({V("is_rev")}/{V("wc_pf")}-1,0)')
    S('wc_dso', '  DSO — receivables / revenues × 365', 'line', 'd', all=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")')
    S('wc_app', '  Accounts payable % of revenues', 'pct', 'pct', all=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_rev")},"")')
    S('wc_oclp', '  Other current liabilities % of revenues', 'pct', 'pct', all=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")')
    S('wc_nwc', '  Operating NWC (receivables + other current assets − payables − other current liabilities; excl. cash and restricted cash)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_oca")}-{V("bs_ap")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of revenues', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm1', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppa_h', 'NCR Atleos — consideration & preliminary purchase-price allocation (424B3 unaudited pro forma; closing-year column)', 'sub', 'gen')
    S('ppa_cashcons', '  Cash consideration ($30.00 × 73.8m NCR Atleos shares; 424B3)', 'sched', 'm1', ae_in=V0['ppa']['cashcons'], note=MAN['ncr_atleos']['ppa_note'])
    S('ppa_shares', '  Brink\'s shares issued (m; 0.1574 × NCR Atleos shares)', 'sched', 'm2', ae_in=V0['ppa']['shares'])
    S('ppa_stock', '  Stock consideration (shares issued × model share price; 424B3 used $107.22)', 'sched', 'm1', ae=lambda: f'={V("ppa_shares")}*{P("v_px")}')
    S('ppa_awards', '  Converted equity awards attributable to pre-acquisition services', 'sched', 'm1', ae_in=V0['ppa']['awards'])
    S('ppa_cons', '  Total purchase consideration', 'sched', 'm1', ae=lambda: f'={V("ppa_cashcons")}+{V("ppa_stock")}+{V("ppa_awards")}')
    for k, lab in PPA:
        S(f'ppa_{k}', f'  {lab}', 'sched', 'm1', ae_in=V0['ppa'][k])
    S('ppa_gw', '  Goodwill (consideration − net identifiable assets acquired)', 'sched', 'm1',
      ae=lambda: f'={V("ppa_cons")}-({"+".join(V("ppa_" + k) for k in PPA_A)})+({"+".join(V("ppa_" + k) for k in PPA_L)})',
      note='424B3: $3,333.1m at a $107.22 share price; the model revalues the stock consideration at the model share price.')
    S('ppa_chk', '  Check: assets acquired + goodwill − liabilities assumed − consideration (should be 0)', 'check', 'm1',
      ae=lambda: f'=ROUND({"+".join(V("ppa_" + k) for k in PPA_A)}+{V("ppa_gw")}-({"+".join(V("ppa_" + k) for k in PPA_L)})-{V("ppa_cons")},1)')
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; awards)', 'sched', 'm1', ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing; assumption)', 'sched', 'pct', ae_in=0.15,
      note='Assumption: the share price used for buybacks compounds at 15% a year, below the modelled non-GAAP EPS growth, so that repurchases are not priced at a falling multiple. Not a price forecast.')
    S('ds_dtl', '  Deferred-tax rate on NCR Atleos acquired-intangible amortization (DTL $650.4m ÷ intangibles $2,895.4m)', 'sched', 'pct', ae_in=0.225)
    S('ds_h', 'Debt schedule (senior notes, other facilities and leases: scheduled; revolver, term loans and acquisition facilities: prepayable, drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (short-term borrowings + current maturities + long-term debt)', 'sched', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_fixed")}+{V("ds_rev")}', note=MAN['debt']['at_2026_09_30'])
    S('ds_fixed', '  Senior notes, other facilities, financing leases and short-term borrowings (scheduled debt)', 'sched', 'm1',
      e26=lambda: f'={B1("ds_total")}-{V0["prepayable_q3"]}-{V("ds_repay")}+{V("ds_iss")}', ae=lambda: f'={P("ds_fixed")}-{V("ds_repay")}+{V("ds_iss")}+{V("ds_deal_fixed")}',
      note='30-Sep-2026: total debt $4,155.1m − revolving credit facility $458.8m − term loans $1,218.9m = $2,477.4m.')
    S('ds_iss', '  New notes issued (input)', 'sched', 'm1', e26_in=0.0, ae_in=V0['iss_notes'], note='2027E: refinancing of the $600m 4.625% senior notes due October 2027 (assumption).')
    S('ds_repay', '  Notes repaid at maturity (input)', 'sched', 'm1', e26_in=0.0, ae_in=V0['repay'], note='$600m 4.625% senior notes due 15-Oct-2027; $400m 6.5% notes due 2029 and $400m 6.75% notes due 2032 remain outstanding (2029 refinanced: issue = repayment).')
    S('ds_deal_fixed', '  NCR Atleos debt assumed that stays outstanding (senior secured notes and other; debt assumed − facilities refinanced)', 'sched', 'm1', e26_in=0.0,
      ae=lambda: f'=IF({P("nc_tgl")}=0,{V("nc_tgl")}*({V("ppa_debt")}-{V0["refinanced"]}),0)', note=MAN['ncr_atleos']['financing'])
    S('ds_deal_prep', '  NCR Atleos acquisition facilities (bridge / permanent debt $2,276m + NCR Atleos facilities refinanced $1,468m; prepayable)', 'sched', 'm1', e26_in=0.0,
      ae=lambda: f'=IF({P("nc_tgl")}=0,{V("nc_tgl")}*({V0["bridge"]}+{V0["refinanced"]}),0)')
    S('ds_cur', '  Short-term borrowings and maturities in the following year (current portion)', 'sched', 'm1', e26_in=V0['cur'][FYC], ae_in={y: V0['cur'][y] for y in range(FYC + 1, FYL + 1)})
    S('ds_pre', '  Cash before prepayable-debt draws / repayments (opening cash + CFO + CFI + buybacks, dividends, other financing + FX − notes repaid + issued − NCR Atleos facilities repaid at closing)', 'sched', 'm1',
      e26=lambda: (f'={B1("cf_end")}+({V("cf_cfo")}-{ACT("cf_cfo")})+({V("cf_cfi")}-{ACT("cf_cfi")})+({V("cf_bb")}-{ACT("cf_bb")})+({V("cf_div")}-{ACT("cf_div")})'
                   f'+({V("cf_divnci")}-{ACT("cf_divnci")})+({V("cf_ofin")}-{ACT("cf_ofin")})+({V("cf_fx")}-{ACT("cf_fx")})-{V("ds_repay")}+{V("ds_iss")}'),
      ae=lambda: (f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_bb")}+{V("cf_div")}+{V("cf_divnci")}+{V("cf_ofin")}+{V("cf_fx")}-{V("ds_repay")}+{V("ds_iss")}'
                  f'-{V("nc_tgl")}*IF({P("nc_tgl")}=0,{V0["refinanced"]},0)'))
    S('ds_min', '  Minimum cash balance (cash, cash equivalents and restricted cash; assumption)', 'sched', 'm1', e26_in=V0['min_cash'][FYC], ae_in={y: V0['min_cash'][y] for y in range(FYC + 1, FYL + 1)},
      note='Brink\'s holds about $2.0bn of cash and restricted cash, much of it operating cash in the cash-management network and cash held for customers. Minimum = the 30-Sep-2026 level; + NCR Atleos cash and restricted cash from 2027E (assumption).')
    S('ds_rev', '  Prepayable bank debt — revolving credit facility, term loans and NCR Atleos acquisition facilities (year end)', 'sched', 'm1',
      e26=lambda: f'=MAX(0,{V0["prepayable_q3"]}+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_rev")}+{V("ds_min")}-{V("ds_pre")})',
      note='Shortfalls below the minimum cash balance are drawn; surplus cash repays the revolver and term loans before any buybacks. 30-Sep-2026: $458.8m + $1,218.9m.')
    S('ds_head', '  Memo: prepayable bank debt vs facilities in place ($1.0bn revolver + $1.225bn term loan; + $600m upsize, delayed-draw term loan and $2,276m bridge with NCR Atleos) — negative = further financing needed', 'memo_calc', 'm1',
      e26=lambda: f'=2225-{V("ds_rev")}', ae=lambda: f'=2225+{V("nc_tgl")}*({V0["bridge"]}+{V0["refinanced"]})-{V("ds_rev")}')
    S('ds_r_fixed', '  Interest rate on opening scheduled debt %', 'sched', 'pct', ae_in=V0['r_fixed'], note=V0['r_note'])
    S('ds_r_rev', '  Interest rate on opening prepayable bank debt %', 'sched', 'pct', ae_in=V0['r_rev'])
    S('ds_r_deal', '  Interest rate on NCR Atleos debt assumed, closing year % (assumption: 9.5% senior secured notes due 2029)', 'sched', 'pct', ae_in=V0['r_deal'],
      note='Assumption — verify against the NCR Atleos indenture: the debt that stays outstanding is mainly its 9.500% senior secured notes due 2029. From the following year it is inside the blended scheduled-debt rate.')
    S('ds_fees', '  Commitment fees and financing-cost amortization ($m)', 'sched', 'm1', ae_in=V0['fees'])
    S('lev_h', 'Leverage-targeted buybacks (repurchases resume once net debt / adjusted EBITDA is below the threshold, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Net debt / adjusted EBITDA threshold (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_ebitda', '  Adjusted EBITDA for leverage (pro forma for the NCR Atleos pre-closing days)', 'sched', 'm1', ae=lambda: f'={V("r_adj")}+N({V("nc_pf_eb")})')
    S('lev_pre', '  Net debt before buybacks (year end; total debt − cash and cash equivalents)', 'sched', 'm1',
      ae=lambda: (f'={P("ds_total")}-{P("bs_cash")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_divnci")}-{V("cf_ofin")}-{V("cf_fx")}'
                  f'+{V("nc_tgl")}*({V("ppa_debt")}+{V("ppa_rcash")})'),
      note='Opening net debt − free cash flow after acquisitions, dividends and other financing + NCR Atleos debt assumed (restricted cash acquired is not netted).')
    S('lev_tgt', '  Threshold net debt = threshold × adjusted EBITDA', 'sched', 'm1', ae=lambda: f'={V("lev_min")}*{V("lev_ebitda")}')
    S('lev_bb', '  Share repurchases: plug to the leverage threshold', 'sched', 'm1', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Cash beyond the leverage threshold is returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of revenues', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_int', '  Interest expense ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    S('hr_nci', '  Noncontrolling interests % of income from continuing operations', 'pct', 'pct', all=ratio('is_nci', 'is_cont'))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted EBIT = non-GAAP operating profit)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT (non-GAAP operating profit; GAAP operating profit where non-GAAP is not published)', 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("r_ebit")}),{V("r_ebit")},{V("is_op")})')
    S('ra_t', 'Tax rate (non-GAAP effective rate; GAAP effective rate bounded 15–40% in history)', 'line', 'pct', ann=True,
      hist=lambda: f'=IFERROR(MIN(0.4,MAX(0.15,{V("is_etr")}+0)),0.3)', fc=lambda: f'={V("e_rate")}')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Total equity + Net debt', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity', 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),{V("bs_teq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − cash and cash equivalents', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Revenues', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Revenues / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),{V("bs_ta")},"n/a")')
    S('rn_gw', '  − Goodwill & other intangibles', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-({V("bs_gw")}+N({V("bs_int")})),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. short-term debt)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})),"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income attributable to Brink\'s', 'line', 'm1', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Brink's shareholders' equity", 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")},"n/a")')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash and cash equivalents', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA (2027E: pro forma for the NCR Atleos pre-closing days)', 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+N({V("nc_pf_eb")}),"n/a")')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")',
      note='Model definition (total debt incl. financing leases − cash and cash equivalents). The company\'s own net debt also deducts cash held by cash-management operations and is therefore higher.')
    S('lv_gx', 'Total debt / adjusted EBITDA (x)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("ds_total")}/{V("lv_eb")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interests (USDm)', 'line', 'm', e26=lambda: f'={V("bs_nci")}', ae=lambda: f'={V("bs_nci")}')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Revenues', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("lv_eb")},"n/a")'),
                      ('v_evop', '  EV / Non-GAAP operating profit', lambda: f'=IFERROR({V("v_ev")}/{V("o_adj")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted, continuing operations)', lambda: f'=IFERROR({V("v_px")}/{V("eps_cont")},"n/a")'),
                      ('v_pea', '  P / E (non-GAAP EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
