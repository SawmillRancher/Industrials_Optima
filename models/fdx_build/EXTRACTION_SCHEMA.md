# FDX data extraction: schema and rules

Derived from `models/templates/EXTRACTION_SCHEMA_TEMPLATE.md`. FedEx departs from the template in one way: extraction is **generic** (every table row is captured as published) and the mapping to model keys happens in `normalize.py`. This keeps 20 years of changing labels out of the extraction step and makes each record a faithful copy of the release.

## Sources
- **SEC EDGAR only** (CIK 1048911; no predecessor CIKs in the window). The IR site is blocked; its releases are the 8-K Ex. 99.1 exhibits.
- **Text versions** of every document are in `$FDX_SRC/txt`: one table row per line, cells joined by ` | `. File names embed `<date>_<form>_<accession>_<doc>`. A document's URL is `https://www.sec.gov/Archives/edgar/data/1048911/<accession-no-dashes>/<doc>`. Those URLs are recorded in `sources`.
- **Text quirks** (handled in `parse_release.py`):
  - A cell that was only ")" is dropped, so "(25,433" is negative.
  - "($ | 895" (an opening parenthesis in its own cell) is negative 895.
  - "—" means zero; "NM" is not a number.
  - Labels wrapped over two lines ("FedEx Express" / "segment | …") are rejoined.
  - Trailing footnote markers ("Other 1 ,") are removed.
- **Cross-check:** `$FDX_SRC/cf_1048911.json` (XBRL company facts); the subset used is committed as `data/_xbrl.json`.
- **EDGAR requests:** send a User-Agent and stay under 5 per second.

## Basis rules
Two bases, kept in separate records and never mixed:

| Basis | Record keys | Source |
|---|---|---|
| Legacy: fiscal years ended 31 May, FedEx Freight consolidated | `2006`–`2012` (annual), `Q1-13`–`Q4-26`, `FY13`–`FY26` | Each quarter's own release |
| Calendar: years ended 31 December, FedEx Freight in discontinued operations | `CQ1-24`–`CQ3-26`, `CY2024`, `CY2025`, `C9M-25`, `C9M-26` | Recast exhibits of 21-Jul-2026 and 28-Oct-2026; release of 28-Oct-2026 |

- **Quarters:** the three-month columns of that quarter's release, **as originally reported**. Q4 = the Q4 release's three-month column.
- **Annual records:** the Q4 release's twelve-month columns. **The Form 10-K wins** when it differs (FY2016 balance sheet, FY2023 balance sheet and cash flow, FY2025 balance sheet; listed in `extract.py` `TENK`).
- **Balance sheet:** the period-end statement.
- **Cash flow:** the **year-to-date** statement; `cf_ytd_months` is 3, 6, 9 or 12. Discrete quarters are derived in `normalize.py`.
- **Prior-year comparatives (`py`):** the prior-year column as presented in the same release (kept for reference; the model does not recast).
- **Units:** USD millions as published; package volumes and pounds in thousands per day; yields in USD; shares in millions; per-share as published.
- **Stock splits:** none in the window.
- **Signs:** as printed. Costs are positive in the income statement; cash flow as presented.
- **Null vs zero:** a line shown as "—" = 0.0. A line not presented is absent. **Never estimate.** Derived values are created only in `normalize.py` and noted in the model.

## Output
One JSON file per period in `models/fdx_build/data/`:

```json
{
  "period": "Q2-21",
  "basis": "legacy (fiscal year ended 31 May; FedEx Freight consolidated; as originally reported)",
  "sources": ["https://www.sec.gov/Archives/edgar/data/1048911/…/fdx-ex991_6.htm"],
  "filed": "2020-12-17",
  "notes": ["three-month columns of the release"],
  "is":  [["Revenue:", "FedEx Express segment", 10370.0], ["Operating Expenses:", "Fuel", 613.0], "…"],
  "exp": [["Average Daily Package Volume (000s):", "U.S. Deferred", 1380.0], "…"],
  "gnd": [["…", "…", 0.0]],
  "frt": [["…", "…", 0.0]],
  "bs":  [["Current Assets", "Cash and cash equivalents", 8256.0], "…"],
  "cf":  [["Operating Activities:", "Net income", 2471.0], "…"],
  "cf_ytd_months": 6,
  "recon": [{"head": "Second Quarter Fiscal 2021 / FedEx Corporation",
             "rows": [["GAAP measure", [1465.0, 7.1, 180.0, 1226.0, 4.55]],
                      ["TNT Express integration expenses", [48.0, 0.2, 12.0, 36.0, 0.13]],
                      ["Non-GAAP measure", [1513.0, 7.4, 203.0, 1303.0, 4.83]]]}],
  "py": {"is": [["Revenue:", "FedEx Express segment", 8943.0], "…"]}
}
```

- **Row format:** `[group, label, value]`. `group` is the sub-heading printed above the row (for example "Average Daily Package Volume (000s):"), which is what distinguishes a volume row from a yield row with the same label.
- **Table keys:**
  - `is`: consolidated income statement / financial highlights.
  - `bs`, `cf`: condensed balance sheet and cash flow.
  - `exp`, `tnt`, `gnd`, `frt`, `kin`, `fec`: legacy segment tables (FedEx Express, TNT Express, FedEx Ground, FedEx Freight, FedEx Kinko's, Federal Express).
  - `usd`, `intl`: Express U.S. Domestic and Express International (calendar basis).
  - `capex`: capital expenditures by asset type (recast exhibit).
- **`recon`:** every reconciliation table from "GAAP measure" to "Non-GAAP measure" (either order). Value columns are operating income, margin, [income taxes], net income, diluted EPS. Calendar records add `entity` (`corp`, `usd`, `intl`).

## Mapping (normalize.py)
- **Income statement:** a state machine over the rows (revenue → operating expenses → operating income → other income → bottom lines), so segment names can change freely.
- **Statistics:** matched by group and label; the legacy mapping of each service line is documented in the model's label comments.
- **Non-GAAP items:** categories by label: `restr` (realignment, optimization, separation, fiscal-year change), `acq` (TNT / GENCO integration), `impair`, `legal`, `mtm`, `other`. The reconciliation used for a period is the one whose GAAP side ties to that period's operating income, net income and EPS, which also converts the pre-FY2018 top-down tables (non-GAAP − charges = GAAP) to an additive convention.
- **Manual items:** `manual_items.json` holds the documented correction, balance-sheet detail from the 10-Q notes, FY2006–FY2010 dividends per share, guidance, deals, debt and the share price, each with a source URL.

## Self-checks (check_data.py)
- Σ expense lines = total operating expenses; revenue − expenses = operating income; Σ segments = consolidated (revenue and operating income).
- Operating income + other income = pre-tax income; − tax = income from continuing operations; + discontinued = net income; EPS ±0.10.
- Bridges: operating income + items = published adjusted operating income (±1.5); adjusted net income (±2); adjusted EPS (±0.10).
- Calendar statistics: volume × yield × days ÷ 1,000 = revenue (±1.2%); Σ service lines = segment revenue.
- Cash roll and CFO + CFI + CFF + FX; balance-sheet cash (+ restricted cash) = cash-flow ending cash; TA = TL&E.
- Σ quarters = year; XBRL cross-checks (operating income, net income, EPS, total assets, operating cash flow, as first filed).
