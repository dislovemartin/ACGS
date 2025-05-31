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
    # Add missing columns to users table
    try:
        # Check if full_name column exists, if not add it
        op.add_column('users', sa.Column('full_name', sa.String(length=255), nullable=True))
    except Exception:
        # Column might already exist
        pass
    
    try:
        # Check if created_at column exists, if not add it
        op.add_column('users', sa.Column('created_at', sa.DateTime(timezone=True), 
                                       server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False))
    except Exception:
        # Column might already exist
        pass
    
    try:
        # Check if updated_at column exists, if not add it
        op.add_column('users', sa.Column('updated_at', sa.DateTime(timezone=True), 
                                       server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False))
    except Exception:
        # Column might already exist
        pass
    
    # Add missing columns to refresh_tokens table if it exists
    try:
        # Check if jti column exists in refresh_tokens, if not add it
        op.add_column('refresh_tokens', sa.Column('jti', sa.String(length=36), nullable=True))
    except Exception:
        # Column might already exist or table might not exist
        pass
    
    try:
        # Check if is_revoked column exists in refresh_tokens, if not add it
        op.add_column('refresh_tokens', sa.Column('is_revoked', sa.Boolean(), 
                                                server_default=sa.text('false'), nullable=False))
    except Exception:
        # Column might already exist or table might not exist
        pass


def downgrade() -> None:
    # Remove the added columns
    try:
        op.drop_column('users', 'updated_at')
    except Exception:
        pass
    
    try:
        op.drop_column('users', 'created_at')
    except Exception:
        pass
    
    try:
        op.drop_column('users', 'full_name')
    except Exception:
        pass
    
    try:
        op.drop_column('refresh_tokens', 'is_revoked')
    except Exception:
        pass
    
    try:
        op.drop_column('refresh_tokens', 'jti')
    except Exception:
        pass
