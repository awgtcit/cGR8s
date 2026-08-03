"""Full logical backup of every cGR8s table to a timestamped JSON file.

Reversible safety net before a destructive purge/reload. Reads DB creds from
.env. Writes to backups/cGR8s_backup_<UTC>.json (list of {table, columns, rows}).
Run:  .venv/Scripts/python.exe scripts/backup_db.py
"""
import os
import sys
import json
import datetime
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(override=True)
from sqlalchemy import create_engine, text


def engine():
    drv = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    return create_engine(
        f"mssql+pyodbc://{urllib.parse.quote_plus(os.getenv('DB_USER'))}:"
        f"{urllib.parse.quote_plus(os.getenv('DB_PASSWORD'))}@{os.getenv('DB_SERVER')},"
        f"{os.getenv('DB_PORT', '1433')}/{os.getenv('DB_NAME')}"
        f"?driver={urllib.parse.quote_plus(drv)}",
        connect_args={"timeout": 15},
    )


def _default(o):
    if isinstance(o, (datetime.datetime, datetime.date, datetime.time)):
        return o.isoformat()
    if isinstance(o, (bytes, bytearray)):
        return o.hex()
    return str(o)


def main():
    eng = engine()
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(out_dir, f"cGR8s_backup_{stamp}.json")

    dump = {"created_utc": stamp, "tables": []}
    with eng.connect() as c:
        tables = [r[0] for r in c.execute(text(
            "SELECT name FROM sys.tables ORDER BY name"))]
        for t in tables:
            res = c.execute(text(f"SELECT * FROM [{t}]"))
            cols = list(res.keys())
            rows = [list(r) for r in res.fetchall()]
            dump["tables"].append({"table": t, "columns": cols, "rows": rows})
            print(f"  {t:30} {len(rows):>6} rows")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(dump, f, default=_default)
    size = os.path.getsize(path) / 1e6
    print(f"\nBackup written: {path}  ({size:.1f} MB, {len(dump['tables'])} tables)")


if __name__ == "__main__":
    main()
