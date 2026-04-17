from typing import Optional
from uuid import UUID
import json
from fastapi import HTTPException
from redis.exceptions import RedisError
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
from app.core.permissions import TEAM_ROLE_PERMISSIONS, TeamPermission
from app.core.redis_client import redis_manager

CACHE_TTL_SECONDS = 300
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
        db_team = team_repo.get_one(name=team.name)
        if db_team:
            raise HTTPException(status_code=409, detail="Team name already used")

        db_team = team_repo.create(team.name)
        return db_team
        
    @staticmethod
    def add_user_to_team(team_id: UUID, user: AddUserToTeam, db: Session):
        team_repo = TeamRepository(db)
        user_repo = UserRepository(db)
        membership_repo = MemebershipRepository(db)
        db_team = team_repo.get_one(team_id=team_id)
        if not db_team:
            raise HTTPException(status_code=404, detail="Team doesn't exist")

        db_user = user_repo.get_one(email=user.email)
        if not db_user:
            raise HTTPException(status_code=404, detail="User doesn't exist")

        db_team_membership = membership_repo.get_one(user_id=db_user.id, team_id=db_team.id)
        if db_team_membership:
            raise HTTPException(status_code=409, detail="User already added to team")
    
        db_team_membership = membership_repo.create(db_user.id, db_team.id, user.role)
        
        redis = redis_manager.get_client()

        if redis is not None:
            cache_key = f"user_todo:team_membership:{db_user.id}:{team_id}"
            try:
                redis.setex(cache_key, CACHE_TTL_SECONDS, user.role)
            except RedisError as e:
                redis_manager.disable(e)
        
        if redis is not None:
            cache_key = f"user_todo:all_team_members:{team_id}"
            try:
                redis.delete(cache_key)
            except RedisError as e:
                redis_manager.disable(e)

        return TeamService._build_team_member_response(db_user, db_team_membership.team_role)
    
    @staticmethod
    def is_teammember_pm(db: Session, team_id: UUID, access_token: str) -> bool:
        membership_repo = MemebershipRepository(db)
        db_user = UserService.get_current_user(db, access_token)

        db_team_membership = membership_repo.get_one(user_id=db_user.id, team_id=team_id)
        if not db_team_membership:
            raise HTTPException(status_code=404, detail="User not added to team")
        
        return db_team_membership.team_role == TeamRole.PM

    @staticmethod
    def is_user_in_team(db: Session, team_id: UUID, access_token: str) -> bool:
        membership_repo = MemebershipRepository(db)

        db_user = UserService.get_current_user(db, access_token)

        if db_user.system_role == SystemRole.ADMIN:
            return True
        return membership_repo.get_one(user_id=db_user.id, team_id=team_id) is not None
    
    @staticmethod
    def get_members_of_team(db: Session, team_id: UUID):
        team_repo = TeamRepository(db)
        membership_repo = MemebershipRepository(db)

        db_team = team_repo.get_one(team_id=team_id)
        if not db_team:
            raise HTTPException(status_code=404, detail="Team doesn't exist")
        
        redis = redis_manager.get_client()
        cache_key = f"user_todo:all_team_members:{team_id}"

        if redis is not None:
            try:
                cached_teammembers = redis.get(cache_key)
            except RedisError as e:
                redis_manager.disable(e)
                cached_teammembers = None
        else: 
            cached_teammembers = None

        if cached_teammembers is not None:
            return json.loads(cached_teammembers)
        
        memberships = membership_repo.get_all_by_team_id(team_id)
        
        response_data = [
            TeamService._build_team_member_response(db_user, team_role)
            for db_user, team_role in memberships
        ]

        if redis is not None:
            try:
                redis.setex(cache_key, CACHE_TTL_SECONDS, json.dumps(response_data, default=str))
            except RedisError as e:
                redis_manager.disable(e)

        return response_data

    @staticmethod
    def change_user_team_role(team_id: UUID, user: ChangeUserTeamRole, db: Session):
        membership_repo = MemebershipRepository(db)
        user_repo = UserRepository(db)
        db_team_membership = membership_repo.get_one(user_id=user.user_id, team_id=team_id)
    
        if not db_team_membership:
            raise HTTPException(status_code=404, detail="User is not in this team")

        db_team_membership = membership_repo.update_role(db_team_membership, user.role)
        db_user = user_repo.get_one(user_id=db_team_membership.user_id)

        redis = redis_manager.get_client()
        if redis is not None:
            cache_key = f"user_todo:team_membership:{db_team_membership.user_id}:{team_id}"
            try:
                redis.delete(cache_key)
            except RedisError as e:
                redis_manager.disable(e)
        
        if redis is not None:
            cache_key = f"user_todo:all_team_members:{team_id}"
            try:
                redis.delete(cache_key)
            except RedisError as e:
                redis_manager.disable(e)

        return TeamService._build_team_member_response(db_user, db_team_membership.team_role)

    @staticmethod
    def remove_user_from_team(team_id: UUID, user_id: UUID, db: Session):
        membership_repo = MemebershipRepository(db)
        
        db_team_membership = membership_repo.get_one(user_id=user_id, team_id=team_id)

        if not db_team_membership:
            raise HTTPException(status_code=404, detail="User is not in this team")
        
        membership_repo.delete_membership(db_team_membership)
        
        redis = redis_manager.get_client()
        if redis is not None:
            cache_key = f"user_todo:team_membership:{user_id}:{team_id}"
            try:
                redis.delete(cache_key)
            except RedisError as e:
                redis_manager.disable(e)

        if redis is not None:
            cache_key = f"user_todo:all_team_members:{team_id}"
            try:
                redis.delete(cache_key)
            except RedisError as e:
                redis_manager.disable(e)

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
    def get_all_teams(db: Session):
                
        team_repo = TeamRepository(db)
        teams = team_repo.get_all()

        return [TeamService._build_team_response(db_team) for db_team in teams]

    @staticmethod
    def get_role_in_team(db: Session, access_token: str, team_id: UUID, permission: TeamPermission) -> RoleResponse:
        membership_repo = MemebershipRepository(db)
        redis = redis_manager.get_client()
        
        db_user = UserService.get_current_user(db, access_token)
        cache_key = f"user_todo:team_membership:{db_user.id}:{team_id}"

        if redis is not None:
            try:
                cached_role = redis.get(cache_key)
            except RedisError as e:
                redis_manager.disable(e)
                cached_role = None
        else: 
            cached_role = None

        if cached_role is not None:
            role = TeamRole(cached_role)
        else:
            membership = membership_repo.get_one(user_id=db_user.id, team_id=team_id)
            if membership is None:
                raise HTTPException(status_code=403, detail="User is not in this team")

            role = membership.team_role
            if redis is not None:
                try:
                    redis.setex(cache_key, CACHE_TTL_SECONDS, role.value)
                except RedisError as e:
                    redis_manager.disable(e)

        is_allowed = permission in TEAM_ROLE_PERMISSIONS.get(role, set())


        return RoleResponse(
            user_id=db_user.id,
            role=role.value,
            is_allowed=is_allowed
            )
    
