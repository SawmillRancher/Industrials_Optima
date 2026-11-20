"""Rewire the Bull-Base-Bear, DCF and Charts tabs of the MLM template (current layout: DCF with live valuation date, fade period,
implied ROIC, target-IRR entry price, reverse DCF and Mauboussin EV/NOPAT; Bull-Base-Bear with buyback rows) to the UNP Model rows;
keep the template chart XML. Columns are unchanged (calendar years 2006-2030E match the template), so only rows are remapped."""
import re, zipfile, shutil
from openpyxl.utils import get_column_letter as L
from fw import R, TEMPLATE, ANN, NOTE, MAN

# template Model row -> UNP row key
MAP = {158: 'is_rev', 164: 'r_cash', 166: 'is_oi', 182: 'is_dda', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 219: 'r_ebit', 221: 'r_adj',
       229: 'e_adjni', 231: 'e_eps', 238: 'gm_cars', 245: 'gm_ebitda_m', 247: 'gm_op_m', 260: 'cf_oth', 262: 'cf_capex', 263: 'cf_acq',
       280: 'fcf', 282: 'fcf_m', 290: 'bb_px', 291: 'bb_cash', 292: 'bb_sh', 331: 'v_nci', 408: 'ra_ic', 411: 'ra_roic', 422: 'rn_ronta',
       428: 'lv_nd', 433: 'v_px', 434: 'v_sh', 12: 'gm_cars', 30: 'gm_cars', 14: 'gm_arpc', 31: 'gm_arpc', 353: 'nd_stock', 355: 'n_tog'}
REF = re.compile(r"Model!(\$?)([A-Z]{1,3})(\$?)(\d+)")
HIST = [ANN[y].c for y in range(2006, 2026)]

def remap(f):
    def rep(m):
        c, r = m.group(2), int(m.group(4))
        r2 = R[MAP[r]] if r in MAP else r
        if c == 'CF' and r == 2: r2 = 2
        return f'Model!{m.group(1)}{c}{m.group(3)}{r2}'
    return REF.sub(rep, f)

def hist_stat(f):
    m = re.match(r'=IFERROR\((AVERAGE|MIN|MAX)\(Model!C(\d+),', f)
    if not m: return None
    fn, r = m.group(1), int(m.group(2))
    rr = R[MAP[r]]
    return f'=IFERROR({fn}({",".join(f"Model!{c}{rr}" for c in HIST)}),"")'

