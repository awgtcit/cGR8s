"""
Report tracking model.
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime
from app.database import Base
from app.models.base import AuditMixin, generate_uuid
from datetime import datetime, timezone


class Report(Base, AuditMixin):
    """Tracks generated reports for download and audit."""
    __tablename__ = 'reports'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_type = Column(String(50), nullable=False, index=True)
    # 'qa_report', 'npl_report', 'optimizer_report', 'target_weight_report', 'batch_report'

    process_order_id = Column(
        String(36), ForeignKey('process_orders.id'), nullable=True, index=True
    )
    batch_job_id = Column(
        String(36), ForeignKey('batch_jobs.id'), nullable=True
    )

    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_format = Column(String(10), nullable=False)  # 'pdf', 'xlsx'
    file_size_bytes = Column(Integer, nullable=True)

    generated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    description = Column(Text, nullable=True)


class FormulaDefinition(Base, AuditMixin):
    """Config-driven formula definitions for future adjustment.
    Stores formula metadata; actual logic is in formula adapter classes.
    """
    __tablename__ = 'formula_definitions'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    formula_code = Column(String(50), unique=True, nullable=False, index=True)
    formula_name = Column(String(100), nullable=False)
    module = Column(String(50), nullable=False)
    # 'target_weight', 'npl', 'optimizer'

    description = Column(Text, nullable=True)
    formula_expression = Column(Text, nullable=True)  # human-readable reference
    parameters = Column(Text, nullable=True)           # JSON list of parameter names
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(String(1), default='Y', nullable=False)
