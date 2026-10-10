# WWD model build kit

`models/WWD_Model.xlsx` is the Woodward, Inc. (NASDAQ: WWD) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `MODEL_BUILD_PLAYBOOK.md` (branch `claude/loving-brahmagupta-4na9sl`), adapted from the STE build kit:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!AV2`, scenario table in `Model!BD:BH`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). Discount dates moved to Woodward's 30-September fiscal year ends; FY2026E (ended 30-Sep-2026, a week before the valuation date) is the base year, so the explicit years are FY2027E–FY2031E and net debt is taken at 30-Sep-2026.
  - Charts: segment contribution to sales growth, adjusted EBITDA / EBIT, returns.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (fiscal year ends 30 September; 2026 = Oct-2025 – Sep-2026)
- **C–L FY2011–FY2020:** annual, as originally reported.
- **M–AK Q1/21–Q4/25 with FY subtotals; AL–AN Q1/26–Q3/26:** grouped and collapsed like the template.
- **AO Q4/26E, AP 2026E:** forecast, calibrated to the FY26 guidance (Q3 FY26 release, 29-Jul-2026).
- **AQ–AU 2027E–2031E:** scenario forecast.
- **Right of the forecast** (template column − 36): AV notes, AX–BA CAGRs (5Y fwd '26–'31, 5Y, 10Y, 14Y), BD–BH scenario table.

## Basis
- **Policy:** as originally reported, from each period's own earnings release.
- **Restatements not recast** (cell comments; restated figures kept as memo rows): FY2016 cost-line reclassification (FY2017 release); FY2018 pension-cost reclassification under ASU 2017-07, which also moved FY2018 segment earnings (Aerospace $301.8m → $308.6m, Industrial $47.9m → $49.9m) in the FY2019 release.
- **Segments:** Aerospace and Energy (renamed Industrial in FY2016) throughout.
- **Sales by primary market** (10-Q / 10-K revenue note, from FY2019; Q4 = fiscal year − nine months):
  - Aerospace: commercial OEM, commercial aftermarket / services, defense OEM, defense aftermarket / services, as reported.
  - Industrial: power generation, transportation, oil & gas were introduced in the FY2023 10-K. FY2021–22 annual comes from the FY2023 10-K and FY2023 quarters from the FY2024 10-Q comparatives (latest filing presenting the period). The earlier reciprocating engines / industrial turbines / renewables split (FY2019–FY2022) is kept as legacy memo rows.
- **Adjusted measures:** published from Q2 FY2018 (adjusted EBIT / EBITDA / net earnings / EPS). FY2011–FY2017 releases publish EBIT, EBITDA and free cash flow only, so adjusted = GAAP there (flagged in the definition rows). Quarters with no adjusting items (Q3 FY24, Q3 FY25) show adjusted = GAAP.
- **Per-share data:** no stock splits since Feb-2008; no share classes. Shares outstanding = shares issued − treasury shares (XBRL).
- **Cash flow:** quarters derived from year to date (Q4 = FY − 9M). The releases show operating cash flow as one line, so working capital & other operating items = CFO − net earnings − D&A − share-based compensation − deferred taxes (D&A from the EBITDA reconciliation; share-based compensation and deferred taxes from XBRL).

## Model structure (Model tab)
- **Segment build:**
  - Aerospace sales = Σ four primary markets; Industrial sales = Σ three primary markets. History falls back to reported segment sales where markets are not published.
  - Segment earnings = sales × segment margin. Woodward's segment earnings are after amortization of intangibles.
  - Plus adjusted nonsegment expenses (as reported + adjusting items) = adjusted EBIT (company definition). Checked against the bridge.
- **Future M&A lever:** spend ÷ EV/sales (3.0x), 15% margin after amortization, PP&E / intangibles / goodwill split, 15-year amortization.
- **Pending divestitures:**
  - Aerospace pilot controls to ONTIC, $180m, close expected FY27. The gain is assumed equal to proceeds − net assets held for sale ($16.4m; goodwill allocation not disclosed); it sits in other income and is adjusted out.
  - Santa Clarita product lines and campus: terms not disclosed.
  - No revenue is removed for either deal (not disclosed; flagged input row).
- **FY26 guidance calibration (Q4/26E):**
  - Sales: one uniform Δ on the 9M FY26 y/y growth of every primary market, solved so FY26 sales = FY25 × (1 + guided growth). The scenario uses 23% / 21.5% / 20%.
  - Margins: one uniform Δ on the segment margins (prior-year quarter + 9M drift), solved so FY26 adjusted EPS = $9.50 / $9.40 / $9.30.
  - Information rows, not forced: segment growth and margin guidance, and FCF guidance ($300–350m).
  - Base result: Aerospace +22.1% at 23.6% (guided +21–23%, ~23.5%); Industrial +22.1% at 18.7% (guided +19–21%, ~19%); FCF $293m.
- **GAAP P&L from the build:** EBIT (company definition: net earnings + taxes + interest expense − interest income) = adjusted EBIT − adjusting items. Gross profit is implied. Interest is calculated on opening balances; tax at 24% in Q4/26E, then 22.5%.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **EBIT → adjusted EBIT:** company items grouped as restructuring; acquisition / business development; purchase accounting; gains / losses on sales, swaps and product rationalization; impairments; other. Company labels are in cell comments.
  2. **Net earnings → EBIT → EBITDA → adjusted EBITDA:** company definitions; the FY2018–19 L'Orange backlog amortization (already in D&A) is not added back twice. Continues to adjusted EBIT, full-cost (for NOPAT / DCF).
  3. **Net earnings → adjusted net earnings → adjusted EPS:** the historical tax effect is derived from published adjusted net earnings (incl. US tax reform FY2018–19 and the German tax-rate change FY2025). Forecast: GAAP tax − adjusted tax.
- **Other schedules:**
  - Cash flow, with a separate line reclassifying the divestiture gain to investing.
  - Buybacks; balance sheet; working capital.
  - PPAs: L'Orange FY2018, Safran EMA Q4 FY25, Valve Research Q3 FY26.
  - Debt: notes and term loan repaid at maturity; $450m Series U/V/W issued 30-Sep-2026; 2027E+ maturities refinanced with new notes; revolver to a $300m minimum cash, with a headroom memo vs the $1.0bn commitment.
  - Leverage-target buybacks, 2027E+: net debt / adjusted EBITDA of 1.75x / 1.25x / 0.75x.
  - Ratios and valuation.
- **DCF basis:**
  - NOPAT on adjusted EBIT (full-cost) less restructuring and acquisition costs.
  - UFCF after capex and bolt-on M&A; the pilot-controls proceeds are excluded.
  - No leases in net debt.
  - Market inputs (risk-free 4.25%, ERP 5%, beta 1.05) are assumptions: U.S. Treasury / FRED data are not reachable from the build environment.
  - Cost of debt 5.5% is anchored on the Aug-2026 note coupons.

## Key forecast assumptions (Base)
- **Primary-market growth 2027E–31E:** commercial OEM 14% → 6%; commercial services 9% → 6%; defense OEM 7% → 5%; defense services 5% → 4%; power generation 12% → 5%; transportation 0% in FY27 (China OH wind-down) then 3–4%; oil & gas 4% → 3% (scenario table; assumptions citing 9M FY26 / FY25 trends).
- **Segment margins:** Aerospace 24.0% → 25.5%; Industrial 19.0% → 20.0%; adjusted nonsegment 3.5% of sales.
- **Other drivers:**
  - Capex 5.0% of sales in FY27 (Spartanburg online summer 2027), falling to 3.0%.
  - Depreciation 2.3–2.6% of sales.
  - Amortization per the 10-Q schedule ($32.5m FY27).
  - Restructuring $30m FY27 and $15m FY28 (Santa Clarita $34–47.5m, servo valve ~$15m).
  - M&A $100m p.a. (assumption).
  - DPS +10% p.a.
- **Share price $382.17:** the weighted average price paid for shares repurchased in June 2026 (Q3 FY26 10-Q Part II Item 2). This is the latest share price in an SEC filing; update it at `Model!AP` in the valuation block.

## Data corrections
- None. Known data exceptions (documented, not corrected):
  - FY2023 Σ quarters vs year for cost of goods sold / R&D differs by $1.4m (reclassification within the year; the 10-K / Q4 release total is used for the year).
  - Q1 FY22 and Q1 FY23 deferred taxes are not tagged in the 10-Q XBRL (treated as 0, absorbed in the derived working-capital line).

## Sources
SEC EDGAR only (CIK 108312):
- Forms 10-K / 10-Q FY2011–Q3 FY2026.
- Form 8-K Item 2.02 earnings releases (Ex. 99.1), Q4 FY2011 – Q3 FY2026.
- 8-Ks:
  - L'Orange (Jun-2018);
  - credit agreements and notes (May-2026, Aug-2026);
  - Item 2.05 restructurings (Jan-2026 China OH; Sep-2026 Santa Clarita);
  - dividends.
- XBRL company facts: share-based compensation, deferred income taxes, shares issued / treasury shares.

The investor-relations site (woodward.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR.
- `filings.csv` indexes the filings.
- Each `data/<period>.json` lists its source URLs; `data/_releases.json` indexes the releases and `data/_xbrl.json` holds the XBRL subset.
- `manual_items.json` holds the FY26 guidance history, restructuring plans, deals and PPAs, the amortization schedule, debt facts, the buyback authorization, dividends and the share price, each with its source.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export WWD_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`.
   3. `python3 check_data.py` runs 724 checks: statement arithmetic, segment and primary-market sums, EBIT / EBITDA / adjusted bridges vs published, EPS, cash and balance-sheet tie-outs, and quarters vs years. The only known exception is the FY2023 $1.4m reclassification.
3. Build: `python3 build.py --snap --recalc` writes `../WWD_Model.xlsx`. It reruns with the switch on Bull and Bear to fill the snapshot panels, then stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 inspect_model.py ../WWD_Model.xlsx` → 0 error cells, 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 cyc.py ../WWD_Model.xlsx` → 0 cycles.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`: EDGAR filings index, downloads, HTML → text.
- `parse_release.py`: release parser. It identifies tables by content and resolves columns (months, current / prior, measure), including the FY2012–13 fixed-width releases.
- `extract.py`: per-period extraction (statements, segments, primary markets, non-GAAP items with categories, cash flow, balance sheet, prior-year comparatives).
- `xbrl.py`: XBRL company-facts helper (30-September fiscal year).
- `normalize.py`: basis rules, flat model keys, discrete quarterly cash flow.
- `check_data.py`: data consistency checks.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
