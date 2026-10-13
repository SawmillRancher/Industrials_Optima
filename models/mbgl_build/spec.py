"""Row specification of the Mobility Global Model sheet, part 1 (MLM template layout and process):
segment build (CARFAX / B2B / Corporate: revenue × Segment Adjusted EBITDA margin) -> S&P Global Mobility segment memo and
spliced revenue history -> group total & FY26 outlook calibration -> M&A lever -> cost drivers -> income statement ->
GAAP-to-adjusted bridges -> growth & margins."""
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
def Q3v(key): return f'${Q3}${R[key]}'
YRS = list(range(FYC + 1, FYL + 1))
SEGS = [('cfx', 'CARFAX', 'CFX'), ('b2b', 'B2B (automotiveMastermind, Polk Automotive Solutions, Market Scan, OEM & supplier data)', 'B2B')]

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
    SCEN_ROWS.append((r, 'pt_hdr', 'FY26 point estimates (all cases; not guided — assumptions unless stated)', None, None, None, None)); r += 1
    for key, lab, vals, nf, note in V0['points']:
        SC[key] = r
        if isinstance(vals, tuple): SCEN_ROWS.append((r, 'out', lab, vals[0], vals[1], vals[2], note, nf))
        else: SCEN_ROWS.append((r, 'pt', lab, None, vals, None, note, nf))
        r += 1
    r += 1
    SC['LEV'] = r
    SCEN_ROWS.append((r, 'lev', '  Target net debt / Adjusted EBITDA (x) — buyback plug 2027E+', *V0['lev'], V0['lev_note']))
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
    # ------------------------------------------------------------------ SEGMENT BUILD
    S('sec_seg', 'SEGMENT P&L — CARFAX · B2B · CORPORATE (revenue × Segment Adjusted EBITDA margin)', 'section',
      note='SEGMENT BUILD — modelling logic (segment revenue → Segment Adjusted EBITDA margin → Adjusted EBITDA → GAAP P&L). Carve-out basis to 30-Jun-2026; consolidated from Q3-26.')
    blank()
    for k, title, code in SEGS:
        S(f'{k}_hdr', title, 'block', note=f'{code} — modelling logic')
        S(f'{k}_rev', '  Segment revenue', 'line_b', 'm', data=f'{k}_rev', flow=True,
          qe=lambda k=k: f'={P(k + "_rev")}*(1+{V(k + "_g")})', ae=lambda k=k: f'={P(k + "_rev")}*(1+{V(k + "_g")})',
          note=('Carve-out segment revenue as published (Form 10 MD&A FY2023–25, Q1-25 / Q1-26; 10-Q / release Q2; FY2025 quarterly data Ex. 99.2 for Q3-25 / Q4-25). '
                'Q3/Q4-26E: prior-year quarter × (1 + growth). 2027E+: prior year × (1 + scenario lever).') if k == 'cfx' else None)
        S(f'{k}_g', '    y/y %', 'growth', 'pct', all=growth(f'{k}_rev'),
          qe=lambda k=k: f'={V(k + "_pre")}+{Q3v("cal_g")}', ae=lambda k=k, code=code: '=' + CH(SC[f'{code}_G'][CTX.col.year]),
          note='Q3/Q4-26E: growth before calibration (row below) + revenue-outlook calibration Δ (Group block). 2027E–2031E: scenario lever.' if k == 'cfx' else None)
        S(f'{k}_pre', '    Q3/Q4-26E growth before revenue calibration (1H/26 y/y)', 'driver', 'pct',
          qe=lambda k=k: f'=IFERROR({H1(k + "_rev")}/{H1(k + "_rev", 2025)}-1,0)')
        S(f'{k}_sub', '    Subscription revenue', 'line', 'm', data=f'{k}_sub', flow=True)
        S(f'{k}_nsub', '    Non-subscription revenue', 'line', 'm', data=f'{k}_nsub', flow=True)
        S(f'{k}_subp', '    Subscription % of segment revenue', 'pct', 'pct', all=ratio(f'{k}_sub', f'{k}_rev'))
        S(f'{k}_intl', '    International revenue (memo)', 'memo', 'm', data=f'{k}_intl', flow=True)
        S(f'{k}_adj', '  Segment Adjusted EBITDA', 'line_b', 'm', data=f'{k}_adj', flow=True,
          qe=lambda k=k: f'={V(k + "_rev")}*{V(k + "_m")}', ae=lambda k=k: f'={V(k + "_rev")}*{V(k + "_m")}',
          note='Company measure: segment operating profit + D&A + SBC + transaction costs + severance & other. Forecast = revenue × margin.' if k == 'cfx' else None)
        S(f'{k}_m', '    Segment Adjusted EBITDA margin %', 'pct', 'pct', all=ratio(f'{k}_adj', f'{k}_rev'),
          qe=lambda k=k: f'={V(k + "_m_pre")}+{Q3v("cal_m")}', ae=lambda k=k, code=code: '=' + CH(SC[f'{code}_M'][CTX.col.year]),
          note='Q3/Q4-26E: margin before calibration + Adjusted-EBITDA-outlook calibration Δ. 2027E–2031E: scenario lever.' if k == 'cfx' else None)
        S(f'{k}_m_pre', '    Q3/Q4-26E margin before calibration (prior-year quarter + 1H/26 y/y drift)', 'driver', 'pct',
          qe=lambda k=k: f'={P(k + "_m")}+({H1(k + "_adj")}/{H1(k + "_rev")}-{H1(k + "_adj", 2025)}/{H1(k + "_rev", 2025)})')
        S(f'{k}_op', '  Segment operating profit (GAAP)', 'memo', 'm', data=f'{k}_op', flow=True)
        S(f'{k}_da', '    Segment D&A (memo)', 'memo', 'm', data=f'{k}_da', flow=True)
        S(f'{k}_sbc', '    Segment stock-based compensation (memo)', 'memo', 'm', data=f'{k}_sbc', flow=True)
        S(f'{k}_items', '    Segment transaction costs, severance & other items (memo)', 'memo', 'm', data=f'{k}_items', flow=True)
        S(f'{k}_chk', '  Check: segment OP + D&A + SBC + items vs Segment Adjusted EBITDA (should be 0; ±1 rounding)', 'check', 'm',
          hist=lambda k=k: (f'=IF(AND(ISNUMBER({V(k + "_op")}),ISNUMBER({V(k + "_adj")})),IF(ABS({V(k + "_op")}+{V(k + "_da")}+N({V(k + "_sbc")})+N({V(k + "_items")})'
                            f'-{V(k + "_adj")})<=1,0,{V(k + "_op")}+{V(k + "_da")}+N({V(k + "_sbc")})+N({V(k + "_items")})-{V(k + "_adj")}),"")'))
        S(f'{k}_adjop', '  Segment Adjusted operating profit (company; Form 10 periods)', 'memo', 'm', data=f'{k}_adjop', flow=True)
        blank()
    S('corp_hdr', 'Corporate (unallocated expense: corporate functions, select initiatives, unoccupied space; separation costs)', 'block',
      note='CORPORATE — modelling logic (carve-out allocations to 30-Jun-2026; standalone public-company costs from Q3-26)')
    S('corp_op', '  Corporate operating profit (GAAP)', 'memo', 'm', data='corp_op', flow=True)
    S('corp_items', '    Corporate transaction costs, severance & other items (memo)', 'memo', 'm', data='corp_items', flow=True)
    S('corp_adj', '  Corporate Adjusted EBITDA', 'line_b', 'm', data='corp_adj', flow=True, qe_in=V0['corp_q'],
      ae=lambda: f'={V("g_rev")}*{V("corp_pct")}', note=V0['corp_note'])
    S('corp_pct', '    Corporate Adjusted EBITDA % of revenue', 'pct', 'pct', all=ratio('corp_adj', 'g_rev'), ae_in=V0['corp_pct'],
      note='2027E+: input (assumption) — full-year standalone corporate cost base.')
    blank()

    # ------------------------------------------------------------------ S&P GLOBAL MOBILITY SEGMENT (memo) + spliced revenue
    S('sp_hdr', 'S&P Global "Mobility" segment as reported by the former parent (memo; S&P Global CIK 64040) — revenue comparable, profit not', 'block',
      note=('S&P GLOBAL MOBILITY SEGMENT — memo. Fills the pre-2025 quarters the carve-out never published. Revenue ties to the carve-out within $0–4m '
            '(≤0.25%) in every overlapping period → spliced revenue history below. Profit is NOT comparable: S&P Global segment results exclude '
            'corporate allocations and stand-up costs, and carry S&P Global\'s deal amortization ($303m vs $296m).'))
    S('sp_rev', '  S&P Global Mobility revenue (2022 = S&P Global non-GAAP pro forma, full year)', 'memo', 'm', data='sp_rev', flow=True)
    S('sp_rev_g', '    y/y %', 'growth', 'pct', all=growth('sp_rev'))
    S('sp_sub', '    Subscription revenue', 'memo', 'm', data='sp_sub', flow=True)
    S('sp_nsub', '    Non-subscription revenue', 'memo', 'm', data='sp_nsub', flow=True)
    S('sp_op', '  S&P Global Mobility operating profit (GAAP segment; 2022 pro forma)', 'memo', 'm', data='sp_op', flow=True)
    S('sp_ngadj', '    + Non-GAAP adjustments (excl. deal amortization)', 'memo', 'm', data='sp_ng_adj', flow=True)
    S('sp_amort', '    + Deal-related amortization', 'memo', 'm', data='sp_amort', flow=True)
    S('sp_adjop', '  S&P Global Mobility adjusted operating profit', 'memo', 'm', data='sp_adj_op', flow=True)
    S('sp_adjop_m', '    Adjusted operating margin %', 'pct', 'pct', all=ratio('sp_adjop', 'sp_rev'))
    S('sp_chk', '  Check: S&P Global OP + adjustments + amortization vs adjusted OP (should be 0; ±1 S&P Global rounding)', 'check', 'm',
      hist=lambda: (f'=IF(AND(ISNUMBER({V("sp_ngadj")}),ISNUMBER({V("sp_adjop")})),IF(ABS({V("sp_op")}+{V("sp_ngadj")}+{V("sp_amort")}-{V("sp_adjop")})<=1,0,'
                    f'{V("sp_op")}+{V("sp_ngadj")}+{V("sp_amort")}-{V("sp_adjop")}),"")'))
    S('sp_dr', '  Basis difference: carve-out revenue − S&P Global segment revenue (information)', 'memo_calc', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("is_rev")}),ISNUMBER({V("sp_rev")})),{V("is_rev")}-{V("sp_rev")},"")',
      note='Carve-out revenue exceeds the S&P Global segment by $0–4m (FY23 +1, FY24 +4, FY25 +3; Q4-25 +2): rounding and minor intercompany items.')
    S('sp_dr_p', '    as % of revenue', 'pct', 'pct', hist=lambda: f'=IF(ISNUMBER({V("sp_dr")}),{V("sp_dr")}/{V("is_rev")},"")')
    S('sp_dop', '  Carve-out segment Adjusted OP (CARFAX + B2B, before corporate) − S&P Global adjusted OP (information)', 'memo_calc', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("cfx_adjop")}),ISNUMBER({V("sp_adjop")})),{V("cfx_adjop")}+{V("b2b_adjop")}-{V("sp_adjop")},"")',
      note='FY2025: 0 (514 + 183 = 697, the 2025 allocation methodology matches); FY2023 +5 and FY2024 +11 (segment cost allocations refined in 2025). Corporate unallocated cost sits outside both.')
    S('rv_splice', '  Revenue — spliced history (carve-out where filed, S&P Global segment otherwise)', 'line_b', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")},IF(ISNUMBER({V("sp_rev")}),{V("sp_rev")},""))',
      fc=lambda: f'={V("is_rev")}',
      note='Comparable revenue series for growth analysis: FY2022 (pro forma) and Q1-23 – Q4-24 from S&P Global (black = formula on the memo rows); carve-out thereafter.')
    S('rv_splice_g', '    y/y % (spliced)', 'growth', 'pct', all=growth('rv_splice'))
    S('rv_basis', '    Basis of the spliced series', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — tuck-ins; none announced)', 'block', note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / revenue (x)', 'driver', 'x2', ae_in=5.0, e26_in=0.0,
      note='Assumption: data / software tuck-ins at ~5x revenue (Market Scan, Feb-2023: $214m cash).')
    S('m_acq', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.06)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq")}',
      note='Mid-year convention. Unallocated to segments (separate line in the group build).')
    S('m_m', '  Adjusted EBITDA margin of acquired businesses %', 'driver', 'pct', e26_in=0.0, ae_in=0.30, note='Assumption (B2B-like margin).')
    S('m_ebitda', '  Adjusted EBITDA from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.40, note='Market Scan: $87m intangibles (customer relationships $81m / 20y, trade names $6m / 7y).')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=15)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)')
    blank()

    # ------------------------------------------------------------------ group total & outlook calibration
    S('g_hdr', 'Group total — revenue & Adjusted EBITDA (segment build) → FY26 outlook calibration', 'block', note='GROUP TOTAL — modelling logic')
    S('g_rev', 'Revenue (segment build)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("cfx_rev")}),{V("cfx_rev")}+{V("b2b_rev")},"")', fc=lambda: f'={V("cfx_rev")}+{V("b2b_rev")}+N({V("m_rev")})',
      note='CARFAX + B2B (+ future acquisitions from 2027E).')
    S('g_rev_g', '  Revenue y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs consolidated revenue (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_rev")}),ISNUMBER({V("is_rev")})),ROUND({V("g_rev")}-{V("is_rev")},1),"")')
    S('g_adj', 'Adjusted EBITDA (segment build)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("cfx_adj")}),{V("cfx_adj")}+{V("b2b_adj")}+{V("corp_adj")},"")',
      fc=lambda: f'={V("cfx_adj")}+{V("b2b_adj")}+{V("corp_adj")}+N({V("m_ebitda")})',
      note="Mobility Global's guided profit KPI. CARFAX + B2B + Corporate Segment Adjusted EBITDA (+ future acquisitions). Drives the GAAP P&L below.")
    S('g_adjm', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('g_adj', 'g_rev'))
    S('g_chk_adj', '  Check: segment build vs company-published Adjusted EBITDA (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("g_adj")}),ISNUMBER({V("r_adj_pub")})),IF(ABS({V("g_adj")}-{V("r_adj_pub")})<=1,0,{V("g_adj")}-{V("r_adj_pub")}),"")',
      fc=lambda: f'=ROUND({V("g_adj")}-{V("r_adj")},1)')
    S('cal_guid', '  Memo: FY26 revenue guidance (scenario end-point)', 'memo', 'm', e26=lambda: '=' + CH(SC['out_rev']), note=V0['rev_guid_note'])
    S('cal_pre', '  Revenue before calibration (Q3/Q4-26E helper)', 'line', 'm', qe=lambda: '=' + '+'.join(f'{P(k + "_rev")}*(1+{V(k + "_pre")})' for k, _, _ in SEGS))
    S('cal_sens', '  Revenue sensitivity to +1.00 of growth (Q3/Q4-26E helper)', 'line', 'm', qe=lambda: '=' + '+'.join(P(k + '_rev') for k, _, _ in SEGS))
    S('cal_g', '  Outlook calibration: Δ y/y growth applied to both segments (Q3/Q4-26E)', 'driver', 'pct',
      qe=lambda: (f'=({V("cal_guid", E26)}-{Q1}{R["g_rev"]}-{Q2}{R["g_rev"]}-{Q3}{R["cal_pre"]}-{Q4}{R["cal_pre"]})/({Q3}{R["cal_sens"]}+{Q4}{R["cal_sens"]})'
                  if CTX.col.q == 3 else f'={Q3v("cal_g")}'),
      note='Closed-form solve: uniform growth shift (vs 1H/26 y/y rates) so FY26 revenue = the guidance end-point for the active scenario.')
    S('cal_rev_chk', '  Check: FY26 revenue vs guidance end-point (should be 0)', 'check', 'm', e26=lambda: f'=ROUND({V("g_rev")}-{V("cal_guid")},1)')
    S('cal_eb', '  Memo: FY26 Adjusted EBITDA guidance (scenario end-point)', 'memo', 'm', e26=lambda: '=' + CH(SC['out_ebitda']), note=V0['eb_guid_note'])
    S('cal_eb_pre', '  Adjusted EBITDA before margin calibration (Q3/Q4-26E helper)', 'line', 'm',
      qe=lambda: f'={V("cfx_rev")}*{V("cfx_m_pre")}+{V("b2b_rev")}*{V("b2b_m_pre")}+{V("corp_adj")}')
    S('cal_m', '  Outlook calibration: Δ Segment Adjusted EBITDA margin (both segments, Q3/Q4-26E)', 'driver', 'pct',
      qe=lambda: (f'=({V("cal_eb", E26)}-{Q1}{R["g_adj"]}-{Q2}{R["g_adj"]}-{Q3}{R["cal_eb_pre"]}-{Q4}{R["cal_eb_pre"]})/'
                  f'({Q3}{R["cfx_rev"]}+{Q3}{R["b2b_rev"]}+{Q4}{R["cfx_rev"]}+{Q4}{R["b2b_rev"]})' if CTX.col.q == 3 else f'={Q3v("cal_m")}'),
      note='Solves the uniform segment-margin shift so FY26 Adjusted EBITDA = the guidance end-point (after the corporate-cost input). Negative = standalone dis-synergies beyond the corporate input.')
    S('cal_eb_chk', '  Check: FY26 Adjusted EBITDA vs guidance end-point (should be 0)', 'check', 'm', e26=lambda: f'=ROUND({V("g_adj")}-{V("cal_eb")},1)')
    S('cal_gr', '  Memo: FY26 revenue growth guidance (+6.9–7.7%) vs model', 'memo_calc', 'pct', e26=lambda: f'={V("g_rev")}/{P("is_rev")}-1')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A and adjusting items', 'block', note='COST DRIVERS — inputs that drive forecast cost lines')
    S('d_opex', '  Operating-related expenses % of revenue', 'pct', 'pct', all=ratio('is_opex', 'is_rev'), qe=lambda: f'={P("d_opex")}', ae_in=V0['opex_pct'],
      note='Q3/Q4-26E: prior-year quarter ratio. 2027E+: input (FY2023–25: 30.2% / 29.4% / 29.5%). Selling & general expenses is the balancing line to the Adjusted EBITDA build.')
    S('d_dep', '  Depreciation', 'line', 'm', data='dep', flow=True, qe=lambda: f'={H1("d_dep")}/2', e26=lambda: S26('d_dep'),
      ae=lambda: f'={V("is_rev")}*{V("d_dep_pct")}', note='Q3/Q4-26E: 1H/26 run-rate. 2027E+: revenue × depreciation %. Q3/Q4-25: not split from amortization (Ex. 99.2 shows D&A combined).')
    S('d_dep_pct', '  Depreciation % of revenue', 'pct', 'pct', all=ratio('d_dep', 'is_rev'), ae_in=V0['dep_pct'])
    S('d_amort', '  Amortization of intangibles', 'line', 'm', data='amort', flow=True,
      qe=lambda: f'=({MAN["amort_sched"]["2026"]}-{H1("d_amort")})/2', e26=lambda: S26('d_amort'), ae=lambda: f'={V("d_amort_sch")}+N({V("m_amort")})',
      note='Q3/Q4-26E: Form 10 schedule ($296m FY2026) less 1H/26. 2027E+: schedule + future-acquisition amortization.')
    S('d_amort_sch', '  Amortization schedule — intangibles held at 31-Dec-2025 (input)', 'driver', 'm', ae_in=V0['amort_ae'], note=V0['amort_note'])
    S('d_da', '  Depreciation & amortization (total)', 'line_b', 'm', data='da', flow=True, fc=lambda: f'={V("d_dep")}+{V("d_amort")}')
    S('d_sbc', '  Stock-based compensation', 'line', 'm', data='sbc', flow=True, qe_in=V0['sbc_q'], e26=lambda: S26('d_sbc'),
      ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}', note=V0['sbc_note'])
    S('d_sbc_pct', '  Stock-based compensation % of revenue', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_trans', '  Transaction costs (stand-up of the spin business / separation)', 'line', 'm', data='trans', flow=True, qe_in=V0['trans_q'], e26=lambda: S26('d_trans'),
      ae_in=V0['trans_ae'], note=V0['trans_note'])
    S('d_oth', '  Severance, integration, acquisition / disposition, ELT transition, legal recovery & other items', 'line', 'm', data='oth_items', flow=True,
      qe_in=V0['oth_q'], e26=lambda: S26('d_oth'), ae_in=V0['oth_ae'], labkey='items_lab',
      note='Company items as labelled each period (cell comments). Forecast: assumption (restructuring-type items recur at a low level).')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'COMBINED / CONSOLIDATED STATEMENT OF INCOME (US GAAP)', 'section',
      note='IS — forecast logic (operating profit = Adjusted EBITDA − D&A − SBC − transaction costs − other items; selling & general expenses implied)')
    S('is_rev', 'Revenue', 'total', 'm', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Carve-out (combined) revenue as filed. Forecast linked to the segment build.')
    S('is_opex', '  Operating-related expenses', 'line', 'm', data='opex', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_opex")}')
    S('is_sga', '  Selling and general expenses', 'line', 'm', data='sga', flow=True, fc=lambda: f'={V("is_rev")}-{V("is_opex")}-{V("d_da")}-{V("is_op")}',
      note='Forecast = balancing line (revenue − operating-related expenses − D&A − operating profit). Includes SBC, transaction costs and other items.')
    S('is_da', '  Depreciation and amortization of intangibles', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("d_da")}),{V("d_da")},"")')
    S('is_op', 'Operating profit', 'total', 'm', data='op', flow=True,
      fc=lambda: f'={V("g_adj")}-{V("d_da")}-{V("d_sbc")}-{V("d_trans")}-{V("d_oth")}',
      note='Historical as filed. Forecast = Adjusted EBITDA − D&A − SBC − transaction costs − other items.')
    S('is_opm', '  Operating margin %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('is_othinc', 'Other income, net (income = +)', 'line', 'm', data='othinc', flow=True, fc=lambda: '=0',
      note='FY2023 $2m / FY2024 $1m: related-party dividend income (pre-spin). Nil forecast.')
    S('is_int', 'Interest expense, net', 'line', 'm', data='int', flow=True,
      qe=lambda: f'={PT("pt_int")}/2',
      ae=lambda: f'={P("ds_face")}*{V("ds_r_notes")}+{V("ds_accr")}+{P("ds_rev")}*{V("ds_r_rev")}+{V("ds_fees")}-{P("cf_end")}*{V("ds_r_cash")}',
      note=('To 30-Jun-2026: related-party (Canada Carfax) loan interest + one month of senior-note interest. Q3/Q4-26E: point estimate. '
            '2027E+: coupons on opening notes face + issuance-cost accretion + revolver + fees − interest on opening cash (no circularity).'))
    S('is_ebt', 'Income before taxes on income', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_op")}),{V("is_op")}+N({V("is_othinc")})-{V("is_int")},"")')
    S('is_tax', 'Provision for taxes on income', 'line', 'm', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Separate-return method pre-spin (FY2023 27.3%, FY2024 26.8%, FY2025 32.5% incl. discretes; 1H/26 29.4%). Not guided; Q3/Q4-26E point estimate; 2027E+ input.')
    S('is_ni', 'Net income', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_ni_chk', '  Check: net income vs reported (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=1,0,{V("is_ni")}-{V("is_ni_pub")}),"")')
    S('is_ni_pub', '  Memo: net income as reported', 'memo', 'm', data='ni', flow=True)
    S('is_dda', '  Memo: depreciation & amortization (total)', 'memo_calc', 'm', all=lambda: f'=IF(ISNUMBER({V("d_da")}),{V("d_da")},"")')
    S('is_sbc', '  Memo: stock-based compensation', 'memo_calc', 'm', all=lambda: f'=IF(ISNUMBER({V("d_sbc")}),{V("d_sbc")},"")')
    S('eps_hdr', '(Earnings per share — 294.8m shares distributed 1-Jul-2026; the 10-Q applies that count to all periods presented)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_basic', avg=True,
      qe=lambda: f'=${Q2}${R["sh_basic"]}+${E26}${R["bb_iss"]}*{0.5 if CTX.col.q == 3 else 1.0}',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note=('Published only for Q2-25 / Q2-26 (10-Q: 294,821,320 for all periods presented). FY2023–25 and Q1 / Q3 / Q4 carve-out periods have no published share '
            'count, so per-share history is not shown there. Q3/Q4-26E: distributed shares + equity-plan issuance.'))
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_dil', avg=True,
      qe=lambda: f'={V("sh_basic")}+{V0["dil_q"]}', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}',
      note='Q3/Q4-26E: + dilutive RSUs / options from the spin-date awards (assumption, ~1m shares).')
    S('eps_basic', 'EPS – basic ($)', 'eps', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_basic")}),IFERROR({V("is_ni")}/{V("sh_basic")},""),"")')
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($)', 'eps_memo', 'ps', data='eps_dil')
    S('eps_chk', '  Check: diluted EPS vs reported (should be 0; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(ISNUMBER({V("eps_pub")}),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0101,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"")')
    S('dps', '  Dividends declared per share ($)', 'line', 'ps', qe_in=V0['dps_q'], e26=lambda: S26('dps'), ae=lambda: f'={P("dps")}*(1+{V("dps_g")})',
      note='$0.06 quarterly declared Aug-2026 (payable 10-Sep-2026); Q4-26E $0.06 (company intention, 10-Q). 2027E+: annualised $0.24 × (1 + growth).')
    S('dps_g', '    DPS growth % (2027E = annualisation of the quarterly rate)', 'driver', 'pct', ae_in=V0['dps_g'])
    blank()

    # ------------------------------------------------------------------ RECON 1: EBITDA
    S('sec_r1', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (company definition)', 'section',
      note='ADJUSTED EBITDA — company reconciliation (Form 10 MD&A; release Exhibit 5): net income + interest + taxes + D&A + SBC + transaction costs + severance & other items')
    S('r_ni', 'Net income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('r_int', '  (+) Interest expense, net', 'line', 'm', all=lambda: f'={V("is_int")}')
    S('r_tax', '  (+) Provision for taxes on income', 'line', 'm', all=lambda: f'={V("is_tax")}')
    S('r_ebit', '  = EBIT (operating profit + other income)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_int")}+{V("r_tax")},"")',
      note='The company reconciliation keeps other income (FY2023 $2m, FY2024 $1m) inside EBITDA.')
    S('r_da', '  (+) Depreciation & amortization', 'line', 'm', all=lambda: f'={V("d_da")}')
    S('r_ebitda', '  = EBITDA', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_ebit")}),ISNUMBER({V("r_da")})),{V("r_ebit")}+{V("r_da")},"")')
    S('r_sbc', '  (+) Stock-based compensation', 'line', 'm', all=lambda: f'={V("d_sbc")}')
    S('r_trans', '  (+) Transaction costs (stand-up of the spin business)', 'line', 'm', all=lambda: f'={V("d_trans")}')
    S('r_oth', '  (+) Severance, integration, acquisition / disposition, legal recovery & other', 'line', 'm', all=lambda: f'={V("d_oth")}')
    S('r_tot', '  Total adjusting items', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{nsum(["r_sbc", "r_trans", "r_oth"])},"")')
    S('r_adj', '  = Adjusted EBITDA (model bridge)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{V("r_ebitda")}+{V("r_tot")},"")')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_adj_pub', '  Company-published Adjusted EBITDA', 'memo', 'm', data='adj_pub', flow=True)
    S('r_adj_chk', '  Check: model bridge vs company-published (should be 0; ±1 whole-$m rounding)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("r_adj_pub")}),ISNUMBER({V("r_adj")})),IF(ABS({V("r_adj")}-{V("r_adj_pub")})<=1,0,{V("r_adj")}-{V("r_adj_pub")}),"")')
    S('r_def', '  Definition basis (company Adjusted EBITDA definition in force)', 'text', 'gen')
    S('r_cash', '  Memo: cash adjusting items (transaction, severance & other; deducted in DCF NOPAT)', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("d_trans")}),{V("d_trans")}+{V("d_oth")},"")')
    S('r_ebit_h', 'To adjusted EBIT:', 'sub', 'gen')
    S('r_dep', '  (−) Depreciation', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("d_dep")}),-{V("d_dep")},"")')
    S('r_ebita', '  = Adjusted EBITA (Adjusted EBITDA − depreciation; incl. SBC add-back)', 'line_b', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_adj")}),ISNUMBER({V("r_dep")})),{V("r_adj")}+{V("r_dep")},"")')
    S('r_amort', '  (−) Amortization of intangibles', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("d_amort")}),-{V("d_amort")},"")')
    S('r_ebit_adj', '  = Adjusted EBIT (model; Adjusted EBITDA − D&A)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}-{V("d_da")},"")',
      note='Full-cost measure for ROIC (amortization of acquired intangibles deducted). Note: the company Adjusted EBITDA adds back SBC; the DCF deducts it.')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: OP -> adjusted OP (company)
    S('sec_r2', 'RECONCILIATION: OPERATING PROFIT → ADJUSTED OPERATING PROFIT (company definition; published in the Form 10)', 'section',
      note='ADJUSTED OPERATING PROFIT — company definition (Form 10): operating profit + amortization of intangibles + transaction costs + severance & other items (SBC and depreciation not added back)')
    S('o_op', 'Operating profit (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_op")}')
    S('o_amort', '  (+) Amortization of intangibles', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("d_amort")}),{V("d_amort")},"")')
    S('o_items', '  (+) Transaction costs, severance & other items', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("d_trans")}),{V("d_trans")}+{V("d_oth")},"")')
    S('o_adj', '  = Adjusted operating profit (model bridge)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("o_op")}),ISNUMBER({V("o_amort")})),{V("o_op")}+{V("o_amort")}+N({V("o_items")}),"")',
      note='Not computable for Q3/Q4-25 (amortization not split from D&A in Ex. 99.2).')
    S('o_adj_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company-published Adjusted operating profit', 'memo', 'm', data='adjop_pub', flow=True)
    S('o_chk', '  Check: model vs company-published (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("o_pub")}),ISNUMBER({V("o_adj")})),IF(ABS({V("o_adj")}-{V("o_pub")})<=1,0,{V("o_adj")}-{V("o_pub")}),"")')
    S('o_chk2', '  Check: Adjusted OP + depreciation + SBC + other income vs Adjusted EBITDA (should be 0; ±1 rounding)', 'check', 'm',
      all=lambda: (f'=IF(AND(ISNUMBER({V("o_adj")}),ISNUMBER({V("r_adj")}),ISNUMBER({V("d_dep")})),IF(ABS({V("o_adj")}+{V("d_dep")}+{V("d_sbc")}+N({V("is_othinc")})-{V("r_adj")})<=1,0,'
                   f'{V("o_adj")}+{V("d_dep")}+{V("d_sbc")}+N({V("is_othinc")})-{V("r_adj")}),"")'))
    S('o_def', '  Definition basis', 'text', 'gen')
    S('o_g', '  Adjusted operating profit y/y %', 'growth', 'pct', all=growth('o_adj'))
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS (model)
    S('sec_r3', 'RECONCILIATION: GAAP NET INCOME → ADJUSTED NET INCOME → ADJUSTED EPS (MODEL DEFINITION — not published by the company)', 'section',
      note='ADJUSTED EPS — model definition (Mobility Global publishes no adjusted EPS): + amortization of intangibles + transaction costs + severance & other, tax-effected at the period effective tax rate')
    S('e_ni', 'Net income (GAAP)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("e_sh")}),{V("is_ni")},"")')
    S('e_amort', '  (+) Amortization of intangibles (pre-tax)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("e_sh")}),{V("d_amort")},"")')
    S('e_items', '  (+) Transaction costs, severance & other (pre-tax)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("e_sh")}),{V("d_trans")}+{V("d_oth")},"")')
    S('e_tax', '  (−) Tax effect of adjustments', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("e_sh")}),-({V("e_amort")}+{V("e_items")})*{V("e_rate")},"")')
    S('e_adjni', '  = Adjusted net income (model)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("e_sh")}),{V("e_ni")}+{V("e_amort")}+{V("e_items")}+{V("e_tax")},"")')
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted EPS – diluted ($) (model definition)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_rate', '  Tax rate applied to adjustments (period effective tax rate, bounded 15–40%)', 'pct', 'pct',
      all=lambda: f'=IF(ISNUMBER({V("is_etr")}),MIN(0.4,MAX(0.15,{V("is_etr")})),"")')
    S('e_def', '  Definition basis', 'text', 'gen')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (combined / consolidated) — outputs')
    S('gm_rev', '  Revenue y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_cfx', '  CARFAX revenue y/y %', 'growth', 'pct', all=growth('cfx_rev'))
    S('gm_b2b', '  B2B revenue y/y %', 'growth', 'pct', all=growth('b2b_rev'))
    S('gm_sub', '  Subscription revenue % of total', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cfx_sub")}),IFERROR(({V("cfx_sub")}+{V("b2b_sub")})/{V("is_rev")},""),"")')
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating profit y/y %', 'growth', 'pct', all=growth('is_op'))
    S('gm_ni', '  Net income y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_inc', '  Incremental Adjusted EBITDA margin (ΔEBITDA / ΔRevenue)', 'pct', 'pct', all=incr('r_adj', 'is_rev'))
    S('gm_adjop_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_sga', '  Selling & general expenses % of revenue', 'pct', 'pct', all=ratio('is_sga', 'is_rev'))
    blank()
