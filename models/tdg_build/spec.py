"""Row specification of the TDG Model sheet, part 1 (MLM template layout and process):
segment x end-market sales build (Power & Control and Airframe: commercial OEM / commercial aftermarket / defense; Non-aviation)
-> segment EBITDA As Defined at the segment margin -> less unallocated corporate = EBITDA As Defined -> M&A lever -> group total
& FY27 guidance calibration -> cost drivers & adjusting items -> income statement -> GAAP-to-adjusted bridges -> growth & margins."""
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
def E(key): return f'${E27}${R[key]}'                      # FY2027E (absolute)
def QSUM(key): return f'SUM({Q1}{R[key]}:{QE4}{R[key]})'   # FY27 quarters
def QF(): return {1: 0.125, 2: 0.375, 3: 0.625, 4: 0.875}[CTX.col.q]   # mid-quarter share of the fiscal year elapsed

SEG = [('pc', 'Power & Control', 'PC', 'sg_pc_rev', 'sg_pc_eb'), ('af', 'Airframe', 'AF', 'sg_af_rev', 'sg_af_eb')]
MKTS = [('coem', 'Commercial OEM', 'COEM'), ('caft', 'Commercial aftermarket', 'CAFT'), ('def', 'Defense', 'DEF')]
LINES = [f'{s}_{t}' for s, *_ in SEG for t, _, _ in MKTS]
SEGK = ['pc', 'af', 'na']
ITEMS = [('acq', 'Acquisition transaction & integration-related expenses (incl. inventory step-up)', 'oa_acq'),
         ('sbc', 'Non-cash stock & deferred compensation expense', 'oa_sbc'),
         ('refin', 'Refinancing costs', 'oa_refin'),
         ('restr', 'COVID-19 / 737 MAX restructuring costs (FY2020–22)', 'oa_restr'),
         ('gain', '(Gain) / loss on sale of businesses', 'oa_gain'),
         ('oadj', 'Other, net (FX, withholding taxes on dividend equivalents, non-service pension, IPO / one-off items)', 'oa_other'),
         ('disc', 'EBITDA of discontinued operations (FY2011)', 'oa_disc')]
