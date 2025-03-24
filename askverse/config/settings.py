from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, RedisDsn, HttpUrl

class Settings(BaseSettings):
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False

    # Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    POSTGRES_URL: PostgresDsn
    REDIS_URL: RedisDsn

    # Vector Database
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str
    PINECONE_INDEX: str = "askverse"

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo-preview"

    # Confluence
    CONFLUENCE_URL: HttpUrl = "https://cwiki.apache.org"
    CONFLUENCE_SPACE: str = "CONF"

    # External APIs
    WEATHER_API_KEY: Optional[str] = None
    MAPS_API_KEY: Optional[str] = None

    # Monitoring
    PROMETHEUS_MULTIPROC_DIR: str = "/tmp/prometheus"
    GRAFANA_URL: HttpUrl = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 