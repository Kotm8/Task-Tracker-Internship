from uuid import UUID
from sqlalchemy.orm import Session
from app.core.enums import SystemRole
from app.models.teams import Team, TeamMembership
from app.models.users import User


class TeamRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_name(self, name: str):
        return (
            self.db.query(Team)
            .filter(Team.name == name)
            .first()
        )
    
    def get_by_team_id(self, team_id: UUID):
        return (
            self.db.query(Team)
            .filter(Team.id == team_id)
            .first()
        )
    
    def get_all_teams_with_user(self, user_id: UUID):
        return (
            self.db.query(Team, TeamMembership.team_role)
            .join(TeamMembership, TeamMembership.team_id == Team.id)
            .filter(TeamMembership.user_id == user_id)
            .all()
        )
    
    def get_all(self):
        return (
            self.db.query(Team)
            .all()
        )
    
    def create(self, name: str)-> Team:
        db_team = Team(name=name)
        self.db.add(db_team)
        self.db.commit()
        self.db.refresh(db_team)
        return db_team
    
    
    
    
