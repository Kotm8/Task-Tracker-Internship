from uuid import UUID
from fastapi import HTTPException
from redis.exceptions import RedisError
from app.core.enums import SystemRole
from app.schemas.user import UserRegister, UserResponse
from sqlalchemy.orm import Session
from app.models.users import User
from app.core.redis_client import redis_manager
from app.services.jwt_service import JWTService
from argon2 import PasswordHasher
from app.repositories.user_repository import UserRepository

ph = PasswordHasher()

class UserService:
    @staticmethod
    def get_current_user(db: Session, access_token: str) -> User:
        user_repo = UserRepository(db)
        payload = JWTService.decode_access_token(access_token)
        user_id = payload.get("sub")
        jti = payload.get("jti")
        redis = redis_manager.get_client()

        if redis is not None and jti:
            try:
                cached_user_id = redis.get(f"user_todo:access_jti:{jti}")
            except RedisError as e:
                redis_manager.disable(e)
                cached_user_id = None
        else:
            cached_user_id = None

        if cached_user_id is None:
            user_id = JWTService.validate_access_token(db, access_token)
        else:
            user_id = cached_user_id

        db_user = user_repo.get_one(user_id=UUID(str(user_id)))

        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        return db_user

    @staticmethod
    def is_user_admin(db: Session, access_token: str) -> bool:
        db_user = UserService.get_current_user(db, access_token)

        if db_user.system_role != SystemRole.ADMIN:
            raise HTTPException(status_code=403, detail="Admin access required")

        return True

    @staticmethod
    def get_user_response(db: Session, access_token: str) -> UserResponse:
        db_user = UserService.get_current_user(db, access_token)
        return UserResponse.model_validate(db_user)

    @staticmethod
    def create_user(db: Session, user: UserRegister):
        user_repo = UserRepository(db)

        db_user = user_repo.get_one(email=user.email)
        if db_user:
            raise HTTPException(status_code=409, detail="Email already used")
        
        hashed_password = ph.hash(user.password)
        db_user = user_repo.create(user.username, user.email, hashed_password)
        return db_user
    
    @staticmethod
    def change_user_role(db: Session, role: SystemRole, user_id: UUID) -> User:
        user_repo = UserRepository(db)

        db_user = user_repo.get_one(user_id=user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        return user_repo.update_role(db_user, role)
