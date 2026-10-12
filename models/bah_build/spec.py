"""Row specification of the BAH Model sheet, part 1 (MLM template layout and process):
revenue by customer type (National Security = Defense + Intelligence; Civil & Commercial) -> Ultra Mission Solutions acquisition block ->
backlog / book-to-bill and headcount KPIs -> future M&A lever -> group revenue and adjusted EBITDA (FY27 guidance calibration) ->
cost drivers and adjusting items -> income statement (two-class EPS) -> GAAP-to-adjusted bridges -> growth & margins."""
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
def A0(key): return f'{QC[(2026, 1)].c}{R[key]}'         # Q1/26 actual
def QE3(key): return f'({Q2}{R[key]}+{Q3}{R[key]}+{Q4}{R[key]})'
def B1(key): return f'{Q1}{R[key]}'                      # 30-Jun-2026 balance

LINES = ['ns', 'cc']                                      # legacy (ex-Ultra) revenue lines by customer type
ULTRA_DAYS = {2: 38 / 91, 3: 1.0, 4: 1.0}                 # closed 24-Aug-2026: 38 of 91 days in Q2 FY27 (Jul-Sep)
OPI = ['d_acq', 'd_restr', 'd_legal', 'd_covid', 'd_sbcx', 'd_fin', 'd_oadj']   # operating adjusting items (inside operating income)

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
    SCEN_ROWS.append((r, 'lev', '  Maximum net debt / adjusted EBITDA before buybacks (x) — buyback floor 2028E+', *V0['lev'], V0['lev_note']))
    r += 2
    for name, lab, dbull, dbear, base, note, nf, clamp in V0['blocks']:
        SCEN_ROWS.append((r, 'blk', lab, dbull, 'Δ →', dbear, note, nf)); hdr = r; r += 1
        SC[name] = {}
        for y, b in zip(range(2028, 2032), base):
            SC[name][y] = r; SCEN_ROWS.append((r, 'yr', f'  {y}E', hdr, b, clamp, None, nf)); r += 1
    return r

