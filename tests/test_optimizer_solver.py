"""Guard for the staged target-weight optimizer (reconstruction of cGr8s-OPT).

Uses the real target-weight engine as the forward model. Asserts the solver
hits a reachable target within tolerance by adjusting within the KP-TOLERANCE
stages, escalates stages when needed, and flags an unreachable target.

  .venv/Scripts/python.exe tests/test_optimizer_solver.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.target_calculation_service import TargetCalculationService as S
from app.services.optimizer_solver import optimize_to_target, EPS

CAL = dict(alpha=10, beta=-0.043, gamma=92.5, delta=-0.056, n_tgt=0.4)
FG = dict(c_plg=4, ntm_wt_mean=179, tobacco_constant=0.99620799)
BASE = dict(n_bld=1.6, p_cu=80, t_vnt=30, f_pd=340, m_ip=12.552)
CONSTS = {"Max_VF": 65, "Min_PD": 220, "Max_PD": 450}


def forward(kv):
    return S.calculate_forward_target(
        {k: kv[k] for k in ("n_bld", "p_cu", "t_vnt", "f_pd", "m_ip")}, CAL, FG
    )["output_data"]["w_cig"]


def test_small_target_reached_stage1():
    base_wcig = forward(BASE)
    target = base_wcig - 8.0            # small drop -> reachable by Tip Vent in stage 1
    r = optimize_to_target(BASE, target, forward, constants=CONSTS)
    assert r["reached"] and r["stage"] == 1
    assert abs(r["achieved_wcig"] - target) <= EPS + 1e-6
    assert r["revised"]["t_vnt"] < BASE["t_vnt"]   # lowered ventilation to reduce weight


def test_bigger_target_escalates_stage():
    base_wcig = forward(BASE)
    target = base_wcig - 120.0          # needs more than stage-1 band -> escalates
    r = optimize_to_target(BASE, target, forward, constants=CONSTS)
    assert r["reached"] and r["stage"] >= 2
    assert abs(r["achieved_wcig"] - target) <= max(EPS, 1.0)


def test_unreachable_flags_not_reached():
    r = optimize_to_target(BASE, 5.0, forward, constants=CONSTS)   # far below any feasible weight
    assert r["reached"] is False and r["stage"] == 4


if __name__ == "__main__":
    test_small_target_reached_stage1()
    test_bigger_target_escalates_stage()
    test_unreachable_flags_not_reached()
    print("optimizer solver: reach + escalate + unreachable ALL PASS")
