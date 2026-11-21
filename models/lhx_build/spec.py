"""Row specification of the LHX Model sheet, part 1 (MLM template layout and process):
segment build (Space & Mission Systems / Communications & Spectrum Dominance / Missile Solutions: revenue x segment operating
margin) -> segment operating income (company measure) -> unallocated corporate items -> operating income; legacy segment
structures as memo rows; orders / backlog; future M&A lever; group total & FY26 guidance calibration; cost drivers; income
statement; GAAP-to-adjusted bridges; growth & margins."""
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
        return f'=IF(AND(ISNUMBER({V(n)}),ISNUMBER({P(n)})),IFERROR(({V(n)}-{P(n)})/({V(d)}-{P(d)}),""),"")'
    return f
def nsum(keys): return '+'.join(f'N({V(k)})' for k in keys)
def QEa(key): return f'${QE}${R[key]}'                    # Q4/26E (absolute)
def QEc(key): return f'{QE}{R[key]}'                      # Q4/26E
def ACT(key): return f'SUM({Q1}{R[key]}:{Q3}{R[key]})'    # 9M 2026 actual (Q1-Q3/26)
def ACT0(key): return f'SUM({PQ1}{R[key]}:{PQ3}{R[key]})' # 9M 2025 actual (Q1-Q3/25)
def B1(key): return f'{LQ}{R[key]}'                       # 2-Oct-2026 balance
def tol(a, b, t=0.6, nd=0, blank='""'):
    """check formula: 0 when |a - b| <= t (source rounding), else the rounded difference."""
    return f'IF(ABS({a}-({b}))<={t},0,ROUND({a}-({b}),{nd}))'

SEG = [('sms', 'Space & Mission Systems', 'SMS'), ('csd', 'Communications & Spectrum Dominance', 'CSD'), ('ms', 'Missile Solutions', 'MS')]
SEGK = [s for s, _, _ in SEG]
# legacy segment structures (as originally reported), memo rows: code, label
LEG = [('rf', 'RF Communications (Harris, to FY2015)'), ('ins', 'Integrated Network Solutions (Harris, to FY2015)'), ('gcs', 'Government Communications Systems (Harris, to FY2015)'),
       ('cn', 'Critical Networks (Harris, FY2016)'), ('cs', 'Communication Systems (Harris FY2016–19; L3Harris 2H19–2025)'), ('sis', 'Space and Intelligence Systems (Harris, FY2016–19)'),
       ('es', 'Electronic Systems (Harris, FY2016–19)'), ('ims', 'Integrated Mission Systems (2H19–2025)'), ('sas', 'Space & Airborne Systems (2H19–2025)'),
       ('avs', 'Aviation Systems (2H19–2021)'), ('ar', 'Aerojet Rocketdyne (from 28-Jul-2023 to 2025)')]