PX = MAN['price']['px']
TEXT = {
    'Bull-Base-Bear': {
        'B2': 'Union Pacific Corporation (UNP) — Bull / Base / Bear Case P&L Summary',
        'B3': ('Adjusted figures (company items affecting comparability excluded; model adjusted EBITDA = adjusted operating income + depreciation) · USD millions · Live panel linked to Model — '
               'toggle scenario via Model!CF2. Bull and Bear panels are value snapshots generated from the Model with the switch set to each case. 2026E = Q1–Q3 actual + Q4 calibrated to the '
               'FY26 guidance (reported EPS growth high-single digit). 2027E+ include Norfolk Southern from the assumed 1-Jul-2027 closing (toggle in the Model).'),
        'G26': 21, 'H26': 21, 'S26': 23, 'T26': 23, 'AD26': 18, 'AE26': 18, 'AF26': 18,
    },
    'DCF': {
        'B2': 'DCF VALUATION — UNION PACIFIC CORPORATION (UNP)',
        'C5': 0.0425, 'D5': 'Assumption (~US 10Y Treasury yield, Nov-2026; government rate sources not reachable from the build environment); update to market',
        'D6': 'Assumption: US implied ERP ~4.5–5.5%',
        'C7': 0.95, 'D7': 'Assumption: North American Class I railroad peers (CSX, NSC, CPKC, CNI) ~0.9–1.1; regulated-ish duopoly network, cyclical volumes (industrial production, coal, intermodal)',
        'C9': 0.05, 'D9': 'Pro forma acquisition-debt assumption 5% (Form 424B3 Note 6[d]); UNP 2025 interest $1,309m on $32.1bn average debt = 4.1%; A-/A3 rated',
        'C10': 0.235, 'D10': 'Model 2027E+ effective tax rate (9M-26 23.2%; federal 21% + state)',
        'C12': 0.15, 'D12': 'Net debt ~$29bn at 30-Sep-2026 vs ~$179bn market cap ($300.62 × ~595m shares) ≈ 14%; rises toward ~20% with the Norfolk Southern acquisition debt',
        'D15': 'Periods = (Dec-31-Year − today) / 365.25; cash flows assumed at year-end. 2026E UFCF is excluded (weight 0) because net debt is taken at YE2026E.',
        'B18': 'Adj. EBIT less acquisition-related costs and costs to achieve synergies',
        'B21': 'plus depreciation (Union Pacific reports no separate amortization)',
        'B22': '− Capital investments and the Norfolk Southern cash consideration, net of cash acquired (2027E)',
        'B23': '− Δ Working capital (other – net operating items incl. share-based compensation)',
        'B26': 'Fade-period growth (2031E–35E; 5.0% → 3.5% linear)', 'I26': 0.05, 'M26': 0.035, 'C27': 0.03,
        'D32': ("Adjusted EBIT = adjusted operating income (company items affecting comparability excluded; no acquired-intangible amortization). Acquisition-related costs and the costs to achieve "
                "synergies are cash items adjusted out and are deducted inside row 18. Row 22 includes the Norfolk Southern cash consideration in 2027E (net of NSC cash acquired); the stock "
                "consideration is deducted in the equity bridge (row 48) at its 2027E present value so that the 2026E share count can be used. Fuel price held at the 9M-26 average."),
        'D43': 'Opening IC = Model 2025A book IC (equity + net debt), rolled forward with capex + cash acquisition − depreciation + ΔWC; the 2027E opening IC adds the NSC stock consideration.',
        'B48': 'Less: Net debt (YE2026E) + PV of the Norfolk Southern stock consideration (2027E)',
        'D48': 'UNP: no noncontrolling interests. Net debt at YE2026E (≈ valuation date) so that 2027E+ cash flows are not double counted; the ~224.9m UNP shares issued to NSC holders are valued at the closing price and deducted here (toggle-weighted).',
        'B50': 'Diluted shares (m, Model 2026E period end; excludes shares to be issued to NSC holders)',
        'D76': 'Rationale (Union Pacific characteristics)',
        'C78': 0.08, 'D78': 'Model adjusted EBIT CAGR 2026–30E: low-single-digit carload growth, pricing above inflation, workforce productivity and the Norfolk Southern synergies → ~8% NOPAT growth',
        'C79': 0.15, 'D79': 'Company-published ROIC 16.3% (2025); a transcontinental network earns high returns on incremental capital, diluted near term by the ~$69bn NSC consideration (goodwill) and $2bn capex to achieve synergies',
        'C80': 15, 'D80': 'Irreplaceable right-of-way across the western two-thirds of the US (23 states; 50,000 route miles combined with NSC), rail duopoly economics and truck-to-rail conversion; regulatory (STB) oversight caps pricing',
        'B90': 'VALUATION  —  Applied to 2028E NOPAT',
        'B91': '2028E Adj. EBIT less acquisition-related costs and costs to achieve synergies',
        'B93': '2028E NOPAT',
        'B95': 'Implied Enterprise Value (2028E basis)',
        'B96': 'Less: YE2027 net debt (Model; post-closing, incl. acquisition and NSC debt)',
        'B98': 'Diluted shares 2028E (m, Model; incl. shares issued to NSC holders)',
        'B99': 'Implied share price 2028 ($)',
        'B106': 'Plus: YE2026 net debt + PV of the NSC stock consideration',
        'B108': 'UNP market-implied EV/NOPAT (on 2028E NOPAT)',
    },
    'Charts': {
        'B2': 'Union Pacific Corporation — Historical Operating Performance (2006–2025)',
        'B3': ('All historicals · USDm · Linked to Model. Volume / price = total revenue carloads and average revenue per car (incl. fuel surcharge) y/y. Adjusted EBITDA = model definition '
               '(adjusted operating income + depreciation; company items affecting comparability excluded). ROIC / RONTA on adjusted operating income.'),
        'B8': 'Revenue carloads y/y %', 'B9': 'Average revenue per car y/y %', 'B12': 'Adjusted EBITDA', 'B13': 'Operating income (GAAP)',
        'B14': 'Adj. EBITDA Margin %', 'B15': 'GAAP Op. Margin %',
    },
}
BBB_ROWS = {9: 'Operating revenues', 10: '   Operating revenues y/y %', 11: '   Revenue carloads y/y %', 12: 'Adjusted EBITDA (model: adjusted operating income + depreciation)',
            15: 'Operating income (GAAP)', 16: '   Operating income y/y %', 17: '   Operating margin (GAAP) %', 19: 'Adjusted net income',
            35: 'Adjusted EBITDA (leverage basis)', 36: '   Adjusted EBITDA % of revenues'}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Freight Revenue Drivers: Revenue Carloads vs. Average Revenue per Car, y/y %',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted EBITDA &amp; Operating Income (USDm)',
}

