import logging
from typing import List

# Run via: uv run --with-editable . python examples/list_demo.py
# or after `pip install -e .[dev]`
from treeparse import argument, cli, command, option

logging.basicConfig(level=logging.INFO)


def echo(words: List[str]):
    logging.info("Echo: " + " ".join(words))


def tag(tags: List[str]):
    logging.info(f"Tags: {tags}")


app = cli(
    name="list-demo",
    help="Demo of list arguments and options.",
    line_connect=True,
    max_width=135,
    show_types=True,
)

echo_cmd = command(
    name="echo",
    help="Echo the provided words.",
    callback=echo,
    arguments=[
        argument(
            name="words",
            nargs="*",
            arg_type=str,
            sort_key=0,
            choices=["hello", "world"],
        ),
    ],
)
app.commands.append(echo_cmd)

tag_cmd = command(
    name="tag",
    help="Add tags.",
    callback=tag,
    options=[
        option(
            flags=["--tags", "-t"],
            nargs="+",
            arg_type=str,
            help="Tags to add",
            sort_key=0,
        ),
    ],
)
app.commands.append(tag_cmd)


def main():
    app.run()


if __name__ == "__main__":
    main()
