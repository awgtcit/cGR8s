"""
Custom exception hierarchy and Flask error handlers.
"""
from flask import jsonify, render_template, request
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exception classes
# ---------------------------------------------------------------------------

class AppError(Exception):
    """Base application error."""
    status_code = 500
    error_code = 'INTERNAL_ERROR'

    def __init__(self, message: str = 'An unexpected error occurred', details=None):
        super().__init__(message)
        self.message = message
        self.details = details

    def to_dict(self):
        rv = {'error': self.error_code, 'message': self.message}
        if self.details:
            rv['details'] = self.details
        return rv


class NotFoundError(AppError):
    status_code = 404
    error_code = 'NOT_FOUND'

    def __init__(self, entity: str = 'Resource', identifier=None):
        msg = f'{entity} not found'
        if identifier:
            msg = f'{entity} "{identifier}" not found'
        super().__init__(msg)


class ValidationError(AppError):
    status_code = 422
    error_code = 'VALIDATION_ERROR'

    def __init__(self, message='Validation failed', errors=None):
        super().__init__(message, details=errors)


class BusinessRuleError(AppError):
    status_code = 409
    error_code = 'BUSINESS_RULE_VIOLATION'


class AuthenticationError(AppError):
    status_code = 401
    error_code = 'AUTHENTICATION_REQUIRED'

    def __init__(self, message='Authentication required'):
        super().__init__(message)


class AuthorizationError(AppError):
    status_code = 403
    error_code = 'FORBIDDEN'

    def __init__(self, message='Insufficient permissions'):
        super().__init__(message)


class ConcurrencyError(AppError):
    status_code = 409
    error_code = 'CONCURRENCY_CONFLICT'

    def __init__(self, message='Record was modified by another user. Please reload and retry.'):
        super().__init__(message)


class ExternalServiceError(AppError):
    status_code = 502
    error_code = 'EXTERNAL_SERVICE_ERROR'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_api_request() -> bool:
    return (
        request.path.startswith('/api/')
        or request.accept_mimetypes.best == 'application/json'
        or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    )


def _error_response(error: AppError):
    if _is_api_request():
        return jsonify(error.to_dict()), error.status_code
    try:
        return render_template(
            'errors/error.html',
            error=error,
            status_code=error.status_code,
        ), error.status_code
    except Exception:
        return jsonify(error.to_dict()), error.status_code


# ---------------------------------------------------------------------------
# Register error handlers on the Flask app
# ---------------------------------------------------------------------------

def register_error_handlers(app):
    """Attach error handlers to the Flask app."""

    @app.errorhandler(AppError)
    def handle_app_error(e):
        logger.warning('AppError: %s [%s]', e.message, e.error_code)
        return _error_response(e)

    @app.errorhandler(404)
    def handle_404(e):
        err = NotFoundError('Page')
        return _error_response(err)

    @app.errorhandler(405)
    def handle_405(e):
        err = AppError('Method not allowed')
        err.status_code = 405
        err.error_code = 'METHOD_NOT_ALLOWED'
        return _error_response(err)

    @app.errorhandler(500)
    def handle_500(e):
        logger.exception('Unhandled 500 error')
        err = AppError('An unexpected error occurred')
        return _error_response(err)
