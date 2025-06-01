"""Add MAB optimization tables

Revision ID: 006_add_mab_optimization_tables
Revises: 005_fix_refresh_token_length
Create Date: 2024-12-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_add_mab_optimization_tables'
down_revision = '005_fix_refresh_token_length'
branch_labels = None
depends_on = None


def upgrade():
    """Add Multi-Armed Bandit optimization tables."""
    
    # Create prompt_templates table
    op.create_table(
        'prompt_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('template_content', sa.Text(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('version', sa.String(50), nullable=True, default='1.0'),
        sa.Column('metadata_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('total_uses', sa.Integer(), nullable=True, default=0),
        sa.Column('total_rewards', sa.Float(), nullable=True, default=0.0),
        sa.Column('success_count', sa.Integer(), nullable=True, default=0),
        sa.Column('average_reward', sa.Float(), nullable=True, default=0.0),
        sa.Column('confidence_lower', sa.Float(), nullable=True, default=0.0),
        sa.Column('confidence_upper', sa.Float(), nullable=True, default=1.0),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_prompt_templates_id', 'prompt_templates', ['id'])
    op.create_index('ix_prompt_templates_template_id', 'prompt_templates', ['template_id'], unique=True)
    op.create_index('ix_prompt_templates_category', 'prompt_templates', ['category'])
    
    # Create prompt_performance table
    op.create_table(
        'prompt_performance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.String(255), nullable=False),
        sa.Column('semantic_similarity', sa.Float(), nullable=False),
        sa.Column('policy_quality', sa.Float(), nullable=False),
        sa.Column('constitutional_compliance', sa.Float(), nullable=False),
        sa.Column('bias_mitigation', sa.Float(), nullable=False),
        sa.Column('composite_score', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('context_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('llm_response_length', sa.Integer(), nullable=True),
        sa.Column('llm_response_hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['template_id'], ['prompt_templates.template_id'])
    )
    op.create_index('ix_prompt_performance_id', 'prompt_performance', ['id'])
    op.create_index('ix_prompt_performance_template_id', 'prompt_performance', ['template_id'])
    op.create_index('ix_prompt_performance_category', 'prompt_performance', ['category'])
    
    # Create optimization_history table
    op.create_table(
        'optimization_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.String(255), nullable=False),
        sa.Column('algorithm_type', sa.String(50), nullable=False),
        sa.Column('selection_reason', sa.String(255), nullable=True),
        sa.Column('composite_score', sa.Float(), nullable=False),
        sa.Column('reward_components', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('total_uses_at_selection', sa.Integer(), nullable=False),
        sa.Column('average_reward_at_selection', sa.Float(), nullable=False),
        sa.Column('context_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['template_id'], ['prompt_templates.template_id'])
    )
    op.create_index('ix_optimization_history_id', 'optimization_history', ['id'])
    op.create_index('ix_optimization_history_template_id', 'optimization_history', ['template_id'])
    op.create_index('ix_optimization_history_category', 'optimization_history', ['category'])
    op.create_index('ix_optimization_history_timestamp', 'optimization_history', ['timestamp'])
    
    # Create mab_configurations table
    op.create_table(
        'mab_configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('config_name', sa.String(255), nullable=False),
        sa.Column('algorithm_type', sa.String(50), nullable=False),
        sa.Column('exploration_rate', sa.Float(), nullable=True, default=0.1),
        sa.Column('confidence_level', sa.Float(), nullable=True, default=0.95),
        sa.Column('alpha_prior', sa.Float(), nullable=True, default=1.0),
        sa.Column('beta_prior', sa.Float(), nullable=True, default=1.0),
        sa.Column('semantic_similarity_weight', sa.Float(), nullable=True, default=0.4),
        sa.Column('policy_quality_weight', sa.Float(), nullable=True, default=0.3),
        sa.Column('constitutional_compliance_weight', sa.Float(), nullable=True, default=0.2),
        sa.Column('bias_mitigation_weight', sa.Float(), nullable=True, default=0.1),
        sa.Column('min_uses_for_confidence', sa.Integer(), nullable=True, default=10),
        sa.Column('reward_threshold', sa.Float(), nullable=True, default=0.8),
        sa.Column('update_frequency', sa.Integer(), nullable=True, default=100),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('additional_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_mab_configurations_id', 'mab_configurations', ['id'])
    op.create_index('ix_mab_configurations_config_name', 'mab_configurations', ['config_name'], unique=True)
    
    # Create mab_sessions table
    op.create_table(
        'mab_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('config_name', sa.String(255), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_selections', sa.Integer(), nullable=True, default=0),
        sa.Column('total_rewards', sa.Float(), nullable=True, default=0.0),
        sa.Column('average_reward', sa.Float(), nullable=True, default=0.0),
        sa.Column('best_template_id', sa.String(255), nullable=True),
        sa.Column('best_template_reward', sa.Float(), nullable=True, default=0.0),
        sa.Column('exploration_rate_actual', sa.Float(), nullable=True),
        sa.Column('convergence_achieved', sa.Boolean(), nullable=True, default=False),
        sa.Column('convergence_iteration', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('status', sa.String(50), nullable=True, default='running'),
        sa.Column('session_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['config_name'], ['mab_configurations.config_name'])
    )
    op.create_index('ix_mab_sessions_id', 'mab_sessions', ['id'])
    op.create_index('ix_mab_sessions_session_id', 'mab_sessions', ['session_id'], unique=True)
    
    # Create prompt_template_versions table
    op.create_table(
        'prompt_template_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.String(255), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('template_content', sa.Text(), nullable=False),
        sa.Column('change_description', sa.Text(), nullable=True),
        sa.Column('parent_version', sa.String(50), nullable=True),
        sa.Column('performance_improvement', sa.Float(), nullable=True),
        sa.Column('a_b_test_results', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=True, default=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_prompt_template_versions_id', 'prompt_template_versions', ['id'])
    op.create_index('ix_prompt_template_versions_template_id', 'prompt_template_versions', ['template_id'])
    
    # Create reward_functions table
    op.create_table(
        'reward_functions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('function_name', sa.String(255), nullable=False),
        sa.Column('function_code', sa.Text(), nullable=False),
        sa.Column('function_type', sa.String(50), nullable=True, default='composite'),
        sa.Column('weight_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('threshold_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_validated', sa.Boolean(), nullable=True, default=False),
        sa.Column('validation_results', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_reward_functions_id', 'reward_functions', ['id'])
    op.create_index('ix_reward_functions_function_name', 'reward_functions', ['function_name'], unique=True)


def downgrade():
    """Remove MAB optimization tables."""
    
    # Drop tables in reverse order to handle foreign key constraints
    op.drop_table('reward_functions')
    op.drop_table('prompt_template_versions')
    op.drop_table('mab_sessions')
    op.drop_table('mab_configurations')
    op.drop_table('optimization_history')
    op.drop_table('prompt_performance')
    op.drop_table('prompt_templates')
