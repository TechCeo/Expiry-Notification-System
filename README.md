# Expiry Notification System

The Expiry Notification System has been migrated from a single-user PyQt/SQLite
desktop application into a multi-user FastAPI, PostgreSQL, and React web platform.
The browser client is now the operational path; the legacy desktop application is
archived under `archive/legacy-pyqt/` for reference and migration history only.

## Current stack

- Backend: FastAPI, SQLAlchemy, Pydantic, Alembic, PostgreSQL
- Frontend: React, TypeScript, Vite, React Router, TanStack Query, React Hook Form, Zod
- Auth: OIDC Bearer tokens with Authorization Code + PKCE on the web client
- Runtime: Docker Compose with API, migrations, PostgreSQL, and web services

## Repository layout

```text
backend/
  alembic/                 # Versioned database migrations
  app/
    api/routes/            # FastAPI endpoint modules
    cli/                   # Operational CLIs, including legacy SQLite importer
    core/                  # Environment configuration and security helpers
    db/models/             # SQLAlchemy models
    domain/                # Lifecycle values and roles
    repositories/          # SQLAlchemy query layer
    schemas/               # Documented Pydantic API contracts
    services/              # Business rules and authorization orchestration
  tests/                   # Backend integration tests

frontend/
  src/                     # React TypeScript web client
  Dockerfile               # Nginx-served production build

archive/legacy-pyqt/      # Archived PyQt/SQLite desktop application
Dockerfile                # FastAPI production/test image
docker-compose.yml        # DB, migration, API, web, and test services
```

## Run the full application

From the repository root:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Local URLs:

- Web app: http://localhost:8080
- API docs: http://localhost:8000/docs
- Liveness: http://localhost:8000/health
- Readiness: http://localhost:8000/ready

If your network intercepts TLS certificates during local image builds, prefer installing
your organization/root CA. As a temporary local-only workaround:

```powershell
docker compose build --build-arg PIP_TRUSTED_HOST="pypi.org files.pythonhosted.org" --build-arg NPM_CONFIG_STRICT_SSL=false
```

Do not use those relaxed build settings in CI or production.

## Backend API

All versioned inventory endpoints require an OIDC Bearer access token. Health endpoints
remain public. The API validates token signature, issuer, audience, expiration, subject,
and asymmetric signing algorithm through the configured JWKS endpoint.

Core resources:

| Resource | Route | Notes |
| --- | --- | --- |
| Organizations | `/api/v1/organizations` | Tenant boundary and inventory owner |
| Products | `/api/v1/products` | Organization-scoped catalog and SKU |
| Locations | `/api/v1/locations` | Warehouses, shops, and storage areas |
| Batches | `/api/v1/batches` | Core inventory unit with quantity and expiry |
| Identity | `/api/v1/me` | Current user, memberships, and roles |

Collection endpoints return `items`, `total`, `limit`, and `offset`. Batch lists support
filters such as `organization_id`, `product_id`, `location_id`, `status`, `expiry_date`,
`expires_from`, and `expires_to`.

## Roles

| Role | Read inventory | Manage inventory | Manage members | Delete organization |
| --- | --- | --- | --- | --- |
| `viewer` | Yes | No | No | No |
| `inventory_manager` | Yes | Yes | No | No |
| `admin` | Yes | Yes | Yes | No |
| `owner` | Yes | Yes | Yes | Yes |

The API prevents removal or demotion of the final organization owner. Inventory,
organization, and membership mutations create audit events in the same PostgreSQL
transaction.

## Frontend

The React web client includes:

- Login and OIDC/PKCE callback handling
- Organization selection
- Inventory dashboard
- Product, location, and batch workflows
- Pagination and filtering
- Expiring-soon, expired, and depleted inventory views
- Responsive layouts
- Loading, empty, validation, and error states
- Role-aware write controls

Run locally from `frontend/`:

```powershell
npm install
npm run dev
```

Build and lint:

```powershell
npm run build
npm run lint
```

## Legacy SQLite importer

The importer is idempotent and supports dry-run mode, validation, duplicate prevention,
source/destination totals, and machine-readable JSON reports.

Supported legacy mappings:

```text
students.roll/mobile/sem/address -> Product + Batch
products.id/expiry_date/quantity/remarks -> Product + Batch
```

Dry-run against the local legacy DB through Docker:

```powershell
docker compose run --rm -v "${PWD}\database.db:/tmp/database.db:ro" api python -m app.cli.import_legacy_sqlite --source /tmp/database.db --source-table auto --organization-name "Legacy Import" --organization-slug legacy-import --location-name "Legacy Default Location" --location-code LEGACY --dry-run
```

Final import after testing a DB copy:

```powershell
docker compose run --rm -v "${PWD}\database.db:/tmp/database.db:ro" api python -m app.cli.import_legacy_sqlite --source /tmp/database.db --source-table auto --organization-name "Legacy Import" --organization-slug legacy-import --location-name "Legacy Default Location" --location-code LEGACY --report-path /tmp/legacy-import-report.json
```

If you want an existing authenticated user to own the imported organization, pass
`--owner-email someone@example.com`; that user must have authenticated once with a
verified OIDC email.

## Tests

Frontend:

```powershell
cd frontend
npm run lint
npm run build
```

Backend with disposable PostgreSQL:

```powershell
docker compose --profile test run --build --rm test sh -c "ruff check --no-cache app tests alembic && python -m pytest -q -p no:cacheprovider"
```

Clean up disposable test containers:

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

Application startup never calls `create_all`; deployed schema changes must pass through
reviewable Alembic revisions.

## Legacy archive

The old desktop client, PyQt dependencies, SQLite repository code, Plyer notifications,
icons, and legacy unit tests live in `archive/legacy-pyqt/`. They are no longer part of
the active runtime or production Docker artifacts.

`database.db` is intentionally ignored and removed from Git tracking. Keep a private copy
only long enough to validate and complete the PostgreSQL import.
