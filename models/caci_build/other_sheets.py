"""Rewire the Bull-Base-Bear, DCF and Charts tabs of the MLM template (current layout: DCF with live valuation date, fade period,
implied ROIC, target-IRR entry price, reverse DCF and Mauboussin EV/NOPAT; Bull-Base-Bear with buyback rows) to the CACI Model rows /
columns; keep the template chart XML. The template's DCF_old tab is not carried.

Column mapping: the template's 2025A base column becomes CACI FY2026 (year ended 30-Jun-2026) and the template's 2026E-2030E become
FY2027E-FY2031E. Valuation net debt is taken at 30-Jun-2027E, so the FY2027E unlevered free cash flow is excluded from the DCF
(inclusion flag in DCF row 28) and the explicit cash flows start in FY2028E."""
import re, zipfile, shutil, copy
from openpyxl.utils import get_column_letter as L
from fw import R, TEMPLATE, ANN, NOTE

# template Model row -> CACI row key
MAP = {158: 'is_rev', 164: 'r_cash', 166: 'is_oi', 182: 'd_dep', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 219: 'r_ebit', 221: 'r_adj',
       229: 'e_adjni', 231: 'e_eps', 238: 'gm_org', 245: 'gm_ebitda_m', 247: 'gm_op_m', 260: 'cf_wc', 262: 'cf_capex', 263: 'cf_acq',
       280: 'fcf', 282: 'fcf_m', 290: 'bb_px', 291: 'bb_cash', 292: 'bb_sh', 331: 'bs_nci', 408: 'ra_ic', 411: 'ra_roic', 422: 'rn_ronta',
       428: 'lv_nd', 433: 'v_px', 434: 'v_sh'}
CMAP = {'BV': ANN[2026].c, 'CA': ANN[2027].c, 'CB': ANN[2028].c, 'CC': ANN[2029].c, 'CD': ANN[2030].c, 'CE': ANN[2031].c, 'CF': NOTE}
REF = re.compile(r"Model!(\$?)([A-Z]{1,3})(\$?)(\d+)")
HIST = [ANN[y].c for y in range(2006, 2027)]

def remap(f):
    def rep(m):
        c, r = m.group(2), int(m.group(4))
        c2 = CMAP.get(c, c)
        r2 = R[MAP[r]] if r in MAP else r
        if c == 'CF' and r == 2: r2 = 2
        return f'Model!{m.group(1)}{c2}{m.group(3)}{r2}'
    return REF.sub(rep, f)

def hist_stat(f):
    """LT historical AVERAGE / MIN / MAX over the template's annual columns -> CACI FY2006-FY2026 annual columns."""
    m = re.match(r'=IFERROR\((AVERAGE|MIN|MAX)\(Model!C(\d+),', f)
    if not m: return None
    fn, r = m.group(1), int(m.group(2))
    rr = R[MAP[r]]
    return f'=IFERROR({fn}({",".join(f"Model!{c}{rr}" for c in HIST)}),"")'

def fy_dates(f):
    f = re.sub(r'DATE\((\d{4}),12,31\)', lambda m: f'DATE({int(m.group(1)) + 1},6,30)', f)
    f = re.sub(r'DATE\((\d{4})-1,12,31\)', lambda m: f'DATE({int(m.group(1)) + 1}-1,6,30)', f)
    return f

