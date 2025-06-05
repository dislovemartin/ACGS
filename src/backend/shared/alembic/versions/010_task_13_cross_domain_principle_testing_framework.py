"""Task 13: Cross-Domain Principle Testing Framework

Revision ID: 010_task_13_cross_domain_testing
Revises: 009_add_secure_aggregation_privacy_models
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_task_13_cross_domain_testing'
down_revision = '009_add_secure_aggregation_privacy_models'
branch_labels = None
depends_on = None


def upgrade():
    """Create tables for cross-domain principle testing framework."""
    
    # Create domain_contexts table
    op.create_table('domain_contexts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('domain_name', sa.String(length=100), nullable=False),
        sa.Column('domain_description', sa.Text(), nullable=True),
        sa.Column('regulatory_frameworks', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('compliance_requirements', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('cultural_contexts', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('domain_constraints', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('risk_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('stakeholder_groups', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain_name')
    )
    op.create_index(op.f('ix_domain_contexts_domain_name'), 'domain_contexts', ['domain_name'], unique=False)
    op.create_index(op.f('ix_domain_contexts_id'), 'domain_contexts', ['id'], unique=False)
    op.create_index(op.f('ix_domain_contexts_is_active'), 'domain_contexts', ['is_active'], unique=False)
    op.create_index('ix_domain_context_name_active', 'domain_contexts', ['domain_name', 'is_active'], unique=False)

    # Create cross_domain_test_scenarios table
    op.create_table('cross_domain_test_scenarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scenario_name', sa.String(length=255), nullable=False),
        sa.Column('scenario_description', sa.Text(), nullable=True),
        sa.Column('primary_domain_id', sa.Integer(), nullable=False),
        sa.Column('secondary_domains', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('test_type', sa.String(length=50), nullable=False),
        sa.Column('test_parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('expected_outcomes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('principle_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('principle_adaptations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('accuracy_score', sa.Float(), nullable=True),
        sa.Column('consistency_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['primary_domain_id'], ['domain_contexts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cross_domain_test_scenarios_id'), 'cross_domain_test_scenarios', ['id'], unique=False)
    op.create_index(op.f('ix_cross_domain_test_scenarios_primary_domain_id'), 'cross_domain_test_scenarios', ['primary_domain_id'], unique=False)
    op.create_index(op.f('ix_cross_domain_test_scenarios_scenario_name'), 'cross_domain_test_scenarios', ['scenario_name'], unique=False)
    op.create_index(op.f('ix_cross_domain_test_scenarios_status'), 'cross_domain_test_scenarios', ['status'], unique=False)
    op.create_index(op.f('ix_cross_domain_test_scenarios_test_type'), 'cross_domain_test_scenarios', ['test_type'], unique=False)
    op.create_index('ix_cross_domain_scenario_domain_status', 'cross_domain_test_scenarios', ['primary_domain_id', 'status'], unique=False)

    # Create cross_domain_test_results table
    op.create_table('cross_domain_test_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scenario_id', sa.Integer(), nullable=False),
        sa.Column('test_run_id', sa.String(length=100), nullable=False),
        sa.Column('domain_id', sa.Integer(), nullable=False),
        sa.Column('principle_id', sa.Integer(), nullable=False),
        sa.Column('test_type', sa.String(length=50), nullable=False),
        sa.Column('is_consistent', sa.Boolean(), nullable=False),
        sa.Column('consistency_score', sa.Float(), nullable=False),
        sa.Column('adaptation_required', sa.Boolean(), nullable=False),
        sa.Column('adaptation_suggestions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('validation_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('conflict_detected', sa.Boolean(), nullable=False),
        sa.Column('conflict_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('memory_usage_mb', sa.Float(), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('executed_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['domain_id'], ['domain_contexts.id'], ),
        sa.ForeignKeyConstraint(['executed_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['principle_id'], ['principles.id'], ),
        sa.ForeignKeyConstraint(['scenario_id'], ['cross_domain_test_scenarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cross_domain_test_results_domain_id'), 'cross_domain_test_results', ['domain_id'], unique=False)
    op.create_index(op.f('ix_cross_domain_test_results_id'), 'cross_domain_test_results', ['id'], unique=False)
    op.create_index(op.f('ix_cross_domain_test_results_principle_id'), 'cross_domain_test_results', ['principle_id'], unique=False)
    op.create_index(op.f('ix_cross_domain_test_results_scenario_id'), 'cross_domain_test_results', ['scenario_id'], unique=False)
    op.create_index(op.f('ix_cross_domain_test_results_test_run_id'), 'cross_domain_test_results', ['test_run_id'], unique=False)
    op.create_index(op.f('ix_cross_domain_test_results_test_type'), 'cross_domain_test_results', ['test_type'], unique=False)
    op.create_index('ix_cross_domain_result_scenario_domain', 'cross_domain_test_results', ['scenario_id', 'domain_id'], unique=False)
    op.create_index('ix_cross_domain_result_principle_executed', 'cross_domain_test_results', ['principle_id', 'executed_at'], unique=False)

    # Create research_data_exports table
    op.create_table('research_data_exports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('export_name', sa.String(length=255), nullable=False),
        sa.Column('export_description', sa.Text(), nullable=True),
        sa.Column('domain_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('principle_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('date_range_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('date_range_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('anonymization_method', sa.String(length=100), nullable=False),
        sa.Column('anonymization_parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('privacy_budget_used', sa.Float(), nullable=True),
        sa.Column('export_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('statistical_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('data_hash', sa.String(length=64), nullable=False),
        sa.Column('pgp_signature', sa.Text(), nullable=True),
        sa.Column('signed_by_key_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('export_format', sa.String(length=50), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_research_data_exports_data_hash'), 'research_data_exports', ['data_hash'], unique=False)
    op.create_index(op.f('ix_research_data_exports_export_name'), 'research_data_exports', ['export_name'], unique=False)
    op.create_index(op.f('ix_research_data_exports_id'), 'research_data_exports', ['id'], unique=False)
    op.create_index('ix_research_export_created_domains', 'research_data_exports', ['created_at', 'domain_ids'], unique=False)


def downgrade():
    """Drop tables for cross-domain principle testing framework."""

    # Drop research_data_exports table first
    op.drop_index('ix_research_export_created_domains', table_name='research_data_exports')
    op.drop_index(op.f('ix_research_data_exports_id'), table_name='research_data_exports')
    op.drop_index(op.f('ix_research_data_exports_export_name'), table_name='research_data_exports')
    op.drop_index(op.f('ix_research_data_exports_data_hash'), table_name='research_data_exports')
    op.drop_table('research_data_exports')

    # Drop cross_domain_test_results table
    op.drop_index('ix_cross_domain_result_principle_executed', table_name='cross_domain_test_results')
    op.drop_index('ix_cross_domain_result_scenario_domain', table_name='cross_domain_test_results')
    op.drop_index(op.f('ix_cross_domain_test_results_test_type'), table_name='cross_domain_test_results')
    op.drop_index(op.f('ix_cross_domain_test_results_test_run_id'), table_name='cross_domain_test_results')
    op.drop_index(op.f('ix_cross_domain_test_results_scenario_id'), table_name='cross_domain_test_results')
    op.drop_index(op.f('ix_cross_domain_test_results_principle_id'), table_name='cross_domain_test_results')
    op.drop_index(op.f('ix_cross_domain_test_results_id'), table_name='cross_domain_test_results')
    op.drop_index(op.f('ix_cross_domain_test_results_domain_id'), table_name='cross_domain_test_results')
    op.drop_table('cross_domain_test_results')

    # Drop cross_domain_test_scenarios table
    op.drop_index('ix_cross_domain_scenario_domain_status', table_name='cross_domain_test_scenarios')
    op.drop_index(op.f('ix_cross_domain_test_scenarios_test_type'), table_name='cross_domain_test_scenarios')
    op.drop_index(op.f('ix_cross_domain_test_scenarios_status'), table_name='cross_domain_test_scenarios')
    op.drop_index(op.f('ix_cross_domain_test_scenarios_scenario_name'), table_name='cross_domain_test_scenarios')
    op.drop_index(op.f('ix_cross_domain_test_scenarios_primary_domain_id'), table_name='cross_domain_test_scenarios')
    op.drop_index(op.f('ix_cross_domain_test_scenarios_id'), table_name='cross_domain_test_scenarios')
    op.drop_table('cross_domain_test_scenarios')

    # Drop domain_contexts table
    op.drop_index('ix_domain_context_name_active', table_name='domain_contexts')
    op.drop_index(op.f('ix_domain_contexts_is_active'), table_name='domain_contexts')
    op.drop_index(op.f('ix_domain_contexts_id'), table_name='domain_contexts')
    op.drop_index(op.f('ix_domain_contexts_domain_name'), table_name='domain_contexts')
    op.drop_table('domain_contexts')
