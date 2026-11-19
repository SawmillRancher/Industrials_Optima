"""Rewire the Bull-Base-Bear, DCF and Charts tabs of the MLM template (current layout: DCF with live valuation date, fade period,
implied ROIC, target-IRR entry price, reverse DCF and Mauboussin EV/NOPAT; Bull-Base-Bear with buyback rows) to the CSX Model rows /
columns; keep the template chart XML. The template's DCF_old tab is not carried.

Column mapping: the template's 2025A base column becomes CSX 2026E (Q1-Q3 actual, Q4 calibrated; the fiscal year ends six weeks after
the valuation date) and the template's 2026E-2030E become CSX 2027E-2031E, so the DCF's explicit years start in 2027E and net debt is
taken at 31-Dec-2026E (no double counting of the 2026 cash flow, which is inside the year-end net debt)."""
import re, zipfile, shutil
from openpyxl.utils import get_column_letter as L
from fw import R, TEMPLATE, ANN, NOTE

# template Model row -> CSX row key
MAP = {158: 'is_rev', 164: 'r_cash', 166: 'is_oi', 182: 'is_dda', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 219: 'r_aebit', 221: 'r_adj',
       229: 'e_adjni', 231: 'e_eps', 238: 'tot_vol_g', 245: 'gm_ebitda_m', 247: 'gm_op_m', 260: 'cf_oth', 262: 'cf_capex', 263: 'cf_acq',
       280: 'fcf', 282: 'fcf_m', 290: 'bb_px', 291: 'bb_cash', 292: 'bb_sh', 331: 'bs_nci', 408: 'ra_ic', 411: 'ra_roic', 422: 'rn_ronta',
       428: 'lv_nd', 433: 'v_px', 434: 'v_sh'}
CMAP = {'BV': ANN[2026].c, 'CA': ANN[2027].c, 'CB': ANN[2028].c, 'CC': ANN[2029].c, 'CD': ANN[2030].c, 'CE': ANN[2031].c, 'CF': NOTE}
REF = re.compile(r"Model!(\$?)([A-Z]{1,3})(\$?)(\d+)")
HIST = [ANN[y].c for y in range(2006, 2026)]

def remap(f):
    def rep(m):
        c, r = m.group(2), int(m.group(4))
        c2 = CMAP.get(c, c)
        r2 = R[MAP[r]] if r in MAP else r
        if c == 'CF' and r == 2: r2 = 2
        return f'Model!{m.group(1)}{c2}{m.group(3)}{r2}'
    return REF.sub(rep, f)

def hist_stat(f):
    """LT historical AVERAGE / MIN / MAX over the template's annual columns -> CSX FY2006-FY2025 annual columns."""
    m = re.match(r'=IFERROR\((AVERAGE|MIN|MAX)\(Model!C(\d+),', f)
    if not m: return None
    fn, r = m.group(1), int(m.group(2))
    rr = R[MAP[r]]
    return f'=IFERROR({fn}({",".join(f"Model!{c}{rr}" for c in HIST)}),"")'

def fy_dates(f):
    f = re.sub(r'DATE\((\d{4}),12,31\)', lambda m: f'DATE({int(m.group(1)) + 1},12,31)', f)
    f = re.sub(r'DATE\((\d{4})-1,12,31\)', lambda m: f'DATE({int(m.group(1)) + 1}-1,12,31)', f)
    return f

