"""Rewire the Bull-Base-Bear, DCF and Charts tabs of the MLM template (current layout: DCF with live valuation date, fade period,
implied ROIC, target-IRR entry price, reverse DCF and Mauboussin EV/NOPAT; Bull-Base-Bear with buyback rows) to the JBHT Model
rows; keep the template chart XML. The template's DCF_old tab is not carried.

JBHT uses the template column map unchanged (2025A = BV, 2026E = CA, 2027E-2030E = CB-CE, switch in CF2), so only row numbers
are remapped. The DCF's 2026E column is kept for the invested-capital roll-forward but its cash flow is excluded from the
present value: net debt is taken at year-end 2026E, which already contains the 2026 cash flows (valuation date ~ Nov-2026)."""
import re, zipfile, shutil
from openpyxl.utils import get_column_letter as L
from openpyxl.comments import Comment
from fw import R, TEMPLATE, ANN, NOTE, AUTHOR, MAN

# template Model row -> JBHT row key
MAP = {158: 'is_rev', 164: 'r_cash', 166: 'is_oi', 182: 'is_dda', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 219: 'r_ebit', 221: 'r_adj',
       229: 'e_adjni', 231: 'e_eps', 238: 'gm_jbi', 245: 'gm_ebitda_m', 247: 'gm_op_m', 260: 'cf_wc', 262: 'cf_capex', 263: 'cf_acq',
       280: 'fcf', 282: 'fcf_m', 290: 'bb_px', 291: 'bb_cash', 292: 'bb_sh', 331: 'bs_nci', 408: 'ra_ic', 411: 'ra_roic', 422: 'rn_ronta',
       428: 'lv_nd', 433: 'v_px', 434: 'v_sh'}
REF = re.compile(r"Model!(\$?)([A-Z]{1,3})(\$?)(\d+)")
HIST = [ANN[y].c for y in range(2006, 2026)]
PX = MAN['price']['px']

def remap(f):
    def rep(m):
        c, r = m.group(2), int(m.group(4))
        if c == NOTE and r == 2: return m.group(0)                # scenario switch
        if r not in MAP: raise KeyError(f'unmapped template row {r} in {f}')
        return f'Model!{m.group(1)}{c}{m.group(3)}{R[MAP[r]]}'
    return REF.sub(rep, f)

def hist_stat(f):
    """LT historical AVERAGE / MIN / MAX over the template's annual columns -> JBHT FY2006-FY2025 annual columns."""
    m = re.match(r'=IFERROR\((AVERAGE|MIN|MAX)\(Model!C(\d+),', f)
    if not m: return None
    fn, r = m.group(1), int(m.group(2))
    rr = R[MAP[r]]
    return f'=IFERROR({fn}({",".join(f"Model!{c}{rr}" for c in HIST)}),"")'

