from uuid import UUID

from sqlalchemy.orm import Session

from app.models.idempotency_keys import IdempotencyKey


class IdempotencyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_endpoint_and_key(self, user_id: UUID, endpoint: str, key: UUID):
        return (
            self.db.query(IdempotencyKey)
            .filter(IdempotencyKey.user_id == user_id)
            .filter(IdempotencyKey.endpoint == endpoint)
            .filter(IdempotencyKey.key == str(key))
            .first()
        )

    def create(self, user_id: UUID, endpoint: str, key: UUID, request_hash: str) -> IdempotencyKey:
        db_idempotency_key = IdempotencyKey(
            key=str(key),
            user_id=user_id,
            endpoint=endpoint,
            request_hash=request_hash,
        )
        self.db.add(db_idempotency_key)
        self.db.commit()
        self.db.refresh(db_idempotency_key)
        return db_idempotency_key

    def delete(self, idempotency_key: IdempotencyKey):
        self.db.delete(idempotency_key)
        self.db.commit()
