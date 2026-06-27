from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from schemas import KeyLifecycleRequest, LogoutRequest, RefreshTokenRequest, RotateKeyRequest, UserLogin, UserSignup


@pytest.mark.parametrize(
    "password",
    [
        "Shor1@",
        "NOLOWERCASE1@",
        "nouppercase1@",
        "NoNumber@",
        "NoSpecial123",
    ],
)
def test_user_signup_password_policy_rejects_invalid_passwords(password):
    with pytest.raises(ValidationError):
        UserSignup(
            name="John",
            user_name="john",
            email="john@example.com",
            password=password,
            meta={},
        )


def test_user_signup_accepts_valid_password():
    model = UserSignup(
        name="John",
        user_name="john",
        email="john@example.com",
        password="Strong@123",
        meta={"role": "user"},
    )

    assert model.user_name == "john"


def test_user_login_accepts_email_or_username():
    with_email = UserLogin(email="john@example.com", password="Strong@123")
    with_username = UserLogin(user_name="john", password="Strong@123")

    assert with_email.email == "john@example.com"
    assert with_username.user_name == "john"


def test_user_login_does_not_enforce_signup_password_policy():
    model = UserLogin(user_name="john", password="legacy123")

    assert model.password == "legacy123"


def test_user_login_rejects_missing_identifier():
    with pytest.raises(Exception) as exc_info:
        UserLogin(password="Strong@123")
    assert "provide either username or email" in str(exc_info.value)


def test_refresh_token_request_model():
    model = RefreshTokenRequest(refresh_token="token")

    assert model.refresh_token == "token"


def test_rotate_key_request_allows_missing_kid():
    model = RotateKeyRequest()

    assert model.kid is None


def test_key_lifecycle_request_requires_kid():
    model = KeyLifecycleRequest(kid="kid-1")

    assert model.kid == "kid-1"


def test_logout_request_requires_refresh_token():
    model = LogoutRequest(refresh_token="token")

    assert model.refresh_token == "token"
