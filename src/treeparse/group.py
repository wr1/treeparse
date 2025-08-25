from typing import List, Union
from pydantic import BaseModel, computed_field
from .command import command
from .chain import Chain
from .option import option
from .argument import argument


class group(BaseModel):
    """group model."""

    name: str
    help: str = ""
    subgroups: List["group"] = []
    commands: List[Union[command, Chain]] = []
    options: List[option] = []
    sort_key: int = 0

    @computed_field
    @property
    def display_name(self) -> str:
        """Get display name, stripping .py suffix if present."""
        return self.name.removesuffix(".py")

    @computed_field
    @property
    def effective_options(self) -> List[option]:
        return self.options

    @computed_field
    @property
    def effective_arguments(self) -> List[argument]:
        return []
