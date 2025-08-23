# import sys

from treeparse.cli import Cli
from treeparse.models import Command


def hello():
    print("Hello, world!")


cli = Cli(
    name="basic.py",
    help="A basic CLI example.",
    commands=[
        Command(
            name="hello",
            help="Print hello world.",
            callback=hello,
        )
    ],
)


def main():
    cli.run()


if __name__ == "__main__":
    main()
