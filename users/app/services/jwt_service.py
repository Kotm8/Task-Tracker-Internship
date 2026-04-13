import os
from uuid import UUID
from fastapi import HTTPException
import jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.models.tokens import AccessToken, RefreshToken
from app.models.users import User
from app.repositories.jwt_repository import JWTRepository

load_dotenv()
ACCESS_SECRET_KEY = os.getenv("ACCESS_SECRET_KEY")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
REFRESH_TOKEN_EXPIRE_MINUTES = timedelta(minutes=int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES")))

class JWTService:
    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRE_MINUTES
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, ACCESS_SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + REFRESH_TOKEN_EXPIRE_MINUTES
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_access_token(access_token: str):
        try:
            payload = jwt.decode(access_token, ACCESS_SECRET_KEY, algorithms=[ALGORITHM])
            user_id  = payload.get("sub")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id 

    @staticmethod
    def decode_refresh_token(refresh_token: str):
        try:
            payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
            user_id  = payload.get("sub")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id 

    @staticmethod
    def validate_access_token(db: Session, access_token: str):
        jwt_repo = JWTRepository(db)
        user_id = JWTService.decode_access_token(access_token)
        db_access_token = jwt_repo.get_access_token_by_hash(access_token)

        if not db_access_token or db_access_token.revoked_at is not None:
            raise HTTPException(status_code=401, detail="Invalid access token")

        return user_id

    @staticmethod
    def validate_refresh_token(db: Session, refresh_token: str):
        jwt_repo = JWTRepository(db)
        user_id = JWTService.decode_refresh_token(refresh_token)
        db_refresh_token = jwt_repo.get_refresh_token_by_hash(refresh_token)

        if not db_refresh_token or db_refresh_token.revoked_at is not None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        return user_id

    @staticmethod
    def save_access_token(db: Session, data: User, access_token: str):
        jwt_repo = JWTRepository(db)
        jwt_repo.save_access_token(access_token, data.id, datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRE_MINUTES)

    @staticmethod
    def save_refresh_token(db: Session, data: User, refresh_token: str):
        jwt_repo = JWTRepository(db)
        jwt_repo.save_refresh_token(refresh_token, data.id, datetime.now(timezone.utc) + REFRESH_TOKEN_EXPIRE_MINUTES)

    @staticmethod
    def revoke_access_token(db: Session, access_token: str):
        jwt_repo = JWTRepository(db)
        db_access_token = jwt_repo.get_access_token_by_hash(access_token)
        if not db_access_token:
            raise HTTPException(status_code=401, detail="Invalid access token")
        jwt_repo.revoke_access_token(db_access_token, datetime.now(timezone.utc))
    
    @staticmethod
    def revoke_refresh_token(db: Session, refresh_token: str):
        jwt_repo = JWTRepository(db)
        db_refresh_token = jwt_repo.get_refresh_token_by_hash(refresh_token)
        if not db_refresh_token:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        jwt_repo.revoke_refresh_token(db_refresh_token, datetime.now(timezone.utc))

    @staticmethod
    def revoke_all_access_tokens(db: Session, user_id: UUID) -> int:
        jwt_repo = JWTRepository(db)
        now = datetime.now(timezone.utc)

        return jwt_repo.revoke_all_access_tokens_by_user_id(user_id, now)

    @staticmethod
    def revoke_all_refresh_tokens(db: Session, user_id: UUID) -> int:
        jwt_repo = JWTRepository(db)
        now = datetime.now(timezone.utc)

        return jwt_repo.revoke_all_refresh_tokens_by_user_id(user_id, now)
