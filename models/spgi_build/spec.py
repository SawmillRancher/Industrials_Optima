"""Row specification of the SPGI Model sheet, part 1 (MLM template layout and process):
division x revenue-type build (Ratings: transaction / non-transaction; Indices: asset-linked fees / exchange-traded derivatives /
data & custom subscriptions; Energy and Market Intelligence: subscription / non-subscription / royalties or recurring variable)
-> divisional adjusted operating profit at the adjusted margin -> - adjusted corporate unallocated expense + adjusted equity income =
adjusted operating profit -> legacy / divested divisions (Mobility, Engineering Solutions, combined MCI) -> M&A lever -> group total &
FY26 guidance calibration -> cost drivers -> income statement -> GAAP-to-adjusted bridges -> growth & margins."""
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
def EA(key): return f'${E26}${R[key]}'                     # FY2026E column (absolute) - calibration helpers live here
def ACT(key): return f'SUM({Q1}{R[key]}:{Q2}{R[key]})'     # 1H-2026 actual
def ACT0(key): return f'SUM({PQ1}{R[key]}:{PQ2}{R[key]})'  # 1H-2025 (pro forma) actual
def H2(key): return f'SUM({Q3}{R[key]}:{Q4}{R[key]})'      # 2H-2026 estimate
def H2P(key): return f'SUM({PQ3}{R[key]}:{PQ4}{R[key]})'   # 2H-2025 (pro forma)
def B1(key): return f'{LQ}{R[key]}'                        # 30-Jun-2026 balance

# division -> revenue-type lines (key, label, data key, scenario lever)
SEG = [('rat', 'Ratings', 'RAT', [('tr', 'Transaction revenue (new issuance: bonds, bank loans, structured finance)', 'RAT_TR'),
                                  ('nt', 'Non-transaction revenue (surveillance, frequent-issuer programs, Crisil & other)', 'RAT_NT')]),
       ('idx', 'Indices (S&P Dow Jones Indices)', 'IDX', [('alf', 'Asset-linked fees (ETFs, mutual funds, insurance products)', 'IDX_ALF'),
                                                          ('etd', 'Exchange-traded derivatives (sales usage-based royalties)', 'IDX_ETD'),
                                                          ('sub', 'Data & custom subscriptions', 'IDX_SUB')]),
       ('en', 'Energy (Commodity Insights / Platts)', 'CI', [('sub', 'Subscription', 'CI_SUB'), ('ns', 'Non-subscription / transaction (incl. CERAWeek conference)', 'CI_NS'),
                                                             ('roy', 'Sales usage-based royalties', 'CI_ROY')]),
       ('mi', 'Market Intelligence', 'MI', [('sub', 'Subscription', 'MI_SUB'), ('ns', 'Non-subscription / transaction', 'MI_NS'),
                                           ('rv', 'Recurring variable', 'MI_RV')])]
LEVER = {'rat_tr': 'RAT_TR', 'rat_nt': 'RAT_NT', 'idx_alf': 'IDX_ALF', 'idx_etd': 'IDX_ETD', 'idx_sub': 'IDX_SUB',
         'en_sub': 'EN', 'en_ns': 'EN', 'en_roy': 'EN', 'mi_sub': 'MI', 'mi_ns': 'MI', 'mi_rv': 'MI'}
LINES = [f'{s}_{t}' for s, _, _, ts in SEG for t, _, _ in ts]
SEGK = [s for s, *_ in SEG]
CODE = {s: c for s, _, c, _ in SEG}
ITEMS = [('d_sev', 'SEVER', 'Employee severance, restructuring & leadership-transition costs'),
         ('d_acq', 'ACQ', 'Acquisition, merger & integration costs (incl. IHS Markit merger costs)'),
         ('d_disp', 'DISP', 'Disposition & separation costs (incl. Mobility separation)'),
         ('d_gain', 'GAIN', '(Gain) / loss on dispositions'),
         ('d_legal', 'LEGAL', 'Legal settlements & costs (net of insurance recoveries)'),
         ('d_imp', 'IMPAIR', 'Asset, lease & technology impairments'),
         ('d_oth', 'OTHER', 'Other items (non-cash acquisition / disposition adjustments, labor-law accrual, other)')]
