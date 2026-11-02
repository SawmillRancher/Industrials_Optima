"""Rewire the Bull-Base-Bear, DCF (10-year + fade version) and Charts tabs of the MLM template to the THEON Model rows / columns;
replace every template text and comment; keep the template chart XML. The template's legacy DCF_old tab is removed."""
import re, zipfile, shutil
from openpyxl.utils import get_column_letter as L
from openpyxl.comments import Comment
from fw import R, TEMPLATE, ANN, NOTE

# template Model row -> THEON row key (per sheet where the meaning differs)
MAP_COMMON = {158: 'is_rev', 164: 'd_nri', 166: 'is_op', 182: 'is_dda', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 219: 'r_ebit', 221: 'r_adj',
              229: 'e_adjni', 231: 'e_eps', 238: 'gm_cc', 245: 'r_adj_m', 247: 'gm_op_m', 260: 'cf_wc', 262: 'cf_capex', 263: 'cf_acq',
              280: 'fcf', 282: 'fcf_m', 290: 'bb_px', 291: 'bb_cash', 292: 'bb_sh', 331: 'v_nci', 408: 'ra_ic', 411: 'ra_roic', 422: 'rn_ronta',
              433: 'v_px', 434: 'v_sh', 353: 'me_px', 355: 'hg_ev'}
MAP_SHEET = {'Bull-Base-Bear': {428: 'lv_nd'}, 'DCF': {428: 'v_ndx'}}
CMAP = {'BV': ANN[2025].c, 'CA': ANN[2026].c, 'CB': ANN[2027].c, 'CC': ANN[2028].c, 'CD': ANN[2029].c, 'CE': ANN[2030].c, 'CF': NOTE}
REF = re.compile(r"Model!(\$?)([A-Z]{1,3})(\$?)(\d+)")
HIST_ANN = [ANN[y].c for y in range(2021, 2026)]

def remap(f, sheet):
    mp = dict(MAP_COMMON); mp.update(MAP_SHEET.get(sheet, {}))
    def rep(m):
        c, r = m.group(2), int(m.group(4))
        if c == 'CF' and r == 2: return f'Model!{m.group(1)}{NOTE}{m.group(3)}2'
        if r not in mp and r > 7 and sheet != 'Charts': raise KeyError(f'{sheet}: template Model row {r} not mapped ({f})')
        return f'Model!{m.group(1)}{CMAP.get(c, c)}{m.group(3)}{R[mp[r]] if r in mp else r}'
    return REF.sub(rep, f)

def M(key, y): return f'Model!{ANN[y].c}{R[key]}'

BBB_LAB = {9: 'Revenue (EUR m)', 10: '   Revenue y/y %', 11: '   Existing-portfolio (organic) growth %',
           12: 'Adjusted EBITDA (company definition)', 13: '   Adjusted EBITDA margin %', 15: 'Operating Profit (IFRS)',
           16: '   Operating profit y/y %', 17: '   Operating margin (IFRS) %', 19: 'Adjusted Net Income (model: ex non-recurring & FVTPL gains)',
           21: 'Weighted-average shares (m)', 23: 'Adjusted EPS (model, EUR)', 26: 'P / E (x) — assumed (model adjusted EPS)',
           27: 'Price Target (EUR)', 35: 'Adjusted EBITDA (leverage basis)', 36: '   Adjusted EBITDA (leverage basis) % of revenue',
           38: 'Net Debt (negative = net cash)', 39: '   Net Debt / Adjusted EBITDA (x)', 40: '   Share buybacks (EUR m)',
           41: '   Implied avg buyback price (EUR)', 42: '   Shares repurchased (m)', 47: 'Implied Market Cap (EUR m)', 48: '(+) Net Debt − investments & NCI',
           49: 'Implied Enterprise Value (EUR m)', 50: 'Implied EV / Adjusted EBITDA (x)'}

PE_NOTE = ('P/E on the model adjusted EPS (IFRS EPS ex non-recurring items and ex fair-value gains on the Exosens / Kopin stakes). At EUR 29.84, THEON trades at c.24x '
           '2026E model adjusted EPS. European defence-electronics peers (Hensoldt, Exosens, Thales, Rheinmetall) have traded at c.20–35x forward earnings in 2025–26. '
           'Base 24x, Bull 28x, Bear 18x (assumption).')
