"""Row specification of the ONON Model sheet, part 1 (MLM template layout and process):
region build (constant-currency growth + FX translation) -> channel / product mix -> group net sales & FY26 outlook calibration ->
gross margin & Adjusted EBITDA margin build -> cost drivers -> IFRS income statement -> IFRS-to-adjusted bridges -> growth & margins."""
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
def Q4v(key): return f'${Q4}${R[key]}'

RGS = [('am', 'Americas', 'AM'), ('emea', 'Europe, Middle East & Africa (EMEA)', 'EMEA'), ('apac', 'Asia-Pacific (APAC)', 'APAC')]
def sprior(): return '+'.join(P(k) for k, _, _ in RGS)

# ====================================================================== scenario table (AU:AY)
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
    SCEN_ROWS.append((r, 'pt_hdr', 'FY26 point estimates (all cases)', None, None, None, None)); r += 1
    for key, lab, vals, nf, note in V0['points']:
        SC[key] = r
        if isinstance(vals, tuple): SCEN_ROWS.append((r, 'out', lab, vals[0], vals[1], vals[2], note, nf))
        else: SCEN_ROWS.append((r, 'pt', lab, None, vals, None, note, nf))
        r += 1
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
    # ------------------------------------------------------------------ REGION BUILD
    S('sec_rg', 'NET SALES BUILD — AMERICAS · EMEA · ASIA-PACIFIC (constant-currency growth + FX translation)', 'section',
      note='REGION BUILD — modelling logic (prior-year net sales × (1 + constant-currency growth + FX translation effect) → net sales → gross margin / Adjusted EBITDA margin → IFRS P&L)')
    blank()
    for k, title, code in RGS:
        S(f'{k}_hdr', {'am': 'Americas (United States, Canada, Latin America; largest wholesale & DTC market)',
                       'emea': 'Europe, Middle East & Africa (incl. home market Switzerland, Germany, UK)',
                       'apac': 'Asia-Pacific (Greater China, Japan, South Korea, Australia)'}[k], 'block',
          note=f'{title.upper()} — modelling logic')
        S(k, '  Net sales (CHF m)', 'line', 'm1', data=f'rg_{k}', flow=True,
          qe=lambda k=k: f'={P(k)}*(1+{V(k + "_ccg")}+{V(k + "_fx")})', ae=lambda k=k: f'={P(k)}*(1+{V(k + "_ccg")}+{V(k + "_fx")})',
          note=('As published on the EMEA / Americas / APAC basis (from 2023; FY2021 and 2022 quarters restated in the 2023 filings). Q4 = FY − 9M where '
                'not printed. Forecast: prior-year period × (1 + constant-currency growth + FX translation effect).') if k == 'am' else None)
        S(k + '_g', '    y/y % (reported, CHF)', 'growth', 'pct', all=growth(k))
        S(k + '_ccg', '    y/y % constant currency', 'growth', 'pct', data=f'ccg_{k}',
          qe=lambda k=k: f'={V(k + "_pre")}+{V("cal_cc")}',
          e26=lambda k=k: f'=IFERROR({V(k + "_ccs")}/{P(k)}-1,"")',
          ae=lambda k=k, code=code: '=' + CH(SC[f'{code}_CC'][CTX.col.year]),
          note=('Published from Q1-24 (company: current period retranslated at prior-year rates). Q3/Q4-26E: 1H/26 constant-currency growth (row below) + '
                'outlook calibration Δ (Group block). 2026E = Σ quarterly constant-currency sales ÷ FY25 − 1. 2027E–2030E: scenario lever.') if k == 'am' else None)
        S(k + '_fx', '    FX translation effect (pts; reported − constant currency)', 'growth', 'pct',
          all=lambda k=k: f'=IF(AND(ISNUMBER({V(k + "_g")}),ISNUMBER({V(k + "_ccg")})),{V(k + "_g")}-{V(k + "_ccg")},"")',
          qe=lambda: f'={Q3v("cal_fx")}', ae_in=V0['fx_ae'],
          note=('Q3/Q4-26E: uniform FX Δ solved so FY26 CHF net sales = the guidance end-point (company: "at current spot rates"). 2027E+: input '
                '(0 = forecasts at constant spot FX; CHF strength vs USD is the main translation risk).') if k == 'am' else None)
        S(k + '_ccs', '    Memo: constant-currency net sales (prior-year period × (1 + cc growth))', 'memo_calc', 'm1',
          all=lambda k=k: (f'=IF(AND(ISNUMBER({V(k + "_ccg")}),ISNUMBER({P(k)})),{P(k)}*(1+{V(k + "_ccg")}),"")' if CTX.col.prior else None),
          e26=lambda k=k: f'=SUM({Q1}{R[k + "_ccs"]}:{Q4}{R[k + "_ccs"]})')
        S(k + '_pre', '    Q3/Q4-26E cc growth before calibration (1H/26 constant-currency growth)', 'driver', 'pct',
          qe=lambda k=k: f'=IFERROR(({Q1}{R[k + "_ccs"]}+{Q2}{R[k + "_ccs"]})/({Q(k, 2025, 1)}+{Q(k, 2025, 2)})-1,0)')
        S(k + '_mix', '    % of net sales', 'pct', 'pct', all=ratio(k, 'g_rev'))
        blank()

    # ------------------------------------------------------------------ group total & outlook calibration
    S('g_hdr', 'Group Total — net sales (region build) → FY26 outlook calibration (constant-currency growth, CHF net sales, Q3 guide)', 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    S('g_rev', 'Net sales (region build)', 'total', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("am")}),{"+".join("N(" + V(k) + ")" for k, _, _ in RGS)},{V("is_rev")})',
      fc=lambda: f'={"+".join(V(k) for k, _, _ in RGS)}',
      note='Σ Americas + EMEA + APAC. FY2019–20 and 2021 quarters (former Europe / North America / APAC / RoW regions only) = reported net sales.')
    S('g_rev_g', '  Net sales y/y % (reported, CHF)', 'growth', 'pct', all=growth('g_rev'))
    S('g_chk_rev', '  Check: region build vs consolidated net sales (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),IF(ABS({V("g_rev")}-{V("is_rev")})<=0.25,0,ROUND({V("g_rev")}-{V("is_rev")},1)),"")')
    S('g_ccs', '  Constant-currency net sales (Σ regions)', 'memo_calc', 'm1',
      all=lambda: (f'=IF(ISNUMBER({V("am_ccs")}),{"+".join(V(k + "_ccs") for k, _, _ in RGS)},"")' if CTX.col.prior else None),
      e26=lambda: f'=SUM({Q1}{R["g_ccs"]}:{Q4}{R["g_ccs"]})')
    S('g_ccg', '  Net sales y/y % constant currency (model: Σ regions)', 'growth', 'pct',
      all=lambda: (f'=IF(ISNUMBER({V("g_ccs")}),IFERROR({V("g_ccs")}/({"+".join(P(k) for k, _, _ in RGS)})-1,""),"")' if CTX.col.prior else None),
      ae=lambda: f'=IFERROR(({"+".join(P(k) + "*(1+" + V(k + "_ccg") + ")" for k, _, _ in RGS)})/({sprior()})-1,"")')
    S('g_ccg_pub', '  Memo: constant-currency growth as published', 'memo', 'pct', data='ccg_total',
      note='Published from Q1-24. Annual published figures are computed by the company on full-year rates (may differ slightly from Σ quarters).')
    S('g_fx', '  FX translation effect on net sales growth (pts)', 'growth', 'pct',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_rev_g")}),ISNUMBER({V("g_ccg")})),{V("g_rev_g")}-{V("g_ccg")},"")')
    S('cal_ccg', '  Memo: FY26 constant-currency growth guidance (scenario end-point)', 'memo', 'pct', e26=lambda: '=' + CH(SC['out_ccg']), note=V0['ccg_guid_note'])
    S('cal_q3g', '  Memo: Q3-26 constant-currency growth guidance (scenario)', 'memo', 'pct', qe=lambda: ('=' + CH(SC['out_q3'])) if CTX.col.q == 3 else None,
      note='Investor Day release (22-Sep-2026): "around 17%" constant-currency growth in Q3-26 (wholesale sell-in discipline; DTC momentum).')
    S('cal_cc', '  Outlook calibration: Δ constant-currency growth applied to all regions (Q3: Q3 guide; Q4: FY26 guide)', 'driver', 'pct',
      qe=lambda: (f'=((1+{V("cal_q3g")})*({sprior()})-({"+".join(P(k) + "*(1+" + V(k + "_pre") + ")" for k, _, _ in RGS)}))/({sprior()})' if CTX.col.q == 3 else
                  f'=((1+{V("cal_ccg", E26)})*{Y("g_rev", 2025)}-{Q1}{R["g_ccs"]}-{Q2}{R["g_ccs"]}-{Q3}{R["g_ccs"]}'
                  f'-({"+".join(P(k) + "*(1+" + V(k + "_pre") + ")" for k, _, _ in RGS)}))/({sprior()})'),
      note='Q3-26E: solves the uniform shift (vs 1H/26 regional cc growth) so Q3 cc growth = the Q3 guide; Q4-26E: so FY26 cc growth = the FY26 guidance end-point.')
    S('cal_ccg_chk', '  Check: FY26 constant-currency growth vs guidance end-point (should be 0)', 'check', 'pct', e26=lambda: f'=ROUND({V("g_ccg")}-{V("cal_ccg")},4)')
    S('cal_q3_chk', '  Check: Q3-26 constant-currency growth vs Q3 guide (should be 0)', 'check', 'pct', qe=lambda: f'=ROUND({V("g_ccg")}-{V("cal_q3g")},4)' if CTX.col.q == 3 else None)
    S('cal_rev', '  Memo: FY26 net sales guidance at current spot rates (CHF m, scenario end-point)', 'memo', 'm1', e26=lambda: '=' + CH(SC['out_rev']), note=V0['rev_guid_note'])
    S('cal_fx', '  Outlook calibration: FX translation effect (pts, all regions, Q3/Q4-26E)', 'driver', 'pct',
      qe=lambda: (f'=({V("cal_rev", E26)}-{Q1}{R["g_rev"]}-{Q2}{R["g_rev"]}-{Q3}{R["g_ccs"]}-{Q4}{R["g_ccs"]})/(({sprior()})+'
                  f'({"+".join(QC[(2025, 4)].c + str(R[k]) for k, _, _ in RGS)}))') if CTX.col.q == 3 else f'={Q3v("cal_fx")}',
      note='Solves the uniform 2H FX translation effect so FY26 CHF net sales = the guidance end-point (the guidance converts low-20% cc growth at spot rates).')
    S('cal_rev_chk', '  Check: FY26 net sales vs guidance end-point (should be 0)', 'check', 'm1', e26=lambda: f'=ROUND({V("g_rev")}-{V("cal_rev")},1)')
    S('tar', '  Tariff refund recognised in gross profit (US IEEPA duties; excluded from guidance)', 'line', 'm1',
      qe=lambda: ('=' + CH(SC['out_tar'])) if CTX.col.q == 3 else '=0', e26=lambda: S26('tar'), ae_in=0.0, flow=True,
      note='Investor Day release: up to USD 65m (up to CHF 53m) expected in Q3-26, benefiting reported gross profit; FY26 guidance excludes it. Not an adjusting item in the company definitions, so it lifts reported Adjusted EBITDA too.')
    blank()

    # ------------------------------------------------------------------ channel & product mix
    S('ch_hdr', 'Sales channel — wholesale vs direct-to-consumer (DTC: e-commerce + own retail stores)', 'block',
      note='CHANNEL MIX — DTC share driver (Q3/Q4-26E: prior-year quarter + 1H/26 y/y share gain; 2027E+: input path)')
    S('ch_whs', '  Wholesale net sales', 'line', 'm1', data='ch_whs', flow=True, fc=lambda: f'={V("is_rev")}-{V("ch_dtc")}')
    S('ch_dtc', '  Direct-to-consumer net sales', 'line', 'm1', data='ch_dtc', flow=True, fc=lambda: f'={V("is_rev")}*{V("ch_dtc_pct")}')
    S('ch_dtc_pct', '  DTC % of net sales', 'pct', 'pct', all=ratio('ch_dtc', 'is_rev'),
      qe=lambda: f'={P("ch_dtc_pct")}+({H1("ch_dtc")}/{H1("is_rev")}-{H1("ch_dtc", 2025)}/{H1("is_rev", 2025)})', ae_in=V0['dtc_ae'],
      note='Q2-26 DTC 45.7% (record Q2); FY25 41.8%. Q2-26 release: DTC expected to strongly outperform wholesale in 2H/26 (wholesale sell-in deliberately managed).')
    S('ch_whs_g', '  Wholesale y/y % (reported)', 'growth', 'pct', all=growth('ch_whs'))
    S('ch_dtc_g', '  DTC y/y % (reported)', 'growth', 'pct', all=growth('ch_dtc'))
    S('ch_whs_cc', '  Wholesale y/y % constant currency (published)', 'memo', 'pct', data='ccg_whs')
    S('ch_dtc_cc', '  DTC y/y % constant currency (published)', 'memo', 'pct', data='ccg_dtc')
    blank()
    S('pr_hdr', 'Product — shoes · apparel · accessories', 'block', note='PRODUCT MIX — apparel / accessories share drivers; shoes = residual')
    S('pr_shoes', '  Shoes net sales', 'line', 'm1', data='pr_shoes', flow=True, fc=lambda: f'={V("is_rev")}-{V("pr_apparel")}-{V("pr_acc")}')
    S('pr_apparel', '  Apparel net sales', 'line', 'm1', data='pr_apparel', flow=True, fc=lambda: f'={V("is_rev")}*{V("pr_app_pct")}')
    S('pr_acc', '  Accessories net sales', 'line', 'm1', data='pr_acc', flow=True, fc=lambda: f'={V("is_rev")}*{V("pr_acc_pct")}')
    S('pr_shoes_pct', '  Shoes % of net sales', 'pct', 'pct', all=ratio('pr_shoes', 'is_rev'))
    S('pr_app_pct', '  Apparel % of net sales', 'pct', 'pct', all=ratio('pr_apparel', 'is_rev'),
      qe=lambda: f'={P("pr_app_pct")}+({H1("pr_apparel")}/{H1("is_rev")}-{H1("pr_apparel", 2025)}/{H1("is_rev", 2025)})', ae_in=V0['app_ae'],
      note='Apparel 6.5% of 1H/26 net sales (+56.9% cc); Investor Day 2026: Apparel one of three immediate growth pillars (Run, Sneaker, Apparel).')
    S('pr_acc_pct', '  Accessories % of net sales', 'pct', 'pct', all=ratio('pr_acc', 'is_rev'),
      qe=lambda: f'={P("pr_acc_pct")}+({H1("pr_acc")}/{H1("is_rev")}-{H1("pr_acc", 2025)}/{H1("is_rev", 2025)})', ae_in=V0['acc_ae'])
    S('pr_shoes_g', '  Shoes y/y % (reported)', 'growth', 'pct', all=growth('pr_shoes'))
    S('pr_app_g', '  Apparel y/y % (reported)', 'growth', 'pct', all=growth('pr_apparel'))
    S('pr_shoes_cc', '  Shoes y/y % constant currency (published)', 'memo', 'pct', data='ccg_shoes')
    S('pr_app_cc', '  Apparel y/y % constant currency (published)', 'memo', 'pct', data='ccg_apparel')
    blank()
    S('ro_hdr', 'Memo: former regional disclosure (to 2022) — Europe · North America · Asia-Pacific · Rest of World', 'block',
      note='FORMER REGIONS — as originally reported (IPO prospectus, 2021–22 MD&A, Forms 20-F FY2021–22); replaced by EMEA / Americas / APAC from Q1-23')
    S('ro_eu', '  Europe', 'memo', 'm1', data='ro_eu', note='Rest of World = net sales − Europe − North America − Asia-Pacific.')
    S('ro_na', '  North America', 'memo', 'm1', data='ro_na')
    S('ro_apac', '  Asia-Pacific (former definition)', 'memo', 'm1', data='ro_apac_o')
    S('ro_row', '  Rest of World', 'memo', 'm1', data='ro_row')
    S('ro_na_g', '  North America y/y %', 'growth', 'pct', all=growth('ro_na'))
    blank()

    # ------------------------------------------------------------------ margin build
    S('m_hdr', 'Profitability build — gross margin & Adjusted EBITDA margin → FY26 outlook calibration (excl. tariff refund)', 'block',
      note='MARGIN BUILD — Q3/Q4-26E: prior-year quarter margin + uniform Δ solved to the FY26 guidance end-point; 2027E+: scenario levers (Investor Day 2029: GM ≥65%, Adj. EBITDA margin ≥22%)')
    S('m_gm', '  Gross margin % (excl. tariff refund)', 'pct', 'pct', hist=lambda: f'=IF(ISNUMBER({V("is_cogs")}),IFERROR({V("is_gp")}/{V("is_rev")},""),"")',
      qe=lambda: f'={P("m_gm")}+{Q3v("cal_gm")}', e26=lambda: f'=IFERROR(({V("is_gp")}-{V("tar")})/{V("is_rev")},"")',
      ae=lambda: '=' + CH(SC['GM'][CTX.col.year]),
      note='Historical = reported gross margin. FY26 guidance "at least 65.0%" excludes the tariff refund. 2027E–2030E: scenario lever (company: ≥65.0% through 2029).')
    S('cal_gmg', '  Memo: FY26 gross margin guidance (scenario end-point)', 'memo', 'pct', e26=lambda: '=' + CH(SC['out_gm']))
    S('cal_gm', '  Outlook calibration: Δ gross margin vs prior-year quarter (Q3/Q4-26E)', 'driver', 'pct',
      qe=lambda: (f'=({V("cal_gmg", E26)}*{V("is_rev", E26)}-{Q1}{R["is_gp"]}-{Q2}{R["is_gp"]}-{Q3}{R["is_rev"]}*{QC[(2025, 3)].c}{R["m_gm"]}'
                  f'-{Q4}{R["is_rev"]}*{QC[(2025, 4)].c}{R["m_gm"]})/({Q3}{R["is_rev"]}+{Q4}{R["is_rev"]})') if CTX.col.q == 3 else f'={Q3v("cal_gm")}')
    S('cal_gm_chk', '  Check: FY26 gross margin (excl. refund) vs guidance end-point (should be 0)', 'check', 'pct', e26=lambda: f'=ROUND({V("m_gm")}-{V("cal_gmg")},4)')
    S('m_ebm', '  Adjusted EBITDA margin % (excl. tariff refund)', 'pct', 'pct', hist=lambda: f'=IF(ISNUMBER({V("r_adj_pub")}),IFERROR({V("r_adj_pub")}/{V("is_rev")},""),"")',
      qe=lambda: f'={P("m_ebm")}+{Q3v("cal_eb")}', e26=lambda: f'=IFERROR(({V("g_adj")}-{V("tar")})/{V("is_rev")},"")',
      ae=lambda: '=' + CH(SC['EBM'][CTX.col.year]),
      note='Historical = published Adjusted EBITDA ÷ net sales. FY26 guidance 19.5–20.0% (excl. tariff refund). 2027E–2030E: scenario lever (company: ≥22% by 2029).')
    S('cal_ebg', '  Memo: FY26 Adjusted EBITDA margin guidance (scenario end-point)', 'memo', 'pct', e26=lambda: '=' + CH(SC['out_ebm']))
    S('cal_eb', '  Outlook calibration: Δ Adjusted EBITDA margin vs prior-year quarter (Q3/Q4-26E)', 'driver', 'pct',
      qe=lambda: (f'=({V("cal_ebg", E26)}*{V("is_rev", E26)}-{Q1}{R["g_adj"]}-{Q2}{R["g_adj"]}-{Q3}{R["is_rev"]}*{QC[(2025, 3)].c}{R["m_ebm"]}'
                  f'-{Q4}{R["is_rev"]}*{QC[(2025, 4)].c}{R["m_ebm"]})/({Q3}{R["is_rev"]}+{Q4}{R["is_rev"]})') if CTX.col.q == 3 else f'={Q3v("cal_eb")}')
    S('cal_eb_chk', '  Check: FY26 Adjusted EBITDA margin (excl. refund) vs guidance end-point (should be 0)', 'check', 'pct', e26=lambda: f'=ROUND({V("m_ebm")}-{V("cal_ebg")},4)')
    S('g_adj', 'Adjusted EBITDA (margin build, incl. tariff refund)', 'total', 'm1',
      hist=lambda: f'={V("r_adj_pub")}', qe=lambda: f'={V("is_rev")}*{V("m_ebm")}+N({V("tar")})', e26=lambda: S26('g_adj'),
      ae=lambda: f'={V("is_rev")}*{V("m_ebm")}',
      note="On's primary profit KPI and guidance metric (company definition: excludes share-based compensation; post-IFRS 16, so store rents sit below EBITDA in D&A / interest). Drives the IFRS P&L below.")
    S('g_adj_g', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('g_adj'))
    S('g_chk_adj', '  Check: build vs Adjusted EBITDA bridge (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_adj")}),ISNUMBER({V("r_adj")})),IF(ABS({V("g_adj")}-{V("r_adj")})<=0.15,0,ROUND({V("g_adj")}-{V("r_adj")},1)),"")')
    S('m_opex', '  SG&A excl. share-based compensation and D&A, % of net sales (cash operating costs)', 'pct', 'pct',
      all=lambda: f'=IF(ISNUMBER({V("is_sga")}),IFERROR(({V("is_sga")}-{V("d_sbc")}-{V("d_dna")}-N({V("d_etc")}))/{V("is_rev")},""),"")',
      note='Output: gross margin − Adjusted EBITDA margin (equity transaction costs 2021–22 also excluded). Investor Day: "meaningful SG&A leverage" to 2029.')
    S('tg_h', '  Investor Day 2026 targets (22-Sep-2026) vs model — information, not forced:', 'sub', 'gen')
    S('tg_rev', '    2029 net sales target: ≥ CHF 5.6bn at current FX (model − target, CHF m)', 'memo_calc', 'm1',
      ae=lambda: f'={V("is_rev")}-{V0["tg_rev"]}' if CTX.col.year == 2029 else None)
    S('tg_cc', '    2026–29 constant-currency net sales CAGR (target: high-teens)', 'memo_calc', 'pct',
      ae=lambda: f'=IFERROR((({Y("g_ccg", 2027)}+1)*({Y("g_ccg", 2028)}+1)*({Y("g_ccg", 2029)}+1))^(1/3)-1,"")' if CTX.col.year == 2029 else None)
    S('tg_eb', '    2026–29 Adjusted EBITDA CAGR (target: > 20%; on FY26 excl. tariff refund)', 'memo_calc', 'pct',
      ae=lambda: f'=IFERROR(({Y("g_adj", 2029)}/({Y("g_adj", 2026)}-{Y("tar", 2026)}))^(1/3)-1,"")' if CTX.col.year == 2029 else None)
    blank()

    # ------------------------------------------------------------------ cost drivers
    S('d_hdr', 'Cost drivers & D&A', 'block', note='COST DRIVERS — Q3/Q4-26E: FY26 point estimates less 1H/26; 2027E+: % of net sales')
    S('d_dna', '  Depreciation & amortization (incl. right-of-use assets)', 'line', 'm1', data='dna', flow=True,
      qe=lambda: f'=({PT("pt_dna")}-{H1("d_dna")})/2', e26=lambda: S26('d_dna'), ae=lambda: f'={V("is_rev")}*{V("d_dna_pct")}',
      note='IFRS 16: includes depreciation of store / office / warehouse right-of-use assets (rent is not in Adjusted EBITDA).')
    S('d_dna_pct', '  D&A % of net sales', 'pct', 'pct', all=ratio('d_dna', 'is_rev'), ae_in=V0['dna_pct'])
    S('d_sbc', '  Share-based compensation (incl. social charges; Adjusted EBITDA reconciliation)', 'line', 'm1', data='sbc', flow=True,
      qe=lambda: f'=({PT("pt_sbc")}-{H1("d_sbc")})/2', e26=lambda: S26('d_sbc'), ae=lambda: f'={V("is_rev")}*{V("d_sbc_pct")}',
      note='2021 includes the IPO founder / employee awards (CHF 176m in Q4-21). Forecast: FY26 point estimate, then % of net sales.')
    S('d_sbc_pct', '  Share-based compensation % of net sales', 'pct', 'pct', all=ratio('d_sbc', 'is_rev'), ae_in=V0['sbc_pct'])
    S('d_etc', '  Equity transaction costs (IPO 2021; added back to Adjusted EBITDA)', 'line', 'm1', data='etc', flow=True, fc=lambda: '=0')
    blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED STATEMENT OF INCOME (IFRS)', 'section',
      note='CONSOLIDATED IS — forecast logic (gross profit = net sales × gross margin + tariff refund; operating result = Adjusted EBITDA − D&A − SBC; SG&A implied)')
    S('is_rev', 'Net sales', 'total', 'm1', data='rev', flow=True, fc=lambda: f'={V("g_rev")}', note='Forecast linked to the region build.')
    S('is_cogs', 'Cost of sales', 'line', 'm1', data='cogs', flow=True, fc=lambda: f'={V("is_rev")}-{V("is_gp")}')
    S('is_gp', 'Gross profit', 'line_b', 'm1', hist=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_rev")}-{V("is_cogs")},"")',
      fc=lambda: f'={V("is_rev")}*{V("m_gm")}+N({V("tar")})', e26=lambda: S26('is_gp'))
    S('is_gm', '  Gross margin % (reported)', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('is_sga', 'Selling, general & administrative expenses', 'line', 'm1', data='sga', flow=True, fc=lambda: f'={V("is_gp")}-{V("is_op")}',
      note='Includes D&A, share-based compensation and (2021) IPO costs. Forecast implied: gross profit − operating result.')
    S('is_op', 'Operating result', 'total', 'm1', data='op', flow=True,
      fc=lambda: f'={V("g_adj")}-{V("d_dna")}-{V("d_sbc")}-{V("d_etc")}', e26=lambda: S26('is_op'),
      note='Historical as reported (Q4-21 corrected: release typo, see check / manual_items.json). Forecast = Adjusted EBITDA − D&A − SBC.')
    S('is_opm', '  Operating margin (IFRS) %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('is_finc', 'Financial income', 'line', 'm1', data='fin_inc', flow=True,
      qe=lambda: f'=({PT("pt_finc")}-{H1("is_finc")})/2', e26=lambda: S26('is_finc'), ae=lambda: f'={P("cf_end")}*{V("ls_yield")}',
      note='Interest on cash and deposits. 2027E+: opening cash × yield (no circularity).')
    S('is_fexp', 'Financial expenses', 'line', 'm1', data='fin_exp', flow=True,
      qe=lambda: f'=({PT("pt_fexp")}-{H1("is_fexp")})/2', e26=lambda: S26('is_fexp'), ae=lambda: f'={P("ls_ll")}*{V("ls_rate")}',
      note='Mostly IFRS 16 lease interest (no bank debt; CHF 700m revolving facility undrawn). 2027E+: opening lease & other financial liabilities × rate.')
    S('is_fx', 'Foreign exchange result (gain = +)', 'line', 'm1', data='fx', flow=True, qe_in={3: 0.0, 4: 0.0}, e26=lambda: S26('is_fx'), ae_in=0.0,
      note='Revaluation of intercompany / USD balances (Q2-25 loss CHF 139.9m on USD weakness). Not forecast; excluded from Adjusted EBITDA.')
    S('is_ebt', 'Income before taxes', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_op")}),{V("is_op")}+{V("is_finc")}-{V("is_fexp")}+{V("is_fx")},"")')
    S('is_tax', 'Income tax expense (benefit)', 'line', 'm1', data='tax', flow=True, fc=lambda: f'={V("is_ebt")}*{V("is_etr")}', e26=lambda: S26('is_tax'))
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), qe=lambda: f'={PT("pt_etr")}', ae_in=V0['etr'],
      note='Swiss holding with a global footprint; 1H/26 13.9% (Q2-26 16.5%). Q3/Q4-26E point estimate; 2027E+ input.')
    S('is_ni', 'Net income (loss)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_ni_chk', '  Check: net income vs reported (should be 0; ±0.15 rounding)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),IF(ABS({V("is_ni")}-{V("is_ni_pub")})<=0.15,0,ROUND({V("is_ni")}-{V("is_ni_pub")},2)),"")')
    S('is_ni_pub', '  Memo: net income (loss) as reported', 'memo', 'm1', data='ni', flow=True)
    S('is_dda', '  Memo: depreciation & amortization (total)', 'memo_calc', 'm1', all=lambda: f'=IF(ISNUMBER({V("d_dna")}),{V("d_dna")},"")')
    S('is_sbc', '  Memo: share-based compensation', 'memo_calc', 'm1', all=lambda: f'={V("d_sbc")}')
    S('eps_hdr', '(Earnings per share — Class A-equivalent shares = Class A + Class B ÷ 10; Class B voting shares carry 1/10 of the Class A economic rights)', 'sub', 'gen')
    S('sh_basic', '  Weighted-average basic shares, Class A-equivalent (m)', 'line', 'm1', data='sh_basic', avg=True,
      qe=lambda: f'=${Q2}${R["sh_basic"]}+${E26}${R["bb_iss"]}*{0.25 if CTX.col.q == 3 else 0.75}-{"0" if CTX.col.q == 3 else "$" + E26 + "$" + str(R["bb_sh"]) + "*0.5"}',
      ae=lambda: f'=AVERAGE({V("bb_beg")},{V("bb_end")})',
      note='Published Class A + Class B weighted shares (adjusted-EPS tables); Class B ÷ 10. FY2019–20 Class A only (×1,250 for the 2021 share-capital reorganisation). Q4-26E: half of the quarter\'s buybacks weighted.')
    S('sh_dil', '  Weighted-average diluted shares, Class A-equivalent (m)', 'line', 'm1', data='sh_dil', avg=True,
      qe=lambda: f'={V("sh_basic")}+(${Q2}${R["sh_dil"]}-${Q2}${R["sh_basic"]})', ae=lambda: f'={V("sh_basic")}+{V("ds_dil")}')
    S('eps_basic', 'EPS – basic, Class A (CHF)', 'eps', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_basic")}),IFERROR({V("is_ni")}/{V("sh_basic")},""),"")')
    S('eps_dil', 'EPS – diluted, Class A (CHF)', 'eps_total', 'ps', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),IFERROR({V("is_ni")}/{V("sh_dil")},""),"")',
      note='Net income ÷ Class A-equivalent diluted shares (Class B EPS = 1/10). Anti-dilution: the company reports diluted = basic in loss periods.')
    S('eps_dil_g', '  EPS – diluted y/y %', 'growth', 'pct', all=growth('eps_dil'))
    S('eps_pub', '  Memo: EPS – basic, Class A as reported (CHF)', 'eps_memo', 'ps', data='eps_a')
    S('eps_chk', '  Check: model basic EPS vs reported (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(AND(ISNUMBER({V("eps_pub")}),ISNUMBER({V("eps_basic")})),IF(ABS({V("eps_basic")}-{V("eps_pub")})<=0.0101,0,ROUND({V("eps_basic")}-{V("eps_pub")},2)),"n/p")')
    S('eps_pub_d', '  Memo: EPS – diluted, Class A as reported (CHF)', 'eps_memo', 'ps', data='eps_dil_a')
    S('dps', '  Dividends per Class A share (CHF)', 'line', 'ps', qe_in={3: 0.0, 4: 0.0}, ae_in=0.0,
      note='On has not paid dividends; capital returns via the USD 1bn Class A share repurchase authorization (Sep-2026 to Dec-2029).')
    blank()

    # ------------------------------------------------------------------ RECON 1: EBITDA
    S('sec_r1', 'RECONCILIATION: NET INCOME → EBITDA → ADJUSTED EBITDA (company definition, as published)', 'section',
      note='ADJUSTED EBITDA — per On release reconciliation: net income + income taxes − financial income + financial expenses − FX result + D&A + SBC (+ equity transaction costs 2021–22)')
    S('r_ni', 'Net income (loss) (IFRS)', 'line_b', 'm1', all=lambda: f'={V("is_ni")}')
    S('r_tax', '  (+) Income taxes', 'line', 'm1', all=lambda: f'={V("is_tax")}')
    S('r_finc', '  (−) Financial income', 'line', 'm1', all=lambda: f'=-{V("is_finc")}')
    S('r_fexp', '  (+) Financial expenses', 'line', 'm1', all=lambda: f'={V("is_fexp")}')
    S('r_fx', '  (−) Foreign exchange result (loss = +)', 'line', 'm1', all=lambda: f'=-{V("is_fx")}')
    S('r_op', '  = Operating result', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ni")}),{V("r_ni")}+{V("r_tax")}+{V("r_finc")}+{V("r_fexp")}+{V("r_fx")},"")')
    S('r_dna', '  (+) Depreciation & amortization', 'line', 'm1', all=lambda: f'={V("d_dna")}')
    S('r_ebitda', '  = EBITDA', 'total', 'm1', all=lambda: f'=IF(AND(ISNUMBER({V("r_op")}),ISNUMBER({V("r_dna")})),{V("r_op")}+{V("r_dna")},"")')
    S('r_sbc', '  (+) Share-based compensation', 'line', 'm1', all=lambda: f'={V("d_sbc")}')
    S('r_etc', '  (+) Equity transaction costs (IPO, 2021–22)', 'line', 'm1', all=lambda: f'=N({V("d_etc")})')
    S('r_tot', '  Total adjusting items', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{nsum(["r_sbc", "r_etc"])},"")')
    S('r_adj', '  = Adjusted EBITDA (model bridge)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),{V("r_ebitda")}+{V("r_tot")},"")',
      note='Rebuilt from the published reconciliation lines; forecast = EBITDA + SBC (equals the margin build — check in the Group block).')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_adj_pub', '  Company-published Adjusted EBITDA', 'memo', 'm1', data='adj_pub', flow=True)
    S('r_adj_chk', '  Check: model bridge vs company-published (should be 0; ±0.15 rounding)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_adj_pub")}),IF(ABS({V("r_adj")}-{V("r_adj_pub")})<=0.15,0,ROUND({V("r_adj")}-{V("r_adj_pub")},2)),"n/p")')
    S('r_def', '  Definition basis (company Adjusted EBITDA definition in force)', 'text', 'gen',
      note='Definition changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('r_xt', '  Memo: Adjusted EBITDA excl. tariff refund (guidance basis)', 'memo_calc', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}-N({V("tar")}),"")')
    S('r_xt_m', '  Memo: Adjusted EBITDA margin excl. tariff refund %', 'pct', 'pct', all=ratio('r_xt', 'is_rev'))
    S('r_lease', '  Memo: Adjusted EBITDA after lease payments (pre-IFRS 16 proxy: − lease principal & interest paid)', 'memo_calc', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_adj")}),ISNUMBER({V("cf_lease")})),{V("r_adj")}+{V("cf_lease")}+{V("cf_intp")},"")')
    S('r_ebit_h', 'To adjusted EBIT:', 'sub', 'gen')
    S('r_dnan', '  (−) Depreciation & amortization', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("r_dna")}),-{V("r_dna")},"")')
    S('r_ebit', '  = Adjusted EBIT (Adjusted EBITDA − D&A = operating result + SBC + equity transaction costs)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")}+{V("r_dnan")},"")',
      note='Used for NOPAT / ROIC; the DCF deducts SBC again (a real cost).')
    S('r_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('r_ebit', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 2
    S('sec_r2', 'RECONCILIATION: IFRS OPERATING RESULT → ADJUSTED OPERATING RESULT (model definition)', 'section',
      note='ADJUSTED OPERATING RESULT — model bridge on the company items: IFRS operating result + SBC + equity transaction costs (On does not publish an adjusted operating result)')
    S('o_op', 'Operating result (IFRS)', 'line_b', 'm1', all=lambda: f'={V("is_op")}')
    S('o_sbc', '  (+) Share-based compensation', 'line', 'm1', all=lambda: f'={V("d_sbc")}')
    S('o_etc', '  (+) Equity transaction costs', 'line', 'm1', all=lambda: f'=N({V("d_etc")})')
    S('o_adj', '  = Adjusted operating result (model)', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_sbc")}+{V("o_etc")},"")')
    S('o_adj_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('o_chk', '  Check: adjusted operating result + D&A vs company-published Adjusted EBITDA (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("r_adj_pub")}),ISNUMBER({V("o_adj")})),IF(ABS({V("o_adj")}+{V("d_dna")}-{V("r_adj_pub")})<=0.15,0,ROUND({V("o_adj")}+{V("d_dna")}-{V("r_adj_pub")},2)),"n/p")')
    S('o_adj_g', '  Adjusted operating result y/y %', 'growth', 'pct', all=growth('o_adj'))
    S('o_inc', '  Incremental adjusted operating margin (Δ adjusted operating result / Δ net sales)', 'pct', 'pct', all=incr('o_adj', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RECON 3
    S('sec_r3', 'RECONCILIATION: IFRS NET INCOME → ADJUSTED NET INCOME → ADJUSTED EPS (company definition, Class A)', 'section',
      note='ADJUSTED EPS — company: net income + SBC (+ equity transaction costs) + tax effect on the tax-deductible portion; Class A + Class B combined, ÷ Class A-equivalent shares')
    S('e_ni', 'Net income (IFRS)', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("e_sh")}),{V("is_ni")},"")')
    S('e_sbc', '  (+) Share-based compensation (adjusted net income table)', 'line', 'm1', data='ani_sbc', flow=True,
      fc=lambda: f'={V("d_sbc")}', note='As published (Class A + Class B); may differ by ±0.1 from the Adjusted EBITDA table through class rounding.')
    S('e_etc', '  (+) Equity transaction costs', 'line', 'm1', data='ani_etc', flow=True, fc=lambda: '=0')
    S('e_tax', '  (+/−) Tax effect of adjustments (tax-deductible portion only)', 'line', 'm1', data='ani_tax', flow=True,
      fc=lambda: f'=-{V("e_sbc")}*{V("e_rate")}')
    S('e_adjni', '  = Adjusted net income (model bridge)', 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("e_sh")}),{V("e_ni")}+N({V("e_sbc")})+N({V("e_etc")})+N({V("e_tax")}),"")',
      note='Annual columns use the components of the full-year table (the company computes the tax effect on a full-year basis, so quarters do not sum exactly to the year).')
    S('e_adjni_pub', '  Company-published adjusted net income (Class A + Class B)', 'memo', 'm1', data='adj_ni_pub')
    S('e_adjni_chk', '  Check: model vs published adjusted net income (should be 0; ±0.35 class rounding)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("e_adjni_pub")}),IF(ABS({V("e_adjni")}-{V("e_adjni_pub")})<=0.35,0,ROUND({V("e_adjni")}-{V("e_adjni_pub")},2)),"n/p")')
    S('e_sh', '  Weighted-average diluted shares, Class A-equivalent (m)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("sh_dil")}),{V("sh_dil")},"")')
    S('e_eps', 'Adjusted EPS – diluted, Class A (CHF) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published adjusted diluted EPS, Class A (CHF)', 'eps_memo', 'ps', data='adj_eps_pub')
    S('e_chk', '  Check: model vs company-published (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(ISNUMBER({V("e_pub")}),IF(ABS({V("e_eps")}-{V("e_pub")})<=0.0101,0,ROUND({V("e_eps")}-{V("e_pub")},2)),"n/p")')
    S('e_epsb', '  Adjusted EPS – basic, Class A (CHF) (model)', 'eps_memo', 'ps', all=ratio('e_adjni', 'sh_basic'))
    S('e_pubb', '  Company-published adjusted basic EPS, Class A (CHF)', 'eps_memo', 'ps', data='adj_eps_basic_pub')
    S('e_chkb', '  Check: model vs published basic (should be 0.00; ±0.01 rounding)', 'check', 'ps',
      hist=lambda: f'=IF(ISNUMBER({V("e_pubb")}),IF(ABS({V("e_epsb")}-{V("e_pubb")})<=0.0101,0,ROUND({V("e_epsb")}-{V("e_pubb")},2)),"n/p")')
    S('e_rate', '  Tax effect as % of share-based compensation (− = tax charge)', 'pct', 'pct',
      hist=lambda: f'=IF(AND(ISNUMBER({V("e_tax")}),ISNUMBER({V("e_sbc")})),IFERROR(-{V("e_tax")}/{V("e_sbc")},""),"")',
      qe_in={3: V0['e_rate'], 4: V0['e_rate']}, ae_in=V0['e_rate'],
      note='Only a small part of SBC is tax-deductible (local rate on the deductible portion); FY25 ≈ 1–2% of SBC.')
    S('e_def', '  Definition basis (company adjusted EPS definition in force when published)', 'text', 'gen')
    S('e_eps_g', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    blank()

    # ------------------------------------------------------------------ growth & margins
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Net sales y/y % (reported, CHF)', 'growth', 'pct', all=growth('is_rev'))
    S('gm_cc', '  Net sales y/y % constant currency', 'growth', 'pct', all=lambda: f'=IF(ISNUMBER({V("g_ccg")}),{V("g_ccg")},"")' if CTX.col.prior else None)
    S('gm_dtc', '  DTC net sales y/y %', 'growth', 'pct', all=growth('ch_dtc'))
    S('gm_ebitda', '  Adjusted EBITDA y/y %', 'growth', 'pct', all=growth('r_adj'))
    S('gm_op', '  Operating result (IFRS) y/y %', 'growth', 'pct', all=growth('is_op'))
    S('gm_ni', '  Net income y/y %', 'growth', 'pct', all=growth('is_ni'))
    S('gm_eps', '  Adjusted EPS y/y %', 'growth', 'pct', all=growth('e_eps'))
    S('gm_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('gm_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('gm_inc', '  Incremental Adjusted EBITDA margin (ΔEBITDA / ΔNet sales)', 'pct', 'pct', all=incr('r_adj', 'is_rev'))
    S('gm_adjop_m', '  Adjusted operating margin %', 'pct', 'pct', all=ratio('o_adj', 'is_rev'))
    S('gm_op_m', '  Operating margin (IFRS) %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_sga', '  SG&A % of net sales', 'pct', 'pct', all=ratio('is_sga', 'is_rev'))
    blank()
