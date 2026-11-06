# JHX model build kit

`models/JHX_Model.xlsx` is the James Hardie Industries plc (NYSE / ASX: JHX) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link;
  - red italic = definition-flag text.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CK2`, scenario table in `Model!CS:CW`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT); discount dates on 31 March.
  - Charts (net sales growth contribution Siding & Trim vs other segments; Adjusted EBITDA and operating income; ROIC / RONTA / margins).
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored** (`build.py --recalc`), so the workbook reads correctly in any viewer.

## Columns (fiscal year ends 31 March)
- **C–I FY2006–FY2012:** annual, as originally reported (20-F / results packages).
- **J–CA Q1/13–Q4/26 with FY subtotals:** grouped and collapsed like the template (Q4 FY21–FY24 = FY − 9M, flagged in the data).
- **CB–CC Q1/27–Q2/27:** actual (Q1 recast to continuing operations); **CD–CE Q3/27E–Q4/27E, CF 2027E:** forecast, set to the FY27 planning assumptions.
- **CG–CJ 2028E–2031E:** scenario forecast.
- **Right of the forecast** (template column + 5): CK notes, CM–CP CAGRs (5Y forward, 5Y, 10Y, 20Y), CS–CW scenario table.

## Basis
- **Policy:** as originally reported in each period's own results package (US GAAP, USD millions). FY2027 quarters are continuing operations.
- **Recasts and discontinued operations:** Europe (fermacell fibre gypsum + European fibre cement) became discontinued operations in the Q2 FY27 release (5-Nov-2026) after the sale of fermacell to Holcim was announced (20-Aug-2026, €840m ≈ US$980m). Q1 FY27 was reported with Europe as a segment, so the model rebuilds Q1 FY27 as the six-month columns of the Q2 FY27 release less Q2 (income statement, segments, bridge items; `recast_cont` flag, originals under `*_orig`), and FY2027E = Q1 + Q2 + Q3E + Q4E is on the planning-assumption basis. The FY26 comparatives recast in the FY27 releases (continuing operations, ex share-based compensation) are kept as data keys `*_rc` and are not used in the as-reported FY26 columns.
- **Segments as reported per year:** USA / Asia Pacific Fibre Cement + Other + R&D (FY2006–08); USA & Europe / Asia Pacific Fibre Cement + R&D (FY2009–16); North America / International Fiber Cement + Other + R&D (FY2017–18; International = Asia Pacific + Europe, memo rows); North America / Asia Pacific / Europe Building Products (+ Other to FY21) + R&D (FY2019–Q1 FY26); Siding & Trim / Deck, Rail & Accessories / Australia & New Zealand / Europe with R&D allocated to the segments (from Q2 FY26, AZEK consolidated from 1-Jul-2025). The model rows are Siding & Trim (= North America fiber cement history), DR&A, Australia & New Zealand (= Asia Pacific history), Europe (to FY26), plus legacy memo rows (International, Other Businesses, R&D segment).
- **Corporate:** general corporate costs as published are a memo; "Corporate & other (derived)" = operating income − segment EBIT − R&D segment + asbestos adjustments ties the build to reported EBIT in every period. Corporate Adjusted EBITDA = company Adjusted EBITDA − Σ segment Adjusted EBITDA (derived; the published General Corporate line is a memo).
- **Per-share data:** no splits; EPS published in US cents to FY2022 (÷100 in extraction). ADS = 1 ordinary share.
- **Cash flow:** quarters derived from year-to-date (Q4 = FY − 9M). Cash on the cash-flow statement includes restricted cash from FY2019 (flag row and check).

## Model structure (Model tab)
- **Operating build:** segment net sales × segment Adjusted EBITDA margin → − segment D&A − AZEK intangible amortization (by segment share) − other segment items = segment operating income; memo volume (mmsf, to FY2023) and ASP (to FY2021) for North America fiber cement; A$ / € net sales memos.
- **Acquisition block:** AZEK (closed 1-Jul-2025): standalone / pro forma memo rows, inventory step-up, intangible amortization (10-K schedule) and the final PPA table (10-K Note 2) in the schedules section with a check.
- **Europe divestiture block:** discontinued-operations income until closing, sale proceeds, net assets held for sale (30-Sep-2026), gain on sale (closing fiscal year input, default FY2028 = Q1 FY28), held-for-sale balances removed at closing, proceeds net of cash disposed in the cash flow, cash sweep to the term loans.
- **Future M&A lever:** spend ÷ EV/sales, Adjusted EBITDA margin, PP&E / intangibles / goodwill split, amortization (inside D&A, not adjusted out).
- **FY27 calibration:** the company gives Q3 FY27 and FY27 ranges for net sales and Adjusted EBITDA by segment (Siding & Trim, DR&A, total). Q3/27E = Q3 end-point (high / mid / low by scenario); Q4/27E = FY end-point − Q1–Q3. ANZ net sales = total − S&T − DR&A; ANZ Adjusted EBITDA from its margin (prior-year quarter + H1 drift) and corporate = total − segments. Check rows: Q3/27E and FY2027E vs the planning assumptions. Free cash flow (> US$650m) and capex (6–7%) are information / point inputs.
- **GAAP P&L from the build:** operating income = Σ segment operating income + corporate & other − asbestos adjustments − AICF SG&A − restructuring − acquisition / divestiture costs − impairments; gross profit is the implied line (SG&A, R&D % of sales). Interest from the debt schedule on opening balances (+ AICF interest income); GAAP tax rate 34% FY27 (point) then 30% → 26% inputs; adjusted rate 22%.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **Net income → EBITDA → Adjusted EBITDA:** company definition from FY2024 (FY2023 as restated in the FY24 release): + asbestos adjustments, AICF SG&A, restructuring, acquisition / divestiture, step-up, impairments, + share-based compensation from FY27. FY2010–20 the company's "Adjusted EBITDA" was EBIT + D&A (asbestos included; "excluding asbestos" variant FY2017–20) — both are carried as memo rows with their own checks; FY2021–22 model bridge.
  2. **EBIT → Adjusted EBIT:** company definition FY2006–FY2025 ("EBIT excluding asbestos …" → "Adjusted EBIT"); not published from FY2026 (model continuation).
  3. **Net income → adjusted net income → adjusted diluted EPS:** "net operating profit excluding asbestos" FY2006–08 (after-tax items; the tax row is the balance), "Adjusted net operating profit" FY2009–21, "Adjusted net income" FY2022+, + AZEK step-up / pre-close financing / intangible amortization FY2026, + share-based compensation FY2027. The tax row is derived (published − GAAP − pre-tax items). FY2024 and Q4 FY24 were published as headlines only (the tax row carries the whole adjustment).
- **Asbestos / AICF schedule:** liability roll-forward (− claims paid + P&L adjustments), AICF restricted cash & investments (+ AFFA contribution + interest − claims), insurance receivable, net unfunded liability (debt-like in the EV bridge) and the related DTA. Contribution FY27 = A$128.2m (≈ US$93m); 2028E+ = 35% × prior-year free cash flow (model).
- **Other schedules:** cash flow (claims paid as its own operating line); buybacks (US$250m authorization, H2 FY27 by scenario; 2028E+ leverage plug capped at cash generated); balance sheet; working capital (DSO / DIO / DPO / other current liabilities % at FY26 year-end levels); debt (senior notes 2031 / 2032 refinanced at maturity, Term Loan A-1 refinanced with notes in FY2029, A-2 amortization with the Oct-2030 maturity assumed extended, prepayments from surplus cash, US$1.0bn revolver to a US$350m minimum cash); leverage-target buybacks (Bull 2.0x / Base 1.75x / Bear 1.5x); DuPont ROIC, RONTA, ROE, leverage incl. the asbestos liability; valuation.
- **DCF basis:** NOPAT on Adjusted EBITA after share-based compensation (before AZEK intangible amortization) less restructuring and acquisition / divestiture costs; depreciation & other amortization added back; capex + bolt-ons + Europe proceeds (closing year) in row 22; net debt + net unfunded asbestos liability in the equity bridge; opening IC = FY2026 book IC; USD risk-free rate.

## Key forecast assumptions (Base)
- FY27: Q3 and FY planning-assumption mid-points (net sales US$5,061.5m, Adjusted EBITDA US$1,490m); interest, net US$230m; GAAP tax 34%, adjusted 21.8%; AZEK amortization US$310m; capex 6.5% of sales; claims paid US$130m; AFFA contribution US$93m; Europe discontinued income US$10m a quarter; no buybacks (Bull: US$100m) — all per the Q2 FY27 release or H1 actuals; items marked "assumption" in the notes column are the analyst's.
- 2028E–2031E: Siding & Trim +6% / +6% / +5.5% / +5%, DR&A +8% / +7% / +6% / +6%, ANZ +4%; Adjusted EBITDA margins S&T 33.5% → 35%, DR&A 30.5% → 33%, ANZ 33%; corporate −2.7% of sales; bolt-on M&A US$100m a year at 3.0x sales; capex 6.5% → 6%; GAAP tax 30% → 26%; Europe closes in Q1 FY28 with US$980m proceeds (gain assumed tax-free, company expectation — unverified).

## Data corrections and documented exceptions
- FY2008 adjusted net income: `manual_items.json` carries 169.7 ("net operating profit excluding asbestos, asset impairments and tax adjustments", Q4 FY08 Management's Analysis).
- FY2024 General Corporate (segment note includes asbestos and the greenfield impairment): the model adds both back so the series stays on the release basis (flag `corp_ebit_fs_plus_asb`). AICF SG&A FY2024 (1.6) = published Adjusted EBIT − EBIT − asbestos − impairment; from FY2025 = bridge "asbestos related expenses and adjustments" − statement asbestos adjustments.
- `check_data.py` exceptions (all explained in its `EXCEPT` table): Σ Q1–Q3 FY13 vs FY13 (NZ product liability reclassification in the Q4 FY13 package); Σ FY18 quarters vs FY18 (Fermacell acquisition costs excluded only in the Q4 FY18 package); FY13 restated D&A rounding (0.6); FY14 APAC EBIT quarter rounding (0.3); Q2 FY27 cash-flow cash vs balance sheet (US$2.0m of cash inside the held-for-sale group); FY13 XBRL tax sign; Q1 FY27 bridge items derived from six-month columns (0.9 rounding).
- Workbook check tolerances: ±0.3 on the bridges (±0.6 on the Adjusted EBITDA check for the derived Q1 FY27 and the FY2010–20 EBITDA memo), ±0.5 on published free cash flow (company definition: CFO − capex + PP&E sale proceeds).

## Sources
SEC EDGAR only (CIK 0001159152, James Hardie Industries N.V. → SE → plc):
- Forms 20-F FY2006–FY2025; Form 10-K FY2026 (19-May-2026); Forms 10-Q Q1 and Q2 FY27 (6-Aug-2026, 5-Nov-2026).
- Form 6-K results packages Q1 FY07 – Q3 FY26 (Management's Analysis of Results, media release / earnings release, financial-statement exhibits); Form 8-K Ex. 99.1 earnings releases from Q4 FY26.
- AZEK: Form F-4 / 424B3 (May-2026 merger documents), FY2026 10-K Note 2; Europe: 8-K of 20-Aug-2026 and the Q2 FY27 10-Q Note 3; debt: 8-K of 26-Jun-2026 (2028 notes redemption), 10-Q Note 8.
- XBRL company facts for cross-checks (20-F FY2011+, 10-K / 10-Q) and for D&A / SBC / deferred tax / shares outstanding where the exhibits omit them (`data/_xbrl.json`).

The investor-relations site (ir.jameshardie.com) and the ASX are blocked from the build environment; their releases are the same documents as filed on EDGAR. `filings.csv` indexes the filings, and each `data/<period>.json` lists its source URLs. `manual_items.json` holds the FY2006–08 old-format items, FY27 planning assumptions, the AZEK PPA and pro forma facts, the amortization schedule, debt terms, the Europe divestiture facts, AICF facts and the share price.

The share price (US$30.45; Form 4 open-market sale of 25-Aug-2026, filed 27-Aug-2026 — the latest EDGAR-filed price) is an input at `Model!CF` in the valuation block; update it to market.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export JHX_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py && python3 normalize.py`.
   3. `python3 check_data.py` runs the statement-arithmetic, segment, bridge, quarter-sum, cash, balance-sheet and XBRL checks (1,644 pass; the 12 documented exceptions above).
