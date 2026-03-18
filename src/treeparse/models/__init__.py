"""Models package initialization."""

from ..utils.color_config import color_config
from .argument import argument
from .chain import chain
from .cli import cli
from .command import command
from .group import group
from .option import option

# Rebuild models to handle forward references
argument.model_rebuild()
option.model_rebuild()
command.model_rebuild()
chain.model_rebuild()
group.model_rebuild()
cli.model_rebuild()
color_config.model_rebuild()

__all__ = ["argument", "option", "command", "chain", "group", "cli", "color_config"]
