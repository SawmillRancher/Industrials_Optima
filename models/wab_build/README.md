# WAB model build kit

`models/WAB_Model.xlsx` is the Westinghouse Air Brake Technologies (Wabtec, NYSE: WAB) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here): same columns (FY2006–12 annual, quarterly Q1/13–Q2/26, Q3/26E–Q4/26E, 2026E–2030E), same formatting and row conventions, Bull / Base / Bear switch in `Model!CF2`, scenario table in `Model!CN:CR`, and the same Bull-Base-Bear, DCF and Charts tabs.

## Model structure (Model tab)
- **Product-line build**: Freight (Services, Equipment, Components, Digital Intelligence) and Transit (OE, Aftermarket) sales → segment adjusted operating margin → adjusted income from operations; 12-month / total backlog by segment; sales-change bridge (acquisitions / portfolio optimization / FX / organic); corporate; future-M&A lever.
- **FY26 calibration**: Q3/Q4-26E growth and adjusted-margin shifts solve so FY26 sales and adjusted EPS equal the guidance end-point of the active scenario ($12.30–12.60bn; $10.60–10.90).
- **GAAP → adjusted bridges** (as published, checks vs company figures): Net income → EBITDA → Adjusted EBITDA; GAAP → adjusted income from operations; GAAP → adjusted net income / EPS (table bridges from Q4-17, per-share narrative bridges before). Definition changes are flagged in the definition rows (2019 merger basis; amortization added back from Q1-20).
- Income statement, cash flow (quarters derived from YTD), balance sheet, working capital, debt / buyback / leverage schedules, 2025–26 acquisition PPAs (Inspection Technologies, Frauscher, Dellner), ratios, valuation.

## Sources
SEC EDGAR only (CIK 0000943452): Forms 10-K, 10-Q, Form 8-K earnings releases (Ex. 99.1) and decks, deal 8-Ks. The Wabtec IR site is blocked from the build environment; its releases are the same documents filed on EDGAR. `filings.csv` indexes every filing; each `data/<period>.json` lists its source URLs. All periods as originally reported; pre-June-2013 shares / per-share data restated for the 2-for-1 split.

## Rebuild
1. `pip install openpyxl`; LibreOffice Calc (`libreoffice-calc`) for recalculation.
2. `python3 build.py --snap` — builds `WAB_Model.xlsx`, then reruns with the switch on Bull and Bear to refresh the snapshot panels. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
3. Recalculate a copy and run `python3 inspect_model.py <file>` to list formula errors and non-zero check rows; `python3 cyc.py` scans for circular references.

## Files
- `fw.py` column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py` Model row specification; `build.py` inputs (V0), compute engine, scenario table, definition flags, PPAs.
- `other_sheets.py` rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `normalize.py` split adjustment, discrete quarterly cash flow, derived lines, bridge harmonisation, cross-checks.
- `h2t.py`, `EXTRACTION_SCHEMA.txt` EDGAR HTML→text converter and extraction schema.
