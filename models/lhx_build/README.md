# LHX model build kit

`models/LHX_Model.xlsx` is the L3Harris Technologies, Inc. (NYSE: LHX) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `MODEL_BUILD_PLAYBOOK.md` (branch `claude/sweet-davinci-07af12`), adapted from the WWD build kit:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!BA2`, scenario table in `Model!BI:BM`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). 2026E (fiscal year ending 1-Jan-2027, six weeks after the valuation date) is the base year, so the explicit years are 2027E–2031E and net debt is taken at the 2026E year end.
  - Charts: revenue vs adjusted operating income growth, adjusted EBITDA / operating income, returns.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns
- **C–I FY2013–FY2019:** Harris Corporation fiscal years ended the Friday nearest 30 June (annual, as originally reported; FY2019 is the last pre-merger year).
- **J–K Q3/19–Q4/19, L 2H19 TP:** the six-month fiscal transition period 29-Jun-2019 – 3-Jan-2020 (Form 10-KT), the first period after the L3 merger. Quarters are grouped under the transition-period column.
- **M–AP Q1/20–Q4/25 with FY subtotals; AQ–AS Q1/26–Q3/26:** fiscal years ended the Friday nearest 31 December, grouped and collapsed like the template. FY2024 has 53 weeks; the 2025 quarters have 12 / 13 / 14 / 13 weeks.
- **AT Q4/26E, AU 2026E:** forecast, calibrated to the FY26 guidance (Q3-26 release, 29-Oct-2026).
- **AV–AZ 2027E–2031E:** scenario forecast.
- **Right of the forecast** (template column − 31): BA notes, BC–BF CAGRs (5Y fwd '26–'31, 5Y '20–'25, FY15–'25 = 10.5 years, FY13–'25 = 12.5 years), BI–BM scenario table.
- **Year-on-year comparisons:** 2020 and the 2019 transition period have no comparable prior-year column (Harris FY2019 is a pre-merger June year). Q3/20 and Q4/20 compare with the transition-period quarters. Ratio rows are blank in the transition-period column (not annualised).

## Basis
- **Policy:** as originally reported, from each period's own earnings release (10-K / 10-KT for annual columns; the 10-K wins where they differ).
- **One documented exception — segments on the current structure:** L3Harris reorganised into three segments from Q1-26 (Space & Mission Systems, Communications & Spectrum Dominance, Missile Solutions). The company recast 2025 by quarter (Q3-26 earnings appendix, 8-K Ex. 99.2) and FY2024 for the year only (Q4-25 release Table 9). Those periods use the recast segments and unallocated items (latest filing presenting the period; cell comments quote the originally reported totals). 2024 quarters and all earlier periods were never recast: they carry the segment totals of the structure in force, with the detail in the legacy memo rows.
- **Segments as reported per year (legacy memo rows, Σ checks):**
  - FY2013–15: RF Communications, Integrated Network Solutions, Government Communications Systems (+ Exelis for one month in FY2015).
  - FY2016: Communication Systems, Space and Intelligence Systems, Electronic Systems, Critical Networks. FY2017–19: the first three.
  - 2H19–2021: Integrated Mission Systems, Space & Airborne Systems, Communication Systems, Aviation Systems. 2022: three segments (Aviation Systems dissolved). Q3-23: Aerojet Rocketdyne added. 2025: Fuzing and Ordnance Systems moved from IMS to Aerojet Rocketdyne.
- **Restatements not recast** (cell comments): FY2016 re-presented for discontinued operations (CapRock, government IT services) in the FY2017 10-K; FY2018 re-presented for ASC 606 and ASU 2017-07 in FY2019; the 2021 segment recast for CAS pension cost; the 2022 IMS / SAS programme transfer; the 2024 recast of non-GAAP EPS without the amortization add-back.
- **Segment measure:** Harris segment operating income to FY2018; segment operating income including FAS pension income with a "Pension adjustment" reconciling line in FY2019–2021; CAS-basis segments with an unallocated FAS/CAS operating adjustment in 2022–2025; segment operating income excluding all unallocated corporate items from 2026. The definition row flags each change.
- **Per-share data:** no stock splits in the period. The L3 merger issued 104.1m shares (1.30 per L3 share) on 29-Jun-2019. Harris-era EPS uses the two-class method (check tolerance ±0.035 in FY2013–19).
- **Cash flow:** quarters derived from year to date (Q2 = H1 − Q1, Q3 = 9M − H1, Q4 = FY − 9M; Q4/19 = transition period − Q3/19). Share-based compensation and deferred taxes come from the statement where printed, otherwise from XBRL company facts; otherwise they stay in the derived working-capital line.
- **Non-service FAS pension income:** split out of the combined non-operating line with the figure disclosed in the 10-Q / 10-K / earnings appendix; Q4 = fiscal year − nine months where the Q4 release does not split it (cell comments).

## Model structure (Model tab)
- **Segment build:** three segments, revenue × segment operating margin = segment operating income; intersegment eliminations and other revenue outside the segments (divested businesses; from Q3-26 the amortization of the DoW program investment asset as a reduction of revenue); less unallocated corporate items (acquisition-related amortization, FAS/CAS adjustment, integration / LHX NeXt, transaction costs, divestiture items, impairments, other) = operating income. Checked against consolidated revenue and operating income in every period.
- **Orders and backlog:** orders, book-to-bill, total and funded backlog as published; a derived adjustments line closes the backlog roll-forward; forecast orders = revenue × book-to-bill.
- **Future M&A lever:** spend ÷ EV/sales (2.0x), 14% segment margin, PP&E / intangibles / goodwill split, 15-year amortization. Base spend is nil.
- **FY26 guidance calibration (Q4/26E):**
  - Revenue: each segment's Q4 = FY26 segment guidance − nine months actual, then one uniform Δ so FY26 revenue = $23.7bn / $23.6bn / $23.5bn (segment end-points don't sum exactly to the consolidated range).
  - Margins: guidance-implied Q4 segment margins ("mid 10%" read as 10.5%, "mid 25%" as 25.5%, "low 12%" as 12.2%: interpretations) plus one uniform Δ so FY26 GAAP diluted EPS = $12.35 / $12.30 / $12.25. The required Q4 operating income is back-solved in closed form through the deemed dividend, tax, non-operating income and interest.
  - Cash from operations: Q4 working capital is solved so FY26 CFO = the $3.6bn guidance, with contract assets as the balance-sheet offset.
  - Information rows, not forced: total segment margin ("low 16%"), free cash flow ($3.0bn).
- **GAAP P&L from the build:** operating income from the segment build; G&A at the nine-month ratio; cost of revenue is implied. Non-service FAS pension income is an input (non-cash; reversed in the cash flow and accreted to the net pension asset). Net interest on opening debt less yield on opening cash and short-term investments. Subsidiary preferred deemed dividends are deducted to reach net income available to common shareholders.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **Operating income → segment operating income (company) → adjusted operating income / EBITA (model):** operating income + acquisition-related amortization + the operating items the company excluded from non-GAAP EPS. Checked against the company's adjusted EBIT in FY2019–2021 (which includes non-operating income).
  2. **Net income → EBITDA → adjusted EBITDA:** EBITDA on the company definition (net income + taxes + net interest + D&A), checked against the published figures for FY2023, FY2024, FY2025, 4Q25 and 1Q–3Q26. Adjusted EBITDA is a model definition: operating income + D&A + operating adjusting items, so it excludes non-cash pension income.
  3. **Diluted EPS → non-GAAP diluted EPS:** company definition in force per period, flagged in the definition row. Published bridges are per share, so $m = per share × diluted shares (pre-tax $ amounts where the release gives them) with a labelled rounding line. The company stopped publishing non-GAAP EPS with the Q1-26 release: the FY2025 definition is rebuilt by the model from Q1-26, with a 24% tax rate on adjustments (assumption).
- **Free cash flow:** model definition CFO − capital expenditures (the company's definition from Q3-26), held constant; the company's free cash flow / adjusted free cash flow of each period is shown with the definition difference and a definition row.
- **Other schedules:**
  - Cash flow; buybacks; balance sheet (mezzanine equity for the subsidiary preferred stock); working capital.
  - PPAs: Viasat Tactical Data Links (Q1-23), Aerojet Rocketdyne (Q3-23).
  - Debt: notes repaid at maturity or refinanced; $1.0bn 2029 / 2032 notes issued 5-Nov-2026; commercial paper to a $1.0bn minimum cash, with a headroom memo vs the $2.5bn programme.
  - Leverage-target buybacks, 2027E+: net debt / adjusted EBITDA of 1.75x / 1.5x / 1.25x (assumptions; no published target).
  - Ratios and valuation.
- **DCF basis:**
  - NOPAT on adjusted operating income before acquisition-related amortization, less cash integration / transaction costs; depreciation and other amortization added back.
  - Non-service pension income is excluded from UFCF, and the net pension asset is not added to equity value.
  - The EV bridge deducts net debt (after cash and short-term investments), NCI and the DoW subsidiary preferred stock (mezzanine plus conversion-feature and warrant liabilities).
  - Market inputs (risk-free 4.25%, ERP 5%, beta 0.8) are assumptions: U.S. Treasury / FRED data are not reachable from the build environment. Cost of debt 5.3% is anchored on the Nov-2026 note coupons.

## Key forecast assumptions (Base)
- **Segment revenue growth 2027E–31E:** Space & Mission Systems 6% → 4%; Communications & Spectrum Dominance 5% → 4%; Missile Solutions 8% in 2027E (held back about 9 points by the Space Technology sale), then 16% → 10% on the $20bn backlog. Assumptions citing the 2026 trends and backlog.
- **Segment margins:** SMS 10.6% → 11.3%; CSD 25.3%; Missile Solutions 12.5% → 14.0%. Other unallocated items 0.7% of segment revenue.
- **Other drivers:**
  - Acquisition-related amortization per the FY2025 10-K schedule ($532m in 2027, $459m, $403m, $386m; $370m assumed for 2031).
  - Non-service FAS pension income $280m in 2027E, drifting to $240m (assumption).
  - Tax rate 16%; capex 3.0% of revenue in 2027E–28E, falling to 2.5%; DPS +4% a year.
  - Deemed dividends on the subsidiary preferred of $90–100m a year to Apr-2031 (assumption on phasing).
- **Not modelled:** the planned Qualified IPO of the Missile Solutions business (no terms filed); it would convert the preferred into subsidiary common stock and create a noncontrolling interest.
- **Guidance source:** EDGAR-filed releases only. The "2028 Financial Framework" the company mentions in its Q1-26 release is not in any EDGAR document, so it is not used; treat any figure for it as unverified.
- **Share price $255.00:** provided by the user on 20-Nov-2026 (input at `Model!AU` in the valuation block). For reference, the latest SEC-filed prices are the $282.50 average repurchase price in fiscal August 2026 and the $260.56 tax-withholding price in fiscal September 2026 (Q3-26 10-Q Part II Item 2). Update to market.

## Data corrections
- None. Known data exceptions (documented in `check_data.py`, not corrected):
  - **FY2013–14 EPS:** two-class method (participating securities); computed EPS differs from published by up to $0.03.
  - **Σ quarters vs year, cost of revenue / G&A:** FY2020 (+$52m G&A), FY2022 (±$32m), FY2023 (+$18m), FY2024 (+$14m). Later filings reclassified quarterly lines (impairment and COVID charges, the Q1-22 cost of revenue / ESA split). The year totals are from the 10-K.
  - **FY2021:** quarterly pension-income splits sum to $3m more than the year; capex differs by $7m (10-K gross of PP&E sale proceeds).
  - **FY2013 XBRL revenue:** the earliest fact tagged `Revenues` is a component line ($420m); the face statement ($5,111.7m) is used.

## Sources
SEC EDGAR only (CIK 0000202058; named Harris Corp until 25-Jun-2019):
- Forms 10-K FY2013–FY2025, the Form 10-KT for the transition period, and Forms 10-Q to Q3-26.
- Form 8-K Item 2.02 earnings releases (Ex. 99.1), Q4 FY2013 – Q3-26, the 2022–Q3-23 investor letters and the Q3-26 earnings appendix (Ex. 99.2).
- 8-Ks: $1bn DoW investment (Apr-2026), notes offering (5-Nov-2026), Space Technology sale announcement (Jan-2026).
- XBRL company facts: share-based compensation, deferred income taxes, and the cross-checks of revenue, net income and total assets.

The investor-relations site (l3harris.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR.
- `filings.csv` indexes the filings.
- Each `data/<period>.json` lists its source URLs; `data/_xbrl.json` holds the XBRL subset.
- `manual_items.json` holds the earnings-appendix recast (2025 quarters, FY2024), company EBITDA, the FY26 guidance history, the DoW investment terms, the Space Technology sale, debt facts, the buyback authorization, PPAs and the share price, each with its source.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export LHX_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 period_index.py`.
   3. Extract the new period to `data/<period>.json` following `EXTRACTION_SCHEMA.md`. `extract_2026.py` does this for the 2026-format releases. The FY2013–2025 records were extracted by four parallel agents on the same schema.
   4. `python3 xbrl.py` refreshes `data/_xbrl.json`.
   5. `python3 check_data.py` runs 712 checks: statement arithmetic, segment build, non-GAAP EPS, adjusted EBIT and EBITDA vs published, cash and balance-sheet tie-outs, quarters vs years, and the XBRL cross-check. Known exceptions are listed above.
3. Build: `python3 build.py --snap --recalc` writes `../LHX_Model.xlsx`, reruns with the switch on Bull and Bear to fill the snapshot panels, and stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../LHX_Model.xlsx` → 0 error cells, 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../LHX_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../LHX_Model.xlsx --extra WWD Woodward 382.17` → 0 residue hits.
   - Intentional exceptions: Charts show `#N/A` returns for the transition-period column (ratios are not annualised).

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`, `period_index.py`: EDGAR filings index, downloads, HTML → text, period → source map.
- `rel_tables.py`, `extract_2026.py`: release table parser and the 2026-quarter extraction.
- `xbrl.py`: XBRL company-facts helper, matched on period end dates (the fiscal calendar changed in 2019).
- `normalize.py`: basis rules, flat model keys, discrete quarterly cash flow, non-GAAP bridge conversion.
- `check_data.py`: data consistency checks.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
