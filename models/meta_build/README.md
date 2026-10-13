# META model build kit

`models/META_Model.xlsx` is the Meta Platforms, Inc. (NASDAQ: META) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, starting from the WWD build kit:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link;
  - red italic = definition flags.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CD2`, scenario table in `Model!CL:CP`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). 2026E is the base year (net debt at 31-Dec-2026E), the explicit years are 2027E–2031E and the fade years 2032E–2036E.
  - Charts: advertising vs other-revenue contribution to growth, adjusted EBITDA (model) and operating income, returns.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (fiscal year ends 31 December)
- **C–F FY2009–FY2012:** annual, as originally reported. FY2009–11 come from the IPO prospectus (424B4, 18-May-2012), which has no 31-Dec-2009 balance sheet; FY2012 comes from the Q4-2012 release.
- **G–BS Q1/13–Q4/25 with FY subtotals; BT–BU Q1/26–Q2/26:** grouped and collapsed like the template.
- **BV–BW Q3/26E–Q4/26E, BX 2026E:** forecast. Q3/26E is calibrated to the Q3 revenue guidance, and 2H/26E to the FY26 total-expense guidance (Q2-26 release, 29-Jul-2026).
- **BY–CC 2027E–2031E:** scenario forecast (one year more than the template's 2027E–2030E, so the DCF has five explicit years).
- **Right of the forecast** (template column − 2): CD notes, CF–CI CAGRs ('26–'31, '20–'25, '15–'25, '09–'25), CL–CP scenario table.

## Basis
- **Policy:** as originally reported, from each period's own earnings release (FY2009–11 from the prospectus).
- **Re-presentations not recast** (cell comments):
  - **FY2011:** marketing & sales / G&A reclassified in the FY2012 release ($427m / $280m as first reported → $393m / $314m).
  - **ASU 2016-09:** early-adopted in the Q4-2016 release with effect from 1-Jan-2016. The FY2016 column is on the new basis ($934m lower provision); Q1–Q3 2016 stay as first reported, so Σ quarters ≠ year.
  - **ASU 2016-18:** restricted cash is in the cash-flow statement from 2018. A restricted-cash memo row reconciles balance-sheet cash to cash-flow cash.
  - **FY2018:** $65m reclassified between operating cash flow and capex in the year column.
- **Segments:** Family of Apps / Reality Labs were first presented in the Q4-2021 release, which recast FY2019–20, Q4-2020 and the 2021 quarters. Earlier periods have total non-advertising revenue only.
- **Per-share data:** no stock splits. Class A and Class B carry the same economics (same EPS); shares are A + B.
  - Pre-IPO (FY2009–11) EPS uses the two-class method, from the prospectus EPS note: basic = A + B shares; diluted = Class A with Class B converted and participating-securities income reallocated.
  - A reallocation row makes NI ÷ diluted shares reproduce the published EPS.
  - Participating-securities income (preferred, unvested awards) is deducted through 2013.
- **Cash flow:** every release has three-month cash-flow statements, so quarters are as published (no year-to-date derivation).

## Model structure (Model tab)
- **Operating build:**
  - **Advertising** = prior-year period × (1 + ad impressions growth) × (1 + average-price-per-ad growth).
    - The KPIs come from the releases from Q4-2021, and before that from 10-Q / 10-K MD&A ("number of ads delivered", price per ad).
    - They are published as whole percentages, so an "implied vs reported" residual row shows the rounding (not a check).
  - **Other revenue:** FoA other revenue (WhatsApp business messaging, Meta Verified) and Reality Labs, each on its own growth.
  - **Segment results:** FoA income = consolidated income from operations − Reality Labs result (Reality Labs loss is a scenario lever).
  - **KPIs:** DAP / MAP, Facebook DAUs / MAUs to Q4-2023, revenue per DAP, headcount.
  - **Memo:** revenue by geography (customer billing address; Q4 = year − nine months).
- **Future M&A lever:** spend → goodwill and intangibles (25% intangibles, 5-year life); no acquired revenue assumed.
- **2026 outlook calibration:**
  1. A uniform Δ on price-per-ad growth (impressions held at the Q2/26 y/y rate) solves Q3/26E revenue to the guidance end-point ($64 / 62.5 / 61bn). The Δ is carried into Q4/26E, which has no guide.
  2. Other operating costs (cash; excluding D&A, SBC and one-offs) are the balancing driver, so FY26 total costs = the expense guidance end-point (Bull $165bn, Base $167bn, Bear $169bn).
  - **Point estimates (all cases):** capex $137.5bn incl. finance leases (guidance mid-point), tax 16% (guided 15–17%), D&A +7% q/q, SBC at the Q2 level.
  - **Information rows (not forced):** "operating income above 2025" and capex vs guidance.
- **GAAP P&L from the build:** total costs = D&A (PP&E roll-forward × depreciation rate) + share-based compensation (% of revenue) + other operating costs + one-offs. Cost lines follow the 1H/26 mix. Interest income is earned on opening cash and marketable securities; interest expense is charged on opening debt, net of capitalized interest.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **Income from operations → adjusted income from operations:** company non-GAAP IPO–Q4 2016 (excl. SBC and payroll tax; amortization from Q3-2014), checked against all 21 published figures. From 2017 a model definition: GAAP + company-quantified one-offs (FTC 2019, restructuring Q3-22–Q4-23, legal Q2-23, Q4-24 release, Q2-26 legal and severance). A current-definition memo series (SBC expensed) drives valuation.
  2. **Net income → EBIT → EBITDA → adjusted EBITDA:** model definitions (Meta publishes no EBITDA); SBC is expensed, with a memo excluding SBC for peer comparison.
  3. **Net income → adjusted net income → adjusted EPS:**
     - Company non-GAAP IPO–2016, including the participating-securities add-back and non-GAAP shares.
     - 2017+: one-offs plus the discrete tax items the company quantified (Tax Act Q4-17, Altera Q2-19, R&D election Q3-20, OBBBA valuation allowance Q3-25, Notice 2026-7 release Q1-26).
     - Checked against every "excluding" EPS the company stated (Q4-17, FY17, Q1-19, Q2-19, Q3-20, Q4-22, Q3-25, Q1-26).
     - Tax effects are derived from those figures; the FTC accruals are non-deductible (company statement); otherwise the tax effect is imputed at the period ETR bounded 15–40% (comments).
  4. **Free cash flow** (company definition in force, flagged): CFO − purchases of P&E (− P&E acquired under capital leases 2013–14; − finance-lease principal from 2019; net of P&E proceeds 2022–23). Checked against all 66 published figures.
- **Other schedules:**
  - Cash flow; buybacks; balance sheet; working capital (DSO; payables % of capex; accrued % of revenue).
  - Debt: notes repaid at maturity and refinanced; a commercial-paper / incremental-notes plug to a $15bn minimum cash balance (labelled financing assumption).
  - Leverage-capped buybacks (net debt / adjusted EBITDA ceiling 0.5x / 0.25x / 0.0x).
  - Ratios and valuation.
- **DCF basis:**
  - NOPAT on adjusted EBIT (current definition, full-cost, SBC expensed) less the cash one-off items.
  - UFCF after capex incl. finance-lease principal and M&A.
  - Leases are excluded from net debt.
  - Net debt includes marketable securities as cash; non-marketable equity investments are not added back (conservative).
  - Market inputs (risk-free 4.25%, ERP 5%, beta 1.20) are assumptions: Treasury / FRED data are not reachable from the build environment.

## Key forecast assumptions (Base; all assumptions unless stated)
- **Ad impressions** 10% → 6% and **price per ad** 8% → 4% a year (2027E–31E). This gives advertising growth of 19% → 10% (1H/26: impressions +19% / +14%, price +12%).
- **FoA other revenue** +40% → +15%; **Reality Labs revenue** +10% a year; **Reality Labs loss** $20.0bn → $17.0bn (FY25 $19.2bn).
- **Other operating costs:** 41% → 38% of revenue (FY25 39.1%, 2026E ~43%).
- **SBC:** 11.5% → 10.5% of revenue. **Taxes on net share settlement:** 90% of SBC (FY25 ratio).
- **Capex** (purchases of P&E) 46% → 23% of revenue, plus $4bn a year of finance-lease principal. **D&A rate:** 11.0–11.5% of opening net PP&E + ½ capex (FY25 11.8%).
- **Tax** 16–16.5%. **DPS** +5% a year from $2.10. **Net shares issued** under equity plans 30m a year. **M&A** $1bn a year.
- **Share price $745.00, per the user (12-Oct-2026)**; update it at `Model!BX` in the valuation block.

## Data corrections
- None. Known data exceptions (documented in `check_data.py`, not corrected):
  - FY2016: ASU 2016-09 basis (above).
  - FY2014: the non-GAAP year figure applies the Q3-2014 amortization exclusion to the full year (−$82m vs Σ quarters).
  - FY2018: $65m CFO / capex reclassification.
  - FY2013: $8m D&A difference between the year column and the quarters as first reported.
  - ±$2m cash-flow rounding in 2018–19.
- One-off items: only those the company quantified are adjusted. The Q2-2024 State of Texas settlement charge was named but not quantified, so it is left in.

## Sources
SEC EDGAR only (CIK 0001326801; Facebook, Inc. until 28-Oct-2021):
- IPO prospectus (424B4, 18-May-2012): FY2009–11 statements, advertising revenue, the EPS note.
- Forms 10-K / 10-Q, Q2-2012 – Q2-2026:
  - ad impressions and price per ad (MD&A, 2014–21);
  - revenue by geography (2018+);
  - Class A + B shares outstanding (balance-sheet caption);
  - debt note and maturities;
  - the interest income / expense table (Q1/Q2-26).
- Form 8-K earnings releases (Ex. 99.1), Q2-2012 – Q2-2026: statements, segment information, non-GAAP and FCF reconciliations, KPIs, one-off items, CFO outlook (guidance).
- Notes-issue 8-Ks: Aug-2022, May-2023, Aug-2024, Nov-2025, May-2026.
- XBRL company facts: revenue / operating income / net income / EPS / CFO / total assets cross-checks; interest income and expense (annual); dividends declared per share.

The investor-relations site (investor.atmeta.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR. All guidance used is from the 8-K releases (verified on EDGAR); no call-transcript or other unverified guidance is used. `filings.csv` indexes the filings, and each `data/<period>.json` lists its source URLs. `data/_xbrl.json` holds the XBRL subset. `manual_items.json` holds:
- the 2026 guidance (with the release text);
- the company-quantified one-off items (wording, amounts, "excluding" EPS and URL);
- the pre-IPO EPS inputs;
- the debt facts and interest table;
- the share price.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export META_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`.
   3. Run `python3 -c "import xbrl; xbrl.dump_subset()"`.
   4. `python3 check_data.py` runs about 1,500 checks: statement arithmetic, segment and geography sums, the company's non-GAAP and FCF reconciliations, EPS, cash and balance-sheet tie-outs, quarters vs years, and XBRL cross-checks. The 19 known exceptions are documented in the script (all quarters-vs-year).
