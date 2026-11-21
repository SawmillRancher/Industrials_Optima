# FDX model build kit

`models/FDX_Model.xlsx` is the FedEx Corporation (NYSE: FDX) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD build kit:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CV2`, scenario table in `Model!DD:DH`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). Calendar 2026E (ending 31-Dec-2026, six weeks after the valuation date) is the base year, so the explicit years are 2027E–2031E and net debt is taken at 31-Dec-2026.
  - Charts: contribution to revenue growth, adjusted EBITDA / operating income, returns (fiscal FY2012–FY2025, then calendar 2026E–2031E).
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Why there are two history bases
On 1-Jun-2026 FedEx did two things at once: it spun off FedEx Freight (80.1% distributed, 19.9% retained) and changed its year end from 31 May to 31 December. It also replaced the Federal Express segment with two new segments, Express U.S. Domestic and Express International.

EDGAR has the go-forward basis (calendar quarters, continuing operations, new segments) only from Q1 2024: the recast exhibits of 21-Jul-2026 and 28-Oct-2026 and the release of 28-Oct-2026. Everything older exists only as fiscal years ended 31 May with FedEx Freight consolidated. Calendar quarters cannot be rebuilt from fiscal quarters without estimating, so the model carries both bases side by side and never mixes them in one growth rate.

## Columns
- **Legacy basis** (fiscal years ended 31 May; FedEx Freight consolidated; as originally reported):
  - **C–I FY2006–FY2012:** annual.
  - **J–CA Q1 FY13–Q4 FY26 with FY subtotals (FY2013–FY2026):** grouped and collapsed like the template.
- **Calendar basis** (years ended 31 December; continuing operations; Express U.S. Domestic / Express International):
  - **CB–CK Q1/24–Q4/25 with 2024 and 2025 totals; CL–CN Q1/26–Q3/26:** actual (recast).
  - **CO Q4/26E, CP 2026E:** forecast, calibrated to the calendar-2026 guidance (release of 28-Oct-2026).
  - **CQ–CU 2027E–2031E:** scenario forecast.
- **Right of the forecast** (template column + 16): CV notes, CX–DA CAGRs (5Y forward '26–'31; historical on fiscal years FY21–26, FY16–26, FY06–26), DD–DH scenario table.

## Basis
- **Policy:** as originally reported, from each period's own earnings release, on both bases.
- **Not recast in the legacy columns** (cell comments where it matters):
  - FY2015 change to mark-to-market pension accounting, adopted in Q4 FY15. Q1–Q3 FY15 stay on the previous basis, so those quarters do not sum to the year.
  - ASU 2017-07 (FY2019): non-service retirement-plan items moved below operating income. FY2015–FY2018 mark-to-market adjustments are an operating expense line.
  - ASC 842 (FY2020): operating lease right-of-use assets and liabilities appear from FY2020.
- **Segments as reported per year** (legacy memo rows with Σ checks): FedEx Express, FedEx Ground, FedEx Freight, FedEx Kinko's (to FY2007), FedEx Services (from FY2008); TNT Express separate in FY2017; Federal Express and FedEx Freight in FY2025–26.
- **Calendar basis:** FedEx Freight is in discontinued operations. The recast exhibits are unaudited and "do not represent a restatement".
- **Per-share data:** no stock splits in the window. FedEx uses the two-class method and prints shares in whole millions, so EPS checks carry a ±$0.10 tolerance. The recast exhibits print no share count; diluted shares for Q1/24–Q2/26 are derived as net income ÷ diluted EPS (cell comments).
- **Cash flow:**
  - Legacy quarters are derived from year-to-date statements (Q4 = FY − nine months).
  - On the calendar basis only nine-month statements exist (2025 and 2026, not recast for discontinued operations). They sit in the Q3/25 and Q3/26 columns with cell comments, and 2026E = nine months + Q4/26E.
- **Balance sheets on the calendar basis:** 31-Dec-2024, 31-Dec-2025 and 30-Sep-2026 only.

## Model structure (Model tab)
- **Operating build:** packages by service: average daily volume × revenue per package × operating days.
  - Express U.S. Domestic: U.S. priority, U.S. deferred, U.S. ground; plus U.S. freight and other revenue.
  - Express International: international priority, economy and domestic; plus international freight and other revenue.
  - A "statistics tie" row shows package revenue ÷ Σ (volume × yield × days) ≈ 1.00.
  - Segment adjusted operating income = segment revenue × adjusted margin (company non-GAAP segment measure).
  - Corporate, other, and eliminations: revenue and an adjusted loss. FedEx Supply Chain (sold 1-Oct-2026) is stripped from Q4/26E with a flagged share assumption, because its revenue is not disclosed.
  - The legacy columns show the same service lines where the releases printed them (definitions changed; see the label comments).
- **Legacy segments memo:** revenue and operating income by segment with Σ checks, and FedEx Freight LTL statistics.
- **Calendar-2026 guidance calibration (Q4/26E):**
  - Revenue: one uniform Δ on the nine-month y/y volume growth of every package service, solved so 2026 revenue = 2025 × (1 + guided growth). Guidance is "~12%"; the scenario uses 12.5% / 12.0% / 11.5% (the ±0.5 pt is a model bound).
  - Margins: one uniform Δ on both adjusted segment margins, solved so 2026 adjusted EPS = $18.60 / $18.30 / $18.00.
  - Information rows, not forced: GAAP EPS guidance ($35.30–35.90) and capital spending ($3.9bn drives Q4 capex).
- **GAAP P&L from the build:** operating income = adjusted operating income − adjusting items. Cost lines follow revenue ratios and "other operating expenses" is the balancing line. Interest is calculated on opening balances; tax at 22.5% in Q4/26E, then 23%.
- **GAAP → adjusted bridges** (checks vs published in every period with a reconciliation table):
  1. **Operating income → adjusted operating income:** company definition; items grouped as realignment / optimization / separation, integration, impairments, legal, mark-to-market (FY2015–18), other. Company labels are in cell comments.
  2. **Income from continuing operations → EBITDA → adjusted EBITDA:** model definition (FedEx publishes no EBITDA in its releases): operating income + D&A, plus operating adjusting items.
  3. **Income from continuing operations → adjusted net income → adjusted EPS:** company definition; operating items, non-operating items (retirement-plan mark-to-market, FedEx Freight stake, debt extinguishment) and the tax column of the company tables.
  - Periods with no reconciliation table (FY2006–FY2011, most quarters before Q2 FY16) show adjusted = GAAP and "n/p" in the check rows.
- **Other schedules:**
  - Cash flow; buybacks; balance sheet; working capital (all ratios on revenue: FedEx has no cost of goods sold).
  - FedEx Supply Chain sale: proceeds, net assets held for sale, and a model gain (see assumptions).
  - Debt: notes repaid at maturity and refinanced; commercial paper to a $4.0bn minimum cash balance, with a headroom memo against the $3.5bn credit agreements.
  - Leverage-target buybacks, 2027E+: net debt / adjusted EBITDA of 1.25x / 1.0x / 0.75x.
  - Ratios and valuation.
- **Net debt definition:** total debt − cash − the retained FedEx Freight stake + IEEPA tariff refunds held for customers ($2.7bn of cash at 30-Sep-2026 belongs to customers). The 37% InPost consortium stake ($2.5bn, equity method) is deducted from EV and invested capital at carrying value.
- **DCF basis:** NOPAT on adjusted operating income less restructuring, integration and legal costs; D&A added back; rent stays an operating cost, so operating leases (~$15bn) are neither debt nor invested capital. The working-capital line excludes the tariff-refund pass-through. Market inputs (risk-free 4.25%, ERP 5%, beta 1.10) are assumptions.

## Key forecast assumptions (Base)
- **Volume and yield 2027E–31E:** U.S. package volume +1.5–2.0% and yield +2.5–3.5%; international volume +1.5% and yield +2.0–2.5% (scenario table; cited against 2025 and nine-month 2026 trends and the 5.9% rate increase of 4-Jan-2027).
- **Adjusted margins:** Express U.S. Domestic 9.0% → 10.0%; Express International 3.4% → 4.5%; corporate loss 0.35% of revenue. These are assumptions. No company target is used.
- **Other drivers:** capex 4.0–4.2% of revenue; D&A 4.0–4.15%; restructuring $300m in 2027E and $150m in 2028E; DPS +5% p.a. from the $1.22 quarterly rate.
- **Flagged assumptions (labelled in the workbook):**
  - FedEx Supply Chain is 50% of corporate & other revenue (not disclosed).
  - Gain on the FedEx Supply Chain sale = $1.4bn proceeds − $264m net assets held for sale, recorded in Q4/26E and adjusted out. The company's outlook table does not list a gain, so model GAAP EPS exceeds the GAAP guidance by about that amount.
  - The retained FedEx Freight stake is sold in 2027E at its 30-Sep-2026 carrying value ($3,254m).
  - The $2.7bn of tariff refunds is still held at year-end 2026 and paid out during 2027.
  - Debt maturities: the FY2026 10-K table is by old fiscal year of maturity; each bucket is repaid in the same-numbered calendar year and refinanced.
- **Guidance and targets:**
  - Calendar-2026 guidance is taken from the 28-Oct-2026 release on EDGAR (verified).
  - The filings mention "calendar 2029 financial performance targets" but no EDGAR exhibit quantifies them. The investor-relations site is not reachable from the build environment, so no 2029 target is used.
- **Share price $300.00:** provided by the user on 20-Nov-2026. SEC-filed reference: $293.07 average price paid for shares repurchased in September 2026 (Form 10-Q, Part II Item 2). It is an input at `Model!CP` in the valuation block; update it to market.

## Data corrections
- **Q3 FY2015 cash flow:** the release prints the nine-month effect of exchange rates on cash as +104. The statement's own arithmetic and the Form 10-Q give (104). The model uses (104) (`manual_items.json`).

Source choices (the 10-K wins over the release):
- **FY2016:** the Q4 FY16 release printed no balance sheet; 31-May-2016 comes from the FY2016 Form 10-K.
- **FY2023:** cash and operating cash flow are $33m higher in the Form 10-K than in the release; the 10-K balance sheet and cash-flow statement are used.
- **FY2025:** total assets are $36m lower in the Form 10-K; the 10-K balance sheet is used.

Known data exceptions (documented, not corrected):
- FY2015 quarters vs year (mark-to-market pension accounting adopted in Q4).
- FY2013 salaries: the year in the Q4 release is $8m below the sum of the quarters as first reported.

## Sources
SEC EDGAR only (CIK 1048911):
- Form 8-K Item 2.02 earnings releases (Ex. 99.1), Q4 FY2006 – Q4 FY2026 (81 releases), and the release for the quarter ended 30-Sep-2026.
- Form 8-K recast exhibits "Supplemental Historical Financial Information" of 21-Jul-2026 and 28-Oct-2026.
- Forms 10-K (FY2008, FY2010, FY2016, FY2023, FY2025, FY2026) and the Form 10-Q for the quarter ended 30-Sep-2026 (debt, held for sale, tariffs, buybacks, shares).
- Form 8-K of 1-Jun-2026 (spin-off completion).
- XBRL company facts for share-based compensation, dividends declared, basic shares and cover-page shares outstanding, and for cross-checks.

The investor-relations site (investors.fedex.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR. `filings.csv` indexes the filings, and each `data/<period>.json` lists its source URLs. `data/_xbrl.json` holds the XBRL subset. `manual_items.json` holds the guidance, deals, debt facts, buybacks, tariff refunds, dividends, the share price and the data correction, each with its source.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export FDX_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`.
   3. `python3 check_data.py` runs 1,690 checks: statement arithmetic, segment sums, non-GAAP bridges vs published, statistics vs revenue, cash and balance-sheet tie-outs, quarters vs years, and XBRL cross-checks. Known exceptions: the two listed above (5 lines).
3. Build: `python3 build.py --snap --recalc` writes `../FDX_Model.xlsx`, reruns with the switch on Bull and Bear to fill the snapshot panels, and stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../FDX_Model.xlsx` should show 0 error cells and 0 non-zero check rows.
   - `python3 ../tools/cyc.py ../FDX_Model.xlsx` should show 0 cycles.
   - `python3 ../tools/residue_scan.py ../FDX_Model.xlsx --extra WWD Woodward 382.17` should show 0 residue hits.

## Files
- `fw.py`: column map for the two bases, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, cell comments, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`: EDGAR filings index, downloads, HTML → text.
- `parse_release.py`: release parser (tables identified from their headings; handles wrapped labels, split negative cells and footnote markers).
- `extract.py`: legacy-basis extraction (every table row as `[group, label, value]`), with Form 10-K fallbacks.
- `extract_cal.py`: calendar-basis extraction from the recast exhibits and the 28-Oct-2026 release.
- `xbrl.py`: XBRL company-facts helper (31-May fiscal periods and date spans).
- `normalize.py`: maps rows to flat model keys on both bases, discrete quarterly cash flow, non-GAAP item categories.
- `check_data.py`: data consistency checks.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