TEXT = {
    'Bull-Base-Bear': {
        'B2': 'CSX Corporation (CSX) — Bull / Base / Bear Case P&L Summary',
        'B3': ('Adjusted figures (company adjusted operating income / EPS where published; adjusted EBITDA = model definition) · USD millions · calendar fiscal years · Live panel linked to Model — '
               'toggle scenario via Model!CG2. Bull and Bear panels are value snapshots generated from the Model with the switch set to each case. 2026E = Q1–Q3 actual + Q4 calibrated to the '
               '(unverified) outlook end-points (revenue +7–9%, Q4 margin +300–400 bps y/y).'),
        'G26': 20, 'H26': 20, 'S26': 22, 'T26': 22, 'AD26': 17, 'AE26': 17, 'AF26': 17,
    },
    'DCF': {
        'B2': 'DCF VALUATION — CSX CORPORATION (CSX)',
        'C5': 0.0425, 'D5': 'Assumption (~US 10Y Treasury yield, Nov-2026; government rate sources not reachable from the build environment); update to market',
        'D6': 'Assumption: US implied ERP ~4.5–5.5%',
        'C7': 0.95, 'D7': 'Assumption: North American Class I railroads (UNP, NSC, CP, CN) ~0.9–1.1; regulated-infrastructure cash flows, cyclical volumes (coal, industrial)',
        'C9': 0.05, 'D9': 'Mar/Oct-2025 5.05% notes due 2035; Sep-2024 4.90% notes due 2055 (FY2025 10-K Note 10); 4.4% average rate on notes outstanding',
        'C10': 0.245, 'D10': 'Model 2027E+ effective tax rate (2025 23.3%; 9M-26 24.1%)',
        'C12': 0.15, 'D12': 'Net debt ~$17.2bn at 30-Sep-2026 vs ~$88bn market cap ($47.67 × ~1.85bn diluted shares); ~2.3x adjusted EBITDA',
        'D15': 'Periods = (Dec-31 of year − today) / 365.25; cash flows assumed at year-end; 2026E (ends 31-Dec-2026, six weeks after the valuation date) is the base year',
        'B18': 'Adjusted operating income less cash restructuring costs',
        'B21': 'plus D&A',
        'B22': '− Property additions and acquisitions (M&A lever 2027E–31E; Base nil)',
        'B26': 'Fade-period growth (2032E–36E; 5.0% → 4.0% linear)', 'I26': 0.05, 'M26': 0.04, 'C27': 0.03,
        'D32': ("CSX's adjusted operating income expenses share-based compensation and all D&A (acquired-intangible amortization is ~$12m p.a.); D&A is added back in row 21 and the "
                'capital intensity of the network (property additions ~15% of revenue, 1.4–1.7x D&A) is deducted in row 22. Cash restructuring costs adjusted out by the company (2017) '
                'are deducted inside row 18; goodwill impairments are non-cash. Equity earnings of affiliates (Conrail, TTX) stay inside operating income and the retained share is not '
                'deducted (immaterial vs the $2.7bn carrying value, which stays inside invested capital).'),
        'D43': 'Opening IC = Model 2026E book IC (equity + net debt at 31-Dec-2026E), rolled forward with property additions + M&A − D&A + ΔWC.',
        'B48': 'Less: Net debt + NCI (Model 2026E year end, 31-Dec-2026)',
        'D48': 'CSX: non-controlling interest immaterial; net debt at the base-year end (≈ valuation date) so that 2027E+ cash flows are not double counted; short-term investments netted.',
        'B50': 'Diluted shares (m, Model 2026E period end)',
        'D76': 'Rationale (CSX characteristics)',
        'C78': 0.06, 'D78': 'Model adjusted operating income CAGR 2026–31E: low-single-digit volume, 3% revenue per unit, labor and purchased-services ratios falling ~100 bps each → ~6% NOPAT growth',
        'C79': 0.12, 'D79': 'Returns on the existing network are high (ROIC mid-teens on book capital) but incremental capital is largely replacement track and equipment; growth projects (sidings, terminals, locomotives) earn low-to-mid-teens',
        'C80': 15, 'D80': 'Duopoly east of the Mississippi with irreplaceable rights of way sustains a long competitive-advantage period; exposure to coal decline, industrial cycles and regulation (STB) tempers it',
        'B90': 'VALUATION  —  Applied to 2029E NOPAT',
        'B91': '2029E Adjusted operating income less cash restructuring costs',
        'B93': '2029E NOPAT',
        'B95': 'Implied Enterprise Value (2029E basis)',
        'B96': 'Less: 2028E year-end net debt + NCI (Model)',
        'B98': 'Diluted shares 2029E (m, Model)',
        'B99': 'Implied share price 2029 ($)',
        'B106': 'Plus: 2026E year-end net debt + NCI',
        'B108': 'CSX market-implied EV/NOPAT (on 2029E NOPAT)',
    },
    'Charts': {
        'B2': 'CSX Corporation — Operating Performance (2012–2025) and Model Forecast (2026E–2031E)',
        'B3': ('USDm · calendar fiscal years · Linked to Model. Bars = total volume y/y % and total revenue per unit y/y % (rail freight). Adjusted EBITDA = model definition '
               '(operating income + D&A + company adjusting items); operating income = GAAP. ROIC / RONTA on adjusted operating income.'),
        'B8': 'Total volume y/y %', 'B9': 'Revenue per unit y/y %', 'B12': 'Adjusted EBITDA (model)', 'B13': 'Operating income (GAAP)',
        'B14': 'Adj. EBITDA Margin %', 'B15': 'Operating Margin %',
    },
}
BBB_ROWS = {9: 'Revenue', 10: '   Revenue y/y %', 11: '   Total volume y/y %', 12: 'Adjusted EBITDA (model definition)',
            15: 'Operating income (GAAP)', 16: '   Operating income y/y %', 17: '   Operating margin (GAAP) %', 19: 'Adjusted net earnings',
            35: 'Adjusted EBITDA (leverage basis)', 36: '   Adjusted EBITDA % of revenue'}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Rail Revenue Drivers: Volume vs. Revenue per Unit, y/y %',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted EBITDA &amp; Operating Income (USDm)',
}

