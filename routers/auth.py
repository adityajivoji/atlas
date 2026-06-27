from fastapi import APIRouter, Depends, Request
import utils
from schemas import KeyLifecycleRequest, LogoutRequest, RefreshTokenRequest, RotateKeyRequest, UserLogin, UserSignup
import services

auth_router = APIRouter()
logger = utils.LoggerUtils.get_logger(__name__)

@auth_router.get('/')
async def online_check():
    return utils.MiscUtils.api_response("Auth route working")

@auth_router.get('/jwks')
async def get_jwks():
    try:
        return utils.AuthUtils.get_jwks()
    except Exception as e:
        logger.exception("Failed to generate JWKS")
        return utils.MiscUtils.error_response(e)

@auth_router.post('/login')
async def login(request_body: UserLogin, request: Request):
    identifier = request_body.email or request_body.user_name
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    logger.info("Login request received for identifier=%s", identifier)
    try:
        login_return = await services.AuthService.login(request_body.password, request_body.user_name, request_body.email)
        subject = request_body.user_name
        try:
            subject = utils.AuthUtils.verify_token(
                login_return["access_token"],
                expected_type="access",
            ).get("sub") or subject
        except Exception:
            logger.exception("Could not decode access token subject for governance logging")
        try:
            await services.GovernanceService.record_login_attempt(
                user_name=subject or request_body.user_name,
                email=request_body.email,
                success=True,
                failure_reason=None,
                ip_address=client_host,
                user_agent=user_agent,
            )
            await services.GovernanceService.record_audit_log(
                actor_user_name=subject or request_body.user_name,
                action="auth.login",
                status_text="SUCCESS",
                resource="auth",
                ip_address=client_host,
                user_agent=user_agent,
                details={"identifier": identifier},
            )
        except Exception:
            logger.exception("Failed to persist successful login governance records")
        logger.info("Login successful for identifier=%s", identifier)
        
        return utils.MiscUtils.api_response(
            "Login Successful",
            data=login_return
        )
        
    except Exception as e:
        try:
            await services.GovernanceService.record_login_attempt(
                user_name=request_body.user_name,
                email=request_body.email,
                success=False,
                failure_reason=str(e),
                ip_address=client_host,
                user_agent=user_agent,
            )
            await services.GovernanceService.record_audit_log(
                actor_user_name=request_body.user_name,
                action="auth.login",
                status_text="FAILED",
                resource="auth",
                ip_address=client_host,
                user_agent=user_agent,
                details={"identifier": identifier, "reason": str(e)},
            )
        except Exception:
            logger.exception("Failed to persist login governance records")
        logger.exception("Login failed for identifier=%s", identifier)
        return utils.MiscUtils.error_response(e)


@auth_router.post('/refresh')
async def refresh(request_body: RefreshTokenRequest, request: Request):
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    logger.info("Refresh token request received")
    try:
        refresh_return = await services.AuthService.refresh(request_body.refresh_token)
        subject = None
        try:
            subject = utils.AuthUtils.verify_token(
                refresh_return["access_token"],
                expected_type="access",
            ).get("sub")
        except Exception:
            logger.exception("Could not decode refreshed access token subject for governance logging")
        try:
            await services.GovernanceService.record_audit_log(
                actor_user_name=subject,
                action="auth.refresh",
                status_text="SUCCESS",
                resource="auth",
                ip_address=client_host,
                user_agent=user_agent,
                details={},
            )
        except Exception:
            logger.exception("Failed to persist successful refresh governance records")
        logger.info("Refresh token request successful")
        return utils.MiscUtils.api_response(
            "Token refreshed",
            data=refresh_return
        )
    except Exception as e:
        try:
            await services.GovernanceService.record_audit_log(
                actor_user_name=None,
                action="auth.refresh",
                status_text="FAILED",
                resource="auth",
                ip_address=client_host,
                user_agent=user_agent,
                details={"reason": str(e)},
            )
        except Exception:
            logger.exception("Failed to persist refresh governance records")
        logger.exception("Refresh token request failed")
        return utils.MiscUtils.error_response(e)


@auth_router.post('/logout')
async def logout(
    request_body: LogoutRequest,
    request: Request,
    access_claims: dict = Depends(services.GovernanceService.require_access_token),
):
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    subject = access_claims.get("sub")
    try:
        await services.AuthService.logout(
            refresh_token=request_body.refresh_token,
            access_subject=subject,
        )
        try:
            await services.GovernanceService.record_audit_log(
                actor_user_name=subject,
                action="auth.logout",
                status_text="SUCCESS",
                resource="auth",
                ip_address=client_host,
                user_agent=user_agent,
                details={},
            )
        except Exception:
            logger.exception("Failed to persist successful logout governance records")
        return utils.MiscUtils.api_response("Logout successful")
    except Exception as e:
        logger.exception("Logout request failed")
        return utils.MiscUtils.error_response(e)


@auth_router.post('/logout-all')
async def logout_all(
    request: Request,
    access_claims: dict = Depends(services.GovernanceService.require_access_token),
):
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    subject = access_claims.get("sub")
    try:
        revoked_count = await services.AuthService.logout_all(access_subject=subject)
        try:
            await services.GovernanceService.record_audit_log(
                actor_user_name=subject,
                action="auth.logout_all",
                status_text="SUCCESS",
                resource="auth",
                ip_address=client_host,
                user_agent=user_agent,
                details={"revoked_sessions": revoked_count},
            )
        except Exception:
            logger.exception("Failed to persist successful logout-all governance records")
        return utils.MiscUtils.api_response(
            "Logout from all sessions successful",
            data={"revoked_sessions": revoked_count},
        )
    except Exception as e:
        logger.exception("Logout-all request failed")
        return utils.MiscUtils.error_response(e)


