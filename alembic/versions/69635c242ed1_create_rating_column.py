"""create rating column

Revision ID: 69635c242ed1
Revises: 93594919c9c0
Create Date: 2025-03-10 13:10:42.820499

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69635c242ed1'
down_revision: Union[str, None] = '93594919c9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("posts", sa.Column("rating", sa.Integer(), nullable=True))
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("posts", "rating")
    pass
