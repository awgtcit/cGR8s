"""
Product Run Optimizer Service.
Supports three optimisation methods: Adjustment, Manual Entry, Direct Input.
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


@dataclass
class OptimizerConfig:
    """Tolerance limits for each key variable."""
    limits: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # e.g. {'n_bld': {'lower': 0.5, 'upper': 1.5}, ...}


@dataclass
class OptimizerInput:
    """Input for the optimizer – base values + adjustments/overrides."""
    method: str             # 'adjustment', 'manual', 'direct'
    base_values: Dict[str, float] = field(default_factory=dict)
    adjustments: Dict[str, float] = field(default_factory=dict)  # for adjustment method
    manual_values: Dict[str, float] = field(default_factory=dict)  # for manual method
    direct_values: Dict[str, float] = field(default_factory=dict)  # for direct method


@dataclass
class OptimizerOutput:
    """Optimizer results."""
    optimized_values: Dict[str, float] = field(default_factory=dict)
    within_tolerance: bool = True
    tolerance_violations: List[str] = field(default_factory=list)
    recalculated: dict = field(default_factory=dict)


class ProductRunOptimizer:
    """
    Optimizes key variables for a product run using one of three methods:
    1) Adjustment – apply delta to base values
    2) Manual – directly specify new key variable values
    3) Direct – enter target output values, back-calculate key variables
    """

    def __init__(self, config: OptimizerConfig = None):
        self.config = config or OptimizerConfig()

    def optimize(self, inp: OptimizerInput) -> OptimizerOutput:
        if inp.method == 'adjustment':
            return self._adjustment_method(inp)
        elif inp.method == 'manual':
            return self._manual_method(inp)
        elif inp.method == 'direct':
            return self._direct_method(inp)
        else:
            raise ValueError(f'Unknown optimizer method: {inp.method}')

    def _adjustment_method(self, inp: OptimizerInput) -> OptimizerOutput:
        """Apply adjustments (deltas) to base values."""
        optimized = {}
        for key, base_val in inp.base_values.items():
            adj = inp.adjustments.get(key, 0)
            optimized[key] = base_val + adj

        return self._validate_and_return(optimized)

    def _manual_method(self, inp: OptimizerInput) -> OptimizerOutput:
        """Use manually-entered key variable values."""
        optimized = dict(inp.base_values)
        optimized.update(inp.manual_values)
        return self._validate_and_return(optimized)

    def _direct_method(self, inp: OptimizerInput) -> OptimizerOutput:
        """
        Back-calculate key variables from target outputs.
        This is a placeholder – actual back-calculation depends on
        the inverse of the target weight formulas.
        """
        optimized = dict(inp.base_values)
        optimized.update(inp.direct_values)
        return self._validate_and_return(optimized)

    def _validate_and_return(self, optimized: dict) -> OptimizerOutput:
        """Check optimized values against tolerance limits."""
        within = True
        violations = []

        for param, value in optimized.items():
            if param in self.config.limits:
                lim = self.config.limits[param]
                lower = lim.get('lower')
                upper = lim.get('upper')
                if lower is not None and value < lower:
                    within = False
                    violations.append(f'{param} ({value:.4f}) below lower limit ({lower})')
                if upper is not None and value > upper:
                    within = False
                    violations.append(f'{param} ({value:.4f}) above upper limit ({upper})')

        return OptimizerOutput(
            optimized_values=optimized,
            within_tolerance=within,
            tolerance_violations=violations,
        )
