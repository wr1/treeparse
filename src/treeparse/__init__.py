"""Treeparse package initialization."""

from .models.argument import argument
from .models.option import option
from .models.command import command
from .models.chain import chain
from .models.group import group
from .models.cli import cli
from .utils.color_config import color_config
from .testing import CliRunner, CliResult

# Rebuild models to handle forward references
argument.model_rebuild()
option.model_rebuild()
command.model_rebuild()
chain.model_rebuild()
group.model_rebuild()
cli.model_rebuild()
color_config.model_rebuild()

__all__ = [
    "argument",
    "option",
    "command",
    "chain",
    "group",
    "cli",
    "color_config",
    "CliRunner",
    "CliResult",
]
