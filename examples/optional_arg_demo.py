"""Demo: required vs optional positional arguments.

Required args show as <ARG>, optional as [ARG] or [ARG=default].
"""

from treeparse import argument, cli, command


def greet(name: str, title: str):
    prefix = f"{title} " if title else ""
    print(f"Hello, {prefix}{name}!")


def convert(input: str, output: str, fmt: str):
    dest = output or (input.rsplit(".", 1)[0] + f".{fmt}")
    print(f"Converting {input} → {dest} (format: {fmt})")


app = cli(
    name="demo",
    help="Demonstrates required vs optional positional arguments.",
    show_types=True,
    show_defaults=True,
    commands=[
        command(
            name="greet",
            help="Greet someone, with an optional title.",
            callback=greet,
            arguments=[
                argument(name="name", arg_type=str, help="Name to greet"),
                argument(name="title", arg_type=str, nargs="?", default=None, help="Optional title (Dr, Prof, ...)"),
            ],
        ),
        command(
            name="convert",
            help="Convert a file, with an optional output path and format.",
            callback=convert,
            arguments=[
                argument(name="input", arg_type=str, help="Input file path"),
                argument(name="output", arg_type=str, nargs="?", default=None, help="Output path (defaults to input stem)"),
                argument(name="fmt", arg_type=str, nargs="?", default="png", help="Output format"),
            ],
        ),
    ],
)


def main():
    app.run()


if __name__ == "__main__":
    main()
