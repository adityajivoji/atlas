from pydantic_settings import BaseSettings
from pathlib import Path

class AuthSettings(BaseSettings):
    PEM_PATH: str = ''
    JWT_ALGORITHM: str = ''
    KEYS_DIR: str = ''
    DEFAULT_KID: str = "auth-service-key-1"
    ACCESS_TOKEN_TTL_MINUTES: int = 10
    REFRESH_TOKEN_TTL_DAYS: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True
        extra = "ignore"

    @property
    def _resolved_private_key_path(self) -> Path:
        if not self.PEM_PATH:
            raise FileNotFoundError("PEM_PATH is not set")

        candidate = Path(self.PEM_PATH)
        if candidate.is_absolute():
            return candidate

        # Resolve relative paths from project root for consistent behavior.
        project_root = Path(__file__).resolve().parents[1]
        return project_root / candidate

    @property
    def resolved_keys_dir(self) -> Path:
        if self.KEYS_DIR:
            candidate = Path(self.KEYS_DIR)
            if candidate.is_absolute():
                return candidate
            project_root = Path(__file__).resolve().parents[1]
            return project_root / candidate
        return self._resolved_private_key_path.parent

    @property
    def PRIVATE_KEY(self) -> str:
        path = self._resolved_private_key_path
        if not path.exists():
            raise FileNotFoundError(f"Private key not found at {path}")
        with open(path, "r") as f:
            return f.read()

    @property
    def PUBLIC_KEY(self) -> str:
        path = self._resolved_private_key_path.with_name("public.pem")
        if not path.exists():
            raise FileNotFoundError(f"Public key not found at {path}")
        with open(path, "r") as f:
            return f.read()
    
    
    
