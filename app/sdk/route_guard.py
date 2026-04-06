"""
Route Guard — SSO authorization decorators (single source of truth).

This module is the canonical implementation for all permission and role
checks across applications using the Al Wahdania Auth Platform SDK.

Decorator semantics:
    require_permission(code)          – exactly ONE permission required
    require_all_permissions(*codes)   – ALL listed permissions required
    require_any_permissions(*codes)   – at least ONE of the listed
    require_role(role)                – exactly ONE role required
    require_any_roles(*roles)         – at least ONE of the listed roles

Usage:
    from app.sdk.route_guard import require_permission, require_all_permissions

    @app.route('/admin')
    @require_permission('ADMIN.PANEL')
    def admin_panel(): ...
"""
from functools import wraps
from flask import session, request, redirect, jsonify


# ── Helpers ───────────────────────────────────────────────────────────────

def _check_auth():
    """Return a 401 response if not SSO-authenticated, else None."""
    if not session.get('sso_authenticated'):
        if request.is_json:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        return redirect('/login')
    return None


def _deny(message='Forbidden'):
    if request.is_json:
        return jsonify({'success': False, 'message': message}), 403
    return message, 403


# ── Permission Decorators ─────────────────────────────────────────────────

def require_permission(permission):
    """Require exactly ONE permission code (e.g. ``'ADMIN.PANEL'``)."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            denied = _check_auth()
            if denied:
                return denied
            perms = session.get('sso_permissions', [])
            if permission not in perms:
                return _deny(f'Missing permission: {permission}')
            return f(*args, **kwargs)
        return decorated
    return decorator


def require_all_permissions(*permission_codes):
    """Require ALL of the listed permission codes."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            denied = _check_auth()
            if denied:
                return denied
            user_perms = set(session.get('sso_permissions', []))
            required = set(permission_codes)
            if not required.issubset(user_perms):
                missing = required - user_perms
                return _deny(f'Missing permissions: {", ".join(sorted(missing))}')
            return f(*args, **kwargs)
        return decorated
    return decorator


def require_any_permissions(*permission_codes):
    """Require at least ONE of the listed permission codes."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            denied = _check_auth()
            if denied:
                return denied
            user_perms = set(session.get('sso_permissions', []))
            required = set(permission_codes)
            if not required.intersection(user_perms):
                return _deny('Insufficient permissions')
            return f(*args, **kwargs)
        return decorated
    return decorator


# ── Role Decorators ───────────────────────────────────────────────────────

def require_role(role):
    """Require exactly ONE role code (e.g. ``'CGRS_SYS_ADMIN'``)."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            denied = _check_auth()
            if denied:
                return denied
            roles = session.get('sso_roles', [])
            if role not in roles:
                return _deny(f'Missing role: {role}')
            return f(*args, **kwargs)
        return decorated
    return decorator


def require_any_roles(*role_codes):
    """Require at least ONE of the listed role codes."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            denied = _check_auth()
            if denied:
                return denied
            user_roles = set(session.get('sso_roles', []))
            required = set(role_codes)
            if not required.intersection(user_roles):
                return _deny('Insufficient roles')
            return f(*args, **kwargs)
        return decorated
    return decorator
