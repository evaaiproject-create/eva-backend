"""
================================================================================
CONFIGURATION MANAGEMENT FOR EVA BACKEND
================================================================================

PURPOSE:
    This file manages all configuration settings for the Eva backend.
    Settings are loaded from environment variables, with sensible defaults
    for development.

HOW IT WORKS:
    1. Looks for a .env file in the project root
    2. Loads environment variables from that file
    3. Falls back to default values if not set

ENVIRONMENT VARIABLES:
    GOOGLE_CLOUD_PROJECT     - Your GCP project ID
    GOOGLE_APPLICATION_CREDENTIALS - Path to service account JSON
    GOOGLE_CLIENT_ID         - OAuth client ID
    GOOGLE_CLIENT_SECRET     - OAuth client secret
    GOOGLE_API_KEY           - API key for Gemini
    API_HOST                 - Server host (default: 0.0.0.0)
    API_PORT                 - Server port (default: 8000)
    API_SECRET_KEY           - Secret for JWT tokens (CHANGE IN PRODUCTION!)
    MAX_USERS                - Maximum allowed users
    CORS_ORIGINS             - Comma-separated allowed origins
    ENVIRONMENT              - "development" or "production"

================================================================================
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    These settings configure:
    - Google Cloud integration (project, credentials, API keys)
    - OAuth authentication (client ID/secret)
    - API server configuration (host, port, secret)
    - Security settings (CORS, user limits)
    
    USAGE:
        from app.config import settings
        print(settings.google_api_key)
    """
    
    # ===== GOOGLE CLOUD CONFIGURATION =====
    # These connect to your Google Cloud project
    
    google_cloud_project: str = "eva-backend-service"
    """
    Your Google Cloud project ID.
    Found in: Google Cloud Console > Project selector
    """
    
    google_application_credentials: str = "service-account-key.json"
    """
    Path to your service account JSON key file.
    Used for: Firestore access, other GCP services
    """
    
    google_client_id: str = "81503423918-3sujbguhqjn6ns89hjb3858t92aksher.apps.googleusercontent.com"
    """
    OAuth 2.0 Client ID from Google Cloud Console.
    Used for: Verifying Google Sign-In tokens from the Android app
    """
    
    google_client_secret: str = ""
    """
    OAuth 2.0 Client Secret from Google Cloud Console.
    Used for: OAuth token exchange (if needed)
    """
    
    google_api_key: str = ""
    """
    Google API Key for Gemini AI.
    Used for: Communicating with Gemini 2.0 Flash model
    Get it from: Google AI Studio (ai.google.dev)
    """

    # ===== API CONFIGURATION =====
    # These control how the server runs
    
    api_host: str = "0.0.0.0"
    """
    Host address to bind to.
    0.0.0.0 = Accept connections from anywhere (needed for Cloud Run)
    127.0.0.1 = Only accept local connections
    """
    
    api_port: int = 8000
    """
    Port number to listen on.
    Cloud Run may override this with the PORT environment variable.
    """
    
    api_secret_key: str = "ChangeThisSecretForProduction"
    """
    Secret key for signing JWT tokens.
    IMPORTANT: Generate a new random key for production!
    Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    """

    # ===== USER MANAGEMENT =====
    
    max_users: int = 5
    """
    Maximum number of users allowed to register.
    This is a soft limit for personal/hobby use.
    """

    # ===== CORS CONFIGURATION =====
    
    cors_origins: str = "http://localhost:3000,http://localhost:8080"
    """
    Comma-separated list of allowed origins for CORS.
    These domains can make API requests to this backend.
    
    For Android app: You typically don't need to add anything here
    since mobile apps don't use CORS.
    """

    # ===== ENVIRONMENT =====
    
    environment: str = "development"
    """
    Current environment: "development" or "production"
    
    Development: Enables debug logging, auto-reload
    Production: Hides error details, optimized performance
    """

    # ===== COMPUTED PROPERTIES =====
    
    @property
    def cors_origins_list(self) -> List[str]:
        """
        Parse CORS origins string into a list.
        
        EXAMPLE:
            "http://localhost:3000,http://localhost:8080"
            becomes
            ["http://localhost:3000", "http://localhost:8080"]
        """
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def is_production(self) -> bool:
        """
        Check if running in production environment.
        
        RETURNS:
            True if environment is "production", False otherwise
        """
        return self.environment.lower() == "production"

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = False


# Create singleton settings instance
# Import this in other files: from app.config import settings
settings = Settings()
