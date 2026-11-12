# TDG model build kit

`models/TDG_Model.xlsx` is the TransDigm Group Incorporated (NYSE: TDG) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD build kit (same 30-September fiscal year):
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CK2`, scenario table in `Model!CS:CW`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). Discount dates moved to TransDigm's 30-September fiscal year ends. FY2026A (ended 30-Sep-2026, about six weeks before the valuation date) is the base year, so the explicit years are FY2027E–FY2031E and net debt is taken at 30-Sep-2026.
  - Charts: segment contribution to sales growth, EBITDA As Defined and income from operations, returns.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (fiscal year ends 30 September; 2026 = Oct-2025 – Sep-2026)
- **C–I FY2006–FY2012:** annual (IPO in March 2006, so FY2006 is the first year in EDGAR filings).
- **J–CA Q1/13–Q4/26 with FY subtotals:** grouped and collapsed like the template. FY2026 (column CA) is actual: the Q4 release and the FY2026 10-K were filed on 10-Nov-2026.
- **CB–CE Q1/27E–Q4/27E, CF 2027E:** forecast, calibrated to the FY27 guidance (Q4 FY26 release, 10-Nov-2026).
- **CG–CJ 2028E–2031E:** scenario forecast.
- **Right of the forecast** (template column + 5): CK notes, CM–CP CAGRs (5Y forward '26–'31, 5Y, 10Y, 20Y), CS–CW scenario table.

## Basis
- **Policy:** hybrid.
  - Income statement, EBITDA / EBITDA As Defined and adjusted-net-income bridges are as originally reported in each period's own earnings release.
  - Balance sheet and cash flow are as originally reported in the 10-Q / 10-K.
  - Segments and end markets come from the latest filing that presents the period: the following fiscal year's 10-Q / 10-K comparative, or for FY2011 the FY2013 10-K.
  - A derived Group row ("not on the segment basis") holds the difference to consolidated net sales / EBITDA As Defined as first reported. It is the whole of FY2006–10 (one reportable segment) and small amounts in recast periods.
- **Recasts and discontinued operations** (cell comments):
  - FY2011: the fastener business and AQS (acquired with McKechnie) were sold and shown as discontinued operations.
  - FY2017: SCHROTH became discontinued operations in the FY2017 10-K. Q1–Q3 FY2017 as first reported include it, so revenue Σ quarters exceeds the year by $14.5m.
  - FY2018: a business moved from Power & Control to Non-aviation. FY2017 segment data use the FY2018 comparatives.
  - FY2019: Esterline closed 14-Mar-2019 and was a separate fourth segment in the Q2–Q3 FY2019 10-Qs. The FY2020 comparatives (used here) allocate it to Power & Control / Airframe and the end markets. Businesses sold in FY2019–20 (e.g. Souriau-Sunbank, Dec-2019) are discontinued operations, so the 10-K year is $165.7m below Σ quarters as first reported.
  - FY2016: ASU 2016-09 was early-adopted retroactive to 1-Oct-2015. Q1–Q3 FY2016 tax as first reported is pre-adoption ($37.6m difference).
- **Segments:** Power & Control, Airframe and Non-aviation from Q3 FY2013, with FY2011–12 and Q1–Q2 FY2013 from comparatives. Net sales to external customers by end market (commercial OEM, commercial aftermarket, defense, per segment) start with the FY2019 10-K, which carries FY2017–18 annual comparatives, and quarterly from FY2018 via the FY2019 10-Q comparatives. FY2025+ labels read "commercial and non-aerospace OEM / aftermarket".
- **Per-share data:** no stock splits since the IPO. EPS uses the two-class method from FY2010 (vested options are participating securities; dividend-equivalent payments reduce income to common).
  - Adjusted EPS uses the company's adjusted share basis, which includes the participating options in loss-to-common quarters (Q1 FY2021).
  - Shares are published to 0.1m from FY2020, so EPS checks use ±0.06 from FY2020 and ±0.01 before.
- **Cash flow:** quarters derived from year to date (Q4 = FY − 9M). Cash includes restricted cash from FY2019: note-redemption escrow at Q2 FY2019, Q2 FY2023 and Q2 FY2024, shown as its own balance-sheet line.

## Model structure (Model tab)
- **Segment build:**
  - Power & Control and Airframe net sales = Σ commercial OEM, commercial aftermarket and defense. Non-aviation is one line.
  - Segment EBITDA As Defined = sales × segment margin; less unallocated corporate = EBITDA As Defined (company definition). History falls back to segment sales where end markets are unpublished, and to consolidated sales before FY2011.
  - Organic / acquisition growth uses the company's organic-sales table (from FY2012), with a check against reported growth. Q4 FY2017 / FY2019 are not derived because their 10-K tables are on the discontinued-operations basis.
- **FY2027E inorganic sales** (Power & Control; assumption from EDGAR revenue disclosures):
  - P&I (closed 28-Sep-2026; ~$390m calendar-2026 revenue): ~$97.5m a quarter.
  - JPE / VSA (closed 7-Apr-2026; ~$280m calendar-2025 revenue): ~$75m in each of Q1–Q2/27E.
  - FY2026 bolt-ons: $25m tapering to $10m a quarter.
  - These are allocated 15% / 65% / 20% to commercial OEM / aftermarket / defense.
- **Future M&A lever:**
  - FY2027E: the Extant asset purchase (~$240m, 8-K 21-Sep-2026). Revenue is not disclosed, so it is modelled from FY2028E.
  - 2028E+: spend ÷ EV/sales (3.5x); 40% EBITDA As Defined margin; 5% PP&E, 35% amortizable intangibles (20 years), rest goodwill.
- **FY27 guidance calibration (all four quarters estimated):**
  - Sales: each end-market line = prior-year quarter × (1 + guided market growth + one uniform Δ) + inorganic sales. Δ is solved in closed form so FY27 net sales = $12,150m / $12,050m / $11,950m by scenario. Market-growth ranges are read numerically: commercial OEM 12% / 10% / 8%; commercial aftermarket and defense 9% / 8% / 7%. Base Δ = −0.05 pp.
  - Margins: segment margin = prior-year quarter + one uniform Δ, solved so FY27 EBITDA As Defined = $6,345m / $6,270m / $6,195m. Base Δ = −0.68 pp, which absorbs the acquisition dilution.
  - Point estimates come from the guidance-midpoint reconciliation (Table 6): D&A $525m (of which intangible amortization $294m per the 10-K schedule), interest $2,255m, tax 23.1%, acquisition costs $42m, stock compensation $225m, other $16m. Each is spread ÷ 4.
  - Information rows: model net income − guidance = −$0.1m. Adjusted EPS is +$0.52 and GAAP EPS +$0.42 above guidance because the model includes $2.0bn of FY27 buybacks; guidance holds 56.7m shares.
- **GAAP P&L from the build:** EBITDA = EBITDA As Defined − adjusting items; − D&A = EBIT; − interest = pre-tax income. Income from operations = EBIT + refinancing costs + other expense. Gross profit is implied (S&A % of sales).
  - FY27E quarters: two-class shares = Q4/26 56.7m − FY27 buybacks + option exercises, mid-quarter weighted. Q1/27E includes the $54m of dividend-equivalent payments accrued at 30-Sep-2026.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **Net income → EBITDA → EBITDA As Defined:** items as published, grouped into acquisition & integration (incl. inventory step-up), non-cash stock & deferred compensation, refinancing, COVID-19 / 737 MAX restructuring (FY2020–22), gain on sale of businesses, other, and FY2011 discontinued-operations EBITDA. Company labels are in cell comments. Definition flags mark each change in the column where it takes effect.
  2. **Income from continuing operations → adjusted net income → adjusted EPS:** + gross adjustments to EBITDA + purchase-accounting backlog amortization + tax adjustment (as published; forecast at the effective rate). A start-line difference row covers Q1–Q4 FY2020, which start from income attributable to TD Group. The model adds an adjusted EBIT, full-cost (EBITDA As Defined − all D&A) for NOPAT and ROIC.
- **Other schedules:**
  - Cash flow, buybacks, balance sheet and working capital (FY2026 year-end days on pro forma sales incl. a full year of P&I).
  - FY2026 PPAs: Simmonds Q1, JPE / VSA Q3, P&I Q4, other bolt-ons in the FY2026 column. Goodwill and intangibles are from 10-K Note 2; other net assets are derived.
  - Debt at carrying value: maturities refinanced with new notes (assumption), term-loan amortization ~$130m p.a., non-cash interest accretes. Incremental borrowings keep a $1.5bn minimum cash balance, with a memo against the $865m revolver availability.
  - Leverage-targeted capital return from 2028E: net debt / EBITDA As Defined 6.25x / 5.75x / 5.0x, split 50 / 50 between special dividends and buybacks. The participating-option share of special dividends reduces GAAP EPS.
  - Ratios and valuation.
- **DCF basis:** NOPAT on adjusted EBIT (full-cost) less stock compensation and acquisition / integration costs, with all D&A added back. UFCF is after capex and M&A (Extant FY2027E, lever 2028E–31E). Net debt and NCI (incl. redeemable) are at 30-Sep-2026. Market inputs are assumptions: US Treasury data is not reachable from the build environment. Risk-free 4.25%, ERP 5%, beta 1.10, cost of debt 6.75% (2035 notes), D/V 32%, terminal growth 3.5%.

## Key forecast assumptions (Base)
- **End-market growth 2028E–31E:** commercial OEM 9% → 6%; commercial aftermarket 7% → 6%; defense 6% → 5%; Non-aviation 3% (scenario table; assumptions citing FY2026 trends and the FY27 guide).
- **Segment margins:** Power & Control 54.0% → 55.3%; Airframe 55.0% → 56.3%; Non-aviation 44%; unallocated corporate 1.05% of sales.
- **Other drivers:**
  - Capex 2.5% of sales; depreciation & other amortization 1.9%; intangible amortization per the 10-K schedule ($271m FY28 … $253m FY31) + future M&A.
  - Stock compensation 1.9% of sales; tax 23%.
  - M&A $1.5bn p.a. (assumption); FY27E buybacks $2.0bn (input).
- **Share price $1,208.04:** the exercise price of stock options granted on 3-Nov-2026 at market (Forms 4 filed 5-Nov-2026). This is the latest share price in an SEC filing; the cross-check is the $1,130.02 average repurchase price for 23-Aug to 30-Sep-2026 (10-K Item 5). Update it at `Model!CA` in the valuation block.

## Data corrections
- **FY2006 EBITDA As Defined reconciliation (8-K 17-Nov-2006):** the row "Non-Recurring IPO Costs" prints three cells for four columns. The fifty-two-week Gross Adjustments ($60,159k) proves the $2,650k belongs to FY2006, so `extract.py` right-aligns short rows in that table (`manual_items.json`).
- **Documented check exceptions** (`check_data.py`, 18; none forced): the discontinued-operations quarters above (FY2017, FY2019), FY2016 ASU 2016-09 tax, the FY2022 relabelling of stock and deferred compensation in the year-end release, and the mixed-basis Q4 organic tables (FY2017, FY2019).

## Sources
SEC EDGAR only (TransDigm Group Incorporated, CIK 1260221):
- Forms 10-K / 10-Q FY2006–FY2026.
- Form 8-K Item 2.02 earnings releases (Ex. 99.1), Q2 FY2006 – Q4 FY2026.
- Deal and financing 8-Ks: Simmonds (Oct-2025), Stellant (Dec-2025 / withdrawn Jul-2026), JPE / VSA (Jan / Apr-2026), P&I (Jul / Sep-2026), Extant asset purchase (Sep-2026), 6.125% 2034 notes and Tranche N (Feb / Apr-2026), 2035 secured notes and the 2028 notes tender (Sep-2026).
- Forms 4 (5-Nov-2026) for the share price.
- XBRL company facts for cross-checks (revenue, total assets; as first filed).

The investor-relations site (transdigm.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR. No guidance or data from outside EDGAR is used, so nothing is marked unverified. The numeric reading of the narrative market-growth ranges is labelled an assumption.
- `filings.csv` indexes the filings.
- Each `data/<period>.json` lists its source URLs. `data/_releases.json` and `data/_filings.json` index the documents used per period, and `data/_xbrl.json` holds the XBRL subset.
- `manual_items.json` holds the FY27 guidance, deals and PPAs, the amortization schedule, debt facts and maturities, buyback and dividend history, the share price and the FY2006 row correction.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export TDG_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`.
   3. `python3 check_data.py` runs 1,538 checks: statement arithmetic, EBITDA / EBITDA As Defined / adjusted-net-income bridges vs published, two-class EPS, segment and end-market sums, organic + acquisition sales, quarters vs years, cash and balance-sheet tie-outs, and XBRL cross-checks. It reports 18 documented exceptions and 0 issues, and lists the segment basis differences as information.
