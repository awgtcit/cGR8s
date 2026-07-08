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

## External MTC production DB

`app/modules/fg_codes/__init__.py` connects via pyodbc (ODBC Driver 17) to the
MTC SQL Server (`MTC_DB_*` in `.env`) — tables `tabfinishgoods` + `brands`:

- `_fetch_mtc_brandcodes(date)` — FG brandcodes produced on a date (FG Codes page daily list)
- `fetch_mtc_month_brandcode_dates(year, month)` — `{brandcode: last production date}`
  for a month (Blend Master "Last Used")

Everything degrades gracefully when MTC is unreachable (full list / no dates).
Production servers need: env vars, ODBC Driver 17, network access to the MTC host.

## Domain rules & data quirks (important)

- `tobacco_blend_analysis.blend_name` holds **either a blend code or a tobacco
  name** (e.g. `50.0097` or `COVINA`). Always look up by BOTH — repo methods
  `get_month_value` / `get_latest_before` accept a list of keys. New monthly
  saves are stored under the tobacco **name** (values are per tobacco, several
  blend codes can share one name).
- `fg_codes` rows carry `blend_code`, `blend` (name) and `blend_gtin`; blends
  missing from `blend_master` fall back to the FG-carried name/GTIN in the UI.
- Nicotine % Wet = Dry × 0.875 (`NIC_WET_FACTOR`, computed server-side).
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
