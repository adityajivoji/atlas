from typing import Optional, Dict, Any
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from schemas import DefaultModel
import helpers


class MiscUtils:
    @staticmethod
    def serialize_data(data: Any) -> Any:
        if isinstance(data, dict):
            return {key: MiscUtils.serialize_data(value) for key, value in data.items()}
        if isinstance(data, (list, tuple, set)):
            return [MiscUtils.serialize_data(value) for value in data]
        if hasattr(data, "to_dict") and callable(data.to_dict):
            return MiscUtils.serialize_data(data.to_dict())
        return data

    @staticmethod
    def api_response(
        message: Optional[str] = None,
        data: Any = None,
        status_code: int = 200
    ) -> JSONResponse:
        if message is None:
            message = "call successful" if 200 <= status_code < 300 else "call unsuccessful"

        payload = DefaultModel(
            message=message,
            data=MiscUtils.serialize_data(data),
            status_code=status_code,
            error=None,
            error_description=None
        ).model_dump()

        return JSONResponse(content=jsonable_encoder(payload), status_code=status_code)

    @staticmethod
    def error_response(exception: Exception, status_code: int = 500) -> JSONResponse:
        if isinstance(exception, helpers.Error):
            payload = DefaultModel(
                message=None,
                error_description=exception.details or {"info": "Internal Server Error"},
                data=None,
                status_code=exception.status_code or status_code or 500,
                error=exception.message
            ).model_dump()
            return JSONResponse(
                content=jsonable_encoder(payload),
                status_code=payload["status_code"]
            )
        else:
            payload = DefaultModel(
                message=None,
                error_description={"info": "Internal Server Error"},
                data=None,
                status_code=status_code,
                error="Internal Server Error"
            ).model_dump()
            return JSONResponse(content=jsonable_encoder(payload), status_code=status_code)

    @staticmethod
    async def get_request_body_from_request(request: Request) -> Dict:
        try:
            return await request.json()
        except Exception:
            return {}
