from uuid import UUID
from sqlalchemy import DateTime, update, select
from sqlalchemy.orm import Session
from app.models.tokens import AccessToken, RefreshToken


class JWTRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_access_token_by_userid(self, user_id: UUID) -> AccessToken:
        stmt = select(AccessToken).where(AccessToken.user_id == user_id)
        return self.db.scalar(stmt)

    def get_all_access_tokens_by_userid(self, user_id: UUID) -> list[AccessToken]:
        stmt = select(AccessToken).where(AccessToken.user_id == user_id)
        return list(self.db.scalars(stmt).all())

    def get_access_token_by_hash(self, token_hash: str) -> AccessToken:
        stmt = select(AccessToken).where(AccessToken.token_hash == token_hash)
        return self.db.scalar(stmt)
    
    def get_refresh_token_by_userid(self, user_id: UUID) -> RefreshToken:
        stmt = select(RefreshToken).where(RefreshToken.user_id == user_id)
        return self.db.scalar(stmt)

    def get_all_refresh_tokens_by_userid(self, user_id: UUID) -> list[RefreshToken]:
        stmt = select(RefreshToken).where(RefreshToken.user_id == user_id)
        return list(self.db.scalars(stmt).all())

    def get_refresh_token_by_hash(self, token_hash: str) -> RefreshToken:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return self.db.scalar(stmt)
    
    def save_access_token(self, token_hash: str, user_id: UUID, expires_at: DateTime):
        db_access_token = AccessToken(token_hash=token_hash, user_id=user_id, expires_at=expires_at)
        self.db.add(db_access_token)
        self.db.commit()

    def save_refresh_token(self, token_hash: str, user_id: UUID, expires_at: DateTime):
        db_refresh_token = RefreshToken(token_hash=token_hash, user_id=user_id, expires_at=expires_at)
        self.db.add(db_refresh_token)
        self.db.commit()

    def revoke_access_token(self, access_token: AccessToken, revoked_at: DateTime):
        access_token.revoked_at = revoked_at
        self.db.commit()

    def revoke_refresh_token(self, refresh_token: RefreshToken, revoked_at: DateTime):
        refresh_token.revoked_at = revoked_at
        self.db.commit()
    
    def revoke_all_access_tokens_by_user_id(self, user_id: UUID, revoked_at: DateTime) -> int:
        stmt = (
            update(AccessToken)
            .where(
                AccessToken.user_id == user_id,
                AccessToken.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        result = self.db.execute(stmt)

        return result.rowcount or 0
    
    def revoke_all_refresh_tokens_by_user_id(self, user_id: UUID, revoked_at: DateTime) -> int:
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        result = self.db.execute(stmt)

        return result.rowcount or 0
