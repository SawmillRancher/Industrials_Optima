"""Row specification of the FSS Model sheet, part 1 (MLM template layout and process):
segment build (Environmental Solutions / Safety and Security Systems: orders -> backlog, net sales x segment operating margin; legacy
Fire Rescue / Tool / Federal Signal Technologies groups as reported) -> corporate expenses -> M&A lever -> group total & FY26 guidance
calibration -> cost drivers & adjusting items -> income statement -> GAAP-to-adjusted bridges -> growth & margins."""
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

SEG = [('esg', 'Environmental Solutions', 'ESG'), ('ssg', 'Safety and Security Systems', 'SSG')]
SEGK = [s for s, _, _ in SEG]
LEG = [('frg', 'Fire Rescue (Bronto; discontinued in the FY2015 10-K)'), ('tool', 'Tool (discontinued 2008)'), ('fst', 'Federal Signal Technologies (FSTech; discontinued 2012)')]
OPI = ['d_acq', 'd_restr', 'd_stepup', 'd_oth']

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
    SCEN_ROWS.append((r, 'lev', '  Target net debt / adjusted EBITDA (x) — buybacks plug up to it, 2027E+', *V0['lev'], V0['lev_note']))
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
    S('sec_seg', 'SEGMENT P&L — ENVIRONMENTAL SOLUTIONS · SAFETY AND SECURITY SYSTEMS (orders → backlog; net sales × segment operating margin)', 'section',
      note='SEGMENT BUILD — modelling logic (orders and backlog by group → net sales → segment operating income at the segment margin → + corporate expenses = operating income)')
    blank()
    descr = {'esg': 'Environmental Solutions Group (street sweepers, sewer cleaners, vacuum / hydro-excavation trucks, dump bodies & trailers, refuse trucks, metal-extraction support, road-marking; rental and aftermarket)',
             'ssg': 'Safety and Security Systems Group (public-safety lighting and sirens, outdoor warning systems, industrial signaling)'}
    for s, title, code in SEG:
        S(f'{s}_hdr', descr[s], 'block', note=f'{title.upper()} — modelling logic')
        S(f'{s}_ord', '  Orders', 'line', 'm1', data=f'orders_{s}', flow=True,
          qe=lambda s=s: f'={V(s + "_rev")}*{V(s + "_b2b")}', ae=lambda s=s: f'={V(s + "_rev")}*{V(s + "_b2b")}',
          note=('Group results tables (releases / MD&A). Forecast = net sales × book-to-bill input (backlog roll-forward below).') if s == 'esg' else None)
        S(f'{s}_b2b', '  Book-to-bill (orders ÷ net sales)', 'driver', 'x2', all=ratio(f'{s}_ord', f'{s}_rev'), qe_in=V0['b2b'][s][0], ae_in=V0['b2b'][s][1],
          note=V0['b2b_note'] if s == 'esg' else None)
        S(f'{s}_bl', '  Backlog (period end)', 'line', 'm1', data=f'backlog_{s}',
          qe=lambda s=s: f'={PQ(s + "_bl")}+{V(s + "_ord")}-{V(s + "_rev")}', e26=lambda s=s: f'={QEc(s + "_bl")}',
          ae=lambda s=s: f'={P(s + "_bl")}+{V(s + "_ord")}-{V(s + "_rev")}',
          note='Forecast: opening backlog + orders − net sales (acquired backlog and FX are not modelled).' if s == 'esg' else None)
        S(f'{s}_rev', f'  {title} — net sales', 'line_b', 'm1', data=f'sales_{s}', flow=True,
          qe=lambda s=s: f'={P(s + "_rev")}*(1+{V(s + "_g")})', ae=lambda s=s: f'={P(s + "_rev")}*(1+{V(s + "_g")})',
          note=('Segment note / group results, as reported. Q4/26E: prior-year quarter × (1 + growth); 2027E+: prior year × (1 + scenario lever).') if s == 'esg' else None)
        S(f'{s}_g', '    y/y %', 'growth', 'pct', all=growth(f'{s}_rev'),
          qe=lambda s=s: f'={V(s + "_pre")}+{QEa("cal_g")}',
          ae=lambda s=s, code=code: '=' + CH(SC[f'{code}_G'][CTX.col.year]),
          note='Q4/26E: 9M 2026 y/y growth + sales-guidance calibration Δ (Group block). 2027E–2031E: scenario lever (Bull/Base/Bear table →).' if s == 'esg' else None)
        S(f'{s}_pre', '    Q4/26E growth before calibration (9M 2026 y/y)', 'driver', 'pct', qe=lambda s=s: f'=IFERROR({ACT(s + "_rev")}/{ACT0(s + "_rev")}-1,0)')
        S(f'{s}_mix', '  % of net sales', 'pct', 'pct', all=ratio(f'{s}_rev', 'is_rev'))
        S(f'{s}_oi', f'  {title} — segment operating income', 'line', 'm1', data=f'oi_{s}', flow=True,
          qe=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}', ae=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}',
          note=('Segment operating income as reported (after amortization of acquired intangibles and the segment\'s acquisition costs). Forecast = net sales × margin.') if s == 'esg' else None)
        S(f'{s}_m', '  Segment operating margin %', 'pct', 'pct', all=ratio(f'{s}_oi', f'{s}_rev'),
          qe=lambda s=s: f'={V(s + "_mpre")}+{QEa("cal_m")}', ae=lambda s=s, code=code: '=' + CH(SC[f'{code}_M'][CTX.col.year]),
          note='Q4/26E: margin before calibration + adjusted-EPS-guidance calibration Δ (Group block). 2027E+: scenario lever.' if s == 'esg' else None)
        S(f'{s}_mpre', '  Q4/26E margin before EPS calibration (prior-year quarter + 9M 2026 y/y change)', 'driver', 'pct',
          qe=lambda s=s: f'={P(s + "_m")}+IFERROR({ACT(s + "_oi")}/{ACT(s + "_rev")}-{ACT0(s + "_oi")}/{ACT0(s + "_rev")},0)')
        S(f'{s}_inc', '  Incremental segment margin (Δ operating income / Δ net sales)', 'pct', 'pct', all=incr(f'{s}_oi', f'{s}_rev'))
        S(f'{s}_aeb', f'  Memo: {title} adjusted EBITDA as published (from 2017)', 'memo', 'm1', data=f'adj_ebitda_{s}', flow=True)
        S(f'{s}_aebm', '    Adjusted EBITDA margin % (published)', 'pct', 'pct', hist=ratio(f'{s}_aeb', f'{s}_rev'))
        S(f'{s}_da', f'  Memo: {title} depreciation & amortization', 'memo', 'm1', data=f'da_{s}', flow=True)
        blank()
    S('leg_hdr', 'Legacy groups (as originally reported until each was discontinued; included in the group totals)', 'block',
      note='LEGACY GROUPS — history only (sold / discontinued; no forecast)')
    for s, lab in LEG:
        S(f'{s}_rev', f'  {lab} — net sales', 'memo', 'm1', data=f'sales_{s}', flow=True)
        S(f'{s}_oi', f'  {lab} — operating income', 'memo', 'm1', data=f'oi_{s}', flow=True)
    blank()
    S('co_hdr', 'Corporate (corporate expenses and items not allocated to the groups)', 'block',
      note='CORPORATE — operating income − Σ group operating income (derived; checked against the published corporate line where shown)')
    S('corp', '  Corporate expenses & eliminations (derived: operating income − Σ group operating income)', 'line', 'm1', data='corp', flow=True,
      qe=lambda: f'=AVERAGE({Q1}{R["corp"]}:{Q3}{R["corp"]})', ae=lambda: f'={V("g_rev")}*{V("corp_pct")}',
      note=('2024+ derived (the segment note no longer shows a corporate line); includes corporate acquisition & integration costs (2025: New Way). '
            'Q4/26E: Q1–Q3 2026 average (Q4-25 included $13.3m of New Way acquisition costs). 2027E+: % of net sales.'))
    S('corp_g', '  Corporate y/y %', 'growth', 'pct', all=growth('corp'))
    S('corp_pct', '  Corporate % of net sales', 'pct', 'pct', all=ratio('corp', 'is_rev'), ae_in=V0['corp_pct'])
    S('corp_pub', '  Memo: corporate expenses as published (segment note / release text)', 'memo', 'm1', hist=lambda: f'=IF(ISNUMBER({V("corp_pubd")}),{V("corp_pubd")},"")')
    S('corp_pubd', '  Memo: corporate line in the segment note (to 2023)', 'memo', 'm1', data='corp_pub', flow=True)
    S('corp_chk', '  Check: derived vs published corporate line (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("corp_pubd")}),IF(ABS({V("corp")}-{V("corp_pubd")})<=0.15,0,ROUND({V("corp")}-{V("corp_pubd")},1)),"")')
    blank()
    S('mx_hdr', 'Mix & contribution to growth (outputs)', 'block', note='MIX — outputs')
    S('gc_esg', '  Contribution to net sales growth — Environmental Solutions (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("esg_rev")}-{P("esg_rev")})/{P("g_rev")},"")' if CTX.col.prior else None))
    S('gc_ssg', '  Contribution to net sales growth — Safety and Security Systems (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("ssg_rev")}-{P("ssg_rev")})/{P("g_rev")},"")' if CTX.col.prior else None))
    S('gc_oth', '  Contribution to net sales growth — legacy groups & acquisitions lever (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("g_rev")}-{V("esg_rev")}-{V("ssg_rev")}-({P("g_rev")}-{P("esg_rev")}-{P("ssg_rev")}))/{P("g_rev")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — specialty-vehicle / aftermarket bolt-ons, unallocated; deals closed from 2027E)', 'block',
      note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=1.6, e26_in=0.0,
      note='New Way $414m for ~$249m 2024 revenue (~1.7x); Mega $45m for ~$40m 2024 sales (~1.1x); Hog $95m incl. earn-out for $66m 2025 sales (~1.4x). 1.6x input (assumption).')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.05)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}',
      note='Mid-year convention.')
    S('m_m', '  Operating margin of acquired businesses (after amortization) %', 'driver', 'pct', e26_in=0.0, ae_in=0.14)
    S('m_oi', '  Operating income from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.10)
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.38,
      note='PPAs: New Way 39% of consideration in intangibles (customer relationships + trade names), Hog 41%, Mega 41%.')
    S('m_life', '  Definite-lived intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=14)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (inside segment operating income)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(0.7*({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)',
      note='70% of acquired intangibles assumed definite-lived (New Way: customer relationships $111m of $161.5m; trade names indefinite).')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group Total — net sales & operating income (segment build) → FY26 guidance calibration', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Net sales (segment build)', 'total', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("esg_rev")}),{nsum(["esg_rev", "ssg_rev", "frg_rev", "tool_rev", "fst_rev"])},{V("is_rev")})',
      fc=lambda: f'={V("esg_rev")}+{V("ssg_rev")}+N({V("m_rev")})',
      note='Σ groups (incl. legacy groups as reported) + future acquisitions from 2027E.')
    S('g_rev_g', '  Net sales y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs consolidated net sales (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=0.15,0,ROUND({V("g_rev")}-{V("is_rev")},1)),"")')
    S('g_oi', 'Operating income (segment build)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("esg_oi")}),{nsum(["esg_oi", "ssg_oi", "frg_oi", "tool_oi", "fst_oi"])}+{V("corp")}+N({V("m_oi")}),"")',
      note='Σ group operating income + corporate (+ future acquisitions). Drives the GAAP P&L below.')
    S('g_oim', '  Operating margin %', 'pct', 'pct', all=ratio('g_oi', 'g_rev'))
    S('g_chk_oi', '  Check: segment build vs consolidated operating income (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_oi")}),ISNUMBER({V("is_oi")})),IF(ABS({V("g_oi")}-{V("is_oi")})<=0.15,0,ROUND({V("g_oi")}-{V("is_oi")},1)),"")')
    S('cal_guid', '  Memo: FY26 net sales guidance (scenario end-point)', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_rev']), note=V0['rev_guid_note'])
    S('cal_pre', '  Net sales before calibration (Q4/26E helper)', 'line', 'm1', qe=lambda: '=' + '+'.join(f'{P(s + "_rev")}*(1+{V(s + "_pre")})' for s in SEGK))
    S('cal_sens', '  Net sales sensitivity to +1.00 of growth (Q4/26E helper)', 'line', 'm1', qe=lambda: '=' + '+'.join(P(s + '_rev') for s in SEGK))
    S('cal_g', '  Guidance calibration: Δ y/y growth applied to both groups (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_guid", E26)}-{ACT("g_rev")}-{V("cal_pre")})/{V("cal_sens")}',
      note='Solves the uniform growth shift (vs 9M 2026 y/y rates) so that FY26 net sales = the guidance end-point for the active scenario.')
    S('cal_rev_chk', '  Check: FY26 net sales vs guidance end-point (should be 0)', 'check', 'm1', e26=lambda: f'=ROUND({V("g_rev")}-{V("cal_guid")},1)')
    S('cal_eps', '  Memo: FY26 adjusted EPS guidance (scenario end-point, $)', 'eps_memo', 'ps', e26=lambda: '=' + CH(SC['out_eps']), note=V0['eps_guid_note'])
    S('cal_ni', '  Adjusted net income required (FY26E diluted shares × EPS guidance)', 'memo_calc', 'm1', e26=lambda: f'={V("cal_eps")}*{V("e_sh")}')
    S('cal_oi', '  Q4/26E operating income required ((NI − 9M) ÷ (1 − tax) − adjusting items + interest + other expense)', 'memo_calc', 'm1',
      e26=lambda: f'=({V("cal_ni")}-{ACT("e_adjni")})/(1-{PT("pt_etr")})-{QEc("e_pre")}+{QEc("is_int")}+{QEc("is_nonop")}')
    S('cal_oi_pre', '  Operating income before margin calibration (Q4/26E helper)', 'line', 'm1',
      qe=lambda: '=' + '+'.join(f'{V(s + "_rev")}*{V(s + "_mpre")}' for s in SEGK) + f'+{V("corp")}')
    S('cal_segrev', '  Group net sales (Q4/26E helper)', 'line', 'm1', qe=lambda: '=' + '+'.join(V(s + '_rev') for s in SEGK))
    S('cal_m', '  Guidance calibration: Δ segment operating margin (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_oi", E26)}-{V("cal_oi_pre")})/{V("cal_segrev")}',
      note='Solves the uniform segment-margin shift so that FY26 adjusted EPS = the guidance end-point for the active scenario.')
    S('cal_eps_chk', '  Check: FY26 adjusted EPS vs guidance end-point (should be 0.00)', 'check', 'ps', e26=lambda: f'=ROUND({V("e_eps")}-{V("cal_eps")},2)')
    S('cal_capex', '  Memo: FY26 capital expenditures guidance (FY25 release; scenario end-point) — information', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_capex']))
    S('cal_capex_d', '    Model FY26 capex − guidance (information)', 'memo_calc', 'm1', e26=lambda: f'=-{V("cf_capex")}-{V("cal_capex")}')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A & adjusting items', 'block', note='COST DRIVERS — inputs that drive forecast cost lines (Q4/26E: point estimates; 2027E+: % of sales or schedules)')
    S('d_dda', '  Depreciation & amortization (total, cash-flow statement; incl. rental fleet)', 'line', 'm1', data='cf_dda', flow=True,
      qe=lambda: f'={PT("pt_dda")}', ae=lambda: f'={V("g_rev")}*{V("d_dda_pct")}+N({V("m_amort")})',
      note='As in the company adjusted EBITDA reconciliation (= cash-flow statement D&A). Q4/26E point estimate; 2027E+: % of net sales + future-acquisition amortization.')
    S('d_dda_pct', '  D&A % of net sales (ex future acquisitions)', 'pct', 'pct', all=ratio('d_dda', 'is_rev'), ae_in=V0['dda_pct'])
    S('d_amort', '  Amortization of acquired intangibles (separate IS line from 2021; inside SEG&A before)', 'line', 'm1', data='amort', flow=True,
      qe=lambda: f'={PT("pt_amort")}', ae=lambda: f'={V("d_amort_sch")}+N({V("m_amort")})',
      note='Q4/26E: Q3-26 10-Q estimate ($6.7m remaining 2026, before GVS). 2027E+: schedule for intangibles held at 30-Sep-2026 + future-acquisition amortization.')
    S('d_amort_sch', '  Amortization schedule — intangibles held at 30-Sep-2026 (10-Q, input)', 'driver', 'm1', ae_in=V0['amort_sched'], note=V0['amort_note'])
    S('d_sga', '  SEG&A % of net sales', 'pct', 'pct', all=ratio('is_sga', 'is_rev'),
      qe=lambda: f'={P("d_sga")}+IFERROR({ACT("is_sga")}/{ACT("is_rev")}-{ACT0("is_sga")}/{ACT0("is_rev")},0)', ae_in=V0['sga_pct'],
      note='Q4/26E: prior-year quarter ratio + 9M 2026 y/y drift; 2027E+ input. Gross profit is implied: operating income (segment build) + operating costs.')
    S('d_sbc', '  Stock-based compensation (cash-flow statement)', 'line', 'm1', data='cf_sbc', flow=True,
      qe=lambda: f'={P("d_sbc")}*(1+IFERROR({ACT("d_sbc")}/{ACT0("d_sbc")}-1,0))', ae=lambda: f'={V("g_rev")}*{V("d_sbc_pct")}',
      note='Q4/26E: prior-year quarter × 9M 2026 y/y; 2027E+: % of net sales. Federal Signal does not adjust out stock-based compensation.')
    S('d_sbc_pct', '  Stock-based compensation % of net sales', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_nonop', '  Other expense, net & non-operating charges (input; + = expense)', 'line', 'm1', data='nonop', flow=True, qe=lambda: f'={PT("pt_nonop")}', ae_in=V0['nonop'],
      note='Other expense / (income), net (non-service pension cost, FX), plus pension / debt settlement charges and (to 2010) the joint-venture loss; derived as operating income − interest − earnings before tax.')
    S('d_adj_h', '  Adjusting items in operating income (company adjusted-EBITDA reconciliation; forecast inputs):', 'sub', 'gen')
    S('d_acq', '  Acquisition & integration-related expenses, net (incl. contingent-consideration remeasurement)', 'line', 'm1', data='oa_acq', flow=True, labkey='oa_acq_lab',
      qe=lambda: f'={PT("pt_acq")}', ae=lambda: f'={V("m_spend")}*{V("d_acq_pct")}')
    S('d_acq_pct', '  Acquisition & integration costs % of acquisition spend', 'pct', 'pct', ae_in=0.02)
    S('d_restr', '  Restructuring & executive severance', 'line', 'm1', data='oa_restr', flow=True, labkey='oa_restr_lab', fc=lambda: '=0')
    S('d_stepup', '  Purchase accounting effects (inventory / rental-equipment step-up, ex the part in D&A)', 'line', 'm1', data='oa_stepup', flow=True, labkey='oa_stepup_lab',
      qe=lambda: f'={PT("pt_stepup")}', ae_in=0.0)
    S('d_oth', '  Other items (coronavirus costs, hearing-loss settlement, environmental remediation, discontinued-business legal costs, operating pension settlement)', 'line', 'm1',
      data='oa_other', flow=True, labkey='oa_other_lab', fc=lambda: '=0')
    S('d_items', '  Total adjusting items in operating income', 'line_b', 'm1', all=lambda: f'={nsum(OPI)}')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF OPERATIONS (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (operating income from the segment build; gross profit implied)')
    S('is_rev', 'Net sales', 'total', 'm1', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the segment build.')
    S('is_cogs', 'Cost of sales', 'line', 'm1', data='cogs', flow=True, fc=lambda: f'={V("is_rev")}-{V("is_gp")}')
    S('is_gp', 'Gross profit', 'line_b', 'm1', hist=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_rev")}-{V("is_cogs")},"")',
      fc=lambda: f'={V("is_oi")}+{V("is_sga")}+{V("is_amort")}+{V("is_acq")}+{V("is_restr")}+{V("is_opx")}',
      note='Forecast = operating income + operating expenses (implied by the segment build).')
    S('is_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('is_sga', 'Selling, engineering, general & administrative expenses', 'line', 'm1', data='sga', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_sga")}')
    S('is_amort', 'Amortization expense (separate line from 2021)', 'line', 'm1', data='amort', flow=True, fc=lambda: f'={V("d_amort")}')
    S('is_acq', 'Acquisition & integration-related expenses, net', 'line', 'm1', data='acq', flow=True, fc=lambda: f'={V("d_acq")}')
    S('is_restr', 'Restructuring charges', 'line', 'm1', data='restr', flow=True, fc=lambda: f'={V("d_restr")}')
    S('is_opx', 'Other operating items (impairment, operating pension settlement, gain on product-line sale; derived)', 'line', 'm1', data='opx_oth', flow=True, labkey='opx_lab',
      fc=lambda: '=0', note='Derived: gross profit − SEG&A − amortization − acquisition costs − restructuring − operating income (labels in the cell comments).')
    S('is_oi', 'Operating income', 'total', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_gp")}),{V("is_gp")}-{V("is_sga")}-{V("is_amort")}-{V("is_acq")}-{V("is_restr")}-{V("is_opx")},"")',
      fc=lambda: f'={V("g_oi")}', note='Forecast = segment build.')
    S('is_oi_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('is_oi_pub', '  Memo: operating income as reported', 'memo', 'm1', data='oi', flow=True)
    S('is_oi_chk', '  Check: model vs reported operating income (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_oi_pub")}),IF(ABS({V("is_oi")}-{V("is_oi_pub")})<=0.15,0,ROUND({V("is_oi")}-{V("is_oi_pub")},1)),"")')
    S('is_int', 'Interest expense, net', 'line', 'm1', data='int', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'={P("ds_tl")}*{V("ds_r_tl")}+{P("ds_rev")}*{V("ds_r_rev")}+{V("ds_fees")}-{P("cf_end")}*{V("ds_r_cash")}',
      note='Q4/26E point estimate. 2027E+ = rate × opening term loan + rate × opening revolver + fees − yield on opening cash (no circularity).')
    S('is_nonop', 'Other expense, net & non-operating charges (+ = expense; derived)', 'line', 'm1', fc=lambda: f'={V("d_nonop")}',
      hist=lambda: f'={V("d_nonop")}')
    S('is_ebt', 'Income from continuing operations before income taxes', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_oi")}),{V("is_oi")}-{V("is_int")}-{V("is_nonop")},"")')
    S('is_tax', 'Income tax expense (derived: pre-tax income − continuing income)', 'line', 'm1', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Q4/26E: point estimate (9M 2026 GAAP 23.5%, adjusted 23.5%). 2027E+: input.')
    S('is_cont', 'Income from continuing operations', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_disc', 'Discontinued operations, net of tax (Tool 2008, FSTech 2012, Fire Rescue 2015-16 and others)', 'line', 'm1', data='disc', flow=True, fc=lambda: '=0')
    S('is_ni', 'Net income', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_cont")}),{V("is_cont")}+N({V("is_disc")}),"")')
    S('is_ni_chk', '  Check: net income vs reported (should be 0; ±0.1 rounding)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=0.15,0,ROUND({V("is_ni")}-{V("is_ni_pub")},1)),"")')
    S('is_ni_pub', '  Memo: net income as reported', 'memo', 'm1', data='ni', flow=True)
    S('is_dda', '  Memo: depreciation & amortization (total)', 'memo_calc', 'm1', all=lambda: f'={V("d_dda")}')
    S('is_sbc', '  Memo: stock-based compensation', 'memo_calc', 'm1', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share — Federal Signal common stock)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={B1("bs_shares")}-${E26}${R["bb_sh"]}*0.5+${E26}${R["bb_iss"]}*0.5',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q4/26E: shares outstanding at 30-Sep-2026 − Q4 buybacks (mid-quarter) + equity-plan issuance. 2027E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")',
      note='Net income / weighted diluted shares (±$0.015 vs reported; 2006–2011 basic = diluted).')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.015 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0151,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('eps_cont', '  Memo: EPS – diluted, continuing operations as reported ($)', 'eps_memo', 'ps', data='eps_dc', fc=lambda: f'={V("eps_dil")}')
    S('dps', '  Cash dividends declared per share ($)', 'line', 'ps', data='dps', flow=True, qe_in=V0['dps_q'],
      ae=lambda: f'={P("dps")}*(1+{V("dps_g")})', note='Quarterly dividend $0.15 (Q1–Q3 2026; similar dividend announced for Q4). 2027E+: prior year × (1 + growth).')
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'])
    blank()

    # ------------------------------------------------------------------ RECON 1: net income -> EBITDA -> adjusted EBITDA
    S('sec_r1', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (company definition, as published)', 'section',
      note='ADJUSTED EBITDA — net income + interest + other expense / settlement charges + income tax + D&A + acquisition / integration, restructuring, purchase accounting and other items (company reconciliation)')
    S('r_ni', 'Net income (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('r_disc', '  (−) Discontinued operations, net of tax', 'line', 'm1', all=lambda: f'=-N({V("is_disc")})')
    S('r_int', '  (+) Interest expense, net', 'line', 'm1', all=lambda: f'={V("is_int")}')
    S('r_nonop', '  (+) Other expense, net & pension / debt settlement charges', 'line', 'm1', all=lambda: f'={V("is_nonop")}')
    S('r_tax', '  (+) Income tax expense', 'line', 'm1', all=lambda: f'={V("is_tax")}')
    S('r_oi', '  = Operating income', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_disc")}+{V("r_int")}+{V("r_nonop")}+{V("r_tax")},"")')
    S('r_dda', '  (+) Depreciation & amortization', 'line', 'm1', all=lambda: f'={V("d_dda")}')
    S('r_ebitda', '  = EBITDA', 'line_b', 'm1', all=lambda: f'=IF(AND(ISNUMBER({V("r_oi")}),ISNUMBER({V("r_dda")})),{V("r_oi")}+{V("r_dda")},"")')
    S('r_items', '  (+) Adjusting items in operating income (cost-driver block)', 'line', 'm1', all=lambda: f'={V("d_items")}')
    S('r_adj', '  = Adjusted EBITDA', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{V("r_ebitda")}+{V("r_items")},"")',
      note='Company definition (published quarterly from Q1-17; annually from FY2013 in the leverage tables; model = EBITDA before). Used for leverage and EV / EBITDA.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_pub', '  Company-published adjusted EBITDA', 'memo', 'm1', data='ebitda_pub', flow=True)
    S('r_chk', '  Check: model vs company-published adjusted EBITDA (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("r_pub")}),ISNUMBER({V("r_adj")})),IF(ABS({V("r_adj")}-{V("r_pub")})<=0.15,0,ROUND({V("r_adj")}-{V("r_pub")},1)),"n/p")')
    S('r_def', '  Definition / basis (company adjusted EBITDA definition in force)', 'text', 'gen',
      note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    blank()

    # ------------------------------------------------------------------ RECON 2: operating income -> adjusted EBIT
    S('sec_r2', 'RECONCILIATION: OPERATING INCOME → ADJUSTED EBIT (model definition; Federal Signal publishes no adjusted operating income)', 'section',
      note='ADJUSTED EBIT — operating income + the company\'s adjusting items in operating income (= adjusted EBITDA − D&A); full-cost (after amortization) for NOPAT, ROIC and the DCF')
    S('o_oi', 'Operating income (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_oi")}')
    S('o_items', '  (+) Adjusting items in operating income', 'line', 'm1', all=lambda: f'={V("d_items")}')
    S('r_ebit', '  = Adjusted EBIT (model; full-cost, after amortization)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_oi")}),{V("o_oi")}+{V("o_items")},"")')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('o_chk', '  Check: adjusted EBIT = adjusted EBITDA − D&A (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_ebit")}),ISNUMBER({V("r_adj")})),ROUND({V("r_ebit")}-({V("r_adj")}-{V("d_dda")}),1),"")')
    S('o_ebita', '  Memo: adjusted EBITA (adjusted EBIT + amortization of acquired intangibles; amortization separate from 2021)', 'memo_calc', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_ebit")}),{V("r_ebit")}+N({V("is_amort")}),"")')
    S('r_cash', '  Memo: cash adjusting items (acquisition, restructuring and other items; deducted in the DCF)', 'memo_calc', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("d_acq")}),{V("d_acq")}+{V("d_restr")}+{V("d_oth")},"")')
    S('o_inc', '  Incremental adjusted EBIT margin (Δ adjusted EBIT / Δ net sales)', 'pct', 'pct', all=incr('r_ebit', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: INCOME FROM CONTINUING OPERATIONS → ADJUSTED NET INCOME → ADJUSTED EPS (company definition)', 'section',
      note='ADJUSTED EPS — continuing income + income tax = pre-tax income; + pre-tax adjusting items = adjusted pre-tax income; − adjusted income tax (derived from the published adjusted net income; excludes special tax items) = adjusted net income')
    S('e_cont', 'Income from continuing operations (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_cont")}')
    S('e_taxadd', '  (+) Income tax expense', 'line', 'm1', all=lambda: f'={V("is_tax")}')
    S('e_ebt', '  = Income before income taxes', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("e_cont")}),{V("e_cont")}+{V("e_taxadd")},"")')
    S('e_pre', '  (+) Pre-tax adjusting items (acquisition / integration, restructuring, purchase accounting incl. D&A step-up, pension / debt settlement, other)', 'line', 'm1',
      data='e_preitems', flow=True, fc=lambda: f'={V("d_items")}')
    S('e_adjebt', '  = Adjusted income before income taxes', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("e_ebt")}),{V("e_ebt")}+{V("e_pre")},"")')
    S('e_net', '  (+) Items shown net of tax (2013 releases: debt settlement, restructuring, special tax items, tax planning benefits)', 'line', 'm1', data='e_netitems', flow=True,
      fc=lambda: '=0')
    S('e_adjtax', '  (−) Adjusted income tax expense (historical: derived = adjusted pre-tax income + net items − published adjusted net income)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("e_pubni")}),{V("e_adjebt")}+N({V("e_net")})-{V("e_pubni")},IF(ISNUMBER({V("e_ebt")}),{V("e_taxadd")},""))',
      fc=lambda: f'={V("e_adjebt")}*{V("e_rate")}')
    S('e_adjni', '  = Adjusted net income (model bridge)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("e_adjtax")}),{V("e_adjebt")}+N({V("e_net")})-{V("e_adjtax")},"")',
      note='Periods without a published adjusted EPS (2006–2012) show continuing income (adjusted = GAAP, flagged in the definition row).')
    S('e_pubni', '  Company-published adjusted net income (Q1–Q3/13: adjusted EPS × diluted shares)', 'memo', 'm1', data='adj_ni_pub', flow=True)
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted EPS – diluted ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted EPS ($)', 'eps_memo', 'ps', data='e_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.015 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0151,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_rate', '  Adjusted effective tax rate', 'pct', 'pct', all=ratio('e_adjtax', 'e_adjebt'), qe=lambda: f'={PT("pt_etr")}', ae=lambda: f'={V("is_etr")}',
      note='9M 2026 adjusted rate 23.5%. Forecast = GAAP effective tax rate.')
    S('e_def', '  Definition / basis (company adjusted EPS definition)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Net sales y/y % (vs prior period as reported)', 'growth', 'pct', all=growth('is_rev'))
    S('gm_rev_cmp', '  Net sales y/y % vs the prior-year comparative in this period\'s filing (like-for-like across discontinued operations)', 'growth', 'pct',
      hist=lambda: f'=IF(ISNUMBER({V("rev_cmp")}),IFERROR({V("is_rev")}/{V("rev_cmp")}-1,""),"")')
    S('rev_cmp', '  Memo: prior-year net sales as presented in this period\'s filing', 'memo', 'm1', data='rev_cmp', flow=True)
    S('gm_esg', '  Environmental Solutions net sales y/y %', 'growth', 'pct', all=growth('esg_rev'))
    S('gm_ssg', '  Safety and Security Systems net sales y/y %', 'growth', 'pct', all=growth('ssg_rev'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating income y/y %', 'growth', 'pct', all=growth('is_oi'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('gm_adj_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('gm_inc', '  Incremental adjusted EBIT margin (Δ adjusted EBIT / Δ net sales)', 'pct', 'pct', all=incr('r_ebit', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_sga', '  SEG&A % of net sales', 'pct', 'pct', all=ratio('is_sga', 'is_rev'))
    blank()
