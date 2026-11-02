# EXENS model build kit

`models/EXENS_Model.xlsx` is the Exosens SAS (Euronext Paris: EXENS) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, starting from the ONON kit (IFRS, non-USD) and re-based to half-year columns (RMS / BC pattern):
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with half-year columns grouped and collapsed under each fiscal year.
- **Scenarios:** Bull / Base / Bear switch in `Model!U2`, scenario table in `Model!AC:AG`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT).
  - Charts.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer.

## Sources (not SEC EDGAR)
Exosens is **not an SEC registrant**. EDGAR holds only the Citibank F-6EF ADR registration (CIK 0002109666, 5-Feb-2026), which contains no financial statements. With the user's agreement, the model is sourced from the **regulator-filed (AMF) documents** published at www.exosens.com/investors/regulatory-information:
- Universal Registration Documents 2025 and 2024 (English versions).
- IPO registration document (July 2024) for the FY2021–23 audited statements.
- Half-year financial reports 2024, 2025 and 2026.
- Results and revenue press releases (H1-24 to 9M-26) and the 17-Sep-2026 guidance raise.
- The monthly share-count notice of 30-Sep-2026.

`filings.csv` lists every document with its URL and the periods it supplies. `fetch.py` downloads them into `$EXENS_SRC` (outside the repo) and converts them to text with `pdftotext -layout`. The period files in `data/` were transcribed from those text files following `EXTRACTION_SCHEMA.md`; there is no automated parser, because the documents are PDFs with varying layouts. Every file lists its source pages and runs the schema's self-checks; any self-check that did not tie, and why, is written in its `notes`. `manual_items.json` holds the guidance, the Q3-2026 trading update, financing terms, the share price and the per-share overrides.

**Network access:** the build environment had to allow `www.exosens.com` (documents) and `live.euronext.com` (share price). `www.info-financiere.fr` stayed unreachable and was not needed.

**Share price:** €56.90, the Euronext Paris close on 30-Oct-2026 (intraday €57.25 on 2-Nov-2026), read from the Euronext quote feed. It is an input at `Model!P` in the valuation block; update it to market.

**Unverified guidance:** all guidance is from outside SEC EDGAR, so it is labelled UNVERIFIED in the workbook: the outlook block of the scenario table, the guidance memo rows, the medium-term target rows and the capex note. That covers the FY26 outlook, the medium-term targets and the capex guidance, which come from company press releases and the URD filed with the AMF as regulated information. Peer multiples in the P/E and beta rationale are labelled as assumptions.

## Columns (fiscal year ends 31 December)
- **C–D FY2021–2022:** annual, from the IPO registration document. FY2021 is the predecessor (Exosens International) full year. Per-share data before the IPO are not comparable.
- **E–M H1/23, H2/23, FY2023 … H1/25, H2/25, FY2025:** half-year columns with FY subtotals, grouped and collapsed like the template's quarters. H2 = FY − H1 for every flow; H2 columns carry the 31-December balance sheet.
- **N H1/26, O H2/26E, P 2026E:** H2/26E = Q3-26 actual + Q4-26E, calibrated to the FY26 guidance.
- **Q–T 2027E–2030E:** scenario forecast.
- **Right of the forecast** (template column − 63): U notes, W–Z CAGRs, AC–AG scenario table.
- **Quarterly revenue and adjusted gross margin** are memo rows inside the half-year columns ("first / second quarter of the half"), as in the RMS / BC builds.

## Basis
- **Policy:** hybrid recast.
  - FY2024 and H1/25 use the continuing-operations figures restated for the Microwave Amplification disposal (closed 31-Dec-2025): URD 2025 and the H1-2026 report.
  - FY2023 and earlier, and H1/24, are as originally reported.
  - H2/24 = FY24 restated − H1/24 as reported. This half is flagged as mixed in the segment block and in the definition row.
