"""Row specification of the TLN Model sheet, part 1 (MLM template layout and process):
operating build (generation x adjusted energy margin per MWh + capacity revenues - adjusted operating costs = Adjusted EBITDA)
-> segment memo -> group total & FY26 / FY27 guidance calibration -> cost drivers -> income statement ->
bridges (net income -> EBITDA -> Adjusted EBITDA -> Adjusted FCF; model adjusted EPS) -> growth & margins."""
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
def ACT(key): return f'SUM({Q1}{R[key]}:{Q3}{R[key]})'    # 9M-26 actual (Q1-Q3/26)
def ACT0(key): return f'SUM({PQ1}{R[key]}:{PQ3}{R[key]})' # 9M-25 actual
def B1(key): return f'{LQ}{R[key]}'                       # 30-Sep-2026 balance
def Y27(): return CTX.col.year == FYC + 1
def tol(a, b, t=0.6, blank='""', cond=None):
    c = cond or f'AND(ISNUMBER({a}),ISNUMBER({b}))'
    return f'=IF({c},IF(ABS({a}-({b}))<={t},0,ROUND({a}-({b}),1)),{blank})'

ITEMS = [('mtm', 'MTM', 'Unrealized (gain) loss on commodity derivative contracts'), ('ndt', 'NDT', 'Nuclear decommissioning trust funds (gain) loss, net'),
         ('sbc', 'SBC', 'Stock-based and other long-term incentive compensation expense'), ('gain', 'GAIN', '(Gain) loss on asset sales, net'),
         ('imp', 'IMPAIR', 'Non-cash impairments, inventory NRV / obsolescence and other non-cash charges'),
         ('restr', 'RESTR', 'Reorganization, restructuring, hedge termination and liability-management items'),
         ('acq', 'ACQ', 'Acquisition and divestiture activities'),
         ('oth', 'OTHER', 'Other (legal settlements, unusual market events, pension, development, noncontrolling interest, other)')]

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of the company guidance ranges.'))
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
    SCEN_ROWS.append((r, 'lev', '  Target net debt / Adjusted EBITDA before buybacks (x) — buyback plug 2027E+', *V0['lev'], V0['lev_note']))
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
    yr = lambda d: {y: d[y] for y in range(FYC + 1, FYL + 1)}
    # ------------------------------------------------------------------ OPERATING BUILD
    S('sec_seg', 'OPERATING BUILD — GENERATION × ENERGY MARGIN + CAPACITY REVENUES − OPERATING COSTS = ADJUSTED EBITDA', 'section',
      note='OPERATING BUILD — modelling logic (generation TWh × adjusted energy margin $/MWh + capacity revenues − adjusted operating costs = Adjusted EBITDA (company definition) → GAAP P&L)')
    blank()
    S('gen_hdr', 'Generation (total fleet: Susquehanna nuclear, PJM gas / coal / oil; Colstrip share in Montana; acquired and sold plants for the periods owned)', 'block',
      note='GENERATION — modelling logic')
    S('gen', '  Total generation (TWh, net of station use)', 'line', 'm1', data='gen_twh', flow=True,
      qe=lambda: f'={Q3}{R["gen"]}*IFERROR({Q("gen", 2024, 4)}/{Q("gen", 2024, 3)},1)',
      ae=lambda: (f'={V("gen_pf", E26)}*(1+{V("gen_g")})' if Y27() else f'={P("gen")}*(1+{V("gen_g")})'),
      note=('As published in the earnings releases (not published for 2021–22 and Q1, Q2, Q4/23). Q4/26E: Q3/26 × the Q4/Q3 seasonal ratio of 2024 (a year with an unchanged fleet in both '
            'quarters). 2027E: 2026E pro forma full-year generation × (1 + scenario growth); 2028E+: prior year × (1 + scenario growth).'))
    S('gen_g', '    y/y %', 'growth', 'pct', all=growth('gen'), ae=lambda: '=' + CH(SC['GEN_G'][CTX.col.year]),
      note='2027E–2031E: scenario lever GEN_G (2027E is applied to the pro forma base below).')
    S('gen_pf', '  2026E pro forma generation — Cornerstone owned for the full year (TWh; analyst estimate, input)', 'driver', 'm1', e26_in=V0['gen_pf'], note=V0['gen_pf_note'])
    S('gen_cf', '  Memo: fleet capacity factor (company-published, from Q1/26; 2025 comparatives)', 'memo', 'pct', data='cap_factor')
    S('gen_cfree', '  Memo: carbon-free (nuclear) share of generation (company-published to Q4/25)', 'memo', 'pct', data='carbon_free')
    blank()
    S('em_hdr', 'Energy margin (energy & other revenues less fuel & energy purchases; realized hedges included, unrealized mark-to-market excluded)', 'block',
      note='ENERGY MARGIN — modelling logic')
    S('em', '  Adjusted energy margin (energy & other revenues − fuel & energy purchases − non-cash contract amortization)', 'line_b', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("is_en")}),{V("is_en")}-{V("is_fuel")}-N({V("d_acl")}),"")',
      qe=lambda: f'={V("gen")}*{V("em_mwh")}', ae=lambda: f'={V("gen")}*{V("em_mwh")}',
      note=('Model measure. The non-cash amortization of acquired fuel-supply contract liabilities (a credit inside fuel & energy purchases from Nov-2025; the company nets it in the D&A line of its '
            'Adjusted EBITDA reconciliation) is removed so that the margin is on the Adjusted EBITDA basis. Forecast = generation × margin per MWh.'))
    S('em_g', '    y/y %', 'growth', 'pct', all=growth('em'))
    S('em_mwh', '  Adjusted energy margin per MWh generated ($/MWh)', 'line', 'm2',
      hist=lambda: f'=IF(AND(ISNUMBER({V("em")}),ISNUMBER({V("gen")})),IFERROR({V("em")}/{V("gen")},""),"")',
      qe=lambda: f'={V("em_pre")}+{V("cal_d")}',
      ae=lambda: (f'=({V("cal27_guid")}-{V("cap")}-{V("opx")})/{V("gen")}' if Y27() else f'={P("em_mwh")}*(1+{CH(SC["EM_G"][CTX.col.year])})'),
      e26=lambda: f'=IFERROR({V("em")}/{V("gen")},"")',
      note=('Q4/26E: prior-year Q4 margin per MWh + the FY26 Adjusted EBITDA guidance calibration Δ (Group block). 2027E: solved so that Adjusted EBITDA equals the FY27 guidance end-point of the '
            'active scenario (generation, capacity revenues and costs are applied first). 2028E+: prior year × (1 + scenario lever EM_G).'))
    S('em_pre', '    Q4/26E margin per MWh before calibration (prior-year Q4)', 'driver', 'm2', qe=lambda: f'={P("em_mwh")}')
    S('fuel_mwh', '  Fuel & energy purchases per MWh, before contract amortization ($/MWh)', 'driver', 'm2',
      hist=lambda: f'=IF(AND(ISNUMBER({V("is_fuel")}),ISNUMBER({V("gen")})),IFERROR(({V("is_fuel")}+N({V("d_acl")}))/{V("gen")},""),"")',
      qe=lambda: f'={PQ("fuel_mwh")}', ae=lambda: f'={P("fuel_mwh")}', e26=lambda: f'=IFERROR(({V("is_fuel")}+{V("d_acl")})/{V("gen")},"")',
      note='Pass-through driver (sets revenues and fuel cost, not the margin): Q4/26E = Q3/26 level; 2027E+ held at the 2026E level.')
    blank()
    S('cap_hdr', 'Capacity revenues (PJM Reliability Pricing Model base residual auctions, bilateral capacity contracts, RMR arrangements)', 'block',
      note='CAPACITY — modelling logic')
    S('cap', '  Capacity revenues', 'line_b', 'm1', data='cap_rev', flow=True, qe=lambda: f'={PT("pt_cap")}',
      ae=lambda: f'={V("cap_con")}+{V("cap_open")}',
      note=('Q4/26E: expected capacity revenues for Oct–Dec 2026 (Q3-26 10-Q Note 3). 2027E+: contracted revenues (10-Q schedule of fixed-fee performance obligations) + capacity not yet '
            'auctioned or contracted (MW × $/MW-day × days). Revenue sold in the Oct-2026 capacity monetization is still recognised as revenue.'))
    S('cap_g', '    y/y %', 'growth', 'pct', all=growth('cap'))
    S('cap_con', '  Contracted capacity revenues — cleared auctions through May-2029 and contracts (10-Q Note 3, input)', 'driver', 'm1', ae_in=yr(V0['cap_con']), note=V0['cap_con_note'])
    S('cap_mw', '  Capacity assumed cleared in future auctions (MW, input)', 'driver', 'm', ae_in=yr(V0['cap_mw']), note=V0['cap_mw_note'])
    S('cap_days', '  Days in the year not covered by cleared auctions', 'driver', 'm', ae_in=yr(V0['cap_days']),
      note='PJM capacity years run 1-Jun to 31-May; auctions are cleared through the 2028/2029 year (to 31-May-2029).')
    S('cap_px', '  Assumed clearing price for future auctions ($/MW-day, scenario)', 'driver', 'm2', ae=lambda: '=' + CH(SC['CAP_PX'][CTX.col.year]),
      note='Scenario lever CAP_PX (applies from the 2029/2030 capacity year).')
    S('cap_open', '  Capacity revenues from future auctions (MW × $/MW-day × days)', 'line', 'm1', ae=lambda: f'={V("cap_mw")}*{V("cap_px")}*{V("cap_days")}/1000000')
    blank()
    S('opx_hdr', 'Operating costs on the Adjusted EBITDA basis (operation & maintenance, G&A excl. stock compensation, other income / expense, net of excluded items)', 'block',
      note='OPERATING COSTS — modelling logic')
    S('opx', '  Adjusted operating costs, net (derived: Adjusted EBITDA − energy margin − capacity revenues)', 'line_b', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}-{V("em")}-{V("cap")},"")',
      qe=lambda: f'={PT("pt_opx")}', ae=lambda: (f'={V("opx_pf", E26)}*(1+{V("opx_g")})' if Y27() else f'={P("opx")}*(1+{V("opx_g")})'),
      note=('Model measure (negative = cost): everything between the energy margin, capacity revenues and the company\'s Adjusted EBITDA. Q4/26E: point estimate. '
            '2027E: 2026E pro forma run-rate × (1 + scenario lever OPX_G); 2028E+: prior year × (1 + OPX_G).'))
    S('opx_g', '    y/y %', 'growth', 'pct', all=growth('opx'), ae=lambda: '=' + CH(SC['OPX_G'][CTX.col.year]))
    S('opx_pf', '  2026E pro forma adjusted operating costs — full-year run-rate with Cornerstone (2 × (Q3/26 + Q4/26E))', 'driver', 'm1',
      e26=lambda: f'=2*({Q3}{R["opx"]}+{QEc("opx")})', note='The second half carries the acquired fleets for the full period; the spring Susquehanna refuelling outage cost sits in Q2 (not annualised here; assumption).')
    S('opx_gaap', '  Memo: operation, maintenance & development + G&A excl. stock compensation (GAAP lines)', 'memo_calc', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("is_om")}),-({V("is_om")}+{V("is_ga")}-N({V("r_sbc")})),"")')
    S('opx_mwh', '  Adjusted operating costs per MWh generated ($/MWh)', 'line', 'm2',
      all=lambda: f'=IF(AND(ISNUMBER({V("opx")}),ISNUMBER({V("gen")})),IFERROR(-{V("opx")}/{V("gen")},""),"")')
    blank()

    # ------------------------------------------------------------------ segments memo
    S('sg_hdr', 'Reportable segment memo — PJM segment Adjusted EBITDA (current segment basis, published from the FY2024 10-K)', 'block',
      note='SEGMENTS — PJM (Susquehanna and the PJM fossil fleet) is the only reportable segment; "Other" = Colstrip share (WECC) and non-material activities')
    S('sg_pjm', '  PJM segment Adjusted EBITDA', 'line', 'm1', data='seg_pjm', flow=True)
    S('sg_oth', '  "Other" operating segment Adjusted EBITDA', 'line', 'm1', data='seg_other', flow=True)
    S('sg_corp', '  Corporate, eliminations, noncontrolling interest & other items (derived)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("sg_pjm")}),{V("r_adj_pub")}-{V("sg_pjm")}-{V("sg_oth")},"")')
    S('sg_pjm_p', '  PJM segment % of Adjusted EBITDA', 'pct', 'pct', hist=lambda: f'=IF(ISNUMBER({V("sg_pjm")}),IFERROR({V("sg_pjm")}/{V("r_adj_pub")},""),"")')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group Total — Adjusted EBITDA (operating build) → FY26 and FY27 guidance calibration', 'block', note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_adj', 'Adjusted EBITDA (operating build)', 'total', 'm1', flow=True,
      all=lambda: f'=IF(ISNUMBER({V("em")}),{V("em")}+{V("cap")}+{V("opx")},"")',
      note='Energy margin + capacity revenues + adjusted operating costs. Talen\'s Adjusted EBITDA (company definition); drives the GAAP P&L below.')
    S('g_adj_g', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('g_adj'))
    S('g_adj_mwh', '  Adjusted EBITDA per MWh generated ($/MWh)', 'line', 'm2', all=lambda: f'=IF(AND(ISNUMBER({V("g_adj")}),ISNUMBER({V("gen")})),IFERROR({V("g_adj")}/{V("gen")},""),"")')
    S('g_chk_adj', '  Check: operating build vs Adjusted EBITDA bridge (should be 0)', 'check', 'm1',
      all=lambda: tol(V('g_adj'), V('r_adj'), 0.15))
    S('cal_guid', '  Memo: FY26 Adjusted EBITDA guidance (scenario end-point)', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_eb26']), note=V0['eb26_note'])
    S('cal_pre', '  Adjusted EBITDA before calibration (Q4/26E helper)', 'line', 'm1', qe=lambda: f'={V("gen")}*{V("em_pre")}+{V("cap")}+{V("opx")}')
    S('cal_sens', '  Adjusted EBITDA sensitivity to +$1.00/MWh of energy margin (Q4/26E helper)', 'line', 'm1', qe=lambda: f'={V("gen")}')
    S('cal_d', '  Guidance calibration: Δ energy margin per MWh (Q4/26E, $/MWh)', 'driver', 'm2',
      qe=lambda: f'=({V("cal_guid", E26)}-{ACT("g_adj")}-{V("cal_pre")})/{V("cal_sens")}',
      note='Solves the Q4/26E energy margin per MWh (the least-guided driver) so that FY26 Adjusted EBITDA = the guidance end-point for the active scenario; closed form, no circularity.')
    S('cal_chk', '  Check: FY26 Adjusted EBITDA vs guidance end-point (should be 0)', 'check', 'm1', e26=lambda: f'=ROUND({V("g_adj")}-{V("cal_guid")},1)')
    S('cal27_guid', '  Memo: FY27 Adjusted EBITDA guidance (scenario end-point)', 'memo', 'm1', ae=lambda: ('=' + CH(SC['out_eb27'])) if Y27() else None, note=V0['eb27_note'])
    S('cal27_chk', '  Check: FY27 Adjusted EBITDA vs guidance end-point (should be 0)', 'check', 'm1', ae=lambda: (f'=ROUND({V("g_adj")}-{V("cal27_guid")},1)') if Y27() else None)
    S('cal_fcf', '  Memo: Adjusted Free Cash Flow guidance (scenario end-point) — information, not forced', 'memo', 'm1',
      e26=lambda: '=' + CH(SC['out_fcf26']), ae=lambda: ('=' + CH(SC['out_fcf27'])) if Y27() else None)
    S('cal_fcf_d', '    Model Adjusted Free Cash Flow − guidance', 'memo_calc', 'm1', e26=lambda: f'={V("f_fcf")}-{V("cal_fcf")}',
      ae=lambda: (f'={V("f_fcf")}-{V("cal_fcf")}') if Y27() else None)
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A & adjusting items', 'block', note='COST DRIVERS — inputs that drive forecast cost lines (Q4/26E: point estimates from guidance less nine months; 2027E+: guidance, schedules or inputs)')
    S('d_dda', '  Depreciation, amortization & accretion (income statement)', 'line', 'm1', flow=True, all=lambda: f'={V("is_dda")}')
    S('d_dda_p', '  D&A % of opening property, plant & equipment', 'pct', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("is_dda")}),ISNUMBER({P("bs_ppe")})),IFERROR({V("is_dda")}/{P("bs_ppe")},""),"")' if (CTX.col.prior and not CTX.col.q) else None),
      ae=lambda: f'=IFERROR({V("is_dda")}/{P("bs_ppe")},"")' if Y27() else f'={P("d_dda_p")}',
      note='2027E: D&A per the FY27 guidance reconciliation ($650m); 2028E+: 2027E rate on opening PP&E held.')
    S('d_acl', '  Non-cash amortization of acquired contract liabilities (credit in fuel & energy purchases; = IS D&A − reconciliation D&A)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("r_dda")}),{V("is_dda")}-{V("r_dda")},"")', qe=lambda: f'={PT("pt_acl")}', ae_in=yr(V0['acl']), note=V0['acl_note'])
    S('d_gax', '  G&A excluding stock-based compensation', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("is_ga")}),{V("is_ga")}-N({V("r_sbc")}),"")', qe=lambda: f'={PT("pt_gax")}', ae=lambda: f'={P("d_gax")}*(1+{V("opx_g")})',
      e26=lambda: f'={V("is_ga")}-{V("r_sbc")}',
      note='History: G&A less the stock-based and long-term incentive compensation of the Adjusted EBITDA reconciliation. Presentation driver only (O&M is the balancing line).')
    S('d_sbc', '  Stock-based & long-term incentive compensation (reconciliation line)', 'line', 'm1', flow=True, hist=lambda: f'={V("r_sbc")}',
      qe=lambda: f'={PT("pt_sbc")}', ae_in=yr(V0['sbc']), note=V0['sbc_note'])
    S('d_ndt_r', '  Nuclear decommissioning trust — assumed annual return on the opening balance %', 'pct', 'pct',
      hist=lambda: (f'=IFERROR({V("is_ndt")}/{P("bs_ndt")},"")' if (CTX.col.prior and not CTX.col.q) else None), ae_in=V0['ndt_r'],
      note='Non-cash (retained in the trust) and excluded from Adjusted EBITDA; assumption. Q4/26E: nil (no market call).')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF OPERATIONS (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (operating income = Adjusted EBITDA − D&A − nuclear fuel amortization − excluded operating items; O&M is the implied balancing line)')
    S('is_en', 'Energy and other revenues', 'line', 'm1', data='en_rev', flow=True, fc=lambda: f'={V("em")}+{V("gen")}*{V("fuel_mwh")}',
      note='Forecast = adjusted energy margin + fuel & energy purchases before contract amortization (generation × $/MWh).')
    S('is_cap', 'Capacity revenues', 'line', 'm1', data='cap_rev', flow=True, fc=lambda: f'={V("cap")}')
    S('is_unr_rev', 'Unrealized gain (loss) on derivative instruments — revenues', 'line', 'm1', data='unr_rev', flow=True, fc=lambda: '=0',
      note='Mark-to-market of economic hedges; excluded from Adjusted EBITDA; forecast nil.')
    S('is_rev', 'Operating revenues', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_en")}),{V("is_en")}+{V("is_cap")}+{V("is_unr_rev")},"")')
    S('is_fuel', 'Fuel and energy purchases', 'line', 'm1', data='fuel', flow=True, fc=lambda: f'={V("gen")}*{V("fuel_mwh")}-{V("d_acl")}')
    S('is_nfa', 'Nuclear fuel amortization', 'line', 'm1', data='nfa', flow=True, qe=lambda: f'={PT("pt_nfa")}', ae_in=yr(V0['nfa']),
      note='Q4/26E = FY26 guidance ($100m) − nine months; 2027E $110m (guidance); then held.')
    S('is_unr_exp', 'Unrealized (gain) loss on derivative instruments — energy expenses (loss +)', 'line', 'm1', flow=True, data='unr_exp_cost', fc=lambda: '=0')
    S('is_enexp', 'Energy expenses', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_fuel")}),{V("is_fuel")}+{V("is_nfa")}+{V("is_unr_exp")},"")')
    S('is_om', 'Operation, maintenance and development', 'line', 'm1', data='om', flow=True,
      fc=lambda: f'={V("is_rev")}-{V("is_enexp")}-{V("is_ga")}-{V("is_dda")}-{V("is_imp")}+{V("is_othop")}-{V("is_ebit")}',
      note='Forecast = implied balancing line (revenues − energy expenses − G&A − D&A + other operating items − operating income from the Adjusted EBITDA build).')
    S('is_ga', 'General and administrative (incl. stock-based compensation)', 'line', 'm1', data='ga', flow=True, fc=lambda: f'={V("d_gax")}+{V("d_sbc")}')
    S('is_dda', 'Depreciation, amortization and accretion', 'line', 'm1', data='dda', flow=True, qe=lambda: f'={PT("pt_dda")}',
      ae=lambda: (f'={PT("pt_dda27")}' if Y27() else f'={P("bs_ppe")}*{V("d_dda_p")}'),
      note='Q4/26E = FY26 guidance ($515m) − nine months; 2027E $650m (guidance); 2028E+: rate on opening PP&E.')
    S('is_imp', 'Impairments and operational restructuring', 'line', 'm1', data='impair_restr', flow=True, fc=lambda: '=0')
    S('is_othop', 'Other operating income (expense), net (income +)', 'line', 'm1', data='oth_op', flow=True, fc=lambda: f'=-({V("r_restr")}+{V("r_acq")}+{V("r_imp")}+{V("r_oth")})',
      note='Forecast = − excluded operating items (nil by default).')
    S('is_ebit', 'Operating income (loss)', 'total', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}-{V("is_enexp")}-{V("is_om")}-{V("is_ga")}-{V("is_dda")}-{V("is_imp")}+{V("is_othop")},"")',
      fc=lambda: f'={V("g_adj")}-{V("r_dda")}-{V("is_nfa")}-{V("r_sbc")}-{V("r_restr")}-{V("r_acq")}-{V("r_imp")}-{V("r_oth")}',
      note='Forecast = Adjusted EBITDA − D&A (reconciliation basis) − nuclear fuel amortization − stock compensation − other excluded operating items.')
    S('is_ebit_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_ebit', 'is_rev'))
    S('is_ndt', 'Nuclear decommissioning trust funds gain (loss), net', 'line', 'm1', data='ndt', flow=True, qe=lambda: '=0', ae=lambda: f'={P("bs_ndt")}*{V("d_ndt_r")}')
    S('is_int', 'Interest expense and other finance charges', 'line', 'm1', data='int', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_rev")}*{V("ds_r_rev")}+{V("ds_fees")}+{V("dco_acc")}',
      note='Q4/26E point estimate. 2027E+ = rate × opening long-term debt + rate × opening revolver + fees + accretion of the capacity-monetization discount (no circularity).')
    S('is_reorg', 'Reorganization income (expense), net and consolidation of subsidiary gain (loss)', 'line', 'm1', data='reorg_consol', flow=True, fc=lambda: '=0')
    S('is_gain', 'Gain (loss) on sale of assets, net', 'line', 'm1', data='gain_sale', flow=True, fc=lambda: '=0')
    S('is_othnon', 'Other non-operating income (expense), net', 'line', 'm1', data='oth_nonop', flow=True, fc=lambda: '=0')
    S('is_ebt', 'Income (loss) before income taxes', 'line_b', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("is_ebit")}),{V("is_ebit")}+{V("is_ndt")}-{V("is_int")}+{V("is_reorg")}+{V("is_gain")}+{V("is_othnon")},"")')
    S('is_tax', 'Income tax expense (benefit)', 'line', 'm1', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      e26=ratio('is_tax', 'is_ebt'), note='Q4/26E: nine-month 2026 rate (25.9%). 2027E+: input (21% federal + state income taxes + NDT taxes).')
    S('is_nitot', 'Net income (loss)', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_nci', '  Less: net income (loss) attributable to noncontrolling interest', 'line', 'm1', data='nci', flow=True, fc=lambda: '=0')
    S('is_ni', 'Net income (loss) attributable to stockholders (member before 17-May-2023)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_nitot")}),{V("is_nitot")}-{V("is_nci")},"")')
    S('is_ni_chk', '  Check: net income attributable vs reported (should be 0; ±0.5 rounding)', 'check', 'm1', hist=lambda: tol(V('is_ni'), V('is_ni_pub')))
    S('is_ni_pub', '  Memo: net income (loss) attributable as reported', 'memo', 'm1', data='ni', flow=True)
    S('is_oi_chk', '  Check: operating income vs reported (should be 0; ±0.5 rounding)', 'check', 'm1', hist=lambda: tol(V('is_ebit'), V('is_oi_pub')))
    S('is_oi_pub', '  Memo: operating income (loss) as reported', 'memo', 'm1', data='oi', flow=True)
    S('is_dda_m', '  Memo: depreciation, amortization & accretion + nuclear fuel amortization', 'memo_calc', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_dda")}),{V("is_dda")}+{V("is_nfa")},"")')
    S('eps_hdr', '(Earnings per share — Talen Energy Corporation common stock; Successor periods from 18-May-2023)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={B1("bs_shares")}-{PT("pt_asr_sh")}-0.5*IFERROR({PT("pt_bb")}/${E26}${R["v_px"]},0)',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q4/26E: shares outstanding at 30-Sep-2026 − ASR shares retired on 1-Oct-2026 − half of any further Q4 repurchases. 2027E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")',
      note='Net income attributable / weighted diluted shares (±$0.02 vs reported).')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.02 rounding)', 'check', 'ps',
      hist=lambda: (f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0201,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")' if CTX.col.q else None))
    blank()

    # ------------------------------------------------------------------ RECON 1: net income -> EBITDA -> Adjusted EBITDA
    S('sec_r1', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (company definition, as published)', 'section',
      note='ADJUSTED EBITDA — per the release / prospectus reconciliations; the company\'s line items are grouped into the rows below and its wording for each period is in the cell comments')
    S('r_ni', 'Net income (loss) (GAAP, incl. noncontrolling interest)', 'line_b', 'm1', all=lambda: f'={V("is_nitot")}')
    S('r_int', '  (+) Interest expense and other finance charges (reconciliation line)', 'line', 'm1', data='ng_int', flow=True, fc=lambda: f'={V("is_int")}',
      note='As shown in the company reconciliation (FY2021–23 prospectus figures include finance charges shown elsewhere in the statement of operations).')
    S('r_tax', '  (+) Income tax expense (benefit)', 'line', 'm1', all=lambda: f'={V("is_tax")}')
    S('r_dda', '  (+) Depreciation, amortization and accretion (reconciliation line; net of acquired-contract amortization)', 'line', 'm1', data='ng_dda', flow=True,
      fc=lambda: f'={V("is_dda")}-{V("d_acl")}')
    S('r_nfa', '  (+) Nuclear fuel amortization', 'line', 'm1', all=lambda: f'={V("is_nfa")}')
    S('r_ebitda', '  = EBITDA incl. nuclear fuel amortization (model subtotal; not published)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_ni")}),ISNUMBER({V("r_dda")})),{V("r_ni")}+{V("r_int")}+{V("r_tax")}+{V("r_dda")}+{V("r_nfa")},"")')
    fcit = {'mtm': lambda: f'=-({V("is_unr_rev")}-{V("is_unr_exp")})', 'ndt': lambda: f'=-{V("is_ndt")}', 'sbc': lambda: f'={V("d_sbc")}', 'gain': lambda: f'=-{V("is_gain")}'}
    for k, cat, lab in ITEMS:
        S(f'r_{k}', f'  (+) {lab}', 'line', 'm1', data=f'ng_{cat}', flow=True, labkey=f'ng_{cat}_lab', fc=fcit.get(k, lambda: '=0'))
    S('r_items', '  Total adjusting items', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_mtm")}),{nsum(["r_" + k for k, _, _ in ITEMS])},"")')
    S('r_adj', '  = Adjusted EBITDA (model bridge)', 'total', 'm1', all=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda")}),ISNUMBER({V("r_items")})),{V("r_ebitda")}+{V("r_items")},"")',
      note='Company definition. Used for leverage (net debt / Adjusted EBITDA) and EV / EBITDA. Forecast = the operating build (check in the Group block).')
    S('r_adj_m', '  Adjusted EBITDA % of energy and capacity revenues', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("r_adj")}),IFERROR({V("r_adj")}/({V("is_en")}+{V("is_cap")}),""),"")')
    S('r_adj_pub', '  Company-published Adjusted EBITDA', 'memo', 'm1', data='adj_ebitda_pub', flow=True)
    S('r_chk', '  Check: model vs company-published Adjusted EBITDA (should be 0; ±1.5 on combined 2023 periods)', 'check', 'm1',
      hist=lambda: tol(V('r_adj'), V('r_adj_pub'), 1.6 if CTX.col.year == 2023 else 0.6, '"n/p"'))
    S('r_def', '  Definition / basis (company Adjusted EBITDA definition in force)', 'text', 'gen',
      note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('r_adj_g', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('r_ebit_h', 'To adjusted EBIT (model definition; for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ddan', '  (−) Depreciation, amortization & accretion (reconciliation basis) and nuclear fuel amortization', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_dda")}),-({V("r_dda")}+{V("r_nfa")}),"")')
    S('r_ebit', '  = Adjusted EBIT (model: Adjusted EBITDA − D&A − nuclear fuel amortization)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+{V("r_ddan")},"")',
      note='Model measure (Talen publishes no adjusted EBIT). Nuclear fuel is a recurring cost (its purchases are in maintenance capex), so its amortization is charged.')
    S('r_ebit_m', '  Adjusted EBIT % of energy and capacity revenues', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("r_ebit")}),IFERROR({V("r_ebit")}/({V("is_en")}+{V("is_cap")}),""),"")')
    S('r_cash', '  Memo: stock compensation, restructuring and acquisition costs excluded by the company (deducted in the DCF)', 'memo_calc', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_sbc")}),{V("r_sbc")}+{V("r_restr")}+{V("r_acq")},"")')
    S('r_ddap', '  Memo: D&A (reconciliation basis) + nuclear fuel amortization (added back in the DCF)', 'memo_calc', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ddan")}),-{V("r_ddan")},"")')
    blank()

    # ------------------------------------------------------------------ RECON 2: Adjusted EBITDA -> Adjusted Free Cash Flow
    S('sec_r2', 'RECONCILIATION: ADJUSTED EBITDA → ADJUSTED FREE CASH FLOW (company definition, published from Q2/24; FY2023 from the Q4/24 release)', 'section',
      note='ADJUSTED FCF — Adjusted EBITDA − capital expenditures, net (incl. nuclear fuel; excl. development, growth and conversion capex) − cash interest − cash income taxes − pension contributions')
    S('f_eb', 'Adjusted EBITDA', 'line_b', 'm1', all=lambda: f'={V("r_adj")}')
    S('f_capex', '  (−) Capital expenditures, net (company definition)', 'line', 'm1', data='f_capex', flow=True, qe=lambda: f'=-{PT("pt_fcapex")}-{ACT("f_capex")}', ae_in=yr(V0['fcapex']),
      note='Q4/26E = FY26 guidance mid-point ($330m) − nine months. 2027E $370m (guidance mid-point); then input.')
    S('f_int', '  (−) Interest and finance charge payments', 'line', 'm1', data='f_int', flow=True, qe=lambda: f'=-{PT("pt_fint")}',
      ae=lambda: f'=-({V("is_int")}-{V("dco_acc")})+({V("bs_accint")}-{P("bs_accint")})', note='Forecast = cash interest: interest expense less the non-cash accretion of the capacity-monetization discount, adjusted for the change in accrued interest.')
    S('f_tax', '  (−) Income taxes paid (company definition)', 'line', 'm1', data='f_tax', flow=True, qe=lambda: f'=-{PT("pt_ftax")}-{ACT("f_tax")}', ae_in=yr(V0['ftax']), note=V0['ftax_note'])
    S('f_pen', '  (−) Pension contributions', 'line', 'm1', data='f_pension', flow=True, qe=lambda: f'=-{PT("pt_fpen")}-{ACT("f_pen")}', ae_in=yr(V0['fpen']),
      note='Q4/26E = FY26 guidance mid-point ($30m) − nine months; 2027E $20m (guidance mid-point); then input.')
    S('f_fcf', '  = Adjusted Free Cash Flow (model bridge)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("f_eb")}),ISNUMBER({V("f_capex")})),{V("f_eb")}+{V("f_capex")}+{V("f_int")}+{V("f_tax")}+{V("f_pen")},"")')
    S('f_pub', '  Company-published Adjusted Free Cash Flow', 'memo', 'm1', data='adj_fcf_pub', flow=True)
    S('f_chk', '  Check: model vs company-published Adjusted Free Cash Flow (should be 0; ±1.5 rounding)', 'check', 'm1', hist=lambda: tol(V('f_fcf'), V('f_pub'), 1.6, '"n/p"'))
    S('f_conv', '  Adjusted Free Cash Flow / Adjusted EBITDA %', 'pct', 'pct', all=ratio('f_fcf', 'f_eb'))
    S('f_ps', '  Adjusted Free Cash Flow per diluted share ($)', 'line', 'ps', all=ratio('f_fcf', 'sh_dil'))
    S('f_ps_g', '  Adjusted Free Cash Flow per share y/y %', 'growth', 'pct', all=growth('f_ps'))
    S('f_def', '  Definition / basis (company Adjusted Free Cash Flow definition)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ RECON 3: model adjusted EPS
    S('sec_r3', 'RECONCILIATION: NET INCOME → ADJUSTED NET INCOME → ADJUSTED EPS (MODEL DEFINITION — Talen publishes no adjusted net income or EPS)', 'section',
      note='ADJUSTED EPS (model definition) — net income attributable + the Adjusted EBITDA adjusting items, tax-effected at an assumed rate; labelled model measure, no company figure to check')
    S('e_ni', 'Net income (loss) attributable (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('e_op', '  (+) Adjusting items of the Adjusted EBITDA reconciliation (pre-tax)', 'line', 'm1', all=lambda: f'={V("r_items")}')
    S('e_rate', '  Assumed tax rate on adjusting items (model assumption)', 'pct', 'pct', hist=lambda: f'=IF(ISNUMBER({V("e_op")}),{V0["adj_rate"]},"")', fc=lambda: f'={V0["adj_rate"]}',
      note='25% (21% federal + state). Applied uniformly; the 2022–23 reorganization items of the Predecessor (a pass-through LLC before Emergence) were largely non-taxable, so 2021–23 adjusted EPS is indicative only.')
    S('e_tax', '  (−) Tax effect of the adjusting items', 'line', 'm1', flow=True, all=lambda: f'=IF(ISNUMBER({V("e_op")}),-{V("e_op")}*{V("e_rate")},"")')
    S('e_adjni', '  = Adjusted net income (model definition)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("e_tax")}),{V("e_ni")}+{V("e_op")}+{V("e_tax")},"")')
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted EPS – diluted ($) (model definition)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_def', '  Definition / basis', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Operating revenues y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_aero', '  Generation y/y %', 'growth', 'pct', all=growth('gen'))
    S('gm_cap', '  Capacity revenues y/y %', 'growth', 'pct', all=growth('cap'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_fcf', '  Adjusted Free Cash Flow y/y %', 'growth', 'pct', all=growth('f_fcf'))
    S('gm_op', '  Operating income (GAAP) y/y %', 'growth', 'pct', all=growth('is_ebit'))
    S('gm_ni', '  Net income attributable y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS (model) y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_ebitda_m', '  Adjusted EBITDA % of energy and capacity revenues', 'pct', 'pct', all=lambda: f'={V("r_adj_m")}')
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_ebit', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_capshare', '  Capacity revenues % of energy and capacity revenues', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("is_cap")}),IFERROR({V("is_cap")}/({V("is_en")}+{V("is_cap")}),""),"")')
    blank()
