# <TICKER> model build kit

<!-- Copy to models/<ticker>_build/README.md and replace every <…>. Delete sections that don't apply. -->

`models/<TICKER>_Model.xlsx` is the <Company legal name> (<EXCHANGE>: <TICKER>) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!<col>2`, scenario table in `Model!<cols>`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT).
  - Charts.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer.

## Columns (fiscal year ends <date>)
- **<C–I> FY<yyyy>–<yyyy>:** annual, <basis>.
- **<J–…> Q1/<yy>–Q<n>/<yy> with FY subtotals:** grouped and collapsed like the template.
- **<…> Q<n>/<yy>E–Q4/<yy>E, <…> <yyyy>E:** forecast, calibrated to the FY<yy> outlook.
- **<…> <yyyy>E–<yyyy>E:** scenario forecast.
- **Right of the forecast** (template column − <shift>): <col> notes, <cols> CAGRs, <cols> scenario table.

## Basis
- **Policy:** <as originally reported / hybrid recast / latest filing presenting the period>.
- **Recasts and discontinued operations:** <list, with dates and how each is handled; recast cells carry comments>.
- **Segments as reported per year:** <structure by period; legacy structures kept as memo rows>.
- **Per-share data:** <split / share-class adjustments>.
- **Cash flow:** quarters derived from year-to-date (Q4 = FY − 9M).

## Model structure (Model tab)
- **Operating build:** <segments / product lines / end markets / regions; drivers (volume × price, organic + M&A + FX)>.
- **Acquisition blocks:** <deal, closing date, consideration, PPA, synergies, toggle; flag undisclosed assumptions>.
- **Future M&A lever:** spend ÷ EV/sales, margin, PP&E / intangibles / goodwill split, amortization.
- **FY<yy> outlook calibration:** <revenue Δ solves FY revenue to guidance end-point (<low / mid / high>); margin Δ solves <anchor KPI> to <low / mid / high>; information rows that are not forced>.
- **GAAP P&L from the build:** <how GAAP OI is derived; implied line; interest; tax>.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **Net income → EBITDA → Adjusted EBITDA:** <company / model definition>.
  2. **GAAP operating income → adjusted operating income:** <definition>.
  3. **GAAP net income → adjusted net income → adjusted EPS:** <definition in force per period; changes flagged in the definition row>.
- **Other schedules:** cash flow; buybacks; balance sheet; working capital; PPAs; debt (<maturities, revolver / CP to minimum cash>); leverage-target buybacks (<floor>); ratios and valuation.
- **DCF basis:** <NOPAT basis, lease treatment, opening invested capital, currency>.

## Key forecast assumptions (Base)
- <growth, margins, M&A, synergies, buybacks, tax, capex — each with its source or "assumption">

## Data corrections
- <period: what was published, why it is wrong, what the model uses (also in `manual_items.json`)>

## Sources
SEC EDGAR only (CIK <##########>):
- Forms 10-K / 10-Q <years>.
- Form 8-K earnings releases (Ex. 99.1) <range>.
- Deal 8-Ks / S-4 / 424B3 / 424B4 <list>.
- XBRL company facts for <items>.

The investor-relations site (<host>) is blocked from the build environment; its releases are the same documents as filed on EDGAR. `filings.csv` indexes the filings, and each `data/<period>.json` lists its source URLs. `manual_items.json` holds <guidance, PPAs, debt facts, amortization schedule, corrections>.

The share price (<$x>, <close date>) is an input at `Model!<col>` in the valuation block; update it to market.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export <TICKER>_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`.
   3. `python3 check_data.py` runs the statement-arithmetic, segment, bridge, quarter-sum, cash and balance-sheet checks. Known exceptions: <list or "none">.
3. Build: `python3 build.py --snap --recalc` writes `../<TICKER>_Model.xlsx`, reruns with the switch on Bull and Bear to fill the snapshot panels, and stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py <file>` should show 0 error cells and 0 non-zero check rows.
   - `python3 ../tools/cyc.py <file>` should show 0 cycles.
   - Intentional exceptions: <e.g. Charts #N/A for years without a balance sheet>.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs, compute engine, scenario table, definition flags, column layout.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `h2t.py`, `make_index.py`, `fetch.py`, `parse_release.py`, `extract.py`: EDGAR HTML → text, filings index, downloads, release parser, per-period extraction.
- `xbrl.py`: XBRL company-facts helper.
- `normalize.py`: basis rules, flat model keys, discrete quarterly cash flow, split / share-class adjustments.
- `check_data.py`: data consistency checks.
