"""Create the cGR8s database and all tables on the SQL Server."""
import pyodbc
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

SERVER = '172.50.35.75'
USER = 'sa'
PASSWORD = 'Admin@123'
DRIVER = 'ODBC Driver 17 for SQL Server'
DB_NAME = 'cGR8s'

# Step 1: Create the database
print(f"Connecting to {SERVER}...")
conn = pyodbc.connect(
    f"DRIVER={{{DRIVER}}};SERVER={SERVER};DATABASE=master;UID={USER};PWD={PASSWORD};",
    autocommit=True
)
cursor = conn.cursor()

# Check if DB exists
cursor.execute("SELECT name FROM sys.databases WHERE name = ?", (DB_NAME,))
if cursor.fetchone():
    print(f"Database '{DB_NAME}' already exists.")
else:
    cursor.execute(f"CREATE DATABASE [{DB_NAME}]")
    print(f"Database '{DB_NAME}' created successfully!")

conn.close()

# Step 2: Create all tables using SQLAlchemy models
print("\nCreating tables from SQLAlchemy models...")
os.environ['DB_SERVER'] = SERVER
os.environ['DB_USER'] = USER
os.environ['DB_PASSWORD'] = PASSWORD
os.environ['DB_NAME'] = DB_NAME
os.environ['DB_AUTH_MODE'] = 'sql'
os.environ['DB_DRIVER'] = DRIVER

from app.database import Base
from app.models import *  # noqa: F401,F403 – import all models so Base.metadata sees them
from sqlalchemy import create_engine
from urllib.parse import quote_plus

conn_str = f"DRIVER={{{DRIVER}}};SERVER={SERVER};DATABASE={DB_NAME};UID={USER};PWD={PASSWORD}"
uri = f"mssql+pyodbc:///?odbc_connect={quote_plus(conn_str)}"

engine = create_engine(uri)
Base.metadata.create_all(engine)

# List created tables
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"\n=== Tables created ({len(tables)}) ===")
for t in sorted(tables):
    print(f"  {t}")

engine.dispose()
print("\nDone! Database is ready.")
