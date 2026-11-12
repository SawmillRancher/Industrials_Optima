"""Row specification of the RTX Model sheet, part 1 (MLM template layout and process):
segment build (Collins Aerospace: commercial / defense; Pratt & Whitney: commercial / military; Raytheon: U.S. government /
international / commercial, each from the 10-Q / 10-K revenue disaggregation by customer type, plus inter-segment sales) ->
segment sales x adjusted segment operating margin -> + eliminations & other, corporate, FAS/CAS operating adjustment = adjusted
operating profit -> legacy segments memo (Otis, Carrier / CCS, UTC Fire & Security, Sikorsky; RIS / RMD) -> M&A lever -> group
total & 2026 outlook calibration -> cost drivers (acquisition accounting amortization, restructuring, pension, interest, tax)
-> income statement -> GAAP-to-adjusted bridges -> growth & margins."""
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
def ACT(key): return f'SUM({Q1}{R[key]}:{Q3}{R[key]})'    # 9M 2026 actual (Q1-Q3/26)
def ACT0(key): return f'SUM({PQ1}{R[key]}:{PQ3}{R[key]})' # 9M 2025 actual (Q1-Q3/25)
def B1(key): return f'{LQ}{R[key]}'                       # 30-Sep-2026 balance
def ISN(key, expr, alt='""'): return f'=IF(ISNUMBER({V(key)}),{expr},{alt})'

# current segments: (key, title, lever prefix, [(subkey, label, data key, growth lever)], reported sales key, GAAP OP key, adjusted OP key)
SEG = [('col', 'Collins Aerospace', 'COL', [('comm', 'Commercial aerospace and other commercial sales', 'c_col_comm', 'COL_COMM'),
                                           ('def', 'Defense sales (U.S. government, foreign military sales, foreign government direct)', 'c_col_def', 'COL_DEF')], 'c_col_inter'),
       ('pw', 'Pratt & Whitney', 'PW', [('comm', 'Commercial aerospace sales (OEM and aftermarket)', 'c_pw_comm', 'PW_COMM'),
                                        ('mil', 'Military sales (U.S. government, foreign military sales, foreign government direct)', 'c_pw_def', 'PW_MIL')], 'c_pw_inter'),
       ('rtn', 'Raytheon', 'RTN', [('usg', 'Sales to the U.S. government', 'c_rtn_usg', 'RTN_USG'),
                                   ('intl', 'International sales (foreign military sales through the U.S. government + foreign government direct commercial)', 'c_rtn_intl', 'RTN_INTL'),
                                   ('comm', 'Commercial and other sales', 'c_rtn_comm', 'RTN_USG')], 'c_rtn_inter')]
LINES = [f'{s}_{t}' for s, _, _, ts, _ in SEG for t, _, _, _ in ts]
SEGK = [s for s, *_ in SEG]
LEGACY = [('otis', 'Otis (separated 3-Apr-2020; discontinued operations from Q2-20)'), ('car', 'Carrier / UTC Climate, Controls & Security (separated 3-Apr-2020)'),
          ('fs', 'UTC Fire & Security (merged into UTC Climate, Controls & Security in 2012)'), ('sik', 'Sikorsky (sold to Lockheed Martin 6-Nov-2015; discontinued operations from Q3-15)'),
          ('ris', 'Raytheon Intelligence & Space (Q2-20 to Q4-22; in Raytheon above)'), ('rmd', 'Raytheon Missiles & Defense (Q2-20 to Q4-22; in Raytheon above)')]
