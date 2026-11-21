"""Row specification of the FDX Model sheet, part 1 (MLM template layout and process):
package build by service (average daily volume x revenue per package x operating days) for Express U.S. Domestic and Express
International -> segment revenue -> adjusted segment operating income at the segment margin -> + corporate = adjusted operating
income -> group total & calendar-2026 guidance calibration -> legacy segments (memo) -> cost drivers -> income statement ->
GAAP-to-adjusted bridges -> growth & margins.

Calendar-basis columns carry the build and the forecast; legacy fiscal-year columns show the same service lines and statements as
originally reported (FedEx Freight consolidated). Rows marked basis='C' / 'L' are filled on one basis only."""
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
def ACT(key): return f'SUM({Q1}{R[key]}:{Q3}{R[key]})'    # nine months 2026 actual (Q1-Q3/26)
def ACT0(key): return f'SUM({PQ1}{R[key]}:{PQ3}{R[key]})' # nine months 2025 (Q1-Q3/25)
def B1(key): return f'{LQ}{R[key]}'                       # 30-Sep-2026 balance
def WD(key, a=Q1, b=Q3):                                  # day-weighted sum of a per-day statistic over quarters a..b
    return f'SUMPRODUCT({a}{R[key]}:{b}{R[key]},{a}{R["days"]}:{b}{R["days"]})'
def chk0(a, b, tol=0.6, nd=0):
    return f'IF(ABS({a}-({b}))<={tol},0,ROUND({a}-({b}),{nd}))'

