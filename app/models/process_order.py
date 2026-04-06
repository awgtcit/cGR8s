"""
Process order model.
Maps to legacy: Production Data / Daily Operation sheets
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from app.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, VersionMixin, generate_uuid


class ProcessOrder(Base, AuditMixin, SoftDeleteMixin, VersionMixin):
    """A process order represents a single production run for an SKU."""
    __tablename__ = 'process_orders'
    __table_args__ = (
        UniqueConstraint('process_order_number', 'process_date', name='uq_po_number_date'),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    fg_code_id = Column(String(36), ForeignKey('fg_codes.id'), nullable=False, index=True)
    process_order_number = Column(String(50), nullable=False, index=True)
    process_date = Column(DateTime, nullable=False)
    status = Column(String(30), nullable=False, default='Draft', index=True)
    # Draft -> Calculated -> QA Pending -> QA Updated -> Completed -> Report Generated

    last_run_date = Column(DateTime, nullable=True)  # last production run date
    notes = Column(String(500), nullable=True)
