"""Row specification of the GHM Model sheet, part 1 (MLM template layout and process):
sales by market (Defense / Space / Energy & Process, current basis from FY2020; legacy industry split as memo) with the FlackTek
acquisition increment -> orders, backlog and book-to-bill -> M&A lever -> group total & FY27 guidance calibration (sales Δ, then
gross-margin Δ to Adjusted EBITDA) -> cost drivers & adjusting items -> income statement -> GAAP-to-adjusted bridges -> growth &
margins."""
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
def ECa(key): return f'${EC}${R[key]}'                    # FY2027E column (absolute)
def ACT(key): return f'{Q1}{R[key]}'                      # actual year to date FY27 (Q1/27)
def ACT0(key): return f'{PQ1}{R[key]}'                    # prior-year year to date (Q1/26)
def B1(key): return f'{LQ}{R[key]}'                       # 30-Jun-2026 balance
def SQE(key): return f'SUM({QE1}{R[key]}:{QE3}{R[key]})'  # Q2-Q4/27E
def LTM(key):                                               # trailing four quarters to Q1/27 (Q2/26-Q1/27)
    return '(' + '+'.join(f'{QC[k].c}{R[key]}' for k in ((2026, 2), (2026, 3), (2026, 4), (2027, 1))) + ')'
def LTM0(key):                                              # the same four quarters a year earlier (Q2/25-Q1/26)
    return '(' + '+'.join(f'{QC[k].c}{R[key]}' for k in ((2025, 2), (2025, 3), (2025, 4), (2026, 1))) + ')'
def chk(a, b, tol=0.0015, nd=3):
    return f'=IF(AND(ISNUMBER({V(a)}),ISNUMBER({V(b)})),IF(ABS({V(a)}-{V(b)})<={tol},0,ROUND({V(a)}-{V(b)},{nd})),"")'
def chk_np(a, b, tol=0.0015, nd=3):
    return f'=IF(AND(ISNUMBER({V(a)}),ISNUMBER({V(b)})),IF(ABS({V(a)}-{V(b)})<={tol},0,ROUND({V(a)}-{V(b)},{nd})),"n/p")'

MK = [('def', 'Defense', 'DEF', 'cb_defense', 'defense'), ('space', 'Space', 'SPACE', 'cb_space', 'space'),
      ('ep', 'Energy & Process', 'EP', 'cb_ep', 'ep')]
