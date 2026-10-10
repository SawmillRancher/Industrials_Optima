# DHR model build kit

`models/DHR_Model.xlsx` is the Danaher Corporation (NYSE: DHR) three-statement model. It is built on the latest MLM template (`MLM_Model.xlsx`, included here) with the same process as the WAB / ODFL / LOAR / WCN builds:
- **Formatting and rows:** the template's archetype rows, colour conventions (blue = input, black = formula, grey = historical growth, green = cross-sheet link), check rows and notes column. View as in the template: frozen at C8, opened on 2019, 70% zoom, quarterly 2013–2025 columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CF2`, scenario table in `Model!CN:CR`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the template's new share-repurchase rows (40–42).
  - DCF: the template's new layout — WACC with live valuation date, 2031–35 fade, implied ROIC / RONIC, target-IRR entry price, WACC × g sensitivity, reverse DCF, Mauboussin EV/NOPAT.
  - Charts.
  - The template's `DCF_old` tab is dropped, as in the WCN / HEI builds.
- **Calculated values stored** (`--recalc`), so the workbook reads correctly in any viewer.

## Columns (MLM layout)
FY2006–12 annual (C–I), quarterly Q1/13–Q2/26 with FY subtotals (J–BX), Q3/26E–Q4/26E (BY–BZ), 2026E (CA), 2027E–2030E (CB–CE), notes (CF), CAGRs (CH–CK), scenario table (CN–CR).

## Basis
- **Hybrid recast** of income statement, segments and adjusted EPS. A period that the following year's filing restated (discontinued operations / segment recast) takes the restated prior-year comparative, so year-over-year growth is like-for-like:
  - Power quality sale (2007); Apex Tool JV (2010); communications split-off (2015).
  - Fortive spin, 2-Jul-2016; ASU 2017-07 pension reclass; Envista split-off, Dec-2019.
  - Veralto spin, 30-Sep-2023; segment recasts (2009; 2022 Biotechnology).
- **Other periods** are as originally reported. Every recast period carries a cell comment on its Sales cell (from `normalize.BASIS`). A segment-only recast is applied to a year's quarters only if all four quarters have it.
- **Balance sheet and cash flow:** as originally reported. Discrete quarterly cash flow is derived from the year-to-date statements (Q4 = FY − 9M).
- **Per-share data:** split-adjusted for the June-2010 2-for-1 split.

## Model structure (Model tab)
- **Segment build: Biotechnology, Life Sciences, Diagnostics.**
  - Sales = prior-year quarter × (1 + core growth + FX). Q3/Q4-26E core inputs come from the Q2-26 segment guidance, plus a uniform calibration Δ so that FY26 core growth = the guidance end-point (+3.0% / 3.5% / 4.0%). FX follows guidance (Q3 −1.0%, FY ~+0.5%).
  - Adjusted operating margin per segment, using the company definition: operating profit + amortization + other operating profit adjustments.
  - Segment "other adjustments" are published for FY24 / Q4-24 / FY25 / Q4-25. Other 2024–26 quarters are allocated from the adjusted-EPS footnotes (`data/manual_items.json`), and the allocations tie to the published FY totals.
  - Q3/26E margin shift solves to the Q3 adjusted operating margin guide (~26.5%). The Q4/26E shift solves FY26 adjusted EPS to the guidance end-point ($8.45 / 8.525 / 8.60).
  - 2027E+: scenario core growth and margin levers.
  - Legacy segments are kept in grouped memo rows (Professional Instrumentation … Environmental & Applied Solutions, Dental).
- **Masimo** (closed 10-Jun-2026, $9.84bn cash + $45m awards; in Diagnostics, modelled as its own block):
  - Standalone history from Masimo's own SEC filings (XBRL, continuing operations, 2024+).
  - Q2/26 stub: 16 days; sales estimated from the published acquisition impact (Diagnostics 4.0% → ~$92m).
  - Forecast: growth and margin levers, with cost / revenue synergies ($125m / $50m by year 5; 2027 EBITDA > $530m target).
  - Purchase accounting: PPA intangibles $4,844m over a ~20-year life implied by the amortization guidance; inventory step-up.
  - Diagnostics rows are shown "legacy" (ex Masimo); the reported segment is a memo row.
- **StatLab** (pending, Leica Biosystems): assumed closed end-2026 and consolidated from 2027E (~$250m 2025 revenue, HSD growth, 30% margin).
  - **The purchase price is not disclosed.** The 7.5x sales (~$2.0bn) is a flagged assumption (`Model` StatLab block; set the closing switch to 0 to exclude).
