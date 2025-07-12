from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    gdrive_auth_mode: str = Field("oauth", validation_alias="GDRIVE_AUTH_MODE")
    gdrive_credentials: str = "credentials.json"
    gdrive_token: str = "token.json"
    gdrive_sa_key: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()