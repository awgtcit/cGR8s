"""Target Weight Calculation Service – correct engineering formulas.

Formulas:
  Stage 1 Dilution  = α × (1 − exp(β × P_CU))          [β is negative]
  Stage 2 Dilution  = T_VNT
  Total Dilution    = Stage1 + Stage2
  Filtration %      = γ × (1 − exp(δ × F_PD / C_PLG))   [δ is negative]

  Pacifying Nicotine Demand:
    Stage 1         = (N_tgt × 100) / (100 − Stage1_Dilution)
    Stage 2         = (N_tgt × 100) / (100 − Stage2_Dilution)
    Total           = (N_tgt × 100) / (100 − Total_Dilution)

  Total Nicotine    = (Total × 100) / ((1 − Filtration/100) × 100)
  W_dry  (mg)       = Total_Nicotine / (N_BLD / 100)   [N_BLD is in %]
  W_tob  (mg)       = (100 / (100 − M_IP)) × W_dry
  W_cig  (mg)       = W_tob + W_NTM
  TW     (mg)       = W_cig  (synonym)
"""
import math
from typing import Dict, Any


class TargetCalculationService:
    """Service for performing forward target weight calculations."""

    @staticmethod
    def calculate_forward_target(key_vars: Dict[str, Any],
                                 calibration: Dict[str, Any],
                                 fg_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform forward target calculation using correct exponential formulas.

        Args:
            key_vars: n_bld, p_cu, t_vnt, f_pd, m_ip
            calibration: alpha, beta, gamma, delta, n_tgt
            fg_info: c_plg, ntm_wt_mean (from FG Code)

        Returns:
            Dictionary with interim_output and output_data results
        """
        # Extract key variables
        n_bld = float(key_vars.get('n_bld', 0))
        p_cu = float(key_vars.get('p_cu', 0))
        t_vnt = float(key_vars.get('t_vnt', 0))
        f_pd = float(key_vars.get('f_pd', 0))
        m_ip = float(key_vars.get('m_ip', 0))

        # Extract calibration constants
        alpha = float(calibration.get('alpha', 0))
        beta_raw = float(calibration.get('beta', 0))
        gamma = float(calibration.get('gamma', 0))
        delta_raw = float(calibration.get('delta', 0))
        n_tgt = float(calibration.get('n_tgt', 0))

        # β and δ must be negative by physics; normalize regardless of source sign
        beta = -abs(beta_raw) if beta_raw else 0.0
        delta = -abs(delta_raw) if delta_raw else 0.0

        # Extract FG physical info
        fg_info = fg_info or {}
        c_plg = float(fg_info.get('c_plg', 1))
        ntm_wt_mean = float(fg_info.get('ntm_wt_mean', 0))

        # Guard against zero c_plg
        if c_plg == 0:
            c_plg = 1

        # ── Stage 1: Dilution ────────────────────────────────────
        stage1_dilution = alpha * (1 - math.exp(beta * p_cu))

        # ── Stage 2: Dilution ────────────────────────────────────
        stage2_dilution = t_vnt

        # ── Total Dilution ───────────────────────────────────────
        total_dilution = stage1_dilution + stage2_dilution

        # ── Filtration % ─────────────────────────────────────────
        filtration_pct = gamma * (1 - math.exp(delta * f_pd / c_plg))

        # ── Nicotine Demand ──────────────────────────────────────
        # Per-stage Pacifying Nicotine Demand
        if stage1_dilution >= 100:
            nic_demand_stage1 = 0
        else:
            nic_demand_stage1 = (n_tgt * 100) / (100 - stage1_dilution)

        if stage2_dilution >= 100:
            nic_demand_stage2 = 0
        else:
            nic_demand_stage2 = (n_tgt * 100) / (100 - stage2_dilution)

        if total_dilution >= 100:
            nic_demand_total = 0
        else:
            nic_demand_total = (n_tgt * 100) / (100 - total_dilution)

        # ── Total Nicotine ───────────────────────────────────────
        filtration_factor = (1 - filtration_pct / 100)
        if filtration_factor <= 0:
            total_nicotine = 0
        else:
            total_nicotine = (nic_demand_total * 100) / ((1 - filtration_pct / 100) * 100)

        # ── Output Weights (in mg) ───────────────────────────────────
        # N_BLD is a percentage (e.g. 1.663 means 1.663%)
        # w_dry = total_nicotine / (n_bld / 100)  → result in mg
        if n_bld <= 0:
            w_dry = 0
        else:
            w_dry = total_nicotine / (n_bld / 100)

        if m_ip >= 100:
            w_tob = w_dry
        else:
            w_tob = (100 / (100 - m_ip)) * w_dry

        w_ntm = ntm_wt_mean
        w_cig = w_tob + w_ntm
        tw = w_cig

        return {
            'interim_output': {
                'stage1_dilution': round(stage1_dilution, 3),
                'stage2_dilution': round(stage2_dilution, 3),
                'total_dilution': round(total_dilution, 3),
                'filtration_pct': round(filtration_pct, 3),
                'nic_demand_stage1': round(nic_demand_stage1, 3),
                'nic_demand_stage2': round(nic_demand_stage2, 3),
                'nic_demand_total': round(nic_demand_total, 3),
                'total_nicotine': round(total_nicotine, 3),
            },
            'output_data': {
                'w_dry': round(w_dry, 3),
                'w_tob': round(w_tob, 3),
                'w_cig': round(w_cig, 3),
                'w_ntm': round(w_ntm, 3),
                'tw': round(tw, 3),
            }
        }

    @staticmethod
    def validate_key_variables(key_vars: Dict[str, Any]) -> bool:
        """Validate that key variables are present and numeric."""
        required_vars = ['n_bld', 'p_cu', 't_vnt', 'f_pd', 'm_ip']
        for var in required_vars:
            if var not in key_vars:
                return False
            try:
                float(key_vars[var])
            except (ValueError, TypeError):
                return False
        return True

    @staticmethod
    def validate_calibration_constants(calibration: Dict[str, Any]) -> bool:
        """Validate that calibration constants are present and numeric."""
        required_constants = ['alpha', 'beta', 'gamma', 'delta', 'n_tgt']
        for constant in required_constants:
            if constant not in calibration:
                return False
            try:
                float(calibration[constant])
            except (ValueError, TypeError):
                return False
        return True
