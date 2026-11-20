# BCO model build kit

`models/BCO_Model.xlsx` is The Brink's Company (NYSE: BCO) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD build kit:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CF2`, scenario table in `Model!CN:CR`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT).
  - Charts: organic vs acquisition / currency growth, adjusted EBITDA and operating profit, returns (window 2011–2030E, so every series has data in every year).
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (calendar fiscal year)
The column map is identical to the template (no shift).
- **C–I FY2006–2012:** annual. FY2006–07 are income-statement-only columns (see Basis).
- **J–BV Q1/13–Q4/25 with FY subtotals:** grouped and collapsed like the template.
- **BW–BY Q1/26–Q3/26:** actual. **BZ Q4/26E, CA 2026E:** forecast, calibrated to the Q4 2026 guidance (third-quarter release, 4-Nov-2026).
- **CB–CE 2027E–2030E:** scenario forecast, including NCR Atleos from the assumed closing (4-Jan-2027).
- **Right of the forecast:** CF notes, CH–CK CAGRs (5Y fwd '25–'30, 5Y, 10Y, 19Y), CN–CR scenario table.

## Basis
- **Policy:** statements as originally reported. Values are the XBRL company facts **as first filed** for each period in a 10-K / 10-Q (checked against the face-statement identities and the release tables).
- **Hybrid recast, 2013–Q3/14:** Brink's re-presented those quarters for discontinued operations at year end. Where the year-end release table differs from the first-filed quarter, the model takes the comparative filed in the following year's 10-Q, which ties to the release tables. Each recast cell carries a comment with the originally reported revenue and operating profit.
- **FY2006–08:** continuing operations from the FY2008 10-K, the first after the Brink's Home Security spin-off (31-Oct-2008; BAX Global was sold in 2006). FY2006–07 carry the income statement, segments and D&A only: the balance sheets and cash flows of those years include Home Security. The balance sheet starts at 31-Dec-2008. Pre-SFAS 160 minority interest is re-presented as noncontrolling interests.
- **Segments as reported per year** (non-GAAP basis from 2014; each year from its own fourth-quarter release):
  - 2019+: North America, Latin America, Europe, Rest of World (2019 as recast in the fourth-quarter 2020 release). This is the operating build.
  - 2017–18: North America, South America, Rest of World (memo).
  - 2014–16: Largest 5 Markets (U.S., France, Mexico, Brazil, Canada), Global Markets, Payment Services (memo).
  - 2006–13: International and North America, GAAP segment profit (memo).
  - Q1–Q3/25 Europe and Rest of World are as re-presented in the fourth-quarter 2025 release (about $20m a quarter moved to Europe); the growth-decomposition rows stay as first published.
- **Non-GAAP figures:** as presented in each year's fourth-quarter release. 2009–12 annual figures are as first published; later re-presentations are quoted in cell comments.
- **Per-share data:** no stock splits. Q4 weighted shares = 4 × FY − Σ Q1–Q3.
- **Cash flow:** quarters derived from year-to-date (Q4 = FY − 9M). Cash in the cash-flow statement is cash and cash equivalents to 2017 and includes restricted cash from 2018 (ASU 2016-18).

## Model structure (Model tab)
- **Operating build:** four segments. Revenue = prior-year period × (1 + organic + acquisitions / dispositions + currency), using the company's growth tables (segment detail from Q4/20; totals from 2015). Segment operating profit = revenue × segment margin. Corporate expenses are a separate line. Σ segments + corporate = non-GAAP operating profit.
- **NCR Atleos block (pending acquisition, behind a toggle):**
  - Terms: $30.00 cash + 0.1574 Brink's shares per NCR Atleos share; closing expected early January 2027 (the 4-Jan-2027 date is an assumption).
  - Standalone path: NCR Atleos management projections from the 424B3, with revenue and margin levers.
  - Synergies: the company's $200m run-rate target; yearly phasing is an assumption.
  - Purchase accounting: preliminary allocation from the 424B3 pro forma ($2,895m of intangibles, $296m a year of amortization, deferred-tax unwind). Goodwill is recomputed at the model share price.
  - Financing: $2,276m bridge / permanent debt, $1,468m of NCR Atleos facilities refinanced, the rest of its debt assumed.
  - Assumptions that are not disclosed and are flagged in the notes: integration costs, the 9.5% rate on the NCR Atleos notes, NCR Atleos capex including capitalized software.
