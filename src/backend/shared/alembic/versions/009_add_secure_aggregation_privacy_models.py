"""Add secure aggregation and privacy models

Revision ID: 009_add_secure_aggregation_privacy_models
Revises: 008_add_federated_evaluation_models
Create Date: 2024-12-19 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_add_secure_aggregation_privacy_models'
down_revision = '008_add_federated_evaluation_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add secure aggregation and privacy tracking models."""
    
    # Create secure_aggregation_sessions table
    op.create_table('secure_aggregation_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=100), nullable=False),
        sa.Column('evaluation_id', sa.Integer(), nullable=False),
        sa.Column('aggregation_method', postgresql.ENUM(
            'federated_averaging', 'secure_sum', 'differential_private', 'byzantine_robust',
            name='aggregationmethodenum'
        ), nullable=False),
        sa.Column('participant_nodes', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('minimum_participants', sa.Integer(), nullable=False),
        sa.Column('encryption_scheme', sa.String(length=100), nullable=True),
        sa.Column('key_exchange_completed', sa.Boolean(), nullable=False),
        sa.Column('verification_hashes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('privacy_epsilon', sa.Float(), nullable=True),
        sa.Column('privacy_delta', sa.Float(), nullable=True),
        sa.Column('noise_mechanism', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('aggregated_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('privacy_budget_consumed', sa.Float(), nullable=False),
        sa.Column('byzantine_nodes_detected', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['evaluation_id'], ['federated_evaluations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_secure_aggregation_sessions_id'), 'secure_aggregation_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_secure_aggregation_sessions_session_id'), 'secure_aggregation_sessions', ['session_id'], unique=True)
    op.create_index(op.f('ix_secure_aggregation_sessions_status'), 'secure_aggregation_sessions', ['status'], unique=False)
    
    # Create secure_shares table
    op.create_table('secure_shares',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('share_id', sa.String(length=100), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=False),
        sa.Column('encrypted_value', sa.Text(), nullable=False),
        sa.Column('verification_hash', sa.String(length=255), nullable=False),
        sa.Column('share_index', sa.Integer(), nullable=False),
        sa.Column('encryption_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['secure_aggregation_sessions.id'], ),
        sa.ForeignKeyConstraint(['node_id'], ['federated_nodes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_secure_shares_id'), 'secure_shares', ['id'], unique=False)
    op.create_index(op.f('ix_secure_shares_share_id'), 'secure_shares', ['share_id'], unique=True)
    
    # Create privacy_metrics table
    op.create_table('privacy_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('evaluation_id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=True),
        sa.Column('epsilon_consumed', sa.Float(), nullable=True),
        sa.Column('delta_consumed', sa.Float(), nullable=True),
        sa.Column('privacy_score', sa.Float(), nullable=True),
        sa.Column('data_minimization_score', sa.Float(), nullable=True),
        sa.Column('anonymization_level', sa.Float(), nullable=True),
        sa.Column('inference_resistance', sa.Float(), nullable=True),
        sa.Column('mechanisms_applied', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('noise_parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('gdpr_compliant', sa.Boolean(), nullable=True),
        sa.Column('ccpa_compliant', sa.Boolean(), nullable=True),
        sa.Column('hipaa_compliant', sa.Boolean(), nullable=True),
        sa.Column('measured_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['evaluation_id'], ['federated_evaluations.id'], ),
        sa.ForeignKeyConstraint(['node_id'], ['federated_nodes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_privacy_metrics_id'), 'privacy_metrics', ['id'], unique=False)
    
    # Create constitutional_validations table
    op.create_table('constitutional_validations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('evaluation_id', sa.Integer(), nullable=False),
        sa.Column('principle_ids_validated', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('compliance_score', sa.Float(), nullable=True),
        sa.Column('constitutional_violations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('validation_method', sa.String(length=100), nullable=True),
        sa.Column('validator_confidence', sa.Float(), nullable=True),
        sa.Column('consistency_across_platforms', sa.Float(), nullable=True),
        sa.Column('platform_specific_issues', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('council_review_required', sa.Boolean(), nullable=False),
        sa.Column('council_decision', sa.String(length=100), nullable=True),
        sa.Column('council_feedback', sa.Text(), nullable=True),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('council_reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['evaluation_id'], ['federated_evaluations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_constitutional_validations_id'), 'constitutional_validations', ['id'], unique=False)
    
    # Create performance indexes
    op.create_index('ix_federated_node_platform_status', 'federated_nodes', ['platform_type', 'status'])
    op.create_index('ix_federated_evaluation_status_created', 'federated_evaluations', ['status', 'created_at'])
    op.create_index('ix_evaluation_node_result_evaluation_node', 'evaluation_node_results', ['evaluation_id', 'node_id'])
    op.create_index('ix_secure_aggregation_session_status', 'secure_aggregation_sessions', ['status', 'started_at'])
    op.create_index('ix_privacy_metric_evaluation_measured', 'privacy_metrics', ['evaluation_id', 'measured_at'])
    op.create_index('ix_constitutional_validation_evaluation', 'constitutional_validations', ['evaluation_id', 'validated_at'])


def downgrade() -> None:
    """Remove secure aggregation and privacy tracking models."""
    
    # Drop performance indexes
    op.drop_index('ix_constitutional_validation_evaluation', table_name='constitutional_validations')
    op.drop_index('ix_privacy_metric_evaluation_measured', table_name='privacy_metrics')
    op.drop_index('ix_secure_aggregation_session_status', table_name='secure_aggregation_sessions')
    op.drop_index('ix_evaluation_node_result_evaluation_node', table_name='evaluation_node_results')
    op.drop_index('ix_federated_evaluation_status_created', table_name='federated_evaluations')
    op.drop_index('ix_federated_node_platform_status', table_name='federated_nodes')
    
    # Drop tables in reverse order
    op.drop_index(op.f('ix_constitutional_validations_id'), table_name='constitutional_validations')
    op.drop_table('constitutional_validations')
    
    op.drop_index(op.f('ix_privacy_metrics_id'), table_name='privacy_metrics')
    op.drop_table('privacy_metrics')
    
    op.drop_index(op.f('ix_secure_shares_share_id'), table_name='secure_shares')
    op.drop_index(op.f('ix_secure_shares_id'), table_name='secure_shares')
    op.drop_table('secure_shares')
    
    op.drop_index(op.f('ix_secure_aggregation_sessions_status'), table_name='secure_aggregation_sessions')
    op.drop_index(op.f('ix_secure_aggregation_sessions_session_id'), table_name='secure_aggregation_sessions')
    op.drop_index(op.f('ix_secure_aggregation_sessions_id'), table_name='secure_aggregation_sessions')
    op.drop_table('secure_aggregation_sessions')