TEXT = {
    'Bull-Base-Bear': {
        'B2': 'CACI International Inc (CACI) — Bull / Base / Bear Case P&L Summary',
        'B3': ('Company measures (EBITDA; adjusted net income / adjusted diluted EPS = GAAP + intangible amortization, net of tax) · USD millions · fiscal years ended 30 June · '
               f'Live panel linked to Model — toggle scenario via Model!{NOTE}2. Bull and Bear panels are value snapshots generated from the Model with the switch set to each case. '
               'FY2027E = Q1 actual + Q2–Q4 calibrated to the FY27 guidance (revenue $10.7–10.9bn, adjusted net income $740–760m).'),
        'G26': 18, 'H26': 18, 'S26': 21, 'T26': 21, 'AD26': 15, 'AE26': 15, 'AF26': 15,
    },
    'DCF': {
        'B2': 'DCF VALUATION — CACI INTERNATIONAL INC (CACI)',
        'C5': 0.0425, 'D5': 'Assumption (~US 10Y Treasury yield, Nov-2026; government rate sources are not reachable from the build environment); update to market',
        'D6': 'Assumption: US implied ERP ~4.5–5.5%',
        'C7': 0.85, 'D7': 'Assumption: government technology & services peers (Leidos, Booz Allen Hamilton, SAIC, Parsons, KBR) ~0.6–1.0; non-cyclical federal demand, budget-driven',
        'C9': 0.06, 'D9': '6.375% senior notes due 2033 (add-on issued at a premium, effective 6.10%, Mar-2026); term loans at SOFR + margin (5.40–5.65% at 30-Sep-2026)',
        'C10': 0.25, 'D10': 'Model FY2028E+ effective tax rate (Q1/27 25.2%; company assumed statutory rate 25.3%)',
        'C12': 0.25, 'D12': 'Net debt ~$4.6bn at 30-Sep-2026 vs ~$13.9bn market cap ($625.00 × ~22.3m diluted shares); ~3.3x FY2027E EBITDA after ARKA',
        'D15': 'Periods = (30-Jun of fiscal year − today) / 365.25; cash flows assumed at fiscal year-end (30 June). FY2027E cash flow is excluded (flag in row 28): it is already in 30-Jun-2027E net debt.',
        'B18': 'Adj. EBITA (EBITDA − depreciation) less company cash adjustments',
        'B21': 'plus depreciation (amortization of acquired intangibles is not deducted in row 18)',
        'B22': '− Capex (PP&E) and acquisitions (M&A lever 2028E–31E)',
        'B26': 'Fade-period growth (2032E–36E; 6.0% → 4.0% linear)', 'I26': 0.06, 'M26': 0.04, 'C27': 0.03,
        'D32': ("NOPAT basis: CACI's EBITDA already expenses stock-based compensation and acquisition-related costs (the company adds back nothing); adjusted EBITA = EBITDA − depreciation, i.e. before "
                'amortization of acquired intangibles (non-cash; consistent with the company\'s adjusted net income), taxed at the model rate; depreciation is added back in row 21. Tax shield not in UFCF: '
                'ARKA goodwill and intangibles of $1.72bn are tax-deductible (company: tax benefit with a present value of $225m) — upside to the DCF. Row 22 includes bolt-on acquisitions in '
                'FY2028E–31E; the fade period and terminal value assume no new acquisitions. Leases are treated as operating (rent inside EBITDA; lease liabilities not in net debt).'),
        'D43': 'Opening IC = Model FY2026 book IC (equity + net debt at 30-Jun-2026, which includes the $2.6bn ARKA acquisition), rolled forward with capex + M&A − depreciation + ΔWC (FY2027E shown for the roll-forward only).',
        'B48': 'Less: Net debt + NCI (Model FY2027E year end, 30-Jun-2027)',
        'D48': 'Net debt at the end of the current fiscal year, so FY2027E cash flow is not double counted (inclusion flag row 28). CACI has no material noncontrolling interest.',
        'B50': 'Diluted shares (m, Model FY2027E period end)',
        'D76': 'Rationale (CACI characteristics)',
        'C78': 0.09, 'D78': 'Model adjusted EBITA CAGR FY2027–31E: mid-single-digit organic growth, bolt-on M&A and ~80bp of margin expansion → ~9% NOPAT growth',
        'C79': 0.15, 'D79': 'Asset-light organic growth (capex ~1% of revenue, negative-to-low working capital needs) earns high incremental returns; acquired growth earns ~7–9% after tax on purchase price (ARKA ~$2.6bn)',
        'C80': 12, 'D80': 'Long-duration contracts and $34bn backlog (3x revenue), cleared workforce and incumbency on classified programs, software-defined technology franchises; exposed to federal budget cycles and recompetes',
        'B90': 'VALUATION  —  Applied to FY2029E NOPAT',
        'B91': 'FY2029E Adj. EBITA less company cash adjustments',
        'B93': 'FY2029E NOPAT',
        'B95': 'Implied Enterprise Value (FY2029E basis)',
        'B96': 'Less: FY2028E year-end net debt + NCI (Model)',
        'B98': 'Diluted shares FY2029E (m, Model)',
        'B99': 'Implied share price FY2029 ($)',
        'B106': 'Plus: FY2027E year-end net debt + NCI',
        'B108': 'CACI market-implied EV/NOPAT (on FY2029E NOPAT)',
    },
    'Charts': {
        'B2': 'CACI International Inc — Historical Operating Performance (FY2007–FY2026)',
        'B3': ('All historicals · USDm · fiscal years ended 30 June · Linked to Model. Bars = organic revenue growth and the contribution of acquired revenue (company definition; organic growth was '
               'not published for FY2014–FY2022 — shown as 0). EBITDA = company measure in force (model build before FY2008). ROIC / RONTA on adjusted EBITA.'),
        'B8': 'Organic revenue growth %', 'B9': 'Acquired revenue contribution (pp)', 'B12': 'EBITDA', 'B13': 'Income from operations (GAAP)',
        'B14': 'EBITDA Margin %', 'B15': 'GAAP Op. Margin %', 'B20': 'EBITDA margin %',
    },
}
BBB_ROWS = {9: 'Revenues', 10: '   Revenues y/y %', 11: '   Organic revenue growth y/y %', 12: 'EBITDA (company measure)', 13: '   EBITDA margin %',
            15: 'Income from Operations (GAAP)', 16: '   Income from operations y/y %', 19: 'Adjusted Net Income',
            35: 'EBITDA (leverage basis)', 36: '   EBITDA % of revenues', 39: '   Net Debt / EBITDA (x)', 50: 'Implied EV / EBITDA (x)'}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Revenue Growth: Organic vs. Acquired Contribution, %',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'EBITDA &amp; Income from Operations (USDm)',
}

