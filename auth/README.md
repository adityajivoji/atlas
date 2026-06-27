# Authenticator Integration Guide

This repository acts as the authentication service for other applications.

## What This Service Does

- Creates users: `POST /auth/signup`
- Authenticates users: `POST /auth/login`
- Issues JWT access and refresh tokens signed with rotating RSA keys (`kid`)
- Exposes verification keys as JWKS: `GET /auth/jwks`
- Stores governance data: audit logs and login history

Other apps should verify those tokens using the matching `public.pem`.

## Base URL

- Local: `http://localhost:8000`
- Auth routes are under: `/auth`

## Endpoints

### `POST /auth/signup`

Creates a user.

Request body:

```json
{
  "name": "John Doe",
  "user_name": "john_doe",
  "email": "john@example.com",
  "password": "Strong@123",
  "meta": {}
}
```

Validation:

- `email` must match a standard email format.
- `password` must be at least 8 chars and include:
  - 1 lowercase letter
  - 1 uppercase letter
  - 1 digit
  - 1 special character

### `POST /auth/login`

Authenticates a user and returns an access token.

Request body:

```json
{
  "email": "john@example.com",
  "password": "Strong@123"
}
```

or

```json
{
  "user_name": "john_doe",
  "password": "Strong@123"
}
```

Response body:

```json
{
  "message": "Login Successful",
  "data": {
    "access_token": "<JWT>",
    "refresh_token": "<JWT>",
    "token_type": "bearer"
  },
  "status_code": 200,
  "error": null,
  "error_description": null
}
```

### `POST /auth/refresh`

Exchanges a valid refresh token for a new access/refresh token pair.

Request body:

```json
{
  "refresh_token": "<JWT>"
}
```

### `GET /auth/jwks`

Returns JSON Web Key Set used by consumer apps to verify RS256 tokens.
When keys are rotated, multiple active public keys are returned.

Response body:

```json
{
  "keys": [
    {
      "kty": "RSA",
      "kid": "auth-service-key-1",
      "use": "sig",
      "alg": "RS256",
      "n": "<modulus>",
      "e": "<exponent>"
    }
  ]
}
```

## JWT Details

- Algorithm: `RS256`
- Signed with: latest key in keyring (`*.private.pem`)
- Verified with: matching public keys from JWKS (`*.public.pem`)
- Current claims include:
  - `sub` (username)
  - `type` (`access` or `refresh`)
  - `iat`
  - `exp` (expiry based on configured TTLs)

## Admin Governance Endpoints

All admin routes require an admin access token (`Authorization: Bearer <token>`).

- `GET /admin/audit-logs`
  - Query params: `limit`, `actor_user_name`, `action`
- `GET /admin/login-history`
  - Query params: `limit`, `user_name`, `success`

`POST /auth/keys/rotate` is also admin protected and records an audit event.

## How Other Apps Should Integrate

1. Client logs in against this authenticator (`/auth/login`) and gets JWT.
2. Client sends `Authorization: Bearer <token>` to your app.
3. Your app verifies token signature using `public.pem` or `/auth/jwks`.
4. Your app reads claims (`sub`, `exp`) and authorizes request.

## FastAPI Consumer Snippet

Use this in another FastAPI app that consumes tokens from this authenticator.

```python
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt import InvalidTokenError

ALGORITHM = "RS256"
PUBLIC_KEY = Path("./public.pem").read_text(encoding="utf-8")

app = FastAPI()
bearer = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject",
            )
        return payload
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


@app.get("/protected")
def protected_route(claims: dict = Depends(get_current_user)):
    return {"ok": True, "claims": claims}
```

## FastAPI Consumer Snippet (JWKS URL)

Use this if you want runtime key discovery from the authenticator service.

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt import InvalidTokenError, PyJWKClient

ALGORITHM = "RS256"
JWKS_URL = "http://localhost:8000/auth/jwks"

app = FastAPI()
bearer = HTTPBearer(auto_error=True)
jwk_client = PyJWKClient(JWKS_URL)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
):
    token = credentials.credentials
    try:
        signing_key = jwk_client.get_signing_key_from_jwt(token).key
        payload = jwt.decode(token, signing_key, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject",
            )
        return payload
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
```

## Operational Notes

- Keep `private.pem` only in this authenticator service.
- Share `public.pem` with consumer services via a secure channel.
- Rotate keys by replacing both key files and redeploying services.
- Never commit private keys to source control.
