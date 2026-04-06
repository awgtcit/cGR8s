"""Clean test PO records."""
from sqlalchemy import create_engine, text

uri = 'mssql+pyodbc://sa:Admin%40123@172.50.35.75:1433/cGR8s?driver=ODBC+Driver+17+for+SQL+Server'
engine = create_engine(uri)

with engine.connect() as conn:
    r = conn.execute(text(
        "SELECT id FROM process_orders WHERE process_order_number = 'PW-TEST-001'"
    ))
    rows = r.fetchall()
    for row in rows:
        pid = row[0]
        conn.execute(text('DELETE FROM npl_results WHERE process_order_id = :id'), {'id': pid})
        conn.execute(text('DELETE FROM npl_inputs WHERE process_order_id = :id'), {'id': pid})
        conn.execute(text('DELETE FROM process_order_key_variables WHERE process_order_id = :id'), {'id': pid})
        conn.execute(text('DELETE FROM target_weight_results WHERE process_order_id = :id'), {'id': pid})
        conn.execute(text('DELETE FROM process_orders WHERE id = :id'), {'id': pid})
    conn.commit()
    print(f'Cleaned up {len(rows)} test PO records')
