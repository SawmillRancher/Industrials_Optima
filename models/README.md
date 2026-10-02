# Company models

## `HII_Model.xlsx` — Huntington Ingalls Industries (NYSE: HII)

3-statement model rebuilt on the DSV template layout (tabs: `Model`, `Bull-Base-Bear`, `DCF`, `Charts`, `Sheet1`).

- **Historicals (Q1/15 – Q2/26):** SEC filings only — 10-K / 10-Q XBRL financial data (latest filing reporting each period; Q4 = FY − 9M) and Form 8-K earnings releases (Ex. 99.1) for non-GAAP reconciliations, Q4 share counts and FY26 guidance. Backlog from the 10-K/10-Q MD&A tables.
- **Segments:** Ingalls Shipbuilding, Newport News Shipbuilding, Mission Technologies (Technical Solutions pre-2022), plus corporate / eliminations (Operating FAS/CAS adjustment, non-current state income taxes).
- **Bridges (below the GAAP income statement):** GAAP operating income → segment operating income (adj. EBIT) → adjusted segment OI; GAAP net earnings → adjusted net earnings / adjusted EPS (with HII-published adjusted figures for 2015–21).
- **2026:** Q1/Q2 actual; Q3/Q4 = FY26 guidance (Q2-26 release) less 1H actuals, split evenly. 2026E FCF calibrated to guidance via contract assets.
- **Scenario switch:** `Model!CA2` (Bull / Base / Bear). Scenario input table at `Model!CH9:CK…` — Bull/Bear = Base + Δ; FY26 guidance block = high / mid / low.
- **Valuation:** current share price $275 (input on `Model` valuation row, 2026E).
