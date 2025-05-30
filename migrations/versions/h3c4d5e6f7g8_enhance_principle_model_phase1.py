"""Enhance Principle model for Phase 1 constitutional features

Revision ID: h3c4d5e6f7g8
Revises: g2b3c4d5e6f7
Create Date: 2025-01-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'h3c4d5e6f7g8'
down_revision: Union[str, None] = 'g2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to enhance Principle model for Phase 1."""
    
    # First, fix the title/name mismatch by renaming title to name
    with op.batch_alter_table('principles', schema=None) as batch_op:
        # Drop the existing index on title
        batch_op.drop_index('ix_principles_title')
        # Rename title column to name
        batch_op.alter_column('title', new_column_name='name')
        # Create new index on name with unique constraint
        batch_op.create_index('ix_principles_name', ['name'], unique=True)
    
    # Add enhanced constitutional principle fields
    with op.batch_alter_table('principles', schema=None) as batch_op:
        # Priority weight for principle prioritization (0.0 to 1.0)
        batch_op.add_column(sa.Column('priority_weight', sa.Float(), nullable=True, 
                                     comment='Priority weight for principle prioritization (0.0 to 1.0)'))
        
        # Scope definitions for principle applicability
        batch_op.add_column(sa.Column('scope', postgresql.JSONB(astext_type=sa.Text()), nullable=True,
                                     comment='JSON array defining contexts where principle applies'))
        
        # Structured normative statement
        batch_op.add_column(sa.Column('normative_statement', sa.Text(), nullable=True,
                                     comment='Structured normative statement for constitutional interpretation'))
        
        # Formal constraints for the principle
        batch_op.add_column(sa.Column('constraints', postgresql.JSONB(astext_type=sa.Text()), nullable=True,
                                     comment='JSON object defining formal constraints and requirements'))
        
        # Rationale for the principle
        batch_op.add_column(sa.Column('rationale', sa.Text(), nullable=True,
                                     comment='Detailed rationale and justification for the principle'))
        
        # Keywords for searchability and categorization
        batch_op.add_column(sa.Column('keywords', postgresql.JSONB(astext_type=sa.Text()), nullable=True,
                                     comment='JSON array of keywords for principle categorization'))
        
        # Category for principle classification
        batch_op.add_column(sa.Column('category', sa.String(length=100), nullable=True, index=True,
                                     comment='Category classification (e.g., Safety, Privacy, Fairness)'))
        
        # Validation criteria for natural language testing
        batch_op.add_column(sa.Column('validation_criteria_nl', sa.Text(), nullable=True,
                                     comment='Natural language validation criteria for testing'))
        
        # Constitutional compliance metadata
        batch_op.add_column(sa.Column('constitutional_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True,
                                     comment='Metadata for constitutional compliance tracking'))
    
    # Create indexes for enhanced searchability
    op.create_index('ix_principles_priority_weight', 'principles', ['priority_weight'], unique=False)
    op.create_index('ix_principles_category', 'principles', ['category'], unique=False)


def downgrade() -> None:
    """Downgrade schema to remove enhanced Principle fields."""
    
    # Drop enhanced field indexes
    op.drop_index('ix_principles_category', table_name='principles')
    op.drop_index('ix_principles_priority_weight', table_name='principles')
    
    # Remove enhanced constitutional principle fields
    with op.batch_alter_table('principles', schema=None) as batch_op:
        batch_op.drop_column('constitutional_metadata')
        batch_op.drop_column('validation_criteria_nl')
        batch_op.drop_column('category')
        batch_op.drop_column('keywords')
        batch_op.drop_column('rationale')
        batch_op.drop_column('constraints')
        batch_op.drop_column('normative_statement')
        batch_op.drop_column('scope')
        batch_op.drop_column('priority_weight')
    
    # Revert name back to title
    with op.batch_alter_table('principles', schema=None) as batch_op:
        # Drop the name index
        batch_op.drop_index('ix_principles_name')
        # Rename name column back to title
        batch_op.alter_column('name', new_column_name='title')
        # Recreate the title index
        batch_op.create_index('ix_principles_title', ['title'], unique=False)
