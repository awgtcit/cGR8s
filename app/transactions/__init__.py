"""
Transaction Manager – wraps SQLAlchemy session lifecycle.
Usage:
    with TransactionManager() as txn:
        txn.session.add(entity)
        # auto-commits on exit, rolls back on exception
"""
from contextlib import contextmanager
from app.database import get_session, get_scoped_session
import logging

logger = logging.getLogger(__name__)


class TransactionManager:
    """Context manager for database transactions with begin / commit / rollback."""

    def __init__(self, use_scoped=True):
        self._use_scoped = use_scoped
        self.session = None

    def __enter__(self):
        self.session = get_scoped_session() if self._use_scoped else get_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(
                'Transaction rolling back due to %s: %s', exc_type.__name__, exc_val
            )
            self.session.rollback()
        else:
            try:
                self.session.commit()
            except Exception:
                self.session.rollback()
                logger.exception('Commit failed, rolled back')
                raise
        if not self._use_scoped:
            self.session.close()
        return False  # do not suppress exceptions


@contextmanager
def transaction(use_scoped=True):
    """Functional shortcut for TransactionManager."""
    with TransactionManager(use_scoped) as txn:
        yield txn
