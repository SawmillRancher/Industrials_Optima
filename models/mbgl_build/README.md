# MBGL model build kit

`models/MBGL_Model.xlsx` is the Mobility Global Inc. (NYSE: MBGL) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`. The kit was adapted from `wwd_build`, and the short-history handling follows `loar_build`.
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8, with quarterly columns grouped and collapsed.
- **Scenarios:** the Bull / Base / Bear switch is in `Model!AC2`; the scenario table is in `Model!AK:AO`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT).
  - Charts (2023–2031E).
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer.

## The company and the spin
- **Spin:** S&P Global spun off its Mobility division on 1-Jul-2026 by a tax-free pro rata distribution: one MBGL share per SPGI share held on 15-Jun-2026, so 294,821,320 shares.
- **Brands:** CARFAX, automotiveMastermind, Polk Automotive Solutions and Market Scan.
- **Origin:** S&P Global acquired the business with IHS Markit (merger closed 28-Feb-2022). Goodwill of $8.8bn and $3.6bn of intangibles from that purchase accounting sit on the balance sheet.
- **Spin financing:**
  - $2.0bn of senior notes (5.050% 2029, 5.450% 2031, 6.050% 2036; issued 29-May-2026) funded a $2.0bn dividend to S&P Global.
  - A $500m revolver (to Jul-2031) is undrawn.
- **Registrant:** CIK 0002090312, named "S&P Global Mobility Holding Co" until Jan-2026.

## Columns (fiscal year ends 31 December)
- **C, FY2022:** the S&P Global Mobility segment memo only (S&P Global non-GAAP pro forma full year). No carve-out data exists for 2022.
- **D–R, Q1/23–Q4/25 with FY subtotals:**
  - FY2023–25 annual come from the Form 10 audited combined statements.
  - All four 2025 quarters come from the Form 10 / 10-Q, and from Ex. 99.2 for Q3 / Q4.
  - The 2023–24 quarters hold only the S&P Global segment memo and the spliced revenue line. The carve-out never published them.
- **S–T, Q1/26–Q2/26:** actual, carve-out basis.
- **U–V, Q3/26E–Q4/26E; W, 2026E:** calibrated to the FY26 outlook.
- **X–AB, 2027E–2031E:** scenario forecast.
- **Right of the forecast** (template column − 55): AC notes, AE–AH CAGRs (26–31 fwd, 23–25, 24–25, 22–25), AK–AO scenario table.

## Basis
- **Policy:** carve-out (combined) statements of the Mobility business, as originally reported. Nothing has been restated yet.
  - The carve-out includes S&P Global corporate allocations, separate-return taxes, related-party loan interest and "parent company investment" equity.
  - From Q3-26 the company reports on a consolidated standalone basis.
- **Segments:** CARFAX and B2B, plus corporate unallocated. This is the 2025 realignment, and the company recast all periods presented. The 2025 cost-allocation refinement also changed segment profit history.
- **Q3-25 / Q4-25:** from the FY2025 quarterly data file (8-K Ex. 99.2, 7-Aug-2026), which the company labels "unaudited and preliminary".
  - The exhibit is slide images. Its values are transcribed in `extract.py` (`EX992`, `EX992_SEG`), and every segment column re-adds to the published Adjusted EBITDA.
  - Depreciation and amortization are shown only combined, so Adjusted operating profit is not computable for those two quarters.
- **S&P Global Mobility segment (memo, CIK 64040):**
  - Revenue ties to the carve-out within $0–4m (≤0.25%) in every overlapping period (FY23 +1, FY24 +4, FY25 +3, Q4-25 +2, others 0–1). On that basis the model carries a **spliced revenue history**: S&P Global for FY2022 pro forma and Q1-23–Q4-24, carve-out thereafter.
  - Profit is **not** comparable. S&P Global segment results exclude corporate allocations and stand-up costs and carry S&P Global's deal amortization ($303m vs $296m). They are shown only as memo rows, with a basis-difference row.
  - FY2025 carve-out segment Adjusted OP (CARFAX + B2B, $697m) equals S&P Global's Mobility adjusted OP exactly. FY2023–24 differ by $5m and $11m because of the 2025 allocation refinement.
- **Per-share data:** published only for Q2-25 / Q2-26. The 10-Q applies the 294.8m distributed shares to all periods it presents. Other historical periods have no per-share data (not estimated).
- **Cash flow:**
  - FY2023–25 annual and Q1 as filed; Q2 = 1H − Q1 (10-Q).
  - Q3-25 / Q4-25 cash flow was never published, so those cells are empty.
- **Balance sheets:** 31-Dec-2023 (from the first Form 10 draft, DRS 23-Oct-2025), 31-Dec-2024 / 2025 and 31-Mar-2026 (Form 10), 30-Jun-2026 (10-Q). Mar-, Jun- and Sep-2025 balance sheets were never published.

## Model structure (Model tab)
- **Segment build:**
  - CARFAX and B2B revenue, each with subscription / non-subscription and international memo rows.
  - Segment Adjusted EBITDA = revenue × margin.
  - Corporate Adjusted EBITDA: an input for Q3/Q4-26E (standalone costs), then % of revenue.
  - Segment GAAP OP, D&A, SBC and items are memo rows, with a check to Segment Adjusted EBITDA.
- **S&P Global segment memo and spliced revenue** (see Basis).
- **Future M&A lever:** spend ÷ EV/sales, margin, intangibles split and amortization. Base is nil; nothing is announced.
- **FY26 outlook calibration** (Q2-26 release, 7-Aug-2026):
  - A uniform growth Δ on both segments (vs 1H/26 y/y) solves FY26 revenue to $1,870 / 1,877.5 / 1,885m (Bear / Base / Bull). Base Δ is −0.3pt.
  - A uniform segment-margin Δ (prior-year quarter margin + 1H/26 drift) solves Adjusted EBITDA to $745 / 752.5 / 760m, after the corporate-cost input. Base Δ is −0.7pt: standalone dis-synergies.
  - Both are closed-form solves via sensitivity helper rows.
- **GAAP P&L from the build:**
  - Operating profit = Adjusted EBITDA − D&A − SBC − transaction costs − severance & other.
  - Operating-related expenses are a % of revenue; selling & general expenses is the balancing line.
  - Amortization follows the Form 10 schedule ($296m 2026–29, $293m 2030).
  - Interest: a 2H/26 point estimate, then coupons on opening notes + accretion + revolver − interest income.
- **Bridges** (checks vs published in every reported period, ±1 whole-$m rounding):
  1. **Net income → EBITDA → Adjusted EBITDA:** company definition. Other income stays inside EBITDA (FY23 $2m, FY24 $1m). Company item wording is in cell comments.
  2. **Operating profit → Adjusted operating profit:** company definition, published in the Form 10 only (FY2023–25, Q1-25, Q1-26). Also checked as Adjusted OP + depreciation + SBC (+ other income) = Adjusted EBITDA.
  3. **Adjusted net income / EPS:** a **model definition** (Mobility Global publishes none). It adds back amortization, transaction costs and other items, tax-effected at the period ETR bounded 15–40%.
- **Other schedules:**
  - cash flow; buybacks; balance sheet; working capital (year-end ratios);
  - debt: notes face / carrying value with accretion; 2029 and 2031 notes refinanced at maturity (assumption); revolver to a $200m minimum cash;
  - leverage-target buybacks; dividends ($0.06 a quarter × beginning shares);
  - ratios and valuation.
- **DCF basis:**
  - Base year 2026E: the valuation date falls in Q4-26, and net debt is taken at 31-Dec-2026. The template columns are rolled one year, so the explicit years are 2027E–31E.
  - NOPAT is taxed on Adjusted EBITA (pre-amortization) less SBC and cash adjusting items, with a depreciation-only add-back (playbook 5.7). The $296m p.a. of acquired-intangible amortization is non-deductible.

## Key forecast assumptions (Base) — all are assumptions unless stated
- **Revenue growth:** CARFAX 8.0% → 7.0% and B2B 5.0% → 4.0% (2027–31). History: CARFAX FY24 +12%, FY25 +10%, 1H/26 +8%; B2B +3%, +6%, +6%.
- **Segment Adjusted EBITDA margins:**
  - CARFAX 48.0% → 50.0% (FY25 46.9%, 1H/26 48.0%).
  - B2B 33.5% → 35.5% (FY25 32.4%, 1H/26 32.6%).
- **Corporate:** −$12m a quarter in 2H/26, then −2.4% → −2.0% of revenue. The Form 10 pro forma quantifies only $12m p.a. of standalone cost (TSA + new leases); the rest is an assumption.
- **Adjusting items:**
  - Transaction (stand-up) costs: $10m a quarter in 2H/26 and $10m in 2027E, then nil.
  - SBC: $6m a quarter in 2H/26, then 1.3% of revenue.
  - Severance & other: $8m p.a.
- **Tax:** 29% in 2H/26 (1H/26 29.4%), 28.5% from 2027.
- **Capex:** 1.4% of revenue.
- **Deferred tax:** −$80m p.a.
- **Interest:** 2H/26 $54m (coupons $110.6m p.a. on $2.0bn). Form 10 pro forma: $114m p.a. gross.
- **Leverage target for buybacks:** 2.0x Base / 2.5x Bull / 1.5x Bear. No company target is published; the covenant is ≤ 3.50x.
- **Dividend:** $0.24 a year, +5% p.a. from 2028.
- **DCF:** WACC 8.5% (beta 1.15, risk-free 4.25%, ERP 5%, cost of debt 5.75%, D/V 25%); fade 6% → 4%; terminal growth 3%.

## Data corrections
- None. Q3-25 / Q4-25 are taken as published in Ex. 99.2 (preliminary). FY2024 Adjusted OP uses the published total ($617m); the segment columns add to $618m.

## Sources
SEC EDGAR only. Mobility Global CIK 0002090312; S&P Global CIK 0000064040.
- **Form 10:** information statement (10-12B/A Ex. 99.1, 27-May-2026; 10-12B 7-May-2026). The first draft (DRS, 23-Oct-2025) supplies the 31-Dec-2023 balance sheet.
- **Form 10-Q, Q2-26** (7-Aug-2026).
- **Form 8-K:** Q2-26 earnings release (Ex. 99.1) and FY2025 quarterly financial data (Ex. 99.2), 7-Aug-2026; separation 8-K (2-Jul-2026).
- **S&P Global earnings releases** (8-K Item 2.02 Ex. 99.1), Q1-22–Q2-26: the Mobility segment memo.

The investor-relations site (ir.mobilityglobal.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR. `filings.csv` indexes the documents, and each `data/<period>.json` lists its source URLs. `manual_items.json` holds guidance, debt terms, the amortization schedule, pro forma standalone costs, share facts and the price.

**Unverified on EDGAR:** the Q2-26 release says the company "reiterated medium-term financial targets", but the targets are in no EDGAR filing. They are not used in the model.

The share price ($18.00, provided by the user on 13-Oct-2026) is an input at `Model!W` in the valuation block (`v_px`); update it to market. The latest SEC-filed price is a Form 4 withholding price of $19.83 (1-Sep-2026).

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export MBGL_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`.
   3. `python3 check_data.py` runs 321 checks (statement arithmetic, segment sums and Adjusted EBITDA builds, the Adjusted EBITDA reconciliation, Ex. 99.2 vs filings, Σ 2025 quarters = FY, cash flow, balance sheet, FCF, S&P Global segment arithmetic). Known exceptions: none.
3. Build: `python3 build.py --snap --recalc` writes `../MBGL_Model.xlsx`, reruns with the switch on Bull and Bear to fill the snapshot panels, and stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../MBGL_Model.xlsx` should show 0 error cells and 0 non-zero check rows.
   - `python3 ../tools/cyc.py ../MBGL_Model.xlsx` should show 0 cycles.
   - `python3 ../tools/residue_scan.py ../MBGL_Model.xlsx --extra WWD Woodward 382.17` should show 0 hits.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, header, recalculation and value storage.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML (re-ranged to C:K, 2023–2031E).
- `h2t.py`, `make_index.py`, `fetch.py`, `extract.py`: EDGAR HTML → text, filings index, downloads, per-period extraction (including the Ex. 99.2 transcription and the S&P Global segment parser).
- `normalize.py`: basis rules, flat model keys, discrete quarterly cash flow, grouped adjusting items.
- `check_data.py`: data consistency checks.
- `inspect_model.py`, `cyc.py`: kit copies of the QA tools (the canonical versions are in `models/tools/`).
- `EXTRACTION_SCHEMA.md`: per-period schema and rules.
