"""
NPL (Non-Product Losses) Calculation Service.
Implements the exact NPL formula from the legacy system.

NPL% = (Actual_Consumption - Theoretical_Consumption) / Theoretical_Consumption × 100

Where:
  Actual = (T_ISS - T_UN) × (100-M_DSP)/(100-M_IP)
           - [losses × (100-M_DST)/(100-M_IP)  +  waste_tobacco_fraction]
  Theoretical = w_tob × N_MC × N_CG
  w_tob uses the same dilution/filtration sub-formulas as Target Weight.

  T_USD = L_DST - T_ISS
  NPL kg = (NPL%/100) × T_USD
  TAC = ROUND((T_ISS×(100-M_DSP)/(100-M_IP)) - (RW1×(100-M_DST)/(100-M_IP)), 2)
  TTC = ROUND(TAC / (1 + NPL%/100), 2)
"""
import math
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NPLInput:
    """NPL calculation inputs – matches legacy NPL window fields."""
    # ── NPL form inputs ──────────────────────────────────────────────────
    t_iss: float = 0        # Tobacco Issued
    t_un: float = 0         # Tobacco Unused
    l_dst: float = 0        # Loss - Dust
    l_win: float = 0        # Loss - Winnowing
    l_flr: float = 0        # Loss - Floor
    l_srt: float = 0        # Loss - Sort
    l_dt: float = 0         # Loss - Downtime
    n_mc: float = 0         # Number of Master Cases
    n_cg: float = 0         # Number of Cigarettes per Case
    r_mkg: float = 0        # Wastage - Maker (kg)
    r_ndt: float = 0        # Wastage - NDT
    r_pkg: float = 0        # Wastage - Packer (kg)
    m_dsp: float = 0        # Moisture - Dispensed
    m_dst: float = 0        # Moisture - Dust
    n_w: float = 0          # NTM weight (W_NTM from TW, mg per cig)

    # ── Key variables (from TW / Process Order) ──────────────────────────
    n_bld: float = 0        # Blend Nicotine (%)
    p_cu: float = 0         # Cigarette Paper CU
    t_vnt: float = 0        # Tip Ventilation
    f_pd: float = 0         # Filter Pressure Drop
    m_ip: float = 0         # Input Moisture

    # ── Calibration constants ────────────────────────────────────────────
    alpha: float = 0
    beta: float = 0         # negative in DB
    gamma_val: float = 0
    delta: float = 0        # negative in DB
    n_tgt: float = 0        # Target Nicotine

    # ── FG code info ─────────────────────────────────────────────────────
    n_c: float = 1          # c_plg (number of cuts from FG code)
    w_tob: float = 0        # W_TOB from TW result (mg per cig)


@dataclass
class NPLResult:
    """NPL calculation results."""
    npl_pct: float          # NPL percentage
    npl_kg: float           # NPL in kilograms
    tac: float              # Total Adjusted Consumption
    ttc: float              # Total Theoretical Consumption
    t_usd: float            # Tobacco Used (L_DST - T_ISS)
    actual_consumption: float
    theoretical_consumption: float


class NPLCalculator:
    """
    Calculates Non-Product Losses (NPL) using the legacy system formula.

    Uses the same dilution/filtration sub-formulas as Target Weight calculation
    to compute theoretical tobacco consumption, then compares against actual
    moisture-adjusted usage.
    """

    def calculate(self, inp: NPLInput) -> NPLResult:
        logger.debug('NPL calc: t_iss=%.3f, t_un=%.3f, n_mc=%.0f, n_cg=%.0f',
                      inp.t_iss, inp.t_un, inp.n_mc, inp.n_cg)

        # Guard against zero c_plg
        n_c = inp.n_c if inp.n_c != 0 else 1

        # ── Dilution (same as TW) ────────────────────────────────
        # beta is negative in DB, so exp(beta * p_cu) gives exp(-|beta|*p_cu)
        stage1_dilution = inp.alpha * (1 - math.exp(inp.beta * inp.p_cu))
        total_dilution = stage1_dilution + inp.t_vnt

        if total_dilution >= 100:
            dilution_factor = 0
        else:
            dilution_factor = 100 / (100 - total_dilution)

        # ── Filtration (same as TW) ──────────────────────────────
        # delta is negative in DB
        filtration_pct = inp.gamma_val * (1 - math.exp(inp.delta * inp.f_pd / n_c))

        if filtration_pct >= 100:
            filtration_factor = 0
        else:
            filtration_factor = 100 / (100 - filtration_pct)

        # ── Theoretical weight per cigarette ─────────────────────
        # w_dry = n_tgt × dilution_factor × filtration_factor / (n_bld/100)
        if inp.n_bld <= 0:
            w_dry = 0
        else:
            w_dry = inp.n_tgt * dilution_factor * filtration_factor / (inp.n_bld / 100)

        # w_tob = w_dry × (100 / (100 - m_ip))
        if inp.m_ip >= 100:
            w_tob_calc = w_dry
        else:
            w_tob_calc = w_dry * (100 / (100 - inp.m_ip))

        # ── Total theoretical consumption ────────────────────────
        theoretical = w_tob_calc * inp.n_mc * inp.n_cg

        # ── Actual consumption (moisture-adjusted) ───────────────
        if (100 - inp.m_ip) == 0:
            adjusted_tobacco = 0
            adjusted_losses = 0
        else:
            adjusted_tobacco = (inp.t_iss - inp.t_un) * (
                (100 - inp.m_dsp) / (100 - inp.m_ip)
            )
            total_losses = inp.l_dst + inp.l_win + inp.l_flr + inp.l_srt + inp.l_dt
            adjusted_losses = total_losses * (
                (100 - inp.m_dst) / (100 - inp.m_ip)
            )

        # Tobacco portion of wastage
        total_waste = inp.r_mkg + inp.r_pkg + inp.r_ndt
        cig_weight = inp.n_w + inp.w_tob   # NTM + tobacco = total cig weight
        if cig_weight <= 0:
            waste_tob_fraction = 0
        else:
            waste_tob_fraction = (total_waste / cig_weight) * inp.w_tob

        actual = adjusted_tobacco - (adjusted_losses + waste_tob_fraction)

        # ── NPL % ────────────────────────────────────────────────
        if theoretical == 0:
            npl_pct = 0
        else:
            npl_pct = ((actual - theoretical) / theoretical) * 100

        # ── T_USD (Tobacco Used) ─────────────────────────────────
        t_usd = inp.l_dst - inp.t_iss

        # ── NPL kg ───────────────────────────────────────────────
        npl_kg = (npl_pct / 100) * t_usd / 1_000_000

        # ── TAC (Total Adjusted Consumption) ─────────────────────
        rw1 = inp.l_dst + inp.l_win + inp.l_flr + inp.l_srt + inp.l_dt
        if (100 - inp.m_ip) == 0:
            tac = 0
        else:
            tac = round(
                (inp.t_iss * (100 - inp.m_dsp) / (100 - inp.m_ip))
                - (rw1 * (100 - inp.m_dst) / (100 - inp.m_ip)),
                2,
            )

        # ── TTC (Total Theoretical Consumption) ──────────────────
        npl_fraction = npl_pct / 100
        if (1 + npl_fraction) == 0:
            ttc = 0
        else:
            ttc = round(tac / (1 + npl_fraction), 2)

        return NPLResult(
            npl_pct=round(npl_pct, 6),
            npl_kg=round(npl_kg, 6),
            tac=tac,
            ttc=ttc,
            t_usd=round(t_usd, 3),
            actual_consumption=round(actual, 3),
            theoretical_consumption=round(theoretical, 3),
        )
