from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import RefreshSessionModel


class RefreshSessionRepository:
    @staticmethod
    async def create_refresh_session(
        session: AsyncSession,
        user_id: UUID,
        user_name: str,
        expires_at: datetime,
        session_id: UUID,
    ) -> RefreshSessionModel:
        refresh_session = RefreshSessionModel(
            id=session_id,
            user_id=user_id,
            user_name=user_name,
            expires_at=expires_at,
            revoked=False,
        )
        session.add(refresh_session)
        await session.flush()
        await session.refresh(refresh_session)
        return refresh_session

    @staticmethod
    async def get_refresh_session(session: AsyncSession, session_id: UUID) -> RefreshSessionModel | None:
        return await session.get(RefreshSessionModel, session_id)

    @staticmethod
    async def revoke_refresh_session(
        session: AsyncSession,
        session_id: UUID,
        revoked_reason: str,
        replaced_by_session_id: UUID | None = None,
    ) -> RefreshSessionModel | None:
        refresh_session = await session.get(RefreshSessionModel, session_id)
        if refresh_session is None:
            return None

        if not refresh_session.revoked:
            refresh_session.revoked = True
            refresh_session.revoked_at = datetime.now(timezone.utc)
            refresh_session.revoked_reason = revoked_reason
            refresh_session.replaced_by_session_id = replaced_by_session_id
            await session.flush()
            await session.refresh(refresh_session)

        return refresh_session

    @staticmethod
    async def revoke_all_refresh_sessions_for_user(
        session: AsyncSession,
        user_id: UUID,
        revoked_reason: str,
        exclude_session_id: UUID | None = None,
    ) -> int:
        stmt = select(RefreshSessionModel).where(RefreshSessionModel.user_id == user_id)
        result = await session.execute(stmt)
        refresh_sessions = result.scalars().all()
        revoked_count = 0

        for refresh_session in refresh_sessions:
            if exclude_session_id is not None and refresh_session.id == exclude_session_id:
                continue
            if refresh_session.revoked:
                continue
            refresh_session.revoked = True
            refresh_session.revoked_at = datetime.now(timezone.utc)
            refresh_session.revoked_reason = revoked_reason
            revoked_count += 1

        await session.flush()
        return revoked_count