CORP = ['c_amort', 'c_fascas', 'c_restr', 'c_acq', 'c_gain', 'c_impair', 'c_other']
AOP = ['a_restr', 'a_acq', 'a_gain', 'a_impair', 'a_oth']

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of the FY26 guidance ranges.'))
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
    SCEN_ROWS.append((r, 'lev', '  Maximum net debt / adjusted EBITDA before buybacks (x) — buyback floor 2027E+', *V0['lev'], V0['lev_note']))
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
    cur = lambda: f'ISNUMBER({V("sms_rev")})'            # column is on the current three-segment basis
    # ------------------------------------------------------------------ SEGMENT BUILD
    S('sec_seg', 'SEGMENT P&L — SPACE & MISSION SYSTEMS · COMMUNICATIONS & SPECTRUM DOMINANCE · MISSILE SOLUTIONS (revenue × segment operating margin)', 'section',
      note='SEGMENT BUILD — modelling logic (segment revenue → segment operating income at the segment margin → − unallocated corporate items = operating income → GAAP P&L)')
    blank()
    descr = {'sms': 'Space & Mission Systems (space payloads & satellites, missionized ISR aircraft, airborne / maritime systems, mission networks incl. FAA, intel & cyber)',
             'csd': 'Communications & Spectrum Dominance (tactical radios / resilient communications, night vision, electronic warfare / spectrum superiority, targeting & sensor systems)',
             'ms': 'Missile Solutions (Aerojet Rocketdyne: solid rocket motors & missile propulsion, advanced effects, RS-25 / hypersonics; subsidiary preferred stock held by the DoW)'}
    for s, title, code in SEG:
        first = s == 'sms'
        S(f'{s}_hdr', descr[s], 'block', note=f'{title.upper()} — modelling logic')
        S(f'{s}_rev', f'  {title} — segment revenue', 'line_b', 'm', data=f'sr_{s}', flow=True,
          qe=lambda s=s: f'={V(s + "_pre")}*(1+{QEa("cal_g")})', ae=lambda s=s: f'={P(s + "_rev")}*(1+{V(s + "_rev_g")})',
          note=('Segment revenue incl. intersegment sales, on the three-segment structure effective Q1-26 (history recast by the company for 2025 only; earlier periods are in the legacy memo rows). '
                'Q4/26E: (FY26 segment revenue guidance − 9M actual) × (1 + revenue-guidance calibration Δ). 2027E+: prior year × (1 + scenario growth).') if first else None)
        S(f'{s}_rev_g', '    y/y %', 'growth', 'pct', all=growth(f'{s}_rev'),
          ae=lambda code=code: '=' + CH(SC[f'{code}_G'][CTX.col.year]),
          note='2027E–2031E: scenario lever (Bull/Base/Bear table →).' if first else None)
        S(f'{s}_pre', '    Q4/26E revenue before calibration (FY26 segment guidance − 9M actual)', 'driver', 'm',
          qe=lambda s=s: f'={PT("pt_rev_" + s)}-{ACT(s + "_rev")}')
        S(f'{s}_mix', '  % of segment revenue', 'pct', 'pct', all=lambda s=s: f'=IF({cur()},IFERROR({V(s + "_rev")}/{V("seg_rev")},""),"")')
        S(f'{s}_oi', f'  {title} — segment operating income', 'line', 'm', data=f'so_{s}', flow=True,
          qe=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}', ae=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}',
          note=('Segment operating income as reported (company measure: excludes unallocated corporate items — amortization of acquisition-related intangibles, divestiture / transaction items, '
                'deferred-compensation fair-value changes and other corporate costs). Forecast = segment revenue × segment margin.') if first else None)
        S(f'{s}_m', '  Segment operating margin %', 'pct', 'pct', all=ratio(f'{s}_oi', f'{s}_rev'),
          qe=lambda s=s: f'={V(s + "_m_pre")}+{QEa("cal_m")}', ae=lambda code=code: '=' + CH(SC[f'{code}_M'][CTX.col.year]),
          note='Q4/26E: guidance-implied margin + EPS-guidance calibration Δ (Group block). 2027E+: scenario lever.' if first else None)
        S(f'{s}_m_pre', '  Q4/26E margin before EPS calibration ((FY26 margin guidance × revenue guidance − 9M operating income) ÷ Q4 revenue before calibration)', 'driver', 'pct',
          qe=lambda s=s: f'=IFERROR(({PT("pt_m_" + s)}*{PT("pt_rev_" + s)}-{ACT(s + "_oi")})/{V(s + "_pre")},0)')
        S(f'{s}_inc', '  Incremental segment margin (Δ operating income / Δ revenue)', 'pct', 'pct', all=incr(f'{s}_oi', f'{s}_rev'))
        S(f'{s}_bk', '  Memo: contractual backlog at period end ($m; published in $bn to one decimal)', 'memo', 'm', data=f'bk_{s}', bs=True)
        S(f'{s}_b2b', '  Memo: book-to-bill (x)', 'memo', 'x2', data=f'b2b_{s}')
        blank()
    S('seg_hdr', 'Total segments (company non-GAAP measures "segment revenue" and "segment operating income")', 'block',
      note='TOTAL SEGMENTS — Σ segments + intersegment eliminations; periods before 2025 carry the totals of the legacy structures (memo block below)')
    S('seg_inter', '  Intersegment revenue (eliminations)', 'line', 'm', data='sr_inter', flow=True, qe=lambda: f'={PT("pt_inter")}',
      ae=lambda: f'={V("seg_inter_p")}*({"+".join(V(s + "_rev") for s in SEGK)})')
    S('seg_inter_p', '    Intersegment % of Σ segment revenue', 'pct', 'pct2',
      all=lambda: f'=IF({cur()},IFERROR({V("seg_inter")}/({"+".join(V(s + "_rev") for s in SEGK)}),""),"")', ae=lambda: f'={V("seg_inter_p", E26)}')
    S('seg_rev', 'Segment revenue (Σ segments + intersegment)', 'total', 'm', flow=True,
      hist=lambda: f'=IF({cur()},{"+".join(V(s + "_rev") for s in SEGK)}+{V("seg_inter")},IF(ISNUMBER({V("leg_rev")}),{V("leg_rev")},""))',
      fc=lambda: f'={"+".join(V(s + "_rev") for s in SEGK)}+{V("seg_inter")}',
      note='History before 2025: total of the segments in force in each period (legacy memo block), as originally reported.')
    S('seg_rev_g', '  Segment revenue y/y %', 'growth', 'pct', all=growth('seg_rev'))
    S('seg_other', '  Other revenue outside the segments (corporate / divested non-reportable businesses; program investment asset amortization from Q3-26)', 'line', 'm',
      data='sr_other', flow=True, qe=lambda: f'={PT("pt_other")}', ae_in=V0['other_rev'], note=V0['other_rev_note'])
    S('seg_oi', 'Segment operating income (Σ segments)', 'total', 'm', flow=True,
      hist=lambda: f'=IF({cur()},{"+".join(V(s + "_oi") for s in SEGK)},IF(ISNUMBER({V("leg_oi")}),{V("leg_oi")},""))',
      fc=lambda: f'={"+".join(V(s + "_oi") for s in SEGK)}+N({V("m_oi")})',
      note='Company measure in force in each period (definition row in the reconciliation section). Forecast: Σ segment revenue × margin (+ future acquisitions).')
    S('seg_m', '  Segment operating margin % (on segment revenue)', 'pct', 'pct', all=ratio('seg_oi', 'seg_rev'))
    S('seg_oi_g', '  Segment operating income y/y %', 'growth', 'pct', all=growth('seg_oi'))
    S('seg_inc', '  Incremental segment margin (Δ segment operating income / Δ segment revenue)', 'pct', 'pct', all=incr('seg_oi', 'seg_rev'))
    S('seg_pub', '  Memo: segment operating income as published (company total)', 'memo', 'm', data='seg_oi_pub', flow=True)
    S('seg_chk', '  Check: Σ segments vs published segment operating income (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("seg_pub")}),ISNUMBER({V("seg_oi")})),{tol(V("seg_oi"), V("seg_pub"), 1.01)},"")')
    blank()
    S('leg_hdr', 'Legacy segment structures — as originally reported in each period (memo; not comparable across restructurings)', 'block',
      note='LEGACY SEGMENTS — Harris segments to FY2019; L3Harris four segments 2H19–2021 (Aviation Systems dissolved 2022); Aerojet Rocketdyne added Jul-2023; three new segments from Q1-26')
    S('leg_r_h', '  Segment revenue:', 'sub', 'gen')
    for k, lab in LEG:
        S(f'lr_{k}', f'    {lab}', 'memo', 'm', data=f'lr_{k}', flow=True)
    S('lr_elim', '    Intersegment eliminations / other inside the segment total', 'memo', 'm', data='lr_elim', flow=True)
    S('leg_rev', '    Total segment revenue (legacy basis)', 'memo', 'm', flow=True,
      hist=lambda: f'=IF(COUNT({V("lr_" + LEG[0][0])}:{V("lr_elim")})>0,SUM({V("lr_" + LEG[0][0])}:{V("lr_elim")}),"")')
    S('leg_o_h', '  Segment operating income:', 'sub', 'gen')
    for k, lab in LEG:
        S(f'lo_{k}', f'    {lab}', 'memo', 'm', data=f'lo_{k}', flow=True)
    S('leg_oi', '    Total segment operating income (legacy basis)', 'memo', 'm', flow=True,
      hist=lambda: f'=IF(COUNT({V("lo_" + LEG[0][0])}:{V("lo_" + LEG[-1][0])})>0,SUM({V("lo_" + LEG[0][0])}:{V("lo_" + LEG[-1][0])}),"")')
    S('leg_chk', '  Check: legacy segments + other revenue vs consolidated revenue (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("leg_rev")}),NOT({cur()})),{tol(V("leg_rev") + "+N(" + V("seg_other") + ")", V("is_rev"), 1.01)},"")')
    blank()
    S('co_hdr', 'Unallocated corporate items (between segment operating income and operating income; expense +)', 'block',
      note='UNALLOCATED CORPORATE ITEMS — as printed in each period\'s reconciliation, grouped; company labels and amounts are in the cell comments of the "other" row')
    S('c_amort', '  Amortization of acquisition-related intangibles', 'line', 'm', data='c_amort', flow=True, qe=lambda: f'={PT("pt_amort")}',
      ae=lambda: f'={V("d_amort_sch")}+N({V("m_amort")})', note='Q4/26E point estimate; 2027E+: 10-K schedule of intangibles held (adjusted for the Aug-2026 Space Technology sale) + future-acquisition amortization.')
    S('c_fascas', '  FAS/CAS operating adjustment / pension adjustment ((income) / expense)', 'line', 'm', data='c_fascas', flow=True, fc=lambda: '=0',
      note='Unallocated until 2025 (CAS pension cost charged to contracts less FAS service cost). From Q1-26 no longer an unallocated item (inside the segments): forecast nil.')
    S('c_restr', '  Merger integration, LHX NeXt implementation & restructuring costs', 'line', 'm', data='c_restr', flow=True, qe_in=0.0, ae_in=0.0,
      note='L3Harris merger integration 2019–22; LHX NeXt 2023–25 (implementation phase completed in fiscal 2025). Forecast nil.')
    S('c_acq', '  Acquisition, divestiture & transaction-related expenses', 'line', 'm', data='c_acq', flow=True, qe=lambda: f'={PT("pt_acq")}', ae_in=V0['ae_acq'],
      note='2026: carve-out and planned public offering costs of Missile Solutions, portfolio-shaping costs. Forecast input (assumption).')
    S('c_gain', '  Business divestiture-related (gains) / losses', 'line', 'm', data='c_gain', flow=True, fc=lambda: '=0')
    S('c_impair', '  Impairment of goodwill and other assets', 'line', 'm', data='c_impair', flow=True, fc=lambda: '=0')
    S('c_other', '  Unallocated corporate department expense & other items (deferred-compensation fair value, eliminations, non-reportable businesses)', 'line', 'm',
      data='c_other', flow=True, labkey='c_labels', qe=lambda: f'={PT("pt_cother")}', ae=lambda: f'={V("seg_rev")}*{V("c_other_p")}',
      note='Q4/26E point estimate; 2027E+: % of segment revenue.')
    S('c_other_p', '    % of segment revenue', 'pct', 'pct2', all=ratio('c_other', 'seg_rev'), ae_in=V0['cother_pct'], note=V0['cother_note'])
    S('c_tot', 'Unallocated corporate items and other, net', 'line_b', 'm', flow=True,
      all=lambda: f'=IF(ISNUMBER({V("c_other")}),{nsum(CORP)},"")')
    blank()
    S('kp_hdr', 'Orders & contractual backlog (company KPIs)', 'block', note='ORDERS & BACKLOG — funded + unfunded contractual backlog; orders = funded and unfunded awards (excl. unexercised options, IDIQ ceilings)')
    S('k_orders', '  Orders', 'line', 'm', data='k_orders', flow=True, qe=lambda: f'={V("is_rev")}*{V("k_b2b")}', ae=lambda: f'={V("is_rev")}*{V("k_b2b")}',
      note='History: orders as published (rounded to $0.1bn in most releases). Forecast = revenue × book-to-bill.')
    S('k_b2b', '  Book-to-bill (x)', 'line', 'x2', all=ratio('k_orders', 'is_rev'), qe_in=V0['b2b_q4'], ae_in=V0['b2b'], note=V0['b2b_note'])
    S('k_adj', '  Backlog adjustments (derived: Δ backlog − orders + revenue; divestitures, de-bookings, FX, rounding)', 'line', 'm', flow=True,
      hist=lambda: (f'=IF(AND(ISNUMBER({V("k_bk")}),ISNUMBER({(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["k_bk"]}),ISNUMBER({V("k_orders")})),'
                    f'{V("k_bk")}-{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["k_bk"]}-{V("k_orders")}+{V("is_rev")},"")'
                    if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None), fc=lambda: '=0')
    S('k_bk', '  Total backlog at period end', 'line_b', 'm', data='k_backlog', bs=True,
      qe=lambda: f'={PQ("k_bk")}+{V("k_orders")}-{V("is_rev")}', e26=lambda: f'={QEc("k_bk")}', ae=lambda: f'={P("k_bk")}+{V("k_orders")}-{V("is_rev")}')
    S('k_funded', '  of which funded backlog', 'memo', 'm', data='k_funded', bs=True)
    S('k_cover', '  Backlog ÷ revenue (years; quarters annualised)', 'line', 'x2',
      all=lambda: f'=IF(AND(ISNUMBER({V("k_bk")}),ISNUMBER({V("is_rev")})),IFERROR({V("k_bk")}/({V("is_rev")}*{4 if CTX.col.q else (2 if CTX.col.tp else 1)}),""),"")')
    S('k_org', '  Memo: organic revenue growth % as published by the company', 'memo', 'pct', data='k_org',
      note='Company definition: excludes revenue of divested businesses (and, in the first twelve months, acquired businesses) from both periods.')
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — unallocated; deals closed from 2027E; Base = none)', 'block',
      note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=2.0, e26_in=0.0, note=V0['mna_mult_note'])
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.05)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}',
      note='Mid-year convention.')
    S('m_m', '  Segment operating margin of acquired businesses (before acquisition amortization) %', 'driver', 'pct', e26_in=0.0, ae_in=0.14)
    S('m_oi', '  Segment operating income from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.08)
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.40, note=V0['mna_int_note'])
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=15)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (unallocated; adjusted out)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group Total — revenue & operating income (segment build) → FY26 guidance calibration', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Revenue (segment build)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("seg_rev")}),{V("seg_rev")}+N({V("seg_other")}),"")',
      fc=lambda: f'={V("seg_rev")}+{V("seg_other")}+N({V("m_rev")})',
      note='Segment revenue + other revenue outside the segments (+ future acquisitions from 2027E).')
    S('g_rev_g', '  Revenue y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs consolidated revenue (should be 0; ±1 rounding)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),{tol(V("g_rev"), V("is_rev"), 1.01)},"")')
    S('g_oi', 'Operating income (segment build: segment operating income − unallocated corporate items)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("seg_oi")}),ISNUMBER({V("c_tot")})),{V("seg_oi")}-{V("c_tot")},"")',
      note='Drives the GAAP income statement below (cost of revenue is the balancing line).')
    S('g_oim', '  Operating margin % (GAAP)', 'pct', 'pct', all=ratio('g_oi', 'is_rev'))
    S('g_chk_oi', '  Check: segment build vs consolidated operating income (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("g_oi")}),ISNUMBER({V("is_oi")})),{tol(V("g_oi"), V("is_oi"), 1.01)},"")')
    S('cal_guid', '  Memo: FY26 revenue guidance (scenario end-point)', 'memo', 'm', e26=lambda: '=' + CH(SC['out_rev']), note=V0['rev_guid_note'])
    S('cal_pre', '  Σ segment revenue before calibration (Q4/26E helper)', 'line', 'm', qe=lambda: '=' + '+'.join(V(s + '_pre') for s in SEGK))
    S('cal_g', '  Guidance calibration: uniform Δ % applied to all segments\' Q4/26E revenue', 'driver', 'pct',
      qe=lambda: f'=({V("cal_guid", E26)}-{ACT("is_rev")}-{V("seg_inter")}-{V("seg_other")}-{V("cal_pre")})/{V("cal_pre")}',
      note='Segment guidance end-points do not sum exactly to the consolidated range; one uniform Δ on the Q4 segment revenues closes FY26 revenue to the guidance end-point of the active scenario.')
    S('cal_rev_chk', '  Check: FY26 revenue vs guidance end-point (should be 0)', 'check', 'm', e26=lambda: f'=ROUND({V("g_rev")}-{V("cal_guid")},0)')
    S('cal_eps', '  Memo: FY26 GAAP diluted EPS guidance (scenario end-point, $)', 'eps_memo', 'ps', e26=lambda: '=' + CH(SC['out_eps']), note=V0['eps_guid_note'])
    S('cal_ni', '  Net income available to common shareholders required (FY26E diluted shares × EPS guidance)', 'memo_calc', 'm', e26=lambda: f'={V("cal_eps")}*{V("sh_dil")}')
    S('cal_oi', '  Q4/26E operating income required (((NI − 9M actual) + Q4 deemed dividend) ÷ (1 − Q4 tax rate) − Q4 non-operating income + Q4 net interest)', 'memo_calc', 'm',
      e26=lambda: f'=({V("cal_ni")}-{ACT("is_nic")}+{QEc("is_pref")})/(1-{PT("pt_etr")})-{QEc("is_pens")}-{QEc("is_othno")}+{QEc("is_int")}')
    S('cal_oi_pre', '  Segment operating income before margin calibration (Q4/26E helper)', 'line', 'm',
      qe=lambda: '=' + '+'.join(f'{V(s + "_rev")}*{V(s + "_m_pre")}' for s in SEGK))
    S('cal_segrev', '  Σ segment revenue (Q4/26E helper)', 'line', 'm', qe=lambda: '=' + '+'.join(V(s + '_rev') for s in SEGK))
    S('cal_m', '  Guidance calibration: Δ segment margin (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_oi", E26)}+{V("c_tot")}-{V("cal_oi_pre")})/{V("cal_segrev")}',
      note='Solves the uniform segment-margin shift so that FY26 GAAP diluted EPS = the guidance end-point for the active scenario (closed form: no circularity).')
    S('cal_eps_chk', '  Check: FY26 GAAP diluted EPS vs guidance end-point (should be 0.00)', 'check', 'ps', e26=lambda: f'=ROUND({V("eps_dil")}-{V("cal_eps")},2)')
    S('cal_sm', '  Memo: FY26 segment operating margin guidance "low 16%" (read as 16.2%) — information, not forced', 'memo', 'pct', e26=lambda: f'={PT("pt_m_tot")}')
    S('cal_sm_d', '    Model segment operating margin − guidance (pp)', 'memo_calc', 'pct', e26=lambda: f'={V("seg_m")}-{V("cal_sm")}')
    S('cal_cfo', '  Memo: FY26 cash from operations guidance ($m) — drives the Q4/26E working-capital calibration', 'memo', 'm', e26=lambda: f'={PT("pt_cfo")}')
    S('cal_cfo_chk', '  Check: FY26 cash from operations vs guidance (should be 0)', 'check', 'm', e26=lambda: f'=ROUND({V("cf_cfo")}-{V("cal_cfo")},0)')
    S('cal_fcf', '  Memo: FY26 free cash flow guidance ($m; CFO − capital expenditures)', 'memo', 'm', e26=lambda: f'={PT("pt_fcf")}')
    S('cal_fcf_d', '  Model FY26 free cash flow − guidance (information)', 'memo_calc', 'm', e26=lambda: f'={V("fcf")}-{V("cal_fcf")}')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A & adjusting items', 'block', note='COST DRIVERS — inputs that drive forecast cost lines (Q4/26E: point estimates; 2027E+: % of revenue or schedules)')
    S('d_dda', '  Depreciation & amortization (total; cash-flow statement)', 'line', 'm', data='cf_da', flow=True,
      fc=lambda: f'={V("d_dep")}+{V("d_amort")}', note='Cash-flow statement line (year to date; discrete quarters derived). Forecast = depreciation & other amortization + acquisition-related amortization.')
    S('d_amort', '  Amortization of acquisition-related intangibles', 'line', 'm', flow=True, all=lambda: f'=IF(ISNUMBER({V("c_amort")}),{V("c_amort")},"")')
    S('d_amort_sch', '  Amortization schedule — acquisition-related intangibles held (10-K, input)', 'driver', 'm', ae_in=V0['amort_sched'], note=V0['amort_note'])
    S('d_dep', '  Depreciation & other amortization (total D&A − acquisition-related amortization)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("d_dda")}),ISNUMBER({V("d_amort")})),{V("d_dda")}-{V("d_amort")},"")',
      qe=lambda: f'={PT("pt_dep")}', ae=lambda: f'={V("is_rev")}*{V("d_dep_pct")}')
    S('d_dep_pct', '  Depreciation & other amortization % of revenue', 'pct', 'pct', all=ratio('d_dep', 'is_rev'), ae_in=V0['dep_pct'], note=V0['dep_note'])
    S('d_sga', '  General & administrative expenses % of revenue', 'pct', 'pct', all=ratio('is_sga', 'is_rev'),
      qe=lambda: f'=IFERROR({ACT("is_sga")}/{ACT("is_rev")},"")', ae=lambda: f'={V("d_sga", E26)}',
      note='"Engineering, selling and administrative expenses" until 2023. Q4/26E: 9M 2026 ratio; 2027E+: held at 2026E. Cost of revenue is the balancing line of the build.')
    S('d_sbc', '  Share-based compensation incl. share-based matching contributions (cash-flow statement)', 'line', 'm', data='cf_sbc', flow=True,
      qe=lambda: f'={P("d_sbc")}', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}',
      note='Q4/26E: prior-year quarter; 2027E+: % of revenue. L3Harris does not adjust out share-based compensation.')
    S('d_sbc_pct', '  Share-based compensation % of revenue', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_rd', '  Memo: company-funded R&D ($m; 10-K)', 'memo', 'm', data='rd', flow=True)
    S('d_emp', '  Memo: employees at year end (approx., 10-K)', 'memo', 'm', data='employees', bs=True)
    S('d_adj_h', '  Adjusting items (pre-tax; items the company excluded from non-GAAP EPS while it published the measure; model definition from Q1-26):', 'sub', 'gen')
    S('a_restr', '  Merger integration, LHX NeXt implementation & restructuring', 'line', 'm', data='a_restr', flow=True, fc=lambda: f'={V("c_restr")}')
    S('a_acq', '  Acquisition, divestiture & transaction-related expenses', 'line', 'm', data='a_acq', flow=True, fc=lambda: f'={V("c_acq")}')
    S('a_gain', '  Business divestiture-related (gains) / losses', 'line', 'm', data='a_gain', flow=True, fc=lambda: f'={V("c_gain")}')
    S('a_impair', '  Impairments', 'line', 'm', data='a_impair', flow=True, fc=lambda: f'={V("c_impair")}')
    S('a_oth', '  Other operating items (COVID-19, legal, deferred compensation, other)', 'line', 'm', data='a_oth', flow=True, labkey='a_labels', fc=lambda: '=0',
      note='Company labels and amounts per period are in the cell comments (historical cells).')
    S('a_nonop', '  Non-operating items (debt extinguishment, pension settlements, investment / preferred-stock derivative fair-value changes)', 'line', 'm', data='a_nonop', flow=True, fc=lambda: '=0')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF OPERATIONS (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (operating income from the segment build; cost of revenue implied)')
    S('is_rev', 'Revenue', 'total', 'm', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the segment build.')
    S('is_cogs', 'Cost of revenue', 'line', 'm', data='cogs', flow=True, fc=lambda: f'={V("is_rev")}-{V("is_sga")}-{V("is_othop")}-{V("is_oi")}',
      note='Forecast = revenue − G&A − other operating items − operating income (implied by the segment build).')
    S('is_gp', 'Gross profit', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_rev")}-{V("is_cogs")},"")')
    S('is_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('is_sga', 'General and administrative expenses (engineering, selling & administrative to 2023)', 'line', 'm', data='sga', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_sga")}')
    S('is_othop', 'Other operating items shown separately (business divestiture-related (gains) losses, impairments; expense +)', 'line', 'm', data='oth_op', flow=True,
      labkey='oth_op_labels', fc=lambda: '=0', note='Shown on the face of the statement in 2019–2023; inside G&A from 2024. Forecast: divestiture / impairment items are booked in G&A (nil in the forecast).')
    S('is_oi', 'Operating income', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_rev")}-{V("is_cogs")}-{V("is_sga")}-N({V("is_othop")}),"")', fc=lambda: f'={V("g_oi")}',
      note='Forecast = segment operating income − unallocated corporate items.')
    S('is_oi_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('is_oi_pub', '  Memo: operating income as reported', 'memo', 'm', data='oi', flow=True)
    S('is_oi_chk', '  Check: operating income vs reported (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("is_oi_pub")}),ISNUMBER({V("is_oi")})),{tol(V("is_oi"), V("is_oi_pub"), 1.01)},"")')
    S('is_pens', 'Non-service FAS pension income (non-operating; non-cash)', 'line', 'm', data='nonop_pens', flow=True, qe=lambda: f'={PT("pt_pens")}', ae_in=V0['pens'],
      note=V0['pens_note'])
    S('is_othno', 'Other non-operating income (expense), net', 'line', 'm', data='nonop_oth', flow=True, labkey='nonop_labels', qe=lambda: f'={PT("pt_othno")}', ae_in=0.0,
      note='Investment gains / losses, deferred-compensation plan assets, fair-value changes of the subsidiary preferred-stock conversion feature and warrants (2026). Forecast nil.')
    S('is_int', 'Interest expense, net of interest income', 'line', 'm', data='int_net', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'={P("ds_total")}*{V("ds_r_debt")}-({P("bs_cash")}+{P("bs_stinv")})*{V("ds_r_cash")}',
      note='Q4/26E point estimate. 2027E+ = rate × opening debt − yield × opening cash & short-term investments (no circularity).')
    S('is_ebt', 'Income from continuing operations before income taxes', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_oi")}),{V("is_oi")}+N({V("is_pens")})+N({V("is_othno")})-{V("is_int")},"")')
    S('is_tax', 'Income taxes', 'line', 'm', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'], note=V0['etr_note'])
    S('is_cont', 'Income from continuing operations', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_disc', 'Discontinued operations, net of income taxes', 'line', 'm', data='disc', flow=True, fc=lambda: '=0')
    S('is_nitot', 'Net income', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_cont")}),{V("is_cont")}+N({V("is_disc")}),"")')
    S('is_nci', 'Noncontrolling interests, net of income taxes (deducted)', 'line', 'm', data='nci', flow=True, fc=lambda: '=0')
    S('is_ni', 'Net income attributable to L3Harris Technologies, Inc.', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_nitot")}),{V("is_nitot")}-N({V("is_nci")}),"")')
    S('is_ni_chk', '  Check: net income attributable vs reported (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),{tol(V("is_ni"), V("is_ni_pub"), 1.01)},"")')
    S('is_ni_pub', '  Memo: net income attributable as reported', 'memo', 'm', data='ni', flow=True)
    S('is_pref', 'Subsidiary preferred stock deemed dividends (deducted; from Q2-26)', 'line', 'm', data='pref_div', flow=True, qe=lambda: f'={PT("pt_pref")}', ae_in=V0['pref_div'],
      note=V0['pref_note'])
    S('is_nic', 'Net income available to common shareholders', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ni")}),{V("is_ni")}-N({V("is_pref")}),"")')
    S('is_dda', '  Memo: depreciation & amortization (total)', 'memo_calc', 'm', all=lambda: f'={V("d_dda")}')
    S('is_sbc', '  Memo: share-based compensation', 'memo_calc', 'm', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share — L3Harris common stock)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={B1("bs_shares")}-${E26}${R["bb_sh"]}*0.5+${E26}${R["bb_iss"]}*0.5',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q4/26E: shares outstanding at 2-Oct-2026 − Q4 buybacks (mid-quarter) + equity-plan issuance. 2027E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_nic")}/{V("sh_dil")},""),"")',
      note='Net income available to common shareholders ÷ weighted diluted shares (±$0.01 vs reported; the company\'s year-to-date share weighting differs slightly from the average of the quarters).')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.02 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0201,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('eps_cont', '  EPS – diluted from continuing operations ($; model)', 'eps_memo', 'ps',
      all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR(({V("is_cont")}-N({V("is_nci")})-N({V("is_pref")}))/{V("sh_dil")},""),"")')
    S('eps_cont_pub', '  Memo: EPS – diluted from continuing operations as reported ($)', 'eps_memo', 'ps', data='eps_cont')
    S('dps', '  Cash dividends paid per share ($)', 'line', 'ps', data='dps', flow=True, qe_in=V0['dps_q'],
      ae=lambda: f'={P("dps")}*(1+{V("dps_g")})', note=V0['dps_note'])
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'])
    blank()

    # ------------------------------------------------------------------ RECON 1: OI -> segment OI / adjusted EBITA
    S('sec_r1', 'RECONCILIATION: OPERATING INCOME → SEGMENT OPERATING INCOME (company) · → ADJUSTED OPERATING INCOME / EBITA (model)', 'section',
      note='SEGMENT OPERATING INCOME — per the release reconciliations (unallocated corporate items); adjusted operating income = operating income + acquisition-related amortization + the items the company excluded from non-GAAP EPS')
    S('o_op', 'Operating income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_oi")}')
    S('o_corp', '  (+) Unallocated corporate items and other, net', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("c_tot")}),{V("c_tot")},"")')
    S('o_seg', '  = Segment operating income (model bridge)', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("o_op")}),ISNUMBER({V("o_corp")})),{V("o_op")}+{V("o_corp")},"")')
    S('o_seg_pub', '  Company-published segment operating income', 'memo', 'm', data='seg_oi_pub', flow=True)
    S('o_seg_chk', '  Check: model bridge vs company-published (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("o_seg_pub")}),ISNUMBER({V("o_seg")})),{tol(V("o_seg"), V("o_seg_pub"), 1.01)},"n/p")')
    S('o_def', '  Definition / basis (company segment operating income definition in force)', 'text', 'gen',
      note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('o_h2', 'To adjusted operating income (model; = adjusted EBITA):', 'sub', 'gen')
    S('o_amort', '  (+) Amortization of acquisition-related intangibles', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("c_amort")}),{V("c_amort")},"")')
    S('a_amort', '    of which added back in the company\'s non-GAAP EPS (Q3-19 to Q4-24 only)', 'memo', 'm', data='a_amort', flow=True, fc=lambda: '=0',
      note='L3Harris added back acquisition-related amortization in non-GAAP EPS from the merger (Q3-19) until Q4-24; from Q1-25 it is no longer added back (2024 comparatives recast by the company). Harris did not add it back.')
    for k, lab, d in (('o_restr', '  (+) Merger integration, LHX NeXt & restructuring', 'a_restr'), ('o_acq', '  (+) Acquisition, divestiture & transaction-related expenses', 'a_acq'),
                      ('o_gain', '  (+) Business divestiture-related (gains) / losses', 'a_gain'), ('o_impair', '  (+) Impairments', 'a_impair'),
                      ('o_oth', '  (+) Other operating items', 'a_oth')):
        S(k, lab, 'line', 'm', all=lambda d=d: f'=IF(ISNUMBER({V(d)}),{V(d)},"")')
    S('o_tot', '  Total operating adjusting items excl. amortization (pre-tax)', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_op")}),{nsum(["o_restr", "o_acq", "o_gain", "o_impair", "o_oth"])},"")')
    S('o_adj', '  = Adjusted operating income before acquisition-related amortization (adjusted EBITA; model)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+N({V("o_amort")})+{V("o_tot")},"")',
      note='Model measure (the company publishes no adjusted operating income from 2022): GAAP operating income + acquisition-related amortization + the operating items excluded from non-GAAP EPS. Basis of NOPAT / the DCF.')
    S('o_adj_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_adj_g', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental adjusted operating margin (Δ adjusted operating income / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    S('o_ebit', '  Memo: adjusted EBIT, company definition 2H19–2021 (adjusted operating income + non-operating income, model)', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_adj")}),{V("o_adj")}+N({V("is_pens")})+N({V("is_othno")})+N({V("a_nonop")}),"")')
    S('o_pub', '  Company-published adjusted EBIT (FY2019–2021)', 'memo', 'm', data='adj_ebit_pub', flow=True)
    S('o_chk', '  Check: model adjusted EBIT vs company-published (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("o_pub")}),ISNUMBER({V("o_ebit")})),{tol(V("o_ebit"), V("o_pub"), 1.01)},"n/p")')
    blank()

    # ------------------------------------------------------------------ RECON 2: NI -> EBITDA -> adjusted EBITDA
    S('sec_r2', 'RECONCILIATION: NET INCOME → EBITDA (company definition, published from FY2023) → ADJUSTED EBITDA (model)', 'section',
      note='EBITDA — net income + income taxes + net interest expense + depreciation & amortization (company, earnings appendix); adjusted EBITDA (model) = operating income + D&A + operating adjusting items (excludes non-cash non-service pension income)')
    S('r_ni', 'Net income (incl. discontinued operations and noncontrolling interests)', 'line_b', 'm', all=lambda: f'={V("is_nitot")}')
    S('r_tax', '  (+) Income taxes', 'line', 'm', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest expense, net', 'line', 'm', all=lambda: f'={V("is_int")}')
    S('r_dda', '  (+) Depreciation & amortization', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("d_dda")}),{V("d_dda")},"")')
    S('r_ebitda', '  = EBITDA (company definition)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_ni")}),ISNUMBER({V("r_dda")})),{V("r_ni")}+{V("r_tax")}+{V("r_int")}+{V("r_dda")},"")')
    S('r_ebitda_pub', '  Company-published EBITDA', 'memo', 'm', data='ebitda_pub', flow=True)
    S('r_ebitda_chk', '  Check: model vs company-published EBITDA (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda_pub")}),ISNUMBER({V("r_ebitda")})),{tol(V("r_ebitda"), V("r_ebitda_pub"), 1.01)},"n/p")')
    S('r_nonop', '  (−) Non-service FAS pension income, other non-operating income and discontinued operations', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),-N({V("is_pens")})-N({V("is_othno")})-N({V("is_disc")}),"")')
    S('r_adjx', '  (+) Operating adjusting items (excl. amortization)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("o_tot")}),{V("o_tot")},"")')
    S('r_adj', '  = Adjusted EBITDA (model)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda")}),ISNUMBER({V("r_adjx")})),{V("r_ebitda")}+{V("r_nonop")}+{V("r_adjx")},"")',
      note='Model definition (= operating income + D&A + operating adjusting items). Used for leverage (net debt / adjusted EBITDA) and EV / EBITDA; excludes the non-cash pension income that the company\'s EBITDA includes.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_chk', '  Check: adjusted EBITDA − D&A + acquisition-related amortization = adjusted operating income (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_adj")}),ISNUMBER({V("o_adj")})),{tol(V("r_adj") + "-" + V("r_dda") + "+N(" + V("o_amort") + ")", V("o_adj"), 0.6)},"")')
    S('r_def', '  Definition / basis (EBITDA)', 'text', 'gen')
    S('r_ebit_h', 'To adjusted EBIT, full-cost (for ROIC):', 'sub', 'gen')
    S('r_ddan', '  (−) Depreciation & amortization (total)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("d_dda")}),-{V("d_dda")},"")')
    S('r_ebit', '  = Adjusted EBIT, full-cost (adjusted EBITDA − total D&A)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+{V("r_ddan")},"")')
    S('r_ebit_m', '  Adjusted EBIT (full-cost) margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: integration, restructuring & transaction costs (cash costs adjusted out; deducted in the DCF)', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_acq")}),N({V("o_acq")})+N({V("o_restr")}),"")')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: DILUTED EPS → NON-GAAP DILUTED EPS (company definition to Q4-25; model rebuild from Q1-26)', 'section',
      note='NON-GAAP EPS — income from continuing operations attributable to common shareholders + pre-tax adjusting items − tax effect; the company stopped publishing non-GAAP EPS with the Q1-26 release (GAAP EPS guidance) — the FY2025 definition is rebuilt by the model from Q1-26')
    S('e_ni', 'Income from continuing operations attributable to common shareholders', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_cont")}),{V("is_cont")}-N({V("is_nci")})-N({V("is_pref")}),"")')
    S('e_amort', '  (+) Amortization of acquisition-related intangibles (where adjusted)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("a_amort")}),{V("a_amort")},IF(ISNUMBER({V("e_ni")}),0,""))')
    S('e_op', '  (+) Operating adjusting items (pre-tax; bridge above)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("o_tot")}),{V("o_tot")},"")')
    S('e_nonop', '  (+) Non-operating adjusting items (pre-tax)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("e_ni")}),N({V("a_nonop")}),"")')
    S('e_tax', '  (−) Tax effect of the adjustments & discrete tax items', 'line', 'm', data='a_tax', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("e_ni")}),-({V("e_amort")}+{V("e_op")}+{V("e_nonop")})*{V("e_trate")},"")',
      fc=lambda: f'=-({V("e_amort")}+{V("e_op")}+{V("e_nonop")})*{V("e_trate")}',
      note='Published periods: company figure (per-share tax effect × diluted shares where only per-share data are published). Q1-26 onward and forecast: adjusting items × the tax rate on adjustments (input row).')
    S('e_nciadj', '  (−) Noncontrolling-interest share of the adjustments', 'line', 'm', data='a_nci', flow=True, fc=lambda: '=0')
    S('e_round', '  Per-share rounding (company bridges are published per share; $m = per share × diluted shares)', 'line', 'm', data='a_round', flow=True, fc=lambda: '=0')
    S('e_adjni', '  = Non-GAAP income from continuing operations attributable to common shareholders (model bridge)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("e_ni")}),{V("e_ni")}+{V("e_amort")}+{V("e_op")}+{V("e_nonop")}+N({V("e_tax")})+N({V("e_nciadj")})+N({V("e_round")}),"")')
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Non-GAAP EPS – diluted ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published non-GAAP diluted EPS ($)', 'eps_memo', 'ps', data='e_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0101,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Non-GAAP EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_trate', '  Tax rate on the adjustments (input from Q1-26; implied in published periods)', 'pct', 'pct',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_tax")}),ISNUMBER({V("e_op")})),IFERROR(-{V("e_tax")}/({V("e_amort")}+{V("e_op")}+{V("e_nonop")}),""),"")',
      hist_in=V0['e_trate'], qe_in=V0['e_trate'], ae_in=V0['e_trate'], note=V0['e_trate_note'])
    S('e_pa', '  Memo: pension adjusted non-GAAP diluted EPS as published ($; FY2025 only)', 'eps_memo', 'ps', data='e_pub_pa')
    S('e_def', '  Definition / basis (company non-GAAP EPS definition)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Revenue y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_sms', '  Space & Mission Systems revenue y/y %', 'growth', 'pct', all=growth('sms_rev'))
    S('gm_csd', '  Communications & Spectrum Dominance revenue y/y %', 'growth', 'pct', all=growth('csd_rev'))
    S('gm_ms', '  Missile Solutions revenue y/y %', 'growth', 'pct', all=growth('ms_rev'))
    S('gc_sms', '  Contribution to revenue growth — Space & Mission Systems (pp)', 'growth', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("sms_rev")}),ISNUMBER({P("sms_rev")})),IFERROR(({V("sms_rev")}-{P("sms_rev")})/{P("is_rev")},""),"")' if CTX.col.prior else None))
    S('gc_csd', '  Contribution to revenue growth — Communications & Spectrum Dominance (pp)', 'growth', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("csd_rev")}),ISNUMBER({P("csd_rev")})),IFERROR(({V("csd_rev")}-{P("csd_rev")})/{P("is_rev")},""),"")' if CTX.col.prior else None))
    S('gc_ms', '  Contribution to revenue growth — Missile Solutions (pp)', 'growth', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("ms_rev")}),ISNUMBER({P("ms_rev")})),IFERROR(({V("ms_rev")}-{P("ms_rev")})/{P("is_rev")},""),"")' if CTX.col.prior else None))
    S('gm_seg', '  Segment operating income y/y %', 'growth', 'pct', all=growth('seg_oi'))
    S('gm_adjop', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating income (GAAP) y/y %', 'growth', 'pct', all=growth('is_oi'))
    S('gm_ni', '  Net income attributable y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Non-GAAP EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('gm_seg_m', '  Segment operating margin %', 'pct', 'pct', all=ratio('seg_oi', 'seg_rev'))
    S('gm_adjop_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_inc', '  Incremental adjusted operating margin (Δ adjusted operating income / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_sga', '  G&A % of revenue', 'pct', 'pct', all=ratio('is_sga', 'is_rev'))
    blank()
