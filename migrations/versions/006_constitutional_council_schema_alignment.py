"""Constitutional Council Schema Alignment

Revision ID: 006_cc_schema
Revises: 005_fix_refresh_token_length
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_cc_schema'
down_revision = '005_fix_refresh_token_length'
branch_labels = None
depends_on = None


def upgrade():
    """Add co-evolution and optimistic locking fields to ACAmendment table"""
    
    # Add co-evolution and scalability fields
    op.add_column('ac_amendments', sa.Column('urgency_level', sa.String(20), nullable=False, server_default='normal'))
    op.add_column('ac_amendments', sa.Column('co_evolution_context', postgresql.JSONB(), nullable=True))
    op.add_column('ac_amendments', sa.Column('expected_impact', sa.String(20), nullable=True))
    op.add_column('ac_amendments', sa.Column('rapid_processing_requested', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('ac_amendments', sa.Column('constitutional_significance', sa.String(20), nullable=False, server_default='normal'))
    
    # Add optimistic locking and versioning fields
    op.add_column('ac_amendments', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('ac_amendments', sa.Column('workflow_state', sa.String(50), nullable=False, server_default='proposed'))
    op.add_column('ac_amendments', sa.Column('state_transitions', postgresql.JSONB(), nullable=True))
    op.add_column('ac_amendments', sa.Column('processing_metrics', postgresql.JSONB(), nullable=True))
    
    # Create indexes for performance
    op.create_index('ix_ac_amendments_urgency_level', 'ac_amendments', ['urgency_level'])
    op.create_index('ix_ac_amendments_expected_impact', 'ac_amendments', ['expected_impact'])
    op.create_index('ix_ac_amendments_workflow_state', 'ac_amendments', ['workflow_state'])
    
    # Add check constraints for valid enum values
    op.create_check_constraint(
        'ck_ac_amendments_urgency_level',
        'ac_amendments',
        "urgency_level IN ('normal', 'rapid', 'emergency')"
    )
    
    op.create_check_constraint(
        'ck_ac_amendments_expected_impact',
        'ac_amendments',
        "expected_impact IN ('low', 'medium', 'high', 'critical')"
    )
    
    op.create_check_constraint(
        'ck_ac_amendments_constitutional_significance',
        'ac_amendments',
        "constitutional_significance IN ('normal', 'significant', 'fundamental')"
    )
    
    op.create_check_constraint(
        'ck_ac_amendments_workflow_state',
        'ac_amendments',
        "workflow_state IN ('proposed', 'under_review', 'voting', 'approved', 'rejected', 'implemented')"
    )


def downgrade():
    """Remove co-evolution and optimistic locking fields from ACAmendment table"""
    
    # Drop check constraints
    op.drop_constraint('ck_ac_amendments_urgency_level', 'ac_amendments')
    op.drop_constraint('ck_ac_amendments_expected_impact', 'ac_amendments')
    op.drop_constraint('ck_ac_amendments_constitutional_significance', 'ac_amendments')
    op.drop_constraint('ck_ac_amendments_workflow_state', 'ac_amendments')
    
    # Drop indexes
    op.drop_index('ix_ac_amendments_urgency_level', 'ac_amendments')
    op.drop_index('ix_ac_amendments_expected_impact', 'ac_amendments')
    op.drop_index('ix_ac_amendments_workflow_state', 'ac_amendments')
    
    # Drop columns
    op.drop_column('ac_amendments', 'processing_metrics')
    op.drop_column('ac_amendments', 'state_transitions')
    op.drop_column('ac_amendments', 'workflow_state')
    op.drop_column('ac_amendments', 'version')
    op.drop_column('ac_amendments', 'constitutional_significance')
    op.drop_column('ac_amendments', 'rapid_processing_requested')
    op.drop_column('ac_amendments', 'expected_impact')
    op.drop_column('ac_amendments', 'co_evolution_context')
    op.drop_column('ac_amendments', 'urgency_level')
