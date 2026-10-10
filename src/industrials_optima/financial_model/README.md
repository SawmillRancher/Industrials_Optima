# Industrial Financial Model Template

A parameterized 3-statement model + scenarios + DCF + charts, modeled on
the Moog Inc. workbook supplied as the reference. The generator strips
all hardcoded historical values from the base template, parameterizes
labels (company name, ticker, segment names, DCF inputs, current share
price), preserves every formula and format, and emits a ready-to-populate
`.xlsx`.

## Tabs

| Tab               | Purpose                                                                 |
|-------------------|-------------------------------------------------------------------------|
| `Model`           | Segment P&L (legacy + current), I/S, CF, BS, forecast schedules, ratios |
| `Bull-Base-Bear`  | Scenario P&L summary linked to `Model!` cells                           |
| `DCF`             | WACC build, UFCF, terminal value, sensitivity, reverse DCF              |
| `Charts`          | Historical operating performance charts linked to `Model!` cells        |

## Column structure (preserved exactly so cross-sheet refs keep resolving)

`Q1/10` is column **C**; subsequent quarters fill four columns and an FY
total occupies the fifth, so `FY10 = G`, `FY11 = L`, … `FY25 = CD`,
`FY26E = CI`, … `FY30E = CM`. The forecast period runs `CI–CM`.

## Build a template

```bash
python -m industrials_optima.financial_model.cli \
  --company "Acme Industries" \
  --ticker  "ACME" \
  --segment "Aerospace Systems" \
  --segment "Defense Electronics" \
  --segment "Space and Satellites" \
  --segment "Industrial Automation" \
  --legacy-segment "Aerospace" \
  --legacy-segment "Defense" \
  --legacy-segment "Industrial" \
  --share-price 150.0 \
  -o Acme_Model.xlsx
```

Or programmatically:

```python
from industrials_optima.financial_model import CompanyConfig, SegmentLine, build_template

cfg = CompanyConfig(
    company_name="Acme Industries",
    ticker="ACME",
    current_share_price=150.0,
    segments_current=[
        SegmentLine("Aerospace Systems"),
        SegmentLine("Defense Electronics"),
        SegmentLine("Space and Satellites"),
        SegmentLine("Industrial Automation"),
    ],
)
build_template(cfg, "Acme_Model.xlsx")
```

## Populating from SEC filings

1. Open the generated template; go to the **Model** tab.
2. **Historicals (columns C–CD)** are blank. Drop in line items from the
   10-K / 10-Q filings:
   - Segment P&L blocks (rows 11–95): Net sales, EBIT, backlog per segment
   - Consolidated I/S (rows 114–139): from the company's income statement
   - Cash flow (rows 175–207): from the company's cash flow statement
   - Balance sheet (rows 226–261): from the company's balance sheet
3. **Forecast (columns CI–CM)** computes automatically from the scenario
   assumption tables at `CT56:CY85` (Base / Bull / Bear by segment).
4. Toggle scenarios via `Model!CO3` (`Base` / `Bull` / `Bear`).
5. **Bull-Base-Bear**, **DCF**, and **Charts** tabs are linked — they
   refresh whenever Model values change.

### TFI International auto-populate (FY19–FY25 annual + FY21Q3–FY25Q3 quarterly)

For TFI International specifically, the `populate_tfi` module pulls
historicals from the EDGAR IFRS XBRL Company Facts API (CIK 0001588823),
the per-filing "Segment Reporting (Details)" rendered R-files, and the
quarterly 6-K MD&A exhibits, then stamps the full set into the annual
(BE/BJ/BO/BT/BY/CD) and quarterly (BF–CC) columns:

- Consolidated IS / CF / BS (~47 line items per year, FY19–FY25; FY19
  is included so the source template's row 161–164 / row 211 y/y%
  formulas at FY20 have a populated prior-year cell to divide by)
- Per-segment Net sales + Operating profit:
  - **Legacy block** (4 segments, FY19–FY23): Package and Courier,
    Less-Than-Truckload, Truckload, Logistics
  - **Current block** (3 segments, FY24–FY25): Less-Than-Truckload,
    Truckload, Logistics — Package and Courier was rolled into LTL in
    the FY24 40-F (confirmed by the FY23 restated comparative, where
    LTL revenue jumped ~$580M = prior-year P&C)
- Formula completions (y/y%, margins, ratios) wherever the source
  Moog template left a gap or pointed at a TFI-irrelevant row:
  - Backfilled legacy block Sales y/y% and Op margin % for FY22/FY23
  - Cross-block FY24 overrides on the current block (Sales y/y%,
    EBIT y/y%, Incremental EBIT, Group totals) so the comparison
    against FY23 references the legacy block, with legacy P&C added
    back to LTL where applicable
  - Repointed Adj EBIT % / Incremental OP margin from row 148 (Adj
    operating profit, unpopulated since TFI doesn't disclose a GAAP→
    Adj bridge) to row 126 (GAAP EBIT)
  - Backlog y/y%, book-to-bill, gross margin %, R&D %, SG&A %, DIO,
    DPO are intentionally left blank — TFI is a logistics business
    and either the metric isn't reported or the underlying line item
    isn't in the IFRS taxonomy

