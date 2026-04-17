# Todo Project

Task management app with a React frontend, an Nginx entrypoint, a FastAPI gateway, and two internal backend services.

## Stack

- Frontend: React Router on Node.js
- Edge: Nginx
- API gateway: FastAPI
- Services: `users`, `todos`
- Databases: PostgreSQL
- Orchestration: Docker Compose

## Architecture

Nginx is the only public entrypoint.

- `http://localhost` -> frontend
- `http://localhost/api/...` -> gateway
- `http://localhost/api/docs` -> Swagger for the gateway

Internal service flow:

- `frontend` -> `gateway`
- `gateway` -> `todo_api` through RabbitMQ RPC for task commands
- `todo_api` -> RabbitMQ `tasks.events` exchange for task domain events
- `audit_worker` <- `task.*`
- `notification_worker` <- `task.created|task.status_changed|task.deleted`
- `user_api` -> `user_db`
- `todo_api` -> `todo_db`

## Services

- `nginx`: reverse proxy for the frontend and API
- `frontend`: server-rendered React app
- `gateway`: public API layer that proxies auth, users, teams, and tasks
- `user_api`: user and team management service
- `todo_api`: task management service
- `todo_event_publisher`: publishes committed outbox events to RabbitMQ
- `audit_worker`: consumes task events for audit persistence
- `notification_worker`: consumes task events for notification persistence
- `user_db`: PostgreSQL for users
- `todo_db`: PostgreSQL for tasks
- `rabbitmq`: broker for internal RPC and task domain events

## Environment Variables

Expected Docker values:

### `frontend/.env`

```env
GATEWAY_URL=http://gateway:8000
```

### `gateway/.env`

```env
USER_API_BASE=http://user_api:8000
TODO_API_BASE=http://todo_api:8000
RABBITMQ_URL=amqp://todo_user:passwordHARD@rabbitmq:5672/
RABBITMQ_TASK_QUEUE=todo.task.rpc
```

### `users/.env`

```env
DATABASE_URL=postgresql://postgres:postgres@user_db:5432/app_db
ACCESS_SECRET_KEY=access_secret123
REFRESH_SECRET_KEY=REFRESH_SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=10080
RABBITMQ_URL=amqp://todo_user:passwordHARD@rabbitmq:5672/
RABBITMQ_ROLE_QUEUE=users.role.rpc
```

### `todos/.env`

```env
DATABASE_URL=postgresql://postgres:postgres@todo_db:5432/todo_db
USER_SERVICE_URL=http://user_api:8000
ACCESS_SECRET_KEY=access_secret123
ALGORITHM=HS256
RABBITMQ_URL=amqp://todo_user:passwordHARD@rabbitmq:5672/
RABBITMQ_ROLE_QUEUE=users.role.rpc
RABBITMQ_TASK_QUEUE=todo.task.rpc
TASK_EVENTS_EXCHANGE=tasks.events
TASK_EVENTS_AUDIT_QUEUE=tasks.events.audit
TASK_EVENTS_NOTIFICATIONS_QUEUE=tasks.events.notifications
```

## Task Events

`todo_api` stores task changes and outbox events in the same PostgreSQL transaction. The `todo_event_publisher` process reads pending outbox rows and publishes versioned domain events to the `tasks.events` topic exchange.

Published routing keys:

- `task.created`
- `task.status_changed`
- `task.deleted`

Common event envelope:

```json
{
  "event_id": "uuid",
  "event_type": "task.created",
  "occurred_at": "2026-04-17T12:00:00Z",
  "producer": "todo_api",
  "correlation_id": "uuid",
  "version": 1,
  "payload": {}
}
```

Consumers:

- `audit_worker` stores every `task.*` event in `audit_event_logs`
- `notification_worker` stores notification work items in `notification_event_logs`

Reliability notes:

- outbox records are written in the same transaction as task changes
- workers use per-consumer processed-event records for idempotency
- failed messages are routed through retry queues and then to DLQ queues

## Run With Docker

Start everything:

```bash
docker compose up --build
```

Stop everything:

```bash
docker compose down
```

## URLs

After startup:

- App: `http://localhost`
- Login page: `http://localhost/login`
- Gateway Swagger: `http://localhost/api/docs`
