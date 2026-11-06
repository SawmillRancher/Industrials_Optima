"""Rewire the Bull-Base-Bear, DCF and Charts tabs of the MLM template (current layout: DCF with live valuation date, fade period,
implied ROIC, target-IRR entry price, reverse DCF and Mauboussin EV/NOPAT; Bull-Base-Bear with buyback rows) to the JHX Model rows /
columns; keep the template chart XML. The template's DCF_old tab is not carried."""
import re, zipfile, shutil
from openpyxl.utils import get_column_letter as L
from fw import R, TEMPLATE, ANN, NOTE

# template Model row -> JHX row key
MAP = {158: 'is_rev', 164: 'r_cash', 166: 'is_op', 182: 'd_dep', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 219: 'r_ebita', 221: 'r_adj',
       229: 'e_adjni', 231: 'e_eps', 238: 'gm_st', 245: 'gm_ebitda_m', 247: 'gm_op_m', 260: 'cf_wc', 262: 'cf_capex', 263: 'cf_acq',
       280: 'fcf', 282: 'fcf_m', 290: 'bb_px', 291: 'bb_cash', 292: 'bb_sh', 331: 'v_asb', 408: 'ra_ic', 411: 'ra_roic', 422: 'rn_ronta',
       428: 'lv_nd', 433: 'v_px', 434: 'v_sh', 353: 'v_asb', 355: 'v_asb'}
# template Model column -> JHX column (template 2025A = JHX FY2026A; template 2026E-2030E = JHX FY2027E-FY2031E)
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
    """LT historical AVERAGE / MIN / MAX over the template's annual columns -> JHX FY2006-FY2026 annual columns."""
    m = re.match(r'=IFERROR\((AVERAGE|MIN|MAX)\(Model!C(\d+),', f)
    if not m: return None
    fn, r = m.group(1), int(m.group(2))
    rr = R[MAP[r]]
    return f'=IFERROR({fn}({",".join(f"Model!{c}{rr}" for c in HIST)}),"")'

def fy_dates(f):
    f = re.sub(r'DATE\((\d{4}),12,31\)', lambda m: f'DATE({int(m.group(1)) + 1},3,31)', f)
    f = re.sub(r'DATE\((\d{4})-1,12,31\)', lambda m: f'DATE({int(m.group(1)) + 1}-1,3,31)', f)
    return f

