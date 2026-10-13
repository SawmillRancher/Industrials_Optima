# RBC model build kit

`models/RBC_Model.xlsx` is the RBC Bearings Incorporated (NYSE: RBC) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD build kit:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CL2`, scenario table in `Model!CT:CX`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). Discount dates moved to RBC's ~31-March fiscal year ends; FY2027E (ends 3-Apr-2027) is the base year, so the explicit years are FY2028E–FY2032E and net debt is taken at the FY2027E year end.
  - Charts: segment contribution to sales growth, adjusted EBITDA / operating income, returns.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (fiscal year ends on the Saturday nearest 31 March; FY2027 = 29-Mar-2026 – 3-Apr-2027, 53 weeks)
- **C–I FY2006–FY2012:** annual, as originally reported (FY2006 = the first 10-K after the Aug-2005 IPO).
- **J–CA Q1/13–Q4/26 with FY subtotals:** grouped and collapsed like the template.
- **CB Q1/27 (actual), CC–CE Q2/27E–Q4/27E, CF FY2027E:** Q2 calibrated to the Q2 FY27 outlook; Q3–Q4 carry the same calibration Δs; Q4/27E has 14 weeks.
- **CG–CK FY2028E–FY2032E:** scenario forecast.
- **Right of the forecast** (template column + 6): CL notes, CN–CQ CAGRs (5Y fwd '27–'32, 5Y, 10Y, 20Y), CT–CX scenario table.

## Basis
- **Policy:** as originally reported. Quarters come from the earnings release three-month columns; fiscal years from the 10-K.
- **Restatement not recast:** the FY2022 10-K/A (5-Aug-2022) restated FY2020–FY2022 and their quarters for stock-based compensation that should have been expensed earlier (SG&A: FY2022 +$9.0m, FY2021 −$3.2m, FY2020 +$7.4m). The restated operating income and net income are memo rows with cell comments.
- **Segments:**
  - Roller / Plain / Ball / Other (Other renamed Engineered Products in FY2016 with Sargent) through Q2 FY22: legacy memo rows with a Σ check.
  - Aerospace & Defense / Industrial from the Q3 FY22 release (after Dodge). FY2021 and Q3 FY21–Q2 FY22 come from the re-presented comparatives in the following year's documents. Q1–Q2 FY21 and earlier were never re-presented, so those cells are blank and a "not on the current segment basis" row carries total sales.
  - Segment gross margin (the CODM measure) from the 10-Q / 10-K segment note; Q4 = fiscal year − nine months. Segment operating income is a memo row for FY2022–FY2025, the only years it was presented. Re-presented SG&A and operating income for Q1–Q2 FY22 carry the 10-K/A restatement and are not used.
- **Per-share data:** no stock splits since the IPO. The 5.00% Series A MCPS (Dodge financing, FY2022) paid ~$5.75m a quarter of preferred dividends, deducted to reach net income available to common, until it converted into common stock in Oct-2024. In FY2006, Class B/C/D preferred dividends and participation rights are deducted. In the loss quarter Q3 FY22, GAAP diluted EPS uses basic shares and adjusted EPS uses the company's diluted count.
- **Cash flow:** quarters derived from year to date (Q4 = FY − 9M). Working capital & other operating items = CFO − net income − D&A − stock-based compensation − deferred taxes.

## Model structure (Model tab)
- **Segment build:**
  - Aerospace & Defense and Industrial net external sales: prior-year quarter × (1 + organic growth) × week factor + acquired sales not in the base. The acquired sales are VACCO in Q1/27 ($34.4m, release text) and its ~3 pre-anniversary weeks in Q2/27E, plus PSC Couplings by days consolidated.
  - Segment gross margin = sales × gross margin %.
  - Consolidated gross margin = Σ segments (+ future M&A) = company adjusted gross margin. Checked against the published adjusted gross margin.
  - SG&A % of sales and other, net (M&A-related amortization schedule + other + adjusting items) give operating income.
- **Future M&A lever:** spend ÷ EV/sales (2.5x), 38% gross margin, 12% PP&E / 45% intangibles (15-year life) / goodwill split, mid-year convention.
- **PSC Couplings:** $24.2m, closed 10-Aug-2026, after the Q2 outlook, so it is added on top of the calibration. The allocation is unpublished: 10% PP&E and 40% intangibles are flagged assumptions.
- **Q2 FY27 outlook calibration** (RBC guides one quarter ahead and publishes no full-year guidance):
  - A uniform growth Δ on both segments' Q1 FY27 organic y/y rates solves Q2 sales to $505 / 510 / 515m (Bear / Base / Bull).
  - A uniform segment gross-margin Δ on prior-year quarter + Q1 drift solves Q2 gross margin to 45.5% / 45.625% / 45.75%.
  - SG&A is the guided 16.5–16.75% (Bull = low end).
  - Both Δs carry into Q3–Q4/27E (UBER precedent). FY2027E is an output; base: net sales $2,157m (+15.3%), adjusted EPS $15.47.
- **GAAP P&L from the build:** gross margin − SG&A − other, net = operating income. Interest is a point estimate for Q2–Q4/27E, then calculated on opening balances; tax at 22.5% (Q2–Q4/27E), then 23%.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **Operating income → adjusted operating income:** company items grouped as restructuring & consolidation, transaction / transition costs, inventory purchase accounting, litigation, disposals, FY2006–07 stock-option expense and other. Company labels are in cell comments. The FY2012 and Q1 FY15 releases adjusted nothing, so adjusted = GAAP there.
  2. **Net income → operating income → EBITDA → adjusted EBITDA:** company definitions. EBITDA adds back stock compensation; adjusted EBITDA = adjusted operating income + D&A + stock compensation. Checked against the "adjusted operating income plus D&A plus incentive stock compensation" figure (Q2 FY16–Q2 FY22) and Adjusted EBITDA (Q3 FY22+). The bridge continues to adjusted EBIT (full-cost) and adjusted EBITA (+ M&A amortization).
  3. **Net income → adjusted net income → adjusted EPS:** the definition in force:
     - FY2006–Q1 FY23 (old): items after tax.
     - Q2 FY23+ (current): also adds back M&A-related amortization, stock compensation and deferred-fee amortization, pre-tax, with a tax line.

     The tax effect is derived as published adjusted net income − net income − items. Preferred dividends are deducted. Memo rows hold the old-definition EPS as published and the current definition re-presented for Q1 FY22–Q1 FY23.
- **Other schedules:**
  - Cash flow; buybacks; balance sheet; working capital (FY-end days).
  - PPAs: Dodge (final, FY2023 10-K) and VACCO (final, FY2026 10-K).
  - Debt: term loan $96m repaid in FY2027 ($50m Jul-2026, $46m at the 2-Nov-2026 maturity); $500m 4.375% notes due Oct-2029 refinanced in FY2030E; revolver ($500m, Oct-2030) drawn or repaid to a $75m minimum cash, with a headroom memo.
  - Leverage-target buybacks from FY2028E: net debt / adjusted EBITDA of 1.5x / 1.0x / 0.5x. This is an assumption: RBC has never used its $100m 2019 authorization.
  - Ratios and valuation.
- **DCF basis:**
  - NOPAT on adjusted EBITA (after stock compensation, before M&A amortization) less transaction & restructuring costs, taxed at 23%.
  - D&A excluding M&A amortization added back.
  - UFCF after capex and the M&A lever.
  - No leases in net debt.
  - Market inputs (risk-free 4.25%, ERP 5%, beta 1.05) are assumptions: U.S. Treasury / FRED data are not reachable from the build environment.

## Key forecast assumptions (Base)
- **Segment sales growth FY2028E–32E:** Aerospace & Defense 11% → 7%; Industrial 6% → 4.5% (scenario table; assumptions citing Q1 FY27 organic +16% / +8.4% and FY2023–26 history).
- **Segment gross margins:** Aerospace & Defense 44.0% → 45.5%; Industrial 48.5% → 50.0%. SG&A 16.3% → 16.0% of sales.
- **Other drivers:**
  - D&A excl. M&A amortization 2.8% of sales.
  - M&A amortization per the 10-Q schedule ($81.3m FY2028 … $69.3m FY2032) × 93% M&A share.
  - Stock compensation 1.8% of sales; capex 4.0% → 3.5% of sales.
  - M&A $250m p.a. (assumption); no dividend.
- **Share price $510.00:** provided by the user on 13-Oct-2026 (not an SEC-filed price); update it at `Model!CF` in the valuation block.

## Data corrections
- None. Known data points, documented rather than corrected:
  - The FY2022 10-K/A restatement (memo rows).
  - The ambiguous two-value rows in some reconciliations, where text conversion drops blank cells (e.g. Q2 FY19, Q2 FY15). These are resolved by the choice that closes the published reconciliation; see `extract.py` `block()`.
  - The FY2006 10-K segment table lists the years oldest-first.

## Sources
SEC EDGAR only (CIK 1324948):
- Forms 10-K / 10-Q FY2006–Q1 FY2027, and the FY2022 10-K/A (restatement).
- Form 8-K Item 2.02 earnings releases (Ex. 99.1), Q1 FY2006 – Q1 FY2027.
- 8-Ks:
  - VACCO agreement (20-May-2025) and closing / revolver draw (21-Jul-2025);
  - credit-agreement amendment (30-Oct-2025);
  - PSC Couplings (11-Aug-2026).
- XBRL company facts: cross-checks of sales, operating income, net income, diluted EPS, CFO and total assets (341 checks, 0 differences), and shares issued / treasury shares.

The investor-relations site is blocked from the build environment; its releases are the same documents as filed on EDGAR. Guidance is taken only from the 8-K releases (no call transcripts or other non-EDGAR guidance are used).
- `filings.csv` indexes the filings, and each `data/<period>.json` lists its source URLs.
- `data/_xbrl.json` holds the XBRL subset.
- `manual_items.json` holds the Q2 FY27 outlook, the 53-week calendar, deals (VACCO, PSC, Dodge) and PPAs, the amortization schedule, debt facts, the MCPS, the buyback authorization, the restatement memo and the share price, each with its source.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export RBC_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`.
   3. `python3 check_data.py` (and `python3 xbrl_check.py`) runs 1,387 checks: statement arithmetic, segment sums (current and legacy), segment gross margin and operating income, adjusted operating income / gross margin / EBITDA / EPS bridges vs published, GAAP EPS, cash and balance-sheet tie-outs, and quarters vs years. There are no known exceptions.
3. Build: `python3 build.py --snap --recalc` writes `../RBC_Model.xlsx`. It reruns with the switch on Bull and Bear to fill the snapshot panels, then stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../RBC_Model.xlsx` → 0 error cells, 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../RBC_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../RBC_Model.xlsx --extra WWD Woodward 382.17` → 0 residue hits.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`: EDGAR filings index, downloads, HTML → text.
- `period_index.py`: maps each period to its release, 10-Q / 10-K and the following year's documents.
- `parse.py`: table helpers (numbers, rows, windows, unit detection).
- `extract.py`: per-period extraction (statement of operations, non-GAAP reconciliations, segment data and segment note, balance sheet, cash flow, prior-year comparatives).
- `xbrl.py`: XBRL company-facts helper (fiscal year ending ~31 March).
- `normalize.py`: basis rules, flat model keys, discrete quarterly cash flow.
- `check_data.py`: data consistency checks.
- `xbrl_check.py`: cross-check against XBRL company facts as first filed (341 checks, 0 differences).
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
