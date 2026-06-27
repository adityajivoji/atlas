from pydantic_settings import BaseSettings, SettingsConfigDict

class InitSettings(BaseSettings):
    SUPER_USER_ID: str = ""
    SUPER_USER_NAME: str = ""
    SUPER_USER_USER_NAME: str = ""
    SUPER_USER_PASSWORD: str = ""
    SUPER_USER_EMAIL: str = ""
    
    
    class Config:
        env_file=".env"
        env_file_encoding="utf-8"
        populate_by_name=True
        extra="ignore"

    # model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", populate_by_name=True, extra="ignore")

