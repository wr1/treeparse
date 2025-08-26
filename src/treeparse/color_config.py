from enum import Enum
from pydantic import BaseModel


class ColorTheme(Enum):
    DEFAULT = "default"
    MONOCHROME = "monochrome"


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

    @classmethod
    def from_theme(cls, theme: ColorTheme):
        if theme == ColorTheme.DEFAULT:
            return cls()
        elif theme == ColorTheme.MONOCHROME:
            return cls(
                app="rgb(200,200,200)",
                group="rgb(180,180,180)",
                command="rgb(160,160,160)",
                argument="rgb(140,140,140)",
                option="rgb(120,120,120)",
                option_help="rgb(100,100,100)",
                requested_help="rgb(255,255,255)",
                normal_help="rgb(220,220,220)",
                type_color="rgb(160,160,160)",
                connector="rgb(80,80,80)",
                guide="rgb(80,80,80)",
            )
