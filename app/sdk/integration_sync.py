"""
Integration Sync Module — sends a full admin-data snapshot to the
Auth Platform's Integration Framework (carbon-copy tables).

The payload includes:
  • pages   – from ADMIN_PAGES (locally-defined modules)
  • actions – from the Permissions enum
  • groups  – roles assigned to this application in Auth-App
  • group ↔ user / page / action mappings

Uses the same _api_request helper and API-key auth as the rest of
the SDK so no extra credentials are required.
"""
import hashlib
import json
import logging
import os
from datetime import datetime, timezone

from app.sdk.auth_client import (
    _api_request,
    get_app_roles,
    get_app_users,
    get_user_roles,
    get_role_permissions,
    sync_roles_to_auth,
    sync_permissions_to_auth,
    map_role_permissions,
)

logger = logging.getLogger('integration_sync')

# ── helpers ──────────────────────────────────────────────────────────────

def _build_admin_version(payload_dict):
    """Deterministic version hash so Auth-App can detect actual changes."""
    raw = json.dumps(payload_dict, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


# ── public API ───────────────────────────────────────────────────────────

def build_full_sync_payload(app, admin_pages, permissions_enum):
    """
    Build a full-sync payload dict ready to POST.

    Parameters
    ----------
    app : Flask app (used to read config values)
    admin_pages : list[dict]  – the ADMIN_PAGES constant
    permissions_enum : Enum   – the Permissions enum class
    """
    app_id = app.config.get('AUTH_APP_APPLICATION_ID', '')
    app_code = os.environ.get('AUTH_APP_APP_CODE', 'CGRS')

    # ── 1. Pages (locally-defined modules) ─────────────────────────────
    pages = []
    for p in admin_pages:
        pages.append({
            'page_code': p['page_code'],
            'page_name': p['page_name'],
            'page_url': p.get('page_url', ''),
            'icon': p.get('icon', ''),
            'display_order': p.get('display_order', 0),
            'category': p.get('category', ''),
            'is_active': True,
        })

    # ── 2. Actions (permissions from local enum) ───────────────────────
    actions = []
    for perm in permissions_enum:
        parts = perm.value.split('.', 1)
        category = parts[0] if len(parts) > 1 else 'GENERAL'
        page_code = _CATEGORY_TO_PAGE.get(category, '')
        actions.append({
            'action_code': perm.value,
            'action_name': perm.name.replace('_', ' ').title(),
            'category': category,
            'page_code': page_code,
            'is_active': True,
        })

    # ── 3. Groups (roles from Auth-App) ────────────────────────────────
    groups = []
    role_map = {}  # role_id -> role_code
    try:
        roles = get_app_roles(app_id)
    except Exception:
        logger.warning("Could not fetch roles from Auth-App, continuing with empty groups")
        roles = []

    for r in roles:
        role_code = r.get('role_code', r.get('code', ''))
        role_id = r.get('id')
        role_map[role_id] = role_code
        groups.append({
            'group_code': role_code,
            'group_name': r.get('role_name', r.get('name', role_code)),
            'description': r.get('description', ''),
            'is_active': True,
            'users': [],  # filled below
        })

    # ── 4. User ↔ group mappings ───────────────────────────────────────
    # Build a group_code lookup set for fast matching
    group_code_set = {g['group_code'] for g in groups}
    group_by_code = {g['group_code']: g for g in groups}

    user_set = set()
    try:
        page_num = 1
        while True:
            users, meta = get_app_users(app_id, page=page_num, per_page=100)
            if users is None:
                break
            # Collect all user IDs from this batch first
            batch_uids = []
            for u in users:
                uid = str(u.get('user_id', u.get('id', '')))
                if uid and uid not in user_set:
                    user_set.add(uid)
                    batch_uids.append(uid)
                    # If the response already includes roles, use them directly
                    u_roles = u.get('roles', None)
                    if u_roles is not None:
                        for ur in u_roles:
                            rcode = ur.get('role_code', ur.get('code', ''))
                            if rcode in group_code_set:
                                group_by_code[rcode]['users'].append(uid)

            # Only call get_user_roles per-user if the list response
            # did NOT pre-hydrate roles
            sample = users[0] if users else {}
            if 'roles' not in sample:
                for uid in batch_uids:
                    try:
                        u_roles = get_user_roles(uid, application_id=app_id)
                    except Exception:
                        u_roles = []
                    for ur in u_roles:
                        rcode = ur.get('role_code', ur.get('code', ''))
                        if rcode in group_code_set:
                            group_by_code[rcode]['users'].append(uid)
            total_pages = meta.get('total_pages', 1) if meta else 1
            if page_num >= total_pages:
                break
            page_num += 1
    except Exception as exc:
        logger.warning("Could not fetch users for sync: %s", exc)

    # ── 5. Group ↔ action mappings (role→permission) ──────────────────
    group_actions = []
    for role_id, role_code in role_map.items():
        try:
            role_perms = get_role_permissions(role_id)
        except Exception:
            role_perms = []
        for rp in role_perms:
            perm_code = rp.get('code', rp.get('permission_code', ''))
            if perm_code:
                group_actions.append({
                    'group_code': role_code,
                    'action_code': perm_code,
                })

    # ── 6. Group ↔ page mappings ──────────────────────────────────────
    # For cGR8s every role that has ADMIN.PANEL can see ADMIN pages,
    # and modules are gated by permissions — derive from existing perms.
    _page_perm_prefix_map = _build_page_permission_map(admin_pages)
    group_pages = []
    for ga in group_actions:
        prefix = ga['action_code'].split('.')[0]
        matched_pages = _page_perm_prefix_map.get(prefix, [])
        for pg_code in matched_pages:
            pair = (ga['group_code'], pg_code)
            # avoid duplicates
            if not any(gp['group_code'] == pair[0] and gp['page_code'] == pair[1]
                       for gp in group_pages):
                group_pages.append({
                    'group_code': pair[0],
                    'page_code': pair[1],
                })

    # ── Assemble ──────────────────────────────────────────────────────
    inner = {
        'groups': groups,
        'pages': pages,
        'actions': actions,
        'group_pages': group_pages,
        'group_actions': group_actions,
        'user_pages': [],
        'user_actions': [],
        'overrides': [],
    }

    admin_version = _build_admin_version(inner)

    return {
        'schema_version': '1.0',
        'admin_version': admin_version,
        'sync_timestamp': _now_iso(),
        'payload': inner,
    }


def send_full_sync(app, admin_pages, permissions_enum):
    """
    Build and POST a full sync payload to Auth-App.
    Returns the response dict or None on failure.
    """
    app_code = os.environ.get('AUTH_APP_APP_CODE', 'CGRS')
    payload = build_full_sync_payload(app, admin_pages, permissions_enum)

    path = f'/api/integrations/apps/{app_code}/sync/full'

    try:
        result = _api_request('POST', path, data=payload)
        if result and result.get('success'):
            logger.info(
                "Full integration sync sent successfully — version=%s, entities=%s",
                payload['admin_version'],
                result.get('data', {}).get('entities_processed', '?'),
            )
        else:
            msg = result.get('message', 'Unknown error') if result else 'No response'
            logger.warning("Integration sync failed: %s", msg)
        return result
    except Exception as exc:
        logger.error("Integration sync request failed: %s", exc)
        return None


def register_sync_on_startup(app, admin_pages, permissions_enum):
    """
    Register a before_request handler that fires the full integration
    sync exactly once on the first incoming HTTP request.

    The sync runs in a background thread so the first request is not
    blocked by the (potentially heavy) API round-trips.
    """
    import threading

    synced = {'done': False}

    @app.before_request
    def _sync_integration_once():
        if synced['done']:
            return None
        synced['done'] = True

        def _bg():
            try:
                # 1. Sync admin navigation (CC tables)
                send_full_sync(app, admin_pages, permissions_enum)
                # 2. Sync RBAC data (roles + permissions)
                sync_rbac_to_auth(app, permissions_enum)
            except Exception as exc:
                logger.error("Integration sync startup failed: %s", exc)

        t = threading.Thread(target=_bg, daemon=True)
        t.start()
        return None


def sync_rbac_to_auth(app, permissions_enum):
    """
    Push cGR8s roles and permissions into Auth-App's RBAC tables.
    Called during startup after the navigation sync.

    Flow:
      1. Sync a default admin role
      2. Sync all permissions from the Permissions enum
      3. Fetch the role + permission IDs, then assign all permissions to admin role
    """
    app_id = app.config.get('AUTH_APP_APPLICATION_ID', '')
    if not app_id:
        logger.warning("sync_rbac_to_auth: no AUTH_APP_APPLICATION_ID configured, skipping")
        return

    # ── 1. Sync default roles ──────────────────────────────────────────
    default_roles = [
        {'code': 'CGRS_ADMIN', 'name': 'cGR8s Administrator',
         'description': 'Full access to all cGR8s modules', 'scope_type': 'APPLICATION'},
        {'code': 'CGRS_OPERATOR', 'name': 'cGR8s Operator',
         'description': 'Day-to-day operational access', 'scope_type': 'APPLICATION'},
        {'code': 'CGRS_VIEWER', 'name': 'cGR8s Viewer',
         'description': 'Read-only access to cGR8s', 'scope_type': 'APPLICATION'},
    ]

    roles_result = sync_roles_to_auth(app_id, default_roles)
    if not roles_result or not roles_result.get('success'):
        logger.error("sync_rbac_to_auth: roles sync failed, aborting")
        return

    # ── 2. Sync all permissions from enum ──────────────────────────────
    perm_list = []
    for perm in permissions_enum:
        parts = perm.value.split('.', 1)
        category = parts[0] if len(parts) > 1 else 'GENERAL'
        perm_list.append({
            'code': perm.value,
            'name': perm.name.replace('_', ' ').title(),
            'category': category,
            'description': f'{category} - {parts[1] if len(parts) > 1 else perm.value}',
        })

    perms_result = sync_permissions_to_auth(app_id, perm_list)
    if not perms_result or not perms_result.get('success'):
        logger.error("sync_rbac_to_auth: permissions sync failed")
        return

    # ── 3. Assign all permissions to the admin role ────────────────────
    # Extract permission IDs from sync response (created + updated + skipped)
    try:
        roles = get_app_roles(app_id)
        admin_role = next((r for r in roles
                           if r.get('code') == 'CGRS_ADMIN'
                           or r.get('role_code') == 'CGRS_ADMIN'), None)
        if not admin_role:
            logger.error("sync_rbac_to_auth: CGRS_ADMIN role not found after sync")
            return

        sync_data = perms_result.get('data', {})
        all_items = (sync_data.get('created', [])
                     + sync_data.get('updated', [])
                     + sync_data.get('skipped', []))
        perm_ids = [item['id'] for item in all_items if item.get('id')]

        if not perm_ids:
            logger.error("sync_rbac_to_auth: no permission IDs available from sync response")
            return

        map_result = map_role_permissions(
            admin_role.get('id'), perm_ids, application_id=app_id)
        if map_result and map_result.get('success'):
            logger.info("sync_rbac_to_auth: assigned %d permissions to CGRS_ADMIN", len(perm_ids))
        else:
            logger.error("sync_rbac_to_auth: role-permission mapping failed: %s",
                         map_result.get('message') if map_result else 'no response')
    except Exception as exc:
        logger.error("sync_rbac_to_auth: admin role permission assignment failed: %s", exc)


# ── internal helpers ─────────────────────────────────────────────────────

# Map permission category prefixes to page codes.
# Example: 'FG_CODE' permissions → 'CGRS_FG' page
_CATEGORY_TO_PAGE = {
    'DASHBOARD':    'CGRS_DASH',
    'FG_CODE':      'CGRS_FG',
    'MASTER_DATA':  'CGRS_MASTER',
    'TARGET_WEIGHT': 'CGRS_TW',
    'PROCESS_ORDER': 'CGRS_PO',
    'NPL':          'CGRS_NPL',
    'QA':           'CGRS_QA',
    'OPTIMIZER':    'CGRS_OPT',
    'BATCH':        'CGRS_BATCH',
    'REPORT':       'CGRS_RPT',
    'PRODUCT_DEV':  'CGRS_PDEV',
    'ADMIN':        'CGRS_ADMIN',
    'AUDIT_LOG':    'CGRS_AUDIT',
}


def _build_page_permission_map(admin_pages):
    """Return {permission_prefix: [page_code, ...]} for group-page derivation."""
    valid_codes = {p['page_code'] for p in admin_pages}
    result = {}
    for prefix, page_code in _CATEGORY_TO_PAGE.items():
        if page_code in valid_codes:
            result.setdefault(prefix, []).append(page_code)
    return result
