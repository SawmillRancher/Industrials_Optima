# AMZN data extraction: schema and rules

Derived from `models/templates/EXTRACTION_SCHEMA_TEMPLATE.md`. `extract.py` implements it for every Amazon earnings release; any manual or agent extraction must follow the same rules.

## Sources
- **SEC EDGAR only** (Amazon.com, Inc., CIK 0001018724; no predecessor registrant). The IR site is blocked; its releases are the 8-K Item 2.02 Ex. 99.1 exhibits.
- **Text versions** of every document are in `$AMZN_SRC/txt`: one table row per line, cells joined by ` | `. File names embed `<date>_<form>_<accession>_<doc>`. A document's URL is `https://www.sec.gov/Archives/edgar/data/1018724/<accession-no-dashes>/<doc>`. Record those URLs in `sources`.
- **Text quirks:**
  - A cell that was only ")" or "%)" is dropped, so "(25,433" is negative.
  - "—" means zero.
  - Non-breaking spaces appear in headers.
  - Blank leading cells are dropped, so supplemental rows with fewer values than quarter columns are right-aligned (e.g. physical stores before Q3-17).
  - Labels can wrap onto a second line (the Q4-12–Q2-13 D&A line arrives as "amortization").
- **Column order:** releases to 2015 print the current year first; from 2016 the prior year comes first. Resolve columns from the year header line, never by position.
- **Optional cross-check:** `$AMZN_SRC/cf_1018724.json` (XBRL company facts); `data/_xbrl.json` keeps the subset the model uses.
- **EDGAR requests:** send a User-Agent and stay under 5 per second.

## Basis rules
- **Quarters:** income statement, segment and supplemental data come from that quarter's release three-month columns, **as originally reported**. Q4 = the Q4 release's three-month column. The releases print discrete three-month cash flows, so no FY − 9M derivation is needed for flows.
- **Balance sheet:** the quarter-end statement (column with the later date).
- **Cash flow:** the three-month column; `cf.months` records 3 or 12.
- **Annual records:** the Q4 release twelve-month columns.
- **Prior-year comparatives (`py`):** the prior-year column as presented in the same release (used for the 2015 SBC-allocation recast of segments).
- **Units:** USD millions as published (Amazon prints whole millions); shares in millions; per-share as published; percentages as published numbers (20 = 20%).
- **Stock split:** record shares / EPS **as published**, with the release filing date in `filed`. `normalize.py` applies the 20-for-1 split of 6-Jun-2022 to documents filed before that date.
- **Signs:**
  - costs positive;
  - interest expense stored positive (the releases print it negative);
  - the tax and equity-method lines are signed by the arithmetic that ties to net income, because the printed sign convention changes between eras;
  - cash flow as presented.
- **Null vs zero:** "—" = 0.0; a line not presented = omitted. **Never estimate.** Computed values (FY product groups = Σ quarters; Q1-26 energy remeasurement = 1H − Q2) are stated in notes or `manual_items.json`.

## Output
One JSON file per period: `models/amzn_build/data/<period_key>.json` (`2006` … `2025`, `Q1-06` … `Q2-26`), plus:
- `_groups.json`: net sales by product group, each quarter from the latest release presenting it.
- `_recast.json`: 8-K 23-Apr-2015 Ex. 99.3 AWS segment recast.
- `_xbrl.json`: the XBRL subset.

```json
{
  "period": "Q2-26", "filed": "2026-07-30",
  "sources": {"release": "https://www.sec.gov/Archives/edgar/data/1018724/.../amzn-20260630xex991.htm"},
  "is": {"rev_prod": 0, "rev_serv": 0, "rev": 0, "cogs": 0, "ful": 0, "mkt": 0, "tech": 0, "ga": 0, "othop": 0, "opex_tot": 0, "oi": 0,
         "int_inc": 0, "int_exp": "positive", "oth_inc": "signed", "remeas": "2006-08 only", "nonop_tot": 0, "ebt": 0, "tax_printed": 0,
         "tax": "positive = expense", "equity": "signed", "cum_eff": 0, "ni": 0, "eps_b": 0, "eps_d": 0, "sh_b": 0, "sh_d": 0, "gp": "2006-09 only"},
  "seg": {"na_rev": 0, "na_oi": 0, "intl_rev": 0, "intl_oi": 0, "aws_rev": "from Q1-15", "aws_oi": 0, "tot_rev": 0, "tot_oi": 0,
          "unalloc_sbc": "to 2015, negative", "unalloc_oth": "to 2015, negative"},
  "media": {"na_media": 0, "na_egm": 0, "na_other": 0, "intl_media": 0, "intl_egm": 0, "intl_other": 0},
  "grp": {"grp_online": 0, "grp_physical": 0, "grp_tp": 0, "grp_subs": 0, "grp_ads": "from Q3-20 (re-presented)", "grp_aws": 0, "grp_other": 0},
  "cf": {"months": 3, "beg": 0, "end": 0, "ni": 0, "dda": 0, "sbc": 0, "deftax": 0, "cfo": 0, "capex": "negative", "capex_proc": 0, "acq": 0,
         "sec_sales": 0, "sec_purch": 0, "cfi": 0, "bb": 0, "debt_net": "short + long-term proceeds less repayments", "lease_prin": "finance / capital lease and financing-obligation principal (from Q4-14)",
         "fin_oblig": 0, "cff": 0, "fx": 0, "net": 0, "lines_raw": [["exact label", "value"]]},
  "bs": {"cash": 0, "msec": 0, "inv": 0, "ar": 0, "tca": 0, "ppe": 0, "oplease": "from 2019", "gw": 0, "ta": 0, "ap": 0, "accr": 0, "unearned": "from Q4-13",
         "cltd": "2008 face only", "tcl": 0, "ltlease": "from 2019", "ltd": 0, "oltl": 0, "te": 0, "tle": 0, "lines_raw": [["exact label", "value"]]},
  "supp": {"fcf_ttm": 0, "fcf_lease_ttm": "Q4-14–Q4-24", "fcf_eq_ttm": "Q4-14–Q4-24", "ocf_ttm": 0, "sh_out": 0, "sh_awards": 0, "fx_ww": "y/y % ex F/X", "employees": 0},
  "py": {"is": {}, "seg": {}, "grp": {}},
  "notes": "self-check failures, if any"
}
```

## Adjusting items
Amazon publishes no adjusted P&L measures. `manual_items.json` holds the items it quantified, quoted verbatim with their source:
- **SPECIAL:** special charges in the release text (Q4-22, Q1-23, Q3-25, Q4-25), with the North America portion where disclosed.
- **ENERGY:** energy-contract derivative remeasurements (10-Q).
- **NONOP:** investment gains quoted in the release text (Rivian, Anthropic). Information only; the model removes the whole other-income line.

## Self-checks before writing each period
Re-read the source if any of these fail, and report any failure that remains, with the reason, in `notes`.
- **IS:**
  - rev − (cogs + ful + mkt + tech + ga + othop) = oi.
  - oi + int_inc − int_exp + oth_inc (+ remeas) = ebt.
  - ebt − tax + equity (+ cum_eff) = ni (±1).
  - rev_prod + rev_serv = rev.
- **Segments:** Σ segment net sales = rev; Σ segment OI + unallocated = oi (±1).
- **Product groups:** Σ groups = rev (±2); AWS group = AWS segment.
- **Cash flow:** cfo + cfi + cff + fx = net; beg + net = end (±1).
- **Balance sheet:** ta = tle; components sum to subtotals (±1).
