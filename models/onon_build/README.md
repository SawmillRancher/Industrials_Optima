# ONON model build kit

`models/ONON_Model.xlsx` is the On Holding AG (NYSE: ONON) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here: the version with the reworked DCF and Bull-Base-Bear tabs) with the same process as the LOAR / ODFL / WAB / SAIA builds:
- **Formatting and rows:** the template's archetype rows, colour conventions (blue = input / published data, black = formula, grey = historical growth, green = cross-sheet link), check rows and notes column.
- **Scenarios:** Bull / Base / Bear switch in `Model!AM2`, scenario table in `Model!AU:AY`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: the 10-year version with a fade period, live valuation date and target-IRR entry price.
  - Charts.
  - All three are rewired to the ONON rows. The template's legacy `DCF_old` tab (MLM-specific) is dropped.

## Currency and share basis
- **CHF as reported (IFRS).** Valuation converts the USD share price with a USD/CHF input (`Model!AH` valuation block). Price targets, the DCF and IRRs are in CHF.
- **Class A-equivalent shares = Class A + Class B ÷ 10.** Class B voting shares carry 1/10 of the Class A nominal value and economic rights. On this basis, net income ÷ shares reproduces the published Class A EPS and adjusted EPS.

## Columns (re-based for ONON's history)
- **C–D FY2019–2020:** from the IPO prospectus (424B4, 16-Sep-2021). CHF thousands are converted to millions; per-share data and share counts are ×1,250 for the 2021 share-capital reorganisation. FY2019 has no balance sheet or cash flow beyond memo items.
- **E–AC Q1/21–Q4/25 with FY subtotals,** grouped and collapsed like the template.
  - Q1–Q2/21 come from the 2022 releases' comparatives.
  - Balance sheets start at Q3-21; FY2020 comes from the FY2021 release comparatives.
- **AD–AE Q1/26–Q2/26, AF–AG Q3/26E–Q4/26E, AH 2026E, AI–AL 2027E–2030E.**
- Columns to the right of the forecast keep the template order (template column − 45): AM notes, AO–AR CAGRs (5Y fwd, 5Y, 3Y, 6Y), AU–AY scenario table.

## Model structure (Model tab)
- **Region build:** Americas / EMEA / APAC.
  - Prior-year period × (1 + constant-currency growth + FX translation effect).
  - Constant-currency growth is published from Q1-24.
  - Former Europe / North America / APAC / RoW disclosure (to 2022) is kept as memo rows.
- **FY26 outlook calibration (Q3/Q4-26E):**
  - Q3 cc Δ hits the Q3 guide (~17%); Q4 cc Δ hits FY26 cc growth (low-20%).
  - A uniform 2H FX Δ hits FY26 CHF net sales at spot (CHF 3.47–3.56bn).
  - Gross-margin and Adjusted EBITDA-margin Δs hit the guidance (≥65.0%; 19.5–20.0%).
  - All of these exclude the Q3-26 tariff refund (CHF ~53m). The refund is modelled as a separate line in reported gross profit and Adjusted EBITDA.
- **2027E–2030E:** regional cc growth, gross margin, Adjusted EBITDA margin and buyback levers. Base follows the Investor Day 2029 targets (22-Sep-2026): ≥CHF 5.6bn sales, high-teens cc CAGR, GM ≥65%, Adjusted EBITDA margin ≥22%, Adjusted EBITDA CAGR >20%. The targets are shown against the model as information rows.
- **Channel** (wholesale / DTC share driver) and **product** (shoes / apparel / accessories) mix.
- **IFRS P&L from the margin build:**
  - Operating result = Adjusted EBITDA − D&A − SBC; SG&A is implied.
  - Financial income comes from opening cash; financial expense from opening lease liabilities.
- **IFRS → adjusted bridges** (checks vs published figures in every reported period):
  1. **Net income → EBITDA → Adjusted EBITDA:** + SBC (+ IPO / equity transaction costs 2021).
  2. **Operating result → adjusted operating result (model):** checked as adjusted operating result + D&A = published Adjusted EBITDA.
  3. **Net income → adjusted net income → adjusted EPS:** Class A + Class B, checked against published adjusted net income and basic / diluted adjusted EPS. Annual columns use the full-year table, because the company computes the tax effect annually and quarters do not sum to the year.
- **Other schedules:**
  - Cash flow (quarters derived from YTD).
  - Balance sheet and working capital (company NWC definition).
  - IFRS 16 lease schedule: right-of-use assets as a % of sales; new leases as the plug; lease principal ≈ right-of-use depreciation.
  - USD 1bn buyback schedule (Sep-2026 to Dec-2029; 2030E assumes a renewal).
  - Ratios and valuation.
- **DCF basis:** rent-as-opex. UFCF deducts SBC and lease principal payments, and lease liabilities are excluded from the net-cash bridge. The risk-free rate is USD-based because the forecasts hold FX at spot.

## Data corrections (documented in `manual_items.json`)
- **Q4-21 operating result:** the FY2021 release prints (354.9)m. Gross profit − SG&A = (177.5)m, which ties to FY − 9M, the published income before taxes and Adjusted EBITDA. Corrected to (177.5)m.
- **Q1-22 cash flow:** net cash is net of a CHF 25.8m bank overdraft (release footnote). The cash check nets it.

## Sources
SEC EDGAR only (CIK 0001858985):
- IPO prospectus (424B4).
- Forms 20-F FY2021–25.
- Form 6-K earnings releases (Ex. 99.1 / 99.3, Q3-21 – Q2-26).
- 6-K MD&A exhibits (Ex. 99.2) for the 2021–23 sales splits and constant-currency growth.
- Investor Day releases (Oct-2023, 22-Sep-2026).

The investor-relations site (investors.on-running.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR. `filings.csv` indexes the filings, and each `data/<period>.json` lists its source documents.

The share price (USD 32.00, early Oct-2026 close ~USD 31.9) and USD/CHF (0.80) are inputs in the Model valuation block; update both to market.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   - `export ONON_SRC=/path/to/src`
   - `python3 make_index.py && python3 fetch.py && python3 extract.py`
   - `python3 check_data.py` runs the statement-arithmetic, bridge, split, quarter-sum, balance-sheet and cash-flow checks.
3. Build: `python3 build.py --snap` writes `../ONON_Model.xlsx`, then reruns with the switch on Bull and Bear to fill the snapshot panels. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - Recalculate a copy, then run `python3 inspect_model.py <file>` to list formula errors and non-zero check rows.
   - `python3 cyc.py <file>` scans for circular references.
   - The Charts `#N/A` cells for FY2019 ROIC / RONTA / FCF margin are intentional (no FY2019 balance sheet or cash flow).

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry. `rows.py`: row lookup for inspection scripts.
- `spec.py`, `spec2.py`: Model row specification. `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML (re-ranged to 2019–2030E).
- `h2t.py`, `parse_release.py`, `extract.py`: EDGAR HTML → text, release-table reader (period-group headers), per-period extraction.
- `normalize.py`: flat model keys, discrete quarterly cash flow, Q4 splits (FY − 9M), Class A-equivalent shares, Class A + B adjusted net income.