- **Future M&A lever:** not used; the NCR Atleos block replaces it.
- **Q4 2026 guidance calibration:**
  - Revenue: one uniform Δ on segment organic growth solves Q4/26E revenues to $1,415m / $1,390m / $1,365m.
  - Margin: one uniform Δ on segment margins solves Q4/26E adjusted EBITDA to $295m / $285m / $275m.
  - Free cash flow: the Q4 working-capital line is solved so that 2026E free cash flow before dividends = 45% / 42.5% / 40% of adjusted EBITDA (2026 framework), with the offset in other current liabilities.
  - Information rows, not forced: Q4 non-GAAP EPS guidance ($2.45–2.80; Base model $2.57), the margin-expansion framework, and Brink's Standalone Projections from the 424B3.
- **GAAP P&L from the build:** GAAP operating profit = non-GAAP operating profit − other items not allocated to segments. Cost of revenues is the implied line. Interest is calculated on opening debt. GAAP tax = non-GAAP tax (27.2% rate) − tax effect of the adjusting items.
- **GAAP → non-GAAP bridges** (checks vs published in every reported period):
  1. **Operating profit → non-GAAP operating profit:** company items grouped as restructuring; acquisitions and dispositions; Argentina highly inflationary; Venezuela; transformation / NCR Atleos costs; retirement plans; other. Company labels and amounts per period are in cell comments. 2009–14 carry the total only.
  2. **Net income → EBITDA → adjusted EBITDA:** company definition from 2018. In 2016–17 the company built adjusted EBITDA from non-GAAP income, so the items row is derived from the published total. Before 2016 it is a model measure.
  3. **Income from continuing operations → non-GAAP income → non-GAAP EPS:** the non-operating, tax and NCI effects are derived as published non-GAAP income − GAAP income − operating items; the company's per-share items are in cell comments. In GAAP-loss periods the share count is the one implied by published non-GAAP income ÷ EPS (commented).
- **Other schedules:** cash flow; buybacks; balance sheet; working capital; NCR Atleos purchase accounting; debt (scheduled notes with maturities refinanced; revolver, term loans and acquisition facilities as one prepayable pool drawn or repaid to a minimum cash balance); leverage-threshold buybacks (2.5x / 2.0x / 1.5x); ratios and valuation.
- **DCF basis:**
  - NOPAT on non-GAAP operating profit (after depreciation and share-based compensation, before acquisition amortization) less cash adjusting costs; D&A add-back excludes acquisition amortization.
  - Net debt is taken at 31-Dec-2026, so the 2026E cash flow is excluded from the present-value sum.
  - NCR Atleos: cash consideration in 2027E UFCF, debt and pension assumed in the EV bridge, consideration shares in the share count.
  - Pension and retiree liabilities are treated as debt-like. Restricted cash is not netted.
  - Market inputs (risk-free 4.25%, ERP 5%, beta 1.3) are assumptions: market data sources are not reachable from the build environment.

## Key forecast assumptions (Base)
- **Organic growth 2027E–30E:** North America 3.0–3.5%, Latin America 4.0–4.5%, Europe 3.0%, Rest of World 9% → 6% (assumptions citing 9M 2026).
- **Segment margins:** North America 15.4% → 16.5%, Latin America 18.0% → 18.5%, Europe 15.0% → 16.0%, Rest of World 25.0%; corporate 2.9% of legacy revenues.
- **NCR Atleos:** management projections (revenue $4,607m → $4,774m; adjusted EBITDA $974m → $1,050m); synergies 25% / 60% / 90% / 100% of $200m; integration costs $150m / $100m / $50m (assumption).
- **Other drivers:** non-GAAP tax rate 27.2% (company estimate for 2026); capex 3.5% of revenues; DPS +5% a year; buyback pricing with 15% a year share-price appreciation (assumption).
- **Share price $114.00:** provided by the user on 20-Nov-2026. It is not an SEC-filed price; update it at `Model!CA` in the valuation block. EDGAR reference points: $125.12 average repurchase price in 9M 2026 (Q3-26 10-Q), $104.79 close on 21-May-2026 (424B3).