- **Other blocks:** future-M&A lever; corporate (Other segment, ~$(90)m per quarter guided).
- **GAAP from the build:** operating profit = adjusted operating profit − amortization − other adjustments.
  - SG&A comes from a % of sales (+ adjustments); R&D from a % of sales; gross profit is implied.
  - Interest follows FY26 guidance (~$310m net), then the debt schedule.
  - Tax: adjusted tax rate ~17% (guided); GAAP tax = adjusted tax − tax effect of items.
- **GAAP → adjusted bridges** (checks vs published in every period that publishes the measure):
  1. **Net earnings → EBITDA → Adjusted EBITDA (model definition):** Danaher does not publish EBITDA. Checked as Adjusted EBITDA = adjusted operating profit + depreciation in every period.
  2. **GAAP operating profit → adjusted operating profit (company definition):** applied to all periods. Checked against FY24, Q4-24, FY25 and Q4-25 as published.
  3. **GAAP net earnings → adjusted net earnings → adjusted diluted EPS:** company definition in force each period (definition row flags the changes: amortization added back from Q1-15; MCPS 2019–23; continuing ops after Veralto).
     - $ amounts come from the release footnotes. Narrative 2006–13 bridges are after tax. MCPS if-converted where the company EPS uses it.
     - **Ties to every published adjusted EPS within ±$0.02.** In recast periods the item detail is on the original basis, so the difference to the recast EPS is shown in the residual row (commented).
- **Other schedules:**
  - Cash flow; FCF on the company definition (components of the release FCF table where published; checked).
  - Balance sheet; working capital.
  - Masimo PPA (checks to consideration).
  - Debt: note maturities from the Q2-26 10-Q; euro CP to a minimum cash balance. Leverage-floor buybacks.
  - Ratios and valuation.
- **DCF:** NOPAT is taxed on adjusted operating profit (before acquired-intangible amortization, as in adjusted EPS) with a depreciation-only add-back. This way the terminal value carries no perpetual amortization add-back. Opening invested capital = 2025A IC + Masimo + StatLab consideration.

## Sources
- **SEC EDGAR only (CIK 0000313616):** Forms 10-K and 10-Q 2006–2026; Form 8-K earnings releases (Ex. 99.1) Q1-06 – Q2-26; deal and financing 8-Ks (Masimo, Feb–Jun 2026).
- **Masimo Corp.** (CIK 0000937556) XBRL companyfacts.
- **The investor-relations site (investors.danaher.com) is blocked** from the build environment; its releases are the same documents as filed on EDGAR.
- `filings.csv` indexes the filings. Each `data/<period>.json` lists its source URLs and notes. `data/deals.json` holds the Masimo / StatLab / debt / buyback facts. `data/manual_items.json` holds the segment allocations and Masimo stub inputs, each with its source.
- **Share price:** $221.21 (NYSE close 5-Oct-2026) is an input at `Model!CA` in the valuation block; update it to market.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   - `export DHR_SRC=/path/to/src`, then run `python3 make_index.py`, `python3 fetch.py` and `python3 period_index.py` (EDGAR → text; period → document map).
   - Extract new periods into `data/<period>.json` per `EXTRACTION_SCHEMA.txt`, the same per-period schema and self-checks as the WAB build.
   - Run `python3 masimo.py`, then `python3 normalize.py` (lists any data issues and the recast basis).
3. Build: `python3 build.py --snap --recalc` writes `../DHR_Model.xlsx`, reruns with the switch on Bull and Bear to fill the snapshot panels, and stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 inspect_model.py <file>` lists formula errors and non-zero check rows.
   - `python3 cyc.py <file>` scans for circular references.
   - `python3 review.py <file> [row keys]` prints key rows.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry. `rows.py`: row lookup for inspection scripts.
- `spec.py`, `spec2.py`: Model row specification. `build.py`: inputs (V0), compute engine, scenario table, definition flags, header.
- `other_sheets.py`: rewires Bull-Base-Bear / new DCF / Charts and re-injects the template chart XML.
- `h2t.py`, `make_index.py`, `fetch.py`, `period_index.py`, `masimo.py`: EDGAR HTML → text, filings index, downloads, period map, Masimo history.
- `normalize.py`: flat model keys, hybrid recast, split adjustment, discrete quarterly cash flow, adjusted-EPS bridge amounts, FCF basis, Masimo / PPA inputs.
