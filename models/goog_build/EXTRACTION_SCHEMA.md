# GOOG data extraction: schema and rules

Derived from `models/templates/EXTRACTION_SCHEMA_TEMPLATE.md`. Unlike the release-parsing kits, GOOG extracts the statements from the **XBRL instance document of each 10-K / 10-Q**, which also carries the dimensional facts (revenue by type, segments). The XBRL company-facts API omits those dimensional facts, so it is used only as a cross-check.

## Sources
- **SEC EDGAR only:** Google Inc. (CIK 1288776; 10-K / 10-Q to Q3-2015) and Alphabet Inc. (CIK 1652044; FY2015 10-K onward). The IR site is blocked; its releases are the 8-K Ex. 99.1 exhibits.
- **Raw files** (not committed) live in `$GOOG_SRC`:
  - `docs/` holds the filings and XBRL instances (`<ticker>-<date>.xml` or the inline-XBRL extract `*_htm.xml`; the 2009 filings also contain a `defnref.xml`, which is skipped).
  - `txt/` holds the h2t text: one table row per line, cells joined by ` | `.
  - `xfacts/` caches the parsed instance facts.
  - `cf_<cik>.json` is the company-facts file.
- **EDGAR requests:** send a User-Agent and stay under 5 per second (`make_index.py`, `fetch.py` throttle and retry).

## Basis rules
- **Income statement:**
  - Q1–Q3 use the 10-Q three-month undimensioned facts.
  - Q4 = 10-K fiscal year − Q3 10-Q nine months (`normalize.py`), stated in each Q4 record's `basis`.
  - Q4 diluted / basic EPS come from the Q4 release three-month column.
  - Q4 weighted shares = 4 × FY − Σ Q1–Q3 (derived).
- **Cash flow:** year-to-date facts (`ytd_months`); discrete quarters derived.
- **Balance sheet:** instant facts at the period end.
- **Annual records:** FY2009+ from the 10-K instance; FY2006–08 from the 10-K text (`pre09.py`, USD thousands → millions).
- **As originally reported:** each period from its own filing. If a period appears in several filings, the first (own) filing wins.
- **Revenue types / segments (dimensional facts):**
  - Each block takes the latest filing that presents the period.
  - A revenue-type block is used only if it is on the current taxonomy, i.e. it includes `GoogleSearchOtherMember`. This keeps the old "Google other incl. Cloud" basis out.
  - Q4 = FY − (Q1 + Q2 + Q3).
- **Legacy revenue split:** the MD&A revenue table of the period's own filing (three-month column; dollar amounts > 100; percentage rows skipped).
- **Units:**
  - USD millions (XBRL values ÷ 10⁶; text in thousands ÷ 10³);
  - shares in millions;
  - per-share as filed.
- **Stock splits:** shares / EPS / DPS are recorded exactly as filed. `normalize.py` adjusts them by the source filing date: ×40 before 3-Apr-2014, ×20 before 15-Jul-2022.
- **Two-class EPS:**
  - basic shares = Class A + B + C;
  - diluted = Class A diluted (assumes Class B conversion) + Class C diluted;
  - EPS = undimensioned fact, else Class A (Class C EPS differs only in 2015, the adjustment payment).
- **Signs:**
  - costs positive; other income signed by effect;
  - cash-flow payments (tagged positive in XBRL) are made negative;
  - (gains) on securities are reversed;
  - net payments for stock-based award activities are negative.
- **Null vs zero:** an untagged line is null (not 0), except where the statement shows no such line (e.g. dividends before 2024). Derived values (cost of revenues 2012–13, OI&E 2009, Q4) are flagged (`cor_derived`, `oie_derived`, `q4_derived`).

## Output
One JSON per period: `data/<period>.json` for `2006`–`2025` and `Q1-13`–`Q2-26`:
```json
{
  "period": "Q2-26", "period_end": "2026-06-30", "filed": "2026-07-23",
  "sources": {"filing": "https://...", "release": "https://..."},
  "xbrl": {"q": {"rev": 0, "...": "three-month and instant facts"}, "ytd": {"...": "year-to-date facts"}, "concepts": {"rev": "Revenues", "...": "concept used per key"}},
  "ytd_months": 6,
  "legacy": {"leg_web": 0, "leg_net": 0, "leg_oth": 0, "leg_moto": 0, "leg_ob": 0},
  "dims": {"streams": {"values": {}, "source": "url", "filed": "date"}, "segrev_new": {}, "segoi_new": {}, "segrev_old": {}, "segoi_old": {}},
  "release": {"eps_d_q": 0, "fcf_q": 0, "tac_q": 0, "employees": 0, "ng_ni_q": 0, "ng_eps_q": 0, "ng_sbc_q": 0, "url": "", "filed": ""},
  "pre09": {"...": "FY2006-08 only: statement lines from the 10-K text"},
  "notes": "derivations"
}
```
Concept aliases per key are in `extract.py` (`A`); the concept actually used is stored in `xbrl.concepts`.

## Manual items (`manual_items.json`)
- Company-quantified adjusting items, each with its Ex. 99.1 URL: EC fines, severance / office-space charges, the Tax Act and the 2008 equity impairment. Also named-but-not-adjusted items.
- Company-published adjusted figures (operating income / net income / EPS excluding the items) and the Google non-GAAP definition.
- Split ratios and dates; known exceptions with reasons.
- Guidance: the capex outlook is call-only and UNVERIFIED.
- Capital structure: debt, the mandatory convertible preferred, the Jun-2026 equity raise, ATM, buybacks and dividends. Deals: the Wiz / Intersect PPA and GFiber. The share price.

## Self-checks (`check_data.py`, 966 checks)
- **IS:** revenues − total costs = operating income; operating income + OI&E = EBT (±1); diluted EPS = (NI − preferred dividends − Class C payment) ÷ diluted shares (±0.015 after split adjustment).
- **Segments:** Σ segment OI = operating income; Σ revenue types = Google Services revenues (±2). Documented exceptions: the 2017–18 recast, the 2013 legacy segments.
- **Cash flow:** beginning + net change = ending; Σ quarters = FY for CFO, capex, CFI, CFF, buybacks and dividends.
- **Balance sheet:** TA = TL&E; BS cash = CF cash before 2018.
- **Release cross-checks:** Q4 revenue / NI; quarterly free cash flow; Google non-GAAP EPS.
- **XBRL company facts:** revenue, OI, NI, total assets, CFO (earliest-filed fact).
