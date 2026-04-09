"""
Purge all transactional and audit data from cGR8s database.

Keeps master data tables intact:
  fg_codes, blend_master, physical_parameters, calibration_constants,
  product_versions, lookups, machines, skus, formula_constants,
  gamma_constants, system_config, formula_definitions, optimizer_limits

Deletes (in FK-safe order):
  qa_updates, batch_job_items, optimizer_results, optimizer_inputs,
  qa_analysis, npl_results, npl_inputs, optimizer_runs,
  target_weight_results, process_order_key_variables, reports,
  batch_jobs, tobacco_blend_analysis, process_orders,
  audit_logs, master_data_change_log
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv(override=True)

from app import create_app
from app.database import get_session

# FK-safe deletion order: children first, parents last
TABLES_TO_PURGE = [
    'qa_updates',
    'batch_job_items',
    'optimizer_results',
    'optimizer_inputs',
    'qa_analysis',
    'npl_results',
    'npl_inputs',
    'optimizer_runs',
    'target_weight_results',
    'process_order_key_variables',
    'reports',
    'batch_jobs',
    'tobacco_blend_analysis',
    'process_orders',
    'audit_logs',
    'master_data_change_log',
]


def purge():
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    with app.app_context():
        session = get_session()
        try:
            total = 0
            for table in TABLES_TO_PURGE:
                result = session.execute(
                    __import__('sqlalchemy').text(f'DELETE FROM [{table}]')
                )
                count = result.rowcount
                total += count
                print(f'  Deleted {count:>6} rows from {table}')
            session.commit()
            print(f'\nDone. Total rows deleted: {total}')
        except Exception as exc:
            session.rollback()
            print(f'\nERROR: {exc}')
            raise
        finally:
            session.close()


if __name__ == '__main__':
    print('=' * 60)
    print('  cGR8s - Purge Transactional & Audit Data')
    print('=' * 60)
    print(f'\nTables to purge ({len(TABLES_TO_PURGE)}):')
    for t in TABLES_TO_PURGE:
        print(f'  - {t}')
    print()

    confirm = input('Type "DELETE" to confirm: ').strip()
    if confirm != 'DELETE':
        print('Aborted.')
        sys.exit(0)

    print('\nPurging...\n')
    purge()
