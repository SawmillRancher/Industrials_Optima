"""Row specification of the GOOG Model sheet, part 1 (MLM template layout and process):
revenue build by type (Google Search & other, YouTube ads, Google Network, Google subscriptions / platforms / devices, Google Cloud,
Other Bets, hedging) -> segment operating income (Google Services, Google Cloud, Other Bets, Alphabet-level activities) ->
M&A lever and pending GFiber divestiture -> group total & Q3-Q4/26E outlook (no company guidance) -> cost drivers -> income
statement -> GAAP-to-adjusted bridges (model definitions) -> growth & margins."""
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
def ACT(key): return f'SUM({Q1}{R[key]}:{Q2}{R[key]})'      # 1H26 actual (Q1-Q2/26)
def ACT0(key): return f'SUM({PQ1}{R[key]}:{PQ2}{R[key]})'   # 1H25 actual (Q1-Q2/25)
def H2(key): return f'SUM({Q3E}{R[key]}:{Q4E}{R[key]})'      # 2H26 estimate
def B1(key): return f'{LQ}{R[key]}'                         # 30-Jun-2026 balance

STREAMS = [('search', 'Google Search & other', 'st_search', 'SEARCH'), ('youtube', 'YouTube ads', 'st_youtube', 'YOUTUBE'),
           ('network', 'Google Network', 'st_network', 'NETWORK'), ('subs', 'Google subscriptions, platforms & devices', 'st_subs', 'SUBS')]
