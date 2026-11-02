# GHM model build kit

`models/GHM_Model.xlsx` is the Graham Corporation (NYSE: GHM) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD build kit.
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped and collapsed.
- **Scenarios:** Bull / Base / Bear switch in `Model!CK2`, scenario table in `Model!CS:CW`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). Discount dates are moved to Graham's 31-March fiscal year ends.
  - Charts: market contribution to sales growth, Adjusted EBITDA and operating profit, returns.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (fiscal year ends 31 March; 2027 = Apr-2026 – Mar-2027)
- **C–I FY2006–FY2012:** annual, as originally reported.
- **J–CA Q1/13–Q4/26 with FY subtotals:** grouped and collapsed like the template.
- **CB Q1/27 (actual), CC–CE Q2/27E–Q4/27E, CF 2027E:** forecast calibrated to the FY27 outlook.
- **CG–CJ 2028E–2031E:** scenario forecast.
- **Right of the forecast** (template column + 5): CK notes, CM–CP CAGRs (5Y fwd '26–'31, 5Y, 10Y, 20Y), CS–CW scenario table.

## Basis
- **Policy:** as originally reported, from each period's own earnings release.
- **Segments:** one reportable segment throughout.
- **Markets:**
  - Current Defense / Space / Energy & Process basis from FY2020 (introduced with the FY2025 10-K).
  - FY2020 Defense comes from the FY2021 releases' prior-year tables (latest presentation).
  - Energy & Process = net sales − Defense − Space where only the legacy industry split was published (FY2020–FY2024).
  - The legacy split (refining, chemical / petrochemical, power, defense, space, other) is kept in memo rows exactly as published.
- **Acquisitions and disposals:**
  - Energy Steel (Dec-2010), Barber-Nichols (1-Jun-2021), P3 (9-Nov-2023), Xdot (20-Oct-2025) and FlackTek (23-Jan-2026).
  - The commercial nuclear utility business was sold in Q1 FY2020; its held-for-sale cash is a separate cash-flow line in FY2019–20.
- **Per-share data:** restated for the 5-for-4 split (effective 3-Jan-2008) and the 2-for-1 split (effective 6-Oct-2008) by release date.
- **Cash flow:** quarters derived from year to date (Q4 = FY − 9M).

## Model structure (Model tab)
- **Market build:**
  - Defense, Space and Energy & Process sales.
  - Q2–Q4/27E = prior-year quarter × (1 + trailing-four-quarter organic growth + calibration Δ) + the FlackTek y/y increment × an assumed market share (E&P 75%, Defense 15%, Space 10%).
  - 2028E+ = prior year × (1 + scenario lever).
- **Orders and backlog:** orders = sales × book-to-bill (1.0x for Q2–Q4/27E, scenario lever after); backlog = opening + orders − sales. Historical adjustments (cancellations, FX, acquired backlog) close the roll and are nil in the forecast.
- **FlackTek block:** Q4 FY26 and Q1 FY27 sales come from the 10-K / 10-Q. Q2–Q4/27E = (the ~$30m FY27 expectation from the Investor Day 8-K − Q1) ÷ 3. Inorganic until 23-Jan-2027.
- **Future M&A lever:** spend ÷ 1.5x EV/sales; 12% Adjusted EBITDA margin; PP&E 6%, intangibles 50%, rest goodwill; 12-year amortization; mid-year convention.
- **FY27 outlook calibration** (Q2–Q4/27E; guidance of 8-Jun-2026, reaffirmed 6-Aug-2026):
  1. Sales: one uniform growth Δ on the three markets solves FY27 sales to $295m / $290m / $285m (Bull / Base / Bear). Base Δ is −14.1pp, giving Q2–Q4 Defense +15%, Space +3%, E&P −16% (E&P backlog −20% y/y).
  2. SG&A, a guided driver, is applied next: Q2–Q4 SG&A is solved so FY27 SG&A incl. amortization = 16.5% / 17.0% / 17.5% of sales.
  3. Gross margin: a uniform Δ on (prior-year quarter + Q1 drift) solves FY27 Adjusted EBITDA to $40m / $37.5m / $35m. Base Δ is +3.2pp, giving a FY27 gross margin of 24.4% vs 24.5–25.5% guided. The guided mid-points are not mutually consistent, so the gross-margin row is shown for information.
  - Tax: the Q2–Q4 rate is solved so the FY27 ETR = 19% (guided 18–20%).
  - Information rows (not forced): gross margin, excluded items (~$5.5–6.5m), capex ($18–22m), and the Investor Day FY27–29 targets (8–10% organic growth, 14–16% Adjusted EBITDA margin in FY29).
