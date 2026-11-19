# CSX model build kit

`models/CSX_Model.xlsx` is the CSX Corporation (NASDAQ: CSX) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD / STE build kit:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CG2`, scenario table in `Model!CO:CS`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). 2026E (year ends 31-Dec-2026, six weeks after the valuation date) is the base year, the explicit years are 2027E–2031E and net debt is taken at 31-Dec-2026E.
  - Charts: total volume and revenue-per-unit growth, adjusted EBITDA / operating income, returns.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (calendar fiscal year; 52/53-week years to 2016)
- **C–I FY2006–FY2012:** annual, as originally reported.
- **J–BV Q1/13–Q4/25 with FY subtotals; BW–BY Q1/26–Q3/26:** grouped and collapsed like the template.
- **BZ Q4/26E, CA 2026E:** forecast; Q4/26E on the 9M-26 year-over-year trends, optionally calibrated to the (unverified) FY26 outlook.
- **CB–CF 2027E–2031E:** scenario forecast.
- **Right of the forecast** (template column + 1): CG notes, CI–CL CAGRs (5Y fwd '26–'31, 5Y, 10Y, 19Y), CO–CS scenario table.

## Basis
- **Policy:** as originally reported, from each period's own earnings release (Ex. 99.2 Quarterly Financial Report). Q4 = the fourth-quarter release's three-month column.
- **Revisions not recast** (cell comments on the annual cells): the Q4-2013 release revised Q1–Q3/13 revenue (−$32m, accounts-receivable review); the Q2-2024 release revised prior periods for engineering scrap and support labor (immaterial). The quarter columns stay as first reported, so Σ quarters ≠ FY for 2013 and 2024 (documented in `check_data.py`). The 2018 releases reclassified 2017 for ASU 2017-07 (pension cost below operating income; FY2017 OI $3,667m → $3,720m) — memo row in the adjusted-OI bridge.
- **Markets:** current basis (Chemicals / Agricultural & Food Products / Minerals / Automotive / Metals & Equipment / Forest Products / Fertilizers; Intermodal; Coal; Trucking from Q3/21; Other) from the Q3-2016 release; Q3/15–Q2/16 and FY2015 from the recast comparatives of the Q3-16 … Q2-17 releases (cell comments). Legacy bases (2006–Q1/10: automotive outside merchandise, coke & iron ore inside coal, intermodal by international / domestic; Q2/10–Q4/12: eight merchandise markets; Q1/13–Q2/16: Minerals and Waste & Equipment) are memo rows with a Σ check; the group rows (merchandise, intermodal, coal, other) run through all periods with a definition-flag row.
- **Segments:** one rail operating segment plus Quality Carriers trucking (acquired 1-Jul-2021, not reportable). Rail / Intermodal reportable segments to Q1/10 are memo rows.
- **Per-share data:** restated for the 3-for-1 splits effective 31-May-2011 and 28-Jun-2021 (×9 before Jun-2011, ×3 to Jun-2021) by the filing date of each document, including XBRL facts.
- **53-week years:** 2010 and 2016 (14-week fourth quarters); calendar quarters from 2017.
- **Cash flow:** quarters derived from year to date (Q4 = FY − 9M). "Other operating activities" (incl. working capital) is the derived residual.

## Model structure (Model tab)
- **Operating build:** volume (thousands of units) × revenue per unit ($) for the seven merchandise markets, intermodal and coal; trucking and other revenue by growth; Σ = total revenue (check vs reported, ±1). A volume / revenue-per-unit growth bridge, fuel-surcharge memo, coal tonnage, operating statistics (RTM, GTM, velocity, dwell, employees).
- **Cost build:** labor & fringe and purchased services & other as % of revenue; fuel = locomotive gallons (GTM × efficiency) × price per gallon + non-locomotive fuel; D&A as % of opening net properties; rents % of revenue; other lines as reported (gains on property dispositions, goodwill impairment, restructuring, inland transportation, Conrail / insurance / other operating income 2006–08). Operating ratio and y/y bps.
- **Future M&A lever:** spend ÷ EV/sales, margin, PP&E / intangibles split, amortization (Base nil).
- **FY26 calibration (optional, UNVERIFIED anchors):** CSX files no numeric guidance. The scenario table carries the Q3-26 call commentary found by web search ("high single digit" 2026 revenue growth → 9 / 8 / 7%; Q4 margin improvement "above 300–350 bps" → 400 / 350 / 300 bps on the Q4/25 margin of 31.6%), flagged UNVERIFIED. A revenue Δ on revenue-per-unit growth and a margin Δ on the labor / purchased-services ratios solve to them; clearing the cells sets both Δ to 0 and the quarter runs on the 9M-26 y/y trends. Verified on EDGAR and used as a point estimate: 2026 capital investment "less than $2.4bn" (Q3-26 10-Q).
- **GAAP P&L from the build:** revenue − expense lines = operating income; interest on opening debt; tax at the input rate; diluted shares from the buyback schedule.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **Operating income → adjusted operating income:** company items only — 2006–08 "comparable" (insurance recovery gains; Surface Transportation basis-difference line), 2017 restructuring charge and Q4/17 Tax Reform remeasurement, Q4/24 and Q3/25 Quality Carriers goodwill impairments; adjusted = GAAP otherwise (definition flags).
  2. **Net earnings → EBITDA → adjusted EBITDA → adjusted EBIT:** model definition (CSX publishes no EBITDA); adjusted EBIT = adjusted operating income.
  3. **Net earnings → adjusted net earnings → adjusted EPS:** company definition where published (2006–08 comparable EPS from continuing operations, per-share only → $m = EPS × diluted shares; 2017; 2024–25); tax effect derived from the published figures.
- **Other schedules:** cash flow (company FCF definition: + other investing to 2021, + property disposition proceeds from 2022, flagged); buybacks (Q4/26E scenario input; 2027E+ leverage plug to 2.5 / 2.25 / 2.0x net debt / adjusted EBITDA); balance sheet (condensed as in the releases); working capital (other current assets / liabilities % of revenue); properties and affiliates roll-forwards; debt (10-K maturity ladder refinanced at 5%, commercial paper to a $800m minimum cash balance, borrowings above the $1.0bn CP program termed out into notes as a labelled assumption); ratios and valuation.
- **DCF basis:** NOPAT on adjusted operating income less cash restructuring; D&A added back; property additions and M&A deducted; opening IC = 2026E book IC; no leases in net debt; market inputs are assumptions (rate sources not reachable).

## Key forecast assumptions (Base)
- **Volume 2027E–31E:** merchandise +2% → +1.5% with per-market offsets (chemicals / metals +1pp, automotive / fertilizers −1.5pp, forest −1pp); intermodal +5% → +3%; coal −2% → −3%.
- **Revenue per unit:** merchandise +3.5% → +3%; intermodal +3% → +2.5%; coal flat then +1%; trucking revenue +3%; other revenue 3.9% of rail freight revenue.
- **Costs:** labor 20.5% → 19.5% of revenue; purchased services 16.7% → 16.0%; fuel $3.70/gal with 1% p.a. efficiency gain; D&A 4.6% of opening net properties; rents 2.3%; tax 24.5%; other income $90m.
- **Capital:** property additions 15.5% → 15% of revenue; dividends +8% p.a. ($0.14 quarterly from Mar-2026); buybacks to 2.25x leverage; maturities refinanced; M&A nil.
- **Share price $47.67:** the September 2026 average price paid for repurchased shares (Q3-26 10-Q Part II Item 2) — the latest share price in an SEC filing; input at `Model!CA` in the valuation block; update to market.

## Data corrections
- None applied. Known, documented exceptions (`check_data.py`): FY2013 and FY2024 Σ quarters ≠ FY (company revisions of prior quarters); FY2017 and FY2021 within-year reclassifications between expense lines (total expense ties); Q4/23 XBRL three-month facts first tagged after the 2024 revision; 2020 company FCF differs by $30m from the cash-flow lines (other-investing classification in the company table; check tolerance widened for 2020 only).

## Sources
SEC EDGAR only (CIK 0000277948):
- Forms 10-K FY2006–FY2025 and 10-Q Q1/07–Q3/26 (notes: debt, goodwill and intangibles, acquisitions, share repurchases, dividend).
- Form 8-K Item 2.02 earnings releases (Ex. 99.1 / 99.2), Q4-2006 (22-Jan-2007) – Q3-2026 (21-Oct-2026): 80 releases.
- 8-Ks: stock splits (4-May-2011, 4-Jun-2021), notes issuances, Quality Carriers (Jul-2021) and Pan Am (Jun-2022).
- XBRL company facts: dividends per share, share-based compensation, shares outstanding (10-K balance sheets, 10-Q cover pages), goodwill and intangibles, receivables, and cross-checks of revenue, operating income, net earnings, EPS and total assets.

The investor-relations site (investors.csx.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR. `filings.csv` indexes the filings; each `data/<period>.json` lists its source URLs; `data/_releases.json` indexes the releases and `data/_xbrl.json` holds the XBRL subset. `manual_items.json` holds the company adjusting items by period, the 2017 ASU 2017-07 restatement, deals, goodwill / intangibles, debt facts, buyback authority, dividend, the share price and the unverified outlook, each with its source.

Outlook outside EDGAR: the FY26 revenue-growth and margin anchors come from a third-party summary of the 21-Oct-2026 earnings call found by web search (the transcript and the IR presentation are not reachable) and are marked UNVERIFIED in the workbook.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export CSX_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`.
   3. `python3 check_data.py` runs ~2,460 checks: statement arithmetic, market sums and volume × RPU, adjusted-measure bridges, EPS, cash and balance-sheet tie-outs, XBRL cross-checks and quarters vs years. The known exceptions above are listed separately.
3. Build: `python3 build.py --snap --recalc` writes `../CSX_Model.xlsx`, reruns with the switch on Bull and Bear to fill the snapshot panels, then stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`). `bash qa.sh --snap --recalc` does the build plus the three QA tools.
4. Validate:
   - `python3 ../tools/inspect_model.py <recalculated.xlsx>` → 0 error cells, 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../CSX_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../CSX_Model.xlsx --extra Woodward WWD 382.17` → 0 residue hits.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`: EDGAR filings index, downloads, HTML → text.
- `parse_release.py`: release parser (tables identified by content; three HTML eras).
- `extract.py`: per-period extraction (statements, markets, fuel, coal, statistics, special-item tables, cash flow, balance sheet, XBRL extras, prior-year comparatives).
- `xbrl.py`: XBRL company-facts helper (calendar fiscal year; split restatement by filing date).
- `normalize.py`: basis rules, flat model keys, market mapping and recast comparatives, split restatement, discrete quarterly cash flow.
- `check_data.py`: data consistency checks.
- `qa.sh`: build + recalculate + inspect + cycle scan.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
