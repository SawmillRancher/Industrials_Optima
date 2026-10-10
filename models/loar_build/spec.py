"""Row specification of the LOAR Model sheet, part 1 (MLM template layout and process):
end-market build -> organic / acquired sales -> M&A lever -> group sales & Adjusted EBITDA (FY26 outlook calibration) ->
cost drivers -> income statement -> GAAP-to-adjusted bridges -> growth & margins."""
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

EMS = [('com', 'Commercial aerospace', 'COM'), ('bj', 'Business jet & general aviation', 'BJ'), ('def', 'Defense', 'DEF'),
       ('oth', 'Other / non-aerospace', 'OTH')]
LINES = [f'{k}_{t}' for k, _, _ in EMS for t in ('oem', 'am')]

# ====================================================================== scenario table (AX:BB)
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
    SCEN_ROWS.append((r, 'pt_hdr', 'FY26 point estimates (all cases)', None, None, None, None)); r += 1
    for key, lab, vals, nf, note in V0['points']:
        SC[key] = r
        if isinstance(vals, tuple): SCEN_ROWS.append((r, 'out', lab, vals[0], vals[1], vals[2], note, nf))
        else: SCEN_ROWS.append((r, 'pt', lab, None, vals, None, note, nf))
        r += 1
    r += 1
    SC['LEV'] = r
    SCEN_ROWS.append((r, 'lev', '  Minimum net debt / Adjusted EBITDA (x) — buyback floor 2027E+', *V0['lev'], V0['lev_note']))
    r += 2
    for name, lab, dbull, dbear, base, note, nf, clamp in V0['blocks']:
        SCEN_ROWS.append((r, 'blk', lab, dbull, 'Δ →', dbear, note, nf)); hdr = r; r += 1
        SC[name] = {}
        for y, b in zip((2027, 2028, 2029, 2030), base):
            SC[name][y] = r; SCEN_ROWS.append((r, 'yr', f'  {y}E', hdr, b, clamp, None, nf)); r += 1
    return r

