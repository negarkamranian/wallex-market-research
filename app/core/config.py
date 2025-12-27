from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    openrouter_api_key: str
    llm_model: str = "meta-llama/llama-3.1-8b-instruct:free"
    
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "market_research"
    postgres_user: str = "research_user"
    postgres_password: str = "research_pass"
    
    mongo_host: str = "mongodb"
    mongo_port: int = 27017
    mongo_db: str = "market_research_logs"
    
    app_name: str = "Market Research API"
    app_version: str = "1.0.0"
    
    @property
    def postgres_url(self) -> str:
        """Build PostgreSQL connection URL."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    @property
    def mongo_url(self) -> str:
        """Build MongoDB connection URL."""
        return f"mongodb://{self.mongo_host}:{self.mongo_port}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
