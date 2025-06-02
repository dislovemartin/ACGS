"""Add QEC conflict resolution fields

Revision ID: 005_add_qec_conflict_resolution_fields
Revises: 004_add_qec_enhancement_fields
Create Date: 2024-01-15 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_add_qec_conflict_resolution_fields'
down_revision = '004_add_qec_enhancement_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add QEC-related fields and indexes for conflict resolution enhancement."""
    
    # Add QEC analysis fields to ac_conflict_resolutions table
    op.add_column('ac_conflict_resolutions', 
                  sa.Column('qec_analysis_data', postgresql.JSONB(), nullable=True))
    op.add_column('ac_conflict_resolutions', 
                  sa.Column('priority_score', sa.Float(), nullable=True))
    op.add_column('ac_conflict_resolutions', 
                  sa.Column('qec_enhanced', sa.Boolean(), default=False, nullable=False))
    op.add_column('ac_conflict_resolutions', 
                  sa.Column('qec_analysis_timestamp', sa.DateTime(), nullable=True))
    
    # Create indexes for QEC-related queries
    op.create_index('idx_conflict_priority_score', 'ac_conflict_resolutions', ['priority_score'])
    op.create_index('idx_conflict_qec_enhanced', 'ac_conflict_resolutions', ['qec_enhanced'])
    op.create_index('idx_conflict_qec_timestamp', 'ac_conflict_resolutions', ['qec_analysis_timestamp'])
    
    # Create table for QEC conflict analysis logs
    op.create_table('qec_conflict_analysis_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conflict_id', sa.Integer(), nullable=False),
        sa.Column('analysis_timestamp', sa.DateTime(), nullable=False),
        sa.Column('constitutional_distances', postgresql.JSONB(), nullable=True),
        sa.Column('average_distance', sa.Float(), nullable=True),
        sa.Column('error_predictions', postgresql.JSONB(), nullable=True),
        sa.Column('recommended_strategy', sa.String(100), nullable=True),
        sa.Column('priority_score', sa.Float(), nullable=True),
        sa.Column('validation_scenarios', postgresql.JSONB(), nullable=True),
        sa.Column('qec_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['conflict_id'], ['ac_conflict_resolutions.id'], ondelete='CASCADE')
    )
    
    # Create indexes for analysis logs
    op.create_index('idx_analysis_logs_conflict_id', 'qec_conflict_analysis_logs', ['conflict_id'])
    op.create_index('idx_analysis_logs_timestamp', 'qec_conflict_analysis_logs', ['analysis_timestamp'])
    op.create_index('idx_analysis_logs_priority', 'qec_conflict_analysis_logs', ['priority_score'])
    
    # Create table for QEC patch generation logs
    op.create_table('qec_patch_generation_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conflict_id', sa.Integer(), nullable=False),
        sa.Column('generation_timestamp', sa.DateTime(), nullable=False),
        sa.Column('patch_success', sa.Boolean(), nullable=False),
        sa.Column('strategy_used', sa.String(100), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('validation_tests_count', sa.Integer(), nullable=True),
        sa.Column('patch_content', sa.Text(), nullable=True),
        sa.Column('patch_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['conflict_id'], ['ac_conflict_resolutions.id'], ondelete='CASCADE')
    )
    
    # Create indexes for patch generation logs
    op.create_index('idx_patch_logs_conflict_id', 'qec_patch_generation_logs', ['conflict_id'])
    op.create_index('idx_patch_logs_timestamp', 'qec_patch_generation_logs', ['generation_timestamp'])
    op.create_index('idx_patch_logs_success', 'qec_patch_generation_logs', ['patch_success'])
    op.create_index('idx_patch_logs_confidence', 'qec_patch_generation_logs', ['confidence_score'])
    
    # Create table for constitutional fidelity monitoring
    op.create_table('constitutional_fidelity_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('composite_score', sa.Float(), nullable=False),
        sa.Column('fidelity_level', sa.String(20), nullable=False),
        sa.Column('principle_coverage', sa.Float(), nullable=True),
        sa.Column('synthesis_success', sa.Float(), nullable=True),
        sa.Column('enforcement_reliability', sa.Float(), nullable=True),
        sa.Column('adaptation_speed', sa.Float(), nullable=True),
        sa.Column('stakeholder_satisfaction', sa.Float(), nullable=True),
        sa.Column('appeal_frequency', sa.Float(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for fidelity history
    op.create_index('idx_fidelity_timestamp', 'constitutional_fidelity_history', ['timestamp'])
    op.create_index('idx_fidelity_composite_score', 'constitutional_fidelity_history', ['composite_score'])
    op.create_index('idx_fidelity_level', 'constitutional_fidelity_history', ['fidelity_level'])
    
    # Create table for fidelity alerts
    op.create_table('constitutional_fidelity_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_level', sa.String(20), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('components_affected', postgresql.JSONB(), nullable=True),
        sa.Column('recommended_actions', postgresql.JSONB(), nullable=True),
        sa.Column('alert_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('resolved', sa.Boolean(), default=False, nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for fidelity alerts
    op.create_index('idx_alerts_level', 'constitutional_fidelity_alerts', ['alert_level'])
    op.create_index('idx_alerts_timestamp', 'constitutional_fidelity_alerts', ['timestamp'])
    op.create_index('idx_alerts_resolved', 'constitutional_fidelity_alerts', ['resolved'])
    
    # Add GIN indexes for JSONB columns for better query performance
    op.create_index('idx_conflict_qec_analysis_gin', 'ac_conflict_resolutions', ['qec_analysis_data'], 
                    postgresql_using='gin')
    op.create_index('idx_analysis_distances_gin', 'qec_conflict_analysis_logs', ['constitutional_distances'], 
                    postgresql_using='gin')
    op.create_index('idx_analysis_predictions_gin', 'qec_conflict_analysis_logs', ['error_predictions'], 
                    postgresql_using='gin')
    op.create_index('idx_patch_metadata_gin', 'qec_patch_generation_logs', ['patch_metadata'], 
                    postgresql_using='gin')
    op.create_index('idx_fidelity_metadata_gin', 'constitutional_fidelity_history', ['metadata'], 
                    postgresql_using='gin')


def downgrade() -> None:
    """Remove QEC conflict resolution fields and tables."""
    
    # Drop tables in reverse order
    op.drop_table('constitutional_fidelity_alerts')
    op.drop_table('constitutional_fidelity_history')
    op.drop_table('qec_patch_generation_logs')
    op.drop_table('qec_conflict_analysis_logs')
    
    # Drop indexes
    op.drop_index('idx_fidelity_metadata_gin', table_name='constitutional_fidelity_history')
    op.drop_index('idx_patch_metadata_gin', table_name='qec_patch_generation_logs')
    op.drop_index('idx_analysis_predictions_gin', table_name='qec_conflict_analysis_logs')
    op.drop_index('idx_analysis_distances_gin', table_name='qec_conflict_analysis_logs')
    op.drop_index('idx_conflict_qec_analysis_gin', table_name='ac_conflict_resolutions')
    
    op.drop_index('idx_conflict_qec_timestamp', table_name='ac_conflict_resolutions')
    op.drop_index('idx_conflict_qec_enhanced', table_name='ac_conflict_resolutions')
    op.drop_index('idx_conflict_priority_score', table_name='ac_conflict_resolutions')
    
    # Drop columns from ac_conflict_resolutions
    op.drop_column('ac_conflict_resolutions', 'qec_analysis_timestamp')
    op.drop_column('ac_conflict_resolutions', 'qec_enhanced')
    op.drop_column('ac_conflict_resolutions', 'priority_score')
    op.drop_column('ac_conflict_resolutions', 'qec_analysis_data')
