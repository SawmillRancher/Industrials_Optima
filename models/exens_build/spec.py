"""Row specification of the EXENS Model sheet, part 1 (MLM template layout and process):
segment build (Amplification / Detection & Imaging: like-for-like growth + scope & currency) -> group revenue & FY26 outlook calibration
(Q3 actual + Q4E solved to the guidance end-point) -> adjusted gross margin -> Adjusted EBITDA margin build -> cost drivers ->
IFRS income statement -> IFRS-to-adjusted bridges -> growth & margins."""
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
def ratio(nk, d): return lambda: f'=IF(AND(ISNUMBER({V(nk)}),ISNUMBER({V(d)})),IFERROR({V(nk)}/{V(d)},""),"")'
def incr(nk, d):
    def f():
        if CTX.col.prior is None: return None
        return f'=IFERROR(({V(nk)}-{P(nk)})/({V(d)}-{P(d)}),"")'
    return f
def nsum(keys): return '+'.join(f'N({V(k)})' for k in keys)
def H2v(key): return f'${H2}${R[key]}'
def E26v(key): return f'${E26}${R[key]}'

SEGS = [('amp', 'Amplification', 'AMP'), ('di', 'Detection & Imaging', 'DI')]
def sprior(): return '+'.join(P(k) for k, _, _ in SEGS)

