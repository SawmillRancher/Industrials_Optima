"""Row specification of the LMT Model sheet, part 1 (MLM template layout and process):
segment build (Aeronautics / Missiles and Fire Control / Rotary and Mission Systems / Space: sales growth x segment margin, backlog
roll-forward) -> unallocated items (FAS/CAS pension operating adjustment, intangible amortization, severance / impairment, other) ->
consolidated operating profit -> pension (FAS / CAS) block -> Ultra Maritime acquisition block -> M&A lever -> group total & 2026
outlook calibration -> cost drivers -> income statement -> GAAP-to-adjusted bridges -> growth & margins."""
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
def B1(key): return f'{LQ}{R[key]}'                       # 27-Sep-2026 balance
def LTM(key):                                             # last twelve months in a quarterly column (sum of 4 quarters), else the year
    c = CTX.col
    if c.q is None: return V(key)
    cols = []
    y, q = c.year, c.q
    for _ in range(4):
        cols.append(f'{QC[(y, q)].c}{R[key]}')
        q -= 1
        if q == 0: y, q = y - 1, 4
        if (y, q) not in QC: return None
    return '(' + '+'.join(cols) + ')'

SEG = [('aero', 'Aeronautics', 'AERO'), ('mfc', 'Missiles and Fire Control', 'MFC'), ('rms', 'Rotary and Mission Systems', 'RMS'), ('space', 'Space', 'SPACE')]
SEGK = [s for s, _, _ in SEG]
LEG = [('isgs', 'Information Systems & Global Solutions (IS&GS; divested to Leidos 16-Aug-2016; discontinued operations in 2016)'),
       ('es', 'Electronic Systems (2006-2010 structure; split into MFC / MST / IS&GS in 2013)')]

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of the 2026 guidance ranges (22-Oct-2026).'))
    r = 11
    SCEN_ROWS.append((r, 'out_hdr', V0['out_hdr'], 'High', 'Mid', 'Low', V0['out_note'])); r += 1
    for key, lab, (hi, mid, lo), nf, note in V0['outlook']:
        SC[key] = r; SCEN_ROWS.append((r, 'out', lab, hi, mid, lo, note, nf)); r += 1
    r += 1
    SCEN_ROWS.append((r, 'pt_hdr', 'Q4/26E and 2026E point estimates (all cases)', None, None, None, None)); r += 1
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
    S('sec_seg', 'BUSINESS SEGMENT P&L — AERONAUTICS · MISSILES AND FIRE CONTROL · ROTARY AND MISSION SYSTEMS · SPACE (sales growth × segment operating margin; backlog)', 'section',
      note='SEGMENT BUILD — modelling logic (segment sales → segment operating profit at the segment margin → Σ = business segment operating profit (company non-GAAP) → + unallocated items = consolidated operating profit → GAAP P&L)')
    blank()
    descr = {'aero': 'Aeronautics (F-35, F-16, F-22, C-130, advanced development programs / Skunk Works)',
             'mfc': 'Missiles and Fire Control (PAC-3, THAAD, GMLRS, HIMARS, JASSM / LRASM, Javelin, PrSM, Hellfire, fire control, sensors)',
             'rms': 'Rotary and Mission Systems (Sikorsky helicopters from 6-Nov-2015; Aegis, radars, C6ISR, undersea systems, training; Ultra Maritime pending) — Mission Systems and Training (MST) to 2015',
             'space': 'Space (satellites, strategic & missile defense, hypersonics, space transportation; ULA equity earnings) — Space Systems to 2019'}
    for s, title, code in SEG:
        S(f'{s}_hdr', descr[s], 'block', note=f'{title.upper()} — modelling logic')
        S(f'{s}_rev', f'  {title} net sales', 'line_b', 'm', data=f'sr_{s}', flow=True,
          qe=lambda s=s: f'={P(s + "_rev")}*(1+{V(s + "_g")})', ae=lambda s=s: f'={P(s + "_rev")}*(1+{V(s + "_g")})',
          note=('Segment net sales as reported (release segment schedules). Q4/26E: prior-year quarter × (1 + growth). 2027E+: prior year × (1 + scenario lever). '
                'Q4/26 has 14 weeks vs 13 in Q4/25 (Q1/26 had 12): the calibration Δ to the full-year guidance absorbs the calendar effect.') if s == 'aero' else None)
        S(f'{s}_g', '    y/y %', 'growth', 'pct', all=growth(f'{s}_rev'),
          qe=lambda s=s: f'={V(s + "_pre")}+{QEa("cal_g")}',
          ae=lambda code=code: '=' + CH(SC[f'{code}_G'][CTX.col.year]),
          note='Q4/26E: 9M 2026 y/y growth of the segment + sales-guidance calibration Δ (Group block). 2027E–2031E: scenario lever (Bull/Base/Bear table →).' if s == 'aero' else None)
        S(f'{s}_pre', '    Q4/26E growth before sales calibration (9M 2026 y/y)', 'driver', 'pct',
          qe=lambda s=s: f'=IFERROR({ACT(s + "_rev")}/{ACT0(s + "_rev")}-1,0)')
        S(f'{s}_mix', '  % of total net sales', 'pct', 'pct', all=ratio(f'{s}_rev', 'g_rev'))
        S(f'{s}_oi', f'  {title} operating profit', 'line', 'm', data=f'so_{s}', flow=True,
          qe=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}', ae=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}',
          note=('Segment operating profit as reported (company measure: excludes the unallocated items — FAS/CAS pension operating adjustment, intangible amortization, severance, '
                'stock-based compensation / corporate costs). Forecast = segment sales × segment margin.') if s == 'aero' else None)
        S(f'{s}_m', '  Segment operating margin %', 'pct', 'pct', all=ratio(f'{s}_oi', f'{s}_rev'),
          qe=lambda s=s: f'={V(s + "_m_pre")}+{QEa("cal_m")}', ae=lambda code=code: '=' + CH(SC[f'{code}_M'][CTX.col.year]),
          note=('Q4/26E: 9M 2026 segment margin + segment-operating-profit-guidance calibration Δ (Group block); the 9M 2026 margin is used rather than the prior-year quarter '
                'because 2025 margins carry the Q2/25 program losses. 2027E+: scenario lever.') if s == 'aero' else None)
        S(f'{s}_m_pre', '  Q4/26E margin before calibration (9M 2026 segment margin)', 'driver', 'pct',
          qe=lambda s=s: f'=IFERROR({ACT(s + "_oi")}/{ACT(s + "_rev")},0)')
        S(f'{s}_inc', '  Incremental segment margin (Δ operating profit / Δ sales)', 'pct', 'pct', all=incr(f'{s}_oi', f'{s}_rev'))
        S(f'{s}_bk', f'  {title} backlog (period end)', 'line', 'm', data=f'bk_{s}', bs=True,
          qe=lambda s=s: f'={PQ(s + "_bk")}+{V(s + "_ord")}-{V(s + "_rev")}', e26=lambda s=s: f'={QEc(s + "_bk")}', ae=lambda s=s: f'={P(s + "_bk")}+{V(s + "_ord")}-{V(s + "_rev")}',
          note=('Backlog as reported (release operating-data tables; 2013-14 on the structure then in force, Q4/15 realignment applied to 2014-15 per the Jan-2016 pro forma tables). '
                'Forecast roll-forward: prior + orders − sales.') if s == 'aero' else None)
        S(f'{s}_ord', '  Implied orders (Δ backlog + sales; incl. acquired backlog, de-bookings, FX)', 'line', 'm',
          hist=lambda s=s: (f'=IF(AND(ISNUMBER({V(s + "_bk")}),ISNUMBER({(PQ if CTX.col.q else P)(s + "_bk")})),{V(s + "_bk")}-{(PQ if CTX.col.q else P)(s + "_bk")}+{V(s + "_rev")},"")'
                            if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None),
          qe=lambda s=s: f'={V(s + "_rev")}*{V(s + "_b2b")}', e26=lambda s=s: f'={ACT(s + "_ord")}+{QEc(s + "_ord")}', ae=lambda s=s: f'={V(s + "_rev")}*{V(s + "_b2b")}',
          note='History: derived from the backlog roll-forward (Lockheed Martin publishes no orders figure; Q4/15 includes ~$15.6bn of Sikorsky acquired backlog in RMS). Forecast: sales × book-to-bill lever.' if s == 'aero' else None)
        S(f'{s}_b2b', '  Book-to-bill (x)', 'pct', 'x2', all=ratio(f'{s}_ord', f'{s}_rev'), qe_in=V0['b2b_q4'][s], e26=ratio(f'{s}_ord', f'{s}_rev'), ae=lambda: '=' + CH(SC['B2B'][CTX.col.year]),
          note='Q4/26E input (Q3/26 MFC 20x on the $52.5bn PAC-3 MSE multi-year award). 2027E+: scenario lever (all segments).' if s == 'aero' else None)
        S(f'{s}_cov', '  Backlog coverage (backlog ÷ last-twelve-month sales, years)', 'pct', 'x2',
          all=lambda s=s: (f'=IF(ISNUMBER({V(s + "_bk")}),IFERROR({V(s + "_bk")}/{LTM(s + "_rev")},""),"")' if LTM(f'{s}_rev') else None))
        blank()
    S('leg_hdr', 'Legacy segments (as reported in their periods; memo — included in the group totals for their periods)', 'block',
      note='LEGACY SEGMENTS — IS&GS (to 2015; discontinued operations 2016) and Electronic Systems (to 2010). 2006 on the four-segment basis of the FY2007 release; 2011-12 on the 2013 five-segment basis (FY2013 10-K / Q4-13 release); 2014-15 on the Q4/15 realignment basis.')
    for k, lab in LEG:
        S(f'{k}_rev', f'  {lab} — net sales', 'memo', 'm', data=f'sr_{k}', flow=True)
        S(f'{k}_oi', f'  {lab} — operating profit', 'memo', 'm', data=f'so_{k}', flow=True)
        S(f'{k}_bk', f'  {lab} — backlog', 'memo', 'm', data=f'bk_{k}', bs=True)
    S('co15_h', '  Memo: 2015 on the 2016 continuing-operations basis (IS&GS in discontinued operations), as re-presented in the 2016 filings:', 'sub', 'gen')
    S('co15_rev', '    Net sales — continuing operations (2016 re-presentation)', 'memo', 'm', data='co_rev')
    S('co15_segop', '    Business segment operating profit — continuing operations', 'memo', 'm', data='co_segop')
    S('co15_op', '    Consolidated operating profit — continuing operations', 'memo', 'm', data='co_op')
    S('co15_g', '    Memo: 2016 like-for-like net sales growth vs the 2015 continuing-operations base', 'memo_calc', 'pct',
      all=lambda: (f'=IF(ISNUMBER({P("co15_rev")}),IFERROR({V("is_rev")}/{P("co15_rev")}-1,""),"")' if CTX.col.prior and CTX.col.year == 2016 else None))
    blank()
    S('ua_hdr', 'Unallocated items (not included in business segment operating profit) → consolidated operating profit', 'block',
      note='UNALLOCATED ITEMS — company lines: FAS/CAS pension adjustment (total to 2017; operating adjustment only from 2018 under ASU 2017-07), intangible asset amortization (shown separately from 2023), severance / impairment and other charges, stock-based compensation and other, net; "unusual items" 2006-2010')
    S('ua_fascas', '  FAS/CAS pension adjustment (2006-17: total, incl. non-service cost; 2018+: FAS/CAS pension operating adjustment)', 'line', 'm', data='ua_fascas', flow=True,
      qe=lambda: f'={PT("pt_fascas")}', ae=lambda: f'={V("pn_op")}',
      note='Q4/26E = 2026 outlook $1,685m − 9M actual. 2027E+ = pension block (CAS pension cost − FAS service cost). Positive = CAS cost recovered in sales exceeds FAS service cost.')
    S('ua_amort', '  Intangible asset amortization expense (Sikorsky and other acquired intangibles; separate line from 2023)', 'line', 'm', data='ua_amort', flow=True,
      qe=lambda: f'=-{PT("pt_amort")}', ae=lambda: f'=-({V("d_amort_sch")}+N({V("um_amort")})+N({V("m_amort")}))',
      note='Q4/26E = 2026 outlook ~$(200)m − 9M actual. 2027E+ = 10-K amortization schedule + Ultra Maritime purchase-accounting amortization (deal block) + M&A lever. Before 2023 inside "Other, net".')
    S('ua_sev', '  Severance / restructuring, impairment and other charges (company special items)', 'line', 'm', data='ua_sev', flow=True, labkey='ua_sev_lab',
      qe=lambda: f'=-{PT("pt_sev")}', ae_in=V0['ae_sev'], note='Company-flagged charges (severance, goodwill impairment 2013-14, fixed-asset write-off Q2/25). Forecast input (none assumed).')
    S('ua_other', '  Stock-based compensation and other, net (corporate costs, state taxes, ULA / other items)', 'line', 'm', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("ua_sbc")}),N({V("ua_sbc")})+N({V("ua_other_only")}),"")',
      qe=lambda: f'=-{PT("pt_other")}', ae=lambda: f'=-{V("is_rev")}*{V("ua_other_pct")}',
      note='History: stock-based compensation (shown separately to 2016) + other, net. Q4/26E = 2026 outlook ~$(540)m − 9M actual. 2027E+ = % of net sales.')
    S('ua_other_pct', '  Stock-based compensation and other, net % of sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("ua_other")}),IFERROR(-{V("ua_other")}/{V("is_rev")},""),"")', ae_in=V0['ua_other_pct'])
    S('ua_sbc', '  Memo: of which stock-based compensation (separately disclosed 2006-2016)', 'memo', 'm', data='ua_sbc', flow=True)
    S('ua_other_only', '  Memo: of which other, net', 'memo', 'm', data='ua_other', flow=True, labkey='ua_other_lab')
    S('ua_special', '  Unusual items, net (2006-2010: gains on sales of businesses / investments, charges; company-flagged)', 'line', 'm', data='ua_special', flow=True, labkey='ua_special_lab', fc=lambda: '=0')
    S('ua_tot', '  Total unallocated items', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("ua_fascas")}),{nsum(["ua_fascas", "ua_amort", "ua_sev", "ua_other", "ua_special"])},"")')
    S('ua_pub', '  Memo: total unallocated items as reported', 'memo', 'm', data='ua_tot', flow=True)
    S('ua_chk', '  Check: unallocated items vs reported total (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("ua_pub")}),IF(ABS({V("ua_tot")}-{V("ua_pub")})<=0.6,0,ROUND({V("ua_tot")}-{V("ua_pub")},0)),"")')
    blank()

    # ------------------------------------------------------------------ pension block
    S('pn_hdr', 'Pension — FAS expense vs CAS cost (qualified defined benefit plans; annual detail from the releases / 10-K; quarterly from 2018 where disclosed)', 'block',
      note='PENSION — CAS pension cost is recovered through contract pricing (in sales); FAS expense is the GAAP cost. FAS/CAS operating adjustment = CAS cost − FAS service cost (in operating profit); non-service FAS pension (expense) income is below operating profit from 2018 (ASU 2017-07; 2017 re-presented). 2026E from the company outlook; 2027E+ inputs (assumptions: held at the 2026 outlook; no 2027 guidance filed)')
    S('pn_cas', '  CAS pension cost (recovered in sales)', 'line', 'm', data='p_cas', ann=True, e26_in=V0['pn']['cas'][2026], ae_in={y: V0['pn']['cas'][y] for y in range(FYC + 1, FYL + 1)},
      note='Annual: release FAS/CAS tables (2006-08 "Less: CAS costs"; 2013+ "CAS pension cost"). 2026 outlook $1,735m. 2027E+: input (assumption, held).')
    S('pn_svc', '  FAS pension service cost', 'line', 'm', data='p_svc', ann=True, e26_in=V0['pn']['svc'][2026], ae_in={y: V0['pn']['svc'][y] for y in range(FYC + 1, FYL + 1)},
      note='Disclosed from 2017 (ASU 2017-07 reconciliation). 2026 outlook $(50)m.')
    S('pn_op', '  FAS/CAS pension operating adjustment (= CAS cost + FAS service cost; in operating profit from 2018)', 'line', 'm', data='p_fascas_op', ann=True,
      e26=lambda: f'={V("pn_cas")}+{V("pn_svc")}', ae=lambda: f'={V("pn_cas")}+{V("pn_svc")}', note='2026E = outlook $1,685m. Drives the unallocated FAS/CAS line (2018+).')
    S('pn_nonsvc', '  Non-service FAS pension (expense) income (below operating profit from 2018; incl. settlement charges)', 'line', 'm', data='p_nonsvc', ann=True,
      e26=lambda: f'={ACT("is_nonsvc")}+{QEc("is_nonsvc")}', ae_in={y: V0['pn']['nonsvc'][y] for y in range(FYC + 1, FYL + 1)},
      note='2026 outlook $(320)m. 2027E+ input (assumption).')
    S('pn_fas', '  Total FAS pension expense (income) (= service + non-service; incl. settlement charges)', 'line', 'm', data='p_fas_exp', ann=True,
      e26=lambda: f'={V("pn_svc")}+{V("pn_nonsvc")}', ae=lambda: f'={V("pn_svc")}+{V("pn_nonsvc")}', note='2006-08 "FAS 87 expense"; 2026 outlook $(370)m.')
    S('pn_tot', '  Total FAS/CAS pension adjustment (= CAS cost + FAS expense; company "net FAS/CAS pension adjustment")', 'line_b', 'm', data='p_fascas', ann=True,
      e26=lambda: f'={V("pn_cas")}+{V("pn_fas")}', ae=lambda: f'={V("pn_cas")}+{V("pn_fas")}', note='2026 outlook ~$1,365m (guided). 2025: $644m incl. the $479m settlement charge ($1,123m adjusted).')
    S('pn_chk', '  Check: operating adjustment + non-service = total FAS/CAS adjustment (should be 0)', 'check', 'm', ann=True,
      all=lambda: f'=IF(AND(ISNUMBER({V("pn_op")}),ISNUMBER({V("pn_nonsvc")}),ISNUMBER({V("pn_tot")})),IF(ABS({V("pn_op")}+{V("pn_nonsvc")}-{V("pn_tot")})<=0.6,0,ROUND({V("pn_op")}+{V("pn_nonsvc")}-{V("pn_tot")},0)),"")')
    S('pn_settle', '  Memo: pension settlement charges (noncash; in non-service FAS pension expense)', 'memo', 'm', data='p_settle', ann=True)
    S('pn_contrib', '  Pension contributions (cash; input)', 'driver', 'm', e26_in=V0['pn']['contrib'][2026], ae_in={y: V0['pn']['contrib'][y] for y in range(FYC + 1, FYL + 1)},
      note='FY2025 10-K: $860m contributed in 2025; no required contributions expected in 2026. 2027E+: none assumed (input).')
    S('pn_cf', '  Memo: cash-flow statement pension line (FAS expense − contributions; "qualified defined benefit pension plans")', 'memo', 'm', data='cf_pens', flow=True)
    blank()

    # ------------------------------------------------------------------ Ultra Maritime (pending)
    S('um_hdr', 'Pending acquisition — Ultra Maritime Solutions ($3.45bn cash; RMS; expected to close Q4 2026; terms per the Q3/26 10-Q Note 13)', 'block',
      note='ULTRA MARITIME — toggle + closing date; standalone sales / margin are MODEL ASSUMPTIONS (the target is private and its revenue is not disclosed on EDGAR). Excluded from the company 2026 outlook; added on top of the segment build')
    S('um_sw', '  Deal switch (1 = closes; 0 = excluded)', 'driver', 'gen', e26_in=1, ae=lambda: f'={P("um_sw")}')
    S('um_cons', '  Consideration (cash, USDm)', 'driver', 'm', e26_in=MAN['ultra_maritime']['consideration'], ae_in=0.0, note=MAN['ultra_maritime']['src'])
    S('um_days', '  Days consolidated in the year ÷ 365 (closing assumed 31-Dec-2026 → no 2026 contribution; full years from 2027E)', 'driver', 'pct', e26_in=0.0, ae_in=1.0)
    S('um_sales0', '  Standalone annual sales — ASSUMPTION, not disclosed (USDm)', 'driver', 'm', e26_in=V0['um']['sales'], ae=lambda: f'={P("um_sales0")}*(1+{V("um_g")})',
      note=MAN['ultra_maritime']['assumptions'])
    S('um_g', '  Sales growth %', 'driver', 'pct', ae_in=V0['um']['g'])
    S('um_rev', '  Ultra Maritime net sales contribution (RMS)', 'line', 'm', e26=lambda: f'={V("um_sw")}*{V("um_sales0")}*{V("um_days")}', ae=lambda: f'={V("um_sw")}*{V("um_sales0")}*{V("um_days")}')
    S('um_m', '  Segment operating margin % — assumption', 'driver', 'pct', e26_in=V0['um']['m'], ae_in=V0['um']['m'])
    S('um_oi', '  Ultra Maritime segment operating profit contribution', 'line', 'm', e26=lambda: f'={V("um_rev")}*{V("um_m")}', ae=lambda: f'={V("um_rev")}*{V("um_m")}')
    S('um_intp', '  Acquired intangibles % of consideration — assumption', 'driver', 'pct', e26_in=V0['um']['intp'])
    S('um_life', '  Intangible amortization life (years) — assumption', 'driver', 'gen', e26_in=V0['um']['life'])
    S('um_ppe', '  PP&E % of consideration — assumption', 'driver', 'pct', e26_in=V0['um']['ppe'])
    S('um_amort', '  Purchase-accounting amortization (unallocated intangible amortization)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'={V("um_sw")}*IFERROR(${E26}${R["um_cons"]}*${E26}${R["um_intp"]}/${E26}${R["um_life"]},0)*{V("um_days")}')
    S('um_rms', '  Memo: RMS net sales incl. Ultra Maritime (as it would be reported)', 'memo_calc', 'm', e26=lambda: f'={V("rms_rev")}+{V("um_rev")}', ae=lambda: f'={V("rms_rev")}+{V("um_rev")}')
    blank()

    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — bolt-ons beyond Ultra Maritime, unallocated to segments; deals closed from 2027E)', 'block',
      note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=V0['m_mult'], e26_in=0.0, note='Ultra Maritime ~3.8x assumed sales; Sikorsky (2015) $9.0bn on ~$6.5bn sales (1.4x). Input (assumption).')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', e26_in=0.0, ae_in=0.05)
    S('m_run', '  Run-rate revenue of businesses acquired (year end)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+{V("m_acq_sales")}')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_run")}*(1+{V("m_g")})+0.5*{V("m_acq_sales")}', note='Mid-year convention.')
    S('m_m', '  Segment operating margin of acquired businesses %', 'driver', 'pct', e26_in=0.0, ae_in=0.12)
    S('m_oi', '  Segment operating profit from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.10)
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.35)
    S('m_life', '  Intangible amortization life (years)', 'driver', 'gen', e26_in=0, ae_in=12)
    S('m_cum', '  Cumulative acquired intangibles (gross)', 'line', 'm', e26_in=0.0, ae=lambda: f'={P("m_cum")}+{V("m_spend")}*{V("m_intp")}')
    S('m_amort', '  Amortization of future-acquisition intangibles (unallocated)', 'line', 'm', e26_in=0.0,
      ae=lambda: f'=IFERROR(({P("m_cum")}+0.5*{V("m_spend")}*{V("m_intp")})/{V("m_life")},0)')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group Total — net sales, business segment operating profit, consolidated operating profit (segment build) → 2026 outlook calibration', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Net sales (segment build)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("aero_rev")}),{"+".join("N(" + V(k) + ")" for k in ["aero_rev", "mfc_rev", "rms_rev", "space_rev", "isgs_rev", "es_rev"])},{V("is_rev")})',
      fc=lambda: f'={V("aero_rev")}+{V("mfc_rev")}+{V("rms_rev")}+{V("space_rev")}+N({V("um_rev")})+N({V("m_rev")})',
      note='Σ segment sales (+ legacy segments in their periods; + Ultra Maritime and future acquisitions in the forecast).')
    S('g_rev_g', '  Net sales y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs consolidated net sales (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=0.6,0,ROUND({V("g_rev")}-{V("is_rev")},0)),"")')
    S('g_segop', 'Business segment operating profit (segment build; company non-GAAP measure)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("aero_oi")}),{"+".join("N(" + V(k) + ")" for k in ["aero_oi", "mfc_oi", "rms_oi", "space_oi", "isgs_oi", "es_oi"])},"")',
      fc=lambda: f'={V("aero_oi")}+{V("mfc_oi")}+{V("rms_oi")}+{V("space_oi")}+N({V("um_oi")})+N({V("m_oi")})',
      note="Σ segment operating profit. Lockheed Martin's primary performance measure and the one it guides.")
    S('g_segm', '  Business segment operating margin %', 'pct', 'pct', all=ratio('g_segop', 'is_rev'))
    S('g_segop_g', '  Business segment operating profit y/y %', 'growth', 'pct', all=growth('g_segop'))
    S('g_segop_pub', '  Memo: business segment operating profit as reported', 'memo', 'm', data='segop_pub', flow=True)
    S('g_chk_segop', '  Check: segment build vs reported business segment operating profit (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("g_segop")}),ISNUMBER({V("g_segop_pub")})),IF(ABS({V("g_segop")}-{V("g_segop_pub")})<=0.6,0,ROUND({V("g_segop")}-{V("g_segop_pub")},0)),"")')
    S('g_op', 'Consolidated operating profit (segment build + unallocated items)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_segop")}),ISNUMBER({V("ua_tot")})),{V("g_segop")}+{V("ua_tot")},"")', note='Business segment operating profit + total unallocated items; drives the GAAP P&L below.')
    S('g_opm', '  Consolidated operating margin %', 'pct', 'pct', all=ratio('g_op', 'is_rev'))
    S('g_chk_op', '  Check: build vs reported consolidated operating profit (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("g_op")}),IF(ABS({V("g_op")}-{V("is_op")})<=0.6,0,ROUND({V("g_op")}-{V("is_op")},0)),"")')
    S('cal_guid', '  Memo: 2026 net sales guidance (scenario end-point; outlook excludes Ultra Maritime)', 'memo', 'm', e26=lambda: '=' + CH(SC['out_sales']), note=V0['rev_guid_note'])
    S('cal_pre', '  Net sales before calibration (Q4/26E helper; four segments)', 'line', 'm', qe=lambda: '=' + '+'.join(f'{P(k + "_rev")}*(1+{V(k + "_pre")})' for k in SEGK))
    S('cal_sens', '  Net sales sensitivity to +1.00 of growth (Q4/26E helper)', 'line', 'm', qe=lambda: '=' + '+'.join(P(k + '_rev') for k in SEGK))
    S('cal_g', '  Guidance calibration: Δ y/y growth applied to all four segments (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_guid", E26)}-{ACT("g_rev")}-{V("cal_pre")})/{V("cal_sens")}',
      note='Solves the uniform growth shift (vs 9M 2026 y/y rates) so that 2026 net sales excluding Ultra Maritime = the guidance end-point for the active scenario.')
    S('cal_rev_chk', '  Check: 2026 net sales (ex Ultra Maritime) vs guidance end-point (should be 0)', 'check', 'm', e26=lambda: f'=ROUND({V("g_rev")}-N({V("um_rev")})-{V("cal_guid")},0)')
    S('cal_segop', '  Memo: 2026 business segment operating profit guidance (scenario end-point)', 'memo', 'm', e26=lambda: '=' + CH(SC['out_segop']), note=V0['segop_guid_note'])
    S('cal_oi_pre', '  Business segment operating profit before margin calibration (Q4/26E helper)', 'line', 'm',
      qe=lambda: '=' + '+'.join(f'{V(k + "_rev")}*{V(k + "_m_pre")}' for k in SEGK))
    S('cal_segrev', '  Segment sales (Q4/26E helper)', 'line', 'm', qe=lambda: '=' + '+'.join(V(k + '_rev') for k in SEGK))
    S('cal_m', '  Guidance calibration: Δ segment operating margin applied to all four segments (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_segop", E26)}-{ACT("g_segop")}-{V("cal_oi_pre")})/{V("cal_segrev")}',
      note='Solves the uniform segment-margin shift so that 2026 business segment operating profit excluding Ultra Maritime = the guidance end-point for the active scenario.')
    S('cal_segop_chk', '  Check: 2026 business segment operating profit (ex Ultra Maritime) vs guidance end-point (should be 0)', 'check', 'm',
      e26=lambda: f'=ROUND({V("g_segop")}-N({V("um_oi")})-{V("cal_segop")},0)')
    S('cal_eps', '  Memo: 2026 diluted EPS guidance (scenario end-point, $) — information, not forced', 'eps_memo', 'ps', e26=lambda: '=' + CH(SC['out_eps']), note=V0['eps_guid_note'])
    S('cal_eps_d', '    Model 2026E diluted EPS − guidance ($; information: unallocated items, interest, tax and share count per the point estimates)', 'memo_calc', 'ps', e26=lambda: f'={V("eps_dil")}-{V("cal_eps")}')
    S('cal_cop', '  Memo: 2026 consolidated operating profit guidance (scenario end-point; company bridge)', 'memo', 'm', e26=lambda: '=' + CH(SC['out_cop']))
    S('cal_cop_d', '    Model 2026E consolidated operating profit (ex Ultra Maritime) − guidance (information)', 'memo_calc', 'm', e26=lambda: f'={V("g_op")}-N({V("um_oi")})-{V("cal_cop")}')
    S('cal_cfo', '  Memo: 2026 cash from operations guidance (scenario end-point)', 'memo', 'm', e26=lambda: '=' + CH(SC['out_cfo']), note=V0['cfo_guid_note'])
    S('cal_cfo_chk', '  Check: 2026E cash from operations vs guidance end-point (should be 0; Q4/26E contract-asset change is the calibration plug)', 'check', 'm',
      e26=lambda: f'=ROUND({V("cf_cfo")}-{V("cal_cfo")},0)')
    S('cal_fcf', '  Memo: 2026 free cash flow guidance (scenario end-point)', 'memo', 'm', e26=lambda: '=' + CH(SC['out_fcf']))
    S('cal_fcf_d', '    Model 2026E free cash flow − guidance (information; capex at the point estimate)', 'memo_calc', 'm', e26=lambda: f'={V("fcf")}-{V("cal_fcf")}')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A & other P&L inputs', 'block', note='COST DRIVERS — inputs that drive forecast cost lines (Q4/26E: point estimates consistent with the 2026 outlook bridge; 2027E+: % of sales or schedules)')
    S('d_dda', '  Depreciation & amortization (cash-flow statement)', 'line', 'm', data='cf_dda', flow=True,
      all=lambda: f'=IF(AND(ISNUMBER({V("d_dep")}),ISNUMBER({V("d_amort")})),{V("d_dep")}+{V("d_amort")},"")',
      note='Cash-flow statement D&A (2006-08: depreciation and amortization + amortization of purchased intangibles).')
    S('d_amort', '  of which: intangible asset amortization (unallocated line, positive)', 'line', 'm', hist=lambda: f'=IF(ISNUMBER({V("ua_amort")}),-{V("ua_amort")},"")', fc=lambda: f'=-{V("ua_amort")}',
      note='Separately disclosed as an unallocated item from 2023 ($247m 2023-24, $254m 2025); earlier years inside "Other, net" (not split: depreciation line = total D&A).')
    S('d_amort_sch', '  Amortization schedule — intangibles held at 31-Dec-2025 (FY2025 10-K Note 7; input)', 'driver', 'm', ae_in=V0['amort_sched'], note=MAN['amort_sched']['src'] + ' 2031E assumed $100m.')
    S('d_dep', '  Depreciation & other amortization (D&A − intangible amortization)', 'line', 'm', data='cf_dda', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("d_dda_pub")}),{V("d_dda_pub")}-N({V("d_amort")}),"")',
      qe=lambda: f'={PT("pt_dep")}', ae=lambda: f'={V("is_rev")}*{V("d_dep_pct")}')
    S('d_dda_pub', '  Memo: depreciation & amortization as reported (cash-flow statement)', 'memo', 'm', data='cf_dda', flow=True)
    S('d_dep_pct', '  Depreciation & other amortization % of net sales', 'pct', 'pct', all=ratio('d_dep', 'is_rev'), ae_in=V0['dep_pct'],
      note='2025: 1.9% of sales; capex ~$2.2bn p.a. (2026 outlook $2.1-2.3bn) vs depreciation ~$1.5bn → drifting up.')
    S('d_sbc', '  Stock-based compensation (cash-flow statement)', 'line', 'm', data='cf_sbc', flow=True,
      qe=lambda: f'={PT("pt_sbc")}', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}')
    S('d_sbc_pct', '  Stock-based compensation % of net sales', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_othinc', '  Other income, net — in operating profit (ULA and other equity earnings, gains); input', 'line', 'm', qe=lambda: f'={PT("pt_othinc")}', ae_in=V0['othinc'],
      note='Other income, net inside operating profit: mainly equity earnings of United Launch Alliance and other investments. 9M 2026 $25m; 2025 $112m. Input (assumption).')
    S('d_othnonop', '  Other non-operating income (expense), net — interest income and other; input', 'line', 'm', qe=lambda: f'={PT("pt_othnonop")}', ae=lambda: f'={P("cf_end")}*{V("ds_r_cash")}+{V("d_othnonop_x")}',
      note='9M 2026 $179m (mainly interest income on ~$5bn of cash). 2027E+ = yield × opening cash + other (input).')
    S('d_othnonop_x', '  Other non-operating items excl. interest income ($m; input)', 'driver', 'm', ae_in=V0['othnonop_x'])
    S('d_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='9M 2026 15.6% (FDDEI deductions, R&D credits); 2025 15.3%. Q4/26E point estimate; 2027E+ input.')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF EARNINGS (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (operating profit = segment build + unallocated items; cost of sales implied)')
    S('is_rev', 'Net sales', 'total', 'm', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the segment build. 2017 on the ASC 606 adjusted basis (2018 release comparatives); 2016 and earlier pre-ASC 606.')
    S('is_cos', 'Cost of sales (incl. severance and other unallocated charges; "operating costs and expenses" from 2026)', 'line', 'm', data='cos', flow=True, fc=lambda: f'={V("is_rev")}-{V("is_gp")}')
    S('is_gp', 'Gross profit', 'line_b', 'm', hist=lambda: f'=IF(ISNUMBER({V("is_cos")}),{V("is_rev")}-{V("is_cos")},"")',
      fc=lambda: f'={V("is_op")}-{V("is_othinc")}', note='Forecast = operating profit − other income, net (implied by the segment build).')
    S('is_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('is_othinc', 'Other income, net (income +)', 'line', 'm', data='othinc', flow=True, fc=lambda: f'={V("d_othinc")}')
    S('is_op', 'Operating profit', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_gp")}),{V("is_gp")}+N({V("is_othinc")}),"")', fc=lambda: f'={V("g_op")}',
      note='Forecast = business segment operating profit + unallocated items (Group block). 2017 re-presented for ASU 2017-07 (non-service pension cost below operating profit); 2016 and earlier include the total FAS/CAS adjustment in operating profit.')
    S('is_opm', '  Operating margin %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('is_int', 'Interest expense', 'line', 'm', data='int', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_rev")}*{V("ds_r_rev")}',
      note='Q4/26E point estimate (Q3/26 $264m). 2027E+ = rate × opening notes + rate × opening commercial paper / revolver (no circularity).')
    S('is_nonsvc', 'Non-service FAS pension (expense) income (from 2018; separate line from Q3/21; incl. settlement charges)', 'line', 'm', data='nonsvc', flow=True,
      qe=lambda: f'=-{PT("pt_nonsvc")}', ae=lambda: f'={V("pn_nonsvc")}',
      note='Q4/26E = 2026 outlook $(320)m − 9M actual $(241)m. 2027E+ = pension block. 2018-19 and Q1/Q2-20: inside other non-operating (not separately presented).')
    S('is_othnonop', 'Other non-operating income (expense), net', 'line', 'm', data='othnonop', flow=True, fc=lambda: f'={V("d_othnonop")}')
    S('is_ebt', 'Earnings from continuing operations before income taxes', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_op")}),{V("is_op")}-{V("is_int")}+N({V("is_nonsvc")})+N({V("is_othnonop")}),"")')
    S('is_tax', 'Income tax expense', 'line', 'm', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("d_etr")}', note='Q4/17 includes the ~$1.9bn Tax Cuts and Jobs Act charge.')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'))
    S('is_cont', 'Net earnings from continuing operations', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_disc', 'Net earnings (loss) from discontinued operations (PAE / EIG 2010-11; IS&GS 2016; other)', 'line', 'm', data='disc', flow=True, fc=lambda: '=0')
    S('is_ni', 'Net earnings', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("is_cont")}),{V("is_cont")}+N({V("is_disc")}),"")')
    S('is_ni_chk', '  Check: net earnings vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=0.6,0,ROUND({V("is_ni")}-{V("is_ni_pub")},0)),"")')
    S('is_ni_pub', '  Memo: net earnings as reported', 'memo', 'm', data='ni', flow=True)
    S('is_dda', '  Memo: depreciation & amortization', 'memo_calc', 'm', all=lambda: f'={V("d_dda")}')
    S('is_sbc', '  Memo: stock-based compensation', 'memo_calc', 'm', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={B1("bs_shares")}-${E26}${R["bb_sh"]}*0.5+${E26}${R["bb_iss"]}*0.5',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Q4/26E: shares outstanding at 27-Sep-2026 − Q4 buybacks (mid-quarter) + equity-plan issuance. 2027E+: average of beginning and ending shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_dil', 'EPS – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")',
      note='Net earnings / weighted diluted shares (±$0.01 vs reported).')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – diluted as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01 rounding, ±0.03 in loss quarters)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=IF({V("is_ni")}<0,0.0301,0.0101),0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")')
    S('eps_cont', '  Memo: EPS – diluted from continuing operations, as reported ($)', 'eps_memo', 'ps', data='eps_d_cont')
    S('dps', '  Cash dividends per share ($; quarterly = rate paid in the quarter)', 'line', 'ps', data='dps', flow=True, qe_in=V0['dps_q'],
      ae=lambda: f'={P("dps")}*(1+{V("dps_g")})',
      note='Annual: dividends declared per share (XBRL; FY2006-08 10-K). Quarterly: the quarterly rate (Q1 declared rate; Q4 = year − 9M). Q4/26: $3.60 (raised Oct-2026 from $3.45). 2027E+: prior year × (1 + growth).')
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'], note='Raised every year since 2003; +4.3% in Oct-2026 ($3.45 → $3.60), +4.5% in 2025. Input.')
    blank()

    # ------------------------------------------------------------------ RECON 1: operating profit -> business segment operating profit
    S('sec_r1', 'RECONCILIATION: CONSOLIDATED OPERATING PROFIT → BUSINESS SEGMENT OPERATING PROFIT (company non-GAAP measure)', 'section',
      note='BUSINESS SEGMENT OPERATING PROFIT — consolidated operating profit less the unallocated items (company definition, published every period; the measure Lockheed Martin guides)')
    S('o_op', 'Consolidated operating profit (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_op")}')
    S('o_fascas', '  (−) FAS/CAS pension adjustment (operating adjustment from 2018)', 'line', 'm', all=lambda: f'=-{V("ua_fascas")}')
    S('o_amort', '  (+) Intangible asset amortization expense', 'line', 'm', all=lambda: f'=-{V("ua_amort")}')
    S('o_sev', '  (+) Severance / impairment and other charges', 'line', 'm', all=lambda: f'=-{V("ua_sev")}')
    S('o_oth', '  (+) Stock-based compensation and other, net; (−) unusual items', 'line', 'm', all=lambda: f'=-{V("ua_other")}-N({V("ua_special")})')
    S('o_adj', '  = Business segment operating profit (model bridge)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_fascas")}+{V("o_amort")}+{V("o_sev")}+{V("o_oth")},"")',
      note='Equals the segment build (check in the Group block); the company-published figure is in the memo row below.')
    S('o_adj_m', '  Business segment operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company-published business segment operating profit', 'memo', 'm', data='segop_pub', flow=True)
    S('o_chk', '  Check: model bridge vs company-published (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),IF(ABS({V("o_adj")}-{V("o_pub")})<=0.6,0,ROUND({V("o_adj")}-{V("o_pub")},0)),"n/p")')
    S('o_def', '  Definition / basis (company segment-reporting basis in force)', 'text', 'gen',
      note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('o_inc', '  Incremental business segment operating margin (Δ segment OP / Δ net sales)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: net earnings -> EBITDA -> adjusted EBITDA (model)
    S('sec_r2', 'RECONCILIATION: NET EARNINGS → EBITDA → ADJUSTED EBITDA → ADJUSTED EBIT (model definitions; Lockheed Martin publishes no EBITDA)', 'section',
      note='EBITDA — model definition: operating profit + D&A; adjusted = + company-flagged severance / impairment / unusual items and the company-quantified program losses (2024-25). Pension settlement charges are below operating profit and therefore outside EBITDA')
    S('r_ni', 'Net earnings (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('r_disc', '  (−) Discontinued operations', 'line', 'm', all=lambda: f'=-N({V("is_disc")})')
    S('r_tax', '  (+) Income tax expense', 'line', 'm', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest expense', 'line', 'm', all=lambda: f'={V("is_int")}')
    S('r_nonop', '  (−) Non-service FAS pension income / other non-operating income', 'line', 'm', all=lambda: f'=-N({V("is_nonsvc")})-N({V("is_othnonop")})')
    S('r_op', '  = Operating profit (GAAP)', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_disc")}+{V("r_tax")}+{V("r_int")}+{V("r_nonop")},"")')
    S('r_op_chk', '  Check: vs statement operating profit (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_op")}),IF(ABS({V("r_op")}-{V("is_op")})<=0.6,0,ROUND({V("r_op")}-{V("is_op")},0)),"")')
    S('r_dda', '  (+) Depreciation & amortization', 'line', 'm', all=lambda: f'={V("d_dda")}')
    S('r_ebitda', '  = EBITDA (model)', 'total', 'm', all=lambda: f'=IF(AND(ISNUMBER({V("r_op")}),ISNUMBER({V("r_dda")})),{V("r_op")}+{V("r_dda")},"")')
    S('r_sev', '  (+) Severance / impairment and other charges; (−) unusual items (company-flagged unallocated items)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("ua_sev")}),-{V("ua_sev")}-N({V("ua_special")}),"")')
    S('r_pl', '  (+) Program losses quantified by the company (Q4/24 classified programs; Q2/25 Aeronautics classified, CMHP, TUHP; consolidated OP effect)', 'line', 'm', data='sp_pl', flow=True, fc=lambda: '=0',
      note='Pre-tax, net of the state-tax offset the company shows in unallocated other (Q4/24 $1,634m; Q2/25 $1,534m excl. the $66m write-off carried in the charges row). The 2024 annual figure published by the company ($1,965m) includes $245m recognised in Q1-Q3/24 that was not quantified by quarter; the model uses the Q4 amount.')
    S('r_adj', '  = Adjusted EBITDA (model definition)', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{V("r_ebitda")}+N({V("r_sev")})+N({V("r_pl")}),"")',
      note='Used for leverage (net debt / adjusted EBITDA) and EV / EBITDA. Includes the FAS/CAS pension operating adjustment (part of operating profit).')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_ddan', '  (−) Depreciation & amortization', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("d_dda")}),-{V("d_dda")},"")')
    S('r_ebit', '  = Adjusted EBIT (model; full-cost, after intangible amortization; for NOPAT, ROIC and the DCF)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+{V("r_ddan")},"")',
      note='Operating profit + company-flagged charges and quantified program losses. Lockheed Martin does not adjust out intangible amortization or stock-based compensation; neither does the model.')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: cash charges adjusted out (severance / restructuring; deducted again in the DCF)', 'memo_calc', 'm', all=lambda: f'=IF(ISNUMBER({V("r_sev")}),MAX(0,{V("r_sev")}),"")')
    S('r_exfas', '  Memo: adjusted EBIT excluding the FAS/CAS pension operating adjustment', 'memo_calc', 'm', all=lambda: f'=IF(ISNUMBER({V("r_ebit")}),{V("r_ebit")}-N({V("ua_fascas")}),"")')
    blank()

    # ------------------------------------------------------------------ RECON 3: adjusted EPS (model)
    S('sec_r3', 'RECONCILIATION: NET EARNINGS / DILUTED EPS → ADJUSTED NET EARNINGS → ADJUSTED EPS (model definition; the company quotes adjusted EPS only for individual items)', 'section',
      note='ADJUSTED EPS — model definition: net earnings from continuing operations + company-flagged charges (severance / impairment / unusual items, tax-effected at the statutory rate) + company-quantified program losses and pension settlement charges (company after-tax amounts) + the 2017 Tax Act charge. Lockheed Martin itself quotes EPS "excluding" only the large items (memo rows)')
    S('e_ni', 'Net earnings from continuing operations (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_cont")}')
    S('e_sev', '  (+) Severance / impairment and other charges; (−) unusual items (pre-tax)', 'line', 'm', all=lambda: f'=N({V("r_sev")})')
    S('e_sev_tax', '  (−) Tax effect at the statutory rate (35% to 2017, 21% from 2018; model assumption)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("e_sev")}),-{V("e_sev")}*{0.35 if CTX.col.year <= 2017 else 0.21},"")')
    S('e_pl', '  (+) Program losses quantified by the company (pre-tax)', 'line', 'm', all=lambda: f'=N({V("r_pl")})')
    S('e_pens', '  (+) Pension settlement charges (pre-tax; Q3/21 $1,665m, Q2/22 $1,470m, Q4/25 $479m)', 'line', 'm', data='sp_pens', flow=True, fc=lambda: '=0')
    S('e_ctax', '  (−) Tax effect of the program losses and settlement charges (company-disclosed after-tax amounts)', 'line', 'm', data='sp_tax', flow=True, fc=lambda: '=0',
      note='Company-disclosed: Q3/21 $1.3bn after tax ($4.72/sh); Q2/22 $1,156m ($4.33); Q4/24 $1,291m ($5.45); Q2/25 $1,367m ($5.83, incl. the write-off); Q4/25 $377m ($1.63).')
    S('e_taxact', '  (+) Tax Cuts and Jobs Act one-time net charge (Q4/17; ~$1.9bn, $6.80 per share)', 'line', 'm', data='sp_taxact', flow=True, fc=lambda: '=0')
    S('e_adjni', '  = Adjusted net earnings (model definition)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("e_ni")}),{V("e_ni")}+N({V("e_sev")})+N({V("e_sev_tax")})+N({V("e_pl")})+N({V("e_pens")})+N({V("e_ctax")})+N({V("e_taxact")}),"")')
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted EPS – diluted ($) (model definition)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_co_h', '  Company-quoted basis (GAAP EPS excluding only the item(s) the company quantified in that release):', 'sub', 'gen')
    S('e_co_base', '  Memo: diluted EPS from continuing operations as originally reported ($; basis of the company quotes)', 'eps_memo', 'ps', data='eps_co_base')
    S('e_co_eps', '  Memo: EPS excluding the company-quantified items — model rebuild (as-reported continuing-operations EPS − items per share as published)', 'eps_memo', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_co_ps")}),{V("e_co_ps")}<>0),{V("e_co_base")}-{V("e_co_ps")},"")')
    S('e_co_ps', '  Memo: per-share impact of the company-quantified items, as published ($; negative = charge)', 'eps_memo', 'ps', data='sp_ps')
    S('e_co_pub', '  Company-quoted EPS excluding the items ($; Q4/17 "adjusted EPS from continuing operations" $4.30 / 2017 $13.33; otherwise GAAP EPS + per-share impact)', 'eps_memo', 'ps', data='sp_eps_pub')
    S('e_co_chk', '  Check: rebuild vs company-quoted (should be 0.00; ±0.01)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_co_pub")}),ISNUMBER({V("e_co_eps")})),IF(ABS({V("e_co_eps")}-{V("e_co_pub")})<=0.0101,0,ROUND({V("e_co_eps")}-{V("e_co_pub")},2)),"n/p")')
    S('e_def', '  Definition / basis (items in the model adjusted EPS)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Net sales y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_aero', '  Aeronautics sales y/y %', 'growth', 'pct', all=growth('aero_rev'))
    S('gm_mfc', '  Missiles and Fire Control sales y/y %', 'growth', 'pct', all=growth('mfc_rev'))
    S('gm_rms', '  Rotary and Mission Systems sales y/y %', 'growth', 'pct', all=growth('rms_rev'))
    S('gm_space', '  Space sales y/y %', 'growth', 'pct', all=growth('space_rev'))
    S('gm_bk', '  Total backlog y/y %', 'growth', 'pct', all=growth('bk_tot'))
    S('gm_segop', '  Business segment operating profit y/y %', 'growth', 'pct', all=growth('g_segop'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating profit (GAAP) y/y %', 'growth', 'pct', all=growth('is_op'))
    S('gm_ni', '  Net earnings y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('gm_segm', '  Business segment operating margin %', 'pct', 'pct', all=ratio('g_segop', 'is_rev'))
    S('gm_inc', '  Incremental business segment operating margin (Δ segment OP / Δ net sales)', 'pct', 'pct', all=incr('g_segop', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_fascas_p', '  FAS/CAS pension adjustment in operating profit % of sales', 'pct', 'pct', all=ratio('ua_fascas', 'is_rev'))
    S('gc_aero', '  Contribution to net sales growth — Aeronautics (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR(({V("aero_rev")}-{P("aero_rev")})/{P("is_rev")},"")' if CTX.col.prior else None))
    S('gc_oth', '  Contribution to net sales growth — MFC + RMS + Space + other (pp)', 'growth', 'pct',
      all=lambda: (f'=IFERROR({V("gm_rev")}-{V("gc_aero")},"")' if CTX.col.prior else None))
    S('bk_tot', '  Memo: total backlog (period end)', 'memo', 'm', data='bk_tot', bs=True,
      fc=lambda: f'={V("aero_bk")}+{V("mfc_bk")}+{V("rms_bk")}+{V("space_bk")}',
      note='Reported total backlog (incl. legacy segments in their periods); forecast = Σ segment backlog roll-forwards (Ultra Maritime backlog not added).')
    S('bk_chk', '  Check: Σ segment backlog vs reported total (should be 0; 2006 sub-segment table n/a)', 'check', 'm',
      hist=lambda: (f'=IF(AND(ISNUMBER({V("bk_tot")}),ISNUMBER({V("aero_bk")})),IF(ABS({nsum(["aero_bk", "mfc_bk", "rms_bk", "space_bk", "isgs_bk", "es_bk"])}-{V("bk_tot")})<=1,0,ROUND({nsum(["aero_bk", "mfc_bk", "rms_bk", "space_bk", "isgs_bk", "es_bk"])}-{V("bk_tot")},0)),"")'
                    if CTX.col.year != 2006 else None))
    S('bk_cov', '  Total backlog ÷ last-twelve-month net sales (years)', 'pct', 'x2', all=lambda: (f'=IF(ISNUMBER({V("bk_tot")}),IFERROR({V("bk_tot")}/{LTM("is_rev")},""),"")' if LTM('is_rev') else None))
    S('kpi_h', '  Aircraft deliveries (units; release operating data)', 'sub', 'gen')
    S('dl_f35', '    F-35', 'memo', 'n0', data='dl_f35', flow=True)
    S('dl_f16', '    F-16', 'memo', 'n0', data='dl_f16', flow=True)
    S('dl_c130j', '    C-130J', 'memo', 'n0', data='dl_c130j', flow=True)
    S('dl_heli', '    Government helicopter programs (Sikorsky, from 2016)', 'memo', 'n0', data='dl_heli', flow=True)
    blank()
