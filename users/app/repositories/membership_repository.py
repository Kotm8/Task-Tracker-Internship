from uuid import UUID
from sqlalchemy import case, select
from sqlalchemy.orm import Session
from app.core.enums import TeamRole
from app.models.teams import TeamMembership
from app.models.users import User


class MemebershipRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_one(
        self,
        *,
        user_id: UUID | None = None,
        team_id: UUID | None = None,
    ) -> TeamMembership:
        stmt = select(TeamMembership)

        if user_id is not None:
            stmt = stmt.where(TeamMembership.user_id == user_id)
        if team_id is not None:
            stmt = stmt.where(TeamMembership.team_id == team_id)

        if user_id is None and team_id is None:
            raise ValueError("No user_id or team_id")

        return self.db.scalar(stmt)
    

    def get_all_by_team_id(self, team_id: UUID):
        role_order = case(
            (TeamMembership.team_role == TeamRole.PM, 1),
            (TeamMembership.team_role == TeamRole.TL, 2),
            (TeamMembership.team_role == TeamRole.MEMBER, 3),
            else_=4,
        )

        stmt = (
            select(User, TeamMembership.team_role)
            .join(TeamMembership, TeamMembership.user_id == User.id)
            .where(TeamMembership.team_id == team_id)
            .order_by(role_order)
        )
        return self.db.execute(stmt).all()

    def create(self, user_id: UUID, team_id: UUID, team_role: TeamRole) -> TeamMembership:
        db_team_membership = TeamMembership(
            user_id=user_id,
            team_id=team_id,
            team_role=team_role,
        )
    
        self.db.add(db_team_membership)
        self.db.commit()
        self.db.refresh(db_team_membership)
        return db_team_membership
    
    def update_role(self, teammembership: TeamMembership, team_role: TeamRole) -> TeamMembership:
        teammembership.team_role = team_role
        self.db.commit()
        self.db.refresh(teammembership)
        return teammembership
    
    def delete_membership(self, teammembership: TeamMembership,):
        self.db.delete(teammembership)
        self.db.commit()
