"""Row specification of the BA Model sheet, part 1 (MLM template layout and process):
Commercial Airplanes deliveries by program × revenue per delivery × operating margin; Defense, Space & Security and Global
Services growth × margin; Boeing Capital / Other (history); unallocated items (core basis) and the pension line (FAS/CAS service
cost adjustment / unallocated pension) -> core operating earnings -> earnings from operations -> 2026 calibration -> cost drivers
-> income statement -> GAAP-to-core bridges -> growth & margins."""
from fw import *

def CH(r):
    return f'CHOOSE(MATCH({SW},{{"Bull","Base","Bear"}},0),${SBULL}${r},${SBASE}${r},${SBEAR}${r})'
def PT(name): return f'${SBASE}${SC[name]}'
SC = {}

def growth(key):
    def f():
        if CTX.col.prior is None: return None
        return f'=IF(AND(ISNUMBER({V(key)}),ISNUMBER({P(key)})),IF({P(key)}>0,IFERROR({V(key)}/{P(key)}-1,""),"n/m"),"")'
    return f
def ratio(n, d): return lambda: f'=IF(AND(ISNUMBER({V(n)}),ISNUMBER({V(d)})),IFERROR({V(n)}/{V(d)},""),"")'
def incr(n, d):
    def f():
        if CTX.col.prior is None: return None
        return f'=IFERROR(({V(n)}-{P(n)})/({V(d)}-{P(d)}),"")'
    return f
def nsum(keys): return '+'.join(f'N({V(k)})' for k in keys)
def ACT(key): return f'SUM({Q1}{R[key]}:{Q2}{R[key]})'      # 1H26 actual (Q1-Q2/26)
def ACT0(key): return f'SUM({PQ1}{R[key]}:{PQ2}{R[key]})'    # 1H25 actual (Q1-Q2/25)
def H2(key): return f'SUM({Q3E}{R[key]}:{QE}{R[key]})'       # 2H26 estimate (Q3E-Q4E)
def H25(key): return f'({QC[(2025, 3)].c}{R[key]}+{QC[(2025, 4)].c}{R[key]})'   # 2H25 actual (Q3-Q4/25)
def B1(key): return f'{LQ}{R[key]}'                          # 30-Jun-2026 balance
def E26a(key): return f'${E26}${R[key]}'

PROGS = [('737', '737 (Next-Generation / MAX)'), ('747', '747 (production ended 2023)'), ('767', '767 (commercial / freighter; tanker deliveries counted in BDS)'),
         ('777', '777 / 777X'), ('787', '787'), ('717', '717 (ended 2006)')]
