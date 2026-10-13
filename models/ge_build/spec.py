"""Row specification of the GE Aerospace Model sheet, part 1 (MLM template layout and process):
segment build (Commercial Engines & Services: services + equipment; Defense & Propulsion Technologies; eliminations) -> segment
operating profit at the segment margin -> + adjusted Corporate & Other operating costs = operating profit (company non-GAAP) ->
run-off insurance and U.S. tax equity -> pending CPP acquisition and M&A lever -> group total & FY26 guidance calibration (2H-26)
-> cost drivers -> GAAP statement of operations -> operating-profit / EBITDA / adjusted-EPS / FCF bridges -> growth & margins."""
from fw import *

def CH(r):
    return f'CHOOSE(MATCH({SW},{{"Bull","Base","Bear"}},0),${SBULL}${r},${SBASE}${r},${SBEAR}${r})'
def PT(name): return f'${SBASE}${SC[name]}'
SC = {}

def growth(key, rc=None):
    """y/y growth; for 2026 columns, vs the Jan-2026 recast memo row (rc) where it holds a value (Q1/Q2-25, FY2025 revised)."""
    def f():
        if CTX.col.prior is None: return None
        if rc and CTX.col.year == FYC and CTX.col.kind in HISTK:
            pr = f'{CTX.col.prior}{R[rc]}'
            return (f'=IF(AND(ISNUMBER({V(key)}),ISNUMBER({P(key)})),IFERROR({V(key)}/IF(ISNUMBER({pr}),{pr},{P(key)})-1,""),"")')
        return f'=IF(AND(ISNUMBER({V(key)}),ISNUMBER({P(key)})),IFERROR({V(key)}/{P(key)}-1,""),"")'
    return f
def ratio(n, d): return lambda: f'=IF(AND(ISNUMBER({V(n)}),ISNUMBER({V(d)})),IFERROR({V(n)}/{V(d)},""),"")'
def incr(n, d):
    def f():
        if CTX.col.prior is None: return None
        return f'=IFERROR(({V(n)}-{P(n)})/({V(d)}-{P(d)}),"")'
    return f
def nsum(keys): return '+'.join(f'N({V(k)})' for k in keys)
def ACT(key): return f'SUM({Q1}{R[key]}:{Q2}{R[key]})'      # H1-26 actual (Q1-Q2/26)
def ACT0(key): return f'SUM({PQ1}{R[key]}:{PQ2}{R[key]})'   # H1-25 actual
def H2(key): return f'SUM({Q3}{R[key]}:{Q4}{R[key]})'       # 2H-26E
def B1(key): return f'{LQ}{R[key]}'                         # 30-Jun-2026 balance
def E(key): return f'${E26}${R[key]}'                       # FY2026E (absolute column)
def HALF(key): return lambda: f'={ACT(key)}/2'              # Q3/Q4-26E: H1-26 run-rate (point estimate)
def SPLIT(key, tgt):
    """Q3/Q4-26E: (FY26E target - H1-26 actual) x prior-year quarter share of 2H-25 (2025 seasonality as originally reported)."""
    return lambda: f'=({E(tgt)}-{ACT(key)})*{P(key)}/({PQ3}{R[key]}+{PQ4}{R[key]})'
