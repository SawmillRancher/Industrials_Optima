# NSC data extraction: schema and rules

## Sources
- **SEC EDGAR only** (CIK 0000702165; Union Pacific CIK 0000100885 for the UNP share price). The IR site is blocked; its releases are the 8-K exhibits.
- **Documents** are downloaded by `fetch.py` into `$NSC_SRC/docs` (names embed `<date>_<form>_<accession>_<doc>`) with text versions in `$NSC_SRC/txt`. A document's URL is `https://www.sec.gov/Archives/edgar/data/702165/<accession-no-dashes>/<doc>`.
- **Release structure:** every earnings 8-K carries a press release and a financial-statements exhibit (named `financials…`, `FinancialStatements`, `ex99-2` / `ex99_2` by era). The statements exhibit holds the income statement (revenues by commodity group, expenses by classification), balance sheet, year-to-date cash flow and notes; the press release holds the non-GAAP reconciliation when items exist.
- **MD&A tables** (10-Q / 10-K): revenues, units and revenue per unit by market group; coal tonnage by market; intermodal units by market; expenses by classification; fuel surcharge revenue in the narrative.
- **EDGAR requests:** send a User-Agent and stay under 5 per second.

## Basis rules
- **Quarters:** income statement from that quarter's release (three-month column), **as originally reported**; Q4 from the fourth-quarter release three-month column (2006–12 releases print separate three- and twelve-month statements; 2013+ one statement with quarter and year columns).
- **Annual:** the fourth-quarter release twelve-month columns plus that year's 10-K (market groups, maturities). FY2006–07 expense classifications: FY2008 10-K recast (`is_recast`).
- **Balance sheet:** the period-end statement. **Cash flow:** year to date, `cf.ytd_months` = 3 / 6 / 9 / 12.
- **Market groups:** 10-Q quarter column; 10-K annual; Q4 = year − nine months for revenues and units (noted), revenue per unit derived.
- **Prior-year comparatives (`py`):** the prior-year column of the same release; compared with the original record by `check_data.py` (restatements are reported, not applied).
- **Units:** USD millions (releases print millions; 2006–07 share counts in thousands → millions); units in thousands; revenue per unit in $; per-share as published.
- **Signs:** costs positive; "Eastern Ohio incident" and "Restructuring and other charges" as printed (negative = net recovery / reversal); cash flow as presented.
- **Null vs zero:** "—" = 0.0; a line not presented = absent. **Never estimate.** Derived values are stated in `notes`.

## Output
One JSON file per period: `data/<period>.json` (`2006` … `2025`, `Q1-13` … `Q3-26`).