Build then populate:

```bash
python -m industrials_optima.financial_model.cli \
  --company "TFI International" \
  --ticker  "TFII" \
  --segment "Less-Than-Truckload" \
  --segment "Truckload" \
  --segment "Logistics" \
  --legacy-segment "Package and Courier" \
  --legacy-segment "Less-Than-Truckload" \
  --legacy-segment "Truckload" \
  --legacy-segment "Logistics" \
  --currency-units "millions (USD)" \
  --basis "IFRS as filed in Form 40-F" \
  --tax-rate 0.26 \
  --share-price 150.0 \
  -o TFI_Model.xlsx

python -m industrials_optima.financial_model.populate_tfi TFI_Model.xlsx \
  --facts-cache /tmp/tfi_facts.json \
  --segment-cache /tmp/tfi_segs
```

The `--facts-cache` / `--segment-cache` paths memoize EDGAR responses
so a re-run is offline; sequential R-file fetches are throttled and
back off on 503.

Known issuer-tagging quirks the populator preserves as-is (see
`populate_tfi.py` docstring): FY24 `CashAndCashEquivalents` tagged as
0; FY21/FY22 `FinanceCosts` sign-flipped (abs() applied); standalone
`Goodwill` only tagged through FY22 (FY23+ rolls into the combined
`IntangibleAssetsAndGoodwill` total).

Additional sections populated below the main model area:

- **Q1/26 operational baseline** (rows 432–484): full set of disclosed
  KPIs per segment from TFI's Q1/26 MD&A, with Q1/25 comparative.
- **Driver forecast** (rows 488–548): per segment × scenario,
  Volume y/y% × Yield y/y% → Implied Sales y/y%, plus EBIT margin
  anchored to LT targets.
- **LT margin anchors** (rows 552–560): publicly-stated Bédard targets
  (LTL 15% op margin / 85% Adj OR; TL ~12%; Logistics ~9–10%). NOT
  verbatim from Q1/26 call (egress allowlist blocks transcript hosts).
- **FX reference** (rows 580–599): Bank of Canada CAD/USD annual
  averages FY11–FY25 (IEXE0101 + FXUSDCAD stitched). For normalizing
  any pre-FY20 CAD figures manually entered from SEDAR.
- **Per-segment operational KPIs by quarter** (rows 605–650): rev/cwt,
  shipments, tonnage, truck count, OR%, ROIC parsed from each quarterly
  MD&A's per-segment narrative. FY21Q3 → FY25Q3 coverage.

Forecast wiring (toggle scenario at `Model!CO3` = Base / Bull / Bear):

- IS, CF, BS forecast all compute end-to-end through FY30E
- BS ties out exactly ($0 gap) via cash-as-literal-plug at row 226
  (Cash = Total L&E − sum of non-cash assets)
- Buybacks (row 199) scale dynamically as 30% of FCF, capped at the
  FY25 actual run-rate
- Dividends (row 198) computed from DPS × diluted shares, with DPS
  growing 4%/yr (TFI's announced Q1/26 dividend hike)
- Corporate cost ramps 3%/yr off the FY25 segment-vs-consolidated
  EBIT gap
- All ratio + valuation multiples compute (ROIC, RONTA, ROE, Net
  debt/EBITDA, interest coverage, EV/Sales, EV/EBITDA, EV/EBIT,
  P/E, FCF yield, dividend yield)

Known gaps:

- **FY11–FY18 historicals**: NOT auto-populated. EDGAR has TFI data
  only from FY19 (cross-listing on NYSE was late 2020). Pre-FY19
  filings live on SEDAR which is blocked by the egress allowlist in
  this environment. The FX section at row 580+ provides the BoC
  CAD/USD rates for manual normalization if you obtain the data.
- **FY20Q1, FY20Q2, FY21Q1**: no MD&A exhibit on EDGAR for these
  quarters (TFI's earliest quarterly MD&A is FY21Q3).
- **TFI doesn't disclose**: Cost of sales / Gross profit / R&D / SG&A
  (IFRS uses Materials & services / Personnel / Other op / D&A
  instead -- those are populated); GAAP→Adjusted bridge components
  (rows 142–159 stay blank); Backlog / Book-to-bill (not a logistics
  metric); DIO / DPO (no COGS to divide against).

## Notes

- The Moog file lives at `templates/base_model.xlsx` and is the structural
  source of truth. Re-run `build_template` whenever the base changes.
- The `Modeling Comments & Assumptions` column (`CQ`) is intentionally
  left blank — write your own notes there as you build the model.
