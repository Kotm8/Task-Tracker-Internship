from uuid import UUID
from sqlalchemy.orm import Session
from app.core.enums import SystemRole, TeamRole
from app.models.teams import Team, TeamMembership
from app.models.users import User


class MemebershipRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id_and_team_id(self, user_id: UUID, team_id: UUID) -> TeamMembership:
        return (
            self.db.query(TeamMembership)
            .filter(TeamMembership.user_id == user_id)
            .filter(TeamMembership.team_id == team_id)
            .first()
        )
    
    def get_by_team_id(self, team_id: UUID):
        return (
            self.db.query(Team)
            .filter(Team.id == team_id)
            .first()
        )
    def get_all_by_team_id(self, team_id: UUID):
        return(
            self.db.query(User, TeamMembership.team_role)
            .join(TeamMembership, TeamMembership.user_id == User.id)
            .filter(TeamMembership.team_id == team_id)
            .all()
        )
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
