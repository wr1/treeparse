"""Color configuration for help output."""

from enum import Enum
from pydantic import BaseModel


class ColorTheme(Enum):
    DEFAULT = "default"
    MONOCHROME = "monochrome"
    MONONEON = "mononeon"
    RED_WHITE_BLUE = "red_white_blue"


class color_config(BaseModel):
    """Color configuration for help output."""

    app: str = "bold bright_cyan"
    group: str = "bold green"
    command: str = "cyan"
    argument: str = "orange1"
    option: str = "orange"
    option_help: str = "italic orange"
    requested_help: str = "bold white"
    normal_help: str = "bold rgb(180,180,180)"
    type_color: str = "dim white"
    connector: str = "rgb(45,45,45)"
    guide: str = "rgb(45,45,45)"

    @classmethod
    def from_theme(cls, theme: ColorTheme):
        if theme == ColorTheme.DEFAULT:
            return cls()
        elif theme == ColorTheme.MONOCHROME:
            return cls(
                app="bold italic rgb(200,200,200)",
                group="bold rgb(180,180,180)",
                command="rgb(160,160,160)",
                argument="rgb(140,140,140)",
                option="rgb(120,120,120)",
                option_help="italic rgb(100,100,100)",
                requested_help="rgb(255,255,255)",
                normal_help="bold rgb(200,200,200)",
                type_color="rgb(160,160,160)",
                connector="rgb(80,80,80)",
                guide="rgb(80,80,80)",
            )
        elif theme == ColorTheme.MONONEON:
            return cls(
                app="bold italic rgb(57,255,20)",
                group="bold rgb(51,229,18)",
                command="rgb(46,204,16)",
                argument="rgb(40,179,14)",
                option="rgb(34,153,12)",
                option_help="italic rgb(29,128,10)",
                requested_help="rgb(57,255,20)",
                normal_help="rgb(46,204,16)",
                type_color="rgb(40,179,14)",
                connector="rgb(29,128,10)",
                guide="rgb(29,128,10)",
            )
        elif theme == ColorTheme.RED_WHITE_BLUE:
            # Strong high-contrast patriotic theme (bright red + blue + readable light-grey text)
            # Fixed the "all white" issue: normal_help is now darker, argument/requested_help use bright_white
            return cls(
                app="bold bright_red",  # vivid patriotic red
                group="bold bright_blue",  # vivid blue for groups
                command="bright_blue",  # bright blue for commands
                argument="bright_white",  # light grey (readable on light terminals)
                option="bright_red",  # red accents
                option_help="italic bright_red",
                requested_help="bold bright_white",
                normal_help="bold rgb(200,200,200)",  # darker grey – visible on both light & dark
                type_color="dim bright_blue",
                connector="rgb(120,120,120)",
                guide="rgb(100,100,100)",
            )
