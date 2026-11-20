# NOC model build kit

`models/NOC_Model.xlsx` is the Northrop Grumman Corporation (NYSE: NOC) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD / STE build kits:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CG2`, scenario table in `Model!CO:CS`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). 2026E (the year ends six weeks after the valuation date) is the base year, so the explicit years are 2027E–2031E and net debt is taken at 31-Dec-2026E.
  - Charts: sector contribution to sales growth, adjusted EBITDA / operating income, returns.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (calendar fiscal year)
- **C–I FY2006–FY2012:** annual, as originally reported (FY2006–08 from the Forms 10-K).
- **J–BV Q1/13–Q4/25 with FY subtotals; BW–BY Q1/26–Q3/26:** grouped and collapsed like the template.
- **BZ Q4/26E, CA 2026E:** forecast, calibrated to the 2026 guidance (Q3 2026 release, 20-Oct-2026).
- **CB–CF 2027E–2031E:** scenario forecast.
- **Right of the forecast** (template column + 1, because the model carries five scenario years): CG notes, CI–CL CAGRs (5Y fwd '26–'31, 5Y, 10Y, 19Y), CO–CS scenario table.

## Basis
- **Policy:** as originally reported, from each period's own earnings release (FY2006–08: own Form 10-K), with one exception: Q1–Q3 2018 take the recast of the Q4 2018 release (Schedule 6) for the mark-to-market pension accounting change adopted in Q4 2018, so that the 2018 quarters sum to the year; the as-reported figures are in the cell comments.
- **Restatements kept as memo rows** (not recast): 2008 for the TASC sale (sales $32,315m vs $33,887m), 2010 for the Shipbuilding spin-off (continuing operations $28,143m vs $34,757m), 2017 for ASC 606 / ASU 2017-07 / MTM ($26,004m vs $25,803m).
- **Segments, current four-sector structure** (Aeronautics / Defense / Mission / Space Systems, in force from 1-Jan-2020): each year on one consistent presentation. 2019 as recast in the 2020 releases; 2018 annual from the FY2020 10-K segment note (2018 quarters were never recast and are blank in this block); 2020–22 and 2025–26 as reported; 2024 as recast for the 1-Jan-2025 realignment (SSAS to Aeronautics) in the 2025 releases; 2023 as reported, because the 2024 releases recast only Q3–Q4 for the 1-Jan-2024 Defense / Space realignment (the FY2024 and FY2025 10-K recasts of FY2022–23 are memo rows). Originally reported figures of recast periods are memo rows and cell comments. The reconciliation items (FAS/CAS, unallocated) follow the same presentation as the segments.
- **Legacy segment structures as originally reported** (memo block with Σ checks): 2016–19 Aerospace / Innovation / Mission / Technology Services; 2009–15 Aerospace / Electronic / Information / Shipbuilding / Technical Services; 2006–08 Information & Services / Aerospace / Electronics / Ships (the 2006 "Other" line is derived).
- **Pension presentation:** net total FAS/CAS pension adjustment inside operating income through 2017; service-cost-only FAS/CAS operating adjustment from 2018 (ASU 2017-07), with the non-operating FAS pension benefit and the fourth-quarter MTM below operating income.
- **Adjusted EPS, definition in force per period:** pension-adjusted diluted EPS (Q4 2009 – Q1 2017 releases; continuing-operations basis 2009–12), "EPS excluding the impact of tax reform" (Q4 / FY2017), MTM-adjusted EPS (Q4 2018 onward; 2021 and 2023 from the following year's comparatives; interim quarters carry no MTM, so adjusted = diluted EPS). 2006–08 and Q2–Q3 2017: none published (adjusted = GAAP, flagged).
- **Per-share data:** no stock splits; 2006–07 diluted EPS adds back dividends on the mandatorily redeemable convertible preferred (if-converted method; derived memo row).
- **Cash flow:** quarters derived from year to date (Q4 = FY − 9M). The 2009–15 releases use the direct method, so D&A, stock-based compensation, deferred taxes and retiree-benefit items come from XBRL (as first filed); working capital & other is the derived residual in every period. The 2018–19 cash-flow statements include restricted cash (memo line in the cash check).

## Model structure (Model tab)
- **Segment build:** sales × segment operating margin for the four sectors, less intersegment eliminations (eliminations % of gross segment sales × eliminations margin rate) = segment operating income (company non-GAAP), checked against the published figure in every period. Backlog block: total / funded backlog, net awards (quoted, else implied from the roll-forward), book-to-bill; forecast roll-forward with a book-to-bill lever.
- **Reconciliation to GAAP operating income:** + FAS/CAS operating adjustment (forecast = CAS pension cost − FAS service cost inputs) + unallocated corporate expense (% of sales; intangible amortization and MTM-related deferred state tax as memo components) + gains on sales of businesses / divestiture costs / royalty reversal (history only) + a derived residual, checked against reported operating income.
- **Future M&A lever:** spend ÷ EV/sales (2.0x), 11% margin, PP&E / intangibles / goodwill split, 12-year amortization through unallocated corporate expense.
- **2026 guidance calibration (Q4/26E):**
  - Sales: each sector's Q4 growth is first set from its own sales guidance mid-point ((guided FY − 9M actual) ÷ Q4 2025 − 1), then one uniform Δ (Group block) closes 2026E sales to the consolidated guidance end-point ($43,750 / 44,000 / 44,250m).
  - Segment operating income: each sector's Q4 margin is set from its margin guidance, then one uniform margin Δ closes 2026E segment operating income to $4,940 / 4,990 / 5,040m (the KPI the company guides).
  - Adjusted free cash flow: the 2026E unbilled-receivables balance is solved so that adjusted FCF = $3,100 / 3,300 / 3,500m; the implied days (66) are carried forward.
  - MTM-adjusted EPS ($29.35–29.75) is an information row (model Base $29.67; the Q4 tax rate point estimate of 18% is an assumption chosen so that the result sits inside the range, since the company's tax, FAS/CAS, interest and share-count guidance is not on EDGAR).
  - Base result: Aeronautics $14.1bn at 9.8% (guided ~$14bn / high 9%), Defense $8.7bn at 10.0% (mid-to-high $8bn / ~10%), Mission $12.9bn at 15.4% (high $12bn / mid 15%), Space $11.1bn at 10.2% (~$11bn / low 10%).
- **GAAP P&L from the build:** operating income = segment operating income + FAS/CAS + unallocated; cost of sales is the implied balancing line (G&A % of sales input; product / service mix held). Interest on opening balances; non-operating FAS pension benefit and other, net as inputs; tax rate input; MTM nil.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **Segment operating income (non-GAAP) → operating income:** company reconciliation, as above.
  2. **Net earnings → EBITDA → adjusted EBITDA (model definitions; Northrop Grumman publishes no EBITDA):** adds back only items the company quantified: gains on business sales (2021, 2025) and divestiture costs, the 2008 goodwill impairment, the B-21 loss provisions (Q4 2023 $1,560m, Q1 2025 $477m). Continues to adjusted EBIT after D&A (NOPAT basis).
  3. **Net earnings → adjusted net earnings → adjusted EPS:** definition flags per period (1 = pension-adjusted, 2 = MTM-adjusted, 3 = tax-reform-adjusted 2017, 0 = none); the tax effect is derived from the published figure; forecast adjusted = GAAP (MTM nil).
- **Other schedules:** cash flow (pension & OPB non-cash items reversed and contributions; working capital linked to the balance sheet); buybacks; balance sheet (pension asset accretes by the non-cash FAS income); trade working capital (company definition); debt (notes repaid at maturity per the FY2025 10-K ladder and refinanced; commercial paper / revolver to a $2.0bn minimum cash balance with a headroom memo vs the $3.0bn facility); buybacks = max(minimum programme, plug to a target net debt / adjusted EBITDA); ratios and valuation.
- **DCF basis:** NOPAT on adjusted EBIT (after D&A) less the FAS/CAS operating adjustment (non-cash pension accounting) and divestiture costs; D&A added back; capex and bolt-on M&A in the explicit years; the non-operating FAS pension benefit never enters UFCF and the overfunded pension is not added to equity value. Market inputs (risk-free 4.25%, ERP 5%, beta 0.85) are assumptions (rate sources not reachable from the build environment).

## Key forecast assumptions (Base)
- **Sector sales growth 2027E–31E:** Aeronautics 7% → 4%; Defense 9% → 5% (Sentinel ramp); Mission 5% → 4%; Space 4–5% (scenario table; notes cite 9M 2026 growth and backlog cover).
- **Sector margins:** Aeronautics 10.0% → 10.8%; Defense 10.2% → 10.8%; Mission ~15.3%; Space 10.4% → 10.8%; eliminations 6.0% of gross sales at a 13.5% margin.
- **Pension / corporate:** CAS pension cost $240m and FAS service cost $200m (FAS/CAS operating adjustment +$40m); non-operating FAS pension benefit $650m; unallocated corporate expense 0.6% of sales; contributions $125m (all assumptions anchored on 2025–26 run-rates).
- **Other drivers:** G&A 9.5–9.6% of sales; D&A 3.3–3.5% of sales; capex 3.0–3.2% of sales; tax rate 16%; DPS +8% p.a.; M&A $500m p.a.; minimum buybacks $1.5bn p.a. and a 1.5x net debt / adjusted EBITDA target; maturities refinanced at 4.35–4.60% blended.
- **Share price $555.32:** Form 4 of 2-Nov-2026 (shares withheld at $555.32; open-market sales the same day at $553.39–557.47), the latest share price in an SEC filing (no repurchases in Q3 2026, so the 10-Q carries no average repurchase price). Update it at `Model!CA` in the valuation block.

## Data corrections
- None. Known data exceptions (documented, not corrected):
  - FY2006–08 10-K cash-flow rows that print blank cells cannot be placed by position; rows that could not be resolved across the FY2006–08 filings (acquisitions 2006–08, the 2008 goodwill-impairment line) are left blank and absorbed in the derived "other" lines (noted per record).
  - The 2019 quarters recast on the 2020 structure sum to $3,967m of segment operating income vs $3,978m for the year (company recast; $11m in unallocated).
  - 2016–17 quarterly releases print no backlog figure (blank); 2018 quarters from the release narrative.

## Sources
SEC EDGAR only (CIK 0001133421):
- Forms 10-K FY2006–FY2025 and 10-Q Q1 2013 – Q3 2026.
- Form 8-K Item 2.02 earnings releases (Ex. 99 / 99.1), Q4 2005 – Q3 2026 (84 releases parsed).
- 8-Ks: Orbital ATK (Jun-2018), Form 10-K recasts for the 2016 and 2020 realignments (Items 7 / 8), senior-notes issues.
- XBRL company facts (first-filed values for cross-checks; D&A, stock-based compensation, deferred taxes, shares outstanding, dividends declared, current debt, remaining performance obligations).
- Form 4 (2-Nov-2026) for the share price.

The investor-relations site (northropgrumman.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR. `filings.csv` indexes the filings, each `data/<period>.json` lists its source URLs, and `manual_items.json` holds the 2026 guidance history, share price, debt ladder, amortization schedule, pension facts, deals, realignments and accounting changes, each with its source. Items the company no longer publishes in the release (FAS/CAS, tax rate, interest, share count guidance) are not taken from the earnings call; the Q4/26E point estimates are run-rate assumptions flagged as such.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export NOC_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`.
   3. `python3 check_data.py` runs 1,751 checks: statement arithmetic, XBRL cross-checks, segment sums and the reconciliation to operating income, adjusted-EPS bridges, cash and balance-sheet tie-outs, and quarters vs years. Documented exceptions: the FY2019 recast quarter sum and the FY2018 annual column on the 2020 structure.
3. Build: `python3 build.py --snap --recalc` writes `../NOC_Model.xlsx`, reruns with the switch on Bull and Bear to fill the snapshot panels, and stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../NOC_Model.xlsx` → 0 error cells, 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../NOC_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../NOC_Model.xlsx --extra Woodward WWD 382.17` → 0 residue hits.
   - Intentional exceptions: Charts `#N/A` for years without a balance sheet; the current-structure segment block is blank before 2018 (legacy memo blocks cover 2006–17).

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification; `rows.py` replays it for QA scripts.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`: EDGAR filings index, downloads, HTML → text.
- `parse_release.py`: release parser (layout-aware table reader: segment table, statements, backlog, non-GAAP rows, guidance).
- `extract.py`: per-period extraction (releases, FY2006–08 10-Ks with the cross-filing cash-flow resolver, 10-K segment notes, the Q4 2018 MTM recast schedule, FAS/CAS tables, XBRL extras).
- `xbrl.py`: XBRL company-facts helper (first-filed values).
- `normalize.py`: basis rules, flat model keys, segment presentation choice, discrete quarterly cash flow.
- `check_data.py`: data consistency checks.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
