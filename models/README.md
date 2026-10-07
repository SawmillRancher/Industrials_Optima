# Company models

Three-statement models built in the MLM template format (`builder/MLM_template.xlsx`):
Model (segment build → GAAP P&L → GAAP-to-adjusted bridges → cash flow → balance sheet →
schedules → ratios → valuation), Bull-Base-Bear, DCF and Charts.

| File | Company | Source documents |
|---|---|---|
| `LECO_Model.xlsx` | Lincoln Electric Holdings (Nasdaq: LECO) | SEC EDGAR CIK 0000059527 — 10-K / 10-Q, 8-K Ex. 99.1 earnings releases, 2016 segment-recast 8-K; XBRL company facts for cross-checks |

## Rebuilding

```
python3 builder/tools/dl.py 59527 <raw_dir>          # download filings (needs builder index.json)
python3 builder/tools/totext.py <raw_dir>            # HTML -> text
# per-period extraction -> builder/leco/extract/*.json (schema: builder/leco/SCHEMA.md)
python3 builder/tools/run_leco.py out/LECO_Model.xlsx   # needs LibreOffice for recalculation
```

`run_leco.py` builds the Bull and Bear cases, recalculates them with headless LibreOffice,
writes the value snapshots into the Bull-Base-Bear sheet, and injects cached values into the
final Base-case workbook. Every check row in the Model sheet must read 0.
