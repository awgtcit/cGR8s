"""Source-of-truth definitions for the config-driven formula chains.

Each module (target_weight, npl) has a SPEC: ordered steps (step code ==
output key), input metadata (value source shown in the Formula panel), the
interim/output groupings, and a build_ns() that normalises raw inputs into the
evaluation namespace. Seeded/overridden per step in `formula_definitions`.
"""


def _fl(d, k, default=0.0):
    try:
        return float(d.get(k, default) if d.get(k, default) is not None else default)
    except (TypeError, ValueError):
        return default


# ══════════════════════════ TARGET WEIGHT ══════════════════════════
TARGET_WEIGHT_STEPS = [
    ("stage1_dilution", "Stage-1 Dilution", "alpha * (1 - exp(beta * p_cu))"),
    ("stage2_dilution", "Stage-2 Dilution", "t_vnt"),
    ("total_dilution", "Total Dilution", "stage1_dilution + stage2_dilution"),
    ("filtration_pct", "Filtration %", "gamma * (1 - exp(delta * f_pd / c_plg))"),
    ("nic_demand_stage1", "Pacifying Nicotine - Stage 1", "(n_tgt * 100) / (100 - stage1_dilution)"),
    ("nic_demand_stage2", "Pacifying Nicotine - Stage 2", "(n_tgt * 100) / (100 - stage2_dilution)"),
    ("nic_demand_total", "Pacifying Nicotine - Total (NTD)", "(n_tgt * 100) / (100 - total_dilution)"),
    ("nicotine_filtration_pct", "Nicotine Filtration %", "(n_tgt * 100) / (100 - filtration_pct)"),
    ("total_nicotine", "Total Nicotine (NTDRY)", "nic_demand_total / (1 - filtration_pct / 100)"),
    ("w_dry", "W DRY (mg)", "total_nicotine / (n_bld / 100)"),
    ("w_ntm", "W NTM (mg)", "ntm_wt_mean"),
    ("w_tob", "W TOB (mg)", "(100 / (100 - m_ip)) * w_dry / tobacco_constant"),
    ("w_cig", "W CIG / Target Weight (mg)", "w_tob + w_ntm"),
]
TW_INTERIM = ["stage1_dilution", "stage2_dilution", "total_dilution", "filtration_pct",
              "nic_demand_stage1", "nic_demand_stage2", "nic_demand_total",
              "nicotine_filtration_pct", "total_nicotine"]
TW_OUTPUT = ["w_dry", "w_tob", "w_cig", "w_ntm"]
TW_INPUT_META = {
    "n_bld": ("N_BLD", "Nicotine %", "Monthly blend nicotine (tobacco_blend_analysis) -> BlendMaster -> last run"),
    "p_cu": ("P_CU", "Paper CU", "Size->CU lookup from format prefix (lookups: size_cu)"),
    "t_vnt": ("T_VNT", "Tip Ventilation", "FG target: Tip Ventilation"),
    "f_pd": ("F_PD", "Filter PD", "FG target: Filter PD"),
    "m_ip": ("M_IP", "Maker Moisture", "FG target: Maker Moisture"),
    "n_tgt": ("N_TGT", "Target Nicotine", "SKU nicotine (sku_code=fg_code) -> FG target_nic"),
    "alpha": ("alpha", "Dilution coefficient", "Formula constants (Constants.xlsx)"),
    "beta": ("beta", "Dilution exponent", "Formula constants (negative)"),
    "gamma": ("gamma", "Filtration coefficient", "Gamma constants (format, plug length, N_tgt<0.3)"),
    "delta": ("delta", "Filtration exponent", "Formula constants (negative)"),
    "c_plg": ("C_PLG", "No. of cuts", "FG: No. of cuts"),
    "ntm_wt_mean": ("W_NTM", "NTM weight", "FG: NTM Wt. Mean"),
    "tobacco_constant": ("tobacco_constant", "Tobacco density", "System config: tobacco_constant (global)"),
}


def _build_tw_ns(raw):
    from app.services.target_calculation_service import DEFAULT_TOBACCO_CONSTANT
    beta, delta = _fl(raw, "beta"), _fl(raw, "delta")
    tc = _fl(raw, "tobacco_constant", DEFAULT_TOBACCO_CONSTANT) or DEFAULT_TOBACCO_CONSTANT
    return {
        "n_bld": _fl(raw, "n_bld"), "p_cu": _fl(raw, "p_cu"), "t_vnt": _fl(raw, "t_vnt"),
        "f_pd": _fl(raw, "f_pd"), "m_ip": _fl(raw, "m_ip"),
        "alpha": _fl(raw, "alpha"), "beta": -abs(beta) if beta else 0.0,
        "gamma": _fl(raw, "gamma"), "delta": -abs(delta) if delta else 0.0,
        "n_tgt": _fl(raw, "n_tgt"), "c_plg": _fl(raw, "c_plg", 1) or 1.0,
        "ntm_wt_mean": _fl(raw, "ntm_wt_mean"), "tobacco_constant": tc if tc > 0 else 1.0,
    }


