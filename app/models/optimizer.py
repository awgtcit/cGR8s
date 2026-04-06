"""
Optimizer models: runs, inputs, results, and limits.
Maps to legacy: Product Run Optimizer workbook (cGr8s-OPT.pdf)
"""
from sqlalchemy import Column, String, Float, Text, ForeignKey, DateTime, Boolean
from app.database import Base
from app.models.base import AuditMixin, VersionMixin, generate_uuid
from datetime import datetime, timezone


class OptimizerRun(Base, AuditMixin):
    """Top-level optimizer run record."""
    __tablename__ = 'optimizer_runs'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    process_order_id = Column(
        String(36), ForeignKey('process_orders.id'), nullable=False, index=True
    )
    method = Column(String(30), nullable=False)
    # 'increment' | 'manual_adjustment' | 'direct_weight'

    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_verified = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)


class OptimizerInput(Base, AuditMixin):
    """Inputs used for an optimizer run."""
    __tablename__ = 'optimizer_inputs'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    optimizer_run_id = Column(
        String(36), ForeignKey('optimizer_runs.id'), nullable=False, index=True
    )

    # Adjustment parameters
    adjustment_value = Column(Float, nullable=True)  # e.g. -5, -1, 0, +1, +5
    manual_weight = Column(Float, nullable=True)     # manual adjustment weight entry
    direct_cig_weight = Column(Float, nullable=True) # direct new cigarette weight

    # Base values before optimization
    base_n_bld = Column(Float, nullable=True)
    base_p_cu = Column(Float, nullable=True)
    base_t_vnt = Column(Float, nullable=True)
    base_f_pd = Column(Float, nullable=True)
    base_m_ip = Column(Float, nullable=True)
    base_w_cig = Column(Float, nullable=True)


class OptimizerResult(Base, AuditMixin):
    """Optimized output values from an optimizer run."""
    __tablename__ = 'optimizer_results'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    optimizer_run_id = Column(
        String(36), ForeignKey('optimizer_runs.id'), nullable=False, index=True
    )

    # Optimized key variables
    opt_n_bld = Column(Float, nullable=True)
    opt_p_cu = Column(Float, nullable=True)
    opt_t_vnt = Column(Float, nullable=True)
    opt_f_pd = Column(Float, nullable=True)
    opt_m_ip = Column(Float, nullable=True)
    opt_n_dm = Column(Float, nullable=True)  # optimizer-specific nicotine demand

    # Recalculated outputs
    opt_w_cig = Column(Float, nullable=True)
    opt_w_tob = Column(Float, nullable=True)
    opt_w_dry = Column(Float, nullable=True)

    # Interim calculation values
    opt_stage1_dilution = Column(Float, nullable=True)
    opt_stage2_dilution = Column(Float, nullable=True)
    opt_total_dilution = Column(Float, nullable=True)
    opt_filtration_pct = Column(Float, nullable=True)
    opt_total_nicotine_demand = Column(Float, nullable=True)

    within_tolerance = Column(Boolean, nullable=True)


class OptimizerLimit(Base, AuditMixin, VersionMixin):
    """Tolerance / limit definitions for optimizer validation."""
    __tablename__ = 'optimizer_limits'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    fg_code_id = Column(
        String(36), ForeignKey('fg_codes.id'), nullable=True, index=True
    )
    # NULL fg_code_id = global default limits

    parameter_name = Column(String(50), nullable=False)
    # e.g. 'w_cig', 'w_tob', 'n_bld', 'p_cu', 't_vnt', 'f_pd'

    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    target_value = Column(Float, nullable=True)
    tolerance_pct = Column(Float, nullable=True)  # e.g. 5.0 means ±5%
    is_active = Column(Boolean, default=True, nullable=False)
