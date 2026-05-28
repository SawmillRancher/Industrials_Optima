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

### TFI International auto-populate (FY20–FY25)

For TFI International specifically, the `populate_tfi` module pulls
historicals from the EDGAR IFRS XBRL Company Facts API (CIK 0001588823)
and the per-filing "Segment Reporting (Details)" rendered R-files, and
stamps them into the FY20–FY25 columns (BE / BJ / BO / BT / BY / CD):

- Consolidated IS / CF / BS (~47 line items per year)
- Per-segment Net sales + Operating profit:
  - **Legacy block** (4 segments, FY20–FY23): Package and Courier,
    Less-Than-Truckload, Truckload, Logistics
  - **Current block** (3 segments, FY24–FY25): Less-Than-Truckload,
    Truckload, Logistics — Package and Courier was rolled into LTL in
    the FY24 40-F (confirmed by the FY23 restated comparative, where
    LTL revenue jumped ~$580M = prior-year P&C)

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

## Notes

- The Moog file lives at `templates/base_model.xlsx` and is the structural
  source of truth. Re-run `build_template` whenever the base changes.
- The `Modeling Comments & Assumptions` column (`CQ`) is intentionally
  left blank — write your own notes there as you build the model.