LINES = ['rv_' + k for k, *_ in STREAMS] + ['rv_cloud', 'rv_ob']

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Alphabet gives no revenue / margin / EPS guidance: the Q3–Q4/26E block holds scenario shifts vs the 1H26 run-rate.'))
    r = 11
    SCEN_ROWS.append((r, 'out_hdr', V0['out_hdr'], 'Bull', 'Base', 'Bear', V0['out_note'])); r += 1
    for key, lab, (hi, mid, lo), nf, note in V0['outlook']:
        SC[key] = r; SCEN_ROWS.append((r, 'out', lab, hi, mid, lo, note, nf)); r += 1
    r += 1
    SCEN_ROWS.append((r, 'pt_hdr', 'Q3–Q4/26E point estimates (all cases)', None, None, None, None)); r += 1
    for key, lab, vals, nf, note in V0['points']:
        SC[key] = r
        SCEN_ROWS.append((r, 'pt', lab, None, vals, None, note, nf)); r += 1
    r += 1
    SC['LEV'] = r
    SCEN_ROWS.append((r, 'lev', '  Target net debt / adjusted EBITDA (x; negative = net-cash floor) — buyback plug 2027E+', *V0['lev'], V0['lev_note']))
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
    S('sec_rev', 'REVENUE BUILD — GOOGLE SERVICES (Search · YouTube · Network · Subscriptions/platforms/devices) · GOOGLE CLOUD · OTHER BETS', 'section',
      note='REVENUE BUILD — modelling logic (revenue by type → segment revenue → segment operating income → Alphabet-level costs → GAAP P&L)')
    blank()
    S('rv_hdr', 'Revenues by type (current taxonomy; latest filing presenting the period — annual from FY2017, quarterly from Q1/19)', 'block',
      note='REVENUE TYPES — Q3–Q4/26E: prior-year quarter × (1 + 1H26 y/y growth + scenario shift); 2027E–2030E: scenario levers')
    for k, lab, dk, code in STREAMS + [('cloud', 'Google Cloud', 'st_cloud', 'CLOUD'), ('ob', 'Other Bets', 'ob_rev', 'OB')]:
        key = 'rv_' + k
        S(key, f'  {lab}', 'line', 'm', data=dk, flow=True,
          qe=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})', ae=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})',
          note=V0['rv_notes'].get(k))
        S(key + '_g', '    y/y %', 'growth', 'pct', all=growth(key),
          qe=lambda key=key: f'={V(key + "_pre", Q3E)}+{V("cal_g", Q3E)}',
          ae=lambda code=code: '=' + CH(SC[code][CTX.col.year]),
          note=('Q3–Q4/26E: 1H26 y/y growth + scenario shift (Group block). 2027E–2030E: scenario lever (Bull/Base/Bear table →).') if k == 'search' else None)
        S(key + '_pre', '    1H26 y/y growth (Q3–Q4/26E driver before scenario shift)', 'driver', 'pct',
          qe=lambda key=key: f'=IFERROR({ACT(key)}/{ACT0(key)}-1,0)')
    S('rv_hedge', '  Hedging gains (losses) (not allocated to segments; derived = revenues − segment revenues)', 'line', 'm', data='st_hedge', flow=True,
      fc=lambda: '=0', note='Cash-flow hedging gains / losses recorded in revenues (Alphabet-level). Forecast nil.')
    S('rv_ns', '  Revenues not split on the current taxonomy / basis differences (derived)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}-({nsum(LINES + ["rv_hedge"])}),"")', fc=lambda: '=0',
      note='Consolidated revenues (as originally reported) − Σ revenue types (latest filing presenting the period). Equals total revenues before FY2017 / Q1-19 (legacy split in the memo block below); Other Bets before FY2015.')
    S('rv_tot', 'Total revenues (revenue build)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{nsum(LINES + ["rv_hedge", "rv_ns"])},"")' if CTX.col.kind in HISTK else '=' + nsum(LINES + ['rv_hedge']))
    S('rv_tot_g', '  Total revenues y/y %', 'growth', 'pct', all=growth('rv_tot'))
    S('rv_svc', '  Google Services revenues (Σ Search, YouTube, Network, subscriptions/platforms/devices)', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("rv_search")}),{V("rv_search")}+{V("rv_youtube")}+{V("rv_network")}+{V("rv_subs")},"")')
    S('rv_svc_g', '    Google Services y/y %', 'growth', 'pct', all=growth('rv_svc'))
    S('rv_svc_pub', '  Memo: Google Services segment revenues as reported (segment note)', 'memo', 'm', data='sr_svc', flow=True)
    S('rv_svc_chk', '  Check: revenue types vs Google Services segment revenues (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("rv_svc")}),ISNUMBER({V("rv_svc_pub")})),IF(ABS({V("rv_svc")}-{V("rv_svc_pub")})<=1,0,ROUND({V("rv_svc")}-{V("rv_svc_pub")},0)),"")')
    S('rv_adv', '  Google advertising (Search + YouTube + Network)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("rv_search")}),{V("rv_search")}+{V("rv_youtube")}+{V("rv_network")},"")')
    S('rv_cloud_mix', '  Google Cloud % of total revenues', 'pct', 'pct', all=ratio('rv_cloud', 'is_rev'))
    S('gc_svc', '  Contribution to revenue growth — Google Services (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("rv_svc")}-{P("rv_svc")})/{P("is_rev")},"")' if CTX.col.prior else None))
    S('gc_cloud', '  Contribution to revenue growth — Google Cloud (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("rv_cloud")}-{P("rv_cloud")})/{P("is_rev")},"")' if CTX.col.prior else None))
    S('kpi_h', '  Operating KPIs:', 'sub', 'gen')
    S('kpi_tac', '  Traffic acquisition costs (TAC; release)', 'memo', 'm', data='tac', flow=True,
      note='Total TAC from the earnings releases (annual = Σ quarters). TAC is inside cost of revenues and Google Services costs.')
    S('kpi_tac_p', '  TAC % of Google advertising revenues', 'pct', 'pct', hist=lambda: f'=IF(AND(ISNUMBER({V("kpi_tac")}),ISNUMBER({V("rv_adv")})),IFERROR({V("kpi_tac")}/{V("rv_adv")},""),"")')
    S('kpi_rpo', '  Revenue backlog — remaining performance obligations (period end; Google Cloud ~99%)', 'memo', 'm', data='rpo', bs=True,
      note='10-Q / 10-K revenue note (XBRL RevenueRemainingPerformanceObligation); Google Cloud $513.9bn of $519.5bn at 30-Jun-2026, about half recognised within 24 months.')
    S('kpi_emp', '  Employees (period end; release)', 'memo', 'gen', data='employees', bs=True)
    S('leg_h', '  Legacy revenue split, as first reported (Google websites / properties incl. YouTube; Network members; other incl. Cloud, Play, hardware; Motorola Mobile 2012–13):', 'sub', 'gen')
    for k, lab in (('web', 'Google websites / properties'), ('net', "Google Network Members' websites / properties"), ('oth', 'Other revenues (licensing, Cloud, Play, hardware)'),
                   ('moto', 'Motorola Mobile (hardware and other)'), ('ob', 'Other Bets revenues')):
        S(f'lg_{k}', f'    {lab}', 'memo', 'm', data=f'leg_{k}', flow=True)
    S('lg_ns', '    Not split / basis differences (derived; FY2013 Motorola after the Home disposal, Other Bets in 2015 quarters)', 'memo_calc', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("lg_web")}),{V("is_rev")}-({nsum(["lg_web", "lg_net", "lg_oth", "lg_moto", "lg_ob"])}),"")')
    blank()

    # ------------------------------------------------------------------ SEGMENT OPERATING INCOME
    S('so_hdr', 'Segment operating income (company measure; latest filing presenting the period — annual from FY2018, quarterly from Q1/20)', 'block',
      note='SEGMENTS — Q3–Q4/26E margins: last actual quarter + sequential seasonality (Services) / held (Cloud) + scenario shift; 2027E+: scenario levers')
    S('so_svc', '  Google Services operating income', 'line', 'm', data='so_svc', flow=True,
      qe=lambda: f'={V("rv_svc")}*{V("so_svc_m")}', ae=lambda: f'={V("rv_svc")}*{V("so_svc_m")}')
    S('so_svc_m', '    Google Services operating margin %', 'pct', 'pct', all=ratio('so_svc', 'rv_svc'),
      qe=lambda: f'={V("so_svc_mpre")}+{V("cal_m", Q3E)}', ae=lambda: '=' + CH(SC['SVC_M'][CTX.col.year]))
    S('so_svc_mpre', '    Q3–Q4/26E margin before scenario shift (prior quarter + last year\'s sequential change)', 'driver', 'pct',
      qe=lambda: (f'={Q2}{R["so_svc_m"]}+({CTX.col.prior}{R["so_svc_m"]}-{QC[(FYC - 1, 2)].c}{R["so_svc_m"]})' if CTX.col.c == Q3E
                  else f'={Q3E}{R["so_svc_mpre"]}+({CTX.col.prior}{R["so_svc_m"]}-{QC[(FYC - 1, 3)].c}{R["so_svc_m"]})'),
      note='Q3E = Q2-26 margin + (Q3-25 − Q2-25); Q4E = Q3E + (Q4-25 − Q3-25): sequential seasonality of the prior year (ODFL approach).')
    S('so_cloud', '  Google Cloud operating income', 'line', 'm', data='so_cloud', flow=True,
      qe=lambda: f'={V("rv_cloud")}*{V("so_cloud_m")}', ae=lambda: f'={V("rv_cloud")}*{V("so_cloud_m")}')
    S('so_cloud_m', '    Google Cloud operating margin %', 'pct', 'pct', all=ratio('so_cloud', 'rv_cloud'),
      qe=lambda: f'={Q2}{R["so_cloud_m"]}+{V("cal_m", Q3E)}', ae=lambda: '=' + CH(SC['CLOUD_M'][CTX.col.year]),
      note='Q3–Q4/26E: Q2-26 margin held (Cloud margins have risen with scale, not seasonally; management flagged leased third-party data-centre capacity in Q3 — call, unverified) + scenario shift.')
    S('so_cloud_inc', '    Incremental Google Cloud margin (Δ operating income / Δ revenues)', 'pct', 'pct', all=incr('so_cloud', 'rv_cloud'))
    S('so_ob', '  Other Bets operating income (loss)', 'line', 'm', data='so_ob', flow=True,
      qe=lambda: f'={PQ("so_ob")}', ae=lambda: '=' + CH(SC['OB_OI'][CTX.col.year]),
      note='Q3–Q4/26E: Q2-26 loss held. 2027E+: scenario lever ($m; Waymo scale-up; GFiber deconsolidated at closing).')
    S('so_alpha', '  Alphabet-level activities (shared AI research & frontier models, corporate costs, fines & settlements, hedging)', 'line', 'm', data='so_alpha', flow=True,
      qe=lambda: f'={PQ("so_alpha")}*(1+{V("so_alpha_g", Q3E)})', ae=lambda: f'=-{V("is_rev")}*{V("so_alpha_p")}',
      note='Includes Google DeepMind / general AI model development (from 2023), EC fines and legal settlements, severance and office-space charges, and hedging gains. '
           'Q3–Q4/26E: prior quarter × (1 + Q2/Q1-26 sequential growth); 2027E+: % of revenues (scenario lever).')
    S('so_alpha_g', '    Q3–Q4/26E sequential growth of Alphabet-level costs (Q2/Q1-26)', 'driver', 'pct', qe=lambda: f'=IFERROR({Q2}{R["so_alpha"]}/{Q1}{R["so_alpha"]}-1,0)')
    S('so_alpha_p', '    Alphabet-level costs % of revenues', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("so_alpha")}),IFERROR(-{V("so_alpha")}/{V("is_rev")},""),"")',
      ae=lambda: '=' + CH(SC['ALPHA_P'][CTX.col.year]))
    S('so_basis', '  Segment recast / basis difference (consolidated OI as originally reported − Σ segments as recast)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("so_svc")}),{V("is_oi")}-({nsum(["so_svc", "so_cloud", "so_ob", "so_alpha"])}),"")', fc=lambda: '=0',
      note='2018: performance fees reclassified from operating expenses to OI&E in 2019 and segments recast ($1,203m); otherwise 0.')
    S('so_tot', 'Operating income (segment build)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("so_svc")}),{nsum(["so_svc", "so_cloud", "so_ob", "so_alpha", "so_basis"])},"")')
    S('so_chk', '  Check: segment build vs consolidated operating income (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("so_tot")}),ISNUMBER({V("is_oi")})),IF(ABS({V("so_tot")}-{V("is_oi")})<=1,0,ROUND({V("so_tot")}-{V("is_oi")},0)),"")')
    S('lso_h', '  Legacy segment structures, as reported (memo):', 'sub', 'gen')
    S('lso_google', '    Google segment operating income (2015–2020 basis; incl. Cloud)', 'memo', 'm', data='lso_google', flow=True)
    S('lso_ob', '    Other Bets operating loss (2015–2020 basis)', 'memo', 'm', data='lso_ob', flow=True)
    S('lso_alpha', '    Unallocated / Alphabet-level (2015–2020 basis)', 'memo', 'm', data='lso_alpha', flow=True)
    S('lso_moto', '    Motorola Mobile operating loss (2012–2013)', 'memo', 'm', data='lso_moto', flow=True)
    blank()

    # ------------------------------------------------------------------ M&A lever / GFiber
    S('m_hdr', 'Future acquisitions (M&A lever — unallocated; deals closed from 2027E)', 'block', note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=15.0, e26_in=0.0, note='Wiz $29.5bn (Mar-2026) at a reported ~$1bn ARR (press, unverified) ≈ 30x; Mandiant $5.4bn (2022). 15x input (assumption).')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_rev', '  Revenue from future acquisitions (mid-year; grows with the acquired base at 20%)', 'line_b', 'm', e26_in=0.0,
      ae=lambda: f'={P("m_rev")}*1.2+0.5*{V("m_acq_sales")}+0.5*{P("m_acq_sales")}')
    S('m_m', '  Operating margin of acquired businesses (after amortization) %', 'driver', 'pct', e26_in=0.0, ae_in=0.0)
    S('m_oi', '  Operating income from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_intp', '  Acquired intangibles % of spend (Wiz 28%)', 'driver', 'pct', e26_in=0.0, ae_in=0.28)
    S('m_life', '  Intangible amortization life (years; Wiz 7–10)', 'driver', 'gen', e26_in=0, ae_in=8)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)')
    blank()
    S('dv_hdr', 'Pending divestiture — GFiber (contribution to a new entity; agreement Mar-2026, close expected late 2026; held for sale)', 'block',
      note='DIVESTITURE — modelled at 31-Dec-2026: $1.5bn cash, $2.0bn note receivable and a 49.99% equity-method interest; no gain assumed')
    S('dv_cash', '  Cash proceeds', 'line', 'm', e26_in=V0['gf_cash'], ae_in=0.0, note=MAN['capital']['gfiber'])
    S('dv_hfs', '  Held-for-sale assets derecognised (property & equipment $7.1bn at 30-Jun-2026)', 'driver', 'm', e26_in=V0['gf_hfs'], ae_in=0.0)
    S('dv_noncash', '  Non-cash consideration recognised (note receivable $2.0bn + equity interest; assumption: carrying value, no gain)', 'line', 'm',
      e26=lambda: f'={V("dv_hfs")}-{V("dv_cash")}', ae_in=0.0,
      note='The equity interest is assumed to be recognised at the carrying value of the net assets contributed less cash and note (no gain or loss; not disclosed).')
    blank()

    # ------------------------------------------------------------------ group total & outlook
    S('g_hdr', 'Group total — revenues & operating income (build) · Q3–Q4/26E outlook (no company guidance)', 'block', note='GROUP TOTAL — modelling logic')
    S('g_rev', 'Total revenues (build)', 'total', 'm', all=lambda: f'={V("rv_tot")}' if CTX.col.kind in HISTK else f'={V("rv_tot")}+N({V("m_rev")})')
    S('g_rev_g', '  Revenues y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: revenue build vs consolidated revenues (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=1,0,ROUND({V("g_rev")}-{V("is_rev")},0)),"")')
    S('g_oi', 'Operating income (build)', 'total', 'm', all=lambda: f'={V("so_tot")}' if CTX.col.kind in HISTK else f'={V("so_tot")}+N({V("m_oi")})')
    S('g_oim', '  Operating margin %', 'pct', 'pct', all=ratio('g_oi', 'is_rev'))
    S('cal_g', '  Q3–Q4/26E revenue growth shift vs 1H26 y/y trend (scenario; applied to every revenue type)', 'driver', 'pct',
      qe=lambda: (f'=IF(ISNUMBER({PT("out_rev")}),({PT("out_rev")}-{ACT("rv_tot")}-{V("cal_pre", Q3E)})/{V("cal_sens", Q3E)},{CH(SC["out_dg"])})' if CTX.col.c == Q3E else f'={V("cal_g", Q3E)}'),
      note='No revenue guidance: Base = 1H26 y/y run-rate; Bull / Bear shift. If an FY26 revenue target is entered in the outlook block (optional, blank by default), the shift is solved to hit it.')
    S('cal_pre', '  2H26E revenues before the shift (helper)', 'line', 'm', qe=lambda: ('=' + '+'.join(f'({P(k)}+{QC[(FYC - 1, 4)].c}{R[k]})*(1+{V(k + "_pre")})' for k in LINES)) if CTX.col.c == Q3E else None)
    S('cal_sens', '  2H26E revenue sensitivity to +1.00 of growth (helper)', 'line', 'm', qe=lambda: ('=' + '+'.join(f'{P(k)}+{QC[(FYC - 1, 4)].c}{R[k]}' for k in LINES)) if CTX.col.c == Q3E else None)
    S('cal_tgt', '  Memo: FY26 revenue target (optional input; blank = driver-based)', 'memo', 'm', e26=lambda: f'=IF(ISNUMBER({PT("out_rev")}),{PT("out_rev")},"n/a")')
    S('cal_tgt_chk', '  Check: FY26 revenues vs target, when a target is entered (should be 0)', 'check', 'm',
      e26=lambda: f'=IF(ISNUMBER({PT("out_rev")}),ROUND({V("is_rev")}-{PT("out_rev")},0),"")')
    S('cal_m', '  Q3–Q4/26E segment-margin shift (scenario; Services and Cloud)', 'driver', 'pct', qe=lambda: '=' + CH(SC['out_dm']))
    S('cal_capex', '  Memo: FY26 capital expenditures guidance mid-point — UNVERIFIED (earnings call only; not in EDGAR filings)', 'memo', 'm',
      e26=lambda: f'={PT("pt_capex")}', note=MAN['guidance']['capex_2026']['status'])
    S('cal_capex_d', '    Model FY26 capex − guidance (information)', 'memo_calc', 'm', e26=lambda: f'=-{V("cf_capex")}-{V("cal_capex")}')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A, adjusting items & other income', 'block', note='COST DRIVERS — Q3–Q4/26E point estimates or 1H26 ratios; 2027E+ ratios / schedules')
    S('d_dep', '  Depreciation of property & equipment (cash-flow statement; incl. impairment on disposition where presented)', 'line', 'm', data='cf_dep', flow=True,
      qe=lambda: f'={PQ("d_dep")}*(1+{PT("pt_depg")})', ae=lambda: f'={P("bs_ppe")}*{V("d_dep_r")}',
      note='Q3–Q4/26E: prior quarter × (1 + sequential growth point estimate; Q2/Q1-26 +9.6%). 2027E+: opening net property & equipment × depreciation rate.')
    S('d_dep_r', '  Depreciation ÷ opening net property & equipment %', 'pct', 'pct', all=lambda: (f'=IFERROR({V("d_dep")}/{P("bs_ppe")},"")' if CTX.col.prior and CTX.col.q is None else None),
      ae_in=V0['dep_r'], note=V0['dep_note'])
    S('d_amort', '  Amortization of intangible assets (cash-flow statement to 2022; note from 2026)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("d_amort_cf")}),IF({V("d_amort_cf")}<>0,{V("d_amort_cf")},N({V("d_amort_nt")})),"")',
      qe=lambda: f'={PT("pt_amort")}', ae=lambda: f'={V("d_amort_sch")}+N({V("m_amort")})',
      note='2023–2025: not presented separately (inside other non-cash items); D&A = depreciation. 2026+: Wiz intangibles ($8.3bn; 7–10 years ≈ $1.0bn p.a.).')
    S('d_amort_cf', '    Memo: amortization (and impairment) of intangibles, cash-flow statement', 'memo', 'm', data='cf_amort', flow=True)
    S('d_amort_nt', '    Memo: amortization of intangible assets (note)', 'memo', 'm', data='amort_int', flow=True)
    S('d_amort_sch', '  Amortization schedule of intangibles held (input)', 'driver', 'm', ae_in=V0['amort_sched'], note=V0['amort_note'])
    S('d_dda', '  Depreciation & amortization (total)', 'line_b', 'm', flow=True, all=lambda: f'=IF(ISNUMBER({V("d_dep")}),{V("d_dep")}+N({V("d_amort")}),"")')
    S('d_sbc', '  Stock-based compensation (cash-flow statement)', 'line', 'm', data='cf_sbc', flow=True,
      qe=lambda: f'={P("d_sbc")}*(1+IFERROR({ACT("d_sbc")}/{ACT0("d_sbc")}-1,0))', ae=lambda: f'={V("is_rev")}*{V("d_sbc_p")}',
      note='Q3–Q4/26E: prior-year quarter × 1H26 y/y. 2027E+: % of revenues. Alphabet does not adjust out stock-based compensation (Google did in its non-GAAP measures to 2016).')
    S('d_sbc_p', '  Stock-based compensation % of revenues', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_p'])
    S('d_rd', '  R&D % of revenues', 'pct', 'pct', all=ratio('is_rd', 'is_rev'), qe=lambda: f'={P("d_rd")}+IFERROR({ACT("is_rd")}/{ACT("is_rev")}-{ACT0("is_rd")}/{ACT0("is_rev")},0)', ae_in=V0['rd_p'])
    S('d_sm', '  Sales & marketing % of revenues', 'pct', 'pct', all=ratio('is_sm', 'is_rev'), qe=lambda: f'={P("d_sm")}+IFERROR({ACT("is_sm")}/{ACT("is_rev")}-{ACT0("is_sm")}/{ACT0("is_rev")},0)', ae_in=V0['sm_p'])
    S('d_ga', '  General & administrative % of revenues', 'pct', 'pct', all=ratio('is_ga', 'is_rev'), qe=lambda: f'=IFERROR({ACT("is_ga")}/{ACT("is_rev")},0)', ae_in=V0['ga_p'],
      note='Cost of revenues is the balancing line: revenues − operating income (segment build) − R&D − S&M − G&A − other operating items.')
    S('d_adj_h', '  Adjusting items (pre-tax; quantified by the company in a published non-GAAP reconciliation):', 'sub', 'gen')
    S('d_fine', '  European Commission fines', 'line', 'm', data='i_fine', flow=True, labkey='i_fine_lab', fc=lambda: '=0',
      note='Q2-17 $2,736m, Q2-18 $5,071m, Q1-19 $1,697m (separate income-statement line), Q3-25 $3,457m (in G&A). Not tax-deductible. Forecast nil (not forecastable).')
    S('d_restr', '  Employee severance & office-space charges', 'line', 'm', data='i_restr', flow=True, labkey='i_restr_lab', fc=lambda: '=0',
      note='Q1-23 $2,558m and Q1-24 $716m (published reconciliation). Other 2023–25 charges were named in MD&A but not reconciled (left in; see manual_items.json).')
    S('d_eqg', '  Gains (losses) on equity securities, net (OI&E; ASU 2016-01 from 2018) / impairment of equity investments (2008)', 'line', 'm', flow=True,
      hist=lambda: f'=N({V("d_eqg_x")})+N({V("d_eqimp")})', fc=lambda: '=0',
      note='Model adjusting item: unrealised and realised gains on marketable and non-marketable equity securities (incl. stakes such as SpaceX / Anthropic, per press; not named in filings). Forecast nil.')
    S('d_eqg_x', '    Memo: gains (losses) on equity securities, net (XBRL)', 'memo', 'm', data='eq_gain', flow=True)
    S('d_eqimp', '    Memo: impairment of equity investments (2008)', 'memo', 'm', data='i_eqimp', flow=True)
    S('d_taxd', '  Discrete tax item: Tax Act (TCJA) charge, Q4-17', 'line', 'm', data='i_taxd', flow=True, labkey='i_taxd_lab', fc=lambda: '=0')
    S('d_int_h', '  Other income (expense), net — drivers:', 'sub', 'gen')
    S('d_intinc', '  Interest income (XBRL)', 'line', 'm', data='int_inc', flow=True, qe=lambda: f'=({B1("bs_cash")}+{B1("bs_msec")})*{PT("pt_yield")}/4',
      ae=lambda: f'=({P("bs_cash")}+{P("bs_msec")})*{V("ds_r_cash")}')
    S('d_intexp', '  Interest expense (XBRL)', 'line', 'm', data='int_exp', flow=True, qe=lambda: f'={PT("pt_intexp")}',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_cp")}*{V("ds_r_cp")}')
    S('d_oie_o', '  Other OI&E (FX, derivatives, performance fees, equity-method results, debt securities; derived)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("is_oie")}),{V("is_oie")}-N({V("d_intinc")})+N({V("d_intexp")})-N({V("d_eqg")}),"")', fc=lambda: '=0',
      note='Derived residual. Forecast nil (assumption).')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENTS OF INCOME (US GAAP, as originally reported)', 'section',
      note='CONSOLIDATED IS — forecast logic (operating income from the segment build; cost of revenues implied)')
    S('is_rev', 'Revenues', 'total', 'm', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the revenue build.')
    S('is_cor', 'Cost of revenues', 'line', 'm', data='cor', flow=True,
      fc=lambda: f'={V("is_rev")}-{V("is_oi")}-{V("is_rd")}-{V("is_sm")}-{V("is_ga")}-{V("is_oth")}',
      note='Includes TAC, content acquisition and other costs (data-centre operations, depreciation). 2012–13: Google + Motorola cost of revenues (derived = total costs − opex). Forecast = balancing line.')
    S('is_gm', '  Gross margin %', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("is_cor")}),IFERROR(1-{V("is_cor")}/{V("is_rev")},""),"")')
    S('is_rd', 'Research & development', 'line', 'm', data='rd', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_rd")}')
    S('is_sm', 'Sales & marketing', 'line', 'm', data='sm', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_sm")}')
    S('is_ga', 'General & administrative', 'line', 'm', data='ga', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_ga")}')
    S('is_oth', 'Other operating items shown separately (European Commission fines 2017–19; DOJ charge 2011)', 'line', 'm', data='oth_op', flow=True, fc=lambda: '=0')
    S('is_opex', 'Total costs & expenses', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_cor")}),{V("is_cor")}+{V("is_rd")}+{V("is_sm")}+{V("is_ga")}+{V("is_oth")},"")')
    S('is_oi', 'Income from operations', 'total', 'm', hist=lambda: f'=IF(ISNUMBER({V("is_opex")}),{V("is_rev")}-{V("is_opex")},"")', fc=lambda: f'={V("g_oi")}')
    S('is_oi_pub', '  Memo: income from operations as reported', 'memo', 'm', data='oi', flow=True)
    S('is_oi_chk', '  Check: model vs reported operating income (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_oi_pub")}),IF(ABS({V("is_oi")}-{V("is_oi_pub")})<=1,0,ROUND({V("is_oi")}-{V("is_oi_pub")},0)),"")')
    S('is_oim', '  Operating margin %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('is_oie', 'Other income (expense), net', 'line', 'm', data='oie', flow=True, fc=lambda: f'={V("d_intinc")}-{V("d_intexp")}+{V("d_eqg")}+{V("d_oie_o")}',
      note='Interest income − interest expense + gains (losses) on equity securities + other. Forecast: interest only (equity gains not forecast).')
    S('is_ebt', 'Income before income taxes', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_oi")}),{V("is_oi")}+{V("is_oie")},"")')
    S('is_tax', 'Provision for income taxes', 'line', 'm', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'])
    S('is_disc', 'Net income (loss) from discontinued operations (Motorola Home 2012–13, Motorola Mobile 2014)', 'line', 'm', data='disc', flow=True, fc=lambda: '=0')
    S('is_ni', 'Net income', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")}+N({V("is_disc")}),"")')
    S('is_ni_pub', '  Memo: net income as reported', 'memo', 'm', data='ni', flow=True)
    S('is_ni_chk', '  Check: net income vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=1,0,ROUND({V("is_ni")}-{V("is_ni_pub")},0)),"")')
    S('is_pref', '  Preferred stock dividends (6.25% mandatory convertible preferred, from Jun-2026)', 'line', 'm', data='pref_div', flow=True,
      qe=lambda: f'={PT("pt_prefq")}', ae=lambda: f'={V("mc_div")}', note=MAN['capital']['mcps'])
    S('is_calloc', '  Class C adjustment payment (Q2-2015; allocated to Class C holders)', 'line', 'm', data='c_alloc', flow=True, fc=lambda: '=0')
    S('is_nic', '  Net income available to common stockholders (Class A / B / C)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ni")}),{V("is_ni")}-N({V("is_pref")})-N({V("is_calloc")}),"")')
    S('is_dda', '  Memo: depreciation & amortization (total)', 'memo_calc', 'm', all=lambda: f'={V("d_dda")}')
    S('is_sbc', '  Memo: stock-based compensation', 'memo_calc', 'm', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share — Class A, B and C; split-adjusted: 2-for-1 Class C dividend Apr-2014, 20-for-1 Jul-2022)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m; Class A + B + C)', 'line', 'm', data='sh_b', avg=True,
      qe=lambda: f'={B1("bs_shares")}+({V("bb_iss", E26)}-{V("bb_sh", E26)})*{0.25 if CTX.col.c == Q3E else 0.75}',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q3–Q4/26E: shares outstanding at 30-Jun-2026 + 2H26 net issuance (¼ in Q3, ¾ in Q4). 2027E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m; RSUs + if-converted preferred)', 'line', 'm', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q2}{R["sh_dil"]}-{Q2}{R["sh_basic"]}-16)+{V("mc_sh", E26)}', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}+{V("mc_shd")}',
      note='Q3–Q4/26E: basic + Q2-26 RSU dilution (diluted − basic − 16m preferred) + preferred if-converted at the forecast price. 2027E+: + RSU dilution + preferred (to May-2029).')
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR(({V("is_nic")}+N({V("mc_flag")})*N({V("is_pref")}))/{V("sh_dil")},""),"")',
      note='Net income available to common (+ preferred dividends when the preferred is if-converted) ÷ diluted shares. 2015: Class A EPS (Class C EPS includes the adjustment payment).')
    S('mc_flag', '  Preferred if-converted in diluted EPS (1 = yes; forecast to the May-2029 conversion)', 'driver', 'gen',
      qe_in=1, e26_in=1, ae_in={y: (1 if y <= 2029 else 0) for y in range(FYC + 1, FYL + 1)})
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($, split-adjusted; Q4 from the release)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01 rounding, ±0.015 split-adjusted)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0151,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('dps', '  Cash dividends declared per share ($; initiated Q2-2024)', 'line', 'ps', data='dps', flow=True, qe_in=V0['dps_q'],
      ae=lambda: f'={P("dps")}*(1+{V("dps_g")})', note='$0.20 quarterly from Q2-24, $0.21 from Q2-25, $0.22 from Q2-26. 2027E+: prior year × (1 + growth).')
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'])
    blank()

    # ------------------------------------------------------------------ RECON 1: OI -> adjusted OI
    S('sec_r1', 'RECONCILIATION: INCOME FROM OPERATIONS → ADJUSTED OPERATING INCOME (model definition; company-published where available)', 'section',
      note='ADJUSTED OI — model definition: GAAP operating income + items the company itself excluded in a published non-GAAP reconciliation (EC fines; severance & office-space charges)')
    S('o_op', 'Income from operations (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_oi")}')
    S('o_fine', '  (+) European Commission fines', 'line', 'm', all=lambda: f'={V("d_fine")}')
    S('o_restr', '  (+) Employee severance & office-space charges', 'line', 'm', all=lambda: f'={V("d_restr")}')
    S('o_tot', '  Total adjusting items (pre-tax)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("o_fine")}),N({V("o_fine")})+N({V("o_restr")}),"")')
    S('o_adj', '  = Adjusted operating income (model)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+N({V("o_tot")}),"")')
    S('o_adj_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company-published operating income excluding the items (non-GAAP; Q2-17, Q2-18, Q1-19, Q1-23, Q1-24, Q3-25)', 'memo', 'm', data='ca_oi', flow=True)
    S('o_chk', '  Check: model vs company-published (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),IF(ABS({V("o_adj")}-{V("o_pub")})<=1,0,ROUND({V("o_adj")}-{V("o_pub")},0)),"n/p")')
    S('o_def', '  Definition / basis (company non-GAAP in force)', 'text', 'gen', note='Definition changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('o_adj_g', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental adjusted operating margin (Δ adjusted OI / Δ revenues)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: NI -> EBITDA -> adjusted EBITDA
    S('sec_r2', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (model definitions; Alphabet publishes no EBITDA)', 'section',
      note='EBITDA — model: net income − discontinued operations + taxes − other income (expense), net = operating income; + D&A = EBITDA; + adjusting items = adjusted EBITDA')
    S('r_ni', 'Net income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('r_disc', '  (−) Net income from discontinued operations', 'line', 'm', all=lambda: f'=-N({V("is_disc")})')
    S('r_tax', '  (+) Provision for income taxes', 'line', 'm', all=lambda: f'={V("is_tax")}')
    S('r_oie', '  (−) Other income (expense), net (incl. equity-security gains)', 'line', 'm', all=lambda: f'=-{V("is_oie")}')
    S('r_gebit', '  = Income from operations (EBIT, model definition)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_disc")}+{V("r_tax")}+{V("r_oie")},"")')
    S('r_gebit_chk', '  Check: vs income from operations (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_gebit")}),IF(ABS({V("r_gebit")}-{V("is_oi")})<=1,0,ROUND({V("r_gebit")}-{V("is_oi")},0)),"")')
    S('r_dda', '  (+) Depreciation & amortization', 'line', 'm', all=lambda: f'={V("d_dda")}')
    S('r_ebitda', '  = EBITDA (model)', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_gebit")}),ISNUMBER({V("r_dda")})),{V("r_gebit")}+{V("r_dda")},"")')
    S('r_adjx', '  (+) Adjusting items (EC fines; severance & office-space charges)', 'line', 'm', all=lambda: f'={V("o_tot")}')
    S('r_adj', '  = Adjusted EBITDA (model)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{V("r_ebitda")}+N({V("r_adjx")}),"")',
      note='Model definition (Alphabet publishes no EBITDA): stock-based compensation is NOT added back. Used for leverage (net debt / adjusted EBITDA) and EV / EBITDA.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_ebit_h', 'To adjusted EBIT (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ddan', '  (−) Depreciation & amortization', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("d_dda")}),-{V("d_dda")},"")')
    S('r_ebit', '  = Adjusted EBIT (= adjusted operating income; full-cost, after stock-based compensation and amortization)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+{V("r_ddan")},"")')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: cash adjusting items (fines, severance & office space; adjusted out, deducted in the DCF)', 'memo_calc', 'm', all=lambda: f'=IF(ISNUMBER({V("o_tot")}),{V("o_tot")},"")')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: NET INCOME → ADJUSTED NET INCOME → ADJUSTED EPS (model definition; company non-GAAP as memo)', 'section',
      note='ADJUSTED EPS — model: net income − discontinued operations + adjusting items − equity-security gains (losses) − model tax effect + discrete tax items')
    S('e_ni', 'Net income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('e_disc', '  (−) Discontinued operations', 'line', 'm', all=lambda: f'=-N({V("is_disc")})')
    S('e_op', '  (+) Operating adjusting items (EC fines; severance & office space)', 'line', 'm', all=lambda: f'={V("o_tot")}')
    S('e_eqg', '  (−) Gains (losses) on equity securities, net / (+) equity-investment impairment', 'line', 'm', all=lambda: f'=-N({V("d_eqg")})')
    S('e_tax', '  (−) Tax effect of the adjustments (model: statutory rate; EC fines not deductible)', 'line', 'm',
      all=lambda: f'=-({V("e_eqg")}+N({V("o_restr")}))*{V("e_trate")}')
    S('e_trate', '    Statutory rate applied (35% to 2017; 21% from 2018)', 'driver', 'pct', all=lambda: '=0.35' if CTX.col.year <= 2017 else '=0.21')
    S('e_taxd', '  (+) Discrete tax items (Tax Act charge Q4-17)', 'line', 'm', all=lambda: f'={V("d_taxd")}')
    S('e_adjni', '  = Adjusted net income (model)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("e_ni")}),{V("e_ni")}+{V("e_disc")}+N({V("e_op")})+{V("e_eqg")}+{V("e_tax")}+N({V("e_taxd")}),"")')
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted EPS – diluted ($) (model)', 'eps_total', 'ps',
      all=lambda: f'=IF(ISNUMBER({V("e_sh")}),IFERROR(({V("e_adjni")}-N({V("is_calloc")})-(1-N({V("mc_flag")}))*N({V("is_pref")}))/{V("e_sh")},""),"")')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_def', '  Definition / basis (company non-GAAP EPS in force)', 'text', 'gen')
    S('e_c_h', '  Company-published non-GAAP net income / EPS (definition in force; memo with checks):', 'sub', 'gen')
    S('e_c_items', '    Company items, pre-tax (stock-based compensation to Q4-16; EC fines; Tax Act)', 'memo', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("e_c_ni")}),N({V("ng_sbc")})+IF(ISNUMBER({V("ng_sbc")}),0,N({V("d_fine")})+N({V("d_taxd")})),"")')
    S('ng_sbc', '      Memo: stock-based compensation excluded by Google (release, continuing operations)', 'memo', 'm', data='ng_sbc', flow=True)
    S('e_c_tax', '    Tax effect of the company items (derived: published − net income + discontinued operations − items)', 'memo_calc', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("e_c_ni")}),{V("e_c_ni")}-{V("e_ni")}-{V("e_disc")}-{V("e_c_items")},"")')
    S('e_c_ni', '    Company-published non-GAAP net income', 'memo', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("ng_ni")}),{V("ng_ni")},IF(ISNUMBER({V("ca_ni")}),{V("ca_ni")},IF(ISNUMBER({V("ca_eps")}),{V("e_ni")}+{V("d_taxd")},"")))')
    S('ng_ni', '      Memo: Google non-GAAP net income (release; to Q4-16)', 'memo', 'm', data='ng_ni_pub', flow=True)
    S('ca_ni', '      Memo: net income excluding the EC fine (release; Q2-17, Q2-18, Q1-19)', 'memo', 'm', data='ca_ni', flow=True)
    S('e_c_eps_m', '    Company non-GAAP net income ÷ diluted shares ($)', 'eps_memo', 'ps', hist=lambda: f'=IF(ISNUMBER({V("e_c_ni")}),IFERROR({V("e_c_ni")}/{V("sh_dil")},""),"")')
    S('e_c_eps', '    Company-published non-GAAP diluted EPS ($, split-adjusted)', 'eps_memo', 'ps', hist=lambda: f'=IF(ISNUMBER({V("ng_eps")}),{V("ng_eps")},IF(ISNUMBER({V("ca_eps")}),{V("ca_eps")},""))')
    S('ng_eps', '      Memo: Google non-GAAP EPS (release)', 'eps_memo', 'ps', data='ng_eps_pub')
    S('ca_eps', '      Memo: EPS excluding the EC fine / Tax Act (release; split-adjusted)', 'eps_memo', 'ps', data='ca_eps')
    S('e_c_chk', '    Check: rebuilt vs company-published non-GAAP EPS (should be 0.00; ±0.015)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_c_eps")}),ISNUMBER({V("e_c_eps_m")})),IF(ABS({V("e_c_eps_m")}-{V("e_c_eps")})<=0.0151,0,ROUND({V("e_c_eps_m")}-{V("e_c_eps")},2)),"n/p")')
    S('e_adjebt', '  Adjusted earnings before tax (adjusted OI + interest income − interest expense + other OI&E)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_adj")}),{V("o_adj")}+N({V("is_oie")})-N({V("d_eqg")}),"")')
    S('e_rate', '  Adjusted effective tax rate (1 − adjusted NI / adjusted EBT, continuing operations)', 'pct', 'pct',
      all=lambda: f'=IF(AND(ISNUMBER({V("e_adjni")}),ISNUMBER({V("e_adjebt")})),IFERROR(1-{V("e_adjni")}/{V("e_adjebt")},""),"")')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Revenues y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_svc', '  Google Services revenues y/y %', 'growth', 'pct', all=growth('rv_svc'))
    S('gm_cloud', '  Google Cloud revenues y/y %', 'growth', 'pct', all=growth('rv_cloud'))
    S('gm_adjop', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_ni', '  Net income y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_gm', '  Gross margin %', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("is_cor")}),IFERROR(1-{V("is_cor")}/{V("is_rev")},""),"")')
    S('gm_adjop_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_inc', '  Incremental adjusted operating margin', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_rd', '  R&D % of revenues', 'pct', 'pct', all=ratio('is_rd', 'is_rev'))
    S('gm_sm', '  Sales & marketing % of revenues', 'pct', 'pct', all=ratio('is_sm', 'is_rev'))
    S('gm_ga', '  G&A % of revenues', 'pct', 'pct', all=ratio('is_ga', 'is_rev'))
    blank()
