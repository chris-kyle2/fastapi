"""add users table

Revision ID: 47a3bb9b7a4c
Revises: 69635c242ed1
Create Date: 2025-03-10 13:13:49.898435

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '47a3bb9b7a4c'
down_revision: Union[str, None] = '69635c242ed1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    print("Table created successfully")
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("users")
    print("Table dropped successfully")
    pass
