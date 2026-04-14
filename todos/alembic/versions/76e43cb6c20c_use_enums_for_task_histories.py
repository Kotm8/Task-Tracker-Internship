"""use enums for task histories

Revision ID: 76e43cb6c20c
Revises: ee3753467a11
Create Date: 2026-04-13 16:55:36.750262

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '76e43cb6c20c'
down_revision: Union[str, Sequence[str], None] = 'ee3753467a11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

task_actions_enum = postgresql.ENUM(
    'CREATE',
    'CHANGED',
    'DELETED',
    name='task_actions_enum',
)

task_status_enum = postgresql.ENUM(
    'TODO',
    'IN_PROGRESS',
    'REVIEW',
    'DONE',
    'CANCELLED',
    name='task_status_enum',
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""
    task_actions_enum.create(op.get_bind(), checkfirst=True)

    op.alter_column('task_history', 'action',
               existing_type=sa.VARCHAR(),
               type_=task_actions_enum,
               postgresql_using='action::task_actions_enum',
               existing_nullable=False)
    op.alter_column('task_status_history', 'old_status',
               existing_type=sa.VARCHAR(),
               type_=task_status_enum,
               postgresql_using='old_status::task_status_enum',
               existing_nullable=True)
    op.alter_column('task_status_history', 'new_status',
               existing_type=sa.VARCHAR(),
               type_=task_status_enum,
               postgresql_using='new_status::task_status_enum',
               existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('task_status_history', 'new_status',
               existing_type=task_status_enum,
               type_=sa.VARCHAR(),
               postgresql_using='new_status::text',
               existing_nullable=False)
    op.alter_column('task_status_history', 'old_status',
               existing_type=task_status_enum,
               type_=sa.VARCHAR(),
               postgresql_using='old_status::text',
               existing_nullable=True)
    op.alter_column('task_history', 'action',
               existing_type=task_actions_enum,
               type_=sa.VARCHAR(),
               postgresql_using='action::text',
               existing_nullable=False)
    task_actions_enum.drop(op.get_bind(), checkfirst=True)