TEXT = {
    'Bull-Base-Bear': {
        'B2': 'J.B. Hunt Transport Services (JBHT) — Bull / Base / Bear Case P&L Summary',
        'B3': ('Adjusted figures are model definitions (J.B. Hunt publishes no non-GAAP measures): operating income / EBITDA / EPS excluding only the items the company quantified · '
               'USD millions · Live panel linked to Model — toggle the scenario with the switch on the Model tab (cell CF2). Bull and Bear panels are value snapshots generated from the '
               'Model with the switch set to each case. 2026E = Q1–Q3 actual + Q4 on historical Q3→Q4 seasonality (no company revenue / EPS guidance).'),
        'G26': 22, 'H26': 22, 'S26': 25, 'T26': 25, 'AD26': 17, 'AE26': 17, 'AF26': 17,
    },
    'DCF': {
        'B2': 'DCF VALUATION — J.B. HUNT TRANSPORT SERVICES (JBHT)',
        'C5': 0.0425, 'D5': 'Assumption (~US 10Y Treasury yield, Nov-2026; government rate sources are not reachable from the build environment); update to market',
        'D6': 'Assumption: US implied equity risk premium ~4.5–5.5%',
        'C7': 1.1, 'D7': 'Assumption: asset-based transportation peers (truckload, intermodal, LTL, brokerage) ~1.0–1.3; freight-cycle earnings sensitivity',
        'C9': 0.05, 'D9': '4.90% senior notes due March 2030 (issued Mar-2025); credit facility at 4.85% average at 30-Sep-2026 (Q3-26 10-Q)',
        'C10': 0.24, 'D10': 'Model 2027E+ effective tax rate (company FY26 outlook ~24.0%)',
        'C12': 0.06, 'D12': f'Net debt ~$1.1bn at 30-Sep-2026 vs ~$22bn market cap (${PX:.2f} × ~94m diluted shares); ~0.7x adjusted EBITDA',
        'D15': 'Periods = (Dec-31-Year − today) / 365.25; cash flows assumed at year-end. 2026E cash flow is excluded from the present value (row 31): it is already in year-end 2026E net debt',
        'B18': 'Adj. EBIT (full-cost) less company-quantified cash items',
        'B21': 'plus D&A (depreciation + amortization of intangibles)',
        'B22': '− Net capital expenditures (additions − equipment sale proceeds) and acquisitions',
        'B26': 'Fade-period growth (2031E–35E; 6.0% → 4.5% linear)', 'I26': 0.06, 'M26': 0.045, 'C27': 0.035,
        'D32': ("Adjusted EBIT (model definition) is after all depreciation, intangible amortization (~$10–20m p.a.) and share-based compensation; total D&A is added back in row 21. "
                "Company-quantified items are nil in the forecast. Row 22 uses J.B. Hunt's net capital expenditures (equipment trade-ins are a recurring source of cash) plus the M&A lever "
                "(Base: none). 2026E is shown for the invested-capital roll-forward only: its present value is set to zero because net debt is taken at year-end 2026E."),
        'D43': 'Opening IC = Model 2025A book IC (equity + net debt), rolled forward with net capex + M&A − D&A + ΔWC.',
        'B48': 'Less: Net debt + NCI (Model 2026E year end)',
        'D48': 'JBHT: no noncontrolling interests; operating leases (~$0.3bn) are not treated as debt (rent stays in operating costs). Net debt at year-end 2026E, so 2026E cash flow is not double counted.',
        'B50': 'Diluted shares (m, Model 2026E period end)',
        'D76': 'Rationale (J.B. Hunt characteristics)',
        'C78': 0.10, 'D78': 'Model adjusted EBIT CAGR 2026–30E: mid-single-digit volume growth, ~2% rate / mix and margin recovery from the 2024–26 trough toward mid-cycle levels → ~10% NOPAT growth',
        'C79': 0.14, 'D79': 'Intermodal returns rest on the BNSF / Norfolk Southern rail relationships and the largest private container fleet; Dedicated earns contract returns on customer-specific fleets; incremental capital is mostly containers, tractors and trailers (ROIC 12–20% over the cycle)',
        'C80': 10, 'D80': 'Scale in intermodal (rail access, ~124k containers, dray network) and long-dated Dedicated contracts (~96% retention) vs commodity truckload / brokerage exposure and rail-service dependence',
        'B90': 'VALUATION  —  Applied to 2028E NOPAT',
        'B91': '2028E Adj. EBIT less company-quantified cash items',
        'B108': 'JBHT market-implied EV/NOPAT (on 2028E NOPAT)',
    },
    'Charts': {
        'B2': 'J.B. Hunt Transport Services — Historical Operating Performance (2006–2025)',
        'B3': ('All historicals · USDm · Linked to Model. Volume / price = Intermodal loads and revenue per load (incl. fuel surcharge) y/y. Adjusted EBITDA = model definition '
               '(operating income + D&A + company-quantified items). ROIC / RONTA on adjusted EBIT (full-cost).'),
        'B8': 'Intermodal loads %', 'B9': 'Intermodal revenue per load %', 'B12': 'Adjusted EBITDA', 'B13': 'Operating income (GAAP)',
        'B14': 'Adj. EBITDA Margin %', 'B15': 'GAAP Op. Margin %',
    },
}
BBB_ROWS = {9: 'Revenues', 10: '   Revenues y/y %', 11: '   Intermodal loads y/y %', 12: 'Adjusted EBITDA (model definition)', 13: '   Adjusted EBITDA margin %',
            15: 'Operating income (GAAP)', 16: '   Operating income y/y %', 17: '   Operating margin (GAAP) %', 19: 'Adjusted Net Earnings (model definition)',
            35: 'Adjusted EBITDA (leverage basis)', 36: '   Adjusted EBITDA % of revenues'}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Intermodal Revenue Drivers: Load Volume vs. Revenue per Load, y/y %',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted EBITDA &amp; Operating Income (USDm)',
}

