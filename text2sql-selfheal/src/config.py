"""
Configuration Management

Loads configuration from environment variables and .env file
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Configuration manager for Text-to-SQL Self-Healing System"""

    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration

        Args:
            env_file: Path to .env file (optional)
        """
        # Load environment variables from .env file
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to load from default location
            env_path = Path(__file__).parent.parent / '.env'
            if env_path.exists():
                load_dotenv(env_path)

        # Load configuration
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY', '')
        self.model = os.getenv('MODEL', 'claude-sonnet-4-20250514')
        self.database_path = os.getenv('DATABASE_PATH', 'data/example.db')
        self.schema_path = os.getenv('SCHEMA_PATH', 'data/schema.json')
        self.max_retries = int(os.getenv('MAX_RETRIES', '2'))
        self.confidence_threshold = float(os.getenv('CONFIDENCE_THRESHOLD', '0.7'))
        self.verbose = os.getenv('VERBOSE', 'false').lower() == 'true'

    def validate(self) -> bool:
        """
        Validate configuration

        Returns:
            True if configuration is valid
        """
        if not self.anthropic_api_key:
            print("Error: ANTHROPIC_API_KEY not set")
            return False

        return True

    def __repr__(self) -> str:
        """String representation (masks API key)"""
        return f"""Config(
    model={self.model},
    database_path={self.database_path},
    schema_path={self.schema_path},
    max_retries={self.max_retries},
    confidence_threshold={self.confidence_threshold},
    verbose={self.verbose},
    api_key={'***' if self.anthropic_api_key else 'NOT SET'}
)"""
