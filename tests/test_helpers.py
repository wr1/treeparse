import pytest
import tempfile
import os
from pathlib import Path
from treeparse.utils.helpers import load_yaml_config


def test_load_yaml_config():
    """Test loading YAML config."""
    config_data = {"key": "value", "number": 42}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        import yaml
        yaml.dump(config_data, f)
        config_path = f.name
    try:
        result = load_yaml_config(config_path)
        assert result == config_data
    finally:
        os.unlink(config_path)


def test_load_yaml_config_file_not_found():
    """Test loading YAML config with non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_yaml_config("nonexistent.yml")


def test_load_yaml_config_empty():
    """Test loading empty YAML config."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write("# empty")
        config_path = f.name
    try:
        result = load_yaml_config(config_path)
        assert result == {}
    finally:
        os.unlink(config_path)
