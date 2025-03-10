"""create posts table

Revision ID: 93594919c9c0
Revises: 
Create Date: 2025-03-10 12:57:01.312860

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93594919c9c0'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "posts",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False, server_default="TRUE"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        
    )
    print("Table created successfully")
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("posts")
    print("Table dropped successfully")
    pass

