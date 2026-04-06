"""
NPL (Non-Product Loss) input and result models.
Maps to legacy: NPL Calculation workbook
"""
from sqlalchemy import Column, String, Float, ForeignKey, DateTime
from app.database import Base
from app.models.base import AuditMixin, generate_uuid
from datetime import datetime, timezone


class NPLInput(Base, AuditMixin):
    """Production data inputs for NPL calculation."""
    __tablename__ = 'npl_inputs'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    process_order_id = Column(
        String(36), ForeignKey('process_orders.id'), nullable=False, index=True
    )

    t_iss = Column(Float, nullable=True)   # Tobacco issued
    t_un = Column(Float, nullable=True)    # Tobacco unused
    l_dst = Column(Float, nullable=True)   # Loss - dust
    l_win = Column(Float, nullable=True)   # Loss - winnowing
    l_flr = Column(Float, nullable=True)   # Loss - floor
    l_srt = Column(Float, nullable=True)   # Loss - short
    l_dt = Column(Float, nullable=True)    # Loss - downtime
    r_mkg = Column(Float, nullable=True)   # Rejects - making
    r_pkg = Column(Float, nullable=True)   # Rejects - packing
    r_ndt = Column(Float, nullable=True)   # Rejects - non-defective tobacco
    n_mc = Column(Float, nullable=True)    # Number of MC
    n_cg = Column(Float, nullable=True)    # Number of cigarettes
    n_w = Column(Float, nullable=True)     # Net weight
    t_usd = Column(Float, nullable=True)   # Tobacco used
    m_dsp = Column(Float, nullable=True)   # Moisture - dispensed
    m_dst = Column(Float, nullable=True)   # Moisture - dust


class NPLResult(Base, AuditMixin):
    """Calculated NPL results for a process order."""
    __tablename__ = 'npl_results'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    process_order_id = Column(
        String(36), ForeignKey('process_orders.id'), nullable=False, index=True
    )
    npl_input_id = Column(
        String(36), ForeignKey('npl_inputs.id'), nullable=False
    )
    calculated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # ── Outputs ───────────────────────────────────────────────────────────
    npl_pct = Column(Float, nullable=True)     # NPL %
    npl_kg = Column(Float, nullable=True)      # NPL in KG
    tac = Column(Float, nullable=True)         # Total Actual Consumption
    ttc = Column(Float, nullable=True)         # Total Theoretical Consumption

    # ── Intermediate values ───────────────────────────────────────────────
    # Store all intermediate calculation steps for auditability
    tobacco_consumed = Column(Float, nullable=True)
    total_loss = Column(Float, nullable=True)
    total_rejects = Column(Float, nullable=True)
    theoretical_consumption = Column(Float, nullable=True)
    actual_consumption = Column(Float, nullable=True)
    variance = Column(Float, nullable=True)
