"""Add violation detection tables

Revision ID: add_violation_detection_tables
Revises: previous_revision
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_violation_detection_tables'
down_revision = None  # Update this with the actual previous revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add violation detection tables."""
    
    # Create constitutional_violations table
    op.create_table(
        'constitutional_violations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('violation_type', sa.String(100), nullable=False, index=True),
        sa.Column('severity', sa.String(20), nullable=False, index=True),
        sa.Column('principle_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('violation_description', sa.Text, nullable=False),
        sa.Column('detection_method', sa.String(100), nullable=False),
        sa.Column('fidelity_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('distance_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('context_data', postgresql.JSONB, nullable=True),
        sa.Column('detection_metadata', postgresql.JSONB, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='detected', index=True),
        sa.Column('resolution_status', sa.String(50), nullable=True),
        sa.Column('resolution_description', sa.Text, nullable=True),
        sa.Column('escalated', sa.Boolean, nullable=False, default=False, index=True),
        sa.Column('escalation_level', sa.String(50), nullable=True),
        sa.Column('escalated_at', sa.DateTime, nullable=True),
        sa.Column('escalated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('detected_at', sa.DateTime, nullable=False, default=sa.func.now(), index=True),
        sa.Column('detected_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime, nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['principle_id'], ['constitutional_principles.id']),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id']),
        sa.ForeignKeyConstraint(['escalated_by'], ['users.id']),
        sa.ForeignKeyConstraint(['detected_by'], ['users.id']),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id']),
    )
    
    # Create indexes for performance
    op.create_index('idx_violation_type_severity', 'constitutional_violations', ['violation_type', 'severity'])
    op.create_index('idx_violation_status_detected', 'constitutional_violations', ['status', 'detected_at'])
    op.create_index('idx_violation_escalated', 'constitutional_violations', ['escalated', 'escalation_level'])
    op.create_index('idx_violation_principle_policy', 'constitutional_violations', ['principle_id', 'policy_id'])
    
    # Create violation_alerts table
    op.create_table(
        'violation_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('violation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alert_type', sa.String(50), nullable=False, index=True),
        sa.Column('alert_level', sa.String(20), nullable=False, index=True),
        sa.Column('threshold_value', sa.Numeric(5, 4), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('recommended_actions', postgresql.JSONB, nullable=True),
        sa.Column('notification_channels', postgresql.JSONB, nullable=True),
        sa.Column('notification_status', sa.String(50), nullable=False, default='pending'),
        sa.Column('notification_attempts', sa.Integer, nullable=False, default=0),
        sa.Column('last_notification_attempt', sa.DateTime, nullable=True),
        sa.Column('acknowledged', sa.Boolean, nullable=False, default=False),
        sa.Column('acknowledged_at', sa.DateTime, nullable=True),
        sa.Column('acknowledged_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('response_actions', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['violation_id'], ['constitutional_violations.id']),
        sa.ForeignKeyConstraint(['acknowledged_by'], ['users.id']),
    )
    
    # Create indexes for violation_alerts
    op.create_index('idx_alert_type_level', 'violation_alerts', ['alert_type', 'alert_level'])
    op.create_index('idx_alert_status_created', 'violation_alerts', ['notification_status', 'created_at'])
    op.create_index('idx_alert_acknowledged', 'violation_alerts', ['acknowledged', 'acknowledged_at'])
    
    # Create violation_thresholds table
    op.create_table(
        'violation_thresholds',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('threshold_name', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('threshold_type', sa.String(50), nullable=False, index=True),
        sa.Column('green_threshold', sa.Numeric(5, 4), nullable=False),
        sa.Column('amber_threshold', sa.Numeric(5, 4), nullable=False),
        sa.Column('red_threshold', sa.Numeric(5, 4), nullable=False),
        sa.Column('enabled', sa.Boolean, nullable=False, default=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('configuration', postgresql.JSONB, nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id']),
    )
    
    # Create violation_escalations table
    op.create_table(
        'violation_escalations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('violation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('escalation_type', sa.String(50), nullable=False, index=True),
        sa.Column('escalation_level', sa.String(50), nullable=False, index=True),
        sa.Column('escalation_reason', sa.Text, nullable=False),
        sa.Column('trigger_conditions', postgresql.JSONB, nullable=True),
        sa.Column('escalation_rules', postgresql.JSONB, nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_role', sa.String(50), nullable=True),
        sa.Column('notification_sent', sa.Boolean, nullable=False, default=False),
        sa.Column('notification_channels', postgresql.JSONB, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='pending', index=True),
        sa.Column('response_time_seconds', sa.Integer, nullable=True),
        sa.Column('resolution_time_seconds', sa.Integer, nullable=True),
        sa.Column('response_actions', postgresql.JSONB, nullable=True),
        sa.Column('resolution_summary', sa.Text, nullable=True),
        sa.Column('escalated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('escalated_at', sa.DateTime, nullable=False, default=sa.func.now(), index=True),
        sa.Column('responded_at', sa.DateTime, nullable=True),
        sa.Column('resolved_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['violation_id'], ['constitutional_violations.id']),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id']),
        sa.ForeignKeyConstraint(['escalated_by'], ['users.id']),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id']),
    )
    
    # Create indexes for violation_escalations
    op.create_index('idx_escalation_type_level', 'violation_escalations', ['escalation_type', 'escalation_level'])
    op.create_index('idx_escalation_status_escalated', 'violation_escalations', ['status', 'escalated_at'])
    op.create_index('idx_escalation_assigned', 'violation_escalations', ['assigned_to', 'assigned_role'])
    
    # Insert default violation thresholds
    op.execute("""
        INSERT INTO violation_thresholds (id, threshold_name, threshold_type, green_threshold, amber_threshold, red_threshold, enabled, description, configuration)
        VALUES 
        (gen_random_uuid(), 'fidelity_score', 'fidelity_score', 0.85, 0.70, 0.55, true, 'Default constitutional fidelity score thresholds', '{}'),
        (gen_random_uuid(), 'violation_count', 'violation_count', 2.0, 5.0, 10.0, true, 'Default violation count thresholds per hour', '{"time_window_hours": 1}'),
        (gen_random_uuid(), 'severity_critical', 'severity_based', 0.0, 1.0, 3.0, true, 'Critical severity violation thresholds', '{"severity_level": "critical", "time_window_hours": 24}'),
        (gen_random_uuid(), 'resolution_time', 'time_based', 15.0, 30.0, 60.0, true, 'Violation resolution time thresholds', '{"unit": "minutes"}')
    """)


def downgrade() -> None:
    """Remove violation detection tables."""
    
    # Drop indexes first
    op.drop_index('idx_escalation_assigned', 'violation_escalations')
    op.drop_index('idx_escalation_status_escalated', 'violation_escalations')
    op.drop_index('idx_escalation_type_level', 'violation_escalations')
    
    op.drop_index('idx_alert_acknowledged', 'violation_alerts')
    op.drop_index('idx_alert_status_created', 'violation_alerts')
    op.drop_index('idx_alert_type_level', 'violation_alerts')
    
    op.drop_index('idx_violation_principle_policy', 'constitutional_violations')
    op.drop_index('idx_violation_escalated', 'constitutional_violations')
    op.drop_index('idx_violation_status_detected', 'constitutional_violations')
    op.drop_index('idx_violation_type_severity', 'constitutional_violations')
    
    # Drop tables
    op.drop_table('violation_escalations')
    op.drop_table('violation_thresholds')
    op.drop_table('violation_alerts')
    op.drop_table('constitutional_violations')