- **GAAP P&L from the build:**
  - gross profit = sales × gross margin; SG&A % of sales; SG&A–amortization = total amortization × its Q1 share;
  - operating profit; net interest on opening balances; other non-operating expense as an input;
  - tax at 19% (FY27) then 20%.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **Net income → EBITDA → Adjusted EBITDA:** the company definition in force each period. EBITDA only in FY2012–14, FY2016 and Q4 FY2020–FY2021; equity-based compensation is added back from Q4 FY2024. Flags are in the definition row.
  2. **Operating profit → adjusted operating profit:** published Q4 FY2018–Q3 FY2020; a model definition elsewhere.
  3. **Net income → adjusted net income → adjusted EPS:**
     - amortization of intangibles is added back from FY2022;
     - the historical tax effect is derived from the published adjusted net income;
     - the forecast tax effect is −23% (statutory) × items;
     - unpublished periods use a model rebuild.
- **Other schedules:**
  - Cash flow, with the FY2019–20 held-for-sale cash line.
  - Buybacks, balance sheet, working capital (FY2026 year-end days; customer deposits as % of backlog).
  - PPAs: Barber-Nichols (final), P3 (final), FlackTek (preliminary).
  - Debt: Wells Fargo $80m revolver to a $15m minimum cash, with a headroom memo.
  - Net-cash-cap buybacks, 2028E+: target net debt / Adjusted EBITDA −0.5x / −1.0x / −1.5x.
  - Ratios and valuation.
- **DCF basis:**
  - NOPAT base = Adjusted EBITA − equity-based compensation − cash acquisition / ERP / restructuring costs, taxed at 20%; depreciation-only add-back.
  - UFCF after capex and bolt-on M&A.
  - Net debt is taken at 31-Mar-2027, so the FY2027E UFCF is set to zero in the PV.
  - Operating leases are not treated as debt.
  - Market inputs are assumptions (risk-free 4.25%, ERP 5%, beta 1.1); Treasury data is not reachable from the build environment.

## Key forecast assumptions (Base)
- **Market growth FY28–FY31:**
  - Defense 9% → 7%;
  - Space 15% → 8%;
  - Energy & Process 4% → 3%;
  - plus M&A of $20m a year (assumption).
- **Book-to-bill:** 1.10x / 1.05x / 1.00x / 1.00x.
- **Margins:** gross margin 25.5% → 27.0%; SG&A 16.0% → 14.7% of sales. Adjusted EBITDA margin reaches 15.0% in FY29 (target 14–16%).
- **Capex and D&A:** capex 6.0% → 4.0% of sales (capacity programme "nearing completion"); depreciation 2.6–2.8% of sales; amortization per the 10-Q schedule ($3.7m a year).
- **Other drivers:** equity-based compensation 0.9% of sales; earn-out fair-value accretion $0.8m / $0.5m / $0.3m.
- **Capital returns:** no dividend (suspended FY2022).
- **Share price:** $95.34, the 8-Jun-2026 tax-withholding price on Form 4s filed 10-Jun-2026. This is the latest share price in an SEC filing; update it to market at `Model!CF` in the valuation block.

