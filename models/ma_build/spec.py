"""Row specification of the MA Model sheet, part 1 (MLM template layout and process):
net revenue build (payment network = GDV x yield; value-added services and solutions) -> legacy revenue categories (memo) ->
pending BVNK acquisition and future-M&A lever -> group total & FY26 guidance calibration (net revenue, adjusted operating expenses)
-> cost drivers -> income statement -> GAAP-to-adjusted bridges -> growth & margins."""
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
def E26a(key): return f'${E26}${R[key]}'                  # FY2026E column (absolute) - holds the calibration deltas
def QQ(key): return f'({Q3E}{R[key]}+{Q4E}{R[key]})'      # Q3/26E + Q4/26E
def ACT(key): return f'SUM({Q1}{R[key]}:{Q2}{R[key]})'    # H1-26 actual (Q1-Q2/26)
def ACT0(key): return f'SUM({PQ1}{R[key]}:{PQ2}{R[key]})' # H1-25 actual (Q1-Q2/25)
def B1(key): return f'{LQ}{R[key]}'                       # 30-Jun-2026 balance
def QCHK(key, pub, tol=1.1, nf=1):
    return lambda: f'=IF(AND(ISNUMBER({V(key)}),ISNUMBER({V(pub)})),IF(ABS({V(key)}-{V(pub)})<={tol},0,ROUND({V(key)}-{V(pub)},{nf})),"n/p")'

