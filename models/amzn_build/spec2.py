"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, B1, A

def build_spec2(V0):
    S = add
    def H2(key): return f'({Q3E}{R[key]}+{Q4E}{R[key]})'      # 2H/26E (Q3E + Q4E)
    def e26f(key, src):                                       # FY2026E flow = 1H actual + 2H estimate
        return lambda: f'={ACT(key)}+{H2(src)}'
    def X2(key): return f'({V(key)}-{ACT(key)})'               # 2H/26E part of a 2026E cash-flow line
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 1H-26 actual + Q3/Q4 estimates; quarters = discrete three-month columns as published)')
    S('cf_ni', 'Net income', 'line', 'm', data='cf_ni', flow=True, e26=e26f('cf_ni', 'is_ni'), ae=lambda: f'={V("is_ni")}')
    S('cf_adj', 'Adjustments to reconcile net income to operating cash flow:', 'sub', 'gen')
    S('cf_dda', '  Depreciation & amortization (P&E, capitalized content, operating-lease assets, other)', 'line', 'm', data='cf_dda', flow=True,
      e26=e26f('cf_dda', 'd_dda'), ae=lambda: f'={V("d_dda")}')
    S('cf_sbc', '  Stock-based compensation', 'line', 'm', data='cf_sbc', flow=True, e26=e26f('cf_sbc', 'd_sbc'), ae=lambda: f'={V("d_sbc")}')
    S('cf_def', '  Deferred income taxes', 'line', 'm', data='cf_def', flow=True, e26=lambda: f'={ACT("cf_def")}+{PT("pt_def")}', ae_in=V0['def_ae'],
      note='2H-26E and 2027E+ inputs (assumption: 100% bonus depreciation made permanent in 2025 keeps deferred taxes positive).')
    S('cf_othnc', '  Non-operating (income) expense, other operating expense & other non-cash items (derived)', 'line', 'm', data='cf_othnc', flow=True,
      e26=lambda: f'={ACT("cf_othnc")}', ae_in=0.0, note='History: CFO − net income − D&A − SBC − deferred taxes − working-capital lines (mainly reverses investment marks in other income).')
    S('cf_oda', '  Operating-lease payments & content / other asset reinvestment (offsets other D&A; forecast)', 'line', 'm', e26=lambda: f'=-{H2("d_oda")}',
      ae=lambda: f'=-{V("d_oda")}',
      note='Forecast assumption: operating-lease liability payments and capitalized-content spending ≈ the non-P&E amortization in D&A, so operating-lease assets / liabilities and other assets are held flat (in the history these flows sit in the working-capital lines).')
    S('cf_wc', '  Changes in operating assets & liabilities (inventories, receivables, payables, accrued, unearned revenue)', 'line', 'm', data='cf_wc', flow=True,
      e26=lambda: (f'={ACT("cf_wc")}-({V("bs_ar")}-{B1("bs_ar")})-({V("bs_inv")}-{B1("bs_inv")})-({V("bs_oca")}-{B1("bs_oca")})'
                   f'+({V("bs_ap")}-{B1("bs_ap")})+({V("bs_accr")}-{B1("bs_accr")})+({V("bs_unearned")}-{B1("bs_unearned")})'),
      ae=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_inv")}-{P("bs_inv")})-({V("bs_oca")}-{P("bs_oca")})'
                  f'+({V("bs_ap")}-{P("bs_ap")})+({V("bs_accr")}-{P("bs_accr")})+({V("bs_unearned")}-{P("bs_unearned")})'),
      note='Forecast linked to the balance sheet (year-end working-capital days).')
    S('cf_cfo', 'Net cash provided by (used in) operating activities', 'line_b', 'm', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Purchases of property and equipment', 'line', 'm', data='cf_capex', flow=True,
      e26=lambda: f'={ACT("cf_capex")}-{H2("d_capex_q")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='Q4-15–Q3-17 releases showed purchases net of proceeds and incentives (proceeds line from Q4-17). 2026E: 1H actual + Q3/Q4 point estimates. 2027E+: net sales × capex % (scenario lever).')
    S('cf_capex_proc', 'Proceeds from property and equipment sales and incentives', 'line', 'm', data='cf_capex_proc', flow=True,
      e26=lambda: f'={ACT("cf_capex_proc")}+{H2("d_capex_q")}*{PT("pt_proc")}', ae=lambda: f'=-{V("cf_capex")}*{V("proc_pct")}')
    S('cf_acq', 'Acquisitions, net of cash acquired, non-marketable investments, and other', 'line', 'm', data='cf_acq', flow=True,
      e26=lambda: f'={ACT("cf_acq")}', ae=lambda: f'=-{V("m_spend")}', note='Includes strategic investments (e.g. Anthropic). 2027E+: M&A lever.')
    S('cf_sec', 'Sales and maturities, net of purchases, of marketable securities', 'line', 'm', data='cf_sec', flow=True, e26=lambda: f'={ACT("cf_sec")}', ae_in=0.0)
    S('cf_oinv', 'Other investing activities (derived)', 'line', 'm', data='cf_oinv', flow=True, e26=lambda: f'={ACT("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Net cash provided by (used in) investing activities', 'line_b', 'm', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_bb', 'Common stock repurchased', 'line', 'm', data='cf_bb', flow=True, e26=lambda: f'={ACT("cf_bb")}', ae=lambda: f'=-{V("lev_bb")}',
      note='No repurchases since 2022 ($10bn authorization of Mar-2022, $6bn used). 2027E+ = leverage plug (surplus cash returned once net debt / adjusted EBITDA is below the scenario target).')
    S('cf_debt', 'Proceeds from (repayments of) short- and long-term debt, net', 'line', 'm', data='cf_debt', flow=True,
      e26=lambda: f'={ACT("cf_debt")}+{V("ds_total")}-{B1("ds_total")}', ae=lambda: f'={V("ds_net")}',
      note='Includes capital-lease repayments until Q3-14 (combined line). Forecast per the debt schedule.')
    S('cf_lease', 'Principal repayments of finance leases and financing obligations', 'line', 'm', data='cf_lease', flow=True,
      e26=lambda: f'={ACT("cf_lease")}+{PT("pt_lease")}', ae_in=V0['lease_ae'])
    S('cf_ofin', 'Other financing activities (stock-plan proceeds, excess tax benefits; derived)', 'line', 'm', data='cf_ofin', flow=True, e26=lambda: f'={ACT("cf_ofin")}', ae_in=0.0)
    S('cf_cff', 'Net cash provided by (used in) financing activities', 'line_b', 'm', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_bb")}:{V("cf_ofin")})')
    S('cf_fx', 'Foreign currency effect on cash, cash equivalents, and restricted cash', 'line', 'm', data='cf_fx', flow=True, e26=lambda: f'={ACT("cf_fx")}', ae_in=0.0)
    S('cf_net', 'Net increase (decrease) in cash, cash equivalents, and restricted cash', 'line', 'm', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")}),"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}')
    S('cf_beg', 'Cash, cash equivalents and restricted cash — beginning of period (restricted cash included from 2018)', 'line', 'm', data='cf_beg',
      e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash, cash equivalents and restricted cash — end of period', 'line_b', 'm', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: beginning cash + net change = ending cash (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=1.01,0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},0)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")})<=1.01,0,ROUND(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")},0)),"")')
    S('cf_restr', '  Memo: restricted cash (cash-flow cash − balance-sheet cash; from 2018)', 'memo', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("cf_end")}),ISNUMBER({V("bs_cash")})),{V("cf_end")}-{V("bs_cash")},"")',
      e26=lambda: f'={B1("cf_restr")}', ae=lambda: f'={P("cf_restr")}')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (company definition: operating cash flow − purchases of P&E net of proceeds from sales and incentives)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")}+N({V("cf_capex_proc")}),"")')
    def ttm(key):
        def f():
            c = CTX.col
            if not c.q: return f'={V(key)}'
            cs = [c.c]; cc = c
            for _ in range(3):
                if not cc.prevq: return None
                cs.append(cc.prevq); cc = COLMAP[cc.prevq]
            return f'=IF(AND({",".join(f"ISNUMBER({x}{R[key]})" for x in cs)}),{"+".join(f"{x}{R[key]}" for x in cs)},"")'
        return f
    S('fcf_ttm', '  Free cash flow — trailing twelve months (quarters: Σ four quarters as originally reported; FY = year)', 'line', 'm', hist=ttm('fcf'))
    S('fcf_basis', '  Basis difference: prior-year quarters restated in the release (ASU 2016-09 in 2017; ASU 2016-15 / 2016-18 in 2018)', 'line', 'm', data='fcf_basis',
      labkey='fcf_basis_note')
    S('fcf_pub', '  Company-published free cash flow — TTM', 'memo', 'm', data='fcf_ttm')
    S('fcf_chk', '  Check: model TTM + basis difference vs company-published (should be 0; ±3 rounding)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("fcf_pub")}),ISNUMBER({V("fcf_ttm")})),IF(ABS({V("fcf_ttm")}+N({V("fcf_basis")})-{V("fcf_pub")})<=3.01,0,ROUND({V("fcf_ttm")}+N({V("fcf_basis")})-{V("fcf_pub")},0)),"n/p")')
    S('fcf_l', 'FCF less principal repayments of finance leases and financing obligations (company definition, published Q4-14–Q4-24)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("fcf")}),{V("fcf")}+N({V("cf_lease")}),"")')
    S('fcf_l_ttm', '  FCF less lease principal — TTM (from Q3-15, when four quarters show lease principal separately)', 'line', 'm',
      hist=lambda: (ttm('fcf_l')() if (CTX.col.year, CTX.col.q or 4) >= (2015, 3) else None))
    S('fcf_l_basis', '  Basis difference: prior-year quarters restated in the release', 'line', 'm', data='fcf_lease_basis')
    S('fcf_l_pub', '  Company-published FCF less principal repayments of finance leases and financing obligations — TTM', 'memo', 'm', data='fcf_lease_ttm')
    S('fcf_l_chk', '  Check: model vs company-published (should be 0; ±3 rounding)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("fcf_l_pub")}),ISNUMBER({V("fcf_l_ttm")})),IF(ABS({V("fcf_l_ttm")}+N({V("fcf_l_basis")})-{V("fcf_l_pub")})<=3.01,0,ROUND({V("fcf_l_ttm")}+N({V("fcf_l_basis")})-{V("fcf_l_pub")},0)),"n/p")')
    S('fcf_eq_pub', '  Memo: FCF less equipment finance leases and principal repayments of all other finance leases and financing obligations — TTM, as published (Q4-14–Q4-24)', 'memo', 'm',
      data='fcf_eq_ttm')
    S('fcf_def', '  Definition / basis', 'text', 'gen')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of net sales', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Gross capex % of net sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae=lambda: '=' + CH(SC['CAPEX'][CTX.col.year]), note='2027E+: scenario lever (AI / data-centre build-out; 2025 18.4%, 1H-26 25.8%).')
    S('proc_pct', '  Proceeds from P&E sales and incentives % of gross capex', 'pct', 'pct',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_capex")}),ISNUMBER({V("cf_capex_proc")})),IFERROR(-{V("cf_capex_proc")}/{V("cf_capex")},""),"")', ae_in=V0['proc_pct'])
    S('capex_dep', '  Gross capex / P&E depreciation (x)', 'line', 'x2', all=lambda: f'=IF(AND(ISNUMBER({V("cf_capex")}),ISNUMBER({V("d_dep")})),IFERROR(-{V("cf_capex")}/{V("d_dep")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E = 2H from shares outstanding at 30-Jun-2026; 2027E+ buybacks via the leverage plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = 2H)', 'line', 'm', e26=lambda: f'=-{X2("cf_bb")}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans (m)', 'driver', 'm2', e26=lambda: f'=2*{PT("pt_iss_q")}', ae_in=V0['iss_ae'])
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from common shares outstanding at 30-Jun-2026 (Q2-26 release).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since 2H-26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET (condensed, as in the releases)', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Jun-2026 balance sheet + 2H flows; 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}-{V("cf_restr")}')
    S('bs_msec', '  Marketable securities', 'line', 'm', data='bs_msec', bs=True, e26=lambda: f'={B1("bs_msec")}', ae=lambda: f'={P("bs_msec")}',
      note='Held flat (counted with cash in net debt).')
    S('bs_inv', '  Inventories', 'line', 'm', data='bs_inv', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dio")}/365')
    S('bs_ar', '  Accounts receivable, net and other', 'line', 'm', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_oca', '  Other current assets (current deferred tax assets to 2015)', 'line', 'm', data='bs_oca', bs=True, e26=lambda: f'={B1("bs_oca")}', ae=lambda: f'={P("bs_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_ppe', '  Property and equipment, net (incl. finance-lease assets)', 'line', 'm', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-{X2("cf_capex")}-{X2("cf_capex_proc")}+{X2("ds_fladd")}-{H2("d_dep")}',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("cf_capex_proc")}+{V("ds_fladd")}-{V("d_dep")}',
      note='Roll-forward: prior + gross capex − proceeds + finance-lease additions (non-cash) − P&E depreciation.')
    S('bs_oplease', '  Operating leases (right-of-use assets; from 2019)', 'line', 'm', data='bs_oplease', bs=True, e26=lambda: f'={B1("bs_oplease")}', ae=lambda: f'={P("bs_oplease")}',
      note='Held flat (new leases ≈ amortization; see the cash-flow offset line).')
    S('bs_gw', '  Goodwill', 'line', 'm', data='bs_gw', bs=True, e26=lambda: f'={B1("bs_gw")}', ae=lambda: f'={P("bs_gw")}+{V("m_spend")}*{V("m_acqp")}*(1-{V("m_intp")})')
    S('bs_onca', '  Other assets (non-marketable investments incl. Anthropic, video & music content, intangibles, deferred tax; derived)', 'line', 'm', data='bs_onca', bs=True,
      e26=lambda: f'={B1("bs_onca")}', ae=lambda: f'={P("bs_onca")}+{V("m_spend")}*(1-{V("m_acqp")})+{V("m_spend")}*{V("m_acqp")}*{V("m_intp")}',
      note='Held flat apart from strategic investments and acquired intangibles (M&A lever); their amortization is inside other D&A.')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_ppe")}:{V("bs_onca")}),"")')
    S('bs_l', "LIABILITIES AND STOCKHOLDERS' EQUITY", 'sub', 'gen')
    S('bs_ap', '  Accounts payable', 'line', 'm', data='bs_ap', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dpo")}/365')
    S('bs_accr', '  Accrued expenses and other (excl. debt)', 'line', 'm', data='bs_accr_x', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_accr")}',
      note='As presented less the current portion of long-term debt and short-term borrowings (XBRL), shown on the next line.')
    S('bs_std', '  Current portion of long-term debt & short-term borrowings (inside "accrued expenses and other" as presented)', 'line', 'm', data='bs_std', bs=True,
      fc=lambda: f'={V("ds_st")}+{V("ds_mat")}', note='Current portion of LTD from 2011 and short-term borrowings from 2021 (XBRL); earlier not disclosed (included in accrued).')
    S('bs_unearned', '  Unearned revenue (separate from Q4-13)', 'line', 'm', data='bs_unearned', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_unearned")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_ap")}:{V("bs_unearned")}),"")')
    S('bs_ltlease', '  Long-term lease liabilities (operating + finance; from 2019)', 'line', 'm', data='bs_ltlease', bs=True,
      e26=lambda: f'={B1("bs_ltlease")}+{X2("ds_fladd")}+{X2("cf_lease")}', ae=lambda: f'={P("bs_ltlease")}+{V("ds_fladd")}+{V("cf_lease")}',
      note='Forecast: + finance-lease additions − principal repayments (operating-lease liabilities held flat).')
    S('bs_ltd', '  Long-term debt', 'line', 'm', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_notes")}-{V("ds_mat")}')
    S('bs_oltl', '  Other long-term liabilities (deferred taxes, tax contingencies, capital / finance leases before 2019; derived)', 'line', 'm', data='bs_oltl', bs=True,
      e26=lambda: f'={B1("bs_oltl")}+{X2("cf_def")}', ae=lambda: f'={P("bs_oltl")}+{V("cf_def")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ltlease")}:{V("bs_oltl")}),"")')
    S('bs_eq', "  Total stockholders' equity", 'line', 'm', data='bs_eq', bs=True,
      e26=lambda: f'={B1("bs_eq")}+{H2("is_ni")}+{H2("d_sbc")}+{X2("cf_bb")}+{X2("cf_ofin")}',
      ae=lambda: f'={P("bs_eq")}+{V("is_ni")}+{V("cf_sbc")}+{V("cf_bb")}+{V("cf_ofin")}',
      note='+ net income + stock-based compensation − repurchases + other financing (OCI held flat). Amazon pays no dividend.')
    S('bs_nci', '  Noncontrolling interests — none', 'line', 'm', e26=lambda: '=0', ae=lambda: '=0')
    S('bs_tle', "TOTAL LIABILITIES AND STOCKHOLDERS' EQUITY", 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_eq")}+N({V("bs_nci")}),"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=1.01,0,ROUND({V("bs_ta")}-{V("bs_tle")},0)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=1.01,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},0)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash vs cash-flow ending cash (should be 0; to 2017 — from 2018 the cash-flow statement includes restricted cash, memo above)', 'check', 'm',
      hist=lambda: (f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}-{V("cf_end")})<=1.01,0,ROUND({V("bs_cash")}-{V("cf_end")},0)),"")'
                    if CTX.col.year < 2018 else None),
      fc=lambda: f'=ROUND({V("bs_cash")}+{V("cf_restr")}-{V("cf_end")},0)')
    S('bs_shares', '  Memo: common shares outstanding at period end (m; split-adjusted)', 'memo', 'm', data='bs_shares', bs=True,
      e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input; year-end levels)')
    S('wc_rev', '  Net sales — annualised (quarters × 4)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{QF()},"")')
    S('wc_cogs', '  Cost of sales — annualised', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_cogs")}*{QF()},"")')
    S('wc_dso', '  Receivable days — receivables / net sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_dio', '  Inventory days — inventories / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_inv")}/{V("wc_cogs")}*365,"")', e26_in=V0['wc']['dio'], ae_in=V0['wc']['dio'])
    S('wc_dpo', '  Payable days — payables / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_cogs")}*365,"")', e26_in=V0['wc']['dpo'], ae_in=V0['wc']['dpo'])
    S('wc_accr', '  Accrued expenses and other (excl. debt) % of net sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_accr")}/{V("wc_rev")},"")', e26_in=V0['wc']['accr'], ae_in=V0['wc']['accr'])
    S('wc_unearned', '  Unearned revenue % of net sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_unearned")}/{V("wc_rev")},"")', e26_in=V0['wc']['unearned'],
      ae_in=V0['wc']['unearned'], note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables + inventories + other current assets − payables − accrued excl. debt − unearned revenue)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_inv")}+N({V("bs_oca")})-{V("bs_ap")}-{V("bs_accr")}-N({V("bs_unearned")}),"")')
    S('wc_nwc_p', '  NWC % of net sales (negative = suppliers fund the business)', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_ccc', '  Cash conversion cycle (inventory days + receivable days − payable days)', 'line', 'd',
      all=lambda: f'=IFERROR({V("wc_dio")}+{V("wc_dso")}-{V("wc_dpo")},"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; restricted stock units)', 'sched', 'm', ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.08)
    S('ds_h', 'Debt schedule (senior notes repaid at maturity and refinanced; commercial paper / revolver drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (senior notes & other LTD incl. current portion + short-term borrowings; carrying value)', 'sched', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("ds_notes")}),{V("ds_notes")}+N({V("ds_st")}),"")', fc=lambda: f'={V("ds_notes")}+{V("ds_st")}', note=MAN['debt']['source_q2'])
    S('ds_notes', '  Senior notes & other long-term debt, incl. current portion', 'sched', 'm', data='debt_notes',
      e26=lambda: f'={B1("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_iss', '  New notes issued (input)', 'sched', 'm', e26_in=V0['iss_notes'][FYC], ae_in={y: V0['iss_notes'][y] for y in range(FYC + 1, FYL + 1)},
      note=MAN['debt']['post_q2_issues']['src'] + ' GBP at an assumed 1.35 USD/GBP. 2027E+: maturities refinanced with new notes (assumption).')
    S('ds_repay', '  Notes repaid at maturity (input)', 'sched', 'm', e26_in=V0['repay'][FYC], ae_in={y: V0['repay'][y] for y in range(FYC + 1, FYL + 1)}, note=V0['repay_note'])
    S('ds_mat', '  Maturities in the following year (current portion)', 'sched', 'm', e26_in=V0['mat'][FYC], ae_in={y: V0['mat'][y] for y in range(FYC + 1, FYL + 1)})
    S('ds_fladd', '  Property and equipment acquired under finance leases (non-cash; supplemental cash-flow information)', 'sched', 'm', data='fl_add', flow=True,
      e26=lambda: f'={ACT("ds_fladd")}+{PT("pt_fladd")}', ae_in=V0['fladd_ae'])
    S('ds_pre', '  Cash before commercial-paper / revolver draws or repayments (opening cash + CFO + CFI + repurchases, lease principal, other financing + FX − notes repaid + issued)', 'sched', 'm',
      e26=lambda: (f'={B1("bs_cash")}+{X2("cf_cfo")}+{X2("cf_cfi")}+{X2("cf_bb")}+{X2("cf_lease")}+{X2("cf_ofin")}+{X2("cf_fx")}-{V("ds_repay")}+{V("ds_iss")}'),
      ae=lambda: f'={P("bs_cash")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_bb")}+{V("cf_lease")}+{V("cf_ofin")}+{V("cf_fx")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_min', '  Minimum cash balance (cash and cash equivalents)', 'sched', 'm', e26_in=V0['min_cash'], ae_in=V0['min_cash'])
    S('ds_st', '  Commercial paper / revolver / short-term borrowings (year end)', 'sched', 'm', data='debt_st',
      e26=lambda: f'=MAX(0,{B1("ds_st")}+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_st")}+{V("ds_min")}-{V("ds_pre")})',
      note=MAN['debt']['facilities'] + ' Shortfalls below the minimum cash balance are drawn; surplus repays. ' + MAN['debt']['ddtl'])
    S('ds_head', '  Memo: headroom vs $30bn CP programs + $20bn revolving facilities (negative = would need other financing)', 'memo_calc', 'm',
      e26=lambda: f'=50000-{V("ds_st")}', ae=lambda: f'=50000-{V("ds_st")}')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on opening notes %', 'sched', 'pct', ae_in=V0['r_notes'], note=V0['r_notes_note'])
    S('ds_r_st', '  Interest rate on opening commercial paper / revolver %', 'sched', 'pct', ae_in=0.045, note='Assumption (CP ~SOFR; revolver benchmark + 0.45%).')
    S('ds_flint', '  Finance-lease & financing-obligation interest ($m)', 'sched', 'm', ae_in=V0['flint'], note='Cash paid for interest on finance leases $295m (2025); financing obligations ~$0.3bn (10-Q commitments).')
    S('ds_r_cash', '  Interest income yield on opening cash & marketable securities %', 'sched', 'pct', ae_in=V0['r_cash'], note=V0['r_cash_note'])
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / adjusted EBITDA, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end; debt − cash − marketable securities)', 'sched', 'm',
      ae=lambda: f'={P("ds_total")}-{P("bs_cash")}-{P("bs_msec")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_lease")}-{V("cf_ofin")}-{V("cf_fx")}')
    S('lev_tgt', '  Target net debt = target leverage × adjusted EBITDA', 'sched', 'm', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to target leverage', 'sched', 'm', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash beyond the leverage target is returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of net sales', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_int', '  Interest expense ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_intexp")}*{QF()}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    S('hr_fl', '  Memo: finance-lease liabilities (capital leases to 2018; XBRL; excluded from net debt)', 'memo', 'm', data='fl_tot', bs=True)
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted EBIT, full-cost)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT, full-cost (adjusted operating income)', 'line', 'm', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate (adjusted)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(MAX(0,MIN(0.4,{V("e_rate")}+0)),0.21)')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', "  Total stockholders' equity", 'line', 'm', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − cash − marketable securities', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")}-{V("bs_msec")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR(IF({V("ra_ic")}<=0,"n/m",{V("ra_nopat")}/{V("ra_ic")}),"n/a")',
      note='n/m where invested capital is negative (2006–11: net cash and negative working capital exceeded equity).')
    S('ra_mg', '  Margin = Adjusted EBIT / Net sales', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Net sales / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-{V("bs_gw")},"n/a")')
    S('rn_cash', '  − Cash and marketable securities', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-({V("bs_cash")}+{V("bs_msec")}),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. debt)', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})),"n/a")')
    S('rn_nta', '  = Net tangible operating assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR(IF({V("rn_nta")}<=0,"n/m",{V("rn_nopat")}/{V("rn_nta")}),"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income', 'line', 'm', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Stockholders' equity", 'line', 'm', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash − marketable securities', 'line', 'm', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA', 'line', 'm', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_gx', 'Total debt / adjusted EBITDA (x)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("ds_total")}/{V("r_adj")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm', e26=lambda: f'={V("bb_end")}+({Q2}{R["sh_dil"]}-{Q2}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm; finance leases excluded — their principal repayments are deducted in UFCF)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interests (USDm)', 'line', 'm', e26=lambda: f'={V("bs_nci")}', ae=lambda: f'={V("bs_nci")}')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_inv', '  Memo: non-marketable equity investments are not deducted (carried in other assets; Anthropic marks in other income)', 'text', 'gen')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Net sales', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted operating income', lambda: f'=IFERROR({V("v_ev")}/{V("o_adj")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS, model)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield (none)', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
