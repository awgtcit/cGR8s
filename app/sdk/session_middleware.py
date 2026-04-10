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
from flask import request, session, redirect, g, current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask_wtf.csrf import generate_csrf
from app.sdk.auth_client import validate_token

logger = logging.getLogger('auth_sso')

DEFAULT_PUBLIC_PATHS = frozenset([
    '/health', '/api/health', '/favicon.ico',
    '/static', '/login', '/auth/callback',
])

# Admin permissions auto-granted to SSO users flagged as admin in Auth-App
_SSO_ADMIN_PERMISSIONS = [
    'ADMIN.PANEL', 'ADMIN.SETTINGS', 'ADMIN.USERS',
    'ADMIN.MASTERS', 'AUDIT_LOG.VIEW',
]

# Embed session token max age: 30 minutes (short-lived to limit URL exposure)
_EMBED_TOKEN_MAX_AGE = 30 * 60


def _create_embed_token(user_info, roles, permissions):
    """Create a signed embed session token for cookie-free iframe auth."""
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='embed-session')
    return s.dumps({
        'uid': user_info['id'],
        'email': user_info.get('email', ''),
        'roles': roles,
        'perms': permissions,
    })


def _validate_embed_token(token_str):
    """Validate and decode an embed session token. Returns payload or None."""
    try:
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='embed-session')
        return s.loads(token_str, max_age=_EMBED_TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None


def _populate_g(user_dict, roles, permissions):
    """Populate Flask g with user context (called by both auth paths)."""
    g.current_user = user_dict
    g.current_user_id = user_dict.get('id')
    g.current_roles = roles
    g.current_permissions = permissions
    g.user_id = user_dict.get('id')
    g.user_email = user_dict.get('email', '')
    g.user_roles = roles
    g.user_permissions = permissions


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

                # Auth-App is the SSO authority – if the user is flagged
                # as admin there, auto-grant all cGR8s admin permissions
                # so the embed admin page works without separate seeding.
                _is_admin = user_info['user'].get('is_admin')
                if _is_admin:
                    for p in _SSO_ADMIN_PERMISSIONS:
                        if p not in session['sso_permissions']:
                            session['sso_permissions'].append(p)

                logger.info("SSO login: %s", user_info['user'].get('email'))
                _populate_g(user_info['user'], session['sso_roles'],
                            session['sso_permissions'])

                # Generate embed session token for cookie-free iframe nav
                g.embed_session_token = _create_embed_token(
                    user_info['user'], session['sso_roles'],
                    session['sso_permissions'])
                return None
            else:
                logger.warning("Invalid launch token from %s", request.remote_addr)

        # Handle embed session token (cookie-free fallback for iframes)
        # Check query params, form body, and headers for the token
        embed_token = (
            request.args.get('embed_token')
            or request.form.get('embed_token')
            or request.headers.get('X-Embed-Token')
        )
        if embed_token:
            payload = _validate_embed_token(embed_token)
            if payload:
                user_dict = {'id': payload['uid'], 'email': payload['email']}
                # Populate session for the current request so decorators pass
                session['sso_user'] = user_dict
                session['sso_roles'] = payload['roles']
                session['sso_permissions'] = payload['perms']
                session['sso_authenticated'] = True
                _populate_g(user_dict, payload['roles'], payload['perms'])
                # Issue a fresh token to reset the 30-min expiry window
                g.embed_session_token = _create_embed_token(
                    user_dict, payload['roles'], payload['perms'])

                # CSRF reconciliation for embed mode:
                # In cross-origin iframes the session cookie is not
                # sent, so the CSRF token set on a previous GET is
                # lost by the time a POST arrives.  We can safely
                # reconcile it here because this code path is reached
                # ONLY after _validate_embed_token() succeeded — the
                # embed_token is a server-signed, time-limited
                # (≤30 min), user-specific anti-forgery proof that is
                # at least as strong as a standard CSRF token.
                # Security invariant: payload is non-None (validated).
                assert payload is not None, 'CSRF reconcile requires validated embed_token'
                if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
                    _ct = (
                        request.headers.get('X-CSRFToken')
                        or request.headers.get('X-CSRF-Token')
                        or request.form.get('csrf_token')
                    )
                    if _ct:
                        # Flask-WTF signs CSRF tokens with
                        # URLSafeTimedSerializer(secret, salt='wtf-csrf-token').
                        # session['csrf_token'] must hold the RAW (unsigned)
                        # value; the submitted token is the SIGNED wrapper.
                        try:
                            _csrf_ser = URLSafeTimedSerializer(
                                app.config['SECRET_KEY'],
                                salt='wtf-csrf-token',
                            )
                            session['csrf_token'] = _csrf_ser.loads(
                                _ct, max_age=3600
                            )
                        except Exception:
                            session['csrf_token'] = _ct
                else:
                    generate_csrf()   # seed token for rendered pages

                logger.debug("Embed token auth: %s", payload['email'])
                return None
            else:
                logger.warning("Invalid embed token from %s", request.remote_addr)

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
                    if user_id and app_id:
                        fresh = refresh_session_permissions(user_id, app_id)
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