- **Segments:** Amplification and Detection & Imaging throughout. The 2024 segment halves use the restated quarterly tables of the FY2025 release. A basis-flag row and a "reported − continuing" memo show the Microwave Amplification difference where the P&L is as reported.
- **Originally reported figures** for restated periods are memo rows: net profit, Adjusted EBITDA, revenue.
- **Per-share data:** at the 7-Jun-2024 IPO, 119.5m preference shares converted and the ordinary shares were reverse-split. FY2022–23 use the restated share basis of URD 2024 (30.39m weighted shares; FY2023 EPS €0.24). Reported EPS before 2025 is after a preferential dividend to A preference shares, which the EPS check deducts.
- **Cash flow:** halves from the H1 statements; H2 = FY − H1. "Other" lines absorb the presentation differences between years: the 2021 predecessor format and the 2023 regrouping in URD 2024.

## Model structure (Model tab)
- **Segment build:** prior-year period × (1 + like-for-like growth + scope & currency effect).
  - The company publishes reported and like-for-like growth only; scope and currency are never split, so they are carried as one effect.
  - Adjusted gross margin by segment is the company's segment measure.
  - Eliminations are a % of gross segment revenue.
- **FY26 outlook calibration (H2/26E):**
  - Revenue: the Q3-26 actual is a blue input. Q4-26E = Q4-25 × (1 + Q3-26 growth + a uniform Δ), with Δ solved in closed form so FY26 revenue = the guidance end-point (€558 / 564 / 570m).
  - Adjusted EBITDA: H2/26E = the guidance end-point (€186 / 189 / 192m) − H1-26.
  - Capex ~9% and capitalised R&D ~3% of revenue, as guided.
- **Future-M&A lever:** spend (scenario; Base €60m p.a.) ÷ 2.5x EV/revenue gives acquired revenue, 70% to D&I, with a mid-year convention. Intangibles are 40% of consideration over 10 years, with a deferred-tax liability; goodwill is the residual.
- **IFRS P&L from the margin build:** EBITDA = Adjusted EBITDA − share-based payments − one-offs. Operating expenses before D&A are implied (revenue − EBITDA); the by-nature lines are history only. D&A excl. PPA is a % of revenue. PPA amortisation comes from the intangibles schedule. Cost of net debt comes from the debt schedule, on opening balances.
- **IFRS → adjusted bridges** (checks vs published in every reported period):
  1. **Net profit → operating profit → EBITDA → Adjusted EBITDA → Adjusted EBIT:** company definition. FY2021–22 and the 2023 halves have one combined "other adjustments" line, because the split is not published.
  2. **Operating profit → Adjusted EBIT:** company items, i.e. other income & expenses, share-based payments, one-offs, PPA amortisation and the H1-26 brand impairment.
  3. **Net profit → net profit excl. PPA amortisation & impairment → adjusted EPS:**
     - The tax effect is derived from the published figure: the company adds back PPA gross, and the H1-26 brand-impairment DTL reversal is netted.
     - Exosens publishes no adjusted EPS; the model divides the company measure by diluted shares.
- **Other schedules:**
  - Cash flow and dividends: 20–25% payout, paid the following year.
  - Share schedule (no buyback programme), balance sheet and working capital (days of revenue at year-end levels).
  - Intangibles: capitalised R&D in, amortisation and PPA out.
  - PP&E roll-forward and IFRS 16 lease schedule.
  - Debt: €250m Term Loan B bullet (Jun-2029, issue-cost accretion, refinanced at maturity). RCF (€200m) / EIB (€140m) drawn to a €60m minimum cash, with a headroom memo. Other loans amortise.
  - Ratios and valuation.
- **DCF basis:**
  - NOPAT on Adjusted EBIT less share-based payments and one-offs (= operating profit + PPA amortisation + impairment), at a 26% tax rate. D&A add-back excludes PPA amortisation.
  - UFCF deducts capex incl. capitalised R&D, M&A spend (explicit years only) and lease principal; lease liabilities are excluded from net debt.
  - 2026E is shown but excluded from the PV sum and the sensitivity grid, because YE2026 net debt is deducted.
  - Euro cash flows; French OAT risk-free rate.

