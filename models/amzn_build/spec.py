"""Row specification of the AMZN Model sheet, part 1 (MLM template layout and process):
net sales by group of similar products (online stores, physical stores, third-party seller services, subscription services,
advertising services, AWS, other) -> segments (North America and International = the retail groups split by the North America share;
AWS = the AWS group) -> segment operating income at segment margins -> M&A lever -> group total & Q3-26 guidance calibration ->
cost drivers -> income statement -> GAAP-to-adjusted bridges (model definitions: Amazon publishes no adjusted operating income,
EBITDA or EPS) -> growth & margins."""
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
def ACT(key): return f'SUM({Q1}{R[key]}:{Q2}{R[key]})'      # 1H/26 actual
def ACT0(key): return f'SUM({PQ1}{R[key]}:{PQ2}{R[key]})'   # 1H/25 actual
def B1(key): return f'{LQ}{R[key]}'                          # 30-Jun-2026 balance
def A(col, key): return f'${col}${R[key]}'

GRP = [('online', 'Online stores', 'grp_online'), ('physical', 'Physical stores', 'grp_physical'), ('tp', 'Third-party seller services', 'grp_tp'),
       ('subs', 'Subscription services', 'grp_subs'), ('ads', 'Advertising services', 'grp_ads'), ('awsg', 'AWS', 'grp_aws'), ('other', 'Other', 'grp_other')]
