from typing import List
from pydantic import BaseModel


class group(BaseModel):
    """group model."""

    name: str
    help: str = ""
    subgroups: List["group"] = []
    commands: List["command"] = []
    options: List["option"] = []
    sort_key: int = 0

