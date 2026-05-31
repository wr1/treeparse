"""Show every built-in color theme side-by-side."""

from rich.console import Console
from rich.rule import Rule

from treeparse import argument, cli, command, group, option
from treeparse.utils.color_config import color_theme


def _make_app(theme: color_theme) -> cli:
    return cli(
        name="myapp",
        help="A demo app for previewing color themes.",
        theme=theme,
        show_types=True,
        show_defaults=True,
        commands=[
            command(
                name="deploy",
                help="Deploy the application to a target environment.",
                callback=lambda env, dry_run: None,
                arguments=[
                    argument(name="env", arg_type=str, help="Target environment"),
                ],
                options=[
                    option(
                        flags=["--dry-run", "-n"],
                        arg_type=bool,
                        default=False,
                        help="Simulate without making changes",
                    ),
                ],
            ),
        ],
        subgroups=[
            group(
                name="db",
                help="Database management commands.",
                commands=[
                    command(
                        name="migrate",
                        help="Run pending migrations.",
                        callback=lambda: None,
                    ),
                    command(
                        name="seed",
                        help="Seed the database with fixture data.",
                        callback=lambda: None,
                    ),
                ],
            ),
        ],
    )


def main():
    console = Console()
    for theme in color_theme:
        console.print()
        console.print(Rule(f"[bold]Theme: {theme.value}[/bold]"))
        console.print()
        app = _make_app(theme)
        app.print_help([])


if __name__ == "__main__":
    main()
