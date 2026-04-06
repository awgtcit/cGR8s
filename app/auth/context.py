"""
Auth helpers — context utilities for accessing current user info.
Reads from SSO session populated by the SDK middleware.
"""
from flask import g, session


def get_current_user_id() -> str | None:
    return getattr(g, 'user_id', None) or (session.get('sso_user') or {}).get('id')


def get_current_user_email() -> str | None:
    return getattr(g, 'user_email', None) or (session.get('sso_user') or {}).get('email')


def get_current_user_permissions() -> list:
    return getattr(g, 'user_permissions', []) or session.get('sso_permissions', [])


def has_permission(permission_code: str) -> bool:
    return permission_code in get_current_user_permissions()
