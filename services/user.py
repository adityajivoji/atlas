from uuid import UUID
from typing import Optional, Dict, List
import helpers
import repositories
import database
import utils
from datetime import datetime, timezone

class UserService():
    
    @staticmethod
    async def get_user_with_user_id(id: str) -> helpers.UserHelper:
        async with database.Postgres.get_session() as session:
            user_helper = await repositories.UserRepository.get_one_by_filter(
                session=session,
                filters={"id": UUID(id)}
            )
            if user_helper is None:
                raise helpers.Error("User not found")
            return user_helper
        
    @staticmethod
    async def create_user_with_id(id: str, name: str, user_name: str, password: str, email: str, meta: Optional[Dict] = None) -> helpers.UserHelper:
        # used for creating with seeding ONLY
        async with database.Postgres.get_session() as session:
            new_user_helper = helpers.UserHelper(
                id=UUID(id),
                name=name,
                user_name=user_name,
                password=utils.AuthUtils.hash_password(password),
                email=email,
                deactivated=False,
                meta=meta or {},
                status=helpers.STATUS.ACTIVE,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            user_helper = await repositories.UserRepository.create_user(
                session=session,
                user_helper=new_user_helper
            )
            return user_helper

    @staticmethod
    async def create_user(name: str, user_name: str, password: str, email: str, meta: Optional[Dict] = None) -> helpers.UserHelper:
        async with database.Postgres.get_session() as session:
            new_user_helper = helpers.UserHelper(
                id=None,
                name=name,
                user_name=user_name,
                password=utils.AuthUtils.hash_password(password),
                email=email,
                deactivated=False,
                meta=meta or {},
                status=helpers.STATUS.VERIFICATION_PENDING,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            user_helper = await repositories.UserRepository.create_user(
                session=session,
                user_helper=new_user_helper
            )
            return user_helper
        
    @staticmethod
    async def update_password(id: Optional[str], email: Optional[str], new_password: str, old_password: str) -> helpers.UserHelper:
        async with database.Postgres.get_session() as session:
            user_helper: Optional[helpers.UserHelper] = None
            if id:
                user_helper = await repositories.UserRepository.get_one_by_filter(
                    session=session,
                    filters={"id": UUID(id)}
                )
            elif email:
                user_helper = await repositories.UserRepository.get_one_by_filter(
                    session=session,
                    filters={"email": email}
                )
                
            if user_helper is None or user_helper.id is None:
                raise helpers.Error("User not found")
                        
            new_user_helper = await repositories.UserRepository.update_password(session, utils.AuthUtils.hash_password(new_password), user_helper.id)
            
            return new_user_helper
            
            
        
    @staticmethod
    async def update_user(id: str, name: Optional[str] = None, user_name: Optional[str] = None, password: Optional[str] = None, email: Optional[str] = None, meta: Optional[Dict] = None):
        async with database.Postgres.get_session() as session:
            user_helper = await repositories.UserRepository.get_one_by_filter(
                session=session,
                filters={"id": UUID(id)}
            )
            if user_helper is None:
                raise helpers.Error("User not found")
            if name:
                user_helper.name = name
            if email:
                user_helper.email = email
            if meta:
                user_helper.meta = meta
                
            user_helper = await repositories.UserRepository.update_user(session, user_helper)
            
            return user_helper
        
    @staticmethod
    async def delete(id: str):
        async with database.Postgres.get_session() as session:
            user_helper = await repositories.UserRepository.delete_user(
                session=session,
                user_id=UUID(id)
            )
            
            return user_helper
        
    @staticmethod
    async def get_all():
        async with database.Postgres.get_session() as session:
            users = await repositories.UserRepository.get_all_by_filter(session=session, filters={})
            
            return users
        
    @staticmethod
    async def get_one_by_filter(filter: dict = {}) -> Optional[helpers.UserHelper]:
        async with database.Postgres.get_session() as session:
            user = await repositories.UserRepository.get_one_by_filter(
                session=session,
                filters=filter
            )
            return user
        
    
    @staticmethod
    async def get_all_by_filter(filter: dict = {}) -> List[helpers.UserHelper]:
        async with database.Postgres.get_session() as session:
            users = await repositories.UserRepository.get_all_by_filter(
                session=session,
                filters=filter
            )
            return users
