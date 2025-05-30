"""Add cryptographic integrity models for Phase 3 PGP Assurance

Revision ID: i4j5k6l7m8n9
Revises: g2b3c4d5e6f7
Create Date: 2024-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'i4j5k6l7m8n9'
down_revision = 'g2b3c4d5e6f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema to add Phase 3 cryptographic integrity models."""
    
    # Add cryptographic integrity fields to policy_rules table
    with op.batch_alter_table('policy_rules', schema=None) as batch_op:
        # Enhanced cryptographic integrity fields
        batch_op.add_column(sa.Column('digital_signature', sa.LargeBinary(), nullable=True,
                                     comment='Digital signature of the rule (binary format)'))
        batch_op.add_column(sa.Column('signature_algorithm', sa.String(50), nullable=True, 
                                     server_default='RSA-PSS-SHA256',
                                     comment='Signature algorithm used'))
        batch_op.add_column(sa.Column('signed_by_key_id', sa.String(64), nullable=True,
                                     comment='Key ID used for signing'))
        batch_op.add_column(sa.Column('signed_at', sa.DateTime(), nullable=True,
                                     comment='When the rule was signed'))
        batch_op.add_column(sa.Column('signature_verified', sa.Boolean(), nullable=False, 
                                     server_default=sa.text('false'),
                                     comment='Signature verification status'))
        batch_op.add_column(sa.Column('merkle_root', sa.String(64), nullable=True,
                                     comment='Merkle tree root for batch verification'))
        batch_op.add_column(sa.Column('rfc3161_timestamp', sa.LargeBinary(), nullable=True,
                                     comment='RFC 3161 timestamp token'))
        
        # Create indexes for cryptographic fields
        batch_op.create_index('ix_policy_rules_signed_by_key_id', ['signed_by_key_id'])
        batch_op.create_index('ix_policy_rules_signature_verified', ['signature_verified'])
    
    # Add cryptographic integrity fields to audit_logs table
    with op.batch_alter_table('audit_logs', schema=None) as batch_op:
        # Enhanced cryptographic integrity fields
        batch_op.add_column(sa.Column('entry_hash', sa.String(64), nullable=True,
                                     comment='SHA3-256 hash of log entry'))
        batch_op.add_column(sa.Column('digital_signature', sa.LargeBinary(), nullable=True,
                                     comment='Digital signature of the log entry'))
        batch_op.add_column(sa.Column('signature_algorithm', sa.String(50), nullable=True,
                                     server_default='RSA-PSS-SHA256',
                                     comment='Signature algorithm used'))
        batch_op.add_column(sa.Column('signed_by_key_id', sa.String(64), nullable=True,
                                     comment='Key ID used for signing'))
        batch_op.add_column(sa.Column('signed_at', sa.DateTime(), nullable=True,
                                     comment='When the log was signed'))
        batch_op.add_column(sa.Column('signature_verified', sa.Boolean(), nullable=False,
                                     server_default=sa.text('false'),
                                     comment='Signature verification status'))
        batch_op.add_column(sa.Column('previous_hash', sa.String(64), nullable=True,
                                     comment='Hash of previous log entry (for chain integrity)'))
        batch_op.add_column(sa.Column('merkle_root', sa.String(64), nullable=True,
                                     comment='Merkle tree root for batch verification'))
        batch_op.add_column(sa.Column('rfc3161_timestamp', sa.LargeBinary(), nullable=True,
                                     comment='RFC 3161 timestamp token'))
        
        # Create indexes for cryptographic fields
        batch_op.create_index('ix_audit_logs_entry_hash', ['entry_hash'])
        batch_op.create_index('ix_audit_logs_signed_by_key_id', ['signed_by_key_id'])
        batch_op.create_index('ix_audit_logs_previous_hash', ['previous_hash'])
    
    # Create crypto_keys table for key management
    op.create_table('crypto_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key_id', sa.String(64), nullable=False, comment='Unique key identifier'),
        sa.Column('key_type', sa.String(20), nullable=False, comment='Key type (RSA, ECDSA, Ed25519)'),
        sa.Column('key_size', sa.Integer(), nullable=False, comment='Key size in bits'),
        sa.Column('public_key_pem', sa.Text(), nullable=False, comment='PEM-encoded public key'),
        sa.Column('private_key_encrypted', sa.LargeBinary(), nullable=True, comment='Encrypted private key'),
        sa.Column('key_purpose', sa.String(50), nullable=False, comment='Key purpose (signing, encryption, timestamping)'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true'), comment='Whether key is active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=True, comment='Key expiration date'),
        sa.Column('revoked_at', sa.DateTime(), nullable=True, comment='Key revocation date'),
        sa.Column('hsm_key_reference', sa.String(255), nullable=True, comment='HSM key reference'),
        sa.Column('parent_key_id', sa.String(64), nullable=True, comment='Previous key in rotation chain'),
        sa.Column('rotation_reason', sa.String(100), nullable=True, comment='Reason for key rotation'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_id')
    )
    
    # Create indexes for crypto_keys
    op.create_index('ix_crypto_keys_id', 'crypto_keys', ['id'])
    op.create_index('ix_crypto_keys_key_id', 'crypto_keys', ['key_id'], unique=True)
    op.create_index('ix_crypto_keys_key_type', 'crypto_keys', ['key_type'])
    op.create_index('ix_crypto_keys_key_purpose', 'crypto_keys', ['key_purpose'])
    op.create_index('ix_crypto_keys_is_active', 'crypto_keys', ['is_active'])
    op.create_index('ix_crypto_keys_parent_key_id', 'crypto_keys', ['parent_key_id'])
    
    # Create merkle_tree_nodes table for batch verification
    op.create_table('merkle_tree_nodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('node_hash', sa.String(64), nullable=False, comment='SHA3-256 hash of the node'),
        sa.Column('parent_hash', sa.String(64), nullable=True, comment='Parent node hash'),
        sa.Column('left_child_hash', sa.String(64), nullable=True, comment='Left child hash'),
        sa.Column('right_child_hash', sa.String(64), nullable=True, comment='Right child hash'),
        sa.Column('level', sa.Integer(), nullable=False, comment='Tree level (0 = leaf)'),
        sa.Column('batch_id', sa.String(64), nullable=False, comment='Batch identifier'),
        sa.Column('audit_log_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Audit log IDs for leaf nodes'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for merkle_tree_nodes
    op.create_index('ix_merkle_tree_nodes_id', 'merkle_tree_nodes', ['id'])
    op.create_index('ix_merkle_tree_nodes_node_hash', 'merkle_tree_nodes', ['node_hash'])
    op.create_index('ix_merkle_tree_nodes_parent_hash', 'merkle_tree_nodes', ['parent_hash'])
    op.create_index('ix_merkle_tree_nodes_level', 'merkle_tree_nodes', ['level'])
    op.create_index('ix_merkle_tree_nodes_batch_id', 'merkle_tree_nodes', ['batch_id'])
    
    # Create timestamp_tokens table for RFC 3161 timestamping
    op.create_table('timestamp_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False, comment='SHA3-256 hash of the token'),
        sa.Column('timestamp_token', sa.LargeBinary(), nullable=False, comment='RFC 3161 timestamp token'),
        sa.Column('tsa_url', sa.String(255), nullable=False, comment='Timestamp Authority URL'),
        sa.Column('timestamp_value', sa.DateTime(), nullable=False, comment='Extracted timestamp value'),
        sa.Column('policy_oid', sa.String(100), nullable=True, comment='TSA policy OID'),
        sa.Column('hash_algorithm', sa.String(50), nullable=False, comment='Hash algorithm used'),
        sa.Column('message_imprint', sa.LargeBinary(), nullable=False, comment='Original message hash'),
        sa.Column('serial_number', sa.String(100), nullable=True, comment='TSA serial number'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash')
    )
    
    # Create indexes for timestamp_tokens
    op.create_index('ix_timestamp_tokens_id', 'timestamp_tokens', ['id'])
    op.create_index('ix_timestamp_tokens_token_hash', 'timestamp_tokens', ['token_hash'], unique=True)
    op.create_index('ix_timestamp_tokens_timestamp_value', 'timestamp_tokens', ['timestamp_value'])
    op.create_index('ix_timestamp_tokens_tsa_url', 'timestamp_tokens', ['tsa_url'])
    
    # Create composite indexes for cryptographic integrity
    op.create_index('ix_crypto_key_purpose_active', 'crypto_keys', ['key_purpose', 'is_active'])
    op.create_index('ix_crypto_key_type_created', 'crypto_keys', ['key_type', 'created_at'])
    op.create_index('ix_merkle_node_batch_level', 'merkle_tree_nodes', ['batch_id', 'level'])
    op.create_index('ix_timestamp_token_tsa_time', 'timestamp_tokens', ['tsa_url', 'timestamp_value'])
    op.create_index('ix_audit_log_hash_chain', 'audit_logs', ['entry_hash', 'previous_hash'])
    op.create_index('ix_policy_rule_signature_key', 'policy_rules', ['signed_by_key_id', 'signature_verified'])


def downgrade() -> None:
    """Downgrade schema to remove Phase 3 cryptographic integrity models."""
    
    # Drop composite indexes
    op.drop_index('ix_policy_rule_signature_key', table_name='policy_rules')
    op.drop_index('ix_audit_log_hash_chain', table_name='audit_logs')
    op.drop_index('ix_timestamp_token_tsa_time', table_name='timestamp_tokens')
    op.drop_index('ix_merkle_node_batch_level', table_name='merkle_tree_nodes')
    op.drop_index('ix_crypto_key_type_created', table_name='crypto_keys')
    op.drop_index('ix_crypto_key_purpose_active', table_name='crypto_keys')
    
    # Drop timestamp_tokens table
    op.drop_index('ix_timestamp_tokens_tsa_url', table_name='timestamp_tokens')
    op.drop_index('ix_timestamp_tokens_timestamp_value', table_name='timestamp_tokens')
    op.drop_index('ix_timestamp_tokens_token_hash', table_name='timestamp_tokens')
    op.drop_index('ix_timestamp_tokens_id', table_name='timestamp_tokens')
    op.drop_table('timestamp_tokens')
    
    # Drop merkle_tree_nodes table
    op.drop_index('ix_merkle_tree_nodes_batch_id', table_name='merkle_tree_nodes')
    op.drop_index('ix_merkle_tree_nodes_level', table_name='merkle_tree_nodes')
    op.drop_index('ix_merkle_tree_nodes_parent_hash', table_name='merkle_tree_nodes')
    op.drop_index('ix_merkle_tree_nodes_node_hash', table_name='merkle_tree_nodes')
    op.drop_index('ix_merkle_tree_nodes_id', table_name='merkle_tree_nodes')
    op.drop_table('merkle_tree_nodes')
    
    # Drop crypto_keys table
    op.drop_index('ix_crypto_keys_parent_key_id', table_name='crypto_keys')
    op.drop_index('ix_crypto_keys_is_active', table_name='crypto_keys')
    op.drop_index('ix_crypto_keys_key_purpose', table_name='crypto_keys')
    op.drop_index('ix_crypto_keys_key_type', table_name='crypto_keys')
    op.drop_index('ix_crypto_keys_key_id', table_name='crypto_keys')
    op.drop_index('ix_crypto_keys_id', table_name='crypto_keys')
    op.drop_table('crypto_keys')
    
    # Remove cryptographic integrity fields from audit_logs table
    with op.batch_alter_table('audit_logs', schema=None) as batch_op:
        batch_op.drop_index('ix_audit_logs_previous_hash')
        batch_op.drop_index('ix_audit_logs_signed_by_key_id')
        batch_op.drop_index('ix_audit_logs_entry_hash')
        
        batch_op.drop_column('rfc3161_timestamp')
        batch_op.drop_column('merkle_root')
        batch_op.drop_column('previous_hash')
        batch_op.drop_column('signature_verified')
        batch_op.drop_column('signed_at')
        batch_op.drop_column('signed_by_key_id')
        batch_op.drop_column('signature_algorithm')
        batch_op.drop_column('digital_signature')
        batch_op.drop_column('entry_hash')
    
    # Remove cryptographic integrity fields from policy_rules table
    with op.batch_alter_table('policy_rules', schema=None) as batch_op:
        batch_op.drop_index('ix_policy_rules_signature_verified')
        batch_op.drop_index('ix_policy_rules_signed_by_key_id')
        
        batch_op.drop_column('rfc3161_timestamp')
        batch_op.drop_column('merkle_root')
        batch_op.drop_column('signature_verified')
        batch_op.drop_column('signed_at')
        batch_op.drop_column('signed_by_key_id')
        batch_op.drop_column('signature_algorithm')
        batch_op.drop_column('digital_signature')
