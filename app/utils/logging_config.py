"""
Structured logging configuration.
"""
import logging
import sys
import os


def configure_logging(app=None):
    """Set up structured logging with appropriate handlers."""
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_format = os.environ.get(
        'LOG_FORMAT',
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    )
    date_format = '%Y-%m-%d %H:%M:%S'

    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level, logging.INFO))

    # Clear existing handlers to avoid duplicates on reload
    root.handlers.clear()

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(getattr(logging, log_level, logging.INFO))
    console.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    root.addHandler(console)

    # Optional file handler
    log_file = os.environ.get('LOG_FILE')
    if log_file:
        os.makedirs(os.path.dirname(log_file) or '.', exist_ok=True)
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(getattr(logging, log_level, logging.INFO))
        fh.setFormatter(logging.Formatter(log_format, datefmt=date_format))
        root.addHandler(fh)

    # Quieten noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(
        logging.INFO if log_level == 'DEBUG' else logging.WARNING
    )

    if app:
        app.logger.setLevel(getattr(logging, log_level, logging.INFO))
