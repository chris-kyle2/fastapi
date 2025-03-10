"""add foreign key to posts table

Revision ID: 01a950b31c8a
Revises: 47a3bb9b7a4c
Create Date: 2025-03-10 13:20:29.397810

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '01a950b31c8a'
down_revision: Union[str, None] = '47a3bb9b7a4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("posts", sa.Column("user_id", sa.Integer(), nullable=False))
    op.create_foreign_key("posts_users_fk", source_table="posts", referent_table="users", local_cols=["user_id"], remote_cols=["id"], ondelete="CASCADE")
    print("Foreign key added successfully")
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("posts_users_fk", table_name="posts", type_="foreignkey")
    op.drop_column("posts", "user_id")
    print("Foreign key dropped successfully")
    pass
