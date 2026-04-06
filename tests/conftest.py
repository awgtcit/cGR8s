import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def app():
    """Create test application."""
    os.environ.setdefault('FLASK_ENV', 'testing')
    os.environ.setdefault('SECRET_KEY', 'test-secret-key')
    os.environ.setdefault('DB_SERVER', 'localhost')
    os.environ.setdefault('DB_NAME', 'cGR8s_test')
    os.environ.setdefault('DB_AUTH_MODE', 'sql')
    os.environ.setdefault('DB_USER', 'sa')
    os.environ.setdefault('DB_PASSWORD', 'test')
    os.environ.setdefault('AUTH_APP_URL', 'http://localhost:5000')
    os.environ.setdefault('AUTH_API_KEY', 'test-key')

    from app import create_app
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create CLI test runner."""
    return app.test_cli_runner()
