# UNP data extraction: schema and rules

## Sources
- **SEC EDGAR only** (Union Pacific Corporation, CIK 0000100885; one registrant throughout). The IR site (up.com/investor) is blocked from the build environment; its releases are the Form 8-K Item 2.02 Ex. 99.1 exhibits.
- **Text versions** of every document are in `$UNP_SRC/txt`: one table row per line, cells joined by ` | `. File names embed `<date>_<form>_<accession>_<doc>`. A document's URL is `https://www.sec.gov/Archives/edgar/data/100885/<accession-no-dashes>/<doc>`; `filings.csv` indexes the filings.
- **Text quirks:** a cell that was only ")" is dropped, so "(25,433" is negative; "—", "-" and "---" are zero; "F" / "U" / "N/A" are placeholders. Labels split over two lines ("Total operating" / "revenues | …") are re-joined by `parse_release.join_lines`.
- **Cross-check:** `$UNP_SRC/companyfacts.json` (XBRL company facts; subset committed as `data/_xbrl.json`).
- **EDGAR requests:** User-Agent on every request; under 5 per second.

## Basis rules
- **Quarters:** income statement, freight statistics (business groups), operating statistics and non-GAAP tables come from that quarter's own release, three-month columns, **as originally reported**. Q4 = the Q4 release's fourth-quarter column (always printed).
- **Balance sheet:** the period-end statement of the release (condensed: cash, short-term investments, other current assets, investments, properties, operating lease assets (2019–25), other assets; debt due within one year, other current liabilities, debt due after one year, operating lease liabilities (2019–25), deferred income taxes, other long-term liabilities, equity).
- **Cash flow:** the **year-to-date** statement (`cf.ytd_months` 3 / 6 / 9 / 12); discrete quarters are derived in `normalize.py`.
- **Annual records:** the Q4 release twelve-month columns. The 10-K wins where it differs (none found 2009–25; 2006–07 expense lines are taken from the FY2008 10-K re-presentation, see `manual_items.json` `recast_2006_2007`).
- **Prior-year comparatives (`py`, `seg_py`, `ops_py`):** the prior-year columns of the same release. Used for the 2018 business groups on the Bulk / Industrial / Premium basis (from the 2019 releases, flagged recast).
- **Units:** USD millions as published (2006–07 commodity revenue in $000 ÷ 1,000; carloads in units ÷ 1,000 to thousands); shares in millions; per-share as published; percentages as numbers (59.1 = 59.1%); gross ton-miles in millions (2006 "billions" × 1,000).
- **Signs:** costs positive (interest expense and income taxes are shown in parentheses in the releases and stored positive); other income signed (income +); cash flow as presented.
- **Null vs zero:** "—" = 0.0; a line not presented is absent. Never estimate. Computed values are stated in `notes` / `manual_items.json`.
- **Stock splits:** 2-for-1 on 27-May-2014 (record date 27-May-2014). Shares, EPS and DPS before Q2-14 are published pre-split; `normalize.py` restates them by the filing date of each source (× 2 shares, ÷ 2 per share for documents filed before 9-Jun-2014).

## Output
One JSON per period in `data/`: `Q1-06` … `Q3-26` (quarters) and `2005` … `2025` (years).

```json
{
  "period": "Q3-26", "period_end": "2026-09-30",
  "sources": {"release": "https://...", "release_date": "2026-10-22", "10-Q": "https://..."},
  "is":  {"frt", "oth_rev", "rev", "comp", "fuel", "psm", "dep", "rents", "oth_exp", "opex", "oi", "oth_inc", "int", "ebt", "tax", "ni",
          "eps_b", "eps_d", "sh_b", "sh_d", "dps", "or", "etr", "mats (2006-07)"},
  "is_ytd": {"same keys, year-to-date column"},
  "py":  {"is": {"same keys, prior-year quarter as presented"}},
  "seg": {"<group>": {"rev", "cars", "arpc", "label"}},     // groups: ag, auto, chem, energy, indprod, intermodal (2006-17); ag, energy, industrial, premium (2018);
                                                             // bulk, industrial, premium + grain, fert, food, coalren, chemplas, metals, forest, energyspec, auto, intermodal (2019+/2020+); total
  "seg_py": {"prior-year comparatives, same layout"},
  "ops": {"gtm", "emp", "fuel_px", "gallons", "fuel_rate", "rtm", "speed", "dwell", "car_inv", "velocity", "train_len", "wf_prod", "loco_prod", "carloads", "sh_b", "sh_d"},
  "ops_py": {"prior-year comparatives"},
  "bs":  {"cash", "sti", "oca", "inv", "ppe", "rou", "oa", "ta", "std", "ocl", "ltd", "olease", "dtl", "oltl", "tl", "eq", "tle"},
  "cf":  {"ytd_months", "ni", "dep", "dtax", "oth_op", "cfo", "capex", "sti_buy", "sti_mat", "oth_inv", "cfi", "bb", "div", "debt_iss", "debt_rep", "debt_exch",
          "oth_fin", "cff", "net", "beg", "end", "fcf", "<key>_py"},
  "ngaap": {"fp": [{"context", "orientation", "measures": {"oi|opex|tax|ni|eps|or|oth_inc": {"gaap", "adj"}}, "items": [{"label", "<measure>": delta}]}],
            "adj_ebitda_ttm", "ebitda_ttm", "adj_debt", "lease_liab", "lease_int_ttm", "roic_pub", "adj_lev_pub", "debt_cap_pub", "adj_debt_cap_pub", "debt_pub"},
  "extra": {"fuel_surcharge_rev", "fuel_surcharge_rev_py", "fuel_surcharge_src"},
  "notes": []
}
```

## Adjusting items
The company's "Financial Performance" tables (items identified as affecting comparability) are curated per period in `manual_items.json` → `adjusted_items` with categories: ACQ (acquisition-related expense, Norfolk Southern), IMPAIR (Brazos Yard 2020), GAIN (intermodal equipment 2024, industrial park land sales 2025 — other income), OTHER (labor accrual 2022, environmental remediation 2024, crew staffing agreements 2024–25), TAXREFORM (2017 equity-method affiliates remeasurement), TAXD (2017 deferred-tax remeasurement, 2025 deferred tax adjustment). The parsed `ngaap.fp` tables are the audit trail.

## Self-checks (check_data.py)
- IS: revenues − total operating expenses = operating income; OI + other income − interest = pre-tax; pre-tax − tax = net income; Σ expense lines = total; NI ÷ diluted shares = EPS (±0.01).
- Freight: Σ groups = total freight revenue (±1); carloads × ARPC ≈ revenue (±1%).
- Σ quarters = fiscal year for every income-statement line and business group (±1.5).
- Cash flow: CFO + CFI + CFF = net change; beginning + change = end; BS cash (+ restricted cash from 2018) = CF ending cash.
- Balance sheet: components = total assets = total liabilities and equity.
- XBRL: revenues, operating income, net income, EPS, CFO, total assets, cash vs company facts (first-filed 10-K / 10-Q).
