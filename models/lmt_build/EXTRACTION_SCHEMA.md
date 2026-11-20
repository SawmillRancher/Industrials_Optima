# LMT data extraction: schema and rules

Per-period extraction of Lockheed Martin Corporation (NYSE: LMT) from SEC EDGAR into `models/lmt_build/data/<period>.json`, run by `extract.py` (parser in `parse_release.py`). Derived from the DHR / TDY / WAB / WWD schemas.

## Sources
- **SEC EDGAR only** (CIK 936468; no predecessor registrants). The investor-relations site is blocked; its releases are the 8-K Item 2.02 Ex. 99.1 exhibits.
- **Documents** are downloaded to `$LMT_SRC/docs` (`make_index.py`, `fetch.py`); text versions (one table row per line, cells joined by ` | `) in `$LMT_SRC/txt`. File names embed `<date>_<form>_<accession>_<doc>`. A document's URL is `https://www.sec.gov/Archives/edgar/data/936468/<accession-no-dashes>/<doc>`; each record stores it in `sources`.
- **Release index:** `data/_releases.json` maps (fiscal year, quarter) to the first 8-K Item 2.02 release of that quarter that contains the statement of earnings, balance sheet and cash-flow tables (release month → quarter: Jan = Q4 of the prior year, Apr = Q1, Jul = Q2, Oct = Q3).
- **Cross-check:** `$LMT_SRC/cf_936468.json` (XBRL company facts; subset used by the model in `data/_xbrl.json`).
- **EDGAR requests:** User-Agent on every request; under 5 per second.

## Basis rules
- **Quarters:** income statement, segment schedule, unallocated items and backlog come from that quarter's release (three-month columns), **as originally reported**. Q4 = the fourth-quarter release three-month column.
- **Annual records (2006–2025):** the fourth-quarter release twelve-month column (statements, segments, cash flow) and that year's 10-K for the amortization and debt schedules (`manual_items.json`).
- **Balance sheet:** the quarter-end statement (`bs`); the prior year-end column of the same release in `bs_py`.
- **Cash flow:** the **year-to-date** statement (`cf.ytd_months` = 3, 6, 9, 12); discrete quarters are derived in `normalize.py`.
- **Prior-year comparatives (`py`):** the prior-year column of the following year's same-quarter release (statement of earnings, segments, unallocated items, pension detail). These are the source of the re-presentations the model applies (hybrid basis, see `normalize.py`): 2006 (FY2007 release), 2012 segments (Q4-13 release), Q1/Q2-16 continuing operations (2017 releases), 2017 ASC 606 / ASU 2017-07 (2018 releases). The Q4-2015 realignment pro forma tables are in `data/_segpf_2015.json`; the 10-K segment tables for the 2011 realignment in `data/_10k_segments.json`.
- **Units:** USD millions as published; shares in millions (one decimal); per share in $; percentages as published.
- **Stock splits:** none in the period.
- **Signs:** costs positive (`cos`, `int`, `tax`); two-sided items signed by their effect on earnings (`othinc`, `nonsvc`, `othnonop`, unallocated items); cash flow as presented.
- **Null vs zero:** a line shown as "—" = 0.0; a line not presented is absent. Never estimate. Any computed value (FY − 9M, derived residual) is stated in `notes` or in the model's cell comments.

