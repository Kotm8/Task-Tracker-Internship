from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from app.schemas.team import ChangeUserTeamRole, RoleResponse, TeamCreate, AddUserToTeam
from sqlalchemy.orm import Session
from app.models.teams import Team, TeamMembership
from app.models.users import User
from app.services.user_service import UserService
from app.core.enums import TeamRole, SystemRole
from argon2 import PasswordHasher

from app.repositories.membership_repository import MemebershipRepository
from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository
ph = PasswordHasher()

class TeamService:
    @staticmethod
    def _build_team_member_response(db_user: User, team_role: TeamRole):
        return {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "role": team_role,
        }

    @staticmethod
    def _build_team_response(db_team: Team):
        return {
            "id": db_team.id,
            "name": db_team.name,
        }

    @staticmethod
    def _build_user_team_response(db_team: Team, team_role: TeamRole):
        return {
            "id": db_team.id,
            "name": db_team.name,
            "role": team_role,
        }

    @staticmethod
    def create_team(team: TeamCreate, db: Session):
        team_repo = TeamRepository(db)
        db_team = team_repo.get_by_name(team.name)
        if db_team:
            raise HTTPException(status_code=409, detail="Team name already used")

        db_team = team_repo.create(team.name)
        return db_team
        
    @staticmethod
    def add_user_to_team(team_id: UUID, user: AddUserToTeam, db: Session):
        team_repo = TeamRepository(db)
        user_repo = UserRepository(db)
        membership_repo = MemebershipRepository(db)
        db_team = team_repo.get_by_team_id(team_id)
        if not db_team:
            raise HTTPException(status_code=404, detail="Team doesn't exist")

        db_user = user_repo.get_by_email(user.email)
        if not db_user:
            raise HTTPException(status_code=404, detail="User doesn't exist")

        db_team_membership = membership_repo.get_by_user_id_and_team_id(db_user.id, db_team.id)
        if db_team_membership:
            raise HTTPException(status_code=409, detail="User already added to team")
    
        db_team_membership = membership_repo.create(db_user.id, db_team.id, user.role)
    
        return TeamService._build_team_member_response(db_user, db_team_membership.team_role)
    
    @staticmethod
    def is_teammember_pm(db: Session, team_id: UUID, access_token: str) -> bool:
        membership_repo = MemebershipRepository(db)
        db_user = UserService.get_current_user(db, access_token)

        db_team_membership = membership_repo.get_by_user_id_and_team_id(db_user.id, team_id)
        if not db_team_membership:
            raise HTTPException(status_code=404, detail="User not added to team")
        
        return db_team_membership.team_role == TeamRole.PM


    @staticmethod
    def get_role_in_team(db: Session, access_token: str, team_id: UUID) -> RoleResponse:
        membership_repo = MemebershipRepository(db)

        db_user = UserService.get_current_user(db, access_token)
        membership = membership_repo.get_by_user_id_and_team_id(db_user.id, team_id)

        if membership is None:
            raise HTTPException(status_code=403, detail="User is not in this team")

        return RoleResponse(
            user_id=db_user.id,
            role=membership.team_role)
    

    @staticmethod
    def is_user_in_team(db: Session, team_id: UUID, access_token: str) -> bool:
        membership_repo = MemebershipRepository(db)

        db_user = UserService.get_current_user(db, access_token)

        if db_user.system_role == SystemRole.ADMIN:
            return True
        return membership_repo.get_by_user_id_and_team_id(db_user.id, team_id) is not None
    
    @staticmethod
    def get_members_of_team(db: Session, team_id: UUID):
        team_repo = TeamRepository(db)
        membership_repo = MemebershipRepository(db)
        db_team = team_repo.get_by_team_id(team_id)
        if not db_team:
            raise HTTPException(status_code=404, detail="Team doesn't exist")
    
        memberships = membership_repo.get_all_by_team_id(team_id)

        return [
            TeamService._build_team_member_response(db_user, team_role)
            for db_user, team_role in memberships
        ]

    @staticmethod
    def change_user_team_role(team_id: UUID, user: ChangeUserTeamRole, db: Session):
        membership_repo = MemebershipRepository(db)
        user_repo = UserRepository(db)
        db_team_membership = membership_repo.get_by_user_id_and_team_id(user.user_id, team_id)
    
        if not db_team_membership:
            raise HTTPException(status_code=404, detail="User is not in this team")

        db_team_membership = membership_repo.update_role(db_team_membership, user.role)
        db_user = user_repo.get_by_user_id(db_team_membership.user_id)
        return TeamService._build_team_member_response(db_user, db_team_membership.team_role)

    @staticmethod
    def remove_user_from_team(team_id: UUID, user_id: UUID, db: Session):
        membership_repo = MemebershipRepository(db)
        
        db_team_membership = membership_repo.get_by_user_id_and_team_id(user_id, team_id)

        if not db_team_membership:
            raise HTTPException(status_code=404, detail="User is not in this team")
        
        membership_repo.delete_membership(db_team_membership)
        return {"detail": "User removed from team"}
    
    
    @staticmethod
    def get_teams_with_user(db: Session, access_token: str):
        team_repo = TeamRepository(db)
        current_user = UserService.get_current_user(db, access_token)

        teams = team_repo.get_all_teams_with_user(current_user.id)
        
        return [
            TeamService._build_user_team_response(db_team, team_role)
            for db_team, team_role in teams
        ]
        
    @staticmethod
    def get_all_teams(db: Session, access_token: str):
                
        team_repo = TeamRepository(db)
        teams = team_repo.get_all()

        return [TeamService._build_team_response(db_team) for db_team in teams]
