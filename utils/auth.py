from argon2 import PasswordHasher
import helpers
from typing import Any, Literal
from settings import AuthSettings
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64
from cryptography.hazmat.primitives.asymmetric import rsa
from pathlib import Path
from datetime import datetime, timezone, timedelta
import uuid
import json


class AuthUtils:
    KEY_STATUS_GENERATED = "generated"
    KEY_STATUS_ACTIVE = "active"
    KEY_STATUS_REVOKED = "revoked"
    ADMIN_ROLE = "admin"

    hasher = PasswordHasher()
    auth_settings = AuthSettings()

    @staticmethod
    def hash_password(password: str) -> str:
        return AuthUtils.hasher.hash(password=password)

    @staticmethod
    def verify_hash(hashed_password: str, compare_to: str) -> Literal[True]:
        try:
            return AuthUtils.hasher.verify(hashed_password, compare_to)

        except Exception as exc:
            raise helpers.Error("Invalid Password") from exc

    @staticmethod
    def _encode_uint(value: int) -> str:
        byte_length = (value.bit_length() + 7) // 8
        return base64.urlsafe_b64encode(value.to_bytes(byte_length, "big")).rstrip(b"=").decode("utf-8")

    @staticmethod
    def _build_jwk(public_key_pem: str, kid: str) -> dict:
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode("utf-8"),
            backend=default_backend(),
        )

        if not isinstance(public_key, rsa.RSAPublicKey):
            raise TypeError("Only RSA public keys are supported for JWKS")

        numbers = public_key.public_numbers()
        return {
            "kty": "RSA",
            "kid": kid,
            "use": "sig",
            "alg": AuthUtils.auth_settings.JWT_ALGORITHM,
            "n": AuthUtils._encode_uint(numbers.n),
            "e": AuthUtils._encode_uint(numbers.e),
        }

    @staticmethod
    def _key_record_from_files(private_path: Path, public_path: Path, kid: str) -> dict:
        if not private_path.exists():
            raise FileNotFoundError(f"Private key not found at {private_path}")
        if not public_path.exists():
            raise FileNotFoundError(f"Public key not found at {public_path}")
        return {
            "kid": kid,
            "private_key": private_path.read_text(encoding="utf-8"),
            "public_key": public_path.read_text(encoding="utf-8"),
            "updated_at": private_path.stat().st_mtime,
        }

    @staticmethod
    def _key_registry_path() -> Path:
        return AuthUtils.auth_settings.resolved_keys_dir / "key_registry.json"

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _load_key_registry() -> dict[str, Any]:
        registry_path = AuthUtils._key_registry_path()
        if registry_path.exists():
            return json.loads(registry_path.read_text(encoding="utf-8"))
        return {"keys": []}

    @staticmethod
    def _save_key_registry(registry: dict[str, Any]) -> dict[str, Any]:
        keys_dir = AuthUtils.auth_settings.resolved_keys_dir
        keys_dir.mkdir(parents=True, exist_ok=True)
        registry_path = AuthUtils._key_registry_path()
        registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True), encoding="utf-8")
        return registry

    @staticmethod
    def _sync_registry_with_files() -> dict[str, Any]:
        settings = AuthUtils.auth_settings
        keys_dir = settings.resolved_keys_dir
        key_records: list[dict] = []

        if keys_dir.exists():
            for private_path in keys_dir.glob("*.private.pem"):
                kid = private_path.name[: -len(".private.pem")]
                public_path = private_path.with_name(f"{kid}.public.pem")
                if public_path.exists():
                    key_records.append(
                        AuthUtils._key_record_from_files(
                            private_path=private_path,
                            public_path=public_path,
                            kid=kid,
                        ),
                    )

        key_records = sorted(key_records, key=lambda item: item["updated_at"])
        registry = AuthUtils._load_key_registry()
        entries_by_kid = {entry["kid"]: entry for entry in registry.get("keys", [])}

        legacy_bootstrap = not entries_by_kid

        for index, record in enumerate(key_records):
            entry = entries_by_kid.get(record["kid"])
            if entry is None:
                status = AuthUtils.KEY_STATUS_GENERATED
                activated_at = None
                if legacy_bootstrap and index == len(key_records) - 1:
                    status = AuthUtils.KEY_STATUS_ACTIVE
                    activated_at = AuthUtils._timestamp()

                entry = {
                    "kid": record["kid"],
                    "status": status,
                    "created_at": AuthUtils._timestamp(),
                    "activated_at": activated_at,
                    "revoked_at": None,
                }
                registry.setdefault("keys", []).append(entry)
                entries_by_kid[record["kid"]] = entry

            entry["private_key_path"] = str(keys_dir / f"{record['kid']}.private.pem")
            entry["public_key_path"] = str(keys_dir / f"{record['kid']}.public.pem")

        discovered_kids = {record["kid"] for record in key_records}
        registry["keys"] = [entry for entry in registry.get("keys", []) if entry["kid"] in discovered_kids]
        AuthUtils._save_key_registry(registry)
        return registry

    @staticmethod
    def _discover_key_records(include_non_active: bool = True) -> list[dict]:
        registry = AuthUtils._sync_registry_with_files()
        entries_by_kid = {entry["kid"]: entry for entry in registry.get("keys", [])}
        key_records: list[dict] = []

        for kid, entry in entries_by_kid.items():
            if not include_non_active and entry.get("status") != AuthUtils.KEY_STATUS_ACTIVE:
                continue

            private_path = Path(entry["private_key_path"])
            public_path = Path(entry["public_key_path"])
            record = AuthUtils._key_record_from_files(private_path=private_path, public_path=public_path, kid=kid)
            record["status"] = entry.get("status")
            record["created_at"] = entry.get("created_at")
            record["activated_at"] = entry.get("activated_at")
            record["revoked_at"] = entry.get("revoked_at")
            key_records.append(record)

        return sorted(key_records, key=lambda item: item["updated_at"])

    @staticmethod
    def get_latest_key_record() -> dict:
        key_records = AuthUtils._discover_key_records(include_non_active=False)
        if not key_records:
            raise helpers.Error("No active signing keys available", status_code=500)
        return key_records[-1]

    @staticmethod
    def get_jwks() -> dict:
        keys = [
            AuthUtils._build_jwk(public_key_pem=record["public_key"], kid=record["kid"])
            for record in AuthUtils._discover_key_records(include_non_active=False)
        ]
        return {"keys": keys}

    @staticmethod
    def issue_token(subject: str, token_type: str, expires_delta: timedelta, extra_claims: dict | None = None) -> str:
        key_record = AuthUtils.get_latest_key_record()
        now = datetime.now(timezone.utc)
        payload = {
            "sub": subject,
            "type": token_type,
            "iat": now,
            "exp": now + expires_delta,
        }
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(
            payload=payload,
            key=key_record["private_key"],
            algorithm=AuthUtils.auth_settings.JWT_ALGORITHM,
            headers={"kid": key_record["kid"]},
        )

    @staticmethod
    def resolve_access_claims(user: Any | None = None, subject: str | None = None) -> dict:
        meta = getattr(user, "meta", {}) or {}
        roles = meta.get("roles")
        if roles is None:
            role = meta.get("role")
            roles = [role] if role else []
        elif not isinstance(roles, list):
            roles = [str(roles)]

        normalized_roles = sorted({str(role).lower() for role in roles if role})
        claims = {"roles": normalized_roles}
        if normalized_roles:
            claims["role"] = normalized_roles[0]

        subject_value = subject or getattr(user, "user_name", None)
        if AuthUtils.ADMIN_ROLE in normalized_roles:
            claims["is_admin"] = True
        elif subject_value and subject_value == "SUPER_USER":
            claims["is_admin"] = False

        return claims

    @staticmethod
    def issue_token_pair(
        subject: str,
        access_claims: dict | None = None,
        refresh_claims: dict | None = None,
    ) -> dict:
        access_token = AuthUtils.issue_token(
            subject=subject,
            token_type="access",
            expires_delta=timedelta(minutes=AuthUtils.auth_settings.ACCESS_TOKEN_TTL_MINUTES),
            extra_claims=access_claims,
        )
        refresh_token = AuthUtils.issue_token(
            subject=subject,
            token_type="refresh",
            expires_delta=timedelta(days=AuthUtils.auth_settings.REFRESH_TOKEN_TTL_DAYS),
            extra_claims=refresh_claims,
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    @staticmethod
    def verify_token(token: str, expected_type: str | None = None) -> dict:
        key_records = AuthUtils._discover_key_records(include_non_active=False)
        keys_by_kid = {record["kid"]: record["public_key"] for record in key_records}

        try:
            headers = jwt.get_unverified_header(token)
        except jwt.InvalidTokenError as exc:
            raise helpers.Error("Invalid token header", status_code=401) from exc

        kid = headers.get("kid")
        if kid:
            public_key = keys_by_kid.get(kid)
            if not public_key:
                raise helpers.Error("Signing key is not active", status_code=401)
            try:
                payload = jwt.decode(
                    token,
                    key=public_key,
                    algorithms=[AuthUtils.auth_settings.JWT_ALGORITHM],
                )
            except jwt.PyJWTError as exc:
                raise helpers.Error("Invalid or expired token", status_code=401) from exc
        else:
            payload = None
            for public_key in keys_by_kid.values():
                try:
                    payload = jwt.decode(
                        token,
                        key=public_key,
                        algorithms=[AuthUtils.auth_settings.JWT_ALGORITHM],
                    )
                    break
                except jwt.PyJWTError:
                    continue
            if payload is None:
                raise helpers.Error("Invalid or expired token", status_code=401)

        token_type = payload.get("type")
        if expected_type and token_type != expected_type:
            raise helpers.Error(f"Invalid token type: expected {expected_type}", status_code=401)
        return payload

    @staticmethod
    def generate_signing_key(kid: str | None = None) -> dict:
        settings = AuthUtils.auth_settings
        keys_dir = settings.resolved_keys_dir
        keys_dir.mkdir(parents=True, exist_ok=True)

        generated_kid = kid or f"key-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        private_path = keys_dir / f"{generated_kid}.private.pem"
        public_path = keys_dir / f"{generated_kid}.public.pem"

        if private_path.exists() or public_path.exists():
            raise helpers.Error("Key id already exists", status_code=409)

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend(),
        )
        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        private_path.write_text(private_pem, encoding="utf-8")
        public_path.write_text(public_pem, encoding="utf-8")

        registry = AuthUtils._load_key_registry()
        registry.setdefault("keys", []).append(
            {
                "kid": generated_kid,
                "private_key_path": str(private_path),
                "public_key_path": str(public_path),
                "status": AuthUtils.KEY_STATUS_GENERATED,
                "created_at": AuthUtils._timestamp(),
                "activated_at": None,
                "revoked_at": None,
            }
        )
        AuthUtils._save_key_registry(registry)

        return {
            "kid": generated_kid,
            "private_key_path": str(private_path),
            "public_key_path": str(public_path),
            "status": AuthUtils.KEY_STATUS_GENERATED,
        }

    @staticmethod
    def activate_signing_key(kid: str) -> dict:
        registry = AuthUtils._sync_registry_with_files()
        target_entry = None
        now = AuthUtils._timestamp()

        for entry in registry.get("keys", []):
            if entry["kid"] == kid:
                target_entry = entry
            elif entry.get("status") == AuthUtils.KEY_STATUS_ACTIVE:
                entry["status"] = AuthUtils.KEY_STATUS_REVOKED
                entry["revoked_at"] = now

        if target_entry is None:
            raise helpers.Error("Signing key not found", status_code=404)
        if target_entry.get("status") == AuthUtils.KEY_STATUS_REVOKED:
            raise helpers.Error("Revoked signing key cannot be reactivated", status_code=409)

        target_entry["status"] = AuthUtils.KEY_STATUS_ACTIVE
        target_entry["activated_at"] = now
        target_entry["revoked_at"] = None
        AuthUtils._save_key_registry(registry)
        return target_entry

    @staticmethod
    def revoke_signing_key(kid: str) -> dict:
        registry = AuthUtils._sync_registry_with_files()
        target_entry = None

        for entry in registry.get("keys", []):
            if entry["kid"] == kid:
                target_entry = entry
                break

        if target_entry is None:
            raise helpers.Error("Signing key not found", status_code=404)

        target_entry["status"] = AuthUtils.KEY_STATUS_REVOKED
        target_entry["revoked_at"] = AuthUtils._timestamp()
        AuthUtils._save_key_registry(registry)
        return target_entry

    @staticmethod
    def generate_new_signing_key(kid: str | None = None) -> dict:
        key_data = AuthUtils.generate_signing_key(kid=kid)
        activated = AuthUtils.activate_signing_key(key_data["kid"])
        key_data["status"] = activated["status"]
        key_data["activated_at"] = activated["activated_at"]
        return key_data
