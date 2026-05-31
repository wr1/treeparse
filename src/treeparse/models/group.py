"""group model."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .argument import argument
from .chain import chain
from .command import command
from .option import option


class group(BaseModel):
    """group model."""

    name: str
    help: str = ""
    subgroups: list[group] = Field(default_factory=list)
    commands: list[command | chain] = Field(default_factory=list)
    options: list[option] = Field(default_factory=list)
    arguments: list[argument] = Field(default_factory=list)
    sort_key: int = 0
    fold: bool = False

    @property
    def display_name(self) -> str:
        """Get display name."""
        return self.name
