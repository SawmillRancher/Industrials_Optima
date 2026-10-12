"""Rewire the Bull-Base-Bear, DCF and Charts tabs of the MLM template (current layout: DCF with live valuation date, fade period,
implied ROIC, target-IRR entry price, reverse DCF and Mauboussin EV/NOPAT; Bull-Base-Bear with buyback rows) to the MCO Model rows;
keep the template chart XML. The template's DCF_old tab is not carried.

Column mapping: MCO uses the template's column layout unchanged (2025A = BV, 2026E = CA, 2027E-2030E = CB-CE, notes = CF), so
only rows are remapped. FY2026E is two-thirds elapsed at the valuation date and net debt is taken at YE2026E, so the 2026E UFCF is
shown but excluded from the DCF sum (it is already in YE2026E net debt); the explicit years are 2027E-2030E."""
import re, zipfile, shutil
from openpyxl.utils import get_column_letter as L
from fw import R, TEMPLATE, ANN, NOTE

# template Model row -> MCO row key
MAP = {158: 'is_rev', 164: 'r_cash', 166: 'is_oi', 182: 'd_dep', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 219: 'r_ebit', 221: 'r_adj',
       229: 'e_adjni', 231: 'e_eps', 238: 'gm_mis', 245: 'gm_ebitda_m', 247: 'gm_op_m', 260: 'cf_wc', 262: 'cf_capex', 263: 'cf_acq',
       280: 'fcf', 282: 'fcf_m', 290: 'bb_px', 291: 'bb_cash', 292: 'bb_sh', 331: 'bs_nci', 408: 'ra_ic', 411: 'ra_roic', 422: 'rn_ronta',
       428: 'lv_nd', 433: 'v_px', 434: 'v_sh'}
REF = re.compile(r"Model!(\$?)([A-Z]{1,3})(\$?)(\d+)")

def remap(f):
    def rep(m):
        c, r = m.group(2), int(m.group(4))
        r2 = R[MAP[r]] if r in MAP else r
        if c == 'CF' and r == 2: r2 = 2
        return f'Model!{m.group(1)}{c}{m.group(3)}{r2}'
    return REF.sub(rep, f)