DITEMS = ['d_' + k for k, _, _ in ITEMS]

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
    SCEN_ROWS.append((r, 'pt_hdr', 'FY27E point estimates (all cases; Table 6 guidance-midpoint reconciliation unless noted)', None, None, None, None)); r += 1
    for key, lab, vals, nf, note in V0['points']:
        SC[key] = r
        SCEN_ROWS.append((r, 'pt', lab, None, vals, None, note, nf)); r += 1
    r += 1
    SC['LEV'] = r
    SCEN_ROWS.append((r, 'lev', '  Target net debt / EBITDA As Defined (x) — capital-return plug 2028E+', *V0['lev'], V0['lev_note']))
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
    S('sec_seg', 'SEGMENT P&L — POWER & CONTROL · AIRFRAME · NON-AVIATION (net sales by end market × segment EBITDA As Defined margin)', 'section',
      note='SEGMENT BUILD — modelling logic (net sales by end market → segment net sales → segment EBITDA As Defined at the segment margin → less unallocated corporate = EBITDA As Defined → GAAP P&L)')
    blank()
    descr = {'pc': 'Power & Control (systems and components that provide or control power: actuators, ignition, pumps, valves, motors, sensors, power conditioning, electronic components)',
             'af': 'Airframe (non-power airframe and cabin structure components: latches, rods, seat belts, lavatory, interiors, cockpit displays, audio, lighting, parachutes, cargo handling)'}
    for s, title, code, pub, earn in SEG:
        S(f'{s}_hdr', descr[s], 'block', note=f'{title.upper()} — modelling logic')
        for t, tl, mk in MKTS:
            key = f'{s}_{t}'
            S(key, f'  {tl} net sales', 'line', 'm1', data=f'em_{key}', flow=True,
              qe=lambda key=key, s=s, t=t: f'={P(key)}*(1+{V(key + "_g")})' + (f'+{V(s + "_acq")}*{V(s + "_al_" + t)}' if s == 'pc' else ''),
              ae=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})',
              note=('Net sales to external customers by end market (10-Q / 10-K segment note; from FY2017 annual, Q1 FY2018 quarterly; latest filing presenting the period; '
                    'Q4 = fiscal year − three quarters). Q1–Q4/27E: prior-year quarter × (1 + FY27 market growth) + inorganic sales (P&C). 2028E+: prior year × (1 + scenario lever).')
              if key == LINES[0] else None)
            S(key + '_g', '    y/y %', 'growth', 'pct', all=growth(key),
              qe=lambda mk=mk: f'={CH(SC["out_" + mk.lower()])}+{E("cal_g")}',
              ae=lambda mk=mk: '=' + CH(SC[mk][CTX.col.year]),
              note=('Q1–Q4/27E: FY27 guided market growth (scenario end-point; read as organic) + sales-guidance calibration Δ (Group block). '
                    '2027E column = total y/y incl. acquisitions. 2028E–2031E: scenario lever (Bull/Base/Bear table →).') if key == LINES[0] else None)
        if s == 'pc':
            S('pc_acq', '  Inorganic sales — businesses acquired in FY2026 not yet in the prior-year base (input, FY27E)', 'driver', 'm1', qe_in=V0['acq27'],
              note=V0['acq27_note'])
            for t, tl, _ in MKTS:
                S(f'pc_al_{t}', f'    Allocation of inorganic sales to {tl.lower()} (input)', 'driver', 'pct', qe_in=V0['acq27_al'][t],
                  note='Assumption: JPE / VSA are nearly all commercial aftermarket; P&I mostly aftermarket (A&D, aeroderivative, transportation); bolt-ons pro rata.' if t == 'coem' else None)
        first = f'{s}_coem'
        S(f'{s}_rev', f'  {title} — segment net sales', 'line_b', 'm1',
          hist=lambda s=s, first=first: f'=IF(ISNUMBER({V(first)}),{"+".join(V(s + "_" + t) for t, _, _ in MKTS)},IF(ISNUMBER({V(s + "_pub")}),{V(s + "_pub")},""))',
          fc=lambda s=s: '=' + '+'.join(V(s + '_' + t) for t, _, _ in MKTS),
          note='History: Σ end markets where published, otherwise segment net sales (from FY2011; latest filing presenting the period).' if s == 'pc' else None)
        S(f'{s}_rev_g', '  Segment net sales y/y %', 'growth', 'pct', all=growth(f'{s}_rev'))
        S(f'{s}_mix', '  % of total net sales', 'pct', 'pct', all=ratio(f'{s}_rev', 'g_rev'))
        S(f'{s}_aft', '  Commercial aftermarket % of segment net sales', 'pct', 'pct', all=ratio(f'{s}_caft', f'{s}_rev'))
        S(f'{s}_pub', f'  Memo: {title} segment net sales (segment note, latest filing presenting the period)', 'memo', 'm1', data=pub, flow=True)
        S(f'{s}_chk', '  Check: end markets vs segment net sales (should be 0)', 'check', 'm1',
          hist=lambda s=s, first=first: f'=IF(AND(ISNUMBER({V(first)}),ISNUMBER({V(s + "_pub")})),IF(ABS({V(s + "_rev")}-{V(s + "_pub")})<=0.15,0,ROUND({V(s + "_rev")}-{V(s + "_pub")},1)),"")')
        S(f'{s}_eb', f'  {title} segment EBITDA As Defined', 'line', 'm1', data=earn, flow=True,
          qe=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}', ae=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}',
          note='Segment EBITDA As Defined as reported (the measure the chief operating decision maker uses; segment note). Forecast = segment net sales × margin.' if s == 'pc' else None)
        S(f'{s}_m', '  Segment EBITDA As Defined margin %', 'pct', 'pct', all=ratio(f'{s}_eb', f'{s}_rev'),
          qe=lambda s=s: f'={P(s + "_m")}+{E("cal_m")}', ae=lambda s=s, code=code: '=' + CH(SC[f'{code}_M'][CTX.col.year]),
          note='Q1–Q4/27E: prior-year quarter margin + EBITDA As Defined guidance calibration Δ (Group block). 2028E+: scenario lever.' if s == 'pc' else None)
        S(f'{s}_inc', '  Incremental segment margin (Δ EBITDA As Defined / Δ net sales)', 'pct', 'pct', all=incr(f'{s}_eb', f'{s}_rev'))
        blank()
    S('na_hdr', 'Non-aviation (seat belts and safety restraints for ground transportation, mobile heat solutions, space, hoists and winches, other industrial)', 'block',
      note='NON-AVIATION — modelling logic')
    S('na_rev', '  Non-aviation — segment net sales', 'line_b', 'm1', data='sg_na_rev', flow=True,
      qe=lambda: f'={P("na_rev")}*(1+{V("na_rev_g")})', ae=lambda: f'={P("na_rev")}*(1+{V("na_rev_g")})')
    S('na_rev_g', '  Segment net sales y/y %', 'growth', 'pct', all=growth('na_rev'), qe=lambda: f'={PT("pt_na_g")}',
      ae=lambda: '=' + CH(SC['NA_G'][CTX.col.year]), note='Not guided. Q1–Q4/27E point estimate; 2028E+ scenario lever.')
    S('na_mix', '  % of total net sales', 'pct', 'pct', all=ratio('na_rev', 'g_rev'))
    S('na_eb', '  Non-aviation segment EBITDA As Defined', 'line', 'm1', data='sg_na_eb', flow=True,
      qe=lambda: f'={V("na_rev")}*{V("na_m")}', ae=lambda: f'={V("na_rev")}*{V("na_m")}')
    S('na_m', '  Segment EBITDA As Defined margin %', 'pct', 'pct', all=ratio('na_eb', 'na_rev'),
      qe=lambda: f'={P("na_m")}+{E("cal_m")}', ae_in=V0['na_m'], note='Q1–Q4/27E: prior-year quarter + calibration Δ; 2028E+ held at the input.')
    blank()
    S('co_hdr', 'Unallocated corporate (corporate-office compensation, benefits, professional services and administration)', 'block',
      note='CORPORATE — modelling logic')
    S('corp', '  Unallocated corporate EBITDA As Defined (cost, +)', 'line', 'm1', data='sg_corp', flow=True,
      qe=lambda: f'=({V("pc_rev")}+{V("af_rev")}+{V("na_rev")})*{V("corp_pct")}', ae=lambda: f'={V("g_rev")}*{V("corp_pct")}')
    S('corp_pct', '  Unallocated corporate % of net sales', 'pct', 'pct', all=ratio('corp', 'is_rev'), qe=lambda: f'={PT("pt_corp")}', ae_in=V0['corp_pct'],
      note='FY2026 1.07% of net sales (FY2024–25 1.3%). Point estimate FY27E; input 2028E+.')
    blank()
    S('mx_hdr', 'Net sales by end market — total (outputs)', 'block', note='MIX — outputs (end markets from FY2017; organic / acquisition split from FY2012)')
    for t, tl, _ in MKTS:
        S(f'mx_{t}', f'  {tl} (Power & Control + Airframe)', 'line', 'm1', all=lambda t=t: f'=IF(ISNUMBER({V("pc_" + t)}),{V("pc_" + t)}+{V("af_" + t)},"")')
    S('mx_aero', '  Total aerospace (commercial OEM + aftermarket + defense)', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("mx_coem")}),{V("mx_coem")}+{V("mx_caft")}+{V("mx_def")},"")')
    for t, tl, _ in MKTS:
        S(f'mx_{t}_p', f'  {tl} % of total net sales', 'pct', 'pct', all=lambda t=t: f'=IF(ISNUMBER({V("mx_" + t)}),IFERROR({V("mx_" + t)}/{V("g_rev")},""),"")')
    for t, tl, _ in MKTS:
        S(f'mx_{t}_g', f'  {tl} y/y % (incl. acquisitions)', 'growth', 'pct', all=growth(f'mx_{t}'))
    S('org_g', '  Organic sales growth % (company: organic sales / prior-year net sales − 1)', 'growth', 'pct',
      hist=lambda: (f'=IF(AND(ISNUMBER({V("org_sales")}),ISNUMBER({P("is_rev")})),IFERROR({V("org_sales")}/{P("is_rev")}-1,""),"")' if CTX.col.prior else None),
      fc=lambda: f'=IFERROR({V("g_rev")}/{P("g_rev")}-1-{V("acq_g")},"")',
      e27=lambda: f'=IFERROR({V("g_rev")}/{P("g_rev")}-1-{V("acq_g")},"")',
      note='Company definition: acquisition sales = sales of businesses owned less than twelve months (10-Q / 10-K MD&A, from FY2012; Q4 = fiscal year − three quarters, not derived for FY2017 / FY2019, whose 10-K tables are on the discontinued-operations basis).')
    S('acq_g', '  Contribution from acquisitions (acquisition sales / prior-year net sales)', 'growth', 'pct',
      hist=lambda: (f'=IF(AND(ISNUMBER({V("acq_sales")}),ISNUMBER({P("is_rev")})),IFERROR({V("acq_sales")}/{P("is_rev")},""),"")' if CTX.col.prior else None),
      fc=lambda: f'=IFERROR((N({V("pc_acq")})+N({V("m_rev")})-(1+N({V("m_g")}))*N({P("m_rev")}))/{P("g_rev")},"")',
      note='Forecast: FY27E inorganic sales input; 2028E+ revenue from future acquisitions in excess of the prior year\'s acquired base grown at the acquired-business growth rate (≈ sales owned under twelve months).',
      e27=lambda: f'=IFERROR(SUM({Q1}{R["pc_acq"]}:{QE4}{R["pc_acq"]})/{P("g_rev")},"")')
    S('org_chk', '  Check: organic + acquisitions vs reported net sales growth (should be 0)', 'check', 'pct',
      hist=lambda: (f'=IF(AND(ISNUMBER({V("org_g")}),ISNUMBER({V("acq_g")})),IF(ABS({V("org_g")}+{V("acq_g")}-({V("is_rev")}/{P("is_rev")}-1))<=0.0005,0,ROUND({V("org_g")}+{V("acq_g")}-({V("is_rev")}/{P("is_rev")}-1),4)),"")' if CTX.col.prior else None))
    S('org_sales', '  Memo: organic sales (company)', 'memo', 'm1', data='org_sales', flow=True)
    S('acq_sales', '  Memo: acquisition sales (company)', 'memo', 'm1', data='acq_sales', flow=True)
    for s, tl in (('pc', 'Power & Control'), ('af', 'Airframe'), ('na', 'Non-aviation')):
        S(f'gc_{s}', f'  Contribution to total net sales growth — {tl} (pp)', 'growth', 'pct',
          all=lambda s=s: (f'=IF(AND(ISNUMBER({V(s + "_rev")}),ISNUMBER({P(s + "_rev")})),IFERROR(({V(s + "_rev")}-{P(s + "_rev")})/{P("g_rev")},""),"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — unallocated; Extant asset purchase FY2027E; bolt-ons and platforms 2028E+)', 'block',
      note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention (2028E+)')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e27_in=V0['mna27'], ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=V0['m_mult'], e27_in=V0['m_mult'], note=V0['m_mult_note'])
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e27=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)',
      ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e27_in=0.0, ae_in=0.06)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e27=lambda: f'={V("m_acq_sales")}', ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e27_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}',
      note='Mid-year convention 2028E+. FY2027E: the Extant asset purchase (close timing in FY27 not disclosed, revenue not disclosed) contributes from FY2028E (assumption); FY27 guidance basis excludes it.')
    S('m_m', '  EBITDA As Defined margin of acquired businesses %', 'driver', 'pct', e27_in=0.0, ae_in=V0['m_m'],
      note='TransDigm targets ~50%+ margins after integration; recent deals were ~2 pp dilutive to the FY2026 margin (Q4 FY26 release). 2028E+: 40% (assumption).')
    S('m_eb', '  EBITDA As Defined from future acquisitions', 'line', 'm', e27_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e27_in=0.05, ae_in=0.05)
    S('m_intp', '  Amortizable intangibles % of spend', 'driver', 'pct', e27_in=0.35, ae_in=0.35,
      note='FY2026 deals: $1,965m of intangibles on $4,391m spent (45%), of which trade names $214m indefinite-lived (10-K Note 8) → ~40% amortizable; 35% input.')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e27_in=20, ae_in=20, note='TransDigm amortizes technology and customer relationships over 10–20 years (20 years for the FY2026 platform deals).')
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e27=lambda: f'={V("m_spend")}*{V("m_intp")}', ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles', 'line', 'm', e27_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)', note='FY2027E: nil (outside the 10-K amortization schedule and the guidance basis).')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group Total — net sales & EBITDA As Defined (segment build) → FY27 guidance calibration', 'block', note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_seg', '  Σ segment net sales (Power & Control + Airframe + Non-aviation)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("pc_rev")}),{V("pc_rev")}+{V("af_rev")}+N({V("na_rev")}),"")')
    S('g_basis', '  Consolidated net sales not on the segment basis (derived: FY2006–10 not split; recast segment periods vs as first reported)', 'line', 'm1',
      hist=lambda: f'={V("is_rev")}-N({V("g_seg")})', fc=lambda: '=0',
      note='FY2006–10: one reportable segment (no split). Recast periods: segment data from the following year\'s filing exclude businesses later presented as discontinued operations (FY2017, FY2019 Esterline) — difference to net sales as first reported. Forecast nil.')
    S('g_rev', 'Net sales (segment build)', 'total', 'm1',
      hist=lambda: f'=N({V("g_seg")})+{V("g_basis")}',
      fc=lambda: f'={V("g_seg")}+{V("g_basis")}+N({V("m_rev")})',
      note='Σ segments (+ basis row historically; + future acquisitions from 2028E).')
    S('g_rev_g', '  Net sales y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs consolidated net sales (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=0.15,0,ROUND({V("g_rev")}-{V("is_rev")},1)),"")')
    S('g_eb_seg', '  Σ segment EBITDA As Defined less unallocated corporate', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("pc_eb")}),{V("pc_eb")}+{V("af_eb")}+N({V("na_eb")})-N({V("corp")}),"")')
    S('g_eb_basis', '  EBITDA As Defined not on the segment basis (derived; as for net sales)', 'line', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_ad_pub")}),{V("r_ad_pub")}-N({V("g_eb_seg")}),"")', fc=lambda: '=0')
    S('g_eb', 'EBITDA As Defined (segment build)', 'total', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("g_eb_basis")}),N({V("g_eb_seg")})+{V("g_eb_basis")},"")',
      fc=lambda: f'={V("g_eb_seg")}+{V("g_eb_basis")}+N({V("m_eb")})',
      note="Σ segment EBITDA As Defined − unallocated corporate (+ future acquisitions). TransDigm's EBITDA As Defined (company definition); drives the GAAP P&L below.")
    S('g_ebm', '  EBITDA As Defined margin %', 'pct', 'pct', all=ratio('g_eb', 'is_rev'))
    S('g_eb_g', '  EBITDA As Defined y/y %', 'growth', 'pct', all=growth('g_eb'))
    S('g_chk_eb', '  Check: segment build vs EBITDA As Defined bridge (should be 0; ±1 from FY2020 rounding)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_eb")}),ISNUMBER({V("r_ad")})),IF(ABS({V("g_eb")}-{V("r_ad")})<={0.15 if CTX.col.year <= 2019 else 1.01},0,ROUND({V("g_eb")}-{V("r_ad")},1)),"")')
    # calibration
    S('cal_guid', '  Memo: FY27 net sales guidance (scenario end-point; excludes future acquisitions)', 'memo', 'm1', e27=lambda: '=' + CH(SC['out_sales']), note=V0['rev_guid_note'])
    S('cal_pre', '  Net sales before calibration (FY27E quarter helper)', 'line', 'm1',
      qe=lambda: '=' + '+'.join(f'{P(k)}*(1+{CH(SC["out_" + k.split("_")[1]])})' for k in LINES) + f'+{V("pc_acq")}+{V("na_rev")}+{V("g_basis")}')
    S('cal_sens', '  Net sales sensitivity to +1.00 of market growth (FY27E quarter helper)', 'line', 'm1', qe=lambda: '=' + '+'.join(P(k) for k in LINES))
    S('cal_g', '  Guidance calibration: Δ y/y growth applied to all six aerospace end-market lines (FY27E)', 'driver', 'pct',
      e27=lambda: f'=({V("cal_guid")}-{QSUM("cal_pre")})/{QSUM("cal_sens")}',
      note='Solves the uniform shift to the guided market growth rates so that FY27 net sales = the guidance end-point for the active scenario (closed form; no circularity).')
    S('cal_rev_chk', '  Check: FY27 net sales vs guidance end-point (should be 0)', 'check', 'm1', e27=lambda: f'=ROUND({V("g_rev")}-{V("cal_guid")},1)')
    S('cal_ebt', '  Memo: FY27 EBITDA As Defined guidance (scenario end-point)', 'memo', 'm1', e27=lambda: '=' + CH(SC['out_ebitda']), note=V0['eb_guid_note'])
    S('cal_eb_pre', '  EBITDA As Defined before margin calibration (FY27E quarter helper)', 'line', 'm1',
      qe=lambda: '=' + '+'.join(f'{V(s + "_rev")}*{P(s + "_m")}' for s in SEGK) + f'-{V("corp")}+{V("g_eb_basis")}')
    S('cal_eb_sens', '  Segment net sales (FY27E quarter helper)', 'line', 'm1', qe=lambda: '=' + '+'.join(V(s + '_rev') for s in SEGK))
    S('cal_m', '  Guidance calibration: Δ segment EBITDA As Defined margin (all segments, FY27E)', 'driver', 'pct',
      e27=lambda: f'=({V("cal_ebt")}-{QSUM("cal_eb_pre")})/{QSUM("cal_eb_sens")}',
      note='Solves the uniform shift to prior-year quarter segment margins so that FY27 EBITDA As Defined = the guidance end-point (absorbs the ~2 pp acquisition dilution).')
    S('cal_eb_chk', '  Check: FY27 EBITDA As Defined vs guidance end-point (should be 0)', 'check', 'm1', e27=lambda: f'=ROUND({V("g_eb")}-{V("cal_ebt")},1)')
    S('cal_aeps', '  Memo: FY27 adjusted EPS guidance (scenario end-point, $) — information, not forced', 'eps_memo', 'ps', e27=lambda: '=' + CH(SC['out_adjeps']))
    S('cal_aeps_d', '    Model adjusted EPS − guidance ($; model includes the FY27 buyback input)', 'memo_calc', 'ps', e27=lambda: f'={V("e_eps")}-{V("cal_aeps")}')
    S('cal_eps', '  Memo: FY27 GAAP EPS guidance (scenario end-point, $) — information', 'eps_memo', 'ps', e27=lambda: '=' + CH(SC['out_eps']))
    S('cal_eps_d', '    Model GAAP EPS − guidance ($)', 'memo_calc', 'ps', e27=lambda: f'={V("eps_d")}-{V("cal_eps")}')
    S('cal_ni', '  Memo: FY27 net income guidance (scenario end-point) — information', 'memo', 'm1', e27=lambda: '=' + CH(SC['out_ni']))
    S('cal_ni_d', '    Model net income − guidance', 'memo_calc', 'm1', e27=lambda: f'={V("is_ni")}-{V("cal_ni")}')
    for t, tl, mk in MKTS:
        S(f'cal_{t}_d', f'    Model FY27 {tl.lower()} growth (ex inorganic) − guided market growth (pp)', 'memo_calc', 'pct',
          e27=lambda t=t, mk=mk: f'=IFERROR(({V("mx_" + t)}-SUMPRODUCT({Q1}{R["pc_acq"]}:{QE4}{R["pc_acq"]},{Q1}{R["pc_al_" + t]}:{QE4}{R["pc_al_" + t]}))/{P("mx_" + t)}-1-{CH(SC["out_" + mk.lower()])},"")')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A & adjusting items', 'block', note='COST DRIVERS — inputs that drive forecast cost lines (FY27E quarters: guidance-midpoint point estimates ÷ 4; 2028E+: % of sales or schedules)')
    S('d_dda', '  Depreciation & amortization (total; EBITDA reconciliation)', 'line', 'm1', data='d_dda', flow=True,
      fc=lambda: f'={V("d_dep")}+{V("d_amort")}', note='Release EBITDA reconciliations ("depreciation and amortization expense"). FY27E guidance midpoint $525m.')
    S('d_amort', '  Amortization of intangible assets (income-statement line)', 'line', 'm1', data='amort_is', flow=True,
      qe=lambda: f'={PT("pt_amort")}', ae=lambda: f'={V("d_amort_sch")}+N({V("m_amort")})',
      note='FY27E: 10-K estimated amortization ($294m) ÷ 4. 2028E+: 10-K schedule for intangibles held at 30-Sep-2026 + future-acquisition amortization.')
    S('d_amort_sch', '  Amortization schedule — intangibles held at 30-Sep-2026 (FY2026 10-K, input)', 'driver', 'm1', ae_in=V0['amort_sched'], note=V0['amort_note'])
    S('d_dep', '  Depreciation & other amortization (derived: total D&A − intangible amortization)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("d_dda")}),{V("d_dda")}-{V("d_amort")},"")', qe=lambda: f'={PT("pt_dep")}', ae=lambda: f'={V("is_rev")}*{V("d_dep_pct")}',
      note='Includes amortization of product certification costs and finance-lease assets. FY27E: guided D&A $525m − $294m intangible amortization, ÷ 4.')
    S('d_dep_pct', '  Depreciation & other amortization % of net sales', 'pct', 'pct', all=ratio('d_dep', 'is_rev'), ae_in=V0['dep_pct'])
    S('d_sga', '  Selling & administrative expenses % of net sales', 'pct', 'pct', all=ratio('is_sga', 'is_rev'), qe=lambda: f'={P("d_sga")}', ae_in=V0['sga_pct'],
      note='FY27E quarters: prior-year quarter ratio; 2028E+ input. Gross profit is implied: income from operations + S&A + amortization (cost of sales the balancing line).')
    S('d_adj_h', '  Adjusting items (pre-tax, added back in EBITDA As Defined; forecast inputs):', 'sub', 'gen')
    for k, lab, dk in ITEMS:
        kw = dict(data=dk, flow=True, labkey=dk + '_lab')
        if k == 'acq': kw.update(qe=lambda: f'={PT("pt_acq")}', ae=lambda: f'={V("m_spend")}*{V("d_acq_pct")}+{V("d_acq_base")}', note='FY27E: guidance midpoint $42m ÷ 4. 2028E+: % of acquisition spend + integration run-rate.')
        elif k == 'sbc': kw.update(qe=lambda: f'={PT("pt_sbc")}', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}', note='FY27E: guidance midpoint $225m ÷ 4 (FY26 $158m). 2028E+: % of net sales.')
        elif k == 'oadj': kw.update(qe=lambda: f'={PT("pt_other")}', ae_in=0.0, note='FY27E: guidance midpoint $16m ÷ 4. 2028E+: nil (assumption).')
        else: kw.update(fc=lambda: '=0')
        S('d_' + k, f'  {lab}', 'line', 'm1', **kw)
    S('d_acq_pct', '  Acquisition & integration costs % of acquisition spend', 'pct', 'pct', ae_in=0.025, note='FY2026: $101m on $4.4bn of acquisitions (2.3%).')
    S('d_acq_base', '  Acquisition & integration costs — run-rate excluding new deals ($m)', 'driver', 'm1', ae_in=15.0)
    S('d_sbc_pct', '  Non-cash stock & deferred compensation % of net sales', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_backlog', '  Purchase-accounting backlog amortization (inside intangible amortization; added back in adjusted net income)', 'line', 'm1', data='adj_backlog', flow=True,
      qe=lambda: f'={PT("pt_backlog")}', ae_in=V0['backlog_ae'], note='FY27E: P&I backlog $12m (1-year life) + other recent deals (assumption $16m); 2028E $4m, nil thereafter.')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF INCOME (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (EBITDA As Defined from the build − adjusting items − D&A = EBIT; − interest = pre-tax income; gross profit implied)')
    S('is_rev', 'Net sales', 'total', 'm1', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the segment build.')
    S('is_cogs', 'Cost of sales', 'line', 'm1', data='cogs', flow=True, fc=lambda: f'={V("is_rev")}-{V("is_gp")}')
    S('is_gp', 'Gross profit', 'line_b', 'm1', hist=lambda: f'={V("is_rev")}-{V("is_cogs")}',
      fc=lambda: f'={V("is_oi")}+{V("is_sga")}+{V("is_amort")}+{V("is_othop")}', note='Forecast = income from operations + S&A + amortization (implied by the EBITDA As Defined build).')
    S('is_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('is_sga', 'Selling and administrative expenses', 'line', 'm1', data='sga', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_sga")}')
    S('is_amort', 'Amortization of intangible assets', 'line', 'm1', data='amort_is', flow=True, fc=lambda: f'={V("d_amort")}')
    S('is_othop', 'Other operating items shown separately (FY2006 refinancing costs)', 'line', 'm1', data='oth_op', flow=True, fc=lambda: '=0', labkey='oth_op_labels')
    S('is_oi', 'Income from operations', 'total', 'm1',
      hist=lambda: f'={V("is_gp")}-N({V("is_sga")})-{V("is_amort")}-{V("is_othop")}',
      fc=lambda: f'={V("is_ebit")}+{V("is_refin")}+{V("is_othexp")}',
      note='Forecast = EBIT + refinancing costs + other expense (both below income from operations).')
    S('is_oi_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('is_int', 'Interest expense — net', 'line', 'm1', data='int_net', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_rev")}*{V("ds_r_rev")}-{P("cf_end")}*{V("ds_r_cash")}',
      note='Net of interest income; includes amortization of debt issuance costs / discount. FY27E: guidance midpoint $2,255m ÷ 4. 2028E+ = rate × opening debt − yield × opening cash (no circularity).')
    S('is_refin', 'Refinancing costs', 'line', 'm1', data='refin', flow=True, fc=lambda: f'={V("d_refin")}')
    S('is_othexp', 'Other expense (income), incl. gain on sale of businesses', 'line', 'm1', data='oth_exp', flow=True, fc=lambda: '=0',
      note='Forecast nil: the FY27E "Other, net" adjusting item is assumed to sit in S&A (assumption).')
    S('is_ebt', 'Income from continuing operations before income taxes', 'line_b', 'm1',
      hist=lambda: f'={V("is_oi")}-{V("is_int")}-{V("is_refin")}-{V("is_othexp")}', fc=lambda: f'={V("is_ebit")}-{V("is_int")}')
    S('is_tax', 'Income tax provision', 'line', 'm1', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='FY27E: guidance midpoint tax $741m on pre-tax income $3,207m (23.1%). FY2018 includes the US tax reform benefit. 2028E+: input.')
    S('is_cont', 'Income from continuing operations (incl. noncontrolling interests)', 'line_b', 'm1', all=lambda: f'={V("is_ebt")}-{V("is_tax")}')
    S('is_disc', 'Income (loss) from discontinued operations, net of tax', 'line', 'm1', data='disc', flow=True, fc=lambda: '=0',
      note='FY2011: fastener business and AQS (acquired with McKechnie, sold in FY2011); FY2017–18: SCHROTH; FY2019–20: Esterline businesses sold (incl. Souriau-Sunbank, Dec-2019).')
    S('is_ni', 'Net income', 'total', 'm1', all=lambda: f'={V("is_cont")}+{V("is_disc")}')
    S('is_ni_chk', '  Check: net income vs reported (should be 0; ±0.15 to FY2019, ±1 from FY2020 rounding)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<={0.15 if CTX.col.year <= 2019 else 1.01},0,ROUND({V("is_ni")}-{V("is_ni_pub")},1)),"")')
    S('is_ni_pub', '  Memo: net income as reported', 'memo', 'm1', data='ni', flow=True)
    S('is_nci', '  Less: net income attributable to noncontrolling interests', 'line', 'm1', data='nci', flow=True, qe=lambda: f'={PT("pt_nci")}', ae_in=V0['nci_ae'],
      note='Redeemable NCI in JPE / VSA (5% / 4%) and P&I (1%) from FY2026.')
    S('is_ni_td', 'Net income attributable to TD Group', 'line_b', 'm1', all=lambda: f'={V("is_ni")}-{V("is_nci")}')
    S('is_divp', '  Less: dividends paid on participating securities (dividend-equivalent payments on vested options; two-class method)', 'line', 'm1',
      data='div_part', flow=True, qe_in={1: V0['divq1'], 2: 0.0, 3: 0.0, 4: 0.0},
      ae=lambda: f'=-{V("cf_div")}*{V("ds_partp")}',
      note='Q1/27E: dividend-equivalent payments of $54m accrued at 30-Sep-2026 (FY2026 10-K Note 9; guidance $0.95 per share). 2028E+: participating share of special dividends.')
    S('is_ni_c', 'Net income applicable to TD Group common stockholders', 'line_b', 'm1', all=lambda: f'={V("is_ni_td")}-{V("is_divp")}')
    S('is_dda', '  Memo: depreciation & amortization (total)', 'memo_calc', 'm1', all=lambda: f'={V("d_dda")}')
    S('is_sbc', '  Memo: non-cash stock & deferred compensation', 'memo_calc', 'm1', all=lambda: f'={V("d_sbc")}')
    S('is_ebit', '  Memo: EBIT (pre-tax income + interest = EBITDA − D&A)', 'memo_calc', 'm1',
      hist=lambda: f'={V("is_ebt")}+{V("is_int")}', fc=lambda: f'={V("g_eb")}-{V("o_tot")}-{V("d_dda")}')
    S('eps_hdr', '(Earnings per share — two-class method: common shares + vested options deemed participating securities)', 'sub', 'gen')
    S('sh_d', '  Weighted-average shares outstanding — basic and diluted (two-class, m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={LQ}{R["sh_d"]}-{E("bb_sh")}*{QF()}+{E("bb_iss")}*{QF()}',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})+{V("ds_part")}',
      note='FY2006–09: diluted shares (treasury-stock method). Two-class method from FY2010. FY27E: Q4/26 shares − FY27 buybacks + option exercises, mid-quarter weighted; guidance 56.7m. 2028E+: average common shares + participating options.')
    S('eps_d', 'EPS — basic and diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_d")}),IFERROR({V("is_ni_c")}/{V("sh_d")},""),"")',
      note='Net income applicable to common stockholders / two-class shares (FY2006–09: net income / diluted shares).')
    S('eps_d_g', '  EPS y/y %', 'growth', 'pct', all=growth('eps_d'))
    S('eps_pub', '  Memo: EPS as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported EPS (should be 0.00; ±0.01 to FY2019, ±0.06 from FY2020: shares published to 0.1m)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_d")})),IF(ABS({V("eps_d")}-{V("eps_pub")})<={0.0101 if CTX.col.year <= 2019 else 0.0601},0,ROUND({V("eps_d")}-{V("eps_pub")},2)),"n/p")')
    S('dps', '  Special cash dividends declared / paid per common share ($)', 'line', 'ps', data='dps', flow=True, qe_in=0.0, e27_in=0.0,
      ae=lambda: f'=IFERROR(-{V("cf_div")}*(1-{V("ds_partp")})/{V("bb_beg")},0)', note='No regular dividend. 2028E+: special dividends from the capital-return plug (scenario split).')
    blank()

    # ------------------------------------------------------------------ RECON 1: net income -> EBITDA -> EBITDA As Defined
    S('sec_r1', 'RECONCILIATION: NET INCOME → EBITDA → EBITDA AS DEFINED (company definitions, as published)', 'section',
      note='EBITDA AS DEFINED — per the release "Reconciliation of EBITDA, EBITDA As Defined to Net Income"; company item labels in the cell comments of the adjusting-item rows')
    S('r_ni', 'Net income', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('r_dsc', '  (−) Income from discontinued operations', 'line', 'm1', all=lambda: f'=-{V("is_disc")}')
    S('r_tax', '  (+) Income tax provision', 'line', 'm1', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest expense — net', 'line', 'm1', all=lambda: f'={V("is_int")}')
    S('r_dda', '  (+) Depreciation & amortization', 'line', 'm1', all=lambda: f'={V("d_dda")}')
    S('r_ebitda', '  = EBITDA (continuing operations)', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_dda")}),{V("r_ni")}+{V("r_dsc")}+{V("r_tax")}+{V("r_int")}+{V("r_dda")},"")')
    S('r_ebitda_pub', '  Company-published EBITDA', 'memo', 'm1', data='ebitda_pub', flow=True)
    S('r_ebitda_chk', '  Check: model vs company-published EBITDA (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda_pub")}),ISNUMBER({V("r_ebitda")})),IF(ABS({V("r_ebitda")}-{V("r_ebitda_pub")})<={0.15 if CTX.col.year <= 2019 else 1.01},0,ROUND({V("r_ebitda")}-{V("r_ebitda_pub")},1)),"n/p")')
    for k, lab, _ in ITEMS:
        S('r_' + k, f'  (+) {lab}', 'line', 'm1', all=lambda k=k: f'={V("d_" + k)}')
    S('o_tot', '  Gross adjustments to EBITDA (pre-tax)', 'line_b', 'm1', all=lambda: '=' + nsum(['r_' + k for k, _, _ in ITEMS]))
    S('r_ad', '  = EBITDA As Defined (model bridge)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{V("r_ebitda")}+{V("o_tot")},"")',
      note='Company definition (FY2006–07 "EBITDA As Defined" before the IPO-related items shown separately; definition flags in the row below). Used for leverage (net debt / EBITDA As Defined) and EV / EBITDA.')
    S('r_ad_m', '  EBITDA As Defined margin %', 'pct', 'pct', all=ratio('r_ad', 'is_rev'))
    S('r_ad_pub', '  Company-published EBITDA As Defined', 'memo', 'm1', data='ebitda_ad_pub', flow=True)
    S('r_chk', '  Check: model vs company-published EBITDA As Defined (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("r_ad_pub")}),ISNUMBER({V("r_ad")})),IF(ABS({V("r_ad")}-{V("r_ad_pub")})<={0.15 if CTX.col.year <= 2019 else 1.01},0,ROUND({V("r_ad")}-{V("r_ad_pub")},1)),"n/p")')
    S('r_def', '  Definition / basis (company EBITDA As Defined in force)', 'text', 'gen', note='Changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('r_ad_g', '  EBITDA As Defined y/y %', 'growth', 'pct', all=growth('r_ad'))
    S('r_inc', '  Incremental EBITDA As Defined margin (Δ EBITDA As Defined / Δ net sales)', 'pct', 'pct', all=incr('r_ad', 'is_rev'))
    S('r_ebit_h', 'To adjusted EBIT, full-cost (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ddan', '  (−) Depreciation & amortization (total)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("d_dda")}),-{V("d_dda")},"")')
    S('r_ebit', '  = Adjusted EBIT, full-cost (EBITDA As Defined − total D&A; model measure)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_ad")}),{V("r_ad")}+{V("r_ddan")},"")',
      note='Model measure (TransDigm publishes no adjusted EBIT): charges all D&A incl. acquired-intangible amortization; excludes stock compensation and acquisition costs (deducted again in the DCF).')
    S('r_ebit_m', '  Adjusted EBIT (full-cost) margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: stock compensation + acquisition, integration & restructuring costs (excluded by the company; deducted in DCF NOPAT)', 'memo_calc', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_acq")}),{V("r_acq")}+{V("r_sbc")}+{V("r_restr")},"")')
    blank()

    # ------------------------------------------------------------------ RECON 2: adjusted net income / EPS
    S('sec_r3', 'RECONCILIATION: NET INCOME → ADJUSTED NET INCOME → ADJUSTED EPS (company definition, two-class method)', 'section',
      note='ADJUSTED EPS — income from continuing operations + gross adjustments to EBITDA + purchase-accounting backlog amortization + tax adjustment = adjusted net income; ÷ two-class shares (dividend-equivalent payments are not deducted)')
    S('e_cont', 'Income from continuing operations (incl. noncontrolling interests)', 'line_b', 'm1', all=lambda: f'={V("is_cont")}')
    S('e_sdiff', '  (±) Company start-line difference (start from income attributable to TD Group; derived)', 'line', 'm1', data='adj_start_diff', flow=True, fc=lambda: '=0',
      note='Most periods start from net income incl. NCI (or continuing operations); Q1 FY2020–Q4 FY2020 start from income attributable to TD Group.')
    S('e_gross', '  (+) Gross adjustments to EBITDA (bridge above)', 'line', 'm1', all=lambda: f'={V("o_tot")}')
    S('e_backlog', '  (+) Purchase-accounting backlog amortization', 'line', 'm1', all=lambda: f'={V("d_backlog")}')
    S('e_tax', '  (−) Tax adjustment (tax effect of the adjustments; excess tax benefits on option exercises excluded)', 'line', 'm1', data='adj_tax', flow=True,
      fc=lambda: f'=-({V("e_gross")}+{V("e_backlog")})*{V("e_rate")}',
      note='Historical: as published. Forecast: (gross adjustments + backlog amortization) × tax rate (FY27E guidance per-share items imply ~23%).')
    S('e_adjni', '  = Adjusted net income (model bridge)', 'total', 'm1', all=lambda: f'={V("e_cont")}+N({V("e_sdiff")})+{V("e_gross")}+{V("e_backlog")}+N({V("e_tax")})')
    S('e_pubni', '  Company-published adjusted net income', 'memo', 'm1', data='adj_ni_pub', flow=True)
    S('e_chk_ni', '  Check: model vs company-published adjusted net income (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("e_pubni")}),IF(ABS({V("e_adjni")}-{V("e_pubni")})<={0.3 if CTX.col.year <= 2019 else 2.01},0,ROUND({V("e_adjni")}-{V("e_pubni")},1)),"n/p")')
    S('e_sh', '  Shares for adjusted EPS (two-class, adjusted basis, m)', 'line', 'm1', data='sh_adj', avg=True, fc=lambda: f'={V("sh_d")}',
      note='Company total shares under the two-class method (in loss-to-common periods the adjusted basis includes the participating options, e.g. Q1 FY2021 58.4m vs 54.7m GAAP).')
    S('e_eps', 'Adjusted EPS ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted EPS ($)', 'eps_memo', 'ps', data='adj_eps_pub')
    S('e_chk', '  Check: model vs company-published adjusted EPS (should be 0.00; ±0.01 to FY2019, ±0.06 from FY2020: shares to 0.1m)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<={0.0101 if CTX.col.year <= 2019 else 0.0601},0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_divx', '  Memo: EPS effect of including dividend-equivalent payments ($, company per-share bridge)', 'eps_memo', 'ps', data='eps_div_equiv')
    S('e_rate', '  Tax rate on adjustments (tax adjustment / (gross adjustments + backlog amortization))', 'pct', 'pct',
      hist=lambda: f'=IFERROR(-{V("e_tax")}/({V("e_gross")}+{V("e_backlog")}),"")', fc=lambda: f'={V("is_etr")}')
    S('e_def', '  Definition / basis (company adjusted EPS definition)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Net sales y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_pc', '  Power & Control net sales y/y %', 'growth', 'pct', all=growth('pc_rev'))
    S('gm_af', '  Airframe net sales y/y %', 'growth', 'pct', all=growth('af_rev'))
    S('gm_ebitda', '  EBITDA As Defined y/y %', 'growth', 'pct', all=growth('r_ad'))
    S('gm_op', '  Income from operations y/y %', 'growth', 'pct', all=growth('is_oi'))
    S('gm_ni', '  Net income y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('gm_ebitda_m', '  EBITDA As Defined margin %', 'pct', 'pct', all=ratio('r_ad', 'is_rev'))
    S('gm_inc', '  Incremental EBITDA As Defined margin', 'pct', 'pct', all=incr('r_ad', 'is_rev'))
    S('gm_op_m', '  Operating margin (income from operations) %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_sga', '  S&A % of net sales', 'pct', 'pct', all=ratio('is_sga', 'is_rev'))
    S('gm_int', '  Interest expense — net % of EBITDA As Defined', 'pct', 'pct', all=ratio('is_int', 'r_ad'))
    blank()
