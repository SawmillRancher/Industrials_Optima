"""Row specification of the MCO Model sheet, part 1 (MLM template layout and process):
MIS ratings revenue by line of business (Corporate Finance / Structured Finance / Financial Institutions / Public, Project &
Infrastructure Finance / MIS Other) and MA revenue by line (Decision Solutions: Banking / Insurance / KYC; Research & Insights;
Data & Information) -> segment total revenue (incl. intersegment) x segment Adjusted Operating Margin = segment Adjusted
Operating Income (company measure) -> M&A lever -> group total & FY26 guidance calibration -> cost drivers -> income statement ->
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
def E(key): return f'${E26}${R[key]}'                       # FY2026E column (absolute)
def chk(a, b, tol=0.6, nd=1):
    return f'IF(ABS({a}-{b})<={tol},0,ROUND({a}-{b},{nd}))'
def B1(key): return f'{LQ}{R[key]}'                         # 30-Jun-2026 balance
def isq3(): return CTX.col.c == Q3E

MIS = [('cfg', 'Corporate Finance (CFG)', 'r_cfg'), ('sfg', 'Structured Finance (SFG)', 'r_sfg'), ('fig', 'Financial Institutions (FIG)', 'r_fig'),
       ('ppif', 'Public, Project & Infrastructure Finance (PPIF)', 'r_ppif'), ('moth', 'MIS Other (ICRA non-ratings, data / research)', 'r_moth')]
MA = [('bank', 'Decision Solutions — Banking', 'r_bank'), ('ins', 'Decision Solutions — Insurance', 'r_ins'), ('kyc', 'Decision Solutions — KYC', 'r_kyc'),
      ('ri', 'Research & Insights', 'r_ri'), ('di', 'Data & Information', 'r_di')]
SEG = [('mis', 'MIS', "Moody's Investors Service (credit ratings; ratings revenue by line of business + MIS Other)", MIS),
       ('ma', 'MA', "Moody's Analytics (data, research, analytics and software; recurring subscription / SaaS)", MA)]
LINES = {s: [f'{s}_{t}' for t, _, _ in ts] for s, _, _, ts in SEG}
LEG_MA = [('l_rda', 'Research, Data & Analytics (RD&A)'), ('l_ers', 'Enterprise Risk Solutions (ERS)'), ('l_ps', 'Professional Services (PS)'),
          ('l_sub', 'Subscriptions (2006–2008 basis)'), ('l_sw', 'Software (2006–2008 basis)'), ('l_rms', 'Risk Management Software (2009–2010)'),
          ('l_ds', 'Decision Solutions (total; sub-lines from 2024 basis)')]

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low of the FY26 guidance (22-Jul-2026).'))
    r = 11
    SCEN_ROWS.append((r, 'out_hdr', V0['out_hdr'], 'High', 'Mid', 'Low', V0['out_note'])); r += 1
    for key, lab, (hi, mid, lo), nf, note in V0['outlook']:
        SC[key] = r; SCEN_ROWS.append((r, 'out', lab, hi, mid, lo, note, nf)); r += 1
    r += 1
    SCEN_ROWS.append((r, 'pt_hdr', 'Q3/26E–Q4/26E and FY26 point estimates (all cases)', None, None, None, None)); r += 1
    for key, lab, vals, nf, note in V0['points']:
        SC[key] = r
        SCEN_ROWS.append((r, 'pt', lab, None, vals, None, note, nf)); r += 1
    r += 1
    SC['LEV'] = r
    SCEN_ROWS.append((r, 'lev', '  Target net debt / Adjusted Operating Income (x) — buyback plug 2027E+', *V0['lev'], V0['lev_note']))
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
    S('sec_seg', 'SEGMENT P&L — MIS · MA (revenue by line of business × segment Adjusted Operating Margin)', 'section',
      note='SEGMENT BUILD — modelling logic (revenue by line → segment external revenue + intersegment revenue → × segment Adjusted Operating Margin = segment Adjusted Operating Income → Σ = Adjusted Operating Income (company measure) → GAAP P&L)')
    blank()
    for s, code, descr, lines in SEG:
        S(f'{s}_hdr', descr, 'block', note=f'{code} — modelling logic')
        for t, tl, dk in lines:
            key = f'{s}_{t}'
            S(key, f'  {tl}', 'line', 'm1', data=dk, flow=True,
              qe=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})', ae=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})',
              note=('External revenue by line as originally reported in each release. Q3/Q4-26E: prior-year quarter × (1 + growth). 2027E+: prior year × (1 + scenario lever).')
              if t == lines[0][0] else None)
            S(key + '_g', '    y/y %', 'growth', 'pct', all=growth(key),
              qe=lambda key=key, s=s: f'={V(key + "_pre")}+{E(s + "_cal_g")}',
              ae=lambda key=key, code=code, t=t: '=' + CH(SC[f'{code}_{t.upper()}'][CTX.col.year]),
              note=f'Q3/Q4-26E: 1H26 y/y growth of the line + {code} revenue-guidance calibration Δ (Group block). 2027E–2030E: scenario lever (table →).' if t == lines[0][0] else None)
            S(key + '_pre', '    Q3/Q4-26E growth before calibration (1H26 y/y)', 'driver', 'pct',
              qe=lambda key=key: f'=IFERROR({ACT(key)}/{ACT0(key)}-1,0)')
        if s == 'ma':
            S('ma_ds', '  Memo: Decision Solutions — total (Banking + Insurance + KYC; as reported before the 2024 split)', 'memo', 'm1', flow=True,
              hist=lambda: f'=IF(ISNUMBER({V("ma_bank")}),{V("ma_bank")}+{V("ma_ins")}+{V("ma_kyc")},IF(ISNUMBER({V("ma_l_ds")}),{V("ma_l_ds")},""))',
              fc=lambda: f'={V("ma_bank")}+{V("ma_ins")}+{V("ma_kyc")}')
        cur = LINES[s]
        S(f'{s}_ns', f'  {code} revenue not split on the current lines (history before the current line structure; derived)', 'line', 'm1', flow=True,
          hist=lambda s=s, cur=cur: (f'=IF(ISNUMBER({V(s + "_pub")}),{V(s + "_pub")}-({nsum(cur)})' +
                                      (f'-IF(AND(NOT(ISNUMBER({V("ma_bank")})),ISNUMBER({V("ma_l_ds")})),{V("ma_l_ds")},0)' if s == 'ma' else '') + ',"")'),
          fc=lambda: '=0',
          note=('Consolidated segment revenue less the current lines: carries the periods before each line was first published (MIS Other from 2013; '
                'MA lines on the 2022 / 2024 bases; legacy MA lines are memo rows below).') if s == 'mis' else None)
        S(f'{s}_rev', f'  {code} — external revenue', 'line_b', 'm1', flow=True,
          hist=lambda s=s, cur=cur: f'=IF(ISNUMBER({V(s + "_pub")}),{nsum(cur)}+{V(s + "_ns")}' + (f'+IF(AND(NOT(ISNUMBER({V("ma_bank")})),ISNUMBER({V("ma_l_ds")})),{V("ma_l_ds")},0)' if s == 'ma' else '') + ',"")',
          fc=lambda s=s, cur=cur: '=' + '+'.join(V(k) for k in cur),
          note='Σ lines (+ not-split residual in history) = segment external revenue as reported.' if s == 'mis' else None)
        S(f'{s}_rev_g', '  Segment revenue y/y %', 'growth', 'pct', all=growth(f'{s}_rev'))
        S(f'{s}_mix', '  % of total revenue', 'pct', 'pct', all=ratio(f'{s}_rev', 'g_rev'))
        S(f'{s}_pub', f'  Memo: {code} external revenue as reported', 'memo', 'm1', data=f'{s}_ext', flow=True)
        S(f'{s}_chk', f'  Check: {code} line build vs reported (should be 0)', 'check', 'm1',
          hist=lambda s=s: f'=IF(AND(ISNUMBER({V(s + "_rev")}),ISNUMBER({V(s + "_pub")})),{chk(V(s + "_rev"), V(s + "_pub"))},"")')
        S(f'{s}_rec', f'  Memo: {code} recurring revenue (as reported)', 'memo', 'm1', data=f'{s}_rec', flow=True)
        S(f'{s}_rec_p', f'  {code} recurring revenue % of segment revenue', 'pct', 'pct',
          hist=lambda s=s: f'=IF(ISNUMBER({V(s + "_rec")}),IFERROR({V(s + "_rec")}/{V(s + "_rev")},""),"")')
        if s == 'ma':
            S('ma_arr', '  Memo: MA Annualized Recurring Revenue (ARR, period end; organic constant currency)', 'memo', 'm1', data='ma_arr')
            S('ma_arr_g', '  MA ARR growth y/y % (as published)', 'memo', 'pct', data='ma_arr_g')
            for k, lab in LEG_MA:
                S(f'ma_{k}', f'    Legacy line: {lab}', 'memo', 'm1', data=f'r_{k}', flow=True,
                  note='Legacy MA revenue lines as originally reported (structure in force in each period; see row comments).' if k == 'l_rda' else None)
        S(f'{s}_isr', f'  {code} intersegment revenue', 'line', 'm1', data=f'{s}_isr', flow=True,
          qe=lambda s=s: f'={V(s + "_rev")}*{V(s + "_isr_p")}', ae=lambda s=s: f'={V(s + "_rev")}*{V(s + "_isr_p")}',
          note=('MIS: royalty / fees charged to MA for use of ratings content; MA: products and services sold to MIS. Eliminated on consolidation. '
                'Forecast: % of segment external revenue held at the 1H26 ratio.') if s == 'mis' else None)
        S(f'{s}_isr_p', '    Intersegment revenue % of external revenue', 'pct', 'pct', all=ratio(f'{s}_isr', f'{s}_rev'),
          qe=lambda s=s: f'=IFERROR({ACT(s + "_isr")}/{ACT(s + "_rev")},0)', ae=lambda s=s: f'={E(s + "_isr_p")}',
          e26=lambda s=s: f'=IFERROR({ACT(s + "_isr")}/{ACT(s + "_rev")},0)')
        S(f'{s}_tot', f'  {code} — total segment revenue (external + intersegment)', 'line', 'm1', flow=True,
          all=lambda s=s: f'=IF(AND(ISNUMBER({V(s + "_rev")}),ISNUMBER({V(s + "_isr")})),{V(s + "_rev")}+{V(s + "_isr")},"")')
        S(f'{s}_aoi', f'  {code} Adjusted Operating Income (segment measure)', 'line_b', 'm1', data=f'{s}_aoi', flow=True,
          qe=lambda s=s: f'={V(s + "_tot")}*{V(s + "_m")}', ae=lambda s=s: f'={V(s + "_tot")}*{V(s + "_m")}',
          note=('Company segment measure (operating income + D&A + restructuring + other items excluded by the company; includes intersegment revenue and expense). '
                'Forecast = total segment revenue × Adjusted Operating Margin.') if s == 'mis' else None)
        S(f'{s}_m', f'  {code} Adjusted Operating Margin % (company basis: on total segment revenue)', 'pct', 'pct', all=ratio(f'{s}_aoi', f'{s}_tot'),
          qe=lambda s=s: f'={V(s + "_m_pre")}+{E("cal_m")}', ae=lambda s=s, code=code: '=' + CH(SC[f'{code}_M'][CTX.col.year]),
          note='Q3/Q4-26E: margin before calibration + adjusted-EPS-guidance calibration Δ (Group block). 2027E+: scenario lever.' if s == 'mis' else None)
        S(f'{s}_m_pre', '  Q3/Q4-26E margin before EPS calibration (prior-year quarter + 1H26 y/y drift)', 'driver', 'pct',
          qe=lambda s=s: f'={P(s + "_m")}+IFERROR({ACT(s + "_aoi")}/{ACT(s + "_tot")}-{ACT0(s + "_aoi")}/{ACT0(s + "_tot")},0)')
        S(f'{s}_m_pub', f'  Memo: {code} Adjusted Operating Margin as published (%)', 'memo', 'pct', data=f'{s}_m_pub')
        S(f'{s}_inc', '  Incremental Adjusted Operating Margin (Δ AOI / Δ total revenue)', 'pct', 'pct', all=incr(f'{s}_aoi', f'{s}_tot'))
        blank()
    S('el_hdr', 'Eliminations and growth decomposition', 'block', note='ELIMINATIONS — intersegment revenue and expense net to zero in Adjusted Operating Income')
    S('elim', '  Eliminations (intersegment revenue)', 'line', 'm1', flow=True,
      all=lambda: f'=IF(ISNUMBER({V("mis_isr")}),-({V("mis_isr")}+N({V("ma_isr")})),"")')
    S('occ_mco', '  Memo: MCO organic constant-currency revenue growth % (as published)', 'memo', 'pct', data='occ_mco')
    S('occ_ma', '  Memo: MA organic constant-currency revenue growth % (as published)', 'memo', 'pct', data='occ_ma')
    S('occ_mis', '  Memo: MIS organic constant-currency revenue growth % (as published)', 'memo', 'pct', data='occ_mis')
    S('gc_mis', '  Contribution to total revenue growth — MIS (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("mis_rev")}-{P("mis_rev")})/{P("g_rev")},"")' if CTX.col.prior else None))
    S('gc_ma', '  Contribution to total revenue growth — MA (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("ma_rev")}-{P("ma_rev")}+N({V("m_rev")})-N({P("m_rev")}))/{P("g_rev")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — MA bolt-ons; deals closed from 2027E)', 'block',
      note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=V0['m_mult'], e26_in=0.0, note=V0['m_mult_note'])
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.06)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions (reported in MA)', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}',
      note='Mid-year convention.')
    S('m_m', '  Adjusted operating margin of acquired businesses %', 'driver', 'pct', e26_in=0.0, ae_in=0.25)
    S('m_aoi', '  Adjusted Operating Income from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.02)
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=V0['m_intp'], note=V0['m_intp_note'])
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=15)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (in D&A; adjusted out of adjusted EPS)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group Total — revenue & Adjusted Operating Income (segment build) → FY26 guidance calibration', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Revenue (segment build)', 'total', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("mis_rev")}),ISNUMBER({V("ma_rev")})),{V("mis_rev")}+{V("ma_rev")},{V("is_rev")})',
      fc=lambda: f'={V("mis_rev")}+{V("ma_rev")}+N({V("m_rev")})',
      note='Σ segment external revenue (+ future acquisitions from 2027E).')
    S('g_rev_g', '  Revenue y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs consolidated revenue (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),{chk(V("g_rev"), V("is_rev"))},"")')
    S('g_aoi', 'Adjusted Operating Income (segment build)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("mis_aoi")}),ISNUMBER({V("ma_aoi")})),{V("mis_aoi")}+{V("ma_aoi")}+N({V("m_aoi")}),"")',
      note="Σ segment Adjusted Operating Income (+ future acquisitions). Moody's allocates all corporate costs to the segments, so Σ segments = consolidated Adjusted Operating Income; drives the GAAP P&L below.")
    S('g_aoim', '  Adjusted Operating Margin % (on consolidated revenue)', 'pct', 'pct', all=ratio('g_aoi', 'is_rev'))
    S('g_aoi_g', '  Adjusted Operating Income y/y %', 'growth', 'pct', all=growth('g_aoi'))
    S('g_chk_aoi', '  Check: segment build vs Adjusted Operating Income bridge (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_aoi")}),ISNUMBER({V("o_adj")})),{chk(V("g_aoi"), V("o_adj"), 1.5)},"")')
    # revenue calibration (one uniform Δ per segment over the 1H26 y/y growth of each line, solved to the segment guidance end-point)
    for s, code, *_ in SEG:
        S(f'{s}_cal_guid', f'  Memo: FY26 {code} revenue guidance end-point (FY2025 × (1 + guided growth, scenario))', 'memo', 'm1',
          e26=lambda s=s: f'={Y(s + "_rev", 2025)}*(1+{CH(SC["out_" + s + "_g"])})', note=V0[f'{s}_guid_note'])
        S(f'{s}_cal_pre', f'  {code} revenue before calibration (Q3/Q4-26E helper)', 'line', 'm1',
          qe=lambda s=s: '=' + '+'.join(f'{P(k)}*(1+{V(k + "_pre")})' for k in LINES[s]), e26=lambda s=s: f'={SQE(s + "_cal_pre")}')
        S(f'{s}_cal_sens', f'  {code} revenue sensitivity to +1.00 of growth (Q3/Q4-26E helper)', 'line', 'm1',
          qe=lambda s=s: '=' + '+'.join(P(k) for k in LINES[s]), e26=lambda s=s: f'={SQE(s + "_cal_sens")}')
        S(f'{s}_cal_g', f'  Guidance calibration: Δ y/y growth applied to all {code} lines (Q3/Q4-26E)', 'driver', 'pct',
          e26=lambda s=s: f'=({V(s + "_cal_guid")}-{ACT(s + "_rev")}-{V(s + "_cal_pre")})/{V(s + "_cal_sens")}',
          note=f'Solves the uniform growth shift (vs 1H26 y/y rates) so that FY26 {code} revenue = the guidance end-point for the active scenario.')
        S(f'{s}_cal_chk', f'  Check: FY26 {code} revenue vs guidance end-point (should be 0)', 'check', 'm1',
          e26=lambda s=s: f'=ROUND({V(s + "_rev")}-{V(s + "_cal_guid")},1)')
    S('cal_mco_g', '  Memo: FY26 MCO revenue growth guidance (scenario end-point) — information, not forced', 'memo', 'pct', e26=lambda: '=' + CH(SC['out_mco_g']))
    S('cal_mco_d', '    Model MCO revenue growth − guidance (pp)', 'memo_calc', 'pct', e26=lambda: f'={V("g_rev_g")}-{V("cal_mco_g")}')
    # margin calibration to adjusted EPS
    S('cal_eps', '  Memo: FY26 adjusted diluted EPS guidance (scenario end-point, $)', 'eps_memo', 'ps', e26=lambda: '=' + CH(SC['out_eps']), note=V0['eps_guid_note'])
    S('cal_ni', '  Adjusted net income required (FY26E diluted shares × EPS guidance)', 'memo_calc', 'm1', e26=lambda: f'={V("cal_eps")}*{V("e_sh")}')
    S('cal_k', '  Adjusted net income excluding Adjusted Operating Income (Q3/Q4-26E helper: (−D&A + acquired-intangible amortization + net interest + other non-operating) × (1 − t) − NCI)', 'line', 'm1',
      qe=lambda: f'=(-{V("d_dna")}+{V("d_amort")}+{V("is_int")}+{V("is_onop")})*(1-{V("is_etr")})-{V("is_nci")}', e26=lambda: f'={SQE("cal_k")}')
    S('cal_oi', '  Q3–Q4/26E Adjusted Operating Income required ((adjusted NI − 1H actual − helper) ÷ (1 − tax rate))', 'memo_calc', 'm1',
      e26=lambda: f'=({V("cal_ni")}-{ACT("e_adjni")}-{V("cal_k")})/(1-{PT("pt_etr")})')
    S('cal_oi_pre', '  Adjusted Operating Income before margin calibration (Q3/Q4-26E helper)', 'line', 'm1',
      qe=lambda: '=' + '+'.join(f'{V(s + "_tot")}*{V(s + "_m_pre")}' for s, *_ in SEG), e26=lambda: f'={SQE("cal_oi_pre")}')
    S('cal_segrev', '  Total segment revenue (Q3/Q4-26E helper)', 'line', 'm1', qe=lambda: '=' + '+'.join(V(s + '_tot') for s, *_ in SEG), e26=lambda: f'={SQE("cal_segrev")}')
    S('cal_m', '  Guidance calibration: Δ segment Adjusted Operating Margin (Q3/Q4-26E)', 'driver', 'pct',
      e26=lambda: f'=({V("cal_oi")}-{V("cal_oi_pre")})/{V("cal_segrev")}',
      note='Solves the uniform segment-margin shift so that FY26 adjusted diluted EPS = the guidance end-point for the active scenario.')
    S('cal_eps_chk', '  Check: FY26 adjusted diluted EPS vs guidance end-point (should be 0.00)', 'check', 'ps', e26=lambda: f'=ROUND({V("e_eps")}-{V("cal_eps")},2)')
    for k, lab, row, nf in (('cal_aom', 'FY26 Adjusted Operating Margin guidance (52–53%)', 'g_aoim', 'pct'), ('cal_misam', 'FY26 MIS Adjusted Operating Margin guidance (~65%)', 'mis_m', 'pct'),
                            ('cal_maam', 'FY26 MA Adjusted Operating Margin guidance (34–35%)', 'ma_m', 'pct'), ('cal_geps', 'FY26 diluted EPS guidance ($)', 'eps_dil', 'ps'),
                            ('cal_fcf', 'FY26 Free Cash Flow guidance ($m)', 'fcf', 'm1')):
        S(k, f'  Memo: {lab} — scenario end-point, information (not forced)', 'memo', nf, e26=lambda k=k: '=' + CH(SC['out_' + k[4:]]))
        S(k + '_d', '    Model − guidance', 'memo_calc', nf, e26=lambda k=k, row=row: f'={V(row)}-{V(k)}')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A & items excluded from Adjusted Operating Income', 'block',
      note='COST DRIVERS — inputs that drive forecast cost lines (Q3/Q4-26E: point estimates from the FY26 guidance reconciliation; 2027E+: % of revenue or schedules)')
    S('d_dna', '  Depreciation & amortization (total, IS face)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("is_dna")}),{V("is_dna")},"")', fc=lambda: f'={V("d_dep")}+{V("d_amort")}')
    S('d_amort', '  Amortization of acquired intangible assets (inside D&A; adjusted out of adjusted EPS from 2016)', 'line', 'm1', data='amort', flow=True,
      qe=lambda: f'={PT("pt_amort")}', ae=lambda: f'={V("d_amort_sch")}+N({V("m_amort")})',
      note='History: XBRL AmortizationOfIntangibleAssets (10-K / 10-Q as first filed; equals "acquisition-related intangible amortization" in the adjusted-EPS bridge). Q3/Q4-26E: 10-Q schedule (remainder of 2026 ÷ 2). 2027E+: schedule of intangibles held at 30-Jun-2026 + future-acquisition amortization.')
    S('d_amort_sch', '  Amortization schedule — intangibles held at 30-Jun-2026 (input)', 'driver', 'm1', ae_in=V0['amort_sched'], note=V0['amort_note'])
    S('d_dep', '  Depreciation & amortization of PP&E / internal-use software (D&A − acquired-intangible amortization)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("d_dna")}),ISNUMBER({V("d_amort")})),{V("d_dna")}-{V("d_amort")},"")',
      qe=lambda: f'={PT("pt_dep")}', ae=lambda: f'={V("is_rev")}*{V("d_dep_pct")}')
    S('d_dep_pct', '  Depreciation (excl. acquired intangibles) % of revenue', 'pct', 'pct', all=ratio('d_dep', 'is_rev'), ae_in=V0['dep_pct'],
      note='Capitalised software and the New York / London office build-outs (capex ~$450m in FY26).')
    S('d_restr', '  Restructuring (excluded from Adjusted Operating Income)', 'line', 'm1', flow=True, hist=lambda: f'=IF(ISNUMBER({V("is_restr")}),{V("is_restr")},"")',
      qe=lambda: f'={PT("pt_restr")}', ae_in=V0['ae_restr'], note=V0['restr_note'])
    S('d_othx', '  Other items excluded from Adjusted Operating Income (settlements, impairments, acquisition costs, asset abandonment, reserves, duplicate rent)', 'line', 'm1',
      data='oa_other', flow=True, labkey='oa_other_lab', qe=lambda: f'={PT("pt_othx")}', ae_in=V0['ae_othx'],
      note='Company items per the Adjusted Operating Income reconciliation of each period (labels in cell comments). Forecast: FY26 guidance reconciliation (reserve for an international non-income tax obligation, duplicate rent — NY HQ) then input.')
    S('d_opr', '  Operating expense % of revenue', 'pct', 'pct', all=ratio('is_opr', 'is_rev'),
      qe=lambda: f'={P("d_opr")}+IFERROR({ACT("is_opr")}/{ACT("is_rev")}-{ACT0("is_opr")}/{ACT0("is_rev")},0)', ae_in=V0['opr_pct'],
      note='Q3/Q4-26E: prior-year quarter ratio + 1H26 y/y drift; 2027E+ input. SG&A is the balancing line (operating income from the Adjusted Operating Income build).')
    S('d_sbc', '  Stock-based compensation (cash-flow statement)', 'line', 'm1', data='cf_sbc', flow=True,
      qe=lambda: f'={P("d_sbc")}*(1+IFERROR({ACT("d_sbc")}/{ACT0("d_sbc")}-1,0))', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}',
      note="Q3/Q4-26E: prior-year quarter × 1H26 y/y; 2027E+: % of revenue. Moody's does not adjust out stock-based compensation.")
    S('d_sbc_pct', '  Stock-based compensation % of revenue', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_onop', '  Other non-operating income, net (FX, pension non-service, affiliates, investments), input', 'line', 'm1',
      qe=lambda: f'={PT("pt_onop")}', ae_in=V0['onop'], note='1H26 $16m. Input (assumption).')
    S('d_gain', '  Gains on business divestitures and other non-operating items excluded from adjusted EPS (input)', 'line', 'm1',
      qe=lambda: (f'=0' if isq3() else f'={PT("pt_gain")}'), ae_in=0.0, note=V0['gain_note'])
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF OPERATIONS (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (operating income = Adjusted Operating Income − D&A − restructuring − other items; SG&A is the balancing line)')
    S('is_rev', 'Revenue', 'total', 'm1', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the segment build.')
    S('is_opr', 'Operating expense', 'line', 'm1', data='opr', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_opr")}')
    S('is_sga', 'Selling, general & administrative expense', 'line', 'm1', data='sga', flow=True,
      fc=lambda: f'={V("is_rev")}-{V("is_oi")}-{V("is_opr")}-{V("is_dna")}-{V("is_restr")}-{V("is_othop")}',
      note='Forecast = balancing line (revenue − operating income − other expense lines); includes the reserve / duplicate-rent items the company excludes from Adjusted Operating Income.')
    S('is_dna', 'Depreciation & amortization', 'line', 'm1', data='dna', flow=True, fc=lambda: f'={V("d_dna")}')
    S('is_restr', 'Restructuring', 'line', 'm1', data='restr', flow=True, fc=lambda: f'={V("d_restr")}')
    S('is_othop', 'Other operating items shown separately (settlement charges, impairments, acquisition-related expenses, asset abandonment; gains negative)', 'line', 'm1',
      data='othop', flow=True, fc=lambda: '=0', labkey='othop_lab')
    S('is_texp', 'Total expenses', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_opr")}),{V("is_opr")}+{V("is_sga")}+{V("is_dna")}+{V("is_restr")}+{V("is_othop")},"")')
    S('is_oi', 'Operating income', 'total', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_texp")}),{V("is_rev")}-{V("is_texp")},"")',
      fc=lambda: f'={V("g_aoi")}-{V("d_dna")}-{V("d_restr")}-{V("d_othx")}',
      note='Forecast = Adjusted Operating Income − D&A − restructuring − other excluded items.')
    S('is_om', '  Operating margin %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('is_oi_pub', '  Memo: operating income as reported', 'memo', 'm1', data='oi', flow=True)
    S('is_oi_chk', '  Check: operating income vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_oi_pub")}),{chk(V("is_oi"), V("is_oi_pub"), 1.5)},"")')
    S('is_int', 'Interest expense, net (expense −)', 'line', 'm1', data='int_net', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'=-({P("ds_notes")}*{V("ds_r_notes")}+{P("ds_cp")}*{V("ds_r_cp")}+{V("ds_fees")})+{P("cf_end")}*{V("ds_r_cash")}',
      note='Q3/Q4-26E point estimate (FY26 guidance $220–240m). 2027E+ = −(rate × opening notes + rate × opening commercial paper + UTP / pension interest & fees) + yield × opening cash (no circularity).')
    S('is_onop', 'Other non-operating income (expense), net', 'line', 'm1', data='onop', flow=True, fc=lambda: f'={V("d_onop")}')
    S('is_gain', 'Other non-operating items shown separately (gains on divestitures / step acquisitions, CCXI, hedge losses)', 'line', 'm1', data='gain', flow=True,
      fc=lambda: f'={V("d_gain")}', labkey='gain_lab')
    S('is_ebt', 'Income before provision for income taxes', 'line_b', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("is_oi")}),{V("is_oi")}+{V("is_int")}+{V("is_onop")}+N({V("is_gain")}),"")')
    S('is_tax', 'Provision for income taxes', 'line', 'm1', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Q3/Q4-26E: point estimate (FY26 ETR guidance 23–25%). 2027E+: input. The model applies the same rate to adjusting items.')
    S('is_nitot', 'Net income', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_nci', '  Less: net income attributable to noncontrolling interests', 'line', 'm1', data='nci', flow=True, qe=lambda: f'={PT("pt_nci")}', ae_in=V0['nci'])
    S('is_ni', "Net income attributable to Moody's", 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_nitot")}),{V("is_nitot")}-N({V("is_nci")}),"")')
    S('is_ni_chk', '  Check: net income attributable vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),{chk(V("is_ni"), V("is_ni_pub"), 1.5)},"")')
    S('is_ni_pub', "  Memo: net income attributable to Moody's as reported", 'memo', 'm1', data='ni', flow=True)
    S('is_dda', '  Memo: depreciation & amortization (total)', 'memo_calc', 'm1', all=lambda: f'={V("d_dna")}')
    S('is_sbc', '  Memo: stock-based compensation', 'memo_calc', 'm1', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', "(Earnings per share — Moody's common stock)", 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={B1("bs_shares")}-{E("bb_sh")}*{0.25 if isq3() else 0.75}+{E("bb_iss")}*{0.25 if isq3() else 0.75}',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q3/Q4-26E: shares outstanding at 30-Jun-2026 − 2H buybacks (spread evenly; ¼ / ¾ weighted) + equity-plan issuance. 2027E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({LQ}{R["sh_dil"]}-{LQ}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")',
      note='Net income attributable / weighted diluted shares (±$0.01 vs reported).')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0101,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('dps', '  Dividends declared per share ($)', 'line', 'ps', data='dps', flow=True, qe_in=V0['dps_q'],
      ae=lambda: f'={P("dps")}*(1+{V("dps_g")})', note=V0['dps_note'])
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'])
    blank()

    # ------------------------------------------------------------------ RECON 1: operating income -> adjusted operating income
    S('sec_r1', 'RECONCILIATION: OPERATING INCOME → ADJUSTED OPERATING INCOME (company definition)', 'section',
      note='ADJUSTED OPERATING INCOME — per the release reconciliations (operating income + D&A + restructuring + other items the company excludes); item labels in the cell comments of the cost-driver rows')
    S('o_op', 'Operating income (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_oi")}')
    S('o_dna', '  (+) Depreciation & amortization', 'line', 'm1', all=lambda: f'={V("d_dna")}')
    S('o_restr', '  (+) Restructuring', 'line', 'm1', all=lambda: f'={V("d_restr")}')
    S('o_oth', '  (+) Other items excluded (settlement charges, impairments, acquisition-related expenses, asset abandonment, reserves, duplicate rent)', 'line', 'm1',
      all=lambda: f'={V("d_othx")}')
    S('o_adj', '  = Adjusted Operating Income (model bridge)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+N({V("o_dna")})+N({V("o_restr")})+N({V("o_oth")}),"")',
      note='Rebuilt from the published reconciliation items; forecast = operating income + forecast items (equals the segment build — check in the Group block).')
    S('o_adj_m', '  Adjusted Operating Margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company-published Adjusted Operating Income', 'memo', 'm1', data='adj_oi_pub', flow=True)
    S('o_chk', '  Check: model bridge vs company-published (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),{chk(V("o_adj"), V("o_pub"), 1.5)},"n/p")')
    S('o_def', '  Definition / basis (company Adjusted Operating Income definition in force)', 'text', 'gen',
      note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('o_adj_g', '  Adjusted Operating Income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental Adjusted Operating Margin (Δ AOI / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: net income -> EBITDA -> adjusted EBITDA
    S('sec_r2', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA → ADJUSTED EBITA (model definitions)', 'section',
      note='EBITDA — model definition (Moody\'s publishes no EBITDA). Adjusted EBITDA = EBITDA + restructuring + other excluded items = the company\'s Adjusted Operating Income (same definition).')
    S('r_ni', "Net income attributable to Moody's", 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('r_nci', '  (+) Net income attributable to noncontrolling interests', 'line', 'm1', all=lambda: f'=N({V("is_nci")})')
    S('r_tax', '  (+) Provision for income taxes', 'line', 'm1', all=lambda: f'={V("is_tax")}')
    S('r_nonop', '  (−) Non-operating income / (+) expense (interest, other, divestiture gains)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("is_int")}),-({V("is_int")}+{V("is_onop")}+N({V("is_gain")})),"")')
    S('r_gebit', '  = EBIT (operating income)', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_nci")}+{V("r_tax")}+{V("r_nonop")},"")')
    S('r_dna', '  (+) Depreciation & amortization', 'line', 'm1', all=lambda: f'={V("d_dna")}')
    S('r_ebitda', '  = EBITDA (model)', 'total', 'm1', all=lambda: f'=IF(AND(ISNUMBER({V("r_gebit")}),ISNUMBER({V("r_dna")})),{V("r_gebit")}+{V("r_dna")},"")')
    S('r_items', '  (+) Restructuring and other items excluded by the company', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_restr")}),N({V("o_restr")})+N({V("o_oth")}),"")')
    S('r_adj', '  = Adjusted EBITDA (= company Adjusted Operating Income)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda")}),ISNUMBER({V("r_items")})),{V("r_ebitda")}+{V("r_items")},"")',
      note='Used for leverage (net debt / Adjusted Operating Income) and EV / EBITDA.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_chk', '  Check: Adjusted EBITDA vs company-published Adjusted Operating Income (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("o_pub")}),ISNUMBER({V("r_adj")})),{chk(V("r_adj"), V("o_pub"), 1.5)},"n/p")')
    S('r_ebit_h', 'To adjusted EBITA (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_dep', '  (−) Depreciation & amortization excl. acquired intangibles', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("d_dep")}),-{V("d_dep")},"")')
    S('r_ebit', '  = Adjusted EBITA (Adjusted Operating Income − depreciation; before acquired-intangible amortization)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_adj")}),ISNUMBER({V("r_dep")})),{V("r_adj")}+{V("r_dep")},"")',
      note='Standard NOPAT basis (playbook 5.7): adjusted EBIT before acquired-intangible amortization; stock-based compensation is already expensed. Restructuring and other excluded cash items are deducted in the DCF (row below).')
    S('r_ebit_m', '  Adjusted EBITA margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: restructuring and other excluded items (cash costs adjusted out; deducted in the DCF)', 'memo_calc', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("o_restr")}),N({V("o_restr")})+N({V("o_oth")}),"")')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: NET INCOME / DILUTED EPS → ADJUSTED NET INCOME → ADJUSTED DILUTED EPS (company definition)', 'section',
      note='ADJUSTED EPS — net income attributable + pre-tax items (acquired-intangible amortization from 2016, restructuring, other operating items, non-operating gains / losses) − tax effect of the items ± discrete tax items')
    S('e_ni', "Net income attributable to Moody's (GAAP)", 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('e_amort', '  (+) Acquisition-related intangible amortization (pre-tax; excluded from 2016)', 'line', 'm1', data='ea_amort', flow=True, fc=lambda: f'={V("d_amort")}')
    S('e_restr', '  (+) Restructuring (pre-tax)', 'line', 'm1', data='ea_restr', flow=True, fc=lambda: f'={V("d_restr")}')
    S('e_oop', '  (+) Other operating items (pre-tax: settlement charges, impairments, acquisition costs, asset abandonment, reserves, duplicate rent)', 'line', 'm1',
      data='ea_op', flow=True, labkey='ea_op_lab', fc=lambda: f'={V("d_othx")}+{V("is_othop")}')
    S('e_nonop', '  (+) Non-operating items (pre-tax: divestiture / remeasurement gains (−), CCXI, hedge losses, legacy items)', 'line', 'm1',
      data='ea_nonop', flow=True, labkey='ea_nonop_lab', fc=lambda: f'=-{V("d_gain")}')
    S('e_tax', '  (−) Tax effect of the items & discrete tax items (legacy tax, Tax Act, UTP releases)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("e_pubni")}),{V("e_pubni")}-{V("e_ni")}-({nsum(["e_amort", "e_restr", "e_oop", "e_nonop"])}),IF(ISNUMBER({V("e_ni")}),0,""))',
      fc=lambda: f'=-({V("e_amort")}+{V("e_restr")}+{V("e_oop")}+{V("e_nonop")})*{V("is_etr")}',
      note='Historical: published adjusted net income − net income − pre-tax items (periods without a published measure: adjusted = GAAP). Forecast: items × the effective tax rate.')
    S('e_adjni', '  = Adjusted net income (model bridge)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("e_tax")}),{V("e_ni")}+{nsum(["e_amort", "e_restr", "e_oop", "e_nonop"])}+{V("e_tax")},"")')
    S('e_pubni', '  Company-published adjusted (non-GAAP) net income', 'memo', 'm1', data='adj_ni_pub', flow=True)
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted diluted EPS ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted (non-GAAP) diluted EPS ($)', 'eps_memo', 'ps', data='e_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.02 per-share rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0201,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Adjusted diluted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_rate', '  Adjusted effective tax rate (adjusted tax ÷ adjusted pre-tax income)', 'pct', 'pct',
      all=lambda: f'=IFERROR(({V("is_tax")}-{V("e_tax")})/({V("is_ebt")}+{nsum(["e_amort", "e_restr", "e_oop", "e_nonop"])}),"")')
    S('e_def', '  Definition / basis (company adjusted EPS definition)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Revenue y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_mis', '  MIS revenue y/y %', 'growth', 'pct', all=growth('mis_rev'))
    S('gm_ma', '  MA revenue y/y %', 'growth', 'pct', all=growth('ma_rev'))
    S('gm_adjop', '  Adjusted Operating Income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('gm_op', '  Operating income (GAAP) y/y %', 'growth', 'pct', all=growth('is_oi'))
    S('gm_ni', '  Net income attributable y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted diluted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_adjop_m', '  Adjusted Operating Margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_inc', '  Incremental Adjusted Operating Margin (Δ AOI / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA (= Adjusted Operating Income) margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_opr', '  Operating expense % of revenue', 'pct', 'pct', all=ratio('is_opr', 'is_rev'))
    S('gm_sga', '  SG&A % of revenue', 'pct', 'pct', all=ratio('is_sga', 'is_rev'))
    blank()