LINES = [f'pg_{k}' for k, _, _ in GRP]
RETAIL = [f'pg_{k}' for k, _, _ in GRP if k != 'awsg']
PRIME = ['pg_online', 'pg_tp', 'pg_ads']
SEGS = [('na', 'North America'), ('intl', 'International'), ('aws', 'AWS')]

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of the Q3-26 guidance ranges.'))
    r = 11
    SCEN_ROWS.append((r, 'out_hdr', V0['out_hdr'], 'High', 'Mid', 'Low', V0['out_note'])); r += 1
    for key, lab, (hi, mid, lo), nf, note in V0['outlook']:
        SC[key] = r; SCEN_ROWS.append((r, 'out', lab, hi, mid, lo, note, nf)); r += 1
    r += 1
    SCEN_ROWS.append((r, 'pt_hdr', 'Q3/26E–Q4/26E point estimates (all cases)', None, None, None, None)); r += 1
    for key, lab, vals, nf, note in V0['points']:
        SC[key] = r
        SCEN_ROWS.append((r, 'pt', lab, None, vals, None, note, nf)); r += 1
    r += 1
    SC['LEV'] = r
    SCEN_ROWS.append((r, 'lev', '  Target net debt / adjusted EBITDA (x) — buyback floor 2027E+', *V0['lev'], V0['lev_note']))
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
    # ------------------------------------------------------------------ NET SALES BUILD
    S('sec_rev', 'NET SALES BUILD — GROUPS OF SIMILAR PRODUCTS & SERVICES → SEGMENTS (NORTH AMERICA · INTERNATIONAL · AWS)', 'section',
      note='NET SALES BUILD — modelling logic (product-group net sales → retail groups split NA / International by the NA share; AWS group = AWS segment → segment operating income at segment margins → GAAP P&L)')
    blank()
    S('pg_hdr', 'Net sales by groups of similar products and services (supplemental release table; from Q2-16; advertising services split out of "Other" from Q3-20)', 'block',
      note='PRODUCT GROUPS — modelling logic: Q3/Q4-26E = prior-year quarter × (1 + growth); 2027E+ = prior year × (1 + scenario lever)')
    for k, lab, dk in GRP:
        key = f'pg_{k}'
        retail = key != 'pg_awsg'
        S(key, f'  {lab}', 'line', 'm', data=dk, flow=True,
          qe=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})', ae=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})',
          note=('Latest release presenting each quarter (Amazon re-presents the groups). FY = Σ quarters. Q3/Q4-26E: prior-year quarter × (1 + growth).') if k == 'online' else
               ('Includes advertising services until Q2-20 (split out from Q3-20 in the Q4-21 release).' if k == 'other' else
                ('Whole Foods Market from 28-Aug-2017 (blank before = 0).' if k == 'physical' else None)))
        if retail:
            qe_g = lambda key=key: f'={V(key + "_pre")}' + (f'+{V("pg_prime")}' if key in PRIME else '') + f'+{V("cal_g")}'
            gnote = ('Q3/Q4-26E: Q1-26 y/y (before the Prime Day shift) + Prime Day timing shift (Q3 only; online stores, third-party seller services, advertising) '
                     '+ net-sales guidance calibration Δ (retail groups only). 2027E+: scenario lever.') if k == 'online' else None
        else:
            qe_g = lambda key=key: f'={V(key + "_pre")}'
            gnote = 'Q3/Q4-26E: Q2-26 y/y (+37%, the fastest in 18 quarters; not part of the calibration Δ). 2027E+: scenario lever.'
        code = {'online': 'ONLINE', 'physical': 'PHYS', 'tp': 'TP', 'subs': 'SUBS', 'ads': 'ADS', 'awsg': 'AWS_G', 'other': 'OTHER'}[k]
        S(key + '_g', '    y/y %', 'growth', 'pct', all=growth(key), qe=qe_g,
          ae=lambda code=code: '=' + CH(SC[code][CTX.col.year]), note=gnote)
        if retail:
            S(key + '_pre', '    Q3/Q4-26E growth before calibration (Q1-26 y/y)', 'driver', 'pct', qe=lambda key=key: f'=IFERROR({Q(key, 2026, 1)}/{Q(key, 2025, 1)}-1,0)')
        else:
            S(key + '_pre', '    Q3/Q4-26E growth (Q2-26 y/y)', 'driver', 'pct', qe=lambda key=key: f'=IFERROR({Q(key, 2026, 2)}/{Q(key, 2025, 2)}-1,0)')
    S('pg_prime', '  Prime Day timing shift — pp of growth on online stores, third-party seller services and advertising (Q3/26E)', 'driver', 'pct',
      qe=lambda: (f'={PT("pt_prime")}*{A(P3, "is_rev")}/({A(P3, "pg_online")}+{A(P3, "pg_tp")}+{A(P3, "pg_ads")})' if CTX.col.q == 3 else '=0'),
      note='Guidance (30-Jul-2026): "excluding the impact of Prime Day in both 2025 and 2026, Q3-26 y/y growth would be nearly 400 bp higher" (Prime Day in Q3 in 2025, Q2 in 2026). '
           '−4.0 pp of total Q3 net sales allocated to the Prime-Day-sensitive groups pro rata to Q3-25 revenue.')
    S('pg_resid', '  Not split by product group (before Q2-16)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("pg_online")}),ROUND({V("is_rev")}-({"+".join(V(k) for k in LINES[:4])}+N({V("pg_ads")})+{V("pg_awsg")}+{V("pg_other")}),0),{V("is_rev")})',
      fc=lambda: '=0')
    S('pg_tot', 'Net sales (Σ product groups)', 'total', 'm',
      hist=lambda: '=' + '+'.join(f'N({V(k)})' for k in LINES) + f'+{V("pg_resid")}',
      fc=lambda: '=' + '+'.join(V(k) for k in LINES) + f'+N({V("m_rev")})', note='Σ groups (+ future acquisitions from 2027E).')
    S('pg_chk', '  Check: product groups vs consolidated net sales (should be 0; ±2 rounding)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("pg_online")}),IF(ABS({V("pg_tot")}-{V("is_rev")})<=2.01,0,ROUND({V("pg_tot")}-{V("is_rev")},0)),"")')
    S('pg_ads_mix', '  Advertising services % of net sales', 'pct', 'pct', all=ratio('pg_ads', 'is_rev'))
    S('pg_aws_mix', '  AWS % of net sales', 'pct', 'pct', all=ratio('pg_awsg', 'is_rev'))
    S('pg_svc_mix', '  Third-party seller services + subscriptions + advertising % of net sales', 'pct', 'pct',
      all=lambda: f'=IF(AND(ISNUMBER({V("pg_ads")}),ISNUMBER({V("pg_tp")})),IFERROR(({V("pg_tp")}+{V("pg_subs")}+{V("pg_ads")})/{V("is_rev")},""),"")')
    S('fx_ww', '  Memo: worldwide net sales y/y growth excluding F/X, as published', 'memo', 'pct', data='fx_ww_f')
    blank()

    # ------------------------------------------------------------------ segments
    S('seg_hdr', 'Segments — North America · International · AWS (segment operating income as reported; AWS a segment from Q1-15, recast FY2013–14)', 'block',
      note='SEGMENTS — modelling logic: NA + International = retail product groups; NA share driver; AWS = AWS group; segment OI = net sales × margin')
    S('seg_retail', '  North America + International net sales (= retail product groups)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("seg_na_rev")}),{V("seg_na_rev")}+{V("seg_intl_rev")},"")',
      fc=lambda: '=' + '+'.join(V(k) for k in RETAIL))
    S('seg_na_sh', '  North America share of NA + International net sales', 'pct', 'pct', all=ratio('seg_na_rev', 'seg_retail'),
      qe=lambda: f'={P("seg_na_sh")}+IFERROR({ACT("seg_na_rev")}/{ACT("seg_retail")}-{ACT0("seg_na_rev")}/{ACT0("seg_retail")},0)',
      ae=lambda: f'={P("seg_na_sh")}', note='Q3/Q4-26E: prior-year quarter share + 1H-26 y/y drift. 2027E+: held at the prior-year share.')
    for s, title in SEGS:
        code = s.upper()
        S(f'seg_{s}_rev', f'  {title} — segment net sales', 'line_b', 'm', data=f'{s}_rev', flow=True,
          fc=(lambda: f'={V("seg_retail")}*{V("seg_na_sh")}') if s == 'na' else ((lambda: f'={V("seg_retail")}-{V("seg_na_rev")}') if s == 'intl' else (lambda: f'={V("pg_awsg")}')),
          note={'na': 'U.S. / Canada consumer-facing sales (incl. Whole Foods from Aug-2017). Forecast = retail groups × NA share.',
                'intl': 'Consumer-facing sales outside North America (UK, Germany, Japan, …). Forecast = retail groups − North America.',
                'aws': 'Compute, storage, database, AI services. Forecast = AWS product group.'}[s])
        S(f'seg_{s}_g', '    y/y %', 'growth', 'pct', all=growth(f'seg_{s}_rev'))
        S(f'seg_{s}_oi', f'  {title} — segment operating income', 'line', 'm', data=f'{s}_oi', flow=True,
          fc=lambda s=s: f'={V(f"seg_{s}_rev")}*{V(f"seg_{s}_m")}',
          note=('Segment operating income as reported (from 2016 after allocated stock-based compensation; 2015 restated on that basis in the 2016 releases; '
                'FY2013–14 before SBC). Forecast = segment net sales × margin (excludes special charges, forecast nil).') if s == 'na' else None)
        S(f'seg_{s}_m', '    Segment operating margin %', 'pct', 'pct', all=ratio(f'seg_{s}_oi', f'seg_{s}_rev'),
          qe=lambda s=s: f'={V(f"seg_{s}_m_pre")}+{V("cal_m")}', ae=lambda code=code: '=' + CH(SC[f'{code}_M'][CTX.col.year]),
          note='Q3/Q4-26E: margin before calibration + operating-income guidance calibration Δ (uniform). 2027E+: scenario lever.' if s == 'na' else None)
        S(f'seg_{s}_m_pre', '    Q3/Q4-26E margin before calibration (prior-year quarter ex disclosed special charges + 1H-26 y/y drift)', 'driver', 'pct',
          qe=lambda s=s: (f'=({P(f"seg_{s}_oi")}' + (f'+{P("seg_na_sc")}' if s == 'na' else '') + f')/{P(f"seg_{s}_rev")}'
                                 f'+IFERROR({ACT(f"seg_{s}_oi")}/{ACT(f"seg_{s}_rev")}-{ACT0(f"seg_{s}_oi")}/{ACT0(f"seg_{s}_rev")},0)'))
        S(f'seg_{s}_inc', '    Incremental segment margin (Δ OI / Δ net sales)', 'pct', 'pct', all=incr(f'seg_{s}_oi', f'seg_{s}_rev'))
    S('seg_na_sc', '  Memo: special charges disclosed by segment — North America (FTC legal settlement $2.5bn, Q3-25)', 'memo', 'm', data='sc_na', flow=True, fc=lambda: '=0')
    S('seg_unalloc', '  Unallocated stock-based compensation & other operating expense (not allocated to segments until 2015)', 'line', 'm', data='seg_unalloc', flow=True,
      fc=lambda: '=0')
    S('seg_resid_rev', '  Net sales not on the current segment basis (FY2006–12, Q1–Q4/13: AWS inside North America — legacy memo below)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("seg_na_rev")}),0,{V("is_rev")})')
    S('seg_resid_oi', '  Operating income not on the current segment basis', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("seg_na_oi")}),0,{V("is_oi")})')
    S('seg_chk_rev', '  Check: segment net sales vs consolidated (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ABS(N({V("seg_na_rev")})+N({V("seg_intl_rev")})+N({V("seg_aws_rev")})+{V("seg_resid_rev")}-{V("is_rev")})<=1.01,0,ROUND(N({V("seg_na_rev")})+N({V("seg_intl_rev")})+N({V("seg_aws_rev")})+{V("seg_resid_rev")}-{V("is_rev")},0))')
    S('seg_chk_oi', '  Check: Σ segment OI + unallocated vs consolidated operating income (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ABS(N({V("seg_na_oi")})+N({V("seg_intl_oi")})+N({V("seg_aws_oi")})+N({V("seg_unalloc")})+{V("seg_resid_oi")}-{V("is_oi")})<=1.01,0,ROUND(N({V("seg_na_oi")})+N({V("seg_intl_oi")})+N({V("seg_aws_oi")})+N({V("seg_unalloc")})+{V("seg_resid_oi")}-{V("is_oi")},0))')
    S('seg_chk_aws', '  Check: AWS segment vs AWS product group (should be 0; ±2, FY = Σ quarters)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("seg_aws_rev")}),ISNUMBER({V("pg_awsg")})),IF(ABS({V("seg_aws_rev")}-{V("pg_awsg")})<=2.01,0,ROUND({V("seg_aws_rev")}-{V("pg_awsg")},0)),"")')
    S('leg_h', '  Legacy segment basis — as originally reported (North America incl. AWS, International; segment OI before SBC & other operating expense):', 'sub', 'gen')
    for k, lab in (('na_rev', 'North America net sales (incl. AWS)'), ('na_oi', 'North America segment operating income'),
                   ('intl_rev', 'International net sales'), ('intl_oi', 'International segment operating income'),
                   ('unalloc', 'Unallocated stock-based compensation & other operating expense')):
        S(f'leg_{k}', f'    {lab}', 'memo', 'm', data=f'leg_{k}', flow=True)
    S('leg_chk', '    Check: legacy segments + unallocated vs consolidated operating income (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("leg_na_oi")}),IF(ABS({V("leg_na_oi")}+{V("leg_intl_oi")}+{V("leg_unalloc")}-{V("is_oi")})<=1.01,0,ROUND({V("leg_na_oi")}+{V("leg_intl_oi")}+{V("leg_unalloc")}-{V("is_oi")},0)),"")')
    S('orig_h', '  2015 as originally reported (before the 2016 restatement allocating SBC to segments):', 'sub', 'gen')
    for k, lab in (('na_oi', 'North America'), ('intl_oi', 'International'), ('aws_oi', 'AWS'), ('unalloc', 'Unallocated SBC & other operating expense')):
        S(f'orig_{k}', f'    {lab}', 'memo', 'm', data=f'orig_{k}', flow=True)
    S('mx_h', '  Legacy supplemental net sales (Media / Electronics & other general merchandise / Other; NA + International; 2006–2016):', 'sub', 'gen')
    for k, lab in (('media', 'Media'), ('egm', 'Electronics and other general merchandise'), ('other', 'Other (incl. AWS to 2014)')):
        S(f'mx_{k}', f'    {lab}', 'memo', 'm', data=f'mx_{k}', flow=True)
    S('gc_na', '  Contribution to net sales growth — North America (pp)', 'growth', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("seg_na_rev")}),ISNUMBER({P("seg_na_rev")})),IFERROR(({V("seg_na_rev")}-{P("seg_na_rev")})/{P("is_rev")},""),"")' if CTX.col.prior else None))
    S('gc_intl', '  Contribution to net sales growth — International (pp)', 'growth', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("seg_intl_rev")}),ISNUMBER({P("seg_intl_rev")})),IFERROR(({V("seg_intl_rev")}-{P("seg_intl_rev")})/{P("is_rev")},""),"")' if CTX.col.prior else None))
    S('gc_aws', '  Contribution to net sales growth — AWS (pp)', 'growth', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("seg_aws_rev")}),ISNUMBER({P("seg_aws_rev")})),IFERROR(({V("seg_aws_rev")}-{P("seg_aws_rev")})/{P("is_rev")},""),"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions & strategic investments (M&A lever — unallocated; from 2027E)', 'block',
      note='M&A LEVER — acquired revenue = spend × acquisition share ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisitions & strategic investments spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_acqp', '  Share of spend on acquisitions of operating businesses (rest = minority / strategic investments, no revenue)', 'driver', 'pct', e26_in=0.0, ae_in=0.5)
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=3.0, e26_in=0.0,
      note='Assumption (3.0x input). Precedents: MGM (17-Mar-2022, $6.1bn net of cash + $2.5bn debt assumed; Q1-22 10-Q), One Medical (22-Feb-2023, $3.5bn; Q1-23 10-Q), Whole Foods (28-Aug-2017, $13.2bn; FY2017 10-K).')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}*{V("m_acqp")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.08)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}', note='Mid-year convention.')
    S('m_m', '  Operating margin of acquired businesses %', 'driver', 'pct', e26_in=0.0, ae_in=0.05)
    S('m_oi', '  Operating income from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_intp', '  Acquired intangibles % of acquisition spend', 'driver', 'pct', e26_in=0.0, ae_in=0.30,
      note='One Medical: $1.3bn intangibles / $3.5bn consideration (37%); 30% input (assumption).')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=10)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_acqp")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (inside the acquired-business margin)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_acqp")}*{V("m_intp")})/{V("m_life")},0)')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group Total — net sales & operating income (segment build) → Q3-26 guidance calibration', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic: Amazon guides one quarter ahead (net sales and operating income ranges); Q4/26E carries the Q3 Δs')
    S('g_rev', 'Net sales (segment build)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("seg_na_rev")}),{V("seg_na_rev")}+{V("seg_intl_rev")}+{V("seg_aws_rev")},{V("is_rev")})',
      fc=lambda: f'={V("seg_na_rev")}+{V("seg_intl_rev")}+{V("seg_aws_rev")}+N({V("m_rev")})', note='Σ segments (+ future acquisitions from 2027E).')
    S('g_rev_g', '  Net sales y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs consolidated net sales (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=1.01,0,ROUND({V("g_rev")}-{V("is_rev")},0)),"")')
    S('g_adj', 'Adjusted operating income (segment build; before special charges and energy-contract remeasurements)', 'total', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("is_oi")}),{V("is_oi")}+{V("o_tot")},"")',
      fc=lambda: f'={V("seg_na_oi")}+{V("seg_intl_oi")}+{V("seg_aws_oi")}+N({V("m_oi")})',
      note='History: GAAP operating income + Amazon-quantified special items (bridge below). Forecast: Σ segment OI (+ acquisitions). Drives the GAAP P&L.')
    S('g_adjm', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('g_adj', 'is_rev'))
    S('g_chk_adj', '  Check: segment build vs adjusted operating income bridge (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_adj")}),ISNUMBER({V("o_adj")})),IF(ABS({V("g_adj")}-{V("o_adj")})<=1.01,0,ROUND({V("g_adj")}-{V("o_adj")},0)),"")')
    S('cal_rev', '  Memo: Q3-26 net sales guidance (scenario end-point: high / mid / low of $197.0–202.0bn)', 'memo', 'm', qe=lambda: ('=' + CH(SC['out_rev'])) if CTX.col.q == 3 else None,
      note=V0['rev_guid_note'])
    S('cal_pre', '  Net sales before calibration (Q3/26E helper)', 'line', 'm',
      qe=lambda: ('=' + '+'.join(f'{P(k)}*(1+{V(k + "_pre")}' + (f'+{V("pg_prime")}' if k in PRIME else '') + ')' for k in LINES)) if CTX.col.q == 3 else None)
    S('cal_sens', '  Net sales sensitivity to +1.00 of retail-group growth (Q3/26E helper)', 'line', 'm',
      qe=lambda: ('=' + '+'.join(P(k) for k in RETAIL)) if CTX.col.q == 3 else None)
    S('cal_g', '  Guidance calibration: Δ y/y growth applied to the retail product groups (Q3 solved; Q4 carried)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_rev")}-{V("cal_pre")})/{V("cal_sens")}' if CTX.col.q == 3 else f'={A(Q3E, "cal_g")}',
      note='Solves the uniform growth shift (vs Q1-26 y/y) so that Q3-26 net sales = the guidance end-point for the active scenario; Q4/26E carries the same Δ (one-quarter-ahead guidance, UBER precedent). AWS excluded (its Q2 trend is held).')
    S('cal_rev_chk', '  Check: Q3-26 net sales vs guidance end-point (should be 0)', 'check', 'm', qe=lambda: f'=ROUND({V("is_rev")}-{V("cal_rev")},0)' if CTX.col.q == 3 else None)
    S('cal_q3g', '    Model Q3-26 net sales y/y % (guided +9–12%; FX ~−80 bp; Prime Day timing ~−400 bp)', 'memo_calc', 'pct', qe=lambda: f'={V("is_rev")}/{P("is_rev")}-1' if CTX.col.q == 3 else None)
    S('cal_oi', '  Memo: Q3-26 operating income guidance (scenario end-point: high / mid / low of $22.5–26.5bn)', 'memo', 'm', qe=lambda: ('=' + CH(SC['out_oi'])) if CTX.col.q == 3 else None,
      note=V0['oi_guid_note'])
    S('cal_oi_pre', '  Adjusted operating income before margin calibration (Q3/26E helper)', 'line', 'm',
      qe=lambda: ('=' + '+'.join(f'{V(f"seg_{s}_rev")}*{V(f"seg_{s}_m_pre")}' for s, _ in SEGS) + f'-{V("o_tot")}') if CTX.col.q == 3 else None)
    S('cal_segrev', '  Segment net sales (Q3/26E helper)', 'line', 'm', qe=lambda: ('=' + '+'.join(V(f'seg_{s}_rev') for s, _ in SEGS)) if CTX.col.q == 3 else None)
    S('cal_m', '  Guidance calibration: Δ segment margin (Q3 solved; Q4 = Q3 Δ adjusted for the prior-year special charges not disclosed by segment)', 'driver', 'pct',
      qe=lambda: (f'=({V("cal_oi")}-{V("cal_oi_pre")})/{V("cal_segrev")}' if CTX.col.q == 3 else
                  f'={A(Q3E, "cal_m")}-({A(P3, "d_sc")}-{A(P3, "seg_na_sc")})/{A(P3, "is_rev")}+({A(P4, "d_sc")}-{A(P4, "seg_na_sc")})/{A(P4, "is_rev")}'),
      note=('Q3: solves the uniform margin shift so that Q3-26 GAAP operating income = the guidance end-point (guidance assumes no energy-derivative remeasurement and no settlements). '
            'Q4 (no guidance): Q3 Δ − Q3-25 special charges not disclosed by segment ($1.8bn severance) ÷ Q3-25 net sales + Q4-25 special charges ($2.44bn) ÷ Q4-25 net sales, '
            'so the solved underlying shift is carried without the one-offs in either base.'))
    S('cal_oi_chk', '  Check: Q3-26 operating income vs guidance end-point (should be 0)', 'check', 'm', qe=lambda: f'=ROUND({V("is_oi")}-{V("cal_oi")},0)' if CTX.col.q == 3 else None)
    S('cal_capex_u', '  Memo: 2026 capital expenditures ~$200bn — UNVERIFIED (Q4-25 earnings call, not in an EDGAR filing; information only)', 'memo', 'm', e26_in=200000.0,
      note=MAN['unverified']['capex_2026']['status'])
    S('cal_capex_d', '    Model 2026E gross capex − unverified call figure (information)', 'memo_calc', 'm', e26=lambda: f'=-{V("cf_capex")}-{V("cal_capex_u")}')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A & special items', 'block', note='COST DRIVERS — inputs that drive forecast cost lines (Q3/Q4-26E: prior-year quarter + 1H-26 drift or point estimates; 2027E+: % of net sales)')
    S('d_dda', '  Depreciation & amortization — total (cash-flow statement: P&E, capitalized content, operating-lease assets, other)', 'line', 'm', data='cf_dda', flow=True,
      fc=lambda: f'={V("d_dep")}+{V("d_oda")}', note='As presented in the cash-flow statement (includes operating-lease ROU amortization from 2019). Forecast = P&E depreciation + other D&A.')
    S('d_dep', '  Depreciation & amortization of property and equipment (XBRL "Depreciation": FY2014+, quarters Q2-24+)', 'line', 'm', data='dep', flow=True,
      qe=lambda: (f'={B1("bs_ppe")}*{V("d_dep_r")}/4' if CTX.col.q == 3 else
                  f'=({B1("bs_ppe")}+{Q3E}{R["d_capex_q"]}*(1-{PT("pt_proc")})-{Q3E}{R["d_dep"]})*{V("d_dep_r")}/4'),
      ae=lambda: f'=({P("bs_ppe")}+0.5*(-{V("cf_capex")}-{V("cf_capex_proc")}+{V("ds_fladd")}))*{V("d_dep_r")}',
      note='Q3/Q4-26E: opening PP&E × Q2-26 annualised rate ÷ 4 (Q4 opening = 30-Jun PP&E + Q3 net capex − Q3 depreciation). 2027E+: rate × (opening PP&E + ½ net additions).')
    S('d_dep_r', '  P&E depreciation ÷ opening PP&E (annualised)', 'pct', 'pct',
      hist=lambda: (f'=IF(AND(ISNUMBER({V("d_dep")}),ISNUMBER({(PQ if CTX.col.q else P)("bs_ppe")})),IFERROR({V("d_dep")}*{QF()}/{(PQ if CTX.col.q else P)("bs_ppe")},""),"")'
                    if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None),
      qe=lambda: f'={B1("d_dep_r")}', ae_in=V0['dep_r'], note=V0['dep_note'])
    S('d_oda', '  Other D&A (operating-lease ROU assets, capitalized video / music content, other) = total − P&E depreciation', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("d_dep")}),{V("d_dda")}-{V("d_dep")},"")', fc=lambda: f'={V("is_rev")}*{V("d_oda_pct")}')
    S('d_oda_pct', '  Other D&A % of net sales', 'pct', 'pct', all=ratio('d_oda', 'is_rev'), qe=lambda: f'=IFERROR(({ACT("d_dda")}-{ACT("d_dep")})/{ACT("is_rev")},"")', ae_in=V0['oda_pct'])
    S('d_capex_q', '  Gross capital expenditures — Q3/Q4-26E point estimate (purchases of property and equipment)', 'driver', 'm', qe=lambda: f'={PT("pt_capex_q")}',
      note='Point estimate: Q2-26 run-rate ($54.2bn; 1H-26 $98.4bn). An unverified ~$200bn FY26 figure from the call is shown as an information row.')
    S('d_sbc', '  Stock-based compensation (cash-flow statement)', 'line', 'm', data='cf_sbc', flow=True,
      qe=lambda: f'={P("d_sbc")}*(1+IFERROR({ACT("d_sbc")}/{ACT0("d_sbc")}-1,0))', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}',
      note='Not adjusted out by Amazon (segment OI is after SBC from 2016). Q3/Q4-26E: prior-year quarter × 1H-26 y/y; 2027E+: % of net sales.')
    S('d_sbc_pct', '  Stock-based compensation % of net sales', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    for k, lab, isk in (('ful', 'Fulfillment', 'is_ful'), ('tech', 'Technology and infrastructure (technology and content to 2021)', 'is_tech'),
                        ('mkt', 'Sales and marketing (marketing to 2021)', 'is_mkt'), ('ga', 'General and administrative', 'is_ga')):
        S(f'd_{k}', f'  {lab} % of net sales', 'pct', 'pct', all=ratio(isk, 'is_rev'),
          qe=lambda isk=isk, k=k: f'={P(f"d_{k}")}+IFERROR({ACT(isk)}/{ACT("is_rev")}-{ACT0(isk)}/{ACT0("is_rev")},0)', ae_in=V0['cost'][k],
          note=('Q3/Q4-26E: prior-year quarter ratio + 1H-26 y/y drift; 2027E+ input. Cost of sales is the balancing line to the operating income from the segment build.') if k == 'ful' else None)
    S('d_othop', '  Other operating expense (income), net', 'line', 'm', qe=lambda: f'={PT("pt_othop")}', ae_in=V0['othop'])
    S('d_adj_h', '  Special items quantified by Amazon (pre-tax; adjusted out in the model bridges; forecast nil):', 'sub', 'gen')
    S('d_sc', '  Special charges quantified in the release text (Q4-22 $2.7bn; Q1-23 $0.5bn; Q3-25 $4.3bn; Q4-25 $2.44bn)', 'line', 'm', data='sc_tot', flow=True,
      labkey='sc_text', fc=lambda: '=0',
      note='Q4-22 self-insurance estimate changes, impairments, severance; Q1-23 severance; Q3-25 FTC settlement $2.5bn + severance $1.8bn; Q4-25 Italy tax disputes & lawsuit $1.1bn, severance $0.73bn, impairments $0.61bn. Forecast nil (guidance assumes no settlements / restructurings).')
    S('d_en', '  Energy-contract derivative remeasurement (unrealized gain −; in technology and infrastructure, mostly AWS; Q2-26 10-Q)', 'line', 'm', data='en', flow=True, fc=lambda: '=0',
      note='Non-cash fair-value changes on long-dated power contracts (Q1-26 gain $48m, Q2-26 gain $551m). Excluded from Q3-26 guidance; forecast nil.')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF OPERATIONS (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (operating income = adjusted OI from the segment build − special items; cost of sales is the balancing line)')
    S('is_rev', 'Total net sales', 'total', 'm', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the segment build.')
    S('is_prod', '  Memo: net product sales', 'memo', 'm', data='rev_prod', flow=True)
    S('is_serv', '  Memo: net service sales', 'memo', 'm', data='rev_serv', flow=True)
    S('is_cogs', 'Cost of sales', 'line', 'm', data='cogs', flow=True,
      fc=lambda: f'={V("is_rev")}-{V("is_oi")}-{V("is_ful")}-{V("is_tech")}-{V("is_mkt")}-{V("is_ga")}-{V("is_othop")}',
      note='Forecast = net sales − operating income − other operating expense lines (balancing line).')
    S('is_gm', '  Gross margin % (net sales less cost of sales; FY2006–09 releases presented gross profit)', 'pct', 'pct',
      all=lambda: f'=IF(ISNUMBER({V("is_cogs")}),IFERROR(1-{V("is_cogs")}/{V("is_rev")},""),"")')
    S('is_ful', 'Fulfillment', 'line', 'm', data='ful', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_ful")}')
    S('is_tech', 'Technology and infrastructure', 'line', 'm', data='tech', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_tech")}+{V("d_en")}')
    S('is_mkt', 'Sales and marketing', 'line', 'm', data='mkt', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_mkt")}')
    S('is_ga', 'General and administrative', 'line', 'm', data='ga', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_ga")}')
    S('is_othop', 'Other operating expense (income), net', 'line', 'm', data='othop', flow=True, fc=lambda: f'={V("d_othop")}')
    S('is_oi', 'Operating income', 'total', 'm', data='oi', flow=True, fc=lambda: f'={V("g_adj")}-{V("o_tot")}',
      note='Forecast = adjusted operating income (segment build) − special items (forecast nil).')
    S('is_oi_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('is_intinc', 'Interest income', 'line', 'm', data='int_inc', flow=True,
      qe=lambda: (f'=({B1("bs_cash")}+{B1("bs_msec")})*{PT("pt_yield")}/4' if CTX.col.q == 3 else f'={Q3E}{R["is_intinc"]}'),
      ae=lambda: f'=({P("bs_cash")}+{P("bs_msec")})*{V("ds_r_cash")}', note='Yield × opening cash, cash equivalents and marketable securities (no circularity).')
    S('is_intexp', 'Interest expense (incl. finance-lease and financing-obligation interest)', 'line', 'm', data='int_exp', flow=True,
      qe=lambda: f'={PT("pt_int_q3")}' if CTX.col.q == 3 else f'={PT("pt_int_q4")}',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_st")}*{V("ds_r_st")}+{V("ds_flint")}',
      note='Q3/Q4-26E point estimates (incl. the $25.0bn July and £4.25bn September notes). 2027E+ = rate × opening notes + rate × opening CP / revolver + lease interest.')
    S('is_othinc', 'Other income (expense), net (investment marks — Anthropic, Rivian — FX, other; incl. "remeasurements and other" 2006–08)', 'line', 'm', data='oth_inc', flow=True,
      fc=lambda: '=0', note='Not forecast (fair-value changes on equity investments and convertible notes are unpredictable); excluded from adjusted net income.')
    S('is_ebt', 'Income before income taxes', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_oi")}),{V("is_oi")}+{V("is_intinc")}-{V("is_intexp")}+{V("is_othinc")},"")')
    S('is_tax', 'Provision for income taxes', 'line', 'm', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='FY2025 19.6%; 1H-26 22.9% (incl. tax on investment gains). Forecast rate on pre-tax income without investment marks (assumption).')
    S('is_eq', 'Equity-method investment activity, net of tax (incl. 2005–06 cumulative effect)', 'line', 'm', data='equity', flow=True, fc=lambda: '=0')
    S('is_ni', 'Net income', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")}+{V("is_eq")},"")')
    S('is_ni_chk', '  Check: net income vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=1.01,0,ROUND({V("is_ni")}-{V("is_ni_pub")},0)),"")')
    S('is_ni_pub', '  Memo: net income as reported', 'memo', 'm', data='ni', flow=True)
    S('is_dda', '  Memo: depreciation & amortization (total)', 'memo_calc', 'm', all=lambda: f'={V("d_dda")}')
    S('is_sbc', '  Memo: stock-based compensation', 'memo_calc', 'm', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share — split-adjusted for the 20-for-1 split of 6-Jun-2022)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm', data='sh_b', avg=True,
      qe=lambda: f'={B1("bs_shares")}+{PT("pt_iss_q")}*({CTX.col.q}-2-0.5)',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q3/Q4-26E: shares outstanding at 30-Jun-2026 + equity-plan issuance (mid-quarter). 2027E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q2}{R["sh_dil"]}-{Q2}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")',
      note='Net income / weighted diluted shares.')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($; split-adjusted)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0101,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('dps', '  Cash dividends per share ($) — Amazon pays no dividend', 'line', 'ps', fc=lambda: '=0')
    blank()

    # ------------------------------------------------------------------ RECON 1: OI -> adjusted OI
    S('sec_r1', 'RECONCILIATION: OPERATING INCOME → ADJUSTED OPERATING INCOME (model definition; items Amazon quantified)', 'section',
      note='ADJUSTED OI — Amazon publishes no adjusted operating income; the model adds back only the special charges Amazon quantified in its release text and the energy-contract remeasurements quantified in the 10-Q')
    S('o_op', 'Operating income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_oi")}')
    S('o_sc', '  (+) Special charges quantified by Amazon', 'line', 'm', all=lambda: f'={V("d_sc")}')
    S('o_en', '  (+) Energy-contract derivative remeasurement (gain −)', 'line', 'm', all=lambda: f'={V("d_en")}')
    S('o_tot', '  Total special items (pre-tax)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("o_sc")}),{V("o_sc")}+{V("o_en")},"")')
    S('o_adj', '  = Adjusted operating income (model bridge)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_tot")},"")',
      note='Equals the segment build in the forecast (check in the Group block).')
    S('o_adj_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company-published operating income "without these charges" (Q3-25 $21.7bn; Q4-25 $27.4bn)', 'memo', 'm', data='oi_ex_sc_pub', flow=True)
    S('o_chk', '  Check: model bridge vs company-published (should be 0; ±50, published to $0.1bn)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),IF(ABS({V("o_op")}+{V("o_sc")}-{V("o_pub")})<=50,0,ROUND({V("o_op")}+{V("o_sc")}-{V("o_pub")},0)),"n/p")')
    S('o_def', '  Definition / basis', 'text', 'gen')
    S('o_adj_g', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental adjusted operating margin (Δ adjusted OI / Δ net sales)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: NI -> EBITDA -> adjusted EBITDA
    S('sec_r2', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (model definitions — Amazon publishes no EBITDA)', 'section',
      note='EBITDA — net income − equity-method activity + taxes − other income (expense) + interest expense − interest income = operating income; + total D&A (as presented, incl. operating-lease ROU amortization) = EBITDA; + special items = adjusted EBITDA')
    S('r_ni', 'Net income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('r_eq', '  (−) Equity-method investment activity, net of tax', 'line', 'm', all=lambda: f'=-{V("is_eq")}')
    S('r_tax', '  (+) Provision for income taxes', 'line', 'm', all=lambda: f'={V("is_tax")}')
    S('r_oth', '  (−) Other income (expense), net', 'line', 'm', all=lambda: f'=-{V("is_othinc")}')
    S('r_int', '  (+) Interest expense', 'line', 'm', all=lambda: f'={V("is_intexp")}')
    S('r_intinc', '  (−) Interest income', 'line', 'm', all=lambda: f'=-{V("is_intinc")}')
    S('r_oi', '  = Operating income (EBIT)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),SUM({V("r_ni")}:{V("r_intinc")}),"")')
    S('r_oi_chk', '  Check: bridge vs reported operating income (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_oi")}),IF(ABS({V("r_oi")}-{V("is_oi")})<=1.01,0,ROUND({V("r_oi")}-{V("is_oi")},0)),"")')
    S('r_dda', '  (+) Depreciation & amortization (total)', 'line', 'm', all=lambda: f'={V("d_dda")}')
    S('r_ebitda', '  = EBITDA (model)', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_oi")}),ISNUMBER({V("r_dda")})),{V("r_oi")}+{V("r_dda")},"")')
    S('r_adjx', '  (+) Special items (bridge above)', 'line', 'm', all=lambda: f'={V("o_tot")}')
    S('r_adj', '  = Adjusted EBITDA (model)', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda")}),ISNUMBER({V("r_adjx")})),{V("r_ebitda")}+{V("r_adjx")},"")',
      note='Model definition (SBC not added back). Used for leverage (net debt / adjusted EBITDA) and EV / EBITDA.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_adj_pub', '  Company-published EBITDA — none (Amazon does not publish EBITDA)', 'memo', 'm')
    S('r_chk', '  Check: adjusted EBITDA − D&A vs adjusted operating income (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_adj")}),ISNUMBER({V("o_adj")})),IF(ABS({V("r_adj")}-{V("d_dda")}-{V("o_adj")})<=1.01,0,ROUND({V("r_adj")}-{V("d_dda")}-{V("o_adj")},0)),"")')
    S('r_adj_rent', '  Memo: adjusted EBITDA after other D&A (operating-lease, content and other amortization; ≈ EBITDA after rent)', 'memo_calc', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_adj")}),ISNUMBER({V("d_oda")})),{V("r_adj")}-{V("d_oda")},"")')
    S('r_ebit_h', 'To adjusted EBIT, full-cost (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ddan', '  (−) Depreciation & amortization (total)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("d_dda")}),-{V("d_dda")},"")')
    S('r_ebit', '  = Adjusted EBIT, full-cost (= adjusted operating income: after SBC and all D&A)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+{V("r_ddan")},"")')
    S('r_ebit_m', '  Adjusted EBIT (full-cost) margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: cash special charges (settlements, severance, tax disputes; deducted in the DCF)', 'memo_calc', 'm', all=lambda: f'={V("o_sc")}')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: NET INCOME / DILUTED EPS → ADJUSTED NET INCOME → ADJUSTED EPS (model definition — Amazon publishes none)', 'section',
      note='ADJUSTED EPS — net income − other income (expense), net (investment marks: Rivian 2021–24, Anthropic 2025–26; FX) − equity-method activity + special items, '
           'tax-effected at the statutory rate (35% to 2017, 21% from 2018)')
    S('e_ni', 'Net income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('e_oth', '  (−) Other income (expense), net (pre-tax)', 'line', 'm', all=lambda: f'=-{V("is_othinc")}')
    S('e_eq', '  (−) Equity-method investment activity, net of tax', 'line', 'm', all=lambda: f'=-{V("is_eq")}')
    S('e_op', '  (+) Special items (pre-tax; bridge above)', 'line', 'm', all=lambda: f'={V("o_tot")}')
    S('e_trate', '  Tax rate applied to the adjustments (US federal statutory rate)', 'pct', 'pct',
      hist_in=lambda: 0.35 if CTX.col.year <= 2017 else 0.21, fc_in=0.21,
      note='Amazon publishes no tax effect; statutory 35% to 2017, 21% from 2018 (TCJA). Assumption.')
    S('e_tax', '  (−) Tax effect of the adjustments', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("e_oth")}),-({V("e_oth")}+{V("e_op")})*{V("e_trate")},"")')
    S('e_adjni', '  = Adjusted net income (model bridge)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("e_tax")}),{V("e_ni")}+{V("e_oth")}+{V("e_eq")}+{V("e_op")}+{V("e_tax")},"")')
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted EPS – diluted ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted EPS — none (Amazon does not publish adjusted EPS)', 'eps_memo', 'ps')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_adjebt', '  Adjusted pre-tax income (adjusted operating income − interest expense + interest income)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_adj")}),{V("o_adj")}-N({V("is_intexp")})+N({V("is_intinc")}),"")')
    S('e_adjtax', '  Adjusted income tax (adjusted pre-tax income − adjusted net income)', 'line', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("e_adjni")}),ISNUMBER({V("e_adjebt")})),{V("e_adjebt")}-{V("e_adjni")},"")')
    S('e_rate', '  Adjusted effective tax rate', 'pct', 'pct', all=ratio('e_adjtax', 'e_adjebt'))
    S('e_def', '  Definition / basis', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Net sales y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_aws', '  AWS segment net sales y/y %', 'growth', 'pct', all=growth('seg_aws_rev'))
    S('gm_ads', '  Advertising services y/y %', 'growth', 'pct', all=growth('pg_ads'))
    S('gm_adjop', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating income (GAAP) y/y %', 'growth', 'pct', all=growth('is_oi'))
    S('gm_ni', '  Net income y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_gm', '  Gross margin %', 'pct', 'pct', all=lambda: f'={V("is_gm")}')
    S('gm_adjop_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_inc', '  Incremental adjusted operating margin (Δ adjusted OI / Δ net sales)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_ful', '  Fulfillment % of net sales', 'pct', 'pct', all=ratio('is_ful', 'is_rev'))
    S('gm_tech', '  Technology and infrastructure % of net sales', 'pct', 'pct', all=ratio('is_tech', 'is_rev'))
    blank()
