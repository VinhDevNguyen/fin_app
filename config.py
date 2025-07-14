from __future__ import annotations
import os
from pathlib import Path
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Legacy settings class for backward compatibility."""
    gdrive_auth_mode: str = Field("oauth", validation_alias="GDRIVE_AUTH_MODE")
    gdrive_credentials: str = "credentials.json"
    gdrive_token: str = "token.json"
    gdrive_sa_key: str | None = None

    model_config = {
        "env_file": ".env"
    }

class AppSettings(BaseSettings):
    """Enhanced application settings with environment variable support."""
    
    # Google Drive settings
    gdrive_auth_mode: Literal["oauth", "service_account"] = Field("oauth", validation_alias="GDRIVE_AUTH_MODE")
    gdrive_credentials: str = Field("credentials.json", validation_alias="GDRIVE_CREDENTIALS")
    gdrive_token: str = Field("token.json", validation_alias="GDRIVE_TOKEN")
    gdrive_sa_key: str | None = Field(None, validation_alias="GDRIVE_SA_KEY")
    
    # Target folder settings
    target_folder_name: str = Field("Debit_VP_Bank", validation_alias="TARGET_FOLDER_NAME")
    
    # PDF processing settings
    pdf_engine: Literal["pymupdf", "pdfminer"] = Field("pymupdf", validation_alias="PDF_ENGINE")
    pdf_password: str | None = Field("05074248", validation_alias="PDF_PASSWORD")
    
    # Output settings
    output_dir: str = Field("processed_statements", validation_alias="OUTPUT_DIR")
    max_files: int | None = Field(None, validation_alias="MAX_FILES")  # None = process all
    
    # Logging settings
    log_level: str = Field("INFO", validation_alias="LOG_LEVEL")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }

# Legacy settings instance for backward compatibility
settings = Settings()

# New enhanced settings instance
app_settings = AppSettings()