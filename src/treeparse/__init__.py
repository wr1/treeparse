"""Treeparse package initialization."""

from __future__ import annotations

from .models.argument import argument
from .models.chain import chain
from .models.cli import cli
from .models.command import command
from .models.group import group
from .models.option import option
from .testing import cli_result, cli_runner
from .utils.color_config import color_config

# Model rebuilds (forward-reference resolution) live in ``models/__init__.py``,
# which runs first when the submodules above are imported.

__all__ = [
    "argument",
    "chain",
    "cli",
    "cli_result",
    "cli_runner",
    "color_config",
    "command",
    "group",
    "option",
]
