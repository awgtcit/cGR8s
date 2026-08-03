"""Config-driven computation on top of the safe formula engine.

Module-generic: works for any spec in formula_defs.SPECS (target_weight, npl).
Loads that module's step chain from `formula_definitions` (falling back to the
built-in defaults), evaluates it, and returns results in the shape the callers
expect PLUS a per-step breakdown and input list for the Formula panel.
"""
import json
import re

from app.services.formula_engine import evaluate_steps, safe_eval, FormulaError
from app.services.formula_defs import SPECS


def _spec(module):
    if module not in SPECS:
        raise FormulaError(f"unknown formula module '{module}'")
    return SPECS[module]


def _dbcode(module, code):
    """Storage key for formula_code. It is globally unique in the table, but the
    same step code (e.g. stage1_dilution) is used by multiple modules, so we
    namespace it by module to avoid collisions."""
    return f"{module}:{code}"


def _logical(formula_code):
    """Strip the module prefix; tolerate legacy unprefixed rows."""
    return formula_code.split(":", 1)[1] if ":" in formula_code else formula_code


def load_steps(session, module):
    """Ordered [{code,name,expression}] from DB for `module`, else defaults."""
    from app.models.report import FormulaDefinition
    spec = _spec(module)
    rows = session.query(FormulaDefinition).filter(
        FormulaDefinition.module == module,
        FormulaDefinition.is_active == "Y",
    ).all()
    by_code = {_logical(r.formula_code): r for r in rows}
    steps = []
    for i, (code, name, expr) in enumerate(spec["steps"]):
        r = by_code.get(code)
        if r and r.formula_expression:
            order = i
            try:
                order = json.loads(r.parameters or "{}").get("order", i)
            except (ValueError, TypeError):
                pass
            steps.append({"code": code, "name": r.formula_name or name,
                          "expression": r.formula_expression, "order": order})
        else:
            steps.append({"code": code, "name": name, "expression": expr, "order": i})
    steps.sort(key=lambda s: s["order"])
    return steps


def _substitute(expr, ns):
    def repl(m):
        tok = m.group(0)
        return f"{ns[tok]:.4g}" if tok in ns else tok
    return re.sub(r"[A-Za-z_][A-Za-z0-9_]*", repl, expr)


def compute(session, module, raw_inputs):
    """Compute `module` outputs from stored formulas over raw_inputs.
    Returns interim_output, output_data, steps (breakdown), inputs (value+source)."""
    spec = _spec(module)
    steps = load_steps(session, module)
    ns = spec["build_ns"](raw_inputs)
    results, breakdown = evaluate_steps(steps, ns)

    step_meta = {s["code"]: s for s in steps}
    running, detailed = dict(ns), []
    for b in breakdown:
        code = b["code"]
        detailed.append({
            "code": code, "name": step_meta[code]["name"],
            "expression": b["expression"], "substituted": _substitute(b["expression"], running),
            "value": round(b["value"], 4), "error": b["error"],
        })
        running[code] = b["value"]

    inputs = []
    for var, (label, unit, source) in spec["input_meta"].items():
        if var in ns:
            inputs.append({"var": var, "label": label, "unit": unit,
                           "source": source, "value": round(ns[var], 6)})

    ri, ro = spec["round_interim"], spec["round_output"]
    interim = {k: round(results.get(k, 0.0), ri) for k in spec["interim"]}
    output = {k: round(results.get(k, 0.0), ro) for k in spec["output"]}
    return {"interim_output": interim, "output_data": output,
            "steps": detailed, "inputs": inputs}


def _allowed_names_upto(spec, step_code):
    names = set(spec["input_meta"].keys())
    for code, _, _ in spec["steps"]:
        if code == step_code:
            break
        names.add(code)
    return names


def validate_and_save(session, module, edits, user=None):
    """Validate + upsert edited expressions for `module` (version bump).
    Raises FormulaError on the first invalid expression."""
    from app.models.report import FormulaDefinition
    from app.models.base import generate_uuid
    spec = _spec(module)
    defaults = {c: (n, e) for c, n, e in spec["steps"]}
    order_of = {c: i for i, (c, _, _) in enumerate(spec["steps"])}

    for code, expr in edits.items():
        if code not in defaults:
            raise FormulaError(f"unknown formula '{code}'")
        safe_eval(expr, {n: 1.0 for n in _allowed_names_upto(spec, code)})

    for code, expr in edits.items():
        row = session.query(FormulaDefinition).filter(
            FormulaDefinition.module == module,
            FormulaDefinition.formula_code.in_([_dbcode(module, code), code]),
        ).first()
        if row:
            row.formula_code = _dbcode(module, code)   # migrate legacy unprefixed
            row.formula_expression = expr
            row.version = (row.version or 1) + 1
            row.is_active = "Y"
            row.updated_by = user
        else:
            session.add(FormulaDefinition(
                id=generate_uuid(), formula_code=_dbcode(module, code), module=module,
                formula_name=defaults[code][0], formula_expression=expr,
                parameters=json.dumps({"order": order_of[code]}),
                version=1, is_active="Y", created_by=user, updated_by=user,
            ))
        session.flush()   # surface any integrity error against the offending row
