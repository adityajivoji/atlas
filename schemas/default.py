from pydantic import BaseModel
from typing import Optional, Any

class DefaultModel(BaseModel):
    data: Optional[Any]
    status_code: int
    message: Optional[str]
    error: Optional[str]
    error_description: Optional[dict]