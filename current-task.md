# Current Task

Purpose: handoff file for future agents working on auth hardening and governance features in this repo.

Last updated: 2026-03-15
Status legend:
- `TODO`: not started
- `IN PROGRESS`: partially designed or partially implemented
- `DONE`: completed and verified enough for current scope
- `BLOCKED`: cannot proceed without user decision / env support

## Context

Recent review identified these concrete issues:

1. Refresh tokens can still be used after user disable/delete because refresh is validated purely from JWT claims.
2. "Key rotation" only adds keys; old signing keys remain trusted forever.
3. Login leaks account existence via distinct failure messages.
4. Login request schema incorrectly enforces password complexity policy.
5. Error responses expose raw internal exception strings.
6. CORS / trusted-host middleware is effectively open.
7. Admin authorization is based on username equality, not roles/claims.
8. Existing access tokens remain valid until expiry after user revocation.

Important constraint / design note from user:
- Keep access token revocation strategy stateless by using short access-token TTL.
- Target shape: `access token ~= 5-15 min`, `refresh token ~= 30 days`.
- Example accepted by user: `access = 10 min`, `refresh = 30 days`.

## Proposed Work Plan

### Task 1: Create a safe handoff file
- Status: `DONE`
- Notes:
  - This file exists specifically so future agents can resume work without rereading the whole repo history.

### Task 2: Fix login validation bug
- Status: `DONE`
- Scope:
  - Remove password-complexity validation from login schema.
  - Require only presence / minimum sanity for login password.
  - Keep complexity validation for signup and password-change flows.
- Target files:
  - `schemas/user.py`
- Notes:
  - This is a behavioral regression risk, not just cleanup.
  - Completed on 2026-03-15.
  - `UserLogin.password` no longer reuses signup password-policy validation.

### Task 3: Prevent account enumeration in login
- Status: `DONE`
- Scope:
  - Make "user not found" and "wrong password" return same client-visible response.
  - Prefer `401 Invalid credentials`.
  - Preserve detailed reason only in logs / governance records.
- Target files:
  - `services/auth.py`
  - potentially `routers/auth.py`
- Notes:
  - Avoid leaking identifier validity by message, status code, or timing where practical.
  - Completed on 2026-03-15.
  - Implemented uniform `401 Invalid credentials`.
  - Added a dummy password-hash path so missing-user and wrong-password paths are closer in behavior.

### Task 4: Sanitize unhandled error responses
- Status: `DONE`
- Scope:
  - Stop returning `str(exception)` for unexpected failures.
  - Return generic 500 payload for non-domain exceptions.
  - Keep detailed trace in logs only.
- Target files:
  - `utils/misc.py`
  - optionally add centralized exception handlers in app bootstrap
- Notes:
  - Expected business/domain errors can remain explicit if intentionally surfaced.
  - Completed on 2026-03-15.
  - Non-domain exceptions now return `Internal Server Error` instead of raw exception strings.

### Task 5: Tighten CORS and Trusted Host config
- Status: `DONE`
- Scope:
  - Replace wildcard CORS with explicit configured origins.
  - Keep `allow_credentials=True` only with non-wildcard origins.
  - Replace `allowed_hosts=["*"]` with env-driven host allowlist.
- Target files:
  - `main.py`
  - settings module(s), probably new config fields
- Notes:
  - Need reasonable dev defaults without opening production config.
  - Completed on 2026-03-15.
  - Added `AppSettings` with env-driven `CORS_ALLOWED_ORIGINS` and `ALLOWED_HOSTS`.
  - Default hosts include `testserver` so local TestClient usage still works.

### Task 6: Access token revocation strategy
- Status: `DONE`
- Current decision:
  - Use short-lived access tokens instead of building server-side access-token revocation.
  - Recommended TTL: `10 minutes`.
- Scope:
  - Confirm/update settings defaults to short access TTL.
  - Document security model: revoked/deactivated users may retain access until access token expiry; refresh must be blocked immediately.
  - Ensure any privileged / admin paths rely on access tokens with short TTL.
- Target files:
  - `settings/auth.py`
  - `utils/auth.py`
  - documentation/tests
- Notes:
  - This is intentionally stateless for access tokens.
  - Immediate revocation is achieved via blocking refresh + short access token lifetime.
  - Completed on 2026-03-15.
  - Default `ACCESS_TOKEN_TTL_MINUTES` updated from `15` to `10`.

### Task 7: Refresh token hardening
- Status: `DONE`
- Preferred solution:
  - Add refresh-session persistence with `jti`, `user_id`, expiry, revoked flag, optional device metadata.
  - Rotate refresh token on each refresh.
  - Revoke old refresh token/session on successful rotation.
- Minimum acceptable interim solution:
  - During refresh, load the user from DB and reject if missing, deactivated, or inactive.
- Target files:
  - `services/auth.py`
  - `utils/auth.py`
  - new model/repository/migration files likely needed
- Notes:
  - Minimum fix addresses disabled-user refresh.
  - Full solution addresses theft/replay and selective logout.
  - Interim safeguard completed on 2026-03-15:
    - refresh now reloads the user by token subject
    - refresh is rejected if the user is missing, deactivated, or not `ACTIVE`
  - Completed on 2026-03-15.
  - Added persisted `refresh_session` records with:
    - `id` used as refresh-token `jti`
    - `user_id`
    - `user_name`
    - `expires_at`
    - `revoked`
    - `revoked_at`
    - `revoked_reason`
    - `replaced_by_session_id`
  - Login now creates a persisted refresh session before issuing the refresh token.
  - Refresh now requires a valid persisted session, rejects revoked/missing sessions, rotates to a new session, and revokes the previous one with reason `rotated`.
  - Added logout endpoints:
    - `POST /auth/logout` revokes the provided refresh session for the authenticated access-token subject
    - `POST /auth/logout-all` revokes all refresh sessions for the authenticated user
  - `logout-all` derives the user from the authenticated access token rather than client-supplied identifiers.
  - Added Alembic migration `f0f1a2b3c4d5_add_refresh_sessions.py`.

