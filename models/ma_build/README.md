# MA model build kit

`models/MA_Model.xlsx` is the Mastercard Incorporated (NYSE: MA) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD build kit:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link;
  - red italic = definition flags.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CF2`, scenario table in `Model!CN:CR`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). The 2026E UFCF is excluded because net debt is taken at YE2026E (valuation date Oct-2026).
  - Charts: payment network vs value-added services contribution to growth, adjusted EBITDA (model) and operating income, returns (2011–2030E).
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (fiscal year ends 31 December)
Mastercard's history window matches the template's own columns, so there is no column shift.
- **C–I FY2006–2012:** annual, as originally reported (Q4 release twelve-month columns).
- **J–BV Q1/13–Q4/25 with FY subtotals:** grouped and collapsed like the template.
- **BW–BX Q1/26–Q2/26:** actual. **BY–BZ Q3/26E–Q4/26E, CA 2026E:** forecast, calibrated to the FY26 outlook (unverified, see below).
- **CB–CE 2027E–2030E:** scenario forecast.
- **Right of the forecast:** CF notes, CH–CK CAGRs (5Y forward '25–'30, 5Y, 10Y, 19Y), CN–CR scenario table.

## Basis
- **Policy:** as originally reported in each period's own earnings release (8-K Item 2.02, Ex. 99.1).
- **Re-presentations kept as memo / comments, not recast:**
  - 2014 net revenue as re-presented in the 2015 releases (e.g. FY2014 $9,473m → $9,441m), in a memo row.
  - FY2018: the Q4-18 release moved $89m from advertising & marketing to G&A for the year; the quarters stay as first reported.
  - Q1-19 non-GAAP as first reported (equity-investment exclusion started Q2-19).
- **Segments:** one reportable segment. Net revenue by category:
  - **Payment network / value-added services and solutions:** presented from the FY2022 10-K. FY2020–21 and the 2021–22 quarters come from the next filings' comparatives (Q1-21 = H1 − Q2; Q4 = FY − 9M).
  - **Legacy categories** (domestic assessments, cross-border volume fees, transaction processing fees, other revenues, rebates and incentives; FY2007–Q3-22): memo rows with a Σ check. FY2007–08 come from the FY2009 10-K recast; FY2006 is not published on this basis.
  - **Payment network key metrics** (assessments and rebates; from FY2022): memo rows with a Σ check to payment network revenue.
- **Per-share data:** 10-for-1 split effective 21-Jan-2014. Documents filed earlier are restated (shares × 10, per share ÷ 10). Class A and Class B shares are combined (EPS is reported for both classes together).
- **Cash flow:**
  - Quarters derived from year to date (Q4 = FY − 9M).
  - From 2018 (ASU 2016-18) cash includes restricted cash and restricted security deposits held for customers.
  - From 2018 to Q3-24 the cash-flow cash also included $15–36m of restricted cash that the balance sheet carried inside prepaid / other assets. This is shown as a memo line in the BS-vs-CF cash check.
- **Releases to 2009** are in USD thousands (converted).

## Model structure (Model tab)
- **Volume drivers:**
  - GDV (all Mastercard-branded programs, worldwide, from the release operating-performance tables).
  - Local-currency growth × FX translation.
  - Memo: cross-border volume growth, switched transactions growth and cards (release text, transcribed).
- **Payment network:**
  - 2027E+: GDV × yield (bps), with a yield-change lever.
  - Q3/Q4-26E: prior-year quarter × (1 + H1-26 y/y + calibration Δ).
- **Value-added services and solutions:** prior year × (1 + growth). The Q3/Q4-26E growth carries the same calibration Δ.
- **Pending BVNK acquisition** ($1.5bn + up to $300m contingent; expected to close by end-Q3-2026 per the Q2-26 10-Q):
  - It has its own block with a switch; closing is assumed at 30-Sep-2026.
  - Revenue and opex are not disclosed, so they are flagged inputs set to 0.
  - Intangibles are assumed at 25% of the consideration and amortized over 8 years; the rest goes to goodwill.
- **Future M&A lever:** spend ÷ EV/sales (8x), 15% adjusted margin after amortization, intangibles 30% (8-year life), the rest goodwill.
- **FY26 outlook calibration** (Q3/Q4-26E; both Δs sit in the 2026E column):
  1. A uniform growth Δ on payment network and value-added services solves FY26 organic net revenue to FY2025 × (1 + 14.0% / 13.5% / 13.0%), the reported-USD translation of "high end of low double digits" currency-neutral + ~1 ppt FX.
  2. A uniform Δ on adjusted operating expense growth solves FY26 adjusted opex to FY2025 × (1 + 11.0% / 11.5% / 12.0%).
  3. Other income, tax (20.5%), D&A and interest are point estimates. Adjusted EPS is an output.
- **GAAP P&L from the build:**
  - Operating income = adjusted operating income − special items.
  - Advertising & marketing runs as % of revenue and D&A as a point estimate / % of revenue; G&A is the balancing line.
  - Interest is calculated on opening balances; investment income on opening cash.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **GAAP operating expenses → adjusted operating expenses → adjusted operating income / margin:** company definition. Special items:
     - litigation provisions;
     - restructuring;
     - other items: Foundation contribution 2006, pension termination 2015, Venezuela 2017, indirect tax 2021, Russia 2022 (incl. a revenue item).

     Adjusted revenue ≠ GAAP only in 2022.
  2. **Net income → EBITDA → adjusted EBITDA:** a **model definition**; Mastercard publishes no EBITDA. Adjusted EBITDA = adjusted operating income + D&A, with an identity check.
  3. **Net income → adjusted net income → adjusted diluted EPS:** company definition.
     - The historical tax effect is derived as published adjusted net income − net income − pre-tax items. It includes discrete tax items (U.S. Tax Act 2017–19).
     - Equity-investment (gains) losses are excluded from Q2-19.
     - FY2006–09 were annual "excluding special items" figures. 2010 and quarters with no special items are adjusted = GAAP, flagged in the definition rows.
- **Other schedules:**
  - Cash flow; buybacks; balance sheet.
  - Working capital: DSO, settlement balances × GDV, prepaid / accrued customer incentives as % of revenue.
  - Debt: notes repaid at maturity per the Q2-26 10-Q ladder and refinanced; commercial paper to a $12.0bn minimum cash balance (cash-flow basis), with a headroom memo vs the $8bn facility.
  - Leverage-target buybacks from 2027E: net debt / adjusted EBITDA of 0.7x / 0.5x / 0.3x.
  - Ratios and valuation.
- **DCF basis:**
  - NOPAT is on adjusted operating income, which is full-cost: share-based compensation and all amortization are expensed. Cash litigation provisions and restructuring are deducted.
  - D&A is added back and capex (incl. capitalized software) deducted.
  - No leases in net debt.
  - Opening IC = 2025A book IC + the BVNK consideration.
  - Market inputs (risk-free 4.25%, ERP 5%, beta 1.0) are assumptions: rate sources are not reachable from the build environment.

## Key forecast assumptions (Base)
- **GDV growth (local currency):** 8.5% / 8.0% / 8.0% / 7.5% (2027E–30E). H1-26 +7.7%; FY2025 +8.6%.
- **Payment network yield change:** +1.5% / +1.5% / +1.0% / +1.0% a year (2021 15.5 bps → 2025 18.3 bps).
- **Value-added services growth:** 15% → 12% (FY2025 +23%, H1-26 +21%).
- **Adjusted operating margin:** 60.3% → 61.8% (2025 59.2%; H1-26 61.0%).
- **Litigation provisions:** $100m a quarter in H2-26, then $450m a year (assumption; FY2022–25 $356–680m).
- **Other cost drivers:** advertising & marketing 2.7% of revenue; D&A 3.4% (+ acquisition amortization); share-based compensation 1.8%; capex 4.0%; tax 20.5%.
- **Capital returns:** M&A $1.0bn a year; H2-26 buybacks $7.0bn; DPS +13% a year (Q4-26 declared $0.99, assumption).
- **Share price $595.00:** user-provided (13-Oct-2026). Update it at `Model!CA` in the valuation block.

**Base outputs:**
- **2026E:** net revenue $37.2bn (+13.5%); adjusted operating margin 59.9%; adjusted EPS $19.89; FCF $16.2bn.
- **2030E:** adjusted EPS $35.05.
- **DCF:** $574 a share (−3.5%). Bull $643, Bear $479.

## FY26 outlook (UNVERIFIED)
Mastercard gives its outlook on the earnings call only. The 8-K release contains none, and the Ex. 99.2 slide decks stopped being furnished after 2019. The FY26 wording below is from the Q2-26 call (30-Jul-2026), taken from third-party transcripts found by web search (Yahoo Finance, Motley Fool, Globe and Mail, Investing.com). investor.mastercard.com is blocked. The workbook marks every guidance input as UNVERIFIED.
- **Net revenue:** growth at the high end of a low-double-digits rate (currency-neutral, ex-acquisitions; raised), FX ~+1 ppt.
- **Adjusted opex:** growth at a low-double-digits rate; FX 0.5–1 ppt headwind.
- **Q3 other expense:** ~$(125)m.
- **Non-GAAP tax rate:** 20–21% in Q3 and Q4.

## Data corrections
- **Q1-26 ending cash:** the release prints end-of-period cash (incl. restricted) as $13,248m, equal to the beginning balance. The Q1-26 10-Q shows $10,764m (= 13,248 − 2,484), which ties to the 31-Mar-2026 balance sheet. The model uses the 10-Q figure (`manual_items.json` → corrections; cell comment).

**Known data exceptions** (documented in `check_data.py`, not corrected):
- 2008–09 EPS: the two-class method, so net income ÷ diluted shares differs by ~$0.007.
- The FY2018 cost reclassification ($89m).
- The FY2019 equity-investment item (the exclusion started in Q2-19).
- GDV revisions between the annual and quarterly tables (≤ $18bn).
- 2018–Q3-24 restricted cash held in other assets ($15–36m).

## Sources
SEC EDGAR only (Mastercard Incorporated, CIK 1141391):
- Forms 10-K / 10-Q FY2006–Q2-2026: revenue by category, dividends declared per share, debt (Note 9), acquisitions (Note 2), share counts and repurchases.
- Form 8-K Item 2.02 earnings releases (Ex. 99.1), Q2-2006 – Q2-2026: statements, non-GAAP reconciliations, operating performance (GDV) tables, KPI text.
- XBRL company facts: cross-checks of revenue, operating income, net income, diluted EPS, CFO and total assets (as first filed).

`filings.csv` indexes the filings (`period_index.py` maps periods to documents). Each `data/<period>.json` lists its source URLs.
- `data/_agent/*.json` hold the transcribed non-GAAP items, KPIs and revenue categories (EXTRACTION_SCHEMA.md).
- `data/_dps.json` holds dividends declared per share; `data/_xbrl.json` the XBRL subset.
- `manual_items.json` holds the share price, the unverified FY26 outlook, the recast revenue categories, BVNK and Recorded Future, the debt ladder, the amortization schedule, buyback authorizations, shares, dividends and corrections, each with its source.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export MA_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 period_index.py && python3 extract.py`.
   3. Re-run the transcription for new periods with EXTRACTION_SCHEMA.md (non-GAAP items, KPIs, revenue categories → `data/_agent/`).
   4. `python3 check_data.py` runs 1,435 checks: statement arithmetic, bridges, revenue categories, EPS, cash and BS tie-outs, quarters vs years and XBRL cross-checks. The 44 known exceptions are listed above, labelled `[known]`.
3. Build: `python3 build.py --snap --recalc` writes `../MA_Model.xlsx`. It reruns with the switch on Bull and Bear to fill the snapshot panels, then stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../MA_Model.xlsx` → 0 error cells and 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../MA_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../MA_Model.xlsx --extra WWD Woodward 382.17 Aerospace Spartanburg ONTIC "L'Orange"` → 0 residue hits.

## Files
- `fw.py`: column map (template columns, no shift), style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- EDGAR pipeline:
  - `make_index.py`, `fetch.py`, `h2t.py`, `period_index.py`: filings index, downloads, HTML → text, period-to-document map.
  - `parse_release.py`: generic release table parser (label | values; units per release).
  - `extract.py`: per-period statements, GDV rows and dividends per share.
- `xbrl.py`: XBRL company-facts helper (calendar years).
- `normalize.py`: basis rules, split adjustment, section-aware balance sheet, discrete quarterly cash flow, transcribed-data merge.
- `check_data.py`: data consistency checks.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and transcription rules.
