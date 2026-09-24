# Personal Expense Tracker API

A Tornado and MongoDB REST backend for private income and expense records. Users register, sign in to receive an API key, manage custom categories and transactions, then view filtered records and monthly totals.

## Setup

1. Copy `.env.example` values only if configuring a different environment; this project uses `.env_5ad06667-9bcd-48b5-bb6c-a469b3be3571`.
2. Ensure MongoDB is reachable at `mongodb://localhost:27017/gen_476aba8b5f9e`.
3. Run `chmod +x start.sh && PORT=25350 bash start.sh`.
4. Visit `http://localhost:25350/health`.

## Environment

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | MongoDB URL; defaults to the verified fallback database. |
| `ADMIN_API_KEY` | Protects administrative API-key lifecycle endpoints. |
| `PORT` | Server port, default `25350`. |

## API endpoints

| Method | Path | Authentication | Purpose |
|---|---|---|---|
| GET | `/health` | No | Health check |
| POST | `/api/v1/auth/register` | No | Register a user |
| POST | `/api/v1/auth/login` | No | Receive a user API key |
| GET | `/api/v1/auth/me` | API key | Current user |
| POST/GET | `/api/v1/admin/api-keys` | Admin key | Create/list admin-managed keys |
| DELETE | `/api/v1/admin/api-keys/{id}` | Admin key | Revoke a key |
| GET/POST | `/api/v1/categories` | API key | List/create categories |
| GET/DELETE | `/api/v1/categories/{id}` | API key | View/delete permitted category |
| GET/POST | `/api/v1/transactions` | API key | List/filter/create transactions |
| GET/PUT/DELETE | `/api/v1/transactions/{id}` | API key | View/update/delete an owned transaction |
| GET | `/api/v1/transactions/summary/monthly?month=YYYY-MM` | API key | Monthly income, expenses, balance and breakdown |

Transaction listing accepts `limit`, `offset`, `type`, `category_id`, `start_date`, `end_date`, `search`, `sort_by` (`date`, `amount`, `category`) and `order` (`asc`, `desc`).

## Tests

Start the API, then run `export BASE_URL=http://localhost:25350 && pytest tests/ -v --tb=short`.

## Docker

Run `docker compose up --build`. The host exposes the service on port `25350`, while the container binds port `8000`.

## Tree

- `main.py` — routes and application startup.
- `database.py` — Motor client and indexes.
- `handlers/` — REST endpoint implementations.
- `schemas.py`, `models.py` — validation and document definitions.
- `tests/` — live Tavern API tests.