SNAP_NOTE = ('Snapshot (values) of the Model share-schedule rows (buybacks, price, shares) with the switch Model!{sw} set to the case named in the panel header, '
             'captured by build.py --snap. The Base panel is live-linked to the Model.')

TEXT = {
    'Bull-Base-Bear': {
        'B2': 'Theon International (THEON) — Bull / Base / Bear Case P&L Summary',
        'B3': ('Adjusted figures (company adjusted EBIT / EBITDA, current definition incl. share of core associates; adjusted EPS = model definition) · EUR millions · '
               'Live panel linked to Model — toggle scenario via Model!AC2. Bull and Bear panels are value snapshots generated from the Model with the switch set to each case. '
               'Guidance inputs come from company releases (unverified — not on EDGAR).'),
        'J2': 'Share price (EUR):',
        'F26': 24, 'G26': 24, 'H26': 24, 'R26': 28, 'S26': 28, 'T26': 28, 'AD26': 18, 'AE26': 18, 'AF26': 18,
        'B7': '(EURm, except EPS and shares)', 'N7': '(EURm, except EPS and shares)', 'Z7': '(EURm, except EPS and shares)',
    },
    'DCF': {
        'B2': 'DCF VALUATION — THEON INTERNATIONAL PLC (THEON)',
        'B5': 'Risk-free rate (German 10Y Bund)', 'C5': 0.027, 'D5': 'Assumption (~German 10Y Bund yield, EUR cash flows); update to market',
        'C6': 0.055, 'D6': 'Euro-area implied ERP ~5–6% (Damodaran); small/mid-cap, founder-controlled (CHRE / Venetus c.60%)',
        'C7': 1.10, 'D7': 'European defence-electronics peers (Hensoldt, Exosens, Thales, Rheinmetall, Elbit) ~0.8–1.3; customer concentration (OCCAR / Bundeswehr 38% of FY25 revenue) and order lumpiness',
        'C9': 0.045, 'D9': 'RCF at 1M Euribor + 1.5% plus fees; HGH term loan; marginal cost ~4–5% (assumption)',
        'C10': 0.23, 'D10': 'Model 2027E+ effective tax rate (Greek 22% statutory)',
        'C12': 0.15, 'D12': 'Target D/V ~15%: post-HGH net debt c.EUR 0.5–0.6bn vs ~EUR 2.3bn market cap; company leverage c.3.0x pro forma → c.2.5x by 2027 (unverified)',
        'B16': '2. UNLEVERED FREE CASH FLOW BUILD (EURm)',
        'B18': 'Adj. EBIT less non-recurring (cash) items',
        'B21': 'plus D&A (incl. Kappa / HGH purchase-price amortisation)',
        'B22': '− Capex and acquisitions (MERIO 2026E, HGH 2027E, bolt-ons 2028E–30E)',
        'B23': '− Δ Working capital (CF statement; fade: scaled to the fading growth rate)',
        'B26': 'Fade-period growth (2031E–35E; 9% → 4% linear)', 'I26': 0.09, 'M26': 0.04, 'C27': 0.025,
        'D32': ('THEON adjusted EBIT is full-cost (after all D&A incl. purchase-price amortisation; THEON has no SBC add-back). UFCF = (adjusted EBIT − non-recurring '
                'cash costs) × (1 − t) + D&A − capex − acquisitions − ΔWC. Fair-value gains on the Exosens / Kopin stakes are excluded from UFCF; the stakes are '
                'deducted at carrying value in the equity bridge (non-operating). Leases are in net debt (immaterial, < EUR 5m). Fade period (2031E–35E): '
                'capex only (acquisitions in the explicit years only) and ΔWC scaled to the fading growth rate (NWC c.40% of revenue makes growth cash-hungry).'),
        'B33': 'IMPLIED ROIC — invested capital roll-forward (EURm)',
        'D43': ('Opening IC = Model 2025A invested capital (equity + net debt − non-operating investments) + Kappa (EUR 62.8m, H1-26 business combinations net of cash) + '
                'MERIO (2026E, assumed EUR 37.5m); HGH (2027E) and bolt-ons flow through row 22. Exosens / associates are non-operating and excluded. Rolled forward with '
                'capex + M&A − D&A + ΔWC.'),
        'B48': 'Less: Net debt − non-operating investments + NCI (Model 2026E YE)',
        'D48': 'YE2026E net debt (RCF EUR 300m drawn, post Exosens / Kappa / MERIO) less the Exosens, Kopin and associate stakes at carrying value; plus Harder Digital NCI at book.',
        'B50': 'Shares outstanding (m, Model 2026E)', 'B51': 'Implied share price (EUR)', 'B52': 'Current share price (EUR)',
        'B55': 'Max entry price for target IRR (EUR)', 'B58': '4. SENSITIVITY: IMPLIED PRICE (EUR) — WACC × Terminal Growth',
        'B70': ('To solve for the market-implied path: Data ▸ What-If Analysis ▸ Goal Seek — set C51 to the current price (C52) by changing C27 (terminal growth), '
                'the fade-period growth inputs (I26:M26) or the Model scenario levers (product-line growth, adjusted EBIT margin, HGH, bolt-on M&A).'),
        'D76': 'Rationale (THEON characteristics)',
        'C78': 0.15, 'D78': 'Model adjusted EBIT CAGR 2026–30E: >15% organic growth target, HGH (2027E) and bolt-ons at a stable mid-twenties margin → ~15% NOPAT growth',
        'C79': 0.30, 'D79': 'Asset-light assembly model (capex c.4% of revenue) with high working-capital intensity (NWC c.40% of revenue); 2025 ROIC >30% on adjusted EBIT',
        'C80': 10, 'D80': ('European night-vision leader (220,000+ systems, 71 countries); long-term tube supply (Exosens to 2030, Harder Digital) and OCCAR framework orders; '
                           're-armament cycle visibility to ~2029, then normalisation risk'),
        'B91': '2028E Adj. EBIT less non-recurring items', 'B96': 'Less: YE2027 net debt − investments + NCI (Model)',
        'B98': 'Shares outstanding 2028E (m, Model)', 'B99': 'Implied share price 2028 (EUR)', 'B101': 'Current share price (EUR)',
        'B108': 'THEON market-implied EV/NOPAT (on 2028E NOPAT)', 'C90': 'EURm', 'C104': 'EURm',
    },
    'Charts': {
        'B2': 'Theon International — Operating Performance (2021–2025) and Model Forecast (2026E–2030E)',
        'B3': ('EURm · Linked to Model. Bars = existing-portfolio (organic) growth vs acquired / deal contribution (Harder Digital from Oct-2024, Kappa from Jan-2026 inside the existing '
               'portfolio; MERIO, HGH and bolt-ons as deal contribution). Adjusted EBIT / EBITDA on the current company definition. ROIC / RONTA on adjusted EBIT (annual).'),
        'B8': 'Existing-portfolio growth %', 'B9': 'Deal contribution %', 'B12': 'Adjusted EBITDA', 'B13': 'Operating Profit (IFRS)',
        'B14': 'Adj. EBITDA Margin %', 'B15': 'IFRS Op. Margin %',
    },
}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Revenue Growth: Existing Portfolio vs. Deal Contribution, y/y %',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted EBITDA &amp; Operating Profit (EURm)',
}
YEARS = list(range(2021, 2031))
LASTCH = L(2 + len(YEARS))          # L

