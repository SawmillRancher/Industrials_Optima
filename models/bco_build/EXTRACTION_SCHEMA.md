# BCO data extraction: schema and rules

Per-period JSON written by `extract.py` to `data/<period>.json`, and the rules behind it. Derived from `models/templates/EXTRACTION_SCHEMA_TEMPLATE.md`; the sections differ from the template because Brink's statements come from XBRL and its releases carry quarterly tables for two years.

## Sources
- **SEC EDGAR only** (CIK 0000078890, The Brink's Company; The Pittston Company to May-2003). The IR site is blocked; its releases are the 8-K Ex. 99.1 exhibits.
- **Text versions** of every document are in `$BCO_SRC/txt`: one table row per line, cells joined by ` | `. File names embed `<date>_<form>_<accession>_<doc>`. A document's URL is `https://www.sec.gov/Archives/edgar/data/78890/<accession-no-dashes>/<doc>`. Those URLs go in `sources`.
- **XBRL company facts:** `$BCO_SRC/cf_78890.json`; the subset the extraction uses is committed as `data/_xbrl.json`.
- **Text quirks:**
  - A cell that was only ")" is dropped, so "(25,433" is negative.
  - "—" means zero.
- **EDGAR requests:** send a User-Agent and stay under 5 per second.

## Basis rules
- **Statements (`is`, `cf`, `bs`):** XBRL value **as first filed** in a 10-K / 10-Q for the period (= as originally reported), FY2009 onward. FY2006–08 are typed from the FY2008 10-K into `hand.json`.
  - `is`: the discrete quarter for Q1–Q3, or the full year. Q4 is not stored: `normalize.py` derives it as FY − Σ Q1–Q3.
  - `cf`: the **year-to-date** statement, with `ytd_months` 3, 6, 9 or 12. `cash_beg` / `cash_end` are the opening and closing balances as presented in that period's own filing.
  - `bs`: the period-end statement.
- **Recast quarters:** if the year-end release table shows a different GAAP operating profit from the first-filed quarter, the income statement takes the comparative filed in the following year's 10-Q, provided it ties to the release (±0.15). The record then carries `recast` with the reason and the originally reported figures. This applies to Q1/13–Q3/14.
- **Tag gaps and errors:**
  - Other operating income not tagged: derived as operating profit − revenues + total costs and expenses, noted.
  - Noncontrolling interests: always net income including NCI − net income attributable (the FY2014 NCI fact has the wrong sign).
  - The Venezuela deconsolidation loss is taken only for Q2/18 and FY2018.
- **Segments and non-GAAP (`seg`, `ngaap`):** the quarterly tables of the 8-K Ex. 99.1 releases.
  - Each year's quarters and full year come from that year's fourth-quarter release (1Q–4Q + full year columns).
  - Exceptions: 2013 from its own release on the International / North America layout; 2019 from the fourth-quarter 2020 release (prior-year columns, current four segments); 2026 from the third-quarter 2026 release.
  - Q4 records (`Q4-yy.json`) hold the three-month column of those tables only.
- **Growth tables (`growth`):** the "nQ'YY vs" table of each quarterly release, 2015 onward: prior-year amount, organic change, acquisitions / dispositions, currency, current amount, in whole $m.
- **Free cash flow (`fcf`):** the release reconciliation, year to date, with `ytd_months`.
- **Units:** USD millions to one decimal as published; shares in millions; per-share as published.
- **Signs:**
  - `is`: costs positive; `oth`, `ooi` and `disc` signed by their effect on income.
  - `cf`: XBRL signs (payments positive); `normalize.py` converts to cash-flow presentation.
  - `seg.op` item rows: signed by their effect on GAAP profit; `normalize.py` turns them into add-backs.
- **Null vs zero:** "—" = 0.0. A line not presented is omitted. **Nothing is estimated.** Every computed value is stated in `notes`.

## Output
One JSON file per period: `data/<period_key>.json`. Keys: `2006` … `2025`, `Q1-13` … `Q3-26`, and `Q4-13` … `Q4-25`.

```json
{
  "period": "Q3-26", "year": 2026, "quarter": 3,
  "sources": ["https://www.sec.gov/Archives/edgar/data/78890/.../bco-20260930.htm", "https://data.sec.gov/api/xbrl/companyfacts/CIK0000078890.json", "https://.../ex991q32026.htm"],
  "notes": ["..."],
  "is": {"rev": 0, "cor": 0, "sga": 0, "tce": 0, "ooi": 0, "op": 0, "int": 0, "ven_decon": 0, "oth": 0, "ebt": 0, "tax": 0,
         "cont": 0, "disc": 0, "pl": 0, "nci": 0, "ni": 0, "cont_att": 0, "disc_att": 0,
         "eps_d": 0, "eps_cont_d": 0, "eps_b": 0, "sh_d": 0, "sh_b": 0, "sh_ng": 0, "dps": 0},
  "cf": {"ytd_months": 9, "ni": 0, "da": 0, "sbc": 0, "def_tax": 0, "cfo": 0, "capex": 0, "acq": 0, "ppe_sale": 0, "cfi": 0,
         "buyback": 0, "div": 0, "div_nci": 0, "cff": 0, "fx": 0, "net": 0, "cash_beg": 0, "cash_end": 0},
  "bs": {"cash": 0, "rcash": 0, "ar": 0, "tca": 0, "rou": 0, "ppe": 0, "gw": 0, "intang": 0, "ta": 0, "stb": 0, "cltd": 0, "ap": 0, "accr": 0,
         "tcl": 0, "ltd": 0, "pension": 0, "opeb": 0, "lease": 0, "tl": 0, "eq": 0, "nci": 0, "teq": 0, "tle": 0, "shares": 0, "cash_cf": 0},
  "seg": [{"basis": "cur4 | three | mkts | intl2", "rev": [["exact label", 0]], "op": [["exact label", 0]]}],
  "ngaap": {"op": [["GAAP", 0], ["exact item label", 0], ["Non-GAAP", 0]], "inc": [], "eps": [], "ebitda": [], "rev": [], "da": [], "int": [], "oth": [], "tax": [], "nci": []},
  "ngaap_tot": {"rev": 0, "op": 0, "inc": 0, "eps": 0},
  "growth": [[["Revenues", "North America", [0, 0, 0, 0, 0]]]],
  "fcf": {"ytd_months": 9, "rows": [["exact label", 0]]},
  "recast": {"reason": "...", "original": {"rev": 0, "op": 0, "cont_att": 0}}
}
```
- `seg.basis`: `cur4` = North America / Latin America / Europe / Rest of World; `three` = North America / South America / Rest of World; `mkts` = nine reporting units of 2014–16; `intl2` = International / North America.
- `seg.op` runs from the segments through corporate and the non-GAAP total, then the other items not allocated to segments, to GAAP operating profit, in the order of the release table.
- `ngaap_tot` is used where the release reconciles in columns rather than rows (2009–13).

## Adjusting-item categories (`normalize.py`)
| Category | Company labels |
|---|---|
| `restr` | Reorganization and Restructuring |
| `acq` | Acquisitions and dispositions |
| `arg` | Argentina highly inflationary impact |
| `ven` | Venezuela operations; FX devaluation in Venezuela |
| `transf` | Transformation initiatives; NCR Atleos acquisition and transformation initiatives |
| `ret` | U.S. and Mexican retirement plans; Retirement plans (in operating profit to 2016) |
| `oth` | Reporting compliance, Internal loss, Chile antitrust matter, Change in allowance estimate, Ship loss matter, Non-routine auto loss matter, DOJ/FinCEN investigations, Incident-related losses, Non-routine legal matters, Share-based compensation adj.; the single total in 2009–14 |

The company's label and amount for every item are kept per period (`it_<cat>_lab`) and written as cell comments.

## Self-checks (`check_data.py`)
- Revenues − cost of revenues − SG&A + other operating income = operating profit; operating profit − interest + other − Venezuela loss = pre-tax income; pre-tax − tax = continuing operations; − NCI = attributable; + discontinued = net income.
- Release-table GAAP operating profit and income = the statements.
- Σ segments = segment revenues; Σ segment profit + corporate = non-GAAP operating profit (each basis).
- GAAP operating profit + items = non-GAAP operating profit; segment-table total = reconciliation total.
- Net income + interest + taxes + D&A = published EBITDA; + items = published adjusted EBITDA.
- Non-GAAP income ÷ diluted shares = non-GAAP EPS.
- Opening cash + CFO + CFI + CFF + FX = closing cash; total assets = total liabilities and equity; components sum to subtotals.
- Growth tables: prior + organic + acquisitions / dispositions + currency = current (±2 in whole $m), and current = segment revenue.
- Σ quarters = full year for segment, bridge and free-cash-flow series.
