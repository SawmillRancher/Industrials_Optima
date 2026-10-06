"""Row specification of the DHR Model sheet, part 1 (MLM template layout and process): segment build, Masimo / StatLab,
future M&A, group total & FY26 outlook calibration, disclosures, cost drivers, income statement, GAAP → adjusted bridges."""
from fw import *

SCN = '$CF$2'
def CH(r):
    return f'CHOOSE(MATCH({SCN},{{"Bull","Base","Bear"}},0),$CO${r},$CP${r},$CQ${r})'
def PT(name): return f'$CP${SC[name]}'
SC = {}

def growth(key):
    def f():
        c = CTX.col
        if c.prior is None: return None
        return f'=IF(AND(ISNUMBER({V(key)}),ISNUMBER({P(key)})),IFERROR({V(key)}/{P(key)}-1,""),"")'
    return f
def ratio(n, d): return lambda: f'=IF(AND(ISNUMBER({V(n)}),ISNUMBER({V(d)})),IFERROR({V(n)}/{V(d)},""),"")'
def incr(n, d):
    def f():
        if CTX.col.prior is None: return None
        return f'=IFERROR(({V(n)}-{P(n)})/({V(d)}-{P(d)}),"")'
    return f
def nsum(keys): return '+'.join(f'N({V(k)})' for k in keys)
def BYv(key): return f'$BY${R[key]}'
def isq(): return CTX.col.q is not None

SEGS = [('bio', 'Biotechnology', 'Biotechnology (bioprocessing — Cytiva, Pall Biotech; discovery & medical — Aldevron, Abcam reagents to 2024 in Life Sciences)'),
        ('ls', 'Life Sciences', 'Life Sciences (Beckman Coulter Life Sciences, Leica Microsystems, SCIEX, Molecular Devices, IDT, Abcam, Aldevron, Pall Industrial)'),
        ('dx', 'Diagnostics', 'Diagnostics (Beckman Coulter Diagnostics, Radiometer, Leica Biosystems, Cepheid; Masimo from 10-Jun-2026)')]
LEGACY = [('lsd', 'Life Sciences & Diagnostics (to 2014)'), ('eas', 'Environmental & Applied Solutions (2015 – Q2/23; Veralto spun 30-Sep-2023)'),
          ('env', 'Environmental (to 2014)'), ('dental', 'Dental (to Q3/19; Envista split-off Dec-2019)'), ('tm', 'Test & Measurement (to Q2/16; Fortive)'),
          ('it', 'Industrial Technologies (to Q2/16; Fortive)'), ('pi', 'Professional Instrumentation (to 2008)'), ('mt', 'Medical Technologies (to 2008)'),
          ('tc', 'Tools & Components (to 2008)'), ('apex', 'Businesses contributed to the Apex Tool JV (2010–12)')]
LINES = [s for s, _, _ in SEGS]

