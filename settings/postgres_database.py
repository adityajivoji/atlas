from pydantic_settings import BaseSettings, SettingsConfigDict

class PostgresSettings(BaseSettings):
    POSTGRES_DB_URL: str = ''
    POSTGRES_MIGRATION_URL: str = ''
    
    
    class Config:
        env_file=".env"
        env_file_encoding="utf-8"
        populate_by_name=True
        extra="ignore"


    # model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", populate_by_name=True, extra="ignore")
    
    
