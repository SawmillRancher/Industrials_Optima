"""Rewire the Bull-Base-Bear, DCF (10-year + fade version) and Charts tabs of the MLM template to the EXENS Model rows / columns;
keep the template chart XML. The template's legacy DCF_old tab is removed."""
import re, zipfile, shutil
from openpyxl.utils import get_column_letter as L
from fw import R, TEMPLATE, ANN, NOTE

# template Model row -> EXENS row key (per sheet where the meaning differs)
MAP_COMMON = {158: 'is_rev', 166: 'is_op', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 221: 'o_adj', 229: 'e_adjni', 231: 'e_eps',
              238: 'gm_lfl', 245: 'o_adj_m', 247: 'gm_op_m', 280: 'fcf', 282: 'fcf_m', 290: 'bb_px', 291: 'bb_cash', 292: 'bb_sh',
              331: 'v_oth', 411: 'ra_roic', 422: 'rn_ronta', 433: 'v_px', 434: 'v_sh', 408: 'ra_ic', 182: 'd_dna_t', 219: 'r_ebit',
              260: 'cf_wc', 262: 'cf_capex', 263: 'cf_lease'}
MAP_SHEET = {'Bull-Base-Bear': {428: 'lv_nd'}, 'DCF': {428: 'v_ndx'}}
CMAP = {'BV': ANN[2025].c, 'CA': ANN[2026].c, 'CB': ANN[2027].c, 'CC': ANN[2028].c, 'CD': ANN[2029].c, 'CE': ANN[2030].c, 'CF': NOTE}
REF = re.compile(r"Model!(\$?)([A-Z]{1,3})(\$?)(\d+)")
HIST_ANN = [ANN[y].c for y in range(2021, 2026)]

def remap(f, sheet):
    mp = dict(MAP_COMMON); mp.update(MAP_SHEET.get(sheet, {}))
    def rep(m):
        c, r = m.group(2), int(m.group(4))
        if c == 'CF' and r == 2: return f'Model!{m.group(1)}{NOTE}{m.group(3)}2'
        return f'Model!{m.group(1)}{CMAP.get(c, c)}{m.group(3)}{R[mp[r]] if r in mp else r}'
    return REF.sub(rep, f)

def M(key, y): return f'Model!{ANN[y].c}{R[key]}'

BBB_LAB = {9: 'Revenue (€m)', 10: '   Revenue y/y % (reported)', 11: '   Revenue y/y % (like-for-like, model)',
           12: 'Adjusted EBITDA (company definition)', 13: '   Adjusted EBITDA margin %', 15: 'Operating Profit (IFRS)',
           16: '   Operating profit y/y %', 17: '   Operating margin %', 19: 'Net Profit excl. PPA & Impairment (continuing)',
           21: 'Diluted shares (m)', 23: 'Adjusted EPS — net profit excl. PPA per diluted share (€)', 26: 'P / E (x) — assumed (adjusted EPS)',
           27: 'Price Target (€)', 35: 'Adjusted EBIT (company definition)', 36: '   Adjusted EBIT margin %',
           38: 'Net Debt incl. leases (company definition)', 39: '   Net Debt / Adjusted EBITDA (x)', 40: '   Share repurchases (€m)',
           41: '   Implied avg repurchase price (€)', 42: '   Shares repurchased (m)', 47: 'Implied Market Cap (€m)', 48: '(+) Net Debt incl. leases & other debt-like items',
           49: 'Implied Enterprise Value (€m)'}