def do_all(wb):
    for name in ('Bull-Base-Bear', 'DCF', 'Charts'):
        ws = wb[name]
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and 'Model!' in c.value:
                    h = hist_stat(c.value) if name == 'Bull-Base-Bear' else None
                    c.value = h or remap(c.value)
        for addr, t in TEXT.get(name, {}).items():
            ws[addr] = t
    b = wb['Bull-Base-Bear']
    for r, t in BBB_ROWS.items():
        for c in ('B', 'N', 'Z'): b[f'{c}{r}'] = t
    from openpyxl.comments import Comment
    cm = Comment(f'P/E on adjusted EPS (company items affecting comparability excluded). UNP at ${PX:.2f} trades at ~23x 2026E adjusted EPS (~$13) and ~21x 2027E. Exit multiples are assumptions: '
                 'Base 21x, Bull 23x, Bear 18x applied to 2029E–30E (2028E–30E for Bear), in line with the 2015–25 range of ~17–25x for the US Class I railroads.', 'UNP model')
    cm.width, cm.height = 420, 120; b['N26'].comment = cm
    cm2 = Comment(f'Snapshot (values) of Model rows {R["bb_cash"]}, {R["bb_px"]} and {R["bb_sh"]} (Share Buyback Schedule) with Model!{NOTE}2 = Bull / Bear. '
                  'Base panel (D40:H42) is live-linked.', 'UNP model')
    cm2.width, cm2.height = 420, 90; b['P40'].comment = cm2
    b['J2'] = 'Share price ($):'
    for c in ('B', 'N', 'Z'):
        if b[f'{c}40'].value: b[f'{c}40'] = '   Share repurchases ($m; 2026E = Q4; paused for the NSC merger)'
        b[f'{c}48'] = '(+) Net Debt & NCI (none)'
    d = wb['DCF']
    a26, a27 = ANN[2026].c, ANN[2027].c
    d['D22'] = f'=Model!{a26}{R["cf_capex"]}'
    d['E22'] = f'=Model!{a27}{R["cf_capex"]}+Model!{a27}{R["cf_acq"]}'
    for col, y in (('F', 2028), ('G', 2029), ('H', 2030)):
        d[f'{col}22'] = f'=Model!{ANN[y].c}{R["cf_capex"]}+Model!{ANN[y].c}{R["cf_acq"]}'
    d['D31'] = '=0*D24*D30'
    d['E34'] = f'=D38+Model!{a27}{R["nd_stock"]}*Model!{a27}{R["n_tog"]}'
    d['D34'] = f'=Model!{ANN[2025].c}{R["ra_ic"]}'
    d['C48'] = f'=Model!{a26}{R["lv_nd"]}+Model!{a26}{R["v_nci"]}+Model!{a27}{R["nd_stock"]}*Model!{a27}{R["n_tog"]}*E30'
    d['C50'] = f'=Model!{a26}{R["v_sh"]}'
    d['C52'] = f'=Model!{a26}{R["v_px"]}'
    d['C96'] = f'=Model!{a27}{R["lv_nd"]}+Model!{a27}{R["v_nci"]}'
    d['C98'] = f'=Model!{ANN[2028].c}{R["v_sh"]}'
    d['C106'] = '=C48'
    build_charts(wb['Charts'])

def build_charts(ws):
    for i, y in enumerate(range(2006, 2026)):
        c = L(3 + i); mc = ANN[y].c
        ws[f'{c}8'] = f'=IFERROR(Model!{mc}{R["gm_cars"]}+0,0)'
        ws[f'{c}9'] = f'=IFERROR(Model!{mc}{R["gm_arpc"]}+0,0)'
        ws[f'{c}12'] = f'=Model!{mc}{R["r_adj"]}'
        ws[f'{c}13'] = f'=Model!{mc}{R["is_oi"]}'
        ws[f'{c}14'] = f'=Model!{mc}{R["gm_ebitda_m"]}'
        ws[f'{c}15'] = f'=Model!{mc}{R["gm_op_m"]}'
        ws[f'{c}18'] = f'=IFERROR(Model!{mc}{R["ra_roic"]}+0,NA())'
        ws[f'{c}19'] = f'=IFERROR(Model!{mc}{R["rn_ronta"]}+0,NA())'
        ws[f'{c}20'] = f'=IFERROR(Model!{mc}{R["gm_ebitda_m"]}+0,NA())'
        ws[f'{c}21'] = f'=IFERROR(Model!{mc}{R["fcf_m"]}+0,NA())'

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
    (Charts!C:V = 2006-2025) and cached values removed so Excel redraws from the UNP cells."""
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
