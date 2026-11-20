# TLN model build kit

`models/TLN_Model.xlsx` is the Talen Energy Corporation (NASDAQ: TLN) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD build kit:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!AD2`, scenario table in `Model!AL:AP`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). 2026E is the base year (nine months actual; net debt at 31-Dec-2026E), so the explicit years are 2027E–2031E.
  - Charts: generation and capacity-revenue growth, Adjusted EBITDA / operating income, returns (re-ranged to 2021–2031E).
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer.

## Columns (calendar fiscal year)
- **C–D FY2021–FY2022:** annual, Predecessor (Talen Energy Supply, LLC), from the Form S-1. FY2021 has no balance sheet.
- **E–S Q1/23–Q4/25 with FY subtotals; T–V Q1/26–Q3/26:** grouped and collapsed like the template.
- **W Q4/26E, X 2026E:** forecast, calibrated to the FY26 Adjusted EBITDA guidance (Q3-26 release, 3-Nov-2026).
- **Y–AC 2027E–2031E:** scenario forecast; 2027E is solved to the FY27 Adjusted EBITDA guidance.
- **Right of the forecast** (template column − 54): AD notes, AF–AI CAGRs (5Y fwd '26–'31, 2Y, 3Y, 4Y), AL–AP scenario table.

## Basis
- **Policy:** as originally reported — each period from the first filing that presents it.
- **Fresh-start accounting:** Talen Energy Corporation emerged from Chapter 11 on 17-May-2023. FY2021, FY2022 and 1-Jan to 17-May-2023 are the Predecessor and are not comparable with the Successor.
  - FY2023 = Predecessor + Successor (18-May to 31-Dec-2023), summed as presented (cell comments).
  - Q1/23 from the S-1; Q2/23 = 1-Apr to 17-May + 18-May to 30-Jun (Q2-24 10-Q); Q3/23 from the Q3-24 10-Q; Q4/23 = FY − Q1 − Q2 − Q3.
  - No balance sheets were published for 31-Mar, 30-Jun and 30-Sep-2023.
- **Q4:** fiscal year − nine months (the releases give no three-month Q4 statements). The Q4/25 Adjusted EBITDA bridge is as published.
- **Segments:** PJM is the only reportable segment. PJM segment Adjusted EBITDA is a memo block on the current basis (FY2022+ annual, quarterly from Q1/24). The S-1 basis (PJM / ERCOT and WECC) is not carried.
- **Per-share data:** Successor only (from 18-May-2023). No splits. Q4 weighted shares = 4 × FY − Σ Q1–Q3 (derived).
- **Cash flow:** quarters derived from year-to-date (Q4 = FY − 9M). Cash includes restricted cash.

## Model structure (Model tab)
- **Operating build:** Adjusted EBITDA = generation (TWh) × adjusted energy margin per MWh + capacity revenues − adjusted operating costs.
  - Adjusted energy margin = energy and other revenues − fuel and energy purchases − the non-cash amortization of acquired contract liabilities (model measure; realized hedges in, unrealized mark-to-market out).
  - Capacity revenues 2027E+ = contracted revenues (10-Q schedule of fixed-fee performance obligations) + future auctions (MW × $/MW-day × uncovered days).
  - Adjusted operating costs are derived historically (Adjusted EBITDA − energy margin − capacity revenues) and grow from a 2026E pro forma run-rate.
- **Acquisition blocks:** Freedom & Guernsey (25-Nov-2025) and Cornerstone (15-Jun-2026) are in actuals; their provisional PPAs are in the schedules block. The 2026E pro forma generation (81 TWh) is an analyst estimate and is flagged.
- **Future M&A lever:** none. Talen's deals are large, discrete plant portfolios and the company benchmarks capital allocation against buybacks; `cf_acq` is nil in the forecast.
- **Guidance calibration:**
  - FY26: capacity revenues (10-Q schedule), costs and guided items are applied first; one Δ on the Q4/26E energy margin per MWh solves FY26 Adjusted EBITDA to $2,200m / $2,125m / $2,050m.
  - FY27: the energy margin per MWh is solved so that Adjusted EBITDA = $2,850m / $2,675m / $2,500m.
  - Adjusted Free Cash Flow guidance (FY26 $1,225–1,325m; FY27 $1,500–1,750m) is an information row, not forced. Base result: $1,275m and $1,617m.
- **GAAP P&L from the build:** operating income = Adjusted EBITDA − D&A (reconciliation basis) − nuclear fuel amortization − stock compensation − other excluded items. O&M is the implied line. Interest is calculated on opening balances plus the accretion of the capacity-monetization discount; tax at 25%.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **Net income → EBITDA → Adjusted EBITDA:** company definition. Company line items are grouped into eight rows; the wording per period is in cell comments.
  2. **Adjusted EBITDA → Adjusted Free Cash Flow:** company definition (published from Q2/24; FY2023 from the Q4-24 release).
  3. **Net income → adjusted net income → adjusted EPS:** model definition (Talen publishes none): adjusting items of bridge 1 after 25% tax. There is no company figure to check.
- **Other schedules:** cash flow; buybacks (incl. the $1.5bn ASR of 1-Oct-2026); balance sheet; working capital; PPAs; debt (term-loan amortization, 2031 refinancing, revolver to a $350m minimum cash, term-loan cash sweep); the deferred capacity obligation of the PJM capacity monetization; leverage-target buybacks (3.5x net debt / Adjusted EBITDA, company target); ratios and valuation.
- **DCF basis:** NOPAT on adjusted EBIT (Adjusted EBITDA − D&A − nuclear fuel amortization) less stock compensation, restructuring and acquisition costs, at 25%. Capex includes nuclear fuel and growth capex. The deferred capacity obligation is counted as debt; the terminal year sets capex equal to D&A. Market inputs are assumptions.

## Key forecast assumptions (Base)
- **Generation:** 81 TWh pro forma base, flat in 2027E, then +0.5–1% (assumption).
- **Energy margin per MWh:** $23.6 in Q4/26E and $26.8 in 2027E (both solved to guidance); +3–4% a year from 2028E (assumption).
- **Capacity:** contracted $1,270m (2027), $1,248m (2028), $529m (2029); then 10,180 MW at $300/MW-day (assumption; $325 Bull, $225 Bear).
- **Costs:** +3% a year. D&A $650m in 2027E (guidance). Stock compensation $160m rising 5% (assumption).
- **Cash items:** maintenance capex $370m (2027E guidance), growth capex $120m falling to $50m (assumption), cash taxes $60m (guidance) rising to $330m (assumption), pension $20m.
- **Capital return:** buybacks plug to 3.5x net debt / Adjusted EBITDA excluding the deferred capacity obligation (switch row; assumption).
- **Share price $354.52:** Form 4 open-market sale on 17-Nov-2026 (filed 19-Nov-2026), the latest share price in an SEC filing. Update it at `Model!X` in the valuation block.

## Data corrections
- None. Known data exceptions (documented, not corrected):
  - Bridge categories do not sum Q1–Q4 = FY in 2024 and 2025 by up to $9m, because the S-1 (Q1/24) and the Q4/25 three-month column group interest, D&A and items slightly differently. Adjusted EBITDA itself ties.
  - Q3/25 diluted EPS computes to $4.26 vs $4.25 reported (check tolerance ±$0.02).
  - Adjusted EBITDA checks on the combined 2023 periods use ±$1.5m.

## Sources
SEC EDGAR only (CIK 1622536):
- Form S-1 (20-Jun-2024): FY2021–22, the two 2023 periods, Q1/23, Q1/24.
- Forms 10-Q Q2/24–Q3/26 and Forms 10-K FY2024–FY2025.
- Form 8-K earnings releases (Ex. 99.1), Q2/24–Q3/26; PJM auction results; deal and financing 8-Ks; the 8-K of 12-Nov-2026 (capacity sales).
- Form 4 filings of Nov-2026 (share price).
- XBRL company facts for cross-checks (`xbrl_check.py`: 58 comparisons, 0 differences).

The investor-relations site (talenenergy.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR. All guidance used is from the Form 8-K of 3-Nov-2026; nothing from outside EDGAR is used. `filings.csv` indexes the filings, and each `data/<tag>.json` lists its source URLs. `manual_items.json` holds guidance, capacity auctions and contracted revenues, the capacity monetization, PPAs, debt facts, share counts, the ASR and the share price, each with its source.

The same CIK also carries the 2015–16 filings of the first public Talen Energy Corporation (taken private in Dec-2016), and Talen Energy Supply filed under CIK 1161976 until 2016. Both are outside the history window: the S-1 presents the Predecessor only from FY2021.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export TLN_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`.
   3. `python3 check_data.py` runs 396 checks: statement arithmetic, both bridges vs published, EPS, cash and balance-sheet tie-outs, and quarters vs years. Known exceptions: none (see Data corrections for the exemptions).
   4. `python3 xbrl_check.py` compares revenues, operating income, net income, operating cash flow and total assets with the XBRL company facts.