### Task 8: Real signing-key lifecycle management
- Status: `DONE`
- Scope:
  - Separate "generate key" from "activate key" and "revoke key".
  - Track key state (DB table or metadata registry).
  - JWKS should expose only active keys.
  - Verification should reject revoked keys, except optional bounded overlap window if explicitly desired.
- Target files:
  - `utils/auth.py`
  - `routers/auth.py`
  - new persistence + migration work
- Notes:
  - Current implementation is additive rollover, not revocation-capable rotation.
  - If incident response is a requirement, revocation semantics are mandatory.
  - Completed on 2026-03-15.
  - Implemented a metadata-backed key registry in the keys directory (`key_registry.json`).
  - Added explicit `generate`, `activate`, and `revoke` operations in `AuthUtils`.
  - Added admin routes:
    - `POST /auth/keys/generate`
    - `POST /auth/keys/activate`
    - `POST /auth/keys/revoke`
  - Existing `POST /auth/keys/rotate` now remains as a convenience wrapper that generates and activates a new key.
  - Activation immediately revokes the previously active key, so JWKS exposes only the current active key and tokens signed with older keys stop validating immediately.

### Task 9: Replace username-based admin check with roles/claims
- Status: `DONE`
- Scope:
  - Stop granting admin access solely because `sub == SUPER_USER_USER_NAME`.
  - Add admin role/claim in issued access tokens or load role from DB.
  - Update admin dependency accordingly.
- Target files:
  - `services/governance.py`
  - `utils/auth.py`
  - user model / seed strategy if roles are persisted
- Notes:
  - Current approach is brittle and not extensible.
  - Completed on 2026-03-15.
  - Access tokens now carry role claims derived from `user.meta`.
  - Admin access now requires the `admin` role claim rather than matching a configured username.
  - Super-user DB seeding now writes `meta={"role": "admin"}` so seeded bootstrap admin accounts receive the claim.

### Task 10: Add coverage for the security-critical cases
- Status: `DONE`
- Scope:
  - login returns uniform invalid-credentials response
  - login schema accepts legacy-but-correct passwords
  - unexpected exceptions do not leak internal strings
  - refresh denied for deactivated/missing user
  - refresh rotation / revocation behavior if implemented
  - revoked old signing key no longer validates tokens
  - admin auth requires proper role/claim
  - CORS/host config behavior at least unit-tested where feasible
- Target files:
  - `tests/`
- Notes:
  - Added/updated tests for:
    - uniform login invalid-credentials behavior
    - login acceptance of legacy-format passwords
    - generic 500 error payloads
    - refresh rejection for missing/deactivated users
    - refresh rejection for revoked / missing-`jti` sessions
    - refresh-session rotation and replay resistance behavior
    - `POST /auth/logout`
    - `POST /auth/logout-all`
    - signing-key lifecycle behavior:
      - only active keys appear in JWKS
      - old tokens stop validating after key activation rotates trust
      - generate/activate/revoke endpoints
    - admin auth requires `admin` role claim
    - access tokens issued by login/refresh include expected role claims
    - super-user seeding assigns admin role metadata
    - `AppSettings` CSV/env parsing for `CORS_ALLOWED_ORIGINS` and `ALLOWED_HOSTS`
    - request-level CORS behavior for allowed and disallowed origins on the real app
    - trusted-host rejection for disallowed `Host` headers on the real app
  - Added test-runner support changes:
    - `tests/conftest.py` now uses a precreated writable temp root instead of `tmp_path`
    - `pytest.ini` now limits collection to `tests/` so temp directories in repo root are not collected as tests
  - Remaining test work:
    - none required for current scope beyond future feature additions.

### Task 11: Run and verify test suite
- Status: `DONE`
- Notes:
  - Verified on 2026-03-15 with:
    - `conda run -n auth python -m pytest -q`
  - Result:
    - `66 passed, 4 warnings in 4.38s`
  - Remaining warnings are Pydantic v2 deprecation warnings for class-based `Config` in settings modules.

## Suggested Execution Order

1. Task 2: fix login schema
2. Task 3: unify login failure behavior
3. Task 4: sanitize error responses
4. Task 5: tighten middleware config
5. Task 6: lock in short access-token TTL and document revocation model
6. Task 7: harden refresh flow
7. Task 8: implement real signing-key lifecycle
8. Task 9: replace username-only admin auth
9. Task 10: expand tests
10. Task 11: run verification

## Agent Notes

- Explicit next step for next agent:
  - Main remaining cleanup item is the Pydantic v2 settings deprecation warnings, or any future expansion such as device metadata / selective session management UI.
- Tests were re-verified in this environment on 2026-03-15.
- Minimal direct sanity checks were executed for:
  - superseded by full pytest run on 2026-03-15 (`50 passed`)
- Be careful with existing uncommitted changes in the repo.
- Prefer small, reviewable steps: implement one hardening area, add tests, then update this file.
- When progress happens, update status inline here and leave short notes describing what changed and what remains.
