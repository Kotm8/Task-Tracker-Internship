from uuid import UUID, uuid4
from fastapi import HTTPException
import jwt
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.core.config import (
    ACCESS_SECRET_KEY,
    ALGORITHM,
    REFRESH_SECRET_KEY,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_MINUTES,
)
from app.models.tokens import AccessToken, RefreshToken
from app.models.users import User
from app.core.redis_client import redis_manager
from app.repositories.jwt_repository import JWTRepository
from redis.exceptions import RedisError

ACCESS_TOKEN_EXPIRE_MINUTES = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
REFRESH_TOKEN_EXPIRE_MINUTES = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

class JWTService:
    @staticmethod
    def _get_expiry_timestamp(payload: dict) -> int | None:
        exp = payload.get("exp")
        if isinstance(exp, datetime):
            return int(exp.timestamp())
        if isinstance(exp, (int, float)):
            return int(exp)
        return None

    @staticmethod
    def _seconds_until_expiry(payload: dict) -> int | None:
        exp_timestamp = JWTService._get_expiry_timestamp(payload)
        if exp_timestamp is None:
            return None

        ttl = exp_timestamp - int(datetime.now(timezone.utc).timestamp())
        return ttl if ttl > 0 else None

    @staticmethod
    def _cache_token_jti(prefix: str, payload: dict, user_id: str) -> None:
        jti = payload.get("jti")
        if not jti:
            return

        ttl = JWTService._seconds_until_expiry(payload)
        if ttl is None:
            return

        redis = redis_manager.get_client()
        if redis is None:
            return

        try:
            redis.setex(f"user_todo:{prefix}:{jti}", ttl, user_id)
        except RedisError as e:
            redis_manager.disable(e)

    @staticmethod
    def _delete_token_jti_cache(prefix: str, payload: dict) -> None:
        jti = payload.get("jti")
        if not jti:
            return

        redis = redis_manager.get_client()
        if redis is None:
            return

        try:
            redis.delete(f"user_todo:{prefix}:{jti}")
        except RedisError as e:
            redis_manager.disable(e)

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRE_MINUTES
        to_encode.update({"exp": expire, "jti": str(uuid4())})
        encoded_jwt = jwt.encode(to_encode, ACCESS_SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + REFRESH_TOKEN_EXPIRE_MINUTES
        to_encode.update({"exp": expire, "jti": str(uuid4())})
        encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_access_token(access_token: str, ignore_expired: bool = False):
        try:
            payload = jwt.decode(access_token, ACCESS_SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError:
            if ignore_expired:
                try:
                    payload = jwt.decode(
                        access_token,
                        ACCESS_SECRET_KEY,
                        algorithms=[ALGORITHM],
                        options={"verify_exp": False},
                    )
                except jwt.InvalidTokenError:
                    raise HTTPException(status_code=401, detail="Invalid token")
            else:
                raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload

    @staticmethod
    def decode_refresh_token(refresh_token: str):
        try:
            payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload

    @staticmethod
    def validate_access_token(db: Session, access_token: str):
        jwt_repo = JWTRepository(db)
        payload = JWTService.decode_access_token(access_token)
        user_id = payload.get("sub")
        db_access_token = jwt_repo.get_access_token_by_hash(access_token)

        if not db_access_token or db_access_token.revoked_at is not None:
            raise HTTPException(status_code=401, detail="Invalid access token")

        JWTService._cache_token_jti("access_jti", payload, user_id)
        return user_id

    @staticmethod
    def validate_refresh_token(db: Session, refresh_token: str):
        jwt_repo = JWTRepository(db)
        payload = JWTService.decode_refresh_token(refresh_token)
        user_id = payload.get("sub")
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
    def revoke_access_token(db: Session, access_token: str, ignore_expired: bool = False):
        jwt_repo = JWTRepository(db)
        payload = JWTService.decode_access_token(access_token, ignore_expired=ignore_expired)
        db_access_token = jwt_repo.get_access_token_by_hash(access_token)
        if not db_access_token:
            raise HTTPException(status_code=401, detail="Invalid access token")
        jwt_repo.revoke_access_token(db_access_token, datetime.now(timezone.utc))
        JWTService._delete_token_jti_cache("access_jti", payload)
    
    @staticmethod
    def revoke_refresh_token(db: Session, refresh_token: str):
        jwt_repo = JWTRepository(db)
        payload = JWTService.decode_refresh_token(refresh_token)
        db_refresh_token = jwt_repo.get_refresh_token_by_hash(refresh_token)
        if not db_refresh_token:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        jwt_repo.revoke_refresh_token(db_refresh_token, datetime.now(timezone.utc))

    @staticmethod
    def revoke_all_access_tokens(db: Session, user_id: UUID) -> int:
        jwt_repo = JWTRepository(db)
        now = datetime.now(timezone.utc)
        access_tokens = jwt_repo.get_all_access_tokens_by_userid(user_id)

        for access_token in access_tokens:
            try:
                payload = JWTService.decode_access_token(access_token.token_hash)
            except HTTPException:
                continue
            JWTService._delete_token_jti_cache("access_jti", payload)

        return jwt_repo.revoke_all_access_tokens_by_user_id(user_id, now)

    @staticmethod
    def revoke_all_refresh_tokens(db: Session, user_id: UUID) -> int:
        jwt_repo = JWTRepository(db)
        now = datetime.now(timezone.utc)
        refresh_tokens = jwt_repo.get_all_refresh_tokens_by_userid(user_id)

        for refresh_token in refresh_tokens:
            try:
                payload = JWTService.decode_refresh_token(refresh_token.token_hash)
            except HTTPException:
                continue

        return jwt_repo.revoke_all_refresh_tokens_by_user_id(user_id, now)
