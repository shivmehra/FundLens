"""Application configuration loaded from environment variables."""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class Config:
    """Application configuration."""

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./fundlens.db")

    # File upload
    STAGING_DIR: str = os.getenv("STAGING_DIR", "./uploads/staging")
    STAGING_TTL_DAYS: int = int(os.getenv("STAGING_TTL_DAYS", "7"))
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".xlsx"]

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Schema configuration
    SCHEMA_CONFIG_PATH: str = os.getenv("SCHEMA_CONFIG_PATH", "./config/schema.json")

    @classmethod
    def ensure_staging_dir(cls) -> None:
        """Ensure staging directory exists."""
        Path(cls.STAGING_DIR).mkdir(parents=True, exist_ok=True)
        logger.info(f"Staging directory ensured: {cls.STAGING_DIR}")

    @classmethod
    def load_schema_config(cls) -> Dict:
        """Load schema configuration from JSON file."""
        try:
            with open(cls.SCHEMA_CONFIG_PATH, "r") as f:
                config = json.load(f)
            logger.info(f"Schema configuration loaded from {cls.SCHEMA_CONFIG_PATH}")
            return config
        except FileNotFoundError:
            logger.warning(f"Schema config file not found: {cls.SCHEMA_CONFIG_PATH}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in schema config: {cls.SCHEMA_CONFIG_PATH}")
            return {}

    @classmethod
    def get_file_size_limit(cls) -> int:
        """Get max file size in bytes."""
        return cls.MAX_FILE_SIZE_MB * 1024 * 1024
