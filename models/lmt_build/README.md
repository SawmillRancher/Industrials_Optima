# LMT model build kit

`models/LMT_Model.xlsx` is the Lockheed Martin Corporation (NYSE: LMT) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD build kit:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CG2`, scenario table in `Model!CO:CS`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). 2026E (ending 31-Dec-2026, six weeks after the valuation date) is the base year, so the explicit years are 2027E–2031E and net debt is taken at 31-Dec-2026, after the Ultra Maritime payment.
  - Charts: segment contribution to sales growth, adjusted EBITDA / operating profit, returns.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (fiscal year ends 31 December; quarters close on the last Sunday of March / June / September)
- **C–I FY2006–FY2012:** annual.
- **J–BV Q1/13–Q4/25 with FY subtotals; BW–BY Q1/26–Q3/26:** grouped and collapsed like the template.
- **BZ Q4/26E, CA 2026E:** forecast, calibrated to the 2026 outlook (Q3 2026 release, 22-Oct-2026).
- **CB–CF 2027E–2031E:** scenario forecast.
- **Right of the forecast** (template column + 1): CG notes, CI–CL CAGRs (5Y fwd '26–'31, 5Y, 10Y, 19Y), CO–CS scenario table.

## Basis
- **Policy:** as originally reported in each period's own earnings release, with the company's own re-presentations applied where the following year's filings re-present the whole period (hybrid). Re-presented cells carry comments with the originally reported figures:
  - FY2006: four-segment structure and the non-operating presentation of the FY2007 release (originally reported operating profit $3,953m incl. $183m of interest income / non-operating items; $3,770m re-presented).
  - FY2011–12 segments: the five-segment structure introduced in 2013 (FY2011 from the FY2013 Form 10-K, FY2012 from the Q4-13 release comparatives); Electronic Systems split into MFC / MST / IS&GS. Consolidated figures unchanged.
  - 2014–15 segments (years and quarters): the Q4/15 program realignment basis (pro forma tables in the Q4-15 release of 26-Jan-2016); consolidated figures unchanged.
  - Q1/Q2-16: continuing operations (IS&GS in discontinued operations) from the 2017 release comparatives, so every 2016 column is on the same basis as the Q3/Q4-16 releases and the 2016 10-K. 2015 and earlier include IS&GS; memo rows carry the 2016 continuing-operations re-presentation of 2015 (net sales $40,536m) for like-for-like 2016 growth.
  - 2017 (year and quarters): the ASC 606 (full retrospective) and ASU 2017-07 adjusted basis from the 2018 release comparatives (net sales $49,960m vs $51,048m first reported; operating profit $6,744m vs $5,921m), with the non-service pension reclassification by quarter from the Q1-18 release table, so 2018 y/y is like-for-like. 2016 and earlier remain pre-ASC 606 (flagged in the definition row).
- **Balance sheet and cash flow:** as originally reported throughout (2017 balance sheet pre-ASC 606; 2016 cash flow incl. IS&GS). A cash-flow memo row shows the net-earnings basis difference in the re-presented periods.
- **Segments:** Aeronautics; Missiles and Fire Control; Rotary and Mission Systems (Mission Systems and Training to 2015; Sikorsky from 6-Nov-2015); Space (Space Systems to 2019). Legacy segments IS&GS (to 2015) and Electronic Systems (to 2010) are memo rows included in the group totals of their periods.
- **Unallocated items** keep the company lines: FAS/CAS pension adjustment (total to 2017; operating adjustment from 2018), intangible asset amortization (separate line from 2023), severance / impairment and other charges, stock-based compensation and other, net, unusual items (2006–10).
- **Per-share data:** no stock splits. Quarterly dividends per share = the rate paid in the quarter (Q1 declared rate; Q4 = year − 9M); annual = declared per share (XBRL; FY2006–08 from the FY2008 10-K).
- **Cash flow:** quarters derived from year to date (Q4 = FY − 9M).

## Model structure (Model tab)
- **Segment build:** segment net sales = prior year × (1 + growth); segment operating profit = sales × segment margin; Σ = business segment operating profit (the company's non-GAAP measure and the one it guides). Backlog roll-forward per segment (orders = sales × book-to-bill lever; history: implied orders = Δ backlog + sales).
- **Unallocated items:** FAS/CAS pension operating adjustment from the pension block; intangible amortization from the 10-K schedule plus deal purchase accounting; severance input; stock-based compensation and other, net as % of sales.
- **Pension block:** CAS pension cost, FAS service cost, FAS/CAS operating adjustment (= CAS − service cost), non-service FAS pension (expense) income, total FAS/CAS adjustment, settlement charges (memo), contributions. 2026E from the company outlook (operating adjustment $1,685m, non-service $(320)m, total $1,365m); 2027E+ inputs held at the 2026 level (assumption; no 2027 guidance has been filed).
- **Ultra Maritime block (pending):** switch, $3.45bn cash consideration (Q3-26 10-Q Note 13), closing assumed 31-Dec-2026 (no 2026 contribution), reported in RMS from 2027E. Standalone sales (~$900m, ~3.8x EV/sales), 12% margin and the PPA (40% intangibles over 12 years, 10% PP&E, rest goodwill) are **model assumptions, flagged** — the target is private and its revenue is not disclosed on EDGAR. Excluded from the 2026 outlook calibration.
- **Future M&A lever:** spend ÷ EV/sales (3.5x), 12% margin, PP&E / intangibles / goodwill split, 12-year amortization.
- **2026 outlook calibration (Q4/26E):**
  - Sales: one uniform Δ on the 9M 2026 y/y growth of the four segments, solved so 2026E net sales ex Ultra Maritime = the guided end-point (~$80.0 / 81.0 / 82.0bn by scenario).
  - Segment margins: one uniform Δ on the 9M 2026 segment margins (the prior-year quarters carry the Q2/25 program losses), solved so business segment operating profit = $8,575 / 8,625 / 8,675m.
  - Cash from operations: the Q4/26E contract-asset change is the plug so that 2026E CFO = $10.0 / 10.1 / 10.2bn.
  - Information rows, not forced: diluted EPS ($30.35–30.75; model Base $30.67 with the point estimates), consolidated operating profit (company bridge $9,520–9,620m), free cash flow ($7.8–8.0bn; model $7.9bn at the $2.2bn capex point estimate).
  - Point estimates for Q4/26E (unallocated items from the company bridge less 9M actuals, interest, non-service pension, tax rate 16.5%, D&A, SBC, deferred taxes, working-capital lines, capex) are in the scenario table.
- **GAAP P&L from the build:** operating profit = business segment operating profit + unallocated items; cost of sales is implied. Interest on opening notes and commercial paper; other non-operating income = yield on opening cash + input; tax at 16% from 2027E.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **Consolidated operating profit → business segment operating profit:** company definition (less the unallocated items), checked against the published figure in every period.
  2. **Net earnings → EBITDA → adjusted EBITDA → adjusted EBIT:** model definitions (Lockheed Martin publishes no EBITDA): operating profit + D&A; + company-flagged severance / impairment / unusual items and the company-quantified program losses (Q4/24 $1,634m, Q2/25 $1,534m at the consolidated level). Intangible amortization and stock-based compensation are not added back (the company adjusts out neither).
  3. **Net earnings → adjusted EPS:** model definition: continuing-operations earnings + the flagged charges (tax-effected at the statutory rate) + the quantified program losses and pension settlement charges (company-disclosed after-tax amounts) + the Q4/17 Tax Act charge. Memo rows rebuild the company's own "excluding" quotes (Q4/17 adjusted EPS from continuing operations $4.30 / 2017 $13.33; per-share impacts of the 2021–25 items) with a check.
- **Other schedules:** cash flow (2026E = 9M actual + Q4 lines in the Q4/26E column); buybacks; balance sheet rolled from the 27-Sep-2026 balance sheet; working capital (receivables days, contract assets / inventories / contract liabilities / salaries / other as % of sales, payable days on cost of sales); Ultra Maritime PPA; debt (notes repaid at maturity per the 10-K ladder and 100% refinanced; commercial paper / revolver to a $2.5bn minimum cash balance; $6.0bn of facilities); pension liability roll-forward (+ FAS expense − contributions); leverage-targeted buybacks 2027E+ (net debt / adjusted EBITDA 1.50 / 1.25 / 1.00x by scenario, floored at a $1.0bn programme); ratios and valuation.
- **DCF basis:** NOPAT on adjusted EBIT (model; full-cost, incl. the FAS/CAS operating adjustment) less cash severance, tax 16%; D&A added back; capex and M&A deducted; non-service pension and settlement charges excluded; no pension contributions (none required in 2026). WACC 7.6% (risk-free 4.25%, ERP 5%, beta 0.75, cost of debt 5.2%, D/V 10%: assumptions, market data not reachable from the build environment); terminal growth 2.5%.

## Key forecast assumptions (Base)
- **Segment growth 2027E–31E:** Aeronautics 5% → 3%; MFC 15% → 5% (munitions ramps, $143bn backlog incl. the $52.5bn PAC-3 MSE award); RMS 5% → 3% (ex Ultra Maritime); Space 5% → 3%. Book-to-bill 1.05x → 1.00x. All assumptions anchored on 9M 2026 growth and backlog coverage (scenario-table notes).
- **Segment margins:** Aeronautics 9.5% → 10.0%; MFC 14.0% → 14.5%; RMS 11.5% → 12.0%; Space 9.5% → 10.0% (recovering toward the 2019–23 ranges from the 2024–25 program losses).
- **Other drivers:** FAS/CAS operating adjustment $1,685m p.a., non-service pension $(300)m p.a. (held); intangible amortization per the 10-K schedule + Ultra Maritime (~$115m p.a.); other unallocated 0.65% of sales; depreciation 1.9–2.0% of sales; capex 2.6% of sales; tax 16%; deferred taxes $200m p.a.; contract assets normalising from ~20.5% of sales at YE2026E to 17.3% by 2030E; DPS +4.5% p.a.; M&A $500m p.a.
- **Share price $601.50:** mid-point of the 23-Oct-2026 open-market sales reported on the Form 4 of F. A. St John (filed 27-Oct-2026; $600.00–602.98). This is the latest share price observable on EDGAR (there were no repurchases in Q3 2026); update it to market at `Model!CA` in the valuation block.

## Data corrections
- None. Known data exceptions (documented, not corrected):
  - The company's 2024 program-loss disclosure gives $1,965m for the year vs $1,720m for Q4; the $245m recognised in Q1–Q3/24 was not quantified by quarter, so the model carries the Q4 amount in the annual column too (cell comment).
  - The non-service FAS pension line was not presented for Q1/Q2-20 (introduced Q3-21; only Q3/Q4-20 re-presented), so those quarters show it inside other non-operating income and the 2020 quarter-sum check is exempt.
  - The FY2006 release backlog table is on the Systems & IT Group sub-segment basis; only the total is used.

## Sources
SEC EDGAR only (CIK 936468):
- Forms 10-K FY2006–FY2025 and 10-Q Q1/07–Q3/26 (segment tables for the 2011 realignment; debt, amortization and pension schedules; Ultra Maritime terms; dividend declaration; share price fallback via Form 4).
- Form 8-K Item 2.02 earnings releases (Ex. 99.1), Q4/06 (Jan-2007) – Q3/26 (22-Oct-2026): 80 releases.
- 8-Ks for the 2025 notes (28-Jul-2025) and the revolving credit agreements (Dec-2025, Aug-2026).
- XBRL company facts: dividends declared per share (cross-checks of sales, operating profit, net earnings).

The investor-relations site (lockheedmartin.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR.
- `filings.csv` indexes the filings; `data/_releases.json` indexes the releases used per period.
- Each `data/<period>.json` lists its source URLs; `data/_segpf_2015.json` (Q4/15 realignment pro forma tables), `data/_10k_segments.json` (10-K segment tables) and `data/_xbrl.json` (XBRL subset) support the re-presentations.
- `manual_items.json` holds the 2026 outlook history, the 2026 pension outlook, the 2017 ASU 2017-07 reclassification by quarter, the company-quantified special items, pre-XBRL dividends, the Ultra Maritime terms and assumptions, the debt ladder, the amortization schedule and the share price, each with its source.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export LMT_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`.
   3. `python3 check_data.py` runs 1,950 checks: statement arithmetic, segment and unallocated sums, pension identities, EPS, cash and balance-sheet tie-outs, published free cash flow, and quarters vs years. Known exception: 2020 non-service pension quarters (see Data corrections).
3. Build: `python3 build.py --snap --recalc` writes `../LMT_Model.xlsx`, reruns with the switch on Bull and Bear to fill the snapshot panels, and stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../LMT_Model.xlsx` → 0 error cells, 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../LMT_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../LMT_Model.xlsx --extra WWD Woodward 382.17` → 0 residue hits.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`: EDGAR filings index, downloads, HTML → text.
- `parse_release.py`: release parser (tables identified by content; columns resolved from the header rows; % change columns handled).
- `extract.py`: per-period extraction (statements, segments and unallocated items, pension tables, backlog, deliveries, cash flow, balance sheet, prior-year comparatives, pro forma realignment tables, 10-K segment tables).
- `xbrl.py`: XBRL company-facts helper (calendar fiscal year).
- `normalize.py`: basis rules (hybrid re-presentations), flat model keys, discrete quarterly cash flow, special items.
- `check_data.py`: data consistency checks.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
