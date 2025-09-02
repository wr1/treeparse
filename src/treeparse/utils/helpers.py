"""Helper functions."""

import yaml
from pathlib import Path
from typing import Dict, Any


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """Load YAML configuration file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}
