"""Row specification of the GD Model sheet, part 1 (MLM template layout and process):
segment build (Aerospace, Marine Systems, Combat Systems, Technologies: revenue growth × operating margin, backlog roll-forward
and book-to-bill, Gulfstream deliveries) -> corporate -> M&A lever -> group total & current-year calibration (optional targets:
GD guides on the call only) -> cost drivers -> income statement -> GAAP-to-adjusted bridges (model definitions; GD publishes no
adjusted measures except free cash flow) -> growth & margins."""
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
def ACT(key): return f'SUM({Q1}{R[key]}:{Q3}{R[key]})'    # 9M 2026 actual (Q1-Q3/26)
def ACT0(key): return f'SUM({PQ1}{R[key]}:{PQ3}{R[key]})' # 9M 2025 actual (Q1-Q3/25)
def B1(key): return f'{LQ}{R[key]}'                       # 4-Oct-2026 balance
def ANNUAL(key):                                          # annualised revenue for backlog coverage (quarter × 4)
    return f'{V(key)}*{4 if CTX.col.q else 1}'

SEG = [('aero', 'Aerospace', 'AERO', 'Aerospace (Gulfstream business jets: G400 / G500 / G600 / G700 / G800; Jet Aviation completions, maintenance, FBO and aircraft-management services)'),
       ('marine', 'Marine Systems', 'MARINE', 'Marine Systems (Electric Boat: Columbia- and Virginia-class submarines; Bath Iron Works: DDG-51 destroyers; NASSCO: auxiliary / commercial ships and repair)'),
       ('combat', 'Combat Systems', 'COMBAT', 'Combat Systems (Land Systems: Abrams, Stryker; European Land Systems; Ordnance and Tactical Systems: munitions, weapons systems)'),
       ('tech', 'Technologies', 'TECH', 'Technologies (GDIT: IT services and mission support; Mission Systems: C4ISR, cyber, space payloads) — IS&T to Q1-18, Information Technology + Mission Systems Q2-18 – 2019')]