# ====================================================================== scenario table (CN:CR)
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of FY26 guidance ranges.'))
    r = 11
    SCEN_ROWS.append((r, 'out_hdr', V0['out_hdr'], 'High', 'Mid', 'Low', V0['out_note']))
    r += 1
    for key, lab, (hi, mid, lo), nf, note in V0['outlook']:
        SC[key] = r; SCEN_ROWS.append((r, 'out', lab, hi, mid, lo, note, nf)); r += 1
    r = max(r + 1, 16)
    SCEN_ROWS.append((r, 'pt_hdr', 'FY26 point estimates (all cases)', None, None, None, None)); r += 1
    for key, lab, vals, nf, note in V0['points']:
        SC[key] = r
        if isinstance(vals, tuple): SCEN_ROWS.append((r, 'out', lab, vals[0], vals[1], vals[2], note, nf))
        else: SCEN_ROWS.append((r, 'pt', lab, None, vals, None, note, nf))
        r += 1
    r = max(r + 1, 30)
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
    # ------------------------------------------------------------------ SEGMENT BUILD
    S('sec_pl', 'SEGMENT P&L — BIOTECHNOLOGY · LIFE SCIENCES · DIAGNOSTICS (+ MASIMO · STATLAB) · CORE GROWTH BRIDGE', 'section',
      note='SEGMENT BUILD — modelling logic (prior-year sales × (1 + core growth + FX) → segment sales × adjusted operating margin → adjusted operating profit → adjusted EPS)')
    blank()
    for s, lab, title in SEGS:
        dxn = ' (legacy, ex Masimo & StatLab)' if s == 'dx' else ''
        S(f'{s}_hdr', title, 'block', note=f'{lab.upper()} — modelling logic')
        S(f'{s}_rev', f'  {lab} sales{dxn}', 'line_b', 'm', data=f'sg_{s}_sales_l', flow=True,
          qe=lambda s=s: f'={P(s + "_rev")}*(1+{V(s + "_core")}+{V(s + "_fx")})',
          ae=lambda s=s: f'={P(s + "_rev")}*(1+{V(s + "_core")})',
          note=('Segment sales as reported (hybrid recast basis: periods before a segment recast / spin-off on the restated comparatives). '
                'Q3/Q4-26E: prior-year quarter × (1 + core growth + FX). 2027E+: prior year × (1 + scenario core growth); FX nil.'
                + (' Diagnostics shown ex Masimo (from 10-Jun-2026) and StatLab — both modelled in their own blocks below.' if s == 'dx' else '')))
        S(f'{s}_rev_g', '    Sales y/y %', 'growth', 'pct', all=growth(f'{s}_rev'))
        S(f'{s}_core', '    Core sales growth % (non-GAAP, as published)', 'growth', 'pct', data=f'sg_{s}_core',
          qe=lambda s=s: f'={V(s + "_core_pre")}+{BYv("cal_g")}',
          ae=lambda s=s: '=' + CH(SC[f'{s.upper()}_CORE'][CTX.col.year]),
          note='Q3/Q4-26E: segment input (row below) + core-growth outlook calibration Δ (Group block). 2027E–2030E: scenario lever (Bull/Base/Bear table →).')
        S(f'{s}_core_pre', '    Q3/Q4-26E core growth input before outlook calibration', 'driver', 'pct',
          qe_in=V0['qe_core'][s], note=V0['qe_core_note'][s])
        S(f'{s}_acq', '    Acquisitions / divestitures contribution % (as published)', 'growth', 'pct', data=f'sg_{s}_acqc')
        S(f'{s}_fx', '    Currency contribution % (as published)', 'growth', 'pct', data=f'sg_{s}_fxc', qe_in=V0['qe_fx'], ae_in=0.0,
          note='Q3/Q4-26E: company FX guidance (Q3 ~−1.0%; FY ~+0.5% → Q4 implied). 2027E+: nil.')
        S(f'{s}_op', f'  {lab} operating profit (GAAP){dxn}', 'line', 'm', data=f'sg_{s}_op_profit_l', flow=True,
          fc=lambda s=s: f'={V(s + "_adjop")}-{V(s + "_amort")}-{V(s + "_oadj")}')
        S(f'{s}_opm', '    Operating margin (GAAP) %', 'pct', 'pct', all=ratio(f'{s}_op', f'{s}_rev'))
        S(f'{s}_amort', '    Amortization of acquired intangibles in segment', 'line', 'm', data=f'sg_{s}_amort', flow=True,
          fc=lambda s=s: f'={V("d_amort")}*{V(s + "_amsh")}',
          note='Segment amortization as published (segment note; 2024+). Forecast = existing-intangibles schedule × segment share (1H/26).')
        S(f'{s}_amsh', '    Segment share of amortization (existing intangibles) %', 'pct', 'pct',
          hist=lambda s=s: f'=IF(ISNUMBER({V(s + "_amort")}),IFERROR({V(s + "_amort")}/({V("bio_amort")}+{V("ls_amort")}+{V("dx_amort")}),""),"")',
          qe=lambda s=s: f'=IFERROR({H1(s + "_amort")}/({H1("bio_amort")}+{H1("ls_amort")}+{H1("dx_amort")}),"")',
          e26=lambda s=s: f'=$BY${R[s + "_amsh"]}', ae=lambda s=s: f'=$BY${R[s + "_amsh"]}')
        S(f'{s}_oadj', '    Other operating profit adjustments in segment (impairments, step-up, contingencies; company definition)', 'line', 'm',
          data=f'sg_{s}_other_adj', flow=True, qe_in={3: 0.0, 4: 0.0}, ae_in=0.0,
          note='Published by segment from the Q4-25 release (FY24, Q4-24, FY25, Q4-25); 2025–26 quarters allocated from the release footnotes (see comments). Blank = not disclosed by segment.')
        S(f'{s}_adjop', f'  {lab} adjusted operating profit (non-GAAP){dxn}', 'line_b', 'm', flow=True,
          hist=lambda s=s: f'=IF(AND(ISNUMBER({V(s + "_op")}),ISNUMBER({V(s + "_amort")})),{V(s + "_op")}+{V(s + "_amort")}+N({V(s + "_oadj")}),"")',
          fc=lambda s=s: f'={V(s + "_rev")}*{V(s + "_adjm")}',
          note='Company definition (Q4-25 release): operating profit + amortization of intangibles + other operating profit adjustments. Historical where segment amortization is disclosed (2024+). Forecast = sales × adjusted margin.')
        S(f'{s}_adjm', '    Adjusted operating margin %', 'pct', 'pct', all=ratio(f'{s}_adjop', f'{s}_rev'),
          qe=lambda s=s: f'={V(s + "_adjm_pre")}+{V("cal_m")}',
          ae=lambda s=s: '=' + CH(SC[f'{s.upper()}_OPM'][CTX.col.year]),
          note='Q3/Q4-26E: margin before calibration + outlook calibration Δ of the quarter (Group block: Q3 margin guidance, Q4 FY26 EPS guidance). 2027E–2030E: scenario lever.')
        S(f'{s}_adjm_pre', '    Adjusted operating margin before outlook calibration % (Q3/Q4-26E helper)', 'pct', 'pct',
          qe=lambda s=s: f'={P(s + "_adjm")}+({H1(s + "_adjop")}/{H1(s + "_rev")}-{H1(s + "_adjop", 2025)}/{H1(s + "_rev", 2025)})',
          note='Prior-year quarter adjusted margin + (1H/26 − 1H/25 adjusted margin drift).')
        S(f'{s}_inc', '    Incremental adjusted operating margin (Δ adj. op. profit / Δ sales)', 'pct', 'pct', all=incr(f'{s}_adjop', f'{s}_rev'))
        S(f'{s}_dep', '    Depreciation in segment', 'line', 'm', data=f'sg_{s}_dep', flow=True)
        blank()

    # ------------------------------------------------------------------ Masimo
    S('ms_hdr', 'Masimo (pulse oximetry & patient monitoring; acquired 10-Jun-2026 for ~$9.9bn EV; standalone operating company in Diagnostics)', 'block',
      note='MASIMO — modelling logic (standalone history from Masimo\'s own SEC filings; consolidated from closing)')
    S('ms_sa_rev', '  Memo: Masimo standalone sales (pre-acquisition; MASI filings, continuing operations)', 'memo', 'm', data='ms_sa_rev', flow=True,
      note='Masimo Corp. Forms 10-K / 10-Q (XBRL), continuing operations (consumer audio sold 2025); Q4 = FY − 9M. 2023 not on the recast basis (omitted).')
    S('ms_sa_g', '  Standalone sales growth y/y %', 'growth', 'pct', hist=growth('ms_sa_rev'))
    S('ms_sa_op', '  Memo: Masimo standalone operating income (GAAP, MASI filings)', 'memo', 'm', data='ms_sa_op', flow=True)
    S('ms_sa_m', '  Standalone operating margin (GAAP) %', 'pct', 'pct', hist=ratio('ms_sa_op', 'ms_sa_rev'))
    S('ms_pf', '  Pro forma Masimo sales (full period, standalone basis)', 'line', 'm', flow=True,
      hist=lambda: (f'={P("ms_sa_rev")}*(1+{PQ("ms_sa_g")})' if (CTX.col.year, CTX.col.q) == (2026, 2) else f'=IF(ISNUMBER({V("ms_sa_rev")}),{V("ms_sa_rev")},"")'),
      qe=lambda: f'={P("ms_sa_rev")}*(1+{V("ms_g")})', e26=lambda: S26('ms_pf'),
      ae=lambda: f'={P("ms_pf")}*(1+{V("ms_g")})+{V("ms_rsyn")}-{P("ms_rsyn")}',
      note='Q2/26 = Q2/25 standalone × (1 + Q1/26 standalone growth) (Masimo stopped filing after closing). Forecast = prior year × (1 + growth) + revenue synergies.')
    S('ms_g', '  Masimo sales growth % (standalone basis)', 'growth', 'pct', all=growth('ms_pf'), qe_in=V0['ms_g26'],
      ae=lambda: '=' + CH(SC['MS_G'][CTX.col.year]), note='Company: high-single-digit core growth long term (Feb-2026 deal release). Scenario lever 2027E+.')
    S('ms_rsyn', '  Revenue synergies (cumulative run-rate; >$50m by year 5)', 'line', 'm', e26_in=0.0, ae_in=V0['ms_rsyn'])
    S('ms_days', '  Days consolidated in period (closing 10-Jun-2026)', 'line', 'gen', data='ms_days', qe_in={3: 91, 4: 98}, e26=lambda: S26('ms_days'), ae_in=365)
    S('ms_rev', '  Masimo sales consolidated (in Diagnostics)', 'line_b', 'm', data='ms_rev', flow=True,
      qe=lambda: f'={V("ms_pf")}', ae=lambda: f'={V("ms_pf")}',
      note='Q2/26: sales contributed since closing (10-Q acquisition note). Q3/Q4-26E: pro forma quarter (full quarter consolidated). 2027E+: full year.')
    S('ms_m', '  Adjusted operating margin of Masimo (before purchase accounting & synergies) %', 'driver', 'pct', qe_in=V0['ms_m26'], e26=ratio('ms_adjop', 'ms_rev'),
      ae_in=V0['ms_m'], note=V0['ms_m_note'])
    S('ms_csyn', '  (+) Cost synergies realised (>$125m run-rate by year 5)', 'line', 'm', qe_in={3: 0.0, 4: 5.0}, ae_in=V0['ms_csyn'])
    S('ms_adjop', '  Masimo adjusted operating profit contribution', 'line_b', 'm', data='ms_adjop', flow=True,
      qe=lambda: f'={V("ms_rev")}*{V("ms_m")}+{V("ms_csyn")}', ae=lambda: f'={V("ms_rev")}*{V("ms_m")}+{V("ms_csyn")}',
      note='Q2/26: stub-period estimate (sales contributed × Q1/26 standalone operating margin + amortization add-back). Forecast = sales × margin + cost synergies.')
    S('ms_adjm', '  Adjusted operating margin incl. synergies %', 'pct', 'pct', all=ratio('ms_adjop', 'ms_rev'))
    S('ms_amort', '  (−) Amortization of Masimo acquired intangibles (within total amortization)', 'line', 'm', data='ms_amort', flow=True,
      qe=lambda: f'=$BX${R["ppa_int"]}/$BX${R["ppa_life"]}*{V("ms_days")}/365', ae=lambda: f'=$BX${R["ppa_int"]}/$BX${R["ppa_life"]}',
      note='Preliminary PPA intangibles ÷ weighted useful life (schedule block). Non-cash; added back in adjusted results.')
    S('ms_inv', '  (−) Inventory fair-value step-up & acquisition-related items expensed', 'line', 'm', data='ms_inv', flow=True,
      qe_in=V0['ms_inv'], ae_in=0.0, note=V0['ms_inv_note'])
    S('ms_ebitda', '  Memo: Masimo EBITDA (adjusted operating profit + D&A ex purchase accounting; company target >$530m in 2027)', 'memo', 'm',
      fc=lambda: f'={V("ms_adjop")}+{V("ms_rev")}*{V("ms_dap")}')
    S('ms_dap', '  Masimo depreciation % of sales (standalone)', 'driver', 'pct', qe_in={3: V0['ms_dep'], 4: V0['ms_dep']}, e26_in=V0['ms_dep'], ae_in=V0['ms_dep'])
    blank()

    # ------------------------------------------------------------------ StatLab
    S('st_hdr', 'StatLab (histology consumables; pending — Leica Biosystems / Diagnostics; ~$250m 2025 sales; closing assumed end-2026)', 'block',
      note='STATLAB — pending acquisition (announced Jul-2026, expected to close by end-2026); excluded from FY26 guidance')
    S('st_close', '  Closing assumed (1 = consolidated from 1-Jan-2027; purchase price paid in 2026E)', 'driver', 'gen', e26_in=1, ae_in=1,
      note='Company: expected to close by the end of 2026, subject to regulatory approvals. Set 2026E to 0 to exclude the deal.')
    S('st_pf', '  StatLab sales (pro forma, standalone)', 'line', 'm', e26_in=V0['st_rev26'], ae=lambda: f'={P("st_pf")}*(1+{V("st_g")})',
      note=V0['st_rev_note'])
    S('st_g', '  StatLab sales growth %', 'growth', 'pct', ae=lambda: '=' + CH(SC['ST_G'][CTX.col.year]), note='Company: high-single-digit core growth long term.')
    S('st_rev', '  StatLab sales consolidated (in Diagnostics)', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={V("st_pf")}*$CA${R["st_close"]}')
    S('st_m', '  Adjusted operating margin of StatLab %', 'driver', 'pct', e26_in=0.0, ae_in=V0['st_m'], note=V0['st_m_note'])
    S('st_adjop', '  StatLab adjusted operating profit contribution', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={V("st_rev")}*{V("st_m")}')
    S('st_amort', '  (−) Amortization of StatLab acquired intangibles', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR($CA${R["st_price"]}*{V("st_intp")}/{V("st_life")},0)*$CA${R["st_close"]}')
    S('st_price', '  Purchase price (enterprise value, cash; scenario-neutral input)', 'driver', 'm',
      e26=lambda: f'={V("st_pf")}*{V("st_mult")}*{V("st_close")}', note=V0['st_price_note'])
    S('st_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', e26_in=V0['st_mult'], note=V0['st_mult_note'])
    S('st_intp', '  Acquired intangibles % of price', 'driver', 'pct', e26_in=0.40, ae_in=0.40)
    S('st_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=15, ae_in=15)
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — bolt-ons, unallocated; deals closed from 2027E)', 'block',
      note='M&A LEVER — acquired sales = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', e26_in=0.0, ae_in=6.0,
      note='Danaher life-science / diagnostics deals: Abcam ~11x, Aldevron ~16x, Cytiva ~6x, Masimo ~6.5x sales; 6.0x input for bolt-ons.')
    S('m_acq_sales', '  Annualised sales acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.06)
    S('m_run', '  Run-rate sales of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Sales from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}',
      note='Mid-year convention: deals close evenly through the year (half a year of sales in year 1). Unallocated to segments.')
    S('m_m', '  Adjusted operating margin of acquired businesses %', 'driver', 'pct', e26_in=0.0, ae_in=0.25)
    S('m_adjop', '  Adjusted operating profit from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.05)
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.40,
      note='Danaher PPAs (Abcam, Aldevron, Cytiva): intangibles ~35–45% of consideration; balance mostly goodwill.')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=15)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)',
      note='Non-cash; added back in adjusted operating profit / adjusted EPS (company definition).')
    blank()

    # ------------------------------------------------------------------ corporate
    S('c_hdr', 'Other (unallocated corporate costs)', 'block', note='CORPORATE ("Other" segment)')
    S('c_op', '  Other / corporate operating profit (GAAP = adjusted)', 'line', 'm', data='sg_other_op_profit', flow=True,
      qe_in={3: V0['corp_q'], 4: V0['corp_q']}, ae=lambda: f'={V("is_rev")}*{V("c_pct")}',
      note='Company guidance: corporate expense ~$(90)m per quarter / ~$(360)m FY26. 2027E+: % of sales input.')
    S('c_pct', '  Corporate cost % of sales', 'pct', 'pct', hist=ratio('c_op', 'is_rev'), e26=ratio('c_op', 'is_rev'), ae_in=V0['c_pct'])
    blank()

    # ------------------------------------------------------------------ group total & outlook calibration
    S('g_hdr', 'Group Total — sales & adjusted operating profit (segment build) → FY26 outlook calibration', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Sales (segment build)', 'total', 'm',
      all=lambda: f'=IF({nsum(["bio_rev", "ls_rev", "dx_rev", "lg_rev"])}=0,"",{nsum(["bio_rev", "ls_rev", "dx_rev", "ms_rev", "st_rev", "m_rev", "lg_rev"])})',
      note='Σ Biotechnology + Life Sciences + Diagnostics (legacy) + Masimo + StatLab + future acquisitions (+ legacy segments in history).')
    S('g_adjop', 'Adjusted operating profit (segment build)', 'total', 'm',
      hist=lambda: None if CTX.col.year < 2024 else (f'=IF(AND(ISNUMBER({V("bio_adjop")}),ISNUMBER({V("ls_adjop")}),ISNUMBER({V("dx_adjop")}),ISNUMBER({V("c_op")}),N({V("lg_rev")})=0),'
                    f'{nsum(["bio_adjop", "ls_adjop", "dx_adjop", "ms_adjop"])}+{V("c_op")},"")'),
      fc=lambda: f'={nsum(["bio_adjop", "ls_adjop", "dx_adjop", "ms_adjop", "st_adjop", "m_adjop"])}+{V("c_op")}',
      note='Σ segment adjusted operating profit + Masimo + StatLab + future M&A + Other (corporate). Historical from 2024 (segment other adjustments published / allocated from FY24). Danaher\'s profit KPI (adjusted operating profit margin guided).')
    S('g_adjm', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('g_adjop', 'g_rev'))
    S('g_rev_g', '  Sales y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs consolidated sales (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=1.5,0,ROUND({V("g_rev")}-{V("is_rev")},1)),"")')
    S('g_chk_adj', '  Check: segment build vs adjusted operating profit bridge (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_adjop")}),ISNUMBER({V("o_adj")})),IF(ABS({V("g_adjop")}-{V("o_adj")})<=1.5,0,ROUND({V("g_adjop")}-{V("o_adj")},1)),"")')
    S('g_core', '  Core sales growth — total company % (published; model 2H/26E)', 'growth', 'pct', data='g_corec',
      qe=lambda: '=(' + '+'.join(f'{P(s + "_rev")}*{V(s + "_core")}' for s in LINES) + ')/(' + '+'.join(P(s + '_rev') for s in LINES) + ')',
      e26=lambda: f'=({Q("cal_core_d", 2026, 1)}+{Q("cal_core_d", 2026, 2)}+{Q("cal_core_d", 2026, 3)}+{Q("cal_core_d", 2026, 4)})/{Y("is_rev", 2025)}',
      ae=lambda: core_ae(),
      note='Historical as published. Q3/Q4-26E = legacy segment core growth (FX excluded). 2026E = Σ quarterly core-sales increments ÷ FY25 sales. 2027E+: Σ segment core growth (+ Masimo / StatLab organic growth once owned >1 year, i.e. from 2028E) ÷ prior-year sales.')
    S('g_acq', '  Acquisitions / divestitures contribution %', 'growth', 'pct', data='g_acqc')
    S('g_fx', '  Currency contribution %', 'growth', 'pct', data='g_fxc')
    S('cal_core_d', '  Core sales increment $ (core growth × prior-year quarter sales; helper)', 'line', 'm',
      hist=lambda: (f'=IF(AND(ISNUMBER({V("g_core")}),ISNUMBER({P("is_rev")})),{V("g_core")}*{P("is_rev")},"")' if (isq() and CTX.col.year == 2026) else None),
      qe=lambda: '=' + '+'.join(f'{P(s + "_rev")}*{V(s + "_core")}' for s in LINES))
    S('cal_guid', '  Memo: FY26 core sales growth guidance (scenario end-point)', 'memo', 'pct', e26=lambda: '=' + CH(SC['out_core']), note=V0['core_guid_note'])
    S('cal_sens', '  Core sales sensitivity to +1.00 of growth (Q3/Q4-26E helper; Σ prior-year segment sales)', 'line', 'm',
      qe=lambda: '=' + '+'.join(P(f'{s}_rev') for s in LINES))
    S('cal_g', '  Outlook calibration: Δ core growth applied to all segments (Q3/Q4-26E)', 'driver', 'pct',
      qe=lambda: ((f'=($CA${R["cal_guid"]}*{Y("is_rev", 2025)}-BW{R["cal_core_d"]}-BX{R["cal_core_d"]}-('
                   + '+'.join(f'{Q(s + "_rev", 2025, 3)}*BY{R[s + "_core_pre"]}+{Q(s + "_rev", 2025, 4)}*BZ{R[s + "_core_pre"]}' for s in LINES)
                   + f'))/(BY{R["cal_sens"]}+BZ{R["cal_sens"]})') if CTX.col.q == 3 else f'=$BY${R["cal_g"]}'),
      note='Solves the uniform core-growth shift (vs the segment inputs) so that FY26 core sales growth = the guidance end-point of the active scenario.')
    S('cal_core_chk', '  Check: FY26 core growth vs guidance end-point (should be 0.0%)', 'check', 'pct',
      e26=lambda: f'=ROUND({V("g_core")}-{V("cal_guid")},4)')
    S('cal_eps', '  Memo: FY26 adjusted diluted EPS guidance (scenario end-point, $)', 'eps_memo', 'ps', e26=lambda: '=' + CH(SC['out_eps']), note=V0['eps_guid_note'])
    S('cal_ni', '  Required FY26 adjusted net earnings = guidance × FY26 diluted shares (ex StatLab)', 'line', 'm', e26=lambda: f'={V("cal_eps")}*{V("e_sh")}')
    S('cal_adj_pre', '  Adjusted operating profit before margin calibration (Q3/Q4-26E helper)', 'line', 'm',
      qe=lambda: '=' + '+'.join(f'{V(s + "_rev")}*{V(s + "_adjm_pre")}' for s in LINES) + f'+{V("ms_adjop")}+{V("c_op")}')
    S('cal_adj_req', '  Required 2H/26 adjusted operating profit (given interest, other income, tax)', 'line', 'm',
      qe=lambda: ((f'=({V("cal_ni", "CA")}-BW{R["e_adjni"]}-BX{R["e_adjni"]})/(1-{PT("pt_etr")})'
                   f'+BY{R["is_intexp"]}+BZ{R["is_intexp"]}-BY{R["is_intinc"]}-BZ{R["is_intinc"]}-BY{R["e_nonop_x"]}-BZ{R["e_nonop_x"]}') if CTX.col.q == 3 else None),
      note='Required 2H adjusted net earnings ÷ (1 − adjusted tax rate) + net interest − adjusted other income: adjusting items are excluded on both sides.')
    S('cal_m', '  Outlook calibration: Δ adjusted operating margin applied to the three segments (Q3: Q3 margin guidance; Q4: FY26 EPS guidance)', 'driver', 'pct',
      qe=lambda: ((f'=({PT("pt_q3m")}*{V("is_rev")}-{V("cal_adj_pre")})/(' + '+'.join(V(s + '_rev') for s in LINES) + ')') if CTX.col.q == 3 else
                  (f'=(BY{R["cal_adj_req"]}-BY{R["g_adjop"]}-{V("cal_adj_pre")})/(' + '+'.join(V(s + '_rev') for s in LINES) + ')')),
      note='Q3/26E: uniform adjusted-margin shift (vs prior-year quarter + 1H drift) so that the Q3 adjusted operating margin = company Q3 guidance (~26.5%). Q4/26E: shift so that FY26 adjusted EPS = the guidance end-point of the active scenario.')
    S('cal_eps_chk', '  Check: FY26 adjusted EPS vs guidance end-point (should be 0.00)', 'check', 'ps', e26=lambda: f'=ROUND({V("e_eps")}-{V("cal_eps")},2)')
    S('cal_q3m', '  Memo: Q3/26 adjusted operating profit margin — company guidance (~26.5%)', 'memo', 'pct', qe=lambda: f'={PT("pt_q3m")}' if CTX.col.q == 3 else None,
      note='Q2-26 release, Non-GAAP forward-looking information: three-month period ending 25-Sep-2026 adjusted operating profit margin ~26.5%.')
    S('cal_q3m_chk', '  Check: Q3/26E adjusted operating margin vs guidance (should be 0.0%)', 'check', 'pct',
      qe=lambda: f'=ROUND({V("o_adj_m")}-{V("cal_q3m")},4)' if CTX.col.q == 3 else None)
    blank()

    # ------------------------------------------------------------------ legacy segments & disclosures
    S('lg_hdr', 'Legacy reportable segments (as reported; memo) & other disclosures', 'block', note='DISCLOSURES — historical only (not forecast)')
    S('lg_rev', '  Legacy segments — sales not in the current three-segment structure (Σ rows below)', 'line', 'm', flow=True,
      hist=lambda: '=' + '+'.join(f'N({V("lg_" + k + "_rev")})' for k, _ in LEGACY), fc=lambda: None)
    for k, lab in LEGACY:
        S(f'lg_{k}_rev', f'    {lab} — sales', 'memo', 'm', data=f'sg_{k}_sales_l', flow=True, group=True)
        S(f'lg_{k}_op', f'    {lab} — operating profit', 'memo', 'm', data=f'sg_{k}_op_profit_l', flow=True, group=True)
    S('lg_seg_chk', '  Check: Σ segment operating profit + Other vs consolidated operating profit (should be 0)', 'check', 'm1',
      hist=lambda: (f'=IF(ISNUMBER({V("c_op")}),IF(ABS(N({V("bio_op")})+N({V("ls_op")})+N({V("dx_op")})+N({V("ms_op_l")})+'
                    + '+'.join(f'N({V("lg_" + k + "_op")})' for k, _ in LEGACY) + f'+{V("c_op")}-{V("is_op")})<=1.5,0,ROUND(N({V("bio_op")})+N({V("ls_op")})+N({V("dx_op")})+N({V("ms_op_l")})+'
                    + '+'.join(f'N({V("lg_" + k + "_op")})' for k, _ in LEGACY) + f'+{V("c_op")}-{V("is_op")},1)),"")'))
    S('ms_op_l', '  Masimo operating profit in Diagnostics as reported (stub; reported Diagnostics − legacy)', 'memo', 'm', data='ms_op_l', flow=True)
    S('dx_rep', '  Diagnostics segment sales as reported (legacy + Masimo + StatLab)', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("dx_rev")}),{V("dx_rev")}+N({V("ms_rev")})+N({V("st_rev")}),"")')
    S('resp', '  Cepheid respiratory testing sales (~, as published)', 'memo', 'm', data='resp_sales', flow=True)
    S('core_xr', '  Core sales growth excl. respiratory testing % (as published)', 'growth', 'pct', data='core_ex_resp_c')
    S('recur', '  Recurring revenue % of sales (company / revenue note)', 'pct', 'pct', data='recurring')
    S('employees', '  Employees (year end, 10-K)', 'memo', 'm', data='employees', annual_only=True)
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers & D&A', 'block', note='COST DRIVERS — inputs that drive forecast cost lines')
    S('d_dep', '  Depreciation', 'line', 'm', data='cf_dep', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_dep_pct")}', note='Forecast = sales × depreciation %.')
    S('d_dep_pct', '  Depreciation % of sales', 'pct', 'pct', hist=ratio('d_dep', 'is_rev'),
      qe=lambda: f'=IFERROR({H1("d_dep")}/{H1("is_rev")},"")', e26=ratio('d_dep', 'is_rev'), ae_in=V0['dep_pct'])
    S('d_amort', '  Amortization of existing intangibles (schedule, ex Masimo / StatLab / future M&A)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("is_amort")}),{V("is_amort")}-N({V("ms_amort")}),"")',
      qe=lambda: (f'={PT("pt_amq3")}-{V("ms_amort")}' if CTX.col.q == 3 else f'={PT("pt_am")}-{H1("is_amort")}-{PT("pt_amq3")}-{V("ms_amort")}'),
      ae_in=V0['amort_sched'], note=V0['amort_note'])
    S('d_sga', '  SG&A excl. other operating profit adjustments % of sales', 'pct', 'pct',
      hist=lambda: f'=IF(ISNUMBER({V("is_sga")}),IFERROR(({V("is_sga")}-N({V("o_oth")}))/{V("is_rev")},""),"")',
      qe=lambda: f'=IFERROR(({H1("is_sga")}-{H1("o_oth")})/{H1("is_rev")},"")', e26=lambda: f'=IFERROR(({V("is_sga")}-{V("o_oth")})/{V("is_rev")},"")',
      ae_in=V0['sga_pct'], note='Other operating profit adjustments (impairments, Masimo acquisition items, contingencies) are booked in SG&A (company footnote).')
    S('d_rnd', '  R&D % of sales', 'pct', 'pct', hist=ratio('is_rnd', 'is_rev'),
      qe=lambda: f'=IFERROR({H1("is_rnd")}/{H1("is_rev")},"")', e26=ratio('is_rnd', 'is_rev'), ae_in=V0['rnd_pct'])
    S('d_sbc', '  Stock-based compensation % of sales', 'pct', 'pct', hist=ratio('is_sbc', 'is_rev'),
      qe=lambda: f'=IFERROR({H1("is_sbc")}/{H1("is_rev")},"")', e26=ratio('is_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF EARNINGS (US GAAP; continuing operations)', 'section', note='CONSOLIDATED IS — forecast logic')
    S('is_rev', 'Sales', 'total', 'm', data='is_sales', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the segment build.')
    S('is_cogs', 'Cost of sales', 'line', 'm', data='is_cogs', flow=True,
      fc=lambda: f'={V("is_rev")}-({V("is_op")}+{V("is_sga")}+{V("is_rnd")}+N({V("is_othop")}))',
      note='Forecast = sales − (operating profit + SG&A + R&D): gross profit is implied by the adjusted operating profit build (amortization sits mainly in cost of sales).')
    S('is_gp', 'Gross profit', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}-{V("is_cogs")},"")')
    S('is_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('is_sga', 'Selling, general & administrative expenses', 'line', 'm', data='is_sga', flow=True,
      fc=lambda: f'={V("is_rev")}*{V("d_sga")}+{V("o_oth")}', note='Forecast = sales × SG&A % + other operating profit adjustments.')
    S('is_rnd', 'Research & development expenses', 'line', 'm', data='is_rnd', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_rnd")}')
    S('is_othop', 'Other operating items (gains on sales, impairments where presented separately)', 'line', 'm', data='is_other_op', flow=True,
      qe_in={3: 0.0, 4: 0.0}, ae_in=0.0)
    S('is_op', 'Operating profit', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_gp")}-{V("is_sga")}-{V("is_rnd")}-N({V("is_othop")}),"")',
      fc=lambda: f'={V("g_adjop")}-{V("is_amort")}-{V("o_oth")}',
      note='Forecast = adjusted operating profit (segment build) − amortization − other operating profit adjustments.')
    S('is_opm', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('is_op_chk', '  Check: operating profit vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_op_pub")}),IF(ABS({V("is_op")}-{V("is_op_pub")})<=0.6,0,ROUND({V("is_op")}-{V("is_op_pub")},1)),"")')
    S('is_op_pub', '  Memo: operating profit as reported', 'memo', 'm', data='is_op_profit', flow=True)
    S('is_nonop', 'Other income (expense), net & other nonoperating items', 'line', 'm', data='is_nonop', flow=True, qe_in={3: 0.0, 4: 0.0}, ae_in=0.0,
      note='Fair-value gains / losses on equity & LP investments (excluded from adjusted EPS), pension non-service items, debt extinguishment. Forecast nil.')
    S('is_intexp', 'Interest expense', 'line', 'm', data='is_interest_exp', flow=True,
      qe=lambda: f'=({PT("pt_int")}-({H1("is_intexp")}-{H1("is_intinc")}))/2+{V("is_intinc")}',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_fac")}*{V("ds_r_fac")}',
      note='Q3/Q4-26E: FY26 net interest guidance (~$310m) less 1H/26 net, split evenly, + interest income. 2027E+ = rate × opening notes + rate × opening CP (no circularity).')
    S('is_intinc', 'Interest income', 'line', 'm', data='is_interest_inc', flow=True, qe_in={3: V0['intinc_q'], 4: V0['intinc_q']},
      ae=lambda: f'={P("cf_end")}*{V("ds_r_cash")}', note='Cash balances fell after the Masimo closing (Jun-2026). 2027E+: yield × opening cash.')
    S('is_ebt', 'Earnings from continuing operations before income taxes', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_op")}),{V("is_op")}+N({V("is_nonop")})-{V("is_intexp")}+N({V("is_intinc")}),"")')
    S('is_tax', 'Income taxes', 'line', 'm', data='is_tax', flow=True,
      fc=lambda: f'=({V("is_ebt")}+{V("e_items")}+{V("e_nonop")})*{V("e_etr")}-({V("e_items")}+{V("e_nonop")})*{V("e_rate")}+N({V("e_disc")})',
      note='Forecast = adjusted pretax earnings × adjusted tax rate (guided ~17%) − tax effect of adjusting items: the adjusted tax rate is the guided input.')
    S('is_etr', '  Effective tax rate (GAAP)', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'))
    S('is_cont', 'Net earnings from continuing operations', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_disc', 'Earnings (loss) from discontinued operations, net of tax', 'line', 'm', data='is_disc_ops', flow=True, qe_in={3: 0.0, 4: 0.0}, ae_in=0.0,
      note='Fortive (2016), Envista (2019), Veralto (2023) and other divested businesses — historical as reported.')
    S('is_ni', 'Net earnings', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_cont")}),{V("is_cont")}+N({V("is_disc")}),"")')
    S('is_nci', '  Less: noncontrolling interests (where presented)', 'line', 'm', data='is_nci', flow=True, qe_in={3: 0.0, 4: 0.0}, ae_in=0.0)
    S('is_pref', '  Less: mandatory convertible preferred stock dividends (2019–2023)', 'line', 'm', data='is_pref_div', flow=True, qe_in={3: 0.0, 4: 0.0}, ae_in=0.0)
    S('is_nic', 'Net earnings attributable to common stockholders', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_ni")}),{V("is_ni")}-N({V("is_nci")})-N({V("is_pref")}),"")')
    S('is_ni_chk', '  Check: net earnings vs reported (should be 0; ±0.6 rounding)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=0.6,0,ROUND({V("is_ni")}-{V("is_ni_pub")},1)),"")')
    S('is_ni_pub', '  Memo: net earnings as reported', 'memo', 'm', data='is_net_income', flow=True)
    S('is_nicont', '  Memo: net earnings from continuing operations attributable to common', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_cont")}),{V("is_cont")}-N({V("is_nci")})-N({V("is_pref")}),"")')
    S('is_amort', '  Memo: amortization of acquisition-related intangibles (total)', 'memo_calc', 'm', data='amort', flow=True,
      fc=lambda: f'={V("d_amort")}+N({V("ms_amort")})+N({V("st_amort")})+N({V("m_amort")})',
      note='Historical: cash-flow statement / adjusted-EPS footnote. Forecast: existing schedule + Masimo + StatLab + future M&A.')
    S('is_dda', '  Memo: depreciation & amortization (total)', 'memo_calc', 'm', all=lambda: f'=IF(ISNUMBER({V("d_dep")}),{V("d_dep")}+N({V("is_amort")}),"")')
    S('is_sbc', '  Memo: stock-based compensation', 'memo_calc', 'm', data='cf_sbc', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_sbc")}')
    S('eps_hdr', '(Earnings per share)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='is_shares_basic', avg=True,
      qe=lambda: f'=$BX${R["sh_basic"]}-$CA${R["bb_sh"]}*{0.25 if CTX.col.q == 3 else 0.75}',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q3/Q4-26E: Q2/26 less the 2H/26 buyback phased in (¼ in Q3, ¾ in Q4). 2027E+: average of beginning and ending shares. Pre-June-2010 restated for the 2-for-1 split.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='is_shares_diluted', avg=True,
      qe=lambda: f'={V("sh_basic")}+($BX${R["sh_dil"]}-$BX${R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_cont', 'EPS – diluted, continuing operations ($)', 'eps_total', 'ps', all=ratio('is_nicont', 'sh_dil'),
      note='Computed as net earnings from continuing operations attributable to common / diluted shares (MCPS anti-dilutive / if-converted cases may differ by a few cents).')
    S('eps_dil', 'EPS – diluted, net earnings ($)', 'eps', 'ps', all=ratio('is_nic', 'sh_dil'))
    S('eps_g', '  EPS – diluted continuing operations y/y %', 'growth', 'pct', all=growth('eps_cont'))
    S('eps_pub', '  Memo: EPS – diluted, continuing operations as reported ($; split-adjusted)', 'eps_memo', 'ps', data='is_eps_dil_cont')
    S('dps', '  Dividends declared per share ($)', 'line', 'ps', data='dps', flow=True,
      qe=lambda: f'=$BX${R["dps"]}', ae=lambda: f'={P("dps")}*(1+{V("dps_g")})', note='Q3/Q4-26E at the current quarterly rate; 2027E+ grows with the DPS growth input.')
    S('dps_g', '  Dividend per share growth %', 'growth', 'pct', hist=growth('dps'), e26=growth('dps'), ae_in=V0['dps_g'])
    S('payout', '  Dividend payout (DPS / adjusted EPS) %', 'pct', 'pct', all=ratio('dps', 'e_eps'))
    blank()

    # ------------------------------------------------------------------ RECON 1: EBITDA (model definition)
    S('sec_r1', 'RECONCILIATION: NET EARNINGS → EBITDA → ADJUSTED EBITDA (model definition — Danaher does not publish EBITDA)', 'section',
      note='ADJUSTED EBITDA (model) — continuing net earnings + taxes + net interest + D&A; + other operating profit adjustments and nonoperating items excluded from adjusted EPS (= adjusted operating profit + depreciation)')
    S('r_ni', 'Net earnings from continuing operations (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_cont")}')
    S('r_tax', '  (+) Income taxes', 'line', 'm', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest expense, net of interest income', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_intexp")}),{V("is_intexp")}-N({V("is_intinc")}),"")')
    S('r_dda', '  (+) Depreciation & amortization', 'line', 'm', all=lambda: f'={V("is_dda")}')
    S('r_ebitda', '  = EBITDA', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_ni")}),ISNUMBER({V("r_dda")})),{V("r_ni")}+{V("r_tax")}+{V("r_int")}+{V("r_dda")},"")')
    S('r_oth', '  (+) Other operating profit adjustments (impairments, acquisition items, restructuring, contingencies)', 'line', 'm', all=lambda: f'={V("o_oth")}')
    S('r_nonop', '  (+/−) Nonoperating (income) expense (investment fair-value gains / losses, other)', 'line', 'm', all=lambda: f'=-N({V("is_nonop")})')
    S('r_tot', '  Total adjusting items', 'line_b', 'm', all=lambda: f'={nsum(["r_oth", "r_nonop"])}')
    S('r_adj', '  = Adjusted EBITDA (model bridge)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{V("r_ebitda")}+{V("r_tot")},"")',
      note='Model definition consistent with Danaher\'s adjusted operating profit: adjusted EBITDA = adjusted operating profit + depreciation. Danaher does not publish EBITDA (only the Masimo deal EBITDA target).')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_adj_pub', '  Company-published Adjusted EBITDA', 'memo', 'm', note='Not published by Danaher (n/p).')
    S('r_adj_chk', '  Check: Adjusted EBITDA = adjusted operating profit (bridge 2) + depreciation (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_adj")}),ISNUMBER({V("o_adj")})),IF(ABS({V("r_adj")}-{V("o_adj")}-{V("d_dep")})<=1,0,ROUND({V("r_adj")}-{V("o_adj")}-{V("d_dep")},1)),"")')
    S('r_adj_pf', '  Memo: Adjusted EBITDA pro forma — Masimo full year (2026E), for leverage & valuation', 'memo_calc', 'm',
      all=lambda: f'={V("r_adj")}',
      e26=lambda: f'={V("r_adj")}+({V("ms_pf")}-{V("ms_rev")})*({V("ms_adjm")}+{V("ms_dap")})',
      note='2026E adds Masimo pre-closing (1-Jan to 9-Jun-2026) EBITDA at the 2026E Masimo margin; other years = Adjusted EBITDA.')
    S('r_def', '  Definition basis (Adjusted EBITDA — model definition in force)', 'text', 'gen')
    S('r_ebit_h', 'To adjusted EBIT:', 'sub', 'gen')
    S('r_ddan', '  (−) Depreciation & amortization', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("r_dda")}),-{V("r_dda")},"")')
    S('r_ebit', '  = Adjusted EBIT (model; Adjusted EBITDA − D&A, i.e. after acquired-intangible amortization)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_ddan")}),{V("r_adj")}+{V("r_ddan")},"")', note='Used for NOPAT / ROIC (conservative: deducts ~$1.7–1.9bn of non-cash acquired-intangible amortization).')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: adjusted operating profit
    S('sec_r2', 'RECONCILIATION: GAAP OPERATING PROFIT → ADJUSTED OPERATING PROFIT (company definition; published from FY24)', 'section',
      note='ADJUSTED OPERATING PROFIT — Danaher definition (Q4-25 release): operating profit + amortization of intangible assets + other operating profit adjustments')
    S('o_op', 'Operating profit (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_op")}')
    S('o_amort', '  (+) Amortization of acquisition-related intangible assets', 'line', 'm', all=lambda: f'={V("is_amort")}')
    S('o_oth', '  (+) Other operating profit adjustments (impairments, acquisition-related items, restructuring, contingencies, gains)', 'line', 'm',
      data='o_oth', flow=True, qe=lambda: f'={V("ms_inv")}', ae=lambda: f'={V("ms_inv")}',
      note='Operating-level items excluded from adjusted EPS (release footnotes, pretax). Forecast: Masimo inventory step-up / acquisition items only.')
    S('o_tot', '  Total operating-level adjusting items', 'line_b', 'm', all=lambda: f'={nsum(["o_amort", "o_oth"])}')
    S('o_adj', '  = Adjusted operating profit (model bridge)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_tot")},"")',
      note='Company definition applied in every period (Danaher has published the measure since the Q4-25 release, with FY24 / Q4-24 comparatives).')
    S('o_adj_m', '  Adjusted operating profit margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_adj_pub', '  Company-published adjusted operating profit', 'memo', 'm', data='adj_op_pub', flow=True)
    S('o_chk', '  Check: model bridge vs company-published (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("o_adj_pub")}),IF(ABS({V("o_adj")}-{V("o_adj_pub")})<=1,0,ROUND({V("o_adj")}-{V("o_adj_pub")},0)),"n/p")')
    S('o_def', '  Definition basis (company adjusted operating profit definition)', 'text', 'gen')
    S('o_adj_g', '  Adjusted operating profit y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental adjusted operating margin (Δ adj. op. profit / Δ sales)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: GAAP NET EARNINGS / DILUTED EPS → ADJUSTED NET EARNINGS → ADJUSTED DILUTED EPS (company definition, as published)', 'section',
      note='ADJUSTED EPS — company definition in force in each period ($ amounts from the release footnotes; per-share lines × diluted shares where no $ amount is given)')
    S('e_ni', 'Net earnings from continuing operations attributable to common (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_nicont")}')
    S('e_amort', '  (+) Amortization of acquisition-related intangibles, pretax', 'line', 'm', data='br_amort', flow=True, fc=lambda: f'={V("o_amort")}',
      note='Added back from Q1-16 (earlier adjusted EPS excluded only discrete items).')
    S('e_oth', '  (+) Other operating-level items, pretax', 'line', 'm', data='br_op', flow=True, fc=lambda: f'={V("o_oth")}')
    S('e_items', '  Operating-level adjusting items in the adjusted EPS bridge, pretax', 'line', 'm', all=lambda: f'={nsum(["e_amort", "e_oth"])}')
    S('e_nonop', '  (+) Nonoperating items, pretax (investment fair-value gains / losses, debt extinguishment)', 'line', 'm', data='br_nonop', flow=True,
      qe_in={3: 0.0, 4: 0.0}, ae_in=0.0)
    S('e_nonop_x', '  Memo: adjusted other income (nonoperating income not excluded; helper)', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_nonop")}),{V("is_nonop")}+{V("e_nonop")},"")')
    S('e_tax', '  (−) Tax effect of adjusting items', 'line', 'm', data='br_taxeff', flow=True,
      fc=lambda: f'=-({V("e_items")}+{V("e_nonop")})*{V("e_rate")}')
    S('e_disc', '  (+/−) Discrete tax adjustments', 'line', 'm', data='br_disc', flow=True, qe_in={3: 0.0, 4: 0.0}, ae_in=0.0)
    S('e_pref', '  (+) MCPS dividends / if-converted adjustment (2019–2023)', 'line', 'm', data='br_pref', flow=True, qe_in={3: 0.0, 4: 0.0}, ae_in=0.0)
    S('e_oth2', '  (+/−) Other per-share-only items & rounding (× diluted shares)', 'line', 'm', data='br_resid', flow=True, qe_in={3: 0.0, 4: 0.0}, ae_in=0.0)
    S('e_adjni', '  = Adjusted net earnings (model bridge)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("e_pub")}),{V("e_ni")}+{nsum(["e_items", "e_nonop", "e_tax", "e_disc", "e_pref", "e_oth2"])},"")',
      fc=lambda: f'={V("e_ni")}+{nsum(["e_items", "e_nonop", "e_tax", "e_disc", "e_pref", "e_oth2"])}', note='Historical shown where Danaher published adjusted EPS.')
    S('e_rate', '  Tax rate applied to adjusting items', 'pct', 'pct',
      hist=lambda: f'=IFERROR(-{V("e_tax")}/({V("e_items")}+N({V("e_nonop")})),"")', qe_in=V0['item_tax'], ae_in=V0['item_tax'],
      note='Historical: implied by the company footnotes (after-tax vs pretax amounts). Forecast input (amortization deductible at blended jurisdictional rates).')
    S('e_etr', '  Adjusted effective tax rate (adjusted tax ÷ adjusted pretax earnings)', 'pct', 'pct',
      hist=lambda: (f'=IFERROR(({V("is_tax")}-{V("e_tax")}-N({V("e_disc")}))/({V("is_ebt")}+{V("e_items")}+N({V("e_nonop")})),"")'),
      qe=lambda: f'={PT("pt_etr")}', e26=lambda: f'=IFERROR(({V("is_tax")}-{V("e_tax")}-N({V("e_disc")}))/({V("is_ebt")}+{V("e_items")}+N({V("e_nonop")})),"")',
      ae_in=V0['etr'], note='Guided ~17% for FY26 (non-GAAP basis). 2027E+ input.')
    S('e_sh', '  Diluted shares used in adjusted EPS (m)', 'line', 'm1', all=lambda: f'={V("sh_dil")}',
      note='Weighted diluted shares (MCPS if-converted shares for 2019–2023 periods are captured in the per-share adjustment row).')
    S('e_eps', 'Adjusted diluted EPS ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted diluted EPS ($; split-adjusted; hybrid-recast basis)', 'eps_memo', 'ps', data='adj_eps_pub')
    S('e_chk', '  Check: model vs company-published adjusted EPS (should be 0.00; ±0.02 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(ISNUMBER({V("e_pub")}),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.025,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_orig', '  Memo: adjusted EPS as originally published (where the period was later recast)', 'eps_memo', 'ps', data='adj_eps_orig')
    S('e_def', '  Definition basis (company adjusted EPS definition in force)', 'text', 'gen')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Sales y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_core', '  Core sales growth %', 'growth', 'pct', all=lambda: f'={V("g_core")}' if CTX.col.prior else None)
    S('gm_bio', '  Biotechnology sales y/y %', 'growth', 'pct', all=lambda: f'={V("bio_rev_g")}' if CTX.col.prior else None)
    S('gm_ls', '  Life Sciences sales y/y %', 'growth', 'pct', all=lambda: f'={V("ls_rev_g")}' if CTX.col.prior else None)
    S('gm_dx', '  Diagnostics sales y/y % (legacy)', 'growth', 'pct', all=lambda: f'={V("dx_rev_g")}' if CTX.col.prior else None)
    S('gm_adjop', '  Adjusted operating profit y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating profit (GAAP) y/y %', 'growth', 'pct', all=growth('is_op'))
    S('gm_ni', '  Net earnings from continuing operations y/y %', 'growth', 'pct', all=growth('is_nicont'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('gm_adjm', '  Adjusted operating profit margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_inc', '  Incremental Adjusted EBITDA margin (ΔEBITDA / ΔSales)', 'pct', 'pct', all=incr('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('gm_net_m', '  Net margin (continuing, attributable to common) %', 'pct', 'pct', all=ratio('is_nicont', 'is_rev'))
    S('gm_sga', '  SG&A % of sales', 'pct', 'pct', all=ratio('is_sga', 'is_rev'))
    S('gm_rnd', '  R&D % of sales', 'pct', 'pct', all=ratio('is_rnd', 'is_rev'))
    blank()


def core_ae():
    y = CTX.col.year
    legacy = '+'.join(f'{P(s + "_rev")}*{V(s + "_core")}' for s in LINES)
    org = f'+({V("ms_pf")}-{P("ms_pf")}-({V("ms_rsyn")}-{P("ms_rsyn")}))+({V("st_rev")}-{P("st_rev")})' if y >= 2028 else ''
    return f'=IFERROR(({legacy}{org})/{P("is_rev")},"")'
