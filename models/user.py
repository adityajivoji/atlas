import uuid
from typing import Dict
from sqlalchemy import String, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from database import Postgres
from datetime import datetime
from sqlalchemy import DateTime, func

class UserModel(Postgres.base):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    user_name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    password: Mapped[str] = mapped_column(String, nullable=False)

    meta: Mapped[Dict] = mapped_column(JSONB, default=dict)

    status: Mapped[str] = mapped_column(String, default="ACTIVE", nullable=False)
    deactivated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
