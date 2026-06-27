from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import AuditLogModel, LoginHistoryModel


class GovernanceRepository:
    @staticmethod
    async def create_audit_log(
        session: AsyncSession,
        actor_user_name: Optional[str],
        action: str,
        status: str,
        resource: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str],
        details: Optional[dict] = None,
    ) -> AuditLogModel:
        model = AuditLogModel(
            actor_user_name=actor_user_name,
            action=action,
            status=status,
            resource=resource,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
        )
        session.add(model)
        await session.flush()
        await session.refresh(model)
        return model

    @staticmethod
    async def create_login_history(
        session: AsyncSession,
        user_name: Optional[str],
        email: Optional[str],
        success: bool,
        failure_reason: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str],
    ) -> LoginHistoryModel:
        model = LoginHistoryModel(
            user_name=user_name,
            email=email,
            success=success,
            failure_reason=failure_reason,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        session.add(model)
        await session.flush()
        await session.refresh(model)
        return model

    @staticmethod
    async def get_audit_logs(
        session: AsyncSession,
        limit: int = 100,
        actor_user_name: Optional[str] = None,
        action: Optional[str] = None,
    ) -> list[AuditLogModel]:
        stmt = select(AuditLogModel).order_by(AuditLogModel.created_at.desc()).limit(limit)
        if actor_user_name:
            stmt = stmt.where(AuditLogModel.actor_user_name == actor_user_name)
        if action:
            stmt = stmt.where(AuditLogModel.action == action)
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_login_history(
        session: AsyncSession,
        limit: int = 100,
        user_name: Optional[str] = None,
        success: Optional[bool] = None,
    ) -> list[LoginHistoryModel]:
        stmt = select(LoginHistoryModel).order_by(LoginHistoryModel.created_at.desc()).limit(limit)
        if user_name:
            stmt = stmt.where(LoginHistoryModel.user_name == user_name)
        if success is not None:
            stmt = stmt.where(LoginHistoryModel.success == success)
        result = await session.execute(stmt)
        return result.scalars().all()
