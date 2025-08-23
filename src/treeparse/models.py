from typing import List, Optional, Callable, Any, Union
import inspect
from pydantic import BaseModel


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
    callback: Callable[..., None]
    arguments: List[Argument] = []
    options: List[Option] = []
    sort_key: int = 0

    def validate(self):
        """Validate that callback parameters match defined arguments and options."""
        sig = inspect.signature(self.callback)
        param_names = set(sig.parameters.keys())
        provided = set()
        for arg in self.arguments:
            dest = arg.dest or arg.name
            provided.add(dest)
        for opt in self.options:
            dest = opt.dest or opt.flags[0].lstrip("-").replace("-", "_")
            provided.add(dest)
        if param_names != provided:
            raise ValueError(
                f"Callback parameters {param_names} do not match provided args/options "
                f"{provided} for command {self.name}"
            )


class Group(BaseModel):
    """Group model."""

    name: str
    help: str = ""
    subgroups: List["Group"] = []
    commands: List[Command] = []
    options: List[Option] = []
    sort_key: int = 0
