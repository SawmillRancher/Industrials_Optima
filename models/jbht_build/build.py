"""Build JBHT_Model.xlsx from the MLM template (same layout, formatting and process as the prior models)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC, SEG
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'JBHT_Model.xlsx')
OUTLOOK = MAN['outlook_2026']

# ====================================================================== inputs (V0)
def wc_inputs():
    q = DATA['2025']['x']; rev = q['rev']
    return {'dso': round(q['bs_ar'] / rev * 365, 1), 'dpo': round(q['bs_ap'] / rev * 365, 1), 'cl': round(q['bs_claims'] / rev, 4), 'ocl': round(q['bs_oacc'] / rev, 4)}
WC = wc_inputs()
WC['note'] = (f'Forecast inputs at year-end (31-Dec-2025) levels on FY2025 revenue (DSO {WC["dso"]}d, payables {WC["dpo"]}d, claims accruals {WC["cl"]:.1%}, '
              f'accrued expenses {WC["ocl"]:.1%} of revenue); year ends are compared with year ends.')
AM = MAN['amort_sched']
UNV = 'UNVERIFIED (not in an SEC filing)'

V0 = {
    'out_hdr': 'FY26 — no company revenue / EPS guidance (Q3-26 release, 15-Oct-2026)',
    'out_note': ('J.B. Hunt publishes no revenue or earnings guidance. Its only forward statements on EDGAR: 2026 annual tax rate ~24.0% (Q3-26 release) and net capital '
                 'expenditures ~$700m (Q3-26 10-Q) — both applied below. Q4/26E volumes, revenue per unit and margins follow historical Q3→Q4 seasonality by scenario.'),
    'outlook': [
        ('bb26', '  Q4/26E share repurchases ($m)', (250.0, 175.0, 100.0), 'm',
         'Assumption. Nine months 2026 $351.7m ($173.8m in Q3); $619.3m left on the $1bn authorization (Oct-2025) at 30-Sep-2026.'),
    ],
    'points': [
        ('pt_etr', '  FY26 annual effective tax rate (company outlook)', OUTLOOK['tax_rate'], 'pct',
         'Company: "We expect our 2026 full year annual tax rate to be approximately 24.0%" (Q3-26 release, SEC-filed). Q4/26E tax is solved to it.'),
        ('pt_capex', '  FY26 net capital expenditures ($m; company outlook)', OUTLOOK['net_capex'], 'm1',
         'Company: "We expect to spend approximately $700 million for net capital expenditures during the full calendar year 2026" (Q3-26 10-Q). Nine months $291.1m.'),
        ('pt_sale', '  Q4/26E proceeds from sale of equipment ($m)', 35.0, 'm1', 'Assumption: nine months 2026 $102.1m (~$34m a quarter).'),
        ('pt_int', '  Q4/26E net interest expense ($m)', 15.5, 'm1', 'Assumption: Q3/26 $15.7m; ~$1.12bn debt at ~4.9%.'),
    ],
    'lev': (1.0, 0.8, 0.6),
    'lev_note': ('Net debt $1.12bn at 30-Sep-26 ≈ 0.7x LTM adjusted EBITDA (FY2021–25: 0.5–0.9x). Target = leverage up to which surplus cash is returned via buybacks; '
                 f'below it free cash flow repays the revolver. A ~1x EBITDA leverage target is often attributed to management on earnings calls — {UNV}; treated here as a scenario assumption.'),
    'blocks': [
        ('JBI_VOL', 'JBI_VOL (Intermodal loads y/y)', 0.02, -0.04, [0.05, 0.04, 0.04, 0.03],
         'Q3/26 +8% (Eastern network +18%, transcontinental +1%); 9M/26 +7%; FY25 +2%, FY24 +2%. Road-to-rail conversion, ~124k containers with spare capacity.', 'pct', False),
        ('JBI_PX', 'JBI_PX (Intermodal revenue per load y/y, incl. fuel surcharge)', 0.015, -0.03, [0.01, 0.025, 0.025, 0.025],
         'Q3/26 +11% gross (+2% ex fuel surcharge): the 2026 increase is mostly fuel surcharge (18% of revenue vs 12–13% in 2025), a pass-through. Base assumes fuel flat, ~2–2.5% rate / mix.', 'pct', False),
        ('JBI_M', 'JBI_M (Intermodal operating margin)', 0.01, -0.015, [0.085, 0.090, 0.095, 0.100],
         f'9M/26 8.1%; FY25 7.5%, FY24 7.2%, FY22 11.4%, FY15 13.0%. A 10–12% long-term margin range is cited from investor presentations — {UNV}; Base reaches its low end by 2030E.', 'pct', False),
        ('DCS_VOL', 'DCS_VOL (Dedicated average trucks y/y)', 0.02, -0.03, [0.02, 0.03, 0.03, 0.03],
         'Q3/26 +1% (12,791 average trucks; +162 y/y at quarter end); FY25 −3%, FY24 −2%; customer retention ~96%.', 'pct', False),
        ('DCS_PX', 'DCS_PX (Dedicated revenue per truck y/y, incl. fuel surcharge)', 0.01, -0.02, [0.01, 0.025, 0.025, 0.025],
         'Q3/26 productivity +10% gross (+3% ex fuel surcharge: index-based price escalators, fewer idle tractors).', 'pct', False),
        ('DCS_M', 'DCS_M (Dedicated operating margin)', 0.01, -0.015, [0.100, 0.105, 0.110, 0.115],
         f'Q3/26 8.5% (group medical, insurance, onboarding costs); 9M/26 10.0%; FY21–25 10.2–11.8%. A 12–14% long-term range is cited from investor presentations — {UNV}.', 'pct', False),
        ('ICS_VOL', 'ICS_VOL (Brokerage loads y/y)', 0.04, -0.06, [0.06, 0.04, 0.03, 0.03],
         'Q3/26 +22% (first growth since 2021); FY25 −9%, FY24 −20%, FY23 −38%.', 'pct', False),
        ('ICS_PX', 'ICS_PX (Brokerage revenue per load y/y)', 0.03, -0.06, [0.00, 0.02, 0.02, 0.02],
         'Q3/26 +29% (contract and spot truckload rates, fuel). Base: rates hold at the Q4/26E level in 2027E, then +2%.', 'pct', False),
        ('ICS_M', 'ICS_M (Brokerage operating margin)', 0.01, -0.02, [0.020, 0.025, 0.030, 0.030],
         f'Q3/26 2.2% (first profit since Q4-22); FY24 −4.9%, FY21–22 1.8–2.5%, FY15 5.1%. A 4–6% long-term range is cited from investor presentations — {UNV}.', 'pct', False),
        ('FMS_VOL', 'FMS_VOL (Final Mile stops y/y)', 0.03, -0.04, [-0.02, 0.02, 0.03, 0.03],
         'Q3/26 −10% (known business losses while improving revenue quality); FY25 −11%, FY24 −6%.', 'pct', False),
        ('FMS_PX', 'FMS_PX (Final Mile revenue per stop y/y)', 0.01, -0.02, [0.03, 0.02, 0.02, 0.02], 'Q3/26 +8% (revenue quality, mix).', 'pct', False),
        ('FMS_M', 'FMS_M (Final Mile operating margin)', 0.01, -0.015, [0.020, 0.030, 0.035, 0.040], 'Q3/26 0.8%; 9M/26 2.5%; FY25 3.3%, FY24 6.6%, FY23 5.1%.', 'pct', False),
        ('JBT_VOL', 'JBT_VOL (Truckload loads y/y)', 0.03, -0.04, [0.03, 0.02, 0.02, 0.02], 'Q3/26 +4%; FY25 +11%, FY24 −5%.', 'pct', False),
        ('JBT_PX', 'JBT_PX (Truckload revenue per load y/y)', 0.03, -0.06, [0.00, 0.02, 0.02, 0.02],
         'Q3/26 +33% gross (+29% ex fuel surcharge). Base: rates hold at the Q4/26E level in 2027E, then +2%.', 'pct', False),
        ('JBT_M', 'JBT_M (Truckload operating margin)', 0.015, -0.02, [0.030, 0.035, 0.040, 0.040], 'Q3/26 2.7%; FY25 2.9%, FY24 3.1%, FY21–22 8.2–8.5%.', 'pct', False),
        ('MNA', 'M&A_spend (acquisitions, $m)', 100.0, 0.0, [0.0, 0.0, 0.0, 0.0],
         'Base: none (J.B. Hunt spent ~$85–120m in each of 2019, 2022 and 2023 on final-mile / brokerage deals; none in 2025–26). Bull +$100m p.a. (assumption).', 'm', True),
    ],
    'dda_pct': {2027: 0.051, 2028: 0.051, 2029: 0.051, 2030: 0.051},
    'dda_note': ('Input. 9M/26 5.3% of revenue (revenue inflated by fuel surcharge; D&A $544m, +1% y/y after longer useful lives for chassis and trailers from 2025); FY25 6.0%, FY21–22 4.4–4.6%.'),
    'amort26': AM['2026'], 'amort_sched': {2027: AM['2027'], 2028: AM['2028'], 2029: AM['2029'], 2030: AM['2030']},
    'amort_note': AM['src'] + ' 2026 $19.7m, 2027 $15.6m, 2028 $9.7m, 2029 $9.5m, 2030 $8.6m.',
    'sbc_pct': 0.0055, 'etr': 0.24,
    'fuel_share': {2027: 0.18, 2028: 0.18, 2029: 0.18, 2030: 0.18},
    'fuel_note': ('Fuel surcharge revenue is a pass-through of diesel. Q2–Q3/26 18% of revenue vs 12–13% in 2024–25. Forecast held at the Q3/26 share (assumption: fuel flat); '
                  'it only splits revenue into ex-fuel and fuel surcharge — the segment build is on gross revenue.'),
    'capex_pct': {2027: 0.055, 2028: 0.060, 2029: 0.060, 2030: 0.060},
    'capex_pct_note': ('Input. FY26 outlook ~$700m (≈5.0% of revenue); FY25 4.8%, FY24 5.6%, FY23 12.5% and FY22 9.7% (container and tractor build-out). '
                       'Intermodal has spare container capacity, so growth capex stays below the 2022–23 peak.'),
    'sale_pct': 0.20,
    'dps_q': 0.45, 'dps_g': 0.03, 'def_q4': 0.0, 'def_ae': 30.0, 'iss_q4': 0.05, 'iss_ae': 0.30, 'dil': 0.9,
    'iss_notes': {2027: 0.0, 2028: 300.0, 2029: 0.0, 2030: 750.0},
    'repay': {2027: 0.0, 2028: 300.0, 2029: 0.0, 2030: 750.0},
    'mat': {2027: 300.0, 2028: 0.0, 2029: 750.0, 2030: 0.0},
    'repay_note': ('Term loans $300m due Nov-2028; $750m 4.90% senior notes due March 2030 (Q3-26 10-Q). Carrying amounts are ~$8m below face (unamortized discount and issuance costs; held). '
                   'Both assumed refinanced at maturity (input row above).'),
    'min_cash': 20.0,
    'r_debt': {2027: 0.049, 2028: 0.049, 2029: 0.050, 2030: 0.050},
    'r_debt_note': '4.90% senior notes due 2030; credit facility (revolver and term loans) at 4.85% average at 30-Sep-2026 (SOFR-based).',
    'wc': WC,
    'px': MAN['price']['px'],
    'px_note': ('VALUATION — share price input $237.64 = average price paid per share for common stock repurchased in September 2026 (Q3-26 Form 10-Q Part II Item 2, filed '
                '23-Oct-2026 — the latest share price in an SEC filing; ~$22bn market cap); update to market'),
    'mna_note': 'Scenario lever M&A_spend (Base none). Funded from cash / revolver (debt schedule).',
    'etr_note': OUTLOOK['note'],
    'capex_note': 'Q3-26 Form 10-Q (23-Oct-2026), Liquidity: "We expect to spend approximately $700 million for net capital expenditures during the full calendar year 2026."',
}

# ====================================================================== compute engine
def hist_value(row, col):
    kw = row.kw; path = kw.get('data')
    if not path: return None
    if kw.get('ppa'):
        v = MAN['ppa'].get(pkey(col), {}).get(path.split('_', 1)[1])
        return v if kw.get('textdata') else num(v)
    v = xget(pkey(col), path)
    return v if kw.get('textdata') else num(v)

def first(kw, keys):
    for k in keys:
        if k in kw: return k
    return None

def compute(row, col):
    kw = row.kw; k = col.kind
    CTX.col = col
    if kw.get('ann') and col.q: return None, False
    if k in HISTK:
        v = hist_value(row, col)
        if v is not None: return v, True
        for key in ('hist', 'all'):
            if key in kw:
                return kw[key](), False
        return None, False
    if k == 'QE':
        if row.spec2: return None, False
        if 'qe_in' in kw:
            v = kw['qe_in']; return (v[col.q] if isinstance(v, dict) else v), True
        key = first(kw, ('qe', 'fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    if k == 'E26':
        if 'e26_in' in kw: return kw['e26_in'], True
        if 'e26' in kw: return kw['e26'](), False
        if kw.get('avg') and ('qe' in kw or 'qe_in' in kw): return f'=AVERAGE({Q1}{row.r}:{QE}{row.r})', False
        if kw.get('flow') and not row.spec2 and any(x in kw for x in ('qe', 'qe_in', 'fc')): return S26(row.key), False
        key = first(kw, ('fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    if k == 'AE':
        if 'ae_in' in kw:
            v = kw['ae_in']; return (v[col.year] if isinstance(v, dict) else v), True
        key = first(kw, ('ae', 'fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    return None, False

# ====================================================================== writers
CAGR_G = {'is_rev', 'is_rev_xf', 'g_rev', 'g_seg', 'g_oi', 'o_adj', 'r_adj', 'r_ebitda', 'is_oi', 'd_dda', 'e_adjni', 'e_eps', 'cf_cfo', 'fcf', 'ncapex', 'bs_ta', 'bs_eq',
          'sh_dil', 'is_ni', 'eps_dil', 'dps', 'is_pt', 'is_sw', 'df_rev', 'df_oi'} | {f'{s[0]}_{k}' for s in SEG for k in ('vol', 'unit', 'rev', 'oi')}
CAGR_A = {'g_oim', 'o_adj_m', 'r_adj_m', 'is_oi_m', 'is_or', 'r_ebit_m', 'gm_rev', 'gm_xf', 'gm_jbi', 'gm_jbi_px', 'gm_ebitda_m', 'gm_op_m', 'gm_or', 'gm_net_m', 'gm_pt', 'gm_sw',
          'gm_adjop_m', 'fcf_m', 'fcf_conv', 'capex_pct', 'ra_roic', 'rn_ronta', 'roe', 'lv_x', 'd_dda_p', 'd_sbc_p', 'd_fuel_rev', 'wc_nwc_p', 'is_etr', 'fcf_eb', 'df_m',
          'd_pt', 'd_sw', 'd_fuel', 'd_ins'} | {f'{s[0]}_{k}' for s in SEG for k in ('m', 'or', 'mix')}
A = {y: ANN[y].c for y in ANN}

def style_cagr(ws, r, on):
    src = 16 if on else 12
    for c in CAGR:
        ws[f'{c}{r}']._style = copy.copy(TM[f'{L(CI(c) + TSHIFT)}{src}']._style)

def write_row(ws, row):
    r = row.r; arch = ARCH[row.arch]
    clone_row_style(ws, arch, r)
    ws.cell(r, 2).value = row.label or None
    if row.kw.get('note'): ws[f'{NOTE}{r}'] = row.kw['note']
    style_cagr(ws, r, row.key in CAGR_G or row.key in CAGR_A)
    if row.arch in ('section', 'block', 'blank', 'sub') and not row.kw.get('data'):
        return
    if row.key in DEFS:
        write_defs(ws, row); return
    nf = NF[row.nf]
    for col in COLS:
        v, inp = compute(row, col)
        if v is None: continue
        cell = ws[f'{col.c}{r}']
        cell.value = v
        if not row.kw.get('textdata'): cell.number_format = nf
        if inp:
            set_color(cell, BLUE, bold=True if col.kind in FCK else None)
            lk = row.kw.get('labkey')
            if lk and col.kind in HISTK and isinstance(v, (int, float)) and abs(v) > 1e-9:
                t = xget(pkey(col), lk)
                if t: comment(cell, f'Company items ({pkey(col)}): {t}', 380, 110)
        elif row.arch == 'growth' and col.kind in HISTK:
            set_color(cell, GRAY)
        else:
            set_color(cell, BLACK)
    rc = CELL_COMMENTS.get(row.key, {})
    for c, t in rc.items(): comment(ws[f'{c}{r}'], t)
    if row.key in CAGR_G:
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(({A[2030]}{r}/{A[2025]}{r})^(1/5)-1,"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2020]}{r})^(1/5)-1,"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2015]}{r})^(1/10)-1,"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2006]}{r})^(1/19)-1,"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = '0%;\\(0%\\);"n/m"'
    elif row.key in CAGR_A:
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2026, 2031))}),"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2021, 2026))}),"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2016, 2026))}),"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2006, 2026))}),"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = NF['pct']
    t = LABEL_SOURCES.get(row.key)
    if t: comment(ws.cell(r, 2), t)

REL = 'Source: J.B. Hunt earnings releases (Form 8-K Item 2.02, Ex. 99.1) — '
LABEL_SOURCES = {
    'jbi_vol': REL + '"Operating Statistics by Segment" (loads; as originally reported).',
    'jbi_rev': REL + '"Financial Information By Segment" (revenue and operating income, as originally reported; FY2006 from the FY2007 release — ICS recast; 2019 from the 2020 releases — FMS recast).',
    'dcs_vol': REL + '"Operating Statistics by Segment" (average trucks during the period: company-owned, independent-contractor and customer-owned trucks). 2019 from the 2020 release comparatives (ex Final Mile).',
    'fms_vol': REL + '"Operating Statistics by Segment" (stops), published from Q1-20; 2019 from the 2020 release comparatives. Σ recast 2019 quarters differs from the recast FY2019 by 53 thousand stops (annual figure used).',
    'is_rev': REL + 'condensed consolidated statements of earnings, as originally reported. Q3-19 from the Q3-20 release comparative (= Q3-19 Form 10-Q).',
    'd_items': REL + 'text of each release (items the company quantified); listed with sources in manual_items.json.',
    'is_oi_x': 'Source: SEC XBRL company facts (us-gaap:OperatingIncomeLoss), value as first filed in the 10-Q / 10-K.',
    'cf_ni': ('Source: Forms 10-K / 10-Q consolidated statements of cash flows via XBRL company facts (values as first filed; year to date, discrete quarters derived, Q4 = FY − 9M). '
              'FY2006–07 from the FY2008 10-K.'),
    'bs_cash': REL + 'condensed consolidated balance sheets (period ends) and supplemental data (actual shares outstanding).',
    'sh_basic': 'Source: XBRL company facts (weighted average basic shares; FY2006–07 from the FY2008 10-K; Q4 = 4 × FY − Σ Q1–Q3). Diluted shares: releases. No stock split since the 2-for-1 of May-2005.',
    'dps': 'Source: XBRL company facts (dividends per share; Q4 = FY − 9M); FY2006–07 from the FY2008 10-K selected financial data.',
    'ds_total': 'Source: release balance sheets; Q3-26 Form 10-Q Note 4 (financing arrangements).',
    'ncapex': 'Company term ("net capital expenditures"), also quoted in the release supplemental data; here from the filed cash-flow statements.',
}
CELL_COMMENTS = {}
def comments_setup():
    a06, a19 = A[2006], A[2019]
    q19 = [QC[(2019, q)].c for q in (1, 2, 3, 4)]
    CELL_COMMENTS['jbt_rev'] = {a06: 'Recast: FY2006 as presented in the FY2007 release, after Integrated Capacity Solutions was separated from Truck (originally reported Truck revenue $1,007.6m).'}
    CELL_COMMENTS['jbt_oi'] = {a06: 'Recast: FY2006 as presented in the FY2007 release (originally reported Truck operating income $86.9m, incl. ICS $3.4m).'}
    CELL_COMMENTS['ics_rev'] = {a06: 'Recast: FY2006 as presented in the FY2007 release (ICS reported separately from 2007).'}
    for k, what in (('dcs_rev', 'revenue'), ('dcs_oi', 'operating income'), ('dcs_vol', 'average trucks')):
        CELL_COMMENTS[k] = {c: f'Recast: 2019 Dedicated {what} as presented in the 2020 releases, excluding Final Mile Services (separated Q1-20). 2018 and earlier include final mile, '
                               'so the 2019 y/y change is not like-for-like — see the Dedicated + Final Mile memo rows.' for c in [a19] + q19}
    q319 = QC[(2019, 3)].c
    CELL_COMMENTS['is_oi'] = {q319: MAN['corrections']['Q3-19']['published'] + '. ' + MAN['corrections']['Q3-19']['why'] + ' Model: ' + MAN['corrections']['Q3-19']['model'] + '.'}
    CELL_COMMENTS['dps'] = {QC[(2013, 1)].c: MAN['x_manual']['Q1-13']['note']}
    CELL_COMMENTS['fms_vol'] = {a19: MAN['known_exceptions']['FY2019 fms_stops']}

DEFS = {}
def defs_setup():
    flags = {}
    for it in MAN['company_items']['items']:
        p = it['period']
        col = QC[(2000 + int(p[-2:]), int(p[1]))].c if p.startswith('Q') else A[int(p)]
        flags[col] = (it['label'].split(':')[0] + ': item quantified by the company' , it['label'])
    DEFS['o_def'] = {'C': ('Model definition throughout: GAAP operating income + only the items the company quantified in its releases (no company non-GAAP measure exists)', MAN['company_items']['note'])}
    DEFS['o_def'].update({c: v for c, v in flags.items() if c != 'C'})
    if 'C' in flags: DEFS['o_def']['C'] = (DEFS['o_def']['C'][0] + ' · ' + flags['C'][0], flags['C'][1])
    DEFS['e_def'] = {'C': ('Model definition throughout: GAAP net earnings + company-quantified items, tax-effected (company after-tax figure where stated; else period rate bounded 15–40%)', None),
                     QC[(2017, 1)].c: ('Q1-17: $13.6m discrete tax benefit removed', None),
                     QC[(2017, 4)].c: ('Q4-17: $309.2m Tax Cuts and Jobs Act benefit removed', None)}
    DEFS['o_pub'] = {'C': ('n/p — J.B. Hunt reports U.S. GAAP results only; no adjusted operating income is published', None)}
    DEFS['r_adj_pub'] = {'C': ('n/p — the company publishes no EBITDA or adjusted EBITDA', None)}
    DEFS['e_pub'] = {'C': ('n/p — the company reports GAAP EPS only (per-share effects of items are quoted in the release text)', None)}
def write_defs(ws, row):
    for c, (txt, cm) in DEFS[row.key].items():
        cell = ws[f'{c}{row.r}']; cell.value = txt
        cell.font = Font(name='Calibri', sz=10, b=True, i=True, color='FFC00000')
        if cm: comment(cell, cm)

def write_scen(ws):
    srcrow = {'hdr': 9, 'out_hdr': 11, 'pt_hdr': 15, 'out': 12, 'pt': 16, 'lev': 28, 'blk': 30, 'yr': 31}
    for spec_ in SCEN_ROWS:
        r, kind = spec_[0], spec_[1]
        for ci in range(CI(SL), CI(SNOTE) + 1):
            ws.cell(r, ci)._style = copy.copy(TM.cell(srcrow[kind], ci + TSHIFT)._style)
        if kind in ('hdr', 'out_hdr', 'pt_hdr'):
            _, _, a, b, c_, d_, e = spec_
            for col, v in zip([SL, SBULL, SBASE, SBEAR, SNOTE], [a, b, c_, d_, e]):
                if v is not None: ws[f'{col}{r}'] = v
        elif kind == 'out':
            _, _, lab, hi, mid, lo, note, nf = spec_
            ws[f'{SL}{r}'] = lab
            for col, v in zip([SBULL, SBASE, SBEAR], [hi, mid, lo]):
                ws[f'{col}{r}'] = v; ws[f'{col}{r}'].number_format = NF[nf]; set_color(ws[f'{col}{r}'], BLUE)
            ws[f'{SNOTE}{r}'] = note
        elif kind == 'pt':
            _, _, lab, _, val, _, note, nf = spec_
            ws[f'{SL}{r}'] = lab; ws[f'{SBASE}{r}'] = val; ws[f'{SBASE}{r}'].number_format = NF[nf]; set_color(ws[f'{SBASE}{r}'], BLUE); ws[f'{SNOTE}{r}'] = note
        elif kind == 'lev':
            _, _, lab, a, b, c_, note = spec_
            ws[f'{SL}{r}'] = lab
            for col, v in zip([SBULL, SBASE, SBEAR], [a, b, c_]):
                ws[f'{col}{r}'] = v; ws[f'{col}{r}'].number_format = NF['x']
            ws[f'{SNOTE}{r}'] = note
        elif kind == 'blk':
            _, _, lab, db, mid, de, note, nf = spec_
            ws[f'{SL}{r}'] = lab; ws[f'{SBULL}{r}'] = db; ws[f'{SBASE}{r}'] = mid; ws[f'{SBEAR}{r}'] = de; ws[f'{SNOTE}{r}'] = note
            for col in (SBULL, SBEAR):
                ws[f'{col}{r}'].number_format = '\\+#,##0;\\-#,##0' if nf == 'm' else '\\+0.0%;\\-0.0%'
        elif kind == 'yr':
            _, _, lab, hdr, base, clamp, _, nf = spec_
            ws[f'{SL}{r}'] = lab; ws[f'{SBASE}{r}'] = base
            if clamp:
                ws[f'{SBULL}{r}'] = f'=MAX(0,{SBASE}{r}+${SBULL}${hdr})'; ws[f'{SBEAR}{r}'] = f'=MAX(0,{SBASE}{r}+${SBEAR}${hdr})'
            else:
                ws[f'{SBULL}{r}'] = f'={SBASE}{r}+${SBULL}${hdr}'; ws[f'{SBEAR}{r}'] = f'={SBASE}{r}+${SBEAR}${hdr}'
            for col in (SBULL, SBASE, SBEAR): ws[f'{col}{r}'].number_format = NF[nf]

def write_header(ws):
    for r in range(1, 8):
        clone_row_style(ws, r, r, 2, CI(LASTC))
    ws[f'{NOTE}1'] = 'SCENARIO SWITCH ▼ (Bull / Base / Bear) — drives all scenario-linked forecast drivers'
    ws[f'{NOTE}2'] = 'Base'
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: Q4/26E seasonality (upper quartile / average / lower quartile of the 2016–25 Q3→Q4 changes in '
            'volume, revenue per unit and segment margin), Q4/26E buybacks, 2027E–2030E segment volume, revenue per unit and operating margin, M&A spend and the leverage '
            f'target for 2027E+ buybacks (scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'J.B. Hunt Transport Services, Inc. (NASDAQ: JBHT) — 3-Statement Financial Model'
    ws['B3'] = ('US GAAP as reported · USD millions (per-share data in USD; shares in millions; loads and stops in thousands) · Calendar fiscal year · '
                'Source: J.B. Hunt Forms 10-K / 10-Q and Form 8-K earnings releases (Ex. 99.1), SEC EDGAR (CIK 728535); XBRL company facts; '
                'investor-relations releases at jbhunt.com are the same documents as filed on EDGAR. No guidance from outside EDGAR is used; statements attributed to earnings calls or '
                'investor presentations are labelled UNVERIFIED in the scenario table')
    ws['B4'] = ('Basis notes: as originally reported, with two segment recasts from the following year\'s release (cell comments): FY2006 (Integrated Capacity Solutions separated from Truck in 2007) '
                'and 2019 (Final Mile Services separated from Dedicated in Q1-20; 2018 and earlier Dedicated includes final mile). Q3-19 statement of earnings per the Form 10-Q '
                '(the release pre-dated $44.2m of BNSF arbitration charges). No stock split since May-2005. J.B. Hunt publishes no non-GAAP measures and no revenue / EPS guidance: '
                'adjusted measures are model definitions; Q4/26E follows historical seasonality; FY26 tax rate (~24%) and net capex (~$700m) per the company.')
    ws[f'{CAGR[0]}5'] = 'Forecast'
    for c in CAGR[1:]: ws[f'{c}5'] = 'Historical'
    ws['B6'] = '(USDm)'
    for col in COLS: ws[f'{col.c}6'] = col.label
    ws[f'{NOTE}6'] = 'Modelling Notes'
    for c, a, b in zip(CAGR, ['5Y CAGR', '5Y CAGR', '10Y CAGR', '19Y CAGR'], ["25-'30", "20-'25", "15-'25", "06-'25"]):
        ws[f'{c}6'] = a; ws[f'{c}7'] = b

def set_columns(ws):
    for k in list(ws.column_dimensions.keys()): del ws.column_dimensions[k]
    ws.column_dimensions['A'].width = TM.column_dimensions['A'].width
    ws.column_dimensions['B'].width = TM.column_dimensions['B'].width
    wid = {'A': 13.0, 'Q': 9.5703125, 'QE': 11.42578125, 'E26': 14.140625, 'AE': 13.0}
    for col in COLS:
        cd = ws.column_dimensions[col.c]; cd.width = wid[col.kind]
        if col.q:
            cd.outlineLevel = 1; cd.hidden = True
    for ci in range(CI(NOTE), CI(LASTC) + 1):
        ws.column_dimensions[L(ci)].width = TM.column_dimensions[L(ci + TSHIFT)].width or 13.0
    ws.sheet_format.outlineLevelCol = 1

def main():
    import openpyxl
    wb = openpyxl.load_workbook(TEMPLATE)
    if 'DCF_old' in wb.sheetnames: del wb['DCF_old']
    ws = wb['Model']
    blank_style = copy.copy(ws['A1']._style)
    for rowc in ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=ws.max_column):
        for c in rowc:
            c.value = None; c.comment = None; c._style = copy.copy(blank_style)
    for k in list(ws.row_dimensions.keys()):
        rd = ws.row_dimensions[k]; rd.outlineLevel = 0; rd.hidden = False
    ws.data_validations.dataValidation = []
    scen_layout(V0)
    build_spec(V0)
    n1 = len(fw.SPEC)
    build_spec2(V0)
    for i, row in enumerate(fw.SPEC): row.spec2 = i >= n1
    last = number_rows(8)
    for r in range(1, last + 1): ws.row_dimensions[r].height = 15.0
    ws.row_dimensions[2].height = 21.0
    defs_setup(); comments_setup()
    write_header(ws)
    for row in fw.SPEC: write_row(ws, row)
    write_scen(ws)
    set_columns(ws)
    ws.freeze_panes = 'C8'
    ws.sheet_view.zoomScale = 70
    import other_sheets as osh
    osh.do_all(wb)
    wb.calculation.fullCalcOnLoad = True
    wb.save(OUT)
    osh.inject_charts(OUT)
    print('rows', fw.SPEC[-1].r, 'saved', OUT)
    return wb

RECALC = os.environ.get('XLSX_RECALC', '/mnt/skills/public/xlsx/scripts/recalc.py')
def recalc(path, timeout=600):
    import subprocess
    out = subprocess.run(['python3', RECALC, path, str(timeout)], capture_output=True, text=True, cwd=os.path.dirname(RECALC))
    try:
        return json.loads(out.stdout)
    except Exception:
        return {'raw': out.stdout[-2000:], 'err': out.stderr[-2000:]}

def scenario_snapshots():
    import openpyxl
    import other_sheets as osh
    snaps = {}
    for scen in ('Bull', 'Bear'):
        p = os.path.join(BASE, f'JBHT_{scen}.xlsx')
        wb = openpyxl.load_workbook(OUT); wb['Model'][f'{NOTE}2'] = scen; wb.save(p)
        res = recalc(p); print(scen, res.get('status'), res.get('total_errors'))
        v = openpyxl.load_workbook(p, data_only=True)['Bull-Base-Bear']
        snaps[scen] = {(r, c): v[f'{c}{r}'].value for r in range(9, 51) for c in 'CDEFGHIJKL' if v[f'{c}{r}'].value is not None}
        os.remove(p)
    wb = openpyxl.load_workbook(OUT)
    osh.snapshot_values(wb, snaps['Bull'], snaps['Bear'])
    wb.calculation.fullCalcOnLoad = True
    wb.save(OUT)
    osh.inject_charts(OUT)

NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
def inject_values(src_xlsx, recalc_xlsx):
    """Store cached formula results (from a LibreOffice-recalculated copy) in the openpyxl file, so the workbook reads correctly in any
    viewer; fullCalcOnLoad stays set so Excel recalculates on open. Same approach as the LECO / ESAB finishing step."""
    import zipfile, shutil, openpyxl
    from lxml import etree
    wbv = openpyxl.load_workbook(recalc_xlsx, data_only=True)
    zin = zipfile.ZipFile(src_xlsx)
    wbxml = etree.fromstring(zin.read('xl/workbook.xml'))
    rels = etree.fromstring(zin.read('xl/_rels/workbook.xml.rels'))
    rid2t = {r.get('Id'): r.get('Target') for r in rels}
    sheets = {}
    for s in wbxml.iter('{%s}sheet' % NS):
        rid = s.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        sheets['xl/' + rid2t[rid].lstrip('/').replace('xl/', '')] = s.get('name')
    tmp = src_xlsx + '.tmp'
    zout = zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED)
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename in sheets:
            ws = wbv[sheets[item.filename]]
            root = etree.fromstring(data)
            for c in root.iter('{%s}c' % NS):
                f = c.find('{%s}f' % NS)
                if f is None: continue
                v = ws[c.get('r')].value
                old = c.find('{%s}v' % NS)
                if old is not None: c.remove(old)
                if v is None: continue
                ve = etree.SubElement(c, '{%s}v' % NS)
                if isinstance(v, bool):
                    c.set('t', 'b'); ve.text = '1' if v else '0'
                elif isinstance(v, (int, float)):
                    if 't' in c.attrib: del c.attrib['t']
                    ve.text = repr(float(v)) if isinstance(v, float) else str(v)
                elif isinstance(v, str) and v.startswith('#'):
                    c.set('t', 'e'); ve.text = v
                else:
                    c.set('t', 'str'); ve.text = str(v)
            data = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
        zout.writestr(item, data)
    zout.close(); zin.close()
    shutil.move(tmp, src_xlsx)

def store_values():
    import shutil
    p = os.path.join(BASE, 'JBHT_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
