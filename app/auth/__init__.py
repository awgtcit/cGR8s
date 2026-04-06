from app.auth.auth_client import AuthClient
from app.auth.decorators import (
    require_auth,
    require_permission,
    require_all_permissions,
    require_any_permissions,
    require_any_permission,   # deprecated alias → require_any_permissions
    require_role,
    require_any_roles,
)
from app.auth.context import get_current_user_id, get_current_user_email, get_current_user_permissions, has_permission
