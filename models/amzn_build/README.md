# AMZN model build kit

`models/AMZN_Model.xlsx` is the Amazon.com, Inc. (NASDAQ: AMZN) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD build kit (pipeline) and the DHR kit (template column layout, other-sheet wiring):
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped and collapsed, opening on 2019, 70% zoom.
- **Scenarios:** Bull / Base / Bear switch in `Model!CF2`, scenario table in `Model!CN:CR`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT).
  - Charts: total vs AWS net-sales growth, adjusted EBITDA / operating income, returns.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (fiscal year ends 31 December; the template's own column map, no re-basing)
- **C–I FY2006–2012:** annual, as originally reported.
- **J–BV Q1/13–Q4/25 with FY subtotals; BW–BX Q1/26–Q2/26:** grouped and collapsed like the template.
- **BY–BZ Q3/26E–Q4/26E, CA 2026E:** forecast; Q3 calibrated to the Q3-26 guidance (8-K, 30-Jul-2026), Q4 carries the Q3 Δs (Amazon guides one quarter ahead).
- **CB–CE 2027E–2030E:** scenario forecast.
- **Right of the forecast:** CF notes, CH–CK CAGRs, CN–CR scenario table.

## Basis
- **Policy:** as originally reported, from each period's own earnings release (quarters: three-month columns; FY: the twelve-month columns of the Q4 release). The releases print discrete three-month cash flows, so no year-to-date derivation is needed.
- **Recasts:**
  - **AWS segment:** a segment from Q1-15. FY2013 and Q1–Q4/FY2014 come from the recast in the 8-K Ex. 99.3 of 23-Apr-2015. FY2006–12 and the 2013 quarters stay on the legacy basis (North America incl. AWS, International) in memo rows, with a "not on the current segment basis" row so every period ties.
  - **SBC allocation:** from 2016, stock-based compensation and other operating items are allocated to segments. The 2016 releases restated 2015, so 2015 segment operating income takes the restated comparative (hybrid recast, commented). The 2015 originals are memo rows. FY2013–14 current-basis segment OI stays before SBC, with an "unallocated" row.
  - **Product groups:** online stores, physical stores, third-party seller services, subscription services, advertising services, AWS, other. Each quarter is taken from the latest release that presents it, because Amazon re-presents the groups (advertising split out of "other" in the Q4-21 release, back to Q3-20). Available from Q2-16; FY = Σ quarters.
  - **Legacy supplemental net sales** (Media / Electronics and other general merchandise / Other, 2006–16): memo rows.
- **Per-share data:** 20-for-1 split effective 6-Jun-2022. Share counts in documents filed before that date are multiplied by 20, and per-share figures divided by 20.
- **Debt:** the face balance sheet shows only long-term debt. The current portion (XBRL, 2011+; on the face in 2008) and short-term borrowings (XBRL, 2021+) sit inside "accrued expenses and other", so the model shows them on their own line and accrued excluding debt above it. Finance-lease liabilities (XBRL) are a memo row and are excluded from net debt.
- **Cash:** the cash-flow statement includes restricted cash from 2018 (memo row: CF cash − BS cash).

## Model structure (Model tab)
- **Net sales build:** seven product groups.
  - Q3/Q4-26E retail groups = prior-year quarter × (1 + Q1-26 y/y + Prime Day timing shift + calibration Δ). Q1 is used because the Q2-26 y/y includes Prime Day, which moved from Q3 in 2025 to Q2 in 2026.
  - The −4.0 pp Prime Day shift ("nearly 400 bp", from guidance) applies to online stores, third-party seller services and advertising in Q3 only.
  - AWS = prior-year quarter × (1 + Q2-26 y/y of 36.8%), outside the calibration.
  - 2027E+: scenario growth levers per group.
- **Segments:** North America + International = the retail groups, split by the NA share (prior-year quarter + 1H drift, then held); AWS = the AWS group. Segment OI = net sales × margin.
  - Q3/Q4-26E margin before calibration = prior-year quarter margin, excluding the FTC charge disclosed for NA, + 1H-26 y/y drift.
  - 2027E+: scenario margin levers.
- **Q3-26 calibration:**
  1. A uniform growth Δ on the retail groups solves Q3 net sales to the guidance end-point ($202.0 / 199.5 / 197.0bn).
  2. A uniform segment-margin Δ solves Q3 GAAP operating income to the guidance end-point ($26.5 / 24.5 / 22.5bn). Guidance assumes no energy-derivative remeasurement and no settlements, so the forecast special items are nil.
  3. Q4 (no guidance) carries the growth Δ. Its margin Δ = Q3 Δ − Q3-25 special charges not disclosed by segment ÷ Q3-25 net sales + Q4-25 special charges ÷ Q4-25 net sales, so the solved underlying shift is carried without the one-offs.
  - Base result: Q3 +10.7% y/y and 12.3% operating margin; Q4 +14.3% and 12.7%; 2026E net sales $825.5bn, operating income $106.8bn.
- **Future M&A lever:** acquisitions and strategic investments spend (Base $5bn p.a.), half assumed to buy businesses at 3.0x sales and a 5% margin; 30% intangibles (One Medical 37%).
- **GAAP P&L from the build:**
  - Operating income = adjusted OI (segment build) − special items. Cost of sales is the balancing line; fulfilment, technology and infrastructure, sales and marketing, and G&A are % of net sales.
  - Interest: Q3/Q4 point estimates that include the July and September 2026 notes, then rate × opening debt. Interest income: yield × opening cash and securities.
  - Other income (investment marks) is not forecast. Tax 19%.
- **D&A split:**
  - P&E depreciation (XBRL "Depreciation") = rate × opening PP&E (Q3/Q4: the Q2-26 annualised 14.0%; 2027E+: 13.5% on opening + ½ net additions).
  - Other D&A (operating-lease ROU, capitalized content, other) = % of net sales.
  - The forecast cash flow offsets the other D&A with an explicit "operating-lease payments & content reinvestment" line, so operating-lease assets and liabilities and content assets stay flat and the balance sheet balances.
- **GAAP → adjusted bridges.** Amazon publishes no adjusted operating income, EBITDA or EPS, so these are model definitions:
  1. **Operating income → adjusted operating income:** + special charges Amazon quantified in its release text (Q4-22 $2.7bn; Q1-23 $0.5bn; Q3-25 $4.3bn; Q4-25 $2.44bn) + energy-contract derivative remeasurements (10-Q: Q1-26 −$48m, Q2-26 −$551m). Checked against the company-published "operating income without these charges" (Q3-25 $21.7bn, Q4-25 $27.4bn; ±$50m, as published to $0.1bn).
  2. **Net income → EBITDA → adjusted EBITDA:** EBITDA = operating income + total D&A as presented (includes operating-lease amortization from 2019); + special items. A memo row shows EBITDA after other D&A (≈ after rent).
  3. **Net income → adjusted net income → adjusted EPS:** − other income (expense), net (Rivian marks 2021–24, Anthropic gains 2025–26, FX) − equity-method activity + special items, tax-effected at the statutory 35% to 2017 and 21% from 2018.
  4. **Free cash flow** (company definition): CFO − purchases of P&E net of proceeds from sales and incentives. TTM checked against every published figure; the lease-adjusted variant (published Q4-14–Q4-24) is checked from Q3-15. Quarters whose release restated prior-year quarters carry an explicit basis-difference row, commented: Q1–Q3/17 ASU 2016-09 excess tax benefits; Q1–Q3/18 ASU 2016-15 / 2016-18.
- **Other schedules:** cash flow; buybacks; balance sheet; working capital (year-end days); debt; leverage-target buybacks; ratios; valuation.
  - Debt: notes repaid at maturity and refinanced; commercial paper / revolver to a $50bn minimum cash; headroom memo vs $30bn CP + $20bn revolvers.
  - Leverage-target buybacks, 2027E+: net debt / adjusted EBITDA of 0.25x / 0.0x / −0.25x.
- **DCF basis:**
  - NOPAT = (adjusted operating income − cash special charges) × (1 − 19%). Stock-based compensation is already expensed.
  - Only P&E depreciation is added back. UFCF deducts net capex, acquisitions and finance-lease principal (leases are excluded from net debt).
  - 2026E UFCF is excluded because net debt is taken at YE2026E. Non-marketable investments (Anthropic) are not added to EV.
  - Market inputs (risk-free 4.25%, ERP 5%, beta 1.10) are labelled assumptions.

## Key forecast assumptions (Base)
- **Growth 2027E–30E:**

  | Group | 2027E | 2030E | Recent history |
  |---|---|---|---|
  | Online stores | 8.5% | 7% | FY25 +9.0% |
  | Physical stores | 5% | 4% | |
  | Third-party seller services | 11% | 9% | |
  | Subscriptions | 11% | 9% | |
  | Advertising | 19% | 13% | FY25 +22% |
  | AWS | 28% | 17% | Q2-26 +37% |
  | Other | 8% | 6% | |

- **Segment margins:** NA 8.5% → 10.0%; International 4.5% → 6.0%; AWS 36% → 35%.
- **Capex:** gross 23% of net sales in 2027E, falling to 17% (FY2025 18.4%; 1H-26 25.8%).
- **2026E capex:** Q3/Q4 held at the Q2-26 run-rate ($54.2bn), so FY26E is $206.8bn. The ~$200bn figure from the Q4-25 call is **unverified** (not in an EDGAR filing) and is shown only as an information row.
- **Other inputs:** SBC 2.6% of net sales; other D&A 3.2%; tax 19%; M&A $5bn p.a.; deferred taxes $6bn p.a.; finance-lease principal $2bn p.a. (assumptions).
- **Share price:** $260.00, provided by the user on 12-Oct-2026. It is an input at `Model!CA` in the valuation block; update it to market.

## Data corrections
- None. Known, documented data exceptions (not corrected):
  - FY2022 D&A in the Q4-22 release includes the 9M-22 "other operating expense (income), net" ($460m), so Σ quarters is $460m lower.
  - TTM free cash flow in Q1–Q3/17 and Q1–Q3/18 differs from Σ originally reported quarters by the restatements above (basis-difference rows).
  - Q4 three-month XBRL facts are not used for cross-checks (10-K facts are annual).

## Sources
SEC EDGAR only (CIK 0001018724):
- Forms 10-K / 10-Q 2006–Q2-2026.
- Form 8-K Item 2.02 earnings releases (Ex. 99.1): Q4-05 – Q2-26. The 8-K of 23-Apr-2015, Ex. 99.3, gives the AWS segment recast.
- Financing 8-Ks of 2026:
  - notes: 13-Mar, 16-Mar, 12-Jun, 9-Jul, 14-Sep;
  - $17.5bn delayed-draw term loan: 10-Jun (drawdown not disclosed by the build date; not modelled).
- XBRL company facts: current portion of long-term debt, short-term borrowings, finance / capital lease liabilities, P&E depreciation, debt maturities, and cross-checks of revenue, operating income, net income and total assets.

The investor-relations site is blocked from the build environment; its releases are the same documents as filed on EDGAR.
- `filings.csv` indexes the filings, and each `data/<period>.json` lists its source URLs.
- `data/_groups.json` holds the product groups from the latest presenting release; `data/_recast.json` holds the 2015 AWS recast; `data/_xbrl.json` holds the XBRL subset.
- `manual_items.json` holds the Q3-26 guidance, the special charges (verbatim release text), the energy-derivative amounts, debt facts and maturities, the buyback authorization, the unverified capex figure and the share price, each with its source.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export AMZN_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`, then `python3 -c "import xbrl; xbrl.dump_subset()"`.
   3. `python3 check_data.py` runs about 2,000 checks: statement arithmetic, segment / product-group / legacy-segment sums, EPS, cash and balance-sheet tie-outs, published TTM free cash flow, quarters vs years, and XBRL cross-checks. The only known exception is the FY2022 D&A above.
3. Build: `python3 build.py --snap --recalc` writes `../AMZN_Model.xlsx`, reruns with the switch on Bull and Bear to fill the snapshot panels, and stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../AMZN_Model.xlsx` → 0 error cells, 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../AMZN_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../AMZN_Model.xlsx --extra WWD Woodward 382.17 Danaher DHR` → 0 residue hits.
   - `python3 review.py ../AMZN_Model.xlsx [row keys]` prints key rows.

## Files
- `fw.py`: column map (template layout), style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, header, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`: EDGAR filings index, downloads, HTML → text.
- `parse_release.py`: release parser. It identifies tables by content and resolves columns by the year header, because the releases print the prior year first from 2016. It also right-aligns supplemental rows with blank leading cells.
- `extract.py`: per-period extraction (statements, segments, product groups, cash flow, balance sheet, supplemental TTM FCF / shares / ex-F/X growth, prior-year comparatives, the 2015 AWS recast).
- `xbrl.py`: XBRL company-facts helper (calendar fiscal year).
- `normalize.py`: basis rules, flat model keys, split adjustment, special items, FCF basis differences.
- `check_data.py`: data consistency checks. `review.py`: prints key rows of a recalculated workbook.
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
