# RTX model build kit

`models/RTX_Model.xlsx` is the RTX Corporation (NYSE: RTX) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD build kit:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped and collapsed.
- **Scenarios:** Bull / Base / Bear switch in `Model!CG2`, scenario table in `Model!CO:CS`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). 2026E (ending 31-Dec-2026, seven weeks after the valuation date) is the base year: the explicit years are 2027E–2031E and net debt is taken at 31-Dec-2026.
  - Charts: contribution to sales growth (Collins + Pratt & Whitney vs Raytheon, legacy UTC segments and eliminations), adjusted EBITDA / operating profit, returns.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (calendar fiscal years)
- **C–I 2006–2012:** annual, on the latest 10-K presentation of each year (see Basis).
- **J–BV Q1/13–Q4/25 with FY subtotals; BW–BY Q1/26–Q3/26:** grouped and collapsed like the template.
- **BZ Q4/26E, CA 2026E:** forecast, calibrated to the 2026 outlook (Q3-26 release, 20-Oct-2026).
- **CB–CF 2027E–2031E:** scenario forecast.
- **Right of the forecast** (template column − 1, because RTX has five scenario years and the template four): CG notes, CI–CL CAGRs (5Y fwd '26–'31, 5Y, 10Y, 19Y), CO–CS scenario table.

