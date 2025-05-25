"""add_policy_and_template_models_fresh

Revision ID: eaa5f6249b99
Revises: 82069bc89d27
Create Date: 2025-05-22 09:46:33.943547

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eaa5f6249b99'
down_revision: Union[str, None] = '82069bc89d27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
