"""Rewire the Bull-Base-Bear, DCF and Charts tabs of the MLM template to the LOAR Model rows / columns; keep the template chart XML."""
import re, zipfile, shutil, os
from openpyxl.utils import get_column_letter as L, column_index_from_string as CI
from fw import R, TEMPLATE, ANN, NOTE, TM

# template Model row -> LOAR row key
MAP = {158: 'is_rev', 166: 'is_op', 164: 'd_trans', 182: 'is_dda', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 219: 'r_ebit',
       221: 'r_adj', 229: 'e_adjni', 231: 'e_eps', 238: 'gm_org', 245: 'gm_ebitda_m', 247: 'gm_op_m', 260: 'cf_wc', 262: 'cf_capex',
       263: 'cf_acq', 280: 'fcf', 282: 'fcf_m', 331: 'v_nci', 408: 'ra_ic', 411: 'ra_roic', 422: 'rn_ronta', 428: 'lv_nd',
       433: 'v_px', 434: 'v_sh', 12: 'a_org_g', 30: 'a_org_g', 14: 'a_acq_g', 31: 'a_acq_g'}
# template Model column -> LOAR column (annual 2025A / forecast years / scenario switch)
CMAP = {'BV': ANN[2025].c, 'CA': ANN[2026].c, 'CB': ANN[2027].c, 'CC': ANN[2028].c, 'CD': ANN[2029].c, 'CE': ANN[2030].c, 'CF': NOTE}
REF = re.compile(r"Model!(\$?)([A-Z]{1,3})(\$?)(\d+)")

def remap(f):
    def rep(m):
        c, r = m.group(2), int(m.group(4))
        c2 = CMAP.get(c, c)
        r2 = R[MAP[r]] if r in MAP else r
        if c == 'CF' and r == 2: r2 = 2
        return f'Model!{m.group(1)}{c2}{m.group(3)}{r2}'
    return REF.sub(rep, f)