# ====================================================================== row spec
def build_spec(V0):
    S = add
    # ------------------------------------------------------------------ END-MARKET BUILD
    S('sec_em', 'END-MARKET P&L — COMMERCIAL AEROSPACE · BUSINESS JET & GA · DEFENSE · OTHER (OEM × aftermarket build)', 'section',
      note='END-MARKET BUILD — modelling logic (OEM / aftermarket net sales by end market → net sales × Adjusted EBITDA margin → Adjusted EBITDA → GAAP P&L)')
    blank()
    for k, title, code in EMS:
        S(f'{k}_hdr', {'com': 'Commercial aerospace (seat-belt & airbag restraints, interiors latches, fluid & ice protection, avionics interface)',
                       'bj': 'Business jet & general aviation (auto-throttles, brakes, actuation, restraints)',
                       'def': 'Defense (military aircraft components, restraints, sensors; LMB fans & motors from Dec-2025)',
                       'oth': 'Other (industrial / non-aerospace; "Non-Aerospace" in the Q2-25 and Q3-25 releases)'}[k], 'block',
          note=f'{title.upper()} — modelling logic')
        for t, tl in (('oem', 'OEM'), ('am', 'Aftermarket')):
            key = f'{k}_{t}'
            S(key, f'  {tl} net sales', 'line', 'm1', data=f'em_{key}', flow=True,
              qe=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})', ae=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})',
              note=('End-market sales as published (release Table 5; FY2022-23 prospectus note; Q1-23 = 1H-23 − Q2-23). Not published before 2022 '
                    'or for 2022 quarters. Q3/Q4-26E: prior-year quarter × (1 + growth). 2027E+: prior year × (1 + scenario lever).') if t == 'oem' else None)
            S(key + '_g', '    y/y %', 'growth', 'pct', all=growth(key),
              qe=lambda key=key: f'={V(key + "_pre")}+{Q3v("cal_g")}',
              ae=lambda key=key, code=code, t=t: '=' + CH(SC[f'{code}_{t.upper()}'][CTX.col.year]),
              note='Q3/Q4-26E: growth before calibration (row below) + revenue-outlook calibration Δ (Group block). 2027E–2030E: scenario lever (Bull/Base/Bear table →).' if t == 'oem' else None)
            S(key + '_pre', '    Q3/Q4-26E growth before revenue calibration (1H/26 y/y)', 'driver', 'pct',
              qe=lambda key=key: f'=IFERROR({H1(key)}/{H1(key, 2025)}-1,0)',
              note='1H/26 y/y growth of the line: includes LMB (closed 23-Dec-2025) and Harper Engineering (21-Jan-2026), which stay inorganic through Q4/26E; Beadlight anniversaries 28-Jul-2026.' if t == 'oem' else None)
        S(f'{k}_tot', f'  {title} — net sales', 'line_b', 'm1', all=lambda k=k: f'=IF(ISNUMBER({V(k + "_oem")}),{V(k + "_oem")}+{V(k + "_am")},"")')
        S(f'{k}_tot_g', '  Net sales y/y %', 'growth', 'pct', all=growth(f'{k}_tot'))
        S(f'{k}_mix', '  % of total net sales', 'pct', 'pct', all=ratio(f'{k}_tot', 'g_rev'))
        S(f'{k}_amsh', '  Aftermarket % of end-market sales', 'pct', 'pct', all=ratio(f'{k}_am', f'{k}_tot'))
        blank()
    S('mx_hdr', 'OEM / aftermarket mix (all end markets)', 'block', note='MIX — outputs')
    S('mx_oem', '  Total OEM net sales', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("com_oem")}),{"+".join(V(k + "_oem") for k, _, _ in EMS)},"")')
    S('mx_am', '  Total aftermarket net sales', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("com_am")}),{"+".join(V(k + "_am") for k, _, _ in EMS)},"")')
    S('mx_am_pct', '  Aftermarket % of net sales', 'pct', 'pct', all=ratio('mx_am', 'g_rev'))
    S('mx_coem_g', '  Commercial + business jet & GA OEM y/y % (company outlook metric)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("com_oem")}+{V("bj_oem")})/({P("com_oem")}+{P("bj_oem")})-1,"")' if CTX.col.prior else None),
      note='FY26 outlook (Q2-26 release): commercial, business jet & GA OEM growth 17–20%; aftermarket low-double digits; defense mid-single digits.')
    S('mx_cam_g', '  Commercial + business jet & GA aftermarket y/y %', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("com_am")}+{V("bj_am")})/({P("com_am")}+{P("bj_am")})-1,"")' if CTX.col.prior else None))
    S('mx_def_g', '  Defense y/y %', 'growth', 'pct', all=lambda: (f'=IFERROR({V("def_tot")}/{P("def_tot")}-1,"")' if CTX.col.prior else None))
    S('mx_unsplit', '  Net sales not split by end market (pre-2022 annual; 2022 quarters)', 'line', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}-N({V("mx_oem")})-N({V("mx_am")}),"")',
      note='Net sales less the end-market split: end-market sales were first disclosed for FY2022 (prospectus).')
    blank()

    # ------------------------------------------------------------------ organic / acquired
    S('a_hdr', 'Organic vs acquired net sales (company definition: acquisitions organic from the 13th month)', 'block',
      note='ORGANIC / ACQUIRED — as published in each release; acquisitions: SCHROTH Jul-22, DAC Jul-23, CAV Sep-23, AAI Aug-24, Beadlight Jul-25, LMB Dec-25, Harper Jan-26')
    S('a_org', '  Organic net sales (as published)', 'line', 'm1', data='org_sales', flow=True,
      qe=lambda: f'={V("is_rev")}-{V("a_acq")}', note='Net sales of businesses owned in both periods (company definition). Q3/Q4-26E = net sales − acquisition sales input.')
    S('a_acq', '  Net acquisition sales (net sales − organic)', 'line', 'm1', data='acq_sales', flow=True, qe_in=V0['qe_acq'], note=V0['qe_acq_note'])
    S('a_org_g', '  Organic growth % (organic sales ÷ prior-period net sales − 1)', 'growth', 'pct', data='org_g',
      qe=lambda: f'=IFERROR({V("a_org")}/{P("is_rev")}-1,"")', e26=lambda: f'=IFERROR({V("a_org")}/{P("is_rev")}-1,"")',
      ae=lambda: f'=IFERROR(({V("is_rev")}-{V("m_rev")})/({P("is_rev")}-{P("m_rev")})-1,"")',
      note='Historical as published. 2027E+: growth of the current portfolio excluding future acquisitions (LMB / Harper organic from 2027).')
    S('a_acq_g', '  Acquisition contribution to growth %', 'growth', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("a_acq")}),ISNUMBER({P("is_rev")})),IFERROR({V("a_acq")}/{P("is_rev")},""),"")' if CTX.col.prior else None),
      ae=lambda: f'=IFERROR({V("m_rev")}/{P("is_rev")},"")')
    S('a_chk', '  Check: published organic growth vs organic sales ÷ prior net sales (should be 0.0%)', 'check', 'pct',
      hist=lambda: (f'=IF(AND(ISNUMBER({V("a_org_g")}),ISNUMBER({V("a_org")}),ISNUMBER({P("is_rev")})),IF(ABS({V("a_org")}/{P("is_rev")}-1-{V("a_org_g")})<0.0015,0,ROUND({V("a_org")}/{P("is_rev")}-1-{V("a_org_g")},3)),"n/p")'
                    if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — bolt-ons, unallocated; deals closed from 2027E)', 'block',
      note='M&A LEVER — acquired sales = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=6.0, e26_in=0.0,
      note='Loar deals: AAI $383.5m, LMB $474.8m on ~$60m 2026E sales (~7.9x), Harper $249.8m (+ up to $55m earn-out); 6.0x input.')
    S('m_acq_sales', '  Annualised sales acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.07)
    S('m_run', '  Run-rate sales of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Net sales from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}',
      note='Mid-year convention: half a year of sales in the year of acquisition. Unallocated to end markets (separate line in the Group build).')
    S('m_m', '  Adjusted EBITDA margin of acquired businesses %', 'driver', 'pct', e26_in=0.0, ae_in=0.40,
      note='LMB: ~$30m Adjusted EBITDA on ~$60m sales (2026E, company); Loar targets niche proprietary businesses with ≥35–40% margins post value drivers.')
    S('m_ebitda', '  Adjusted EBITDA from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.02)
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.50,
      note='Recent PPAs: AAI 40%, LMB 45%, Harper 61% of consideration in intangibles (customer relationships, trade names, technology).')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=15)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)',
      note='Non-cash; added back in Adjusted EPS (current company definition) and excluded from Adjusted EBITDA.')
    blank()

    # ------------------------------------------------------------------ group total & outlook calibration
    S('g_hdr', 'Group Total — net sales & Adjusted EBITDA (end-market build) → FY26 outlook calibration', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Net sales (end-market build)', 'total', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("com_oem")}),{"+".join("N(" + V(k) + ")" for k in LINES)},{V("is_rev")})',
      fc=lambda: f'={"+".join(V(k) for k in LINES)}+N({V("m_rev")})',
      note='Σ end-market OEM + aftermarket sales (+ future acquisitions from 2027E). Before 2022 (and 2022 quarters) = reported net sales (no split).')
    S('g_rev_g', '  Net sales y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: end-market build vs consolidated net sales (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=0.15,0,ROUND({V("g_rev")}-{V("is_rev")},1)),"")')
    S('g_adjm', '  Adjusted EBITDA margin % (current portfolio, before future M&A)', 'pct', 'pct',
      hist=lambda: f'=IF(ISNUMBER({V("r_adj_pub")}),IFERROR({V("r_adj_pub")}/{V("is_rev")},""),"")',
      qe=lambda: f'={V("g_adjm_pre")}+{Q3v("cal_m")}', e26=lambda: f'=IFERROR(({V("g_adj")})/{V("is_rev")},"")',
      ae=lambda: '=' + CH(SC['EBM'][CTX.col.year]),
      note='Historical = published Adjusted EBITDA ÷ net sales. Q3/Q4-26E: margin before calibration + Adjusted-EBITDA-outlook calibration Δ. 2027E–2030E: scenario lever (current portfolio).')
    S('g_adjm_pre', '  Adjusted EBITDA margin before outlook calibration % (Q3/Q4-26E helper)', 'pct', 'pct',
      qe=lambda: f'={P("g_adjm")}+({H1("r_adj_pub")}/{H1("is_rev")}-{H1("r_adj_pub", 2025)}/{H1("is_rev", 2025)})',
      note='Prior-year quarter margin + (1H/26 − 1H/25 Adjusted EBITDA margin drift: +2.5pts, LMB / Harper mix and value drivers).')
    S('g_adj', 'Adjusted EBITDA (end-market build)', 'total', 'm1',
      hist=lambda: f'={V("r_adj_pub")}',
      qe=lambda: f'={V("is_rev")}*{V("g_adjm")}', e26=lambda: S26('g_adj'),
      ae=lambda: f'=({V("is_rev")}-{V("m_rev")})*{V("g_adjm")}+{V("m_ebitda")}',
      note="Loar's primary profit KPI and guidance metric. Forecast = net sales × Adjusted EBITDA margin (+ future acquisitions' EBITDA). Drives the GAAP P&L below.")
    S('g_adj_g', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('g_adj'))
    S('g_chk_adj', '  Check: build vs Adjusted EBITDA bridge (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_adj")}),ISNUMBER({V("r_adj")})),ROUND({V("g_adj")}-{V("r_adj")},1),"")')
    S('cal_guid', '  Memo: FY26 net sales guidance (scenario end-point)', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_rev']), note=V0['rev_guid_note'])
    S('cal_pre', '  Net sales before revenue calibration (Q3/Q4-26E helper)', 'line', 'm1',
      qe=lambda: '=' + '+'.join(f'{P(k)}*(1+{V(k + "_pre")})' for k in LINES))
    S('cal_sens', '  Net sales sensitivity to +1.00 of growth (Q3/Q4-26E helper)', 'line', 'm1', qe=lambda: '=' + '+'.join(P(k) for k in LINES))
    S('cal_g', '  Outlook calibration: Δ y/y growth applied to all end-market lines (Q3/Q4-26E)', 'driver', 'pct',
      qe=lambda: (f'=({V("cal_guid", E26)}-{Q1}{R["g_rev"]}-{Q2}{R["g_rev"]}-{Q3}{R["cal_pre"]}-{Q4}{R["cal_pre"]})/({Q3}{R["cal_sens"]}+{Q4}{R["cal_sens"]})'
                  if CTX.col.q == 3 else f'={Q3v("cal_g")}'),
      note='Solves the uniform growth shift (vs 1H/26 y/y rates) so that FY26 net sales = the FY26 guidance end-point for the active scenario.')
    S('cal_rev_chk', '  Check: FY26 net sales vs guidance end-point (should be 0)', 'check', 'm1', e26=lambda: f'=ROUND({V("g_rev")}-{V("cal_guid")},1)')
    S('cal_eb', '  Memo: FY26 Adjusted EBITDA guidance (scenario end-point)', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_ebitda']), note=V0['eb_guid_note'])
    S('cal_eb_pre', '  Adjusted EBITDA before margin calibration (Q3/Q4-26E helper)', 'line', 'm1', qe=lambda: f'={V("is_rev")}*{V("g_adjm_pre")}')
    S('cal_m', '  Outlook calibration: Δ Adjusted EBITDA margin (Q3/Q4-26E)', 'driver', 'pct',
      qe=lambda: (f'=({V("cal_eb", E26)}-{Q1}{R["g_adj"]}-{Q2}{R["g_adj"]}-{Q3}{R["cal_eb_pre"]}-{Q4}{R["cal_eb_pre"]})/({Q3}{R["is_rev"]}+{Q4}{R["is_rev"]})'
                  if CTX.col.q == 3 else f'={Q3v("cal_m")}'),
      note='Solves the uniform margin shift so that FY26 Adjusted EBITDA = the guidance end-point for the active scenario.')
    S('cal_eb_chk', '  Check: FY26 Adjusted EBITDA vs guidance end-point (should be 0)', 'check', 'm1', e26=lambda: f'=ROUND({V("g_adj")}-{V("cal_eb")},1)')
    S('cal_ni', '  Memo: FY26 net income guidance (scenario end-point) — model net income − guidance shown in the next row', 'memo', 'm1',
      e26=lambda: '=' + CH(SC['out_ni']), note='Not calibrated: net income follows from the guided D&A, interest and the tax-rate point estimate.')
    S('cal_ni_d', '  Model FY26 net income − guidance end-point (information; not forced to 0)', 'memo_calc', 'm1', e26=lambda: f'={V("is_ni")}-{V("cal_ni")}')
    S('cal_eps', '  Memo: FY26 Adjusted EPS guidance (scenario end-point, $)', 'eps_memo', 'ps', e26=lambda: '=' + CH(SC['out_eps']))
    S('cal_eps_d', '  Model FY26 Adjusted EPS − guidance end-point ($; information)', 'eps_memo', 'ps', e26=lambda: f'={V("e_eps")}-{V("cal_eps")}')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers & D&A', 'block', note='COST DRIVERS — inputs that drive forecast cost lines (Q3/Q4-26E: FY26 guidance point estimates less 1H/26)')
    S('d_dep', '  Depreciation', 'line', 'm1', data='dep', flow=True,
      qe=lambda: f'=({PT("pt_dep")}-{H1("d_dep")})/2', e26=lambda: S26('d_dep'), ae=lambda: f'={V("is_rev")}*{V("d_dep_pct")}',
      note='Q3/Q4-26E: FY26 guidance (~$15m) less 1H/26, split evenly. 2027E+: net sales × depreciation %.')
    S('d_dep_pct', '  Depreciation % of net sales', 'pct', 'pct', all=ratio('d_dep', 'is_rev'), ae_in=V0['dep_pct'])
    S('d_amort', '  Amortization of intangible & other long-term assets', 'line', 'm1', data='amort', flow=True,
      qe=lambda: f'=({PT("pt_amort")}-{H1("d_amort")})/2', e26=lambda: S26('d_amort'),
      ae=lambda: f'={V("d_amort_sch")}+N({V("m_amort")})',
      note='Q3/Q4-26E: FY26 guidance (~$65m) less 1H/26. 2027E+: existing-intangibles schedule (row below) + future-acquisition amortization. Charged mostly to SG&A (2025: $34.2m of $38.5m).')
    S('d_amort_sch', '  Amortization schedule — intangibles held at 30-Jun-2026 (input)', 'driver', 'm1', ae_in=V0['amort_sched'], note=V0['amort_note'])
    S('d_sga', '  SG&A % of net sales (incl. amortization, SBC & integration costs in SG&A)', 'pct', 'pct', all=ratio('is_sga', 'is_rev'),
      qe=lambda: f'=IFERROR({H1("is_sga")}/{H1("is_rev")},"")', ae_in=V0['sga_pct'],
      note='Q3/Q4-26E at the 1H/26 ratio; 2027E+ input (operating leverage on fixed costs). Gross profit is implied: GAAP operating income (from Adjusted EBITDA) + SG&A + transaction & other items.')
    S('d_sbc', '  Stock-based compensation', 'line', 'm1', data='sbc', flow=True,
      qe=lambda: f'={H1("d_sbc")}/2', e26=lambda: S26('d_sbc'), ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}', note='Q3/Q4-26E at the 1H/26 run-rate; 2027E+: % of net sales.')
    S('d_sbc_pct', '  Stock-based compensation % of net sales', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_trans', '  Transaction expenses (acquisition deal costs)', 'line', 'm1', data='trans', flow=True,
      qe=lambda: f'=({PT("pt_trans")}-{H1("d_trans")})/2', e26=lambda: S26('d_trans'), ae=lambda: f'={V("m_spend")}*{V("d_trans_pct")}',
      note='Q3/Q4-26E: FY26 point estimate less 1H/26. 2027E+: % of acquisition spend (M&A lever).')
    S('d_trans_pct', '  Transaction expenses % of acquisition spend', 'pct', 'pct', ae_in=0.015)
    S('d_integ', '  Acquisition & facility integration costs', 'line', 'm1', data='integ', flow=True, qe_in={3: 0.5, 4: 0.5}, e26=lambda: S26('d_integ'), ae_in=2.0,
      note='Booked in cost of sales / SG&A; added back in Adjusted EBITDA. 1H/26 $0.5m (2025: $5.5m).')
    S('d_step', '  Recognition of inventory step-up (purchase accounting)', 'line', 'm1', data='stepup', flow=True, qe_in={3: 0.0, 4: 0.0}, e26=lambda: S26('d_step'), ae_in=0.0,
      note='LMB $4.5m and Harper $0.4m fully recognised in 1H/26 (Q2-26 10-Q). None forecast.')
    S('d_oth', '  Other (income) expense added back (contingent consideration, grants, insurance; expense = +)', 'line', 'm1', data='othadj', flow=True,
      qe_in={3: 0.0, 4: 0.0}, e26=lambda: S26('d_oth'), ae_in=0.0)
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF INCOME (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (operating income = Adjusted EBITDA − D&A − EBITDA adjusting items; gross profit implied)')
    S('is_rev', 'Net sales', 'total', 'm1', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the end-market build.')
    S('is_cogs', 'Cost of sales', 'line', 'm1', data='cogs', flow=True, fc=lambda: f'={V("is_rev")}-{V("is_gp")}')
    S('is_gp', 'Gross profit', 'line_b', 'm1', hist=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_rev")}-{V("is_cogs")},"")',
      fc=lambda: f'={V("is_op")}+{V("is_sga")}+{V("is_trans")}-{V("is_othinc")}',
      note='Forecast = operating income + SG&A + transaction expenses − other income (implied by the Adjusted EBITDA build).')
    S('is_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('is_sga', 'Selling, general & administrative expenses', 'line', 'm1', data='sga', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_sga")}')
    S('is_trans', 'Transaction expenses', 'line', 'm1', data='trans', flow=True, fc=lambda: f'={V("d_trans")}')
    S('is_othinc', 'Other income (expense), net (income = +)', 'line', 'm1', data='othinc', flow=True, fc=lambda: f'=-{V("d_oth")}',
      note='AMJP grants 2020–23, CAV contingent-consideration release & DAC insurance 2024 (income); Harper contingent consideration Q2-26 (expense).')
    S('is_op', 'Operating income', 'total', 'm1', data='op', flow=True,
      fc=lambda: f'={V("g_adj")}-{V("d_dep")}-{V("d_amort")}-({V("d_step")}+{V("d_oth")}+{V("d_trans")}+{V("d_sbc")}+{V("d_integ")})',
      note='Historical as reported (FY2012–21: prospectus EBITDA reconciliation). Forecast = Adjusted EBITDA − D&A − EBITDA adjusting items.')
    S('is_opm', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('is_int', 'Interest expense, net', 'line', 'm1', data='int', flow=True,
      qe=lambda: f'=({PT("pt_int")}-{H1("is_int")})/2',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_fac")}*{V("ds_r_fac")}-{P("cf_end")}*{V("ds_r_cash")}',
      note='Q3/Q4-26E: FY26 guidance (~$80m) less 1H/26, split evenly. 2027E+ = rate × opening term loans + rate × other debt − yield × opening cash (no circularity). Includes debt-cost amortization.')
    S('is_refi', 'Refinancing costs / loss on debt extinguishment & other non-operating items', 'line', 'm1', data='refi', flow=True, qe_in={3: 0.0, 4: 0.0}, ae_in=0.0,
      note='2024: write-off of unamortized debt costs on the IPO / follow-on term-loan repayments ($1.6m Q2, $4.8m Q4). 2016–17: loss on extinguishment; 2015–16 FX / insurance gains.')
    S('is_ebt', 'Income before income taxes', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_op")}),{V("is_op")}-{V("is_int")}-N({V("is_refi")}),"")')
    S('is_tax', 'Income tax provision (benefit)', 'line', 'm1', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Pre-IPO rates are not meaningful (LLC structure, valuation allowances). Q3/Q4-26E: point estimate (1H/26 23.9%). 2027E+ input.')
    S('is_ni', 'Net income (loss)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_ni_chk', '  Check: net income vs reported (should be 0; ±0.01 rounding)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=0.015,0,ROUND({V("is_ni")}-{V("is_ni_pub")},2)),"")')
    S('is_ni_pub', '  Memo: net income (loss) as reported', 'memo', 'm1', data='ni', flow=True)
    S('is_dda', '  Memo: depreciation & amortization (total)', 'memo_calc', 'm1', all=lambda: f'=IF(ISNUMBER({V("d_dep")}),{V("d_dep")}+{V("d_amort")},"")')
    S('is_sbc', '  Memo: stock-based compensation', 'memo_calc', 'm1', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share — common shares from the April-2024 IPO; pre-IPO LLC units not meaningful)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_basic', avg=True,
      qe=lambda: f'=${Q2}${R["sh_basic"]}+${E26}${R["bb_iss"]}*{0.25 if CTX.col.q == 3 else 0.75}-${E26}${R["bb_sh"]}*{0.25 if CTX.col.q == 3 else 0.75}',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q3/Q4-26E: Q2/26 + equity-plan issuance − 2H/26 buybacks phased (¼ in Q3, ¾ in Q4). 2027E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_dil', avg=True,
      qe=lambda: f'={V("sh_basic")}+(${Q2}${R["sh_dil"]}-${Q2}${R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_basic', 'EPS – basic ($)', 'eps', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_basic")}),IFERROR({V("is_ni")}/{V("sh_basic")},""),"")')
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")',
      note='Net income / weighted diluted shares (may differ by ±$0.01 vs reported). FY2024 weighting as published (IPO 29-Apr-2024).')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($)', 'eps_memo', 'ps', data='eps_dil')
    S('dps', '  Dividends declared per share ($)', 'line', 'ps', qe_in={3: 0.0, 4: 0.0}, ae_in=0.0,
      note='Loar has not paid and does not anticipate paying regular cash dividends (10-K); free cash flow funds acquisitions and debt reduction.')
    blank()

    # ------------------------------------------------------------------ RECON 1: EBITDA
    S('sec_r1', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (company definition, as published)', 'section',
      note='ADJUSTED EBITDA — per Loar release Table 4 / prospectus reconciliations (net income + interest + refinancing + tax = operating income; + D&A = EBITDA; + adjustments)')
    S('r_ni', 'Net income (loss) (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('r_tax', '  (+) Income tax provision (benefit)', 'line', 'm1', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest expense, net', 'line', 'm1', all=lambda: f'={V("is_int")}')
    S('r_refi', '  (+) Refinancing costs / loss on extinguishment (− FX & insurance gains, 2015–16)', 'line', 'm1', all=lambda: f'=N({V("is_refi")})')
    S('r_op', '  = Operating income', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_tax")}+{V("r_int")}+{V("r_refi")},"")')
    S('r_dep', '  (+) Depreciation', 'line', 'm1', all=lambda: f'={V("d_dep")}')
    S('r_amort', '  (+) Amortization (intangible & other long-term assets)', 'line', 'm1', all=lambda: f'={V("d_amort")}')
    S('r_ebitda', '  = EBITDA', 'total', 'm1', all=lambda: f'=IF(AND(ISNUMBER({V("r_op")}),ISNUMBER({V("r_dep")})),{V("r_op")}+{V("r_dep")}+{V("r_amort")},"")')
    S('r_ebitda_pub', '  Memo: EBITDA as published', 'memo', 'm1', data='ebitda_pub', flow=True)
    S('r_ebitda_chk', '  Check: model EBITDA vs published (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_ebitda_pub")}),IF(ABS({V("r_ebitda")}-{V("r_ebitda_pub")})<=0.015,0,ROUND({V("r_ebitda")}-{V("r_ebitda_pub")},2)),"n/p")')
    S('r_step', '  (+) Recognition of inventory step-up', 'line', 'm1', all=lambda: f'={V("d_step")}')
    S('r_oth', '  (+/−) Other (income) expense (grants, contingent consideration, insurance; 2017–21 asset write-offs)', 'line', 'm1', all=lambda: f'={V("d_oth")}')
    S('r_trans', '  (+) Transaction expenses', 'line', 'm1', all=lambda: f'={V("d_trans")}')
    S('r_sbc', '  (+) Stock-based compensation', 'line', 'm1', all=lambda: f'={V("d_sbc")}')
    S('r_integ', '  (+) Acquisition & facility integration costs', 'line', 'm1', all=lambda: f'={V("d_integ")}')
    S('r_covid', '  (+) COVID-19 related expenses (2020–22)', 'line', 'm1', data='covid', flow=True, fc=lambda: '=0')
    S('r_msa', '  (+) Management service agreement fees (2012–17)', 'line', 'm1', data='msa', flow=True, fc=lambda: '=0')
    S('r_tot', '  Total adjusting items (= "gross adjustments to EBITDA")', 'line_b', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{nsum(["r_step", "r_oth", "r_trans", "r_sbc", "r_integ", "r_covid", "r_msa"])},"")')
    S('r_adj', '  = Adjusted EBITDA (model bridge)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{V("r_ebitda")}+{V("r_tot")},"")',
      note='Rebuilt from the published reconciliation lines; forecast = EBITDA + forecast adjusting items (equals the end-market build — check in the Group block).')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_adj_pub', '  Company-published Adjusted EBITDA', 'memo', 'm1', data='adj_pub', flow=True)
    S('r_adj_chk', '  Check: model bridge vs company-published (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_adj_pub")}),IF(ABS({V("r_adj")}-{V("r_adj_pub")})<=0.015,0,ROUND({V("r_adj")}-{V("r_adj_pub")},2)),"n/p")')
    S('r_def', '  Definition basis (company Adjusted EBITDA definition in force)', 'text', 'gen',
      note='Definition changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('r_ebit_h', 'To adjusted EBITA / EBIT:', 'sub', 'gen')
    S('r_depn', '  (−) Depreciation', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_dep")}),-{V("r_dep")},"")')
    S('r_ebita', '  = Adjusted EBITA (Adjusted EBITDA − depreciation; pre-amortization operating profit)', 'line_b', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+{V("r_depn")},"")')
    S('r_amortn', '  (−) Amortization', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_amort")}),-{V("r_amort")},"")')
    S('r_ebit', '  = Adjusted EBIT (model; Adjusted EBITDA − D&A)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ebita")}),{V("r_ebita")}+{V("r_amortn")},"")',
      note='Used for NOPAT / ROIC and the DCF (amortization of acquired intangibles deducted, so returns are on a full-cost basis).')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: operating income -> adjusted EBITA
    S('sec_r2', 'RECONCILIATION: GAAP OPERATING INCOME → ADJUSTED OPERATING INCOME (ADJUSTED EBITA, model definition)', 'section',
      note='ADJUSTED OPERATING INCOME — model bridge on the company items: GAAP operating income + amortization + EBITDA adjusting items (Loar does not publish an adjusted operating income)')
    S('o_op', 'Operating income (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_op")}')
    S('o_amort', '  (+) Amortization of intangible & other long-term assets', 'line', 'm1', all=lambda: f'={V("d_amort")}')
    S('o_items', '  (+) EBITDA adjusting items (step-up, other, transaction, SBC, integration, COVID, MSA)', 'line', 'm1', all=lambda: f'={V("r_tot")}')
    S('o_adj', '  = Adjusted operating income / Adjusted EBITA (model)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_amort")}+{V("o_items")},"")')
    S('o_adj_m', '  Adjusted operating (EBITA) margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_chk', '  Check: Adjusted EBITA + depreciation vs company-published Adjusted EBITDA (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("r_adj_pub")}),ISNUMBER({V("o_adj")})),IF(ABS({V("o_adj")}+{V("d_dep")}-{V("r_adj_pub")})<=0.015,0,ROUND({V("o_adj")}+{V("d_dep")}-{V("r_adj_pub")},2)),"n/p")')
    S('o_adj_g', '  Adjusted EBITA y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental Adjusted EBITA margin (Δ adjusted EBITA / Δ net sales)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: GAAP NET INCOME / DILUTED EPS → ADJUSTED NET INCOME → ADJUSTED EPS (current company definition)', 'section',
      note='ADJUSTED EPS — current definition (from the Q1-26 release): + refinancing costs + gross adjustments to EBITDA + amortization of acquired intangibles, tax-effected; applied to all periods')
    S('e_ni', 'Net income (GAAP)', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("e_sh")}),{V("is_ni")},"")')
    S('e_refi', '  (+) Refinancing costs (pre-tax)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("e_sh")}),N({V("is_refi")}),"")')
    S('e_gross', '  (+) Gross adjustments to EBITDA (pre-tax; as in the Adjusted EBITDA bridge)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("e_sh")}),{V("r_tot")},"")')
    S('e_amort', '  (+) Amortization of acquired intangible assets (pre-tax)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("e_sh")}),{V("d_amort")},"")')
    S('e_tax', '  (−) Tax adjustment', 'line', 'm1', data='e_tax', flow=True,
      fc=lambda: f'=-({V("e_refi")}+{V("e_gross")}-{V("d_sbc")}-{V("d_trans")}+{V("e_amort")})*{V("e_rate")}',
      note=('Historical: published current-definition tax adjustment (Q1-25, Q2-25 restated; Q1-26, Q2-26); other periods = published prior-definition tax '
            'adjustment + amortization × tax rate on amortization (row below). Forecast: (adjustments excl. SBC and transaction costs, which the company treats '
            'as non-deductible in the applicable rate) × tax rate.'))
    S('e_adjni', '  = Adjusted net income (model bridge)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("e_sh")}),{V("e_ni")}+{V("e_refi")}+{V("e_gross")}+{V("e_amort")}+{V("e_tax")},"")')
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted EPS – diluted ($) (model bridge, current definition)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published Adjusted EPS – current definition ($)', 'eps_memo', 'ps', data='e_pub')
    S('e_chk', '  Check: model vs company-published, current definition (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(ISNUMBER({V("e_pub")}),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0101,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_rate', '  Tax rate applied to adjustments (forecast) / on the amortization add-back (historical)', 'pct', 'pct',
      hist=lambda: (f'=IF(ISNUMBER({V("e_rate_imp")}),{V("e_rate_imp")},IF(ISNUMBER({V("e_rate_in")}),{V("e_rate_in")},""))'),
      qe=lambda: f'={PT("pt_etr")}', ae=lambda: f'={V("is_etr")}',
      note='Historical: implied by the restated tables (Q1-25 20.2%, Q2-25 20.2%) or input (2024 24%, 2H-25 20.2%). Forecast: GAAP effective tax rate.')
    S('e_rate_imp', '    Implied tax rate on amortization (current − prior definition tax adjustment ÷ amortization)', 'memo', 'pct', data='e_amort_rate')
    S('e_rate_in', '    Input: tax rate on amortization (prior-definition periods)', 'memo', 'pct', data='e_amort_rate_in')
    S('e_def', '  Definition basis (company Adjusted EPS definition in force when published)', 'text', 'gen')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_old_h', '  Prior definition (published Q2-24 – Q4-25; amortization not added back):', 'sub', 'gen')
    S('e_tax_old', '    Tax adjustment — prior definition (as published)', 'memo', 'm1', data='e_tax_old', flow=True)
    S('e_eps_old', '    Adjusted EPS – prior definition (model = NI + refinancing + gross adjustments + prior tax adjustment)', 'eps_memo', 'ps',
      hist=lambda: f'=IF(ISNUMBER({V("e_tax_old")}),({V("e_ni")}+{V("e_refi")}+{V("e_gross")}+{V("e_tax_old")})/{V("e_sh")},"")')
    S('e_pub_old', '    Company-published Adjusted EPS – prior definition ($, as originally reported)', 'eps_memo', 'ps', data='e_pub_old')
    S('e_chk_old', '    Check: model vs published, prior definition (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(ISNUMBER({V("e_pub_old")}),IF(ABS({V("e_eps_old")}-{V("e_pub_old")})<=0.0101,0,ROUND({V("e_eps_old")}-{V("e_pub_old")},2)),"n/p")')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Net sales y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_org', '  Organic growth %', 'growth', 'pct', all=lambda: f'={V("a_org_g")}' if CTX.col.prior else None)
    S('gm_oem', '  Total OEM net sales y/y %', 'growth', 'pct', all=growth('mx_oem'))
    S('gm_am', '  Total aftermarket net sales y/y %', 'growth', 'pct', all=growth('mx_am'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating income (GAAP) y/y %', 'growth', 'pct', all=growth('is_op'))
    S('gm_ni', '  Net income y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_inc', '  Incremental Adjusted EBITDA margin (ΔEBITDA / ΔNet sales)', 'pct', 'pct', all=incr('r_adj', 'is_rev'))
    S('gm_adjop_m', '  Adjusted EBITA margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP operating income) %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_sga', '  SG&A % of net sales', 'pct', 'pct', all=ratio('is_sga', 'is_rev'))
    blank()
