"""Row specification of the THEON Model sheet, part 1 (MLM template layout and process):
revenue build (night vision · thermal · platform-based / ISR & other) -> deal blocks (MERIO, HGH, future bolt-ons) -> group revenue & FY26 outlook
calibration -> adjusted EBIT margin build -> cost drivers -> IFRS income statement -> IFRS-to-adjusted bridges -> growth & margins."""
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
def Q3v(key): return f'${Q3}${R[key]}'
def Q2v(key): return f'${Q2}${R[key]}'
def H2(key): return f'({Q3}{R[key]}+{Q4}{R[key]})'
def yr(): return CTX.col.year

LINES = [('nv', 'Night vision devices', 'pr_night', 'NV_G'), ('th', 'Thermal imaging devices', 'pr_thermal', 'TH_G'),
         ('pl', 'Platform-based, ISR & other (incl. Kappa Optronics from 14-Jan-2026; services & spares)', 'pr_other', 'PL_G')]

# ====================================================================== scenario table
SCEN_ROWS = []
def scen_layout(V0):
    r = 9
    SCEN_ROWS.append((r, 'hdr', 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear',
                      'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of the FY26 guidance (company releases; unverified — not on EDGAR).'))
    r = 11
    SCEN_ROWS.append((r, 'out_hdr', V0['out_hdr'], 'High', 'Mid', 'Low', V0['out_note'])); r += 1
    for key, lab, (hi, mid, lo), nf, note in V0['outlook']:
        SC[key] = r; SCEN_ROWS.append((r, 'out', lab, hi, mid, lo, note, nf)); r += 1
    r += 1
    SCEN_ROWS.append((r, 'pt_hdr', 'FY26 point estimates and deal inputs (all cases)', None, None, None, None)); r += 1
    for key, lab, vals, nf, note in V0['points']:
        SC[key] = r
        if isinstance(vals, tuple): SCEN_ROWS.append((r, 'out', lab, vals[0], vals[1], vals[2], note, nf))
        else: SCEN_ROWS.append((r, 'pt', lab, None, vals, None, note, nf))
        r += 1
    r += 1
    for key, lab, (a, b, c), _nf, note in V0['levers']:
        SC[key] = r; SCEN_ROWS.append((r, 'lev', lab, a, b, c, note)); r += 1
    r += 1
    for name, lab, dbull, dbear, base, note, nf, clamp in V0['blocks']:
        SCEN_ROWS.append((r, 'blk', lab, dbull, 'Δ →', dbear, note, nf)); hdr = r; r += 1
        SC[name] = {}
        for y, b in zip((2027, 2028, 2029, 2030), base):
            SC[name][y] = r; SCEN_ROWS.append((r, 'yr', f'  {y}E', hdr, b, clamp, None, nf)); r += 1
    return r

