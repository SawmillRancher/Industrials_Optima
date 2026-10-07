"""Row specification of the STE Model sheet, part 1 (MLM template layout and process):
segment x revenue-type build (Healthcare / AST / Life Sciences x capital / consumables / service) -> organic growth bridge ->
M&A lever -> group revenue & adjusted operating income (FY27 outlook calibration) -> cost drivers -> income statement ->
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
def Q2v(key): return f'${Q2}${R[key]}'
def A1(key): return f'{Q1}{R[key]}'                      # Q1/27 actual
def A0(key): return f'{QC[(2026, 1)].c}{R[key]}'         # Q1/26 actual
def QE3(key): return f'({Q2}{R[key]}+{Q3}{R[key]}+{Q4}{R[key]})'

SEG = [('hc', 'Healthcare', 'HC', [('cap', 'Capital equipment'), ('cons', 'Consumables'), ('serv', 'Service')]),
       ('ast', 'Applied Sterilization Technologies (AST)', 'AST', [('serv', 'Service (contract sterilization & lab testing)'), ('cap', 'Capital equipment')]),
       ('ls', 'Life Sciences', 'LS', [('cap', 'Capital equipment'), ('cons', 'Consumables'), ('serv', 'Service')])]
LINES = [f'{s}_{t}' for s, _, _, ts in SEG for t, _ in ts]
SEGK = [s for s, _, _, _ in SEG]

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
    # ------------------------------------------------------------------ SEGMENT BUILD
    S('sec_seg', 'SEGMENT P&L — HEALTHCARE · AST · LIFE SCIENCES (revenue by type × segment operating margin)', 'section',
      note='SEGMENT BUILD — modelling logic (capital / consumables / service revenue by segment → segment operating income at the segment margin → + corporate = adjusted operating income → GAAP P&L)')
    blank()
    descr = {'hc': 'Healthcare (infection prevention consumables, sterilizers & washers, surgical tables / lights / OR integration, endoscopy (Cantel), repair & instrument services)',
             'ast': 'Applied Sterilization Technologies (contract EO / gamma / E-beam / X-ray sterilization and lab testing; "Isomedix" to FY2015)',
             'ls': 'Life Sciences (barrier & cleaning consumables, sterilizers / washers for pharma & biotech, service)'}
    for s, title, code, types in SEG:
        S(f'{s}_hdr', descr[s], 'block', note=f'{title.upper()} — modelling logic')
        for t, tl in types:
            key = f'{s}_{t}'
            S(key, f'  {tl} revenue', 'line', 'm1', data=f'ty_{key}', flow=True,
              qe=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})', ae=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})',
              note=('Revenue by type as published (release "Unaudited Supplemental Financial Data"). Q2–Q4/27E: prior-year quarter × (1 + growth). '
                    '2028E+: prior year × (1 + scenario lever).') if t == types[0][0] else None)
            S(key + '_g', '    y/y %', 'growth', 'pct', all=growth(key),
              qe=lambda key=key: f'={V(key + "_pre")}+{Q2v("cal_g")}',
              ae=lambda key=key, code=code, t=t: '=' + CH(SC[f'{code}_{t.upper()}'][CTX.col.year]),
              note='Q2–Q4/27E: Q1/27 y/y growth of the line + revenue-outlook calibration Δ (Group block). 2028E–2031E: scenario lever (Bull/Base/Bear table →).' if t == types[0][0] else None)
            S(key + '_pre', '    Q2–Q4/27E growth before revenue calibration (Q1/27 y/y)', 'driver', 'pct',
              qe=lambda key=key: f'=IFERROR({A1(key)}/{A0(key)}-1,0)')
        S(f'{s}_rev', f'  {title} — revenue', 'line_b', 'm1',
          all=lambda s=s, types=types: f'=IF(ISNUMBER({V(s + "_" + types[0][0])}),{"+".join(V(s + "_" + t) for t, _ in types)},"")')
        S(f'{s}_rev_g', '  Revenue y/y %', 'growth', 'pct', all=growth(f'{s}_rev'))
        S(f'{s}_mix', '  % of total revenue', 'pct', 'pct', all=ratio(f'{s}_rev', 'g_rev'))
        if s != 'ast':
            S(f'{s}_recur', '  Recurring (consumables + service) % of segment revenue', 'pct', 'pct',
              all=lambda s=s: f'=IF(ISNUMBER({V(s + "_cons")}),IFERROR(({V(s + "_cons")}+{V(s + "_serv")})/{V(s + "_rev")},""),"")')
        S(f'{s}_pub', f'  Memo: {title} revenue as published (segment data)', 'memo', 'm1', data=f'sr_{s}', flow=True)
        S(f'{s}_chk', '  Check: revenue by type vs segment revenue (should be 0)', 'check', 'm1',
          hist=lambda s=s: f'=IF(AND(ISNUMBER({V(s + "_rev")}),ISNUMBER({V(s + "_pub")})),IF(ABS({V(s + "_rev")}-{V(s + "_pub")})<=0.15,0,ROUND({V(s + "_rev")}-{V(s + "_pub")},1)),"")')
        S(f'{s}_oi', f'  Segment operating income ({"adjusted basis" if s else ""})', 'line', 'm1', data=f'so_{s}', flow=True,
          qe=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}', ae=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}',
          note=('Segment income before adjustments (company measure; FY2012–15: adjusted segment operating income from the release reconciliations). '
                'Forecast = revenue × segment margin.') if s == 'hc' else None)
        S(f'{s}_m', '  Segment operating margin %', 'pct', 'pct', all=ratio(f'{s}_oi', f'{s}_rev'),
          qe=lambda s=s: f'={V(s + "_m_pre")}+{Q2v("cal_m")}', ae=lambda s=s, code=code: '=' + CH(SC[f'{code}_M'][CTX.col.year]),
          note='Q2–Q4/27E: margin before calibration + adjusted-EPS-outlook calibration Δ (Group block). 2028E+: scenario lever.' if s == 'hc' else None)
        S(f'{s}_m_pre', '  Q2–Q4/27E margin before EPS-outlook calibration (prior-year quarter + Q1/27 y/y drift)', 'driver', 'pct',
          qe=lambda s=s: f'={P(s + "_m")}+IFERROR({A1(s + "_oi")}/{A1(s + "_rev")}-{A0(s + "_oi")}/{A0(s + "_rev")},0)')
        S(f'{s}_inc', '  Incremental segment margin (Δ operating income / Δ revenue)', 'pct', 'pct', all=incr(f'{s}_oi', f'{s}_rev'))
        blank()
    S('dn_hdr', 'Dental (Cantel, Jun-2021 – Sep-2024) — discontinued operations from the Q4 FY24 release; FY2023+ on the restated basis', 'block',
      note='DENTAL / OTHER — as originally reported in FY2022 (sold to Peak Rock Capital, 9-Sep-2024)')
    S('dn_rev', '  Dental revenue (FY2022 as reported; discontinued from FY2023 restated)', 'line', 'm1', data='sr_dental', flow=True, fc=lambda: '=0')
    S('dn_oi', '  Dental segment operating income', 'line', 'm1', data='so_dental', flow=True, fc=lambda: '=0')
    S('oth_rev', '  Corporate & other revenue (Defense & Industrial, FY2012–17)', 'line', 'm1', data='sr_oth', flow=True, fc=lambda: '=0')
    blank()
    S('co_hdr', 'Corporate costs (adjusted basis; reported separately from FY2019 — partially allocated to segments before)', 'block',
      note='CORPORATE — public-company, corporate functions, shared distribution & R&D, legacy pension; tariff refunds (FY27)')
    S('corp', '  Corporate operating loss (adjusted)', 'line', 'm1', data='so_corp', flow=True,
      qe=lambda: f'={P("corp")}*(1+{V("corp_g")})', ae=lambda: f'={V("is_rev")}*{V("corp_pct")}',
      note='FY2012–15: plug = adjusted operating income − adjusted segment operating income. Q2–Q4/27E: prior-year quarter × (1 + Q1/27 y/y). 2028E+: % of revenue.')
    S('corp_g', '  Corporate cost y/y %', 'growth', 'pct', all=growth('corp'), qe=lambda: f'=IFERROR({A1("corp")}/{A0("corp")}-1,0)')
    S('corp_pct', '  Corporate cost % of revenue', 'pct', 'pct', all=ratio('corp', 'is_rev'), ae_in=V0['corp_pct'])
    blank()
    S('mx_hdr', 'Revenue by type (all segments; recurring = consumables + service)', 'block', note='MIX — outputs')
    S('mx_cap', '  Capital equipment revenue', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("hc_cap")}),{V("hc_cap")}+{V("ast_cap")}+{V("ls_cap")},"")')
    S('mx_cons', '  Consumables revenue', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("hc_cons")}),{V("hc_cons")}+{V("ls_cons")},"")')
    S('mx_serv', '  Service revenue', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("hc_serv")}),{V("hc_serv")}+{V("ast_serv")}+{V("ls_serv")},"")')
    S('mx_rec', '  Recurring revenue % of total', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("mx_cons")}),IFERROR(({V("mx_cons")}+{V("mx_serv")})/{V("g_rev")},""),"")')
    S('mx_cap_g', '  Capital equipment y/y %', 'growth', 'pct', all=growth('mx_cap'))
    S('mx_rec_g', '  Recurring revenue y/y %', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("mx_cons")}+{V("mx_serv")})/({P("mx_cons")}+{P("mx_serv")})-1,"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ organic growth bridge
    S('og_hdr', 'Revenue growth bridge — as reported → organic → constant-currency organic (company definitions; table published from FY2017)', 'block',
      note='ORGANIC — acquisitions organic from the 13th month; divestitures removed from the prior-year base; FX at prior-year rates')
    S('og_rev', '  Revenue (as presented in the bridge; FY2023 – Q3 FY24 incl. Dental)', 'line', 'm1', data='org_rev', flow=True, fc=lambda: f'={V("is_rev")}')
    S('og_py', '  Prior-year revenue (as presented in the bridge)', 'line', 'm1', data='org_rev_py', flow=True, fc=lambda: f'={P("is_rev")}')
    S('og_acq', '  Impact of acquisitions ($m)', 'line', 'm1', data='org_acq', flow=True, qe_in=V0['qe_acq'], ae=lambda: f'={V("m_rev")}', note=V0['qe_acq_note'])
    S('og_div', '  Impact of divestitures (prior-year revenue removed, $m)', 'line', 'm1', data='org_div', flow=True, fc=lambda: '=0')
    S('og_fx', '  Impact of foreign currency ($m)', 'line', 'm1', data='org_fx', flow=True, qe_in=V0['qe_fx'], ae_in=0.0,
      note='Q2–Q4/27E: slightly favourable currency (FY27 outlook: as-reported growth 7–8% vs constant-currency organic 6–7%, incl. tuck-ins).')
    S('og_g', '  Revenue growth as reported %', 'growth', 'pct', data='org_g', fc=lambda: f'=IFERROR({V("og_rev")}/{V("og_py")}-1,"")')
    S('og_og', '  Organic growth % (published)', 'growth', 'pct', data='org_og',
      fc=lambda: f'=IFERROR(({V("og_rev")}-{V("og_acq")})/({V("og_py")}+{V("og_div")})-1,"")')
    S('og_cc', '  Constant-currency organic growth % (published)', 'growth', 'pct', data='org_ccog',
      fc=lambda: f'=IFERROR(({V("og_rev")}-{V("og_acq")}-{V("og_fx")})/({V("og_py")}+{V("og_div")})-1,"")',
      note="STERIS's headline growth KPI and guidance metric (FY27 outlook 6–7%). Historical as published; forecast = (revenue − acquisitions − FX) ÷ prior-year revenue − 1.")
    S('og_chk', '  Check: published CC organic growth vs (revenue − acquisitions − FX) ÷ (prior-year revenue + divestitures) − 1 (should be 0.0%)', 'check', 'pct',
      hist=lambda: (f'=IF(ISNUMBER({V("og_cc")}),IF(ABS(({V("og_rev")}-{V("og_acq")}-{V("og_fx")})/({V("og_py")}+{V("og_div")})-1-{V("og_cc")})<0.0015,0,'
                    f'ROUND(({V("og_rev")}-{V("og_acq")}-{V("og_fx")})/({V("og_py")}+{V("og_div")})-1-{V("og_cc")},3)),"n/p")'))
    for s in SEGK:
        S(f'og_{s}', f'  {dict((a, b) for a, b, _, _ in SEG)[s]} — constant-currency organic growth % (published)', 'growth', 'pct', data=f'org_{s}_ccog')
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — Healthcare / Life Sciences tuck-ins, unallocated; deals closed from 2028E)', 'block',
      note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=4.0, e26_in=0.0,
      note='Cantel ~4.4x sales ($4.6bn incl. debt on ~$1.0bn), BD surgical instrumentation ~$540m on ~$80m sales; tuck-ins 3–5x. 4.0x input.')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.05)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}',
      note='Mid-year convention. Treated as acquired (inorganic) revenue in the growth bridge in the year of acquisition and the following year (simplified: all years).')
    S('m_m', '  Adjusted operating margin of acquired businesses %', 'driver', 'pct', e26_in=0.0, ae_in=0.22)
    S('m_oi', '  Adjusted operating income from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.05)
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.55,
      note='PPAs: Cantel 82% of consideration (excl. debt) in intangibles, BD instrumentation 56%, Synergy 35% (asset-heavy AST / HSS).')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=10)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)',
      note='Non-cash; excluded from adjusted operating income and adjusted EPS (company definition).')
    blank()

    # ------------------------------------------------------------------ group total & outlook calibration
    S('g_hdr', 'Group Total — revenue & adjusted operating income (segment build) → FY27 outlook calibration', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Revenue (segment build)', 'total', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("hc_rev")}),{V("hc_rev")}+{V("ast_rev")}+{V("ls_rev")}+N({V("dn_rev")})+N({V("oth_rev")}),{V("is_rev")})',
      fc=lambda: f'={V("hc_rev")}+{V("ast_rev")}+{V("ls_rev")}+N({V("m_rev")})',
      note='Σ segment revenue by type (+ Dental FY2022, Corporate & other FY2012–17, future acquisitions from 2028E).')
    S('g_rev_g', '  Revenue y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs consolidated revenue (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=0.25,0,ROUND({V("g_rev")}-{V("is_rev")},1)),"")')
    S('g_adj', 'Adjusted operating income (segment build)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("hc_oi")}),{V("hc_oi")}+{V("ast_oi")}+{V("ls_oi")}+N({V("dn_oi")})+{V("corp")}+N({V("m_oi")}),"")',
      note="Σ segment operating income + corporate (+ future acquisitions). STERIS's primary profit KPI (\"adjusted income from operations\"); drives the GAAP P&L below.")
    S('g_adjm', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('g_adj', 'is_rev'))
    S('g_adj_g', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('g_adj'))
    S('g_chk_adj', '  Check: segment build vs adjusted operating income bridge (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_adj")}),ISNUMBER({V("o_adj")})),IF(ABS({V("g_adj")}-{V("o_adj")})<=0.15,0,ROUND({V("g_adj")}-{V("o_adj")},1)),"")')
    S('cal_guid', '  Memo: FY27 revenue outlook (scenario end-point = FY2026 × (1 + guided as-reported growth))', 'memo', 'm1',
      e26=lambda: f'={Y("is_rev", 2026)}*(1+{CH(SC["out_g"])})', note=V0['rev_guid_note'])
    S('cal_pre', '  Revenue before calibration (Q2–Q4/27E helper)', 'line', 'm1', qe=lambda: '=' + '+'.join(f'{P(k)}*(1+{V(k + "_pre")})' for k in LINES))
    S('cal_sens', '  Revenue sensitivity to +1.00 of growth (Q2–Q4/27E helper)', 'line', 'm1', qe=lambda: '=' + '+'.join(P(k) for k in LINES))
    S('cal_g', '  Outlook calibration: Δ y/y growth applied to all revenue lines (Q2–Q4/27E)', 'driver', 'pct',
      qe=lambda: (f'=({V("cal_guid", E26)}-{A1("g_rev")}-({QE3("cal_pre")}))/({QE3("cal_sens")})' if CTX.col.q == 2 else f'={Q2v("cal_g")}'),
      note='Solves the uniform growth shift (vs Q1/27 y/y rates) so that FY27 revenue = the outlook end-point for the active scenario.')
    S('cal_rev_chk', '  Check: FY27 revenue vs outlook end-point (should be 0)', 'check', 'm1', e26=lambda: f'=ROUND({V("g_rev")}-{V("cal_guid")},1)')
    S('cal_eps', '  Memo: FY27 adjusted EPS outlook (scenario end-point, $)', 'eps_memo', 'ps', e26=lambda: '=' + CH(SC['out_eps']), note=V0['eps_guid_note'])
    S('cal_ni', '  Adjusted net income required (FY27E adjusted diluted shares × EPS outlook)', 'memo_calc', 'm1', e26=lambda: f'={V("cal_eps")}*{V("e_sh")}')
    S('cal_oi', '  Q2–Q4/27E adjusted operating income required ((NI − Q1 actual + NCI) ÷ (1 − tax rate) + non-operating expense)', 'memo_calc', 'm1',
      e26=lambda: (f'=({V("cal_ni")}-{A1("e_adjni")}+({QE3("is_nci")}))/(1-{PT("pt_etr")})'
                   f'+({QE3("is_int")})+({QE3("is_onop")})-({QE3("e_nonop")})'))
    S('cal_oi_pre', '  Adjusted operating income before margin calibration (Q2–Q4/27E helper)', 'line', 'm1',
      qe=lambda: '=' + '+'.join(f'{V(s + "_rev")}*{V(s + "_m_pre")}' for s in SEGK) + f'+{V("corp")}')
    S('cal_segrev', '  Segment revenue (Q2–Q4/27E helper)', 'line', 'm1', qe=lambda: '=' + '+'.join(V(s + '_rev') for s in SEGK))
    S('cal_m', '  Outlook calibration: Δ segment operating margin (Q2–Q4/27E)', 'driver', 'pct',
      qe=lambda: (f'=({V("cal_oi", E26)}-({QE3("cal_oi_pre")}))/({QE3("cal_segrev")})' if CTX.col.q == 2 else f'={Q2v("cal_m")}'),
      note='Solves the uniform margin shift so that FY27 adjusted EPS = the outlook end-point for the active scenario.')
    S('cal_eps_chk', '  Check: FY27 adjusted EPS vs outlook end-point (should be 0.00)', 'check', 'ps', e26=lambda: f'=ROUND({V("e_eps")}-{V("cal_eps")},2)')
    S('cal_geps', '  Memo: FY27 GAAP diluted EPS outlook (continuing operations, scenario end-point, $)', 'eps_memo', 'ps', e26=lambda: '=' + CH(SC['out_geps']))
    S('cal_geps_d', '  Model FY27 GAAP diluted EPS − outlook end-point ($; information, not forced)', 'eps_memo', 'ps', e26=lambda: f'={V("eps_dilc")}-{V("cal_geps")}')
    S('cal_fcf', '  Memo: FY27 free cash flow outlook (~$800m)', 'memo', 'm1', e26=lambda: f'={PT("pt_fcf")}')
    S('cal_fcf_d', '  Model FY27 free cash flow − outlook (information)', 'memo_calc', 'm1', e26=lambda: f'={V("fcf")}-{V("cal_fcf")}')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A & adjusting items', 'block', note='COST DRIVERS — inputs that drive forecast cost lines (Q2–Q4/27E: FY27 point estimates less Q1/27)')
    S('d_dda', '  Depreciation, depletion & amortization (total; cash-flow statement)', 'line', 'm1', data='cf_dda', flow=True,
      fc=lambda: f'={V("d_amort")}+{V("d_dep")}', note='10-K / 10-Q cash-flow statement (XBRL, year to date; discrete quarters derived).')
    S('d_amort', '  Amortization of acquired intangible assets (adjusted out)', 'line', 'm1', data='oa_amort', flow=True,
      qe=lambda: f'=({PT("pt_amort")}-{A1("d_amort")})/3', ae=lambda: f'={V("d_amort_sch")}+N({V("m_amort")})',
      note='Q2–Q4/27E: FY27 point estimate less Q1/27. 2028E+: 10-K schedule of intangibles held at 31-Mar-2026 + future-acquisition amortization.')
    S('d_amort_sch', '  Amortization schedule — intangibles held at 31-Mar-2026 (10-K, input)', 'driver', 'm1', ae_in=V0['amort_sched'], note=V0['amort_note'])
    S('d_dep', '  Depreciation & other amortization (total D&A − acquired-intangible amortization)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("d_dda")}),ISNUMBER({V("d_amort")})),{V("d_dda")}-{V("d_amort")},"")',
      qe=lambda: f'=({PT("pt_dep")}-{A1("d_dep")})/3', ae=lambda: f'={V("is_rev")}*{V("d_dep_pct")}')
    S('d_dep_pct', '  Depreciation & other amortization % of revenue', 'pct', 'pct', all=ratio('d_dep', 'is_rev'), ae_in=V0['dep_pct'],
      note='Rising with the capex step-up (North Carolina chemistries and Mentor, OH sterility-assurance plants; AST capacity).')
    S('d_sga', '  SG&A % of revenue (incl. acquired-intangible amortization in SG&A)', 'pct', 'pct', all=ratio('is_sga', 'is_rev'),
      qe=lambda: f'={P("d_sga")}+IFERROR({A1("is_sga")}/{A1("is_rev")}-{A0("is_sga")}/{A0("is_rev")},0)', ae_in=V0['sga_pct'],
      note='Q2–Q4/27E: prior-year quarter ratio + Q1/27 y/y drift; 2028E+ input. Gross profit is implied: GAAP operating income (from the adjusted build) + operating expenses.')
    S('d_rd', '  R&D % of revenue', 'pct', 'pct', all=ratio('is_rd', 'is_rev'), qe=lambda: f'=IFERROR({A1("is_rd")}/{A1("is_rev")},"")', ae_in=V0['rd_pct'])
    S('d_sbc', '  Share-based compensation (cash-flow statement)', 'line', 'm1', data='cf_sbc', flow=True,
      qe=lambda: f'={P("d_sbc")}*(1+IFERROR({A1("d_sbc")}/{A0("d_sbc")}-1,0))', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}',
      note='Q2–Q4/27E: prior-year quarter × Q1/27 y/y (annual grants in Q2); 2028E+: % of revenue. STERIS does not adjust out share-based compensation.')
    S('d_sbc_pct', '  Share-based compensation % of revenue', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_acq', '  Acquisition & integration-related charges (adjusted out; incl. contingent-consideration fair value)', 'line', 'm1', data='oa_acq', flow=True,
      qe_in={2: 0.5, 3: 0.5, 4: 0.5}, ae=lambda: f'=0.5+{V("m_spend")}*{V("d_acq_pct")}', note='FY27 outlook $0.01 per share. 2028E+: $0.5m + % of acquisition spend.')
    S('d_acq_pct', '  Acquisition & integration charges % of acquisition spend', 'pct', 'pct', ae_in=0.02)
    S('d_restr', '  Restructuring charges (adjusted out)', 'line', 'm1', data='oa_restr', flow=True, qe_in=V0['qe_restr'], ae_in=V0['ae_restr'], note=V0['restr_note'])
    S('d_step', '  Amortization of inventory & property step-up (adjusted out)', 'line', 'm1', data='oa_stepup', flow=True, qe_in={2: 1.5, 3: 1.5, 4: 1.5}, ae_in=2.0)
    S('d_oadj', '  Other adjusted-out items (tax restructuring, divestitures, impairment, litigation, COVID-19, other)', 'line', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("o_taxr")}),{nsum(["o_taxr", "o_div", "o_imp", "o_lit", "o_cov", "o_oth"])},"")',
      qe_in={2: 0.3, 3: 0.3, 4: 0.3}, ae_in=0.0, note='FY27 outlook "other unusual items" $0.02 per share (tax restructuring ~$0.3m a quarter + equity-method intangible amortization, non-operating).')
    S('d_nonadj', '  Non-operating adjustments (pre-tax: (gain) / loss on businesses & investments, convertible-debt fair value, equity-method intangible amortization)', 'line', 'm1',
      data='na_nonop', flow=True, qe_in={2: 0.8, 3: 0.8, 4: 0.8}, ae_in=3.2)
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF INCOME (US GAAP; continuing operations)', 'section',
      note='CONSOLIDATED IS — forecast logic (operating income = adjusted operating income − adjusting items; gross profit implied)')
    S('is_rev', 'Revenues', 'total', 'm1', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the segment build.')
    S('is_cogs', 'Cost of revenues', 'line', 'm1', data='cogs', flow=True, fc=lambda: f'={V("is_rev")}-{V("is_gp")}')
    S('is_gp', 'Gross profit', 'line_b', 'm1', hist=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_rev")}-{V("is_cogs")},"")',
      fc=lambda: f'={V("is_op")}+{V("is_sga")}+{V("is_rd")}+{V("is_restr")}+{V("is_oth")}',
      note='Forecast = operating income + operating expenses (implied by the adjusted operating income build).')
    S('is_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('is_sga', 'Selling, general & administrative', 'line', 'm1', data='sga', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_sga")}')
    S('is_rd', 'Research & development', 'line', 'm1', data='rd', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_rd")}')
    S('is_restr', 'Restructuring expenses', 'line', 'm1', data='restr', flow=True, fc=lambda: f'={V("d_restr")}',
      note='Restructuring charges in cost of revenues are part of gross profit; the adjusted-out total is in the bridge below.')
    S('is_oth', 'Other operating items (Illinois EO settlement FY25; goodwill impairment FY17; class action FY11)', 'line', 'm1', data='oth_opex', flow=True, fc=lambda: '=0')
    S('is_op', 'Income from operations', 'total', 'm1', data='op', flow=True,
      fc=lambda: f'={V("g_adj")}-{V("d_amort")}-{V("d_acq")}-{V("d_restr")}-{V("d_step")}-{V("d_oadj")}',
      note='Forecast = adjusted operating income − amortization of acquired intangibles − other adjusting items.')
    S('is_opm', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('is_int', 'Interest expense', 'line', 'm1', data='int_exp', flow=True,
      qe=lambda: f'=({PT("pt_int")}-{A1("is_int")})/3',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_rev")}*{V("ds_r_rev")}+{V("ds_fees")}',
      note='Q2–Q4/27E: FY27 point estimate less Q1/27. 2028E+ = rate × opening notes + rate × opening revolver / CP + fees (no circularity). Release / XBRL (FY2012–23 quarters).')
    S('is_onop', 'Other non-operating (income) expense, net (interest & misc. income, gains / losses on businesses)', 'line', 'm1', data='onop', flow=True,
      qe=lambda: f'=({PT("pt_onop")}-{A1("is_onop")})/3', ae=lambda: f'=-{P("cf_end")}*{V("ds_r_cash")}+{V("d_nonadj")}')
    S('is_ebt', 'Income from continuing operations before income taxes', 'line_b', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("is_op")}),{V("is_op")}-{V("is_int")}-N({V("is_onop")}),"")')
    S('is_tax', 'Income tax expense', 'line', 'm1', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate (continuing operations)', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='FY27 outlook ~25% (Q1/27 26.5% GAAP, 25.9% adjusted). Irish parent; US ~73% of revenue.')
    S('is_nic', 'Income from continuing operations, net of tax', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_disc', 'Income (loss) from discontinued operations (Dental), net of tax', 'line', 'm1', data='disc', flow=True, fc=lambda: '=0')
    S('is_ni', 'Net income', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_nic")}),{V("is_nic")}+N({V("is_disc")}),"")')
    S('is_nci', '  Less: net income attributable to noncontrolling interests', 'line', 'm1', data='nci', flow=True,
      qe=lambda: f'={A1("is_nci")}', ae=lambda: f'={P("is_nci")}*1.05')
    S('is_nia', 'Net income attributable to shareholders', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_ni")}),{V("is_ni")}-N({V("is_nci")}),"")')
    S('is_nica', '  Net income from continuing operations attributable to shareholders', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("is_nia")}),{V("is_nia")}-N({V("is_disc")}),"")')
    S('is_ni_chk', '  Check: net income attributable vs reported (should be 0; ±0.1 rounding)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_nia")}-{V("is_ni_pub")})<=0.15,0,ROUND({V("is_nia")}-{V("is_ni_pub")},1)),"")')
    S('is_ni_pub', '  Memo: net income attributable to shareholders as reported', 'memo', 'm1', data='ni_attr', flow=True)
    S('is_dda', '  Memo: depreciation, depletion & amortization (total)', 'memo_calc', 'm1', all=lambda: f'={V("d_dda")}')
    S('is_sbc', '  Memo: share-based compensation', 'memo_calc', 'm1', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share — STERIS plc ordinary shares; STERIS Corp common shares to Nov-2015)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={A1("bs_shares")}-${E26}${R["bb_sh"]}/3*{ {2: 0.5, 3: 1.5, 4: 2.5}[CTX.col.q] }+${E26}${R["bb_iss"]}/3*{ {2: 0.5, 3: 1.5, 4: 2.5}[CTX.col.q] }',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q2–Q4/27E: shares outstanding at 30-Jun-2026 − Q2–Q4 buybacks phased evenly (mid-quarter) + equity-plan issuance. 2028E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({A1("sh_dil")}-{A1("sh_basic")})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dilc', 'EPS – diluted, continuing operations ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_nica")}/{V("sh_dil")},""),"")',
      note='Net income from continuing operations attributable / weighted diluted shares (±$0.01 vs reported).')
    S('eps_dilc_g', '  EPS – diluted (continuing) y/y %', 'growth', 'pct', all=growth('eps_dilc'))
    S('eps_pub', '  Memo: EPS – diluted, continuing operations as reported ($)', 'eps_memo', 'ps', data='eps_d_cont')
    S('eps_chk', '  Check: model vs reported diluted EPS, continuing (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dilc")})),IF(ABS({V("eps_dilc")}-{V("eps_pub")})<=0.0101,0,ROUND({V("eps_dilc")}-{V("eps_pub")},2)),"n/p")')
    S('eps_dil', 'EPS – diluted, total incl. discontinued operations ($)', 'eps', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_nia")}/{V("sh_dil")},""),"")')
    S('dps', '  Dividends declared per share ($)', 'line', 'ps', data='dps', flow=True, qe_in={2: V0['dps_q'], 3: V0['dps_q'], 4: V0['dps_q']},
      ae=lambda: f'={P("dps")}*(1+{V("dps_g")})', note='Quarterly dividend $0.63 from Q1/27 (raised each August). 2028E+: prior year × (1 + growth).')
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=0.08)
    blank()

    # ------------------------------------------------------------------ RECON 1: GAAP operating income -> adjusted operating income
    S('sec_r1', 'RECONCILIATION: GAAP INCOME FROM OPERATIONS → ADJUSTED INCOME FROM OPERATIONS (company definition, as published)', 'section',
      note='ADJUSTED OPERATING INCOME — per the release Non-GAAP tables ("Income from Operations" column) and the segment-data adjustments')
    S('o_op', 'Income from operations (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_op")}')
    S('o_amort', '  (+) Amortization (and impairment) of acquired intangible assets', 'line', 'm1', all=lambda: f'={V("d_amort")}')
    S('o_acq', '  (+) Acquisition & integration-related charges (incl. contingent-consideration fair value)', 'line', 'm1', all=lambda: f'={V("d_acq")}')
    S('o_step', '  (+) Amortization of inventory & property step-up to fair value', 'line', 'm1', all=lambda: f'={V("d_step")}')
    S('o_restr', '  (+) Restructuring charges', 'line', 'm1', all=lambda: f'={V("d_restr")}')
    S('o_taxr', '  (+) Redomiciliation & tax restructuring costs', 'line', 'm1', data='oa_taxrestr', flow=True, fc=lambda: '=0')
    S('o_div', '  (+) Net loss (gain) on divestiture of businesses', 'line', 'm1', data='oa_divest', flow=True, fc=lambda: '=0')
    S('o_imp', '  (+) Goodwill impairment', 'line', 'm1', data='oa_impair', flow=True, fc=lambda: '=0')
    S('o_lit', '  (+) Litigation & settlements (SYSTEM 1 rebate & class action FY2012–13; Illinois EO settlement FY2025)', 'line', 'm1', data='oa_litig', flow=True, fc=lambda: '=0')
    S('o_cov', '  (+) COVID-19 incremental costs (FY2020–21)', 'line', 'm1', data='oa_covid', flow=True, fc=lambda: '=0')
    S('o_oth', '  (+) Other (pension settlement FY2016, US tax reform bonus FY2018, S1E inventory reserve FY2012; forecast: other unusual items)', 'line', 'm1',
      data='oa_other', flow=True, fc=lambda: f'={V("d_oadj")}')
    S('o_tot', '  Total adjusting items (pre-tax)', 'line_b', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("o_op")}),{nsum(["o_amort", "o_acq", "o_step", "o_restr", "o_taxr", "o_div", "o_imp", "o_lit", "o_cov", "o_oth"])},"")')
    S('o_adj', '  = Adjusted income from operations (model bridge)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_tot")},"")',
      note='Rebuilt from the published reconciliation lines; forecast = GAAP operating income + forecast adjusting items (equals the segment build — check in the Group block).')
    S('o_adj_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company-published adjusted income from operations', 'memo', 'm1', data='adj_op_pub', flow=True)
    S('o_chk', '  Check: model bridge vs company-published (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),IF(ABS({V("o_adj")}-{V("o_pub")})<=0.15,0,ROUND({V("o_adj")}-{V("o_pub")},1)),"n/p")')
    S('o_def', '  Definition / basis (company adjusted definition and presentation basis in force)', 'text', 'gen',
      note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('o_adj_g', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental adjusted operating margin (Δ adjusted operating income / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    S('o_gp_h', 'Adjusted gross profit:', 'sub', 'gen')
    S('o_gpadj', '  (+) Adjusting items in cost of revenues (step-up, restructuring, amortization, other)', 'line', 'm1', data='ga_tot', flow=True)
    S('o_agp', '  = Adjusted gross profit (model)', 'line_b', 'm1', hist=lambda: f'=IF(ISNUMBER({V("o_gpadj")}),{V("is_gp")}+{V("o_gpadj")},"")')
    S('o_agp_m', '  Adjusted gross margin %', 'pct', 'pct', all=ratio('o_agp', 'is_rev'))
    S('o_agp_pub', '  Company-published adjusted gross profit', 'memo', 'm1', data='adj_gp_pub', flow=True)
    S('o_agp_chk', '  Check: model vs company-published adjusted gross profit (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("o_agp_pub")}),ISNUMBER({V("o_agp")})),IF(ABS({V("o_agp")}-{V("o_agp_pub")})<=0.15,0,ROUND({V("o_agp")}-{V("o_agp_pub")},1)),"n/p")')
    blank()

    # ------------------------------------------------------------------ RECON 2: net income -> EBITDA -> adjusted EBITDA (model)
    S('sec_r2', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (model definition; STERIS does not publish EBITDA)', 'section',
      note='ADJUSTED EBITDA — model bridge on the company items: GAAP net income + NCI + tax + non-operating = operating income; + total D&A = EBITDA; + adjusting items other than acquired-intangible amortization')
    S('r_nica', 'Net income from continuing operations attributable to shareholders (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_nica")}')
    S('r_nci', '  (+) Net income attributable to noncontrolling interests', 'line', 'm1', all=lambda: f'=N({V("is_nci")})')
    S('r_tax', '  (+) Income tax expense', 'line', 'm1', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest expense', 'line', 'm1', all=lambda: f'={V("is_int")}')
    S('r_onop', '  (+) Other non-operating expense (income), net', 'line', 'm1', all=lambda: f'=N({V("is_onop")})')
    S('r_op', '  = Income from operations', 'line_b', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_nica")}),{V("r_nica")}+{V("r_nci")}+{V("r_tax")}+N({V("r_int")})+{V("r_onop")},"")')
    S('r_dda', '  (+) Depreciation, depletion & amortization (total)', 'line', 'm1', all=lambda: f'={V("d_dda")}')
    S('r_ebitda', '  = EBITDA (model)', 'total', 'm1', all=lambda: f'=IF(AND(ISNUMBER({V("r_op")}),ISNUMBER({V("r_dda")})),{V("r_op")}+{V("r_dda")},"")')
    S('r_ebitda_chk', '  Check: rebuilt operating income vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_op")}),IF(ABS({V("r_op")}-{V("is_op")})<=0.15,0,ROUND({V("r_op")}-{V("is_op")},1)),"")')
    S('r_adjx', '  (+) Adjusting items excl. acquired-intangible amortization (already in D&A)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("o_tot")}),{V("o_tot")}-{V("o_amort")},"")')
    S('r_adj', '  = Adjusted EBITDA (model: adjusted income from operations + depreciation & other amortization)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda")}),ISNUMBER({V("r_adjx")})),{V("r_ebitda")}+{V("r_adjx")},"")',
      note='Used for leverage (net debt / adjusted EBITDA) and EV / EBITDA. Accelerated depreciation in restructuring (FY27–30 plan) is excluded once in restructuring.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_chk', '  Check: adjusted EBITDA − depreciation & other amortization vs company adjusted operating income (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("r_adj")}),ISNUMBER({V("o_pub")})),IF(ABS({V("r_adj")}-{V("d_dep")}-{V("o_pub")})<=0.15,0,ROUND({V("r_adj")}-{V("d_dep")}-{V("o_pub")},1)),"n/p")')
    S('r_ebit_h', 'To adjusted EBIT (full-cost; for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ddan', '  (−) Depreciation, depletion & amortization (total)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_dda")}),-{V("r_dda")},"")')
    S('r_ebit', '  = Adjusted EBIT (model; adjusted EBITDA − total D&A = adjusted operating income − acquired-intangible amortization)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+{V("r_ddan")},"")',
      note='Acquired-intangible amortization deducted, so returns are on a full-cost basis.')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: acquisition, integration & restructuring charges (cash costs adjusted out; deducted in the DCF)', 'memo_calc', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("o_acq")}),{V("o_acq")}+{V("o_restr")},"")')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: GAAP NET INCOME / DILUTED EPS → ADJUSTED NET INCOME → ADJUSTED EPS (continuing operations, company definition)', 'section',
      note='ADJUSTED EPS — GAAP net income from continuing operations attributable + pre-tax adjusting items − tax effect of the adjustments (incl. discrete tax items)')
    S('e_ni', 'Net income from continuing operations attributable to shareholders (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_nica")}')
    S('e_op', '  (+) Operating adjusting items (pre-tax; bridge above)', 'line', 'm1', all=lambda: f'={V("o_tot")}')
    S('e_nonop', '  (+) Non-operating adjusting items (pre-tax)', 'line', 'm1', all=lambda: f'=N({V("d_nonadj")})')
    S('e_tax', '  (−) Tax effect of the adjustments & discrete tax items', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("e_pubni")}),{V("e_pubni")}-{V("e_ni")}-{V("e_op")}-{V("e_nonop")},"")',
      fc=lambda: f'={V("is_tax")}-{V("e_adjtax")}',
      note=('Historical: published adjusted net income less GAAP net income and the pre-tax items ("net impact of adjustments after tax" less the pre-tax amounts; '
            'FY2012–15 releases show the items net of tax). Includes discrete tax items (European / Canadian tax restructuring, US tax reform). Forecast: GAAP tax − adjusted tax.'))
    S('e_adjni', '  = Adjusted net income, continuing operations (model bridge)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("e_tax")}),{V("e_ni")}+{V("e_op")}+{V("e_nonop")}+{V("e_tax")},"")')
    S('e_pubni', '  Company-published adjusted net income (continuing operations, attributable)', 'memo', 'm1', data='adj_ni_pub', flow=True)
    S('e_sh_in', '  Adjusted diluted shares where different from GAAP (net-loss quarters; input)', 'memo', 'm1', data='e_sh_in')
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("e_sh_in")}),{V("e_sh_in")},IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},""))')
    S('e_eps', 'Adjusted EPS – diluted, continuing operations ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted EPS, continuing operations ($)', 'eps_memo', 'ps', data='e_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0101,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_adjebt', '  Adjusted income before tax (adjusted operating income − non-operating expense + non-operating adjustments)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("o_adj")}),{V("o_adj")}-N({V("is_int")})-N({V("is_onop")})+{V("e_nonop")},"")')
    S('e_adjtax', '  Adjusted income tax (adjusted income before tax − adjusted net income − NCI)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_adjni")}),ISNUMBER({V("e_adjebt")})),{V("e_adjebt")}-{V("e_adjni")}-N({V("is_nci")}),"")',
      fc=lambda: f'={V("e_adjebt")}*{V("e_rate")}')
    S('e_rate', '  Adjusted effective tax rate', 'pct', 'pct', all=ratio('e_adjtax', 'e_adjebt'), qe=lambda: f'={PT("pt_etr")}', ae=lambda: f'={V("is_etr")}',
      note='Q1/27 adjusted rate 25.9%; FY27 outlook ~25%. Forecast = GAAP effective tax rate.')
    S('e_def', '  Definition / basis (company adjusted EPS definition and presentation basis)', 'text', 'gen')
    S('e_orig_h', '  As originally reported (incl. Dental) — FY2023 to FY2024, before the discontinued-operations recast:', 'sub', 'gen')
    S('e_disc', '    Adjusted income from discontinued operations (Dental), net of tax (Q4 FY24 release recast)', 'memo', 'm1', data='e_disc_adj', flow=True)
    S('e_eps_orig', '    Adjusted EPS – total company incl. Dental (model = (adjusted NI continuing + Dental adjusted NI) ÷ diluted shares)', 'eps_memo', 'ps',
      hist=lambda: f'=IF(ISNUMBER({V("e_disc")}),({V("e_adjni")}+{V("e_disc")})/{V("e_sh")},"")')
    S('e_pub_orig', '    Company-published adjusted EPS as originally reported (incl. Dental; Q4 FY24 / FY2024: total company)', 'eps_memo', 'ps', data='e_pub_orig')
    S('e_chk_orig', '    Check: model vs originally reported (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub_orig")}),ISNUMBER({V("e_eps_orig")})),IF(ABS({V("e_eps_orig")}-{V("e_pub_orig")})<=0.0101,0,ROUND({V("e_eps_orig")}-{V("e_pub_orig")},2)),"n/p")')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Revenue y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_org', '  Constant-currency organic growth %', 'growth', 'pct', all=lambda: f'=IF(ISNUMBER({V("og_cc")}),{V("og_cc")},"")' if CTX.col.prior else None)
    S('gm_rec', '  Recurring revenue y/y %', 'growth', 'pct', all=lambda: f'={V("mx_rec_g")}' if CTX.col.prior else None)
    S('gm_cap', '  Capital equipment revenue y/y %', 'growth', 'pct', all=growth('mx_cap'))
    S('gm_adjop', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Income from operations (GAAP) y/y %', 'growth', 'pct', all=growth('is_op'))
    S('gm_ni', '  Net income (continuing, attributable) y/y %', 'growth', 'pct', all=growth('is_nica'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('gm_agm', '  Adjusted gross margin %', 'pct', 'pct', all=ratio('o_agp', 'is_rev'))
    S('gm_adjop_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_inc', '  Incremental adjusted operating margin (Δ adjusted operating income / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('gm_net_m', '  Net margin (continuing, attributable) %', 'pct', 'pct', all=ratio('is_nica', 'is_rev'))
    S('gm_sga', '  SG&A % of revenue', 'pct', 'pct', all=ratio('is_sga', 'is_rev'))
    S('gm_rd', '  R&D % of revenue', 'pct', 'pct', all=ratio('is_rd', 'is_rev'))
    blank()
