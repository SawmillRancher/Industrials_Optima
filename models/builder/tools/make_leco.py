"""Assemble the LECO workbook: Model + Bull-Base-Bear + DCF + Charts (template formats)."""
import sys, os, re, copy, json
sys.path.insert(0, os.path.dirname(__file__))
import openpyxl
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.drawing.line import LineProperties
from openpyxl.chart.layout import Layout as CLayout, ManualLayout
import leco_model as LM
from leco_model2 import build_rest

CFG = LM.CFG


def build_model(scenario='Base'):
    M, wb, ws, t = LM.build(None)
    build_rest(M)
    M.render()
    M.frame('Lincoln Electric Holdings, Inc. (Nasdaq: LECO) — 3-Statement Financial Model',
            'US GAAP as reported · USD millions (per-share data in USD; shares in millions) · Source: Lincoln Electric Forms 10-K / 10-Q and Form 8-K earnings releases (Ex. 99.1), segment-recast 8-K (10-Feb-2016), SEC EDGAR CIK 0000059527 (investor-relations releases are the same documents as filed on EDGAR); XBRL company facts used to cross-check totals',
            'Basis notes: calendar fiscal year. Three reportable segments (Americas Welding, International Welding, The Harris Products Group) from Q1/16, recast for FY2013 and 2014–15 quarters (no 2013 quarterly recast); five legacy segments (North America / Europe / Asia Pacific / South America Welding + Harris) 2009–2015 and North America / Europe / Other Countries 2006–2008 shown as memo. Per-share data 2006–2010 restated for the 2-for-1 split (May-2011). Venezuela deconsolidated Q4/15. Adjusted measures = company definitions (special items: rationalization & asset impairments, acquisition costs & inventory step-up, pension settlements, Venezuela, disposal gains, discrete tax items). FY26 outlook per the Q2-26 call (30-Jul-2026).',
            None)
    ws.cell(2, M.lay.notes).value = scenario
    return M, wb, ws, t


def remap_formula(f, rowmap):
    def rep(m):
        col, row = m.group(2), int(m.group(4))
        if row in rowmap:
            row = rowmap[row]
        return f'Model!{m.group(1)}{col}{m.group(3)}{row}'
    return re.sub(r'Model!(\$?)([A-Z]{1,3})(\$?)(\d+)', rep, f)


def adapt_bbb(wb, M):
    ws = wb['Bull-Base-Bear']
    R = M.rows
    rowmap = {158: R['is_sales'], 238: R['gm_org'], 211: R['aebit'], 212: R['aebit_m'], 166: R['is_oi'], 247: R['gm_op_m'],
              229: R['adj_ni'], 186: R['sh_d'], 231: R['adj_eps'], 280: R['fcf'], 282: R['fcf_pct'], 221: R['aebitda'],
              245: R['aebitda_m'], 428: R['lev_nd'], 291: R['bb_cash'], 290: R['bb_px'], 292: R['bb_sh'], 411: R['roic'],
              422: R['ronta'], 331: R['bs_nci'], 433: R['val_px']}
    sw = f'Model!${openpyxl.utils.get_column_letter(M.lay.notes)}$2'
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and c.value.startswith('='):
                v = remap_formula(c.value, rowmap)
                v = v.replace('Model!$CF$2', sw)
                c.value = v
    ws['B2'] = 'Lincoln Electric (LECO) — Bull / Base / Bear Case P&L Summary'
    ws['B3'] = ('Adjusted figures (company definitions: adjusted EBIT / adjusted net income / adjusted diluted EPS) · USD millions · Live panel linked to Model — toggle scenario via Model!'
                + sw.replace('Model!', '').replace('$', '') + '. Bull and Bear panels are value snapshots generated from the Model with the switch set to each case. Adjusted EBITDA is a model measure (adjusted EBIT + D&A).')
    labels = {9: 'Net sales', 10: '   Net sales y/y %', 11: '   Organic sales growth % (volume + price)', 12: 'Adjusted EBIT (company definition)',
              13: '   Adjusted EBIT margin %', 15: 'Operating income (GAAP)', 16: '   Operating income y/y %', 17: '   Operating margin (GAAP) %',
              19: 'Adjusted net income (attributable to Lincoln Electric)', 21: 'FDSO (m)', 23: 'Adjusted EPS — Diluted ($)',
              35: 'Adjusted EBITDA (model: adjusted EBIT + D&A)', 36: '   Adjusted EBITDA % of net sales'}
    for r, lbl in labels.items():
        for col in ('B', 'N', 'Z'):
            ws[f'{col}{r}'] = lbl
    for col, v in (('G', 22), ('H', 22), ('S', 25), ('T', 25), ('AD', 18), ('AE', 18), ('AF', 18)):
        ws[f'{col}26'] = v
    return ws


