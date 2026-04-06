"""
Authentication and authorization decorators — BACKWARD-COMPATIBILITY WRAPPER.

DEPRECATED: Authorization logic has been consolidated into
``app.sdk.route_guard``.  This module re-exports the SDK decorators
under the same names so existing ``from app.auth.decorators import …``
statements keep working.  New code should import directly from the SDK.

This file will be removed in a future release once all call-sites are
migrated.
"""
import functools
import logging
from flask import request, g, redirect, url_for, flash, jsonify, session

# ── SDK (single source of truth) ──────────────────────────────────────────
from app.sdk.route_guard import (              # noqa: F401  – re-exports
    require_permission,
    require_all_permissions,
    require_any_permissions,
    require_role,
    require_any_roles,
)

logger = logging.getLogger(__name__)


# ── App-specific helpers (not in the portable SDK) ────────────────────────

def _ensure_g_context():
    """Populate g.user_* from SSO session (safety net)."""
    if not getattr(g, 'user_id', None):
        user = session.get('sso_user', {})
        g.user_id = user.get('id')
        g.user_email = user.get('email', '')
        g.user_roles = session.get('sso_roles', [])
        g.user_permissions = session.get('sso_permissions', [])


def _is_api_request():
    return (
        request.path.startswith('/api/')
        or request.headers.get('Accept', '').startswith('application/json')
        or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    )


def require_auth(f):
    """Decorator: require an active SSO session and populate ``g.user_*``.

    This is app-specific and NOT part of the portable SDK because it
    references the ``auth.login`` blueprint and populates Flask ``g``
    context used by cGR8s modules.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('sso_authenticated'):
            if _is_api_request():
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login', next=request.url))
        _ensure_g_context()
        return f(*args, **kwargs)
    return decorated


# ── Backward-compatibility alias ──────────────────────────────────────────
# Old code: ``from app.auth.decorators import require_any_permission``
# New name: ``require_any_permissions`` (plural, matches SDK)
require_any_permission = require_any_permissions
