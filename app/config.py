from pydantic import BaseSettings

class Settings(BaseSettings):
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    class Config:
        env_file = ".env"




settings = Settings()
