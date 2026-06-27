from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4
import database
import repositories
import helpers
import utils

class AuthService():
    _invalid_credentials_error = helpers.Error("Invalid credentials", status_code=401)
    _invalid_refresh_error = helpers.Error("Refresh token is no longer valid", status_code=401)
    _dummy_password_hash: Optional[str] = None
    _refresh_rotation_reason = "rotated"
    _logout_reason = "user_logout"
    _logout_all_reason = "user_logout_all"

    @staticmethod
    def _get_dummy_password_hash() -> str:
        if AuthService._dummy_password_hash is None:
            AuthService._dummy_password_hash = utils.AuthUtils.hash_password("DummyPassword@123")
        return AuthService._dummy_password_hash

    @staticmethod
    def _build_access_claims(user) -> dict:
        return utils.AuthUtils.resolve_access_claims(user=user, subject=getattr(user, "user_name", None))

    @staticmethod
    async def _get_active_user_by_subject(subject: str):
        async with database.Postgres.get_session() as session:
            user = await repositories.UserRepository.get_one_by_filter(
                session=session,
                filters={"user_name": subject},
            )

        if user is None or user.deactivated or user.status != helpers.STATUS.ACTIVE:
            raise AuthService._invalid_refresh_error

        return user

    @staticmethod
    def _parse_refresh_session_id(payload: dict) -> UUID:
        session_id = payload.get("jti")
        if not session_id:
            raise AuthService._invalid_refresh_error
        try:
            return UUID(str(session_id))
        except ValueError as exc:
            raise AuthService._invalid_refresh_error from exc

    @staticmethod
    async def _create_refresh_session(session, user) -> UUID:
        if user.id is None:
            raise helpers.Error("User missing id", status_code=500)
        session_id = uuid4()
        expires_at = datetime.now(timezone.utc) + timedelta(days=utils.AuthUtils.auth_settings.REFRESH_TOKEN_TTL_DAYS)
        await repositories.RefreshSessionRepository.create_refresh_session(
            session=session,
            user_id=user.id,
            user_name=user.user_name,
            expires_at=expires_at,
            session_id=session_id,
        )
        return session_id

    @staticmethod
    async def _issue_token_pair_for_user(session, user) -> dict:
        refresh_session_id = await AuthService._create_refresh_session(session=session, user=user)
        return utils.AuthUtils.issue_token_pair(
            subject=user.user_name,
            access_claims=AuthService._build_access_claims(user),
            refresh_claims={"jti": str(refresh_session_id)},
        )

    @staticmethod
    async def login(
        password: str,
        user_name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> dict:
        async with database.Postgres.get_session() as session:
            user = None
            if email:
                user = await repositories.UserRepository.get_one_by_filter(
                    session=session,
                    filters={
                        "email": email
                    }
                )
            elif user_name:
                user = await repositories.UserRepository.get_one_by_filter(
                    session=session,
                    filters={
                        "user_name": user_name
                    }
                )
            password_hash = user.password if user is not None else AuthService._get_dummy_password_hash()

            try:
                utils.AuthUtils.verify_hash(password_hash, password)
            except helpers.Error as exc:
                raise AuthService._invalid_credentials_error from exc

            if user is None:
                raise AuthService._invalid_credentials_error

            return await AuthService._issue_token_pair_for_user(session=session, user=user)

    @staticmethod
    async def refresh(refresh_token: str) -> dict:
        payload = utils.AuthUtils.verify_token(
            token=refresh_token,
            expected_type="refresh",
        )
        subject = payload.get("sub")
        if not subject:
            raise helpers.Error("Refresh token missing subject", status_code=401)
        current_session_id = AuthService._parse_refresh_session_id(payload)

        async with database.Postgres.get_session() as session:
            stored_session = await repositories.RefreshSessionRepository.get_refresh_session(
                session=session,
                session_id=current_session_id,
            )
            if stored_session is None or stored_session.revoked:
                raise AuthService._invalid_refresh_error
            if stored_session.expires_at <= datetime.now(timezone.utc):
                raise AuthService._invalid_refresh_error
            if stored_session.user_name != subject:
                raise AuthService._invalid_refresh_error

            user = await repositories.UserRepository.get_one_by_filter(
                session=session,
                filters={"user_name": subject},
            )
            if user is None or user.deactivated or user.status != helpers.STATUS.ACTIVE:
                raise AuthService._invalid_refresh_error

            next_session_id = await AuthService._create_refresh_session(session=session, user=user)
            await repositories.RefreshSessionRepository.revoke_refresh_session(
                session=session,
                session_id=current_session_id,
                revoked_reason=AuthService._refresh_rotation_reason,
                replaced_by_session_id=next_session_id,
            )

            return utils.AuthUtils.issue_token_pair(
                subject=subject,
                access_claims=AuthService._build_access_claims(user),
                refresh_claims={"jti": str(next_session_id)},
            )

    @staticmethod
    async def logout(refresh_token: str, access_subject: str) -> None:
        payload = utils.AuthUtils.verify_token(
            token=refresh_token,
            expected_type="refresh",
        )
        subject = payload.get("sub")
        if not subject:
            raise helpers.Error("Refresh token missing subject", status_code=401)
        if subject != access_subject:
            raise helpers.Error("Refresh token does not belong to the authenticated user", status_code=403)

        session_id = AuthService._parse_refresh_session_id(payload)

        async with database.Postgres.get_session() as session:
            await repositories.RefreshSessionRepository.revoke_refresh_session(
                session=session,
                session_id=session_id,
                revoked_reason=AuthService._logout_reason,
            )

    @staticmethod
    async def logout_all(access_subject: str) -> int:
        async with database.Postgres.get_session() as session:
            user = await repositories.UserRepository.get_one_by_filter(
                session=session,
                filters={"user_name": access_subject},
            )
            if user is None or user.id is None:
                raise helpers.Error("Authenticated user not found", status_code=401)

            return await repositories.RefreshSessionRepository.revoke_all_refresh_sessions_for_user(
                session=session,
                user_id=user.id,
                revoked_reason=AuthService._logout_all_reason,
            )
            