TEXT = {
    'Bull-Base-Bear': {
        'B2': "Moody's Corporation (MCO) — Bull / Base / Bear Case P&L Summary",
        'B3': ("Adjusted figures (company definitions: Adjusted Operating Income = model Adjusted EBITDA; adjusted diluted EPS) · USD millions · Live panel linked to Model — toggle "
               "scenario via Model!CF2. Bull and Bear panels are value snapshots generated from the Model with the switch set to each case. 2026E = Q1–Q2 actual + Q3–Q4 calibrated "
               "to the FY26 guidance (MIS revenue up HSD, MA up MSD, adjusted EPS $16.50–17.00)."),
        'G26': 31, 'H26': 31, 'S26': 35, 'T26': 35, 'AD26': 24, 'AE26': 24, 'AF26': 24,
    },
    'DCF': {
        'B2': "DCF VALUATION — MOODY'S CORPORATION (MCO)",
        'C5': 0.0425, 'D5': 'Assumption (~US 10Y Treasury yield, Oct-2026; government rate sources are not reachable from the build environment); update to market',
        'D6': 'Assumption: US implied ERP ~4.5–5.5%',
        'C7': 1.10, 'D7': 'Assumption: financial data / ratings peers (SPGI, MSCI, FDS, ICE) ~0.9–1.2; MIS issuance-driven revenue (~55% of total) adds cyclicality to the recurring MA base',
        'C9': 0.050, 'D9': 'Aug-2024 $500m 5.00% senior notes due 2034 (latest issue; Q2-26 10-Q Note 13); marginal 10-year cost ~5.0% (assumption)',
        'C10': 0.24, 'D10': 'Model 2027E+ effective tax rate (FY26 ETR guidance 23–25%)',
        'C12': 0.08, 'D12': 'Total debt ~$6.9bn at 30-Jun-2026 vs ~$82bn market cap ($470 × ~174m diluted shares); net debt ~1.3x Adjusted Operating Income',
        'D15': 'Periods = (31-Dec-Year − today) / 365.25; cash flows assumed at year-end. 2026E UFCF is shown but excluded from the sum (YE2026E net debt already reflects it)',
        'B18': 'Adj. EBITA less restructuring & other excluded cash items',
        'B21': 'plus depreciation & amortization excl. acquired intangibles',
        'B22': '− Capex and acquisitions (M&A lever 2027E–30E)',
        'B26': 'Fade-period growth (2031E–35E; 7% → 5% linear)', 'I26': 0.07, 'M26': 0.05, 'C27': 0.04,
        'D32': ("NOPAT basis (playbook 5.7): Adjusted EBITA = Adjusted Operating Income (which excludes D&A, restructuring and other items) − depreciation and amortization of PP&E / "
                "software, i.e. before acquired-intangible amortization; stock-based compensation is already expensed. Restructuring and the other items Moody's excludes "
                "(reserves, duplicate rent, asset abandonment) are deducted as cash costs in row 18. Row 21 adds back depreciation only. Row 22 includes bolt-on M&A in 2027E–30E; "
                "the fade period and terminal value assume no new acquisitions. 2026E (column D) is excluded from the sum of PV because net debt is taken at YE2026E. "
                "Divestiture gains and contingent consideration (Regulatory Solutions) are excluded. Leases are treated as operating costs (not in net debt)."),
        'D43': 'Opening IC = Model 2025A book IC (equity incl. NCI + net debt), rolled forward through 2026E with capex + M&A − depreciation + ΔWC.',
        'B48': 'Less: Net debt + NCI (Model 2026E year end)',
        'D48': 'MCO: noncontrolling interests (ICRA, ~$0.15bn) deducted alongside net debt (total debt − cash − short-term investments) at YE2026E.',
        'B50': 'Diluted shares (m, Model 2026E period end)',
        'D76': "Rationale (Moody's characteristics)",
        'C78': 0.08, 'D78': 'Model Adjusted EBITA CAGR 2025–30E: mid- to high-single-digit revenue growth (issuance cycle + recurring MA) with margin expansion → ~8% NOPAT growth',
        'C79': 0.40, 'D79': 'Ratings duopoly with S&P (NRSRO certification, issuer-pays model) and data / analytics with high renewal rates; incremental capital needs are small (capex ~5% of revenue), so returns on incremental capital are very high; large acquisitions (BvD, RMS) earned much lower returns on purchase price',
        'C80': 20, 'D80': 'Regulatory and reputational moat in ratings (decades of track record, investor mandates) and embedded MA workflow data; risks: regulation, issuance cyclicality, AI-driven disintermediation of research',
        'B90': 'VALUATION  —  Applied to 2028E NOPAT',
        'B91': '2028E Adj. EBITA less restructuring & other excluded cash items',
        'B108': 'MCO market-implied EV/NOPAT (on 2028E NOPAT)',
    },
    'Charts': {
        'B2': "Moody's Corporation — Operating Performance (2011–2025) and Model Forecast (2026E–2030E)",
        'B3': ('USDm · Linked to Model. Bars = contribution of each segment to total revenue growth (pp). Adjusted Operating Income = company definition (Adjusted EBITDA; before '
               '2012 the model applies the current definition). Book ROIC is not charted (invested capital is near zero or negative after debt-funded buybacks); FCF conversion is shown instead.'),
        'B8': 'MIS contribution to growth (pp)', 'B9': 'MA contribution to growth (pp)', 'B12': 'Adjusted Operating Income', 'B13': 'Operating income (GAAP)',
        'B14': 'Adj. Operating Margin %', 'B15': 'GAAP Op. Margin %', 'B18': 'FCF conversion (FCF / adj. net income)', 'B19': 'Adj. EBITA margin %', 'B20': 'Adj. Operating Margin %', 'B21': 'FCF margin %',
    },
}
BBB_ROWS = {9: 'Revenue', 10: '   Revenue y/y %', 11: '   MIS revenue y/y %', 12: 'Adjusted Operating Income (= Adjusted EBITDA)', 13: '   Adjusted Operating Margin %',
            15: 'Operating Income (GAAP)', 16: '   Operating income y/y %', 17: '   Operating margin (GAAP) %', 19: "Adjusted Net Income (attributable to Moody's)",
            35: 'Adjusted Operating Income (leverage basis)', 36: '   Adjusted Operating Income % of revenue', 39: '   Net Debt / Adjusted Operating Income (x)',
            50: '   Implied EV / Adjusted Operating Income (x)'}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Revenue Growth: MIS vs. MA Contribution, pp',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted Operating Income &amp; Operating Income (USDm)',
    'Returns Profile: ROIC, RONTA, Adjusted EBITDA Margin &amp; FCF Margin': 'Returns Profile: FCF Conversion, Adj. EBITA Margin, Adj. Operating Margin &amp; FCF Margin',
}