3. Build: `python3 build.py --snap --recalc` writes `../JHX_Model.xlsx` from `data/_normalized.json`, reruns with the switch on Bull and Bear to fill the snapshot panels, and stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../JHX_Model.xlsx` → 0 error cells and 0 non-zero check rows.
   - `python3 ../tools/cyc.py ../JHX_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../JHX_Model.xlsx --extra STE 211.07` → 0 residue hits (the kit was adapted from `ste_build`).
   - Intentional: Charts `#N/A` for FY2006 ratios (no prior-year balance sheet) and the FY2006 growth bars at 0.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (`V0`), compute engine, scenario table, definition flags, column layout, snapshots.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts, re-injects the template chart XML and restores comment authors after recalculation.
- `h2t.py`, `make_index.py`, `fetch.py`, `parse_release.py`, `extract.py`: EDGAR HTML → text, filings index, downloads, release parser, per-period extraction (`EXTRACTION_SCHEMA.md` describes the keys).
- `xbrl.py`: XBRL company-facts helper.
- `normalize.py`: basis rules, flat model keys, discrete quarterly cash flow, Q4 derivations, the Q1 FY27 recast, bridge-item categories (`data/_normalized.json`).
- `check_data.py`: data consistency checks; `review.py`: per-period coverage summary.
