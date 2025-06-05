"""Add Constitutional Council fields to User model

Revision ID: f1a2b3c4d5e6
Revises: eaa5f6249b99
Create Date: 2025-05-28 04:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'eaa5f6249b99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add Constitutional Council fields to users table
    op.add_column('users', sa.Column('is_constitutional_council_member', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('users', sa.Column('constitutional_council_appointed_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('constitutional_council_term_expires', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove Constitutional Council fields from users table
    op.drop_column('users', 'constitutional_council_term_expires')
    op.drop_column('users', 'constitutional_council_appointed_at')
    op.drop_column('users', 'is_constitutional_council_member')
