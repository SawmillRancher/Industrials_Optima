# Industrials Optima

The repository has two parts:
- **News aggregator / hazardous-waste tools:** the Python package in `src/industrials_optima/` (see `README.md`).
- **Company financial models:** three-statement Excel models under `models/`.

## Building or updating a company model
When asked to build a new model (or rebuild or update one), follow `models/MODEL_BUILD_PLAYBOOK.md`:
- **Read it in full first.** Use its master checklist (section 3) as the task list and report progress by phase.
- **Template:** start from `models/templates/MLM_Model.xlsx`, the current MLM template. Don't use an older template unless asked.
- **Reference kit:** copy the build kit closest to the company as your starting scripts. `models/README.md` lists every model and the branch it lives on. The most complete kits are STE, DHR, ONON and LOAR.
- **Kit docs:** write the kit README from `models/templates/NEW_MODEL_README_TEMPLATE.md` and the extraction schema from `models/templates/EXTRACTION_SCHEMA_TEMPLATE.md`.
- **Sources:** SEC EDGAR only (send a User-Agent; stay under 5 requests/s). Investor-relations sites and SEDAR are blocked; the 8-K Ex. 99.1 releases are the same documents. Never estimate a historical number.
- **Share price:** if the user didn't give one, ask or use the latest observable close, and state its date.
- **Done means:**
  1. Recalculate with LibreOffice Calc (the xlsx skill's `recalc.py`).
  2. `python3 models/tools/inspect_model.py <file>` shows 0 error cells and 0 non-zero check rows.
  3. `python3 models/tools/cyc.py <file>` shows 0 cycles.
  4. The model is added to `models/README.md`.
  5. Everything is committed and pushed.
- **Improvements:** when a build teaches something new (a fix, a pitfall, a new adaptation), add it to the playbook in the same commit.

## Repo notes
- `.gitignore` ignores `*.md` except `README.md`, `CLAUDE.md` and Markdown under `models/`. Any new doc elsewhere needs an exception.
- Raw EDGAR downloads go outside the repo (scratchpad or `$<TICKER>_SRC`). Commit only the extracted `data/*.json`.
