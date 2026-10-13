"""Row specification of the NFLX Model sheet, part 1 (MLM template layout and process):
regional revenue build (UCAN / EMEA / LATAM / APAC; paid memberships and ARM as history KPIs) -> legacy segments (memo) ->
M&A lever -> group total & FY26 guidance calibration (Q3-26 quarter guide + FY26 revenue / operating-margin guide) -> cost
drivers (content amortization first, then the non-content cost ratios) -> income statement -> GAAP-to-adjusted bridges ->
growth & margins."""
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
def ACT(key): return f'SUM({Q1}{R[key]}:{Q2}{R[key]})'      # 1H-26 actual (Q1-Q2/26)
def ACT0(key): return f'SUM({PQ1}{R[key]}:{PQ2}{R[key]})'   # 1H-25 actual (Q1-Q2/25)
def H2(key): return f'SUM({Q3E}{R[key]}:{Q4E}{R[key]})'     # 2H-26 estimate (Q3-Q4/26E)
def QEc(key): return f'{CTX.col.c}{R[key]}'                  # current estimate quarter
def B1(key): return f'{LQ}{R[key]}'                          # 30-Jun-2026 balance
def drift(n, d):                                             # 1H-26 vs 1H-25 change in the ratio n / d
    return f'IFERROR({ACT(n)}/{ACT(d)}-{ACT0(n)}/{ACT0(d)},0)'

REG = [('ucan', 'UCAN', 'United States and Canada'), ('emea', 'EMEA', 'Europe, Middle East and Africa'),
       ('latam', 'LATAM', 'Latin America'), ('apac', 'APAC', 'Asia-Pacific')]
