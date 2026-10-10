"""Rewire the Bull-Base-Bear, DCF (10-year + fade version) and Charts tabs of the MLM template to the ONON Model rows / columns;
keep the template chart XML. The template's legacy DCF_old tab (MLM-specific) is removed."""
import re, zipfile, shutil
from openpyxl.utils import get_column_letter as L
from fw import R, TEMPLATE, ANN, NOTE

# template Model row -> ONON row key (per sheet where the meaning differs)
MAP_COMMON = {158: 'is_rev', 166: 'is_op', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 221: 'r_xt', 229: 'e_adjni', 231: 'e_eps',
              238: 'gm_cc', 245: 'r_xt_m', 247: 'gm_op_m', 280: 'fcf', 282: 'fcf_m', 290: 'bb_px', 291: 'bb_cash', 292: 'bb_sh',
              331: 'v_nci', 411: 'ra_roic', 422: 'rn_ronta', 433: 'v_px', 434: 'v_sh', 408: 'ra_ic', 182: 'is_dda', 219: 'r_ebit',
              260: 'cf_wc', 262: 'cf_capex', 263: 'cf_lease'}
MAP_SHEET = {'Bull-Base-Bear': {428: 'lv_nd'}, 'DCF': {428: 'v_ndx'}}
CMAP = {'BV': ANN[2025].c, 'CA': ANN[2026].c, 'CB': ANN[2027].c, 'CC': ANN[2028].c, 'CD': ANN[2029].c, 'CE': ANN[2030].c, 'CF': NOTE}
REF = re.compile(r"Model!(\$?)([A-Z]{1,3})(\$?)(\d+)")
HIST_ANN = [ANN[y].c for y in range(2019, 2026)]

def remap(f, sheet):
    mp = dict(MAP_COMMON); mp.update(MAP_SHEET.get(sheet, {}))
    def rep(m):
        c, r = m.group(2), int(m.group(4))
        if c == 'CF' and r == 2: return f'Model!{m.group(1)}{NOTE}{m.group(3)}2'
        return f'Model!{m.group(1)}{CMAP.get(c, c)}{m.group(3)}{R[mp[r]] if r in mp else r}'
    return REF.sub(rep, f)

def M(key, y): return f'Model!{ANN[y].c}{R[key]}'

BBB_LAB = {9: 'Net Sales (CHF m)', 10: '   Net sales y/y % (reported)', 11: '   Net sales y/y % (constant currency)',
           12: 'Adjusted EBITDA (company definition)', 13: '   Adjusted EBITDA margin %', 15: 'Operating Result (IFRS)',
           16: '   Operating result y/y %', 17: '   Operating margin (IFRS) %', 19: 'Adjusted Net Income (Class A + B)',
           21: 'Diluted shares, Class A-equivalent (m)', 23: 'Adjusted EPS — Diluted, Class A (CHF)', 26: 'P / E (x) — assumed (adjusted EPS)',
           27: 'Price Target (CHF)', 35: 'Adjusted EBITDA excl. tariff refund (guidance basis)', 36: '   Adjusted EBITDA (excl. refund) % of net sales',
           38: 'Net Debt incl. leases (negative = net cash)', 39: '   Net Debt / Adjusted EBITDA (x)', 40: '   Share repurchases (CHF m)',
           41: '   Implied avg buyback price (USD)', 42: '   Shares repurchased (m)', 47: 'Implied Market Cap (CHF m)', 48: '(+) Net Debt incl. leases & NCI',
           49: 'Implied Enterprise Value (CHF m)'}

