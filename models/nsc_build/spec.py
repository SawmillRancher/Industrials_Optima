"""Row specification of the NSC Model sheet, part 1 (MLM template layout and process):
railway operating build (units x revenue per unit by commodity group: merchandise / intermodal / coal) -> operating-ratio build
(expense classifications % of revenue, special items) -> income statement -> GAAP-to-adjusted bridges -> growth & margins."""
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
def seq(key):
    def f():
        if not CTX.col.q or CTX.col.prevq is None: return None
        return f'=IF(AND(ISNUMBER({V(key)}),ISNUMBER({PQ(key)})),IFERROR({V(key)}/{PQ(key)}-1,""),"")'
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
def ACT(key): return f'SUM({Q1}{R[key]}:{Q3}{R[key]})'    # 9M-26 actual (Q1-Q3/26)
def ACT0(key): return f'SUM({PQ1}{R[key]}:{PQ3}{R[key]})' # 9M-25 actual (Q1-Q3/25)
def B1(key): return f'{LQ}{R[key]}'                       # 30-Sep-2026 balance
def Q3c(key): return f'${Q3}${R[key]}'                    # Q3/26 (absolute)
def PQ3c(key): return f'${PQ3}${R[key]}'                  # Q3/25 (absolute)
def seas(fn, key, years=range(2016, 2026)):
    """formula over the historical Q3->Q4 sequential changes of row `key`, 2016-2025 (evaluated after row numbering)."""
    return lambda: f'={fn}(' + ','.join(f'{QC[(y, 4)].c}{R[key]}' for y in years) + ')'

GROUPS = [('merch', 'Merchandise', 'MER', 'rev_merch', 'Merchandise (agriculture, forest & consumer products; chemicals; metals & construction; automotive) — carloads'),
          ('im', 'Intermodal', 'IM', 'rev_im', 'Intermodal (domestic and international containers and trailers) — units'),
          ('coal', 'Coal', 'COAL', 'rev_coal', 'Coal (utility, export, domestic metallurgical, industrial) — carloads')]
GK = [g for g, *_ in GROUPS]
COST = [('comp', 'Compensation and benefits'), ('psr', 'Purchased services and rents'), ('fuel', 'Fuel'), ('dep', 'Depreciation'), ('mat', 'Materials and other')]
VAR = ['comp', 'psr', 'mat']                               # variable lines scaled to the operating-ratio target
SPECIAL = [('merger', 'Merger-related expenses', 'merger'), ('restr', 'Restructuring and other charges', 'restr'),
           ('eoi', 'Eastern Ohio incident (costs net of insurance recoveries)', 'eoi'), ('loss', 'Loss on asset disposal (Q1-20 locomotive rationalization)', 'loss_disp')]
