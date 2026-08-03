# cGR8s — Comprehensive Goods Reconciliation at Secondary

Flask web app for cigarette production QA at AWGTC: FG code master data, target
weight calculation, NPL, monthly blend nicotine, QA data entry, process orders,
batch processing and reports.

> **Keep this file current.** Any change that adds/renames a module, route,
> table, env var, integration, or workflow MUST update this file in the same
> commit, so a new chat or agent understands the complete project without
> re-discovering it. `AGENTS.md` just points here.

## Stack & entry point

- Python / Flask / SQLAlchemy / Jinja2 + Bootstrap 5 (jQuery on a few pages)
- DB: SQL Server (`DB_SERVER`/`DB_NAME` in `.env`), repository pattern
- Entry: `python run.py` → http://127.0.0.1:5053 (`.env`: `PORT`, `FLASK_DEBUG=1`
  in dev = auto-reload). Virtualenv: `.venv/`
- Auth: SSO middleware (`app/sdk/session_middleware.py`) + permission helpers
  (`has_perm('MASTER_DATA.EDIT')` etc. in templates, `@require_permission` /
  `@require_any_permissions` on routes). Dev login bypass: `GET /login/test-bypass`
- CSRF: Flask-SeaSurf — `meta[name="csrf-token"]` in `base.html`, send
  `X-CSRFToken` header on fetch/AJAX POSTs

## Layout

- `app/modules/<name>/__init__.py` — blueprints: `dashboard`, `fg_codes`,
  `master_data`, `qa`, `admin`, process orders, target weight, NPL, optimizer,
  batch, reports. Some modules have their own `templates/` folder; shared pages
  live in top-level `templates/`
- `app/models/` — SQLAlchemy models; `app/repositories/__init__.py` — one
  repository class per model over `BaseRepository`
- `app/services/` — domain logic (e.g. `key_variable_populator.py` resolves
  N_BLD, P_CU, gamma, N_tgt for an FG code)
- `app/database.py` — engine + request-scoped session (`g.db`)
- Tests: `tests/e2e/` — Python Playwright scripts (`python tests/e2e/test_full_app.py`,
  server must be running) plus some `.spec.ts`

## External production DBs (MTC + ps_utc + ps_specialtobacco)

`app/modules/fg_codes/__init__.py` connects via pyodbc (ODBC Driver 17) to
**three** production SQL Servers sharing the `tabfinishgoods` + `brands` schema.
`_prod_sources()` builds the list: `mtc` (`MTC_DB_*`), `ps_utc` (`PS_UTC_DB_*`)
and `ps_specialtobacco` (`PS_SPECIALTOBACCO_DB_*`); the two PS sources default
to the MTC host + credentials with just a different `DATABASE`, overridable per
source. Both lookups **union across all three**:

- `_fetch_mtc_brandcodes(date)` — FG brandcodes produced on a date, deduped union
  (FG Codes page daily list)
- `fetch_mtc_month_brandcode_dates(year, month)` — `{brandcode: latest production
  date}` merged (max date per code) across sources (Blend Master "Last Used")

Per-source failure is skipped and logged; a source down doesn't drop the others.
`_fetch_mtc_brandcodes` raises (→ 502) only when EVERY source fails; the client
then falls back to the full local list. Production servers need: env vars, ODBC
Driver 17, network access to each production host.

## Domain rules & data quirks (important)

- `tobacco_blend_analysis.blend_name` holds **either a blend code or a tobacco
  name** (e.g. `50.0097` or `COVINA`). Always look up by BOTH — repo methods
  `get_month_value` / `get_latest_before` accept a list of keys. New monthly
  saves are stored under the tobacco **name** (values are per tobacco, several
  blend codes can share one name).
- `fg_codes` rows carry `blend_code`, `blend` (name) and `blend_gtin`; blends
  missing from `blend_master` fall back to the FG-carried name/GTIN in the UI.
- Nicotine % Wet = Dry × 0.875 (`NIC_WET_FACTOR`, computed server-side).
- Target weight: `W_TOB = (100/(100−M_IP))·W_dry ÷ tobacco_constant`. The
  **tobacco constant** (real-tobacco density) defaults to
  `DEFAULT_TOBACCO_CONSTANT = 0.99620799` in `target_calculation_service.py`,
  overridable via `system_config.tobacco_constant`; resolved server-side by
  `get_tobacco_constant()` and injected in `api_calculate_target` (never from
  the client). Matches the cell-trace PDF. Guarded by `tests/test_pdf_celltrace.py`.
