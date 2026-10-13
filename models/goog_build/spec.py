"""Row specification of the WWD Model sheet, part 1 (MLM template layout and process):
segment x primary-market sales build (Aerospace: commercial OEM / commercial services / defense OEM / defense services;
Industrial: power generation / transportation / oil and gas) -> segment earnings at the segment margin -> + adjusted nonsegment
expenses = adjusted EBIT -> M&A lever and pending divestitures -> group total & FY26 guidance calibration -> cost drivers ->
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
def QEa(key): return f'${QE}${R[key]}'                    # Q4/26E (absolute)
def QEc(key): return f'{QE}{R[key]}'                      # Q4/26E
def ACT(key): return f'SUM({Q1}{R[key]}:{Q3}{R[key]})'    # 9M FY26 actual (Q1-Q3/26)
def ACT0(key): return f'SUM({PQ1}{R[key]}:{PQ3}{R[key]})' # 9M FY25 actual (Q1-Q3/25)
def B1(key): return f'{LQ}{R[key]}'                       # 30-Jun-2026 balance

SEG = [('aero', 'Aerospace', 'AERO', [('coem', 'Commercial OEM', 'em_com_oem'), ('cserv', 'Commercial services (aftermarket)', 'em_com_aft'),
                                      ('doem', 'Defense OEM', 'em_def_oem'), ('dserv', 'Defense services (aftermarket)', 'em_def_aft')], 'sr_aero', 'se_aero'),
       ('ind', 'Industrial', 'IND', [('pg', 'Power generation', 'em_pg'), ('trans', 'Transportation', 'em_trans'), ('og', 'Oil and gas', 'em_og')], 'sr_ind', 'se_ind')]
LINES = [f'{s}_{t}' for s, _, _, ts, _, _ in SEG for t, _, _ in ts]
SEGK = [s for s, *_ in SEG]
ADJ = ['d_restr', 'd_acq', 'd_pa', 'd_gain', 'd_impair', 'd_oadj']

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
    S('sec_seg', 'SEGMENT P&L — AEROSPACE · INDUSTRIAL (sales by primary market × segment earnings margin)', 'section',
      note='SEGMENT BUILD — modelling logic (sales by primary market → segment sales → segment earnings at the segment margin → + adjusted nonsegment expenses = adjusted EBIT → GAAP P&L)')
    blank()
    descr = {'aero': 'Aerospace (fuel, combustion, actuation, motion & flight-control systems for commercial and defense aircraft, guided weapons; OEM and aftermarket)',
             'ind': 'Industrial ("Energy" to FY2015; fuel, combustion, ignition & control systems for gas turbines, reciprocating engines and compressors; L\'Orange fuel injection from Jun-2018)'}
    for s, title, code, types, pub, earn in SEG:
        S(f'{s}_hdr', descr[s], 'block', note=f'{title.upper()} — modelling logic')
        for t, tl, dk in types:
            key = f'{s}_{t}'
            S(key, f'  {tl} sales', 'line', 'm1', data=dk, flow=True,
              qe=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})', ae=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})',
              note=('Sales by primary market (10-Q / 10-K revenue-disaggregation note, from FY2019; Q4 = fiscal year − nine months). Q4/26E: prior-year quarter × (1 + growth). '
                    '2027E+: prior year × (1 + scenario lever).') if t == types[0][0] else None)
            S(key + '_g', '    y/y %', 'growth', 'pct', all=growth(key),
              qe=lambda key=key: f'={V(key + "_pre")}+{QEa("cal_g")}',
              ae=lambda key=key, code=code, t=t: '=' + CH(SC[f'{code}_{t.upper()}'][CTX.col.year]),
              note='Q4/26E: 9M FY26 y/y growth of the market + sales-guidance calibration Δ (Group block). 2027E–2031E: scenario lever (Bull/Base/Bear table →).' if t == types[0][0] else None)
            S(key + '_pre', '    Q4/26E growth before sales calibration (9M FY26 y/y)', 'driver', 'pct',
              qe=lambda key=key: f'=IFERROR({ACT(key)}/{ACT0(key)}-1,0)')
        first = f'{s}_{types[0][0]}'
        S(f'{s}_rev', f'  {title} — segment net sales', 'line_b', 'm1',
          hist=lambda s=s, types=types, first=first: f'=IF(ISNUMBER({V(first)}),{"+".join(V(s + "_" + t) for t, _, _ in types)},{V(s + "_pub")})',
          fc=lambda s=s, types=types: '=' + '+'.join(V(s + '_' + t) for t, _, _ in types),
          note='History: Σ primary markets where published, otherwise segment net sales as reported.' if s == 'aero' else None)
        S(f'{s}_rev_g', '  Segment sales y/y %', 'growth', 'pct', all=growth(f'{s}_rev'))
        S(f'{s}_mix', '  % of total net sales', 'pct', 'pct', all=ratio(f'{s}_rev', 'g_rev'))
        if s == 'aero':
            S('aero_aft', '  Aftermarket (commercial + defense services) % of Aerospace sales', 'pct', 'pct',
              all=lambda: f'=IF(ISNUMBER({V("aero_cserv")}),IFERROR(({V("aero_cserv")}+{V("aero_dserv")})/{V("aero_rev")},""),"")')
        S(f'{s}_pub', f'  Memo: {title} segment net sales as reported (segment schedule)', 'memo', 'm1', data=pub, flow=True)
        S(f'{s}_chk', '  Check: primary markets vs segment net sales (should be 0)', 'check', 'm1',
          hist=lambda s=s, first=first: f'=IF(AND(ISNUMBER({V(first)}),ISNUMBER({V(s + "_pub")})),IF(ABS({V(s + "_rev")}-{V(s + "_pub")})<=0.15,0,ROUND({V(s + "_rev")}-{V(s + "_pub")},1)),"")')
        S(f'{s}_oi', f'  {title} segment earnings', 'line', 'm1', data=earn, flow=True,
          qe=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}', ae=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}',
          note=('Segment earnings as reported (company measure: after amortization of intangibles; excludes nonsegment expenses). Forecast = segment sales × segment margin.')
          if s == 'aero' else None)
        S(f'{s}_m', '  Segment margin %', 'pct', 'pct', all=ratio(f'{s}_oi', f'{s}_rev'),
          qe=lambda s=s: f'={V(s + "_m_pre")}+{QEa("cal_m")}', ae=lambda s=s, code=code: '=' + CH(SC[f'{code}_M'][CTX.col.year]),
          note='Q4/26E: margin before calibration + adjusted-EPS-guidance calibration Δ (Group block). 2027E+: scenario lever.' if s == 'aero' else None)
        S(f'{s}_m_pre', '  Q4/26E margin before EPS calibration (prior-year quarter + 9M FY26 y/y drift)', 'driver', 'pct',
          qe=lambda s=s: f'={P(s + "_m")}+IFERROR({ACT(s + "_oi")}/{ACT(s + "_rev")}-{ACT0(s + "_oi")}/{ACT0(s + "_rev")},0)')
        S(f'{s}_inc', '  Incremental segment margin (Δ earnings / Δ sales)', 'pct', 'pct', all=incr(f'{s}_oi', f'{s}_rev'))
        S(f'{s}_oi_py', f'  Memo: {title} segment earnings as restated in the following year\'s release (where different)', 'memo', 'm1', data=f'{earn}_py', flow=True,
          note='FY2018 restated in the FY2019 release (pension-cost reclassification, ASU 2017-07); the model keeps the originally reported figure.' if s == 'aero' else None)
        if s == 'ind':
            S('ind_leg_h', '  Legacy primary markets (as originally reported FY2019–FY2022; replaced in the FY2023 10-K):', 'sub', 'gen')
            for k, lab in (('recip', 'Reciprocating engines'), ('ind_turb', 'Industrial turbines'), ('renew', 'Renewables (sold May-2020)')):
                S(f'ind_l_{k}', f'    {lab}', 'memo', 'm1', data=f'em_{k}', flow=True)
            S('ind_l_chk', '    Check: legacy markets vs segment net sales (should be 0)', 'check', 'm1',
              hist=lambda: f'=IF(ISNUMBER({V("ind_l_recip")}),IF(ABS({V("ind_l_recip")}+N({V("ind_l_ind_turb")})+N({V("ind_l_renew")})-{V("ind_pub")})<=0.15,0,ROUND({V("ind_l_recip")}+N({V("ind_l_ind_turb")})+N({V("ind_l_renew")})-{V("ind_pub")},1)),"")')
        blank()
    S('co_hdr', 'Nonsegment expenses (corporate costs, restructuring and other items not allocated to the segments)', 'block',
      note='NONSEGMENT — corporate office costs (compensation, benefits, depreciation, administration); adjusting items are recorded here')
    S('ns_gaap', '  Nonsegment expenses, as reported (incl. adjusting items)', 'line', 'm1', data='nonseg', flow=True,
      fc=lambda: f'={V("corp")}-{V("o_tot")}')
    S('corp', '  Adjusted nonsegment expenses (model: as reported + adjusting items)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("ns_gaap")}),{V("ns_gaap")}+{V("o_tot")},"")',
      qe=lambda: f'={P("corp")}*(1+{V("corp_g")})', ae=lambda: f'={V("is_rev")}*{V("corp_pct")}',
      note=('Equals the company\'s adjusted nonsegment expenses where all adjusting items sit in nonsegment (FY2021+); FY2018–19 L\'Orange purchase accounting sat in Industrial segment earnings. '
            'Q4/26E: prior-year quarter × (1 + 9M FY26 y/y). 2027E+: % of net sales.'))
    S('corp_g', '  Adjusted nonsegment expenses y/y %', 'growth', 'pct', all=growth('corp'), qe=lambda: f'=IFERROR({ACT("corp")}/{ACT0("corp")}-1,0)')
    S('corp_pct', '  Adjusted nonsegment expenses % of net sales', 'pct', 'pct', all=ratio('corp', 'is_rev'), ae_in=V0['corp_pct'])
    blank()
    S('mx_hdr', 'Sales by end market (outputs)', 'block', note='MIX — outputs')
    S('mx_com', '  Commercial aerospace (OEM + services)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("aero_coem")}),{V("aero_coem")}+{V("aero_cserv")},"")')
    S('mx_def', '  Defense (OEM + services)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("aero_doem")}),{V("aero_doem")}+{V("aero_dserv")},"")')
    S('mx_com_p', '  Commercial aerospace % of total sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("mx_com")}),IFERROR({V("mx_com")}/{V("g_rev")},""),"")')
    S('mx_def_p', '  Defense % of total sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("mx_def")}),IFERROR({V("mx_def")}/{V("g_rev")},""),"")')
    S('mx_com_g', '  Commercial aerospace y/y %', 'growth', 'pct', all=growth('mx_com'))
    S('mx_def_g', '  Defense y/y %', 'growth', 'pct', all=growth('mx_def'))
    S('gc_aero', '  Contribution to total sales growth — Aerospace (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("aero_rev")}-{P("aero_rev")})/{P("g_rev")},"")' if CTX.col.prior else None))
    S('gc_ind', '  Contribution to total sales growth — Industrial (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("ind_rev")}-{P("ind_rev")})/{P("g_rev")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — Aerospace / Industrial bolt-ons, unallocated; deals closed from 2027E)', 'block',
      note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=3.0, e26_in=0.0,
      note='L\'Orange (Jun-2018) $771m on ~$290m annual sales (~2.7x); Valve Research (Apr-2026) $121m; Safran EMA (Jul-2025) $40m. 3.0x input (assumption).')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.05)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}',
      note='Mid-year convention.')
    S('m_m', '  Earnings margin of acquired businesses (after amortization) %', 'driver', 'pct', e26_in=0.0, ae_in=0.15)
    S('m_oi', '  Earnings from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.10)
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.40,
      note='PPAs: L\'Orange 74% of the purchase price in intangibles, Valve Research 30%, Safran EMA 0%.')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=15)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (inside segment earnings)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)',
      note='Woodward does not adjust out amortization; the acquired-business margin above is after amortization.')
    blank()

    # ------------------------------------------------------------------ pending divestitures
    S('dv_hdr', 'Pending divestitures — Aerospace pilot controls (to ONTIC, $180m; close expected FY2027) · Santa Clarita product lines & campus (terms not disclosed)', 'block',
      note='DIVESTITURES — gain recorded in other income, net and excluded from adjusted earnings (company practice for divestitures)')
    S('dv_proc', '  Cash proceeds (USDm; ONTIC $180m in 2027E)', 'line', 'm1', e26_in=0.0, ae_in=V0['dv_proc'], note=MAN['deals']['ontic_pilot_controls'])
    S('dv_nav', '  Net assets held for sale (30-Jun-2026: assets $20.0m − liabilities $3.6m)', 'driver', 'm1', e26_in=0.0, ae_in=V0['dv_nav'])
    S('dv_gain', '  Pre-tax gain on sale (assumption: proceeds − net assets held for sale; goodwill allocation not disclosed)', 'line', 'm1', e26_in=0.0,
      ae=lambda: f'={V("dv_proc")}-{V("dv_nav")}')
    S('dv_rev', '  Sales of the divested product lines (not disclosed — input 0; flag)', 'driver', 'm1', e26_in=0.0, ae_in=0.0,
      note='Neither the pilot-controls nor the Santa Clarita product-line sales are disclosed; no revenue is removed from the Aerospace build (assumption).')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group Total — net sales & adjusted EBIT (segment build) → FY26 guidance calibration', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Net sales (segment build)', 'total', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("aero_rev")}),{V("aero_rev")}+{V("ind_rev")},{V("is_rev")})',
      fc=lambda: f'={V("aero_rev")}+{V("ind_rev")}+N({V("m_rev")})-N({V("dv_rev")})',
      note='Σ segment sales (+ future acquisitions − divested product lines from 2027E).')
    S('g_rev_g', '  Net sales y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs consolidated net sales (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=0.15,0,ROUND({V("g_rev")}-{V("is_rev")},1)),"")')
    S('g_adj', 'Adjusted EBIT (segment build)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("aero_oi")}),{V("aero_oi")}+{V("ind_oi")}+{V("corp")}+N({V("m_oi")}),"")',
      note="Σ segment earnings + adjusted nonsegment expenses (+ future acquisitions). Woodward's adjusted EBIT (company definition); drives the GAAP P&L below.")
    S('g_adjm', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('g_adj', 'is_rev'))
    S('g_adj_g', '  Adjusted EBIT y/y %', 'growth', 'pct', all=growth('g_adj'))
    S('g_chk_adj', '  Check: segment build vs adjusted EBIT bridge (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_adj")}),ISNUMBER({V("o_adj")})),IF(ABS({V("g_adj")}-{V("o_adj")})<=0.15,0,ROUND({V("g_adj")}-{V("o_adj")},1)),"")')
    S('cal_guid', '  Memo: FY26 net sales guidance (scenario end-point = FY2025 × (1 + guided sales growth))', 'memo', 'm1',
      e26=lambda: f'={Y("is_rev", 2025)}*(1+{CH(SC["out_g"])})', note=V0['rev_guid_note'])
    S('cal_pre', '  Net sales before calibration (Q4/26E helper)', 'line', 'm1', qe=lambda: '=' + '+'.join(f'{P(k)}*(1+{V(k + "_pre")})' for k in LINES))
    S('cal_sens', '  Net sales sensitivity to +1.00 of growth (Q4/26E helper)', 'line', 'm1', qe=lambda: '=' + '+'.join(P(k) for k in LINES))
    S('cal_g', '  Guidance calibration: Δ y/y growth applied to all primary markets (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_guid", E26)}-{ACT("g_rev")}-{V("cal_pre")})/{V("cal_sens")}',
      note='Solves the uniform growth shift (vs 9M FY26 y/y rates) so that FY26 net sales = the guidance end-point for the active scenario.')
    S('cal_rev_chk', '  Check: FY26 net sales vs guidance end-point (should be 0)', 'check', 'm1', e26=lambda: f'=ROUND({V("g_rev")}-{V("cal_guid")},1)')
    S('cal_eps', '  Memo: FY26 adjusted EPS guidance (scenario end-point, $)', 'eps_memo', 'ps', e26=lambda: '=' + CH(SC['out_eps']), note=V0['eps_guid_note'])
    S('cal_ni', '  Adjusted net earnings required (FY26E diluted shares × EPS guidance)', 'memo_calc', 'm1', e26=lambda: f'={V("cal_eps")}*{V("e_sh")}')
    S('cal_oi', '  Q4/26E adjusted EBIT required ((NI − 9M actual) ÷ (1 − Q4 tax rate) + Q4 interest expense − interest income)', 'memo_calc', 'm1',
      e26=lambda: f'=({V("cal_ni")}-{ACT("e_adjni")})/(1-{PT("pt_etr")})+{QEc("is_int")}-{QEc("is_intinc")}')
    S('cal_oi_pre', '  Adjusted EBIT before margin calibration (Q4/26E helper)', 'line', 'm1',
      qe=lambda: '=' + '+'.join(f'{V(s + "_rev")}*{V(s + "_m_pre")}' for s in SEGK) + f'+{V("corp")}')
    S('cal_segrev', '  Segment sales (Q4/26E helper)', 'line', 'm1', qe=lambda: '=' + '+'.join(V(s + '_rev') for s in SEGK))
    S('cal_m', '  Guidance calibration: Δ segment margin (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_oi", E26)}-{V("cal_oi_pre")})/{V("cal_segrev")}',
      note='Solves the uniform segment-margin shift so that FY26 adjusted EPS = the guidance end-point for the active scenario.')
    S('cal_eps_chk', '  Check: FY26 adjusted EPS vs guidance end-point (should be 0.00)', 'check', 'ps', e26=lambda: f'=ROUND({V("e_eps")}-{V("cal_eps")},2)')
    S('cal_ag', '  Memo: FY26 Aerospace sales growth guidance (scenario end-point) — information, not forced', 'memo', 'pct', e26=lambda: '=' + CH(SC['out_ag']))
    S('cal_ag_d', '    Model Aerospace sales growth − guidance (pp)', 'memo_calc', 'pct', e26=lambda: f'={V("aero_rev_g")}-{V("cal_ag")}')
    S('cal_ig', '  Memo: FY26 Industrial sales growth guidance (scenario end-point) — information', 'memo', 'pct', e26=lambda: '=' + CH(SC['out_ig']))
    S('cal_ig_d', '    Model Industrial sales growth − guidance (pp)', 'memo_calc', 'pct', e26=lambda: f'={V("ind_rev_g")}-{V("cal_ig")}')
    S('cal_am', '  Memo: FY26 segment margin guidance — Aerospace ~23.5% / Industrial ~19% (information)', 'memo', 'pct', e26=lambda: f'={PT("pt_am")}')
    S('cal_am_d', '    Model Aerospace margin − guidance (pp)', 'memo_calc', 'pct', e26=lambda: f'={V("aero_m")}-{V("cal_am")}')
    S('cal_im_d', '    Model Industrial margin − guidance (pp)', 'memo_calc', 'pct', e26=lambda: f'={V("ind_m")}-{PT("pt_im")}')
    S('cal_fcf', '  Memo: FY26 free cash flow guidance (scenario end-point)', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_fcf']))
    S('cal_fcf_d', '  Model FY26 free cash flow − guidance (information)', 'memo_calc', 'm1', e26=lambda: f'={V("fcf")}-{V("cal_fcf")}')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A & adjusting items', 'block', note='COST DRIVERS — inputs that drive forecast cost lines (Q4/26E: point estimates; 2027E+: % of sales or schedules)')
    S('d_dda', '  Depreciation & amortization (total; EBITDA reconciliation)', 'line', 'm1', flow=True,
      all=lambda: f'=IF(AND(ISNUMBER({V("d_dep")}),ISNUMBER({V("d_amort")})),{V("d_dep")}+{V("d_amort")},"")',
      note='Release EBIT / EBITDA reconciliations: depreciation expense + amortization of intangible assets.')
    S('d_amort', '  Amortization of intangible assets (inside segment earnings; not adjusted out)', 'line', 'm1', data='d_amort', flow=True,
      qe=lambda: f'={PT("pt_amort")}', ae=lambda: f'={V("d_amort_sch")}+N({V("m_amort")})',
      note='Q4/26E: 10-Q schedule ($8.4m remaining FY26). 2027E+: schedule of intangibles held at 30-Jun-2026 + future-acquisition amortization.')
    S('d_amort_sch', '  Amortization schedule — intangibles held at 30-Jun-2026 (10-Q, input)', 'driver', 'm1', ae_in=V0['amort_sched'], note=V0['amort_note'])
    S('d_dep', '  Depreciation expense', 'line', 'm1', data='d_dep', flow=True, qe=lambda: f'={PT("pt_dep")}', ae=lambda: f'={V("is_rev")}*{V("d_dep_pct")}')
    S('d_dep_pct', '  Depreciation % of net sales', 'pct', 'pct', all=ratio('d_dep', 'is_rev'), ae_in=V0['dep_pct'],
      note='Rising with the Spartanburg, SC aerospace campus (online summer 2027) and capacity additions.')
    S('d_sga', '  SG&A % of net sales', 'pct', 'pct', all=ratio('is_sga', 'is_rev'),
      qe=lambda: f'={P("d_sga")}+IFERROR({ACT("is_sga")}/{ACT("is_rev")}-{ACT0("is_sga")}/{ACT0("is_rev")},0)', ae_in=V0['sga_pct'],
      note='Q4/26E: prior-year quarter ratio + 9M FY26 y/y drift; 2027E+ input. Gross profit is implied: EBIT (from the adjusted build) + operating costs − other income.')
    S('d_rd', '  R&D % of net sales', 'pct', 'pct', all=ratio('is_rd', 'is_rev'), qe=lambda: f'=IFERROR({ACT("is_rd")}/{ACT("is_rev")},"")', ae_in=V0['rd_pct'])
    S('d_sbc', '  Share-based compensation (cash-flow statement, XBRL)', 'line', 'm1', data='cf_sbc', flow=True,
      qe=lambda: f'={P("d_sbc")}*(1+IFERROR({ACT("d_sbc")}/{ACT0("d_sbc")}-1,0))', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}',
      note='Q4/26E: prior-year quarter × 9M FY26 y/y; 2027E+: % of net sales. Woodward does not adjust out share-based compensation.')
    S('d_sbc_pct', '  Share-based compensation % of net sales', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_othinc', '  Other income, net — recurring (excl. divestiture gains), input', 'line', 'm1', qe=lambda: f'={PT("pt_othinc")}', ae_in=V0['othinc'],
      note='Other income includes the amortization of deferred revenue from the GE joint venture (Jan-2016), rental income, pension and investment items. 9M FY26 $60.3m. Input (assumption).')
    S('d_adj_h', '  Adjusting items (pre-tax, adjusted out by the company; forecast inputs):', 'sub', 'gen')
    S('d_restr', '  Restructuring charges', 'line', 'm1', data='oa_restr', flow=True, labkey='oa_restr_lab', qe=lambda: f'={PT("pt_restr")}', ae_in=V0['ae_restr'],
      note=MAN['restructuring']['model'])
    S('d_acq', '  Acquisition, transaction, integration & business development costs', 'line', 'm1', data='oa_acq', flow=True, labkey='oa_acq_lab',
      qe_in=0.0, ae=lambda: f'={V("m_spend")}*{V("d_acq_pct")}')
    S('d_acq_pct', '  Acquisition & integration costs % of acquisition spend', 'pct', 'pct', ae_in=0.02)
    S('d_pa', '  Purchase accounting (L\'Orange inventory step-up and backlog amortization)', 'line', 'm1', data='oa_pa', flow=True, labkey='oa_pa_lab', fc=lambda: '=0')
    S('d_gain', '  (Gains) / losses on sales of businesses, properties & product lines; swaps (product rationalization)', 'line', 'm1', data='oa_gain', flow=True,
      labkey='oa_gain_lab', qe_in=0.0, ae=lambda: f'=-{V("dv_gain")}', note='2027E: gain on the pending pilot-controls sale (negative = gain adjusted out).')
    S('d_impair', '  Impairments (Senvion FY2019; assets sold FY2020)', 'line', 'm1', data='oa_impair', flow=True, labkey='oa_impair_lab', fc=lambda: '=0')
    S('d_oadj', '  Other items (inventory / collections charges, non-recurring matters, stock-compensation acceleration, Forward Option)', 'line', 'm1',
      data='oa_other', flow=True, labkey='oa_other_lab', fc=lambda: '=0')
    S('d_indda', '  Memo: adjusting items recorded in D&A (L\'Orange backlog amortization; not added back again in adjusted EBITDA)', 'memo', 'm1', data='oa_in_dda', flow=True, fc=lambda: '=0')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF EARNINGS (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (EBIT = adjusted EBIT − adjusting items; gross profit implied)')
    S('is_rev', 'Net sales', 'total', 'm1', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the segment build.')
    S('is_cogs', 'Cost of goods sold', 'line', 'm1', data='cogs', flow=True, fc=lambda: f'={V("is_rev")}-{V("is_gp")}')
    S('is_gp', 'Gross profit', 'line_b', 'm1', hist=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_rev")}-{V("is_cogs")},"")',
      fc=lambda: f'={V("is_ebit")}+{V("is_sga")}+{V("is_rd")}+{V("is_amort")}+{V("is_restr")}+{V("is_othop")}-{V("is_othinc")}',
      note='Forecast = EBIT + operating costs − other income (implied by the adjusted EBIT build).')
    S('is_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('is_sga', 'Selling, general & administrative expenses', 'line', 'm1', data='sga', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_sga")}')
    S('is_rd', 'Research & development costs', 'line', 'm1', data='rd', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_rd")}')
    S('is_amort', 'Amortization of intangible assets (separate line to FY2020; in cost of goods sold / SG&A from FY2021)', 'line', 'm1', data='amort_is', flow=True, fc=lambda: '=0')
    S('is_restr', 'Restructuring charges', 'line', 'm1', data='restr', flow=True, fc=lambda: f'={V("d_restr")}')
    S('is_othop', 'Other items shown separately (gain on cross-currency swaps FY2020, impairments)', 'line', 'm1', data='oth_op', flow=True, fc=lambda: '=0',
      labkey='oth_op_labels')
    S('is_othinc', 'Other income, net (income +)', 'line', 'm1', data='oth_inc', flow=True, fc=lambda: f'={V("d_othinc")}-{V("d_gain")}',
      note='Forecast = recurring other income + divestiture gains (adjusted out in the bridge).')
    S('is_ebit', 'EBIT (earnings before interest and taxes — company definition)', 'total', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_gp")}),{V("is_gp")}-{V("is_sga")}-{V("is_rd")}-{V("is_amort")}-{V("is_restr")}-{V("is_othop")}+{V("is_othinc")},"")',
      fc=lambda: f'={V("g_adj")}-{V("o_tot")}',
      note='Woodward presents no operating-income line; EBIT = net earnings + income taxes + interest expense − interest income (= segment earnings + nonsegment expenses). Forecast = adjusted EBIT − adjusting items.')
    S('is_ebit_m', '  EBIT margin %', 'pct', 'pct', all=ratio('is_ebit', 'is_rev'))
    S('is_int', 'Interest expense', 'line', 'm1', data='int_exp', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_rev")}*{V("ds_r_rev")}+{V("ds_fees")}',
      note='Q4/26E point estimate. 2027E+ = rate × opening notes & term loan + rate × opening revolver + fees (no circularity).')
    S('is_intinc', 'Interest income', 'line', 'm1', data='int_inc', flow=True, qe=lambda: f'={PT("pt_intinc")}', ae=lambda: f'={P("cf_end")}*{V("ds_r_cash")}')
    S('is_ebt', 'Earnings before income taxes', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_ebit")}),{V("is_ebit")}-{V("is_int")}+{V("is_intinc")},"")')
    S('is_tax', 'Income taxes', 'line', 'm1', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Q4/26E: point estimate consistent with the ~22.5% FY26 adjusted-rate guidance. 2027E+: input.')
    S('is_ni', 'Net earnings', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_ni_chk', '  Check: net earnings vs reported (should be 0; ±0.1 rounding)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=0.15,0,ROUND({V("is_ni")}-{V("is_ni_pub")},1)),"")')
    S('is_ni_pub', '  Memo: net earnings as reported (attributable to Woodward)', 'memo', 'm1', data='ni', flow=True)
    S('is_nci', '  Memo: net earnings attributable to noncontrolling interests (none since FY2011)', 'memo', 'm1', data='nci', flow=True, fc=lambda: '=0')
    S('is_dda', '  Memo: depreciation & amortization (total)', 'memo_calc', 'm1', all=lambda: f'={V("d_dda")}')
    S('is_sbc', '  Memo: share-based compensation', 'memo_calc', 'm1', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share — Woodward common stock)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={B1("bs_shares")}-${E26}${R["bb_sh"]}*0.5+${E26}${R["bb_iss"]}*0.5',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q4/26E: shares outstanding at 30-Jun-2026 − Q4 buybacks (mid-quarter) + equity-plan issuance. 2027E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")',
      note='Net earnings / weighted diluted shares (±$0.01 vs reported).')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0101,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('dps', '  Cash dividends paid per share ($)', 'line', 'ps', data='dps', flow=True, qe_in=V0['dps_q'],
      ae=lambda: f'={P("dps")}*(1+{V("dps_g")})', note='Quarterly dividend $0.32 (declared Jun-2026 and Sep-2026). 2027E+: prior year × (1 + growth).')
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'])
    blank()

    # ------------------------------------------------------------------ RECON 1: EBIT -> adjusted EBIT
    S('sec_r1', 'RECONCILIATION: EBIT → ADJUSTED EBIT (company definition, as published from Q2 FY2018)', 'section',
      note='ADJUSTED EBIT — per the release reconciliations ("Reconciliation of Net Earnings to EBIT and Adjusted EBIT"); items in the labels of each period are in the cell comments of the cost-driver rows')
    S('o_op', 'EBIT (GAAP basis, company definition)', 'line_b', 'm1', all=lambda: f'={V("is_ebit")}')
    for k, lab, d in (('o_restr', '  (+) Restructuring charges', 'd_restr'), ('o_acq', '  (+) Acquisition, transaction, integration & business development costs', 'd_acq'),
                      ('o_pa', '  (+) Purchase accounting (inventory step-up, backlog amortization)', 'd_pa'),
                      ('o_gain', '  (+) (Gains) / losses on sales of businesses, properties, product lines; swaps', 'd_gain'),
                      ('o_impair', '  (+) Impairments', 'd_impair'), ('o_oth', '  (+) Other items', 'd_oadj')):
        S(k, lab, 'line', 'm1', all=lambda d=d: f'={V(d)}')
    S('o_tot', '  Total adjusting items (pre-tax)', 'line_b', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("o_restr")}),{nsum(["o_restr", "o_acq", "o_pa", "o_gain", "o_impair", "o_oth"])},"")')
    S('o_adj', '  = Adjusted EBIT (model bridge)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_tot")},"")',
      note='Rebuilt from the published reconciliation items; forecast = EBIT + forecast adjusting items (equals the segment build — check in the Group block).')
    S('o_adj_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company-published adjusted EBIT', 'memo', 'm1', data='adj_ebit_pub', flow=True)
    S('o_chk', '  Check: model bridge vs company-published (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),IF(ABS({V("o_adj")}-{V("o_pub")})<=0.15,0,ROUND({V("o_adj")}-{V("o_pub")},1)),"n/p")')
    S('o_def', '  Definition / basis (company adjusted definition in force)', 'text', 'gen',
      note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('o_adj_g', '  Adjusted EBIT y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental adjusted EBIT margin (Δ adjusted EBIT / Δ net sales)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: net earnings -> EBIT -> EBITDA -> adjusted EBITDA
    S('sec_r2', 'RECONCILIATION: NET EARNINGS → EBIT → EBITDA → ADJUSTED EBITDA (company definitions, as published)', 'section',
      note='EBITDA — net earnings + income taxes + interest expense − interest income = EBIT; + depreciation + amortization = EBITDA; + adjusting items not already in D&A = adjusted EBITDA')
    S('r_ni', 'Net earnings (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('r_tax', '  (+) Income taxes', 'line', 'm1', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest expense', 'line', 'm1', all=lambda: f'={V("is_int")}')
    S('r_intinc', '  (−) Interest income', 'line', 'm1', all=lambda: f'=-{V("is_intinc")}')
    S('r_gebit', '  = EBIT', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_tax")}+{V("r_int")}+{V("r_intinc")},"")')
    S('r_gebit_pub', '  Company-published EBIT', 'memo', 'm1', data='ebit_pub', flow=True)
    S('r_gebit_chk', '  Check: model vs company-published EBIT (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_gebit_pub")}),IF(ABS({V("r_gebit")}-{V("r_gebit_pub")})<=0.15,0,ROUND({V("r_gebit")}-{V("r_gebit_pub")},1)),"n/p")')
    S('r_dep', '  (+) Depreciation expense', 'line', 'm1', all=lambda: f'={V("d_dep")}')
    S('r_amort', '  (+) Amortization of intangible assets', 'line', 'm1', all=lambda: f'={V("d_amort")}')
    S('r_ebitda', '  = EBITDA', 'total', 'm1', all=lambda: f'=IF(AND(ISNUMBER({V("r_gebit")}),ISNUMBER({V("r_dep")})),{V("r_gebit")}+{V("r_dep")}+{V("r_amort")},"")')
    S('r_ebitda_pub', '  Company-published EBITDA', 'memo', 'm1', data='ebitda_pub', flow=True)
    S('r_ebitda_chk', '  Check: model vs company-published EBITDA (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda_pub")}),ISNUMBER({V("r_ebitda")})),IF(ABS({V("r_ebitda")}-{V("r_ebitda_pub")})<=0.15,0,ROUND({V("r_ebitda")}-{V("r_ebitda_pub")},1)),"n/p")')
    S('r_adjx', '  (+) Adjusting items not already in D&A (total adjusting items − backlog amortization)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("o_tot")}),{V("o_tot")}-N({V("d_indda")}),"")')
    S('r_adj', '  = Adjusted EBITDA', 'total', 'm1', all=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda")}),ISNUMBER({V("r_adjx")})),{V("r_ebitda")}+{V("r_adjx")},"")',
      note='Company definition (published from Q2 FY2018; = EBITDA before). Used for leverage (net debt / adjusted EBITDA) and EV / EBITDA.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_adj_pub', '  Company-published adjusted EBITDA', 'memo', 'm1', data='adj_ebitda_pub', flow=True)
    S('r_chk', '  Check: model vs company-published adjusted EBITDA (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("r_adj_pub")}),ISNUMBER({V("r_adj")})),IF(ABS({V("r_adj")}-{V("r_adj_pub")})<=0.15,0,ROUND({V("r_adj")}-{V("r_adj_pub")},1)),"n/p")')
    S('r_ebit_h', 'To adjusted EBIT, full-cost (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ddan', '  (−) Depreciation & amortization (total)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("d_dda")}),-{V("d_dda")},"")')
    S('r_ebit', '  = Adjusted EBIT, full-cost (adjusted EBITDA − total D&A; = adjusted EBIT except purchase-accounting amortization)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+{V("r_ddan")},"")',
      note='Woodward does not adjust out amortization, so adjusted EBIT is already full-cost; this line also charges the FY2018–19 L\'Orange backlog amortization.')
    S('r_ebit_m', '  Adjusted EBIT (full-cost) margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: acquisition, integration & restructuring costs (cash costs adjusted out; deducted in the DCF)', 'memo_calc', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("o_acq")}),{V("o_acq")}+{V("o_restr")},"")')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: NET EARNINGS / DILUTED EPS → ADJUSTED NET EARNINGS → ADJUSTED EPS (company definition)', 'section',
      note='ADJUSTED EPS — net earnings + pre-tax adjusting items − tax effect of the adjustments (incl. discrete tax items: US tax reform FY2018–19, German tax-rate change FY2025)')
    S('e_ni', 'Net earnings (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('e_op', '  (+) Adjusting items (pre-tax; bridge above)', 'line', 'm1', all=lambda: f'={V("o_tot")}')
    S('e_tax', '  (−) Tax effect of the adjustments & discrete tax items', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("e_pubni")}),{V("e_pubni")}-{V("e_ni")}-{V("e_op")},IF(ISNUMBER({V("e_ni")}),0,""))',
      fc=lambda: f'={V("is_tax")}-{V("e_adjtax")}',
      note='Historical: published adjusted net earnings − net earnings − pre-tax items (FY2011–17: none published; adjusted = GAAP). Forecast: GAAP tax − adjusted tax.')
    S('e_adjni', '  = Adjusted net earnings (model bridge)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("e_tax")}),{V("e_ni")}+{V("e_op")}+{V("e_tax")},"")')
    S('e_pubni', '  Company-published adjusted net earnings', 'memo', 'm1', data='adj_ni_pub', flow=True)
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted EPS – diluted ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted EPS ($)', 'eps_memo', 'ps', data='e_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0101,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_adjebt', '  Adjusted earnings before tax (adjusted EBIT − interest expense + interest income)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("o_adj")}),{V("o_adj")}-N({V("is_int")})+N({V("is_intinc")}),"")')
    S('e_adjtax', '  Adjusted income tax (adjusted earnings before tax − adjusted net earnings)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_adjni")}),ISNUMBER({V("e_adjebt")})),{V("e_adjebt")}-{V("e_adjni")},"")',
      fc=lambda: f'={V("e_adjebt")}*{V("e_rate")}')
    S('e_rate', '  Adjusted effective tax rate', 'pct', 'pct', all=ratio('e_adjtax', 'e_adjebt'), qe=lambda: f'={PT("pt_etr")}', ae=lambda: f'={V("is_etr")}',
      note='9M FY26 adjusted rate 21.9%; FY26 guidance ~22.5%. Forecast = GAAP effective tax rate.')
    S('e_def', '  Definition / basis (company adjusted EPS definition)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Net sales y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_aero', '  Aerospace segment sales y/y %', 'growth', 'pct', all=growth('aero_rev'))
    S('gm_ind', '  Industrial segment sales y/y %', 'growth', 'pct', all=growth('ind_rev'))
    S('gm_adjop', '  Adjusted EBIT y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  EBIT (GAAP) y/y %', 'growth', 'pct', all=growth('is_ebit'))
    S('gm_ni', '  Net earnings y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('gm_adjop_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_inc', '  Incremental adjusted EBIT margin (Δ adjusted EBIT / Δ net sales)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  EBIT margin (GAAP) %', 'pct', 'pct', all=ratio('is_ebit', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_sga', '  SG&A % of net sales', 'pct', 'pct', all=ratio('is_sga', 'is_rev'))
    S('gm_rd', '  R&D % of net sales', 'pct', 'pct', all=ratio('is_rd', 'is_rev'))
    blank()
