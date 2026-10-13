"""Row specification of the FICO Model sheet, part 1 (MLM template layout and process):
segment x revenue-stream build (Scores: B2B / B2C; Software: platform / non-platform / professional services) -> segment
operating income at the segment margin -> + unallocated corporate expenses = non-GAAP operating income (model measure; FICO's
segment basis) -> M&A lever -> group total & FY26 guidance calibration -> cost drivers & adjusting items -> income statement ->
GAAP-to-non-GAAP bridges -> growth & margins."""
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
def ACT(key): return f'SUM({Q1}{R[key]}:{Q3}{R[key]})'    # 9M FY26 actual (Q1-Q3/26)
def ACT0(key): return f'SUM({PQ1}{R[key]}:{PQ3}{R[key]})' # 9M FY25 actual (Q1-Q3/25)
def B1(key): return f'{LQ}{R[key]}'                       # 30-Jun-2026 balance
def CHK(a, b, tol=0.15, nd=1, na='""'):
    return lambda: f'=IF(AND(ISNUMBER({V(a)}),ISNUMBER({V(b)})),IF(ABS({V(a)}-{V(b)})<={tol},0,ROUND({V(a)}-{V(b)},{nd})),{na})'

SEG = [('sc', 'Scores', 'SC', [('b2b', 'B2B scores (FICO Scores sold to lenders through the credit bureaus; mortgage, auto, card, personal loans)', 'k_b2b'),
                               ('b2c', 'B2C scores (myFICO.com subscriptions; royalties on scores sold to consumers through the bureaus)', 'k_b2c')], 's_sc_rev', 's_sc_oi'),
       ('sw', 'Software', 'SW', [('plat', 'Platform software (FICO Platform: SaaS / cloud decisioning)', 'k_plat'),
                                 ('nonplat', 'Non-platform software (on-premises & SaaS point solutions: fraud, originations, customer management)', 'k_nonplat'),
                                 ('ps', 'Professional services', 'rev_ps')], 's_sw_rev', 's_sw_oi')]
