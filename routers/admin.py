from typing import Optional

from fastapi import APIRouter, Depends, Query

import services
import utils

admin_router = APIRouter()
logger = utils.LoggerUtils.get_logger(__name__)


@admin_router.get("/audit-logs")
async def get_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    actor_user_name: Optional[str] = None,
    action: Optional[str] = None,
    admin_claims: dict = Depends(services.GovernanceService.require_admin),
):
    _ = admin_claims
    try:
        logs = await services.GovernanceService.get_audit_logs(
            limit=limit,
            actor_user_name=actor_user_name,
            action=action,
        )
        return utils.MiscUtils.api_response(
            message="Audit logs fetched successfully",
            data=logs,
        )
    except Exception as e:
        logger.exception("Failed to fetch audit logs")
        return utils.MiscUtils.error_response(e)


@admin_router.get("/login-history")
async def get_login_history(
    limit: int = Query(default=100, ge=1, le=500),
    user_name: Optional[str] = None,
    success: Optional[bool] = None,
    admin_claims: dict = Depends(services.GovernanceService.require_admin),
):
    _ = admin_claims
    try:
        history = await services.GovernanceService.get_login_history(
            limit=limit,
            user_name=user_name,
            success=success,
        )
        return utils.MiscUtils.api_response(
            message="Login history fetched successfully",
            data=history,
        )
    except Exception as e:
        logger.exception("Failed to fetch login history")
        return utils.MiscUtils.error_response(e)