@auth_router.post('/keys/rotate')
async def rotate_key(
    request_body: RotateKeyRequest,
    request: Request,
    admin_claims: dict = Depends(services.GovernanceService.require_admin),
):
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    admin_sub = admin_claims.get("sub")
    logger.info("Key rotation request received")
    try:
        key_data = utils.AuthUtils.generate_new_signing_key(kid=request_body.kid)
        try:
            await services.GovernanceService.record_audit_log(
                actor_user_name=admin_sub,
                action="auth.keys.rotate",
                status_text="SUCCESS",
                resource="signing_key",
                ip_address=client_host,
                user_agent=user_agent,
                details={"kid": key_data["kid"]},
            )
        except Exception:
            logger.exception("Failed to persist successful key rotation governance records")
        logger.info("Key rotation successful with kid=%s", key_data["kid"])
        return utils.MiscUtils.api_response(
            "New signing key generated",
            data=key_data,
            status_code=201
        )
    except Exception as e:
        try:
            await services.GovernanceService.record_audit_log(
                actor_user_name=admin_sub,
                action="auth.keys.rotate",
                status_text="FAILED",
                resource="signing_key",
                ip_address=client_host,
                user_agent=user_agent,
                details={"reason": str(e), "requested_kid": request_body.kid},
            )
        except Exception:
            logger.exception("Failed to persist key rotation governance records")
        logger.exception("Key rotation request failed")
        return utils.MiscUtils.error_response(e)


@auth_router.post('/keys/generate')
async def generate_key(
    request_body: RotateKeyRequest,
    request: Request,
    admin_claims: dict = Depends(services.GovernanceService.require_admin),
):
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    admin_sub = admin_claims.get("sub")
    try:
        key_data = utils.AuthUtils.generate_signing_key(kid=request_body.kid)
        try:
            await services.GovernanceService.record_audit_log(
                actor_user_name=admin_sub,
                action="auth.keys.generate",
                status_text="SUCCESS",
                resource="signing_key",
                ip_address=client_host,
                user_agent=user_agent,
                details={"kid": key_data["kid"]},
            )
        except Exception:
            logger.exception("Failed to persist successful key generation governance records")
        return utils.MiscUtils.api_response(
            "Signing key generated",
            data=key_data,
            status_code=201,
        )
    except Exception as e:
        logger.exception("Key generation request failed")
        return utils.MiscUtils.error_response(e)


@auth_router.post('/keys/activate')
async def activate_key(
    request_body: KeyLifecycleRequest,
    request: Request,
    admin_claims: dict = Depends(services.GovernanceService.require_admin),
):
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    admin_sub = admin_claims.get("sub")
    try:
        key_data = utils.AuthUtils.activate_signing_key(kid=request_body.kid)
        try:
            await services.GovernanceService.record_audit_log(
                actor_user_name=admin_sub,
                action="auth.keys.activate",
                status_text="SUCCESS",
                resource="signing_key",
                ip_address=client_host,
                user_agent=user_agent,
                details={"kid": key_data["kid"]},
            )
        except Exception:
            logger.exception("Failed to persist successful key activation governance records")
        return utils.MiscUtils.api_response("Signing key activated", data=key_data)
    except Exception as e:
        logger.exception("Key activation request failed")
        return utils.MiscUtils.error_response(e)


@auth_router.post('/keys/revoke')
async def revoke_key(
    request_body: KeyLifecycleRequest,
    request: Request,
    admin_claims: dict = Depends(services.GovernanceService.require_admin),
):
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    admin_sub = admin_claims.get("sub")
    try:
        key_data = utils.AuthUtils.revoke_signing_key(kid=request_body.kid)
        try:
            await services.GovernanceService.record_audit_log(
                actor_user_name=admin_sub,
                action="auth.keys.revoke",
                status_text="SUCCESS",
                resource="signing_key",
                ip_address=client_host,
                user_agent=user_agent,
                details={"kid": key_data["kid"]},
            )
        except Exception:
            logger.exception("Failed to persist successful key revoke governance records")
        return utils.MiscUtils.api_response("Signing key revoked", data=key_data)
    except Exception as e:
        logger.exception("Key revoke request failed")
        return utils.MiscUtils.error_response(e)
    
    
@auth_router.post('/signup')
async def signup(request_body: UserSignup, request: Request):
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    logger.info(
        "Signup request received for user_name=%s email=%s",
        request_body.user_name,
        request_body.email
    )
    try:
        signup_return = await services.UserService.create_user(
            name=request_body.name,
            user_name=request_body.user_name,
            email=request_body.email,
            password=request_body.password,
            meta=request_body.meta
        )
        logger.info(
            "Signup successful for user_name=%s email=%s",
            request_body.user_name,
            request_body.email
        )
        try:
            await services.GovernanceService.record_audit_log(
                actor_user_name=request_body.user_name,
                action="auth.signup",
                status_text="SUCCESS",
                resource="user",
                ip_address=client_host,
                user_agent=user_agent,
                details={"email": request_body.email},
            )
        except Exception:
            logger.exception("Failed to persist successful signup governance records")
        
        return utils.MiscUtils.api_response(
            "Signup Successful",
            data=signup_return.to_dict()
        )
        
    except Exception as e:
        try:
            await services.GovernanceService.record_audit_log(
                actor_user_name=request_body.user_name,
                action="auth.signup",
                status_text="FAILED",
                resource="user",
                ip_address=client_host,
                user_agent=user_agent,
                details={"email": request_body.email, "reason": str(e)},
            )
        except Exception:
            logger.exception("Failed to persist signup governance records")
        logger.exception(
            "Signup failed for user_name=%s email=%s",
            request_body.user_name,
            request_body.email
        )
        return utils.MiscUtils.error_response(e)