def build_charts(ws):
    for i, y in enumerate(range(2007, 2027)):
        c = L(3 + i); mc = ANN[y].c
        ws[f'{c}7'] = y
        ws[f'{c}8'] = f'=IFERROR(Model!{mc}{R["b_org_g"]}+0,0)'
        ws[f'{c}9'] = f'=IFERROR(Model!{mc}{R["b_acq_p"]}+0,0)'
        ws[f'{c}11'] = f'={c}7'
        ws[f'{c}12'] = f'=Model!{mc}{R["r_adj"]}'
        ws[f'{c}13'] = f'=Model!{mc}{R["is_oi"]}'
        ws[f'{c}14'] = f'=Model!{mc}{R["gm_ebitda_m"]}'
        ws[f'{c}15'] = f'=Model!{mc}{R["gm_op_m"]}'
        ws[f'{c}17'] = f'={c}7'
        ws[f'{c}18'] = f'=IFERROR(Model!{mc}{R["ra_roic"]}+0,NA())'
        ws[f'{c}19'] = f'=IFERROR(Model!{mc}{R["rn_ronta"]}+0,NA())'
        ws[f'{c}20'] = f'=IFERROR(Model!{mc}{R["gm_ebitda_m"]}+0,NA())'
        ws[f'{c}21'] = f'=IFERROR(Model!{mc}{R["fcf_m"]}+0,NA())'