TEXT = {
    'Bull-Base-Bear': {
        'B2': 'Loar Holdings (LOAR) — Bull / Base / Bear Case P&L Summary',
        'B3': ('Adjusted figures (company definitions: Adjusted EBITDA; Adjusted EPS on the current definition, adding back amortization of acquired intangibles) · USD millions · '
               'Live panel linked to Model — toggle scenario via Model!AP2. Bull and Bear panels are value snapshots generated from the Model with the switch set to each case. '
               '2026E includes LMB (from 23-Dec-2025) and Harper Engineering (from 21-Jan-2026).'),
        'B9': 'Net Sales', 'N9': 'Net Sales', 'Z9': 'Net Sales',
        'B10': '   Net sales y/y %', 'N10': '   Net sales y/y %', 'Z10': '   Net sales y/y %',
        'B11': '   Organic growth %', 'N11': '   Organic growth %', 'Z11': '   Organic growth %',
        'B12': 'Adjusted EBITDA', 'N12': 'Adjusted EBITDA', 'Z12': 'Adjusted EBITDA',
        'B15': 'Operating Income (GAAP)', 'N15': 'Operating Income (GAAP)', 'Z15': 'Operating Income (GAAP)',
        'B16': '   Operating income y/y %', 'N16': '   Operating income y/y %', 'Z16': '   Operating income y/y %',
        'B19': 'Adjusted Net Income', 'N19': 'Adjusted Net Income', 'Z19': 'Adjusted Net Income',
        'B35': 'Adjusted EBITDA (leverage basis)', 'N35': 'Adjusted EBITDA (leverage basis)', 'Z35': 'Adjusted EBITDA (leverage basis)',
        'B36': '   Adjusted EBITDA % of net sales', 'N36': '   Adjusted EBITDA % of net sales', 'Z36': '   Adjusted EBITDA % of net sales',
        'G26': 45, 'H26': 45, 'S26': 52, 'T26': 52, 'AD26': 35, 'AE26': 35, 'AF26': 35,
    },
    'DCF': {
        'B2': 'DCF VALUATION — LOAR HOLDINGS (LOAR)',
        'C5': 0.042, 'D5': 'Assumption (~US 10Y Treasury yield); update to market',
        'C7': 1.10, 'D7': 'Aerospace components peers (TransDigm, HEICO, Ducommun, Karman) ~1.0–1.2; proprietary, sole-source content and ~50% aftermarket mix dampen cyclicality',
        'C9': 0.082, 'D9': 'Term loans at SOFR + 4.25% (B-rated, secured; ~8.2% all-in at 30-Jun-2026)',
        'C10': 0.24, 'D10': 'Model 2027E+ effective tax rate',
        'C12': 0.12, 'D12': 'Net debt ~$0.83bn at 30-Jun-26 vs ~$7.2bn market cap ($75 × ~95.6m diluted shares); D/V ~10–15%',
        'B20': '(−) Transaction & integration costs (cash; added back in Adjusted EBITDA)',
        'B22': 'NOPAT  =  (Adjusted EBIT − transaction & integration costs) × (1 − t)',
        'B23': 'plus depreciation & amortization (total, incl. acquired-intangible amortization)',
        'B24': '− Capex (PP&E) and acquisitions (M&A lever, 2027E+)',
        'I31': 0.08, 'M31': 0.05, 'C32': 0.035,
        'D37': ("Loar's Adjusted EBITDA excludes stock-based compensation (~2.6% of sales), which is a real cost; Adjusted EBIT here deducts all D&A incl. ~$65m p.a. of "
                'acquired-intangible amortization (non-cash, added back in row 23). The 1H/26 Harper Engineering consideration ($249.8m) is excluded from 2026E UFCF and added to opening invested capital.'),
        'D48': ('Opening IC = Model 2025A book IC (equity + net debt) + 2026 acquisitions (Harper Engineering, $249.8m cash), rolled forward with DCF net investment '
                '(capex + M&A − D&A + ΔWC). Terminal incremental ROIC = g / reinvestment rate.'),
        'B53': 'Less: net debt incl. finance leases (Model 2026E YE)', 'B54': 'Less: non-controlling interests (none)',
        'B56': 'Diluted shares (m, Model 2026E period end)',
        'B76': ('To solve for the market-implied path: Data ▸ What-If Analysis ▸ Goal Seek — set C57 (implied price) to the current price (C58) by changing C32 '
                '(terminal growth) or the Model scenario levers (end-market growth, Adjusted EBITDA margin, M&A spend).'),
        'D82': 'Rationale (Loar characteristics)',
        'C84': 0.15, 'D84': 'Model Adjusted EBIT CAGR 2026–30E: high-single-digit organic growth, ~50 bps p.a. margin expansion, ~$300m p.a. of bolt-on M&A and deleveraging → ~15% NOPAT growth',
        'C85': 0.20, 'D85': 'Proprietary, mostly sole-source components (~50% aftermarket) earn very high returns on organic capital (capex ~2.5% of sales); acquisitions at 6–8x sales earn ~8–10% after tax, rising with value drivers',
        'C86': 12, 'D86': 'Niche positions on long-lived platforms (20–30-year aircraft lives), FAA / OEM qualification barriers and a TransDigm-style value-driver model; growth reliant on continued M&A',
        'B98': '(−) 2028E transaction & integration costs',
        'B100': '2028E NOPAT  =  (Adj. EBIT − transaction & integration costs) × (1 − t)',
        'B103': 'Less: YE2027 net debt (Model)',
        'B115': "LOAR's market-implied EV/NOPAT (on 2028E NOPAT)",
    },
    'Charts': {
        'B2': 'Loar Holdings — Operating Performance (2012–2025) and Model Forecast (2026E–2030E)',
        'B3': ('USDm · Linked to Model. Bars = organic growth vs acquisition contribution (as published from 2023; earlier years: total growth shown as organic where no split is available). '
               'Adjusted EBITDA as reconciled by Loar in each period (prospectus for FY2012–23). ROIC / RONTA on Adjusted EBIT (balance sheets from FY2022).'),
        'B8': 'Organic growth %', 'B9': 'Acquisition contribution %', 'B12': 'Adjusted EBITDA', 'B13': 'Operating Income (GAAP)',
    },
}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Net Sales Growth: Organic vs. Acquisitions, y/y %',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted EBITDA &amp; Operating Income (USDm)',
}

