from uuid import UUID
from sqlalchemy import DateTime
from sqlalchemy.orm import Session
from app.models.tokens import AccessToken, RefreshToken


class JWTRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_access_token_by_userid(self, user_id: UUID) -> AccessToken:
        return (
            self.db.query(AccessToken)
            .filter(AccessToken.user_id == user_id)
            .first()
        )

    def get_access_token_by_hash(self, token_hash: str) -> AccessToken:
        return (
            self.db.query(AccessToken)
            .filter(AccessToken.token_hash == token_hash)
            .first()
        )
    
    def get_refresh_token_by_userid(self, user_id: UUID) -> RefreshToken:
        return (
            self.db.query(RefreshToken)
            .filter(RefreshToken.user_id == user_id)
            .first()
        )

    def get_refresh_token_by_hash(self, token_hash: str) -> RefreshToken:
        return (
            self.db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .first()
        )
    
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
        updated_count = (
            self.db.query(AccessToken)
            .filter(
                AccessToken.user_id == user_id,
                AccessToken.revoked_at.is_(None),
            )
            .update(
                {AccessToken.revoked_at: revoked_at},
                synchronize_session=False,
            )
        )

        return updated_count
    
    def revoke_all_refresh_tokens_by_user_id(self, user_id: UUID, revoked_at: DateTime) -> int:
        updated_count = (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .update(
                {RefreshToken.revoked_at: revoked_at},
                synchronize_session=False,
            )
        )

        return updated_count
