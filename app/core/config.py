from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    MONGODB_URI: str
    SECRET_KEY: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    SECRET_KEY_JWT: str
    ALGORITHM: str
    ENVIRONMENT: str = "development"  # "development" ou "production"

    model_config = SettingsConfigDict(env_file=".env")
    
    @property
    def is_production(self) -> bool:
        """Retourne True si l'environnement est en production"""
        return self.ENVIRONMENT.lower() == "production"

