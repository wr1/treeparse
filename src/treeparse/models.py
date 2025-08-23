from typing import List, Optional, Callable, Any, Union
import inspect
from pydantic import BaseModel


class argument(BaseModel):
    """Positional argument model."""

    name: str
    dest: Optional[str] = None
    arg_type: Any = str
    help: str = ""
    nargs: Union[int, str, None] = None
    default: Any = None
    sort_key: int = 0


class option(BaseModel):
    """option model."""

    flags: List[str]
    dest: Optional[str] = None
    arg_type: Any = str
    help: str = ""
    default: Any = None
    nargs: Union[int, str, None] = None
    is_flag: bool = False
    sort_key: int = 0


class command(BaseModel):
    """command model."""

    name: str
    help: str = ""
    callback: Callable[..., None]
    arguments: List[argument] = []
    options: List[option] = []
    sort_key: int = 0

    def validate(self):
        """Validate that callback parameters match defined arguments and options in name and type."""
        sig = inspect.signature(self.callback)
        param_names = set(sig.parameters.keys())
        param_types = {
            k: v.annotation
            for k, v in sig.parameters.items()
            if v.annotation != inspect.Parameter.empty
        }
        provided = {}
        for arg in self.arguments:
            dest = arg.dest or arg.name
            arg_type = arg.arg_type
            if arg.nargs in ["*", "+"]:
                arg_type = List[arg_type]
            provided[dest] = arg_type
        for opt in self.options:
            dest = opt.dest or opt.flags[0].lstrip("-").replace("-", "_")
            opt_type = bool if opt.is_flag else opt.arg_type
            if opt.nargs in ["*", "+"] and not opt.is_flag:
                opt_type = List[opt_type]
            provided[dest] = opt_type
        provided_names = set(provided.keys())
        if param_names != provided_names:
            missing = param_names - provided_names
            extra = provided_names - param_names
            error_msg = f"Parameter name mismatch for command '[bold red]{self.name}[/bold red]': "
            if missing:
                error_msg += f"Missing parameters in CLI definition: [yellow]{missing}[/yellow]. "
            if extra:
                error_msg += (
                    f"Extra parameters in CLI definition: [yellow]{extra}[/yellow]. "
                )
            error_msg += f"Callback expects: [cyan]{param_names}[/cyan], CLI provides: [cyan]{provided_names}[/cyan]"
            raise ValueError(error_msg)
        # Check types
        type_mismatches = []
        for param, p_type in param_types.items():
            cli_type = provided.get(param)
            if cli_type != p_type:
                type_mismatches.append(
                    f"{param}: callback [green]{p_type.__name__}[/green] vs CLI [green]{cli_type.__name__}[/green]"
                )
        if type_mismatches:
            error_msg = (
                f"Parameter type mismatch for command '[bold red]{self.name}[/bold red]': "
                + "; ".join(type_mismatches)
            )
            raise ValueError(error_msg)


class group(BaseModel):
    """group model."""

    name: str
    help: str = ""
    subgroups: List["group"] = []
    commands: List[command] = []
    options: List[option] = []
    sort_key: int = 0


class color_config(BaseModel):
    """Color configuration for help output."""

    app: str = "bold bright_cyan"
    group: str = "bold green"
    command: str = "cyan"
    argument: str = "orange1"
    option: str = "yellow"
    option_help: str = "italic yellow"
    requested_help: str = "bold white"
    normal_help: str = "white"
    type_color: str = "dim white"