TEXT = {
    'Bull-Base-Bear': {
        'B2': 'James Hardie Industries plc (JHX) — Bull / Base / Bear Case P&L Summary',
        'B3': ('Adjusted figures (company definitions: Adjusted EBITDA, adjusted net income and adjusted diluted EPS; FY2027+ continuing operations, ex share-based compensation) · '
               'USD millions · fiscal years ended 31 March · Live panel linked to Model — toggle scenario via Model!CK2. Bull and Bear panels are value snapshots generated '
               'from the Model with the switch set to each case. FY2027E set to the FY27 planning assumptions (net sales US$4.99–5.13bn, Adjusted EBITDA US$1,446–1,534m).'),
        'G26': 18, 'H26': 18, 'S26': 20, 'T26': 20, 'AD26': 14, 'AE26': 14, 'AF26': 14,
    },
    'DCF': {
        'B2': 'DCF VALUATION — JAMES HARDIE INDUSTRIES PLC (JHX)',
        'C5': 0.045, 'D5': 'Assumption (~US 10Y Treasury yield, Nov-2026); update to market',
        'C7': 1.15, 'D7': 'US building-products / housing peers (Trex, AZEK pre-deal, Louisiana-Pacific, Masonite, Owens Corning) ~1.1–1.3; new-construction and R&R cyclicality, now with a US$3.7bn net debt load',
        'C9': 0.058, 'D9': 'BB+ / Ba1 senior notes (5.875% 2031, 6.125% 2032) and SOFR-based term loans; weighted-average rate 5.7% at 30-Sep-2026',
        'C10': 0.26, 'D10': 'Model 2028E+ GAAP effective tax rate (30% → 26%); adjusted rate ~22%',
        'C12': 0.20, 'D12': 'Net debt ~US$3.7bn + net asbestos liability ~US$0.7bn vs ~US$17.8bn market cap (US$30.45 × ~586m diluted shares); deleveraging to < 2.0x by Q2 FY28',
        'D15': 'Periods = (31-Mar of fiscal year − today) / 365.25; cash flows assumed at fiscal year-end (31 March)',
        'B18': 'Adj. EBITA after SBC less restructuring and acquisition / divestiture costs',
        'B21': 'plus depreciation & other amortization (excl. AZEK intangible amortization)',
        'B22': '− Capex (PP&E) and acquisitions (bolt-ons 2028E–31E) + Europe sale proceeds (closing year)',
        'B26': 'Fade-period growth (2032E–36E; 5.0% → 4.0% linear)', 'I26': 0.05, 'M26': 0.04, 'C27': 0.03,
        'D32': ("James Hardie's Adjusted EBITDA excludes share-based compensation (from FY27), asbestos adjustments, restructuring and acquisition items and, through D&A, the AZEK "
                'intangible amortization (~US$310m in FY27E). Adjusted EBITA here is before that amortization and after share-based compensation; only depreciation & other amortization '
                'is added back (row 21). Restructuring and acquisition / divestiture costs (cash; adjusted out by the company) are deducted inside row 18. Row 22 includes bolt-on '
                'acquisitions in 2028E–31E and the Europe (fermacell) sale proceeds in the closing year, so the discontinued European business is valued through its proceeds; asbestos '
                'claims paid flow through working capital. The net unfunded asbestos liability is deducted with net debt in the equity bridge.'),
        'D43': 'Opening IC = Model FY2026A book IC (equity + net debt; AZEK consolidated from 1-Jul-2025), rolled forward with capex + M&A − DD&A + ΔWC.',
        'B48': 'Less: Net debt + net unfunded asbestos liability (Model FY2027E year end, 31-Mar-2027)',
        'D48': 'JHX: the net unfunded asbestos liability (liability − insurance receivable − AICF cash & investments, ~US$0.7bn) is deducted alongside net debt; no NCI.',
        'B50': 'Diluted shares (m, Model FY2027E period end)',
        'D76': 'Rationale (James Hardie characteristics)',
        'C78': 0.09, 'D78': 'Model Adjusted EBITA CAGR FY2027–31E: mid-single-digit volume growth (US housing recovery, material conversion), DR&A share gains, AZEK synergies (US$125m cost + US$125m commercial run-rate) and deleveraging → ~9% NOPAT growth',
        'C79': 0.15, 'D79': 'Fiber cement network (~30% US siding share, HOS cost programme) earns high returns on legacy capital; the AZEK deal (~17x EBITDA) earns ~7–8% after tax on consideration; capacity expansions (Prattville, Crystal City, Westfield) at mid-teens',
        'C80': 12, 'D80': 'Brand, builder exclusivity and contractor conversion sustain pricing; cyclicality of US new construction / R&R, substitution (vinyl, engineered wood, composites) and the asbestos funding obligation limit the CAP',
        'B90': 'VALUATION  —  Applied to FY2029E NOPAT',
        'B91': 'FY2029E Adj. EBITA after SBC less restructuring and acquisition / divestiture costs',
        'B93': 'FY2029E NOPAT',
        'B95': 'Implied Enterprise Value (FY2029E basis)',
        'B96': 'Less: FY2028E year-end net debt + net asbestos liability (Model)',
        'B98': 'Diluted shares FY2029E (m, Model)',
        'B99': 'Implied share price FY2029 ($)',
        'B106': 'Plus: FY2027E year-end net debt + net asbestos liability',
        'B108': 'JHX market-implied EV/NOPAT (on FY2029E NOPAT)',
    },
    'Charts': {
        'B2': 'James Hardie Industries — Operating Performance (FY2006–FY2026) and Model Forecast (FY2027E–FY2031E)',
        'B3': ('USDm · fiscal years ended 31 March · Linked to Model. Bars = contribution to group net sales growth from Siding & Trim (North America fiber cement) vs the other segments '
               '(DR&A from FY26, Australia & New Zealand, Europe to FY26, legacy). Adjusted EBITDA = company definition from FY2023 (model bridge before). ROIC / RONTA on Adjusted EBITA after SBC.'),
        'B8': 'Siding & Trim contribution to growth %', 'B9': 'Other segments contribution %', 'B12': 'Adjusted EBITDA', 'B13': 'Operating Income (GAAP)',
    },
}
BBB_ROWS = {9: 'Net sales', 10: '   Net sales y/y %', 11: '   Siding & Trim (NA fiber cement) net sales y/y %', 12: 'Adjusted EBITDA (company definition / model bridge)',
            15: 'Operating Income (GAAP)', 16: '   Operating income y/y %', 19: 'Adjusted Net Income',
            35: 'Adjusted EBITDA (leverage basis)', 36: '   Adjusted EBITDA % of net sales'}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Net Sales Growth Contribution: Siding &amp; Trim (NA Fiber Cement) vs. Other Segments, y/y %',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted EBITDA &amp; Operating Income (USDm)',
}

