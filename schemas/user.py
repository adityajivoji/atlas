import re
from typing import Optional
from pydantic import BaseModel, model_validator, field_validator, Field
import helpers

EMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"


def validate_password_policy(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if re.search(r"[a-z]", password) is None:
        raise ValueError("Password must include at least one lowercase letter")
    if re.search(r"[A-Z]", password) is None:
        raise ValueError("Password must include at least one uppercase letter")
    if re.search(r"\d", password) is None:
        raise ValueError("Password must include at least one digit")
    if re.search(r"[^A-Za-z0-9]", password) is None:
        raise ValueError("Password must include at least one special character")
    return password

class UserLogin(BaseModel):
    email: Optional[str] = Field(default=None, pattern=EMAIL_REGEX)
    user_name: Optional[str] = None
    password: str = Field(min_length=8)
    
    
    @model_validator(mode="after")
    def check_email_or_user_name(self) -> "UserLogin":
        if not self.email and not self.user_name:
            raise helpers.Error("Invalid Request Body: provide either username or email")
        
        return self
    
    
class UserSignup(BaseModel):
    name: str
    user_name: str
    password: str = Field(min_length=8)
    email: str = Field(pattern=EMAIL_REGEX)
    meta: dict

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_policy(value)

class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RotateKeyRequest(BaseModel):
    kid: Optional[str] = None


class KeyLifecycleRequest(BaseModel):
    kid: str


class LogoutRequest(BaseModel):
    refresh_token: str
