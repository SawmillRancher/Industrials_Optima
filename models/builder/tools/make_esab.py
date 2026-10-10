"""Assemble the ESAB workbook: Model + Bull-Base-Bear + DCF + Charts (template formats)."""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(__file__))
import openpyxl
from openpyxl.utils import get_column_letter as L
from openpyxl.chart import BarChart, LineChart, Reference
import esab_model as EM
from esab_model2 import build_rest

CFG = EM.CFG
lay = EM.lay
HIST_YEARS = list(range(2019, 2026))      # ESAB stand-alone history used for LT averages


def build_model(scenario='Base'):
    M, wb, ws, t = EM.build(scenario)
    build_rest(M)
    M.render()
    M.frame('ESAB Corporation (NYSE: ESAB) — 3-Statement Financial Model',
            'US GAAP as reported · USD millions (per-share data in USD; shares in millions) · Source: ESAB Forms 10-K / 10-Q, Form 10 information statement (10-12B/A, 17-Mar-2022; carve-out combined financial statements 2019–2021), Form 8-K earnings releases (Ex. 99.1) and Eddyfi deal 8-Ks / 8-K/A (Ex. 99.1–99.3), SEC EDGAR CIK 0001877322; pre-spin Colfax 10-K "Fabrication Technology" segment data 2012–2021 (CIK 0001420800) as memo',
            'Basis notes: calendar fiscal year (fiscal quarters end on the Friday nearest quarter end). Spun off from Colfax on 4-Apr-2022: 2019–Q1/22 carve-out (combined) basis, 2012–2018 Colfax segment memo only. Two reportable segments (Americas; EMEA & APAC). "Core" = excluding Russia (from Q2/22). Adjusted EBITDA / adjusted EPS = company definitions (restructuring, acquisition-amortization & other, separation costs 2022–23, pension settlements, performance option awards; MCPS if-converted). Eddyfi Technologies acquired 1-Jun-2026 ($1.45bn) — inside the segments in Q2/26 actuals, modelled separately from Q3/26E; FY26 outlook (6-Aug-2026) includes Eddyfi. Asbestos activity of divested Colfax businesses reported in discontinued operations.',
            None)
    ws.cell(2, M.lay.notes).value = scenario
    return M, wb, ws, t


def fy(y):
    return lay.fy[y].letter


