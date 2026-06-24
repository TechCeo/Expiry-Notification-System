# Expiry Notification System

![Docker Pulls](https://img.shields.io/docker/pulls/techceo/expiry-notifier?style=flat-square)
![GitHub Repo stars](https://img.shields.io/github/stars/TechCeo/Expiry-Notification-System?style=flat-square)
![GitHub last commit](https://img.shields.io/github/last-commit/TechCeo/Expiry-Notification-System?style=flat-square)

The Expiry Notification System is being migrated from a single-user PyQt/SQLite
desktop application to a multi-user FastAPI and PostgreSQL service. The legacy client
remains in `src/` during the migration, while all new server development lives in
`backend/`.

## Backend foundation

The first backend milestone includes:

- FastAPI application with automatic OpenAPI documentation.
- Environment-driven configuration through Pydantic Settings.
- PostgreSQL connectivity through SQLAlchemy and Psycopg.
- Alembic migration management with an initial baseline revision.
- Separate liveness (`/health`) and database readiness (`/ready`) probes.
- Docker Compose orchestration for PostgreSQL, migrations, and the API.
- Non-root, multi-stage API image without the legacy Qt/X11 dependencies.

## Inventory API

Milestone 2 adds a complete PostgreSQL-backed inventory API:

- Organizations own all catalog and inventory records.
- Products represent reusable catalog definitions and organization-scoped SKUs.
- Locations represent warehouses, stores, and storage areas.
- Batches are the core inventory unit, tracking product, location, quantities,
  receipt date, expiration date, lifecycle status, and notes.

All collection endpoints return an envelope containing `items`, `total`, `limit`,
and `offset`. The maximum page size is 200.

| Resource | Collection route | Available filters |
| --- | --- | --- |
| Organizations | `/api/v1/organizations` | `name`, `limit`, `offset` |
| Products | `/api/v1/products` | `organization_id`, `status`, `category`, `search`, pagination |
| Locations | `/api/v1/locations` | `organization_id`, `is_active`, `name`, pagination |
| Batches | `/api/v1/batches` | `organization_id`, `product_id`, `location_id`, `status`, `expiry_date`, `expires_from`, `expires_to`, pagination |

Each collection supports `POST` and `GET`. Individual resources support `GET`,
`PATCH`, and `DELETE` through `/{resource_id}` routes. Product and location deletion
is rejected while inventory batches still reference the resource.

## Identity, tenancy, and authorization

All versioned inventory and organization endpoints require an OIDC Bearer access token.
The API validates the token signature through the provider's JWKS endpoint and verifies
the configured issuer, audience, expiration, subject, and asymmetric signing algorithm.
Passwords are never accepted or stored by this application.

The first valid token for an OIDC subject provisions a local user profile. An authenticated
user may create an organization and automatically becomes its first owner. Additional users
must authenticate once before an administrator can grant membership using their verified
email address.

| Role | Read inventory | Manage inventory | Manage members | Delete organization |
| --- | --- | --- | --- | --- |
| `viewer` | Yes | No | No | No |
| `inventory_manager` | Yes | Yes | No | No |
| `admin` | Yes | Yes | Yes | No |
| `owner` | Yes | Yes | Yes | Yes |

Identity endpoints include:

- `GET /api/v1/me`
- `GET/POST /api/v1/organizations/{organization_id}/memberships`
- `PATCH/DELETE /api/v1/organizations/{organization_id}/memberships/{membership_id}`
- `GET /api/v1/organizations/{organization_id}/audit-events`

The API prevents removal or demotion of the final organization owner. Every inventory,
organization, and membership mutation records the authenticated actor and affected resource
in the same PostgreSQL transaction.

## Repository layout

```text
backend/
├── alembic/                 # Versioned database migrations
├── app/
│   ├── api/routes/          # FastAPI endpoint modules
│   ├── core/                # Environment configuration
│   ├── db/models/           # SQLAlchemy inventory models
│   ├── domain/              # Product and batch lifecycle values
│   ├── repositories/        # SQLAlchemy queries and pagination
│   ├── schemas/             # Documented Pydantic API contracts
│   ├── services/            # Inventory rules and transaction orchestration
│   └── main.py              # API composition root
├── tests/                   # Backend tests
├── alembic.ini
├── requirements.txt
└── requirements-dev.txt

src/                         # Transitional legacy PyQt application
Dockerfile                   # FastAPI production image
docker-compose.yml           # API, migration, and PostgreSQL services
```

## Start the backend with Docker

From the repository root:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

The development defaults also allow Compose to start without a `.env` file. Always
replace the sample password before deploying beyond a local workstation.

Once the stack is healthy:

- API documentation: http://localhost:8000/docs
- Liveness probe: http://localhost:8000/health
- Readiness probe: http://localhost:8000/ready
- Versioned API probe: http://localhost:8000/api/v1/health

Stop the services while retaining PostgreSQL data:

```powershell
docker compose down
```

Remove services and the development database volume:

```powershell
docker compose down --volumes
```

## Run the backend locally

Create and activate a virtual environment, then run from `backend/`:

```powershell
python -m pip install -r requirements-dev.txt
alembic upgrade head
python -m uvicorn app.main:app --reload
```

For local execution outside Docker, set `DATABASE_URL` to a PostgreSQL URL whose host
is `localhost` instead of the Compose service name `db`.

Run backend tests from `backend/`:

```powershell
python -m pytest -q
```

Or run them without installing Python dependencies on the host:

```powershell
docker compose --profile test run --build --rm test
```

The integration suite starts a separate PostgreSQL database using temporary memory-backed
storage, applies every Alembic migration, and exercises the API against the real database.
Remove the disposable dependency containers after a test run with:

```powershell
docker compose --profile test rm --stop --force test test-migrate test-db
```

## Migrations

Run migration commands from `backend/`:

```powershell
alembic current
alembic upgrade head
alembic revision --autogenerate -m "describe the schema change"
alembic downgrade -1
```

To deploy the inventory schema directly through Docker Compose:

```powershell
docker compose run --rm migrate alembic upgrade head
docker compose up -d --build api
```

The inventory schema is introduced by revision `20260623_0002`; identity, memberships,
role constraints, and audit events are introduced by `20260623_0003`. Verify the applied
revision with:

```powershell
docker compose exec db psql -U expiry_app -d expiry_notification -c "SELECT version_num FROM alembic_version;"
```

Application startup never calls `create_all`; deployed schema changes must pass through
reviewable Alembic revisions.

## Configuration

Copy `.env.example` to `.env` for local overrides. Relevant settings include:

- `APP_NAME`, `APP_VERSION`, and `APP_ENVIRONMENT`
- `LOG_LEVEL` and `API_V1_PREFIX`
- `DATABASE_URL`
- `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW`, and timeout settings
- PostgreSQL database, user, password, and exposed port
- `OIDC_ISSUER_URL`, `OIDC_AUDIENCE`, and `OIDC_JWKS_URL`
- `OIDC_ALGORITHMS` and `OIDC_JWKS_CACHE_SECONDS`

The `.env` file is ignored by Git. `.env.example` contains development-only examples.
Replace the placeholder OIDC values before attempting authenticated API calls. Swagger UI's
Authorize button accepts a Bearer access token issued for the configured API audience.

## Legacy desktop application

The previous PyQt client and its tests remain temporarily available:

```powershell
python Main.py
python -m unittest discover -v
```

It will be replaced with a web client after API and data-migration parity are complete.