OI = [k for k, _, _ in ITEMS]

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
    SCEN_ROWS.append((r, 'pt_hdr', 'Q3/26E–Q4/26E point estimates (all cases; per quarter unless stated)', None, None, None, None)); r += 1
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
    # ------------------------------------------------------------------ DIVISION BUILD
    S('sec_seg', 'DIVISION P&L — RATINGS · INDICES · ENERGY · MARKET INTELLIGENCE (revenue by type × adjusted operating margin)', 'section',
      note='DIVISION BUILD — modelling logic (revenue by type → division revenue → division adjusted OP at the adjusted margin → − adjusted corporate unallocated + adjusted equity income = adjusted OP → GAAP P&L)')
    blank()
    descr = {'rat': 'S&P Global Ratings (credit ratings, research & analytics; Crisil) — "S&P Ratings" 2010–15',
             'idx': 'S&P Dow Jones Indices (73% / 27% JV with CME Group from Jul-2012; S&P DJ Indices to 2015)',
             'en': 'S&P Global Energy — Commodities & Commercial 2010–15 (incl. J.D. Power, Aviation Week, McGraw-Hill Construction while owned); Platts 2018–21; '
                   'Commodity Insights 2022–25; Energy (recast with 451 Research and Maritime & Trade) from 2025',
             'mi': 'S&P Global Market Intelligence — S&P Capital IQ 2010–15; Market Intelligence (SNL from Sep-2015) 2018+; incl. IHS Markit financial services from Mar-2022; '
                   'recast 2025+ (451 Research / Maritime & Trade to Energy)'}
    for s, title, code, types in SEG:
        S(f'{s}_hdr', descr[s], 'block', note=f'{title.upper()} — modelling logic')
        for t, tl, dk in types:
            key = f'{s}_{t}'
            S(key, f'  {tl}', 'line', 'm', data=f't_{dk}', flow=True,
              qe=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})', ae=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})',
              note=('Revenue by type (release revenue-information exhibit; 10-K / 10-Q revenue note). Q3–Q4/26E: prior-year quarter × (1 + growth). '
                    '2027E+: prior year × (1 + scenario lever).') if s == 'rat' and t == types[0][0] else None)
            S(key + '_g', '    y/y %', 'growth', 'pct', all=growth(key),
              qe=lambda key=key: f'={EA(key + "_pre")}+{EA("cal_g")}',
              ae=lambda key=key: '=' + CH(SC[LEVER[key]][CTX.col.year]),
              note='Q3–Q4/26E: 1H-26 y/y growth of the line + revenue-guidance calibration Δ (Group block). 2027E–2031E: scenario lever.' if s == 'rat' and t == types[0][0] else None)
            S(key + '_pre', '    Q3–Q4/26E growth before revenue calibration (1H-26 y/y)', 'driver', 'pct',
              e26=lambda key=key: f'=IFERROR({ACT(key)}/{ACT0(key)}-1,0)')
        first = f'{s}_{types[0][0]}'
        S(f'{s}_nsp', f'  Not split by type (history only: periods without a revenue-by-type table on this basis)', 'line', 'm',
          hist=lambda s=s, types=types, first=first: f'=IF(ISNUMBER({V(s + "_pub")}),{V(s + "_pub")}-({nsum([s + "_" + t for t, _, _ in types])}),"")')
        S(f'{s}_rev', f'  {title} — division revenue', 'line_b', 'm',
          hist=lambda s=s, types=types: f'=IF(ISNUMBER({V(s + "_pub")}),{nsum([s + "_" + t for t, _, _ in types])}+N({V(s + "_nsp")}),"")',
          fc=lambda s=s, types=types: '=' + '+'.join(V(s + '_' + t) for t, _, _ in types),
          note='History: division revenue as reported (Σ revenue types + any unsplit remainder).' if s == 'rat' else None)
        S(f'{s}_rev_g', '  Division revenue y/y %', 'growth', 'pct', all=growth(f'{s}_rev'))
        S(f'{s}_mix', '  % of total revenue', 'pct', 'pct', all=ratio(f'{s}_rev', 'g_rev'))
        S(f'{s}_pub', f'  Memo: {title} revenue as reported (segment exhibit; 2025+ adjusted as recast)', 'memo', 'm', data=f'sr_{code}', flow=True)
        S(f'{s}_chk', '  Check: revenue types vs division revenue (should be 0; ±1 rounding)', 'check', 'm',
          hist=lambda s=s, first=first: f'=IF(AND(ISNUMBER({V(first)}),ISNUMBER({V(s + "_pub")})),IF(ABS({V(s + "_rev")}-{V(s + "_pub")})<=1.01,0,ROUND({V(s + "_rev")}-{V(s + "_pub")},0)),"")')
        S(f'{s}_oi', f'  {title} — adjusted operating profit', 'line', 'm', data=f'sa_{code}', flow=True,
          qe=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}', ae=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}',
          note=('Division adjusted OP (company non-GAAP: OP + non-GAAP adjustments + deal-related amortization). 2025+: pro forma recast basis. Forecast = revenue × adjusted margin.')
          if s == 'rat' else None)
        S(f'{s}_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio(f'{s}_oi', f'{s}_rev'),
          qe=lambda s=s: f'={V(s + "_m_pre")}+{EA("cal_m")}', ae=lambda s=s, code=code: '=' + CH(SC[f'{code}_M'][CTX.col.year]),
          note='Q3–Q4/26E: margin before calibration + adjusted-EPS-guidance calibration Δ (Group block). 2027E+: scenario lever.' if s == 'rat' else None)
        S(f'{s}_m_pre', '  Q3–Q4/26E margin before EPS calibration (prior-year quarter + 1H-26 y/y drift)', 'driver', 'pct',
          qe=lambda s=s: f'={P(s + "_m")}+IFERROR({ACT(s + "_oi")}/{ACT(s + "_rev")}-{ACT0(s + "_oi")}/{ACT0(s + "_rev")},0)')
        S(f'{s}_inc', '  Incremental adjusted margin (Δ adjusted OP / Δ revenue)', 'pct', 'pct', all=incr(f'{s}_oi', f'{s}_rev'))
        S(f'{s}_gop', f'  Memo: {title} — operating profit (GAAP, as reported)', 'memo', 'm', data=f'se_{code}', flow=True)
        blank()
    # ------------------------------------------------------------------ legacy / divested divisions
    S('lg_hdr', 'Spun-off, divested & legacy divisions (history only; not in the forecast)', 'block',
      note='LEGACY — Mobility (Mar-2022 to Jun-2026; spun off as Mobility Global, 1-Jul-2026), Engineering Solutions (Mar-2022 to May-2023, sold to KKR), combined MCI 2016–17')
    for k, lab, code in (('mob', 'Mobility (spun off 1-Jul-2026; 2025+ pro forma excludes it)', 'MOB'), ('es', 'Engineering Solutions (sold 2-May-2023)', 'ES'),
                         ('leg', 'Market & Commodities Intelligence (combined segment 2016–17) and other', 'LEG')):
        S(f'{k}_rev', f'  {lab} — revenue', 'line', 'm', data=f'sr_{code}', flow=True, fc=lambda: '=0')
        S(f'{k}_oi', f'  {lab} — adjusted OP', 'line', 'm', data=f'sa_{code}', flow=True, fc=lambda: '=0')
        S(f'{k}_gop', '    Memo: operating profit (GAAP)', 'memo', 'm', data=f'se_{code}', flow=True)
    S('elim', '  Intersegment elimination (Ratings content licensed to Market Intelligence)', 'line', 'm', data='elim', flow=True,
      qe=lambda: f'={P("elim")}*(1+{EA("elim_g")})', ae=lambda: f'={P("elim")}*(1+{V("mi_rev_g")})')
    S('elim_g', '  Elimination y/y % (Q3–Q4/26E: 1H-26 y/y; 2027E+: with Market Intelligence revenue)', 'driver', 'pct', all=growth('elim'),
      e26=lambda: f'=IFERROR({ACT("elim")}/{ACT0("elim")}-1,0)')
    blank()
    S('co_hdr', 'Corporate unallocated expense & equity income (OSTTRA 50% JV with CME to Oct-2025)', 'block',
      note='CORPORATE — unallocated corporate costs; adjusting items are recorded here (merger, disposition, separation costs, gains)')
    S('corp', '  Adjusted corporate unallocated expense (cost +)', 'line', 'm', data='adj_corp', flow=True,
      qe=lambda: f'={PT("pt_corp")}', ae=lambda: f'={V("is_rev")}*{V("corp_pct")}',
      note='Company adjusted corporate unallocated expense (2025+: pro forma recast, after the Mobility TSA income). Q3–Q4/26E: FY26 guidance $185–195m less 1H actual, split evenly. 2027E+: % of revenue.')
    S('corp_pct', '  Adjusted corporate unallocated % of revenue', 'pct', 'pct', all=ratio('corp', 'is_rev'), ae_in=V0['corp_pct'])
    S('corp_gaap', '  Memo: corporate unallocated expense (GAAP, as reported)', 'memo', 'm', data='corp', flow=True)
    S('aeq', '  Adjusted equity income on unconsolidated subsidiaries (OSTTRA; sold Q4-2025)', 'line', 'm', data='adj_eq', flow=True, fc=lambda: '=0')
    blank()
    S('mx_hdr', 'Mix & contribution (outputs)', 'block', note='MIX — outputs')
    S('mx_tr', '  Ratings transaction revenue % of Ratings', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("rat_tr")}),IFERROR({V("rat_tr")}/{V("rat_rev")},""),"")')
    S('mx_alf', '  Indices asset-linked fees % of Indices', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("idx_alf")}),IFERROR({V("idx_alf")}/{V("idx_rev")},""),"")')
    S('mx_rec', '  Recurring share (subscription + non-transaction + recurring variable + asset-linked) % of revenue', 'pct', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("rat_nt")}),ISNUMBER({V("en_sub")}),ISNUMBER({V("mi_sub")})),IFERROR(({V("rat_nt")}+{V("idx_alf")}+{V("idx_sub")}+{V("en_sub")}+{V("mi_sub")}+{V("mi_rv")})/{V("g_rev")},""),"")'))
    for s, title, *_ in SEG:
        S(f'gc_{s}', f'  Contribution to total revenue growth — {title.split(" (")[0]} (pp)', 'growth', 'pct',
          all=lambda s=s: (f'=IF(AND(ISNUMBER({V(s + "_rev")}),ISNUMBER({P(s + "_rev")})),IFERROR(({V(s + "_rev")}-{P(s + "_rev")})/{P("g_rev")},""),"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — bolt-ons across the divisions, unallocated; deals closed from 2027E)', 'block',
      note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention; amortization of acquired intangibles is deal-related (adjusted out)')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / revenue (x)', 'driver', 'x2', ae_in=8.0, e26_in=0.0,
      note='Assumption: data / analytics bolt-ons at ~8x revenue (With Intelligence, Nov-2025, ~$1.8bn; Visible Alpha 2024; ProntoNLP, TeraHelix, Enertel AI small).')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.08)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}', note='Mid-year convention.')
    S('m_m', '  Adjusted operating margin of acquired businesses %', 'driver', 'pct', e26_in=0.0, ae_in=0.30)
    S('m_oi', '  Adjusted OP from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.35,
      note='IHS Markit PPA: intangibles $18.2bn of ~$44bn consideration (~41%); bolt-on data businesses typically 30–40% (assumption 35%).')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=15)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (deal-related; adjusted out)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group Total — revenue & adjusted operating profit (division build) → FY26 guidance calibration (continuing operations, excluding Mobility)', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Revenue (division build)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("rat_rev")}),{V("rat_rev")}+{V("idx_rev")}+N({V("en_rev")})+N({V("mi_rev")})+N({V("mob_rev")})+N({V("es_rev")})+N({V("leg_rev")})+N({V("elim")}),{V("is_rev")})',
      fc=lambda: f'={V("rat_rev")}+{V("idx_rev")}+{V("en_rev")}+{V("mi_rev")}+{V("elim")}+N({V("m_rev")})',
      note='Σ divisions (+ legacy / divested divisions in history) + intersegment elimination (+ future acquisitions from 2027E).')
    S('g_rev_g', '  Revenue y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: division build vs consolidated revenue (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=1.01,0,ROUND({V("g_rev")}-{V("is_rev")},0)),"")')
    S('g_adj', 'Adjusted operating profit (division build)', 'total', 'm',
      all=lambda: (f'=IF(ISNUMBER({V("rat_oi")}),{V("rat_oi")}+{V("idx_oi")}+N({V("en_oi")})+N({V("mi_oi")})+N({V("mob_oi")})+N({V("es_oi")})+N({V("leg_oi")})'
                   f'-N({V("corp")})+N({V("aeq")})+N({V("m_oi")})+N({V("g_res")}),"")'),
      note='Σ division adjusted OP − adjusted corporate unallocated + adjusted equity income (+ future acquisitions) (+ company rounding residual). Drives the GAAP P&L below.')
    S('g_res', '  Company rounding / definitional residual (published adjusted OP − Σ published components; history only)', 'line', 'm', data='g_res', flow=True)
    S('g_adjm', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('g_adj', 'is_rev'))
    S('g_adj_g', '  Adjusted operating profit y/y %', 'growth', 'pct', all=growth('g_adj'))
    S('g_chk_adj', '  Check: division build vs adjusted OP bridge (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_adj")}),ISNUMBER({V("o_adj")})),IF(ABS({V("g_adj")}-{V("o_adj")})<=1.01,0,ROUND({V("g_adj")}-{V("o_adj")},0)),"")')
    S('cal_guid', '  Memo: FY26 revenue guidance (scenario end-point = FY2025 pro forma revenue × (1 + guided growth))', 'memo', 'm',
      e26=lambda: f'={Y("is_rev", 2025)}*(1+{CH(SC["out_g"])})', note=V0['rev_guid_note'])
    S('cal_pre', '  2H-26 revenue before calibration (FY2026E helper; excl. elimination)', 'line', 'm',
      e26=lambda: '=' + '+'.join(f'({PQ3}{R[k]}+{PQ4}{R[k]})*(1+{V(k + "_pre")})' for k in LINES))
    S('cal_sens', '  2H-26 revenue sensitivity to +1.00 of growth (FY2026E helper)', 'line', 'm', e26=lambda: '=' + '+'.join(H2P(k) for k in LINES))
    S('cal_g', '  Guidance calibration: Δ y/y growth applied to all revenue lines (Q3–Q4/26E)', 'driver', 'pct',
      e26=lambda: f'=({V("cal_guid")}-{ACT("g_rev")}-{V("cal_pre")}-{H2("elim")})/{V("cal_sens")}',
      note='Solves the uniform growth shift (vs 1H-26 y/y rates) so that FY26 revenue = the guidance end-point for the active scenario.')
    S('cal_rev_chk', '  Check: FY26 revenue vs guidance end-point (should be 0)', 'check', 'm', e26=lambda: f'=ROUND({V("g_rev")}-{V("cal_guid")},1)')
    S('cal_eps', '  Memo: FY26 adjusted EPS guidance (scenario end-point, $)', 'eps_memo', 'ps', e26=lambda: '=' + CH(SC['out_eps']), note=V0['eps_guid_note'])
    S('cal_ni', '  2H-26 adjusted net income required (FY diluted shares × EPS guidance − 1H actual)', 'memo_calc', 'm',
      e26=lambda: f'={V("cal_eps")}*{V("e_sh")}-{ACT("e_adjni")}')
    S('cal_t', '  2H-26 adjusted tax rate (point estimate)', 'memo_calc', 'pct', e26=lambda: f'={PT("pt_etr")}')
    S('cal_r', '  NCI ratio to Indices adjusted OP (Q3–Q4/26E input)', 'memo_calc', 'pct', e26=lambda: f'={Q3}{R["nci_r"]}')
    S('cal_pre_oi', '  2H-26 adjusted OP before margin calibration (FY2026E helper)', 'line', 'm',
      e26=lambda: '=' + '+'.join(f'{Q3}{R[s + "_rev"]}*{Q3}{R[s + "_m_pre"]}+{Q4}{R[s + "_rev"]}*{Q4}{R[s + "_m_pre"]}' for s in SEGK) + f'-{H2("corp")}')
    S('cal_pre_idx', '  2H-26 Indices adjusted OP before calibration (FY2026E helper)', 'line', 'm',
      e26=lambda: f'={Q3}{R["idx_rev"]}*{Q3}{R["idx_m_pre"]}+{Q4}{R["idx_rev"]}*{Q4}{R["idx_m_pre"]}')
    S('cal_segrev', '  2H-26 division revenue (FY2026E helper)', 'line', 'm', e26=lambda: '=' + '+'.join(H2(s + '_rev') for s in SEGK))
    S('cal_nonop', '  2H-26 adjusted other income − adjusted interest (FY2026E helper)', 'line', 'm', e26=lambda: f'={H2("is_oth")}-{H2("e_int")}')
    S('cal_m', '  Guidance calibration: Δ division adjusted margin (Q3–Q4/26E)', 'driver', 'pct',
      e26=lambda: (f'=({V("cal_ni")}+{V("cal_r")}*{V("cal_pre_idx")}-({V("cal_pre_oi")}+{V("cal_nonop")})*(1-{V("cal_t")}))'
                   f'/({V("cal_segrev")}*(1-{V("cal_t")})-{V("cal_r")}*{H2("idx_rev")})'),
      note=('Closed-form solve: 2H adjusted NI = (adjusted OP + other income − adjusted interest) × (1 − t) − NCI, with NCI = ratio × Indices adjusted OP and adjusted OP = pre-calibration OP + Δ × division revenue. '
            'Solves the uniform margin shift so that FY26 adjusted EPS = the guidance end-point for the active scenario.'))
    S('cal_eps_chk', '  Check: FY26 adjusted EPS vs guidance end-point (should be 0.00)', 'check', 'ps', e26=lambda: f'=ROUND({V("e_eps")}-{V("cal_eps")},2)')
    S('cal_geps', '  Memo: FY26 GAAP diluted EPS guidance, continuing operations (scenario end-point) — information, not forced', 'eps_memo', 'ps', e26=lambda: '=' + CH(SC['out_geps']))
    S('cal_geps_d', '    Model GAAP EPS (continuing operations) − guidance ($)', 'memo_calc', 'ps', e26=lambda: f'={V("eps_cont")}-{V("cal_geps")}')
    S('cal_mx', '  Memo: FY26 adjusted margin expansion guidance (bp, scenario end-point) — information', 'memo', 'gen', e26=lambda: '=' + CH(SC['out_m']))
    S('cal_mx_d', '    Model adjusted margin expansion vs FY2025 pro forma (bp)', 'memo_calc', 'gen', e26=lambda: f'=ROUND(({V("o_adj_m")}-{Y("o_adj_m", 2025)})*10000,0)')
    S('cal_og', '  Memo: FY26 organic constant-currency growth guidance 6–8% (information; model total growth incl. M&A / divestitures / FX)', 'memo', 'pct', e26=lambda: '=' + CH(SC['out_og']))
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A & adjusting items', 'block', note='COST DRIVERS — inputs that drive forecast cost lines (Q3–Q4/26E: point estimates from guidance; 2027E+: % of revenue or schedules)')
    S('d_dep', '  Depreciation', 'line', 'm', data='dep', flow=True, qe=lambda: f'={PT("pt_dep")}', ae=lambda: f'={V("is_rev")}*{V("d_dep_pct")}')
    S('d_dep_pct', '  Depreciation % of revenue', 'pct', 'pct', all=ratio('d_dep', 'is_rev'), ae_in=V0['dep_pct'])
    S('d_amort', '  Deal-related amortization (amortization of acquired intangibles in OP; adjusted out)', 'line', 'm', data='deal_amort', flow=True,
      qe=lambda: f'={PT("pt_amort")}', ae=lambda: f'={V("d_amort_sch")}+N({V("m_amort")})',
      note='Company "deal-related amortization" (incl. OSTTRA equity-method amortization to 2025). Q3–Q4/26E: FY26 guidance ~$785m less 1H, split evenly. 2027E+: 10-K schedule ex-Mobility + future M&A.')
    S('d_amort_sch', '  Amortization schedule ex-Mobility (FY2025 10-K schedule − Mobility $303m; input)', 'driver', 'm', ae_in=V0['amort_sched'], note=V0['amort_note'])
    S('d_opr', '  Operating-related expenses % of revenue', 'pct', 'pct', all=ratio('is_opr', 'is_rev'),
      qe=lambda: f'={P("d_opr")}+IFERROR({ACT("is_opr")}/{ACT("is_rev")}-{ACT0("is_opr")}/{ACT0("is_rev")},0)', ae_in=V0['opr_pct'],
      note='Q3–Q4/26E: prior-year quarter ratio + 1H-26 y/y drift; 2027E+ input. Selling & general expenses are implied (OP from the adjusted build).')
    S('d_sbc', '  Stock-based compensation (cash-flow statement)', 'line', 'm', data='cf_sbc', flow=True,
      qe=lambda: f'={P("d_sbc")}*(1+IFERROR({ACT("d_sbc")}/{ACT0("d_sbc")}-1,0))', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}',
      note='Q3–Q4/26E: prior-year quarter × 1H y/y; 2027E+: % of revenue. S&P Global does not adjust out stock-based compensation. 2025–1H26 as reported (incl. Mobility).')
    S('d_sbc_pct', '  Stock-based compensation % of revenue', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_adj_h', '  Non-GAAP adjustments in operating profit (pre-tax, added back by the company; forecast inputs):', 'sub', 'gen')
    for k, cat, lab in ITEMS:
        kw = dict(data=f'oa_{cat}', flow=True, labkey=f'oa_{cat}_lab')
        if k == 'd_sev': kw.update(qe=lambda: f'={PT("pt_sev")}', ae_in=V0['ae_sev'], note='Q3–Q4/26E point estimate; 2027E+ input (assumption: ongoing restructuring ~0.3% of revenue).')
        elif k == 'd_acq': kw.update(qe_in=0.0, ae=lambda: f'={V("m_spend")}*{V("d_acq_pct")}')
        elif k == 'd_disp': kw.update(qe=lambda: f'={PT("pt_disp")}', ae_in=0.0, note='Q3–Q4/26E: remaining Mobility separation / geoscience disposition costs (assumption).')
        elif k == 'd_gain': kw.update(qe=lambda: (f'={PT("pt_gain")}' if CTX.col.q == 4 else '=0'), ae_in=0.0, note=V0['gain_note'])
        else: kw.update(fc=lambda: '=0')
        S(k, f'  {lab}', 'line', 'm', **kw)
    S('d_acq_pct', '  Acquisition & integration costs % of acquisition spend', 'pct', 'pct', ae_in=0.02)
    S('d_nonop', '  Non-GAAP adjustments below operating profit (premium amortization benefit on IHS Markit notes, pension / investment items)', 'line', 'm',
      data='nonop', flow=True, qe=lambda: f'=-{PT("pt_prem")}', ae=lambda: f'=-{PT("pt_prem")}*4', labkey='nonop_lab',
      note='Interest-expense premium amortization benefit (fair-value step-up on assumed IHS Markit notes; $6m a quarter) is removed in adjusted interest. Forecast continues at $6m a quarter (assumption).')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF INCOME (US GAAP; continuing operations — 2025 and 1H-26 pro forma excluding Mobility)', 'section',
      note='CONSOLIDATED IS — forecast logic (OP = adjusted OP − deal amortization − non-GAAP adjustments; selling & general expenses implied)')
    S('is_rev', 'Revenue', 'total', 'm', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the division build.')
    S('is_opr', 'Operating-related expenses', 'line', 'm', data='op_rel', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_opr")}')
    S('is_sga', 'Selling and general expenses', 'line', 'm', data='sga', flow=True,
      fc=lambda: f'={V("is_rev")}-{V("is_opr")}-{V("is_dep")}-{V("is_amort")}+{V("is_gain")}+{V("is_eq")}-{V("is_op")}',
      note='Forecast = implied balancing line (revenue − other expenses + gains + equity income − OP from the adjusted build). Includes non-GAAP adjustments other than gains.')
    S('is_dep', 'Depreciation', 'line', 'm', data='dep', flow=True, fc=lambda: f'={V("d_dep")}')
    S('is_amort', 'Amortization of intangibles', 'line', 'm', data='amort', flow=True, fc=lambda: f'={V("d_amort")}',
      note='IS amortization (forecast = deal-related amortization; history differs by OSTTRA equity-method amortization and small non-deal items).')
    S('is_exp', 'Total expenses', 'line_b', 'm', data='exp', flow=True,
      fc=lambda: f'={V("is_opr")}+{V("is_sga")}+{V("is_dep")}+{V("is_amort")}')
    S('is_exp_chk', '  Check: expense lines vs total expenses (should be 0; history where the lines are published)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("is_opr")}),ISNUMBER({V("is_exp")})),IF(ABS({V("is_opr")}+{V("is_sga")}+{V("is_dep")}+{V("is_amort")}-{V("is_exp")})<=1.01,0,ROUND({V("is_opr")}+{V("is_sga")}+{V("is_dep")}+{V("is_amort")}-{V("is_exp")},0)),"")')
    S('is_gain', 'Gain (loss) on dispositions (income +; FY2010–12 "other income" inside OP)', 'line', 'm', data='gain', flow=True, fc=lambda: f'=-{V("d_gain")}')
    S('is_eq', 'Equity in income on unconsolidated subsidiaries (OSTTRA)', 'line', 'm', data='eq_inc', flow=True, fc=lambda: f'={V("aeq")}')
    S('is_op', 'Operating profit', 'total', 'm', data='op', flow=True,
      fc=lambda: f'={V("g_adj")}-{V("d_amort")}-({nsum(OI)})',
      note='Forecast = adjusted OP (division build) − deal-related amortization − non-GAAP adjustments (gains enter with a negative sign).')
    S('is_op_chk', '  Check: revenue − expenses + gains + equity income = operating profit (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("is_exp")}),ISNUMBER({V("is_op")})),IF(ABS({V("is_rev")}-{V("is_exp")}+N({V("is_gain")})+N({V("is_eq")})-{V("is_op")})<=1.01,0,ROUND({V("is_rev")}-{V("is_exp")}+N({V("is_gain")})+N({V("is_eq")})-{V("is_op")},0)),"")')
    S('is_op_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('is_oth', 'Other income (expense), net (income +; pension and investment items)', 'line', 'm', data='oth_inc', flow=True,
      qe=lambda: f'={PT("pt_oth")}', ae_in=V0['oth_ae'])
    S('is_int', 'Interest expense, net', 'line', 'm', data='int', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_rev")}*{V("ds_r_rev")}-{P("cf_end")}*{V("ds_r_cash")}+{V("ds_fees")}-{PT("pt_prem")}*4',
      note='Q3–Q4/26E: FY26 GAAP guidance $365–385m less 1H, split evenly. 2027E+ = coupon on opening notes + CP rate × opening CP − yield × opening cash + fees − premium amortization benefit (no circularity).')
    S('is_ebt', 'Income from continuing operations before taxes', 'line_b', 'm', data='ebt', flow=True,
      fc=lambda: f'={V("is_op")}+{V("is_oth")}-{V("is_int")}')
    S('is_ebt_chk', '  Check: OP + other income − interest = income before taxes (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_ebt")}),IF(ABS({V("is_op")}+N({V("is_oth")})-N({V("is_int")})-{V("is_ebt")})<=1.01,0,ROUND({V("is_op")}+N({V("is_oth")})-N({V("is_int")})-{V("is_ebt")},0)),"")')
    S('is_tax', 'Provision for taxes on income', 'line', 'm', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Q3–Q4/26E: FY26 guided 22–23% (mid-point). 2027E+: input.')
    S('is_nic', 'Net income from continuing operations', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_nci', '  Less: net income attributable to noncontrolling interests (CME Group 27% of S&P DJI; other)', 'line', 'm', data='nci', flow=True,
      fc=lambda: f'={V("idx_oi")}*{V("nci_r")}')
    S('nci_r', '  NCI ratio to Indices adjusted OP', 'driver', 'pct', all=ratio('is_nci', 'idx_oi'),
      qe=lambda: f'=IFERROR({ACT("is_nci")}/{ACT("idx_oi")},0)', ae=lambda: f'={EA("nci_r")}',
      note='Q3–Q4/26E: 1H-26 ratio; 2027E+: held at the FY2026E ratio.')
    S('is_nicattr', 'Net income from continuing operations attributable to S&P Global', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_nic")}),{V("is_nic")}-{V("is_nci")},"")')
    S('is_disc', 'Income from discontinued operations, net (McGraw-Hill Education 2010–13; Mobility 2025–1H26 incl. pro forma TSA adjustment)', 'line', 'm', data='disc', flow=True,
      fc=lambda: '=0', note='2025 and 1H-26: reported net income attributable − pro forma continuing net income attributable (Mobility results, separation costs and the pro forma Transition Services Agreement adjustment).')
    S('is_ni', 'Net income attributable to S&P Global', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_nicattr")}),{V("is_nicattr")}+N({V("is_disc")}),"")')
    S('is_ni_chk', '  Check: net income attributable vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=1.01,0,ROUND({V("is_ni")}-{V("is_ni_pub")},0)),"")')
    S('is_ni_pub', '  Memo: net income attributable to S&P Global as reported', 'memo', 'm', data='ni_attr', flow=True)
    S('is_dda', '  Memo: depreciation & amortization (IS)', 'memo_calc', 'm', all=lambda: f'=IF(ISNUMBER({V("is_dep")}),{V("is_dep")}+{V("is_amort")},"")')
    S('is_sbc', '  Memo: stock-based compensation', 'memo_calc', 'm', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: (f'={B1("bs_shares")}-{EA("bb_sh")}*0.25' if CTX.col.q == 3 else f'={B1("bs_shares")}-{EA("bb_sh")}*0.75'),
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q3/26E: shares at 30-Jun-2026 − ¼ of 2H buybacks; Q4/26E: − ¾ (2H buyback spread evenly). 2027E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q2}{R["sh_dil"]}-{Q2}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_cont', 'EPS – diluted, continuing operations ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_nicattr")}/{V("sh_dil")},""),"")',
      note='2025 and 1H-26: pro forma continuing operations excluding Mobility.')
    S('eps_dil', 'EPS – diluted, net income ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")')
    S('eps_dil_g', '  EPS – diluted (continuing) y/y %', 'growth', 'pct', all=growth('eps_cont'))
    S('eps_pub', '  Memo: EPS – diluted (net income) as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.02 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0201,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('dps', '  Dividends declared per share ($)', 'line', 'ps', data='dps', flow=True, qe_in=V0['dps_q'],
      ae=lambda: f'={P("dps")}*(1+{V("dps_g")})', note='Quarterly dividend $0.97 (2026). 2027E+: prior year × (1 + growth). FY2012 excludes the $2.50 special dividend.')
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'])
    blank()

    # ------------------------------------------------------------------ RECON 1: OP -> adjusted OP
    S('sec_r1', 'RECONCILIATION: OPERATING PROFIT → ADJUSTED OPERATING PROFIT (company definition, as published)', 'section',
      note='ADJUSTED OP — per the release "Reported vs Adjusted" exhibits; company item wording per period in the cell comments of the cost-driver rows')
    S('o_op', 'Operating profit (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_op")}')
    for k, cat, lab in ITEMS:
        S('o_' + k[2:], f'  (+) {lab}', 'line', 'm', all=lambda k=k: f'={V(k)}')
    S('o_tot', '  Total non-GAAP adjustments in OP (pre-tax)', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_sev")}),{nsum(["o_" + k[2:] for k in OI])},"")')
    S('o_amort', '  (+) Deal-related amortization', 'line', 'm', all=lambda: f'={V("d_amort")}')
    S('o_adj', '  = Adjusted operating profit (model bridge)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("o_op")}),ISNUMBER({V("o_tot")}),ISNUMBER({V("o_amort")})),{V("o_op")}+{V("o_tot")}+{V("o_amort")},"")',
      note='Rebuilt from the published reconciliation items; forecast = OP + adjustments + deal amortization (equals the division build — check in the Group block).')
    S('o_adj_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company-published adjusted operating profit', 'memo', 'm', data='adj_op_pub', flow=True)
    S('o_chk', '  Check: model bridge vs company-published (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("o_pub")}),ISNUMBER({V("o_adj")})),IF(ABS({V("o_adj")}-{V("o_pub")})<=1.01,0,ROUND({V("o_adj")}-{V("o_pub")},0)),"n/p")')
    S('o_def', '  Definition / basis (company adjusted definition in force)', 'text', 'gen',
      note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('o_adj_g', '  Adjusted OP y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental adjusted margin (Δ adjusted OP / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: NI -> EBITDA -> adjusted EBITDA
    S('sec_r2', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (model definition; S&P Global publishes no EBITDA)', 'section',
      note='EBITDA (model) — net income from continuing operations + taxes + interest − other income + depreciation + amortization; + non-GAAP adjustments = adjusted EBITDA = adjusted OP + depreciation')
    S('r_ni', 'Net income from continuing operations (incl. NCI)', 'line_b', 'm', all=lambda: f'={V("is_nic")}')
    S('r_tax', '  (+) Provision for taxes', 'line', 'm', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest expense, net', 'line', 'm', all=lambda: f'={V("is_int")}')
    S('r_oth', '  (−) Other income, net', 'line', 'm', all=lambda: f'=-N({V("is_oth")})')
    S('r_gop', '  = Operating profit', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_tax")}+N({V("r_int")})+{V("r_oth")},"")')
    S('r_dep', '  (+) Depreciation', 'line', 'm', all=lambda: f'={V("is_dep")}')
    S('r_amort', '  (+) Amortization of intangibles', 'line', 'm', all=lambda: f'={V("is_amort")}')
    S('r_ebitda', '  = EBITDA (model)', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_gop")}),ISNUMBER({V("r_dep")})),{V("r_gop")}+{V("r_dep")}+{V("r_amort")},"")')
    S('r_adjx', '  (+) Non-GAAP adjustments in OP (pre-tax)', 'line', 'm', all=lambda: f'={V("o_tot")}')
    S('r_eqa', '  (+) Deal-related amortization outside the IS amortization line (equity-method OSTTRA amortization, rounding)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("d_amort")}),{V("d_amort")}-N({V("is_amort")}),"")')
    S('r_adj', '  = Adjusted EBITDA (model: adjusted OP + depreciation)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda")}),ISNUMBER({V("r_adjx")})),{V("r_ebitda")}+{V("r_adjx")}+N({V("r_eqa")}),"")',
      note='Model definition, labelled as such (no company EBITDA measure). Used for leverage (net debt / adjusted EBITDA) and EV / EBITDA.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_chk', '  Check: adjusted EBITDA − (adjusted OP + depreciation) (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_adj")}),ISNUMBER({V("o_adj")})),IF(ABS({V("r_adj")}-{V("o_adj")}-{V("is_dep")})<=1.01,0,ROUND({V("r_adj")}-{V("o_adj")}-{V("is_dep")},0)),"")')
    S('r_ebit_h', 'To adjusted EBIT for NOPAT (standard basis: before acquired-intangible amortization, after SBC and cash restructuring):', 'sub', 'gen')
    S('r_ebit', '  Adjusted EBITA (= adjusted OP: after depreciation and SBC, before deal amortization)', 'total', 'm', all=lambda: f'={V("o_adj")}')
    S('r_ebit_m', '  Adjusted EBITA margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: severance, acquisition, disposition & legal costs (cash costs adjusted out; deducted in the DCF)', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_sev")}),{V("o_sev")}+{V("o_acq")}+{V("o_disp")}+{V("o_legal")},"")')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: NET INCOME / DILUTED EPS → ADJUSTED NET INCOME → ADJUSTED DILUTED EPS (company definition)', 'section',
      note='ADJUSTED EPS — GAAP net income attributable (continuing operations from 2025) + non-GAAP adjustments + deal-related amortization (pre-tax) − tax effect')
    S('e_ni', 'Net income attributable (bridge start: continuing operations where the company starts there)', 'line_b', 'm', data='start_ni', flow=True,
      fc=lambda: f'={V("is_nicattr")}', note='As published: total net income attributable 2013–24 (continuing operations in 2013 and 2025+ pro forma).')
    S('e_op', '  (+) Non-GAAP adjustments in OP (pre-tax)', 'line', 'm', all=lambda: f'={V("o_tot")}')
    S('e_amort', '  (+) Deal-related amortization (pre-tax)', 'line', 'm', all=lambda: f'={V("d_amort")}')
    S('e_nonop', '  (+) Adjustments below OP (pre-tax: premium amortization benefit, pension / investment items)', 'line', 'm', all=lambda: f'={V("d_nonop")}')
    S('e_tax', '  (−) Tax effect of the adjustments & discrete tax items (incl. NCI share, rounding)', 'line', 'm', flow=True,
      hist=lambda: (f'=IF(ISNUMBER({V("e_pubni")}),{V("e_pubni")}-{V("e_ni")}-N({V("e_op")})-N({V("e_amort")})-N({V("e_nonop")}),'
                    f'IF(ISNUMBER({V("e_modni")}),{V("e_modni")}-{V("e_ni")}-N({V("e_op")})-N({V("e_amort")})-N({V("e_nonop")}),""))'),
      fc=lambda: f'=-({V("e_op")}+{V("e_amort")}+{V("e_nonop")})*{V("is_etr")}',
      note='Historical: published adjusted net income − bridge start − pre-tax items (derived). Forecast: pre-tax items × tax rate.')
    S('e_adjni', '  = Adjusted net income attributable (model bridge)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("e_tax")}),{V("e_ni")}+N({V("e_op")})+N({V("e_amort")})+N({V("e_nonop")})+{V("e_tax")},"")')
    S('e_pubni', '  Company-published adjusted net income attributable', 'memo', 'm', data='adj_ni_pub', flow=True)
    S('e_modni', '  Memo: actual-scope adjusted net income where the company published only IHS Markit pro forma figures (Q1-22: GAAP + published after-tax items; FY2022: Σ quarters)',
      'memo', 'm', data='adj_ni_mod', flow=True)
    S('e_sh', '  Weighted-average diluted shares (m; company adjusted count where it differs, e.g. loss quarter Q4-14)', 'line', 'm1', data='adj_sh_d',
      all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted diluted EPS ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted diluted EPS ($)', 'eps_memo', 'ps', data='e_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.02 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0201,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_orig', '  Memo: adjusted diluted EPS as originally published (2025–1H26 including Mobility)', 'eps_memo', 'ps', data='e_pub_orig')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_int', '  Adjusted interest expense, net (GAAP interest + premium amortization benefit removed)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_int")}),{V("is_int")}-N({V("d_nonop")}),"")')
    S('e_adjebt', '  Adjusted income before taxes (adjusted OP + other income − adjusted interest)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_adj")}),{V("o_adj")}+N({V("is_oth")})-N({V("e_int")}),"")')
    S('e_adjtax', '  Adjusted provision for taxes (derived: adjusted EBT − NCI − adjusted net income)', 'line', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("e_adjni")}),ISNUMBER({V("e_adjebt")})),{V("e_adjebt")}-N({V("is_nci")})-{V("e_adjni")},"")')
    S('e_rate', '  Adjusted effective tax rate', 'pct', 'pct', all=ratio('e_adjtax', 'e_adjebt'))
    S('e_def', '  Definition / basis (company adjusted EPS definition)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ pro forma memo
    S('pf_hdr', 'Memo: pro forma continuing operations excluding Mobility (Article 11; 8-K/A 6-Jul-2026) — annual', 'block',
      note='PRO FORMA MEMO — FY2023–FY2024 are published only as annual pro forma statements; the main rows keep FY2023–24 as reported (incl. Mobility)')
    S('pf_rev', '  Pro forma revenue', 'memo', 'm', data='pf_rev', flow=True)
    S('pf_op', '  Pro forma operating profit', 'memo', 'm', data='pf_op', flow=True)
    S('pf_ni', '  Pro forma net income from continuing operations attributable', 'memo', 'm', data='pf_ni', flow=True)
    S('pf_g', '  Pro forma revenue y/y %', 'growth', 'pct', all=growth('pf_rev'))
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Revenue y/y %', 'growth', 'pct', all=growth('is_rev'))
    for s, title, *_ in SEG:
        S(f'gm_{s}', f'  {title.split(" (")[0]} revenue y/y %', 'growth', 'pct', all=growth(f'{s}_rev'))
    S('gm_adjop', '  Adjusted OP y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating profit (GAAP) y/y %', 'growth', 'pct', all=growth('is_op'))
    S('gm_ni', '  Net income from continuing operations attributable y/y %', 'growth', 'pct', all=growth('is_nicattr'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_adjop_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_inc', '  Incremental adjusted margin (Δ adjusted OP / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('gm_net_m', '  Net margin (continuing, attributable) %', 'pct', 'pct', all=ratio('is_nicattr', 'is_rev'))
    S('gm_opr', '  Operating-related expenses % of revenue', 'pct', 'pct', all=ratio('is_opr', 'is_rev'))
    S('gm_sga', '  Selling & general expenses % of revenue', 'pct', 'pct', all=ratio('is_sga', 'is_rev'))
    blank()
