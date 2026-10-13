# MSFT model build kit

`models/MSFT_Model.xlsx` is the Microsoft Corporation (NASDAQ: MSFT) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD build kit:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped and collapsed.
- **Scenarios:** Bull / Base / Bear switch in `Model!CK2`, scenario table in `Model!CS:CW`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). Discount dates moved to Microsoft's 30-June fiscal year ends; FY2026A (ended 30-Jun-2026) is the base year, so the explicit years are FY2027E–FY2031E and net debt is taken at 30-Jun-2026.
  - Charts: FY27-segment contribution to revenue growth, adjusted EBITDA / operating income, returns.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (fiscal year ends 30 June; 2027 = Jul-2026 – Jun-2027)
- **C–I FY2006–FY2012:** annual, from the 10-Ks (Item 8), as originally reported.
- **J–CA Q1/13–Q4/26 with FY subtotals:** grouped and collapsed like the template; quarters from each earnings release (three-month columns), years from the Q4 release twelve-month columns.
- **CB–CE Q1/27E–Q4/27E, CF 2027E:** forecast; Q1/27E calibrated to the Q1 FY27 outlook, Q2–Q4/27E carry the Q1 calibration.
- **CG–CJ 2028E–2031E:** scenario forecast.
- **Right of the forecast** (template column + 5): CK notes, CM–CP CAGRs (5Y fwd '26–'31, 5Y, 10Y, 20Y), CS–CW scenario table.