## Key forecast assumptions (Base)
- **Like-for-like growth:** Amplification 12% → 9% and D&I 12% → 10% over 2027–30E. The company's medium-term target is organic growth "up to mid-teens".
- **Margins:** adjusted gross margin of 51.5% for Amplification and 47% for D&I, held at the 9M-26 level. Adjusted EBITDA margin rises from 34.0% to 35.0%; the company guides a "mild progressive improvement".
- **Capex:** 7% of revenue in 2027E, then 5%, plus capitalised R&D of 3%. The company says normalised capex is ~5% after the 2027 completion.
- **Below the operating line:**
  - D&A excl. PPA is 5.0% of revenue and share-based payments 1.2%.
  - The tax rate is 26%; the French loss carry-forwards were used up in 2026.
  - The dividend payout is 25%, with no buybacks.
- **Market inputs** (assumptions): WACC 8.9% (OAT 3.4%, ERP 5.5%, beta 1.2, D/V 15%), terminal growth 2.5%, fade 9% → 4%. P/E is 24x Base, 30x Bull and 16x Bear on the adjusted measure.

## Data corrections and known differences
- **No company figure was overridden.**
- **Per-share overrides** in `manual_items.json`: the FY2022–23 share counts and EPS use the restated share basis, and FY2022 D&A excl. PPA = bridge D&A 20.5 − printed PPA amortisation 7.4.
- **Cash adjustments:** the 31-Dec-24 and 30-Jun-25 BS-cash vs cash-flow-cash differences are accrued interest receivable and overdrafts, taken from the cash notes.
- **H1-24 bridge:** the H1-2024 report prints only a top-down EBITDA bridge. Share-based payments, non-recurring costs and D&A excl. PPA for H1/24 come from the H1-2025 report's comparative column.
- **Net debt:** the company nets derivatives and accrued interest receivable. The check tolerates ±€1.0m from 2024; the pre-IPO definition (2021–23) is not checked.
- **Rounding tolerances:** check rows on the €m-to-one-decimal tables tolerate ±0.25. H2 = FY − H1 compounds two roundings. The Adjusted EBIT route via PPA amortisation tolerates ±0.45, because H1 PPA amortisation is as printed in the releases while FY PPA is implied by the bridge.

## Rebuild
1. Install the tools: `pip install openpyxl`, plus LibreOffice Calc for recalculation and `pdftotext` (poppler-utils) for the source text.
2. Refresh the data (only needed for new documents; `data/` is committed):
   1. Run `export EXENS_SRC=/path/to/src`.
   2. Run `python3 fetch.py`, then transcribe new periods into `data/<period>.json` per `EXTRACTION_SCHEMA.md` and add the release KPIs to `data/releases.json`.
   3. `python3 check_data.py` runs the statement-arithmetic, segment, bridge, half-year-sum, cash, balance-sheet, EPS and quarter-memo checks. Known exceptions: none.
3. Build: `python3 build.py --snap --recalc` writes `../EXENS_Model.xlsx`. It reruns with the switch on Bull and Bear to fill the snapshot panels, then stores the calculated values and restores the comment authors that LibreOffice resets. Set `XLSX_RECALC` to a LibreOffice recalculation script; the default is the xlsx skill's `recalc.py`.
4. Validate:
   - `python3 ../tools/inspect_model.py ../EXENS_Model.xlsx` should show 0 error cells and 0 non-zero check rows.
   - `python3 ../tools/cyc.py ../EXENS_Model.xlsx` should show 0 cycles.
   - `python3 ../tools/residue_scan.py ../EXENS_Model.xlsx --extra ONON 32.00` should show 0 residue hits.
   - Intentional blanks: FY2021 per-share data, because they were not published on a comparable basis, and the H1/23 balance sheet, because no 30-Jun-2023 balance sheet was published.

## Files
- `fw.py`: column map (half-year columns), style cloning from the MLM template archetype rows, row registry. `rows.py` is the row lookup for inspection scripts.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, snapshots and stored values.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts, re-injects the template chart XML and restores comment authors.
- `filings.csv`, `fetch.py`: source index and downloader / text converter.
- `EXTRACTION_SCHEMA.md`, `data/*.json`, `data/releases.json`, `manual_items.json`: extraction contract, period data, release KPIs and manual items.
- `normalize.py`: basis rules (hybrid recast), flat model keys, H2 = FY − H1, quarterly memo rows, restated 2024 segment halves.
- `check_data.py`: data consistency checks.
