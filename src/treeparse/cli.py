from __future__ import annotations

from treeparse import cli, command


def hello():
    print("Treeparse CLI")


app = cli(
    name="treeparse-demo",
    help="Treeparse framework demo CLI",
    commands=[command(name="hello", callback=hello)],
)


def main():
    app.run()
