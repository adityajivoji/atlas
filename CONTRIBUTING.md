# Contributing to Atlas

Thanks for helping improve Atlas. This project is intended to be easy to run locally and straightforward to review.

## Development setup

1. Fork and clone the repository.
2. Copy `.env.example` to `.env` and adjust values as needed.
3. Create a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

4. Install dependencies:

   ```bash
   pip install -r requirements-dev.txt
   ```

5. Start PostgreSQL locally or use Docker Compose:

   ```bash
   docker compose up --build
   ```

6. Run tests:

   ```bash
   ./run-tests.sh
   ```

## Pull requests

- Keep pull requests focused on one behavioral change.
- Add or update tests when changing application behavior.
- Update documentation when setup, configuration, or API behavior changes.
- Do not commit secrets, private keys, generated key registries, local `.env` files, or database data.

## Code style

The codebase currently uses plain `pytest` and FastAPI conventions without a separate formatter configuration. Prefer small, readable functions and follow the existing module layout.

## Reporting issues

For bugs, include reproduction steps, expected behavior, actual behavior, and relevant logs. For security issues, do not open a public issue; follow `SECURITY.md`.
