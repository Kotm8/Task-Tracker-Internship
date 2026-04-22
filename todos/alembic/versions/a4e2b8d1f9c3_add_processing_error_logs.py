"""add processing error logs

Revision ID: a4e2b8d1f9c3
Revises: 9fb6ad31c2d8
Create Date: 2026-04-21 15:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a4e2b8d1f9c3"
down_revision: Union[str, Sequence[str], None] = "9fb6ad31c2d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "processing_error_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("consumer_name", sa.String(), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=True),
        sa.Column("event_type", sa.String(), nullable=True),
        sa.Column("team_id", sa.UUID(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("error_type", sa.String(), nullable=False),
        sa.Column("error_text", sa.Text(), nullable=False),
        sa.Column("failed_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("processing_error_logs")
