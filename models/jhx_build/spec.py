"""Row specification of the JHX Model sheet, part 1 (MLM template layout and process):
segment build (Siding & Trim / Deck, Rail & Accessories / Australia & New Zealand / Europe (discontinued from FY27)) -> corporate ->
group net sales & Adjusted EBITDA with the FY27 planning-assumption calibration (Q3 FY27 guide; Q4 = FY guide - 9M) -> AZEK memo ->
cost drivers -> income statement -> GAAP-to-adjusted bridges (Adjusted EBITDA, Adjusted EBIT, Adjusted net income / EPS) -> growth & margins."""
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
def H1(key): return f'({Q1}{R[key]}+{Q2}{R[key]})'                      # H1 FY27 actual (Q1 recast + Q2)
def H1P(key): return f'({QC[(2026, 1)].c}{R[key]}+{QC[(2026, 2)].c}{R[key]})'   # H1 FY26 as reported
def QE2(key): return f'({Q3}{R[key]}+{Q4}{R[key]})'                     # Q3E + Q4E
def LQ(key): return f'{Q2}{R[key]}'                                      # latest actual quarter (30-Sep-2026 balance / Q2 FY27 flow)
def Q3v(key): return f'${Q3}${R[key]}'

SEG = [('st', 'Siding & Trim', 'ST', 'na'), ('dra', 'Deck, Rail & Accessories', 'DRA', 'dra'), ('anz', 'Australia & New Zealand', 'ANZ', 'apac')]
SEGK = [s for s, _, _, _ in SEG]
DMAP = {'st': 'na', 'dra': 'dra', 'anz': 'apac', 'eu': 'eu'}

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of the FY27 planning-assumption ranges.'))
    r = 11
    SCEN_ROWS.append((r, 'out_hdr', V0['out_hdr'], 'High', 'Mid', 'Low', V0['out_note'])); r += 1
    for key, lab, (hi, mid, lo), nf, note in V0['outlook']:
        SC[key] = r; SCEN_ROWS.append((r, 'out', lab, hi, mid, lo, note, nf)); r += 1
    r += 1
    SCEN_ROWS.append((r, 'pt_hdr', 'FY27 point estimates and schedule inputs (all cases)', None, None, None, None)); r += 1
    for key, lab, vals, nf, note in V0['points']:
        SC[key] = r
        SCEN_ROWS.append((r, 'pt', lab, None, vals, None, note, nf)); r += 1
    r += 1
    SC['LEV'] = r
    SCEN_ROWS.append((r, 'lev', '  Maximum net debt / Adjusted EBITDA before buybacks (x) — buyback floor 2028E+', *V0['lev'], V0['lev_note']))
    r += 2
    for name, lab, dbull, dbear, base, note, nf, clamp in V0['blocks']:
        SCEN_ROWS.append((r, 'blk', lab, dbull, 'Δ →', dbear, note, nf)); hdr = r; r += 1
        SC[name] = {}
        for y, b in zip(range(2028, 2032), base):
            SC[name][y] = r; SCEN_ROWS.append((r, 'yr', f'  {y}E', hdr, b, clamp, None, nf)); r += 1
    return r

# ====================================================================== row spec
def seg_rev_qe(s):
    def f():
        q = CTX.col.q; r = R[f'{s}_rev']
        if s in ('st', 'dra'):
            if q == 3: return '=' + CH(SC[f'q3_{s}'])
            return f'={CH(SC[f"fy_{s}"])}-{Q1}{r}-{Q2}{r}-{Q3}{r}'
        if q == 3: return f'={CH(SC["q3_tot"])}-{Q3}{R["st_rev"]}-{Q3}{R["dra_rev"]}'
        return f'={CH(SC["fy_tot"])}-{CH(SC["fy_st"])}-{CH(SC["fy_dra"])}-{Q1}{r}-{Q2}{r}-{Q3}{r}'
    return f
def seg_adj_qe(s):
    def f():
        q = CTX.col.q; r = R[f'{s}_adj']
        if s in ('st', 'dra'):
            if q == 3: return '=' + CH(SC[f'q3e_{s}'])
            return f'={CH(SC[f"fye_{s}"])}-{Q1}{r}-{Q2}{r}-{Q3}{r}'
        return f'={V(s + "_rev")}*{V(s + "_adjm")}'
    return f