# ====================================================================== scenario table (AC:AG)
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of the FY26 guidance ranges (17-Sep-2026).'))
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
    S('sec_sg', 'REVENUE BUILD — AMPLIFICATION · DETECTION & IMAGING (like-for-like growth + scope & currency effect)', 'section',
      note='SEGMENT BUILD — modelling logic (prior-year period × (1 + like-for-like growth + scope & currency effect) → segment revenue → adjusted gross margin → Adjusted EBITDA margin → IFRS P&L). '
           'H2/26E = Q3-26 actual (memo rows) + Q4-26E solved to the FY26 revenue guidance; 2027E+ scenario levers')
    blank()
    for k, title, code in SEGS:
        S(f'{k}_hdr', {'amp': 'Amplification (image intensifier tubes for night vision; power tubes) — c.69% of 9M-26 revenue',
                       'di': 'Detection & Imaging (infrared / SWIR / UV cameras, neutron & gamma detectors, electron & ion detectors, wavefront sensors) — c.31%'}[k], 'block',
          note=f'{title.upper()} — modelling logic')
        S(k, '  Revenue (€m)', 'line', 'm1', data=f'{k}_rev', flow=True,
          he=lambda k=k: f'={V(k + "_qa")}+{V(k + "_qb")}', ae=lambda k=k: f'={P(k)}*(1+{V(k + "_lfl")}+{V(k + "_scope")})',
          note=('Segment revenue as published (continuing-operations basis from 2024: the FY2025 release restated the 2024 quarters for the Microwave Amplification '
                'disposal; 2023 and earlier as originally reported). H2 = FY − H1. H2/26E = Q3-26 actual + Q4-26E (memo rows). 2027E+: prior year × (1 + like-for-like growth + scope & currency).') if k == 'amp' else
                'Segment revenue as published (restated 2024; H2 = FY − H1). H2/26E = Q3-26 actual + Q4-26E. 2027E+: prior year × (1 + like-for-like growth + scope).')
        S(k + '_g', '    y/y % (reported)', 'growth', 'pct', all=growth(k))
        S(k + '_lfl', '    y/y % like-for-like (company definition: excl. acquisitions and currency)', 'growth', 'pct', data=f'{k}_lfl',
          he=lambda k=k: f'=IFERROR({V(k)}/{P(k)}-1-{V(k + "_scope")},"")', e26=lambda k=k: f'=IFERROR({V(k)}/{P(k)}-1-{V(k + "_scope")},"")',
          ae=lambda k=k, code=code: '=' + CH(SC[f'{code}_LFL'][CTX.col.year]),
          note=('Published like-for-like growth (H1 / 9M / FY releases; acquired companies enter like-for-like after 12 months). H2/26E and 2026E: implied '
                '(reported growth − scope input). 2027E–2030E: scenario lever (medium-term target "up to mid-teens" organic growth).') if k == 'amp' else None)
        S(k + '_scope', '    Scope & currency effect (pts; reported − like-for-like)', 'growth', 'pct',
          all=lambda k=k: f'=IF(AND(ISNUMBER({V(k + "_g")}),ISNUMBER({V(k + "_lfl")})),{V(k + "_g")}-{V(k + "_lfl")},"")',
          he_in=V0['scope_he'][k], ae=lambda k=k: f'=IFERROR({V("ma_rev_" + k)}/{P(k)},0)+{PT("pt_fx")}',
          e26=lambda k=k: f'=IFERROR((N({Hc(k + "_scope", 2026, 1)})*{Hc(k, 2025, 1)}+N({Hc(k + "_scope", 2026, 2)})*{Hc(k, 2025, 2)})/{P(k)},"")',
          note=('Company releases give reported and like-for-like growth only; the difference is acquisitions plus currency. H2/26E: input (2025 acquisitions '
                'Noxant / NVLS / Phasics anniversaried by Q4-26 except Phasics (20-Oct-2025); Emberion immaterial). 2027E+: future-M&A lever contribution + FX input.') if k == 'amp' else
                'H2/26E input: Phasics (acquired 20-Oct-2025) and Emberion (24-Apr-2026, immaterial) scope in Q4-26. 2027E+: future-M&A lever (70% allocated to D&I) + FX input.')
        S(k + '_qa', '    Memo: first quarter of the half (Q1 in H1 columns; Q3 in H2 columns)', 'memo', 'm1', data=f'qa_{k}', he_in=V0['q3'][k],
          note=('Quarterly revenue from the Q1 / Q3 trading updates and the FY release appendices (2024 restated). H2/26E: Q3-26 actual (9M-26 release, 27-Oct-2026), blue input.') if k == 'amp' else None)
        S(k + '_qb', '    Memo: second quarter of the half (Q2 in H1 columns; Q4 in H2 columns)', 'memo', 'm1', data=f'qb_{k}',
          he=lambda k=k: f'={P(k + "_qb")}*(1+{V(k + "_q4g")})',
          note=('Q4-26E = Q4-25 × (1 + Q4 growth). Q4-25 = H2-25 − Q3-25 (restated).') if k == 'amp' else None)
        S(k + '_q4pre', '    Q4-26E y/y growth before calibration (= Q3-26 reported growth)', 'driver', 'pct', he=lambda k=k: f'=IFERROR({V(k + "_qa")}/{P(k + "_qa")}-1,0)',
          note=('Q3-26: Amplification +23.9%, D&I +22.5% reported (capacity ramp-up ahead of plan; 9M-26 release). Carried into Q4 before the uniform calibration Δ.') if k == 'amp' else None)
        S(k + '_q4g', '    Q4-26E y/y growth (before calibration + uniform Δ)', 'driver', 'pct', he=lambda k=k: f'={V(k + "_q4pre")}+{V("cal_g")}')
        S(k + '_agp', '  Adjusted gross margin (€m; company segment measure)', 'line', 'm1', data=f'{k}_agp', flow=True,
          he=lambda k=k: f'={V(k + "_agp_qa")}+{V(k + "_agp_qb")}', ae=lambda k=k: f'={V(k)}*{V(k + "_agpm")}',
          note=('Company "adjusted gross profit / margin": selling price less cost of products and services incl. employee costs (segment note; management basis). '
                'H2/26E = Q3-26 actual + Q4-26E (Q4-25 margin + Δ input). 2027E+: revenue × margin lever.') if k == 'amp' else None)
        S(k + '_agpm', '    Adjusted gross margin % of segment revenue', 'pct', 'pct', all=ratio(k + '_agp', k), ae=lambda k=k, code=code: '=' + CH(SC[f'{code}_AGM'][CTX.col.year]),
          note=('FY25 50.5% (FY24 48.7%); H1-26 52.5%; 9M-26 51.9% (NVLS complete-system mix, US plant staffing). 2027E+: scenario lever.') if k == 'amp' else
                'FY25 48.3%; H1-26 48.1%; 9M-26 46.6% (defense imaging mix vs life-science detectors). 2027E+: scenario lever.')
        S(k + '_agp_qa', '    Memo: adjusted gross margin, first quarter of the half (€m)', 'memo', 'm1', data=f'qa_agp_{k}', he_in=V0['q3'][k + '_agp'])
        S(k + '_agp_qb', '    Memo: adjusted gross margin, second quarter of the half (€m)', 'memo', 'm1', data=f'qb_agp_{k}',
          he=lambda k=k: f'={V(k + "_qb")}*(IFERROR({P(k + "_agp_qb")}/{P(k + "_qb")},0)+{PT("pt_agm_d")})',
          note=('Q4-26E = Q4-26E revenue × (Q4-25 margin + Δ point estimate).') if k == 'amp' else None)
        S(k + '_mix', '    % of group revenue', 'pct', 'pct', all=ratio(k, 'g_rev'))
        blank()
    S('el_hdr', 'Eliminations & other (inter-segment sales)', 'block', note='ELIMINATIONS — % of gross segment revenue')
    S('elim', '  Eliminations & other (€m)', 'line', 'm1', data='elim_rev', flow=True,
      he=lambda: f'={V("elim_qa")}+{P("elim_qb")}*(1+{V("g_q4pre")}+{V("cal_g")})', ae=lambda: f'=({V("amp")}+{V("di")})*{V("elim_pct")}')
    S('elim_qa', '    Memo: first quarter of the half', 'memo', 'm1', data='qa_elim', he_in=V0['q3']['elim'])
    S('elim_qb', '    Memo: second quarter of the half', 'memo', 'm1', data='qb_elim', he=lambda: f'={V("elim")}-{V("elim_qa")}')
    S('elim_pct', '    Eliminations % of gross segment revenue', 'pct', 'pct', all=lambda: f'=IFERROR({V("elim")}/({V("amp")}+{V("di")}),"")', ae_in=V0['elim_pct'],
      note='FY25 −0.3%, FY24 −1.0%, H1-26 −0.2%. 2027E+: input.')
    blank()

    # ------------------------------------------------------------------ group total & outlook calibration
    S('g_hdr', 'Group Total — revenue (segment build) → FY26 outlook calibration (revenue guidance €558–570m; Adjusted EBITDA €186–192m)', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Revenue (segment build)', 'total', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("amp")}),N({V("amp")})+N({V("di")})+N({V("elim")}),{V("is_rev")})',
      fc=lambda: f'={V("amp")}+{V("di")}+{V("elim")}',
      note='Σ Amplification + Detection & Imaging + eliminations. Reported revenue where no segment split is published (FY2021–22 in the registration document key figures only if absent).')
    S('g_rev_g', '  Revenue y/y % (reported)', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs consolidated revenue (should be 0; blank where the build is on the restated basis and the P&L as originally reported)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_rev")}),ISNUMBER({V("is_rev")}),{V("g_basis")}=""),IF(ABS({V("g_rev")}-{V("is_rev")})<=0.15,0,ROUND({V("g_rev")}-{V("is_rev")},1)),"")')
    S('g_basis', '  Basis flag: segment build restated (continuing operations) while the P&L is as originally reported', 'text', 'gen', data='seg_flag', textdata=True,
      note='H1/24 and H2/24: the segment build uses the FY2025 release\'s restated 2024 quarters (Microwave Amplification excluded, €10.6m FY24 revenue) while the H1/24 income statement is as originally reported; H2/24 P&L = FY24 restated − H1/24 reported.')
    S('g_madiff', '  Memo: reported revenue − continuing-operations build (Microwave Amplification, discontinued 31-Dec-2025)', 'memo_calc', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("g_rev")}),ISNUMBER({V("is_rev")}),{V("g_basis")}<>""),ROUND({V("is_rev")}-{V("g_rev")},1),"")')
    S('g_lfl', '  Like-for-like growth, model (Σ segment like-for-like growth weighted by prior-year revenue; eliminations at their reported change)', 'growth', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("amp_lfl")}),ISNUMBER({V("di_lfl")})),IFERROR(({P("amp")}*(1+{V("amp_lfl")})+{P("di")}*(1+{V("di_lfl")})+N({V("elim")}))/({sprior()}+N({P("elim")}))-1,""),"")' if CTX.col.prior else None))
    S('g_lfl_pub', '  Memo: group like-for-like growth as published', 'memo', 'pct', data='tot_lfl',
      note='Company definition: revenue of the companies in the scope at the end of period n−1, at constant currency. Published for H1, 9M, FY and (from 2025) each quarter.')
    S('g_lfl_chk', '  Check: model vs published like-for-like growth (should be 0; ±0.3pt, eliminations are not in the segment rates)', 'check', 'pct',
      hist=lambda: f'=IF(AND(ISNUMBER({V("g_lfl")}),ISNUMBER({V("g_lfl_pub")})),IF(ABS({V("g_lfl")}-{V("g_lfl_pub")})<=0.003,0,ROUND({V("g_lfl")}-{V("g_lfl_pub")},4)),"")')
    S('g_scope', '  Scope & currency effect (pts; reported growth − like-for-like)', 'growth', 'pct',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_rev_g")}),ISNUMBER({V("g_lfl")})),{V("g_rev_g")}-{V("g_lfl")},"")')
    S('g_qa', '  Memo: group revenue, first quarter of the half (Q1 / Q3)', 'memo', 'm1', data='qa_tot', he=lambda: f'={V("amp_qa")}+{V("di_qa")}+{V("elim_qa")}',
      note='Q1 / Q3 revenue from the trading updates (2024 restated, FY2025 release appendix). H2/26E: Q3-26 actual €133.8m (+23.5%; like-for-like +20.5%).')
    S('g_qa_lfl', '    like-for-like growth %, first quarter of the half (published)', 'memo', 'pct', data='qa_lfl', he_in=V0['q3']['lfl'])
    S('g_qb', '  Memo: group revenue, second quarter of the half (Q2 / Q4)', 'memo', 'm1', data='qb_tot', he=lambda: f'={V("g_rev")}-{V("g_qa")}',
      note='Q4-26E = H2/26E − Q3-26 actual (solved to the FY26 revenue guidance end-point below).')
    S('g_qb_lfl', '    like-for-like growth %, second quarter of the half (published)', 'memo', 'pct', data='qb_lfl')
    S('g_q4pre', '  Q4-26E group growth before calibration (= Q3-26 reported growth; used for eliminations)', 'driver', 'pct', he=lambda: f'=IFERROR({V("g_qa")}/{P("g_qa")}-1,0)')
    S('g_q4g', '  Q4-26E group revenue y/y % (output)', 'growth', 'pct', he=lambda: f'=IFERROR({V("g_qb")}/{P("g_qb")}-1,"")',
      note='Guidance mid-point implies Q4-26E ≈ €177m vs Q4-25 €140.4m (+26%); Q3-26 was +23.5% with capacity ramping faster than planned.')
    S('cal_rev', '  Memo: FY26 revenue guidance (scenario end-point, €m)', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_rev']), note=V0['rev_guid_note'])
    S('cal_g', '  Outlook calibration: uniform Δ on Q4-26E segment growth so FY26 revenue = guidance end-point', 'driver', 'pct',
      he=lambda: (f'=({V("cal_rev", E26)}-{V("g_rev", H1)}-{V("g_qa")}-({P("amp_qb")}*(1+{V("amp_q4pre")})+{P("di_qb")}*(1+{V("di_q4pre")})+{P("elim_qb")}*(1+{V("g_q4pre")})))'
                  f'/({P("amp_qb")}+{P("di_qb")}+{P("elim_qb")})'),
      note='Closed-form solve: Δ = (FY26 target − H1-26 − Q3-26 − Σ Q4-25 × (1 + Q3-26 growth)) ÷ Σ Q4-25. Applied uniformly to Amplification, D&I and eliminations.')
    S('cal_rev_chk', '  Check: FY26 revenue vs guidance end-point (should be 0)', 'check', 'm1', e26=lambda: f'=ROUND({V("g_rev")}-{V("cal_rev")},1)')
    S('tg_h', '  Medium-term outlook (FY2025 release / URD 2025 §5.8; UNVERIFIED — not on SEC EDGAR) vs model — information, not forced:', 'sub', 'gen')
    S('tg_lfl', '    Organic revenue growth target "up to mid-teens" (model like-for-like growth)', 'memo_calc', 'pct', ae=lambda: f'={V("g_lfl")}')
    S('tg_eb', '    Organic Adjusted EBITDA growth target "above 15%" (model Adjusted EBITDA y/y %, incl. M&A)', 'memo_calc', 'pct', ae=lambda: f'=IFERROR({V("g_adj")}/{P("g_adj")}-1,"")')
    S('tg_1bn', '    €1bn revenue ambition (model revenue − 1,000)', 'memo_calc', 'm1', ae=lambda: f'={V("g_rev")}-1000')
    blank()

    # ------------------------------------------------------------------ margin build
    S('m_hdr', 'Profitability build — adjusted gross margin → Adjusted EBITDA margin → FY26 outlook calibration (Adjusted EBITDA €186–192m)', 'block',
      note='MARGIN BUILD — H2/26E Adjusted EBITDA = FY26 guidance end-point − H1-26 actual (the company guides Adjusted EBITDA); 2027E+: scenario margin lever')
    S('m_agp', '  Adjusted gross margin (Σ segments + unallocated, €m)', 'line', 'm1', data='agp_pub', flow=True,
      fc=lambda: f'={V("amp_agp")}+{V("di_agp")}+{V("m_agp_oth")}', note='Company "gross profit (adjusted)" total; forecast = Σ segment adjusted gross margin + unallocated / eliminations.')
    S('m_agp_oth', '    Unallocated / eliminations (€m)', 'line', 'm1', data='oth_agp', flow=True, he_in=V0['q3']['agp_oth'], ae_in=0.0)
    S('m_agp_chk', '    Check: Σ segments + unallocated vs published adjusted gross margin (should be 0; ±0.25 rounding of one-decimal tables)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("amp_agp")}),ISNUMBER({V("m_agp")})),IF(ABS({V("amp_agp")}+{V("di_agp")}+N({V("m_agp_oth")})-{V("m_agp")})<=0.25,0,ROUND({V("amp_agp")}+{V("di_agp")}+N({V("m_agp_oth")})-{V("m_agp")},1)),"")')
    S('m_agpm', '  Adjusted gross margin % of revenue', 'pct', 'pct', all=ratio('m_agp', 'g_rev'))
    S('m_ebm', '  Adjusted EBITDA margin %', 'pct', 'pct', hist=lambda: f'=IF(ISNUMBER({V("r_adj_pub")}),IFERROR({V("r_adj_pub")}/{V("is_rev")},""),"")',
      he=lambda: f'=IFERROR({V("g_adj")}/{V("g_rev")},"")', e26=lambda: f'=IFERROR({V("g_adj")}/{V("g_rev")},"")', ae=lambda: '=' + CH(SC['EBM'][CTX.col.year]),
      note='Historical = published Adjusted EBITDA ÷ revenue (FY25 32.4%, H1-26 33.0%). H2/26E: output of the guidance solve. 2027E–2030E: scenario lever (company: "mild progressive improvement").')
    S('m_ebm_d', '  H2/26E implied margin change vs H2/25 (pts; output of the guidance solve)', 'driver', 'pct', he=lambda: f'=IFERROR({V("m_ebm")}-{P("m_ebm")},"")')
    S('cal_eb', '  Memo: FY26 Adjusted EBITDA guidance (scenario end-point, €m)', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_ebitda']), note=V0['eb_guid_note'])
    S('g_adj', 'Adjusted EBITDA (company definition; margin build)', 'total', 'm1',
      hist=lambda: f'={V("r_adj_pub")}', he=lambda: f'={V("cal_eb", E26)}-{V("g_adj", H1)}', e26=lambda: S26('g_adj'), ae=lambda: f'={V("g_rev")}*{V("m_ebm")}',
      note="Exosens' guidance metric (operating profit before D&A / impairment, other income & expenses, share-based payments and non-recurring costs). H2/26E = FY26 guidance end-point − H1-26. Drives the IFRS P&L below.")
    S('g_adj_g', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('g_adj'))
    S('cal_eb_chk', '  Check: FY26 Adjusted EBITDA vs guidance end-point (should be 0)', 'check', 'm1', e26=lambda: f'=ROUND({V("g_adj")}-{V("cal_eb")},1)')
    S('g_chk_adj', '  Check: margin build vs Adjusted EBITDA bridge (should be 0; ±0.25: published one-decimal bridge lines, H2 = FY − H1)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_adj")}),ISNUMBER({V("r_adj")})),IF(ABS({V("g_adj")}-{V("r_adj")})<=0.25,0,ROUND({V("g_adj")}-{V("r_adj")},1)),"")')
    S('m_opex', '  Operating costs below adjusted gross margin, before D&A, share-based payments and one-offs (= adjusted gross margin − Adjusted EBITDA)', 'line', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("m_agp")}),ISNUMBER({V("g_adj")})),{V("m_agp")}-{V("g_adj")},"")', note='R&D, sales, general & administration (management basis) before D&A. Output.')
    S('m_opex_p', '  … % of revenue', 'pct', 'pct', all=ratio('m_opex', 'g_rev'), note='FY25 17.6%, FY24 17.9%, H1-26 18.3%. Operating leverage is the margin story: the Base margin lever implies a slowly falling ratio.')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers below Adjusted EBITDA — D&A, PPA amortisation, share-based payments, one-off costs', 'block',
      note='COST DRIVERS — H2/26E: FY26 point estimates less H1-26; 2027E+: % of revenue / schedules')
    S('d_dna', '  Depreciation & amortisation excl. PPA amortisation and brand impairment (incl. capitalised R&D and IFRS 16)', 'line', 'm1', data='dna_ex_ppa', flow=True,
      he=lambda: f'={PT("pt_dna")}-{V("d_dna", H1)}', e26=lambda: S26('d_dna'), ae=lambda: f'={V("g_rev")}*{V("d_dna_pct")}',
      note='Company bridge line "D&A and impairment excl. PPA" (FY25 €24.0m; H1-26 €11.8m). Includes amortisation of capitalised development costs (~€12.6m in FY25) and right-of-use depreciation.')
    S('d_dna_pct', '  … % of revenue', 'pct', 'pct', all=ratio('d_dna', 'g_rev'), ae_in=V0['dna_pct'],
      note='FY25 5.1%, FY24 5.7%, 2026E 4.4%; the €37m capacity programme and capitalised R&D (~3% of revenue p.a.) enter service from 2027. 2027E+: input 5.0%.')
    S('d_ppa', '  Amortisation of purchase-price-allocation intangibles (customer relationships, technologies)', 'line', 'm1', data='ppa_amort', flow=True,
      he=lambda: f'={PT("pt_ppa")}-{V("d_ppa", H1)}', e26=lambda: S26('d_ppa'), ae=lambda: f'={V("ia_ppa_am")}',
      note='Implied by the company bridge (D&A in the EBITDA bridge − D&A excl. PPA; H1-26 €7.9m and H1-25 €6.5m as printed in the release). 2027E+: intangibles schedule (existing PPA assets + future M&A).')
    S('d_brand', '  Brand impairment (Photonis / Telops / Xenics brands, H1-26; non-cash)', 'line', 'm1', data='brand', flow=True, he_in=0.0, e26=lambda: S26('d_brand'), ae_in=0.0,
      note='€28.2m non-cash impairment on unifying all brands under Exosens (H1-26); deferred tax reversal +€7.6m. Excluded from Adjusted EBITDA / EBIT and from net profit ex PPA & impairment.')
    S('d_dna_t', '  Total D&A and impairment of non-current assets (bridge line)', 'line_b', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("d_dna")}),{V("d_dna")}+N({V("d_ppa")})+N({V("d_brand")}),"")')
    S('d_sbc', '  Share-based payments (IFRS 2 incl. social charges; added back to Adjusted EBITDA)', 'line', 'm1', data='sbc', flow=True,
      he=lambda: f'={PT("pt_sbc")}-{V("d_sbc", H1)}', e26=lambda: S26('d_sbc'), ae=lambda: f'={V("g_rev")}*{V("d_sbc_pct")}',
      note='FY25 €6.8m (ExoShare €2.9m, LTIP €2.8m, related tax €1.0m); H1-26 €3.0m. 2027E+: % of revenue.')
    S('d_sbc_pct', '  … % of revenue', 'pct', 'pct', all=ratio('d_sbc', 'g_rev'), ae_in=V0['sbc_pct'])
    S('d_nonrec', '  Non-recurring costs (acquisition fees, earn-outs with bad-leaver clauses; added back)', 'line', 'm1', data='nonrec', flow=True,
      he=lambda: f'={PT("pt_nonrec")}-{V("d_nonrec", H1)}', e26=lambda: S26('d_nonrec'), ae_in=V0['nonrec_ae'],
      note='FY25 €4.7m, FY24 €4.5m, H1-26 €1.6m. 2027E+: input (ongoing bolt-on M&A).')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED INCOME STATEMENT (IFRS, by nature, as presented by Exosens)', 'section',
      note='CONSOLIDATED IS — forecast logic (operating expenses before D&A = revenue − EBITDA; EBITDA = Adjusted EBITDA − share-based payments − one-offs; D&A from the cost drivers; cost of net debt from the debt schedule)')
    S('is_rev', 'Revenue', 'total', 'm1', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the segment build.')
    S('is_cos', 'Cost of sales (materials and bought-in goods)', 'line', 'm1', data='cos', flow=True)
    S('is_ext', 'Other purchases and external expenses', 'line', 'm1', data='ext', flow=True)
    S('is_taxes', 'Taxes and duties other than income tax', 'line', 'm1', data='taxes', flow=True)
    S('is_staff', 'Employee benefit expense', 'line', 'm1', data='staff', flow=True)
    S('is_othop', 'Other operating income (expense), net (grants, research tax credit, acquisition fees)', 'line', 'm1', data='oth_op', flow=True)
    S('is_opex', 'Operating expenses before D&A, net (cost of sales + external + taxes + employee − other operating income)', 'line_b', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_cos")}),{V("is_cos")}+{V("is_ext")}+{V("is_taxes")}+{V("is_staff")}-N({V("is_othop")}),"")',
      fc=lambda: f'={V("is_rev")}-{V("r_ebitda")}', note='Forecast implied: revenue − EBITDA (Adjusted EBITDA − share-based payments − one-off costs). The by-nature lines are history only.')
    S('is_dna', 'Depreciation, amortisation, impairment and charges to provisions, net', 'line', 'm1', data='dna_prov', flow=True, fc=lambda: f'={V("d_dna_t")}',
      note='IFRS line (incl. current-asset impairment and provision movements). Forecast = D&A and impairment of non-current assets (provisions assumed nil).')
    S('is_rop', 'Recurring (current) operating profit', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}-{V("is_opex")}-{V("is_dna")},"")')
    S('is_othie', 'Other income and expenses (non-recurring, below recurring operating profit)', 'line', 'm1', data='oth_ie', flow=True, fc=lambda: '=0',
      note='FY24: €3.9m of IPO fees not attributable to the share issue. Forecast nil.')
    S('is_op', 'Operating profit', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_rop")}),{V("is_rop")}+N({V("is_othie")}),"")')
    S('is_op_chk', '  Check: operating profit vs reported (should be 0; ±0.05)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_op_pub")}),IF(ABS({V("is_op")}-{V("is_op_pub")})<=0.05,0,ROUND({V("is_op")}-{V("is_op_pub")},2)),"")')
    S('is_op_pub', '  Memo: operating profit as reported', 'memo', 'm1', data='op', flow=True)
    S('is_opm', '  Operating margin %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('is_cnd', 'Cost of net debt (interest on borrowings and leases)', 'line', 'm1', data='cost_nd', flow=True,
      he=lambda: f'={PT("pt_int")}-{V("is_cnd", H1)}', e26=lambda: S26('is_cnd'), ae=lambda: f'={V("db_int")}',
      note='FY25 €12.1m (3M Euribor + 1.75% margin on the €250m TLB; margin cut to 1.15% in Jun-2026); H1-26 €6.3m. 2027E+: debt schedule (interest on opening balances).')
    S('is_deriv', 'Net gains (losses) on derivative instruments and foreign exchange', 'line', 'm1', data='deriv', flow=True, he_in=0.0, e26=lambda: S26('is_deriv'), ae_in=0.0,
      note='Caps / cross-currency swaps and FX on intragroup balances. Not forecast.')
    S('is_finoth', 'Other financial income (expense) — incl. interest income on cash', 'line', 'm1', data='fin_oth', flow=True, he_in=0.0, e26=lambda: S26('is_finoth'),
      ae=lambda: f'={P("bs_cash")}*{V("ls_yield")}', note='History: interest on deposits, put-option remeasurement, other. 2027E+: opening cash × yield (no circularity).')
    S('is_netfin', 'Net financial income (expense)', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_cnd")}),-{V("is_cnd")}+N({V("is_deriv")})+N({V("is_finoth")}),"")')
    S('is_ebt', 'Profit before tax', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_op")}),{V("is_op")}+{V("is_netfin")},"")')
    S('is_tax', 'Income tax', 'line', 'm1', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}', e26=lambda: S26('is_tax'))
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), he=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='French statutory 25%; FY25 20.4% (loss carry-forwards, MA disposal loss); H1-26 current tax rate 26% (39% reported incl. the brand DTL reversal). H2/26E point estimate; 2027E+ input.')
    S('is_nic', 'Net profit from continuing operations', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_disc', 'Net profit (loss) from discontinued operations (Microwave Amplification)', 'line', 'm1', data='disc', flow=True, he_in=0.0, e26=lambda: S26('is_disc'), ae_in=0.0,
      note='FY25: −€4.4m operating result and −€23.1m loss on disposal (net assets written off; no consideration). FY24 restated −€3.4m.')
    S('is_ni', 'Net profit attributable to shareholders', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_nic")}),{V("is_nic")}+N({V("is_disc")}),"")')
    S('is_ni_chk', '  Check: net profit vs reported (should be 0; ±0.05)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=0.05,0,ROUND({V("is_ni")}-{V("is_ni_pub")},2)),"")')
    S('is_ni_pub', '  Memo: net profit as reported', 'memo', 'm1', data='ni', flow=True)
    S('is_orig', '  Memo: net profit as originally reported (before the IFRS 5 restatement)', 'memo', 'm1', data='orig_ni',
      note='FY24 and H1/25 were restated in the following year\'s filing for the Microwave Amplification disposal; the originally reported figures are kept here (revenue / Adjusted EBITDA memos in the bridge sections).')
    S('eps_hdr', '(Per-share data — ordinary shares; the 119.5m pre-IPO preference shares were converted at the 7-Jun-2024 IPO, so FY2021–23 per-share data are not comparable)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average shares, basic (m)', 'line', 'm2', data='wsh', avg=True,
      he=lambda: f'={V("sh_basic", H1)}', e26=lambda: f'=AVERAGE({H1}{R["sh_basic"]},{H2}{R["sh_basic"]})', ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Published weighted average (excl. treasury shares). H2/26E = H1-26 weighted average; 2027E+: average of opening / closing shares (share schedule).')
    S('sh_dil', '  Weighted-average shares, diluted (m)', 'line', 'm2', all=lambda: f'=IF(ISNUMBER({V("sh_basic")}),{V("sh_basic")}+N({V("ds_dil")}),"")',
      note='Company: dilutive instruments (ExoShare matching, LTIP performance shares) "not material"; diluted EPS = basic as reported. Forecast adds the LTIP shares outstanding (~0.4m).')
    S('eps_basic', 'EPS – basic (€)', 'eps', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_basic")}),IFERROR({V("is_ni")}/{V("sh_basic")},""),"")')
    S('eps_dil', 'EPS – diluted (€)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")')
    S('eps_cont', 'EPS – basic, continuing operations (€)', 'eps', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_basic")}),IFERROR({V("is_nic")}/{V("sh_basic")},""),"")')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – basic as reported (€)', 'eps_memo', 'ps', data='eps_basic')
    S('eps_chk', '  Check: model basic EPS vs reported (should be 0.00; ±0.01; FY24 reported EPS is after the €5.1m preference dividend)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_basic")})),IF(ABS({V("eps_basic")}-N({V("eps_pref")})-{V("eps_pub")})<=0.0101,0,ROUND({V("eps_basic")}-N({V("eps_pref")})-{V("eps_pub")},2)),"")')
    S('eps_pref', '  Memo: preference dividend per share deducted in reported EPS (€)', 'eps_memo', 'ps', hist=lambda: f'=IF(ISNUMBER({V("pref_div")}),IFERROR({V("pref_div")}/{V("sh_basic")},""),"")')
    S('pref_div', '  Memo: preferential dividend attributable to A preference shares (€m)', 'memo', 'm1', data='pref_div')
    S('dps', '  Dividend per share declared for the year (€; paid the following May)', 'line', 'ps', data='dps', he=lambda: f'={V("dps", E26)}',
      e26=lambda: f'=ROUND({V("pay_ratio")}*{V("eps_basic")},2)', ae=lambda: f'=ROUND({V("pay_ratio")}*{V("eps_basic")},2)',
      note='First dividend €0.10 for FY24 (paid May-2025); €0.30 for FY25 (paid Jun-2026). Policy: 20–25% payout of net income. Forecast = payout ratio × basic EPS, paid the following year.')
    S('dps_g', '  DPS y/y %', 'growth', 'pct', all=growth('dps'))
    blank()

    # ------------------------------------------------------------------ RECON 1: EBITDA
    S('sec_r1', 'RECONCILIATION: NET PROFIT → OPERATING PROFIT → EBITDA → ADJUSTED EBITDA → ADJUSTED EBIT (company definition, as published)', 'section',
      note='ADJUSTED EBITDA / EBIT — per the company reconciliation: operating profit + D&A and impairment (net) + other income & expenses = EBITDA; + share-based payments + non-recurring costs = Adjusted EBITDA; − D&A excl. PPA amortisation (and brand impairment) = Adjusted EBIT')
    S('r_ni', 'Net profit from continuing operations', 'line_b', 'm1', all=lambda: f'={V("is_nic")}')
    S('r_tax', '  (+) Income tax', 'line', 'm1', all=lambda: f'={V("is_tax")}')
    S('r_fin', '  (−) Net financial income (expense)', 'line', 'm1', all=lambda: f'=-{V("is_netfin")}')
    S('r_op', '  = Operating profit', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_tax")}+{V("r_fin")},"")')
    S('r_dna', '  (+) Depreciation, amortisation and impairment of non-current assets, net (incl. PPA amortisation, brand impairment, IFRS 16)', 'line', 'm1', data='dna_br', flow=True, fc=lambda: f'={V("d_dna_t")}',
      note='Company bridge line = first two lines of the D&A note (excl. current-asset impairment and provisions, which stay in EBITDA).')
    S('r_othie', '  (+) Other income and expenses (non-recurring, IPO fees 2024)', 'line', 'm1', data='oth_ie_br', flow=True, fc=lambda: f'=-N({V("is_othie")})')
    S('r_ebitda', '  = EBITDA', 'total', 'm1', hist=lambda: f'=IF(AND(ISNUMBER({V("r_op")}),ISNUMBER({V("r_dna")})),{V("r_op")}+{V("r_dna")}+N({V("r_othie")}),"")',
      fc=lambda: f'={V("g_adj")}-{V("d_sbc")}-{V("d_nonrec")}', note='Forecast = Adjusted EBITDA (margin build) − share-based payments − one-offs; the P&L above is derived from it (no circularity).')
    S('r_sbc', '  (+) Share-based payments', 'line', 'm1', all=lambda: f'={V("d_sbc")}')
    S('r_nonrec', '  (+) Non-recurring (one-off) costs', 'line', 'm1', all=lambda: f'={V("d_nonrec")}')
    S('r_oth', '  (+) Other adjustments — share-based payments and non-recurring costs not split (FY2021–22 registration document; H1/23 and H2/23 per the H1-2024 report)', 'line', 'm1',
      data='oth_adj', flow=True, fc=lambda: '=0', note='Printed as one "other restatements" line in the registration document key figures and the H1-2024 bridge.')
    S('r_tot', '  Total adjusting items', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{nsum(["r_sbc", "r_nonrec", "r_oth"])},"")')
    S('r_adj', '  = Adjusted EBITDA (model bridge)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{V("r_ebitda")}+{V("r_tot")},"")',
      note='Rebuilt from the published reconciliation lines; forecast = EBITDA + share-based payments + one-offs (equals the margin build; check in the Group block).')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_adj_pub', '  Company-published Adjusted EBITDA', 'memo', 'm1', data='adj_ebitda_pub', flow=True)
    S('r_adj_chk', '  Check: model bridge vs company-published (should be 0; ±0.25: one-decimal tables, H2 = FY − H1 compounds two roundings)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_adj_pub")}),IF(ABS({V("r_adj")}-{V("r_adj_pub")})<=0.25,0,ROUND({V("r_adj")}-{V("r_adj_pub")},2)),"n/p")')
    S('r_orig', '  Memo: Adjusted EBITDA as originally reported (before the IFRS 5 restatement)', 'memo', 'm1', data='orig_adj_ebitda_pub',
      note='FY24 €118.5m as reported in the FY2024 release vs €119.8m restated (Microwave Amplification lost €1.3m of Adjusted EBITDA in 2024); H1/25 €69.5m vs €70.6m restated.')
    S('r_def', '  Definition basis (company Adjusted EBITDA definition in force)', 'text', 'gen',
      note='Definition unchanged since the IPO registration document; the only basis change is the IFRS 5 restatement of 2024 / H1-25 for the Microwave Amplification disposal (flagged).')
    S('r_ebit_h', 'To Adjusted EBIT (company measure):', 'sub', 'gen')
    S('r_dnax', '  (−) Depreciation, amortisation and impairment excl. PPA amortisation and brand impairment', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("d_dna")}),-{V("d_dna")},"")')
    S('r_ebit', '  = Adjusted EBIT (model bridge)', 'total', 'm1', all=lambda: f'=IF(AND(ISNUMBER({V("r_adj")}),ISNUMBER({V("r_dnax")})),{V("r_adj")}+{V("r_dnax")},"")',
      note='Company Adjusted EBIT = Adjusted EBITDA − D&A other than PPA amortisation (and, in H1-26, the brand impairment). Used for NOPAT / ROIC; the DCF deducts share-based payments and one-offs again (cash / real costs).')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_ebit_pub', '  Company-published Adjusted EBIT', 'memo', 'm1', data='adj_ebit_pub', flow=True)
    S('r_ebit_chk', '  Check: model vs company-published Adjusted EBIT (should be 0; ±0.25 rounding)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("r_ebit_pub")}),ISNUMBER({V("r_ebit")})),IF(ABS({V("r_ebit")}-{V("r_ebit_pub")})<=0.25,0,ROUND({V("r_ebit")}-{V("r_ebit_pub")},2)),"n/p")')
    blank()

    # ------------------------------------------------------------------ RECON 2
    S('sec_r2', 'RECONCILIATION: OPERATING PROFIT → ADJUSTED EBIT (company items only)', 'section',
      note='ADJUSTED EBIT BRIDGE — operating profit + other income & expenses + share-based payments + non-recurring costs + PPA amortisation + brand impairment')
    S('o_op', 'Operating profit (IFRS)', 'line_b', 'm1', all=lambda: f'={V("is_op")}')
    S('o_othie', '  (+) Other income and expenses', 'line', 'm1', all=lambda: f'=N({V("r_othie")})')
    S('o_sbc', '  (+) Share-based payments', 'line', 'm1', all=lambda: f'={V("d_sbc")}')
    S('o_nonrec', '  (+) Non-recurring costs', 'line', 'm1', all=lambda: f'={V("d_nonrec")}')
    S('o_ppa', '  (+) PPA amortisation', 'line', 'm1', all=lambda: f'=N({V("d_ppa")})')
    S('o_brand', '  (+) Brand impairment', 'line', 'm1', all=lambda: f'=N({V("d_brand")})')
    S('o_oth', '  (+) Other adjustments not split (FY2021–22, 2023 halves)', 'line', 'm1', all=lambda: f'=N({V("r_oth")})')
    S('o_adj', '  = Adjusted EBIT (model)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_othie")}+{V("o_sbc")}+{V("o_nonrec")}+{V("o_ppa")}+{V("o_brand")}+{V("o_oth")},"")')
    S('o_adj_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_chk', '  Check: vs company-published Adjusted EBIT (should be 0; ±0.45: H1 PPA amortisation is as printed in the release income statement (H1-25 6.5) while FY PPA is implied by the bridge (38.1 − 24.0), so H2 = FY − H1 carries ~0.2 of definitional rounding; n/p where PPA amortisation is not published)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("r_ebit_pub")}),ISNUMBER({V("d_ppa")})),IF(ABS({V("o_adj")}-{V("r_ebit_pub")})<=0.45,0,ROUND({V("o_adj")}-{V("r_ebit_pub")},2)),"n/p")')
    S('o_adj_g', '  Adjusted EBIT y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental Adjusted EBIT margin (Δ Adjusted EBIT / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 3
    S('sec_r3', 'RECONCILIATION: NET PROFIT → NET PROFIT EXCLUDING PPA AMORTISATION (AND BRAND IMPAIRMENT) → ADJUSTED EPS (company definition)', 'section',
      note='ADJUSTED NET PROFIT — company: net profit from continuing operations excluding the effects of purchase price allocations (PPA amortisation net of deferred tax); from H1-26 also excluding the brand impairment net of tax')
    S('e_ni', 'Net profit from continuing operations', 'line_b', 'm1', all=lambda: f'={V("is_nic")}')
    S('e_ppa', '  (+) PPA amortisation', 'line', 'm1', all=lambda: f'=N({V("d_ppa")})')
    S('e_brand', '  (+) Brand impairment', 'line', 'm1', all=lambda: f'=N({V("d_brand")})')
    S('e_tax', '  (−) Tax effect of adjustments (derived: published adjusted net profit − net profit − items; forecast at the deferred-tax rate on PPA)', 'line', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("e_pub")}),{V("e_pub")}-{V("e_ni")}-{V("e_ppa")}-{V("e_brand")},"")', fc=lambda: f'=-({V("e_ppa")}+{V("e_brand")})*{V("e_rate")}',
      note='Derived from the published figure (FY25: 84.2 − 70.2 − 14.1 = −0.1, i.e. the company adds back PPA amortisation almost gross; H1-26: 43.9 − 15.3 − 7.9 − 28.2 = −7.5, the brand DTL reversal). Forecast: PPA amortisation × deferred-tax rate.')
    S('e_adjni', '  = Net profit from continuing operations excl. PPA & impairment (model bridge)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("e_ni")}),{V("e_ni")}+{V("e_ppa")}+{V("e_brand")}+N({V("e_tax")}),"")')
    S('e_pub', '  Company-published net profit from continuing operations excl. PPA (and impairment)', 'memo', 'm1', data='ni_cont_ex_ppa_pub', flow=True)
    S('e_chk', '  Check: model vs published (should be 0; ±0.15)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("e_pub")}),IF(ABS({V("e_adjni")}-{V("e_pub")})<=0.15,0,ROUND({V("e_adjni")}-{V("e_pub")},2)),"n/p")')
    S('e_pub_all', '  Memo: company-published net profit excl. PPA incl. discontinued operations', 'memo', 'm1', data='ni_ex_ppa_pub', flow=True)
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm2', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted EPS – diluted (€; net profit excl. PPA & impairment ÷ diluted shares; model)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'),
      note='Exosens publishes no adjusted EPS; this is the company net profit excl. PPA measure per diluted share. Used for the P/E in the Bull-Base-Bear tab.')
    S('e_rate', '  Tax rate applied to forecast adjustments (deferred tax on PPA intangibles)', 'pct', 'pct',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_tax")}),ISNUMBER({V("e_ppa")})),IFERROR(-{V("e_tax")}/({V("e_ppa")}+{V("e_brand")}),""),"")',
      he_in=V0['e_rate'], ae_in=V0['e_rate'],
      note='History: implied rate is ~0–1% on PPA (the company adds amortisation back gross in FY24–25) and ~21% on the brand impairment (H1-26). Forecast input 0% keeps the company convention (so the forecast series is comparable with the published history).')
    S('e_def', '  Definition basis (company net profit excl. PPA definition in force)', 'text', 'gen')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Revenue y/y % (reported)', 'growth', 'pct', all=growth('is_rev'))
    S('gm_lfl', '  Revenue y/y % like-for-like (model)', 'growth', 'pct', all=lambda: f'=IF(ISNUMBER({V("g_lfl")}),{V("g_lfl")},"")' if CTX.col.prior else None)
    S('gm_agp', '  Adjusted gross margin y/y %', 'growth', 'pct', all=growth('m_agp'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating profit y/y %', 'growth', 'pct', all=growth('is_op'))
    S('gm_ni', '  Net profit y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_agpm', '  Adjusted gross margin %', 'pct', 'pct', all=ratio('m_agp', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_inc', '  Incremental Adjusted EBITDA margin (ΔEBITDA / Δrevenue)', 'pct', 'pct', all=incr('r_adj', 'is_rev'))
    S('gm_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('gm_op_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_staff', '  Employee benefit expense % of revenue', 'pct', 'pct', all=ratio('is_staff', 'is_rev'))
    blank()