def snapshot_bbb(wb, values_bull, values_bear):
    """values_*: dict row -> list of 11 values for columns C..L (2025A..LT max)"""
    ws = wb['Bull-Base-Bear']
    for vals, start in ((values_bull, 15), (values_bear, 27)):  # N=14 -> O=15 ; Z=26 -> AA=27
        for r, lst in vals.items():
            for k, v in enumerate(lst):
                cell = ws.cell(r, start + k)
                if v is None:
                    continue
                cell.value = v


def adapt_dcf(wb, M):
    ws = wb['DCF']
    R = M.rows
    L = openpyxl.utils.get_column_letter
    fy = {y: M.lay.fy[y].letter for y in M.lay.fy}
    ws['B2'] = 'DCF VALUATION — LINCOLN ELECTRIC HOLDINGS (LECO)'
    ws['C7'] = 1.1
    ws['D7'] = 'Diversified industrials / welding peers (ESAB, ITW, Kennametal, Snap-on) ~1.0–1.2; short-cycle industrial capex exposure, partly offset by consumables (~2/3 of welding sales) and automation growth'
    ws['C9'] = 0.055
    ws['D9'] = 'Investment-grade private-placement notes (2024 Notes priced at 5.55%–5.74%); marginal cost ~5.5%'
    ws['C10'] = CFG['etr']
    ws['D10'] = 'Model 2027E+ effective tax rate'
    ws['C12'] = 0.08
    ws['D12'] = 'Net debt ~$0.9bn at YE2026E vs ~$15bn market cap ($275.54 × ~54m shares); LECO runs ~0.5–1.0x net leverage'
    ws['B18'] = 'Adj. EBIT less rationalization & transaction costs (cash special items)'
    ws['B21'] = 'plus D&A'
    ws['B22'] = '− Capex and acquisitions (M&A 2027E–30E)'
    years = [2026, 2027, 2028, 2029, 2030]
    for k, y in enumerate(years):
        col = L(4 + k)
        m = fy[y]
        ws[f'{col}18'] = f'=Model!{m}{R["aebit"]}-Model!{m}{R["eb_rat"]}-Model!{m}{R["eb_txn"]}'
        ws[f'{col}21'] = f'=Model!{m}{R["da"]}'
        ws[f'{col}22'] = f'=Model!{m}{R["capex"]}' if y == 2026 else f'=Model!{m}{R["capex"]}+Model!{m}{R["cf_acq"]}'
        ws[f'{col}23'] = f'=Model!{m}{R["cf_wc"]}'
    ws['I22'] = f'=Model!{fy[2030]}{R["capex"]}*(1+I$26)'
    ws['B26'] = 'Fade-period growth (2031E–35E; 6% → 4.5% linear)'
    ws['I26'] = 0.06; ws['M26'] = 0.045
    ws['C27'] = 0.035
    ws['D32'] = ("LECO-specific: Lincoln Electric's adjusted EBIT expenses stock-based compensation and includes all amortization of acquired intangibles "
                 "(no amortization add-back in the company's adjusted measures). Rationalization and acquisition transaction costs are cash costs and are deducted in row 18 "
                 "(Model adjusted EBIT less those special items). Acquisition spend from the M&A lever is deducted in 2027E–30E; the fade period and terminal value assume no new acquisitions. "
                 "Pension non-service items sit in other income (outside adjusted EBIT). Operating-lease costs are inside operating income.")
    ws['D34'] = f'=Model!{fy[2025]}{R["ic"]}'
    ws['D43'] = 'Opening IC = Model 2025A book invested capital (total equity + net debt), rolled forward with capex + M&A − D&A + ΔWC.'
    ws['C48'] = f'=Model!{fy[2026]}{R["lev_nd"]}+Model!{fy[2026]}{R["bs_nci"]}'
    ws['B48'] = 'Less: Net debt + NCI (Model 2026E YE)'
    ws['D48'] = 'LECO has no noncontrolling interests since 2023 (Model row shown for completeness).'
    ws['B50'] = 'Diluted shares (m, Model 2026E)'
    ws['C50'] = f'=Model!{fy[2026]}{R["val_sh"]}'
    ws['C52'] = f'=Model!{fy[2026]}{R["val_px"]}'
    ws['D77'] = 'Linked from Section 1 WACC build'
    ws['C78'] = 0.07
    ws['D78'] = 'Model adjusted EBIT CAGR 2026–30E: low/mid-single-digit organic growth (volume recovery + price), automation mix, bolt-on M&A and buybacks → ~7% NOPAT growth'
    ws['C79'] = 0.25
    ws['D79'] = 'Consumables franchise and distribution reach earn high returns on organic investment (company adjusted ROIC ~22–23%); acquired growth earns lower returns on purchase price'
    ws['C80'] = 12
    ws['D80'] = '#1 global arc-welding brand; consumables razor/razor-blade model; installed base, distributor network and application know-how; welding automation and cobot growth; RISE 2030 strategy'
    ws['B90'] = 'VALUATION  —  Applied to 2028E NOPAT'
    ws['B91'] = '2028E Adj. EBIT less rationalization & transaction costs'
    ws['C91'] = f'=Model!{fy[2028]}{R["aebit"]}-Model!{fy[2028]}{R["eb_rat"]}-Model!{fy[2028]}{R["eb_txn"]}'
    ws['C96'] = f'=Model!{fy[2027]}{R["lev_nd"]}+Model!{fy[2027]}{R["bs_nci"]}'
    ws['C98'] = f'=Model!{fy[2028]}{R["val_sh"]}'
    ws['B108'] = 'LECO market-implied EV/NOPAT (on 2028E NOPAT)'
    for r in range(1, ws.max_row + 1):
        for c in range(1, ws.max_column + 1):
            v = ws.cell(r, c).value
            if isinstance(v, str) and ('Martin Marietta' in v or 'MLM' in v or 'LNA' in v):
                ws.cell(r, c).value = v.replace('Martin Marietta Materials', 'Lincoln Electric').replace('Martin Marietta', 'Lincoln Electric').replace('MLM', 'LECO')
    return ws