LINES = [f'{s}_{t}' for s, _, _, ts, _, _ in SEG for t, _, _ in ts]
SEGK = [s for s, *_ in SEG]
ITEMS = ['d_sbc', 'd_amort', 'd_restr', 'd_gain']

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = FY26 guidance (point guidance: high = mid = low).'))
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
    # ------------------------------------------------------------------ SEGMENT BUILD
    S('sec_seg', 'SEGMENT P&L — SCORES · SOFTWARE (revenue streams × segment operating margin)', 'section',
      note='SEGMENT BUILD — modelling logic (revenue streams → segment revenue → segment operating income at the segment margin → + unallocated corporate expenses = non-GAAP operating income → GAAP P&L)')
    blank()
    descr = {'sc': 'Scores (B2B and B2C scoring; "Scoring Solutions" product-line segment in FY2006–09)',
             'sw': 'Software (= consolidated revenue − Scores: Strategy Machine Solutions + Professional Services + Analytic Software Tools to FY2009; Applications + Tools / Decision Management Software FY2010–Q3/21; Software from FY2021)'}
    for s, title, code, types, pub, earn in SEG:
        S(f'{s}_hdr', descr[s], 'block', note=f'{title.upper()} — modelling logic')
        for t, tl, dk in types:
            key = f'{s}_{t}'
            S(key, f'  {tl}', 'line', 'm1', data=dk, flow=True,
              qe=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})', ae=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})',
              note=('Revenue streams from the 10-Q / 10-K MD&A tables (first published in the FY2021 10-K: FY2019–21 annual; FY2021 quarters from the FY2022 10-Q comparatives; '
                    'Q4 = fiscal year − nine months). Q4/26E: prior-year quarter × (1 + growth). 2027E+: prior year × (1 + scenario lever).') if t == types[0][0] else None)
            S(key + '_g', '    y/y %', 'growth', 'pct', all=growth(key),
              qe=lambda key=key: f'={V(key + "_pre")}+{QEa("cal_g")}',
              ae=lambda key=key, code=code, t=t: '=' + CH(SC[f'{code}_{t.upper()}'][CTX.col.year]),
              note='Q4/26E: 9M FY26 y/y growth of the stream + revenue-guidance calibration Δ (Group block). 2027E–2031E: scenario lever (Bull/Base/Bear table →).' if t == types[0][0] else None)
            S(key + '_pre', '    Q4/26E growth before revenue calibration (9M FY26 y/y)', 'driver', 'pct',
              qe=lambda key=key: f'=IFERROR({ACT(key)}/{ACT0(key)}-1,0)')
        first = [f'{s}_{t}' for t, _, _ in types]
        S(f'{s}_rev', f'  {title} — segment revenue', 'line_b', 'm1',
          hist=lambda s=s, first=first: f'=IF(AND({",".join(f"ISNUMBER({V(k)})" for k in first)}),{"+".join(V(k) for k in first)},{V(s + "_pub")})',
          fc=lambda s=s, first=first: '=' + '+'.join(V(k) for k in first),
          note='History: Σ revenue streams where all are published, otherwise segment revenue as reported.' if s == 'sc' else None)
        S(f'{s}_rev_g', '  Segment revenue y/y %', 'growth', 'pct', all=growth(f'{s}_rev'))
        S(f'{s}_mix', '  % of total revenue', 'pct', 'pct', all=ratio(f'{s}_rev', 'g_rev'))
        if s == 'sc':
            S('sc_b2b_p', '  B2B % of Scores revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("sc_b2b")}),IFERROR({V("sc_b2b")}/{V("sc_rev")},""),"")')
            S(f'{s}_pub', '  Memo: Scores segment revenue as reported (segment note)', 'memo', 'm1', data=pub, flow=True)
        else:
            S('sw_plat_p', '  Platform % of on-premises & SaaS software revenue', 'pct', 'pct',
              all=lambda: f'=IF(ISNUMBER({V("sw_plat")}),IFERROR({V("sw_plat")}/({V("sw_plat")}+{V("sw_nonplat")}),""),"")')
            S(f'{s}_pub', '  Memo: Software segment revenue as reported (= consolidated revenue − Scores)', 'memo', 'm1', data=pub, flow=True)
        S(f'{s}_chk', '  Check: revenue streams vs segment revenue (should be 0)', 'check', 'm1',
          hist=lambda s=s, first=first: f'=IF(AND({",".join(f"ISNUMBER({V(k)})" for k in first)},ISNUMBER({V(s + "_pub")})),IF(ABS({V(s + "_rev")}-{V(s + "_pub")})<=0.15,0,ROUND({V(s + "_rev")}-{V(s + "_pub")},1)),"")')
        S(f'{s}_oi', f'  {title} segment operating income', 'line', 'm1', data=earn, flow=True,
          qe=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}', ae=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}',
          note=('Segment operating income as reported (company measure: excludes share-based compensation, amortization, restructuring & acquisition costs and unallocated corporate '
                'expenses; FY2006–09 segment results were after amortization and corporate costs). Forecast = segment revenue × segment margin.') if s == 'sc' else None)
        S(f'{s}_m', '  Segment operating margin %', 'pct', 'pct', all=ratio(f'{s}_oi', f'{s}_rev'),
          qe=lambda s=s: f'={V(s + "_m_pre")}+{QEa("cal_m")}', ae=lambda s=s, code=code: '=' + CH(SC[f'{code}_M'][CTX.col.year]),
          note='Q4/26E: margin before calibration + non-GAAP-EPS-guidance calibration Δ (Group block). 2027E+: scenario lever.' if s == 'sc' else None)
        S(f'{s}_m_pre', '  Q4/26E margin before EPS calibration (prior-year quarter + 9M FY26 y/y drift)', 'driver', 'pct',
          qe=lambda s=s: f'={P(s + "_m")}+IFERROR({ACT(s + "_oi")}/{ACT(s + "_rev")}-{ACT0(s + "_oi")}/{ACT0(s + "_rev")},0)')
        S(f'{s}_inc', '  Incremental segment margin (Δ operating income / Δ revenue)', 'pct', 'pct', all=incr(f'{s}_oi', f'{s}_rev'))
        if s == 'sw':
            S('leg_h', '  Legacy software segments (as originally reported; replaced by "Software" in the FY2021 10-K):', 'sub', 'gen')
            for k, lab in (('sms', 'Strategy Machine Solutions (FY2006–09)'), ('pserv', 'Professional Services (FY2006–09)'),
                           ('app', 'Applications (FY2010–Q3/21)'), ('tools', 'Analytic Software Tools (FY2006–09) / Tools (FY2010–16)'),
                           ('dms', 'Decision Management Software (FY2016–Q3/21)')):
                S(f'leg_{k}_rev', f'    {lab} — revenue', 'memo', 'm1', data=f's_leg_{k}_rev', flow=True)
                S(f'leg_{k}_oi', f'    {lab} — segment operating income', 'memo', 'm1', data=f's_leg_{k}_oi', flow=True)
            LEGR = ['leg_sms_rev', 'leg_pserv_rev', 'leg_app_rev', 'leg_tools_rev', 'leg_dms_rev']
            S('leg_chk', '    Check: legacy software segments vs Software revenue (should be 0)', 'check', 'm1',
              hist=lambda: (f'=IF(OR({",".join(f"ISNUMBER({V(k)})" for k in LEGR)}),IF(ABS({nsum(LEGR)}-{V("sw_pub")})<=0.15,0,ROUND({nsum(LEGR)}-{V("sw_pub")},1)),"")'))
        blank()
    S('co_hdr', 'Unallocated corporate expenses (corporate functions; allocated to the segments in FY2006–09)', 'block',
      note='CORPORATE — unallocated corporate expenses (negative = cost); share-based compensation, amortization and restructuring are not allocated (adjusting items below)')
    S('corp', '  Unallocated corporate expenses', 'line', 'm1', data='s_corp', flow=True,
      qe=lambda: f'={P("corp")}*(1+{V("corp_g")})', ae=lambda: f'={V("is_rev")}*{V("corp_pct")}',
      note='MD&A segment operating-income summary. Q4/26E: prior-year quarter × (1 + 9M FY26 y/y). 2027E+: % of revenue (scenario-neutral input).')
    S('corp_g', '  Unallocated corporate expenses y/y %', 'growth', 'pct', all=growth('corp'), qe=lambda: f'=IFERROR({ACT("corp")}/{ACT0("corp")}-1,0)')
    S('corp_pct', '  Unallocated corporate expenses % of revenue', 'pct', 'pct', all=ratio('corp', 'is_rev'), ae_in=V0['corp_pct'],
      note=V0['corp_note'])
    blank()
    S('mx_hdr', 'Revenue mix & growth contribution (outputs)', 'block', note='MIX — outputs')
    S('gc_sc', '  Contribution to total revenue growth — Scores (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("sc_rev")}-{P("sc_rev")})/{P("g_rev")},"")' if CTX.col.prior else None))
    S('gc_sw', '  Contribution to total revenue growth — Software (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("sw_rev")}-{P("sw_rev")})/{P("g_rev")},"")' if CTX.col.prior else None))
    S('gc_chk', '  Check: Scores + Software contributions vs total revenue growth (should be 0)', 'check', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("gc_sc")}),ISNUMBER({V("g_rev_g")})),IF(ABS({V("gc_sc")}+{V("gc_sw")}+IFERROR({V("m_rev")}/{P("g_rev")},0)-{V("g_rev_g")})<0.0005,0,{V("gc_sc")}+{V("gc_sw")}-{V("g_rev_g")}),"")'
                   if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — software bolt-ons, unallocated; deals closed from 2027E)', 'block',
      note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=6.0, e26_in=0.0, note='Assumption (software bolt-ons ~5–8x revenue); FICO has spent little on acquisitions since FY2014.')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.08)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}', note='Mid-year convention.')
    S('m_m', '  Operating margin of acquired businesses (before amortization) %', 'driver', 'pct', e26_in=0.0, ae_in=0.20)
    S('m_oi', '  Operating income from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.02)
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.30, note='Assumption for software targets (technology and customer relationships).')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=8)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (adjusted out of non-GAAP)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)',
      note='FICO excludes amortization of acquired intangibles from its non-GAAP measures.')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group Total — revenue & non-GAAP operating income (segment build) → FY26 guidance calibration', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Revenue (segment build)', 'total', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("sc_rev")}),{V("sc_rev")}+{V("sw_rev")},{V("is_rev")})',
      fc=lambda: f'={V("sc_rev")}+{V("sw_rev")}+N({V("m_rev")})', note='Σ segment revenue (+ future acquisitions from 2027E).')
    S('g_rev_g', '  Revenue y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs consolidated revenue (should be 0)', 'check', 'm1', all=CHK('g_rev', 'is_rev'))
    S('g_adj', 'Non-GAAP operating income (segment build: segment operating income + unallocated corporate)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("sc_oi")}),{V("sc_oi")}+{V("sw_oi")}+{V("corp")}+N({V("m_oi")}),"")',
      note="Σ segment operating income + unallocated corporate expenses (+ future acquisitions). Model measure: FICO publishes no non-GAAP operating income; = GAAP operating income + its non-GAAP adjusting items. Drives the GAAP P&L below.")
    S('g_adjm', '  Non-GAAP operating margin %', 'pct', 'pct', all=ratio('g_adj', 'is_rev'))
    S('g_adj_g', '  Non-GAAP operating income y/y %', 'growth', 'pct', all=growth('g_adj'))
    S('g_chk_adj', '  Check: segment build vs non-GAAP operating income bridge (should be 0)', 'check', 'm1', all=CHK('g_adj', 'o_adj'))
    S('cal_guid', '  Memo: FY26 revenue guidance (scenario end-point)', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_rev']), note=V0['rev_guid_note'])
    S('cal_pre', '  Revenue before calibration (Q4/26E helper)', 'line', 'm1', qe=lambda: '=' + '+'.join(f'{P(k)}*(1+{V(k + "_pre")})' for k in LINES))
    S('cal_sens', '  Revenue sensitivity to +1.00 of growth (Q4/26E helper)', 'line', 'm1', qe=lambda: '=' + '+'.join(P(k) for k in LINES))
    S('cal_g', '  Guidance calibration: Δ y/y growth applied to all revenue streams (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_guid", E26)}-{ACT("g_rev")}-{V("cal_pre")})/{V("cal_sens")}',
      note='Solves the uniform growth shift (vs 9M FY26 y/y rates) so that FY26 revenue = the guidance end-point for the active scenario.')
    S('cal_rev_chk', '  Check: FY26 revenue vs guidance end-point (should be 0)', 'check', 'm1', e26=lambda: f'=ROUND({V("g_rev")}-{V("cal_guid")},1)')
    S('cal_eps', '  Memo: FY26 non-GAAP EPS guidance (scenario end-point, $)', 'eps_memo', 'ps', e26=lambda: '=' + CH(SC['out_eps']), note=V0['eps_guid_note'])
    S('cal_ni', '  Non-GAAP net income required (FY26E diluted shares × EPS guidance)', 'memo_calc', 'm1', e26=lambda: f'={V("cal_eps")}*{V("e_sh")}')
    S('cal_oi', '  Q4/26E non-GAAP operating income required ((NI − 9M actual) ÷ (1 − Q4 non-GAAP tax rate) + Q4 net interest − other income)', 'memo_calc', 'm1',
      e26=lambda: f'=({V("cal_ni")}-{ACT("e_adjni")})/(1-{PT("pt_ngtax")})+{QEc("is_int")}-{QEc("is_othinc")}-{QEc("e_nonop")}')
    S('cal_oi_pre', '  Non-GAAP operating income before margin calibration (Q4/26E helper)', 'line', 'm1',
      qe=lambda: '=' + '+'.join(f'{V(s + "_rev")}*{V(s + "_m_pre")}' for s in SEGK) + f'+{V("corp")}')
    S('cal_segrev', '  Segment revenue (Q4/26E helper)', 'line', 'm1', qe=lambda: '=' + '+'.join(V(s + '_rev') for s in SEGK))
    S('cal_m', '  Guidance calibration: Δ segment operating margin (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_oi", E26)}-{V("cal_oi_pre")})/{V("cal_segrev")}',
      note='Solves the uniform segment-margin shift so that FY26 non-GAAP EPS = the guidance end-point for the active scenario.')
    S('cal_eps_chk', '  Check: FY26 non-GAAP EPS vs guidance end-point (should be 0.00)', 'check', 'ps', e26=lambda: f'=ROUND({V("e_eps")}-{V("cal_eps")},2)')
    S('cal_gni', '  Memo: FY26 GAAP net income guidance ($850m, 29-Jul-2026) — information, not forced', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_gni']))
    S('cal_gni_d', '    Model FY26 GAAP net income − guidance (Q4 restructuring of $27m announced 6-Oct-2026 is not in the guidance)', 'memo_calc', 'm1',
      e26=lambda: f'={V("is_ni")}-{V("cal_gni")}')
    S('cal_geps', '  Memo: FY26 GAAP EPS guidance ($) — information', 'eps_memo', 'ps', e26=lambda: '=' + CH(SC['out_geps']))
    S('cal_geps_d', '    Model FY26 GAAP EPS − guidance ($)', 'memo_calc', 'ps', e26=lambda: f'={V("eps_dil")}-{V("cal_geps")}')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A & adjusting items', 'block', note='COST DRIVERS — inputs that drive forecast cost lines (Q4/26E: point estimates; 2027E+: % of revenue or schedules)')
    S('d_dda', '  Depreciation & amortization (cash-flow statement)', 'line', 'm1', data='cf_dda', flow=True,
      qe=lambda: f'={PT("pt_dda")}', ae=lambda: f'={V("is_rev")}*{V("d_dda_pct")}+N({V("m_amort")})',
      note='Includes amortization of capitalized software and of acquired intangibles. 2027E+: % of revenue + future-acquisition amortization.')
    S('d_dda_pct', '  D&A (excl. future-acquisition amortization) % of revenue', 'pct', 'pct', all=ratio('d_dda', 'is_rev'), ae_in=V0['dda_pct'])
    S('d_dep', '  Depreciation & software amortization (D&A − amortization of acquired intangibles)', 'line', 'm1', flow=True,
      all=lambda: f'=IF(ISNUMBER({V("d_dda")}),{V("d_dda")}-N({V("is_amort")}),"")')
    S('d_sga', '  SG&A % of revenue (balancing line of the GAAP cost structure)', 'pct', 'pct', all=ratio('is_sga', 'is_rev'))
    S('d_cogs', '  Cost of revenues % of revenue', 'pct', 'pct', all=ratio('is_cogs', 'is_rev'),
      qe=lambda: f'={P("d_cogs")}+IFERROR({ACT("is_cogs")}/{ACT("is_rev")}-{ACT0("is_cogs")}/{ACT0("is_rev")},0)', ae_in=V0['cogs_pct'],
      note='Q4/26E: prior-year quarter ratio + 9M FY26 y/y drift; 2027E+ input. SG&A is implied: revenue − operating income − other cost lines.')
    S('d_rd', '  Research & development % of revenue', 'pct', 'pct', all=ratio('is_rd', 'is_rev'), qe=lambda: f'=IFERROR({ACT("is_rd")}/{ACT("is_rev")},"")', ae_in=V0['rd_pct'])
    S('d_adj_h', '  Adjusting items (pre-tax; unallocated in the segment summary and excluded from non-GAAP; forecast inputs):', 'sub', 'gen')
    S('d_sbc', '  Share-based compensation', 'line', 'm1', data='adj_sbc', flow=True, qe=lambda: f'={PT("pt_sbc")}', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}',
      note='Q4/26E: FY26 guidance ($188m) − 9M actual. 2027E+: % of revenue. FICO excludes share-based compensation from non-GAAP; the DCF deducts it.')
    S('d_sbc_pct', '  Share-based compensation % of revenue', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_amort', '  Amortization of acquired intangibles (unallocated)', 'line', 'm1', data='adj_amort', flow=True, qe_in=0.0, ae=lambda: f'=N({V("m_amort")})',
      note='Fully amortized during FY2025 (FY2024 $0.9m); 2027E+: future acquisitions only. FY2006–09 amortization sat inside segment results (not adjusted).')
    S('d_restr', '  Restructuring, impairment & acquisition-related charges', 'line', 'm1', data='adj_restr', flow=True,
      qe=lambda: f'={PT("pt_restr")}', ae_in=V0['ae_restr'], note=MAN['restructuring_oct2026']['text'])
    S('d_gain', '  (Gains) / losses on product-line and business sales', 'line', 'm1', data='adj_gain', flow=True, fc=lambda: '=0')
    S('d_othinc', '  Other income (expense), net — excl. interest (input)', 'line', 'm1', qe=lambda: f'={PT("pt_othinc")}', ae_in=V0['othinc'],
      note='FX, investment income on marketable securities and rabbi-trust assets. 9M FY26 $9.9m; input (assumption).')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONDENSED CONSOLIDATED STATEMENTS OF INCOME (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (operating income = non-GAAP operating income − adjusting items; SG&A implied)')
    S('is_rev', 'Total revenues', 'total', 'm1', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the segment build.')
    S('is_rev_lines', '  Memo: revenues by type as reported (label and amount)', 'text', 'gen', data='rev_lines', textdata=True)
    S('is_cogs', 'Cost of revenues', 'line', 'm1', data='cogs', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_cogs")}')
    S('is_rd', 'Research & development', 'line', 'm1', data='rd', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_rd")}')
    S('is_sga', 'Selling, general & administrative', 'line', 'm1', data='sga', flow=True,
      fc=lambda: f'={V("is_rev")}-{V("is_cogs")}-{V("is_rd")}-{V("is_amort")}-{V("is_restr")}-{V("is_othop")}-{V("is_op")}',
      note='Forecast = balancing line (revenue − operating income − other cost lines).')
    S('is_amort', 'Amortization of intangible assets', 'line', 'm1', data='amort_is', flow=True, fc=lambda: f'={V("d_amort")}')
    S('is_restr', 'Restructuring, impairment & acquisition-related', 'line', 'm1', data='restr_is', flow=True, fc=lambda: f'={V("d_restr")}')
    S('is_othop', '(Gains) / losses on product-line asset sales & business divestitures', 'line', 'm1', data='oth_op', flow=True, fc=lambda: f'={V("d_gain")}',
      labkey='oth_op_lab')
    S('is_op', 'Operating income', 'total', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_rev")}-{V("is_cogs")}-{V("is_rd")}-{V("is_sga")}-{V("is_amort")}-{V("is_restr")}-{V("is_othop")},"")',
      fc=lambda: f'={V("g_adj")}-{V("o_tot")}', note='Forecast = non-GAAP operating income − adjusting items (SBC, amortization, restructuring, gains).')
    S('is_op_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('is_op_chk', '  Check: operating income vs reported (should be 0)', 'check', 'm1', all=CHK('is_op', 'is_op_pub'))
    S('is_op_pub', '  Memo: operating income as reported', 'memo', 'm1', data='opinc', flow=True)
    S('is_int', 'Interest expense, net', 'line', 'm1', data='int_net', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_tl")}*{V("ds_r_tl")}+{P("ds_rev")}*{V("ds_r_rev")}+{V("ds_fees")}-{P("cf_end")}*{V("ds_r_cash")}',
      note='Segment note ("unallocated interest expense, net"; FY2006–13 interest expense − interest income). Q4/26E point estimate; 2027E+ = rates × opening balances (no circularity).')
    S('is_othinc', 'Other income (expense), net', 'line', 'm1', data='oth_inc', flow=True, fc=lambda: f'={V("d_othinc")}')
    S('is_ebt', 'Income before income taxes', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_op")}),{V("is_op")}-{V("is_int")}+{V("is_othinc")},"")')
    S('is_tax', 'Provision for income taxes', 'line', 'm1', data='tax', flow=True,
      fc=lambda: f'={V("is_ebt")}-({V("e_adjni")}-{V("e_op")}-{V("e_nonop")}-{V("e_tax")}-{V("e_etb")}-{V("e_taxd")})',
      note='Forecast = pre-tax income − GAAP net income, where GAAP net income = non-GAAP net income − adjusting items − their tax effect − excess tax benefit (bridge below).')
    S('is_etr', '  Effective tax rate (GAAP)', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'))
    S('is_cont', 'Income from continuing operations', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_disc', 'Income (loss) from discontinued operations (FY2007–09)', 'line', 'm1', data='disc', flow=True, fc=lambda: '=0')
    S('is_ni', 'Net income', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_cont")}),{V("is_cont")}+N({V("is_disc")}),"")')
    S('is_ni_chk', '  Check: net income vs reported (should be 0)', 'check', 'm1', all=CHK('is_ni', 'is_ni_pub'))
    S('is_ni_pub', '  Memo: net income as reported', 'memo', 'm1', data='ni', flow=True)
    S('is_dda', '  Memo: depreciation & amortization (total)', 'memo_calc', 'm1', all=lambda: f'={V("d_dda")}')
    S('is_sbc', '  Memo: share-based compensation', 'memo_calc', 'm1', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share — Fair Isaac common stock)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={B1("bs_shares")}-({V("bb_asr", E26)}+{V("bb_sh", E26)})*0.5+{V("bb_iss", E26)}*0.5',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q4/26E: shares outstanding at 30-Jun-2026 − ASR final delivery and Q4 buybacks (mid-quarter) + equity-plan issuance. 2027E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dil', 'Diluted EPS ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")',
      note='Net income / weighted diluted shares (±$0.015 vs reported: shares printed in thousands).')
    S('eps_dil_g', '  Diluted EPS y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: diluted EPS as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.015)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0151,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('dps', '  Dividends paid per share ($; derived = dividends paid ÷ basic shares)', 'line', 'ps',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_div")}),ISNUMBER({V("sh_basic")})),IFERROR(-{V("cf_div")}/{V("sh_basic")},0),"")',
      note='$0.02 per quarter until the dividend was discontinued in FY2017. No dividend assumed.')
    blank()

    # ------------------------------------------------------------------ RECON 1: GAAP OI -> non-GAAP OI
    S('sec_r1', 'RECONCILIATION: OPERATING INCOME → NON-GAAP OPERATING INCOME (model; items FICO excludes, = the unallocated items of its segment summary)', 'section',
      note='NON-GAAP OPERATING INCOME — FICO publishes non-GAAP net income / EPS but no non-GAAP operating income; the items are those in its MD&A segment operating-income summary')
    S('o_op', 'Operating income (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_op")}')
    for k, lab, d in (('o_sbc', '  (+) Share-based compensation', 'd_sbc'), ('o_amort', '  (+) Amortization of acquired intangibles', 'd_amort'),
                      ('o_restr', '  (+) Restructuring, impairment & acquisition-related charges', 'd_restr'),
                      ('o_gain', '  (+) (Gains) / losses on product-line and business sales', 'd_gain')):
        S(k, lab, 'line', 'm1', all=lambda d=d: f'={V(d)}')
    S('o_tot', '  Total adjusting items (pre-tax)', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_sbc")}),{nsum(["o_sbc", "o_amort", "o_restr", "o_gain"])},"")')
    S('o_adj', '  = Non-GAAP operating income (model bridge)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_tot")},"")',
      note='Forecast = operating income + forecast adjusting items (equals the segment build — check in the Group block).')
    S('o_adj_m', '  Non-GAAP operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company segment summary: Σ segment operating income + unallocated corporate expenses', 'memo', 'm1', flow=True,
      all=lambda: f'=IF(ISNUMBER({V("sc_oi")}),{V("sc_oi")}+{V("sw_oi")}+{V("corp")},"")' if CTX.col.kind in HISTK else None)
    S('o_chk', '  Check: model bridge vs company segment summary (should be 0)', 'check', 'm1', hist=CHK('o_adj', 'o_pub', na='"n/p"'))
    S('o_def', '  Definition / basis (segment measure in force)', 'text', 'gen',
      note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('o_adj_g', '  Non-GAAP operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental non-GAAP operating margin (Δ income / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: NI -> EBITDA -> adjusted EBITDA
    S('sec_r2', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (model definitions — FICO publishes no EBITDA)', 'section',
      note='EBITDA — net income + taxes + net interest + D&A; + share-based compensation, restructuring / acquisition charges, (gains) / losses on sales and non-operating items FICO excludes = adjusted EBITDA (model)')
    S('r_ni', 'Net income (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('r_disc', '  (−) Income from discontinued operations', 'line', 'm1', all=lambda: f'=-N({V("is_disc")})')
    S('r_tax', '  (+) Provision for income taxes', 'line', 'm1', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest expense, net', 'line', 'm1', all=lambda: f'={V("is_int")}')
    S('r_dda', '  (+) Depreciation & amortization', 'line', 'm1', all=lambda: f'={V("d_dda")}')
    S('r_ebitda', '  = EBITDA (model)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_ni")}),ISNUMBER({V("r_dda")})),{V("r_ni")}+{V("r_disc")}+{V("r_tax")}+{V("r_int")}+{V("r_dda")},"")')
    S('r_adjx', '  (+) SBC, restructuring / acquisition charges, (gains) / losses on sales, excluded non-operating items', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("o_tot")}),{V("o_tot")}-N({V("o_amort")})+N({V("e_nonop")}),"")')
    S('r_adj', '  = Adjusted EBITDA (model)', 'total', 'm1', all=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda")}),ISNUMBER({V("r_adjx")})),{V("r_ebitda")}+{V("r_adjx")},"")',
      note='Model definition (FICO publishes no EBITDA): excludes share-based compensation, like FICO\'s non-GAAP measures. Used for leverage (net debt / adjusted EBITDA) and EV / EBITDA.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_chk', '  Check: adjusted EBITDA = non-GAAP operating income + other income (ex excluded items) + D&A − acquired amortization (should be 0)', 'check', 'm1',
      all=lambda: (f'=IF(ISNUMBER({V("r_adj")}),IF(ABS({V("r_adj")}-({V("o_adj")}+{V("is_othinc")}+N({V("e_nonop")})+{V("d_dda")}-N({V("o_amort")})))<=0.15,0,'
                   f'ROUND({V("r_adj")}-({V("o_adj")}+{V("is_othinc")}+N({V("e_nonop")})+{V("d_dda")}-N({V("o_amort")})),1)),"")'))
    S('r_ebit_h', 'To adjusted EBITA after share-based compensation (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_dep', '  (−) Depreciation & software amortization', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("d_dep")}),-{V("d_dep")},"")')
    S('r_sbcx', '  (−) Share-based compensation (a real cost; excluded from FICO\'s non-GAAP)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("d_sbc")}),-{V("d_sbc")},"")')
    S('r_ebit', '  = Adjusted EBITA after SBC (before acquired-intangible amortization)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+{V("r_dep")}+{V("r_sbcx")},"")',
      note='Standard NOPAT basis: adjusted EBIT before acquired-intangible amortization − SBC; the DCF also deducts cash restructuring.')
    S('r_ebit_m', '  Adjusted EBITA after SBC margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: restructuring & acquisition-related charges (cash; deducted in the DCF)', 'memo_calc', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_restr")}),{V("o_restr")},"")')
    blank()

    # ------------------------------------------------------------------ RECON 3: non-GAAP EPS
    S('sec_r3', 'RECONCILIATION: NET INCOME / DILUTED EPS → NON-GAAP NET INCOME → NON-GAAP EPS (company definition)', 'section',
      note='NON-GAAP EPS — net income + pre-tax adjusting items (+ excluded non-operating gains) + tax effect of the items + excess tax benefit + discrete tax items = non-GAAP net income')
    S('e_ni', 'Net income (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('e_op', '  (+) Adjusting items (pre-tax; operating-income bridge above)', 'line', 'm1', all=lambda: f'={V("o_tot")}')
    S('e_nonop', '  (+) Non-operating items excluded (realized gain on a cost-method investment FY2018–19)', 'line', 'm1', data='adj_nonop', flow=True, fc=lambda: '=0')
    S('e_tax', '  (+) Income tax adjustments (tax effect of the items)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("e_pubni")}),{V("e_pubni")}-{V("e_ni")}-{V("e_op")}-N({V("e_nonop")})-N({V("e_etb")})-N({V("e_taxd")}),IF(ISNUMBER({V("e_ni")}),0,""))',
      fc=lambda: f'=-({V("e_op")}+{V("e_nonop")})*{V("e_trate")}',
      note='Historical: published non-GAAP net income − net income − pre-tax items − excess tax benefit − discrete items (FY2013–Q2/16 the company showed items net of tax; FY2006–12 nothing published: adjusted = GAAP). Forecast: −items × tax rate on items.')
    S('e_trate', '  Tax rate on adjusting items', 'pct', 'pct', all=lambda: f'=IFERROR(-{V("e_tax")}/({V("e_op")}+N({V("e_nonop")})),"")',
      qe=lambda: f'={PT("pt_trate")}', ae_in=V0['trate'])
    S('e_etb', '  (+) Excess tax benefit on share-based awards (excluded from FY2017)', 'line', 'm1', data='ng_co_etb', flow=True,
      qe=lambda: f'={PT("pt_etb")}', ae_in=V0['etb'], note='Q4/26E: FY26 guidance (−$13m) − 9M actual. 2027E+: input (assumption; FY26 guided −$13m).')
    S('e_taxd', '  (+) Discrete tax items (valuation allowance, tax reserves, foreign tax credit, Tax Cuts and Jobs Act)', 'line', 'm1', data='ng_co_taxd', flow=True, fc=lambda: '=0')
    S('e_adjni', '  = Non-GAAP net income (model bridge)', 'total', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("e_tax")}),{V("e_ni")}+{V("e_op")}+N({V("e_nonop")})+{V("e_tax")}+N({V("e_etb")})+N({V("e_taxd")}),"")',
      fc=lambda: f'={V("e_adjebt")}*(1-{V("e_rate")})',
      note='Forecast = non-GAAP pre-tax income × (1 − non-GAAP tax rate); GAAP net income is derived from it (income-statement tax line).')
    S('e_pubni', '  Company-published non-GAAP net income', 'memo', 'm1', data='ng_ni_pub', flow=True)
    S('e_chk_ni', '  Check: model bridge vs company-published non-GAAP net income (should be 0)', 'check', 'm1', hist=CHK('e_adjni', 'e_pubni', na='"n/p"'))
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Non-GAAP diluted EPS ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published non-GAAP diluted EPS ($)', 'eps_memo', 'ps', data='ng_eps_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.015 — shares printed in thousands)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0151,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Non-GAAP EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_adjebt', '  Non-GAAP pre-tax income (non-GAAP operating income − net interest + other income excl. excluded gains)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("o_adj")}),{V("o_adj")}-N({V("is_int")})+N({V("is_othinc")})+N({V("e_nonop")}),"")')
    S('e_adjtax', '  Non-GAAP income tax (pre-tax income − non-GAAP net income)', 'line', 'm1', flow=True,
      all=lambda: f'=IF(AND(ISNUMBER({V("e_adjni")}),ISNUMBER({V("e_adjebt")})),{V("e_adjebt")}-{V("e_adjni")},"")')
    S('e_rate', '  Non-GAAP effective tax rate', 'pct', 'pct', all=ratio('e_adjtax', 'e_adjebt'), qe=lambda: f'={PT("pt_ngtax")}', ae_in=V0['ngtax'],
      note='9M FY26 25.4%; FY2025 24.3%. Forecast input.')
    S('e_def', '  Definition / basis (company non-GAAP definition in force)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Revenue y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_sc', '  Scores segment revenue y/y %', 'growth', 'pct', all=growth('sc_rev'))
    S('gm_sw', '  Software segment revenue y/y %', 'growth', 'pct', all=growth('sw_rev'))
    S('gm_adjop', '  Non-GAAP operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating income (GAAP) y/y %', 'growth', 'pct', all=growth('is_op'))
    S('gm_ni', '  Net income y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Non-GAAP EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_adjop_m', '  Non-GAAP operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_inc', '  Incremental non-GAAP operating margin (Δ income / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_sga', '  SG&A % of revenue', 'pct', 'pct', all=ratio('is_sga', 'is_rev'))
    S('gm_rd', '  R&D % of revenue', 'pct', 'pct', all=ratio('is_rd', 'is_rev'))
    blank()
