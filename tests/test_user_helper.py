from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import helpers


def test_user_helper_normalizes_status_and_serializes():
    helper = helpers.UserHelper(
        id=uuid4(),
        name="John",
        user_name="john",
        password="hashed",
        email="john@example.com",
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deactivated=False,
        meta={"team": "auth"},
    )

    payload = helper.to_dict()

    assert payload["status"] == "ACTIVE"
    assert payload["meta"] == {"team": "auth"}


def test_user_helper_from_model_maps_fields():
    model = SimpleNamespace(
        id=uuid4(),
        name="Jane",
        user_name="jane",
        password="hashed",
        email="jane@example.com",
        deactivated=False,
        meta={},
        status="ACTIVE",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    helper = helpers.UserHelper.from_model(model)

    assert helper.user_name == "jane"
    assert helper.status == helpers.STATUS.ACTIVE