LEG_IN_TOTAL = ['otis', 'car', 'fs', 'sik']          # legacy segments that are part of the consolidated total in their years (RIS / RMD already summed into Raytheon)

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of the 2026 outlook ranges.'))
    r = 11
    SCEN_ROWS.append((r, 'out_hdr', V0['out_hdr'], 'High', 'Mid', 'Low', V0['out_note'])); r += 1
    for key, lab, (hi, mid, lo), nf, note in V0['outlook']:
        SC[key] = r; SCEN_ROWS.append((r, 'out', lab, hi, mid, lo, note, nf)); r += 1
    r += 1
    SCEN_ROWS.append((r, 'pt_hdr', 'Q4/26E and 2026E point estimates (all cases)', None, None, None, None)); r += 1
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
    # ------------------------------------------------------------------ SEGMENT BUILD
    S('sec_seg', 'SEGMENT BUILD — COLLINS AEROSPACE · PRATT & WHITNEY · RAYTHEON (sales by customer type × adjusted segment operating margin)', 'section',
      note='SEGMENT BUILD — modelling logic (customer-type sales lines → segment sales → adjusted segment operating profit at the segment margin → + eliminations, corporate and the FAS/CAS operating adjustment = adjusted operating profit → GAAP P&L)')
    blank()
    descr = {'col': 'Collins Aerospace (avionics, interiors, mechanical systems, mission systems, power & controls; = Hamilton Sundstrand → UTC Aerospace Systems (Goodrich, Jul-2012) → Collins Aerospace (Rockwell Collins, 26-Nov-2018))',
             'pw': 'Pratt & Whitney (large commercial engines, Pratt & Whitney Canada, military engines; OEM, aftermarket and military)',
             'rtn': 'Raytheon (missiles, air & missile defense, naval and space systems; = Raytheon Intelligence & Space + Raytheon Missiles & Defense 3-Apr-2020 to Q4-22, one segment from 1-Jul-2023)'}
    for s, title, code, types, inter in SEG:
        S(f'{s}_hdr', descr[s], 'block', note=f'{title.upper()} — modelling logic')
        for t, tl, dk, lever in types:
            key = f'{s}_{t}'
            S(key, f'  {tl}', 'line', 'm', data=dk, flow=True,
              qe=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})', ae=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})',
              note=('Sales by type of customer (10-Q / 10-K revenue-disaggregation note, from 2018; external sales). Q4/26E: prior-year quarter × (1 + growth). '
                    '2027E+: prior year × (1 + scenario lever).') if t == types[0][0] else None)
            S(key + '_g', '    y/y %', 'growth', 'pct', all=growth(key),
              qe=lambda key=key: f'={V(key + "_pre")}+{QEa("cal_g")}',
              ae=lambda lever=lever: '=' + CH(SC[lever][CTX.col.year]),
              note='Q4/26E: 9M 2026 y/y growth of the line + sales-guidance calibration Δ (Group block). 2027E–2031E: scenario lever (Bull / Base / Bear table →).' if t == types[0][0] else None)
            S(key + '_pre', '    Q4/26E growth before sales calibration (9M 2026 y/y)', 'driver', 'pct',
              qe=lambda key=key: f'=IFERROR({ACT(key)}/{ACT0(key)}-1,0)')
        first = f'{s}_{types[0][0]}'
        S(f'{s}_ext', f'  {title} — external sales (Σ customer types)', 'line', 'm',
          hist=lambda s=s, types=types, first=first: ISN(first, '+'.join(V(s + '_' + t) for t, _, _, _ in types)),
          fc=lambda s=s, types=types: '=' + '+'.join(V(s + '_' + t) for t, _, _, _ in types))
        S(f'{s}_inter', '  Inter-segment sales', 'line', 'm', data=inter, flow=True,
          qe=lambda s=s: f'={V(s + "_ext")}*{V(s + "_inter_p")}', ae=lambda s=s: f'={V(s + "_ext")}*{V(s + "_inter_p")}')
        S(f'{s}_inter_p', '    Inter-segment % of external sales', 'pct', 'pct', all=ratio(f'{s}_inter', f'{s}_ext'),
          qe=lambda s=s: f'=IFERROR({ACT(s + "_inter")}/{ACT(s + "_ext")},0)', ae_in=V0['inter_p'][s],
          note='Q4/26E: 9M 2026 ratio; 2027E+: input held at the 2025–26 level.' if s == 'col' else None)
        S(f'{s}_rev', f'  {title} — segment net sales', 'line_b', 'm',
          hist=lambda s=s, first=first: f'=IF(ISNUMBER({V(first)}),{V(s + "_ext")}+N({V(s + "_inter")}),{V(s + "_pub")})',
          fc=lambda s=s: f'={V(s + "_ext")}+{V(s + "_inter")}',
          note='History: Σ customer-type sales + inter-segment where published (2018+), otherwise segment net sales as reported (segment table).' if s == 'col' else None)
        S(f'{s}_rev_g', '  Segment sales y/y %', 'growth', 'pct', all=growth(f'{s}_rev'))
        S(f'{s}_mix', '  % of consolidated net sales', 'pct', 'pct', all=ratio(f'{s}_rev', 'g_rev'))
        S(f'{s}_pub', f'  Memo: {title} segment net sales as reported (segment table)', 'memo', 'm', data=f's_{s}_rev', flow=True)
        S(f'{s}_chk', '  Check: customer-type build vs reported segment net sales (should be 0; ±1 rounding)', 'check', 'm',
          hist=lambda s=s, first=first: f'=IF(AND(ISNUMBER({V(first)}),ISNUMBER({V(s + "_pub")})),IF(ABS({V(s + "_rev")}-{V(s + "_pub")})<=1.5,0,ROUND({V(s + "_rev")}-{V(s + "_pub")},0)),"")')
        S(f'{s}_org', '  Memo: organic sales growth % (company-published)', 'memo', 'pct', data=f'k_org_{s}', pctdata=True)
        if s == 'col':
            for k, lab in (('k_col_oe', 'commercial OE'), ('k_col_am', 'commercial aftermarket'), ('k_col_def', 'defense')):
                S(f'{s}_{k}', f'  Memo: {lab} sales growth y/y % (release narrative)', 'memo', 'pct', data=k, pctdata=True)
        if s == 'pw':
            for k, lab in (('k_pw_oe', 'commercial OE'), ('k_pw_am', 'commercial aftermarket'), ('k_pw_mil', 'military')):
                S(f'{s}_{k}', f'  Memo: {lab} sales growth y/y % (release narrative)', 'memo', 'pct', data=k, pctdata=True)
        if s == 'rtn':
            S('rtn_bl', '  Memo: Raytheon backlog ($bn, period end)', 'memo', 'bn', data='k_bl_rtn')
            S('rtn_b2b', '  Memo: Raytheon implied book-to-bill (Δ backlog + sales) ÷ sales (x; annual)', 'memo_calc', 'x2', ann=True,
              all=lambda: (f'=IF(AND(ISNUMBER({V("rtn_bl")}),ISNUMBER({P("rtn_bl")})),IFERROR((({V("rtn_bl")}-{P("rtn_bl")})*1000+{V("rtn_rev")})/{V("rtn_rev")},""),"")' if CTX.col.prior else None))
        S(f'{s}_op', f'  {title} — segment operating profit (GAAP, segment table)', 'line', 'm', data=f's_{s}_op', flow=True,
          fc=lambda s=s: f'={V(s + "_aop")}-{V(s + "_restr")}+{V(s + "_sig")}',
          note='Segment operating profit as reported (excludes acquisition accounting adjustments, the FAS/CAS operating adjustment and corporate). Forecast = adjusted segment OP − restructuring + significant items.' if s == 'col' else None)
        S(f'{s}_restr', '  Segment restructuring costs (adjusted out)', 'line', 'm', data=f's_{s}_restr', flow=True,
          qe=lambda s=s: f'={QEc("d_restr")}*{V0["restr_mix"][s]}', ae=lambda s=s: f'={V("d_restr")}*{V0["restr_mix"][s]}',
          note=f'Forecast = total restructuring × {V0["restr_mix"][s]:.0%} (segment share of 2024–26 restructuring; assumption).' if True else None)
        S(f'{s}_sig', '  Segment significant and/or non-recurring items in operating profit (income +; adjusted out)', 'line', 'm', data=f's_{s}_sig', flow=True, fc=lambda: '=0',
          note='Company items by segment (gains on sales, charges such as the Q3-23 powder metal matter, customer bankruptcies); forecast nil.' if s == 'col' else None)
        S(f'{s}_aop', f'  {title} — adjusted segment operating profit', 'line_b', 'm', data=f's_{s}_aop', flow=True,
          hist=lambda s=s: f'=IF(ISNUMBER({V(s + "_op")}),{V(s + "_op")}+N({V(s + "_restr")})-N({V(s + "_sig")}),"")',
          qe=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}', ae=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}',
          note=('Company definition: segment operating profit excluding restructuring and net significant / non-recurring items (published from Q4-13 as "adjusted"; earlier years rebuilt as OP + restructuring − non-recurring items). '
                'Forecast = segment sales × adjusted margin.') if s == 'col' else None)
        S(f'{s}_m', '  Adjusted segment operating margin %', 'pct', 'pct', all=ratio(f'{s}_aop', f'{s}_rev'),
          qe=lambda s=s: f'={V(s + "_m_pre")}+{QEa("cal_m")}', ae=lambda s=s, code=code: '=' + CH(SC[f'{code}_M'][CTX.col.year]),
          note='Q4/26E: margin before calibration + adjusted-EPS-guidance calibration Δ (Group block). 2027E+: scenario lever.' if s == 'col' else None)
        S(f'{s}_m_pre', '  Q4/26E margin before EPS calibration (prior-year quarter + 9M 2026 y/y drift)', 'driver', 'pct',
          qe=lambda s=s: f'={P(s + "_m")}+IFERROR({ACT(s + "_aop")}/{ACT(s + "_rev")}-{ACT0(s + "_aop")}/{ACT0(s + "_rev")},0)')
        S(f'{s}_inc', '  Incremental adjusted margin (Δ adjusted OP / Δ sales)', 'pct', 'pct', all=incr(f'{s}_aop', f'{s}_rev'))
        blank()
    # legacy segments (memo; part of the consolidated totals in their years)
    S('leg_hdr', 'Legacy segments (as reported in their years; included in the consolidated totals below)', 'block',
      note='LEGACY SEGMENTS — Otis, Carrier / CCS and UTC Fire & Security (UTC conglomerate to 2019), Sikorsky (to Q2-15); RIS / RMD shown as memo (summed into Raytheon above)')
    for k, lab in LEGACY:
        S(f'{k}_rev', f'  {lab} — net sales', 'memo', 'm', data=f's_{k}_rev', flow=True)
        S(f'{k}_op', f'    operating profit', 'memo', 'm', data=f's_{k}_op', flow=True)
        S(f'{k}_aop', f'    adjusted operating profit (OP + restructuring − non-recurring items)', 'memo', 'm', data=f's_{k}_aop', flow=True,
          hist=lambda k=k: f'=IF(ISNUMBER({V(k + "_op")}),{V(k + "_op")}+N({V(k + "_items")}),"")')
        S(f'{k}_items', f'    restructuring − significant items (adjusted out)', 'memo', 'm', data=f's_{k}_items', flow=True)
    blank()
    S('oth_hdr', 'Eliminations and other · Corporate · FAS/CAS operating adjustment · acquisition accounting adjustments', 'block',
      note='BELOW THE SEGMENTS — eliminations & other (intercompany eliminations and smaller operations), corporate expenses, the FAS/CAS operating adjustment (CAS pension cost recovered in Raytheon pricing less FAS service cost), acquisition accounting adjustments (acquired-intangible and PP&E fair-value amortization)')
    S('el_rev', '  Eliminations and other — net sales (inter-segment eliminations and smaller operations)', 'line', 'm', data='s_elim_rev', flow=True,
      qe=lambda: f'={V("el_rev_p")}*{V("g_segrev")}', ae=lambda: f'={V("el_rev_p")}*{V("g_segrev")}')
    S('el_rev_p', '    Eliminations and other % of Σ segment sales', 'pct', 'pct', all=ratio('el_rev', 'g_segrev'),
      qe=lambda: f'=IFERROR({ACT("el_rev")}/{ACT("g_segrev")},0)', ae_in=V0['elim_p'], note='Q4/26E: 9M 2026 ratio; 2027E+: input (2024–26 about −2.6% to −2.8%).')
    S('el_op', '  Eliminations and other — operating profit (GAAP)', 'line', 'm', data='s_elim_op', flow=True, fc=lambda: f'={V("el_aop")}-{V("el_items")}')
    S('el_items', '    Adjustments in eliminations and other (restructuring − significant items; incl. items not allocated to segments)', 'line', 'm', data='s_elim_items', flow=True, fc=lambda: '=0',
      note=('History = published adjusted OP of eliminations and other − GAAP where published; otherwise the consolidated adjustments not allocated to a segment '
            '(restructuring + acquisition accounting − significant items − Σ segment and corporate items; pre-2013 UTC releases gave no segment adjusted figures). Forecast nil.'))
    S('el_aop', '  Eliminations and other — adjusted operating profit', 'line', 'm', data='s_elim_aop', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("el_op")}),{V("el_op")}+N({V("el_items")}),"")', qe=lambda: f'={PT("pt_elim")}', ae_in=V0['elim_aop'],
      note='Q4/26E point estimate; 2027E+ input (9M 2026 $17m, 2025 $(19)m).')
    S('co_op', '  Corporate expenses and other unallocated items (GAAP; negative = cost)', 'line', 'm', data='s_corp_op', flow=True,
      fc=lambda: f'={V("co_aop")}-{V("co_items")}')
    S('co_items', '    Adjustments in corporate (restructuring − significant items such as litigation and tax-audit matters)', 'line', 'm', data='s_corp_items', flow=True,
      qe=lambda: f'={QEc("d_restr")}*{V0["restr_mix"]["corp"]}', ae=lambda: f'={V("d_restr")}*{V0["restr_mix"]["corp"]}',
      note=f'History = published adjusted corporate − GAAP corporate. Forecast = total restructuring × {V0["restr_mix"]["corp"]:.0%} (corporate share; assumption).')
    S('co_aop', '  Adjusted corporate expenses and other unallocated items', 'line', 'm', data='s_corp_aop', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("co_op")}),{V("co_op")}+N({V("co_items")}),"")', qe=lambda: f'={PT("pt_corp")}', ae_in=V0['corp_aop'],
      note='Q4/26E point estimate; 2027E+ input (2025 $(136)m; 9M 2026 $(59)m).')
    S('fc_adj', '  FAS/CAS operating adjustment (CAS pension & PRB expense recovered in Raytheon contracts − FAS service cost; income +)', 'line', 'm', data='s_fascas', flow=True,
      qe=lambda: f'={PT("pt_fascas")}', ae_in=V0['fascas'],
      note='Raytheon-legacy pension cost recognised under U.S. government Cost Accounting Standards is recovered through contract pricing; the segment measure uses CAS cost, consolidated GAAP uses FAS service cost. Q4/26E point estimate; 2027E+ input (declining as the CAS cost of closed plans runs off; assumption).')
    S('aa_adj', '  Acquisition accounting adjustments (amortization of acquired intangibles and PP&E fair-value step-ups; negative)', 'line', 'm', data='s_acqadj', flow=True,
      qe=lambda: f'=-{PT("pt_acqadj")}', ae=lambda: f'=-{V("d_acq")}',
      note='Separate line in the segment table from Q2-20 (Raytheon merger); before 2020 the amortization sat inside the UTC segments. Forecast from the amortization schedule (cost drivers).')
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — bolt-ons, unallocated; deals closed from 2027E)', 'block',
      note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention; margin after amortization of the acquired intangibles')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=2.5, e26_in=0.0, note='Assumption (defense and aerospace component bolt-ons ~2–3x sales).')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.05)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}', note='Mid-year convention.')
    S('m_m', '  Adjusted operating margin of acquired businesses %', 'driver', 'pct', e26_in=0.0, ae_in=0.12)
    S('m_oi', '  Adjusted operating profit from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.10)
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.40, note='Raytheon merger PPA (2020): intangibles $19.1bn of $33.1bn consideration (58%); Rockwell Collins (2018): $12.8bn of $30.6bn EV (42%).')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=15)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (acquisition accounting adjustment)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)',
      note='RTX adjusts acquired-intangible amortization out of adjusted results; the acquired margin above is before that amortization.')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group Total — net sales & adjusted operating profit (segment build) → 2026 outlook calibration', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_segrev', 'Σ segment net sales (incl. inter-segment; legacy segments in their years)', 'line', 'm',
      hist=lambda: ISN('col_rev', '+'.join(f'N({V(s + "_rev")})' for s in SEGK + LEG_IN_TOTAL)),
      fc=lambda: '=' + '+'.join(V(s + '_rev') for s in SEGK))
    S('g_rev', 'Net sales (segment build)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("col_rev")}),{V("g_segrev")}+N({V("el_rev")}),{V("is_rev")})',
      fc=lambda: f'={V("g_segrev")}+{V("el_rev")}+N({V("m_rev")})', note='Σ segment sales + eliminations and other (+ future acquisitions from 2027E).')
    S('g_rev_g', '  Net sales y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs consolidated net sales (should be 0; ±1 rounding)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=1.5,0,ROUND({V("g_rev")}-{V("is_rev")},0)),"")')
    S('g_segaop', 'Σ adjusted segment operating profit (company "adjusted segment operating profit")', 'line', 'm',
      hist=lambda: ISN('col_aop', '+'.join(f'N({V(s + "_aop")})' for s in SEGK + LEG_IN_TOTAL)),
      fc=lambda: '=' + '+'.join(V(s + '_aop') for s in SEGK) + f'+N({V("m_oi")})')
    S('g_segaop_m', '  Adjusted segment operating margin % (on Σ segment sales)', 'pct', 'pct', all=ratio('g_segaop', 'g_segrev'))
    S('g_adj', 'Adjusted operating profit (segment build)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("g_segaop")}),{V("g_segaop")}+N({V("el_aop")})+N({V("co_aop")})+N({V("fc_adj")}),"")',
      note="Σ adjusted segment OP + eliminations & other + corporate + FAS/CAS operating adjustment = RTX adjusted operating profit (company definition); drives the GAAP P&L below.")
    S('g_adjm', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('g_adj', 'is_rev'))
    S('g_adj_g', '  Adjusted operating profit y/y %', 'growth', 'pct', all=growth('g_adj'))
    S('g_chk_adj', '  Check: segment build vs adjusted operating profit bridge (should be 0; ±1 rounding)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_adj")}),ISNUMBER({V("o_adj")})),IF(ABS({V("g_adj")}-{V("o_adj")})<=1.5,0,ROUND({V("g_adj")}-{V("o_adj")},0)),"")')
    S('g_op', 'Σ segment operating profit + eliminations + corporate + FAS/CAS + acquisition accounting adjustments (+ future acquisitions, unallocated; GAAP)', 'line', 'm',
      all=lambda: ISN('col_op', '+'.join(f'N({V(s + "_op")})' for s in SEGK + LEG_IN_TOTAL) + f'+N({V("el_op")})+N({V("co_op")})+N({V("fc_adj")})+N({V("aa_adj")})+N({V("m_oi")})'))
    S('g_chk_op', '  Check: segment table vs consolidated operating profit (should be 0; ±1 rounding)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_op")}),ISNUMBER({V("is_op")})),IF(ABS({V("g_op")}-{V("is_op")})<=1.5,0,ROUND({V("g_op")}-{V("is_op")},0)),"")')
    S('cal_guid', '  Memo: 2026 adjusted sales outlook (scenario end-point, $m)', 'memo', 'm', e26=lambda: '=' + CH(SC['out_sales']), note=V0['rev_guid_note'])
    S('cal_pre', '  Net sales before calibration (Q4/26E helper: Σ customer lines at 9M y/y rates × (1 + inter-segment %) × (1 + eliminations %))', 'line', 'm',
      qe=lambda: '=(1+' + V('el_rev_p') + ')*(' + '+'.join(f'(1+{V(s + "_inter_p")})*(' + '+'.join(f'{P(s + "_" + t)}*(1+{V(s + "_" + t + "_pre")})' for t, _, _, _ in types) + ')' for s, _, _, types, _ in SEG) + ')')
    S('cal_sens', '  Net sales sensitivity to +1.00 of growth (Q4/26E helper)', 'line', 'm',
      qe=lambda: '=(1+' + V('el_rev_p') + ')*(' + '+'.join(f'(1+{V(s + "_inter_p")})*(' + '+'.join(P(s + '_' + t) for t, _, _, _ in types) + ')' for s, _, _, types, _ in SEG) + ')')
    S('cal_g', '  Guidance calibration: Δ y/y growth applied to all customer-type lines (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_guid", E26)}-{ACT("g_rev")}-{V("cal_pre")})/{V("cal_sens")}',
      note='Solves the uniform growth shift (vs 9M 2026 y/y rates) so that 2026E net sales = the adjusted-sales outlook end-point for the active scenario (no significant sales items expected, so adjusted sales = net sales).')
    S('cal_rev_chk', '  Check: 2026E net sales vs outlook end-point (should be 0)', 'check', 'm', e26=lambda: f'=ROUND({V("g_rev")}-{V("cal_guid")},0)')
    S('cal_eps', '  Memo: 2026 adjusted EPS outlook (scenario end-point, $)', 'eps_memo', 'ps', e26=lambda: '=' + CH(SC['out_eps']), note=V0['eps_guid_note'])
    S('cal_ni', '  Adjusted net income attributable required (2026E diluted shares × EPS outlook)', 'memo_calc', 'm', e26=lambda: f'={V("cal_eps")}*{V("e_sh")}')
    S('cal_oi', '  Q4/26E adjusted operating profit required ((required NI − 9M actual + Q4 NCI) ÷ (1 − adjusted tax rate) − non-service pension income + net interest − other)', 'memo_calc', 'm',
      e26=lambda: f'=({V("cal_ni")}-{ACT("e_adjni")}+{QEc("is_nci")})/(1-{PT("pt_etr")})-{QEc("is_nsp")}+{QEc("is_int")}-{QEc("is_othnonop")}')
    S('cal_oi_pre', '  Adjusted operating profit before margin calibration (Q4/26E helper)', 'line', 'm',
      qe=lambda: '=' + '+'.join(f'{V(s + "_rev")}*{V(s + "_m_pre")}' for s in SEGK) + f'+{V("el_aop")}+{V("co_aop")}+{V("fc_adj")}')
    S('cal_segrev', '  Σ segment sales (Q4/26E helper)', 'line', 'm', qe=lambda: '=' + '+'.join(V(s + '_rev') for s in SEGK))
    S('cal_m', '  Guidance calibration: Δ adjusted segment margin (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_oi", E26)}-{V("cal_oi_pre")})/{V("cal_segrev")}',
      note='Solves the uniform segment-margin shift so that 2026E adjusted EPS = the outlook end-point for the active scenario.')
    S('cal_eps_chk', '  Check: 2026E adjusted EPS vs outlook end-point (should be 0.00)', 'check', 'ps', e26=lambda: f'=ROUND({V("e_eps")}-{V("cal_eps")},2)')
    S('cal_org', '  Memo: 2026 organic sales growth outlook (scenario end-point) — information', 'memo', 'pct', e26=lambda: '=' + CH(SC['out_org']))
    S('cal_org_d', '    Model 2026E net sales growth − organic outlook (pp; model growth includes divestitures and FX)', 'memo_calc', 'pct', e26=lambda: f'={V("g_rev_g")}-{V("cal_org")}')
    S('cal_fcf', '  Memo: 2026 free cash flow outlook (scenario end-point, $m) — information, not forced', 'memo', 'm', e26=lambda: '=' + CH(SC['out_fcf']))
    S('cal_fcf_d', '    Model 2026E free cash flow − outlook ($m)', 'memo_calc', 'm', e26=lambda: f'={V("fcf")}-{V("cal_fcf")}')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A, pension & adjusting items', 'block',
      note='COST DRIVERS — inputs that drive forecast cost lines (Q4/26E: point estimates from the outlook; 2027E+: % of sales, schedules or inputs)')
    S('d_dda', '  Depreciation & amortization (cash-flow statement; includes acquisition accounting amortization)', 'line', 'm', data='cf_dda', flow=True,
      qe=lambda: f'={PT("pt_dda")}', ae=lambda: f'={V("d_dep")}+{V("d_acq")}',
      note='Q4/26E point estimate. 2027E+: depreciation & other amortization (% of sales) + acquisition accounting amortization (schedule).')
    S('d_acq', '  Acquisition accounting adjustments — amortization of acquired intangibles & PP&E step-ups', 'line', 'm', flow=True, data='a_acq',
      hist=lambda: f'=IF(ISNUMBER({V("aa_adj")}),-{V("aa_adj")},"")', qe=lambda: f'={PT("pt_acqadj")}', ae=lambda: f'={V("d_acq_sch")}+N({V("m_amort")})',
      note=('History = acquisition accounting adjustments in the adjusted-results reconciliation (from Q2-20; nil before — UTC did not adjust out amortization). The Q2-20 Collins goodwill '
            'impairment ($3,183m) sits in the segment table\'s acquisition-accounting line but is a significant item in the bridge. 2027E+: amortization schedule + future acquisitions.'))
    S('d_acq_sch', '  Acquisition accounting adjustments schedule — intangibles held at 30-Sep-2026 (input)', 'driver', 'm', ae_in=V0['acq_sched'], note=V0['acq_sched_note'])
    S('d_dep', '  Depreciation & other amortization (D&A − acquisition accounting amortization)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("d_dda")}),{V("d_dda")}-N({V("d_acq")}),"")', qe=lambda: f'={V("d_dda")}-{V("d_acq")}', ae=lambda: f'={V("is_rev")}*{V("d_dep_pct")}')
    S('d_dep_pct', '  Depreciation & other amortization % of net sales', 'pct', 'pct', all=ratio('d_dep', 'is_rev'), ae_in=V0['dep_pct'],
      note='2024–26 about 1.9–2.0% of sales; capex running above depreciation (new capacity for GTF MRO and munitions).')
    S('d_sga', '  SG&A % of net sales', 'pct', 'pct', all=ratio('is_sga', 'is_rev'),
      qe=lambda: f'={P("d_sga")}+IFERROR({ACT("is_sga")}/{ACT("is_rev")}-{ACT0("is_sga")}/{ACT0("is_rev")},0)', ae_in=V0['sga_pct'],
      note='Q4/26E: prior-year quarter ratio + 9M 2026 y/y drift; 2027E+ input. Gross profit is implied: operating profit + R&D + SG&A − other income.')
    S('d_rd', '  Company-funded R&D % of net sales', 'pct', 'pct', all=ratio('is_rd', 'is_rev'), qe=lambda: f'=IFERROR({ACT("is_rd")}/{ACT("is_rev")},"")', ae_in=V0['rd_pct'])
    S('d_othinc', '  Other income, net (recurring; input)', 'line', 'm', flow=True, qe=lambda: f'={PT("pt_othinc")}', ae_in=V0['othinc'],
      note='Other income, net (royalties, JV results, gains; 2026 includes IEEPA tariff refunds and investment gains). Input (assumption).')
    S('d_sbc', '  Stock compensation cost (cash-flow statement)', 'line', 'm', data='cf_sbc', flow=True,
      qe=lambda: f'={P("d_sbc")}*(1+IFERROR({ACT("d_sbc")}/{ACT0("d_sbc")}-1,0))', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}',
      note='Q4/26E: prior-year quarter × 9M 2026 y/y; 2027E+: % of net sales. RTX does not adjust out stock compensation.')
    S('d_sbc_pct', '  Stock compensation % of net sales', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_nsp', '  Non-service pension income (income +; below operating profit, non-cash)', 'line', 'm', data='nsp', flow=True,
      qe=lambda: f'={PT("pt_nsp")}', ae_in=V0['nsp'],
      note='Expected return on the ~$50bn of plan assets less interest cost and amortization (ASU 2017-07 presentation from 2018). Q4/26E point estimate; 2027E+ input (2026 run-rate ~$1.4bn, drifting lower as plans de-risk; assumption).')
    S('d_restr', '  Restructuring costs (total, pre-tax; adjusted out)', 'line', 'm', data='a_restr', flow=True, qe=lambda: f'={PT("pt_restr")}', ae_in=V0['ae_restr'],
      note='Severance and facility consolidation across the segments and corporate; 2027E+ input ($200m p.a. assumption; 2025 $257m, 2024 $71m).')
    S('d_sig_h', '  Significant and/or non-recurring items (pre-tax, income +; adjusted out; forecast nil):', 'sub', 'gen')
    S('d_sig_op', '  Net significant items in operating profit (Σ segments, eliminations, corporate)', 'line', 'm', data='a_sig', flow=True, labkey='a_sig_op_lab', fc=lambda: '=0',
      note='Company items: Q3-23 powder metal charge $(2.9)bn, Q2-20 Collins goodwill impairment $(3.2)bn, 2022 Russia charges, portfolio gains / losses, customer bankruptcies, legal matters.')
    S('d_sig_rev', '  Memo: significant items in net sales (Q3-23 powder metal; adjusted sales = net sales − items)', 'memo', 'm', data='a_sig_rev', flow=True, fc=lambda: '=0')
    S('d_sig_nsp', '  Significant items in non-service pension income (pension restructuring, curtailments)', 'line', 'm', data='a_nsp', flow=True, labkey='a_nsp_lab', fc=lambda: '=0')
    S('d_sig_int', '  Significant items in interest expense, net (tax-audit interest, debt extinguishment)', 'line', 'm', data='a_int', flow=True, labkey='a_int_lab', fc=lambda: '=0')
    S('d_sig_oth', '  Significant items in other non-operating income (expense)', 'line', 'm', data='a_oth', flow=True, labkey='a_oth_lab', fc=lambda: '=0')
    S('d_sig_taxd', '  Discrete tax items (tax reform, audit settlements, valuation allowances; income +)', 'line', 'm', data='a_taxd', flow=True, labkey='a_taxd_lab', fc=lambda: '=0')
    S('d_sig_nci', '  Items attributable to noncontrolling interests (income +)', 'line', 'm', data='a_nci', flow=True, labkey='a_nci_lab', fc=lambda: '=0')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF OPERATIONS (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (operating profit = adjusted operating profit − restructuring − acquisition accounting adjustments + significant items; gross profit implied)')
    S('is_rev', 'Net sales', 'total', 'm', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the segment build.')
    S('is_rev_p', '  of which products', 'memo', 'm', data='rev_prod', flow=True)
    S('is_rev_s', '  of which services', 'memo', 'm', data='rev_serv', flow=True)
    S('is_cogs', 'Cost of sales (products and services)', 'line', 'm', data='cogs', flow=True, fc=lambda: f'={V("is_rev")}-{V("is_gp")}')
    S('is_gp', 'Gross profit', 'line_b', 'm', hist=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_rev")}-{V("is_cogs")},"")',
      fc=lambda: f'={V("is_op")}+{V("is_sga")}+{V("is_rd")}-{V("is_othinc")}', note='Forecast = operating profit + R&D + SG&A − other income (implied by the adjusted build).')
    S('is_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('is_rd', 'Research and development (company-funded)', 'line', 'm', data='rnd', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_rd")}')
    S('is_sga', 'Selling, general and administrative', 'line', 'm', data='sga', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_sga")}')
    S('is_othinc', 'Other income, net (income +)', 'line', 'm', data='oth_inc', flow=True, fc=lambda: f'={V("d_othinc")}',
      labkey='oth_op_labels', note='Forecast = recurring other income input (significant items are nil in the forecast). Includes other operating lines shown separately in some years (cell comments).')
    S('is_op', 'Operating profit', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_gp")}),{V("is_gp")}-{V("is_rd")}-{V("is_sga")}+N({V("is_othinc")}),"")',
      fc=lambda: f'={V("g_adj")}-{V("d_restr")}-{V("d_acq")}+{V("d_sig_op")}',
      note='Forecast = adjusted operating profit − restructuring − acquisition accounting adjustments + significant items.')
    S('is_op_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('is_nsp', 'Non-service pension income (income +; from 2018)', 'line', 'm', data='nsp', flow=True, fc=lambda: f'={V("d_nsp")}+{V("d_sig_nsp")}')
    S('is_int', 'Interest expense, net', 'line', 'm', data='int_net', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_cp")}*{V("ds_r_cp")}+{V("ds_fees")}-{P("cf_end")}*{V("ds_r_cash")}-{V("d_sig_int")}',
      note='Q4/26E point estimate. 2027E+ = rate × opening notes + rate × opening commercial paper / revolver − yield × opening cash (no circularity).')
    S('is_othnonop', 'Other non-operating income (expense), net (income +)', 'line', 'm', data='oth_nonop', flow=True, fc=lambda: f'={V("d_sig_oth")}')
    S('is_ebt', 'Income from continuing operations before income taxes', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_op")}),{V("is_op")}+N({V("is_nsp")})-{V("is_int")}+N({V("is_othnonop")}),"")')
    S('is_tax', 'Income tax expense', 'line', 'm', data='tax', flow=True, fc=lambda: f'={V("e_adjtax")}+{V("e_taxeff")}-{V("d_sig_taxd")}',
      note='Forecast = adjusted tax (adjusted pre-tax income × adjusted rate) − tax effect of the adjusting items (marginal rate) − discrete items.')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'))
    S('is_cont', 'Net income from continuing operations (incl. noncontrolling interests)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_disc', 'Income (loss) from discontinued operations, net of tax (Sikorsky 2015; Otis & Carrier 2020; earlier UTC disposals)', 'line', 'm', data='disc', flow=True, fc=lambda: '=0')
    S('is_ni_tot', 'Net income', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_cont")}),{V("is_cont")}+N({V("is_disc")}),"")')
    S('is_nci', 'Less: noncontrolling interest in subsidiaries\' earnings', 'line', 'm', data='nci', flow=True,
      qe=lambda: f'={PT("pt_nci")}', ae=lambda: f'={V("is_cont")}*{V("is_nci_p")}',
      note='Q4/26E point estimate; 2027E+ = % of net income from continuing operations (2024–26 about 4–5%: Pratt & Whitney and Raytheon JV partners).')
    S('is_nci_p', '  NCI % of net income from continuing operations', 'pct', 'pct', all=ratio('is_nci', 'is_cont'), ae_in=V0['nci_pct'])
    S('is_ni', 'Net income attributable to common shareowners', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ni_tot")}),{V("is_ni_tot")}-N({V("is_nci")}),"")')
    S('is_ni_chk', '  Check: net income attributable vs reported (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=1.5,0,ROUND({V("is_ni")}-{V("is_ni_pub")},0)),"")')
    S('is_ni_pub', '  Memo: net income attributable to common shareowners as reported', 'memo', 'm', data='ni', flow=True)
    S('is_ni_cont', '  Memo: net income from continuing operations attributable to common shareowners', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_ni")}),{V("is_ni")}-N({V("is_disc")})+N({V("is_disc_nci")}),"")')
    S('is_disc_nci', '  Memo: NCI share of discontinued operations', 'memo', 'm', data='disc_nci', flow=True, fc=lambda: '=0')
    S('is_dda', '  Memo: depreciation & amortization', 'memo_calc', 'm', all=lambda: f'={V("d_dda")}')
    S('is_sbc', '  Memo: stock compensation cost', 'memo_calc', 'm', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share attributable to common shareowners)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={B1("bs_shares")}-${E26}${R["bb_sh"]}*0.5+${E26}${R["bb_iss"]}*0.5', ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q4/26E: shares outstanding at 30-Sep-2026 − Q4 buybacks (mid-quarter) + equity-plan issuance. 2027E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")', note='Net income attributable ÷ weighted diluted shares (±$0.01 vs reported).')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_cont', 'EPS – diluted, continuing operations ($)', 'eps', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni_cont")}/{V("sh_dil")},""),"")')
    S('eps_pub', '  Memo: EPS – diluted as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0151,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('dps', '  Dividends declared per share ($)', 'line', 'ps', data='dps', flow=True, qe_in=V0['dps_q'], ae=lambda: f'={P("dps")}*(1+{V("dps_g")})',
      note='Quarterly dividend $0.73 from Q2-26 (raised ~8% each May). 2027E+: prior year × (1 + growth).')
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'])
    blank()

    # ------------------------------------------------------------------ RECON 1: OP -> adjusted OP
    S('sec_r1', 'RECONCILIATION: OPERATING PROFIT → ADJUSTED OPERATING PROFIT (company definition)', 'section',
      note='ADJUSTED OPERATING PROFIT — per the release reconciliations: operating profit excluding restructuring, acquisition accounting adjustments (from 2020) and net significant and/or non-recurring items; UTC (2013–19) "adjusted operating profit" excluded restructuring and significant items only')
    S('o_op', 'Operating profit (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_op")}')
    S('o_restr', '  (+) Restructuring costs', 'line', 'm', all=lambda: f'={V("d_restr")}')
    S('o_acq', '  (+) Acquisition accounting adjustments', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("d_acq")}),{V("d_acq")},0)')
    S('o_sig', '  (−) Net significant and/or non-recurring items in operating profit (income +)', 'line', 'm', all=lambda: f'=-N({V("d_sig_op")})')
    S('o_tot', '  Total adjustments (pre-tax)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("o_restr")}),{nsum(["o_restr", "o_acq", "o_sig"])},"")')
    S('o_adj', '  = Adjusted operating profit (model bridge)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_tot")},"")',
      note='Rebuilt from the published reconciliation items; forecast = operating profit + forecast adjustments (equals the segment build — check in the Group block).')
    S('o_adj_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company-published adjusted operating profit', 'memo', 'm', data='adj_op_pub', flow=True)
    S('o_chk', '  Check: model bridge vs company-published (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),IF(ABS({V("o_adj")}-{V("o_pub")})<=1.5,0,ROUND({V("o_adj")}-{V("o_pub")},0)),"n/p")')
    S('o_def', '  Definition / basis (company adjusted definition in force)', 'text', 'gen', note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('o_rev', '  Memo: adjusted net sales (company-published; = net sales − significant sales items)', 'memo', 'm', data='adj_rev_pub', flow=True)
    S('o_adj_g', '  Adjusted operating profit y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental adjusted operating margin (Δ adjusted OP / Δ net sales)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: NI -> EBITDA -> adjusted EBITDA
    S('sec_r2', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (model definition; RTX publishes no EBITDA)', 'section',
      note='EBITDA — model definition: net income + taxes + interest expense, net − non-service pension income − other non-operating + D&A = EBITDA; + restructuring − significant items = adjusted EBITDA (acquisition accounting amortization is inside D&A, so it is not added back again); used for leverage and EV / EBITDA')
    S('r_ni', 'Net income (incl. NCI)', 'line_b', 'm', all=lambda: f'={V("is_ni_tot")}')
    S('r_disc', '  (−) Discontinued operations', 'line', 'm', all=lambda: f'=-N({V("is_disc")})')
    S('r_tax', '  (+) Income tax expense', 'line', 'm', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest expense, net', 'line', 'm', all=lambda: f'={V("is_int")}')
    S('r_nsp', '  (−) Non-service pension income', 'line', 'm', all=lambda: f'=-N({V("is_nsp")})')
    S('r_oth', '  (−) Other non-operating income', 'line', 'm', all=lambda: f'=-N({V("is_othnonop")})')
    S('r_gop', '  = Operating profit', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_disc")}+{V("r_tax")}+{V("r_int")}+{V("r_nsp")}+{V("r_oth")},"")')
    S('r_gop_chk', '  Check: vs operating profit (should be 0; ±1 rounding)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_gop")}),ISNUMBER({V("is_op")})),IF(ABS({V("r_gop")}-{V("is_op")})<=1.5,0,ROUND({V("r_gop")}-{V("is_op")},0)),"")')
    S('r_dda', '  (+) Depreciation & amortization', 'line', 'm', all=lambda: f'={V("d_dda")}')
    S('r_ebitda', '  = EBITDA', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_gop")}),ISNUMBER({V("r_dda")})),{V("r_gop")}+{V("r_dda")},"")')
    S('r_adjx', '  (+) Restructuring − significant items in operating profit', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("o_restr")}),{V("o_restr")}+{V("o_sig")},"")')
    S('r_adj', '  = Adjusted EBITDA (model definition)', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda")}),ISNUMBER({V("r_adjx")})),{V("r_ebitda")}+{V("r_adjx")},"")',
      note='Equals adjusted operating profit + depreciation & other amortization (acquisition accounting amortization excluded from both). Used for leverage (net debt / adjusted EBITDA) and EV / EBITDA.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_chk', '  Check: adjusted EBITDA = adjusted OP + depreciation & other amortization (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_adj")}),ISNUMBER({V("o_adj")})),IF(ABS({V("r_adj")}-{V("o_adj")}-N({V("d_dep")}))<=1.5,0,ROUND({V("r_adj")}-{V("o_adj")}-N({V("d_dep")}),0)),"")')
    S('r_ebit_h', 'To adjusted EBIT for NOPAT, ROIC and the DCF:', 'sub', 'gen')
    S('r_ebit', '  Adjusted EBIT (= adjusted operating profit, before acquisition accounting amortization)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("o_adj")}),{V("o_adj")},"")',
      note='RTX adjusted operating profit already excludes acquired-intangible amortization and includes stock compensation and FAS service cost; depreciation-only add-back in the DCF.')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: restructuring costs (cash items adjusted out; deducted in the DCF)', 'memo_calc', 'm', all=lambda: f'=IF(ISNUMBER({V("o_restr")}),{V("o_restr")},"")')
    S('r_fcadj', '  Memo: FAS/CAS operating adjustment inside adjusted EBIT (CAS cost recovered in pricing; cash in the period)', 'memo_calc', 'm', all=lambda: f'=N({V("fc_adj")})')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: NET INCOME ATTRIBUTABLE → ADJUSTED NET INCOME → ADJUSTED EPS (company definition)', 'section',
      note='ADJUSTED EPS — net income attributable + restructuring + acquisition accounting adjustments − net significant items (operating, pension, interest, other) − tax effect − discrete tax items − NCI share; UTC 2006–13: items published pre-tax with the tax effect; adjusted EPS first printed in the Q3-14 release')
    S('e_ni', 'Net income attributable to common shareowners (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('e_disc', '  (−) Discontinued operations attributable to common shareowners', 'line', 'm', all=lambda: f'=-(N({V("is_disc")})-N({V("is_disc_nci")}))',
      note='RTX adjusted EPS is from continuing operations (Sikorsky 2015; Otis / Carrier 2020).')
    S('e_op', '  (+) Adjustments in operating profit (restructuring + acquisition accounting − significant items; bridge above)', 'line', 'm', all=lambda: f'={V("o_tot")}')
    S('e_nsp', '  (−) Significant items in non-service pension income (income +)', 'line', 'm', all=lambda: f'=-N({V("d_sig_nsp")})')
    S('e_int', '  (−) Significant items in interest expense, net (income +)', 'line', 'm', all=lambda: f'=-N({V("d_sig_int")})')
    S('e_oth', '  (−) Significant items in other non-operating income (income +)', 'line', 'm', all=lambda: f'=-N({V("d_sig_oth")})')
    S('e_taxeff', '  (−) Tax effect of the adjustments', 'line', 'm', flow=True,
      hist=lambda: (f'=IF(NOT(ISNUMBER({V("e_ni")})),"",IF(ISNUMBER({V("e_pubni")}),{V("e_pubni")}-{V("e_ni")}-N({V("e_disc")})-N({V("e_op")})-N({V("e_nsp")})-N({V("e_int")})-N({V("e_oth")})-N({V("e_taxd")})-N({V("e_nci")}),'
                    f'IF(N({V("e_taxpub")})=1,-N({V("e_taxstated")}),-(N({V("e_op")})+N({V("e_nsp")})+N({V("e_int")})+N({V("e_oth")}))*{V0["stat_rate_hist"]})))'),
      fc=lambda: f'=-({V("e_op")}+{V("e_nsp")}+{V("e_int")}+{V("e_oth")})*{V("e_mrate")}',
      note=('Historical: published adjusted net income − GAAP net income − items (incl. discrete tax and NCI); where no adjusted net income was published (2006–Q2/14), the tax effect the company stated, '
            f'otherwise the {V0["stat_rate_hist"]:.0%} U.S. statutory rate (flagged). Forecast: items × marginal rate.'))
    S('e_taxstated', '  Memo: tax effect of the items as printed by the company (income +; removed with the opposite sign)', 'memo', 'm', data='a_taxeff', flow=True)
    S('e_taxpub', '  Memo: 1 = tax effect stated by the company in the period', 'memo', 'gen', data='a_taxeff_pub')
    S('e_mrate', '  Marginal tax rate on adjustments (forecast input)', 'driver', 'pct', qe_in=V0['mrate'], ae_in=V0['mrate'],
      note='Implied 2024–26 tax effect ÷ pre-tax items about 20–22% (acquisition amortization partly non-deductible).')
    S('e_taxd', '  (−) Discrete tax items (income +)', 'line', 'm', all=lambda: f'=-N({V("d_sig_taxd")})')
    S('e_nci', '  (−) Items attributable to noncontrolling interests', 'line', 'm', all=lambda: f'=-N({V("d_sig_nci")})')
    S('e_adjni', '  = Adjusted net income attributable (model bridge)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("e_taxeff")}),{V("e_ni")}+{V("e_disc")}+{V("e_op")}+{V("e_nsp")}+{V("e_int")}+{V("e_oth")}+{V("e_taxeff")}+{V("e_taxd")}+{V("e_nci")},"")')
    S('e_pubni', '  Company-published adjusted net income attributable', 'memo', 'm', data='adj_ni_pub', flow=True)
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted EPS – diluted ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted EPS ($)', 'eps_memo', 'ps', data='adj_eps_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0151,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_adjebt', '  Adjusted pre-tax income (adjusted OP + non-service pension income − net interest + other, excl. significant items)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_adj")}),{V("o_adj")}+N({V("is_nsp")})-N({V("d_sig_nsp")})-N({V("is_int")})-N({V("d_sig_int")})+N({V("is_othnonop")})-N({V("d_sig_oth")}),"")')
    S('e_adjtax', '  Adjusted income tax (adjusted pre-tax − adjusted net income − NCI ex items)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_adjni")}),ISNUMBER({V("e_adjebt")})),{V("e_adjebt")}-{V("e_adjni")}-N({V("is_nci")})-N({V("d_sig_nci")}),"")',
      fc=lambda: f'={V("e_adjebt")}*{V("e_rate")}')
    S('e_rate', '  Adjusted effective tax rate', 'pct', 'pct', all=ratio('e_adjtax', 'e_adjebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['adj_etr'],
      note='9M 2026 adjusted rate 17.7%; 2026 outlook ~18%. 2027E+: input (assumption; 2025 18.1%).')
    S('e_rate_pub', '  Memo: company-published adjusted effective tax rate', 'memo', 'pct', data='adj_etr_pub', pctdata=True)
    S('e_def', '  Definition / basis (company adjusted EPS definition)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Net sales y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_col', '  Collins Aerospace sales y/y %', 'growth', 'pct', all=growth('col_rev'))
    S('gm_pw', '  Pratt & Whitney sales y/y %', 'growth', 'pct', all=growth('pw_rev'))
    S('gm_rtn', '  Raytheon sales y/y %', 'growth', 'pct', all=growth('rtn_rev'))
    S('gc_aero', '  Contribution to net sales growth — Collins + Pratt & Whitney (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR((N({V("col_rev")})+N({V("pw_rev")})-N({P("col_rev")})-N({P("pw_rev")}))/{P("is_rev")},"")' if CTX.col.prior else None))
    S('gc_oth', '  Contribution to net sales growth — Raytheon, legacy UTC segments & eliminations (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("is_rev")}-{P("is_rev")})/{P("is_rev")}-{V("gc_aero")},"")' if CTX.col.prior else None))
    S('gm_adjop', '  Adjusted operating profit y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating profit (GAAP) y/y %', 'growth', 'pct', all=growth('is_op'))
    S('gm_ni', '  Net income attributable y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('gm_adjop_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_inc', '  Incremental adjusted operating margin (Δ adjusted OP / Δ net sales)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_sga', '  SG&A % of net sales', 'pct', 'pct', all=ratio('is_sga', 'is_rev'))
    S('gm_rd', '  R&D % of net sales', 'pct', 'pct', all=ratio('is_rd', 'is_rev'))
    S('gm_bl', '  Memo: company backlog ($bn; commercial + defense)', 'memo', 'bn', data='k_bl_tot')
    S('gm_bl_c', '    of which commercial ($bn)', 'memo', 'bn', data='k_bl_com')
    S('gm_bl_d', '    of which defense ($bn)', 'memo', 'bn', data='k_bl_def')
    S('gm_book', '  Memo: defense bookings ($bn, period)', 'memo', 'bn', data='k_book_def')
    S('gm_org', '  Memo: organic sales growth % (company-published)', 'memo', 'pct', data='k_org', pctdata=True)
    S('gm_rc_rev', '  Memo: net sales as recast in a later filing (continuing operations / new segment basis) — periods kept as reported', 'memo', 'm', data='rc_rev', flow=True)
    S('gm_rc_op', '  Memo: operating profit as recast in a later filing', 'memo', 'm', data='rc_op', flow=True)
    S('gm_rc_eps', '  Memo: adjusted EPS as recast in a later filing ($)', 'memo', 'ps', data='rc_adj_eps')
    blank()
