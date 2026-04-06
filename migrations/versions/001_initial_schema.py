"""
Initial schema – creates all cGR8s tables.

Revision ID: 001_initial
Revises: None
Create Date: 2026-03-26
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── system_config ─────────────────────────────────────────────────────
    op.create_table(
        'system_config',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('config_key', sa.String(100), unique=True, nullable=False),
        sa.Column('config_value', sa.Text, nullable=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('is_sensitive', sa.Boolean, default=False),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_system_config_key', 'system_config', ['config_key'])

    # ── lookups ───────────────────────────────────────────────────────────
    op.create_table(
        'lookups',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('sort_order', sa.Integer, default=0),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('parent_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_lookups_category', 'lookups', ['category'])

    # ── fg_codes ──────────────────────────────────────────────────────────
    op.create_table(
        'fg_codes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('fg_code', sa.String(50), unique=True, nullable=False),
        sa.Column('brand', sa.String(100), nullable=True),
        sa.Column('fg_gtin', sa.String(50), nullable=True),
        sa.Column('format', sa.String(50), nullable=True),
        sa.Column('tow_used', sa.String(100), nullable=True),
        sa.Column('filter_code', sa.String(50), nullable=True),
        sa.Column('blend_code', sa.String(50), nullable=True),
        sa.Column('blend', sa.String(100), nullable=True),
        sa.Column('blend_gtin', sa.String(50), nullable=True),
        sa.Column('cig_length', sa.Float, nullable=True),
        sa.Column('tobacco_rod_length', sa.Float, nullable=True),
        sa.Column('filter_length', sa.Float, nullable=True),
        sa.Column('plug_length', sa.Float, nullable=True),
        sa.Column('cig_code', sa.String(50), nullable=True),
        sa.Column('c_plg', sa.Integer, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('is_deleted', sa.Boolean, default=False, nullable=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('deleted_by', sa.String(36), nullable=True),
        sa.Column('row_version', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_fg_codes_fg_code', 'fg_codes', ['fg_code'])
    op.create_index('ix_fg_codes_blend_code', 'fg_codes', ['blend_code'])
    op.create_index('ix_fg_codes_is_deleted', 'fg_codes', ['is_deleted'])

    # ── blend_master ──────────────────────────────────────────────────────
    op.create_table(
        'blend_master',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('blend_code', sa.String(50), unique=True, nullable=False),
        sa.Column('blend_name', sa.String(100), nullable=False),
        sa.Column('blend_gtin', sa.String(50), nullable=True),
        sa.Column('n_bld', sa.Float, nullable=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('is_deleted', sa.Boolean, default=False, nullable=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('deleted_by', sa.String(36), nullable=True),
        sa.Column('row_version', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_blend_master_blend_code', 'blend_master', ['blend_code'])

    # ── physical_parameters ───────────────────────────────────────────────
    op.create_table(
        'physical_parameters',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('fg_code_id', sa.String(36), sa.ForeignKey('fg_codes.id'), nullable=False),
        sa.Column('p_cu', sa.Float, nullable=True),
        sa.Column('t_vnt', sa.Float, nullable=True),
        sa.Column('f_pd', sa.Float, nullable=True),
        sa.Column('m_ip', sa.Float, nullable=True),
        sa.Column('cig_length', sa.Float, nullable=True),
        sa.Column('tobacco_rod_length', sa.Float, nullable=True),
        sa.Column('filter_length', sa.Float, nullable=True),
        sa.Column('plug_length', sa.Float, nullable=True),
        sa.Column('c_plg', sa.Float, nullable=True),
        sa.Column('row_version', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_physical_parameters_fg_code_id', 'physical_parameters', ['fg_code_id'])

    # ── calibration_constants ─────────────────────────────────────────────
    op.create_table(
        'calibration_constants',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('fg_code_id', sa.String(36), sa.ForeignKey('fg_codes.id'), nullable=False),
        sa.Column('alpha', sa.Float, nullable=True),
        sa.Column('beta', sa.Float, nullable=True),
        sa.Column('gamma', sa.Float, nullable=True),
        sa.Column('delta', sa.Float, nullable=True),
        sa.Column('n_tgt', sa.Float, nullable=True),
        sa.Column('row_version', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_calibration_constants_fg_code_id', 'calibration_constants', ['fg_code_id'])

    # ── product_versions ──────────────────────────────────────────────────
    op.create_table(
        'product_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('fg_code_id', sa.String(36), sa.ForeignKey('fg_codes.id'), nullable=True),
        sa.Column('version_number', sa.Integer, nullable=False, default=1),
        sa.Column('status', sa.String(20), nullable=False, default='Draft'),
        sa.Column('brand', sa.String(100), nullable=True),
        sa.Column('fg_gtin', sa.String(50), nullable=True),
        sa.Column('format', sa.String(50), nullable=True),
        sa.Column('blend_code', sa.String(50), nullable=True),
        sa.Column('blend_name', sa.String(100), nullable=True),
        sa.Column('cig_length', sa.Float, nullable=True),
        sa.Column('tobacco_rod_length', sa.Float, nullable=True),
        sa.Column('filter_length', sa.Float, nullable=True),
        sa.Column('plug_length', sa.Float, nullable=True),
        sa.Column('alpha', sa.Float, nullable=True),
        sa.Column('beta', sa.Float, nullable=True),
        sa.Column('gamma', sa.Float, nullable=True),
        sa.Column('delta', sa.Float, nullable=True),
        sa.Column('n_tgt', sa.Float, nullable=True),
        sa.Column('submitted_by', sa.String(36), nullable=True),
        sa.Column('submitted_at', sa.DateTime, nullable=True),
        sa.Column('reviewed_by', sa.String(36), nullable=True),
        sa.Column('reviewed_at', sa.DateTime, nullable=True),
        sa.Column('review_notes', sa.Text, nullable=True),
        sa.Column('cloned_from_id', sa.String(36), sa.ForeignKey('product_versions.id'), nullable=True),
        sa.Column('change_summary', sa.Text, nullable=True),
        sa.Column('is_deleted', sa.Boolean, default=False, nullable=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('deleted_by', sa.String(36), nullable=True),
        sa.Column('row_version', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_product_versions_status', 'product_versions', ['status'])

    # ── process_orders ────────────────────────────────────────────────────
    op.create_table(
        'process_orders',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('fg_code_id', sa.String(36), sa.ForeignKey('fg_codes.id'), nullable=False),
        sa.Column('process_order_number', sa.String(50), nullable=False),
        sa.Column('process_date', sa.DateTime, nullable=False),
        sa.Column('status', sa.String(30), nullable=False, default='Draft'),
        sa.Column('last_run_date', sa.DateTime, nullable=True),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('is_deleted', sa.Boolean, default=False, nullable=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('deleted_by', sa.String(36), nullable=True),
        sa.Column('row_version', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_process_orders_fg_code_id', 'process_orders', ['fg_code_id'])
    op.create_index('ix_process_orders_status', 'process_orders', ['status'])
    op.create_unique_constraint('uq_process_order_number', 'process_orders', ['process_order_number'])

    # ── process_order_key_variables ───────────────────────────────────────
    op.create_table(
        'process_order_key_variables',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('process_order_id', sa.String(36), sa.ForeignKey('process_orders.id'), nullable=False),
        sa.Column('n_bld', sa.Float, nullable=True),
        sa.Column('p_cu', sa.Float, nullable=True),
        sa.Column('t_vnt', sa.Float, nullable=True),
        sa.Column('f_pd', sa.Float, nullable=True),
        sa.Column('m_ip', sa.Float, nullable=True),
        sa.Column('alpha', sa.Float, nullable=True),
        sa.Column('beta', sa.Float, nullable=True),
        sa.Column('gamma', sa.Float, nullable=True),
        sa.Column('delta', sa.Float, nullable=True),
        sa.Column('n_tgt', sa.Float, nullable=True),
        sa.Column('row_version', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_pokv_process_order_id', 'process_order_key_variables', ['process_order_id'])

    # ── target_weight_results ─────────────────────────────────────────────
    op.create_table(
        'target_weight_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('process_order_id', sa.String(36), sa.ForeignKey('process_orders.id'), nullable=False),
        sa.Column('calculated_at', sa.DateTime, nullable=False),
        sa.Column('stage1_dilution', sa.Float, nullable=True),
        sa.Column('stage2_dilution', sa.Float, nullable=True),
        sa.Column('total_dilution', sa.Float, nullable=True),
        sa.Column('filtration_pct', sa.Float, nullable=True),
        sa.Column('stage1_pacifying_nicotine_demand', sa.Float, nullable=True),
        sa.Column('stage2_pacifying_nicotine_demand', sa.Float, nullable=True),
        sa.Column('total_pacifying_nicotine_demand', sa.Float, nullable=True),
        sa.Column('total_filtration_pct', sa.Float, nullable=True),
        sa.Column('total_nicotine_demand', sa.Float, nullable=True),
        sa.Column('tw', sa.Float, nullable=True),
        sa.Column('w_dry', sa.Float, nullable=True),
        sa.Column('w_tob', sa.Float, nullable=True),
        sa.Column('w_cig', sa.Float, nullable=True),
        sa.Column('w_ntm', sa.Float, nullable=True),
        sa.Column('input_n_bld', sa.Float, nullable=True),
        sa.Column('input_p_cu', sa.Float, nullable=True),
        sa.Column('input_t_vnt', sa.Float, nullable=True),
        sa.Column('input_f_pd', sa.Float, nullable=True),
        sa.Column('input_m_ip', sa.Float, nullable=True),
        sa.Column('input_alpha', sa.Float, nullable=True),
        sa.Column('input_beta', sa.Float, nullable=True),
        sa.Column('input_gamma', sa.Float, nullable=True),
        sa.Column('input_delta', sa.Float, nullable=True),
        sa.Column('input_n_tgt', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_twr_process_order_id', 'target_weight_results', ['process_order_id'])

    # ── npl_inputs ────────────────────────────────────────────────────────
    op.create_table(
        'npl_inputs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('process_order_id', sa.String(36), sa.ForeignKey('process_orders.id'), nullable=False),
        sa.Column('t_iss', sa.Float, nullable=True),
        sa.Column('t_un', sa.Float, nullable=True),
        sa.Column('l_dst', sa.Float, nullable=True),
        sa.Column('l_win', sa.Float, nullable=True),
        sa.Column('l_flr', sa.Float, nullable=True),
        sa.Column('l_srt', sa.Float, nullable=True),
        sa.Column('l_dt', sa.Float, nullable=True),
        sa.Column('r_mkg', sa.Float, nullable=True),
        sa.Column('r_pkg', sa.Float, nullable=True),
        sa.Column('r_ndt', sa.Float, nullable=True),
        sa.Column('n_mc', sa.Float, nullable=True),
        sa.Column('n_cg', sa.Float, nullable=True),
        sa.Column('n_w', sa.Float, nullable=True),
        sa.Column('t_usd', sa.Float, nullable=True),
        sa.Column('m_dsp', sa.Float, nullable=True),
        sa.Column('m_dst', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_npl_inputs_process_order_id', 'npl_inputs', ['process_order_id'])

    # ── npl_results ───────────────────────────────────────────────────────
    op.create_table(
        'npl_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('process_order_id', sa.String(36), sa.ForeignKey('process_orders.id'), nullable=False),
        sa.Column('npl_input_id', sa.String(36), sa.ForeignKey('npl_inputs.id'), nullable=False),
        sa.Column('calculated_at', sa.DateTime, nullable=False),
        sa.Column('npl_pct', sa.Float, nullable=True),
        sa.Column('npl_kg', sa.Float, nullable=True),
        sa.Column('tac', sa.Float, nullable=True),
        sa.Column('ttc', sa.Float, nullable=True),
        sa.Column('tobacco_consumed', sa.Float, nullable=True),
        sa.Column('total_loss', sa.Float, nullable=True),
        sa.Column('total_rejects', sa.Float, nullable=True),
        sa.Column('theoretical_consumption', sa.Float, nullable=True),
        sa.Column('actual_consumption', sa.Float, nullable=True),
        sa.Column('variance', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_npl_results_process_order_id', 'npl_results', ['process_order_id'])

    # ── qa_analysis ───────────────────────────────────────────────────────
    op.create_table(
        'qa_analysis',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('process_order_id', sa.String(36), sa.ForeignKey('process_orders.id'), nullable=False),
        sa.Column('npl_result_id', sa.String(36), sa.ForeignKey('npl_results.id'), nullable=True),
        sa.Column('target_weight_result_id', sa.String(36), sa.ForeignKey('target_weight_results.id'), nullable=True),
        sa.Column('status', sa.String(30), nullable=False, default='Pending'),
        sa.Column('qa_w_cig', sa.Float, nullable=True),
        sa.Column('qa_w_tob', sa.Float, nullable=True),
        sa.Column('qa_moisture', sa.Float, nullable=True),
        sa.Column('qa_nicotine', sa.Float, nullable=True),
        sa.Column('qa_tar', sa.Float, nullable=True),
        sa.Column('qa_co', sa.Float, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('analyzed_at', sa.DateTime, nullable=True),
        sa.Column('row_version', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_qa_analysis_process_order_id', 'qa_analysis', ['process_order_id'])
    op.create_index('ix_qa_analysis_status', 'qa_analysis', ['status'])

    # ── qa_updates ────────────────────────────────────────────────────────
    op.create_table(
        'qa_updates',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('qa_analysis_id', sa.String(36), sa.ForeignKey('qa_analysis.id'), nullable=False),
        sa.Column('updated_w_cig', sa.Float, nullable=True),
        sa.Column('updated_w_tob', sa.Float, nullable=True),
        sa.Column('updated_moisture', sa.Float, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('finalized_at', sa.DateTime, nullable=True),
        sa.Column('finalized_by', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_qa_updates_qa_analysis_id', 'qa_updates', ['qa_analysis_id'])

    # ── optimizer_runs ────────────────────────────────────────────────────
    op.create_table(
        'optimizer_runs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('process_order_id', sa.String(36), sa.ForeignKey('process_orders.id'), nullable=False),
        sa.Column('method', sa.String(30), nullable=False),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_optimizer_runs_po_id', 'optimizer_runs', ['process_order_id'])

    # ── optimizer_inputs ──────────────────────────────────────────────────
    op.create_table(
        'optimizer_inputs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('optimizer_run_id', sa.String(36), sa.ForeignKey('optimizer_runs.id'), nullable=False),
        sa.Column('adjustment_value', sa.Float, nullable=True),
        sa.Column('manual_weight', sa.Float, nullable=True),
        sa.Column('direct_cig_weight', sa.Float, nullable=True),
        sa.Column('base_n_bld', sa.Float, nullable=True),
        sa.Column('base_p_cu', sa.Float, nullable=True),
        sa.Column('base_t_vnt', sa.Float, nullable=True),
        sa.Column('base_f_pd', sa.Float, nullable=True),
        sa.Column('base_m_ip', sa.Float, nullable=True),
        sa.Column('base_w_cig', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_optimizer_inputs_run_id', 'optimizer_inputs', ['optimizer_run_id'])

    # ── optimizer_results ─────────────────────────────────────────────────
    op.create_table(
        'optimizer_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('optimizer_run_id', sa.String(36), sa.ForeignKey('optimizer_runs.id'), nullable=False),
        sa.Column('opt_n_bld', sa.Float, nullable=True),
        sa.Column('opt_p_cu', sa.Float, nullable=True),
        sa.Column('opt_t_vnt', sa.Float, nullable=True),
        sa.Column('opt_f_pd', sa.Float, nullable=True),
        sa.Column('opt_m_ip', sa.Float, nullable=True),
        sa.Column('opt_n_dm', sa.Float, nullable=True),
        sa.Column('opt_w_cig', sa.Float, nullable=True),
        sa.Column('opt_w_tob', sa.Float, nullable=True),
        sa.Column('opt_w_dry', sa.Float, nullable=True),
        sa.Column('opt_stage1_dilution', sa.Float, nullable=True),
        sa.Column('opt_stage2_dilution', sa.Float, nullable=True),
        sa.Column('opt_total_dilution', sa.Float, nullable=True),
        sa.Column('opt_filtration_pct', sa.Float, nullable=True),
        sa.Column('opt_total_nicotine_demand', sa.Float, nullable=True),
        sa.Column('within_tolerance', sa.Boolean, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_optimizer_results_run_id', 'optimizer_results', ['optimizer_run_id'])

    # ── optimizer_limits ──────────────────────────────────────────────────
    op.create_table(
        'optimizer_limits',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('fg_code_id', sa.String(36), sa.ForeignKey('fg_codes.id'), nullable=True),
        sa.Column('parameter_name', sa.String(50), nullable=False),
        sa.Column('min_value', sa.Float, nullable=True),
        sa.Column('max_value', sa.Float, nullable=True),
        sa.Column('target_value', sa.Float, nullable=True),
        sa.Column('tolerance_pct', sa.Float, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('row_version', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_optimizer_limits_fg_code_id', 'optimizer_limits', ['fg_code_id'])

    # ── batch_jobs ────────────────────────────────────────────────────────
    op.create_table(
        'batch_jobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('job_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='Pending'),
        sa.Column('total_items', sa.Integer, default=0),
        sa.Column('completed_items', sa.Integer, default=0),
        sa.Column('failed_items', sa.Integer, default=0),
        sa.Column('range_start', sa.String(50), nullable=True),
        sa.Column('range_end', sa.String(50), nullable=True),
        sa.Column('parameters', sa.Text, nullable=True),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('result_file_path', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_batch_jobs_status', 'batch_jobs', ['status'])
    op.create_index('ix_batch_jobs_job_type', 'batch_jobs', ['job_type'])

    # ── batch_job_items ───────────────────────────────────────────────────
    op.create_table(
        'batch_job_items',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('batch_job_id', sa.String(36), nullable=False),
        sa.Column('record_id', sa.String(36), nullable=False),
        sa.Column('record_type', sa.String(50), nullable=True),
        sa.Column('sequence', sa.Integer, nullable=False, default=0),
        sa.Column('status', sa.String(20), nullable=False, default='Pending'),
        sa.Column('attempt_count', sa.Integer, default=0),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('processed_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_batch_job_items_batch_job_id', 'batch_job_items', ['batch_job_id'])

    # ── reports ───────────────────────────────────────────────────────────
    op.create_table(
        'reports',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('report_type', sa.String(50), nullable=False),
        sa.Column('process_order_id', sa.String(36), sa.ForeignKey('process_orders.id'), nullable=True),
        sa.Column('batch_job_id', sa.String(36), sa.ForeignKey('batch_jobs.id'), nullable=True),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_format', sa.String(10), nullable=False),
        sa.Column('file_size_bytes', sa.Integer, nullable=True),
        sa.Column('generated_at', sa.DateTime, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_reports_report_type', 'reports', ['report_type'])
    op.create_index('ix_reports_process_order_id', 'reports', ['process_order_id'])

    # ── formula_definitions ───────────────────────────────────────────────
    op.create_table(
        'formula_definitions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('formula_code', sa.String(50), unique=True, nullable=False),
        sa.Column('formula_name', sa.String(100), nullable=False),
        sa.Column('module', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('formula_expression', sa.Text, nullable=True),
        sa.Column('parameters', sa.Text, nullable=True),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('is_active', sa.String(1), default='Y', nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_formula_definitions_code', 'formula_definitions', ['formula_code'])

    # ── audit_logs ────────────────────────────────────────────────────────
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('user_email', sa.String(255), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=True),
        sa.Column('entity_id', sa.String(36), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('before_value', sa.Text, nullable=True),
        sa.Column('after_value', sa.Text, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('module', sa.String(50), nullable=True),
    )
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_entity_type', 'audit_logs', ['entity_type'])

    # ── master_data_change_log ────────────────────────────────────────────
    op.create_table(
        'master_data_change_log',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.String(36), nullable=False),
        sa.Column('field_name', sa.String(100), nullable=False),
        sa.Column('old_value', sa.Text, nullable=True),
        sa.Column('new_value', sa.Text, nullable=True),
        sa.Column('changed_by', sa.String(36), nullable=True),
        sa.Column('change_reason', sa.Text, nullable=True),
    )
    op.create_index('ix_mdcl_entity_type', 'master_data_change_log', ['entity_type'])


def downgrade() -> None:
    tables = [
        'master_data_change_log', 'audit_logs', 'formula_definitions',
        'reports', 'batch_job_items', 'batch_jobs',
        'optimizer_limits', 'optimizer_results', 'optimizer_inputs', 'optimizer_runs',
        'qa_updates', 'qa_analysis',
        'npl_results', 'npl_inputs',
        'target_weight_results', 'process_order_key_variables', 'process_orders',
        'product_versions', 'calibration_constants', 'physical_parameters',
        'blend_master', 'fg_codes', 'lookups', 'system_config',
    ]
    for t in tables:
        op.drop_table(t)
