# Administrator guide

## Database prerequisites

`geopublish` connects to an **existing** PostgreSQL server (version 12+)
with the ability to create the `postgis` and `postgis_raster` extensions.
It does not provision or manage the PostgreSQL server itself.

Required privileges for the configured `PGUSER`:

- `CREATE` on the target database (for `init-db`'s `CREATE EXTENSION`).
- `CREATE` on the target schema (default `public`) for publishing tables.

## Connection configuration

All connection details come from environment variables, loaded from a
gitignored `.env` (see `.env.example`):

| Variable | Required | Default |
|---|---|---|
| `PGHOST` | yes | — |
| `PGPORT` | yes | — |
| `PGDATABASE` | yes | — |
| `PGUSER` | yes | — |
| `PGPASSWORD` | no | empty |
| `PGSSLMODE` | no | `prefer` |

## QGIS service file

`config/pg_service.conf.example` is a template for a `PGSERVICEFILE` that
both `psql` and QGIS understand, so end users never type a password into
QGIS. Copy it to `config/pg_service.conf` (gitignored) and fill in real
values.