def do_all(wb):
    for name in ('Bull-Base-Bear', 'DCF', 'Charts'):
        ws = wb[name]
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and 'Model!' in c.value:
                    h = hist_stat(c.value) if name == 'Bull-Base-Bear' else None
                    c.value = h or remap(c.value)
                if isinstance(c.value, str) and 'DATE(' in c.value:
                    c.value = fy_dates(c.value)
        for addr, t in TEXT.get(name, {}).items():
            ws[addr] = t
    b = wb['Bull-Base-Bear']
    for r, t in BBB_ROWS.items():
        for c in ('B', 'N', 'Z'): b[f'{c}{r}'] = t
    for c0 in ('C', 'O', 'AA'):
        i = b[f'{c0}7'].column
        b.cell(7, i).value = '2026A'
        for k in range(1, 6): b.cell(7, i + k).value = f'{2026 + k}E'
        b.cell(7, i + 6).value = "26-'31 CAGR"
    from openpyxl.comments import Comment
    cm = Comment('P/E on adjusted diluted EPS (company definition: GAAP + intangible amortization, net of tax). At the $625.00 input price CACI trades at about 18.6x FY2027E adjusted EPS '
                 '(guidance mid-point $33.63). Exit multiples are assumptions: Base 18x, Bull 21x, Bear 15x applied to FY2030E–31E (FY2029E–31E for Bear).', 'CACI model')
    cm.width, cm.height = 420, 120; b['N26'].comment = cm
    cm2 = Comment(f'Snapshot (values) of Model rows {R["bb_cash"]}, {R["bb_px"]} and {R["bb_sh"]} (Share Buyback Schedule) with Model!{NOTE}2 = Bull / Bear. '
                  'Base panel (D40:H42) is live-linked.', 'CACI model')
    cm2.width, cm2.height = 420, 90; b['P40'].comment = cm2
    b['J2'] = 'Share price ($):'
    for c in ('B', 'N', 'Z'): b[f'{c}29'] = 'IRR (to 30-Jun of Y-1)'
    for c in ('B', 'N', 'Z'):
        if b[f'{c}40'].value: b[f'{c}40'] = '   Share repurchases ($m; FY2027E = Q2–Q4)'
    d = wb['DCF']
    for i, col in enumerate('DEFGHIJKLM'):
        d[f'{col}17'] = f'{2027 + i}E'
    a26, a27 = ANN[2026].c, ANN[2027].c
    d['D22'] = f'=Model!{a27}{R["cf_capex"]}+Model!{a27}{R["cf_acq"]}'
    d['D34'] = f'=Model!{a26}{R["ra_ic"]}'
    d['P17'] = 'CAGR 27–31E'; d['Q17'] = 'CAGR 27–36E'
    # FY2027E inclusion flag (net debt is taken at 30-Jun-2027E): UFCF of the flagged year is excluded from the valuation
    d['B28'] = 'UFCF inclusion flag (FY2027E = 0: already in 30-Jun-2027E net debt)'
    d['B28']._style = copy.copy(d['B29']._style)
    for col in 'DEFGHIJKLM':
        d[f'{col}28'] = 0 if col == 'D' else 1
        d[f'{col}28']._style = copy.copy(d[f'{col}19']._style); d[f'{col}28'].number_format = '0'
        f = d[f'{col}24'].value
        if isinstance(f, str) and f.startswith('=') and '28' not in f: d[f'{col}24'] = f'=({f[1:]})*{col}28'
    d['P24'] = '=IFERROR((H24/E24)^(1/(COLUMNS(E24:H24)-1))-1,"n/m")'; d['Q24'] = '=IFERROR((M24/E24)^(1/(COLUMNS(E24:M24)-1))-1,"n/m")'
    build_charts(wb['Charts'])

def snapshot_values(wb, bull, bear):
    ws = wb['Bull-Base-Bear']
    cols = 'CDEFGHIJKL'
    for snap, off in ((bull, 'OPQRSTUVWX'), (bear, ['AA', 'AB', 'AC', 'AD', 'AE', 'AF', 'AG', 'AH', 'AI', 'AJ'])):
        for (r, c), v in snap.items():
            tgt = f'{off[cols.index(c)]}{r}'
            cur = ws[tgt].value
            if isinstance(cur, str) and cur.startswith('='): continue
            if r in (7, 26): continue
            ws[tgt] = v

def inject_charts(path):
    """Replace openpyxl-rewritten chart parts with the template chart XML (combo charts, colours, layout), retitled, ranges kept
    (Charts!C:V = FY2007-FY2026) and cached values removed so Excel redraws from the CACI cells."""
    tz = zipfile.ZipFile(TEMPLATE)
    tmpl = {n: tz.read(n) for n in tz.namelist() if n.startswith('xl/charts/chart')}
    tmp = path + '.tmp'
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in tmpl:
                t = tmpl[item.filename].decode('utf-8')
                for a, b2 in CHART_TITLES.items(): t = t.replace(a, b2)
                t = re.sub(r'<c:numCache>.*?</c:numCache>', '', t, flags=re.S)
                t = re.sub(r'<c:strCache>.*?</c:strCache>', '', t, flags=re.S)
                data = t.encode('utf-8')
            zout.writestr(item, data)
    shutil.move(tmp, path)