- N_tgt cascade keys `skus.sku_code == fg.fg_code` (NOT cig_code — several SKUs
  share a cig_code with different nicotine). Matches the Data.xlsx SKU block.
- **Config-driven formulas**: both the target-weight calc AND the NPL calc run
  through `formula_service.compute(session, module, raw)` over ordered step
  chains stored in `formula_definitions`, evaluated by a sandboxed AST engine
  (`formula_engine.safe_eval` — no Python eval; whitelist of arithmetic +
  exp/log/sqrt/min/max/abs). `formula_defs.SPECS` holds per-module specs
  (`target_weight`, `npl`): steps, input metadata (value source), interim/output
  keys, build_ns. Steps fall back to built-in defaults when no DB row exists.
  Stored `formula_code` is namespaced `module:code` (same step codes recur
  across modules; the column is globally unique).
  Both the **FG Codes** page (Formula button replaced NPL) and the **NPL
  Calculate** page have a **Formula** button → modal showing each input
  (value + source), the step-by-step derivation with substituted values, and —
  for `MASTER_DATA.FORMULA_CONSTANTS` holders — editable expressions.
  Endpoints: `/fg-codes/api/formula/target-weight[/save]`,
  `/npl/api/formula/<po_id>` + `/npl/api/formula/save`. Guards:
  `tests/test_formula_engine.py`, `tests/test_pdf_celltrace.py`.
- **Optimizer** (`app/services/optimizer_solver.py`) reconstructs the legacy
  cGr8s-OPT staged solver: given a target W_CIG, it adjusts key variables in the
  KP-TOLERANCE priority (Tip Ventilation, then Filter PD, then Moisture/PaperCU/
  BlendNic) within staged bands (S1→S4, widening each stage), via monotonic
  bisection on the same forward engine, and records the Stage reached (or
  best-effort + unreachable). KP-tolerance stages read from lookups
  (`kp_tolerance`), physical clamps from formula_constants (Max_VF/Min_PD/Max_PD).
  Wired as the optimizer `direct` method (`app/modules/optimizer/__init__.py`);
  UI takes a target weight and shows revised key vars + stage. The
  target-weight equation is underdetermined (VF+FPD for one target), so the
  chosen VF/FPD split may differ from a given legacy row while hitting the same
  target. Guard: `tests/test_optimizer_solver.py`.
- Master data (fg_codes, skus, blends, machines, tobacco, lookups) loads from
  `Data.xlsx` (pw `ALW`); gamma/formula constants from `Constants.xlsx`. Reset
  toolkit: `scripts/backup_db.py`, `reset_and_load_from_data.py`,
  `seed_constants.py`. Local runs need `DB_AUTH_MODE=sql` + comma-port URI.
- NPL **Data Grid** (`/qa/data-grid`) shows `process_orders` (in-app runs), not
  Data.xlsx. Load production history from `cGr8s.xlsm` (Production Data + QA
  Analysis sheets) with `scripts/import_production_history.py` — SKUs absent
  from fg_codes are skipped, dup (PO,date) get a `/n` suffix, file ends
  2026-07-30.
- Monthly blend nicotine is editable only for the current and previous month.
- Blend Master page = single editable grid: all blends, used-this-month on top
  sorted by latest MTC production date desc; Save Month writes only used blends
  + rows the user explicitly touched.
- Calibration page hides Gamma — gamma is maintained in the Gamma Constants tab
  (`gamma_constants` table) and resolved by `key_variable_populator`.

## Required sequence for every task

1. Understand the impacted system → 2. Confirm requirement → 3. Risks/security
→ 4. Plan → 5. Implement → 6. Test → 7. Validate UI in browser with Playwright
→ 8. Retest until correct.

Never claim success without evidence. Never skip security review. Never skip
browser validation for UI-facing changes.

## Security

- `.env` holds real credentials (app DB, MTC DB, SMTP) — never commit it, never
  echo its values into chat, code, or docs. `.env.example` is the template.
- Note: `.vscode/mcp.json`, `.claude/agents/`, `.claude/skills/` are leftovers
  from an SAP ABAP workspace template and are unrelated to this app.
