"""Add QEC enhancement fields to constitutional principles

Revision ID: 004_add_qec_enhancement_fields
Revises: 003_add_constitutional_council_schema
Create Date: 2024-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_qec_enhancement_fields'
down_revision = '003_add_constitutional_council_schema'
branch_labels = None
depends_on = None


def upgrade():
    """Add QEC enhancement fields to constitutional_principles table."""
    
    # Add QEC enhancement fields to constitutional_principles table
    op.add_column('constitutional_principles', 
                  sa.Column('validation_criteria_structured', 
                           postgresql.JSONB(astext_type=sa.Text()), 
                           nullable=True,
                           comment='Machine-actionable validation criteria for automated testing'))
    
    op.add_column('constitutional_principles', 
                  sa.Column('distance_score', 
                           sa.Float, 
                           nullable=True,
                           comment='Constitutional robustness metric (0.0-1.0, higher = more robust)'))
    
    op.add_column('constitutional_principles', 
                  sa.Column('score_updated_at', 
                           sa.DateTime(timezone=True), 
                           nullable=True,
                           comment='Timestamp of last distance score calculation'))
    
    op.add_column('constitutional_principles', 
                  sa.Column('error_prediction_metadata', 
                           postgresql.JSONB(astext_type=sa.Text()), 
                           nullable=True,
                           comment='Historical error patterns and predictions for proactive failure detection'))
    
    op.add_column('constitutional_principles', 
                  sa.Column('recovery_strategies', 
                           postgresql.ARRAY(sa.String), 
                           nullable=True,
                           comment='Configured recovery mechanisms for synthesis failures'))
    
    # Create index on distance_score for performance
    op.create_index('idx_constitutional_principles_distance_score', 
                    'constitutional_principles', 
                    ['distance_score'])
    
    # Create index on score_updated_at for performance
    op.create_index('idx_constitutional_principles_score_updated_at', 
                    'constitutional_principles', 
                    ['score_updated_at'])
    
    # Create GIN index on validation_criteria_structured for JSONB queries
    op.create_index('idx_constitutional_principles_validation_criteria_gin', 
                    'constitutional_principles', 
                    ['validation_criteria_structured'], 
                    postgresql_using='gin')
    
    # Create GIN index on error_prediction_metadata for JSONB queries
    op.create_index('idx_constitutional_principles_error_metadata_gin', 
                    'constitutional_principles', 
                    ['error_prediction_metadata'], 
                    postgresql_using='gin')
    
    # Create new table for QEC synthesis attempt logs
    op.create_table('qec_synthesis_attempt_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('attempt_id', sa.String(255), nullable=False, unique=True),
        sa.Column('principle_id', sa.String(255), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('llm_model', sa.String(100), nullable=False),
        sa.Column('prompt_template', sa.String(100), nullable=False),
        sa.Column('failure_type', sa.String(50), nullable=True),
        sa.Column('error_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recovery_strategy', sa.String(100), nullable=True),
        sa.Column('final_outcome', sa.String(50), nullable=False),
        sa.Column('prediction_accuracy', sa.Float, nullable=True),
        sa.Column('synthesis_time_ms', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='QEC synthesis attempt logs for error prediction model training'
    )
    
    # Create indexes for synthesis attempt logs
    op.create_index('idx_qec_synthesis_logs_principle_id', 
                    'qec_synthesis_attempt_logs', 
                    ['principle_id'])
    
    op.create_index('idx_qec_synthesis_logs_timestamp', 
                    'qec_synthesis_attempt_logs', 
                    ['timestamp'])
    
    op.create_index('idx_qec_synthesis_logs_failure_type', 
                    'qec_synthesis_attempt_logs', 
                    ['failure_type'])
    
    op.create_index('idx_qec_synthesis_logs_final_outcome', 
                    'qec_synthesis_attempt_logs', 
                    ['final_outcome'])
    
    # Create GIN index on error_details for JSONB queries
    op.create_index('idx_qec_synthesis_logs_error_details_gin', 
                    'qec_synthesis_attempt_logs', 
                    ['error_details'], 
                    postgresql_using='gin')
    
    # Create new table for QEC constitutional distance calculations
    op.create_table('qec_distance_calculations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('principle_id', sa.String(255), nullable=False),
        sa.Column('calculation_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('distance_score', sa.Float, nullable=False),
        sa.Column('language_ambiguity', sa.Float, nullable=False),
        sa.Column('criteria_formality', sa.Float, nullable=False),
        sa.Column('synthesis_reliability', sa.Float, nullable=False),
        sa.Column('calculation_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('calculator_version', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='QEC constitutional distance calculation history'
    )
    
    # Create indexes for distance calculations
    op.create_index('idx_qec_distance_calc_principle_id', 
                    'qec_distance_calculations', 
                    ['principle_id'])
    
    op.create_index('idx_qec_distance_calc_timestamp', 
                    'qec_distance_calculations', 
                    ['calculation_timestamp'])
    
    op.create_index('idx_qec_distance_calc_score', 
                    'qec_distance_calculations', 
                    ['distance_score'])
    
    # Create new table for QEC error predictions
    op.create_table('qec_error_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('principle_id', sa.String(255), nullable=False),
        sa.Column('prediction_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('overall_risk_score', sa.Float, nullable=False),
        sa.Column('predicted_failures', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('recommended_strategy', sa.String(100), nullable=False),
        sa.Column('confidence', sa.Float, nullable=False),
        sa.Column('prediction_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('model_version', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='QEC error prediction history'
    )
    
    # Create indexes for error predictions
    op.create_index('idx_qec_error_pred_principle_id', 
                    'qec_error_predictions', 
                    ['principle_id'])
    
    op.create_index('idx_qec_error_pred_timestamp', 
                    'qec_error_predictions', 
                    ['prediction_timestamp'])
    
    op.create_index('idx_qec_error_pred_risk_score', 
                    'qec_error_predictions', 
                    ['overall_risk_score'])
    
    op.create_index('idx_qec_error_pred_strategy', 
                    'qec_error_predictions', 
                    ['recommended_strategy'])
    
    # Create GIN index on predicted_failures for JSONB queries
    op.create_index('idx_qec_error_pred_failures_gin', 
                    'qec_error_predictions', 
                    ['predicted_failures'], 
                    postgresql_using='gin')
    
    # Add foreign key constraints
    op.create_foreign_key('fk_qec_synthesis_logs_principle_id',
                         'qec_synthesis_attempt_logs', 'constitutional_principles',
                         ['principle_id'], ['principle_id'],
                         ondelete='CASCADE')
    
    op.create_foreign_key('fk_qec_distance_calc_principle_id',
                         'qec_distance_calculations', 'constitutional_principles',
                         ['principle_id'], ['principle_id'],
                         ondelete='CASCADE')
    
    op.create_foreign_key('fk_qec_error_pred_principle_id',
                         'qec_error_predictions', 'constitutional_principles',
                         ['principle_id'], ['principle_id'],
                         ondelete='CASCADE')


def downgrade():
    """Remove QEC enhancement fields and tables."""
    
    # Drop foreign key constraints
    op.drop_constraint('fk_qec_error_pred_principle_id', 'qec_error_predictions', type_='foreignkey')
    op.drop_constraint('fk_qec_distance_calc_principle_id', 'qec_distance_calculations', type_='foreignkey')
    op.drop_constraint('fk_qec_synthesis_logs_principle_id', 'qec_synthesis_attempt_logs', type_='foreignkey')
    
    # Drop QEC tables
    op.drop_table('qec_error_predictions')
    op.drop_table('qec_distance_calculations')
    op.drop_table('qec_synthesis_attempt_logs')
    
    # Drop indexes from constitutional_principles
    op.drop_index('idx_constitutional_principles_error_metadata_gin', 'constitutional_principles')
    op.drop_index('idx_constitutional_principles_validation_criteria_gin', 'constitutional_principles')
    op.drop_index('idx_constitutional_principles_score_updated_at', 'constitutional_principles')
    op.drop_index('idx_constitutional_principles_distance_score', 'constitutional_principles')
    
    # Remove QEC enhancement columns from constitutional_principles
    op.drop_column('constitutional_principles', 'recovery_strategies')
    op.drop_column('constitutional_principles', 'error_prediction_metadata')
    op.drop_column('constitutional_principles', 'score_updated_at')
    op.drop_column('constitutional_principles', 'distance_score')
    op.drop_column('constitutional_principles', 'validation_criteria_structured')
