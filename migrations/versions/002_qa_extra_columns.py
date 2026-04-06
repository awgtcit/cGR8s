"""
Add missing QA measurement columns: tobacco_weight, filter_weight, cig_wt.

Revision ID: 002_qa_extra_columns
Revises: 001_initial
Create Date: 2026-04-06
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_qa_extra_columns'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('qa_analysis', sa.Column('tobacco_weight_mean', sa.Float, nullable=True))
    op.add_column('qa_analysis', sa.Column('tobacco_weight_sd', sa.Float, nullable=True))
    op.add_column('qa_analysis', sa.Column('filter_weight', sa.Float, nullable=True))
    op.add_column('qa_analysis', sa.Column('cig_wt_mean', sa.Float, nullable=True))
    op.add_column('qa_analysis', sa.Column('cig_wt_sd', sa.Float, nullable=True))


def downgrade() -> None:
    op.drop_column('qa_analysis', 'cig_wt_sd')
    op.drop_column('qa_analysis', 'cig_wt_mean')
    op.drop_column('qa_analysis', 'filter_weight')
    op.drop_column('qa_analysis', 'tobacco_weight_sd')
    op.drop_column('qa_analysis', 'tobacco_weight_mean')
