# FSS model build kit

`models/FSS_Model.xlsx` is the Federal Signal Corporation (NYSE: FSS) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD build kit:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CG2`, scenario table in `Model!CO:CS`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). 2026E is the base year (it ends about two months after the valuation date), so the explicit years are 2027E–2031E and net debt is taken at 31-Dec-2026.
  - Charts: group contribution to sales growth, adjusted EBITDA and operating income, returns.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (calendar fiscal year)
- **C–I FY2006–2012:** annual, as originally reported.
- **J–BV Q1/13–Q4/25 with FY subtotals; BW–BY Q1/26–Q3/26:** grouped and collapsed like the template.
- **BZ Q4/26E, CA 2026E:** forecast, calibrated to the FY26 outlook (Q3-26 release, 29-Oct-2026).
- **CB–CF 2027E–2031E:** scenario forecast.
- **Right of the forecast** (template column + 1, because Q3/26 is an actual and 2031E is added): CG notes, CI–CL CAGRs, CO–CS scenario table.

## Basis
- **Policy:** as originally reported, from each period's own 10-K / 10-Q.
- **Recasts:** one rule. When the following year's 10-Q re-presents a quarter, the quarter takes that restated comparative, so the quarters of a year match its annual column:
  - Q1–Q3/15: Fire Rescue (Bronto) moved to discontinued operations in the FY2015 10-K; the 2016 10-Q comparatives are used (net sales as first reported in the cell comments).
  - 2021 quarters: amortization expense became a separate line in the FY2021 10-K; the 2022 10-Q comparatives give the reclassification out of SEG&A.
- **Discontinued operations as reported per year:** Tool Group (2008), FSTech (2012), Fire Rescue (2015–16) and smaller businesses. Annual columns keep each business until the filing that discontinued it. The "y/y vs the prior-year comparative in this period's filing" row gives like-for-like growth.
- **Groups:** Environmental Solutions (Environmental Products to 2006) and Safety and Security Systems throughout; Fire Rescue (to 2014), Tool (to 2007) and Federal Signal Technologies (2009–2011) as legacy rows inside the totals.
- **Q4:** the fourth-quarter earnings release three-month column (lines it lacks = FY − 9M).
- **Per-share data:** no stock splits in the period; FY2006–2011 basic = diluted shares (10-K note text and EPS tables).
- **Cash flow:** as originally reported, year to date; quarters derived (Q4 = FY − 9M). Where the statements show discontinued cash flows separately (to 2017), the CFO / CFI / CFF lines are the continuing figures and the discontinued flows sit in their own derived line. FY2015 cash-flow cash includes $5.0m held by Fire Rescue (memo line in the cash check).

## Model structure (Model tab)
- **Segment build:** orders = net sales × book-to-bill; backlog = opening + orders − sales; net sales = prior-year period × (1 + growth); segment operating income = sales × margin (as reported: after amortization and the group's acquisition costs); corporate = operating income − Σ groups (derived; checked against the published corporate line to 2023). Segment adjusted EBITDA (published from Q1-17) is a memo.
- **Acquisitions:** Hog (Feb-25), New Way (Nov-25), Kinloch (Dec-25), Mega (Jan-26), Western Technology (Jul-26) are inside the actuals. PPAs for New Way and Hog are in the schedule block. Global Vacuum Systems (~$29m, closed 28-Oct-2026) enters the Q4/26E cash flow and balance sheet with an assumed allocation (PPA not yet published).
- **Future M&A lever:** spend ÷ EV/sales (1.6x), 14% margin after amortization, PP&E / intangibles / goodwill split, 14-year amortization on 70% of intangibles.
- **FY26 outlook calibration (Q4/26E):**
  - Sales: one uniform Δ on the 9M 2026 y/y growth of both groups, solved so FY26 net sales = $2.64bn / $2.625bn / $2.61bn.
  - Margins: one uniform Δ on the segment margins (prior-year quarter + 9M change), solved so FY26 adjusted EPS = $5.32 / $5.26 / $5.20.
  - Information row, not forced: capex guidance ($45–55m).
- **GAAP P&L from the build:** operating income from the segment build; gross profit implied; interest on opening balances; tax 24%.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **Net income → EBITDA → adjusted EBITDA (company):** + interest, other expense / settlement charges, tax, D&A, + the reconciliation's operating items (acquisition & integration, restructuring, purchase accounting excluding the part in D&A, other). Published quarterly from Q1-17 and annually from FY2013; 2014–16 quarters use the adjusted-EPS items (model); 2006–2012 model = EBITDA.
  2. **Operating income → adjusted EBIT (model):** + the same operating items; = adjusted EBITDA − D&A.
  3. **Continuing income → adjusted net income → adjusted EPS (company, from Q1-13):** pre-tax items from the EPS reconciliation (including the purchase-accounting depreciation step-up and pension / debt settlement charges); adjusted tax derived as adjusted pre-tax income + net items − published adjusted net income; 2013 items shown net of tax; Q1–Q3/13 per share only (× diluted shares).
- **Other schedules:** cash flow (rental-fleet investment as its own forecast line); buybacks; balance sheet; working capital; PPAs; debt (term loan $375m held, revolver to a $60m minimum cash, headroom memo vs the $1.1bn commitment); leverage-target buybacks (net debt / adjusted EBITDA 1.0x / 0.75x / 0.5x); ratios and valuation.
- **DCF basis:** NOPAT on full-cost adjusted EBIT less the cash adjusting items; total D&A added back (recent intangibles and goodwill are tax-deductible); capex, rental fleet and M&A deducted in the explicit years; no leases in net debt; no NCI.

## Key forecast assumptions (Base)
- **Growth 2027E–31E:** Environmental Solutions 7.5% → 5.5% (includes GVS and New Way synergies in 2027E); Safety and Security Systems 3% → 4%.
- **Segment margins:** Environmental Solutions 18.5% → 19.5%; Safety and Security Systems 24.5% → 25.0%; corporate 2.3% of sales.
- **Other drivers (assumptions):** D&A 3.7–3.8% of sales; amortization per the 10-Q schedule; capex 1.8% and rental fleet 1.1% of sales; M&A $150m p.a.; tax 24%; DPS +7% p.a.; rates 5.0–5.2% on the credit facility.
- **Share price $114.00:** the weighted average price paid for shares repurchased 30-Aug – 26-Sep-2026 (Q3-26 10-Q Part II Item 2, filed 29-Oct-2026). This is the latest share price in an SEC filing; update it at `Model!CA` in the valuation block.

## Data corrections
- None. Known data exceptions (documented, not corrected):
  - FY2009 and FY2011 XBRL revenue facts were first tagged in the following year's restated comparatives, so the as-first-filed XBRL cross-check is skipped for those two years.
  - FY2015 cash-flow cash includes $5.0m of Fire Rescue cash (memo line); the Q4-16 derivation carries a matching cash-basis line because the 2016 10-Qs start from the balance-sheet cash.
  - The Q3-26 release notes that $1.0m of Q1-26 discontinued-business legal costs were not excluded from Q1-26 adjusted EBITDA and that prior periods will be recast; the model keeps the published figures.

## Sources
SEC EDGAR only (CIK 277509):
- Forms 10-K / 10-Q FY2005–Q3 2026 (primary documents).
- Earnings releases: Federal Signal files them as Ex. 99.1 to each 10-Q / 10-K (only three Item 2.02 8-Ks exist; the FY2008 release is an 8-K exhibit).
- 8-Ks: acquisitions (New Way 25-Sep-2025 deck and 1-Dec-2025 release, Mega 18-Dec-2025 / 16-Jan-2026), credit agreements, investor decks.
- XBRL company facts: stock-based compensation, deferred taxes, dividends declared, shares, and as-first-filed revenue / net income / assets cross-checks.

The investor-relations site is not used; its releases are the same documents as filed on EDGAR. No guidance from outside EDGAR is used: the FY26 outlook comes from the EDGAR-filed releases. `filings.csv` indexes the filings, each `data/<period>.json` lists its source URLs, `data/_docs.json` maps each period to its filing and release, and `data/_xbrl.json` holds the XBRL subset. `manual_items.json` holds the FY26 guidance history, deals and PPAs, the amortization schedule, debt facts, the buyback programs, dividends and the share price, each with its source.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export FSS_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`.
   3. `python3 check_data.py` runs 1,344 checks: statement arithmetic, group sums, corporate vs published, adjusted EBITDA and adjusted EPS bridges vs published, EPS, cash and balance-sheet tie-outs, XBRL cross-checks, and quarters vs years. Known exceptions: the two XBRL years above (skipped by design).
3. Build: `python3 build.py --snap --recalc` writes `../FSS_Model.xlsx`, reruns with the switch on Bull and Bear to fill the snapshot panels, and stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../FSS_Model.xlsx` → 0 error cells and 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../FSS_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../FSS_Model.xlsx --extra WWD Woodward 382.17` → 0 residue hits.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs, compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`: EDGAR filings index, downloads (10-K / 10-Q primary documents and their Ex. 99 releases; 8-K exhibits), HTML → text.
- `parse_fss.py`: table parser. It types tables by content and resolves each column to (months, year) from the header row that carries the years, then re-expresses years relative to the document's fiscal year.
- `extract.py`: per-period extraction from the period's own filing, the next year's filing (restated comparatives) and the releases.
- `xbrl.py`: XBRL company-facts helper.
- `normalize.py`: basis rules, Q4 from the release, flat model keys, discrete quarterly cash flow, adjusting-item categories.
- `check_data.py`: data consistency checks.
- `inspect_model.py`, `cyc.py`: QA tools (copies of `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
