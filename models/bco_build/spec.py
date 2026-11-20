"""Row specification of the BCO Model sheet, part 1 (MLM template layout and process):
segment build (North America / Latin America / Europe / Rest of World: revenue = prior year x (1 + organic + acquisitions-dispositions
+ currency), segment operating profit at the segment margin) -> corporate expenses -> legacy segment structures (memo) ->
NCR Atleos acquisition block (pending; toggle) -> group total & Q4/26 guidance calibration -> cost drivers -> income statement ->
GAAP-to-non-GAAP bridges -> growth & margins."""
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
def tol(a, b, t=0.15, nd=1): return f'IF(ABS({a}-({b}))<={t},0,ROUND({a}-({b}),{nd}))'

SEG = [('na', 'North America', 'NA'), ('la', 'Latin America', 'LA'), ('eu', 'Europe', 'EU'), ('row', 'Rest of World', 'ROW')]
SEGK = [s for s, _, _ in SEG]
ITEMS = [('restr', 'Reorganization and restructuring'), ('acq', 'Acquisitions and dispositions (incl. amortization of acquisition-related intangibles)'),
         ('arg', 'Argentina highly inflationary impact'), ('ven', 'Venezuela operations (deconsolidated 30-Jun-2018)'),
         ('transf', 'Transformation initiatives / NCR Atleos acquisition costs'), ('ret', 'Retirement plans (in operating profit to 2016)'),
         ('oth', 'Other items (legal, compliance, loss and incident matters; 2009–14 total of all items)')]

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of the Q4 2026 guidance ranges.'))
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
    SCEN_ROWS.append((r, 'lev', '  Net debt / adjusted EBITDA below which surplus cash is returned via buybacks (x) — 2027E+', *V0['lev'], V0['lev_note']))
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
    S('sec_seg', 'SEGMENT P&L — NORTH AMERICA · LATIN AMERICA · EUROPE · REST OF WORLD (revenue growth = organic + acquisitions / dispositions + currency; segment operating profit)', 'section',
      note='SEGMENT BUILD — modelling logic (segment revenue → segment operating profit at the segment margin → − corporate expenses = non-GAAP operating profit → − other items not allocated to segments = GAAP operating profit)')
    blank()
    descr = {'na': "North America (operations in the U.S. and Canada, including the Brink's Global Services line of business)",
             'la': 'Latin America (Latin American countries where Brink\'s has an ownership interest, including the BGS line of business; Argentina under highly inflationary accounting from Q3/18)',
             'eu': 'Europe (European countries, other than operations that primarily provide BGS services; G4S cash operations acquired in 2020)',
             'row': 'Rest of World (Middle East, Africa and Asia; European operations that primarily provide BGS services; Malaysia subsidiaries deconsolidated in Q3/26)'}
    for s, title, code in SEG:
        first = s == 'na'
        S(f'{s}_hdr', descr[s], 'block', note=f'{title.upper()} — modelling logic')
        S(f'{s}_rev', f'  {title} — segment revenues', 'line_b', 'm1', data=f'{s}_rev', flow=True,
          qe=lambda s=s: f'={P(s + "_rev")}*(1+{V(s + "_g")})', ae=lambda s=s: f'={P(s + "_rev")}*(1+{V(s + "_g")})',
          note=('Current four-segment basis (from 2019; 2019 as recast in the fourth-quarter 2020 release). Q4/26E and 2027E+: prior-year period × (1 + organic + acquisitions / dispositions + currency).') if first else None)
        S(f'{s}_g', '    Revenue y/y %', 'growth', 'pct', all=growth(f'{s}_rev'),
          qe=lambda s=s: f'={V(s + "_org")}+{V(s + "_acq")}+{V(s + "_fx")}', ae=lambda s=s: f'={V(s + "_org")}+{V(s + "_acq")}+{V(s + "_fx")}')
        S(f'{s}_org', '    Organic growth % (organic change ÷ prior-year revenue)', 'pct', 'pct', data=f'g_{s}_orgp',
          qe=lambda s=s: f'={V(s + "_org_pre")}+{QEa("cal_g")}', ae=lambda s=s, code=code: '=' + CH(SC[f'{code}_ORG'][CTX.col.year]),
          note=('History: organic change ÷ prior-year revenue, both from the "nQ vs" table of each quarterly release (whole $m; segment detail from Q4/20). '
                'Q4/26E: 9M 2026 average + revenue-guidance calibration Δ (Group block). 2027E+: scenario lever.') if first else None)
        S(f'{s}_org_pre', '    Q4/26E organic growth before calibration (average of Q1–Q3/26)', 'driver', 'pct',
          qe=lambda s=s: f'=AVERAGE({Q1}{R[s + "_org"]}:{Q3}{R[s + "_org"]})')
        S(f'{s}_acq', '    Acquisitions / dispositions %', 'pct', 'pct', data=f'g_{s}_acqp', qe_in=V0['acq_q4'][s], ae_in=V0['acq_ae'][s],
          note=V0['acq_note'] if s == 'row' else None)
        S(f'{s}_fx', '    Currency effect % (incl. Argentina devaluation under highly inflationary accounting)', 'pct', 'pct', data=f'g_{s}_fxp',
          qe_in=V0['fx_q4'][s], ae_in=V0['fx_ae'][s], note=V0['fx_note'] if first else None)
        S(f'{s}_gt', '    Memo: total change % per the release table (current ÷ prior-year period, whole $m)', 'memo', 'pct', data=f'g_{s}_totp')
        S(f'{s}_gchk', '    Check: organic + acquisitions / dispositions + currency vs table change (should be 0; ±1.2pp rounding of whole-$m tables)', 'check', 'pct2',
          hist=lambda s=s: f'=IF(AND(ISNUMBER({V(s + "_gt")}),ISNUMBER({V(s + "_org")})),{tol(V(s + "_gt"), V(s + "_org") + "+" + V(s + "_acq") + "+" + V(s + "_fx"), 0.012, 3)},"")')
        S(f'{s}_op', f'  {title} — segment operating profit', 'line', 'm1', data=f'{s}_op', flow=True,
          qe=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}', ae=lambda s=s: f'={V(s + "_rev")}*{V(s + "_m")}',
          note='Segment operating profit (company measure: before corporate expenses and other items not allocated to segments). Forecast = segment revenue × segment margin.' if first else None)
        S(f'{s}_m', '    Segment operating margin %', 'pct', 'pct', all=ratio(f'{s}_op', f'{s}_rev'),
          qe=lambda s=s: f'={V(s + "_m_pre")}+{QEa("cal_m")}', ae=lambda s=s, code=code: '=' + CH(SC[f'{code}_M'][CTX.col.year]),
          note='Q4/26E: margin before calibration + adjusted-EBITDA-guidance calibration Δ (Group block). 2027E+: scenario lever.' if first else None)
        S(f'{s}_m_pre', '    Q4/26E margin before calibration (prior-year quarter + 9M 2026 y/y drift)', 'driver', 'pct',
          qe=lambda s=s: f'={P(s + "_m")}+IFERROR({ACT(s + "_op")}/{ACT(s + "_rev")}-{ACT0(s + "_op")}/{ACT0(s + "_rev")},0)')
        S(f'{s}_inc', '    Incremental segment margin (Δ operating profit / Δ revenue)', 'pct', 'pct', all=incr(f'{s}_op', f'{s}_rev'))
        S(f'{s}_mix', '    % of segment revenues', 'pct', 'pct', all=ratio(f'{s}_rev', 'seg_rev'))
        blank()
    S('sg_hdr', 'Segment totals and corporate expenses', 'block', note='SEGMENT TOTALS — Σ segments; corporate expenses are not allocated to segments')
    S('seg_rev', '  Segment revenues (Σ four segments)', 'line_b', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("na_rev")}),{"+".join(V(s + "_rev") for s in SEGK)},"")', fc=lambda: '=' + '+'.join(V(s + '_rev') for s in SEGK))
    S('seg_g', '  Segment revenues y/y %', 'growth', 'pct', all=growth('seg_rev'))
    S('seg_pub', '  Memo: segment revenues as published', 'memo', 'm1', data='seg_rev4', flow=True)
    S('seg_chk', '  Check: Σ segments vs published segment revenues (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("seg_pub")}),ISNUMBER({V("seg_rev")})),{tol(V("seg_rev"), V("seg_pub"), 0.25)},"")')
    S('rev_out', '  Revenues outside the segments (derived: GAAP revenues − segment revenues; acquisitions / dispositions and internal loss, 2019–20)', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("seg_rev")}),ROUND({V("is_rev")}-{V("seg_rev")},1),"")', fc=lambda: '=0',
      note='Segment revenues are on the non-GAAP basis; the difference to GAAP revenues was Venezuela (to Q2/18, legacy block) and small acquisition / disposition and internal-loss items in 2019–20. Nil since 2021.')
    S('seg_op', '  Segment operating profit (Σ four segments)', 'line_b', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("na_op")}),{"+".join(V(s + "_op") for s in SEGK)},"")', fc=lambda: '=' + '+'.join(V(s + '_op') for s in SEGK))
    S('seg_m', '  Segment operating margin %', 'pct', 'pct', all=ratio('seg_op', 'seg_rev'))
    S('corp', '  Corporate expenses (not allocated to segments; negative)', 'line', 'm1', data='corp4', flow=True,
      qe=lambda: f'={P("corp")}*(1+IFERROR({ACT("corp")}/{ACT0("corp")}-1,0))*{PT("pt_corp")}', ae=lambda: f'=({V("is_rev")}-N({V("nc_rev")}))*{V("corp_pct")}',
      note=('Corporate staff, headquarters, regional management, currency transaction gains / losses and adjustments to bad-debt and incentive accruals not charged to segments. '
            'Q4/26E: prior-year quarter × 9M 2026 y/y × point-estimate factor. 2027E+: % of legacy revenues (NCR Atleos corporate costs are inside its adjusted EBITDA).'))
    S('corp_pct', '  Corporate expenses % of revenues (legacy)', 'pct', 'pct', hist=ratio('corp', 'is_rev'), qe=ratio('corp', 'is_rev'), e26=ratio('corp', 'is_rev'), ae_in=V0['corp_pct'])
    for s, title, code in SEG:
        S(f'gc_{s}', f'  Contribution to segment revenue growth — {title} (pp)', 'growth', 'pct',
          all=lambda s=s: (f'=IFERROR(({V(s + "_rev")}-{P(s + "_rev")})/{P("seg_rev")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ legacy segment structures (memo)
    S('lg_hdr', 'Legacy segment structures (memo, as published; not on the current four-segment basis)', 'block',
      note='LEGACY SEGMENTS — memo rows as published in each year\'s fourth-quarter release / 10-K; Σ checks to the published totals')
    S('l3_h', '  2017–2018: North America · South America · Rest of World (non-GAAP basis, excl. Venezuela)', 'sub', 'gen')
    for k, lab in (('l3_na', 'North America'), ('l3_sa', 'South America'), ('l3_row', 'Rest of World')):
        S(f'{k}_rev', f'    {lab} — revenues', 'memo', 'm1', data=f'{k}_rev', flow=True)
    for k, lab in (('l3_na', 'North America'), ('l3_sa', 'South America'), ('l3_row', 'Rest of World')):
        S(f'{k}_op', f'    {lab} — operating profit', 'memo', 'm1', data=f'{k}_op', flow=True)
    S('l3_corp', '    Corporate', 'memo', 'm1', data='l3_corp', flow=True)
    S('l3_seg', '    Memo: segment revenues as published', 'memo', 'm1', data='l3_seg_rev', flow=True)
    S('l3_ng', '    Memo: non-GAAP operating profit as published (segment table)', 'memo', 'm1', data='l3_ng', flow=True)
    S('l3_chk', '    Check: Σ revenues and Σ operating profit + corporate vs published (should be 0)', 'check', 'm1',
      hist=lambda: (f'=IF(ISNUMBER({V("l3_seg")}),IF(ABS({V("l3_na_rev")}+{V("l3_sa_rev")}+{V("l3_row_rev")}-{V("l3_seg")})+ABS({V("l3_na_op")}+{V("l3_sa_op")}+{V("l3_row_op")}+{V("l3_corp")}-{V("l3_ng")})<=0.5,0,'
                    f'ROUND(ABS({V("l3_na_rev")}+{V("l3_sa_rev")}+{V("l3_row_rev")}-{V("l3_seg")})+ABS({V("l3_na_op")}+{V("l3_sa_op")}+{V("l3_row_op")}+{V("l3_corp")}-{V("l3_ng")}),1)),"")'))
    S('m_h', '  2014–2016: Largest 5 Markets (U.S., France, Mexico, Brazil, Canada) · Global Markets · Payment Services (non-GAAP basis)', 'sub', 'gen')
    MK = (('m_us', 'U.S.'), ('m_fr', 'France'), ('m_mx', 'Mexico'), ('m_br', 'Brazil'), ('m_ca', 'Canada'), ('m_l5', 'Largest 5 Markets'), ('m_gm', 'Global Markets (Latin America, EMEA, Asia)'), ('m_ps', 'Payment Services'))
    for k, lab in MK:
        S(f'{k}_rev', f'    {lab} — revenues', 'memo', 'm1', data=f'{k}_rev', flow=True)
    for k, lab in MK:
        S(f'{k}_op', f'    {lab} — operating profit', 'memo', 'm1', data=f'{k}_op', flow=True)
    S('m_corp', '    Corporate items', 'memo', 'm1', data='m_corp', flow=True)
    S('m_seg', '    Memo: non-GAAP revenues as published', 'memo', 'm1', data='m_seg_rev', flow=True)
    S('m_ng', '    Memo: non-GAAP operating profit as published (segment table)', 'memo', 'm1', data='m_ng', flow=True)
    S('m_chk', '    Check: Σ revenues and Σ operating profit + corporate items vs published (should be 0)', 'check', 'm1',
      hist=lambda: (f'=IF(ISNUMBER({V("m_seg")}),IF(ABS({V("m_l5_rev")}+{V("m_gm_rev")}+{V("m_ps_rev")}-{V("m_seg")})+ABS({V("m_l5_op")}+{V("m_gm_op")}+{V("m_ps_op")}+{V("m_corp")}-{V("m_ng")})<=0.5,0,'
                    f'ROUND(ABS({V("m_l5_rev")}+{V("m_gm_rev")}+{V("m_ps_rev")}-{V("m_seg")})+ABS({V("m_l5_op")}+{V("m_gm_op")}+{V("m_ps_op")}+{V("m_corp")}-{V("m_ng")}),1)),"")'))
    S('i_h', '  2006–2013: International · North America (GAAP segment operating profit; non-segment = corporate and former operations)', 'sub', 'gen')
    S('i_intl_rev', '    International — revenues', 'memo', 'm1', data='i_intl_rev', flow=True)
    S('i_na_rev', '    North America — revenues', 'memo', 'm1', data='i_na_rev', flow=True)
    S('i_intl_op', '    International — operating profit', 'memo', 'm1', data='i_intl_op', flow=True)
    S('i_na_op', '    North America — operating profit', 'memo', 'm1', data='i_na_op', flow=True)
    S('i_nonseg', '    Non-segment income (expense)', 'memo', 'm1', data='i_nonseg', flow=True)
    S('i_chk', '    Check: Σ revenues vs GAAP revenues and Σ operating profit + non-segment vs GAAP operating profit (should be 0)', 'check', 'm1',
      hist=lambda: (f'=IF(ISNUMBER({V("i_intl_rev")}),IF(ABS({V("i_intl_rev")}+{V("i_na_rev")}-{V("is_rev")})+ABS({V("i_intl_op")}+{V("i_na_op")}+{V("i_nonseg")}-{V("is_op")})<=0.3,0,'
                    f'ROUND(ABS({V("i_intl_rev")}+{V("i_na_rev")}-{V("is_rev")})+ABS({V("i_intl_op")}+{V("i_na_op")}+{V("i_nonseg")}-{V("is_op")}),1)),"")'))
    blank()

    # ------------------------------------------------------------------ NCR Atleos (pending acquisition)
    S('nc_hdr', 'NCR Atleos acquisition (pending; $30.00 cash + 0.1574 Brink\'s shares per NCR Atleos share; closing expected early January 2027) — outside the 2026 guidance', 'block',
      note='NCR ATLEOS — own block behind a toggle: standalone projections (NCR Atleos management, 424B3) × levers, cost synergies, purchase accounting, financing; consolidated from the closing date')
    S('nc_tgl', '  Deal completes (1 = yes, 0 = no) — toggle', 'driver', 'gen', e26_in=0, ae_in=V0['nc_tgl'], note=MAN['ncr_atleos']['terms'])
    S('nc_frac', '  Share of the year consolidated (closing date assumption: 4-Jan-2027 → 362 / 365 days)', 'driver', 'pct', e26_in=0.0, ae_in=V0['nc_frac'],
      note='Closing "early January 2027" per the third-quarter 2026 release; the exact date is an assumption (4-Jan-2027). Change the 2027E cell to move the closing.')
    S('nc_sa_rev', '  NCR Atleos standalone revenue (as reported FY2025; NCR Atleos management projections 2026E–2030E)', 'line', 'm1', flow=True,
      hval=lambda col: (MAN['ncr_atleos']['hist']['2025']['rev'] if (col.year == 2025 and not col.q) else None), e26_in=V0['nc_rev'][2026], ae_in={y: V0['nc_rev'][y] for y in range(2027, FYL + 1)},
      note=MAN['ncr_atleos']['proj_note'] + ' ' + MAN['ncr_atleos']['hist_note'])
    S('nc_sa_g', '    Standalone revenue y/y %', 'growth', 'pct', all=growth('nc_sa_rev'))
    S('nc_sa_eb', '  NCR Atleos standalone adjusted EBITDA (before stock-based compensation; management projections)', 'line', 'm1', flow=True,
      e26_in=V0['nc_eb'][2026], ae_in={y: V0['nc_eb'][y] for y in range(2027, FYL + 1)})
    S('nc_sa_m', '    Standalone adjusted EBITDA margin %', 'pct', 'pct', all=ratio('nc_sa_eb', 'nc_sa_rev'))
    S('nc_adj', '  Revenue vs management projections % (scenario lever)', 'driver', 'pct', e26_in=0.0, ae=lambda: '=' + CH(SC['NCR_REV'][CTX.col.year]))
    S('nc_madj', '  Adjusted EBITDA margin vs management projections (pp, scenario lever)', 'driver', 'pct', e26_in=0.0, ae=lambda: '=' + CH(SC['NCR_M'][CTX.col.year]))
    S('nc_rev', '  NCR Atleos revenue consolidated', 'line_b', 'm1', e26_in=0.0, ae=lambda: f'={V("nc_tgl")}*{V("nc_frac")}*{V("nc_sa_rev")}*(1+{V("nc_adj")})')
    S('nc_eb', '  NCR Atleos adjusted EBITDA consolidated (before synergies)', 'line', 'm1', e26_in=0.0, ae=lambda: f'={V("nc_rev")}*({V("nc_sa_m")}+{V("nc_madj")})')
    S('nc_syn_run', '  Run-rate cost synergies ($200m within three years of closing × realisation lever)', 'line', 'm1', e26_in=0.0,
      ae=lambda: f'={MAN["ncr_atleos"]["syn_run"]}*{CH(SC["SYN"][CTX.col.year])}', note=MAN['ncr_atleos']['synergies'])
    S('nc_syn_ph', '  Synergy phasing (% of run-rate realised in the year; assumption)', 'driver', 'pct', e26_in=0.0, ae_in=V0['syn_phase'],
      note='The company guides to the full run-rate "within three years of closing"; the yearly phasing is a model assumption.')
    S('nc_syn', '  Cost synergies realised', 'line', 'm1', e26_in=0.0, ae=lambda: f'={V("nc_tgl")}*{V("nc_syn_run")}*{V("nc_syn_ph")}')
    S('nc_dep', '  NCR Atleos depreciation & amortization excl. acquired intangibles (% of its revenue; FY2025: ($277m − $95m) ÷ $4,353.5m)', 'driver', 'pct', e26_in=0.0, ae_in=V0['nc_dep_pct'])
    S('nc_sbc', '  NCR Atleos stock-based compensation (% of its revenue; FY2025 $34m)', 'driver', 'pct', e26_in=0.0, ae_in=V0['nc_sbc_pct'])
    S('nc_op', '  NCR Atleos contribution to non-GAAP operating profit (adjusted EBITDA + synergies − D&A excl. acquired intangibles − stock-based compensation)', 'line_b', 'm1', e26_in=0.0,
      ae=lambda: f'={V("nc_eb")}+{V("nc_syn")}-{V("nc_rev")}*({V("nc_dep")}+{V("nc_sbc")})',
      note='Brink\'s non-GAAP operating profit is after depreciation and share-based compensation and before amortization of acquisition-related intangibles; NCR Atleos is mapped to that presentation.')
    S('nc_amort', '  Amortization of NCR Atleos acquired intangibles (pro forma $296.4m a year; adjusted out as "acquisitions and dispositions")', 'line', 'm1', e26_in=0.0,
      ae=lambda: f'={V("nc_tgl")}*{V("nc_frac")}*{MAN["ncr_atleos"]["amort"]}', note=MAN['ncr_atleos']['ppa_note'])
    S('nc_integ', '  Integration and transaction costs (adjusted out; assumption — not disclosed)', 'driver', 'm1', e26_in=0.0, ae_in=V0['nc_integ'],
      note='Assumption: costs to achieve the $200m synergies and closing costs are not disclosed. 9M 2026 "NCR Atleos acquisition and transformation initiatives" were $121.0m. Multiplied by the toggle.')
    S('nc_capex', '  NCR Atleos capital expenditures (% of its revenue; FY2025 $117m PP&E = 2.7%, plus capitalized software)', 'driver', 'pct', e26_in=0.0, ae_in=V0['nc_capex_pct'])
    S('nc_pf_eb', '  Memo: NCR Atleos adjusted EBITDA for the pre-closing days of the year (pro forma, for leverage)', 'memo_calc', 'm1', e26_in=0.0,
      ae=lambda: f'={V("nc_tgl")}*(1-{V("nc_frac")})*{V("nc_sa_eb")}*IF({P("nc_tgl")}=0,1,0)')
    blank()

    # ------------------------------------------------------------------ group total & guidance calibration
    S('g_hdr', 'Group Total — revenues & non-GAAP operating profit (segment build + NCR Atleos) → Q4 2026 guidance calibration', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Revenues (segment build)', 'total', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("seg_rev")}),{V("seg_rev")}+{V("rev_out")},{V("is_rev")})',
      fc=lambda: f'={V("seg_rev")}+{V("rev_out")}+N({V("nc_rev")})', note='Σ segment revenues + revenues outside the segments (+ NCR Atleos from closing).')
    S('g_rev_g', '  Revenues y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_org', '  Organic growth % — total (release table, segment / non-GAAP revenue basis; forecast = revenue-weighted segments)', 'pct', 'pct', data='g_orgp',
      qe=lambda: '=(' + '+'.join(f'{P(s + "_rev")}*{V(s + "_org")}' for s in SEGK) + f')/{P("seg_rev")}',
      e26=lambda: f'=(SUMPRODUCT({PQ1}{R["seg_rev"]}:{PQ4}{R["seg_rev"]},{Q1}{R["g_org"]}:{QE}{R["g_org"]}))/{P("seg_rev")}',
      ae=lambda: '=(' + '+'.join(f'{P(s + "_rev")}*{V(s + "_org")}' for s in SEGK) + f')/{P("seg_rev")}',
      note='Company definition: change excluding acquisitions / dispositions for one year and currency (2015–18 on the non-GAAP basis, i.e. excluding Venezuela). Annual history = Σ of the four quarterly tables; blank where a quarter is missing (Q1/19 release filed without tables). 2026E = quarterly organic growth weighted by the 2025 quarters (compare the "mid-single digits" 2026 framework).')
    S('g_acq', '  Acquisitions / dispositions % — total', 'pct', 'pct', data='g_acqp')
    S('g_fx', '  Currency effect % — total', 'pct', 'pct', data='g_fxp')
    S('g_gt', '  Memo: total change % per the release table', 'memo', 'pct', data='g_totp')
    S('g_gchk', '  Check: organic + acquisitions / dispositions + currency vs table change (should be 0; ±0.5pp rounding)', 'check', 'pct2',
      hist=lambda: f'=IF(AND(ISNUMBER({V("g_gt")}),ISNUMBER({V("g_org")})),{tol(V("g_gt"), V("g_org") + "+" + V("g_acq") + "+" + V("g_fx"), 0.005, 3)},"")')
    S('g_chk_rev', '  Check: segment build vs consolidated revenues (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),{tol(V("g_rev"), V("is_rev"))},"")')
    S('g_adj', 'Non-GAAP operating profit (segment build)', 'total', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("seg_op")}),{V("seg_op")}+{V("corp")},IF(ISNUMBER({V("o_pub")}),{V("o_pub")},""))',
      fc=lambda: f'={V("seg_op")}+{V("corp")}+N({V("nc_op")})',
      note='Σ segment operating profit + corporate expenses (+ NCR Atleos). Before 2019: non-GAAP operating profit as published (legacy segment bases). Drives the GAAP P&L below.')
    S('g_adjm', '  Non-GAAP operating margin %', 'pct', 'pct', all=ratio('g_adj', 'is_rev'))
    S('g_adj_g', '  Non-GAAP operating profit y/y %', 'growth', 'pct', all=growth('g_adj'))
    S('g_chk_adj', '  Check: segment build vs non-GAAP operating profit bridge (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_adj")}),ISNUMBER({V("o_adj")})),{tol(V("g_adj"), V("o_adj"), 0.25)},"")')
    S('cal_guid', '  Memo: Q4 2026 revenue guidance (scenario end-point)', 'memo', 'm1', qe=lambda: '=' + CH(SC['out_rev']), note=V0['rev_guid_note'])
    S('cal_pre', '  Revenues before calibration (Q4/26E helper)', 'line', 'm1',
      qe=lambda: '=' + '+'.join(f'{P(s + "_rev")}*(1+{V(s + "_org_pre")}+{V(s + "_acq")}+{V(s + "_fx")})' for s in SEGK))
    S('cal_sens', '  Revenue sensitivity to +1.00 of organic growth (Q4/26E helper)', 'line', 'm1', qe=lambda: '=' + '+'.join(P(s + '_rev') for s in SEGK))
    S('cal_g', '  Guidance calibration: Δ organic growth applied to all segments (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_guid")}-{V("cal_pre")})/{V("cal_sens")}',
      note='Solves the uniform organic-growth shift (vs the 9M 2026 average) so that Q4/26E revenues = the guidance end-point for the active scenario (closed form, no circularity). The Δ also absorbs any currency move against the Q3/26 effect assumed for Q4.')
    S('cal_rev_chk', '  Check: Q4/26E revenues vs guidance end-point (should be 0)', 'check', 'm1', qe=lambda: f'=ROUND({V("g_rev")}-{V("cal_guid")},1)')
    S('cal_eb', '  Memo: Q4 2026 non-GAAP adjusted EBITDA guidance (scenario end-point)', 'memo', 'm1', qe=lambda: '=' + CH(SC['out_eb']), note=V0['eb_guid_note'])
    S('cal_oi', '  Q4/26E non-GAAP operating profit required (adjusted EBITDA − D&A excl. acquisition amortization − share-based compensation − interest & other income + noncontrolling interests)', 'memo_calc', 'm1',
      qe=lambda: f'={V("cal_eb")}-({V("d_dda")}-{V("d_amort")})-{V("d_sbc")}-{V("is_oth")}+{V("is_nci")}')
    S('cal_oi_pre', '  Non-GAAP operating profit before margin calibration (Q4/26E helper)', 'line', 'm1',
      qe=lambda: '=' + '+'.join(f'{V(s + "_rev")}*{V(s + "_m_pre")}' for s in SEGK) + f'+{V("corp")}')
    S('cal_m', '  Guidance calibration: Δ segment margin applied to all segments (Q4/26E)', 'driver', 'pct',
      qe=lambda: f'=({V("cal_oi")}-{V("cal_oi_pre")})/{V("seg_rev")}',
      note='Solves the uniform segment-margin shift so that Q4/26E adjusted EBITDA = the guidance end-point for the active scenario.')
    S('cal_eb_chk', '  Check: Q4/26E adjusted EBITDA vs guidance end-point (should be 0)', 'check', 'm1', qe=lambda: f'=ROUND({V("r_adj")}-{V("cal_eb")},1)')
    S('cal_eps', '  Memo: Q4 2026 non-GAAP EPS guidance (scenario end-point, $) — information, not forced', 'eps_memo', 'ps', qe=lambda: '=' + CH(SC['out_eps']))
    S('cal_eps_d', '    Model Q4/26E non-GAAP EPS − guidance ($)', 'eps_memo', 'ps', qe=lambda: f'={V("e_eps")}-{V("cal_eps")}')
    S('cal_fw_m', '  Memo: 2026 framework — adjusted EBITDA margin expansion (bps; guided 30–50) vs model', 'memo_calc', 'gen',
      e26=lambda: f'=ROUND(({V("r_adj_m")}-{P("r_adj_m")})*10000,0)', note='Information row: 2026 non-GAAP framework (organic growth mid-single digits; AMS/DRS organic growth mid-to-high teens; adjusted EBITDA margin +30–50 bps; free cash flow conversion 40–45%).')
    S('cal_fw_f', '  Memo: 2026 framework — free cash flow conversion (FCF before dividends ÷ adjusted EBITDA; guided 40–45%; drives the Q4 working-capital calibration)', 'memo_calc', 'pct',
      e26=lambda: f'=IFERROR({V("fcf")}/{V("r_adj")},"")')
    S('cal_sp_rev', '  Memo: Brink\'s Standalone Projections — revenue (management, Feb-2026; 424B3; not guidance)', 'memo', 'm', e26_in=V0['sp_rev'][2026], ae_in={y: V0['sp_rev'][y] for y in range(2027, FYL + 1)},
      note=MAN['standalone_projections']['note'])
    S('cal_sp_d', '    Model legacy revenues (excl. NCR Atleos) vs Standalone Projections %', 'memo_calc', 'pct', e26=lambda: f'=({V("g_rev")}-N({V("nc_rev")}))/{V("cal_sp_rev")}-1', ae=lambda: f'=({V("g_rev")}-N({V("nc_rev")}))/{V("cal_sp_rev")}-1')
    S('cal_sp_eb', '  Memo: Brink\'s Standalone Projections — adjusted EBITDA', 'memo', 'm', e26_in=V0['sp_eb'][2026], ae_in={y: V0['sp_eb'][y] for y in range(2027, FYL + 1)})
    S('cal_sp_ed', '    Model legacy adjusted EBITDA (excl. NCR Atleos and synergies) vs Standalone Projections %', 'memo_calc', 'pct',
      e26=lambda: f'=({V("r_adj")}-N({V("nc_eb")})-N({V("nc_syn")}))/{V("cal_sp_eb")}-1', ae=lambda: f'=({V("r_adj")}-N({V("nc_eb")})-N({V("nc_syn")}))/{V("cal_sp_eb")}-1')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A & adjusting items', 'block', note='COST DRIVERS — inputs that drive forecast cost lines (Q4/26E: point estimates; 2027E+: % of revenues or schedules)')
    S('d_dda', '  Depreciation & amortization (total; cash-flow statement)', 'line', 'm1', data='cf_da', flow=True,
      qe=lambda: f'={PT("pt_dda")}', ae=lambda: f'=({V("is_rev")}-N({V("nc_rev")}))*{V("d_dep_pct")}+{V("d_amort")}+N({V("nc_rev")})*N({V("nc_dep")})',
      note='Q4/26E point estimate. 2027E+: legacy D&A excl. acquisition amortization as % of legacy revenues + amortization of acquisition-related intangibles + NCR Atleos depreciation.')
    S('d_amort', '  Amortization of acquisition-related intangibles (adjusted out; in "acquisitions and dispositions")', 'line', 'm1', flow=True,
      hval=lambda col: (MAN['amort_sched']['fy2025'] if (col.year == 2025 and not col.q) else None),
      qe=lambda: f'={PT("pt_amort")}', e26=lambda: f'={MAN["amort_sched"]["ytd_2026"]}+{QEc("d_amort")}', ae=lambda: f'={V("d_amort_sch")}+N({V("nc_amort")})',
      note=MAN['amort_sched']['text'] + ' Not published by quarter before 2026 (FY2025 shown). 2027E+: 10-K schedule + NCR Atleos purchase accounting.')
    S('d_amort_sch', '  Amortization schedule — intangibles held at 31-Dec-2025 (10-K, input)', 'driver', 'm1', ae_in=V0['amort_sched'])
    S('d_dep_pct', '  D&A excl. acquisition amortization % of revenues (legacy)', 'pct', 'pct',
      hist=lambda: (f'=IF(ISNUMBER({V("d_amort")}),IFERROR(({V("d_dda")}-{V("d_amort")})/{V("is_rev")},""),"")'), ae_in=V0['dep_pct'],
      note='FY2025: ($290.8m − $58.9m) ÷ $5,261.2m = 4.4%.')
    S('d_sga', '  SG&A % of revenues', 'pct', 'pct', all=ratio('is_sga', 'is_rev'),
      qe=lambda: f'={P("d_sga")}+IFERROR({ACT("is_sga")}/{ACT("is_rev")}-{ACT0("is_sga")}/{ACT0("is_rev")},0)', ae_in=V0['sga_pct'],
      note='Presentation driver: cost of revenues is the implied balancing line (operating profit comes from the non-GAAP build). 2027E+ input (the blended ratio rises with NCR Atleos, which carries more SG&A and R&D).')
    S('d_sbc', '  Share-based compensation (cash-flow statement)', 'line', 'm1', data='cf_sbc', flow=True,
      qe=lambda: f'={PT("pt_sbc")}', ae=lambda: f'=({V("is_rev")}-N({V("nc_rev")}))*{V("d_sbc_pct")}+N({V("nc_rev")})*N({V("nc_sbc")})',
      note='Added back in adjusted EBITDA (company definition, from 2017). Q4/26E point estimate; 2027E+ % of revenues (+ NCR Atleos).')
    S('d_sbc_pct', '  Share-based compensation % of revenues (legacy)', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_adj_h', '  Other items not allocated to segments (pre-tax add-backs: GAAP operating profit + items = non-GAAP; forecast inputs):', 'sub', 'gen')
    fc_items = {'restr': dict(fc=lambda: '=0'), 'acq': dict(qe=lambda: f'={V("d_amort")}', ae=lambda: f'={V("d_amort")}'),
                'arg': dict(qe_in=0.0, ae_in=0.0), 'ven': dict(fc=lambda: '=0'),
                'transf': dict(qe=lambda: f'={PT("pt_transf")}', ae=lambda: f'={V("d_transf_in")}+{V("nc_tgl")}*{V("nc_integ")}'),
                'ret': dict(fc=lambda: '=0'), 'oth': dict(fc=lambda: '=0')}
    notes = {'acq': 'Forecast = amortization of acquisition-related intangibles (existing schedule + NCR Atleos); other acquisition / disposition items are not forecast.',
             'arg': 'Not forecast (the company states it cannot forecast the impact of highly inflationary accounting): input 0.',
             'transf': 'Q4/26E: point estimate. 2027E+: transformation programme input + NCR Atleos integration and transaction costs (assumption).',
             'oth': 'Cell comments list the company\'s items per period. 2009–2014: total of all items (published non-GAAP − GAAP operating profit); item detail not in row format.'}
    for k, lab in ITEMS:
        S(f'd_{k}', f'  {lab}', 'line', 'm1', data=f'it_{k}', flow=True, labkey=f'it_{k}_lab', note=notes.get(k), **fc_items[k])
    S('d_transf_in', '  Transformation programme costs — input (2027E+)', 'driver', 'm1', ae_in=V0['transf_in'])
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF OPERATIONS (US GAAP)', 'section',
      note='CONSOLIDATED IS — forecast logic (GAAP operating profit = non-GAAP operating profit − other items not allocated to segments; cost of revenues implied)')
    S('is_rev', 'Revenues', 'total', 'm1', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the segment build.')
    S('is_cor', 'Cost of revenues', 'line', 'm1', data='cor', flow=True, fc=lambda: f'={V("is_rev")}-{V("is_sga")}+{V("is_ooi")}-{V("is_op")}',
      note='Forecast = revenues − SG&A + other operating income − operating profit (implied by the non-GAAP build).')
    S('is_sga', 'Selling, general & administrative expenses', 'line', 'm1', data='sga', flow=True, fc=lambda: f'={V("is_rev")}*{V("d_sga")}')
    S('is_ooi', 'Other operating income (expense)', 'line', 'm1', data='ooi', flow=True, fc=lambda: '=0')
    S('is_op', 'Operating profit', 'total', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_cor")}),{V("is_rev")}-{V("is_cor")}-{V("is_sga")}+N({V("is_ooi")}),"")', fc=lambda: f'={V("g_adj")}-{V("o_tot")}',
      note='Forecast = non-GAAP operating profit − other items not allocated to segments.')
    S('is_op_m', '  Operating margin %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('is_op_pub', '  Memo: operating profit as reported', 'memo', 'm1', data='op', flow=True)
    S('is_op_chk', '  Check: operating profit vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_op_pub")}),{tol(V("is_op"), V("is_op_pub"))},"")')
    S('is_int', 'Interest expense', 'line', 'm1', data='int', flow=True, qe=lambda: f'={PT("pt_int")}',
      ae=lambda: (f'={P("ds_fixed")}*{V("ds_r_fixed")}+{V("ds_deal_fixed")}*{V("nc_frac")}*{V("ds_r_deal")}+({P("ds_rev")}+{V("ds_deal_prep")}*{V("nc_frac")})*{V("ds_r_rev")}+{V("ds_fees")}'),
      note='Q4/26E point estimate. 2027E+ = rate × opening debt (+ NCR Atleos acquisition and assumed debt for the consolidated part of the closing year) + fees; no circularity.')
    S('is_ven', 'Loss on deconsolidation of Venezuela operations (Q2/18)', 'line', 'm1', data='ven_decon', flow=True, fc=lambda: '=0')
    S('is_oth', 'Interest and other nonoperating income (expense)', 'line', 'm1', data='oth', flow=True, qe=lambda: f'={PT("pt_oth")}', ae_in=V0['oth_ae'],
      note='Interest income, non-service retirement costs, marketable-securities and Argentina currency items, other. Forecast input (non-GAAP basis; no adjusting items forecast).')
    S('is_ebt', 'Income from continuing operations before tax', 'line_b', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("is_op")}),{V("is_op")}-{V("is_int")}-N({V("is_ven")})+N({V("is_oth")}),"")')
    S('is_tax', 'Provision for income taxes', 'line', 'm1', data='tax', flow=True, fc=lambda: f'={V("e_adjtax")}-{V("o_tot")}*{V("e_itax")}',
      note='Forecast = non-GAAP income tax (non-GAAP pre-tax income × non-GAAP effective tax rate) − tax effect of the adjusting items.')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'))
    S('is_cont', 'Income from continuing operations', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_nci', '  Less: net income attributable to noncontrolling interests', 'line', 'm1', data='nci', flow=True, qe=lambda: f'={PT("pt_nci")}', ae_in=V0['nci_ae'],
      note='Forecast input ($m). FY2006–08: minority interest as presented before SFAS 160.')
    S('is_cont_att', 'Income from continuing operations attributable to Brink\'s', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_cont")}),{V("is_cont")}-N({V("is_nci")}),"")')
    S('is_disc', 'Income (loss) from discontinued operations attributable to Brink\'s, net of tax', 'line', 'm1', data='disc_att', flow=True, fc=lambda: '=0')
    S('is_ni', 'Net income attributable to Brink\'s', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_cont_att")}),{V("is_cont_att")}+N({V("is_disc")}),"")')
    S('is_ni_chk', '  Check: net income attributable vs reported (should be 0; ±0.25 rounding)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),{tol(V("is_ni"), V("is_ni_pub"), 0.25)},"")')
    S('is_ni_pub', '  Memo: net income attributable to Brink\'s as reported', 'memo', 'm1', data='ni', flow=True)
    S('is_dda', '  Memo: depreciation & amortization (total)', 'memo_calc', 'm1', all=lambda: f'=IF(ISNUMBER({V("d_dda")}),{V("d_dda")},"")')
    S('is_sbc', '  Memo: share-based compensation', 'memo_calc', 'm1', all=lambda: f'=IF(ISNUMBER({V("d_sbc")}),{V("d_sbc")},"")')
    S('eps_hdr', '(Earnings per share — Brink\'s common stock)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='sh_b', avg=True,
      qe=lambda: f'={V0["cover_sh"]}-${E26}${R["bb_sh"]}*0.5', ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})+{V("bb_deal")}*({V("nc_frac")}-0.5)',
      note='Q4/26E: shares outstanding at 30-Oct-2026 (10-Q cover) − Q4 buybacks (mid-quarter). 2027E+: average of beginning and ending shares (NCR Atleos consideration shares weighted from closing).')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='sh_d', avg=True,
      qe=lambda: f'={V("sh_basic")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_cont', 'EPS from continuing operations – diluted ($)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_cont_att")}/{V("sh_dil")},""),"")',
      note='Income from continuing operations attributable to Brink\'s ÷ weighted diluted shares.')
    S('eps_cont_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_cont'))
    S('eps_pub', '  Memo: EPS from continuing operations – diluted as reported ($)', 'eps_memo', 'ps', data='eps_cont_d')
    S('eps_chk', '  Check: model vs reported diluted EPS (should be 0.00; ±0.01 rounding; ±0.05 in Q4, where shares are derived as 4 × FY − Σ Q1–Q3)', 'check', 'ps',
      hist=lambda: (f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_cont")})),IF(ABS({V("eps_cont")}-{V("eps_pub")})<={0.0501 if CTX.col.q == 4 else 0.0101},0,ROUND({V("eps_cont")}-{V("eps_pub")},2)),"n/p")'))
    S('eps_dil', '  EPS – diluted, net income ($; as reported)', 'eps_memo', 'ps', data='eps_d', fc=lambda: f'=IFERROR({V("is_ni")}/{V("sh_dil")},"")')
    S('dps', '  Dividends declared per share ($)', 'line', 'ps', data='dps', flow=True, qe_in=V0['dps_q'],
      ae=lambda: f'={P("dps")}*(1+{V("dps_g")})', note='Q4/26E = the quarterly dividend declared in Q1–Q3/26 (as tagged in XBRL, rounded to cents). 2027E+: prior year × (1 + growth).')
    S('dps_g', '  Dividend per share growth %', 'driver', 'pct', all=growth('dps'), ae_in=V0['dps_g'])
    blank()

    # ------------------------------------------------------------------ RECON 1: operating profit -> non-GAAP operating profit
    S('sec_r1', 'RECONCILIATION: OPERATING PROFIT → NON-GAAP OPERATING PROFIT (company definition: GAAP operating profit excluding "other items not allocated to segments")', 'section',
      note='NON-GAAP OPERATING PROFIT — per the release tables ("Segment Results" / "Non-GAAP Results Reconciled to GAAP"); the company\'s item labels of each period are in the cell comments of the cost-driver rows')
    S('o_op', 'Operating profit (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_op")}')
    for k, lab in ITEMS:
        S(f'o_{k}', f'  (+) {lab.split(" (")[0]}', 'line', 'm1', all=lambda k=k: f'=IF(ISNUMBER({V("d_" + k)}),{V("d_" + k)},"")')
    S('o_tot', '  Total other items not allocated to segments (pre-tax)', 'line_b', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("o_restr")}),{nsum(["o_" + k for k, _ in ITEMS])},"")')
    S('o_adj', '  = Non-GAAP operating profit (model bridge)', 'total', 'm1', all=lambda: f'=IF(AND(ISNUMBER({V("o_op")}),ISNUMBER({V("o_tot")})),{V("o_op")}+{V("o_tot")},"")',
      note='Rebuilt from the published reconciliation items; forecast = GAAP operating profit + forecast items (equals the segment build — check in the Group block).')
    S('o_adj_m', '  Non-GAAP operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_pub', '  Company-published non-GAAP operating profit', 'memo', 'm1', data='op_ng_pub', flow=True)
    S('o_chk', '  Check: model bridge vs company-published (should be 0; ±0.25)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("o_pub")}),ISNUMBER({V("o_adj")})),{tol(V("o_adj"), V("o_pub"), 0.25)},"n/p")')
    S('o_def', '  Definition / basis (company non-GAAP definition in force)', 'text', 'gen',
      note='Definition changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('o_rev_pub', '  Memo: company-published non-GAAP revenues (differ from GAAP to 2020: Venezuela, acquisitions / dispositions, internal loss)', 'memo', 'm1', data='rev_ng_pub', flow=True)
    S('o_rev_d', '  Memo: GAAP revenues − non-GAAP revenues', 'memo_calc', 'm1', hist=lambda: f'=IF(ISNUMBER({V("o_rev_pub")}),ROUND({V("is_rev")}-{V("o_rev_pub")},1),"")')
    S('o_adj_g', '  Non-GAAP operating profit y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental non-GAAP operating margin (Δ non-GAAP operating profit / Δ revenues)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2: net income -> EBITDA -> adjusted EBITDA
    S('sec_r2', 'RECONCILIATION: NET INCOME ATTRIBUTABLE TO BRINK\'S → EBITDA → ADJUSTED EBITDA (company definition, as published from 2016)', 'section',
      note='ADJUSTED EBITDA — net income attributable to Brink\'s + interest expense + income taxes + D&A = EBITDA; + discontinued operations + adjusting items + share-based compensation + marketable-securities (gain) loss = adjusted EBITDA')
    S('r_ni', 'Net income attributable to Brink\'s (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('r_int', '  (+) Interest expense', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_int")}),{V("is_int")},"")')
    S('r_tax', '  (+) Income tax provision', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_tax")}),{V("is_tax")},"")')
    S('r_da', '  (+) Depreciation and amortization', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("d_dda")}),{V("d_dda")},"")')
    S('r_ebitda', '  = EBITDA', 'total', 'm1', all=lambda: f'=IF(AND(ISNUMBER({V("r_ni")}),ISNUMBER({V("r_da")})),{V("r_ni")}+{V("r_int")}+{V("r_tax")}+{V("r_da")},"")')
    S('r_ebitda_pub', '  Company-published EBITDA (from 2018)', 'memo', 'm1', data='ebitda_pub', flow=True)
    S('r_ebitda_chk', '  Check: model vs company-published EBITDA (should be 0; ±0.3)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda_pub")}),ISNUMBER({V("r_ebitda")})),{tol(V("r_ebitda"), V("r_ebitda_pub"), 0.3)},"n/p")')
    S('r_disc', '  (+) Loss (income) from discontinued operations', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_disc")}),-{V("is_disc")},"")')
    S('r_items', '  (+) Adjusting items in EBITDA (company reconciliation; excl. amounts already in interest, taxes and D&A)', 'line', 'm1', data='eb_items', flow=True, labkey='eb_items_lab',
      hist=lambda: f'=IF(ISNUMBER({V("o_tot")}),{V("o_tot")},"")', fc=lambda: f'={V("o_tot")}-{V("d_amort")}',
      note=('2018+: sum of the company\'s adjusting items in the adjusted-EBITDA table (cell comments list them). 2016–17: derived from the published total. Before 2016 (not published): '
            'model definition = other items not allocated to segments. Forecast = other items − amortization of acquisition-related intangibles (already in D&A).'))
    S('r_sbc', '  (+) Share-based compensation', 'line', 'm1', data='eb_sbc', flow=True, fc=lambda: f'={V("d_sbc")}', note='Added back by the company from 2017.')
    S('r_mkt', '  (+) Marketable securities (gain) loss', 'line', 'm1', data='eb_mkt', flow=True, fc=lambda: '=0', note='Added back by the company from 2020.')
    S('r_adj', '  = Adjusted EBITDA', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_ebitda")}),ISNUMBER({V("r_items")})),{V("r_ebitda")}+N({V("r_disc")})+{V("r_items")}+N({V("r_sbc")})+N({V("r_mkt")}),"")',
      note='Company definition (published from 2016; before that a model measure). Used for leverage (net debt / adjusted EBITDA), the Q4 2026 guidance calibration and EV / EBITDA.')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_adj_pub', '  Company-published adjusted EBITDA', 'memo', 'm1', data='adj_ebitda_pub', flow=True)
    S('r_chk', '  Check: model vs company-published adjusted EBITDA (should be 0; ±0.4)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("r_adj_pub")}),ISNUMBER({V("r_adj")})),{tol(V("r_adj"), V("r_adj_pub"), 0.4)},"n/p")')
    S('r_def', '  Definition / basis (company adjusted EBITDA definition in force)', 'text', 'gen')
    S('r_ebit_h', 'To adjusted EBIT (for NOPAT, ROIC and the DCF):', 'sub', 'gen')
    S('r_dep', '  Depreciation & amortization excl. acquisition-related intangibles (forecast; history where the amortization is published)', 'line', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("d_dda")}),ISNUMBER({V("d_amort")})),{V("d_dda")}-{V("d_amort")},"")')
    S('r_ebit', '  = Adjusted EBIT (= non-GAAP operating profit: after depreciation and share-based compensation, before amortization of acquisition-related intangibles)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("o_adj")}),{V("o_adj")},"")')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_cash', '  Memo: cash adjusting costs (restructuring, transformation / integration, other items; deducted in the DCF)', 'memo_calc', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("o_restr")}),{V("o_restr")}+{V("o_transf")}+{V("o_oth")},"")')
    blank()

    # ------------------------------------------------------------------ RECON 3: non-GAAP income / EPS
    S('sec_r3', 'RECONCILIATION: INCOME FROM CONTINUING OPERATIONS ATTRIBUTABLE TO BRINK\'S → NON-GAAP INCOME → NON-GAAP EPS (company definition)', 'section',
      note='NON-GAAP EPS — GAAP income from continuing operations + other items not allocated to segments (pre-tax) + non-operating items, tax effects, tax items and the interim tax-rate adjustment = non-GAAP income; ÷ diluted shares')
    S('e_ni', 'Income from continuing operations attributable to Brink\'s (GAAP)', 'line_b', 'm1', all=lambda: f'={V("is_cont_att")}')
    S('e_op', '  (+) Other items not allocated to segments (pre-tax; bridge above)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_tot")}),{V("o_tot")},"")')
    S('e_tax', '  (+/−) Non-operating items (retirement plans, Venezuela deconsolidation, debt costs), tax effect of the adjustments, tax items, NCI share and interim tax-rate adjustment', 'line', 'm1', flow=True,
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pubni")}),ISNUMBER({V("e_op")})),{V("e_pubni")}-{V("e_ni")}-{V("e_op")},"")',
      fc=lambda: f'={V("e_adjni")}-{V("e_ni")}-{V("e_op")}', labkey='eps_items_lab',
      note=('Historical: derived = published non-GAAP income − GAAP income − pre-tax operating items (the company reconciles item by item after tax; the per-share items of each period are in the cell comments). '
            'Forecast: implied by the non-GAAP tax rate.'))
    S('e_adjni', '  = Non-GAAP income from continuing operations attributable to Brink\'s', 'total', 'm1', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("e_tax")}),{V("e_ni")}+{V("e_op")}+{V("e_tax")},"")', fc=lambda: f'={V("e_adjebt")}-{V("e_adjtax")}-{V("is_nci")}')
    S('e_pubni', '  Company-published non-GAAP income from continuing operations', 'memo', 'm1', data='inc_ng_pub', flow=True)
    S('e_sh', '  Diluted shares used for non-GAAP EPS (m; = GAAP diluted shares except in GAAP-loss periods)', 'line', 'm1', data='sh_ng', avg=True, shnote=True,
      qe=lambda: f'={V("sh_dil")}', ae=lambda: f'={V("sh_dil")}',
      note='In GAAP-loss periods the company includes dilutive awards that GAAP excludes; there the share count is implied by published non-GAAP income ÷ published non-GAAP EPS (cell comments).')
    S('e_eps', 'Non-GAAP EPS – diluted ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published non-GAAP EPS ($)', 'eps_memo', 'ps', data='eps_ng_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.015 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_pub")}),ISNUMBER({V("e_eps")})),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0151,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_eps_g', '  Non-GAAP EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('e_adjebt', '  Non-GAAP pre-tax income (forecast: non-GAAP operating profit − interest expense + interest and other income)', 'line', 'm1',
      fc=lambda: f'={V("o_adj")}-{V("is_int")}+{V("is_oth")}')
    S('e_adjtax', '  Non-GAAP income tax (forecast: non-GAAP pre-tax income × non-GAAP effective tax rate)', 'line', 'm1', fc=lambda: f'={V("e_adjebt")}*{V("e_rate")}')
    S('e_rate', '  Non-GAAP effective tax rate', 'pct', 'pct', qe=lambda: f'={PT("pt_etr")}', e26=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Company estimate of the full-year 2026 non-GAAP effective tax rate: 27.2% (2025: 27.5%). 2027E+ input.')
    S('e_itax', '  Tax rate on adjusting items (forecast input)', 'pct', 'pct', qe=lambda: f'={PT("pt_itax")}', e26=lambda: f'={PT("pt_itax")}', ae_in=V0['itax'],
      note='9M 2026: adjusting items of $221.9m pre-tax carried $47.0m of tax (21%); acquisition and legal items are only partly deductible.')
    S('e_def', '  Definition / basis (company non-GAAP EPS definition)', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Revenues y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_org', '  Organic revenue growth % (company definition)', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("g_org")}),{V("g_org")},"")')
    for s, title, code in SEG:
        S(f'gm_{s}', f'  {title} revenues y/y %', 'growth', 'pct', all=growth(f'{s}_rev'))
    S('gm_adjop', '  Non-GAAP operating profit y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating profit (GAAP) y/y %', 'growth', 'pct', all=growth('is_op'))
    S('gm_ni', '  Income from continuing operations y/y %', 'growth', 'pct', all=growth('is_cont_att'))
    S('gm_eps', '  Non-GAAP EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_adjop_m', '  Non-GAAP operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_inc', '  Incremental non-GAAP operating margin (Δ non-GAAP operating profit / Δ revenues)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('gm_net_m', '  Net margin % (income from continuing operations attributable to Brink\'s)', 'pct', 'pct', all=ratio('is_cont_att', 'is_rev'))
    S('gm_sga', '  SG&A % of revenues', 'pct', 'pct', all=ratio('is_sga', 'is_rev'))
    S('gm_cor', '  Cost of revenues % of revenues', 'pct', 'pct', all=ratio('is_cor', 'is_rev'))
    blank()
