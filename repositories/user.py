from uuid import UUID
from typing import Optional, List, Dict, Any
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models import UserModel
import helpers

class UserRepository:

    @staticmethod
    async def create_user(session: AsyncSession, user_helper: helpers.UserHelper) -> helpers.UserHelper:
        user_model = user_helper.to_model()
        session.add(user_model)
        await session.flush()
        await session.refresh(user_model)
        return helpers.UserHelper.from_model(user_model)
    
    
    @staticmethod
    async def update_password(session: AsyncSession, new_password: str, id: UUID) -> helpers.UserHelper:
        user_model = await session.get(UserModel, id)
        if user_model is None:
            raise helpers.Error("User not found")
        user_model.password = new_password
        await session.flush()
        return helpers.UserHelper.from_model(user_model)

    
    @staticmethod
    async def update_user(session: AsyncSession, user_helper: helpers.UserHelper) -> helpers.UserHelper:
        user = await session.get(UserModel, user_helper.id)
        if user is None:
            raise helpers.Error("User not found")
        user.name = user_helper.name
        user.email = user_helper.email
        user.meta = user_helper.meta
        
        await session.flush()
        await session.refresh(user)
        return helpers.UserHelper.from_model(user) 

    @staticmethod
    async def delete_user(session: AsyncSession, user_id: UUID) -> helpers.UserHelper:
        user = await session.get(UserModel, user_id)
        if user is None:
            raise helpers.Error("User not found")
        user.deactivated = True
        
        await session.flush()
        return helpers.UserHelper.from_model(user) 
    
        
    @staticmethod
    async def get_one_by_filter(session: AsyncSession, filters: Dict[str, Any]) -> Optional[helpers.UserHelper]:
        stmt = select(UserModel)
        for key, value in filters.items():
            stmt = stmt.where(getattr(UserModel, key) == value)
        result = await session.execute(stmt)
        user_model = result.scalar_one_or_none()
        return None if user_model is None else helpers.UserHelper.from_model(user_model)

    @staticmethod
    async def get_all_by_filter(session: AsyncSession, filters: Dict[str, Any]) -> List[helpers.UserHelper]:
        stmt = select(UserModel)
        for key, value in filters.items():
            stmt = stmt.where(getattr(UserModel, key) == value)
        result = await session.execute(stmt)
        user_models = result.scalars().all()
        return [helpers.UserHelper.from_model(user) for user in user_models]
