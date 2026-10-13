"""Row specification of the META Model sheet, part 1 (MLM template layout and process):
Family of Apps advertising (ad impressions x average price per ad) + other revenue (FoA other, Reality Labs) -> segment results ->
KPIs and revenue by geography -> M&A lever -> group total & 2026 guidance calibration (Q3/26E revenue; FY26 total expenses) ->
cost drivers (D&A from the PP&E schedule, share-based compensation, other operating costs, company-quantified one-offs) ->
income statement -> GAAP-to-adjusted bridges -> growth & margins."""
from fw import *

def CH(r):
    return f'CHOOSE(MATCH({SW},{{"Bull","Base","Bear"}},0),${SBULL}${r},${SBASE}${r},${SBEAR}${r})'
def PT(name): return f'${SBASE}${SC[name]}'
SC = {}

def growth(key):
    def f():
        if CTX.col.prior is None: return None
        return f'=IF(AND(ISNUMBER({V(key)}),ISNUMBER({P(key)})),IFERROR({V(key)}/{P(key)}-1,""),"")'
    return f
def ratio(n, d): return lambda: f'=IF(AND(ISNUMBER({V(n)}),ISNUMBER({V(d)})),IFERROR({V(n)}/{V(d)},""),"")'
def incr(n, d):
    def f():
        if CTX.col.prior is None: return None
        return f'=IFERROR(({V(n)}-{P(n)})/({V(d)}-{P(d)}),"")'
    return f
def nsum(keys): return '+'.join(f'N({V(k)})' for k in keys)
def H1(key): return f'SUM({Q1}{R[key]}:{Q2}{R[key]})'      # 1H/26 actual (Q1-Q2/26)
def H1P(key): return f'SUM({PQ1}{R[key]}:{PQ2}{R[key]})'   # 1H/25 actual
def B1(key): return f'{LQ}{R[key]}'                        # 30-Jun-2026 balance / Q2/26 value
def QA(col, key): return f'${col}${R[key]}'
def is_q3(): return CTX.col.q == 3
def ann(): return 1 if CTX.col.q is None else 4
COMPANY_NG = lambda col: col.kind in HISTK and ((col.year == 2012 and col.q is None) or 2013 <= col.year <= 2016)   # company non-GAAP in force

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of the 2026 guidance ranges.'))
    r = 11
    SCEN_ROWS.append((r, 'out_hdr', V0['out_hdr'], 'High', 'Mid', 'Low', V0['out_note'])); r += 1
    for key, lab, (hi, mid, lo), nf, note in V0['outlook']:
        SC[key] = r; SCEN_ROWS.append((r, 'out', lab, hi, mid, lo, note, nf)); r += 1
    r += 1
    SCEN_ROWS.append((r, 'pt_hdr', 'Q3/26E, Q4/26E and FY26 point estimates (all cases)', None, None, None, None)); r += 1
    for key, lab, vals, nf, note in V0['points']:
        SC[key] = r
        SCEN_ROWS.append((r, 'pt', lab, None, vals, None, note, nf)); r += 1
    r += 1
    SC['LEV'] = r
    SCEN_ROWS.append((r, 'lev', '  Maximum net debt / adjusted EBITDA before buybacks (x) — buyback ceiling 2027E+', *V0['lev'], V0['lev_note']))
    r += 2
    for name, lab, dbull, dbear, base, note, nf, clamp in V0['blocks']:
        SCEN_ROWS.append((r, 'blk', lab, dbull, 'Δ →', dbear, note, nf)); hdr = r; r += 1
        SC[name] = {}
        for y, b in zip(range(FYC + 1, FYL + 1), base):
            SC[name][y] = r; SCEN_ROWS.append((r, 'yr', f'  {y}E', hdr, b, clamp, None, nf)); r += 1
    return r

