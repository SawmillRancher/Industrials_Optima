# BA model build kit

`models/BA_Model.xlsx` is The Boeing Company (NYSE: BA) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD build kit:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CG2`, scenario table in `Model!CO:CS`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). 2026E (Q4 in progress at the 10-Oct-2026 valuation date) is the base year, so the explicit years are 2027E–2031E and net debt is taken at 31-Dec-2026.
  - Charts: commercial deliveries vs revenue per delivery, adjusted EBITDA / earnings from operations, returns.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (fiscal year ends 31 December)
- **C–I FY2006–FY2012:** annual, as originally reported.
- **J–BV Q1/13–Q4/25 with FY subtotals; BW–BX Q1/26–Q2/26:** grouped and collapsed like the template.
- **BY–BZ Q3/26E–Q4/26E, CA 2026E:** forecast, calibrated to the 2026 end-points (UNVERIFIED call statements, see below).
- **CB–CF 2027E–2031E:** scenario forecast (one year more than the template, so the DCF has five explicit years after the 2026E base year).
- **Right of the forecast** (template column + 1): CG notes, CI–CL CAGRs (5Y fwd '26–'31, 5Y, 10Y, 19Y), CO–CS scenario table.

## Basis
- **Policy:** as originally reported, from each period's own earnings release (8-K Item 2.02, Ex. 99.1).
- **Not recast (documented in comments and the definition rows):**
  - the 2018 full-retrospective adoption of ASC 606 and ASU 2017-07 (2016–17 restated in the 2018 releases; FY2017 core EPS $12.04 as published vs $12.33 restated);
  - the Q3-17 formation of Global Services (Q1/Q2-17 stay on the prior BCA / BDS structure, so FY2017 Σ quarters ≠ year for the segment rows);
  - the 2019 segment realignment and the 2023 move of Boeing Capital into unallocated items.
- **Segments as reported per year:** Commercial Airplanes; Integrated Defense Systems (PE&MS / N&SS / Support Systems to 2007; BMA / N&SS / GS&S from Q3-08), renamed Defense, Space & Security in 2010 (sub-segments kept as memo rows to Q2-17); Global Services from Q3-17; Boeing Capital to 2022; Other segment to 2013.
- **Core (non-GAAP) measures:** core operating earnings and core EPS were first published in the Q4-2012 release (with FY2011 comparatives, used for FY2011). 2011–17: earnings from operations + unallocated pension / postretirement expense (after tax for EPS). 2018+: earnings from operations − FAS/CAS service cost adjustment; core EPS also removes non-operating pension / postretirement income and adds the published deferred-tax provision. 2008–10: model rebuild from the unallocated detail (flagged); 2006–07: = GAAP (detail not disclosed; the 2006–07 releases' "adjusted EPS" used a different basis and is not carried).
- **Per-share data:** no stock splits in the history window; Q4-25 diluted EPS is on the if-converted basis for the mandatory convertible preferred (flag row). FY2006: the release's $2.85 diluted EPS is not net earnings ÷ the 787.6m shares shown ($2.81) — the check row reads "n/c" with a comment.
- **Cash flow:** quarters derived from year-to-date statements (Q2 = H1 − Q1, Q3 = 9M − H1, Q4 = FY − 9M). From 2018 the cash-flow statement includes restricted cash (in Investments); a memo row reconciles it to balance-sheet cash.
- **Shares outstanding:** 1,012,261,159 issued − treasury shares (balance-sheet caption); 2017–19 year ends from XBRL `TreasuryStockCommonShares` (the caption omits the count).

## Model structure (Model tab)
- **Operating build:**
  - Commercial Airplanes: deliveries by program (737, 747, 767, 777 / 777X, 787, 717) × revenue per delivery (BCA revenues ÷ deliveries; includes non-delivery revenue) × operating margin. Backlog and backlog ÷ revenues as memo rows.
  - Defense, Space & Security and Global Services: revenues × (1 + growth) × operating margin.
  - Boeing Capital and Other segment: history only.
  - Unallocated items, eliminations and other on a core basis (excluding pension), plus the pension line (FAS/CAS service cost adjustment 2018+ / −unallocated pension & postretirement expense to 2017) = earnings from operations. Checks: build vs reported revenues and earnings from operations, and vs the core bridge.
- **Acquisitions / divestitures:** Spirit AeroSystems (closed 8-Dec-2025; $8,371m consideration; preliminary PPA from the 10-K in the Q4-25 column, with its check) and the Digital Aviation Solutions sale (31-Oct-2025, $10.55bn, $9.6bn gain in BGS / gain on dispositions) are in the actuals. There is no pending deal. The future-M&A lever is kept at zero spend.
- **2026 calibration (Q3/Q4-26E):**
  - 737 and 787 deliveries = 2026 target − 1H26, split by the Q3:Q4-25 pattern (targets ~500 and 90–100);
  - 767 and 777: prior-year quarter × 1H26 y/y;
  - BDS and BGS margins: one closed-form Δ on the 1H26 margin so the 2026 margin = ~2.5% / ~18%;
  - BCA 2H margin: a scenario assumption (company said negative in 2026);
  - free cash flow ($1–3bn): solved through 2026E year-end inventories (closed form via an operating-cash-flow-before-inventory helper).
  
  These end-points come from earnings calls (27-Jan and 28-Jul-2026), not EDGAR filings. They are labelled **UNVERIFIED** in the scenario table, header row 3 and `manual_items.json` (with the third-party sources). Boeing has published no numeric outlook in its releases since 2019.
- **GAAP P&L from the build:** earnings from operations = core operating earnings + pension line. Cost of products & services is implied. Interest is calculated on opening debt; other income = yield on opening cash & investments + non-operating pension. Tax uses an input rate (valuation allowance). Mandatory convertible preferred dividends run to the Oct-2027 conversion.
- **Bridges** (checks vs published in every reported period):
  1. **Earnings from operations → core operating earnings** (company definition, flags by period).
  2. **Net earnings → earnings from operations → EBITDA → adjusted EBITDA:** a model definition (core operating earnings + D&A), because Boeing publishes no EBITDA.
  3. **Diluted EPS → core EPS:** deferred-tax provision as published 2018+; derived from the published per-share figures 2011–17; 35% statutory 2008–10.
- **Other schedules:**
  - Cash flow (incl. the non-cash 401(k) treasury-share line) and the share schedule (401(k) issuance at the model price; preferred conversion of 5.828–6.994 shares per preferred share).
  - Balance sheet: 2026E rolled from 30-Jun-2026 + 2H flows, with the pension liability rolled with the cash-flow pension line.
  - Working capital (inventory days on cost of sales, advances % of revenues).
  - Debt: 10-K maturities, refinancing % input, revolver / CP to minimum cash, headroom memo.
  - Leverage-target buybacks (net debt / adjusted EBITDA: 1.0x / 0.5x / 0.0x).
  - Ratios and valuation (EV includes pension & retiree-health liabilities and NCI).
- **DCF basis:** NOPAT on core operating earnings (full-cost; after D&A, share-based plans, reach-forward losses) less gains on dispositions, at 21%. The FAS/CAS recovery is excluded with core. UFCF adds D&A, less capex, ± working capital. EV → equity deducts net debt (incl. short-term investments), pension & retiree-health liabilities and NCI. The preferred is in the diluted share count, not in debt.

## Key forecast assumptions (Base)
- **Deliveries:** 737 560 / 610 / 640 / 650 / 660; 787 110 / 125 / 135 / 140 / 140; 777 / 777X 35 / 55 / 65 / 70 / 70; 767 25 / 5 / 0 (2027E–2031E).
- **Revenue and margins:**
  - Revenue per delivery +4% in 2027E, then +3% a year.
  - BCA margin 3% → 12%.
  - BDS +5% → +4% growth at 6% → 9% margin; BGS +5–6% at 18%.
  - Unallocated −2.0% → −1.6% of segment revenues; FAS/CAS $600m → $400m.
- **Costs, tax and capex:** D&A 2.3–2.4% of revenues; G&A 5.8% → 5.5%; R&D 3.9% → 3.7%; tax 10% → 20% (valuation allowance unwinds); capex 4.2% → 3.3% of revenues.
- **Working capital:** inventory days 370 → 315; advances 64% → 57% of revenues.
- **Debt:** maturities refinanced 0% (2027) → 100% (2030+); minimum cash $8bn.
- **Valuation inputs:** WACC 9.1% (risk-free 4.25%, ERP 5%, beta 1.2; market inputs are assumptions, since rate sources are not reachable from the build environment).
- **Share price:** $185.00, user-provided (10-Oct-2026). Update it at `Model!CA` in the valuation block.

Base outputs: 2026E FCF $2.0bn (solved), 2027E $6.7bn, 2028E $10.6bn; core EPS −$0.88 (2026E), $4.17 (2027E), $15.08 (2031E); DCF $193.55 per share (+4.6%); price target (30x 2031E core EPS) $452 (Bull $729 / Bear $201).

## Data corrections
None: no published figure is overridden. Known data exceptions are documented, not corrected:
- FY2006 diluted EPS denominator.
- Q4-20 core EPS $(15.25) vs bridge $(15.23) (per-share rounding; the check tolerance is ±0.025).
- FY2017 segment Σ quarters ≠ year (Global Services formed in Q3-17).

## Sources
SEC EDGAR only (CIK 0000012927):
- Forms 10-K / 10-Q 2006–Q2-2026.
- Form 8-K Item 2.02 earnings releases (Ex. 99.1), Q4-2005 – Q2-2026 (78 releases).
- FY2025 10-K: Spirit acquisition PPA, debt maturities, amortization schedule, preferred conversion terms.
- Q2-26 10-Q: debt, liquidity, revolvers.
- XBRL company facts: cross-checks of revenue, net income and total assets, and treasury shares.

The investor-relations site (boeing.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR.
- `filings.csv` indexes the filings, and each `data/<period>.json` lists its source URLs.
- `data/_xbrl.json` holds the XBRL subset.
- `manual_items.json` holds the Spirit PPA, the EDGAR facts used as inputs (debt, maturities, amortization, preferred, production rates), the share price, the Q4-25 if-converted flag and the UNVERIFIED 2026 call guidance with its sources.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export BA_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`.
   3. `python3 check_data.py` runs 1,522 checks: statement arithmetic, segment sums, core bridges vs published, EPS, deliveries, FCF, cash and balance-sheet tie-outs, quarters vs years, and XBRL cross-checks. 8 known exceptions, all documented above.
3. Build: `python3 build.py --snap --recalc` writes `../BA_Model.xlsx`, reruns with the switch on Bull and Bear to fill the snapshot panels, and stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate (on a recalculated copy):
   - `python3 ../tools/inspect_model.py <file>` → 0 error cells, 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../BA_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../BA_Model.xlsx --extra WWD Woodward 382.17` → 0 residue hits.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`: EDGAR filings index, downloads, HTML → text.
- `tables.py`: positional (colspan-aware) HTML table reader. It assigns each value to the period header it sits under, so sparse rows stay aligned.
- `extract.py`: release classification and per-period extraction (statements, segments, unallocated detail, deliveries, backlog, core reconciliation, FCF, prior-year comparatives).
- `xbrl.py`: XBRL company-facts helper (calendar year).
- `normalize.py`: basis rules, flat model keys, discrete quarterly cash flow.
- `check_data.py`: data consistency checks.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