def build_charts(ws):
    years = list(range(2012, 2031))
    for i, y in enumerate(years):
        c = L(3 + i); mc = ANN[y].c
        ws[f'{c}7'] = y if y <= 2025 else f'{y}E'
        ws[f'{c}8'] = (f'=IFERROR(Model!{mc}{R["a_org_g"]}+0,IFERROR(Model!{mc}{R["gm_rev"]}+0,0))')
        ws[f'{c}9'] = f'=IFERROR(Model!{mc}{R["a_acq_g"]}+0,0)'
        ws[f'{c}11'] = f'={c}7'
        ws[f'{c}12'] = f'=Model!{mc}{R["r_adj"]}'
        ws[f'{c}13'] = f'=Model!{mc}{R["is_op"]}'
        ws[f'{c}14'] = f'=Model!{mc}{R["gm_ebitda_m"]}'
        ws[f'{c}15'] = f'=Model!{mc}{R["gm_op_m"]}'
        ws[f'{c}17'] = f'={c}7'
        ws[f'{c}18'] = f'=IFERROR(Model!{mc}{R["ra_roic"]}+0,NA())'
        ws[f'{c}19'] = f'=IFERROR(Model!{mc}{R["rn_ronta"]}+0,NA())'
        ws[f'{c}20'] = f'=IFERROR(Model!{mc}{R["gm_ebitda_m"]}+0,NA())'
        ws[f'{c}21'] = f'=IFERROR(Model!{mc}{R["fcf_m"]}+0,NA())'
    for r in (7, 8, 9, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21):
        ws[f'V{r}'] = None

def do_all(wb):
    for name in ('Bull-Base-Bear', 'DCF', 'Charts'):
        ws = wb[name]
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and 'Model!' in c.value:
                    c.value = remap(c.value)
        for addr, t in TEXT.get(name, {}).items():
            ws[addr] = t
    build_charts(wb['Charts'])
    d = wb['DCF']
    a26, a25 = ANN[2026].c, ANN[2025].c
    for col, y in zip('DEFGH', range(2026, 2031)):
        d[f'{col}20'] = f'=-(Model!{ANN[y].c}{R["d_trans"]}+Model!{ANN[y].c}{R["d_integ"]})'
    d['C98'] = f'=-(Model!{ANN[2028].c}{R["d_trans"]}+Model!{ANN[2028].c}{R["d_integ"]})'
    d['D42'] = f'=Model!{a25}{R["ra_ic"]}-Model!{a26}{R["cf_acq"]}'
    b = wb['Bull-Base-Bear']
    b['J2'] = 'Share price ($):'

def snapshot_values(wb, bull, bear):
    ws = wb['Bull-Base-Bear']
    cols = 'CDEFGHIJKL'
    for snap, off in ((bull, 'OPQRSTUVWX'), (bear, ['AA', 'AB', 'AC', 'AD', 'AE', 'AF', 'AG', 'AH', 'AI', 'AJ'])):
        for (r, c), v in snap.items():
            tgt = f'{off[cols.index(c)]}{r}'
            cur = ws[tgt].value
            if isinstance(cur, str) and cur.startswith('='): continue
            if r in (26,): continue
            ws[tgt] = v

def inject_charts(path):
    """Replace openpyxl-rewritten chart parts with the template chart XML (combo charts, colours, layout), retitled,
    re-ranged to Charts!C:U (2012-2030E) and with cached values removed so Excel redraws from the LOAR cells."""
    tz = zipfile.ZipFile(TEMPLATE)
    tmpl = {n: tz.read(n) for n in tz.namelist() if n.startswith('xl/charts/chart')}
    tmp = path + '.tmp'
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in tmpl:
                t = tmpl[item.filename].decode('utf-8')
                for a, b2 in CHART_TITLES.items(): t = t.replace(a, b2)
                t = re.sub(r'(Charts!\$C\$\d+:\$)V(\$\d+)', r'\1U\2', t)
                t = re.sub(r'<c:numCache>.*?</c:numCache>', '', t, flags=re.S)
                t = re.sub(r'<c:strCache>.*?</c:strCache>', '', t, flags=re.S)
                data = t.encode('utf-8')
            zout.writestr(item, data)
    shutil.move(tmp, path)