3. Build: `python3 build.py --snap --recalc` writes `../TDG_Model.xlsx`. It reruns with the switch on Bull and Bear to fill the snapshot panels, then stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`). A rebuild from the committed data alone reproduces the workbook cell for cell.
4. Validate:
   - `python3 ../tools/inspect_model.py ../TDG_Model.xlsx` → 0 error cells, 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../TDG_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../TDG_Model.xlsx --extra Woodward WWD 382.17 STERIS` → 0 residue hits.
   - Intentional: Charts show `#N/A` returns only where a year has no balance sheet (none from FY2012).

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`: EDGAR filings index, downloads, HTML → text.
- `tables.py`, `parse_filing.py`: HTML table reader; table typing and column resolution for releases, 10-Qs and 10-Ks (13- / 26- / 39-week and fiscal-year columns, thousands vs millions, ASU 2023-07 segment tables).
- `extract.py`: per-period extraction (income statement, EBITDA and adjusted-net-income reconciliations, segments, end markets, organic sales, cash flow, balance sheet, prior-year comparatives).
- `xbrl.py`: XBRL company-facts helper (30-September fiscal year).
- `normalize.py`: basis rules, flat model keys, Q4 derivations, discrete quarterly cash flow.
- `check_data.py`: data consistency checks.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
