# VMC model build kit

`models/VMC_Model.xlsx` is the Vulcan Materials (NYSE: VMC) three-statement model. It is built on the TDY template layout: the same columns (FY2006–12 annual, quarterly from Q1/13, Q3/26E–Q4/26E, 2026E–2030E), the same formatting, a Bull / Base / Bear switch in `Model!CT2`, and the same Bull-Base-Bear, DCF and Charts tabs.

## Sources
Every historical input comes from SEC EDGAR: Forms 10-K and 10-Q, plus the Form 8-K earnings releases (Ex. 99.1). Vulcan's current CIK is 0001396009; before Nov-2007 it filed as legacy Vulcan, CIK 0000103973. The source document for each period is listed under `sources` in `data/<period>.json`, and `filings.csv` indexes every filing used.

- **Basis:** all periods are shown as originally reported.
- **Q4:** taken from the three-month column of each Q4 release.
- **FY2006–12:** from that year's 10-K.
- **FY26 guidance:** `data/outlook.json` holds the Q4-25 / Q1-26 / Q2-26 guidance, the projected Adjusted EBITDA bridge and the debt ladder.

## Rebuild
1. Place the TDY template as `TDY_Model.xlsx` next to these scripts.
2. Run `python3 build.py --snap`. This builds the model, then reruns it with the switch on Bull and on Bear to refresh the snapshot columns in the Bull-Base-Bear tab. It needs `openpyxl` and LibreOffice Calc. Set the `XLSX_RECALC` environment variable to the path of a LibreOffice recalculation script.
3. Run `python3 inspect_model.py <recalculated.xlsx>`. It lists every check row that is not zero.

## Files
- `fw.py`: column map, style cloning from the template's row archetypes, and the row registry.
- `spec.py` and `spec2.py`: the Model row specification: segment build, income statement, the three GAAP→adjusted bridges, cash flow, balance sheet, schedules, ratios and valuation.
- `build.py`: writes the scenario table and the Model sheet, the scenario snapshots, and the recalculation driver.
- `other_sheets.py`: rewires the Bull-Base-Bear, DCF and Charts tabs, and re-injects the template chart XML, including the bar + line combo chart.
- `normalize.py`: harmonises the extraction JSON (for example Vulcan's discontinued-ops treatment in its EBITDA build, and per-share Adjusted EPS bridges) and runs the cross-checks.
- `h2t.py` and `EXTRACTION_SCHEMA.txt`: the EDGAR HTML→text converter and the field schema used for extraction.
