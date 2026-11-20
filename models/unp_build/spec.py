"""Row specification of the UNP Model sheet, part 1 (MLM template layout and process):
freight revenue build (revenue carloads x average revenue per car by business group: Bulk / Industrial / Premium; legacy groups as
memo) + other revenues -> operating statistics & cost build (gross ton-miles, fuel gallons x price, employees x compensation per
employee, cost ratios) -> operating ratio -> Norfolk Southern acquisition block (toggle) -> group total & FY26 EPS-guidance
calibration -> income statement -> GAAP-to-adjusted bridges -> growth & margins."""
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
def B1(key): return f'{LQ}{R[key]}'                       # 30-Sep-2026 balance
def ANNQ(): return 4 if CTX.col.q else 1                  # annualisation factor for quarterly columns
def CB(key): return f'${ANN[2027].c}${R[key]}'            # deal inputs held in the 2027E column

GROUPS = [('bulk', 'Bulk', 'BULK', 'grain & grain products, fertilizer, food & refrigerated, coal & renewables'),
          ('industrial', 'Industrial', 'IND', 'industrial chemicals & plastics, metals & minerals, forest products, energy & specialized markets'),
          ('premium', 'Premium', 'PREM', 'finished automobiles & parts, intermodal (domestic & international containers / trailers; each unit = one carload)')]
SUBS = [('grain', 'Grain & grain products', 'bulk'), ('fert', 'Fertilizer', 'bulk'), ('food', 'Food & refrigerated', 'bulk'), ('coalren', 'Coal & renewables', 'bulk'),
        ('chemplas', 'Industrial chemicals & plastics', 'industrial'), ('metals', 'Metals & minerals', 'industrial'), ('forest', 'Forest products', 'industrial'),
        ('energyspec', 'Energy & specialized markets', 'industrial'), ('auto', 'Automotive', 'premium'), ('intermodal', 'Intermodal', 'premium')]
LEG6 = [('ag', 'Agricultural (Products)'), ('auto', 'Automotive'), ('chem', 'Chemicals'), ('energy', 'Energy / Coal'), ('indprod', 'Industrial Products'), ('intermodal', 'Intermodal')]
LEG4 = [('ag', 'Agricultural Products'), ('energy', 'Energy'), ('industrial', 'Industrial'), ('premium', 'Premium')]
VARC = ['comp', 'psm', 'rents', 'oth']        # cost lines carrying the calibration shift
ADJ = ['d_acq', 'd_impair', 'd_gain', 'd_oadj']