SUBS = [('agr', 'Agriculture, forest & consumer products (2020+) / Agriculture products (2019) / Agriculture, consumer products & government (to 2018)'),
        ('chem', 'Chemicals'), ('metals', 'Metals and construction'), ('auto', 'Automotive'),
        ('paper', 'Paper, clay and forest products (to 2018; legacy)'), ('forest', 'Forest and consumer products (2019 only; legacy)')]

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Q4/26E block: no company guidance on EDGAR — anchors are the 9M-26 / Q3-26 '
                      'y/y trends plus a scenario Δ, and the Q3→Q4 operating-ratio seasonality (best / average / worst, 2016–25).'))
    r = 11
    SCEN_ROWS.append((r, 'out_hdr', V0['out_hdr'], 'Bull', 'Base', 'Bear', V0['out_note'])); r += 1
    for key, lab, vals, nf, note in V0['outlook']:
        SC[key] = r; SCEN_ROWS.append((r, 'out', lab, *vals, note, nf)); r += 1
    r += 1
    SCEN_ROWS.append((r, 'pt_hdr', 'Q4/26E and 2026E point estimates (all cases)', None, None, None, None)); r += 1
    for key, lab, vals, nf, note in V0['points']:
        SC[key] = r
        SCEN_ROWS.append((r, 'pt', lab, None, vals, None, note, nf)); r += 1
    r += 1
    SC['LEV'] = r
    SCEN_ROWS.append((r, 'lev', '  Maximum net debt / adjusted EBITDA before buybacks (x) — buyback plug from 2028E', *V0['lev'], V0['lev_note']))
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
    # ------------------------------------------------------------------ RAILWAY OPERATING BUILD
    S('sec_ob', 'RAILWAY OPERATING BUILD — UNITS × REVENUE PER UNIT BY COMMODITY GROUP (MERCHANDISE · INTERMODAL · COAL)', 'section',
      note='OPERATING BUILD — modelling logic (units (carloads) × average revenue per unit → railway operating revenues by commodity group → operating-ratio cost build → EPS)')
    blank()
    for g, title, code, revkey, descr in GROUPS:
        S(f'{g}_hdr', descr, 'block', note=f'{title.upper()} — modelling logic')
        S(f'{g}_units', f'  {title} units (thousands)', 'line_b', 'u', data=f'mg_units_{g}', flow=True,
          qe=lambda g=g: f'={P(g + "_units")}*(1+{V(g + "_units_g")})', ae=lambda g=g: f'={P(g + "_units")}*(1+{V(g + "_units_g")})',
          note=('Units (carloads / intermodal units) from the 10-Q / 10-K MD&A market-group tables; Q4 = year − nine months. Q4/26E: prior-year quarter × (1 + 9M-26 y/y + scenario Δ). '
                '2027E+: prior year × (1 + scenario lever).') if g == 'merch' else None)
        S(f'{g}_units_g', '    y/y %', 'growth', 'pct', all=growth(f'{g}_units'),
          qe=lambda g=g: f'={V(g + "_units_pre")}+{CH(SC["q4_vol_d"])}', ae=lambda g=g, code=code: '=' + CH(SC[f'{code}_VOL'][CTX.col.year]),
          note='Q4/26E: 9M-26 y/y units growth of the group + scenario Δ (table →). 2027E–2031E: scenario lever (Bull / Base / Bear table →).' if g == 'merch' else None)
        S(f'{g}_units_pre', '    Q4/26E volume trend (9M-26 y/y)', 'driver', 'pct', qe=lambda g=g: f'=IFERROR({ACT(g + "_units")}/{ACT0(g + "_units")}-1,0)')
        S(f'{g}_units_sq', '    sequential % (vs prior quarter)', 'growth', 'pct', all=seq(f'{g}_units'))
        S(f'{g}_rpu', f'  {title} average revenue per unit ($)', 'line_b', 'rpu', data=f'mg_rpu_{g}', avg=True,
          qe=lambda g=g: f'={P(g + "_rpu")}*(1+{V(g + "_rpu_g")})', e26=lambda g=g: f'=IFERROR({V(g + "_rev")}*1000/{V(g + "_units")},"")',
          ae=lambda g=g: f'={P(g + "_rpu")}*(1+{V(g + "_rpu_g")})',
          note=('Revenue per unit as published (10-Q / 10-K; Q4 derived = revenue ÷ units). Includes fuel surcharges (NSC: ~95% of revenue under contracts with negotiated fuel surcharges; '
                'Q3-26 fuel surcharge revenue $468m vs $208m). Q4/26E: prior-year quarter × (1 + Q3-26 y/y + scenario Δ). 2027E+: scenario lever (core price + mix + fuel surcharge).') if g == 'merch' else None)
        S(f'{g}_rpu_g', '    y/y %', 'growth', 'pct', all=growth(f'{g}_rpu'),
          qe=lambda g=g: f'={V(g + "_rpu_pre")}+{CH(SC["q4_rpu_d"])}', ae=lambda g=g, code=code: '=' + CH(SC[f'{code}_RPU'][CTX.col.year]),
          note='Q4/26E: Q3-26 y/y revenue-per-unit growth of the group (fuel surcharges lag diesel prices by ~two months) + scenario Δ. 2027E–2031E: scenario lever.' if g == 'merch' else None)
        S(f'{g}_rpu_pre', '    Q4/26E revenue-per-unit trend (Q3-26 y/y)', 'driver', 'pct', qe=lambda g=g: f'=IFERROR({Q3c(g + "_rpu")}/{PQ3c(g + "_rpu")}-1,0)')
        S(f'{g}_rev_b', f'  {title} revenue — build (units × revenue per unit)', 'line', 'm', all=lambda g=g: f'=IF(AND(ISNUMBER({V(g + "_units")}),ISNUMBER({V(g + "_rpu")})),{V(g + "_units")}*{V(g + "_rpu")}/1000,"")')
        S(f'{g}_rev', f'  {title} railway operating revenues (reported)', 'line_b', 'm', data=revkey, flow=True, fc=lambda g=g: f'={V(g + "_rev_b")}',
          note='Income-statement commodity-group revenue (as originally reported; "General merchandise" to 2012). Forecast = units × revenue per unit.' if g == 'merch' else None)
        S(f'{g}_rev_g', '    y/y %', 'growth', 'pct', all=growth(f'{g}_rev'))
        S(f'{g}_chk', f'  Check: build vs reported {title.lower()} revenue (should be 0; revenue per unit is published to the nearest $1 → tolerance ±$1m + $0.6 × units)', 'check', 'm1',
          hist=lambda g=g: f'=IF(AND(ISNUMBER({V(g + "_rev_b")}),ISNUMBER({V(g + "_rev")})),IF(ABS({V(g + "_rev_b")}-{V(g + "_rev")})<=0.0006*{V(g + "_units")}+1.1,0,ROUND({V(g + "_rev_b")}-{V(g + "_rev")},1)),"")')
        S(f'{g}_mix', f'  {title} % of total revenues', 'pct', 'pct', all=ratio(f'{g}_rev', 'is_rev'))
        if g == 'merch':
            S('ms_hdr', '  Merchandise by market group — memo, as published (basis changes: five groups to 2018; 2019 five groups incl. "Forest and consumer"; four groups from 2020):', 'sub', 'gen')
            for k, lab in SUBS:
                S(f'ms_u_{k}', f'    Units — {lab} (thousands)', 'memo', 'u', data=f'mg_units_{k}', flow=True)
            S('ms_u_chk', '    Check: Σ market-group units vs merchandise units (should be 0)', 'check', 'u',
              hist=lambda: f'=IF(ISNUMBER({V("ms_u_chem")}),IF(ABS({nsum([f"ms_u_{k}" for k, _ in SUBS])}-{V("merch_units")})<=0.15,0,ROUND({nsum([f"ms_u_{k}" for k, _ in SUBS])}-{V("merch_units")},1)),"")')
            for k, lab in SUBS:
                S(f'ms_r_{k}', f'    Revenue — {lab}', 'memo', 'm', data=f'mg_rev_{k}', flow=True)
            S('ms_r_chk', '    Check: Σ market-group revenues vs merchandise revenues (should be 0)', 'check', 'm1',
              hist=lambda: f'=IF(ISNUMBER({V("ms_r_chem")}),IF(ABS({nsum([f"ms_r_{k}" for k, _ in SUBS])}-{V("merch_rev")})<=0.6,0,ROUND({nsum([f"ms_r_{k}" for k, _ in SUBS])}-{V("merch_rev")},1)),"")')
            for k, lab in SUBS:
                S(f'ms_p_{k}', f'    Revenue per unit — {lab} ($)', 'memo', 'rpu', data=f'mg_rpu_{k}', avg=True)
            S('ms_def', '    Market-group basis (definition in force)', 'text', 'gen')
        if g == 'im':
            S('im_dom', '  Memo: domestic intermodal units (thousands)', 'memo', 'u', data='im_domestic', flow=True)
            S('im_intl', '  Memo: international intermodal units (thousands)', 'memo', 'u', data='im_international', flow=True)
            S('im_dom_p', '  Domestic % of intermodal units', 'pct', 'pct', hist=lambda: f'=IF(ISNUMBER({V("im_dom")}),IFERROR({V("im_dom")}/{V("im_units")},""),"")')
        if g == 'coal':
            for k, lab in (('utility', 'Utility'), ('export', 'Export'), ('domestic_metallurgical', 'Domestic metallurgical'), ('industrial', 'Industrial')):
                S(f'coal_t_{k}', f'  Memo: {lab} coal tonnage (thousands of tons)', 'memo', 'm', data=f'coal_{k}', flow=True)
            S('coal_t_tot', '  Memo: total coal tonnage (thousands of tons)', 'memo', 'm', data='coal_total', flow=True)
            S('coal_tpu', '  Tons per coal unit', 'line', 'm1', hist=lambda: f'=IF(AND(ISNUMBER({V("coal_t_tot")}),ISNUMBER({V("coal_units")})),IFERROR({V("coal_t_tot")}/{V("coal_units")},""),"")')
        blank()

    # ------------------------------------------------------------------ group total & revenue bridge
    S('g_hdr', 'Group Total — railway operating revenues (operating build) · volume / revenue-per-unit bridge · fuel surcharge', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_units', 'Total units (thousands)', 'total', 'u', data='mg_units_total', flow=True, fc=lambda: '=' + '+'.join(V(g + '_units') for g in GK))
    S('g_units_g', '  Total units y/y %', 'growth', 'pct', all=growth('g_units'))
    S('g_rpu', 'Average revenue per unit — total ($)', 'total', 'rpu', data='mg_rpu_total', avg=True, fc=lambda: f'=IFERROR({V("g_rev")}*1000/{V("g_units")},"")',
      e26=lambda: f'=IFERROR({V("g_rev")}*1000/{V("g_units")},"")')
    S('g_rpu_g', '  Revenue per unit y/y %', 'growth', 'pct', all=growth('g_rpu'))
    S('g_rev', 'Railway operating revenues (operating build)', 'total', 'm', hist=lambda: f'=IF(ISNUMBER({V("merch_rev")}),{V("merch_rev")}+{V("im_rev")}+{V("coal_rev")},{V("is_rev")})',
      fc=lambda: '=' + '+'.join(V(g + '_rev') for g in GK), note='Σ commodity-group revenues.')
    S('g_rev_g', '  Revenues y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: operating build vs consolidated railway operating revenues (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=0.6,0,ROUND({V("g_rev")}-{V("is_rev")},1)),"")')
    S('br_h', '  Δ revenues y/y — volume / revenue per unit by group (Σ check):', 'sub', 'gen')
    S('br_vol', '    Volume effect (Δ units × prior-year revenue per unit)', 'line', 'm',
      all=lambda: (f'=IF(ISNUMBER({V("merch_units")}),' + '+'.join(f'IFERROR(({V(g + "_units")}-{P(g + "_units")})*{P(g + "_rpu")}/1000,0)' for g in GK) + ',"")') if CTX.col.prior else None)
    S('br_rpu', '    Revenue-per-unit effect (Δ revenue per unit × units; incl. fuel surcharge and mix)', 'line', 'm',
      all=lambda: (f'=IF(ISNUMBER({V("merch_units")}),' + '+'.join(f'IFERROR(({V(g + "_rpu")}-{P(g + "_rpu")})*{V(g + "_units")}/1000,0)' for g in GK) + ',"")') if CTX.col.prior else None)
    S('br_oth', '    Rounding / other (reported Δ revenues − build effects)', 'line', 'm',
      all=lambda: (f'=IF(ISNUMBER({V("br_vol")}),{V("g_rev")}-{P("g_rev")}-{V("br_vol")}-{V("br_rpu")},"")' if CTX.col.prior else None))
    S('br_chk', '    Check: Σ effects vs Δ revenues (should be 0)', 'check', 'm1',
      all=lambda: (f'=IF(ISNUMBER({V("br_vol")}),ROUND({V("br_vol")}+{V("br_rpu")}+{V("br_oth")}-({V("g_rev")}-{P("g_rev")}),1),"")' if CTX.col.prior else None))
    S('fsc', '  Memo: fuel surcharge revenue ($m, where disclosed in the 10-Q / 10-K narrative)', 'memo', 'm', data='fsc', flow=True)
    S('fsc_p', '  Fuel surcharge % of revenues', 'pct', 'pct', hist=lambda: f'=IF(ISNUMBER({V("fsc")}),IFERROR({V("fsc")}/{V("is_rev")},""),"")')
    S('lrp_rev', '  Memo: management long-range plan revenue (merger proxy, mid-2025; not guidance)', 'memo', 'm',
      e26_in=V0['lrp']['rev'][2026], ae_in={y: V0['lrp']['rev'][y] for y in range(2027, 2031)}, note=V0['lrp']['note'])
    S('lrp_rev_d', '  Model revenues vs long-range plan (%)', 'memo_calc', 'pct', e26=lambda: f'=IFERROR({V("is_rev")}/{V("lrp_rev")}-1,"")',
      ae=lambda: (f'=IFERROR({V("is_rev")}/{V("lrp_rev")}-1,"")' if CTX.col.year <= 2030 else None))
    blank()

    # ------------------------------------------------------------------ OPERATING RATIO BUILD
    S('or_hdr', 'Operating ratio build — expense classifications % of revenues → Q4/26E seasonality anchor · 2027E+ adjusted operating-ratio lever · special items', 'block',
      note='OPERATING RATIO — modelling logic (railway operating expenses ÷ railway operating revenues; NSC\'s primary profitability KPI; adjusted = excluding the company\'s special items)')
    for k, lab in COST:
        if k == 'dep':
            S('c_dep', '  Depreciation % of revenues', 'pct', 'pct', hist=ratio('is_dep', 'is_rev'), qe=ratio('is_dep', 'is_rev'), e26=ratio('is_dep', 'is_rev'),
              ae=lambda: f'=IFERROR({V("is_dep")}/{V("is_rev")},"")', note='Depreciation is driven from the properties roll-forward (depreciation rate × opening gross properties proxy = % of opening net properties); shown here as % of revenues.')
            continue
        if k == 'fuel':
            S('c_fuel', '  Fuel % of revenues', 'pct', 'pct', hist=ratio('is_fuel', 'is_rev'), qe=ratio('is_fuel', 'is_rev'), e26=ratio('is_fuel', 'is_rev'),
              ae=lambda: '=' + CH(SC['FUEL'][CTX.col.year]),
              note='Fuel expense: Q4/26E = prior-year quarter × (1 + Q3-26 y/y fuel expense growth) — the 10-Q says Q4 fuel expense is expected to increase y/y on current fuel prices (pass-through: surcharges in revenue per unit). 2027E+: scenario lever (% of revenues).')
            continue
        S(f'c_{k}', f'  {lab} % of revenues', 'pct', 'pct', hist=ratio(f'is_{k}', 'is_rev'),
          qe=lambda k=k: f'={V("c_" + k + "_pre")}*(1+{V("or_cal")})', e26=ratio(f'is_{k}', 'is_rev'),
          ae=lambda k=k: f'=${E26}${R["c_" + k]}*{V("or_scale")}',
          note=('Q4/26E: prior-year quarter ratio + 9M-26 y/y drift, then a uniform proportional shift on the three variable lines so the adjusted operating ratio '
                'equals the seasonality anchor. 2027E+: 2026E ratios scaled pro rata so the adjusted operating ratio equals the scenario lever.') if k == 'comp' else None)
        S(f'c_{k}_pre', '    Q4/26E before calibration (prior-year quarter + 9M-26 y/y drift)', 'driver', 'pct',
          qe=lambda k=k: f'={P("c_" + k)}+IFERROR({ACT("is_" + k)}/{ACT("is_rev")}-{ACT0("is_" + k)}/{ACT0("is_rev")},0)')
    S('or_pre', '  Adjusted operating ratio before calibration (Q4/26E helper)', 'pct', 'pct',
      qe=lambda: '=' + '+'.join(V(f'c_{k}_pre') for k in VAR) + f'+{V("c_fuel")}+{V("c_dep")}')
    S('or_tgt', '  Q4/26E adjusted operating-ratio anchor: Q3/26 adjusted OR + 2016–25 Q3→Q4 sequential change (scenario: best / average / worst)', 'pct', 'pct',
      qe=lambda: f'={Q3c("or_adj")}+{CH(SC["seq_or"])}',
      note='No company guidance is filed on EDGAR (outlook is given on earnings calls only). Anchor = Q3/26 adjusted operating ratio (65.4%) + the Q3→Q4 change in adjusted OR, '
           'min / average / max over 2016–25 excl. 2024 (−2.6 pts in 2018 / +0.4 / +2.0 pts in 2025; 2024 excluded because the Q3/24 base carried $380m of line-sale gains inside "materials and other").')
    S('or_cal', '  Calibration: proportional shift on the variable cost ratios (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("or_tgt")}-{V("c_fuel")}-{V("c_dep")})/(' + '+'.join(V(f'c_{k}_pre') for k in VAR) + ')-1',
      note='Solves the uniform % change in compensation & benefits, purchased services & rents and materials & other (vs prior-year quarter + 9M drift) so the Q4/26E adjusted operating ratio equals the anchor.')
    S('or_lever', '  Adjusted operating ratio — scenario lever (2027E+)', 'pct', 'pct', ae=lambda: '=' + CH(SC['OR'][CTX.col.year]),
      note='Scenario lever OR (Bull / Base / Bear table →). Management long-range plan (merger proxy) implied 61.8% (2027) → 58.7% (2030) — information row below.')
    S('or_scale', '  Variable cost scaling vs 2026E mix (2027E+ helper)', 'line', 'x2',
      ae=lambda: f'=({V("or_lever")}-{V("c_fuel")}-{V("c_dep")})/(' + '+'.join(f'${E26}${R["c_" + k]}' for k in VAR) + ')')
    S('or_gaap', 'Operating ratio (GAAP: total railway operating expenses ÷ revenues)', 'total', 'pct', all=ratio('is_opex', 'is_rev'))
    S('or_adj', 'Adjusted operating ratio (excluding special items; company definition where published)', 'total', 'pct',
      all=lambda: f'=IF(ISNUMBER({V("is_opex")}),IFERROR(({V("is_opex")}-{V("sp_tot")})/{V("is_rev")},""),"")',
      note='= (total operating expenses − special items adjusted out) ÷ revenues. Equals the company\'s adjusted operating ratio in every period NSC published one (check in the bridge section).')
    S('or_chk', '  Check: Q4/26E adjusted OR vs seasonality anchor; 2027E+ vs scenario lever (should be 0; bps)', 'check', 'm1',
      qe=lambda: f'=ROUND(({V("or_adj")}-{V("or_tgt")})*10000,1)', ae=lambda: f'=ROUND(({V("or_adj")}-{V("or_lever")})*10000,1)')
    S('or_seq', '  Adjusted OR change vs prior quarter (pts)', 'growth', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("or_adj")}),ISNUMBER({PQ("or_adj")})),{V("or_adj")}-{PQ("or_adj")},"")' if (CTX.col.q and CTX.col.prevq) else None))
    S('or_yy', '  Adjusted OR change y/y (pts)', 'growth', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("or_adj")}),ISNUMBER({P("or_adj")})),{V("or_adj")}-{P("or_adj")},"")' if CTX.col.prior else None))
    S('lrp_or', '  Memo: long-range plan implied adjusted OR (1 − adjusted OI ÷ revenue; merger proxy, not guidance)', 'memo', 'pct',
      e26_in=V0['lrp']['or'][2026], ae_in={y: V0['lrp']['or'][y] for y in range(2027, 2031)})
    S('sp_h', '  Special items inside railway operating expenses (company-identified; adjusted out):', 'sub', 'gen')
    S('sp_merger', '  Merger-related expenses (Union Pacific; retention, advisors, legal)', 'line', 'm', data='merger', flow=True,
      qe=lambda: f'={PT("pt_merger")}', ae_in=V0['merger_ae'],
      note='9M-26 $145m ($42m Q3). Q4/26E point estimate; 2027E input through the assumed closing (30-Jun-2027), nil thereafter (assumption).')
    S('sp_restr', '  Restructuring and other charges', 'line', 'm', data='restr', flow=True, qe_in=0.0, ae_in=0.0,
      note='2024 $183m (separation programs, software rationalization), 2025 $22m, 9M-26 $6m. Forecast nil (assumption).')
    S('sp_eoi', '  Eastern Ohio incident — costs net of insurance recoveries', 'line', 'm', data='eoi', flow=True,
      qe=lambda: f'={PT("pt_eoi")}', ae_in=V0['eoi_ae'],
      note='2023 $1,116m; 2024 $325m (net of $650m recoveries); 2025 −$254m (net recoveries; $418m recoveries); 9M-26 $53m ($7m recoveries). Q4/26E point estimate; 2027E+ declining input (assumption).')
    S('sp_loss', '  Loss on asset disposal (Q1-20 locomotive rationalization, $385m)', 'line', 'm', data='loss_disp', flow=True, fc=lambda: '=0')
    S('sp_other', '  Other items inside regular expense lines (Q3-20 $99m investment impairment in purchased services & rents; 2024 railway line-sale gains −$433m in materials & other; Q4-17 tax-reform effect −$151m)',
      'line', 'm', data='sp_other', flow=True, fc=lambda: '=0', labkey='sp_other_lab')
    S('sp_resid', '  Incident-related amounts outside the "Eastern Ohio incident" line (company reconciliation effect − line item; 2025: $64m)', 'line', 'm', data='sp_resid', flow=True, fc=lambda: '=0',
      note='NSC\'s adjusted figures exclude "the overall impact on operating expenses resulting from costs and recoveries associated with the Incident", which differs from the separate income-statement line '
           '(FY2025: −$190m effect vs −$254m line; Q3-25 +$13m vs −$11m; Q4-25 +$29m vs −$11m). Derived in published periods as the reconciliation total less the itemised lines.')
    S('sp_tot', '  Total special items in operating expenses (pre-tax)', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_opex")}),{nsum(["sp_merger", "sp_restr", "sp_eoi", "sp_loss", "sp_other", "sp_resid"])},"")')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF INCOME (US GAAP)', 'section', note='CONSOLIDATED IS — forecast logic (revenues from the operating build; expenses from the operating-ratio build)')
    S('is_rev', 'Railway operating revenues', 'total', 'm', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the operating build.')
    for g, title, code, revkey, descr in GROUPS:
        S(f'is_rev_{g}', f'  {title}', 'line', 'm', data=revkey, flow=True, fc=lambda g=g: f'={V(g + "_rev")}')
    S('is_opex_h', 'Railway operating expenses', 'sub', 'gen')
    for k, lab in COST:
        if k == 'dep':
            S('is_dep', '  Depreciation', 'line', 'm', data='dep', flow=True, qe=lambda: f'={PT("pt_dep")}', ae=lambda: f'={P("bs_ppe")}*{V("ppe_dep_rate")}',
              note='Q4/26E point estimate (Q3-26 $363m, rising with the asset base). 2027E+: depreciation rate × opening net properties (schedule).')
        elif k == 'fuel':
            S('is_fuel', '  Fuel', 'line', 'm', data='fuel', flow=True, qe=lambda: f'={P("is_fuel")}*(1+IFERROR({Q3c("is_fuel")}/{PQ3c("is_fuel")}-1,0))', ae=lambda: f'={V("is_rev")}*{V("c_fuel")}')
        else:
            S(f'is_{k}', f'  {lab}', 'line', 'm', data=k, flow=True, fc=lambda k=k: f'={V("is_rev")}*{V("c_" + k)}')
    for k, lab, dk in SPECIAL:
        S(f'is_{k}', f'  {lab}', 'line', 'm', data=dk, flow=True, fc=lambda k=k: f'={V("sp_" + k)}')
    S('is_opex', 'Total railway operating expenses', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_rev")}),' + '+'.join(f'N({V("is_" + k)})' for k, _ in COST) + '+' + '+'.join(f'N({V("is_" + k)})' for k, _, _ in SPECIAL) + ',"")')
    S('is_opex_chk', '  Check: Σ expense lines vs reported total operating expenses (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_opex_pub")}),IF(ABS({V("is_opex")}-{V("is_opex_pub")})<=0.6,0,ROUND({V("is_opex")}-{V("is_opex_pub")},1)),"")')
    S('is_opex_pub', '  Memo: total railway operating expenses as reported', 'memo', 'm', data='opex', flow=True)
    S('is_oi', 'Income from railway operations', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}-{V("is_opex")},"")')
    S('is_oi_chk', '  Check: income from railway operations vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_oi_pub")}),IF(ABS({V("is_oi")}-{V("is_oi_pub")})<=0.6,0,ROUND({V("is_oi")}-{V("is_oi_pub")},1)),"")')
    S('is_oi_pub', '  Memo: income from railway operations as reported', 'memo', 'm', data='oi', flow=True)
    S('is_or', '  Operating ratio %', 'pct', 'pct', all=ratio('is_opex', 'is_rev'))
    S('is_othinc', 'Other income – net', 'line', 'm', data='oth_inc', flow=True, qe=lambda: f'={PT("pt_othinc")}',
      ae=lambda: f'={P("bs_inv")}*{V("inv_yield")}+{V("othinc_oth")}',
      note='Equity earnings of Conrail / TTX and other investments, returns on company-owned life insurance, interest income, rental income; 2024 included $59m of shareholder advisory costs and a $20m OPEB curtailment gain. '
           'Q4/26E point estimate; 2027E+: yield on opening investments + other (input).')
    S('is_int', 'Interest expense on debt', 'line', 'm', data='int', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_cp")}*{V("ds_r_cp")}', note='Q4/26E point estimate (Q3-26 $193m). 2027E+ = rate × opening notes + rate × opening commercial paper / revolver (no circularity).')
    S('is_ebt', 'Income before income taxes', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_oi")}),{V("is_oi")}+{V("is_othinc")}-{V("is_int")},"")')
    S('is_tax', 'Income taxes', 'line', 'm', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Q4/26E: 9M-26 effective rate (23.3%); 2027E+ input (federal 21% + state).')
    S('is_ni', 'Net income', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_ni_chk', '  Check: net income vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=0.6,0,ROUND({V("is_ni")}-{V("is_ni_pub")},1)),"")')
    S('is_ni_pub', '  Memo: net income as reported', 'memo', 'm', data='ni', flow=True)
    S('is_dda', '  Memo: depreciation (NSC has no acquired-intangible amortization)', 'memo_calc', 'm', all=lambda: f'={V("is_dep")}')
    S('is_sbc', '  Memo: share-based compensation (XBRL; cash-flow statement)', 'memo', 'm', data='cf_sbc', flow=True, qe=lambda: f'={PT("pt_sbc")}', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}')
    S('d_sbc_pct', '  Share-based compensation % of revenues', 'pct', 'pct', all=ratio('is_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('eps_hdr', '(Earnings per share — no stock splits in the period; share counts in millions)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={B1("bs_shares")}-${E26}${R["bb_sh"]}*0.5+${E26}${R["bb_iss"]}*0.5', ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q4/26E: shares outstanding at 30-Sep-2026 (no repurchases: suspended under the Merger Agreement) + plan issuance. 2027E+: average of beginning and ending shares. 2024+ releases print diluted shares only; basic from XBRL.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q3c("sh_dil")}-{Q3c("sh_basic")})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_basic', 'EPS – basic ($)', 'eps', 'ps', all=ratio('is_ni', 'sh_basic'))
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")',
      note='Net income ÷ weighted diluted shares. To 2016 NSC applied the two-class method (dividend equivalents on options reduce income available to common), so the computed figure can differ by up to ±$0.02 from the reported EPS.')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.02 — two-class method to 2016, share counts printed to 0.1m)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0251,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('dps', '  Dividends declared per share ($)', 'line', 'ps', data='dps', flow=True, qe_in=V0['dps_q'],
      ae=lambda: f'={P("dps")}*(1+{V("dps_g")})', note='XBRL (CommonStockDividendsPerShareDeclared; FY = annual). Quarterly dividend $1.35 since Q1-24. 2027E+: prior year × (1 + growth input).')
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'])
    S('payout', '  Dividend payout (DPS ÷ diluted EPS) %', 'pct', 'pct', all=ratio('dps', 'eps_dil'))
    blank()

    # ------------------------------------------------------------------ RECON 1: OI -> adjusted OI
    S('sec_r1', 'RECONCILIATION: INCOME FROM RAILWAY OPERATIONS → ADJUSTED INCOME FROM RAILWAY OPERATIONS / ADJUSTED OPERATING RATIO (company definition where published)', 'section',
      note='ADJUSTED OI — NSC publishes reconciliations only when special items occur (2017 tax reform; 2020 locomotive / investment impairments; 2023+ Eastern Ohio incident; 2024 railway line sales, '
           'restructuring; 2025+ merger-related expenses). Other periods: adjusted = GAAP (flagged). Model items = the company\'s own items.')
    S('o_oi', 'Income from railway operations (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_oi")}')
    S('o_items', '  (+) Special items in operating expenses (bridge above: merger, restructuring, incident, asset-disposal loss, other)', 'line', 'm', all=lambda: f'={V("sp_tot")}')
    S('o_adj', '  = Adjusted income from railway operations (model bridge)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("o_oi")}),{V("o_oi")}+{V("o_items")},"")',
      note='Equals the company-published adjusted figure in every published period; forecast = GAAP OI + forecast special items. Drives the adjusted operating ratio, adjusted EBITDA, NOPAT and the DCF.')
    S('o_adj_m', '  Adjusted operating margin % (1 − adjusted operating ratio)', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company-published adjusted income from railway operations', 'memo', 'm', data='adj_oi_pub', flow=True)
    S('o_chk', '  Check: model bridge vs company-published (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),IF(ABS({V("o_adj")}-{V("o_pub")})<=0.6,0,ROUND({V("o_adj")}-{V("o_pub")},1)),"n/p")')
    S('o_or_pub', '  Company-published adjusted operating ratio', 'memo', 'pct', data='adj_or_pub')
    S('o_or_chk', '  Check: model adjusted OR vs company-published (should be 0; published to 0.1 pt)', 'check', 'pct',
      hist=lambda: f'=IF(ISNUMBER({V("o_or_pub")}),IF(ABS({V("or_adj")}-{V("o_or_pub")})<=0.00051,0,ROUND({V("or_adj")}-{V("o_or_pub")},4)),"n/p")')
    S('o_def', '  Definition / basis (company adjusted definition in force)', 'text', 'gen', note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('o_adj_g', '  Adjusted income from railway operations y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental adjusted operating margin (Δ adjusted OI / Δ revenues)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    S('lrp_oi', '  Memo: long-range plan adjusted operating income (merger proxy; not guidance)', 'memo', 'm',
      e26_in=V0['lrp']['oi'][2026], ae_in={y: V0['lrp']['oi'][y] for y in range(2027, 2031)})
    blank()

    # ------------------------------------------------------------------ RECON 2: NI -> EBITDA -> adjusted EBITDA
    S('sec_r2', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (model definition = adjusted income from railway operations + depreciation; NSC publishes no EBITDA)', 'section',
      note='EBITDA — net income + income taxes + interest expense − other income = income from railway operations; + depreciation = EBITDA; + special items = adjusted EBITDA '
           '(same construction as the "Adjusted EBITDA" in the management projections of the merger proxy: income from railway operations before other income, depreciation and taxes, adjusted for non-recurring items)')
    S('r_ni', 'Net income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('r_tax', '  (+) Income taxes', 'line', 'm', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest expense on debt', 'line', 'm', all=lambda: f'={V("is_int")}')
    S('r_oth', '  (−) Other income – net', 'line', 'm', all=lambda: f'=-{V("is_othinc")}')
    S('r_oi', '  = Income from railway operations', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_tax")}+{V("r_int")}+{V("r_oth")},"")')
    S('r_oi_chk', '  Check: bridge vs income statement (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_oi")}),IF(ABS({V("r_oi")}-{V("is_oi")})<=0.6,0,ROUND({V("r_oi")}-{V("is_oi")},1)),"")')
    S('r_dep', '  (+) Depreciation', 'line', 'm', all=lambda: f'={V("is_dep")}')
    S('r_ebitda', '  = EBITDA', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_oi")}),ISNUMBER({V("r_dep")})),{V("r_oi")}+{V("r_dep")},"")')
    S('r_ebitda_m', '  EBITDA margin %', 'pct', 'pct', all=ratio('r_ebitda', 'is_rev'))
    S('r_items', '  (+) Special items in operating expenses', 'line', 'm', all=lambda: f'={V("sp_tot")}')
    S('r_adj', '  = Adjusted EBITDA (model)', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda")}),ISNUMBER({V("r_items")})),{V("r_ebitda")}+{V("r_items")},"")',
      note='Used for leverage (net debt / adjusted EBITDA) and EV / EBITDA.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_adj_g', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('lrp_ebitda', '  Memo: long-range plan adjusted EBITDA (merger proxy; not guidance)', 'memo', 'm',
      e26_in=V0['lrp']['ebitda'][2026], ae_in={y: V0['lrp']['ebitda'][y] for y in range(2027, 2031)})
    S('r_ebit_h', 'To adjusted EBIT (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ddan', '  (−) Depreciation', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("r_dep")}),-{V("r_dep")},"")')
    S('r_ebit', '  = Adjusted EBIT (= adjusted income from railway operations; NSC has no amortization of acquired intangibles)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+{V("r_ddan")},"")')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: cash special items (merger costs, restructuring, incident costs net of recoveries — deducted in the DCF; asset-disposal loss, impairments and gains are non-cash)', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("sp_merger")}),{V("sp_merger")}+{V("sp_restr")}+{V("sp_eoi")},"")')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: NET INCOME / DILUTED EPS → ADJUSTED NET INCOME → ADJUSTED DILUTED EPS (company definition where published)', 'section',
      note='ADJUSTED EPS — net income + pre-tax special items (operating and non-operating) − tax effect at the applicable rates − discrete tax items (2017 tax reform remeasurement, 2024 deferred-tax adjustment); '
           'company-published only when items exist, otherwise adjusted = GAAP (flagged)')
    S('e_ni', 'Net income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('e_op', '  (+) Special items in operating expenses (bridge above)', 'line', 'm', all=lambda: f'={V("sp_tot")}')
    S('e_nonop', '  (+) Non-operating items (2024 shareholder advisory costs in other income – net)', 'line', 'm', data='sp_nonop', flow=True, fc=lambda: '=0', labkey='sp_nonop_lab')
    S('e_tax', '  (−) Tax effect of the items', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("e_pub")}),ROUND({V("e_pub")}*{V("e_sh")},0)-{V("e_ni")}-{V("e_op")}-{V("e_nonop")}-N({V("e_disc")}),IF(ISNUMBER({V("e_ni")}),-({V("e_op")}+{V("e_nonop")})*{V("e_rate")},""))',
      fc=lambda: f'=-({V("e_op")}+{V("e_nonop")})*{V("is_etr")}',
      note='Published periods: derived as published adjusted EPS × diluted shares − net income − pre-tax items − discrete tax (the company applies "the applicable tax rates to which the adjustments relate"); '
           'includes rounding of the published per-share figure. Unpublished periods with items: tax-effected at the period effective rate. Forecast: at the effective tax rate.')
    S('e_rate', '  Tax rate applied (effective rate, bounded 15–40%)', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),MIN(0.4,MAX(0.15,IFERROR(({V("is_tax")}-N({V("e_disc")}))/{V("is_ebt")},0.24))),"")')
    S('e_disc', '  (+/−) Discrete tax items (Q4-17 −$3,482m deferred-tax remeasurement; Q1-24 −$27m deferred-tax adjustment; removed from adjusted)', 'line', 'm', data='sp_taxd', flow=True, fc=lambda: '=0')
    S('e_adjni', '  = Adjusted net income (model bridge)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("e_tax")}),{V("e_ni")}+{V("e_op")}+{V("e_nonop")}+{V("e_tax")}+N({V("e_disc")}),"")')
    S('e_pubni', '  Company-published adjusted net income (2017, 2020 only)', 'memo', 'm', data='adj_ni_pub', flow=True)
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted EPS – diluted ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted diluted EPS ($)', 'eps_memo', 'ps', data='adj_eps_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0101,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_def', '  Definition / basis (company adjusted EPS definition)', 'text', 'gen')
    S('lrp_eps', '  Memo: long-range plan adjusted EPS (merger proxy; not guidance)', 'memo', 'ps',
      e26_in=V0['lrp']['eps'][2026], ae_in={y: V0['lrp']['eps'][y] for y in range(2027, 2031)})
    S('lrp_eps_d', '  Model adjusted EPS vs long-range plan (%)', 'memo_calc', 'pct', e26=lambda: f'=IFERROR({V("e_eps")}/{V("lrp_eps")}-1,"")',
      ae=lambda: (f'=IFERROR({V("e_eps")}/{V("lrp_eps")}-1,"")' if CTX.col.year <= 2030 else None))
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Railway operating revenues y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_units', '  Total units y/y % (volume)', 'growth', 'pct', all=growth('g_units'))
    S('gm_rpu', '  Average revenue per unit y/y % (price, mix, fuel surcharge)', 'growth', 'pct', all=growth('g_rpu'))
    S('gm_adjoi', '  Adjusted income from railway operations y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_oi', '  Income from railway operations (GAAP) y/y %', 'growth', 'pct', all=growth('is_oi'))
    S('gm_ni', '  Net income y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_or', '  Operating ratio (GAAP) %', 'pct', 'pct', all=ratio('is_opex', 'is_rev'))
    S('gm_aor', '  Adjusted operating ratio %', 'pct', 'pct', all=lambda: f'={V("or_adj")}')
    S('gm_adjop_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_inc', '  Incremental adjusted operating margin (Δ adjusted OI / Δ revenues)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_comp', '  Compensation & benefits % of revenues', 'pct', 'pct', all=ratio('is_comp', 'is_rev'))
    S('gm_fuel', '  Fuel % of revenues', 'pct', 'pct', all=ratio('is_fuel', 'is_rev'))
    blank()
