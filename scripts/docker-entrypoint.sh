#!/usr/bin/env bash
set -euo pipefail

python - <<'PY'
import utils

settings = utils.AuthUtils.auth_settings
keys_dir = settings.resolved_keys_dir
keys_dir.mkdir(parents=True, exist_ok=True)

if not list(keys_dir.glob("*.private.pem")):
    utils.AuthUtils.generate_new_signing_key(kid=settings.DEFAULT_KID)
PY

python migrate.py upgrade head

exec "$@"
