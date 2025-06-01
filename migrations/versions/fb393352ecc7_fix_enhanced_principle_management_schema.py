# ACGS/alembic/script.py.mako
"""fix_enhanced_principle_management_schema

Revision ID: fb393352ecc7
Revises: 005_fix_refresh_token_length
Create Date: 2025-06-01 05:15:34.718145

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb393352ecc7'
down_revision: Union[str, None] = '005_fix_refresh_token_length'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix Enhanced Principle Management schema inconsistencies."""

    # 1. Rename 'title' column to 'name' to match the model
    op.alter_column('principles', 'title', new_column_name='name')

    # 2. Change 'scope' from varchar(100) to JSONB to match the model
    op.alter_column('principles', 'scope',
                   type_=sa.dialects.postgresql.JSONB(),
                   nullable=True,
                   server_default=None)

    # 3. Add missing enhanced principle management fields
    op.add_column('principles', sa.Column('keywords', sa.dialects.postgresql.JSONB(), nullable=True,
                                         comment="JSON array of keywords for principle categorization"))
    op.add_column('principles', sa.Column('category', sa.String(length=100), nullable=True,
                                         comment="Category classification (e.g., Safety, Privacy, Fairness)"))
    op.add_column('principles', sa.Column('validation_criteria_nl', sa.Text(), nullable=True,
                                         comment="Natural language validation criteria for testing"))
    op.add_column('principles', sa.Column('constitutional_metadata', sa.dialects.postgresql.JSONB(), nullable=True,
                                         comment="Metadata for constitutional compliance tracking"))

    # 4. Create indexes for better performance
    op.create_index('ix_principles_name', 'principles', ['name'])
    op.create_index('ix_principles_category', 'principles', ['category'])


def downgrade() -> None:
    """Reverse the Enhanced Principle Management schema fixes."""

    # Drop indexes
    op.drop_index('ix_principles_category', table_name='principles')
    op.drop_index('ix_principles_name', table_name='principles')

    # Remove added columns
    op.drop_column('principles', 'constitutional_metadata')
    op.drop_column('principles', 'validation_criteria_nl')
    op.drop_column('principles', 'category')
    op.drop_column('principles', 'keywords')

    # Revert scope back to varchar(100)
    op.alter_column('principles', 'scope',
                   type_=sa.String(length=100),
                   nullable=False,
                   server_default='general')

    # Rename 'name' back to 'title'
    op.alter_column('principles', 'name', new_column_name='title')
