from typing import List
from pydantic import BaseModel
from .command import command
from .option import option


class group(BaseModel):
    """group model."""

    name: str
    help: str = ""
    subgroups: List["group"] = []
    commands: List[command] = []
    options: List[option] = []
    sort_key: int = 0
