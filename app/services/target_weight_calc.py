"""
Target Weight Calculator Service.
Implements the core engineering formulas for cigarette target weight calculation.
Formulas are derived from the cGR8s specification / OPT PDF.
"""
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TargetWeightInput:
    """All inputs needed for target weight calculation."""
    # Blend & key variables
    n_bld: float       # Number of blends
    p_cu: float         # Pressure CU
    t_vnt: float        # Temperature vent
    f_pd: float         # Filter PD
    m_ip: float         # Moisture IP

    # Calibration constants
    alpha: float
    beta: float
    gamma: float
    delta: float
    n_tgt: float        # Target nicotine

    # Physical parameters
    cig_length: float
    tobacco_rod_length: float
    filter_length: float
    plug_length: float
    c_plg: float


@dataclass
class TargetWeightOutput:
    """Calculated target weight results."""
    target_weight: float
    tobacco_rod_weight: float
    filter_weight: float
    total_cig_weight: float
    plug_weight: float
    tipping_length: float
    draw_resistance: float
    ventilation: float
    nicotine_delivery: float
    tar_delivery: float
    firmness: float
    moisture_content: float
    pressure_drop_open: float
    pressure_drop_closed: float


class TargetWeightCalculator:
    """
    Calculates target weight for a given set of key variables,
    calibration constants, and physical parameters.

    NOTE: The exact formulae are derived from the cGR8s-OPT.pdf specification.
    The placeholder implementations below follow the input/output contracts
    and will be refined once the PDF formulas are fully specified.
    """

    def calculate(self, inp: TargetWeightInput) -> TargetWeightOutput:
        """Run the full target weight calculation chain."""
        logger.debug('TargetWeight calc: n_bld=%.4f, p_cu=%.4f, t_vnt=%.4f, f_pd=%.4f, m_ip=%.4f',
                      inp.n_bld, inp.p_cu, inp.t_vnt, inp.f_pd, inp.m_ip)

        # Step 1: Nicotine delivery estimate
        nicotine_delivery = inp.alpha * inp.n_bld + inp.beta

        # Step 2: Tar delivery estimate
        tar_delivery = inp.gamma * nicotine_delivery + inp.delta

        # Step 3: Ventilation from temperature vent
        ventilation = inp.t_vnt

        # Step 4: Draw resistance / pressure drop
        draw_resistance = inp.f_pd
        pressure_drop_open = inp.p_cu * (1 - ventilation / 100) if ventilation < 100 else 0
        pressure_drop_closed = inp.p_cu

        # Step 5: Plug weight
        plug_weight = inp.c_plg * inp.plug_length

        # Step 6: Filter weight
        filter_weight = inp.f_pd * inp.filter_length / 10

        # Step 7: Tobacco rod weight (target)
        tobacco_rod_weight = (inp.n_tgt / inp.alpha) if inp.alpha else 0

        # Step 8: Total cigarette weight
        total_cig_weight = tobacco_rod_weight + filter_weight + plug_weight

        # Step 9: Target weight (rod only – this is the primary output)
        target_weight = tobacco_rod_weight

        # Step 10: Firmness (derived from rod weight and dimensions)
        firmness = (tobacco_rod_weight / inp.tobacco_rod_length * 1000) if inp.tobacco_rod_length else 0

        # Step 11: Moisture
        moisture_content = inp.m_ip

        # Step 12: Tipping
        tipping_length = inp.cig_length - inp.tobacco_rod_length

        return TargetWeightOutput(
            target_weight=round(target_weight, 4),
            tobacco_rod_weight=round(tobacco_rod_weight, 4),
            filter_weight=round(filter_weight, 4),
            total_cig_weight=round(total_cig_weight, 4),
            plug_weight=round(plug_weight, 4),
            tipping_length=round(tipping_length, 4),
            draw_resistance=round(draw_resistance, 4),
            ventilation=round(ventilation, 4),
            nicotine_delivery=round(nicotine_delivery, 4),
            tar_delivery=round(tar_delivery, 4),
            firmness=round(firmness, 4),
            moisture_content=round(moisture_content, 4),
            pressure_drop_open=round(pressure_drop_open, 4),
            pressure_drop_closed=round(pressure_drop_closed, 4),
        )
