import services
from settings import InitSettings

class InitUtils():
    
    @staticmethod
    async def seed_db():
        init_settings = InitSettings()
        super_user_exist = await services.UserService.get_one_by_filter({"id": init_settings.SUPER_USER_ID})
        if not super_user_exist:
            super_user = await services.UserService.create_user_with_id(
                name=init_settings.SUPER_USER_NAME,
                user_name=init_settings.SUPER_USER_USER_NAME,
                password=init_settings.SUPER_USER_PASSWORD,
                email=init_settings.SUPER_USER_EMAIL,
                id=init_settings.SUPER_USER_ID,
                meta={"role": "admin"},
            )
