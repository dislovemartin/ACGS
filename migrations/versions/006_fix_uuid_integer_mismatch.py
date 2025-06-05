"""Fix UUID/INTEGER datatype mismatch for users and refresh_tokens

Revision ID: 006_fix_uuid_integer_mismatch
Revises: 005_fix_refresh_token_length
Create Date: 2025-06-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '006_fix_uuid_integer_mismatch'
down_revision = '005_fix_refresh_token_length'
branch_labels = None
depends_on = None


def upgrade():
    """Convert users.id and refresh_tokens.user_id to UUID type."""
    
    # Enable UUID extension if not already enabled
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Step 1: Add a temporary UUID column to users table
    op.add_column('users', sa.Column('id_uuid', UUID(as_uuid=True), nullable=True))
    
    # Step 2: Populate the UUID column with generated UUIDs for existing users
    op.execute("""
        UPDATE users 
        SET id_uuid = uuid_generate_v4() 
        WHERE id_uuid IS NULL
    """)
    
    # Step 3: Add a temporary UUID column to refresh_tokens table
    op.add_column('refresh_tokens', sa.Column('user_id_uuid', UUID(as_uuid=True), nullable=True))
    
    # Step 4: Map existing refresh_tokens to the new UUID values
    op.execute("""
        UPDATE refresh_tokens 
        SET user_id_uuid = users.id_uuid 
        FROM users 
        WHERE refresh_tokens.user_id = users.id
    """)
    
    # Step 5: Drop the foreign key constraint on refresh_tokens.user_id
    op.drop_constraint('refresh_tokens_user_id_fkey', 'refresh_tokens', type_='foreignkey')
    
    # Step 6: Drop the old integer columns
    op.drop_column('refresh_tokens', 'user_id')
    op.drop_column('users', 'id')
    
    # Step 7: Rename the UUID columns to the original names
    op.alter_column('users', 'id_uuid', new_column_name='id')
    op.alter_column('refresh_tokens', 'user_id_uuid', new_column_name='user_id')
    
    # Step 8: Make the UUID columns NOT NULL and set as primary key
    op.alter_column('users', 'id', nullable=False)
    op.alter_column('refresh_tokens', 'user_id', nullable=False)
    
    # Step 9: Add primary key constraint back to users.id
    op.create_primary_key('users_pkey', 'users', ['id'])
    
    # Step 10: Recreate the foreign key constraint with UUID types
    op.create_foreign_key(
        'refresh_tokens_user_id_fkey', 
        'refresh_tokens', 
        'users', 
        ['user_id'], 
        ['id'], 
        ondelete='CASCADE'
    )
    
    # Step 11: Recreate indexes that were dropped
    op.create_index('ix_users_id', 'users', ['id'], unique=False)


def downgrade():
    """Revert UUID columns back to INTEGER type."""
    
    # This is a destructive operation - UUIDs cannot be cleanly converted back to integers
    # We'll create new integer IDs but this will break existing relationships
    
    # Step 1: Drop foreign key constraint
    op.drop_constraint('refresh_tokens_user_id_fkey', 'refresh_tokens', type_='foreignkey')
    
    # Step 2: Drop primary key constraint
    op.drop_constraint('users_pkey', 'users', type_='primary')
    
    # Step 3: Add temporary integer columns
    op.add_column('users', sa.Column('id_int', sa.Integer(), nullable=True))
    op.add_column('refresh_tokens', sa.Column('user_id_int', sa.Integer(), nullable=True))
    
    # Step 4: Generate new integer IDs (this will break existing relationships)
    op.execute("""
        UPDATE users 
        SET id_int = row_number() OVER (ORDER BY created_at)
    """)
    
    # Step 5: Map refresh_tokens to new integer IDs
    op.execute("""
        UPDATE refresh_tokens 
        SET user_id_int = users.id_int 
        FROM users 
        WHERE refresh_tokens.user_id = users.id
    """)
    
    # Step 6: Drop UUID columns
    op.drop_column('refresh_tokens', 'user_id')
    op.drop_column('users', 'id')
    
    # Step 7: Rename integer columns
    op.alter_column('users', 'id_int', new_column_name='id')
    op.alter_column('refresh_tokens', 'user_id_int', new_column_name='user_id')
    
    # Step 8: Set constraints
    op.alter_column('users', 'id', nullable=False)
    op.alter_column('refresh_tokens', 'user_id', nullable=False)
    
    # Step 9: Recreate primary key and foreign key
    op.create_primary_key('users_pkey', 'users', ['id'])
    op.create_foreign_key(
        'refresh_tokens_user_id_fkey', 
        'refresh_tokens', 
        'users', 
        ['user_id'], 
        ['id'], 
        ondelete='CASCADE'
    )
    
    # Step 10: Recreate indexes
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
