"""Phase 3: Z3 SMT Solver Integration and Advanced Verification

Revision ID: 007_phase3_z3_integration
Revises: 005_fix_refresh_token_length
Create Date: 2024-12-19 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_phase3_z3_integration'
down_revision = '005_fix_refresh_token_length'
branch_labels = None
depends_on = None


def upgrade():
    """Add Phase 3 Z3 integration and advanced verification tables."""

    # Define enums for use in table creation
    safety_property_type_enum = postgresql.ENUM(
        'safety', 'liveness', 'security', 'fairness',
        name='safety_property_type_enum'
    )

    validation_tier_enum = postgresql.ENUM(
        'automated', 'human_in_the_loop', 'rigorous',
        name='validation_tier_enum'
    )

    validation_level_enum = postgresql.ENUM(
        'baseline', 'standard', 'comprehensive', 'critical',
        name='validation_level_enum'
    )

    conflict_type_enum = postgresql.ENUM(
        'logical_contradiction', 'practical_incompatibility',
        'priority_conflict', 'resource_conflict',
        name='conflict_type_enum'
    )

    # Create safety_properties table
    op.create_table(
        'safety_properties',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.String(255), nullable=False, unique=True),
        sa.Column('property_type', safety_property_type_enum, nullable=False),
        sa.Column('property_description', sa.Text(), nullable=False),
        sa.Column('formal_specification', sa.Text(), nullable=False),
        sa.Column('criticality_level', sa.String(50), nullable=False, default='medium'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL')
    )
    
    # 6. Create tiered_verification_results table
    op.create_table(
        'tiered_verification_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('policy_rule_id', sa.Integer(), nullable=False),
        sa.Column('validation_tier', validation_tier_enum, nullable=False),
        sa.Column('validation_level', validation_level_enum, nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('verification_method', sa.String(255), nullable=False),
        sa.Column('proof_trace', sa.Text(), nullable=True),
        sa.Column('counter_example', sa.Text(), nullable=True),
        sa.Column('safety_violations', sa.JSON(), nullable=True),
        sa.Column('human_review_notes', sa.Text(), nullable=True),
        sa.Column('verification_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('verified_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['policy_rule_id'], ['policy_rules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['verified_by'], ['users.id'], ondelete='SET NULL')
    )
    
    # 7. Create safety_check_results table
    op.create_table(
        'safety_check_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.String(255), nullable=False),
        sa.Column('policy_rule_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),  # satisfied, violated, unknown
        sa.Column('witness_trace', sa.Text(), nullable=True),
        sa.Column('counter_example_trace', sa.Text(), nullable=True),
        sa.Column('verification_depth', sa.Integer(), nullable=True),
        sa.Column('verification_time_ms', sa.Integer(), nullable=True),
        sa.Column('verification_method', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('checked_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['policy_rule_id'], ['policy_rules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['checked_by'], ['users.id'], ondelete='SET NULL')
    )
    
    # 8. Create conflict_detection_results table
    op.create_table(
        'conflict_detection_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conflict_id', sa.String(255), nullable=False, unique=True),
        sa.Column('conflict_type', conflict_type_enum, nullable=False),
        sa.Column('conflicting_rule_ids', sa.JSON(), nullable=False),  # Array of rule IDs
        sa.Column('conflict_description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('resolution_suggestion', sa.Text(), nullable=True),
        sa.Column('affected_principle_ids', sa.JSON(), nullable=True),  # Array of principle IDs
        sa.Column('resolution_status', sa.String(50), nullable=False, default='unresolved'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('detected_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['detected_by'], ['users.id'], ondelete='SET NULL')
    )
    
    # 9. Create z3_solver_cache table for performance optimization
    op.create_table(
        'z3_solver_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cache_key', sa.String(255), nullable=False, unique=True),
        sa.Column('input_hash', sa.String(64), nullable=False),  # SHA-256 hash of input
        sa.Column('datalog_rules', sa.JSON(), nullable=False),
        sa.Column('proof_obligations', sa.JSON(), nullable=False),
        sa.Column('result_status', sa.String(50), nullable=False),
        sa.Column('is_satisfiable', sa.Boolean(), nullable=False),
        sa.Column('is_unsatisfiable', sa.Boolean(), nullable=False),
        sa.Column('counter_example', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('solver_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_accessed', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('access_count', sa.Integer(), nullable=False, default=1),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 10. Create verification_audit_log table for comprehensive tracking
    op.create_table(
        'verification_audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('policy_rule_id', sa.Integer(), nullable=False),
        sa.Column('verification_type', sa.String(100), nullable=False),  # tiered, safety, conflict, standard
        sa.Column('validation_tier', validation_tier_enum, nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('verification_details', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['policy_rule_id'], ['policy_rules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL')
    )
    
    # 11. Add indexes for performance
    op.create_index('idx_tiered_verification_results_rule_tier', 'tiered_verification_results', ['policy_rule_id', 'validation_tier'])
    op.create_index('idx_tiered_verification_results_status', 'tiered_verification_results', ['status'])
    op.create_index('idx_tiered_verification_results_created_at', 'tiered_verification_results', ['created_at'])
    
    op.create_index('idx_safety_check_results_property_rule', 'safety_check_results', ['property_id', 'policy_rule_id'])
    op.create_index('idx_safety_check_results_status', 'safety_check_results', ['status'])
    
    op.create_index('idx_conflict_detection_results_type', 'conflict_detection_results', ['conflict_type'])
    op.create_index('idx_conflict_detection_results_severity', 'conflict_detection_results', ['severity'])
    op.create_index('idx_conflict_detection_results_resolution_status', 'conflict_detection_results', ['resolution_status'])
    
    op.create_index('idx_z3_solver_cache_input_hash', 'z3_solver_cache', ['input_hash'])
    op.create_index('idx_z3_solver_cache_last_accessed', 'z3_solver_cache', ['last_accessed'])
    
    op.create_index('idx_verification_audit_log_rule_type', 'verification_audit_log', ['policy_rule_id', 'verification_type'])
    op.create_index('idx_verification_audit_log_created_at', 'verification_audit_log', ['created_at'])
    op.create_index('idx_verification_audit_log_user_id', 'verification_audit_log', ['user_id'])
    
    # 12. Add Phase 3 specific columns to existing policy_rules table
    op.add_column('policy_rules', sa.Column('z3_verification_status', sa.String(50), nullable=True))
    op.add_column('policy_rules', sa.Column('last_z3_verification', sa.DateTime(timezone=True), nullable=True))
    op.add_column('policy_rules', sa.Column('safety_check_status', sa.String(50), nullable=True))
    op.add_column('policy_rules', sa.Column('conflict_check_status', sa.String(50), nullable=True))
    op.add_column('policy_rules', sa.Column('verification_confidence', sa.Float(), nullable=True))
    op.add_column('policy_rules', sa.Column('requires_human_review', sa.Boolean(), nullable=False, default=False))


def downgrade():
    """Remove Phase 3 Z3 integration and advanced verification tables."""
    
    # Remove added columns from policy_rules
    op.drop_column('policy_rules', 'requires_human_review')
    op.drop_column('policy_rules', 'verification_confidence')
    op.drop_column('policy_rules', 'conflict_check_status')
    op.drop_column('policy_rules', 'safety_check_status')
    op.drop_column('policy_rules', 'last_z3_verification')
    op.drop_column('policy_rules', 'z3_verification_status')
    
    # Drop indexes
    op.drop_index('idx_verification_audit_log_user_id')
    op.drop_index('idx_verification_audit_log_created_at')
    op.drop_index('idx_verification_audit_log_rule_type')
    op.drop_index('idx_z3_solver_cache_last_accessed')
    op.drop_index('idx_z3_solver_cache_input_hash')
    op.drop_index('idx_conflict_detection_results_resolution_status')
    op.drop_index('idx_conflict_detection_results_severity')
    op.drop_index('idx_conflict_detection_results_type')
    op.drop_index('idx_safety_check_results_status')
    op.drop_index('idx_safety_check_results_property_rule')
    op.drop_index('idx_tiered_verification_results_created_at')
    op.drop_index('idx_tiered_verification_results_status')
    op.drop_index('idx_tiered_verification_results_rule_tier')
    
    # Drop tables
    op.drop_table('verification_audit_log')
    op.drop_table('z3_solver_cache')
    op.drop_table('conflict_detection_results')
    op.drop_table('safety_check_results')
    op.drop_table('tiered_verification_results')
    op.drop_table('safety_properties')
    
    # Note: Enums will be dropped automatically by SQLAlchemy when tables are dropped
    # No need to explicitly drop them here
