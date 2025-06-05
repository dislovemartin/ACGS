"""add missing user columns

Revision ID: 004_add_missing_user_columns
Revises: 003_comprehensive_acgs_enhancements
Create Date: 2024-12-30 23:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_missing_user_columns'
down_revision = 'c2a48966'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Get connection to check for existing columns
    conn = op.get_bind()

    # Check if columns exist before adding them
    inspector = sa.inspect(conn)

    # Check users table columns
    users_columns = [col['name'] for col in inspector.get_columns('users')]

    if 'full_name' not in users_columns:
        op.add_column('users', sa.Column('full_name', sa.String(length=255), nullable=True))

    if 'created_at' not in users_columns:
        op.add_column('users', sa.Column('created_at', sa.DateTime(timezone=True),
                                       server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False))

    if 'updated_at' not in users_columns:
        op.add_column('users', sa.Column('updated_at', sa.DateTime(timezone=True),
                                       server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False))

    # Check if refresh_tokens table exists
    table_names = inspector.get_table_names()
    if 'refresh_tokens' in table_names:
        refresh_tokens_columns = [col['name'] for col in inspector.get_columns('refresh_tokens')]

        if 'jti' not in refresh_tokens_columns:
            op.add_column('refresh_tokens', sa.Column('jti', sa.String(length=36), nullable=True))

        if 'is_revoked' not in refresh_tokens_columns:
            op.add_column('refresh_tokens', sa.Column('is_revoked', sa.Boolean(),
                                                    server_default=sa.text('false'), nullable=False))


def downgrade() -> None:
    # Get connection to check for existing columns
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Check users table columns
    users_columns = [col['name'] for col in inspector.get_columns('users')]

    if 'updated_at' in users_columns:
        op.drop_column('users', 'updated_at')

    if 'created_at' in users_columns:
        op.drop_column('users', 'created_at')

    if 'full_name' in users_columns:
        op.drop_column('users', 'full_name')

    # Check if refresh_tokens table exists
    table_names = inspector.get_table_names()
    if 'refresh_tokens' in table_names:
        refresh_tokens_columns = [col['name'] for col in inspector.get_columns('refresh_tokens')]

        if 'is_revoked' in refresh_tokens_columns:
            op.drop_column('refresh_tokens', 'is_revoked')

        if 'jti' in refresh_tokens_columns:
            op.drop_column('refresh_tokens', 'jti')
