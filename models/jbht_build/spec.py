"""Row specification of the JBHT Model sheet, part 1 (MLM template layout and process):
segment unit-economics build (Intermodal, Dedicated, Integrated Capacity Solutions, Final Mile, Truckload: volume x revenue per
unit -> segment revenue -> operating income at the segment margin) -> M&A lever -> group total, price / volume bridge and the
company-outlook checks -> cost drivers -> income statement -> GAAP-to-adjusted bridges (model definitions) -> growth & margins."""
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
def QEa(key): return f'${QE}${R[key]}'
def QEc(key): return f'{QE}{R[key]}'
def ACT(key): return f'SUM({Q1}{R[key]}:{Q3}{R[key]})'    # 9M 2026 actual (Q1-Q3/26)
def B1(key): return f'{LQ}{R[key]}'                       # 30-Sep-2026 balance

def seq_pct(key):
    """Q3 -> Q4 sequential change (%), history in the Q4 columns; Q4/26E = seasonality by scenario."""
    def f():
        c = CTX.col
        if c.kind == 'Q' and c.q == 4 and c.prevq:
            return f'=IF(AND(ISNUMBER({V(key)}),ISNUMBER({PQ(key)})),IFERROR({V(key)}/{PQ(key)}-1,""),"")'
        return None
    return f
def seq_pp(key):
    def f():
        c = CTX.col
        if c.kind == 'Q' and c.q == 4 and c.prevq:
            return f'=IF(AND(ISNUMBER({V(key)}),ISNUMBER({PQ(key)})),{V(key)}-{PQ(key)},"")'
        return None
    return f
def seas(rowkey):
    """upper quartile / average / lower quartile of the 2016-2025 Q3->Q4 changes (Bull / Base / Bear)."""
    def f():
        rng = f'${SEAS0}{R[rowkey]}:${SEAS1}{R[rowkey]}'
        return f'=CHOOSE(MATCH({SW},{{"Bull","Base","Bear"}},0),QUARTILE({rng},3),AVERAGE({rng}),QUARTILE({rng},1))'
    return f

