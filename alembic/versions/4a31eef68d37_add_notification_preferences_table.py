"""Add notification preferences table

Revision ID: 4a31eef68d37
Revises: 4e1482ee43f7
Create Date: 2025-03-11 10:47:41.877365

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a31eef68d37'
down_revision: Union[str, None] = '4e1482ee43f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("sms_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("webhook_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("webhook_url", sa.String(255), nullable=True),
        sa.Column("phone_number", sa.String(20), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
    )
    print("Notification preferences table created successfully")
    op.execute("""
        INSERT INTO notification_preferences (user_id, sms_enabled, webhook_enabled, created_at, updated_at)
        SELECT id, false, false, now(), now() FROM users
    """)
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("notification_preferences")
    print("Notification preferences table dropped successfully")
    pass