def build_charts(ws):
    for i, y in enumerate(range(2006, 2026)):
        c = L(3 + i); mc = ANN[y].c
        ws[f'{c}7'] = y
        ws[f'{c}8'] = f'=IFERROR(Model!{mc}{R["jbi_vol_g"]}+0,0)'
        ws[f'{c}9'] = f'=IFERROR(Model!{mc}{R["jbi_unit_g"]}+0,0)'
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
                if c.comment is not None: c.comment = None                  # template-company comments are not carried
                if name == 'DCF' and c.coordinate == 'D34': continue           # template deal-specific cell, rewritten below
                if isinstance(c.value, str) and 'Model!' in c.value and name != 'Charts':
                    h = hist_stat(c.value) if name == 'Bull-Base-Bear' else None
                    c.value = h or remap(c.value)
        for addr, t in TEXT.get(name, {}).items():
            ws[addr] = t
    b = wb['Bull-Base-Bear']
    for r, t in BBB_ROWS.items():
        for c in ('B', 'N', 'Z'): b[f'{c}{r}'] = t
    cm = Comment(f'P/E on adjusted EPS (model definition; equals GAAP EPS in the forecast). At ${PX:.2f} (September 2026 average repurchase price, Q3-26 10-Q) JBHT trades at about '
                 '33x 2026E EPS, on earnings still near the freight-cycle trough. Exit multiples are assumptions: Base 22x, Bull 25x, Bear 17x applied to 2029E–30E '
                 '(2028E–30E for Bear), against a 2006–25 history of roughly 15–30x.', AUTHOR)
    cm.width, cm.height = 420, 120; b['N26'].comment = cm
    cm2 = Comment(f'Snapshot (values) of Model rows {R["bb_cash"]}, {R["bb_px"]} and {R["bb_sh"]} (Share Buyback Schedule) with the Model scenario switch (cell {NOTE}2) set to '
                  'Bull / Bear. Base panel (D40:H42) is live-linked.', AUTHOR)
    cm2.width, cm2.height = 420, 90; b['P40'].comment = cm2
    for c in ('B', 'N', 'Z'):
        if b[f'{c}40'].value: b[f'{c}40'] = '   Share repurchases ($m; 2026E = Q4)'
    d = wb['DCF']
    for col in 'DEFGH':
        y = 2026 + 'DEFGH'.index(col); mc = ANN[y].c
        d[f'{col}22'] = f'=Model!{mc}{R["cf_capex"]}+Model!{mc}{R["cf_sale"]}+Model!{mc}{R["cf_acq"]}'
    d['I22'] = '=H22*(1+I$26)'
    d['D31'] = '=0*D24*D30'
    d['D34'] = f'=Model!{ANN[2025].c}{R["ra_ic"]}'
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
    (Charts!C:V = FY2006-FY2025) and cached values removed so Excel redraws from the JBHT cells."""
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