# key, title, code, volume label, volume data key, average (not a flow), unit label, description
SEG = [
    ('jbi', 'Intermodal (JBI)', 'JBI', 'Loads (000)', 'jbi_loads', False, 'Revenue per load ($)',
     'Intermodal (JBI) — rail intermodal: company containers, chassis and dray tractors on BNSF, Norfolk Southern and CSX rail service; revenue incl. fuel surcharge'),
    ('dcs', 'Dedicated Contract Services (DCS)', 'DCS', 'Average trucks during the period', 'dcs_trucks', True, 'Revenue per average truck ($000 per period)',
     'Dedicated Contract Services (DCS) — customer-specific fleets under multi-year contracts (includes final-mile operations to 2018; Final Mile Services reported separately from 2019)'),
    ('ics', 'Integrated Capacity Solutions (ICS)', 'ICS', 'Loads (000)', 'ics_loads', False, 'Revenue per load ($)',
     'Integrated Capacity Solutions (ICS) — non-asset freight brokerage (truckload, LTL, flatbed) through third-party carriers; separated from Truck in 2007'),
    ('fms', 'Final Mile Services (FMS)', 'FMS', 'Stops (000)', 'fms_stops', False, 'Revenue per stop ($)',
     'Final Mile Services (FMS) — home delivery and installation of big and bulky goods; reported separately from Q1-20 (2019 recast in the 2020 releases)'),
    ('jbt', 'Truckload (JBT)', 'JBT', 'Loads (000)', 'jbt_loads', False, 'Revenue per load ($)',
     'Truckload (JBT) — dry-van truckload, drop-trailer "J.B. Hunt 360box" (company trailers, third-party power); "Truck" to Q2-21'),
]
SEGK = [s[0] for s in SEG]

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). J.B. Hunt gives no revenue or earnings guidance: Q4/26E uses historical Q3→Q4 seasonality '
                      '(upper quartile / average / lower quartile of 2016–25) by scenario.'))
    r = 11
    SCEN_ROWS.append((r, 'out_hdr', V0['out_hdr'], 'High', 'Mid', 'Low', V0['out_note'])); r += 1
    for key, lab, (hi, mid, lo), nf, note in V0['outlook']:
        SC[key] = r; SCEN_ROWS.append((r, 'out', lab, hi, mid, lo, note, nf)); r += 1
    r += 1
    SCEN_ROWS.append((r, 'pt_hdr', 'Q4/26E and FY26 point estimates (all cases)', None, None, None, None)); r += 1
    for key, lab, vals, nf, note in V0['points']:
        SC[key] = r
        SCEN_ROWS.append((r, 'pt', lab, None, vals, None, note, nf)); r += 1
    r += 1
    SC['LEV'] = r
    SCEN_ROWS.append((r, 'lev', '  Target net debt / adjusted EBITDA (x) — buyback plug 2027E+', *V0['lev'], V0['lev_note']))
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
    S('sec_seg', 'SEGMENT P&L — INTERMODAL · DEDICATED · INTEGRATED CAPACITY SOLUTIONS · FINAL MILE · TRUCKLOAD (volume × revenue per unit × segment margin)', 'section',
      note='SEGMENT BUILD — modelling logic (volume × revenue per unit → segment revenue → operating income at the segment margin → consolidated operating income → GAAP P&L)')
    blank()
    for s, title, code, vlab, vkey, avg, ulab, descr in SEG:
        vol, unit, rev, oi, m = f'{s}_vol', f'{s}_unit', f'{s}_rev', f'{s}_oi', f'{s}_m'
        first = s == 'jbi'
        S(f'{s}_hdr', descr, 'block', note=f'{title.upper()} — modelling logic')
        S(vol, f'  {vlab}', 'line', 'm1' if not avg else 'm', data=vkey, **({'avg': True} if avg else {'flow': True}),
          qe=lambda vol=vol: f'={PQ(vol)}*(1+{V(vol + "_seq")})',
          e26=(lambda vol=vol: f'=AVERAGE({Q1}{R[vol]}:{QE}{R[vol]})') if avg else (lambda vol=vol: S26(vol)),
          ae=lambda vol=vol, code=code: f'={P(vol)}*(1+{CH(SC[code + "_VOL"][CTX.col.year])})',
          note=('Operating statistics by segment (earnings releases). Q4/26E: Q3/26 × (1 + historical Q3→Q4 seasonality by scenario). 2027E+: prior year × (1 + scenario lever).') if first else None)
        S(vol + '_g', '    y/y %', 'growth', 'pct', all=growth(vol))
        S(vol + '_seq', '    Q3→Q4 sequential change (history in Q4 columns; Q4/26E = seasonality by scenario)', 'driver', 'pct', hist=seq_pct(vol), qe=seas(vol + '_seq'),
          note='Q4/26E: upper quartile / average / lower quartile (Bull / Base / Bear) of the 2016–2025 Q3→Q4 changes; quartiles keep outliers (Q4-20 COVID rebound) out of the cases.' if first else None)
        S(unit, f'  {ulab}', 'line', 'm' if s != 'dcs' else 'm1',
          hist=lambda rev=rev, vol=vol: f'=IF(AND(ISNUMBER({V(rev)}),ISNUMBER({V(vol)})),IFERROR({V(rev)}*1000/{V(vol)},""),"")',
          qe=lambda unit=unit: f'={PQ(unit)}*(1+{V(unit + "_seq")})',
          e26=lambda rev=rev, vol=vol: f'=IFERROR({V(rev)}*1000/{V(vol)},"")',
          ae=lambda unit=unit, code=code: f'={P(unit)}*(1+{CH(SC[code + "_PX"][CTX.col.year])})',
          note=('Segment revenue ÷ volume (gross revenue incl. fuel surcharge, so the statistic ties exactly to reported revenue). Fuel surcharge is a pass-through: '
                'it moves revenue per unit with diesel, not real pricing.') if first else None)
        S(unit + '_g', '    y/y %', 'growth', 'pct', all=growth(unit))
        S(unit + '_seq', '    Q3→Q4 sequential change (history; Q4/26E = seasonality by scenario)', 'driver', 'pct', hist=seq_pct(unit), qe=seas(unit + '_seq'))
        S(rev, f'  {title} — segment revenue', 'line_b', 'm1', data=f'sr_{s}', flow=True,
          qe=lambda vol=vol, unit=unit: f'={V(vol)}*{V(unit)}/1000', ae=lambda vol=vol, unit=unit: f'={V(vol)}*{V(unit)}/1000',
          note='Segment revenue as reported (gross of intersegment eliminations; incl. fuel surcharge). Forecast = volume × revenue per unit.' if first else None)
        S(rev + '_g', '  Segment revenue y/y %', 'growth', 'pct', all=growth(rev))
        S(f'{s}_mix', '  % of consolidated revenue', 'pct', 'pct', all=ratio(rev, 'g_rev'))
        S(oi, f'  {title} operating income', 'line', 'm1', data=f'so_{s}', flow=True,
          qe=lambda rev=rev, m=m: f'={V(rev)}*{V(m)}', ae=lambda rev=rev, m=m: f'={V(rev)}*{V(m)}',
          note='Segment operating income as reported. Forecast = segment revenue × operating margin.' if first else None)
        S(m, '  Operating margin %', 'pct', 'pct', all=ratio(oi, rev),
          qe=lambda m=m: f'={PQ(m)}+{V(m + "_seq")}', ae=lambda code=code: '=' + CH(SC[code + '_M'][CTX.col.year]),
          note='Q4/26E: Q3/26 margin + historical Q3→Q4 change by scenario. 2027E+: scenario lever.' if first else None)
        S(m + '_seq', '    Q3→Q4 sequential change in margin (pp; history; Q4/26E = seasonality by scenario)', 'driver', 'pct2', hist=seq_pp(m), qe=seas(m + '_seq'))
        S(f'{s}_or', '  Operating ratio % (1 − margin)', 'pct', 'pct', all=lambda m=m: f'=IF(ISNUMBER({V(m)}),1-{V(m)},"")')
        S(f'{s}_inc', '  Incremental margin (Δ operating income / Δ revenue)', 'pct', 'pct', all=incr(oi, rev))
        if s == 'jbi':
            S('jbi_rpl_pub', '  Memo: revenue per load as published ($)', 'memo', 'm', data='jbi_rpl_pub', avg=True)
            S('jbi_loh', '  Memo: average length of haul (miles)', 'memo', 'm', data='jbi_loh', avg=True)
            S('jbi_trucks', '  Memo: average tractors during the period', 'memo', 'm', data='jbi_trucks', avg=True)
            S('jbi_trailing', '  Memo: trailing equipment — containers (end of period)', 'memo', 'm', data='jbi_trailing', bs=True)
            S('jbi_turns', '  Memo: loads per container per month (loads ÷ period-end trailing equipment ÷ months)', 'memo_calc', 'm2',
              hist=lambda: f'=IF(AND(ISNUMBER({V("jbi_vol")}),ISNUMBER({V("jbi_trailing")})),IFERROR({V("jbi_vol")}*1000/{V("jbi_trailing")}/{3 if CTX.col.q else 12},""),"")')
        if s == 'dcs':
            S('dcs_rptw', '  Memo: revenue per truck per week as published ($)', 'memo', 'm', data='dcs_rptw', avg=True)
            S('dcs_loads', '  Memo: loads (000)', 'memo', 'm1', data='dcs_loads', flow=True)
            S('dcs_rev_orig', '  Memo: Dedicated revenue as originally reported in 2019 (incl. final mile)', 'memo', 'm1', data='dcs_rev_orig', flow=True,
              note='2019 Dedicated as first reported, before Final Mile Services was separated (Q1-20). 2018 and earlier Dedicated figures include final-mile operations and were never recast in the releases.')
            S('dcs_oi_orig', '  Memo: Dedicated operating income as originally reported in 2019 (incl. final mile)', 'memo', 'm1', data='dcs_oi_orig', flow=True)
        if s == 'ics':
            S('ics_rpl_pub', '  Memo: revenue per load as published ($)', 'memo', 'm', data='ics_rpl_pub', avg=True)
            S('ics_gpm', '  Memo: gross profit margin % (as published)', 'memo', 'pct', data='ics_gpm', avg=True)
            S('ics_emp', '  Memo: employee count (end of period)', 'memo', 'm', data='ics_emp', bs=True)
        if s == 'fms':
            S('fms_trucks', '  Memo: average trucks during the period', 'memo', 'm', data='fms_trucks', avg=True)
            S('df_rev', '  Memo: Dedicated + Final Mile revenue (comparable across the 2019 separation)', 'memo_calc', 'm1',
              all=lambda: f'=IF(ISNUMBER({V("dcs_rev")}),{V("dcs_rev")}+N({V("fms_rev")}),"")')
            S('df_rev_g', '    y/y %', 'growth', 'pct', all=growth('df_rev'))
            S('df_oi', '  Memo: Dedicated + Final Mile operating income', 'memo_calc', 'm1',
              all=lambda: f'=IF(ISNUMBER({V("dcs_oi")}),{V("dcs_oi")}+N({V("fms_oi")}),"")')
            S('df_m', '    Operating margin %', 'pct', 'pct', all=ratio('df_oi', 'df_rev'))
        if s == 'jbt':
            S('jbt_rpl_pub', '  Memo: revenue per load as published ($; from Q2-22)', 'memo', 'm', data='jbt_rpl_pub', avg=True)
            S('jbt_loh', '  Memo: average length of haul (miles)', 'memo', 'm', data='jbt_loh', avg=True)
            S('jbt_trucks', '  Memo: average tractors during the period (published to Q4-21)', 'memo', 'm', data='jbt_trucks', avg=True)
        blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — unallocated; deals closed from 2027E; Base = none)', 'block',
      note='M&A LEVER — acquired revenue = spend ÷ EV/revenue; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / revenue (x)', 'driver', 'x2', ae_in=0.5, e26_in=0.0,
      note='Asset-light logistics / final-mile deals: BNSF Logistics brokerage (Sep-2023) ~$85m; Zenith Freight Lines (Feb-2022) ~$87m; Cory 1st Choice (Feb-2019) ~$100m. 0.5x input (assumption).')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.03)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}', note='Mid-year convention.')
    S('m_m', '  Operating margin of acquired businesses (after amortization) %', 'driver', 'pct', e26_in=0.0, ae_in=0.04)
    S('m_oi', '  Operating income from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.20)
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.40)
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=10)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (inside operating income)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)')
    blank()

    # ------------------------------------------------------------------ group total
    S('g_hdr', 'Group Total — revenue & operating income (segment build) → company-outlook checks', 'block', note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_seg', 'Total segment revenue (before intersegment eliminations)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("jbi_rev")}),{nsum([k + "_rev" for k in SEGK])},"")')
    S('g_elim', '  Intersegment eliminations', 'line', 'm1', data='sr_elim', flow=True, qe=lambda: f'=-{V("g_seg")}*{V("g_elim_p")}', ae=lambda: f'=-{V("g_seg")}*{V("g_elim_p")}')
    S('g_elim_p', '  Intersegment eliminations % of segment revenue', 'pct', 'pct2', hist=lambda: f'=IFERROR(-{V("g_elim")}/{V("g_seg")},"")',
      qe=lambda: f'={PQ("g_elim_p")}', e26=lambda: f'=IFERROR(-{V("g_elim")}/{V("g_seg")},"")', ae=lambda: f'={P("g_elim_p")}', note='Forecast held at the latest ratio.')
    S('g_rev', 'Total operating revenues (segment build)', 'total', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("g_seg")}),{V("g_seg")}+{V("g_elim")},"")', fc=lambda: f'={V("g_seg")}+{V("g_elim")}+N({V("m_rev")})',
      note='Σ segment revenue − intersegment eliminations (+ future acquisitions from 2027E).')
    S('g_rev_g', '  Revenue y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs consolidated revenue (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=0.02,0,ROUND({V("g_rev")}-{V("is_rev")},1)),"")')
    S('g_other', '  Corporate / other operating income (not allocated to segments)', 'line', 'm1', data='so_other', flow=True, fc=lambda: '=0',
      note='"Other" in the segment schedule: corporate support activity (small). Forecast nil.')
    S('g_oi', 'Operating income (segment build)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("jbi_oi")}),{nsum([k + "_oi" for k in SEGK])}+N({V("g_other")})+N({V("m_oi")}),"")',
      note='Σ segment operating income + corporate / other (+ future acquisitions). Drives the GAAP P&L below.')
    S('g_oim', '  Operating margin %', 'pct', 'pct', all=ratio('g_oi', 'g_rev'))
    S('g_oi_g', '  Operating income y/y %', 'growth', 'pct', all=growth('g_oi'))
    S('g_chk_oi', '  Check: segment build vs consolidated operating income (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_oi")}),ISNUMBER({V("is_oi")})),IF(ABS({V("g_oi")}-{V("is_oi")})<=0.02,0,ROUND({V("g_oi")}-{V("is_oi")},1)),"")')
    S('g_br_h', '  Revenue bridge (y/y, USDm):', 'sub', 'gen')
    def br(kind):
        def f():
            if CTX.col.prior is None: return None
            parts = []
            for k in SEGK:
                v, vp, u, up = V(k + '_vol'), P(k + '_vol'), V(k + '_unit'), P(k + '_unit')
                core = f'({v}-{vp})*{up}/1000' if kind == 'vol' else f'({u}-{up})*{v}/1000'
                parts.append(f'IF(AND(ISNUMBER({v}),ISNUMBER({vp}),ISNUMBER({u}),ISNUMBER({up})),{core},0)')
            return '=' + '+'.join(parts)
        return f
    S('g_bv', '    Volume effect (Δ volume × prior-period revenue per unit, Σ segments)', 'line', 'm1', all=br('vol'),
      note='Price / volume bridge: volume effect + revenue-per-unit effect + other = change in consolidated revenue. DCS volume = average trucks, so annual effects are per truck-year.')
    S('g_bp', '    Revenue-per-unit effect (Δ revenue per unit × current volume; incl. fuel surcharge and mix)', 'line', 'm1', all=br('px'))
    S('g_bo', '    Other (eliminations, acquisitions, segments without prior-period statistics)', 'line', 'm1',
      all=lambda: (f'=IF(AND(ISNUMBER({V("g_rev")}),ISNUMBER({P("g_rev")})),{V("g_rev")}-{P("g_rev")}-{V("g_bv")}-{V("g_bp")},"")' if CTX.col.prior else None))
    S('g_bchk', '    Check: bridge vs change in revenue (should be 0)', 'check', 'm1',
      all=lambda: (f'=IF(AND(ISNUMBER({V("g_rev")}),ISNUMBER({P("g_rev")})),ROUND({V("g_bv")}+{V("g_bp")}+{V("g_bo")}-({V("g_rev")}-{P("g_rev")}),1),"")' if CTX.col.prior else None))
    S('cal_h', '  Company outlook (the only forward statements J.B. Hunt files; no revenue or earnings guidance):', 'sub', 'gen')
    S('cal_etr', '  Memo: FY26 annual tax rate — company outlook (~24.0%)', 'memo', 'pct', e26=lambda: f'={PT("pt_etr")}', note=V0['etr_note'])
    S('cal_etr_chk', '  Check: FY26 effective tax rate vs company outlook (should be 0)', 'check', 'pct2', e26=lambda: f'=ROUND({V("is_etr")}-{V("cal_etr")},4)')
    S('cal_capex', '  Memo: FY26 net capital expenditures — company outlook (~$700m)', 'memo', 'm1', e26=lambda: f'={PT("pt_capex")}', note=V0['capex_note'])
    S('cal_capex_chk', '  Check: FY26 net capital expenditures vs company outlook (should be 0)', 'check', 'm1',
      e26=lambda: f'=ROUND(-({V("cf_capex")}+{V("cf_sale")})-{V("cal_capex")},1)')
    S('cal_tgt', '  Optional: FY26 diluted EPS target (blank = seasonality-driven; no company guidance)', 'memo', 'ps',
      note='Left blank: J.B. Hunt publishes no EPS guidance and none is invented. Enter a target (e.g. consensus) to see the gap in the row below; the model is not forced to it.')
    S('cal_tgt_d', '    Model FY26 diluted EPS − target (information)', 'memo_calc', 'ps', e26=lambda: f'=IF(ISNUMBER({V("cal_tgt")}),{V("eps_dil")}-{V("cal_tgt")},"n/a")')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A & company-quantified items', 'block',
      note='COST DRIVERS — expense lines as % of revenue (Q4/26E: Q3/26 ratio; 2027E+: prior-year ratio); rents and purchased transportation balances to the segment operating income')
    COST = [('sw', 'Salaries, wages and employee benefits'), ('fuel', 'Fuel and fuel taxes'), ('supplies', 'Operating supplies and expenses'),
            ('ins', 'Insurance and claims'), ('ga', 'General and administrative expenses, net of asset dispositions'),
            ('taxlic', 'Operating taxes and licenses'), ('comm', 'Communication and utilities')]
    S('d_pt', '  Rents and purchased transportation % of revenue (implied in the forecast)', 'pct', 'pct', all=ratio('is_pt', 'is_rev'),
      note='Rail, third-party carrier and dray costs: more than half of total costs and tied to load volumes; the balancing line of the forecast.')
    for k, lab in COST:
        S(f'd_{k}', f'  {lab} % of revenue', 'pct', 'pct', all=ratio(f'is_{k}', 'is_rev'), qe=lambda k=k: f'={PQ("d_" + k)}', ae=lambda k=k: f'={P("d_" + k)}')
    S('d_dda', '  Depreciation and amortization', 'line', 'm1', data='da', flow=True, qe=lambda: f'={PQ("d_dda")}', ae=lambda: f'={V("is_rev")}*{V("d_dda_p")}+N({V("m_amort")})',
      note='Q4/26E: Q3/26 amount. 2027E+: % of revenue (input) + future-acquisition amortization.')
    S('d_dda_p', '  Depreciation and amortization % of revenue', 'pct', 'pct', all=ratio('d_dda', 'is_rev'), ae_in=V0['dda_pct'], note=V0['dda_note'])
    S('d_amort', '  of which amortization of intangible assets (schedule; inside D&A)', 'line', 'm1', e26_in=V0['amort26'], ae_in=V0['amort_sched'], note=V0['amort_note'])
    S('d_sbc', '  Share-based compensation (cash-flow statement)', 'line', 'm1', data='cf_sbc', flow=True, qe=lambda: f'={PQ("d_sbc")}', ae=lambda: f'={V("is_rev")}*{V("d_sbc_p")}',
      note='Expensed in salaries, wages and employee benefits; not adjusted out.')
    S('d_sbc_p', '  Share-based compensation % of revenue', 'pct', 'pct2', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_fuel_rev', '  Fuel surcharge revenues % of revenue', 'pct', 'pct', all=ratio('is_fuel_rev', 'is_rev'), qe=lambda: f'={PQ("d_fuel_rev")}', ae_in=V0['fuel_share'],
      note=V0['fuel_note'])
    S('d_adj_h', '  Items quantified by the company in its releases (pre-tax; J.B. Hunt publishes no non-GAAP reconciliation):', 'sub', 'gen')
    S('d_items', '  Company-quantified charges / (benefits) in operating income', 'line', 'm1', data='oa_items', flow=True, labkey='oa_lab', fc=lambda: '=0',
      note=MAN['company_items']['note'])
    S('d_after', '  Memo: after-tax amount of the items where the company stated it', 'memo', 'm1', data='oa_after', flow=True)
    S('d_taxd', '  Discrete income-tax items quantified by the company ((benefit) / charge)', 'line', 'm1', data='oa_taxd', flow=True, fc=lambda: '=0',
      note='Q1-17 $13.6m tax-credit benefit (2012–16 tax years); Q4-17 $309.2m Tax Cuts and Jobs Act remeasurement of deferred taxes.')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONDENSED CONSOLIDATED STATEMENT OF EARNINGS (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (operating income from the segment build; expense lines % of revenue; rents and purchased transportation implied)')
    S('is_rev_xf', 'Operating revenues, excluding fuel surcharge revenues', 'line', 'm1', data='rev_xfuel', flow=True, fc=lambda: f'={V("is_rev")}-{V("is_fuel_rev")}')
    S('is_fuel_rev', 'Fuel surcharge revenues', 'line', 'm1', data='fuel_rev', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_fuel_rev")}')
    S('is_rev', 'Total operating revenues', 'total', 'm1', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the segment build.')
    S('is_pt', 'Rents and purchased transportation', 'line', 'm1', data='pt', flow=True,
      fc=lambda: f'={V("is_rev")}-{V("is_oi")}-' + '-'.join(V(f'is_{k}') for k, _ in COST) + f'-{V("is_da")}',
      note='Forecast = revenue − operating income − other expense lines (implied by the segment build).')
    for k, lab in COST[:2]:
        S(f'is_{k}', lab, 'line', 'm1', data=k, flow=True, fc=lambda k=k: f'={V("is_rev")}*{V("d_" + k)}')
    S('is_da', 'Depreciation and amortization', 'line', 'm1', data='da', flow=True, fc=lambda: f'={V("d_dda")}')
    for k, lab in COST[2:]:
        S(f'is_{k}', lab, 'line', 'm1', data=k, flow=True, fc=lambda k=k: f'={V("is_rev")}*{V("d_" + k)}')
    S('is_opex', 'Total operating expenses', 'line_b', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("is_pt")}),{V("is_pt")}+' + '+'.join(V(f'is_{k}') for k, _ in COST) + f'+{V("is_da")},"")')
    S('is_oi', 'Operating income', 'total', 'm1', hist=lambda: f'=IF(ISNUMBER({V("is_opex")}),{V("is_rev")}-{V("is_opex")},"")',
      fc=lambda: f'={V("g_oi")}', note='Forecast = segment build (company-quantified items nil in the forecast).')
    S('is_oi_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('is_or', '  Operating ratio %', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("is_oi_m")}),1-{V("is_oi_m")},"")')
    S('is_oi_chk', '  Check: operating income vs XBRL fact (10-Q / 10-K, as first filed; should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_oi_x")}),IF(ABS({V("is_oi")}-{V("is_oi_x")})<=0.02,0,ROUND({V("is_oi")}-{V("is_oi_x")},1)),"n/a")')
    S('is_oi_x', '  Memo: operating income per XBRL company facts (from FY2008; Q4 not tagged)', 'memo', 'm1', data='x_oi', flow=True)
    S('is_int', 'Net interest expense', 'line', 'm1', data='net_int', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'={P("ds_total")}*{V("ds_r_debt")}-{P("cf_end")}*{V("ds_r_cash")}',
      note='Q4/26E point estimate. 2027E+ = rate × opening debt − yield × opening cash (no circularity).')
    S('is_eq', 'Equity in loss / (earnings) of affiliated company (Transplace; 2006–2010)', 'line', 'm1', data='equity_loss', flow=True, fc=lambda: '=0')
    S('is_ebt', 'Earnings before income taxes', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_oi")}),{V("is_oi")}-{V("is_int")}-N({V("is_eq")}),"")')
    S('is_tax', 'Income taxes', 'line', 'm1', data='tax', flow=True,
      qe=lambda: f'={PT("pt_etr")}*({ACT("is_ebt")}+{V("is_ebt")})-{ACT("is_tax")}', ae=lambda: f'={V("is_ebt")}*{V("is_etr")}',
      note='Q4/26E: solved so that the FY26 rate equals the company outlook (~24.0%): 24% × FY26 pre-tax earnings − nine-month tax. 2027E+: rate × pre-tax earnings.')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), ae_in=V0['etr'], note='2027E+ input (FY2024 24.8%, FY2025 24.7%, FY26 outlook ~24.0%).')
    S('is_ni', 'Net earnings', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_ni_chk', '  Check: net earnings vs XBRL fact (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_x")}),IF(ABS({V("is_ni")}-{V("is_ni_x")})<=0.02,0,ROUND({V("is_ni")}-{V("is_ni_x")},1)),"n/a")')
    S('is_ni_x', '  Memo: net earnings per XBRL company facts', 'memo', 'm1', data='x_ni', flow=True)
    S('is_dda', '  Memo: depreciation and amortization', 'memo_calc', 'm1', all=lambda: f'={V("d_dda")}')
    S('is_sbc', '  Memo: share-based compensation', 'memo_calc', 'm1', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share — J.B. Hunt common stock; no stock split since May-2005)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={B1("bs_shares")}-${E26}${R["bb_sh"]}*0.5+${E26}${R["bb_iss"]}*0.5',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q4/26E: shares outstanding at 30-Sep-2026 − Q4 buybacks (mid-quarter) + issuance. 2027E+: average of beginning and ending shares. History: XBRL (Q4 = 4 × FY − Σ Q1–Q3).')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")',
      note='Net earnings / weighted diluted shares (±$0.01 vs reported).')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0101,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('dps', '  Cash dividends per share ($)', 'line', 'ps', data='dps', flow=True, qe_in=V0['dps_q'],
      ae=lambda: f'={P("dps")}*(1+{V("dps_g")})', note='Quarterly dividend $0.45 in 2026. 2027E+: prior year × (1 + growth). Q1-13: nil (dividend accelerated into Dec-2012).')
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'])
    blank()

    # ------------------------------------------------------------------ RECON 1
    S('sec_r1', 'RECONCILIATION: OPERATING INCOME → ADJUSTED OPERATING INCOME (model definition — J.B. Hunt publishes no non-GAAP measures)', 'section',
      note='ADJUSTED OPERATING INCOME — model definition: operating income + only the charges / benefits the company itself quantified in its earnings releases (cell comments quote them)')
    S('o_op', 'Operating income (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_oi")}')
    S('o_tot', '  (+) Company-quantified charges / (benefits) (pre-tax)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_op")}),N({V("d_items")}),"")')
    S('o_adj', '  = Adjusted operating income (model definition)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_tot")},"")',
      note='Not a company measure. Forecast: no items, so adjusted = GAAP operating income.')
    S('o_adj_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company-published adjusted operating income', 'text', 'gen', textrow='n/p — J.B. Hunt reports U.S. GAAP results only')
    S('o_def', '  Definition / basis (items the company quantified, by period)', 'text', 'gen',
      note='Flags mark the periods with company-quantified items (cell comments give the wording).')
    S('o_adj_g', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental adjusted operating margin (Δ adjusted operating income / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2
    S('sec_r2', 'RECONCILIATION: NET EARNINGS → EBITDA → ADJUSTED EBITDA (model definitions)', 'section',
      note='EBITDA — model definition: net earnings + income taxes + net interest expense + equity in affiliate + depreciation and amortization; adjusted EBITDA adds the company-quantified items')
    S('r_ni', 'Net earnings (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('r_tax', '  (+) Income taxes', 'line', 'm1', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Net interest expense', 'line', 'm1', all=lambda: f'={V("is_int")}')
    S('r_eq', '  (+) Equity in loss / (earnings) of affiliated company', 'line', 'm1', all=lambda: f'=N({V("is_eq")})')
    S('r_dda', '  (+) Depreciation and amortization', 'line', 'm1', all=lambda: f'={V("d_dda")}')
    S('r_ebitda', '  = EBITDA (model definition)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_ni")}),ISNUMBER({V("r_dda")})),{V("r_ni")}+{V("r_tax")}+{V("r_int")}+{V("r_eq")}+{V("r_dda")},"")')
    S('r_chk0', '  Check: EBITDA = operating income + D&A (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),IF(ABS({V("r_ebitda")}-{V("is_oi")}-{V("d_dda")})<=0.02,0,ROUND({V("r_ebitda")}-{V("is_oi")}-{V("d_dda")},1)),"")')
    S('r_adjx', '  (+) Company-quantified charges / (benefits)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_tot")}),{V("o_tot")},"")')
    S('r_adj', '  = Adjusted EBITDA (model definition)', 'total', 'm1', all=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda")}),ISNUMBER({V("r_adjx")})),{V("r_ebitda")}+{V("r_adjx")},"")',
      note='Model measure (the company publishes no EBITDA). Share-based compensation is not added back. Used for leverage (net debt / adjusted EBITDA) and EV / EBITDA.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_adj_pub', '  Company-published EBITDA / adjusted EBITDA', 'text', 'gen', textrow='n/p — not published by the company')
    S('r_ebit_h', 'To adjusted EBIT, full-cost (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ddan', '  (−) Depreciation and amortization (total)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("d_dda")}),-{V("d_dda")},"")')
    S('r_ebit', '  = Adjusted EBIT, full-cost (adjusted EBITDA − total D&A = adjusted operating income)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+{V("r_ddan")},"")',
      note='After all depreciation, intangible amortization (~$20m p.a.) and share-based compensation.')
    S('r_ebit_m', '  Adjusted EBIT (full-cost) margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: cash costs adjusted out (company-quantified items; nil in the forecast; deducted in the DCF)', 'memo_calc', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("o_tot")}),{V("o_tot")},"")')
    blank()

    # ------------------------------------------------------------------ RECON 3
    S('sec_r3', 'RECONCILIATION: NET EARNINGS / DILUTED EPS → ADJUSTED NET EARNINGS → ADJUSTED EPS (model definition)', 'section',
      note='ADJUSTED EPS — model definition: net earnings + company-quantified pre-tax items − tax effect + company-quantified discrete tax items')
    S('e_ni', 'Net earnings (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('e_op', '  (+) Company-quantified charges / (benefits) (pre-tax; bridge above)', 'line', 'm1', all=lambda: f'={V("o_tot")}')
    S('e_tax', '  (−) Tax effect of the items', 'line', 'm1', flow=True,
      hist=lambda: (SUMQ('e_tax') if (CTX.col.kind == 'A' and CTX.col.year >= FYQ0) else
                    f'=IF(ISNUMBER({V("e_op")}),IF(ISNUMBER({V("d_after")}),{V("d_after")}-{V("e_op")},-{V("e_op")}*MIN(0.4,MAX(0.15,N({V("is_etr")})))),"")'),
      fc=lambda: f'=-{V("e_op")}*{V("is_etr")}',
      note='After-tax amount as stated by the company where given (Q4-16, Q3-18); otherwise the period effective tax rate bounded to 15–40% (assumption; FY columns of quarterly years = Σ quarters).')
    S('e_taxd', '  (+) Discrete tax items quantified by the company', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("e_ni")}),N({V("d_taxd")}),"")')
    S('e_adjni', '  = Adjusted net earnings (model definition)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("e_tax")}),{V("e_ni")}+{V("e_op")}+{V("e_tax")}+{V("e_taxd")},"")')
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted EPS – diluted ($) (model definition)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted EPS', 'text', 'gen', textrow='n/p — the company reports GAAP EPS only (per-share effects of items are quoted in the release text)')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_def', '  Definition / basis (adjusted EPS, model definition)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Revenue y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_xf', '  Revenue excluding fuel surcharge y/y %', 'growth', 'pct', all=growth('is_rev_xf'))
    S('gm_jbi', '  Intermodal loads y/y %', 'growth', 'pct', all=growth('jbi_vol'))
    S('gm_jbi_px', '  Intermodal revenue per load y/y %', 'growth', 'pct', all=growth('jbi_unit'))
    S('gm_adjop', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating income (GAAP) y/y %', 'growth', 'pct', all=growth('is_oi'))
    S('gm_ni', '  Net earnings y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_adjop_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_inc', '  Incremental adjusted operating margin (Δ adjusted operating income / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('gm_or', '  Operating ratio % (GAAP)', 'pct', 'pct', all=lambda: f'={V("is_or")}')
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_pt', '  Rents and purchased transportation % of revenue', 'pct', 'pct', all=ratio('is_pt', 'is_rev'))
    S('gm_sw', '  Salaries, wages and employee benefits % of revenue', 'pct', 'pct', all=ratio('is_sw', 'is_rev'))
    blank()
