from __future__ import annotations
import os
from pathlib import Path
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings
class AppSettings(BaseSettings):
    """Enhanced application settings with environment variable support."""
    
    # Google Drive settings
    gdrive_auth_mode: Literal["oauth", "service_account"] = Field(validation_alias="GDRIVE_AUTH_MODE")
    gdrive_credentials: str = Field(validation_alias="GDRIVE_CREDENTIALS")
    gdrive_token: str = Field(validation_alias="GDRIVE_TOKEN")
    gdrive_sa_key: str | None = Field(None, validation_alias="GDRIVE_SA_KEY")
    
    # Target folder settings
    target_folder_name: str = Field(validation_alias="TARGET_FOLDER_NAME")
    
    # PDF processing settings
    pdf_engine: Literal["pymupdf", "pdfminer"] = Field(validation_alias="PDF_ENGINE")
    pdf_password: str | None = Field(None, validation_alias="PDF_PASSWORD")
    
    # Output settings
    output_dir: str = Field(validation_alias="OUTPUT_DIR")
    max_files: int | None = Field(None, validation_alias="MAX_FILES")  # None = process all
    
    # Logging settings
    log_level: str = Field(validation_alias="LOG_LEVEL")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }

# New enhanced settings instance
app_settings = AppSettings()