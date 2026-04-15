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
- `gateway` -> `user_api`
- `gateway` -> `todo_api`
- `user_api` -> `user_db`
- `todo_api` -> `todo_db`

## Services

- `nginx`: reverse proxy for the frontend and API
- `frontend`: server-rendered React app
- `gateway`: public API layer that proxies auth, users, teams, and tasks
- `user_api`: user and team management service
- `todo_api`: task management service
- `user_db`: PostgreSQL for users
- `todo_db`: PostgreSQL for tasks

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
```

### `users/.env`

```env
DATABASE_URL=postgresql://postgres:postgres@user_db:5432/app_db
ACCESS_SECRET_KEY=access_secret123
REFRESH_SECRET_KEY=REFRESH_SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=10080
```

### `todos/.env`

```env
DATABASE_URL=postgresql://postgres:postgres@todo_db:5432/todo_db
USER_SERVICE_URL=http://user_api:8000
ACCESS_SECRET_KEY=access_secret123
ALGORITHM=HS256
```

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

