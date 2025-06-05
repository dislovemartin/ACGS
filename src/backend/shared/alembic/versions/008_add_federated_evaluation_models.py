"""Add federated evaluation models

Revision ID: 008_add_federated_evaluation_models
Revises: 007_phase3_z3_integration
Create Date: 2024-12-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_add_federated_evaluation_models'
down_revision = '007_phase3_z3_integration'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add federated evaluation framework models."""
    
    # Create enum types
    platform_type_enum = postgresql.ENUM(
        'cloud_openai', 'cloud_anthropic', 'cloud_cohere', 'cloud_groq', 
        'local_ollama', 'acgs_internal',
        name='platformtypeenum'
    )
    platform_type_enum.create(op.get_bind())
    
    evaluation_status_enum = postgresql.ENUM(
        'pending', 'running', 'completed', 'failed', 'cancelled',
        name='evaluationstatusenum'
    )
    evaluation_status_enum.create(op.get_bind())
    
    node_status_enum = postgresql.ENUM(
        'active', 'inactive', 'maintenance', 'error',
        name='nodestatusenum'
    )
    node_status_enum.create(op.get_bind())
    
    aggregation_method_enum = postgresql.ENUM(
        'federated_averaging', 'secure_sum', 'differential_private', 'byzantine_robust',
        name='aggregationmethodenum'
    )
    aggregation_method_enum.create(op.get_bind())
    
    # Create federated_nodes table
    op.create_table('federated_nodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.String(length=100), nullable=False),
        sa.Column('platform_type', platform_type_enum, nullable=False),
        sa.Column('endpoint_url', sa.String(length=500), nullable=False),
        sa.Column('api_key_hash', sa.String(length=255), nullable=True),
        sa.Column('capabilities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('configuration', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', node_status_enum, nullable=False),
        sa.Column('last_heartbeat', sa.DateTime(timezone=True), nullable=True),
        sa.Column('health_score', sa.Float(), nullable=False),
        sa.Column('total_evaluations', sa.Integer(), nullable=False),
        sa.Column('successful_evaluations', sa.Integer(), nullable=False),
        sa.Column('failed_evaluations', sa.Integer(), nullable=False),
        sa.Column('average_response_time_ms', sa.Float(), nullable=False),
        sa.Column('mab_template_preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('prompt_optimization_history', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_federated_nodes_id'), 'federated_nodes', ['id'], unique=False)
    op.create_index(op.f('ix_federated_nodes_node_id'), 'federated_nodes', ['node_id'], unique=True)
    op.create_index(op.f('ix_federated_nodes_platform_type'), 'federated_nodes', ['platform_type'], unique=False)
    op.create_index(op.f('ix_federated_nodes_status'), 'federated_nodes', ['status'], unique=False)
    
    # Create federated_evaluations table
    op.create_table('federated_evaluations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.String(length=100), nullable=False),
        sa.Column('policy_content', sa.Text(), nullable=False),
        sa.Column('evaluation_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('target_platforms', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('privacy_requirements', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('privacy_budget_used', sa.Float(), nullable=False),
        sa.Column('mab_context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('selected_template_id', sa.String(length=100), nullable=True),
        sa.Column('status', evaluation_status_enum, nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('estimated_completion_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('aggregated_results', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('aggregation_method', aggregation_method_enum, nullable=True),
        sa.Column('participant_count', sa.Integer(), nullable=False),
        sa.Column('byzantine_nodes_detected', sa.Integer(), nullable=False),
        sa.Column('total_execution_time_ms', sa.Float(), nullable=True),
        sa.Column('cross_platform_consistency_score', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('submitted_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['submitted_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_federated_evaluations_id'), 'federated_evaluations', ['id'], unique=False)
    op.create_index(op.f('ix_federated_evaluations_task_id'), 'federated_evaluations', ['task_id'], unique=True)
    op.create_index(op.f('ix_federated_evaluations_status'), 'federated_evaluations', ['status'], unique=False)
    
    # Create evaluation_node_assignments table
    op.create_table('evaluation_node_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('evaluation_id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['evaluation_id'], ['federated_evaluations.id'], ),
        sa.ForeignKeyConstraint(['node_id'], ['federated_nodes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evaluation_node_assignments_id'), 'evaluation_node_assignments', ['id'], unique=False)
    op.create_index(op.f('ix_evaluation_node_assignments_status'), 'evaluation_node_assignments', ['status'], unique=False)
    
    # Create evaluation_node_results table
    op.create_table('evaluation_node_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('evaluation_id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=False),
        sa.Column('raw_response', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('processed_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('policy_compliance_score', sa.Float(), nullable=True),
        sa.Column('execution_time_ms', sa.Float(), nullable=True),
        sa.Column('success_rate', sa.Float(), nullable=True),
        sa.Column('consistency_score', sa.Float(), nullable=True),
        sa.Column('privacy_score', sa.Float(), nullable=True),
        sa.Column('is_byzantine', sa.Boolean(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('validation_passed', sa.Boolean(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['evaluation_id'], ['federated_evaluations.id'], ),
        sa.ForeignKeyConstraint(['node_id'], ['federated_nodes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evaluation_node_results_id'), 'evaluation_node_results', ['id'], unique=False)


def downgrade() -> None:
    """Remove federated evaluation framework models."""
    
    # Drop tables in reverse order
    op.drop_index(op.f('ix_evaluation_node_results_id'), table_name='evaluation_node_results')
    op.drop_table('evaluation_node_results')
    
    op.drop_index(op.f('ix_evaluation_node_assignments_status'), table_name='evaluation_node_assignments')
    op.drop_index(op.f('ix_evaluation_node_assignments_id'), table_name='evaluation_node_assignments')
    op.drop_table('evaluation_node_assignments')
    
    op.drop_index(op.f('ix_federated_evaluations_status'), table_name='federated_evaluations')
    op.drop_index(op.f('ix_federated_evaluations_task_id'), table_name='federated_evaluations')
    op.drop_index(op.f('ix_federated_evaluations_id'), table_name='federated_evaluations')
    op.drop_table('federated_evaluations')
    
    op.drop_index(op.f('ix_federated_nodes_status'), table_name='federated_nodes')
    op.drop_index(op.f('ix_federated_nodes_platform_type'), table_name='federated_nodes')
    op.drop_index(op.f('ix_federated_nodes_node_id'), table_name='federated_nodes')
    op.drop_index(op.f('ix_federated_nodes_id'), table_name='federated_nodes')
    op.drop_table('federated_nodes')
    
    # Drop enum types
    postgresql.ENUM(name='aggregationmethodenum').drop(op.get_bind())
    postgresql.ENUM(name='nodestatusenum').drop(op.get_bind())
    postgresql.ENUM(name='evaluationstatusenum').drop(op.get_bind())
    postgresql.ENUM(name='platformtypeenum').drop(op.get_bind())
