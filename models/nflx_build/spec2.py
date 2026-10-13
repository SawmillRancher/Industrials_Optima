"""Row specification part 2: cash flow (content investment), share schedule, balance sheet, working capital, debt and cash-return
schedules, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, H2, B1

def build_spec2(V0):
    S = add
    def e26f(key, src):          # FY2026E flow = 1H-26 actual + 2H-26 estimate (Q3-Q4/26E of the linked P&L row)
        return lambda: f'={ACT(key)}+{H2(src)}'
    def d2(bs):                  # 2H-26 change of a balance-sheet line (2026E year end − 30-Jun-2026)
        return f'({V(bs)}-{B1(bs)})'
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENTS OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 1H-26 actual + 2H estimate; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net income', 'line', 'm1', data='cf_ni', flow=True, fc=lambda: f'={V("is_ni")}', e26=e26f('cf_ni', 'is_ni'))
    S('cf_adj', 'Adjustments (content and non-cash items):', 'sub', 'gen')
    S('cf_cadd', '  Additions to content assets (operating; streaming content from 2010)', 'line', 'm1', data='cf_cadd', flow=True,
      e26=lambda: f'=-{PT("pt_ccr")}*{V("cf_camort")}-{V("cf_cliab")}', ae=lambda: f'=-{V("ccr")}*{V("cf_camort")}-{V("cf_cliab")}',
      note='Forecast: cash content spend (additions + change in content liabilities) = cash content spend / amortization ratio × content amortization (2026E: ~1.1x guided; 2027E+: scenario lever).')
    S('cf_cliab', '  Change in content liabilities', 'line', 'm1', data='cf_cliab', flow=True, e26=lambda: f'={ACT("cf_cliab")}', ae_in=0.0)
    S('cf_camort', '  Amortization of content assets (streaming + DVD)', 'line', 'm1', data='camort', flow=True, fc=lambda: f'={V("d_camort")}', e26=e26f('cf_camort', 'd_camort'))
    S('cf_dep', '  Depreciation & amortization of property, equipment & intangibles', 'line', 'm1', data='cf_dep', flow=True, fc=lambda: f'={V("is_dda")}', e26=e26f('cf_dep', 'is_dda'))
    S('cf_sbc', '  Stock-based compensation expense', 'line', 'm1', data='cf_sbc', flow=True, fc=lambda: f'={V("is_sbc")}', e26=e26f('cf_sbc', 'is_sbc'))
    S('cf_fxdebt', '  Foreign-currency remeasurement loss / (gain) on debt', 'line', 'm1', data='cf_fxdebt', flow=True, e26=lambda: f'={ACT("cf_fxdebt")}', ae_in=0.0)
    S('cf_def', '  Deferred income taxes', 'line', 'm1', data='cf_def', flow=True, e26=lambda: f'={ACT("cf_def")}', ae_in=V0['def_ae'], note='Forecast input (assumption).')
    S('cf_oop', '  Working capital & other operating items, net (derived)', 'line', 'm1', data='cf_oop', flow=True,
      e26=lambda: (f'={ACT("cf_oop")}-{d2("bs_oca")}+{d2("bs_ap")}+{d2("bs_accr")}+{d2("bs_defrev")}+{d2("bs_ocl")}+{V("cal_wc")}'),
      ae=lambda: (f'=-({V("bs_oca")}-{P("bs_oca")})+({V("bs_ap")}-{P("bs_ap")})+({V("bs_accr")}-{P("bs_accr")})+({V("bs_defrev")}-{P("bs_defrev")})+({V("bs_ocl")}-{P("bs_ocl")})'),
      note=('History: net cash from operating activities − the lines above (other non-cash items and changes in operating assets and liabilities). '
            'Forecast linked to the balance sheet: −Δ other current assets + Δ(payables, accrued, deferred revenue, other current liabilities).'))
    S('cf_cfo', 'Net cash provided by (used in) operating activities', 'line_b', 'm1', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_oop")})')
    S('cf_capex', 'Purchases of property and equipment', 'line', 'm1', data='cf_capex', flow=True,
      e26=lambda: f'={ACT("cf_capex")}-{H2("is_rev")}*{PT("pt_capex")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='2026E: 1H-26 actual + 2H revenue × capex % (point estimate; not guided). 2027E+: revenue × capex %.')
    S('cf_dvd', 'Acquisitions of DVD / content library (investing; streaming content too before 2010)', 'line', 'm1', data='cf_dvd', flow=True, e26=lambda: f'={ACT("cf_dvd")}', ae_in=0.0)
    S('cf_acq', 'Acquisitions (businesses, intangibles)', 'line', 'm1', data='cf_acq', flow=True, e26=lambda: f'={ACT("cf_acq")}', ae=lambda: f'=-{V("m_spend")}',
      note='2026E = 1H actual (Mar-2026 acquisition, $585.7m). 2027E+: M&A lever.')
    S('cf_inv', 'Purchases, sales & maturities of investments, net', 'line', 'm1', data='cf_inv', flow=True, e26=lambda: f'={ACT("cf_inv")}', ae_in=0.0)
    S('cf_oinv', 'Other investing activities (derived)', 'line', 'm1', data='cf_oinv', flow=True, e26=lambda: f'={ACT("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Net cash provided by (used in) investing activities', 'line_b', 'm1', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_diss', 'Proceeds from issuance of debt (incl. revolver draws)', 'line', 'm1', data='cf_diss', flow=True,
      e26=lambda: f'={ACT("cf_diss")}+{V("ds_iss")}+MAX(0,{V("ds_rev")}-{B1("ds_rev")})', ae=lambda: f'={V("ds_iss")}+MAX(0,{V("ds_rev")}-{P("ds_rev")})',
      note='2026E: $1bn 5.250% notes due 2036 issued 22-Jul-2026. 2027E+: maturities refinanced (debt schedule).')
    S('cf_drep', 'Repayments of debt (incl. revolver repayments)', 'line', 'm1', data='cf_drep', flow=True,
      e26=lambda: f'={ACT("cf_drep")}-{V("ds_repay")}-MAX(0,{B1("ds_rev")}-{V("ds_rev")})', ae=lambda: f'=-{V("ds_repay")}-MAX(0,{P("ds_rev")}-{V("ds_rev")})')
    S('cf_stock', 'Proceeds from issuance of common stock', 'line', 'm1', data='cf_stock', flow=True, e26=lambda: f'={ACT("cf_stock")}+{V0["stock_2h"]}', ae_in=V0['stock_ae'])
    S('cf_bb', 'Repurchases of common stock (incl. taxes paid on net share settlement)', 'line', 'm1', data='cf_bb', flow=True,
      e26=lambda: f'={ACT("cf_bb")}-{V("cr_bb")}', ae=lambda: f'=-{V("cr_bb")}',
      note='2026E: 1H actual ($6.0bn) + 2H cash-return plug; 2027E+: plug to the target cash balance (cash-return schedule). $27.1bn authorization left at 30-Jun-2026.')
    S('cf_ofin', 'Other financing activities (derived)', 'line', 'm1', data='cf_ofin', flow=True, e26=lambda: f'={ACT("cf_ofin")}', ae_in=0.0)
    S('cf_cff', 'Net cash provided by (used in) financing activities', 'line_b', 'm1', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_diss")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of exchange-rate changes on cash', 'line', 'm1', data='cf_fx', flow=True, e26=lambda: f'={ACT("cf_fx")}', ae_in=0.0)
    S('cf_net', 'Net change in cash (cash, cash equivalents and restricted cash from 2018)', 'line', 'm1', data='cf_net', flow=True,
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}')
    S('cf_beg', 'Cash — beginning of period', 'line', 'm1', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period', 'line_b', 'm1', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: beginning cash + CFO + CFI + CFF + FX = ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")})-{V("cf_end")})<=0.15,0,ROUND({V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")})-{V("cf_end")},1)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS(SUM({V("cf_ni")}:{V("cf_oop")})-{V("cf_cfo")})<=0.15,0,ROUND(SUM({V("cf_ni")}:{V("cf_oop")})-{V("cf_cfo")},1)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('cf_restr', '  Restricted cash (cash-flow cash − balance-sheet cash; included in cash-flow cash from 2018)', 'line', 'm1', data='cf_restr',
      e26=lambda: f'={B1("cf_restr")}', ae=lambda: f'={P("cf_restr")}')
    S('ccs', 'Cash content spend (additions to content assets + change in content liabilities + DVD acquisitions)', 'line', 'm1', flow=True,
      all=lambda: f'=IF(ISNUMBER({V("cf_cadd")}),-({V("cf_cadd")}+{V("cf_cliab")}+N({V("cf_dvd")})),"")')
    S('ccr', '  Cash content spend / content amortization (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("ccs")}),IFERROR({V("ccs")}/{V("cf_camort")},""),"")',
      ae=lambda: '=' + CH(SC['CCR'][CTX.col.year]), note='Guided ~1.1x for 2026. 2027E+: scenario lever (content cash spend running slightly ahead of amortization).')
    S('fcf', 'Free cash flow (company definition)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")}+N({V("fcf_oth")}),"")',
      note='CFO − purchases of property and equipment (from 2021). Earlier definitions also deducted DVD / content-library acquisitions, intangibles and other assets (2006–2016) and the change in other assets (2017–2020) — row below.')
    S('fcf_oth', '  Other items in the company FCF definition (DVD library, other assets, investing ex investments; to 2020)', 'line', 'm1', data='fcf_oth', flow=True, labkey='fcf_oth_lab', fc=lambda: '=0')
    S('fcf_pub', '  Company-published free cash flow', 'memo', 'm1', data='fcf_pub', flow=True)
    S('fcf_chk', '  Check: model vs company-published free cash flow (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("fcf_pub")}),IF(ABS({V("fcf")}-{V("fcf_pub")})<=0.15,0,ROUND({V("fcf")}-{V("fcf_pub")},1)),"n/p")')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of revenue', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / net income %', 'pct', 'pct', all=ratio('fcf', 'is_ni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note='2027E+ input (1H-26 1.7% of revenue: studio and production-facility investment).')
    S('capex_dep', '  Capex / non-content D&A (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("d_dep")},""),"")')
    S('cal_wc', '  FY26 FCF calibration: 2H other operating cash flow — deposits in other non-current assets (solves FCF to guidance)', 'driver', 'm1',
      e26=lambda: (f'={V("cal_fcf")}-({ACT("cf_cfo")}+{H2("is_ni")}+{H2("d_camort")}+({V("cf_cadd")}-{ACT("cf_cadd")})+({V("cf_cliab")}-{ACT("cf_cliab")})'
                   f'+{H2("is_dda")}+{H2("is_sbc")}-{d2("bs_oca")}+{d2("bs_ap")}+{d2("bs_accr")}+{d2("bs_defrev")}+{d2("bs_ocl")}+{V("cf_capex")})'),
      note=('FCF guidance (~$12.5bn) is hit by a 2H-26 other operating cash flow booked to other non-current assets (negative = outflow). The Q4-25 letter expected a ~$700m deposit '
            'in 2026 for the Brazilian tax dispute; a deposit does not reverse, so 2027E+ working capital is unaffected.'))
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E = 2H from shares outstanding at 30-Jun-2026; buybacks = cash-return plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = 2H)', 'line', 'm', e26=lambda: f'={V("cr_bb")}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans (m)', 'driver', 'm2', e26_in=V0['iss_2h'], ae_in=V0['iss_ae'])
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from shares outstanding at 30-Jun-2026 (Q2-26 10-Q, XBRL).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since 30-Jun-2026 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEETS (condensed, as reported)', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Jun-2026 balance sheet + 2H flows; 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm1', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}-{V("cf_restr")}')
    S('bs_sti', '  Short-term investments', 'line', 'm1', data='bs_sti', bs=True, e26=lambda: f'={B1("bs_sti")}', ae=lambda: f'={P("bs_sti")}')
    S('bs_ccont', '  Current content assets / library, net (to 2019)', 'line', 'm1', data='bs_ccont', bs=True, e26=lambda: f'={B1("bs_ccont")}', ae=lambda: f'={P("bs_ccont")}')
    S('bs_oca', '  Other current assets', 'line', 'm1', data='bs_oca', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_cont', '  Content assets, net (non-current; DVD library to 2011)', 'line', 'm1', data='bs_cont', bs=True,
      e26=lambda: f'={B1("bs_cont")}-({V("cf_cadd")}-{ACT("cf_cadd")})-({V("cf_camort")}-{ACT("cf_camort")})',
      ae=lambda: f'={P("bs_cont")}-{V("cf_cadd")}-{V("cf_camort")}', note='Roll-forward: prior + additions (cash content spend − change in liabilities) − amortization.')
    S('bs_ppe', '  Property and equipment, net', 'line', 'm1', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-({V("cf_capex")}-{ACT("cf_capex")})-({V("cf_dep")}-{ACT("cf_dep")})', ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("cf_dep")}',
      note='Roll-forward: prior + capex − non-content D&A (intangibles amortization included; small).')
    S('bs_onca', '  Other non-current assets (incl. goodwill, lease right-of-use, deferred taxes; derived)', 'line', 'm1', data='bs_onca', bs=True,
      e26=lambda: f'={B1("bs_onca")}-({V("cf_acq")}-{ACT("cf_acq")})-{V("cal_wc")}', ae=lambda: f'={P("bs_onca")}-{V("cf_acq")}',
      note='2026E: + 2H acquisitions + the FCF-calibration deposit; 2027E+: + M&A spend.')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_cont")}:{V("bs_onca")}),"")')
    S('bs_l', "LIABILITIES AND STOCKHOLDERS' EQUITY", 'sub', 'gen')
    S('bs_ccl', '  Current content liabilities', 'line', 'm1', data='bs_ccl', bs=True, e26=lambda: f'={B1("bs_ccl")}', ae=lambda: f'={P("bs_ccl")}')
    S('bs_ap', '  Accounts payable', 'line', 'm1', data='bs_ap', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_ap")}')
    S('bs_accr', '  Accrued expenses and other liabilities', 'line', 'm1', data='bs_accr', bs=True,
      fc=lambda: f'={V("wc_rev")}*{V("wc_accr")}')
    S('bs_defrev', '  Deferred revenue', 'line', 'm1', data='bs_defrev', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_def")}')
    S('bs_std', '  Short-term debt (current portion of notes; lease financing to 2010)', 'line', 'm1', data='bs_std', bs=True, fc=lambda: f'={V("ds_rev")}+MIN({V("ds_notes")},{V("ds_mat")})')
    S('bs_ocl', '  Other current liabilities (derived)', 'line', 'm1', data='bs_ocl', bs=True, e26=lambda: f'={B1("bs_ocl")}', ae=lambda: f'={P("bs_ocl")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ccl")}),SUM({V("bs_ccl")}:{V("bs_ocl")}),"")')
    S('bs_nccl', '  Non-current content liabilities', 'line', 'm1', data='bs_nccl', bs=True, e26=lambda: f'={B1("bs_nccl")}', ae=lambda: f'={P("bs_nccl")}')
    S('bs_ltd', '  Long-term debt', 'line', 'm1', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_std")}')
    S('bs_oncl', '  Other non-current liabilities (incl. leases, deferred taxes; derived)', 'line', 'm1', data='bs_oncl', bs=True,
      e26=lambda: f'={B1("bs_oncl")}+({V("cf_def")}-{ACT("cf_def")})', ae=lambda: f'={P("bs_oncl")}+{V("cf_def")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ccl")}),{V("bs_tcl")}+SUM({V("bs_nccl")}:{V("bs_oncl")}),"")')
    S('bs_eq', "Total stockholders' equity", 'line', 'm1', data='bs_eq', bs=True,
      e26=lambda: (f'={B1("bs_eq")}+{H2("is_ni")}+({V("cf_bb")}-{ACT("cf_bb")})+{H2("is_sbc")}+({V("cf_stock")}-{ACT("cf_stock")})'),
      ae=lambda: f'={P("bs_eq")}+{V("is_ni")}+{V("cf_bb")}+{V("cf_sbc")}+{V("cf_stock")}',
      note='+ net income − repurchases + stock-based compensation + stock issued (OCI held flat; no dividends).')
    S('bs_tle', "TOTAL LIABILITIES AND STOCKHOLDERS' EQUITY", 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_eq")},"")')
    S('bs_nci', '  Noncontrolling interests (none)', 'line', 'm1', e26=lambda: '=0', ae=lambda: '=0')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=0.15,0,ROUND({V("bs_ta")}-{V("bs_tle")},1)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=0.15,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},1)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm1', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash + restricted cash vs cash-flow ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}+N({V("cf_restr")})-{V("cf_end")})<=0.15,0,ROUND({V("bs_cash")}+N({V("cf_restr")})-{V("cf_end")},1)),"")')
    S('bs_shares', '  Memo: shares outstanding at period end (m; XBRL, split-adjusted)', 'memo', 'm1', data='bs_shares', bs=True, e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL, CONTENT INVESTMENT & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input; year-end ratios)')
    S('wc_rev', '  Revenue — annualised (quarters × 4)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_oca', '  Other current assets % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_oca")}/{V("wc_rev")},"")', e26_in=V0['wc']['oca'], ae_in=V0['wc']['oca'])
    S('wc_ap', '  Accounts payable % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_rev")},"")', e26_in=V0['wc']['ap'], ae_in=V0['wc']['ap'])
    S('wc_accr', '  Accrued expenses & other liabilities % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_accr")}/{V("wc_rev")},"")',
      e26_in=V0['wc']['accr'], ae_in=V0['wc']['accr'])
    S('wc_def', '  Deferred revenue % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_defrev")}/{V("wc_rev")},"")', e26_in=V0['wc']['def'], ae_in=V0['wc']['def'],
      note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (other current assets − payables − accrued − deferred revenue − other current liabilities)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_oca")}),{V("bs_oca")}-{V("bs_ap")}-{V("bs_accr")}-{V("bs_defrev")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_cnet', '  Net content assets (content assets − content liabilities)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_cont")}),{V("bs_cont")}+N({V("bs_ccont")})-{V("bs_ccl")}-{V("bs_nccl")},"")')
    S('wc_cyrs', '  Content assets / annualised content amortization (years)', 'line', 'x2',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cont")}),ISNUMBER({V("d_camort")})),IFERROR(({V("bs_cont")}+N({V("bs_ccont")}))/({V("d_camort")}*{4 if CTX.col.q else 1}),""),"")')
    S('wc_cash_m', '  Cash and short-term investments in months of revenue', 'line', 'x2',
      all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),IFERROR(({V("bs_cash")}+N({V("bs_sti")}))/({V("wc_rev")}/12),""),"")')
    S('wc_dnwc', '  Δ(NWC + net content assets) y/y (investment; DCF working-capital line)', 'line', 'm1',
      all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}+{V("wc_cnet")}-{P("wc_nwc")}-{P("wc_cnet")},"")' if CTX.col.prior else None))
    S('wc_cf', '  Content & working-capital cash flow (cash-flow statement: content additions + liabilities + amortization + other operating)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_cadd")}),{V("cf_cadd")}+{V("cf_cliab")}+{V("cf_camort")}+{V("cf_oop")}+N({V("cf_dvd")}),"")',
      note='DCF row "Δ working capital": cash content spend in excess of amortization + other operating items (negative = investment).')
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; options & RSUs)', 'sched', 'm1', ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.08)
    S('ds_h', 'Debt schedule (senior notes repaid at maturity and refinanced; $3bn revolver drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (short-term + long-term debt)', 'sched', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_rev")}', note=MAN['debt']['at_2026_06_30'])
    S('ds_notes', '  Senior notes (carrying amount)', 'sched', 'm1', data='debt_tot',
      e26=lambda: f'={B1("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_repay', '  Notes repaid at maturity (input, par)', 'sched', 'm1', e26_in=V0['repay'][FYC], ae_in={y: V0['repay'][y] for y in range(FYC + 1, FYL + 1)}, note=V0['repay_note'])
    S('ds_iss', '  New notes issued (2026E actual; 2027E+ = maturities × refinancing %)', 'sched', 'm1', e26_in=V0['iss_2026'],
      ae=lambda: f'={V("ds_repay")}*{V("ds_refi")}', note=MAN['debt']['new_notes'])
    S('ds_refi', '  Refinancing % of maturities (assumption)', 'sched', 'pct', ae_in=1.0,
      note='Netflix plans to refinance the 2026 maturity (Q2-26 letter) and targets a solid investment-grade rating; 100% refinancing assumed.')
    S('ds_mat', '  Maturities in the following year (current portion, par)', 'sched', 'm1', e26_in=V0['mat'][FYC], ae_in={y: V0['mat'][y] for y in range(FYC + 1, FYL + 1)})
    S('ds_min', '  Minimum cash balance (cash-flow basis)', 'sched', 'm1', e26_in=V0['min_cash'], ae_in=V0['min_cash'])
    S('ds_rev', '  Revolving credit facility (year end)', 'sched', 'm1', e26=lambda: f'=MAX(0,{V("ds_min")}-({V("cr_avail")}-{V("cr_bb")}))',
      ae=lambda: f'=MAX(0,{V("ds_min")}-({V("cr_avail")}-{V("cr_bb")}))',
      note='$3bn revolver (Apr-2024, matures Apr-2029), undrawn at 30-Jun-2026. Drawn only if cash before draws falls below the minimum; repaid first from surplus cash.')
    S('ds_head', '  Memo: revolver headroom vs the $3.0bn commitment (negative = would need other financing)', 'memo_calc', 'm1',
      e26=lambda: f'=3000-{V("ds_rev")}', ae=lambda: f'=3000-{V("ds_rev")}')
    S('ds_net', '  Net debt issuance / (repayment)', 'sched', 'm1', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on opening notes %', 'sched', 'pct', ae_in=V0['r_notes'], note=V0['r_notes_note'])
    S('ds_r_rev', '  Interest rate on opening revolver %', 'sched', 'pct', ae_in=0.055, note='Adjusted term SOFR + 0.75–1.25% (credit-rating grid).')
    S('ds_fees', '  Commitment fees & financing-cost amortization ($m)', 'sched', 'm1', ae_in=15.0)
    S('ds_r_cash', '  Interest and other income yield on opening cash & investments %', 'sched', 'pct', ae_in=V0['r_cash'], note=V0['r_cash_note'])
    S('cr_h', 'Cash-return buybacks (repurchases return cash above the target year-end balance)', 'sub', 'gen')
    S('cr_tgt_m', '  Target year-end cash (months of revenue, scenario)', 'sched', 'x2', fc=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('cr_tgt', '  Target year-end cash (cash-flow basis)', 'sched', 'm1', fc=lambda: f'=MAX({V("ds_min")},{V("cr_tgt_m")}*{V("is_rev")}/12)')
    S('cr_avail', '  Cash available before buybacks and revolver (after notes issued / repaid and repaying the opening revolver)', 'sched', 'm1',
      e26=lambda: (f'={B1("cf_end")}+({V("cf_cfo")}-{ACT("cf_cfo")})+({V("cf_cfi")}-{ACT("cf_cfi")})+({V("cf_stock")}-{ACT("cf_stock")})+({V("cf_ofin")}-{ACT("cf_ofin")})'
                   f'+({V("cf_fx")}-{ACT("cf_fx")})+{V("ds_iss")}-{V("ds_repay")}-{B1("ds_rev")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_stock")}+{V("cf_ofin")}+{V("cf_fx")}+{V("ds_iss")}-{V("ds_repay")}-{P("ds_rev")}')
    S('cr_bb', '  Share repurchases: plug to the target cash balance (2026E = 2H)', 'sched', 'm1', fc=lambda: f'=MAX(0,{V("cr_avail")}-{V("cr_tgt")})',
      note='Surplus cash above the target is returned via buybacks; feeds the cash-flow repurchase line. Check against the $27.1bn authorization remaining at 30-Jun-2026.')
    S('cr_auth', '  Memo: cumulative buybacks from 2H-26 vs the $27.1bn authorization remaining at 30-Jun-2026 (headroom)', 'memo_calc', 'm1',
      e26=lambda: f'=27100-{V("cr_bb")}', ae=lambda: f'={P("cr_auth")}-{V("cr_bb")}')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_int', '  Interest expense ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    S('hr_yield', '  Interest and other income ÷ opening cash & investments %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_oth")}*{4 if CTX.col.q else 1}/({(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["bs_cash"]}+N({(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["bs_sti"]})),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted EBIT, full-cost: after content amortization, D&A and SBC)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT, full-cost (= adjusted operating income)', 'line', 'm1', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate', 'line', 'pct', ann=True, all=lambda: f'=MAX(0.1,MIN(0.35,IFERROR({V("is_etr")}+0,0.17)))')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity', 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − cash − short-term investments', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")}-N({V("bs_sti")}),"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Revenue', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Revenue / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm1', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangibles (inside other non-current assets; not split out — 0)', 'line', 'm1', ann=True, all=lambda: '=0')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. short-term debt)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})),"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income', 'line', 'm1', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Stockholders' equity", 'line', 'm1', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash − short-term investments', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA (company definition)', 'line', 'm1', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_gx', 'Gross debt / adjusted EBITDA (x)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("ds_total")}/{V("r_adj")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+({Q2}{R["sh_dil"]}-{Q2}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interests (USDm)', 'line', 'm', e26=lambda: f'={V("bs_nci")}', ae=lambda: f'={V("bs_nci")}')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Revenue', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Operating income', lambda: f'=IFERROR({V("v_ev")}/{V("is_oi")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield (no dividend)', lambda: '=0')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
