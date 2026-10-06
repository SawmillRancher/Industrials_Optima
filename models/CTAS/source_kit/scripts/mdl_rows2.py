"""Row definitions part 2: cost drivers, consolidated income statement, EBITDA & adjusted EPS bridges, growth & margins."""
from mdl_core import Row, BYNAME, prior_year
import curated as C

def build_part2(S, H, X):
    def hv(*keys, scale=1.0, neg=False):
        def f(p):
            h = H.get(p.name, {})
            for k in keys:
                v = h.get(k)
                if isinstance(v, (int, float)):
                    return (-v if neg else v) * scale
            return None
        return f
    def yoy(k):
        def f(p):
            if prior_year(p) is None: return None
            return '=IF(AND(ISNUMBER({%s}),ISNUMBER({%s@py})),IFERROR({%s}/{%s@py}-1,""),"")' % (k, k, k, k)
        return f
    def ratio(n, d):
        return '=IF(AND(ISNUMBER({%s}),ISNUMBER({%s})),IFERROR({%s}/{%s},""),"")' % (n, d, n, d)
    def has(p, k='rev'): return H.get(p.name, {}).get(k) is not None
    def hf(tpl, k='rev'):
        return lambda p: tpl if has(p, k) else None
    SUMQ = lambda k: '=SUM({%s@q1},{%s@q2},{%s@q3},{%s@q4})' % (k, k, k, k)
    SC = X['scn']
    add = S.add
    fcf = lambda tpl: dict(fq=tpl, f27=tpl, fa=tpl)

    # ---------------- cost drivers
    add(Row(None, 'Cost drivers & D&A', 'sub', note='COST DRIVERS — inputs that drive forecast cost lines'))
    add(Row('da_leg', '  D&A — legacy Cintas (depreciation + amortization of intangibles & capitalized contract costs)', 'line', 'n1',
            h=lambda p: (H[p.name]['cf_dep'] + H[p.name].get('cf_amort', 0)) if 'cf_dep' in H.get(p.name, {}) else None,
            fq='={leg_rev}*{da_pct@$P:FY2027Q1}', f27=SUMQ('da_leg'), fa='={leg_rev}*{da_pct}',
            note='Historical = cash-flow statement depreciation + amortization (intangibles; capitalized contract costs from FY2019, ASC 606). Q2–Q4/27E at the Q1/27 ratio; FY28E+ % of legacy revenues.'))
    add(Row('da_pct', '  D&A (legacy) % of legacy revenues', 'pct', 'p1', h=lambda p: '=IFERROR({da_leg}/{leg_rev},"")' if has(p) else None,
            f27='=IFERROR({da_leg}/{leg_rev},"")', fa='={da_pct_in@abs}', note='FY2026 4.6%; Q1/27 4.2% → 4.3% input FY28E+ (capex intensity ~3.5–4% of revenue).'))
    add(Row('sbc_pct', '  Stock-based compensation % of revenues', 'pct', 'p1', h=lambda p: '=IFERROR({is_sbc}/{is_rev},"")' if has(p, 'cf_sbc') else None,
            fq='={sbc_pct@$P:FY2027Q1}', f27='={sbc_pct@$P:FY2027Q1}', fa='={sbc_pct@pa}'))
    S.blank()

    # ---------------- income statement
    add(Row(None, 'CONSOLIDATED STATEMENT OF INCOME (US GAAP; as reported — continuing operations from FY2015)', 'sec', note='CONSOLIDATED IS — forecast logic'))
    add(Row('is_rev', 'Total revenue', 'total', 'n1', h=hv('rev'), **fcf('={grp_rev}'), cagr=True, note='Forecast linked to the segment build (incl. UniFirst from closing and future M&A).'))
    add(Row('is_rev_u', '  of which: uniform rental & facility services (legacy "rentals" / "rental uniforms & ancillary products")', 'line', 'n1', h=hv('rev_urfs_line'),
            **fcf('={urfs_rev}+{unf_rev}*{unf_rent_sh@abs}'), note='UniFirst U&F Service Solutions + Specialty Garments ≈ 95% of its revenue mapped to this line; future M&A to "other".'))
    add(Row('is_rev_o', '  of which: other (first aid & safety, fire protection, uniform direct sale; legacy "other services")', 'line', 'n1', h=hv('rev_other_line'), **fcf('={is_rev}-{is_rev_u}')))
    add(Row('is_cogs', 'Cost of sales (total)', 'line', 'n1', h=lambda p: (H[p.name]['cogs_urfs'] + H[p.name]['cogs_other']) if has(p) else None,
            **fcf('={is_rev}-{grp_gm}'), note='Forecast = revenues − segment-build gross margin.'))
    add(Row('is_cogs_u', '  of which: cost of uniform rental & facility services', 'line', 'n1', h=hv('cogs_urfs'), level=1))
    add(Row('is_cogs_o', '  of which: cost of other', 'line', 'n1', h=hv('cogs_other'), level=1))
    add(Row('is_gm', 'Gross margin', 'key', 'n1', h=hf('={is_rev}-{is_cogs}'), **fcf('={is_rev}-{is_cogs}'), cagr=True))
    add(Row('is_gmp', '  Gross margin %', 'pct', 'p1', h=hf(ratio('is_gm', 'is_rev')), **fcf(ratio('is_gm', 'is_rev'))))
    add(Row('is_sga', 'Selling & administrative expenses', 'line', 'n1', h=hv('sga'),
            fq='=SUM({urfs_sga},{fas_sga},{oth_sga},{unf_sga})', f27='=SUM({urfs_sga},{fas_sga},{oth_sga},{unf_sga})',
            fa='=SUM({urfs_sga},{fas_sga},{oth_sga},{unf_sga},{ma_sga})',
            note='Includes (historically) a $40m one-time employee payment (Q3/18) and gains on operating-asset sales / equity-method transactions (FY21–22) — adjusted in the bridges below.'))
    add(Row('is_trans', 'Acquisition transaction & integration expenses (G&K FY2017–19; UniFirst FY2026+)', 'line', 'n1', h=hv('sp_trans'), **fcf('={unf_cost}'),
            note='Separate income-statement line as reported. Q3/26 UniFirst costs ($1.1m) were within S&A as first reported.'))
    add(Row('is_spo', 'Restructuring, impairment, legal settlements & Shred-it transaction charges', 'line', 'n1', h=hv('sp_other_op'), **fcf('=0'),
            note='FY2009: restructuring $10.2m + asset impairment $48.9m; FY2010: legal settlements $23.5m, restructuring reversal ($2.9m); FY2014: Shredding transaction costs $28.5m + impairment $16.1m.'))
    add(Row('is_oi', 'Operating income', 'total', 'n1', h=hf('={is_gm}-{is_sga}-{is_trans}-{is_spo}'), **fcf('={is_gm}-{is_sga}-{is_trans}-{is_spo}'), cagr=True))
    add(Row('is_oim', '  Operating margin %', 'pct', 'p1', h=hf(ratio('is_oi', 'is_rev')), **fcf(ratio('is_oi', 'is_rev'))))
    add(Row('is_nonop', 'Gains on Shredding deconsolidation, sale of equity/cost-method investments & other (gain = +)', 'line', 'n1', h=hv('nonop_gain'), **fcf('=0'),
            note='Below operating income as reported: FY2014 Shredding deconsolidation gain $106.4m; FY2015 equity-method share sale $21.7m and deconsolidation true-ups; FY2019 cost-method investment sale $69.4m.'))
    add(Row('is_ii', 'Interest income', 'line', 'n1', h=hv('int_inc'),
            fq='={is_ii@$P:FY2027Q1}', f27=SUMQ('is_ii'), fa='={debt_ii}', note='Q2–Q4/27E at the Q1/27 run-rate. FY28E+: yield on opening cash (debt schedule).'))
    add(Row('is_ie', 'Interest expense', 'line', 'n1', h=hv('int_exp'),
            fq='=({g_int@abs}+SUM({is_ii@q1},{is_ii@q2},{is_ii@q3},{is_ii@q4})-{is_ie@q1})/3+{unf_debt@abs}*{unf_rate@abs}*{unf_days}/365',
            f27=SUMQ('is_ie'), fa='={debt_ie}',
            note='Q2–Q4/27E: FY27 guidance interest, net $103.0m (incl. bridge-fee amortization) spread evenly + UniFirst acquisition debt $2.8bn × 5.0% (424B3 pro forma assumption) from closing. FY28E+: debt schedule.'))
    add(Row('is_pbt', 'Income before income taxes', 'key', 'n1', h=hf('={is_oi}+{is_nonop}+{is_ii}-{is_ie}'), **fcf('={is_oi}+{is_nonop}+{is_ii}-{is_ie}'), cagr=True))
    add(Row('is_tax', 'Income taxes', 'line', 'n1', h=hv('tax'), fq='={is_pbt}*{is_etr}', f27=SUMQ('is_tax'), fa='={is_pbt}*{is_etr}',
            note='FY2018: Tax Act revaluation benefit (~$175m in Q3/18). Q2–Q4/27E at the FY27 guidance ETR 20.4%; FY28E+ input.'))
    add(Row('is_etr', '  Effective tax rate', 'pct', 'p1', h=hf(ratio('is_tax', 'is_pbt')), fq='={g_etr@abs}', f27=ratio('is_tax', 'is_pbt'), fa='={etr_in@abs}',
            note='FY27 guidance 20.4% (FY26 20.2%; discrete stock-comp benefits). FY28E+: 21.0% input (UniFirst earnings taxed nearer 25%).'))
    add(Row('is_eqat', 'Equity-method investment (Shred-it) income / (loss), net of tax', 'line', 'n1', h=hv('eq_at'), **fcf('=0'), level=1))
    add(Row('is_nic', 'Income from continuing operations', 'key', 'n1', h=hf('={is_pbt}-{is_tax}+{is_eqat}'), **fcf('={is_pbt}-{is_tax}+{is_eqat}'), cagr=True))
    add(Row('is_disc', 'Income (loss) from discontinued operations, net of tax (document management / Shred-it, FY2015–2020)', 'line', 'n1', h=hv('disc'), **fcf('=0')))
    add(Row('is_ni', 'Net income', 'total', 'n1', h=hf('={is_nic}+{is_disc}'), **fcf('={is_nic}+{is_disc}'), cagr=True))
    add(Row('chk_ni', '  Check: net income vs reported (should be 0)', 'check', 'n1', h=hf('=ROUND({is_ni}-{is_ni_rep},1)')))
    add(Row('is_ni_rep', '  Memo: net income as reported', 'memo', 'n1', h=hv('ni'), level=1))
    add(Row('is_da', '  Memo: depreciation & amortization (total; cash-flow statement)', 'memo', 'n1',
            h=lambda p: (H[p.name]['cf_dep'] + H[p.name].get('cf_amort', 0)) if 'cf_dep' in H.get(p.name, {}) else None,
            fq='={da_leg}+{unf_da}', f27=SUMQ('is_da'), fa='={da_leg}+{unf_da}+{ma_da}',
            note='Forecast = legacy D&A + UniFirst D&A (incl. PPA) + future-M&A D&A.'))
    add(Row('is_sbc', '  Memo: stock-based compensation', 'memo', 'n1', h=hv('cf_sbc'), fq='={is_rev}*{sbc_pct}', f27=SUMQ('is_sbc'), fa='={is_rev}*{sbc_pct}'))
    add(Row(None, '(Earnings per share — restated for the 4-for-1 stock split effective 11-Sep-2024)', 'head'))
    add(Row('sh_b', '  Weighted-average basic shares (m)', 'line', 'n1', h=hv('sh_basic'),
            fq='={sh_d}-({sh_d@$P:FY2027Q1}-{sh_b@$P:FY2027Q1})', f27='=AVERAGE({sh_b@q1},{sh_b@q2},{sh_b@q3},{sh_b@q4})', fa='={sh_d}-{dil_sec}',
            note='Pre-split periods × 4.'))
    add(Row('sh_d', '  Weighted-average diluted shares (m)', 'line', 'n1', h=hv('sh_dil'),
            fq='={sh_d@$P:FY2027Q1}-{bb_q_sh@abs}*(COLUMN()-COLUMN({sh_d@$P:FY2027Q1}))+{unf_sh@abs}*{unf_days}/IF(COLUMN()=COLUMN({sh_d@$P:FY2027Q2}),91,IF(COLUMN()=COLUMN({sh_d@$P:FY2027Q3}),90,92))',
            f27='=AVERAGE({sh_d@q1},{sh_d@q2},{sh_d@q3},{sh_d@q4})', fa='=AVERAGE({bb_beg},{bb_end})+{dil_sec}',
            note='Q2–Q4/27E: Q1/27 diluted shares − ~1.0m per quarter net buybacks ($545m repurchased in Q1 and to 22-Sep) + 14.07m UniFirst consideration shares time-weighted from closing. FY28E+: average shares outstanding + dilutive securities.'))
    add(Row('eps_b', 'EPS – basic ($)', 'line', 'n2', h=hf('=IFERROR({is_ni}/{sh_b},"")'), **fcf('=IFERROR({is_ni}/{sh_b},"")')))
    add(Row('eps_d', 'EPS – diluted ($)', 'total', 'n2', h=hf('=IFERROR({is_ni}/{sh_d},"")'), **fcf('=IFERROR({is_ni}/{sh_d},"")'), cagr=True,
            note='Computed as net income / weighted diluted shares; Cintas uses the two-class method, so ±$0.01–0.02 differences vs reported EPS are possible (memo rows show reported EPS).'))
    add(Row('eps_dc', 'EPS – diluted, continuing operations ($)', 'line', 'n2', h=hf('=IFERROR({is_nic}/{sh_d},"")'), **fcf('=IFERROR({is_nic}/{sh_d},"")'), cagr=True))
    add(Row('eps_dc_g', '  EPS – diluted, continuing operations y/y %', 'yoy', 'p1', h=yoy('eps_dc'),
            fq='=IFERROR({eps_dc}/{eps_dc@py}-1,"")', f27='=IFERROR({eps_dc}/{eps_dc@pa}-1,"")', fa='=IFERROR({eps_dc}/{eps_dc@pa}-1,"")'))
    add(Row('eps_d_rep', '  Memo: EPS – diluted as reported ($, split-adjusted)', 'memo', 'n2', h=hv('eps_dil'), level=1))
    add(Row('eps_dc_rep', '  Memo: EPS – diluted, continuing operations as reported ($, split-adjusted)', 'memo', 'n2', h=hv('eps_dil_cont'), level=1))
    def dps_h(p):
        if p.is_q: return C.dps_q(p.fy, p.q) if (p.fy, p.q) in C.DPS_Q_RAW or (p.fy, p.q) in C.DPS_Q_POST else None
        return C.dps_annual(p.fy)
    add(Row('dps', '  Dividends declared per share ($)', 'line', 'n2', h=dps_h,
            fq='={dps@$P:FY2027Q1}', f27=SUMQ('dps'), fa='={dps@pa}*(1+{dps_g_in@abs})',
            note='Annual dividend declared in Q2 until FY2020; quarterly from FY2021 (FY2015 incl. $0.2125 special; FY2021 incl. catch-up). Q1/27 $0.52 (+15.6%). FY28E+: +12% p.a. input.'))
    add(Row('dps_g', '  Dividend per share growth %', 'yoy', 'p1', h=yoy('dps'), f27='=IFERROR({dps}/{dps@pa}-1,"")', fa='=IFERROR({dps}/{dps@pa}-1,"")'))
    S.blank()

    # ---------------- EBITDA bridge
    add(Row(None, 'RECONCILIATION: INCOME FROM CONTINUING OPERATIONS → EBITDA → ADJUSTED EBITDA (model definition; adjusting items = company-identified items)', 'sec',
            note='ADJUSTED EBITDA — Cintas does not publish Adjusted EBITDA; EBITDA was published FY2012–14 (Debt/EBITDA). Adjusting items = items the company excluded from adjusted EPS.'))
    add(Row('e_nic', 'Income from continuing operations (GAAP)', 'line', 'n1', h=hf('={is_nic}'), **fcf('={is_nic}')))
    add(Row('e_tax', '  (+) Income taxes', 'line', 'n1', h=hf('={is_tax}'), **fcf('={is_tax}')))
    add(Row('e_ie', '  (+) Interest expense', 'line', 'n1', h=hf('={is_ie}'), **fcf('={is_ie}')))
    add(Row('e_ii', '  (−) Interest income', 'line', 'n1', h=hf('=-{is_ii}'), **fcf('=-{is_ii}')))
    add(Row('e_da', '  (+) Depreciation & amortization', 'line', 'n1', h=lambda p: '={is_da}' if has(p, 'cf_dep') else None, **fcf('={is_da}')))
    add(Row('e_ebitda', '  = EBITDA', 'total', 'n1', h=lambda p: '=SUM({e_nic},{e_tax},{e_ie},{e_ii},{e_da})' if has(p, 'cf_dep') else None,
            **fcf('=SUM({e_nic},{e_tax},{e_ie},{e_ii},{e_da})'), cagr=True))
    add(Row('e_trans', '  (+) Acquisition transaction & integration expenses (G&K; UniFirst)', 'line', 'n1', h=hf('={is_trans}'), **fcf('={is_trans}')))
    add(Row('e_spo', '  (+) Restructuring, impairment, legal settlements & Shred-it transaction charges', 'line', 'n1', h=hf('={is_spo}'), **fcf('={is_spo}')))
    add(Row('e_inv', '  (+) Inventory valuation charge in cost of sales (FY2009)', 'line', 'n1', h=lambda p: C.INV_CHARGE.get(p.name, 0 if has(p) else None), **fcf('=0')))
    add(Row('e_sga', '  (+/−) Items within S&A: one-time employee payment (Q3/18); (gains) on operating-asset sales & equity-method transactions (FY21–22)', 'line', 'n1',
            h=lambda p: C.SGA_ITEMS.get(p.name, 0 if has(p) else None), **fcf('=0')))
    add(Row('e_nonop', '  (−) Non-operating gains (Shredding deconsolidation, investment sales)', 'line', 'n1', h=hf('=-{is_nonop}'), **fcf('=-{is_nonop}')))
    add(Row('e_eqat', '  (−) Equity-method (Shred-it) results, net of tax', 'line', 'n1', h=hf('=-{is_eqat}'), **fcf('=-{is_eqat}')))
    add(Row('e_adj', '  Total adjusting items', 'line', 'n1', h=hf('=SUM({e_trans},{e_spo},{e_inv},{e_sga},{e_nonop},{e_eqat})'), **fcf('=SUM({e_trans},{e_spo},{e_inv},{e_sga},{e_nonop},{e_eqat})')))
    add(Row('adj_ebitda', '  = Adjusted EBITDA (model bridge)', 'total', 'n1', h=lambda p: '={e_ebitda}+{e_adj}' if has(p, 'cf_dep') else None, **fcf('={e_ebitda}+{e_adj}'), cagr=True,
            note='Historical bridge rebuilt from the reported income statement and company-identified items; forecast = EBITDA + UniFirst transaction/integration costs.'))
    add(Row('adj_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'p1', h=lambda p: ratio('adj_ebitda', 'is_rev') if has(p, 'cf_dep') else None, **fcf(ratio('adj_ebitda', 'is_rev'))))
    add(Row('e_pub', '  Company-published EBITDA (FY2012–14 Debt/EBITDA computation: net income + interest expense + taxes + D&A)', 'memo', 'n1', h=lambda p: C.EBITDA_PUB.get(p.name)))
    add(Row('e_chk', '  Check: model EBITDA (company basis, before interest income) vs company-published (should be 0)', 'check', 'n1',
            h=lambda p: '=IF(ISNUMBER({e_pub}),ROUND({e_ebitda}-{e_ii}-{e_pub},1),"n/p")' if has(p, 'cf_dep') else None))
    def defb(p):
        n = p.name
        if n in C.EBITDA_PUB: return 'EBITDA (Debt/EBITDA)'
        if n in C.ADJ_EPS_RAW: return 'Adj. EPS items'
        return None
    add(Row('e_def', '  Definition basis (company non-GAAP measure published in period)', 'def', 'gen', h=defb,
            note='Cintas\' core non-GAAP measures are organic growth and free cash flow; adjusted EPS is published only when special items occur (FY2009–11, FY2014–15, FY2017–23, FY2026+).'))
    add(Row(None, 'To adjusted EBIT:', 'head'))
    add(Row('e_mda', '  (−) Depreciation & amortization', 'line', 'n1', h=lambda p: '=-{e_da}' if has(p, 'cf_dep') else None, **fcf('=-{e_da}')))
    add(Row('adj_ebit', '  = Adjusted EBIT (model; = adjusted operating income)', 'total', 'n1', h=lambda p: '={adj_ebitda}+{e_mda}' if has(p, 'cf_dep') else None, **fcf('={adj_ebitda}+{e_mda}'), cagr=True))
    add(Row('adj_ebit_m', '  Adjusted EBIT margin %', 'pct', 'p1', h=lambda p: ratio('adj_ebit', 'is_rev') if has(p, 'cf_dep') else None, **fcf(ratio('adj_ebit', 'is_rev'))))
    add(Row('adj_ebitda_pf', '  Memo: Adjusted EBITDA pro forma — UniFirst full year (FY2027E), for leverage & valuation', 'memo', 'n1',
            h=lambda p: '={adj_ebitda}' if (not p.is_q and has(p, 'cf_dep')) else None,
            f27='={adj_ebitda}+{unf_rr}*({unf_gmp}-{unf_sgap}+{unf_da_pct})*(365-{unf_days})/365*{unf_on}', fa='={adj_ebitda}',
            note='FY2027E adds UniFirst pre-closing days at its standalone margin (no synergies) so leverage and valuation are on a full-year basis.'))
    S.blank()

    # ---------------- adjusted EPS bridge
    add(Row(None, 'RECONCILIATION: GAAP INCOME FROM CONTINUING OPERATIONS / DILUTED EPS → ADJUSTED DILUTED EPS (company definition)', 'sec',
            note='ADJUSTED EPS — company publishes adjusted EPS only when special items occur; FY27 guidance is adjusted diluted EPS excl. UniFirst transaction costs.'))
    add(Row('a_nic', 'Income from continuing operations (GAAP)', 'line', 'n1', h=hf('={is_nic}'), **fcf('={is_nic}')))
    add(Row('a_items', '  (+) Adjusting items, pre-tax (as in the Adjusted EBITDA bridge, excl. after-tax equity-method results)', 'line', 'n1',
            h=hf('=SUM({e_trans},{e_spo},{e_inv},{e_sga},{e_nonop})'), **fcf('=SUM({e_trans},{e_spo},{e_inv},{e_sga},{e_nonop})')))
    add(Row('a_rate', '  Tax rate applied to adjustments', 'pct', 'p1', h=hf('=IFERROR(MIN(MAX({is_etr},0.15),0.4),0.25)'), **fcf('={adj_tax_in@abs}'),
            note='Historical: period ETR bounded 15–40%. Forecast: 25% (424B3 blended statutory rate; ~70% of transaction costs deductible).'))
    add(Row('a_taxeff', '  (−) Income tax effect of adjusting items', 'line', 'n1', h=hf('=-{a_items}*{a_rate}'), **fcf('=-{a_items}*{a_rate}')))
    add(Row('a_eqat', '  (−) Equity-method (Shred-it) results, net of tax', 'line', 'n1', h=hf('={e_eqat}'), **fcf('={e_eqat}')))
    add(Row('a_taxd', '  (−) Discrete tax items excluded by the company (Tax Act revaluation, Q3/18)', 'line', 'n1', h=lambda p: C.TAX_ITEMS.get(p.name, 0 if has(p) else None), **fcf('=0')))
    add(Row('a_other', '  (+/−) Other company-defined items & per-share rounding (periods with published adjusted EPS)', 'line', 'n1', h=X['a_other'], **fcf('=0'),
            note='Plug to the published figure where the company published adjusted EPS (e.g., ASU 2016-09 benefit excluded in Q3/17; equity-method tax benefit Q3/22; rounding).'))
    add(Row('a_ni', '  = Adjusted income from continuing operations (model)', 'total', 'n1', h=hf('=SUM({a_nic},{a_items},{a_taxeff},{a_eqat},{a_taxd},{a_other})'),
            **fcf('=SUM({a_nic},{a_items},{a_taxeff},{a_eqat},{a_taxd},{a_other})'), cagr=True))
    add(Row('a_sh', '  Weighted-average diluted shares (m)', 'line', 'n1', h=hf('={sh_d}'), **fcf('={sh_d}')))
    add(Row('a_eps', 'Adjusted EPS – diluted ($) (model)', 'total', 'n2', h=hf('=IFERROR({a_ni}/{a_sh},"")'), **fcf('=IFERROR({a_ni}/{a_sh},"")'), cagr=True))
    add(Row('a_pub', '  Company-published adjusted EPS – diluted ($, split-adjusted)', 'memo', 'n2', h=lambda p: C.adj_eps(p.name)))
    add(Row('a_chk', '  Check: model vs company-published adjusted EPS (should be 0.00)', 'check', 'n2', h=hf('=IF(ISNUMBER({a_pub}),ROUND({a_eps}-{a_pub},2),"n/p")')))
    add(Row('a_def', '  Definition basis (company adjusted EPS, where published)', 'def', 'gen',
            h=lambda p: (C.ADJ_EPS_RAW[p.name][2][:60] if p.name in C.ADJ_EPS_RAW else None)))
    add(Row('a_leg', '  Memo: legacy adjusted EPS ex-UniFirst on guidance basis (FY27E; vs guidance end-point)', 'memo', 'n2',
            f27='=({leg_adj_oi}-{g_int@abs})*(1-{g_etr@abs})/{g_shares@abs}', note='Should equal the guidance end-point for the active scenario (calibration check).'))
    S.blank()

    # ---------------- growth & margins
    add(Row(None, 'GROWTH & MARGINS', 'sec', note='GROWTH & MARGINS (consolidated) — forecast outputs'))
    gm = [
        ('gm_rev', '  Revenues y/y %', 'yoy', '{is_rev}'),
        ('gm_org', '  Organic revenue growth % (company; forecast = legacy segment growth)', 'yoy', None),
        ('gm_urfs', '  UR&FS revenues y/y %', 'yoy', '{urfs_rev}'),
        ('gm_ebitda', '  Adjusted EBITDA y/y %', 'yoy', '{adj_ebitda}'),
        ('gm_oi', '  Operating income y/y %', 'yoy', '{is_oi}'),
        ('gm_ni', '  Net income y/y %', 'yoy', '{is_ni}'),
        ('gm_aeps', '  Adjusted EPS y/y %', 'yoy', '{a_eps}'),
    ]
    for k, lab, st, ref in gm:
        if ref is None:
            add(Row(k, lab, st, 'p1', h=lambda p: '={og_org}' if p.name in C.ORG else None,
                    fq='=IFERROR({leg_rev}/{leg_rev@py}-1-IF(COLUMN()=COLUMN({leg_rev@$P:FY2027Q1}),{wd_q1},0),"")', f27='=IFERROR({leg_rev}/{leg_rev@pa}-1-{wd_q1@P:FY2027Q1}/4,"")',
                    fa='=IFERROR({leg_rev}/{leg_rev@pa}-1,"")'))
            continue
        k0 = ref.strip('{}')
        add(Row(k, lab, st, 'p1', h=yoy(k0), fq='=IFERROR(%s/{%s@py}-1,"")' % (ref, k0), f27='=IFERROR(%s/{%s@pa}-1,"")' % (ref, k0), fa='=IFERROR(%s/{%s@pa}-1,"")' % (ref, k0)))
    add(Row('gm_gmp', '  Gross margin %', 'pct', 'p1', h=hf('={is_gmp}'), **fcf('={is_gmp}')))
    add(Row('gm_ebm', '  Adjusted EBITDA margin %', 'pct', 'p1', h=lambda p: '={adj_ebitda_m}' if has(p, 'cf_dep') else None, **fcf('={adj_ebitda_m}')))
    add(Row('gm_inc', '  Incremental adjusted EBITDA margin (Δ EBITDA / Δ revenues, y/y)', 'pct', 'p1',
            h=lambda p: ('=IFERROR(({adj_ebitda}-{adj_ebitda@py})/({is_rev}-{is_rev@py}),"")' if (prior_year(p) is not None and has(prior_year(p), 'cf_dep') and has(p, 'cf_dep')) else None),
            fq='=IFERROR(({adj_ebitda}-{adj_ebitda@py})/({is_rev}-{is_rev@py}),"")', f27='=IFERROR(({adj_ebitda}-{adj_ebitda@pa})/({is_rev}-{is_rev@pa}),"")',
            fa='=IFERROR(({adj_ebitda}-{adj_ebitda@pa})/({is_rev}-{is_rev@pa}),"")'))
    add(Row('gm_oim', '  Operating margin %', 'pct', 'p1', h=hf('={is_oim}'), **fcf('={is_oim}')))
    add(Row('gm_aoim', '  Adjusted operating margin % (adjusted EBIT)', 'pct', 'p1', h=lambda p: '={adj_ebit_m}' if has(p, 'cf_dep') else None, **fcf('={adj_ebit_m}')))
    add(Row('gm_nim', '  Net margin %', 'pct', 'p1', h=hf(ratio('is_ni', 'is_rev')), **fcf(ratio('is_ni', 'is_rev'))))
    add(Row('gm_sga', '  S&A % of revenues', 'pct', 'p1', h=hf(ratio('is_sga', 'is_rev')), **fcf(ratio('is_sga', 'is_rev'))))
    S.blank()