3. Build: `python3 build.py --snap --recalc` writes `../META_Model.xlsx`. It reruns with the switch on Bull and Bear to fill the snapshot panels, then stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../META_Model.xlsx` → 0 error cells, 0 non-zero check rows.
   - `python3 ../tools/cyc.py ../META_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../META_Model.xlsx --extra WWD Woodward 382.17 Aerospace` → 0 residue hits.
   - Intentional exceptions: none on the Model tab (the DuPont identity row is not a check). FY2009 has no balance sheet, so its balance-sheet, ratio and returns cells are blank.

## Files
- `fw.py`: column map (two estimate quarters, 2026E base, 2027E–31E), style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification (the historical tax-effect and FCF formulas are chosen per column from what the company published).
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts (dates moved one year for the 2026E base year) and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`: EDGAR filings index, downloads, HTML → text.
- `parse_release.py`: release parser. It identifies tables by title and resolves columns from the year header, whatever the order (prior-year-first to 2016, current-first after) and footnote markers.
- `extract.py`: per-period extraction (statements, segments, non-GAAP and FCF, KPIs; 424B4; 10-Q / 10-K impressions and price per ad, geography, shares).
- `xbrl.py`: XBRL company-facts helper.
- `normalize.py`: basis rules, flat model keys, one-off items, pre-IPO EPS, Q4 geography.
- `check_data.py`: data consistency checks.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
