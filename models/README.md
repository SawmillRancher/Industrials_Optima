# Company models

## `RBA_Model.xlsx` — RB Global, Inc. (NYSE / TSX: RBA; formerly Ritchie Bros. Auctioneers)

3-statement model built on the HII model template. It has the same tabs (`Model`, `Bull-Base-Bear`, `DCF`, `Charts`, `Sheet1`), section order, styling, scenario switch, CAGR columns and modelling-notes column. The structure is adapted to RB Global's reporting.

- **Historicals:** annual FY2006–FY2012, then quarterly Q1/13–Q2/26 (with 1H and FY columns), all from SEC EDGAR (CIK 0001046102):
  - Forms 40-F (2006–14) and 6-K (2013–15 quarterly releases).
  - Forms 10-K / 10-Q (2015+).
  - Form 8-K earnings releases (Ex. 99.1) for the non-GAAP reconciliations, GTV, lots and sector data.
  - Each period uses the latest filing that presents it. Every income statement, balance sheet and cash flow ties to the reported totals, and annual / quarterly revenue, net income, operating income, CFO, total assets and EPS were cross-checked against SEC XBRL company facts.
- **Reporting changes handled:**
  - **Accounting basis:** Canadian GAAP (2006–10), IFRS (2011–12 and 2013–14 quarters), US GAAP (FY2013–14 annuals as recast in the FY2015 10-K; 2015+).
  - **ASC 606 (2018, full retrospective):** the company's recast of 2017 is used; 2016 and earlier stay on the legacy net basis, with a memo row for the company's 2016 recast.
  - **Acquisitions and capital:** IronPlanet (2017), IAA (Mar-2023: one reportable segment, Series A Senior Preferred and two-class EPS), and the 2026 sector re-presentation (Automotive / HE&T / Other, recast from Q1/25).
- **Revenue build** (replaces HII's segment P&L, since RB Global reports a single segment): GTV by sector × service take rate, plus inventory sales (inventory % of GTV and inventory rate). The group KPIs are adjusted EBITDA and a model adjusted EBIT.
- **Bridges:**
  - GAAP net income → EBITDA → adjusted EBITDA → adjusted EBIT.
  - GAAP net income available to common → adjusted net income → diluted adjusted EPS.
  - Adjusting items follow the **company's definition in force in each period**. A definition row flags each change in the column where it takes effect (cell comments give the detail), and each adjusting-item cell carries the company's wording.
  - Model bridges tie to the company-published figures in every period except FY2013–14, where the EBITDA definition (operating income + D&A) differs by $2.5–4m, as annotated.
- **2026:** Q1/Q2 actual. Q3/Q4 = FY26 outlook from the Q2-26 release (GTV growth 9–11%, adjusted EBITDA $1,495–1,545m, tax 23–25%, capex $350–400m) less 1H actuals.
- **Scenario switch:** `Model!CT2` (Bull / Base / Bear). Scenario table at `Model!DB9:DF49`: Bull/Bear = Base + Δ, and the outlook block is high / mid / low. Levers: sector GTV growth, adjusted EBITDA margin and buybacks.
- **Valuation:** share price $80 (input per user, `Model` valuation row, 2026E).

Rebuild: `RECALC_SCRIPT=<path to recalc.py> python -m models.rba.build` (from the repo root). It needs LibreOffice Calc for recalculation and for the Bull/Bear snapshot values. Source data is in `models/data/rba/*.json` (extraction spec in `models/data/rba/README.md`).
