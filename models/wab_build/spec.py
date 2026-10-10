"""Row specification of the WAB Model sheet (MLM template layout and process)."""
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

FRT = [('svc', 'Services', 'services'), ('eq', 'Equipment', 'equipment'), ('comp', 'Components', 'components'),
       ('dig', 'Digital Intelligence (Digital Electronics to 2023)', 'digital')]
TRN = [('oe', 'Original Equipment Manufacturer (OE)', 'oe'), ('am', 'Aftermarket', 'aftermarket')]
LINES = [f'f_{k}' for k, _, _ in FRT] + [f't_{k}' for k, _, _ in TRN]

# ====================================================================== scenario table (CN:CR)
SCEN_ROWS = []
def scen_layout(V0):
    """V0: dict of scenario inputs (outlook, point estimates, lever bases)."""
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of FY26 guidance ranges.'))
    r = 11
    SCEN_ROWS.append((r, 'out_hdr', V0['out_hdr'], 'High', 'Mid', 'Low', V0['out_note']))
    r += 1
    for key, lab, (hi, mid, lo), nf, note in V0['outlook']:
        SC[key] = r; SCEN_ROWS.append((r, 'out', lab, hi, mid, lo, note, nf)); r += 1
    r = 15
    SCEN_ROWS.append((r, 'pt_hdr', 'FY26 point estimates (all cases)', None, None, None, None)); r += 1
    for key, lab, vals, nf, note in V0['points']:
        SC[key] = r
        if isinstance(vals, tuple): SCEN_ROWS.append((r, 'out', lab, vals[0], vals[1], vals[2], note, nf))
        else: SCEN_ROWS.append((r, 'pt', lab, None, vals, None, note, nf))
        r += 1
    r = max(r, 28)
    SC['LEV'] = r
    SCEN_ROWS.append((r, 'lev', '  Minimum net debt / Adjusted EBITDA (x) — buyback floor 2027E+', *V0['lev'], V0['lev_note']))
    r = 30
    for name, lab, dbull, dbear, base, note, nf, clamp in V0['blocks']:
        SCEN_ROWS.append((r, 'blk', lab, dbull, 'Δ →', dbear, note, nf)); hdr = r; r += 1
        SC[name] = {}
        for y, b in zip((2027, 2028, 2029, 2030), base):
            SC[name][y] = r; SCEN_ROWS.append((r, 'yr', f'  {y}E', hdr, b, clamp, None, nf)); r += 1
    return r

