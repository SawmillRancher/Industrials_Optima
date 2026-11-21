"""Row specification of the CACI Model sheet, part 1 (MLM template layout and process):
revenue build (organic growth + acquired revenue, company definition) -> revenue by customer type (mix) -> contract / delivery mix
memos -> backlog & awards -> reportable segments memo -> M&A lever -> group total & FY27 guidance calibration -> cost drivers ->
income statement -> GAAP-to-non-GAAP bridges -> growth & margins."""
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
def Q2v(key): return f'${Q2}${R[key]}'
def A1(key): return f'{Q1}{R[key]}'                      # Q1/27 actual
def A0(key): return f'{PQ1}{R[key]}'                     # Q1/26 actual
def QE3(key): return f'({Q2}{R[key]}+{Q3}{R[key]}+{Q4}{R[key]})'
def chk(a, b, tol=0.15, nd=1, guard=None):
    g = guard or f'AND(ISNUMBER({a}),ISNUMBER({b}))'
    return f'=IF({g},IF(ABS({a}-{b})<={tol},0,ROUND({a}-{b},{nd})),"")'

CUST = [('ic', 'Intelligence Community (IC)', 'c_ic'), ('fed', 'Federal civilian agencies', 'c_fed'), ('comm', 'Commercial and other (incl. state & local, international)', 'c_comm')]
YRS = list(range(FYC + 1, FYL + 1))

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
    SCEN_ROWS.append((r, 'pt_hdr', 'FY27 point estimates (all cases)', None, None, None, None)); r += 1
    for key, lab, vals, nf, note in V0['points']:
        SC[key] = r
        SCEN_ROWS.append((r, 'pt', lab, None, vals, None, note, nf)); r += 1
    r += 1
    SC['LEV'] = r
    SCEN_ROWS.append((r, 'lev', '  Target net debt / EBITDA (x) — leverage down to which free cash flow repays debt; buybacks beyond (2028E+)', *V0['lev'], V0['lev_note']))
    r += 2
    for name, lab, dbull, dbear, base, note, nf, clamp in V0['blocks']:
        SCEN_ROWS.append((r, 'blk', lab, dbull, 'Δ →', dbear, note, nf)); hdr = r; r += 1
        SC[name] = {}
        for y, b in zip(YRS, base):
            SC[name][y] = r; SCEN_ROWS.append((r, 'yr', f'  {y}E', hdr, b, clamp, None, nf)); r += 1
    return r

