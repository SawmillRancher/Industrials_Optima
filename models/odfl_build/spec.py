"""Row specification of the ODFL Model sheet (MLM template layout and process), part 1:
LTL operating build, operating-ratio build & FY26 calibration, income statement, GAAP → adjusted bridges, growth & margins."""
from fw import *

SCN = '$CF$2'
def CH(r):
    return f'CHOOSE(MATCH({SCN},{{"Bull","Base","Bear"}},0),$CO${r},$CP${r},$CQ${r})'
def PT(name): return f'$CP${SC[name]}'
SC = {}

def growth(key):
    def f():
        c = CTX.col
        if c.prior is None: return None
        return f'=IF(AND(ISNUMBER({V(key)}),ISNUMBER({P(key)})),IFERROR({V(key)}/{P(key)}-1,""),"")'
    return f
def seq(key):
    def f():
        c = CTX.col
        if not c.q or c.prevq is None: return None
        return f'=IF(AND(ISNUMBER({V(key)}),ISNUMBER({PQ(key)})),IFERROR({V(key)}/{PQ(key)}-1,""),"")'
    return f
def ratio(n, d): return lambda: f'=IF(AND(ISNUMBER({V(n)}),ISNUMBER({V(d)})),IFERROR({V(n)}/{V(d)},""),"")'
def incr(n, d):
    def f():
        if CTX.col.prior is None: return None
        return f'=IFERROR(({V(n)}-{P(n)})/({V(d)}-{P(d)}),"")'
    return f
def nsum(keys): return '+'.join(f'N({V(k)})' for k in keys)
def BYv(key): return f'$BY${R[key]}'
def Q3(): return CTX.col.q == 3
def SP(a, b):   # 2026E quantity-weighted average of a per-unit row a over quantity row b (quarters BW:BZ)
    return f'=IFERROR(SUMPRODUCT(BW{R[a]}:BZ{R[a]},BW{R[b]}:BZ{R[b]})/SUM(BW{R[b]}:BZ{R[b]}),"")'

VAR = [('swb', 'Salaries, wages & benefits'), ('ops', 'Operating supplies & expenses (incl. fuel)'), ('gen', 'General supplies & expenses'),
       ('taxlic', 'Operating taxes & licenses'), ('ins', 'Insurance & claims'), ('comm', 'Communications & utilities'),
       ('pt', 'Purchased transportation')]
SEAS_YEARS = range(2016, 2026)

# ====================================================================== scenario table (CN:CR)
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). FY26 block: Q3/26E anchored to the 3-Sep-26 mid-quarter update; '
                      'Q4/26E and the Q3/Q4 operating ratio from 2016–25 seasonality (best / average / worst).'))
    r = 11
    SCEN_ROWS.append((r, 'out_hdr', V0['out_hdr'], 'Bull', 'Base', 'Bear', V0['out_note']))
    r += 1
    for key, lab, vals, nf, note in V0['outlook']:
        SC[key] = r; SCEN_ROWS.append((r, 'out', lab, *vals, note, nf)); r += 1
    r += 1
    SCEN_ROWS.append((r, 'pt_hdr', 'FY26 point estimates & Q3/26E anchors (all cases)', None, None, None, None)); r += 1
    for key, lab, vals, nf, note in V0['points']:
        SC[key] = r
        if isinstance(vals, tuple): SCEN_ROWS.append((r, 'out', lab, vals[0], vals[1], vals[2], note, nf))
        else: SCEN_ROWS.append((r, 'pt', lab, None, vals, None, note, nf))
        r += 1
    r += 1
    SC['LEV'] = r
    SCEN_ROWS.append((r, 'lev', '  Target cash balance ($m) — buyback plug 2027E+ (surplus cash returned)', *V0['lev'], V0['lev_note'])); r += 2
    for name, lab, dbull, dbear, base, note, nf, clamp in V0['blocks']:
        SCEN_ROWS.append((r, 'blk', lab, dbull, 'Δ →', dbear, note, nf)); hdr = r; r += 1
        SC[name] = {}
        for y, b in zip((2027, 2028, 2029, 2030), base):
            SC[name][y] = r; SCEN_ROWS.append((r, 'yr', f'  {y}E', hdr, b, clamp, None, nf)); r += 1
    return r

def seas(fn, key, q):
    """formula over the historical quarter-q cells of row `key`, 2016–2025 (evaluated after row numbering)."""
    return lambda: f'={fn}(' + ','.join(f'{QC[(y, q)].c}{R[key]}' for y in SEAS_YEARS) + ')'