# ====================================================================== row spec
def build_spec(V0):
    S = add
    # ------------------------------------------------------------------ REVENUE BUILD
    S('sec_seg', 'REVENUE BUILD — CUSTOMER TYPE (NATIONAL SECURITY · CIVIL & COMMERCIAL) · ULTRA MISSION SOLUTIONS · BACKLOG', 'section',
      note='REVENUE BUILD — modelling logic (one reportable segment: revenue by customer type → + Ultra Mission Solutions (closed 24-Aug-2026) + future M&A = revenue; adjusted EBITDA = revenue × margin → GAAP P&L)')
    blank()
    S('ns_hdr', 'National Security (Defense + Intelligence customers; one customer type from Q1 FY2027)', 'block', note='NATIONAL SECURITY — modelling logic')
    S('ns', '  National Security revenue (Defense + Intelligence)', 'line', 'm1', data='c_ns', flow=True,
      qe=lambda: f'={P("ns")}*(1+{V("ns_g")})', ae=lambda: f'={P("ns")}*(1+{V("ns_g")})',
      note=('Revenue by customer type (10-Q / 10-K revenue note; FY2017–18 from the FY2019 10-K comparatives; Q4 = fiscal year − nine months). '
            'Q2–Q4/27E: prior-year quarter × (1 + growth). 2028E+: prior year × (1 + scenario lever). Excludes Ultra (own block below).'))
    S('ns_g', '    y/y %', 'growth', 'pct', all=growth('ns'), qe=lambda: f'={V("ns_pre")}+{Q2v("cal_g")}',
      ae=lambda: '=' + CH(SC['NS_G'][CTX.col.year]),
      note='Q2–Q4/27E: Q1/27 y/y growth + guidance-calibration Δ (Group block). 2028E–2031E: scenario lever (Bull/Base/Bear table →).')
    S('ns_pre', '    Q2–Q4/27E growth before calibration (Q1/27 y/y)', 'driver', 'pct', qe=lambda: f'=IFERROR({A1("ns")}/{A0("ns")}-1,0)')
    S('ns_mix', '  National Security % of revenue', 'pct', 'pct', all=ratio('ns', 'is_rev'))
    S('cc_hdr', 'Civil & Commercial (Civil customers + Global Commercial)', 'block', note='CIVIL & COMMERCIAL — modelling logic')
    S('cc', '  Civil & Commercial revenue', 'line', 'm1', data='c_cc', flow=True,
      qe=lambda: f'={P("cc")}*(1+{V("cc_g")})', ae=lambda: f'={P("cc")}*(1+{V("cc_g")})',
      note='Civil customers + Global Commercial (reported separately to FY2024, inside Civil from FY2025). Same forecast logic as National Security.')
    S('cc_g', '    y/y %', 'growth', 'pct', all=growth('cc'), qe=lambda: f'={V("cc_pre")}+{Q2v("cal_g")}', ae=lambda: '=' + CH(SC['CC_G'][CTX.col.year]))
    S('cc_pre', '    Q2–Q4/27E growth before calibration (Q1/27 y/y)', 'driver', 'pct', qe=lambda: f'=IFERROR({A1("cc")}/{A0("cc")}-1,0)')
    S('cc_mix', '  Civil & Commercial % of revenue', 'pct', 'pct', all=ratio('cc', 'is_rev'))
    S('out_rev', '  Revenue outside the customer split (FY2012–16 not split; FY2017–18 ASC 606 recast basis difference; rounding) — derived', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("ns")}),{V("is_rev")}-{V("ns")}-{V("cc")},{V("is_rev")})', fc=lambda: '=0',
      note=('Derived = revenue − Σ customer types, so the build ties in every period. FY2012–16: no customer split published (whole revenue). FY2017–18: the split comes from the '
            'FY2019 10-K (ASC 606 full-retrospective recast: $5,809.5m / $6,167.6m vs $5,804.3m / $6,171.9m as originally reported). From FY2025 the 10-Q tables are in whole $m (±1 rounding).'))
    S('leg_h', '  Legacy customer types (as reported; replaced by National Security / Civil & Commercial):', 'sub', 'gen')
    for k, lab in (('def', 'Defense'), ('intel', 'Intelligence'), ('civ', 'Civil (incl. Global Commercial from FY2025)'), ('com', 'Global Commercial (to FY2024)')):
        S(f'leg_{k}', f'    {lab}', 'memo', 'm1', data=f'c_{k}', flow=True)
    S('leg_chk', '    Check: legacy customer types vs National Security + Civil & Commercial (should be 0; ±0.15, ±0.6 from Q4 FY25)', 'check', 'm1',
      hist=lambda: (f'=IF(ISNUMBER({V("leg_def")}),IF(ABS({V("leg_def")}+{V("leg_intel")}+{V("leg_civ")}+N({V("leg_com")})-{V("ns")}-{V("cc")})<=1,0,'
                    f'ROUND({V("leg_def")}+{V("leg_intel")}+{V("leg_civ")}+N({V("leg_com")})-{V("ns")}-{V("cc")},1)),"")'))
    blank()
    # ------------------------------------------------------------------ Ultra Mission Solutions
    S('ul_hdr', 'Ultra I&C Mission Solutions — acquired 24-Aug-2026 for $720m (National Security defense technology; revenue not disclosed)', 'block',
      note='ULTRA MISSION SOLUTIONS — modelling logic (closed after the FY27 guidance; added on top of the calibrated legacy business)')
    S('ul_run', '  Annualised revenue run-rate (USDm; FY2027E = assumption, then × (1 + growth))', 'driver', 'm1', e26_in=V0['ul_run'],
      ae=lambda: f'={P("ul_run")}*(1+{V("ul_g")})',
      note=MAN['deals']['ultra'] + ' Run-rate $' + f'{V0["ul_run"]:.0f}' + 'm is an ASSUMPTION (~4x EV / sales); replace with the Q2 FY27 10-Q disclosure.')
    S('ul_g', '    Growth % (scenario lever from 2028E; company: "strong double-digit rate for the next several years")', 'growth', 'pct',
      ae=lambda: '=' + CH(SC['ULTRA_G'][CTX.col.year]))
    S('ul_days', '  Share of the quarter consolidated (closed 24-Aug-2026: 38 of 91 days in Q2/27)', 'driver', 'pct', qe_in=ULTRA_DAYS)
    S('ul_rev', '  Ultra revenue', 'line_b', 'm1', flow=True, qe=lambda: f'=${E26}${R["ul_run"]}/4*{V("ul_days")}', ae=lambda: f'={V("ul_run")}')
    S('ul_m', '  Adjusted EBITDA margin % (company: "EBITDA margins well above 20%")', 'driver', 'pct',
      qe=lambda: f'={PT("pt_ul_m")}', e26=lambda: f'={PT("pt_ul_m")}', ae=lambda: '=' + CH(SC['ULTRA_M'][CTX.col.year]))
    S('ul_ebitda', '  Ultra adjusted EBITDA', 'line', 'm1', flow=True, qe=lambda: f'={V("ul_rev")}*{V("ul_m")}', ae=lambda: f'={V("ul_rev")}*{V("ul_m")}')
    S('ul_cons', '  Consideration (USDm; 8-K 22-Jun-2026, subject to adjustments)', 'driver', 'm1', e26_in=720.0)
    S('ul_intp', '  Acquired intangibles % of consideration (assumption; Defy 37%)', 'driver', 'pct', e26_in=V0['ul_intp'])
    S('ul_life', '  Intangible amortization life (years; assumption)', 'driver', 'gen', e26_in=V0['ul_life'])
    S('ul_amort', '  Ultra acquisition amortization (adjusted out by the company)', 'line', 'm1', flow=True,
      qe=lambda: f'=${E26}${R["ul_cons"]}*${E26}${R["ul_intp"]}/${E26}${R["ul_life"]}/4*{V("ul_days")}',
      ae=lambda: f'={Y("ul_cons", 2027)}*{Y("ul_intp", 2027)}/{Y("ul_life", 2027)}')
    blank()
    # ------------------------------------------------------------------ backlog & KPIs
    S('bl_hdr', 'Backlog, book-to-bill & headcount (operating data, release Exhibit 5)', 'block',
      note='BACKLOG — roll-forward: closing = opening + net bookings − revenue; net bookings = revenue × book-to-bill (company definition)')
    S('bl_funded', '  Funded backlog', 'line', 'm', data='bl_funded', bs=True)
    S('bl_unfunded', '  Unfunded backlog', 'line', 'm', data='bl_unfunded', bs=True)
    S('bl_options', '  Priced options', 'line', 'm', data='bl_options', bs=True)
    S('bl_total', '  Total backlog (period end)', 'line_b', 'm', data='bl_total', bs=True,
      qe=lambda: f'={PQ("bl_total")}+{V("bl_book")}-{V("is_rev")}', e26=lambda: f'={Q4}{R["bl_total"]}', ae=lambda: f'={P("bl_total")}+{V("bl_book")}-{V("is_rev")}',
      note='Company definition: funded + unfunded + priced options (100% of unexercised option value). Acquired backlog (EverWatch, Liberty, Defy, Ultra) enters through net bookings.')
    S('bl_book', '  Net bookings (Δ total backlog + revenue; incl. acquired backlog)', 'line', 'm', flow=True,
      hist=lambda: (f'=IF(AND(ISNUMBER({V("bl_total")}),ISNUMBER({(CTX.col.prevq if CTX.col.q else CTX.col.prior) or "X"}{R["bl_total"]})),'
                    f'{V("bl_total")}-{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["bl_total"]}+{V("is_rev")},"")') if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None,
      qe=lambda: f'={V("is_rev")}*{V("bl_b2b")}', ae=lambda: f'={V("is_rev")}*{V("bl_b2b")}')
    S('bl_b2b', '  Book-to-bill (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("bl_book")}),IFERROR({V("bl_book")}/{V("is_rev")},""),"")',
      qe_in=1.0, e26=lambda: f'=IFERROR({V("bl_book")}/{V("is_rev")},"")', ae=lambda: '=' + CH(SC['B2B'][CTX.col.year]),
      note='Q2–Q4/27E 1.0x (government awards are lumpy; Q1/27 1.5x, TTM 1.1x). 2028E+: scenario lever.')
    S('bl_b2b_pub', '  Memo: book-to-bill as published (quarter / fiscal year)', 'memo', 'x2', data='b2b_q', ann_data='b2b_ytd')
    S('bl_cov', '  Total backlog / revenue (x, annualised)', 'line', 'x2',
      all=lambda: f'=IF(ISNUMBER({V("bl_total")}),IFERROR({V("bl_total")}/({V("is_rev")}*{4 if CTX.col.q else 1}),""),"")')
    S('bl_fund_p', '  Funded backlog % of total', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("bl_funded")}),IFERROR({V("bl_funded")}/{V("bl_total")},""),"")')
    S('hc_total', '  Total headcount (period end)', 'line', 'm', data='hc_total', bs=True)
    S('hc_staff', '  Client / customer staff headcount (period end)', 'line', 'm', data='hc_staff', bs=True)
    S('hc_rxb', '  Revenue ex-billable expenses per average customer-staff head ($000, annualised)', 'line', 'm1',
      hist=lambda: (f'=IFERROR({V("rev_xb")}*{4 if CTX.col.q else 1}/AVERAGE({V("hc_staff")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["hc_staff"]})*1000,"")'
                    if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    S('ct_h', '  Revenue by contract type (% of revenue):', 'sub', 'gen')
    for k, lab in (('ct_cr', 'Cost-reimbursable'), ('ct_tm', 'Time-and-materials'), ('ct_fp', 'Fixed-price')):
        S(k, f'    {lab}', 'pct', 'pct', data=k)
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — bolt-ons from 2028E)', 'block', note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=2.0, e26_in=0.0,
      note='Assumption: technology-services bolt-ons ~1.5–2.5x sales (Liberty IT Solutions $725m, Q2 FY22; EverWatch $440m, Q3 FY23; Defy $235m, Q1 FY27 — target revenue not disclosed).')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.05)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}', note='Mid-year convention.')
    S('m_m', '  Adjusted EBITDA margin of acquired businesses %', 'driver', 'pct', e26_in=0.0, ae_in=0.12)
    S('m_ebitda', '  Adjusted EBITDA from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.02)
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.35,
      note='Defy Security (Apr-2026): intangibles $86m of $235m (37%), goodwill $129m (Q1 FY27 10-Q Note 5).')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=8)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (adjusted out as acquisition amortization)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group Total — revenue & adjusted EBITDA (build) → FY27 guidance calibration', 'block', note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_leg', '  Legacy revenue (excl. Ultra and future M&A; FY27 guidance basis)', 'line', 'm1', flow=True,
      all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("ns")}*N(ISNUMBER({V("ns")}))+N({V("cc")})+N({V("out_rev")}),"")',
      fc=lambda: f'={V("ns")}+{V("cc")}+{V("out_rev")}')
    S('g_rev', 'Revenue (build)', 'total', 'm1', hist=lambda: f'={V("g_leg")}', fc=lambda: f'={V("g_leg")}+{V("ul_rev")}+N({V("m_rev")})',
      note='Σ customer types + Ultra + future acquisitions.')
    S('g_rev_g', '  Revenue y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: build vs consolidated revenue (should be 0; ±0.15, ±0.6 from Q4 FY25)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<={TL()},0,ROUND({V("g_rev")}-{V("is_rev")},1)),"")')
    S('g_lm', '  Legacy adjusted EBITDA margin on revenue %', 'pct', 'pct',
      hist=lambda: f'=IF(ISNUMBER({V("r_adj")}),IFERROR({V("r_adj")}/{V("is_rev")},""),"")',
      qe=lambda: f'={V("g_lm_pre")}+{Q2v("cal_m")}', e26=lambda: f'=IFERROR({V("g_lebitda")}/{V("g_leg")},"")',
      ae=lambda: '=' + CH(SC['ADJ_M'][CTX.col.year]),
      note=('History = company adjusted EBITDA margin on revenue. Q2–Q4/27E: prior-year quarter margin + Q1/27 y/y drift + calibration Δ. '
            '2028E+: scenario lever on legacy revenue.'))
    S('g_lm_pre', '  Q2–Q4/27E margin before calibration (prior-year quarter + Q1/27 y/y drift)', 'driver', 'pct',
      qe=lambda: f'={P("g_lm")}+IFERROR({A1("g_lm")}-{A0("g_lm")},0)')
    S('g_lebitda', '  Legacy adjusted EBITDA', 'line', 'm1', flow=True, hist=lambda: f'={V("r_adj")}',
      qe=lambda: f'={V("g_leg")}*{V("g_lm")}', ae=lambda: f'={V("g_leg")}*{V("g_lm")}')
    S('g_adj', 'Adjusted EBITDA (build)', 'total', 'm1', hist=lambda: f'={V("g_lebitda")}',
      fc=lambda: f'={V("g_lebitda")}+{V("ul_ebitda")}+N({V("m_ebitda")})',
      note='Legacy + Ultra + future acquisitions. Company definition; drives the GAAP P&L below (operating income = adjusted EBITDA − D&A − operating adjusting items).')
    S('g_adjm', '  Adjusted EBITDA margin on revenue %', 'pct', 'pct', all=ratio('g_adj', 'is_rev'))
    S('g_chk_adj', '  Check: build vs adjusted EBITDA bridge (should be 0; ±0.15, ±0.6 from Q4 FY25)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_adj")}),ISNUMBER({V("r_adj")})),IF(ABS({V("g_adj")}-{V("r_adj")})<={TL()},0,ROUND({V("g_adj")}-{V("r_adj")},1)),"")')
    S('cal_guid', '  Memo: FY27 revenue guidance (scenario end-point; legacy basis, excl. Ultra — assumption)', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_rev']),
      note=V0['rev_guid_note'])
    S('cal_pre', '  Legacy revenue before calibration (Q2–Q4/27E helper)', 'line', 'm1', qe=lambda: '=' + '+'.join(f'{P(k)}*(1+{V(k + "_pre")})' for k in LINES))
    S('cal_sens', '  Revenue sensitivity to +1.00 of growth (Q2–Q4/27E helper)', 'line', 'm1', qe=lambda: '=' + '+'.join(P(k) for k in LINES))
    S('cal_g', '  Guidance calibration: Δ y/y growth applied to both customer types (Q2–Q4/27E)', 'driver', 'pct',
      qe=lambda: (f'=({V("cal_guid", E26)}-{A1("g_leg")}-({QE3("cal_pre")}))/({QE3("cal_sens")})' if CTX.col.q == 2 else f'={Q2v("cal_g")}'),
      note='Solves the uniform growth shift (vs Q1/27 y/y rates) so that FY27 legacy revenue = the guidance end-point for the active scenario (closed form; no circularity).')
    S('cal_rev_chk', '  Check: FY27 legacy revenue vs guidance end-point (should be 0; ±0.15, ±0.6 from Q4 FY25)', 'check', 'm1', e26=lambda: f'=ROUND({V("g_leg")}-{V("cal_guid")},1)')
    S('cal_eb', '  Memo: FY27 adjusted EBITDA guidance (scenario end-point; legacy basis)', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_ebitda']), note=V0['eb_guid_note'])
    S('cal_eb_pre', '  Legacy adjusted EBITDA before margin calibration (Q2–Q4/27E helper)', 'line', 'm1', qe=lambda: f'={V("g_leg")}*{V("g_lm_pre")}')
    S('cal_m', '  Guidance calibration: Δ adjusted EBITDA margin (Q2–Q4/27E)', 'driver', 'pct',
      qe=lambda: (f'=({V("cal_eb", E26)}-{A1("g_lebitda")}-({QE3("cal_eb_pre")}))/({QE3("g_leg")})' if CTX.col.q == 2 else f'={Q2v("cal_m")}'),
      note='Solves the uniform margin shift so that FY27 legacy adjusted EBITDA = the guidance end-point for the active scenario.')
    S('cal_eb_chk', '  Check: FY27 legacy adjusted EBITDA vs guidance end-point (should be 0; ±0.15, ±0.6 from Q4 FY25)', 'check', 'm1', e26=lambda: f'=ROUND({V("g_lebitda")}-{V("cal_eb")},1)')
    S('cal_eps', '  Memo: FY27 adjusted diluted EPS guidance (scenario end-point, $) — information, not forced', 'eps_memo', 'ps', e26=lambda: '=' + CH(SC['out_eps']))
    S('cal_eps_d', '    Model FY27 adjusted EPS − guidance ($; incl. Ultra, which the guidance is assumed to exclude)', 'eps_memo', 'ps', e26=lambda: f'={V("e_eps")}-{V("cal_eps")}')
    S('cal_fcf', '  Memo: FY27 free cash flow guidance (scenario end-point) — solved via payables & accrued % (working-capital block)', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_fcf']))
    S('cal_sh_d', '    Model FY27 diluted shares − guidance mid-point (119m)', 'memo_calc', 'm1', e26=lambda: f'={V("sh_dil")}-119')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A & adjusting items', 'block', note='COST DRIVERS — inputs that drive forecast cost lines (Q2–Q4/27E: point estimates / drift; 2028E+: % of revenue or schedules)')
    S('d_bill', '  Billable expenses % of revenue', 'pct', 'pct', all=ratio('is_bill', 'is_rev'),
      qe=lambda: f'={P("d_bill")}+IFERROR({A1("d_bill")}-{A0("d_bill")},0)', ae_in=V0['bill_pct'],
      note='Subcontractor, travel and other direct non-labor costs (pass-through, low margin). Q2–Q4/27E: prior-year quarter + Q1/27 y/y drift; 2028E+ input.')
    S('d_cost', '  Cost of revenue (direct labor & related) % of revenue', 'pct', 'pct', all=ratio('is_cost', 'is_rev'),
      qe=lambda: f'={P("d_cost")}+IFERROR({A1("d_cost")}-{A0("d_cost")},0)', ae_in=V0['cost_pct'],
      note='G&A is the implied balancing line: revenue − cost of revenue − billable expenses − D&A − operating income (from the adjusted EBITDA build).')
    S('d_dda', '  Depreciation & amortization (total, income statement)', 'line', 'm1', flow=True,
      all=lambda: f'=IF(AND(ISNUMBER({V("d_dep")}),ISNUMBER({V("d_acqam")})),{V("d_dep")}+{V("d_acqam")},"")')
    S('d_acqam', '  Acquisition amortization (adjusted out of adjusted net income / operating income where the company did so)', 'line', 'm1', data='an_amort', flow=True,
      qe=lambda: f'=({PT("pt_amort")}-{A1("d_acqam")})/3+{V("ul_amort")}', ae=lambda: f'={V("d_acqam_sch")}+{V("ul_amort")}+N({V("m_amort")})',
      labkey='an_amort_lab',
      note=('Carlyle-acquisition intangibles to FY2017; none adjusted FY2018–21; "significant acquisition amortization" (Liberty, EverWatch, PGSC, Defy) from FY2022. '
            'Q2–Q4/27E: FY27 point estimate (excl. Ultra) + Ultra. 2028E+: schedule + Ultra + future M&A.'))
    S('d_acqam_sch', '  Acquisition amortization schedule excl. Ultra (input; 10-K schedule ratios applied to the Q1/27 run-rate)', 'driver', 'm1', ae_in=V0['acqam_sched'],
      note=V0['acqam_note'])
    S('d_dep', '  Depreciation & other amortization (D&A − acquisition amortization adjusted out)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("is_da")}),{V("is_da")}-{V("d_acqam")},"")',
      qe=lambda: f'=({PT("pt_dep")}-{A1("d_dep")})/3', ae=lambda: f'={V("is_rev")}*{V("d_dep_pct")}')
    S('d_dep_pct', '  Depreciation & other amortization % of revenue', 'pct', 'pct', all=ratio('d_dep', 'is_rev'), ae_in=V0['dep_pct'])
    S('d_sbc', '  Stock-based compensation (cash-flow statement)', 'line', 'm1', data='cf_sbc', flow=True,
      qe=lambda: f'=({PT("pt_sbc")}-{A1("d_sbc")})/3', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}',
      note='Booz Allen does not adjust out stock-based compensation (since FY2016; FY2012–15 only the Carlyle-acquisition option expense).')
    S('d_sbc_pct', '  Stock-based compensation % of revenue', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_adj_h', '  Adjusting items (pre-tax, adjusted out by the company; forecast inputs):', 'sub', 'gen')
    S('d_acq', '  Acquisition, divestiture, transaction & other corporate expenses', 'line', 'm1', data='eb_acq', flow=True, labkey='eb_acq_lab',
      qe=lambda: f'=({PT("pt_acqc")}-{A1("d_acq")})/3', ae=lambda: f'={V("m_spend")}*{V("d_acq_pct")}',
      note='Q2–Q4/27E: Ultra transaction & integration costs (assumption, FY27 point estimate). 2028E+: % of acquisition spend.')
    S('d_acq_pct', '  Acquisition costs % of acquisition spend', 'pct', 'pct', ae_in=0.03)
    S('d_restr', '  Restructuring (FY2012 restructuring charge net of revenue; FY2022)', 'line', 'm1', data='eb_restr', flow=True, labkey='eb_restr_lab', fc=lambda: '=0')
    S('d_legal', '  Legal matter reserve, change in provision for claimed costs, insurance recoveries, DC tax assessment', 'line', 'm1', data='eb_legal', flow=True,
      labkey='eb_legal_lab', fc=lambda: '=0',
      note='FY2023–24 $377m legal reserve (DOJ civil settlement); Q2 FY25 claimed-costs provision release ($113m, booked in revenue) and insurance recoveries ($115m).')
    S('d_covid', '  COVID-19 supplemental employee benefits (FY2020–22)', 'line', 'm1', data='eb_covid', flow=True, labkey='eb_covid_lab', fc=lambda: '=0')
    S('d_sbcx', '  Certain stock-based compensation (Carlyle-acquisition options; FY2012–15)', 'line', 'm1', data='eb_sbc', flow=True, labkey='eb_sbc_lab', fc=lambda: '=0')
    S('d_fin', '  Financing transaction costs (debt refinancing costs in G&A)', 'line', 'm1', data='eb_fin', flow=True, labkey='eb_fin_lab', fc=lambda: '=0')
    S('d_oadj', '  Other operating items', 'line', 'm1', data='eb_other', flow=True, labkey='eb_other_lab', fc=lambda: '=0')
    S('d_nonop', '  Non-operating items (debt issuance-cost amortization / write-offs, debt extinguishment, gains on divestitures & investments)', 'line', 'm1',
      data='an_nonop', flow=True, labkey='an_nonop_lab', qe=lambda: f'=({PT("pt_nonop")}-{A1("d_nonop")})/3', ae_in=V0['nonop_ae'],
      note='In adjusted net income only (below operating income). Forecast: amortization of debt issuance costs (input).')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF OPERATIONS (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (operating income = adjusted EBITDA − D&A − operating adjusting items; G&A implied)')
    S('is_rev', 'Revenue', 'total', 'm1', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the revenue build.')
    S('is_cost', 'Cost of revenue', 'line', 'm1', data='cost_rev', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_cost")}')
    S('is_bill', 'Billable expenses', 'line', 'm1', data='bill', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_bill")}')
    S('is_ga', 'General and administrative expenses', 'line', 'm1', data='ga', flow=True,
      fc=lambda: f'={V("is_rev")}-{V("is_cost")}-{V("is_bill")}-{V("is_da")}-{V("is_restr")}-{V("is_othop")}-{V("is_oi")}',
      note='Forecast = implied balancing line (revenue − other operating costs − operating income).')
    S('is_da', 'Depreciation and amortization', 'line', 'm1', data='da', flow=True, fc=lambda: f'={V("d_dda")}')
    S('is_restr', 'Restructuring charge (shown separately in FY2012)', 'line', 'm1', data='restr', flow=True, fc=lambda: '=0')
    S('is_othop', 'Other operating costs (none presented separately since FY2012)', 'line', 'm1', data='oth_op', flow=True, fc=lambda: '=0')
    S('is_oi', 'Operating income', 'total', 'm1', data='oi', flow=True, fc=lambda: f'={V("g_adj")}-{V("is_da")}-{V("o_items")}',
      note='Forecast = adjusted EBITDA − D&A − operating adjusting items.')
    S('is_oi_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('is_int', 'Interest expense (gross to Q3 FY2025; net of interest income from Q4 FY2025)', 'line', 'm1', data='int_exp', flow=True,
      qe=lambda: f'=({PT("pt_int")}-{A1("is_int")})/3',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_rev")}*{V("ds_r_rev")}+{V("ds_fees")}-{P("cf_end")}*{V("ds_r_cash")}',
      note=('From the Q4 FY25 release interest income is netted in "interest expense, net" (previously in other income); FY2025 annual is on the new basis, Q1–Q3 FY25 on the old. '
            'Q2–Q4/27E: FY27 point estimate. 2028E+ = rate × opening notes & term loans + rate × opening revolver + fees − yield × opening cash (no circularity).'))
    S('is_oth', 'Other income (expense), net', 'line', 'm1', data='oth_inc', flow=True, qe=lambda: f'=({PT("pt_oth")}-{A1("is_oth")})/3', ae_in=V0['oth_ae'],
      note='Gains / losses on investments and dispositions; interest income to Q3 FY2025. 2028E+ input.')
    S('is_ebt', 'Income before income taxes', 'line_b', 'm1', data='ebt', flow=True, fc=lambda: f'={V("is_oi")}-{V("is_int")}+{V("is_oth")}')
    S('is_tax', 'Income tax expense (benefit)', 'line', 'm1', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Q2–Q4/27E: FY27 guidance 20–23% (Q1/27 21.1%). 2028E+: input. FY2021, FY2024 and FY2026 include discrete benefits (tax method change, IRS agreement).')
    S('is_ni', 'Net income', 'line_b', 'm1', data='ni', flow=True, fc=lambda: f'={V("is_ebt")}-{V("is_tax")}')
    S('is_nci', '  Net income attributable to non-controlling interest (FY2020–25)', 'line', 'm1', data='nci', flow=True, fc=lambda: '=0')
    S('is_nic', 'Net income attributable to common stockholders', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_ni")}),{V("is_ni")}-N({V("is_nci")}),"")')
    S('is_ni_chk', '  Check: net income attributable vs reported (should be 0; ±0.15, ±0.6 from Q4 FY25)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_nic")}-{V("is_ni_pub")})<={TL()},0,ROUND({V("is_nic")}-{V("is_ni_pub")},1)),"")')
    S('is_ni_pub', '  Memo: net income attributable to common stockholders as reported', 'memo', 'm1', data='ni_c', flow=True)
    S('is_dda', '  Memo: depreciation & amortization (total)', 'memo_calc', 'm1', all=lambda: f'={V("d_dda")}')
    S('is_sbc', '  Memo: stock-based compensation', 'memo_calc', 'm1', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share — Class A common stock; two-class method)', 'sub', 'gen')
    S('eps_alloc', '  Earnings allocated to participating securities (unvested restricted stock; two-class method)', 'line', 'm1', data='alloc', flow=True,
      fc=lambda: f'={V("is_nic")}*{V("eps_allocp")}',
      note='Net income attributable − earnings for diluted EPS (XBRL "UndistributedEarningsDiluted", as first filed; Q4 = fiscal year − nine months).')
    S('eps_allocp', '  Allocation % of net income attributable', 'pct', 'pct', all=ratio('eps_alloc', 'is_nic'), qe=lambda: f'={PT("pt_alloc")}', ae=lambda: f'={PT("pt_alloc")}')
    S('eps_earn', '  Earnings for diluted EPS', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("eps_alloc")}),{V("is_nic")}-{V("eps_alloc")},"")')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={A1("bs_shares")}-${E26}${R["bb_sh"]}/3*{ {2: 0.5, 3: 1.5, 4: 2.5}[CTX.col.q] }+${E26}${R["bb_iss"]}/3*{ {2: 0.5, 3: 1.5, 4: 2.5}[CTX.col.q] }',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note=('Q2–Q4/27E: Class A shares outstanding at 30-Jun-2026 − Q2–Q4 buybacks + equity-plan issuance (mid-quarter). 2027E+: average of beginning and ending shares. '
            'Q1 FY22 basic shares are not in the XBRL company facts (blank).'))
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({A1("sh_dil")}-{A1("sh_basic")})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("eps_earn")}/{V("sh_dil")},""),"")',
      note='Earnings for diluted EPS (two-class) / weighted diluted shares (±$0.01 vs reported).')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0101,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('dps', '  Cash dividends paid per share ($)', 'line', 'ps', data='dps', flow=True, qe_in=V0['dps_q'],
      ae=lambda: f'={P("dps")}*(1+{V("dps_g")})', note='Quarterly dividend $0.59 (declared 24-Jul-2026). 2028E+: prior year × (1 + growth).')
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'])
    blank()

    # ------------------------------------------------------------------ RECON 1: OI -> adjusted OI
    S('sec_r1', 'RECONCILIATION: OPERATING INCOME → ADJUSTED OPERATING INCOME (company definition, published FY2012 – Q3 FY2025)', 'section',
      note='ADJUSTED OPERATING INCOME — per the release reconciliations; not published from Q4 FY2025 (model continuation on the last definition)')
    S('o_op', 'Operating income (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_oi")}')
    S('o_items', '  (+) Operating adjusting items (as in adjusted EBITDA)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("d_acq")}),{nsum(OPI)},"")')
    S('o_amort', '  (+) Acquisition amortization (adjusted out)', 'line', 'm1', all=lambda: f'=N({V("d_acqam")})')
    S('o_adj', '  = Adjusted operating income (model bridge)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+N({V("o_items")})+{V("o_amort")},"")')
    S('o_adj_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company-published adjusted operating income', 'memo', 'm1', data='adj_oi_pub', flow=True)
    S('o_chk', '  Check: model bridge vs company-published (should be 0; ±0.15, ±0.6 from Q4 FY25)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),IF(ABS({V("o_adj")}-{V("o_pub")})<={TL()},0,ROUND({V("o_adj")}-{V("o_pub")},1)),"n/p")')
    S('o_def', '  Definition / basis (company adjusted definition in force)', 'text', 'gen', note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    blank()

    # ------------------------------------------------------------------ RECON 2: NI -> EBITDA -> adjusted EBITDA
    S('sec_r2', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (company definitions, as published)', 'section',
      note='EBITDA — net income + income tax + interest & other, net + D&A; adjusted EBITDA adds back the operating adjusting items (company definition)')
    S('r_ni', 'Net income attributable to common stockholders', 'line_b', 'm1', all=lambda: f'={V("is_nic")}')
    S('r_nci', '  (+) Non-controlling interest (where the company bridge starts from consolidated net income: FY2022, Q3–Q4 FY2022)', 'line', 'm1', data='eb_nci', flow=True,
      fc=lambda: '=0')
    S('r_tax', '  (+) Income tax expense (benefit)', 'line', 'm1', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest & other, net (interest expense − other income)', 'line', 'm1', all=lambda: f'={V("is_int")}-{V("is_oth")}')
    S('r_da', '  (+) Depreciation and amortization', 'line', 'm1', all=lambda: f'={V("is_da")}')
    S('r_ebitda', '  = EBITDA', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+N({V("r_nci")})+{V("r_tax")}+{V("r_int")}+{V("r_da")},"")')
    S('r_ebitda_pub', '  Company-published EBITDA', 'memo', 'm1', data='ebitda_pub', flow=True)
    S('r_ebitda_chk', '  Check: model vs company-published EBITDA (should be 0; ±0.15, ±0.6 from Q4 FY25)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_ebitda_pub")}),IF(ABS({V("r_ebitda")}-{V("r_ebitda_pub")})<={TL()},0,ROUND({V("r_ebitda")}-{V("r_ebitda_pub")},1)),"n/p")')
    S('r_items', '  (+) Operating adjusting items', 'line', 'm1', all=lambda: f'={V("o_items")}')
    S('r_adj', '  = Adjusted EBITDA', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{V("r_ebitda")}+N({V("r_items")}),"")',
      note='Company definition. Used for leverage (net debt / adjusted EBITDA, the company "net leverage ratio") and EV / EBITDA.')
    S('r_adj_m', '  Adjusted EBITDA margin on revenue %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_adj_xm', '  Adjusted EBITDA margin on revenue ex-billable expenses %', 'pct', 'pct', all=ratio('r_adj', 'rev_xb'))
    S('r_adj_pub', '  Company-published adjusted EBITDA', 'memo', 'm1', data='adj_ebitda_pub', flow=True)
    S('r_chk', '  Check: model vs company-published adjusted EBITDA (should be 0; ±0.15, ±0.6 from Q4 FY25)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("r_adj_pub")}),ISNUMBER({V("r_adj")})),IF(ABS({V("r_adj")}-{V("r_adj_pub")})<={TL()},0,ROUND({V("r_adj")}-{V("r_adj_pub")},1)),"n/p")')
    S('r_def', '  Definition / basis (company adjusted EBITDA definition)', 'text', 'gen')
    S('r_ebit_h', 'To adjusted EBITA / EBIT (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ebita', '  = Adjusted EBITA (adjusted EBITDA − depreciation & other amortization; before acquisition amortization)', 'line_b', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}-{V("d_dep")},"")')
    S('r_ebit', '  = Adjusted EBIT, full-cost (adjusted EBITDA − total D&A)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}-{V("d_dda")},"")')
    S('r_ebit_m', '  Adjusted EBIT (full-cost) margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: acquisition, restructuring, legal & financing costs (cash items adjusted out; deducted in the DCF)', 'memo_calc', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("d_acq")}),{V("d_acq")}+{V("d_restr")}+{V("d_legal")}+{V("d_fin")},"")')
    S('rx_h', '  Revenue, excluding billable expenses (company non-GAAP):', 'sub', 'gen')
    S('rev_xb', '  Revenue, excluding billable expenses', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}-{V("is_bill")},"")')
    S('rev_xb_g', '    y/y %', 'growth', 'pct', all=growth('rev_xb'))
    S('rev_xb_pub', '  Company-published revenue, excluding billable expenses', 'memo', 'm1', data='rev_xb_pub', flow=True)
    S('rev_xb_chk', '  Check: model vs company-published (should be 0; ±0.15, ±0.6 from Q4 FY25)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("rev_xb_pub")}),IF(ABS({V("rev_xb")}-{V("rev_xb_pub")})<={TL()},0,ROUND({V("rev_xb")}-{V("rev_xb_pub")},1)),"n/p")')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: NET INCOME → ADJUSTED NET INCOME → ADJUSTED DILUTED EPS (company definition)', 'section',
      note='ADJUSTED EPS — net income + pre-tax adjusting items − tax effect at the company\'s assumed rate (40% to Q2 FY2018, 36.5% Q3 FY2018 – FY2018, 26% from FY2019; discrete items specifically) ± discrete tax items; ÷ diluted shares (no two-class adjustment)')
    S('e_ni', 'Net income attributable to common stockholders', 'line_b', 'm1', all=lambda: f'={V("is_nic")}')
    S('e_nci', '  (+) Non-controlling interest (bridge starts from consolidated net income: FY2022)', 'line', 'm1', data='an_nci', flow=True, fc=lambda: '=0')
    S('e_op', '  (+) Operating adjusting items', 'line', 'm1', all=lambda: f'={V("o_items")}')
    S('e_amort', '  (+) Acquisition amortization', 'line', 'm1', all=lambda: f'={V("o_amort")}')
    S('e_nonop', '  (+) Non-operating items (debt costs, gains)', 'line', 'm1', all=lambda: f'={V("d_nonop")}')
    S('e_tax', '  (−) Tax effect of the adjustments', 'line', 'm1', data='an_tax', flow=True, labkey='an_tax_lab',
      fc=lambda: f'=-({V("e_op")}+{V("e_amort")}+{V("e_nonop")})*{PT("pt_adjtax")}',
      note='Historical as published (includes the FY2026 IRS-agreement release, $86m + $20m, per the release footnote). Forecast: items × 26% (company assumed rate).')
    S('e_taxd', '  (±) Discrete tax items (release of tax reserves, R&D credits, deferred-tax remeasurement)', 'line', 'm1', data='an_taxd', flow=True, labkey='an_taxd_lab',
      fc=lambda: '=0')
    S('e_adjni', '  = Adjusted net income (model bridge)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("e_ni")}),{V("e_ni")}+N({V("e_nci")})+N({V("e_op")})+{V("e_amort")}+N({V("e_nonop")})+N({V("e_tax")})+N({V("e_taxd")}),"")')
    S('e_pubni', '  Company-published adjusted net income', 'memo', 'm1', data='adj_ni_pub', flow=True)
    S('e_ni_chk', '  Check: model vs company-published adjusted net income (should be 0; ±0.15, ±0.6 from Q4 FY25)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("e_pubni")}),IF(ABS({V("e_adjni")}-{V("e_pubni")})<={TL()},0,ROUND({V("e_adjni")}-{V("e_pubni")},1)),"n/p")')
    S('e_sh', '  Weighted-average diluted shares (m; company adjusted share count)', 'line', 'm1', data='adj_sh', avg=True, fc=lambda: f'={V("sh_dil")}')
    S('e_eps', 'Adjusted diluted EPS ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted diluted EPS ($)', 'eps_memo', 'ps', data='adj_eps_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0101,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_adjebt', '  Adjusted income before tax (income before tax + pre-tax adjusting items)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}+N({V("e_op")})+{V("e_amort")}+N({V("e_nonop")}),"")')
    S('e_adjtax', '  Adjusted income tax (tax − tax effect − discrete items)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("is_tax")}),{V("is_tax")}-N({V("e_tax")})-N({V("e_taxd")}),"")')
    S('e_rate', '  Adjusted effective tax rate', 'pct', 'pct', all=ratio('e_adjtax', 'e_adjebt'))
    S('e_def', '  Definition / basis (company adjusted EPS definition)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Revenue y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_ns', '  National Security revenue y/y %', 'growth', 'pct', all=growth('ns'))
    S('gm_cc', '  Civil & Commercial revenue y/y %', 'growth', 'pct', all=growth('cc'))
    S('gm_xb', '  Revenue ex-billable expenses y/y %', 'growth', 'pct', all=growth('rev_xb'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating income (GAAP) y/y %', 'growth', 'pct', all=growth('is_oi'))
    S('gm_ni', '  Net income y/y %', 'growth', 'pct', all=growth('is_nic'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin on revenue %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_inc', '  Incremental adjusted EBITDA margin (Δ adjusted EBITDA / Δ revenue)', 'pct', 'pct', all=incr('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_nic', 'is_rev'))
    S('gm_bill', '  Billable expenses % of revenue', 'pct', 'pct', all=ratio('is_bill', 'is_rev'))
    S('gm_ga', '  G&A % of revenue', 'pct', 'pct', all=ratio('is_ga', 'is_rev'))
    blank()
