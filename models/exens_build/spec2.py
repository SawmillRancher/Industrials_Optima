"""Row specification part 2: cash flow, dividends & share schedule, balance sheet, working capital, forecast schedules
(intangibles & PPA, PP&E, IFRS 16 leases, future-M&A lever, debt & revolver to minimum cash, deferred tax, equity), ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum

def B6(key): return f'{H1}{R[key]}'            # 30-Jun-2026 balance
def h26(key): return f'{H1}{R[key]}'           # H1/26 actual for a flow row
def is_he(): return CTX.col.kind == 'HE'
def PB(key):
    """prior balance: 30-Jun-26 in the H2/26E column, prior year end in 2027E+"""
    return B6(key) if is_he() else P(key)
def PF(key):
    """prior flow reference for schedules"""
    return B6(key) if is_he() else P(key)

def build_spec2(V0):
    S = add
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS (as presented; condensed)', 'section',
      note='CASH FLOW — forecast logic (H2/26E from the H1-26 statement; 2027E+ annual; halves derived as FY − H1). From FY2025 the statement starts from net profit from continuing operations')
    S('cf_ni', 'Net profit (from continuing operations, 2025+)', 'line', 'm1', data='cf_ni', flow=True, fc=lambda: f'={V("is_nic")}')
    S('cf_adj', 'Adjustments:', 'sub', 'gen')
    S('cf_fin', '  Net financial income and expenses (cash and non-cash)', 'line', 'm1', data='cf_fin', flow=True, fc=lambda: f'=-{V("is_netfin")}')
    S('cf_tax', '  Income tax', 'line', 'm1', data='cf_tax', flow=True, fc=lambda: f'={V("is_tax")}')
    S('cf_dna', '  Depreciation, amortisation, impairment and provisions, net', 'line', 'm1', data='cf_dna', flow=True, fc=lambda: f'={V("is_dna")}')
    S('cf_oth', '  Other income and expenses (IFRS 2 share-based payments, grant releases; derived)', 'line', 'm1', data='cf_oth', flow=True, fc=lambda: f'={V("d_sbc")}',
      note='Forecast = share-based payments (non-cash).')
    S('cf_taxp', '  Income tax paid', 'line', 'm1', data='cf_taxp', flow=True, fc=lambda: f'=-{V("is_tax")}-{V("d_ppa")}*{V("dtl_rate")}',
      note='Forecast: cash tax = P&L tax + the deferred-tax credit on PPA amortisation (the DTL unwind is non-cash; the French tax-group loss carry-forwards were used up by mid-2026).')
    S('cf_wc', '  Change in working capital, net of impairment', 'line', 'm1', data='cf_wc', flow=True,
      he=lambda: (f'=-({V("bs_ar")}-{B6("bs_ar")})-({V("bs_inv")}-{B6("bs_inv")})-({V("bs_oca")}-{B6("bs_oca")})+({V("bs_ap")}-{B6("bs_ap")})+({V("bs_ocl")}-{B6("bs_ocl")})'),
      ae=lambda: f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_inv")}-{P("bs_inv")})-({V("bs_oca")}-{P("bs_oca")})+({V("bs_ap")}-{P("bs_ap")})+({V("bs_ocl")}-{P("bs_ocl")})',
      note='Linked to the balance sheet (receivables, inventories, other current assets, payables, other current liabilities). H2/26E = change from 30-Jun-26. Acquired working capital is excluded (future-M&A net assets go to PP&E / goodwill).')
    S('cf_cfo', 'Net cash from operating activities', 'line_b', 'm1', data='cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Purchases of intangible assets and PP&E (capex + capitalised R&D)', 'line', 'm1', data='cf_capex', flow=True,
      he=lambda: f'=-({V("capex_pct", E26)}+{V("caprd_pct", E26)})*{V("is_rev", E26)}-{h26("cf_capex")}', ae=lambda: f'=-{V("is_rev")}*({V("capex_pct")}+{V("caprd_pct")})',
      note='2026E: guided ~9% capex + ~3% capitalised R&D of FY26 revenue (H2 = FY − H1). 2027E+: capex % (normalising to ~5% after the 2027 capacity completion) + capitalised R&D % of revenue.')
    S('cf_acq', 'Acquisitions of equity investments, net of cash acquired', 'line', 'm1', data='cf_acq', flow=True, he_in=0.0, ae=lambda: f'=-{V("ma_spend")}',
      note='History as reported. H2/26E: none assumed after Emberion (closed Apr-2026). 2027E+: future-M&A lever (scenario table).')
    S('cf_oinv', 'Other investing (disposals, grants, other financial assets)', 'line', 'm1', data='cf_oinv', flow=True, he_in=0.0, ae_in=0.0)
    S('cf_cfi', 'Net cash from investing activities', 'line_b', 'm1', data='cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_eq', 'Share capital increases net of costs, treasury-share purchases / sales', 'line', 'm1', data='cf_eq', flow=True, he_in=0.0, ae=lambda: f'=-{V("bb_cash")}',
      note='IPO Jun-2024 (€180m gross); ExoShare 2025 (€4.3m); LTIP buyback 2025 (€8.8m). Forecast: buyback input (no open-market programme; treasury purchases only cover share plans).')
    S('cf_div', 'Dividends paid', 'line', 'm1', data='cf_div', flow=True, he_in=0.0, ae=lambda: f'=-{V("dv_paid")}',
      note='€0.10 per share paid May-2025; €0.30 paid Jun-2026 (in H1). Forecast: prior-year DPS × opening shares, paid in H1 of the following year.')
    S('cf_debt', 'Borrowings drawn (repaid), net, incl. issue costs', 'line', 'm1', data='cf_debt', flow=True, fc=lambda: f'={V("db_flow")}',
      note='Jun-2024: €250m TLB drawn, €307.6m legacy bonds / loans repaid. Forecast: revolver (RCF / EIB) drawn or repaid to the minimum cash balance + other loan amortisation (debt schedule).')
    S('cf_int', 'Interest paid (borrowings and leases), net of interest received', 'line', 'm1', data='cf_int', flow=True, fc=lambda: f'=-{V("is_cnd")}+{V("db_accr")}+N({V("is_finoth")})',
      note='Forecast = cost of net debt less the non-cash accretion of Term Loan B issue costs, plus interest income.')
    S('cf_lease', 'Repayment of IFRS 16 lease liabilities', 'line', 'm1', data='cf_lease', flow=True, he=lambda: f'=-{PT("pt_lease")}', ae=lambda: f'=-{V("ls_rep")}')
    S('cf_ofin', 'Other financing', 'line', 'm1', data='cf_ofin', flow=True, he_in=0.0, ae_in=0.0)
    S('cf_cff', 'Net cash from financing activities', 'line_b', 'm1', data='cff', flow=True, fc=lambda: f'=SUM({V("cf_eq")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of exchange-rate changes', 'line', 'm1', data='cf_fx', flow=True, he_in=0.0, ae_in=0.0)
    S('cf_disc', 'Cash flow from discontinued operations (Microwave Amplification)', 'line', 'm1', data='cf_disc', flow=True, he_in=0.0, ae_in=0.0)
    S('cf_net', 'Increase (decrease) in cash and cash equivalents', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")})+N({V("cf_disc")}),"")')
    S('cf_beg', 'Opening cash and cash equivalents (cash-flow basis)', 'line', 'm1', data='cf_beg', he=lambda: f'={B6("cf_end")}', e26=lambda: f'={Y("cf_end", 2025)}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Closing cash and cash equivalents (cash-flow basis: net of overdrafts, excl. accrued interest)', 'line_b', 'm1', data='cf_end', he=lambda: f'={V("cf_beg")}+{V("cf_net")}',
      e26=lambda: f'={H2}{R["cf_end"]}', ae=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: opening + CFO + CFI + CFF + FX + discontinued = closing cash (should be 0; ±0.01)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=0.011,0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},3)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0; ±0.01)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")})<=0.011,0,ROUND(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")},3)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow, model (CFO − purchases of intangible assets & PP&E − lease repayments)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")}+N({V("cf_lease")}),"")',
      note='Model definition (after capitalised R&D and IFRS 16 principal). The company "free cash flow after growth capex" (below) starts from Adjusted EBITDA and excludes interest and acquisitions.')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of revenue', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / net profit excl. PPA conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share (€)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_co', '  Company-published free cash flow after growth capex (Adj. EBITDA − capitalised R&D − ΔWC − tax paid − capex − other)', 'memo', 'm1', data='fcf_pub', flow=True,
      note='Company APM (FY25 €57.3m; FY24 €58.7m; H1-26 €31.4m). Not forecast: it excludes interest, acquisitions and dividends.')
    S('cc_conv', '  Company cash conversion % ((Adj. EBITDA − capitalised R&D − capex) ÷ (Adj. EBITDA − capitalised R&D))', 'pct', 'pct', data='cash_conv_pub',
      fc=lambda: f'=IFERROR(({V("r_adj")}-{V("caprd")}-{V("capex")})/({V("r_adj")}-{V("caprd")}),"")',
      note='Company target 70–75% (FY25 73.6%, FY24 73.4%). Forecast falls to ~70% in 2026–27 with the capacity programme, then recovers with capex at ~5% of revenue.')
    S('capex_h', 'Capital expenditure (company split)', 'sub', 'gen')
    S('capex', '  Capital expenditure excl. capitalised R&D (€m)', 'line', 'm1', data='capex', flow=True,
      he=lambda: f'={V("capex_pct", E26)}*{V("is_rev", E26)}-{h26("capex")}', ae=lambda: f'={V("is_rev")}*{V("capex_pct")}',
      note='Company APM (growth + maintenance capex; FY25 €36.4m = 7.8% of revenue; H1-26 €23.3m = 9.2%). 2026E guided ~9%.')
    S('caprd', '  Capitalised R&D costs (€m)', 'line', 'm1', data='cap_rd', flow=True,
      he=lambda: f'={V("caprd_pct", E26)}*{V("is_rev", E26)}-{h26("caprd")}', ae=lambda: f'={V("is_rev")}*{V("caprd_pct")}',
      note='FY25 €13.7m (2.9%); H1-26 €9.2m (3.6%); guided ~3%.')
    S('capex_pct', '  Capex % of revenue', 'pct', 'pct', all=ratio('capex', 'is_rev'), e26=lambda: '=' + CH(SC['out_capex']), ae_in=V0['capex_pct'],
      note='2026E guidance ~9%; company: normalised ~5% after the capacity expansion completes in 2027. 2027E input 7%, then 5%.')
    S('caprd_pct', '  Capitalised R&D % of revenue', 'pct', 'pct', all=ratio('caprd', 'is_rev'), e26=lambda: '=' + CH(SC['out_caprd']), ae_in=V0['caprd_pct'])
    S('capex_chk', '  Check: capex + capitalised R&D vs cash-flow purchases of intangible assets & PP&E (should be 0; ±1.5: timing of capex payables; from 2022, the 2021 predecessor statement is on a different basis)', 'check', 'm1',
      hist=lambda: (f'=IF(AND(ISNUMBER({V("capex")}),ISNUMBER({V("cf_capex")})),IF(ABS({V("capex")}+{V("caprd")}+{V("cf_capex")})<=1.5,0,ROUND({V("capex")}+{V("caprd")}+{V("cf_capex")},1)),"")' if CTX.col.year >= 2022 else None),
      note='The company reclassifies unpaid capex at period end into working capital, so cash purchases differ from the APM by the change in capex payables.')
    S('cf_capex_t', '  Memo: total purchases of intangible assets and PP&E (positive)', 'memo_calc', 'm1', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),-{V("cf_capex")},"")')
    S('capex_dep', '  Purchases / D&A excl. PPA (x)', 'line', 'x2', all=lambda: f'=IF(AND(ISNUMBER({V("cf_capex")}),ISNUMBER({V("d_dna")})),IFERROR(-{V("cf_capex")}/{V("d_dna")},""),"")')
    blank()

    # ------------------------------------------------------------------ DIVIDENDS & SHARES
    S('sec_bb', 'DIVIDENDS & SHARE SCHEDULE (no open-market buyback programme; treasury purchases cover share plans)', 'section',
      note='SHARES — 50.94m shares in issue (unchanged since Nov-2025); dividends = prior-year DPS × opening shares (paid in H1); buybacks are an input (none assumed)')
    S('pay_ratio', '  Dividend payout ratio (declared on the year\'s net profit)', 'driver', 'pct', hist=lambda: f'=IF(AND(ISNUMBER({V("dps")}),ISNUMBER({V("eps_basic")})),IFERROR({V("dps")}/{V("eps_basic")},""),"")',
      e26=lambda: f'={PT("pt_div")}', ae=lambda: f'={PT("pt_div")}', note='Policy 20–25% of net income; FY25 €0.30 on €0.84 EPS = 36% (25% of EPS before the MA disposal loss).')
    S('dv_paid', '  Dividends paid in the year (€m; prior-year DPS × opening shares)', 'line', 'm1', hist=lambda: f'=IF(ISNUMBER({V("cf_div")}),-{V("cf_div")},"")',
      he_in=0.0, e26=lambda: f'=-{h26("cf_div")}', ae=lambda: f'={P("dps")}*{V("bb_beg")}')
    S('bb_cash', '  Share repurchases (€m; input — none assumed)', 'line', 'm1', he_in=0.0, ae_in=V0['bb_ae'],
      note='No buyback authorisation beyond share-plan coverage (240,000 shares bought Jul–Sep 2025 for the LTIP). Scenario input, 0 in all cases.')
    S('bb_px', '  Avg repurchase price (€)', 'line', 'm2', he=lambda: f'={V("v_px", E26)}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_sh', '  Shares repurchased (m)', 'line', 'm2', he=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued / delivered under share plans (m)', 'driver', 'm2', he_in=0.0, ae_in=V0['iss'],
      note='ExoShare 2025: 154,197 new shares; LTIP 2025-26 (216,750) vests 2027 from treasury shares; assumed ~0.15m p.a. net issuance.')
    S('bb_beg', '  Opening shares outstanding, net of treasury shares (m)', 'line', 'm2', he=lambda: f'={B6("bs_shares")}', e26=lambda: f'={Y("bs_shares", 2025)}', ae=lambda: f'={P("bb_end")}',
      note='Shares in issue less treasury shares (31-Dec-25: 50.937m − 0.247m; 30-Sep-26 notice: 50,936,749 in issue).')
    S('bb_end', '  Closing shares outstanding, net of treasury shares (m)', 'line', 'm2', he=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', e26=lambda: f'={H2}{R["bb_end"]}',
      ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', he=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED STATEMENT OF FINANCIAL POSITION', 'section',
      note='BS FORECAST — H2/26E (31-Dec-26) rolled forward from the 30-Jun-2026 balance sheet + H2 flows; 2027E+ from the prior year end. 30-Jun balance sheets from H1/24 (none published for 30-Jun-23)')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_gw', '  Goodwill', 'line', 'm1', data='bs_gw', bs=True, he=lambda: f'={B6("bs_gw")}+{V("ma_gw")}', ae=lambda: f'={P("bs_gw")}+{V("ma_gw")}', note='+ goodwill on future M&A (lever).')
    S('bs_int', '  Intangible assets (development costs, technologies, customer relationships, brands)', 'line', 'm1', data='bs_int', bs=True,
      he=lambda: f'={B6("bs_int")}+{V("caprd")}+{V("ma_int")}-{V("d_dna")}*{V("ia_share")}-{V("d_ppa")}-{V("d_brand")}',
      ae=lambda: f'={P("bs_int")}+{V("caprd")}+{V("ma_int")}-{V("d_dna")}*{V("ia_share")}-{V("d_ppa")}-{V("d_brand")}',
      note='Roll-forward: + capitalised R&D + acquired intangibles (M&A lever) − amortisation (share of D&A excl. PPA) − PPA amortisation − impairment.')
    S('bs_ppe', '  Property, plant and equipment', 'line', 'm1', data='bs_ppe', bs=True,
      he=lambda: f'={B6("bs_ppe")}+{V("capex")}+{V("ma_na")}-{V("d_dna")}*{V("ppe_share")}', ae=lambda: f'={P("bs_ppe")}+{V("capex")}+{V("ma_na")}-{V("d_dna")}*{V("ppe_share")}',
      note='Roll-forward: + capex (+ other net assets of future acquisitions) − depreciation (share of D&A excl. PPA). €37m capacity programme (Europe, Sturbridge US plant from 2027).')
    S('bs_rou', '  Right-of-use assets (IFRS 16)', 'line', 'm1', data='bs_rou', bs=True, he=lambda: f'={V("is_rev", E26)}*{V("ls_rou_pct")}', ae=lambda: f'={V("is_rev")}*{V("ls_rou_pct")}',
      note='Property and equipment leases; forecast at a % of revenue (new leases = plug in the lease schedule).')
    S('bs_eqinv', '  Investments in equity-accounted companies and other investments', 'line', 'm1', data='bs_eqinv', bs=True, he=lambda: f'={B6("bs_eqinv")}', ae=lambda: f'={P("bs_eqinv")}',
      note='30-Jun-26: Adelphi Technology 29.99% (€2.3m), Emberion shares (€2.5m, consolidated from H2-26; held flat for simplicity), Photonis Asia / other.')
    S('bs_onca', '  Non-current financial and other assets', 'line', 'm1', data='bs_onca', bs=True, he=lambda: f'={B6("bs_onca")}', ae=lambda: f'={P("bs_onca")}')
    S('bs_dta', '  Deferred tax assets', 'line', 'm1', data='bs_dta', bs=True, he=lambda: f'={B6("bs_dta")}', ae=lambda: f'={P("bs_dta")}')
    S('bs_tnca', 'Non-current assets', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_gw")}),SUM({V("bs_gw")}:{V("bs_dta")}),"")')
    S('bs_inv', '  Inventories', 'line', 'm1', data='bs_inv', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dinv")}/365')
    S('bs_ar', '  Trade receivables', 'line', 'm1', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_oca', '  Current financial and other current assets (tax receivables, prepayments, derivatives)', 'line', 'm1', data='bs_oca', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_ocap")}')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm1', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}+N({V("bs_cashadj")})')
    S('bs_tca', 'Current assets', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_inv")}),SUM({V("bs_inv")}:{V("bs_cash")}),"")')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_gw")}),{V("bs_tnca")}+{V("bs_tca")},"")')
    S('bs_l', 'EQUITY AND LIABILITIES', 'sub', 'gen')
    S('bs_cap', '  Share capital and share premiums', 'line', 'm1', data='bs_cap', bs=True, he=lambda: f'={B6("bs_cap")}', ae=lambda: f'={P("bs_cap")}',
      note='€21.6m capital (50,936,749 shares × €0.425) + €346.8m premiums; held flat (share-plan issues immaterial).')
    S('bs_res', '  Reserves (retained earnings, translation, treasury shares, IFRS 2 reserve)', 'line', 'm1', data='bs_res', bs=True,
      he=lambda: f'={B6("bs_res")}+{V("is_ni")}-{V("dv_paid")}+{V("d_sbc")}-{V("bb_cash")}',
      ae=lambda: f'={P("bs_res")}+{V("is_ni")}-{V("dv_paid")}+{V("d_sbc")}-{V("bb_cash")}',
      note='Roll-forward: + net profit − dividends paid + IFRS 2 share-based payment reserve − treasury purchases. No OCI assumed (hedges, actuarial, translation).')
    S('bs_teq', 'Equity (attributable to shareholders; no non-controlling interests)', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cap")}),{V("bs_cap")}+{V("bs_res")},"")')
    S('bs_ncb', '  Non-current loans and borrowings (Term Loan B, RCF / EIB, other loans)', 'line', 'm1', data='bs_ncb', bs=True, fc=lambda: f'={V("db_tlb")}+{V("db_rcf")}+{V("db_oth")}-{V("bs_cb")}')
    S('bs_ncll', '  Non-current lease liabilities', 'line', 'm1', data='bs_ncll', bs=True, fc=lambda: f'={V("ls_ll")}-{V("bs_cll")}')
    S('bs_pens', '  Provisions for employee benefit obligations', 'line', 'm1', data='bs_pens', bs=True, he=lambda: f'={B6("bs_pens")}', ae=lambda: f'={P("bs_pens")}')
    S('bs_oncl', '  Non-current provisions and other non-current liabilities (incl. NVLS put, R&D grants)', 'line', 'm1', data='bs_oncl', bs=True, he=lambda: f'={B6("bs_oncl")}', ae=lambda: f'={P("bs_oncl")}')
    S('bs_dtl', '  Deferred tax liabilities', 'line', 'm1', data='bs_dtl', bs=True,
      he=lambda: f'={B6("bs_dtl")}-{V("d_ppa")}*{V("dtl_rate")}+{V("ma_dtl")}', ae=lambda: f'={P("bs_dtl")}-{V("d_ppa")}*{V("dtl_rate")}+{V("ma_dtl")}',
      note='Mostly on PPA intangibles: unwinds with PPA amortisation at the deferred-tax rate; new DTL on acquired intangibles (M&A lever).')
    S('bs_tncl', 'Non-current liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ncb")}),SUM({V("bs_ncb")}:{V("bs_dtl")}),"")')
    S('bs_cb', '  Current loans and borrowings (incl. accrued interest, overdrafts)', 'line', 'm1', data='bs_cb', bs=True, he_in=0.5, ae_in=0.5, note='Current portion of the other loans; forecast input.')
    S('bs_cll', '  Current lease liabilities', 'line', 'm1', data='bs_cll', bs=True, fc=lambda: f'={V("ls_ll")}*{V("ls_cur")}')
    S('bs_ap', '  Trade payables', 'line', 'm1', data='bs_ap', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dpo")}/365')
    S('bs_ocl', '  Current provisions and other current liabilities (social / tax payables, customer advances, accruals, derivatives)', 'line', 'm1', data='bs_ocl', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_oclp")}')
    S('bs_tcl', 'Current liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cb")}),SUM({V("bs_cb")}:{V("bs_ocl")}),"")')
    S('bs_tl', 'Total liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_tncl")}),{V("bs_tncl")}+{V("bs_tcl")},"")')
    S('bs_tle', 'TOTAL EQUITY AND LIABILITIES', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E; should be 0; ±0.01)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=0.011,0,ROUND({V("bs_ta")}-{V("bs_tle")},3)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0; ±0.01)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=0.011,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},3)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm1', data='bs_ta', bs=True)
    S('bs_cashadj', '  Memo: BS cash − cash-flow cash (accrued interest receivable in cash, less overdrafts)', 'memo', 'm1', data='cash_adj', he_in=0.0, ae_in=0.0,
      note='The cash-flow statement closes on cash net of bank overdrafts and (from 2025) excluding accrued interest receivable; 31-Dec-25 difference €0.1m, 31-Dec-24 €0.9m (€1.2m accrued interest − €0.3m overdraft).')
    S('bs_chk_cash', '  Check: BS cash vs cash-flow closing cash + adjustment (should be 0; ±0.05)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}-N({V("bs_cashadj")})-{V("cf_end")})<=0.05,0,ROUND({V("bs_cash")}-N({V("bs_cashadj")})-{V("cf_end")},3)),"")')
    S('bs_shares', '  Memo: shares outstanding at period end, net of treasury shares (m)', 'memo', 'm2',
      hist=lambda: f'=IF(ISNUMBER({V("bs_sh_iss")}),{V("bs_sh_iss")}-N({V("bs_treas")}),"")', fc=lambda: f'={V("bb_end")}')
    S('bs_sh_iss', '  Memo: shares in issue at period end (m)', 'memo', 'm2', data='shares_out', bs=True)
    S('bs_treas', '  Memo: treasury shares at period end (m)', 'memo', 'm2', data='treasury', bs=True)
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input), on annual revenue (H1 balances on annualised H1 revenue)')
    S('wc_rev', '  Revenue reference (annual; H1 columns annualised × 2)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{2 if (CTX.col.h == 1) else 1},"")', he=lambda: f'={V("is_rev", E26)}',
      note='31-Dec balances are measured on the year\'s revenue (H2 columns carry the year-end balance sheet); 30-Jun balances on 2 × H1 revenue.')
    S('wc_dso', '  Receivable days — trade receivables / revenue × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', he_in=V0['wc']['dso'], ae_in=V0['wc']['dso'],
      note='FY25 57d (FY24 68d); H1-26 55d on annualised H1 revenue. Held at the FY25 year-end level.')
    S('wc_dinv', '  Inventory days — inventories / revenue × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_inv")}/{V("wc_rev")}*365,"")', he_in=V0['wc']['dinv'], ae_in=V0['wc']['dinv'],
      note='On revenue (the IFRS cost-of-sales line covers materials only; the management cost of sales incl. staff is unaudited). FY25 82d; 30-Jun-26 89d (second-half deliveries).')
    S('wc_dpo', '  Payable days — trade payables / revenue × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_rev")}*365,"")', he_in=V0['wc']['dpo'], ae_in=V0['wc']['dpo'])
    S('wc_ocap', '  Other current assets % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_oca")}/{V("wc_rev")},"")', he_in=V0['wc']['oca'], ae_in=V0['wc']['oca'])
    S('wc_oclp', '  Other current liabilities % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")', he_in=V0['wc']['ocl'], ae_in=V0['wc']['ocl'], note=V0['wc']['note'])
    S('wc_nwc', '  Net working capital (receivables + inventories + other current assets − payables − other current liabilities)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_inv")}+{V("bs_oca")}-{V("bs_ap")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm1', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions (blue = input)')
    S('da_h', 'D&A excl. PPA — allocation to asset classes', 'sub', 'gen')
    S('ia_share', '  Intangible assets (capitalised development costs, software) share of D&A excl. PPA', 'sched', 'pct', he_in=0.43, ae_in=0.43,
      note='FY25: amortisation of non-PPA intangibles ≈ €10.8m (Note 16 €24.9m less ~€14.1m PPA), PP&E depreciation €10.5m (Note 17), right-of-use €3.7m (Note 10 continuing) of €24.0m.')
    S('ppe_share', '  PP&E share', 'sched', 'pct', he_in=0.42, ae_in=0.42)
    S('rou_share', '  Right-of-use share', 'sched', 'pct', he=lambda: f'=1-{V("ia_share")}-{V("ppe_share")}', ae=lambda: f'=1-{V("ia_share")}-{V("ppe_share")}')
    S('ppa_h', 'PPA intangibles amortisation schedule', 'sub', 'gen')
    S('ia_ppa_ex', '  Existing PPA intangibles amortisation (customer relationships / technologies acquired to 2025; €m p.a.)', 'sched', 'm1', ae_in={2027: 15.8, 2028: 15.8, 2029: 15.8, 2030: 15.0},
      note='FY26 run-rate ~€15.8m (H1-26 €7.9m); customer relationships amortised over 8–20 years, technologies 5–15 years (€97.8m + ~€26m net at 30-Jun-26). Input, slightly declining in 2030.')
    S('ia_ppa_ma', '  Amortisation of intangibles acquired through the M&A lever (€m; straight-line, half-year in the deal year)', 'sched', 'm1',
      ae=lambda: f'=({V("ma_int_cum")}-{V("ma_int")}/2)/{V("ma_life")}')
    S('ia_ppa_am', '  = PPA amortisation (2027E+)', 'sched', 'm1', ae=lambda: f'={V("ia_ppa_ex")}+{V("ia_ppa_ma")}')
    S('ma_h', 'Future-M&A lever (bolt-on acquisitions; scenario table)', 'sub', 'gen')
    S('ma_spend', '  Acquisition spend (€m; consideration incl. net debt assumed)', 'sched', 'm1', he_in=0.0, ae=lambda: '=' + CH(SC['MA'][CTX.col.year]),
      note='Base €60m p.a. (FY23–25 average ~€57m): technology bolt-ons in imaging / detection; leverage may rise to ~2x (company).')
    S('ma_evs', '  EV / revenue paid (x)', 'sched', 'x', ae_in=V0['ma_evs'], note='Noxant ~2.1x (€45.7m for ~€22m annualised revenue), Phasics ~2.1x; NVLS, Centronic lower. Input 2.5x.')
    S('ma_rev_full', '  Acquired revenue, full-year run-rate (€m)', 'sched', 'm1', ae=lambda: f'=IFERROR({V("ma_spend")}/{V("ma_evs")},0)')
    S('ma_di_share', '  Share allocated to Detection & Imaging', 'sched', 'pct', ae_in=V0['ma_di_share'], note='Recent deals: Noxant, Phasics, Emberion, Centronic, LR Tech, Telops, El-Mul → D&I; NVLS → Amplification.')
    S('ma_rev_di', '  Revenue contribution — Detection & Imaging (mid-year convention: ½ in the deal year, ½ the next)', 'sched', 'm1',
      ae=lambda: f'={V("ma_di_share")}*({V("ma_rev_full")}+{P("ma_rev_full") if CTX.col.year > 2027 else "0"})/2')
    S('ma_rev_amp', '  Revenue contribution — Amplification', 'sched', 'm1',
      ae=lambda: f'=(1-{V("ma_di_share")})*({V("ma_rev_full")}+{P("ma_rev_full") if CTX.col.year > 2027 else "0"})/2')
    S('ma_int_pct', '  Intangibles % of consideration', 'sched', 'pct', ae_in=V0['ma_int'], note='Noxant: €19.0m intangibles on €45.7m (42%); Phasics €10.6m on €32.1m (33%).')
    S('ma_int', '  Acquired intangibles (€m)', 'sched', 'm1', he_in=0.0, ae=lambda: f'={V("ma_spend")}*{V("ma_int_pct")}')
    S('ma_int_cum', '  Cumulative acquired intangibles (gross, €m)', 'sched', 'm1', ae=lambda: f'={V("ma_int")}+{P("ma_int_cum") if CTX.col.year > 2027 else "0"}')
    S('ma_life', '  Amortisation life (years)', 'sched', 'yrs', ae_in=V0['ma_life'])
    S('ma_dtl', '  Deferred tax liability on acquired intangibles (€m)', 'sched', 'm1', he_in=0.0, ae=lambda: f'={V("ma_int")}*{V("dtl_rate")}')
    S('ma_na', '  Other net assets acquired (working capital, PP&E; 10% of consideration, booked in PP&E)', 'sched', 'm1', he_in=0.0, ae=lambda: f'={V("ma_spend")}*0.1')
    S('ma_gw', '  Goodwill (= consideration − intangibles − other net assets + DTL)', 'sched', 'm1', he_in=0.0, ae=lambda: f'={V("ma_spend")}-{V("ma_int")}-{V("ma_na")}+{V("ma_dtl")}')
    S('dtl_rate', '  Deferred-tax rate on PPA intangibles', 'sched', 'pct', he_in=V0['dtl_rate'], ae_in=V0['dtl_rate'])
    S('ls_h', 'Leases (IFRS 16) — right-of-use assets and lease liabilities', 'sub', 'gen')
    S('ls_rou_pct', '  Right-of-use assets % of revenue', 'sched', 'pct', hist=lambda: f'=IFERROR({V("bs_rou")}/{V("wc_rev")},"")', he_in=V0['rou_pct'], ae_in=V0['rou_pct'],
      note='31-Dec-25 3.2%; 30-Jun-26 3.1% of annualised revenue (new US property leases).')
    S('ls_rdep', '  Right-of-use depreciation (share of D&A excl. PPA)', 'sched', 'm1', he=lambda: f'={V("d_dna")}*{V("rou_share")}', ae=lambda: f'={V("d_dna")}*{V("rou_share")}')
    S('ls_new', '  New leases (non-cash additions; plug = Δ right-of-use + depreciation)', 'sched', 'm1',
      he=lambda: f'={V("bs_rou")}-{B6("bs_rou")}+{V("ls_rdep")}', ae=lambda: f'={V("bs_rou")}-{P("bs_rou")}+{V("ls_rdep")}')
    S('ls_rep', '  Lease principal repayments (2027E+ ≈ right-of-use depreciation)', 'sched', 'm1', he=lambda: f'={PT("pt_lease")}', ae=lambda: f'={V("ls_rdep")}')
    S('ls_ll', '  Lease liabilities (current + non-current)', 'sched', 'm1', bs=True, hist=lambda: f'=IF(ISNUMBER({V("bs_cll")}),{V("bs_cll")}+{V("bs_ncll")},"")',
      he=lambda: f'={B6("ls_ll")}+{V("ls_new")}-{V("ls_rep")}', ae=lambda: f'={P("ls_ll")}+{V("ls_new")}-{V("ls_rep")}', note='Roll-forward: prior + new leases − principal repayments.')
    S('ls_cur', '  Current portion %', 'sched', 'pct', hist=lambda: f'=IFERROR({V("bs_cll")}/{V("ls_ll")},"")', he_in=0.25, ae_in=0.25)
    S('ls_rate', '  Lease interest rate on opening lease liabilities %', 'sched', 'pct', he_in=V0['ll_rate'], ae_in=V0['ll_rate'], note='H1-26 €0.66m on €16.6m opening (~7.9% annualised); FY25 €1.0m on €10.9m. Input.')
    S('db_h', 'Debt schedule — Term Loan B, revolver / EIB to minimum cash, other loans (interest on opening balances; no circularity)', 'sub', 'gen')
    S('db_tlb', '  Term Loan B (€250m bullet, Jun-2029; carrying amount net of issue costs)', 'sched', 'm1', data='tlb', bs=True,
      he=lambda: f'={B6("db_tlb")}+{V("db_accr")}', ae=lambda: (f'={P("db_tlb")}+{V("db_accr")}' if CTX.col.year < 2029 else (f'=250*{V("db_refi")}' if CTX.col.year == 2029 else f'={P("db_tlb")}')),
      note='3M Euribor + 1.15% (grid 0.95–1.75% by leverage; renegotiated 3-Jun-2026); issue costs (€3.9m at 30-Jun-26) accrete to par by maturity. 2029E: refinanced at the % below (company: 5-year RCF / EIB lines run to 2029 and 2033).')
    S('db_accr', '  Term Loan B issue-cost accretion (non-cash interest, €m)', 'sched', 'm1', he_in=0.4, ae=lambda: ('=0.8' if CTX.col.year < 2029 else '=0'),
      note='€3.9m of unamortised issue costs at 30-Jun-26 accrete to par by Jun-2029 (effective-interest method); in the cost of net debt but not in interest paid.')
    S('db_refi', '  Term Loan B refinanced at maturity (%)', 'sched', 'pct', ae_in=V0['tlb_refi'])
    S('db_tlb_r', '  Term Loan B all-in rate %', 'sched', 'pct', he_in=V0['tlb_rate'], ae_in=V0['tlb_rate'], note='3M Euribor ~2.1% (Oct-2026) + 1.15% margin; H1-26 interest on bank borrowings €5.7m on €250m ≈ 4.5% annualised incl. fees and the pre-June margin.')
    S('db_rcf', '  RCF / EIB drawn (€200m RCF to Jun-2029 + €140m EIB; plug to minimum cash)', 'sched', 'm1', data='rcf_drawn', bs=True,
      he=lambda: f'=MAX(0,{B6("db_rcf")}+{V("db_mincash")}-{V("db_cashpre")})', ae=lambda: f'=MAX(0,{P("db_rcf")}+{V("db_mincash")}-{V("db_cashpre")})',
      note='Drawn when cash before revolver flows would fall below the minimum; repaid first when cash exceeds it. Undrawn at 30-Jun-26.')
    S('db_rcf_r', '  RCF / EIB rate %', 'sched', 'pct', he_in=V0['rcf_rate'], ae_in=V0['rcf_rate'], note='RCF 3M Euribor + 0.75% (1.0–1.5x grid); EIB illustrative fixed 4.08% / EUR3M + 1.20%.')
    S('db_oth', '  Other loans (Photonis France, Phasics, Xenics; amortising)', 'sched', 'm1', bs=True, hist=lambda: f'=IF(ISNUMBER({V("bs_cb")}),{V("bs_ncb")}+{V("bs_cb")}-N({V("db_tlb")})-N({V("db_rcf")}),"")',
      he=lambda: f'={B6("db_oth")}-0.3', ae=lambda: f'=MAX(0,{P("db_oth")}-1.0)', note='€4.6m at 30-Jun-26 (incl. the €7.8m Brive extension loan at 3.30% drawing down); ~€1m p.a. repayments assumed.')
    S('db_oth_r', '  Other loans rate %', 'sched', 'pct', he_in=V0['oth_rate'], ae_in=V0['oth_rate'])
    S('db_mincash', '  Minimum cash balance (€m)', 'sched', 'm1', he_in=V0['min_cash'], ae_in=V0['min_cash'], note='Cash has run at €68–117m since the IPO; €60m operating minimum assumed.')
    S('db_cashpre', '  Cash before revolver draw / repayment (€m)', 'sched', 'm1',
      he=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_eq")}+{V("cf_div")}+({V("db_tlb")}-{B6("db_tlb")}-{V("db_accr")})+({V("db_oth")}-{B6("db_oth")})+{V("cf_int")}+{V("cf_lease")}+{V("cf_ofin")}+N({V("cf_fx")})',
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_eq")}+{V("cf_div")}+({V("db_tlb")}-{P("db_tlb")}-{V("db_accr")})+({V("db_oth")}-{P("db_oth")})+{V("cf_int")}+{V("cf_lease")}+{V("cf_ofin")}+N({V("cf_fx")})',
      note='Opening cash + all cash flows except the revolver movement (TLB accretion is non-cash and excluded).')
    S('db_flow', '  Net borrowings drawn (repaid) in the cash flow (€m)', 'sched', 'm1',
      he=lambda: f'=({V("db_rcf")}-{B6("db_rcf")})+({V("db_oth")}-{B6("db_oth")})+({V("db_tlb")}-{B6("db_tlb")}-{V("db_accr")})',
      ae=lambda: f'=({V("db_rcf")}-{P("db_rcf")})+({V("db_oth")}-{P("db_oth")})+({V("db_tlb")}-{P("db_tlb")}-{V("db_accr")})')
    S('db_int', '  Cost of net debt (interest on opening TLB, revolver, other loans and leases)', 'sched', 'm1',
      ae=lambda: f'={P("db_tlb")}*{V("db_tlb_r")}+{P("db_rcf")}*{V("db_rcf_r")}+{P("db_oth")}*{V("db_oth_r")}+{P("ls_ll")}*{V("ls_rate")}')
    S('db_head', '  Memo: undrawn RCF + EIB headroom (€m; €340m commitments)', 'sched', 'm1', he=lambda: f'=340-{V("db_rcf")}', ae=lambda: f'=340-{V("db_rcf")}',
      note='Negative = financing assumption beyond the committed lines (would need new debt).')
    S('db_gross', '  Gross financial debt incl. leases (€m)', 'sched', 'm1', hist=lambda: f'=IF(ISNUMBER({V("bs_ncb")}),{V("bs_ncb")}+{V("bs_cb")}+{V("bs_ncll")}+{V("bs_cll")},"")',
      fc=lambda: f'={V("db_tlb")}+{V("db_rcf")}+{V("db_oth")}+{V("ls_ll")}')
    S('db_nd', '  Net debt (company definition: financial liabilities incl. leases − cash; €m)', 'sched', 'm1', all=lambda: f'=IF(ISNUMBER({V("db_gross")}),{V("db_gross")}-{V("bs_cash")},"")')
    S('db_nd_pub', '  Memo: net debt as published', 'memo', 'm1', data='nd_pub', bs=True)
    S('db_nd_chk', '  Check: model vs published net debt (should be 0; ±1.0: the company nets derivative instruments and accrued interest receivable; from 2024, the pre-IPO definition included derivatives)', 'check', 'm1',
      hist=lambda: (f'=IF(ISNUMBER({V("db_nd_pub")}),IF(ABS({V("db_nd")}-{V("db_nd_pub")})<=1.0,0,ROUND({V("db_nd")}-{V("db_nd_pub")},2)),"")' if CTX.col.year >= 2024 else None))
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive instruments (m shares; LTIP performance shares, ExoShare matching)', 'sched', 'm2', he_in=V0['dil'], ae_in=V0['dil'],
      note='LTIP 2025-26 (216,750) + LTIP 2026-28 (197,000) ≈ 0.41m; the company reports diluted = basic (immaterial).')
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.08)
    S('ls_yield', '  Interest income yield on opening cash %', 'sched', 'pct', he_in=V0['cash_yield'], ae_in=V0['cash_yield'], note='FY25 financial income on investments €2.8m on ~€90m average cash.')
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on Adjusted EBIT less share-based payments and one-offs; invested capital incl. leases and goodwill)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT less share-based payments and non-recurring costs (= operating profit + PPA amortisation + impairment + other income/expenses)', 'line', 'm1', ann=True,
      all=lambda: f'=IF(ISNUMBER({V("r_ebit")}),{V("r_ebit")}-{V("d_sbc")}-{V("d_nonrec")},"")')
    S('ra_t', 'Tax rate (statutory 25% where the effective rate is distorted)', 'line', 'pct', ann=True,
      all=lambda: f'=IF(AND(ISNUMBER({V("is_etr")}),{V("is_etr")}>0.15,{V("is_etr")}<0.35),{V("is_etr")},0.25)')
    S('ra_nopat', 'NOPAT = (Adjusted EBIT − SBC − one-offs) × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = equity + net debt incl. leases', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Equity', 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),{V("bs_teq")},"n/a")')
    S('ra_nd', '  Net debt incl. leases', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("db_nd")}+0,"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = (Adjusted EBIT − SBC − one-offs) / revenue', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = revenue / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition (excl. goodwill and acquired / capitalised intangibles)', 'sub', 'gen')
    S('rn_nopat', 'NOPAT', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm1', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_cash', '  − Cash', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-{V("bs_cash")},"n/a")')
    S('rn_gw', '  − Goodwill and intangible assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-({V("bs_gw")}+{V("bs_int")}),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (payables, other current liabilities)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-({V("bs_ap")}+{V("bs_ocl")}),"n/a")')
    S('rn_nta', '  = Net tangible operating assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / net tangible operating assets', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")',
      note='Goodwill (€233m) and intangibles (€197m) are half the balance sheet (2021 HLD buy-out PPA and bolt-ons), so tangible returns are far above ROIC.')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net profit', 'line', 'm1', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', 'Equity', 'line', 'm1', ann=True, all=lambda: f'={V("ra_eq")}')
    S('roe', 'ROE = net profit / equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt incl. leases (company definition)', 'line', 'm1', all=lambda: f'=IFERROR({V("db_nd")}+0,"n/a")')
    S('lv_eb', 'Adjusted EBITDA (LTM in half-year columns)', 'line', 'm1',
      all=lambda: ((f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+N({PH("r_adj")}),"n/a")' if CTX.col.prevh else '="n/a"') if CTX.col.h else f'=IFERROR({V("r_adj")}+0,"n/a")'))
    S('lv_x', 'Net debt / Adjusted EBITDA (x)', 'total', 'x2', all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")',
      note='Company leverage uses pro forma Adjusted EBITDA (acquisitions annualised): 1.2x at 30-Jun-26, 1.3x at 31-Dec-25. Covenant ≤ 3.0x; company says leverage may temporarily reach ~2x for M&A.')
    S('lv_pub', '  Memo: leverage ratio as published (x; pro forma Adjusted EBITDA)', 'memo', 'x2', data='lev_pub', bs=True)
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price (€, Euronext Paris: EXENS) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m; shares outstanding net of treasury + dilutive instruments)', 'line', 'm2', e26=lambda: f'={V("bb_end")}+N({V("ds_dil")})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (€m)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt incl. lease liabilities (€m; company definition)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_ndx', 'Net debt excl. lease liabilities (€m; DCF bridge — UFCF deducts lease payments)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("db_nd")}),{V("db_nd")}-{V("ls_ll")},"")')
    S('v_oth', 'Other debt-like items (NVLS minority put, contingent consideration; €m)', 'line', 'm', e26_in=6.2, ae_in=6.2,
      note='30-Jun-26: NVLS 15% put (~€2.4m, exercisable H1-2027) and contingent consideration liabilities €3.8m (Note 26). No non-controlling interests.')
    S('v_ev', 'Enterprise value (€m; incl. leases)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_oth")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_oth")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / revenue', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted EBIT', lambda: f'=IFERROR({V("v_ev")}/{V("r_ebit")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (IFRS diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (net profit excl. PPA & impairment per diluted share)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield (DPS declared for the year)', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