## Results (Base, at $95.34)
- **FY27E:** sales $290m; Adjusted EBITDA $37.5m (12.9%); adjusted EPS $1.93 (49x); FCF −$5m after $20m capex.
- **FY31E:** sales $430m; Adjusted EBITDA $72.5m (16.9%); adjusted EPS $3.76.
- **Bull-Base-Bear price targets (FY2031E):** Base $150 at 40x; Bull $233 at 45x; Bear $69 at 30x.
- **DCF:** about $30 a share. The market-implied EV/NOPAT is ~35x vs ~21x from the Mauboussin framework, so the price discounts more growth or returns than the Base case.

## Data corrections and known exceptions
- **Q1 FY2022:** the release statement has no operating-profit line; it is derived (GP − SG&A − amortization), commented.
- **FY2021:** the statement line "Net other interest (income)/expense" includes $0.113m of other income; it is split per the EBITDA reconciliation, commented.
- **FY2019 and Q4 FY2019 – Q1 FY2020:** the cash-flow statement deducts cash held within assets held for sale; carried as a separate line so cash ties.
- **FY2015 / Q4 FY2015:** restructuring is shown net of tax in the adjusted net income table; the tax effect is derived.
- **FY2011–FY2012:** EBITDA tables are in USD millions; the checks use ±0.15.
- **Supplemental exhibits:** the Q1 FY2026 exhibit labels the Q1 FY2026 column "2025". Grid columns are sequenced (a Q1 after a Q4 / YTD column starts the next fiscal year).

## Sources
SEC EDGAR only (CIK 0000716314):
- Forms 10-K / 10-Q FY2006 – Q1 FY2027.
- Form 8-K Item 2.02 earnings releases (Ex. 99.1) and supplemental tables (Ex. 99.2 / 99.3), Q4 FY2006 – Q1 FY2027.
- Investor Day presentation (8-K Item 7.01, Ex. 99.1, 18-Jun-2026).
- PIPE 8-K (15-Apr-2026); FlackTek 8-K (26-Jan-2026); Form 4s (Jun-2026) for the share price.
- XBRL company facts: shares outstanding and cross-checks.

All guidance and targets used are from EDGAR filings; none is unverified. The investor-relations site (ir.grahamcorp.com) is not used; its releases are the same documents as filed on EDGAR.
- `filings.csv` indexes the filings.
- Each `data/<period>.json` lists its source URLs; `data/_releases.json` indexes the releases and `data/_xbrl.json` holds the XBRL subset.
- `manual_items.json` holds the FY27 guidance, Investor Day targets, FlackTek facts and market-share assumption, PPAs, the amortization schedule, debt facts, the buyback authorization, the dividend status, splits and the share price, each with its source.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export GHM_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`.
   3. `python3 check_data.py` runs 1,679 checks: statement arithmetic, EPS, EBITDA / Adjusted EBITDA / adjusted net income / adjusted operating profit bridges vs published, market and region sums, cash and balance-sheet tie-outs, XBRL cross-checks, and quarters vs years. Known exceptions: none.
3. Build: `python3 build.py --snap --recalc` writes `../GHM_Model.xlsx`. It reruns with the switch on Bull and Bear to fill the snapshot panels, then stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../GHM_Model.xlsx` → 0 error cells, 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../GHM_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../GHM_Model.xlsx --extra Woodward WWD 382.17` → 0 residue hits.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`: EDGAR filings index, downloads, HTML → text.
- `parse_release.py`: release parser. It places cells by grid column (colspan-aware) and types tables by content. It resolves statement columns (months, current / prior, value / per share) and grid columns (fiscal year, quarter) across the FY2006–FY2027 formats.
- `extract.py`: per-period extraction (statements, non-GAAP tables with item categories, orders / backlog / market / region grids, revenue-note market table, cash flow, balance sheet, prior-year comparatives, XBRL extras).
- `xbrl.py`: XBRL company-facts helper (31-March fiscal year).
- `normalize.py`: basis rules, split restatement, market basis, discrete quarterly cash flow.
- `check_data.py`: data consistency checks.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
