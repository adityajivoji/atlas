from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy import MetaData
from settings import PostgresSettings



class Postgres:
    engine = create_async_engine(PostgresSettings().POSTGRES_DB_URL, echo=False, future=True)
    sessionLocal = async_sessionmaker(
        bind=engine, expire_on_commit=False, class_=AsyncSession
    )
    base = declarative_base(metadata=MetaData())

    @staticmethod
    @asynccontextmanager
    async def get_session() -> AsyncGenerator[AsyncSession, None]:
        async with Postgres.sessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            else:
                await session.commit()
                await session.close()