def adapt_bbb(wb, M):
    ws = wb['Bull-Base-Bear']
    R = M.rows
    sw = f'Model!${L(lay.notes)}$2'
    rows = {9: 'is_sales', 11: 'gm_core_org', 12: 'aebitda', 13: 'aebitda_m', 15: 'is_oi', 17: 'gm_op_m', 19: 'core_adj_ni', 21: 'rB_sh',
            23: 'core_adj_eps', 31: 'fcf', 32: 'fcf_pct', 35: 'lev_ebitda', 36: None, 38: 'lev_nd', 40: 'bb_cash', 41: 'bb_px', 42: 'bb_sh',
            44: 'roic', 45: 'ronta'}
    cols = {3: 2025, 4: 2026, 5: 2027, 6: 2028, 7: 2029, 8: 2030}
    for r, key in rows.items():
        if key is None:
            continue
        for c, y in cols.items():
            if r in (40, 41, 42) and y == 2025:
                continue
            ws.cell(r, c).value = f'=Model!{fy(y)}{R[key]}'
    avg_rows = {13: 'aebitda_m', 17: 'gm_op_m', 32: 'fcf_pct', 36: 'aebitda_m', 44: 'roic', 45: 'ronta'}
    for r, key in avg_rows.items():
        refs = ','.join(f'Model!{fy(y)}{R[key]}' for y in HIST_YEARS)
        for c, fn in ((10, 'AVERAGE'), (11, 'MIN'), (12, 'MAX')):
            ws.cell(r, c).value = f'=IFERROR({fn}({refs}),"")'
    for c in range(3, 9):
        ws.cell(48, c).value = None
    for c, y in ((6, 2028), (7, 2029), (8, 2030)):
        ws.cell(48, c).value = f'={L(c)}38+Model!{fy(y)}{R["bs_nci"]}+Model!{fy(y)}{R["val_asb"]}'
    for c, y in ((18, 2028), (19, 2029), (20, 2030)):
        ws.cell(48, c).value = f'={L(c)}38+Model!{fy(y)}{R["bs_nci"]}+Model!{fy(y)}{R["val_asb"]}'
    for c, y in ((30, 2028), (31, 2029), (32, 2030)):
        ws.cell(48, c).value = f'={L(c)}38+Model!{fy(y)}{R["bs_nci"]}+Model!{fy(y)}{R["val_asb"]}'
    ws['C5'] = f'={sw}'
    ws['K2'] = f'=Model!${fy(2026)}${R["val_px"]}'
    ws['B2'] = 'ESAB Corporation (ESAB) — Bull / Base / Bear Case P&L Summary'
    ws['B3'] = ('Adjusted figures (company definitions: adjusted EBITDA; core adjusted net income / EPS excluding Russia, MCPS if-converted) · USD millions · Live panel linked to Model — toggle scenario via Model!'
                + sw.replace('Model!', '').replace('$', '') + '. Bull and Bear panels are value snapshots generated from the Model with the switch set to each case. 2026E includes Eddyfi from 1-Jun-2026; adjusted EBITDA for leverage / EV is pro forma for Eddyfi full year in 2026E.')
    labels = {9: 'Net sales', 10: '   Net sales y/y %', 11: '   Core organic growth % (ex-Russia)', 12: 'Adjusted EBITDA (company definition)',
              13: '   Adjusted EBITDA margin %', 15: 'Operating income (GAAP)', 16: '   Operating income y/y %', 17: '   Operating margin (GAAP) %',
              19: 'Core adjusted net income (continuing ops, ex-Russia)', 21: 'FDSO (m; incl. MCPS if-converted)', 23: 'Core adjusted EPS — Diluted ($)',
              35: 'Adjusted EBITDA — pro forma (2026E incl. Eddyfi full year)', 36: '   Adjusted EBITDA (pro forma) % of net sales'}
    for r, lbl in labels.items():
        for col in ('B', 'N', 'Z'):
            ws[f'{col}{r}'] = lbl
    for col, v in (('G', 16), ('H', 16), ('S', 19), ('T', 19), ('AD', 13), ('AE', 13), ('AF', 13)):
        ws[f'{col}26'] = v
    return ws


