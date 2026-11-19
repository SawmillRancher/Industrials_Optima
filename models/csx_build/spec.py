"""Row specification of the CSX Model sheet, part 1 (MLM template layout and process):
operating build by market (volume x revenue per unit for the seven merchandise markets, intermodal and coal; trucking and other
revenue) -> cost build by expense line (labor, purchased services, fuel = gallons x price, D&A, rents) -> operating ratio ->
Q4/26E calibration -> income statement -> GAAP-to-adjusted bridges -> growth & margins."""
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
def QEa(key): return f'${QE}${R[key]}'                    # Q4/26E (absolute)
def QEc(key): return f'{QE}{R[key]}'                      # Q4/26E
def ACT(key): return f'SUM({Q1}{R[key]}:{Q3}{R[key]})'    # 9M-26 actual (Q1-Q3/26)
def ACT0(key): return f'SUM({PQ1}{R[key]}:{PQ3}{R[key]})' # 9M-25 actual (Q1-Q3/25)
def B1(key): return f'{LQ}{R[key]}'                       # 30-Sep-2026 balance
def YY(key): return f'IFERROR({ACT(key)}/{ACT0(key)}-1,0)'   # 9M-26 y/y growth

MERCH = [('chem', 'Chemicals'), ('agfood', 'Agricultural and food products'), ('minerals', 'Minerals'), ('auto', 'Automotive'),
         ('metals', 'Metals and equipment'), ('forest', 'Forest products'), ('fert', 'Fertilizers')]
