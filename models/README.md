# Company models

## `TDY_Model.xlsx` — Teledyne Technologies Incorporated (NYSE: TDY)

3-statement model built on the RBA model template (same generator framework, tabs `Model`, `Bull-Base-Bear`, `DCF`,
`Charts`, `Sheet1`, section order, styling, scenario switch, CAGR columns, definition-flag rows and check rows), adapted
to Teledyne's reporting.

- **Historicals:** annual FY2006–FY2012, then quarterly Q1/13–Q2/26 (with 1H and FY columns), all from SEC EDGAR
  (CIK 0001094285):
  - Forms 10-K / 10-Q.
  - Form 8-K earnings releases (Ex. 99.1) for the non-GAAP reconciliations, segment non-GAAP tables, incremental
    acquisition sales, free cash flow and the FY26 outlook. These are the same documents posted on the Teledyne IR
    site, which is not reachable from the build environment.
  - Each period uses the latest filing that presents it. Income statements, segment builds, balance sheets and cash
    flows tie to the reported totals. Sales, operating income, net income, EPS, CFO and total assets were cross-checked
    against SEC XBRL company facts.
- **Reporting changes handled:**
  - **Fiscal calendar:** 52/53-week years (FY2009, FY2015 and FY2020 are 53 weeks).
  - **Teledyne Continental Motors:** discontinued in the FY2010 10-K (sold Apr-2011). FY2006–07 include it.
  - **Segments:** legacy segments (FY2006–07) shown as memo. The current four segments start FY2008, as recast in the
    FY2010 10-K. Later intra-segment recasts are noted (Q2-13, 2018/2019 recasts of 2017, PCT 2016).
  - **Accounting standards:** ASU 2017-07 (2018) recast 2017; ASC 606 from 2018; ASU 2016-09 from 2016.
  - **IS presentation:** acquired-intangible amortization is its own income-statement line from 2021.
  - **Acquisitions:** FLIR from 14-May-2021; Excelitas A&D and Micropac in 2025.
- **Segment build** (HII-style segment P&L): for Digital Imaging, Instrumentation, A&DE and Engineered Systems, segment
  net sales → GAAP segment operating income → + acquired-intangible amortization + other items → non-GAAP segment
  operating income. Corporate expense is shown GAAP and non-GAAP. A future-M&A block (scenario lever) adds unallocated
  acquired sales, non-GAAP operating income and amortization.
- **Bridges:**
  1. GAAP operating income → non-GAAP operating income (company definition).
  2. GAAP net income → EBITDA → adjusted EBITDA → adjusted EBIT. This is a model measure; Teledyne does not publish
     EBITDA.
  3. GAAP net income attributable to Teledyne → non-GAAP net income → non-GAAP diluted EPS.
  - Adjusting items follow the **company definition in force in each period**:
    - 2006–07: EPS "excluding pension, stock option expense and tax benefit".
    - Q4/16–2017: e2v charges.
    - 2018–19: none.
    - 2020: recast comparatives, amortization only.
    - Q1/21 onward: the FLIR-era definition.
  - A definition row flags each change in the column where it takes effect, and cell comments carry the company's
    wording.
  - **Current-definition memo series:** non-GAAP OI, non-GAAP NI and EPS on today's definition for every period, using
    10-K amortization. These drive the growth / valuation outputs.
  - Model bridges tie to the company-published figures in every period:
    - 2017 OI bridges start from pre-ASU 2017-07 OI, so they carry an explicit basis-difference line.
    - Where Teledyne reconciled in per-share amounts only (2006–07, Q4/16–2017), $m = EPS × diluted shares, with a
      labelled rounding line.
- **2026:** Q1/Q2 actual. Q3/Q4 come from the FY26 outlook in the Q2-26 release (22-Jul-2026): FY non-GAAP EPS
  $24.45–24.65 and Q3 $6.05–6.15 by scenario (high / mid / low). Segment sales = prior-year quarter × Q2/26 y/y growth.
  A uniform segment-margin calibration Δ makes non-GAAP net income equal the outlook EPS × diluted shares. No tax-rate
  or capex guidance was given; the 21.5% tax rate and $125m capex are analyst inputs.
- **Scenario switch:** `Model!CT2` (Bull / Base / Bear). Scenario table at `Model!DB9:DF79`: Bull/Bear = Base + Δ.
  Levers:
  - organic sales growth and non-GAAP operating margin for each of the four segments;
  - acquisition spend (M&A lever: EV/sales, margin, intangibles % and amortization life are inputs in the M&A block);
  - buybacks.
- **Debt:** scheduled note maturities (Apr-2028 $700m, Aug-2030 $427m), with a revolver that draws only to keep a
  minimum cash balance. Interest is calculated on opening balances, so there is no circularity.
- **Valuation:** share price $615 (input per user, `Model` valuation row, 2026E). The DCF deducts M&A spend in 2027E–30E
  only (no new deals in the fade or terminal period).

Rebuild (from the repo root): `RECALC_SCRIPT=<path to recalc.py> python -m models.tdy.build`.
- Recalculation and the Bull/Bear snapshot values need LibreOffice **Calc** (`apt-get install libreoffice-calc`;
  `libreoffice-core` alone cannot open .xlsx).
- Source data is in `models/data/tdy/*.json`; the extraction spec is `models/data/tdy/README.md`.
