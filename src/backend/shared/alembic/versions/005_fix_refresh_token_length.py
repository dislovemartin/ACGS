"""Fix refresh token length

Revision ID: 005_fix_refresh_token_length
Revises: 004_add_missing_user_columns
Create Date: 2025-05-31 04:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_fix_refresh_token_length'
down_revision = '004_add_missing_user_columns'
branch_labels = None
depends_on = None


def upgrade():
    """Increase refresh token column length to accommodate JWT tokens."""
    # Increase token column length from 255 to 1024 characters
    op.alter_column('refresh_tokens', 'token',
                    existing_type=sa.VARCHAR(length=255),
                    type_=sa.VARCHAR(length=1024),
                    existing_nullable=False)


def downgrade():
    """Revert refresh token column length back to 255."""
    op.alter_column('refresh_tokens', 'token',
                    existing_type=sa.VARCHAR(length=1024),
                    type_=sa.VARCHAR(length=255),
                    existing_nullable=False)
