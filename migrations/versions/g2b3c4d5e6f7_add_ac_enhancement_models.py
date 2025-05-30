"""Add AC enhancement models for Constitutional Council

Revision ID: g2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2025-05-28 04:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'g2b3c4d5e6f7'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create ac_meta_rules table
    op.create_table('ac_meta_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_type', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rule_definition', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('threshold', sa.String(length=50), nullable=True),
        sa.Column('stakeholder_roles', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('decision_mechanism', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ac_meta_rules_id'), 'ac_meta_rules', ['id'], unique=False)
    op.create_index(op.f('ix_ac_meta_rules_rule_type'), 'ac_meta_rules', ['rule_type'], unique=False)
    op.create_index(op.f('ix_ac_meta_rules_name'), 'ac_meta_rules', ['name'], unique=False)
    op.create_index(op.f('ix_ac_meta_rules_status'), 'ac_meta_rules', ['status'], unique=False)

    # Create ac_amendments table
    op.create_table('ac_amendments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('principle_id', sa.Integer(), nullable=False),
        sa.Column('amendment_type', sa.String(length=50), nullable=False),
        sa.Column('proposed_changes', sa.Text(), nullable=False),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('proposed_content', sa.Text(), nullable=True),
        sa.Column('proposed_status', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='proposed'),
        sa.Column('voting_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('voting_ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('votes_for', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('votes_against', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('votes_abstain', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('required_threshold', sa.String(length=50), nullable=True),
        sa.Column('consultation_period_days', sa.Integer(), nullable=True),
        sa.Column('public_comment_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('stakeholder_groups', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('proposed_by_user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['principle_id'], ['principles.id'], ),
        sa.ForeignKeyConstraint(['proposed_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ac_amendments_id'), 'ac_amendments', ['id'], unique=False)
    op.create_index(op.f('ix_ac_amendments_amendment_type'), 'ac_amendments', ['amendment_type'], unique=False)
    op.create_index(op.f('ix_ac_amendments_status'), 'ac_amendments', ['status'], unique=False)

    # Create ac_amendment_votes table
    op.create_table('ac_amendment_votes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('amendment_id', sa.Integer(), nullable=False),
        sa.Column('voter_id', sa.Integer(), nullable=False),
        sa.Column('vote', sa.String(length=20), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('voted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['amendment_id'], ['ac_amendments.id'], ),
        sa.ForeignKeyConstraint(['voter_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ac_amendment_votes_id'), 'ac_amendment_votes', ['id'], unique=False)
    op.create_index(op.f('ix_ac_amendment_votes_vote'), 'ac_amendment_votes', ['vote'], unique=False)

    # Create ac_amendment_comments table
    op.create_table('ac_amendment_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('amendment_id', sa.Integer(), nullable=False),
        sa.Column('commenter_id', sa.Integer(), nullable=True),
        sa.Column('commenter_name', sa.String(length=255), nullable=True),
        sa.Column('commenter_email', sa.String(length=255), nullable=True),
        sa.Column('stakeholder_group', sa.String(length=100), nullable=True),
        sa.Column('comment_text', sa.Text(), nullable=False),
        sa.Column('sentiment', sa.String(length=20), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_moderated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['amendment_id'], ['ac_amendments.id'], ),
        sa.ForeignKeyConstraint(['commenter_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ac_amendment_comments_id'), 'ac_amendment_comments', ['id'], unique=False)
    op.create_index(op.f('ix_ac_amendment_comments_sentiment'), 'ac_amendment_comments', ['sentiment'], unique=False)

    # Create ac_conflict_resolutions table
    op.create_table('ac_conflict_resolutions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conflict_type', sa.String(length=100), nullable=False),
        sa.Column('principle_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('context', sa.String(length=255), nullable=True),
        sa.Column('conflict_description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('resolution_strategy', sa.String(length=100), nullable=False),
        sa.Column('resolution_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('precedence_order', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='identified'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('identified_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['identified_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ac_conflict_resolutions_id'), 'ac_conflict_resolutions', ['id'], unique=False)
    op.create_index(op.f('ix_ac_conflict_resolutions_conflict_type'), 'ac_conflict_resolutions', ['conflict_type'], unique=False)
    op.create_index(op.f('ix_ac_conflict_resolutions_severity'), 'ac_conflict_resolutions', ['severity'], unique=False)
    op.create_index(op.f('ix_ac_conflict_resolutions_status'), 'ac_conflict_resolutions', ['status'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order
    op.drop_index(op.f('ix_ac_conflict_resolutions_status'), table_name='ac_conflict_resolutions')
    op.drop_index(op.f('ix_ac_conflict_resolutions_severity'), table_name='ac_conflict_resolutions')
    op.drop_index(op.f('ix_ac_conflict_resolutions_conflict_type'), table_name='ac_conflict_resolutions')
    op.drop_index(op.f('ix_ac_conflict_resolutions_id'), table_name='ac_conflict_resolutions')
    op.drop_table('ac_conflict_resolutions')

    op.drop_index(op.f('ix_ac_amendment_comments_sentiment'), table_name='ac_amendment_comments')
    op.drop_index(op.f('ix_ac_amendment_comments_id'), table_name='ac_amendment_comments')
    op.drop_table('ac_amendment_comments')

    op.drop_index(op.f('ix_ac_amendment_votes_vote'), table_name='ac_amendment_votes')
    op.drop_index(op.f('ix_ac_amendment_votes_id'), table_name='ac_amendment_votes')
    op.drop_table('ac_amendment_votes')

    op.drop_index(op.f('ix_ac_amendments_status'), table_name='ac_amendments')
    op.drop_index(op.f('ix_ac_amendments_amendment_type'), table_name='ac_amendments')
    op.drop_index(op.f('ix_ac_amendments_id'), table_name='ac_amendments')
    op.drop_table('ac_amendments')

    op.drop_index(op.f('ix_ac_meta_rules_status'), table_name='ac_meta_rules')
    op.drop_index(op.f('ix_ac_meta_rules_name'), table_name='ac_meta_rules')
    op.drop_index(op.f('ix_ac_meta_rules_rule_type'), table_name='ac_meta_rules')
    op.drop_index(op.f('ix_ac_meta_rules_id'), table_name='ac_meta_rules')
    op.drop_table('ac_meta_rules')