# ====================================================================== row spec
def build_spec(V0):
    S = add
    # ------------------------------------------------------------------ PRODUCT-LINE BUILD
    S('sec_pl', 'PRODUCT-LINE P&L — FREIGHT (SERVICES · EQUIPMENT · COMPONENTS · DIGITAL INTELLIGENCE) · TRANSIT (OE · AFTERMARKET) · BACKLOG', 'section',
      note='PRODUCT-LINE BUILD — modelling logic (product-line sales → segment sales × adjusted operating margin → adjusted operating income → Adjusted EBITDA / adjusted EPS)')
    blank()
    for seg, segkey, title, lines, blab in [
        ('f', 'frt', 'Freight segment (locomotives & modernizations, services, components, digital intelligence; ~70% of sales)', FRT, 'Freight'),
        ('t', 'trn', 'Transit segment (passenger-rail original equipment & aftermarket: brakes, doors, HVAC, couplers, pantographs)', TRN, 'Transit')]:
        S(f'{seg}_hdr', title, 'block', note=f'{blab.upper()} — modelling logic')
        S(f'{seg}_bl12', f'  12-month backlog — {blab} (period end)', 'line', 'm', data=f'seg.{segkey}_backlog_12m', stock=True,
          note='Company-reported 12-month backlog (subset of total backlog). Historical only; context for the Q3/Q4-26E growth inputs.')
        S(f'{seg}_bltot', f'  Total (multi-year) backlog — {blab} (period end)', 'line', 'm', data=f'seg.{segkey}_backlog_total', stock=True)
        S(f'{seg}_cov', '  12-month backlog ÷ annualised sales (x)', 'line', 'x2',
          hist=lambda seg=seg: f'=IF(AND(ISNUMBER({V(seg + "_bl12")}),ISNUMBER({V(seg + "_rev")})),IFERROR({V(seg + "_bl12")}/({V(seg + "_rev")}*{4 if CTX.col.q else 1}),""),"")',
          note='12-month backlog over quarterly sales × 4 (annual columns: full-year sales). >1.0x = next-twelve-month sales largely covered.')
        for k, lab, dk in lines:
            key = f'{seg}_{k}'
            S(key, f'  {lab} — sales', 'line', 'm', data=f'seg.{segkey}_pl.{dk}', flow=True,
              qe=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})',
              ae=lambda key=key: f'={P(key)}*(1+{V(key + "_g")})',
              note=f'Product-line sales as published (from 2019, GE Transportation merger). Q3/Q4-26E: prior-year quarter × (1 + growth). 2027E+: prior year × (1 + scenario lever).')
            S(key + '_g', '    y/y %', 'growth', 'pct', all=growth(key),
              qe=lambda key=key: f'={V(key + "_pre")}+{BYv("cal_g")}',
              ae=lambda key=key, k=k, seg=seg: '=' + CH(SC[f'{seg.upper()}_{k.upper()}'][CTX.col.year]),
              note='Q3/Q4-26E: growth input (row below) + revenue-outlook calibration Δ (Group block). 2027E–2030E: scenario lever (Bull/Base/Bear table →).')
            S(key + '_pre', '    Q3/Q4-26E growth input before revenue calibration', 'driver', 'pct',
              qe_in=V0['qe_growth'][key], note=V0['qe_growth_note'][key])
        S(f'{seg}_unsplit', f'  {blab} sales not split by product line (pre-2019 disclosure)', 'line', 'm',
          hist=lambda seg=seg, lines=lines: f'=IF(ISNUMBER({V(seg + "_rev")}),{V(seg + "_rev")}-({nsum([f"{seg}_{k}" for k, _, _ in lines])}),"")',
          note='Historical segment sales less the product-line split (product lines are published from 2019; earlier years show the segment total here).')
        S(f'{seg}_rev', f'  {blab} segment net sales', 'line_b', 'm', data=f'seg.{segkey}_rev', flow=True,
          fc=lambda seg=seg, lines=lines: '=' + nsum([f'{seg}_{k}' for k, _, _ in lines]),
          note='Historical = segment net sales as originally reported. Forecast = Σ product lines.')
        S(f'{seg}_rev_g', '  Segment net sales y/y %', 'growth', 'pct', all=growth(f'{seg}_rev'))
        S(f'{seg}_gp', '  Segment gross profit (GAAP; published from 2019)', 'line', 'm', data=f'seg.{segkey}_gp', flow=True)
        S(f'{seg}_gm', '  Segment gross margin %', 'pct', 'pct', hist=ratio(f'{seg}_gp', f'{seg}_rev'))
        S(f'{seg}_adjop', f'  {blab} adjusted income from operations (company definition)', 'line_b', 'm', data=f'seg.{segkey}_adj_op', flow=True,
          qe=lambda seg=seg: f'={V(seg + "_rev")}*{V(seg + "_adjm")}', ae=lambda seg=seg: f'={V(seg + "_rev")}*{V(seg + "_adjm")}',
          note='Segment adjusted operating income as published (segment Reported→Adjusted tables). Forecast = segment sales × adjusted operating margin.')
        S(f'{seg}_adjm', '  Adjusted operating margin %', 'pct', 'pct', all=ratio(f'{seg}_adjop', f'{seg}_rev'),
          qe=lambda seg=seg: f'={V(seg + "_adjm_pre")}+{BYv("cal_m")}',
          ae=lambda seg=seg: '=' + CH(SC[f'{seg.upper()}_OPM'][CTX.col.year]),
          note='Q3/Q4-26E: margin before calibration + adjusted-EPS-outlook calibration Δ (Group block). 2027E–2030E: scenario lever.')
        S(f'{seg}_adjm_pre', '  Adjusted operating margin before outlook calibration % (Q3/Q4-26E helper)', 'pct', 'pct',
          qe=lambda seg=seg: (f'={P(seg + "_adjm")}+({H1(seg + "_adjop")}/{H1(seg + "_rev")}-{H1(seg + "_adjop", 2025)}/{H1(seg + "_rev", 2025)})'),
          note='Prior-year quarter margin + (1H/26 − 1H/25 adjusted margin drift).')
        S(f'{seg}_inc', '  Incremental adjusted operating margin (Δ adj. op. income / Δ sales)', 'pct', 'pct', all=incr(f'{seg}_adjop', f'{seg}_rev'))
        S(f'{seg}_items', '  Adjusting items in segment (amortization, restructuring, purchase accounting, transaction)', 'line', 'm', flow=True,
          hist=lambda seg=seg: f'=IF(AND(ISNUMBER({V(seg + "_adjop")}),ISNUMBER({V(seg + "_op")})),{V(seg + "_adjop")}-{V(seg + "_op")},"")',
          fc=lambda seg=seg: f'={V("o_tot")}*{V(seg + "_share")}',
          note='Historical = adjusted − GAAP segment operating income. Forecast = consolidated operating-level adjusting items × segment share.')
        S(f'{seg}_share', '  Segment share of consolidated operating-level adjusting items %', 'pct', 'pct',
          hist=lambda seg=seg: f'=IF(ISNUMBER({V(seg + "_items")}),IFERROR({V(seg + "_items")}/{V("o_tot")},""),"")',
          qe=lambda seg=seg: f'=IFERROR({H1(seg + "_items")}/{H1("o_tot")},0)', e26=lambda seg=seg: f'=IFERROR({V(seg + "_items")}/{V("o_tot")},"")',
          ae=lambda seg=seg: f'=$BZ${R[seg + "_share"]}', note='Forecast at the 1H/26 share (Freight carries most acquired-intangible amortization).')
        S(f'{seg}_op', f'  {blab} income from operations (GAAP)', 'line', 'm', data=f'seg.{segkey}_op', flow=True,
          fc=lambda seg=seg: f'={V(seg + "_adjop")}-{V(seg + "_items")}')
        S(f'{seg}_opm', '  GAAP operating margin %', 'pct', 'pct', all=ratio(f'{seg}_op', f'{seg}_rev'))
        blank()

    # ------------------------------------------------------------------ 2025-26 acquired businesses / sales bridge
    S('a_hdr', '2025–26 acquired businesses (Frauscher · Inspection Technologies · Dellner Couplers · 2026 bolt-ons) & sales-change bridge', 'block',
      note='ACQUIRED BUSINESSES — sales-change bridge as published (acquisitions / portfolio optimization / FX / organic); purchase-price allocations in the BS schedules')
    S('a_acq', '  Sales change from acquisitions (y/y, as published)', 'line', 'm', data='seg.bridge.total.acq', flow=True,
      qe_in=V0['qe_acq'], note=V0['qe_acq_note'])
    S('a_frt_acq', '    of which: Freight', 'line', 'm', data='seg.bridge.frt.acq', flow=True)
    S('a_trn_acq', '    of which: Transit', 'line', 'm', data='seg.bridge.trn.acq', flow=True)
    S('a_div', '  Sales change from portfolio optimization / divestitures (y/y)', 'line', 'm', data='seg.bridge.total.divest', flow=True, qe_in={3: 0.0, 4: 0.0})
    S('a_fx', '  Sales change from foreign exchange (y/y)', 'line', 'm', data='seg.bridge.total.fx', flow=True, qe_in={3: 0.0, 4: 0.0})
    S('a_org', '  Organic sales change (y/y)', 'line', 'm', data='seg.bridge.total.organic', flow=True,
      qe=lambda: f'={V("is_rev")}-{P("is_rev")}-{V("a_acq")}-{V("a_div")}-{V("a_fx")}',
      note='Forecast = total change − acquisitions − divestitures − FX (FX assumed nil).')
    S('a_org_g', '  Organic sales growth %', 'growth', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("a_org")}),ISNUMBER({P("is_rev")})),IFERROR({V("a_org")}/{P("is_rev")},""),"")' if CTX.col.prior else None),
      ae=lambda: f'=IFERROR(({V("is_rev")}-{V("m_rev")}-({P("is_rev")}-{P("m_rev")}))/{P("is_rev")},"")',
      note='2027E+: growth excluding sales from future acquisitions (FX nil).')
    S('a_acq_g', '  Acquisition contribution to growth %', 'growth', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("a_acq")}),ISNUMBER({P("is_rev")})),IFERROR({V("a_acq")}/{P("is_rev")},""),"")' if CTX.col.prior else None),
      ae=lambda: f'=IFERROR(({V("m_rev")}-{P("m_rev")})/{P("is_rev")},"")')
    S('a_fx_g', '  FX contribution to growth %', 'growth', 'pct',
      all=lambda: (f'=IF(AND(ISNUMBER({V("a_fx")}),ISNUMBER({P("is_rev")})),IFERROR({V("a_fx")}/{P("is_rev")},""),"")' if CTX.col.prior else None))
    S('a_chk', '  Check: bridge vs reported sales change (should be 0)', 'check', 'm1',
      hist=lambda: (f'=IF(AND(ISNUMBER({V("a_org")}),ISNUMBER({V("a_acq")}),ISNUMBER({P("is_rev")})),ROUND({V("is_rev")}-{P("is_rev")}-{V("a_acq")}-N({V("a_div")})-N({V("a_fx")})-{V("a_org")},0),"n/p")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ corporate
    S('c_hdr', 'Corporate activities & elimination (unallocated)', 'block', note='CORPORATE & RECONCILING ITEMS')
    S('c_adjop', '  Corporate adjusted income (loss) from operations', 'line', 'm', flow=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("o_adj_pub")}),ISNUMBER({V("f_adjop")}),ISNUMBER({V("t_adjop")})),{V("o_adj_pub")}-{V("f_adjop")}-{V("t_adjop")},"")',
      qe=lambda: f'={H1("c_adjop")}/2', ae=lambda: f'={V("is_rev")}*{V("c_pct")}',
      note='Historical = published consolidated adjusted operating income − segment adjusted operating income. Q3/Q4-26E: 1H/26 run-rate; 2027E+: % of sales input.')
    S('c_pct', '  Corporate adjusted cost % of sales', 'pct', 'pct', hist=ratio('c_adjop', 'is_rev'), e26=ratio('c_adjop', 'is_rev'), ae_in=V0['c_pct'])
    S('c_items', '  Corporate adjusting items', 'line', 'm', flow=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("c_adjop")}),ISNUMBER({V("c_op")})),{V("c_adjop")}-{V("c_op")},"")',
      fc=lambda: f'={V("o_tot")}-{V("f_items")}-{V("t_items")}-N({V("m_amort")})')
    S('c_op', '  Corporate income (loss) from operations (GAAP)', 'line', 'm', data='seg.corp_op', flow=True,
      fc=lambda: f'={V("c_adjop")}-{V("c_items")}')
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — bolt-ons, unallocated; deals closed from 2027E)', 'block',
      note='M&A LEVER — acquired sales = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})',
      note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=3.5, e26_in=0.0,
      note='Wabtec bolt-ons: Inspection Technologies ~$1.78bn on ~$0.45bn sales (~4x), Dellner ~$0.96bn, Frauscher ~€0.68bn; 3.5x input.')
    S('m_acq_sales', '  Annualised sales acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.06)
    S('m_run', '  Run-rate sales of businesses acquired (year end)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Sales from future acquisitions', 'line_b', 'm', e26_in=0.0,
      ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}',
      note='Mid-year convention: deals close evenly through the year (half a year of sales in year 1). Allocated to neither segment (unallocated line in the Group build).')
    S('m_m', '  Adjusted operating margin of acquired businesses % (before PPA amortization)', 'driver', 'pct', e26_in=0.0, ae_in=0.22)
    S('m_adjop', '  Adjusted operating income from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.08)
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.35,
      note='Inspection Technologies / Dellner PPAs: customer relationships, technology and trade names ~30–40% of consideration; balance goodwill.')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=15)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (within amortization expense)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)',
      note='Non-cash; added back in adjusted operating income / adjusted EPS (company definition).')
    blank()

    # ------------------------------------------------------------------ group total & outlook calibration
    S('g_hdr', 'Group Total — net sales & adjusted operating income (product-line build) → FY26 outlook calibration', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Net sales (product-line build)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("f_rev")}),N({V("f_rev")})+N({V("t_rev")}),"")',
      fc=lambda: f'=N({V("f_rev")})+N({V("t_rev")})+N({V("m_rev")})',
      note='Σ Freight + Transit segment sales (+ future acquisitions from 2027E).')
    S('g_adjop', 'Adjusted income from operations (product-line build)', 'total', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("f_adjop")}),ISNUMBER({V("c_adjop")})),{V("f_adjop")}+{V("t_adjop")}+{V("c_adjop")},"")',
      fc=lambda: f'={V("f_adjop")}+{V("t_adjop")}+{V("c_adjop")}+N({V("m_adjop")})',
      note='Σ segment adjusted operating income + corporate (+ future acquisitions). Wabtec\'s primary profit KPI.')
    S('g_adjm', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('g_adjop', 'g_rev'))
    S('g_rev_g', '  Net sales y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: product-line build vs consolidated net sales (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=0.15,0,ROUND({V("g_rev")}-{V("is_rev")},1)),"")')
    S('g_chk_adj', '  Check: build vs adjusted income from operations bridge (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_adjop")}),ISNUMBER({V("o_adj")})),ROUND({V("g_adjop")}-{V("o_adj")},1),"")')
    S('g_op', '  Income from operations (GAAP; Σ segments + corporate)', 'line', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("f_op")}),ISNUMBER({V("c_op")})),{V("f_op")}+{V("t_op")}+{V("c_op")}+N({V("m_adjop")})-N({V("m_amort")}),"")')
    S('g_chk_op', '  Check: segment build vs consolidated income from operations (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_op")}),ROUND({V("g_op")}-{V("is_op")},0),"")')
    S('cal_guid', '  Memo: FY26 net sales guidance (scenario end-point)', 'memo', 'm', e26=lambda: '=' + CH(SC['out_rev']),
      note=V0['rev_guid_note'])
    S('cal_pre', '  Net sales before revenue calibration (Q3/Q4-26E helper)', 'line', 'm',
      qe=lambda: '=' + '+'.join(f'{P(k)}*(1+{V(k + "_pre")})' for k in LINES))
    S('cal_sens', '  Net sales sensitivity to +1.00 of growth (Q3/Q4-26E helper)', 'line', 'm',
      qe=lambda: '=' + '+'.join(P(k) for k in LINES))
    S('cal_g', '  Outlook calibration: Δ y/y growth applied to all product lines (Q3/Q4-26E)', 'driver', 'pct',
      qe=lambda: (f'=({V("cal_guid","CA")}-BW{R["g_rev"]}-BX{R["g_rev"]}-BY{R["cal_pre"]}-BZ{R["cal_pre"]})/(BY{R["cal_sens"]}+BZ{R["cal_sens"]})'
                  if CTX.col.q == 3 else f'=$BY${R["cal_g"]}'),
      note='Solves the uniform growth shift (vs the Q3/Q4-26E inputs) so that FY26 net sales = the FY26 guidance end-point for the active scenario.')
    S('cal_rev_chk', '  Check: FY26 net sales vs guidance end-point (should be 0)', 'check', 'm1',
      e26=lambda: f'=ROUND({V("g_rev")}-{V("cal_guid")},1)')
    S('cal_eps', '  Memo: FY26 adjusted EPS guidance (scenario end-point, $)', 'eps_memo', 'ps', e26=lambda: '=' + CH(SC['out_eps']),
      note=V0['eps_guid_note'])
    S('cal_ni', '  Required FY26 adjusted net income = guidance × FY26 diluted shares', 'line', 'm',
      e26=lambda: f'={V("cal_eps")}*{V("e_sh")}')
    S('cal_adj_pre', '  Adjusted income from operations before margin calibration (Q3/Q4-26E helper)', 'line', 'm',
      qe=lambda: f'={V("f_rev")}*{V("f_adjm_pre")}+{V("t_rev")}*{V("t_adjm_pre")}+{V("c_adjop")}')
    S('cal_adj_req', '  Required 2H/26 adjusted income from operations (given interest, other, tax & NCI)', 'line', 'm',
      qe=lambda: ((f'=(({V("cal_ni","CA")}-BW{R["e_adjni"]}-BX{R["e_adjni"]})+BY{R["is_nci"]}+BZ{R["is_nci"]})/(1-{PT("pt_etr")})'
                   f'+BY{R["is_int"]}+BZ{R["is_int"]}-BY{R["is_oth"]}-BZ{R["is_oth"]}') if CTX.col.q == 3 else None),
      note='(Required 2H adjusted net income + NCI) ÷ (1 − tax rate) + net interest − other income: adjusting items are excluded on both sides.')
    S('cal_m', '  Outlook calibration: Δ adjusted operating margin applied to both segments (Q3/Q4-26E)', 'driver', 'pct',
      qe=lambda: (f'=(BY{R["cal_adj_req"]}-BY{R["cal_adj_pre"]}-BZ{R["cal_adj_pre"]})/(BY{R["f_rev"]}+BZ{R["f_rev"]}+BY{R["t_rev"]}+BZ{R["t_rev"]})'
                  if CTX.col.q == 3 else f'=$BY${R["cal_m"]}'),
      note='Solves the uniform adjusted-margin shift (vs prior-year quarter + 1H drift) so that FY26 adjusted EPS = the guidance end-point for the active scenario.')
    S('cal_eps_chk', '  Check: FY26 adjusted EPS vs guidance end-point (should be 0.00)', 'check', 'ps',
      e26=lambda: f'=ROUND({V("e_eps")}-{V("cal_eps")},2)')
    blank()

    # ------------------------------------------------------------------ disclosures
    S('b_hdr', 'Backlog, legacy product lines & other disclosures (memo; historical only)', 'block',
      note='DISCLOSURES — historical only (not forecast)')
    S('b_tot', '  Total (multi-year) backlog — Wabtec', 'line', 'm', data='seg.backlog_total', stock=True)
    S('b_12m', '  12-month backlog — Wabtec', 'line', 'm', data='seg.backlog_12m', stock=True)
    S('b_tot_g', '  Total backlog y/y %', 'growth', 'pct', hist=growth('b_tot'))
    S('b_orders', '  Implied orders = Δ total backlog + net sales (incl. FX & acquired backlog)', 'line', 'm',
      hist=lambda: ((f'=IF(AND(ISNUMBER({V("b_tot")}),ISNUMBER({PQ("b_tot")})),{V("b_tot")}-{PQ("b_tot")}+{V("is_rev")},"")') if CTX.col.q
                    else (f'=IF(AND(ISNUMBER({V("b_tot")}),ISNUMBER({P("b_tot")})),{V("b_tot")}-{P("b_tot")}+{V("is_rev")},"")' if CTX.col.prior else None)),
      note='Wabtec does not publish orders; implied from the backlog roll-forward (includes FX translation and backlog acquired).')
    S('b_btb', '  Implied book-to-bill (x)', 'line', 'x2', hist=ratio('b_orders', 'is_rev'))
    S('lp_hdr', '  Legacy product-line sales (10-K, annual; pre-2019 product categories):', 'sub', 'gen', group=True)
    for k, lab in V0['legacy_pl']:
        S(f'lp_{k}', f'    {lab}', 'memo', 'm', data=f'xl.{k}', annual_only=True, group=True)
    S('loco', '  Locomotive deliveries (units, where stated)', 'memo', 'gen', data='seg.loco_deliveries', flow=True)
    S('employees', '  Employees (year end, 10-K)', 'memo', 'm', data='extra.employees', annual_only=True)
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers & D&A', 'block', note='COST DRIVERS — inputs that drive forecast cost lines')
    S('d_dep', '  Depreciation (D&A less intangible amortization)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("is_dda")}),ISNUMBER({V("is_amort")})),{V("is_dda")}-{V("is_amort")},"")',
      fc=lambda: f'={V("is_rev")}*{V("d_dep_pct")}', note='Forecast = net sales × depreciation %.')
    S('d_dep_pct', '  Depreciation % of net sales', 'pct', 'pct', hist=ratio('d_dep', 'is_rev'),
      qe=lambda: f'=IFERROR({H1("d_dep")}/{H1("is_rev")},"")', e26=ratio('d_dep', 'is_rev'), ae_in=V0['dep_pct'])
    S('d_amort', '  Amortization of existing intangibles (schedule)', 'line', 'm', flow=True,
      qe=lambda: f'=$BX${R["is_amort"]}', ae_in=V0['amort_sched'],
      note=V0['amort_note'])
    S('d_sga', '  SG&A excl. adjusting items % of net sales', 'pct', 'pct',
      hist=lambda: f'=IF(ISNUMBER({V("is_sga")}),IFERROR({V("is_sga")}/{V("is_rev")},""),"")',
      qe=lambda: f'=IFERROR(({H1("is_sga")}-{H1("o_restr")}-{H1("o_trans")})/{H1("is_rev")},"")', e26=ratio('is_sga', 'is_rev'), ae_in=V0['sga_pct'],
      note='Historical = GAAP SG&A % (includes restructuring/transaction costs booked in SG&A). Forecast: adjusted basis (1H/26 SG&A less restructuring & transaction costs).')
    S('d_eng', '  Engineering expense % of net sales', 'pct', 'pct', hist=ratio('is_eng', 'is_rev'),
      qe=lambda: f'=IFERROR({H1("is_eng")}/{H1("is_rev")},"")', e26=ratio('is_eng', 'is_rev'), ae_in=V0['eng_pct'])
    S('d_sbc', '  Stock-based compensation % of net sales', 'pct', 'pct', hist=ratio('is_sbc', 'is_rev'),
      qe=lambda: f'=IFERROR({H1("is_sbc")}/{H1("is_rev")},"")', e26=ratio('is_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF INCOME (US GAAP)', 'section', note='CONSOLIDATED IS — forecast logic')
    S('is_rev', 'Net sales', 'total', 'm', data='is.net_sales', flow=True, fc=lambda: f'={V("g_rev")}',
      note='Forecast linked to the product-line build.')
    S('is_cogs', 'Cost of sales', 'line', 'm', data='is.cost_of_sales', flow=True,
      fc=lambda: f'={V("is_rev")}-({V("g_adjop")}+{V("is_rev")}*{V("d_sga")}+{V("is_eng")}-{V("o_inv")})',
      note='Forecast = net sales − (adjusted operating income + adjusted SG&A + engineering − inventory purchase-accounting charge): gross profit is implied by the build.')
    S('is_gp', 'Gross profit', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}-{V("is_cogs")},"")')
    S('is_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('is_sga', 'Selling, general & administrative expenses', 'line', 'm', data='is.sga', flow=True,
      fc=lambda: f'={V("is_rev")}*{V("d_sga")}+{V("o_restr")}+{V("o_trans")}',
      note='Forecast = net sales × adjusted SG&A % + restructuring & transaction costs (booked in SG&A).')
    S('is_eng', 'Engineering expenses', 'line', 'm', data='is.eng', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_eng")}')
    S('is_amort', 'Amortization expense', 'line', 'm', data='is.amort', flow=True,
      fc=lambda: f'={V("d_amort")}+N({V("m_amort")})', note='Existing-intangibles schedule + future-acquisition intangibles.')
    S('is_othop', 'Other operating items (impairments / other, where presented)', 'line', 'm', data='x.othop', flow=True, qe_in={3: 0.0, 4: 0.0}, ae_in=0.0)
    S('is_op', 'Income from operations', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_gp")}-{V("is_sga")}-{V("is_eng")}-{V("is_amort")}-N({V("is_othop")}),"")')
    S('is_opm', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('is_int', 'Interest expense, net', 'line', 'm', data='is.interest', flow=True,
      qe=lambda: f'=({PT("pt_int")}-{H1("is_int")})/2',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_fac")}*{V("ds_r_fac")}-{P("cf_end")}*{V("ds_r_cash")}',
      note='Q3/Q4-26E: FY26 interest point estimate less 1H/26, split evenly. 2027E+ = rate × opening notes + rate × opening facilities − yield × opening cash (no circularity).')
    S('is_oth', 'Other income (expense), net', 'line', 'm', data='is.other_inc', flow=True,
      qe=lambda: f'=({PT("pt_oth")}-{H1("is_oth")})/2', ae_in=V0['oth_ae'],
      note='FX, pension non-service income, equity income. Q3/Q4-26E: FY26 point estimate less 1H/26; 2027E+ input.')
    S('is_ebt', 'Income before income taxes', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_op")}),{V("is_op")}-{V("is_int")}+{V("is_oth")},"")')
    S('is_tax', 'Income tax expense', 'line', 'm', data='is.tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Q3/Q4-26E: FY26 tax-rate point estimate; 2027E+ input.')
    S('is_cont', 'Income from continuing operations', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_disc', 'Income (loss) from discontinued operations, net of tax', 'line', 'm', data='is.disc_ops', flow=True, qe_in={3: 0.0, 4: 0.0}, ae_in=0.0)
    S('is_nitot', 'Net income (incl. noncontrolling interest)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_cont")}),{V("is_cont")}+N({V("is_disc")}),"")')
    S('is_nci', '  Less: net income attributable to noncontrolling interest', 'line', 'm', data='is.nci', flow=True,
      qe=lambda: f'={H1("is_nci")}/2', ae_in=V0['nci_ae'])
    S('is_ni', 'Net income attributable to Wabtec shareholders', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_nitot")}),{V("is_nitot")}-N({V("is_nci")}),"")')
    S('is_ni_chk', '  Check: net income attributable vs reported (should be 0; ±0.5 rounding)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=0.55,0,ROUND({V("is_ni")}-{V("is_ni_pub")},1)),"")')
    S('is_ni_pub', '  Memo: net income attributable to Wabtec as reported', 'memo', 'm', data='is.ni_wab', flow=True)
    S('is_dda', '  Memo: depreciation & amortization (total)', 'memo_calc', 'm', data='x.dda', flow=True,
      fc=lambda: f'={V("d_dep")}+{V("is_amort")}', note='Historical: EBITDA reconciliation where published, otherwise cash-flow statement. Forecast = depreciation + amortization.')
    S('is_sbc', '  Memo: stock-based compensation', 'memo_calc', 'm', data='cfq.sbc', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_sbc")}')
    S('eps_hdr', '(Earnings per share)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='is.shares_basic', avg=True,
      qe=lambda: f'=$BX${R["sh_basic"]}-$CA${R["bb_sh"]}*{0.25 if CTX.col.q == 3 else 0.75}',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q3/Q4-26E: Q2/26 less the 2H/26 buyback phased in (¼ in Q3, ¾ in Q4). 2027E+: average of beginning and ending shares. Pre-June-2013 restated for the 2-for-1 split.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='is.shares_diluted', avg=True,
      qe=lambda: f'={V("sh_basic")}+($BX${R["sh_dil"]}-$BX${R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_basic', 'EPS – basic, attributable to Wabtec ($)', 'eps', 'ps', all=ratio('is_ni', 'sh_basic'))
    S('eps_dil', 'EPS – diluted, attributable to Wabtec ($)', 'eps_total', 'ps', all=ratio('is_ni', 'sh_dil'),
      note='EPS computed as net income / weighted diluted shares (may differ by ±$0.01 vs reported; participating securities).')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($; split-adjusted)', 'eps_memo', 'ps', data='is.eps_dil')
    S('dps', '  Dividends declared per share ($)', 'line', 'ps', data='is.dps', flow=True,
      qe=lambda: f'=$BX${R["dps"]}', ae=lambda: f'={P("dps")}*(1+{V("dps_g")})',
      note='Q3/Q4-26E at the current quarterly rate; 2027E+ grows with the DPS growth input.')
    S('dps_g', '  Dividend per share growth %', 'growth', 'pct', hist=growth('dps'), e26=growth('dps'), ae_in=V0['dps_g'])
    S('payout', '  Dividend payout (DPS / diluted EPS) %', 'pct', 'pct', all=ratio('dps', 'eps_dil'))
    blank()

    # ------------------------------------------------------------------ RECON 1: EBITDA
    S('sec_r1', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (company definition, as published)', 'section',
      note='ADJUSTED EBITDA — per Wabtec earnings-release reconciliation (income from operations + other income + D&A; + restructuring & transaction costs)')
    S('r_ni', 'Net income attributable to Wabtec shareholders (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('r_nci', '  (+) Net income attributable to noncontrolling interest', 'line', 'm', all=lambda: f'=N({V("is_nci")})')
    S('r_disc', '  (−) Income from discontinued operations, net of tax', 'line', 'm', all=lambda: f'=-N({V("is_disc")})')
    S('r_tax', '  (+) Income tax expense', 'line', 'm', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest expense, net', 'line', 'm', all=lambda: f'={V("is_int")}')
    S('r_opo', '  = Income from operations + other income (expense)', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_nci")}+{V("r_disc")}+{V("r_tax")}+{V("r_int")},"")')
    S('r_dda', '  (+) Depreciation & amortization', 'line', 'm', all=lambda: f'={V("is_dda")}')
    S('r_basis', '  (+/−) Basis difference vs company EBITDA (2019: other income excluded; D&A basis)', 'line', 'm', data='x.r_basis', flow=True,
      note='Historical only: published EBITDA less (income from operations + other income + D&A). 2019 definition = income from operations + D&A.')
    S('r_ebitda', '  = EBITDA', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_opo")}),ISNUMBER({V("r_dda")})),{V("r_opo")}+{V("r_dda")}+N({V("r_basis")}),"")')
    S('r_ebitda_pub', '  Memo: EBITDA as published', 'memo', 'm', data='ngaap.ebitda_pub', flow=True)
    S('r_ebitda_chk', '  Check: model EBITDA vs published (should be 0; ±1 rounding)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_ebitda_pub")}),IF(ABS({V("r_ebitda")}-{V("r_ebitda_pub")})<=1,0,ROUND({V("r_ebitda")}-{V("r_ebitda_pub")},1)),"n/p")')
    S('r_restr', '  (+) Restructuring & portfolio optimization costs', 'line', 'm', data='x.r_restr', flow=True, fc=lambda: f'={V("o_restr")}')
    S('r_inv', '  (+) Inventory purchase-accounting charge', 'line', 'm', data='x.r_inv', flow=True, fc=lambda: f'={V("o_inv")}')
    S('r_trans', '  (+) Transaction costs', 'line', 'm', data='x.r_trans', flow=True, fc=lambda: f'={V("o_trans")}')
    S('r_oth', '  (+/−) Other items / definitional differences (company bridge)', 'line', 'm', data='x.r_oth', flow=True, qe_in={3: 0.0, 4: 0.0}, ae_in=0.0)
    S('r_tot', '  Total adjusting items', 'line_b', 'm', all=lambda: f'={nsum(["r_restr", "r_inv", "r_trans", "r_oth"])}')
    S('r_adj', '  = Adjusted EBITDA (model bridge)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("r_adj_pub")}),{V("r_ebitda")}+{V("r_tot")},"")', fc=lambda: f'={V("r_ebitda")}+{V("r_tot")}',
      note='Historical shown only where Wabtec published Adjusted EBITDA (bridge rebuilt from the release reconciliation); forecast = EBITDA + forecast adjusting items (non-cash amortization is inside D&A).')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_adj_pub', '  Company-published Adjusted EBITDA', 'memo', 'm', data='ngaap.adj_ebitda_pub', flow=True)
    S('r_adj_chk', '  Check: model bridge vs company-published (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_adj_pub")}),ROUND({V("r_adj")}-{V("r_adj_pub")},0),"n/p")')
    S('r_def', '  Definition basis (company Adjusted EBITDA definition in force)', 'text', 'gen',
      note='Definition changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('r_ebit_h', 'To adjusted EBIT:', 'sub', 'gen')
    S('r_ddan', '  (−) Depreciation & amortization', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("r_dda")}),-{V("r_dda")},"")')
    S('r_ebit', '  = Adjusted EBIT (model; Adjusted EBITDA − D&A; EBITDA − D&A where no adjusted figure was published)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_ddan")}),IF(ISNUMBER({V("r_adj")}),{V("r_adj")},{V("r_ebitda")})+{V("r_ddan")},"")',
      note='Used for NOPAT / ROIC. Before 2019 Wabtec published no Adjusted EBITDA, so EBITDA (model) − D&A is used.')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: adjusted operating income
    S('sec_r2', 'RECONCILIATION: GAAP INCOME FROM OPERATIONS → ADJUSTED INCOME FROM OPERATIONS (company definition, as published)', 'section',
      note='ADJUSTED OPERATING INCOME — Wabtec "Reconciliation of Reported Results to Adjusted Results" (income-from-operations column)')
    S('o_op', 'Income from operations (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_op")}')
    S('o_restr', '  (+) Restructuring, integration & portfolio optimization costs', 'line', 'm', data='ngaap.items.restructuring', flow=True,
      qe=lambda: f'=({PT("pt_restr")}-{H1("o_restr")})/2', ae_in=V0['restr_ae'],
      note='Q3/Q4-26E: FY26 point estimate less 1H/26; 2027E+ input (Wabtec has reported restructuring every year since 2016).')
    S('o_inv', '  (+) Inventory purchase-accounting (step-up) charge', 'line', 'm', data='ngaap.items.inventory_pa', flow=True,
      qe_in=V0['qe_inv'], ae_in=0.0, note=V0['inv_note'])
    S('o_trans', '  (+) Transaction / acquisition costs', 'line', 'm', data='ngaap.items.transaction', flow=True, qe_in={3: 2.0, 4: 2.0}, ae_in=0.0)
    S('o_amort', '  (+) Non-cash amortization expense (added back where in the company definition)', 'line', 'm', data='ngaap.items.amortization', flow=True,
      fc=lambda: f'={V("is_amort")}', note='Forecast: all amortization of acquired intangibles added back (current company definition).')
    S('o_contract', '  (+) Contract adjustments / loss provisions', 'line', 'm', data='ngaap.items.contract', flow=True)
    S('o_lit', '  (+/−) Litigation, legal & settlement items', 'line', 'm', data='ngaap.items.litigation', flow=True)
    S('o_oth', '  (+/−) Other operating-level items', 'line', 'm', data='ngaap.items.other_op', flow=True, fc=lambda: f'=N({V("is_othop")})')
    S('o_tot', '  Total operating-level adjusting items', 'line_b', 'm',
      all=lambda: f'={nsum(["o_restr", "o_inv", "o_trans", "o_amort", "o_contract", "o_lit", "o_oth"])}')
    S('o_adj', '  = Adjusted income from operations (model bridge)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("o_adj_pub")}),{V("o_op")}+{V("o_tot")},"")', fc=lambda: f'={V("o_op")}+{V("o_tot")}',
      note='Historical shown where Wabtec published adjusted operating income. Forecast ties to the product-line build (check row in the Group block).')
    S('o_adj_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_adj_pub', '  Company-published adjusted income from operations', 'memo', 'm', data='ngaap.adj_op_pub', flow=True)
    S('o_chk', '  Check: model bridge vs company-published (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("o_adj_pub")}),ROUND({V("o_adj")}-{V("o_adj_pub")},0),"n/p")')
    S('o_def', '  Definition basis (company adjusted operating income definition in force)', 'text', 'gen')
    S('o_adj_g', '  Adjusted income from operations y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental adjusted operating margin (Δ adj. op. income / Δ sales)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: GAAP NET INCOME / DILUTED EPS → ADJUSTED NET INCOME → ADJUSTED DILUTED EPS (company definition, as published)', 'section',
      note='ADJUSTED EPS — company definition in force in each period (table bridges from 2016; per-share narrative bridges before)')
    S('e_ni', 'Net income attributable to Wabtec shareholders (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('e_items', '  (+) Operating-level adjusting items, pre-tax (as in the adjusted operating income bridge)', 'line', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("e_ps_in")}),"",IF(ISNUMBER({V("e_pub")}),{V("o_tot")},""))', fc=lambda: f'={V("o_tot")}')
    S('e_nonop', '  (+) Adjusting items in interest & other income, pre-tax (deal financing, FX, gains)', 'line', 'm', data='x.e_nonop', flow=True,
      qe_in={3: 0.0, 4: 0.0}, ae_in=0.0)
    S('e_tax', '  (−) Income tax effect of adjusting items', 'line', 'm', data='x.e_tax', flow=True,
      fc=lambda: f'=-({V("e_items")}+{V("e_nonop")})*{V("e_rate")}')
    S('e_disc', '  (+/−) Discrete tax items (tax reform, valuation allowances)', 'line', 'm', data='x.e_disc', flow=True, qe_in={3: 0.0, 4: 0.0}, ae_in=0.0)
    S('e_ps', '  (+/−) Items from per-share-only bridges (after tax; × diluted shares)', 'line', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("e_ps_in")}),{V("e_ps_in")}*{V("e_sh")},"")')
    S('e_adjni', '  = Adjusted net income attributable to Wabtec (model bridge)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("e_pub")}),{V("e_ni")}+{nsum(["e_items", "e_nonop", "e_tax", "e_disc", "e_ps"])},"")',
      fc=lambda: f'={V("e_ni")}+{nsum(["e_items", "e_nonop", "e_tax", "e_disc"])}',
      note='Historical shown only where Wabtec published adjusted EPS.')
    S('e_rate', '  Tax rate applied to adjustments', 'pct', 'pct',
      hist=lambda: f'=IFERROR(-{V("e_tax")}/({V("e_items")}+N({V("e_nonop")})),"")', qe=lambda: f'={PT("pt_etr")}',
      e26=lambda: f'=IFERROR(-{V("e_tax")}/({V("e_items")}+N({V("e_nonop")})),"")', ae=lambda: f'={V("is_etr")}',
      note='Historical: implied by the company table. Forecast: GAAP effective rate (adjusted tax = tax on adjusted pre-tax income).')
    S('e_sh', '  Diluted shares used in the adjusted EPS bridge (m)', 'line', 'm1', data='ngaap.adj_dil_shares', all=lambda: f'={V("sh_dil")}',
      note='Company "fully diluted shares outstanding" from the adjusted-results table where published (differs from GAAP diluted shares in loss quarters, e.g. Q1-19); otherwise weighted diluted shares.')
    S('e_eps', 'Adjusted EPS – diluted ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted diluted EPS ($; split-adjusted)', 'eps_memo', 'ps', data='ngaap.adj_eps_pub')
    S('e_chk', '  Check: model vs company-published adjusted EPS (should be 0.00; ±0.02 rounding / two-class method)', 'check', 'ps',
      hist=lambda: f'=IF(ISNUMBER({V("e_pub")}),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.025,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_ps_in', '  Input: per-share bridge items, after tax ($/share, as published; narrative bridges)', 'eps_memo', 'ps', data='x.e_ps_in')
    S('e_def', '  Definition basis (company adjusted EPS definition in force)', 'text', 'gen')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Net sales y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_org', '  Organic sales growth %', 'growth', 'pct', all=lambda: f'={V("a_org_g")}' if CTX.col.prior else None)
    S('gm_frt', '  Freight segment sales y/y %', 'growth', 'pct', all=lambda: f'={V("f_rev_g")}' if CTX.col.prior else None)
    S('gm_trn', '  Transit segment sales y/y %', 'growth', 'pct', all=lambda: f'={V("t_rev_g")}' if CTX.col.prior else None)
    S('gm_adjop', '  Adjusted income from operations y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Income from operations (GAAP) y/y %', 'growth', 'pct', all=growth('is_op'))
    S('gm_ni', '  Net income attributable y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('gm_adjm', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_inc', '  Incremental Adjusted EBITDA margin (ΔEBITDA / ΔSales)', 'pct', 'pct', all=incr('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP income from operations) %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_sga', '  SG&A % of net sales', 'pct', 'pct', all=ratio('is_sga', 'is_rev'))
    S('gm_eng', '  Engineering % of net sales', 'pct', 'pct', all=ratio('is_eng', 'is_rev'))
    blank()