# ====================================================================== row spec
def build_spec(V0):
    S = add
    # ------------------------------------------------------------------ LTL OPERATING BUILD
    S('sec_pl', 'LTL OPERATING BUILD — TONS PER DAY × WORK DAYS × REVENUE PER HUNDREDWEIGHT (EX-FUEL + FUEL SURCHARGE) · OTHER SERVICES · NETWORK', 'section',
      note='LTL OPERATING BUILD — modelling logic (tons/day × work days → tons; × 20 cwt × revenue/cwt → LTL revenue (statistics basis) → reported revenue → operating ratio → EPS)')
    blank()
    S('v_hdr', 'LTL volume — tonnage, shipments & weight per shipment (operating statistics as published; total tons & shipments to 2013, LTL from 2014)', 'block',
      note='VOLUME — modelling logic')
    S('l_days', '  Work days', 'line', 'm', data='st.days', flow=True, qe_in=V0['qe_days'], ae_in=V0['ae_days'],
      note='Published in the releases from 2012 (Q4) / 2013; earlier years per the ODFL calendar (weekdays less New Year, Memorial Day, July 4, Labor Day, '
           'Thanksgiving + Friday, Christmas Eve & Day — reproduces every published count 2012–26). Q3/26E 64, Q4/26E 62; 2027E–30E 252 / 253 / 253 / 253.')
    S('l_tpd', '  LTL tons per day (total tons per day to 2013)', 'line_b', 'm', data='st.tpd', avg=True,
      qe=lambda: (f'={P("l_tpd")}*(1+{PT("q3_tpd_g")})' if Q3() else f'={PQ("l_tpd")}*(1+{CH(SC["seq_tpd"])})'),
      e26=lambda: f'=IFERROR({V("l_tons")}*1000/{V("l_days")},"")',
      ae=lambda: f'={P("l_tpd")}*(1+{V("l_tpd_g")})',
      note='Q3/26E: Q3/25 × (1 + Aug-26 tons/day y/y from the 3-Sep-26 update). Q4/26E: Q3/26E × (1 + 2016–25 Q3→Q4 sequential change: best / average / worst by scenario). '
           '2027E+: prior year × (1 + scenario lever). Derived as tons ÷ work days where not published (2014–15, 2018–19).')
    S('l_tpd_g', '    y/y %', 'growth', 'pct', all=growth('l_tpd'), ae=lambda: '=' + CH(SC['TPD'][CTX.col.year]),
      note='2027E–2030E: scenario lever TPD (Bull / Base / Bear table →).')
    S('l_tpd_sq', '    sequential % (vs prior quarter)', 'growth', 'pct', all=seq('l_tpd'))
    S('l_tons', '  LTL tons (thousands; total tons to 2013)', 'line', 'm', data='st.tons', flow=True,
      fc=lambda: f'={V("l_tpd")}*{V("l_days")}/1000')
    S('l_tons_g', '    y/y %', 'growth', 'pct', all=growth('l_tons'))
    S('l_wps', '  LTL weight per shipment (lbs.)', 'line', 'm', data='st.wps', avg=True,
      qe=lambda: f'={P("l_wps")}*$BX${R["l_wps"]}/$BS${R["l_wps"]}', e26=lambda: f'=IFERROR({V("l_tons")}*2000/{V("l_ship")},"")',
      ae=lambda: f'={P("l_wps")}', note='Q3/Q4-26E: prior-year quarter × Q2/26 y/y change (+1.7%; Aug-26 +1.7%). 2027E+ flat.')
    S('l_wps_g', '    y/y %', 'growth', 'pct', all=growth('l_wps'))
    S('l_ship', '  LTL shipments (thousands; total shipments to 2013)', 'line', 'm', data='st.ship', flow=True,
      fc=lambda: f'=IFERROR({V("l_tons")}*2000/{V("l_wps")},"")')
    S('l_spd', '  LTL shipments per day', 'line', 'm', data='st.spd', avg=True, fc=lambda: f'=IFERROR({V("l_ship")}*1000/{V("l_days")},"")',
      e26=lambda: f'=IFERROR({V("l_ship")}*1000/{V("l_days")},"")')
    S('l_spd_g', '    y/y %', 'growth', 'pct', all=growth('l_spd'))
    S('l_loh', '  Average length of haul (miles)', 'memo', 'm', data='st.loh')
    S('l_miles', '  LTL intercity miles (thousands)', 'memo', 'm', data='st.miles')
    S('l_emp', '  Average active full-time employees (from 2019 releases)', 'memo', 'm', data='st.emp_avg')
    S('l_def', '  Statistics basis (definition in force)', 'text', 'gen')
    blank()

    S('y_hdr', 'Yield — LTL revenue per hundredweight (ex-fuel + fuel surcharge; statistics exclude undelivered-freight revenue adjustments)', 'block',
      note='YIELD — modelling logic')
    S('y_xf', '  LTL revenue per hundredweight, excluding fuel surcharges ($)', 'line_b', 'm2', data='st.rev_cwt_xf', avg=True,
      qe=lambda: (f'={P("y_xf")}*(1+{PT("q3_xf_g")})' if Q3() else f'={PQ("y_xf")}*(1+{CH(SC["seq_xf"])})'),
      e26=lambda: SP('y_xf', 'l_tons'), ae=lambda: f'={P("y_xf")}*(1+{V("y_xf_g")})',
      note='Q3/26E: Q3/25 × (1 + Jul–Aug quarter-to-date y/y from the 3-Sep-26 update, +4.8%). Q4/26E: Q3/26E × (1 + 2016–25 Q3→Q4 sequential change by scenario). '
           '2027E+: scenario lever YXF. 2026E = tonnage-weighted average of the quarters.')
    S('y_xf_g', '    y/y %', 'growth', 'pct', all=growth('y_xf'), ae=lambda: '=' + CH(SC['YXF'][CTX.col.year]))
    S('y_xf_sq', '    sequential % (vs prior quarter)', 'growth', 'pct', all=seq('y_xf'))
    S('y_fsc', '  Fuel surcharge per hundredweight ($)', 'line', 'm2',
      hist=lambda: f'=IF(AND(ISNUMBER({V("y_cwt")}),ISNUMBER({V("y_xf")})),{V("y_cwt")}-{V("y_xf")},"")',
      fc=lambda: f'={V("y_xf")}*{V("y_fsc_pct")}', e26=lambda: f'={V("y_cwt")}-{V("y_xf")}')
    S('y_fsc_pct', '  Fuel surcharge % of ex-fuel yield', 'pct', 'pct', hist=ratio('y_fsc', 'y_xf'),
      qe=lambda: (f'=(1+{PT("q3_cwt_g")})*{P("y_cwt")}/{V("y_xf")}-1' if Q3() else f'={PQ("y_fsc_pct")}'),
      e26=ratio('y_fsc', 'y_xf'), ae=lambda: f'=$BZ${R["y_fsc_pct"]}',
      note='Q3/26E implied by the Jul–Aug QTD revenue/cwt (+11.3% y/y) and ex-fuel (+4.8%) changes. Q4/26E and 2027E+ held at the Q3/26E level (diesel flat).')
    S('y_cwt', '  LTL revenue per hundredweight ($)', 'total', 'm2', data='st.rev_cwt', avg=True, fc=lambda: f'={V("y_xf")}+{V("y_fsc")}',
      e26=lambda: SP('y_cwt', 'l_tons'))
    S('y_cwt_g', '    y/y %', 'growth', 'pct', all=growth('y_cwt'))
    S('y_cwt_sq', '    sequential % (vs prior quarter)', 'growth', 'pct', all=seq('y_cwt'))
    S('y_shp', '  LTL revenue per shipment ($)', 'line', 'm2', data='st.rev_shp', avg=True, fc=lambda: f'={V("y_cwt")}*{V("l_wps")}/100')
    S('y_shp_xf', '  LTL revenue per shipment, excluding fuel surcharges ($)', 'line', 'm2', data='st.rev_shp_xf', avg=True,
      fc=lambda: f'={V("y_xf")}*{V("l_wps")}/100')
    blank()

    S('rv_hdr', 'Revenue build — LTL services (statistics basis × revenue-recognition adjustment) + other services', 'block',
      note='REVENUE BUILD — modelling logic')
    S('r_stat', '  LTL revenue — statistics basis (tons × 20 cwt × revenue/cwt)', 'line', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("l_tons")}),ISNUMBER({V("y_cwt")})),{V("l_tons")}*20*{V("y_cwt")}/1000,"")',
      note='Operating statistics exclude undelivered-freight adjustments (revenue recognised over transit) and non-weight-priced services.')
    S('r_rra', '  Revenue-recognition, undelivered-freight & other adjustments (reported LTL revenue − statistics basis)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("r_stat")}),IF(ISNUMBER({V("r_ltl")}),{V("r_ltl")},{V("is_rev")})-{V("r_stat")},"")',
      fc=lambda: f'={V("r_stat")}*{V("r_rra_pct")}',
      note='To 2018 (LTL / other services split not published) = total revenue − statistics basis, i.e. includes other services.')
    S('r_rra_pct', '  Adjustment % of statistics-basis revenue', 'pct', 'pct', hist=ratio('r_rra', 'r_stat'),
      qe=lambda: f'=IFERROR({H1("r_rra")}/{H1("r_stat")},"")', e26=ratio('r_rra', 'r_stat'), ae=lambda: f'=$BY${R["r_rra_pct"]}')
    S('r_ltl', '  LTL services revenue (reported; from 2019)', 'line_b', 'm', data='is.ltl_rev', flow=True,
      fc=lambda: f'={V("r_stat")}+{V("r_rra")}')
    S('r_ltl_g', '    y/y %', 'growth', 'pct', all=growth('r_ltl'))
    S('r_osv', '  Other services revenue (container drayage, truckload brokerage, supply-chain consulting)', 'line', 'm', data='is.other_rev', flow=True,
      qe=lambda: f'={P("r_osv")}*{H1("r_osv")}/{H1("r_osv", 2025)}', ae=lambda: f'={P("r_osv")}*(1+{V("r_osv_g")})',
      note='Q3/Q4-26E: prior-year quarter × 1H/26 y/y. 2027E+: growth input.')
    S('r_osv_g', '    y/y %', 'growth', 'pct', all=growth('r_osv'), ae_in=V0['oth_g'])
    S('r_rev', 'Total revenue (LTL operating build)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("r_stat")}),IF(ISNUMBER({V("r_ltl")}),{V("r_ltl")}+N({V("r_osv")}),{V("r_stat")}+{V("r_rra")}),"")',
      fc=lambda: f'={V("r_ltl")}+{V("r_osv")}', note='Σ LTL services + other services revenue (historically = statistics basis + adjustments).')
    S('r_rev_g', '  Revenue y/y %', 'growth', 'pct', all=growth('r_rev'))
    S('r_chk', '  Check: LTL operating build vs consolidated revenue (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_rev")}),ROUND({V("r_rev")}-{V("is_rev")},1),"")')
    S('r_rpd', '  Revenue per work day ($m)', 'line', 'm2', all=ratio('is_rev', 'l_days'))
    S('r_rpd_g', '    Revenue per day y/y % (mid-quarter update metric)', 'growth', 'pct', all=growth('r_rpd'))
    S('r_br', '  Δ LTL revenue (statistics basis) y/y — volume / ex-fuel yield / fuel surcharge:', 'sub', 'gen')
    S('r_dvol', '    Volume effect (Δ tons × prior-period revenue/cwt)', 'line', 'm',
      all=lambda: (f'=IF(AND(ISNUMBER({V("l_tons")}),ISNUMBER({P("l_tons")}),ISNUMBER({P("y_cwt")})),({V("l_tons")}-{P("l_tons")})*20*{P("y_cwt")}/1000,"")' if CTX.col.prior else None))
    S('r_dyld', '    Ex-fuel yield effect (Δ ex-fuel revenue/cwt × tons)', 'line', 'm',
      all=lambda: (f'=IF(AND(ISNUMBER({V("y_xf")}),ISNUMBER({P("y_xf")}),ISNUMBER({V("l_tons")})),({V("y_xf")}-{P("y_xf")})*20*{V("l_tons")}/1000,"")' if CTX.col.prior else None))
    S('r_dfsc', '    Fuel surcharge effect (Δ fuel surcharge/cwt × tons)', 'line', 'm',
      all=lambda: (f'=IF(AND(ISNUMBER({V("y_fsc")}),ISNUMBER({P("y_fsc")}),ISNUMBER({V("l_tons")})),({V("y_fsc")}-{P("y_fsc")})*20*{V("l_tons")}/1000,"")' if CTX.col.prior else None))
    S('r_dchk', '    Check: Σ effects vs Δ statistics-basis revenue (should be 0)', 'check', 'm1',
      all=lambda: (f'=IF(ISNUMBER({V("r_dvol")}),ROUND({V("r_dvol")}+{V("r_dyld")}+{V("r_dfsc")}-({V("r_stat")}-{P("r_stat")}),1),"")' if CTX.col.prior else None))
    blank()

    S('n_hdr', 'Network, capacity & productivity (10-K, year end; memo — historical only)', 'block', note='NETWORK — historical only (not forecast)')
    S('n_sc', '  Service centers (year end)', 'memo', 'm', data='extra.service_centers', annual_only=True)
    S('n_trac', '  Tractors (owned, year end)', 'memo', 'm', data='extra.tractors', annual_only=True)
    S('n_trl', '  Linehaul trailers (year end)', 'memo', 'm', data='extra.trailers_lh', annual_only=True)
    S('n_emp', '  Full-time employees (year end)', 'memo', 'm', data='extra.employees', annual_only=True)
    S('n_tpd_sc', '  LTL tons per day per service center', 'line', 'm1',
      hist=lambda: (f'=IF(ISNUMBER({V("n_sc")}),IFERROR({V("l_tpd")}/{V("n_sc")},""),"")' if not CTX.col.q else None))
    S('n_rev_emp', '  Revenue per year-end employee ($000)', 'line', 'm1',
      hist=lambda: (f'=IF(ISNUMBER({V("n_emp")}),IFERROR({V("is_rev")}/{V("n_emp")}*1000,""),"")' if not CTX.col.q else None))
    S('n_spd_emp', '  LTL shipments per day per 100 average employees (from 2019)', 'line', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("l_emp")}),IFERROR({V("l_spd")}/{V("l_emp")}*100,""),"")')
    blank()

    # ------------------------------------------------------------------ OPERATING RATIO BUILD
    S('or_hdr', 'Operating ratio build — cost lines % of revenue → operating ratio → Q3/Q4-26E calibration (seasonality) · 2027E+ OR lever', 'block',
      note='OPERATING RATIO — modelling logic (operating ratio = total operating expenses ÷ revenue; ODFL\'s primary profitability KPI)')
    for k, lab in VAR:
        S(f'c_{k}', f'  {lab} % of revenue', 'pct', 'pct', hist=ratio(f'is_{k}', 'is_rev'),
          qe=lambda k=k: f'={V("c_" + k + "_pre")}*(1+{V("or_cal")})', e26=ratio(f'is_{k}', 'is_rev'),
          ae=lambda k=k: f'=$CA${R["c_" + k]}*{V("or_scale")}')
        S(f'c_{k}_pre', '    before calibration (Q3/Q4-26E helper: prior-year quarter + 1H/26 y/y drift)', 'pct', 'pct', group=True,
          qe=lambda k=k: f'={P("c_" + k)}+({H1("is_" + k)}/{H1("is_rev")}-{H1("is_" + k, 2025)}/{H1("is_rev", 2025)})')
    S('c_dda', '  Depreciation & amortization % of revenue', 'pct', 'pct', hist=ratio('is_dda', 'is_rev'), qe=ratio('is_dda', 'is_rev'),
      e26=ratio('is_dda', 'is_rev'), ae_in=V0['dda_pct'],
      note='Q3/Q4-26E: FY26 D&A point estimate (ODFL guides D&A in the Q4 call; not on EDGAR) less 1H/26, split evenly. 2027E+ input (FY2025 6.6%; capex-led).')
    S('c_misc', '  Miscellaneous (income) expense, net % of revenue (incl. disposal gains / losses)', 'pct', 'pct', hist=ratio('is_misc', 'is_rev'),
      qe=lambda: f'=IFERROR(({H1("is_misc")}-{H1("r_gain")})/{H1("is_rev")},"")', e26=ratio('is_misc', 'is_rev'), ae=lambda: f'=$BY${R["c_misc"]}',
      note='Q3/Q4-26E and 2027E+: 1H/26 run-rate excluding net gains on disposal of property & equipment (no disposal gains forecast).')
    S('c_rents', '  Building & office equipment rents % of revenue (separate line to 2012)', 'pct', 'pct', hist=ratio('is_rents', 'is_rev'))
    S('or_pre', '  Operating ratio before calibration (Q3/Q4-26E helper)', 'pct', 'pct',
      qe=lambda: '=' + '+'.join(V(f'c_{k}_pre') for k, _ in VAR) + f'+{V("c_dda")}+{V("c_misc")}')
    S('or_tgt', '  Operating-ratio target: prior quarter + 2016–25 sequential change (scenario: best / average / worst)', 'pct', 'pct',
      qe=lambda: (f'=$BX${R["or"]}+{CH(SC["seq_or3"])}' if Q3() else f'=$BY${R["or"]}+{CH(SC["seq_or4"])}'),
      note='Q3/26E = Q2/26 operating ratio + Q2→Q3 change; Q4/26E = Q3/26E + Q3→Q4 change (min / average / max of 2016–25 by scenario). '
           'Note: the 2016–25 Q2→Q3 best case is 2020 (−332 bps, COVID rebound).')
    S('or_cal', '  Outlook calibration: proportional shift on variable cost lines (Q3/Q4-26E)', 'driver', 'pct',
      qe=lambda: f'=({V("or_tgt")}-{V("c_dda")}-{V("c_misc")})/(' + '+'.join(V(f'c_{k}_pre') for k, _ in VAR) + ')-1',
      note='Solves the uniform % change in the seven variable cost ratios (vs prior-year quarter + 1H drift) so the operating ratio equals the seasonality target.')
    S('or_lever', '  Operating ratio — scenario lever (2027E+)', 'pct', 'pct', ae=lambda: '=' + CH(SC['OR'][CTX.col.year]),
      note='Scenario lever OR (Bull / Base / Bear table →). Variable cost lines scaled pro rata to the FY26E mix; D&A and miscellaneous per their inputs.')
    S('or_scale', '  Variable cost scaling vs FY26E mix (2027E+ helper)', 'line', 'x2',
      ae=lambda: f'=({V("or_lever")}-{V("c_dda")}-{V("c_misc")})/(' + '+'.join(f'$CA${R["c_" + k]}' for k, _ in VAR) + ')')
    S('or', 'Operating ratio (total operating expenses ÷ revenue)', 'total', 'pct', all=ratio('is_opex', 'is_rev'))
    S('or_chk', '  Check: Q3/Q4-26E operating ratio vs seasonality target; 2027E+ vs scenario lever (should be 0, bps)', 'check', 'm1',
      qe=lambda: f'=ROUND(({V("or")}-{V("or_tgt")})*10000,1)', ae=lambda: f'=ROUND(({V("or")}-{V("or_lever")})*10000,1)')
    S('or_seq', '  Operating ratio change vs prior quarter (bps → %)', 'growth', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("or")}),ISNUMBER({PQ("or")})),{V("or")}-{PQ("or")},"")' if (CTX.col.q and CTX.col.prevq) else None))
    S('or_yy', '  Operating ratio change y/y', 'growth', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("or")}),ISNUMBER({P("or")})),{V("or")}-{P("or")},"")' if CTX.col.prior else None))
    S('or_pub', '  Memo: operating ratio as published', 'memo', 'pct', data='st.or_pub')
    S('cal_tpd', '  Check: Q3/26E tons per day y/y vs Aug-26 update anchor (should be 0)', 'check', 'pct',
      qe=lambda: (f'=ROUND({V("l_tpd_g")}-{PT("q3_tpd_g")},6)' if Q3() else None))
    S('cal_cwt', '  Check: Q3/26E revenue/cwt (incl. & excl. fuel) y/y vs Jul–Aug QTD update anchors (should be 0)', 'check', 'pct',
      qe=lambda: (f'=ROUND(ABS({V("y_cwt_g")}-{PT("q3_cwt_g")})+ABS({V("y_xf_g")}-{PT("q3_xf_g")}),6)' if Q3() else None))
    S('cal_rpd', '  Memo: Aug-26 revenue per day y/y (3-Sep-26 update; Q3/26E model revenue per day y/y above)', 'memo', 'pct',
      qe=lambda: (f'={PT("q3_rpd_g")}' if Q3() else None))
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'STATEMENT OF OPERATIONS (US GAAP)', 'section', note='STATEMENT OF OPERATIONS — forecast logic')
    S('is_rev', 'Revenue', 'total', 'm', data='is.revenue', flow=True, fc=lambda: f'={V("r_rev")}', note='Forecast linked to the LTL operating build.')
    for k, lab in VAR:
        S(f'is_{k}', f'{lab}', 'line', 'm', data=f'is.{k}', flow=True, fc=lambda k=k: f'={V("is_rev")}*{V("c_" + k)}')
    S('is_dda', 'Depreciation & amortization', 'line', 'm', data='is.dda', flow=True,
      qe=lambda: f'=({PT("pt_dda")}-{H1("is_dda")})/2', ae=lambda: f'={V("is_rev")}*{V("c_dda")}')
    S('is_rents', 'Building & office equipment rents (to 2012; within general supplies thereafter)', 'line', 'm', data='is.rents', flow=True,
      qe_in={3: 0.0, 4: 0.0}, ae_in=0.0)
    S('is_misc', 'Miscellaneous (income) expense, net (incl. gains / losses on disposal of property & equipment)', 'line', 'm', data='is.misc', flow=True,
      fc=lambda: f'={V("is_rev")}*{V("c_misc")}')
    S('is_opex', 'Total operating expenses', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_rev")}),' + '+'.join(f'N({V("is_" + k)})' for k, _ in VAR) + f'+N({V("is_dda")})+N({V("is_rents")})+N({V("is_misc")}),"")')
    S('is_opex_chk', '  Check: Σ expense lines vs reported total operating expenses (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_opex_pub")}),ROUND({V("is_opex")}-{V("is_opex_pub")},1),"")')
    S('is_opex_pub', '  Memo: total operating expenses as reported', 'memo', 'm', data='is.total_opex', flow=True)
    S('is_op', 'Operating income', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}-{V("is_opex")},"")')
    S('is_or', '  Operating ratio %', 'pct', 'pct', all=ratio('is_opex', 'is_rev'))
    S('is_opm', '  Operating margin %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('is_int', 'Interest expense (income), net', 'line', 'm', data='is.int_net', flow=True,
      qe=lambda: f'=({PT("pt_int")}-{H1("is_int")})/2',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_fac")}*{V("ds_r_fac")}-({P("cf_end")}+N({P("bs_sti")}))*{V("ds_r_cash")}',
      note='Interest expense less interest income (expense positive). Q3/Q4-26E: FY26 point estimate less 1H/26. 2027E+ = coupon × opening notes + rate × opening revolver − yield × opening cash & investments.')
    S('is_oth', 'Other non-operating expense (income), net', 'line', 'm', data='is.other_exp', flow=True,
      qe=lambda: f'={H1("is_oth")}/2', ae_in=V0['oth_ae'], note='Mainly life-insurance cash-surrender value / deferred-compensation investments. Q3/Q4-26E: 1H/26 run-rate.')
    S('is_ebt', 'Income before income taxes', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_op")}),{V("is_op")}-{V("is_int")}-{V("is_oth")},"")')
    S('is_tax', 'Provision for income taxes', 'line', 'm', data='is.tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Q3/Q4-26E: FY26 tax-rate point estimate (1H/26 25.0%); 2027E+ input.')
    S('is_ni', 'Net income', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")}-N({V("is_cum")}),"")')
    S('is_cum', '  Memo: cumulative effect of accounting change (2005 comparative only; nil from 2006)', 'memo', 'm', data='is.cum_eff', flow=True)
    S('is_ni_chk', '  Check: net income vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=0.0015,0,ROUND({V("is_ni")}-{V("is_ni_pub")},1)),"")')
    S('is_ni_pub', '  Memo: net income as reported', 'memo', 'm', data='is.net_income', flow=True)
    S('is_sbc', '  Memo: share-based compensation (cash-flow statement, where presented)', 'memo_calc', 'm', data='cfq.sbc', flow=True,
      fc=lambda: f'={V("is_rev")}*{V("d_sbc")}')
    S('d_sbc', '  Share-based compensation % of revenue', 'pct', 'pct', hist=ratio('is_sbc', 'is_rev'), qe_in=V0['sbc_pct'], e26=ratio('is_sbc', 'is_rev'),
      ae_in=V0['sbc_pct'])
    S('eps_hdr', '(Earnings per share — split-adjusted to the current basis: 3-for-2 Aug-2010, Sep-2012, Mar-2020; 2-for-1 Mar-2024)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='is.sh_basic', avg=True,
      qe=lambda: f'=$BX${R["sh_basic"]}-$CA${R["bb_sh"]}*{0.25 if Q3() else 0.75}',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q3/Q4-26E: Q2/26 less the 2H/26 buyback phased in (¼ in Q3, ¾ in Q4). 2027E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='is.sh_dil', avg=True,
      qe=lambda: f'={V("sh_basic")}+($BX${R["sh_dil"]}-$BX${R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_basic', 'EPS – basic ($)', 'eps', 'ps', all=ratio('is_ni', 'sh_basic'))
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=ratio('is_ni', 'sh_dil'),
      note='EPS computed as net income / weighted diluted shares (split-adjusted); may differ by ±$0.01 vs reported.')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($; split-adjusted)', 'eps_memo', 'ps', data='is.eps_dil')
    S('dps', '  Dividends declared per share ($; quarterly dividend initiated 2017)', 'line', 'ps', data='is.dps', flow=True,
      qe=lambda: f'=$BX${R["dps"]}', ae=lambda: f'={P("dps")}*(1+{V("dps_g")})',
      note='Q3/Q4-26E at the current quarterly rate ($0.29); 2027E+ grows with the DPS growth input (raised every Q1 since 2017).')
    S('dps_g', '  Dividend per share growth %', 'growth', 'pct', hist=growth('dps'), e26=growth('dps'), ae_in=V0['dps_g'])
    S('payout', '  Dividend payout (DPS / diluted EPS) %', 'pct', 'pct', all=ratio('dps', 'eps_dil'))
    blank()

    # ------------------------------------------------------------------ RECON 1: EBITDA
    S('sec_r1', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (model definition — ODFL publishes no non-GAAP measures)', 'section',
      note='ADJUSTED EBITDA — model definition: EBITDA = net income + taxes + net interest + other non-operating + D&A; Adjusted EBITDA excludes net (gains) losses on '
           'disposal of property & equipment (cash-flow statement) and one-off items named by ODFL in its releases / filings')
    S('r_ni', 'Net income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('r_tax', '  (+) Provision for income taxes', 'line', 'm', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest expense (income), net', 'line', 'm', all=lambda: f'={V("is_int")}')
    S('r_oth', '  (+) Other non-operating expense (income), net (and cumulative effect)', 'line', 'm', all=lambda: f'={V("is_oth")}+N({V("is_cum")})')
    S('r_op', '  = Operating income', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_tax")}+{V("r_int")}+{V("r_oth")},"")')
    S('r_op_chk', '  Check: operating income in the bridge vs SEC XBRL OperatingIncomeLoss (should be 0; n/p before XBRL, 2006–07)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_op_xb")}),ROUND({V("r_op")}-{V("r_op_xb")},1),"n/p")')
    S('r_op_xb', '  Memo: operating income — SEC XBRL (as originally filed)', 'memo', 'm', data='x.xb_op', flow=True)
    S('r_dda', '  (+) Depreciation & amortization', 'line', 'm', all=lambda: f'={V("is_dda")}')
    S('r_dda_chk', '  Check: D&A vs SEC XBRL DepreciationAndAmortization (should be 0; tag = cash-flow D&A, ±0.05 minor non-operating amortization)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_dda_xb")}),IF(ABS({V("r_dda")}-{V("r_dda_xb")})<=0.05,0,ROUND({V("r_dda")}-{V("r_dda_xb")},2)),"n/p")')
    S('r_dda_xb', '  Memo: D&A — SEC XBRL (cash-flow statement)', 'memo', 'm', data='x.xb_dda', flow=True)
    S('r_ebitda', '  = EBITDA', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_op")}),ISNUMBER({V("r_dda")})),{V("r_op")}+{V("r_dda")},"")')
    S('r_ebitda_m', '  EBITDA margin %', 'pct', 'pct', all=ratio('r_ebitda', 'is_rev'))
    S('r_gain', '  (+/−) Net (gain) loss on disposal of property & equipment (in miscellaneous, net)', 'line', 'm', data='x.gain', flow=True,
      qe_in={3: 0.0, 4: 0.0}, ae_in=0.0,
      note='Cash-flow statement line (gain negative). Quarters derived from year-to-date statements. Forecast nil (ODFL does not plan disposal gains).')
    S('r_gain_chk', '  Check: disposal (gain) loss vs SEC XBRL GainLossOnSaleOfPropertyPlantEquipment (absolute values; should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_gain_xb")}),ROUND(ABS({V("r_gain")})-{V("r_gain_xb")},1),"n/p")')
    S('r_gain_xb', '  Memo: disposal gain / loss — SEC XBRL (absolute; XBRL sign convention changed in 2019)', 'memo', 'm', data='x.xb_gain', flow=True)
    S('r_items', '  (+/−) Company-identified one-off items, pre-tax (customer pricing resolution 2007; TCJA special bonus Q4-17; executive agreement termination Q3-22)',
      'line', 'm', data='x.op_items', flow=True, qe_in={3: 0.0, 4: 0.0}, ae_in=0.0,
      note='Only items quantified by ODFL itself in its earnings releases / 10-Q / 10-K (source and wording in cell comments). Positive = charge added back.')
    S('r_tot', '  Total adjusting items', 'line_b', 'm', all=lambda: f'=N({V("r_gain")})+N({V("r_items")})')
    S('r_adj', '  = Adjusted EBITDA (model)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{V("r_ebitda")}+{V("r_tot")},"")')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_ni_chk', '  Check: bridge starting net income vs SEC XBRL NetIncomeLoss (should be 0; n/p before XBRL, 2006–07)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_ni_xb")}),ROUND({V("r_ni")}-{V("r_ni_xb")},1),"n/p")')
    S('r_ni_xb', '  Memo: net income — SEC XBRL (as originally filed)', 'memo', 'm', data='x.xb_ni', flow=True)
    S('r_def', '  Definition basis (model definition; no company-published Adjusted EBITDA)', 'text', 'gen',
      note='Definition notes are flagged in the column where they take effect (cell comment gives the detail).')
    S('r_ebit_h', 'To adjusted EBIT:', 'sub', 'gen')
    S('r_ddan', '  (−) Depreciation & amortization', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("r_dda")}),-{V("r_dda")},"")')
    S('r_ebit', '  = Adjusted EBIT (model; adjusted operating income)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_adj")}),ISNUMBER({V("r_ddan")})),{V("r_adj")}+{V("r_ddan")},"")',
      note='Used for NOPAT / ROIC and the DCF.')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_aor', '  Memo: adjusted operating ratio (1 − adjusted EBIT margin)', 'memo', 'pct',
      all=lambda: f'=IF(ISNUMBER({V("r_ebit_m")}),1-{V("r_ebit_m")},"")')
    blank()

    # ------------------------------------------------------------------ RECON 2: adjusted EPS
    S('sec_r2', 'RECONCILIATION: GAAP NET INCOME / DILUTED EPS → ADJUSTED NET INCOME → ADJUSTED DILUTED EPS (model definition)', 'section',
      note='ADJUSTED EPS — model definition: GAAP net income excluding the Adjusted EBITDA adjusting items (tax-effected at the effective rate excl. discrete items) '
           'and discrete tax items named by ODFL (TCJA deferred-tax revaluation, Q4-17)')
    S('e_ni', 'Net income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('e_items', '  (+/−) Adjusting items, pre-tax (as in the Adjusted EBITDA bridge)', 'line', 'm', all=lambda: f'={V("r_tot")}')
    S('e_rate', '  Tax rate applied to adjusting items (effective rate excl. discrete items)', 'pct', 'pct',
      all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),IFERROR(({V("is_tax")}-N({V("e_disc")}))/{V("is_ebt")},""),"")')
    S('e_tax', '  (−) Income tax effect of adjusting items', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("e_items")}),-{V("e_items")}*N({V("e_rate")}),"")')
    S('e_disc', '  (+/−) Discrete tax items (Tax Cuts and Jobs Act deferred-tax revaluation, Q4-17: −$104.9m benefit removed)', 'line', 'm',
      data='x.disc_tax', flow=True, qe_in={3: 0.0, 4: 0.0}, ae_in=0.0)
    S('e_adjni', '  = Adjusted net income (model)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("e_ni")}),{V("e_ni")}+N({V("e_items")})+N({V("e_tax")})+N({V("e_disc")}),"")')
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'={V("sh_dil")}')
    S('e_eps', 'Adjusted EPS – diluted ($) (model)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_ps', '  Adjusting items per diluted share, after tax ($)', 'eps_memo', 'ps',
      all=lambda: f'=IF(AND(ISNUMBER({V("e_adjni")}),ISNUMBER({V("e_sh")})),({V("e_adjni")}-{V("e_ni")})/{V("e_sh")},"")')
    S('e_pub', '  Memo: GAAP EPS – diluted as published ($; split-adjusted)', 'eps_memo', 'ps', data='is.eps_dil')
    S('e_chk', '  Check: published GAAP diluted EPS + per-share items vs model adjusted EPS (should be 0.00; ±0.01 rounding / split restatement)', 'check', 'ps',
      hist=lambda: f'=IF(ISNUMBER({V("e_pub")}),IF(ABS({V("e_pub")}+{V("e_ps")}-{V("e_eps")})<=0.0151,0,ROUND({V("e_pub")}+{V("e_ps")}-{V("e_eps")},2)),"n/p")')
    S('e_def', '  Definition basis (model definition; no company-published adjusted EPS)', 'text', 'gen')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Revenue y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_tpd', '  LTL tons per day y/y % (volume)', 'growth', 'pct', all=lambda: f'={V("l_tpd_g")}' if CTX.col.prior else None)
    S('gm_xf', '  LTL revenue/cwt ex fuel y/y % (price)', 'growth', 'pct', all=lambda: f'={V("y_xf_g")}' if CTX.col.prior else None)
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating income y/y %', 'growth', 'pct', all=growth('is_op'))
    S('gm_ni', '  Net income y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_or', '  Operating ratio %', 'pct', 'pct', all=ratio('is_opex', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_inc', '  Incremental Adjusted EBITDA margin (ΔEBITDA / ΔRevenue)', 'pct', 'pct', all=incr('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (operating income) %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_swb', '  Salaries, wages & benefits % of revenue', 'pct', 'pct', all=ratio('is_swb', 'is_rev'))
    blank()
