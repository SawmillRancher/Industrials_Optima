# NFLX model build kit

`models/NFLX_Model.xlsx` is the Netflix, Inc. (NASDAQ: NFLX) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD build kit:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CG2`, scenario table in `Model!CO:CS`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). 2026E is the base year (net debt at its year end); the explicit years are 2027E–2031E.
  - Charts: regional contribution to revenue growth, adjusted EBITDA / operating income, returns.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (fiscal year ends 31 December)
- **C–I FY2006–FY2012:** annual, as originally reported.
- **J–BV Q1/13–Q4/25 with FY subtotals; BW–BX Q1/26–Q2/26:** grouped and collapsed like the template.
- **BY–BZ Q3/26E–Q4/26E, CA 2026E:** forecast, calibrated to the Q3-26 and FY26 outlook (Q2-26 letter, 16-Jul-2026).
- **CB–CF 2027E–2031E:** scenario forecast.
- **Right of the forecast** (template column + 1, because 2031E is added): CG notes, CI–CL CAGRs (5Y fwd '26–'31, 5Y, 10Y, 19Y), CO–CS scenario table.

## Basis
- **Policy:** as originally reported in each period's own 10-Q / 10-K (annual = 10-K; Q4 = FY − 9M, tied to the Q4 letter).
- **Recasts:**
  - **2018 quarters:** Q1–Q3 2018 take the recast comparatives from the 2019 10-Qs, because personnel costs were reclassified effective Q4-2018 (8-K 3-Jan-2019; operating income unchanged). The originally reported cost lines are quoted in the cell comments.
  - **Regional data:** first published in the FY2019 10-K, which gives FY2017–19 annual; the 2019 quarters come from the 2020 10-Q comparatives (latest filing presenting the period).
- **Segments:** Domestic streaming / International streaming / Domestic DVD (Q4-2011–2019; memo rows with Σ checks). There is a single operating segment from 2020. Revenue by region (UCAN / EMEA / LATAM / APAC) runs from 2017. Paid memberships and ARM were published to Q4-2024. The DVD service closed in Sep-2023, so DVD revenue to 2023 sits outside the regional tables in a derived row.
- **Per-share data:** split-adjusted by the filing date of each source, ×70 before 15-Jul-2015 (7-for-1) and ×10 before 14-Nov-2025 (10-for-1). Per-share history is therefore small (FY2006 EPS $0.01).
- **Cash flow:** quarters derived from year to date (Q4 = FY − 9M). From 2018 cash-flow cash includes restricted cash, shown as a memo line (CF cash − BS cash).

## Model structure (Model tab)
- **Operating build:**
  - Regional revenue = prior-year quarter × (1 + growth); out-years = prior year × (1 + scenario lever).
  - Paid memberships, ARM, paid net additions and revenue per paid membership are history KPIs.
  - Regional and legacy contribution-to-growth rows feed the Charts tab.
- **Deals:**
  - **WBD:** the WBD merger (agreed 4-Dec-2025, amended 19-Jan-2026) was terminated on 27-Feb-2026, and the $2.8bn fee received is in Q1-26 interest and other income, adjusted out of adjusted EPS.
  - **Q1-26 acquisition:** ~$587m, no PPA disclosed, in other non-current assets. No pending deal.
  - **Future M&A lever:** cash spend only (capability acquisitions; no revenue attached).
- **FY26 outlook calibration (Q3/Q4-26E):**
  - **Revenue:** a uniform Δ on the 1H-26 y/y growth of the four regions, solved separately per quarter. Q3-26E hits the $12,860m Q3 guide; Q4-26E hits the FY26 end-point ($51.4 / 51.2 / 51.0bn).
  - **Content amortization:** FY26 = FY25 × 1.10 (guided ~10%), with 2H split by the 2H-25 mix.
  - **Non-content costs:** one proportional Δ on other cost of revenues, marketing, T&D and G&A (prior-year quarter ratio + 1H-26 drift), solved to the Q3 operating margin (33.2%) and the FY26 margin (31.5%). These are separate Δs per quarter.
  - **Free cash flow:** FY26 FCF (~$12.5bn) is hit through a 2H other operating cash flow booked to other non-current assets (deposits; the Q4-25 letter expects a ~$700m Brazil tax deposit in 2026). It does not reverse in 2027E.
  - **Information rows:** Q3 net income and EPS guides (model: $3,452m / $0.82, on the guide), FY26 operating-income growth (20%+) and content-amortization growth.
- **GAAP P&L from the build:**
  - Operating income = revenue − content amortization − non-content costs. In 2027E+ other cost of revenues balances to the operating-margin lever.
  - Interest is on opening balances. Interest and other income = yield × opening cash and investments.
  - Tax is 16.5% for Q3/Q4-26E (implied by the Q3 guide), then 17%.
- **GAAP → adjusted bridges:**
  1. **Operating income → adjusted operating income:** model definition. Only one-offs the company quantified are added back: Q2-22 restructuring ~$150m and the Q3-25 Brazilian non-income tax expense ~$619m. Netflix publishes no adjusted operating income.
  2. **Net income → EBITDA → adjusted EBITDA:** company definition (+ interest and other, tax, non-content D&A, SBC). Published Q2-14 – Q1-23 and checked; rebuilt on the same definition elsewhere. The bridge continues to adjusted EBIT, full-cost (= adjusted operating income), for NOPAT.
  3. **Net income → non-GAAP / adjusted net income → EPS:** the company definition where published (2006–09 excluding stock-based compensation; Q1-13, Q4-14, Q1-15, Q4-15), checked to the published EPS. Elsewhere it is a model definition: GAAP + F/X remeasurement on euro debt (2017+), restructuring, Brazil expense and the WBD fee, tax-effected at the period ETR bounded to 15–40%.
  4. **Free cash flow:** company definition with the historical extra items (DVD / content library, other assets to 2020), checked to every published figure.
- **Other schedules:**
  - Cash flow with content investment: cash content spend = ratio × content amortization.
  - Buybacks and balance sheet (content-asset roll-forward), working capital at year-end ratios.
  - Debt: notes repaid at par maturity and refinanced 100%; $1bn 5.250% notes due 2036 issued 22-Jul-2026; $3bn revolver to a $3bn minimum cash.
  - Cash-return buybacks: plug to a target year-end cash balance of 1.75 / 2.0 / 2.5 months of revenue.
  - Ratios and valuation.
- **DCF basis:**
  - NOPAT is on operating income after content amortization and SBC, plus non-content D&A.
  - Cash content spend above amortization and other working capital are deducted (DCF row 23).
  - Leases are operating. No NCI. Net debt is taken at the 2026E year end (includes the WBD fee).
  - Market inputs (risk-free 4.25%, ERP 5%, beta 1.15) are assumptions.

## Key forecast assumptions (Base)
- **Regional revenue growth 2027E–31E:** UCAN 9% → 6%; EMEA 11% → 7%; LATAM 12% → 8%; APAC 13% → 9% (assumptions citing FY25 / 1H-26 trends).
- **Operating margin:** 33.5% → 38.5% (FY26 guided 31.5%; +2–3pp a year since 2023).
- **Content:** amortization +8% → +5.5%; cash content spend / amortization 1.10x → 1.05x.
- **Opex % of revenue (inputs):** marketing ~7%, T&D 7.7% → 7.2%, G&A 4.2% → 3.9%.
- **Other inputs:** capex 1.6% → 1.3% of revenue; non-content D&A 0.8%; SBC 1.1%; tax 17%; M&A $500m a year.
- **Share price $70.00:** provided by the user (13-Oct-2026), at `Model!CA` in the valuation block; update to market.

## Data corrections
- **Q4-14 non-GAAP net income:** the Q4-14 letter prints the release of tax accrual as +38,612 but deducts it; the model deducts it, as the later letters print it.
- **FY2006 10-K:** columns are presented oldest first; the extraction takes the 2006 column.
- **Known exceptions** (documented, not corrected):
  - The FY2007 10-K CFO ($291.8m) differs from the Q4-07 release ($290.1m), so the FY2007 FCF check is n/p.
  - Q2-13 published FCF matches within $0.1m, because the Q2-13 letter uses a restated Q1-13 CFO.

## Sources
SEC EDGAR only (CIK 1065280):
- Forms 10-K FY2006–FY2025 and 10-Q Q1-2013 – Q2-2026.
- Form 8-K Item 2.02 shareholder letters / earnings releases (Ex. 99.1), Q4-2006 – Q2-2026, for published FCF, adjusted EBITDA, non-GAAP net income, Q4 EPS and shares, Q4 regional ARM and guidance.
- 8-Ks:
  - WBD merger agreement (5-Dec-2025, 20-Jan-2026) and its termination (27-Feb-2026, Item 1.02);
  - bridge facility (22-Dec-2025);
  - stock split (30-Oct-2025);
  - buyback authorization (23-Apr-2026);
  - $1bn 2036 notes (22-Jul-2026);
  - personnel-cost reclassification (3-Jan-2019).
- XBRL company facts for cross-checks and shares outstanding.

The investor-relations site (ir.netflix.net) is not used; its letters are the same documents as filed on EDGAR.
- `filings.csv` indexes the filings, and each `data/<period>.json` lists its source URLs.
- `manual_items.json` holds the FY26 guidance history, the debt ladder and new notes, capital-return facts, the WBD and acquisition facts, the company-quantified one-offs, the share price and the data corrections, each with its source.
- **Guidance:** all FY26 guidance is from the EDGAR letters, so none is unverified.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export NFLX_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`, then `python3 -c "import xbrl; xbrl.dump_subset()"`.
   3. `python3 check_data.py` runs 1,254 checks: statement arithmetic, EPS, cash and balance-sheet tie-outs, regions / legacy segments, published FCF / adjusted EBITDA / non-GAAP net income, quarters vs years and XBRL. Known exceptions are logged: FY2007 FCF, Q2-13 restated CFO, Q4-14 sign.
3. Build: `python3 build.py --snap --recalc` writes `../NFLX_Model.xlsx`. It reruns with the switch on Bull and Bear to fill the snapshot panels, then stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 inspect_model.py <recalculated file>` → 0 error cells, 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 cyc.py ../NFLX_Model.xlsx` → 0 cycles.
   - `python3 residue_scan.py ../NFLX_Model.xlsx --extra WWD Woodward 382.17` → 0 residue hits.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs, compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `h2t.py`, `make_index.py`, `fetch.py`, `extract.py`: EDGAR HTML → text, filings index, downloads, per-period extraction (face statements, segment and regional tables, letter non-GAAP tables).
- `xbrl.py`: XBRL company-facts helper.
- `normalize.py`: basis rules, flat model keys, discrete quarterly cash flow, split adjustments, published non-GAAP matching.
- `check_data.py`: data consistency checks.
- `inspect_model.py`, `cyc.py`, `residue_scan.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