# ====================================================================== row spec
def build_spec(V0):
    S = add
    # ------------------------------------------------------------------ OPERATING BUILD
    S('sec_op', 'OPERATING BUILD — FAMILY OF APPS (ADVERTISING = AD IMPRESSIONS × PRICE PER AD; OTHER REVENUE) · REALITY LABS', 'section',
      note='OPERATING BUILD — modelling logic (advertising = prior-year period × (1 + impressions growth) × (1 + price-per-ad growth); other revenue by line; segment profit; costs built separately below)')
    blank()
    S('adv_hdr', 'Family of Apps — advertising (Facebook, Instagram, Messenger, WhatsApp, Threads)', 'block', note='ADVERTISING — modelling logic')
    S('adv', '  Advertising revenue', 'line_b', 'm', data='adv', flow=True,
      qe=lambda: f'={P("adv")}*(1+{V("adv_g")})', ae=lambda: f'={P("adv")}*(1+{V("adv_g")})',
      note=('History: release reconciliation ("GAAP advertising revenue"; 2009-11 prospectus; segment table from Q4-2021). '
            'Forecast: prior-year period × (1 + ad impressions growth) × (1 + price-per-ad growth).'))
    S('adv_g', '    y/y %', 'growth', 'pct', all=growth('adv'), qe=lambda: f'=(1+{V("impr_g")})*(1+{V("price_g")})-1', ae=lambda: f'=(1+{V("impr_g")})*(1+{V("price_g")})-1')
    S('impr_g', '  Ad impressions delivered y/y % (company-reported, rounded)', 'driver', 'pct', data='impr_g',
      qe=lambda: f'={V("impr_pre")}', ae=lambda: '=' + CH(SC['IMPR'][CTX.col.year]),
      note=('Releases from Q4-2021; before that the 10-Q / 10-K MD&A ("number of ads delivered", 2014-21; Q4 not published, year from the 10-K). '
            'Q3/Q4-26E: Q2/26 y/y held. 2027E+: scenario lever.'))
    S('price_g', '  Average price per ad y/y % (company-reported, rounded)', 'driver', 'pct', data='price_g',
      qe=lambda: f'={V("price_pre")}+{QA(Q3E, "cal_p")}', ae=lambda: '=' + CH(SC['PRICE'][CTX.col.year]),
      note='Not disclosed 2019-Q3 2021 in some quarters. Q3/Q4-26E: Q2/26 y/y + revenue-guidance calibration Δ (solved in Q3, carried into Q4). 2027E+: scenario lever.')
    S('impr_pre', '    Q3/Q4-26E ad impressions growth (Q2/26 y/y, held)', 'driver', 'pct', qe=lambda: f'={QA(Q2, "impr_g")}')
    S('price_pre', '    Q3/Q4-26E price-per-ad growth before calibration (Q2/26 y/y, held)', 'driver', 'pct', qe=lambda: f'={QA(Q2, "price_g")}')
    S('adv_impl', '  Memo: implied advertising growth = (1 + impressions) × (1 + price) − 1', 'memo_calc', 'pct',
      hist=lambda: f'=IF(AND(ISNUMBER({V("impr_g")}),ISNUMBER({V("price_g")})),(1+{V("impr_g")})*(1+{V("price_g")})-1,"")')
    S('adv_res', '  Memo: reported advertising growth − implied (rounding of the published whole-% figures; not a check)', 'memo_calc', 'pct',
      hist=lambda: (f'=IF(AND(ISNUMBER({V("adv_impl")}),ISNUMBER({V("adv_g")})),{V("adv_g")}-{V("adv_impl")},"")' if CTX.col.prior else None))
    S('adv_exfx', '  Memo: advertising revenue excluding foreign-exchange effect (company non-GAAP)', 'memo', 'm', data='adv_exfx', flow=True)
    S('adv_cc', '  Advertising growth at constant currency %', 'growth', 'pct',
      hist=lambda: (f'=IF(AND(ISNUMBER({V("adv_exfx")}),ISNUMBER({P("adv")})),IFERROR({V("adv_exfx")}/{P("adv")}-1,""),"")' if CTX.col.prior else None))
    S('adv_fx', '  FX effect on advertising growth (pp)', 'growth', 'pct',
      hist=lambda: (f'=IF(AND(ISNUMBER({V("adv_cc")}),ISNUMBER({V("adv_g")})),{V("adv_g")}-{V("adv_cc")},"")' if CTX.col.prior else None))
    blank()
    S('oth_hdr', 'Other revenue — FoA other revenue (WhatsApp business messaging, Meta Verified; payments & other fees to 2017) · Reality Labs (Quest, AI glasses)', 'block',
      note='OTHER REVENUE — FoA other revenue and Reality Labs split from 2019 (segment recast in the Q4-2021 release); before that total non-advertising revenue only')
    S('foa_oth', '  Family of Apps other revenue', 'line', 'm', data='foa_oth', flow=True,
      qe=lambda: f'={P("foa_oth")}*(1+{V("foa_oth_g")})', ae=lambda: f'={P("foa_oth")}*(1+{V("foa_oth_g")})')
    S('foa_oth_g', '    y/y %', 'growth', 'pct', all=growth('foa_oth'), qe=lambda: f'=IFERROR({H1("foa_oth")}/{H1P("foa_oth")}-1,0)',
      ae=lambda: '=' + CH(SC['FOTH'][CTX.col.year]), note='Q3/Q4-26E: 1H/26 y/y. 2027E+: scenario lever.')
    S('rl_rev', '  Reality Labs revenue', 'line', 'm', data='rl_rev', flow=True,
      qe=lambda: f'={P("rl_rev")}*(1+{V("rl_rev_g")})', ae=lambda: f'={P("rl_rev")}*(1+{V("rl_rev_g")})')
    S('rl_rev_g', '    y/y %', 'growth', 'pct', all=growth('rl_rev'), qe=lambda: f'=IFERROR({H1("rl_rev")}/{H1P("rl_rev")}-1,0)',
      ae=lambda: '=' + CH(SC['RLREV'][CTX.col.year]), note='Q3/Q4-26E: 1H/26 y/y. 2027E+: scenario lever.')
    S('oth_rev', '  Total non-advertising revenue', 'line_b', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("foa_oth")}),{V("foa_oth")}+{V("rl_rev")},IF(ISNUMBER({V("adv")}),{V("is_rev")}-{V("adv")},""))',
      fc=lambda: f'={V("foa_oth")}+{V("rl_rev")}',
      note='History: FoA other + Reality Labs where the segment split is published; otherwise revenue − advertising (payments and other fees, Oculus hardware).')
    S('oth_rev_g', '    y/y %', 'growth', 'pct', all=growth('oth_rev'))
    S('gc_adv', '  Contribution to revenue growth — advertising (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("adv")}-{P("adv")})/{P("is_rev")},"")' if CTX.col.prior else None))
    S('gc_oth', '  Contribution to revenue growth — other revenue (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("oth_rev")}-{P("oth_rev")})/{P("is_rev")},"")' if CTX.col.prior else None))
    blank()
    S('seg_hdr', 'Segment results — Family of Apps · Reality Labs (first presented in the Q4-2021 release; FY2019-20, Q4-2020 and 2021 quarters recast)', 'block',
      note='SEGMENTS — FoA income = consolidated income from operations − Reality Labs result (forecast)')
    S('foa_rev', '  Family of Apps revenue', 'line_b', 'm', data='foa_rev', flow=True, fc=lambda: f'={V("adv")}+{V("foa_oth")}')
    S('foa_rev_g', '    y/y %', 'growth', 'pct', all=growth('foa_rev'))
    S('foa_oi', '  Family of Apps income from operations', 'line', 'm', data='foa_oi', flow=True, fc=lambda: f'={V("is_oi")}-{V("rl_oi")}',
      note='Forecast: consolidated income from operations − Reality Labs operating loss (FoA carries all one-off items in the forecast).')
    S('foa_m', '  FoA operating margin %', 'pct', 'pct', all=ratio('foa_oi', 'foa_rev'))
    S('rl_oi', '  Reality Labs income (loss) from operations', 'line', 'm', data='rl_oi', flow=True,
      qe=lambda: f'={P("rl_oi")}*IFERROR({H1("rl_oi")}/{H1P("rl_oi")},1)', ae=lambda: '=-' + CH(SC['RLLOSS'][CTX.col.year]),
      note='Q3/Q4-26E: prior-year quarter × 1H/26 ÷ 1H/25 loss ratio. 2027E+: scenario lever (operating loss, $m).')
    S('rl_oi_g', '    y/y %', 'growth', 'pct', all=growth('rl_oi'))
    S('seg_chk_rev', '  Check: segment revenue vs consolidated revenue (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("foa_rev")}),ROUND({V("foa_rev")}+{V("rl_rev")}-{V("is_rev")},1),"")')
    S('seg_chk_oi', '  Check: segment results vs income from operations (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("foa_oi")}),ROUND({V("foa_oi")}+{V("rl_oi")}-{V("is_oi")},1),"")')
    blank()
    S('kpi_hdr', 'People, engagement & productivity (company-reported KPIs)', 'block', note='KPIs — information rows (release text)')
    S('dap', '  Family daily active people (DAP), m (average for the last month of the quarter; from Q4-2019)', 'memo', 'm', data='dap')
    S('dap_g', '    DAP y/y %', 'growth', 'pct', all=growth('dap'))
    S('map_', '  Family monthly active people (MAP), m (Q4-2019 to Q4-2023)', 'memo', 'm', data='map')
    S('dau', '  Facebook daily active users (DAUs), m (to Q4-2023)', 'memo', 'm', data='dau')
    S('mau', '  Facebook monthly active users (MAUs), m (to Q4-2023)', 'memo', 'm', data='mau')
    S('rpd', '  Revenue per DAP — annualised, on period DAP ($)', 'memo_calc', 'ps',
      hist=lambda: f'=IF(ISNUMBER({V("dap")}),IFERROR({V("is_rev")}*{ann()}/{V("dap")},""),"")')
    S('hc', '  Headcount (period end)', 'memo', 'm', data='headcount')
    S('hc_g', '    Headcount y/y %', 'growth', 'pct', all=growth('hc'))
    S('rev_hc', '  Revenue per employee — annualised ($000)', 'memo_calc', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("hc")}),IFERROR({V("is_rev")}*{ann()}/{V("hc")}*1000,""),"")')
    blank()
    S('geo_hdr', 'Revenue by geography (billing address of the customer; 10-Q / 10-K revenue note from 2018; Q4 = year − nine months)', 'block',
      note='GEOGRAPHY — memo (customer billing address, not user location)')
    for k, lab in (('geo_usc', 'United States & Canada'), ('geo_eu', 'Europe (incl. Russia and Turkey)'), ('geo_ap', 'Asia-Pacific'),
                   ('geo_row', 'Rest of World (Africa, Latin America, Middle East)')):
        S(k, f'  {lab}', 'memo', 'm', data=k, flow=True)
    S('geo_chk', '  Check: Σ geographies vs revenue (should be 0; ±1 where Q4 = year − nine months)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("geo_usc")}),IF(ABS({V("geo_usc")}+{V("geo_eu")}+{V("geo_ap")}+{V("geo_row")}-{V("is_rev")})<=1.1,0,ROUND({V("geo_usc")}+{V("geo_eu")}+{V("geo_ap")}+{V("geo_row")}-{V("is_rev")},1)),"")')
    S('geo_usc_p', '  United States & Canada % of revenue', 'pct', 'pct', hist=lambda: f'=IF(ISNUMBER({V("geo_usc")}),IFERROR({V("geo_usc")}/{V("is_rev")},""),"")')
    S('geo_usc_g', '  United States & Canada y/y %', 'growth', 'pct', all=growth('geo_usc'))
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — technology and talent deals; no acquired revenue assumed)', 'block',
      note='M&A LEVER — spend → goodwill & intangibles; acquired intangibles amortised (inside D&A); mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_intp', '  Acquired intangibles % of spend (rest goodwill)', 'driver', 'pct', e26_in=0.0, ae_in=0.25,
      note='Assumption (Meta\'s purchase-price allocations are mostly goodwill: WhatsApp 2014, Oculus 2014, Giphy, Within, Kustomer).')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=5)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (inside D&A)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group total — revenue (build) → 2026 guidance calibration (Q3/26E revenue; FY26 total expenses)', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Revenue (build)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("adv")}),{V("adv")}+{V("oth_rev")},{V("is_rev")})', fc=lambda: f'={V("adv")}+{V("oth_rev")}',
      note='Advertising + non-advertising revenue.')
    S('g_rev_g', '  Revenue y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: build vs consolidated revenue (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),ROUND({V("g_rev")}-{V("is_rev")},1),"")')
    S('cal_rguid', '  Memo: Q3/26 revenue guidance (scenario end-point: high / mid / low of $61–64bn)', 'memo', 'm',
      qe=lambda: ('=' + CH(SC['out_q3rev'])) if is_q3() else None, note=V0['rev_guid_note'])
    S('cal_pre', '  Q3/26E revenue before calibration (helper)', 'line', 'm',
      qe=lambda: (f'={P("adv")}*(1+{V("impr_g")})*(1+{V("price_pre")})+{V("foa_oth")}+{V("rl_rev")}') if is_q3() else None)
    S('cal_sens', '  Q3/26E revenue sensitivity to +1.00 of price-per-ad growth (helper)', 'line', 'm',
      qe=lambda: f'={P("adv")}*(1+{V("impr_g")})' if is_q3() else None)
    S('cal_p', '  Guidance calibration: Δ price-per-ad growth (solved in Q3/26E; carried into Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_rguid")}-{V("cal_pre")})/{V("cal_sens")}' if is_q3() else f'={QA(Q3E, "cal_p")}',
      note='Closed-form linear solve: Δ = (guidance end-point − revenue before calibration) ÷ sensitivity. No guidance for Q4: the Q3 Δ is carried forward.')
    S('cal_rchk', '  Check: Q3/26E revenue vs guidance end-point (should be 0)', 'check', 'm',
      qe=lambda: f'=ROUND({V("is_rev")}-{V("cal_rguid")},1)' if is_q3() else None)
    S('cal_x', '  Memo: FY26 total expenses guidance (scenario end-point: low / mid / high of $165–169bn)', 'memo', 'm',
      e26=lambda: '=' + CH(SC['out_exp']), note=V0['exp_guid_note'])
    S('cal_x2h', '  2H/26E total costs and expenses required (guidance − 1H/26 actual)', 'memo_calc', 'm', e26=lambda: f'={V("cal_x")}-{H1("is_costs")}')
    S('cal_xs', '  Q3 share of 2H costs (2H/25 pattern: Q3/25 ÷ (Q3/25 + Q4/25))', 'memo_calc', 'pct',
      e26=lambda: f'={PQ3}{R["is_costs"]}/({PQ3}{R["is_costs"]}+{PQ4}{R["is_costs"]})')
    S('cal_xq', '  Total costs and expenses target (Q3/26E, Q4/26E)', 'line', 'm',
      qe=lambda: f'={QA(E26, "cal_x2h")}*' + (f'{QA(E26, "cal_xs")}' if is_q3() else f'(1-{QA(E26, "cal_xs")})'),
      note='Other operating costs (cash) are the balancing driver: target − D&A − share-based compensation − one-off items.')
    S('cal_xchk', '  Check: FY26 total costs and expenses vs guidance end-point (should be 0)', 'check', 'm', e26=lambda: f'=ROUND({V("is_costs")}-{V("cal_x")},1)')
    S('cal_oi', '  Memo: FY26 income from operations − FY25 ("above 2025 operating income" — information, should be > 0)', 'memo_calc', 'm',
      e26=lambda: f'={V("is_oi")}-{Y("is_oi", 2025)}')
    S('cal_cx', '  Memo: FY26 capital expenditures incl. principal payments on finance leases — guidance mid-point ($130–145bn)', 'memo', 'm',
      e26=lambda: f'={PT("pt_capex")}')
    S('cal_cx_d', '    Model − guidance (information)', 'memo_calc', 'm', e26=lambda: f'={V("capex_all")}-{V("cal_cx")}')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers — D&A (capex-driven), share-based compensation, other operating costs, one-off items; interest & other', 'block',
      note='COST DRIVERS — total costs = D&A + share-based compensation + other operating costs (cash) + company-quantified one-offs')
    S('d_dda', '  Depreciation & amortization (cash-flow statement)', 'line', 'm', data='cf_dda', flow=True,
      qe=lambda: f'={PQ("d_dda")}*(1+{PT("pt_ddag")})',
      ae=lambda: f'=({P("bs_ppe")}+0.5*{V("capex_all")})*{V("d_dep_r")}+N({V("m_amort")})',
      note='Q3/Q4-26E: prior quarter × (1 + q/q growth point estimate). 2027E+: (opening net PP&E + ½ × capex incl. finance leases) × depreciation rate + acquired-intangible amortization.')
    S('d_dep_r', '  D&A rate — D&A ÷ (opening net PP&E + ½ capex incl. finance leases) (annual)', 'pct', 'pct', ann=True,
      hist=lambda: (f'=IFERROR({V("d_dda")}/({P("bs_ppe")}+0.5*{V("capex_all")}),"")' if CTX.col.prior and CTX.col.year >= 2012 else None),
      ae_in=V0['dep_r'], note=V0['dep_note'])
    S('d_sbc', '  Share-based compensation (cash-flow statement)', 'line', 'm', data='cf_sbc', flow=True,
      qe=lambda: f'={PT("pt_sbc")}', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}', note='Q3/Q4-26E: point estimate (Q2/26 level). 2027E+: % of revenue.')
    S('d_sbc_pct', '  Share-based compensation % of revenue', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_legal', '  One-off: legal accruals and settlements (company-quantified; G&A)', 'line', 'm', data='oo_legal', flow=True, labkey='oo_label', fc=lambda: '=0',
      note='Only items the company quantified in its releases (FTC 2019; Q2-23; Q4-24 release; Q2-26). The Q2-24 Texas settlement was named but not quantified (left in).')
    S('d_restr', '  One-off: restructuring and severance (company-quantified)', 'line', 'm', data='oo_restr', flow=True, labkey='oo_label', fc=lambda: '=0',
      note='Q3-22 lease impairment; Q4-22–Q4-23 facilities consolidation, layoffs and data-center restructuring; Q2-26 severance (May-2026 headcount reduction). Forecast: none assumed.')
    S('d_cash', '  Other operating costs (cash; excl. D&A, share-based compensation and one-offs)', 'line_b', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("d_dda")}),{V("is_costs")}-{V("d_dda")}-{V("d_sbc")}-N({V("d_legal")})-N({V("d_restr")}),"")',
      qe=lambda: f'={V("cal_xq")}-{V("d_dda")}-{V("d_sbc")}-{V("d_legal")}-{V("d_restr")}',
      ae=lambda: f'={V("is_rev")}*{V("d_cash_pct")}',
      note='Q3/Q4-26E: balancing driver to the FY26 expense guidance. 2027E+: % of revenue (scenario lever): AI compute (third-party cloud, data-center operations), people, content, marketing.')
    S('d_cash_pct', '  Other operating costs % of revenue', 'pct', 'pct', all=ratio('d_cash', 'is_rev'), ae=lambda: '=' + CH(SC['OPEX'][CTX.col.year]))
    S('d_cash_g', '    y/y %', 'growth', 'pct', all=growth('d_cash'))
    S('d_mix_h', '  Cost lines — share of total costs excluding one-offs (forecast presentation; one-offs booked in G&A):', 'sub', 'gen')
    for k, lab, line in (('d_cogs_p', 'Cost of revenue', 'is_cogs'), ('d_rd_p', 'Research & development', 'is_rd'),
                         ('d_mm_p', 'Marketing & sales', 'is_mm'), ('d_ga_p', 'General & administrative', 'is_ga')):
        if k == 'd_ga_p':
            h = lambda line=line: f'=IFERROR(({V(line)}-N({V("d_legal")})-N({V("d_restr")}))/({V("is_costs")}-N({V("d_legal")})-N({V("d_restr")})),"")'
            q = lambda line=line: f'=IFERROR(({H1(line)}-{H1("d_legal")}-{H1("d_restr")})/({H1("is_costs")}-{H1("d_legal")}-{H1("d_restr")}),0)'
        else:
            h = lambda line=line: f'=IFERROR({V(line)}/({V("is_costs")}-N({V("d_legal")})-N({V("d_restr")})),"")'
            q = lambda line=line: f'=IFERROR({H1(line)}/({H1("is_costs")}-{H1("d_legal")}-{H1("d_restr")}),0)'
        S(k, f'    {lab} %', 'pct', 'pct', hist=h, qe=q, ae=lambda k=k: f'={QA(Q4E, k)}',
          note='Q3/Q4-26E: 1H/26 mix (G&A excluding the Q2 legal charges; the Q2 severance spread across the lines is not separable). 2027E+: held.' if k == 'd_cogs_p' else None)
    S('d_io_h', '  Interest and other income (expense), net — components:', 'sub', 'gen')
    S('d_intinc', '  Interest income', 'line', 'm', data='x_intinc', flow=True,
      qe=lambda: f'=({B1("bs_cash")}+{B1("bs_ms")})*{PT("pt_yld")}/4', ae=lambda: f'=({P("bs_cash")}+{P("bs_ms")})*{V("ds_r_cash")}',
      note='History: XBRL (annual; Q1/Q2-26 from the 10-Q). Forecast: yield × opening cash, cash equivalents and marketable securities.')
    S('d_intexp', '  Interest expense (net of capitalized interest)', 'line', 'm', data='x_intexp', flow=True,
      qe=lambda: f'={B1("ds_total")}*{PT("pt_rate")}/4', ae=lambda: f'={P("ds_total")}*{V("ds_r_debt")}',
      note='History: XBRL (annual; Q1/Q2-26 from the 10-Q). Forecast: rate × opening debt (net of capitalized interest on data-center construction).')
    S('d_oio', '  FX, gains / (losses) on equity investments and other (derived; forecast nil)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("d_intinc")}),{V("is_io")}-{V("d_intinc")}+{V("d_intexp")},"")', fc=lambda: '=0')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENTS OF INCOME (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (revenue from the build; total costs from the cost drivers; cost lines by mix)')
    S('is_rev', 'Revenue', 'total', 'm', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the operating build.')
    def line(key, data, lab, pkey, extra=''):
        S(key, lab, 'line', 'm', data=data, flow=True,
          fc=lambda: f'=({V("is_costs")}-{V("d_legal")}-{V("d_restr")})*{V(pkey)}{extra}')
    line('is_cogs', 'cogs', 'Cost of revenue', 'd_cogs_p')
    line('is_rd', 'rd', 'Research and development', 'd_rd_p')
    line('is_mm', 'mm', 'Marketing and sales', 'd_mm_p')
    S('is_ga', 'General and administrative', 'line', 'm', data='ga', flow=True,
      fc=lambda: f'=({V("is_costs")}-{V("d_legal")}-{V("d_restr")})*{V("d_ga_p")}+{V("d_legal")}+{V("d_restr")}')
    S('is_costs', 'Total costs and expenses', 'line_b', 'm', data='costs', flow=True,
      fc=lambda: f'={V("d_dda")}+{V("d_sbc")}+{V("d_cash")}+{V("d_legal")}+{V("d_restr")}')
    S('is_costs_g', '  Total costs and expenses y/y %', 'growth', 'pct', all=growth('is_costs'))
    S('is_oi', 'Income from operations', 'total', 'm', data='oi', flow=True, fc=lambda: f'={V("is_rev")}-{V("is_costs")}')
    S('is_oim', '  Operating margin %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('is_oi_chk', '  Check: revenue − total costs = income from operations (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_costs")}),ROUND({V("is_rev")}-{V("is_costs")}-{V("is_oi")},1),"")')
    S('is_io', 'Interest and other income (expense), net', 'line', 'm', data='io_net', flow=True,
      fc=lambda: f'={V("d_intinc")}-{V("d_intexp")}+{V("d_oio")}')
    S('is_ebt', 'Income before provision for income taxes', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_oi")}),{V("is_oi")}+{V("is_io")},"")')
    S('is_tax', 'Provision (benefit) for income taxes', 'line', 'm', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Q3/Q4-26E: guidance 15–17% for the remaining quarters of 2026 (mid-point). 2027E+: input (U.S. Corporate Alternative Minimum Tax; FDII).')
    S('is_ni', 'Net income', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_ni_chk', '  Check: net income vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),ROUND({V("is_ni")}-{V("is_ni_pub")},1),"")')
    S('is_ni_pub', '  Memo: net income as reported', 'memo', 'm', data='ni', flow=True)
    S('is_part', '  Less: net income attributable to participating securities (pre-IPO preferred; unvested awards)', 'line', 'm', data='ni_part', flow=True, fc=lambda: '=0')
    S('is_realloc', '  Reallocation to Class A for diluted EPS (pre-IPO two-class method, FY2009–11)', 'line', 'm', data='ni_dil_realloc', flow=True, fc=lambda: '=0')
    S('is_nic', 'Net income attributable to Class A and Class B common stockholders (diluted EPS numerator)', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_ni")}),{V("is_ni")}-N({V("is_part")})+N({V("is_realloc")}),"")')
    S('is_dda', '  Memo: depreciation & amortization', 'memo_calc', 'm', all=lambda: f'={V("d_dda")}')
    S('is_sbc', '  Memo: share-based compensation', 'memo_calc', 'm', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share — Class A and Class B common stock; same per-share amount for both classes)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm', data='sh_b', avg=True,
      qe=lambda: f'={PQ("sh_basic")}+({QA(E26, "bb_iss")}-{QA(E26, "bb_sh")})*{0.25 if is_q3() else 0.5}',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q3/Q4-26E: prior quarter + 2H net share issuance less buybacks (phased). 2027E+: average of beginning and ending shares. FY2009–11: prospectus EPS note (Class A + B).')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({QA(Q2, "sh_dil")}-{QA(Q2, "sh_basic")})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}',
      note='FY2009–11: Class A diluted computation (Class B converted).')
    S('eps_dil', 'EPS — diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_nic")}/{V("sh_dil")},""),"")')
    S('eps_dil_g', '  EPS — diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS — diluted as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0101,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('dps', '  Dividends declared per share ($; first dividend Q1-2024)', 'line', 'ps', data='dps', flow=True, qe=lambda: f'={PT("pt_dps")}',
      ae=lambda: f'={P("dps")}*(1+{V("dps_g")})', note='XBRL (10-Q / 10-K). Quarterly $0.525 (2025–2026). 2027E+: prior year × (1 + growth).')
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'])
    blank()

    # ------------------------------------------------------------------ RECON 1: income from operations -> adjusted
    S('sec_r1', 'RECONCILIATION: INCOME FROM OPERATIONS → ADJUSTED INCOME FROM OPERATIONS (company definition IPO–2016; model definition after)', 'section',
      note='ADJUSTED OI — company non-GAAP IPO–Q4 2016 (excl. share-based compensation, payroll tax, amortization from Q3-14); 2017+ model: company-quantified one-offs only')
    S('o_op', 'Income from operations (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_oi")}')
    S('o_sbc', '  (+) Share-based compensation (company definition IPO–2016 only)', 'line', 'm', data='ng_sbc', flow=True, hist=lambda: '=0', fc=lambda: '=0')
    S('o_payroll', '  (+) Payroll tax related to share-based compensation (IPO–2016)', 'line', 'm', data='ng_payroll', flow=True, hist=lambda: '=0', fc=lambda: '=0')
    S('o_amort', '  (+) Amortization of intangible assets (Q3-2014–2016)', 'line', 'm', data='ng_amort', flow=True, hist=lambda: '=0', fc=lambda: '=0')
    S('o_legal', '  (+) Legal accruals and settlements (company-quantified)', 'line', 'm', all=lambda: f'=N({V("d_legal")})')
    S('o_restr', '  (+) Restructuring and severance (company-quantified)', 'line', 'm', all=lambda: f'=N({V("d_restr")})')
    S('o_tot', '  Total adjusting items (pre-tax)', 'line_b', 'm', all=lambda: f'={nsum(["o_sbc", "o_payroll", "o_amort", "o_legal", "o_restr"])}')
    S('o_adj', '  = Adjusted income from operations (definition in force)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_tot")},"")',
      note='Company definition where published (IPO–2016); otherwise GAAP + company-quantified one-offs (model).')
    S('o_adj_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company-published non-GAAP income from operations', 'memo', 'm', data='ng_oi', flow=True)
    S('o_chk', '  Check: model bridge vs company-published (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),ROUND({V("o_adj")}-{V("o_pub")},1),"n/p")')
    S('o_def', '  Definition / basis (adjusted definition in force)', 'text', 'gen',
      note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('o_cur', '  Memo: adjusted income from operations — current definition (GAAP + company-quantified one-offs; SBC expensed) — drives valuation', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_legal")}+{V("o_restr")},"")')
    S('o_cur_m', '  Adjusted operating margin (current definition) %', 'pct', 'pct', all=ratio('o_cur', 'is_rev'))
    S('o_cur_g', '  Adjusted income from operations (current definition) y/y %', 'growth', 'pct', all=growth('o_cur'))
    S('o_inc', '  Incremental margin (Δ adjusted OI, current definition / Δ revenue)', 'pct', 'pct', all=incr('o_cur', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: net income -> EBITDA -> adjusted EBITDA
    S('sec_r2', 'RECONCILIATION: NET INCOME → EBIT → EBITDA → ADJUSTED EBITDA (model definitions — Meta publishes no EBITDA)', 'section',
      note='EBITDA (model) — net income + tax − interest and other income (net) = income from operations; + D&A = EBITDA; + company-quantified one-offs = adjusted EBITDA (SBC expensed)')
    S('r_ni', 'Net income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('r_tax', '  (+) Provision for income taxes', 'line', 'm', all=lambda: f'={V("is_tax")}')
    S('r_io', '  (−) Interest and other income (expense), net', 'line', 'm', all=lambda: f'=-{V("is_io")}')
    S('r_ebit', '  = EBIT (= income from operations)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_tax")}+{V("r_io")},"")')
    S('r_ebit_chk', '  Check: EBIT vs income from operations (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("r_ebit")}),ROUND({V("r_ebit")}-{V("is_oi")},1),"")')
    S('r_dda', '  (+) Depreciation & amortization', 'line', 'm', all=lambda: f'={V("d_dda")}')
    S('r_ebitda', '  = EBITDA (model)', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_ebit")}),ISNUMBER({V("r_dda")})),{V("r_ebit")}+{V("r_dda")},"")')
    S('r_oo', '  (+) Company-quantified one-offs (legal accruals and settlements; restructuring and severance)', 'line', 'm',
      all=lambda: f'=N({V("o_legal")})+N({V("o_restr")})')
    S('r_adj', '  = Adjusted EBITDA (model definition; share-based compensation expensed)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{V("r_ebitda")}+{V("r_oo")},"")',
      note='Model definition (labelled; Meta publishes no EBITDA). Used for leverage (net debt / adjusted EBITDA) and EV / EBITDA.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_sbcx', '  Memo: adjusted EBITDA excluding share-based compensation (peer comparison only)', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+{V("d_sbc")},"")')
    S('r_ebit_h', 'To adjusted EBIT, full-cost (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ddan', '  (−) Depreciation & amortization', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("d_dda")}),-{V("d_dda")},"")')
    S('r_aebit', '  = Adjusted EBIT, full-cost (= adjusted income from operations, current definition)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+{V("r_ddan")},"")')
    S('r_aebit_m', '  Adjusted EBIT (full-cost) margin %', 'pct', 'pct', all=ratio('r_aebit', 'is_rev'))
    S('r_cash', '  Memo: one-off items adjusted out that are cash costs (legal settlements, severance, facilities; deducted in the DCF)', 'memo_calc', 'm',
      all=lambda: f'=N({V("o_legal")})+N({V("o_restr")})')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: NET INCOME / DILUTED EPS → ADJUSTED NET INCOME → ADJUSTED EPS', 'section',
      note='ADJUSTED EPS — company non-GAAP IPO–2016; 2017+: GAAP + company-quantified one-offs and discrete tax items (the company stated "excluding" EPS for each)')
    S('e_ni', 'Net income attributable to common stockholders (GAAP; diluted EPS numerator)', 'line_b', 'm', all=lambda: f'={V("is_nic")}')
    S('e_part', '  (+) Participating-securities allocation (added back in the company non-GAAP definition, 2012–13)', 'line', 'm',
      all=lambda: (f'=N({V("is_part")})-N({V("is_realloc")})' if COMPANY_NG(CTX.col) else '=0'))
    S('e_items', '  (+) Pre-tax adjusting items (bridge above)', 'line', 'm', all=lambda: f'={V("o_tot")}')
    S('e_tax', '  (−) Tax effect of the adjusting items', 'line', 'm', flow=True, hist=lambda: TAXEFF(CTX.col), fc=lambda: f'=-({V("o_legal")}+{V("o_restr")})*{V("is_etr")}',
      note=('Historical: company "income tax adjustments" (IPO–2016); where the company stated an "excluding" EPS, derived as published EPS × diluted shares − GAAP − items − '
            'discrete tax; FTC accruals non-deductible (company); otherwise imputed at the period effective tax rate bounded 15–40% (cell comments). Forecast: items × tax rate.'))
    S('e_disc', '  (+/−) Discrete tax items the company quantified (2017 Tax Act; 2019 Altera; 2020 R&D election; 2025 OBBBA valuation allowance; 2026 partial release)', 'line', 'm',
      data='oo_tax', flow=True, hist=lambda: '=0', fc=lambda: '=0')
    S('e_adjni', '  = Adjusted net income (definition in force)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("e_ni")}),{V("e_ni")}+{V("e_part")}+{V("e_items")}+{V("e_tax")}+{V("e_disc")},"")')
    S('e_pubni', '  Company-published non-GAAP net income (IPO–2016)', 'memo', 'm', data='ng_ni', flow=True)
    S('e_ngsh', '  Memo: company non-GAAP diluted shares (IPO–2016; incl. assumed preferred conversion pre-IPO)', 'memo', 'm', data='ng_sh', avg=True)
    S('e_sh', '  Diluted shares for adjusted EPS (m)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("e_ngsh")}),{V("e_ngsh")},{V("sh_dil")})')
    S('e_eps', 'Adjusted EPS — diluted ($) (definition in force)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted / "excluding" EPS ($)', 'eps_memo', 'ps', data='e_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0101,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_def', '  Definition / basis (adjusted EPS definition in force)', 'text', 'gen')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_curni', '  Memo: adjusted net income — current definition (SBC expensed; one-offs and discrete tax only) — drives P/E and valuation', 'total', 'm',
      all=lambda: (f'={V("is_nic")}' if COMPANY_NG(CTX.col) else f'=IF(ISNUMBER({V("e_adjni")}),{V("e_adjni")}-{V("e_part")},"")'))
    S('e_cureps', '  Memo: adjusted EPS — current definition ($)', 'eps_total', 'ps', all=ratio('e_curni', 'sh_dil'))
    S('e_cureps_g', '    y/y %', 'growth', 'pct', all=growth('e_cureps'))
    S('e_adjebt', '  Adjusted income before taxes (current definition: adjusted OI + interest and other)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_cur")}),{V("o_cur")}+{V("is_io")},"")')
    S('e_adjtax', '  Adjusted income tax (adjusted income before taxes − adjusted net income, current definition)', 'line', 'm', flow=True,
      all=lambda: f'=IF(AND(ISNUMBER({V("e_curni")}),ISNUMBER({V("e_adjebt")})),{V("e_adjebt")}-{V("e_curni")}-N({V("is_part")})+N({V("is_realloc")}),"")')
    S('e_rate', '  Adjusted effective tax rate (current definition)', 'pct', 'pct', all=ratio('e_adjtax', 'e_adjebt'))
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Revenue y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_adv', '  Advertising revenue y/y %', 'growth', 'pct', all=growth('adv'))
    S('gm_costs', '  Total costs and expenses y/y %', 'growth', 'pct', all=growth('is_costs'))
    S('gm_cur', '  Adjusted income from operations (current definition) y/y %', 'growth', 'pct', all=growth('o_cur'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_ni', '  Net income y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS (current definition) y/y %', 'growth', 'pct', all=growth('e_cureps'))
    S('gm_cogs', '  Cost of revenue % of revenue', 'pct', 'pct', all=ratio('is_cogs', 'is_rev'))
    S('gm_rd', '  R&D % of revenue', 'pct', 'pct', all=ratio('is_rd', 'is_rev'))
    S('gm_mm', '  Marketing & sales % of revenue', 'pct', 'pct', all=ratio('is_mm', 'is_rev'))
    S('gm_ga', '  G&A % of revenue', 'pct', 'pct', all=ratio('is_ga', 'is_rev'))
    S('gm_cur_m', '  Adjusted operating margin (current definition) %', 'pct', 'pct', all=ratio('o_cur', 'is_rev'))
    S('gm_inc', '  Incremental adjusted operating margin (Δ adjusted OI / Δ revenue)', 'pct', 'pct', all=incr('o_cur', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    blank()

# per-column historical tax effect of the adjusting items (formula chosen from what the company published for that period)
def TAXEFF(col):
    p = pkey(col)
    x = DATA.get(p, {}).get('x', {})
    if x.get('ng_taxadj') is not None: return f'={x["ng_taxadj"]}'
    items = (x.get('oo_legal') or 0) + (x.get('oo_restr') or 0)
    if x.get('oo_taxeff') is not None and items: return f'={-x["oo_taxeff"] if x["oo_taxeff"] else 0}'
    if x.get('oo_eps_pub') is not None and items:
        return f'={V("e_pub")}*{V("e_sh")}-{V("e_ni")}-{V("e_part")}-{V("e_items")}-{V("e_disc")}'
    if items:
        return f'=-{V("e_items")}*MIN(0.4,MAX(0.15,IFERROR({V("is_tax")}/{V("is_ebt")},0.21)))'
    return '=0'
