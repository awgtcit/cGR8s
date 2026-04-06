"""
Change PO unique constraint to composite (process_order_number, process_date).
Add verified column to npl_results.

Revision ID: 003_po_composite_npl_verified
Revises: 002_qa_extra_columns
Create Date: 2026-04-06
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_po_composite_npl_verified'
down_revision: Union[str, None] = '002_qa_extra_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old unique constraint on process_order_number only
    op.drop_constraint('uq_process_order_number', 'process_orders', type_='unique')
    # Add composite unique constraint on (process_order_number, process_date)
    op.create_unique_constraint(
        'uq_po_number_date', 'process_orders',
        ['process_order_number', 'process_date']
    )
    # Add verified column to npl_results
    op.add_column(
        'npl_results',
        sa.Column('verified', sa.Boolean(), nullable=False, server_default=sa.text('0'))
    )


def downgrade() -> None:
    op.drop_column('npl_results', 'verified')
    op.drop_constraint('uq_po_number_date', 'process_orders', type_='unique')
    op.create_unique_constraint(
        'uq_process_order_number', 'process_orders',
        ['process_order_number']
    )
