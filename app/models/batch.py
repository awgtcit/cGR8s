"""
Batch job and batch job item models.
"""
from sqlalchemy import Column, String, Integer, Text, DateTime
from app.database import Base
from app.models.base import AuditMixin, generate_uuid
from datetime import datetime, timezone


class BatchJob(Base, AuditMixin):
    """Top-level batch job record."""
    __tablename__ = 'batch_jobs'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_type = Column(String(50), nullable=False, index=True)
    # 'qa_report', 'npl_calculation', 'optimizer'

    status = Column(String(20), nullable=False, default='Pending', index=True)
    # Pending -> Running -> Completed -> Failed

    total_items = Column(Integer, default=0)
    completed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)

    range_start = Column(String(50), nullable=True)  # start record ID or number
    range_end = Column(String(50), nullable=True)    # end record ID or number
    parameters = Column(Text, nullable=True)          # JSON extra params

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    result_file_path = Column(String(500), nullable=True)


class BatchJobItem(Base, AuditMixin):
    """Individual item within a batch job."""
    __tablename__ = 'batch_job_items'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    batch_job_id = Column(String(36), nullable=False, index=True)
    # Not using FK to avoid circular - batch_jobs may not exist yet at migration time

    record_id = Column(String(36), nullable=False)     # the target record ID
    record_type = Column(String(50), nullable=True)     # entity type
    sequence = Column(Integer, nullable=False, default=0)

    status = Column(String(20), nullable=False, default='Pending')
    # Pending -> Running -> Completed -> Failed -> Skipped

    attempt_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