## Basis
- **Policy:** as originally reported, from each period's own earnings release (quarters, FY2013+) or 10-K (FY2006–FY2012). Every statement value ties to XBRL company facts (353 comparisons; one documented exception).
- **Restatements not recast** (cell comments): ASC 606 / 842 restatement of FY2016–FY2017 (8-K 3-Aug-2017: FY2017 revenue $89,950m → $96,571m), so FY2018 y/y crosses bases; FY2008 operating income ($22,492m original vs $22,271m in later comparatives).
- **Segments as reported per year:**
  - Main build on the **FY27 structure** — Agents and Infra / Devices and Consumer and eight product & service lines — announced and restated in the 8-K of 2-Sep-2026 (Item 7.01, Ex. 99.1). Restated history exists for Q1 FY25–Q4 FY26 only; earlier periods show consolidated revenue in the segment-build total.
  - Memo blocks, each as originally reported with Σ checks to the consolidated figures: PBP / IC / MPC (+ Corporate and Other, FY2016–FY2018) for FY2016–FY2026; Devices & Consumer / Commercial (revenue and gross margin) for FY2014–FY2015; the five divisions for FY2006–FY2013 (FY2006's seven segments aggregated into the FY2007 divisions).
- **Per-share data:** no stock splits since Feb-2003; one share class.
- **Cash flow:** Microsoft's releases present three-month cash-flow columns, used directly. Q1 FY26 is restated from the Q2 FY26 six-month column ($4,914m of OpenAI equity-method results moved from "Depreciation, amortization, and other" to investment gains; CFO unchanged).

## Model structure (Model tab)
- **Operating build:** eight product & service lines (Azure; Microsoft 365 cloud; productivity & server licensing; industry solutions; frontier & support services; search & advertising; XBOX; Windows OEM & devices) → two segments → segment operating income = revenue × segment margin. Microsoft allocates all costs to segments (no corporate line), so the build equals GAAP operating income.
- **Future M&A lever:** spend ÷ EV/sales (10x), 15% margin after amortization, PP&E / intangibles / goodwill split, 7-year amortization (Base $3bn p.a. from FY2028E).
- **Q1 FY27 outlook calibration** (8-K 2-Sep-2026, which re-files the 29-Jul-2026 call outlook — SEC-filed, so verified):
  - Revenue: one Δ per segment on the Q4/26 y/y growth of its lines, solved so Q1/27E segment revenue = the guidance end-point (Agents and Infra $75.15–75.75bn; Devices and Consumer $14.7–15.2bn; high / mid / low by scenario).
  - Margin: one uniform Δ on both segment margins, solved so Q1/27E operating income = guided revenue − COGS ($29.6–29.8bn) − opex ($16.8–16.9bn); Bull takes the low cost end. Opex lines follow the guided opex growth.
  - Q2–Q4/27E carry the Q1 Δs (the company guides one quarter ahead). Other income ~$(100)m a quarter and a ~20% tax rate are guided for Q1 and held.
  - **Information rows, UNVERIFIED (not filed on EDGAR):** FY27 "double-digit" revenue and operating-income growth from the 29-Jul-2026 call, as reported by third parties. Not used as a solve target.
  - Base result: FY27E revenue $389.1bn (+17%), operating income $180.5bn (+16%), adjusted EPS $19.37.
- **GAAP P&L from the build:** operating income = segment build − adjusting items (nil); gross margin is implied (operating income + opex); other income from Q1 guidance, then interest income on cash & short-term investments − interest on debt − finance-lease interest; tax 20% FY27E, 19% thereafter.
- **GAAP → adjusted bridges** (checks vs published in every reported period; `ngaap.json`):
  1. **GAAP operating income → adjusted operating income** (company "As Adjusted"): revenue deferrals (Windows / Office upgrade offers, pre-sales, Windows 10; FY2012–FY2017), impairment / integration / restructuring / severance (FY2012, FY2015–FY2017, Q2 FY23), European Commission fine (Q3 FY13). Plus an adjusted-revenue memo check.
  2. **Net income → EBIT → EBITDA → adjusted EBITDA:** model definitions (Microsoft publishes no EBITDA); D&A = cash-flow line "Depreciation, amortization, and other".
  3. **Net income → adjusted net income → adjusted EPS:** operating items less their tax effect, discrete tax items (TCJA, intangible-property transfers, India), OpenAI impact (after tax). FY2012–Q1 FY14 were published per share only ($ = per-share × diluted shares, labelled). Definition changes are flagged in the definition rows.
- **Other schedules:** cash flow; buybacks; balance sheet; working capital (DSO, unearned revenue and payables % of revenue at June year-end levels); PPAs (LinkedIn, Nuance, Activision Blizzard); debt (notes repaid at maturity at face, short-term borrowing to a $40bn minimum liquidity); finance leases (additions = 17.5% of capex incl. leases, principal 6.7% of opening liabilities, interest 4.5%); liquidity-target buybacks (cash & short-term investments target $60 / 70 / 80bn by scenario, with a $25 / 20 / 15bn minimum); ratios and valuation.
- **DCF basis:** NOPAT on adjusted operating income (amortization and SBC already expensed); capex in UFCF includes finance-lease assets because finance-lease liabilities are counted in net debt; investment gains / losses (incl. OpenAI) excluded; equity investments (~$36bn, incl. OpenAI) not added back (conservative, memo row). Market inputs (risk-free 4.25%, ERP 5%, beta 1.05) are assumptions.

## Key forecast assumptions (Base)
- **Product-line growth 2028E–31E:** Azure 32% → 17%; Microsoft 365 cloud 14% → 11%; productivity & server licensing −2% → −3%; industry solutions 9% → 8%; frontier & support 4% → 3%; search & advertising 8% → 7%; XBOX 2–3%; Windows OEM & devices 0–1% (scenario table; assumptions citing FY26 trends and the Q1 FY27 outlook).
- **Segment margins:** Agents and Infra 47.0% → 47.5% (FY26 50.9%; depreciation ramp from the capex wave); Devices and Consumer 29.0% → 30.0%.
- **Capex incl. finance leases:** FY27E $200bn (Q1 guidance "over $50 billion" × 4, assumption), then 45% → 32% of revenue; depreciation 17% of opening net PP&E (FY26 16.7%); amortization per the 10-K schedule ($3.1bn FY27).
- **Capital returns:** dividend $1.00 a quarter in FY27E (assumption: +10%; the Sep-2026 declaration is not in the filings reviewed), +10% p.a.; buybacks per the liquidity target.
- **Share price $541:** user-provided (12-Oct-2026); update it at `Model!CA` in the valuation block.

## Data corrections
- Q1 FY26 cash flow: D&A & other $13,061m → $8,147m and investment gains −$1,007m → −$5,921m, restated from the Q2 FY26 six-month statement (`manual_items.json`). CFO unchanged.
- Known data exceptions (documented, not corrected; exempted in `check_data.py`):
  - FY2016 Σ quarters ≠ year: early adoption of ASU 2016-09 in Q4 FY16, effective 1-Jul-2015 ($302m tax; CFO / CFF reclassification); Q1–Q3 FY16 stay as first reported. FY2016 segment figures re-allocated in the Q4 release.
  - Adjusting items that do not sum across quarters as published: Q1 FY14 pre-sales deferral (+$113m; FY2014 annual shows none), Q2 FY15 revenue-deferral re-presentation (−$326m; FY2015 annual shows none), Q2 FY16 "net impact from revenue deferrals" $1,897m vs the FY2016 Windows 10 total.
  - FY2008 operating income vs later XBRL comparatives (see Basis).

## Sources
SEC EDGAR only (CIK 0000789019):
- Forms 10-K FY2006–FY2026 and 10-Q (balance-sheet / note cross-references).
- Form 8-K Item 2.02 earnings releases (Ex. 99.1), Q1 FY2013 – Q4 FY2026 (FY2006–FY2012 releases carry no financial tables; the 10-Ks are used).
- 8-Ks: 2-Sep-2026 (Item 7.01: FY27 segments, restated history, Q1 FY27 outlook); 3-Aug-2017 (ASC 606 / 842 restatement); segment re-presentations of Nov-2013, Oct-2015 and Dec-2024 (memo context).
- XBRL company facts: dividends declared per share, depreciation, amortization of intangibles, finance-lease data, and the cross-check of revenue, operating income, net income, EPS, CFO and total assets.

The investor-relations site (microsoft.com/investor) is blocked from the build environment; its releases are the same documents as filed on EDGAR. `filings.csv` indexes the filings, and each `data/<period>.json` lists its source URLs. `data/_recast27.json` holds the FY27-basis history, `ngaap.json` the company non-GAAP reconciliations, and `manual_items.json` the guidance, debt and lease facts, amortization schedule, buyback authorization, dividends, share count, PPAs, corrections and share price, each with its source. FY27 full-year call commentary is the only non-EDGAR input and is labelled UNVERIFIED in the workbook.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export MSFT_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py && python3 recast27.py`, then `python3 -c "import xbrl; xbrl.dump_subset()"`.
   3. `python3 check_data.py` runs 2,094 checks: statement arithmetic, every segment structure vs consolidated, FY27 lines vs segments vs revenue, non-GAAP bases and bridges vs published, EPS, cash and balance-sheet tie-outs, quarters vs years and the XBRL cross-check. Known exceptions: listed under Data corrections.
3. Build: `python3 build.py --snap --recalc` writes `../MSFT_Model.xlsx`, reruns with the switch on Bull and Bear to fill the snapshot panels, and stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py <file>` → 0 error cells and 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py <file>` → 0 cycles.
   - `python3 ../tools/residue_scan.py <file> --extra WWD Woodward 382.17` → 0 residue hits.
   - Intentional exceptions: Charts segment-contribution bars are 0 before FY2026 (no FY27-basis history before FY2025); the Bull-Base-Bear "LT Hist Avg" ROIC (~99%) reflects Microsoft's net-cash, low-invested-capital years before FY2016.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs, compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `h2t.py`, `tables.py`, `make_index.py`, `fetch.py`, `extract.py`: EDGAR HTML → text / cell-level tables, filings index, downloads, per-period extraction.
- `recast27.py`: FY27-basis history and Q1 FY27 outlook from the 8-K of 2-Sep-2026.
- `xbrl.py`: XBRL company-facts helper (30-June fiscal year).
- `normalize.py`: basis rules, flat model keys, segment structures, non-GAAP, corrections.
- `check_data.py`: data consistency checks.
- `ngaap.json`, `manual_items.json`, `data/`: curated and extracted data; `EXTRACTION_SCHEMA.md`: per-period JSON schema.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
