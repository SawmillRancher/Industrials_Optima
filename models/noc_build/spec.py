"""Row specification of the NOC Model sheet, part 1 (MLM template layout and process):
segment build (Aeronautics / Defense / Mission / Space Systems: sales × segment operating margin, intersegment eliminations) ->
segment operating income (company non-GAAP) -> + FAS/CAS operating adjustment + unallocated corporate expense = operating income ->
M&A lever -> group total & FY26 guidance calibration -> backlog -> legacy segment structures (memo) -> cost drivers -> income
statement -> GAAP-to-adjusted bridges -> growth & margins."""
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
def chk(expr_a, expr_b, tol=0.6, cond=None, dp=1):
    c = cond or f'AND(ISNUMBER({expr_a}),ISNUMBER({expr_b}))'
    return f'=IF({c},IF(ABS({expr_a}-{expr_b})<={tol},0,ROUND({expr_a}-{expr_b},{dp})),"")'

SEG = [('as', 'Aeronautics Systems', 'AS'), ('ds', 'Defense Systems', 'DS'), ('ms', 'Mission Systems', 'MS'), ('ss', 'Space Systems', 'SS')]
SEGK = [s for s, _, _ in SEG]
DESCR = {'as': 'Aeronautics Systems (B-21, F-35 centre fuselage and sustainment, E-2D, Triton / Global Hawk, B-2; strike and surveillance aircraft solutions from 1-Jan-2025)',
         'ds': 'Defense Systems (Sentinel ICBM from the 1-Jan-2024 realignment, tactical weapons and solid rocket motors, armament systems, battle management; training services sold Q2 2025)',
         'ms': 'Mission Systems (airborne and maritime radar, restricted advanced microelectronics, navigation / targeting, C4ISR, marine systems; IT services sold Jan-2021)',
         'ss': 'Space Systems (restricted space, launch and strategic missiles, satellites, Commercial Resupply Services; Sentinel moved to Defense Systems from 1-Jan-2024)'}

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of the 2026 guidance ranges (Q3 2026 release, 20-Oct-2026).'))
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
    # ------------------------------------------------------------------ SEGMENT BUILD
    S('sec_seg', 'SEGMENT P&L — AERONAUTICS · DEFENSE · MISSION · SPACE SYSTEMS (sales × segment operating margin; current four-sector structure)', 'section',
      note=('SEGMENT BUILD — modelling logic (segment sales → segment operating income at the segment margin → less intersegment eliminations = segment operating income '
            '(company non-GAAP) → + FAS/CAS operating adjustment + unallocated corporate expense = GAAP operating income). Basis per column in the definition row below.'))
    blank()
    for s, title, code in SEG:
        S(f'{s}_hdr', DESCR[s], 'block', note=f'{title.upper()} — modelling logic')
        S(f'{s}_s', f'  {title} sales', 'line', 'm', data=f'cur_{s}_s', flow=True,
          qe=lambda s=s: f'={P(s + "_s")}*(1+{V(s + "_g")})', ae=lambda s=s: f'={P(s + "_s")}*(1+{V(s + "_g")})',
          note=('Segment sales incl. intersegment sales (release segment table). Q4/26E: prior-year quarter × (1 + growth). 2027E+: prior year × (1 + scenario lever).') if s == 'as' else None)
        S(f'{s}_g', '    y/y %', 'growth', 'pct', all=growth(f'{s}_s'),
          qe=lambda s=s: f'={V(s + "_g_pre")}+{QEa("cal_g")}', ae=lambda s=s, code=code: '=' + CH(SC[f'{code}_G'][CTX.col.year]),
          note='Q4/26E: growth implied by the segment sales guidance + total-sales calibration Δ (Group block). 2027E–2031E: scenario lever (table →).' if s == 'as' else None)
        S(f'{s}_g_pre', '    Q4/26E growth before sales calibration (implied by the segment sales guidance mid-point: (guided FY − 9M actual) ÷ Q4 2025 − 1)', 'driver', 'pct',
          qe=lambda s=s: f'=IFERROR(({PT("pt_g_" + s + "_s")}-{ACT(s + "_s")})/{P(s + "_s")}-1,0)',
          note=('Segment end-points first (Q3 2026 release segment guidance, mid-points of the ranges in words), then one total-level Δ to the consolidated sales guidance (CW precedent: segment ranges do not sum to the total). '
                'The plain 9M y/y rate would overstate Aeronautics (Q4 2025 was +25% q/q).') if s == 'as' else None)
        S(f'{s}_mix', '    % of gross segment sales', 'pct', 'pct', all=ratio(f'{s}_s', 'g_gross'))
        S(f'{s}_oi', f'  {title} operating income', 'line', 'm', data=f'cur_{s}_oi', flow=True,
          qe=lambda s=s: f'={V(s + "_s")}*{V(s + "_m")}', ae=lambda s=s: f'={V(s + "_s")}*{V(s + "_m")}',
          note='Segment operating income as reported (includes CAS pension cost; excludes FAS service cost and unallocated corporate items). Forecast = sales × margin.' if s == 'as' else None)
        S(f'{s}_m', '    Operating margin rate %', 'pct', 'pct', all=ratio(f'{s}_oi', f'{s}_s'),
          qe=lambda s=s: f'={V(s + "_m_pre")}+{QEa("cal_m")}', ae=lambda s=s, code=code: '=' + CH(SC[f'{code}_M'][CTX.col.year]),
          note='Q4/26E: margin implied by the segment guidance + segment-OI calibration Δ (Group block). 2027E+: scenario lever.' if s == 'as' else None)
        S(f'{s}_m_pre', '    Q4/26E margin before calibration (implied by the segment margin guidance: (guided FY margin × guided FY sales − 9M actual OI) ÷ Q4 sales)', 'driver', 'pct',
          qe=lambda s=s: f'=IFERROR(({PT("pt_g_" + s + "_m")}*{PT("pt_g_" + s + "_s")}-{ACT(s + "_oi")})/{V(s + "_s")},0)',
          note='Segment margin end-points first, then one total-level Δ to the segment-operating-income guidance. (The prior-year-quarter-plus-drift method is distorted by the Q1 2025 B-21 loss provision.)' if s == 'as' else None)
        S(f'{s}_inc', '    Incremental margin (Δ operating income / Δ sales)', 'pct', 'pct', all=incr(f'{s}_oi', f'{s}_s'))
        S(f'{s}_orig_s', f'  Memo: {title} sales as originally reported (periods later recast for realignments)', 'memo', 'm', data=f'orig_{s}_s', flow=True)
        S(f'{s}_orig_oi', f'  Memo: {title} operating income as originally reported', 'memo', 'm', data=f'orig_{s}_oi', flow=True)
        S(f'{s}_10k_s', f'  Memo: {title} sales on the latest structure (10-K segment note; annual only)', 'memo', 'm', data=f'c10k_{s}_s', flow=True,
          note='FY2022 on the 1-Jan-2024 structure (FY2024 10-K) and FY2023 on the 1-Jan-2025 structure (FY2025 10-K): later recasts than the one the quarters of those years carry.' if s == 'as' else None)
        blank()
    S('el_hdr', 'Intersegment eliminations', 'block', note='ELIMINATIONS — intersegment sales and the profit on them')
    S('el_s', '  Intersegment sales eliminated (negative)', 'line', 'm', data='cur_elim_s', flow=True,
      qe=lambda: f'=-{V("g_gross")}*{V("el_p")}', ae=lambda: f'=-{V("g_gross")}*{V("el_p")}',
      note='Forecast = − eliminations % × gross segment sales. 2026 guidance ~($2.7bn) (Q3 2026 release).')
    S('el_p', '  Eliminations % of gross segment sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("el_s")}),IFERROR(-{V("el_s")}/{V("g_gross")},""),"")',
      qe=lambda: f'={PT("pt_elim_p")}', ae=lambda: '=' + CH(SC['ELIM_P'][CTX.col.year]),
      note='9M 2026 6.0%; 2025 5.2%; 2024 (recast) 4.4%. Q4/26E point estimate; 2027E+ scenario lever (higher intersegment content as Sentinel / B-21 subcontracting grows).')
    S('el_oi', '  Intersegment operating income eliminated (negative)', 'line', 'm', data='cur_elim_oi', flow=True,
      qe=lambda: f'={V("el_s")}*{V("el_m")}', ae=lambda: f'={V("el_s")}*{V("el_m")}', note='Forecast = eliminated sales × eliminations margin rate.')
    S('el_m', '  Eliminations margin rate %', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("el_oi")}),IFERROR({V("el_oi")}/{V("el_s")},""),"")',
      qe=lambda: f'={PT("pt_elim_m")}', ae=lambda: f'={PT("pt_elim_m")}', note='2026 guidance "mid 13%" (Q3 2026 release); 9M 2026 13.5%; 2025 13.7%.')
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — bolt-ons, unallocated; deals closed from 2027E)', 'block', note='M&A LEVER — acquired sales = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=2.0, e26_in=0.0,
      note='Orbital ATK (Jun-2018): $7.7bn net of cash + $1.4bn debt assumed on ~$5.0bn of sales (~1.8x). 2.0x input (assumption).')
    S('m_acq_sales', '  Annualised sales acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.05)
    S('m_run', '  Run-rate sales of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Sales from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}', note='Mid-year convention.')
    S('m_m', '  Operating margin of acquired businesses (before purchase-accounting amortization) %', 'driver', 'pct', e26_in=0.0, ae_in=0.11)
    S('m_oi', '  Operating income from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.10)
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.30, note='Orbital ATK PPA (FY2018 10-K Note 3): ~$2.7bn of intangibles on $9.2bn of consideration incl. debt (~30%).')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=12)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (in unallocated corporate expense)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)',
      note='Northrop Grumman reports purchased-intangible amortization in unallocated corporate expense, outside segment operating income.')
    blank()

    # ------------------------------------------------------------------ group total & calibration
    S('g_hdr', 'Group Total — sales & segment operating income (segment build) → 2026 guidance calibration', 'block', note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_gross', '  Gross segment sales (Σ segments, incl. intersegment)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("as_s")}),{"+".join(V(s + "_s") for s in SEGK)}+N({V("m_rev")}),"")')
    S('g_rev', 'Total sales (segment build)', 'total', 'm', hist=lambda: f'=IF(ISNUMBER({V("as_s")}),{V("g_gross")}+{V("el_s")},{V("is_rev")})',
      fc=lambda: f'={V("g_gross")}+{V("el_s")}', note='Σ segment sales + intersegment eliminations (+ future acquisitions from 2027E). History before 2019 falls back to reported sales.')
    S('g_rev_g', '  Total sales y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs consolidated sales (should be 0; ±0.5 rounding)', 'check', 'm', all=lambda: chk(V('g_rev'), V('is_rev')))
    S('g_soi', 'Segment operating income (segment build; company non-GAAP)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("as_oi")}),{"+".join(V(s + "_oi") for s in SEGK)}+N({V("el_oi")})+N({V("m_oi")}),"")',
      note='Σ segment operating income + intersegment eliminations (+ future acquisitions). Company non-GAAP measure; reconciled to GAAP operating income below.')
    S('g_som', '  Segment operating margin rate %', 'pct', 'pct', all=ratio('g_soi', 'g_rev'))
    S('g_soi_g', '  Segment operating income y/y %', 'growth', 'pct', all=growth('g_soi'))
    S('g_soi_pub', '  Company-published segment operating income', 'memo', 'm', data='seg_oi_pub', flow=True)
    S('g_chk_soi', '  Check: segment build vs company-published segment operating income (should be 0; ±0.5 rounding)', 'check', 'm', hist=lambda: chk(V('g_soi'), V('g_soi_pub')))
    S('cal_guid', '  Memo: 2026 sales guidance (scenario end-point)', 'memo', 'm', e26=lambda: '=' + CH(SC['out_sales']), note=V0['rev_guid_note'])
    S('cal_pre', '  Sales before calibration (Q4/26E helper)', 'line', 'm',
      qe=lambda: f'=(1-{V("el_p")})*(' + '+'.join(f'{P(s + "_s")}*(1+{V(s + "_g_pre")})' for s in SEGK) + ')')
    S('cal_sens', '  Sales sensitivity to +1.00 of growth (Q4/26E helper)', 'line', 'm', qe=lambda: f'=(1-{V("el_p")})*(' + '+'.join(P(s + '_s') for s in SEGK) + ')')
    S('cal_g', '  Guidance calibration: Δ y/y growth applied to all segments (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_guid", E26)}-{ACT("g_rev")}-{V("cal_pre")})/{V("cal_sens")}',
      note='Solves the uniform growth shift (vs the segment-guidance-implied Q4 rates) so that 2026 sales = the consolidated guidance end-point for the active scenario. Closed form, no circularity.')
    S('cal_rev_chk', '  Check: 2026 sales vs guidance end-point (should be 0; ±0.5 rounding)', 'check', 'm', e26=lambda: f'=ROUND({V("g_rev")}-{V("cal_guid")},1)')
    S('cal_soi', '  Memo: 2026 segment operating income guidance (scenario end-point)', 'memo', 'm', e26=lambda: '=' + CH(SC['out_soi']), note=V0['soi_guid_note'])
    S('cal_soi_pre', '  Segment operating income before margin calibration (Q4/26E helper)', 'line', 'm',
      qe=lambda: '=' + '+'.join(f'{V(s + "_s")}*{V(s + "_m_pre")}' for s in SEGK) + f'+{V("el_oi")}')
    S('cal_segs', '  Segment sales (Q4/26E helper)', 'line', 'm', qe=lambda: '=' + '+'.join(V(s + '_s') for s in SEGK))
    S('cal_m', '  Guidance calibration: Δ segment margin (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_soi", E26)}-{ACT("g_soi")}-{V("cal_soi_pre")})/{V("cal_segs")}',
      note='Solves the uniform segment-margin shift so that 2026 segment operating income = the guidance end-point for the active scenario (the KPI the company guides).')
    S('cal_soi_chk', '  Check: 2026 segment operating income vs guidance end-point (should be 0; ±0.5 rounding)', 'check', 'm', e26=lambda: f'=ROUND({V("g_soi")}-{V("cal_soi")},1)')
    S('cal_eps', '  Memo: 2026 MTM-adjusted EPS guidance (scenario end-point, $) — information, not forced', 'eps_memo', 'ps', e26=lambda: '=' + CH(SC['out_eps']), note=V0['eps_guid_note'])
    S('cal_eps_d', '    Model 2026E MTM-adjusted EPS − guidance ($)', 'memo_calc', 'ps', e26=lambda: f'={V("e_eps")}-{V("cal_eps")}')
    S('cal_fcf', '  Memo: 2026 adjusted free cash flow guidance (scenario end-point) — drives the year-end unbilled-receivables calibration', 'memo', 'm', e26=lambda: '=' + CH(SC['out_fcf']),
      note='Guided $3,100–3,500m. The 2026E unbilled receivables balance (the dominant working-capital swing item) is solved so that adjusted FCF = this end-point (closed form; working-capital calibration as in the HII / WCN builds).')
    S('cal_fcf_pre', '  2026E free cash flow before the unbilled calibration (unbilled held at 30-Sep-2026; helper)', 'line', 'm',
      e26=lambda: (f'={ACT("cf_cfo")}+{QEc("is_ni")}+{QEc("is_dda")}+{QEc("is_sbc")}+{PT("pt_def")}+{QEc("cf_pens_q")}'
                   f'-({V("bs_ar")}-{B1("bs_ar")})-({V("bs_inv")}-{B1("bs_inv")})-({V("bs_oca")}-{B1("bs_oca")})'
                   f'+({V("bs_ap")}-{B1("bs_ap")})+({V("bs_accr")}-{B1("bs_accr")})+({V("bs_adv")}-{B1("bs_adv")})+({V("bs_ocl")}-{B1("bs_ocl")})+{V("cf_capex")}'))
    S('cal_unb', '  2026E unbilled receivables solved to the FCF guidance (= 30-Sep balance + FCF before calibration − guidance)', 'line', 'm',
      e26=lambda: f'={B1("bs_unb")}+{V("cal_fcf_pre")}-{V("cal_fcf")}')
    S('cal_fcf_chk', '  Check: 2026E adjusted free cash flow vs guidance end-point (should be 0; ±0.5 rounding)', 'check', 'm', e26=lambda: f'=ROUND({V("afcf")}-{V("cal_fcf")},1)')
    S('cal_seg_h', '  Memo: 2026 segment guidance (Q3 2026 release; mid-points of the ranges in words) — information rows', 'sub', 'gen')
    for s, title, code in SEG:
        S(f'cal_{s}_s', f'    {title}: model 2026E sales − guided sales (~mid-point)', 'memo_calc', 'm', e26=lambda s=s: f'={V(s + "_s")}-{PT("pt_g_" + s + "_s")}')
        S(f'cal_{s}_m', f'    {title}: model 2026E margin − guided margin (pp)', 'memo_calc', 'pct', e26=lambda s=s: f'={V(s + "_m")}-{PT("pt_g_" + s + "_m")}')
    blank()

    # ------------------------------------------------------------------ backlog
    S('bl_hdr', 'Backlog & awards (total backlog excludes unexercised options and IDIQ; funded = appropriated)', 'block',
      note='BACKLOG — net awards = Δ backlog + sales (implied where awards are not quoted); forecast awards = sales × book-to-bill lever')
    S('bl_tot', '  Total backlog (period end)', 'line', 'm', data='backlog', bs=True,
      qe=lambda: f'={PQ("bl_tot")}+{V("bl_awd")}-{V("is_rev")}', ae=lambda: f'={P("bl_tot")}+{V("bl_awd")}-{V("is_rev")}',
      note='Release backlog schedule ($m; FY2010–2015 and some 2016–18 quarters from the release / 10-Q narrative in $bn). Forecast roll-forward: opening + net awards − sales.')
    S('bl_fund', '  of which funded', 'memo', 'm', data='backlog_funded', bs=True)
    S('bl_awd', '  Net awards (quoted in the release where available; else implied = Δ backlog + sales)', 'line', 'm', data='awards', flow=True,
      hist=lambda: (f'=IF(AND(ISNUMBER({V("bl_tot")}),ISNUMBER({(PQ("bl_tot") if CTX.col.q else P("bl_tot"))}),ISNUMBER({V("is_rev")})),{V("bl_tot")}-{(PQ("bl_tot") if CTX.col.q else P("bl_tot"))}+{V("is_rev")},"")'
                    if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None),
      qe=lambda: f'={V("is_rev")}*{V("bl_b2b")}', ae=lambda: f'={V("is_rev")}*{V("bl_b2b")}',
      note='Quoted net awards ($bn, rounded in the release text) where given; otherwise implied from the backlog roll-forward (includes adjustments / de-bookings). Forecast = sales × book-to-bill.')
    S('bl_b2b', '  Book-to-bill (net awards ÷ sales, x)', 'pct', 'x2', all=lambda: f'=IF(AND(ISNUMBER({V("bl_awd")}),ISNUMBER({V("is_rev")})),IFERROR({V("bl_awd")}/{V("is_rev")},""),"")',
      qe=lambda: f'={PT("pt_b2b")}', ae=lambda: '=' + CH(SC['B2B'][CTX.col.year]),
      note='Q3 2026 1.5x; 9M 2026 ~1.4x; 2025 1.1x; 2024 1.1x. Q4/26E point estimate; 2027E+ scenario lever (government awards are lumpy; Base 1.05x = backlog growing slightly faster than sales).')
    S('bl_cov', '  Backlog / sales (years of sales)', 'pct', 'x2', all=lambda: f'=IF(ISNUMBER({V("bl_tot")}),IFERROR({V("bl_tot")}/({V("is_rev")}*{4 if CTX.col.q else 1}),""),"")')
    S('bl_rpo', '  Memo: remaining performance obligations (10-Q / 10-K, XBRL; from 2018)', 'memo', 'm', data='rpo', bs=True)
    blank()

    # ------------------------------------------------------------------ legacy structures (memo)
    S('lg_hdr', 'Legacy segment structures — as originally reported (memo; sales incl. intersegment; eliminations shown)', 'block',
      note='LEGACY SEGMENTS — 2016–19 (Aerospace / Innovation / Mission / Technology Services), 2009–15 (Aerospace / Electronic / Information / Shipbuilding / Technical Services), 2006–08 (four businesses). Σ checks vs reported sales and segment operating income.')
    L16 = [('aer', 'Aerospace Systems'), ('inn', 'Innovation Systems (Orbital ATK, from 6-Jun-2018)'), ('mis', 'Mission Systems (legacy, 2016–19)'), ('tsv', 'Technology Services')]
    L09 = [('aer', 'Aerospace Systems'), ('ele', 'Electronic Systems'), ('inf', 'Information Systems'), ('shp', 'Shipbuilding (spun off as HII 31-Mar-2011)'), ('tec', 'Technical Services')]
    L06 = [('ins', 'Information & Services (Mission Systems, Information Technology, Technical Services)'), ('aer', 'Aerospace (Integrated Systems, Space Technology)'), ('ele', 'Electronics'), ('shp', 'Ships / Shipbuilding'), ('oth', 'Other (derived residual; row prints blank cells)')]
    for blk, items, lab in (('l16', L16, '2016–2019 structure'), ('l09', L09, '2009–2015 structure'), ('l06', L06, '2006–2008 structure')):
        S(f'{blk}_sh', f'  {lab}: sales', 'sub', 'gen')
        for k, t in items: S(f'{blk}_{k}_s', f'    {t}', 'memo', 'm', data=f'{blk}_{k}_s', flow=True)
        S(f'{blk}_el_s', '    Intersegment eliminations', 'memo', 'm', data=f'{blk}_elim_s', flow=True)
        S(f'{blk}_chk_s', '    Check: Σ segments + eliminations vs consolidated sales (should be 0; ±0.5 rounding)', 'check', 'm',
          hist=lambda blk=blk, items=items: chk('+'.join(f'N({V(blk + "_" + k + "_s")})' for k, _ in items) + f'+N({V(blk + "_el_s")})', V('is_rev'), cond=f'ISNUMBER({V(blk + "_" + items[0][0] + "_s")})'))
        S(f'{blk}_oh', f'  {lab}: segment operating income', 'sub', 'gen')
        for k, t in items: S(f'{blk}_{k}_oi', f'    {t}', 'memo', 'm', data=f'{blk}_{k}_oi', flow=True)
        S(f'{blk}_el_oi', '    Intersegment eliminations', 'memo', 'm', data=f'{blk}_elim_oi', flow=True)
        S(f'{blk}_soi', '    Segment operating income as published', 'memo', 'm', data=f'{blk}_seg_oi', flow=True)
        S(f'{blk}_chk_oi', '    Check: Σ segments + eliminations vs published segment operating income (should be 0; ±0.5 rounding)', 'check', 'm',
          hist=lambda blk=blk, items=items: chk('+'.join(f'N({V(blk + "_" + k + "_oi")})' for k, _ in items) + f'+N({V(blk + "_el_oi")})', V(blk + '_soi'), cond=f'ISNUMBER({V(blk + "_" + items[0][0] + "_oi")})'))
    blank()

    # ------------------------------------------------------------------ reconciliation to operating income (pension block)
    S('sec_rc', 'RECONCILIATION: SEGMENT OPERATING INCOME (NON-GAAP) → GAAP OPERATING INCOME (FAS/CAS pension adjustment, unallocated corporate expense)', 'section',
      note=('PENSION / CORPORATE BLOCK — segment operating income carries CAS pension cost; the FAS/CAS operating adjustment converts to FAS service cost (service-cost-only from 2018 under ASU 2017-07; '
            'net total FAS/CAS through 2017, incl. the non-service components). Unallocated corporate expense = unallowable costs, purchased-intangible amortization and PP&E step-up depreciation, deferred state taxes.'))
    S('rc_soi', 'Segment operating income (build; company non-GAAP)', 'line_b', 'm', all=lambda: f'={V("g_soi")}')
    S('rc_cas', '  Memo: CAS pension cost allocated to the segments (10-K; annual)', 'memo', 'm', data='cas_cost', flow=True,
      ae=lambda: f'={V("rc_cas_in")}', e26=lambda: f'={V("rc_cas_in")}', note='CAS pension expense recovered through contracts (FY2025 10-K MD&A table: $475m 2025, $279m 2024, $154m 2023). Forecast input.')
    S('rc_cas_in', '  CAS pension cost — forecast input (USDm, assumption)', 'driver', 'm', e26_in=V0['cas_26'], ae_in=V0['cas_ae'],
      note=('Assumption: CAS cost driven by prior plan-asset returns and CAS actuarial assumptions; 2026E implied by the 9M FAS/CAS operating adjustment of $29m (vs $193m in 9M 2025) '
            'and a FAS service cost of ~$200m. Held at the 2026E level (no guidance on EDGAR).'))
    S('rc_svc', '  Memo: FAS pension service cost (10-K; annual)', 'memo', 'm', data='fas_svc', flow=True, ae=lambda: f'={V("rc_svc_in")}', e26=lambda: f'={V("rc_svc_in")}',
      note='FAS pension service cost (FY2025 10-K: $217m 2025, $239m 2024, $236m 2023; included in operating costs). Forecast input.')
    S('rc_svc_in', '  FAS pension service cost — forecast input (USDm, assumption)', 'driver', 'm', e26_in=V0['svc_26'], ae_in=V0['svc_ae'],
      note='Assumption: ~$200m p.a. (2025 $217m, declining with the higher discount rate at 31-Dec-2025, 5.58%).')
    S('rc_fascas', '  (+) FAS/CAS operating adjustment (CAS pension cost − FAS service cost; net total FAS/CAS pension adjustment through 2017)', 'line', 'm', data='rc_fascas', flow=True,
      qe=lambda: f'={PT("pt_fascas")}', ae=lambda: f'={V("rc_cas")}-{V("rc_svc")}',
      note=('As published in the release reconciliation ("Net pension adjustment" 2006–11; "Net FAS/CAS pension adjustment" 2012–17; "Net FAS (service)/CAS pension adjustment" 2018–20; '
            '"FAS/CAS operating adjustment" 2021+). Q4/26E: point estimate (9M 2026 $29m). 2027E+ = CAS cost − FAS service cost inputs.'))
    S('rc_unalloc', '  (+) Unallocated corporate expense (total; negative = expense)', 'line', 'm', data='rc_unalloc', flow=True,
      qe=lambda: f'={PT("pt_unalloc")}', ae=lambda: f'=-{V("is_rev")}*{V("rc_unalloc_p")}-N({V("m_amort")})',
      note=('Unallowable corporate costs, intangible amortization & PP&E step-up depreciation, deferred state taxes (incl. the deferred state tax effect of MTM and the B-21 provisions), '
            'divestiture gains / costs from 2021. Q4/26E point estimate; 2027E+ = % of sales input + future-acquisition amortization.'))
    S('rc_unalloc_p', '  Unallocated corporate expense % of sales (excl. gains / divestiture items)', 'pct', 'pct',
      all=lambda: f'=IF(ISNUMBER({V("rc_unalloc")}),IFERROR(-({V("rc_unalloc")}-N({V("rc_gain")})-N({V("rc_divest")}))/{V("is_rev")},""),"")', ae_in=V0['unalloc_pct'],
      note='2025 0.3% (−$124m incl. the $231m gain), 9M 2026 0.8% (−$250m; intangible amortization & step-up depreciation −$51m), 2024 0.5%. Input (assumption).')
    S('rc_intang', '    of which: intangible asset amortization & PP&E step-up depreciation (2018+)', 'memo', 'm', data='rc_intang', flow=True,
      note='Component of unallocated corporate expense (released separately from 2018; $84m 2025). Purchased-intangible amortization schedule (FY2025 10-K): $42m 2026, $31m p.a. 2027–30.')
    S('rc_mtm_state', '    of which: MTM-related / B-21 deferred state tax (benefit) expense (Q4)', 'memo', 'm', data='rc_mtm_state', flow=True)
    S('rc_oth_un', '    of which: other unallocated corporate expense', 'memo', 'm', data='rc_other_unalloc', flow=True)
    S('rc_gain', '  (+) Gain on sale of business (IT services Jan-2021 $1,980m; training services Q2 2025 $231m)', 'line', 'm', data='rc_gain', flow=True, fc=lambda: '=0',
      note='Shown inside unallocated corporate (expense) income by the company from 2021; the total row above includes it in those periods (the Σ check reconciles only the items that are not already in the total).')
    S('rc_divest', '  (+) Divestiture-related unallowable state taxes and transaction costs', 'line', 'm', data='rc_divest', flow=True, fc=lambda: '=0')
    S('rc_royalty', '  (+) Reversal of royalty income included in segment operating income (2006–2013)', 'line', 'm', data='rc_royalty', flow=True, fc=lambda: '=0')
    S('rc_other', '  (+) Other reconciling items (derived residual; labelled items in cell comments)', 'line', 'm', data='rc_other', flow=True, fc=lambda: '=0', labkey='rc_other_lab')
    S('rc_oi', '  = Operating income (model)', 'total', 'm',
      all=lambda: (f'=IF(ISNUMBER({V("rc_soi")}),{V("rc_soi")}+N({V("rc_fascas")})+N({V("rc_unalloc")})+IF(ISNUMBER({V("rc_intang")}),0,N({V("rc_gain")})+N({V("rc_divest")}))'
                   f'+N({V("rc_royalty")})+N({V("rc_other")}),"")'),
      note='Segment operating income + FAS/CAS + unallocated (+ gains / divestiture items where not already inside the published unallocated total) + royalty reversal + other.')
    S('rc_chk', '  Check: model vs reported operating income (should be 0; ±0.5 rounding)', 'check', 'm', hist=lambda: chk(V('rc_oi'), V('is_oi')))
    S('rc_def', '  Definition / basis (segment structure and pension presentation in force)', 'text', 'gen',
      note='Basis flags per column: segment structure of each period and the FAS/CAS presentation (cell comments give the detail and the recast sources).')
    S('rc_nonop', '  Memo: non-operating FAS pension benefit (below operating income, 2018+; incl. in the net FAS/CAS adjustment through 2017)', 'memo_calc', 'm', all=lambda: f'={V("is_nonop")}')
    S('rc_tot', '  Memo: total net FAS/CAS pension adjustment (operating + non-operating; company supplemental per-share schedule)', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("rc_fascas")}),{V("rc_fascas")}+N({V("is_nonop")}),"")')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A & other items', 'block', note='COST DRIVERS — inputs that drive forecast cost lines (Q4/26E: point estimates; 2027E+: % of sales or schedules)')
    S('d_svc_p', '  Service sales % of total sales', 'pct', 'pct', all=ratio('is_svc', 'is_rev'), qe=lambda: f'=IFERROR({ACT("is_svc")}/{ACT("is_rev")},"")', ae=lambda: f'={P("d_svc_p")}',
      note='Mix memo (product vs service sales); forecast holds the 9M 2026 share.')
    S('d_ga', '  General & administrative expenses % of sales', 'pct', 'pct', all=ratio('is_ga', 'is_rev'),
      qe=lambda: f'={P("d_ga")}+IFERROR({ACT("is_ga")}/{ACT("is_rev")}-{ACT0("is_ga")}/{ACT0("is_rev")},0)', ae_in=V0['ga_pct'],
      note='Q4/26E: prior-year quarter ratio + 9M 2026 y/y drift; 2027E+ input (2025 9.6%, 9M 2026 9.7%). Cost of sales is the implied balancing line to the operating-income build.')
    S('d_dda', '  Depreciation & amortization (cash-flow statement)', 'line', 'm', data='cf_dda', flow=True, qe=lambda: f'={PT("pt_dda")}', ae=lambda: f'={V("is_rev")}*{V("d_dda_p")}',
      note='Cash-flow statement D&A (2009–15 from XBRL; incl. purchased-intangible amortization). Q4/26E point estimate; 2027E+ % of sales.')
    S('d_dda_p', '  D&A % of sales', 'pct', 'pct', all=ratio('d_dda', 'is_rev'), ae_in=V0['dda_pct'], note='2025 3.5%, 9M 2026 3.5% (capacity investments in solid rocket motors, microelectronics, Sentinel / B-21).')
    S('d_amort', '  of which: purchased-intangible amortization (10-K schedule, input; in unallocated corporate expense)', 'driver', 'm', e26_in=V0['amort'][2026], ae_in={y: V0['amort'][y] for y in range(2027, 2032)},
      note=MAN['amort_sched']['src'] + '. 2031E: $31m assumed (schedule ends 2030).')
    S('d_dep', '  Depreciation (D&A − intangible amortization − future-acquisition amortization)', 'line', 'm', fc=lambda: f'={V("d_dda")}-{V("d_amort")}-N({V("m_amort")})')
    S('d_sbc', '  Stock-based compensation (cash-flow statement)', 'line', 'm', data='cf_sbc', flow=True, qe=lambda: f'={PT("pt_sbc")}', ae=lambda: f'={V("is_rev")}*{V("d_sbc_p")}')
    S('d_sbc_p', '  Stock-based compensation % of sales', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_nonop', '  Non-operating FAS pension benefit — forecast input (USDm, assumption)', 'driver', 'm', qe=lambda: f'={PT("pt_nonop")}', ae_in=V0['nonop_ae'],
      note='Non-cash (interest cost − expected return on assets, incl. OPB). 2025 $541m; 9M 2026 $499m (~$665m annualised). Held near the 2026E run-rate (assumption; EROA 7.5%, discount rate 5.58% at 31-Dec-2025).')
    S('d_oth', '  Other, net excl. interest income — forecast input (USDm, assumption)', 'driver', 'm', qe=lambda: f'={PT("pt_oth")}', ae_in=V0['oth_ae'],
      note='Marketable-securities returns on non-qualified plan assets, equity-method results and other. Interest income on cash is modelled separately below.')
    S('d_mtm', '  Mark-to-market pension & OPB (benefit) expense — forecast (nil: actuarial gains / losses are not forecast)', 'driver', 'm', fc=lambda: '=0',
      note='Fourth-quarter remeasurement (2025 +$527m benefit; 2024 +$443m; 2023 −$422m). Not forecast; the FY2025 10-K sensitivity is ±$314m per 100bp of actual vs expected return.')
    S('d_b21', '  Memo: B-21 loss provisions (company-quantified; Q4 2023 $1,560m, Q1 2025 $477m — model adjusting item in the EBITDA bridge)', 'driver', 'm', data='b21', flow=True, fc=lambda: '=0')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF EARNINGS (US GAAP)', 'section', note='CONSOLIDATED IS — forecast logic (operating income from the segment build + pension / corporate block; cost of sales implied)')
    S('is_prod', 'Product sales', 'line', 'm', data='prod_sales', flow=True, fc=lambda: f'={V("is_rev")}-{V("is_svc")}')
    S('is_svc', 'Service sales', 'line', 'm', data='svc_sales', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_svc_p")}')
    S('is_rev', 'Total sales', 'total', 'm', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the segment build.')
    S('is_cos', 'Cost of sales (product and service operating costs; incl. CAS pension cost and FAS service cost)', 'line', 'm', data='cos', flow=True,
      fc=lambda: f'={V("is_rev")}-{V("is_ga")}-{V("is_othop")}-{V("is_oi")}', note='Forecast = sales − G&A − other operating items − operating income (implied by the build).')
    S('is_gp', 'Gross profit (sales − cost of sales)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_cos")}),{V("is_rev")}-{V("is_cos")},"")')
    S('is_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('is_ga', 'General and administrative expenses', 'line', 'm', data='ga', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_ga")}')
    S('is_othop', 'Other operating items (goodwill impairment 2008 +$3,060m; gains on sale of business 2021 / 2025 shown negative; expense = +)', 'line', 'm', data='oth_op', flow=True, fc=lambda: '=0', labkey='oth_op_lab')
    S('is_oi', 'Operating income', 'total', 'm', data='oi', flow=True, fc=lambda: f'={V("rc_oi")}', note='Forecast = segment operating income + FAS/CAS operating adjustment + unallocated corporate expense (reconciliation block).')
    S('is_oim', '  Operating margin rate %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('is_int', 'Interest expense', 'line', 'm', data='int_exp', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_rev")}*{V("ds_r_rev")}+{V("ds_fees")}',
      note='Q4/26E point estimate (Q3 $158m). 2027E+ = rate × opening notes + rate × opening commercial paper / revolver + fees and amortization (no circularity).')
    S('is_intinc', 'Interest income (within "Other, net"; 2006–08 separate line)', 'line', 'm', data='int_inc', flow=True, qe=lambda: '=0', ae=lambda: f'={P("cf_end")}*{V("ds_r_cash")}',
      note='Separate line only in 2006–08; inside Other, net otherwise (Q4/26E: inside the Other, net point estimate). 2027E+ = yield × opening cash.')
    S('is_nonop', 'Non-operating FAS pension benefit (2018+; in operating income through 2017)', 'line', 'm', data='nonop_fas', flow=True, fc=lambda: f'={V("d_nonop")}')
    S('is_mtm', 'Mark-to-market pension and OPB benefit (expense) (Q4, 2018+)', 'line', 'm', data='mtm', flow=True, fc=lambda: f'={V("d_mtm")}')
    S('is_oth', 'Other, net (incl. interest income from 2009; 2010–11 debt-redemption charges) (income +)', 'line', 'm', data='oth_nonop', flow=True, fc=lambda: f'={V("d_oth")}')
    S('is_ebt', 'Earnings before income taxes', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_oi")}),{V("is_oi")}-{V("is_int")}+N({V("is_intinc")})+N({V("is_nonop")})+N({V("is_mtm")})+N({V("is_oth")}),"")')
    S('is_tax', 'Federal and foreign income tax expense', 'line', 'm', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='9M 2026 11.5% (higher research credits); 2025 17.5%; 2024 16.8%. Q4/26E point estimate; 2027E+ input (assumption).')
    S('is_cont', 'Earnings from continuing operations', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_disc', 'Earnings from discontinued operations, net of tax (Shipbuilding to 2011; TASC 2009)', 'line', 'm', data='disc_ops', flow=True, fc=lambda: '=0')
    S('is_ni', 'Net earnings', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_cont")}),{V("is_cont")}+N({V("is_disc")}),"")')
    S('is_ni_chk', '  Check: net earnings vs reported (should be 0; ±0.5 rounding)', 'check', 'm', hist=lambda: chk(V('is_ni'), V('is_ni_pub')))
    S('is_ni_pub', '  Memo: net earnings as reported', 'memo', 'm', data='ni', flow=True)
    S('is_ni_py', '  Memo: net earnings as restated in the following year\'s release / 10-K (where different)', 'memo', 'm', data='ni_py', flow=True)
    S('is_rev_py', '  Memo: sales as restated in the following year\'s release / 10-K (where different: TASC 2008, Shipbuilding 2010, ASC 606 2017)', 'memo', 'm', data='rev_py', flow=True)
    S('is_dda', '  Memo: depreciation & amortization', 'memo_calc', 'm', all=lambda: f'={V("d_dda")}')
    S('is_sbc', '  Memo: stock-based compensation', 'memo_calc', 'm', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={B1("bs_shares")}-${E26}${R["bb_sh"]}*0.5+${E26}${R["bb_iss"]}*0.5', ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q4/26E: shares outstanding at 30-Sep-2026 − Q4 buybacks (mid-quarter) + equity-plan issuance. 2027E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR(({V("is_ni")}+N({V("eps_adj")}))/{V("sh_dil")},""),"")',
      note='Net earnings ÷ weighted diluted shares (2006–07: + dividends on the convertible preferred added back under the if-converted method, derived).')
    S('eps_adj', '  Memo: diluted EPS numerator adjustment (convertible preferred dividends, 2006–07; derived from published EPS)', 'memo', 'm', data='eps_num_adj')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_cont', '  Memo: EPS – diluted, continuing operations as reported ($) (2006–2013)', 'eps_memo', 'ps', data='eps_d_cont')
    S('eps_pub', '  Memo: EPS – diluted as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0101,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('dps', '  Dividends declared per share ($)', 'line', 'ps', data='dps', flow=True, qe_in=V0['dps_q'], ae=lambda: f'={P("dps")}*(1+{V("dps_g")})',
      note='XBRL CommonStockDividendsPerShareDeclared. Quarterly $2.47 from Q2 2026 (raised from $2.31). 2027E+: prior year × (1 + growth).')
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'])
    blank()

    # ------------------------------------------------------------------ RECON 2: NI -> EBITDA -> adjusted EBITDA (model)
    S('sec_r2', 'RECONCILIATION: NET EARNINGS → EBITDA → ADJUSTED EBITDA (model definitions — Northrop Grumman publishes no EBITDA)', 'section',
      note=('EBITDA (model) = operating income + D&A. Adjusted EBITDA (model) adds back only items the company itself quantified: gains on sales of businesses, divestiture costs, '
            'the 2008 goodwill impairment and the B-21 loss provisions (Q4 2023, Q1 2025). MTM sits below operating income from 2018.'))
    S('r_ni', 'Net earnings (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('r_disc', '  (−) Discontinued operations', 'line', 'm', all=lambda: f'=-N({V("is_disc")})')
    S('r_tax', '  (+) Income taxes', 'line', 'm', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest expense', 'line', 'm', all=lambda: f'={V("is_int")}')
    S('r_nonop', '  (−) Non-operating FAS pension benefit, MTM, other net and interest income', 'line', 'm', all=lambda: f'=-(N({V("is_intinc")})+N({V("is_nonop")})+N({V("is_mtm")})+N({V("is_oth")}))')
    S('r_ebit', '  = Operating income (EBIT)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_disc")}+{V("r_tax")}+{V("r_int")}+{V("r_nonop")},"")')
    S('r_ebit_chk', '  Check: EBIT vs operating income (should be 0; ±0.5 rounding)', 'check', 'm', all=lambda: chk(V('r_ebit'), V('is_oi')))
    S('r_dda', '  (+) Depreciation & amortization', 'line', 'm', all=lambda: f'={V("d_dda")}')
    S('r_ebitda', '  = EBITDA (model)', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_ebit")}),ISNUMBER({V("r_dda")})),{V("r_ebit")}+{V("r_dda")},"")')
    S('r_gain', '  (−) Gains on sales of businesses / (+) divestiture costs (unallocated corporate)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),-N({V("rc_gain")})-N({V("rc_divest")}),"")')
    S('r_impair', '  (+) Goodwill impairment (Q4 2008)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),IF(N({V("is_othop")})>0,{V("is_othop")},0),"")')
    S('r_b21', '  (+) B-21 loss provisions (company-quantified; model item)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),N({V("d_b21")}),"")')
    S('r_adj', '  = Adjusted EBITDA (model)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{V("r_ebitda")}+{V("r_gain")}+{V("r_impair")}+{V("r_b21")},"")',
      note='Model definition; used for leverage (net debt / adjusted EBITDA) and EV / EBITDA. Includes the FAS/CAS operating adjustment (part of GAAP operating income).')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_def', '  Definition / basis', 'text', 'gen')
    S('r_ebit_h', 'To adjusted EBIT (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ddan', '  (−) Depreciation & amortization', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("d_dda")}),-{V("d_dda")},"")')
    S('r_aebit', '  = Adjusted EBIT (model; after purchased-intangible amortization, incl. the FAS/CAS operating adjustment)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+{V("r_ddan")},"")',
      note='Full-cost: amortization and the FAS/CAS adjustment are not added back. The DCF deducts the FAS/CAS operating adjustment (non-cash pension accounting) from NOPAT.')
    S('r_aebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_aebit', 'is_rev'))
    S('r_cash', '  Memo: divestiture costs (cash; added back above, deducted in the DCF)', 'memo_calc', 'm', all=lambda: f'=IF(ISNUMBER({V("rc_divest")}),-N({V("rc_divest")}),0)')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: NET EARNINGS / DILUTED EPS → ADJUSTED NET EARNINGS → ADJUSTED EPS (company definitions in force: pension-adjusted 2009–17, MTM-adjusted 2018+)', 'section',
      note=('ADJUSTED EPS — 2009–2016 "pension-adjusted diluted EPS" (excludes the net FAS/CAS pension adjustment after tax at the statutory rate; continuing operations in the 2009–12 releases); '
            '2017 "EPS excluding the impact of tax reform and the related discretionary pension contribution"; 2018+ "MTM-adjusted EPS" (excludes the Q4 MTM (benefit) expense net of federal and deferred state tax). '
            'Interim quarters from 2018 carry no MTM, so MTM-adjusted EPS = diluted EPS. 2006–08: none published (adjusted = GAAP, flagged).'))
    S('e_ni', 'Net earnings (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('e_basis', '  (−) Basis difference: discontinued operations (company adjusted EPS on continuing operations, 2009–12)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("e_pub")}),IF({V("e_cont_flag")}=1,-N({V("is_disc")}),0),IF(ISNUMBER({V("e_ni")}),0,""))', fc=lambda: '=0')
    S('e_cont_flag', '  Flag: company adjusted EPS on continuing operations (1 = yes)', 'driver', 'gen', data='e_cont_flag', fc=lambda: '=0')
    S('e_item', '  (+/−) Company adjusting item, pre-tax: − net FAS/CAS pension adjustment (2009–17) / − MTM benefit, + MTM expense (2018+)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("e_pub")}),IF({V("e_def_flag")}=2,-N({V("is_mtm")}),IF({V("e_def_flag")}=1,-N({V("rc_tot")}),0)),IF(ISNUMBER({V("e_ni")}),0,""))',
      fc=lambda: f'=-N({V("is_mtm")})',
      note='Definition 1 (pension-adjusted): the whole net FAS/CAS pension adjustment is removed. Definition 2 (MTM-adjusted): only the Q4 MTM (benefit) expense. Forecast: MTM nil.')
    S('e_def_flag', '  Flag: definition (1 = pension-adjusted, 2 = MTM-adjusted, 3 = tax-reform-adjusted 2017, 0 = none published)', 'driver', 'gen', data='e_def_flag', fc=lambda: '=2')
    S('e_tax', '  (−) Tax effect of the adjustment & other company items (derived: published adjusted net earnings − net earnings − item)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_sh")})),{V("e_pub")}*{V("e_sh")}-{V("e_ni")}-{V("e_basis")}-{V("e_item")},IF(ISNUMBER({V("e_ni")}),0,""))',
      fc=lambda: f'=-{V("e_item")}*{V("e_rate")}',
      note=('Historical: derived from the published adjusted EPS × diluted shares (the company publishes the per-share bridge: statutory federal tax at 35% / 21% plus deferred state tax; '
            '2017 also removes the tax-reform charge and the related discretionary pension contribution). Forecast: 26.25% (21% federal + 5.25% blended state, as in the company\'s per-share schedule).'))
    S('e_rate', '  Tax rate on the adjusting item (forecast)', 'pct', 'pct', fc_in=0.2625)
    S('e_adjni', '  = Adjusted net earnings (model bridge)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("e_tax")}),{V("e_ni")}+{V("e_basis")}+{V("e_item")}+{V("e_tax")},"")')
    S('e_pubni', '  Company-published MTM-adjusted net earnings (2018+)', 'memo', 'm', data='mtm_adj_ni_pub', flow=True)
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted EPS – diluted ($) (model bridge; = MTM-adjusted EPS in the forecast)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("e_sh")}),IFERROR(({V("e_adjni")}+N({V("eps_adj")}))/{V("e_sh")},""),"")')
    S('e_pub', '  Company-published adjusted EPS ($) (pension-adjusted / tax-reform-adjusted / MTM-adjusted)', 'eps_memo', 'ps', data='adj_eps_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0101,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_ps_pub', '  Memo: company per-share impact of the adjustment, net of tax (after-tax net pension adjustment / MTM adjustment per share)', 'eps_memo', 'ps', data='e_ps_pub')
    S('e_def', '  Definition / basis (company adjusted EPS definition in force)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Sales y/y %', 'growth', 'pct', all=growth('is_rev'))
    for s, title, code in SEG: S(f'gm_{s}', f'  {title} sales y/y %', 'growth', 'pct', all=growth(f'{s}_s'))
    S('gm_soi', '  Segment operating income y/y %', 'growth', 'pct', all=growth('g_soi'))
    S('gm_ebitda', '  Adjusted EBITDA (model) y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating income y/y %', 'growth', 'pct', all=growth('is_oi'))
    S('gm_ni', '  Net earnings y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_som', '  Segment operating margin rate %', 'pct', 'pct', all=ratio('g_soi', 'is_rev'))
    S('gm_inc', '  Incremental segment operating margin (Δ segment OI / Δ sales)', 'pct', 'pct', all=incr('g_soi', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin rate %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_ga', '  G&A % of sales', 'pct', 'pct', all=ratio('is_ga', 'is_rev'))
    S('gm_fascas', '  FAS/CAS operating adjustment % of sales', 'pct', 'pct', all=ratio('rc_fascas', 'is_rev'))
    blank()
