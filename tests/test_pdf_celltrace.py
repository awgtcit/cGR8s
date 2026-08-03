"""Golden-value guard for the FG 15200523.04 cell-trace PDF.

Pins the target-weight engine to the PDF's expected screen values so the
tobacco-constant divide and the dilution/filtration/nicotine chain cannot
silently regress. Pure math — no DB, no Flask.

  .venv/Scripts/python.exe -m pytest tests/test_pdf_celltrace.py
  (or run directly: .venv/Scripts/python.exe tests/test_pdf_celltrace.py)
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.target_calculation_service import (
    TargetCalculationService as S, DEFAULT_TOBACCO_CONSTANT,
)

# Inputs traced in cGr8s-CellTrace-15200523.04.pdf
KEY_VARS = dict(n_bld=1.6, p_cu=80, t_vnt=30, f_pd=340, m_ip=12.552)
CALIBRATION = dict(alpha=10, beta=-0.043, gamma=92.5, delta=-0.056, n_tgt=0.4)
FG_INFO = dict(c_plg=4, ntm_wt_mean=179, tobacco_constant=DEFAULT_TOBACCO_CONSTANT)

# §5 expected screen values
EXPECTED = {
    "stage1_dilution": 9.679, "stage2_dilution": 30.0, "total_dilution": 39.679,
    "filtration_pct": 91.708,
    "nic_demand_stage1": 0.443, "nic_demand_stage2": 0.571,
    "nic_demand_total": 0.663, "nicotine_filtration_pct": 4.824,
    "total_nicotine": 7.997,
    "w_dry": 499.802, "w_tob": 573.718, "w_cig": 752.718,
}


def test_pdf_celltrace_15200523_04():
    out = S.calculate_forward_target(KEY_VARS, CALIBRATION, FG_INFO)
    flat = {**out["interim_output"], **out["output_data"]}
    for box, exp in EXPECTED.items():
        got = flat[box]
        assert abs(got - exp) <= max(0.01, abs(exp) * 0.0006), \
            f"{box}: got {got}, PDF expects {exp}"


def test_tobacco_constant_default():
    assert DEFAULT_TOBACCO_CONSTANT == 0.99620799


if __name__ == "__main__":
    test_pdf_celltrace_15200523_04()
    test_tobacco_constant_default()
    print("PDF cell-trace golden values: ALL MATCH")
