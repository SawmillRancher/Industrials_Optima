"""Row specification of the UPS Model sheet, part 1 (MLM template layout and process):
segment x product build (U.S. Domestic Package: Next Day Air / Deferred / Ground; International Package: Domestic / Export;
average daily volume x revenue per piece x operating days; Supply Chain Solutions by revenue line) -> segment non-GAAP adjusted
operating profit at the segment margin -> M&A lever -> group total & FY26 guidance calibration -> cost drivers -> income statement
-> GAAP-to-adjusted bridges -> growth & margins."""
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
def LQG(key): return f'IFERROR({LQ}{R[key]}/{LQP}{R[key]}-1,0)'   # Q3/26 y/y growth (latest actual quarter)
def WAVG(key): return f'=IFERROR(SUMPRODUCT({Q1}{R[key]}:{QE}{R[key]},{Q1}{R["days"]}:{QE}{R["days"]})/SUM({Q1}{R["days"]}:{QE}{R["days"]}),"")'


PK = [('us', 'U.S. Domestic Package', 'US', [('nda', 'Next Day Air'), ('def', 'Deferred'), ('gnd', 'Ground')]),
      ('intl', 'International Package', 'INTL', [('dom', 'Domestic'), ('exp', 'Export')])]
PKL = [f'{s}_{p}' for s, _, _, ps in PK for p, _ in ps]            # package products
SCSL = ['scs_fl', 'scs_oth']                                       # Supply Chain Solutions lines that are forecast
SEGK = ['us', 'intl', 'scs']
CODE = {'us': 'US', 'intl': 'INTL', 'scs': 'SCS'}

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block: Mid = the company\'s FY26 point guidance; High / Low = model assumptions around it.'))
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
    S('sec_seg', 'SEGMENT P&L — U.S. DOMESTIC PACKAGE · INTERNATIONAL PACKAGE · SUPPLY CHAIN SOLUTIONS (average daily volume × revenue per piece × operating days)', 'section',
      note='SEGMENT BUILD — modelling logic (average daily package volume × revenue per piece × operating days → product revenue → segment revenue → non-GAAP adjusted operating profit at the segment margin → GAAP P&L)')
    blank()
    S('days_h', 'Operating calendar', 'block', note='OPERATING DAYS — company-published operating days ("operating weekdays" to 2018) per period')
    S('days', '  Operating days in period', 'line', 'm', data='o_days', flow=True, qe_in=V0['days_q4'], ae_in=V0['days_ae'],
      note='Published in every release / 10-Q. Q4/26E and 2027E+: inputs (assumption: Q4/26 as Q4/25; 254 days a year).')
    blank()
    descr = {'us': 'U.S. Domestic Package (time-definite small-package delivery in the United States: air — Next Day Air, Deferred — and Ground)',
             'intl': 'International Package (small-package delivery outside the United States — Domestic — and cross-border Export; Europe, Asia, Americas, ISMEA)'}
    for s, title, code, prods in PK:
        S(f'{s}_hdr', descr[s], 'block', note=f'{title.upper()} — modelling logic')
        for i, (p, pl) in enumerate(prods):
            k = f'{s}_{p}'
            S(k + '_adv', f'  {pl} — average daily package volume (000)', 'line', 'm', data=f'o_adv_{s}_{p}', avg=True,
              qe=lambda k=k: f'={P(k + "_adv")}*(1+{V(k + "_adv_g")})', ae=lambda k=k: f'={P(k + "_adv")}*(1+{V(k + "_adv_g")})', e26=lambda k=k: WAVG(k + '_adv'),
              note=('Average daily package volume as published (thousands). Q4/26E: prior-year quarter × (1 + growth); 2026E = day-weighted average of the quarters; '
                    '2027E+: prior year × (1 + scenario lever).') if i == 0 else None)
            S(k + '_adv_g', '    y/y %', 'growth', 'pct', all=growth(k + '_adv'),
              qe=lambda k=k: f'={V(k + "_adv_pre")}+{QEa("cal_g")}', ae=lambda code=code: '=' + CH(SC[f'{code}_ADV'][CTX.col.year]),
              note='Q4/26E: Q3/26 y/y growth of the product + revenue-guidance calibration Δ (Group block). 2027E–2030E: scenario lever (Bull/Base/Bear table →).' if i == 0 else None)
            S(k + '_adv_pre', '    Q4/26E volume growth before revenue calibration (Q3/26 y/y)', 'driver', 'pct', qe=lambda k=k: '=' + LQG(k + '_adv'))
            S(k + '_rpp', f'  {pl} — average revenue per piece ($)', 'line', 'ps', data=f'o_rpp_{s}_{p}',
              qe=lambda k=k: f'={P(k + "_rpp")}*(1+{V(k + "_rpp_g")})', ae=lambda k=k: f'={P(k + "_rpp")}*(1+{V(k + "_rpp_g")})',
              e26=lambda k=k: f'=IFERROR({V(k)}/({V(k + "_adv")}*{V("days")})*1000,"")',
              note='Average revenue per piece as published ($; includes fuel and other surcharges). Q4/26E: prior-year quarter × (1 + Q3/26 y/y); 2027E+: scenario lever.' if i == 0 else None)
            S(k + '_rpp_g', '    y/y %', 'growth', 'pct', all=growth(k + '_rpp'), qe=lambda k=k: '=' + LQG(k + '_rpp'),
              ae=lambda code=code: '=' + CH(SC[f'{code}_RPP'][CTX.col.year]))
            S(k, f'  {pl} — revenue', 'line', 'm', data=f'o_rev_{s}_{p}', flow=True,
              qe=lambda k=k: f'={V(k + "_adv")}*{V(k + "_rpp")}*{V("days")}/1000', ae=lambda k=k: f'={V(k + "_adv")}*{V(k + "_rpp")}*{V("days")}/1000',
              note='Product revenue as published (Selected Operating Data). Forecast = average daily volume (000) × revenue per piece × operating days ÷ 1,000.' if i == 0 else None)
        ck = f'{s}_cargo'
        S(ck, '  Cargo and Other — revenue' if s == 'us' else '  Cargo and Other — revenue ("Cargo" to 2017)', 'line', 'm', data=f'o_rev_{s}_cargo', flow=True,
          qe=lambda ck=ck: f'={P(ck)}*(1+{LQG(ck)})', ae=lambda ck=ck, code=code: f'={P(ck)}*(1+{CH(SC[code + "_ADV"][CTX.col.year])}+{CH(SC[code + "_RPP"][CTX.col.year])})',
          note=('U.S. Domestic "Cargo and Other" (air cargo, incl. USPS air cargo volumes) is presented from the Q4-2024 release (2024 recast; within Supply Chain Solutions before). '
                if s == 'us' else '') + 'Q4/26E: prior-year quarter × (1 + Q3/26 y/y). 2027E+: prior year × (1 + segment volume lever + revenue-per-piece lever).')
        allp = [f'{s}_{p}' for p, _ in prods]
        S(f'{s}_rev', f'  {title} — segment revenue', 'line_b', 'm', data=f'rev_{s}', flow=True,
          fc=lambda allp=allp, ck=ck: '=' + '+'.join(V(k) for k in allp) + f'+{V(ck)}',
          note='History: segment revenue as reported (Selected Financial Data). Forecast: Σ products + cargo and other.' if s == 'us' else None)
        S(f'{s}_rev_g', '  Segment revenue y/y %', 'growth', 'pct', all=growth(f'{s}_rev'))
        S(f'{s}_mix', '  % of consolidated revenue', 'pct', 'pct', all=ratio(f'{s}_rev', 'g_rev'))
        S(f'{s}_chk', '  Check: products + cargo vs segment revenue (should be 0; ±1 rounding)', 'check', 'm',
          hist=lambda allp=allp, ck=ck, s=s: (f'=IF(ISNUMBER({V(allp[0])}),IF(ABS({"+".join(V(k) for k in allp)}+N({V(ck)})-{V(s + "_rev")})<=1.5,0,'
                                           f'ROUND({"+".join(V(k) for k in allp)}+N({V(ck)})-{V(s + "_rev")},0)),"")'))
        S(f'{s}_adv', f'  {title} — total average daily package volume (000)', 'line_b', 'm', data=f'o_adv_{s}', avg=True,
          qe=lambda allp=allp: '=' + '+'.join(V(k + '_adv') for k in allp), ae=lambda allp=allp: '=' + '+'.join(V(k + '_adv') for k in allp),
          e26=lambda allp=allp: '=' + '+'.join(V(k + '_adv') for k in allp))
        S(f'{s}_adv_g', '  Total average daily volume y/y %', 'growth', 'pct', all=growth(f'{s}_adv'))
        S(f'{s}_rpp', f'  {title} — total average revenue per piece ($)', 'line_b', 'ps', data=f'o_rpp_{s}',
          fc=lambda allp=allp, s=s: f'=IFERROR(({"+".join(V(k) for k in allp)})/({V(s + "_adv")}*{V("days")})*1000,"")')
        S(f'{s}_rpp_g', '  Total revenue per piece y/y %', 'growth', 'pct', all=growth(f'{s}_rpp'))
        S(f'{s}_tie', '  Product revenue ÷ (average daily volume × revenue per piece × operating days) — tie of the published statistics to revenue (≈ 1.000)', 'memo_calc', 'x2',
          hist=lambda allp=allp, s=s: (f'=IF(AND(ISNUMBER({V(s + "_adv")}),ISNUMBER({V(s + "_rpp")}),ISNUMBER({V("days")})),'
                                       f'IFERROR(({"+".join(V(k) for k in allp)})/({V(s + "_adv")}*{V(s + "_rpp")}*{V("days")}/1000),""),"")'),
          note='Statistics are rounded as published (volume to the thousand, revenue per piece to the cent); the forecast uses a ratio of 1.' if s == 'us' else None)
        S(f'{s}_oi', f'  {title} — non-GAAP adjusted operating profit', 'line', 'm', data=f'aop_{s}', flow=True,
          qe=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}', ae=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}',
          note=('Segment operating profit on the company\'s non-GAAP adjusted basis (published in periods with adjusting items; otherwise = GAAP segment operating profit). '
                'Forecast = segment revenue × adjusted operating margin.') if s == 'us' else None)
        S(f'{s}_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio(f'{s}_oi', f'{s}_rev'),
          qe=lambda s=s: f'={V(s + "_m_pre")}+{QEa("cal_m")}', ae=lambda code=code: '=' + CH(SC[f'{code}_M'][CTX.col.year]),
          note='Q4/26E: margin before calibration + adjusted-operating-profit-guidance calibration Δ (Group block). 2027E+: scenario lever.' if s == 'us' else None)
        S(f'{s}_m_pre', '  Q4/26E margin before calibration (prior-year quarter + Q3/26 y/y change)', 'driver', 'pct',
          qe=lambda s=s: f'={P(s + "_m")}+({LQ}{R[s + "_m"]}-{LQP}{R[s + "_m"]})')
        S(f'{s}_inc', '  Incremental adjusted operating margin (Δ profit / Δ revenue)', 'pct', 'pct', all=incr(f'{s}_oi', f'{s}_rev'))
        S(f'{s}_gaap', f'  {title} — operating profit (GAAP)', 'line', 'm', data=f'op_{s}', flow=True, fc=lambda s=s: f'={V(s + "_oi")}-{V("d_" + s)}',
          note='As reported. Forecast = adjusted operating profit − adjusting items of the segment.' if s == 'us' else None)
        S(f'{s}_cpp', '  Adjusted cost per piece — model: (segment revenue − adjusted operating profit) ÷ packages ($)', 'memo_calc', 'ps',
          all=lambda s=s: f'=IF(AND(ISNUMBER({V(s + "_adv")}),ISNUMBER({V(s + "_oi")})),IFERROR(({V(s + "_rev")}-{V(s + "_oi")})/({V(s + "_adv")}*{V("days")})*1000,""),"")',
          note='Model measure on total segment cost; the company\'s published U.S. cost per piece excludes cargo and other expense.' if s == 'us' else None)
        blank()
    # ---- Supply Chain Solutions
    S('scs_hdr', 'Supply Chain Solutions ("Supply Chain & Freight" to Q1-2021: Forwarding, Logistics (incl. healthcare), UPS Freight to 30-Apr-2021, Coyote to 16-Sep-2024, other)', 'block',
      note='SUPPLY CHAIN SOLUTIONS — modelling logic (revenue lines × growth; adjusted operating margin)')
    S('scs_fl', '  Forwarding and Logistics — revenue', 'line', 'm', data='o_rev_scs_fl', flow=True,
      qe=lambda: f'={P("scs_fl")}*(1+{V("scs_fl_g")})', ae=lambda: f'={P("scs_fl")}*(1+{V("scs_fl_g")})',
      note='One line to Q3-2018; Forwarding and Logistics are published separately from the Q4-2018 release (memo rows; summed here). Forecast: prior period × (1 + growth).')
    S('scs_fl_g', '    y/y %', 'growth', 'pct', all=growth('scs_fl'), qe=lambda: f'={V("scs_fl_pre")}+{QEa("cal_g")}', ae=lambda: '=' + CH(SC['SCS_G'][CTX.col.year]))
    S('scs_fl_pre', '    Q4/26E growth before revenue calibration (Q3/26 y/y)', 'driver', 'pct', qe=lambda: '=' + LQG('scs_fl'))
    S('scs_fwd', '    Memo: Forwarding (from Q4-2018)', 'memo', 'm', data='o_rev_scs_fwd', flow=True)
    S('scs_log', '    Memo: Logistics (from Q4-2018)', 'memo', 'm', data='o_rev_scs_log', flow=True)
    S('scs_frt', '  Freight (UPS Freight, LTL) — revenue (sold 30-Apr-2021)', 'line', 'm', data='o_rev_scs_frt', flow=True, fc=lambda: '=0')
    S('scs_oth', '  Other — revenue', 'line', 'm', data='o_rev_scs_oth', flow=True,
      qe=lambda: f'={P("scs_oth")}*(1+{V("scs_oth_g")})', ae=lambda: f'={P("scs_oth")}*(1+{V("scs_oth_g")})')
    S('scs_oth_g', '    y/y %', 'growth', 'pct', all=growth('scs_oth'), qe=lambda: f'={V("scs_oth_pre")}+{QEa("cal_g")}', ae=lambda: '=' + CH(SC['SCS_G'][CTX.col.year]))
    S('scs_oth_pre', '    Q4/26E growth before revenue calibration (Q3/26 y/y)', 'driver', 'pct', qe=lambda: '=' + LQG('scs_oth'))
    S('scs_rev', '  Supply Chain Solutions — segment revenue', 'line_b', 'm', data='rev_scs', flow=True, fc=lambda: f'={V("scs_fl")}+{V("scs_frt")}+{V("scs_oth")}')
    S('scs_rev_g', '  Segment revenue y/y %', 'growth', 'pct', all=growth('scs_rev'))
    S('scs_mix', '  % of consolidated revenue', 'pct', 'pct', all=ratio('scs_rev', 'g_rev'))
    S('scs_chk', '  Check: revenue lines vs segment revenue (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: (f'=IF(ISNUMBER({V("scs_fl")}),IF(ABS({V("scs_fl")}+N({V("scs_frt")})+N({V("scs_oth")})-{V("scs_rev")})<=1.5,0,'
                    f'ROUND({V("scs_fl")}+N({V("scs_frt")})+N({V("scs_oth")})-{V("scs_rev")},0)),"")'))
    S('scs_oi', '  Supply Chain Solutions — non-GAAP adjusted operating profit', 'line', 'm', data='aop_scs', flow=True,
      qe=lambda: f'={V("scs_rev")}*{V("scs_m")}', ae=lambda: f'={V("scs_rev")}*{V("scs_m")}')
    S('scs_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('scs_oi', 'scs_rev'),
      qe=lambda: f'={V("scs_m_pre")}+{QEa("cal_m")}', ae=lambda: '=' + CH(SC['SCS_M'][CTX.col.year]))
    S('scs_m_pre', '  Q4/26E margin before calibration (Q3/26 adjusted margin)', 'driver', 'pct', qe=lambda: f'={LQ}{R["scs_m"]}',
      note='Q3/25 included a $330m sale-leaseback gain in Supply Chain Solutions (not adjusted out by the company), so the Q3/26 margin is used instead of the prior-year quarter + drift.')
    S('scs_inc', '  Incremental adjusted operating margin (Δ profit / Δ revenue)', 'pct', 'pct', all=incr('scs_oi', 'scs_rev'))
    S('scs_gaap', '  Supply Chain Solutions — operating profit (GAAP)', 'line', 'm', data='op_scs', flow=True, fc=lambda: f'={V("scs_oi")}-{V("d_scs")}')
    blank()
    S('mx_hdr', 'Consolidated package statistics and contribution to growth (outputs)', 'block', note='MIX — outputs')
    S('g_adv', '  Consolidated average daily package volume (000)', 'line', 'm', data='o_adv_tot', avg=True,
      hist=lambda: f'=IF(ISNUMBER({V("us_adv")}),{V("us_adv")}+{V("intl_adv")},"")', fc=lambda: f'={V("us_adv")}+{V("intl_adv")}',
      note='As published; Q3/26 (no release schedule) = U.S. Domestic + International.')
    S('g_adv_g', '  Consolidated average daily volume y/y %', 'growth', 'pct', all=growth('g_adv'))
    S('g_rpp', '  Consolidated average revenue per piece ($)', 'line', 'ps', data='o_rpp_tot',
      hist=lambda: f'=IFERROR(({"+".join(V(k) for k in PKL)})/({V("g_adv")}*{V("days")})*1000,"")',
      fc=lambda: f'=IFERROR(({"+".join(V(k) for k in PKL)})/({V("g_adv")}*{V("days")})*1000,"")')
    S('g_rpp_g', '  Consolidated revenue per piece y/y %', 'growth', 'pct', all=growth('g_rpp'))
    S('g_vol', '  Consolidated package volume (millions)', 'line', 'm', data='o_vol', flow=True, hist=lambda: f'=IFERROR({V("g_adv")}*{V("days")}/1000,"")',
      qe=lambda: f'={V("g_adv")}*{V("days")}/1000', ae=lambda: f'={V("g_adv")}*{V("days")}/1000')
    for s, lab in (('us', 'U.S. Domestic Package'), ('intl', 'International Package'), ('scs', 'Supply Chain Solutions')):
        S(f'gc_{s}', f'  Contribution to consolidated revenue growth — {lab} (pp)', 'growth', 'pct',
          all=lambda s=s: (f'=IFERROR(({V(s + "_rev")}-{P(s + "_rev")})/{P("g_rev")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — healthcare logistics / Supply Chain Solutions bolt-ons, unallocated; deals closed from 2027E)', 'block',
      note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=3.0, e26_in=0.0,
      note='Assumption. 2025 acquisitions cost $1,968m net of cash (Andlauer Healthcare Group, Frigo-Trans / BPL); target revenue is not disclosed in the filings used.')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.05)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}',
      note='Mid-year convention.')
    S('m_m', '  Operating margin of acquired businesses (after amortization) %', 'driver', 'pct', e26_in=0.0, ae_in=0.10, note='Assumption (in line with the Supply Chain Solutions adjusted margin).')
    S('m_oi', '  Operating profit from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.15, note='Assumption.')
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.35, note='Assumption.')
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=15)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (inside operating profit)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)',
      note='UPS does not adjust out amortization; the acquired-business margin above is after amortization.')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group Total — revenue & non-GAAP adjusted operating profit (segment build) → FY26 guidance calibration', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Revenue (segment build)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("us_rev")}),{V("us_rev")}+{V("intl_rev")}+{V("scs_rev")},"")',
      fc=lambda: f'={V("us_rev")}+{V("intl_rev")}+{V("scs_rev")}+N({V("m_rev")})', note='Σ segment revenue (+ future acquisitions from 2027E).')
    S('g_rev_g', '  Revenue y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs consolidated revenue (should be 0; ±1 rounding)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=1.5,0,ROUND({V("g_rev")}-{V("is_rev")},0)),"")')
    S('g_adj', 'Non-GAAP adjusted operating profit (segment build)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("us_oi")}),{V("us_oi")}+{V("intl_oi")}+{V("scs_oi")}+N({V("m_oi")}),"")',
      note='Σ segment adjusted operating profit (+ future acquisitions). Company non-GAAP adjusted measure; drives the GAAP P&L below.')
    S('g_adjm', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('g_adj', 'is_rev'))
    S('g_adj_g', '  Adjusted operating profit y/y %', 'growth', 'pct', all=growth('g_adj'))
    S('g_chk_adj', '  Check: segment build vs adjusted operating profit bridge (should be 0; ±1 rounding)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_adj")}),ISNUMBER({V("o_adj")})),IF(ABS({V("g_adj")}-{V("o_adj")})<=1.5,0,ROUND({V("g_adj")}-{V("o_adj")},0)),"")')
    S('cal_guid', '  Memo: FY26 consolidated revenue guidance (scenario end-point)', 'memo', 'm', e26=lambda: '=' + CH(SC['out_rev']), note=V0['rev_guid_note'])
    S('cal_pre', '  Revenue before calibration (Q4/26E helper)', 'line', 'm',
      qe=lambda: '=' + '+'.join(f'{P(k + "_adv")}*(1+{V(k + "_adv_pre")})*{V(k + "_rpp")}*{V("days")}/1000' for k in PKL)
      + f'+{V("us_cargo")}+{V("intl_cargo")}+' + '+'.join(f'{P(k)}*(1+{V(k + "_pre")})' for k in SCSL))
    S('cal_sens', '  Revenue sensitivity to +1.00 of volume / revenue-line growth (Q4/26E helper)', 'line', 'm',
      qe=lambda: '=' + '+'.join(f'{P(k + "_adv")}*{V(k + "_rpp")}*{V("days")}/1000' for k in PKL) + '+' + '+'.join(P(k) for k in SCSL))
    S('cal_g', '  Guidance calibration: Δ y/y growth applied to package volumes and Supply Chain Solutions revenue lines (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_guid", E26)}-{ACT("g_rev")}-{V("cal_pre")})/{V("cal_sens")}',
      note='Solves the uniform growth shift (vs Q3/26 y/y rates) so that FY26 revenue = the guidance end-point for the active scenario (closed form, no circularity).')
    S('cal_rev_chk', '  Check: FY26 revenue vs guidance end-point (should be 0)', 'check', 'm', e26=lambda: f'=ROUND({V("g_rev")}-{V("cal_guid")},1)')
    S('cal_op', '  Memo: FY26 non-GAAP adjusted operating profit guidance (scenario end-point)', 'memo', 'm', e26=lambda: '=' + CH(SC['out_op']), note=V0['op_guid_note'])
    S('cal_oi', '  Q4/26E adjusted operating profit required (FY guidance end-point − 9M actual)', 'memo_calc', 'm', e26=lambda: f'={V("cal_op")}-{ACT("g_adj")}')
    S('cal_oi_pre', '  Adjusted operating profit before margin calibration (Q4/26E helper)', 'line', 'm',
      qe=lambda: '=' + '+'.join(f'{V(s + "_rev")}*{V(s + "_m_pre")}' for s in SEGK))
    S('cal_segrev', '  Segment revenue (Q4/26E helper)', 'line', 'm', qe=lambda: '=' + '+'.join(V(s + '_rev') for s in SEGK))
    S('cal_m', '  Guidance calibration: Δ adjusted operating margin applied to all segments (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_oi", E26)}-{V("cal_oi_pre")})/{V("cal_segrev")}',
      note='Solves the uniform segment-margin shift so that FY26 non-GAAP adjusted operating profit = the guidance end-point for the active scenario.')
    S('cal_op_chk', '  Check: FY26 adjusted operating profit vs guidance end-point (should be 0)', 'check', 'm', e26=lambda: f'=ROUND({V("g_adj")}-{V("cal_op")},1)')
    S('cal_q4r', '  Memo: Q4/26 revenue guidance ~$25.7bn (information) — model Q4/26E less guidance', 'memo_calc', 'm', e26=lambda: f'={QEc("g_rev")}-{PT("pt_q4rev")}',
      note='The FY and Q4 guidance points are rounded ("approximately"); the model is solved to the FY point, so small differences to the Q4 point are expected.')
    S('cal_q4o', '  Memo: Q4/26 adjusted operating profit guidance ~$3.3bn (information) — model Q4/26E less guidance', 'memo_calc', 'm', e26=lambda: f'={QEc("g_adj")}-{PT("pt_q4op")}')
    S('cal_eps', '  Memo: FY26 non-GAAP adjusted diluted EPS guidance ~$7.28 (information, not forced)', 'eps_memo', 'ps', e26=lambda: f'={PT("pt_eps")}')
    S('cal_eps_d', '    Model FY26 adjusted EPS − guidance ($)', 'eps_memo', 'ps', e26=lambda: f'={V("e_eps")}-{V("cal_eps")}')
    S('cal_fcf', '  Memo: FY26 non-GAAP adjusted free cash flow guidance ~$6.1bn (information, not forced)', 'memo', 'm', e26=lambda: f'={PT("pt_fcf")}',
      note='The company\'s "adjusted" free cash flow guidance definition is not reconciled in the release; the model row is free cash flow on the published definition.')
    S('cal_fcf_d', '    Model FY26 free cash flow − guidance', 'memo_calc', 'm', e26=lambda: f'={V("fcf")}-{V("cal_fcf")}')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A & adjusting items', 'block', note='COST DRIVERS — inputs that drive forecast cost lines (Q4/26E: point estimates / 9M ratios; 2027E+: % of revenue or inputs)')
    S('d_da', '  Depreciation & amortization (total)', 'line', 'm', data='x_da', flow=True, qe=lambda: f'={PT("pt_da")}', ae=lambda: f'={V("is_rev")}*{V("d_da_pct")}+N({V("m_amort")})',
      note='Income-statement line. Q4/26E point estimate; 2027E+: % of revenue (+ amortization of future acquisitions).')
    S('d_da_pct', '  D&A % of revenue', 'pct', 'pct', all=ratio('d_da', 'is_rev'), ae_in=V0['da_pct'], note='9M 2026 4.4% (building closures shorten useful lives; software amortization; AHG). Input.')
    S('d_amort', '  of which amortization of intangible assets (annual; 10-K)', 'line', 'm', data='amort', flow=True, e26_in=V0['amort_26'], ae_in=V0['amort_ae'],
      note='Annual history from the 10-K (XBRL AmortizationOfIntangibleAssets, as first filed); not published quarterly. Forecast input (assumption: FY2025 level rising with capitalized software). Splits D&A between PP&E and intangibles on the balance sheet only.')
    for k, lab, dk in (('d_rm', 'Repairs and maintenance', 'is_rm'), ('d_pt', 'Purchased transportation', 'is_pt'), ('d_fuel', 'Fuel', 'is_fuel'),
                       ('d_occ', 'Other occupancy', 'is_occ'), ('d_othx', 'Other expenses', 'is_othx')):
        S(k, f'  {lab} % of revenue', 'pct', 'pct', all=ratio(dk, 'is_rev'), qe=lambda dk=dk: f'=IFERROR({ACT(dk)}/{ACT("is_rev")},"")', ae=lambda k=k: f'={P(k)}',
          note='Q4/26E: 9M 2026 ratio; 2027E+: held at the prior-year ratio. Presentation only — compensation and benefits is the balancing line to GAAP operating profit.' if k == 'd_rm' else None)
    S('d_comp', '  Compensation and benefits % of revenue (balancing line in the forecast)', 'pct', 'pct', all=ratio('is_comp', 'is_rev'))
    S('d_sbc', '  Stock compensation expense (cash-flow statement)', 'line', 'm', data='cf_sbc', flow=True, qe=lambda: f'={PT("pt_sbc")}', ae_in=V0['sbc_ae'],
      note='Cash-flow statement (not adjusted out by UPS). Q4/26E point estimate; 2027E+ input.')
    S('d_othinc', '  Other income: other pension income (expense) + investment income (expense) and other — forecast input', 'line', 'm', qe=lambda: f'={PT("pt_othinc")}', ae_in=V0['othinc'],
      note='9M 2026 $342m (other pension income ~$65m a quarter + investment income). Excludes any year-end pension mark-to-market (not forecast). Input (assumption).')
    S('d_adj_h', '  Adjusting items (pre-tax, excluded from the company\'s non-GAAP adjusted measures; added back):', 'sub', 'gen')
    S('d_us', '  U.S. Domestic Package — adjusting items in operating profit (transformation strategy costs, pension, impairments, other)', 'line', 'm', data='oa_us', flow=True,
      qe=lambda: f'={PT("pt_transf")}', ae_in=V0['ae_transf'], note=V0['transf_note'])
    S('d_intl', '  International Package — adjusting items in operating profit', 'line', 'm', data='oa_intl', flow=True, fc=lambda: '=0')
    S('d_scs', '  Supply Chain Solutions — adjusting items in operating profit', 'line', 'm', data='oa_scs', flow=True, fc=lambda: '=0')
    S('d_nonop', '  Adjusting items below operating profit (pension mark-to-market and curtailment from 2018; investment write-downs)', 'line', 'm', data='oa_nonop', flow=True, fc=lambda: '=0',
      note='From Q1-2018 (ASU 2017-07) non-service pension cost, incl. the year-end mark-to-market outside the 10% corridor, sits in other income; before 2018 it was inside operating profit (segment rows above). Not forecast.')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'STATEMENTS OF CONSOLIDATED INCOME (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (operating profit = adjusted operating profit − adjusting items; compensation and benefits is the balancing expense line)')
    S('is_rev', 'Revenue', 'total', 'm', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the segment build.')
    S('is_comp', 'Compensation and benefits', 'line', 'm', data='x_comp', flow=True,
      fc=lambda: f'={V("is_rev")}-{V("is_ebit")}-{V("is_rm")}-{V("is_da")}-{V("is_pt")}-{V("is_fuel")}-{V("is_occ")}-{V("is_othx")}',
      note='Forecast = revenue − operating profit − other expense lines (implied by the adjusted operating profit build).')
    S('is_rm', 'Repairs and maintenance', 'line', 'm', data='x_rm', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_rm")}')
    S('is_da', 'Depreciation and amortization', 'line', 'm', data='x_da', flow=True, fc=lambda: f'={V("d_da")}')
    S('is_pt', 'Purchased transportation', 'line', 'm', data='x_pt', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_pt")}')
    S('is_fuel', 'Fuel', 'line', 'm', data='x_fuel', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_fuel")}')
    S('is_occ', 'Other occupancy', 'line', 'm', data='x_occ', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_occ")}')
    S('is_othx', 'Other expenses', 'line', 'm', data='x_othx', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_othx")}')
    S('is_opex', 'Total operating expenses', 'line_b', 'm', data='opex', flow=True, fc=lambda: f'=SUM({V("is_comp")}:{V("is_othx")})')
    S('is_opex_chk', '  Check: expense lines vs total operating expenses (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("is_comp")}),ISNUMBER({V("is_othx")})),IF(ABS(SUM({V("is_comp")}:{V("is_othx")})-{V("is_opex")})<=1.5,0,ROUND(SUM({V("is_comp")}:{V("is_othx")})-{V("is_opex")},0)),"")')
    S('is_ebit', 'Operating profit', 'total', 'm', hist=lambda: f'=IF(ISNUMBER({V("is_opex")}),{V("is_rev")}-{V("is_opex")},"")', fc=lambda: f'={V("g_adj")}-{V("o_tot")}',
      note='Forecast = non-GAAP adjusted operating profit − adjusting items in operating profit.')
    S('is_ebit_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_ebit', 'is_rev'))
    S('is_othinc', 'Other pension income (expense) and investment income (expense) and other', 'line', 'm', data='oth_inc', flow=True, fc=lambda: f'={V("d_othinc")}-{V("d_nonop")}',
      note='Two lines in the releases from Q1-2018 (other pension income (expense); investment income and other), summed here; the 10-Q face statement shows one line.')
    S('is_pen', '  Memo: of which other pension income (expense) (from Q1-2018; incl. year-end mark-to-market)', 'memo', 'm', data='pen_inc', flow=True)
    S('is_int', 'Interest expense', 'line', 'm', data='int_exp', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_rev")}*{V("ds_r_rev")}',
      note='Q4/26E point estimate. 2027E+ = rate × opening notes, leases & other debt + rate × opening commercial paper (no circularity).')
    S('is_ebt', 'Income before income taxes', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ebit")}),{V("is_ebit")}+{V("is_othinc")}-{V("is_int")},"")')
    S('is_tax', 'Income tax expense', 'line', 'm', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Q4/26E: FY26 guidance ~23%. 2027E+: input.')
    S('is_ni', 'Net income', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_ni_chk', '  Check: net income vs reported (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=1.5,0,ROUND({V("is_ni")}-{V("is_ni_pub")},0)),"")')
    S('is_ni_pub', '  Memo: net income as reported', 'memo', 'm', data='ni', flow=True)
    S('is_dda', '  Memo: depreciation & amortization (total)', 'memo_calc', 'm', all=lambda: f'={V("d_da")}')
    S('is_sbc', '  Memo: stock compensation expense', 'memo_calc', 'm', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share — class A and class B common stock; same per-share amounts)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm', data='sh_b', avg=True,
      qe=lambda: f'={B1("bs_shares")}-${E26}${R["bb_sh"]}*0.5+${E26}${R["bb_iss"]}*0.5',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q4/26E: class A + class B shares issued at 30-Sep-2026 − Q4 buybacks (mid-quarter) + equity-plan issuance. 2027E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")',
      note='Net income / weighted diluted shares (shares published in whole millions; ±$0.01 vs reported).')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.0111,0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('dps', '  Dividends declared per share ($)', 'line', 'ps', data='dps', flow=True, qe_in=V0['dps_q'],
      ae=lambda: f'={P("dps")}*(1+{V("dps_g")})', note='Quarterly dividend $1.64 (2025 and 2026). 2027E+: prior year × (1 + growth).')
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'])
    blank()

    # ------------------------------------------------------------------ RECON 1: operating profit -> adjusted operating profit
    S('sec_r1', 'RECONCILIATION: OPERATING PROFIT → NON-GAAP ADJUSTED OPERATING PROFIT (company definition in force in each period)', 'section',
      note='ADJUSTED OPERATING PROFIT — per the release schedules ("as adjusted" data to 2018; "Reconciliation of GAAP and Non-GAAP Adjusted Measures" after); the company\'s item wording per period is in the cell comments of the total row')
    S('o_op', 'Operating profit (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ebit")}')
    for k, lab, d in (('o_us', '  (+) Adjusting items — U.S. Domestic Package', 'd_us'), ('o_intl', '  (+) Adjusting items — International Package', 'd_intl'),
                      ('o_scs', '  (+) Adjusting items — Supply Chain Solutions', 'd_scs')):
        S(k, lab, 'line', 'm', all=lambda d=d: f'={V(d)}')
    S('o_tot', '  Total adjusting items in operating profit (pre-tax)', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_us")}),{nsum(["o_us", "o_intl", "o_scs"])},"")')
    S('o_adj', '  = Non-GAAP adjusted operating profit (model bridge)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_tot")},"")',
      note='GAAP operating profit + the adjusting items of each segment (= published adjusted segment operating profit − GAAP segment operating profit). Forecast = GAAP + forecast items (equals the segment build — check in the Group block).')
    S('o_adj_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company-published non-GAAP adjusted operating profit', 'memo', 'm', data='aop_pub', flow=True)
    S('o_chk', '  Check: model bridge vs company-published (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),IF(ABS({V("o_adj")}-{V("o_pub")})<=1.5,0,ROUND({V("o_adj")}-{V("o_pub")},0)),"n/p")')
    S('o_def', '  Definition / basis (company adjusted definition in force)', 'text', 'gen',
      note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('o_adj_g', '  Adjusted operating profit y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental adjusted operating margin (Δ adjusted operating profit / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: net income -> EBITDA -> adjusted EBITDA (model definition)
    S('sec_r2', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (model definition — UPS publishes adjusted EBITDA only on a trailing basis in its debt-leverage reconciliation)', 'section',
      note='EBITDA — model definition: net income + income taxes + interest expense − other pension / investment income = operating profit; + D&A = EBITDA; + adjusting items in operating profit = adjusted EBITDA (= adjusted operating profit + D&A)')
    S('r_ni', 'Net income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('r_tax', '  (+) Income tax expense', 'line', 'm', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest expense', 'line', 'm', all=lambda: f'={V("is_int")}')
    S('r_oth', '  (−) Other pension income (expense) and investment income and other', 'line', 'm', all=lambda: f'=-{V("is_othinc")}')
    S('r_gebit', '  = Operating profit', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_tax")}+{V("r_int")}+{V("r_oth")},"")')
    S('r_gebit_chk', '  Check: bridge vs income-statement operating profit (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("r_gebit")}),IF(ABS({V("r_gebit")}-{V("is_ebit")})<=1.5,0,ROUND({V("r_gebit")}-{V("is_ebit")},0)),"")')
    S('r_da', '  (+) Depreciation and amortization', 'line', 'm', all=lambda: f'={V("d_da")}')
    S('r_ebitda', '  = EBITDA (model)', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_gebit")}),ISNUMBER({V("r_da")})),{V("r_gebit")}+{V("r_da")},"")')
    S('r_adjx', '  (+) Adjusting items in operating profit', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("o_tot")}),{V("o_tot")},"")')
    S('r_adj', '  = Adjusted EBITDA (model)', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda")}),ISNUMBER({V("r_adjx")})),{V("r_ebitda")}+{V("r_adjx")},"")',
      note='Model definition = non-GAAP adjusted operating profit + D&A (stock compensation is not added back). Used for leverage (net debt / adjusted EBITDA) and EV / EBITDA. '
           'The company\'s own trailing "adjusted EBITDA" (debt-leverage reconciliation) also adjusts for pension items and is not rebuilt here.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_def', '  Definition / basis', 'text', 'gen')
    S('r_ebit_h', 'To adjusted EBIT (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ddan', '  (−) Depreciation & amortization (total)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("d_da")}),-{V("d_da")},"")')
    S('r_ebit', '  = Adjusted EBIT (adjusted EBITDA − total D&A; = non-GAAP adjusted operating profit)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+{V("r_ddan")},"")',
      note='UPS does not adjust out amortization or stock compensation, so adjusted operating profit is already full-cost.')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: adjusting items in operating profit (transformation strategy and other costs excluded by the company; deducted in the DCF)', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_tot")}),{V("o_tot")},"")')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS
    S('sec_r3', 'RECONCILIATION: NET INCOME / DILUTED EPS → NON-GAAP ADJUSTED NET INCOME → ADJUSTED EPS (company definition)', 'section',
      note='ADJUSTED EPS — net income + pre-tax adjusting items (operating and non-operating) − tax effect of the adjustments and discrete tax items (US tax reform 2017–18, valuation-allowance items)')
    S('e_ni', 'Net income (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('e_op', '  (+) Adjusting items in operating profit (pre-tax; bridge above)', 'line', 'm', all=lambda: f'={V("o_tot")}')
    S('e_nonop', '  (+) Adjusting items below operating profit (pre-tax; pension mark-to-market from 2018, investment write-downs)', 'line', 'm', all=lambda: f'={V("d_nonop")}')
    S('e_tax', '  (−) Tax effect of the adjustments & discrete tax items', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("e_pubni")}),{V("e_pubni")}-{V("e_ni")}-{V("e_op")}-{V("e_nonop")},IF(ISNUMBER({V("e_ni")}),0,""))',
      fc=lambda: f'=-({V("e_op")}+{V("e_nonop")})*{V("is_etr")}',
      note='Historical: derived as published adjusted net income − net income − pre-tax items (periods without adjusted measures: nil; adjusted = GAAP). Forecast: items × effective tax rate.')
    S('e_adjni', '  = Non-GAAP adjusted net income (model bridge)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("e_tax")}),{V("e_ni")}+{V("e_op")}+{V("e_nonop")}+{V("e_tax")},"")')
    S('e_pubni', '  Company-published non-GAAP adjusted net income', 'memo', 'm', data='a_ni_pub', flow=True)
    S('e_sh', '  Diluted shares used for adjusted EPS (m)', 'line', 'm', data='a_sh', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")',
      note='GAAP diluted shares; in GAAP-loss quarters (Q4/16, Q4/19, Q4/20) the company\'s adjusted EPS uses diluted shares including dilutive securities, as stated in the release footnote (blue inputs).')
    S('e_eps', 'Non-GAAP adjusted EPS – diluted ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published non-GAAP adjusted diluted EPS ($)', 'eps_memo', 'ps', data='a_eps_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0111,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_adjebt', '  Adjusted income before income taxes (adjusted operating profit + other income − interest + non-operating items)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_adj")}),{V("o_adj")}+N({V("is_othinc")})-N({V("is_int")})+N({V("e_nonop")}),"")')
    S('e_adjtax', '  Adjusted income tax (adjusted income before income taxes − adjusted net income)', 'line', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("e_adjni")}),ISNUMBER({V("e_adjebt")})),{V("e_adjebt")}-{V("e_adjni")},"")')
    S('e_rate', '  Adjusted effective tax rate', 'pct', 'pct', all=ratio('e_adjtax', 'e_adjebt'))
    S('e_def', '  Definition / basis (company adjusted EPS definition)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Revenue y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_adv', '  Consolidated average daily package volume y/y %', 'growth', 'pct', all=growth('g_adv'))
    S('gm_rpp', '  Consolidated revenue per piece y/y %', 'growth', 'pct', all=growth('g_rpp'))
    S('gm_us', '  U.S. Domestic Package revenue y/y %', 'growth', 'pct', all=growth('us_rev'))
    S('gm_intl', '  International Package revenue y/y %', 'growth', 'pct', all=growth('intl_rev'))
    S('gm_scs', '  Supply Chain Solutions revenue y/y %', 'growth', 'pct', all=growth('scs_rev'))
    S('gm_adjop', '  Adjusted operating profit y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating profit (GAAP) y/y %', 'growth', 'pct', all=growth('is_ebit'))
    S('gm_ni', '  Net income y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_adjop_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_inc', '  Incremental adjusted operating margin (Δ adjusted operating profit / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_ebit', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_comp', '  Compensation and benefits % of revenue', 'pct', 'pct', all=ratio('is_comp', 'is_rev'))
    S('gm_pt', '  Purchased transportation % of revenue', 'pct', 'pct', all=ratio('is_pt', 'is_rev'))
    blank()
