import configparser
import os
from typing import List, Optional

# Config file path: data/config.ini relative to project root
_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "config.ini"
)

_config = None

def _load_config() -> configparser.ConfigParser:
    """Load config from disk (cached after first read)."""
    global _config
    if _config is None:
        _config = configparser.ConfigParser()
        if os.path.exists(_CONFIG_PATH):
            _config.read(_CONFIG_PATH)
    return _config



def reload_config():
    """Force reload config from disk."""
    global _config
    _config = None

def get(section: str, key: str, fallback: Optional[str] = None) -> Optional[str]:
    """Get a config value. Returns fallback if not found or empty."""
    cfg = _load_config()
    value = cfg.get(section, key, fallback=fallback)
    # Treat empty strings as None
    return value if value and value.strip() else fallback

def get_counsel_name() -> Optional[str]:
    """Get the default counsel name."""
    return get("counsel", "name")

def get_counsel_aliases() -> List[str]:
    """Get all counsel names (primary + aliases) for flexible matching."""
    names = []
    primary = get_counsel_name()
    if primary:
        names.append(primary)
    aliases_str = get("counsel", "aliases")
    if aliases_str:
        for alias in aliases_str.split(","):
            alias = alias.strip()
            if alias and alias not in names:
                names.append(alias)
    return names

def get_counsel_address() -> Optional[str]:
    """Get the counsel's address (for invoices)."""
    return get("counsel", "address")

def get_counsel_phone() -> Optional[str]:
    """Get the counsel's phone number."""
    return get("counsel", "phone")

def get_counsel_email() -> Optional[str]:
    """Get the counsel's email."""
    return get("counsel", "email")

def get_default_zone() -> str:
    """Get the default zone type for NGT searches."""
    return get("defaults", "zone", fallback="1") or "1"

def get_default_case_type() -> str:
    """Get the default case type."""
    return get("defaults", "case_type", fallback="1") or "1"

def get_default_download_dir() -> str:
    """Get the default download directory."""
    return get("defaults", "download_dir", fallback="data/orders") or "data/orders"

def config_path() -> str:
    """Return the config file path."""
    return _CONFIG_PATH
