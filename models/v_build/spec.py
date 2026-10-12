"""Row specification of the Visa Model sheet, part 1 (MLM template layout and process):
operating drivers (nominal payments volume, processed transactions) -> gross revenue by category (service = payments volume x
yield; data processing = processed transactions x revenue per transaction; international transaction and other revenue by
growth) -> client incentives (% of gross revenue) -> net revenue -> adjusted operating expenses (non-GAAP, company definition)
-> adjusted operating income -> M&A lever -> Q4/26E calibration -> cost drivers & adjusting items -> income statement ->
GAAP-to-non-GAAP bridges -> growth & margins."""
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

OPC = ['litig', 'amort', 'acq', 'restr', 've', 'other']           # operating adjusting items (model rows d_<c>)
NOPC = ['eqinv', 've', 'other']                                   # non-operating adjusting items (model rows n_<c>)
CATS = [('svc', 'Service revenue', 'rev_svc'), ('dp', 'Data processing revenue', 'rev_dp'),
        ('itr', 'International transaction revenue', 'rev_itr'), ('oth', 'Other revenue', 'rev_oth')]
LINES = [('pers', 'Personnel', 'personnel', 'restr'), ('mkt', 'Marketing', 'marketing', None), ('net', 'Network and processing', 'network', None),
         ('prof', 'Professional fees', 'prof', None), ('dna', 'Depreciation and amortization', 'dna', 'amort'),
         ('ga', 'General and administrative', 'ga', 'acq'), ('lit', 'Litigation provision', 'litig', 'litig')]

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of the Q4 FY26 outlook (UNVERIFIED — call only).'))
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
    # ------------------------------------------------------------------ REVENUE BUILD
    S('sec_rev', 'NET REVENUE BUILD — PAYMENTS VOLUME × YIELD · PROCESSED TRANSACTIONS × YIELD · CROSS-BORDER · CLIENT INCENTIVES', 'section',
      note='REVENUE BUILD — modelling logic (operating drivers → gross revenue by category → client incentives → net revenue; Visa reports one segment)')
    blank()
    S('kpi_hdr', 'Operating drivers — Visa-branded payments volume and processed transactions (10-Q / 10-K MD&A)', 'block',
      note='KPIs — service revenue in a quarter is assessed on the PRIOR quarter\'s nominal payments volume; data processing revenue on processed transactions')
    S('k_pv', '  Nominal payments volume ($bn; the calendar quarter driving the period\'s service revenue)', 'line', 'm', data='k_pv', flow=True,
      qe=lambda: f'={P("k_pv")}*(1+{V("k_pv_g")})', ae=lambda: f'={P("k_pv")}*(1+{V("k_pv_g")})',
      note='10-Q / 10-K "Total nominal payments volume" (three / twelve months ended one quarter before the fiscal period; Q4 = twelve months − nine months). Forecast = prior year × (1 + growth).')
    S('k_pv_g', '    y/y %', 'growth', 'pct', all=growth('k_pv'), qe=lambda: f'={PT("pt_pvg")}', ae=lambda: '=' + CH(SC['PV'][CTX.col.year]),
      note='Q4/26E: published — Q3 FY26 release: payments volume for the quarter ended 30-Jun-2026 +11% nominal (drives Q4 service revenue). 2027E+: scenario lever.')
    S('k_pv_us', '    of which U.S. ($bn)', 'memo', 'm', data='k_pv_us', flow=True)
    S('k_pv_intl', '    of which international ($bn)', 'memo', 'm', data='k_pv_intl', flow=True)
    S('k_pv_ip', '    International % of payments volume', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("k_pv_intl")}),IFERROR({V("k_pv_intl")}/{V("k_pv")},""),"")')
    S('k_ptx', '  Processed transactions (millions)', 'line', 'm', data='k_ptx', flow=True,
      qe=lambda: f'={P("k_ptx")}*(1+{V("k_ptx_g")})', ae=lambda: f'={P("k_ptx")}*(1+{V("k_ptx_g")})',
      note='10-Q / 10-K "Visa processed transactions" (current period; Q4 = fiscal year − nine months). Forecast = prior year × (1 + growth).')
    S('k_ptx_g', '    y/y %', 'growth', 'pct', all=growth('k_ptx'), qe=lambda: f'=IFERROR({ACT("k_ptx")}/{ACT0("k_ptx")}-1,0)',
      ae=lambda: '=' + CH(SC['PTX'][CTX.col.year]), note='Q4/26E: 9M FY26 y/y (+9%). 2027E+: scenario lever.')
    blank()
    S('rv_hdr', 'Gross revenue by category → client incentives → net revenue', 'block', note='REVENUE CATEGORIES — company presentation (service, data processing, international transaction, other; less client incentives)')
    S('rev_svc', '  Service revenue', 'line', 'm', data='rev_svc', flow=True, fc=lambda: f'={V("k_pv")}*1000*{V("svc_yld")}',
      note='Forecast = nominal payments volume ($bn × 1,000) × service yield.')
    S('svc_yld', '    Service yield (% of nominal payments volume)', 'pct', 'pct2', all=lambda: f'=IF(AND(ISNUMBER({V("rev_svc")}),ISNUMBER({V("k_pv")})),IFERROR({V("rev_svc")}/({V("k_pv")}*1000),""),"")',
      qe=lambda: f'={P("svc_yld")}*(1+{V("svc_yld_pre")}+{QEa("cal_g")})', ae=lambda: f'={P("svc_yld")}*(1+{CH(SC["SVC_YLD"][CTX.col.year])})',
      note='Q4/26E: prior-year quarter × (1 + 9M FY26 y/y yield change + revenue calibration Δ). 2027E+: prior year × (1 + scenario yield change: pricing, mix, card benefits).')
    S('svc_yld_pre', '    Q4/26E yield change before calibration (9M FY26 y/y)', 'driver', 'pct',
      qe=lambda: f'=IFERROR(({ACT("rev_svc")}/{ACT("k_pv")})/({ACT0("rev_svc")}/{ACT0("k_pv")})-1,0)')
    S('rev_svc_g', '    Service revenue y/y %', 'growth', 'pct', all=growth('rev_svc'))
    S('rev_dp', '  Data processing revenue', 'line', 'm', data='rev_dp', flow=True, fc=lambda: f'={V("k_ptx")}*{V("dp_rpt")}',
      note='Forecast = processed transactions (m) × data processing revenue per transaction ($).')
    S('dp_rpt', '    Data processing revenue per processed transaction ($)', 'line', 'm2', all=ratio('rev_dp', 'k_ptx'),
      qe=lambda: f'={P("dp_rpt")}*(1+{V("dp_rpt_pre")}+{QEa("cal_g")})', ae=lambda: f'={P("dp_rpt")}*(1+{CH(SC["DP_RPT"][CTX.col.year])})',
      note='Q4/26E: prior-year quarter × (1 + 9M FY26 y/y change + calibration Δ). 2027E+: scenario (pricing, value-added services, cross-border mix).')
    S('dp_rpt_pre', '    Q4/26E change before calibration (9M FY26 y/y)', 'driver', 'pct',
      qe=lambda: f'=IFERROR(({ACT("rev_dp")}/{ACT("k_ptx")})/({ACT0("rev_dp")}/{ACT0("k_ptx")})-1,0)')
    S('rev_dp_g', '    Data processing revenue y/y %', 'growth', 'pct', all=growth('rev_dp'))
    for c, lab, code in (('itr', 'International transaction revenue', 'ITR'), ('oth', 'Other revenue (value-added services, licensing, marketing services)', 'OTH')):
        S(f'rev_{c}', f'  {lab}', 'line', 'm', data=f'rev_{c}', flow=True,
          qe=lambda c=c: f'={P("rev_" + c)}*(1+{V("rev_" + c + "_g")})', ae=lambda c=c: f'={P("rev_" + c)}*(1+{V("rev_" + c + "_g")})',
          note=('Driven by cross-border volume (excl. intra-Europe) and currency volatility. ' if c == 'itr' else 'Value-added services, consulting, marketing services, licensing. ')
               + 'Q4/26E: prior-year quarter × (1 + 9M FY26 y/y + calibration Δ). 2027E+: scenario growth.')
        S(f'rev_{c}_g', '    y/y %', 'growth', 'pct', all=growth(f'rev_{c}'), qe=lambda c=c: f'={V("rev_" + c + "_pre")}+{QEa("cal_g")}',
          ae=lambda code=code: '=' + CH(SC[code][CTX.col.year]))
        S(f'rev_{c}_pre', '    Q4/26E growth before calibration (9M FY26 y/y)', 'driver', 'pct', qe=lambda c=c: f'=IFERROR({ACT("rev_" + c)}/{ACT0("rev_" + c)}-1,0)')
    S('rev_gross', '  Gross revenue', 'line_b', 'm', flow=True,
      all=lambda: f'=IF(ISNUMBER({V("rev_svc")}),{V("rev_svc")}+{V("rev_dp")}+{V("rev_itr")}+{V("rev_oth")},"")')
    S('rev_gross_g', '    Gross revenue y/y %', 'growth', 'pct', all=growth('rev_gross'))
    S('rev_ci', '  Client incentives (deducted from gross revenue)', 'line', 'm', data='rev_ci', flow=True, fc=lambda: f'={V("rev_gross")}*{V("ci_pct")}',
      note='Contra-revenue: incentives to financial-institution clients and merchants ("volume and support incentives" to FY2012).')
    S('ci_pct', '    Client incentives % of gross revenue', 'pct', 'pct', all=ratio('rev_ci', 'rev_gross'),
      qe=lambda: f'={P("ci_pct")}+IFERROR({ACT("rev_ci")}/{ACT("rev_gross")}-{ACT0("rev_ci")}/{ACT0("rev_gross")},0)', ae=lambda: '=' + CH(SC['CI'][CTX.col.year]),
      note='Q4/26E: prior-year quarter + 9M FY26 y/y drift. 2027E+: scenario lever (renewals; FY2025 28.0%).')
    S('rev_m', '  Revenue from future acquisitions (M&A lever)', 'line', 'm', fc=lambda: f'=N({V("m_rev")})')
    S('rev_build', 'Net revenue (build)', 'total', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("rev_gross")}),{V("rev_gross")}-{V("rev_ci")},{V("is_rev")})',
      fc=lambda: f'={V("rev_gross")}-{V("rev_ci")}+{V("rev_m")}', note='Gross revenue − client incentives (+ future acquisitions from 2027E). Drives the income statement.')
    S('rev_build_g', '  Net revenue y/y %', 'growth', 'pct', all=growth('rev_build'))
    S('rev_chk', '  Check: build vs reported net revenue (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("rev_build")}),IF(ABS({V("rev_build")}-{V("is_rev")})<=0.6,0,ROUND({V("rev_build")}-{V("is_rev")},1)),"")')
    S('ny', '  Net revenue yield (net revenue ÷ nominal payments volume)', 'pct', 'pct2',
      all=lambda: f'=IF(AND(ISNUMBER({V("rev_build")}),ISNUMBER({V("k_pv")})),IFERROR({V("rev_build")}/({V("k_pv")}*1000),""),"")')
    S('gc_vol', '  Net revenue growth decomposition — payments volume y/y (pp)', 'growth', 'pct', all=lambda: (f'=IFERROR({V("k_pv")}/{P("k_pv")}-1,"")' if CTX.col.prior else None))
    S('gc_yld', '  Net revenue growth decomposition — net revenue yield y/y (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("rev_build")}/{P("rev_build")})/({V("k_pv")}/{P("k_pv")})-1,"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ Q4 calibration (revenue)
    S('cal_hdr', 'Q4/26E calibration — net revenue and non-GAAP EPS to the Q4 FY26 outlook (UNVERIFIED: given on the call, not filed on EDGAR)', 'block',
      note='CALIBRATION — Visa guides on the earnings call only (no outlook in the 8-K release since FY2020); end-points are labelled unverified')
    S('cal_guid', '  Memo: Q4/26E net revenue end-point = Q4/25 × (1 + outlook growth, active scenario)', 'memo', 'm',
      qe=lambda: f'={P("is_rev")}*(1+{CH(SC["out_g"])})', note=V0['rev_guid_note'])
    S('cal_pre', '  Net revenue before calibration (Q4/26E helper)', 'line', 'm',
      qe=lambda: (f'=({V("k_pv")}*1000*{P("svc_yld")}*(1+{V("svc_yld_pre")})+{V("k_ptx")}*{P("dp_rpt")}*(1+{V("dp_rpt_pre")})'
                  f'+{P("rev_itr")}*(1+{V("rev_itr_pre")})+{P("rev_oth")}*(1+{V("rev_oth_pre")}))*(1-{V("ci_pct")})'))
    S('cal_sens', '  Net revenue sensitivity to +1.00 of the calibration Δ (Q4/26E helper)', 'line', 'm',
      qe=lambda: f'=({V("k_pv")}*1000*{P("svc_yld")}+{V("k_ptx")}*{P("dp_rpt")}+{P("rev_itr")}+{P("rev_oth")})*(1-{V("ci_pct")})')
    S('cal_g', '  Calibration Δ: uniform shift in service yield, data processing yield, international and other revenue growth (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_guid")}-{V("cal_pre")})/{V("cal_sens")}',
      note='Closed-form solve (no goal-seek): Δ = (end-point − pre-calibration) ÷ sensitivity. Payments volume is published, so the Δ falls on yields and growth rates.')
    S('cal_rev_chk', '  Check: Q4/26E net revenue vs outlook end-point (should be 0)', 'check', 'm', qe=lambda: f'=ROUND({V("rev_build")}-{V("cal_guid")},1)')
    S('cal_fyg', '  Memo: implied FY26 net revenue growth (information; see the unverified full-year commentary)', 'memo_calc', 'pct', e26=lambda: f'={V("rev_build_g")}')
    blank()

    # ------------------------------------------------------------------ adjusted opex & operating income
    S('ox_hdr', 'Operating expenses (non-GAAP, company definition) → adjusted operating income', 'block',
      note='OPEX — non-GAAP operating expenses exclude the company\'s adjusting items (litigation provisions, acquired-intangible amortization, acquisition costs, severance …)')
    S('aox', '  Adjusted operating expenses (GAAP operating expenses − operating adjusting items)', 'line_b', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("is_opex")}),{V("is_opex")}-{V("o_tot")},"")',
      qe=lambda: f'={P("aox")}*(1+{V("aox_pre")}+{QEa("cal_m")})', ae=lambda: f'={V("rev_build")}*(1-{V("aom")})',
      note='Q4/26E: prior-year quarter × (1 + 9M FY26 y/y + EPS calibration Δ). 2027E+: net revenue × (1 − adjusted operating margin lever).')
    S('aox_g', '    y/y %', 'growth', 'pct', all=growth('aox'))
    S('aox_pre', '    Q4/26E growth before EPS calibration (9M FY26 y/y)', 'driver', 'pct', qe=lambda: f'=IFERROR({ACT("aox")}/{ACT0("aox")}-1,0)')
    S('aox_pub', '  Company-published non-GAAP operating expenses', 'memo', 'm', data='adj_opex_pub', flow=True)
    S('aox_chk', '  Check: model vs company-published non-GAAP operating expenses (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("aox_pub")}),IF(ABS({V("aox")}-{V("aox_pub")})<=1.01,0,ROUND({V("aox")}-{V("aox_pub")},1)),"n/p")')
    S('aoi', 'Adjusted operating income (net revenue − non-GAAP operating expenses)', 'total', 'm', flow=True,
      all=lambda: f'=IF(ISNUMBER({V("aox")}),{V("rev_build")}-{V("aox")},"")')
    S('aom', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('aoi', 'rev_build'), ae=lambda: '=' + CH(SC['AOM'][CTX.col.year]),
      note='2027E+: scenario lever (FY2025 adjusted operating margin 67.4%; FY2019 68.5%).')
    S('aoi_g', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('aoi'))
    S('aoi_inc', '  Incremental adjusted operating margin (Δ adjusted OI / Δ net revenue)', 'pct', 'pct', all=incr('aoi', 'rev_build'))
    S('cal_eps', '  Memo: Q4/26E non-GAAP EPS end-point = Q4/25 × (1 + outlook growth, active scenario) ($)', 'eps_memo', 'ps',
      qe=lambda: f'={P("e_pub")}*(1+{CH(SC["out_eps"])})', note=V0['eps_guid_note'])
    S('cal_ni', '  Adjusted net income required (Q4/26E diluted shares × EPS end-point)', 'memo_calc', 'm', qe=lambda: f'={V("cal_eps")}*{V("e_sh")}')
    S('cal_oi', '  Adjusted operating income required (NI ÷ (1 − adjusted tax rate) − adjusted non-operating income)', 'memo_calc', 'm',
      qe=lambda: f'={V("cal_ni")}/(1-{V("e_rate")})-({V("is_invoth")}-{V("is_intexp")})')
    S('cal_m', '  Calibration Δ: shift in adjusted operating-expense growth (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("rev_build")}-{V("cal_oi")})/{P("aox")}-1-{V("aox_pre")}',
      note='Solves Q4/26E adjusted opex so that non-GAAP EPS = the end-point for the active scenario.')
    S('cal_eps_chk', '  Check: Q4/26E non-GAAP EPS vs outlook end-point (should be 0.00)', 'check', 'ps', qe=lambda: f'=ROUND({V("e_eps")}-{V("cal_eps")},2)')
    S('cal_fyeps', '  Memo: implied FY26 non-GAAP EPS growth (information; call commentary "low end of mid-teens", UNVERIFIED)', 'memo_calc', 'pct', e26=lambda: f'={V("e_eps_g")}')
    S('cal_oxg', '  Memo: Q4/26E adjusted operating-expense growth (information; call commentary "low double digits", UNVERIFIED)', 'memo_calc', 'pct', qe=lambda: f'={V("aox_g")}')
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — value-added services / new flows bolt-ons; deals closed from 2027E)', 'block',
      note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=8.0, e26_in=0.0,
      note='Fintech / software targets (Tink, Pismo, Featurespace, Currencycloud): prices not split by revenue in the filings; 8.0x EV/sales input (assumption).')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.15)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}', note='Mid-year convention.')
    S('m_m', '  Adjusted operating margin of acquired businesses %', 'driver', 'pct', e26_in=0.0, ae_in=0.0,
      note='Assumption: acquired businesses break even at the adjusted operating level (already inside the group margin lever).')
    S('m_ppe', '  PP&E (technology) % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.05)
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.25,
      note='Assumption: technology and customer relationships ~25% of consideration, the remainder goodwill (Visa\'s FY22–25 deals were mostly goodwill).')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=7)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (non-GAAP item)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)')
    blank()

    # ------------------------------------------------------------------ cost drivers & adjusting items
    S('d_hdr', 'Cost drivers, D&A, share-based compensation & adjusting items', 'block',
      note='COST DRIVERS — expense lines are allocated from adjusted opex by the 9M FY26 mix; adjusting items are added back on their GAAP line')
    for k, lab, dk, item in LINES:
        S(f'mx_{k}', f'  {lab} (ex adjusting items) % of adjusted operating expenses', 'pct', 'pct',
          hist=lambda dk=dk, item=item: (f'=IF(ISNUMBER({V("aox")}),IFERROR((N({V("is_" + dk)})' + (f'-N({V("d_" + item)})' if item else '') + f')/{V("aox")},""),"")'),
          fc=lambda k=k: f'=${QE}${R["mx_" + k]}' if CTX.col.kind != 'QE' else None,
          qe=lambda dk=dk, item=item: (f'=IFERROR((SUM({Q1}{R["is_" + dk]}:{Q3}{R["is_" + dk]})' + (f'-{ACT("d_" + item)}' if item else '') + f')/{ACT("aox")},0)'),
          note='History: (GAAP line − adjusting items recorded on it) ÷ adjusted opex. Forecast: 9M FY26 mix, held.' if k == 'pers' else None)
    S('mx_chk', '  Check: expense-line mix sums to 100% (should be 0)', 'check', 'pct',
      fc=lambda: '=ROUND(' + '+'.join(V('mx_' + k) for k, *_ in LINES) + '-1,4)')
    S('d_dna_pct', '  Depreciation & amortization (GAAP) % of net revenue', 'pct', 'pct', all=ratio('is_dna', 'is_rev'))
    S('d_sbc', '  Share-based compensation (cash-flow statement)', 'line', 'm', data='cf_sbc', flow=True,
      qe=lambda: f'={P("d_sbc")}*(1+IFERROR({ACT("d_sbc")}/{ACT0("d_sbc")}-1,0))', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}',
      note='Q4/26E: prior-year quarter × 9M FY26 y/y; 2027E+: % of net revenue. Visa does not adjust out share-based compensation.')
    S('d_sbc_pct', '  Share-based compensation % of net revenue', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_adj_h', '  Operating adjusting items (pre-tax, excluded from non-GAAP by the company; forecast inputs):', 'sub', 'gen')
    S('d_litig', '  Litigation provision (U.S. covered litigation, VE territory and other significant matters)', 'line', 'm', data='oa_litig', flow=True,
      labkey='oa_litig_lab', qe=lambda: f'={PT("pt_litig")}', ae_in=0.0, note=MAN['litigation']['note'])
    S('d_amort', '  Amortization of acquired intangible assets (inside D&A)', 'line', 'm', data='oa_amort', flow=True, labkey='oa_amort_lab',
      qe=lambda: f'={PT("pt_amort")}', ae=lambda: f'={V("d_amort_sch")}+N({V("m_amort")})', note=MAN['amort']['note'])
    S('d_amort_sch', '  Amortization schedule — acquired intangibles held at 30-Jun-2026 (assumption from the 10-K schedules)', 'driver', 'm', ae_in=V0['amort_sched'])
    S('d_acq', '  Acquisition-related costs', 'line', 'm', data='oa_acq', flow=True, labkey='oa_acq_lab', qe=lambda: f'={PT("pt_acq")}',
      ae=lambda: f'={V("m_spend")}*{V("d_acq_pct")}+{V0["acq_base"]}')
    S('d_acq_pct', '  Acquisition costs % of acquisition spend (plus $60m p.a. integration base)', 'pct', 'pct', ae_in=0.03)
    S('d_restr', '  Severance, restructuring & lease consolidation costs', 'line', 'm', data='oa_restr', flow=True, labkey='oa_restr_lab', qe_in=0.0, ae_in=0.0,
      note='Q3 FY26 severance $563m (organizational efficiency). No further charges assumed (assumption).')
    S('d_ve', '  Visa Europe items (framework agreement loss FY2016)', 'line', 'm', data='oa_ve', flow=True, labkey='oa_ve_lab', fc=lambda: '=0')
    S('d_other', '  Other items (indirect taxes, charitable contributions, Russia-Ukraine charges, IPO-era restructuring)', 'line', 'm', data='oa_other',
      flow=True, labkey='oa_other_lab', fc=lambda: '=0')
    S('d_nadj_h', '  Non-operating adjusting items (pre-tax; income +):', 'sub', 'gen')
    S('n_eqinv', '  (Gains) losses on equity investments, net (adjustment; + = loss added back)', 'line', 'm', data='na_eqinv', flow=True, labkey='na_eqinv_lab', fc=lambda: '=0',
      note='Fair-value and sale gains / losses on equity investments, excluded from non-GAAP from FY2020. Forecast nil (no market view).')
    S('n_ve', '  Visa Europe items (put-option revaluation, currency forwards, FX on euro deposits; FY2010–16)', 'line', 'm', data='na_ve', flow=True, labkey='na_ve_lab', fc=lambda: '=0')
    S('n_other', '  Other non-operating items (FY2008–09 escrow income / settlement accretion; FY2018 charitable contribution)', 'line', 'm', data='na_other',
      flow=True, labkey='na_other_lab', fc=lambda: '=0')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF OPERATIONS (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (GAAP lines = adjusted opex × mix + adjusting items on their line; interest on opening balances)')
    S('is_rev', 'Net revenue', 'total', 'm', data='rev_net', flow=True, fc=lambda: f'={V("rev_build")}', note='Forecast linked to the revenue build.')
    S('is_rev_g', '  Net revenue y/y %', 'growth', 'pct', all=growth('is_rev'))
    for k, lab, dk, item in LINES:
        S(f'is_{dk}', lab, 'line', 'm', data=dk, flow=True,
          fc=lambda k=k, item=item: f'={V("aox")}*{V("mx_" + k)}' + (f'+{V("d_" + item)}' if item else ''))
    S('is_othop', 'Other operating items shown separately (Visa Europe framework agreement loss FY2016)', 'line', 'm', data='oth_op', flow=True, labkey='oth_op_labels',
      fc=lambda: f'={V("d_ve")}+{V("d_other")}')
    S('is_opex', 'Total operating expenses', 'line_b', 'm', data='opex', flow=True,
      fc=lambda: '=' + '+'.join(V('is_' + dk) for _, _, dk, _ in LINES) + f'+{V("is_othop")}')
    S('is_opex_chk', '  Check: total operating expenses = adjusted opex + operating adjusting items (should be 0)', 'check', 'm',
      fc=lambda: f'=ROUND({V("is_opex")}-{V("aox")}-{V("o_tot")},1)')
    S('is_oi', 'Operating income', 'total', 'm', data='opinc', flow=True, fc=lambda: f'={V("is_rev")}-{V("is_opex")}')
    S('is_oi_chk', '  Check: net revenue − operating expenses = operating income (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_oi")}),IF(ABS({V("is_rev")}-{V("is_opex")}-{V("is_oi")})<=1.01,0,ROUND({V("is_rev")}-{V("is_opex")}-{V("is_oi")},1)),"")')
    S('is_oi_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('is_intexp', 'Interest expense', 'line', 'm', data='int_exp', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_rev")}*{V("ds_r_rev")}+{V("ds_fees")}',
      note='Shown separately from FY2016 (earlier inside non-operating income). Q4/26E point estimate; 2027E+ = rate × opening notes + rate × opening commercial paper + fees (no circularity).')
    S('is_invoth', 'Investment income (expense) and other', 'line', 'm', data='inv_oth', flow=True, qe=lambda: f'={PT("pt_inv")}',
      ae=lambda: f'=({P("cf_end")}+{P("bs_inv")})*{V("ds_r_cash")}+{V("n_eqinv")}*-1',
      note='Investment income on cash, investment securities and the litigation escrow; equity-investment gains / losses. 2027E+: yield × opening cash & investments.')
    S('is_nonop', 'Total non-operating income (expense)', 'line_b', 'm', data='nonop', flow=True, fc=lambda: f'={V("is_invoth")}-{V("is_intexp")}')
    S('is_ebt', 'Income before income taxes', 'line_b', 'm', data='ebt', flow=True, fc=lambda: f'={V("is_oi")}+{V("is_nonop")}')
    S('is_ebt_chk', '  Check: operating income + non-operating = pre-tax income (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_ebt")}),IF(ABS({V("is_oi")}+{V("is_nonop")}-{V("is_ebt")})<=1.01,0,ROUND({V("is_oi")}+{V("is_nonop")}-{V("is_ebt")},1)),"")')
    S('is_tax', 'Income tax provision', 'line', 'm', data='tax', flow=True, fc=lambda: f'={V("e_adjtax")}+{V("e_tax")}',
      note='Forecast = non-GAAP tax + tax effect of the adjusting items (negative; items taxed at the non-GAAP rate).')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'))
    S('is_ni_tot', 'Net income (incl. non-controlling interest)', 'line_b', 'm', data='ni_tot', flow=True, fc=lambda: f'={V("is_ebt")}-{V("is_tax")}')
    S('is_nci', '  Non-controlling interest (Visa Japan to FY2012; none since)', 'line', 'm', data='nci', flow=True, fc=lambda: '=0')
    S('is_ni', 'Net income attributable to Visa Inc.', 'total', 'm', flow=True,
      all=lambda: f'=IF(ISNUMBER({V("is_ni_tot")}),{V("is_ni_tot")}-N({V("is_nci")}),"")')
    S('is_ni_pub', '  Memo: net income attributable as reported', 'memo', 'm', data='ni', flow=True)
    S('is_ni_chk', '  Check: net income vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=1.01,0,ROUND({V("is_ni")}-{V("is_ni_pub")},1)),"")')
    S('is_dda', '  Memo: depreciation & amortization (total, incl. acquired intangibles)', 'memo_calc', 'm', all=lambda: f'=IF(ISNUMBER({V("is_dna")}),{V("is_dna")},"")')
    S('is_sbc', '  Memo: share-based compensation', 'memo_calc', 'm', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per class A share — as-converted; split-adjusted for the 4-for-1 split of Mar-2015)', 'sub', 'gen')
    S('sh_dil', '  Weighted-average diluted class A shares, as-converted (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("bb_beg", E26)}-${E26}${R["bb_sh"]}*0.5+${E26}${R["bb_iss"]}*0.5',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note=('As-converted: class B / C common and series A / B / C preferred on an as-converted basis (×4 before the Mar-2015 split). Q4 FY18–20: 4 × fiscal year − Q1–Q3 '
            '(image-based releases). Q4/26E: 30-Jun-2026 proxy − half the Q4 buybacks + plan issuance. 2027E+: average of beginning and ending shares.'))
    S('eps_dil', 'EPS — diluted, class A ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")',
      note='Net income ÷ as-converted diluted class A shares (= the company\'s class A diluted EPS; ±$0.01).')
    S('eps_dil_g', '  EPS — diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: diluted class A EPS as reported ($, split-adjusted)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: (f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0101,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")'
                    if pkey(CTX.col) != '2008' else '="n/m"'))
    S('dps', '  Dividends declared per class A share ($)', 'line', 'ps', data='dps', flow=True, qe_in=V0['dps_q'],
      ae=lambda: f'={P("dps")}*(1+{V("dps_g")})', note='Q4/26E: $0.670 declared 28-Jul-2026 (Q3 FY26 release). 2027E+: prior year × (1 + growth).')
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'])
    blank()

    # ------------------------------------------------------------------ RECON 1: GAAP operating income -> adjusted operating income
    S('sec_r1', 'RECONCILIATION: GAAP OPERATING INCOME → ADJUSTED OPERATING INCOME (company non-GAAP operating expenses)', 'section',
      note='NON-GAAP OPEX — per the release reconciliations ("GAAP / items / non-GAAP" tables); company item labels per period in the cell comments of the cost-driver rows')
    S('o_op', 'Operating income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_oi")}')
    for c, lab in (('litig', 'Litigation provision'), ('amort', 'Amortization of acquired intangible assets'), ('acq', 'Acquisition-related costs'),
                   ('restr', 'Severance, restructuring & lease consolidation'), ('ve', 'Visa Europe items'), ('other', 'Other items')):
        S(f'o_{c}', f'  (+) {lab}', 'line', 'm', all=lambda c=c: f'={V("d_" + c)}')
    S('o_tot', '  Total operating adjusting items (pre-tax)', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_litig")}),{nsum(["o_" + c for c in OPC])},"")')
    S('o_adj', '  = Adjusted operating income (model bridge)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_tot")},"")',
      note='Equals net revenue − non-GAAP operating expenses (check in the opex block).')
    S('o_chk', '  Check: bridge vs revenue-build adjusted operating income (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("o_adj")}),ISNUMBER({V("aoi")})),ROUND({V("o_adj")}-{V("aoi")},1),"")')
    S('o_adj_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_def', '  Definition / basis (company non-GAAP definition in force)', 'text', 'gen',
      note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    blank()

    # ------------------------------------------------------------------ RECON 2: NI -> EBITDA -> adjusted EBITDA (model definition)
    S('sec_r2', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (MODEL DEFINITION — Visa publishes no EBITDA)', 'section',
      note='EBITDA (model) — net income + tax − non-operating income + D&A = EBITDA; + operating adjusting items other than acquired-intangible amortization (already in D&A) = adjusted EBITDA')
    S('r_ni', 'Net income (GAAP, incl. NCI)', 'line_b', 'm', all=lambda: f'={V("is_ni_tot")}')
    S('r_tax', '  (+) Income tax provision', 'line', 'm', all=lambda: f'={V("is_tax")}')
    S('r_nonop', '  (−) Non-operating income (expense)', 'line', 'm', all=lambda: f'=-{V("is_nonop")}')
    S('r_oi', '  = Operating income', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_tax")}+{V("r_nonop")},"")')
    S('r_oi_chk', '  Check: vs reported operating income (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("r_oi")}),IF(ABS({V("r_oi")}-{V("is_oi")})<=1.01,0,ROUND({V("r_oi")}-{V("is_oi")},1)),"")')
    S('r_dna', '  (+) Depreciation & amortization', 'line', 'm', all=lambda: f'={V("is_dda")}')
    S('r_ebitda', '  = EBITDA', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_oi")}),ISNUMBER({V("r_dna")})),{V("r_oi")}+{V("r_dna")},"")')
    S('r_adjx', '  (+) Operating adjusting items excl. acquired-intangible amortization', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_tot")}),{V("o_tot")}-{V("o_amort")},"")')
    S('r_adj', '  = Adjusted EBITDA (model definition)', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda")}),ISNUMBER({V("r_adjx")})),{V("r_ebitda")}+{V("r_adjx")},"")',
      note='Model definition (Visa publishes no EBITDA): adjusted operating income + D&A excl. acquired-intangible amortization. Used for leverage and EV / EBITDA.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_chk', '  Check: adjusted EBITDA − D&A + acquired amortization = adjusted operating income (should be 0; ±1 rounding)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_adj")}),ISNUMBER({V("o_adj")})),IF(ABS({V("r_adj")}-{V("r_dna")}+{V("o_amort")}-{V("o_adj")})<=1.01,0,ROUND({V("r_adj")}-{V("r_dna")}+{V("o_amort")}-{V("o_adj")},1)),"")')
    S('r_ebit_h', 'To adjusted EBIT, full-cost (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ddan', '  (−) Depreciation & amortization (total)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_dda")}),-{V("is_dda")},"")')
    S('r_ebit', '  = Adjusted EBIT, full-cost (adjusted EBITDA − total D&A = adjusted operating income − acquired-intangible amortization)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+{V("r_ddan")},"")')
    S('r_ebit_m', '  Adjusted EBIT (full-cost) margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: acquisition, severance & restructuring costs (cash costs adjusted out; deducted in the DCF)', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_acq")}),{V("o_acq")}+{V("o_restr")},"")')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: NET INCOME / DILUTED EPS → NON-GAAP NET INCOME → NON-GAAP EPS (company definition)', 'section',
      note='NON-GAAP EPS — net income + pre-tax adjusting items (operating and non-operating) − tax effect of the items (incl. tax-only items: deferred-tax remeasurements, tax reserve reversals)')
    S('e_ni', 'Net income attributable (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('e_op', '  (+) Operating adjusting items (pre-tax)', 'line', 'm', all=lambda: f'={V("o_tot")}')
    S('e_nop', '  (+) Non-operating adjusting items (pre-tax)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("n_eqinv")}),{nsum(["n_" + c for c in NOPC])},"")')
    S('e_tax', '  (−) Tax effect of the adjustments & tax-only items', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("e_pubni")}),{V("e_pubni")}-{V("e_ni")}-{V("e_op")}-{V("e_nop")},IF(ISNUMBER({V("e_ni")}),0,""))',
      fc=lambda: f'=-({V("e_op")}+{V("e_nop")})*{V("e_rate")}',
      note='Historical: published non-GAAP net income − GAAP net income − pre-tax items (covers the FY2008–09 normalized-rate tables and tax-only items). Forecast: items × adjusted tax rate.')
    S('e_adjni', '  = Non-GAAP net income (model bridge)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("e_tax")}),{V("e_ni")}+{V("e_op")}+{V("e_nop")}+{V("e_tax")},"")')
    S('e_pubni', '  Company-published non-GAAP net income', 'memo', 'm', data='adj_ni_pub', flow=True)
    S('e_sh', '  Weighted-average diluted class A shares (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Non-GAAP EPS — diluted class A ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published non-GAAP EPS ($, split-adjusted)', 'eps_memo', 'ps', data='adj_eps_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.015 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0151,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Non-GAAP EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_adjebt', '  Non-GAAP pre-tax income (adjusted operating income + non-operating income + non-operating items)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_adj")}),{V("o_adj")}+{V("is_nonop")}+{V("e_nop")},"")')
    S('e_adjtax', '  Non-GAAP income tax (pre-tax − non-GAAP net income − NCI)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_adjni")}),ISNUMBER({V("e_adjebt")})),{V("e_adjebt")}-{V("e_adjni")}-N({V("is_nci")}),"")',
      fc=lambda: f'={V("e_adjebt")}*{V("e_rate")}')
    S('e_rate', '  Non-GAAP effective tax rate', 'pct', 'pct', all=ratio('e_adjtax', 'e_adjebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Q4/26E: point estimate from the FY26 18.0–18.25% commentary (UNVERIFIED; 9M FY26 non-GAAP 17.8%). 2027E+: input.')
    S('e_def', '  Definition / basis (company non-GAAP EPS definition)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Net revenue y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_pv', '  Nominal payments volume y/y %', 'growth', 'pct', all=growth('k_pv'))
    S('gm_ptx', '  Processed transactions y/y %', 'growth', 'pct', all=growth('k_ptx'))
    S('gm_adjop', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating income (GAAP) y/y %', 'growth', 'pct', all=growth('is_oi'))
    S('gm_ni', '  Net income y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Non-GAAP EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_ci', '  Client incentives % of gross revenue', 'pct', 'pct', all=ratio('rev_ci', 'rev_gross'))
    S('gm_adjop_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_inc', '  Incremental adjusted operating margin (Δ adjusted OI / Δ net revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_pers', '  Personnel % of net revenue', 'pct', 'pct', all=ratio('is_personnel', 'is_rev'))
    S('gm_mkt', '  Marketing % of net revenue', 'pct', 'pct', all=ratio('is_marketing', 'is_rev'))
    blank()