def adapt_charts(wb, M):
    ws = wb['Charts']
    R = M.rows
    ws['B2'] = 'Lincoln Electric — Historical Operating Performance (2006–2025)'
    ws['B3'] = ('All historicals · USDm · Linked to Model. Volume / price = company "change in net sales" table (consolidated; 2006–08 from the 10-K MD&A). '
                'Adjusted EBIT as reconciled by Lincoln Electric in each period ("EBIT, as adjusted" to 2019).')
    years = list(range(2006, 2026))
    L = openpyxl.utils.get_column_letter
    rows = {8: ('Organic volume %', 'cons_volume', 'pct0'), 9: ('Price %', 'cons_price', 'pct0'),
            12: ('Adjusted EBIT', 'aebit', 'num'), 13: ('Operating income (GAAP)', 'is_oi', 'num'),
            14: ('Adj. EBIT margin %', 'aebit_m', 'pct'), 15: ('GAAP Op. margin %', 'gm_op_m', 'pct'),
            18: ('ROIC', 'roic', 'na'), 19: ('RONTA', 'ronta', 'na'), 20: ('Adj. EBIT margin %', 'aebit_m', 'na'), 21: ('FCF margin %', 'fcf_pct', 'na')}
    for r, (lbl, key, kind) in rows.items():
        ws[f'B{r}'] = lbl
        for k, y in enumerate(years):
            m = M.lay.fy[y].letter
            col = L(3 + k)
            if kind == 'pct0':
                ws[f'{col}{r}'] = f'=IFERROR(Model!{m}{R[key]}+0,0)'
            elif kind == 'na':
                ws[f'{col}{r}'] = f'=IFERROR(Model!{m}{R[key]}+0,NA())'
            else:
                ws[f'{col}{r}'] = f'=Model!{m}{R[key]}'
    # charts (openpyxl drops the template's charts on load — rebuild with the template palette)
    cats = Reference(ws, min_col=3, max_col=22, min_row=7)
    c1 = BarChart(); c1.type = 'col'; c1.grouping = 'stacked'; c1.overlap = 100
    c1.title = 'Organic Sales Drivers: Volume vs. Price, y/y %'
    for r, color in ((8, '2F3E46'), (9, '84A98C')):
        c1.add_data(Reference(ws, min_col=2, max_col=22, min_row=r), titles_from_data=True, from_rows=True)
        c1.series[-1].graphicalProperties.solidFill = color
    c1.set_categories(cats); c1.y_axis.numFmt = '0%'; c1.height = 7.5; c1.width = 24; c1.legend.position = 'b'
    ws.add_chart(c1, 'B23')
    c2 = BarChart(); c2.type = 'col'; c2.grouping = 'clustered'
    c2.title = 'Adjusted EBIT & Operating Income (USDm)'
    for r, color in ((12, 'A8C5D6'), (13, '1F4E79')):
        c2.add_data(Reference(ws, min_col=2, max_col=22, min_row=r), titles_from_data=True, from_rows=True)
        c2.series[-1].graphicalProperties.solidFill = color
    c2.set_categories(cats)
    l2 = LineChart()
    for r, color in ((14, '2F3E46'), (15, 'C8553D')):
        l2.add_data(Reference(ws, min_col=2, max_col=22, min_row=r), titles_from_data=True, from_rows=True)
        l2.series[-1].graphicalProperties.line.solidFill = color
    l2.y_axis.axId = 200; l2.y_axis.numFmt = '0%'; l2.y_axis.crosses = 'max'
    c2 += l2
    c2.height = 7.5; c2.width = 24; c2.legend.position = 'b'
    ws.add_chart(c2, 'B44')
    c3 = LineChart(); c3.title = 'Returns Profile: ROIC, RONTA, Adjusted EBIT Margin & FCF Margin'
    for r, color in ((18, '2F3E46'), (19, '84A98C'), (20, '1F4E79'), (21, 'C8553D')):
        c3.add_data(Reference(ws, min_col=2, max_col=22, min_row=r), titles_from_data=True, from_rows=True)
        c3.series[-1].graphicalProperties.line.solidFill = color
    c3.set_categories(cats); c3.y_axis.numFmt = '0%'; c3.height = 7.5; c3.width = 24; c3.legend.position = 'b'
    ws.add_chart(c3, 'B65')
    return ws


def finalize(wb, ws_new):
    del wb['Model']
    del wb['DCF_old']
    ws_new.title = 'Model'
    order = ['Model', 'Bull-Base-Bear', 'DCF', 'Charts']
    wb._sheets = [wb[n] for n in order]
    wb.active = 0
    wb.calculation.fullCalcOnLoad = True


def make(path, scenario='Base'):
    M, wb, ws, t = build_model(scenario)
    adapt_bbb(wb, M)
    adapt_dcf(wb, M)
    adapt_charts(wb, M)
    finalize(wb, ws)
    wb.save(path)
    return M


if __name__ == '__main__':
    out = sys.argv[1]
    M = make(out, sys.argv[2] if len(sys.argv) > 2 else 'Base')
    json.dump(M.rows, open(out + '.rows.json', 'w'))
    print('rows', M.r)
