"""
Target weight calculation results model.
Maps to legacy: Forward Target Calculation worksheet outputs
"""
from sqlalchemy import Column, String, Float, ForeignKey, DateTime
from app.database import Base
from app.models.base import AuditMixin, generate_uuid
from datetime import datetime, timezone


class TargetWeightResult(Base, AuditMixin):
    """Stores the computed outputs of a target weight calculation."""
    __tablename__ = 'target_weight_results'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    process_order_id = Column(
        String(36), ForeignKey('process_orders.id'), nullable=False, index=True
    )
    calculated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # ── Derived outputs ───────────────────────────────────────────────────
    stage1_dilution = Column(Float, nullable=True)
    stage2_dilution = Column(Float, nullable=True)
    total_dilution = Column(Float, nullable=True)
    filtration_pct = Column(Float, nullable=True)

    stage1_pacifying_nicotine_demand = Column(Float, nullable=True)
    stage2_pacifying_nicotine_demand = Column(Float, nullable=True)
    total_pacifying_nicotine_demand = Column(Float, nullable=True)

    total_filtration_pct = Column(Float, nullable=True)
    total_nicotine_demand = Column(Float, nullable=True)

    tw = Column(Float, nullable=True)        # Tobacco weight with moisture
    w_dry = Column(Float, nullable=True)     # Dry weight
    w_tob = Column(Float, nullable=True)     # Tobacco weight
    w_cig = Column(Float, nullable=True)     # Cigarette weight
    w_ntm = Column(Float, nullable=True)     # NTM weight

    # ── Snapshot of inputs used ───────────────────────────────────────────
    input_n_bld = Column(Float, nullable=True)
    input_p_cu = Column(Float, nullable=True)
    input_t_vnt = Column(Float, nullable=True)
    input_f_pd = Column(Float, nullable=True)
    input_m_ip = Column(Float, nullable=True)
    input_alpha = Column(Float, nullable=True)
    input_beta = Column(Float, nullable=True)
    input_gamma = Column(Float, nullable=True)
    input_delta = Column(Float, nullable=True)
    input_n_tgt = Column(Float, nullable=True)
