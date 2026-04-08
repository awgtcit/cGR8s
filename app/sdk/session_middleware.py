"""
SSO Session Middleware — enables single-sign-on via the
Al Wahdania Auth Platform.

Usage:
    from app.sdk.session_middleware import init_sso_middleware
    init_sso_middleware(app)
"""
import logging
import time
from functools import wraps
from flask import request, session, redirect, g
from app.sdk.auth_client import validate_token

logger = logging.getLogger('auth_sso')

DEFAULT_PUBLIC_PATHS = frozenset([
    '/health', '/api/health', '/favicon.ico',
    '/static', '/login', '/auth/callback',
])


def init_sso_middleware(app, public_paths=None, login_url='/login'):
    """
    Register a before_request handler that validates SSO sessions.
    On first hit with a ?token= query param, validates the launch token
    and populates the Flask session.
    """
    public = frozenset(public_paths) if public_paths else DEFAULT_PUBLIC_PATHS

    @app.before_request
    def _sso_before_request():
        path = request.path
        if any(path.startswith(p) for p in public):
            return None

        # Handle incoming launch token
        launch_token = request.args.get('token')
        if launch_token:
            user_info = validate_token(launch_token)
            if user_info:
                session['sso_user'] = user_info['user']
                session['sso_roles'] = [r['code'] for r in user_info.get('roles', [])]
                session['sso_permissions'] = user_info.get('permissions', [])
                session['sso_token'] = launch_token
                session['sso_authenticated'] = True
                session['sso_perm_ts'] = time.time()
                session.permanent = True
                logger.info("SSO login: %s", user_info['user'].get('email'))

                g.current_user = user_info['user']
                g.current_user_id = user_info['user']['id']
                g.current_roles = session['sso_roles']
                g.current_permissions = session['sso_permissions']

                # Also populate legacy g.user_* for backward compat
                g.user_id = user_info['user']['id']
                g.user_email = user_info['user'].get('email', '')
                g.user_roles = session['sso_roles']
                g.user_permissions = session['sso_permissions']
                return None
            else:
                logger.warning("Invalid launch token from %s", request.remote_addr)

        # Check existing session
        if session.get('sso_authenticated'):
            # Optional: auto-refresh permissions if stale
            perm_ttl = app.config.get('SSO_PERMISSION_TTL', 900)  # 15 min default
            perm_ts = session.get('sso_perm_ts', 0)
            if perm_ttl and (time.time() - perm_ts) > perm_ttl:
                try:
                    from app.sdk.auth_client import refresh_session_permissions
                    user_id = session.get('sso_user', {}).get('id')
                    app_id = app.config.get('AUTH_APP_APPLICATION_ID', '')
                    token = session.get('sso_token')
                    if user_id and app_id:
                        fresh = refresh_session_permissions(user_id, app_id, token=token)
                        if fresh:
                            session['sso_permissions'] = fresh
                            session['sso_perm_ts'] = time.time()
                except Exception:
                    logger.debug("Permission TTL refresh failed, using cached permissions")

            g.current_user = session.get('sso_user', {})
            g.current_user_id = g.current_user.get('id')
            g.current_roles = session.get('sso_roles', [])
            g.current_permissions = session.get('sso_permissions', [])

            g.user_id = g.current_user_id
            g.user_email = g.current_user.get('email', '')
            g.user_roles = g.current_roles
            g.user_permissions = g.current_permissions
            return None

        # Not authenticated
        if request.is_json:
            from flask import jsonify
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        return redirect(login_url)


def require_sso_auth(f):
    """Decorator for routes that require an active SSO session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('sso_authenticated'):
            if request.is_json:
                from flask import jsonify
                return jsonify({'success': False, 'message': 'Authentication required'}), 401
            return redirect('/login')
        g.current_user = session.get('sso_user', {})
        g.current_user_id = g.current_user.get('id')
        g.current_roles = session.get('sso_roles', [])
        g.current_permissions = session.get('sso_permissions', [])

        g.user_id = g.current_user_id
        g.user_email = g.current_user.get('email', '')
        g.user_roles = g.current_roles
        g.user_permissions = g.current_permissions
        return f(*args, **kwargs)
    return decorated
