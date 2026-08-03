"""Safe, config-driven formula engine for target-weight (and future) calculations.

Formulas are stored as text expressions in `formula_definitions` and evaluated
here with a strict AST whitelist — NO Python eval/exec. Only arithmetic on
names supplied in the namespace plus a small whitelist of math functions is
allowed; anything else (attribute access, subscripts, arbitrary calls, names
not in the namespace) raises FormulaError.

This lets authorised users edit the actual formula expressions while keeping
evaluation sandboxed.
"""
import ast
import math

# Whitelisted callables usable inside formulas.
FUNCTIONS = {
    "exp": math.exp, "log": math.log, "log10": math.log10, "ln": math.log,
    "sqrt": math.sqrt, "abs": abs, "min": min, "max": max,
    "round": round, "pow": pow,
}

# Allowed binary / unary operators.
_BIN = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: (a / b) if b != 0 else 0.0,   # guard: /0 -> 0 (legacy behaviour)
    ast.Mod: lambda a, b: (a % b) if b != 0 else 0.0,
    ast.Pow: lambda a, b: a ** b,
    ast.FloorDiv: lambda a, b: (a // b) if b != 0 else 0.0,
}
_UNARY = {ast.USub: lambda a: -a, ast.UAdd: lambda a: +a}


class FormulaError(ValueError):
    """Raised when an expression is invalid or references an unknown name."""


def _eval_node(node, names):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, names)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise FormulaError(f"literal not allowed: {node.value!r}")
        return float(node.value)
    if isinstance(node, ast.Name):
        if node.id in names:
            return float(names[node.id])
        raise FormulaError(f"unknown variable '{node.id}'")
    if isinstance(node, ast.BinOp):
        op = _BIN.get(type(node.op))
        if not op:
            raise FormulaError(f"operator not allowed: {type(node.op).__name__}")
        return op(_eval_node(node.left, names), _eval_node(node.right, names))
    if isinstance(node, ast.UnaryOp):
        op = _UNARY.get(type(node.op))
        if not op:
            raise FormulaError(f"unary operator not allowed: {type(node.op).__name__}")
        return op(_eval_node(node.operand, names))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in FUNCTIONS:
            raise FormulaError("only whitelisted functions may be called")
        if node.keywords:
            raise FormulaError("keyword arguments not allowed")
        args = [_eval_node(a, names) for a in node.args]
        try:
            return float(FUNCTIONS[node.func.id](*args))
        except (ValueError, OverflowError):
            return 0.0
    raise FormulaError(f"syntax element not allowed: {type(node).__name__}")


def safe_eval(expr: str, names: dict) -> float:
    """Evaluate a single arithmetic expression against `names`. Raises FormulaError."""
    if not expr or not str(expr).strip():
        raise FormulaError("empty expression")
    try:
        tree = ast.parse(str(expr), mode="eval")
    except SyntaxError as e:
        raise FormulaError(f"syntax error: {e.msg}")
    return _eval_node(tree, names)


def evaluate_steps(steps, namespace: dict):
    """Evaluate ordered steps, each adding its result to the namespace.

    steps: iterable of dicts with keys 'code' and 'expression'.
    Returns (results: {code: value}, breakdown: [{code, expression, value, error}]).
    A step that fails evaluation yields 0.0 and records the error (so one bad
    edited formula can't crash the whole calculation).
    """
    ns = dict(namespace)
    results, breakdown = {}, []
    for step in steps:
        code, expr = step["code"], step["expression"]
        try:
            val = safe_eval(expr, ns)
            err = None
        except FormulaError as e:
            val, err = 0.0, str(e)
        ns[code] = val
        results[code] = val
        breakdown.append({"code": code, "expression": expr, "value": val, "error": err})
    return results, breakdown


def validate_expression(expr: str, allowed_names) -> None:
    """Static check used before saving an edited formula. Raises FormulaError.

    Ensures the expression parses, uses only whitelisted syntax, and references
    only names in `allowed_names` (inputs + prior step codes).
    """
    dummy = {n: 1.0 for n in allowed_names}
    safe_eval(expr, dummy)  # will raise FormulaError on unknown name / bad syntax
