"""keep task history after task delete

Revision ID: 9fb6ad31c2d8
Revises: 4bc9fbc6f6a1
Create Date: 2026-04-17 18:10:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "9fb6ad31c2d8"
down_revision: Union[str, Sequence[str], None] = "4bc9fbc6f6a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("task_history_task_id_fkey", "task_history", type_="foreignkey")
    op.drop_constraint("task_status_history_task_id_fkey", "task_status_history", type_="foreignkey")


def downgrade() -> None:
    op.create_foreign_key(
        "task_history_task_id_fkey",
        "task_history",
        "tasks",
        ["task_id"],
        ["id"],
    )
    op.create_foreign_key(
        "task_status_history_task_id_fkey",
        "task_status_history",
        "tasks",
        ["task_id"],
        ["id"],
    )
