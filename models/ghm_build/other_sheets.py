"""Rewire the Bull-Base-Bear, DCF and Charts tabs of the MLM template (current layout: DCF with live valuation date, fade period,
implied ROIC, target-IRR entry price, reverse DCF and Mauboussin EV/NOPAT; Bull-Base-Bear with buyback rows) to the GHM Model rows /
columns; keep the template chart XML. The template's DCF_old tab is not carried.

Column mapping: the template's 2025A base column becomes GHM FY2026 (fiscal year ended 31-Mar-2026, actual); the template's 2026E
becomes GHM FY2027E (Q1 actual + Q2-Q4 calibrated to guidance) and 2027E-2030E become FY2028E-FY2031E. Net debt in the DCF is taken at
31-Mar-2027 (FY2027E year end), so the FY2027E unlevered cash flow is excluded from the PV (it is already in that net debt)."""
import re, zipfile, shutil
from openpyxl.utils import get_column_letter as L
from openpyxl.comments import Comment
from fw import R, TEMPLATE, ANN, NOTE, AUTHOR, MAN

# template Model row -> GHM row key
MAP = {158: 'is_rev', 164: 'r_cash', 166: 'is_op', 182: 'd_dep', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 219: 'r_ebita_s', 221: 'r_adj',
       229: 'e_adjni', 231: 'e_eps', 238: 'gm_def', 245: 'gm_ebitda_m', 247: 'gm_op_m', 260: 'cf_wc', 262: 'cf_capex', 263: 'cf_acq',
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
    """LT historical AVERAGE / MIN / MAX over the template's annual columns -> GHM FY2006-FY2026 annual columns."""
    m = re.match(r'=IFERROR\((AVERAGE|MIN|MAX)\(Model!C(\d+),', f)
    if not m: return None
    fn, r = m.group(1), int(m.group(2))
    rr = R[MAP[r]]
    return f'=IFERROR({fn}({",".join(f"Model!{c}{rr}" for c in HIST)}),"")'

def fy_dates(f):
    f = re.sub(r'DATE\((\d{4}),12,31\)', lambda m: f'DATE({int(m.group(1)) + 1},3,31)', f)
    f = re.sub(r'DATE\((\d{4})-1,12,31\)', lambda m: f'DATE({int(m.group(1)) + 1}-1,3,31)', f)
    return f

PX = MAN['price']['px']
TEXT = {
    'Bull-Base-Bear': {
        'B2': 'Graham Corporation (GHM) — Bull / Base / Bear Case P&L Summary',
        'B3': ('Adjusted figures (company definitions: Adjusted EBITDA, adjusted net income / EPS) · USD millions · fiscal years ended 31 March · Live panel linked to Model — '
               'toggle scenario via Model!CK2. Bull and Bear panels are value snapshots generated from the Model with the switch set to each case. FY2027E = Q1 actual + '
               'Q2–Q4 calibrated to the FY27 guidance (net sales $285–295m, Adjusted EBITDA $35–40m).'),
        'G26': 40, 'H26': 40, 'S26': 45, 'T26': 45, 'AD26': 30, 'AE26': 30, 'AF26': 30,
    },
    'DCF': {
        'B2': 'DCF VALUATION — GRAHAM CORPORATION (GHM)',
        'C5': 0.0425, 'D5': 'Assumption (~US 10Y Treasury yield, Nov-2026; government rate sources not reachable from the build environment); update to market',
        'D6': 'Assumption: US implied ERP ~4.5–5.5%',
        'C7': 1.1, 'D7': ('Assumption: small-cap defense / flow-control peers (ESAB, CW, MOG) ~1.0–1.3; Defense backlog (84%) dampens cyclicality, while size, '
                         'project lumpiness and Energy & Process (~30% of sales) argue against the low end'),
        'C9': 0.052, 'D9': 'Wells Fargo revolver: SOFR (3.68% at 31-Mar-2026) + 1.25–2.50%; undrawn at 30-Jun-2026',
        'C10': 0.20, 'D10': 'Model FY2028E+ effective tax rate (FY27 guidance 18–20%; statutory 23% used by the company for adjustments)',
        'C12': 0.02, 'D12': f'Net cash ~$27m at 30-Jun-2026 vs ~$1.1bn market cap (${PX} × ~11.8m diluted shares); funding mostly equity — 2% debt weight (assumption)',
        'D15': 'Periods = (31-Mar of fiscal year − today) / 365.25; cash flows assumed at fiscal year-end (31 March)',
        'B18': 'Adjusted EBITA after SBC (Adjusted EBITDA − depreciation − equity-based compensation) less cash acquisition, ERP & restructuring costs',
        'B21': 'plus depreciation (amortization of acquired intangibles not added back — already excluded from Adjusted EBITA)',
        'B22': '− Capex (PP&E) and acquisitions (bolt-ons; M&A lever FY2028E–31E)',
        'B26': 'Fade-period growth (FY2032E–36E; 8.0% → 5.0% linear)', 'I26': 0.08, 'M26': 0.05, 'C27': 0.035,
        'D32': ("Graham's Adjusted EBITDA adds back equity-based compensation (from Q4 FY2024), acquisition & integration and ERP costs; NOPAT here deducts SBC and "
                'those cash costs again (row 18) and adds back depreciation only (row 21), so acquired-intangible amortization is neither deducted nor added back. '
                'Row 22 includes bolt-on acquisitions in FY2028E–31E; the fade period and terminal value assume no new acquisitions. FY2027E UFCF is excluded '
                '(row 31 set to zero): net debt is taken at 31-Mar-2027 and already contains it.'),
        'D43': 'Opening IC = Model FY2026A book IC (equity + net debt at 31-Mar-2026, incl. FlackTek), rolled forward with capex + M&A − depreciation + ΔWC.',
        'B48': 'Less: Net debt (cash) + NCI (Model FY2027E year end, 31-Mar-2027)',
        'D48': 'GHM: no noncontrolling interests, preferred stock or funded debt; operating leases treated as operating costs (not in net debt). FlackTek earn-out liability (~$7m) sits in other liabilities.',
        'B50': 'Diluted shares (m, Model FY2027E period end)',
        'D76': 'Rationale (Graham characteristics)',
        'C78': 0.14, 'D78': 'Model NOPAT CAGR FY2027–31E: ~9–10% sales growth (record $557m backlog, 84% Defense) with margin expansion toward the 14–16% Investor Day Adjusted EBITDA margin',
        'C79': 0.20, 'D79': 'Company >20% ROIC hurdle on organic capacity / automation projects (customer-funded Navy facility); sole-source content on long-lived submarine and carrier programs',
        'C80': 12, 'D80': 'Multi-decade Navy platform demand (Virginia / Columbia / Ford classes; ~$1.8bn opportunity to 2056) and a >$1bn installed base for aftermarket; offset by Energy & Process cyclicality and fixed-price execution risk',
        'B90': 'VALUATION  —  Applied to FY2029E NOPAT',
        'B91': 'FY2029E NOPAT base (Adjusted EBITA after SBC less cash adjusting costs)',
        'B93': 'FY2029E NOPAT',
        'B95': 'Implied Enterprise Value (FY2029E basis)',
        'B96': 'Less: FY2028E year-end net debt (cash) + NCI (Model)',
        'B98': 'Diluted shares FY2029E (m, Model)',
        'B99': 'Implied share price FY2029 ($)',
        'B106': 'Plus: FY2027E year-end net debt (cash) + NCI',
        'B108': 'GHM market-implied EV/NOPAT (on FY2029E NOPAT)',
    },
    'Charts': {
        'B2': 'Graham Corporation — Operating Performance (FY2012–FY2026) and Model Forecast (FY2027E–FY2031E)',
        'B3': ('USDm · fiscal years ended 31 March · Linked to Model. Bars = contribution of each market group to net-sales growth (pp; current market basis from FY2020). '
               'Adjusted EBITDA = company definition (EBITDA where no adjusted figure was published). ROIC / RONTA on NOPAT after SBC and cash adjusting costs.'),
        'B8': 'Defense contribution to growth (pp)', 'B9': 'Space + Energy & Process contribution (pp)', 'B12': 'Adjusted EBITDA', 'B13': 'Operating profit (GAAP)',
        'B14': 'Adj. EBITDA Margin %', 'B15': 'Operating Margin %',
    },
}
BBB_ROWS = {9: 'Net sales', 10: '   Net sales y/y %', 11: '   Defense sales y/y %', 12: 'Adjusted EBITDA',
            15: 'Operating profit (GAAP)', 16: '   Operating profit y/y %', 17: '   Operating margin (GAAP) %', 19: 'Adjusted net income',
            35: 'Adjusted EBITDA (leverage basis)', 36: '   Adjusted EBITDA % of net sales', 38: 'Net debt (cash)', 39: '   Net debt (cash) / Adjusted EBITDA (x)'}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Net Sales Growth: Defense vs. Space + Energy &amp; Process Contribution, pp',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted EBITDA &amp; Operating Profit (USDm)',
}