# ====================================================================== row spec
def build_spec(V0):
    S = add
    # ------------------------------------------------------------------ REVENUE BUILD
    S('sec_rv', 'REVENUE BUILD — NIGHT VISION · THERMAL · PLATFORM-BASED / ISR & OTHER (single reportable segment: Optronics)', 'section',
      note='REVENUE BUILD — modelling logic (product categories from the revenue-disaggregation note; Q3/Q4-26E: prior-year quarter × (1 + 1H/26 y/y + calibration Δ); 2027E+: scenario growth)')
    blank()
    for k, title, data, code in LINES:
        S(f'{k}_hdr', title, 'block', note=f'{title.split(" (")[0].upper()} — modelling logic')
        if k == 'pl':
            qe = lambda k=k: f'={Q2v(k)}*(1+{Q3v("cal_g")})'
            notek = ('Residual of revenue after night vision and thermal (company categories changed: "Platform based", "ISR", "Miscellaneous", "Other"; combined here so the '
                     'series is consistent). Q3/Q4-26E: Q2-26 run-rate (Kappa consolidated from 14-Jan-2026, so y/y growth is not meaningful) × (1 + calibration Δ). 2027E+: prior year × (1 + scenario growth).')
        else:
            qe = lambda k=k: f'={P(k)}*(1+{V(k + "_pre")}+{Q3v("cal_g")})'
            notek = ('As published in the revenue-disaggregation note (Q1 / H1 / 9M / FY documents; discrete quarters = YTD differences). Forecast: Q3/Q4-26E prior-year quarter × '
                     '(1 + 1H/26 y/y growth + uniform calibration Δ); 2027E+ prior year × (1 + scenario growth).') if k == 'nv' else None
        S(k, '  Revenue (EUR m)', 'line', 'm1', data=data, flow=True, qe=qe,
          ae=lambda k=k, code=code: f'={P(k)}*(1+{CH(SC[code][yr()])})', note=notek)
        S(k + '_g', '    y/y %', 'growth', 'pct', all=growth(k))
        if k != 'pl':
            S(k + '_pre', '    Q3/Q4-26E growth before calibration (1H/26 y/y)', 'driver', 'pct',
              qe=lambda k=k: f'=IFERROR(({Q1}{R[k]}+{Q2}{R[k]})/({Q(k, 2025, 1)}+{Q(k, 2025, 2)})-1,0)')
        S(k + '_mix', '    % of revenue', 'pct', 'pct', all=ratio(k, 'is_rev'))
        blank()
    S('rg_hdr', 'Memo: revenue by primary geographic market (as published)', 'block', note='GEOGRAPHY — memo (history only); Greece <0.1% of revenue (export model)')
    for k, lab in (('rg_eu', '  Europe'), ('rg_asia', '  Asia'), ('rg_am', '  Americas'), ('rg_row', '  Africa, Oceania & other (derived: revenue − listed regions)')):
        S(k, lab, 'memo', 'm1', data=k)
    S('rg_eu_pct', '  Europe % of revenue', 'pct', 'pct', all=ratio('rg_eu', 'is_rev'))
    S('rg_asia_g', '  Asia y/y %', 'growth', 'pct', all=growth('rg_asia'))
    blank()
    S('kp_hdr', 'Operating KPIs — order intake, soft backlog and options (company releases)', 'block',
      note='KPIs — company definitions: soft backlog = remaining contract value of existing and anticipated contracts; options = contractual options on top of soft backlog')
    S('kp_oi', '  Order intake (EUR m; quarters = YTD differences)', 'memo', 'm1', data='order_intake',
      note='Year-to-date order intake as printed in each release; discrete quarters derived. Q4-25 includes the c.EUR 1bn OCCAR firm order for 100,000 NVGs (Bundeswehr).')
    S('kp_btb', '  Book-to-bill (x)', 'line', 'x2', hist=lambda: f'=IF(ISNUMBER({V("kp_oi")}),IFERROR({V("kp_oi")}/{V("is_rev")},""),"")')
    S('kp_bl', '  Soft backlog at period end (EUR m)', 'memo', 'm1', data='soft_backlog')
    S('kp_opt', '  Options on soft backlog (EUR m)', 'memo', 'm1', data='options')
    S('kp_cov', '  Soft backlog / next-12-month revenue proxy (soft backlog ÷ revenue × 4 or × 1) (x)', 'line', 'x2',
      hist=lambda: f'=IF(ISNUMBER({V("kp_bl")}),IFERROR({V("kp_bl")}/({V("is_rev")}*{4 if CTX.col.q else 1}),""),"")')
    blank()

    # ------------------------------------------------------------------ DEAL BLOCKS
    S('dl_sec', 'ACQUISITIONS — MERIO (80%, closing Q4-26) · HGH SYSTÈMES INFRAROUGES (100%, closing ~1-Jan-2027) · FUTURE BOLT-ONS', 'section',
      note='DEALS — announced after the FY26 guidance (Feb-26), so carried outside the calibration (KRMN precedent). Undisclosed terms are labelled ASSUMPTION.')
    S('me_hdr', 'MERIO SAS (France; gyrostabilised gimbals / turrets for UAV, C-UAS, ground and maritime) — 80% stake', 'block',
      note='MERIO — binding terms 4-May-2026; approvals received, completion underway 29-Oct-2026. Price NOT disclosed ("accretive EBIT multiple") → assumption.')
    S('me_rev', '  MERIO revenue consolidated (EUR m)', 'line', 'm1', qe=lambda: f'={PT("pt_me_q4")}' if CTX.col.q == 4 else '=0',
      e26=lambda: S26('me_rev'), ae=lambda: (f'={PT("pt_me_fy")}*(1+{CH(SC["PL_G"][2027])})' if yr() == 2027 else f'={P("me_rev")}*(1+{CH(SC["PL_G"][yr()])})'),
      flow=True, note='Company: FY2026 revenue "above EUR 15m", EBIT "above EUR 3.5m". Q4-26E = c.2 months from 1-Nov-2026 (assumption). 2027E = FY26 standalone × (1 + platform growth).')
    S('me_ebit', '  MERIO adjusted EBIT (EUR m)', 'line', 'm1', qe=lambda: f'={V("me_rev")}*{PT("pt_me_m")}', e26=lambda: S26('me_ebit'),
      ae=lambda: f'={V("me_rev")}*{PT("pt_me_m")}', flow=True, note='Margin = company FY26 EBIT ÷ revenue (>3.5 / >15 ≈ 23%).')
    S('me_px', '  MERIO consideration for 80% (EUR m; ASSUMPTION — not disclosed)', 'driver', 'm1', e26=lambda: f'={PT("pt_me_px")}',
      note='ASSUMPTION: c.13x FY26 EBIT for 100% (below THEON\'s own EV/EBIT, consistent with "accretive"), × 80%. Replace with the Q3/FY26 report figure.')
    blank()
    S('hg_hdr', 'HGH Systèmes Infrarouges (SAS Stéropès; France; EO/IR surveillance and C-UAS; seller Carlyle) — 100%', 'block',
      note='HGH — exclusivity 17-Jun-2026; EV c.EUR 300m; closing "by the beginning of 2027"; funded entirely by the new EUR 325m term loan. Toggle and EV in the scenario table.')
    S('hg_on', '  Deal toggle (1 = HGH consolidated from 1-Jan-2027)', 'driver', 'gen', ae=lambda: f'={PT("pt_hg_on")}')
    S('hg_rev', '  HGH revenue (EUR m)', 'line', 'm1', ae=lambda: (f'={V("hg_on")}*{PT("pt_hg_rev")}*(1+{CH(SC["HG_G"][2027])})' if yr() == 2027
                                                             else f'={V("hg_on")}*IFERROR({P("hg_rev")}/{P("hg_on")},0)*(1+{CH(SC["HG_G"][yr()])})'),
      note='Company: "c. EUR 40 million of revenues" with c.30% revenue CAGR (taken as the 2026 base; ASSUMPTION on the base year). Growth = scenario lever.')
    S('hg_ebitda_m', '  HGH standalone EBITDA margin % (derived from the stated deal multiple)', 'driver', 'pct', ae=lambda: f'={PT("pt_hg_m")}',
      note='Derived, not disclosed: EV EUR 300m ÷ "mid- to high-teens" EV/EBITDA (16.5x mid) = c.EUR 18m EBITDA on c.EUR 40m revenue (≈45%). ASSUMPTION — HGH financials are not published.')
    S('hg_syn', '  Run-rate synergies (EUR m; phased 1/3, 2/3, 100% from 2027E)', 'line', 'm1',
      ae=lambda: f'={V("hg_on")}*{PT("pt_hg_syn")}*{ {2027: "1/3", 2028: "2/3"}.get(yr(), "1") }',
      note='Company: c.10x EV/EBITDA "post the full impact of run-rate synergies by year 2 to 3" → EUR 300m ÷ 10 − c.EUR 18m standalone ≈ EUR 12m (derived; unverified).')
    S('hg_ebitda', '  HGH EBITDA incl. synergies (EUR m)', 'line_b', 'm1', ae=lambda: f'={V("hg_rev")}*{V("hg_ebitda_m")}+{V("hg_syn")}')
    S('hg_dep', '  HGH depreciation (% of revenue, ASSUMPTION 3%)', 'line', 'm1', ae=lambda: f'={V("hg_rev")}*{PT("pt_hg_dep")}')
    S('hg_amort', '  HGH purchase-price amortisation (intangibles % of EV ÷ life; ASSUMPTION)', 'line', 'm1',
      ae=lambda: f'={V("hg_on")}*{PT("pt_hg_ev")}*{PT("pt_hg_int")}/{PT("pt_hg_life")}',
      note='ASSUMPTION: identified intangibles 25% of EV, 10-year life (Kappa PPA: intangibles EUR 27.1m of EUR 69.9m = 39%). THEON adjusted EBIT does not exclude amortisation.')
    S('hg_ebit', '  HGH adjusted EBIT (EUR m)', 'total', 'm1', ae=lambda: f'={V("hg_ebitda")}-{V("hg_dep")}-{V("hg_amort")}')
    S('hg_ev', '  HGH enterprise value paid at closing (EUR m)', 'line', 'm1', ae=lambda: f'={V("hg_on")}*{PT("pt_hg_ev")}' if yr() == 2027 else '=0',
      note='Company: EV c.EUR 300m (cash-free / debt-free assumed); funded by the EUR 325m term loan drawn at closing.')
    blank()
    S('ma_hdr', 'Future bolt-on M&A lever (company: "small bolt-on M&A", organic growth >15% "supported by bolt-on M&A")', 'block',
      note='FUTURE M&A — spend (scenario) ÷ EV/sales → acquired revenue (half-year in the deal year); margin input; consideration to goodwill & intangibles')
    S('ma_sp', '  Acquisition spend (EUR m)', 'line', 'm1', ae=lambda: f'={CH(SC["MA"][yr()])}')
    S('ma_evs', '  EV / sales paid (x)', 'driver', 'x', ae_in=V0['ma_evs'], note='Kappa EV EUR 75m on c.EUR 40m FY26 revenue = 1.9x; HGH EUR 300m on c.EUR 40m = 7.5x. Base 3.0x (assumption).')
    S('ma_rev', '  Acquired revenue (EUR m; half-year in the deal year, then grows with platform)', 'line', 'm1',
      ae=lambda: (f'={V("ma_sp")}/{V("ma_evs")}*0.5' if yr() == 2027 else
                  f'=N({P("ma_rev")})*(1+{CH(SC["PL_G"][yr()])})+{P("ma_sp")}/{V("ma_evs")}*0.5+{V("ma_sp")}/{V("ma_evs")}*0.5'))
    S('ma_m', '  Acquired adjusted EBIT margin %', 'driver', 'pct', ae_in=V0['ma_m'], note='Assumption below the group margin (sub-scale targets; MERIO c.23%).')
    S('ma_ebit', '  Acquired adjusted EBIT (EUR m)', 'line', 'm1', ae=lambda: f'={V("ma_rev")}*{V("ma_m")}')
    blank()

    # ------------------------------------------------------------------ GROUP & CALIBRATION
    S('g_hdr', 'Group Total — revenue build → FY26 outlook calibration (guidance basis excludes MERIO)', 'block',
      note='GROUP TOTAL — modelling logic (Σ product lines + deals; FY26 guidance EUR 570–600m set 16-Feb-2026, reiterated 27-Jul-2026; unverified — company release, not EDGAR)')
    S('g_org', 'Revenue — existing portfolio (Σ product lines; guidance basis)', 'line_b', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("nv")}),{V("nv")}+{V("th")}+{V("pl")},{V("is_rev")})', fc=lambda: f'={V("nv")}+{V("th")}+{V("pl")}',
      note='FY2021 has no product split (revenue as reported). Includes Kappa Optronics from 14-Jan-2026 (inside the FY26 guidance).')
    S('g_rev', 'Revenue (build)', 'total', 'm1', hist=lambda: f'={V("g_org")}', fc=lambda: f'={V("g_org")}+N({V("me_rev")})+N({V("hg_rev")})+N({V("ma_rev")})')
    S('g_rev_g', '  Revenue y/y %', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: build vs consolidated revenue (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=0.001,0,ROUND({V("g_rev")}-{V("is_rev")},3)),"")')
    S('g_orgg', '  Existing-portfolio growth % (Kappa included from 2026; MERIO in 2027E+ once annualised; HGH / bolt-ons excluded)', 'growth', 'pct',
      all=growth('g_org'), ae=lambda: f'=IFERROR(({V("g_org")}+N({V("me_rev")}))/({P("g_org")}+N({P("me_rev")}))-1,"")',
      note='Company medium-term target: organic growth >15% p.a. (unverified). H1-26 organic growth as published: 24.7% (Kappa excluded). 2027E+: existing portfolio incl. MERIO once annualised.')
    S('cal_rev', '  Memo: FY26 revenue guidance end-point (scenario; EUR m)', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_rev']), note=V0['rev_guid_note'])
    S('cal_sens', '  Calibration helper: FY26 revenue sensitivity to +1.00 of growth Δ (Q3/Q4 bases)', 'driver', 'm1',
      e26=lambda: '=' + '+'.join(f'{Q(k, 2025, 3)}+{Q(k, 2025, 4)}' for k in ('nv', 'th')) + f'+2*{Q2}{R["pl"]}',
      note='Σ prior-year Q3/Q4 revenue of night vision and thermal + 2 × Q2-26 platform run-rate: the revenue added by +1.00 of Δ (closed-form linear solve; no goal-seek).')
    S('cal_pre', '  Calibration helper: FY26 revenue before calibration (Δ = 0)', 'driver', 'm1',
      e26=lambda: (f'={Q1}{R["g_org"]}+{Q2}{R["g_org"]}+' + '+'.join(f'{QC[(2025, q)].c}{R[k]}*(1+{QC[(2026, q)].c}{R[k + "_pre"]})' for k in ('nv', 'th') for q in (3, 4))
                   + f'+2*{Q2}{R["pl"]}'))
    S('cal_g', '  Outlook calibration: uniform Δ growth (pts) on the remaining quarters', 'driver', 'pct',
      qe=lambda: f'=IFERROR(({V("cal_rev", E26)}-{V("cal_pre", E26)})/{V("cal_sens", E26)},0)' if CTX.col.q == 3 else f'={Q3v("cal_g")}',
      note='Δ = (guidance end-point − revenue before calibration) ÷ sensitivity. Same Δ in Q3 and Q4.')
    S('cal_rev_chk', '  Check: FY26 revenue (guidance basis) vs guidance end-point (should be 0)', 'check', 'm1', e26=lambda: f'=ROUND({V("g_org")}-{V("cal_rev")},3)')
    blank()

    # ------------------------------------------------------------------ MARGIN BUILD
    S('m_hdr', 'Profitability build — adjusted EBIT margin (company definition) → FY26 outlook calibration', 'block',
      note='MARGIN BUILD — Q3/Q4-26E: prior-year quarter margin (current definition) + uniform Δ solved to the FY26 "mid-twenties" adjusted EBIT margin; 2027E+: scenario margin on the existing portfolio')
    S('m_org', '  Adjusted EBIT margin % — existing portfolio (current definition, incl. share of profit of core equity-accounted investees)', 'pct', 'pct',
      hist=lambda: f'=IF(ISNUMBER({V("r_ebit")}),IFERROR({V("r_ebit")}/{V("is_rev")},""),"")',
      qe=lambda: f'={P("m_org")}+{Q3v("cal_m")}', e26=lambda: f'=IFERROR(({V("r_ebit")}-N({V("me_ebit")}))/{V("g_org")},"")',
      ae=lambda: '=' + CH(SC['MRG'][yr()]),
      note='Historical = model adjusted EBIT (current definition) ÷ revenue. FY26 guidance "mid-twenties" margin (H1-26 26.2%). 2027E+: scenario lever on the existing portfolio + MERIO.')
    S('cal_mg', '  Memo: FY26 adjusted EBIT margin guidance end-point (scenario)', 'memo', 'pct', e26=lambda: '=' + CH(SC['out_m']))
    S('cal_m', '  Outlook calibration: Δ adjusted EBIT margin vs prior-year quarter (Q3/Q4-26E)', 'driver', 'pct',
      qe=lambda: (f'=({V("cal_mg", E26)}*{V("g_org", E26)}-{Q1}{R["g_ebit_org"]}-{Q2}{R["g_ebit_org"]}-{Q3}{R["g_org"]}*{QC[(2025, 3)].c}{R["m_org"]}'
                  f'-{Q4}{R["g_org"]}*{QC[(2025, 4)].c}{R["m_org"]})/({Q3}{R["g_org"]}+{Q4}{R["g_org"]})') if CTX.col.q == 3 else f'={Q3v("cal_m")}',
      note='Solves the uniform shift so FY26 adjusted EBIT of the existing portfolio ÷ guidance-basis revenue = the guidance end-point (closed form).')
    S('g_ebit_org', '  Adjusted EBIT — existing portfolio (EUR m)', 'line', 'm1', hist=lambda: f'={V("r_ebit")}',
      qe=lambda: f'={V("g_org")}*{V("m_org")}', e26=lambda: S26('g_ebit_org'), ae=lambda: f'={V("g_org")}*{V("m_org")}')
    S('cal_m_chk', '  Check: FY26 adjusted EBIT margin (guidance basis) vs guidance end-point (should be 0)', 'check', 'pct',
      e26=lambda: f'=ROUND({V("g_ebit_org")}/{V("g_org")}-{V("cal_mg")},5)')
    S('g_adj', 'Adjusted EBIT (build: existing portfolio + MERIO + HGH + bolt-ons)', 'total', 'm1', hist=lambda: f'={V("r_ebit")}',
      qe=lambda: f'={V("g_ebit_org")}+N({V("me_ebit")})', e26=lambda: S26('g_adj'),
      ae=lambda: f'={V("g_ebit_org")}+N({V("me_ebit")})+N({V("hg_ebit")})+N({V("ma_ebit")})',
      note="THEON's guided profit KPI (company definition: EBIT + non-recurring items; from Q2-25 includes the share of profit of core equity-accounted investees). Drives the IFRS P&L below.")
    S('g_adj_m', '  Adjusted EBIT margin % (group)', 'pct', 'pct', all=ratio('g_adj', 'is_rev'))
    S('g_chk_adj', '  Check: build vs adjusted EBIT bridge (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_adj")}),ISNUMBER({V("r_ebit")})),IF(ABS({V("g_adj")}-{V("r_ebit")})<=0.001,0,ROUND({V("g_adj")}-{V("r_ebit")},3)),"")')
    S('tg_h', '  Medium-term targets vs model — information, not forced (company releases; unverified):', 'sub', 'gen')
    S('tg_org', '    Organic growth vs >15% p.a. target (model − 15%)', 'memo_calc', 'pct', ae=lambda: f'=IFERROR({V("g_orgg")}-0.15,"")')
    S('tg_1bn', '    EUR 1bn revenue target "ahead of 2030" (model revenue − EUR 1,000m)', 'memo_calc', 'm1', ae=lambda: f'={V("is_rev")}-1000')
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers, D&A and other operating items', 'block',
      note='COST DRIVERS — D&A = adjusted EBITDA − adjusted EBIT (company reconciliation); Q3/Q4-26E at the Q2-26 run-rate; 2027E+ % of revenue + deal D&A')
    S('d_dna', '  Depreciation & amortisation (company bridge: adjusted EBITDA − adjusted EBIT)', 'line', 'm1', data='dna', flow=True,
      qe=lambda: f'={Q2v("d_dna")}', e26=lambda: S26('d_dna'),
      ae=lambda: f'=({V("g_org")}+N({V("me_rev")})+N({V("ma_rev")}))*{V("d_dna_pct")}+N({V("hg_dep")})+N({V("hg_amort")})',
      note='Includes Kappa purchase-price amortisation from 2026 (H1-26 amortisation EUR 1.9m). Q4-23 prints −0.03 (9M-23 comparative D&A 1.30 > FY23 1.27): source inconsistency, kept as reported.')
    S('d_dna_pct', '  D&A % of revenue (existing portfolio, MERIO and bolt-ons)', 'pct', 'pct', all=ratio('d_dna', 'is_rev'), ae_in=V0['dna_pct'])
    S('d_assoc', '  Share of profit of core equity-accounted investees (inside operating profit and adjusted EBIT)', 'line', 'm1', data='assoc', flow=True,
      qe=lambda: f'=({Q1}{R["d_assoc"]}+{Q2}{R["d_assoc"]})/2', e26=lambda: S26('d_assoc'), ae=lambda: f'={P("d_assoc")}',
      note='Associates (Kopin Europe 49%, ShockEOS 30%, Andres etc.). Presented inside operating profit from Q2-25 (2024 restated); shown separately in every period. Forecast held at the 1H/26 run-rate.')
    S('d_nri', '  Non-recurring items (company adjusting items; mainly legal, due-diligence and acquisition costs)', 'line', 'm1', data='nri', flow=True,
      qe_in={3: V0['nri_q'], 4: V0['nri_q']}, e26=lambda: S26('d_nri'), ae=lambda: f'={V0["nri_ae"]}+N({V("hg_on")})*{V0["nri_hgh"] if yr() == 2027 else 0}',
      note='Forecast: nil, except an ASSUMED EUR 5m of HGH transaction / integration costs in 2027E (not company-guided).')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF PROFIT OR LOSS (IFRS)', 'section',
      note='CONSOLIDATED IS — forecast logic (operating profit = adjusted EBIT − non-recurring items; gross profit / opex shown historically; net finance from the debt and cash schedules)')
    S('is_rev', 'Revenue', 'total', 'm1', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the revenue build.')
    S('is_cogs', 'Cost of sales', 'line', 'm1', data='cogs', flow=True, fc=lambda: f'={V("is_rev")}*(1-{V("is_gm")})')
    S('is_gp', 'Gross profit', 'line_b', 'm1', hist=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_rev")}-{V("is_cogs")},"")', fc=lambda: f'={V("is_rev")}-{V("is_cogs")}')
    S('is_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'), qe=lambda: f'={P("is_gm")}', ae=lambda: f'={P("is_gm")}',
      note='Forecast held at the prior-year level (drives cost of sales for working-capital days only; profit is driven by the adjusted EBIT margin).')
    S('is_oinc', 'Other income', 'line', 'm1', data='oinc', flow=True)
    S('is_admin', 'Administrative expenses', 'line', 'm1', data='admin', flow=True)
    S('is_sell', 'Selling and distribution expenses', 'line', 'm1', data='sell', flow=True)
    S('is_rnd', 'Research and development expenses', 'line', 'm1', data='rnd', flow=True)
    S('is_oexp', 'Other expenses and impairment losses on financial assets', 'line', 'm1', data='oexp', flow=True)
    S('is_opex', 'Operating expenses net of other income (forecast: implied)', 'line', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_admin")}),{V("is_admin")}+{V("is_sell")}+{V("is_rnd")}+{V("is_oexp")}-{V("is_oinc")},"")',
      fc=lambda: f'={V("is_gp")}+{V("is_assoc")}-{V("is_op")}', note='Forecast = gross profit + share of associates − operating profit (the balancing line).')
    S('is_assoc', 'Share of profit of core equity-accounted investees', 'line', 'm1', all=lambda: f'=N({V("d_assoc")})')
    S('is_op', 'Operating profit (EBIT; current presentation incl. share of associates)', 'total', 'm1', data='op', flow=True,
      fc=lambda: f'={V("g_adj")}-{V("d_nri")}', e26=lambda: S26('is_op'),
      note='Historical: as printed, plus the share of associates where the document presented it below operating profit (pre-Q2-25 documents). Forecast = adjusted EBIT − non-recurring items.')
    S('is_op_chk', '  Check: gross profit − opex + associates = operating profit (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_opex")}),IF(ABS({V("is_gp")}-{V("is_opex")}+{V("is_assoc")}-{V("is_op")})<=0.002,0,ROUND({V("is_gp")}-{V("is_opex")}+{V("is_assoc")}-{V("is_op")},3)),"")')
    S('is_opm', '  Operating margin %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('is_finc', 'Finance income (interest and fair-value gains on financial assets)', 'line', 'm1', data='finc', flow=True,
      qe=lambda: f'=({Q1}{R["is_finc"]}+{Q2}{R["is_finc"]}-{V0["fv_h126"]})/2', e26=lambda: S26('is_finc'), ae=lambda: f'={P("bs_cash")}*{V("ls_yield")}',
      note='Q1/H1-26 include the Exosens mark-to-market (H1-26 net FVTPL gains EUR 37.2m; FVTPL financial asset). Forecast: interest only (1H/26 ex-FV run-rate; 2027E+ opening cash × yield); no fair-value changes assumed.')
    S('is_fcost', 'Finance costs', 'line', 'm1', data='fcost', flow=True, qe=lambda: f'={Q2v("is_fcost")}', e26=lambda: S26('is_fcost'),
      ae=lambda: f'=({P("bs_debt")}+{V("dt_tl")})*{V("ls_rate")}',
      note='Q3/Q4-26E at the Q2-26 run-rate (EUR 300m RCF fully drawn from 2-Jan-2026). 2027E+: opening bank debt × rate (no circularity); the HGH term loan is drawn at 1-Jan-2027, so it is in opening debt of 2027E via the draw row below.')
    S('is_ebt', 'Profit before tax', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_op")}),{V("is_op")}+{V("is_finc")}-{V("is_fcost")},"")')
    S('is_tax', 'Income tax expense (current + deferred)', 'line', 'm1', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}', e26=lambda: S26('is_tax'))
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Greek operating subsidiary (22% statutory) with Cyprus holding; FY25 23.1%, FY24 23.4%. H1-26 17.8% is lowered by the largely untaxed Exosens fair-value gain.')
    S('is_ni', 'Profit for the period after tax', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_ni_chk', '  Check: profit after tax vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=0.002,0,ROUND({V("is_ni")}-{V("is_ni_pub")},3)),"")')
    S('is_ni_pub', '  Memo: profit after tax as reported', 'memo', 'm1', data='ni', flow=True)
    S('is_nci', '  Non-controlling interests (Harder Digital 40% minority from Oct-2024)', 'line', 'm1', data='nci', flow=True,
      qe=lambda: f'={V("is_ni")}*{PT("pt_nci")}', e26=lambda: f'={MAN["nci_profit"]["H1-26"]}+{H2("is_nci")}', ae=lambda: f'={V("is_ni")}*{PT("pt_nci")}',
      note='Printed only in H1 / FY statements (the Q1 / 9M updates carry no split), so quarterly history is blank. 2026E = H1-26 actual + 2H estimate.')
    S('is_nip', 'Profit attributable to owners of the Company', 'total', 'm1', all=lambda: f'=IF(AND(ISNUMBER({V("is_ni")}),ISNUMBER({V("is_nci")})),{V("is_ni")}-{V("is_nci")},"")')
    S('is_dda', '  Memo: depreciation & amortisation', 'memo_calc', 'm1', all=lambda: f'=IF(ISNUMBER({V("d_dna")}),{V("d_dna")},"")')
    S('eps_hdr', '(Earnings per share — basic = diluted; pre-IPO per-share data not meaningful: 200,000 shares to FY2021, split x100 in Nov-2023)', 'sub', 'gen')
    S('sh_dil', '  Weighted-average shares, basic = diluted (m)', 'line', 'm1', data='sh_w',
      qe=lambda: f'={MAN["shares"]["H1-26"]}', e26=lambda: f'={MAN["shares"]["H1-26"]}', ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='As published in the EPS notes (annual). 2026E = H1-26 weighted average (77.59m; rights-issue shares in issue all year). 2027E+: average of beginning / ending shares outstanding.')
    S('eps_dil', 'EPS – basic = diluted (EUR)', 'eps_total', 'ps', all=lambda: f'=IF(AND(ISNUMBER({V("sh_dil")}),ISNUMBER({V("is_nip")})),IFERROR({V("is_nip")}/{V("sh_dil")},""),"")')
    S('eps_g', '  EPS y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS as reported (EUR)', 'eps_memo', 'ps', data='eps_pub')
    S('eps_chk', '  Check: model EPS vs reported (should be 0.00; ±0.006 rounding to 2 dp)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_dil")})),IF(ABS({V("eps_dil")}-{V("eps_pub")})<=0.006,0,ROUND({V("eps_dil")}-{V("eps_pub")},3)),"n/p")')
    S('eps_q1', '  Memo: Q1 EPS as printed in the Q1 trading-update release (EUR)', 'eps_memo', 'ps', data='eps_q1')
    S('dps', '  Dividend per share declared for the financial year (EUR; paid the following June)', 'line', 'ps',
      hist=lambda: (f'={MAN["dps"][str(yr())]}' if str(yr()) in MAN['dps'] and CTX.col.q is None else None),
      e26=lambda: f'={V("pay")}*{V("is_nip")}/{V("bb_end")}', ae=lambda: f'={V("pay")}*{V("is_nip")}/{V("bb_end")}',
      note='FY2023 EUR 0.206 (EUR 14.4m), FY2024 EUR 0.34 (EUR 23.8m), FY2025 EUR 0.31 (EUR 24.4m; 30% payout). Forecast DPS = payout × net income attributable ÷ year-end shares.')
    S('pay', '  Dividend payout ratio (% of net income attributable)', 'pct', 'pct', e26=lambda: f'={CH(SC["lv_pay"])}', ae=lambda: f'={CH(SC["lv_pay"])}',
      note='Company policy 20–30% of net income (FY2025: 30%, top of the range).')
    blank()

    # ------------------------------------------------------------------ RECON 1: EBIT
    S('sec_r1', 'RECONCILIATION: PROFIT AFTER TAX → EBIT → ADJUSTED EBIT → ADJUSTED EBITDA (company APM, as published)', 'section',
      note='ADJUSTED EBIT / EBITDA — company: profit after tax + income tax − net finance = EBIT; + non-recurring items = adjusted EBIT; + D&A = adjusted EBITDA')
    S('r_ni', 'Profit after tax', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('r_tax', '  (+) Income tax expense', 'line', 'm1', all=lambda: f'={V("is_tax")}')
    S('r_nf', '  (+) Net finance costs (finance costs − finance income)', 'line', 'm1', all=lambda: f'={V("is_fcost")}-{V("is_finc")}')
    S('r_op', '  = EBIT (current definition, incl. share of associates)', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_tax")}+{V("r_nf")},"")')
    S('r_nri', '  (+) Non-recurring items', 'line', 'm1', all=lambda: f'=N({V("d_nri")})')
    S('r_ebit', '  = Adjusted EBIT (model, current definition)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_op")}),{V("r_op")}+{V("r_nri")},"")',
      note='Current definition in all periods: the share of profit of core equity-accounted investees is inside EBIT.')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('r_xa', '  (−) Share of associates where the definition in force excluded it (to Q1-25)', 'line', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_def_f")}),-(1-{V("r_def_f")})*N({V("d_assoc")}),"")')
    S('r_ebit_inf', '  = Adjusted EBIT on the definition in force when published', 'line_b', 'm1', hist=lambda: f'=IF(ISNUMBER({V("r_def_f")}),{V("r_ebit")}+{V("r_xa")},"")')
    S('r_ebit_pub', '  Company-published adjusted EBIT (definition in force)', 'memo', 'm1', data='adj_ebit_pub', flow=True,
      note='Q2/Q3/Q4 = YTD differences on one definition (Q2-25 = H1-25 − restated Q1-25 of the Q1-26 update). FY2021: not published.')
    S('r_ebit_chk', '  Check: model vs company-published adjusted EBIT (should be 0; ±0.002)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_ebit_pub")}),IF(ABS({V("r_ebit_inf")}-{V("r_ebit_pub")})<=0.002,0,ROUND({V("r_ebit_inf")}-{V("r_ebit_pub")},3)),"n/p")')
    S('r_def_f', '  Definition flag (1 = share of associates inside adjusted EBIT / EBITDA)', 'line', 'gen', data='adj_def')
    S('r_dna', '  (+) Depreciation & amortisation', 'line', 'm1', all=lambda: f'=N({V("d_dna")})')
    S('r_adj', '  = Adjusted EBITDA (model, current definition)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ebit")}),{V("r_ebit")}+{V("r_dna")},"")')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_adj_pub', '  Company-published adjusted EBITDA (definition in force)', 'memo', 'm1', data='adj_ebitda_pub', flow=True)
    S('r_adj_chk', '  Check: model (definition in force) vs company-published adjusted EBITDA (should be 0; ±0.002)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_adj_pub")}),IF(ABS({V("r_ebit_inf")}+{V("r_dna")}-{V("r_adj_pub")})<=0.002,0,ROUND({V("r_ebit_inf")}+{V("r_dna")}-{V("r_adj_pub")},3)),"n/p")')
    S('r_def', '  Definition basis (company adjusted EBIT / EBITDA definition in force)', 'text', 'gen',
      note='Definition changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('r_xt', '  Memo: adjusted EBIT, guidance basis (existing portfolio; excl. MERIO / HGH / bolt-ons)', 'memo_calc', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_ebit")}),{V("r_ebit")}-N({V("me_ebit")})-N({V("hg_ebit")})-N({V("ma_ebit")}),"")')
    S('r_xt_m', '  Memo: adjusted EBIT margin, guidance basis %', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("r_xt")}),IFERROR({V("r_xt")}/{V("g_org")},""),"")')
    blank()

    # ------------------------------------------------------------------ RECON 2
    S('sec_r2', 'RECONCILIATION: OPERATING PROFIT → ADJUSTED OPERATING PROFIT (= adjusted EBIT; company items only)', 'section',
      note='ADJUSTED OPERATING PROFIT — THEON adjusts only for the non-recurring items it quantifies (no amortisation, SBC or FX add-backs)')
    S('o_op', 'Operating profit (IFRS, current presentation)', 'line_b', 'm1', all=lambda: f'={V("is_op")}')
    S('o_nri', '  (+) Non-recurring items', 'line', 'm1', all=lambda: f'=N({V("d_nri")})')
    S('o_adj', '  = Adjusted operating profit', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_nri")},"")')
    S('o_chk', '  Check: adjusted operating profit vs adjusted EBIT bridge (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("o_adj")}),ISNUMBER({V("r_ebit")})),IF(ABS({V("o_adj")}-{V("r_ebit")})<=0.002,0,ROUND({V("o_adj")}-{V("r_ebit")},3)),"")')
    S('o_inc', '  Incremental adjusted EBIT margin (Δ adjusted EBIT / Δ revenue)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 3
    S('sec_r3', 'RECONCILIATION: NET INCOME → ADJUSTED NET INCOME → ADJUSTED EPS (MODEL DEFINITION — THEON publishes no adjusted EPS)', 'section',
      note='ADJUSTED EPS (model) — net income attributable + non-recurring items after tax − fair-value gains on financial assets at FVTPL (Exosens, Kopin etc.); annual columns (FV gains are not disclosed in the Q1 / 9M updates)')
    S('e_ni', 'Profit attributable to owners of the Company', 'line_b', 'm1', ann=True, all=lambda: f'={V("is_nip")}')
    S('e_nri', '  (+) Non-recurring items × (1 − effective tax rate)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(N({V("d_nri")})*(1-{V("ra_t")}),"")')
    S('e_fv', '  (−) Net fair-value gains on financial assets at FVTPL (treated as untaxed)', 'line', 'm1', ann=True, data='fv_gain',
      e26=lambda: f'={V0["fv_h126"]}', ae_in=0.0, note='From the cash-flow add-back in the H1 / FY statements (FY2024 0.10, FY2025 5.68, H1-26 37.24). Forecast: nil.')
    S('e_fvn', '  (−) Fair-value gains (sign applied)', 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("e_ni")}),-ABS(N({V("e_fv")})),"")')
    S('e_adjni', '  = Adjusted net income (model)', 'total', 'm1', ann=True, all=lambda: f'=IFERROR({V("e_ni")}+{V("e_nri")}+{V("e_fvn")},"")')
    S('e_sh', '  Weighted-average shares (m)', 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted EPS (model, EUR)', 'eps_total', 'ps', ann=True, all=ratio('e_adjni', 'e_sh'),
      note='Model definition labelled as such (ODFL / DHR precedent). The P/E in Bull-Base-Bear uses this measure because the Exosens mark-to-market inflates 2026 IFRS EPS.')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', ann=True, all=growth('e_eps'))
    S('e_def', '  Definition basis', 'text', 'gen')
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Revenue y/y %', 'growth', 'pct', all=growth('is_rev'))
    S('gm_cc', '  Organic revenue y/y % (existing portfolio)', 'growth', 'pct', all=lambda: f'=IF(ISNUMBER({V("g_orgg")}),{V("g_orgg")},"")' if CTX.col.prior else None)
    S('g_fx', '  Acquired / deal contribution to growth (pts)', 'growth', 'pct',
      all=lambda: f'=IF(AND(ISNUMBER({V("gm_rev")}),ISNUMBER({V("gm_cc")})),{V("gm_rev")}-{V("gm_cc")},"")')
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_ebit', '  Adjusted EBIT y/y %', 'growth', 'pct', all=growth('r_ebit'))
    S('gm_ni', '  Profit after tax y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_adjop_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    S('gm_inc', '  Incremental adjusted EBIT margin (Δ adjusted EBIT / Δ revenue)', 'pct', 'pct', all=incr('r_ebit', 'is_rev'))
    S('gm_op_m', '  Operating margin (IFRS) %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_opex', '  Operating expenses net of other income, % of revenue', 'pct', 'pct', all=ratio('is_opex', 'is_rev'))
    blank()
