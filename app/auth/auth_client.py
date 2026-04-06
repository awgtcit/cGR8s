"""
Auth-App HTTP client — thin wrapper around the SDK auth_client.

DEPRECATED: This module exists solely for backward compatibility.
New code should import directly from ``app.sdk.auth_client`` instead
of using the ``AuthClient`` class.  This wrapper will be removed in
a future release once all call-sites are migrated.
"""
import logging
import os
import requests
from flask import current_app

from app.sdk.auth_client import validate_token as sdk_validate_token

logger = logging.getLogger(__name__)


def _base_url() -> str:
    """Resolve Auth-App base URL from config / env."""
    try:
        return current_app.config.get('AUTH_APP_URL', os.getenv('AUTH_APP_URL', 'http://ams-it-126:5000'))
    except RuntimeError:
        return os.getenv('AUTH_APP_URL', 'http://ams-it-126:5000')


def _api_key() -> str:
    try:
        return current_app.config.get('AUTH_APP_API_KEY', os.getenv('AUTH_APP_API_KEY', ''))
    except RuntimeError:
        return os.getenv('AUTH_APP_API_KEY', '')


def _timeout() -> int:
    try:
        return int(current_app.config.get('AUTH_APP_TIMEOUT', 10))
    except RuntimeError:
        return int(os.getenv('AUTH_APP_TIMEOUT', '10'))


class AuthClient:
    """Backward-compatible wrapper — most auth logic now lives in the SDK middleware."""

    def __init__(self, base_url=None, api_key=None, timeout=10):
        self.base_url = base_url or _base_url()
        self.api_key = api_key or _api_key()
        self.timeout = timeout or _timeout()

    @classmethod
    def from_config(cls):
        return cls(base_url=_base_url(), api_key=_api_key(), timeout=_timeout())

    # ── Token validation (delegates to SDK) ──────────────────────────
    def validate_token(self, token: str) -> dict | None:
        return sdk_validate_token(token)

    # ── User info lookup ─────────────────────────────────────────────
    def get_user_info(self, user_id: str) -> dict | None:
        try:
            resp = requests.get(
                f'{self.base_url}/api/users/{user_id}',
                headers={'X-API-Key': self.api_key},
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get('data', data)
            return None
        except requests.RequestException as e:
            logger.error('Failed to fetch user info: %s', e)
            return None
