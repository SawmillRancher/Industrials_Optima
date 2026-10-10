# ODFL model build kit

`models/ODFL_Model.xlsx` is the Old Dominion Freight Line (Nasdaq: ODFL) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here) with the same process as the WAB build:
- **Columns:** FY2006–12 annual, quarterly Q1/13–Q2/26, Q3/26E–Q4/26E, then 2026E–2030E.
- **Formatting and rows:** the template's formatting and row conventions.
- **Scenarios:** Bull / Base / Bear switch in `Model!CF2`, scenario table in `Model!CN:CR`.
- **Other tabs:** the same Bull-Base-Bear, DCF and Charts tabs.

## Model structure (Model tab)
- **LTL operating build** (in place of MLM's product lines):
  - Work days × LTL tons per day → tons; shipments and weight per shipment.
  - × 20 cwt × revenue per hundredweight (ex-fuel + fuel surcharge) → LTL revenue on the statistics basis.
  - + revenue-recognition adjustment + other services revenue → total revenue, checked against reported revenue.
  - Volume / ex-fuel yield / fuel-surcharge revenue bridge; network and productivity memo (service centers, tractors, trailers, employees).
- **Operating-ratio build:** the nine reported expense lines as % of revenue → operating ratio.
- **FY26 calibration** (ODFL gives no revenue / EPS guidance):
  - Q3/26E is anchored to the 3-Sep-26 mid-quarter update: Aug-26 tons/day −0.9% y/y; Jul–Aug revenue/cwt +11.3%, ex fuel +4.8%.
  - Q4/26E tons/day and ex-fuel yield, and the Q3 and Q4 operating ratios, apply the 2016–25 sequential seasonality: best / average / worst for Bull / Base / Bear. These are formulas on the historical columns.
  - A calibration helper scales the variable cost lines to hit the operating-ratio target, with check rows.
- **GAAP → adjusted bridges** (model definitions — ODFL publishes no non-GAAP measures):
  - **Net income → EBITDA → Adjusted EBITDA.** EBITDA = net income + tax + net interest + other non-operating + D&A. Adjusted EBITDA excludes net (gains) / losses on disposal of property & equipment (from the cash-flow statement) and one-off items quantified by ODFL:
    - Q2-07: +$2.0m customer pricing resolution.
    - Q4-17: $9.8m TCJA special bonus.
    - Q3-22: −$15.8m one-time SWB reduction.
  - **GAAP EPS → adjusted EPS.** Adjusting items are tax-effected at the effective rate excluding discrete items. The Q4-17 TCJA $104.9m deferred-tax benefit is removed.
  - **Check rows** tie the bridges to SEC XBRL (OperatingIncomeLoss, NetIncomeLoss, DepreciationAndAmortization, GainLossOnSaleOfPropertyPlantEquipment) and to published GAAP EPS.
- **Other schedules:**
  - Statement of operations; cash flow (quarters derived from year-to-date); balance sheet; working capital.
  - Debt schedule (Series B notes, revolver) and cash-return buybacks: repurchases plug to a scenario target cash balance.
  - Ratios and valuation.

## Sources
SEC EDGAR only (CIK 0000878927):
- Forms 10-K and 10-Q.
- Form 8-K earnings releases (Item 2.02, Ex. 99.1) and mid-quarter updates (Item 7.01).
- SEC XBRL companyfacts, used for cross-checks and dividends per share.

The ODFL IR site (ir.odfl.com) is blocked from the build environment; its releases are the same documents filed on EDGAR. `filings.csv` indexes every filing, and each `data/<period>.json` lists its source URLs.

All periods are as originally reported. Shares and per-share data are restated for the 3-for-2 splits (Aug-2010, Sep-2012, Mar-2020) and the 2-for-1 split (Mar-2024), by the filing date of each source document.

## Rebuild
1. `pip install openpyxl`; LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. `python3 make_index.py` (filings index), `python3 fetch.py` (downloads to `$ODFL_SRC`), `python3 extract.py` (per-period JSON), `python3 xbrl.py` (needs the companyfacts JSON at `$ODFL_FACTS`). The `data/` folder is committed, so these steps are only needed to refresh the data.
3. `python3 build.py --snap` builds `../ODFL_Model.xlsx`, then reruns with the switch on Bull and Bear to refresh the snapshot panels. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Recalculate a copy and run `python3 inspect_model.py <file>` to list formula errors and non-zero check rows; `python3 cyc.py <file>` scans for circular references.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification. `build.py`: inputs (V0), compute engine, scenario table, definition flags.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `parse_release.py`, `parse_fin.py`, `extract.py`: EDGAR release / 10-Q / 10-K parsers. `h2t.py`: HTML→text. `workdays.py`: ODFL work-day calendar (reproduces every published count).
- `normalize.py`: operating-statistics basis, discrete quarterly cash flow, derived lines, bridge items, XBRL cross-checks. `data/manual_items.json`: company-identified one-off items with sources.