# ====================================================================== row spec
def build_spec(V0):
    S = add
    # ------------------------------------------------------------------ REVENUE BUILD
    S('sec_seg', 'OPERATING BUILD — REVENUE (organic growth + acquired revenue) · CUSTOMER MIX · BACKLOG · EBITDA MARGIN', 'section',
      note='OPERATING BUILD — modelling logic (prior-year revenue × (1 + organic growth) + acquired revenue → revenue; × EBITDA margin → EBITDA (company measure) → GAAP P&L)')
    blank()
    S('b_hdr', 'Revenue build — organic growth and acquired revenue (company definition: revenue of an acquired business counts as acquired until the first anniversary of closing)', 'block',
      note='REVENUE BUILD — CACI is managed as one business (Domestic ~97% of revenue); the company reports total and organic revenue growth')
    S('b_orgrev', '  Organic revenue (revenue excl. acquired revenue)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("b_acq")}),{V("is_rev")}-{V("b_acq")},"")',
      qe=lambda: f'={P("is_rev")}*(1+{V("b_org_g")})', ae=lambda: f'=({P("b_orgrev")}+N({P("b_acq")}))*(1+{V("b_org_g")})',
      note='History: revenue − acquired revenue. Q2–Q4/27E: prior-year quarter revenue × (1 + organic growth). 2028E+: prior-year revenue (ex future M&A) × (1 + scenario lever).')
    S('b_org_g', '  Organic revenue growth y/y %', 'growth', 'pct',
      hist=lambda: (f'=IF(AND(ISNUMBER({V("b_orgrev")}),ISNUMBER({P("is_rev")})),IFERROR({V("b_orgrev")}/{P("is_rev")}-1,""),"")' if CTX.col.prior else None),
      qe=lambda: f'={V("b_org_pre")}+{Q2v("cal_g")}', e26=lambda: f'=IFERROR({V("b_orgrev")}/{P("is_rev")}-1,"")',
      ae=lambda: '=' + CH(SC['ORG'][CTX.col.year]),
      note='Q2–Q4/27E: Q1/27 organic growth + revenue-guidance calibration Δ (Group block). 2028E–2031E: scenario lever (Bull/Base/Bear table →).')
    S('b_org_pre', '    Q2–Q4/27E organic growth before calibration (= Q1/27 organic growth)', 'driver', 'pct', qe=lambda: f'={A1("b_org_g")}')
    S('b_org_pub', '  Memo: organic growth as published by the company', 'memo', 'pct', data='org_pub',
      note='FY2006–FY2013: release "Reconciliation of Total Revenue Growth and Organic Revenue Growth" (organic revenue ÷ prior-year revenue − 1). '
           'Later: stated in the release / 10-K text only (FY2020+, where given; rounded as published). Not published = blank.')
    S('b_org_chk', '  Check: model vs published organic growth (should be 0; ±0.1pp — narrative figures are rounded)', 'check', 'pct2',
      hist=lambda: f'=IF(AND(ISNUMBER({V("b_org_pub")}),ISNUMBER({V("b_org_g")})),IF(ABS({V("b_org_g")}-{V("b_org_pub")})<=0.001,0,ROUND({V("b_org_g")}-{V("b_org_pub")},4)),"")')
    S('b_acq', '  Acquired revenue (within 12 months of closing)', 'line', 'm1', data='acq_any', flow=True,
      qe=lambda: f'={A1("b_acq")}*{V("b_acqf")}', ae_in=0.0,
      note='History: as published in the organic-growth reconciliation (FY2006–FY2013); from FY2020 derived = revenue − prior-year revenue × (1 + published organic growth) (cell comments). '
           'Q2–Q4/27E: Q1/27 acquired revenue (ARKA, closed 9-Mar-2026, and Datalynx) × share of the quarter before the first anniversary. Future deals: M&A lever below.')
    S('b_acqf', '    Share of the quarter before the acquisition anniversary (ARKA: 9-Mar-2027)', 'driver', 'pct', qe_in={2: 1.0, 3: round(67 / 90, 3), 4: 0.0},
      note='Q2/27E: full quarter; Q3/27E: 1-Jan to 8-Mar-2027 = 67 of 90 days; Q4/27E: organic.')
    S('b_acq_p', '  Acquired revenue — contribution to growth (pp of prior-year revenue)', 'pct', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("b_acq")}),ISNUMBER({P("is_rev")})),IFERROR({V("b_acq")}/{P("is_rev")},""),"")' if CTX.col.prior else None))
    S('b_m', '  EBITDA margin % (company measure; drives the P&L)', 'pct', 'pct', all=ratio('r_adj', 'is_rev'),
      qe=lambda: f'={V("b_m_pre")}+{Q2v("cal_m")}', ae=lambda: '=' + CH(SC['EBITDA_M'][CTX.col.year]),
      note='Q2–Q4/27E: margin before calibration + adjusted-net-income-guidance calibration Δ (Group block). 2028E+: scenario lever.')
    S('b_m_pre', '    Q2–Q4/27E margin before calibration (prior-year quarter + Q1/27 y/y drift)', 'driver', 'pct',
      qe=lambda: f'={P("b_m")}+({A1("b_m")}-{A0("b_m")})')
    blank()
    S('c_hdr', 'Revenue by customer type (Department of War / Intelligence Community / Federal civilian basis from FY2025; mix-driven forecast)', 'block',
      note='CUSTOMER MIX — forecast = total revenue × share; Department of War is the balancing line')
    S('c_dod', '  Department of War (Department of Defense; excl. Intelligence Community)', 'line', 'm1', data='c_dod', flow=True,
      fc=lambda: f'={V("g_rev")}-{V("c_ic")}-{V("c_fed")}-{V("c_comm")}',
      note='Customer types redefined in the Q1 FY26 release (Intelligence Community split out of DoD and Federal civilian): FY2025 quarters and FY2025 are the comparatives of the '
           'FY2026 releases (latest filing presenting the period); earlier periods on the legacy basis only (memo rows). Forecast = revenue − other customer types.')
    for k, lab, dk in CUST:
        S(f'c_{k}', f'  {lab}', 'line', 'm1', data=dk, flow=True, fc=lambda k=k: f'={V("g_rev")}*{V("s_" + k)}')
    S('c_ns', '  U.S. federal government not split on the current basis (legacy DoD + Federal civilian, to FY2024)', 'line', 'm1', data='c_ns', flow=True)
    S('c_tot', '  Revenue by customer type — total', 'line_b', 'm1', flow=True,
      all=lambda: f'=IF(ISNUMBER({V("c_comm")}),{nsum(["c_dod", "c_ic", "c_fed", "c_comm", "c_ns"])},"")')
    S('c_chk', '  Check: customer types vs consolidated revenue (should be 0)', 'check', 'm1', all=lambda: chk(V('c_tot'), V('is_rev')))
    S('s_dod', '  Department of War % of revenue', 'pct', 'pct', all=ratio('c_dod', 'is_rev'))
    for k, lab, dk in CUST:
        S(f's_{k}', f'  {lab.split(" (")[0]} % of revenue', 'pct', 'pct', all=ratio(f'c_{k}', 'is_rev'),
          qe=lambda k=k: f'={P("s_" + k)}+({A1("s_" + k)}-{A0("s_" + k)})', ae=lambda k=k: f'={P("s_" + k)}',
          note='Q2–Q4/27E: prior-year quarter share + Q1/27 y/y change in share; 2028E+: held at the 2027E share (mix is an output, not a scenario lever).' if k == 'ic' else None)
    for k, lab in (('dod', 'Department of War'), ('ic', 'Intelligence Community'), ('fed', 'Federal civilian agencies'), ('comm', 'Commercial and other')):
        S(f'cg_{k}', f'  {lab} revenue y/y %', 'growth', 'pct', all=growth(f'c_{k}'))
    S('cl_h', '  Legacy customer types as originally reported (Department of Defense incl. intelligence agencies; to FY2025):', 'sub', 'gen')
    S('cl_dod', '    Department of Defense (legacy basis)', 'memo', 'm1', data='cl_dod', flow=True)
    S('cl_fed', '    Federal civilian agencies (legacy basis)', 'memo', 'm1', data='cl_fed', flow=True)
    S('cl_comm', '    Commercial and other, as originally reported (FY2025: before the FY2026 recast)', 'memo', 'm1', data='c_comm_orig', flow=True)
    S('cl_chk', '    Check: legacy customer types vs consolidated revenue (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("cl_dod")}),IF(ABS({V("cl_dod")}+{V("cl_fed")}+IF(ISNUMBER({V("cl_comm")}),{V("cl_comm")},{V("c_comm")})-{V("is_rev")})<=0.15,0,'
                   f'ROUND({V("cl_dod")}+{V("cl_fed")}+IF(ISNUMBER({V("cl_comm")}),{V("cl_comm")},{V("c_comm")})-{V("is_rev")},1)),"")')
    blank()
    S('mx_hdr', 'Revenue mix memos — contract type · prime / subcontractor · Technology / Expertise (history as published)', 'block',
      note='MIX — disclosure rows (release schedules); not forecast')
    for k, lab, dk in (('t_cpf', 'Cost-plus-fee ("cost reimbursable" to FY2018)', 't_cpf'), ('t_ffp', 'Fixed-price', 't_ffp'), ('t_tm', 'Time-and-materials', 't_tm'),
                       ('p_prime', 'Prime contractor', 'p_prime'), ('p_sub', 'Subcontractor', 'p_sub'),
                       ('e_tech', 'Technology (published from FY2021; FY2020 from FY2021 comparatives)', 'e_tech'), ('e_exp', 'Expertise', 'e_exp')):
        S(k, f'  {lab}', 'memo', 'm1', data=dk, flow=True)
    S('mx_chk1', '  Check: contract types vs revenue (should be 0)', 'check', 'm1', hist=lambda: chk(f'({V("t_cpf")}+{V("t_ffp")}+{V("t_tm")})', V('is_rev'), guard=f'ISNUMBER({V("t_cpf")})'))
    S('mx_chk2', '  Check: prime + subcontractor vs revenue (should be 0)', 'check', 'm1', hist=lambda: chk(f'({V("p_prime")}+{V("p_sub")})', V('is_rev'), guard=f'ISNUMBER({V("p_prime")})'))
    S('mx_chk3', '  Check: Technology + Expertise vs revenue (should be 0)', 'check', 'm1', hist=lambda: chk(f'({V("e_tech")}+{V("e_exp")})', V('is_rev'), guard=f'ISNUMBER({V("e_tech")})'))
    S('mx_ffp', '  Fixed-price % of revenue', 'pct', 'pct', hist=ratio('t_ffp', 'is_rev'))
    S('mx_tech', '  Technology % of revenue', 'pct', 'pct', hist=ratio('e_tech', 'is_rev'))
    S('mx_tech_g', '  Technology revenue y/y %', 'growth', 'pct', hist=growth('e_tech'))
    S('mx_exp_g', '  Expertise revenue y/y %', 'growth', 'pct', hist=growth('e_exp'))
    S('mx_prime', '  Prime contractor % of revenue', 'pct', 'pct', hist=ratio('p_prime', 'is_rev'))
    S('dc_labor', '  Direct labor (direct costs by category; published FY2010–Q1 FY18)', 'memo', 'm1', data='dc_labor', flow=True)
    S('dc_odc', '  Other direct costs (subcontractors, materials, travel)', 'memo', 'm1', data='dc_odc', flow=True)
    S('dc_chk', '  Check: direct labor + other direct costs vs direct costs (should be 0)', 'check', 'm1',
      hist=lambda: chk(f'({V("dc_labor")}+{V("dc_odc")})', V('is_direct'), guard=f'ISNUMBER({V("dc_labor")})'))
    blank()
    S('k_hdr', 'Backlog, contract awards and book-to-bill', 'block',
      note='BACKLOG — roll-forward: opening + awards − revenue ± adjustments = closing (adjustments derived historically, nil in the forecast)')
    S('k_bl', '  Total backlog (USDm; funded + unfunded, incl. unexercised options)', 'line', 'm', data='bl_total', bs=True,
      qe=lambda: f'={PQ("k_bl")}+{V("k_awd")}-{V("is_rev")}', e26=lambda: f'={Q4}{R["k_bl"]}', ae=lambda: f'={P("k_bl")}+{V("k_awd")}-{V("is_rev")}',
      note='As stated in the release text (rounded to USD 0.1bn). FY2016: USD 2.5bn removed after a review of backlog definitions (release 17-Aug-2016).')
    S('k_fund', '  Funded backlog (USDm)', 'line', 'm', data='bl_funded', bs=True)
    S('k_awd', '  Contract awards (USDm; excl. ceilings of multi-award IDIQ contracts)', 'line', 'm1', data='awards', flow=True,
      qe=lambda: f'={V("is_rev")}*{V("k_btb")}', ae=lambda: f'={V("is_rev")}*{V("k_btb")}',
      note='Published from Q3 FY19 (FY2018 and FY2019 from comparatives). Forecast = revenue × book-to-bill input.')
    S('k_btb', '  Book-to-bill (contract awards ÷ revenue)', 'driver', 'x2', hist=ratio('k_awd', 'is_rev'), qe_in=1.0, e26=ratio('k_awd', 'is_rev'), ae_in=V0['btb'],
      note='Q2–Q4/27E 1.0x (awards are lumpy; Q1/27 2.0x); 2028E+ input (FY2019–26 average ~1.6x; trailing-twelve-month ~1.1x at Q1/27).')
    S('k_ord', '  Contract funding orders (USDm; published to FY2019)', 'memo', 'm1', data='orders', flow=True)
    S('k_adj', '  Backlog adjustments, net (derived: Δ backlog − awards + revenue; de-obligations, acquired backlog, rounding)', 'memo_calc', 'm',
      hist=lambda: ((f'=IF(AND(ISNUMBER({V("k_bl")}),ISNUMBER({(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["k_bl"]}),ISNUMBER({V("k_awd")})),'
                     f'{V("k_bl")}-{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["k_bl"]}-{V("k_awd")}+{V("is_rev")},"")')
                    if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    S('k_cov', '  Total backlog ÷ annualised revenue (years)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("k_bl")}),IFERROR({V("k_bl")}/({V("is_rev")}*{4 if CTX.col.q else 1}),""),"")')
    S('k_emp', '  Employees (approximate, Form 10-K)', 'memo', 'm', data='employees', ann=True)
    S('k_rpe', '  Revenue per employee (USD thousand)', 'memo_calc', 'm', ann=True, hist=lambda: f'=IF(ISNUMBER({V("k_emp")}),{V("is_rev")}/{V("k_emp")}*1000,"")')
    blank()
    S('sg_hdr', 'Reportable segments memo — Domestic Operations · International Operations (Form 10-K / 10-Q segment note)', 'block',
      note='SEGMENTS — memo; segment profit measure = net income to FY2025 (10-Qs), income from operations from the FY2025 10-K (ASU 2023-07)')
    S('sg_dom', '  Domestic Operations revenue', 'memo', 'm1', data='sg_dom', flow=True, note='Quarters from the 10-Q three-month columns; Q4 = fiscal year (10-K) − Q1–Q3.')
    S('sg_int', '  International Operations revenue (U.K. and the Netherlands)', 'memo', 'm1', data='sg_int', flow=True)
    S('sg_chk', '  Check: segments vs consolidated revenue (should be 0)', 'check', 'm1', hist=lambda: chk(f'({V("sg_dom")}+{V("sg_int")})', V('is_rev'), guard=f'ISNUMBER({V("sg_dom")})'))
    S('sg_int_p', '  International % of revenue', 'pct', 'pct', hist=ratio('sg_int', 'is_rev'))
    S('sgn_dom', '  Domestic Operations net income (segment measure to FY2025)', 'memo', 'm1', data='sgn_dom', flow=True)
    S('sgn_int', '  International Operations net income', 'memo', 'm1', data='sgn_int', flow=True)
    S('sgn_chk', '  Check: segment net income vs net income attributable to CACI (should be 0)', 'check', 'm1',
      hist=lambda: chk(f'({V("sgn_dom")}+{V("sgn_int")})', V('is_ni'), guard=f'ISNUMBER({V("sgn_dom")})'),
      note='Q4 FY16: the FY2016 10-K reflects the early adoption of ASU 2016-09, which the Q4 FY16 release applied to the full year; Q4 = FY − 9M as first reported differs by USD 1.0m (documented exception in the data checks; the model shows the release quarter).')
    S('sgo_dom', '  Domestic Operations income from operations (segment measure from FY2025 10-K)', 'memo', 'm1', data='sgo_dom', flow=True)
    S('sgo_int', '  International Operations income from operations', 'memo', 'm1', data='sgo_int', flow=True)
    S('sgo_chk', '  Check: segment income from operations vs consolidated (should be 0)', 'check', 'm1',
      hist=lambda: chk(f'({V("sgo_dom")}+{V("sgo_int")})', V('is_oi'), guard=f'ISNUMBER({V("sgo_dom")})'))
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — deals closed from 2028E; unallocated)', 'block',
      note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=2.5, e26_in=0.0,
      note='Assumption. ARKA: USD 2.6bn; its revenue was not disclosed (ARKA + Datalynx contributed USD 166.8m in the ~3.7 months to 30-Jun-2026 ≈ USD 0.5bn annualised, ~5x). FY2025 deals: USD 1.68bn. 2.5x input for bolt-ons.')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.06)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}', note='Mid-year convention.')
    S('m_m', '  EBITDA margin of acquired businesses %', 'driver', 'pct', e26_in=0.0, ae_in=0.16, note='Assumption: technology-weighted targets carry margins above the group average.')
    S('m_oi', '  EBITDA from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.05, note='ARKA purchase-price allocation: PP&E 5.7% of consideration.')
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.43, note='ARKA: intangibles USD 1,145m of USD 2,643m (43%); FY2025 deals 44%.')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=15, note='ARKA weighted-average life 16.6 years.')
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group Total — revenue & EBITDA (build) → FY27 guidance calibration', 'block', note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Revenue (build)', 'total', 'm1', flow=True, hist=lambda: f'={V("is_rev")}',
      fc=lambda: f'={V("b_orgrev")}+{V("b_acq")}+N({V("m_rev")})', note='Organic revenue + acquired revenue (+ future acquisitions from 2028E).')
    S('g_rev_g', '  Revenue y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: build vs consolidated revenue (should be 0)', 'check', 'm1', all=lambda: chk(V('g_rev'), V('is_rev')))
    S('g_adj', 'EBITDA (build; company measure)', 'total', 'm1', flow=True, hist=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")},"")',
      fc=lambda: f'=({V("g_rev")}-N({V("m_rev")}))*{V("b_m")}+N({V("m_oi")})',
      note='Revenue × EBITDA margin (+ future acquisitions). CACI\'s EBITDA: net income + interest and other, net + income taxes + depreciation and amortization (incl. depreciation within direct costs). Drives the GAAP P&L below.')
    S('g_adjm', '  EBITDA margin %', 'pct', 'pct', all=ratio('g_adj', 'is_rev'))
    S('g_adj_g', '  EBITDA y/y %', 'growth', 'pct', all=growth('g_adj'))
    S('g_chk_adj', '  Check: build vs EBITDA bridge (should be 0)', 'check', 'm1', all=lambda: chk(V('g_adj'), V('r_adj')))
    S('cal_guid', '  Memo: FY27 revenue guidance (scenario end-point)', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_rev']), note=V0['rev_guid_note'])
    S('cal_pre', '  Revenue before calibration (Q2–Q4/27E helper)', 'line', 'm1', qe=lambda: f'={P("is_rev")}*(1+{V("b_org_pre")})+{V("b_acq")}')
    S('cal_sens', '  Revenue sensitivity to +1.00 of organic growth (Q2–Q4/27E helper)', 'line', 'm1', qe=lambda: f'={P("is_rev")}')
    S('cal_g', '  Guidance calibration: Δ organic growth (Q2–Q4/27E)', 'driver', 'pct',
      qe=lambda: (f'=({V("cal_guid", E26)}-{A1("g_rev")}-({QE3("cal_pre")}))/({QE3("cal_sens")})' if CTX.col.q == 2 else f'={Q2v("cal_g")}'),
      note='Solves the uniform shift in organic growth (vs Q1/27) so that FY27 revenue = the guidance end-point for the active scenario.')
    S('cal_rev_chk', '  Check: FY27 revenue vs guidance end-point (should be 0)', 'check', 'm1', e26=lambda: f'=ROUND({V("g_rev")}-{V("cal_guid")},1)')
    S('cal_ani', '  Memo: FY27 adjusted net income guidance (scenario end-point)', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_ani']), note=V0['ani_guid_note'])
    S('cal_oi', '  Q2–Q4/27E EBITDA required ((adjusted NI − Q1 actual − after-tax amortization add-back) ÷ (1 − tax rate) + depreciation, amortization, interest & other)', 'memo_calc', 'm1',
      e26=lambda: (f'=({V("cal_ani")}-{A1("e_adjni")}-({QE3("d_amort")})*(1-{PT("pt_stat")}))/(1-{PT("pt_etr")})'
                   f'+({QE3("d_dep")})+({QE3("d_amort")})+({QE3("is_int")})'))
    S('cal_oi_pre', '  EBITDA before margin calibration (Q2–Q4/27E helper)', 'line', 'm1', qe=lambda: f'={V("g_rev")}*{V("b_m_pre")}')
    S('cal_m', '  Guidance calibration: Δ EBITDA margin (Q2–Q4/27E)', 'driver', 'pct',
      qe=lambda: (f'=({V("cal_oi", E26)}-({QE3("cal_oi_pre")}))/({QE3("g_rev")})' if CTX.col.q == 2 else f'={Q2v("cal_m")}'),
      note='Solves the uniform EBITDA-margin shift so that FY27 adjusted net income = the guidance end-point for the active scenario.')
    S('cal_ani_chk', '  Check: FY27 adjusted net income vs guidance end-point (should be 0)', 'check', 'm1', e26=lambda: f'=ROUND({V("e_adjni")}-{V("cal_ani")},1)')
    S('cal_eps', '  Memo: FY27 adjusted diluted EPS guidance (scenario end-point, $; on 22.3m guided shares) — information, not forced', 'eps_memo', 'ps', e26=lambda: '=' + CH(SC['out_eps']))
    S('cal_eps_d', '  Model FY27 adjusted EPS − guidance ($; model share count vs 22.3m guided)', 'eps_memo', 'ps', e26=lambda: f'={V("e_eps")}-{V("cal_eps")}')
    S('cal_gni', '  Memo: FY27 GAAP net income implied by the guidance reconciliation (scenario end-point)', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_ni']))
    S('cal_gni_d', '  Model FY27 net income − guidance (information)', 'memo_calc', 'm1', e26=lambda: f'={V("is_ni")}-{V("cal_gni")}')
    S('cal_fcf', '  Memo: FY27 free cash flow guidance (at least USD 900m)', 'memo', 'm1', e26=lambda: f'={PT("pt_fcf")}')
    S('cal_fcf_d', '  Model FY27 free cash flow − guidance floor (information)', 'memo_calc', 'm1', e26=lambda: f'={V("fcf")}-{V("cal_fcf")}')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A & EBITDA reconciling items', 'block', note='COST DRIVERS — inputs that drive forecast cost lines (Q2–Q4/27E: point estimates; 2028E+: % of revenue or schedules)')
    S('d_amort', '  Amortization of intangible assets', 'line', 'm1', data='amort', flow=True,
      qe=lambda: f'={PT("pt_amort")}', ae=lambda: f'={V("d_amort_sch")}+N({V("m_amort")})',
      note='Annual: Form 10-K (FY2006–10 note text; FY2011+ XBRL). Quarterly: published from Q3 FY21 (adjusted-net-income reconciliation; FY2021 quarters and Q3–Q4 FY20 from comparatives); '
           'not published quarterly before. Q2–Q4/27E: (FY27 guidance USD 215m − Q1) ÷ 3. 2028E+: 10-K schedule + future-acquisition amortization.')
    S('d_amort_sch', '  Amortization schedule — intangibles held at 30-Jun-2026 (10-K, input)', 'driver', 'm1', ae_in=V0['amort_sched'], note=V0['amort_note'])
    S('d_dadir', '  Depreciation within direct costs (in EBITDA add-back; not in the D&A line)', 'line', 'm1', data='da_direct', flow=True,
      qe=lambda: f'={A1("d_dadir")}', ae=lambda: f'={V("is_rev")}*{Y("d_dadir", FYC)}/{Y("is_rev", FYC)}',
      note='Company EBITDA reconciliation: "depreciation and amortization expense, including amounts within direct costs" less the income-statement line (shown from FY2020).')
    S('d_dep', '  Depreciation (D&A line − intangible amortization + depreciation within direct costs)', 'line', 'm1', data='dep_tot', flow=True,
      qe=lambda: f'={PT("pt_dep")}', ae=lambda: f'={V("is_rev")}*{V("d_dep_pct")}')
    S('d_dep_pct', '  Depreciation % of revenue', 'pct', 'pct', all=ratio('d_dep', 'is_rev'), ae_in=V0['dep_pct'])
    S('d_ind', '  Indirect costs and selling expenses % of revenue', 'pct', 'pct', all=ratio('is_ind', 'is_rev'),
      qe=lambda: f'={P("d_ind")}+({A1("d_ind")}-{A0("d_ind")})', ae_in=V0['ind_pct'],
      note='Q2–Q4/27E: prior-year quarter ratio + Q1/27 y/y drift; 2028E+ input. Direct costs are implied: revenue − indirect costs − D&A − income from operations (from the EBITDA build).')
    S('d_sbc', '  Stock-based compensation (cash-flow statement)', 'line', 'm1', data='cf_sbc', flow=True,
      qe=lambda: f'={A1("d_sbc")}', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}',
      note='Expensed inside EBITDA (CACI does not add it back). Q2–Q4/27E: Q1/27 level; 2028E+: % of revenue.')
    S('d_sbc_pct', '  Stock-based compensation % of revenue', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_adj', '  Company EBITDA adjustments (earn-out adjustments FY2011–21; FY2013 product-sale and fixed-price contract adjustments)', 'line', 'm1', data='eb_adj', flow=True,
      fc=lambda: '=0', note='Adjusting items in the company\'s "pro forma" / "adjusted" EBITDA (definition row in the bridge). None since FY2022: EBITDA is unadjusted.')
    S('d_bdiff', '  Basis difference: company reconciliation vs income statement (net interest excl. other items; NCI FY2010–16)', 'line', 'm1', data='eb_bdiff', flow=True, fc=lambda: '=0',
      note='The published reconciliation starts from net income attributable to CACI and adds back "interest income and expense, net", which excludes the other items inside "interest expense and other, net".')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF OPERATIONS (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (income from operations = EBITDA − D&A − depreciation within direct costs; direct costs implied)')
    S('is_rev', 'Revenues', 'total', 'm1', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the revenue build.')
    S('is_direct', 'Direct costs (direct labor, subcontractors, materials, other direct costs)', 'line', 'm1', data='direct', flow=True,
      fc=lambda: f'={V("is_rev")}-{V("is_ind")}-{V("is_da")}-{V("is_oi")}', note='Forecast = implied (balancing line).')
    S('is_gp', 'Revenues less direct costs', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_direct")}),{V("is_rev")}-{V("is_direct")},"")')
    S('is_gm', '  % of revenues', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('is_ind', 'Indirect costs and selling expenses', 'line', 'm1', data='indirect', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_ind")}')
    S('is_da', 'Depreciation and amortization', 'line', 'm1', data='da', flow=True, fc=lambda: f'={V("d_dep")}-{V("d_dadir")}+{V("d_amort")}')
    S('is_oi', 'Income from operations', 'total', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("is_direct")}),{V("is_rev")}-{V("is_direct")}-{V("is_ind")}-{V("is_da")},"")',
      fc=lambda: f'={V("g_adj")}-{V("is_da")}-{V("d_dadir")}-{V("d_adj")}-{V("d_bdiff")}',
      note='Forecast = EBITDA − D&A − depreciation within direct costs.')
    S('is_oi_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('is_int', 'Interest expense and other, net', 'line', 'm1', data='int_net', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_rev")}*{V("ds_r_rev")}+{V("ds_fees")}-{P("cf_end")}*{V("ds_r_cash")}',
      note='Q2–Q4/27E point estimate. 2028E+ = rate × opening term loans & notes + rate × opening revolver + fees − yield × opening cash (no circularity).')
    S('is_ebt', 'Income before income taxes', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_oi")}),{V("is_oi")}-{V("is_int")},"")')
    S('is_tax', 'Income taxes', 'line', 'm1', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Q2–Q4/27E: point estimate (Q1/27 25.2%). 2028E+: input.')
    S('is_nit', 'Net income (incl. noncontrolling interest)', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_nci', 'Noncontrolling interest in earnings of joint ventures (FY2010–16)', 'line', 'm1', data='nci', flow=True, fc=lambda: '=0')
    S('is_ni', 'Net income attributable to CACI', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_nit")}),{V("is_nit")}-N({V("is_nci")}),"")')
    S('is_ni_chk', '  Check: net income attributable vs reported (should be 0)', 'check', 'm1', hist=lambda: chk(V('is_ni'), V('is_ni_pub')))
    S('is_ni_pub', '  Memo: net income attributable to CACI as reported', 'memo', 'm1', data='ni', flow=True)
    S('is_dda', '  Memo: depreciation & amortization incl. depreciation within direct costs', 'memo_calc', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_da")}),{V("is_da")}+N({V("d_dadir")}),"")')
    S('is_sbc', '  Memo: stock-based compensation', 'memo_calc', 'm1', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share — CACI common stock)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={PQ("sh_basic")}-${E26}${R["bb_sh"]}/3+${E26}${R["bb_iss"]}/3', ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q2–Q4/27E: prior quarter − Q2–Q4 buybacks (spread evenly) + equity-plan issuance. 2028E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q1}{R["sh_dil"]}-{Q1}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")',
      note='Net income attributable / weighted diluted shares (±$0.01 vs reported).')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0101,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('dps', '  Cash dividends per share ($) — CACI pays no dividend', 'line', 'ps', all=lambda: '=0')
    blank()

    # ------------------------------------------------------------------ RECON 1: net income -> EBITDA
    S('sec_r1', 'RECONCILIATION: NET INCOME → EBITDA (company definition in force, as published from Q3 FY08) → EBITA (model)', 'section',
      note='EBITDA — per the release reconciliations; definition changes are flagged in the definition row (column where they take effect)')
    S('r_ni', 'Net income attributable to CACI (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('r_tax', '  (+) Income taxes', 'line', 'm1', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest expense and other, net', 'line', 'm1', all=lambda: f'={V("is_int")}')
    S('r_da', '  (+) Depreciation and amortization (income-statement line)', 'line', 'm1', all=lambda: f'={V("is_da")}')
    S('r_dadir', '  (+) Depreciation within direct costs', 'line', 'm1', all=lambda: f'=N({V("d_dadir")})')
    S('r_adjx', '  (+) Company adjustments (earn-out; FY2013 product-sale / fixed-price contract adjustments)', 'line', 'm1', all=lambda: f'=N({V("d_adj")})')
    S('r_bd', '  (+) Basis difference: company reconciliation vs income statement', 'line', 'm1', all=lambda: f'=N({V("d_bdiff")})')
    S('r_adj', '  = EBITDA (company measure in force; model bridge)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_tax")}+{V("r_int")}+{V("r_da")}+{V("r_dadir")}+{V("r_adjx")}+{V("r_bd")},"")',
      note='Company definition (FY2011–12 "pro forma EBITDA", FY2013 and Q2 FY16–Q3 FY23 "adjusted EBITDA"; "EBITDA" otherwise). Before Q3 FY08 no EBITDA was published: model = same build. '
           'Used for leverage (net debt / EBITDA) and EV / EBITDA.')
    S('r_adj_m', '  EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_adj_pub', '  Company-published EBITDA / adjusted EBITDA', 'memo', 'm1', data='ebitda_pub', flow=True)
    S('r_chk', '  Check: model vs company-published EBITDA (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("r_adj_pub")}),ISNUMBER({V("r_adj")})),IF(ABS({V("r_adj")}-{V("r_adj_pub")})<=0.15,0,ROUND({V("r_adj")}-{V("r_adj_pub")},1)),"n/p")')
    S('o_def', '  Definition / basis (company EBITDA definition in force)', 'text', 'gen',
      note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('r_adj_g', '  EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('r_inc', '  Incremental EBITDA margin (Δ EBITDA / Δ revenue)', 'pct', 'pct', all=incr('r_adj', 'is_rev'))
    S('r_ebit_h', 'To EBITA (EBITDA − depreciation; before amortization of acquired intangibles) — model measure for NOPAT, ROIC and the DCF:', 'sub', 'gen')
    S('r_depn', '  (−) Depreciation (incl. within direct costs)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("d_dep")}),-{V("d_dep")},"")')
    S('r_ebit', '  = Adjusted EBITA (model: EBITDA − depreciation)', 'total', 'm1', all=lambda: f'=IF(AND(ISNUMBER({V("r_adj")}),ISNUMBER({V("r_depn")})),{V("r_adj")}+{V("r_depn")},"")',
      note='Model definition (CACI publishes no EBITA): consistent with the company\'s adjusted net income, which adds back intangible amortization only. Stock-based compensation stays expensed. '
           'Available where intangible amortization is published (annual; quarterly from Q3 FY20).')
    S('r_ebit_m', '  Adjusted EBITA margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_amortn', '  (−) Amortization of intangible assets', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("d_amort")}),-{V("d_amort")},"")')
    S('r_ebitg', '  = EBIT after amortization (EBITDA − total D&A)', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ebit")}),{V("r_ebit")}+{V("r_amortn")},"")')
    S('r_cash', '  Memo: cash items adjusted out of EBITDA by the company (earn-out and contract adjustments; nil since FY2022)', 'memo_calc', 'm1', all=lambda: f'=N({V("d_adj")})')
    blank()

    # ------------------------------------------------------------------ RECON 2: adjusted net income / EPS
    S('sec_r3', 'RECONCILIATION: NET INCOME / DILUTED EPS → ADJUSTED NET INCOME → ADJUSTED DILUTED EPS (company definition in force)', 'section',
      note='ADJUSTED EPS — current definition (from Q3 FY21): net income + intangible amortization − related tax effect at the assumed statutory rate; earlier definitions flagged in the definition row')
    S('e_ni', 'Net income attributable to CACI (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('e_amort', '  (+) Intangible amortization expense (current definition)', 'line', 'm1', data='a_intang', flow=True, fc=lambda: f'={V("d_amort")}')
    S('e_old', '  (+) Earlier-definition add-backs (stock-based compensation, D&A, financing-cost amortization, non-cash interest, earn-out; Q4 FY09–Q2 FY18)', 'line', 'm1',
      data='a_old', flow=True, labkey='a_old_lab', fc=lambda: '=0')
    S('e_tax', '  (−) Related tax effect', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("e_pubni")}),{V("e_pubni")}-{V("e_ni")}-N({V("e_amort")})-N({V("e_old")}),IF(ISNUMBER({V("e_ni")}),0,""))',
      fc=lambda: f'=-{V("e_amort")}*{V("e_trate")}',
      note='Historical: published adjusted net income − net income − pre-tax add-backs. Forecast: amortization × the company\'s assumed statutory rate.')
    S('e_trate', '  Tax rate on the adjustments (company: assumed full-year statutory rate)', 'pct', 'pct',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pubni")}),N({V("e_amort")})+N({V("e_old")})<>0),-{V("e_tax")}/(N({V("e_amort")})+N({V("e_old")})),"")',
      qe=lambda: f'={PT("pt_stat")}', e26=lambda: f'=IFERROR(-{V("e_tax")}/{V("e_amort")},"")', ae=lambda: f'={PT("pt_stat")}')
    S('e_adjni', '  = Adjusted net income (model bridge; definition in force)', 'total', 'm1', flow=True,
      all=lambda: f'=IF(ISNUMBER({V("e_tax")}),{V("e_ni")}+N({V("e_amort")})+N({V("e_old")})+{V("e_tax")},"")',
      note='Periods without a published adjusted measure (to Q3 FY09; Q3 FY18–Q2 FY20) show adjusted = GAAP (flag in the definition row). See the current-definition memo below for a consistent series.')
    S('e_pubni', '  Company-published adjusted net income', 'memo', 'm1', data='adj_ni_pub', flow=True)
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted EPS – diluted ($) (model bridge; definition in force)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted diluted EPS ($)', 'eps_memo', 'ps', data='adj_eps_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0101,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_def', '  Definition / basis (company adjusted net income / EPS definition in force)', 'text', 'gen')
    S('e_cd_h', 'Current-definition memo (model rebuild for all periods with published intangible amortization; drives the P/E):', 'sub', 'gen')
    S('e_cd_rate', '  Tax rate applied to intangible amortization', 'pct', 'pct',
      hist=lambda: (f'=IF(ISNUMBER({V("d_amort")}),IF(AND(ISNUMBER({V("e_amort")}),N({V("e_amort")})<>0),{V("e_trate")},MAX(0.15,MIN(0.4,{V("is_etr")}))),"")'),
      fc=lambda: f'={V("e_trate")}',
      note='Company rate where it published the current definition; otherwise the period effective tax rate bounded to 15–40% (model assumption for the memo series only).')
    S('e_cd_ni', '  Adjusted net income — current definition (net income + intangible amortization × (1 − rate))', 'line_b', 'm1', flow=True,
      all=lambda: f'=IF(AND(ISNUMBER({V("d_amort")}),ISNUMBER({V("e_cd_rate")})),{V("is_ni")}+{V("d_amort")}*(1-{V("e_cd_rate")}),"")')
    S('e_cd_eps', '  Adjusted EPS — current definition ($)', 'eps_memo', 'ps', all=ratio('e_cd_ni', 'e_sh'))
    S('e_cd_g', '  Adjusted EPS (current definition) y/y %', 'growth', 'pct', all=growth('e_cd_eps'))
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Revenue y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_org', '  Organic revenue growth y/y % (company definition)', 'growth', 'pct', all=lambda: f'=IF(ISNUMBER({V("b_org_g")}),{V("b_org_g")},"")')
    S('gm_ebitda', '  EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Income from operations y/y %', 'growth', 'pct', all=growth('is_oi'))
    S('gm_ni', '  Net income y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_gm', '  Revenues less direct costs % of revenue', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('gm_ind', '  Indirect costs and selling expenses % of revenue', 'pct', 'pct', all=ratio('is_ind', 'is_rev'))
    S('gm_ebitda_m', '  EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_inc', '  Incremental EBITDA margin (Δ EBITDA / Δ revenue)', 'pct', 'pct', all=incr('r_adj', 'is_rev'))
    S('gm_ebita_m', '  Adjusted EBITA margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    blank()
