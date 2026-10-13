"""Row specification of the MSFT Model sheet, part 1 (MLM template layout and process):
FY27 segment build (Agents and Infra: Azure, Microsoft 365 cloud, productivity and server licensing, industry solutions, frontier and
support services; Devices and Consumer: search and advertising, XBOX, Windows OEM and devices) -> segment operating income at the
segment margin -> legacy segment structures (memo) -> M&A lever -> group total & Q1 FY27 guidance calibration -> cost drivers ->
income statement -> GAAP-to-adjusted bridges -> growth & margins."""
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
def Q1a(key): return f'${Q1}${R[key]}'                    # Q1/27E (absolute): the guided quarter
def LQG(key): return f'IFERROR({LQ}{R[key]}/{LQP}{R[key]}-1,0)'   # Q4/26 y/y growth (latest actual quarter)
def B1(key): return f'{A26}{R[key]}'                       # 30-Jun-2026 balance (FY2026 column)
def isQ1(): return CTX.col.q == 1

SEG = [('ai', 'Agents and Infra', 'AI', [('az', 'Azure'), ('m365', 'Microsoft 365 cloud'), ('psl', 'Productivity and server licensing'),
                                          ('ind', 'Industry solutions'), ('fss', 'Frontier and support services')]),
       ('dc', 'Devices and Consumer', 'DC', [('sa', 'Search and advertising'), ('xbox', 'XBOX'), ('win', 'Windows OEM and devices')])]
