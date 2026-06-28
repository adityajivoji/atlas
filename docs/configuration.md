# Configuration

Atlas reads configuration from environment variables and, for local development, a `.env` file.

Copy `.env.example` to `.env` before running the app without Docker Compose.

## Required variables

| Variable | Purpose |
| --- | --- |
| `POSTGRES_DB_URL` | Async SQLAlchemy database URL used by the running API. |
| `POSTGRES_MIGRATION_URL` | Sync SQLAlchemy database URL used by Alembic migrations. |
| `JWT_ALGORITHM` | JWT signing algorithm. Use `RS256`. |
| `KEYS_DIR` | Directory where local signing keys and key registry files are stored. |
| `SUPER_USER_ID` | UUID for the seeded admin user. |
| `SUPER_USER_NAME` | Display name for the seeded admin user. |
| `SUPER_USER_USER_NAME` | Username for the seeded admin user. |
| `SUPER_USER_PASSWORD` | Password for the seeded admin user. |
| `SUPER_USER_EMAIL` | Email for the seeded admin user. |

## Optional variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `DEFAULT_KID` | `auth-service-key-1` | Key id used when bootstrapping a signing key. |
| `ACCESS_TOKEN_TTL_MINUTES` | `10` | Access token lifetime. |
| `REFRESH_TOKEN_TTL_DAYS` | `30` | Refresh token lifetime. |
| `CORS_ALLOWED_ORIGINS` | Local development origins | Comma-separated allowed CORS origins. |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated trusted hosts. |

## Signing keys

Docker Compose generates a development signing key automatically when the key volume is empty. For manual local development, create a key before issuing tokens:

```bash
python -c "import utils; utils.AuthUtils.generate_new_signing_key(kid='atlas-local-dev-key')"
```

Keep generated private keys out of git.