MK = [k for k, _ in MERCH]
GROUPS = MK + ['intermodal', 'coal']                      # markets with volume x revenue per unit
LEGACY = [('ag', 'Agricultural products'), ('phos', 'Phosphates and fertilizers'), ('food', 'Food and consumer'), ('chem', 'Chemicals'),
          ('auto', 'Automotive'), ('metals', 'Metals'), ('emerging', 'Emerging markets'), ('forest', 'Forest products'),
          ('minerals', 'Minerals (Q1/13 – Q2/16)'), ('waste', 'Waste and equipment (Q1/13 – Q2/16)'), ('coal', 'Coal'),
          ('coke', 'Coke and iron ore (to Q1/10)'), ('intl', 'Intermodal — international (to Q1/10)'), ('dom', 'Intermodal — domestic (to Q1/10)'),
          ('intermodal', 'Intermodal (from Q2/10)'), ('railother', 'Other — rail (to Q1/10)'), ('imother', 'Other — intermodal (to Q1/10)'),
          ('other', 'Other (from Q2/10)')]

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of the (unverified) 2026 outlook; clear a cell to switch that calibration off.'))
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
    SCEN_ROWS.append((r, 'lev', '  Maximum net debt / adjusted EBITDA before buybacks (x) — buyback plug 2027E+', *V0['lev'], V0['lev_note']))
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
    S('sec_ops', 'OPERATING BUILD — VOLUME × REVENUE PER UNIT BY MARKET (merchandise · intermodal · coal) · TRUCKING · OTHER', 'section',
      note='OPERATING BUILD — modelling logic (units × revenue per unit = revenue by market → Σ = total revenue → cost lines → operating ratio → GAAP P&L)')
    blank()
    S('mk_hdr', 'Merchandise markets — current basis (Q3/16 release onward; Q3/15 – Q2/16 and FY2015 from the recast comparatives; earlier periods in the legacy memo block)', 'block',
      note='MERCHANDISE — seven markets: volume (thousands of units) × revenue per unit ($) = revenue. Q4/26E: prior-year quarter × (1 + 9M-26 y/y) + calibration Δ. 2027E+: scenario levers (merchandise volume growth + per-market offset; merchandise revenue-per-unit growth).')
    for k, lab in MERCH:
        S(f'{k}_vol', f'  {lab} — volume (thousands of units)', 'line', 'm', data=f'm_{k}_vol', flow=True,
          qe=lambda k=k: f'={P(k + "_vol")}*(1+{V(k + "_vol_g")})', ae=lambda k=k: f'={P(k + "_vol")}*(1+{V(k + "_vol_g")})')
        S(f'{k}_vol_g', '    volume y/y %', 'growth', 'pct', all=growth(f'{k}_vol'),
          qe=lambda k=k: f'={YY(k + "_vol")}+{QEa("cal_v")}', ae=lambda k=k: f'={CH(SC["MERCH_VOL"][CTX.col.year])}+{V(k + "_vol_off")}',
          note='Q4/26E: 9M-26 y/y + volume calibration Δ (Group block; 0 unless a volume target is entered). 2027E+: merchandise volume lever + per-market offset (row below).' if k == 'chem' else None)
        S(f'{k}_vol_off', '    2027E+ volume growth offset vs merchandise lever (pp, input)', 'driver', 'pct', ae_in=V0['vol_off'][k],
          note=V0['vol_off_note'][k])
        S(f'{k}_rpu', f'  {lab} — revenue per unit ($)', 'line', 'm', data=f'm_{k}_rpu', avg=True,
          qe=lambda k=k: f'={P(k + "_rpu")}*(1+{V(k + "_rpu_g")})', ae=lambda k=k: f'={P(k + "_rpu")}*(1+{V(k + "_rpu_g")})',
          e26=lambda k=k: f'=IFERROR({V(k + "_rev")}/{V(k + "_vol")}*1000,"")')
        S(f'{k}_rpu_g', '    revenue per unit y/y % (price, mix, fuel surcharge)', 'growth', 'pct', all=growth(f'{k}_rpu'),
          qe=lambda k=k: f'={YY(k + "_rpu")}+{QEa("cal_p")}', ae=lambda k=k: '=' + CH(SC['MERCH_RPU'][CTX.col.year]),
          note='Q4/26E: 9M-26 y/y + revenue calibration Δ (Group block). 2027E+: merchandise revenue-per-unit lever (all-in: core price, mix and fuel surcharge).' if k == 'chem' else None)
        S(f'{k}_rev', f'  {lab} — revenue', 'line_b', 'm', data=f'm_{k}_rev', flow=True,
          qe=lambda k=k: f'={V(k + "_vol")}*{V(k + "_rpu")}/1000', ae=lambda k=k: f'={V(k + "_vol")}*{V(k + "_rpu")}/1000',
          note='Forecast = volume × revenue per unit ÷ 1,000. History as published (volume × RPU reproduces it within rounding).' if k == 'chem' else None)
    S('merch_vol', 'Merchandise volume (thousands of units)', 'total', 'm', data='a_merch_vol', flow=True, fc=lambda: '=' + '+'.join(V(k + '_vol') for k in MK),
      note='History: published Total Merchandise (2006 – Q1/10: merchandise + automotive, which was then shown separately). Forecast: Σ seven markets.')
    S('merch_vol_g', '  Merchandise volume y/y %', 'growth', 'pct', all=growth('merch_vol'))
    S('merch_rev', 'Merchandise revenue', 'total', 'm', data='a_merch_rev', flow=True, fc=lambda: '=' + '+'.join(V(k + '_rev') for k in MK),
      note='History: published Total Merchandise revenue (2006 – Q1/10 incl. automotive). Forecast: Σ seven markets.')
    S('merch_rev_g', '  Merchandise revenue y/y %', 'growth', 'pct', all=growth('merch_rev'))
    S('merch_rpu', '  Merchandise revenue per unit ($)', 'line', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("merch_rev")}),ISNUMBER({V("merch_vol")})),IFERROR({V("merch_rev")}/{V("merch_vol")}*1000,""),"")')
    S('merch_rpu_g', '  Merchandise revenue per unit y/y %', 'growth', 'pct', all=growth('merch_rpu'))
    S('merch_chk', '  Check: Σ seven markets vs published Total Merchandise revenue (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("chem_rev")}),IF(ABS({"+".join(V(k + "_rev") for k in MK)}-{V("merch_rev")})<=1.01,0,ROUND({"+".join(V(k + "_rev") for k in MK)}-{V("merch_rev")},0)),"")')
    S('merch_chkv', '  Check: Σ seven markets vs published Total Merchandise volume (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("chem_vol")}),IF(ABS({"+".join(V(k + "_vol") for k in MK)}-{V("merch_vol")})<=1.01,0,ROUND({"+".join(V(k + "_vol") for k in MK)}-{V("merch_vol")},0)),"")')
    S('merch_def', '  Market basis in force (definition flag)', 'text', 'gen', note='Red flags mark the column where the market taxonomy changed (cell comments quote the release).')
    blank()
    for g, title, descr in (('intermodal', 'Intermodal', 'Intermodal (domestic and international containers and trailers; volume in units)'),
                            ('coal', 'Coal', 'Coal (domestic utility and industrial, export metallurgical and thermal; volume in carloads; 2006 – Q1/10 "Total Coal" incl. coke and iron ore)')):
        S(f'{g}_hdr', descr, 'block', note=f'{title.upper()} — volume × revenue per unit; Q4/26E = prior-year quarter × (1 + 9M-26 y/y) + calibration Δ; 2027E+ scenario levers')
        S(f'{g}_vol', f'  {title} volume (thousands of units)', 'line', 'm', data=f'a_{g}_vol', flow=True,
          qe=lambda g=g: f'={P(g + "_vol")}*(1+{V(g + "_vol_g")})', ae=lambda g=g: f'={P(g + "_vol")}*(1+{V(g + "_vol_g")})')
        S(f'{g}_vol_g', '    volume y/y %', 'growth', 'pct', all=growth(f'{g}_vol'),
          qe=lambda g=g: f'={YY(g + "_vol")}+{QEa("cal_v")}', ae=lambda g=g: '=' + CH(SC['IM_VOL' if g == 'intermodal' else 'COAL_VOL'][CTX.col.year]))
        S(f'{g}_rpu', f'  {title} revenue per unit ($)', 'line', 'm', data=f'a_{g}_rpu', avg=True,
          qe=lambda g=g: f'={P(g + "_rpu")}*(1+{V(g + "_rpu_g")})', ae=lambda g=g: f'={P(g + "_rpu")}*(1+{V(g + "_rpu_g")})',
          e26=lambda g=g: f'=IFERROR({V(g + "_rev")}/{V(g + "_vol")}*1000,"")')
        S(f'{g}_rpu_g', '    revenue per unit y/y %', 'growth', 'pct', all=growth(f'{g}_rpu'),
          qe=lambda g=g: f'={YY(g + "_rpu")}+{QEa("cal_p")}', ae=lambda g=g: '=' + CH(SC['IM_RPU' if g == 'intermodal' else 'COAL_RPU'][CTX.col.year]))
        S(f'{g}_rev', f'{title} revenue', 'total', 'm', data=f'a_{g}_rev', flow=True,
          qe=lambda g=g: f'={V(g + "_vol")}*{V(g + "_rpu")}/1000', ae=lambda g=g: f'={V(g + "_vol")}*{V(g + "_rpu")}/1000')
        S(f'{g}_rev_g', f'  {title} revenue y/y %', 'growth', 'pct', all=growth(f'{g}_rev'))
        if g == 'coal':
            S('coal_tons', '  Memo: coal tonnage (millions of tons; published from 2014)', 'memo', 'm1', data='coal_tons', flow=True)
            S('coal_dom', '    of which domestic', 'memo', 'm1', data='coal_dom', flow=True)
            S('coal_exp', '    of which export', 'memo', 'm1', data='coal_exp', flow=True)
            S('coal_rpt', '  Memo: coal revenue per ton ($)', 'memo_calc', 'm', all=lambda: f'=IF(ISNUMBER({V("coal_tons")}),IFERROR({V("coal_rev")}/{V("coal_tons")},""),"")')
        blank()
    S('tr_hdr', 'Trucking (Quality Carriers, acquired 1-Jul-2021) and other revenue', 'block',
      note='TRUCKING — revenue growth lever (no units published). OTHER — intermodal storage, equipment usage, demurrage, switching; grows with rail revenue.')
    S('truck_rev', 'Trucking revenue (from Q3/21)', 'total', 'm', data='a_trucking_rev', flow=True,
      qe=lambda: f'={P("truck_rev")}*(1+{V("truck_g")})', ae=lambda: f'={P("truck_rev")}*(1+{V("truck_g")})')
    S('truck_g', '  Trucking revenue y/y %', 'growth', 'pct', all=growth('truck_rev'), qe=lambda: f'={YY("truck_rev")}', ae=lambda: '=' + CH(SC['TRUCK'][CTX.col.year]),
      note='Q4/26E: 9M-26 y/y (+5.6%, mostly fuel surcharge). 2027E+: scenario lever.')
    S('other_rev', 'Other revenue', 'total', 'm', data='a_other_rev', flow=True,
      qe=lambda: f'={P("other_rev")}*(1+{V("other_g")})', ae=lambda: f'={V("rail_rev")}*{V("other_pct")}')
    S('other_g', '  Other revenue y/y %', 'growth', 'pct', all=growth('other_rev'), qe=lambda: f'={YY("other_rev")}')
    S('other_pct', '  Other revenue % of rail freight revenue (merchandise + intermodal + coal)', 'pct', 'pct',
      all=lambda: f'=IF(ISNUMBER({V("other_rev")}),IFERROR({V("other_rev")}/{V("rail_rev")},""),"")', ae_in=V0['other_pct'],
      note='2027E+ input: 2025 3.8%, 9M-26 3.9%.')
    blank()
    S('g_hdr', 'Group Total — revenue build → FY26 calibration (optional, unverified outlook anchors)', 'block', note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('rail_rev', 'Rail freight revenue (merchandise + intermodal + coal)', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("merch_rev")}),{V("merch_rev")}+{V("intermodal_rev")}+{V("coal_rev")},"")')
    S('tot_vol', 'Total volume (thousands of units; merchandise + intermodal + coal)', 'line', 'm', data='a_total_vol', flow=True,
      fc=lambda: f'={V("merch_vol")}+{V("intermodal_vol")}+{V("coal_vol")}')
    S('tot_vol_g', '  Total volume y/y %', 'growth', 'pct', all=growth('tot_vol'))
    S('g_rev', 'Total revenue (build)', 'total', 'm', hist=lambda: f'=IF(ISNUMBER({V("merch_rev")}),{V("rail_rev")}+N({V("truck_rev")})+N({V("other_rev")}),{V("is_rev")})',
      fc=lambda: f'={V("rail_rev")}+{V("truck_rev")}+{V("other_rev")}+N({V("m_rev")})', note='Σ markets + trucking + other (+ future acquisitions). Drives the income statement.')
    S('g_rev_g', '  Total revenue y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_rpu', '  Total revenue per unit ($; company "Total" RPU = total revenue ÷ total units)', 'line', 'm', all=lambda: f'=IFERROR({V("g_rev")}/{V("tot_vol")}*1000,"")')
    S('g_chk', '  Check: market build vs reported revenue (should be 0; ±1 rounding)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_rev")}),ISNUMBER({V("is_rev")})),IF(ABS({V("g_rev")}-{V("is_rev")})<=1.01,0,ROUND({V("g_rev")}-{V("is_rev")},0)),"")')
    S('br_h', '  Revenue growth bridge (rail freight): volume effect / revenue-per-unit effect', 'sub', 'gen')
    def _br(kind):
        def f():
            if not CTX.col.prior: return None
            terms = []
            for g in ('merch', 'intermodal', 'coal'):
                if kind == 'vol': terms.append(f'({V(g + "_vol")}-{P(g + "_vol")})*{P(g + "_rpu")}/1000')
                else: terms.append(f'({V(g + "_rpu")}-{P(g + "_rpu")})*{V(g + "_vol")}/1000')
            return f'=IF(AND(ISNUMBER({V("merch_rpu")}),ISNUMBER({P("merch_rpu")})),{"+".join(terms)},"")'
        return f
    S('br_vol', '    Volume effect (Δ units × prior-period revenue per unit)', 'line', 'm', all=_br('vol'))
    S('br_rpu', '    Revenue-per-unit effect (Δ RPU × current units; price, mix, fuel surcharge)', 'line', 'm', all=_br('rpu'))
    S('br_chk', '    Check: volume + RPU effects = Δ rail freight revenue (should be 0; ±3: revenue per unit is published to the nearest $1)', 'check', 'm',
      all=lambda: (f'=IF(AND(ISNUMBER({V("br_vol")}),ISNUMBER({P("rail_rev")})),IF(ABS({V("br_vol")}+{V("br_rpu")}-({V("rail_rev")}-{P("rail_rev")}))<=3.01,0,ROUND({V("br_vol")}+{V("br_rpu")}-({V("rail_rev")}-{P("rail_rev")}),0)),"")' if CTX.col.prior else None))
    S('fsc_rev', '  Memo: fuel surcharge revenue (published from 2014; inside the market revenues, excl. trucking)', 'memo', 'm', data='fsc_rev', flow=True)
    S('fsc_pct', '  Memo: fuel surcharge % of rail freight revenue', 'memo_calc', 'pct', all=lambda: f'=IF(ISNUMBER({V("fsc_rev")}),IFERROR({V("fsc_rev")}/{V("rail_rev")},""),"")')
    S('fsc_lag', '  Memo: fuel lag (unfavorable) / favorable', 'memo', 'm', data='fsc_lag', flow=True)
    # calibration
    S('cal_h', '  FY26 calibration (anchors are optional inputs in the scenario table; blank = no calibration):', 'sub', 'gen')
    S('cal_tgt', '  Memo: FY26 revenue target = FY2025 × (1 + outlook revenue growth) — UNVERIFIED call commentary', 'memo', 'm',
      e26=lambda: f'=IF(ISNUMBER({CH(SC["out_g"])}),{Y("is_rev", 2025)}*(1+{CH(SC["out_g"])}),"")', note=V0['rev_guid_note'])
    S('cal_pre', '  Revenue before calibration (Q4/26E helper)', 'line', 'm',
      qe=lambda: '=' + '+'.join(f'{P(g + "_vol")}*(1+{YY(g + "_vol")})*{P(g + "_rpu")}*(1+{YY(g + "_rpu")})/1000' for g in GROUPS) + f'+{P("truck_rev")}*(1+{YY("truck_rev")})+{P("other_rev")}*(1+{YY("other_rev")})')
    S('cal_sens', '  Revenue sensitivity to +1.00 of revenue-per-unit growth (Q4/26E helper)', 'line', 'm',
      qe=lambda: '=' + '+'.join(f'{P(g + "_vol")}*(1+{YY(g + "_vol")})*{P(g + "_rpu")}/1000' for g in GROUPS))
    S('cal_p', '  Calibration Δ: revenue-per-unit growth, all markets (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=IF(ISNUMBER({V("cal_tgt", E26)}),({V("cal_tgt", E26)}-{ACT("g_rev")}-{V("cal_pre")})/{V("cal_sens")},0)',
      note='Solves the uniform RPU-growth shift so FY26 revenue = the outlook end-point for the active scenario (0 if the outlook cell is blank).')
    S('cal_v', '  Calibration Δ: volume growth, all markets (Q4/26E; input, 0 = 9M-26 y/y trend)', 'driver', 'pct', qe_in=0.0,
      note='No volume anchor in any filing; the revenue solve runs through RPU. Enter a shift here to test volume scenarios.')
    S('cal_rev_chk', '  Check: FY26 revenue vs outlook end-point (should be 0 when a target is entered; ±1)', 'check', 'm',
      e26=lambda: f'=IF(ISNUMBER({V("cal_tgt")}),IF(ABS({V("g_rev")}-{V("cal_tgt")})<=1.01,0,ROUND({V("g_rev")}-{V("cal_tgt")},0)),0)')
    S('cal_om_tgt', '  Memo: Q4/26E operating margin target = Q4/25 margin + outlook improvement (bps) — UNVERIFIED call commentary', 'memo', 'pct',
      qe=lambda: f'=IF(ISNUMBER({CH(SC["out_m"])}),{P("is_om")}+{CH(SC["out_m"])}/10000,"")', note=V0['om_guid_note'])
    S('cal_oi_pre', '  Operating income before margin calibration (Q4/26E helper)', 'line', 'm',
      qe=lambda: f'={V("is_rev")}*(1-{V("labor_pct_pre")}-{V("pso_pct_pre")}-{V("rents_pct")})-{V("fuel")}-{V("dep")}')
    S('cal_m', '  Calibration Δ: labor and purchased-services cost ratios (each, Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=IF(ISNUMBER({V("cal_om_tgt")}),({V("cal_oi_pre")}-{V("cal_om_tgt")}*{V("is_rev")})/(2*{V("is_rev")}),0)',
      note='Solves the uniform shift of the labor and purchased-services ratios so the Q4/26E operating margin = the target (0 if the outlook cell is blank).')
    S('cal_om_chk', '  Check: Q4/26E operating margin vs target (should be 0 when a target is entered; bps)', 'check', 'm1',
      qe=lambda: f'=IF(ISNUMBER({V("cal_om_tgt")}),ROUND(({V("is_om")}-{V("cal_om_tgt")})*10000,1),0)')
    S('cal_om_fy', '  Memo: FY26 operating margin improvement vs FY25 adjusted margin (bps; outlook ">350 bps", information)', 'memo_calc', 'm',
      e26=lambda: f'=({V("is_om")}-{Y("o_adj_m", 2025)})*10000')
    S('cal_capex', '  Memo: FY26 capital investment outlook "less than $2.4bn" (10-Q, verified) vs model property additions', 'memo_calc', 'm',
      e26=lambda: f'=-{V("cf_capex")}')
    blank()

    # ------------------------------------------------------------------ legacy markets memo
    S('lg_hdr', 'Legacy market structures (as originally reported; memo) — 2006 – Q1/10: automotive outside merchandise, coke & iron ore in coal, intermodal by international / domestic; Q2/10 – Q4/12: eight merchandise markets; Q1/13 – Q2/16: Emerging Markets split into Minerals and Waste & Equipment', 'block',
      note='LEGACY MARKETS — revenue by market as published before the Q3/16 re-cut (volumes in the next block). Current-basis rows above are blank before Q3/15.')
    for k, lab in LEGACY:
        S(f'lg_{k}_rev', f'  {lab} — revenue', 'memo', 'm', data=f'l_{k}_rev', flow=True)
    S('lg_chk', '  Check: Σ legacy markets vs reported revenue (should be 0; ±1)', 'check', 'm',
      hist=lambda: (f'=IF(AND(ISNUMBER({V("lg_chem_rev")}),NOT(ISNUMBER({V("chem_rev")}))),IF(ABS({nsum(["lg_" + k + "_rev" for k, _ in LEGACY])}'
                    f'-IF(ISNUMBER({V("lg_intl_rev")}),N({V("lg_intermodal_rev")}),0)-{V("is_rev")})<=1.01,0,'
                    f'ROUND({nsum(["lg_" + k + "_rev" for k, _ in LEGACY])}-IF(ISNUMBER({V("lg_intl_rev")}),N({V("lg_intermodal_rev")}),0)-{V("is_rev")},0)),"")'))
    S('lgv_h', '  Legacy market volumes (thousands of units):', 'sub', 'gen')
    for k, lab in LEGACY:
        if k in ('railother', 'imother', 'other'): continue
        S(f'lg_{k}_vol', f'  {lab} — volume', 'memo', 'm', data=f'l_{k}_vol', flow=True)
    S('seg_h', '  Reportable segments to Q1/10 (Rail · Intermodal; memo):', 'sub', 'gen')
    S('seg_rail_rev', '  Rail segment revenue', 'memo', 'm', data='seg_rail_rev', flow=True)
    S('seg_im_rev', '  Intermodal segment revenue', 'memo', 'm', data='seg_im_rev', flow=True)
    S('seg_rail_oi', '  Rail segment operating income', 'memo', 'm', data='seg_rail_oi', flow=True)
    S('seg_im_oi', '  Intermodal segment operating income', 'memo', 'm', data='seg_im_oi', flow=True)
    S('seg_chk', '  Check: Rail + Intermodal revenue vs consolidated (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("seg_rail_rev")}),IF(ABS({V("seg_rail_rev")}+{V("seg_im_rev")}-{V("is_rev")})<=1.01,0,ROUND({V("seg_rail_rev")}+{V("seg_im_rev")}-{V("is_rev")},0)),"")')
    blank()
    S('st_hdr', 'Operating statistics (estimated by the company; memo)', 'block', note='OPERATING STATISTICS — memo (not forecast except gross ton-miles, which scale with volume for the fuel build)')
    S('st_rtm', '  Revenue ton-miles (billions)', 'memo', 'm1', data='rtm', flow=True)
    S('st_gtm', '  Gross ton-miles (billions)', 'memo', 'm1', data='gtm', flow=True, fc=lambda: f'={P("st_gtm")}*(1+{V("tot_vol_g")})',
      note='Forecast: prior period × (1 + total volume growth) — drives locomotive fuel gallons.')
    S('st_eff', '  Fuel efficiency (gallons per 1,000 GTM; published from 2020, computed before)', 'memo', 'ps', data='fuel_eff',
      all=lambda: f'=IF(ISNUMBER({V("fuel_gal")}),IFERROR({V("fuel_gal")}/{V("st_gtm")},""),"")')
    S('st_vel', '  Train velocity (mph)', 'memo', 'm1', data='velocity')
    S('st_dwell', '  Dwell (hours)', 'memo', 'm1', data='dwell')
    S('st_emp', '  Average employees (published from Q2/25; 10-K year-end counts before)', 'memo', 'm', data='emp_avg')
    S('st_emp_ye', '  Employees at year end (10-K)', 'memo', 'm', data='employees_ye')
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever; Base 0 — CSX has made no acquisition since Pan Am, Jun-2022)', 'block',
      note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention; Base case nil')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=2.5, e26_in=0.0,
      note='Quality Carriers (Jul-2021): $544m on ~$800m of revenue (~0.7x, trucking); Pan Am (Jun-2022): $600m (regional railroad; revenue not disclosed). 2.5x input (assumption).')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.03)
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}', note='Mid-year convention.')
    S('m_m', '  Operating margin of acquired businesses %', 'driver', 'pct', e26_in=0.0, ae_in=0.15)
    S('m_oi', '  Operating income from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.60)
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.20, note='Quality Carriers: intangibles $180m of $544m (33%).')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=15)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (inside D&A)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)')
    blank()

    # ------------------------------------------------------------------ COST BUILD
    S('sec_cost', 'COST BUILD & OPERATING RATIO — expense lines as presented (labor & fringe · purchased services & other · fuel · D&A · equipment rents · other)', 'section',
      note='COST BUILD — Q4/26E: prior-year quarter ratio + 9M-26 drift (+ margin calibration Δ on labor and purchased services); fuel = gallons × price per gallon; 2027E+: scenario levers (labor %, purchased services %), fuel from gross ton-miles × efficiency × price, D&A % of opening net properties, rents % of revenue')
    S('labor', 'Labor and fringe', 'line', 'm', data='labor', flow=True, fc=lambda: f'={V("is_rev")}*{V("labor_pct")}')
    S('labor_pct', '  Labor and fringe % of revenue', 'pct', 'pct', all=ratio('labor', 'is_rev'),
      qe=lambda: f'={V("labor_pct_pre")}+{QEa("cal_m")}', ae=lambda: '=' + CH(SC['LABOR'][CTX.col.year]),
      note='Q4/26E: ratio before calibration + margin Δ. 2027E+: scenario lever (2025 23.1%; 9M-26 21.7%; Q3-26 20.8%; headcount −6% y/y in Q3-26).')
    S('labor_pct_pre', '  Q4/26E labor ratio before calibration (prior-year quarter + 9M-26 y/y drift)', 'driver', 'pct',
      qe=lambda: f'={P("labor_pct")}+IFERROR({ACT("labor")}/{ACT("is_rev")}-{ACT0("labor")}/{ACT0("is_rev")},0)')
    S('labor_emp', '  Memo: labor and fringe per average employee ($ thousands, annualised)', 'memo_calc', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("st_emp")}),IFERROR({V("labor")}*{4 if CTX.col.q else 1}/{V("st_emp")}*1000,""),"")')
    S('pso', 'Purchased services and other (materials, supplies and other to Q2/21; incl. equity earnings of affiliates and property gains unless shown separately)', 'line', 'm', data='pso', flow=True,
      fc=lambda: f'={V("is_rev")}*{V("pso_pct")}')
    S('pso_pct', '  Purchased services and other % of revenue', 'pct', 'pct', all=ratio('pso', 'is_rev'),
      qe=lambda: f'={V("pso_pct_pre")}+{QEa("cal_m")}', ae=lambda: '=' + CH(SC['PSO'][CTX.col.year]),
      note='Q4/26E: ratio before calibration + margin Δ. 2027E+: scenario lever (2025 21.4%; 9M-26 16.8%; Q3-26 16.4%, incl. $11m of property gains).')
    S('pso_pct_pre', '  Q4/26E purchased-services ratio before calibration (prior-year quarter + 9M-26 y/y drift)', 'driver', 'pct',
      qe=lambda: f'={P("pso_pct")}+IFERROR({ACT("pso")}/{ACT("is_rev")}-{ACT0("pso")}/{ACT0("is_rev")},0)')
    S('fuel', 'Fuel', 'line', 'm', data='fuel', flow=True, fc=lambda: f'={V("fuel_loco")}+{V("fuel_nonloco")}',
      note='Forecast = locomotive fuel (gallons × price) + non-locomotive fuel.')
    S('fuel_gal', '  Locomotive fuel consumption (millions of gallons; estimated)', 'line', 'm1', data='fuel_gal', flow=True,
      qe=lambda: f'={P("fuel_gal")}*(1+{YY("fuel_gal")})', ae=lambda: f'={P("fuel_gal")}*(1+{V("tot_vol_g")})*(1-{V("fuel_eff_g")})',
      note='Q4/26E: prior-year quarter × (1 + 9M-26 y/y). 2027E+: prior year × (1 + total volume growth) × (1 − efficiency gain).')
    S('fuel_eff_g', '  Locomotive fuel efficiency gain % p.a. (gallons per GTM; input)', 'driver', 'pct', ae_in=V0['fuel_eff_g'],
      note='Gallons per 1,000 GTM: 2020 0.98 → 2025 0.97 → 9M-26 0.94 (−3%). Input 1% p.a. (assumption).')
    S('fuel_ppg', '  Locomotive fuel price per gallon ($)', 'line', 'm2', data='fuel_ppg', avg=True, qe=lambda: f'={PT("pt_ppg")}', ae_in=V0['ppg'],
      note='Q4/26E point estimate (Q3-26 $4.24; 9M-26 $3.69). 2027E+ input held near the 9M-26 average (assumption; fuel surcharge recovers most of the change with a two-month lag).',
      e26=lambda: f'=IFERROR({V("fuel_loco")}/{V("fuel_gal")},"")')
    S('fuel_loco', '  Locomotive fuel expense', 'line', 'm', data='fuel_loco', flow=True, fc=lambda: f'={V("fuel_gal")}*{V("fuel_ppg")}')
    S('fuel_nonloco', '  Non-locomotive fuel expense (trucking, vehicles, equipment)', 'line', 'm', data='fuel_nonloco', flow=True, fc=lambda: f'={V("is_rev")}*{V("nonloco_pct")}')
    S('nonloco_pct', '  Non-locomotive fuel % of revenue', 'pct', 'pct', all=ratio('fuel_nonloco', 'is_rev'), qe=lambda: f'=IFERROR({ACT("fuel_nonloco")}/{ACT("is_rev")},0)', ae_in=V0['nonloco_pct'])
    S('dep', 'Depreciation and amortization', 'line', 'm', data='dep', flow=True, qe=lambda: f'={PT("pt_dep")}', ae=lambda: f'={P("bs_ppe")}*{V("dep_pct")}+N({V("m_amort")})',
      note='Q4/26E point estimate (Q3-26 $413m; equipment depreciation study). 2027E+: % of opening net properties (+ future-acquisition amortization).')
    S('dep_pct', '  D&A % of opening net properties', 'pct', 'pct', all=lambda: (f'=IFERROR({V("dep")}*{4 if CTX.col.q else 1}/{P("bs_ppe")},"")' if CTX.col.prior else None), ae_in=V0['dep_pct'],
      note='2025 4.7%, 2024 4.8%; 2027E+ input 4.6% (depreciation study lowered equipment rates in 2026).')
    S('rents', 'Equipment and other rents', 'line', 'm', data='rents', flow=True, fc=lambda: f'={V("is_rev")}*{V("rents_pct")}')
    S('rents_pct', '  Equipment and other rents % of revenue', 'pct', 'pct', all=ratio('rents', 'is_rev'), qe=lambda: f'={P("rents_pct")}', ae_in=V0['rents_pct'])
    S('inland', 'Inland transportation (intermodal drayage; separate line to Q1/10)', 'line', 'm', data='inland', flow=True, fc=lambda: '=0')
    S('oth_exp', 'Other operating items shown separately (Conrail rents 2006; insurance recovery gains 2006–08; equity earnings of affiliates Q4/17–Q1/19; other operating income 2006–08)', 'line', 'm',
      data='oth_exp', flow=True, fc=lambda: '=0', labkey='oth_exp_lab')
    S('gain_disp', 'Gains on property dispositions (separate line Q2/21 – Q4/24; inside purchased services otherwise; negative = gain)', 'line', 'm', data='gain_disp', flow=True, fc=lambda: '=0')
    S('impair', 'Goodwill impairment (Quality Carriers: Q4/24 $108m, Q3/25 $164m)', 'line', 'm', data='impair', flow=True, fc=lambda: f'={V("d_impair")}')
    S('restr', 'Restructuring charge (2017 management workforce reduction)', 'line', 'm', data='restr', flow=True, fc=lambda: f'={V("d_restr")}')
    S('tot_exp', 'Total expense', 'line_b', 'm', hist=lambda: f'=IF(ISNUMBER({V("labor")}),{nsum(["labor", "pso", "fuel", "dep", "rents", "inland", "oth_exp", "gain_disp", "impair", "restr"])},"")',
      fc=lambda: f'={nsum(["labor", "pso", "fuel", "dep", "rents", "inland", "oth_exp", "gain_disp", "impair", "restr"])}')
    S('tot_exp_chk', '  Check: Σ expense lines vs reported total expense (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("tot_exp_pub")}),IF(ABS({V("tot_exp")}-{V("tot_exp_pub")})<=0.6,0,ROUND({V("tot_exp")}-{V("tot_exp_pub")},0)),"")')
    S('tot_exp_pub', '  Memo: total expense as reported (2006–08: Surface Transportation expense less other operating income)', 'memo', 'm', data='tot_exp', flow=True)
    S('or_', 'Operating ratio (total expense ÷ revenue)', 'total', 'pct', all=ratio('tot_exp', 'is_rev'))
    S('or_yy', '  Operating ratio change y/y (bps)', 'growth', 'm', all=lambda: (f'=IF(AND(ISNUMBER({V("or_")}),ISNUMBER({P("or_")})),({V("or_")}-{P("or_")})*10000,"")' if CTX.col.prior else None))
    S('d_adj_h', '  Company adjusting items (pre-tax; inside operating income unless noted) — forecast inputs:', 'sub', 'gen')
    S('d_impair', '  Goodwill impairment', 'line', 'm', data='oa_impair', flow=True, labkey='oa_lab', fc=lambda: '=0')
    S('d_restr', '  Restructuring charge', 'line', 'm', data='oa_restr', flow=True, fc=lambda: '=0')
    S('d_gain', '  (Gains) on insurance recoveries (2006–07)', 'line', 'm', data='oa_gain', flow=True, fc=lambda: '=0')
    S('d_other', '  Other company items in operating income (Q4/17 Tax Reform remeasurement in equity earnings of affiliates)', 'line', 'm', data='oa_other', flow=True, fc=lambda: '=0')
    S('d_basis', '  Basis difference: company comparable OI = Surface Transportation OI, excl. other operating income (2006–07)', 'line', 'm', data='oa_basis', flow=True, fc=lambda: '=0')
    S('d_nonop', '  Items below operating income (Conrail property gain 2006; Greenbrier impairment 2008)', 'line', 'm', data='oa_nonop', flow=True, fc=lambda: '=0')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED INCOME STATEMENT (US GAAP)', 'section', note='CONSOLIDATED IS — revenue from the market build, expense from the cost build; interest on opening debt; tax at the input rate')
    S('is_rev', 'Revenue', 'total', 'm', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the market build.')
    S('is_rev_g', '  Revenue y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('is_exp', 'Total expense', 'line', 'm', all=lambda: f'={V("tot_exp")}')
    S('is_oi', 'Operating income', 'total', 'm', hist=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}-{V("is_exp")},"")', fc=lambda: f'={V("is_rev")}-{V("is_exp")}+N({V("m_oi")})',
      note='Revenue − total expense (+ operating income of future acquisitions).')
    S('is_oi_chk', '  Check: operating income vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_oi_pub")}),IF(ABS({V("is_oi")}-{V("is_oi_pub")})<=0.6,0,ROUND({V("is_oi")}-{V("is_oi_pub")},0)),"")')
    S('is_oi_pub', '  Memo: operating income as reported', 'memo', 'm', data='oi', flow=True)
    S('is_om', '  Operating margin %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('is_om_pub', '  Memo: operating margin as published (from 2020)', 'memo', 'pct', data='op_margin_pub')
    S('is_int', 'Interest expense', 'line', 'm', data='int_exp', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'=({P("ds_notes")}+{P("ds_pn")})*{V("ds_r_notes")}+{P("ds_cp")}*{V("ds_r_cp")}+{V("ds_iss")}*{V("ds_r_new")}*0.5',
      note='Q4/26E point estimate (Q3-26 $207m). 2027E+ = rate × opening notes (incl. plug notes) + rate × opening commercial paper + half a year on the refinancing notes (input); interest on in-year plug borrowings starts the following year (no circularity).')
    S('is_debt_rep', 'Debt repurchase expense (2005 comparative; 2016 $115m)', 'line', 'm', data='debt_rep', flow=True, fc=lambda: '=0')
    S('is_othinc', 'Other income — net (interest income, real estate, miscellaneous; income +)', 'line', 'm', data='oth_inc', flow=True, qe=lambda: f'={PT("pt_othinc")}', ae_in=V0['othinc'],
      note='Q4/26E point estimate (Q3-26 $21m). 2027E+ input ($90m; 2025 $92m, 2024 $142m incl. higher interest income on cash).')
    S('is_ebt', 'Earnings before income taxes', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_oi")}),{V("is_oi")}-{V("is_int")}-{V("is_debt_rep")}+{V("is_othinc")},"")')
    S('is_tax', 'Income tax expense', 'line', 'm', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Q4/26E point estimate (9M-26 24.1%). 2027E+ input 24.5% (2025 23.3%, 2024 23.8%; 21% federal + state).')
    S('is_cont', 'Earnings from continuing operations', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_disc', 'Discontinued operations — net of tax (2005 comparative; 2007 $110m tax benefit)', 'line', 'm', data='disc_ops', flow=True, fc=lambda: '=0')
    S('is_ni', 'Net earnings', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_cont")}),{V("is_cont")}+{V("is_disc")},"")')
    S('is_ni_chk', '  Check: net earnings vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=0.6,0,ROUND({V("is_ni")}-{V("is_ni_pub")},0)),"")')
    S('is_ni_pub', '  Memo: net earnings as reported', 'memo', 'm', data='ni', flow=True)
    S('is_dda', '  Memo: depreciation and amortization', 'memo_calc', 'm', all=lambda: f'={V("dep")}')
    S('is_sbc', '  Memo: share-based compensation (10-K / 10-Q XBRL)', 'memo', 'm', data='sbc', flow=True, qe=lambda: f'={PT("pt_sbc")}', ae=lambda: f'={V("is_rev")}*{V("sbc_pct")}')
    S('sbc_pct', '  Share-based compensation % of revenue', 'pct', 'pct', all=ratio('is_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('eps_hdr', '(Per common share — restated for the 3-for-1 splits of 31-May-2011 and 28-Jun-2021)', 'sub', 'gen')
    S('sh_dil', '  Weighted-average shares outstanding, assuming dilution (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={B1("bs_shares")}-${E26}${R["bb_sh"]}*0.5+${E26}${R["bb_iss"]}*0.5+{V("ds_dil")}',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})+{V("ds_dil")}',
      note='Q4/26E: shares outstanding at 30-Sep-2026 (10-Q cover) − Q4 buybacks (mid-quarter) + equity-plan issuance + dilutive awards. 2027E+: average of beginning and ending shares + dilutive awards.')
    S('eps_dil', 'Net earnings per share, assuming dilution ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")',
      note='Net earnings ÷ diluted shares (±$0.005 vs reported after split restatement).')
    S('eps_dil_g', '  EPS y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS as reported, split-adjusted ($)', 'eps_memo', 'ps3', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.005 rounding, ±0.0101 for 2006–10 after the ×9 restatement)', 'check', 'ps3',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<={"0.0101" if CTX.col.year <= 2010 else "0.0051"},0,ROUND({V("eps_dil")}-{V("eps_pub")},3)),"n/p")')
    S('eps_cont_pub', '  Memo: EPS from continuing operations as reported (2006–08, split-adjusted)', 'eps_memo', 'ps3', data='eps_cont')
    S('dps', '  Cash dividends per share ($; split-adjusted)', 'line', 'ps3', data='dps', flow=True, qe_in=V0['dps_q'],
      ae=lambda: f'={P("dps")}*(1+{V("dps_g")})', note='Release income statements to 2016, then 10-K / 10-Q XBRL (declared / paid per share; Q4 = FY − 9M). Quarterly $0.14 from March 2026. 2027E+: prior year × (1 + growth).')
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'], note='2026 +8% (10-Q); 2025 +8%; 2024 +9%. Input 8% p.a.')
    blank()

    # ------------------------------------------------------------------ RECON 1: OI -> adjusted OI
    S('sec_r1', 'RECONCILIATION: OPERATING INCOME → ADJUSTED OPERATING INCOME (company "comparable" / "adjusted" measures where published; adjusted = GAAP otherwise)', 'section',
      note='ADJUSTED OPERATING INCOME — company items only (2006–08 comparable, 2017 restructuring / Tax Reform, Q4/24 and Q3/25 goodwill impairment); forecast items nil')
    S('o_op', 'Operating income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_oi")}')
    for k, lab, d in (('o_impair', '  (+) Goodwill impairment', 'd_impair'), ('o_restr', '  (+) Restructuring charge', 'd_restr'),
                      ('o_gain', '  (−) Gains on insurance recoveries', 'd_gain'), ('o_oth', '  (+/−) Other company items in operating income', 'd_other'),
                      ('o_basis', '  (−) Basis difference: other operating income excluded from the company\'s comparable OI (2006–07)', 'd_basis')):
        S(k, lab, 'line', 'm', all=lambda d=d: f'={V(d)}')
    S('o_tot', '  Total adjusting items in operating income (pre-tax)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("o_impair")}),{nsum(["o_impair", "o_restr", "o_gain", "o_oth", "o_basis"])},"")')
    S('o_adj', '  = Adjusted operating income (model bridge)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_tot")},"")',
      note='GAAP operating income + company adjusting items. Used for adjusted EBITDA, leverage, ROIC and the DCF (less the basis line, which is presentation only).')
    S('o_adj_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_or', '  Adjusted operating ratio %', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("o_adj_m")}),1-{V("o_adj_m")},"")')
    S('o_pub', '  Company-published comparable / adjusted operating income', 'memo', 'm', data='adj_oi_pub', flow=True)
    S('o_chk', '  Check: model bridge vs company-published (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),IF(ABS({V("o_adj")}-{V("o_pub")})<=0.6,0,ROUND({V("o_adj")}-{V("o_pub")},0)),"n/p")')
    S('o_def', '  Definition / basis (company adjusted definition in force)', 'text', 'gen', note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('o_adj_g', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental adjusted operating margin (Δ adjusted OI / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    S('o_rest', '  Memo: 2017 operating income as reclassified for ASU 2017-07 in the 2018 releases (pension cost below OI)', 'memo', 'm', data='oi_restated', flow=True)
    blank()

    # ------------------------------------------------------------------ RECON 2: NI -> EBITDA -> adjusted EBITDA
    S('sec_r2', 'RECONCILIATION: NET EARNINGS → EBITDA → ADJUSTED EBITDA (model definition — CSX publishes no EBITDA)', 'section',
      note='EBITDA (model) = net earnings + tax − discontinued + interest + debt repurchase − other income + D&A = operating income + D&A; adjusted EBITDA adds the company items in operating income')
    S('r_ni', 'Net earnings (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('r_disc', '  (−) Discontinued operations', 'line', 'm', all=lambda: f'=-{V("is_disc")}')
    S('r_tax', '  (+) Income tax expense', 'line', 'm', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest expense and debt repurchase expense', 'line', 'm', all=lambda: f'={V("is_int")}+{V("is_debt_rep")}')
    S('r_othinc', '  (−) Other income — net', 'line', 'm', all=lambda: f'=-{V("is_othinc")}')
    S('r_ebit', '  = Operating income (EBIT)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_disc")}+{V("r_tax")}+{V("r_int")}+{V("r_othinc")},"")')
    S('r_ebit_chk', '  Check: rebuilt EBIT vs operating income (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_ebit")}),IF(ABS({V("r_ebit")}-{V("is_oi")})<=0.6,0,ROUND({V("r_ebit")}-{V("is_oi")},0)),"")')
    S('r_dda', '  (+) Depreciation and amortization', 'line', 'm', all=lambda: f'={V("dep")}')
    S('r_ebitda', '  = EBITDA (model)', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_ebit")}),ISNUMBER({V("r_dda")})),{V("r_ebit")}+{V("r_dda")},"")')
    S('r_ebitda_m', '  EBITDA margin %', 'pct', 'pct', all=ratio('r_ebitda', 'is_rev'))
    S('r_adjx', '  (+) Company adjusting items in operating income (excl. the 2006–07 basis line)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_tot")}),{V("o_tot")}-N({V("o_basis")}),"")')
    S('r_adj', '  = Adjusted EBITDA (model)', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda")}),ISNUMBER({V("r_adjx")})),{V("r_ebitda")}+{V("r_adjx")},"")',
      note='Model definition (no company EBITDA). Used for leverage (net debt / adjusted EBITDA) and EV / EBITDA.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_ebit_h', 'To adjusted EBIT (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ddan', '  (−) Depreciation and amortization', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("r_dda")}),-{V("r_dda")},"")')
    S('r_aebit', '  = Adjusted EBIT (= adjusted operating income excl. the basis line)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+{V("r_ddan")},"")',
      note='CSX has no acquired-intangible amortization of note ($12m p.a. on the Quality Carriers intangibles) and expenses share-based compensation; adjusted EBIT = adjusted operating income.')
    S('r_aebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_aebit', 'is_rev'))
    S('r_cash', '  Memo: cash restructuring costs adjusted out (deducted in the DCF NOPAT)', 'memo_calc', 'm', all=lambda: f'=IF(ISNUMBER({V("o_restr")}),{V("o_restr")},"")')
    S('r_lev_ltm', '  Memo: LTM adjusted EBITDA (quarter columns; for quarter-end leverage)', 'memo_calc', 'm',
      all=lambda: (f'=IF(ISNUMBER({V("r_adj")}),SUM({V("r_adj")},{PQ("r_adj")},{QC[(CTX.col.year, CTX.col.q - 2)].c if CTX.col.q >= 3 else QC[(CTX.col.year - 1, CTX.col.q + 2)].c}{R["r_adj"]},{QC[(CTX.col.year, CTX.col.q - 3)].c if CTX.col.q >= 4 else QC[(CTX.col.year - 1, CTX.col.q + 1)].c}{R["r_adj"]}),"")'
                   if (CTX.col.q and CTX.col.prevq and (CTX.col.year, CTX.col.q) >= (2013, 4)) else (f'={V("r_adj")}' if not CTX.col.q else None)))
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: NET EARNINGS / DILUTED EPS → ADJUSTED NET EARNINGS → ADJUSTED EPS (company "comparable" / "adjusted" definition where published)', 'section',
      note='ADJUSTED EPS — net earnings − discontinued operations + pre-tax items (operating and non-operating) − tax effect & discrete tax items; 2006–08: company comparable EPS from continuing operations (per-share only; $m = EPS × diluted shares)')
    S('e_ni', 'Net earnings (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('e_disc', '  (−) Discontinued operations (company comparable EPS is from continuing operations)', 'line', 'm', all=lambda: f'=-{V("is_disc")}')
    S('e_op', '  (+) Adjusting items in operating income (pre-tax; bridge above, excl. the basis line)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("o_tot")}),{V("o_tot")}-N({V("o_basis")}),"")')
    S('e_nonop', '  (+) Items below operating income (pre-tax)', 'line', 'm', all=lambda: f'={V("d_nonop")}')
    S('e_tax', '  (−) Tax effect of the items & discrete tax items (2006 audit resolutions; 2008 tax benefit / equity-earnings adjustment; Q4/17 Tax Reform)', 'line', 'm', flow=True,
      hist=lambda: (f'=IF(ISNUMBER({V("e_pubni")}),{V("e_pubni")}-{V("e_ni")}-{V("e_disc")}-{V("e_op")}-{V("e_nonop")},'
                    f'IF(ISNUMBER({V("e_pub")}),ROUND({V("e_pub")}*{V("sh_dil")},0)-{V("e_ni")}-{V("e_disc")}-{V("e_op")}-{V("e_nonop")},IF(ISNUMBER({V("e_ni")}),0,"")))'),
      fc=lambda: f'=-({V("e_op")}+{V("e_nonop")})*{V("is_etr")}',
      note='Historical: published adjusted net earnings − net earnings − items (2006–08: comparable EPS × diluted shares, a per-share-only disclosure; cell comment). Forecast: items × tax rate (items nil).')
    S('e_adjni', '  = Adjusted net earnings (model bridge)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("e_tax")}),{V("e_ni")}+{V("e_disc")}+{V("e_op")}+{V("e_nonop")}+{V("e_tax")},"")')
    S('e_pubni', '  Company-published adjusted net earnings (2017, 2024–25)', 'memo', 'm', data='adj_ni_pub', flow=True)
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted EPS — diluted ($) (model bridge)', 'eps_total', 'ps3', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published comparable / adjusted EPS ($; split-adjusted)', 'eps_memo', 'ps3', data='adj_eps_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.000; ±0.005 rounding, ±0.0101 for 2006–08 after the ×9 restatement)', 'check', 'ps3',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<={"0.0101" if CTX.col.year <= 2010 else "0.0051"},0,ROUND({V("e_eps")}-{V("e_pub")},3)),"n/p")')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_adjebt', '  Adjusted earnings before tax (adjusted EBIT − interest − debt repurchase + other income + non-operating items)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_aebit")}),{V("r_aebit")}-{V("is_int")}-{V("is_debt_rep")}+{V("is_othinc")}+{V("e_nonop")},"")')
    S('e_adjtax', '  Adjusted income tax (adjusted EBT − adjusted net earnings)', 'line', 'm', flow=True,
      all=lambda: f'=IF(AND(ISNUMBER({V("e_adjni")}),ISNUMBER({V("e_adjebt")})),{V("e_adjebt")}-{V("e_adjni")},"")')
    S('e_rate', '  Adjusted effective tax rate', 'pct', 'pct', all=ratio('e_adjtax', 'e_adjebt'))
    S('e_def', '  Definition / basis (company adjusted EPS definition)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Revenue y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_vol', '  Total volume y/y %', 'growth', 'pct', all=growth('tot_vol'))
    S('gm_rpu', '  Total revenue per unit y/y %', 'growth', 'pct', all=growth('g_rpu'))
    S('gm_merch', '  Merchandise revenue y/y %', 'growth', 'pct', all=growth('merch_rev'))
    S('gm_im', '  Intermodal revenue y/y %', 'growth', 'pct', all=growth('intermodal_rev'))
    S('gm_coal', '  Coal revenue y/y %', 'growth', 'pct', all=growth('coal_rev'))
    S('gm_adjop', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating income (GAAP) y/y %', 'growth', 'pct', all=growth('is_oi'))
    S('gm_ni', '  Net earnings y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_or', '  Operating ratio %', 'pct', 'pct', all=ratio('tot_exp', 'is_rev'))
    S('gm_adjop_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_inc', '  Incremental adjusted operating margin (Δ adjusted OI / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_labor', '  Labor and fringe % of revenue', 'pct', 'pct', all=ratio('labor', 'is_rev'))
    S('gm_pso', '  Purchased services and other % of revenue', 'pct', 'pct', all=ratio('pso', 'is_rev'))
    S('gm_fuel', '  Fuel % of revenue', 'pct', 'pct', all=ratio('fuel', 'is_rev'))
    S('gm_dda', '  D&A % of revenue', 'pct', 'pct', all=ratio('dep', 'is_rev'))
    blank()
