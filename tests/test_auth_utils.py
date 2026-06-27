import os
import time
from datetime import timedelta

import jwt
import pytest

import helpers
import utils


def test_generate_new_signing_key_creates_private_and_public_files():
    key_data = utils.AuthUtils.generate_new_signing_key("utils-key-1")

    assert key_data["kid"] == "utils-key-1"
    assert os.path.exists(key_data["private_key_path"])
    assert os.path.exists(key_data["public_key_path"])
    assert key_data["status"] == "active"


def test_get_jwks_contains_all_public_keys():
    utils.AuthUtils.generate_signing_key("utils-kid-a")
    utils.AuthUtils.generate_signing_key("utils-kid-b")
    utils.AuthUtils.activate_signing_key("utils-kid-a")
    utils.AuthUtils.activate_signing_key("utils-kid-b")

    jwks = utils.AuthUtils.get_jwks()
    kids = {entry["kid"] for entry in jwks["keys"]}

    assert kids == {"utils-kid-b"}


def test_issue_token_pair_and_verify_both_token_types():
    utils.AuthUtils.generate_new_signing_key("utils-issue")

    token_pair = utils.AuthUtils.issue_token_pair("john")

    access_payload = utils.AuthUtils.verify_token(token_pair["access_token"], expected_type="access")
    refresh_payload = utils.AuthUtils.verify_token(token_pair["refresh_token"], expected_type="refresh")

    assert access_payload["sub"] == "john"
    assert refresh_payload["sub"] == "john"


def test_verify_token_rejects_unknown_kid():
    utils.AuthUtils.generate_new_signing_key("utils-unknown")
    key_record = utils.AuthUtils.get_latest_key_record()

    forged = jwt.encode(
        payload={"sub": "john", "type": "access", "exp": 9999999999},
        key=key_record["private_key"],
        algorithm=utils.AuthUtils.auth_settings.JWT_ALGORITHM,
        headers={"kid": "does-not-exist"},
    )

    with pytest.raises(helpers.Error, match="not active"):
        utils.AuthUtils.verify_token(forged)


def test_verify_token_rejects_wrong_expected_type():
    utils.AuthUtils.generate_new_signing_key("utils-type")
    token = utils.AuthUtils.issue_token("john", "access", timedelta(minutes=5))

    with pytest.raises(helpers.Error, match="Invalid token type"):
        utils.AuthUtils.verify_token(token, expected_type="refresh")


def test_get_latest_key_record_prefers_newer_key():
    first = utils.AuthUtils.generate_new_signing_key("utils-old")
    second = utils.AuthUtils.generate_new_signing_key("utils-new")

    old_ts = time.time() - 300
    os.utime(first["private_key_path"], (old_ts, old_ts))

    latest = utils.AuthUtils.get_latest_key_record()

    assert latest["kid"] == second["kid"]


def test_revoked_signing_key_no_longer_validates_tokens():
    utils.AuthUtils.generate_new_signing_key("utils-old-active")
    old_token = utils.AuthUtils.issue_token("john", "access", timedelta(minutes=5))
    utils.AuthUtils.generate_new_signing_key("utils-new-active")

    with pytest.raises(helpers.Error, match="not active"):
        utils.AuthUtils.verify_token(old_token)
