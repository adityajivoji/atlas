# Development

## Run with Docker Compose

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`. Compose also starts PostgreSQL, generates a development signing key if needed, runs migrations, and seeds the configured admin user on API startup.

Stop the stack with:

```bash
docker compose down
```

Remove generated database and key volumes with:

```bash
docker compose down -v
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python -c "import utils; utils.AuthUtils.generate_new_signing_key(kid='atlas-local-dev-key')"
python migrate.py upgrade head
uvicorn main:app --reload
```

You need a PostgreSQL database matching the URLs in `.env`.

## Tests

```bash
./run-tests.sh
```

or:

```bash
python -m pytest -q
```
