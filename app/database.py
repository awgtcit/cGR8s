"""
Database engine, session factory, and connection pooling for MSSQL via pyodbc.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base

Base = declarative_base()
_engine = None
_session_factory = None
db_session = None  # scoped session – request-bound


def init_db(app):
    """Initialize the database engine and session with the Flask app config."""
    global _engine, _session_factory, db_session

    config = app.config
    uri = config.get('SQLALCHEMY_DATABASE_URI')
    if uri is None:
        # Build from config object's property
        cfg = config.get('_config_obj')
        uri = cfg.SQLALCHEMY_DATABASE_URI if cfg else ''

    _engine = create_engine(
        uri,
        pool_size=config.get('DB_POOL_SIZE', 10),
        max_overflow=config.get('DB_MAX_OVERFLOW', 5),
        pool_recycle=config.get('DB_POOL_RECYCLE', 3600),
        pool_timeout=config.get('DB_POOL_TIMEOUT', 30),
        pool_pre_ping=True,
        echo=config.get('DEBUG', False),
        use_setinputsizes=False,
    )

    _session_factory = sessionmaker(bind=_engine)
    db_session = scoped_session(_session_factory)

    # Register teardown to remove scoped session at end of request
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        if db_session is not None:
            db_session.remove()

    return _engine


def ensure_extra_tables():
    """Create formula_constants and gamma_constants tables if they don't exist."""
    if _engine is None:
        return
    import logging
    logger = logging.getLogger(__name__)
    from app.models.formula_constant import FormulaConstant
    from app.models.gamma_constant import GammaConstant
    for model in (FormulaConstant, GammaConstant):
        try:
            model.__table__.create(_engine, checkfirst=True)
        except Exception as exc:
            logger.warning('Could not auto-create %s: %s', model.__tablename__, exc)


def get_engine():
    """Return the current SQLAlchemy engine."""
    return _engine


def get_session():
    """Return a new raw session (for use outside request context)."""
    if _session_factory is None:
        raise RuntimeError('Database not initialised. Call init_db(app) first.')
    return _session_factory()


def get_scoped_session():
    """Return the request-scoped session proxy."""
    if db_session is None:
        raise RuntimeError('Database not initialised. Call init_db(app) first.')
    return db_session