def BASE25(rc): return f'${A25}${R[rc]}'                    # FY2025 revised (Jan-2026 segment structure)
LINES = [('ces_sv', 'CES_SV', 'out_ces_sv'), ('ces_eq', 'CES_EQ', 'out_ces_eq'), ('dpt', 'DPT_G', 'out_dpt')]

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
    SCEN_ROWS.append((r, 'pt_hdr', 'Q3/Q4-26E and FY26 point estimates (all cases)', None, None, None, None)); r += 1
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
    MAN_ = MAN
    # ------------------------------------------------------------------ SEGMENT BUILD
    S('sec_seg', 'SEGMENT BUILD — COMMERCIAL ENGINES & SERVICES · DEFENSE & PROPULSION TECHNOLOGIES (revenue × segment operating profit margin)', 'section',
      note='SEGMENT BUILD — modelling logic (CES services + equipment, DPT → segment revenue × margin → + adjusted Corporate & Other operating costs = operating profit → GAAP P&L)')
    blank()
    # CES
    S('ces_hdr', 'Commercial Engines & Services (CES) — commercial and business-jet engines (CFM LEAP / CFM56, GE9X, GEnx, GE90, Passport), services (MRO, spare parts); Aeroderivative moved to DPT from Q1-26',
      'block', note='CES — modelling logic')
    for k, lab, dk in (('ces_sv', 'CES services revenue (internal shop visits, spare parts, long-term service agreements)', 'ces_sv'),
                       ('ces_eq', 'CES equipment revenue (install and spare engines)', 'ces_eq')):
        code = 'CES_SV' if k == 'ces_sv' else 'CES_EQ'
        S(k, f'  {lab}', 'line', 'm', data=dk, flow=True, qe=SPLIT(k, k + '_tgt'), ae=lambda k=k: f'={P(k)}*(1+{V(k + "_g")})',
          note=('History as reported in each period (Jan-2026 structure from Q1-26). Q3/Q4-26E = (FY26E target − H1-26) × Q3/Q4-25 share of 2H-25. '
                '2027E+: prior year × (1 + scenario growth).') if k == 'ces_sv' else None)
        S(k + '_g', '    y/y % (2026: vs the recast prior year)', 'growth', 'pct', all=growth(k, k + '_rc'),
          e26=lambda k=k: f'={E(k)}/{BASE25(k + "_rc")}-1', ae=lambda code=code: '=' + CH(SC[code][CTX.col.year]),
          note='2026 quarters and FY2026E vs the Jan-2026 recast comparatives (memo row). 2027E+: scenario lever.' if k == 'ces_sv' else None)
        S(k + '_rc', '    Memo: on the Jan-2026 segment structure (Q1–Q2/25 recast in the 2026 10-Qs; FY2025 revised, $bn estimate)', 'memo', 'm', data=k + '_rc', flow=True)
        S(k + '_tgt', '    FY26E target = FY2025 revised × (1 + guided growth + calibration Δ)', 'memo_calc', 'm',
          e26=lambda k=k: f'={BASE25(k + "_rc")}*(1+{V(k + "_gp")}+{V("cal_g")})')
        S(k + '_gp', '    FY26 guided growth (scenario end-point; before calibration)', 'driver', 'pct',
          e26=lambda k=k: '=' + CH(SC[{'ces_sv': 'out_ces_sv', 'ces_eq': 'out_ces_eq'}[k]]))
    S('ces', '  CES — segment revenue', 'line_b', 'm', hist=lambda: f'={V("ces_sv")}+{V("ces_eq")}', fc=lambda: f'={V("ces_sv")}+{V("ces_eq")}')
    S('ces_g', '  CES revenue y/y % (2026: vs recast prior year)', 'growth', 'pct', all=growth('ces', 'ces_rc'),
      e26=lambda: f'={E("ces")}/{BASE25("ces_rc")}-1')
    S('ces_rc', '  Memo: CES revenue on the Jan-2026 structure (recast)', 'memo', 'm', data='ces_rc', flow=True)
    S('ces_pub', '  Memo: CES segment revenue as reported', 'memo', 'm', data='ces', flow=True)
    S('ces_chk', '  Check: services + equipment vs CES segment revenue (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("ces_pub")}),IF(ABS({V("ces")}-{V("ces_pub")})<=1.01,0,ROUND({V("ces")}-{V("ces_pub")},0)),"")')
    S('ces_op', '  CES segment operating profit', 'line', 'm', data='ces_op', flow=True, qe=lambda: f'={V("ces")}*{V("ces_m")}', ae=lambda: f'={V("ces")}*{V("ces_m")}',
      note='Segment profit as reported (company measure; after amortization and stock-based compensation). Forecast = segment revenue × margin.')
    S('ces_m', '  CES operating profit margin %', 'pct', 'pct', all=ratio('ces_op', 'ces'), qe=lambda: f'={E("ces_m_pre")}+{E("cal_m")}',
      ae=lambda: '=' + CH(SC['CES_M'][CTX.col.year]),
      note='Q3/Q4-26E: 2H margin implied by the CES operating-profit guide end-point + operating-profit calibration Δ (Group block). 2027E+: scenario lever.')
    S('ces_m_pre', '  2H-26E margin before calibration = (CES operating-profit guide − H1-26) ÷ 2H-26E revenue', 'driver', 'pct',
      e26=lambda: f'=({CH(SC["out_ces_op"])}-{ACT("ces_op")})/{H2("ces")}')
    S('ces_op_rc', '  Memo: CES operating profit on the Jan-2026 structure (recast)', 'memo', 'm', data='ces_op_rc', flow=True)
    S('ces_inc', '  Incremental margin (Δ profit / Δ revenue)', 'pct', 'pct', all=incr('ces_op', 'ces'))
    S('ces_kpi', '  Operating statistics (memo):', 'sub', 'gen')
    S('u_ce', '    Commercial engine deliveries (units; incl. LEAP)', 'memo', 'm', data='u_ce', flow=True)
    S('u_leap', '    of which LEAP engines (units)', 'memo', 'm', data='u_leap', flow=True)
    S('u_rev', '    Implied CES equipment revenue per commercial engine ($m; incl. spare engines, other equipment)', 'memo_calc', 'm2',
      hist=lambda: f'=IF(ISNUMBER({V("u_ce")}),IFERROR({V("ces_eq")}/{V("u_ce")},""),"")')
    S('u_isv', '    Internal shop visit revenue growth % (as reported; n/d for derived Q4s)', 'memo', 'pct', data='u_isv_p')
    S('ord_ces', '    CES orders', 'memo', 'm', data='ord_ces', flow=True)
    S('btb_ces', '    CES book-to-bill (orders / revenue)', 'memo_calc', 'x2', hist=lambda: f'=IF(ISNUMBER({V("ord_ces")}),IFERROR({V("ord_ces")}/{V("ces")},""),"")')
    S('rpo_ces', '    CES remaining performance obligation (period end)', 'memo', 'm', data='rpo_ces', bs=True)
    blank()
    # DPT
    S('dpt_hdr', 'Defense & Propulsion Technologies (DPT) — Defense & Systems (military engines, Aeroderivative from Q1-26) · Propulsion & Additive Technologies (Avio Aero, Unison, Dowty, Colibrium Additive)',
      'block', note='DPT — modelling logic')
    S('dpt', '  DPT — segment revenue', 'line_b', 'm', data='dpt', flow=True, qe=SPLIT('dpt', 'dpt_tgt'), ae=lambda: f'={P("dpt")}*(1+{V("dpt_g")})',
      note='Q3/Q4-26E = (FY26E target − H1-26) × Q3/Q4-25 share of 2H-25. 2027E+: prior year × (1 + scenario growth).')
    S('dpt_g', '    y/y % (2026: vs the recast prior year)', 'growth', 'pct', all=growth('dpt', 'dpt_rc'),
      e26=lambda: f'={E("dpt")}/{BASE25("dpt_rc")}-1', ae=lambda: '=' + CH(SC['DPT_G'][CTX.col.year]))
    S('dpt_rc', '    Memo: on the Jan-2026 segment structure (recast)', 'memo', 'm', data='dpt_rc', flow=True)
    S('dpt_tgt', '    FY26E target = FY2025 revised × (1 + guided growth + calibration Δ)', 'memo_calc', 'm',
      e26=lambda: f'={BASE25("dpt_rc")}*(1+{V("dpt_gp")}+{V("cal_g")})')
    S('dpt_gp', '    FY26 guided growth (scenario end-point; before calibration)', 'driver', 'pct', e26=lambda: '=' + CH(SC['out_dpt']))
    S('ds', '    Memo: Defense & Systems revenue', 'memo', 'm', data='ds', flow=True)
    S('pat', '    Memo: Propulsion & Additive Technologies revenue', 'memo', 'm', data='pat', flow=True)
    S('dpt_eq', '    Memo: DPT equipment revenue', 'memo', 'm', data='dpt_eq', flow=True)
    S('dpt_sv', '    Memo: DPT services revenue', 'memo', 'm', data='dpt_sv', flow=True)
    S('dpt_chk', '  Check: D&S + P&AT vs DPT revenue (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("ds")}),IF(ABS({V("ds")}+{V("pat")}-{V("dpt")})<=1.01,0,ROUND({V("ds")}+{V("pat")}-{V("dpt")},0)),"")')
    S('dpt_op', '  DPT segment operating profit', 'line', 'm', data='dpt_op', flow=True, qe=lambda: f'={V("dpt")}*{V("dpt_m")}', ae=lambda: f'={V("dpt")}*{V("dpt_m")}')
    S('dpt_m', '  DPT operating profit margin %', 'pct', 'pct', all=ratio('dpt_op', 'dpt'), qe=lambda: f'={E("dpt_m_pre")}+{E("cal_m")}',
      ae=lambda: '=' + CH(SC['DPT_M'][CTX.col.year]))
    S('dpt_m_pre', '  2H-26E margin before calibration = (DPT operating-profit guide − H1-26) ÷ 2H-26E revenue', 'driver', 'pct',
      e26=lambda: f'=({CH(SC["out_dpt_op"])}-{ACT("dpt_op")})/{H2("dpt")}')
    S('dpt_op_rc', '  Memo: DPT operating profit on the Jan-2026 structure (recast)', 'memo', 'm', data='dpt_op_rc', flow=True)
    S('dpt_inc', '  Incremental margin (Δ profit / Δ revenue)', 'pct', 'pct', all=incr('dpt_op', 'dpt'))
    S('u_def', '    Defense engine deliveries (units; incl. Aeroderivative from Q1-26)', 'memo', 'm', data='u_def', flow=True)
    S('ord_dpt', '    DPT orders', 'memo', 'm', data='ord_dpt', flow=True)
    S('btb_dpt', '    DPT book-to-bill (orders / revenue)', 'memo_calc', 'x2', hist=lambda: f'=IF(ISNUMBER({V("ord_dpt")}),IFERROR({V("ord_dpt")}/{V("dpt")},""),"")')
    S('rpo_dpt', '    DPT remaining performance obligation (period end)', 'memo', 'm', data='rpo_dpt', bs=True)
    blank()
    # eliminations
    S('el_hdr', 'Eliminations & other (inter-segment revenue eliminations; inside Corporate & Other revenue)', 'block', note='ELIMINATIONS — % of segment revenue')
    S('elim', '  Eliminations and other (revenue)', 'line', 'm', data='c_elim', flow=True, qe=lambda: f'=({V("ces")}+{V("dpt")})*{V("elim_p")}',
      ae=lambda: f'=({V("ces")}+{V("dpt")})*{V("elim_p")}')
    S('elim_p', '  Eliminations % of segment revenue', 'pct', 'pct', all=lambda: f'=IFERROR({V("elim")}/({V("ces")}+{V("dpt")}),"")',
      qe=lambda: f'=IFERROR({ACT("elim")}/({ACT("ces")}+{ACT("dpt")}),0)', ae_in=V0['elim_p'],
      note='Q3/Q4-26E: H1-26 ratio; 2027E+: input (FY2026E level).')
    blank()

    # ------------------------------------------------------------------ insurance & U.S. tax equity
    S('ins_hdr', 'Run-off insurance (North American Life & Health; outside operating profit) · U.S. tax equity investments', 'block',
      note='INSURANCE / TAX EQUITY — excluded from adjusted revenue, operating profit and adjusted EPS (company definitions)')
    S('ins_rev', '  Insurance revenue', 'line', 'm', data='rev_ins', flow=True, qe=HALF('ins_rev'), ae=lambda: f'={P("ins_rev")}*(1+{V("ins_g")})',
      note='Q3/Q4-26E: H1-26 run-rate (the annual premium-deficiency / assumption review in Q3 is not forecast). 2027E+: run-off decline (input).')
    S('ins_g', '  Insurance revenue y/y %', 'growth', 'pct', all=growth('ins_rev'), ae_in=V0['ins_g'])
    S('ins_cost', '  Insurance costs and expenses (company non-GAAP table)', 'line', 'm', data='ng_ins_cost', flow=True,
      qe=lambda: f'={V("ins_rev")}*(1-{V("ins_m")})', ae=lambda: f'={V("ins_rev")}*(1-{V("ins_m")})')
    S('ins_op', '  Insurance profit (pre-tax; revenue − costs)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("ins_cost")}),{V("ins_rev")}-{V("ins_cost")},"")')
    S('ins_m', '  Insurance profit margin %', 'pct', 'pct', all=ratio('ins_op', 'ins_rev'), qe=lambda: f'=IFERROR(({ACT("ins_rev")}-{ACT("ins_cost")})/{ACT("ins_rev")},0)',
      ae_in=V0['ins_m'])
    S('te_pre', '  U.S. tax equity profit (loss), pre-tax (adjusted-EPS table)', 'line', 'm', data='ae_te_pre', flow=True, qe=HALF('te_pre'), ae_in=V0['te_pre'],
      note='Renewable-energy tax-equity investments retained at the GE Vernova spin; pre-tax losses offset by tax credits (below). Forecast: H1-26 run-rate, then input.')
    S('te_tax', '  U.S. tax equity tax benefit (credits)', 'line', 'm', data='ae_te_tax', flow=True, qe=HALF('te_tax'), ae_in=V0['te_tax'])
    blank()

    # ------------------------------------------------------------------ CPP acquisition (pending)
    S('cpp_hdr', 'Pending acquisition — Consolidated Precision Products (CPP; castings), $11.75bn cash, close expected 2H-2027 (8-K 8-Sep-2026)', 'block',
      note='CPP — deal block (toggle; closing-year share; standalone revenue and EBITDA from the deal deck; synergies phased; PPA assumed)')
    S('cpp_on', '  Include CPP (1 = yes, 0 = no)', 'driver', 'gen', ae_in=1)
    S('cpp_cl', '  Closing year flag (1 in the closing year)', 'driver', 'gen', ae_in=V0['cpp_cl'])
    S('cpp_share', '  Share of the year consolidated (closing 30-Sep-2027 assumed → 0.25)', 'driver', 'pct', ae_in=V0['cpp_share'],
      note='Closing date not disclosed beyond "second half of 2027" — assumption.')
    S('cpp_sa', '  CPP standalone revenue (full year)', 'line', 'm', ae=lambda: (f'={MAN_["cpp"]["rev_2027e"]}' if CTX.col.year == FYC + 1 else f'={P("cpp_sa")}*(1+{V("cpp_g")})'),
      note='~$2.0bn 2027E revenue (deal presentation, 8-K 8-Sep-2026). 2028E+: growth input (assumption).')
    S('cpp_g', '  CPP revenue growth %', 'driver', 'pct', ae_in=V0['cpp_g'])
    S('cpp_ic', '  Share of CPP revenue sold to GE Aerospace (eliminated on consolidation; assumption — not disclosed)', 'driver', 'pct', ae_in=V0['cpp_ic'])
    S('cpp_rev', '  CPP revenue consolidated (external)', 'line_b', 'm', ae=lambda: f'={V("cpp_on")}*{V("cpp_share")}*{V("cpp_sa")}*(1-{V("cpp_ic")})')
    S('cpp_m', '  CPP EBITDA margin before synergies % ($11.75bn ÷ ~26x ≈ $452m on ~$2.0bn)', 'driver', 'pct', ae_in=V0['cpp_m'])
    S('cpp_syn', '  Net synergies (run-rate ~$200m by year 3 × phasing × scenario realisation)', 'line', 'm',
      ae=lambda: f'={V("cpp_on")}*{MAN_["cpp"]["synergies_y3"]}*{V0["cpp_phase"][CTX.col.year]}*{CH(SC["CPP_SYN"][CTX.col.year])}',
      note='Deck: ~$200m net synergies by year 3, >2x by year 6. Phasing 0% / 25% / 60% / 100% / 120% for 2027E–31E (assumption); realisation = scenario multiplier.')
    S('cpp_da', '  CPP depreciation (% of standalone revenue; assumption)', 'line', 'm', ae=lambda: f'={V("cpp_on")}*{V("cpp_share")}*{V("cpp_sa")}*{V0["cpp_dep"]}')
    S('cpp_amort', '  Amortization of acquired CPP intangibles (PPA; 35% of price over 15 years — assumption)', 'line', 'm',
      ae=lambda: f'={V("cpp_on")}*{V("cpp_share")}*{MAN_["cpp"]["price"]}*{V0["cpp_intp"]}/{V0["cpp_life"]}')
    S('cpp_op', '  CPP operating profit (EBITDA incl. inter-company sales − depreciation − PPA amortization + synergies)', 'line_b', 'm',
      ae=lambda: f'={V("cpp_on")}*{V("cpp_share")}*{V("cpp_sa")}*{V("cpp_m")}-{V("cpp_da")}-{V("cpp_amort")}+{V("cpp_syn")}',
      note='Margin on sales to GE Aerospace stays in the group (lower GE cost of sales), so the full standalone EBITDA is consolidated while only external revenue is. GE operating profit is after amortization; the deck\'s accretion basis excludes deal amortization.')
    S('cpp_ebitda_pf', '  Memo: CPP EBITDA for the full closing year (pro forma; leverage / EV)', 'memo_calc', 'm',
      ae=lambda: f'={V("cpp_on")}*{V("cpp_sa")}*{V("cpp_m")}+{V("cpp_syn")}')
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — bolt-ons beyond CPP; deals closed from 2027E)', 'block', note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=4.0, note='Aerospace components bolt-ons; CPP at ~5.9x 2027E sales. 4.0x input (assumption).')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', ae_in=0.06)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', ae=lambda: f'=N({P("m_run")})*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', ae=lambda: f'=N({P("m_run")})*(1+{V("m_g")})+0.5*{V("m_acq_sales")}', note='Mid-year convention.')
    S('m_m', '  Operating margin of acquired businesses (after amortization) %', 'driver', 'pct', ae_in=0.16)
    S('m_op', '  Operating profit from future acquisitions', 'line', 'm', ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', ae_in=0.15)
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', ae_in=0.35)
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', ae_in=15)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', ae=lambda: f'=N({P("m_cum")})+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (inside operating profit)', 'line', 'm',
      ae=lambda: f'=IFERROR((N({P("m_cum")})+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group Total — adjusted revenue & operating profit (segment build) → FY26 guidance calibration (2H-26E)', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Adjusted revenue (segment build; total revenue excl. insurance)', 'total', 'm',
      hist=lambda: f'={V("ces")}+{V("dpt")}+{V("elim")}', fc=lambda: f'={V("ces")}+{V("dpt")}+{V("elim")}+N({V("cpp_rev")})+N({V("m_rev")})',
      note='Σ CES + DPT + eliminations (+ CPP from closing + future acquisitions). Company non-GAAP "adjusted revenue".')
    S('g_rev_g', '  Adjusted revenue y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs adjusted revenue (total revenue − insurance) (should be 0; ±2 company rounding)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_adjrev")})<=2.01,0,ROUND({V("g_rev")}-{V("is_adjrev")},0)),"")')
    S('corp', '  Adjusted Corporate & Other operating costs (corporate costs + eliminations)', 'line', 'm', data='c_adj', flow=True,
      qe=lambda: f'=({CH(SC["out_corp"])}-{ACT("corp")})/2', ae=lambda: f'={V("g_rev")}*{V("corp_pct")}',
      note='Company non-GAAP (excludes insurance, U.S. tax equity, gains, restructuring, separation, impairments). Q3/Q4-26E: (FY26 guide − H1-26) ÷ 2. 2027E+: % of adjusted revenue.')
    S('corp_pct', '  Adjusted Corporate & Other operating costs % of adjusted revenue', 'pct', 'pct', all=ratio('corp', 'g_rev'), ae_in=V0['corp_pct'])
    S('corp_rc', '  Memo: on the Jan-2026 segment structure (recast; FY2025 revised $(1.0)bn)', 'memo', 'm', data='c_adj_rc', flow=True)
    S('g_op', 'Operating profit (segment build; company non-GAAP)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("ces_op")}),{V("ces_op")}+{V("dpt_op")}+{V("corp")}+N({V("cpp_op")})+N({V("m_op")}),"")',
      note='Σ segment operating profit + adjusted Corporate & Other costs (+ CPP + future acquisitions). Drives the GAAP P&L below.')
    S('g_opm', '  Operating profit margin % (of adjusted revenue)', 'pct', 'pct', all=ratio('g_op', 'g_rev'))
    S('g_op_g', '  Operating profit y/y %', 'growth', 'pct', all=growth('g_op'))
    S('g_chk_op', '  Check: segment build vs operating-profit bridge (should be 0; ±3 company rounding / derived quarters)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_op")}),ISNUMBER({V("o_op")})),IF(ABS({V("g_op")}-{V("o_op")})<=3.01,0,ROUND({V("g_op")}-{V("o_op")},0)),"")')
    S('cal_hdr', '  FY26 guidance calibration (16-Jul-2026 guide; 2H-26E):', 'sub', 'gen')
    S('cal_rev_tgt', '  Memo: FY26 adjusted revenue guidance end-point (FY2025 $42,322m × (1 + guided growth))', 'memo', 'm',
      e26=lambda: f'={Y("g_rev", 2025)}*(1+{CH(SC["out_g"])})', note=V0['rev_guid_note'])
    S('cal_rev_pre', '  Adjusted revenue before calibration (FY26E helper)', 'line', 'm',
      e26=lambda: f'={ACT("g_rev")}+(' + '+'.join(f'{BASE25(k + "_rc")}*(1+{V(k + "_gp")})-{ACT(k)}' for k, _, _ in LINES) + f')*(1+{Q3}{R["elim_p"]})')
    S('cal_rev_sens', '  Adjusted revenue sensitivity to +1.00 of growth (FY26E helper)', 'line', 'm',
      e26=lambda: '=(' + '+'.join(BASE25(k + '_rc') for k, _, _ in LINES) + f')*(1+{Q3}{R["elim_p"]})')
    S('cal_g', '  Guidance calibration: Δ growth applied to CES services, CES equipment and DPT (FY26E)', 'driver', 'pct',
      e26=lambda: f'=({V("cal_rev_tgt")}-{V("cal_rev_pre")})/{V("cal_rev_sens")}',
      note='Solves the uniform growth shift (vs the guided segment growth rates) so that FY26 adjusted revenue = the company guidance end-point for the active scenario.')
    S('cal_rev_chk', '  Check: FY26 adjusted revenue vs guidance end-point (should be 0)', 'check', 'm', e26=lambda: f'=ROUND({V("g_rev")}-{V("cal_rev_tgt")},0)')
    S('cal_op_tgt', '  Memo: FY26 operating profit guidance (scenario end-point)', 'memo', 'm', e26=lambda: '=' + CH(SC['out_op']), note=V0['op_guid_note'])
    S('cal_op_pre', '  Operating profit before calibration = CES + DPT operating-profit guides + Corporate cost guide (FY26E helper)', 'line', 'm',
      e26=lambda: f'={CH(SC["out_ces_op"])}+{CH(SC["out_dpt_op"])}+{CH(SC["out_corp"])}')
    S('cal_m', '  Guidance calibration: Δ segment margin (2H-26E, CES and DPT)', 'driver', 'pct',
      e26=lambda: f'=({V("cal_op_tgt")}-{V("cal_op_pre")})/({H2("ces")}+{H2("dpt")})',
      note='Segment and corporate guides do not sum exactly to the total; one uniform margin Δ on 2H CES and DPT revenue closes FY26 operating profit to the total guide end-point.')
    S('cal_op_chk', '  Check: FY26 operating profit vs guidance end-point (should be 0)', 'check', 'm', e26=lambda: f'=ROUND({V("g_op")}-{V("cal_op_tgt")},0)')
    S('cal_info', '  Information rows (not forced):', 'sub', 'gen')
    S('cal_ces_d', '    Model CES operating profit − CES guide end-point', 'memo_calc', 'm', e26=lambda: f'={V("ces_op")}-{CH(SC["out_ces_op"])}')
    S('cal_dpt_d', '    Model DPT operating profit − DPT guide end-point', 'memo_calc', 'm', e26=lambda: f'={V("dpt_op")}-{CH(SC["out_dpt_op"])}')
    S('cal_eps', '    Memo: FY26 adjusted EPS guidance (scenario end-point, $)', 'eps_memo', 'ps', e26=lambda: '=' + CH(SC['out_eps']))
    S('cal_eps_d', '    Model FY26 adjusted EPS − guidance ($)', 'memo_calc', 'ps', e26=lambda: f'={V("e_eps")}-{V("cal_eps")}')
    blank()

    # ------------------------------------------------------------------ cost drivers & items outside operating profit
    S('d_hdr', 'Cost drivers, D&A and items outside operating profit', 'block',
      note='COST DRIVERS — Q3/Q4-26E: H1-26 run-rate point estimates; 2027E+: % of adjusted revenue or inputs')
    S('d_dda', '  Depreciation & amortization (total; cash-flow statement)', 'line', 'm', flow=True,
      all=lambda: f'=IF(AND(ISNUMBER({V("d_dep")}),ISNUMBER({V("d_amort")})),{V("d_dep")}+{V("d_amort")},"")')
    S('d_dep', '  Depreciation & amortization of PP&E', 'line', 'm', data='cf_dep', flow=True, qe=HALF('d_dep'),
      ae=lambda: f'={V("g_rev")}*{V("d_dep_pct")}+N({V("cpp_da")})')
    S('d_dep_pct', '  PP&E depreciation % of adjusted revenue (excl. CPP)', 'pct', 'pct', all=lambda: f'=IFERROR(({V("d_dep")}-N({V("cpp_da")}))/{V("g_rev")},"")', ae_in=V0['dep_pct'])
    S('d_amort', '  Amortization of intangible assets', 'line', 'm', data='cf_amort', flow=True,
      qe=lambda: f'=({V0["amort26"]}-{ACT("d_amort")})/2', ae=lambda: f'={V("d_amort_sch")}+N({V("cpp_amort")})+N({V("m_amort")})',
      note='Q3/Q4-26E: (FY2025 10-K schedule for 2026, $351m − H1-26) ÷ 2. 2027E+: 10-K schedule + CPP PPA + future-acquisition amortization.')
    S('d_amort_sch', '  Amortization schedule — intangibles held at 31-Dec-2025 (10-K, input)', 'driver', 'm', ae_in=V0['amort_sched'], note=V0['amort_note'])
    S('d_sga', '  SG&A % of adjusted revenue', 'pct', 'pct', all=ratio('is_sga', 'g_rev'), qe=lambda: f'=IFERROR({ACT("is_sga")}/{ACT("g_rev")},"")', ae_in=V0['sga_pct'])
    S('d_rd', '  R&D % of adjusted revenue (company-funded)', 'pct', 'pct', all=ratio('is_rd', 'g_rev'), qe=lambda: f'=IFERROR({ACT("is_rd")}/{ACT("g_rev")},"")', ae_in=V0['rd_pct'])
    S('d_eqsh', '  Sales of equipment % of adjusted revenue', 'pct', 'pct', all=ratio('is_rev_eq', 'g_rev'), qe=lambda: f'=IFERROR({ACT("is_rev_eq")}/{ACT("g_rev")},"")',
      ae_in=V0['eq_share'])
    S('d_cogs_eq', '  Cost of equipment sold % of sales of equipment', 'pct', 'pct', all=ratio('is_cogs_eq', 'is_rev_eq'),
      qe=lambda: f'=IFERROR({ACT("is_cogs_eq")}/{ACT("is_rev_eq")},"")', ae_in=V0['cogs_eq'],
      note='New engines (LEAP, GE9X) are sold near or below cost; profit comes from services. Cost of services sold is the implied balancing line.')
    S('d_adjoi', '  Adjusted other income (inside operating profit: interest & investment income, equity-method income, licensing)', 'line', 'm', data='ng_adj_oi', flow=True,
      qe=HALF('d_adjoi'), ae=lambda: f'={V("g_rev")}*{V("d_adjoi_p")}')
    S('d_adjoi_p', '  Adjusted other income % of adjusted revenue', 'pct', 'pct', all=ratio('d_adjoi', 'g_rev'), ae_in=V0['adjoi_pct'])
    S('d_nonop', '  Non-operating benefit income (pension / OPEB; outside operating profit; income +)', 'line', 'm', flow=True,
      hist=lambda: f'=-{V("is_nonop")}', qe=HALF('d_nonop'), ae_in=V0['nonop'])
    S('d_items_h', '  Items excluded from operating profit / adjusted EPS (pre-tax; forecast inputs):', 'sub', 'gen')
    S('d_restr', '  Restructuring & other charges (company non-GAAP item)', 'line', 'm', data='ng_restr', flow=True, qe=HALF('d_restr'), ae_in=V0['restr'],
      note='2028E includes ~$150m of CPP one-time integration costs (assumption).')
    S('d_sep', '  Separation costs (GE HealthCare / GE Vernova)', 'line', 'm', data='ng_sep', flow=True, qe=HALF('d_sep'), ae_in=V0['sep'])
    S('d_gw', '  Goodwill impairments (Q3-24 Colibrium Additive $251m)', 'line', 'm', data='ng_gw', flow=True, fc=lambda: '=0')
    S('d_geq', '  Gains (losses) on retained / sold ownership interests and other equity securities (GE HealthCare, AerCap, BETA)', 'line', 'm', data='ng_g_eq', flow=True,
      fc=lambda: '=0', note='Mark-to-market gains / losses are not forecast (BETA Technologies investment marked to market from 2026).')
    S('d_gbiz', '  Gains (losses) on purchases and sales of business interests', 'line', 'm', data='ng_g_biz', flow=True, fc=lambda: '=0')
    S('d_nci', '  Noncontrolling interests in operating profit (bridge "add" line)', 'line', 'm', data='ng_nci_add', flow=True, fc=lambda: '=0')
    S('d_rate', '  Tax rate on adjusting items (insurance, non-operating benefit, restructuring, separation)', 'pct', 'pct', fc=lambda: f'={PT("pt_items_rate")}',
      note='H1-26 company tax effects: ~21% on non-operating benefit income, separation and restructuring.')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'STATEMENT OF OPERATIONS (US GAAP; GE Aerospace continuing operations)', 'section',
      note='CONSOLIDATED IS — forecast logic (profit before tax = operating profit + items outside operating profit; cost of services sold is implied)')
    S('is_rev_eq', 'Sales of equipment', 'line', 'm', data='rev_eq', flow=True, fc=lambda: f'={V("g_rev")}*{V("d_eqsh")}')
    S('is_rev_sv', 'Sales of services', 'line', 'm', data='rev_sv', flow=True, fc=lambda: f'={V("g_rev")}-{V("is_rev_eq")}')
    S('is_rev_ins', 'Insurance revenue', 'line', 'm', data='rev_ins', flow=True, fc=lambda: f'={V("ins_rev")}')
    S('is_rev', 'Total revenue', 'total', 'm', data='rev', flow=True, fc=lambda: f'={V("is_rev_eq")}+{V("is_rev_sv")}+{V("is_rev_ins")}')
    S('is_adjrev', '  Memo: adjusted revenue (total revenue − insurance revenue)', 'memo_calc', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}-{V("is_rev_ins")},"")')
    S('is_cogs_eq', 'Cost of equipment sold', 'line', 'm', data='cogs_eq', flow=True, fc=lambda: f'={V("is_rev_eq")}*{V("d_cogs_eq")}')
    S('is_cogs_sv', 'Cost of services sold', 'line', 'm', data='cogs_sv', flow=True,
      fc=lambda: (f'={V("is_rev")}+{V("is_oth")}-{V("is_ebt")}-{V("is_cogs_eq")}-{V("is_sga")}-{V("is_sep")}-{V("is_gw")}-{V("is_debt")}-{V("is_rd")}'
                  f'-{V("is_int")}-{V("is_ins")}-{V("is_nonop")}'),
      note='Forecast = implied balancing line (revenue + other income − profit before tax − other costs); absorbs restructuring & other charges.')
    S('is_gm', '  Gross margin % (total revenue − cost of equipment and services sold)', 'pct', 'pct',
      all=lambda: f'=IFERROR(({V("is_rev")}-{V("is_rev_ins")}-{V("is_cogs_eq")}-{V("is_cogs_sv")})/({V("is_rev")}-{V("is_rev_ins")}),"")')
    S('is_sga', 'Selling, general and administrative expenses', 'line', 'm', data='sga', flow=True, fc=lambda: f'={V("g_rev")}*{V("d_sga")}')
    S('is_sep', 'Separation costs', 'line', 'm', data='sep', flow=True, fc=lambda: f'={V("d_sep")}')
    S('is_gw', 'Goodwill impairments', 'line', 'm', data='gw_imp', flow=True, fc=lambda: f'={V("d_gw")}')
    S('is_debt', 'Debt extinguishment costs (2022)', 'line', 'm', data='debt_ext', flow=True, fc=lambda: '=0')
    S('is_rd', 'Research and development', 'line', 'm', data='rd', flow=True, fc=lambda: f'={V("g_rev")}*{V("d_rd")}')
    S('is_int', 'Interest and other financial charges', 'line', 'm', data='int', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_rev")}*{V("ds_r_rev")}+{V("ds_fees")}',
      note='Q3/Q4-26E: point estimate (H1-26 run-rate). 2027E+ = rate × opening notes + rate × opening revolver / CP + other financial charges (no circularity).')
    S('is_ins', 'Insurance losses, annuity benefits and other costs', 'line', 'm', data='ins_cost', flow=True, fc=lambda: f'={V("ins_cost")}',
      note='Forecast = insurance costs from the run-off block (the company table also includes small insurance costs in other lines).')
    S('is_nonop', 'Non-operating benefit cost (income)', 'line', 'm', data='nonop', flow=True, fc=lambda: f'=-{V("d_nonop")}')
    S('is_tcost', 'Total costs and expenses', 'line_b', 'm', data='tcost', flow=True,
      fc=lambda: f'={V("is_cogs_eq")}+{V("is_cogs_sv")}+{V("is_sga")}+{V("is_sep")}+{V("is_gw")}+{V("is_debt")}+{V("is_rd")}+{V("is_int")}+{V("is_ins")}+{V("is_nonop")}')
    S('is_oth', 'Other income (loss)', 'line', 'm', data='oth', flow=True, fc=lambda: f'={V("d_adjoi")}+{V("te_pre")}+{V("d_geq")}+{V("d_gbiz")}',
      note='Forecast = adjusted other income + U.S. tax equity result + gains (nil). Historically includes AerCap / GE HealthCare / BETA marks.')
    S('is_ebt', 'Profit before income taxes (continuing operations) — "Profit (GAAP)"', 'total', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}-{V("is_tcost")}+{V("is_oth")},"")',
      fc=lambda: (f'={V("g_op")}+{V("ins_op")}+{V("te_pre")}-{V("is_int")}+{V("d_nonop")}-{V("d_restr")}-{V("d_sep")}-{V("d_gw")}+{V("d_geq")}+{V("d_gbiz")}+{V("d_nci")}'),
      note='Forecast = operating profit + insurance profit + tax equity − interest + non-operating benefit income − restructuring − separation (+ gains).')
    S('is_ebt_m', '  Profit margin (GAAP) %', 'pct', 'pct', all=ratio('is_ebt', 'is_rev'))
    S('is_ebt_chk', '  Check: profit before tax vs reported (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_ebt_pub")}),IF(ABS({V("is_ebt")}-{V("is_ebt_pub")})<=1.01,0,ROUND({V("is_ebt")}-{V("is_ebt_pub")},0)),"")')
    S('is_ebt_pub', '  Memo: profit before income taxes as reported', 'memo', 'm', data='ebt', flow=True)
    S('is_tax', 'Provision (benefit) for income taxes', 'line', 'm', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}-{V("is_ni_cont")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'))
    S('is_ni_cont', 'Net income from continuing operations', 'line_b', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")', fc=lambda: f'={V("is_ni_cc")}+{V("is_nci")}+{V("is_pref")}',
      note='Forecast = adjusted net income + after-tax items (adjusted-EPS bridge) + NCI; tax is the residual vs profit before tax.')
    S('is_ni_cont_chk', '  Check: net income from continuing operations vs reported (should be 0; ±1, ±2 in derived quarters)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_cont_pub")}),IF(ABS({V("is_ni_cont")}-{V("is_ni_cont_pub")})<=2.01,0,ROUND({V("is_ni_cont")}-{V("is_ni_cont_pub")},0)),"")')
    S('is_ni_cont_pub', '  Memo: net income from continuing operations as reported', 'memo', 'm', data='ni_cont', flow=True)
    S('is_nci', '  Less: noncontrolling interests (continuing operations)', 'line', 'm', data='nci_cont', flow=True, fc=lambda: '=0')
    S('is_pref', '  Less: preferred dividends, excise tax / accretion on preferred redemption & rounding (derived)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_cc_pub")}),{V("is_ni_cont")}-{V("is_nci")}-{V("is_ni_cc_pub")},0)', fc=lambda: '=0',
      note='Preferred stock redeemed in 2023 (dividends and $58m excise tax in 2023); small differences are company rounding in the EPS note.')
    S('is_ni_cc', 'Net income from continuing operations attributable to common shareholders', 'total', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_cont")}),{V("is_ni_cont")}-{V("is_nci")}-{V("is_pref")},"")',
      fc=lambda: f'={V("e_adjni")}-({V("e_ins")}+{V("e_te")}+{V("e_nonop")}+{V("e_gain")}+{V("e_restr")}+{V("e_sep")}+{V("e_oth")})')
    S('is_ni_cc_pub', '  Memo: as reported (EPS-note numerator)', 'memo', 'm', data='ni_cc', flow=True)
    S('is_disc', 'Net income (loss) from discontinued operations (GE Vernova, GE HealthCare, Bank BPH)', 'line', 'm', data='disc', flow=True, fc=lambda: '=0')
    S('is_ni', 'Net income (incl. discontinued operations and NCI)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ni_cont")}),{V("is_ni_cont")}+{V("is_disc")},"")')
    S('is_dda', '  Memo: depreciation & amortization (total)', 'memo_calc', 'm', all=lambda: f'={V("d_dda")}')
    S('eps_hdr', '(Earnings per share — continuing operations)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={B1("bs_shares")}-${E26}${R["bb_sh"]}*{0.25 if CTX.col.q == 3 else 0.75}+${E26}${R["bb_iss"]}*{0.25 if CTX.col.q == 3 else 0.75}',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q3/Q4-26E: shares outstanding at 30-Jun-2026 − 2H buybacks (¼ weighted in Q3, ¾ in Q4) + equity-plan issuance. 2027E+: average of beginning and ending shares. Q4 history = 4 × FY − (Q1 + Q2 + Q3).')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q2}{R["sh_dil"]}-{Q2}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dil', 'EPS from continuing operations – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni_cc")}/{V("sh_dil")},""),"")')
    S('eps_dil_g', '  EPS y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: continuing EPS – diluted as reported ($)', 'eps_memo', 'ps', data='eps_cont_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01, ±0.03 where Q4 shares are derived)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<={0.0301 if CTX.col.q == 4 else 0.0101},0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('dps', '  Dividends declared per share ($)', 'line', 'ps', data='dps', flow=True, qe_in=V0['dps_q'], ae=lambda: f'={P("dps")}*(1+{V("dps_g")})',
      note='$0.47 a quarter in 2026 (XBRL; Q1/Q2-26). 2027E+: prior year × (1 + growth).')
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'])
    blank()

    # ------------------------------------------------------------------ RECON 1: profit (GAAP) -> operating profit
    S('sec_r1', 'RECONCILIATION: PROFIT (GAAP) → OPERATING PROFIT (company non-GAAP, as published)', 'section',
      note='OPERATING PROFIT — per the release reconciliation "Adjusted revenue, operating profit and profit margin" (GE Aerospace basis from 2023)')
    S('o_ebt', 'Profit before income taxes (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ebt")}')
    S('o_ins', '  (−) Insurance profit (insurance revenue − insurance costs)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),-({V("is_rev_ins")}-{V("ins_cost")}),"")', fc=lambda: f'=-{V("ins_op")}')
    S('o_te', '  (−) U.S. tax equity profit (loss) (other income − costs)', 'line', 'm', data='ng_te_op_neg', flow=True, fc=lambda: f'=-{V("te_pre")}')
    S('o_int', '  (+) Interest and other financial charges', 'line', 'm', flow=True, hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),{V("is_int")},"")', fc=lambda: f'={V("is_int")}')
    S('o_nonop', '  (+) Non-operating benefit cost (income)', 'line', 'm', flow=True, hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),{V("is_nonop")},"")', fc=lambda: f'={V("is_nonop")}')
    S('o_restr', '  (+) Restructuring & other', 'line', 'm', flow=True, hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),{V("d_restr")},"")', fc=lambda: f'={V("d_restr")}')
    S('o_sep', '  (+) Separation costs', 'line', 'm', flow=True, hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),{V("d_sep")},"")', fc=lambda: f'={V("d_sep")}')
    S('o_gw', '  (+) Goodwill impairments', 'line', 'm', flow=True, hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),{V("d_gw")},"")', fc=lambda: f'={V("d_gw")}')
    S('o_gain', '  (−) Gains (losses) on equity securities and business interests', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),-({V("d_geq")}+{V("d_gbiz")}),"")', fc=lambda: f'=-({V("d_geq")}+{V("d_gbiz")})')
    S('o_nci', '  (−) Noncontrolling interests', 'line', 'm', flow=True, hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),-{V("d_nci")},"")', fc=lambda: f'=-{V("d_nci")}')
    S('o_op', '  = Operating profit (model bridge)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_ins")}),{V("o_ebt")}+' + '+'.join(V(k) for k in ('o_ins', 'o_te', 'o_int', 'o_nonop', 'o_restr', 'o_sep', 'o_gw', 'o_gain', 'o_nci')) + ',"")',
      note='Forecast equals the segment build (check in the Group block).')
    S('o_opm', '  Operating profit margin % (of adjusted revenue)', 'pct', 'pct', all=ratio('o_op', 'g_rev'))
    S('o_pub', '  Company-published operating profit', 'memo', 'm', data='op_pub', flow=True)
    S('o_chk', '  Check: model bridge vs company-published (should be 0; ±3 company rounding)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),IF(ABS({V("o_op")}-{V("o_pub")})<=3.01,0,ROUND({V("o_op")}-{V("o_pub")},0)),"n/p")')
    S('o_def', '  Definition / basis (company operating-profit definition in force)', 'text', 'gen',
      note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('o_g', '  Operating profit y/y %', 'growth', 'pct', all=growth('o_op'))
    S('o_inc', '  Incremental operating margin (Δ operating profit / Δ adjusted revenue)', 'pct', 'pct', all=incr('o_op', 'g_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: EBITDA (model definition)
    S('sec_r2', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (model definition — GE Aerospace publishes no EBITDA)', 'section',
      note='EBITDA — net income from continuing operations + tax + interest + D&A = EBITDA; + operating-profit adjustments = adjusted EBITDA (= operating profit + D&A)')
    S('r_ni', 'Net income from continuing operations (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni_cont")}')
    S('r_tax', '  (+) Income taxes', 'line', 'm', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest and other financial charges', 'line', 'm', all=lambda: f'={V("is_int")}')
    S('r_dda', '  (+) Depreciation & amortization', 'line', 'm', all=lambda: f'={V("d_dda")}')
    S('r_ebitda', '  = EBITDA (model)', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_ni")}),ISNUMBER({V("r_dda")})),{V("r_ni")}+{V("r_tax")}+{V("r_int")}+{V("r_dda")},"")')
    S('r_adjx', '  (+) Operating-profit adjustments (insurance, tax equity, non-operating benefit, restructuring, separation, impairments, gains, NCI)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}-{V("o_ebt")}-{V("o_int")},"")')
    S('r_adj', '  = Adjusted EBITDA (model: operating profit + D&A)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda")}),ISNUMBER({V("r_adjx")})),{V("r_ebitda")}+{V("r_adjx")},"")',
      note='Model definition (operating profit, company definition, + depreciation & amortization). Used for leverage and EV / EBITDA.')
    S('r_adj_m', '  Adjusted EBITDA margin % (of adjusted revenue)', 'pct', 'pct', all=ratio('r_adj', 'g_rev'))
    S('r_chk', '  Check: adjusted EBITDA vs operating profit + D&A (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),ROUND({V("r_adj")}-{V("o_op")}-{V("d_dda")},0),"")')
    S('r_adj_pf', '  Memo: adjusted EBITDA pro forma (closing year incl. CPP full year), for leverage & valuation', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+N({V("cpp_cl")})*N({V("cpp_ebitda_pf")})*(1-N({V("cpp_share")})),"")')
    S('r_ebit_h', 'Adjusted EBIT, full-cost (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ebit', '  = Adjusted EBIT, full-cost (= operating profit; after amortization and stock-based compensation)', 'total', 'm', all=lambda: f'={V("o_op")}',
      note='GE Aerospace does not adjust out amortization or stock-based compensation, so operating profit is already full-cost.')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'g_rev'))
    S('r_cash', '  Memo: restructuring & separation costs (cash costs adjusted out; deducted in the DCF)', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("d_restr")}),{V("d_restr")}+{V("d_sep")},"")')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: NET INCOME FROM CONTINUING OPERATIONS → ADJUSTED NET INCOME → ADJUSTED EPS (company definition)', 'section',
      note='ADJUSTED EPS — continuing net income to common − insurance − U.S. tax equity − non-operating benefit − gains + restructuring + separation + impairments (each net of tax)')
    S('e_ni', 'Net income from continuing operations attributable to common shareholders (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni_cc")}')
    S('e_basis', '  (±) Basis difference: company starting figure − model (rounding / two-class effects)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("e_start")}),{V("e_start")}-{V("e_ni")},"")', fc=lambda: '=0')
    S('e_ins', '  (−) Insurance net income (net of tax)', 'line', 'm', data='e_ins', flow=True, fc=lambda: f'=-({V("ins_op")}-{V("ins_op")}*{V("d_rate")})')
    S('e_te', '  (−) U.S. tax equity net income (net of tax)', 'line', 'm', data='e_te', flow=True, fc=lambda: f'=-({V("te_pre")}+{V("te_tax")})')
    S('e_nonop', '  (−) Non-operating benefit income (net of tax)', 'line', 'm', data='e_nonop', flow=True, fc=lambda: f'=-{V("d_nonop")}*(1-{V("d_rate")})')
    S('e_gain', '  (−) Gains (losses) on equity securities and business interests (net of tax)', 'line', 'm', data='e_gain', flow=True, fc=lambda: '=0')
    S('e_restr', '  (+) Restructuring & other (net of tax)', 'line', 'm', data='e_restr', flow=True, fc=lambda: f'={V("d_restr")}*(1-{V("d_rate")})')
    S('e_sep', '  (+) Separation costs (net of tax)', 'line', 'm', data='e_sep', flow=True, fc=lambda: f'={V("d_sep")}*(1-{V("d_rate")})')
    S('e_oth', '  (+) Goodwill impairments, Russia & Ukraine charges, preferred excise / accretion (net of tax)', 'line', 'm', data='e_oth', flow=True, fc=lambda: '=0')
    S('e_adjni', '  = Adjusted net income (model)', 'total', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("e_basis")}),' + '+'.join(V(k) for k in ('e_ni', 'e_basis', 'e_ins', 'e_te', 'e_nonop', 'e_gain', 'e_restr', 'e_sep', 'e_oth')) + ',"")',
      fc=lambda: f'={V("e_adjebt")}-{V("e_adjtax")}',
      note='Historical: rebuilt from the published items. Forecast: (operating profit − interest) × (1 − adjusted tax rate); GAAP net income = adjusted − items.')
    S('e_pubni', '  Company-published adjusted net income', 'memo', 'm', data='adj_ni_pub', flow=True)
    S('e_ni_chk', '  Check: model vs company-published adjusted net income (should be 0; ±4 company rounding)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("e_pubni")}),IF(ABS({V("e_adjni")}-{V("e_pubni")})<=4.01,0,ROUND({V("e_adjni")}-{V("e_pubni")},0)),"n/p")')
    S('e_start', '  Memo: company starting figure (continuing net income to common, release table)', 'memo', 'm', data='ae_start', flow=True)
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted EPS – diluted ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted EPS ($)', 'eps_memo', 'ps', data='adj_eps_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.01, ±0.03 where Q4 shares are derived)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<={0.0301 if CTX.col.q == 4 else 0.0101},0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_adjebt', '  Adjusted earnings before tax (operating profit − interest and other financial charges)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}-{V("is_int")},"")')
    S('e_adjtax', '  Adjusted income tax (adjusted earnings before tax − adjusted net income)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_adjni")}),ISNUMBER({V("e_adjebt")})),{V("e_adjebt")}-{V("e_adjni")},"")',
      fc=lambda: f'={V("e_adjebt")}*{V("e_rate")}')
    S('e_rate', '  Adjusted effective tax rate (model basis)', 'pct', 'pct', all=ratio('e_adjtax', 'e_adjebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Company adjusted ETR: 17.3% FY2025, 15.7% H1-26 (OBBBA, tax benefits on global activities). Forecast input.')
    S('e_def', '  Definition / basis (company adjusted EPS definition)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Adjusted revenue y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('gm_ces', '  CES revenue y/y %', 'growth', 'pct', all=growth('ces', 'ces_rc'), e26=lambda: f'={E("ces")}/{BASE25("ces_rc")}-1')
    S('gm_dpt', '  DPT revenue y/y %', 'growth', 'pct', all=growth('dpt', 'dpt_rc'), e26=lambda: f'={E("dpt")}/{BASE25("dpt_rc")}-1')
    S('gm_op', '  Operating profit y/y %', 'growth', 'pct', all=growth('o_op'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_ebt', '  Profit before tax (GAAP) y/y %', 'growth', 'pct', all=growth('is_ebt'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_opm', '  Operating profit margin %', 'pct', 'pct', all=ratio('o_op', 'g_rev'))
    S('gm_inc', '  Incremental operating margin', 'pct', 'pct', all=incr('o_op', 'g_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'g_rev'))
    S('gm_op_m', '  Profit margin (GAAP, pre-tax) %', 'pct', 'pct', all=ratio('is_ebt', 'is_rev'))
    S('gm_net_m', '  Net margin (continuing, to common) %', 'pct', 'pct', all=ratio('is_ni_cc', 'is_rev'))
    S('gm_sga', '  SG&A % of adjusted revenue', 'pct', 'pct', all=ratio('is_sga', 'g_rev'))
    S('gm_rd', '  R&D % of adjusted revenue', 'pct', 'pct', all=ratio('is_rd', 'g_rev'))
    S('gc_ces', '  Contribution to adjusted revenue growth — CES (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("ces")}-{P("ces")})/{P("g_rev")},"")' if CTX.col.prior else None))
    S('gc_dpt', '  Contribution to adjusted revenue growth — DPT (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("dpt")}-{P("dpt")})/{P("g_rev")},"")' if CTX.col.prior else None))
    blank()
