# BAH model build kit

`models/BAH_Model.xlsx` is the Booz Allen Hamilton Holding Corporation (NYSE: BAH) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`. The scripts are adapted from the STE kit, which has the same 31-March fiscal year and column layout, and use the WWD finishing steps (cached values, residue scan).
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped and collapsed.
- **Scenarios:** Bull / Base / Bear switch in `Model!AU2`, scenario table in `Model!BC:BG`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). Discount dates are moved to the 31-March fiscal year ends.
  - Charts: revenue-growth contribution (National Security vs Civil & Commercial, Ultra and other), adjusted EBITDA and operating income, returns.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (fiscal year ends 31 March; 2027 = Apr-2026 – Mar-2027)
- **C–L FY2012–FY2021:** annual, as originally reported (fourth-quarter release, fiscal-year column).
- **M–AK Q1/22–Q4/26 with FY subtotals; AL Q1/27:** quarterly actuals, grouped and collapsed like the template.
- **AM–AO Q2/27E–Q4/27E, AP 2027E:** forecast, calibrated to the FY27 guidance.
- **AQ–AT 2028E–2031E:** scenario forecast.
- **Right of the forecast** (template column − 37): AU notes, AW–AZ CAGRs (5Y fwd '26–'31, 5Y, 10Y, 14Y), BC–BG scenario table.

## Basis
- **Policy:** as originally reported, from each period's own earnings release (8-K Item 2.02, Ex. 99.1). Releases are in USD thousands to Q3 FY2025 and USD millions from Q4 FY2025; check tolerances are ±0.15 before and ±0.6 from Q4 FY2025 (stated in the check labels).
- **One reportable segment.** Revenue by customer type comes from the 10-Q / 10-K revenue note:
  - Defense / Intelligence / Civil / Global Commercial (FY2017–FY2024).
  - Global Commercial inside Civil from FY2025; Civil and Commercial as one type in the FY2026 10-K.
  - National Security (Defense + Intelligence) and Civil & Commercial from Q1 FY2027.
  - The model builds on National Security and Civil & Commercial, with the legacy four types as memo rows and a Σ check.
  - FY2017–18 come from the FY2019 10-K comparatives, which are on the ASC 606 full-retrospective basis ($5,809.5m / $6,167.6m vs $5,804.3m / $6,171.9m as originally reported). A derived "outside the customer split" row absorbs that difference and the FY2012–16 years with no split.
- **Presentation changes (cell comments):**
  - Q4 FY2025: "interest expense, net" (interest income moved from other income). The FY2025 annual column is on the new basis, Q1–Q3 FY25 on the old, so FY2025 interest / other income / G&A are exempt from the quarters-vs-year check.
  - FY2022 (and Q3–Q4 FY22): the company's EBITDA and adjusted net income bridges start from consolidated net income. An explicit non-controlling-interest row carries the $0.1–0.2m difference.
- **Per-share data:** Class A common stock; no splits since the Nov-2010 IPO. Diluted EPS uses the two-class method: earnings for diluted EPS = net income attributable − earnings allocated to participating securities (XBRL `UndistributedEarningsDiluted`, as first filed; Q4 = FY − 9M). Adjusted EPS = adjusted net income ÷ diluted shares (the company makes no two-class adjustment).
- **Shares:** weighted basic and diluted from XBRL (as first filed). Q4 diluted comes from the release non-GAAP exhibit; Q4 basic = 4 × FY − (Q1+Q2+Q3). Q1 FY22 basic is not in the company facts and is left blank.
- **Cash flow:** quarters derived from year to date (Q4 = FY − 9M). Quarterly deferred taxes come from XBRL because the quarterly releases fold them into working capital.

## Model structure (Model tab)
- **Operating build:** National Security and Civil & Commercial revenue = prior-year period × (1 + growth); Ultra Mission Solutions in its own block; future M&A lever. Adjusted EBITDA = legacy revenue × legacy margin + Ultra + M&A.
- **KPIs:**
  - Backlog roll-forward: net bookings = Δ backlog + revenue (company definition), book-to-bill 1.0x in Q2–Q4/27E, scenario book-to-bill from 2028E.
  - Funded / unfunded / priced options.
  - Headcount and revenue ex-billables per customer-staff head.
  - Contract-type mix.
- **Acquisition blocks:**
  - Defy Security (6-Apr-2026, $235m) is inside Q1/27 actuals. Its provisional PPA from the Q1 FY27 10-Q is in the schedules.
  - Ultra I&C Mission Solutions closed 24-Aug-2026 for $720m (38 of 91 days in Q2/27).
  - Ultra's revenue is **not disclosed**. The $180m run-rate (~4x EV/sales) is a flagged assumption. The 25% adjusted EBITDA margin rests on the company's "well above 20%"; growth on its "strong double-digit rate for the next several years".
  - Ultra's PPA (40% intangibles over 10 years, no net working capital) is an assumption to replace with the Q2 FY27 10-Q.
- **Future M&A lever:** spend ÷ 2.0x EV/sales, 12% margin, 35% intangibles amortized over 8 years (Defy precedent).
- **FY27 guidance calibration (Q2–Q4/27E):**
  - **Revenue:** one uniform Δ on the Q1/27 y/y growth of both customer types, solved so FY27 legacy revenue = $11.7bn / $11.45bn / $11.2bn (Bull / Base / Bear).
  - **Margin:** one uniform Δ on the adjusted EBITDA margin (prior-year quarter + Q1 drift), solved to legacy adjusted EBITDA of $1,290m / $1,265m / $1,240m.
  - **Free cash flow:** FY2027E payables & accrued % (one working-capital plug, closed form) solved so FCF = $925m / $875m / $825m.
  - **Information rows (not forced):** adjusted EPS (guided $6.00–6.35; Base model $6.40 incl. Ultra) and diluted shares (118–120m; Base 119.9m).
  - **Ultra basis:** the guidance was issued before the Ultra agreement and reiterated before the close without saying whether it includes Ultra. The model assumes it excludes Ultra.
- **GAAP P&L from the build:**
  - Operating income = adjusted EBITDA − D&A − operating adjusting items.
  - Cost of revenue and billable expenses are % of revenue. G&A is the implied balancing line.
  - Interest: FY27 point estimate, then rates on opening notes and term loans, the opening revolver and opening cash.
  - Tax: 21.5% for Q2–Q4/27E (guidance 20–23%), then 22.5%.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **Operating income → adjusted operating income:** company measure, published FY2012 – Q3 FY2025. It covers operating items plus Carlyle-acquisition amortization (to FY2017) or significant acquisition amortization (from FY2022). From Q4 FY2025 it is a model continuation (flagged).
  2. **Net income → EBITDA → adjusted EBITDA:** company definition. Operating items in the releases include:
     - Carlyle option expense (FY2012–15);
     - transaction / acquisition & divestiture costs, "other corporate expenses";
     - restructuring;
     - COVID-19 benefits;
     - financing transaction costs;
     - legal matter reserve, claimed-costs provision, DC tax assessment and insurance recoveries.

     The bridge continues to adjusted EBITA (before acquisition amortization) and full-cost adjusted EBIT.
  3. **Net income → adjusted net income → adjusted EPS:** operating items + acquisition amortization + non-operating items (debt-cost amortization / extinguishment, gains), tax effect as published, and discrete tax items.
     - Assumed tax rate on items: 40% to Q2 FY2018, 36.5% for Q3–Q4 FY2018, 26% from FY2019.
     - Forecast items are taxed at 26%.
- **Other schedules:**
  - Cash flow, buybacks, balance sheet and working capital (revenue basis; no inventories).
  - Debt: Term Loan A-1 repaid from the Aug-2026 notes; A-2 amortization; 2028 / 2029 / 2030 notes and the A-2 balloon refinanced; revolver to a $400m minimum cash with a headroom memo vs the $1.5bn commitment.
  - Leverage-target buybacks from 2028E: net debt / adjusted EBITDA 3.25x / 3.0x / 2.5x (assumption; no target in the filings).
  - Ratios and valuation.
- **DCF basis:**
  - NOPAT = (adjusted EBITA − acquisition, restructuring, legal and financing costs) × (1 − 22.5%), plus depreciation & other amortization. Stock-based compensation is already expensed.
  - Valuation net debt is at the FY2027E year end, after the Ultra payment, so the FY2027E UFCF is excluded from the PV and the explicit years are FY2028E–31E.
  - Operating leases are treated as operating costs.
  - Market inputs (risk-free 4.25%, ERP 5%, beta 1.0, terminal growth 2.5%) are assumptions.

## Key forecast assumptions (Base)
- **Revenue growth:** National Security 4% (FY28) then 5%. Civil & Commercial −4% (FY28), 0%, +2%, +3%. Ultra 15% → 10%. Book-to-bill 1.05x. M&A $150m a year. All assumptions citing FY26 / Q1 FY27 trends.
- **Margins:** legacy adjusted EBITDA margin 11.2% → 11.5% (FY24–26 11.0%).
- **Cost and capital inputs:**
  - Billable expenses 30.5% of revenue; cost of revenue 47.5%.
  - Depreciation & other amortization 1.0%; stock-based compensation 0.65%.
  - Capex: $220m guidance in FY27, then 0.9% of revenue.
  - Acquisition amortization: 10-K schedule ratios on the Q1/27 run-rate + Defy + Ultra.
  - DPS +6% a year from $0.59 a quarter.
- **Share price $75.00:** user-provided, recorded 12-Oct-2026. Q1 FY27 10-Q Part II Item 2 average repurchase prices were $76 (May-2026) and $74 (Jun-2026). Update it at `Model!AP` in the valuation block.
- **Base results:**

  | Item | FY2027E | FY2031E |
  |---|---|---|
  | Revenue | $11,559m | $13,797m |
  | Adjusted EBITDA | $1,292m | $1,628m |
  | Adjusted EPS | $6.40 | $10.45 |
  | Free cash flow | $875m | — |

  - Net leverage 3.0x at the FY2027E year end.
  - DCF $131 per share (WACC 7.8%); Mauboussin $140.
  - Bull / Bear DCF $158 / $98.

## Data corrections
- None. Known data exceptions, documented rather than corrected:
  - FY2017–18 customer revenue is on the ASC 606 recast basis (derived row).
  - Q4 FY2025 interest / other income / G&A re-presentation (quarters-vs-year check exempted).
  - Q1 FY22 basic shares are not in XBRL.

## Sources
SEC EDGAR only (CIK 1443646):
- Forms 10-K / 10-Q FY2011 – Q1 FY2027.
- Form 8-K Item 2.02 earnings releases (Ex. 99.1): Q4 FY2012 – Q4 FY2021 (annual columns) and every quarter Q1 FY2022 – Q1 FY2027. These were in HTML-table format to FY2019 and a PDF-rendered single text block after; `parse_release.py` reads both.
- Deal and financing filings:
  - 8-K 22-Jun-2026 (Ultra agreement, Ex. 99.1);
  - 8-K 24-Aug-2026 (Ultra closing);
  - 8-K 4-Aug-2026 (5.375% 2030 / 5.900% 2034 notes);
  - 424B2 30-Jul-2026 (use of proceeds, as-adjusted capitalization).
- XBRL company facts: weighted shares, two-class earnings for diluted EPS, quarterly deferred taxes and stock-based compensation, shares outstanding, and cross-checks (revenue, operating income, net income, diluted EPS, CFO, total assets).

The investor-relations site (investors.boozallen.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR.
- `filings.csv` indexes the filings.
- Each `data/<period>.json` lists its source URLs; `data/_releases.json` indexes the releases and `data/_xbrl.json` holds the XBRL subset.
- `manual_items.json` holds the FY27 guidance (and FY26 guidance history), the deals, debt facts, the amortization schedule, the buyback authorization, the dividend and the share price, each with its source.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export BAH_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`. `extract.py` expects the XBRL company facts at `$BAH_SRC/cf_1443646.json` (`fetch.py` downloads them).
   3. `python3 check_data.py` runs 1,084 checks: statement arithmetic; the three company bridges vs published; two-class EPS; FCF; customer and backlog sums; cash and balance-sheet tie-outs; quarters vs years; XBRL cross-checks. The known exceptions above are exempted in the code with comments.
3. Build: `python3 build.py --snap --recalc` writes `../BAH_Model.xlsx`, reruns with the switch on Bull and Bear to fill the snapshot panels, and stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py <recalculated file>` → 0 error cells, 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../BAH_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../BAH_Model.xlsx --extra STE STERIS 211.07 WWD Woodward 382.17` → 0 residue hits.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry, period-dependent check tolerance.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`: EDGAR filings index, downloads, HTML → text.
- `parse_release.py`: release tokenizer for both release formats (label + numbers entries by exhibit section).
- `extract.py`: per-period extraction (statements, non-GAAP bridges with item categories, operating data, customers, XBRL shares).
- `xbrl.py`: XBRL company-facts helper (31-March fiscal year).
- `normalize.py`: basis rules, flat model keys, discrete quarterly cash flow, NCI start-line differences.
- `check_data.py`: data consistency checks.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