def adapt_dcf(wb, M):
    ws = wb['DCF']
    R = M.rows
    ws['B2'] = 'DCF VALUATION — ESAB CORPORATION (ESAB)'
    ws['C7'] = 1.2
    ws['D7'] = 'Welding / fabrication peers (Lincoln Electric, ITW, Kennametal) ~1.0–1.2; higher financial leverage post-Eddyfi (~3x) and Europe / emerging-market exposure → 1.2'
    ws['C9'] = 0.058
    ws['D9'] = 'BB-rated senior unsecured notes: 6.25% 2029, 5.625% 2031 (Mar-2026); TLA / revolver SOFR + 1.125–1.75%; marginal cost ~5.75–6.0%'
    ws['C10'] = CFG['etr']; ws['D10'] = 'Model 2027E+ effective tax rate'
    ws['C12'] = 0.35
    ws['D12'] = 'Net debt ~$2.1bn at YE2026E vs ~$4.3bn market cap ($69.94 × ~62m shares); target leverage < 3.0x YE26, ~2x medium term'
    ws['B18'] = 'Adj. EBITA less restructuring, transaction & integration costs (cash items)'
    ws['B21'] = 'plus depreciation & other amortization'
    ws['B22'] = '− Capex and acquisitions (M&A 2027E–30E)'
    for k, y in enumerate([2026, 2027, 2028, 2029, 2030]):
        col = L(4 + k); m = fy(y)
        ws[f'{col}18'] = f'=Model!{m}{R["aebita"]}-Model!{m}{R["is_restr"]}-Model!{m}{R["txn"]}'
        ws[f'{col}21'] = f'=Model!{m}{R["da_oth"]}'
        ws[f'{col}22'] = f'=Model!{m}{R["capex"]}' if y == 2026 else f'=Model!{m}{R["capex"]}+Model!{m}{R["cf_acq"]}'
        ws[f'{col}23'] = f'=Model!{m}{R["cf_wc"]}'
    ws['I22'] = f'=Model!{fy(2030)}{R["capex"]}*(1+I$26)'
    ws['B26'] = 'Fade-period growth (2031E–35E; 6% → 4.5% linear)'
    ws['I26'] = 0.06; ws['M26'] = 0.045
    ws['C27'] = 0.035
    ws['D32'] = ("ESAB-specific: adjusted EBITA excludes amortization of acquired intangibles (Eddyfi PPA ~$58m p.a.) and the performance option awards; NOPAT is struck on adjusted EBITA "
                 "less cash restructuring and integration costs (row 18). Eddyfi cash consideration (closed 1-Jun-2026) sits in YE2026E net debt, not in UFCF. Acquisition spend from the M&A lever is deducted in 2027E–30E. "
                 "Asbestos liabilities of divested Colfax businesses (net of insurance, ~$55m) are deducted as a debt-like item; MCPS conversion shares are included in the diluted share count.")
    ws['D34'] = f'=Model!{fy(2025)}{R["ic"]}+Model!{fy(2026)}{R["ppa_cons"]}'
    ws['D43'] = 'Opening IC = Model 2025A book invested capital (equity + net debt) + Eddyfi consideration ($1.49bn), rolled forward with capex + M&A − D&A + ΔWC.'
    ws['C48'] = f'=Model!{fy(2026)}{R["lev_nd"]}+Model!{fy(2026)}{R["bs_nci"]}+Model!{fy(2026)}{R["val_asb"]}'
    ws['B48'] = 'Less: Net debt + NCI + net asbestos (Model 2026E YE, post-Eddyfi)'
    ws['D48'] = 'ESAB-specific: NCI (~$40m) and net asbestos liabilities (~$55m) deducted alongside net debt; YE2026E net debt includes the Eddyfi purchase price.'
    ws['B50'] = 'Diluted shares (m, Model 2026E incl. MCPS conversion shares)'
    ws['C50'] = f'=Model!{fy(2026)}{R["val_sh"]}'
    ws['C52'] = f'=Model!{fy(2026)}{R["val_px"]}'
    ws['C78'] = 0.10
    ws['D78'] = 'Model adjusted EBITA CAGR 2026–30E: low/mid-single-digit organic growth, Eddyfi high-single-digit growth and synergies, EBXai margin expansion, deleveraging → ~10% NOPAT growth'
    ws['C79'] = 0.18
    ws['D79'] = 'Consumables-heavy welding franchise (~60% of sales) and gas control earn high returns on organic capital; acquired growth (Eddyfi ~18x EBITDA) earns ~5–6% after tax on purchase price initially'
    ws['C80'] = 12
    ws['D80'] = 'Global #2 in welding & cutting; installed base and consumables pull-through; EBXai continuous-improvement system; workflow extension into inspection / monitoring (Eddyfi); Russia and Europe cyclicality offset'
    ws['B91'] = '2028E Adj. EBITA less restructuring & integration costs'
    ws['C91'] = f'=Model!{fy(2028)}{R["aebita"]}-Model!{fy(2028)}{R["is_restr"]}-Model!{fy(2028)}{R["txn"]}'
    ws['B96'] = 'Less: YE2027 net debt + NCI + net asbestos (Model)'
    ws['C96'] = f'=Model!{fy(2027)}{R["lev_nd"]}+Model!{fy(2027)}{R["bs_nci"]}+Model!{fy(2027)}{R["val_asb"]}'
    ws['C98'] = f'=Model!{fy(2028)}{R["val_sh"]}'
    ws['B106'] = 'Plus: YE2026 net debt + NCI + net asbestos'
    ws['B108'] = 'ESAB market-implied EV/NOPAT (on 2028E NOPAT)'
    ws['B90'] = 'VALUATION  —  Applied to 2028E NOPAT'
    for r in range(1, ws.max_row + 1):
        for c in range(1, ws.max_column + 1):
            v = ws.cell(r, c).value
            if isinstance(v, str) and ('Martin Marietta' in v or 'MLM' in v or 'LNA' in v):
                ws.cell(r, c).value = v.replace('Martin Marietta Materials', 'ESAB').replace('Martin Marietta', 'ESAB').replace('MLM', 'ESAB').replace('LNA', 'Eddyfi')
    return ws


