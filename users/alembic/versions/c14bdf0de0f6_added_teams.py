"""added teams

Revision ID: c14bdf0de0f6
Revises: 9ca7416c3bbf
Create Date: 2026-04-09 18:03:32.526795

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c14bdf0de0f6'
down_revision: Union[str, Sequence[str], None] = '9ca7416c3bbf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    team_role_enum = postgresql.ENUM('member', 'pm', 'tl', name='team_role_enum', create_type=False)
    system_role_enum = postgresql.ENUM('user', 'admin', name='system_role_enum', create_type=False)

    postgresql.ENUM('member', 'pm', 'tl', name='team_role_enum').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('user', 'admin', name='system_role_enum').create(op.get_bind(), checkfirst=True)

    op.create_table('teams',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('team_memberships',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('team_id', sa.UUID(), nullable=False),
    sa.Column('team_role', team_role_enum, server_default='member', nullable=False),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'team_id', name='uq_user_team')
    )
    op.add_column('users', sa.Column('system_role', system_role_enum, server_default='user', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    team_role_enum = postgresql.ENUM('member', 'pm', 'tl', name='team_role_enum', create_type=False)
    system_role_enum = postgresql.ENUM('user', 'admin', name='system_role_enum', create_type=False)

    op.drop_column('users', 'system_role')
    op.drop_table('team_memberships')
    op.drop_table('teams')
    system_role_enum.drop(op.get_bind(), checkfirst=True)
    team_role_enum.drop(op.get_bind(), checkfirst=True)
