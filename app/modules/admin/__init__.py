"""Admin module – system configuration, user management, audit trail."""
import json
import logging
import os
import urllib.request
import urllib.error
from urllib.parse import urlparse

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, g
from app.auth.decorators import require_auth, require_permission
from app.config.constants import Permissions
from app.repositories import SystemConfigRepository, AuditLogRepository
from app.utils.helpers import paginate_args

bp = Blueprint('admin', __name__, template_folder='templates')
logger = logging.getLogger(__name__)

# Config keys that map to form field names
_CONFIG_KEYS = [
    'auth_app_url', 'auth_api_key',
    'default_page_size', 'batch_max_workers', 'batch_chunk_size', 'batch_max_retries',
    'company_name', 'report_footer',
]

# Keys that should update environment variables at runtime
_ENV_MAP = {
    'auth_app_url': 'AUTH_BASE_URL',
    'auth_api_key': 'AUTH_API_KEY',
}


def _validate_url(url: str) -> bool:
    """Check that the value looks like a valid HTTP(S) URL."""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
    except Exception:
        return False


@bp.route('/')
@require_auth
@require_permission(Permissions.ADMIN_PANEL)
def index():
    return render_template('admin/index.html')


@bp.route('/system-config')
@require_auth
@require_permission(Permissions.ADMIN_PANEL)
def system_config():
    repo = SystemConfigRepository(g.db)
    config_list = repo.get_all()
    configs = {cfg.config_key: cfg.config_value for cfg in config_list}
    return render_template('admin/system_config.html', configs=configs)


@bp.route('/system-config', methods=['POST'])
@require_auth
@require_permission(Permissions.ADMIN_PANEL)
def update_system_config():
    repo = SystemConfigRepository(g.db)

    for key in _CONFIG_KEYS:
        value = request.form.get(key)
        if value is None:
            continue

        value = value.strip()

        # Validate URL fields
        if key == 'auth_app_url' and value and not _validate_url(value):
            flash('Invalid Auth-App URL format. Must be http:// or https://.', 'error')
            return redirect(url_for('admin.system_config'))

        existing = repo.get_by_key(key)
        if existing:
            repo.update(existing.id, {'config_value': value})
        else:
            repo.create({'config_key': key, 'config_value': value})

        # Update runtime environment variable if applicable
        if key in _ENV_MAP and value:
            os.environ[_ENV_MAP[key]] = value

    g.db.commit()
    flash('Configuration saved successfully.', 'success')
    return redirect(url_for('admin.system_config'))


@bp.route('/test-auth-connection', methods=['POST'])
@require_auth
@require_permission(Permissions.ADMIN_PANEL)
def test_auth_connection():
    """Test connectivity and authentication against the Auth-App URL."""
    data = request.get_json(silent=True) or {}
    auth_url = (data.get('auth_url') or '').strip()
    api_key = (data.get('api_key') or '').strip()

    if not auth_url:
        return jsonify({'success': False, 'message': 'Auth URL is required.'}), 400

    if not _validate_url(auth_url):
        return jsonify({'success': False, 'message': 'Invalid URL format. Must start with http:// or https://.'}), 400

    # --- Step 1: Connectivity check (GET base URL) ---
    try:
        req = urllib.request.Request(auth_url, method='GET')
        req.add_header('User-Agent', 'cGR8s-Admin/1.0')
        with urllib.request.urlopen(req, timeout=8) as resp:
            connectivity_ok = resp.status < 500
    except urllib.error.HTTPError as e:
        # 4xx is OK for connectivity (server responded)
        connectivity_ok = e.code < 500
    except Exception as exc:
        logger.warning("Auth connection test failed for %s: %s", auth_url, exc)
        return jsonify({
            'success': False,
            'message': f'Cannot reach Auth server: {exc}',
            'connectivity': False,
        })

    if not connectivity_ok:
        return jsonify({
            'success': False,
            'message': 'Auth server returned a server error.',
            'connectivity': False,
        })

    # --- Step 2: API authentication check ---
    api_ok = False
    api_message = ''
    try:
        test_url = f"{auth_url.rstrip('/')}/api/authorize/validate-token"
        body = json.dumps({'token': '__connection_test__'}).encode('utf-8')
        req = urllib.request.Request(test_url, data=body, method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('User-Agent', 'cGR8s-Admin/1.0')
        if api_key:
            req.add_header('X-API-Key', api_key)

        with urllib.request.urlopen(req, timeout=8) as resp:
            resp_body = json.loads(resp.read().decode('utf-8'))
            # A proper auth server will respond (token invalid is fine - API is reachable)
            api_ok = True
            api_message = 'API endpoint responded successfully.'
    except urllib.error.HTTPError as e:
        # 401/403 with API key issue, 400 for invalid token — all mean the API is reachable
        if e.code in (400, 401, 403, 422):
            api_ok = True
            api_message = f'API endpoint reachable (HTTP {e.code}).'
        else:
            api_message = f'API returned HTTP {e.code}.'
    except Exception as exc:
        api_message = f'API check failed: {exc}'

    return jsonify({
        'success': api_ok,
        'message': api_message if api_ok else f'Server reachable but API check failed. {api_message}',
        'connectivity': True,
        'api_reachable': api_ok,
    })


@bp.route('/audit-trail')
@require_auth
@require_permission(Permissions.AUDIT_LOG_VIEW)
def audit_trail():
    page, per_page = paginate_args(request.args)
    repo = AuditLogRepository(g.db)
    result = repo.get_paginated(page=page, per_page=per_page, order_by='timestamp', order_dir='desc')
    from app.config.constants import AuditAction
    actions = [a.value for a in AuditAction]
    return render_template('admin/audit_trail.html',
                           logs=result.get('items', []),
                           page=result.get('page', 1),
                           total_pages=result.get('total_pages', 1),
                           actions=actions)
