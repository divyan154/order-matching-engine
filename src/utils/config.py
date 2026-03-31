from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    service_key: str = ""
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24 hours

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