def adapt_charts(wb, M):
    ws = wb['Charts']
    R = M.rows
    years = list(range(2012, 2026))
    for r in range(7, 22):
        for c in range(2, 23):
            ws.cell(r, c).value = None
    ws['B2'] = 'ESAB — Historical Operating Performance (2012–2025; 2012–2018 = Colfax "Fabrication Technology" segment)'
    ws['B3'] = ('USDm · Linked to Model. 2012–2018: pre-spin Colfax segment data (organic / acquisitions / FX and segment operating income); 2019–2025: ESAB carve-out / stand-alone reporting '
                '(adjusted EBITDA per company reconciliations). Not strictly comparable across the two bases.')
    for k, y in enumerate(years):
        ws.cell(7, 3 + k).value = y; ws.cell(7, 3 + k)._style = ws['C6']._style if False else ws.cell(7, 3 + k)._style
        for rr in (11, 17):
            ws.cell(rr, 3 + k).value = f'={L(3 + k)}7'
    rows = {8: ('Organic growth %', lambda m: f'=IFERROR(Model!{m}{R["gm_org"]}+0,IFERROR(Model!{m}{R["cfx_organic_pct"]}+0,0))'),
            9: ('Acquisitions %', lambda m: f'=IFERROR(Model!{m}{R["gm_acq"]}+0,IFERROR(Model!{m}{R["cfx_acquisitions_pct"]}+0,0))'),
            10: ('Foreign currency %', lambda m: f'=IFERROR(Model!{m}{R["gm_fx"]}+0,IFERROR(Model!{m}{R["cfx_fx_pct"]}+0,0))'),
            12: ('Adjusted EBITDA (ESAB, 2019+)', lambda m: f'=IFERROR(Model!{m}{R["aebitda"]}+0,NA())'),
            13: ('Operating income (GAAP, 2019+)', lambda m: f'=IFERROR(Model!{m}{R["is_oi"]}+0,NA())'),
            14: ('Adj. EBITDA margin %', lambda m: f'=IFERROR(Model!{m}{R["aebitda_m"]}+0,NA())'),
            15: ('GAAP Op. margin %', lambda m: f'=IFERROR(Model!{m}{R["gm_op_m"]}+0,NA())'),
            16: ('Colfax Fab. Tech. segment op. income (pre-spin)', lambda m: f'=IFERROR(Model!{m}{R["cfx_segment_operating_income"]}+0,NA())'),
            18: ('ROIC', lambda m: f'=IFERROR(Model!{m}{R["roic"]}+0,NA())'),
            19: ('RONTA', lambda m: f'=IFERROR(Model!{m}{R["ronta"]}+0,NA())'),
            20: ('Adj. EBITDA margin %', lambda m: f'=IFERROR(Model!{m}{R["aebitda_m"]}+0,NA())'),
            21: ('FCF margin %', lambda m: f'=IFERROR(Model!{m}{R["fcf_pct"]}+0,NA())')}
    for r, (lbl, f) in rows.items():
        ws.cell(r, 2).value = lbl
        for k, y in enumerate(years):
            cell = ws.cell(r, 3 + k)
            cell.value = f(fy(y))
            cell.number_format = '0.0%;\\(0.0%\\);\\-' if ('%' in lbl or r >= 18) else '#,##0;\\(#,##0\\);\\-'
            src = ws.cell(r if r in (8, 9, 12, 13, 14, 15, 18, 19, 20, 21) else 8, 3)
    last = 2 + len(years)
    cats = Reference(ws, min_col=3, max_col=last, min_row=7)
    c1 = BarChart(); c1.type = 'col'; c1.grouping = 'stacked'; c1.overlap = 100
    c1.title = 'Sales Drivers: Organic vs. Acquisitions vs. FX, y/y %'
    for r, color in ((8, '2F3E46'), (9, '84A98C'), (10, 'A8C5D6')):
        c1.add_data(Reference(ws, min_col=2, max_col=last, min_row=r), titles_from_data=True, from_rows=True)
        c1.series[-1].graphicalProperties.solidFill = color
    c1.set_categories(cats); c1.y_axis.numFmt = '0%'; c1.height = 7.5; c1.width = 24; c1.legend.position = 'b'
    ws.add_chart(c1, 'B23')
    c2 = BarChart(); c2.type = 'col'; c2.grouping = 'clustered'; c2.title = 'Adjusted EBITDA & Operating Income (USDm)'
    for r, color in ((12, 'A8C5D6'), (13, '1F4E79'), (16, '878787')):
        c2.add_data(Reference(ws, min_col=2, max_col=last, min_row=r), titles_from_data=True, from_rows=True)
        c2.series[-1].graphicalProperties.solidFill = color
    c2.set_categories(cats)
    l2 = LineChart()
    for r, color in ((14, '2F3E46'), (15, 'C8553D')):
        l2.add_data(Reference(ws, min_col=2, max_col=last, min_row=r), titles_from_data=True, from_rows=True)
        l2.series[-1].graphicalProperties.line.solidFill = color
    l2.y_axis.axId = 200; l2.y_axis.numFmt = '0%'; l2.y_axis.crosses = 'max'
    c2 += l2; c2.height = 7.5; c2.width = 24; c2.legend.position = 'b'
    ws.add_chart(c2, 'B44')
    c3 = LineChart(); c3.title = 'Returns Profile: ROIC, RONTA, Adjusted EBITDA Margin & FCF Margin'
    for r, color in ((18, '2F3E46'), (19, '84A98C'), (20, '1F4E79'), (21, 'C8553D')):
        c3.add_data(Reference(ws, min_col=2, max_col=last, min_row=r), titles_from_data=True, from_rows=True)
        c3.series[-1].graphicalProperties.line.solidFill = color
    c3.set_categories(cats); c3.y_axis.numFmt = '0%'; c3.height = 7.5; c3.width = 24; c3.legend.position = 'b'
    ws.add_chart(c3, 'B65')


def finalize(wb, ws_new):
    del wb['Model']; del wb['DCF_old']
    ws_new.title = 'Model'
    wb._sheets = [wb[n] for n in ['Model', 'Bull-Base-Bear', 'DCF', 'Charts']]
    wb.active = 0
    wb.calculation.fullCalcOnLoad = True


def make(path, scenario='Base'):
    M, wb, ws, t = build_model(scenario)
    adapt_bbb(wb, M); adapt_dcf(wb, M); adapt_charts(wb, M)
    finalize(wb, ws)
    wb.save(path)
    return M


if __name__ == '__main__':
    M = make(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'Base')
    json.dump(M.rows, open(sys.argv[1] + '.rows.json', 'w'))
    print('rows', M.r)
