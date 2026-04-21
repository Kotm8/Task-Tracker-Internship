import logging
from datetime import datetime, timedelta, timezone
from redis import Redis
from redis.exceptions import RedisError
from redis.backoff import NoBackoff
from redis.retry import Retry

from app.core.config import REDIS_HOST, REDIS_PASSWORD, REDIS_PORT

logger = logging.getLogger(__name__)

REDIS_RETRY_AFTER = timedelta(seconds=30)


class RedisManager:
    def __init__(self) -> None:
        self.client: Redis | None = None
        self.disabled_until: datetime | None = None

    def _build_client(self) -> Redis:
        return Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=0.2,
            socket_timeout=0.2,
            retry=Retry(NoBackoff(), 0),
        )

    def disable(self, exc: Exception | None = None) -> None:
        if self.client is not None:
            try:
                self.client.close()
            except Exception:
                pass

        self.client = None
        self.disabled_until = datetime.now(timezone.utc) + REDIS_RETRY_AFTER

        if exc is not None:
            logger.warning("Redis disabled temporarily: %s", exc)

    def init(self) -> None:
        client = self._build_client()
        try:
            client.ping()
            self.client = client
            self.disabled_until = None
            logger.info("Redis connected")
        except RedisError as exc:
            self.disable(exc)

    def get_client(self) -> Redis | None:
        now = datetime.now(timezone.utc)

        if self.disabled_until is not None and now < self.disabled_until:
            return None

        if self.client is not None:
            return self.client

        client = self._build_client()
        try:
            client.ping()
            self.client = client
            self.disabled_until = None
            logger.info("Redis reconnected")
            return self.client
        except RedisError as exc:
            self.disable(exc)
            return None

    def close(self) -> None:
        if self.client is not None:
            self.client.close()

        self.client = None
        self.disabled_until = None


redis_manager = RedisManager()
