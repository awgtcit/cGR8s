"""Integration API – receives config pushes from the Auth-App Configurator."""
import logging
import os
import re

from flask import Blueprint, request, jsonify

bp = Blueprint('integration_api', __name__)
logger = logging.getLogger(__name__)

# .env keys that correspond to pushed config values
_AUTH_URL_KEYS = ('AUTH_APP_URL', 'AUTH_BASE_URL')
_API_KEY_KEYS = ('AUTH_APP_API_KEY', 'AUTH_API_KEY')


def _env_file_path():
    """Return the absolute path to the project-root .env file."""
    # app/modules/integration_api/__init__.py → project root
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))),
        '.env',
    )


def _update_env_file(updates: dict):
    """Safely update specific key=value pairs in the .env file.

    ``updates`` maps environment-variable names to their new values.
    Lines for existing keys are replaced in-place; missing keys are
    appended under the "External Auth App Integration" section.
    """
    env_path = _env_file_path()
    if not os.path.isfile(env_path):
        raise FileNotFoundError(f'.env file not found at {env_path}')

    with open(env_path, 'r', encoding='utf-8') as fh:
        lines = fh.readlines()

    remaining = dict(updates)  # keys still to write
    new_lines = []
    for line in lines:
        stripped = line.strip()
        matched = False
        if stripped and not stripped.startswith('#') and '=' in stripped:
            key = stripped.split('=', 1)[0].strip()
            if key in remaining:
                new_lines.append(f'{key}={remaining.pop(key)}\n')
                matched = True
        if not matched:
            new_lines.append(line)

    # Append any keys that weren't found in the file
    if remaining:
        new_lines.append('\n')
        for key, val in remaining.items():
            new_lines.append(f'{key}={val}\n')

    with open(env_path, 'w', encoding='utf-8') as fh:
        fh.writelines(new_lines)


@bp.route('/receive-config', methods=['POST'])
def receive_config():
    """Accept a config push from the Auth-App Configurator.

    Auth: ``X-Application-ID`` header must match the local
    ``AUTH_APP_APPLICATION_ID`` environment variable.
    """
    # ── Authentication via shared Application ID ──────────────────────
    incoming_id = (request.headers.get('X-Application-ID') or '').strip()
    expected_id = os.environ.get('AUTH_APP_APPLICATION_ID', '')
    if not incoming_id or not expected_id:
        return jsonify({'success': False, 'message': 'Missing credentials'}), 403
    if incoming_id.lower() != expected_id.lower():
        logger.warning('receive-config: Application-ID mismatch')
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    # ── Parse payload ─────────────────────────────────────────────────
    data = request.get_json(silent=True) or {}
    auth_url = (data.get('auth_url') or '').strip()
    api_key = (data.get('api_key') or '').strip()

    if not auth_url and not api_key:
        return jsonify({'success': False, 'message': 'No config values provided'}), 400

    # Basic URL validation
    if auth_url:
        url_pattern = re.compile(r'^https?://.+', re.IGNORECASE)
        if not url_pattern.match(auth_url):
            return jsonify({'success': False, 'message': 'Invalid auth_url format'}), 400

    # ── Build updates ─────────────────────────────────────────────────
    env_updates = {}
    if auth_url:
        for k in _AUTH_URL_KEYS:
            env_updates[k] = auth_url
    if api_key:
        for k in _API_KEY_KEYS:
            env_updates[k] = api_key

    # ── Persist to .env file ──────────────────────────────────────────
    try:
        _update_env_file(env_updates)
    except Exception:
        logger.exception('receive-config: Failed to update .env file')
        return jsonify({'success': False, 'message': 'Failed to update .env file'}), 500

    # ── Update os.environ for immediate runtime effect ────────────────
    for k, v in env_updates.items():
        os.environ[k] = v

    updated = []
    if auth_url:
        updated.append('auth_url')
    if api_key:
        updated.append('api_key')
    logger.info('receive-config: Updated %s via push from Auth-App', ', '.join(updated))
    return jsonify({'success': True, 'message': 'Configuration updated', 'updated': updated})
