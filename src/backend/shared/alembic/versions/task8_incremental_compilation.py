"""Task 8: Add PolicyVersion model for incremental compilation

Revision ID: task8_incremental_compilation
Revises: i4j5k6l7m8n9
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'task8_incremental_compilation'
down_revision = 'i4j5k6l7m8n9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add PolicyVersion model and enhance PolicyRule for incremental compilation."""
    
    # Add incremental compilation fields to policy_rules table
    op.add_column('policy_rules', sa.Column('compilation_hash', sa.String(64), nullable=True))
    op.add_column('policy_rules', sa.Column('last_compiled_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('policy_rules', sa.Column('compilation_status', sa.String(50), nullable=False, server_default='pending'))
    op.add_column('policy_rules', sa.Column('compilation_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # Create indexes for policy_rules
    op.create_index('ix_policy_rules_compilation_hash', 'policy_rules', ['compilation_hash'])
    op.create_index('ix_policy_rules_compilation_status', 'policy_rules', ['compilation_status'])
    
    # Create policy_versions table
    op.create_table(
        'policy_versions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('policy_rule_id', sa.Integer(), sa.ForeignKey('policy_rules.id'), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False, index=True),
        sa.Column('compilation_hash', sa.String(64), nullable=True, index=True),
        
        # Compilation metadata
        sa.Column('compilation_status', sa.String(50), nullable=False, server_default='pending', index=True),
        sa.Column('compilation_time_ms', sa.Float(), nullable=True),
        sa.Column('compilation_strategy', sa.String(50), nullable=True),
        
        # Version control and rollback support
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false', index=True),
        sa.Column('is_rollback_point', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('rollback_reason', sa.Text(), nullable=True),
        
        # Constitutional amendment integration
        sa.Column('amendment_id', sa.Integer(), sa.ForeignKey('ac_amendments.id'), nullable=True),
        
        # Deployment tracking
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deployment_status', sa.String(50), nullable=False, server_default='pending', index=True),
        sa.Column('deployment_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        
        # Backward compatibility tracking (3-version requirement)
        sa.Column('compatible_versions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('breaking_changes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        
        # Timestamps and user tracking
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
    )
    
    # Create indexes for policy_versions
    op.create_index('ix_policy_versions_policy_rule_id', 'policy_versions', ['policy_rule_id'])
    op.create_index('ix_policy_versions_version_number', 'policy_versions', ['version_number'])
    op.create_index('ix_policy_versions_content_hash', 'policy_versions', ['content_hash'])
    op.create_index('ix_policy_versions_compilation_hash', 'policy_versions', ['compilation_hash'])
    op.create_index('ix_policy_versions_compilation_status', 'policy_versions', ['compilation_status'])
    op.create_index('ix_policy_versions_is_active', 'policy_versions', ['is_active'])
    op.create_index('ix_policy_versions_deployment_status', 'policy_versions', ['deployment_status'])
    op.create_index('ix_policy_versions_created_at', 'policy_versions', ['created_at'])
    
    # Create composite indexes for common queries
    op.create_index(
        'ix_policy_versions_policy_active', 
        'policy_versions', 
        ['policy_rule_id', 'is_active']
    )
    op.create_index(
        'ix_policy_versions_policy_version', 
        'policy_versions', 
        ['policy_rule_id', 'version_number']
    )
    op.create_index(
        'ix_policy_versions_deployment_status_created', 
        'policy_versions', 
        ['deployment_status', 'created_at']
    )
    
    # Add constraints
    op.create_unique_constraint(
        'uq_policy_versions_policy_version',
        'policy_versions',
        ['policy_rule_id', 'version_number']
    )
    
    # Create check constraints
    op.create_check_constraint(
        'ck_policy_versions_version_positive',
        'policy_versions',
        'version_number > 0'
    )
    
    op.create_check_constraint(
        'ck_policy_versions_compilation_time_positive',
        'policy_versions',
        'compilation_time_ms IS NULL OR compilation_time_ms >= 0'
    )
    
    op.create_check_constraint(
        'ck_policy_versions_compilation_status',
        'policy_versions',
        "compilation_status IN ('pending', 'compiled', 'failed')"
    )
    
    op.create_check_constraint(
        'ck_policy_versions_deployment_status',
        'policy_versions',
        "deployment_status IN ('pending', 'deploying', 'deployed', 'failed', 'rolling_back', 'rolled_back')"
    )
    
    op.create_check_constraint(
        'ck_policy_versions_compilation_strategy',
        'policy_versions',
        "compilation_strategy IS NULL OR compilation_strategy IN ('full', 'incremental', 'partial', 'optimized', 'hot_swap', 'rollback')"
    )


def downgrade() -> None:
    """Remove PolicyVersion model and incremental compilation enhancements."""
    
    # Drop policy_versions table (this will automatically drop its indexes and constraints)
    op.drop_table('policy_versions')
    
    # Remove incremental compilation fields from policy_rules table
    op.drop_index('ix_policy_rules_compilation_status', 'policy_rules')
    op.drop_index('ix_policy_rules_compilation_hash', 'policy_rules')
    
    op.drop_column('policy_rules', 'compilation_metrics')
    op.drop_column('policy_rules', 'compilation_status')
    op.drop_column('policy_rules', 'last_compiled_at')
    op.drop_column('policy_rules', 'compilation_hash')
