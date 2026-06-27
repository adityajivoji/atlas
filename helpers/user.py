from uuid import UUID
from typing import Optional, Union
from enum import Enum
from datetime import datetime

from models import UserModel

class STATUS(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    VERIFICATION_PENDING = "VERIFICATION_PENDING"
    SUSPENDED = "SUSPENDED"

class UserHelper:
    name: str
    user_name: str
    password: str
    email: str
    meta: dict
    deactivated: bool
    status: STATUS
    created_at: datetime
    updated_at: datetime
    id: Optional[UUID] = None

    def __init__(
        self,
        id: Optional[UUID],
        name: str,
        user_name: str,
        password: str,
        email: str,
        status: Union[str, STATUS],
        created_at: datetime,
        updated_at: datetime,
        deactivated: bool,
        meta: Optional[dict] = None,
    ):
        self.id = id
        self.name = name
        self.user_name = user_name
        self.password = password
        self.email = email
        self.deactivated = deactivated
        self.meta = meta or {}
        # Allow either enum or string; normalise to enum, tolerating lower‑case inputs.
        status_value = status.value if isinstance(status, STATUS) else str(status).upper()
        self.status = STATUS(status_value)
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "user_name": self.user_name,
            "email": self.email,
            "deactivated": self.deactivated,
            "meta": self.meta,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, d: dict):
        try:
            status = d.get("status")
            if status is None:
                raise ValueError("Missing status")
            return cls(
                id=d.get("id"),
                name=d["name"],
                user_name=d["user_name"],
                password=d["password"],
                email=d["email"],
                deactivated=d["deactivated"],
                meta=d.get("meta", {}),
                status=status,
                created_at=d["created_at"],
                updated_at=d["updated_at"],
            )
        except Exception as e:
            raise e
        
    def to_model(self):
        return UserModel(
            id=self.id,
            name=self.name,
            user_name=self.user_name,
            password=self.password,
            email=self.email,
            deactivated=self.deactivated,
            meta=self.meta,
            status=self.status.value,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
    
    @classmethod
    def from_model(cls, model: UserModel):
        try:
            return cls(
                id=model.id,
                name=model.name,
                user_name=model.user_name,
                password=model.password,
                email=model.email,
                deactivated=model.deactivated,
                meta=model.meta,
                status=model.status,
                created_at=model.created_at,
                updated_at=model.updated_at,
            )
        except Exception as e:
            raise e
        
    
