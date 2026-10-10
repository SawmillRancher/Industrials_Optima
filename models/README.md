# Company models

**Building a new model?** Start with [`MODEL_BUILD_PLAYBOOK.md`](MODEL_BUILD_PLAYBOOK.md) for the process and master checklist. Then read the entries for similar companies in [`MODEL_LESSONS.md`](MODEL_LESSONS.md), which records the nuances of every model built so far. Start from [`templates/MLM_Model.xlsx`](templates/MLM_Model.xlsx) and check the result with [`tools/`](tools).

## Model index
All models are on this branch. The template lineage runs Moog → DSV → HII → RBA → TDY → MLM. ★ marks builds on the current MLM template (6-Oct-2026) with a full build kit; prefer them as references.

| Ticker | Company | Template | Workbook | Build kit / rebuild |
|---|---|---|---|---|
| TFII | TFI International | Moog generator | `../TFI_Model.xlsx` | `src/industrials_optima/financial_model/` (`build-model-template` CLI, `populate_tfi.py`) |
| CPRT | Copart (v1, SEC builder) | DSV-style | `Copart_SEC_Model.xlsx` | `src/industrials_optima/secmodel/` (`copart-model` CLI) |
| — | R&Y Tool & Die (private, LBO) | Moog styling | `RY_Tool_3_Statement_Model.xlsx` | `build_ry_model.py` |
| HII | Huntington Ingalls | DSV | `HII_Model.xlsx` | workbook only |
| RBA | RB Global | HII | `RBA_Model.xlsx` | `rba/` + `data/rba/`: `RECALC_SCRIPT=<recalc.py> python -m models.rba.build` |
| CPRT | Copart | RBA | `Copart_Model.xlsx` | workbook only |
| TDY | Teledyne | RBA | `TDY_Model.xlsx` | `tdy/` + `data/tdy/`: `RECALC_SCRIPT=<recalc.py> python -m models.tdy.build` |
| KRMN | Karman | TDY | `karman/KRMN_Model.xlsx` | `karman/builder/`: `python3 driver.py ../KRMN_Model.xlsx` |
| VMC | Vulcan Materials | TDY | `VMC_Model.xlsx` | `vmc_build/`: `python3 build.py --snap` |
| MLM | Martin Marietta (template source) | TDY | `MLM_Model.xlsx` | workbook only (the template is `templates/MLM_Model.xlsx`) |
| RMS | Hermès | MLM | `RMS_Model.xlsx` | `rms/` + `data/rms/`: `python3 -m models.rms.build` |
| CLH | Clean Harbors | MLM | `CLH_Model.xlsx` | workbook only |
| WAB | Wabtec | MLM | `WAB_Model.xlsx` | `wab_build/`: `python3 build.py --snap` |
| XPO | XPO | MLM | `XPO_Model.xlsx` | workbook only |
| CHRW | C.H. Robinson (+ RXO PF) | MLM | `CHRW/CHRW_Model.xlsx` | data only: `CHRW/data/`. The build scripts its README references were never committed |
| ODFL | Old Dominion | MLM | `ODFL_Model.xlsx` | `odfl_build/`: `python3 build.py --snap` |
| SAIA | Saia | MLM | `SAIA_Model.xlsx` | workbook only |
| BC | Brunello Cucinelli | MLM | `BC_Model.xlsx` | workbook only |
| WCN | Waste Connections | MLM | `WCN_Model.xlsx` | workbook only |
| HEI | HEICO | MLM | `HEI_Model.xlsx` | workbook only |
| LOAR | Loar Holdings | MLM | `LOAR_Model.xlsx` | `loar_build/`: `python3 build.py --snap` |
| ONON | On Holding ★ | MLM (6-Oct) | `ONON_Model.xlsx` | `onon_build/`: `python3 build.py --snap` |
| CSGP | CoStar | MLM | `CSGP_Model.xlsx` | workbook only |
| DHR | Danaher ★ | MLM (6-Oct) | `DHR_Model.xlsx` | `dhr_build/`: `python3 build.py --snap --recalc` |
| TMO | Thermo Fisher | MLM | `TMO_Model.xlsx` | workbook only |
| CTAS | Cintas ★ | MLM (6-Oct) | `CTAS/CTAS_Model.xlsx` | `CTAS/source_kit/`: `python3 scripts/build_model.py out.xlsx` |
| STE | STERIS ★ | MLM (6-Oct) | `STE_Model.xlsx` | `ste_build/`: `python3 build.py --snap` |
| UBER | Uber | MLM | `UBER_Model.xlsx` | workbook only |
| LECO | Lincoln Electric ★ | MLM (6-Oct) | `LECO_Model.xlsx` | `builder/`: `python3 builder/tools/run_leco.py out/LECO_Model.xlsx` |
| LECO | Lincoln Electric (alternate build) | MLM | `LECO/LECO_Model.xlsx` | workbook only |
| ESAB | ESAB ★ | MLM (6-Oct) | `ESAB_Model.xlsx` | `builder/`: `python3 builder/tools/run_esab.py out/ESAB_Model.xlsx` |
| BWXT | BWX Technologies | MLM | `BWXT_Model.xlsx` | workbook only |
| CW | Curtiss-Wright | MLM | `CW_Model.xlsx` | workbook only |
| WWD | Woodward ★ (first build on the playbook) | MLM (6-Oct) | `WWD_Model.xlsx` | `wwd_build/`: `python3 build.py --snap --recalc` |

Kit paths are relative to `models/`. Every kit README gives its sources, basis and full rebuild steps. Recalculation needs LibreOffice Calc and the xlsx skill's `recalc.py` (set `XLSX_RECALC` or `RECALC_SCRIPT`). For a "workbook only" model, its basis notes, Modelling Notes column and cell comments are the documentation; `MODEL_LESSONS.md` summarises them.

## Shared assets
| Path | Purpose |
|---|---|
| `MODEL_BUILD_PLAYBOOK.md` | Process, master checklist, adaptation guide, pitfalls |
| `MODEL_LESSONS.md` | Per-model nuances and reusable lessons from all builds |
| `templates/MLM_Model.xlsx` | Canonical template workbook (6-Oct-2026 MLM version: reworked DCF, Bull-Base-Bear buyback rows) |
| `templates/NEW_MODEL_README_TEMPLATE.md` | Fill-in README for each new build kit |
| `templates/EXTRACTION_SCHEMA_TEMPLATE.md` | Per-period extraction schema, basis rules and self-checks |
| `tools/inspect_model.py` | Lists formula errors and non-zero check rows in a recalculated model |
| `tools/cyc.py` | Scans the Model sheet for circular references |
