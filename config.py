"""
Configuration management for Project Cerebrospinal Fluid.
Centralized configuration with validation and environment-aware defaults.
"""
import os
import sys
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path
import json

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class FirebaseConfig:
    """Firebase configuration with validation"""
    project_id: str
    credentials_path: Path
    database_url: str
    
    def __post_init__(self):
        """Validate Firebase configuration"""
        if not self.project_id:
            raise ValueError("Firebase project_id cannot be empty")
        if not self.credentials_path.exists():
            raise FileNotFoundError(f"Firebase credentials not found at {self.credentials_path}")
        if not self.database_url.startswith("https://"):
            raise ValueError(f"Invalid database URL: {self.database_url}")


@dataclass
class ModelConfig:
    """AI model configuration with retry logic"""
    model_name: str = "deepseek-chat"
    max_tokens: int = 4096
    temperature: float = 0.7
    max_retries: int = 3
    timeout_seconds: int = 30
    fallback_models: list = None
    
    def __post_init__(self):
        if self.fallback_models is None:
            self.fallback_models = ["gpt-3.5-turbo", "claude-instant"]


@dataclass
class LoggingConfig:
    """Structured logging configuration"""
    level: str = "INFO"
    format: str = "json"
    file_path: Optional[Path] = None
    
    def __post_init__(self):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")


class ConfigManager:
    """
    Central configuration manager with environment-specific overrides.
    Implements fail-fast pattern for critical configuration.
    """
    
    def __init__(self, env: str = None):
        self.env = env or os.getenv("ENVIRONMENT", "development")
        self._config: Dict[str, Any] = {}
        self._load_config()
        
    def _load_config(self) -> None:
        """Load configuration from environment and config files"""
        try:
            # Base configuration
            self._config = {
                "app": {
                    "name": "project_cerebrospinal_fluid",
                    "version": "1.0.0",
                    "environment": self.env
                },
                "firebase": self._load_firebase_config(),
                "model": ModelConfig(),
                "logging": LoggingConfig(
                    level=os.getenv("LOG_LEVEL", "INFO"),
                    file_path=Path(os.getenv("LOG_PATH", "logs/app.log"))
                ),
                "api": {
                    "max_concurrent_requests": int(os.getenv("MAX_CONCURRENT_REQUESTS", "10")),
                    "request_timeout": int(os.getenv("REQUEST_TIMEOUT", "60"))
                },
                "paths": {
                    "data_dir":