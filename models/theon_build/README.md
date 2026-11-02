# THEON model build kit — WORK IN PROGRESS (blocked on source access)

`models/THEON_Model.xlsx` will be the Theon International Plc (Euronext Amsterdam: THEON) three-statement model, built on the MLM template (`templates/MLM_Model.xlsx`, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`. **The workbook does not exist yet.** This directory holds the Phase 0 scope work and the document index, so the build can start the moment the sources are reachable.

## Status (2-Nov-2026)

### Sourcing finding
- **Theon is not an SEC registrant.** EDGAR holds one CIK for it, **0002095508** (Theon International Plc., Cyprus, fiscal year end 31-Dec), used only for two Schedule 13G filings about its stake in Kopin Corp (13G 6-Nov-2025, 13G/A 27-Jul-2026). It has filed no annual report, interim report or prospectus with the SEC. EDGAR therefore contains **no Theon historical financial statements**, and the instruction "historical numbers from SEC EDGAR only" cannot be satisfied for this company.
- **Playbook rule for non-SEC issuers** (section 5.1, RMS / BC precedent): confirm EDGAR holds only ADR-type CIKs, say so in header row 3, and source from the home-regulator filings. Theon's regulated disclosures are its prospectus (24-Jan-2024), annual reports, half-year reports and trading updates, published on theon.com / media.theon.com / s204.q4cdn.com and distributed through GlobeNewswire (Euronext / AFM-regulated information).
- **Every one of those hosts is blocked from this build environment** (proxy 403 from the container; DNS failure from the fetch tool): theon.com, investors.theon.com, media.theon.com, s204.q4cdn.com, globenewswire.com, live.euronext.com, afm.nl, filings.xbrl.org, and the newswire mirrors (investegate, placera, via.ritzau, adnkronos). Only EDGAR is reachable.
- Web-search snippets (third-party summaries of the releases) are **not** acceptable sources under the playbook ("never estimate a historical number"; "don't use unverifiable web quotes"), so nothing from them has been entered as data. The figures quoted below are scope notes only and are marked unverified.

### What is needed to proceed
One of:
1. Allow `theon.com`, `media.theon.com`, `s204.q4cdn.com` and `www.globenewswire.com` in the cloud environment's network settings, or
2. Upload the documents in the index below (prospectus, FY2023–25 annual reports, H1 2024–26 reports, the trading updates and deal releases) into the session, or
3. Accept a model with no history (not recommended; every check and bridge would be empty).

## Scope notes (Phase 0) — all facts below are from web-search snippets and are **unverified** until the primary documents are read
- **Company:** Theon International Plc, public limited company under Cyprus law (5 Agiou Antoniou, Muskita Building 2, Nicosia). Night-vision and thermal-imaging systems for defence and security; operations started in Greece in 1997 (Theon Sensors). Majority owner Venetus Ltd (controlled by Christianos Hadjiminas via CHRE Investments Ltd). [EDGAR 13G/A, Kopin 8-K Ex. 99.2 — these two facts are EDGAR-verified.]
- **Listing:** Euronext Amsterdam, ticker THEON, ISIN CY0200751713; first trading day 7-Feb-2024; IPO price €10.00 per share; 15.4m shares placed (10.0m new, 5.4m existing incl. 1.4m over-allotment); prospectus dated 24-Jan-2024. 70,000,000 ordinary shares in issue (Nov-2025). A rights offering of ~€150m was announced at some point in 2026 (date and terms to verify).
- **Reporting basis:** IFRS as adopted by the EU, EUR, calendar fiscal year. **Half-year reporter:** full statements at FY and H1; Q1 and Q3 (and Q2/H1) trading updates with revenue, adjusted EBIT, order intake and backlog. → Use the RMS / BC half-year layout (H1 / H2 / FY columns, H2 = FY − H1, quarterly revenue memo rows inside the half columns).
- **History window:** FY2021–23 from the prospectus (annual P&L / BS / CF); FY2023 annual report; H1 columns from H1/24; latest actual H1/26 (report published 7-Sep-2026). Forecast: H2/26E (calibrated to FY26 guidance), 2026E, 2027E–2030E.
- **Headline figures seen in snippets (unverified):** FY2025 revenue €443.5m (+25.9%), adjusted EBIT margin ~26.2%, order intake €1,313.9m (+182%); Q1/26 revenue €120.1m (+32.3%), adjusted EBIT €30.0m; H1/26 revenue €248.7m (+35.4%, organic +24.7%), adjusted EBIT €65.1m (26.2%), order intake €232.5m, net debt €237.9m; backlog €1,420m at Q1/26. FY2025 dividend €0.31 per share (€24.4m, 30% payout; policy 20–30%).
- **Guidance (unverified, from the Q1/26 and Q2/26 updates):** FY2026 revenue €570–600m, mid-twenties adjusted EBIT margin; medium-term organic growth >15% p.a. plus bolt-on M&A. Q3/26 trading update scheduled 9-Nov-2026.
- **Deals needing blocks:** Harder Digital (image-intensifier tubes, acquired Oct-2024); Kappa Optronics GmbH (announced 4-Aug-2025, EV €75m, cash consideration €69.9m, closed 14-Jan-2026, ~€40m FY26 revenue); 9.8% stake in Exosens for €268.7m (closed 7-Jan-2026; financial asset, not consolidated); Kopin Corp investment (Series A convertible preferred, converted 28-May-2026; 6,190,496 shares = 3.33% at 27-Jul-2026 — EDGAR-verified) and a 49% interest in Kopin Europe (terms to verify). Pro forma net debt after Kappa and Exosens stated as €211.7m / 1.8x LTM EBITDA (unverified).
- **Share price:** not given by the user and no SEC-filed price exists (Theon files no Forms 4 / 10-Q). Must be asked for or taken from a dated Euronext close once reachable; flag "update to market".
- **Closest reference kits:** ONON (IFRS, foreign currency, recent IPO, 6-Oct template kit) for the scripts; RMS and BC lessons for the half-year column layout, IFRS 16 schedule and net-cash / lease treatment.

## Document index
`filings.csv` lists every document the build needs, with the URL found so far, the host, and whether it is reachable from this environment. Raw downloads go to `$THEON_SRC` outside the repo; only the extracted `data/*.json` is committed.

## Files (so far)
- `README.md`: this file.
- `EXTRACTION_SCHEMA.md`: per-period extraction schema adapted for an IFRS, EUR, half-year reporter.
- `filings.csv`: document index.