LINES = [f'{s}_{t}' for s, _, _, ts in SEG for t, _ in ts]
SEGK = [s for s, *_ in SEG]

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of the Q1 FY27 guidance ranges (costs: low / mid / high).'))
    r = 11
    SCEN_ROWS.append((r, 'out_hdr', V0['out_hdr'], 'High', 'Mid', 'Low', V0['out_note'])); r += 1
    for key, lab, (hi, mid, lo), nf, note in V0['outlook']:
        SC[key] = r; SCEN_ROWS.append((r, 'out', lab, hi, mid, lo, note, nf)); r += 1
    r += 1
    SCEN_ROWS.append((r, 'pt_hdr', 'FY2027E point estimates (all cases)', None, None, None, None)); r += 1
    for key, lab, vals, nf, note in V0['points']:
        SC[key] = r
        SCEN_ROWS.append((r, 'pt', lab, None, vals, None, note, nf)); r += 1
    r += 1
    SC['LIQ'] = r
    SCEN_ROWS.append((r, 'tgt', '  Target cash & short-term investments before buybacks ($m) — buyback plug FY2027E+', *V0['liq'], V0['liq_note']))
    r += 1
    SC['BBMIN'] = r
    SCEN_ROWS.append((r, 'tgt', '  Minimum share repurchases per year ($m)', *V0['bbmin'], V0['bbmin_note']))
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
    # ------------------------------------------------------------------ SEGMENT BUILD (FY27 structure)
    S('sec_seg', 'SEGMENT P&L — AGENTS AND INFRA · DEVICES AND CONSUMER (FY27 structure: product & service lines × segment operating margin)', 'section',
      note='SEGMENT BUILD — modelling logic (product & service revenue → segment revenue → segment operating income at the segment margin → operating income → GAAP P&L)')
    blank()
    descr = {'ai': 'Agents and Infra (Azure, Microsoft 365 cloud, productivity & server licensing, industry solutions — Dynamics 365, LinkedIn Talent / Sales, healthcare — and frontier & support services)',
             'dc': 'Devices and Consumer (search & advertising incl. LinkedIn Marketing / Premium, XBOX content, services & hardware, Windows OEM & devices)'}
    for s, title, code, types in SEG:
        S(f'{s}_hdr', descr[s], 'block', note=f'{title.upper()} — modelling logic (history: restated FY27 basis, 8-K 2-Sep-2026, Q1/25–Q4/26 only)')
        for t, tl in types:
            key = f'{s}_{t}'
            S(key, f'  {tl} revenue', 'line', 'm', data=f'pl_{t}', flow=True,
              qe=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})', ae=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})',
              note=('Restated product & service revenue (FY27 definitions; 8-K 2-Sep-2026, Ex. 99.1). Q1–Q4/27E: prior-year quarter × (1 + growth). '
                    '2028E+: prior year × (1 + scenario lever).') if t == types[0][0] else None)
            S(key + '_g', '    y/y %', 'growth', 'pct', all=growth(key),
              qe=lambda key=key, s=s: f'={V(key + "_pre")}+{Q1a("cal_" + s + "_d")}',
              ae=lambda key=key, code=code, t=t: '=' + CH(SC[f'{code}_{t.upper()}'][CTX.col.year]),
              note=('Q1–Q4/27E: Q4/26 y/y growth of the line + the segment calibration Δ solved in Q1/27E to the segment revenue guidance (carried to Q2–Q4). '
                    '2028E–2031E: scenario lever (Bull/Base/Bear table →).') if t == types[0][0] else None)
            S(key + '_pre', '    Growth before calibration (Q4/26 y/y, latest actual quarter)', 'driver', 'pct', qe=lambda key=key: f'={LQG(key)}')
        S(f'{s}_rev', f'  {title} — segment revenue', 'line_b', 'm',
          all=lambda types=types, s=s: f'=IF(ISNUMBER({V(s + "_" + types[0][0])}),{"+".join(V(s + "_" + t) for t, _ in types)},"")',
          note='Σ product & service lines.' if s == 'ai' else None)
        S(f'{s}_rev_g', '  Segment revenue y/y %', 'growth', 'pct', all=growth(f'{s}_rev'))
        S(f'{s}_mix', '  % of total revenue', 'pct', 'pct', all=ratio(f'{s}_rev', 'g_rev'))
        S(f'{s}_pub', f'  Memo: {title} segment revenue as restated (8-K 2-Sep-2026)', 'memo', 'm', data=f'sg_{s}_rev', flow=True)
        S(f'{s}_chk', '  Check: product & service lines vs segment revenue (should be 0)', 'check', 'm',
          hist=lambda s=s: f'=IF(AND(ISNUMBER({V(s + "_rev")}),ISNUMBER({V(s + "_pub")})),IF(ABS({V(s + "_rev")}-{V(s + "_pub")})<=1,0,ROUND({V(s + "_rev")}-{V(s + "_pub")},0)),"")')
        S(f'{s}_oi', f'  {title} — segment operating income', 'line', 'm', data=f'sg_{s}_oi', flow=True,
          qe=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}', ae=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}',
          note='Segment operating income as restated (segment revenue − cost of revenue − operating expenses; all costs are allocated, no corporate line). Forecast = revenue × margin.' if s == 'ai' else None)
        S(f'{s}_m', '  Segment operating margin %', 'pct', 'pct', all=ratio(f'{s}_oi', f'{s}_rev'),
          qe=lambda s=s: f'={V(s + "_m_pre")}+{Q1a("cal_m")}', ae=lambda s=s, code=code: '=' + CH(SC[f'{code}_M'][CTX.col.year]),
          note='Q1–Q4/27E: margin before calibration + uniform margin Δ solved in Q1/27E to the guided operating income (revenue − COGS − opex guidance), carried to Q2–Q4. 2028E+: scenario lever.' if s == 'ai' else None)
        S(f'{s}_m_pre', '  Margin before calibration (prior-year quarter + FY26 vs FY25 margin drift)', 'driver', 'pct',
          qe=lambda s=s: f'={P(s + "_m")}+IFERROR({Y(s + "_oi", 2026)}/{Y(s + "_rev", 2026)}-{Y(s + "_oi", 2025)}/{Y(s + "_rev", 2025)},0)')
        S(f'{s}_gm', '  Memo: segment gross margin % (revenue − cost of revenue, restated)', 'pct', 'pct',
          hist=lambda s=s: f'=IF(AND(ISNUMBER({V(s + "_pub")}),ISNUMBER({V(s + "_cogs")})),IFERROR(1-{V(s + "_cogs")}/{V(s + "_pub")},""),"")')
        S(f'{s}_cogs', '  Memo: segment cost of revenue (restated)', 'memo', 'm', data=f'sg_{s}_cogs', flow=True)
        S(f'{s}_opex', '  Memo: segment operating expenses (restated)', 'memo', 'm', data=f'sg_{s}_opex', flow=True)
        S(f'{s}_inc', '  Incremental segment margin (Δ operating income / Δ revenue)', 'pct', 'pct', all=incr(f'{s}_oi', f'{s}_rev'))
        blank()
    S('mx_hdr', 'Mix & KPIs (outputs)', 'block', note='MIX — outputs')
    S('mx_az_p', '  Azure % of total revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("ai_az")}),IFERROR({V("ai_az")}/{V("g_rev")},""),"")')
    S('mx_cloud', '  Azure + Microsoft 365 cloud + Industry solutions revenue (proxy for the Microsoft Cloud metric; not the company definition)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("ai_az")}),{V("ai_az")}+{V("ai_m365")}+{V("ai_ind")},"")',
      note='Industry solutions includes on-premises products; Microsoft Cloud (company metric) counts only Industry solutions cloud — this row is a labelled proxy.')
    S('mx_cloud_g', '    y/y %', 'growth', 'pct', all=growth('mx_cloud'))
    S('gc_ai', '  Contribution to total revenue growth — Agents and Infra (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("ai_rev")}-{P("ai_rev")})/{P("g_rev")},"")' if CTX.col.prior else None))
    S('gc_dc', '  Contribution to total revenue growth — Devices and Consumer (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("dc_rev")}-{P("dc_rev")})/{P("g_rev")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ legacy segment structures (memo, as originally reported)
    S('lg_hdr', 'Legacy segment structures — memo, as originally reported in each period\'s release / 10-K (not on the FY27 basis)', 'block',
      note='LEGACY SEGMENTS — memo only; each structure ties to consolidated revenue / profit in its own periods (check rows)')
    S('s3_h', '  Productivity and Business Processes / Intelligent Cloud / More Personal Computing (FY2016–FY2026; recast Aug-2019, Aug-2024 not applied)', 'sub', 'gen')
    for k, lab in (('pbp', 'Productivity and Business Processes'), ('ic', 'Intelligent Cloud'), ('mpc', 'More Personal Computing'), ('corp', 'Corporate and Other (FY2016–FY2018)')):
        S(f's3_{k}_r', f'    {lab} — revenue', 'memo', 'm', data=f's3_{k}_r', flow=True)
    S('s3_chk_r', '    Check: Σ revenue vs consolidated (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("s3_pbp_r")}),ROUND({nsum(["s3_pbp_r", "s3_ic_r", "s3_mpc_r", "s3_corp_r"])}-{V("is_rev")},0),"")')
    for k, lab in (('pbp', 'Productivity and Business Processes'), ('ic', 'Intelligent Cloud'), ('mpc', 'More Personal Computing'), ('corp', 'Corporate and Other')):
        S(f's3_{k}_o', f'    {lab} — operating income', 'memo', 'm', data=f's3_{k}_o', flow=True)
    S('s3_chk_o', '    Check: Σ operating income vs consolidated (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("s3_pbp_o")}),ROUND({nsum(["s3_pbp_o", "s3_ic_o", "s3_mpc_o", "s3_corp_o"])}-{V("is_oi")},0),"")')
    S('l2_h', '  Devices & Consumer / Commercial (FY2014–FY2015; revenue and gross margin only)', 'sub', 'gen')
    L2 = (('dcl', 'D&C Licensing'), ('cgh', 'Computing and Gaming Hardware (D&C Hardware to Q3/14)'), ('ph', 'Phone Hardware (Nokia, from Apr-2014)'),
          ('dco', 'D&C Other'), ('cl', 'Commercial Licensing'), ('co', 'Commercial Other'), ('corp', 'Corporate and Other'))
    for k, lab in L2: S(f'l2_{k}_r', f'    {lab} — revenue', 'memo', 'm', data=f'l2_{k}_r', flow=True)
    S('l2_chk_r', '    Check: Σ revenue vs consolidated (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("l2_cl_r")}),ROUND({nsum(["l2_" + k + "_r" for k, _ in L2])}-{V("is_rev")},0),"")')
    for k, lab in L2: S(f'l2_{k}_g', f'    {lab} — gross margin', 'memo', 'm', data=f'l2_{k}_g', flow=True)
    S('l2_chk_g', '    Check: Σ gross margin vs consolidated (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("l2_cl_g")}),ROUND({nsum(["l2_" + k + "_g" for k, _ in L2])}-{V("is_gp")},0),"")')
    S('l1_h', '  Divisions (FY2006–FY2013; FY2006 seven segments aggregated into the FY2007 five divisions)', 'sub', 'gen')
    L1 = (('win', 'Client / Windows (& Windows Live) Division'), ('st', 'Server and Tools'), ('osd', 'Online Services (MSN to FY2006)'),
          ('mbd', 'Microsoft Business Division (FY2006: Information Worker + Business Solutions)'),
          ('edd', 'Entertainment and Devices (FY2006: Home & Entertainment + Mobile & Embedded)'), ('unal', 'Unallocated / reconciling amounts / corporate'))
    for k, lab in L1: S(f'l1_{k}_r', f'    {lab} — revenue', 'memo', 'm', data=f'l1_{k}_r', flow=True)
    S('l1_chk_r', '    Check: Σ revenue vs consolidated (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("l1_win_r")}),ROUND({nsum(["l1_" + k + "_r" for k, _ in L1])}-{V("is_rev")},0),"")')
    for k, lab in L1: S(f'l1_{k}_o', f'    {lab} — operating income', 'memo', 'm', data=f'l1_{k}_o', flow=True)
    S('l1_chk_o', '    Check: Σ operating income vs consolidated (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("l1_win_o")}),ROUND({nsum(["l1_" + k + "_o" for k, _ in L1])}-{V("is_oi")},0),"")')
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — unallocated; deals closed from 2028E)', 'block', note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=10.0, e26_in=0.0,
      note='Activision Blizzard (Oct-2023) $75.4bn on ~$8.7bn of sales (~8.7x); Nuance (Mar-2022) $18.8bn on ~$1.4bn (~13x); LinkedIn (Dec-2016) $27.0bn on ~$3.3bn (~8x). 10x input (assumption).')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.08)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}', note='Mid-year convention.')
    S('m_m', '  Operating margin of acquired businesses (after amortization) %', 'driver', 'pct', e26_in=0.0, ae_in=0.15)
    S('m_oi', '  Operating income from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.02)
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.30,
      note='PPAs: Activision 29% of the purchase price in intangibles, LinkedIn 29%, Nuance 23%.')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=7)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (inside segment operating income)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)',
      note='Microsoft does not adjust out amortization; the acquired-business margin above is after amortization.')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group Total — revenue & operating income (segment build) → Q1 FY27 guidance calibration', 'block', note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Revenue (segment build)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("ai_rev")}),{V("ai_rev")}+{V("dc_rev")},{V("is_rev")})',
      fc=lambda: f'={V("ai_rev")}+{V("dc_rev")}+N({V("m_rev")})', note='Σ segment revenue (+ future acquisitions from 2028E). Before Q1/25 = consolidated revenue (no FY27-basis split).')
    S('g_rev_g', '  Revenue y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs consolidated revenue (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=1,0,ROUND({V("g_rev")}-{V("is_rev")},0)),"")')
    S('g_oi', 'Operating income (segment build)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("ai_oi")}),{V("ai_oi")}+{V("dc_oi")}+N({V("m_oi")}),"")',
      note='Σ segment operating income (+ future acquisitions). Equals GAAP operating income (no corporate line; no forecast adjusting items); drives the GAAP P&L.')
    S('g_oim', '  Operating margin %', 'pct', 'pct', all=ratio('g_oi', 'is_rev'))
    S('g_chk_oi', '  Check: segment build vs operating income (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("g_oi")}),IF(ABS({V("g_oi")}-{V("is_oi")}-N({V("o_tot")}))<=1,0,ROUND({V("g_oi")}-{V("is_oi")}-N({V("o_tot")}),0)),"")')
    for s, title in (('ai', 'Agents and Infra'), ('dc', 'Devices and Consumer')):
        S(f'cal_{s}_gd', f'  Memo: Q1 FY27 {title} revenue guidance (scenario end-point)', 'memo', 'm', qe=lambda s=s: ('=' + CH(SC[f'out_{s}'])) if isQ1() else None,
          note=V0['guid_note'] if s == 'ai' else None)
        S(f'cal_{s}_pre', f'  {title} revenue before calibration (Q1/27E helper)', 'line', 'm',
          qe=lambda s=s: ('=' + '+'.join(f'{P(k)}*(1+{V(k + "_pre")})' for k in LINES if k.startswith(s + '_'))) if isQ1() else None)
        S(f'cal_{s}_sens', f'  {title} revenue sensitivity to +1.00 of growth (Q1/27E helper)', 'line', 'm',
          qe=lambda s=s: ('=' + '+'.join(P(k) for k in LINES if k.startswith(s + '_'))) if isQ1() else None)
        S(f'cal_{s}_d', f'  Guidance calibration: Δ y/y growth, all {title} lines (solved in Q1/27E; carried to Q2–Q4)', 'driver', 'pct',
          qe=lambda s=s: f'=({V("cal_" + s + "_gd")}-{V("cal_" + s + "_pre")})/{V("cal_" + s + "_sens")}' if isQ1() else None)
        S(f'cal_{s}_chk', f'  Check: Q1/27E {title} revenue vs guidance end-point (should be 0)', 'check', 'm',
          qe=lambda s=s: f'=ROUND({V(s + "_rev")}-{V("cal_" + s + "_gd")},0)' if isQ1() else None)
    S('cal_oi_t', '  Memo: Q1 FY27 operating income implied by guidance (revenue − COGS − operating expenses end-points)', 'memo_calc', 'm',
      qe=lambda: f'={V("cal_ai_gd")}+{V("cal_dc_gd")}-{CH(SC["out_cogs"])}-{CH(SC["out_opex"])}' if isQ1() else None,
      note='Bull = high revenue / low costs; Bear = low revenue / high costs. Guidance also says Q1 operating margin "relatively flat year-over-year".')
    S('cal_oi_pre', '  Operating income before margin calibration (Q1/27E helper)', 'line', 'm',
      qe=lambda: ('=' + '+'.join(f'{V(s + "_rev")}*{V(s + "_m_pre")}' for s in SEGK)) if isQ1() else None)
    S('cal_m', '  Guidance calibration: Δ segment operating margin (solved in Q1/27E; carried to Q2–Q4)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_oi_t")}-{V("cal_oi_pre")})/({V("ai_rev")}+{V("dc_rev")})' if isQ1() else None,
      note='Uniform shift on both segment margins so that Q1/27E operating income = guided revenue − guided COGS − guided operating expenses.')
    S('cal_oi_chk', '  Check: Q1/27E operating income vs guidance-implied (should be 0)', 'check', 'm', qe=lambda: f'=ROUND({V("g_oi")}-{V("cal_oi_t")},0)' if isQ1() else None)
    S('cal_cogs_chk', '  Check: Q1/27E cost of revenue vs COGS guidance end-point (should be 0)', 'check', 'm',
      qe=lambda: f'=ROUND({V("is_cogs")}-{CH(SC["out_cogs"])},0)' if isQ1() else None)
    S('cal_fyg', '  Memo: FY27 revenue growth "double-digit" — UNVERIFIED (call commentary, not filed on EDGAR); information only', 'memo', 'pct',
      e26=lambda: f'={PT("pt_fyg")}', note=V0['unver_note'])
    S('cal_fyg_d', '    Model FY27E revenue growth − 10% (information)', 'memo_calc', 'pct', e26=lambda: f'={V("g_rev_g")}-{V("cal_fyg")}')
    S('cal_fyo_d', '    Model FY27E operating income growth − 10% (information; also UNVERIFIED "double-digit")', 'memo_calc', 'pct', e26=lambda: f'={V("gm_op")}-{V("cal_fyg")}')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A, capex intensity & adjusting items', 'block',
      note='COST DRIVERS — inputs that drive forecast cost lines (Q1/27E: guidance; Q2–Q4/27E: prior-year quarter × Q1 trend; 2028E+: % of revenue or schedules)')
    S('d_dda', '  Depreciation, amortization & other (cash-flow statement)', 'line', 'm', data='cf_dda', flow=True,
      e26=lambda: f'={V("d_dep")}+{V("d_amort")}', qe=lambda: f'={E26}{R["d_dda"]}/4', ae=lambda: f'={V("d_dep")}+{V("d_amort")}',
      note='Cash-flow line "Depreciation, amortization, and other" (includes other non-cash items). Forecast = depreciation + amortization of intangibles; quarters = FY ÷ 4.')
    S('d_dep', '  Depreciation expense (10-K, annual)', 'line', 'm', data='x_dep', ann=True,
      fc=lambda: f'={P("bs_ppe")}*{V("d_dep_r")}', note='10-K Note (Property and equipment): FY26 $34.3bn. Forecast = opening net PP&E × depreciation rate.')
    S('d_dep_r', '  Depreciation ÷ opening net PP&E %', 'pct', 'pct', ann=True,
      hist=lambda: (f'=IF(AND(ISNUMBER({V("d_dep")}),ISNUMBER({P("bs_ppe")})),IFERROR({V("d_dep")}/{P("bs_ppe")},""),"")' if CTX.col.prior else None),
      e26_in=V0['dep_rate'][FYC], ae_in={y: V0['dep_rate'][y] for y in range(FYC + 1, FYL + 1)}, note=V0['dep_note'])
    S('d_amort', '  Amortization of intangible assets (10-K, annual; inside cost of revenue / opex, not adjusted out)', 'line', 'm', data='x_amort', ann=True,
      e26=lambda: f'={V("d_amort_sch")}', ae=lambda: f'={V("d_amort_sch")}+N({V("m_amort")})')
    S('d_amort_sch', '  Amortization schedule — intangibles held at 30-Jun-2026 (10-K, input)', 'driver', 'm', e26_in=V0['amort_sched'][FYC],
      ae_in={y: V0['amort_sched'][y] for y in range(FYC + 1, FYL + 1)}, note=V0['amort_note'])
    S('d_sbc', '  Stock-based compensation expense (cash-flow statement)', 'line', 'm', data='cf_sbc', flow=True,
      qe=lambda: f'={P("d_sbc")}*(1+{V("g_rev_g")})', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}',
      note='Q1–Q4/27E: prior-year quarter × (1 + revenue growth); 2028E+: % of revenue. Microsoft does not adjust out stock-based compensation.')
    S('d_sbc_pct', '  Stock-based compensation % of revenue', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_opex_g', '  Operating expenses (R&D + S&M + G&A) y/y % — Q1/27E from guidance, Q2–Q4 carried', 'driver', 'pct', all=growth('is_opex'),
      qe=lambda: (f'={CH(SC["out_opex"])}/{P("is_opex")}-1' if isQ1() else f'={Q1a("d_opex_g")}'))
    S('d_rd', '  R&D % of revenue', 'pct', 'pct', all=ratio('is_rd', 'is_rev'), ae_in=V0['rd_pct'])
    S('d_sm', '  Sales & marketing % of revenue', 'pct', 'pct', all=ratio('is_sm', 'is_rev'), ae_in=V0['sm_pct'])
    S('d_ga', '  General & administrative % of revenue', 'pct', 'pct', all=ratio('is_ga', 'is_rev'), ae_in=V0['ga_pct'],
      note='2028E+ inputs; gross profit (cost of revenue) is the balancing line between segment operating income and operating expenses.')
    S('d_capex', '  Capital expenditures incl. finance leases (USDm; company capex metric = additions to PP&E + finance-lease assets)', 'line', 'm', ann=True,
      hist=lambda: f'=IF(ISNUMBER({V("x_fl_add")}),-{V("cf_capex")}+{V("x_fl_add")},"")',
      e26_in=V0['capex_fy27'], ae=lambda: f'={V("is_rev")}*{V("d_capex_pct")}', note=V0['capex_note'])
    S('x_fl_add', '  of which: finance-lease right-of-use assets obtained (10-K, non-cash)', 'line', 'm', data='x_fl_add', ann=True,
      fc=lambda: f'={V("d_capex")}*{V("d_fl_sh")}')
    S('d_fl_sh', '  Finance-lease share of capital expenditures %', 'pct', 'pct', ann=True,
      hist=lambda: f'=IF(ISNUMBER({V("x_fl_add")}),IFERROR({V("x_fl_add")}/{V("d_capex")},""),"")',
      e26_in=V0['fl_share'], ae_in=V0['fl_share'], note='FY26: $24.6bn of $140.6bn (17.5%); FY25 $20.5bn of $85.1bn (24%). Input (assumption).')
    S('d_capex_pct', '  Capital expenditures incl. finance leases % of revenue', 'pct', 'pct', ann=True, all=ratio('d_capex', 'is_rev'),
      ae_in=V0['capex_pct'], note='2028E+ input (assumption): capex intensity normalises from the FY27E AI build-out peak.')
    S('d_adj_h', '  Adjusting items (company non-GAAP; forecast inputs nil — not forecastable):', 'sub', 'gen')
    S('d_revdef', '  Revenue deferrals / recognition (Windows upgrade offers, Windows 10; FY2012–FY2017)', 'line', 'm', data='oa_revdef', flow=True, fc=lambda: '=0')
    S('d_restr', '  Impairment, integration, restructuring & severance (FY2012–FY2023)', 'line', 'm', data='oa_restr', flow=True, fc=lambda: '=0')
    S('d_legal', '  European Commission fine (Q3 FY13)', 'line', 'm', data='oa_legal', flow=True, fc=lambda: '=0')
    S('d_taxi', '  Discrete tax items, after tax (TCJA; intangible-property transfers; India withholding-tax decision)', 'line', 'm', data='na_tax', flow=True, fc=lambda: '=0')
    S('d_openai', '  Impact from investments in OpenAI, after tax (other income; FY2025 re-presented, FY2026)', 'line', 'm', data='na_openai', flow=True, fc=lambda: '=0',
      note='Not forecast (equity-method results / remeasurement gains of the OpenAI stake depend on OpenAI\'s results and capital events). Forecast other income excludes them (as guided).')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'INCOME STATEMENTS (US GAAP)', 'section', note='CONSOLIDATED IS — forecast logic (operating income = segment build; cost of revenue implied)')
    S('is_rev', 'Total revenue', 'total', 'm', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the segment build.')
    S('is_rev_p', '  Memo: product revenue', 'memo', 'm', data='rev_prod', flow=True)
    S('is_rev_s', '  Memo: service and other revenue', 'memo', 'm', data='rev_serv', flow=True)
    S('is_cogs', 'Total cost of revenue', 'line', 'm', data='cogs', flow=True, fc=lambda: f'={V("is_rev")}-{V("is_gp")}')
    S('is_gp', 'Gross margin', 'line_b', 'm', hist=lambda: f'={V("is_rev")}-{V("is_cogs")}',
      fc=lambda: f'={V("is_oi")}+{V("is_opex")}+{V("is_impair")}', note='Forecast = operating income + operating expenses (implied by the segment build).')
    S('is_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('is_rd', 'Research and development', 'line', 'm', data='rd', flow=True,
      qe=lambda: f'={P("is_rd")}*(1+{V("d_opex_g")})', ae=lambda: f'={V("is_rev")}*{V("d_rd")}')
    S('is_sm', 'Sales and marketing', 'line', 'm', data='sm', flow=True,
      qe=lambda: f'={P("is_sm")}*(1+{V("d_opex_g")})', ae=lambda: f'={V("is_rev")}*{V("d_sm")}')
    S('is_ga', 'General and administrative', 'line', 'm', data='ga', flow=True,
      qe=lambda: f'={P("is_ga")}*(1+{V("d_opex_g")})', ae=lambda: f'={V("is_rev")}*{V("d_ga")}',
      note='Q1/27E: each line = prior-year quarter × (guided operating expenses ÷ prior-year operating expenses); Q2–Q4 carry the Q1 growth; 2028E+: % of revenue.')
    S('is_opex', '  Memo: operating expenses (R&D + S&M + G&A)', 'memo_calc', 'm', all=lambda: f'={V("is_rd")}+{V("is_sm")}+{V("is_ga")}')
    S('is_impair', 'Impairment, integration and restructuring; employee severance; goodwill impairment', 'line', 'm', data='impair', flow=True, fc=lambda: '=0')
    S('is_oi', 'Operating income', 'total', 'm', data='oi', flow=True, fc=lambda: f'={V("g_oi")}-{V("o_tot")}', note='Forecast = segment build operating income − adjusting items (nil).')
    S('is_oi_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('is_oi_chk', '  Check: gross margin − operating expenses − impairment = operating income (should be 0)', 'check', 'm',
      hist=lambda: f'=ROUND({V("is_gp")}-{V("is_opex")}-{V("is_impair")}-{V("is_oi")},0)')
    S('is_oth', 'Other income (expense), net', 'line', 'm', data='oth', flow=True, qe=lambda: f'={PT("pt_oth")}',
      ae=lambda: f'={V("oi_int")}-{V("oi_exp")}-{V("oi_fl")}+{V("oi_other")}',
      note='Q1–Q4/27E: guided ~$(100)m a quarter excluding any OpenAI impact (Q1 guidance; Q2–Q4 held, assumption). 2028E+: interest income − interest expense on debt − finance-lease interest + other.')
    S('oi_int', '  Interest & dividend income (yield × opening cash & short-term investments)', 'line', 'm', ae=lambda: f'=({P("bs_cash")}+{P("bs_sti")})*{V("ds_r_cash")}')
    S('oi_exp', '  Interest expense on debt, net of capitalised interest (rate × opening debt)', 'line', 'm', ae=lambda: f'={P("ds_total")}*{V("ds_r_debt")}')
    S('oi_fl', '  Finance-lease interest (rate × opening finance-lease liabilities)', 'line', 'm', ae=lambda: f'={P("fl_liab")}*{V("fl_rate")}')
    S('oi_other', '  Other (investment gains / losses, FX, equity-method results excl. OpenAI): input', 'line', 'm', ae_in=0.0)
    S('is_ebt', 'Income before income taxes', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_oi")}),{V("is_oi")}+{V("is_oth")},"")')
    S('is_tax', 'Provision for income taxes', 'line', 'm', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Q1/27E: guided ~20% (Q2–Q4 held, assumption). FY26 19.4%, FY25 17.6%. 2028E+: input.')
    S('is_ni', 'Net income', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_ni_chk', '  Check: net income vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=1,0,ROUND({V("is_ni")}-{V("is_ni_pub")},0)),"")')
    S('is_ni_pub', '  Memo: net income as reported', 'memo', 'm', data='ni', flow=True)
    S('is_dda', '  Memo: depreciation, amortization & other', 'memo_calc', 'm', all=lambda: f'={V("d_dda")}')
    S('is_sbc', '  Memo: stock-based compensation', 'memo_calc', 'm', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm', data='sh_b', avg=True,
      qe=lambda: f'=${E26}${R["bb_beg"]}+(${E26}${R["bb_iss"]}-${E26}${R["bb_sh"]})*({CTX.col.q}-0.5)/4',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q1–Q4/27E: shares outstanding at 30-Jun-2026 + (issuance − buybacks) spread evenly through FY27E. 2028E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({LQ}{R["sh_dil"]}-{LQ}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dil', 'Diluted EPS ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")',
      note='Net income / weighted diluted shares (±$0.01 vs reported).')
    S('eps_dil_g', '  Diluted EPS y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: diluted EPS as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0101,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('dps', '  Dividends declared per share ($)', 'line', 'ps', data='dps', flow=True, qe=lambda: f'={PT("pt_dps")}',
      ae=lambda: f'={P("dps")}*(1+{V("dps_g")})', note='XBRL dividends declared per share (10-K / 10-Q; Q4 = FY − 9M). Q1–Q4/27E: assumed quarterly rate (input). 2028E+: prior year × (1 + growth).')
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'])
    blank()

    # ------------------------------------------------------------------ RECON 1: GAAP operating income -> adjusted operating income
    S('sec_r1', 'RECONCILIATION: GAAP OPERATING INCOME → ADJUSTED ("AS ADJUSTED") OPERATING INCOME (company definition, published FY2012–FY2017 and FY2023)', 'section',
      note='ADJUSTED OPERATING INCOME — per the release "GAAP to Non-GAAP" tables; company item labels per period are in the cell comments of the revenue-deferral row')
    S('o_op', 'Operating income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_oi")}')
    S('o_revdef', '  (+) Revenue deferrals / (recognition)', 'line', 'm', all=lambda: f'={V("d_revdef")}')
    S('o_restr', '  (+) Impairment, integration, restructuring & severance', 'line', 'm', all=lambda: f'={V("d_restr")}')
    S('o_legal', '  (+) European Commission fine', 'line', 'm', all=lambda: f'={V("d_legal")}')
    S('o_tot', '  Total operating adjusting items (pre-tax)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("o_revdef")}),{nsum(["o_revdef", "o_restr", "o_legal"])},"")')
    S('o_adj', '  = Adjusted operating income (model bridge)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+N({V("o_tot")}),"")',
      note='FY2006–FY2011: no adjusted measures published (adjusted = GAAP, flagged). Periods with no items: adjusted = GAAP.')
    S('o_adj_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company-published adjusted operating income', 'memo', 'm', data='adj_oi_pub', flow=True)
    S('o_chk', '  Check: model bridge vs company-published (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),IF(ABS({V("o_adj")}-{V("o_pub")})<=1,0,ROUND({V("o_adj")}-{V("o_pub")},0)),"n/p")')
    S('o_rev', '  Memo: adjusted revenue (GAAP revenue + revenue deferrals)', 'memo_calc', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}+N({V("o_revdef")}),"")')
    S('o_rev_pub', '  Memo: company-published adjusted revenue', 'memo', 'm', data='adj_rev_pub', flow=True)
    S('o_rev_chk', '  Check: adjusted revenue vs company-published (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("o_rev_pub")}),IF(ABS({V("o_rev")}-{V("o_rev_pub")})<=1,0,ROUND({V("o_rev")}-{V("o_rev_pub")},0)),"n/p")')
    S('o_def', '  Definition / basis (company adjusted definition in force)', 'text', 'gen',
      note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('o_adj_g', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental adjusted operating margin (Δ adjusted OI / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: net income -> EBITDA -> adjusted EBITDA (model definitions)
    S('sec_r2', 'RECONCILIATION: NET INCOME → EBIT → EBITDA → ADJUSTED EBITDA (model definitions — Microsoft publishes no EBITDA)', 'section',
      note='EBITDA (MODEL) — net income + taxes − other income (expense) = EBIT (= operating income); + depreciation, amortization & other (cash-flow line) = EBITDA; + operating adjusting items = adjusted EBITDA')
    S('r_ni', 'Net income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('r_tax', '  (+) Provision for income taxes', 'line', 'm', all=lambda: f'={V("is_tax")}')
    S('r_oth', '  (−) Other income (expense), net', 'line', 'm', all=lambda: f'=-{V("is_oth")}')
    S('r_gebit', '  = EBIT (model; equals operating income)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_tax")}+{V("r_oth")},"")')
    S('r_gebit_chk', '  Check: EBIT vs reported operating income (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("r_gebit")}),IF(ABS({V("r_gebit")}-{V("is_oi")})<=1,0,ROUND({V("r_gebit")}-{V("is_oi")},0)),"")')
    S('r_dda', '  (+) Depreciation, amortization & other (cash-flow statement)', 'line', 'm', all=lambda: f'={V("d_dda")}')
    S('r_ebitda', '  = EBITDA (model)', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_gebit")}),ISNUMBER({V("r_dda")})),{V("r_gebit")}+{V("r_dda")},"")')
    S('r_adjx', '  (+) Operating adjusting items (bridge above)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("o_tot")}),{V("o_tot")},"")')
    S('r_adj', '  = Adjusted EBITDA (model)', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda")}),ISNUMBER({V("r_adjx")})),{V("r_ebitda")}+{V("r_adjx")},"")',
      note='Model definition (labelled): adjusted operating income + depreciation, amortization & other. Used for leverage and EV / EBITDA.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_def', '  Definition / basis', 'text', 'gen')
    S('r_ebit_h', 'To adjusted EBIT, full-cost (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ebit', '  = Adjusted EBIT, full-cost (= adjusted operating income; amortization and stock-based compensation are not adjusted out)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_adj")}),{V("o_adj")},"")')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: impairment, integration, restructuring & severance (adjusted out; deducted in the DCF as a cash cost where it recurs)', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_restr")}),{V("o_restr")}+{V("o_legal")},"")')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted net income / EPS
    S('sec_r3', 'RECONCILIATION: NET INCOME / DILUTED EPS → ADJUSTED NET INCOME → ADJUSTED DILUTED EPS (company definition)', 'section',
      note='ADJUSTED EPS — net income + operating items − their tax effect + discrete tax items + OpenAI impact (after tax). FY2012–Q1 FY14: published per share only — $ = per share × diluted shares (labelled)')
    S('e_ni', 'Net income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('e_op', '  (+) Operating adjusting items (pre-tax; bridge above)', 'line', 'm', all=lambda: f'={V("o_tot")}')
    S('e_optax', '  (−) Tax effect of the operating items', 'line', 'm', flow=True,
      hist=lambda: (f'=IF(ISNUMBER({V("e_opni")}),{V("e_opni")}-{V("e_op")},IF(ISNUMBER({V("e_opps")}),ROUND({V("e_opps")}*{V("sh_dil")},0)-{V("e_op")},0))'),
      fc=lambda: '=0', note='Historical: company after-tax effect − pre-tax items; per-share-only periods: per-share effect × diluted shares − pre-tax items (rounding included).')
    S('e_opni', '  Memo: after-tax effect of the operating items (company, $m)', 'memo', 'm', data='na_op', flow=True)
    S('e_opps', '  Memo: after-tax effect of the operating items (company, $ per share; FY2012–Q1 FY14)', 'eps_memo', 'ps', data='na_op_ps')
    S('e_taxi', '  (+) Discrete tax items', 'line', 'm', all=lambda: f'={V("d_taxi")}')
    S('e_oai', '  (+) Impact from investments in OpenAI (after tax)', 'line', 'm', all=lambda: f'={V("d_openai")}')
    S('e_adjni', '  = Adjusted net income (model bridge)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("e_ni")}),{V("e_ni")}+N({V("e_op")})+N({V("e_optax")})+N({V("e_taxi")})+N({V("e_oai")}),"")')
    S('e_pubni', '  Company-published adjusted net income', 'memo', 'm', data='adj_ni_pub', flow=True)
    S('e_chkni', '  Check: model vs company-published adjusted net income (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("e_pubni")}),IF(ABS({V("e_adjni")}-{V("e_pubni")})<=1,0,ROUND({V("e_adjni")}-{V("e_pubni")},0)),"n/p")')
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted diluted EPS ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted diluted EPS ($)', 'eps_memo', 'ps', data='adj_eps_pub', labkey='ng_lab')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.015: per-share items rounded)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0151,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Adjusted diluted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_rate', '  Effective tax rate used for NOPAT (GAAP rate)', 'pct', 'pct', all=lambda: f'={V("is_etr")}')
    S('e_def', '  Definition / basis (company adjusted EPS definition)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Revenue y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_ai', '  Agents and Infra revenue y/y %', 'growth', 'pct', all=growth('ai_rev'))
    S('gm_dc', '  Devices and Consumer revenue y/y %', 'growth', 'pct', all=growth('dc_rev'))
    S('gm_az', '  Azure revenue y/y %', 'growth', 'pct', all=growth('ai_az'))
    S('gm_adjop', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating income (GAAP) y/y %', 'growth', 'pct', all=growth('is_oi'))
    S('gm_ni', '  Net income y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted diluted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('gm_adjop_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_inc', '  Incremental adjusted operating margin (Δ adjusted OI / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_rd', '  R&D % of revenue', 'pct', 'pct', all=ratio('is_rd', 'is_rev'))
    S('gm_sm', '  Sales & marketing % of revenue', 'pct', 'pct', all=ratio('is_sm', 'is_rev'))
    S('gm_ga', '  G&A % of revenue', 'pct', 'pct', all=ratio('is_ga', 'is_rev'))
    blank()
