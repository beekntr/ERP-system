"""
Configuration module for ERP Purchase Order System.
Handles environment variables and application settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application configuration settings."""
    
    # Database Configuration
    # Default to SQLite for easy setup (no PostgreSQL required)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./erp_po_system.db"
    )
    
    # JWT Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/callback")
    
    # Application Settings
    APP_NAME: str = "ERP Purchase Order System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Tax Configuration
    TAX_RATE: float = float(os.getenv("TAX_RATE", "0.05"))  # 5% tax
    
    # Optional: LLM API Configuration for AI descriptions
    # Supports OpenAI or Google Gemini (free tier available)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    

# Create settings instance
settings = Settings()
