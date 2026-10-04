# Hermès International (Euronext Paris: RMS) — 3-statement model

`models/RMS_Model.xlsx` is built on the MLM model template. It keeps MLM's layout, cell styles, colour conventions
(blue = input, black = formula, green = cross-sheet link), check rows and scenario mechanics, adapted to Hermès'
reporting (IFRS, EUR, half-yearly financial statements).

## Sheets
| Sheet | Contents |
|---|---|
| Model | Métier revenue build → group revenue, quarterly revenue and geographic memo → profitability drivers → IFRS income statement → four IFRS→adjusted bridges → growth & margins → cash flow → buybacks → balance sheet → working capital → schedules (leases, net cash, shares) → ratios → valuation. Scenario switch in `BD2`; scenario input table in `BL:BP`. |
| Bull-Base-Bear | Live panel linked to the Model, plus value snapshots of the Model run with the switch on Bull and on Bear. |
| DCF | WACC, UFCF on recurring operating income, fade period and terminal value, implied ROIC, WACC × g sensitivity, reverse DCF, Mauboussin EV/NOPAT. |
| Charts | Constant-currency growth vs currency effect, EBITDA & recurring operating income with margins, returns profile (2009–2025). |

## Period coverage
- **FY2006–08:** key consolidated figures only (revenue, recurring operating income, operating income, net income, operating cash flows, capex, equity, net cash), from the 2010 registration document. No 2006–09 annual reports are on the IR site.
- **FY2009 onward:** full statements. FY2009 comes from the comparative column of the 2010 document.
- **Interim columns are half-years**, because Hermès publishes full financial statements only for H1 and FY:
  - H1 is as reported (2013 onward).
  - H2 = FY − H1 for flows; balances are the 31-Dec figures.
  - Q1–Q4 revenue (2014 onward) is shown in memo rows within the half-year columns.
- **H1/26** is actual (29-Jul-2026 report). **H2/26E, 2026E and 2027E–2030E** are forecast. Hermès gives no numeric guidance, so the forecast is driven by the scenario table.

## Hermès-specific adaptations vs MLM
- **Revenue build:** Hermès discloses no volumes or prices, so MLM's shipments × ASP build is replaced by a seven-métier build:
  - The métiers are Leather Goods & Saddlery, RTW & Accessories, Silk & Textiles, Other Hermès sectors, Perfume & Beauty, Watches and Other products. Tableware was a separate line until 2013 and is folded into Other Hermès sectors.
  - Each métier = prior period × (1 + constant-currency growth + currency effect).
  - The company's constant-currency growth is shown for every reported period, and the currency effect = reported − constant.
- **Profit:** Hermès reports profitability only by geographic area (IFRS 8 segments). So margins are modelled at group level, with a gross-margin lever and a recurring-operating-margin lever; sales & administrative expenses are the balancing line. Revenue and recurring operating income by area are a memo with sum checks.
- **Bridges.** Each has a "model vs published (should be 0)" check against every period Hermès published:
  1. **Net income → operating income → recurring operating income → EBITDA**, with EBITDA after lease payments for a pre-IFRS 16 comparable figure. ROI is checked against the published figure; EBITDA is a model measure.
  2. **Net income → recurring net income / recurring EPS**, which excludes:
     - non-recurring items after tax: the 2018 HK property gain of €52.7m and the 2020 Shang Xia deconsolidation of €91.1m, both untaxed;
     - French exceptional tax items: the 2017 surtaxes net (€20m) and the 2025 exceptional contribution (€331m; H1/25 and H1/26 estimated from the disclosed tax rates).

     It is checked against Hermès' "net income excluding the exceptional contribution" (2025, H1/25, H1/26), which is published rounded to €0.1bn / €0.01bn.
  3. **Operating cash flows → adjusted free cash flow**, Hermès' APM (free cash flow in 2018).
  4. **Cash → net cash → restated net cash**, Hermès' APM.
- **Capital allocation:** Hermès has net cash and no financial debt. So MLM's debt schedule is replaced by:
  - a lease (IFRS 16) schedule;
  - net-cash yield for financial income;
  - levers for payout, exceptional dividends and buybacks.

## Sources
Hermès International is not an SEC registrant. On EDGAR it has only ADR registrations on Form F-6 (CIK 0001450490 and 0001436949), with no 10-K, 10-Q or 8-K filings. All data therefore comes from finance.hermes.com (documents filed with the AMF), extracted into `models/data/rms/*.json` (schema: `SCHEMA.md`):
- Registration documents and Universal Registration Documents: annual financial reports FY2010–FY2025.
- Half-year financial reports, H1 2013–H1 2026.
- Half-year and full-year results releases, and quarterly revenue releases (Q1 2014–Q2 2026).
- Share price: €1,299.50, Euronext close 2-Oct-2026 (quote feed on finance.hermes.com). It is a user-updatable input in the Valuation block.

Source notes are attached as cell comments on the row labels and in the Modelling Notes column.

## Rebuild
```
RECALC_SCRIPT=<xlsx skill>/scripts/recalc.py python3 -m models.rms.build    # from the repo root
```
Requires `openpyxl` and LibreOffice Calc (`libreoffice-calc`). The build writes the Base case, recalculates, runs Bull and Bear to fill the snapshot panels, then recalculates again.
