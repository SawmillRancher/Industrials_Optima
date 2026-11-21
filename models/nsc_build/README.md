# NSC model build kit

`models/NSC_Model.xlsx` is the Norfolk Southern Corporation (NYSE: NSC) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD / STE build kit (statements and scenario machinery) and the ODFL kit (operating-ratio build):
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CG2`, scenario table in `Model!CO:CS`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). 2026E (ends six weeks after the valuation date) is the base year; explicit years 2027E–2031E; net debt at 31-Dec-2026E.
  - Charts: units / revenue-per-unit growth, adjusted EBITDA / income from railway operations, returns.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (calendar fiscal year)
- **C–I FY2006–2012:** annual, as originally reported (fourth-quarter releases).
- **J–BV Q1/13–Q4/25 with FY subtotals; BW–BY Q1/26–Q3/26:** grouped and collapsed like the template.
- **BZ Q4/26E, CA 2026E:** forecast, anchored on 9M-26 / Q3-26 trends and operating-ratio seasonality (NSC files no numeric guidance).
- **CB–CF 2027E–2031E:** scenario forecast.
- **Right of the forecast** (template column + 1): CG notes, CI–CL CAGRs (5Y fwd '26–'31, 5Y, 10Y, 19Y), CO–CS scenario table.

## Basis
- **Policy:** as originally reported, from each period's own earnings release (income statement, balance sheet, year-to-date cash flow).
- **Recasts:** FY2006–07 operating-expense lines use the FY2008 10-K recast into the five classifications used since 2008 (totals unchanged; the original seven-line presentation is in the cell comments). FY2017 is kept as originally reported; the 2018 releases restated it for ASU 2017-07 (operating expenses $6,965m → $7,029m; noted in a cell comment). 2006 cash / short-term investments (one balance-sheet line) are split with the cash-flow ending cash.
- **Segments:** one reportable segment (railway operations). Revenues by commodity group (merchandise / intermodal / coal; "General merchandise" to 2012) are on the income statement; units and revenue per unit come from the 10-Q / 10-K MD&A market-group tables (Q4 = year − nine months; Q4 revenue per unit derived). Merchandise market groups are memo rows on each published basis (five groups to 2018; 2019 five groups incl. "Forest and consumer"; four groups from 2020), with a definition-flag row.
- **Adjusted measures:** NSC publishes reconciliations only when special items occur: Q4/FY2017 (tax reform), Q1/Q3/FY2020 (locomotive rationalization, investment impairment), 2023+ (Eastern Ohio incident), 2024 (restructuring, railway line-sale gains, shareholder advisory costs, deferred-tax adjustment), Q3-25+ (merger-related expenses). Other periods: adjusted = GAAP, flagged. Adjusted EBITDA is a model definition (adjusted income from railway operations + depreciation, the construction used in the merger proxy projections).
- **Per-share data:** no stock splits; 2006–07 share counts converted from thousands. To 2016 NSC applied the two-class method, so net income ÷ diluted shares can differ from reported EPS by up to ±$0.02.
- **Cash flow:** quarters derived from year-to-date (Q4 = FY − 9M). Share-based compensation and deferred taxes come from XBRL / the cash-flow statement.

## Model structure (Model tab)
- **Operating build:** three commodity groups, each units × average revenue per unit (revenue per unit includes fuel surcharges). Q4/26E = prior-year quarter × (1 + 9M-26 y/y units trend + Δ) and × (1 + Q3-26 y/y revenue-per-unit trend + Δ). 2027E+ scenario levers per group. Volume / revenue-per-unit bridge with Σ check; memo KPIs (intermodal domestic / international, coal tonnage by market, fuel surcharge revenue where disclosed).
- **Operating-ratio build:** compensation & benefits, purchased services & rents and materials & other as % of revenues; fuel from the Q3-26 y/y trend (Q4/26E) and a % of revenues lever (2027E+); depreciation from the properties roll-forward. Q4/26E anchor = Q3/26 adjusted operating ratio + the 2016–25 Q3→Q4 sequential change (best / average / worst, 2024 excluded), hit by a uniform proportional shift on the three variable lines. 2027E+: adjusted operating-ratio lever. Special items (merger, restructuring, Eastern Ohio incident, asset-disposal loss, items inside regular lines, incident effects outside the line item) are separate rows.
- **Pending merger block:** Union Pacific consideration (1.0 UNP share + $88.82 cash) at an input UNP price, implied equity value / EV / EV-EBITDA, premium to the current price, gross and annualised spread to an assumed closing (30-Jun-2027, model assumption), the $2.5bn termination fee per share and cumulative merger costs. The operating forecast is standalone in all scenarios; buybacks are nil while the merger is pending (2026E–27E) and resume from 2028E through a capped leverage plug.
- **GAAP P&L from the build:** income from railway operations = revenues − cost lines − special items; other income = yield on opening investments + input; interest = rate × opening notes + rate × opening commercial paper; tax at 23.3% (Q4/26E) then 23.5%.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **Income from railway operations → adjusted income from railway operations / adjusted operating ratio:** company items (merger, restructuring, incident, 2020 impairments, 2024 line-sale gains, 2017 tax-reform effect, incident effects outside the line item).
  2. **Net income → EBITDA → adjusted EBITDA:** model definition (adjusted OI + depreciation); continues to adjusted EBIT for NOPAT / DCF.
  3. **Net income → adjusted net income → adjusted EPS:** operating and non-operating items (2024 shareholder advisory costs), the tax effect derived from the published adjusted EPS, discrete tax items (2017 remeasurement, 2024 deferred-tax adjustment).
- **Other schedules:** cash flow (NSC line structure; "other – net" derived); buybacks; balance sheet; working capital (DSO, materials & supplies and payable days on cash operating expenses, taxes and other current liabilities % of revenues); properties roll-forward; debt (10-K maturity ladder, refinancing %, commercial paper / assumed new debt to a $1.0bn minimum cash balance); capped leverage-target buybacks from 2028E; ratios and valuation.
- **DCF basis:** NOPAT on adjusted income from railway operations less cash special items; depreciation added back; capex only (no M&A); no leases in net debt; terminal growth 3%; market inputs (risk-free 4.25%, ERP 5%, beta 1.0) are assumptions.

## Key forecast assumptions (Base)
- **Volumes 2027E–31E:** merchandise +2% → +1.5%; intermodal +3% → +2%; coal −3% p.a. **Revenue per unit:** merchandise +3%; intermodal +2–2.5%; coal 0 → +1% (scenario table; rationale notes cite 9M-26 trends and 2015–25 CAGRs).
- **Adjusted operating ratio:** 63.5% (2027E) → 60.0% (2031E); fuel 10% → 9.5% of revenues. The management long-range plan from the merger proxy (61.8% → 58.7%, 2027–30) is shown as information rows only.
- **Capex** 17% → 16% of revenues (2026E $2.1bn per the 10-Q); depreciation 3.9% of opening net properties; tax 23.5%; DPS +5% p.a.; buybacks capped at $3.5bn p.a. from 2028E to a 2.5x net debt / adjusted EBITDA ceiling.
- **Share price $332.09:** the price of shares withheld for taxes on RSU vestings on 24-Oct-2026 (Forms 4 filed 26-Oct-2026), the latest share price in an SEC filing; UNP $300.62 (UNP Forms 4, 10-Nov-2026). Update both at `Model!CA` in the valuation / merger blocks.

## Data corrections
- None. Known data exceptions (documented, not corrected):
  - Published revenue per unit is rounded to $1, so units × revenue per unit differs from reported revenue by up to ~$2m (check tolerance ±$1m + $0.6 per thousand units).
  - 2018–19 cash-flow cash includes restricted cash (ASU 2016-18; $86–88m), shown as a memo row in the balance-sheet checks.
  - 2025 "Eastern Ohio incident" income-statement line (−$254m) differs from the company's reconciliation effect (−$190m); the $64m sits in other expense lines and is carried as a separate bridge row.

## Sources
SEC EDGAR only (CIK 0000702165):
- Forms 10-K FY2006–FY2025 and 10-Q Q1/13–Q3/26 (MD&A market-group, coal tonnage, intermodal, expense tables; debt and incident notes).
- Form 8-K Item 2.02 earnings releases (financial statements exhibits; Ex. 99.1 press releases with the non-GAAP reconciliations), Q4-06 – Q3-26.
- Merger filings: 8-K 29-Jul-2025 (Merger Agreement), DEFM14A 1-Oct-2025 (management projections, fairness opinions), 8-K 17-Nov-2025 (shareholder vote), 8-K 19-Dec-2025 (STB application); Union Pacific Forms 4 (CIK 100885) for the UNP price.
- XBRL company facts: share-based compensation, deferred taxes, shares outstanding, dividends declared, operating income / net income cross-checks.

The investor-relations site (norfolksouthern.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR. `filings.csv` indexes the filings, and each `data/<period>.json` lists its source URLs. `manual_items.json` holds the merger terms, the long-range plan, debt facts, buyback / dividend facts, items booked inside regular lines (with sources) and the share prices.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export NSC_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`.
   3. `python3 check_data.py` runs ~2,260 checks (statement arithmetic, commodity-group and market-group sums, revenue per unit, published adjusted figures vs items, EPS, cash and balance-sheet tie-outs, XBRL cross-checks, prior-year comparatives, quarters vs years). Known exceptions: revenue-per-unit rounding (±$2m) and share-count rounding on EPS (±$0.015); the 2018 ASU 2017-07 restatement and 2018–19 restricted cash are listed as documented exceptions.
3. Build: `python3 build.py --snap --recalc` writes `../NSC_Model.xlsx`, reruns with the switch on Bull and Bear to fill the snapshot panels, and stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../NSC_Model.xlsx` → 0 error cells, 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../NSC_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../NSC_Model.xlsx --extra WWD Woodward 382.17` → 0 residue hits.
   - Intentional exceptions: Charts `#N/A` is not used (balance sheets exist for every year).

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, cell comments, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`: EDGAR filings index, downloads, HTML → text.
- `parse_release.py`: statement and MD&A table parser (content-based table typing, column resolution by era, market-group tables incl. percent-change columns).
- `extract.py`: per-period extraction (statements, market groups, KPIs, non-GAAP reconciliations, XBRL extras, prior-year comparatives).
- `xbrl.py`: XBRL company-facts helper (calendar year).
- `normalize.py`: basis rules, flat model keys, discrete quarterly cash flow, special-item mapping.
- `check_data.py`: data consistency checks.
- `inspect_model.py`, `cyc.py`: QA tools (copies of `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