```json
{
  "period": "Q3-26", "fy": 2026, "q": 3,
  "sources": {"release": "…", "release_date": "YYYY-MM-DD", "filing": "…", "press": ["…"]},
  "is": {"rev_coal": null, "rev_merch": null, "rev_im": null, "rev": null,
         "comp": null, "psr": null, "fuel": null, "dep": null, "mat": null,
         "merger": null, "restr": null, "eoi": null, "loss_disp": null, "opex": null, "oi": null,
         "oth_inc": null, "int": null, "ebt": null, "tax_cur": null, "tax_def": null, "tax": null, "ni": null,
         "eps_b": null, "eps_d": null, "sh_b": null, "sh_d": null, "other_lines": [["exact label", "value"]]},
  "is_recast": "FY2006-07 only: five-line expense classification from the FY2008 10-K",
  "bs": {"cash": null, "sti": null, "ar": null, "ms": null, "dta": null, "oca": null, "tca": null, "inv": null, "ppe": null, "oa": null, "ta": null,
         "ap": null, "std": null, "taxes_pay": null, "ocl": null, "cmltd": null, "tcl": null, "ltd": null, "ol": null, "dtl": null, "tl": null,
         "cs": null, "apic": null, "aoci": null, "re": null, "teq": null, "tle": null, "shares_out": null, "lines_raw": []},
  "cf": {"ytd_months": 9, "ni": null, "dep": null, "deftax": null, "gains": null, "conrail_eq": null,
         "ar_chg": null, "ms_chg": null, "oca_chg": null, "cl_chg": null, "oth_chg": null, "cfo": null,
         "capex": null, "acq": null, "prop_sales": null, "inv_purch": null, "inv_sales": null, "cfi": null,
         "div": null, "stock": null, "bb": null, "borrow": null, "repay": null, "cff": null, "net": null, "beg": null, "end": null, "lines_raw": []},
  "mg": {"rev": {"coal": null, "merch": null, "im": null, "total": null, "chem": null, "agr": null, "metals": null, "auto": null, "paper": null, "forest": null},
         "units": {"…": null}, "rpu": {"…": null}},
  "mg_9m": "Q3 records only: nine-month market-group values (for Q4 derivation)",
  "kpi": {"coal_tons": {"utility": null, "export": null, "domestic metallurgical": null, "industrial": null, "total": null},
          "im_units": {"domestic": null, "international": null, "total": null},
          "opex_detail": {"purchased services": null, "equipment rents": null, "materials": null, "claims": null, "other": null}},
  "fsc": "fuel surcharge revenue ($m) where the MD&A sentence was parsed",
  "ngaap": {"adj_oi_pub": null, "adj_or_pub": null, "adj_eps_pub": null, "adj_ni_pub": null, "adj_opex_pub": null, "fsc_pub": null, "rev_xfsc_pub": null,
            "items": [{"after": "income from railway operations | operating ratio | diluted earnings per share", "label": "exact", "value": null}], "source": "…"},
  "x": {"sbc_ytd": null, "deftax_ytd": null, "sh_out": null, "dps_q": null, "div_paid_ytd": null, "oi_xb": null, "ni_xb": null, "sh_b_xb": null, "eps_b_xb": null},
  "py": {"is": {}, "cf": {}},
  "notes": ["computed values; failed self-checks and why"]
}
```

Market-group keys: `coal`, `merch` (merchandise / general merchandise), `im` (intermodal), `total`, and the merchandise sub-groups `chem`, `agr` (agriculture / consumer / government to 2018; agriculture products 2019; agriculture, forest & consumer products 2020+), `metals`, `auto`, `paper` (to 2018), `forest` (2019 only).

## Items inside regular lines (manual_items.json → `adjusting_items_manual`)
| Code | Meaning |
|---|---|
| IMPAIR | Q3-20 $99m equity-investment impairment (purchased services & rents) |
| TAXD_OPEX | Q4-17 −$151m tax-reform effect in operating expenses |
| TAXD_TAX | Discrete tax items removed from adjusted EPS (Q4-17 −$3,482m; Q1-24 −$27m) |
| GAIN | 2024 railway line-sale gains in materials & other (Q3 −$380m, Q4 −$53m) |
| ADVIS | 2024 shareholder advisory costs in other income – net (Q1 $21m, Q2 $29m, Q3 $1m, Q4 $8m) |

## Self-checks (check_data.py)
- **IS:** Σ commodity-group revenues = revenues; Σ expense lines = total operating expenses; revenues − expenses = income from railway operations; + other income − interest = pre-tax income; − taxes = net income (±0.6); net income ÷ diluted shares = EPS (±0.015; ±0.025 to 2016, two-class method).
- **Market groups:** Σ merchandise sub-groups = merchandise (units and revenues); Σ groups = total; revenue per unit × units = revenue (±$1m + $0.5 per thousand units); MD&A revenues = income-statement revenues.
- **Non-GAAP:** income from railway operations + reconciliation items = published adjusted figure; 1 − adjusted OI ÷ revenues = published adjusted operating ratio (±0.05 pt); GAAP EPS + per-share items = published adjusted EPS (±0.01).
- **Cash flow / balance sheet:** beginning + net change = ending cash; ending cash = balance-sheet cash (2018–19 restricted cash excepted); total assets = total liabilities and equity; equity components sum.
- **Cross-checks:** XBRL OperatingIncomeLoss / NetIncomeLoss vs the release; prior-year comparatives vs the original record; Σ quarters = year for every line.