# ══════════════════════════ NPL ══════════════════════════
NPL_STEPS = [
    ("stage1_dilution", "Stage-1 Dilution", "alpha * (1 - exp(beta * p_cu))"),
    ("total_dilution", "Total Dilution", "stage1_dilution + t_vnt"),
    ("dilution_factor", "Dilution Factor", "100 / (100 - total_dilution)"),
    ("filtration_pct", "Filtration %", "gamma * (1 - exp(delta * f_pd / n_c))"),
    ("filtration_factor", "Filtration Factor", "100 / (100 - filtration_pct)"),
    ("w_dry", "Theoretical W DRY (mg/cig)", "n_tgt * dilution_factor * filtration_factor / (n_bld / 100)"),
    ("w_tob_calc", "Theoretical W TOB (mg/cig)", "w_dry * (100 / (100 - m_ip))"),
    ("theoretical", "Theoretical Consumption", "w_tob_calc * n_mc * n_cg"),
    ("adjusted_tobacco", "Adjusted Tobacco", "(t_iss - t_un) * ((100 - m_dsp) / (100 - m_ip))"),
    ("total_losses", "Total Losses", "l_dst + l_win + l_flr + l_srt + l_dt"),
    ("adjusted_losses", "Adjusted Losses", "total_losses * ((100 - m_dst) / (100 - m_ip))"),
    ("total_waste", "Total Wastage", "r_mkg + r_pkg + r_ndt"),
    ("cig_weight", "Cigarette Weight", "n_w + w_tob"),
    ("waste_tob_fraction", "Tobacco Wastage Fraction", "(total_waste / cig_weight) * w_tob"),
    ("actual", "Actual Consumption", "adjusted_tobacco - (adjusted_losses + waste_tob_fraction)"),
    ("npl_pct", "NPL %", "((actual - theoretical) / theoretical) * 100"),
    ("t_usd", "Tobacco Used", "l_dst - t_iss"),
    ("npl_kg", "NPL kg", "(npl_pct / 100) * t_usd / 1000000"),
    ("tac", "TAC (Total Adjusted Consumption)", "(t_iss * (100 - m_dsp) / (100 - m_ip)) - (total_losses * (100 - m_dst) / (100 - m_ip))"),
    ("ttc", "TTC (Total Theoretical Consumption)", "tac / (1 + npl_pct / 100)"),
]
NPL_OUTPUT = ["npl_pct", "npl_kg", "tac", "ttc"]
NPL_INTERIM = [c for c, _, _ in NPL_STEPS if c not in NPL_OUTPUT]
NPL_INPUT_META = {
    "n_bld": ("N_BLD", "Nicotine %", "Key variables (from Target Weight)"),
    "p_cu": ("P_CU", "Paper CU", "Key variables"),
    "t_vnt": ("T_VNT", "Tip Ventilation", "Key variables"),
    "f_pd": ("F_PD", "Filter PD", "Key variables"),
    "m_ip": ("M_IP", "Input Moisture", "Key variables"),
    "alpha": ("alpha", "Dilution coefficient", "Calibration snapshot"),
    "beta": ("beta", "Dilution exponent", "Calibration snapshot (negative)"),
    "gamma": ("gamma", "Filtration coefficient", "Calibration snapshot"),
    "delta": ("delta", "Filtration exponent", "Calibration snapshot (negative)"),
    "n_tgt": ("N_TGT", "Target Nicotine", "Calibration snapshot"),
    "n_c": ("N_C", "No. of cuts", "FG: No. of cuts"),
    "w_tob": ("W_TOB", "Cig tobacco weight", "Target Weight result"),
    "t_iss": ("T_ISS", "Tobacco Issued (mg)", "NPL form"),
    "t_un": ("T_UN", "Tobacco Unused (mg)", "NPL form"),
    "l_dst": ("L_DST", "Loss - Dust", "NPL form"),
    "l_win": ("L_WIN", "Loss - Winnowing", "NPL form"),
    "l_flr": ("L_FLR", "Loss - Floor", "NPL form"),
    "l_srt": ("L_SRT", "Loss - Sort", "NPL form"),
    "l_dt": ("L_DT", "Loss - Downtime", "NPL form"),
    "n_mc": ("N_MC", "No. of Master Cases", "NPL form"),
    "n_cg": ("N_CG", "Cigs per Case", "NPL form"),
    "r_mkg": ("R_MKG", "Wastage - Maker (kg)", "NPL form"),
    "r_pkg": ("R_PKG", "Wastage - Packer (kg)", "NPL form"),
    "r_ndt": ("R_NDT", "Wastage - NDT", "NPL form"),
    "m_dsp": ("M_DSP", "Moisture - Dispensed", "NPL form"),
    "m_dst": ("M_DST", "Moisture - Dust", "NPL form"),
    "n_w": ("N_W", "NTM weight per cig", "NPL form"),
}


def _build_npl_ns(raw):
    beta, delta = _fl(raw, "beta"), _fl(raw, "delta")
    ns = {k: _fl(raw, k) for k in NPL_INPUT_META}
    ns["beta"] = -abs(beta) if beta else 0.0
    ns["delta"] = -abs(delta) if delta else 0.0
    ns["n_c"] = _fl(raw, "n_c", 1) or 1.0
    return ns


SPECS = {
    "target_weight": {
        "steps": TARGET_WEIGHT_STEPS, "input_meta": TW_INPUT_META,
        "interim": TW_INTERIM, "output": TW_OUTPUT, "build_ns": _build_tw_ns,
        "round_output": 3, "round_interim": 3,
    },
    "npl": {
        "steps": NPL_STEPS, "input_meta": NPL_INPUT_META,
        "interim": NPL_INTERIM, "output": NPL_OUTPUT, "build_ns": _build_npl_ns,
        "round_output": 4, "round_interim": 4,
    },
}
