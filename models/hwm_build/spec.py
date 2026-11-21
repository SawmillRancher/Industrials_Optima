"""Row specification of the HWM Model sheet, part 1 (MLM template layout and process):
segment build (Engine Products / Fastening Systems / Engineered Structures / Forged Wheels: third-party sales x Segment Adjusted
EBITDA margin) -> less adjusted corporate expense = Adjusted EBITDA -> end-market memo -> M&A lever -> group total & FY26
guidance calibration -> cost drivers & special items -> income statement -> GAAP-to-adjusted bridges -> growth & margins."""
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
def ACT0(key): return f'SUM({PQ1}{R[key]}:{PQ3}{R[key]})' # 9M 2025 actual
def B1(key): return f'{LQ}{R[key]}'                       # 30-Sep-2026 balance
def tolchk(a, b, tol, nd=0, np_=''):
    return f'=IF(AND(ISNUMBER({a}),ISNUMBER({b})),IF(ABS({a}-{b})<={tol},0,ROUND({a}-{b},{nd})),"{np_}")'

SEG = [('ep', 'Engine Products', 'EP'), ('fs', 'Fastening Systems', 'FS'), ('es', 'Engineered Structures', 'ES'), ('fw', 'Forged Wheels', 'FW')]
SEGK = [s for s, *_ in SEG]
DESCR = {
    'ep': 'Engine Products (airfoils and seamless rolled rings for aircraft engines and industrial gas turbines; engine spares)',
    'fs': 'Fastening Systems (aerospace fastening systems, fluid fittings, latches; commercial-transportation fasteners; CAM and Brunner from 2026)',
    'es': 'Engineered Structures (titanium ingots and mill products, aluminum and nickel forgings, machined airframe structures; Savannah disk forging sold Mar-2026)',
    'fw': 'Forged Wheels (forged aluminum wheels for heavy-duty trucks, trailers and buses; aluminum cost passed through)'}

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / baseline / low of the FY26 guidance ranges.'))
    r = 11
    SCEN_ROWS.append((r, 'out_hdr', V0['out_hdr'], 'High', 'Baseline', 'Low', V0['out_note'])); r += 1
    for key, lab, (hi, mid, lo), nf, note in V0['outlook']:
        SC[key] = r; SCEN_ROWS.append((r, 'out', lab, hi, mid, lo, note, nf)); r += 1
    r += 1
    SCEN_ROWS.append((r, 'pt_hdr', 'Q4/26E and FY26 point estimates (all cases)', None, None, None, None)); r += 1
    for key, lab, vals, nf, note in V0['points']:
        SC[key] = r
        SCEN_ROWS.append((r, 'pt', lab, None, vals, None, note, nf)); r += 1
    r += 1
    SC['LEV'] = r
    SCEN_ROWS.append((r, 'lev', '  Target net debt / Adjusted EBITDA (x) — buyback plug 2027E+', *V0['lev'], V0['lev_note']))
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
    S('sec_seg', 'SEGMENT P&L — ENGINE PRODUCTS · FASTENING SYSTEMS · ENGINEERED STRUCTURES · FORGED WHEELS (third-party sales × Segment Adjusted EBITDA margin)', 'section',
      note='SEGMENT BUILD — modelling logic (segment third-party sales → Segment Adjusted EBITDA at the segment margin → less adjusted corporate expense = Adjusted EBITDA → GAAP P&L)')
    blank()
    for s, title, code in SEG:
        first = s == 'ep'
        S(f'{s}_hdr', DESCR[s], 'block', note=f'{title.upper()} — modelling logic')
        S(f'{s}_rev', f'  {title} — third-party sales', 'line_b', 'm1', data=f'{s}_rev', flow=True,
          qe=lambda s=s: f'={P(s + "_rev")}*(1+{V(s + "_g")})', ae=lambda s=s: f'={P(s + "_rev")}*(1+{V(s + "_g")})',
          note=('Release segment panel, as originally reported (2025 as recast for the Q1-26 realignment; FY2019 and Q1/20 recast continuing operations). '
                'Q4/26E: prior-year quarter × (1 + growth). 2027E+: prior year × (1 + scenario lever).') if first else None)
        S(f'{s}_g', '    y/y %', 'growth', 'pct', all=growth(f'{s}_rev'),
          qe=lambda s=s: f'={V(s + "_pre")}+{QEa("cal_g")}', ae=lambda code=code: '=' + CH(SC[f'{code}_G'][CTX.col.year]),
          note='Q4/26E: Q3/26 y/y growth of the segment + revenue-guidance calibration Δ (Group block). 2027E–2030E: scenario lever (Bull/Base/Bear table →).' if first else None)
        S(f'{s}_pre', '    Q4/26E growth before revenue calibration (= Q3/26 y/y; same perimeter: CAM / Brunner in, Savannah out)', 'driver', 'pct',
          qe=lambda s=s: f'=IFERROR({Q3}{R[s + "_rev"]}/{PQ3}{R[s + "_rev"]}-1,0)')
        S(f'{s}_gorg', '    Memo: organic revenue growth % (company; excl. acquisitions and divestitures)', 'memo', 'pct', data=f'{s}_gorg',
          note='Published in the release "Reconciliation of Organic Revenue Growth" from Q1-26 (CAM, Brunner, Savannah); before 2026 there were no acquisitions or divestitures in the comparison, so organic = reported.' if first else None)
        S(f'{s}_ad', '    Memo: sales of acquisitions in the period (excluded from organic revenue)', 'memo', 'm1', data=f'{s}_ad', flow=True)
        S(f'{s}_mix', '  % of total sales', 'pct', 'pct', all=ratio(f'{s}_rev', 'g_rev'))
        S(f'{s}_ebitda', f'  {title} — Segment Adjusted EBITDA', 'line', 'm1', data=f'{s}_ebitda', flow=True,
          qe=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}', ae=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}',
          note=('Company segment measure from Q1-22 (2021 as recast by the company; 2019–20 = segment operating profit + segment D&A, the identity behind that recast). '
                'Forecast = segment sales × segment margin.') if first else None)
        S(f'{s}_m', '  Segment Adjusted EBITDA margin %', 'pct', 'pct', all=ratio(f'{s}_ebitda', f'{s}_rev'),
          qe=lambda s=s: f'={V(s + "_m_pre")}+{QEa("cal_m")}', ae=lambda code=code: '=' + CH(SC[f'{code}_M'][CTX.col.year]),
          note='Q4/26E: Q3/26 margin + Adjusted-EBITDA-guidance calibration Δ (Group block). 2027E+: scenario lever.' if first else None)
        S(f'{s}_m_pre', '  Q4/26E margin before calibration (= Q3/26 segment margin)', 'driver', 'pct', qe=lambda s=s: f'={Q3}{R[s + "_m"]}')
        S(f'{s}_inc', '  Incremental margin (Δ Segment Adjusted EBITDA / Δ sales)', 'pct', 'pct', all=incr(f'{s}_ebitda', f'{s}_rev'))
        S(f'{s}_da', '  Memo: segment provision for depreciation and amortization', 'memo', 'm1', data=f'{s}_da', flow=True)
        S(f'{s}_capex', '  Memo: segment capital expenditures', 'memo', 'm1', data=f'{s}_capex', flow=True)
        if s in ('ep', 'es'):
            S(f'{s}_rev_rc', '  Memo: FY2024 third-party sales as recast for the Q1-26 segment realignment', 'memo', 'm1', data=f'{s}_rev_rc', flow=True,
              note='Q1-26: a titanium alloy location moved from Engine Products to Engineered Structures; the company recast FY2024 and the 2025 quarters. FY2024 stays as reported (its quarters were never recast).' if first else None)
            S(f'{s}_ebitda_rc', '  Memo: FY2024 Segment Adjusted EBITDA as recast for the Q1-26 segment realignment', 'memo', 'm1', data=f'{s}_ebitda_rc', flow=True)
        blank()
    S('co_hdr', 'Corporate (costs not allocated to the segments)', 'block',
      note='CORPORATE — adjusted corporate expense = Σ Segment Adjusted EBITDA − consolidated Adjusted EBITDA (excludes corporate D&A and special items)')
    S('rev_oth', '  Corporate / other sales outside the segments (derived: consolidated sales − Σ segments)', 'line', 'm1', data='rev_oth', flow=True, fc=lambda: '=0',
      note='2019–20: small corporate sales as recast; otherwise whole-million rounding of the release. Forecast nil.')
    S('corp', '  Adjusted corporate expense (excl. D&A and special items; derived)', 'line', 'm1', data='corp_adj', flow=True,
      qe=lambda: f'={PT("pt_corp")}', ae=lambda: f'={V("is_rev")}*{V("corp_pct")}',
      note='History: Σ Segment Adjusted EBITDA − Adjusted EBITDA (model bridge). Q4/26E: point estimate. 2027E+: % of sales.')
    S('corp_pct', '  Adjusted corporate expense % of sales', 'pct', 'pct', all=ratio('corp', 'is_rev'), ae_in=V0['corp_pct'])
    S('corp_rep', '  Memo: Corporate expense as reported (segment reconciliation; incl. corporate D&A and special items)', 'memo', 'm1', data='corp_rep', flow=True)
    blank()
    S('mx_hdr', 'Revenue by end market (Form 10-Q / 10-K revenue note; memo — history)', 'block', note='END MARKETS — as disclosed; Q4 = year − nine months')
    for k, lab in (('ca', 'Aerospace — commercial'), ('df', 'Aerospace — defense'), ('ct', 'Commercial transportation'),
                   ('io', 'Industrial and other (gas turbines, oil & gas, general industrial)')):
        S(f'em_{k}', f'  {lab}', 'line', 'm1', data=f'em_{k}', flow=True)
    S('em_gt', '    of which gas turbines (basis of the FY2025 Form 10-K)', 'memo', 'm1', data='em_gt', flow=True)
    S('em_tot', '  Total end-market revenue (as disclosed)', 'memo', 'm1', data='em_tot', flow=True)
    S('em_chk', '  Check: end markets vs total end-market revenue (should be 0; ±1 rounding)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("em_ca")}),ISNUMBER({V("em_tot")})),IF(ABS({V("em_ca")}+{V("em_df")}+{V("em_ct")}+{V("em_io")}-{V("em_tot")})<=1.1,0,ROUND({V("em_ca")}+{V("em_df")}+{V("em_ct")}+{V("em_io")}-{V("em_tot")},0)),"")')
    for k, lab in (('ca', 'Commercial aerospace'), ('df', 'Defense aerospace'), ('ct', 'Commercial transportation'), ('io', 'Industrial and other')):
        S(f'em_{k}_p', f'  {lab} % of end-market revenue', 'pct', 'pct', hist=ratio(f'em_{k}', 'em_tot'))
    for k, lab in (('ca', 'Commercial aerospace'), ('df', 'Defense aerospace'), ('ct', 'Commercial transportation'), ('io', 'Industrial and other'), ('gt', 'Gas turbines')):
        S(f'em_{k}_g', f'  {lab} y/y %', 'growth', 'pct', hist=growth(f'em_{k}'))
    S('gc_ep', '  Contribution to total sales growth — Engine Products (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("ep_rev")}-{P("ep_rev")})/{P("g_rev")},"")' if CTX.col.prior else None))
    S('gc_oth', '  Contribution to total sales growth — other segments (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR((({V("g_rev")}-{V("ep_rev")})-({P("g_rev")}-{P("ep_rev")}))/{P("g_rev")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — unallocated bolt-ons closed from 2027E; Base = none)', 'block',
      note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=3.7, e26_in=0.0,
      note='CAM: ~$1.8bn for FY2026 revenue of ~$485–495m (8-K 22-Dec-2025) ≈ 3.7x sales; ~13x FY2026 adjusted EBITDA after synergies and tax benefit. Input (assumption for future deals).')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.06)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}',
      note='Mid-year convention.')
    S('m_m', '  Adjusted EBITDA margin of acquired businesses %', 'driver', 'pct', e26_in=0.0, ae_in=0.22, note='CAM: adjusted EBITDA margin above 20% before synergies (8-K 22-Dec-2025).')
    S('m_ebitda', '  Adjusted EBITDA from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.11, note='CAM + Brunner preliminary PPA: PP&E $204m of $1,929m (11%).')
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.22, note='CAM + Brunner preliminary PPA: intangibles $425m of $1,929m (22%); goodwill $1,096m.')
    S('m_life', '  Intangible amortization life (years; assumption)', 'driver', 'gen', e26_in=0, ae_in=15)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (inside D&A)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group Total — sales & Adjusted EBITDA (segment build) → FY26 guidance calibration', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Sales (segment build)', 'total', 'm1',
      hist=lambda: '=' + '+'.join(V(s + '_rev') for s in SEGK) + f'+N({V("rev_oth")})',
      fc=lambda: '=' + '+'.join(V(s + '_rev') for s in SEGK) + f'+N({V("rev_oth")})+N({V("m_rev")})',
      note='Σ segment third-party sales (+ corporate / other; + future acquisitions from 2027E).')
    S('g_rev_g', '  Sales y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs consolidated sales (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=0.15,0,ROUND({V("g_rev")}-{V("is_rev")},1)),"")')
    S('g_adj', 'Adjusted EBITDA (segment build)', 'total', 'm1',
      all=lambda: '=' + '+'.join(V(s + '_ebitda') for s in SEGK) + f'-{V("corp")}+N({V("m_ebitda")})',
      note='Σ Segment Adjusted EBITDA − adjusted corporate expense (+ future acquisitions). Drives the GAAP P&L below (operating income = Adjusted EBITDA − D&A − special items).')
    S('g_adjm', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('g_adj', 'is_rev'))
    S('g_adj_g', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('g_adj'))
    S('g_chk_adj', '  Check: segment build vs Adjusted EBITDA bridge (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_adj")}),ISNUMBER({V("r_adj")})),IF(ABS({V("g_adj")}-{V("r_adj")})<=0.15,0,ROUND({V("g_adj")}-{V("r_adj")},1)),"")')
    S('cal_guid', '  Memo: FY26 revenue guidance (scenario end-point: high / baseline / low)', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_rev']), note=V0['rev_guid_note'])
    S('cal_pre', '  Sales before calibration (Q4/26E helper)', 'line', 'm1', qe=lambda: '=' + '+'.join(f'{P(s + "_rev")}*(1+{V(s + "_pre")})' for s in SEGK))
    S('cal_sens', '  Sales sensitivity to +1.00 of growth (Q4/26E helper)', 'line', 'm1', qe=lambda: '=' + '+'.join(P(s + '_rev') for s in SEGK))
    S('cal_g', '  Guidance calibration: Δ y/y growth applied to all segments (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_guid", E26)}-{ACT("g_rev")}-{V("cal_pre")})/{V("cal_sens")}',
      note='Solves the uniform growth shift (vs Q3/26 y/y rates) so that FY26 sales = the guidance end-point for the active scenario (closed form, no circularity).')
    S('cal_rev_chk', '  Check: FY26 sales vs guidance end-point (should be 0)', 'check', 'm1', e26=lambda: f'=ROUND({V("g_rev")}-{V("cal_guid")},1)')
    S('cal_eb', '  Memo: FY26 Adjusted EBITDA guidance (scenario end-point)', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_ebitda']), note=V0['eb_guid_note'])
    S('cal_eb_req', '  Q4/26E Adjusted EBITDA required (guidance − nine months actual)', 'memo_calc', 'm1', e26=lambda: f'={V("cal_eb")}-{ACT("g_adj")}')
    S('cal_eb_pre', '  Adjusted EBITDA before margin calibration (Q4/26E helper)', 'line', 'm1',
      qe=lambda: '=' + '+'.join(f'{V(s + "_rev")}*{V(s + "_m_pre")}' for s in SEGK) + f'-{V("corp")}')
    S('cal_segrev', '  Segment sales (Q4/26E helper)', 'line', 'm1', qe=lambda: '=' + '+'.join(V(s + '_rev') for s in SEGK))
    S('cal_m', '  Guidance calibration: Δ segment margin applied to all segments (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_eb_req", E26)}-{V("cal_eb_pre")})/{V("cal_segrev")}',
      note='Solves the uniform segment-margin shift (vs Q3/26 margins) so that FY26 Adjusted EBITDA = the guidance end-point for the active scenario.')
    S('cal_eb_chk', '  Check: FY26 Adjusted EBITDA vs guidance end-point (should be 0)', 'check', 'm1', e26=lambda: f'=ROUND({V("g_adj")}-{V("cal_eb")},1)')
    S('cal_eps', '  Memo: FY26 adjusted EPS guidance (scenario end-point, $) — information, not forced', 'eps_memo', 'ps', e26=lambda: '=' + CH(SC['out_eps']), note=V0['eps_guid_note'])
    S('cal_eps_d', '    Model FY26 adjusted EPS − guidance ($)', 'eps_memo', 'ps', e26=lambda: f'={V("e_eps")}-{V("cal_eps")}')
    S('cal_fcf', '  Memo: FY26 free cash flow guidance (scenario end-point) — information', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_fcf']))
    S('cal_fcf_d', '    Model FY26 free cash flow − guidance', 'memo_calc', 'm1', e26=lambda: f'={V("fcf")}-{V("cal_fcf")}')
    S('cal_q4', '  Memo: Q4 2026 revenue guidance (scenario end-point) — information (FY guidance less nine months implies ~$13m less)', 'memo', 'm1',
      qe=lambda: '=' + CH(SC['out_q4rev']))
    S('cal_q4_d', '    Model Q4/26E sales − Q4 guidance', 'memo_calc', 'm1', qe=lambda: f'={V("g_rev")}-{V("cal_q4")}')
    S('cal_27', '  Memo: FY2027 revenue outlook ~$11.5bn, ~+12% y/y (Q3-26 release) — information', 'memo', 'm1', ae_in={2027: V0['rev_2027']})
    S('cal_27_d', '    Model FY2027E sales vs outlook %', 'memo_calc', 'pct', ae=lambda: (f'={V("g_rev")}/{V("cal_27")}-1' if CTX.col.year == 2027 else None))
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A & special items', 'block', note='COST DRIVERS — inputs that drive forecast cost lines (Q4/26E: point estimates; 2027E+: % of sales or schedules)')
    S('d_da', '  Provision for depreciation and amortization (total)', 'line', 'm1', data='da', flow=True,
      qe=lambda: f'={PT("pt_da")}', ae=lambda: f'={V("is_rev")}*{V("d_da_pct")}+N({V("m_amort")})',
      note='Statement of operations line. Q4/26E point estimate; 2027E+: % of sales (+ future-acquisition amortization).')
    S('d_da_pct', '  D&A % of sales', 'pct', 'pct', all=ratio('d_da', 'is_rev'), ae_in=V0['da_pct'],
      note='Q3/26 3.4% (incl. CAM / Brunner fair-value depreciation and amortization); rising with capacity investment in Engine Products.')
    S('d_amort', '  of which amortization of intangibles (input — annual figures only in the Form 10-K)', 'line', 'm1',
      qe=lambda: f'={PT("pt_amort")}', ae=lambda: f'={V("d_amort_in")}+N({V("m_amort")})', note=V0['amort_note'])
    S('d_amort_in', '  Amortization of intangibles held at 30-Sep-2026 (input, assumption)', 'driver', 'm1', ae_in=V0['amort_in'])
    S('d_dep', '  of which depreciation (D&A − amortization)', 'line', 'm1', qe=lambda: f'={V("d_da")}-{V("d_amort")}', ae=lambda: f'={V("d_da")}-{V("d_amort")}')
    S('d_sga', '  SG&A % of sales', 'pct', 'pct', all=ratio('is_sga', 'is_rev'), qe=lambda: f'={Q3}{R["d_sga"]}', ae_in=V0['sga_pct'],
      note='Q4/26E: Q3/26 ratio; 2027E+ input. Cost of goods sold is implied: sales − operating income − other operating costs.')
    S('d_rd', '  R&D % of sales', 'pct', 'pct', all=ratio('is_rd', 'is_rev'), qe=lambda: f'={Q3}{R["d_rd"]}', ae_in=V0['rd_pct'])
    S('d_sbc', '  Stock-based compensation (cash-flow statement)', 'line', 'm1', data='cf_sbc', flow=True,
      qe=lambda: f'={Q3}{R["d_sbc"]}', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}',
      note='Q4/26E: Q3/26 level; 2027E+: % of sales. Howmet does not adjust out stock-based compensation.')
    S('d_sbc_pct', '  Stock-based compensation % of sales', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_adj_h', '  Special items (pre-tax, excluded by the company from adjusted measures; forecast inputs = nil):', 'sub', 'gen')
    S('sp_restr', '  Restructuring and other charges / (credits)', 'line', 'm1', data='sp_restr', flow=True, qe_in=0.0, ae_in=0.0,
      note='Statement of operations line (incl. gains / losses on asset sales: Savannah gain $93m in Q1/26). Forecast input nil.')
    S('sp_oth', '  Other operating special items (acquisition costs, plant fires, closures, legal, separation; in cost of goods sold / SG&A)', 'line', 'm1',
      data='sp_oth_op', flow=True, labkey='sp_op_labels', qe_in=0.0, ae=lambda: f'={V("m_spend")}*{V("sp_acq_pct")}',
      note='History: published adjusted operating income (or Adjusted EBITDA) − operating income − restructuring. 2027E+: acquisition costs on M&A-lever spend.')
    S('sp_acq_pct', '  Acquisition costs % of acquisition spend (assumption)', 'pct', 'pct', ae_in=0.02, note='CAM + Brunner: $36m of acquisition and acquisition-related costs in 9M 2026 on $1,929m (1.9%).')
    S('sp_nonop', '  Non-operating special items (loss on debt redemption, financing and separation interest, legal settlement; below operating income)', 'line', 'm1',
      data='sp_nonop', flow=True, qe_in=0.0, ae_in=0.0, note='History: pre-tax special items in the adjusted-net-income reconciliation − operating special items. Forecast nil.')
    S('sp_in_da', '  Memo: special items recorded in D&A (not added back again in Adjusted EBITDA; Q2/20 only)', 'memo', 'm1', data='sp_in_da', flow=True, fc=lambda: '=0')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'STATEMENT OF CONSOLIDATED OPERATIONS (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (operating income = Adjusted EBITDA − D&A − special items; cost of goods sold implied)')
    S('is_rev', 'Sales', 'total', 'm1', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the segment build.')
    S('is_cogs', 'Cost of goods sold (exclusive of expenses below)', 'line', 'm1', data='cogs', flow=True,
      fc=lambda: f'={V("is_rev")}-{V("is_sga")}-{V("is_rd")}-{V("is_dda")}-{V("is_restr")}-{V("is_oi")}', note='Forecast = implied by operating income from the Adjusted EBITDA build.')
    S('is_sga', 'Selling, general administrative, and other expenses', 'line', 'm1', data='sga', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_sga")}')
    S('is_rd', 'Research and development expenses', 'line', 'm1', data='rd', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_rd")}')
    S('is_dda', 'Provision for depreciation and amortization', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("d_da")}),{V("d_da")},"")')
    S('is_restr', 'Restructuring and other charges / (credits)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sp_restr")}),{V("sp_restr")},"")')
    S('is_oi', 'Operating income', 'total', 'm1', data='oi', flow=True, fc=lambda: f'={V("g_adj")}-{V("d_da")}-{V("o_tot")}+{V("sp_in_da")}',
      note='History as reported. Forecast = Adjusted EBITDA (segment build) − D&A − special items.')
    S('is_oi_m', '  Operating income margin %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('is_oi_chk', '  Check: sales − costs vs reported operating income (should be 0; ±2 whole-million rounding)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_oi")}),IF(ABS({V("is_rev")}-{V("is_cogs")}-{V("is_sga")}-{V("is_rd")}-{V("is_dda")}-{V("is_restr")}-{V("is_oi")})<=2.1,0,ROUND({V("is_rev")}-{V("is_cogs")}-{V("is_sga")}-{V("is_rd")}-{V("is_dda")}-{V("is_restr")}-{V("is_oi")},0)),"")')
    S('is_int', 'Interest expense, net', 'line', 'm1', data='int', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_cp")}*{V("ds_r_cp")}+{V("ds_fees")}',
      note='Q4/26E point estimate. 2027E+ = rate × opening notes + rate × opening commercial paper + fees (opening balances: no circularity).')
    S('is_loss', 'Loss on debt redemption', 'line', 'm1', data='loss_debt', flow=True, fc=lambda: '=0',
      note='Shown on its own line from the Q4-21 release; Q2/21 split out of interest expense ($23m) per the company\'s later presentation. Forecast nil.')
    S('is_oth', 'Other expense / (income), net', 'line', 'm1', data='oth', flow=True, qe=lambda: f'={PT("pt_oth")}', ae_in=V0['oth'],
      note='Non-service pension and postretirement cost, deferred-compensation and FX items, net of interest income. Input.')
    S('is_ebt', 'Income before income taxes', 'line_b', 'm1', data='ebt', flow=True, fc=lambda: f'={V("is_oi")}-{V("is_int")}-{V("is_loss")}-{V("is_oth")}')
    S('is_tax', 'Provision for income taxes', 'line', 'm1', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Q4/26E: point estimate (operational rate 20.3% in 9M 2026). 2027E+: input.')
    S('is_cont', 'Income from continuing operations after income taxes', 'line_b', 'm1', data='cont', flow=True, fc=lambda: f'={V("is_ebt")}-{V("is_tax")}')
    S('is_disc', 'Income from discontinued operations after income taxes (Arconic Corporation, separated 1-Apr-2020)', 'line', 'm1', data='disc', flow=True, fc=lambda: '=0')
    S('is_ni', 'Net income', 'total', 'm1', data='ni', flow=True, fc=lambda: f'={V("is_cont")}+{V("is_disc")}')
    S('is_ni_chk', '  Check: statement arithmetic below operating income (should be 0; ±2 whole-million rounding)', 'check', 'm1',
      hist=lambda: (f'=IF(ISNUMBER({V("is_ni")}),IF(ABS({V("is_oi")}-{V("is_int")}-{V("is_loss")}-{V("is_oth")}-{V("is_tax")}+{V("is_disc")}-{V("is_ni")})<=2.1,0,'
                    f'ROUND({V("is_oi")}-{V("is_int")}-{V("is_loss")}-{V("is_oth")}-{V("is_tax")}+{V("is_disc")}-{V("is_ni")},0)),"")'))
    S('is_sbc', '  Memo: stock-based compensation', 'memo_calc', 'm1', all=lambda: f'=IF(ISNUMBER({V("d_sbc")}),{V("d_sbc")},"")')
    S('eps_hdr', '(Earnings per share — Howmet Aerospace common shareholders)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={B1("bs_shares")}-${E26}${R["bb_sh"]}*0.5',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q4/26E: shares outstanding at 30-Sep-2026 − Q4 buybacks (mid-quarter). 2027E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")',
      note='Net income / weighted diluted shares (preferred dividends of ~$0.5m a quarter to Q3/25 not deducted; ±$0.01 vs reported).')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01 rounding; FY2019 ±0.02)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<={0.0201 if CTX.col.year == 2019 else 0.0101},0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('eps_cont', '  Memo: EPS – diluted, continuing operations, as reported ($)', 'eps_memo', 'ps', data='eps_d_cont')
    S('dps', '  Cash dividends paid per common share ($; derived: dividends paid ÷ basic shares)', 'line', 'ps', data='dps', flow=True, qe_in=V0['dps_q'],
      ae=lambda: f'={P("dps")}*(1+{V("dps_g")})', note='History derived from the cash-flow statement (includes <$1m a quarter of preferred dividends to 2025). Q4/26E: $0.14 declared rate. 2027E+: prior year × (1 + growth).')
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'])
    blank()

    # ------------------------------------------------------------------ RECON 1: OI -> adjusted OI -> adjusted EBITDA
    S('sec_r1', 'RECONCILIATION: OPERATING INCOME → ADJUSTED OPERATING INCOME → ADJUSTED EBITDA (company definition)', 'section',
      note='ADJUSTED EBITDA — operating income + restructuring and other charges + other special items = adjusted operating income; + D&A = Adjusted EBITDA (release "Calculation of Financial Measures")')
    S('o_op', 'Operating income (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_oi")}')
    S('o_restr', '  (+) Restructuring and other charges / (credits)', 'line', 'm1', all=lambda: f'={V("sp_restr")}')
    S('o_oth', '  (+) Other operating special items', 'line', 'm1', all=lambda: f'={V("sp_oth")}')
    S('o_tot', '  Total operating special items (pre-tax)', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_restr")}),{nsum(["o_restr", "o_oth"])},"")')
    S('o_adj', '  = Adjusted operating income (model bridge)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_tot")},"")')
    S('o_adj_m', '  Adjusted operating income margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company-published adjusted operating income (operating income excluding special items)', 'memo', 'm1', data='adj_oi_pub', flow=True)
    S('o_chk', '  Check: model bridge vs company-published adjusted operating income (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),IF(ABS({V("o_adj")}-{V("o_pub")})<=0.15,0,ROUND({V("o_adj")}-{V("o_pub")},1)),"n/p")')
    S('o_da', '  (+) Provision for depreciation and amortization', 'line', 'm1', all=lambda: f'={V("d_da")}')
    S('o_inda', '  (−) Special items recorded in D&A', 'line', 'm1', all=lambda: f'=-N({V("sp_in_da")})')
    S('r_adj', '  = Adjusted EBITDA (model bridge)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_adj")}),{V("o_adj")}+{V("o_da")}+{V("o_inda")},"")',
      note='Company definition: operating income excluding restructuring and other charges, D&A and special items. Used for leverage (net debt / Adjusted EBITDA) and EV / EBITDA.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_adj_pub', '  Company-published Adjusted EBITDA', 'memo', 'm1', data='adj_ebitda_pub', flow=True)
    S('r_chk', '  Check: model vs company-published Adjusted EBITDA (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("r_adj_pub")}),ISNUMBER({V("r_adj")})),IF(ABS({V("r_adj")}-{V("r_adj_pub")})<=0.15,0,ROUND({V("r_adj")}-{V("r_adj_pub")},1)),"n/p")')
    S('o_def', '  Definition / basis (company adjusted definition in force)', 'text', 'gen',
      note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('o_adj_g', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental Adjusted EBITDA margin (Δ Adjusted EBITDA / Δ sales)', 'pct', 'pct', all=incr('r_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: net income -> EBITDA -> adjusted EBITDA
    S('sec_r2', 'RECONCILIATION: INCOME FROM CONTINUING OPERATIONS → EBITDA → ADJUSTED EBITDA (model definition of EBITDA; ties to the company Adjusted EBITDA)', 'section',
      note='EBITDA — income from continuing operations + income taxes + interest + loss on debt redemption + other expense + D&A = EBITDA (model definition: the company publishes Adjusted EBITDA only); + special items = Adjusted EBITDA')
    S('r_ni', 'Income from continuing operations (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_cont")}')
    S('r_tax', '  (+) Provision for income taxes', 'line', 'm1', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest expense, net and loss on debt redemption', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_int")}),{V("is_int")}+N({V("is_loss")}),"")')
    S('r_oth', '  (+) Other expense / (income), net', 'line', 'm1', all=lambda: f'={V("is_oth")}')
    S('r_da', '  (+) Provision for depreciation and amortization', 'line', 'm1', all=lambda: f'={V("d_da")}')
    S('r_ebitda', '  = EBITDA (model definition)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_tax")}+{V("r_int")}+{V("r_oth")}+{V("r_da")},"")')
    S('r_sp', '  (+) Operating special items not already in D&A', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_tot")}),{V("o_tot")}-N({V("sp_in_da")}),"")')
    S('r_adj2', '  = Adjusted EBITDA (from income from continuing operations)', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{V("r_ebitda")}+{V("r_sp")},"")')
    S('r_chk2', '  Check: vs Adjusted EBITDA bridge above (should be 0; ±2 whole-million rounding)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_adj2")}),ISNUMBER({V("r_adj")})),IF(ABS({V("r_adj2")}-{V("r_adj")})<=2.1,0,ROUND({V("r_adj2")}-{V("r_adj")},0)),"")')
    S('r_ebit_h', 'To adjusted EBIT, full-cost (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ddan', '  (−) Provision for depreciation and amortization (total)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("d_da")}),-{V("d_da")},"")')
    S('r_ebit', '  = Adjusted EBIT, full-cost (Adjusted EBITDA − total D&A; = adjusted operating income)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+{V("r_ddan")},"")',
      note='Howmet does not add back amortization of acquired intangibles or stock-based compensation, so adjusted operating income is already full-cost.')
    S('r_ebit_m', '  Adjusted EBIT (full-cost) margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: operating special items (cash costs excluded by the company; deducted in the DCF)', 'memo_calc', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("o_tot")}),{V("o_tot")},"")')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: INCOME FROM CONTINUING OPERATIONS / DILUTED EPS → ADJUSTED NET INCOME → ADJUSTED EPS (company definition)', 'section',
      note='ADJUSTED EPS — income from continuing operations + pre-tax special items + tax impact of special items and discrete tax items ("Net income excluding Special items"; "Adjusted Net income" from Q1-26)')
    S('e_ni', 'Income from continuing operations (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_cont")}')
    S('e_restr', '  (+) Restructuring and other charges / (credits)', 'line', 'm1', all=lambda: f'={V("sp_restr")}')
    S('e_oth', '  (+) Other operating special items', 'line', 'm1', all=lambda: f'={V("sp_oth")}')
    S('e_nonop', '  (+) Non-operating special items', 'line', 'm1', all=lambda: f'={V("sp_nonop")}')
    S('e_tax', '  (+) Tax impact of special items & discrete and other tax special items', 'line', 'm1', flow=True, labkey='sp_labels', data='sp_tax',
      fc=lambda: f'={V("is_tax")}-{V("e_adjtax")}',
      note='Historical: published adjusted net income − income from continuing operations − pre-tax special items (company lines "Tax impact" and "Discrete tax items" in the cell comments). Forecast: GAAP tax − adjusted tax.')
    S('e_adjni', '  = Adjusted net income (model bridge)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("e_tax")}),{V("e_ni")}+{V("e_restr")}+{V("e_oth")}+{V("e_nonop")}+{V("e_tax")},"")')
    S('e_pubni', '  Company-published adjusted net income (net income excluding special items)', 'memo', 'm1', data='adj_ni_pub', flow=True)
    S('e_sh', '  Diluted shares used by the company for adjusted EPS (m)', 'line', 'm1', data='adj_sh', avg=True,
      hist=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")', fc=lambda: f'={V("sh_dil")}',
      note='Blue = share count printed in the company reconciliation; black = weighted diluted shares.')
    S('e_eps', 'Adjusted EPS – diluted ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted EPS ($)', 'eps_memo', 'ps', data='adj_eps_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.01 rounding; FY2019 ±0.02)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<={0.0201 if CTX.col.year == 2019 else 0.0101},0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_adjebt', '  Adjusted income before income taxes (income before taxes + pre-tax special items)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}+{V("e_restr")}+{V("e_oth")}+{V("e_nonop")},"")')
    S('e_adjtax', '  Adjusted income tax (adjusted income before taxes − adjusted net income)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_adjni")}),ISNUMBER({V("e_adjebt")})),{V("e_adjebt")}-{V("e_adjni")},"")',
      fc=lambda: f'={V("e_adjebt")}*{V("e_rate")}')
    S('e_rate', '  Operational tax rate (adjusted)', 'pct', 'pct', all=ratio('e_adjtax', 'e_adjebt'), qe=lambda: f'={PT("pt_etr")}', ae=lambda: f'={V("is_etr")}',
      note='Company "operational tax rate": 20.3% in 9M 2026. Forecast = GAAP effective tax rate (no special items).')
    S('e_def', '  Definition / basis (company adjusted EPS definition)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Sales y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_ep', '  Engine Products sales y/y %', 'growth', 'pct', all=growth('ep_rev'))
    S('gm_fs', '  Fastening Systems sales y/y %', 'growth', 'pct', all=growth('fs_rev'))
    S('gm_es', '  Engineered Structures sales y/y %', 'growth', 'pct', all=growth('es_rev'))
    S('gm_fw', '  Forged Wheels sales y/y %', 'growth', 'pct', all=growth('fw_rev'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_adjop', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('gm_op', '  Operating income (GAAP) y/y %', 'growth', 'pct', all=growth('is_oi'))
    S('gm_ni', '  Net income y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_adjop_m', '  Adjusted operating income margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_inc', '  Incremental Adjusted EBITDA margin (Δ Adjusted EBITDA / Δ sales)', 'pct', 'pct', all=incr('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating income margin (GAAP) %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_cogs', '  Cost of goods sold % of sales', 'pct', 'pct', all=ratio('is_cogs', 'is_rev'))
    S('gm_sga', '  SG&A % of sales', 'pct', 'pct', all=ratio('is_sga', 'is_rev'))
    S('gm_rd', '  R&D % of sales', 'pct', 'pct', all=ratio('is_rd', 'is_rev'))
    blank()
