import hashlib
import json
from typing import Any
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.idempotency_repository import IdempotencyRepository


class IdempotencyService:
    def hash_request(payload: Any) -> str:
        encoded_payload = jsonable_encoder(payload)
        canonical = json.dumps(encoded_payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def validate_request(
        db: Session,
        user_id: UUID,
        endpoint: str,
        idempotency_key: UUID,
        payload: Any,
    ):
        idempotency_repo = IdempotencyRepository(db)
        request_hash = IdempotencyService.hash_request(payload)

        existing_key = idempotency_repo.get_by_user_endpoint_and_key(
            user_id,
            endpoint,
            idempotency_key,
        )

        if not existing_key:
            return idempotency_repo.create(
                user_id,
                endpoint,
                idempotency_key,
                request_hash,
            )

        if existing_key.request_hash != request_hash:
            raise HTTPException(
                status_code=409,
                detail="Idempotency key already used with different request body",
            )

        raise HTTPException(
            status_code=409,
            detail="Duplicate request already processed",
        )
    