US = [('pri', 'U.S. priority'), ('def', 'U.S. deferred'), ('gnd', 'U.S. ground')]
INTL = [('ip', 'International priority'), ('ie', 'International economy'), ('id', 'International domestic')]
PKG = [k for k, _ in US + INTL]
OTHL = ['r_ufrt', 'r_uoth', 'r_ifrt', 'r_ioth']
OITEMS = ['o_restr', 'o_acq', 'o_impair', 'o_legal', 'o_mtm', 'o_oth', 'o_gain']

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of the calendar-2026 guidance.'))
    r = 11
    SCEN_ROWS.append((r, 'out_hdr', V0['out_hdr'], 'High', 'Mid', 'Low', V0['out_note'])); r += 1
    for key, lab, (hi, mid, lo), nf, note in V0['outlook']:
        SC[key] = r; SCEN_ROWS.append((r, 'out', lab, hi, mid, lo, note, nf)); r += 1
    r += 1
    SCEN_ROWS.append((r, 'pt_hdr', 'Q4/26E and calendar-2026 point estimates (all cases)', None, None, None, None)); r += 1
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
    yr = lambda: CTX.col.year
    # ------------------------------------------------------------------ OPERATING BUILD
    S('sec_seg', 'OPERATING BUILD — EXPRESS U.S. DOMESTIC · EXPRESS INTERNATIONAL (average daily package volume × revenue per package × operating days)', 'section',
      note=('OPERATING BUILD — modelling logic (packages: average daily volume × yield × operating days → segment revenue → adjusted segment operating income at the '
            'segment margin → + corporate = adjusted operating income → GAAP P&L). Calendar columns are continuing operations; legacy fiscal-year columns are as originally reported.'))
    blank()
    S('days', 'Operating days (weekdays; FedEx Express / Federal Express operating weekdays in the legacy columns)', 'driver', 'gen', data='days',
      qe_in=V0['days_q4'], e26=lambda: f'=SUM({Q1}{R["days"]}:{QE}{R["days"]})', ae_in=V0['days'],
      note='Company: 63 / 64 / 64 / 64 operating days in calendar 2026 and 63 / 64 / 64 / 63 (254) in 2027 (recast exhibits). 2028E+: 255 (assumption).')
    blank()

    def package_block(seg, title, lines, code, descr):
        S(f'{seg}_hdr', descr, 'block', note=f'{title.upper()} — modelling logic')
        for k, lab in lines:
            first = k == lines[0][0]
            S(f'adv_{k}', f'  {lab} — average daily packages (000s)', 'line', 'm', data=f'adv_{k}',
              qe=lambda k=k: f'={P("adv_" + k)}*(1+{V("adv_" + k + "_g")})',
              e26=lambda k=k: f'={WD("adv_" + k, Q1, QE)}/SUM({Q1}{R["days"]}:{QE}{R["days"]})',
              ae=lambda k=k: f'={P("adv_" + k)}*(1+{V("adv_" + k + "_g")})',
              note=('Average daily package volume (ADV, 5-day-per-week basis). Q4/26E: prior-year quarter × (1 + growth); 2026E: day-weighted average of the quarters; '
                    '2027E+: prior year × (1 + scenario lever).') if first else None)
            S(f'adv_{k}_g', '    ADV y/y %', 'growth', 'pct', all=growth(f'adv_{k}'),
              qe=lambda k=k: f'={V("adv_" + k + "_pre")}+{QEa("cal_g")}',
              ae=lambda code=code: '=' + CH(SC[f'{code}_VOL'][yr()]),
              note='Q4/26E: nine-month 2026 y/y ADV growth + revenue-guidance calibration Δ (Group block). 2027E–2031E: scenario lever (Bull/Base/Bear table →).' if first else None)
            S(f'adv_{k}_pre', '    Q4/26E ADV growth before calibration (nine months 2026 y/y, day-weighted)', 'driver', 'pct',
              qe=lambda k=k: f'=IFERROR({WD("adv_" + k)}/{WD("adv_" + k, PQ1, PQ3)}-1,0)')
            S(f'y_{k}', f'  {lab} — revenue per package ($)', 'line', 'm2', data=f'y_{k}',
              qe=lambda k=k: f'={P("y_" + k)}*(1+{V("y_" + k + "_g")})',
              e26=lambda k=k: f'=IFERROR({V("r_" + k)}/({V("adv_" + k)}*{V("days")})*1000,"")',
              ae=lambda k=k: f'={P("y_" + k)}*(1+{V("y_" + k + "_g")})',
              note='Yield (revenue per package, incl. fuel and demand surcharges). Q4/26E: prior-year quarter × (1 + nine-month y/y yield change); 2027E+: scenario lever.' if first else None)
            S(f'y_{k}_g', '    Yield y/y %', 'growth', 'pct', all=growth(f'y_{k}'),
              qe=lambda k=k: f'=IFERROR(({ACT("r_" + k)}/{WD("adv_" + k)})/({ACT0("r_" + k)}/{WD("adv_" + k, PQ1, PQ3)})-1,0)',
              ae=lambda code=code: '=' + CH(SC[f'{code}_YLD'][yr()]))
            S(f'r_{k}', f'  {lab} — revenue', 'line', 'm', data=f'r_{k}', flow=True,
              qe=lambda k=k: f'={V("adv_" + k)}*{V("y_" + k)}*{V("days")}/1000',
              ae=lambda k=k: f'={V("adv_" + k)}*{V("y_" + k)}*{V("days")}/1000',
              note='Revenue = ADV × yield × operating days ÷ 1,000 (ties to the reported revenue within rounding — check row below).' if first else None)

    package_block('usd', 'Express U.S. Domestic', US, 'US',
                  'Express U.S. Domestic (U.S. priority, deferred and ground package services; U.S. freight) — reportable segment from 1-Jun-2026 (recast from Q1/24)')
    S('adv_gc', '  Memo: U.S. ground commercial ADV (000s)', 'memo', 'm', data='adv_gc')
    S('adv_ghd', '  Memo: U.S. ground home delivery / economy ADV (000s)', 'memo', 'm', data='adv_ghd')
    S('usd_stat', '  Statistics tie: U.S. package revenue ÷ Σ (ADV × yield × days) (≈ 1.00)', 'memo_calc', 'x2', basis='C',
      hist=lambda: (f'=IFERROR(({V("r_pri")}+{V("r_def")}+{V("r_gnd")})/(({V("adv_pri")}*{V("y_pri")}+{V("adv_def")}*{V("y_def")}+{V("adv_gnd")}*{V("y_gnd")})*{V("days")}/1000),"")'))
    S('lb_us', '  Memo: U.S. freight — average daily pounds (000s)', 'memo', 'm', data='lb_us')
    S('ylb_us', '  Memo: U.S. freight — revenue per pound ($)', 'memo', 'm2', data='ylb_us')
    S('r_ufrt', '  U.S. freight revenue', 'line', 'm', data='r_ufrt', flow=True, basis='C',
      qe=lambda: f'={P("r_ufrt")}*(1+{V("ufrt_g")})', ae=lambda: f'={P("r_ufrt")}*(1+{V("ufrt_g")})',
      note='U.S. airfreight (the U.S. Postal Service contract expired 29-Sep-2024, hence the 2024 step-down). Forecast: prior period × (1 + growth).')
    S('ufrt_g', '    y/y %', 'growth', 'pct', all=growth('r_ufrt'), qe=lambda: f'=IFERROR({ACT("r_ufrt")}/{ACT0("r_ufrt")}-1,0)', ae_in=V0['ufrt_g'])
    S('r_uoth', '  Other U.S. Domestic revenue', 'line', 'm', data='r_uoth', flow=True, basis='C',
      qe=lambda: f'={P("r_uoth")}*(1+{V("uoth_g")})', ae=lambda: f'={P("r_uoth")}*(1+{V("uoth_g")})')
    S('uoth_g', '    y/y %', 'growth', 'pct', all=growth('r_uoth'), qe=lambda: f'=IFERROR({ACT("r_uoth")}/{ACT0("r_uoth")}-1,0)', ae_in=V0['uoth_g'])
    S('usd_rev', '  Express U.S. Domestic — segment revenue', 'line_b', 'm', data='usd_rev', flow=True, basis='C',
      fc=lambda: '=' + '+'.join(V(k) for k in ('r_pri', 'r_def', 'r_gnd', 'r_ufrt', 'r_uoth')))
    S('usd_rev_g', '  Segment revenue y/y %', 'growth', 'pct', all=growth('usd_rev'))
    S('usd_chk', '  Check: Σ revenue lines vs segment revenue (should be 0)', 'check', 'm', basis='C',
      hist=lambda: f'=IF(ISNUMBER({V("usd_rev")}),{chk0(nsum(["r_pri", "r_def", "r_gnd", "r_ufrt", "r_uoth"]), V("usd_rev"), 1.01)},"")')
    S('usd_adj', '  Express U.S. Domestic — adjusted operating income (company definition)', 'line', 'm', data='usd_adj_oi', flow=True, basis='C',
      fc=lambda: f'={V("usd_rev")}*{V("usd_m")}',
      note='Segment operating income excluding the company\'s adjusting items (non-GAAP reconciliations). Forecast = segment revenue × adjusted margin.')
    S('usd_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('usd_adj', 'usd_rev'),
      qe=lambda: f'={V("usd_m_pre")}+{QEa("cal_m")}', ae=lambda: '=' + CH(SC['US_M'][yr()]),
      note='Q4/26E: margin before calibration + adjusted-EPS-guidance calibration Δ (Group block). 2027E+: scenario lever.')
    S('usd_m_pre', '  Q4/26E margin before EPS calibration (prior-year quarter + nine-month y/y drift)', 'driver', 'pct',
      qe=lambda: f'={P("usd_m")}+IFERROR({ACT("usd_adj")}/{ACT("usd_rev")}-{ACT0("usd_adj")}/{ACT0("usd_rev")},0)')
    S('usd_inc', '  Incremental adjusted margin (Δ adjusted OI / Δ revenue)', 'pct', 'pct', all=incr('usd_adj', 'usd_rev'))
    S('usd_oi', '  Memo: segment operating income as reported (GAAP)', 'memo', 'm', data='usd_oi', flow=True, basis='C')
    blank()

    package_block('intl', 'Express International', INTL, 'INTL',
                  'Express International (international export and intra-country package services, international airfreight, FedEx Logistics) — reportable segment from 1-Jun-2026')
    S('intl_stat', '  Statistics tie: international package revenue ÷ Σ (ADV × yield × days) (≈ 1.00)', 'memo_calc', 'x2', basis='C',
      hist=lambda: (f'=IFERROR(({V("r_ip")}+{V("r_ie")}+{V("r_id")})/(({V("adv_ip")}*{V("y_ip")}+{V("adv_ie")}*{V("y_ie")}+{V("adv_id")}*{V("y_id")})*{V("days")}/1000),"")'))
    S('lb_intl', '  Memo: international freight — average daily pounds (000s)', 'memo', 'm', data='lb_intl')
    S('ylb_intl', '  Memo: international freight — composite revenue per pound ($)', 'memo', 'm2', data='ylb_intl')
    S('r_ifrt', '  International freight revenue', 'line', 'm', data='r_ifrt', flow=True, basis='C',
      qe=lambda: f'={P("r_ifrt")}*(1+{V("ifrt_g")})', ae=lambda: f'={P("r_ifrt")}*(1+{V("ifrt_g")})')
    S('ifrt_g', '    y/y %', 'growth', 'pct', all=growth('r_ifrt'), qe=lambda: f'=IFERROR({ACT("r_ifrt")}/{ACT0("r_ifrt")}-1,0)', ae_in=V0['ifrt_g'])
    S('r_ioth', '  Other International revenue (incl. FedEx Logistics)', 'line', 'm', data='r_ioth', flow=True, basis='C',
      qe=lambda: f'={P("r_ioth")}*(1+{V("ioth_g")})', ae=lambda: f'={P("r_ioth")}*(1+{V("ioth_g")})')
    S('ioth_g', '    y/y %', 'growth', 'pct', all=growth('r_ioth'), qe=lambda: f'=IFERROR({ACT("r_ioth")}/{ACT0("r_ioth")}-1,0)', ae_in=V0['ioth_g'])
    S('intl_rev', '  Express International — segment revenue', 'line_b', 'm', data='intl_rev', flow=True, basis='C',
      fc=lambda: '=' + '+'.join(V(k) for k in ('r_ip', 'r_ie', 'r_id', 'r_ifrt', 'r_ioth')))
    S('intl_rev_g', '  Segment revenue y/y %', 'growth', 'pct', all=growth('intl_rev'))
    S('intl_chk', '  Check: Σ revenue lines vs segment revenue (should be 0)', 'check', 'm', basis='C',
      hist=lambda: f'=IF(ISNUMBER({V("intl_rev")}),{chk0(nsum(["r_ip", "r_ie", "r_id", "r_ifrt", "r_ioth"]), V("intl_rev"), 1.01)},"")')
    S('intl_adj', '  Express International — adjusted operating income (company definition)', 'line', 'm', data='intl_adj_oi', flow=True, basis='C',
      fc=lambda: f'={V("intl_rev")}*{V("intl_m")}')
    S('intl_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('intl_adj', 'intl_rev'),
      qe=lambda: f'={V("intl_m_pre")}+{QEa("cal_m")}', ae=lambda: '=' + CH(SC['INTL_M'][yr()]))
    S('intl_m_pre', '  Q4/26E margin before EPS calibration (prior-year quarter + nine-month y/y drift)', 'driver', 'pct',
      qe=lambda: f'={P("intl_m")}+IFERROR({ACT("intl_adj")}/{ACT("intl_rev")}-{ACT0("intl_adj")}/{ACT0("intl_rev")},0)')
    S('intl_inc', '  Incremental adjusted margin (Δ adjusted OI / Δ revenue)', 'pct', 'pct', all=incr('intl_adj', 'intl_rev'))
    S('intl_oi', '  Memo: segment operating income as reported (GAAP)', 'memo', 'm', data='intl_oi', flow=True, basis='C')
    blank()

    S('co_hdr', 'Corporate, other, and eliminations (FedEx Office, FedEx Dataworks, corporate headquarters; FedEx Supply Chain to its sale on 1-Oct-2026)', 'block',
      note='CORPORATE & OTHER — revenue of the operating segments below the reporting thresholds, net of eliminations; corporate costs')
    S('corp_rev', '  Corporate, other, and eliminations — revenue', 'line', 'm', data='corp_rev', flow=True, basis='C',
      qe=lambda: f'={P("corp_rev")}*(1+{V("corp_g")})*(1-{V("sc_share")})',
      ae=lambda: (f'={QEa("corp_rev")}*4*(1+{V("corp_g")})' if yr() == FYC + 1 else f'={P("corp_rev")}*(1+{V("corp_g")})'),
      note=('Q4/26E: prior-year quarter × (1 + nine-month y/y) × (1 − share divested with FedEx Supply Chain). 2027E: Q4/26E run-rate × 4 × (1 + growth) '
            '(first full year without FedEx Supply Chain); then prior year × (1 + growth).'))
    S('corp_g', '    y/y %', 'growth', 'pct', all=growth('corp_rev'), qe=lambda: f'=IFERROR({ACT("corp_rev")}/{ACT0("corp_rev")}-1,0)', ae_in=V0['corp_g'])
    S('sc_share', '    FedEx Supply Chain share of corporate & other revenue (not disclosed — ASSUMPTION; sold to CMA CGM 1-Oct-2026)', 'driver', 'pct',
      qe_in=V0['sc_share'], note=V0['sc_note'])
    S('corp_adj', '  Corporate, other, and eliminations — adjusted operating loss', 'line', 'm', data='corp_adj_oi', flow=True, basis='C',
      qe=lambda: f'={P("corp_adj")}*(1+{V("corp_adj_g")})', ae=lambda: f'={V("g_rev")}*{V("corp_pct")}',
      note=('History = published consolidated adjusted operating income − the two adjusted segment figures. Q4/26E: prior-year quarter × (1 + nine-month y/y); '
            '2027E+: % of revenue (includes costs stranded by the FedEx Freight spin-off, to be reduced through transition services and cost actions).'))
    S('corp_adj_g', '    y/y %', 'growth', 'pct', all=growth('corp_adj'), qe=lambda: f'=IFERROR({ACT("corp_adj")}/{ACT0("corp_adj")}-1,0)')
    S('corp_pct', '    Adjusted corporate loss % of revenue', 'pct', 'pct', all=ratio('corp_adj', 'is_rev'), ae_in=V0['corp_pct'])
    S('corp_oi', '  Memo: corporate, other, and eliminations operating loss as reported (GAAP)', 'memo', 'm', data='corp_oi', flow=True, basis='C')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group Total — revenue & adjusted operating income (operating build) → calendar-2026 guidance calibration', 'block',
      note='GROUP TOTAL (CONSOLIDATED, CONTINUING OPERATIONS) — modelling logic')
    S('g_rev', 'Revenue (operating build)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("usd_rev")}),{V("usd_rev")}+{V("intl_rev")}+{V("corp_rev")},{V("is_rev")})',
      fc=lambda: f'={V("usd_rev")}+{V("intl_rev")}+{V("corp_rev")}',
      note='Σ segments + corporate & other. Legacy columns: consolidated revenue as reported (FedEx Freight included).')
    S('g_rev_g', '  Revenue y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: operating build vs consolidated revenue (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),{chk0(V("g_rev"), V("is_rev"), 1.01)},"")')
    S('g_adj', 'Adjusted operating income (operating build)', 'total', 'm', basis='C',
      all=lambda: f'=IF(ISNUMBER({V("usd_adj")}),{V("usd_adj")}+{V("intl_adj")}+{V("corp_adj")},"")',
      note="Σ adjusted segment operating income + adjusted corporate loss = FedEx's adjusted operating income (company definition); drives the GAAP P&L below.")
    S('g_adjm', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('g_adj', 'is_rev'))
    S('g_chk_adj', '  Check: operating build vs adjusted operating income bridge (should be 0)', 'check', 'm', basis='C',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_adj")}),ISNUMBER({V("o_adj")})),{chk0(V("g_adj"), V("o_adj"), 1.51)},"")')
    S('cal_guid', '  Memo: calendar-2026 revenue guidance (scenario end-point = 2025 × (1 + guided growth))', 'memo', 'm',
      e26=lambda: f'={Y("is_rev", 2025)}*(1+{CH(SC["out_g"])})', note=V0['rev_guid_note'])
    S('cal_pre', '  Revenue before calibration (Q4/26E helper)', 'line', 'm',
      qe=lambda: '=' + '+'.join(f'{P("adv_" + k)}*(1+{V("adv_" + k + "_pre")})*{V("y_" + k)}*{V("days")}/1000' for k in PKG) + '+' + '+'.join(V(k) for k in OTHL) + f'+{V("corp_rev")}')
    S('cal_sens', '  Revenue sensitivity to +1.00 of ADV growth (Q4/26E helper)', 'line', 'm',
      qe=lambda: '=' + '+'.join(f'{P("adv_" + k)}*{V("y_" + k)}*{V("days")}/1000' for k in PKG))
    S('cal_g', '  Guidance calibration: Δ y/y ADV growth applied to all package services (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_guid", E26)}-{ACT("g_rev")}-{V("cal_pre")})/{V("cal_sens")}',
      note='Solves the uniform volume-growth shift (vs nine-month 2026 y/y rates) so that 2026 revenue = the guidance end-point for the active scenario. Closed form, no circularity.')
    S('cal_rev_chk', '  Check: 2026E revenue vs guidance end-point (should be 0)', 'check', 'm', e26=lambda: f'=ROUND({V("g_rev")}-{V("cal_guid")},0)')
    S('cal_eps', '  Memo: calendar-2026 adjusted EPS guidance (continuing operations; scenario end-point, $)', 'eps_memo', 'ps', e26=lambda: '=' + CH(SC['out_eps']),
      note=V0['eps_guid_note'])
    S('cal_ni', '  Adjusted net income required (2026E diluted shares × EPS guidance)', 'memo_calc', 'm', e26=lambda: f'={V("cal_eps")}*{V("e_sh")}')
    S('cal_oi', '  Q4/26E adjusted operating income required ((adjusted NI − nine months) ÷ (1 − Q4 tax rate) − Q4 adjusted non-operating income)', 'memo_calc', 'm',
      e26=lambda: f'=({V("cal_ni")}-{ACT("e_adjni")})/(1-{PT("pt_etr")})-({QEc("is_ret")}+{QEc("is_int")}+{QEc("is_onop")}+{QEc("is_inv")}+{QEc("e_nonop")})')
    S('cal_oi_pre', '  Adjusted operating income before margin calibration (Q4/26E helper)', 'line', 'm',
      qe=lambda: f'={V("usd_rev")}*{V("usd_m_pre")}+{V("intl_rev")}*{V("intl_m_pre")}+{V("corp_adj")}')
    S('cal_segrev', '  Segment revenue (Q4/26E helper)', 'line', 'm', qe=lambda: f'={V("usd_rev")}+{V("intl_rev")}')
    S('cal_m', '  Guidance calibration: Δ adjusted segment margin (Q4/26E)', 'driver', 'pct2',
      qe=lambda: f'=({V("cal_oi", E26)}-{V("cal_oi_pre")})/{V("cal_segrev")}',
      note='Solves the uniform segment-margin shift so that 2026 adjusted EPS = the guidance end-point for the active scenario.')
    S('cal_eps_chk', '  Check: 2026E adjusted EPS vs guidance end-point (should be 0.00)', 'check', 'ps', e26=lambda: f'=ROUND({V("e_eps")}-{V("cal_eps")},2)')
    S('cal_geps', '  Memo: calendar-2026 GAAP EPS guidance, continuing operations (scenario end-point) — information, not forced', 'eps_memo', 'ps',
      e26=lambda: '=' + CH(SC['out_geps']))
    S('cal_geps_d', '    Model GAAP EPS (continuing) − guidance ($): the model adds the FedEx Supply Chain sale gain, which the outlook table does not list', 'memo_calc', 'ps',
      e26=lambda: f'={V("eps_cont")}-{V("cal_geps")}')
    S('cal_capex', '  Memo: calendar-2026 capital spending guidance ($m) — drives Q4/26E capex', 'memo', 'm', e26=lambda: f'={PT("pt_capex")}')
    blank()

    # ------------------------------------------------------------------ legacy segments (memo)
    S('lg_hdr', 'Legacy reportable segments — fiscal years ended 31 May, as originally reported (memo; not comparable with the calendar-basis segments)', 'block',
      note=('LEGACY SEGMENTS — FedEx Express (incl. TNT Express from FY2018; separate in FY2017), FedEx Ground, FedEx Freight, FedEx Kinko\'s / Office (to FY2009, then in '
            'FedEx Services); Federal Express (Express + Ground + Services) and FedEx Freight from FY2025. History only.'))
    LSEG = [('exp', 'FedEx Express segment'), ('tnt', 'TNT Express segment (FY2017)'), ('gnd', 'FedEx Ground segment'), ('fec', 'Federal Express segment (FY2025–26)'),
            ('frt', 'FedEx Freight segment'), ('kin', "FedEx Kinko's segment (to FY2007)"), ('svc', 'FedEx Services segment (operating loss FY2008–09: FedEx Office impairment charges)'), ('oth', 'Other, corporate & eliminations')]
    for k, lab in LSEG:
        S(f'ls_{k}', f'  Revenue — {lab}', 'memo', 'm', data=f'sr_{k}', flow=True, basis='L')
    S('ls_chk', '  Check: Σ legacy segment revenue vs consolidated revenue (should be 0)', 'check', 'm', basis='L',
      hist=lambda: f'=IF(ISNUMBER({V("is_rev")}),{chk0(nsum(["ls_" + k for k, _ in LSEG]), V("is_rev"), 1.01)},"")')
    for k, lab in LSEG:
        S(f'lo_{k}', f'  Operating income — {lab}', 'memo', 'm', data=f'so_{k}', flow=True, basis='L')
    S('lo_chk', '  Check: Σ legacy segment operating income vs consolidated (should be 0)', 'check', 'm', basis='L',
      hist=lambda: f'=IF(ISNUMBER({V("is_oi")}),{chk0(nsum(["lo_" + k for k, _ in LSEG]), V("is_oi"), 1.01)},"")')
    S('lf_h', '  FedEx Freight (LTL) operating statistics — legacy (spun off 1-Jun-2026):', 'sub', 'gen')
    S('lf_ship', '    Average daily LTL shipments (000s)', 'memo', 'm1', data='lf_ship', basis='L')
    S('lf_wt', '    Weight per LTL shipment (lbs)', 'memo', 'm', data='lf_wt', basis='L')
    S('lf_cwt', '    LTL revenue per hundredweight ($)', 'memo', 'm2', data='lf_cwt', basis='L')
    S('lf_rps', '    LTL revenue per shipment ($)', 'memo', 'm2', data='lf_rps', basis='L')
    S('gc_a', '  Contribution to revenue growth — Express U.S. Domestic (legacy: Express, TNT, Ground, Federal Express segments) (pp)', 'growth', 'pct',
      all=lambda: ((f'=IFERROR(({V("usd_rev")}-{P("usd_rev")})/{P("is_rev")},"")' if CTX.col.basis == 'C' else
                    f'=IFERROR(({nsum(["ls_exp", "ls_tnt", "ls_gnd", "ls_fec"])}-({"+".join("N(" + P(k) + ")" for k in ("ls_exp", "ls_tnt", "ls_gnd", "ls_fec"))}))/{P("is_rev")},"")')
                   if CTX.col.prior else None))
    S('gc_b', '  Contribution to revenue growth — International, corporate & other (legacy: FedEx Freight, services, eliminations) (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR({V("g_rev_g")}-{V("gc_a")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers (operating expenses by nature, % of revenue)', 'block',
      note='COST DRIVERS — Q4/26E: prior-year quarter ratio + nine-month y/y drift; 2027E+: prior-year ratio held (other operating expense is the balancing line to the adjusted build)')
    for k, lab in (('sal', 'Salaries & employee benefits'), ('pt', 'Purchased transportation'), ('rent', 'Rentals & landing fees'), ('fuel', 'Fuel'), ('maint', 'Maintenance & repairs')):
        S(f'c_{k}', f'  {lab} % of revenue', 'pct', 'pct', all=ratio(f'is_{k}', 'is_rev'),
          qe=lambda k=k: f'={P("c_" + k)}+IFERROR({ACT("is_" + k)}/{ACT("is_rev")}-{ACT0("is_" + k)}/{ACT0("is_rev")},0)',
          ae=lambda k=k: f'={P("c_" + k)}')
    S('c_da', '  Depreciation & amortization % of revenue', 'pct', 'pct', all=ratio('is_da', 'is_rev'), ae_in=V0['da_pct'],
      note='Q4/26E: point estimate (scenario table). 2027E+: input (capital spending ~$3.9bn in 2026 against ~$3.9bn of depreciation).')
    S('d_sbc', '  Share-based compensation (XBRL: annual cash-flow statement; quarterly where tagged)', 'line', 'm', data='sbc', flow=True,
      qe_in=V0['sbc_q4'], e26=lambda: f'={ACT("d_sbc")}+{QEc("d_sbc")}+{V0["sbc_h1"]}', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}',
      note=f'2026E = Q3/26 actual + Q4 estimate + {V0["sbc_h1"]:.0f} for the first half (not tagged on the calendar basis; assumption at the Q3 run-rate). 2027E+: % of revenue.')
    S('d_sbc_pct', '  Share-based compensation % of revenue', 'pct', 'pct2', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF INCOME (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (operating income = adjusted operating income − adjusting items; other operating expense implied)')
    S('is_rev', 'Revenue', 'total', 'm', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the operating build.')
    S('is_sal', 'Salaries and employee benefits', 'line', 'm', data='sal', flow=True, fc=lambda: f'={V("is_rev")}*{V("c_sal")}')
    S('is_pt', 'Purchased transportation', 'line', 'm', data='pt', flow=True, fc=lambda: f'={V("is_rev")}*{V("c_pt")}')
    S('is_rent', 'Rentals and landing fees', 'line', 'm', data='rent', flow=True, fc=lambda: f'={V("is_rev")}*{V("c_rent")}')
    S('is_da', 'Depreciation and amortization', 'line', 'm', data='da', flow=True, qe=lambda: f'={PT("pt_da")}', ae=lambda: f'={V("is_rev")}*{V("c_da")}')
    S('is_fuel', 'Fuel', 'line', 'm', data='fuel', flow=True, fc=lambda: f'={V("is_rev")}*{V("c_fuel")}')
    S('is_maint', 'Maintenance and repairs', 'line', 'm', data='maint', flow=True, fc=lambda: f'={V("is_rev")}*{V("c_maint")}')
    S('is_spec', 'Impairment, business realignment / optimization, separation & other charges shown separately', 'line', 'm', data='spec', flow=True, labkey='spec_lab',
      fc=lambda: f'={V("o_tot")}',
      note=('As presented on the face of each release (cell comments list the lines). From the 28-Oct-2026 presentation these costs sit inside "Other, net". '
            'Forecast = adjusting items (bridge below), incl. the FedEx Supply Chain sale gain in Q4/26E.'))
    S('is_oth', 'Other operating expenses', 'line', 'm', data='oth', flow=True,
      fc=lambda: f'={V("is_rev")}-{V("is_oi")}-{V("is_sal")}-{V("is_pt")}-{V("is_rent")}-{V("is_da")}-{V("is_fuel")}-{V("is_maint")}-{V("is_spec")}',
      note='Forecast = balancing line: revenue − operating income − the other cost lines.')
    S('is_opex', 'Total operating expenses', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_sal")}),{nsum(["is_sal", "is_pt", "is_rent", "is_da", "is_fuel", "is_maint", "is_spec", "is_oth"])},"")')
    S('is_oi', 'Operating income', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_opex")}),{V("is_rev")}-{V("is_opex")},"")', fc=lambda: f'={V("g_adj")}-{V("o_tot")}',
      note='Forecast = adjusted operating income (operating build) − adjusting items.')
    S('is_oi_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('is_ret', 'Other retirement plans income (expense), incl. year-end mark-to-market adjustments (below operating income from FY2019)', 'line', 'm', data='ret', flow=True,
      qe=lambda: f'={PT("pt_ret")}', ae_in=V0['ret_ae'],
      note=('Non-service retirement-plan income and MTM gains / losses (ASU 2017-07 from FY2019; FY2015–18 MTM adjustments were an operating expense line). '
            'The Q3/26 release shows it inside "Other, non-operating, net". Forecast: input; no MTM adjustment is forecast.'))
    S('is_int', 'Interest, net (expense −)', 'line', 'm', data='int_net', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'=-({P("ds_notes")}*{V("ds_r_notes")}+{P("ds_rev")}*{V("ds_r_rev")})+{P("cf_end")}*{V("ds_r_cash")}',
      note='Q4/26E point estimate. 2027E+ = −(rate × opening notes + rate × opening commercial paper) + yield × opening cash (no circularity).')
    S('is_inv', 'Gain (loss) on short-term investment (retained 19.9% FedEx Freight stake; shown separately from Q3/26)', 'line', 'm', data='inv_gain', flow=True,
      qe_in=0.0, ae_in=0.0, note='Fair-value changes of the retained stake (Q2/26 gain of ~$4.5bn is inside other, net in the recast exhibit). Forecast nil: the stake is assumed sold at carrying value in 2027E.')
    S('is_onop', 'Other, net (incl. debt-extinguishment gains / losses)', 'line', 'm', data='oth_nonop', flow=True, labkey='oth_nonop_lab',
      qe=lambda: f'={PT("pt_onop")}', ae_in=V0['onop_ae'])
    S('is_ebt', 'Income before income taxes', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_oi")}),{V("is_oi")}+N({V("is_ret")})+N({V("is_int")})+N({V("is_inv")})+N({V("is_onop")}),"")')
    S('is_tax', 'Provision for income taxes', 'line', 'm', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'),
      qe=lambda: f'=IFERROR((({V("is_ebt")}+{V("o_gain")})*{PT("pt_etr")}+{V("sc_tax", E26)})/{V("is_ebt")},{PT("pt_etr")})', ae_in=V0['etr'],
      note='Q4/26E: guided ~22.5% on pre-tax income before the FedEx Supply Chain gain + tax on that gain (input, schedules). 2027E+: input.')
    S('is_nic', 'Income from continuing operations', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_disc', 'Income from discontinued operations, net of tax (FedEx Freight; calendar basis)', 'line', 'm', data='disc', flow=True, fc=lambda: '=0')
    S('is_ni', 'Net income', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_nic")}),{V("is_nic")}+N({V("is_disc")}),"")')
    S('is_ni_chk', '  Check: net income vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),{chk0(V("is_ni"), V("is_ni_pub"), 1.01)},"")')
    S('is_ni_pub', '  Memo: net income as reported', 'memo', 'm', data='ni', flow=True)
    S('is_capex', '  Memo: capital expenditures as shown with the income statement (continuing operations on the calendar basis)', 'memo', 'm', data='capex_is', flow=True)
    S('eps_hdr', '(Earnings per share — FedEx common stock)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m) (XBRL)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={B1("bs_shares")}-${E26}${R["bb_sh"]}*0.5+${E26}${R["bb_iss"]}*0.5',
      e26=lambda: f'={V("sh_dil")}-({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q4/26E: shares outstanding at 26-Oct-2026 (10-Q cover) − Q4 buybacks (mid-quarter) + issuance. 2027E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}',
      note=('Releases print whole millions. Recast calendar periods (Q1/24–Q2/26, 2024, 2025): derived as net income ÷ diluted EPS, because the recast exhibits print no share count '
            '(cell comments). 2026E = average of the quarters.'))
    S('eps_cont', 'EPS – diluted, continuing operations ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_nic")}/{V("sh_dil")},""),"")',
      note='Income from continuing operations ÷ weighted diluted shares (FedEx uses the two-class method; ±$0.10 vs reported).')
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.10: two-class method, shares in whole millions)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.1001,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('dps', '  Dividends declared per share ($)', 'line', 'ps', data='dps', flow=True, qe_in=V0['dps_q'],
      ae=lambda: f'={P("dps")}*(1+{V("dps_g")})' if yr() > FYC + 1 else f'={QEa("dps")}*4*(1+{V("dps_g")})',
      note=('Dividends declared (legacy: XBRL; two declarations fall in fiscal Q1 and none in Q4). Quarterly rate $1.22 after the FedEx Freight spin-off (declared 21-Aug-2026). '
            '2027E: Q4/26E rate × 4 × (1 + growth); then prior year × (1 + growth).'))
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'])
    blank()

    # ------------------------------------------------------------------ RECON 1: OI -> adjusted OI
    S('sec_r1', 'RECONCILIATION: OPERATING INCOME → ADJUSTED OPERATING INCOME (company definition, as published)', 'section',
      note='ADJUSTED OPERATING INCOME — per the release reconciliations of non-GAAP measures; the items of each period are in the cell comments')
    S('o_op', 'Operating income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_oi")}')
    S('o_restr', '  (+) Business realignment / optimization, restructuring, separation (FedEx Freight spin-off) & fiscal-year-change costs', 'line', 'm', data='oa_restr', flow=True,
      labkey='oa_restr_lab', qe=lambda: f'={PT("pt_restr")}-{ACT("o_tot")}', ae_in=V0['ae_restr'], note=V0['restr_note'])
    S('o_acq', '  (+) TNT Express / GENCO integration & acquisition-related expenses', 'line', 'm', data='oa_acq', flow=True, labkey='oa_acq_lab', fc=lambda: '=0')
    S('o_impair', '  (+) Goodwill, aircraft & other asset impairment charges', 'line', 'm', data='oa_impair', flow=True, labkey='oa_impair_lab', fc=lambda: '=0')
    S('o_legal', '  (+) Legal & regulatory matters', 'line', 'm', data='oa_legal', flow=True, labkey='oa_legal_lab', fc=lambda: '=0')
    S('o_mtm', '  (+) Retirement plans mark-to-market adjustment in operating income (FY2015–FY2018)', 'line', 'm', data='oa_mtm', flow=True, labkey='oa_mtm_lab', fc=lambda: '=0')
    S('o_oth', '  (+) Other items', 'line', 'm', data='oa_other', flow=True, labkey='oa_other_lab', fc=lambda: '=0')
    S('o_gain', '  (+) Gain on the sale of FedEx Supply Chain (model, Q4/26E: proceeds − net assets held for sale; gain −)', 'line', 'm', flow=True,
      qe=lambda: f'=-({V("sc_proc", E26)}-{V("sc_nav", E26)})', ae_in=0.0,
      note=('ASSUMPTION: FedEx Supply Chain was sold on 1-Oct-2026 for $1.4bn; net assets held for sale at 30-Sep-2026 were $264m. The outlook table of 28-Oct-2026 does not '
            'list a gain; the model records proceeds − net assets held for sale as an operating gain and adjusts it out.'))
    S('o_tot', '  Total adjusting items (pre-tax, operating)', 'line_b', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("o_op")}),{nsum(OITEMS)},"")', fc=lambda: '=' + nsum(OITEMS))
    S('o_adj', '  = Adjusted operating income (model bridge)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_tot")},"")',
      note='Rebuilt from the published reconciliation items; forecast = operating income + forecast adjusting items (equals the operating build — check in the Group block).')
    S('o_adj_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company-published adjusted operating income', 'memo', 'm', data='adj_oi_pub', flow=True)
    S('o_chk', '  Check: model bridge vs company-published (should be 0; ±1.5 rounding)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),{chk0(V("o_adj"), V("o_pub"), 1.51)},"n/p")')
    S('o_def', '  Definition / basis (company adjusted definition in force)', 'text', 'gen',
      note='Basis changes are flagged in the column where they take effect (cell comment gives the detail). "n/p" in the check row = no reconciliation table published for the period (adjusted = GAAP).')
    S('o_adj_g', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental adjusted operating margin (Δ adjusted OI / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: NI -> EBITDA -> adjusted EBITDA (model)
    S('sec_r2', 'RECONCILIATION: INCOME FROM CONTINUING OPERATIONS → EBITDA → ADJUSTED EBITDA (model definition — FedEx publishes no EBITDA in its releases)', 'section',
      note=('EBITDA (MODEL DEFINITION) — operating income + depreciation & amortization; adjusted EBITDA = adjusted operating income + D&A. Non-operating retirement-plan, '
            'investment and other items are excluded. The credit-agreement "adjusted EBITDA" (debt / adjusted EBITDA 1.9x at 30-Sep-2026) is a different, undisclosed calculation.'))
    S('r_ni', 'Income from continuing operations (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_nic")}')
    S('r_tax', '  (+) Provision for income taxes', 'line', 'm', all=lambda: f'={V("is_tax")}')
    S('r_nonop', '  (−) Other income / (+) other expense (retirement plans, interest, investment gains, other)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_oi")}),-(N({V("is_ret")})+N({V("is_int")})+N({V("is_inv")})+N({V("is_onop")})),"")')
    S('r_gebit', '  = Operating income', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_tax")}+{V("r_nonop")},"")')
    S('r_da', '  (+) Depreciation and amortization', 'line', 'm', all=lambda: f'={V("is_da")}')
    S('r_ebitda', '  = EBITDA (model)', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_gebit")}),ISNUMBER({V("r_da")})),{V("r_gebit")}+{V("r_da")},"")')
    S('r_adjx', '  (+) Adjusting items (operating; bridge above)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("o_tot")}),{V("o_tot")},"")')
    S('r_adj', '  = Adjusted EBITDA (model)', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda")}),ISNUMBER({V("r_adjx")})),{V("r_ebitda")}+{V("r_adjx")},"")',
      note='Model definition. Used for leverage (net debt / adjusted EBITDA) and EV / EBITDA. Operating leases are not capitalised (rent stays an operating cost).')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_chk', '  Check: adjusted EBITDA − D&A = adjusted operating income (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),ROUND({V("r_adj")}-{V("r_da")}-{V("o_adj")},0),"")')
    S('r_ebit_h', 'To adjusted EBIT (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ebit', '  = Adjusted EBIT (= adjusted operating income; after depreciation, amortization and share-based compensation)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}-{V("r_da")},"")')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: restructuring, integration & legal costs (cash costs adjusted out; deducted in the DCF)', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_op")}),N({V("o_restr")})+N({V("o_acq")})+N({V("o_legal")}),"")')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: INCOME FROM CONTINUING OPERATIONS → ADJUSTED NET INCOME → ADJUSTED EPS (company definition)', 'section',
      note=('ADJUSTED EPS — income from continuing operations + operating adjusting items + non-operating items (retirement plans MTM, FedEx Freight stake, debt extinguishment) '
            '− tax effect (incl. discrete tax items)'))
    S('e_ni', 'Income from continuing operations (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_nic")}')
    S('e_op', '  (+) Operating adjusting items (pre-tax; bridge above)', 'line', 'm', all=lambda: f'={V("o_tot")}')
    S('e_nonop', '  (+) Non-operating adjusting items (pre-tax: retirement plans MTM, short-term investment, debt extinguishment)', 'line', 'm', data='oa_nonop', flow=True,
      labkey='oa_nonop_lab', hist=lambda: f'=IF(ISNUMBER({V("e_ni")}),0,"")', fc=lambda: f'=-{V("is_inv")}',
      note='Pre-tax amount = after-tax effect + tax effect of each company item, less its operating-income effect. Forecast: reverses the short-term investment line (nil).')
    S('e_tax', '  (−) Tax effect of the adjustments & discrete tax items', 'line', 'm', data='e_tax_in', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("e_ni")}),0,"")', fc=lambda: f'={V("is_tax")}-{V("e_adjtax")}',
      note='Historical: the income-tax column of the company reconciliations (to FY2015: pre-tax − after-tax amounts). Forecast: GAAP tax − adjusted tax.')
    S('e_adjni', '  = Adjusted net income (model bridge)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("e_ni")}),{V("e_ni")}+N({V("e_op")})+N({V("e_nonop")})+N({V("e_tax")}),"")')
    S('e_pubni', '  Company-published adjusted net income', 'memo', 'm', data='adj_ni_pub', flow=True)
    S('e_nichk', '  Check: model vs company-published adjusted net income (should be 0; ±2 rounding)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("e_pubni")}),{chk0(V("e_adjni"), V("e_pubni"), 2.01)},"n/p")')
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted EPS – diluted ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted EPS ($)', 'eps_memo', 'ps', data='adj_eps_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.10: two-class method, shares in whole millions)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.1001,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_adjebt', '  Adjusted income before taxes (pre-tax income + operating and non-operating adjusting items)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}+N({V("e_op")})+N({V("e_nonop")}),"")')
    S('e_adjtax', '  Adjusted income tax (adjusted pre-tax income − adjusted net income)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_adjni")}),ISNUMBER({V("e_adjebt")})),{V("e_adjebt")}-{V("e_adjni")},"")',
      fc=lambda: f'={V("e_adjebt")}*{V("e_rate")}')
    S('e_rate', '  Adjusted effective tax rate', 'pct', 'pct', all=ratio('e_adjtax', 'e_adjebt'), qe=lambda: f'={PT("pt_etr")}', ae=lambda: f'={V("is_etr")}',
      note='Calendar-2026 guidance ~22.5% (before MTM adjustments and the FedEx Supply Chain deferred-tax benefit). Forecast = effective tax rate input.')
    S('e_def', '  Definition / basis (company adjusted EPS definition)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Revenue y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_usd', '  Express U.S. Domestic revenue y/y %', 'growth', 'pct', all=growth('usd_rev'))
    S('gm_intl', '  Express International revenue y/y %', 'growth', 'pct', all=growth('intl_rev'))
    S('gm_adjop', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating income (GAAP) y/y %', 'growth', 'pct', all=growth('is_oi'))
    S('gm_ni', '  Net income y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_adjop_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_inc', '  Incremental adjusted operating margin (Δ adjusted OI / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_sal', '  Salaries & employee benefits % of revenue', 'pct', 'pct', all=ratio('is_sal', 'is_rev'))
    S('gm_pt', '  Purchased transportation % of revenue', 'pct', 'pct', all=ratio('is_pt', 'is_rev'))
    S('gm_fuel', '  Fuel % of revenue', 'pct', 'pct', all=ratio('is_fuel', 'is_rev'))
    blank()
