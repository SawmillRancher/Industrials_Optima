# HWM model build kit

`models/HWM_Model.xlsx` is the Howmet Aerospace Inc. (NYSE: HWM) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD build kit:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!AQ2`, scenario table in `Model!AY:BC`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). The 2026E unlevered free cash flow is excluded by the flag in row 28, because net debt is taken at the end of 2026E.
  - Charts: segment contribution to sales growth, Adjusted EBITDA / operating income, returns (2020–2030E).
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (calendar fiscal year)
- **C FY2019:** annual, recast continuing operations (P&L and segments only).
- **D–AG Q1/20–Q4/25 with FY subtotals; AH–AJ Q1/26–Q3/26:** grouped and collapsed like the template.
- **AK Q4/26E, AL 2026E:** forecast, calibrated to the FY26 guidance (Q3 2026 release, 29-Oct-2026).
- **AM–AP 2027E–2030E:** scenario forecast.
- **Right of the forecast** (template column − 41): AQ notes, AS–AV CAGRs (5Y fwd '25–'30, 5Y '20–'25, 3Y '22–'25, 6Y '19–'25), AY–BC scenario table.

## Basis
- **Registrant:** CIK 4281 throughout (Alcoa Inc. to Oct-2016, Arconic Inc. to 31-Mar-2020, then Howmet Aerospace Inc.).
- **History window:** the model starts with the post-separation company. Arconic Corporation (rolled products) was spun off on 1-Apr-2020; earlier filings report a different, much larger group (FY2019 sales $14.2bn vs $7.1bn for Howmet).
- **Policy:** each period as originally reported in its own earnings release, with these exceptions (each one commented in the workbook):
  - **FY2019 and Q1/20** are the recast continuing-operations comparatives (Q4-20 and Q1-21 releases). They carry the P&L, segments, end markets and adjusted measures only.
  - **Balance sheet** starts at 30-Jun-2020, the first post-separation balance sheet. The 31-Dec-2020 balance sheet follows the 2020 Form 10-K, which differs from the release by $3m.
  - **Cash flow:** Q1/20 and FY2020 include Arconic Corporation for the first quarter, because the company never segregated it. H1-20 is taken as revised in Q3-20 (prior-year column of the Q2-21 release), so the 2020 quarters are on one classification.
  - **Segment Adjusted EBITDA** became the segment measure in Q1-22. 2021 comes from the company's recast (2022 release panels). 2019–2020 = segment operating profit + segment D&A, the identity behind that recast (it reproduces every 2021 figure).
  - **Q1-26 segment realignment** (a titanium alloy location moved from Engine Products to Engineered Structures): the company recast FY2024 and the 2025 quarters. The model uses the recast for the 2025 quarters and FY2025 (all four quarters recast; originals in cell comments). FY2024 stays as reported, with the recast figures in memo rows; 2024 quarters were never recast. FY2025 y/y for those two segments therefore compares bases that differ by ~$64m of sales.
- **End markets:** from the Form 10-Q / 10-K revenue note (Q4 = year − nine months). The commercial / defense aerospace split starts in Q3-20; Q1/20, Q2/20 and FY2019 come from the following year's comparatives. "Gas turbines" for the 2025 quarters is on the FY2025 10-K basis, from the 2026 10-Q comparatives.
- **Per-share data:** no stock splits in the period. FY2019 and FY2020 diluted EPS = continuing + discontinued per-share lines (the full-year statements print no total). Dividends per share are derived as dividends paid ÷ basic shares.
- **Cash flow:** quarters derived from year-to-date (Q4 = FY − 9M).

## Model structure (Model tab)
- **Segment build:** Engine Products, Fastening Systems, Engineered Structures, Forged Wheels. Third-party sales × Segment Adjusted EBITDA margin, less adjusted corporate expense (Σ segments − consolidated Adjusted EBITDA) = Adjusted EBITDA. Company organic growth and acquisition sales are memo rows (published from Q1-26).
- **End-market memo:** commercial aerospace, defense aerospace, commercial transportation, industrial and other (of which gas turbines), with a Σ check.
- **Deals inside the build:** CAM (closed 6-Apr-2026, $1,812m) and Brunner (6-Feb-2026, $120m) are in Fastening Systems actuals; the Savannah disk forging facility (sold 31-Mar-2026, $230m, $93m gain) left Engineered Structures. The combined preliminary PPA is in the Q2/26 column with a check row. The FY26 guidance already includes all three.
- **Future M&A lever:** spend ÷ EV/sales (3.7x, CAM), 22% EBITDA margin, PP&E / intangibles / goodwill split from the CAM PPA, 15-year amortization. Base spend is nil.
- **FY26 guidance calibration (Q4/26E):**
  - Sales: one uniform Δ on the Q3/26 y/y growth of every segment, solved so FY26 sales = $10,310m / $10,300m / $10,290m.
  - Margins: one uniform Δ on the Q3/26 segment margins, solved so FY26 Adjusted EBITDA = $3,335m / $3,330m / $3,325m.
  - Information rows, not forced: adjusted EPS ($5.49–5.51), free cash flow ($1.95–2.05bn), Q4 revenue ($2.74–2.76bn), FY2027 revenue (~$11.5bn).
  - Base result: adjusted EPS $5.50 (guided $5.50), free cash flow $2,085m (guided $2,000m), FY2027E sales $11,468m.
- **GAAP P&L from the build:** operating income = Adjusted EBITDA − D&A − special items. Cost of goods sold is implied. Interest on opening notes and commercial paper; tax at 20% in Q4/26E, then 21%.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **Operating income → adjusted operating income → Adjusted EBITDA:** company definition. Adjusted operating income was not published Q1/22–Q2/23, and Adjusted EBITDA is missing from some 2019–21 schedules; the definition row flags each.
  2. **Income from continuing operations → EBITDA → Adjusted EBITDA:** EBITDA is a model definition (the company publishes Adjusted EBITDA only); it ties to bridge 1.
  3. **Income from continuing operations → adjusted net income → adjusted EPS:** company definition. The tax line is derived as published adjusted net income − GAAP − pre-tax special items; the company's labels are in the cell comments.
- **Other schedules:** cash flow; buybacks; balance sheet; working capital; PPA; debt (notes repaid at maturity, refinancing by input, commercial paper to a $500m minimum cash, headroom memo vs the $1.0bn program); leverage-target buybacks from 2027E (1.25x / 1.0x / 0.75x); ratios and valuation.
- **DCF basis:** NOPAT on adjusted EBIT, full-cost (Howmet does not add back acquired-intangible amortization or stock-based compensation), with total D&A added back. Net debt at the end of 2026E; 2026E UFCF excluded. No leases, pension deficit or receivables program in net debt (stated on the tab). Market inputs (risk-free 4.25%, ERP 5%, beta 1.10) are assumptions.

## Key forecast assumptions (Base)
- **Segment sales growth 2027E–30E:** Engine Products 14% → 8%; Fastening Systems 12% (CAM annualisation) → 6%; Engineered Structures 3% (Savannah) → 4%; Forged Wheels 6% → 3%. 2027E is set against the company's ~$11.5bn outlook.
- **Segment margins:** Engine Products 39.5% → 41.0%; Fastening Systems 30.0% → 32.0%; Engineered Structures 24.0% → 25.0%; Forged Wheels 27.0% → 28.0%. Adjusted corporate expense 1.1% of sales.
- **Other drivers (assumptions unless stated):** capex 5.0% of sales falling to 4.0% (the release expects elevated spending beyond 2027); D&A ~3.5% of sales; amortization ~$60m a year (legacy per the 10-K plus CAM over an assumed 15 years); tax 21%; DPS +15% a year; no special items; no M&A.
- **Share price $220.00:** provided by the user on 20-Nov-2026. It is an input at `Model!AL` in the valuation block; update it to market. For reference, the latest SEC-filed price is $251.49, the average paid for shares repurchased in September 2026 (Q3-26 10-Q Part II Item 2).
- **Guidance:** only the SEC-filed release of 29-Oct-2026 is used. Nothing from conference calls or other sources outside EDGAR is in the model; any such figure added later should be marked unverified.

## Data corrections
Both are in `manual_items.json` and commented in the workbook.
- **Q2/21:** the release showed interest expense of $89m, including a $23m loss on debt redemption. The company shows that loss on its own line from Q4-21, so the model uses $66m and $23m (Q1-22 release panel). Quarters then sum to FY2021.
- **Q4/20 and FY2020 balance sheet:** deferred income taxes $272m, total assets $11,443m and total equity $3,577m per the 2020 Form 10-K; the release showed $275m / $11,446m / $3,580m.

Known data exceptions (documented, not corrected):
- FY2019 EPS: per-share amounts were computed independently for continuing and discontinued operations, so the checks allow ±$0.02 for that year.
- Q2/20: $6m of special items is recorded in D&A, so adjusted operating income + D&A exceeds Adjusted EBITDA by $6m (memo row).
- Releases are in whole USD millions; arithmetic checks allow ±2.

## Sources
SEC EDGAR only (CIK 0000004281):
- Forms 10-K / 10-Q FY2020–Q3 2026 (end-market note, PPA, debt, repurchase table).
- Form 8-K Item 2.02 earnings releases (Ex. 99.1), Q2 2020 – Q3 2026.
- Deal and financing 8-Ks: CAM announcement (22-Dec-2025), completion (6-Apr-2026), notes offering (3-Mar-2026).
- XBRL company facts: cross-check of sales, operating income, net income, EPS, operating cash flow, total assets and cash (190 checks).

The investor-relations site (howmet.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR. `filings.csv` indexes the filings, and each `data/<period>.json` lists its source URLs; `data/_releases.json` indexes the releases and `data/_xbrl.json` holds the XBRL subset. `manual_items.json` holds the guidance, deals and PPA, debt facts, the buyback authorization, dividends, the share price and the two corrections, each with its source.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export HWM_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`.
   3. `python3 check_data.py` runs 924 checks: statement arithmetic, segment and end-market sums, adjusted bridges vs published, EPS, cash and balance-sheet tie-outs, quarters vs years, and the XBRL cross-check. All pass.
3. Build: `python3 build.py --snap --recalc` writes `../HWM_Model.xlsx`, reruns with the switch on Bull and Bear to fill the snapshot panels, and stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../HWM_Model.xlsx` → 0 error cells, 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../HWM_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../HWM_Model.xlsx --extra WWD Woodward 382.17` → 0 residue hits.
   - `python3 review.py <recalculated.xlsx>` prints the key rows for a sanity check.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, cell comments, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`: EDGAR filings index, downloads, HTML → text.
- `parse_release.py`: splits a release into its schedules and reads rows by label.
- `extract.py`: per-period extraction (statements, segment panels, special items, adjusted measures, organic growth, end markets, cash flow, balance sheet).
- `xbrl.py`: XBRL company-facts helper.
- `normalize.py`: basis rules, corrections, flat model keys, discrete quarterly cash flow.
- `check_data.py`: data consistency checks.
- `review.py`: prints key rows of a recalculated workbook.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