RK = [f'{g}_rev' for g, _, _ in REG]
COSTS = [('ocor', 'Other cost of revenues (excl. content amortization and one-offs)'), ('mkt', 'Marketing / sales and marketing'),
         ('td', 'Technology and development'), ('ga', 'General and administrative')]

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of the FY26 guidance ranges (point guidance = all cases).'))
    r = 11
    SCEN_ROWS.append((r, 'out_hdr', V0['out_hdr'], 'High', 'Mid', 'Low', V0['out_note'])); r += 1
    for key, lab, (hi, mid, lo), nf, note in V0['outlook']:
        SC[key] = r; SCEN_ROWS.append((r, 'out', lab, hi, mid, lo, note, nf)); r += 1
    r += 1
    SCEN_ROWS.append((r, 'pt_hdr', 'Q3-26E / Q4-26E and FY26 point estimates (all cases)', None, None, None, None)); r += 1
    for key, lab, vals, nf, note in V0['points']:
        SC[key] = r
        SCEN_ROWS.append((r, 'pt', lab, None, vals, None, note, nf)); r += 1
    r += 1
    SC['LEV'] = r
    SCEN_ROWS.append((r, 'lev', '  Target year-end cash (months of revenue) — buybacks return cash above it (2026E–2031E)', *V0['lev'], V0['lev_note']))
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
    # ------------------------------------------------------------------ REVENUE BUILD
    S('sec_rev', 'REVENUE BUILD — STREAMING REVENUE BY REGION (UCAN · EMEA · LATAM · APAC; paid memberships × ARM as history KPIs)', 'section',
      note='REVENUE BUILD — modelling logic (regional revenue → consolidated revenue; Q3/Q4-26E calibrated to the Q3-26 and FY26 revenue guidance; 2027E+ regional growth levers)')
    blank()
    for g, code, name in REG:
        S(f'{g}_hdr', f'{name} ({code})', 'block', note=f'{code} — modelling logic' if g == 'ucan' else None)
        S(f'{g}_rev', f'  {code} streaming revenue', 'line', 'm1', data=f'rg_{g}_rev', flow=True,
          qe=lambda g=g: f'={P(g + "_rev")}*(1+{V(g + "_g")})', ae=lambda g=g: f'={P(g + "_rev")}*(1+{V(g + "_g")})',
          note=('Revenue by region (10-Q / 10-K revenue note; FY2017–19 from the FY2019 10-K and the 2019 quarters from the 2020 10-Q comparatives; Q4 = FY − 9M). '
                'Q3/Q4-26E: prior-year quarter × (1 + growth); 2027E+: prior year × (1 + scenario lever).') if g == 'ucan' else None)
        S(f'{g}_g', '    y/y %', 'growth', 'pct', all=growth(f'{g}_rev'),
          qe=lambda g=g: f'={V(g + "_pre")}+{QEc("cal_g")}', ae=lambda g=g, code=code: '=' + CH(SC[f'{code}_G'][CTX.col.year]),
          note='Q3/Q4-26E: 1H-26 y/y growth of the region + revenue-guidance calibration Δ of that quarter (Group block). 2027E–2031E: scenario lever (table →).' if g == 'ucan' else None)
        S(f'{g}_pre', '    Q3/Q4-26E growth before calibration (1H-26 y/y)', 'driver', 'pct', qe=lambda g=g: f'=IFERROR({ACT(g + "_rev")}/{ACT0(g + "_rev")}-1,0)')
        S(f'{g}_mix', '    % of revenue', 'pct', 'pct', all=ratio(f'{g}_rev', 'is_rev'))
        S(f'{g}_paid', f'    Memo: {code} paid memberships at period end (m)', 'memo', 'm1', data=f'rg_{g}_paid',
          note='Paid memberships and ARM were published to Q4-2024; from 2025 Netflix reports revenue by region only.' if g == 'ucan' else None)
        S(f'{g}_arm', f'    Memo: {code} average monthly revenue per paying membership ($)', 'memo', 'm2', data=f'rg_{g}_arm')
        blank()
    S('rg_hdr', 'Regional total and memberships', 'block')
    S('rg_dvd', '  DVD and other revenue outside the regional tables (derived: consolidated − Σ regions; DVD service closed Sep-2023)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("ucan_rev")}),{V("is_rev")}-({"+".join(V(k) for k in RK)}),"")', fc=lambda: '=0')
    S('rg_paid', '  Global streaming paid memberships at period end (m; Σ regions 2017–24, Σ legacy domestic + international streaming 2011–16)', 'line', 'm1',
      all=lambda: (f'=IF(ISNUMBER({V("ucan_paid")}),{"+".join(V(g + "_paid") for g, _, _ in REG)},'
                   f'IF(ISNUMBER({V("sg_dom_mem")}),{V("sg_dom_mem")}+{V("sg_int_mem")},""))'))
    S('rg_nadd', '  Paid net additions (m)', 'line', 'm1',
      all=lambda: (f'=IF(AND(ISNUMBER({V("rg_paid")}),ISNUMBER({(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["rg_paid"]})),{V("rg_paid")}-{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["rg_paid"]},"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    S('rg_rpm', '  Revenue per average paid membership — annualised ($; derived)', 'line', 'm2',
      all=lambda: (f'=IF(AND(ISNUMBER({V("rg_paid")}),ISNUMBER({(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["rg_paid"]})),'
                   f'IFERROR({V("is_rev")}*{4 if CTX.col.q else 1}/AVERAGE({V("rg_paid")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["rg_paid"]}),""),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    S('gc_dom', '  Contribution to revenue growth — UCAN (legacy domestic streaming + DVD to 2017) (pp)', 'growth', 'pct',
      all=lambda: (f'=IF(ISNUMBER({P("ucan_rev")}),IFERROR(({V("ucan_rev")}-{P("ucan_rev")})/{P("is_rev")},""),'
                   f'IF(ISNUMBER({P("sg_dom_rev")}),IFERROR(({V("sg_dom_rev")}+N({V("sg_dvd_rev")})-{P("sg_dom_rev")}-N({P("sg_dvd_rev")}))/{P("is_rev")},""),""))' if CTX.col.prior else None))
    S('gc_int', '  Contribution to revenue growth — international (EMEA + LATAM + APAC; legacy international streaming to 2017) (pp)', 'growth', 'pct',
      all=lambda: (f'=IF(ISNUMBER({V("gc_dom")}),IFERROR({V("is_rev")}/{P("is_rev")}-1-{V("gc_dom")},""),"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ legacy segments (memo)
    S('lg_hdr', 'Legacy reportable segments 2011–2019 (memo, as reported: Domestic streaming · International streaming · Domestic DVD; contribution profit = revenue − cost of revenues − marketing)', 'block',
      note='LEGACY SEGMENTS — history only (single operating segment from 2020)')
    for s_, lab in (('dom', 'Domestic streaming'), ('int', 'International streaming'), ('dvd', 'Domestic DVD')):
        S(f'sg_{s_}_rev', f'  {lab} revenue', 'memo', 'm1', data=f'sg_{s_}_rev', flow=True)
    S('sg_chk', '  Check: legacy segments vs consolidated revenue (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("sg_dom_rev")}),IF(ABS({V("sg_dom_rev")}+{V("sg_int_rev")}+N({V("sg_dvd_rev")})-{V("is_rev")})<=0.15,0,ROUND({V("sg_dom_rev")}+{V("sg_int_rev")}+N({V("sg_dvd_rev")})-{V("is_rev")},1)),"")')
    for s_, lab in (('dom', 'Domestic streaming'), ('int', 'International streaming'), ('dvd', 'Domestic DVD')):
        S(f'sg_{s_}_cp', f'  {lab} contribution profit', 'memo', 'm1', data=f'sg_{s_}_cp', flow=True)
        S(f'sg_{s_}_cpm', '    Contribution margin %', 'pct', 'pct', all=ratio(f'sg_{s_}_cp', f'sg_{s_}_rev'))
    S('sg_chkcp', '  Check: Σ contribution profit vs revenue − cost of revenues − marketing (should be 0)', 'check', 'm1',
      hist=lambda: (f'=IF(ISNUMBER({V("sg_dom_cp")}),IF(ABS({V("sg_dom_cp")}+{V("sg_int_cp")}+N({V("sg_dvd_cp")})-({V("is_rev")}-{V("is_cor")}-{V("is_mkt")}-N({V("is_othop")})))<=0.15,0,'
                    f'ROUND({V("sg_dom_cp")}+{V("sg_int_cp")}+N({V("sg_dvd_cp")})-({V("is_rev")}-{V("is_cor")}-{V("is_mkt")}-N({V("is_othop")})),1)),"")'))
    for s_, lab in (('dom', 'Domestic streaming'), ('int', 'International streaming'), ('dvd', 'Domestic DVD')):
        S(f'sg_{s_}_mem', f'  {lab} memberships at period end (m; paid where published, else total)', 'memo', 'm1', data=f'sg_{s_}_mem')
    blank()

    # ------------------------------------------------------------------ future M&A
    S('m_hdr', 'Future acquisitions (M&A lever — studios, technology and games capability acquisitions; cash use only)', 'block',
      note='M&A LEVER — cash spend from 2027E; no revenue or margin is attached (Netflix discloses no revenue for its acquisitions)')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_note', '  Acquired revenue: not modelled (capability acquisitions; Q1-26 deal ~$587m, no revenue or PPA disclosed) — spend is booked to goodwill & other non-current assets', 'sub', 'gen')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group Total — revenue build → Q3-26 and FY26 guidance calibration (revenue · operating margin · FCF)', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Revenue (regional build)', 'total', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("ucan_rev")}),{"+".join(V(k) for k in RK)}+N({V("rg_dvd")}),{V("is_rev")})',
      fc=lambda: '=' + '+'.join(V(k) for k in RK),
      note='Σ regions (+ DVD / other revenue outside the regional tables to 2023). Before 2017 (annual) / 2019 (quarters) consolidated revenue (no regional split on EDGAR).')
    S('g_rev_g', '  Revenue y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: regional build vs consolidated revenue (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=0.15,0,ROUND({V("g_rev")}-{V("is_rev")},1)),"")')
    S('cal_rh', '  Revenue calibration (Q3-26E solved to the Q3 guide; Q4-26E solved to the FY26 end-point):', 'sub', 'gen')
    S('cal_tgt', '  Revenue target — Q3-26E: Q3 guidance; Q4-26E: FY26 end-point − 1H-26 actual − Q3-26E', 'memo_calc', 'm1',
      qe=lambda: (f'={CH(SC["out_q3rev"])}' if CTX.col.q == 3 else f'={V("cal_fyrev", E26)}-{ACT("g_rev")}-{Q3E}{R["g_rev"]}'))
    S('cal_fyrev', '  Memo: FY26 revenue guidance (scenario end-point)', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_rev']), note=V0['rev_guid_note'])
    S('cal_pre', '  Revenue before calibration (helper: Σ prior-year quarter × (1 + 1H-26 y/y))', 'line', 'm1',
      qe=lambda: '=' + '+'.join(f'{P(k)}*(1+{V(k[:-4] + "_pre")})' for k in RK))
    S('cal_sens', '  Revenue sensitivity to +1.00 of growth (helper: Σ prior-year quarter)', 'line', 'm1', qe=lambda: '=' + '+'.join(P(k) for k in RK))
    S('cal_g', '  Guidance calibration: Δ y/y growth applied to all regions (per quarter)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_tgt")}-{V("cal_pre")})/{V("cal_sens")}',
      note='Closed-form solve: Δ = (target − revenue before calibration) ÷ sensitivity. Q3 and Q4 have separate Δs (quarter guide + full-year guide).')
    S('cal_rev_chk', '  Check: revenue vs guidance target — Q3-26E quarter / FY26 end-point (should be 0)', 'check', 'm1',
      qe=lambda: f'=ROUND({V("g_rev")}-{V("cal_tgt")},1)', e26=lambda: f'=ROUND({V("g_rev")}-{V("cal_fyrev")},1)')
    S('cal_mh', '  Operating-margin calibration (content amortization from its ~10% guide first; one Δ on the non-content cost ratios):', 'sub', 'gen')
    S('cal_om', '  Operating-margin guidance — Q3-26E quarter / FY26 (scenario end-point)', 'memo', 'pct',
      qe=lambda: (f'={CH(SC["out_q3om"])}' if CTX.col.q == 3 else None), e26=lambda: '=' + CH(SC['out_om']), note=V0['om_guid_note'])
    S('cal_oi', '  Operating income required — Q3: revenue × Q3 margin; Q4: FY margin × FY revenue − 1H-26 − Q3-26E', 'memo_calc', 'm1',
      qe=lambda: (f'={V("is_rev")}*{V("cal_om")}' if CTX.col.q == 3 else
                  f'={V("cal_om", E26)}*{V("is_rev", E26)}-{ACT("is_oi")}-{Q3E}{R["is_oi"]}'))
    S('cal_cpre', '  Non-content costs before calibration (helper: revenue × Σ pre-calibration ratios)', 'line', 'm1',
      qe=lambda: f'={V("is_rev")}*(' + '+'.join(V(f'd_{k}_pre') for k, _ in COSTS) + f')+{V("d_oneoff")}')
    S('cal_m', '  Guidance calibration: proportional Δ on the non-content cost ratios (per quarter)', 'driver', 'pct',
      qe=lambda: f'=({V("is_rev")}-{V("d_camort")}-{V("cal_oi")}-{V("d_oneoff")})/({V("cal_cpre")}-{V("d_oneoff")})-1',
      note='Solves the proportional shift of other cost of revenues, marketing, technology & development and G&A (vs prior-year quarter ratio + 1H-26 drift) so that operating income = the requirement.')
    S('cal_om_chk', '  Check: operating margin vs guidance — Q3-26E / FY26 (should be 0.0%)', 'check', 'pct',
      qe=lambda: (f'=ROUND({V("is_oi_m")}-{V("cal_om")},4)' if CTX.col.q == 3 else None), e26=lambda: f'=ROUND({V("is_oi_m")}-{V("cal_om")},4)')
    S('cal_ih', '  Information rows (guided, not forced):', 'sub', 'gen')
    S('cal_q3ni', '  Memo: Q3-26 net income guidance ($m) — model − guidance', 'memo_calc', 'm1', qe=lambda: (f'={V("is_ni")}-{PT("pt_q3ni")}' if CTX.col.q == 3 else None))
    S('cal_q3eps', '  Memo: Q3-26 diluted EPS guidance ($0.82) — model − guidance', 'memo_calc', 'm2', qe=lambda: (f'={V("eps_dil")}-{PT("pt_q3eps")}' if CTX.col.q == 3 else None))
    S('cal_camg', '  Memo: FY26 content amortization growth — model (guided ~10%)', 'memo_calc', 'pct', e26=lambda: f'={V("d_camort_g")}')
    S('cal_oig', '  Memo: FY26 operating income growth — model (guided 20%+)', 'memo_calc', 'pct', e26=lambda: f'={V("is_oi")}/{P("is_oi")}-1')
    S('cal_fcf', '  Memo: FY26 free cash flow guidance (~$12.5bn) — forced through 2H working capital (cash-flow block)', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_fcf']))
    S('cal_fcf_chk', '  Check: FY26 free cash flow vs guidance (should be 0)', 'check', 'm1', e26=lambda: f'=ROUND({V("fcf")}-{V("cal_fcf")},1)')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers (content amortization · other cost of revenues · operating expenses · D&A · SBC) and adjusting items', 'block',
      note='COST DRIVERS — Q3/Q4-26E: guided content amortization, then calibrated ratios; 2027E+: content amortization growth lever, operating-margin lever, opex % inputs')
    S('d_camort', '  Content amortization (cost of revenues; streaming + DVD; cash-flow statement)', 'line', 'm1', data='camort', flow=True,
      qe=lambda: f'=({Y("d_camort", 2025)}*(1+{PT("pt_camg")})-{ACT("d_camort")})*{P("d_camort")}/({Q("d_camort", 2025, 3)}+{Q("d_camort", 2025, 4)})',
      ae=lambda: f'={P("d_camort")}*(1+{V("d_camort_g")})',
      note='Q3/Q4-26E: FY26 = FY25 × (1 + ~10% guided), 2H = FY − 1H actual, split by the 2H-25 quarterly mix. 2027E+: prior year × (1 + scenario lever).')
    S('d_camort_g', '  Content amortization y/y %', 'growth', 'pct', all=growth('d_camort'), ae=lambda: '=' + CH(SC['CAMORT_G'][CTX.col.year]))
    S('d_camort_p', '  Content amortization % of revenue', 'pct', 'pct', all=ratio('d_camort', 'is_rev'))
    for k, lab in COSTS:
        kw = dict(all=(ratio('d_ocor_x', 'is_rev') if k == 'ocor' else ratio(f'is_{k}', 'is_rev')),
                  qe=lambda k=k: f'={V("d_" + k + "_pre")}*(1+{QEc("cal_m")})')
        if k == 'ocor':
            kw['ae'] = lambda: f'=IFERROR({V("d_ocor_x")}/{V("is_rev")},"")'
            kw['note'] = ('Q3/Q4-26E: prior-year quarter ratio + 1H-26 y/y drift, × (1 + calibration Δ). 2027E+: other cost of revenues is the balancing line to the operating-margin lever; '
                          'marketing, T&D and G&A are inputs (1H-26 levels with modest leverage).')
        else:
            kw['ae_in'] = V0[f'{k}_pct']
        S(f'd_{k}_pct', f'  {lab} % of revenue', 'pct', 'pct', **kw)
        S(f'd_{k}_pre', '    Q3/Q4-26E ratio before calibration (prior-year quarter + 1H-26 drift)', 'driver', 'pct',
          qe=lambda k=k: (f'=IFERROR({P("d_ocor_x")}/{P("is_rev")},0)+{drift("d_ocor_x", "is_rev")}' if k == 'ocor'
                          else f'=IFERROR({P("is_" + k)}/{P("is_rev")},0)+{drift("is_" + k, "is_rev")}'))
    S('d_ocor_x', '  Other cost of revenues excl. company-quantified one-offs (Q3-25 Brazil non-income tax expense)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("is_ocor")}),{V("is_ocor")}-N({V("o_brazil")}),"")',
      qe=lambda: f'={V("is_rev")}*{V("d_ocor_pct")}', ae=lambda: f'={V("is_rev")}*(1-{V("d_om")})-{V("d_camort")}-{V("is_mkt")}-{V("is_td")}-{V("is_ga")}-N({V("d_oneoff")})')
    S('d_om', '  Operating-margin lever (2027E+; scenario)', 'driver', 'pct', ae=lambda: '=' + CH(SC['OM'][CTX.col.year]),
      note='2027E+: GAAP operating margin by scenario; other cost of revenues balances. FY2025 29.5%, FY26 guided 31.5% (+2pp a year since 2023).')
    S('d_oneoff', '  One-off operating items in the forecast (input; none assumed)', 'driver', 'm1', qe_in=0.0, ae_in=0.0)
    S('d_dep', '  Depreciation & amortization of property, equipment & intangibles (non-content D&A)', 'line', 'm1', data='cf_dep', flow=True,
      qe=lambda: f'={P("d_dep")}*(1+IFERROR({ACT("d_dep")}/{ACT0("d_dep")}-1,0))', ae=lambda: f'={V("is_rev")}*{V("d_dep_pct")}',
      note='Cash-flow statement. Q3/Q4-26E: prior-year quarter × 1H-26 y/y; 2027E+: % of revenue (input). Inside cost of revenues and opex.')
    S('d_dep_pct', '  Non-content D&A % of revenue', 'pct', 'pct', all=ratio('d_dep', 'is_rev'), ae_in=V0['dep_pct'])
    S('d_sbc', '  Stock-based compensation (cash-flow statement)', 'line', 'm1', data='cf_sbc', flow=True,
      qe=lambda: f'={P("d_sbc")}*(1+IFERROR({ACT("d_sbc")}/{ACT0("d_sbc")}-1,0))', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}',
      note='Q3/Q4-26E: prior-year quarter × 1H-26 y/y; 2027E+: % of revenue. Expensed in operating costs; added back only in the company adjusted EBITDA.')
    S('d_sbc_pct', '  Stock-based compensation % of revenue', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_adj_h', '  Adjusting items quantified by the company (pre-tax; model adjusted measures):', 'sub', 'gen')
    S('o_restr', '  Restructuring: severance and real-estate lease impairment (Q2-22, ~$150m)', 'line', 'm1', data='oa_restr', flow=True, fc=lambda: '=0',
      note=MAN['one_offs']['restructuring_q222']['src'])
    S('o_brazil', '  Brazilian non-income tax assessment expense (Q3-25, ~$619m; in cost of revenues)', 'line', 'm1', data='oa_brazil', flow=True, fc=lambda: '=0',
      note=MAN['one_offs']['brazil_q325']['src'])
    S('n_fee', '  WBD termination fee received (Q1-26, $2.8bn; in interest and other income) — gain, negative', 'line', 'm1', data='na_fee', flow=True, fc=lambda: '=0',
      note=MAN['one_offs']['wbd_fee_q126']['src'])
    S('n_fx', '  Foreign-currency remeasurement loss / (gain) on euro debt (in interest and other income; cash-flow statement, from 2017)', 'line', 'm1', data='na_fx', flow=True, fc=lambda: '=0')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENTS OF OPERATIONS (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (revenue from the regional build; content amortization and cost ratios from the cost drivers; operating income = the guidance / lever outcome)')
    S('is_rev', 'Revenues', 'total', 'm1', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the regional build.')
    S('is_cor', 'Cost of revenues', 'line', 'm1', data='cor', flow=True, fc=lambda: f'={V("is_camort")}+{V("is_ocor")}',
      note='2006–2011: subscription + fulfillment expenses (DVD era). Personnel costs reclassified into cost of revenues and marketing from Q4-2018 (2018 quarters recast).')
    S('is_camort', '  of which content amortization', 'line', 'm1', all=lambda: f'={V("d_camort")}')
    S('is_ocor', '  of which other cost of revenues (derived)', 'line', 'm1', hist=lambda: f'=IF(ISNUMBER({V("is_cor")}),{V("is_cor")}-{V("is_camort")},"")',
      fc=lambda: f'={V("d_ocor_x")}+N({V("d_oneoff")})')
    S('is_gp', 'Gross profit', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_cor")}),{V("is_rev")}-{V("is_cor")},"")')
    S('is_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('is_mkt', 'Marketing (sales and marketing from 2024)', 'line', 'm1', data='mkt', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_mkt_pct")}')
    S('is_td', 'Technology and development', 'line', 'm1', data='td', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_td_pct")}')
    S('is_ga', 'General and administrative', 'line', 'm1', data='ga', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_ga_pct")}')
    S('is_othop', 'Gain on disposal of DVDs / legal settlement (to 2011)', 'line', 'm1', data='oth_op', flow=True, fc=lambda: '=0')
    S('is_oi', 'Operating income', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("is_cor")}),{V("is_rev")}-{V("is_cor")}-{V("is_mkt")}-{V("is_td")}-{V("is_ga")}-N({V("is_othop")}),"")',
      note="Netflix's primary profit metric (company guides operating margin).")
    S('is_oi_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('is_oi_pub', '  Memo: operating income as reported', 'memo', 'm1', data='oi', flow=True)
    S('is_oi_chk', '  Check: operating income vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_oi_pub")}),IF(ABS({V("is_oi")}-{V("is_oi_pub")})<=0.15,0,ROUND({V("is_oi")}-{V("is_oi_pub")},1)),"")')
    S('is_int', 'Interest expense', 'line', 'm1', data='int_exp', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_rev")}*{V("ds_r_rev")}+{V("ds_fees")}',
      note='Q3/Q4-26E point estimate. 2027E+ = coupon rate × opening notes + rate × opening revolver + fees (no circularity).')
    S('is_oth', 'Interest and other income (expense)', 'line', 'm1', data='oth_inc', flow=True, qe=lambda: f'={PT("pt_oth")}',
      ae=lambda: f'=({P("cf_end")}+{P("bs_sti")})*{V("ds_r_cash")}',
      note='Interest income, F/X remeasurement of euro debt and hedging, and (Q1-26) the $2.8bn WBD termination fee. Forecast: yield on opening cash and investments; F/X nil.')
    S('is_ext', 'Loss on extinguishment of debt (2013–14)', 'line', 'm1', data='ext', flow=True, fc=lambda: '=0')
    S('is_ebt', 'Income before income taxes', 'line_b', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("is_oi")}),{V("is_oi")}-{V("is_int")}+{V("is_oth")}+N({V("is_ext")}),"")')
    S('is_tax', 'Provision for income taxes', 'line', 'm1', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Q3/Q4-26E: rate implied by the Q3-26 guide (net income $3,452m on operating income $4,268m). 2027E+: input.')
    S('is_ni', 'Net income', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_ni_chk', '  Check: net income vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=0.15,0,ROUND({V("is_ni")}-{V("is_ni_pub")},1)),"")')
    S('is_ni_pub', '  Memo: net income as reported', 'memo', 'm1', data='ni', flow=True)
    S('is_dda', '  Memo: non-content depreciation & amortization', 'memo_calc', 'm1', all=lambda: f'={V("d_dep")}')
    S('is_sbc', '  Memo: stock-based compensation', 'memo_calc', 'm1', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share — split-adjusted: 7-for-1 Jul-2015, 10-for-1 Nov-2025)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: (f'={B1("bs_shares")}-${E26}${R["bb_sh"]}*{0.25 if CTX.col.q == 3 else 0.75}+${E26}${R["bb_iss"]}*{0.25 if CTX.col.q == 3 else 0.75}'),
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q3/Q4-26E: shares outstanding at 30-Jun-2026 − 2H buybacks (half per quarter, mid-quarter) + plan issuance. 2027E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q2}{R["sh_dil"]}-{Q2}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")',
      note='Net income / weighted diluted shares (split-adjusted by the filing date of each source; Q4 from the Q4 letter three-month column).')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported, split-adjusted ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.005 split rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0051,0,ROUND({V("eps_dil")}-{V("eps_pub")},3)),"n/p")')
    S('dps', '  Dividends per share ($) — none paid', 'line', 'ps', fc=lambda: '=0')
    blank()

    # ------------------------------------------------------------------ RECON 1: OI -> adjusted OI (model)
    S('sec_r1', 'RECONCILIATION: OPERATING INCOME → ADJUSTED OPERATING INCOME (model definition: one-offs the company quantified)', 'section',
      note='ADJUSTED OPERATING INCOME — model definition; Netflix publishes no adjusted operating income (its "adjusted operating margin" is the F/X-neutral YTD margin)')
    S('o_op', 'Operating income (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_oi")}')
    S('o_r', '  (+) Restructuring (Q2-22)', 'line', 'm1', all=lambda: f'={V("o_restr")}')
    S('o_b', '  (+) Brazilian non-income tax expense (Q3-25)', 'line', 'm1', all=lambda: f'={V("o_brazil")}')
    S('o_tot', '  Total adjusting items (pre-tax)', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{nsum(["o_r", "o_b"])},"")')
    S('o_adj', '  = Adjusted operating income (model)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_tot")},"")')
    S('o_adj_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_chk', '  Check: model vs company-published (n/p — no company adjusted operating income)', 'check', 'm1', hist=lambda: '="n/p"')
    S('o_def', '  Definition / basis', 'text', 'gen', note='Definition notes in the columns where they apply (cell comments quote the company wording).')
    S('o_adj_g', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental adjusted operating margin (Δ adjusted OI / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: NI -> EBITDA -> adjusted EBITDA
    S('sec_r2', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (company definition, published Q2-14 – Q1-23)', 'section',
      note='ADJUSTED EBITDA — GAAP net income + interest and other (income) expense + taxes + D&A of property, equipment & intangibles + stock-based compensation (content amortization stays a cost)')
    S('r_ni', 'Net income (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('r_tax', '  (+) Provision for income taxes', 'line', 'm1', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest and other (income) expense, incl. debt extinguishment', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("is_int")}),{V("is_int")}-{V("is_oth")}-N({V("is_ext")}),"")')
    S('r_oi', '  = Operating income', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_tax")}+{V("r_int")},"")')
    S('r_dep', '  (+) Depreciation & amortization of property, equipment & intangibles', 'line', 'm1', all=lambda: f'={V("d_dep")}')
    S('r_ebitda', '  = EBITDA', 'total', 'm1', all=lambda: f'=IF(AND(ISNUMBER({V("r_oi")}),ISNUMBER({V("r_dep")})),{V("r_oi")}+{V("r_dep")},"")')
    S('r_sbc', '  (+) Stock-based compensation', 'line', 'm1', all=lambda: f'={V("d_sbc")}')
    S('r_adj', '  = Adjusted EBITDA (company definition)', 'total', 'm1', all=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda")}),ISNUMBER({V("r_sbc")})),{V("r_ebitda")}+{V("r_sbc")},"")',
      note='Company definition (letters Q2-15 – Q1-23, quarters Q2-14 – Q1-23); rebuilt on the same definition in every other period. Leverage and EV / EBITDA use it.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_adj_pub', '  Company-published adjusted EBITDA', 'memo', 'm1', data='adj_ebitda_pub', flow=True)
    S('r_chk', '  Check: model vs company-published adjusted EBITDA (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("r_adj_pub")}),ISNUMBER({V("r_adj")})),IF(ABS({V("r_adj")}-{V("r_adj_pub")})<=0.15,0,ROUND({V("r_adj")}-{V("r_adj_pub")},1)),"n/p")')
    S('r_def', '  Definition / basis', 'text', 'gen')
    S('r_x', '  (+) Company-quantified operating one-offs (bridge above)', 'line', 'm1', all=lambda: f'={V("o_tot")}')
    S('r_adjx', '  = Adjusted EBITDA excl. one-offs (model)', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+{V("r_x")},"")')
    S('r_ebit_h', 'To adjusted EBIT, full-cost (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ddan', '  (−) Non-content D&A and stock-based compensation', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_dep")}),-{V("r_dep")}-{V("r_sbc")},"")')
    S('r_ebit', '  = Adjusted EBIT, full-cost (= adjusted operating income: after content amortization, D&A and SBC)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_adjx")}),{V("r_adjx")}+{V("r_ddan")},"")')
    S('r_ebit_m', '  Adjusted EBIT (full-cost) margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_ebit_chk', '  Check: adjusted EBIT vs adjusted operating income bridge (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_ebit")}),ROUND({V("r_ebit")}-{V("o_adj")},1),"")')
    S('r_cash', '  Memo: company-quantified one-offs treated as cash costs (deducted in the DCF)', 'memo_calc', 'm1', all=lambda: f'={V("o_tot")}')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: NET INCOME → NON-GAAP / ADJUSTED NET INCOME → ADJUSTED EPS (company definition in force where published; model otherwise)', 'section',
      note='ADJUSTED EPS — company non-GAAP net income where published (2006–2009 excl. stock-based compensation; Q1-13, Q4-14, Q1-15, Q4-15); otherwise GAAP + company-quantified items, tax-effected')
    S('e_ni', 'Net income (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('e_op', '  (+) Operating one-offs (bridge 1)', 'line', 'm1', all=lambda: f'={V("o_tot")}')
    S('e_sbc', '  (+) Stock-based compensation (company non-GAAP definition, FY2006–09)', 'line', 'm1', data='ng_sbc', flow=True, fc=lambda: '=0')
    S('e_fx', '  (+) F/X remeasurement loss / (gain) on euro debt (2017+; Q1-15 company "foreign exchange impact")', 'line', 'm1', all=lambda: f'=N({V("n_fx")})')
    S('e_ext', '  (+) Loss on extinguishment of debt', 'line', 'm1', all=lambda: f'=-N({V("is_ext")})')
    S('e_fee', '  (−) WBD termination fee (Q1-26)', 'line', 'm1', all=lambda: f'=N({V("n_fee")})')
    S('e_pre', '  Total pre-tax items', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("e_ni")}),{nsum(["e_op", "e_sbc", "e_fx", "e_ext", "e_fee"])},"")')
    S('e_tax', '  (−) Tax effect of the items (and tax-accrual releases Q4-14 / Q4-15)', 'line', 'm1', flow=True,
      hist=lambda: SUMQ('e_tax') if (CTX.col.kind == 'A' and CTX.col.year >= FYQ0) else (f'=IF(ISNUMBER({V("e_pubni")}),{V("e_pubni")}-{V("e_ni")}-{V("e_pre")},IF(ISNUMBER({V("e_ni")}),-{V("e_pre")}*MAX(0.15,MIN(0.4,IFERROR({V("is_etr")}+0,0.21))),""))'),
      fc=lambda: f'=-{V("e_pre")}*{V("is_etr")}',
      note='Published periods: company non-GAAP net income − GAAP − pre-tax items. Other periods: pre-tax items × the period effective tax rate bounded to 15–40% (assumption; Netflix gives no tax effect).')
    S('e_adjni', '  = Adjusted net income', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("e_tax")}),{V("e_ni")}+{V("e_pre")}+{V("e_tax")},"")')
    S('e_pubni', '  Company-published non-GAAP net income', 'memo', 'm1', data='ng_ni_pub', flow=True)
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted EPS – diluted ($)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published non-GAAP EPS – diluted, split-adjusted ($)', 'eps_memo', 'ps', data='ng_eps_pub')
    S('e_chk', '  Check: model vs company-published non-GAAP EPS (should be 0.00; ±0.005 split rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0051,0,ROUND({V("e_eps")}-{V("e_pub")},3)),"n/p")')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_def', '  Definition / basis (company non-GAAP net income in force)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Revenue y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_ucan', '  UCAN revenue y/y %', 'growth', 'pct', all=growth('ucan_rev'))
    S('gm_intl', '  International (EMEA + LATAM + APAC) revenue y/y %', 'growth', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("emea_rev")}),ISNUMBER({P("emea_rev")})),IFERROR(({V("emea_rev")}+{V("latam_rev")}+{V("apac_rev")})/({P("emea_rev")}+{P("latam_rev")}+{P("apac_rev")})-1,""),"")'
                   if CTX.col.prior else None))
    S('gm_oi', '  Operating income y/y %', 'growth', 'pct', all=growth('is_oi'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_ni', '  Net income y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('gm_camort', '  Content amortization % of revenue', 'pct', 'pct', all=ratio('d_camort', 'is_rev'))
    S('gm_op_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('gm_inc', '  Incremental operating margin (Δ OI / Δ revenue)', 'pct', 'pct', all=incr('is_oi', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_mkt', '  Marketing % of revenue', 'pct', 'pct', all=ratio('is_mkt', 'is_rev'))
    S('gm_td', '  Technology & development % of revenue', 'pct', 'pct', all=ratio('is_td', 'is_rev'))
    S('gm_ga', '  G&A % of revenue', 'pct', 'pct', all=ratio('is_ga', 'is_rev'))
    blank()
