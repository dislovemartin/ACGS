"""Enhance policy rules for audit findings

Revision ID: 004_enhance_policy_rules_for_audit_findings
Revises: 003_add_constitutional_council_tables
Create Date: 2024-01-15 10:00:00.000000

Addresses audit findings:
- Add PGP signature fields for integrity verification
- Add framework field for policy format tracking
- Add principle_text field for human-readable descriptions
- Add source_file field for provenance tracking
- Add content_hash field for integrity checking
- Add import_dependencies field for dependency tracking
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_enhance_policy_rules_for_audit_findings'
down_revision = '003_add_constitutional_council_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add enhanced fields to policy_rules table for audit compliance"""
    
    # Add new columns to policy_rules table in integrity_service
    op.add_column('policy_rules', sa.Column('framework', sa.String(length=50), nullable=True, default='Datalog'))
    op.add_column('policy_rules', sa.Column('principle_text', sa.Text, nullable=True))
    op.add_column('policy_rules', sa.Column('pgp_signature', sa.Text, nullable=True))
    op.add_column('policy_rules', sa.Column('source_file', sa.String(length=500), nullable=True))
    op.add_column('policy_rules', sa.Column('content_hash', sa.String(length=128), nullable=True))
    op.add_column('policy_rules', sa.Column('import_dependencies', postgresql.ARRAY(sa.String), nullable=True))
    
    # Add indexes for performance
    op.create_index('idx_policy_rules_framework', 'policy_rules', ['framework'])
    op.create_index('idx_policy_rules_content_hash', 'policy_rules', ['content_hash'])
    op.create_index('idx_policy_rules_source_file', 'policy_rules', ['source_file'])
    
    # Update existing records with default values
    op.execute("""
        UPDATE policy_rules 
        SET framework = 'Datalog' 
        WHERE framework IS NULL
    """)
    
    # Generate content hashes for existing rules
    op.execute("""
        UPDATE policy_rules 
        SET content_hash = encode(digest(rule_content, 'sha256'), 'hex')
        WHERE content_hash IS NULL
    """)
    
    # Try to extract principle_text from rule comments for existing rules
    op.execute("""
        UPDATE policy_rules 
        SET principle_text = (
            SELECT substring(rule_content FROM '#\s*(.+)')
            WHERE principle_text IS NULL 
            AND rule_content ~ '#\s*.+'
        )
        WHERE principle_text IS NULL
    """)
    
    # Set default principle_text for rules without comments
    op.execute("""
        UPDATE policy_rules 
        SET principle_text = 'Policy rule: ' || COALESCE(rule_name, 'Rule ID ' || id::text)
        WHERE principle_text IS NULL
    """)


def downgrade() -> None:
    """Remove enhanced fields from policy_rules table"""
    
    # Drop indexes
    op.drop_index('idx_policy_rules_source_file', table_name='policy_rules')
    op.drop_index('idx_policy_rules_content_hash', table_name='policy_rules')
    op.drop_index('idx_policy_rules_framework', table_name='policy_rules')
    
    # Drop columns
    op.drop_column('policy_rules', 'import_dependencies')
    op.drop_column('policy_rules', 'content_hash')
    op.drop_column('policy_rules', 'source_file')
    op.drop_column('policy_rules', 'pgp_signature')
    op.drop_column('policy_rules', 'principle_text')
    op.drop_column('policy_rules', 'framework')
