# Atlas

Atlas is an open-source Identity and Access Management (IAM) service for authentication, authorization, identity management, and access control.

The project is a FastAPI application backed by PostgreSQL. It includes user management, JWT access and refresh tokens, signing key rotation, audit logs, and login history.

## Quick start

The fastest way to run Atlas locally is Docker Compose:

```bash
docker compose up --build
```

Then open:

- API health check: `http://localhost:8000/`
- OpenAPI docs: `http://localhost:8000/docs`
- JWKS endpoint: `http://localhost:8000/auth/jwks`

Compose starts PostgreSQL, builds the API image, generates a development signing key if one does not exist, runs migrations, and seeds the configured admin user.

Development credentials are intentionally local-only:

- Username: `admin`
- Email: `admin@example.com`
- Password: `ChangeMe123!`

Change these before any shared or deployed environment.

## Local setup without Docker

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements-dev.txt
   ```

3. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

4. Start PostgreSQL and update the database URLs in `.env`.

5. Generate a local signing key:

   ```bash
   python -c "import utils; utils.AuthUtils.generate_new_signing_key(kid='atlas-local-dev-key')"
   ```

6. Run migrations:

   ```bash
   python migrate.py upgrade head
   ```

7. Start the API:

   ```bash
   uvicorn main:app --reload
   ```

## Tests

```bash
./run-tests.sh
```

## Documentation

- [Configuration](docs/configuration.md)
- [Development](docs/development.md)
- [API overview](docs/api.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Code of conduct](CODE_OF_CONDUCT.md)
- [Changelog](CHANGELOG.md)

## License

Atlas is licensed under the Apache License 2.0. See [LICENSE](LICENSE).
