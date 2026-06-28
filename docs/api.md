# API Overview

Atlas exposes a FastAPI application.

## Health

- `GET /` returns a simple health response.

## Authentication

- `GET /auth/` checks the auth router.
- `GET /auth/jwks` returns active public signing keys.
- `POST /auth/login` exchanges user credentials for access and refresh tokens.
- `POST /auth/refresh` exchanges a refresh token for a new token pair.
- `POST /auth/logout` revokes one refresh session.
- `POST /auth/logout-all` revokes all refresh sessions for the authenticated user.
- `POST /auth/keys/rotate` creates and activates a new signing key. Requires admin access.

## Admin

- `GET /admin/audit-logs` returns audit log entries. Requires admin access.
- `GET /admin/login-history` returns login history entries. Requires admin access.

Interactive OpenAPI documentation is available at `http://localhost:8000/docs` when the app is running.
