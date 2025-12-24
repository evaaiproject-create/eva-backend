"""
Configuration management for Eva backend.
Handles environment variables and application settings using Pydantic.
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    These settings configure:
    - Google Cloud integration (Project ID, credentials)
    - OAuth authentication
    - API server configuration
    - User limits and security settings
    """
    
    # Google Cloud Configuration
    google_cloud_project: str = "eva-assistant-project"
    google_application_credentials: str = "service-account-key.json"
    google_client_id: str = ""
    google_client_secret: str = ""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_secret_key: str = "change-this-secret-key-in-production"
    
    # User Management
    max_users: int = 5
    
    # CORS Configuration
    cors_origins: str = "http://localhost:3000,http://localhost:8080"
    
    # Environment
    environment: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"


# Global settings instance
settings = Settings()