MKEYS = [f'mk_{m}' for m, *_ in MK]
FT = MAN['flacktek']
FTQ = round((FT['fy27_run_rate'] - FT['sales']['Q1-27']) / 3.0, 3)

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of the FY27 guidance ranges.'))
    r = 11
    SCEN_ROWS.append((r, 'out_hdr', V0['out_hdr'], 'High', 'Mid', 'Low', V0['out_note'])); r += 1
    for key, lab, (hi, mid, lo), nf, note in V0['outlook']:
        SC[key] = r; SCEN_ROWS.append((r, 'out', lab, hi, mid, lo, note, nf)); r += 1
    r += 1
    SCEN_ROWS.append((r, 'pt_hdr', 'Q2–Q4/27E and FY27 point estimates (all cases)', None, None, None, None)); r += 1
    for key, lab, vals, nf, note in V0['points']:
        SC[key] = r
        SCEN_ROWS.append((r, 'pt', lab, None, vals, None, note, nf)); r += 1
    r += 1
    SC['LEV'] = r
    SCEN_ROWS.append((r, 'lev', '  Target net debt / adjusted EBITDA (x; negative = net cash cap) — buyback floor 2028E+', *V0['lev'], V0['lev_note']))
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
    # ------------------------------------------------------------------ MARKET BUILD
    S('sec_mk', 'SALES BY MARKET — DEFENSE · SPACE · ENERGY & PROCESS (single reportable segment)', 'section',
      note='MARKET BUILD — modelling logic (sales by market → net sales; orders = sales × book-to-bill; backlog roll-forward; FlackTek increment explicit until its 23-Jan-2027 anniversary)')
    blank()
    S('mk_hdr', 'Net sales by market — current basis (Defense / Space / Energy & Process; FY2020+, latest presentation)', 'block',
      note='MARKETS — modelling logic: Q2–Q4/27E = prior-year quarter × (1 + trailing-four-quarter organic y/y + sales-calibration Δ) + FlackTek increment × market share; 2028E+ = prior year × (1 + scenario lever)')
    for m, title, code, dk, _ in MK:
        key = f'mk_{m}'
        S(key, f'  {title}', 'line', 'm1', data=dk, flow=True,
          qe=lambda key=key, m=m: f'={P(key)}*(1+{V(key + "_g")})+{V("ft_inc")}*{V("ft_sh_" + m)}',
          ae=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})',
          note=('Release supplemental tables / 10-K and 10-Q revenue note. Defense and Space from FY2020 (Space nil before Barber-Nichols, Jun-2021); '
                'Energy & Process = net sales − Defense − Space where the company published the legacy industry split.') if m == 'def' else None)
        S(key + '_g', '    y/y %', 'growth', 'pct', all=growth(key),
          qe=lambda key=key: f'={V(key + "_pre")}+{ECa("cal_g")}',
          ae=lambda key=key, code=code: '=' + CH(SC[f'{code}_G'][CTX.col.year]),
          note='Q2–Q4/27E: trailing-four-quarter organic y/y (ex FlackTek) + sales-guidance calibration Δ. 2028E–2031E: scenario lever (table →).' if m == 'def' else None)
        S(key + '_pre', '    Q2–Q4/27E organic growth before calibration (four quarters to Q1/27 vs a year earlier, ex FlackTek)', 'driver', 'pct',
          qe=lambda key=key, m=m: f'=IFERROR(({LTM(key)}-{LTM("ft_rev")}*{V("ft_sh_" + m)})/{LTM0(key)}-1,0)',
          note=('Trailing four quarters rather than Q1/27 alone: sales are recognised over time on milestone-driven projects, so single-quarter y/y is noisy '
                '(Q1/27 Defense +40% on "timing of project milestones").') if m == 'def' else None)
        S(key + '_mix', '    % of net sales', 'pct', 'pct', all=ratio(key, 'g_rev'))
    S('mk_tot', '  Net sales — market build', 'line_b', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("mk_def")}),{V("mk_def")}+{V("mk_space")}+{V("mk_ep")},{V("is_rev")})',
      fc=lambda: f'={V("mk_def")}+{V("mk_space")}+{V("mk_ep")}',
      note='History: Σ markets where the current basis is published (FY2020+), otherwise consolidated net sales.')
    S('mk_tot_g', '  Net sales y/y %', 'growth', 'pct', all=growth('mk_tot'))
    S('mk_chk', '  Check: markets vs consolidated net sales (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("mk_def")}),IF(ABS({V("mk_tot")}-{V("is_rev")})<=0.0015,0,ROUND({V("mk_tot")}-{V("is_rev")},3)),"")')
    S('gc_def', '  Contribution to sales growth — Defense (pp)', 'growth', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("mk_def")}),ISNUMBER({P("mk_def")})),IFERROR(({V("mk_def")}-{P("mk_def")})/{P("g_rev")},""),"")' if CTX.col.prior else None))
    S('gc_oth', '  Contribution to sales growth — Space + Energy & Process (pp)', 'growth', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("mk_def")}),ISNUMBER({P("mk_def")})),IFERROR(({V("mk_space")}+{V("mk_ep")}-{P("mk_space")}-{P("mk_ep")})/{P("g_rev")},""),"")' if CTX.col.prior else None))
    S('rg_us', '  Memo: sales to the United States', 'memo', 'm1', data='rg_us', flow=True)
    S('rg_us_p', '    United States % of net sales', 'pct', 'pct', hist=ratio('rg_us', 'is_rev'))
    S('lg_h', '  Legacy industry split as originally reported (release grids, USD m to one decimal to FY2022; 10-K / 10-Q revenue note from FY2023):', 'sub', 'gen')
    for k, lab in (('refining', 'Refining'), ('chem', 'Chemical / petrochemical'), ('power', 'Power (incl. nuclear) / "Energy & New Energy"'),
                   ('defense', 'Defense (as published; inside "Other" before FY2017)'), ('space', 'Space'),
                   ('other', 'Other commercial & industrial (incl. defense FY2015–19; "Other" until FY2024)'), ('ep', 'Energy & Process (FY2025 presentation)')):
        S(f'lg_{k}', f'    {lab}', 'memo', 'm1', data=f'mk_{k}', flow=True)
    S('lg_chk', '    Check: legacy split vs net sales (should be 0; ±0.35 where the grid is in USD m to one decimal)', 'check', 'm1',
      hist=lambda: (f'=IF(COUNT({V("lg_refining")}:{V("lg_ep")})>0,IF(ABS(SUM({V("lg_refining")}:{V("lg_ep")})-{V("is_rev")})<=0.36,0,'
                    f'ROUND(SUM({V("lg_refining")}:{V("lg_ep")})-{V("is_rev")},2)),"")'))
    blank()

    # ------------------------------------------------------------------ FlackTek
    S('ft_hdr', 'FlackTek acquisition (advanced mixing; closed 23-Jan-2026; $37.0m incl. shares and earn-out) — inorganic until 23-Jan-2027', 'block',
      note='FLACKTEK — sales inside the market lines; the y/y increment is added explicitly so the organic trend is not inflated by the acquisition')
    S('ft_rev', '  FlackTek net sales (included in the market lines)', 'line', 'm1', flow=True,
      hist_in=lambda: FT['sales'].get(pkey(CTX.col)) if FT['sales'].get(pkey(CTX.col)) is not None else (FT['sales']['Q4-26'] if CTX.col.c == A26 else None),
      qe_in=FTQ, note=FT['sales_src'] + f' Q2–Q4/27E: (~$30m FY27 expectation − Q1 actual) ÷ 3 = ${FTQ}m a quarter (Investor Day 8-K, 18-Jun-2026).')
    S('ft_inc', '  FlackTek y/y increment (inorganic sales)', 'line', 'm1', flow=True,
      qe=lambda: f'={V("ft_rev")}-N({P("ft_rev")})', note='Q4/27E increment = Q4 sales − the 68-day Q4/26 stub ($2.8m).')
    for m, title, *_ in MK:
        S(f'ft_sh_{m}', f'  FlackTek sales allocated to {title} (assumption)', 'driver', 'pct', qe_in=FT['market_share'][m],
          note=FT['market_share_note'] if m == 'def' else None)
    S('ft_m', '  Memo: FY27 FlackTek Adjusted EBITDA expectation (~$3m) — information', 'memo', 'm1', ec_in=3.0)
    blank()

    # ------------------------------------------------------------------ ORDERS & BACKLOG
    S('ob_hdr', 'Orders, backlog & book-to-bill (key performance indicators; release order & backlog trend tables, USD m)', 'block',
      note='BACKLOG — orders = net sales × book-to-bill; backlog = opening + orders − net sales (+ historical adjustments: cancellations, FX, acquired backlog)')
    S('ob_ord', '  Orders', 'line', 'm1', data='orders', flow=True, fc=lambda: f'={V("is_rev")}*{V("ob_b2b")}',
      note='As published (USD m to one decimal; FY2023+ supplemental tables in USD thousands). Forecast = net sales × book-to-bill.')
    S('ob_b2b', '  Book-to-bill (orders ÷ net sales)', 'driver', 'x2', all=ratio('ob_ord', 'is_rev'),
      qe=lambda: f'={PT("pt_b2b")}', ae=lambda: '=' + CH(SC['B2B'][CTX.col.year]),
      note='Q2–Q4/27E 1.0x (Navy awards are lumpy). 2028E+: scenario lever.')
    S('ob_bkl', '  Backlog (period end)', 'line_b', 'm1', data='backlog',
      qe=lambda: f'={PQ("ob_bkl")}+{V("ob_ord")}-{V("is_rev")}', ec=lambda: f'={V("ob_bkl", QE3)}',
      ae=lambda: f'={P("ob_bkl")}+{V("ob_ord")}-{V("is_rev")}')
    S('ob_adj', '  Backlog adjustments (closing − opening − orders + sales; cancellations, FX, acquired backlog — FlackTek $6.1m FY26)', 'line', 'm1',
      all=lambda: ((f'=IF(AND(ISNUMBER({V("ob_bkl")}),ISNUMBER({(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ob_bkl"]})),'
                    f'ROUND({V("ob_bkl")}-{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ob_bkl"]}-{V("ob_ord")}+{V("is_rev")},1),"")')
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None), qe=lambda: '=0', ec=lambda: '=0', ae=lambda: '=0')
    S('ob_g', '  Backlog y/y %', 'growth', 'pct', all=growth('ob_bkl'))
    S('ob_cov', '  Backlog ÷ annualised net sales (years)', 'line', 'x2',
      all=lambda: f'=IF(ISNUMBER({V("ob_bkl")}),IFERROR({V("ob_bkl")}/({V("is_rev")}*{4 if CTX.col.q else 1}),""),"")')
    for k, lab in (('defense', 'Defense'), ('space', 'Space'), ('ep', 'Energy & Process')):
        S(f'om_{k}', f'  Memo: orders — {lab} (FY2022+)', 'memo', 'm1', data=f'om_{k}', flow=True)
    for k, lab in (('defense', 'Defense'), ('space', 'Space'), ('ep', 'Energy & Process')):
        S(f'bm_{k}', f'  Memo: backlog — {lab} (FY2023+)', 'memo', 'm1', data=f'bm_{k}')
    S('bm_def_p', '    Defense % of backlog', 'pct', 'pct', hist=ratio('bm_defense', 'ob_bkl'))
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — bolt-ons in fluid, power, thermal and mixing technologies; from 2028E)', 'block',
      note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', ec_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=1.5, ec_in=0.0,
      note='Barber-Nichols (Jun-2021) $72.0m on ~$48m FY22 sales (~1.5x); FlackTek (Jan-2026) $37.0m on ~$30m (~1.2x); P3 (Nov-2023) $11.2m. 1.5x input (assumption).')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', ec_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', ec_in=0.0, ae_in=0.06)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', ec_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', ec_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}',
      note='Mid-year convention.')
    S('m_m', '  Adjusted EBITDA margin of acquired businesses %', 'driver', 'pct', ec_in=0.0, ae_in=0.12,
      note='FlackTek ~10% (~$3m on ~$30m, Investor Day). 12% input (assumption).')
    S('m_eb', '  Adjusted EBITDA from future acquisitions', 'line', 'm', ec_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', ec_in=0.0, ae_in=0.06, note='FlackTek 5%, P3 5%, Barber-Nichols 11% of the purchase price.')
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', ec_in=0.0, ae_in=0.50,
      note='Intangibles: FlackTek 63% (incl. $6.7m indefinite-lived tradename), P3 64%, Barber-Nichols 45% of the purchase price.')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', ec_in=0, ae_in=12, note='Customer relationships 8–20 years, technology 9–20 years (10-K Note 5).')
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', ec_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles', 'line', 'm', ec_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group total — net sales & Adjusted EBITDA → FY27 guidance calibration', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic: step 1 solves a uniform growth Δ on the markets to FY27 sales guidance; step 2 solves a uniform gross-margin Δ to FY27 Adjusted EBITDA guidance')
    S('g_rev', 'Net sales (build)', 'total', 'm1',
      hist=lambda: f'={V("mk_tot")}', fc=lambda: f'={V("mk_tot")}+N({V("m_rev")})',
      note='Σ markets (+ future acquisitions from 2028E).')
    S('g_rev_g', '  Net sales y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: build vs consolidated net sales (should be 0)', 'check', 'm1', all=lambda: chk('g_rev', 'is_rev').replace(',"")', ',"")'))
    S('cal_guid', '  Memo: FY27 net sales guidance (scenario end-point: high / mid / low)', 'memo', 'm1', ec=lambda: '=' + CH(SC['out_rev']), note=V0['rev_guid_note'])
    S('cal_pre', '  Net sales before calibration (Q2–Q4/27E helper)', 'line', 'm1',
      qe=lambda: '=' + '+'.join(f'{P("mk_" + m)}*(1+{V("mk_" + m + "_pre")})' for m, *_ in MK) + f'+{V("ft_inc")}')
    S('cal_sens', '  Net sales sensitivity to +1.00 of growth (Q2–Q4/27E helper)', 'line', 'm1',
      qe=lambda: '=' + '+'.join(P('mk_' + m) for m, *_ in MK))
    S('cal_g', '  Guidance calibration: Δ y/y growth applied to all markets (Q2–Q4/27E)', 'driver', 'pct',
      ec=lambda: f'=({V("cal_guid")}-{ACT("is_rev")}-{SQE("cal_pre")})/{SQE("cal_sens")}',
      note='Closed-form solve (no goal seek): Δ = (guidance end-point − Q1 actual − Σ pre-calibration sales) ÷ Σ sensitivity.')
    S('cal_rev_chk', '  Check: FY27 net sales vs guidance end-point (should be 0)', 'check', 'm1', ec=lambda: f'=ROUND({V("g_rev")}-{V("cal_guid")},3)')
    S('cal_eb', '  Memo: FY27 Adjusted EBITDA guidance (scenario end-point)', 'memo', 'm1', ec=lambda: '=' + CH(SC['out_eb']), note=V0['eb_guid_note'])
    S('cal_sga_i', '  Memo: FY27 SG&A incl. amortization % of sales guidance (scenario end-point: 16.5% / 17.0% / 17.5%)', 'memo', 'pct', ec=lambda: '=' + CH(SC['out_sga']))
    S('cal_gm_pre', '  Gross margin before calibration (prior-year quarter + Q1/27 y/y drift; Q2–Q4/27E helper)', 'driver', 'pct',
      qe=lambda: f'={P("d_gm")}+IFERROR({ACT("is_gp")}/{ACT("is_rev")}-{ACT0("is_gp")}/{ACT0("is_rev")},0)')
    S('cal_sga_q', '  SG&A (excl. amortization line) % of sales for Q2–Q4/27E, solved to the FY27 SG&A guidance end-point', 'driver', 'pct',
      ec=lambda: f'=({V("cal_sga_i")}*{V("is_rev")}-{ACT("is_sga")}-{V("is_amort")})/{SQE("is_rev")}',
      note='Guided driver applied first, then the margin solve: FY27 SG&A incl. amortization = 16.5% / 17.0% / 17.5% of sales (Bull / Base / Bear).')
    S('cal_eb_pre', '  Adjusted EBITDA before margin calibration (Q2–Q4/27E helper)', 'line', 'm1',
      qe=lambda: (f'={V("is_rev")}*{V("cal_gm_pre")}-{V("is_sga")}-{V("is_amort")}-{V("is_othop")}-{V("is_othnon")}'
                  f'+{V("d_da")}+{V("o_items_eb")}'))
    S('cal_m', '  Guidance calibration: Δ gross margin (Q2–Q4/27E)', 'driver', 'pct',
      ec=lambda: f'=({V("cal_eb")}-{ACT("r_adj")}-{SQE("cal_eb_pre")})/{SQE("is_rev")}',
      note='Closed-form: Adjusted EBITDA is linear in gross margin with sensitivity = net sales.')
    S('cal_eb_chk', '  Check: FY27 Adjusted EBITDA vs guidance end-point (should be 0)', 'check', 'm1', ec=lambda: f'=ROUND({V("r_adj")}-{V("cal_eb")},3)')
    S('cal_gm_i', '  Memo: FY27 gross margin guidance (high / mid / low) — information, not forced', 'memo', 'pct', ec=lambda: '=' + CH(SC['out_gm']))
    S('cal_gm_d', '    Model gross margin − guidance (pp)', 'memo_calc', 'pct', ec=lambda: f'={V("is_gm")}-{V("cal_gm_i")}')
    S('cal_sga_chk', '  Check: FY27 SG&A incl. amortization % vs guidance end-point (should be 0)', 'check', 'pct',
      ec=lambda: f'=ROUND(({V("is_sga")}+{V("is_amort")})/{V("is_rev")}-{V("cal_sga_i")},6)')
    S('cal_it_i', '  Memo: FY27 excluded items (SBC, acquisition & integration, ERP) guidance ~$5.5–6.5m — information', 'memo', 'm1', ec=lambda: '=' + CH(SC['out_items']))
    S('cal_it_d', '    Model items − guidance', 'memo_calc', 'm1', ec=lambda: f'={V("o_items_eb")}-{V("cal_it_i")}')
    S('cal_cx_i', '  Memo: FY27 capital expenditures guidance ($18–22m) — information', 'memo', 'm1', ec=lambda: '=' + CH(SC['out_capex']))
    S('id_g', '  Memo: Investor Day FY27–FY29 organic revenue CAGR target 8–10% — model FY26–29E net sales CAGR (information)', 'memo_calc', 'pct',
      ae=lambda: (f'=({V("g_rev")}/{Y("g_rev", 2026)})^(1/3)-1' if CTX.col.year == 2029 else None))
    S('id_m', '  Memo: Investor Day FY29 Adjusted EBITDA margin target 14–16% — model (information)', 'memo_calc', 'pct',
      ae=lambda: (f'={V("r_adj_m")}' if CTX.col.year == 2029 else None))
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A & adjusting items', 'block', note='COST DRIVERS — Q2–Q4/27E point estimates and calibrated gross margin; 2028E+ scenario levers / % of sales / schedules')
    S('d_gm', '  Gross margin % (GAAP, after D&A in cost of products sold)', 'driver', 'pct', all=ratio('is_gp', 'is_rev'),
      qe=lambda: f'={V("cal_gm_pre")}+{ECa("cal_m")}', ae=lambda: '=' + CH(SC['GM'][CTX.col.year]),
      note='Q2–Q4/27E: prior-year quarter + Q1/27 y/y drift + calibration Δ (Adjusted EBITDA guidance). 2028E+: scenario lever.')
    S('d_sga', '  SG&A (excl. the separate amortization line) % of net sales', 'driver', 'pct', all=ratio('is_sga', 'is_rev'),
      qe=lambda: f'={ECa("cal_sga_q")}', ae_in=V0['sga_pct'],
      note='Includes SBC, acquisition & integration and ERP costs and the ~$2.5m FY27 investment programme. Q2–Q4/27E: solved to the FY27 SG&A guidance (Group block); 2028E+ input (operating leverage).')
    S('d_dep', '  Depreciation (cash-flow statement)', 'line', 'm1', data='cf_dep', flow=True, qe=lambda: f'={PT("pt_dep")}', ae=lambda: f'={V("is_rev")}*{V("d_dep_pct")}',
      note='FY2006–FY2010 releases show depreciation and amortization combined (in this row).')
    S('d_dep_pct', '  Depreciation % of net sales', 'pct', 'pct', all=ratio('d_dep', 'is_rev'), ae_in=V0['dep_pct'])
    S('d_amort', '  Amortization of intangibles & inventory step-up (cash-flow statement)', 'line', 'm1', data='cf_amort', flow=True,
      qe=lambda: f'={PT("pt_amort")}', ae=lambda: f'={V("d_amort_sch")}+N({V("m_amort")})',
      note='Q2–Q4/27E: 10-Q schedule ($2.8m remaining FY27 ÷ 3). 2028E+: schedule + future-acquisition amortization.')
    S('d_amort_sch', '  Amortization schedule — intangibles held at 30-Jun-2026 (10-Q, input)', 'driver', 'm1', ae_in=V0['amort_sched'], note=V0['amort_note'])
    S('d_amort_sh', '  Share of amortization shown on the SG&A–amortization line (rest in cost of products sold)', 'driver', 'pct',
      hist=lambda: f'=IF(AND(ISNUMBER({V("is_amort")}),N({V("d_amort")})>0),IFERROR({V("is_amort")}/{V("d_amort")},""),"")',
      qe=lambda: f'={ACT("is_amort")}/{ACT("d_amort")}', ae=lambda: f'={ECa("d_amort_sh")}', ec=lambda: f'={V("is_amort")}/{V("d_amort")}')
    S('d_da', '  Depreciation & amortization (total; Adjusted EBITDA reconciliation)', 'line', 'm1', data='eb_dda', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("d_dep")}),{V("d_dep")}+N({V("d_amort")}),"")', fc=lambda: f'={V("d_dep")}+{V("d_amort")}',
      note='As published in the EBITDA reconciliations (FY2011+); earlier: cash-flow statement depreciation and amortization.')
    S('d_sbc', '  Equity-based compensation (cash-flow statement)', 'line', 'm1', data='cf_sbc', flow=True, qe=lambda: f'={PT("pt_sbc")}',
      ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}', note='Added back in Adjusted EBITDA from Q4 FY2024 (not in adjusted net income).')
    S('d_sbc_pct', '  Equity-based compensation % of net sales', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_othnon', '  Other (income) expense, net — non-operating (pension non-service cost etc.), input', 'line', 'm1', qe=lambda: f'={PT("pt_othnon")}', ae_in=V0['othnon'])
    S('d_adj_h', '  Adjusting items (pre-tax, excluded from Adjusted EBITDA by the company; forecast inputs):', 'sub', 'gen')
    S('d_acq', '  Acquisition & integration expense (income), net (incl. contingent earn-out fair-value changes, inventory step-up)', 'line', 'm1',
      data='eb_acq', flow=True, labkey='eb_acq_lab', qe=lambda: f'={PT("pt_acq")}', ae=lambda: f'={V("m_spend")}*{V("d_acq_pct")}+{V("d_eo")}',
      note='Q2–Q4/27E: FlackTek integration and earn-out fair-value accretion (point estimate). 2028E+: % of M&A spend + earn-out accretion input.')
    S('d_acq_pct', '  Acquisition costs % of acquisition spend', 'pct', 'pct', ae_in=0.03)
    S('d_eo', '  FlackTek earn-out fair-value accretion (input; liability $7.1m at 30-Jun-2026, maximum $25m)', 'driver', 'm1', ae_in={2028: 0.8, 2029: 0.5, 2030: 0.3, 2031: 0.0})
    S('d_erp', '  ERP implementation costs (Batavia go-live 2Q FY27)', 'line', 'm1', data='eb_erp', flow=True, labkey='eb_erp_lab', qe=lambda: f'={PT("pt_erp")}', ae_in=0.0)
    S('d_restr', '  Restructuring, severance & CEO / CFO transition', 'line', 'm1', data='eb_restr', flow=True, labkey='eb_restr_lab', fc=lambda: '=0')
    S('d_impair', '  Impairments, bad debt and loss on the commercial nuclear utility business (FY2018–20)', 'line', 'm1', data='eb_impair', flow=True,
      labkey='eb_impair_lab', fc=lambda: '=0')
    S('d_oadj', '  Other items (Barber-Nichols performance bonus FY2024, debt amendment costs, ERC tax credit)', 'line', 'm1', data='eb_oth', flow=True,
      labkey='eb_oth_lab', fc=lambda: '=0')
    S('o_items_eb', '  Total items excluded from Adjusted EBITDA (incl. equity-based compensation from Q4 FY2024)', 'line_b', 'm1', flow=True,
      all=lambda: f'=IF(ISNUMBER({V("d_acq")}),{nsum(["d_acq", "d_erp", "d_restr", "d_impair", "d_oadj"])}+N({V("r_sbc")}),"")')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF OPERATIONS (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (gross profit = net sales × calibrated gross margin; SG&A % of sales; interest on opening balances)')
    S('is_rev', 'Net sales', 'total', 'm1', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the market build.')
    S('is_cogs', 'Cost of products sold (incl. technology amortization)', 'line', 'm1', data='cogs', flow=True, fc=lambda: f'={V("is_rev")}-{V("is_gp")}')
    S('is_gp', 'Gross profit', 'line_b', 'm1', flow=True, hist=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_rev")}-{V("is_cogs")},"")',
      fc=lambda: f'={V("is_rev")}*{V("d_gm")}')
    S('is_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('is_sga', 'Selling, general & administrative', 'line', 'm1', data='sga', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_sga")}')
    S('is_amort', 'Selling, general & administrative — amortization', 'line', 'm1', data='amort', flow=True, fc=lambda: f'={V("d_amort")}*{V("d_amort_sh")}')
    S('is_restr', 'Restructuring charge (FY2015, FY2017–18)', 'line', 'm1', data='restr', flow=True, fc=lambda: '=0')
    S('is_impair', 'Impairment of goodwill and intangible assets (FY2018–19)', 'line', 'm1', data='impair', flow=True, fc=lambda: '=0')
    S('is_othop', 'Other operating expense (income), net (earn-out fair value, severance, other)', 'line', 'm1', data='oth_op', flow=True, labkey='oth_op_labels',
      fc=lambda: '=0', note='Forecast nil: earn-out fair-value changes and other items are assumed within SG&A (adjusting items above).')
    S('is_op', 'Operating profit (loss)', 'total', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("is_gp")}),{V("is_gp")}-{V("is_sga")}-{V("is_amort")}-{V("is_restr")}-{V("is_impair")}-{V("is_othop")},"")',
      fc=lambda: f'={V("is_gp")}-{V("is_sga")}-{V("is_amort")}-{V("is_restr")}-{V("is_impair")}-{V("is_othop")}')
    S('is_op_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('is_op_pub', '  Memo: operating profit as reported (Q1 FY22: no line on the face; derived)', 'memo', 'm1', data='op', flow=True)
    S('is_op_chk', '  Check: operating profit vs reported (should be 0)', 'check', 'm1', hist=lambda: chk('is_op', 'is_op_pub'))
    S('is_int', 'Net interest expense (income)', 'line', 'm1', data='int_net', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'={P("ds_rev")}*{V("ds_r_rev")}+{V("ds_fees")}-{P("cf_end")}*{V("ds_r_cash")}',
      note='Q2–Q4/27E point estimate (no debt; interest income on cash). 2028E+ = revolver rate × opening revolver + fees − yield × opening cash (no circularity). FY2021: the statement line also held other income ($0.1m), split per the EBITDA reconciliation.')
    S('is_othnon', 'Other expense (income), net — non-operating (incl. FY2024 loss on debt extinguishment)', 'line', 'm1', data='oth_nonop', flow=True,
      labkey='oth_nonop_labels', fc=lambda: f'={V("d_othnon")}')
    S('is_ebt', 'Income (loss) before income taxes', 'line_b', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("is_op")}),{V("is_op")}-{V("is_int")}-{V("is_othnon")},"")')
    S('is_tax', 'Provision (benefit) for income taxes', 'line', 'm1', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'),
      qe=lambda: f'=({PT("pt_etr")}*{ECa("is_ebt")}-{ACT("is_tax")})/({ECa("is_ebt")}-{ACT("is_ebt")})', ae_in=V0['etr'],
      note='Q2–Q4/27E: rate solved so the FY27 ETR = guidance mid-point (19%; guided 18–20%). 2028E+: input (FY2025 21%, FY2026 15% with R&D credits).')
    S('is_ni', 'Net income (loss)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_ni_pub', '  Memo: net income as reported', 'memo', 'm1', data='ni', flow=True)
    S('is_ni_chk', '  Check: net income vs reported (should be 0)', 'check', 'm1', hist=lambda: chk('is_ni', 'is_ni_pub'))
    S('is_dda', '  Memo: depreciation & amortization (total)', 'memo_calc', 'm1', all=lambda: f'={V("d_da")}')
    S('is_sbc', '  Memo: equity-based compensation', 'memo_calc', 'm1', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Per share data — restated for the 5-for-4 (Jan-2008) and 2-for-1 (Oct-2008) stock splits)', 'sub', 'gen')
    S('sh_basic', '  Weighted average basic shares (m)', 'line', 'm3', data='sh_b', avg=True,
      qe=lambda: f'={B1("bs_shares")}+{ECa("bb_iss")}/3*({CTX.col.q}-1.5)', ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q2–Q4/27E: shares outstanding at 30-Jun-2026 (incl. the 600k PIPE shares, Apr-2026) + equity-plan issuance. 2028E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted average diluted shares (m)', 'line', 'm3', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q1}{R["sh_dil"]}-{Q1}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dil', 'Net income per share – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")',
      note='Net income / weighted diluted shares (±$0.01 vs reported).')
    S('eps_dil_g', '  Diluted EPS y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: diluted EPS as reported (split-adjusted) ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01, ±0.02 for split-adjusted FY2006–08)', 'check', 'ps',
      hist=lambda: (f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<='
                    f'{0.0201 if CTX.col.kind == "A" and CTX.col.year <= 2008 else 0.0101},0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")'))
    S('dps', '  Dividends declared per share ($; suspended Q4 FY2022)', 'line', 'ps', data='dps', flow=True, qe_in=0.0, ae_in=0.0)
    blank()

    # ------------------------------------------------------------------ RECON 1: NI -> EBITDA -> Adjusted EBITDA
    S('sec_r1', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (company definition, as published)', 'section',
      note='ADJUSTED EBITDA — net income + net interest + income taxes + D&A = EBITDA; + items the company excluded in each period = Adjusted EBITDA (company labels in the cell comments of the adjusting-item rows)')
    S('r_ni', 'Net income (loss)', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('r_int', '  (+) Net interest expense (income)', 'line', 'm1', all=lambda: f'={V("is_int")}')
    S('r_tax', '  (+) Income taxes', 'line', 'm1', all=lambda: f'={V("is_tax")}')
    S('r_da', '  (+) Depreciation & amortization', 'line', 'm1', all=lambda: f'={V("d_da")}')
    S('r_ebitda', '  = EBITDA', 'total', 'm1', all=lambda: f'=IF(AND(ISNUMBER({V("r_ni")}),ISNUMBER({V("r_da")})),{V("r_ni")}+{V("r_int")}+{V("r_tax")}+{V("r_da")},"")')
    S('r_ebitda_pub', '  Company-published EBITDA (FY2012–14, FY2016, FY2021 quarters)', 'memo', 'm1', data='ebitda_pub', flow=True)
    S('r_ebitda_chk', '  Check: model vs company-published EBITDA (should be 0; ±0.15 for USD m tables)', 'check', 'm1', hist=lambda: chk_np('r_ebitda', 'r_ebitda_pub', TOLM()))
    for k, lab, d in (('r_acq', '  (+) Acquisition & integration expense (income), net', 'd_acq'), ('r_restr', '  (+) Restructuring, severance & transition', 'd_restr'),
                      ('r_impair', '  (+) Impairments, bad debt, nuclear business', 'd_impair'), ('r_erp', '  (+) ERP implementation costs', 'd_erp'),
                      ('r_oth', '  (+) Other items', 'd_oadj')):
        S(k, lab, 'line', 'm1', all=lambda d=d: f'={V(d)}')
    S('r_sbc', '  (+) Equity-based compensation (added back from Q4 FY2024)', 'line', 'm1', data='eb_sbc', flow=True, fc=lambda: f'={V("d_sbc")}')
    S('r_adj', '  = Adjusted EBITDA', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{V("r_ebitda")}+{nsum(["r_acq", "r_restr", "r_impair", "r_erp", "r_oth", "r_sbc"])},"")',
      note='Company definition in force each period (definition row); = EBITDA where the company published no adjusted figure. Drives leverage, EV/EBITDA and the FY27 calibration.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_adj_pub', '  Company-published Adjusted EBITDA', 'memo', 'm1', data='adj_ebitda_pub', flow=True)
    S('r_chk', '  Check: model vs company-published Adjusted EBITDA (should be 0; ±0.15 for USD m tables)', 'check', 'm1', hist=lambda: chk_np('r_adj', 'r_adj_pub', TOLM()))
    S('r_def', '  Definition / basis (company Adjusted EBITDA definition in force)', 'text', 'gen',
      note='Definition changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('r_ebit_h', 'To adjusted EBITA and NOPAT base (for ROIC and the DCF):', 'sub', 'gen')
    S('r_ebita', '  Adjusted EBITA (Adjusted EBITDA − depreciation)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}-{V("d_dep")},"")')
    S('r_ebit', '  Adjusted EBIT, full-cost (Adjusted EBITDA − total D&A)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}-{V("d_da")},"")')
    S('r_ebita_s', '  Adjusted EBITA after equity-based compensation', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ebita")}),{V("r_ebita")}-N({V("d_sbc")}),"")')
    S('r_cash', '  Memo: cash adjusting costs excluded by the company (acquisition & integration, ERP, restructuring, other)', 'memo_calc', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_acq")}),{nsum(["r_acq", "r_erp", "r_restr", "r_oth"])},"")')
    S('r_nopb', '  NOPAT base: Adjusted EBITA − equity-based compensation − cash adjusting costs (playbook standard)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_ebita_s")}),{V("r_ebita_s")}-N({V("r_cash")}),"")',
      note='Graham\'s Adjusted EBITDA adds back SBC (from Q4 FY2024), acquisition and ERP costs; NOPAT deducts them again.')
    S('r_nopb_m', '  NOPAT base margin %', 'pct', 'pct', all=ratio('r_nopb', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: operating profit -> adjusted operating profit
    S('sec_r2', 'RECONCILIATION: OPERATING PROFIT → ADJUSTED OPERATING PROFIT (company definition published FY2018–Q3 FY2020; model elsewhere)', 'section',
      note='ADJUSTED OPERATING PROFIT — operating profit + non-recurring items (excludes equity-based compensation and amortization, as published)')
    S('o_op', 'Operating profit (loss)', 'line_b', 'm1', all=lambda: f'={V("is_op")}')
    S('o_items', '  (+) Acquisition, restructuring, impairment, ERP and other items (pre-tax; Adjusted EBITDA bridge items excl. SBC)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_acq")}),{nsum(["r_acq", "r_restr", "r_impair", "r_erp", "r_oth"])},"")')
    S('o_adj', '  = Adjusted operating profit', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+N({V("o_items")}),"")')
    S('o_adj_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company-published adjusted operating profit', 'memo', 'm1', data='adj_op_pub', flow=True)
    S('o_chk', '  Check: model vs company-published (should be 0)', 'check', 'm1', hist=lambda: chk_np('o_adj', 'o_pub'))
    S('o_def', '  Definition / basis', 'text', 'gen')
    S('o_inc', '  Incremental adjusted operating margin (Δ adjusted operating profit / Δ net sales)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted net income / EPS
    S('sec_r3', 'RECONCILIATION: NET INCOME → ADJUSTED NET INCOME → ADJUSTED EPS (company definition)', 'section',
      note='ADJUSTED NET INCOME — net income + pre-tax items (+ amortization of intangibles from FY2022) − tax at a normalized / statutory rate (23%) ± discrete tax items')
    S('e_ni', 'Net income (loss)', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('e_items', '  (+) Pre-tax items (Adjusted EBITDA bridge items excl. SBC)', 'line', 'm1', all=lambda: f'={V("o_items")}')
    S('e_amort', '  (+) Amortization of intangible assets (company definition from FY2022)', 'line', 'm1', data='an_amort', flow=True,
      fc=lambda: f'={V("d_amort")}', note='Added back from Q1 FY2022 (Barber-Nichols); not adjusted before.')
    S('e_taxd', '  (+/−) Discrete tax items (FY2018 US tax law impact)', 'line', 'm1', data='an_taxd', flow=True, fc=lambda: '=0')
    S('e_tax', '  (−) Tax effect of the adjustments (normalized rate)', 'line', 'm1', flow=True,
      hist=lambda: (f'=IF(ISNUMBER({V("e_pubni")}),{V("e_pubni")}-{V("e_ni")}-N({V("e_items")})-N({V("e_amort")})-N({V("e_taxd")}),'
                    f'IF(ISNUMBER({V("e_ni")}),-{V("e_rate")}*(N({V("e_items")})+N({V("e_amort")})),""))'),
      fc=lambda: f'=-{V("e_rate")}*({V("e_items")}+{V("e_amort")})',
      note='Historical: published adjusted net income − net income − pre-tax items (FY2015 items were shown net of tax). Unpublished periods and forecast: − statutory rate × items.')
    S('e_rate', '  Tax rate on adjustments (company: 23% statutory; 35% before FY2019 for unpublished periods)', 'pct', 'pct',
      all=lambda: (f'={0.35 if (CTX.col.year < 2019) else 0.23}'))
    S('e_adjni', '  = Adjusted net income (model bridge)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("e_tax")}),{V("e_ni")}+N({V("e_items")})+N({V("e_amort")})+N({V("e_taxd")})+{V("e_tax")},"")')
    S('e_pubni', '  Company-published adjusted net income', 'memo', 'm1', data='adj_ni_pub', flow=True)
    S('e_sh', '  Weighted average diluted shares (m)', 'line', 'm3', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted net income per diluted share ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted EPS ($)', 'eps_memo', 'ps', data='adj_eps_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0101,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_nichk', '  Check: model vs company-published adjusted net income (should be 0)', 'check', 'm1', hist=lambda: chk_np('e_adjni', 'e_pubni'))
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_def', '  Definition / basis (company adjusted net income definition)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Net sales y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_def', '  Defense sales y/y %', 'growth', 'pct', all=growth('mk_def'))
    S('gm_ord', '  Orders y/y %', 'growth', 'pct', all=growth('ob_ord'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating profit (GAAP) y/y %', 'growth', 'pct', all=growth('is_op'))
    S('gm_ni', '  Net income y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_inc', '  Incremental Adjusted EBITDA margin (Δ Adjusted EBITDA / Δ net sales)', 'pct', 'pct', all=incr('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_sga', '  SG&A incl. amortization % of net sales', 'pct', 'pct',
      all=lambda: f'=IF(ISNUMBER({V("is_sga")}),IFERROR(({V("is_sga")}+N({V("is_amort")}))/{V("is_rev")},""),"")')
    blank()

def TOLM():
    """check tolerance: FY2011-FY2012 annual reconciliations were published in USD millions (one decimal)."""
    return 0.151 if CTX.col.kind == 'A' and CTX.col.year in (2011, 2012) else 0.0015
