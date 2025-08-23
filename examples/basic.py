# import sys

from treeparse import cli, command


def hello():
    print("Hello, world!")


app = cli(
    name="basic.py",
    help="A basic CLI example.",
    commands=[
        command(
            name="hello",
            help="Print hello world.",
            callback=hello,
        )
    ],
)


def main():
    app.run()


if __name__ == "__main__":
    main()
