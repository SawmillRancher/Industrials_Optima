"""Build EXENS_Model.xlsx from the MLM template (same layout, formatting and process as the prior models; half-year columns)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'EXENS_Model.xlsx')
GU = MAN['guidance_2026']; Q3 = MAN['q3_2026']; PX = MAN['share_price']; SHL = MAN['shares_out_latest']

# ====================================================================== inputs (V0)
def wc_inputs():
    a = DATA['2025']['x']
    rev = a['rev']
    return {'dso': round(a['bs_ar'] / rev * 365), 'dinv': round(a['bs_inv'] / rev * 365), 'dpo': round(a['bs_ap'] / rev * 365),
            'oca': round(a['bs_oca'] / rev, 3), 'ocl': round(a['bs_ocl'] / rev, 3)}
WC = wc_inputs()
WC['note'] = (f'Forecast inputs at 31-Dec-2025 levels on FY25 revenue (receivables {WC["dso"]}d, inventories {WC["dinv"]}d, payables {WC["dpo"]}d of revenue; '
              f'other current assets {WC["oca"]:.1%} and other current liabilities {WC["ocl"]:.1%} of revenue). Year-end days are used because H1 balances carry '
              'inventory built for the seasonally stronger second half (30-Jun-26 inventories €123m vs €105m).')

V0 = {
    'out_hdr': 'FY26 outlook — raised 17-Sep-2026 (confirmed in the 9M-26 release, 27-Oct-2026)',
    'out_note': ('17-Sep-2026: revenue €558–570m (from €520–540m); Adjusted EBITDA €186–192m (from €168–178m); capex ~9% of revenue excl. capitalized R&D (~3%). '
                 'FY27 guidance due with the FY26 results on 22-Feb-2027.'),
    'outlook': [
        ('out_rev', '  FY26 revenue (€m)', (GU['rev_high'], GU['rev_mid'], GU['rev_low']), 'm1', 'Guided €558–570m (c.20% growth at mid-point). Drives the Q4-26E calibration Δ.'),
        ('out_ebitda', '  FY26 Adjusted EBITDA (€m)', (GU['ebitda_high'], GU['ebitda_mid'], GU['ebitda_low']), 'm1', 'Guided €186–192m (c.25% growth at mid-point). H2/26E = end-point − H1-26 (€83.6m).'),
        ('out_capex', '  FY26 capital expenditure % of revenue (excl. capitalised R&D)', (0.09, 0.09, 0.09), 'pct', 'Guided "around 9%" (capacity expansion in Europe and the US; H1-26 9.2%).'),
        ('out_caprd', '  FY26 capitalised R&D % of revenue', (0.03, 0.03, 0.03), 'pct', 'Guided "around 3%" (FY25 2.9%; H1-26 3.6%).'),
    ],
    'points': [
        ('pt_dna', '  D&A excl. PPA amortisation and brand impairment (€m)', 24.8, 'm1', 'Not guided; H1-26 €11.8m, FY25 €24.0m; capacity assets entering service in H2-26.'),
        ('pt_ppa', '  PPA amortisation (€m)', 15.8, 'm1', 'H1-26 €7.9m (release appendix); FY25 €14.1m implied by the bridge; annualised H1 rate.'),
        ('pt_sbc', '  Share-based payments (€m)', 6.5, 'm1', 'H1-26 €3.0m (LTIP 2025-26 and 2026-28 plans, ExoShare); FY25 €6.8m.'),
        ('pt_nonrec', '  Non-recurring costs (€m)', 3.5, 'm1', 'H1-26 €1.6m (acquisition activity); FY25 €4.7m incl. a €2.4m LR Tech earn-out.'),
        ('pt_int', '  Cost of net debt (€m)', 12.3, 'm1', 'H1-26 €6.3m; TLB margin cut to 1.15% from Jun-2026 offsets higher lease interest.'),
        ('pt_etr', '  Tax rate (H2/26E)', 0.27, 'pct', 'H1-26 current tax rate 26% after loss utilisation; the French tax-group loss carry-forward asset has been fully reversed; statutory 25% + CVAE / foreign rates.'),
        ('pt_agm_d', '  Q4-26E adjusted gross margin Δ vs Q4-25 (pts, both segments)', -0.01, 'pct', '9M-26 margin −85bp y/y (NVLS complete-system mix, US plant staffing, defense-imaging mix); Q3-26 −350bp on a high Q3-25 base. Point estimate.'),
        ('pt_fx', '  Currency effect on revenue growth, 2027E+ (pts)', 0.0, 'pct', 'Forecasts at constant currency (~7% of revenue in USD, ~15% Asia).'),
        ('pt_lease', '  Lease principal repayments, H2/26E (€m)', 2.0, 'm1', 'H1-26 €1.6m; FY25 €3.4m; new US property leases.'),
        ('pt_div', '  Dividend payout ratio (declared on net profit; paid the following year)', 0.25, 'pct', 'Policy 20–25% of net income (FY25: €0.30 = 35% of reported EPS, 25% of EPS ex MA loss). Upper end of the range.'),
    ],
    'blocks': [
        ('AMP_LFL', 'AMP_LFL (Amplification like-for-like revenue growth)', 0.03, -0.05, [0.12, 0.11, 0.10, 0.09],
         '9M-26 +14.5% (Q3 +23.9% reported as the +40% capacity programme ramps); OCCAR tranche 4 (200,000 tubes, >€500m, deliveries 2027–29), Czech (17,000 tubes), BiNOD US. Base fades from the capacity-constrained low-teens.', 'pct', False),
        ('DI_LFL', 'DI_LFL (Detection & Imaging like-for-like revenue growth)', 0.03, -0.05, [0.12, 0.12, 0.11, 0.10],
         '9M-26 +14.1% (drone / counter-drone imaging, SMR nuclear instrumentation; life-science detectors soft). Thermal camera capacity ×3 and cooled IR ×2 in 2026.', 'pct', False),
        ('AMP_AGM', 'AMP_AGM (Amplification adjusted gross margin %)', 0.01, -0.015, [0.515, 0.515, 0.515, 0.515],
         'FY25 50.5%, H1-26 52.5%, 9M-26 51.9% (NVLS systems mix, US staffing). Base holds the 9M-26 level.', 'pct', False),
        ('DI_AGM', 'DI_AGM (Detection & Imaging adjusted gross margin %)', 0.01, -0.015, [0.47, 0.47, 0.47, 0.47],
         'FY25 48.3%, 9M-26 46.6% (defense-imaging mix). Base holds ~47%.', 'pct', False),
        ('EBM', 'EBM (Adjusted EBITDA margin)', 0.01, -0.02, [0.34, 0.345, 0.35, 0.35],
         'FY25 32.4%; FY26 guidance mid-point 33.5%; company: organic Adjusted EBITDA growth >15% "implying a mild progressive improvement in the adjusted EBITDA margin".', 'pct', False),
        ('MA', 'MA (acquisition spend, €m p.a.)', 40.0, -60.0, [60.0, 60.0, 60.0, 60.0],
         'Bolt-on M&A strategy (€1bn revenue ambition; leverage may rise to ~2x): FY25 spend €69.7m (Noxant, NVLS, Phasics), FY24 €31.4m, FY23 €69.3m. Base €60m p.a.', 'm', True),
    ],
    'scope_he': {'amp': 0.0, 'di': 0.02}, 'q3': {'amp': Q3['amp'], 'di': Q3['di'], 'elim': Q3['elim'], 'tot': Q3['tot'], 'lfl': Q3['lfl'],
                                                 'amp_agp': Q3['agp_amp'], 'di_agp': Q3['agp_di'], 'agp_oth': Q3['agp_oth']},
    'elim_pct': -0.003, 'dna_pct': 0.050, 'sbc_pct': 0.012, 'nonrec_ae': 3.0, 'etr': 0.26, 'e_rate': 0.0,
    'capex_pct': {2027: 0.07, 2028: 0.05, 2029: 0.05, 2030: 0.05}, 'caprd_pct': 0.03,
    'ma_evs': 2.5, 'ma_margin': 0.20, 'ma_int': 0.40, 'ma_life': 10, 'ma_di_share': 0.70,
    'wc': WC,
    'rou_pct': 0.033, 'll_rate': 0.065, 'cash_yield': 0.02, 'min_cash': 60.0, 'tlb_rate': 0.0325, 'rcf_rate': 0.0285, 'oth_rate': 0.033, 'tlb_refi': 1.0,
    'dtl_rate': 0.25, 'dil': SHL['dilutive'], 'iss': 0.15, 'bb_ae': 0.0,
    'px': PX['px'], 'px_date': PX['date'],
    'px_note': f'VALUATION — share price input €{PX["px"]:.2f} (Euronext Paris: EXENS, close {PX["date"]}; 2-Nov-2026 intraday €57.25); update to market',
    'rev_guid_note': 'Company FY26 revenue guidance €558–570m (17-Sep-2026, confirmed 27-Oct-2026). Drives the Q4-26E calibration Δ.',
    'eb_guid_note': 'Company FY26 Adjusted EBITDA guidance €186–192m (17-Sep-2026, confirmed 27-Oct-2026). H2/26E = end-point − H1-26 actual.',
}

# ====================================================================== compute engine
def hist_value(row, col):
    kw = row.kw; path = kw.get('data')
    if not path: return None
    v = xget(pkey(col), path)
    if kw.get('textdata'): return v
    return num(v)

def first(kw, keys):
    for k in keys:
        if k in kw: return k
    return None

def compute(row, col):
    kw = row.kw; k = col.kind
    CTX.col = col
    if kw.get('ann') and col.h: return None, False
    if k in HISTK:
        v = hist_value(row, col)
        if v is not None: return v, True
        for key in ('hist', 'all'):
            if key in kw:
                return kw[key](), False
        return None, False
    if k == 'HE':
        if row.spec2 and 'he' not in kw and 'he_in' not in kw and 'fc' not in kw and 'all' not in kw: return None, False
        if 'he_in' in kw: return kw['he_in'], True
        key = first(kw, ('he', 'fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    if k == 'E26':
        if 'e26_in' in kw: return kw['e26_in'], True
        if 'e26' in kw: return kw['e26'](), False
        if kw.get('avg') and ('he' in kw or 'he_in' in kw): return f'=AVERAGE({H1}{row.r},{H2}{row.r})', False
        if kw.get('bs'): return f'={H2}{row.r}', False
        if kw.get('flow') and any(x in kw for x in ('he', 'he_in', 'fc')): return S26(row.key), False
        key = first(kw, ('fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    if k == 'AE':
        if 'ae_in' in kw:
            v = kw['ae_in']; return (v[col.year] if isinstance(v, dict) else v), True
        key = first(kw, ('ae', 'fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    return None, False

# ====================================================================== writers
CAGR_G = {'is_rev', 'g_rev', 'amp', 'di', 'amp_agp', 'di_agp', 'm_agp', 'g_adj', 'r_adj', 'r_ebitda', 'r_ebit', 'is_op', 'is_ni', 'is_nic', 'o_adj', 'e_adjni', 'e_eps',
          'eps_dil', 'cf_cfo', 'fcf', 'fcf_co', 'bs_ta', 'bs_teq', 'sh_dil', 'd_dna', 'd_sbc', 'is_staff', 'dps', 'cf_capex_t'}
CAGR_A = {'m_agpm', 'm_ebm', 'r_adj_m', 'r_ebit_m', 'o_adj_m', 'is_opm', 'gm_rev', 'gm_lfl', 'gm_agpm', 'gm_ebitda_m', 'gm_ebit_m', 'gm_op_m', 'gm_net_m', 'gm_staff',
          'amp_agpm', 'di_agpm', 'amp_lfl', 'di_lfl', 'amp_g', 'di_g', 'g_lfl', 'g_scope', 'amp_mix', 'di_mix', 'm_opex_p', 'fcf_m', 'fcf_conv', 'capex_pct', 'caprd_pct',
          'ra_roic', 'rn_ronta', 'roe', 'is_etr', 'wc_nwc_p', 'd_dna_pct', 'd_sbc_pct', 'lv_x', 'cc_conv'}

def style_cagr(ws, r, on):
    src = 16 if on else 12
    for c in CAGR:
        ws[f'{c}{r}']._style = copy.copy(TM[f'{L(CI(c) + TSHIFT)}{src}']._style)

def write_row(ws, row):
    r = row.r; arch = ARCH[row.arch]
    clone_row_style(ws, arch, r)
    ws.cell(r, 2).value = row.label or None
    if row.kw.get('note'): ws[f'{NOTE}{r}'] = row.kw['note']
    if row.kw.get('group'):
        ws.row_dimensions[r].outlineLevel = 1; ws.row_dimensions[r].hidden = True
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
        elif row.arch == 'growth' and col.kind in HISTK:
            set_color(cell, GRAY)
        else:
            set_color(cell, BLACK)
    a = {y: ANN[y].c for y in ANN}
    if row.key in CAGR_G:
        ws[f'W{r}'] = f'=IFERROR(({a[2030]}{r}/{a[2025]}{r})^(1/5)-1,"n/m")'
        ws[f'X{r}'] = f'=IFERROR(({a[2025]}{r}/{a[2021]}{r})^(1/4)-1,"n/m")'
        ws[f'Y{r}'] = f'=IFERROR(({a[2025]}{r}/{a[2023]}{r})^(1/2)-1,"n/m")'
        ws[f'Z{r}'] = f'=IFERROR(({a[2026]}{r}/{a[2021]}{r})^(1/5)-1,"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = '0%;\\(0%\\);"n/m"'
    elif row.key in CAGR_A:
        ws[f'W{r}'] = f'=IFERROR(AVERAGE({",".join(f"{a[y]}{r}" for y in range(2026, 2031))}),"n/m")'
        ws[f'X{r}'] = f'=IFERROR(AVERAGE({",".join(f"{a[y]}{r}" for y in range(2021, 2026))}),"n/m")'
        ws[f'Y{r}'] = f'=IFERROR(AVERAGE({",".join(f"{a[y]}{r}" for y in range(2023, 2026))}),"n/m")'
        ws[f'Z{r}'] = f'=IFERROR(AVERAGE({",".join(f"{a[y]}{r}" for y in range(2021, 2027))}),"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = NF['pct']
    t = LABEL_SOURCES.get(row.key)
    if t: comment(ws.cell(r, 2), t)

SRC = 'Source: Exosens results / revenue press releases and the half-year and annual financial reports filed with the AMF (www.exosens.com/investors/regulatory-information) — '
LABEL_SOURCES = {
    'amp': ('Source: segment note (Note 5) of the annual and half-year reports; revenue press releases (segment tables and quarterly appendices). FY2021–23 from the IPO '
            'registration document (July 2024) / URD 2024; 2024 halves on the restated continuing-operations basis of the FY2025 release appendix; H2 = FY − H1.'),
    'amp_lfl': SRC + 'like-for-like growth as printed (called "organic growth" in the 2024 releases). The releases never split scope and currency.',
    'amp_qa': SRC + 'Q1 / Q3 trading updates and FY release quarterly appendices (2024 restated for the Microwave Amplification disposal; 2023 from the 9M-2024 release).',
    'amp_agp': SRC + 'adjusted gross margin by segment (segment note; release tables). Company definition: selling price − cost of products and services incl. employee costs (management basis, unaudited).',
    'is_rev': ('Source: consolidated income statements — URD 2025 p.217 (FY2025; FY2024 restated), URD 2024 p.213 (FY2024 as reported; FY2023), IPO registration document '
               '(FY2023 with FY2022; FY2022 with FY2021), half-year reports 2024–2026 (H1-25 restated in the 2026 report). € thousands → € millions; H2 = FY − H1.'),
    'd_dna': SRC + '"Reconciliation of operating profit to Adjusted EBITDA and Adjusted EBIT" (D&A excl. PPA line).',
    'd_ppa': 'Source: implied by the company reconciliation (D&A in the EBITDA bridge − D&A excl. PPA − brand impairment); H1 figures as printed in the release income-statement appendix ("o/w PPA amortization").',
    'r_adj_pub': SRC + 'Adjusted EBITDA as published (segment note / key financial indicators). FY2021–22 from the registration document key figures.',
    'e_pub': SRC + '"Net profit from continued operations ex. PPA amortization (& impairment)" (key financial indicators; URD 2025 §5.2.13).',
    'sh_basic': 'Source: EPS note (Note 14) of the annual / half-year reports: weighted average number of shares outstanding excl. treasury shares. Pre-IPO (FY2021–23) counts are on the former share structure (ordinary + preference shares) and are not comparable.',
    'cf_ni': ('Source: consolidated cash flow statements (URD 2025, URD 2024, registration document, half-year reports); H2 = FY − H1. From FY2025 the statement starts from net profit '
              'from continuing operations with the Microwave Amplification cash flows on one line.'),
    'bs_cash': 'Source: consolidated statements of financial position at 31-Dec (annual reports) and 30-Jun (half-year reports); H2 columns carry the 31-Dec balance sheet.',
    'g_qa': SRC + 'quarterly revenue tables (appendices); 2024 restated per the FY2025 release.',
}

DEFS = {}
def defs_setup():
    h = lambda y, n: HC[(y, n)].c
    DEFS['r_def'] = {
        'C': ('FY2021–23: registration document definition (operating profit + D&A / impairment of non-current assets + other income & expenses + share-based payments + non-recurring costs); MA business included', None),
        h(2024, 1): ('H1/24: as originally reported (incl. Microwave Amplification)', 'H1-2024 report; the FY2025 release later restated 2024 for the MA disposal.'),
        h(2024, 2): ('H2/24: FY24 restated − H1/24 reported (mixed basis)', 'FY24 restated Adjusted EBITDA €119.8m (URD 2025) − H1/24 as reported €56.1m. MA lost €1.3m of Adjusted EBITDA in FY24.'),
        'J': ('FY2024: restated, continuing operations (URD 2025); originally reported €118.5m in the memo row', None),
        h(2025, 1): ('H1/25: restated, continuing operations (H1-2026 report); originally reported €69.5m', None),
        h(2026, 1): ('H1/26+: continuing operations; Adjusted EBIT also excludes the €28.2m brand impairment', None),
    }
    DEFS['e_def'] = {
        'C': ('FY2021–23: "net profit excl. PPA" from the registration document / FY2024 release (incl. MA)', None),
        'J': ('FY2024+: net profit from continuing operations excl. PPA amortisation (restated basis); published gross of tax effect', None),
        h(2026, 1): ('H1/26: also excl. the brand impairment net of the €7.6m deferred-tax reversal', None),
    }

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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: FY26 outlook end-points (revenue, Adjusted EBITDA; high / mid / low), and 2027E–2030E '
            f'segment like-for-like growth, adjusted gross margins, Adjusted EBITDA margin and acquisition spend (scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'Exosens SAS (Euronext Paris: EXENS) — 3-Statement Financial Model'
    ws['B3'] = ('IFRS as adopted by the EU, as reported · € millions (per-share data in €; shares in millions) · Sources: regulator-filed (AMF) documents published at '
                'www.exosens.com/investors — Universal Registration Documents 2024 and 2025, IPO registration document (July 2024, FY2021–23), half-year financial reports 2024–26, '
                'results and revenue press releases, monthly share-count notices · Not an SEC registrant: SEC EDGAR holds only the Citibank F-6EF ADR registration (CIK 0002109666, 5-Feb-2026), with no financial statements')
    ws['B4'] = ('Basis notes: calendar fiscal year; half-year reporter (H1 / FY statements; Q1 and Q3 revenue updates in memo rows). Two segments (Amplification; Detection & Imaging). '
                'Hybrid recast: FY2024 and H1/25 on the continuing-operations basis restated for the Microwave Amplification disposal (31-Dec-2025); FY2023 and earlier and H1/24 as originally '
                'reported; H2 = FY − H1. IPO 7-Jun-2024 (pre-IPO per-share data not comparable). Acquisitions: Xenics (2022), Telops / El-Mul / ProxiVision (2023), Centronic / LR Tech (2024), '
                'Noxant / NVLS / Phasics (2025), Emberion (Apr-2026). H2/26E = Q3-26 actual + Q4-26E calibrated to the 17-Sep-2026 guidance; 2027E–2030E scenario levers.')
    ws[f'{CAGR[0]}5'] = 'Forecast'
    for c in CAGR[1:]: ws[f'{c}5'] = 'Historical'
    ws['B6'] = '(€m)'
    for col in COLS: ws[f'{col.c}6'] = col.label
    ws[f'{NOTE}6'] = 'Modelling Notes'
    for c, a, b in zip(CAGR, ['5Y CAGR', '4Y CAGR', '2Y CAGR', '5Y CAGR'], ["25-'30", "21-'25", "23-'25", "21-'26"]):
        ws[f'{c}6'] = a; ws[f'{c}7'] = b

def set_columns(ws):
    for k in list(ws.column_dimensions.keys()): del ws.column_dimensions[k]
    ws.column_dimensions['A'].width = TM.column_dimensions['A'].width
    ws.column_dimensions['B'].width = TM.column_dimensions['B'].width
    wid = {'A': 13.0, 'H': 11.0, 'HE': 11.5, 'E26': 14.140625, 'AE': 13.0}
    for col in COLS:
        cd = ws.column_dimensions[col.c]; cd.width = wid[col.kind]
        if col.h:
            cd.outlineLevel = 1; cd.hidden = True
    for ci in range(CI(NOTE), CI(LASTC) + 1):
        ws.column_dimensions[L(ci)].width = TM.column_dimensions[L(ci + TSHIFT)].width or 13.0
    ws.sheet_format.outlineLevelCol = 1

def main():
    import openpyxl
    wb = openpyxl.load_workbook(TEMPLATE)
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
    defs_setup()
    write_header(ws)
    for row in fw.SPEC: write_row(ws, row)
    write_scen(ws)
    set_columns(ws)
    ws.freeze_panes = 'C8'
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
        p = os.path.join(BASE, f'EXENS_{scen}.xlsx')
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

def store_values():
    """recalculate a copy with LibreOffice and inject the cached values into the formula workbook"""
    import openpyxl, shutil
    p = os.path.join(BASE, 'EXENS_recalc.xlsx'); shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    shutil.move(p, OUT)
    import other_sheets as osh
    osh.inject_charts(OUT)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
