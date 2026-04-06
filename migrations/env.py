"""
Alembic environment configuration.
Reads the database URI from app config.
"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add project root to path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from app.database import Base
from app.config.settings import config_by_name
# Import all models so metadata is populated
import app.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Build DB URL from app config
flask_env = os.getenv('FLASK_ENV', 'development')
app_config = config_by_name.get(flask_env, config_by_name['development'])()
# Escape '%' for configparser interpolation
config.set_main_option('sqlalchemy.url',
                       app_config.SQLALCHEMY_DATABASE_URI.replace('%', '%%'))


def run_migrations_offline():
    """Run migrations in 'offline' mode – generates SQL script."""
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode – connects to DB."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