TEXT = {
    'Bull-Base-Bear': {
        'B2': 'Exosens (EXENS) — Bull / Base / Bear Case P&L Summary',
        'B3': ('Adjusted figures (company definitions: Adjusted EBITDA / EBIT excl. share-based payments, one-offs and PPA amortisation; net profit excl. PPA amortisation & impairment) · € millions · '
               'Live panel linked to Model — toggle scenario via Model!U2. Bull and Bear panels are value snapshots generated from the Model with the switch set to each case. '
               'Price target / IRR in €.'),
        'J2': 'Share price (€):',
        'F26': 24, 'G26': 24, 'H26': 24, 'R26': 30, 'S26': 30, 'T26': 30, 'AD26': 16, 'AE26': 16, 'AF26': 16,
        'B7': '(€m, except EPS and shares)', 'N7': '(€m, except EPS and shares)', 'Z7': '(€m, except EPS and shares)',
        'B33': '   FCF / share (€)', 'N33': '   FCF / share (€)', 'Z33': '   FCF / share (€)',
    },
    'DCF': {
        'B2': 'DCF VALUATION — EXOSENS SAS (EXENS)',
        'B5': 'Risk-free rate (French 10Y OAT)', 'B16': '2. UNLEVERED FREE CASH FLOW BUILD (€m)',
        'B33': 'IMPLIED ROIC — invested capital roll-forward (€m)', 'B58': '4. SENSITIVITY: IMPLIED PRICE (€) — WACC × Terminal Growth',
        'C5': 0.034, 'D5': 'French 10Y OAT ~3.3–3.5% (Oct-2026); euro cash flows',
        'C6': 0.055, 'D6': 'Euro-area equity risk premium ~5–6% (Damodaran mature-market ERP + France)',
        'C7': 1.2, 'D7': 'Defense / photonics mid-caps (Theon, Hensoldt, Exail, Lumibird) ~1.0–1.4; small-cap, HLD-controlled float (~40%), defense-cycle exposure',
        'C9': 0.035, 'D9': 'Term Loan B at 3M Euribor + 1.15% (~3.3%); EIB fixed ~4.1%',
        'C10': 0.26, 'D10': 'Model 2027E+ effective tax rate (French statutory 25% + foreign mix; loss carry-forwards exhausted in 2026)',
        'C12': 0.15, 'D12': 'Net debt ~€200m vs ~€2.9bn market cap (6%); company tolerates ~2x leverage for M&A → 15% target D/V',
        'B18': 'Adj. EBIT less share-based payments and one-off costs (= operating profit + PPA amortisation + impairment)',
        'B21': 'plus D&A excl. PPA amortisation (incl. right-of-use depreciation)',
        'B22': '− Capex incl. capitalised R&D, acquisitions (M&A lever) and lease principal payments',
        'B26': 'Fade-period growth (2031E–35E; 9% → 4% linear)', 'I26': 0.09, 'M26': 0.04, 'C27': 0.025,
        'D32': ("Exosens' Adjusted EBITDA / EBIT exclude share-based payments (~1.3% of revenue) and one-off acquisition costs, which are deducted here (row 18 = Adjusted EBIT − SBC − one-offs "
                '= operating profit + PPA amortisation + brand impairment). PPA amortisation (~€16m p.a.) is not added back as a perpetual shield: it is excluded from EBIT and from the D&A add-back. '
                'IFRS 16: D&A includes right-of-use depreciation, so lease principal payments are deducted with capex in row 22 and lease liabilities are excluded from net debt in the equity bridge. '
                'Capex includes capitalised R&D (~3% of revenue) and the ~9% capacity programme to 2027, normalising to ~5%; acquisition spend (M&A lever) is deducted in the explicit years. Euro cash flows at constant currency.'),
        'D43': 'Opening IC = Model 2025A equity + net debt excl. leases (TLB, other loans − cash), rolled forward with capex + M&A + lease payments − D&A + ΔWC.',
        'B48': 'Less: Net debt excl. leases + other debt-like items (Model 2026E YE)',
        'D48': 'Net debt at 2026E year end (TLB €250m, RCF / EIB draws, other loans − cash), excl. lease liabilities (lease payments are in UFCF); plus NVLS put and contingent consideration.',
        'B50': 'Diluted shares (m, Model 2026E)', 'B51': 'Implied share price (€)', 'B52': 'Current share price (€; Euronext close 30-Oct-2026)',
        'B55': 'Max entry price for target IRR (€)',
        'B70': ('To solve for the market-implied path: Data ▸ What-If Analysis ▸ Goal Seek — set C51 to the current price (C52) by changing C27 (terminal growth), '
                'the fade-period growth inputs (I26:M26) or the Model scenario levers (segment like-for-like growth, adjusted gross margins, Adjusted EBITDA margin, M&A spend).'),
        'D76': 'Rationale (Exosens characteristics)',
        'C78': 0.14, 'D78': 'Model Adjusted EBIT CAGR 2026–30E: low-double-digit organic growth (night-vision capacity +40% by 2027, defense imaging, SMR nuclear) plus bolt-on M&A and a slowly rising Adjusted EBITDA margin → ~14% NOPAT growth',
        'C79': 0.30, 'D79': 'Incremental returns: ~33% Adjusted EBITDA margin, capex normalising to ~5% + 3% capitalised R&D, modest working capital → RONTA well above 50%; goodwill-heavy IC keeps ROIC near 15–20%',
        'C80': 10, 'D80': 'ITAR-free image intensifier tube leadership (OCCAR, NATO programmes to 2029–2032), multi-spectral imaging portfolio and SMR instrumentation; defense-cycle, customer-concentration (Theon ~38% of H1-26 revenue) and technology-substitution (digital night vision) risks cap the advantage period',
        'B91': '2028E Adj. EBIT less share-based payments and one-offs', 'B96': 'Less: YE2027 net debt excl. leases + other debt-like items (Model)',
        'B98': 'Diluted shares 2028E (m, Model)', 'B99': 'Implied share price 2028 (€)', 'B101': 'Current share price (€)',
        'B108': 'EXENS market-implied EV/NOPAT (on 2028E NOPAT)', 'C90': '€m', 'C104': '€m',
    },
    'Charts': {
        'B2': 'Exosens — Operating Performance (2021–2025) and Model Forecast (2026E–2030E)',
        'B3': ('€m · Linked to Model. Bars = like-for-like growth vs scope & currency effect (like-for-like published from 2023; earlier years: reported growth shown as like-for-like). '
               'Adjusted EBITDA as reconciled by Exosens in each period (registration document for FY2021–22; FY2024 restated for the Microwave Amplification disposal). ROIC / RONTA on Adjusted EBIT less SBC and one-offs.'),
        'B8': 'Like-for-like growth %', 'B9': 'Scope & currency effect %', 'B12': 'Adjusted EBITDA', 'B13': 'Operating Profit (IFRS)',
        'B14': 'Adj. EBITDA Margin %', 'B15': 'IFRS Op. Margin %',
    },
}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Revenue Growth: Like-for-Like vs. Scope &amp; Currency, y/y %',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted EBITDA &amp; Operating Profit (€m)',
}
YEARS = list(range(2021, 2031))
LASTCH = L(2 + len(YEARS))          # L

