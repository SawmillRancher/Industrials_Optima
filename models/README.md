# Company models

Three-statement models built in the MLM template format (`builder/MLM_template.xlsx`):
Model (segment build → GAAP P&L → GAAP-to-adjusted bridges → cash flow → balance sheet →
schedules → ratios → valuation), Bull-Base-Bear, DCF and Charts.

| File | Company | Source documents |
|---|---|---|
| `LECO_Model.xlsx` | Lincoln Electric Holdings (Nasdaq: LECO) | SEC EDGAR CIK 0000059527 — 10-K / 10-Q, 8-K Ex. 99.1 earnings releases, 2016 segment-recast 8-K; XBRL company facts for cross-checks |
| `ESAB_Model.xlsx` | ESAB Corporation (NYSE: ESAB) | SEC EDGAR CIK 0001877322 — Form 10 information statement (2019–21 carve-out), 10-K / 10-Q, 8-K Ex. 99.1 earnings releases, Eddyfi deal 8-Ks and 8-K/A (Ex. 99.1–99.3); Colfax 10-Ks (CIK 0001420800) for the 2012–21 pre-spin segment memo |

## Rebuilding

```
python3 builder/tools/dl.py 59527 <raw_dir>          # download filings (needs builder index.json)
python3 builder/tools/totext.py <raw_dir>            # HTML -> text
# per-period extraction -> builder/leco/extract/*.json (schema: builder/leco/SCHEMA.md)
python3 builder/tools/run_leco.py out/LECO_Model.xlsx   # needs LibreOffice for recalculation
python3 builder/tools/run_esab.py out/ESAB_Model.xlsx   # ESAB data: builder/esab/extract (+ builder/colfax/extract)
```

`run_leco.py` builds the Bull and Bear cases, recalculates them with headless LibreOffice,
writes the value snapshots into the Bull-Base-Bear sheet, and injects cached values into the
final Base-case workbook. Every check row in the Model sheet must read 0.