# ====================================================================== scenario table (CN:CR)
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of the FY26 guidance (reported EPS growth "high-single digit").'))
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
    # ------------------------------------------------------------------ FREIGHT REVENUE BUILD
    S('sec_frt', 'FREIGHT REVENUE BUILD — REVENUE CARLOADS × AVERAGE REVENUE PER CAR BY BUSINESS GROUP (BULK · INDUSTRIAL · PREMIUM) + OTHER REVENUES', 'section',
      note='FREIGHT BUILD — modelling logic (carloads × ARPC per business group → freight revenues; + other revenues = operating revenues → cost build → operating ratio → EPS)')
    blank()
    for g, title, code, descr in GROUPS:
        S(f'{g}_hdr', f'{title} ({descr})', 'block', note=f'{title.upper()} — carloads × average revenue per car (ARPC, incl. fuel surcharge)')
        S(f'{g}_cars', '  Revenue carloads (thousands)', 'line', 'm', data=f'g_{g}_cars', flow=True,
          qe=lambda g=g: f'={P(g + "_cars")}*(1+{V(g + "_cars_g")})', ae=lambda g=g: f'={P(g + "_cars")}*(1+{V(g + "_cars_g")})',
          note=('Business groups on the current basis (Bulk / Industrial / Premium) from the 2020 releases; 2019 from the 2020 releases\' prior-year comparatives (recast). '
                'Q4/26E: prior-year quarter × (1 + 9M-26 y/y). 2027E+: prior year × (1 + scenario lever).') if g == 'bulk' else None)
        S(f'{g}_cars_g', '    Carloads y/y %', 'growth', 'pct', all=growth(f'{g}_cars'), qe=lambda g=g: f'=IFERROR({ACT(g + "_cars")}/{ACT0(g + "_cars")}-1,0)',
          ae=lambda g=g, code=code: '=' + CH(SC[f'{code}_VOL'][CTX.col.year]))
        S(f'{g}_arpc', '  Average revenue per car ($; incl. fuel surcharge)', 'line', 'm', data=f'g_{g}_arpc', avg=True,
          qe=lambda g=g: f'={P(g + "_arpc")}*(1+{V(g + "_arpc_g")})', ae=lambda g=g: f'={P(g + "_arpc")}*(1+{V(g + "_arpc_g")})',
          note='ARPC = freight revenue ÷ carloads (price, mix and fuel surcharge). Q4/26E: prior-year quarter × (1 + 9M-26 y/y). 2027E+: scenario lever (core price + mix + fuel surcharge).' if g == 'bulk' else None)
        S(f'{g}_arpc_g', '    ARPC y/y %', 'growth', 'pct', all=growth(f'{g}_arpc'), qe=lambda g=g: f'=IFERROR({ACT(g + "_rev")}/{ACT(g + "_cars")}/({ACT0(g + "_rev")}/{ACT0(g + "_cars")})-1,0)',
          ae=lambda g=g, code=code: '=' + CH(SC[f'{code}_PX'][CTX.col.year]))
        S(f'{g}_rev', f'  {title} freight revenues (USDm)', 'line_b', 'm', data=f'g_{g}_rev', flow=True,
          fc=lambda g=g: f'={V(g + "_cars")}*{V(g + "_arpc")}/1000', note='Forecast = carloads × ARPC ÷ 1,000.' if g == 'bulk' else None)
        S(f'{g}_rev_g', '    Freight revenues y/y %', 'growth', 'pct', all=growth(f'{g}_rev'))
        S(f'{g}_mix', '    % of freight revenues', 'pct', 'pct', all=ratio(f'{g}_rev', 'f_rev'))
        S(f'{g}_chk', '    Check: carloads × ARPC vs reported group revenues (should be 0; within carload / ARPC rounding ±0.3%)', 'check', 'm1',
          hist=lambda g=g: f'=IF(AND(ISNUMBER({V(g + "_cars")}),ISNUMBER({V(g + "_rev")})),IF(ABS({V(g + "_cars")}*{V(g + "_arpc")}/1000-{V(g + "_rev")})<=0.003*{V(g + "_rev")},0,ROUND({V(g + "_cars")}*{V(g + "_arpc")}/1000-{V(g + "_rev")},1)),"")')
        blank()
    S('f_hdr', 'Total freight revenues (Σ business groups) and other revenues', 'block', note='TOTAL FREIGHT — Σ groups; history before 2019 = reported totals (legacy group structures in the memo blocks below)')
    S('f_cars', '  Total revenue carloads (thousands)', 'line', 'm', data='g_total_cars', flow=True, fc=lambda: '=' + '+'.join(V(g + '_cars') for g, *_ in GROUPS))
    S('f_cars_g', '    Carloads y/y %', 'growth', 'pct', all=growth('f_cars'))
    S('f_arpc', '  Average revenue per car — total ($)', 'line', 'm', data='g_total_arpc', avg=True, fc=lambda: f'=IFERROR({V("f_rev")}/{V("f_cars")}*1000,"")')
    S('f_arpc_g', '    ARPC y/y %', 'growth', 'pct', all=growth('f_arpc'))
    S('f_rev', 'Freight revenues (build)', 'total', 'm', data='frt', flow=True, fc=lambda: '=' + '+'.join(V(g + '_rev') for g, *_ in GROUPS),
      note='History: freight revenues as reported (2006–07 re-presented in the FY2008 10-K; the releases then showed "commodity revenue"). Forecast: Σ groups.')
    S('f_rev_g', '  Freight revenues y/y %', 'growth', 'pct', all=growth('f_rev'))
    S('f_chk', '  Check: Σ business groups vs reported freight revenues (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bulk_rev")}),IF(ABS({"+".join(V(g + "_rev") for g, *_ in GROUPS)}-{V("is_frt")})<=0.6,0,ROUND({"+".join(V(g + "_rev") for g, *_ in GROUPS)}-{V("is_frt")},1)),"")')
    S('f_fs', '  Memo: fuel surcharge revenues (10-K / 10-Q MD&A, where stated in dollars)', 'memo', 'm', data='fs_rev', flow=True,
      note='Annual from the 10-K ("fuel surcharge programs generated freight revenues of $x"); quarters from the 10-Q MD&A where a dollar figure is given. Included in ARPC above.')
    S('f_fs_p', '  Memo: fuel surcharge % of freight revenues', 'memo_calc', 'pct', all=ratio('f_fs', 'f_rev'))
    S('f_xfs', '  Memo: freight revenues excluding fuel surcharge', 'memo_calc', 'm', all=lambda: f'=IF(ISNUMBER({V("f_fs")}),{V("f_rev")}-{V("f_fs")},"")')
    S('o_rev', 'Other revenues (subsidiaries, accessorial, commuter operations)', 'line', 'm', data='oth_rev', flow=True,
      qe=lambda: f'={P("o_rev")}*(1+{V("o_rev_g")})', ae=lambda: f'={P("o_rev")}*(1+{V("o_rev_g")})',
      note='Q4/26E: prior-year quarter × (1 + 9M-26 y/y). 2027E+: scenario lever (OTH_g).')
    S('o_rev_g', '  Other revenues y/y %', 'growth', 'pct', all=growth('o_rev'), qe=lambda: f'=IFERROR({ACT("o_rev")}/{ACT0("o_rev")}-1,0)', ae=lambda: '=' + CH(SC['OTH'][CTX.col.year]))
    S('t_rev', 'Total operating revenues (build)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("f_rev")}),{V("f_rev")}+{V("o_rev")},"")')
    S('t_rev_g', '  Operating revenues y/y %', 'growth', 'pct', all=growth('t_rev'))
    S('t_chk', '  Check: build (+ Norfolk Southern) vs consolidated operating revenues (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("t_rev")}),IF(ABS({V("t_rev")}+N({V("nc_rev")})-{V("is_rev")})<=0.6,0,ROUND({V("t_rev")}+N({V("nc_rev")})-{V("is_rev")},1)),"")')
    blank()
    S('sub_hdr', 'Commodity detail inside the business groups (freight revenues, USDm; published from the Q1-2020 release, 2019 recast) — memo', 'block',
      note='COMMODITY MEMO — ten commodity lines (history only); Σ checks per group')
    for k, lab, g in SUBS:
        S(f'c_{k}', f'  {lab}', 'memo', 'm', data=f'g_{k}_rev', flow=True)
    for g, title, *_ in GROUPS:
        subs = [f'c_{k}' for k, _, gg in SUBS if gg == g]
        S(f'c_chk_{g}', f'  Check: Σ commodities vs {title} (should be 0)', 'check', 'm1',
          hist=lambda subs=subs, g=g: f'=IF(ISNUMBER({V(subs[0])}),IF(ABS({"+".join(V(s) for s in subs)}-{V(g + "_rev")})<=0.6,0,ROUND({"+".join(V(s) for s in subs)}-{V(g + "_rev")},1)),"")')
    blank()
    S('leg_hdr', 'Legacy business groups as originally reported (freight revenues, USDm) — memo', 'block',
      note='LEGACY GROUPS — six groups 2006–2017; four groups (Agricultural Products / Energy / Industrial / Premium) 2018–2019; not comparable with the current basis')
    for k, lab in LEG6:
        S(f'l6_{k}', f'  {lab} (2006–17)', 'memo', 'm', data=f's6_{k}_rev', flow=True)
    S('l6_tot', '  Memo: total commodity / freight revenues as reported in the release', 'memo', 'm', data='g_total_rev', flow=True,
      note='2006–07: "commodity revenue" ($000 in the releases, ÷1,000); the FY2008 10-K reclassified $71m (2006) and $30m (2007) from freight to other revenues.')
    S('l6_chk', '  Check: Σ six groups vs reported total (should be 0; ±1 rounding of $000 figures)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("l6_ag")}),IF(ABS({"+".join(V("l6_" + k) for k, _ in LEG6)}-{V("l6_tot")})<=1.1,0,ROUND({"+".join(V("l6_" + k) for k, _ in LEG6)}-{V("l6_tot")},1)),"")')
    for k, lab in LEG4:
        S(f'l4_{k}', f'  {lab} (2018–19)', 'memo', 'm', data=f's4_{k}_rev', flow=True)
    S('l4_chk', '  Check: Σ four groups vs reported freight revenues (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("l4_ag")}),IF(ABS({"+".join(V("l4_" + k) for k, _ in LEG4)}-{V("is_frt")})<=0.6,0,ROUND({"+".join(V("l4_" + k) for k, _ in LEG4)}-{V("is_frt")},1)),"")')
    S('l_def', '  Business-group structure in force (definition flag)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ OPERATING STATISTICS & COST BUILD
    S('sec_ops', 'OPERATING STATISTICS & COST BUILD — GROSS TON-MILES · FUEL (GALLONS × PRICE) · EMPLOYEES × COMPENSATION · COST RATIOS → OPERATING RATIO', 'section',
      note='COST BUILD — modelling logic (GTMs from carloads; fuel = gallons × price; compensation = employees × cost per employee; PS&M, rents and other as % of revenues; depreciation growth)')
    S('v_hdr', 'Volume & productivity statistics (release operating statistics)', 'block', note='VOLUME — gross ton-miles (GTMs) drive fuel gallons and headcount')
    S('v_gtm', '  Gross ton-miles (GTMs, millions)', 'line', 'm', data='gtm', flow=True, fc=lambda: f'={V("f_cars")}*{V("v_gtm_pc")}/1000',
      note='History as reported (2006–07 billions × 1,000; FY2017 as published differs from Σ quarters by 2,398, a company restatement). Forecast = carloads × GTMs per carload.')
    S('v_gtm_g', '    GTMs y/y %', 'growth', 'pct', all=growth('v_gtm'))
    S('v_gtm_pc', '  GTMs per revenue carload (thousands)', 'line', 'm3', all=lambda: f'=IF(AND(ISNUMBER({V("v_gtm")}),ISNUMBER({V("f_cars")})),IFERROR({V("v_gtm")}/{V("f_cars")}*1000,""),"")',
      qe=lambda: f'={P("v_gtm_pc")}*(1+IFERROR({ACT("v_gtm")}/{ACT("f_cars")}/({ACT0("v_gtm")}/{ACT0("f_cars")})-1,0))', ae=lambda: f'={P("v_gtm_pc")}*(1+{V("v_gtm_pc_g")})',
      note='Mix proxy (heavier bulk / lighter intermodal). Q4/26E: prior-year quarter × (1 + 9M-26 y/y). 2027E+: prior year × (1 + input).')
    S('v_gtm_pc_g', '    GTMs per carload y/y % (input 2027E+)', 'driver', 'pct', all=growth('v_gtm_pc'), ae_in=V0['gtm_pc_g'])
    S('v_rtm', '  Memo: revenue ton-miles (millions)', 'memo', 'm', data='rtm', flow=True)
    S('v_emp', '  Employees (average)', 'line', 'm', data='emp', avg=True, fc=lambda: f'=IFERROR({V("v_gtm")}*{ANNQ()}/{V("v_gtm_emp")},"")',
      e26=lambda: f'=AVERAGE({Q1}{R["v_emp"]}:{QE}{R["v_emp"]})',
      note='Forecast = GTMs ÷ GTMs per employee (workforce productivity lever).')
    S('v_emp_g', '    Employees y/y %', 'growth', 'pct', all=growth('v_emp'))
    S('v_gtm_emp', '  GTMs per employee (millions, annualised)', 'line', 'm2', all=lambda: f'=IF(AND(ISNUMBER({V("v_gtm")}),ISNUMBER({V("v_emp")})),IFERROR({V("v_gtm")}*{ANNQ()}/{V("v_emp")},""),"")',
      qe=lambda: f'={P("v_gtm_emp")}*(1+IFERROR({ACT("v_gtm")}/AVERAGE({Q1}{R["v_emp"]}:{Q3}{R["v_emp"]})/({ACT0("v_gtm")}/AVERAGE({PQ1}{R["v_emp"]}:{PQ3}{R["v_emp"]}))-1,0))',
      ae=lambda: f'={P("v_gtm_emp")}*(1+{V("v_prod_g")})', note='Q4/26E: prior-year quarter × (1 + 9M-26 y/y productivity change). 2027E+: prior year × (1 + PROD lever).')
    S('v_prod_g', '    Workforce productivity y/y % (GTMs per employee; scenario lever 2027E+)', 'growth', 'pct', all=growth('v_gtm_emp'), ae=lambda: '=' + CH(SC['PROD'][CTX.col.year]))
    S('v_wf', '  Memo: workforce productivity as published (car miles per employee)', 'memo', 'm', data='wf_prod', avg=True)
    S('v_speed', '  Memo: average train speed (mph)', 'memo', 'm1', data='speed', avg=True)
    S('v_dwell', '  Memo: average terminal dwell (hours)', 'memo', 'm1', data='dwell', avg=True)
    S('v_vel', '  Memo: freight car velocity (daily miles per car)', 'memo', 'm', data='velocity', avg=True)
    S('v_len', '  Memo: train length (feet)', 'memo', 'm', data='train_len', avg=True)
    blank()
    S('fu_hdr', 'Locomotive fuel — gallons consumed × average price per gallon', 'block', note='FUEL — gallons = GTMs × consumption rate; price per gallon is a point input (no EDGAR forward curve)')
    S('fu_rate', '  Fuel consumption rate (gallons per thousand GTMs)', 'line', 'm3', data='fuel_rate', avg=True,
      qe=lambda: f'={P("fu_rate")}*(1+IFERROR({ACT("fu_gal")}/{ACT("v_gtm")}/({ACT0("fu_gal")}/{ACT0("v_gtm")})-1,0))', ae=lambda: f'={P("fu_rate")}*(1+{V("fu_rate_g")})',
      note='Q4/26E: prior-year quarter × (1 + 9M-26 y/y). 2027E+: prior year × (1 + efficiency input; 2019–25 averaged ~−1% a year).')
    S('fu_rate_g', '    Consumption rate y/y % (input 2027E+)', 'driver', 'pct', all=growth('fu_rate'), ae_in=V0['fuel_rate_g'])
    S('fu_gal', '  Fuel consumed (millions of gallons)', 'line', 'm', data='gallons', flow=True, fc=lambda: f'={V("v_gtm")}*{V("fu_rate")}/1000')
    S('fu_px', '  Average fuel price per gallon consumed ($)', 'line', 'm2', data='fuel_px', avg=True, qe=lambda: f'={PT("pt_fuel")}', ae_in=V0['fuel_px'],
      note=V0['fuel_px_note'])
    S('fu_px_g', '    Fuel price y/y %', 'growth', 'pct', all=growth('fu_px'))
    S('fu_calc', '  Locomotive fuel cost = gallons × price (USDm)', 'line', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("fu_gal")}),ISNUMBER({V("fu_px")})),{V("fu_gal")}*{V("fu_px")},"")')
    S('fu_ratio', '  Reported fuel expense ÷ locomotive fuel cost (x; non-locomotive fuel, hedges, timing)', 'line', 'x2', hist=ratio('is_fuel', 'fu_calc'),
      qe=lambda: f'=IFERROR({ACT("is_fuel")}/{ACT("fu_calc")},1)', e26=lambda: f'=IFERROR(SUM({Q1}{R["is_fuel"]}:{QE}{R["is_fuel"]})/SUM({Q1}{R["fu_calc"]}:{QE}{R["fu_calc"]}),1)',
      ae=lambda: f'={V("fu_ratio", E26)}', note='Forecast holds the 9M-26 ratio.')
    S('fu_exp', '  Fuel expense (forecast = gallons × price × ratio)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("fu_calc")}),{V("fu_calc")}*{V("fu_ratio")},"")')
    blank()
    S('co_hdr', 'Compensation & benefits — employees × compensation per employee', 'block', note='COMPENSATION — average employees × cost per employee (wage inflation input)')
    S('co_pe', '  Compensation & benefits per average employee ($000, annualised)', 'line', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("is_comp")}),ISNUMBER({V("v_emp")})),IFERROR({V("is_comp")}*{ANNQ()}/{V("v_emp")}*1000,""),"")',
      qe=lambda: f'={P("co_pe")}*(1+IFERROR({ACT("is_comp")}/AVERAGE({Q1}{R["v_emp"]}:{Q3}{R["v_emp"]})/({ACT0("is_comp")}/AVERAGE({PQ1}{R["v_emp"]}:{PQ3}{R["v_emp"]}))-1,0))*(1+{QEa("cal_c")})',
      ae=lambda: f'={P("co_pe")}*(1+{V("co_pe_g")})',
      note='Q4/26E: prior-year quarter × (1 + 9M-26 y/y) × (1 + calibration shift). 2027E+: prior year × (1 + wage / benefit inflation input).')
    S('co_pe_g', '    Compensation per employee y/y % (input 2027E+)', 'driver', 'pct', all=growth('co_pe'), ae_in=V0['wage_g'],
      note='2026 labor agreements (national bargaining round) and crew staffing agreements; 2019–25 averaged ~4% a year.')
    S('co_exp', '  Compensation & benefits (forecast = employees × cost per employee)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("co_pe")}),{V("v_emp")}*{V("co_pe")}/1000/{ANNQ()},"")')
    blank()
    S('cr_hdr', 'Other cost ratios (% of operating revenues) and depreciation', 'block', note='COST RATIOS — PS&M, equipment & other rents, other (incl. casualty, state & local taxes); depreciation grows with the asset base')
    for k, lab, key in (('psm', 'Purchased services & materials % of revenues', 'is_psm'), ('rents', 'Equipment & other rents % of revenues', 'is_rents'),
                        ('oth', 'Other expenses % of revenues (excl. company-adjusted items)', 'is_oth_adj')):
        S(f'cr_{k}', f'  {lab}', 'pct', 'pct', all=ratio(key, 'is_rev'),
          qe=lambda key=key, k=k: f'=({P("cr_" + k)}+IFERROR({ACT(key)}/{ACT("is_rev")}-{ACT0(key)}/{ACT0("is_rev")},0))*(1+{QEa("cal_c")})',
          ae=lambda k=k: f'={V("cr_" + k + "_in")}+{CH(SC["COST"][CTX.col.year])}',
          note=('Q4/26E: prior-year quarter ratio + 9M-26 y/y drift, × (1 + calibration shift). 2027E+: input + COST lever (uniform shift, pp).') if k == 'psm' else None)
        S(f'cr_{k}_in', f'    {lab.split(" %")[0]} — 2027E+ input (before the COST lever)', 'driver', 'pct', ae_in=V0[f'{k}_pct'])
    S('cr_dep', '  Depreciation (USDm)', 'line', 'm', all=lambda: f'={V("is_dep")}' if False else (f'=IF(ISNUMBER({V("is_dep")}),{V("is_dep")},"")'),
      qe=lambda: f'={PT("pt_dep")}', ae=lambda: f'={P("cr_dep")}*(1+{V("cr_dep_g")})',
      note='Group depreciation on the asset base (composite rates ~2.8%); Q4/26E point estimate; 2027E+: prior year × (1 + growth input, consistent with the $3.5bn capital plan).')
    S('cr_dep_g', '    Depreciation y/y % (input 2027E+)', 'driver', 'pct', all=growth('cr_dep'), ae_in=V0['dep_g'])
    S('cr_dep_pct', '  Depreciation % of revenues', 'pct', 'pct', all=ratio('cr_dep', 'is_rev'))
    S('cr_sbc', '  Memo: share-based compensation (XBRL; inside compensation & benefits)', 'memo', 'm', data='sbc', flow=True, qe=lambda: f'={P("cr_sbc")}', ae=lambda: f'={P("cr_sbc")}*(1+{V("t_rev_g")})')
    blank()
    S('or_hdr', 'Operating ratio build (standalone Union Pacific)', 'block', note='OPERATING RATIO — total operating expenses ÷ operating revenues; adjusted = excluding company-adjusted items')
    S('or_opex_x', '  Total operating expenses excl. company-adjusted items (standalone build)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("co_exp")}),{V("co_exp")}+{V("fu_exp")}+({V("is_rev")}-N({V("nc_rev")}))*({V("cr_psm")}+{V("cr_rents")}+{V("cr_oth")})+{V("cr_dep")},"")',
      note='Forecast standalone operating expenses (on standalone revenues) before the Norfolk Southern block and before acquisition-related costs.')
    S('or_adj', '  Adjusted operating ratio (standalone, before acquisition-related costs)', 'total', 'pct',
      all=lambda: f'=IF(ISNUMBER({V("or_opex_x")}),IFERROR({V("or_opex_x")}/({V("is_rev")}-N({V("nc_rev")})),""),"")')
    S('or_rep', '  Operating ratio — reported (consolidated statement)', 'pct', 'pct', all=ratio('is_opex', 'is_rev'))
    S('or_pub', '  Memo: operating ratio as published (%)', 'memo', 'pct', data='or_pub', pctin=True)
    S('or_chk', '  Check: model vs published operating ratio (should be 0; ±0.05pt rounding)', 'check', 'pct2',
      hist=lambda: f'=IF(ISNUMBER({V("or_pub")}),IF(ABS({V("or_rep")}-{V("or_pub")})<=0.00051,0,ROUND({V("or_rep")}-{V("or_pub")},4)),"")')
    blank()

    # ------------------------------------------------------------------ NORFOLK SOUTHERN ACQUISITION BLOCK
    S('sec_nsc', 'PENDING ACQUISITION — NORFOLK SOUTHERN (NSC): TOGGLE · CONSIDERATION · FINANCING · PPA · SYNERGIES · CONTRIBUTION', 'section',
      note=('NSC BLOCK — modelling logic: merger agreement 28-Jul-2025 ($88.82 cash + 1.0 UNP share per NSC share); STB application filed 19-Dec-2025, accepted 16-Jan-2026; '
            'closing expected 2H 2027 (Q3-26 10-Q). Toggle 1 = consolidate from the closing date; 0 = standalone.'))
    S('n_tog', '  Deal toggle (1 = closes; 0 = standalone) — input', 'driver', 'gen', ae=lambda: (1 if CTX.col.year == 2027 else f'={CB("n_tog")}'), ae_in_year=2027,
      note='Input in the 2027E column (referenced by every year).')
    S('n_close', '  Assumed closing date — input', 'driver', 'date', ae_in_year=2027, ae=lambda: ('=DATE(2027,7,1)' if CTX.col.year == 2027 else f'={CB("n_close")}'),
      note='Q3-26 10-Q Note 18: "currently expected to be completed in the second half of 2027" → 1-Jul-2027 assumed (STB decision timetable; update when the STB rules).')
    S('n_frac', '  Fraction of the year consolidated', 'driver', 'pct', e26_in=0.0,
      ae=lambda: f'={CB("n_tog")}*MAX(0,MIN(1,(DATE({CTX.col.year},12,31)-{CB("n_close")}+1)/(DATE({CTX.col.year},12,31)-DATE({CTX.col.year},1,1)+1)))')
    S('n_yrs', '  Years since closing (end of year; for synergy phasing)', 'driver', 'm2', e26_in=0.0, ae=lambda: f'=MAX(0,(DATE({CTX.col.year},12,31)-{CB("n_close")}+1)/365.25)')
    S('ns_hdr', 'Norfolk Southern standalone (NSC Forms 10-K / 10-Q and 8-K releases; USDm)', 'sub', 'gen')
    S('ns_rev', '  Railway operating revenues', 'line', 'm', nsc='rev', e26=lambda: f'={V("ns_rev_9m")}+{V("ns_rev_q4py")}*(1+{V("ns_g")})', ae=lambda: f'={P("ns_rev")}*(1+{V("ns_g")})',
      note='2024–25 as reported; 2026E = 9M-26 actual + Q4-25 × (1 + growth); 2027E+: growth input.')
    S('ns_rev_9m', '    Memo: 9M-26 revenues (NSC Q3-26 release)', 'memo', 'm', e26_in=NSC_9M('railway_operating_revenues'))
    S('ns_rev_q4py', '    Memo: Q4-25 revenues', 'memo', 'm', e26_in=NSC_Q('Q4-25', 'railway_operating_revenues'))
    S('ns_g', '    NSC revenue growth % (input)', 'driver', 'pct', all=growth('ns_rev'), e26_in=V0['nsc_g'][2026], ae_in={y: V0['nsc_g'][y] for y in range(2027, 2031)},
      note='9M-26 +8.5% y/y (fuel surcharge, volume +1%); 2027E+ assumption (NSC gave no multi-year revenue guidance in its filings).')
    S('ns_or', '  NSC adjusted operating ratio (excl. merger costs, Eastern Ohio incident, restructuring) %', 'pct', 'pct', nsc='adj_or', e26_in=V0['nsc_or'][2026],
      ae_in={y: V0['nsc_or'][y] for y in range(2027, 2031)}, note='FY2025 65.0% (adjusted); 9M-26 ~66.5% on higher fuel. Input (assumption).')
    S('ns_dep', '  NSC depreciation', 'line', 'm', nsc='dep', e26=lambda: f'={V("ns_rev")}*{V("ns_dep_p")}', ae=lambda: f'={V("ns_rev")}*{V("ns_dep_p")}')
    S('ns_dep_p', '    NSC depreciation % of revenues (input)', 'pct', 'pct', all=ratio('ns_dep', 'ns_rev'), e26_in=0.113, ae_in=0.113)
    S('ns_oi', '  NSC adjusted operating income', 'line_b', 'm', nsc='adj_oi', fc=lambda: f'={V("ns_rev")}*(1-{V("ns_or")})')
    S('ns_int', '  NSC interest expense on debt', 'line', 'm', nsc='int', e26_in=NSC_INT26, ae=lambda: f'={V("ns_debt")}*{V("ns_r")}')
    S('ns_debt', '  NSC debt (year end; assumed at closing)', 'driver', 'm', nsc='debt', e26_in=NSC_BS('total_debt'), ae=lambda: f'={P("ns_debt")}',
      note='$16,613m at 30-Sep-2026 (current $649m + long-term $15,964m); held flat.')
    S('ns_r', '    NSC average interest rate on debt %', 'driver', 'pct', all=ratio('ns_int', 'ns_debt'), ae_in=0.047)
    S('ns_sh', '  NSC common shares outstanding (m; converted 1 : 1 plus $88.82 cash)', 'driver', 'm1', nsc='shout', e26_in=NSC_BS('shares_outstanding_m'), ae=lambda: f'={P("ns_sh")}',
      note='224.6m at 30-Sep-2026 (NSC 10-Q). Equity awards settled in shares / cash per the merger agreement (~0.3m UNP shares, pro forma).')
    S('ns_eps', '  Memo: NSC adjusted diluted EPS ($)', 'memo', 'ps', nsc='adj_eps')
    S('nd_hdr', 'Consideration, financing and purchase price allocation (at closing; USDm)', 'sub', 'gen')
    S('nd_cashps', '  Cash per NSC share ($) — merger agreement', 'driver', 'm2', ae_in_year=2027, ae=lambda: ('88.82' if CTX.col.year == 2027 else None), ae_literal=True)
    S('nd_xr', '  Exchange ratio (UNP shares per NSC share)', 'driver', 'm2', ae_in_year=2027, ae=lambda: ('1' if CTX.col.year == 2027 else None), ae_literal=True)
    S('nd_px', '  UNP share price at closing ($) — model share price × (1 + appreciation to closing)', 'driver', 'm2', ae_in_year=2027,
      ae=lambda: (f'={V("v_px", E26)}*(1+{V("ds_pxg")})^0.5' if CTX.col.year == 2027 else None),
      note='Stock consideration is valued at the UNP price at the first effective time (pro forma used $216.05). Model: valuation share price grown half a year.')
    S('nd_cash', '  Cash consideration (NSC shares × $88.82 + $20m award settlements)', 'line', 'm', ae_in_year=2027,
      ae=lambda: (f'={CB("ns_sh")}*{CB("nd_cashps")}+20' if CTX.col.year == 2027 else None))
    S('nd_shares', '  UNP shares issued (m; NSC shares × exchange ratio + ~0.3m for assumed equity awards)', 'line', 'm1', ae_in_year=2027,
      ae=lambda: (f'={CB("ns_sh")}*{CB("nd_xr")}+0.3' if CTX.col.year == 2027 else None))
    S('nd_stock', '  Stock consideration (shares issued × UNP price at closing)', 'line', 'm', ae_in_year=2027, ae=lambda: (f'={CB("nd_shares")}*{CB("nd_px")}' if CTX.col.year == 2027 else None))
    S('nd_total', '  Total consideration', 'line_b', 'm', ae_in_year=2027, ae=lambda: (f'={CB("nd_cash")}+{CB("nd_stock")}' if CTX.col.year == 2027 else None),
      note='Pro forma (424B3, UNP at $216.05): $68,711m. ±20% in the UNP price = ±$10bn of consideration and goodwill.')
    S('nd_debtpct', '  Cash consideration funded with new debt % (remainder from cash & short-term investments) — input', 'driver', 'pct', ae_in_year=2027,
      ae=lambda: (str(V0['nsc_debt_pct']) if CTX.col.year == 2027 else None), ae_literal=True,
      note='10-Q Note 18: "a combination of new debt and cash accumulated through cash provided by operating activities"; pro forma assumed 100% debt. Short-term investments of $875m at 30-Sep-2026 are being accumulated. Assumption.')
    S('nd_newdebt', '  New acquisition debt issued at closing', 'line', 'm', ae_in_year=2027, ae=lambda: (f'={CB("nd_cash")}*{CB("nd_debtpct")}+{CB("nd_fees")}' if CTX.col.year == 2027 else None))
    S('nd_rate', '  Interest rate on acquisition debt % — input', 'driver', 'pct', ae_in_year=2027, ae=lambda: ('0.05' if CTX.col.year == 2027 else None), ae_literal=True,
      note='Pro forma assumption 5% (±0.125% = ±$25m a year); UNP 2025 average cost of debt 4.1%.')
    S('nd_fees', '  Debt issuance & liability-management costs (capitalised, amortised over 15 years)', 'driver', 'm', ae_in_year=2027, ae=lambda: ('190' if CTX.col.year == 2027 else None), ae_literal=True)
    S('nd_mcost', '  Merger transaction costs expensed (UNP; adjusted out)', 'driver', 'm', ae_in_year=2027, ae=lambda: ('190' if CTX.col.year == 2027 else None), ae_literal=True,
      note='Pro forma estimate $190m; UNP expensed $72m in 2025 and $93m in 9M-26 as acquisition-related expense (adjusted out). Model: the input is recognised in the closing year on top of the run-rate.')
    S('np_hdr', 'Purchase price allocation (preliminary, per the pro forma; book values except the items below)', 'sub', 'gen')
    S('np_eq', '  NSC book equity at closing (30-Sep-2026 equity + retained earnings to closing)', 'line', 'm', ae_in_year=2027,
      ae=lambda: (f'={NSC_BS("total_stockholders_equity")}+({CB("ns_rev_q4py")}*(1+{CB("ns_g", )})*0+({CB("n_close")}-DATE(2026,9,30))/365.25*({CB("np_ni_rr")}-{CB("np_div_rr")}))' if CTX.col.year == 2027 else None),
      note='NSC equity $16,730m at 30-Sep-2026 plus (net income − dividends) at the 9M-26 annualised run-rate for the months to closing.')
    S('np_ni_rr', '    NSC net income run-rate (9M-26 annualised)', 'memo', 'm', ae_in_year=2027, ae=lambda: (str(round(NSC_9M('net_income') * 4 / 3, 1)) if CTX.col.year == 2027 else None), ae_literal=True)
    S('np_div_rr', '    NSC dividends run-rate (9M-26 annualised)', 'memo', 'm', ae_in_year=2027, ae=lambda: (str(round(NSC_9M_CF('dividends_paid') * 4 / 3, 1)) if CTX.col.year == 2027 else None), ae_literal=True)
    S('np_ppe', '  Fair-value step-up of NSC properties — input (pro forma: none; "a material portion could be attributed to properties")', 'driver', 'm', ae_in_year=2027,
      ae=lambda: (str(V0['nsc_ppe_stepup']) if CTX.col.year == 2027 else None), ae_literal=True,
      note='Assumption 0 (as in the pro forma). A $10bn step-up adds ~$275m of annual depreciation (2.75% composite rate, 424B3 Note 6[f]) and a $2.3bn deferred tax liability.')
    S('np_debtfv', '  Debt fair-value adjustment (NSC debt marked to market; reduces liabilities)', 'driver', 'm', ae_in_year=2027, ae=lambda: ('1348' if CTX.col.year == 2027 else None), ae_literal=True,
      note='424B3 Note 5[c]: $16,464m → $15,116m at 30-Jun-2025 (−$1,348m). The discount accretes through interest expense over the remaining life (assumed 10 years).')
    S('np_other', '  Other fair-value adjustments (retention bonus accrual −$192m; other liabilities)', 'driver', 'm', ae_in_year=2027, ae=lambda: ('-192' if CTX.col.year == 2027 else None), ae_literal=True)
    S('np_dtl', '  Deferred tax on the fair-value adjustments (23.0%)', 'line', 'm', ae_in_year=2027,
      ae=lambda: (f'=-0.23*({CB("np_ppe")}+{CB("np_debtfv")}+{CB("np_other")})' if CTX.col.year == 2027 else None))
    S('np_gw', '  Goodwill = consideration − (book equity + fair-value adjustments net of tax)', 'line_b', 'm', ae_in_year=2027,
      ae=lambda: (f'={CB("nd_total")}-({CB("np_eq")}+{CB("np_ppe")}+{CB("np_debtfv")}+{CB("np_other")}+{CB("np_dtl")})' if CTX.col.year == 2027 else None),
      note='Pro forma goodwill $53,078m at a $216.05 UNP price (424B3 Note 5[e]). Not amortised; no acquired-intangible amortization is assumed (none identified in the pro forma).')
    S('np_chk', '  Check: identifiable net assets + goodwill − consideration (should be 0)', 'check', 'm1', ae_in_year=2027,
      ae=lambda: (f'=ROUND({CB("np_eq")}+{CB("np_ppe")}+{CB("np_debtfv")}+{CB("np_other")}+{CB("np_dtl")}+{CB("np_gw")}-{CB("nd_total")},1)' if CTX.col.year == 2027 else None))
    S('sy_hdr', 'Synergies and costs to achieve (management assumed synergies, 424B3)', 'sub', 'gen')
    S('sy_rr', '  Net run-rate EBITDA synergies (USDm; scenario)', 'driver', 'm', ae=lambda: '=' + CH(SC['SYN'][CTX.col.year]),
      note='Gross $2.75bn (revenue $1.75bn + cost $1.0bn); advisors used $2.0bn net of illustrative concessions. Base $2.0bn, Bull $2.75bn, Bear $1.5bn.')
    S('sy_ph', '  Phase-in % (25% in year 1, 60% in year 2, 100% from year 3 after closing — assumption)', 'driver', 'pct',
      ae=lambda: f'=IF({V("n_yrs")}<=0,0,IF({V("n_yrs")}<1,0.25*{V("n_yrs")},IF({V("n_yrs")}<2,0.25+0.35*({V("n_yrs")}-1),IF({V("n_yrs")}<3,0.6+0.4*({V("n_yrs")}-2),1))))')
    S('sy_real', '  Synergies realised (reduce consolidated operating expenses)', 'line', 'm', ae=lambda: f'={CB("n_tog")}*{V("sy_rr")}*{V("sy_ph")}')
    S('sy_cta', '  Operating costs to achieve ($170m in the first year after closing; assumed pro rata)', 'line', 'm',
      ae=lambda: f'={CB("n_tog")}*170*MAX(0,MIN(1,{V("n_yrs")})-MAX(0,MIN(1,{P("n_yrs")})))')
    S('sy_capex', '  Capital expenditures to achieve ($2.0bn: half in each of the first two years)', 'line', 'm',
      ae=lambda: f'={CB("n_tog")}*1000*(MAX(0,MIN(2,{V("n_yrs")}))-MAX(0,MIN(2,{P("n_yrs")})))')
    S('nc_hdr', 'Contribution to the consolidated statements (× fraction of the year consolidated)', 'sub', 'gen')
    S('nc_rev', '  Operating revenues from Norfolk Southern', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("ns_rev")}*{V("n_frac")}')
    S('nc_opex', '  Operating expenses excl. depreciation (NSC OR − depreciation %) − synergies + costs to achieve', 'line', 'm', e26_in=0.0,
      ae=lambda: f'={V("ns_rev")}*({V("ns_or")}-{V("ns_dep_p")})*{V("n_frac")}-{V("sy_real")}+{V("sy_cta")}')
    S('nc_dep', '  Depreciation (NSC + step-up depreciation at 2.75%)', 'line', 'm', e26_in=0.0, ae=lambda: f'=({V("ns_dep")}+0.0275*{CB("np_ppe")})*{V("n_frac")}')
    S('nc_oi', '  Operating income contribution', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={V("nc_rev")}-{V("nc_opex")}-{V("nc_dep")}')
    S('nc_int', '  Interest: acquisition debt + NSC debt assumed + accretion of the debt fair-value discount + fee amortisation', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=({V("nd_newdebt_bal")}*{CB("nd_rate")}+{V("ns_int")}+{CB("np_debtfv")}/10+{CB("nd_fees")}/15)*{V("n_frac")}')
    S('nd_newdebt_bal', '  Memo: acquisition debt outstanding (held; refinanced at maturity)', 'memo', 'm', e26_in=0.0, ae=lambda: f'={CB("n_tog")}*{CB("nd_newdebt")}')
    S('nc_noncash', '  Memo: non-cash interest in the contribution (debt-discount accretion + fee amortisation; added back in cash from operations)', 'memo_calc', 'm', e26_in=0.0,
      ae=lambda: f'={CB("n_tog")}*({CB("np_debtfv")}/10*MIN(1,MAX(0,MIN(10,{V("n_yrs")})-MIN(10,{P("n_yrs")})))+{CB("nd_fees")}/15*{V("n_frac")})')
    S('nc_sh', '  Weighted average UNP shares added (m)', 'line', 'm1', e26_in=0.0, ae=lambda: f'={CB("n_tog")}*{CB("nd_shares")}*{V("n_frac")}')
    S('nc_ni', '  Memo: after-tax contribution to net income (OI − interest − merger costs) × (1 − tax rate)', 'memo_calc', 'm', e26_in=0.0,
      ae=lambda: f'=({V("nc_oi")}-{V("nc_int")}-IF(AND({V("n_frac")}>0,{P("n_frac")}=0),{CB("nd_mcost")},0))*(1-{V("is_etr")})')
    S('nc_acc', '  Memo: EPS accretion / (dilution) vs standalone (%)', 'memo_calc', 'pct', e26_in=0.0,
      ae=lambda: f'=IFERROR({V("eps_dil")}/(({V("is_ni")}-{V("nc_ni")})/({V("sh_dil")}-{V("nc_sh")}))-1,"")',
      note='Reported-EPS basis including purchase-accounting depreciation, acquisition interest and costs to achieve; the companies\' own accretion claims were on an adjusted basis (not in the 8-Ks).')
    S('nc_pf', '  Memo: pro forma full-year adjusted EBITDA (UNP + NSC run-rate + synergies; for leverage sizing)', 'memo_calc', 'm', e26_in=0.0,
      ae=lambda: f'={V("r_adj")}+{CB("n_tog")}*(1-{V("n_frac")})*({V("ns_oi")}+{V("ns_dep")}+{V("sy_rr")}*{V("sy_ph")})')
    blank()

    # ------------------------------------------------------------------ GROUP TOTAL & GUIDANCE CALIBRATION
    S('g_hdr', 'Group Total — operating revenues & operating income (build) → FY26 guidance calibration (reported EPS growth)', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Operating revenues (build + Norfolk Southern)', 'total', 'm', hist=lambda: f'={V("t_rev")}', fc=lambda: f'={V("t_rev")}+N({V("nc_rev")})')
    S('g_rev_g', '  Operating revenues y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: build vs consolidated operating revenues (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=0.6,0,ROUND({V("g_rev")}-{V("is_rev")},1)),"")')
    S('g_oi', 'Operating income (build: revenues − standalone adjusted operating expenses − adjusting items + NSC contribution)', 'total', 'm',
      hist=lambda: f'={V("is_oi")}', fc=lambda: f'={V("is_rev")}-{V("or_opex_x")}-{V("o_tot")}+N({V("nc_oi")})-N({V("nc_rev")})', e26=lambda: f'=SUM({Q1}{R["g_oi"]}:{QE}{R["g_oi"]})')
    S('g_oim', '  Operating margin %', 'pct', 'pct', all=ratio('g_oi', 'is_rev'))
    S('g_chk_oi', '  Check: build vs consolidated operating income (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_oi")}),IF(ABS({V("g_oi")}-{V("is_oi")})<=0.6,0,ROUND({V("g_oi")}-{V("is_oi")},1)),"")')
    S('cal_g', '  Memo: FY26 reported EPS growth guidance (scenario end-point; "high-single digit")', 'memo', 'pct', e26=lambda: '=' + CH(SC['out_eps']), note=V0['eps_guid_note'])
    S('cal_eps', '  Memo: FY26 reported diluted EPS target = FY2025 reported EPS × (1 + growth)', 'eps_memo', 'ps', e26=lambda: f'={Y("eps_dil", 2025)}*(1+{V("cal_g")})')
    S('cal_ni', '  Net income required (target EPS × FY26E diluted shares)', 'memo_calc', 'm', e26=lambda: f'={V("cal_eps")}*{V("sh_dil")}')
    S('cal_oi', '  Q4/26E operating income required ((NI − 9M actual) ÷ (1 − Q4 tax rate) + Q4 interest − Q4 other income)', 'memo_calc', 'm',
      e26=lambda: f'=({V("cal_ni")}-{ACT("is_ni")})/(1-{PT("pt_etr")})+{QEc("is_int")}-{QEc("is_othinc")}')
    S('cal_var_pre', '  Q4/26E variable cost lines before calibration (compensation, PS&M, rents, other at 9M-26 trends)', 'line', 'm',
      qe=lambda: (f'={V("v_emp")}*{P("co_pe")}*(1+IFERROR({ACT("is_comp")}/AVERAGE({Q1}{R["v_emp"]}:{Q3}{R["v_emp"]})/({ACT0("is_comp")}/AVERAGE({PQ1}{R["v_emp"]}:{PQ3}{R["v_emp"]}))-1,0))/1000/4'
                  f'+{V("is_rev")}*(({P("cr_psm")}+IFERROR({ACT("is_psm")}/{ACT("is_rev")}-{ACT0("is_psm")}/{ACT0("is_rev")},0))'
                  f'+({P("cr_rents")}+IFERROR({ACT("is_rents")}/{ACT("is_rev")}-{ACT0("is_rents")}/{ACT0("is_rev")},0))'
                  f'+({P("cr_oth")}+IFERROR({ACT("is_oth_adj")}/{ACT("is_rev")}-{ACT0("is_oth_adj")}/{ACT0("is_rev")},0)))'))
    S('cal_c', '  Guidance calibration: proportional shift on the variable cost lines (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("is_rev")}-{V("cal_oi", E26)}-{V("fu_exp")}-{V("cr_dep")}-{V("o_tot")})/{V("cal_var_pre")}-1',
      note='Solves the uniform % shift on compensation, PS&M, rents and other so that FY26 reported diluted EPS = FY2025 × (1 + guided growth) for the active scenario. Fuel (gallons × price), depreciation and acquisition costs are point estimates.')
    S('cal_chk', '  Check: FY26 reported diluted EPS vs guidance end-point (should be 0.00)', 'check', 'ps', e26=lambda: f'=ROUND({V("eps_dil")}-{V("cal_eps")},2)')
    S('cal_or', '  Memo: FY26E reported operating ratio vs FY2025 (pts; guidance: "improvement from the core business, challenged by fuel")', 'memo_calc', 'pct2',
      e26=lambda: f'={V("or_rep")}-{Y("or_rep", 2025)}')
    S('cal_capex', '  Memo: FY26 capital plan (guided $3.5bn) vs model capital investments', 'memo_calc', 'm', e26=lambda: f'=-{V("cf_capex")}-{PT("pt_capex")}')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF INCOME (US GAAP; Union Pacific presentation)', 'section',
      note='CONSOLIDATED IS — forecast logic (expense lines from the cost build + Norfolk Southern contribution; acquisition-related costs in other expenses)')
    S('is_frt', 'Freight revenues', 'line', 'm', data='frt', flow=True, fc=lambda: f'={V("f_rev")}+N({V("nc_rev")})',
      note='Forecast = freight build (+ NSC revenues, all shown as freight).')
    S('is_othrev', 'Other revenues', 'line', 'm', data='oth_rev', flow=True, fc=lambda: f'={V("o_rev")}')
    S('is_rev', 'Total operating revenues', 'total', 'm', data='rev', flow=True, fc=lambda: f'={V("is_frt")}+{V("is_othrev")}')
    S('is_comp', 'Compensation and benefits', 'line', 'm', data='comp', flow=True, fc=lambda: f'={V("co_exp")}+N({V("nc_opex")})*{V("nc_mix_comp")}')
    S('is_fuel', 'Fuel', 'line', 'm', data='fuel', flow=True, fc=lambda: f'={V("fu_exp")}+N({V("nc_opex")})*{V("nc_mix_fuel")}')
    S('is_psm', 'Purchased services and materials', 'line', 'm', data='psm', flow=True, fc=lambda: f'={V("is_rev")}*{V("cr_psm")}-N({V("nc_rev")})*{V("cr_psm")}+N({V("nc_opex")})*{V("nc_mix_psm")}')
    S('is_dep', 'Depreciation', 'line', 'm', data='dep', flow=True, fc=lambda: f'={V("cr_dep")}+N({V("nc_dep")})')
    S('is_rents', 'Equipment and other rents', 'line', 'm', data='rents', flow=True, fc=lambda: f'={V("is_rev")}*{V("cr_rents")}-N({V("nc_rev")})*{V("cr_rents")}+N({V("nc_opex")})*{V("nc_mix_rents")}')
    S('is_oth', 'Other (incl. acquisition-related expense and other company-adjusted items)', 'line', 'm', data='oth_exp', flow=True,
      fc=lambda: f'={V("is_rev")}*{V("cr_oth")}-N({V("nc_rev")})*{V("cr_oth")}+N({V("nc_opex")})*{V("nc_mix_oth")}+{V("o_tot")}')
    S('is_oth_adj', '  Memo: other expenses excl. company-adjusted items', 'memo_calc', 'm', all=lambda: f'=IF(ISNUMBER({V("is_oth")}),{V("is_oth")}-{V("o_tot")},"")')
    S('is_opex', 'Total operating expenses', 'line_b', 'm', data='opex', flow=True, fc=lambda: f'=SUM({V("is_comp")}:{V("is_rents")})+{V("is_oth")}')
    S('is_opex_chk', '  Check: Σ expense lines vs reported total (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_opex")}),IF(ABS({V("is_comp")}+{V("is_fuel")}+{V("is_psm")}+{V("is_dep")}+{V("is_rents")}+{V("is_oth")}-{V("is_opex")})<=0.6,0,ROUND({V("is_comp")}+{V("is_fuel")}+{V("is_psm")}+{V("is_dep")}+{V("is_rents")}+{V("is_oth")}-{V("is_opex")},1)),"")')
    S('is_oi', 'Operating income', 'total', 'm', data='oi', flow=True, fc=lambda: f'={V("is_rev")}-{V("is_opex")}')
    S('is_or', '  Operating ratio %', 'pct', 'pct', all=ratio('is_opex', 'is_rev'))
    S('is_othinc', 'Other income, net (income +; incl. real-estate gains, pension income, interest income)', 'line', 'm', data='oth_inc', flow=True,
      qe=lambda: f'={PT("pt_othinc")}', ae=lambda: f'={V("oi_othinc")}+{V("oi_cash_y")}*{P("cf_end")}',
      note='Q4/26E point estimate. 2027E+: recurring other income input + yield on opening cash & short-term investments.')
    S('oi_othinc', '  Recurring other income excl. interest income — input (2027E+)', 'driver', 'm', ae_in=V0['othinc'],
      note='2025 $629m incl. $250m of industrial park land sales (adjusted out); 2024 $350m; 9M-26 $291m. Input ~$300m (assumption).')
    S('oi_cash_y', '  Interest yield on opening cash & short-term investments % (input)', 'driver', 'pct', ae_in=0.035)
    S('is_int', 'Interest expense', 'line', 'm', data='int', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_cp")}*{V("ds_r_cp")}+{V("ds_newnotes")}*{V("ds_r_notes")}*0.5+N({V("nc_int")})',
      note='Q4/26E point estimate. 2027E+ = rate × opening notes + rate × opening CP / revolver + half-year on new notes + Norfolk Southern block interest (no circularity).')
    S('is_ebt', 'Income before income taxes', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_oi")}),{V("is_oi")}+{V("is_othinc")}-{V("is_int")},"")')
    S('is_tax', 'Income tax expense', 'line', 'm', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}+IF(AND(N({V("n_frac")})>0,N({P("n_frac")})=0),{CB("nd_mcost")}*{V("is_etr")},0)*0')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='9M-26 23.2% (Q3 23.8%); 2025 22.1% incl. the $115m deferred tax benefit; federal 21% + state ~3%. Q4/26E point estimate; 2027E+ input 23.5%.')
    S('is_ni', 'Net income', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_ni_chk', '  Check: net income vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=0.6,0,ROUND({V("is_ni")}-{V("is_ni_pub")},1)),"")')
    S('is_ni_pub', '  Memo: net income as reported', 'memo', 'm', data='ni', flow=True)
    S('is_dda', '  Memo: depreciation (total D&A; Union Pacific reports no separate amortization line)', 'memo_calc', 'm', all=lambda: f'={V("is_dep")}')
    S('is_sbc', '  Memo: share-based compensation', 'memo_calc', 'm', all=lambda: f'={V("cr_sbc")}')
    S('eps_hdr', '(Earnings per share — split-adjusted for the 2-for-1 stock split of 27-May-2014)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={B1("bs_shares")}-${E26}${R["bb_sh"]}*0.5+${E26}${R["bb_iss"]}*0.5',
      ae=lambda: f'=AVERAGE({V("bb_beg")}-N({P("nd_sh_cum")}),{V("bb_end")}-N({V("nd_sh_cum")}))+N({V("nc_sh")})',
      note='Q4/26E: shares outstanding at 30-Sep-2026 − Q4 buybacks (mid-quarter) + equity-plan issuance. 2027E+: average of beginning / ending shares (ex-deal) + deal shares weighted by days outstanding.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_basic', 'EPS – basic ($)', 'eps', 'ps', all=ratio('is_ni', 'sh_basic'))
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")',
      note='Net income ÷ weighted diluted shares (±$0.01 vs reported).')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($; split-adjusted)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0101,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('dps', '  Dividends declared per share ($; split-adjusted)', 'line', 'ps', data='dps', flow=True, qe_in=V0['dps_q'],
      ae=lambda: f'={P("dps")}*(1+{V("dps_g")})', note='Quarterly dividend $1.42 from Q3-26 (+3%). 2027E+: prior year × (1 + growth input; "consistent annual dividend increases").')
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'])
    S('payout', '  Dividend payout (DPS ÷ diluted EPS) %', 'pct', 'pct', all=ratio('dps', 'eps_dil'))
    S('leg_is_h', 'Legacy expense presentation 2006–07 (as originally reported; the FY2008 10-K re-presented the lines above) — memo', 'sub', 'gen')
    for k, lab in (('l_swb', 'Salaries, wages & employee benefits'), ('l_rents', 'Equipment & other rents'), ('l_dep', 'Depreciation'), ('l_fuelut', 'Fuel & utilities'),
                   ('l_mats', 'Materials & supplies'), ('l_pso', 'Purchased services & other')):
        S(f'leg_{k}', f'  {lab}', 'memo', 'm', data=k, flow=True)
    S('nc_mix_h', 'Allocation of the Norfolk Southern operating expenses (excl. depreciation) to Union Pacific expense lines (pro forma reclassified mix, FY2024) — inputs', 'sub', 'gen')
    for k, lab, v in (('comp', 'Compensation & benefits', 0.44), ('fuel', 'Fuel', 0.15), ('psm', 'Purchased services & materials', 0.27), ('rents', 'Equipment & other rents', 0.06), ('oth', 'Other', 0.08)):
        S(f'nc_mix_{k}', f'  {lab} share of NSC opex excl. depreciation', 'driver', 'pct', e26_in=v, ae_in=v,
          note='424B3 pro forma FY2024 NSC expenses reclassified to the UNP presentation: compensation 2,823 + 101 + 300; PS&M 2,048 − 393 + 369; fuel 987; rents 393; other 454 + 82 (excl. depreciation and the Eastern Ohio incident).' if k == 'comp' else None)
    blank()

    # ------------------------------------------------------------------ RECON 1: OI -> adjusted OI
    S('sec_r1', 'RECONCILIATION: OPERATING INCOME → ADJUSTED OPERATING INCOME / OPERATING RATIO (company "Financial Performance" items; adjusted = GAAP where none published)', 'section',
      note='ADJUSTED OI — items the company identified as affecting comparability (release non-GAAP tables); forecast = acquisition-related expense only')
    S('o_op', 'Operating income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_oi")}')
    S('d_acq', '  (+) Acquisition-related expense (Norfolk Southern merger costs; non-deductible)', 'line', 'm', data='oa_acq', flow=True, labkey='oa_acq_lab',
      qe=lambda: f'={PT("pt_acq")}', ae=lambda: f'=IF(AND(N({V("n_frac")})>0,N({P("n_frac")})=0),{CB("nd_mcost")},0)+{V("d_acq_rr")}',
      note='9M-26 $93m ($36m / $35m / $22m); Q4/26E point estimate. 2027E: closing-year transaction costs input (pro forma $190m) + run-rate until closing.')
    S('d_acq_rr', '  Run-rate pre-closing merger costs (input; 0 after closing)', 'driver', 'm', ae=lambda: f'=IF(N({V("n_frac")})<1,{V0["acq_rr"]}*(1-N({V("n_frac")})),0)')
    S('d_impair', '  (+) Brazos Yard impairment (Q4-20)', 'line', 'm', data='oa_impair', flow=True, labkey='oa_impair_lab', fc=lambda: '=0')
    S('d_gain', '  (+/−) Gains on asset sales adjusted out (intermodal equipment Q2-24)', 'line', 'm', data='oa_gain', flow=True, labkey='oa_gain_lab', fc=lambda: '=0')
    S('d_oadj', '  (+) Other items (2017 equity-method remeasurement, 2022 labor accrual, 2024 environmental remediation, 2024–25 crew staffing agreements)', 'line', 'm',
      data='oa_other', flow=True, labkey='oa_other_lab', fc=lambda: '=0')
    S('o_tot', '  Total adjusting items in operating income', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("d_acq")}),{nsum(ADJ)},"")')
    S('o_adj', '  = Adjusted operating income (model bridge)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_tot")},"")',
      note='Company definition where published (2017, 2020, 2022, 2024–26); otherwise equal to GAAP operating income.')
    S('o_adj_or', '  Adjusted operating ratio %', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("o_adj")}),1-{V("o_adj")}/{V("is_rev")},"")')
    S('o_pub', '  Company-published adjusted operating income', 'memo', 'm', data='adj_oi_pub', flow=True)
    S('o_chk', '  Check: model bridge vs company-published adjusted operating income (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),IF(ABS({V("o_adj")}-{V("o_pub")})<=0.6,0,ROUND({V("o_adj")}-{V("o_pub")},1)),"n/p")')
    S('o_or_pub', '  Company-published adjusted operating ratio (%)', 'memo', 'pct', data='adj_or_pub', pctin=True)
    S('o_or_chk', '  Check: model vs published adjusted operating ratio (should be 0; ±0.05pt)', 'check', 'pct2',
      hist=lambda: f'=IF(ISNUMBER({V("o_or_pub")}),IF(ABS({V("o_adj_or")}-{V("o_or_pub")})<=0.00051,0,ROUND({V("o_adj_or")}-{V("o_or_pub")},4)),"n/p")')
    S('o_def', '  Definition / basis (company adjusted definition in force)', 'text', 'gen', note='Changes flagged in the column where they take effect (cell comments quote the release).')
    S('o_adj_g', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental adjusted operating margin (Δ adjusted OI / Δ revenues)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: NI -> EBITDA -> adjusted EBITDA
    S('sec_r2', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (model definition) · COMPANY "ADJUSTED EBITDA" (leverage covenant basis, trailing twelve months)', 'section',
      note='EBITDA — NI + tax + interest − other income = operating income; + depreciation = EBITDA; + adjusting items = adjusted EBITDA (model). The company measure also deducts other income and adds operating-lease interest.')
    S('r_ni', 'Net income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('r_tax', '  (+) Income tax expense', 'line', 'm', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest expense', 'line', 'm', all=lambda: f'={V("is_int")}')
    S('r_oth', '  (−) Other income, net', 'line', 'm', all=lambda: f'=-{V("is_othinc")}')
    S('r_op', '  = Operating income', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_tax")}+{V("r_int")}+{V("r_oth")},"")')
    S('r_dep', '  (+) Depreciation', 'line', 'm', all=lambda: f'={V("is_dep")}')
    S('r_ebitda', '  = EBITDA (operating income + depreciation)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("r_op")}),{V("r_op")}+{V("r_dep")},"")')
    S('r_ebitda_m', '  EBITDA margin %', 'pct', 'pct', all=ratio('r_ebitda', 'is_rev'))
    S('r_items', '  (+) Adjusting items in operating income (bridge above)', 'line', 'm', all=lambda: f'={V("o_tot")}')
    S('r_adj', '  = Adjusted EBITDA (model; adjusted operating income + depreciation)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{V("r_ebitda")}+{V("r_items")},"")',
      note='Used for leverage (net debt / adjusted EBITDA) and EV / EBITDA. Union Pacific publishes "adjusted EBITDA" only on a trailing-twelve-month covenant basis (memo below).')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_co_h', 'Company "adjusted EBITDA" (trailing twelve months; adjusted debt / adjusted EBITDA tables):', 'sub', 'gen')
    S('r_co', '  Model rebuild: NI + tax + depreciation + interest − other income + interest on operating lease liabilities (annual columns)', 'line', 'm', ann=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("r_co_lease")}),ISNUMBER({V("is_ni")})),{V("is_ni")}+{V("is_tax")}+{V("is_dep")}+{V("is_int")}-{V("is_othinc")}+{V("r_co_lease")},"")',
      fc=lambda: f'={V("is_ni")}+{V("is_tax")}+{V("is_dep")}+{V("is_int")}-{V("is_othinc")}+{V("r_co_lease")}')
    S('r_co_lease', '  Interest on operating lease liabilities (company table; forecast input)', 'line', 'm', ann=True, data='lease_int_ttm', fc=lambda: f'={V0["lease_int"]}')
    S('r_co_pub', '  Company-published adjusted EBITDA (TTM at year end)', 'memo', 'm', ann=True, data='adj_ebitda_ttm')
    S('r_co_chk', '  Check: rebuild vs company-published adjusted EBITDA (should be 0; n/p where the item is not disclosed)', 'check', 'm1', ann=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("r_co_pub")}),ISNUMBER({V("r_co")})),IF(ABS({V("r_co")}-{V("r_co_pub")})<=0.6,0,ROUND({V("r_co")}-{V("r_co_pub")},1)),"n/p")')
    S('r_roic_pub', '  Memo: company-published return on invested capital as adjusted (%)', 'memo', 'pct', ann=True, data='roic_pub', pctin=True)
    S('r_ebit_h', 'To adjusted EBIT (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ddan', '  (−) Depreciation', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("r_dep")}),-{V("r_dep")},"")')
    S('r_ebit', '  = Adjusted EBIT (= adjusted operating income; Union Pacific has no acquired-intangible amortization)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+{V("r_ddan")},"")')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: acquisition-related costs and costs to achieve synergies (cash items adjusted out; deducted in the DCF)', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("d_acq")}),{V("d_acq")}+N({V("sy_cta")}),"")')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: NET INCOME / DILUTED EPS → ADJUSTED NET INCOME → ADJUSTED EPS (company definition where published)', 'section',
      note='ADJUSTED EPS — net income + items in operating income + items in other income − tax effect (incl. discrete tax items: 2017 Tax Act, 2025 deferred tax adjustment)')
    S('e_ni', 'Net income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('e_op', '  (+) Adjusting items in operating income', 'line', 'm', all=lambda: f'={V("o_tot")}')
    S('e_othinc', '  (+/−) Items in other income adjusted out (industrial park land sales 2025)', 'line', 'm', data='oa_othinc', flow=True, fc=lambda: '=0')
    S('e_tax', '  (−) Tax effect of the items and discrete tax items (company tables; acquisition-related costs are non-deductible)', 'line', 'm', data='oa_tax', flow=True,
      fc=lambda: f'=-({V("e_op")}-{V("d_acq")}+{V("e_othinc")})*{V("is_etr")}', neg=True,
      note='Historical: company tax column (2017 deferred-tax remeasurement $5,935m; 2025 deferred tax adjustment $115m benefit). Forecast: items × tax rate; acquisition costs non-deductible.')
    S('e_adjni', '  = Adjusted net income (model bridge)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("e_ni")}),{V("e_ni")}+{V("e_op")}+N({V("e_othinc")})+{V("e_tax")},"")')
    S('e_pubni', '  Company-published adjusted net income', 'memo', 'm', data='adj_ni_pub', flow=True)
    S('e_chkni', '  Check: model vs company-published adjusted net income (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("e_pubni")}),IF(ABS({V("e_adjni")}-{V("e_pubni")})<=0.6,0,ROUND({V("e_adjni")}-{V("e_pubni")},1)),"n/p")')
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted EPS – diluted ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted EPS ($)', 'eps_memo', 'ps', data='adj_eps_pub')
    S('e_chk', '  Check: model vs company-published adjusted EPS (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0101,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_def', '  Definition / basis (company adjusted EPS definition)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Operating revenues y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_frt', '  Freight revenues y/y %', 'growth', 'pct', all=growth('is_frt'))
    S('gm_cars', '  Revenue carloads y/y %', 'growth', 'pct', all=growth('f_cars'))
    S('gm_arpc', '  Average revenue per car y/y %', 'growth', 'pct', all=growth('f_arpc'))
    S('gm_adjop', '  Adjusted operating income y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating income y/y %', 'growth', 'pct', all=growth('is_oi'))
    S('gm_ni', '  Net income y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Diluted EPS y/y % (reported)', 'growth', 'pct', all=growth('eps_dil'))
    S('gm_or', '  Operating ratio %', 'pct', 'pct', all=ratio('is_opex', 'is_rev'))
    S('gm_aor', '  Adjusted operating ratio %', 'pct', 'pct', all=lambda: f'={V("o_adj_or")}')
    S('gm_adjop_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_inc', '  Incremental adjusted operating margin (Δ adjusted OI / Δ revenues)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_oi', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_comp', '  Compensation & benefits % of revenues', 'pct', 'pct', all=ratio('is_comp', 'is_rev'))
    S('gm_fuel', '  Fuel % of revenues', 'pct', 'pct', all=ratio('is_fuel', 'is_rev'))
    blank()

# ---------------------------------------------------------------- NSC helpers (data from data/nsc_standalone.json)
def NSC_Q(k, field):
    return NSC['periods'][k]['is'][field]
def NSC_9M(field):
    return sum(NSC['periods'][k]['is'][field] for k in ('Q1-26', 'Q2-26', 'Q3-26'))
def NSC_9M_CF(field):
    return NSC['periods']['Q3-26']['cf_ytd'][field]
def NSC_BS(field):
    return NSC['periods']['Q3-26']['bs'][field]
NSC_INT26 = sum(NSC['periods'][k]['is']['interest_expense_on_debt'] for k in ('Q1-26', 'Q2-26', 'Q3-26')) + NSC['periods']['Q4-25']['is']['interest_expense_on_debt']