SEGK = [s for s, *_ in SEG]
ADJ = ['d_impair', 'd_disputes', 'd_restr', 'd_inv']            # operating adjusting items (company-quantified, FY2012)

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block: optional FY26 targets (blank = no calibration; GD gives guidance only on its earnings call, which is outside EDGAR — anything entered is UNVERIFIED).'))
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
    # ------------------------------------------------------------------ SEGMENT BUILD
    S('sec_seg', 'SEGMENT BUILD — AEROSPACE · MARINE SYSTEMS · COMBAT SYSTEMS · TECHNOLOGIES (revenue growth × operating margin; backlog roll-forward)', 'section',
      note='SEGMENT BUILD — modelling logic (segment revenue = prior year × (1 + growth) → segment operating earnings at the segment margin → + corporate = operating earnings → GAAP P&L; backlog = opening + orders − revenue, orders = revenue × book-to-bill)')
    blank()
    for s, title, code, descr in SEG:
        S(f'{s}_hdr', descr, 'block', note=f'{title.upper()} — modelling logic')
        S(f'{s}_rev', f'  {title} revenue', 'line_b', 'm', data=f'sr_{s}', flow=True,
          qe=lambda s=s: f'={P(s + "_rev")}*(1+{V(s + "_g")})', ae=lambda s=s: f'={P(s + "_rev")}*(1+{V(s + "_g")})',
          note=('Segment revenue as reported (release segment schedule; structure in force in each period, see the Technologies memo rows). '
                'Q4/26E: prior-year quarter × (1 + growth). 2027E+: prior year × (1 + scenario lever).') if s == 'aero' else None)
        S(f'{s}_g', '    y/y %', 'growth', 'pct', all=growth(f'{s}_rev'),
          qe=lambda s=s: f'={V(s + "_pre")}+{QEa("cal_g")}',
          ae=lambda s=s, code=code: '=' + CH(SC[f'{code}_G'][CTX.col.year]),
          note='Q4/26E: 9M-26 y/y growth of the segment + the optional revenue-target calibration Δ (Group block; 0 when no target is entered). 2027E–2031E: scenario lever (Bull/Base/Bear table →).' if s == 'aero' else None)
        S(f'{s}_pre', '    Q4/26E growth before calibration (9M-26 y/y)', 'driver', 'pct', qe=lambda s=s: f'=IFERROR({ACT(s + "_rev")}/{ACT0(s + "_rev")}-1,0)')
        S(f'{s}_mix', '    % of total revenue', 'pct', 'pct', all=ratio(f'{s}_rev', 'g_rev'))
        S(f'{s}_oi', f'  {title} operating earnings', 'line', 'm', data=f'so_{s}', flow=True,
          qe=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}', ae=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}',
          note='Segment operating earnings as reported (GAAP; after amortization of intangibles — GD allocates no corporate costs). Forecast = segment revenue × segment margin.' if s == 'aero' else None)
        S(f'{s}_m', '    Operating margin %', 'pct', 'pct', all=ratio(f'{s}_oi', f'{s}_rev'),
          qe=lambda s=s: f'={V(s + "_m_pre")}+{QEa("cal_m")}', ae=lambda s=s, code=code: '=' + CH(SC[f'{code}_M'][CTX.col.year]),
          note='Q4/26E: prior-year quarter margin + 9M-26 y/y drift + the optional EPS-target calibration Δ (0 when no target is entered). 2027E+: scenario lever.' if s == 'aero' else None)
        S(f'{s}_m_pre', '    Q4/26E margin before calibration (prior-year quarter + 9M-26 y/y drift)', 'driver', 'pct',
          qe=lambda s=s: f'={P(s + "_m")}+IFERROR({ACT(s + "_oi")}/{ACT(s + "_rev")}-{ACT0(s + "_oi")}/{ACT0(s + "_rev")},0)')
        S(f'{s}_inc', '    Incremental operating margin (Δ earnings / Δ revenue)', 'pct', 'pct', all=incr(f'{s}_oi', f'{s}_rev'))
        # backlog roll-forward
        S(f'{s}_bl', f'  {title} total backlog (period end)', 'line', 'm', data=f'bl_{s}_total',
          fc=lambda s=s: f'={PB(s + "_bl")}+{V(s + "_ord")}-{V(s + "_rev")}', e26=lambda s=s: f'={QE}{R[s + "_bl"]}',
          note='Total backlog (funded + unfunded) as reported (release backlog exhibit). Forecast: opening backlog + orders − revenue.' if s == 'aero' else None)
        S(f'{s}_bl_f', '    of which funded', 'memo', 'm', data=f'bl_{s}_funded')
        S(f'{s}_bl_u', '    of which unfunded', 'memo', 'm', data=f'bl_{s}_unfunded')
        S(f'{s}_pcv', '    Estimated potential contract value (unfunded IDIQ + unexercised options; memo)', 'memo', 'm', data=f'bl_{s}_pcv')
        S(f'{s}_ord', '    Implied orders (Δ backlog + revenue; includes backlog adjustments)', 'line', 'm',
          hist=lambda s=s: (f'=IF(AND(ISNUMBER({V(s + "_bl")}),ISNUMBER({PB(s + "_bl")})),{V(s + "_bl")}-{PB(s + "_bl")}+{V(s + "_rev")},"")' if PB(s + '_bl') else None),
          fc=lambda s=s: f'={V(s + "_rev")}*{V(s + "_b2b")}', e26=lambda s=s: f'={ACT(s + "_ord")}+{QEc(s + "_ord")}',
          note='History: derived from the backlog roll (GD publishes orders only in narrative and, for Aerospace, in the book-to-bill exhibit from Q4-18); forecast = revenue × book-to-bill input.' if s == 'aero' else None)
        S(f'{s}_b2b', '    Book-to-bill (orders ÷ revenue, x)', 'driver', 'x2', all=lambda s=s: f'=IF(ISNUMBER({V(s + "_ord")}),IFERROR({V(s + "_ord")}/{V(s + "_rev")},""),"")',
          qe_in=V0['b2b'][s]['qe'], ae_in=V0['b2b'][s]['ae'], note=V0['b2b'][s]['note'])
        S(f'{s}_cov', '    Backlog coverage (total backlog ÷ annualised revenue, years)', 'pct', 'x2',
          all=lambda s=s: f'=IF(ISNUMBER({V(s + "_bl")}),IFERROR({V(s + "_bl")}/({ANNUAL(s + "_rev")}),""),"")')
        if s == 'aero':
            S('aero_ord_pub', '    Memo: Aerospace orders as published (book-to-bill exhibit; excludes defaults, cancellations, FX and other backlog adjustments)', 'memo', 'm', data='aero_orders', flow=True)
            S('dl_hdr', '  Gulfstream aircraft deliveries (units)', 'sub', 'gen')
            S('dl_out', '    Outfitted deliveries (ASC 606 basis from 2017; completions to 2016)', 'line', 'm', data='dl_outfitted', flow=True,
              qe_in=V0['dl_qe'], ae_in=V0['dl_ae'],
              note=('2017+: Gulfstream aircraft deliveries per the release (revenue recognised at outfitted delivery under ASC 606). 2006–09: completions (release); 2010–16: outfitted deliveries '
                    '(10-Q / 10-K MD&A; Q4 = FY − 9M). Forecast: input (assumption; information row — Aerospace revenue is driven by the growth lever, not by units).'))
            S('dl_green', '    Green deliveries (revenue-recognition basis to 2016)', 'memo', 'm', data='dl_green', flow=True,
              note='Green (unfinished airframe) deliveries, the revenue-recognition event before ASC 606: release exhibit 2006–09, 10-Q / 10-K MD&A 2010–16.')
            S('dl_large', '    of which large-cabin', 'memo', 'm', data='dl_large', flow=True, note='Large-cabin / mid-cabin split published in the release exhibit 2006–09 and 2017+.')
            S('dl_mid', '    of which mid-cabin', 'memo', 'm', data='dl_mid', flow=True)
            S('dl_pre', '    Pre-owned aircraft deliveries', 'memo', 'm', data='dl_preowned', flow=True)
            S('dl_rpd', '    Implied Aerospace revenue per delivery ($m; includes Jet Aviation services)', 'pct', 'm1',
              all=lambda: f'=IF(AND(ISNUMBER({V("dl_out")}),ISNUMBER({V("aero_rev")})),IFERROR({V("aero_rev")}/{V("dl_out")},""),"")')
            S('dl_def', '    Deliveries basis', 'text', 'gen')
        if s == 'tech':
            S('tech_leg_h', '  Segment structure as reported (memo; the Technologies line above is continuous):', 'sub', 'gen')
            S('tech_ist', '    Information Systems and Technology (2006 – Q1-18)', 'memo', 'm', data='sr_ist', flow=True)
            S('tech_it', '    Information Technology (Q2-18 – 2019)', 'memo', 'm', data='sr_it', flow=True)
            S('tech_ms', '    Mission Systems (Q2-18 – 2019)', 'memo', 'm', data='sr_ms', flow=True)
            S('tech_it_oi', '    Information Technology operating earnings', 'memo', 'm', data='so_it', flow=True)
            S('tech_ms_oi', '    Mission Systems operating earnings', 'memo', 'm', data='so_ms', flow=True)
            S('tech_chk', '    Check: IT + Mission Systems vs Technologies line (should be 0)', 'check', 'm',
              hist=lambda: f'=IF(ISNUMBER({V("tech_it")}),ROUND({V("tech_it")}+{V("tech_ms")}-{V("tech_rev")},1),"")')
            S('tech_def', '    Segment basis', 'text', 'gen')
        blank()
    S('co_hdr', 'Corporate (unallocated corporate costs; not part of any segment)', 'block', note='CORPORATE — corporate office costs, pension-related corporate items; Q4/26E point estimate, 2027E+ input')
    S('corp', '  Corporate operating earnings (as reported)', 'line', 'm', data='so_corp', flow=True, qe=lambda: f'={PT("pt_corp")}', ae_in=V0['corp_ae'],
      note='Corporate as reported in the segment schedule. Q4/26E point estimate; 2027E+ input (FY2025 $(175)m; 9M-26 $(140)m).')
    blank()
    S('bl_hdr', 'Total backlog & orders (outputs)', 'block', note='BACKLOG — Σ segments')
    S('g_bl', '  Total backlog (Σ segments)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("aero_bl")}),{"+".join(V(s + "_bl") for s in SEGK)},"")')
    S('g_bl_g', '  Total backlog y/y %', 'growth', 'pct', all=growth('g_bl'))
    S('g_bl_pub', '  Memo: total backlog as published', 'memo', 'm', data='bl_tot_total')
    S('g_bl_chk', '  Check: Σ segment backlog vs published total (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("g_bl_pub")}),ROUND({V("g_bl")}-{V("g_bl_pub")},1),"")')
    S('g_tecv', '  Memo: total estimated contract value (backlog + estimated potential contract value)', 'memo', 'm', data='bl_tot_tecv')
    S('g_ord', '  Implied orders (Σ segments)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("aero_ord")}),{"+".join(V(s + "_ord") for s in SEGK)},"")')
    S('g_b2b', '  Book-to-bill (x)', 'pct', 'x2', all=lambda: f'=IF(ISNUMBER({V("g_ord")}),IFERROR({V("g_ord")}/{V("g_rev")},""),"")')
    S('g_def_b2b', '  Defense segments book-to-bill (Marine + Combat + Technologies, x)', 'pct', 'x2',
      all=lambda: f'=IF(ISNUMBER({V("g_ord")}),IFERROR(({V("marine_ord")}+{V("combat_ord")}+{V("tech_ord")})/({V("marine_rev")}+{V("combat_rev")}+{V("tech_rev")}),""),"")')
    S('g_cov', '  Backlog coverage (total backlog ÷ annualised revenue, years)', 'pct', 'x2', all=lambda: f'=IF(ISNUMBER({V("g_bl")}),IFERROR({V("g_bl")}/({ANNUAL("g_rev")}),""),"")')
    S('gc_aero', '  Contribution to total revenue growth — Aerospace (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("aero_rev")}-{P("aero_rev")})/{P("g_rev")},"")' if CTX.col.prior else None))
    S('gc_def', '  Contribution to total revenue growth — defense segments (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("marine_rev")}+{V("combat_rev")}+{V("tech_rev")}-{P("marine_rev")}-{P("combat_rev")}-{P("tech_rev")})/{P("g_rev")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — bolt-ons, unallocated; deals closed from 2027E)', 'block',
      note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention. GD has made no acquisition of size since CSRA (Apr-2018); Base = 0.')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=2.0, e26_in=0.0,
      note='CSRA (Apr-2018): $9.7bn on ~$5bn of revenue (~1.9x). 2.0x input (assumption).')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.04)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}', note='Mid-year convention.')
    S('m_m', '  Operating margin of acquired businesses (after amortization) %', 'driver', 'pct', e26_in=0.0, ae_in=0.10)
    S('m_oi', '  Operating earnings from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.07)
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.21, note='CSRA PPA: intangibles $2,066 = 21% of the $9,749 purchase price; PP&E 7%; goodwill 81%.')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=12)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (inside operating earnings)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)',
      note='GD does not adjust out amortization; the acquired-business margin above is after amortization.')
    blank()

    # ------------------------------------------------------------------ group total & calibration
    S('g_hdr', 'Group Total — revenue & operating earnings (segment build) → FY26 calibration (optional targets)', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic. GD publishes no guidance on EDGAR: the FY26 target cells are optional; blank = no calibration (Δ = 0).')
    S('g_rev', 'Revenue (segment build)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("aero_rev")}),{"+".join(V(s + "_rev") for s in SEGK)},{V("is_rev")})',
      fc=lambda: '=' + '+'.join(V(s + '_rev') for s in SEGK) + f'+N({V("m_rev")})',
      note='Σ segment revenue (+ future acquisitions from 2027E).')
    S('g_rev_g', '  Revenue y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs consolidated revenue (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),ROUND({V("g_rev")}-{V("is_rev")},1),"")')
    S('g_oi', 'Operating earnings (segment build)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("aero_oi")}),{"+".join(V(s + "_oi") for s in SEGK)}+{V("corp")}+N({V("m_oi")}),"")',
      note='Σ segment operating earnings + corporate (+ future acquisitions). GAAP operating earnings; drives the P&L below.')
    S('g_oim', '  Operating margin %', 'pct', 'pct', all=ratio('g_oi', 'is_rev'))
    S('g_oi_g', '  Operating earnings y/y %', 'growth', 'pct', all=growth('g_oi'))
    S('g_chk_oi', '  Check: segment build vs consolidated operating earnings (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_oi")}),ISNUMBER({V("is_oi")})),ROUND({V("g_oi")}-{V("is_oi")},1),"")')
    S('cal_guid', '  Memo: FY26 revenue target (optional scenario input; blank = none — GD guides on the call only, outside EDGAR)', 'memo', 'm',
      e26=lambda: f'=IF(ISNUMBER({CH(SC["out_rev"])}),{CH(SC["out_rev"])},"none")', note=V0['rev_guid_note'])
    S('cal_pre', '  Revenue before calibration (Q4/26E helper)', 'line', 'm', qe=lambda: '=' + '+'.join(f'{P(s + "_rev")}*(1+{V(s + "_pre")})' for s in SEGK))
    S('cal_sens', '  Revenue sensitivity to +1.00 of growth (Q4/26E helper)', 'line', 'm', qe=lambda: '=' + '+'.join(P(s + '_rev') for s in SEGK))
    S('cal_g', '  Calibration: Δ y/y growth applied to all segments (Q4/26E; 0 without a target)', 'driver', 'pct',
      qe=lambda: f'=IF(ISNUMBER({V("cal_guid", E26)}),({V("cal_guid", E26)}-{ACT("g_rev")}-{V("cal_pre")})/{V("cal_sens")},0)',
      note='Solves the uniform growth shift (vs 9M-26 y/y rates) so that FY26 revenue = the target for the active scenario; 0 when the target cell is blank.')
    S('cal_rev_chk', '  Check: FY26 revenue vs target (should be 0; 0 when no target)', 'check', 'm',
      e26=lambda: f'=IF(ISNUMBER({V("cal_guid")}),ROUND({V("g_rev")}-{V("cal_guid")},1),0)')
    S('cal_eps', '  Memo: FY26 diluted EPS target ($; optional scenario input; blank = none)', 'eps_memo', 'ps',
      e26=lambda: f'=IF(ISNUMBER({CH(SC["out_eps"])}),{CH(SC["out_eps"])},"none")', note=V0['eps_guid_note'])
    S('cal_ni', '  Net earnings required (FY26E diluted shares × EPS target)', 'memo_calc', 'm', e26=lambda: f'=IF(ISNUMBER({V("cal_eps")}),{V("cal_eps")}*{V("sh_dil")},"")')
    S('cal_oi', '  Q4/26E operating earnings required ((NI − 9M actual) ÷ (1 − Q4 tax rate) − Q4 interest, net − Q4 other, net)', 'memo_calc', 'm',
      e26=lambda: f'=IF(ISNUMBER({V("cal_ni")}),({V("cal_ni")}-{ACT("is_ni")})/(1-{PT("pt_etr")})-{QEc("is_int")}-{QEc("is_oth")},"")')
    S('cal_oi_pre', '  Operating earnings before margin calibration (Q4/26E helper)', 'line', 'm',
      qe=lambda: '=' + '+'.join(f'{V(s + "_rev")}*{V(s + "_m_pre")}' for s in SEGK) + f'+{V("corp")}')
    S('cal_segrev', '  Segment revenue (Q4/26E helper)', 'line', 'm', qe=lambda: '=' + '+'.join(V(s + '_rev') for s in SEGK))
    S('cal_m', '  Calibration: Δ segment margin (Q4/26E; 0 without a target)', 'driver', 'pct',
      qe=lambda: f'=IF(ISNUMBER({V("cal_oi", E26)}),({V("cal_oi", E26)}-{V("cal_oi_pre")})/{V("cal_segrev")},0)',
      note='Solves the uniform segment-margin shift so that FY26 diluted EPS = the target for the active scenario; 0 when the target cell is blank.')
    S('cal_eps_chk', '  Check: FY26 diluted EPS vs target (should be 0.00; 0 when no target)', 'check', 'ps',
      e26=lambda: f'=IF(ISNUMBER({V("cal_eps")}),ROUND({V("eps_dil")}-{V("cal_eps")},2),0)')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A & adjusting items', 'block', note='COST DRIVERS — inputs that drive forecast cost lines (Q4/26E: point estimates; 2027E+: % of revenue or schedules)')
    S('d_dda', '  Depreciation & amortization (cash-flow statement)', 'line', 'm', flow=True,
      all=lambda: f'=IF(AND(ISNUMBER({V("d_dep")}),ISNUMBER({V("d_amort")})),{V("d_dep")}+{V("d_amort")},"")',
      note='Depreciation of PP&E + amortization of intangible (and, from 2019, finance-lease right-of-use) assets, per the cash-flow statement.')
    S('d_amort', '  Amortization of intangible assets (inside operating costs; not adjusted out)', 'line', 'm', data='cf_amort', flow=True,
      qe=lambda: f'={PT("pt_amort")}', ae=lambda: f'={V("d_amort_sch")}+N({V("m_amort")})',
      note='Q4/26E point estimate. 2027E+: FY2025 10-K schedule of intangibles held at 31-Dec-2025 (+ ~$55m p.a. of finance-lease ROU amortization, assumption) + future-acquisition amortization.')
    S('d_amort_sch', '  Amortization schedule — intangibles held at 31-Dec-2025 + finance-lease ROU (input)', 'driver', 'm', ae_in=V0['amort_sched'], note=V0['amort_note'])
    S('d_dep', '  Depreciation of PP&E', 'line', 'm', data='cf_dep', flow=True, qe=lambda: f'={PT("pt_dep")}', ae=lambda: f'={V("is_rev")}*{V("d_dep_pct")}')
    S('d_dep_pct', '  Depreciation % of revenue', 'pct', 'pct', all=ratio('d_dep', 'is_rev'), ae_in=V0['dep_pct'],
      note='FY2023–25 1.3–1.4% of revenue; rising capex (shipyard capacity, Gulfstream) keeps it ~1.4%.')
    S('d_ga', '  Memo: general & administrative expenses (XBRL; inside operating costs)', 'memo', 'm', data='ga', flow=True)
    S('d_ga_pct', '  G&A % of revenue', 'pct', 'pct', all=ratio('d_ga', 'is_rev'))
    S('d_sbc', '  Equity-based compensation (cash-flow statement)', 'line', 'm', data='cf_sbc', flow=True,
      qe=lambda: f'={P("d_sbc")}*(1+IFERROR({ACT("d_sbc")}/{ACT0("d_sbc")}-1,0))', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}',
      note='Q4/26E: prior-year quarter × 9M-26 y/y; 2027E+: % of revenue. GD does not adjust out equity-based compensation.')
    S('d_sbc_pct', '  Equity-based compensation % of revenue', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_adj_h', '  Adjusting items (company-quantified one-offs, FY2012 / FY2017 only; forecast nil):', 'sub', 'gen')
    S('d_impair', '  Goodwill & intangible asset impairments (Q4-12: $1,994 IS&T goodwill + $301 intangibles)', 'line', 'm', data='oa_impair', flow=True, labkey='oa_labels', fc=lambda: '=0',
      note='Only the items GD itself quantified and excluded in its Q4-2012 / FY2012 adjusted non-GAAP reconciliation (Exhibit C) and the FY2017 tax-law item. Items GD named but did not adjust (2018 CSRA one-time charges ~$75m; 2011 Aerospace intangible impairment) are left in GAAP and in the model adjusted measures.')
    S('d_disputes', '  Contract disputes accruals (Combat Systems, European Land Systems; Q4-12)', 'line', 'm', data='oa_disputes', flow=True, fc=lambda: '=0')
    S('d_restr', '  Restructuring-related charges (Q4-12)', 'line', 'm', data='oa_restr', flow=True, fc=lambda: '=0')
    S('d_inv', '  Inventory-related charges (Q4-12)', 'line', 'm', data='oa_inv', flow=True, fc=lambda: '=0')
    S('d_debt', '  Debt retirement charge (Q4-12; in other, net — below operating earnings)', 'line', 'm', data='oa_debt', flow=True, fc=lambda: '=0')
    S('d_taxd', '  Discrete tax item (Q4-17: Tax Cuts and Jobs Act, in the provision for income tax)', 'line', 'm', data='oa_taxd', flow=True, fc=lambda: '=0')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF EARNINGS (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (operating earnings from the segment build; operating costs implied; interest on opening debt and cash; tax rate input)')
    S('is_rev', 'Revenue', 'total', 'm', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the segment build. Products / services split not carried (GD stopped printing it in the release in 2013).')
    S('is_costs', 'Operating costs and expenses', 'line', 'm', data='costs', flow=True, fc=lambda: f'={V("is_rev")}-{V("is_oi")}',
      note='Forecast = revenue − operating earnings (implied by the segment build).')
    S('is_oi', 'Operating earnings', 'total', 'm', hist=lambda: f'=IF(ISNUMBER({V("is_costs")}),{V("is_rev")}-{V("is_costs")},"")', fc=lambda: f'={V("g_oi")}')
    S('is_oi_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('is_oi_pub', '  Memo: operating earnings as reported', 'memo', 'm', data='oi', flow=True)
    S('is_oi_chk', '  Check: operating earnings vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_oi_pub")}),ROUND({V("is_oi")}-{V("is_oi_pub")},1),"")')
    S('is_oi_x', '  Memo: operating earnings per XBRL company facts (as first filed, 2008+)', 'memo', 'm', data='oi_xbrl', flow=True)
    S('is_oi_xchk', '  Check: reported vs XBRL operating earnings (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("is_oi_x")}),ISNUMBER({V("is_oi_pub")})),ROUND({V("is_oi_pub")}-{V("is_oi_x")},1),"")')
    S('is_int', 'Interest, net (expense negative)', 'line', 'm', data='int', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'=-({P("ds_notes")}*{V("ds_r_notes")}+{P("ds_cp")}*{V("ds_r_cp")})+{P("cf_end")}*{V("ds_r_cash")}',
      note='Q4/26E point estimate. 2027E+ = −(rate × opening notes + rate × opening commercial paper) + yield × opening cash (no circularity).')
    S('is_oth', 'Other, net (income positive)', 'line', 'm', data='oth', flow=True, qe=lambda: f'={PT("pt_oth")}', ae_in=V0['oth_ae'],
      note='Non-operating items (non-service pension components since 2018, investment and other). Q4-12 includes the $(123)m debt retirement charge. Forecast input.')
    S('is_ebt', 'Earnings before income tax', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_oi")}),{V("is_oi")}+{V("is_int")}+{V("is_oth")},"")')
    S('is_tax', 'Provision for income tax, net', 'line', 'm', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Q4/26E point estimate (9M-26 ETR 17.6%; FY2025 17.5%). 2027E+: input.')
    S('is_cont', 'Earnings from continuing operations', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_disc', 'Discontinued operations, net of tax', 'line', 'm', data='disc', flow=True, fc=lambda: '=0',
      note='Coal mining and Material Service crushed-stone businesses (2006), Axletech (2011), the axle business (2014–16) and other legacy items; nil in the forecast.')
    S('is_ni', 'Net earnings', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_cont")}),{V("is_cont")}+{V("is_disc")},"")')
    S('is_ni_chk', '  Check: net earnings vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),ROUND({V("is_ni")}-{V("is_ni_pub")},1),"")')
    S('is_ni_pub', '  Memo: net earnings as reported', 'memo', 'm', data='ni', flow=True)
    S('is_dda', '  Memo: depreciation & amortization', 'memo_calc', 'm', all=lambda: f'={V("d_dda")}')
    S('is_sbc', '  Memo: equity-based compensation', 'memo_calc', 'm', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share — GD has one class of common stock; no stock splits since 24-Mar-2006)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={B1("bs_shares")}-${E26}${R["bb_sh"]}*0.5+${E26}${R["bb_iss"]}*0.5',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q4/26E: shares outstanding at 4-Oct-2026 − Q4 buybacks (mid-quarter) + equity-plan issuance. 2027E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")',
      note='Net earnings / weighted diluted shares (±$0.01 vs reported; Q4-12 / FY2012 loss periods use basic shares as GD did).')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0101,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('eps_cont', '  Memo: EPS – diluted, continuing operations as reported ($)', 'eps_memo', 'ps', data='eps_d_cont')
    S('dps', '  Dividends declared per share ($)', 'line', 'ps', data='dps', flow=True, qe_in=V0['dps_q'],
      ae=lambda: f'={P("dps")}*(1+{V("dps_g")})', note='Quarterly dividend $1.59 since March 2026 ($1.50 in 2025); 29 consecutive annual increases. Q4/26E input = Q3 rate. 2027E+: prior year × (1 + growth), raised each March.')
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'])
    blank()

    # ------------------------------------------------------------------ RECON 1: operating earnings -> adjusted operating earnings
    S('sec_r1', 'RECONCILIATION: OPERATING EARNINGS → ADJUSTED OPERATING EARNINGS (model definition; GD publishes no adjusted measures except in Q4-12 / FY2012)', 'section',
      note='ADJUSTED OPERATING EARNINGS — model definition: GAAP operating earnings + the one-off items GD itself quantified and excluded (Q4-2012 Exhibit C). All other periods: adjusted = GAAP.')
    S('o_op', 'Operating earnings (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_oi")}')
    for k, lab, d in (('o_impair', '  (+) Goodwill & intangible asset impairments', 'd_impair'), ('o_disputes', '  (+) Contract disputes accruals', 'd_disputes'),
                      ('o_restr', '  (+) Restructuring-related charges', 'd_restr'), ('o_inv', '  (+) Inventory-related charges', 'd_inv')):
        S(k, lab, 'line', 'm', all=lambda d=d: f'={V(d)}')
    S('o_tot', '  Total operating adjusting items (pre-tax)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("o_impair")}),{nsum(["o_impair", "o_disputes", "o_restr", "o_inv"])},"")')
    S('o_adj', '  = Adjusted operating earnings (model)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_tot")},"")',
      note='Equals GAAP operating earnings except Q4-12 / FY2012. Forecast adjusting items nil.')
    S('o_adj_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company-published adjusted non-GAAP operating earnings (Q4-12 / FY2012 only)', 'memo', 'm', data='adj_oi_pub', flow=True)
    S('o_chk', '  Check: model vs company-published (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),ROUND({V("o_adj")}-{V("o_pub")},1),"n/p")')
    S('o_def', '  Definition / basis', 'text', 'gen', note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('o_adj_g', '  Adjusted operating earnings y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental adjusted operating margin (Δ adjusted OI / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: net earnings -> EBITDA -> adjusted EBITDA
    S('sec_r2', 'RECONCILIATION: NET EARNINGS → EBITDA → ADJUSTED EBITDA (model definitions)', 'section',
      note='EBITDA — model definition: operating earnings + depreciation + amortization (GD publishes EBITDA only in the FY2018–20 releases); adjusted EBITDA adds the operating adjusting items. Used for leverage and EV / EBITDA.')
    S('r_ni', 'Net earnings (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('r_disc', '  (−) Discontinued operations', 'line', 'm', all=lambda: f'=-{V("is_disc")}')
    S('r_tax', '  (+) Provision for income tax', 'line', 'm', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (−) Interest, net', 'line', 'm', all=lambda: f'=-{V("is_int")}')
    S('r_oth', '  (−) Other, net', 'line', 'm', all=lambda: f'=-{V("is_oth")}')
    S('r_oi', '  = Operating earnings', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_disc")}+{V("r_tax")}+{V("r_int")}+{V("r_oth")},"")')
    S('r_oi_chk', '  Check: vs statement of earnings (should be 0)', 'check', 'm', all=lambda: f'=IF(ISNUMBER({V("r_oi")}),ROUND({V("r_oi")}-{V("is_oi")},1),"")')
    S('r_dep', '  (+) Depreciation of PP&E', 'line', 'm', all=lambda: f'={V("d_dep")}')
    S('r_amort', '  (+) Amortization of intangible assets', 'line', 'm', all=lambda: f'={V("d_amort")}')
    S('r_ebitda', '  = EBITDA', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_oi")}),ISNUMBER({V("r_dep")})),{V("r_oi")}+{V("r_dep")}+{V("r_amort")},"")')
    S('r_ebitda_m', '  EBITDA margin %', 'pct', 'pct', all=ratio('r_ebitda', 'is_rev'))
    S('r_adjx', '  (+) Operating adjusting items (bridge above)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("o_tot")}),{V("o_tot")},"")')
    S('r_adj', '  = Adjusted EBITDA (model)', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda")}),ISNUMBER({V("r_adjx")})),{V("r_ebitda")}+{V("r_adjx")},"")',
      note='Model definition (= EBITDA except Q4-12 / FY2012). Used for net debt / adjusted EBITDA and EV / EBITDA.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_ebit_h', 'To adjusted EBIT (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ddan', '  (−) Depreciation & amortization', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("d_dda")}),-{V("d_dda")},"")')
    S('r_ebit', '  = Adjusted EBIT (= adjusted operating earnings; full-cost, after amortization)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+{V("r_ddan")},"")',
      note='GD does not adjust out amortization or equity-based compensation, so adjusted EBIT is full-cost.')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: cash adjusting items (restructuring, contract disputes, inventory charges; deducted in the DCF)', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_restr")}),{V("o_restr")}+{V("o_disputes")}+{V("o_inv")},"")')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: EARNINGS FROM CONTINUING OPERATIONS / DILUTED EPS → ADJUSTED NET EARNINGS → ADJUSTED EPS (company Q4-12 / FY2012 / Q4-17 / FY2017 reconciliations; model elsewhere)', 'section',
      note='ADJUSTED EPS — earnings from continuing operations + pre-tax operating items + debt retirement charge − tax effect + discrete tax items, per GD\'s own one-off reconciliations; adjusted = GAAP (continuing operations) in every other period and in the forecast')
    S('e_ni', 'Earnings from continuing operations (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_cont")}')
    S('e_op', '  (+) Operating adjusting items (pre-tax; bridge above)', 'line', 'm', all=lambda: f'={V("o_tot")}')
    S('e_debt', '  (+) Debt retirement charge (other, net; Q4-12)', 'line', 'm', all=lambda: f'={V("d_debt")}')
    S('e_tax', '  (−) Tax effect of the adjustments (limited: impairments largely non-deductible)', 'line', 'm', data='oa_tax', flow=True, fc=lambda: '=0',
      note='Company figure (Q4-12 $(240)m; FY2012 $(249)m).')
    S('e_taxd', '  (+) Discrete tax items (Q4-17 / FY2017 tax-law change)', 'line', 'm', all=lambda: f'={V("d_taxd")}')
    S('e_adjni', '  = Adjusted net earnings (model bridge)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("e_ni")}),{V("e_ni")}+{V("e_op")}+{V("e_debt")}+{V("e_tax")}+{V("e_taxd")},"")')
    S('e_pubni', '  Company-published adjusted non-GAAP earnings from continuing operations', 'memo', 'm', data='adj_ni_pub', flow=True)
    S('e_nichk', '  Check: model vs company-published adjusted earnings (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("e_pubni")}),ROUND({V("e_adjni")}-{V("e_pubni")},1),"n/p")')
    S('e_sh', '  Diluted shares used (m; company figure where published — Q4-12 used 353.2m diluted shares although the GAAP loss per share used basic)', 'line', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("e_sh_pub")}),{V("e_sh_pub")},IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},""))', fc=lambda: f'={V("sh_dil")}')
    S('e_sh_pub', '  Memo: diluted shares in the company reconciliation (m)', 'memo', 'm1', data='adj_sh')
    S('e_eps', 'Adjusted EPS – diluted, continuing operations ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted non-GAAP diluted EPS ($)', 'eps_memo', 'ps', data='adj_eps_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0101,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_def', '  Definition / basis', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Revenue y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_aero', '  Aerospace revenue y/y %', 'growth', 'pct', all=growth('aero_rev'))
    S('gm_def', '  Defense segments revenue y/y % (Marine + Combat + Technologies)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("marine_rev")}+{V("combat_rev")}+{V("tech_rev")})/({P("marine_rev")}+{P("combat_rev")}+{P("tech_rev")})-1,"")' if CTX.col.prior else None))
    S('gm_bl', '  Total backlog y/y %', 'growth', 'pct', all=growth('g_bl'))
    S('gm_op', '  Operating earnings y/y %', 'growth', 'pct', all=growth('is_oi'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_ni', '  Net earnings y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Diluted EPS y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('gm_adjop_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_inc', '  Incremental operating margin (Δ operating earnings / Δ revenue)', 'pct', 'pct', all=incr('is_oi', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_etr', '  Effective tax rate %', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'))
    blank()
