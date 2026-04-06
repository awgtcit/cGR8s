"""Check unique constraints on process_orders table."""
from sqlalchemy import create_engine, text

uri = 'mssql+pyodbc://sa:Admin%40123@172.50.35.75:1433/cGR8s?driver=ODBC+Driver+17+for+SQL+Server'
engine = create_engine(uri)

with engine.connect() as conn:
    r = conn.execute(text(
        "SELECT name, type_desc FROM sys.key_constraints "
        "WHERE parent_object_id = OBJECT_ID('process_orders') AND type = 'UQ'"
    ))
    print("Unique constraints on process_orders:")
    for row in r:
        print(f"  {row}")

    # Also check index-based unique constraints
    r2 = conn.execute(text(
        "SELECT i.name, i.is_unique "
        "FROM sys.indexes i "
        "WHERE i.object_id = OBJECT_ID('process_orders') AND i.is_unique = 1"
    ))
    print("\nUnique indexes on process_orders:")
    for row in r2:
        print(f"  {row}")
