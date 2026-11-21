# JBHT model build kit

`models/JBHT_Model.xlsx` is the J.B. Hunt Transport Services, Inc. (NASDAQ: JBHT) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD build kit with the trucking lessons of ODFL, SAIA, XPO and CHRW:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CF2`, scenario table in `Model!CN:CR`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). The 2026E cash flow is excluded from the present value because net debt is taken at year-end 2026E.
  - Charts: Intermodal volume vs revenue per load, adjusted EBITDA / operating income, returns (2006–2025).
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (calendar fiscal year; same column map as the template)
- **C–I FY2006–FY2012:** annual, as originally reported.
- **J–BV Q1/13–Q4/25 with FY subtotals; BW–BY Q1/26–Q3/26:** grouped and collapsed like the template.
- **BZ Q4/26E, CA 2026E:** forecast. J.B. Hunt gives no revenue or earnings guidance, so Q4/26E follows historical Q3→Q4 seasonality; the FY26 tax rate and net capital expenditures follow the company's outlook.
- **CB–CE 2027E–2030E:** scenario forecast.
- **Right of the forecast** (template columns, no shift): CF notes, CH–CK CAGRs (5Y fwd '25–'30, 5Y, 10Y, 19Y), CN–CR scenario table.

## Basis
- **Policy:** as originally reported, from each period's own earnings release.
- **Segment recasts** (taken from the following year's release comparatives; each recast cell carries a comment):
  - FY2006: Integrated Capacity Solutions (ICS) was separated from Truck in 2007.
  - FY2019 and Q1–Q4/19: Final Mile Services (FMS) was separated from Dedicated (DCS) in Q1-20. Dedicated as originally reported in 2019 is kept as memo rows. 2018 and earlier Dedicated figures include final mile and were never recast, so the 2019 y/y change in DCS is not like-for-like; the "Dedicated + Final Mile" memo rows are comparable across the break.
- **Segments as reported per year:** Truck, Intermodal, Dedicated (2006); + ICS (2007–2018); + FMS (2019 recast onward). "Truck" was renamed "Truckload" in Q3-21.
- **Per-share data:** no stock split since the 2-for-1 of May-2005; no share classes. Basic shares come from XBRL (Q4 = 4 × FY − Σ Q1–Q3); dividends per share from XBRL (Q4 = FY − 9M).
- **Cash flow:** the releases give only two supplemental cash-flow figures, so the statements come from XBRL company facts as first filed (FY2006–07 from the FY2008 10-K). Quarters are derived from year to date (Q4 = FY − 9M).
- **Adjusted measures:** J.B. Hunt publishes none. Every adjusted line is a labelled model definition that adds back only the items the company quantified in its releases.

## Model structure (Model tab)
- **Operating build (unit economics per segment):**
  - Intermodal, ICS, Truckload: loads × revenue per load.
  - Dedicated: average trucks × revenue per average truck.
  - Final Mile: stops × revenue per stop.
  - Revenue per unit = segment revenue ÷ volume, on gross revenue including fuel surcharge, so the statistics tie exactly to reported revenue. The published revenue per load / per truck per week are memo rows.
  - Segment operating income = revenue × operating margin; operating ratio and incremental margin are shown per segment.
  - Group: Σ segments − intersegment eliminations (+ M&A lever) with checks against consolidated revenue and operating income, and a volume / revenue-per-unit / other revenue bridge with a check.
- **Future M&A lever:** spend ÷ EV/revenue (0.5x), 4% margin, PP&E / intangibles / goodwill split, 10-year amortization. Base: no acquisitions.
- **Q4/26E (no guidance):** each segment's volume, revenue per unit and margin = Q3/26 × or + the historical Q3→Q4 change for 2016–2025: upper quartile (Bull), average (Base), lower quartile (Bear). The history sits in "Q3→Q4 sequential change" rows (Q4 columns). An optional FY26 EPS target cell is left blank.
- **Company outlook applied (the only forward statements on EDGAR), each with a check row that reads 0:**
  - FY26 annual tax rate ≈ 24.0%: Q4/26E tax is solved so the full-year rate matches.
  - FY26 net capital expenditures ≈ $700m.
- **GAAP P&L from the build:** operating income = segment build. Expense lines are % of revenue (Q4/26E at the Q3/26 ratios; then held); rents and purchased transportation is the balancing line. Net interest on opening debt and cash; tax 24%.
- **GAAP → adjusted bridges** (model definitions; no published figures exist to check against, so the checks run against XBRL facts and arithmetic identities):
  1. **Operating income → adjusted operating income:** + company-quantified charges / (benefits). The definition row flags each period with an item, and the cell comment quotes the release.
  2. **Net earnings → EBITDA → adjusted EBITDA:** check EBITDA = operating income + D&A. Continues to adjusted EBIT, full-cost.
  3. **Net earnings → adjusted net earnings → adjusted EPS:** tax effect = the company's after-tax figure where stated (Q4-16, Q3-18), otherwise the period rate bounded to 15–40%; discrete tax items (Q1-17 credits, Q4-17 Tax Act) removed.
- **Other schedules:** cash flow (net capital expenditures as the company defines them; free cash flow is a model definition); buybacks; balance sheet; working capital on a revenue basis; debt ($300m term loans due Nov-2028 and $750m 4.90% notes due Mar-2030 refinanced; revolver to a $20m minimum cash, with a headroom memo against the $1.0bn commitment); leverage-target buybacks from 2027E (net debt / adjusted EBITDA 1.0x / 0.8x / 0.6x); ratios and valuation.
- **DCF basis:** NOPAT on adjusted EBIT after all D&A and share-based compensation; total D&A added back; net capital expenditures; operating leases not treated as debt; opening invested capital = 2025A book equity + net debt. Market inputs (risk-free 4.25%, ERP 5%, beta 1.1) are assumptions.

## Key forecast assumptions (Base)
- **Intermodal:** loads +5% → +3%; revenue per load +1% → +2.5% (fuel surcharge held flat); margin 8.5% → 10.0% (9M/26 8.1%).
- **Dedicated:** average trucks +2–3%; revenue per truck +1% → +2.5%; margin 10.0% → 11.5% (9M/26 10.0%).
- **ICS:** loads +6% → +3%; revenue per load flat in 2027E, then +2%; margin 2.0% → 3.0%.
- **Final Mile:** stops −2% then +2–3%; revenue per stop +2–3%; margin 2.0% → 4.0%.
- **Truckload:** loads +2–3%; revenue per load flat in 2027E, then +2%; margin 3.0% → 4.0%.
- **Other:** D&A 5.1% of revenue; net capex 5.5–6.0% of revenue; tax 24%; DPS +3% p.a.; Q4/26E buybacks $175m. All are assumptions citing history in the scenario-table notes.
- **Unverified statements:** long-term segment margin ranges and a ~1x leverage target are attributed to investor presentations / earnings calls. They are not in an SEC filing, are labelled UNVERIFIED in the scenario table, and are not used as inputs.

## Data corrections
- **Q3-19:** the release (17-Oct-2019) showed operating income $212.1m and net earnings $151.2m. It pre-dated the final BNSF arbitration award (8-K 30-Oct-2019); $44.2m of pre-tax charges were booked in the Q3-19 Form 10-Q. The model uses the Q3-19 statement of earnings as presented in the Q3-20 release comparative (= the 10-Q: operating income $167.9m, net earnings $118.4m). Recorded in `manual_items.json` → `corrections`.
- **Known exceptions (documented, not corrected):**
  - FY2019 Final Mile stops: Σ recast quarters differs from the recast year by 53 thousand stops; the annual figure is used for the year.
  - Release supplemental cash-flow figures differ from the filed statements in FY2009, FY2017, Q1–Q2/15, Q3/17 and Q1/19 (preliminary figures); the filed statements are used.

## Sources
SEC EDGAR only (CIK 0000728535):
- Forms 10-K / 10-Q FY2006–Q3 2026 (cash-flow statements via XBRL; FY2008 and FY2009 10-K text for 2006–2009).
- Form 8-K earnings releases (Ex. 99.1), Q4 2006 – Q3 2026, plus the 8-Ks of 12-Oct-2018 and 30-Oct-2019 (pre-announced charges; arbitration award).
- XBRL company facts for cash flow, basic shares, dividends per share, goodwill and intangibles, and the operating-income / net-earnings cross-checks.

The investor-relations site (jbhunt.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR. `filings.csv` indexes the filings, and each `data/<period>.json` lists its source URLs. `manual_items.json` holds the company-quantified items, the 2026 outlook statements, FY2006–07 cash flow and per-share data, debt facts, the amortization schedule, the buyback authorization, the correction and the share price, each with its source.

The share price ($237.64) is the average price paid for shares repurchased in September 2026 (Q3-26 Form 10-Q Part II Item 2, filed 23-Oct-2026), the latest share price in an SEC filing. It is an input at `Model!CA` in the valuation block; update it to market.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export JBHT_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`.
   3. `python3 check_data.py` runs 1,541 checks: statement arithmetic, segment sums, EPS, XBRL cross-checks, cash and balance-sheet tie-outs, published revenue per load vs revenue ÷ loads, and quarters vs years. Known exceptions: the two listed above (the cash-flow differences print as information).
3. Build: `python3 build.py --snap --recalc` writes `../JBHT_Model.xlsx`, reruns with the switch on Bull and Bear to fill the snapshot panels, and stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../JBHT_Model.xlsx` should show 0 error cells and 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../JBHT_Model.xlsx` should show 0 cycles.
   - `python3 ../tools/residue_scan.py ../JBHT_Model.xlsx --extra WWD Woodward 382.17` should show 0 residue hits.
   - Intentional exceptions: Charts show `#N/A` for RONTA / ROIC only where a year has no value (none at present).

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `h2t.py`, `make_index.py`, `fetch.py`: EDGAR HTML → text, filings index, downloads.
- `parse_release.py`: release parser (typed sections; repairs split-letter labels; types sections by content when headings are missing).
- `extract.py`: per-period extraction (statements, segments, statistics, balance sheet, XBRL cash flow, prior-year comparatives).
- `xbrl.py`: XBRL company-facts helper.
- `normalize.py`: basis rules, recasts, flat model keys, discrete quarterly cash flow.
- `check_data.py`: data consistency checks.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
