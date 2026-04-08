"""
cGR8s Configuration Module.
Loads environment-specific settings for Flask application.
"""
import os
from datetime import timedelta
from urllib.parse import quote_plus


class BaseConfig:
    """Base configuration shared across all environments."""

    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-me')

    # ── Database ──────────────────────────────────────────────────────────
    DB_AUTH_MODE = os.getenv('DB_AUTH_MODE', 'windows')
    DB_DRIVER = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
    DB_SERVER = os.getenv('DB_SERVER', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '1433')
    DB_NAME = os.getenv('DB_NAME', 'cGR8s')
    DB_USER = os.getenv('DB_USER', '')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '10'))
    DB_POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '3600'))
    DB_POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))
    DB_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '5'))

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        """Build the MSSQL connection URI for SQLAlchemy."""
        driver = self.DB_DRIVER.replace(' ', '+')
        if self.DB_AUTH_MODE == 'windows':
            return (
                f"mssql+pyodbc://@{self.DB_SERVER}:{self.DB_PORT}"
                f"/{self.DB_NAME}"
                f"?driver={driver}&Trusted_Connection=yes"
            )
        password = quote_plus(self.DB_PASSWORD)
        return (
            f"mssql+pyodbc://{self.DB_USER}:{password}"
            f"@{self.DB_SERVER}:{self.DB_PORT}/{self.DB_NAME}"
            f"?driver={driver}"
        )

    # ── Auth-App Integration ──────────────────────────────────────────────
    AUTH_APP_URL = os.getenv('AUTH_APP_URL', 'http://ams-it-126:5000')
    AUTH_APP_API_KEY = os.getenv('AUTH_APP_API_KEY', '')
    AUTH_APP_TIMEOUT = int(os.getenv('AUTH_APP_TIMEOUT', '10'))
    AUTH_APP_APPLICATION_ID = os.getenv('AUTH_APP_APPLICATION_ID', '')

    # ── Session ───────────────────────────────────────────────────────────
    SESSION_COOKIE_NAME = 'cgr8s_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # ── CSRF ──────────────────────────────────────────────────────────────
    WTF_CSRF_ENABLED = True

    # ── Reports ───────────────────────────────────────────────────────────
    REPORT_OUTPUT_DIR = os.getenv('REPORT_OUTPUT_DIR', 'reports')
    REPORT_TEMPLATE_DIR = os.getenv('REPORT_TEMPLATE_DIR', 'app/reports/templates')
    MAX_BATCH_SIZE = int(os.getenv('MAX_BATCH_SIZE', '500'))

    # ── Logging ───────────────────────────────────────────────────────────
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/cgr8s.log')

    # ── Batch Processing ──────────────────────────────────────────────────
    BATCH_WORKER_THREADS = int(os.getenv('BATCH_WORKER_THREADS', '3'))
    BATCH_CHUNK_SIZE = int(os.getenv('BATCH_CHUNK_SIZE', '50'))
    BATCH_RETRY_MAX = int(os.getenv('BATCH_RETRY_MAX', '3'))


class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class TestingConfig(BaseConfig):
    """Testing environment configuration."""
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False
    DB_NAME = os.getenv('DB_NAME', 'cGR8s_test')
    SESSION_COOKIE_SECURE = False


class ProductionConfig(BaseConfig):
    """Production environment configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Lax'


config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}
