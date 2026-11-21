"""Rewire the Bull-Base-Bear, DCF and Charts tabs of the MLM template (current layout: DCF with live valuation date, fade period,
implied ROIC, target-IRR entry price, reverse DCF and Mauboussin EV/NOPAT; Bull-Base-Bear with buyback rows) to the NSC Model rows /
columns; keep the template chart XML. The template's DCF_old tab is not carried.

Column mapping: the template's 2025A base column becomes NSC 2026E (Q1-Q3 actual, Q4 estimated; the year ends six weeks after the
valuation date) and the template's 2026E-2030E become NSC 2027E-2031E, so the DCF's explicit years start in 2027E and net debt is
taken at 31-Dec-2026E."""
import re, zipfile, shutil
from openpyxl.utils import get_column_letter as L
from fw import R, TEMPLATE, ANN, NOTE

# template Model row -> NSC row key
MAP = {158: 'is_rev', 164: 'r_cash', 166: 'is_oi', 182: 'is_dda', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 219: 'r_ebit', 221: 'r_adj',
       229: 'e_adjni', 231: 'e_eps', 238: 'gm_units', 245: 'gm_ebitda_m', 247: 'gm_op_m', 260: 'cf_wc', 262: 'cf_capex', 263: 'cf_acq',
       280: 'fcf', 282: 'fcf_m', 290: 'bb_px', 291: 'bb_cash', 292: 'bb_sh', 331: 'v_nci', 408: 'ra_ic', 411: 'ra_roic', 422: 'rn_ronta',
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
    """LT historical AVERAGE / MIN / MAX over the template's annual columns -> NSC 2006-2025 annual columns."""
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
        'B2': 'Norfolk Southern Corporation (NSC) — Bull / Base / Bear Case P&L Summary',
        'B3': ('Adjusted figures (company definition where published: adjusted income from railway operations / operating ratio / diluted EPS; adjusted EBITDA = model) · USD millions · calendar years · '
               'Live panel linked to Model — toggle scenario via Model!CG2. Bull and Bear panels are value snapshots generated from the Model with the switch set to each case. 2026E = Q1–Q3 actual + Q4 '
               'anchored on 9M-26 trends and OR seasonality (no company guidance on EDGAR). Standalone forecast: the pending Union Pacific acquisition (1.0 UNP share + $88.82 cash) is valued in the Model merger block.'),
        'G26': 18, 'H26': 18, 'S26': 20, 'T26': 20, 'AD26': 15, 'AE26': 15, 'AF26': 15,
    },
    'DCF': {
        'B2': 'DCF VALUATION — NORFOLK SOUTHERN CORPORATION (NSC) — standalone',
        'C5': 0.0425, 'D5': 'Assumption (~US 10Y Treasury yield, Nov-2026; government rate sources not reachable from the build environment); update to market',
        'D6': 'Assumption: US implied ERP ~4.5–5.5%',
        'C7': 1.0, 'D7': 'Assumption: Class I railroad peers (UNP, CSX, CPKC, CNI) ~0.9–1.1; regulated-oligopoly network with cyclical volumes and fuel pass-through',
        'C9': 0.051, 'D9': 'May-2025 $400m senior notes at 5.10% (FY2025 10-K Note 11); weighted-average coupons 4.19–5.22%; investment grade',
        'C10': 0.235, 'D10': 'Model 2027E+ effective tax rate (9M-26 23.3%)',
        'C12': 0.18, 'D12': 'Net debt ~$15.6bn at YE2026E vs ~$75bn market cap ($332.09 × ~225m diluted shares); 2.7x adjusted EBITDA; debt-to-total-capitalization 49.8% (book)',
        'D15': 'Periods = (Dec-31-Year − today) / 365.25; cash flows assumed at year-end; 2026E (ends 31-Dec-2026, six weeks after the valuation date) is the base year',
        'B18': 'Adj. income from railway operations less cash special items (merger, restructuring, incident)',
        'B21': 'plus depreciation (NSC has no acquired-intangible amortization)',
        'B22': '− Property additions (capex); no acquisitions assumed',
        'B26': 'Fade-period growth (2032E–36E; 5.0% → 3.0% linear)', 'I26': 0.05, 'M26': 0.03, 'C27': 0.03,
        'D32': ("NSC's adjusted income from railway operations (company definition: GAAP OI excluding merger-related expenses, restructuring and other charges, the Eastern Ohio incident and the 2020 impairments) "
                'is used as adjusted EBIT; share-based compensation stays expensed. Row 18 deducts the cash special items the company excludes (merger costs, restructuring, incident costs net of recoveries); '
                'the non-cash 2020 asset-disposal loss, the 2024 line-sale gains and the Q3-20 impairment are not cash items. Row 22 is property additions only (no acquisitions). The fade period and terminal '
                'value assume no new M&A. The standalone DCF ignores the pending Union Pacific acquisition; the merger consideration (cash + UNP stock) and the $2.5bn termination fee are valued in the Model merger block.'),
        'D43': 'Opening IC = Model 2026E book IC (equity + net debt at 31-Dec-2026E), rolled forward with capex − depreciation + ΔWC.',
        'B48': 'Less: Net debt + NCI (Model 2026E year end, 31-Dec-2026)',
        'D48': 'NSC: no noncontrolling interests; net debt at the base-year end (≈ valuation date) so that 2027E+ cash flows are not double counted. Finance leases ($18m) are inside debt; operating leases are not treated as debt.',
        'B50': 'Diluted shares (m, Model 2026E period end)',
        'D76': 'Rationale (Norfolk Southern characteristics)',
        'C78': 0.08, 'D78': 'Model adjusted EBIT CAGR 2026–31E: ~5% revenue growth (volume + pricing) with the adjusted operating ratio improving from ~66% to 60% → ~8% NOPAT growth',
        'C79': 0.12, 'D79': 'Returns on incremental track, terminal and locomotive investment are modest (ROIC ~10–11% on book IC); pricing power above rail inflation and productivity (operating-ratio improvement) lift returns',
        'C80': 15, 'D80': 'Irreplaceable 22-state eastern network (duopoly with CSX east of the Mississippi), high barriers to entry and long-lived assets; cyclical volumes, coal secular decline and regulatory risk (STB) bound the advantage',
        'B90': 'VALUATION  —  Applied to 2029E NOPAT',
        'B91': '2029E Adj. income from railway operations less cash special items',
        'B93': '2029E NOPAT',
        'B95': 'Implied Enterprise Value (2029E basis)',
        'B96': 'Less: YE2028E net debt + NCI (Model)',
        'B98': 'Diluted shares 2029E (m, Model)',
        'B99': 'Implied share price 2029 ($)',
        'B106': 'Plus: YE2026E net debt + NCI',
        'B108': 'NSC market-implied EV/NOPAT (on 2029E NOPAT)',
    },
    'Charts': {
        'B2': 'Norfolk Southern — Operating Performance (2012–2025) and Model Forecast (2026E–2031E)',
        'B3': ('USDm · calendar years · Linked to Model. Volume / price = total units (carloads) and average revenue per unit y/y (revenue per unit includes fuel surcharges). Adjusted EBITDA = model definition '
               '(adjusted income from railway operations + depreciation); income from railway operations = GAAP. ROIC / RONTA on adjusted income from railway operations.'),
        'B8': 'Total units (volume) y/y %', 'B9': 'Revenue per unit (price, mix, fuel) y/y %', 'B12': 'Adjusted EBITDA', 'B13': 'Income from railway operations (GAAP)',
        'B14': 'Adj. EBITDA Margin %', 'B15': 'GAAP Op. Margin %',
    },
}
BBB_ROWS = {9: 'Railway operating revenues', 10: '   Revenues y/y %', 11: '   Total units (volume) y/y %', 12: 'Adjusted EBITDA (model: adjusted OI + depreciation)',
            15: 'Income from railway operations (GAAP)', 16: '   Income from railway operations y/y %', 17: '   Operating margin (GAAP) %', 19: 'Adjusted Net Income',
            35: 'Adjusted EBITDA (leverage basis)', 36: '   Adjusted EBITDA % of revenues'}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Revenue Drivers: Units (Volume) vs. Revenue per Unit, y/y %',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted EBITDA &amp; Income from Railway Operations (USDm)',
}

