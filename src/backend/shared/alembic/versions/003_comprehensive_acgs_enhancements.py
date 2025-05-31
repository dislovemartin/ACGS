"""Comprehensive ACGS enhancements for Phase 1-3

Revision ID: 003_acgs_enhancements
Revises: f1a2b3c4d5e6
Create Date: 2025-01-15 10:00:00.000000

Includes:
- Phase 1: Enhanced Principle Management, Constitutional Council, Meta-Rules
- Phase 2: AlphaEvolve integration models
- Phase 3: Cryptographic integrity and formal verification
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_acgs_enhancements'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with comprehensive ACGS enhancements."""
    
    # ===== PHASE 1 ENHANCEMENTS =====
    
    # Add enhanced fields to principles table
    op.add_column('principles', sa.Column('priority_weight', sa.Float(), nullable=False, server_default='1.0'))
    op.add_column('principles', sa.Column('scope', sa.String(length=100), nullable=False, server_default='general'))
    op.add_column('principles', sa.Column('normative_statement', sa.Text(), nullable=True))
    op.add_column('principles', sa.Column('constraints', sa.JSON(), nullable=True))
    op.add_column('principles', sa.Column('rationale', sa.Text(), nullable=True))
    
    # Add enhanced fields to policy_rules table
    op.add_column('policy_rules', sa.Column('framework', sa.String(length=50), nullable=False, server_default='rego'))
    op.add_column('policy_rules', sa.Column('hash_sha256', sa.String(length=64), nullable=True))
    op.add_column('policy_rules', sa.Column('pgp_signature', sa.Text(), nullable=True))
    op.add_column('policy_rules', sa.Column('signature_timestamp', sa.DateTime(), nullable=True))
    
    # Create meta_rules table
    op.create_table('meta_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('condition', sa.Text(), nullable=False),
        sa.Column('resolution_strategy', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_meta_rules_id'), 'meta_rules', ['id'], unique=False)
    op.create_index(op.f('ix_meta_rules_priority'), 'meta_rules', ['priority'], unique=False)
    
    # Create conflict_resolutions table
    op.create_table('conflict_resolutions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conflict_type', sa.String(length=100), nullable=False),
        sa.Column('principle_ids', sa.JSON(), nullable=False),
        sa.Column('resolution', sa.Text(), nullable=False),
        sa.Column('meta_rule_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('resolved_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['meta_rule_id'], ['meta_rules.id'], ),
        sa.ForeignKeyConstraint(['resolved_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conflict_resolutions_id'), 'conflict_resolutions', ['id'], unique=False)
    
    # Create amendment_proposals table
    op.create_table('amendment_proposals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('proposed_changes', sa.Text(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='proposed'),
        sa.Column('voting_deadline', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('proposed_by_user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['proposed_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_amendment_proposals_id'), 'amendment_proposals', ['id'], unique=False)
    op.create_index(op.f('ix_amendment_proposals_status'), 'amendment_proposals', ['status'], unique=False)
    
    # Create amendment_votes table
    op.create_table('amendment_votes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('amendment_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('vote', sa.String(length=20), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['amendment_id'], ['amendment_proposals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('amendment_id', 'user_id', name='unique_vote_per_amendment')
    )
    op.create_index(op.f('ix_amendment_votes_id'), 'amendment_votes', ['id'], unique=False)
    
    # Create amendment_comments table
    op.create_table('amendment_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('amendment_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['amendment_id'], ['amendment_proposals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_amendment_comments_id'), 'amendment_comments', ['id'], unique=False)
    
    # Create environmental_factors table
    op.create_table('environmental_factors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('factor_type', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('value', sa.JSON(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_environmental_factors_id'), 'environmental_factors', ['id'], unique=False)
    op.create_index(op.f('ix_environmental_factors_factor_type'), 'environmental_factors', ['factor_type'], unique=False)

    # ===== POLICY TEMPLATES AND POLICIES TABLES =====

    # Create policy_templates table
    op.create_table('policy_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('default_content', sa.Text(), nullable=False),
        sa.Column('parameters_schema', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_policy_templates_id'), 'policy_templates', ['id'], unique=False)

    # Create policies table
    op.create_table('policies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('status', sa.String(), nullable=False, server_default='draft'),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('customization_parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('previous_version_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['previous_version_id'], ['policies.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['policy_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_policies_id'), 'policies', ['id'], unique=False)
    op.create_index(op.f('ix_policies_name'), 'policies', ['name'], unique=False)
    op.create_index(op.f('ix_policies_status'), 'policies', ['status'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order

    # Drop policies and policy_templates tables
    op.drop_index(op.f('ix_policies_status'), table_name='policies')
    op.drop_index(op.f('ix_policies_name'), table_name='policies')
    op.drop_index(op.f('ix_policies_id'), table_name='policies')
    op.drop_table('policies')
    op.drop_index(op.f('ix_policy_templates_id'), table_name='policy_templates')
    op.drop_table('policy_templates')

    op.drop_index(op.f('ix_environmental_factors_factor_type'), table_name='environmental_factors')
    op.drop_index(op.f('ix_environmental_factors_id'), table_name='environmental_factors')
    op.drop_table('environmental_factors')
    
    op.drop_index(op.f('ix_amendment_comments_id'), table_name='amendment_comments')
    op.drop_table('amendment_comments')
    
    op.drop_index(op.f('ix_amendment_votes_id'), table_name='amendment_votes')
    op.drop_table('amendment_votes')
    
    op.drop_index(op.f('ix_amendment_proposals_status'), table_name='amendment_proposals')
    op.drop_index(op.f('ix_amendment_proposals_id'), table_name='amendment_proposals')
    op.drop_table('amendment_proposals')
    
    op.drop_index(op.f('ix_conflict_resolutions_id'), table_name='conflict_resolutions')
    op.drop_table('conflict_resolutions')
    
    op.drop_index(op.f('ix_meta_rules_priority'), table_name='meta_rules')
    op.drop_index(op.f('ix_meta_rules_id'), table_name='meta_rules')
    op.drop_table('meta_rules')
    
    # Remove enhanced fields from policy_rules
    op.drop_column('policy_rules', 'signature_timestamp')
    op.drop_column('policy_rules', 'pgp_signature')
    op.drop_column('policy_rules', 'hash_sha256')
    op.drop_column('policy_rules', 'framework')
    
    # Remove enhanced fields from principles
    op.drop_column('principles', 'rationale')
    op.drop_column('principles', 'constraints')
    op.drop_column('principles', 'normative_statement')
    op.drop_column('principles', 'scope')
    op.drop_column('principles', 'priority_weight')