## Basis
- **Registrant:** CIK 0000101829 throughout. United Technologies Corporation to 3-Apr-2020, Raytheon Technologies Corporation to Jul-2023, RTX Corporation since. Raytheon Company (CIK 1047122) merged in on 3-Apr-2020; its own history is not carried.
- **Policy: hybrid recast** (DHR / STE style) for the income statement, segments and published adjusted figures:
  - A quarterly year (2013+) takes the comparatives re-presented in the following year's releases when all four quarters were re-presented and the four restated quarters add up to the restated year. Otherwise the year stays as originally reported, and the recast figures sit in memo rows.
  - Recast years and reasons: 2015 (Sikorsky discontinued), 2016 (ASU 2016-09), 2017 (ASU 2017-07 pension), 2019 (Otis and Carrier discontinued, new segment measure), 2020 (RIS / RMD reorganization), 2023 (2024 Collins / Raytheon realignment).
  - Kept as reported: 2013, 2014, 2018, 2021, 2022, 2024 and 2025. 2014 and 2022 were only partly re-presented (Q3–Q4 in the following year's releases); RIS and RMD are summed into Raytheon in every period anyway.
  - 2006–2012: 2006 and 2012 as originally reported; 2007 as presented in the FY2009 10-K (SFAS 160, collaboration gross-up); 2008–09 in the FY2010–11 10-Ks (other income moved out of revenues); 2010–11 in the FY2012–13 10-Ks (Rocketdyne, Clipper, UTC Power and Hamilton Sundstrand Industrial in discontinued operations). 2006–07 revenues therefore still include other income, net (2006: $711m), flagged in cell comments.
  - Each recast cell carries a comment.
- **Balance sheet and cash flow:** as originally reported.
- **Segments:**
  - Current lineage rows: Collins Aerospace (Hamilton Sundstrand → UTC Aerospace Systems from Jul-2012 → Collins from Nov-2018), Pratt & Whitney, and Raytheon (RIS + RMD summed for Q2-20 to 2022).
  - Legacy segments are memo rows included in the consolidated totals in their years: Otis, Carrier / CCS and UTC Fire & Security to Q4-19 (Q1-20 as reported), and Sikorsky to Q2-15.
- **Customer-type build:** from the 10-Q / 10-K revenue disaggregation (ASC 606, 2018+). Collins and Pratt & Whitney are split commercial vs defense (U.S. government + FMS + direct foreign government); Raytheon is split U.S. government vs international vs commercial; inter-segment sales are shown separately.
- **Per-share data:** no splits. Share counts step up from Q2-20, when 648.4m shares were issued in the Raytheon merger.
- **Cash flow:** quarters derived from year-to-date statements (Q4 = FY − 9M). Five quarters use the release three-month column instead, because the year-to-date statements change basis mid-year (`manual_items.json` → `cf_quarter_override`):
  - Q2-15;
  - Q3-15 (Sikorsky);
  - Q3-16 and Q4-16 (ASU 2016-15 / 2016-18);
  - Q2-20 (Otis and Carrier).

## Model structure (Model tab)
- **Segment build:**
  - customer-type lines → external sales → + inter-segment = segment sales (checked against the segment table);
  - × adjusted segment margin = adjusted segment OP;
  - + eliminations & other + corporate + FAS/CAS operating adjustment = adjusted operating profit (checked against the bridge).

  GAAP segment OP = adjusted − restructuring + significant items.
- **Below the segments:** FAS/CAS operating adjustment (CAS pension cost recovered in U.S. government pricing − FAS service cost) and acquisition accounting adjustments. Both are separate lines from Q2-20. A Σ segment-table check against consolidated operating profit runs in every period.
- **Future M&A lever:** spend ÷ EV/sales (2.5x), 12% adjusted margin, PP&E / intangibles / goodwill split, 15-year amortization. Base nil; Bull $500m p.a.
- **2026 outlook calibration (Q4/26E):**
  - Sales: one uniform Δ on the 9M-26 y/y growth of every customer-type line, solved so 2026E net sales = the adjusted-sales end-point ($97.5 / 97.25 / 97.0bn). Base Δ is −6.5pp; Q4-25 was strong.
  - Margins: one uniform Δ on adjusted segment margins (prior-year quarter + 9M drift), solved so 2026E adjusted EPS = $7.75 / 7.70 / 7.65. Base Δ is −1.3pp: the Q3-26 margins included IEEPA tariff refunds.
  - FCF: 2026E contract assets are the designated working-capital plug, solved so FCF = $9.2 / 9.1 / 9.0bn.
  - Organic growth (10–11%) is an information row.
- **GAAP P&L from the build:** operating profit = adjusted OP − restructuring − acquisition accounting adjustments + significant items. Gross profit is implied.

  Other lines:
  - non-service pension income (non-cash) is an input;
  - interest is calculated on opening balances;
  - GAAP tax = adjusted tax − tax effect of the items (21% marginal rate);
  - NCI is a % of continuing income.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **Operating profit → adjusted operating profit:** + restructuring + acquisition accounting adjustments (from Q2-20) − net significant items.

     Definition flags:
     - 2006–12: no adjusted OP published except 2009 and 2011 on a later basis; net items derived from the published figure where one exists, otherwise from the release bullet items.
     - 2013–19: excludes restructuring and significant items.
     - Q2-20+: also excludes acquisition accounting.
     - Q3-23: powder metal.

     The Q2-20 goodwill impairment ($3,183m) sits in the segment table's acquisition-accounting line but is a significant item in the bridge.
  2. **Net income → EBITDA → adjusted EBITDA:** model definition; RTX publishes no EBITDA. Equals adjusted OP + depreciation & other amortization.
  3. **Net income attributable → adjusted net income → adjusted EPS:** the tax effect is derived from published adjusted net income where available. Otherwise it is the company-stated tax effect, or 35% statutory, flagged. Adjusted EPS is first printed for Q3-14; Q1-19 recast adjusted net income is derived as 6M − Q2 from the Q2-20 release.
- **Other schedules:**
  - Cash flow with the restricted-cash memo.
  - Buybacks and dividends (DPS × beginning shares).
  - Balance sheet: other assets accrete with non-cash pension income; other long-term liabilities take deferred tax and other operating items.
  - Working capital at FY2025 year-end days.
  - Purchase-price allocation memo rows (not filled; deal details are in the data notes).
  - Debt: Q3-26 10-Q ladder, half of 2027E+ maturities refinanced, commercial paper / incremental borrowings to a $6bn minimum cash balance, headroom memo vs the $5bn revolver.
  - Leverage-target buybacks, 2027E+: 1.75x / 1.25x / 0.75x net debt to adjusted EBITDA.
- **DCF basis:**
  - NOPAT = adjusted EBIT (before acquired-intangible amortization, after stock compensation and the FAS/CAS adjustment) less restructuring, × (1 − 19%).
  - Depreciation & other amortization added back; capex and M&A deducted.
  - Non-service pension income excluded; leases operating; NCI and redeemable NCI deducted.
  - Market inputs are assumptions (U.S. Treasury data not reachable): risk-free 4.25%, ERP 5%, beta 0.85, cost of debt 5.5%, D/V 10%.

## Key forecast assumptions (Base)
- **Customer-type growth 2027E → 2031E:**
  - Collins commercial 8% → 5%; Collins defense 5% → 4%.
  - Pratt & Whitney commercial 9% → 5%; Pratt & Whitney military 6% → 4%.
  - Raytheon U.S. government 8% → 4%; Raytheon international 10% → 5%.

  These are scenario-table assumptions citing 9M-26 rates and backlog.
- **Adjusted segment margins:** Collins 18.5% → 19.5%; Pratt & Whitney 9.5% → 11.5%; Raytheon 13.2% → 14.0%.
- **Other drivers** (assumptions, labelled in the notes):
  - FAS/CAS $620m falling to $420m; non-service pension income $1,350m falling to $1,150m.
  - Restructuring $200m falling to $150m; adjusted tax rate 19%.
  - Capex 3.0% → 2.8% of sales; depreciation & other amortization 2.5–2.6%.
  - Acquisition amortization per the Q3-26 10-Q schedule ($1,884m in 2027 → $1,593m in 2031).
  - DPS +7% p.a.; minimum cash $6bn.
- **Share price $201.70:** open-market sale on 30-Oct-2026 at a weighted average $201.6951 (Form 4 filed 3-Nov-2026). This is the latest share price in an SEC filing; update it at `Model!CA` in the valuation block.

## Outlook sources and unverified items
- The 2026 outlook (adjusted sales, organic growth, adjusted EPS, FCF) comes from the SEC-filed releases (27-Jan, 21-Apr, 23-Jul, 20-Oct-2026).
- RTX gives segment, tax-rate, interest, pension, capex and share-count outlooks on its calls and slides. These are not filed on EDGAR, and rtx.com is not reachable from the build environment, so none are used. Every Q4/26E point estimate for those items is labelled in the scenario table as an assumption not guided in any SEC filing.

## Data corrections and exceptions
- None corrected. Documented exceptions, each handled in `normalize.py` and logged:
  - 2006–2007: UTC "Revenues" included other income, net in those presentations (2006 $711m). No later filing re-presents those years without it, so they are kept and flagged; 2008 onward excludes it.
  - 2010: adjusted OP ($7,800m) exists only on the original basis, so it is a memo; the recast 2010 has no published adjusted OP.
  - 2006–2011: the segment adjustments do not add up to the consolidated items (UTC published no segment adjusted figures). The difference sits in "adjustments in eliminations and other (incl. items not allocated to segments)".
  - Q3-15, Q1-13 and 2012: cash held for sale is included in the restricted-cash memo.
  - Cash-flow quarters vs year are not compared for 2015, 2016 and 2020 (basis changes above).

## Sources
SEC EDGAR only (CIK 0000101829):
- Forms 10-K FY2006–FY2025 (financial statements in Exhibit 13 to FY2018) and 10-Q Q1-2007–Q3-2026.
- Form 8-K Item 2.02 earnings releases (Ex. 99), Q4-2006 – Q3-2026 (the Q3-17 release was filed under Item 2.01).
- Form 4 filed 3-Nov-2026 for the share price.
- XBRL company facts, used to cross-check sales, operating profit, net income, diluted EPS and total assets (176 comparisons, all matching).

The investor-relations site (rtx.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR.
- `filings.csv` indexes the filings.
- `data/_period_index.json` maps each period to its release and filings.
- Each `data/<period>.json` lists its source URLs.
- `data/_xbrl.json` holds the XBRL subset.
- `manual_items.json` holds:
  - the 2026 outlook history;
  - Q3-26 10-Q facts (IEEPA refunds, backlog, the Pratt & Whitney customer bankruptcy);
  - the amortization schedule, the debt ladder by maturity year, revolver and commercial paper;
  - buyback authorization, dividends, pension facts;
  - the share price and the cash-flow quarter overrides, each with its source.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export RTX_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 period_index.py`. Exhibit 13 annual reports for FY2006–FY2018 must also be fetched; see `period_index.py` (`ex13_txt`).
   3. Extract new periods per `EXTRACTION_SCHEMA.md`. The kit has no automated parser: the 75 records were extracted by agents from the text versions, each validated with `check_record.py`.
   4. `python3 check_data.py` runs 1,402 checks plus 176 XBRL comparisons: statement arithmetic, segment and customer-type sums, the adjusted-OP bridge, EPS and adjusted EPS, cash and balance-sheet tie-outs, and quarters vs years on the same basis. Known exceptions are listed in its output.
3. Build: `python3 build.py --snap --recalc` writes `../RTX_Model.xlsx`. It reruns with the switch on Bull and Bear to fill the snapshot panels, then stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../RTX_Model.xlsx` → 0 error cells, 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../RTX_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../RTX_Model.xlsx --extra WWD Woodward 382.17` → 0 residue hits.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`, `period_index.py`: EDGAR filings index, downloads, HTML → text, period → document map.
- `xbrl.py`: XBRL company-facts helper.
- `normalize.py`: basis selection (hybrid recast), flat model keys, discrete quarterly cash flow, quarter overrides, derived unallocated adjustments.
- `check_record.py`: per-record self-checks used during extraction.
- `check_data.py`: data consistency checks and the XBRL cross-check.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