def build_charts(ws):
    for i, y in enumerate(range(2012, 2032)):
        c = L(3 + i); mc = ANN[y].c
        ws[f'{c}7'] = y if y <= 2025 else f'{y}E'
        ws[f'{c}8'] = f'=IFERROR(Model!{mc}{R["tot_vol_g"]}+0,0)'
        ws[f'{c}9'] = f'=IFERROR(Model!{mc}{R["gm_rpu"]}+0,0)'
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
        b.cell(7, i).value = '2026E'
        for k in range(1, 6): b.cell(7, i + k).value = f'{2026 + k}E'
        b.cell(7, i + 6).value = "26-'31 CAGR"
    from openpyxl.comments import Comment
    cm = Comment('P/E on adjusted EPS (company definition where published; = GAAP otherwise). CSX at $47.67 trades at ~23x 2026E adjusted EPS and ~20x 2027E. Exit multiples are assumptions: '
                 'Base 20x, Bull 22x, Bear 17x applied to 2030E–31E (2029E–31E for Bear), in line with the Class I railroad range of the last decade (~16–23x).', 'CSX model')
    cm.width, cm.height = 420, 120; b['N26'].comment = cm
    cm2 = Comment(f'Snapshot (values) of Model rows {R["bb_cash"]}, {R["bb_px"]} and {R["bb_sh"]} (Share Buyback Schedule) with Model!{NOTE}2 = Bull / Bear. '
                  'Base panel (D40:H42) is live-linked.', 'CSX model')
    cm2.width, cm2.height = 420, 90; b['P40'].comment = cm2
    b['J2'] = 'Share price ($):'
    for c in ('B', 'N', 'Z'): b[f'{c}29'] = 'IRR (to Dec-Y-1)'
    for c in ('B', 'N', 'Z'):
        if b[f'{c}40'].value: b[f'{c}40'] = '   Share repurchases ($m; 2026E = Q4)'
    d = wb['DCF']
    for i, col in enumerate('DEFGHIJKLM'):
        d[f'{col}17'] = f'{2027 + i}E'
    a26, a27 = ANN[2026].c, ANN[2027].c
    d['D22'] = f'=Model!{a27}{R["cf_capex"]}+Model!{a27}{R["cf_acq"]}'
    d['D34'] = f'=Model!{a26}{R["ra_ic"]}'
    d['C48'] = f'=Model!{a26}{R["lv_nd"]}+Model!{a26}{R["bs_nci"]}'
    d['C50'] = f'=Model!{a26}{R["v_sh"]}'
    d['C52'] = f'=Model!{a26}{R["v_px"]}'
    d['P17'] = 'CAGR 27–31E'; d['Q17'] = 'CAGR 27–36E'
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
    (Charts!C:V = 2012-2031E) and cached values removed so Excel redraws from the CSX cells."""
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
