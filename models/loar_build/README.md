# LOAR model build kit

`models/LOAR_Model.xlsx` is the Loar Holdings Inc. (NYSE: LOAR) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here) with the same process as the ODFL / WAB / SAIA builds:
- **Formatting and rows:** the template's archetype rows, colour conventions (blue = input, black = formula, grey = historical growth, green = cross-sheet link), check rows and notes column.
- **Scenarios:** Bull / Base / Bear switch in `Model!AP2`, scenario table in `Model!AX:BB`.
- **Other tabs:** the same Bull-Base-Bear (live panel + Bull / Bear value snapshots), DCF and Charts tabs, rewired to the LOAR rows.

## Columns (re-based for LOAR's history)
- **C–L FY2012–2021:** annual net income → Adjusted EBITDA reconciliation from the IPO prospectus. Only the P&L / bridge lines are populated (no balance sheet or cash flow). FY2017 = predecessor (1-Jan–1-Oct) + successor (2-Oct–31-Dec) as presented.
- **M–AF Q1/22–Q4/25 with FY subtotals:** grouped and collapsed like the template.
  - 2022–23 quarters come from the prospectus quarterly tables and the 2024 release comparatives.
  - Quarter-end balance sheets start at Q1-24; FY2022–23 year ends come from the prospectus.
- **AG–AH Q1/26–Q2/26, AI–AJ Q3/26E–Q4/26E, AK 2026E, AL–AO 2027E–2030E.**
- Columns to the right of the forecast keep the template order (template column − 42): AP notes, AR–AU CAGRs (5Y fwd, 5Y, 10Y, 13Y), AX–BB scenario table.

## Model structure (Model tab)
- **End-market build** (in place of MLM's product lines):
  - Commercial aerospace, Business jet & GA, Defense and Other, each split OEM / aftermarket (release Table 5).
  - Q3/Q4-26E: prior-year quarter × (1 + 1H/26 y/y growth + a uniform calibration Δ), so FY26 net sales hit the guidance end-point ($665–675m).
  - 2027E+: scenario growth levers per line.
  - Mix memo: OEM / aftermarket and the company's outlook metrics.
- **Organic vs acquired net sales:** as published. Acquisitions count as organic from the 13th month.
- **Future M&A lever:** spend ÷ EV/sales, Adjusted EBITDA margin, PP&E / intangibles / goodwill split, amortization.
- **Adjusted EBITDA build:**
  - Margin × net sales.
  - Q3/Q4-26E: prior-year quarter margin + 1H drift + calibration Δ, so FY26 Adjusted EBITDA = guidance ($265–270m).
  - 2027E+: scenario margin lever.
  - Net income and Adjusted EPS guidance are shown against the model as information rows; they are not forced.
- **GAAP P&L from the build:**
  - Operating income = Adjusted EBITDA − D&A − EBITDA adjusting items. SG&A comes from a % of sales; gross profit is implied.
  - D&A, interest and the tax rate follow FY26 guidance, then the amortization schedule and the debt schedule.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **Net income → EBITDA → Adjusted EBITDA:** company lines exactly as published (FY2012–26).
  2. **GAAP operating income → Adjusted EBITA (model):** + amortization + EBITDA adjusting items. Checked as Adjusted EBITA + depreciation = published Adjusted EBITDA.
  3. **GAAP net income → Adjusted net income → Adjusted EPS:**
     - On the **current definition** (adds back amortization of acquired intangibles, tax-effected; from the Q1-26 release) for all periods from Q2-24.
     - Checked against published current-definition figures (Q1-25 and Q2-25 restated; Q1-26, Q2-26).
     - Memo rows rebuild the **prior definition** and check it against every figure as originally published (Q2-24 – Q4-25, FY24, FY25).
- **Other schedules:**
  - Cash flow (quarters derived from YTD).
  - Balance sheet; working capital.
  - Acquisition PPAs: SCHROTH, DAC + CAV, AAI, Beadlight, LMB, Harper.
  - Debt: term loans prepayable at par, cash sweep to minimum cash, debt-cost accretion. Leverage-floor buybacks.
  - Ratios and valuation.

## Sources
SEC EDGAR only (CIK 0002000178):
- IPO prospectus (424B4, 26-Apr-2024).
- Forms 10-K and 10-Q.
- Form 8-K earnings releases (Ex. 99.1, Q1-24 – Q2-26) and deal 8-Ks.

The investor-relations site (ir.loargroup.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR. `filings.csv` indexes the filings, and each `data/<period>.json` lists its source URLs. `manual_items.json` holds the PPAs, the 10-K amortization schedule, debt and equity facts, and the tax rate applied to the amortization add-back in prior-definition periods (2024 24%; 2025 20.2%, implied by the restatements).

The share price ($75.00, early Oct-2026 quote) is an input at `Model!AK` in the valuation block; update it to market.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed): `export LOAR_SRC=/path/to/src`, then run `python3 make_index.py`, `python3 fetch.py` and `python3 extract.py`. `python3 check_data.py` then runs the statement-arithmetic, quarter-sum and end-market checks on the extracted data.
3. Build: `python3 build.py --snap` writes `../LOAR_Model.xlsx`, then reruns with the switch on Bull and Bear to fill the snapshot panels. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate: recalculate a copy, then run `python3 inspect_model.py <file>` to list formula errors and non-zero check rows. `python3 cyc.py <file>` scans for circular references. The Charts `#N/A` cells for 2012–21 returns are intentional (no balance sheet before FY2022).

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry. `rows.py`: row lookup for inspection scripts.
- `spec.py`, `spec2.py`: Model row specification. `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML (re-ranged to 2012–2030E).
- `h2t.py`, `parse_release.py`, `extract.py`: EDGAR HTML → text, release-table parser, per-period extraction (prospectus + releases).
- `normalize.py`: flat model keys, discrete quarterly cash flow, derived lines, Q1-23 end markets, both Adjusted EPS definitions.
