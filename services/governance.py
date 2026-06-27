from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import database
import helpers
import repositories
import utils


class GovernanceService:
    _bearer = HTTPBearer(auto_error=True)

    @staticmethod
    async def record_audit_log(
        actor_user_name: Optional[str],
        action: str,
        status_text: str,
        resource: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str],
        details: Optional[dict] = None,
    ):
        async with database.Postgres.get_session() as session:
            await repositories.GovernanceRepository.create_audit_log(
                session=session,
                actor_user_name=actor_user_name,
                action=action,
                status=status_text,
                resource=resource,
                ip_address=ip_address,
                user_agent=user_agent,
                details=details,
            )

    @staticmethod
    async def record_login_attempt(
        user_name: Optional[str],
        email: Optional[str],
        success: bool,
        failure_reason: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str],
    ):
        async with database.Postgres.get_session() as session:
            await repositories.GovernanceRepository.create_login_history(
                session=session,
                user_name=user_name,
                email=email,
                success=success,
                failure_reason=failure_reason,
                ip_address=ip_address,
                user_agent=user_agent,
            )

    @staticmethod
    async def get_audit_logs(
        limit: int = 100,
        actor_user_name: Optional[str] = None,
        action: Optional[str] = None,
    ) -> list[dict]:
        async with database.Postgres.get_session() as session:
            rows = await repositories.GovernanceRepository.get_audit_logs(
                session=session,
                limit=limit,
                actor_user_name=actor_user_name,
                action=action,
            )
            return [
                {
                    "id": row.id,
                    "actor_user_name": row.actor_user_name,
                    "action": row.action,
                    "status": row.status,
                    "resource": row.resource,
                    "ip_address": row.ip_address,
                    "user_agent": row.user_agent,
                    "details": row.details,
                    "created_at": row.created_at,
                }
                for row in rows
            ]

    @staticmethod
    async def get_login_history(
        limit: int = 100,
        user_name: Optional[str] = None,
        success: Optional[bool] = None,
    ) -> list[dict]:
        async with database.Postgres.get_session() as session:
            rows = await repositories.GovernanceRepository.get_login_history(
                session=session,
                limit=limit,
                user_name=user_name,
                success=success,
            )
            return [
                {
                    "id": row.id,
                    "user_name": row.user_name,
                    "email": row.email,
                    "success": row.success,
                    "failure_reason": row.failure_reason,
                    "ip_address": row.ip_address,
                    "user_agent": row.user_agent,
                    "created_at": row.created_at,
                }
                for row in rows
            ]

    @staticmethod
    def require_access_token(
        credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    ) -> dict:
        try:
            payload = utils.AuthUtils.verify_token(
                token=credentials.credentials,
                expected_type="access",
            )
        except helpers.Error as exc:
            raise HTTPException(
                status_code=exc.status_code or status.HTTP_401_UNAUTHORIZED,
                detail=exc.message,
            ) from exc

        return payload

    @staticmethod
    def require_admin(
        credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    ) -> dict:
        try:
            payload = utils.AuthUtils.verify_token(
                token=credentials.credentials,
                expected_type="access",
            )
        except helpers.Error as exc:
            raise HTTPException(
                status_code=exc.status_code or status.HTTP_401_UNAUTHORIZED,
                detail=exc.message,
            ) from exc

        roles = payload.get("roles") or []
        if isinstance(roles, str):
            roles = [roles]
        normalized_roles = {str(role).lower() for role in roles}

        if utils.AuthUtils.ADMIN_ROLE not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )
        return payload
