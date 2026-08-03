"""Guards for the safe formula engine: sandbox rejects unsafe input, the default
target-weight chain reproduces the PDF, and an edited expression changes output.

  .venv/Scripts/python.exe tests/test_formula_engine.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.formula_engine import safe_eval, evaluate_steps, FormulaError
from app.services.formula_defs import TARGET_WEIGHT_STEPS, SPECS

STEPS = [{"code": c, "expression": e} for c, _, e in TARGET_WEIGHT_STEPS]
_RAW = dict(n_bld=1.6, p_cu=80, t_vnt=30, f_pd=340, m_ip=12.552,
            alpha=10, beta=-0.043, gamma=92.5, delta=-0.056, n_tgt=0.4,
            c_plg=4, ntm_wt_mean=179, tobacco_constant=0.99620799)


KV = CAL = FG = _RAW  # test shim: build_ns takes one flat dict now


def build_namespace(*_):
    return SPECS["target_weight"]["build_ns"](_RAW)


def test_sandbox_blocks_unsafe():
    for bad in ["__import__('os').system('x')", "().__class__", "open('x')",
                "a.b", "x[0]", "unknown_var + 1", "lambda: 1"]:
        try:
            safe_eval(bad, {"a": 1, "x": 1})
            raise AssertionError(f"should have rejected: {bad}")
        except FormulaError:
            pass


def test_arithmetic_and_funcs():
    assert abs(safe_eval("2 + 3 * 4", {}) - 14) < 1e-9
    assert abs(safe_eval("exp(0) + sqrt(9)", {}) - 4) < 1e-9
    assert safe_eval("a / b", {"a": 1, "b": 0}) == 0.0   # /0 guard


def test_default_chain_matches_pdf():
    res, _ = evaluate_steps(STEPS, build_namespace(KV, CAL, FG))
    assert abs(res["w_tob"] - 573.718) < 0.01
    assert abs(res["w_cig"] - 752.718) < 0.01


def test_edit_changes_output():
    edited = [dict(s) for s in STEPS]
    for s in edited:
        if s["code"] == "w_ntm":
            s["expression"] = "ntm_wt_mean + 21"
    res, _ = evaluate_steps(edited, build_namespace(KV, CAL, FG))
    assert abs(res["w_cig"] - 752.718 - 21) < 0.01


if __name__ == "__main__":
    test_sandbox_blocks_unsafe()
    test_arithmetic_and_funcs()
    test_default_chain_matches_pdf()
    test_edit_changes_output()
    print("formula engine: sandbox + parity + edit ALL PASS")
