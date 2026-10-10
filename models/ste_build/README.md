# STE model build kit

`models/STE_Model.xlsx` is the STERIS plc (NYSE: STE) three-statement model. It is built on the current MLM template (`MLM_Model.xlsx`, included here), the version uploaded on 6-Oct-2026, with the same process as the LOAR / ODFL / WAB / SAIA builds:
- **Formatting and rows:** the template's archetype rows, colour conventions (blue = input, black = formula, grey = historical growth), check rows and notes column.
- **Scenarios:** Bull / Base / Bear switch in `Model!AU2`, scenario table in `Model!BC:BG`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the template's new buyback rows.
  - DCF: the template's current layout — live valuation date, fade period, implied ROIC, target-IRR entry price, reverse DCF, Mauboussin EV/NOPAT. Discount dates are moved to STERIS's 31-March fiscal year ends.
  - Charts: rewired to the STE rows.
  - The template's `DCF_old` tab is dropped.

## Columns (fiscal years ended 31 March; 2027 = Apr-2026 – Mar-2027)
- **C–L FY2012–FY2021:** annual, as originally reported.
- **M–AK Q1/22–Q4/26 with FY subtotals:** grouped and collapsed like the template.
- **AL Q1/27:** actual.
- **AM–AO Q2/27E–Q4/27E, AP 2027E:** forecast, calibrated to the FY27 outlook.
- **AQ–AT 2028E–2031E:** scenario forecast.
- **Right of the forecast** (template column − 37): AU notes, AW–AZ CAGRs (5Y fwd '26–'31, 5Y, 10Y, 14Y), BC–BG scenario table.

## Basis
- **FY2012–FY2022:** as originally reported. Dental (Cantel, Jun-2021) is shown as a segment in FY2022.
- **FY2023 onward:** continuing operations. Dental moved to discontinued operations in the Q4 FY24 release (8-May-2024) and was sold Sep-2024.
  - FY2023 quarters: GAAP and adjusted totals from that release's recast tables. Opex lines are derived: R&D, restructuring and other are scaled to the FY2023 restated totals, and SG&A is the plug.
  - Q1–Q3 FY24: comparatives in the FY25 releases.
  - Originally reported adjusted EPS (incl. Dental) is rebuilt from the adjusted Dental discontinued-operations income and checked in memo rows.
- **Segments as reported per year:**
  - FY2012–15: Healthcare / Life Sciences / Isomedix (= AST).
  - FY2016–20: Healthcare Products + Healthcare Specialty Services, shown combined as Healthcare.
  - FY2021+: Healthcare.
  - Corporate costs reported separately from FY2019.
  - FY2012–15 segment operating income is the adjusted figure from the release reconciliations.

## Model structure (Model tab)
- **Segment build:**
  - Revenue by segment × type: Healthcare and Life Sciences capital / consumables / service; AST service / capital.
  - Segment operating income = revenue × segment margin; plus corporate = adjusted operating income.
  - Dental (FY2022) and Corporate & other revenue (FY2012–17) are shown for history.
- **Revenue growth bridge:** as reported → organic → constant-currency organic, as published from FY2017, with a check.
- **Future M&A lever:** tuck-in spend ÷ EV/sales, margin, PP&E / intangibles / goodwill split, amortization.
- **FY27 outlook calibration (Q2–Q4/27E):**
  - Revenue lines: Q1/27 y/y growth + a uniform Δ, so FY27 revenue = FY26 × (1 + guided growth). The scenario uses 8.0% / 7.5% / 7.0%.
  - Segment margins: prior-year quarter + Q1 drift + a uniform Δ, so FY27 adjusted EPS = guidance ($11.30 / $11.20 / $11.10).
  - Information rows, not forced: GAAP EPS vs guidance and FCF vs the ~$800m outlook.
- **GAAP P&L from the build:** operating income = adjusted operating income − acquired-intangible amortization − other adjusting items. Gross profit is implied.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **GAAP income from operations → adjusted income from operations:** company items by category. Includes a sub-bridge to adjusted gross profit.
  2. **Net income → EBITDA → adjusted EBITDA:** model definition; STERIS does not publish EBITDA. Leads on to adjusted EBIT (full-cost) for NOPAT / DCF.
  3. **GAAP net income (continuing) → adjusted net income → adjusted EPS:** the historical tax effect is derived from published adjusted net income; the forecast uses GAAP tax − adjusted tax.
- **Other schedules:**
  - Cash flow (quarters derived from year to date).
  - Share buybacks.
  - Balance sheet (condensed, as in the releases); working capital.
  - PPAs: Synergy, Cantel, BD surgical instrumentation.
  - Debt: notes repaid at maturity; revolver drawn / repaid to minimum cash.
  - Leverage-target buybacks, FY2028E+.
  - Ratios and valuation.

## Sources
SEC EDGAR only, across three registrants:
- STERIS Corp, CIK 815065, to FY2015.
- STERIS plc (UK), CIK 1624899, FY2016–19.
- STERIS plc (Ireland), CIK 1757898.

Documents used:
- Form 8-K Item 2.02 earnings releases (Ex. 99.1), FY2011–Q1 FY27.
- Forms 10-K / 10-Q.
- XBRL company facts for D&A, share-based compensation, deferred taxes, goodwill (FY2012–15), NCI, shares outstanding and interest expense where releases do not show it.

The investor-relations site (steris-ir.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR. `filings.csv` indexes the filings. `data/<period>.json` holds the per-release extraction, keyed by source date; `data/_releases.json` holds the release index and `data/_xbrl.json` the XBRL subset. `manual_items.json` holds:
- FY27 guidance;
- PPAs and debt facts;
- the 10-K amortization schedule;
- the Q1 FY22 adjusted share count (GAAP net-loss quarter).

The share price ($211.07, close 5-Oct-2026) is an input in the valuation block (`Model!AP`); update it to market.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export STE_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py`, `python3 fetch.py` and `python3 extract.py`. These also download the XBRL company facts `cf_<cik>.json` into `$STE_SRC`.
   3. `python3 check_data.py` runs the statement-arithmetic, segment / revenue-type, bridge, cash, balance-sheet and quarter-sum checks. Two known items remain: Q1 FY22 adjusted EPS on GAAP shares, handled by the manual share count; and a $0.4m amortization split in STERIS's own FY2023 recast.
3. Build: `python3 build.py --snap` writes `../STE_Model.xlsx`, then reruns with the switch on Bull and Bear to fill the snapshot panels. `XLSX_RECALC` points to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   1. Recalculate a copy, then run `python3 inspect_model.py <file>`. It lists formula errors and non-zero check rows; the DuPont "Margin × Turnover × Tax burden = ROIC" row shows ROIC by design.
   2. `python3 cyc.py <file>` scans for circular references.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `h2t.py`, `parse_release.py`, `extract.py`: EDGAR HTML → text, release section parser and column-aligned Non-GAAP matrix parser, per-release extraction.
- `xbrl.py`: XBRL company-facts helper.
- `normalize.py`: source-priority rules, flat model keys, discrete quarterly cash flow.
