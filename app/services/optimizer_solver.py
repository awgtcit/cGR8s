"""Staged target-weight optimizer — reconstruction of the legacy cGr8s-OPT solver.

Given a target cigarette weight, it adjusts the key variables within the
KP-TOLERANCE stage bands (widening S1 -> S4) until the forward model's W_CIG
reaches the target, recording the stage that succeeded. The forward model is
injected (the same config-driven target-weight engine used everywhere), so the
optimizer stays consistent with Target Weight and any edited formulas.

Legacy behaviour (verified against the old cGr8s.xlsm revised block):
  * primarily moves Tip Ventilation (VF) then Filter PD; a param is pushed to
    its band edge and the next param takes the remainder,
  * W_CIG is monotonically increasing in each of these, so each param is solved
    by bisection when it brackets the target, else pinned at its best edge,
  * Stage No is the stage at which the target was met; if unreachable even at
    the widest stage the result is the best effort and reached=False.
"""

# Adjustable key variables, in the legacy KP-TOLERANCE priority (weight movers
# first: Tip Ventilation, Filter PD, then the fine-tolerance ones).
PRIORITY = ["t_vnt", "f_pd", "m_ip", "p_cu", "n_bld"]

# KP-TOLERANCE max deviation per stage (from Constants.xlsx / Data.xlsx).
# Stage 4 = best effort: physical bounds only.
DEFAULT_STAGE_TOLS = [
    {"t_vnt": 10, "f_pd": 10, "m_ip": 0.002},
    {"t_vnt": 20, "f_pd": 20, "m_ip": 0.004},
    {"t_vnt": 75, "f_pd": 220, "m_ip": 0.004, "p_cu": 0.1, "n_bld": 0.1},
    {"t_vnt": 1e9, "f_pd": 1e9, "m_ip": 1e9, "p_cu": 1e9, "n_bld": 1e9},
]

EPS = 0.25  # mg — target-match tolerance


def _phys_bounds(param, constants):
    """Physical clamp for a parameter (relaxed only by the KP band)."""
    c = constants or {}
    if param == "t_vnt":
        return 0.0, float(c.get("Max_VF", 65) or 65)
    if param == "f_pd":
        # min not clamped hard — legacy stage-4 goes below Min_PD; keep a sane floor
        return 1.0, float(c.get("Max_PD", 450) or 450)
    if param == "m_ip":
        return 0.0, 30.0
    if param == "p_cu":
        return 1.0, 200.0
    if param == "n_bld":
        return 0.01, 10.0
    return float("-inf"), float("inf")


def _solve_param(kv, param, lo, hi, target, forward):
    """W_CIG is monotone increasing in `param`. If the target is bracketed on
    [lo,hi], bisection-solve it; otherwise pin to the edge nearest the target so
    the next priority parameter can take the remainder."""
    if hi <= lo:
        return kv[param]

    def f(x):
        k = dict(kv); k[param] = x
        return forward(k)

    flo, fhi = f(lo), f(hi)
    if (flo - target) * (fhi - target) <= 0:      # bracketed -> root find
        a, b, fa = lo, hi, flo
        for _ in range(60):
            mid = (a + b) / 2.0
            fm = f(mid)
            if abs(fm - target) <= EPS:
                return mid
            if (fa - target) * (fm - target) <= 0:
                b = mid
            else:
                a, fa = mid, fm
        return (a + b) / 2.0
    return lo if abs(flo - target) < abs(fhi - target) else hi


def optimize_to_target(base_kv, target_wcig, forward, *, constants=None,
                       stage_tols=None):
    """base_kv: {t_vnt,f_pd,m_ip,p_cu,n_bld,...} current key variables.
    forward: callable(kv_dict) -> W_CIG (mg).
    Returns dict: revised (key vars), stage (1..4), reached (bool),
    achieved_wcig, target_wcig, deltas {param: revised-nominal}."""
    stage_tols = stage_tols or DEFAULT_STAGE_TOLS
    nominal = {p: float(base_kv.get(p, 0) or 0) for p in PRIORITY}
    target_wcig = float(target_wcig)

    best_kv, best_gap, best_stage = dict(base_kv), float("inf"), len(stage_tols)
    for stage_no, tols in enumerate(stage_tols, 1):
        kv = dict(base_kv)
        for p in PRIORITY:
            tol = tols.get(p)
            if not tol:
                continue
            lo_p, hi_p = _phys_bounds(p, constants)
            lo = max(nominal[p] - tol, lo_p)
            hi = min(nominal[p] + tol, hi_p)
            kv[p] = _solve_param(kv, p, lo, hi, target_wcig, forward)
            gap = abs(forward(kv) - target_wcig)
            if gap < best_gap:
                best_kv, best_gap, best_stage = dict(kv), gap, stage_no
            if gap <= EPS:
                return _result(kv, nominal, stage_no, True, forward, target_wcig)
    return _result(best_kv, nominal, best_stage, False, forward, target_wcig)


def _result(kv, nominal, stage, reached, forward, target):
    achieved = forward(kv)
    return {
        "revised": {p: kv.get(p) for p in PRIORITY},
        "deltas": {p: round((kv.get(p, 0) or 0) - nominal[p], 4) for p in PRIORITY},
        "stage": stage,
        "reached": reached,
        "achieved_wcig": round(achieved, 3),
        "target_wcig": round(target, 3),
    }