GUIDED = {'737': 'out_d737', '787': 'out_d787'}
LEV = {'737': 'D737', '767': 'D767', '777': 'D777', '787': 'D787'}

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of the 2026 ranges (UNVERIFIED: earnings-call statements, not in EDGAR filings).'))
    r = 11
    SCEN_ROWS.append((r, 'out_hdr', V0['out_hdr'], 'High', 'Mid', 'Low', V0['out_note'])); r += 1
    for key, lab, (hi, mid, lo), nf, note in V0['outlook']:
        SC[key] = r; SCEN_ROWS.append((r, 'out', lab, hi, mid, lo, note, nf)); r += 1
    r += 1
    SCEN_ROWS.append((r, 'pt_hdr', 'Q3/Q4-26E point estimates (all cases; assumptions unless stated)', None, None, None, None)); r += 1
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
    S('sec_seg', 'SEGMENT P&L — COMMERCIAL AIRPLANES (deliveries × revenue per delivery) · DEFENSE, SPACE & SECURITY · GLOBAL SERVICES → CORE OPERATING EARNINGS', 'section',
      note='SEGMENT BUILD — modelling logic (BCA deliveries × revenue per delivery × margin; BDS / BGS growth × margin; + unallocated items (core basis) = core operating earnings; + FAS/CAS service cost adjustment = earnings from operations)')
    blank()
    # ---- Commercial Airplanes
    S('bca_hdr', 'Commercial Airplanes (BCA) — 737, 767, 777 / 777X, 787 commercial jetliners; incl. Spirit AeroSystems Boeing-related operations from 8-Dec-2025; '
      'commercial services moved to Global Services from Q3-17', 'block', note='COMMERCIAL AIRPLANES — modelling logic')
    S('del_h', '  Commercial airplane deliveries (units):', 'sub', 'gen')
    for k, lab in PROGS:
        key = f'del_{k}'
        kw = dict(data=key, flow=True, nf='m')
        if k in GUIDED:
            g = GUIDED[k]
            kw['qe'] = (lambda key=key, g=g: f'=({CH(SC[g])}-{ACT(key)})*IFERROR({P(key)}/{H25(key)},0.5)')
        elif k in ('767', '777'):
            kw['qe'] = (lambda key=key: f'={P(key)}*IFERROR({ACT(key)}/{ACT0(key)},1)')
        else:
            kw['qe'] = (lambda: '=0')
        kw['ae'] = (lambda k=k: '=' + CH(SC[LEV[k]][CTX.col.year])) if k in LEV else (lambda: '=0')
        note = None
        if k == '737':
            note = ('History: release deliveries table. Q3/Q4-26E: (2026 delivery target − 1H26 actual) split by the Q3:Q4-25 pattern (target ~500, UNVERIFIED call statement). '
                    '2027E+: scenario lever (production rate: 42/month Q4-25, 47/month from mid-2026, 52/month planned — releases / 10-Q).')
        elif k == '787':
            note = 'Q3/Q4-26E: 2026 target 90–100 (UNVERIFIED call statement) less 1H26; 787 production transitioning to 8/month (Q4-25 release). 2027E+: lever.'
        elif k == '767':
            note = 'Q3/Q4-26E: prior-year quarter × 1H26 y/y ratio. 767F production ends 2027 (assumption per program announcements in the 10-K); KC-46A tankers are BDS.'
        elif k == '777':
            note = 'Q3/Q4-26E: prior-year quarter × 1H26 y/y. 777X certification / first delivery assumed 2027 (lever).'
        S(key, f'    {lab}', 'line', note=note, **kw)
    S('del_tot', '  Total commercial deliveries', 'line_b', 'm', flow=True,
      all=lambda: '=' + '+'.join(f'N({V("del_" + k)})' for k, _ in PROGS))
    S('del_g', '    Deliveries y/y %', 'growth', 'pct', all=growth('del_tot'))
    S('del_pub', '  Memo: total deliveries as reported', 'memo', 'm', data='del_tot', flow=True)
    S('del_chk', '  Check: program deliveries vs total as reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("del_pub")}),ROUND({V("del_tot")}-{V("del_pub")},1),"")')
    S('bca_rpd', '  Revenue per delivery (BCA revenue ÷ deliveries, $m; includes non-delivery revenue)', 'line', 'm1',
      hist=lambda: f'=IFERROR({V("bca_rev")}/{V("del_tot")},"")', qe=lambda: f'=IFERROR({ACT("bca_rev")}/{ACT("del_tot")},"")',
      e26=lambda: f'=IFERROR({V("bca_rev")}/{V("del_tot")},"")',
      ae=lambda: f'={P("bca_rpd")}*(1+{V("bca_rpd_g")})',
      note='Q3/Q4-26E: 1H26 average (737-heavy mix, Spirit included). 2027E+: prior year × (1 + scenario lever: price escalation + widebody / 777X mix).')
    S('bca_rpd_g', '    Revenue per delivery y/y %', 'growth', 'pct', all=growth('bca_rpd'), ae=lambda: '=' + CH(SC['BCA_RPD'][CTX.col.year]))
    S('bca_rev', '  BCA revenues', 'line_b', 'm1', data='sr_bca', flow=True, fc=lambda: f'={V("del_tot")}*{V("bca_rpd")}',
      note='As reported (segment table). Forecast = deliveries × revenue per delivery.')
    S('bca_rev_g', '  BCA revenues y/y %', 'growth', 'pct', all=growth('bca_rev'))
    S('bca_oi', '  BCA earnings / (loss) from operations', 'line', 'm1', data='se_bca', flow=True, fc=lambda: f'={V("bca_rev")}*{V("bca_m")}',
      note='As reported (incl. reach-forward losses: 787 2016–21, 777X 2024–25, 767 / 737 abnormal costs). Forecast = revenues × margin.')
    S('bca_m', '  BCA operating margin %', 'pct', 'pct', all=ratio('bca_oi', 'bca_rev'), qe=lambda: '=' + CH(SC['out_bcam']),
      ae=lambda: '=' + CH(SC['BCA_M'][CTX.col.year]),
      note='Q3/Q4-26E: 2H26 margin assumption (scenario; 1H26 −4.2% incl. Spirit integration; company said BCA margins stay negative in 2026 — UNVERIFIED). 2027E+: lever.')
    S('bca_inc', '  Incremental BCA margin (Δ earnings / Δ revenues)', 'pct', 'pct', all=incr('bca_oi', 'bca_rev'))
    S('bca_bl', '  Memo: BCA backlog at period end ($m)', 'memo', 'm', data='bl_bca', bs=True)
    S('bca_bl_y', '  Memo: BCA backlog ÷ annual BCA revenues (years)', 'memo_calc', 'x',
      all=lambda: f'=IF(ISNUMBER({V("bca_bl")}),IFERROR({V("bca_bl")}/({V("bca_rev")}*{4 if CTX.col.q else 1}),""),"")')
    blank()
    # ---- Defense, Space & Security
    S('bds_hdr', 'Defense, Space & Security (BDS) — military aircraft, space & weapons (Integrated Defense Systems to 2009; Global Services & Support moved to BGS in Q3-17)',
      'block', note='DEFENSE, SPACE & SECURITY — modelling logic')
    S('bds_rev', '  BDS revenues', 'line_b', 'm1', data='sr_bds', flow=True, fc=lambda: f'={P("bds_rev")}*(1+{V("bds_g")})',
      note='As reported (2006–Q2-17 incl. Global Services & Support; 2010–11 = Σ sub-segments, no total printed). Forecast = prior year / prior-year quarter × (1 + growth).')
    S('bds_g', '  BDS revenues y/y %', 'growth', 'pct', all=growth('bds_rev'), qe=lambda: f'=IFERROR({ACT("bds_rev")}/{ACT0("bds_rev")}-1,0)',
      ae=lambda: '=' + CH(SC['BDS_G'][CTX.col.year]), note='Q3/Q4-26E: 1H26 y/y. 2027E+: scenario lever.')
    S('bds_oi', '  BDS earnings / (loss) from operations', 'line', 'm1', data='se_bds', flow=True, fc=lambda: f'={V("bds_rev")}*{V("bds_m")}',
      note='As reported (incl. fixed-price development charges: KC-46A, T-7A, MQ-25, VC-25B, Starliner, commercial crew).')
    S('bds_m', '  BDS operating margin %', 'pct', 'pct', all=ratio('bds_oi', 'bds_rev'), qe=lambda: f'={V("bds_m_pre")}+{QEa("cal_bdsm")}',
      ae=lambda: '=' + CH(SC['BDS_M'][CTX.col.year]), note='Q3/Q4-26E: 1H26 margin + calibration Δ (2026 BDS margin target). 2027E+: lever.')
    S('bds_m_pre', '  Q3/Q4-26E margin before calibration (1H26 margin)', 'driver', 'pct', qe=lambda: f'=IFERROR({ACT("bds_oi")}/{ACT("bds_rev")},0)')
    S('bds_inc', '  Incremental BDS margin', 'pct', 'pct', all=incr('bds_oi', 'bds_rev'))
    S('bds_bl', '  Memo: BDS backlog at period end ($m)', 'memo', 'm', data='bl_bds', bs=True)
    S('bds_leg_h', '  Legacy sub-segments, as originally reported (memo):', 'sub', 'gen')
    for k, lab in (('bma', 'Boeing Military Aircraft (2008–16)'), ('nss', 'Network & Space Systems (2006–16)'), ('gss', 'Global Services & Support (2008–Q2-17)'),
                   ('pems', 'Precision Engagement & Mobility Systems (2006–07)'), ('ss', 'Support Systems (2006–07)')):
        S(f'bds_l_{k}', f'    {lab} — revenues', 'memo', 'm1', data=f'sr_{k}', flow=True)
    S('bds_l_chk', '    Check: legacy sub-segments vs BDS revenues (should be 0)', 'check', 'm1',
      hist=lambda: (f'=IF(ISNUMBER({V("bds_l_nss")}),ROUND({nsum(["bds_l_bma", "bds_l_nss", "bds_l_gss", "bds_l_pems", "bds_l_ss"])}-{V("bds_rev")},1),"")'))
    blank()
    # ---- Global Services
    S('bgs_hdr', 'Global Services (BGS) — commercial & government services, parts, training, digital (formed Q3-17; Digital Aviation Solutions incl. Jeppesen sold 31-Oct-2025)',
      'block', note='GLOBAL SERVICES — modelling logic')
    S('bgs_rev', '  BGS revenues', 'line_b', 'm1', data='sr_bgs', flow=True, fc=lambda: f'={P("bgs_rev")}*(1+{V("bgs_g")})',
      note='As reported from Q3-17 (Q1/Q2-17 and earlier: services inside BCA / BDS).')
    S('bgs_g', '  BGS revenues y/y %', 'growth', 'pct', all=growth('bgs_rev'), qe=lambda: f'=IFERROR({ACT("bgs_rev")}/{ACT0("bgs_rev")}-1,0)',
      ae=lambda: '=' + CH(SC['BGS_G'][CTX.col.year]),
      note='Q3/Q4-26E: 1H26 y/y (1H25 includes the divested Digital Aviation Solutions business; Q4-25 two months). 2027E+: lever.')
    S('bgs_oi', '  BGS earnings from operations', 'line', 'm1', data='se_bgs', flow=True, fc=lambda: f'={V("bgs_rev")}*{V("bgs_m")}',
      note='As reported; Q4-25 includes the $9.6bn gain on the Digital Aviation Solutions sale (in "gain on dispositions").')
    S('bgs_m', '  BGS operating margin %', 'pct', 'pct', all=ratio('bgs_oi', 'bgs_rev'), qe=lambda: f'={V("bgs_m_pre")}+{QEa("cal_bgsm")}',
      ae=lambda: '=' + CH(SC['BGS_M'][CTX.col.year]), note='Q3/Q4-26E: 1H26 margin + calibration Δ (2026 BGS margin target). 2027E+: lever.')
    S('bgs_m_pre', '  Q3/Q4-26E margin before calibration (1H26 margin)', 'driver', 'pct', qe=lambda: f'=IFERROR({ACT("bgs_oi")}/{ACT("bgs_rev")},0)')
    S('bgs_inc', '  Incremental BGS margin', 'pct', 'pct', all=incr('bgs_oi', 'bgs_rev'))
    S('bgs_bl', '  Memo: BGS backlog at period end ($m)', 'memo', 'm', data='bl_bgs', bs=True)
    blank()
    # ---- Boeing Capital / Other / unallocated
    S('oth_hdr', 'Boeing Capital, Other segment, unallocated items and the pension line', 'block',
      note='BCC / OTHER / UNALLOCATED — history as reported; forecast: unallocated (core basis) and FAS/CAS as inputs')
    S('bcc_rev', '  Boeing Capital (BCC) revenues (separate segment to 2022; in unallocated from 2023)', 'line', 'm1', data='sr_bcc', flow=True, fc=lambda: '=0')
    S('bcc_oi', '  BCC earnings from operations', 'line', 'm1', data='se_bcc', flow=True, fc=lambda: '=0')
    S('os_rev', '  Other segment revenues (to 2013; Engineering, Operations & Technology, Connexion, Shared Services)', 'line', 'm1', data='sr_oth', flow=True, fc=lambda: '=0')
    S('os_oi', '  Other segment earnings / (loss)', 'line', 'm1', data='se_oth', flow=True, fc=lambda: '=0')
    S('un_rev', '  Unallocated items, eliminations and other — revenues', 'line', 'm1', data='sr_unal', flow=True,
      qe=lambda: f'={ACT("un_rev")}/2', ae=lambda: f'=({V("bca_rev")}+{V("bds_rev")}+{V("bgs_rev")})*{V("un_rev_pct")}')
    S('un_rev_pct', '    % of segment revenues', 'pct', 'pct', all=lambda: f'=IFERROR({V("un_rev")}/({V("bca_rev")}+{V("bds_rev")}+N({V("bgs_rev")})),"")', ae_in=V0['un_rev_pct'])
    S('un_rep', '  Unallocated items, eliminations and other — earnings, as reported', 'memo', 'm1', data='se_unal', flow=True,
      note='As reported in the segment table: to 2017 includes unallocated pension / postretirement expense (and the 2006 DOJ settlement, $571m); from 2018 excludes the FAS/CAS service cost adjustment (separate line).')
    S('un_core', '  Unallocated items, eliminations and other — core basis (excl. pension items)', 'line', 'm1', flow=True,
      hist=lambda: (f'={V("un_rep")}-N({V("pens_item")})' if CTX.col.year < 2018 else f'={V("un_rep")}'),
      qe=lambda: f'={PT("pt_unal")}', ae=lambda: f'=({V("bca_rev")}+{V("bds_rev")}+{V("bgs_rev")})*{V("un_pct")}',
      note=('Share-based plans, deferred compensation, capitalized interest, unallocated R&D, eliminations and other (2025 incl. the $445m DOJ non-prosecution agreement charge). '
            'History: as reported less the pension item to 2017. Q3/Q4-26E: point estimate. 2027E+: % of segment revenues.'))
    S('un_pct', '    Unallocated (core basis) % of segment revenues', 'pct', 'pct', all=lambda: f'=IFERROR({V("un_core")}/({V("bca_rev")}+{V("bds_rev")}+N({V("bgs_rev")})),"")',
      ae_in=V0['un_pct'])
    S('pens_item', '  Pension line in earnings from operations: FAS/CAS service cost adjustment (2018+, income) / unallocated pension & postretirement expense (to 2017)', 'line', 'm1',
      data='pens_item', flow=True, qe=lambda: f'={PT("pt_fascas")}', ae_in=V0['fascas'],
      note=('2018+: FAS/CAS service cost adjustment (CAS pension / postretirement cost allocated to US government contracts less FAS service cost). To 2017: −unallocated pension and '
            'postretirement expense (unallocated items detail; 2006–07 not disclosed). Q3/Q4-26E: 1H26 run-rate; 2027E+: input (declining CAS recovery).'))
    blank()
    # ------------------------------------------------------------------ future M&A lever
    S('m_hdr', 'Future acquisitions (M&A lever — none assumed: deleveraging after the Spirit acquisition)', 'block',
      note='M&A LEVER — acquired revenue = spend ÷ EV/sales; mid-year convention (scenario spend 0 in all cases)')
    S('m_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_in=0.0, ae=lambda: f'=MAX(0,{CH(SC["MNA"][CTX.col.year])})', note=V0['mna_note'])
    S('m_mult', '  Purchase multiple — EV / sales (x)', 'driver', 'x2', ae_in=1.0, e26_in=0.0,
      note='Spirit AeroSystems: $8.4bn total consideration (10-K Note 2) for the Boeing-related operations. 1.0x input (assumption; unused at zero spend).')
    S('m_acq_sales', '  Annualised revenue acquired in the year', 'line', 'm', e26_in=0.0, ae=lambda: f'=IFERROR({V("m_spend")}/{V("m_mult")},0)')
    S('m_rev', '  Revenue from future acquisitions', 'line_b', 'm', e26_in=0.0, ae=lambda: f'={P("m_rev")}+0.5*{V("m_acq_sales")}+0.5*{P("m_acq_sales")}')
    S('m_m', '  Operating margin of acquired businesses %', 'driver', 'pct', e26_in=0.0, ae_in=0.08)
    S('m_oi', '  Earnings from future acquisitions', 'line', 'm', e26_in=0.0, ae=lambda: f'={V("m_rev")}*{V("m_m")}')
    S('m_ppe', '  PP&E % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.25)
    S('m_intp', '  Acquired intangibles % of spend', 'driver', 'pct', e26_in=0.0, ae_in=0.05, note='Spirit PPA: intangibles $109m (1%), PP&E $2.4bn, goodwill $10.0bn.')
    blank()

    # ------------------------------------------------------------------ group total & calibration
    S('g_hdr', 'Group Total — revenues, core operating earnings & earnings from operations (segment build) → 2026 calibration', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Total revenues (segment build)', 'total', 'm1',
      all=lambda: f'={nsum(["bca_rev", "bds_rev", "bgs_rev", "bcc_rev", "os_rev", "un_rev"])}' + ('' if CTX.col.kind in HISTK else f'+N({V("m_rev")})'),
      note='Σ segments + BCC + Other + unallocated / eliminations (+ future acquisitions).')
    S('g_rev_g', '  Total revenues y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: segment build vs consolidated revenues (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_rev_pub")}),ROUND({V("g_rev")}-{V("is_rev_pub")},1),"")')
    S('g_core', 'Core operating earnings (segment build)', 'total', 'm1',
      all=lambda: f'={nsum(["bca_oi", "bds_oi", "bgs_oi", "bcc_oi", "os_oi", "un_core"])}' + ('' if CTX.col.kind in HISTK else f'+N({V("m_oi")})'),
      note='Σ segment earnings + BCC + Other + unallocated items (core basis). Company "core operating earnings" (non-GAAP, published from FY2011 / Q4-12). Drives the GAAP P&L.')
    S('g_core_m', '  Core operating margin %', 'pct', 'pct', all=ratio('g_core', 'g_rev'))
    S('g_efo', 'Earnings / (loss) from operations (segment build: core + pension line)', 'total', 'm1', all=lambda: f'={V("g_core")}+N({V("pens_item")})')
    S('g_chk_efo', '  Check: segment build vs reported earnings from operations (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_efo_pub")}),ROUND({V("g_efo")}-{V("is_efo_pub")},1),"")')
    S('g_chk_core', '  Check: segment build vs core operating earnings bridge (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("o_core")}),ROUND({V("g_core")}-{V("o_core")},1),"")')
    S('cal_h', '  2026 calibration (Q3/Q4-26E) — guidance end-points are UNVERIFIED (earnings-call statements; Boeing has published no numeric outlook in its releases since 2019):', 'sub', 'gen')
    for k, g, lab in (('737', 'out_d737', '737'), ('787', 'out_d787', '787')):
        S(f'cal_d{k}', f'  Memo: 2026 {lab} delivery target (scenario end-point)', 'memo', 'm', e26=lambda g=g: '=' + CH(SC[g]))
        S(f'cal_d{k}_chk', f'  Check: 2026E {lab} deliveries vs target (should be 0)', 'check', 'm', e26=lambda k=k: f'=ROUND({V("del_" + k)}-{V("cal_d" + k)},1)')
    for s, g, lab in (('bds', 'out_bdsm', 'BDS'), ('bgs', 'out_bgsm', 'BGS')):
        S(f'cal_{s}t', f'  Memo: 2026 {lab} operating margin target (scenario end-point)', 'memo', 'pct', e26=lambda g=g: '=' + CH(SC[g]))
        S(f'cal_{s}m', f'  Calibration: Δ {lab} margin applied to Q3/Q4-26E (closed form)', 'driver', 'pct',
          qe=lambda s=s: (f'=({E26a("cal_" + s + "t")}*{E26a(s + "_rev")}-{ACT(s + "_oi")}-{V(s + "_m_pre", Q3E)}*{Q3E}{R[s + "_rev"]}-{V(s + "_m_pre", QE)}*{QE}{R[s + "_rev"]})'
                          f'/({Q3E}{R[s + "_rev"]}+{QE}{R[s + "_rev"]})'),
          note=f'Solves one uniform shift on the 1H26 {lab} margin so that the 2026E margin = the target for the active scenario.' if s == 'bds' else None)
        S(f'cal_{s}_chk', f'  Check: 2026E {lab} margin vs target (should be 0.0%)', 'check', 'pct', e26=lambda s=s: f'=ROUND({V(s + "_m")}-{V("cal_" + s + "t")},4)')
    S('cal_fcf', '  Memo: 2026 free cash flow target (scenario end-point; solved through year-end inventories — see balance sheet)', 'memo', 'm', e26=lambda: '=' + CH(SC['out_fcf']))
    S('cal_fcf_chk', '  Check: 2026E free cash flow vs target (should be 0)', 'check', 'm', e26=lambda: f'=ROUND({V("fcf")}-{V("cal_fcf")},1)')
    S('cal_bcam', '  Memo: 2H26 BCA margin (scenario assumption — information; company indicated negative BCA margins in 2026, UNVERIFIED)', 'memo', 'pct', e26=lambda: '=' + CH(SC['out_bcam']))
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A, pension and other income', 'block', note='COST DRIVERS — inputs that drive forecast cost lines (Q3/Q4-26E: point estimates / 1H26 ratios; 2027E+: % of revenues or inputs)')
    S('d_dda', '  Depreciation & amortization (cash-flow statement)', 'line', 'm1', data='cf_dda', flow=True, qe=lambda: f'={PT("pt_dda")}', ae=lambda: f'={V("is_rev")}*{V("d_dda_pct")}',
      note='Q3/Q4-26E: 1H26 run-rate (Spirit PP&E added $2.4bn). 2027E+: % of revenues.')
    S('d_dda_pct', '  D&A % of revenues', 'pct', 'pct', all=ratio('d_dda', 'is_rev'), ae_in=V0['dda_pct'])
    S('d_amort_sch', '  Memo: amortization of acquired intangibles — 10-K schedule (included in D&A)', 'memo', 'm1', ae_in=V0['amort_sched'], note=V0['amort_note'])
    S('d_ga', '  G&A % of revenues', 'pct', 'pct', all=ratio('is_ga', 'is_rev'), qe=lambda: f'=IFERROR({ACT("is_ga")}/{ACT("is_rev")},"")', ae_in=V0['ga_pct'],
      note='Q3/Q4-26E: 1H26 ratio; 2027E+: input. Cost of products & services is implied (earnings from operations from the build).')
    S('d_rd', '  R&D % of revenues', 'pct', 'pct', all=ratio('is_rd', 'is_rev'), qe=lambda: f'=IFERROR({ACT("is_rd")}/{ACT("is_rev")},"")', ae_in=V0['rd_pct'])
    S('d_sbc', '  Share-based plans expense (cash-flow statement)', 'line', 'm1', data='cf_sbc', flow=True, qe=lambda: f'={ACT("d_sbc")}/2', ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}')
    S('d_sbc_pct', '  Share-based plans expense % of revenues', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_401k', '  Treasury shares issued for 401(k) contributions (non-cash; cash-flow statement, from 2020)', 'line', 'm1', data='cf_401k', flow=True,
      qe=lambda: f'={ACT("d_401k")}/2', ae=lambda: f'={P("d_401k")}*(1+{V0["k401_g"]})',
      note='Company match paid in treasury shares since 2020 (non-cash expense; adds to equity and to the share count). 2027E+: +3% p.a. (assumption).')
    S('d_nonop', '  Non-operating pension & postretirement income / (expense) (in other income; core reconciliation, 2018+)', 'line', 'm1', data='nonop_inc', flow=True,
      qe=lambda: f'={PT("pt_nonop")}', ae_in=V0['nonop'],
      note='2018+ (ASU 2017-07): non-service pension cost below earnings from operations; adjusted out of core EPS. 2026 turned to an expense (1H26 −$129m). 2027E+: input (assumption).')
    S('d_intinc', '  Interest & other income (other income, net excl. non-operating pension)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("is_othinc")}),{V("is_othinc")}-N({V("d_nonop")}),"")', qe=lambda: f'={PT("pt_intinc")}',
      ae=lambda: f'=({P("bs_cash")}+{P("bs_sti")})*{V("ds_r_cash")}',
      note='Mostly interest on cash and short-term investments. Q3/Q4-26E: point estimate; 2027E+: yield × opening cash & short-term investments.')
    S('d_opinv', '  Income / (loss) from operating investments (ULA and other JVs; input)', 'line', 'm1', qe_in=0.0, ae_in=V0['opinv'])
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENTS OF OPERATIONS (US GAAP, as presented)', 'section',
      note='CONSOLIDATED IS — forecast logic (earnings from operations from the build; cost of products & services implied)')
    S('is_rev', 'Total revenues', 'total', 'm1', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Sales of products + sales of services. Forecast linked to the segment build.')
    S('is_rev_pub', '  Memo: total revenues as reported', 'memo', 'm1', data='rev', flow=True)
    S('is_cogs', 'Cost of products & services', 'line', 'm1', data='cogs', flow=True, fc=lambda: f'={V("is_rev")}-{V("is_gp")}-{V("is_bccint")}')
    S('is_bccint', 'Boeing Capital interest expense (to 2023)', 'line', 'm1', data='bcc_int', flow=True, fc=lambda: '=0')
    S('is_gp', 'Gross profit (revenues − cost of products & services − BCC interest)', 'line_b', 'm1',
      hist=lambda: f'={V("is_rev")}-{V("is_cogs")}-{V("is_bccint")}',
      fc=lambda: f'={V("is_efo")}+{V("is_ga")}+{V("is_rd")}-{V("is_opinv")}-{V("is_gain")}+{V("is_othop")}',
      note='Forecast = earnings from operations + G&A + R&D − income from operating investments − gains (implied by the build).')
    S('is_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('is_opinv', 'Income / (loss) from operating investments, net', 'line', 'm1', data='opinv', flow=True, fc=lambda: f'={V("d_opinv")}')
    S('is_ga', 'General and administrative expense', 'line', 'm1', data='ga', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_ga")}')
    S('is_rd', 'Research and development expense, net', 'line', 'm1', data='rd', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_rd")}')
    S('is_gain', 'Gain / (loss) on dispositions, net', 'line', 'm1', data='gain', flow=True, fc=lambda: '=0',
      note='FY2025: $9.6bn gain on the Digital Aviation Solutions divestiture (Q4-25; inside BGS earnings, in core EPS).')
    S('is_othop', 'Other operating items shown separately (FY2006: settlement with the U.S. Department of Justice, net)', 'line', 'm1', data='oth_op', flow=True, fc=lambda: '=0')
    S('is_efo', 'Earnings / (loss) from operations', 'total', 'm1',
      hist=lambda: f'={V("is_gp")}+{V("is_opinv")}-{V("is_ga")}-{V("is_rd")}+{V("is_gain")}-{V("is_othop")}',
      fc=lambda: f'={V("g_efo")}', note='Forecast = core operating earnings + FAS/CAS service cost adjustment (segment build).')
    S('is_efo_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_efo', 'is_rev'))
    S('is_efo_pub', '  Memo: earnings from operations as reported', 'memo', 'm1', data='efo', flow=True)
    S('is_efo_chk', '  Check: statement lines vs reported earnings from operations (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_efo_pub")}),ROUND({V("is_efo")}-{V("is_efo_pub")},1),"")')
    S('is_othinc', 'Other income / (expense), net', 'line', 'm1', data='oth_inc', flow=True, fc=lambda: f'={V("d_nonop")}+{V("d_intinc")}',
      note='Interest income on cash & investments + non-operating pension / postretirement income (2018+).')
    S('is_int', 'Interest and debt expense', 'line', 'm1', data='int_exp', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: f'={P("ds_notes")}*{V("ds_r_notes")}+{P("ds_rev")}*{V("ds_r_rev")}',
      note='Q3/Q4-26E: point estimate (Q2-26 $600m on $45.9bn). 2027E+ = rate × opening notes + rate × opening revolver / CP (no circularity).')
    S('is_ebt', 'Earnings / (loss) before income taxes', 'line_b', 'm1', all=lambda: f'={V("is_efo")}+{V("is_othinc")}-{V("is_int")}')
    S('is_tax', 'Income tax (expense) / benefit — shown as expense', 'line', 'm1', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=lambda: f'=IFERROR({V("is_tax")}/{V("is_ebt")},"")', qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Valuation allowance ($9.8bn at YE25) keeps the GAAP rate low while losses / credits are used. Forecast inputs (assumption).')
    S('is_nicont', 'Net earnings / (loss) from continuing operations', 'line', 'm1', all=lambda: f'={V("is_ebt")}-{V("is_tax")}')
    S('is_disc', 'Discontinued operations, net of taxes (and FY2006 cumulative effect of accounting change)', 'line', 'm1', data='disc', flow=True, fc=lambda: '=0')
    S('is_ni', 'Net earnings / (loss)', 'total', 'm1', all=lambda: f'={V("is_nicont")}+{V("is_disc")}')
    S('is_ni_pub', '  Memo: net earnings / (loss) as reported (incl. noncontrolling interests)', 'memo', 'm1', data='ni', flow=True)
    S('is_ni_chk', '  Check: net earnings vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),ROUND({V("is_ni")}-{V("is_ni_pub")},1),"")')
    S('is_nci', '  Less: net earnings / (loss) attributable to noncontrolling interests', 'line', 'm1', data='nci', flow=True, fc=lambda: '=0')
    S('is_niattr', 'Net earnings / (loss) attributable to Boeing shareholders', 'line_b', 'm1', all=lambda: f'={V("is_ni")}-{V("is_nci")}')
    S('is_pref', '  Less: mandatory convertible preferred stock dividends (6.00%, issued Oct-2024; converts Oct-2027)', 'line', 'm1', data='pref', flow=True,
      qe=lambda: f'={PT("pt_pref")}', ae_in=V0['pref_div'],
      note='$5.75bn liquidation preference × 6% = $345m p.a. ($86.25m a quarter); 2027E accrues to the 15-Oct-2027 conversion (288 / 365 days, assumption).')
    S('is_nicom', 'Net earnings / (loss) available to common shareholders', 'total', 'm1', all=lambda: f'={V("is_niattr")}-{V("is_pref")}')
    S('is_dda', '  Memo: depreciation & amortization', 'memo_calc', 'm1', all=lambda: f'={V("d_dda")}')
    S('is_sbc', '  Memo: share-based plans expense', 'memo_calc', 'm1', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share — common stock)', 'sub', 'gen')
    S('mcps_f', '  Memo: preferred dividends added back (1 = if-converted, mandatory convertible preferred dilutive)', 'memo', 'gen', data='mcps_ifconv', flow=False,
      qe_in=0, ae=lambda: (f'=IF({V("is_niattr")}>0,1,0)' if CTX.col.year == 2027 else '=0'))
    S('eps_num', '  EPS numerator (net earnings available to common; attributable when if-converted)', 'line', 'm1',
      all=lambda: f'=IF(N({V("mcps_f")})=1,{V("is_niattr")},{V("is_nicom")})')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={PQ("sh_dil")}+{ACT("d_401k")}/2/{E26a("v_px")}',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})+{V("ds_dil")}+IF(N({V("mcps_f")})=1,{V("mc_sh")}*{V0["mcps_frac"]},0)',
      note='Q3/Q4-26E: prior quarter + 401(k) treasury-share issuance at the model price (loss periods: diluted = basic). 2027E+: average shares + dilutive awards (+ preferred if-converted shares until conversion when dilutive).')
    S('eps_dil', 'Diluted earnings / (loss) per share ($)', 'eps_total', 'ps', all=lambda: f'=IFERROR({V("eps_num")}/{V("sh_dil")},"")')
    S('eps_dil_g', '  Diluted EPS y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: diluted EPS as reported ($)', 'eps_memo', 'ps', data='eps_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01 rounding, ±0.02 above $10)', 'check', 'ps',
      hist=lambda: ('="n/c"' if CTX.col.year == 2006 and CTX.col.q is None else
                    f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=IF(ABS({V("eps_pub")})>=10,0.0201,0.0101),0,ROUND({V("eps_dil")}-{V("eps_pub")},2)),"n/p")'))
    S('dps', '  Cash dividends paid per share ($; suspended from Q2-2020)', 'line', 'ps', data='dps', flow=True, qe_in=0.0, ae_in=V0['dps'])
    blank()

    # ------------------------------------------------------------------ RECON 1: earnings from operations -> core operating earnings
    S('sec_r1', 'RECONCILIATION: EARNINGS FROM OPERATIONS → CORE OPERATING EARNINGS (company non-GAAP definition, published from FY2011)', 'section',
      note='CORE OPERATING EARNINGS — 2011–17: + unallocated pension & postretirement expense; 2018+ (ASU 2017-07): − FAS/CAS service cost adjustment')
    S('o_efo', 'Earnings / (loss) from operations (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_efo")}')
    S('o_pens', '  (−) FAS/CAS service cost adjustment (2018+) / (+) unallocated pension & postretirement expense (to 2017)', 'line', 'm1',
      all=lambda: f'=-N({V("pens_item")})')
    S('o_core', '  = Core operating earnings (model bridge)', 'total', 'm1', all=lambda: f'={V("o_efo")}+{V("o_pens")}',
      note='2006–07: pension detail not disclosed (= GAAP, flagged); 2008–10: model rebuild from the unallocated detail (not published).')
    S('o_core_m', '  Core operating margin %', 'pct', 'pct', all=ratio('o_core', 'is_rev'))
    S('o_pub', '  Company-published core operating earnings', 'memo', 'm1', data='core_oe_pub', flow=True)
    S('o_chk', '  Check: model bridge vs company-published (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("o_pub")}),ROUND({V("o_core")}-{V("o_pub")},1),"n/p")')
    S('o_def', '  Definition / basis (company core definition in force)', 'text', 'gen',
      note='Basis changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('o_g', '  Core operating earnings y/y %', 'growth', 'pct', all=growth('o_core'))
    S('o_inc', '  Incremental core operating margin (Δ core operating earnings / Δ revenues)', 'pct', 'pct', all=incr('o_core', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: net earnings -> EBITDA -> adjusted EBITDA (model)
    S('sec_r2', 'RECONCILIATION: NET EARNINGS → EARNINGS FROM OPERATIONS → EBITDA → ADJUSTED EBITDA (model definitions; Boeing publishes no EBITDA)', 'section',
      note='EBITDA (MODEL) — net earnings + taxes + interest & debt expense − other income = earnings from operations; + D&A = EBITDA; − pension line = adjusted EBITDA (core basis)')
    S('r_ni', 'Net earnings / (loss) (GAAP, incl. noncontrolling interests)', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('r_disc', '  (−) Discontinued operations / accounting change', 'line', 'm1', all=lambda: f'=-{V("is_disc")}')
    S('r_tax', '  (+) Income taxes', 'line', 'm1', all=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest and debt expense', 'line', 'm1', all=lambda: f'={V("is_int")}')
    S('r_oth', '  (−) Other income, net', 'line', 'm1', all=lambda: f'=-{V("is_othinc")}')
    S('r_efo', '  = Earnings / (loss) from operations', 'line_b', 'm1', all=lambda: f'={V("r_ni")}+{V("r_disc")}+{V("r_tax")}+{V("r_int")}+{V("r_oth")}')
    S('r_chk', '  Check: bridge vs earnings from operations (should be 0)', 'check', 'm1', all=lambda: f'=ROUND({V("r_efo")}-{V("is_efo")},1)')
    S('r_dda', '  (+) Depreciation & amortization', 'line', 'm1', all=lambda: f'={V("d_dda")}')
    S('r_ebitda', '  = EBITDA (model)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_dda")}),{V("r_efo")}+{V("r_dda")},"")')
    S('r_pens', '  (−) FAS/CAS service cost adjustment / (+) unallocated pension expense', 'line', 'm1', all=lambda: f'={V("o_pens")}')
    S('r_adj', '  = Adjusted EBITDA (model: core operating earnings + D&A)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{V("r_ebitda")}+{V("r_pens")},"")',
      note='Model definition (Boeing publishes no EBITDA): core operating earnings + D&A. Charges (reach-forward losses, DOJ) and the 2025 divestiture gain are not removed. Used for leverage and EV / EBITDA.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_ebit_h', 'To adjusted EBIT (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_ebit', '  = Adjusted EBIT (= core operating earnings; full-cost: after all D&A and share-based plans)', 'total', 'm1', all=lambda: f'={V("o_core")}')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_gain', '  Memo: gain on dispositions inside core earnings (excluded from NOPAT; FY2025 Digital Aviation Solutions $9.6bn)', 'memo_calc', 'm1', all=lambda: f'={V("is_gain")}')
    blank()

    # ------------------------------------------------------------------ RECON 3: core EPS
    S('sec_r3', 'RECONCILIATION: DILUTED EPS → CORE EARNINGS PER SHARE (company non-GAAP definition)', 'section',
      note='CORE EPS — GAAP diluted EPS − FAS/CAS service cost adjustment − non-operating pension & postretirement income + deferred taxes on the adjustments (2018+); to 2017: + unallocated pension & postretirement expense, after tax')
    S('e_ni', 'EPS numerator — net earnings available to common shareholders (GAAP)', 'line_b', 'm1', all=lambda: f'={V("eps_num")}')
    S('e_pens', '  (+/−) Pension line in earnings from operations (pre-tax; bridge above)', 'line', 'm1', all=lambda: f'={V("o_pens")}')
    S('e_nonop', '  (+) Non-operating pension & postretirement expense / (−) income (2018+)', 'line', 'm1', all=lambda: f'=-N({V("d_nonop")})')
    S('e_tax', '  (+/−) Provision for deferred income taxes on the adjustments', 'line', 'm1', flow=True,
      hist=lambda: (f'=IF(ISNUMBER({V("e_taxpub")}),{V("e_taxpub")},IF(ISNUMBER({V("e_pub")}),({V("e_pub")}-{V("eps_pub")})*{V("e_sh")}-{V("e_pens")}-{V("e_nonop")},'
                    f'-{V0["tax_old"]}*({V("e_pens")}+{V("e_nonop")})))'),
      fc=lambda: f'=-{V("e_rate")}*({V("e_pens")}+{V("e_nonop")})',
      note=('2018+: as published ("calculated using the U.S. corporate statutory tax rate"). 2011–17: derived = (published core EPS − GAAP EPS) × diluted shares − pre-tax item. '
            '2008–10 (not published): model at the 35% statutory rate. Forecast: −21% × pre-tax adjustments.'))
    S('e_taxpub', '  Memo: company-published provision for deferred taxes on adjustments (2018+)', 'memo', 'm1', data='core_dtax', flow=True)
    S('e_rate', '  Tax rate on adjustments (U.S. statutory, company method)', 'pct', 'pct', qe_in=0.21, ae_in=0.21)
    S('e_coreni', '  = Core earnings / (loss) for EPS (model bridge)', 'total', 'm1', all=lambda: f'={V("e_ni")}+{V("e_pens")}+{V("e_nonop")}+{V("e_tax")}')
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'={V("sh_dil")}')
    S('e_eps', 'Core earnings / (loss) per share ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_coreni', 'e_sh'))
    S('e_pub', '  Company-published core EPS ($)', 'eps_memo', 'ps', data='core_eps_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.015 rounding, ±0.025 in Q4-20)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0251,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_def', '  Definition / basis (company core EPS definition in force)', 'text', 'gen')
    S('e_g', '  Core EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Revenues y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_del', '  Commercial deliveries y/y %', 'growth', 'pct', all=growth('del_tot'))
    S('gm_bca', '  BCA revenues y/y %', 'growth', 'pct', all=growth('bca_rev'))
    S('gm_bds', '  BDS revenues y/y %', 'growth', 'pct', all=growth('bds_rev'))
    S('gm_bgs', '  BGS revenues y/y %', 'growth', 'pct', all=growth('bgs_rev'))
    S('gm_core', '  Core operating earnings y/y %', 'growth', 'pct', all=growth('o_core'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_eps', '  Core EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('gm_core_m', '  Core operating margin %', 'pct', 'pct', all=ratio('o_core', 'is_rev'))
    S('gm_inc', '  Incremental core operating margin', 'pct', 'pct', all=incr('o_core', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_efo', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_niattr', 'is_rev'))
    S('gm_ga', '  G&A % of revenues', 'pct', 'pct', all=ratio('is_ga', 'is_rev'))
    S('gm_rd', '  R&D % of revenues', 'pct', 'pct', all=ratio('is_rd', 'is_rev'))
    blank()

def QEa(key): return f'${QE}${R[key]}'