def build_charts(ws):
    for i, y in enumerate(range(2012, 2032)):
        c = L(3 + i); mc = ANN[y].c
        ws[f'{c}7'] = y if y <= 2026 else f'{y}E'
        ws[f'{c}8'] = f'=IFERROR(Model!{mc}{R["gc_def"]}+0,0)'
        ws[f'{c}9'] = f'=IFERROR(Model!{mc}{R["gc_oth"]}+0,0)'
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
                if c.comment is not None: c.comment = None
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
    cm = Comment(f'P/E on adjusted EPS (company definition: adds back acquired-intangible amortization, tax-effected at 23%; does not add back SBC). GHM at ${PX} trades at '
                 '~49x FY2027E and ~41x FY2028E adjusted EPS, reflecting a long-cycle Defense backlog and margin expansion still ahead. Exit multiples are assumptions: Base 40x, Bull 45x, '
                 'Bear 30x applied to FY2030E–31E (FY2029E–31E for Bear), converging toward defense-component peers as growth normalises.', AUTHOR)
    cm.width, cm.height = 420, 130; b['N26'].comment = cm
    cm2 = Comment(f'Snapshot (values) of Model rows {R["bb_cash"]}, {R["bb_px"]} and {R["bb_sh"]} (Share Buyback Schedule) with Model!{NOTE}2 = Bull / Bear. '
                  'Base panel (D40:H42) is live-linked.', AUTHOR)
    cm2.width, cm2.height = 420, 90; b['P40'].comment = cm2
    b['J2'] = 'Share price ($):'
    for c in ('B', 'N', 'Z'): b[f'{c}29'] = 'IRR (to 31-Mar of Y-1)'
    for c in ('B', 'N', 'Z'):
        if b[f'{c}40'].value: b[f'{c}40'] = '   Share repurchases ($m; FY2027E = Q2–Q4)'
    d = wb['DCF']
    for i, col in enumerate('DEFGHIJKLM'):
        d[f'{col}17'] = f'{2027 + i}E'
    a26, a27 = ANN[2026].c, ANN[2027].c
    d['D22'] = f'=Model!{a27}{R["cf_capex"]}+Model!{a27}{R["cf_acq"]}'
    d['D31'] = '=0*D24*D30'
    d['D34'] = f'=Model!{a26}{R["ra_ic"]}'
    d['C48'] = f'=Model!{a27}{R["lv_nd"]}+Model!{a27}{R["bs_nci"]}'
    d['C50'] = f'=Model!{a27}{R["v_sh"]}'
    d['C52'] = f'=Model!{a27}{R["v_px"]}'
    d['P17'] = 'CAGR 28–31E'; d['Q17'] = 'CAGR 28–36E'
    for r in range(18, 45):                       # CAGRs from FY2028E (FY2027E is excluded from the DCF)
        for c, end, n in (('P', 'H', 3), ('Q', 'M', 8)):
            v = d[f'{c}{r}'].value
            if isinstance(v, str) and v.startswith('=(') and 'COLUMNS(' in v:
                d[f'{c}{r}'] = f'=IFERROR(({end}{r}/E{r})^(1/{n})-1,"n/m")'
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
    (Charts!C:V = FY2012-FY2031E) and cached values removed so Excel redraws from the GHM cells."""
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