def build_spec(V0):
    S = add
    # ------------------------------------------------------------------ SEGMENT BUILD
    S('sec_seg', 'SEGMENT P&L — SIDING & TRIM · DECK, RAIL & ACCESSORIES · AUSTRALIA & NEW ZEALAND · EUROPE (net sales × segment Adjusted EBITDA margin)', 'section',
      note='SEGMENT BUILD — modelling logic (segment net sales → segment Adjusted EBITDA at the segment margin → − segment D&A − AZEK intangible amortization = segment operating income; + corporate = group; Europe = discontinued operations from FY27)')
    blank()
    descr = {'st': 'Siding & Trim (North America Fiber Cement to Q1 FY26 + AZEK Exteriors from 1-Jul-2025; "USA (& Europe) Fibre Cement" FY2006–16, North America Fiber Cement FY2017–Q1 FY26)',
             'dra': 'Deck, Rail & Accessories (AZEK, consolidated from 1-Jul-2025 — TimberTech decking, railing, accessories)',
             'anz': 'Australia & New Zealand (Asia Pacific Fiber Cement to Q1 FY26; Philippines manufacturing closed Aug-2024; A$ reporting currency)'}
    notes_seg = {'st': ('Net sales as published per segment (as originally reported; FY2017–18 International Fiber Cement in the legacy memo rows). Q3/27E = Q3 FY27 '
                        'planning assumption (scenario end-point); Q4/27E = FY27 planning assumption − Q1–Q3. 2028E+: prior year × (1 + scenario lever).'),
                 'dra': 'Q3/27E and Q4/27E from the DR&A planning assumptions (scenario end-points); 2028E+: scenario lever.',
                 'anz': 'Q3/27E = total net sales planning assumption − Siding & Trim − DR&A; Q4/27E = FY total − S&T − DR&A − Q1–Q3. 2028E+: scenario lever.'}
    for s, title, code, dk in SEG:
        S(f'{s}_hdr', descr[s], 'block', note=f'{title.upper()} — modelling logic')
        S(f'{s}_rev', '  Net sales', 'line', 'm1', data=f'{dk}_rev', flow=True, qe=seg_rev_qe(s), ae=lambda s=s: f'={P(s + "_rev")}*(1+{V(s + "_g")})', note=notes_seg[s])
        S(f'{s}_g', '    y/y %', 'growth', 'pct', all=growth(f'{s}_rev'), ae=lambda code=code: '=' + CH(SC[f'{code}_G'][CTX.col.year]),
          note='2028E–2031E: scenario lever (Bull / Base / Bear table →). Q1–Q2/27 vs the FY26 quarters as originally reported (incl. Europe in the group; segment unaffected).' if s == 'st' else None)
        if s == 'st':
            S('st_vol', '    Memo: fiber cement volume (mmsf; North America, published to FY2023)', 'memo', 'm1', data='na_vol', flow=True)
            S('st_vol_g', '      Volume y/y %', 'growth', 'pct', all=growth('st_vol'))
            S('st_asp', '    Memo: average net sales price per msf (US$; published to FY2021)', 'memo', 'm', data='na_asp')
            S('st_asp_g', '      ASP y/y %', 'growth', 'pct', all=growth('st_asp'))
        if s == 'anz':
            S('anz_lc', '    Memo: net sales in A$ millions (published)', 'memo', 'm1', data='apac_rev_lc', flow=True)
            S('anz_vol', '    Memo: volume (mmsf; published to FY2023)', 'memo', 'm1', data='apac_vol', flow=True)
        S(f'{s}_oi', '  Segment operating income (EBIT; company segment measure)', 'line', 'm1', data=f'{dk}_ebit', flow=True,
          fc=lambda s=s: f'={V(s + "_adj")}-{V(s + "_dna")}' + (f'-{V(s + "_amort")}' if s != 'anz' else '') + f'-N({V(s + "_oth")})',
          note=('Segment EBIT as published (asbestos, R&D (to Q1 FY26) and general corporate sit outside the segments). Forecast = Adjusted EBITDA − segment D&A'
                ' − AZEK intangible amortization − other segment items.') if s == 'st' else None)
        S(f'{s}_oim', '  Segment operating margin %', 'pct', 'pct', all=ratio(f'{s}_oi', f'{s}_rev'))
        S(f'{s}_dna', '  Segment depreciation & amortization (excl. AZEK intangible amortization; published from FY2025)', 'line', 'm1', data=f'{dk}_dna', flow=True,
          fc=lambda s=s: f'={V(s + "_rev")}*{V(s + "_dna_pct")}')
        S(f'{s}_dna_pct', '    D&A % of net sales', 'pct', 'pct', all=ratio(f'{s}_dna', f'{s}_rev'),
          qe=lambda s=s: f'=IFERROR({H1(s + "_dna")}/{H1(s + "_rev")},0)', ae_in=V0['seg_dna_pct'][s],
          note='Q3–Q4/27E: H1 FY27 ratio; 2028E+ input (FY26–H1 FY27 range).' if s == 'st' else None)
        if s != 'anz':
            S(f'{s}_amort', '  Amortization of intangible assets from the AZEK acquisition (in segment operating income)', 'line', 'm1', data=f'{dk}_azek_amort', flow=True,
              fc=lambda s=s: f'={V("d_amort")}*{V(s + "_amsh")}')
            S(f'{s}_amsh', '    Share of AZEK intangible amortization', 'pct', 'pct', all=ratio(f'{s}_amort', 'd_amort'),
              fc=lambda s=s: f'=IFERROR({H1(s + "_amort")}/{H1("d_amort")},0)', note='H1 FY27 split (customer relationships / trade names / technology by segment).' if s == 'st' else None)
        S(f'{s}_oth', '  Other items in segment operating income (inventory step-up, restructuring, impairments; derived)', 'line', 'm1',
          hist=lambda s=s: (f'=IF(AND(ISNUMBER({V(s + "_adj")}),ISNUMBER({V(s + "_oi")}),ISNUMBER({V(s + "_dna")})),{V(s + "_adj")}-{V(s + "_oi")}-{V(s + "_dna")}'
                            + (f'-N({V(s + "_amort")})' if s != 'anz' else '') + ',"")'), fc=lambda: '=0',
          note='Historical: Adjusted EBITDA − operating income − D&A − AZEK amortization (items the company adds back at segment level). Forecast 0.' if s == 'st' else None)
        S(f'{s}_adj', '  Segment Adjusted EBITDA (company measure; published from FY2024)', 'line_b', 'm1', data=f'{dk}_adj_ebitda', flow=True,
          qe=seg_adj_qe(s), ae=lambda s=s: f'={V(s + "_rev")}*{V(s + "_adjm")}',
          note={'st': 'Q3/27E = S&T Adjusted EBITDA planning assumption; Q4/27E = FY assumption − Q1–Q3. 2028E+: net sales × scenario margin. FY2024–Q1 FY26 = segment EBITDA (North America Fiber Cement); from FY27 excludes share-based compensation (prior periods as published).',
                'dra': 'Q3/27E and Q4/27E from the DR&A Adjusted EBITDA planning assumptions; 2028E+: net sales × scenario margin.',
                'anz': 'Q3–Q4/27E = net sales × (prior-year quarter margin + H1 FY27 y/y margin drift); corporate absorbs the difference to the total planning assumption. 2028E+: scenario margin.'}[s])
        S(f'{s}_adjm', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio(f'{s}_adj', f'{s}_rev'),
          qe=(lambda: f'={P("anz_adjm")}+IFERROR({H1("anz_adj")}/{H1("anz_rev")}-{H1P("anz_adj")}/{H1P("anz_rev")},0)') if s == 'anz' else None,
          ae=lambda code=code: '=' + CH(SC[f'{code}_M'][CTX.col.year]))
        S(f'{s}_inc', '  Incremental Adjusted EBITDA margin (Δ Adjusted EBITDA / Δ net sales)', 'pct', 'pct', all=incr(f'{s}_adj', f'{s}_rev'))
        blank()
    # Europe (discontinued operations from Q1 FY27 — see the divestiture block)
    S('eu_hdr', 'Europe (Europe Building Products: fermacell® fibre gypsum from Apr-2018 + European fibre cement; segment to Q4 FY26; discontinued operations and held for sale from Q2 FY27)', 'block',
      note='EUROPE — history as reported (segment FY2019–FY2026, as originally reported; FY2017–18 inside International Fiber Cement); sale of fermacell to Holcim announced 20-Aug-2026 (divestiture block below)')
    S('eu_rev', '  Net sales', 'line', 'm1', data='eu_rev', flow=True, fc=lambda: '=0', note='Q1 FY27 as originally reported (156.4) sits in the divestiture block; the segment rows stop at FY2026 (continuing-operations basis from FY27).')
    S('eu_g', '    y/y %', 'growth', 'pct', all=growth('eu_rev'))
    S('eu_lc', '    Memo: net sales in € millions (published)', 'memo', 'm1', data='eu_rev_lc', flow=True)
    S('eu_oi', '  Segment operating income (EBIT)', 'line', 'm1', data='eu_ebit', flow=True, fc=lambda: '=0')
    S('eu_oim', '  Segment operating margin %', 'pct', 'pct', all=ratio('eu_oi', 'eu_rev'))
    S('eu_dna', '  Segment depreciation & amortization (published from FY2025)', 'line', 'm1', data='eu_dna', flow=True, fc=lambda: '=0')
    S('eu_adj', '  Segment Adjusted EBITDA (published from FY2024)', 'line_b', 'm1', data='eu_adj_ebitda', flow=True, fc=lambda: '=0')
    S('eu_adjm', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('eu_adj', 'eu_rev'))
    blank()
    S('lg_hdr', 'Legacy segments as originally reported (memo; included in the build sums for their periods)', 'block',
      note='LEGACY — International Fiber Cement (FY2017–18: Asia Pacific + Europe fibre cement), Other Businesses (FY2006–21), Research & Development segment (to Q1 FY26; allocated to the segments from 1-Jul-2025)')
    S('int_rev', '  International Fiber Cement — net sales (FY2017–FY2018)', 'memo', 'm1', data='int_rev', flow=True)
    S('int_oi', '  International Fiber Cement — segment operating income', 'memo', 'm1', data='int_ebit', flow=True)
    S('oth_rev', '  Other Businesses — net sales (FY2006–FY2021)', 'memo', 'm1', data='oth_rev', flow=True)
    S('oth_oi', '  Other Businesses — segment operating income', 'memo', 'm1', data='oth_ebit', flow=True)
    S('rd_oi', '  Research & Development segment — EBIT (to FY2025; R&D allocated to the operating segments from Q2 FY26)', 'memo', 'm1', data='rd_ebit', flow=True)
    blank()
    S('co_hdr', 'Corporate (general corporate costs, AICF SG&A, corporate-level one-offs; asbestos adjustments shown on their own line in the P&L)', 'block',
      note='CORPORATE — general corporate costs as published (ex asbestos); the derived "corporate & other" row makes the segment build tie to reported operating income')
    S('corp_adj', '  Corporate Adjusted EBITDA (company Adjusted EBITDA − Σ segment Adjusted EBITDA; derived FY2024–FY2027 H1)', 'line', 'm1', flow=True,
      hist=lambda: (f'=IF(AND(ISNUMBER({V("r_pub")}),ISNUMBER({V("st_adj")}),ISNUMBER({V("anz_adj")}){"" if CTX.col.year >= 2027 else ",ISNUMBER(" + V("eu_adj") + ")"}),'
                    f'{V("r_pub")}-{V("st_adj")}-N({V("dra_adj")})-{V("anz_adj")}{"" if CTX.col.year >= 2027 else "-" + V("eu_adj")},"")'),
      qe=lambda: (f'={CH(SC["q3e_tot"])}-{Q3}{R["st_adj"]}-{Q3}{R["dra_adj"]}-{Q3}{R["anz_adj"]}' if CTX.col.q == 3 else
                  f'={CH(SC["fye_tot"])}-{CH(SC["fye_st"])}-{CH(SC["fye_dra"])}-SUM({Q1}{R["anz_adj"]}:{Q4}{R["anz_adj"]})-{Q1}{R["corp_adj"]}-{Q2}{R["corp_adj"]}-{Q3}{R["corp_adj"]}'),
      ae=lambda: f'={V("is_rev")}*{V("corp_pct")}',
      note='Historical: company Adjusted EBITDA − Σ segment Adjusted EBITDA (derived residual; the published General Corporate line is the memo below, the difference being unallocated items and rounding). Q3–Q4/27E: total Adjusted EBITDA planning assumption − segments (plug). 2028E+: % of net sales.')
    S('corp_adj_pub', '  Memo: General Corporate (Adjusted EBITDA basis) as published (FY2026+ releases; costs negative)', 'memo', 'm1', data='corp_adj_ebitda', flow=True)
    S('corp_pct', '  Corporate Adjusted EBITDA % of net sales', 'pct', 'pct', all=ratio('corp_adj', 'is_rev'), ae_in=V0['corp_pct'], note=V0['corp_pct_note'])
    S('corp_dna', '  Corporate depreciation & amortization (derived)', 'line', 'm1', flow=True,
      hist=lambda: (f'=IF(AND(ISNUMBER({V("d_dna")}),ISNUMBER({V("st_dna")}),ISNUMBER({V("anz_dna")})),{V("d_dna")}-{V("st_dna")}-N({V("dra_dna")})-{V("anz_dna")}-N({V("eu_dna")})-N({V("d_amort")}),"")'),
      qe=lambda: f'=AVERAGE({Q1}{R["corp_dna"]},{Q2}{R["corp_dna"]})', ae_in=V0['corp_dna'], note='Total D&A − segment D&A − AZEK amortization. Forecast: H1 FY27 average; 2028E+ input.')
    S('corp', '  Memo: general corporate costs as published (ex asbestos; FY2013–FY2025 segment EBIT tables, FY2026+ release)', 'memo', 'm1', data='corp_ebit', flow=True)
    S('corp_aicf', '  Memo: AICF SG&A expenses (published FY2006–FY2023; in "asbestos related expenses" from FY2024)', 'memo', 'm1', data='aicf_sga', flow=True)
    S('corp_der', '  Corporate & other, GAAP (derived: operating income − segment EBIT − R&D segment + asbestos adjustments)', 'line_b', 'm1',
      hist=lambda: (f'=IF(ISNUMBER({V("is_op")}),{V("is_op")}-N({V("st_oi")})-N({V("dra_oi")})-N({V("anz_oi")})-N({V("eu_oi")})-N({V("int_oi")})-N({V("oth_oi")})-N({V("rd_oi")})+N({V("d_asb")}),"")'),
      fc=lambda: f'={V("corp_adj")}-{V("corp_dna")}-{V("d_sbc")}',
      note='Historical plug (ties the build to reported operating income: general corporate costs, AICF SG&A, corporate-level one-offs such as ASIC / NZ product liability / impairments / SCI / acquisition costs). Forecast = corporate Adjusted EBITDA − corporate D&A − share-based compensation (excluded from Adjusted EBITDA from FY27).')
    S('corp_items', '  Memo: corporate-level one-offs & other (derived = corporate & other − general corporate costs − AICF SG&A)', 'memo_calc', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("corp_der")}),ISNUMBER({V("corp")})),{V("corp_der")}-{V("corp")}-N({V("corp_aicf")}),"")')
    blank()

    # ------------------------------------------------------------------ group total & calibration
    S('g_hdr', 'Group Total — net sales & Adjusted EBITDA (segment build) → FY27 planning-assumption calibration', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic; FY2027 = Q1 (recast to continuing operations) + Q2 actual + Q3E (quarter guide) + Q4E (FY guide − 9M)')
    S('g_rev', 'Net sales (segment build)', 'total', 'm1',
      hist=lambda: (f'=IF(ISNUMBER({V("st_rev")}),{V("st_rev")}+N({V("dra_rev")})+N({V("anz_rev")})+{"N(" + V("eu_rev") + ")+" if CTX.col.year < 2027 else ""}N({V("int_rev")})+N({V("oth_rev")}),{V("is_rev")})'),
      fc=lambda: f'={V("st_rev")}+{V("dra_rev")}+{V("anz_rev")}+N({V("m_rev")})',
      note='Σ segment net sales (+ International FY2017–18, Other Businesses to FY2021; Europe to FY2026; future acquisitions from 2028E).')
    S('g_rev_g', '  Net sales y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs consolidated net sales (should be 0; ±0.3 rounding)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=0.3,0,ROUND({V("g_rev")}-{V("is_rev")},1)),"")')
    S('g_adj', 'Adjusted EBITDA (segment build: Σ segment Adjusted EBITDA + corporate)', 'total', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("st_adj")}),ISNUMBER({V("corp_adj")})),{V("st_adj")}+N({V("dra_adj")})+N({V("anz_adj")})+{"N(" + V("eu_adj") + ")+" if CTX.col.year < 2027 else ""}{V("corp_adj")},"")',
      fc=lambda: f'={V("st_adj")}+{V("dra_adj")}+{V("anz_adj")}+{V("corp_adj")}+N({V("m_oi")})',
      note="James Hardie's primary profit KPI and the FY27 planning-assumption metric; drives the GAAP P&L below.")
    S('g_adjm', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('g_adj', 'is_rev'))
    S('g_adj_g', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('g_adj'))
    S('g_chk_adj', '  Check: segment build vs Adjusted EBITDA bridge (should be 0; ±0.6 — Q1 FY27 derived from six-month columns)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_adj")}),ISNUMBER({V("r_adj")})),IF(ABS({V("g_adj")}-{V("r_adj")})<=0.6,0,ROUND({V("g_adj")}-{V("r_adj")},1)),"")')
    S('cal_h', 'FY27 planning assumptions (Q2 FY27 release, 5-Nov-2026; continuing operations, ex share-based compensation) — scenario end-points', 'sub', 'gen')
    for key, lab in [('q3_tot', '  Q3 FY27 net sales — total'), ('q3_st', '  Q3 FY27 net sales — Siding & Trim'), ('q3_dra', '  Q3 FY27 net sales — Deck, Rail & Accessories'),
                     ('q3e_tot', '  Q3 FY27 Adjusted EBITDA — total'), ('q3e_st', '  Q3 FY27 Adjusted EBITDA — Siding & Trim'), ('q3e_dra', '  Q3 FY27 Adjusted EBITDA — DR&A')]:
        S('cg_' + key, lab, 'memo', 'm1', qe=lambda key=key: ('=' + CH(SC[key])) if CTX.col.q == 3 else None)
    for key, lab in [('fy_tot', '  FY27 net sales — total'), ('fy_st', '  FY27 net sales — Siding & Trim'), ('fy_dra', '  FY27 net sales — DR&A'),
                     ('fye_tot', '  FY27 Adjusted EBITDA — total'), ('fye_st', '  FY27 Adjusted EBITDA — Siding & Trim'), ('fye_dra', '  FY27 Adjusted EBITDA — DR&A')]:
        S('cg_' + key, lab, 'memo', 'm1', e26=lambda key=key: '=' + CH(SC[key]))
    S('cal_chk_q3', '  Check: Q3/27E net sales and Adjusted EBITDA vs the Q3 planning assumptions (should be 0)', 'check', 'm1',
      qe=lambda: (f'=ROUND(ABS({V("g_rev")}-{V("cg_q3_tot")})+ABS({V("g_adj")}-{V("cg_q3e_tot")}),1)' if CTX.col.q == 3 else None))
    S('cal_chk_fy', '  Check: FY2027E net sales and Adjusted EBITDA vs the FY27 planning assumptions (should be 0)', 'check', 'm1',
      e26=lambda: f'=ROUND(ABS({V("g_rev")}-{V("cg_fy_tot")})+ABS({V("g_adj")}-{V("cg_fye_tot")}),1)')
    S('cal_fcf', '  Memo: FY27 free cash flow planning assumption (> US$650m; information)', 'memo', 'm1', e26=lambda: f'={PT("pt_fcf")}')
    S('cal_fcf_d', '  Model FY27 free cash flow − planning assumption (information, not forced)', 'memo_calc', 'm1', e26=lambda: f'={V("fcf")}-{V("cal_fcf")}')
    blank()

    # ------------------------------------------------------------------ AZEK memo
    S('az_hdr', 'AZEK acquisition (closed 1-Jul-2025; US$8.4bn consideration — cash US$4.25bn incl. US$437.8m AZEK debt repaid + 148.9m shares at US$26.82) — memo', 'block',
      note='AZEK — standalone and pro forma memo (Form 10-K FY2026 Note 2; Q2 FY27 release pro forma reconciliation); PPA in the schedules section; synergy targets per the Q2 FY27 release')
    S('az_std_rev', '  AZEK standalone net sales before closing (pro forma; Q1 FY26)', 'memo', 'm1', data='man:azek:std_rev')
    S('az_std_adj', '  AZEK standalone Adjusted EBITDA before closing (pro forma; Q1 FY26)', 'memo', 'm1', data='man:azek:std_adj')
    S('az_pc_rev', '  AZEK net sales consolidated since 1-Jul-2025 (FY2026, 10-K Note 2)', 'memo', 'm1', data='man:azek:pc_rev')
    S('az_pc_ni', '  AZEK net loss consolidated since 1-Jul-2025 (FY2026, incl. step-up and amortization)', 'memo', 'm1', data='man:azek:pc_ni')
    S('az_pf_rev', '  Pro forma combined net sales (full-year basis, 10-K Note 2)', 'memo', 'm1', data='man:azek:pf_rev')
    S('az_pf_ni', '  Pro forma combined net income (10-K Note 2)', 'memo', 'm1', data='man:azek:pf_ni')
    S('az_step', '  Inventory fair-value step-up expensed (in cost of goods sold; adjusted out)', 'memo_calc', 'm1', all=lambda: f'=N({V("d_stepup")})')
    S('az_amort', '  Amortization of AZEK intangible assets (customer relationships 18y, trade names 5–15y, technology 10y)', 'memo_calc', 'm1', all=lambda: f'=N({V("d_amort")})')
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — bolt-ons, unallocated; deals closed from 2028E)', 'block', note='M&A LEVER — acquired net sales = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=3.0, e26_in=0.0, note='AZEK ~5.8x sales (US$8.4bn on ~US$1.45bn); Fermacell (Apr-2018) ~1.8x. 3.0x input for bolt-ons.')
    S('m_acq_sales', '  Annualised net sales acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.05)
    S('m_run', '  Run-rate net sales of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Net sales from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}', note='Mid-year convention.')
    S('m_m', '  Adjusted EBITDA margin of acquired businesses %', 'driver', 'pct', e26_in=0.0, ae_in=0.20)
    S('m_oi', '  Adjusted EBITDA from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.15)
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.40, note='AZEK PPA: intangibles 40% of consideration, goodwill 55%, PP&E 10%.')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=15)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)', note='Non-cash; inside depreciation & amortization (not adjusted out).')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A, asbestos and adjusting items', 'block', note='COST DRIVERS — inputs that drive the forecast cost lines (Q3–Q4/27E: FY27 point estimates less H1 FY27 actual)')
    S('d_dna', '  Depreciation & amortization (total; cash-flow statement; FY27 continuing operations per the Adjusted EBITDA bridge)', 'line', 'm1', data='dna_model', flow=True, fc=lambda: f'={V("d_dep")}+{V("d_amort")}',
      note='Cash-flow statement (year to date; discrete quarters derived). FY27: continuing-operations D&A from the Adjusted EBITDA reconciliation (the cash-flow statement includes Europe).')
    S('d_amort', '  Amortization of intangible assets from the AZEK acquisition (adjusted out from FY26)', 'line', 'm1', data='ni_it_amort', flow=True,
      qe=lambda: f'=({PT("pt_amort")}-{H1("d_amort")})/2', ae=lambda: f'={V("d_amort_sch")}',
      note='Q3–Q4/27E: FY27 point estimate less H1 FY27. 2028E+: 10-K schedule of intangibles held at 31-Mar-2026 less the Europe (held-for-sale) and legacy amortization.')
    S('d_amort_sch', '  Amortization schedule — AZEK intangibles (10-K Note 7 total less legacy / Europe amortization; input)', 'driver', 'm1', ae_in=V0['amort_sched'], note=V0['amort_note'])
    S('d_dep', '  Depreciation & other amortization (total D&A − AZEK intangible amortization)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("d_dna")}),{V("d_dna")}-N({V("d_amort")}),"")',
      fc=lambda: f'={V("st_dna")}+{V("dra_dna")}+{V("anz_dna")}+{V("corp_dna")}+N({V("m_amort")})', note='Forecast = Σ segment D&A + corporate D&A (+ future-acquisition amortization).')
    S('d_dep_pct', '  Depreciation & other amortization % of net sales', 'pct', 'pct', all=ratio('d_dep', 'is_rev'))
    S('d_sga', '  SG&A % of net sales', 'pct', 'pct', all=ratio('is_sga', 'is_rev'),
      qe=lambda: f'={P("d_sga")}+IFERROR({H1("is_sga")}/{H1("is_rev")}-{H1P("is_sga")}/{H1P("is_rev")},0)', ae_in=V0['sga_pct'],
      note='Q3–Q4/27E: prior-year quarter ratio + H1 FY27 y/y drift; 2028E+ input. Gross profit is implied (operating income from the Adjusted EBITDA build + operating expenses).')
    S('d_rd', '  R&D % of net sales', 'pct', 'pct', all=ratio('is_rd', 'is_rev'), qe=lambda: f'=IFERROR({H1("is_rd")}/{H1("is_rev")},"")', ae_in=V0['rd_pct'])
    S('d_sbc', '  Share-based compensation (cash-flow statement; excluded from Adjusted EBITDA / adjusted net income from FY27)', 'line', 'm1', data='cf_sbc', flow=True,
      qe=lambda: f'={P("d_sbc")}*(1+IFERROR({H1("d_sbc")}/{H1P("d_sbc")}-1,0))', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}',
      note='Q3–Q4/27E: prior-year quarter × H1 FY27 y/y; 2028E+: % of net sales.')
    S('d_sbc_pct', '  Share-based compensation % of net sales', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_asb', '  Asbestos adjustments (P&L; actuarial, claims-handling and A$/US$ translation; charge positive)', 'line', 'm1', data='asb_adj', flow=True, qe_in=0.0, ae_in=0.0,
      note='Not forecastable (FX and actuarial); 0 assumed. Q1 FY27 −1.6 (gain), Q2 FY27 0.3.')
    S('d_aicf', '  AICF SG&A expenses (published to FY2023; from FY2024 derived = bridge "asbestos related expenses and adjustments" − statement asbestos adjustments)', 'line', 'm1', data='aicf_sga', flow=True,
      qe_in=0.5, ae_in=2.0, note='FY2024: published Adjusted EBIT − EBIT − asbestos adjustments − impairment (1.6). Forecast: ~US$2m a year (claims-fund running costs).')
    S('d_restr', '  Restructuring expenses (adjusted out)', 'line', 'm1', data='restr', flow=True, qe_in=V0['qe_restr'], ae_in=V0['ae_restr'], note=V0['restr_note'])
    S('d_acq', '  Acquisition & divestiture related expenses (AZEK integration, Europe sale costs; adjusted out)', 'line', 'm1', data='acq_exp', flow=True, qe_in=V0['qe_acq'], ae_in=V0['ae_acq'],
      note=V0['acq_note'])
    S('d_impair', '  Asset impairments (FY2008, FY2012–13, FY2019–20 product line discontinuation, FY2024 greenfield site)', 'line', 'm1', data='impair', flow=True, fc=lambda: '=0')
    S('d_stepup', '  Inventory fair-value step-up (AZEK; in cost of goods sold, Q2 FY26)', 'line', 'm1', data='ni_it_stepup', flow=True, fc=lambda: '=0')
    S('d_othop', '  Other operating items (SCI FY2006–07, other operating expense)', 'line', 'm1', flow=True, hist=lambda: f'=IF(ISNUMBER({V("is_rev")}),N({V("d_sci")})+N({V("d_otherop")}),"")', fc=lambda: '=0')
    S('d_sci', '    of which SCI and related expenses (FY2006–07; Special Commission of Inquiry)', 'memo', 'm1', data='sci', flow=True)
    S('d_otherop', '    of which other operating expense', 'memo', 'm1', data='other_op', flow=True)
    S('d_preclose', '  Pre-close financing costs (AZEK bridge / notes before closing, Q1 FY26; in interest, adjusted out)', 'line', 'm1', data='ni_it_preclose', flow=True, fc=lambda: '=0')
    S('d_fxgain', '  Non-cash (gain) loss on foreign currency forward contracts (Europe sale proceeds hedge; non-operating, adjusted out)', 'line', 'm1', data='ni_it_fxgain', flow=True, fc=lambda: '=0')
    S('d_debtext', '  Loss on early debt extinguishment (FY2018, FY2021; adjusted out)', 'line', 'm1', data='debt_ext', flow=True, fc=lambda: '=0')
    S('d_aicf_int', '  AICF interest income (in interest, net; adjusted out)', 'line', 'm1', data='ni_it_aicf_int', flow=True,
      qe=lambda: f'={H1("d_aicf_int")}/2', ae=lambda: f'=-{P("as_cash")}*{V("as_yield")}', note='Forecast = −yield × opening AICF restricted cash & investments.')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF OPERATIONS (US GAAP; FY2006–FY2026 as reported, FY2027 continuing operations — Europe discontinued)', 'section',
      note='CONSOLIDATED IS — forecast logic (operating income = Σ segment EBIT + corporate & other − asbestos − adjusting items; gross profit implied)')
    S('is_rev', 'Net sales', 'total', 'm1', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the segment build. Q1 FY27 recast to continuing operations (six months in the Q2 FY27 release − Q2).')
    S('is_cogs', 'Cost of goods sold', 'line', 'm1', data='cogs', flow=True, fc=lambda: f'={V("is_rev")}-{V("is_gp")}')
    S('is_gp', 'Gross profit', 'line_b', 'm1', flow=True, hist=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_rev")}-{V("is_cogs")},"")',
      fc=lambda: f'={V("is_op")}+{V("is_sga")}+{V("is_rd")}+{V("is_restr")}+{V("is_acq")}+{V("is_asb")}+{V("is_oth")}',
      note='Forecast = operating income + operating expenses (implied by the Adjusted EBITDA build).')
    S('is_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('is_sga', 'Selling, general & administrative expenses', 'line', 'm1', data='sga', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_sga")}')
    S('is_rd', 'Research & development expenses', 'line', 'm1', data='rd', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_rd")}')
    S('is_restr', 'Restructuring expenses', 'line', 'm1', data='restr', flow=True, fc=lambda: f'={V("d_restr")}')
    S('is_acq', 'Acquisition & divestiture related expenses', 'line', 'm1', data='acq_exp', flow=True, fc=lambda: f'={V("d_acq")}')
    S('is_asb', 'Asbestos adjustments (charge positive)', 'line', 'm1', data='asb_adj', flow=True, fc=lambda: f'={V("d_asb")}')
    S('is_oth', 'Asset impairments, SCI & other operating items', 'line', 'm1', flow=True, hist=lambda: f'=IF(ISNUMBER({V("is_rev")}),N({V("d_impair")})+N({V("d_othop")}),"")',
      fc=lambda: f'={V("d_impair")}+{V("d_othop")}')
    S('is_op', 'Operating income (EBIT)', 'total', 'm1', data='op', flow=True,
      fc=lambda: f'={V("st_oi")}+{V("dra_oi")}+{V("anz_oi")}+{V("corp_der")}-{V("d_asb")}-{V("d_aicf")}-{V("d_restr")}-{V("d_acq")}-{V("d_impair")}-{V("d_othop")}+N({V("m_oi")})-N({V("m_amort")})',
      note='Forecast = Σ segment operating income + corporate & other − asbestos adjustments − AICF SG&A − restructuring − acquisition / divestiture costs − impairments (+ future acquisitions).')
    S('is_opm', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('is_int', 'Interest, net (interest expense less interest income incl. AICF interest income; pre-close financing costs FY26)', 'line', 'm1', data='int_net', flow=True,
      qe=lambda: f'=({PT("pt_int")}-{H1("is_int")})/2',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_tla")}*{V("ds_r_tla")}+{P("ds_rev")}*{V("ds_r_rev")}+{V("ds_fees")}-{P("bs_cash")}*{V("ds_r_cash")}+{V("d_aicf_int")}',
      note='Q3–Q4/27E: FY27 point estimate less H1. 2028E+ = rates × opening notes / term loans / revolver + fees − yield × opening cash + AICF interest income (no circularity).')
    S('is_debtext', 'Loss on early debt extinguishment', 'line', 'm1', data='debt_ext', flow=True, fc=lambda: f'={V("d_debtext")}')
    S('is_onop', 'Other (income) expense, net', 'line', 'm1', data='onop', flow=True, qe=lambda: f'={V("d_fxgain")}', ae=lambda: f'={V("d_fxgain")}',
      note='FY27 Q2: −18.9 incl. the −19.4 non-cash gain on the Europe-proceeds hedge. Forecast 0.')
    S('is_ebt', 'Income before income taxes', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_op")}),{V("is_op")}-{V("is_int")}-N({V("is_debtext")})-N({V("is_onop")}),"")')
    S('is_tax', 'Income tax expense', 'line', 'm1', data='tax', flow=True, qe=lambda: f'={V("is_ebt")}*{V("is_etr")}', ae=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate (GAAP)', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'], note=V0['etr_note'])
    S('is_nic', 'Net income from continuing operations', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_cum', 'Cumulative effect of a change in accounting principle (FY2007, net of tax)', 'line', 'm1', data='cum_eff', flow=True, fc=lambda: '=0')
    S('is_disc', 'Income from discontinued operations, net of tax (Europe, from Q1 FY27 recast)', 'line', 'm1', data='disc', flow=True, fc=lambda: f'={V("dv_disc")}',
      note='Forecast from the Europe divestiture block (operating result until closing; gain on sale in the closing year).')
    S('is_ni', 'Net income', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_nic")}),{V("is_nic")}+N({V("is_cum")})+N({V("is_disc")}),"")')
    S('is_ni_chk', '  Check: net income vs reported (should be 0; ±0.15 rounding)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=0.15,0,ROUND({V("is_ni")}-{V("is_ni_pub")},1)),"")')
    S('is_ni_pub', '  Memo: net income as reported (FY2006–08 "net operating profit (loss)")', 'memo', 'm1', data='ni', flow=True)
    S('is_dda', '  Memo: depreciation & amortization (total)', 'memo_calc', 'm1', all=lambda: f'={V("d_dna")}')
    S('is_sbc', '  Memo: share-based compensation', 'memo_calc', 'm1', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share — ordinary shares / CUFS; NYSE ADS = 1 ordinary share; James Hardie Industries plc (Ireland), formerly N.V. / SE)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={LQ("bs_shares")}-${E26}${R["bb_sh"]}/2*{ {3: 0.5, 4: 1.5}[CTX.col.q] }+${E26}${R["bb_iss"]}/2*{ {3: 0.5, 4: 1.5}[CTX.col.q] }',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q3–Q4/27E: shares outstanding at 30-Sep-2026 − Q3–Q4 buybacks phased evenly (mid-quarter) + equity-plan issuance. 2028E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({LQ("sh_dil")}-{LQ("sh_basic")})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dilc', 'EPS – diluted, continuing operations ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_nic")}/{V("sh_dil")},""),"")',
      note='Net income from continuing operations / weighted diluted shares.')
    S('eps_dilc_g', '  EPS – diluted (continuing) y/y %', 'growth', 'pct', all=growth('eps_dilc'))
    S('eps_dil', 'EPS – diluted, total ($)', 'eps', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")')
    S('eps_pub', '  Memo: EPS – diluted as reported ($; FY2006–22 published in US cents)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0101,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('dps', '  Dividends per share ($; fiscal-year totals; none since FY2022)', 'line', 'ps', data='dps', ann=True, e26_in=0.0, ae_in=0.0, note=V0['dps_note'])
    blank()

    # ------------------------------------------------------------------ RECON 1: net income -> EBITDA -> Adjusted EBITDA
    S('sec_r1', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (company definition in force; model bridge FY2021–22)', 'section',
      note='ADJUSTED EBITDA — net income + tax + interest + other = EBIT; + D&A = EBITDA; + asbestos adjustments, AICF SG&A, restructuring, acquisition / divestiture costs, inventory step-up, impairments (+ share-based compensation from FY27)')
    S('r_ni', 'Net income (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('r_disc', '  (−) Discontinued operations and cumulative effect of accounting change', 'line', 'm1', all=lambda: f'=-N({V("is_disc")})-N({V("is_cum")})')
    S('r_tax', '  (+) Income tax expense', 'line', 'm1', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest, net', 'line', 'm1', all=lambda: f'={V("is_int")}')
    S('r_debtext', '  (+) Loss on early debt extinguishment', 'line', 'm1', all=lambda: f'=N({V("is_debtext")})')
    S('r_onop', '  (+) Other (income) expense, net', 'line', 'm1', all=lambda: f'=N({V("is_onop")})')
    S('r_op', '  = Operating income (EBIT)', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_disc")}+{V("r_tax")}+{V("r_int")}+{V("r_debtext")}+{V("r_onop")},"")')
    S('r_op_chk', '  Check: rebuilt operating income vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_op")}),IF(ABS({V("r_op")}-{V("is_op")})<=0.15,0,ROUND({V("r_op")}-{V("is_op")},1)),"")')
    S('r_dna', '  (+) Depreciation & amortization (total, incl. AZEK intangible amortization)', 'line', 'm1', all=lambda: f'={V("d_dna")}')
    S('r_ebitda', '  = EBITDA', 'total', 'm1', all=lambda: f'=IF(AND(ISNUMBER({V("r_op")}),ISNUMBER({V("r_dna")})),{V("r_op")}+{V("r_dna")},"")')
    S('r_asb', '  (+) Asbestos adjustments', 'line', 'm1', all=lambda: f'=N({V("d_asb")})')
    S('r_aicf', '  (+) AICF SG&A expenses', 'line', 'm1', all=lambda: f'=N({V("d_aicf")})')
    S('r_restr', '  (+) Restructuring expenses', 'line', 'm1', all=lambda: f'=N({V("d_restr")})')
    S('r_acq', '  (+) Acquisition & divestiture related expenses', 'line', 'm1', all=lambda: f'=N({V("d_acq")})')
    S('r_stepup', '  (+) Inventory fair-value step-up', 'line', 'm1', all=lambda: f'=N({V("d_stepup")})')
    S('r_oth', '  (+) Asset impairments, SCI & other operating items', 'line', 'm1', all=lambda: f'=N({V("d_impair")})+N({V("d_othop")})')
    S('r_sbc', '  (+) Share-based compensation (company definition from FY27; FY26 comparatives recast in the FY27 releases)', 'line', 'm1', data='ni_it_sbc', flow=True,
      fc=lambda: f'={V("d_sbc")}', note='Historical: only where the company adds it back (FY27 quarters). Forecast: share-based compensation from the cost drivers.')
    S('r_adj', '  = Adjusted EBITDA (model bridge)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{V("r_ebitda")}+{nsum(["r_asb", "r_aicf", "r_restr", "r_acq", "r_stepup", "r_oth", "r_sbc"])},"")',
      note='Company definition from FY2024 (FY2023 as restated in the FY24 release). FY2021–22: model bridge on the same items (no company figure). FY2010–20: see the "excluding asbestos" and "EBITDA" rows.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_pub', '  Company-published Adjusted EBITDA (FY2023 onward)', 'memo', 'm1', data='adj_ebitda_pub', flow=True)
    S('r_chk', '  Check: model bridge vs company-published Adjusted EBITDA (should be 0; ±0.6 — Q1 FY27 derived from six-month columns)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_pub")}),IF(ABS({V("r_adj")}-{V("r_pub")})<=0.6,0,ROUND({V("r_adj")}-{V("r_pub")},1)),"n/p")')
    S('r_pub_ex', '  Company-published "Adjusted EBITDA excluding asbestos" (FY2017–FY2020 definition: EBITDA + asbestos adjustments + AICF SG&A)', 'memo', 'm1', data='ebitda_ex_asb_pub', flow=True)
    S('r_chk_ex', '  Check: EBITDA + asbestos + AICF SG&A vs company-published excluding asbestos (should be 0; ±0.3)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_pub_ex")}),IF(ABS({V("r_ebitda")}+{V("r_asb")}+{V("r_aicf")}-{V("r_pub_ex")})<=0.3,0,ROUND({V("r_ebitda")}+{V("r_asb")}+{V("r_aicf")}-{V("r_pub_ex")},1)),"n/p")')
    S('r_pub_old', '  Company-published "EBITDA" / "Adjusted EBITDA" FY2010–FY2020 (= EBIT + D&A, asbestos included)', 'memo', 'm1', data='ebitda_old_pub', flow=True)
    S('r_chk_old', '  Check: EBITDA vs company-published FY2010–20 (should be 0; ±0.6 — Q3 FY13 D&A rounded in the release)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_pub_old")}),IF(ABS({V("r_ebitda")}-{V("r_pub_old")})<=0.6,0,ROUND({V("r_ebitda")}-{V("r_pub_old")},1)),"n/p")')
    S('r_def', '  Definition / basis (company Adjusted EBITDA definition and presentation basis in force)', 'text', 'gen', note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('r_adj_g', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('r_ebit_h', 'To Adjusted EBIT / EBITA (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ebita', '  Adjusted EBITA after share-based compensation (model: Adjusted EBITDA − SBC add-back − depreciation & other amortization; NOPAT basis)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}-N({V("r_sbc")})-{V("d_dep")},"")',
      note='Before AZEK intangible amortization, after share-based compensation (the playbook NOPAT basis). Pre-FY27 Adjusted EBITDA already expenses SBC.')
    S('r_ebit', '  Adjusted EBIT (model: Adjusted EBITDA − SBC add-back − total D&A; full cost)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}-N({V("r_sbc")})-{V("d_dna")},"")')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: restructuring and acquisition / divestiture costs (cash items adjusted out; deducted in the DCF)', 'memo_calc', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_restr")}),{V("r_restr")}+{V("r_acq")},"")')
    blank()

    # ------------------------------------------------------------------ RECON 2: EBIT -> Adjusted EBIT (company, FY2006-FY2025)
    S('sec_r2', 'RECONCILIATION: EBIT → ADJUSTED EBIT (company definition FY2006–FY2025: "EBIT excluding asbestos …" / "Adjusted EBIT"; not published from FY2026 — model continuation)', 'section',
      note='ADJUSTED EBIT — EBIT + asbestos adjustments + AICF SG&A + other items the company excluded in each period (impairments, ASIC, NZ product liability / weathertightness, stamp duty, restructuring, acquisition costs, product line discontinuation)')
    S('o_op', 'Operating income (EBIT)', 'line_b', 'm1', all=lambda: f'={V("is_op")}')
    S('o_asb', '  (+) Asbestos adjustments', 'line', 'm1', all=lambda: f'=N({V("d_asb")})')
    S('o_aicf', '  (+) AICF SG&A expenses', 'line', 'm1', all=lambda: f'=N({V("d_aicf")})')
    S('o_items', '  (+) Other items excluded by the company (as published per period; forecast: restructuring, acquisition / divestiture costs, step-up, impairments)', 'line', 'm1',
      data='eb_items_x', flow=True, hist=lambda: f'=N({V("d_restr")})+N({V("d_acq")})+N({V("d_impair")})+N({V("d_othop")})+N({V("d_stepup")})',
      fc=lambda: f'={V("d_restr")}+{V("d_acq")}+{V("d_impair")}+{V("d_othop")}+{V("d_stepup")}',
      note='Historical: Σ of the published bridge items other than asbestos / AICF SG&A; FY2024–25 (no itemised EBIT bridge): restructuring, merger / acquisition costs and impairments from the statement of operations.')
    S('o_adj', '  = Adjusted EBIT (model bridge)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_asb")}+{V("o_aicf")}+N({V("o_items")}),"")')
    S('o_adj_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company-published Adjusted EBIT / EBIT excluding asbestos (FY2006–FY2025)', 'memo', 'm1', data='tot_adj_ebit', flow=True)
    S('o_chk', '  Check: model bridge vs company-published (should be 0; ±0.3)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),IF(ABS({V("o_adj")}-{V("o_pub")})<=0.3,0,ROUND({V("o_adj")}-{V("o_pub")},1)),"n/p")')
    S('o_def', '  Definition / basis (company adjusted definition in force)', 'text', 'gen')
    S('o_adj_g', '  Adjusted EBIT y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental Adjusted EBIT margin (Δ Adjusted EBIT / Δ net sales)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 3: net income -> adjusted net income -> adjusted EPS
    S('sec_r3', 'RECONCILIATION: NET INCOME / DILUTED EPS → ADJUSTED NET INCOME → ADJUSTED DILUTED EPS (company definition in force)', 'section',
      note='ADJUSTED NET INCOME — net income from continuing operations + pre-tax adjusting items + tax adjustments (tax effect of the items, asbestos-related and other tax items)')
    S('e_ni', 'Net income from continuing operations (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_nic")}')
    S('e_asb', '  (+) Asbestos adjustments (statement of operations line)', 'line', 'm1', all=lambda: f'=N({V("d_asb")})')
    S('e_aicf', '  (+) AICF SG&A expenses (from FY2024 inside the company\'s "asbestos related expenses and adjustments" line; derived)', 'line', 'm1', all=lambda: f'=N({V("d_aicf")})')
    S('e_aicf_int', '  (−) AICF interest income', 'line', 'm1', data='ni_it_aicf_int', flow=True, fc=lambda: f'={V("d_aicf_int")}')
    S('e_restr', '  (+) Restructuring expenses', 'line', 'm1', data='ni_it_restr', flow=True, fc=lambda: f'={V("d_restr")}')
    S('e_acq', '  (+) Acquisition & divestiture related expenses (Fermacell FY2018–19; AZEK / Europe FY2025–)', 'line', 'm1', data='ni_it_acq', flow=True, fc=lambda: f'={V("d_acq")}')
    S('e_stepup', '  (+) Inventory fair-value step-up', 'line', 'm1', data='ni_it_stepup', flow=True, fc=lambda: f'={V("d_stepup")}')
    S('e_preclose', '  (+) Pre-close financing costs', 'line', 'm1', data='ni_it_preclose', flow=True, fc=lambda: f'={V("d_preclose")}')
    S('e_fxgain', '  (+) Non-cash (gain) loss on foreign currency forward contracts', 'line', 'm1', data='ni_it_fxgain', flow=True, fc=lambda: f'={V("d_fxgain")}')
    S('e_amort', '  (+) Amortization of AZEK intangible assets (from FY26)', 'line', 'm1', data='ni_it_amort', flow=True, fc=lambda: f'={V("d_amort")}')
    S('e_sbc', '  (+) Share-based compensation (from FY27)', 'line', 'm1', data='ni_it_sbc', flow=True, fc=lambda: f'={V("d_sbc")}')
    S('e_other', '  (+) Other items (impairments, product line discontinuation, ASIC, NZ product liability, stamp duty, debt extinguishment)', 'line', 'm1', data='ni_other_x', flow=True,
      hist=lambda: f'=N({V("d_impair")})+N({V("d_othop")})+N({V("d_debtext")})', fc=lambda: f'={V("d_impair")}+{V("d_othop")}+{V("d_debtext")}',
      note='FY2006–08: pre-tax items from the statement of operations (the published after-tax bridge is reproduced through the tax row).')
    S('e_pre', '  Total pre-tax adjusting items', 'line_b', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("e_ni")}),{nsum(["e_asb", "e_aicf", "e_aicf_int", "e_restr", "e_acq", "e_stepup", "e_preclose", "e_fxgain", "e_amort", "e_sbc", "e_other"])},"")')
    S('e_tax', '  (−) Tax adjustments: tax effect of the items, asbestos-related and other tax items (derived historically)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("e_pub")}),{V("e_pub")}-{V("e_ni")}-{V("e_pre")},"")', fc=lambda: f'={V("is_tax")}-{V("e_adjtax")}',
      note='Historical: published adjusted net income − GAAP net income (continuing) − pre-tax items. FY2024 and Q4 FY24 items were not itemised (headline only): this row carries the whole adjustment. Forecast: GAAP tax − adjusted tax.')
    S('e_adjni', '  = Adjusted net income (model bridge)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("e_tax")}),{V("e_ni")}+{V("e_pre")}+{V("e_tax")},"")')
    S('e_pub', '  Company-published adjusted net income ("net operating profit excluding asbestos …" FY2006–08; "Adjusted net operating profit" FY2009–21; "Adjusted net income" from FY2022)', 'memo', 'm1', data='tot_adj_ni', flow=True)
    S('e_chk', '  Check: model vs company-published (should be 0; ±0.3)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_adjni")})),IF(ABS({V("e_adjni")}-{V("e_pub")})<=0.3,0,ROUND({V("e_adjni")}-{V("e_pub")},1)),"n/p")')
    S('e_sh_in', '  Adjusted diluted shares where published (input)', 'memo', 'm1', data='tot_adj_sh_d')
    S('e_sh', '  Weighted-average diluted shares used (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("e_sh_in")}),{V("e_sh_in")},IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},""))')
    S('e_eps', 'Adjusted diluted EPS ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_eps_pub', '  Company-published adjusted diluted EPS ($; US cents to FY2022; FY2006–08 = adjusted net income ÷ diluted shares)', 'eps_memo', 'ps', data='tot_adj_eps')
    S('e_eps_chk', '  Check: model vs company-published (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_eps_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_eps_pub")})<=0.0101,0,ROUND({V("e_eps")}-{V("e_eps_pub")},2)),"n/p")')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_adjebt', '  Adjusted income before tax (income before tax + pre-tax items)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}+{V("e_pre")},"")')
    S('e_adjtax', '  Adjusted income tax (adjusted income before tax − adjusted net income)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_adjni")}),ISNUMBER({V("e_adjebt")})),{V("e_adjebt")}-{V("e_adjni")},"")', qe=lambda: f'={V("e_adjebt")}*{V("e_rate")}', ae=lambda: f'={V("e_adjebt")}*{V("e_rate")}')
    S('e_rate', '  Adjusted effective tax rate', 'pct', 'pct', all=ratio('e_adjtax', 'e_adjebt'), qe=lambda: f'={PT("pt_aetr")}', ae_in=V0['aetr'], note=V0['aetr_note'])
    S('e_rate_pub', '  Memo: company-published adjusted effective tax rate', 'pct', 'pct', data='tot_adj_etr_f')
    S('e_def', '  Definition / basis (company adjusted net income definition and presentation basis)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Net sales y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_st', '  Siding & Trim (North America fiber cement) net sales y/y %', 'growth', 'pct', all=growth('st_rev'))
    S('gm_adj', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating income (GAAP) y/y %', 'growth', 'pct', all=growth('is_op'))
    S('gm_ni', '  Net income (continuing) y/y %', 'growth', 'pct', all=growth('is_nic'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_inc', '  Incremental Adjusted EBITDA margin (Δ Adjusted EBITDA / Δ net sales)', 'pct', 'pct', all=incr('r_adj', 'is_rev'))
    S('gm_adjebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('gm_net_m', '  Net margin (continuing) %', 'pct', 'pct', all=ratio('is_nic', 'is_rev'))
    S('gm_sga', '  SG&A % of net sales', 'pct', 'pct', all=ratio('is_sga', 'is_rev'))
    S('gm_rd', '  R&D % of net sales', 'pct', 'pct', all=ratio('is_rd', 'is_rev'))
    blank()