def build_charts(ws):
    for i, y in enumerate(range(2011, 2031)):
        c = L(3 + i); mc = ANN[y].c
        ws[f'{c}7'] = y if y <= 2025 else f'{y}E'
        ws[f'{c}8'] = f'=IFERROR(Model!{mc}{R["gc_mis"]}+0,0)'
        ws[f'{c}9'] = f'=IFERROR(Model!{mc}{R["gc_ma"]}+0,0)'
        ws[f'{c}11'] = f'={c}7'
        ws[f'{c}12'] = f'=Model!{mc}{R["r_adj"]}'
        ws[f'{c}13'] = f'=Model!{mc}{R["is_oi"]}'
        ws[f'{c}14'] = f'=Model!{mc}{R["gm_ebitda_m"]}'
        ws[f'{c}15'] = f'=Model!{mc}{R["gm_op_m"]}'
        ws[f'{c}17'] = f'={c}7'
        ws[f'{c}18'] = f'=IFERROR(Model!{mc}{R["fcf_conv"]}+0,0)'
        ws[f'{c}19'] = f'=IFERROR(Model!{mc}{R["r_ebit_m"]}+0,0)'
        ws[f'{c}20'] = f'=IFERROR(Model!{mc}{R["gm_ebitda_m"]}+0,0)'
        ws[f'{c}21'] = f'=IFERROR(Model!{mc}{R["fcf_m"]}+0,0)'

def do_all(wb):
    for name in ('Bull-Base-Bear', 'DCF', 'Charts'):
        ws = wb[name]
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and 'Model!' in c.value:
                    c.value = remap(c.value)
        for addr, t in TEXT.get(name, {}).items():
            ws[addr] = t
    b = wb['Bull-Base-Bear']
    for r, t in BBB_ROWS.items():
        for c in ('B', 'N', 'Z'):
            if b[f'{c}{r}'].value is not None or r in (12, 19, 35): b[f'{c}{r}'] = t
    # BBB row 45 (RONTA): net tangible assets are negative for Moody's -> show ROE-free "n/m"-safe Adj. EBITA margin instead
    for c0 in ('C', 'O', 'AA'):
        i = b[f'{c0}7'].column
        b.cell(7, i).value = '2025A'
        for k in range(1, 6): b.cell(7, i + k).value = f'{2025 + k}E'
        b.cell(7, i + 6).value = "25-'30 CAGR"
    from openpyxl.comments import Comment
    cm = Comment("P/E on adjusted diluted EPS (company definition: excludes acquired-intangible amortization, restructuring and other items). MCO at $470 trades at ~28x FY2026E "
                 "adjusted EPS (~$16.75 guidance mid-point). Exit multiples are assumptions: Base 31x, Bull 35x, Bear 24x applied to 2028E–30E "
                 "(assumptions; the 2028E column was added to the Base and Bull panels).", 'MCO model')
    cm.width, cm.height = 420, 120; b['N26'].comment = cm
    cm2 = Comment(f'Snapshot (values) of Model rows {R["bb_cash"]}, {R["bb_px"]} and {R["bb_sh"]} (Share Buyback Schedule) with Model!{NOTE}2 = Bull / Bear. '
                  'Base panel (D40:H42) is live-linked.', 'MCO model')
    cm2.width, cm2.height = 420, 90; b['P40'].comment = cm2
    # the template's Base / Bull panels carry P/E rows for 2029E-30E only, so the 2028E implied-EV cells (F47:F50, R47:R50) read zero:
    # add the 2028E P/E rows so every panel values 2028E-30E (Bear already does)
    for col, pe in (('F', TEXT['Bull-Base-Bear']['G26']), ('R', TEXT['Bull-Base-Bear']['S26'])):
        b[f'{col}26'] = pe; b[f'{col}27'] = f'={col}26*{col}23'; b[f'{col}28'] = f'=IFERROR({col}27/$K$2-1,"")'
        b[f'{col}29'] = f'=IFERROR(({col}27/$K$2)^(1/((DATE(2028-1,12,31)-$K$3)/365.25))-1,"")'
        for r in (26, 27, 28, 29):
            src = b[f'{chr(ord(col) + 1)}{r}']
            b[f'{col}{r}']._style = src._style
    b['J2'] = 'Share price ($):'
    for c in ('B', 'N', 'Z'):
        if b[f'{c}40'].value: b[f'{c}40'] = '   Share repurchases ($m; 2026E = 2H)'
        if b[f'{c}45'].value: b[f'{c}45'] = 'RONTA (n/m where net tangible assets ≤ 0)'
    d = wb['DCF']
    a25 = ANN[2025].c
    d['D34'] = f'=Model!{a25}{R["ra_ic"]}'
    d['C45'] = '=SUM(E31:M31)'
    d['B45'] = 'Sum of PV (explicit 2027E–30E + fade; 2026E excluded)'
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
    (Charts!C:V = 2011-2030E) and cached values removed so Excel redraws from the MCO cells."""
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
