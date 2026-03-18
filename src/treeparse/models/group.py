"""group model."""

from typing import List, Union

from pydantic import BaseModel

from .argument import argument
from .chain import chain
from .command import command
from .option import option


class group(BaseModel):
    """group model."""

    name: str
    help: str = ""
    subgroups: List["group"] = []
    commands: List[Union[command, chain]] = []
    options: List[option] = []
    arguments: List[argument] = []
    sort_key: int = 0
    fold: bool = False

    @property
    def display_name(self) -> str:
        """Get display name."""
        return self.name
