# UPS model build kit

`models/UPS_Model.xlsx` is the United Parcel Service, Inc. (NYSE: UPS) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD build kit:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CF2`, scenario table in `Model!CN:CR`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows. The price target is shown for 2028E–2030E in all three panels.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). The 2026E cash flow is switched off (`DCF!C28 = 0`) because net debt is taken at YE2026E.
  - Charts: U.S. Domestic volume vs revenue per piece, adjusted EBITDA / operating profit, returns.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (calendar fiscal year)
The layout is the template's own (column shift 0):
- **C–I FY2006–FY2012:** annual, as originally reported.
- **J–BV Q1/13–Q4/25 with FY subtotals; BW–BY Q1/26–Q3/26:** grouped and collapsed like the template.
- **BZ Q4/26E, CA 2026E:** forecast, calibrated to the FY26 guidance (Q3-26 release, 27-Oct-2026).
- **CB–CE 2027E–2030E:** scenario forecast.
- **Right of the forecast:** CF notes, CH–CK CAGRs (5Y fwd '25–'30, 5Y, 10Y, 19Y), CN–CR scenario table.

## Basis
- **Policy:** as originally reported. Each period comes from its own earnings release (segments, operating data, adjusted measures) and its own Form 10-K / 10-Q (operating-expense detail, balance sheet, cash flow).
- **Not recast** (flagged in the definition rows):
  - FY2006–FY2010 are on the pension accounting in force before UPS adopted mark-to-market (10% corridor) accounting in Q4-2011. The 8-K of 27-Jan-2012 recast 2007–2011; it is not used.
  - FY2017 and earlier are before ASU 2017-07 (adopted Q1-2018): non-service pension cost, including the year-end mark-to-market, sits in operating expenses to 2017 and in other income from 2018.
- **Two documented exceptions to "own release"** (cell comments quote the original figures):
  - **FY2020 / Q4-2020: the 10-K wins.** The release (2-Feb-2021) recorded a $556m UPS Freight held-for-sale impairment; the 10-K (22-Feb-2021) recorded $686m. Operating profit, tax, net income and EPS take the 10-K values; Q4 = 10-K fiscal year − nine months. Adjusted measures are unchanged.
  - **Q1–Q3 2024 segments: recast basis.** The Q4-2024 release moved air cargo from Supply Chain Solutions to U.S. Domestic Package ("Cargo and Other") and presented FY2024 that way, so the three quarters take the prior-year columns of the 2025 releases. All four quarters are then on one basis and tie to the year.
- **Segments:** U.S. Domestic Package, International Package, Supply Chain Solutions ("Supply Chain & Freight" to Q1-2021; UPS Freight sold 30-Apr-2021; Coyote divested 16-Sep-2024). UPS allocates all costs to segments, so there is no corporate line.
- **Per-share data:** no stock splits in the period. Class A and class B shares have the same per-share amounts; shares outstanding = class A + class B shares issued (balance-sheet captions).
- **Cash flow:** quarters derived from year to date (Q4 = FY − 9M). Operating-expense detail for Q4 = fiscal year (10-K) − nine months (Q3 10-Q) where the release has no quarterly table (before 2021).
- **Q3-2026:** the 8-K of 27-Oct-2026 has no Ex. 99.2 financial schedules on EDGAR. Segment revenue / operating profit and the reconciliations come from Ex. 99.1; the income statement, operating data, shares, balance sheet and cash flow come from the Q3-2026 Form 10-Q.

## Model structure (Model tab)
- **Operating build:**
  - U.S. Domestic Package (Next Day Air, Deferred, Ground) and International Package (Domestic, Export): average daily package volume (000) × average revenue per piece × operating days = product revenue, plus "Cargo and Other". A ratio row ties the published statistics to revenue (≈ 1.000).
  - Supply Chain Solutions: Forwarding and Logistics (one line to Q3-2018, split in memo rows after), Freight (to Q2-2021), Other.
  - Segment profit = revenue × non-GAAP adjusted operating margin (company measure; = GAAP where none was published). GAAP segment profit = adjusted − adjusting items.
  - Model cost per piece, consolidated volume / revenue per piece, contribution to growth.
- **Future M&A lever:** spend ÷ EV/sales (3.0x, assumption), 10% margin after amortization, PP&E / intangibles / goodwill split, 15-year amortization. Base $200m a year.
- **FY26 guidance calibration (Q4/26E):**
  - Revenue: one uniform Δ on the Q3/26 y/y growth of every package product's volume and of the Supply Chain Solutions revenue lines, solved in closed form so FY26 revenue = $92.6bn (Base).
  - Margin: one uniform Δ on the three segment margins (prior-year quarter + Q3/26 y/y change; Supply Chain Solutions from its Q3/26 margin), solved so FY26 adjusted operating profit = $8.75bn (Base).
  - UPS gives point guidance, not ranges. The High / Low end-points (revenue ±$300m, adjusted operating profit ±$150m) are **model assumptions** and are labelled as such.
  - Information rows, not forced: Q4 revenue (~$25.7bn) and adjusted operating profit (~$3.3bn), adjusted EPS (~$7.28), adjusted free cash flow (~$6.1bn).
  - Base result: Q4/26E revenue $25,711m and adjusted operating profit $3,272m; FY26 adjusted EPS $7.30 (guided ~$7.28); free cash flow $6.2bn.
- **GAAP P&L from the build:** operating profit = adjusted operating profit − adjusting items. Expense lines other than compensation run as % of revenue; compensation and benefits is the balancing line. Interest is calculated on opening balances; tax at 23%.
- **GAAP → adjusted bridges** (checks vs published in every period the company published the measure):
  1. **Operating profit → non-GAAP adjusted operating profit:** adjusting items by segment = published adjusted segment profit − GAAP segment profit. The company's item wording per period is stored as a cell comment on the total row.
  2. **Net income → EBITDA → adjusted EBITDA:** model definition (adjusted operating profit + D&A). UPS reconciles adjusted EBITDA only on a trailing basis for its debt ratio; that measure is not rebuilt.
  3. **Net income → adjusted net income → adjusted EPS:** operating items + items below operating profit (pension mark-to-market from 2018) − tax effect. The historical tax effect is derived from published adjusted net income. In GAAP-loss quarters (Q4/16, Q4/19, Q4/20) the adjusted share count is the one stated in the release footnote.
- **Other schedules:**
  - Cash flow, with business-disposal proceeds split out of the PP&E disposal line (UPS Freight $848m, Coyote $1,002m) and pension expense netted against contributions.
  - Free cash flow on the company definition, rebuilt from the filed statements, with the published figure and the difference as information rows.
  - Buybacks; balance sheet; working capital on revenue (UPS has no cost of goods sold).
  - Debt: notes repaid at maturity and refinanced; commercial paper to a $5.0bn minimum cash balance, with a headroom memo vs the $3.0bn credit commitments.
  - Leverage-target buybacks, 2027E+: net debt / adjusted EBITDA of 1.6x / 1.5x / 1.4x.
  - Ratios and valuation.
- **DCF basis:**
  - NOPAT on adjusted operating profit (already after amortization and stock compensation) less transformation costs, with total D&A added back.
  - 2026E excluded (inclusion flag) because the EV bridge uses YE2026E net debt.
  - The EV bridge deducts net debt, NCI and the pension and postretirement obligation (~$5.6bn, gross of tax). Operating leases stay in operating costs.
  - Market inputs (risk-free 4.25%, ERP 5%, beta 1.0) are assumptions: government and market data are not reachable from the build environment.

## Key forecast assumptions (Base)
All are model assumptions with the history they rest on quoted in the scenario table:
- **U.S. Domestic:** volume −1.0% in 2027E (the largest customer's planned reduction annualises through 1H-27), then +1.0% / +1.5% / +1.5%; revenue per piece +3.0% then +2.5%; adjusted margin 8.0% → 9.5% by 2030E (9M-2026 6.3%, FY2022 11.8%).
- **International:** volume 0% then +2.0% / +2.5% / +2.5%; revenue per piece +3% then +2%; adjusted margin 15.0% → 16.8% (9M-2026 13.2%, FY2021 24.2%).
- **Supply Chain Solutions:** revenue +5% then +4%; adjusted margin 9.5% → 10.0%.
- **Other drivers:** D&A 4.2% of revenue; capex 3.8% → 4.4%; transformation costs $300m / $150m then nil; pension contributions $400m a year above expense; DPS +0.6% a year; tax 23%; M&A $200m a year.
- **Share price $105.39:** a Form 4 sale of class A shares on 28-Oct-2026 (filed 30-Oct-2026). This is the latest share price in an SEC filing; update it at `Model!CA` in the valuation block.

## Data corrections
- **FY2020 / Q4-2020:** the 10-K values replace the release (see Basis).
- **Q4-2018:** the release's three-month "Forwarding and Logistics" row (878) is Logistics; the twelve-month table shows Forwarding 6,580 / Logistics 3,234.
- Known data exceptions (documented, not corrected):
  - Published free cash flow for Q1-2025 / FY2025 differs from the filed cash-flow statement by $10m (other investing reclassified in the 10-Q).
  - Release free-cash-flow reconciliations before 2016 are "preliminary … subject to reclassification" and are shown as information only.

## Sources
SEC EDGAR only (CIK 1090727):
- Forms 10-K FY2006–FY2025 and 10-Q Q1-2013–Q3-2026.
- Form 8-K Item 2.02 earnings releases (Ex. 99.1 / 99.2), Q4-2006 – Q3-2026.
- Financing and other 8-Ks from 2024 (indexed in `filings.csv`).
- XBRL company facts: annual amortization of intangibles, and cross-checks of revenue, operating profit, net income, EPS, operating cash flow and total assets.
- Form 4 (30-Oct-2026) for the share price.

The investor-relations site (investors.ups.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR. The FY26 guidance is in the EDGAR-filed release, so no guidance in the model is unverified; the scenario High / Low end-points and all 2027E+ levers are model assumptions.
- `filings.csv` indexes the filings.
- Each `data/<period>.json` lists its source URLs; `data/_xbrl.json` holds the XBRL subset.
- `manual_items.json` holds the FY26 guidance, transformation programme, debt facts, the buyback authorization, deals, data corrections and the share price, each with its source.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export UPS_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`.
   3. `python3 check_data.py` runs 2,357 checks: statement arithmetic, segment and product sums, volume × revenue per piece × days vs product revenue, adjusted measures, cash and balance-sheet tie-outs, quarters vs years, and XBRL cross-checks. Known exceptions: the two free-cash-flow differences above.
3. Build: `python3 build.py --snap --recalc` writes `../UPS_Model.xlsx`, reruns with the switch on Bull and Bear to fill the snapshot panels, and stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../UPS_Model.xlsx` should show 0 error cells and 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../UPS_Model.xlsx` should show 0 cycles.
   - `python3 ../tools/residue_scan.py ../UPS_Model.xlsx --allow 'Model!CF2' --extra WWD Woodward 382.17` should show 0 residue hits. `Model!CF2` is allowed because it is UPS's own switch cell (the layout has no column shift).

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`: EDGAR filings index, downloads, HTML → text.
- `parse_release.py`: release / filing text parser (sections, rows, face statements).
- `extract.py`: per-period extraction (Selected Financial Data, Selected Operating Data, reconciliations, face statements, 10-Q MD&A tables for Q3-2026).
- `xbrl.py`: XBRL company-facts helper.
- `normalize.py`: basis rules, flat model keys, discrete quarterly cash flow, the documented corrections.
- `check_data.py`: data consistency checks.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
