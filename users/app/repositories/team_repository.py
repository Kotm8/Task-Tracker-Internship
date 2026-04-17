from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.enums import SystemRole
from app.models.teams import Team, TeamMembership
from app.models.users import User


class TeamRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_one(
        self,
        *,
        team_id: UUID | None = None,
        name: str | None = None,
    ):
        stmt = select(Team)

        if team_id is not None:
            stmt = stmt.where(Team.id == team_id)
        elif name is not None:
            stmt = stmt.where(Team.name == name)
        else:
            raise ValueError("No team_id or name")

        return self.db.scalar(stmt)
    
    def get_all_teams_with_user(self, user_id: UUID):
        stmt = (
            select(Team, TeamMembership.team_role)
            .join(TeamMembership, TeamMembership.team_id == Team.id)
            .where(TeamMembership.user_id == user_id)
        )
        return self.db.execute(stmt).all()
    
    def get_all(self):
        stmt = select(Team)
        return self.db.scalars(stmt).all()
    
    def create(self, name: str)-> Team:
        db_team = Team(name=name)
        self.db.add(db_team)
        self.db.commit()
        self.db.refresh(db_team)
        return db_team
    
    
    
    
