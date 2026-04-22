import os

from dotenv import load_dotenv


load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")

RABBITMQ_ROLE_QUEUE = os.getenv("RABBITMQ_ROLE_QUEUE", "role_queue")
RABBITMQ_TASK_QUEUE = os.getenv("RABBITMQ_TASK_QUEUE", "task_queue")

RABBITMQ_URL = (os.getenv("RABBITMQ_URL") or "").strip()
RABBITMQ_CONNECT_RETRIES = int(os.getenv("RABBITMQ_CONNECT_RETRIES", "20"))
RABBITMQ_CONNECT_DELAY_SECONDS = float(os.getenv("RABBITMQ_CONNECT_DELAY_SECONDS", "2"))

TASK_EVENTS_EXCHANGE = os.getenv("TASK_EVENTS_EXCHANGE", "tasks.events")
TASK_EVENTS_AUDIT_QUEUE = os.getenv("TASK_EVENTS_AUDIT_QUEUE", "tasks.events.audit")
TASK_EVENTS_AUDIT_RETRY_QUEUE = os.getenv("TASK_EVENTS_AUDIT_RETRY_QUEUE", "tasks.events.audit.retry")
TASK_EVENTS_AUDIT_DLQ_QUEUE = os.getenv("TASK_EVENTS_AUDIT_DLQ_QUEUE", "tasks.events.audit.dlq")
TASK_EVENTS_NOTIFICATIONS_QUEUE = os.getenv("TASK_EVENTS_NOTIFICATIONS_QUEUE", "tasks.events.notifications")
TASK_EVENTS_NOTIFICATIONS_RETRY_QUEUE = os.getenv(
    "TASK_EVENTS_NOTIFICATIONS_RETRY_QUEUE",
    "tasks.events.notifications.retry",
)
TASK_EVENTS_NOTIFICATIONS_DLQ_QUEUE = os.getenv(
    "TASK_EVENTS_NOTIFICATIONS_DLQ_QUEUE",
    "tasks.events.notifications.dlq",
)

TASK_EVENT_PUBLISH_BATCH_SIZE = int(os.getenv("TASK_EVENT_PUBLISH_BATCH_SIZE", "50"))
TASK_EVENT_PUBLISH_INTERVAL_SECONDS = float(os.getenv("TASK_EVENT_PUBLISH_INTERVAL_SECONDS", "2"))
TASK_EVENT_RETRY_DELAY_MS = int(os.getenv("TASK_EVENT_RETRY_DELAY_MS", "5000"))
TASK_EVENT_MAX_RETRIES = int(os.getenv("TASK_EVENT_MAX_RETRIES", "3"))
