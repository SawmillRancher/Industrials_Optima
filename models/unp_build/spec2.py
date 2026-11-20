"""Row specification part 2: cash flow, share schedule, balance sheet (Union Pacific condensed presentation + Norfolk Southern
closing entries), working capital, schedules (PP&E, debt, leverage-targeted buybacks), ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, ACT0, QEc, B1, CB

NB = MAN['nsc_deal']['bs_2026_09_30']

def build_spec2(V0):
    S = add
    def e26f(key, q4):          # 2026E flow = 9M actual (Q1-Q3/26) + Q4/26E estimate
        return lambda: f'={ACT(key)}+{q4()}'
    def close_add(amount):      # amount added in the closing year only (toggle)
        return f'IF(AND(N({V("n_frac")})>0,N({P("n_frac")})=0),{CB("n_tog")}*({amount}),0)'
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS (condensed, as in the releases)', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 9M actual + Q4 estimate; quarters discrete, derived from the year-to-date statements)')
    S('cf_ni', 'Net income', 'line', 'm', data='cf_ni', flow=True, fc=lambda: f'={V("is_ni")}', e26=e26f('cf_ni', lambda: QEc('is_ni')))
    S('cf_dep', 'Depreciation', 'line', 'm', data='cf_dep', flow=True, fc=lambda: f'={V("is_dep")}', e26=e26f('cf_dep', lambda: QEc('is_dep')))
    S('cf_dtax', 'Deferred and other income taxes', 'line', 'm', data='cf_dtax', flow=True, e26=lambda: f'={ACT("cf_dtax")}+{QEc("is_tax")}*{QEc("cf_dtax_p")}',
      ae=lambda: f'={V("is_tax")}*{V("cf_dtax_p")}', note='Forecast = deferred share of the tax expense (input). 2025: $207m of $2,028m (10%); 2024: $172m... see ratio row.')
    S('cf_dtax_p', '  Deferred share of income tax expense % (input)', 'pct', 'pct', all=ratio('cf_dtax', 'is_tax'), qe_in=V0['dtax_p'], ae_in=V0['dtax_p'])
    S('cf_oth', 'Other – net (working capital, share-based compensation, pension, gains; derived)', 'line', 'm', data='cf_oth', flow=True,
      e26=lambda: f'={ACT("cf_oth")}+{QEc("is_sbc")}-({V("bs_oca")}-{B1("bs_oca")})+({V("bs_ocl")}-{B1("bs_ocl")})-{V0["inv_q4"]}',
      ae=lambda: f'={V("is_sbc")}-({V("bs_oca")}-{P("bs_oca")}-{V("nsc_oca_add")})+({V("bs_ocl")}-{P("bs_ocl")}-{V("nsc_ocl_add")})-{V0["inv_ae"]}+N({V("nc_noncash")})',
      note=('History: cash from operations − net income − depreciation − deferred taxes. Forecast: share-based compensation − Δ other current assets + Δ other current liabilities '
            '(acquired NSC balances excluded) − undistributed equity income retained in investments.'))
    S('cf_cfo', 'Cash provided by operating activities', 'line_b', 'm', data='cf_cfo', flow=True, fc=lambda: f'={V("cf_ni")}+{V("cf_dep")}+{V("cf_dtax")}+{V("cf_oth")}')
    S('cf_capex', 'Capital investments', 'line', 'm', data='cf_capex', flow=True, e26=lambda: f'=-{PT("pt_capex")}',
      ae=lambda: f'=-({V("t_rev")}*{V("capex_pct")}+N({V("nc_rev")})*{V("nsc_capex_p")}+N({V("sy_capex")}))',
      note='2026E: capital plan $3.5bn (incl. locomotive / freight car lease buyouts). 2027E+: standalone revenues × capex % + NSC revenues × NSC capex % + capex to achieve synergies.')
    S('nsc_capex_p', '  NSC capital expenditures % of NSC revenues (input)', 'driver', 'pct', ae_in=0.19, note='NSC 2025 property additions $2,204m on $12,180m revenues (18%); 9M-26 $1,407m.')
    S('cf_acq', 'Acquisition of Norfolk Southern — cash consideration and debt issuance costs, net of cash acquired', 'line', 'm', e26_in=0.0,
      ae=lambda: '=-' + close_add(f'{CB("nd_cash")}+{CB("nd_fees")}-{V("nsc_cash_add")}'))
    S('cf_sti', 'Purchases / maturities of short-term investments, net', 'line', 'm', data='cf_sti', flow=True, e26=lambda: f'={ACT("cf_sti")}-({V("bs_sti")}-{B1("bs_sti")})',
      ae=lambda: f'=-({V("bs_sti")}-{P("bs_sti")})', note='Short-term investments (time deposits, agency securities) accumulated for the merger cash consideration; liquidated at closing.')
    S('cf_oinv', 'Other – net (investing; derived)', 'line', 'm', data='cf_oinv', flow=True, e26=lambda: f'={ACT("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Cash used in investing activities', 'line_b', 'm', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_bb', 'Share repurchase programs', 'line', 'm', data='cf_bb', flow=True, e26=lambda: f'={ACT("cf_bb")}-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='Paused for the Norfolk Southern merger (9M-26 $26m = settlements). 2027E+ = leverage plug (resumes once net debt / adjusted EBITDA is below the target).')
    S('cf_div', 'Dividends paid', 'line', 'm', data='cf_div', flow=True, e26=lambda: f'={ACT("cf_div")}-{QEc("dps")}*{QEc("sh_basic")}',
      ae=lambda: f'=-{V("dps")}*({V("bb_beg")}+N({V("nc_sh")}))', note='Dividends = DPS × beginning shares (+ deal shares weighted by days outstanding); avoids circularity with plug-driven buybacks.')
    S('cf_debt_iss', 'Debt issued (new notes; acquisition debt at closing)', 'line', 'm', data='cf_debt_iss', flow=True, e26=lambda: f'={ACT("cf_debt_iss")}+{QEc("ds_newnotes_q")}',
      ae=lambda: f'={V("ds_newnotes")}+' + close_add(f'{CB("nd_newdebt")}'))
    S('cf_debt_rep', 'Debt repaid (maturities; CP / revolver repayments)', 'line', 'm', data='cf_debt_rep', flow=True,
      e26=lambda: f'={ACT("cf_debt_rep")}-{QEc("ds_repay_q")}-MAX(0,{B1("ds_cp")}-{V("ds_cp")})', ae=lambda: f'=-{V("ds_repay")}-MAX(0,{P("ds_cp")}-{V("ds_cp")})')
    S('cf_cp', 'Commercial paper / revolver drawn (plug to minimum cash)', 'line', 'm', e26=lambda: f'=MAX(0,{V("ds_cp")}-{B1("ds_cp")})', ae=lambda: f'=MAX(0,{V("ds_cp")}-{P("ds_cp")})')
    S('cf_ofin', 'Other – net (financing; derived)', 'line', 'm', data='cf_ofin', flow=True, e26=lambda: f'={ACT("cf_ofin")}+{V0["ofin_q4"]}', ae_in=V0['ofin_ae'],
      note='Equity-plan proceeds net of withholding, debt issuance costs. Input.')
    S('cf_cff', 'Cash used in financing activities', 'line_b', 'm', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_bb")}:{V("cf_ofin")})')
    S('cf_net', 'Net change in cash, cash equivalents and restricted cash', 'line', 'm', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")},"")', fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}')
    S('cf_beg', 'Cash — beginning of period', 'line', 'm', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period (incl. restricted cash from 2018)', 'line_b', 'm', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: beginning cash + net change = ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=0.6,0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},1)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS({V("cf_ni")}+{V("cf_dep")}+{V("cf_dtax")}+{V("cf_oth")}-{V("cf_cfo")})<=0.6,0,ROUND({V("cf_ni")}+{V("cf_dep")}+{V("cf_dtax")}+{V("cf_oth")}-{V("cf_cfo")},1)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf_co', 'Free cash flow — company definition (cash from operations − cash used in investing − dividends paid)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_cfi")})),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_div")},"")')
    S('fcf_pub', '  Company-published free cash flow', 'memo', 'm', data='fcf_pub', flow=True)
    S('fcf_chk', '  Check: model vs company-published free cash flow (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("fcf_pub")}),IF(ABS({V("fcf_co")}-{V("fcf_pub")})<=0.6,0,ROUND({V("fcf_co")}-{V("fcf_pub")},1)),"n/p")')
    S('fcf', 'Free cash flow (model: cash from operations − capital investments)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")},"")')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of operating revenues', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capital investments % of operating revenues (standalone input 2027E+)', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note='2025 14.2% ($3,471m); 2026 plan $3.5bn (~13.5%). Input 13.5% of standalone revenues (assumption; "long-term ~15% of revenue" in prior Investor Day material, not on EDGAR).')
    S('capex_dep', '  Capital investments / depreciation (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_dep")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E from shares outstanding at 30-Sep-2026; 2027E+ buybacks via the leverage plug; NSC consideration shares added at closing')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = Q4)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans (m)', 'driver', 'm2', e26_in=V0['iss_q4'], ae_in=V0['iss_ae'])
    S('nd_sh_end', '  Shares issued for Norfolk Southern (m; closing year)', 'line', 'm2', e26_in=0.0, ae=lambda: '=' + close_add(f'{CB("nd_shares")}'))
    S('nd_sh_cum', '  Memo: cumulative shares issued for Norfolk Southern (m)', 'memo_calc', 'm2', e26_in=0.0, ae=lambda: f'={P("nd_sh_cum")}+{V("nd_sh_end")}')
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from shares outstanding at 30-Sep-2026 (594.2m, Q3-26 10-Q).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}+{V("nd_sh_end")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED STATEMENT OF FINANCIAL POSITION (condensed, as in the releases)', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Sep-2026 balance sheet + Q4 flows; 2027E+ from the prior year end; Norfolk Southern balances added at closing')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}-{V("bs_restr")}')
    S('bs_restr', '  Memo: restricted cash included in the cash-flow balance (from 2018)', 'memo', 'm', data='cash_restricted', bs=True, e26=lambda: f'={B1("bs_restr")}', ae=lambda: f'={P("bs_restr")}')
    S('bs_sti', '  Short-term investments', 'line', 'm', data='bs_sti', bs=True, e26_in=V0['sti_26'],
      ae=lambda: f'=IF(N({V("n_frac")})>0,0,{P("bs_sti")}+{V0["sti_build"]})',
      note='$875m at 30-Sep-2026; 2026E input (continued accumulation, assumption); grows until closing, then applied to the cash consideration.')
    S('bs_oca', '  Other current assets (receivables, materials & supplies, other)', 'line', 'm', data='bs_oca', bs=True,
      fc=lambda: f'={V("wc_rev")}*{V("wc_oca_p")}+{V("nsc_oca_add")}*0+IF(N({V("n_frac")})>0,{V("nsc_oca_add_cum")},0)')
    S('nsc_oca_add', '    NSC current assets acquired (receivables, materials, other; closing year)', 'memo', 'm', e26_in=0.0,
      ae=lambda: '=' + close_add(f'{NB["ar"] + NB["materials"] + NB["other_ca"]}'))
    S('nsc_oca_add_cum', '    Memo: NSC current assets carried (held at the acquired level)', 'memo', 'm', e26_in=0.0, ae=lambda: f'={P("nsc_oca_add_cum")}+{V("nsc_oca_add")}')
    S('bs_inv', '  Investments (equity-method affiliates, incl. TTX)', 'line', 'm', data='bs_inv', bs=True, e26=lambda: f'={B1("bs_inv")}+{V0["inv_q4"]}',
      ae=lambda: f'={P("bs_inv")}+{V0["inv_ae"]}+' + close_add(f'{NB["investments"]}'),
      note='Equity income retained (~$150m a year, assumption); NSC investments ($4,186m, 30-Sep-2026) added at closing.')
    S('bs_ppe', '  Properties, net', 'line', 'm', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-({V("cf_capex")}-{ACT("cf_capex")})-{QEc("is_dep")}',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("is_dep")}+' + close_add(f'{NB["ppe_net"]}+{CB("np_ppe")}'),
      note='Roll-forward: prior − capital investments (negative cash flow) − depreciation (+ NSC properties and the fair-value step-up at closing).')
    S('bs_gw', '  Goodwill (Norfolk Southern acquisition; Union Pacific\'s existing $106m sits in other assets)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("bs_gw")}+' + close_add(f'{CB("np_gw")}'))
    S('bs_oa', '  Other assets (incl. operating lease assets, pension asset, goodwill $106m)', 'line', 'm', data='bs_oa', bs=True, e26=lambda: f'={B1("bs_oa")}',
      ae=lambda: f'={P("bs_oa")}+' + close_add(f'{NB["other_assets"]}+{CB("nd_fees")}') + f'-IF(N({V("n_frac")})>0,{CB("nd_fees")}/15*{V("n_frac")},0)')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_cash")}+{V("bs_sti")}+{V("bs_oca")}+{V("bs_inv")}+{V("bs_ppe")}+N({V("bs_gw")})+{V("bs_oa")},"")')
    S('bs_l', "LIABILITIES AND COMMON SHAREHOLDERS' EQUITY", 'sub', 'gen')
    S('bs_std', '  Debt due within one year', 'line', 'm', data='bs_std', bs=True, fc=lambda: f'={V("ds_cp")}+MIN({V("ds_notes")},{V("ds_mat")})',
      note='Commercial paper / revolver + notes maturing in the next year.')
    S('bs_ocl', '  Other current liabilities (payables, accrued wages, casualty, taxes)', 'line', 'm', data='bs_ocl', bs=True,
      fc=lambda: f'={V("wc_rev")}*{V("wc_ocl_p")}+IF(N({V("n_frac")})>0,{V("nsc_ocl_add_cum")},0)')
    S('nsc_ocl_add', '    NSC current liabilities assumed (payables, taxes, other; + retention accrual; closing year)', 'memo', 'm', e26_in=0.0,
      ae=lambda: '=' + close_add(f'{NB["ap"] + NB["income_taxes"] + NB["other_cl"]}-{CB("np_other")}'))
    S('nsc_ocl_add_cum', '    Memo: NSC current liabilities carried (held at the assumed level)', 'memo', 'm', e26_in=0.0, ae=lambda: f'={P("nsc_ocl_add_cum")}+{V("nsc_ocl_add")}')
    S('bs_ltd', '  Debt due after one year', 'line', 'm', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_std")}')
    S('bs_dtl', '  Deferred income taxes', 'line', 'm', data='bs_dtl', bs=True, e26=lambda: f'={B1("bs_dtl")}+({V("cf_dtax")}-{ACT("cf_dtax")})',
      ae=lambda: f'={P("bs_dtl")}+{V("cf_dtax")}+' + close_add(f'{NB["dtl"]}-{CB("np_dtl")}'))
    S('bs_oltl', '  Other long-term liabilities (incl. operating lease liabilities, casualty, OPEB)', 'line', 'm', data='bs_oltl', bs=True, e26=lambda: f'={B1("bs_oltl")}',
      ae=lambda: f'={P("bs_oltl")}+' + close_add(f'{NB["other_liabilities"]}'))
    S('bs_tl', 'Total liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_std")}),{V("bs_std")}+{V("bs_ocl")}+{V("bs_ltd")}+{V("bs_dtl")}+{V("bs_oltl")},"")')
    S('bs_eq', "  Total common shareholders' equity", 'line', 'm', data='bs_eq', bs=True,
      e26=lambda: f'={B1("bs_eq")}+{QEc("is_ni")}+({V("cf_div")}-{ACT("cf_div")})+({V("cf_bb")}-{ACT("cf_bb")})+{QEc("is_sbc")}+({V("cf_ofin")}-{ACT("cf_ofin")})',
      ae=lambda: f'={P("bs_eq")}+{V("is_ni")}+{V("cf_div")}+{V("cf_bb")}+{V("is_sbc")}+{V("cf_ofin")}+' + close_add(f'{CB("nd_stock")}'),
      note='+ net income − dividends − repurchases + share-based compensation + other financing (equity plans) + shares issued to NSC shareholders at closing (OCI held flat).')
    S('bs_tle', "TOTAL LIABILITIES AND COMMON SHAREHOLDERS' EQUITY", 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_eq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=0.6,0,ROUND({V("bs_ta")}-{V("bs_tle")},1)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=0.6,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},1)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash + restricted cash vs cash-flow ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}+N({V("bs_restr")})-{V("cf_end")})<=0.6,0,ROUND({V("bs_cash")}+N({V("bs_restr")})-{V("cf_end")},1)),"")')
    S('bs_shares', '  Memo: shares outstanding at period end (m; XBRL)', 'memo', 'm1', data='sh_out', bs=True, e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    S('nsc_cash_add', '  Memo: NSC cash acquired at closing (30-Sep-2026 cash + retained earnings to closing)', 'memo', 'm', e26_in=0.0,
      ae=lambda: '=' + close_add(f'{NB["cash"]}+({CB("np_eq")}-{NB["equity"]})'))
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL', 'section', note='WORKING CAPITAL — other current assets / liabilities as % of annualised revenues (the releases give condensed balance sheets)')
    S('wc_rev', '  Operating revenues — annualised (quarters × 4; standalone build)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),({V("is_rev")}-N({V("nc_rev")}))*{4 if CTX.col.q else 1},"")')
    S('wc_oca_p', '  Other current assets % of revenues', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_oca")}/{V("wc_rev")},"")', e26_in=V0['wc']['oca'], ae_in=V0['wc']['oca'])
    S('wc_ocl_p', '  Other current liabilities % of revenues', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")', e26_in=V0['wc']['ocl'], ae_in=V0['wc']['ocl'],
      note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (other current assets − other current liabilities)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_oca")}),{V("bs_oca")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of revenues', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; options & RSUs)', 'sched', 'm1', ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing; UNP price at closing)', 'sched', 'pct', ae_in=0.07)
    S('ds_h', 'Debt schedule (notes repaid at maturity and refinanced; acquisition debt and NSC debt added at closing; commercial paper / revolver to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (debt due within one year + debt due after one year)', 'sched', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_acq")}+{V("ds_nsc")}+{V("ds_cp")}', note=MAN['debt']['maturities_src'])
    S('ds_notes', '  Union Pacific notes & debentures (incl. finance leases)', 'sched', 'm', data='debt_tot',
      e26=lambda: f'={B1("ds_notes")}-{V("ds_repay_q")}+{V("ds_newnotes_q")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_newnotes")}',
      note='$30,324m at 30-Sep-2026 (no commercial paper outstanding).')
    S('ds_repay_q', '  Q4/26E maturities (input)', 'sched', 'm', qe_in=V0['repay_q4'], e26=lambda: f'={QEc("ds_repay_q")}', note='2026 maturities $1,521m of which $1,519m repaid in 9M-26.')
    S('ds_newnotes_q', '  Q4/26E new notes (input)', 'sched', 'm', qe_in=0.0, e26=lambda: f'={QEc("ds_newnotes_q")}')
    S('ds_repay', '  Maturities repaid (10-K schedule; input)', 'sched', 'm', ae_in={y: V0['mat'][y] for y in range(FYC + 1, FYL + 1)},
      note='FY2025 10-K: 2027 $1,291m; 2028 $1,239m; 2029 $1,276m; 2030 $753m.')
    S('ds_refi', '  Refinancing % of maturities (input)', 'sched', 'pct', ae_in=V0['refi'])
    S('ds_newnotes', '  New notes issued (maturities × refinancing % + additional issuance input)', 'sched', 'm', ae=lambda: f'={V("ds_repay")}*{V("ds_refi")}+{V("ds_newnotes_add")}')
    S('ds_newnotes_add', '  Additional note issuance (input)', 'sched', 'm', ae_in=V0['newnotes_add'])
    S('ds_mat', '  Maturities in the following year (current portion)', 'sched', 'm', e26_in=V0['mat'][2027], ae_in={y: V0['mat'].get(y + 1, 0.0) for y in range(FYC + 1, FYL + 1)})
    S('ds_acq', '  Acquisition debt (issued at closing; held)', 'sched', 'm', e26_in=0.0, ae=lambda: f'={V("nd_newdebt_bal")}')
    S('ds_nsc', '  NSC debt assumed (at fair value at closing; discount accretes over 10 years)', 'sched', 'm', e26_in=0.0,
      ae=lambda: f'=IF(N({V("n_frac")})>0,{CB("n_tog")}*({CB("ns_debt")}-{CB("np_debtfv")}+{CB("np_debtfv")}/10*MIN(10,{V("n_yrs")})),0)')
    S('ds_pre', '  Cash before CP / revolver (opening cash + CFO + CFI + buybacks, dividends, debt flows, other financing)', 'sched', 'm',
      e26=lambda: (f'={B1("cf_end")}+({V("cf_cfo")}-{ACT("cf_cfo")})+({V("cf_cfi")}-{ACT("cf_cfi")})+({V("cf_bb")}-{ACT("cf_bb")})+({V("cf_div")}-{ACT("cf_div")})'
                   f'+({V("cf_debt_iss")}-{ACT("cf_debt_iss")})-{V("ds_repay_q")}+({V("cf_ofin")}-{ACT("cf_ofin")})'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_bb")}+{V("cf_div")}+{V("cf_debt_iss")}-{V("ds_repay")}+{V("cf_ofin")}')
    S('ds_min', '  Minimum cash balance (incl. restricted)', 'sched', 'm', e26_in=V0['min_cash'], ae_in=V0['min_cash'])
    S('ds_cp', '  Commercial paper / revolver outstanding (year end; $2.0bn facility)', 'sched', 'm', e26=lambda: f'=MAX(0,{B1("ds_cp")}+{V("ds_min")}-{V("ds_pre")})',
      ae=lambda: f'=MAX(0,{P("ds_cp")}+{V("ds_min")}-{V("ds_pre")})', hist=lambda: '=0',
      note='$2.0bn revolving credit facility (renewed 2026, expires May-2031) supporting the commercial paper program; nothing drawn at 30-Sep-2026. Draws above $2.0bn would need other financing (headroom memo).')
    S('ds_head', '  Memo: facility headroom vs the $2.0bn commitment', 'memo_calc', 'm', e26=lambda: f'=2000-{V("ds_cp")}', ae=lambda: f'=2000-{V("ds_cp")}')
    S('ds_r_notes', '  Interest rate on opening notes %', 'sched', 'pct', ae_in=V0['r_notes'], note=MAN['debt']['rate_note'] + ' New notes assumed at ~5%.')
    S('ds_r_cp', '  Interest rate on opening commercial paper %', 'sched', 'pct', ae_in=0.045)
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / adjusted EBITDA, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end; opening net debt + NSC debt assumed − CFO − CFI (ex short-term investments) + dividends − other financing)', 'sched', 'm',
      ae=lambda: f'={P("ds_total")}-{P("cf_end")}-{P("bs_sti")}+({V("ds_nsc")}-{P("ds_nsc")})-{V("cf_cfo")}-({V("cf_cfi")}-{V("cf_sti")})-{V("cf_div")}-{V("cf_ofin")}',
      note='Debt refinancing, acquisition debt (cash-neutral) and commercial paper are excluded so the plug has no circularity; NSC debt assumed is added (non-cash).')
    S('lev_eb', '  Adjusted EBITDA for leverage (pro forma full year in the closing year)', 'sched', 'm', ae=lambda: f'=IF(AND(N({V("n_frac")})>0,N({V("n_frac")})<1),{V("nc_pf")},{V("r_adj")})')
    S('lev_tgt', '  Target net debt = target leverage × adjusted EBITDA', 'sched', 'm', ae=lambda: f'={V("lev_min")}*{V("lev_eb")}')
    S('lev_bb', '  Share repurchases: plug to target leverage', 'sched', 'm', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash beyond the leverage target is returned via buybacks; nil while leverage is above the target (post-closing deleveraging).')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_int', '  Interest expense ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    S('hr_lease', '  Memo: operating lease liabilities (company tables; not in debt)', 'memo', 'm', ann=True, data='lease_liab')
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted EBIT = adjusted operating income)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT (adjusted operating income)', 'line', 'm', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(MIN(0.4,MAX(0.15,{V("is_etr")})),0.235)')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity', 'line', 'm', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − cash − short-term investments', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")}-N({V("bs_sti")}),"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Revenues', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Revenues / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill', 'line', 'm', ann=True, all=lambda: f'=-N({V("bs_gw")})')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (other current liabilities)', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-{V("bs_ocl")},"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income', 'line', 'm', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Common shareholders' equity", 'line', 'm', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash − short-term investments', 'line', 'm', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA (model)', 'line', 'm', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_co', 'Memo: company adjusted debt / adjusted EBITDA (x; total debt + operating leases + unfunded post-retirement ÷ covenant EBITDA)', 'line', 'x2', ann=True, data='adj_lev_pub')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interests (USDm; none)', 'line', 'm', e26_in=0.0, ae=lambda: '=0')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Operating revenues', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted operating income', lambda: f'=IFERROR({V("v_ev")}/{V("o_adj")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield (CFO − capital investments)', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
