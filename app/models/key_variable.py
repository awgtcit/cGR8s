"""
Key variables stored per process order.
These are the input parameters used in target weight calculations.
"""
from sqlalchemy import Column, String, Float, ForeignKey
from app.database import Base
from app.models.base import AuditMixin, VersionMixin, generate_uuid


class ProcessOrderKeyVariable(Base, AuditMixin, VersionMixin):
    """Key input variables captured for a process order run."""
    __tablename__ = 'process_order_key_variables'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    process_order_id = Column(
        String(36), ForeignKey('process_orders.id'), nullable=False, index=True
    )

    # Key input parameters
    n_bld = Column(Float, nullable=True)   # Blend Nicotine
    p_cu = Column(Float, nullable=True)    # Cigarette Paper CU
    t_vnt = Column(Float, nullable=True)   # Tip Ventilation
    f_pd = Column(Float, nullable=True)    # Filter Pressure Drop
    m_ip = Column(Float, nullable=True)    # Input Moisture

    # Calibration constants (snapshot at time of process order)
    alpha = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    gamma = Column(Float, nullable=True)
    delta = Column(Float, nullable=True)
    n_tgt = Column(Float, nullable=True)   # Target Nicotine