3. Build: `python3 build.py --snap --recalc` writes `../TLN_Model.xlsx`, reruns with the switch on Bull and Bear to fill the snapshot panels, and stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../TLN_Model.xlsx` should show 0 error cells and 0 non-zero check rows.
   - `python3 ../tools/cyc.py ../TLN_Model.xlsx` should show 0 cycles.
   - `python3 ../tools/residue_scan.py ../TLN_Model.xlsx --extra WWD Woodward 382.17` should show 0 residue hits.
   - `python3 qa_scen.py <workdir>` flips the switch to Bull and Bear, recalculates, and prints the ordering.
   - Intentional exceptions: none. Chart cells for years without data (ROIC 2021; Adjusted FCF 2021–22) are left empty.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `h2t.py`, `make_index.py`, `fetch.py`, `parse_release.py`, `extract.py`: EDGAR HTML → text, filings index, downloads, table parser, per-period extraction.
- `normalize.py`: basis rules, Predecessor + Successor combination, flat model keys, discrete quarterly cash flow.
- `check_data.py`, `xbrl_check.py`: data consistency checks and the XBRL cross-check.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`). `qa_scen.py`, `dump.py`: scenario QA and a row dumper.
- `EXTRACTION_SCHEMA.md`: raw-record schema and rules.
