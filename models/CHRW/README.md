# C.H. Robinson (CHRW) — 3-statement model + RXO pro forma

`CHRW_Model.xlsx` is built on the MLM model template: same tab set, layout, colour conventions, scenario switch and GAAP→Adjusted bridges.

## Tabs

| Tab | Contents |
|---|---|
| **Model** | Annual history 2006–2012, then quarterly Q1/13–Q2/26; forecast Q3/26E–Q4/26E, 2026E and 2027E–2030E. Scenario switch in `CF2` (Bull / Base / Bear); scenario table in `CN:CR`. |
| **Bull-Base-Bear** | Live Base block plus Bull and Bear value snapshots (the Model run with the switch set to each case). |
| **DCF** | WACC build, unlevered FCF to 2035E, terminal value, WACC × g sensitivity, reverse DCF and Mauboussin EV/NOPAT. |
| **Charts** | Historical NAST volume vs. AGP per shipment; adjusted vs. GAAP operating income; ROIC / RONTA / margins. |
| **RXO PF** | RXO acquisition announced 5-Oct-2026 (see below). |

**Model tab, section by section**

- **Segment build:**
  - NAST: volume × AGP per shipment.
  - Global Forwarding: ocean volume × AGP per shipment.
  - All Other & Corporate: AGP growth.
- **Service-line AGP** history (truckload, LTL, intermodal, ocean, air, customs, other, sourcing, payment services).
- **Opex** = headcount × cost per head (Lean AI productivity lever) + other SG&A as % of AGP.
- **Statements:** GAAP P&L, cash flow and balance sheet, plus working capital, debt / buyback schedules, ratios and valuation.
- **Bridges** (company definitions, with check rows against published figures):
  1. GAAP gross profit → AGP
  2. Operating income → adjusted operating income
  3. Net income → EBITDA → adjusted EBITDA
  4. GAAP EPS → adjusted EPS
- **FY26 calibration:** Q3/26E–Q4/26E are calibrated to the scenario end-point of the FY26 adjusted operating income target ($964m–$1.04bn).

**RXO PF tab, section by section**

1. Consideration: $17.25 cash + 0.0856 CHRW shares per RXO share; $5.3bn equity / $5.8bn EV.
2. Sources & uses.
3. Illustrative purchase price allocation.
4. RXO standalone history (FY21–LTM Q2/26) and forecast.
5. Synergies ($300m net run-rate) and costs to achieve.
6. Pro forma P&L, shares, net debt and leverage; adjusted EPS accretion on the company deal definition, which excludes acquisition amortization and restructuring.
7. Cross-checks against company deal metrics (≈2.9x leverage at close; 1.75–2.25x by YE2028; "mid-teens accretive in 2028").
8. Accretion sensitivity grid.

## Sources

Everything comes from SEC EDGAR; the investor-relations releases are the same documents filed there.

- **CHRW (CIK 1043277):**
  - Form 8-K earnings releases (Ex. 99.1), 2006–Q2/26, each period as originally reported.
  - Ex. 99.3 segment recast (Jan-2017).
  - Q2/26 earnings deck (Ex. 99.2).
  - 10-K / 10-Q filings.
  - XBRL companyfacts (goodwill, retained earnings, AOCI, shares outstanding, dividends per share).
- **RXO (CIK 1929561):** 10-K / 10-Q filings and earnings releases.
- **Deal documents:** CHRW 8-K of 5-Oct-2026 (press release, merger agreement, investor presentation).

Row-level sources are in cell comments and the notes column (`CF`). The extracted datasets with per-value sources are in `data/`.

## Base case headlines (as built)

| | 2025A | 2026E | 2027E | 2028E | 2030E |
|---|---|---|---|---|---|
| Adjusted gross profit ($m) | 2,729 | 2,870 | 3,031 | 3,219 | 3,612 |
| Adjusted income from operations ($m) | 834 | 1,002 | 1,098 | 1,194 | 1,362 |
| Adjusted operating margin (% AGP) | 30.5% | 34.9% | 36.2% | 37.1% | 37.7% |
| Adjusted EPS ($) | 5.09 | 6.33 | 7.24 | 8.10 | 9.77 |

**RXO pro forma, Base case**
- Leverage: 3.0x at close (company: ~2.9x) and 2.1x at YE2028E.
- 2028E adjusted EPS: −3.8% vs. standalone including buybacks; −2.4% on the company-style comparison (no post-2026 standalone buybacks).
- Reaching the company's "mid-teens accretive" needs RXO adjusted EBITDA margin of ~5% and the full $300m synergies in 2028 (sensitivity grid, section 8).

## Rebuild

```bash
pip install openpyxl beautifulsoup4
cd models/CHRW/data
PYTHONPATH=../build python3 ../build/extract.py    # relp/*.json → data_rel.json  (needs rel_manifest.json)
PYTHONPATH=../build python3 ../build/compile.py    # → hist.json, hsrc.json, cols.json
PYTHONPATH=../build python3 ../build/build.py Base ../CHRW_Model.xlsx
```

Formulas need a recalculation pass (Excel does it on open). `build/pipeline.sh` regenerates the Bull and Bear snapshots; it uses LibreOffice (`libreoffice-calc`) for recalculation.