TEXT = {
    'Bull-Base-Bear': {
        'B2': 'On Holding (ONON) — Bull / Base / Bear Case P&L Summary',
        'B3': ('Adjusted figures (company definitions: Adjusted EBITDA excl. SBC; adjusted EPS Class A on Class A-equivalent shares) · CHF millions · '
               'Live panel linked to Model — toggle scenario via Model!AM2. Bull and Bear panels are value snapshots generated from the Model with the switch set to each case. '
               '2026E reported figures include the Q3-26 tariff refund (row 35 excludes it, as guided). Price target / IRR in CHF (USD price × USD/CHF).'),
        'J2': 'Share price (CHF):',
        'F26': 25, 'G26': 25, 'H26': 25, 'R26': 32, 'S26': 32, 'T26': 32, 'AD26': 16, 'AE26': 16, 'AF26': 16,
        'B7': '(CHFm, except EPS and shares)', 'N7': '(CHFm, except EPS and shares)', 'Z7': '(CHFm, except EPS and shares)',
    },
    'DCF': {
        'B2': 'DCF VALUATION — ON HOLDING AG (ONON)',
        'C5': 0.042, 'D5': 'US 10Y Treasury (~4.2%): forecasts hold FX at spot, so CHF cash flows carry USD / EUR economics (a CHF rate would need ~2–3% p.a. CHF appreciation built in)',
        'C6': 0.05, 'D6': 'Implied ERP ~4.5–5.5% (Damodaran)',
        'C7': 1.25, 'D7': 'Premium sportswear / footwear peers (Deckers, Lululemon, Nike, adidas, Amer Sports) ~1.0–1.4; high-growth, discretionary, founder-led',
        'C9': 0.05, 'D9': 'No bank debt; CHF 700m revolving facility undrawn (marginal cost ~SARON / SOFR + margin)',
        'C10': 0.17, 'D10': 'Model 2027E+ effective tax rate (Swiss holding, global footprint)',
        'C12': 0.0, 'D12': 'Net cash (CHF ~1.2bn at 30-Jun-26) and no financial debt; leases treated as operating costs in UFCF (lease payments deducted, liabilities not in net debt)',
        'B18': 'Adj. EBIT less share-based compensation (= IFRS operating result; SBC is a real cost)',
        'B21': 'plus D&A (incl. right-of-use depreciation)',
        'B22': '− Capex (PP&E, intangibles) and lease principal payments',
        'B26': 'Fade-period growth (2031E–35E; 12% → 6% linear)', 'I26': 0.12, 'M26': 0.06, 'C27': 0.035,
        'D32': ("On's Adjusted EBITDA excludes share-based compensation (~2% of sales), which is deducted here (row 18 = Adjusted EBIT − SBC = IFRS operating result). "
                'IFRS 16: D&A includes right-of-use depreciation, so lease principal payments are deducted with capex in row 22 and lease liabilities are excluded '
                'from net debt in the equity bridge (rent-as-opex basis). No acquisitions assumed. Forecasts at constant spot FX; FX translation is the largest '
                'swing factor (≈ 80%+ of sales outside Switzerland, ~50% in the Americas).'),
        'D43': 'Opening IC = Model 2025A equity − cash (leases treated as operating), rolled forward with capex + lease payments − D&A + ΔWC.',
        'B48': 'Less: Net debt excl. leases + NCI (Model 2026E YE; negative = net cash)',
        'D48': 'Net cash (2026E year end, after Q4-26 buybacks) is added to enterprise value; lease liabilities excluded (lease payments are in UFCF).',
        'B50': 'Diluted Class A-equivalent shares (m, Model 2026E)', 'B51': 'Implied share price (CHF)', 'B52': 'Current share price (CHF; USD price × USD/CHF)',
        'B55': 'Max entry price for target IRR (CHF)',
        'B70': ('To solve for the market-implied path: Data ▸ What-If Analysis ▸ Goal Seek — set C51 to the current price (C52) by changing C27 (terminal growth), '
                'the fade-period growth inputs (I26:M26) or the Model scenario levers (regional cc growth, gross margin, Adjusted EBITDA margin).'),
        'D76': 'Rationale (On Holding characteristics)',
        'C78': 0.18, 'D78': 'Model Adjusted EBIT CAGR 2026–30E: high-teens cc sales growth and ~2.5pts Adjusted EBITDA margin expansion to ≥22% (Investor Day 2029) → ~18% NOPAT growth',
        'C79': 0.35, 'D79': 'Asset-light, outsourced manufacturing, ≥65% gross margin and negative-to-low net working capital intensity at scale: incremental returns well above WACC (2025 ROIC >30%)',
        'C80': 12, 'D80': 'Brand / innovation moat (CloudTec, LightSpray, athlete validation), DTC and global expansion runway; fashion / brand-cycle risk caps the advantage period',
        'B91': '2028E Adj. EBIT less share-based compensation', 'B96': 'Less: YE2027 net debt excl. leases + NCI (Model)',
        'B98': 'Diluted shares 2028E (m, Model)', 'B99': 'Implied share price 2028 (CHF)', 'B101': 'Current share price (CHF)',
        'B108': 'ONON market-implied EV/NOPAT (on 2028E NOPAT)', 'C90': 'CHFm', 'C104': 'CHFm',
    },
    'Charts': {
        'B2': 'On Holding — Operating Performance (2019–2025) and Model Forecast (2026E–2030E)',
        'B3': ('CHFm · Linked to Model. Bars = constant-currency growth vs FX translation effect (published from 2024; earlier years: reported growth shown as constant currency). '
               'Adjusted EBITDA as reconciled by On in each period (prospectus for FY2019–20). ROIC / RONTA on Adjusted EBIT (balance sheets from FY2020).'),
        'B8': 'Constant-currency growth %', 'B9': 'FX translation effect %', 'B12': 'Adjusted EBITDA', 'B13': 'Operating Result (IFRS)',
        'B14': 'Adj. EBITDA Margin %', 'B15': 'IFRS Op. Margin %',
    },
}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Net Sales Growth: Constant Currency vs. FX Translation, y/y %',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted EBITDA &amp; Operating Result (CHFm)',
}
YEARS = list(range(2019, 2031))
LASTCH = L(2 + len(YEARS))          # N

