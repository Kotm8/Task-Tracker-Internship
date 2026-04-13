from sqlalchemy import Column, String, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.core.enums import TeamRole
from app.db.database import Base
import uuid


class Team(Base):
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)


class TeamMembership(Base):
    __tablename__ = "team_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)

    team_role = Column(
        Enum(
            TeamRole,
            name="team_role_enum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=TeamRole.MEMBER.value,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "team_id", name="uq_user_team"),
    )
