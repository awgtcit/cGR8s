"""Fix constraint: drop old, create composite."""
from sqlalchemy import create_engine, text

uri = 'mssql+pyodbc://sa:Admin%40123@172.50.35.75:1433/cGR8s?driver=ODBC+Driver+17+for+SQL+Server'
engine = create_engine(uri)

with engine.connect() as conn:
    # Drop old constraint
    conn.execute(text('ALTER TABLE process_orders DROP CONSTRAINT uq_process_order_number'))
    # Create composite constraint
    conn.execute(text(
        'ALTER TABLE process_orders ADD CONSTRAINT uq_po_number_date '
        'UNIQUE (process_order_number, process_date)'
    ))
    # Check if verified column exists
    r = conn.execute(text(
        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_NAME = 'npl_results' AND COLUMN_NAME = 'verified'"
    ))
    rows = r.fetchall()
    if not rows:
        conn.execute(text(
            'ALTER TABLE npl_results ADD verified BIT NOT NULL DEFAULT 0'
        ))
        print('Added verified column to npl_results')
    else:
        print('verified column already exists')
    conn.commit()
    print('Constraints updated successfully')

    # Verify
    r2 = conn.execute(text(
        "SELECT name FROM sys.key_constraints "
        "WHERE parent_object_id = OBJECT_ID('process_orders') AND type = 'UQ'"
    ))
    for row in r2:
        print(f'  Constraint: {row[0]}')
