# UNP model build kit

`models/UNP_Model.xlsx` is the Union Pacific Corporation (NYSE: UNP) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD / STE build kits (framework) and the ODFL / SAIA kits (operating-ratio cost build):
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link;
  - red = definition flags.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CF2`, scenario table in `Model!CN:CR`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). 2026E UFCF is excluded (net debt is taken at YE2026E); the Norfolk Southern stock consideration is deducted in the equity bridge at its 2027E present value.
  - Charts: carload / ARPC growth, adjusted EBITDA and operating income, returns (2006–2025).
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (calendar fiscal year; no shift vs the template)
- **C–I FY2006–FY2012:** annual, as originally reported (2006–07 expense lines re-presented per the FY2008 10-K).
- **J–BV Q1/13–Q4/25 with FY subtotals; BW–BY Q1/26–Q3/26:** grouped and collapsed like the template.
- **BZ Q4/26E, CA 2026E:** forecast, calibrated to the FY26 outlook (Q3-26 release, 22-Oct-2026).
- **CB–CE 2027E–2030E:** scenario forecast (Norfolk Southern consolidated from the assumed 1-Jul-2027 closing).
- **Right of the forecast:** CF notes, CH–CK CAGRs (5Y fwd '25–'30, 5Y, 10Y, 19Y), CN–CR scenario table.

## Basis
- **Policy:** as originally reported, from each period's own earnings release (84 releases, Q4-05 to Q3-26). Exceptions, each commented in the workbook:
  - FY2006–07 revenue split and expense lines: FY2008 Form 10-K re-presentation (the releases used "Operating Revenues", "commodity revenue" and six legacy expense lines; totals unchanged; legacy lines kept as memo).
  - 2019 business groups: Bulk / Industrial / Premium and the ten commodity lines come from the 2020 releases' prior-year comparatives (the 2019 releases reported Agricultural Products / Energy / Industrial / Premium).
- **Business-group structures:** six groups 2006–2017 (Agricultural, Automotive, Chemicals, Energy / Coal, Industrial Products, Intermodal); four groups 2018–2019; three groups with commodity detail from 2020. Legacy structures are memo rows with Σ checks; a definition-flag row marks the changes.
- **Adjusted measures:** company "Financial Performance" tables, published only when items affecting comparability exist: Q4-17 / FY17 (Tax Cuts and Jobs Act), Q4-20 / FY20 (Brazos Yard impairment), Q3-22 / FY22 (labor accrual; Q4-22 derived), 2024 (first published retroactively in the 2025 releases), Q2-25 onward (crew staffing agreement, deferred tax adjustment, acquisition-related expense, industrial park land sales). All other periods: adjusted = GAAP, flagged.
- **Per-share data:** 2-for-1 split of 27-May-2014 applied to shares, EPS and DPS from documents filed before 9-Jun-2014.
- **Cash flow:** quarters derived from year to date (Q4 = FY − 9M). "Other – net" = cash from operations − net income − depreciation − deferred taxes. Restricted cash is in the cash-flow balance from 2018 (memo reconciles to BS cash).
- **Balance sheet:** Union Pacific's condensed presentation (cash, short-term investments, other current assets, investments, properties, other assets; debt within / after one year, other current liabilities, deferred taxes, other long-term liabilities). Operating lease assets / liabilities (shown separately 2019–25) are folded into other assets / other long-term liabilities.

## Model structure (Model tab)
- **Freight build:** revenue carloads × average revenue per car (ARPC, incl. fuel surcharge) for Bulk, Industrial and Premium → freight revenues; + other revenues. Q4/26E: prior-year quarter × (1 + 9M-26 y/y) for carloads and ARPC. 2027E+: scenario levers (carloads and ARPC per group, other revenues). Checks: carloads × ARPC vs reported group revenues (±0.3% rounding), Σ groups vs freight revenues, Σ commodities vs groups, build vs consolidated revenues. Memo: fuel surcharge revenues (10-K / 10-Q MD&A) and freight revenues ex fuel surcharge.
- **Operating statistics & cost build:** gross ton-miles = carloads × GTMs per carload; employees = GTMs ÷ GTMs per employee (PROD lever); compensation = employees × compensation per employee (wage input); fuel = gallons (GTMs × consumption rate) × price per gallon (point input) × the reported-to-locomotive-fuel ratio; purchased services & materials, rents and other as % of revenues (inputs + COST lever); depreciation growth input. Output: standalone adjusted operating ratio and reported OR, checked against the published OR (±0.05pt).
- **Norfolk Southern block (toggle, inputs in the 2027E column):** closing date 1-Jul-2027 (Q3-26 10-Q: "second half of 2027"); NSC standalone (2024–25 as reported; 2026E = 9M actual + Q4; growth and adjusted-OR inputs); consideration = NSC shares × ($88.82 + 1.0 UNP share at the modelled closing price); funding 75% new debt at 5% (pro forma assumed 100% at 5%) and 25% accumulated cash / short-term investments; preliminary PPA per the 424B3 (book values; debt fair-value −$1,348m; retention accrual; DTL at 23%; no property step-up, with a step-up input); goodwill residual with a check row; synergies $2.0bn net run-rate (Bull $2.75bn gross, Bear $1.5bn) phased 25 / 60 / 100%; $170m operating cost to achieve; $2.0bn capex to achieve; contribution rows (revenues, opex ex-D&A, depreciation, interest incl. debt-discount accretion and fee amortisation, shares, NI, EPS accretion memo); pro forma full-year EBITDA memo for leverage.
- **FY26 outlook calibration (Q4/26E):** the only numeric anchor is "reported EPS growth of high-single digit" (7 / 8 / 9% Bear / Base / Bull on FY2025 $11.98). Required Q4 operating income is back-solved through tax, interest and other income; one proportional shift on the variable cost lines (compensation per employee, PS&M, rents, other) hits it in closed form. Fuel (gallons × $4.21), depreciation, interest, other income, tax rate and acquisition costs are point estimates. Check: FY26 EPS vs end-point = 0. Information rows: OR change vs 2025, capital plan $3.5bn.
- **GAAP P&L from the build:** expense lines = cost build + the NSC contribution allocated by the pro forma expense mix; other expenses carry the acquisition-related costs; interest on opening notes / CP plus the deal block (no circularity); tax rate input.
- **GAAP → adjusted bridges** (checks vs published in every published period):
  1. **Operating income → adjusted operating income / adjusted OR** (company items: acquisition-related expense, Brazos Yard impairment, asset-sale gains, other items).
  2. **Net income → EBITDA → adjusted EBITDA** (model: adjusted operating income + depreciation) and a rebuild of the company's covenant-basis "adjusted EBITDA" (EBITDA − other income + operating-lease interest, TTM) checked against the published figures from 2019.
  3. **Net income → adjusted net income → adjusted EPS** (items in OI, items in other income, company tax column incl. discrete tax items).
- **Other schedules:** cash flow (company FCF definition = CFO − CFI − dividends, checked; model FCF = CFO − capex); buybacks (paused; 2027E+ leverage plug); balance sheet with NSC closing entries; working capital (other current assets / liabilities % of revenues); debt (10-K maturities refinanced, acquisition debt, NSC debt at fair value accreting, CP / revolver to a $1.0bn minimum cash with a $2.0bn facility headroom memo); leverage-targeted buybacks (net debt / adjusted EBITDA 2.7 / 2.5 / 2.3x); DuPont ROIC, RONTA, ROE, leverage (model and company-published); valuation.
- **DCF basis:** NOPAT on adjusted operating income less acquisition-related costs and costs to achieve synergies; depreciation added back; capex + NSC cash consideration in 2027E; ΔWC from "other – net"; 2026E weight 0; PV of the NSC stock consideration deducted in the equity bridge; market inputs are assumptions (rate sources not reachable).

## Key forecast assumptions (Base)
- **Carloads 2027E–30E:** Bulk +1.0% → +0.5%; Industrial +2.0% → +1.5%; Premium +3.0% → +2.0%. **ARPC:** Bulk +2.0–2.5%; Industrial +3.0%; Premium +1.5–2.0%. Other revenues +4% → +3%.
- **Costs:** GTMs per employee +2.0% → +1.5%; compensation per employee +3.5%; fuel $3.59/gal (9M-26 average) and consumption rate −1% a year; PS&M 10.7%, rents 3.7%, other 5.1% of revenues (FY2025); depreciation +3.5%.
- **Norfolk Southern:** revenue +3%; adjusted OR 65.5% → 64.0%; depreciation 11.3% of revenues; capex 19% of revenues; debt $16.6bn at 4.7%; 224.6m shares.
- **Capital:** capex 13.5% of standalone revenues; DPS +3%; tax 23.5%; deferred taxes 10% of tax expense; notes refinanced at maturity (4.2% → 4.5% on opening notes); minimum cash $1.0bn.
- **Share price $300.62:** Form 4 filed 12-Nov-2026 (dividend-reinvestment acquisition at $300.62 on 10-Nov-2026), the latest share price in an SEC filing; update to market at `Model!CA` in the valuation block.

## Calibration outcome and known tensions
- Q4/26E needs a −9.5% shift on the variable cost lines to reach FY26 reported EPS of $12.94 (+8%): the fuel point estimate ($4.21, +64% y/y) is carried in full while ARPC carries only the 9M-26 y/y trend (+7–8%), so the Q4 fuel-surcharge catch-up is understated and carloads use the 9M trend (+2.6%) rather than Q3's +6%. The resulting Q4/26E OR of 59.3% is in line with Q3-26 (59.1%).
- The deal-year leverage (3.2x) and the 2027E EPS dilution (−4%) follow the merger terms at the current UNP share price; the pro forma used $216.05.

## Data corrections
- None. Known exceptions (documented, not corrected): FY2017 gross ton-miles as published (898,746) differ from Σ quarters as first reported (901,144), a company restatement; full-year 2025 land-sale and acquisition-cost adjustments exceed the quarterly items by $16m / $1m (not attributed to quarters by the company); XBRL Q4-09 / FY2009 operating income differs from the release by $3m (later restatement; the release figures are kept).

## Sources
SEC EDGAR only (CIK 0000100885):
- Forms 10-K FY2005–FY2025 and 10-Q Q1-06–Q3-26.
- Form 8-K Item 2.02 earnings releases (Ex. 99.1), Q4-2005 – Q3-2026 (84 releases; the 2022–24 exhibits are named `ex_<n>.htm`).
- Merger: 8-K 29-Jul-2025 (Ex. 2.1 merger agreement), Form 424B3 joint proxy statement / prospectus (1-Oct-2025; pro forma Notes 4–7, management assumed synergies), 8-Ks of 17-Nov-2025 (shareholder approvals) and 19-Dec-2025 (STB application), Q3-26 10-Q Note 18 (timing, funding).
- Norfolk Southern (CIK 702165): Forms 10-K FY2023–25, 10-Q Q1-24–Q3-26 and 8-K releases (`data/nsc_standalone.json`).
- XBRL company facts (share-based compensation, shares outstanding, cross-checks of revenues, operating income, net income, EPS, total assets, cash).
- Form 4 filed 12-Nov-2026 (share price).

The investor-relations site (up.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR. `filings.csv` indexes the filings, and each `data/<period>.json` lists its source URLs. `manual_items.json` holds the guidance history, the company adjusting items per period, the 2006–07 re-presentation, debt maturities, leases, pension, share data, the Norfolk Southern terms / pro forma / synergies / balance sheet and the share price, each with its source. The Investor Day 3-year EPS CAGR target is not on EDGAR and is marked unverified.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export UNP_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py && python3 xbrl.py`.
   3. `python3 check_data.py` runs 2,254 checks (statement arithmetic, group sums and carloads × ARPC, adjusted bridges vs published, EPS, cash and balance-sheet tie-outs, quarters vs years, XBRL). Known exception: the FY2017 GTM restatement.
3. Build: `python3 build.py --snap --recalc` writes `../UNP_Model.xlsx`, reruns with the switch on Bull and Bear to fill the snapshot panels, and stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../UNP_Model.xlsx` → 0 error cells, 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../UNP_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../UNP_Model.xlsx --allow "Model!CF2" --extra Woodward WWD 382.17` → 0 hits (`Model!CF2` is UNP's own switch cell: the layout has no column shift).

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification (freight build, cost build, NSC block, calibration, statements, bridges; cash flow, balance sheet, schedules, ratios, valuation).
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`: EDGAR filings index, downloads, HTML → text.
- `parse_release.py`: release parser for every format since 2006 (income statement, freight statistics, balance sheet, cash flow, operating statistics, "Financial Performance" tables in both orientations).
- `extract.py`: per-period extraction, plus 10-K / 10-Q fuel surcharge revenues.
- `xbrl.py`: XBRL company-facts helper (`data/_xbrl.json` subset).
- `normalize.py`: basis rules, flat model keys, split adjustment, discrete quarterly cash flow, company adjusting items.
- `check_data.py`: data consistency checks.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
- `data/nsc_standalone.json`: Norfolk Southern standalone data (extraction brief in the file's `source_note`).