## Record layout
```json
{
  "period": "Q3-26", "fy": 2026, "q": 3,
  "sources": {"release": "https://...", "release_date": "2026-10-22", "filing": "https://..."},
  "is": {"rev", "cos", "gp", "othinc", "op", "int", "nonsvc", "othnonop", "ebt", "tax", "cont", "disc", "ni", "etr",
         "eps_b", "eps_d", "eps_b_cont", "eps_d_cont", "sh_b", "sh_d", "sh_end"},
  "seg": {"sales": {"aero", "mfc", "rms", "space", "isgs", "es", "itgs", "iss"}, "op": {...}, "sales_tot", "op_tot",
          "unalloc": [["exact label", "category", value]], "unalloc_tot", "op_cons", "margin": {...}},
  "pension": {"fas_exp", "cas", "fascas", "fas_svc", "fascas_op", "nonsvc", "settle"},
  "cf": {"ytd_months", "ni", "dda", "sbc", "deftax", "sev", "settle", "rfl", "pens", "wc_ar", "wc_ca", "wc_inv", "wc_ap", "wc_cl", "wc_tax",
         "cfo", "capex", "acq", "divest", "cfi", "debt_iss", "debt_rep", "bb", "div", "stock_iss", "cff", "fx", "net", "beg", "end", "lines_raw": [[label, value]]},
  "bs": {"cash", "ar", "ca", "inv", "oca", "tca", "ppe", "gw", "intang", "dta", "onca", "ta", "ap", "sal", "cl", "std", "ocl", "tcl", "ltd", "pens",
         "opeb", "oncl", "tl", "cs", "apic", "re", "aoci", "eq", "nci", "te", "tle", "lines_raw": [...]},
  "backlog": {"aero", "mfc", "rms", "space", "isgs", "es", "total"}, "backlog_py": {...},
  "deliv": {"f35", "f16", "c130j", "governmenthelicopterprograms", ...},
  "summary": {"fcf_pub", "cfo", "capex", "seg_op"},
  "py": {"release", "release_date", "is": {...}, "seg": {...}, "pension": {...}},
  "x": {"dps", "dps_ytd"},
  "notes": []
}
```

## Segment keys
| Key | Segment (period in force) |
|---|---|
| `aero` | Aeronautics (all periods) |
| `mfc` | Missiles and Fire Control (2011+ on the 2013 structure) |
| `rms` | Mission Systems and Training (2011–15) / Rotary and Mission Systems (2016+) |
| `space` | Space Systems (to 2019) / Space (2020+) |
| `isgs` | Information Systems & Global Solutions (2006–15; discontinued operations 2016) |
| `es` | Electronic Systems (2006–10 structure) |
| `itgs`, `iss`, `sitg` | IT & Global Services, Integrated Systems & Solutions, Systems & IT Group (FY2006 release only; superseded by the FY2007 re-presentation) |

## Unallocated-item categories
| Code | Meaning |
|---|---|
| `fas_exp`, `cas`, `fas_svc` | FAS pension expense, CAS pension cost, FAS service cost (detail lines; not summed) |
| `fascas` / `fascas_op` | FAS/CAS pension adjustment (total to 2017) / operating adjustment (2018+) |
| `nonsvc`, `settle` | Non-service FAS pension cost; pension settlement charge (pension tables) |
| `sev`, `impair` | Severance / restructuring charges; goodwill impairment, impairment and other charges |
| `sbc` | Stock-based compensation (shown separately to 2016) |
| `amort` | Intangible asset amortization expense (2023+) |
| `other` | Other, net |
| `special` | Unusual items, net (2006–10) and any other company label |

## Self-checks (`check_data.py`, 1,950 checks)
- IS: sales − cost of sales = gross profit; + other income = operating profit; − interest + non-service pension + other non-operating = EBT; − tax = continuing operations; + discontinued = net earnings; NI ÷ diluted shares = diluted EPS (±0.01; ±0.03 in loss quarters).
- Segments: Σ segment sales = sales; Σ segment OP = published business segment OP; Σ unallocated items = published total; segment OP + unallocated = consolidated OP (build and published).
- Pension: CAS + FAS expense = total FAS/CAS adjustment; operating adjustment + non-service = total; 2018+ operating adjustment = unallocated line.
- Cash flow: beginning + net change = ending; ending = balance-sheet cash; CFO − capex = published free cash flow (2018+); CF net earnings = IS net earnings (as-reported periods).
- Balance sheet: TA = TL&E; components sum to subtotals.
- Backlog: Σ segments = total (except the 2006 sub-segment table).
- Quarters vs years (2013–25): Σ Q1–Q4 = FY for every IS, segment, unallocated, cash-flow and dividend series. Known exception: the non-service FAS pension line was not presented for Q1/Q2-20 (introduced Q3-21; only Q3/Q4-20 re-presented), so 2020 `nonsvc` / `othnonop` are not summed.
