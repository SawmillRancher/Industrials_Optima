# Company models

**Building a new model?** Start with [`MODEL_BUILD_PLAYBOOK.md`](MODEL_BUILD_PLAYBOOK.md). It has the process, the master checklist, the template workbook ([`templates/MLM_Model.xlsx`](templates/MLM_Model.xlsx)), fill-in README / extraction-schema templates and the QA tools in [`tools/`](tools).

## Model index
Each model was built on its own branch and is not yet on this one. Template generation (the template each model was built on) runs Moog → DSV → HII → RBA → TDY → MLM. Use the latest builds on the 6-Oct-2026 MLM template (★) as references.

| Ticker | Company | Template | Branch | File |
|---|---|---|---|---|
| TFII | TFI International | Moog generator | `claude/quirky-mendel-0xqtQ` | `TFI_Model.xlsx` |
| CPRT | Copart (v1, SEC builder) | DSV-style | `claude/optimistic-heisenberg-3egsy8` | `models/Copart_SEC_Model.xlsx` |
| — | R&Y Tool & Die (private, LBO) | Moog styling | `claude/keen-gates-14p91s` | `models/RY_Tool_3_Statement_Model.xlsx` |
| HII | Huntington Ingalls | DSV | `claude/keen-knuth-bqfr5g` | `models/HII_Model.xlsx` |
| RBA | RB Global | HII | `claude/exciting-dirac-i0xacm` | `models/RBA_Model.xlsx` |
| CPRT | Copart | RBA | `claude/lucid-sagan-mtsd21` | `models/Copart_Model.xlsx` |
| TDY | Teledyne | RBA | `claude/dreamy-lamport-2r2q2y` | `models/TDY_Model.xlsx` |
| KRMN | Karman | TDY | `claude/funny-heisenberg-nfxrwu` | `models/karman/KRMN_Model.xlsx` |
| VMC | Vulcan Materials | TDY | `claude/wonderful-rubin-pz9j20` | `models/VMC_Model.xlsx` |
| MLM | Martin Marietta (template source) | TDY | `claude/admiring-mendel-ioiosk` | `models/MLM_Model.xlsx` |
| RMS | Hermès | MLM | `claude/exciting-hamilton-njvy1u` | `models/RMS_Model.xlsx` |
| CLH | Clean Harbors | MLM | `claude/funny-davinci-41jujt` | `models/CLH_Model.xlsx` |
| WAB | Wabtec | MLM | `claude/intelligent-noether-279c47` | `models/WAB_Model.xlsx` |
| XPO | XPO | MLM | `claude/serene-hopper-mw0kgc` | `models/XPO_Model.xlsx` |
| CHRW | C.H. Robinson (+ RXO PF) | MLM | `claude/magical-planck-7qjmqd` | `models/CHRW/CHRW_Model.xlsx` |
| ODFL | Old Dominion | MLM | `claude/inspiring-heisenberg-q6cefw` | `models/ODFL_Model.xlsx` |
| SAIA | Saia | MLM | `claude/dazzling-sagan-96mhry` | `models/SAIA_Model.xlsx` |
| BC | Brunello Cucinelli | MLM | `claude/cool-faraday-wk9ft3` | `models/BC_Model.xlsx` |
| WCN | Waste Connections | MLM | `claude/blissful-edison-d4kjl4` | `models/WCN_Model.xlsx` |
| HEI | HEICO | MLM | `claude/brave-ritchie-e535fc` | `models/HEI_Model.xlsx` |
| LOAR | Loar Holdings | MLM | `claude/modest-goldberg-886gpx` | `models/LOAR_Model.xlsx` |
| ONON | On Holding ★ | MLM (6-Oct) | `claude/confident-planck-uj4pis` | `models/ONON_Model.xlsx` |
| CSGP | CoStar | MLM | `claude/relaxed-ride-lw790g` | `models/CSGP_Model.xlsx` |
| DHR | Danaher ★ | MLM (6-Oct) | `claude/wizardly-dijkstra-zxf7n3` | `models/DHR_Model.xlsx` |
| TMO | Thermo Fisher | MLM | `claude/magical-mccarthy-btowq2` | `models/TMO_Model.xlsx` |
| CTAS | Cintas ★ | MLM (6-Oct) | `claude/affectionate-wozniak-l9cppl` | `models/CTAS/CTAS_Model.xlsx` |
| STE | STERIS ★ | MLM (6-Oct) | `claude/gifted-lamport-4idqjn` | `models/STE_Model.xlsx` |
| UBER | Uber | MLM | `claude/great-fermat-efvr52` | `models/UBER_Model.xlsx` |
| BWXT | BWX Technologies | MLM | `claude/intelligent-ride-0feye2` | `models/BWXT_Model.xlsx` |
| CW | Curtiss-Wright | MLM | `claude/zealous-wright-co1vi8` | `models/CW_Model.xlsx` |
| LECO | Lincoln Electric ★ | MLM (6-Oct) | `claude/compassionate-ramanujan-wx8j8s` | `models/LECO_Model.xlsx` (alternate build: `claude/blissful-cerf-7e09o7`, `models/LECO/LECO_Model.xlsx`) |
| ESAB | ESAB ★ | MLM (6-Oct) | `claude/compassionate-ramanujan-wx8j8s` | `models/ESAB_Model.xlsx` |

To fetch a model or its build kit without switching branches:
`git fetch origin <branch> && git show origin/<branch>:<path> > <local file>`. For a whole directory, use `git archive origin/<branch> <dir> | tar -x`.

## Shared assets on this branch
| Path | Purpose |
|---|---|
| `MODEL_BUILD_PLAYBOOK.md` | Process, master checklist, adaptation guide, pitfalls |
| `templates/MLM_Model.xlsx` | Canonical template workbook (6-Oct-2026 MLM version: reworked DCF, Bull-Base-Bear buyback rows) |
| `templates/NEW_MODEL_README_TEMPLATE.md` | Fill-in README for each new build kit |
| `templates/EXTRACTION_SCHEMA_TEMPLATE.md` | Per-period extraction schema, basis rules and self-checks |
| `tools/inspect_model.py` | Lists formula errors and non-zero check rows in a recalculated model |
| `tools/cyc.py` | Scans the Model sheet for circular references |
