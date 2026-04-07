"""Color configuration for help output."""

from enum import Enum

from pydantic import BaseModel


class ColorTheme(Enum):
    DEFAULT = "default"
    MONOCHROME = "monochrome"
    MONONEON = "mononeon"
    RED_WHITE_BLUE = "red_white_blue"
    GITHUB = "github"
    MONOKAI = "monokai"
    TOKYO_NIGHT = "tokyo_night"


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
            # Neon green base: rgb(57,255,20)
            # Varying intensities by scaling brightness
            return cls(
                app="bold italic rgb(57,255,20)",  # full bright
                group="bold rgb(51,229,18)",  # 90%
                command="rgb(46,204,16)",  # 80%
                argument="rgb(40,179,14)",  # 70%
                option="rgb(34,153,12)",  # 60%
                option_help="italic rgb(29,128,10)",  # 50%
                requested_help="rgb(57,255,20)",  # full
                normal_help="rgb(46,204,16)",  # 80%
                type_color="rgb(40,179,14)",  # 70%
                connector="rgb(29,128,10)",  # 50%
                guide="rgb(29,128,10)",  # 50%
            )
        elif theme == ColorTheme.RED_WHITE_BLUE:
            # Red / White(light grey) / Blue patriotic theme
            # "White" replaced with light grey (rgb-based) for perfect readability on light terminals
            return cls(
                app="bold rgb(255,50,50)",  # red for the app title
                group="bold rgb(160,180,255)",  # blue for groups
                command="rgb(80,90,255)",  # blue for commands
                argument="rgb(237,237,237)",  # light grey (instead of white)
                option="rgb(255,50,50)",  # red accents for options
                option_help="italic rgb(255,80,80)",
                requested_help="bold rgb(237,237,237)",  # light grey help (user request)
                normal_help="bold rgb(185,185,185)",  # soft light grey for dimmed text
                type_color="dim rgb(120,140,255)",
                connector="rgb(105,105,105)",
                guide="rgb(95,95,95)",
            )
        elif theme == ColorTheme.GITHUB:
            # GitHub dark syntax palette (#0d1117 background)
            # purple=app, blue=group/type, light-blue=command, orange=argument,
            # red-pink=option, near-white=help, grey=dim help
            return cls(
                app="bold rgb(210,168,255)",  # #d2a8ff — purple (prominent title)
                group="bold rgb(121,192,255)",  # #79c0ff — blue (structural)
                command="rgb(165,214,255)",  # #a5d6ff — light blue (action)
                argument="rgb(255,166,87)",  # #ffa657 — orange (constant-like)
                option="rgb(255,123,114)",  # #ff7b72 — red-pink (keyword-like)
                option_help="italic rgb(255,123,114)",
                requested_help="bold rgb(230,237,243)",  # #e6edf3 — near-white
                normal_help="rgb(139,148,158)",  # #8b949e — comment grey
                type_color="dim rgb(121,192,255)",  # #79c0ff — blue
                connector="rgb(48,54,61)",  # #30363d — dark border
                guide="rgb(48,54,61)",
            )
        elif theme == ColorTheme.TOKYO_NIGHT:
            # Tokyo Night palette — popular VS Code dark theme
            # purple=app, cyan=group/type, blue=command, orange=argument,
            # red=option, light-fg=help, comment-blue=dim help
            return cls(
                app="bold rgb(187,154,247)",   # #bb9af7 — purple (prominent)
                group="bold rgb(125,207,255)", # #7dcfff — cyan (structural)
                command="rgb(122,162,247)",    # #7aa2f7 — blue (action)
                argument="rgb(255,158,100)",   # #ff9e64 — orange (constant-like)
                option="rgb(247,118,142)",     # #f7768e — red (keyword-like)
                option_help="italic rgb(247,118,142)",
                requested_help="bold rgb(192,202,245)",  # #c0caf5 — foreground
                normal_help="rgb(86,95,137)",  # #565f89 — comment blue-grey
                type_color="dim rgb(125,207,255)",       # #7dcfff — cyan
                connector="rgb(31,35,53)",     # #1f2335 — dark bg variant
                guide="rgb(31,35,53)",
            )
        elif theme == ColorTheme.MONOKAI:
            # Classic Monokai palette (Sublime Text / TextMate)
            # green=app/command, cyan=group/type, purple=argument,
            # pink=option, near-white=help, grey-brown=dim help
            return cls(
                app="bold rgb(166,226,46)",  # #a6e22e — green (function-like)
                group="bold rgb(102,217,232)",  # #66d9e8 — cyan (type-like)
                command="rgb(166,226,46)",  # #a6e22e — green
                argument="rgb(174,129,255)",  # #ae81ff — purple (constant-like)
                option="rgb(249,38,114)",  # #f92672 — pink (keyword-like)
                option_help="italic rgb(249,38,114)",
                requested_help="bold rgb(248,248,242)",  # #f8f8f2 — near-white
                normal_help="rgb(117,113,94)",  # #75715e — grey-brown comment
                type_color="rgb(102,217,232)",  # #66d9e8 — cyan
                connector="rgb(73,72,62)",  # #49483e — dark monokai line
                guide="rgb(73,72,62)",
            )
