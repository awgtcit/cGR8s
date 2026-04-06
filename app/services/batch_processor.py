"""
Batch Processing Service.
DB-queue based batch processor using threading.
"""
import logging
import threading
import time
from datetime import datetime
from typing import Callable, Optional

from app.config.constants import BatchJobStatus, BatchJobItemStatus
from app.database import get_session

logger = logging.getLogger(__name__)

_workers = {}


class BatchProcessor:
    """Manages batch job execution using background threads and a DB queue."""

    def __init__(self, max_workers: int = 3, chunk_size: int = 50, max_retries: int = 3):
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.max_retries = max_retries

    def submit_job(self, job_id: str, processor_fn: Callable):
        """Start processing a batch job in a background thread."""
        if len(_workers) >= self.max_workers:
            raise RuntimeError('Maximum concurrent batch workers reached')

        thread = threading.Thread(
            target=self._run_job,
            args=(job_id, processor_fn),
            daemon=True,
            name=f'batch-{job_id}',
        )
        _workers[job_id] = thread
        thread.start()
        logger.info('Batch job %s submitted', job_id)

    def _run_job(self, job_id: str, processor_fn: Callable):
        """Process all items in the batch job."""
        session = get_session()
        try:
            from app.models.batch import BatchJob, BatchJobItem
            job = session.query(BatchJob).get(job_id)
            if not job:
                logger.error('Batch job %s not found', job_id)
                return

            job.status = BatchJobStatus.PROCESSING.value
            job.started_at = datetime.utcnow()
            session.commit()

            items = (
                session.query(BatchJobItem)
                .filter_by(batch_job_id=job_id, status=BatchJobItemStatus.PENDING.value)
                .order_by(BatchJobItem.created_at)
                .all()
            )

            total = len(items)
            processed = 0
            failed = 0

            for item in items:
                try:
                    item.status = BatchJobItemStatus.PROCESSING.value
                    item.started_at = datetime.utcnow()
                    session.commit()

                    processor_fn(item, session)

                    item.status = BatchJobItemStatus.COMPLETED.value
                    item.completed_at = datetime.utcnow()
                    processed += 1
                except Exception as e:
                    logger.exception('Batch item %s failed: %s', item.id, e)
                    item.retry_count = (item.retry_count or 0) + 1
                    item.error_message = str(e)[:500]
                    if item.retry_count >= self.max_retries:
                        item.status = BatchJobItemStatus.FAILED.value
                        failed += 1
                    else:
                        item.status = BatchJobItemStatus.PENDING.value
                finally:
                    job.processed_count = processed
                    job.failed_count = failed
                    job.total_count = total
                    session.commit()

            job.status = (
                BatchJobStatus.COMPLETED.value if failed == 0
                else BatchJobStatus.COMPLETED_WITH_ERRORS.value
            )
            job.completed_at = datetime.utcnow()
            session.commit()
            logger.info('Batch job %s completed: %d/%d processed, %d failed',
                        job_id, processed, total, failed)
        except Exception as e:
            logger.exception('Batch job %s error: %s', job_id, e)
            try:
                job = session.query(BatchJob).get(job_id)
                if job:
                    job.status = BatchJobStatus.FAILED.value
                    job.error_message = str(e)[:500]
                    session.commit()
            except Exception:
                session.rollback()
        finally:
            session.close()
            _workers.pop(job_id, None)

    @staticmethod
    def get_active_jobs():
        return list(_workers.keys())