def build_charts(ws):
    for i, y in enumerate(YEARS):
        c = L(3 + i); mc = ANN[y].c
        ws[f'{c}7'] = y if y <= 2025 else f'{y}E'
        ws[f'{c}8'] = f'=IFERROR(Model!{mc}{R["gm_cc"]}+0,0)'
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
        ws[f'{c}21'] = f'=IFERROR(Model!{mc}{R["fcf_m"]}+0,NA())' if y > 2021 else None   # FY2021: no cash-flow statement used
    for ci in range(3 + len(YEARS), 23):
        for r in range(7, 22):
            ws.cell(r, ci).value = None

def lt_hist(ws):
    """LT Hist Avg / Min / Max (J:L) on THEON annual history 2021–2025."""
    for r, key in ((13, 'r_adj_m'), (17, 'gm_op_m'), (32, 'fcf_m'), (36, 'r_adj_m'), (44, 'ra_roic'), (45, 'rn_ronta')):
        refs = ','.join(f'Model!{c}{R[key]}' for c in HIST_ANN)
        for col, fn in (('J', 'AVERAGE'), ('K', 'MIN'), ('L', 'MAX')):
            ws[f'{col}{r}'] = f'=IFERROR({fn}({refs}),"")'

def generic_text(v):
    v = v.replace('($)', '(EUR)').replace('USDm', 'EURm').replace('USD m', 'EUR m').replace('(USD', '(EUR')
    return v

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
                elif isinstance(v, str):
                    c.value = generic_text(v)
                if c.comment is not None:
                    c.comment = None
        for addr, t in TEXT.get(name, {}).items():
            ws[addr] = t
    b = wb['Bull-Base-Bear']
    for r, t in BBB_LAB.items():
        for col in ('B', 'N', 'Z'): b[f'{col}{r}'] = t
    for addr in ('B26', 'N26', 'Z26'):
        cm = Comment(PE_NOTE, 'THEON model'); cm.width, cm.height = 420, 160; b[addr].comment = cm
    for addr in ('P40', 'AB40'):
        cm = Comment(SNAP_NOTE.format(sw=f'{NOTE}2'), 'THEON model'); cm.width, cm.height = 420, 120; b[addr].comment = cm
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
        d[f'{col}18'] = f'={M("r_ebit", y)}-{M("d_nri", y)}'
        d[f'{col}22'] = f'={M("cf_capex", y)}' if y == 2026 else f'={M("cf_capex", y)}+{M("cf_acq", y)}'
    # fade / terminal: capex only (M&A in the explicit years only), working-capital investment scaled to the fading growth rate
    d['I22'] = f'=Model!{ANN[2030].c}{R["cf_capex"]}*(1+I$26)'
    d['I23'] = f'=IFERROR(H23*(1+Model!{ANN[2030].c}{R["gm_rev"]})*I$26/Model!{ANN[2030].c}{R["gm_rev"]},H23*(1+I$26))'
    for c, pc in zip('JKLM', 'IJKL'):
        d[f'{c}23'] = f'=IFERROR({pc}23*(1+{pc}$26)*{c}$26/{pc}$26,{pc}23*(1+{c}$26))'
    d['P24'] = '=IFERROR((H24/E24)^(1/(COLUMNS(E24:H24)-1))-1,"n/m")'
    d['O24'] = 'CAGR 27–30E'
    # FY2026 is ~10/12 complete at the valuation date and the bridge uses YE2026 net debt: exclude 2026E UFCF (BWXT / CW / WWD rule)
    d['C45'] = '=SUM(E31:M31)'
    d['B45'] = 'Sum of PV (explicit 2027E–30E + fade; 2026E excluded — in YE2026 net debt)'
    d['D34'] = f'={M("ra_ic", 2025)}+62.838507+{M("me_px", 2026)}'
    d['C91'] = f'={M("r_ebit", 2028)}-{M("d_nri", 2028)}'

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
    re-ranged to Charts!C:L (2021–2030E) and with cached values removed so Excel redraws from the THEON cells."""
    tz = zipfile.ZipFile(TEMPLATE)
    tmpl = {n: tz.read(n) for n in tz.namelist() if n.startswith('xl/charts/chart')}
    tmp = path + '.tmp'
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in tmpl:
                t = tmpl[item.filename].decode('utf-8')
                for a, b2 in CHART_TITLES.items(): t = t.replace(a, b2)
                t = t.replace('(USDm)', '(EURm)').replace('USDm', 'EURm')
                t = re.sub(r'(Charts!\$C\$\d+:\$)V(\$\d+)', r'\g<1>' + LASTCH + r'\2', t)
                t = re.sub(r'<c:numCache>.*?</c:numCache>', '', t, flags=re.S)
                t = re.sub(r'<c:strCache>.*?</c:strCache>', '', t, flags=re.S)
                data = t.encode('utf-8')
            zout.writestr(item, data)
    shutil.move(tmp, path)
