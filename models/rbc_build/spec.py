"""Row specification of the RBC Model sheet, part 1 (MLM template layout and process):
segment build (Aerospace & Defense / Industrial: external net sales x segment gross margin, the company's segment measure) ->
consolidated gross margin -> SG&A and other operating costs -> operating income -> M&A lever -> group total & Q2 FY27 guidance
calibration -> cost drivers -> income statement -> GAAP-to-adjusted bridges -> growth & margins."""
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
def QEa(key): return f'${Q2}${R[key]}'                    # Q2/27E (the guided quarter; absolute)
def QEc(key): return f'SUM({Q2}{R[key]}:{QE}{R[key]})'    # Q2/27E - Q4/27E (remaining quarters)
def ACT(key): return f'SUM({Q1}{R[key]}:{Q1}{R[key]})'    # Q1 FY27 actual
def ACT0(key): return f'SUM({PQ1}{R[key]}:{PQ1}{R[key]})' # Q1 FY26 actual (prior-year year to date)
def B1(key): return f'{LQ}{R[key]}'                       # 27-Jun-2026 balance
def ISQ2(): return CTX.col.c == Q2

SEG = [('aero', 'Aerospace & Defense', 'AERO', 's_aero', 'gm_aero'), ('ind', 'Industrial', 'IND', 's_ind', 'gm_ind')]
SEGK = [s for s, *_ in SEG]
OITEMS = ['d_restr', 'd_acq', 'd_stepup', 'd_legal', 'd_gain', 'd_sbci', 'd_oadj']

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of the Q2 FY27 guidance ranges.'))
    r = 11
    SCEN_ROWS.append((r, 'out_hdr', V0['out_hdr'], 'High', 'Mid', 'Low', V0['out_note'])); r += 1
    for key, lab, (hi, mid, lo), nf, note in V0['outlook']:
        SC[key] = r; SCEN_ROWS.append((r, 'out', lab, hi, mid, lo, note, nf)); r += 1
    r += 1
    SCEN_ROWS.append((r, 'pt_hdr', 'Q2–Q4 FY27E point estimates (all cases)', None, None, None, None)); r += 1
    for key, lab, vals, nf, note in V0['points']:
        SC[key] = r
        SCEN_ROWS.append((r, 'pt', lab, None, vals, None, note, nf)); r += 1
    r += 1
    SC['LEV'] = r
    SCEN_ROWS.append((r, 'lev', '  Maximum net debt / adjusted EBITDA before buybacks (x) — buyback floor FY2028E+', *V0['lev'], V0['lev_note']))
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
    # ------------------------------------------------------------------ SEGMENT BUILD
    S('sec_seg', 'SEGMENT P&L — AEROSPACE & DEFENSE · INDUSTRIAL (external net sales × segment gross margin)', 'section',
      note='SEGMENT BUILD — modelling logic (segment net sales → segment gross margin (the CODM measure) → − SG&A − other, net = operating income → GAAP P&L)')
    blank()
    descr = {'aero': 'Aerospace & Defense (bearings, precision components and systems for commercial aerospace, defense aerospace / marine / ground, missiles, space; VACCO from 18-Jul-2025)',
             'ind': 'Industrial (bearings, gearing and power-transmission components for construction, mining, food & beverage, warehousing, semicon, energy; Dodge from 1-Nov-2021)'}
    for s, title, code, dk, gk in SEG:
        S(f'{s}_hdr', descr[s], 'block', note=f'{title.upper()} — modelling logic')
        S(f'{s}_rev', f'  {title} — segment net external sales', 'line_b', 'm1', data=dk, flow=True,
          qe=lambda s=s: f'={P(s + "_rev")}*(1+{V(s + "_g")})*{V("wk")}+{V(s + "_acq")}',
          ae=lambda s=s: f'={P(s + "_rev")}*(1+{V(s + "_g")})',
          note=('Release segment data (Aerospace & Defense / Industrial from the Q3 FY22 release; FY2021 and Q3 FY21–Q2 FY22 from the re-presented comparatives). '
                'Q2–Q4/27E: prior-year quarter × (1 + organic growth) × week factor + acquired sales not in the prior-year base. FY2028E+: prior year × (1 + scenario growth).') if s == 'aero' else None)
        S(f'{s}_g', '    y/y % (Q2–Q4/27E: organic, before acquired sales)', 'growth', 'pct', all=growth(f'{s}_rev'),
          qe=lambda s=s: f'={V(s + "_pre")}+{QEa("cal_g")}',
          ae=lambda s=s, code=code: '=' + CH(SC[f'{code}_G'][CTX.col.year]),
          note='Q2–Q4/27E: Q1 FY27 organic y/y + the Q2 sales-guidance calibration Δ (solved in Q2/27E, carried into Q3–Q4). FY2028E+: scenario lever.' if s == 'aero' else None)
        S(f'{s}_pre', '    Q2–Q4/27E organic growth before calibration (Q1 FY27 organic y/y)', 'driver', 'pct',
          qe=lambda s=s: f'=IFERROR(({ACT(s + "_rev")}-{ACT(s + "_acq")})/{ACT0(s + "_rev")}-1,0)')
        S(f'{s}_acq', '    Acquired sales not in the prior-year base (VACCO / PSC Couplings; input)', 'driver', 'm1',
          data='vacco' if s == 'aero' else None, qe_in=V0[f'{s}_acq'],
          note=V0[f'{s}_acq_note'])
        S(f'{s}_mix', '  % of total net sales', 'pct', 'pct', all=ratio(f'{s}_rev', 'g_rev'))
        S(f'{s}_gm', f'  {title} segment gross margin', 'line', 'm1', data=gk, flow=True,
          qe=lambda s=s: f'={V(s + "_rev")}*{V(s + "_gmp")}', ae=lambda s=s: f'={V(s + "_rev")}*{V(s + "_gmp")}',
          note=('10-Q / 10-K segment note (segment gross margin is the CODM measure; Q4 = fiscal year − nine months). Forecast = segment sales × gross margin %.') if s == 'aero' else None)
        S(f'{s}_gmp', '  Segment gross margin %', 'pct', 'pct', all=ratio(f'{s}_gm', f'{s}_rev'),
          qe=lambda s=s: f'={V(s + "_gmp_pre")}+{QEa("cal_m")}', ae=lambda s=s, code=code: '=' + CH(SC[f'{code}_M'][CTX.col.year]),
          note='Q2–Q4/27E: margin before calibration + the Q2 gross-margin-guidance Δ (solved in Q2/27E, carried). FY2028E+: scenario lever.' if s == 'aero' else None)
        S(f'{s}_gmp_pre', '  Q2–Q4/27E margin before calibration (prior-year quarter + Q1 FY27 y/y drift)', 'driver', 'pct',
          qe=lambda s=s: f'={P(s + "_gmp")}+IFERROR({ACT(s + "_gm")}/{ACT(s + "_rev")}-{ACT0(s + "_gm")}/{ACT0(s + "_rev")},0)')
        S(f'{s}_inc', '  Incremental gross margin (Δ gross margin / Δ sales)', 'pct', 'pct', all=incr(f'{s}_gm', f'{s}_rev'))
        S(f'{s}_soi', f'  Memo: {title} segment operating income as reported (FY2022–FY2025 segment note)', 'memo', 'm1', data=f'soi_{s}', flow=True)
        blank()
    S('wk', '  Week factor (Q4/27E: 14 of 13 weeks — FY2027 is a 53-week year)', 'driver', 'x2', qe_in={2: 1.0, 3: 1.0, 4: 14 / 13},
      note=MAN['calendar']['src'] + '. The extra week falls in Q4 (Q1 had 13 weeks); applied to sales only (assumption).')
    S('seg_nb', '  Net sales not on the current segment basis (FY2006–FY2020 and Q1–Q2 FY21: total)', 'memo', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("aero_rev")}),"",{V("is_rev")})',
      note='Aerospace & Defense / Industrial were introduced after the Dodge acquisition; earlier periods were never re-presented (legacy segments below).')
    S('soi_corp', '  Memo: corporate operating loss as reported (segment note)', 'memo', 'm1', data='soi_corp', flow=True)
    S('soi_chk', '  Check: segment operating income + corporate vs operating income (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("aero_soi")}),IF(ABS({V("aero_soi")}+{V("ind_soi")}+N({V("soi_corp")})-{V("is_oi")})<=0.15,0,ROUND({V("aero_soi")}+{V("ind_soi")}+N({V("soi_corp")})-{V("is_oi")},1)),"")')
    S('leg_h', 'Legacy segments (net external sales as originally reported, FY2006–Q2 FY22):', 'sub', 'gen')
    for k, lab in (('plain', 'Plain bearings'), ('roller', 'Roller bearings'), ('ball', 'Ball bearings'), ('other', 'Other / Engineered products (renamed FY2016, Sargent)')):
        S(f'leg_{k}', f'    {lab}', 'memo', 'm1', data=f'l_{k}', flow=True)
    S('leg_chk', '    Check: legacy segments vs net sales (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("leg_plain")}),IF(ABS({nsum(["leg_plain", "leg_roller", "leg_ball", "leg_other"])}-{V("is_rev")})<=0.15,0,ROUND({nsum(["leg_plain", "leg_roller", "leg_ball", "leg_other"])}-{V("is_rev")},1)),"")')
    S('gc_aero', '  Contribution to total sales growth — Aerospace & Defense (pp)', 'growth', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("aero_rev")}),ISNUMBER({P("aero_rev")})),IFERROR(({V("aero_rev")}-{P("aero_rev")})/{P("g_rev")},""),"")' if CTX.col.prior else None))
    S('gc_ind', '  Contribution to total sales growth — Industrial (pp)', 'growth', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("ind_rev")}),ISNUMBER({P("ind_rev")})),IFERROR(({V("ind_rev")}-{P("ind_rev")})/{P("g_rev")},""),"")' if CTX.col.prior else None))
    S('gc_tot', '  Total net sales growth where the segment split is not available (pp)', 'growth', 'pct',
      all=lambda: (f'=IF(ISNUMBER({V("aero_rev")}),"",IFERROR({V("is_rev")}/{P("is_rev")}-1,""))' if CTX.col.prior and CTX.col.kind in HISTK else None))
    S('bkl', '  Memo: backlog at period end (release)', 'memo', 'm1', data='backlog', bs=True)
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — bolt-ons from FY2028E, unallocated)', 'block', note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=2.5, e26_in=0.0,
      note='VACCO $276.7m on ~$118m LTM revenue (2.3x); PSC Couplings $24.2m on ~$15.1m (1.6x); Sargent (FY2016) $500m. 2.5x input (assumption).')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.05)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}', note='Mid-year convention.')
    S('m_gmp', '  Gross margin of acquired businesses %', 'driver', 'pct', e26_in=0.0, ae_in=0.38,
      note='Assumption: below the group (~45%) before integration (VACCO and Dodge were acquired below RBC margins).')
    S('m_gm', '  Gross margin from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_gmp")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.12, note='VACCO: PP&E $40.6m of $276.7m (15%); Dodge $165.1m of $2,880.8m (6%).')
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.45,
      note='PPAs: VACCO 45% of consideration in intangibles ($123.8m), Dodge 48% ($1,385.1m).')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=15)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (M&A-related; added back in adjusted EPS)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group Total — net sales & gross margin (segment build) → Q2 FY27 guidance calibration', 'block', note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Net sales (segment build)', 'total', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("aero_rev")}),{V("aero_rev")}+{V("ind_rev")},{V("is_rev")})',
      fc=lambda: f'={V("aero_rev")}+{V("ind_rev")}+N({V("m_rev")})',
      note='Σ segment sales (+ future acquisitions from FY2028E); history before the segment split = reported net sales.')
    S('g_rev_g', '  Net sales y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs consolidated net sales (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=0.15,0,ROUND({V("g_rev")}-{V("is_rev")},1)),"")')
    S('g_gm', 'Adjusted gross margin (segment build)', 'total', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("aero_gm")}),{V("aero_gm")}+{V("ind_gm")}+{V("ga_tot")},"")',
      fc=lambda: f'={V("aero_gm")}+{V("ind_gm")}+N({V("m_gm")})',
      note='Σ segment gross margin (+ future acquisitions) + items adjusted out of cost of sales (history) = company adjusted gross margin; drives the GAAP P&L below.')
    S('g_gmp', '  Adjusted gross margin %', 'pct', 'pct', all=ratio('g_gm', 'is_rev'))
    S('g_chk_gm', '  Check: segment build vs adjusted gross margin (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_gm")}),ISNUMBER({V("is_agm")})),IF(ABS({V("g_gm")}-{V("is_agm")})<=0.15,0,ROUND({V("g_gm")}-{V("is_agm")},1)),"")')
    S('cal_sal', '  Memo: Q2 FY27 net sales guidance (scenario end-point)', 'memo', 'm1', qe=lambda: ('=' + CH(SC['out_sal'])) if ISQ2() else None, note=V0['rev_guid_note'])
    S('cal_pre', '  Net sales before calibration (Q2/27E helper)', 'line', 'm1',
      qe=lambda: ('=' + '+'.join(f'{P(s + "_rev")}*(1+{V(s + "_pre")})*{V("wk")}+{V(s + "_acq")}' for s in SEGK)) if ISQ2() else None)
    S('cal_sens', '  Net sales sensitivity to +1.00 of growth (Q2/27E helper)', 'line', 'm1',
      qe=lambda: ('=' + '+'.join(f'{P(s + "_rev")}*{V("wk")}' for s in SEGK)) if ISQ2() else None)
    S('cal_g', '  Guidance calibration: Δ y/y growth applied to both segments (solved in Q2/27E, carried to Q3–Q4/27E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_sal")}-{V("cal_pre")})/{V("cal_sens")}' if ISQ2() else f'={QEa("cal_g")}',
      note='Solves the uniform growth shift (vs Q1 FY27 organic rates) so that Q2 FY27 net sales = the guidance end-point for the active scenario; RBC guides one quarter ahead, so the same Δ is carried into Q3–Q4 (UBER precedent).')
    S('cal_rev_chk', '  Check: Q2 FY27 net sales vs guidance end-point (should be 0)', 'check', 'm1', qe=lambda: f'=ROUND({V("g_rev")}-{V("cal_sal")},1)' if ISQ2() else None)
    S('cal_gmg', '  Memo: Q2 FY27 gross margin guidance (scenario end-point, %)', 'memo', 'pct', qe=lambda: ('=' + CH(SC['out_gm'])) if ISQ2() else None, note=V0['gm_guid_note'])
    S('cal_gm_pre', '  Gross margin before calibration (Q2/27E helper)', 'line', 'm1',
      qe=lambda: ('=' + '+'.join(f'{V(s + "_rev")}*{V(s + "_gmp_pre")}' for s in SEGK)) if ISQ2() else None)
    S('cal_m', '  Guidance calibration: Δ segment gross margin (solved in Q2/27E, carried to Q3–Q4/27E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_gmg")}*{V("g_rev")}-{V("cal_gm_pre")})/({V("aero_rev")}+{V("ind_rev")})' if ISQ2() else f'={QEa("cal_m")}',
      note='Solves the uniform segment gross-margin shift so that Q2 FY27 gross margin = the guidance end-point; carried into Q3–Q4.')
    S('cal_gm_chk', '  Check: Q2 FY27 gross margin % vs guidance end-point (should be 0.0%)', 'check', 'pct', qe=lambda: f'=ROUND({V("g_gmp")}-{V("cal_gmg")},4)' if ISQ2() else None)
    S('cal_sgag', '  Memo: Q2 FY27 SG&A % of net sales guidance (scenario end-point; applied directly)', 'memo', 'pct', qe=lambda: ('=' + CH(SC['out_sga'])) if ISQ2() else None)
    S('cal_fy', '  Memo: FY2027E net sales y/y (output; RBC publishes no full-year guidance)', 'memo_calc', 'pct', e26=lambda: f'={V("g_rev")}/{P("g_rev")}-1')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A & adjusting items', 'block', note='COST DRIVERS — inputs that drive forecast cost lines (Q2–Q4/27E: guidance / point estimates; FY2028E+: % of sales or schedules)')
    S('d_sga', '  SG&A % of net sales', 'pct', 'pct', all=ratio('is_sga', 'is_rev'),
      qe=lambda: f'={V("cal_sgag")}' if ISQ2() else f'={P("d_sga")}+({Q2}{R["d_sga"]}-{QC[(FYC - 1, 2)].c}{R["d_sga"]})',
      ae=lambda: '=' + CH(SC['SGA'][CTX.col.year]),
      note='Q2/27E: guided ratio (scenario end-point). Q3–Q4/27E: prior-year quarter ratio + the Q2 guided change vs Q2 FY26. FY2028E+: scenario lever.')
    S('d_dda', '  Depreciation & amortization (total; cash-flow statement)', 'line', 'm1', data='cf_dda', flow=True,
      fc=lambda: f'={V("d_dxa")}+{V("d_amA")}', note='History: cash-flow statement (discrete quarters derived from year to date).')
    S('d_amA', '  M&A-related amortization of intangibles (adjusted EPS add-back; FY2023+ as published)', 'line', 'm1', data='ea_amort', flow=True,
      qe=lambda: f'={V("d_amT")}*{V("d_amAs")}', ae=lambda: f'={V("d_amT")}*{V("d_amAs")}+N({V("m_amort")})',
      note='Forecast: intangible-amortization schedule (10-Q) × M&A-related share + future-acquisition amortization.')
    S('d_amT', '  Amortization schedule — intangibles held at 27-Jun-2026 (10-Q, input)', 'driver', 'm1', qe_in=V0['amort_q'], ae_in=V0['amort_sched'], note=V0['amort_note'])
    S('d_amAs', '  M&A-related share of the amortization schedule %', 'driver', 'pct', qe_in=V0['amort_share'], ae_in=V0['amort_share'],
      note='Q1 FY27: M&A-related amortization $19.5m of $21.0m total amortization of intangible assets (release text); the rest is mainly software.')
    S('d_dxa', '  D&A excluding M&A-related amortization (depreciation + other amortization)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("d_amA")}),ISNUMBER({V("d_dda")})),{V("d_dda")}-{V("d_amA")},"")',
      fc=lambda: f'={V("is_rev")}*{V("d_dxa_pct")}')
    S('d_dxa_pct', '  D&A excl. M&A amortization % of net sales', 'pct', 'pct', all=ratio('d_dxa', 'is_rev'),
      qe=lambda: f'=IFERROR({ACT("d_dxa")}/{ACT("is_rev")},0)', ae_in=V0['dxa_pct'])
    S('d_sbc', '  Stock-based compensation (cash-flow statement)', 'line', 'm1', data='cf_sbc', flow=True,
      qe=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}',
      note='RBC adds stock compensation back in adjusted EPS (from Q2 FY23) and adjusted EBITDA; the DCF deducts it.')
    S('d_sbc_pct', '  Stock-based compensation % of net sales', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'),
      qe=lambda: f'=IFERROR({ACT("d_sbc")}/{ACT("is_rev")},0)', ae_in=V0['sbc_pct'])
    S('d_othx', '  Other, net excl. M&A amortization and adjusting items (other amortization, FX, other)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("is_oth")}),{V("is_oth")}-N({V("d_amA")})-({V("o_tot")}-{V("ga_tot")}),"")',
      qe=lambda: f'={PT("pt_othx")}', ae=lambda: f'={V("is_rev")}*{V("d_othx_pct")}',
      note='History before FY2023 includes all amortization of intangibles (M&A-related amortization not published separately).')
    S('d_othx_pct', '  Other, net excl. M&A amortization and items % of net sales', 'pct', 'pct', all=ratio('d_othx', 'is_rev'), ae_in=V0['othx_pct'])
    S('d_adj_h', '  Adjusting items (pre-tax, adjusted out by the company; forecast inputs):', 'sub', 'gen')
    S('d_restr', '  Restructuring & consolidation (plant moves, integration)', 'line', 'm1', data='oa_restr', flow=True, labkey='oa_restr_lab',
      qe=lambda: f'={PT("pt_restr")}', ae_in=V0['ae_restr'])
    S('d_acq', '  Transaction & related costs, transition services (acquisitions)', 'line', 'm1', data='oa_acq', flow=True, labkey='oa_acq_lab',
      qe_in={2: 0.3, 3: 0.0, 4: 0.0}, ae=lambda: f'={V("m_spend")}*{V("d_acq_pct")}', note='Q2/27E: PSC Couplings deal costs (assumption).')
    S('d_acq_pct', '  Transaction costs % of acquisition spend', 'pct', 'pct', ae_in=0.02)
    S('d_stepup', '  Inventory purchase-accounting (fair-value step-up)', 'line', 'm1', data='oa_stepup', flow=True, labkey='oa_stepup_lab', fc=lambda: '=0')
    S('d_legal', '  Litigation / legal reserves', 'line', 'm1', data='oa_legal', flow=True, labkey='oa_legal_lab', fc=lambda: '=0')
    S('d_gain', '  (Gains) / losses on disposals', 'line', 'm1', data='oa_gain', flow=True, labkey='oa_gain_lab', fc=lambda: '=0')
    S('d_sbci', '  Stock-option compensation (adjusted out of operating income FY2006–07 only)', 'line', 'm1', data='oa_sbc', flow=True, labkey='oa_sbc_lab', fc=lambda: '=0')
    S('d_oadj', '  Other items (FY2006 IPO compensation and management fees, other)', 'line', 'm1', data='oa_other', flow=True, labkey='oa_other_lab', fc=lambda: '=0')
    S('ga_tot', '  Memo: adjusting items recorded in cost of sales (adjusted gross margin reconciliation)', 'memo', 'm1', data='ga_tot', flow=True, fc=lambda: '=0')
    S('d_dff', '  Amortization of deferred finance fees (in interest; adjusted EPS add-back)', 'line', 'm1', data='ea_dff', flow=True,
      qe=lambda: f'={PT("pt_dff")}', ae_in=V0['dff'])
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF OPERATIONS (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (gross margin from the segment build; SG&A % of sales; other, net = M&A amortization + other + adjusting items)')
    S('is_rev', 'Net sales', 'total', 'm1', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the segment build.')
    S('is_cogs', 'Cost of sales', 'line', 'm1', data='cogs', flow=True, fc=lambda: f'={V("is_rev")}-{V("is_gp")}')
    S('is_gp', 'Gross margin', 'line_b', 'm1', data='gp', flow=True, fc=lambda: f'={V("g_gm")}-{V("ga_tot")}',
      note='Forecast = adjusted gross margin (segment build) − items in cost of sales.')
    S('is_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('is_agm', '  Memo: adjusted gross margin (company; = gross margin where nothing is adjusted)', 'memo', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("agm_pub")}),{V("agm_pub")},{V("is_gp")}+{V("ga_tot")})', fc=lambda: f'={V("is_gp")}+{V("ga_tot")}')
    S('agm_pub', '  Memo: company-published adjusted gross margin', 'memo', 'm1', data='adj_gm_pub', flow=True)
    S('is_sga', 'Selling, general & administrative', 'line', 'm1', data='sga', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_sga")}')
    S('is_oth', 'Other, net (amortization of intangibles, restructuring, transaction costs, other)', 'line', 'm1', data='oth', flow=True,
      fc=lambda: f'={V("d_amA")}+{V("d_othx")}+{V("o_tot")}-{V("ga_tot")}')
    S('is_oi', 'Operating income', 'total', 'm1', data='oi', flow=True, fc=lambda: f'={V("is_gp")}-{V("is_sga")}-{V("is_oth")}')
    S('is_oi_chk', '  Check: gross margin − SG&A − other, net vs operating income (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_oi")}),IF(ABS({V("is_gp")}-{V("is_sga")}-{V("is_oth")}-{V("is_oi")})<=0.15,0,ROUND({V("is_gp")}-{V("is_sga")}-{V("is_oth")}-{V("is_oi")},1)),"")')
    S('is_oim', '  Operating margin %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('is_int', 'Interest expense, net', 'line', 'm1', data='int', flow=True, qe=lambda: f'={V("pt_int_q")}',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_rev")}*{V("ds_r_rev")}+{V("ds_fees")}-{P("cf_end")}*{V("ds_r_cash")}',
      note='Q2–Q4/27E point estimates (see the row below). FY2028E+ = rate × opening notes & term debt + rate × opening revolver + fees & deferred-fee amortization − yield on opening cash (no circularity).')
    S('pt_int_q', '  Q2–Q4/27E interest expense, net (point estimates, input)', 'driver', 'm1', qe_in=V0['int_q'], note=V0['int_q_note'])
    S('is_loe', 'Loss on early extinguishment of debt (shown separately FY2006–FY2008)', 'line', 'm1', data='loe', flow=True, fc=lambda: '=0')
    S('is_onop', 'Other non-operating expense / (income)', 'line', 'm1', data='onop', flow=True, qe=lambda: f'={PT("pt_onop")}', ae_in=V0['onop'])
    S('is_ebt', 'Income before income taxes', 'line_b', 'm1', data='ebt', flow=True,
      fc=lambda: f'={V("is_oi")}-{V("is_int")}-{V("is_loe")}-{V("is_onop")}')
    S('is_ebt_chk', '  Check: operating income − interest − other vs income before taxes (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ebt")}),IF(ABS({V("is_oi")}-{V("is_int")}-{V("is_loe")}-{V("is_onop")}-{V("is_ebt")})<=0.15,0,ROUND({V("is_oi")}-{V("is_int")}-{V("is_loe")}-{V("is_onop")}-{V("is_ebt")},1)),"")')
    S('is_tax', 'Provision for income taxes', 'line', 'm1', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Q2–Q4/27E: point estimate (Q1 FY27 22.1%, 23.2% excluding discrete items). FY2028E+: input.')
    S('is_ni', 'Net income', 'total', 'm1', flow=True, all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_ni_chk', '  Check: net income vs reported (should be 0; ±0.1 rounding)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=0.15,0,ROUND({V("is_ni")}-{V("is_ni_pub")},1)),"")')
    S('is_ni_pub', '  Memo: net income as reported', 'memo', 'm1', data='ni', flow=True)
    S('is_pref', 'Preferred stock dividends (5.00% Series A MCPS, FY2022–FY2025; FY2006 Class B/C/D preferred)', 'line', 'm1', data='pref', flow=True, fc=lambda: '=0',
      note=MAN['mcps'])
    S('is_nic', 'Net income available to common stockholders', 'total', 'm1', flow=True, all=lambda: f'=IF(ISNUMBER({V("is_ni")}),{V("is_ni")}-N({V("is_pref")}),"")')
    S('is_rs_h', '  Restated per the FY2022 10-K/A (stock-based compensation timing; memo, not recast):', 'sub', 'gen')
    S('is_oi_rs', '    Operating income as restated', 'memo', 'm1', data='oi_rs', flow=True, note=MAN['restated']['src'])
    S('is_ni_rs', '    Net income as restated (fiscal years)', 'memo', 'm1', data='ni_rs', flow=True)
    S('is_nic_rs', '    Net income available to common stockholders as restated (quarters)', 'memo', 'm1', data='nic_rs', flow=True)
    S('is_dda', '  Memo: depreciation & amortization (total)', 'memo_calc', 'm1', all=lambda: f'={V("d_dda")}')
    S('is_sbc', '  Memo: stock-based compensation', 'memo_calc', 'm1', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share — RBC common stock)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={PQ("sh_basic")}+{V("bb_issq")}',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q2–Q4/27E: prior quarter + equity-plan issuance (no open-market buybacks: the $100m 2019 authorization is unused). FY2028E+: average of beginning and ending shares.')
    S('bb_issq', '  Shares issued under equity plans per quarter (m; Q2–Q4/27E input)', 'driver', 'm2', qe_in=V0['iss_q'])
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q1}{R["sh_dil"]}-{Q1}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_nic")}/{V("sh_dil")},""),"")',
      note='Net income available to common / weighted diluted shares (±$0.01 vs reported; loss quarters use basic shares as reported).')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01 rounding, ±0.03 in loss quarters)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=IF({V("eps_pub")}<0,0.03,0.0101),0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('dps', '  Dividends per common share ($)', 'line', 'ps', data='dps', flow=True, fc=lambda: '=0',
      note='No regular dividend; $2.00 special dividend in FY2015 (Dec-2014). Forecast: none (assumption; capital goes to debt reduction, M&A and buybacks).')
    blank()

    # ------------------------------------------------------------------ RECON 1: operating income -> adjusted operating income
    S('sec_r1', 'RECONCILIATION: OPERATING INCOME → ADJUSTED OPERATING INCOME (company definition, as published)', 'section',
      note='ADJUSTED OPERATING INCOME — per the release reconciliations ("Reconciliation of Reported Operating Income to Adjusted Operating Income"); company labels per period in the cell comments of the cost-driver rows')
    S('o_op', 'Operating income (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_oi")}')
    for k, lab, d in (('o_restr', '  (+) Restructuring & consolidation', 'd_restr'), ('o_acq', '  (+) Transaction & related costs, transition services', 'd_acq'),
                      ('o_stepup', '  (+) Inventory purchase accounting', 'd_stepup'), ('o_legal', '  (+) Litigation / legal reserves', 'd_legal'),
                      ('o_gain', '  (+) (Gains) / losses on disposals', 'd_gain'), ('o_sbci', '  (+) Stock-option compensation (FY2006–07)', 'd_sbci'),
                      ('o_oth', '  (+) Other items', 'd_oadj')):
        S(k, lab, 'line', 'm1', all=lambda d=d: f'={V(d)}')
    S('o_tot', '  Total adjusting items (pre-tax)', 'line_b', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("o_restr")}),{nsum(["o_restr", "o_acq", "o_stepup", "o_legal", "o_gain", "o_sbci", "o_oth"])},"")')
    S('o_adj', '  = Adjusted operating income (model bridge)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_tot")},"")',
      note='Rebuilt from the published reconciliation items; FY2012 and Q1 FY15 releases adjusted nothing (adjusted = GAAP).')
    S('o_adj_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company-published adjusted operating income', 'memo', 'm1', data='adj_oi_pub', flow=True)
    S('o_chk', '  Check: model bridge vs company-published (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),IF(ABS({V("o_adj")}-{V("o_pub")})<=0.15,0,ROUND({V("o_adj")}-{V("o_pub")},1)),"n/p")')
    S('o_agm_chk', '  Check: adjusted gross margin (gross margin + items in cost of sales) vs company-published (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("agm_pub")}),IF(ABS({V("is_gp")}+{V("ga_tot")}-{V("agm_pub")})<=0.15,0,ROUND({V("is_gp")}+{V("ga_tot")}-{V("agm_pub")},1)),"n/p")')
    S('o_def', '  Definition / basis (company adjusted definition in force)', 'text', 'gen',
      note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('o_adj_g', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental adjusted operating margin (Δ adjusted OI / Δ net sales)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: net income -> EBITDA -> adjusted EBITDA
    S('sec_r2', 'RECONCILIATION: NET INCOME → OPERATING INCOME → EBITDA → ADJUSTED EBITDA (company definitions)', 'section',
      note='ADJUSTED EBITDA — net income + interest + taxes + other non-operating = operating income; + D&A + stock compensation = EBITDA (company definition); + operating adjusting items = adjusted EBITDA')
    S('r_ni', 'Net income (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('r_tax', '  (+) Provision for income taxes', 'line', 'm1', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest expense, net', 'line', 'm1', all=lambda: f'={V("is_int")}')
    S('r_onop', '  (+) Other non-operating expense & loss on extinguishment of debt', 'line', 'm1', all=lambda: f'={V("is_onop")}+{V("is_loe")}')
    S('r_oi', '  = Operating income', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_tax")}+{V("r_int")}+{V("r_onop")},"")')
    S('r_dda', '  (+) Depreciation & amortization', 'line', 'm1', all=lambda: f'={V("d_dda")}')
    S('r_sbc', '  (+) Stock compensation expense', 'line', 'm1', all=lambda: f'={V("d_sbc")}')
    S('r_ebitda', '  = EBITDA (company definition: adds back stock compensation)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_oi")}),ISNUMBER({V("r_dda")})),{V("r_oi")}+{V("r_dda")}+{V("r_sbc")},"")')
    S('r_ebitda_pub', '  Company-published EBITDA (FY2022–Q1 FY23 reconciliations)', 'memo', 'm1', data='ebitda_pub', flow=True)
    S('r_ebitda_chk', '  Check: model vs company-published EBITDA (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda_pub")}),ISNUMBER({V("r_ebitda")})),IF(ABS({V("r_ebitda")}-{V("r_ebitda_pub")})<=0.15,0,ROUND({V("r_ebitda")}-{V("r_ebitda_pub")},1)),"n/p")')
    S('r_adjx', '  (+) Operating adjusting items (excl. stock-option compensation already added back)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("o_tot")}),{V("o_tot")}-N({V("o_sbci")}),"")')
    S('r_adj', '  = Adjusted EBITDA', 'total', 'm1', all=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda")}),ISNUMBER({V("r_adjx")})),{V("r_ebitda")}+{V("r_adjx")},"")',
      note='Equals adjusted operating income + D&A + stock compensation. Published as "adjusted operating income plus depreciation / amortization plus incentive stock compensation" from Q2 FY16 and as Adjusted EBITDA from Q3 FY22. Used for leverage and EV / EBITDA.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_adj_pub', '  Company-published adjusted EBITDA', 'memo', 'm1', data='adj_ebitda_pub', flow=True)
    S('r_chk', '  Check: model vs company-published adjusted EBITDA (should be 0; ±0.15)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("r_adj_pub")}),ISNUMBER({V("r_adj")})),IF(ABS({V("r_adj")}-{V("r_adj_pub")})<=0.15,0,ROUND({V("r_adj")}-{V("r_adj_pub")},1)),"n/p")')
    S('r_ebit_h', 'To adjusted EBITA and EBIT (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ebit', '  Adjusted EBIT, full-cost (= adjusted operating income: after all D&A and stock compensation)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}-{V("r_dda")}-{V("r_sbc")},"")')
    S('r_ebit_m', '  Adjusted EBIT (full-cost) margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_ebita', '  Adjusted EBITA (adjusted operating income + M&A-related amortization; after stock compensation)', 'line', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_ebit")}),ISNUMBER({V("d_amA")})),{V("r_ebit")}+{V("d_amA")},"")',
      note='NOPAT basis (playbook 5.7): adjusted EBIT before acquired-intangible amortization, after stock compensation; FY2023+ (M&A amortization published from then).')
    S('r_cash', '  Memo: transaction & restructuring costs (cash costs adjusted out; deducted in the DCF)', 'memo_calc', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("o_acq")}),{V("o_acq")}+{V("o_restr")},"")')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: NET INCOME → ADJUSTED NET INCOME → ADJUSTED EPS (company definition in force)', 'section',
      note='ADJUSTED EPS — net income + operating items (pre-tax) + non-operating items + (current definition, from Q2 FY23) M&A amortization, stock compensation and deferred-fee amortization − tax effect (derived) − preferred dividends')
    S('e_ni', 'Net income (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('e_op', '  (+) Operating adjusting items (pre-tax; bridge above)', 'line', 'm1', all=lambda: f'={V("o_tot")}')
    S('e_oth', '  (+) Non-operating items as published (FX translation, debt extinguishment, other; after tax before Q3 FY22)', 'line', 'm1',
      data='ea_oth', flow=True, labkey='ea_oth_lab', fc=lambda: '=0')
    S('e_amort', '  (+) M&A-related amortization (current definition)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF({V("e_defk")}="current",N({V("d_amA")}),IF(ISNUMBER({V("e_ni")}),0,""))', fc=lambda: f'={V("d_amA")}')
    S('e_sbc', '  (+) Stock compensation expense (current definition)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF({V("e_defk")}="current",{V("ea_sbc")},IF(ISNUMBER({V("e_ni")}),0,""))', fc=lambda: f'={V("d_sbc")}')
    S('ea_sbc', '  Memo: stock compensation added back (as published)', 'memo', 'm1', data='ea_sbc', flow=True)
    S('e_dff', '  (+) Amortization of deferred finance fees (current definition)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF({V("e_defk")}="current",N({V("d_dff")}),IF(ISNUMBER({V("e_ni")}),0,""))', fc=lambda: f'={V("d_dff")}')
    S('e_tax', '  (−) Tax effect of the adjustments & other tax matters (derived)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("e_pubni")}),{V("e_pubni")}-{V("e_ni")}-{V("e_op")}-N({V("e_oth")})-{V("e_amort")}-{V("e_sbc")}-{V("e_dff")},IF(ISNUMBER({V("e_ni")}),0,""))',
      fc=lambda: f'={V("e_adjni")}-{V("e_ni")}-{V("e_op")}-{V("e_oth")}-{V("e_amort")}-{V("e_sbc")}-{V("e_dff")}',
      note='Historical: published adjusted net income − net income − items (the old-definition items were published after tax, so this row also carries their tax effect). Forecast: adjusted pre-tax income × adjusted tax rate.')
    S('e_adjni', '  = Adjusted net income (model bridge)', 'total', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("e_tax")}),{V("e_ni")}+{V("e_op")}+N({V("e_oth")})+{V("e_amort")}+{V("e_sbc")}+{V("e_dff")}+{V("e_tax")},"")',
      fc=lambda: f'={V("e_adjebt")}-{V("e_adjtax")}')
    S('e_pubni', '  Company-published adjusted net income (before preferred dividends)', 'memo', 'm1', data='adj_ni_pub', flow=True)
    S('e_pref', '  (−) Preferred stock dividends', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("e_ni")}),N({V("is_pref")}),"")')
    S('e_adjnic', '  = Adjusted net income available to common stockholders', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("e_adjni")}),{V("e_adjni")}-{V("e_pref")},"")')
    S('e_sh', '  Diluted shares used for adjusted EPS (m; company count)', 'line', 'm1', data='e_sh', avg=True, fc=lambda: f'={V("sh_dil")}')
    S('e_eps', 'Adjusted EPS – diluted ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjnic', 'e_sh'))
    S('e_pub', '  Company-published adjusted EPS ($; definition in force)', 'eps_memo', 'ps', data='e_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0101,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_pub_old', '  Memo: adjusted EPS, old definition, as originally published ($; through Q1 FY23)', 'eps_memo', 'ps', data='e_pub_old')
    S('e_pub_cur', '  Memo: adjusted EPS on the current definition, incl. re-presented Q1 FY22–Q1 FY23 ($; restated GAAP base)', 'eps_memo', 'ps', data='e_pub_cur')
    S('e_adjebt', '  Adjusted income before taxes (income before taxes + all adjustments)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}+{V("e_op")}+N({V("e_oth")})+{V("e_amort")}+{V("e_sbc")}+{V("e_dff")},"")')
    S('e_adjtax', '  Adjusted income tax (adjusted income before taxes − adjusted net income)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_adjni")}),ISNUMBER({V("e_adjebt")})),{V("e_adjebt")}-{V("e_adjni")},"")',
      fc=lambda: f'={V("e_adjebt")}*{V("e_rate")}')
    S('e_rate', '  Adjusted effective tax rate', 'pct', 'pct', all=ratio('e_adjtax', 'e_adjebt'), qe=lambda: f'={PT("pt_aetr")}', ae_in=V0['aetr'],
      note='Q1 FY27: "overall tax rate applied to adjusted pre-tax earnings" 22.0% (release). Forecast input.')
    S('e_defk', '  Definition key (old / current / none)', 'text', 'gen', data='e_def', textdata=True, fc=lambda: '="current"')
    S('e_def', '  Definition / basis (company adjusted EPS definition)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Net sales y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_aero', '  Aerospace & Defense sales y/y %', 'growth', 'pct', all=growth('aero_rev'))
    S('gm_ind', '  Industrial sales y/y %', 'growth', 'pct', all=growth('ind_rev'))
    S('gm_adjop', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating income (GAAP) y/y %', 'growth', 'pct', all=growth('is_oi'))
    S('gm_ni', '  Net income y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('gm_adjop_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_inc', '  Incremental adjusted EBITDA margin (Δ adjusted EBITDA / Δ net sales; company "incremental margin")', 'pct', 'pct', all=incr('r_adj', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_sga', '  SG&A % of net sales', 'pct', 'pct', all=ratio('is_sga', 'is_rev'))
    blank()