def build_charts(ws):
    for i, y in enumerate(range(2012, 2032)):
        c = L(3 + i); mc = ANN[y].c
        ws[f'{c}7'] = y if y <= 2025 else f'{y}E'
        ws[f'{c}8'] = f'=IFERROR(Model!{mc}{R["g_units_g"]}+0,0)'
        ws[f'{c}9'] = f'=IFERROR(Model!{mc}{R["g_rpu_g"]}+0,0)'
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
    cm = Comment('P/E on adjusted EPS (company definition). NSC at $332.09 trades at ~27x 2025 adjusted EPS ($12.49) and ~25x 2026E; Class I railroads traded at ~15–22x over 2015–24 before the '
                 'Union Pacific offer (1.0 UNP share + $88.82 cash) re-rated the stock. Standalone exit multiples are assumptions: Base 18x, Bull 20x, Bear 15x applied to 2030E–31E adjusted EPS (2029E–31E for Bear).', 'NSC model')
    cm.width, cm.height = 420, 130; b['N26'].comment = cm
    cm2 = Comment(f'Snapshot (values) of Model rows {R["bb_cash"]}, {R["bb_px"]} and {R["bb_sh"]} (Share Buyback Schedule) with Model!{NOTE}2 = Bull / Bear. '
                  'Base panel (D40:H42) is live-linked. Buybacks are nil in 2026E–2027E (suspended under the Merger Agreement).', 'NSC model')
    cm2.width, cm2.height = 420, 90; b['P40'].comment = cm2
    b['J2'] = 'Share price ($):'
    for c in ('B', 'N', 'Z'): b[f'{c}29'] = 'IRR (to 31-Dec of Y-1)'
    for c in ('B', 'N', 'Z'):
        if b[f'{c}40'].value: b[f'{c}40'] = '   Share repurchases ($m; 2026E–27E nil: merger pending)'
    d = wb['DCF']
    for i, col in enumerate('DEFGHIJKLM'):
        d[f'{col}17'] = f'{2027 + i}E'
    a26, a27 = ANN[2026].c, ANN[2027].c
    d['D22'] = f'=Model!{a27}{R["cf_capex"]}+Model!{a27}{R["cf_acq"]}'
    d['D34'] = f'=Model!{a26}{R["ra_ic"]}'
    d['C48'] = f'=Model!{a26}{R["lv_nd"]}+Model!{a26}{R["v_nci"]}'
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
    (Charts!C:V = 2012-2031E) and cached values removed so Excel redraws from the NSC cells."""
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