def build_charts(ws):
    for i, y in enumerate(YEARS):
        c = L(3 + i); mc = ANN[y].c
        ws[f'{c}7'] = y if y <= 2025 else f'{y}E'
        ws[f'{c}8'] = f'=IFERROR(Model!{mc}{R["gm_lfl"]}+0,IFERROR(Model!{mc}{R["gm_rev"]}+0,0))'
        ws[f'{c}9'] = f'=IFERROR(Model!{mc}{R["g_scope"]}+0,0)'
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
    """LT Hist Avg / Min / Max (J:L, V:X, AH:AJ) on EXENS annual history 2021–2025."""
    for r, key in ((13, 'r_adj_m'), (17, 'gm_op_m'), (32, 'fcf_m'), (36, 'o_adj_m'), (44, 'ra_roic'), (45, 'rn_ronta')):
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
                if c.comment is not None: c.comment = None
        for addr, t in TEXT.get(name, {}).items():
            ws[addr] = t
    b = wb['Bull-Base-Bear']
    for r, t in BBB_LAB.items():
        for col in ('B', 'N', 'Z'): b[f'{col}{r}'] = t
    lt_hist(b)
    from fw import comment as _comment
    _comment(b['B26'], ('Assumed P/E on net profit from continuing operations excl. PPA amortisation & impairment (company measure) per diluted share. '
                        'Base 24x ≈ the current multiple on 2026E (€56.90 ÷ €2.27 = 25x); European defense-electronics / photonics peers (Hensoldt, Theon, Exail, Lumibird) '
                        'have traded at ~18–30x forward earnings in 2025–26 (assumption, not company data). Bull 30x (sustained mid-teens organic growth, capacity '
                        'ramp, US BiNOD), Bear 16x (defense-cycle de-rating, Theon concentration ~38% of H1-26 revenue).'))
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
        d[f'{col}18'] = f'={M("r_ebit", y)}-{M("d_sbc", y)}-{M("d_nonrec", y)}'
        d[f'{col}21'] = f'={M("d_dna", y)}'
        d[f'{col}22'] = f'={M("cf_capex", y)}+{M("cf_acq", y)}+{M("cf_lease", y)}'
    # fade years grow capex + leases only: acquisition spend is deducted in the explicit years (2027E–30E) only (playbook 5.7 / Phase 7)
    d['I22'] = f'=(H22-{M("cf_acq", 2030)})*(1+I$26)'
    # FY2026 ends ~8 weeks after the valuation date and its cash flow is already in the YE2026 net debt: show 2026E, exclude it from the sums
    d['C45'] = '=SUM(E31:M31)'
    d['B28'] = ('Note: 2026E UFCF is shown for reference but excluded from the PV sum and the sensitivity grid — FY2026 ends ~8 weeks after the valuation date '
                'and its cash flow is already in the YE2026 net debt deducted below.')
    for row in d.iter_rows(min_row=62, max_row=66):
        for c in row:
            v = c.value
            if hasattr(v, 'text') and v.text:
                v.text = v.text.replace('$D$24:$M$24', '$E$24:$M$24').replace('$D$29:$M$29', '$E$29:$M$29')
            elif isinstance(v, str) and v.startswith('='):
                c.value = v.replace('$D$24:$M$24', '$E$24:$M$24').replace('$D$29:$M$29', '$E$29:$M$29')
    d['D34'] = f'={M("ra_eq", 2025)}+{M("v_ndx", 2025)}'
    d['C91'] = f'={M("r_ebit", 2028)}-{M("d_sbc", 2028)}-{M("d_nonrec", 2028)}'

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
    re-ranged to Charts!C:L (2021–2030E) and with cached values removed so Excel redraws from the EXENS cells."""
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
            elif re.match(r'xl/comments\d*\.xml$', item.filename):
                # LibreOffice recalculation resets comment authors; restore the build's author name
                data = re.sub(rb'<authors>.*?</authors>', b'<authors><author>EXENS model</author></authors>', data, flags=re.S)
            zout.writestr(item, data)
    shutil.move(tmp, path)