## Guidance and verification status
- The Q4 2026 guidance, the 2026 non-GAAP framework and the 27.2% tax-rate estimate are in the 8-K earnings release on EDGAR (verified).
- The NCR Atleos terms, pro forma figures, synergy target, leverage target and both sets of management projections are from EDGAR filings (424B3 and the deal 8-K). The projections are labelled "not guidance" in the workbook.
- No guidance from outside EDGAR (calls, transcripts) is used.

## Data corrections
- None. Known data exceptions (documented, not corrected; `check_data.py` lists them):
  - Q2/16: the six-month cash-flow statement opens $16.4m below the balance the Q1/16 statement implies. The model shows it on its own memo line.
  - Q4/18: Q4 shares are derived in a GAAP-loss year, so model EPS differs from the reported figure by $0.04 (inside the ±$0.05 Q4 tolerance).
  - Q1–Q3/25 Europe and Rest of World growth tables are on the pre-re-presentation basis.
  - Q1/19: the release was filed without tables, so that quarter's growth decomposition (and the FY2019 total) is blank.
  - FY2014 XBRL: the noncontrolling-interest fact has the wrong sign; NCI is taken as net income including NCI − net income attributable.
- Not extracted (blank, not estimated): AMS / DRS revenue mix and growth (release narrative only); quarterly amortization of acquisition intangibles before 2026; company-defined net debt.

## Sources
SEC EDGAR only (CIK 78890; The Pittston Company to May-2003):
- Forms 10-K / 10-Q FY2008–Q3 2026 (XBRL company facts; FY2008 10-K text for 2006–08).
- Form 8-K earnings releases (Ex. 99.1), Q4 2009 – Q3 2026.
- NCR Atleos: deal 8-K of 26-Feb-2026, joint proxy statement / prospectus (424B3, 27-May-2026), NCR Atleos XBRL company facts (CIK 1974138).
- Q3-26 10-Q for debt, repurchases and the cover share count; FY2025 10-K for the amortization schedule.

The investor-relations site (investors.brinks.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR. `filings.csv` indexes the filings, and each `data/<period>.json` lists its source URLs. `hand.json` holds the FY2006–12 annual items typed from the 10-Ks and releases. `manual_items.json` holds the guidance, the NCR Atleos terms, pro forma and projections, debt facts, the buyback data, the amortization schedule and the share price, each with its source. `data/_xbrl.json` is the subset of XBRL facts the extraction uses.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export BCO_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`.
   3. `python3 check_data.py` runs 1,844 checks (statement arithmetic, segment sums, bridges, quarter sums, growth tables, cash and balance-sheet tie-outs). Known exceptions: the eight listed above.
3. Build: `python3 build.py --snap --recalc` writes `../BCO_Model.xlsx`, reruns with the switch on Bull and Bear to fill the snapshot panels, and stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../BCO_Model.xlsx` → 0 error cells, 0 non-zero check rows.
   - `python3 ../tools/cyc.py ../BCO_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../BCO_Model.xlsx --extra WWD Woodward 382.17` → 0 residue hits.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `h2t.py`, `make_index.py`, `fetch.py`: EDGAR HTML → text, filings index, downloads.
- `parse_release.py`: release parser for the quarterly tables (rows of 1Q–4Q + full year for two years).
- `extract.py`: per-period extraction (XBRL statements, release segment / non-GAAP tables, growth tables, free cash flow).
- `xbrl.py`: XBRL company-facts helper (first-filed values; `filed_from` for recast comparatives).
- `normalize.py`: basis rules, flat model keys, discrete quarterly cash flow, item categories.
- `check_data.py`: data consistency checks.
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
