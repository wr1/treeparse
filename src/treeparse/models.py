from typing import List, Optional, Callable, Any, Union
from pydantic import BaseModel
import argparse


class Argument(BaseModel):
    """Positional argument model."""

    name: str
    dest: Optional[str] = None
    arg_type: Any = str
    help: str = ""
    nargs: Union[int, str, None] = None
    default: Any = None
    sort_key: int = 0


class Option(BaseModel):
    """Option model."""

    flags: List[str]
    dest: Optional[str] = None
    arg_type: Any = str
    help: str = ""
    default: Any = None
    is_flag: bool = False
    sort_key: int = 0


class Command(BaseModel):
    """Command model."""

    name: str
    help: str = ""
    callback: Callable[[argparse.Namespace], None]
    arguments: List[Argument] = []
    options: List[Option] = []
    sort_key: int = 0


class Group(BaseModel):
    """Group model."""

    name: str
    help: str = ""
    subgroups: List["Group"] = []
    commands: List[Command] = []
    options: List[Option] = []
    sort_key: int = 0
