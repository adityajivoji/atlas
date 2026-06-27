import asyncio
import json
from datetime import datetime, timezone
from uuid import uuid4

import helpers
import utils


class ObjWithToDict:
    def to_dict(self):
        return {
            "id": str(uuid4()),
            "when": datetime(2026, 1, 1, tzinfo=timezone.utc),
        }


class GoodRequest:
    async def json(self):
        return {"ok": True}


class BadRequest:
    async def json(self):
        raise ValueError("no body")


def test_serialize_data_handles_objects_with_to_dict():
    payload = utils.MiscUtils.serialize_data(ObjWithToDict())

    assert "id" in payload
    assert "when" in payload


def test_api_response_wraps_success_payload():
    response = utils.MiscUtils.api_response("done", data={"x": 1}, status_code=201)
    body = json.loads(response.body)

    assert response.status_code == 201
    assert body["message"] == "done"
    assert body["data"] == {"x": 1}


def test_error_response_maps_helpers_error():
    err = helpers.Error("bad request", status_code=400, details={"field": "email"})

    response = utils.MiscUtils.error_response(err)
    body = json.loads(response.body)

    assert response.status_code == 400
    assert body["error"] == "bad request"
    assert body["error_description"] == {"field": "email"}


def test_get_request_body_from_request_returns_empty_dict_on_failure():
    good = asyncio.run(utils.MiscUtils.get_request_body_from_request(GoodRequest()))
    bad = asyncio.run(utils.MiscUtils.get_request_body_from_request(BadRequest()))

    assert good == {"ok": True}
    assert bad == {}
