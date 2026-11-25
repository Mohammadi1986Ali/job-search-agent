# Job Search Agent

Netherlands graduate and early-career job discovery. Phase 1 implements the editable company registry; no crawler or fabricated vacancies yet.

## Start (Docker Desktop)

```sh
docker compose up --build -d
```

Open http://localhost:8000/docs to add, list, edit, disable and archive companies. The API is bound to localhost only. PostgreSQL data persists in the jobdata volume. Local development credentials are not suitable for public deployment.

## Run tests

```sh
docker compose run --rm api python -m pytest -q
```

Tests use temporary SQLite databases. PostgreSQL integration testing and Alembic migrations remain to be implemented; initial schema is created at startup.

## Stop

```sh
docker compose down
```

Do not use `-v` unless you intend to erase database contents. The next milestone is the company management web interface and CSV/Excel import/export.