def build_charts(ws):
    for i, y in enumerate(range(2006, 2032)):
        c = L(3 + i); mc = ANN[y].c; pc = ANN[y - 1].c if y - 1 in ANN else None
        ws[f'{c}7'] = y if y <= 2026 else f'{y}E'
        if pc:
            ws[f'{c}8'] = f'=IFERROR((Model!{mc}{R["st_rev"]}-Model!{pc}{R["st_rev"]})/Model!{pc}{R["is_rev"]},0)'
            ws[f'{c}9'] = f'=IFERROR(Model!{mc}{R["gm_rev"]}-{c}8,0)'
        else:
            ws[f'{c}8'] = 0; ws[f'{c}9'] = 0
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
    b['J2'] = 'Share price ($):'
    from openpyxl.comments import Comment
    for addr in ('N26', 'Z26', 'G26'):
        if b[addr].comment is not None or addr == 'N26':
            c = Comment('P/E on adjusted diluted EPS. James Hardie has traded at ~15–30x NTM adjusted EPS over FY2019–26 (≈18x FY27E adjusted EPS at US$30.45). Panel inputs: Bull 20x, Base 18x, Bear 14x.', 'JHX model')
            c.width, c.height = 420, 120; b[addr].comment = c
    for addr in ('P40', 'AB40', 'D40'):
        if b[addr].comment is not None:
            c = Comment('Snapshot (values) of the Model share-buyback schedule rows with the scenario switch (Model!CK2) set to this case, captured by build.py --snap.', 'JHX model')
            c.width, c.height = 420, 100; b[addr].comment = c
    for c in ('B', 'N', 'Z'): b[f'{c}29'] = 'IRR (to 31-Mar of Y-1)'
    for c in ('B', 'N', 'Z'):
        if b[f'{c}40'].value: b[f'{c}40'] = '   Share repurchases ($m; FY2027E = Q3–Q4)'
    d = wb['DCF']
    for i, col in enumerate('DEFGHIJKLM'):
        d[f'{col}17'] = f'{2027 + i}E'
    a26 = ANN[2026].c
    for i, col in enumerate('DEFGH'):
        ac = ANN[2027 + i].c
        d[f'{col}22'] = f'=Model!{ac}{R["cf_capex"]}+Model!{ac}{R["cf_acq"]}+Model!{ac}{R["cf_dvp"]}'
    d['D34'] = f'=Model!{a26}{R["ra_ic"]}'
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
    (Charts!C:AB = FY2006-FY2031E) and cached values removed so Excel redraws from the JHX cells."""
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
            elif item.filename.startswith('xl/comments'):
                # LibreOffice's recalculation re-saves the cell comments without their author: restore the build's author
                data = re.sub(r'<author>[^<]*</author>', '<author>JHX model</author>', data.decode('utf-8')).encode('utf-8')
            zout.writestr(item, data)
    shutil.move(tmp, path)
