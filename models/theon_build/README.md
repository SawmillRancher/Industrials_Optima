# THEON model build kit

`models/THEON_Model.xlsx` is the Theon International Plc (Euronext Amsterdam: THEON) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`. The scripts started from the ONON kit (IFRS, non-USD, recent IPO) and were rewritten for Theon.
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link;
  - red = definition-flag text.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped and collapsed, at 70% zoom.
- **Scenarios:** Bull / Base / Bear switch in `Model!AC2`, scenario table in `Model!AK:AO`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT).
  - Charts.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Sourcing (read first)
Theon is **not an SEC registrant**. EDGAR holds one CIK for it, 0002095508, used only for Schedule 13G filings on its Kopin stake, and no financial statements. The user accepted regulator-filed documents in lieu of EDGAR for a foreign issuer (2-Nov-2026). The history therefore comes from Theon's own regulated reports and releases on `media.theon.com`. Guidance and deal terms from those releases are labelled **unverified (not on EDGAR)** in the workbook. Header row 3 says so.

## Columns (fiscal year ends 31 December)
- **C–D FY2021–2022:** annual. FY2021 is the P&L as first reported (AR2021). FY2022 and the 31-Dec-2021 / 31-Dec-2022 balance sheets are the restated figures in AR2023 (correction of errors, note 37).
- **E–S Q1/23–Q4/25 with FY subtotals:** grouped and collapsed like the template. 2023 quarters come from the comparatives in the 2024 Q1 / H1 / 9M documents; quarter-end balance sheets start at Q1-24 (2023 quarter ends were not published).
- **T–U Q1/26–Q2/26; V–W Q3/26E–Q4/26E; X 2026E:** forecast quarters calibrated to the FY26 outlook.
- **Y–AB 2027E–2030E:** scenario forecast.
- **Right of the forecast** (template column − 55): AC notes, AE–AH CAGRs (5Y fwd, 4Y, 3Y, 2Y), AK–AO scenario table.

## Basis
- **Policy:** as originally reported, except FY2022 (restated in AR2023) and the FY2021 balance sheet (AR2023 opening balance sheet). Each later comparative is kept in `data/<period>.json` under `cmp`.
- **Share of profit of equity-accounted investees:** from Q2-25 (effective 1-Jan-2025, 2024 restated) Theon presents the share of profit of core associates inside operating profit, adjusted EBIT and EBITDA. The model shows it as its own line inside operating profit in every period. Earlier documents printed it below operating profit, so the model adds it back. The adjusted-EBIT check compares with each period's figure on the definition then in force (definition-flag row).
- **Segments:** one reportable segment (Optronics). Revenue is disaggregated by product (night vision, thermal, and a "platform-based / ISR & other" residual, because the company's minor categories changed between documents) and by geography (memo).
- **Per-share data:** pre-IPO data are not meaningful (200,000 shares to FY2021; split ×100 in Nov-2023 to 20m; 60m before the IPO). IPO 7-Feb-2024 (+10m shares at €10.00). Rights issue Dec-2025 (+8.62m shares at €17.40; 78.62m in issue).
- **Interim frequency:** Theon publishes full statements at H1 and FY and condensed statements in its Q1 and 9M trading updates. Discrete quarters are derived (Q2 = H1 − Q1, Q3 = 9M − H1, Q4 = FY − 9M) for the P&L, APM reconciliation, revenue splits, cash flow and order intake.
- **NCI and shares:** the profit attribution split and weighted shares are printed only in H1 / FY statements, so they sit in the annual columns; quarterly EPS is a memo from the Q1 releases.

## Model structure (Model tab)
- **Revenue build:** night vision, thermal, platform-based / ISR & other. Q3/Q4-26E = prior-year quarter × (1 + 1H/26 y/y + Δ); platform at the Q2-26 run-rate × (1 + Δ), because Kappa is consolidated from 14-Jan-2026. Order intake, soft backlog, options and book-to-bill are KPI rows.
- **Deal blocks** (announced after the Feb-26 guidance, so outside the calibration):
  - **MERIO** (80%, completion underway 29-Oct-2026): revenue and EBIT from the company (>€15m, >€3.5m); Q4-26E stub and price (€37.5m) are **assumptions**.
  - **HGH Systèmes Infrarouges** (100%, EV c.€300m, closing ~1-Jan-2027, toggle): revenue c.€40m; EBITDA margin and synergies **derived** from the stated multiples (mid- to high-teens pre-synergies, c.10x post); PPA split and life are **assumptions**; funded by the €325m term loan.
  - **Future bolt-ons:** spend lever ÷ EV/sales 3.0x at a 20% margin.
- **FY26 outlook calibration:** a uniform growth Δ solves FY26 revenue (guidance basis, excl. MERIO) to €600 / 585 / 570m (closed form via a sensitivity helper row). A uniform margin Δ solves the existing-portfolio adjusted EBIT margin to 26 / 25 / 24% ("mid-twenties"). Both have check rows.
- **IFRS P&L from the build:** operating profit = adjusted EBIT − non-recurring items; opex is the balancing line; finance income = interest only (no fair-value changes forecast); finance costs on opening debt plus the term loan drawn at 1-Jan-2027; tax 23%.
- **Bridges** (checks vs published in every reported period):
  1. **Profit after tax → EBIT → adjusted EBIT → adjusted EBITDA:** company APM; definition flag for the associates change.
  2. **Operating profit → adjusted operating profit:** company items only (non-recurring items).
  3. **Adjusted EPS (model definition):** Theon publishes none; = profit attributable + non-recurring items after tax − fair-value gains on FVTPL stakes (Exosens mark-to-market lifted H1-26 IFRS EPS). Annual columns only (fair-value gains are not disclosed in the Q1 / 9M updates).
- **Other schedules:** cash flow (condensed to the trading-update presentation); debt schedule with cash sweep to minimum cash and leverage-floor buybacks; share schedule; balance sheet with derived "other" lines; working capital at FY2025 year-end days; D&A split; ratios; valuation with non-operating investments deducted.
- **DCF basis:** full-cost adjusted EBIT less non-recurring cash items, × (1 − t), + D&A − capex − acquisitions (explicit years) − ΔWC. 2026E UFCF excluded (in YE2026 net debt). Fade period: capex only and ΔWC scaled to the fading growth rate. Equity bridge deducts net debt less the Exosens / Kopin / associate stakes, plus NCI. Opening IC adds Kappa and MERIO.

## Key forecast assumptions (Base)
- Night vision +15 / 12 / 10 / 8%, thermal +20 / 18 / 15 / 12%, platform +35 / 30 / 25 / 20% (2027E–30E; Bull / Bear Δ in the scenario table).
- Adjusted EBIT margin 25% on the existing portfolio (company: "mid-twenties").
- HGH revenue growth 25 / 22 / 18 / 15%; synergies phased 1/3, 2/3, 100%.
- Bolt-on M&A €50m p.a. from 2028E.
- Capex €30m in 2026E (guided), then 4% of revenue (mid-term target); D&A 2.2% of revenue plus deal D&A.
- Tax 23%; debt cost 5.0%; cash yield 2.0%; minimum cash €75m; payout 30%; buyback floor 1.5x net debt / adjusted EBITDA (assumption).

## Data corrections and known exceptions
- **FY2022:** restated in AR2023 (revenue 147.4 → 142.9; net income 30.6 → 30.0). The model uses the restated figures.
- **Q4-23 D&A −0.03:** FY2023 (1.27) less the 9M-23 comparative (1.30); the two documents are inconsistent. Kept as published.
- **FY2025 Σ quarters ≠ FY published adjusted EBIT by €0.759m:** Q1-25 was published before the associates change. Exempt in `check_data.py`; Q2-25 is derived from the restated Q1-25.
- **H1-26 adjusted EBITDA:** the 27-Jul trading update printed 69.0, the 7-Sep report 69.956. The report is used.
- **Q2-26 acquisitions +€2.9m:** the Q1 condensed and H1 full cash flows classify investment lines differently; the derived quarter is kept as computed.
- **Cash:** the cash-flow statement nets small overdrafts (FY2025 €0.007m; 30-Sep-2025 €1.74m); a memo row reconciles BS and cash-flow cash.

## Sources
Regulated reports and releases of Theon International Plc (`media.theon.com`; full list with URLs in `filings.csv` and `doc_urls.txt`):
- Annual reports FY2021–25 and signed financial statements FY2024–25.
- Semi-annual reports H1-24, H1-25, H1-26.
- Q1 / 9M trading updates 2024–26 (condensed statements).
- Results and trading-update releases; rights-issue and IPO releases; deal releases on theon.com (MERIO, HGH, Exosens, Harder Digital, RCF, AGM).
- EDGAR: Kopin Corp 8-K (16-Oct-2025) and Theon's Schedule 13G / 13G/A on Kopin (CIK 0002095508).

The share price (€29.84 = H1 2026 report market capitalisation €2,346.2m ÷ 78,624,645 shares, 30-Jun-2026) is an input at `Model!X322` in the valuation block. The user gave no price and no SEC-filed price exists; **update it to market**.

## Rebuild
1. Install the tools: `pip install openpyxl lxml`, `poppler-utils` (pdftotext) and LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new documents; `data/` is committed):
   1. `export THEON_SRC=/path/to/src` (outside the repo). The environment must allow `media.theon.com`.
   2. Run `python3 fetch.py && python3 -I extract.py`. New documents need a spec entry (line ranges, column cuts) in `extract.py` `DOCS` and their URL in `doc_urls.txt`.
   3. `python3 check_data.py` runs the statement-arithmetic, quarter-sum, cash, balance-sheet and APM checks. Known exceptions: listed above.
3. Build: `python3 build.py --snap --recalc` writes `../THEON_Model.xlsx`, reruns with the switch on Bull and Bear to fill the snapshot panels, and stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../THEON_Model.xlsx` → 0 error cells and 0 non-zero check rows.
   - `python3 ../tools/cyc.py ../THEON_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../THEON_Model.xlsx --extra ONON "On Holding" 32.00 CHF "Class A"` → 0 residue hits.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, header, snapshots, value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts, replaces template text and comments, re-injects the template chart XML.
- `fetch.py`, `parse_stmt.py`, `extract.py`: download and pdftotext conversion, statement-line parser (side-by-side layouts, both thousand separators), per-document extraction.
- `normalize.py`: basis rules, discrete quarters, definition-consistent APM differencing, flat model keys.
- `check_data.py`: data consistency checks. `manual_items.json`: KPIs, guidance, deals, capital events, share price. `doc_urls.txt`, `filings.csv`: document index.
- `inspect_model.py`, `cyc.py`: copies of the shared QA tools.
