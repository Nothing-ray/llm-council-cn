"""Configuration for the LLM Council.

Configuration is loaded from JSON files in the following priority order:
1. Environment variable LLM_COUNCIL_CONFIG_PATH
2. config.local.json (for local overrides, not in version control)
3. config.json (default configuration)
4. Built-in DEFAULT_CONFIG (fallback)

API keys are always read from environment variables for security.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# Default Configuration (used as fallback)
# ============================================================================

DEFAULT_CONFIG = {
    "providers": {
        "openrouter": {
            "enabled": True,
            "api_url": "https://openrouter.ai/api/v1/chat/completions",
            "api_key_env": "OPENROUTER_API_KEY",
            "models": {
                "council": [
                    "openai/gpt-5.1",
                    "google/gemini-3-pro-preview",
                    "anthropic/claude-sonnet-4.5",
                    "x-ai/grok-4",
                ],
                "chairman": "google/gemini-3-pro-preview",
                "title_generator": "google/gemini-2.5-flash",
            }
        }
    },
    "storage": {
        "type": "json",
        "data_dir": "data/conversations"
    },
    "server": {
        "host": "0.0.0.0",
        "port": 8001,
        "cors_origins": [
            "http://localhost:5173",
            "http://localhost:3000"
        ]
    }
}


# ============================================================================
# Configuration Loading
# ============================================================================

def _find_config_file() -> Optional[Path]:
    """Find the configuration file to use.

    Priority:
    1. Environment variable LLM_COUNCIL_CONFIG_PATH
    2. config.local.json (for local development)
    3. config/config.json (config subdirectory)
    4. config.json (project root)

    Returns:
        Path object if found, None otherwise
    """
    # Check environment variable first
    env_path = os.getenv("LLM_COUNCIL_CONFIG_PATH")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path
        raise FileNotFoundError(f"Config file specified by LLM_COUNCIL_CONFIG_PATH not found: {env_path}")

    # Get the project root (when running as `python -m backend.main`, __file__ is backend/config.py)
    config_dir = Path(__file__).parent.parent

    # Check for local config (higher priority, not in version control)
    local_config = config_dir / "config.local.json"
    if local_config.exists():
        return local_config

    # Check for config subdirectory
    subdirectory_config = config_dir / "config" / "config.json"
    if subdirectory_config.exists():
        return subdirectory_config

    # Check for default config in project root
    default_config = config_dir / "config.json"
    if default_config.exists():
        return default_config

    return None


def _load_config() -> Dict[str, Any]:
    """Load configuration from JSON file or use defaults.

    Returns:
        Configuration dictionary
    """
    config_file = _find_config_file()

    if config_file is None:
        # No config file found, use defaults
        return DEFAULT_CONFIG.copy()

    try:
        # Use standard JSON parser (no comments support)
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Validate config has required structure
        if "providers" not in config:
            raise ValueError("Configuration must include 'providers' section")

        return config

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file {config_file}: {e}")
    except Exception as e:
        raise ValueError(f"Error loading config from {config_file}: {e}")


# Load configuration once at module import
_config = _load_config()


def _get_provider_config(provider_name: str) -> Dict[str, Any]:
    """Get configuration for a specific provider.

    Args:
        provider_name: Name of the provider (e.g., 'openrouter')

    Returns:
        Provider configuration dict

    Raises:
        ValueError: If provider not found or disabled
    """
    provider = _config.get("providers", {}).get(provider_name)

    if not provider:
        raise ValueError(f"Provider '{provider_name}' not found in configuration")

    if not provider.get("enabled", False):
        raise ValueError(f"Provider '{provider_name}' is disabled")

    return provider


# ============================================================================
# Legacy API - Backward compatibility with existing code
# ============================================================================

# OpenRouter configuration
_provider_config = _get_provider_config("openrouter")
OPENROUTER_API_URL = _provider_config["api_url"]
OPENROUTER_API_KEY = os.getenv(_provider_config["api_key_env"])

if not OPENROUTER_API_KEY:
    raise ValueError(
        f"API key not found. Please set environment variable: "
        f"{_provider_config['api_key_env']}"
    )

# Council models configuration
_models_config = _provider_config["models"]
COUNCIL_MODELS: List[str] = _models_config["council"]
CHAIRMAN_MODEL: str = _models_config["chairman"]

# Title generator model (previously hardcoded in council.py)
TITLE_GENERATOR_MODEL = _models_config.get("title_generator", "google/gemini-2.5-flash")

# Storage configuration
_storage_config = _config.get("storage", {})
DATA_DIR: str = _storage_config.get("data_dir", "data/conversations")

# Server configuration (for main.py)
_server_config = _config.get("server", {})
SERVER_HOST: str = _server_config.get("host", "0.0.0.0")
SERVER_PORT: int = _server_config.get("port", 8001)
CORS_ORIGINS: List[str] = _server_config.get("cors_origins", [
    "http://localhost:5173",
    "http://localhost:3000"
])


# ============================================================================
# New API - Future-proof configuration access
# ============================================================================

def get_config() -> Dict[str, Any]:
    """Get the full configuration dictionary.

    Returns:
        Complete configuration as loaded from JSON file
    """
    return _config.copy()


def get_provider_models(provider_name: str = "openrouter") -> Dict[str, Any]:
    """Get models configuration for a provider.

    Args:
        provider_name: Name of the provider (default: 'openrouter')

    Returns:
        Dict with 'council', 'chairman', and optional 'title_generator'
    """
    provider = _get_provider_config(provider_name)
    return provider.get("models", {})


def get_server_config() -> Dict[str, Any]:
    """Get server configuration.

    Returns:
        Dict with 'host', 'port', and 'cors_origins'
    """
    return _config.get("server", {})


def get_storage_config() -> Dict[str, Any]:
    """Get storage configuration.

    Returns:
        Dict with 'type' and 'data_dir'
    """
    return _config.get("storage", {})


def get_active_provider() -> str:
    """Get the currently active provider name.

    Returns:
        Provider name (e.g., 'openrouter', 'siliconflow')
    """
    return _config.get("active_provider", "openrouter")


def get_provider_config(provider_name: str = None) -> Dict[str, Any]:
    """Get configuration for a specific provider.

    Args:
        provider_name: Name of the provider (e.g., 'openrouter', 'siliconflow').
                     If None, returns the active provider's configuration.

    Returns:
        Provider configuration dict with 'api_url', 'api_key_env', 'models', etc.

    Raises:
        ValueError: If provider not found or disabled
    """
    if provider_name is None:
        provider_name = get_active_provider()

    provider = _config.get("providers", {}).get(provider_name)

    if not provider:
        raise ValueError(f"Provider '{provider_name}' not found in configuration")

    if not provider.get("enabled", False):
        raise ValueError(f"Provider '{provider_name}' is disabled")

    return provider


def reload_config() -> None:
    """Reload configuration from file.

    Useful for development when config file changes.
    In production, restart is recommended.
    """
    global _config, _provider_config, _models_config, _storage_config, _server_config
    global OPENROUTER_API_URL, OPENROUTER_API_KEY, COUNCIL_MODELS, CHAIRMAN_MODEL
    global TITLE_GENERATOR_MODEL, DATA_DIR, SERVER_HOST, SERVER_PORT, CORS_ORIGINS

    _config = _load_config()

    # Re-update global variables
    _provider_config = _get_provider_config("openrouter")
    OPENROUTER_API_URL = _provider_config["api_url"]
    OPENROUTER_API_KEY = os.getenv(_provider_config["api_key_env"])

    _models_config = _provider_config["models"]
    COUNCIL_MODELS = _models_config["council"]
    CHAIRMAN_MODEL = _models_config["chairman"]
    TITLE_GENERATOR_MODEL = _models_config.get("title_generator", "google/gemini-2.5-flash")

    _storage_config = _config.get("storage", {})
    DATA_DIR = _storage_config.get("data_dir", "data/conversations")

    _server_config = _config.get("server", {})
    SERVER_HOST = _server_config.get("host", "0.0.0.0")
    SERVER_PORT = _server_config.get("port", 8001)
    CORS_ORIGINS = _server_config.get("cors_origins", [
        "http://localhost:5173",
        "http://localhost:3000"
    ])