def build_charts(ws):
    for i, y in enumerate(YEARS):
        c = L(3 + i); mc = ANN[y].c
        ws[f'{c}7'] = y if y <= 2025 else f'{y}E'
        ws[f'{c}8'] = f'=IFERROR(Model!{mc}{R["gm_cc"]}+0,IFERROR(Model!{mc}{R["gm_rev"]}+0,0))'
        ws[f'{c}9'] = f'=IFERROR(Model!{mc}{R["g_fx"]}+0,0)'
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
    for ci in range(3 + len(YEARS), 23):
        for r in range(7, 22):
            ws.cell(r, ci).value = None

def lt_hist(ws):
    """LT Hist Avg / Min / Max (J:L, V:X, AH:AJ) on ONON annual history 2019–2025."""
    for r, key in ((13, 'r_adj_m'), (17, 'gm_op_m'), (32, 'fcf_m'), (36, 'r_xt_m'), (44, 'ra_roic'), (45, 'rn_ronta')):
        refs = ','.join(f'Model!{c}{R[key]}' for c in HIST_ANN)
        for col, fn in (('J', 'AVERAGE'), ('K', 'MIN'), ('L', 'MAX')):
            ws[f'{col}{r}'] = f'=IFERROR({fn}({refs}),"")'

def do_all(wb):
    if 'DCF_old' in wb.sheetnames: del wb['DCF_old']
    for name in ('Bull-Base-Bear', 'DCF', 'Charts'):
        ws = wb[name]
        for row in ws.iter_rows():
            for c in row:
                v = c.value
                if hasattr(v, 'text') and 'Model!' in v.text:
                    v.text = remap(v.text, name)
                elif isinstance(v, str) and 'Model!' in v:
                    c.value = remap(v, name)
        for addr, t in TEXT.get(name, {}).items():
            ws[addr] = t
    b = wb['Bull-Base-Bear']
    for r, t in BBB_LAB.items():
        for col in ('B', 'N', 'Z'): b[f'{col}{r}'] = t
    lt_hist(b)
    import copy as _copy
    for c, src in (('F', 'G'), ('R', 'S')):          # template has 2028 price-target rows only in the Bear panel; add Base / Bull
        b[f'{c}27'] = f'={c}26*{c}23'
        b[f'{c}28'] = f'=IFERROR({c}27/$K$2-1,"")'
        b[f'{c}29'] = f'=IFERROR(({c}27/$K$2)^(1/((DATE(2028-1,12,31)-$K$3)/365.25))-1,"")'
        for r in (26, 27, 28, 29):
            b[f'{c}{r}']._style = _copy.copy(b[f'{src}{r}']._style)
    build_charts(wb['Charts'])
    d = wb['DCF']
    for col, y in zip('DEFGH', range(2026, 2031)):
        d[f'{col}18'] = f'={M("r_ebit", y)}-{M("d_sbc", y)}'
        d[f'{col}22'] = f'={M("cf_capex", y)}+{M("cf_lease", y)}'
    d['I22'] = '=H22*(1+I$26)'
    d['D34'] = f'={M("ra_eq", 2025)}-{M("bs_cash", 2025)}'
    d['C91'] = f'={M("r_ebit", 2028)}-{M("d_sbc", 2028)}'

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
    re-ranged to Charts!C:N (2019–2030E) and with cached values removed so Excel redraws from the ONON cells."""
    tz = zipfile.ZipFile(TEMPLATE)
    tmpl = {n: tz.read(n) for n in tz.namelist() if n.startswith('xl/charts/chart')}
    tmp = path + '.tmp'
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in tmpl:
                t = tmpl[item.filename].decode('utf-8')
                for a, b2 in CHART_TITLES.items(): t = t.replace(a, b2)
                t = re.sub(r'(Charts!\$C\$\d+:\$)V(\$\d+)', r'\g<1>' + LASTCH + r'\2', t)
                t = re.sub(r'<c:numCache>.*?</c:numCache>', '', t, flags=re.S)
                t = re.sub(r'<c:strCache>.*?</c:strCache>', '', t, flags=re.S)
                data = t.encode('utf-8')
            zout.writestr(item, data)
    shutil.move(tmp, path)
