"""Add WINA Constitutional Updates tables

Revision ID: 006_add_wina_constitutional_updates
Revises: 005_add_qec_conflict_resolution_fields
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_add_wina_constitutional_updates'
down_revision = '005_add_qec_conflict_resolution_fields'
branch_labels = None
depends_on = None


def upgrade():
    """Add WINA constitutional updates tables and fields."""
    
    # Create table for WINA constitutional principle updates
    op.create_table('wina_constitutional_updates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('principle_id', sa.String(50), nullable=False),
        sa.Column('update_type', sa.String(20), nullable=False),
        sa.Column('proposed_content', sa.Text(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('efficiency_impact', postgresql.JSONB(), nullable=True),
        sa.Column('compliance_assessment', postgresql.JSONB(), nullable=True),
        sa.Column('approval_status', sa.String(30), nullable=False, default='pending'),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        
        # Enhanced WINA-specific fields
        sa.Column('wina_analysis', postgresql.JSONB(), nullable=True),
        sa.Column('constitutional_distance', sa.Float(), nullable=True),
        sa.Column('risk_assessment', postgresql.JSONB(), nullable=True),
        sa.Column('validation_criteria', postgresql.JSONB(), nullable=True),
        sa.Column('recovery_strategies', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        
        # Tracking fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('approved_by_user_id', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['approved_by_user_id'], ['users.id'], ),
        
        comment='WINA-informed constitutional principle updates'
    )
    
    # Create indexes for performance
    op.create_index('idx_wina_updates_principle_id', 'wina_constitutional_updates', ['principle_id'])
    op.create_index('idx_wina_updates_approval_status', 'wina_constitutional_updates', ['approval_status'])
    op.create_index('idx_wina_updates_update_type', 'wina_constitutional_updates', ['update_type'])
    op.create_index('idx_wina_updates_timestamp', 'wina_constitutional_updates', ['timestamp'])
    op.create_index('idx_wina_updates_constitutional_distance', 'wina_constitutional_updates', ['constitutional_distance'])
    
    # Create table for WINA optimization analysis results
    op.create_table('wina_optimization_analysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('principle_id', sa.String(50), nullable=False),
        sa.Column('analysis_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('optimization_potential', sa.Float(), nullable=False),
        sa.Column('efficiency_impact', postgresql.JSONB(), nullable=True),
        sa.Column('constitutional_compatibility', sa.Float(), nullable=True),
        sa.Column('risk_factors', postgresql.JSONB(), nullable=True),
        sa.Column('recommendations', postgresql.JSONB(), nullable=True),
        sa.Column('wina_specific_insights', postgresql.JSONB(), nullable=True),
        sa.Column('optimization_context', postgresql.JSONB(), nullable=True),
        sa.Column('analyzer_version', sa.String(20), nullable=True),
        
        # Tracking fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        
        comment='WINA optimization analysis results for constitutional principles'
    )
    
    # Create indexes for analysis table
    op.create_index('idx_wina_analysis_principle_id', 'wina_optimization_analysis', ['principle_id'])
    op.create_index('idx_wina_analysis_timestamp', 'wina_optimization_analysis', ['analysis_timestamp'])
    op.create_index('idx_wina_analysis_optimization_potential', 'wina_optimization_analysis', ['optimization_potential'])
    
    # Create table for WINA update performance monitoring
    op.create_table('wina_update_performance_monitoring',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('update_id', sa.Integer(), nullable=False),
        sa.Column('monitoring_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('monitoring_duration', sa.Integer(), nullable=False),
        sa.Column('performance_metrics', postgresql.JSONB(), nullable=True),
        sa.Column('compliance_status', sa.String(20), nullable=False),
        sa.Column('issues_detected', postgresql.JSONB(), nullable=True),
        sa.Column('recommendations', postgresql.JSONB(), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=True),
        
        # Tracking fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['update_id'], ['wina_constitutional_updates.id'], ),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        
        comment='Performance monitoring results for applied WINA constitutional updates'
    )
    
    # Create indexes for monitoring table
    op.create_index('idx_wina_monitoring_update_id', 'wina_update_performance_monitoring', ['update_id'])
    op.create_index('idx_wina_monitoring_start', 'wina_update_performance_monitoring', ['monitoring_start'])
    op.create_index('idx_wina_monitoring_compliance_status', 'wina_update_performance_monitoring', ['compliance_status'])
    op.create_index('idx_wina_monitoring_overall_score', 'wina_update_performance_monitoring', ['overall_score'])
    
    # Create table for WINA constitutional update approvals (Constitutional Council integration)
    op.create_table('wina_update_approvals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('update_id', sa.Integer(), nullable=False),
        sa.Column('amendment_id', sa.Integer(), nullable=True),  # Link to AC amendments
        sa.Column('approval_type', sa.String(20), nullable=False),  # 'auto', 'council', 'manual'
        sa.Column('approval_status', sa.String(20), nullable=False),
        sa.Column('approval_context', postgresql.JSONB(), nullable=True),
        sa.Column('submission_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('approval_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('estimated_review_time', sa.String(50), nullable=True),
        sa.Column('council_tracking_info', postgresql.JSONB(), nullable=True),
        
        # Tracking fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('submitted_by_user_id', sa.Integer(), nullable=True),
        sa.Column('approved_by_user_id', sa.Integer(), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['update_id'], ['wina_constitutional_updates.id'], ),
        sa.ForeignKeyConstraint(['amendment_id'], ['ac_amendments.id'], ),
        sa.ForeignKeyConstraint(['submitted_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['approved_by_user_id'], ['users.id'], ),
        
        comment='Approval tracking for WINA constitutional updates'
    )
    
    # Create indexes for approvals table
    op.create_index('idx_wina_approvals_update_id', 'wina_update_approvals', ['update_id'])
    op.create_index('idx_wina_approvals_amendment_id', 'wina_update_approvals', ['amendment_id'])
    op.create_index('idx_wina_approvals_status', 'wina_update_approvals', ['approval_status'])
    op.create_index('idx_wina_approvals_type', 'wina_update_approvals', ['approval_type'])
    op.create_index('idx_wina_approvals_submission_timestamp', 'wina_update_approvals', ['submission_timestamp'])
    
    # Add WINA-related fields to existing constitutional_principles table
    op.add_column('constitutional_principles', 
                  sa.Column('wina_optimization_enabled', 
                           sa.Boolean, 
                           nullable=True, 
                           default=False,
                           comment='Whether WINA optimization is enabled for this principle'))
    
    op.add_column('constitutional_principles', 
                  sa.Column('wina_optimization_config', 
                           postgresql.JSONB(), 
                           nullable=True,
                           comment='WINA optimization configuration for this principle'))
    
    op.add_column('constitutional_principles', 
                  sa.Column('wina_last_analysis_at', 
                           sa.DateTime(timezone=True), 
                           nullable=True,
                           comment='Timestamp of last WINA analysis for this principle'))
    
    op.add_column('constitutional_principles', 
                  sa.Column('wina_optimization_potential', 
                           sa.Float, 
                           nullable=True,
                           comment='Last calculated WINA optimization potential (0.0-1.0)'))
    
    # Create indexes for new constitutional_principles fields
    op.create_index('idx_constitutional_principles_wina_enabled', 
                    'constitutional_principles', 
                    ['wina_optimization_enabled'])
    op.create_index('idx_constitutional_principles_wina_potential', 
                    'constitutional_principles', 
                    ['wina_optimization_potential'])
    op.create_index('idx_constitutional_principles_wina_last_analysis', 
                    'constitutional_principles', 
                    ['wina_last_analysis_at'])


def downgrade():
    """Remove WINA constitutional updates tables and fields."""
    
    # Drop indexes for constitutional_principles WINA fields
    op.drop_index('idx_constitutional_principles_wina_last_analysis', table_name='constitutional_principles')
    op.drop_index('idx_constitutional_principles_wina_potential', table_name='constitutional_principles')
    op.drop_index('idx_constitutional_principles_wina_enabled', table_name='constitutional_principles')
    
    # Remove WINA fields from constitutional_principles table
    op.drop_column('constitutional_principles', 'wina_optimization_potential')
    op.drop_column('constitutional_principles', 'wina_last_analysis_at')
    op.drop_column('constitutional_principles', 'wina_optimization_config')
    op.drop_column('constitutional_principles', 'wina_optimization_enabled')
    
    # Drop WINA update approvals table
    op.drop_index('idx_wina_approvals_submission_timestamp', table_name='wina_update_approvals')
    op.drop_index('idx_wina_approvals_type', table_name='wina_update_approvals')
    op.drop_index('idx_wina_approvals_status', table_name='wina_update_approvals')
    op.drop_index('idx_wina_approvals_amendment_id', table_name='wina_update_approvals')
    op.drop_index('idx_wina_approvals_update_id', table_name='wina_update_approvals')
    op.drop_table('wina_update_approvals')
    
    # Drop WINA update performance monitoring table
    op.drop_index('idx_wina_monitoring_overall_score', table_name='wina_update_performance_monitoring')
    op.drop_index('idx_wina_monitoring_compliance_status', table_name='wina_update_performance_monitoring')
    op.drop_index('idx_wina_monitoring_start', table_name='wina_update_performance_monitoring')
    op.drop_index('idx_wina_monitoring_update_id', table_name='wina_update_performance_monitoring')
    op.drop_table('wina_update_performance_monitoring')
    
    # Drop WINA optimization analysis table
    op.drop_index('idx_wina_analysis_optimization_potential', table_name='wina_optimization_analysis')
    op.drop_index('idx_wina_analysis_timestamp', table_name='wina_optimization_analysis')
    op.drop_index('idx_wina_analysis_principle_id', table_name='wina_optimization_analysis')
    op.drop_table('wina_optimization_analysis')
    
    # Drop WINA constitutional updates table
    op.drop_index('idx_wina_updates_constitutional_distance', table_name='wina_constitutional_updates')
    op.drop_index('idx_wina_updates_timestamp', table_name='wina_constitutional_updates')
    op.drop_index('idx_wina_updates_update_type', table_name='wina_constitutional_updates')
    op.drop_index('idx_wina_updates_approval_status', table_name='wina_constitutional_updates')
    op.drop_index('idx_wina_updates_principle_id', table_name='wina_constitutional_updates')
    op.drop_table('wina_constitutional_updates')
