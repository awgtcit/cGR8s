"""
Flask Application Factory.
Creates and configures the cGR8s Flask application.
Auth-first architecture — SSO via the Al Wahdania Auth Platform.
"""
import os
import logging
from flask import Flask, g, request, session

from app.config.settings import config_by_name
from app.database import init_db, db_session, ensure_extra_tables
from app.utils.errors import register_error_handlers
from app.utils.logging_config import configure_logging
from app.utils.helpers import format_date, format_number

logger = logging.getLogger(__name__)

# ── Admin Pages for Auth Platform Sync ────────────────────────────────────
ADMIN_PAGES = [
    {'page_code': 'CGRS_DASH',       'page_name': 'Dashboard',        'page_url': '/',               'icon': 'dashboard',      'display_order': 1},
    {'page_code': 'CGRS_FG',         'page_name': 'FG Codes',         'page_url': '/fg-codes',       'icon': 'inventory_2',    'display_order': 2},
    {'page_code': 'CGRS_MASTER',     'page_name': 'Master Data',      'page_url': '/master-data',    'icon': 'dataset',        'display_order': 3},
    {'page_code': 'CGRS_TW',         'page_name': 'Target Weight',    'page_url': '/target-weight',  'icon': 'scale',          'display_order': 4},
    {'page_code': 'CGRS_PO',         'page_name': 'Process Orders',   'page_url': '/process-orders', 'icon': 'receipt_long',   'display_order': 5},
    {'page_code': 'CGRS_NPL',        'page_name': 'NPL',             'page_url': '/npl',            'icon': 'calculate',      'display_order': 6},
    {'page_code': 'CGRS_QA',         'page_name': 'QA',              'page_url': '/qa',             'icon': 'verified',       'display_order': 7},
    {'page_code': 'CGRS_OPT',        'page_name': 'Optimizer',        'page_url': '/optimizer',      'icon': 'tune',           'display_order': 8},
    {'page_code': 'CGRS_BATCH',      'page_name': 'Batch',           'page_url': '/batch',          'icon': 'pending_actions', 'display_order': 9},
    {'page_code': 'CGRS_RPT',        'page_name': 'Reports',         'page_url': '/reports',        'icon': 'assessment',     'display_order': 10},
    {'page_code': 'CGRS_PDEV',       'page_name': 'Product Dev',     'page_url': '/product-dev',    'icon': 'science',        'display_order': 11},
    {'page_code': 'CGRS_ADMIN',      'page_name': 'Admin',           'page_url': '/admin',          'icon': 'admin_panel_settings', 'display_order': 12},
    {'page_code': 'CGRS_AUDIT',      'page_name': 'Audit Log',       'page_url': '/admin/audit',    'icon': 'history',        'display_order': 13},
]


def create_app(config_name: str = None) -> Flask:
    """Application factory – returns a fully-configured Flask instance."""

    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(
        __name__,
        template_folder='../templates',
        static_folder='../static',
    )

    # ── Configuration ─────────────────────────────────────────────────
    config_cls = config_by_name.get(config_name, config_by_name['development'])
    config_obj = config_cls()
    app.config.from_object(config_obj)
    app.config['_config_obj'] = config_obj
    # Materialise the property so Flask config dict has the URI
    app.config['SQLALCHEMY_DATABASE_URI'] = config_obj.SQLALCHEMY_DATABASE_URI

    # ── Logging ───────────────────────────────────────────────────────
    configure_logging(app)

    # ── Database ──────────────────────────────────────────────────────
    init_db(app)
    ensure_extra_tables()

    # ── Error Handlers ────────────────────────────────────────────────
    register_error_handlers(app)

    # ── CSRF ──────────────────────────────────────────────────────────
    from flask_wtf.csrf import CSRFProtect
    csrf = CSRFProtect(app)

    # ── SSO Middleware (Auth-first) ───────────────────────────────────
    from app.sdk.session_middleware import init_sso_middleware
    init_sso_middleware(
        app,
        public_paths=['/health', '/api/health', '/favicon.ico', '/static', '/login', '/logout'],
        login_url='/login',
    )

    # ── Admin Page Sync ───────────────────────────────────────────────
    app_id = app.config.get('AUTH_APP_APPLICATION_ID', '')
    if app_id:
        from app.sdk.app_registry_sync import sync_pages_on_startup
        sync_pages_on_startup(app, app_id, ADMIN_PAGES)

    # ── Jinja2 Globals / Filters ──────────────────────────────────────
    def _has_perm(code):
        """Template helper — True when current session owns *code*."""
        return code in session.get('sso_permissions', [])

    app.jinja_env.globals.update(
        app_name='cGR8s',
        app_version='1.0.0',
        has_perm=_has_perm,
    )
    app.jinja_env.filters['date'] = format_date
    app.jinja_env.filters['number'] = format_number

    # ── Request Hooks ─────────────────────────────────────────────────
    @app.before_request
    def set_request_context():
        from app.database import get_scoped_session
        g.db = get_scoped_session()

    # ── Register Blueprints ───────────────────────────────────────────
    _register_blueprints(app)

    logger.info('cGR8s app created [env=%s, auth=SSO]', config_name)
    return app


def _register_blueprints(app: Flask):
    """Import and register all module blueprints."""
    from app.modules.auth import bp as auth_bp
    from app.modules.dashboard import bp as dashboard_bp
    from app.modules.admin import bp as admin_bp
    from app.modules.fg_codes import bp as fg_codes_bp
    from app.modules.master_data import bp as master_data_bp
    from app.modules.target_weight import bp as target_weight_bp
    from app.modules.process_orders import bp as process_orders_bp
    from app.modules.npl import bp as npl_bp
    from app.modules.qa import bp as qa_bp
    from app.modules.optimizer import bp as optimizer_bp
    from app.modules.batch import bp as batch_bp
    from app.modules.reports import bp as reports_bp
    from app.modules.product_dev import bp as product_dev_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(fg_codes_bp, url_prefix='/fg-codes')
    app.register_blueprint(master_data_bp, url_prefix='/master-data')
    app.register_blueprint(target_weight_bp, url_prefix='/target-weight')
    app.register_blueprint(process_orders_bp, url_prefix='/process-orders')
    app.register_blueprint(npl_bp, url_prefix='/npl')
    app.register_blueprint(qa_bp, url_prefix='/qa')
    app.register_blueprint(optimizer_bp, url_prefix='/optimizer')
    app.register_blueprint(batch_bp, url_prefix='/batch')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(product_dev_bp, url_prefix='/product-dev')