LINES = ['pn', 'vas']
OPX = ['d_lit', 'd_restr', 'd_oadj']                       # opex special items (pre-tax, excluded from adjusted)

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of the FY26 guidance (UNVERIFIED: call commentary, not in an SEC filing).'))
    r = 11
    SCEN_ROWS.append((r, 'out_hdr', V0['out_hdr'], 'High', 'Mid', 'Low', V0['out_note'])); r += 1
    for key, lab, (hi, mid, lo), nf, note in V0['outlook']:
        SC[key] = r; SCEN_ROWS.append((r, 'out', lab, hi, mid, lo, note, nf)); r += 1
    r += 1
    SCEN_ROWS.append((r, 'pt_hdr', 'Q3/26E – Q4/26E and FY26 point estimates (all cases)', None, None, None, None)); r += 1
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
    # ------------------------------------------------------------------ NET REVENUE BUILD
    S('sec_rev', 'NET REVENUE BUILD — PAYMENT NETWORK (GDV × YIELD) · VALUE-ADDED SERVICES & SOLUTIONS (single reportable segment)', 'section',
      note='REVENUE BUILD — modelling logic (GDV → payment network net revenue at the network yield; value-added services and solutions by growth; Σ = net revenue → adjusted opex → adjusted operating income → GAAP P&L)')
    blank()
    S('k_hdr', 'Network volume drivers (Mastercard-branded programs, worldwide; operating-performance tables in each release)', 'block',
      note='VOLUME DRIVERS — GDV in USD = prior year × (1 + local-currency growth) × (1 + FX translation)')
    S('k_gdv', '  Gross dollar volume (GDV), USD bn', 'line', 'm', data='gdv', flow=True,
      qe=lambda: f'={P("k_gdv")}*(1+{V("k_gdv_gu")})', ae=lambda: f'={P("k_gdv")}*(1+{V("k_gdv_gu")})',
      note='Release "Mastercard Incorporated Operating Performance" table, all programs, worldwide (three months; annual = full-year table). GDV = purchase + cash volume; customer-reported and revised over time.')
    S('k_gdv_gl', '    GDV growth, local currency %', 'growth', 'pct', data='gdv_g_loc',
      qe=lambda: f'=AVERAGE({Q1}{R["k_gdv_gl"]}:{Q2}{R["k_gdv_gl"]})', ae=lambda: '=' + CH(SC['GDV'][CTX.col.year]),
      e26=lambda: f'=AVERAGE({Q1}{R["k_gdv_gl"]}:{Q4E}{R["k_gdv_gl"]})',
      note='As published (EU-rule-adjusted figures 2016–17 are in the transcription notes, not used). Q3/Q4-26E: H1-26 average (8.0%, 7.3%→8.0%); 2027E+: scenario lever.')
    S('k_fx', '    FX translation (USD growth − local-currency growth), pp', 'growth', 'pct',
      hist=lambda: f'=IF(AND(ISNUMBER({V("k_gdv_gu")}),ISNUMBER({V("k_gdv_gl")})),{V("k_gdv_gu")}-{V("k_gdv_gl")},"")',
      qe_in={3: V0['fx_q3'], 4: V0['fx_q4']}, ae_in=0.0, e26=lambda: f'={V("k_gdv_gu")}-{V("k_gdv_gl")}',
      note='Q3/Q4-26E: point estimates consistent with the ~1 ppt FY26 FX tailwind in the (unverified) outlook after +2.6 ppt in H1-26; 2027E+: constant currency (0).')
    S('k_gdv_gu', '    GDV growth, USD %', 'growth', 'pct', data='gdv_g_usd', fc=lambda: f'=(1+{V("k_gdv_gl")})*(1+{V("k_fx")})-1', e26=growth('k_gdv'),
      note='2026E = 2026E GDV ÷ 2025 GDV − 1; local-currency 2026E = average of the quarters (approximation).')
    S('k_xb', '  Memo: cross-border volume growth, local currency % (release text)', 'growth', 'pct', data='k_xb_g',
      note='Release narrative ("cross-border volume growth of x% on a local currency basis"); 2006–09 not stated. Drives cross-border assessments inside payment network yield.')
    S('k_sw', '  Memo: switched transactions growth % ("processed transactions" to Q3-16; release text)', 'growth', 'pct', data='k_sw_g')
    S('k_cards', '  Memo: Mastercard and Maestro-branded cards issued (bn; period end, release text)', 'memo', 'm2', data='k_cards',
      note='Mastercard-branded only to 2009 (0.8–1.0bn); including Maestro from 2010.')
    blank()
    S('pn_hdr', 'Payment network (assessments for switching, cross-border, scheme fees, less payment network rebates & incentives)', 'block',
      note='PAYMENT NETWORK — modelling logic (2027E+: GDV × yield; 2026E H2: prior-year quarter × (1 + H1-26 y/y + calibration Δ))')
    S('pn', '  Payment network net revenue', 'line_b', 'm', data='rc_pn', flow=True,
      qe=lambda: f'={P("pn")}*(1+{V("pn_g")})', ae=lambda: f'={V("k_gdv")}*{V("pn_yld")}/10',
      note=('10-Q / 10-K revenue tables (current presentation from the FY2022 10-K; FY2020–21 and 2021–22 quarters from the next filings\' comparatives, '
            'Q4 = FY − 9M). Before 2020 net revenue is not split this way (legacy categories in memo below).'))
    S('pn_g', '    y/y %', 'growth', 'pct', all=growth('pn'), qe=lambda: f'={V("pn_pre")}+{E26a("cal_g")}',
      note='Q3/Q4-26E: H1-26 y/y growth + net revenue calibration Δ (Group block).')
    S('pn_pre', '    Q3/Q4-26E growth before revenue calibration (H1-26 y/y)', 'driver', 'pct', qe=lambda: f'=IFERROR({ACT("pn")}/{ACT0("pn")}-1,0)')
    S('pn_yld', '  Payment network yield (net revenue ÷ GDV, bps)', 'pct', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("pn")}),ISNUMBER({V("k_gdv")})),IFERROR({V("pn")}/{V("k_gdv")}*10,""),"")',
      ae=lambda: f'={P("pn_yld")}*(1+{V("pn_yg")})',
      note='bps of GDV (USD m ÷ USD bn × 10). Mix of cross-border (higher yield), switching, pricing, less rebates & incentives on new and renewed deals. 2027E+: prior year × (1 + yield change lever).')
    S('pn_yg', '  Payment network yield change y/y % (scenario lever 2027E+)', 'growth', 'pct', all=growth('pn_yld'), ae=lambda: '=' + CH(SC['YLD'][CTX.col.year]))
    S('pn_reb', '  Memo: payment network rebates & incentives growth % (release text, from 2020)', 'growth', 'pct', data='k_reb_g')
    S('pn_cn', '  Memo: payment network growth, currency-neutral % (release text)', 'growth', 'pct', data='k_pn_g_cn')
    blank()
    S('vas_hdr', 'Value-added services and solutions (cyber & intelligence, data & services, open banking, loyalty, processing)', 'block',
      note='VALUE-ADDED SERVICES — prior year × (1 + growth); includes acquisitions (Recorded Future Dec-2024) — the company reports VAS growth incl. M&A')
    S('vas', '  Value-added services and solutions net revenue', 'line_b', 'm', data='rc_vas', flow=True,
      qe=lambda: f'={P("vas")}*(1+{V("vas_g")})', ae=lambda: f'={P("vas")}*(1+{V("vas_g")})',
      note='Same sources as payment network. Q3/Q4-26E: prior-year quarter × (1 + H1-26 y/y + calibration Δ); 2027E+: scenario lever.')
    S('vas_g', '    y/y %', 'growth', 'pct', all=growth('vas'), qe=lambda: f'={V("vas_pre")}+{E26a("cal_g")}', ae=lambda: '=' + CH(SC['VAS'][CTX.col.year]))
    S('vas_pre', '    Q3/Q4-26E growth before revenue calibration (H1-26 y/y)', 'driver', 'pct', qe=lambda: f'=IFERROR({ACT("vas")}/{ACT0("vas")}-1,0)')
    S('vas_cn', '  Memo: value-added services growth, currency-neutral % (release text)', 'growth', 'pct', data='k_vas_g_cn')
    S('vas_mix', '  Value-added services % of net revenue', 'pct', 'pct', all=ratio('vas', 'g_rev'))
    blank()
    S('ns', 'Net revenue not split into payment network / value-added services (FY2006–19, Q1-13 – Q4-20)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("pn")}),0,{V("is_rev")})', fc=lambda: '=0',
      note='History before the current presentation (first presented in the FY2022 10-K, with FY2020–21 comparatives): consolidated net revenue. The legacy categories are in the memo block below.')
    S('lg_h', '  Legacy revenue categories (as presented FY2006–Q3-22; FY2006 not published; 2007–08 recast in the FY2009 10-K) — memo:', 'sub', 'gen')
    for k, lab in (('dom', 'Domestic assessments'), ('xb', 'Cross-border volume fees'), ('tp', 'Transaction processing fees'),
                   ('oth', 'Other revenues'), ('reb', 'Rebates and incentives (contra-revenue)')):
        S(f'lg_{k}', f'    {lab}', 'memo', 'm', data=f'rcl_{k}', flow=True)
    S('lg_chk', '    Check: legacy categories vs net revenue (should be 0)', 'check', 'm',
      hist=lambda: (f'=IF(ISNUMBER({V("lg_dom")}),IF(ABS({nsum(["lg_dom", "lg_xb", "lg_tp", "lg_oth", "lg_reb"])}-{V("is_rev")})<=1.1,0,'
                    f'ROUND({nsum(["lg_dom", "lg_xb", "lg_tp", "lg_oth", "lg_reb"])}-{V("is_rev")},0)),"")'))
    S('lg_xbg', '    Cross-border volume fees y/y %', 'growth', 'pct', all=growth('lg_xb'))
    S('lg_rebp', '    Rebates & incentives % of gross revenue', 'pct', 'pct',
      all=lambda: f'=IF(ISNUMBER({V("lg_reb")}),IFERROR(-{V("lg_reb")}/({V("is_rev")}-{V("lg_reb")}),""),"")')
    S('pm_h', '  Payment network key metrics (current presentation, from FY2022; assessments are gross of rebates) — memo:', 'sub', 'gen')
    for k, lab in (('dom', 'Domestic assessments'), ('xb', 'Cross-border assessments'), ('tp', 'Transaction processing assessments'),
                   ('oth', 'Other network assessments'), ('reb', 'Payment network rebates & incentives (MD&A text)')):
        S(f'pm_{k}', f'    {lab}', 'memo', 'm', data=f'rcm_{k}', flow=True)
    S('pm_chk', '    Check: key metrics vs payment network net revenue (should be 0)', 'check', 'm',
      hist=lambda: (f'=IF(AND(ISNUMBER({V("pm_dom")}),ISNUMBER({V("pm_reb")})),IF(ABS({nsum(["pm_dom", "pm_xb", "pm_tp", "pm_oth", "pm_reb"])}-{V("pn")})<=1.1,0,'
                    f'ROUND({nsum(["pm_dom", "pm_xb", "pm_tp", "pm_oth", "pm_reb"])}-{V("pn")},0)),"")'))
    blank()

    # ------------------------------------------------------------------ pending acquisition: BVNK
    S('bv_hdr', 'Pending acquisition — BVNK (stablecoin payments infrastructure): $1.5bn + up to $300m contingent; expected to close by end-Q3-2026', 'block',
      note='BVNK — closing assumed 30-Sep-2026 (Q2-26 10-Q: "expected to complete before the end of the third quarter"); revenue and PPA not disclosed (flagged inputs)')
    S('bv_on', '  Deal switch (1 = include BVNK from 30-Sep-2026; 0 = exclude)', 'driver', 'gen', e26_in=1, ae=lambda: f'={P("bv_on")}')
    S('bv_cons', '  Cash consideration at closing (USDm)', 'line', 'm', e26=lambda: f'={V0["bv_cons"]}*{V("bv_on")}', ae_in=0.0, note=MAN['deals']['bvnk']['status'])
    S('bv_rev', '  BVNK net revenue (not disclosed — input 0; flag)', 'driver', 'm', qe_in=0.0, ae_in=0.0,
      note='Not disclosed by Mastercard; outlook excludes acquisitions. Enter an estimate here to add BVNK revenue on top of the organic build (adjusted opex below).')
    S('bv_ox', '  BVNK adjusted operating expenses (not disclosed — input 0; flag)', 'driver', 'm', qe_in=0.0, ae_in=0.0)
    S('bv_intp', '  Acquired intangibles % of consideration (assumption)', 'driver', 'pct', e26_in=0.25, ae=lambda: f'={P("bv_intp")}',
      note='Assumption: Recorded Future (Dec-2024) — $2.65bn with ~$1.7bn goodwill, i.e. ~35% to intangibles and other net assets; 25% assumed for an early-stage platform.')
    S('bv_life', '  Intangible amortization life (years, assumption)', 'driver', 'gen', e26_in=8, ae=lambda: f'={P("bv_life")}')
    S('bv_amort', '  Amortization of BVNK intangibles (in D&A)', 'line', 'm',
      e26=lambda: '=0', ae=lambda: f'=IFERROR({E26a("bv_cons")}*{E26a("bv_intp")}/{V("bv_life")},0)')
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — value-added services bolt-ons; deals closed from 2027E)', 'block',
      note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=8.0, e26_in=0.0,
      note='Assumption: Recorded Future $2.65bn (~9x sales at announcement), Finicity $825m, Ekata $850m — high-growth software / data assets at high-single-digit sales multiples.')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.12)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}', note='Mid-year convention.')
    S('m_m', '  Adjusted operating margin of acquired businesses (after amortization) %', 'driver', 'pct', e26_in=0.0, ae_in=0.15,
      note='Assumption: acquired data / security businesses are margin-dilutive versus the ~60% group adjusted operating margin.')
    S('m_oi', '  Adjusted operating income from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.30)
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=8)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (inside adjusted operating income)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)',
      note='Mastercard does not adjust out amortization of acquired intangibles; the acquired-business margin above is after amortization.')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group Total — net revenue & adjusted operating income → FY26 guidance calibration (guidance UNVERIFIED: earnings-call commentary)', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Net revenue (build)', 'total', 'm',
      hist=lambda: f'=N({V("pn")})+N({V("vas")})+N({V("ns")})',
      fc=lambda: f'={V("pn")}+{V("vas")}+N({V("ns")})+N({V("m_rev")})+N({V("bv_rev")})*N({E26a("bv_on")})',
      note='Payment network + value-added services (+ not split, history) (+ future acquisitions and BVNK from 2026E).')
    S('g_rev_g', '  Net revenue y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: build vs consolidated net revenue (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=1.1,0,ROUND({V("g_rev")}-{V("is_rev")},0)),"")')
    S('g_cn', '  Memo: company currency-neutral net revenue growth % (release; 2006–08: currency effect given only in points)', 'growth', 'pct', data='k_rev_g_cn')
    S('g_fx', '  Memo: currency effect on net revenue growth (reported − currency-neutral), pp', 'growth', 'pct',
      hist=lambda: f'=IF(AND(ISNUMBER({V("g_cn")}),ISNUMBER({V("g_rev_g")})),{V("g_rev_g")}-{V("g_cn")},"")')
    S('g_ox', 'Adjusted operating expenses (build)', 'line_b', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("o_adjox")}),{V("o_adjox")},"")',
      qe=lambda: f'={P("g_ox")}*(1+{V("g_ox_g")})+N({V("bv_ox")})*N({E26a("bv_on")})',
      ae=lambda: f'={V("g_arev")}*(1-{V("g_om")})',
      note=('Company adjusted operating expenses (GAAP less litigation provisions, restructuring and other special items). Q3/Q4-26E: prior-year quarter × (1 + H1-26 y/y + '
            'opex calibration Δ) (+ BVNK). 2027E+: adjusted net revenue × (1 − adjusted operating margin lever).'))
    S('g_ox_g', '  Adjusted operating expenses y/y %', 'growth', 'pct', all=growth('g_ox'), qe=lambda: f'={V("g_ox_pre")}+{E26a("cal_ox")}')
    S('g_ox_pre', '  Q3/Q4-26E adjusted opex growth before calibration (H1-26 y/y)', 'driver', 'pct', qe=lambda: f'=IFERROR({ACT("g_ox")}/{ACT0("g_ox")}-1,0)')
    S('g_arev', 'Adjusted net revenue (net revenue + revenue special items)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}+N({V("d_rev")}),"")', fc=lambda: f'={V("g_rev")}')
    S('g_adj', 'Adjusted operating income (build)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("g_ox")}),{V("g_arev")}-{V("g_ox")},"")',
      note='Adjusted net revenue − adjusted operating expenses (company definition); drives the GAAP P&L below.')
    S('g_om', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('g_adj', 'g_arev'),
      ae=lambda: '=' + CH(SC['OM'][CTX.col.year]) + f'+IFERROR(N({V("m_oi")})/{V("g_arev")}-N({V("m_rev")})/{V("g_arev")}*' + CH(SC['OM'][CTX.col.year]) + ',0)',
      note='2027E+: scenario margin lever on the organic business, blended with the future-acquisition margin.')
    S('g_adj_g', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('g_adj'))
    S('g_inc', '  Incremental adjusted operating margin (Δ adj. OI / Δ adj. net revenue)', 'pct', 'pct', all=incr('g_adj', 'g_arev'))
    S('g_chk_adj', '  Check: build vs adjusted operating income bridge (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_adj")}),ISNUMBER({V("o_aoi")})),IF(ABS({V("g_adj")}-{V("o_aoi")})<=1.1,0,ROUND({V("g_adj")}-{V("o_aoi")},0)),"")')
    S('cal_h', '  FY26 calibration (Q3/Q4-26E; deltas in the 2026E column):', 'sub', 'gen')
    S('cal_guid', '  Memo: FY26 net revenue end-point (FY2025 × (1 + guided reported growth); scenario) — UNVERIFIED guidance', 'memo', 'm',
      e26=lambda: f'={Y("is_rev", 2025)}*(1+{CH(SC["out_g"])})', note=V0['rev_guid_note'])
    S('cal_pre', '  Net revenue before calibration (Q3/Q4-26E helper; 2026E = Σ)', 'line', 'm',
      qe=lambda: f'={P("pn")}*(1+{V("pn_pre")})+{P("vas")}*(1+{V("vas_pre")})', e26=lambda: f'={QQ("cal_pre")}')
    S('cal_sens', '  Net revenue sensitivity to +1.00 of growth (Q3/Q4-26E helper; 2026E = Σ)', 'line', 'm',
      qe=lambda: f'={P("pn")}+{P("vas")}', e26=lambda: f'={QQ("cal_sens")}')
    S('cal_g', '  Calibration: Δ y/y growth applied to payment network and value-added services (Q3/Q4-26E)', 'driver', 'pct',
      e26=lambda: f'=({V("cal_guid")}-{ACT("g_rev")}-{V("cal_pre")})/{V("cal_sens")}',
      note='Closed-form solve: the uniform growth shift (vs H1-26 y/y rates) so that FY26 organic net revenue = the guidance end-point for the active scenario.')
    S('cal_rev_chk', '  Check: FY26 organic net revenue vs guidance end-point (should be 0)', 'check', 'm',
      e26=lambda: f'=ROUND({V("g_rev")}-N({QQ("bv_rev")})*N({V("bv_on")})-{V("cal_guid")},0)')
    S('cal_oxg', '  Memo: FY26 adjusted operating expenses end-point (FY2025 × (1 + guided growth); scenario) — UNVERIFIED guidance', 'memo', 'm',
      e26=lambda: f'={Y("g_ox", 2025)}*(1+{CH(SC["out_ox"])})', note=V0['ox_guid_note'])
    S('cal_ox_pre', '  Adjusted opex before calibration (Q3/Q4-26E helper; 2026E = Σ)', 'line', 'm', qe=lambda: f'={P("g_ox")}*(1+{V("g_ox_pre")})', e26=lambda: f'={QQ("cal_ox_pre")}')
    S('cal_ox_sens', '  Adjusted opex sensitivity to +1.00 of growth (helper; 2026E = Σ)', 'line', 'm', qe=lambda: f'={P("g_ox")}', e26=lambda: f'={QQ("cal_ox_sens")}')
    S('cal_ox', '  Calibration: Δ adjusted opex growth (Q3/Q4-26E)', 'driver', 'pct', e26=lambda: f'=({V("cal_oxg")}-{ACT("g_ox")}-{V("cal_ox_pre")})/{V("cal_ox_sens")}',
      note='Solves the uniform shift in adjusted opex growth so that FY26 organic adjusted opex = the guidance end-point (scenario).')
    S('cal_ox_chk', '  Check: FY26 organic adjusted opex vs guidance end-point (should be 0)', 'check', 'm',
      e26=lambda: f'=ROUND({V("g_ox")}-N({QQ("bv_ox")})*N({V("bv_on")})-{V("cal_oxg")},0)')
    S('cal_cn', '  Memo: implied FY26 currency-neutral net revenue growth (end-point − FX point estimate) — guided "high end of low double digits"', 'memo_calc', 'pct',
      e26=lambda: f'={CH(SC["out_g"])}-{PT("pt_fxrev")}')
    S('cal_eps', '  Memo: FY26 adjusted EPS (model output; not guided)', 'eps_memo', 'ps', e26=lambda: f'={V("e_eps")}')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A, other income & special items', 'block', note='COST DRIVERS — inputs that drive forecast cost lines (Q3/Q4-26E: point estimates or H1 trend; 2027E+: % of net revenue or schedules)')
    S('d_am', '  Advertising & marketing % of net revenue', 'pct', 'pct', all=ratio('is_am', 'is_rev'),
      qe=lambda: f'={P("d_am")}+IFERROR({ACT("is_am")}/{ACT("is_rev")}-{ACT0("is_am")}/{ACT0("is_rev")},0)', ae_in=V0['am_pct'],
      note='Q3/Q4-26E: prior-year quarter ratio + H1-26 y/y drift; 2027E+ input. G&A is the balancing line to adjusted opex.')
    S('d_da', '  Depreciation & amortization (IS; incl. amortization of capitalized software and acquired intangibles)', 'line', 'm', data='da', flow=True,
      qe=lambda: f'={PT("pt_da")}', ae=lambda: f'={V("is_rev")}*{V("d_da_pct")}+N({V("bv_amort")})+N({V("m_amort")})',
      note='Q3/Q4-26E point estimate (Q2-26 $309m). 2027E+: % of net revenue + BVNK / future-acquisition amortization. FY2025 10-K schedule of finite-lived intangibles: $765m (2027) … $569m (2030) incl. capitalized software.')
    S('d_da_pct', '  D&A % of net revenue (organic)', 'pct', 'pct', all=ratio('d_da', 'is_rev'), ae_in=V0['da_pct'])
    S('d_sbc', '  Share-based compensation (cash-flow statement)', 'line', 'm', data='cf_sbc', flow=True,
      qe=lambda: f'={P("d_sbc")}*(1+IFERROR({ACT("d_sbc")}/{ACT0("d_sbc")}-1,0))', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}',
      note='Q3/Q4-26E: prior-year quarter × H1-26 y/y; 2027E+: % of net revenue. Mastercard does not adjust out share-based compensation.')
    S('d_sbc_pct', '  Share-based compensation % of net revenue', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_inv', '  Investment income (interest on cash & investments)', 'line', 'm', qe=lambda: f'={PT("pt_inv")}',
      ae=lambda: f'=({P("cf_end")}+{P("bs_inv")})*{V("ds_r_cash")}', note='Q3/Q4-26E point estimate (Q2-26 $88m); 2027E+: yield × opening cash, restricted cash and investments.')
    S('d_oth', '  Other income (expense), net — recurring (government grants, other)', 'line', 'm', qe=lambda: f'={PT("pt_oth")}', ae_in=V0['oth_inc'],
      note='H1-26 $106m incl. government grant agreements executed in Q4-25. Q3/Q4-26E: point estimate set so total other income (expense) ≈ −$125m in Q3 (UNVERIFIED call guidance).')
    S('d_adj_h', '  Special items (pre-tax, excluded from adjusted results; forecast inputs):', 'sub', 'gen')
    S('d_lit', '  Litigation provisions excluded from adjusted results (forecast: all litigation provisions)', 'line', 'm', data='oa_lit', flow=True, labkey='oa_lit_lab', qe_in=V0['lit_q'], ae_in=V0['lit_ae'],
      note=V0['lit_note'])
    S('d_restr', '  Restructuring charges', 'line', 'm', data='oa_restr', flow=True, labkey='oa_restr_lab', qe_in=0.0, ae_in=0.0,
      note='Q4-23 $82m, Q4-24 $190m, Q1-26 $202m (in G&A). Not forecast (assumption).')
    S('d_oadj', '  Other operating special items (Foundation 2006–08, settlements, pension termination, Venezuela, indirect tax, Russia, other)', 'line', 'm',
      data='oa_oth', flow=True, labkey='oa_oth_lab', fc=lambda: '=0')
    S('d_rev', '  Revenue special items (Russia-related rebate reversals 2022; + = adjusted revenue higher)', 'line', 'm', data='oa_rev', flow=True, labkey='oa_rev_lab', fc=lambda: '=0')
    S('d_eqgl', '  (Gains) losses on equity investments (excluded from Q2-19; + = loss added back)', 'line', 'm', data='oa_eqgl', flow=True, labkey='oa_eqgl_lab', fc=lambda: '=0')
    S('d_ngain', '  Other non-operating special items (Redecard gains, customer-agreement termination, other; + = loss added back)', 'line', 'm',
      data='oa_gain', flow=True, labkey='oa_gain_lab', fc=lambda: '=0')
    S('d_taxd', '  Discrete tax items excluded (net income effect; + = raises adjusted)', 'line', 'm', data='oa_taxd', flow=True, labkey='oa_taxd_lab', fc=lambda: '=0')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF OPERATIONS (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (operating income = adjusted operating income − special items; G&A is the balancing line)')
    S('is_rev', 'Net revenue', 'total', 'm', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the revenue build.')
    S('is_ga', 'General and administrative', 'line', 'm', data='ga', flow=True,
      fc=lambda: f'={V("g_ox")}-{V("is_am")}-{V("is_da")}+{V("d_restr")}+{V("d_oadj")}',
      note='Forecast = adjusted opex − advertising & marketing − D&A + restructuring and other special items booked in G&A (balancing line).')
    S('is_am', 'Advertising and marketing', 'line', 'm', data='am', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_am")}')
    S('is_da', 'Depreciation and amortization', 'line', 'm', data='da', flow=True, fc=lambda: f'={V("d_da")}')
    S('is_lit', 'Provision for litigation (settlements)', 'line', 'm', data='lit', flow=True, fc=lambda: f'={V("d_lit")}')
    S('is_char', 'Charitable contributions to the Mastercard Foundation (2006–08)', 'line', 'm', data='char', flow=True, fc=lambda: '=0')
    S('is_opex', 'Total operating expenses', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ga")}),SUM({V("is_ga")}:{V("is_char")}),"")')
    S('is_oi', 'Operating income', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_opex")}),{V("is_rev")}-{V("is_opex")},"")')
    S('is_oim', '  Operating margin %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('is_inv', 'Investment income', 'line', 'm', data='inv_inc', flow=True, fc=lambda: f'={V("d_inv")}')
    S('is_eq', 'Gains (losses) on equity investments, net', 'line', 'm', data='eq_gl', flow=True, fc=lambda: f'=-{V("d_eqgl")}')
    S('is_int', 'Interest expense', 'line', 'm', data='int_exp', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_rev")}*{V("ds_r_rev")}+{V("ds_fees")}',
      note='Q3/Q4-26E point estimate (full quarter of the $5.0bn June-2026 notes). 2027E+ = rate × opening notes + rate × opening commercial paper + fees (no circularity).')
    S('is_oth', 'Other income (expense), net', 'line', 'm', data='oth_inc', flow=True, fc=lambda: f'={V("d_oth")}-{V("d_ngain")}')
    S('is_ot', 'Total other income (expense)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_inv")}),{V("is_inv")}+{V("is_eq")}-{V("is_int")}+{V("is_oth")},"")')
    S('is_ebt', 'Income before income taxes', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_oi")}),{V("is_oi")}+{V("is_ot")},"")')
    S('is_tax', 'Income tax expense', 'line', 'm', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective income tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Q3/Q4-26E: 20.5% (non-GAAP 20–21% guided for Q3 and Q4 — UNVERIFIED call guidance; H1-26 GAAP 19.7%). 2027E+: input.')
    S('is_nit', 'Net income (incl. non-controlling interests)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_nci', '  Less: net income (loss) attributable to non-controlling interests', 'line', 'm', data='nci', flow=True, fc=lambda: '=0')
    S('is_ni', 'Net income attributable to Mastercard', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_nit")}),{V("is_nit")}-N({V("is_nci")}),"")')
    S('is_ni_chk', '  Check: net income vs reported (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=1.1,0,ROUND({V("is_ni")}-{V("is_ni_pub")},0)),"")')
    S('is_ni_pub', '  Memo: net income attributable to Mastercard as reported', 'memo', 'm', data='ni', flow=True)
    S('is_oi_chk', '  Check: operating income vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_oi_pub")}),IF(ABS({V("is_oi")}-{V("is_oi_pub")})<=1.1,0,ROUND({V("is_oi")}-{V("is_oi_pub")},0)),"")')
    S('is_oi_pub', '  Memo: operating income as reported', 'memo', 'm', data='oi', flow=True)
    S('is_rev_py', '  Memo: net revenue as re-presented in the following year\'s release (where different)', 'memo', 'm', data='rev_py', flow=True,
      note='2014 net revenue re-presented in the 2015 releases (reclassification of certain customer incentives); the model keeps the originally reported figures.')
    S('is_dda', '  Memo: depreciation & amortization', 'memo_calc', 'm', all=lambda: f'={V("is_da")}')
    S('is_sbc', '  Memo: share-based compensation', 'memo_calc', 'm', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share — Class A and Class B common stock combined; split-adjusted for the 10-for-1 split of Jan-2014)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={B1("bs_shares")}-${E26}${R["bb_sh"]}*{0.25 if CTX.col.q == 3 else 0.75}+${E26}${R["bb_iss"]}*{0.25 if CTX.col.q == 3 else 0.75}',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q3/Q4-26E: shares outstanding at 30-Jun-2026 − H2 buybacks (mid-quarter: ¼ in Q3, ¾ in Q4) + equity-plan issuance. 2027E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q2}{R["sh_dil"]}-{Q2}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")',
      note='Net income / weighted diluted shares (±$0.01 vs reported; 2008–09 two-class method ±$0.007).')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($, split-adjusted)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01, 2008–09 ±0.008 two-class)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0101,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('dps', '  Dividends declared per share ($)', 'line', 'ps', data='dps', flow=True, qe_in={3: V0['dps_q3'], 4: V0['dps_q4']},
      ae=lambda: f'={P("dps")}*(1+{V("dps_g")})',
      note='10-Q / 10-K "dividends declared per share" (split-adjusted). Mastercard declares the next year\'s higher quarterly rate in December (Q4). Q3-26E $0.87; Q4-26E $0.99 (assumption: +14%, 2025 +14.5%). 2027E+: prior year × (1 + growth).')
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'])
    blank()

    # ------------------------------------------------------------------ RECON 1: GAAP opex -> adjusted opex -> adjusted OI
    S('sec_r1', 'RECONCILIATION: GAAP OPERATING EXPENSES → ADJUSTED OPERATING EXPENSES → ADJUSTED OPERATING INCOME (company definitions)', 'section',
      note='ADJUSTED OPEX / MARGIN — per the release non-GAAP reconciliations ("special items"); item wording per period in the cell comments of the special-item rows')
    S('o_opex', 'Total operating expenses (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_opex")}')
    S('o_lit', '  (−) Litigation provisions', 'line', 'm', all=lambda: f'=-{V("d_lit")}')
    S('o_restr', '  (−) Restructuring charges', 'line', 'm', all=lambda: f'=-{V("d_restr")}')
    S('o_oth', '  (−) Other operating special items', 'line', 'm', all=lambda: f'=-{V("d_oadj")}')
    S('o_adjox', '  = Adjusted operating expenses (model bridge)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_opex")}),{V("o_opex")}+{V("o_lit")}+{V("o_restr")}+{V("o_oth")},"")')
    S('o_pub', '  Company-published adjusted operating expenses', 'memo', 'm', data='adj_opex_pub', flow=True)
    S('o_chk', '  Check: model vs company-published (should be 0; ±1 rounding)', 'check', 'm', hist=QCHK('o_adjox', 'o_pub', 1.1, 0))
    S('o_arev', 'Adjusted net revenue (net revenue + revenue special items)', 'line', 'm', all=lambda: f'={V("g_arev")}')
    S('o_arev_pub', '  Company-published adjusted net revenue (where it differs from GAAP: 2022)', 'memo', 'm', data='adj_rev_pub', flow=True)
    S('o_aoi', '  = Adjusted operating income', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("o_adjox")}),{V("o_arev")}-{V("o_adjox")},"")')
    S('o_aom', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_aoi', 'o_arev'))
    S('o_aom_pub', '  Company-published adjusted operating margin %', 'memo', 'pct', data='adj_om_pub')
    S('o_aom_chk', '  Check: adjusted operating margin vs published (should be 0; ±0.1 pt rounding)', 'check', 'pct',
      hist=lambda: f'=IF(AND(ISNUMBER({V("o_aom")}),ISNUMBER({V("o_aom_pub")})),IF(ABS({V("o_aom")}-{V("o_aom_pub")})<=0.00151,0,ROUND({V("o_aom")}-{V("o_aom_pub")},4)),"n/p")')
    S('o_def', '  Definition / basis (company non-GAAP definition in force)', 'text', 'gen',
      note='Definition changes are flagged in the column where they take effect (cell comment gives the company wording).')
    S('o_aoi_g', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_aoi'))
    blank()

    # ------------------------------------------------------------------ RECON 2: NI -> EBITDA -> adjusted EBITDA (model)
    S('sec_r2', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (MODEL DEFINITION — Mastercard publishes no EBITDA)', 'section',
      note='EBITDA (model) — net income + tax − total other income (expense) = operating income; + D&A = EBITDA; + operating special items = adjusted EBITDA (= adjusted operating income + D&A)')
    S('r_ni', 'Net income (incl. non-controlling interests)', 'line_b', 'm', all=lambda: f'={V("is_nit")}')
    S('r_tax', '  (+) Income tax expense', 'line', 'm', all=lambda: f'={V("is_tax")}')
    S('r_ot', '  (−) Total other income (expense)', 'line', 'm', all=lambda: f'=-{V("is_ot")}')
    S('r_oi', '  = Operating income (GAAP)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_tax")}+{V("r_ot")},"")')
    S('r_da', '  (+) Depreciation and amortization', 'line', 'm', all=lambda: f'={V("is_da")}')
    S('r_ebitda', '  = EBITDA (model)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("r_oi")}),{V("r_oi")}+{V("r_da")},"")')
    S('r_sp', '  (+) Operating special items (litigation, restructuring, other; + revenue special items)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("d_lit")}),{V("d_lit")}+{V("d_restr")}+{V("d_oadj")}+N({V("d_rev")}),"")')
    S('r_adj', '  = Adjusted EBITDA (model)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{V("r_ebitda")}+{V("r_sp")},"")',
      note='Model definition (Mastercard publishes no EBITDA): adjusted operating income + D&A. Used for leverage (net debt / adjusted EBITDA) and EV / EBITDA.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_chk', '  Check: adjusted EBITDA − D&A vs adjusted operating income (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_adj")}),ISNUMBER({V("o_aoi")})),IF(ABS({V("r_adj")}-{V("r_da")}-{V("o_aoi")})<=1.1,0,ROUND({V("r_adj")}-{V("r_da")}-{V("o_aoi")},0)),"")')
    S('r_ebit_h', 'To adjusted EBIT, full-cost (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ebit', '  = Adjusted EBIT (= adjusted operating income; amortization and share-based compensation are not adjusted out)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}-{V("r_da")},"")')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: litigation provisions & restructuring (cash costs adjusted out; deducted in the DCF)', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("d_lit")}),{V("d_lit")}+{V("d_restr")},"")')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: NET INCOME / DILUTED EPS → ADJUSTED NET INCOME → ADJUSTED DILUTED EPS (company definition)', 'section',
      note='ADJUSTED EPS — net income + pre-tax special items + equity-investment (gains) losses − tax effect (+ discrete tax items); adjusted = GAAP where nothing was published')
    S('e_ni', 'Net income attributable to Mastercard (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('e_op', '  (+) Operating special items (pre-tax, incl. revenue items)', 'line', 'm', all=lambda: f'={V("r_sp")}')
    S('e_nop', '  (+) Equity-investment (gains) losses & other non-operating special items (pre-tax)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("d_eqgl")}),{V("d_eqgl")}+N({V("d_ngain")}),"")')
    S('e_tax', '  (−) Tax effect of the items & discrete tax items', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("e_pubni")}),{V("e_pubni")}-{V("e_ni")}-{V("e_op")}-{V("e_nop")},IF(ISNUMBER({V("e_ni")}),0,""))',
      fc=lambda: f'={V("is_tax")}-{V("e_adjtax")}',
      note='Historical: published adjusted net income − net income − pre-tax items (incl. discrete tax items: U.S. tax reform 2017–18, other; see the discrete-tax row). Forecast: GAAP tax − adjusted tax.')
    S('e_adjni', '  = Adjusted net income (model bridge)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("e_tax")}),{V("e_ni")}+{V("e_op")}+{V("e_nop")}+{V("e_tax")},"")')
    S('e_pubni', '  Company-published adjusted net income', 'memo', 'm', data='adj_ni_pub', flow=True)
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted EPS – diluted ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted diluted EPS ($, split-adjusted)', 'eps_memo', 'ps', data='e_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.02 rounding; 2008–09 two-class)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0201,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_adjebt', '  Adjusted income before tax (adjusted operating income + adjusted other income (expense))', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_aoi")}),{V("o_aoi")}+{V("is_ot")}+{V("e_nop")},"")')
    S('e_adjtax', '  Adjusted income tax (adjusted income before tax − adjusted net income − NCI)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_adjni")}),ISNUMBER({V("e_adjebt")})),{V("e_adjebt")}-{V("e_adjni")}-N({V("is_nci")}),"")',
      fc=lambda: f'={V("e_adjebt")}*{V("e_rate")}')
    S('e_rate', '  Adjusted effective tax rate', 'pct', 'pct', all=ratio('e_adjtax', 'e_adjebt'), qe=lambda: f'={PT("pt_etr")}', ae=lambda: f'={V("is_etr")}',
      note='H1-26 adjusted 19.7%; Q3/Q4 guided 20–21% (UNVERIFIED). Forecast = GAAP effective tax rate (special items taxed at the same rate).')
    S('e_def', '  Definition / basis (company adjusted EPS definition)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Net revenue y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_pn', '  Payment network y/y %', 'growth', 'pct', all=growth('pn'))
    S('gm_vas', '  Value-added services and solutions y/y %', 'growth', 'pct', all=growth('vas'))
    S('gm_gdv', '  GDV y/y % (USD)', 'growth', 'pct', all=growth('k_gdv'))
    S('gc_pn', '  Contribution to net revenue growth — payment network (pp; before 2021: total net revenue growth)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(IF(ISNUMBER({P("pn")}),({V("pn")}-{P("pn")})/{P("g_rev")},{V("g_rev")}/{P("g_rev")}-1),"")' if CTX.col.prior else None))
    S('gc_vas', '  Contribution to net revenue growth — value-added services & other (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(IF(ISNUMBER({P("pn")}),({V("g_rev")}-{P("g_rev")}-({V("pn")}-{P("pn")}))/{P("g_rev")},0),"")' if CTX.col.prior else None))
    S('gm_aoi', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_aoi'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_oi', '  Operating income (GAAP) y/y %', 'growth', 'pct', all=growth('is_oi'))
    S('gm_ni', '  Net income y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_aom', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_aoi', 'o_arev'))
    S('gm_inc', '  Incremental adjusted operating margin (Δ adj. OI / Δ net revenue)', 'pct', 'pct', all=incr('o_aoi', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_ga', '  G&A % of net revenue', 'pct', 'pct', all=ratio('is_ga', 'is_rev'))
    S('gm_am', '  Advertising & marketing % of net revenue', 'pct', 'pct', all=ratio('is_am', 'is_rev'))
    S('gm_aox', '  Adjusted operating expenses % of net revenue', 'pct', 'pct', all=ratio('o_adjox', 'is_rev'))
    blank()
