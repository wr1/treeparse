from pydantic import BaseModel


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
    connector: str = "rgb(45,45,45)"
    guide: str = "rgb(45,45,45)"
