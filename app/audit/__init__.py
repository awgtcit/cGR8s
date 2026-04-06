"""
Audit logging service and decorator.
Logs all business actions to the audit_logs table.
"""
import json
import functools
import logging
from datetime import datetime, timezone

from flask import g, request

from app.models.audit_log import AuditLog
from app.models.base import generate_uuid
from app.database import get_scoped_session

logger = logging.getLogger(__name__)


class AuditLogger:
    """Service for writing audit log entries."""

    @staticmethod
    def log(
        action: str,
        entity_type: str = None,
        entity_id: str = None,
        description: str = None,
        before_value: dict = None,
        after_value: dict = None,
        module: str = None,
        user_id: str = None,
        user_email: str = None,
    ):
        """Write an audit log entry."""
        try:
            session = get_scoped_session()
            entry = AuditLog(
                id=generate_uuid(),
                timestamp=datetime.now(timezone.utc),
                user_id=user_id or getattr(g, 'user_id', None),
                user_email=user_email or getattr(g, 'user_email', None),
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                description=description,
                before_value=json.dumps(before_value, default=str) if before_value else None,
                after_value=json.dumps(after_value, default=str) if after_value else None,
                ip_address=request.remote_addr if request else None,
                user_agent=str(request.user_agent)[:500] if request else None,
                module=module,
            )
            session.add(entry)
            session.flush()
        except Exception:
            logger.exception('Failed to write audit log')


def audit_action(action: str, entity_type: str = None, module: str = None):
    """Decorator that logs the action after successful execution."""
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            try:
                AuditLogger.log(
                    action=action,
                    entity_type=entity_type,
                    module=module,
                    description=f'Executed {f.__name__}',
                )
            except Exception:
                logger.exception('Audit decorator failed')
            return result
        return wrapper
    return decorator
